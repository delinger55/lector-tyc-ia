"""Tests para app/core/config.py y app/core/exceptions.py."""

import pytest
from pydantic import ValidationError

from app.core.config import AppSettings
from app.core.exceptions import (
    AnalysisValidationError,
    AppBaseException,
    ExtractionError,
    FileTooLargeException,
    InvalidFormatException,
    LLMCommunicationError,
    LLMTimeoutError,
    NotTermsException,
    ScannedDocumentException,
    TextTooLongException,
)


# --- Tests de AppSettings ---


class TestAppSettingsDefaults:
    """Verifica que AppSettings carga valores por defecto correctamente."""

    def test_default_llm_provider(self):
        settings = AppSettings(llm_provider="mock")
        assert settings.llm_provider == "mock"

    def test_default_llm_api_key(self):
        settings = AppSettings(llm_provider="mock")
        assert settings.llm_api_key == ""

    def test_default_llm_timeout(self):
        settings = AppSettings(llm_provider="mock")
        assert settings.llm_timeout_seconds == 30

    def test_default_max_file_size_mb(self):
        settings = AppSettings(llm_provider="mock")
        assert settings.max_file_size_mb == 10

    def test_default_max_words(self):
        settings = AppSettings(llm_provider="mock")
        assert settings.max_words == 20_000

    def test_default_chunking_threshold(self):
        settings = AppSettings(llm_provider="mock")
        assert settings.chunking_threshold == 12_000

    def test_default_debug(self):
        settings = AppSettings(llm_provider="mock")
        assert settings.debug is False


class TestAppSettingsValidation:
    """Verifica validación condicional de LLM_API_KEY."""

    def test_mock_provider_accepts_empty_api_key(self):
        """Provider mock no requiere API key."""
        settings = AppSettings(llm_provider="mock", llm_api_key="")
        assert settings.llm_provider == "mock"

    def test_non_mock_provider_rejects_empty_api_key(self):
        """Provider diferente de mock requiere API key."""
        with pytest.raises(ValidationError) as exc_info:
            AppSettings(llm_provider="openai", llm_api_key="")
        assert "LLM_API_KEY es requerida" in str(exc_info.value)

    def test_non_mock_provider_accepts_with_api_key(self):
        """Provider openai con API key válida es aceptado."""
        settings = AppSettings(llm_provider="openai", llm_api_key="sk-test-key-123")
        assert settings.llm_provider == "openai"
        assert settings.llm_api_key == "sk-test-key-123"


class TestAppSettingsProperties:
    """Verifica propiedades calculadas."""

    def test_max_file_size_bytes_default(self):
        """10 MB = 10 * 1024 * 1024 bytes."""
        settings = AppSettings(llm_provider="mock")
        assert settings.max_file_size_bytes == 10 * 1024 * 1024

    def test_max_file_size_bytes_custom(self):
        """Valor personalizado se calcula correctamente."""
        settings = AppSettings(llm_provider="mock", max_file_size_mb=5)
        assert settings.max_file_size_bytes == 5 * 1024 * 1024


# --- Tests de Excepciones ---


class TestExceptions:
    """Verifica que cada excepción tiene el error_code y message correctos."""

    def test_app_base_exception(self):
        exc = AppBaseException(message="test msg", error_code="TEST_CODE")
        assert exc.message == "test msg"
        assert exc.error_code == "TEST_CODE"
        assert str(exc) == "test msg"

    def test_invalid_format_exception(self):
        exc = InvalidFormatException()
        assert exc.error_code == "INVALID_FORMAT"
        assert "PDF" in exc.message
        assert "Word" in exc.message

    def test_file_too_large_exception(self):
        exc = FileTooLargeException(max_size_mb=10)
        assert exc.error_code == "FILE_TOO_LARGE"
        assert "10 MB" in exc.message

    def test_scanned_document_exception(self):
        exc = ScannedDocumentException()
        assert exc.error_code == "SCANNED_DOCUMENT"
        assert "escaneado" in exc.message

    def test_extraction_error(self):
        exc = ExtractionError()
        assert exc.error_code == "CORRUPT_FILE"
        assert "corrupto" in exc.message

    def test_text_too_long_exception(self):
        exc = TextTooLongException(max_words=20_000)
        assert exc.error_code == "TEXT_TOO_LONG"
        assert "20,000" in exc.message

    def test_llm_timeout_error(self):
        exc = LLMTimeoutError()
        assert exc.error_code == "LLM_TIMEOUT"
        assert "tiempo" in exc.message

    def test_llm_communication_error(self):
        exc = LLMCommunicationError()
        assert exc.error_code == "LLM_COMMUNICATION_ERROR"
        assert "disponible" in exc.message

    def test_analysis_validation_error(self):
        exc = AnalysisValidationError()
        assert exc.error_code == "ANALYSIS_FAILED"
        assert "completarse" in exc.message

    def test_not_terms_exception(self):
        exc = NotTermsException()
        assert exc.error_code == "NOT_TERMS"
        assert "términos y condiciones" in exc.message

    def test_all_exceptions_inherit_from_base(self):
        """Todas las excepciones heredan de AppBaseException."""
        exceptions = [
            InvalidFormatException(),
            FileTooLargeException(max_size_mb=10),
            ScannedDocumentException(),
            ExtractionError(),
            TextTooLongException(max_words=20_000),
            LLMTimeoutError(),
            LLMCommunicationError(),
            AnalysisValidationError(),
            NotTermsException(),
        ]
        for exc in exceptions:
            assert isinstance(exc, AppBaseException)
