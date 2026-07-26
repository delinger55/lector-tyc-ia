"""Extractor de texto desde URLs de páginas web."""

import httpx
from bs4 import BeautifulSoup

from app.core.exceptions import ExtractionError


# Tags a eliminar antes de extraer texto
_TAGS_TO_REMOVE = [
    "script", "style", "nav", "header", "footer",
    "aside", "iframe", "noscript", "form", "button",
]


class WebUrlExtractor:
    """Descarga una página web y extrae su texto limpio.

    Usa httpx para la descarga y BeautifulSoup para parsear HTML,
    eliminando elementos no relevantes (scripts, estilos, navegación, etc.).
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
            ExtractionError: Si no se puede descargar o parsear la página.
        """
        if not url or not url.startswith(("http://", "https://")):
            raise ExtractionError()

        try:
            response = httpx.get(
                url,
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "LectorTyC/1.0"},
            )
            response.raise_for_status()
        except (httpx.HTTPError, httpx.InvalidURL) as e:
            raise ExtractionError() from e

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            raise ExtractionError()

        try:
            soup = BeautifulSoup(response.text, "html.parser")

            # Eliminar tags no deseados
            for tag_name in _TAGS_TO_REMOVE:
                for tag in soup.find_all(tag_name):
                    tag.decompose()

            # Extraer texto
            text = soup.get_text(separator="\n", strip=True)

            if not text or len(text) < 50:
                raise ExtractionError()

            return text
        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError() from e
