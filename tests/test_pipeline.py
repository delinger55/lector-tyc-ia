"""Tests para app/services/analysis_pipeline.py.

Verifica análisis directo, Map-Reduce, retry logic y timeout.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import AnalysisValidationError, LLMTimeoutError
from app.llm.base import AnalizadorLLM
from app.schemas.analysis import AnalysisResult, RiskClause, Severity
from app.services.analysis_pipeline import AnalysisPipeline


# --- Helpers ---


def _valid_result(**kwargs) -> AnalysisResult:
    """Crea un AnalysisResult válido con defaults."""
    defaults = {
        "is_valid_terms": True,
        "summary_points": ["p1", "p2", "p3", "p4", "p5"],
        "risk_clauses": [
            RiskClause(title="Test", severity=Severity.LOW, explanation="Test")
        ],
        "rejection_reason": None,
    }
    defaults.update(kwargs)
    return AnalysisResult(**defaults)


def _invalid_result_4_points() -> AnalysisResult:
    """Crea un AnalysisResult con 4 puntos (inválido para el pipeline)."""
    # Bypass del validator creando con construct
    return AnalysisResult.model_construct(
        is_valid_terms=True,
        summary_points=["p1", "p2", "p3", "p4"],
        risk_clauses=[],
        rejection_reason=None,
    )


def _invalid_result_6_points() -> AnalysisResult:
    """Crea un AnalysisResult con 6 puntos (inválido para el pipeline)."""
    return AnalysisResult.model_construct(
        is_valid_terms=True,
        summary_points=["p1", "p2", "p3", "p4", "p5", "p6"],
        risk_clauses=[],
        rejection_reason=None,
    )


# --- Tests análisis directo ---


class TestAnalysisDirectPath:
    """Tests para análisis directo (texto <= threshold)."""

    @pytest.mark.asyncio
    async def test_short_text_calls_llm_once(self):
        """Texto corto usa análisis directo: 1 sola llamada al LLM."""
        mock_analyzer = AsyncMock(spec=AnalizadorLLM)
        mock_analyzer.analyze.return_value = _valid_result()

        with patch("app.services.analysis_pipeline.get_settings") as mock_settings:
            mock_settings.return_value.chunking_threshold = 12000
            mock_settings.return_value.llm_timeout_seconds = 30

            pipeline = AnalysisPipeline(mock_analyzer)
            result = await pipeline.analyze_document("Texto corto de prueba")

        assert mock_analyzer.analyze.call_count == 1
        assert len(result.summary_points) == 5

    @pytest.mark.asyncio
    async def test_text_at_threshold_uses_direct(self):
        """Texto exactamente en el threshold usa análisis directo."""
        text = "A" * 12000  # Exactamente en el threshold

        mock_analyzer = AsyncMock(spec=AnalizadorLLM)
        mock_analyzer.analyze.return_value = _valid_result()

        with patch("app.services.analysis_pipeline.get_settings") as mock_settings:
            mock_settings.return_value.chunking_threshold = 12000
            mock_settings.return_value.llm_timeout_seconds = 30

            pipeline = AnalysisPipeline(mock_analyzer)
            result = await pipeline.analyze_document(text)

        assert mock_analyzer.analyze.call_count == 1
        assert result.is_valid_terms is True


# --- Tests Map-Reduce ---


class TestAnalysisMapReduce:
    """Tests para análisis Map-Reduce (texto > threshold)."""

    @pytest.mark.asyncio
    async def test_long_text_calls_llm_multiple_times(self):
        """Texto largo activa Map-Reduce: múltiples llamadas al LLM."""
        # Crear texto con 3 párrafos, cada uno > threshold/3
        paragraphs = ["Párrafo largo. " * 50] * 3  # Cada ~750 chars
        text = "\n\n".join(paragraphs)  # Total ~2250 chars

        mock_analyzer = AsyncMock(spec=AnalizadorLLM)
        mock_analyzer.analyze.return_value = _valid_result()

        with patch("app.services.analysis_pipeline.get_settings") as mock_settings:
            mock_settings.return_value.chunking_threshold = 800
            mock_settings.return_value.llm_timeout_seconds = 30

            pipeline = AnalysisPipeline(mock_analyzer)
            result = await pipeline.analyze_document(text)

        # Debe haber llamado al LLM más de 1 vez (Map)
        assert mock_analyzer.analyze.call_count > 1
        assert len(result.summary_points) == 5

    @pytest.mark.asyncio
    async def test_map_reduce_consolidates_clauses(self):
        """Map-Reduce consolida cláusulas de múltiples chunks."""
        text = "Párrafo uno largo. " * 40 + "\n\n" + "Párrafo dos largo. " * 40

        # Cada llamada retorna cláusulas diferentes usando un counter
        call_counter = {"n": 0}

        async def mock_analyze(text_input: str) -> AnalysisResult:
            call_counter["n"] += 1
            if call_counter["n"] == 1:
                return _valid_result(
                    risk_clauses=[
                        RiskClause(title="Recopilación masiva de datos personales", severity=Severity.HIGH, explanation="A")
                    ]
                )
            else:
                return _valid_result(
                    risk_clauses=[
                        RiskClause(title="Modificación unilateral del contrato", severity=Severity.MEDIUM, explanation="B")
                    ]
                )

        mock_analyzer = AsyncMock(spec=AnalizadorLLM)
        mock_analyzer.analyze.side_effect = mock_analyze

        with patch("app.services.analysis_pipeline.get_settings") as mock_settings:
            mock_settings.return_value.chunking_threshold = 400
            mock_settings.return_value.llm_timeout_seconds = 30

            pipeline = AnalysisPipeline(mock_analyzer)
            result = await pipeline.analyze_document(text)

        # Ambas cláusulas deben estar en el resultado consolidado
        titles = {c.title for c in result.risk_clauses}
        assert "Recopilación masiva de datos personales" in titles
        assert "Modificación unilateral del contrato" in titles


# --- Tests retry logic ---


class TestAnalysisRetryLogic:
    """Tests para la lógica de reintento."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self):
        """Primer intento inválido (4 puntos), segundo válido → éxito."""
        mock_analyzer = AsyncMock(spec=AnalizadorLLM)
        mock_analyzer.analyze.side_effect = [
            _invalid_result_4_points(),  # Primer intento: 4 puntos
            _valid_result(),             # Segundo intento: 5 puntos
        ]

        with patch("app.services.analysis_pipeline.get_settings") as mock_settings:
            mock_settings.return_value.chunking_threshold = 12000
            mock_settings.return_value.llm_timeout_seconds = 30

            pipeline = AnalysisPipeline(mock_analyzer)
            result = await pipeline.analyze_document("Texto corto")

        assert mock_analyzer.analyze.call_count == 2
        assert len(result.summary_points) == 5

    @pytest.mark.asyncio
    async def test_double_failure_raises_validation_error(self):
        """Dos intentos inválidos consecutivos → AnalysisValidationError."""
        mock_analyzer = AsyncMock(spec=AnalizadorLLM)
        mock_analyzer.analyze.side_effect = [
            _invalid_result_4_points(),  # Primer intento: 4 puntos
            _invalid_result_6_points(),  # Segundo intento: 6 puntos
        ]

        with patch("app.services.analysis_pipeline.get_settings") as mock_settings:
            mock_settings.return_value.chunking_threshold = 12000
            mock_settings.return_value.llm_timeout_seconds = 30

            pipeline = AnalysisPipeline(mock_analyzer)
            with pytest.raises(AnalysisValidationError):
                await pipeline.analyze_document("Texto corto")

        assert mock_analyzer.analyze.call_count == 2

    @pytest.mark.asyncio
    async def test_valid_first_attempt_no_retry(self):
        """Si el primer intento es válido, no se reintenta."""
        mock_analyzer = AsyncMock(spec=AnalizadorLLM)
        mock_analyzer.analyze.return_value = _valid_result()

        with patch("app.services.analysis_pipeline.get_settings") as mock_settings:
            mock_settings.return_value.chunking_threshold = 12000
            mock_settings.return_value.llm_timeout_seconds = 30

            pipeline = AnalysisPipeline(mock_analyzer)
            result = await pipeline.analyze_document("Texto")

        assert mock_analyzer.analyze.call_count == 1
        assert len(result.summary_points) == 5


