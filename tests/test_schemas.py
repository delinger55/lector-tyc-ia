"""Tests para app/schemas/analysis.py.

Incluye Property-Based Tests (hypothesis) y unit tests.
- Property 7: Validación de AnalysisResult rechaza listas sin 5 elementos
- Property 8: Serialización round-trip de AnalysisResult
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.schemas.analysis import (
    AnalysisResult,
    ErrorResponse,
    RiskClause,
    Severity,
)

# --- Strategies para hypothesis ---

severity_strategy = st.sampled_from([Severity.HIGH, Severity.MEDIUM, Severity.LOW])

risk_clause_strategy = st.builds(
    RiskClause,
    title=st.text(min_size=1, max_size=50),
    severity=severity_strategy,
    explanation=st.text(min_size=1, max_size=100),
    quote=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
)

valid_analysis_result_strategy = st.builds(
    AnalysisResult,
    is_valid_terms=st.booleans(),
    summary_points=st.lists(st.text(min_size=1, max_size=50), min_size=5, max_size=5),
    risk_clauses=st.lists(risk_clause_strategy, min_size=0, max_size=5),
    rejection_reason=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
)


# --- Property 7: Validación rechaza listas sin 5 elementos ---


class TestProperty7SummaryPointsValidation:
    """Property 7: For any lista con len != 5, AnalysisResult lanza ValidationError."""

    @settings(max_examples=200, deadline=None)
    @given(
        points=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10).filter(
            lambda x: len(x) != 5
        )
    )
    def test_rejects_non_five_summary_points(self, points: list[str]):
        """Listas con longitud != 5 siempre son rechazadas."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                is_valid_terms=True,
                summary_points=points,
                risk_clauses=[],
            )

    @settings(max_examples=200, deadline=None)
    @given(
        points=st.lists(st.text(min_size=1, max_size=20), min_size=5, max_size=5)
    )
    def test_accepts_exactly_five_summary_points(self, points: list[str]):
        """Listas con exactamente 5 elementos siempre son aceptadas."""
        result = AnalysisResult(
            is_valid_terms=True,
            summary_points=points,
            risk_clauses=[],
        )
        assert len(result.summary_points) == 5


# --- Property 8: Serialización round-trip ---


class TestProperty8RoundTrip:
    """Property 8: For any AnalysisResult válido, serialize → deserialize == original."""

    @settings(max_examples=200, deadline=None)
    @given(result=valid_analysis_result_strategy)
    def test_json_round_trip(self, result: AnalysisResult):
        """Serializar a JSON y deserializar produce objeto equivalente."""
        json_str = result.model_dump_json()
        restored = AnalysisResult.model_validate_json(json_str)
        assert restored == result

    @settings(max_examples=200, deadline=None)
    @given(result=valid_analysis_result_strategy)
    def test_dict_round_trip(self, result: AnalysisResult):
        """Serializar a dict y deserializar produce objeto equivalente."""
        data = result.model_dump()
        restored = AnalysisResult.model_validate(data)
        assert restored == result


# --- Unit Tests ---


class TestAnalysisResultUnit:
    """Unit tests para AnalysisResult."""

    def test_valid_instance(self):
        """Instancia válida con 5 puntos se crea correctamente."""
        result = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p1", "p2", "p3", "p4", "p5"],
            risk_clauses=[
                RiskClause(
                    title="Cláusula de datos",
                    severity=Severity.HIGH,
                    explanation="Comparten tus datos con terceros",
                )
            ],
            rejection_reason=None,
        )
        assert result.is_valid_terms is True
        assert len(result.summary_points) == 5
        assert len(result.risk_clauses) == 1
        assert result.rejection_reason is None

    def test_empty_list_rejected(self):
        """Lista vacía es rechazada."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                is_valid_terms=True,
                summary_points=[],
                risk_clauses=[],
            )

    def test_four_points_rejected(self):
        """4 puntos es rechazado."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                is_valid_terms=True,
                summary_points=["a", "b", "c", "d"],
                risk_clauses=[],
            )

    def test_six_points_rejected(self):
        """6 puntos es rechazado."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                is_valid_terms=True,
                summary_points=["a", "b", "c", "d", "e", "f"],
                risk_clauses=[],
            )

    def test_with_rejection_reason(self):
        """AnalysisResult con rejection_reason se crea correctamente."""
        result = AnalysisResult(
            is_valid_terms=False,
            summary_points=["p1", "p2", "p3", "p4", "p5"],
            risk_clauses=[],
            rejection_reason="No es un documento de términos y condiciones",
        )
        assert result.is_valid_terms is False
        assert result.rejection_reason is not None


class TestRiskClauseUnit:
    """Unit tests para RiskClause."""

    def test_with_quote(self):
        """RiskClause con quote es válido."""
        clause = RiskClause(
            title="Cesión de derechos",
            severity=Severity.MEDIUM,
            explanation="Ceden tus derechos de autor",
            quote="El usuario cede todos sus derechos...",
        )
        assert clause.quote is not None

    def test_without_quote(self):
        """RiskClause sin quote (None) es válido."""
        clause = RiskClause(
            title="Recopilación de datos",
            severity=Severity.LOW,
            explanation="Recopilan datos básicos de uso",
        )
        assert clause.quote is None

    def test_all_severities(self):
        """Los 3 niveles de severidad son aceptados."""
        for sev in [Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            clause = RiskClause(
                title="Test", severity=sev, explanation="Test"
            )
            assert clause.severity == sev


class TestSeverityEnum:
    """Unit tests para Severity enum."""

    def test_has_three_values(self):
        """Severity tiene exactamente 3 valores."""
        assert len(Severity) == 3

    def test_values(self):
        """Los valores son HIGH, MEDIUM, LOW."""
        assert set(Severity) == {Severity.HIGH, Severity.MEDIUM, Severity.LOW}

    def test_string_values(self):
        """Los valores string son los esperados."""
        assert Severity.HIGH.value == "HIGH"
        assert Severity.MEDIUM.value == "MEDIUM"
        assert Severity.LOW.value == "LOW"


class TestErrorResponse:
    """Unit tests para ErrorResponse."""

    def test_creation(self):
        """ErrorResponse se crea correctamente."""
        resp = ErrorResponse(detail="Archivo no válido", error_code="INVALID_FORMAT")
        assert resp.detail == "Archivo no válido"
        assert resp.error_code == "INVALID_FORMAT"

    def test_serialization(self):
        """ErrorResponse se serializa a JSON correctamente."""
        resp = ErrorResponse(detail="Error", error_code="TEST")
        data = resp.model_dump()
        assert data == {"detail": "Error", "error_code": "TEST"}
