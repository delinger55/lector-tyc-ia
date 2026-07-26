"""Extractor de texto desde URLs de páginas web.

Incluye protección contra SSRF (Server-Side Request Forgery):
valida que el hostname resuelva a una IP pública antes de realizar la petición.
"""

import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.exceptions import UrlExtractionError


# Tags a eliminar antes de extraer texto
_TAGS_TO_REMOVE = [
    "script", "style", "nav", "header", "footer",
    "aside", "iframe", "noscript", "form", "button",
]


def _validate_url_target(url: str) -> None:
    """Valida que la URL no apunte a servicios internos (protección SSRF).

    Resuelve el hostname a IP y rechaza si pertenece a rangos:
    - Loopback (127.0.0.0/8, ::1)
    - Privados (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, etc.)
    - Link-local (169.254.0.0/16, fe80::/10) — incluye metadata cloud 169.254.169.254
    - Reservados (0.0.0.0/8, 240.0.0.0/4, etc.)

    Args:
        url: URL a validar.

    Raises:
        UrlExtractionError: Si la IP resuelta es privada, loopback, link-local o reservada.
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            raise UrlExtractionError()

        # Resolver hostname a IP
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if not addr_info:
            raise UrlExtractionError()

        # Verificar todas las IPs resueltas
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)

            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise UrlExtractionError()

    except UrlExtractionError:
        raise
    except (socket.gaierror, socket.herror, ValueError, OSError):
        # DNS resolution failed o IP inválida
        raise UrlExtractionError()


class WebUrlExtractor:
    """Descarga una página web y extrae su texto limpio.

    Usa httpx para la descarga y BeautifulSoup para parsear HTML,
    eliminando elementos no relevantes (scripts, estilos, navegación, etc.).

    Incluye validación SSRF: rechaza URLs que resuelvan a IPs internas.
    """

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    def extract(self, url: str) -> str:
        """Descarga la URL y extrae el texto limpio.

        Args:
            url: URL completa de la página web.

        Returns:
            Texto plano extraído de la página.

        Raises:
            UrlExtractionError: Si la URL es inválida, apunta a IP interna,
                               o no se puede descargar/parsear.
        """
        if not url or not url.startswith(("http://", "https://")):
            raise UrlExtractionError()

        # Validación SSRF: rechazar IPs internas antes de hacer la petición
        _validate_url_target(url)

        try:
            response = httpx.get(
                url,
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "LectorTyC/1.0"},
            )
            response.raise_for_status()
        except (httpx.HTTPError, httpx.InvalidURL) as e:
            raise UrlExtractionError() from e

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            raise UrlExtractionError()

        try:
            soup = BeautifulSoup(response.text, "html.parser")

            # Eliminar tags no deseados
            for tag_name in _TAGS_TO_REMOVE:
                for tag in soup.find_all(tag_name):
                    tag.decompose()

            # Extraer texto
            text = soup.get_text(separator="\n", strip=True)

            if not text or len(text) < 50:
                raise UrlExtractionError()

            return text
        except UrlExtractionError:
            raise
        except Exception as e:
            raise UrlExtractionError() from e
