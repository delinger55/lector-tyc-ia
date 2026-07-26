"""Tests para app/llm/.

Verifica MockLLMAnalyzer, factory get_llm_analyzer y la interfaz abstracta.
"""

from unittest.mock import patch

import pytest

from app.llm import get_llm_analyzer
from app.llm.base import AnalizadorLLM
from app.llm.mock_provider import MockLLMAnalyzer
from app.schemas.analysis import AnalysisResult, Severity


# --- Tests MockLLMAnalyzer ---


class TestMockLLMAnalyzer:
    """Unit tests para MockLLMAnalyzer."""

    @pytest.mark.asyncio
    async def test_returns_valid_analysis_result(self):
        """Mock retorna un AnalysisResult válido."""
        analyzer = MockLLMAnalyzer()
        result = await analyzer.analyze("Texto de prueba")
        assert isinstance(result, AnalysisResult)

    @pytest.mark.asyncio
    async def test_returns_exactly_five_summary_points(self):
        """Mock retorna exactamente 5 puntos de resumen."""
        analyzer = MockLLMAnalyzer()
        result = await analyzer.analyze("Cualquier texto")
        assert len(result.summary_points) == 5

    @pytest.mark.asyncio
    async def test_returns_is_valid_terms_true(self):
        """Mock retorna is_valid_terms=True."""
        analyzer = MockLLMAnalyzer()
        result = await analyzer.analyze("Texto")
        assert result.is_valid_terms is True

    @pytest.mark.asyncio
    async def test_returns_risk_clauses(self):
        """Mock retorna cláusulas de riesgo con diferentes severidades."""
        analyzer = MockLLMAnalyzer()
        result = await analyzer.analyze("Texto")
        assert len(result.risk_clauses) > 0
        severities = {clause.severity for clause in result.risk_clauses}
        assert Severity.HIGH in severities
        assert Severity.MEDIUM in severities
        assert Severity.LOW in severities

    @pytest.mark.asyncio
    async def test_summary_points_are_in_spanish(self):
        """Los puntos de resumen están en español."""
        analyzer = MockLLMAnalyzer()
        result = await analyzer.analyze("Texto")
        # Verificar que al menos un punto contiene palabras en español
        all_text = " ".join(result.summary_points)
        assert "usuario" in all_text.lower() or "datos" in all_text.lower()

    @pytest.mark.asyncio
    async def test_rejection_reason_is_none(self):
        """Mock retorna rejection_reason=None."""
        analyzer = MockLLMAnalyzer()
        result = await analyzer.analyze("Texto")
        assert result.rejection_reason is None

    def test_inherits_from_analizador_llm(self):
        """MockLLMAnalyzer hereda de AnalizadorLLM."""
        analyzer = MockLLMAnalyzer()
        assert isinstance(analyzer, AnalizadorLLM)


# --- Tests Factory get_llm_analyzer ---


class TestGetLLMAnalyzer:
    """Unit tests para factory get_llm_analyzer."""

    def test_returns_mock_analyzer_when_provider_is_mock(self):
        """LLM_PROVIDER=mock retorna MockLLMAnalyzer."""
        with patch("app.llm.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "mock"
            analyzer = get_llm_analyzer()
            assert isinstance(analyzer, MockLLMAnalyzer)

    def test_raises_not_implemented_for_openai(self):
        """LLM_PROVIDER=openai lanza NotImplementedError (pendiente)."""
        with patch("app.llm.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "openai"
            with pytest.raises(NotImplementedError):
                get_llm_analyzer()

    def test_raises_value_error_for_unsupported_provider(self):
        """Proveedor no soportado lanza ValueError."""
        with patch("app.llm.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = "anthropic"
            with pytest.raises(ValueError, match="no soportado"):
                get_llm_analyzer()

    def test_raises_value_error_for_empty_provider(self):
        """Proveedor vacío lanza ValueError."""
        with patch("app.llm.get_settings") as mock_settings:
            mock_settings.return_value.llm_provider = ""
            with pytest.raises(ValueError):
                get_llm_analyzer()