# --- Tests timeout ---


class TestAnalysisTimeout:
    """Tests para timeout de LLM."""

    @pytest.mark.asyncio
    async def test_timeout_raises_llm_timeout_error(self):
        """LLM que excede timeout → LLMTimeoutError."""

        async def slow_analyze(text: str) -> AnalysisResult:
            await asyncio.sleep(5)  # Simular delay largo
            return _valid_result()

        mock_analyzer = AsyncMock(spec=AnalizadorLLM)
        mock_analyzer.analyze.side_effect = slow_analyze

        with patch("app.services.analysis_pipeline.get_settings") as mock_settings:
            mock_settings.return_value.chunking_threshold = 12000
            mock_settings.return_value.llm_timeout_seconds = 0.1  # 100ms timeout

            pipeline = AnalysisPipeline(mock_analyzer)
            with pytest.raises(LLMTimeoutError):
                await pipeline.analyze_document("Texto corto")

    @pytest.mark.asyncio
    async def test_timeout_in_map_reduce_raises_error(self):
        """Timeout en un chunk de Map-Reduce cancela todo."""

        call_count = 0

        async def sometimes_slow(text: str) -> AnalysisResult:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                await asyncio.sleep(5)  # Segundo chunk es lento
            return _valid_result()

        mock_analyzer = AsyncMock(spec=AnalizadorLLM)
        mock_analyzer.analyze.side_effect = sometimes_slow

        text = "Párrafo uno. " * 50 + "\n\n" + "Párrafo dos. " * 50

        with patch("app.services.analysis_pipeline.get_settings") as mock_settings:
            mock_settings.return_value.chunking_threshold = 300
            mock_settings.return_value.llm_timeout_seconds = 0.1

            pipeline = AnalysisPipeline(mock_analyzer)
            with pytest.raises(LLMTimeoutError):
                await pipeline.analyze_document(text)
