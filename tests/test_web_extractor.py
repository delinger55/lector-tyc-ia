"""Tests para app/extractors/web_extractor.py.

Cubre la protección SSRF: valida que URLs apuntando a IPs internas
(loopback, privadas, link-local, reservadas) sean rechazadas.
"""

from unittest.mock import patch

import pytest

from app.core.exceptions import UrlExtractionError
from app.extractors.web_extractor import WebUrlExtractor, _validate_url_target


class TestSSRFProtectionLoopback:
    """Rechaza acceso a localhost / loopback (127.0.0.0/8)."""

    def test_rejects_localhost(self):
        """http://localhost debe ser rechazado."""
        extractor = WebUrlExtractor()
        with pytest.raises(UrlExtractionError):
            extractor.extract("http://localhost/admin")

    def test_rejects_127_0_0_1(self):
        """http://127.0.0.1 debe ser rechazado."""
        extractor = WebUrlExtractor()
        with pytest.raises(UrlExtractionError):
            extractor.extract("http://127.0.0.1/secret")

    def test_rejects_127_0_0_1_with_port(self):
        """http://127.0.0.1:8080 debe ser rechazado."""
        extractor = WebUrlExtractor()
        with pytest.raises(UrlExtractionError):
            extractor.extract("http://127.0.0.1:8080/api")

    def test_rejects_ipv6_loopback(self):
        """http://[::1] debe ser rechazado."""
        extractor = WebUrlExtractor()
        with pytest.raises(UrlExtractionError):
            extractor.extract("http://[::1]/path")


class TestSSRFProtectionPrivateRanges:
    """Rechaza acceso a rangos de IP privada (RFC 1918)."""

    def test_rejects_192_168_x_x(self):
        """http://192.168.1.1 debe ser rechazado."""
        with patch("app.extractors.web_extractor.socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (2, 1, 6, "", ("192.168.1.1", 80))
            ]
            extractor = WebUrlExtractor()
            with pytest.raises(UrlExtractionError):
                extractor.extract("http://internal-server.local/terms")

    def test_rejects_10_x_x_x(self):
        """IPs en rango 10.0.0.0/8 deben ser rechazadas."""
        with patch("app.extractors.web_extractor.socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (2, 1, 6, "", ("10.0.0.5", 80))
            ]
            extractor = WebUrlExtractor()
            with pytest.raises(UrlExtractionError):
                extractor.extract("http://corporate-intranet.example/policy")

    def test_rejects_172_16_x_x(self):
        """IPs en rango 172.16.0.0/12 deben ser rechazadas."""
        with patch("app.extractors.web_extractor.socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (2, 1, 6, "", ("172.16.0.100", 80))
            ]
            extractor = WebUrlExtractor()
            with pytest.raises(UrlExtractionError):
                extractor.extract("http://docker-service.internal/terms")


class TestSSRFProtectionCloudMetadata:
    """Rechaza acceso al endpoint de metadata cloud (169.254.169.254)."""

    def test_rejects_cloud_metadata_endpoint(self):
        """http://169.254.169.254 (AWS/GCP metadata) debe ser rechazado."""
        with patch("app.extractors.web_extractor.socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (2, 1, 6, "", ("169.254.169.254", 80))
            ]
            extractor = WebUrlExtractor()
            with pytest.raises(UrlExtractionError):
                extractor.extract("http://169.254.169.254/latest/meta-data/")

    def test_rejects_link_local_range(self):
        """Cualquier IP en 169.254.0.0/16 (link-local) debe ser rechazada."""
        with patch("app.extractors.web_extractor.socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (2, 1, 6, "", ("169.254.1.1", 80))
            ]
            extractor = WebUrlExtractor()
            with pytest.raises(UrlExtractionError):
                extractor.extract("http://link-local-service.test/data")

    def test_rejects_metadata_via_hostname(self):
        """Hostname que resuelve a 169.254.169.254 debe ser rechazado."""
        with patch("app.extractors.web_extractor.socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (2, 1, 6, "", ("169.254.169.254", 80))
            ]
            extractor = WebUrlExtractor()
            with pytest.raises(UrlExtractionError):
                extractor.extract("http://metadata.google.internal/computeMetadata/v1/")


class TestSSRFProtectionReserved:
    """Rechaza acceso a IPs reservadas."""

    def test_rejects_0_0_0_0(self):
        """0.0.0.0 debe ser rechazada."""
        with patch("app.extractors.web_extractor.socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (2, 1, 6, "", ("0.0.0.0", 80))
            ]
            extractor = WebUrlExtractor()
            with pytest.raises(UrlExtractionError):
                extractor.extract("http://zero.example/path")


class TestSSRFValidationFunction:
    """Tests directos de _validate_url_target."""

    def test_rejects_localhost_directly(self):
        """Validación directa rechaza localhost."""
        with pytest.raises(UrlExtractionError):
            _validate_url_target("http://localhost/path")

    def test_rejects_127_directly(self):
        """Validación directa rechaza 127.0.0.1."""
        with pytest.raises(UrlExtractionError):
            _validate_url_target("http://127.0.0.1/path")

    def test_rejects_empty_hostname(self):
        """URL sin hostname es rechazada."""
        with pytest.raises(UrlExtractionError):
            _validate_url_target("http:///path")

    def test_accepts_public_ip(self):
        """IP pública es aceptada (no lanza excepción)."""
        with patch("app.extractors.web_extractor.socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (2, 1, 6, "", ("93.184.216.34", 80))  # example.com
            ]
            # No debe lanzar excepción
            _validate_url_target("http://example.com/terms")

    def test_dns_resolution_failure_raises(self):
        """Si DNS no resuelve, lanza UrlExtractionError."""
        with patch("app.extractors.web_extractor.socket.getaddrinfo") as mock_dns:
            import socket
            mock_dns.side_effect = socket.gaierror("Name resolution failed")
            with pytest.raises(UrlExtractionError):
                _validate_url_target("http://nonexistent-domain-xyz.invalid/path")
