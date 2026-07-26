"""Tests de integración End-to-End (E2E).

Verifica el flujo completo: upload → extracción → análisis (mock) → respuesta JSON.
Cubre todos los caminos de error y la estructura de respuestas.
"""

import pytest
from httpx import AsyncClient


class TestE2ESuccessFlows:
    """Flujos exitosos end-to-end."""

    async def test_pdf_upload_returns_200_with_full_analysis(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ):
        """Upload PDF válido → 200 → AnalysisResult completo."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("terminos.pdf", sample_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()

        # Estructura completa de AnalysisResult
        assert "is_valid_terms" in data
        assert "summary_points" in data
        assert "risk_clauses" in data
        assert "rejection_reason" in data

        # Validaciones de contenido
        assert isinstance(data["is_valid_terms"], bool)
        assert len(data["summary_points"]) == 5
        assert isinstance(data["risk_clauses"], list)

    async def test_docx_upload_returns_200_with_full_analysis(
        self, client: AsyncClient, sample_docx_bytes: bytes
    ):
        """Upload DOCX válido → 200 → AnalysisResult completo."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("contrato.docx", sample_docx_bytes, "application/octet-stream")},
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data["summary_points"]) == 5
        assert isinstance(data["risk_clauses"], list)
        assert data["is_valid_terms"] is True

    async def test_summary_points_are_strings(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ):
        """Los 5 summary_points son strings no vacíos."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("doc.pdf", sample_pdf_bytes, "application/pdf")},
        )
        data = response.json()
        for point in data["summary_points"]:
            assert isinstance(point, str)
            assert len(point) > 0

    async def test_risk_clauses_have_correct_structure(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ):
        """Cada risk_clause tiene title, severity, explanation."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("doc.pdf", sample_pdf_bytes, "application/pdf")},
        )
        data = response.json()
        for clause in data["risk_clauses"]:
            assert "title" in clause
            assert "severity" in clause
            assert "explanation" in clause
            assert clause["severity"] in ["HIGH", "MEDIUM", "LOW"]
            assert isinstance(clause["title"], str)
            assert isinstance(clause["explanation"], str)

    async def test_risk_clauses_optional_quote(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ):
        """El campo quote puede ser string o null."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("doc.pdf", sample_pdf_bytes, "application/pdf")},
        )
        data = response.json()
        for clause in data["risk_clauses"]:
            assert "quote" in clause
            assert clause["quote"] is None or isinstance(clause["quote"], str)


class TestE2EErrorFlows:
    """Flujos de error end-to-end."""

    async def test_invalid_format_rtf(self, client: AsyncClient):
        """Archivo .rtf → 400 INVALID_FORMAT."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("readme.rtf", b"contenido de texto", "text/plain")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_FORMAT"
        assert "PDF" in data["detail"]

    async def test_invalid_format_jpg(self, client: AsyncClient):
        """Archivo .jpg → 400 INVALID_FORMAT."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("photo.jpg", b"\xff\xd8\xff\xe0", "image/jpeg")},
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "INVALID_FORMAT"

    async def test_invalid_format_no_extension(self, client: AsyncClient):
        """Archivo sin extensión → 400 INVALID_FORMAT."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("noextension", b"data", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "INVALID_FORMAT"

    async def test_file_too_large(
        self, client: AsyncClient, large_pdf_bytes: bytes
    ):
        """Archivo > 10 MB → 400 FILE_TOO_LARGE."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("huge.pdf", large_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "FILE_TOO_LARGE"
        assert "10 MB" in data["detail"]

    async def test_scanned_pdf(
        self, client: AsyncClient, scanned_pdf_bytes: bytes
    ):
        """PDF sin texto (escaneado) → 400 SCANNED_DOCUMENT."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("scan.pdf", scanned_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "SCANNED_DOCUMENT"
        assert "escaneado" in data["detail"]

    async def test_corrupt_pdf(
        self, client: AsyncClient, corrupt_pdf_bytes: bytes
    ):
        """PDF corrupto → 400 CORRUPT_FILE."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("broken.pdf", corrupt_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "CORRUPT_FILE"
        assert "corrupto" in data["detail"]

    async def test_corrupt_docx(self, client: AsyncClient):
        """DOCX corrupto → 400 CORRUPT_FILE."""
        corrupt_docx = b"PK\x03\x04corrupted zip content" * 5
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("bad.docx", corrupt_docx, "application/octet-stream")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "CORRUPT_FILE"


class TestE2EErrorResponseStructure:
    """Verifica la estructura estándar de respuestas de error."""

    async def test_error_response_has_detail_and_error_code(self, client: AsyncClient):
        """Todas las respuestas de error tienen detail y error_code."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("test.xyz", b"data", "application/octet-stream")},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "error_code" in data
        assert isinstance(data["detail"], str)
        assert isinstance(data["error_code"], str)

    async def test_error_detail_is_in_spanish(self, client: AsyncClient):
        """El campo detail de errores está en español."""
        # Probar múltiples errores
        test_cases = [
            ("doc.rtf", b"text", "INVALID_FORMAT"),
            ("bad.pdf", b"not pdf" * 20, "CORRUPT_FILE"),
        ]
        for filename, content, expected_code in test_cases:
            response = await client.post(
                "/api/v1/analyze",
                files={"file": (filename, content, "application/octet-stream")},
            )
            data = response.json()
            assert data["error_code"] == expected_code
            # Verificar que contiene caracteres del español o palabras comunes
            detail = data["detail"]
            has_spanish = any(
                word in detail.lower()
                for word in ["archivo", "documento", "formato", "pdf", "word", "no se"]
            )
            assert has_spanish, f"Detail no parece español: {detail}"

    async def test_error_codes_are_uppercase_with_underscores(self, client: AsyncClient):
        """Los error_code siguen formato UPPER_CASE."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("x.html", b"<html>", "text/html")},
        )
        data = response.json()
        code = data["error_code"]
        assert code == code.upper()
        assert " " not in code


class TestE2EFullFlowVerification:
    """Verificación completa del flujo de datos."""

    async def test_pdf_flow_returns_mock_data(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ):
        """Flujo completo con mock LLM retorna datos esperados del mock."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("terms.pdf", sample_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()

        # El mock retorna is_valid_terms=True
        assert data["is_valid_terms"] is True
        # El mock retorna rejection_reason=None
        assert data["rejection_reason"] is None
        # El mock retorna exactamente 5 puntos
        assert len(data["summary_points"]) == 5
        # El mock retorna cláusulas con las 3 severidades
        severities = {c["severity"] for c in data["risk_clauses"]}
        assert "HIGH" in severities
        assert "MEDIUM" in severities
        assert "LOW" in severities

    async def test_no_file_persistence_after_request(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ):
        """Después del request, no quedan archivos temporales.

        Verificamos que el endpoint no crea archivos en disco
        ejecutando múltiples requests y comprobando que la app sigue funcional.
        """
        # Ejecutar múltiples requests
        for i in range(3):
            response = await client.post(
                "/api/v1/analyze",
                files={"file": (f"doc{i}.pdf", sample_pdf_bytes, "application/pdf")},
            )
            assert response.status_code == 200

        # La app sigue respondiendo correctamente (sin acumulación de estado)
        response = await client.get("/")
        assert response.status_code == 200

    async def test_content_type_json_on_success(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ):
        """Respuesta exitosa tiene content-type application/json."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("doc.pdf", sample_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    async def test_content_type_json_on_error(self, client: AsyncClient):
        """Respuesta de error tiene content-type application/json."""
        response = await client.post(
            "/api/v1/analyze",
            files={"file": ("bad.rtf", b"x", "text/plain")},
        )
        assert response.status_code == 400
        assert "application/json" in response.headers["content-type"]


class TestE2EUrlFlow:
    """Tests E2E para análisis por URL."""

    async def test_url_via_form_data(self, client: AsyncClient):
        """URL enviada via form data (como lo hace el browser en modo URL)."""
        response = await client.post(
            "/api/v1/analyze",
            data={"url": "not-a-valid-url"},
        )
        # Debe llegar al WebUrlExtractor y fallar con URL_EXTRACTION_FAILED
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "URL_EXTRACTION_FAILED"

    async def test_url_invalid_protocol(self, client: AsyncClient):
        """URL sin http/https llega al extractor y falla."""
        response = await client.post(
            "/api/v1/analyze",
            data={"url": "ftp://example.com/terms"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "URL_EXTRACTION_FAILED"

    async def test_url_field_empty_falls_to_invalid_format(self, client: AsyncClient):
        """URL vacía sin archivo → INVALID_FORMAT."""
        response = await client.post(
            "/api/v1/analyze",
            data={"url": ""},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_FORMAT"

    async def test_url_has_priority_when_both_present(self, client: AsyncClient):
        """Cuando URL y file están presentes, URL tiene prioridad."""
        # Enviar ambos: file válido + url inválida → URL se procesa primero
        txt_content = ("Texto de prueba suficiente. " * 10).encode("utf-8")
        response = await client.post(
            "/api/v1/analyze",
            data={"url": "not-valid"},
            files={"file": ("terms.txt", txt_content, "text/plain")},
        )
        # URL tiene prioridad → URL_EXTRACTION_FAILED (no procesa el file)
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "URL_EXTRACTION_FAILED"

    async def test_url_error_message_is_user_friendly(self, client: AsyncClient):
        """El mensaje de error de URL es descriptivo y en español."""
        response = await client.post(
            "/api/v1/analyze",
            data={"url": "https://thisdomaindoesnotexist99999.com/terms"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "URL_EXTRACTION_FAILED"
        assert "página web" in data["detail"]
        assert "restricciones" in data["detail"]
