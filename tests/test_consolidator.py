"""Tests para app/services/consolidator.py.

Incluye Property 6 (consolidación elimina cláusulas duplicadas) y unit tests.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.schemas.analysis import AnalysisResult, RiskClause, Severity
from app.services.consolidator import consolidate_results


# --- Strategies para hypothesis ---

severity_strategy = st.sampled_from([Severity.HIGH, Severity.MEDIUM, Severity.LOW])

risk_clause_strategy = st.builds(
    RiskClause,
    title=st.text(min_size=3, max_size=30),
    severity=severity_strategy,
    explanation=st.text(min_size=5, max_size=50),
    quote=st.one_of(st.none(), st.text(min_size=5, max_size=50)),
)

partial_result_strategy = st.builds(
    AnalysisResult,
    is_valid_terms=st.booleans(),
    summary_points=st.lists(st.text(min_size=5, max_size=40), min_size=5, max_size=5),
    risk_clauses=st.lists(risk_clause_strategy, min_size=0, max_size=4),
    rejection_reason=st.one_of(st.none(), st.text(min_size=5, max_size=40)),
)


# --- Property 6: Consolidación elimina cláusulas duplicadas ---


class TestProperty6Deduplication:
    """Property 6: resultado consolidado tiene <= total cláusulas originales."""

    @settings(max_examples=200, deadline=None)
    @given(
        partial_results=st.lists(partial_result_strategy, min_size=1, max_size=5)
    )
    def test_consolidated_clauses_lte_total(self, partial_results: list[AnalysisResult]):
        """Número de cláusulas consolidadas <= suma de todas las parciales."""
        total_clauses = sum(len(r.risk_clauses) for r in partial_results)
        result = consolidate_results(partial_results)
        assert len(result.risk_clauses) <= total_clauses

    @settings(max_examples=200, deadline=None)
    @given(
        partial_results=st.lists(partial_result_strategy, min_size=1, max_size=5)
    )
    def test_consolidated_has_exactly_five_summary_points(
        self, partial_results: list[AnalysisResult]
    ):
        """Resultado consolidado siempre tiene exactamente 5 summary_points."""
        result = consolidate_results(partial_results)
        assert len(result.summary_points) == 5


# --- Unit Tests ---


class TestConsolidateResultsDeduplication:
    """Tests de deduplicación de cláusulas."""

    def test_exact_duplicate_titles_deduplicated(self):
        """Cláusulas con título idéntico se deduplicican."""
        clause = RiskClause(
            title="Cesión de datos",
            severity=Severity.MEDIUM,
            explanation="Explica algo",
        )
        partial_a = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p1", "p2", "p3", "p4", "p5"],
            risk_clauses=[clause],
        )
        partial_b = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p6", "p7", "p8", "p9", "p10"],
            risk_clauses=[clause],
        )
        result = consolidate_results([partial_a, partial_b])
        assert len(result.risk_clauses) == 1

    def test_similar_titles_deduplicated(self):
        """Cláusulas con títulos muy similares se deduplican."""
        clause_a = RiskClause(
            title="Cesión de datos personales",
            severity=Severity.LOW,
            explanation="Algo",
        )
        clause_b = RiskClause(
            title="Cesion de datos personales",  # sin tilde, misma idea
            severity=Severity.HIGH,
            explanation="Otra cosa",
        )
        partial_a = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p1", "p2", "p3", "p4", "p5"],
            risk_clauses=[clause_a],
        )
        partial_b = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p6", "p7", "p8", "p9", "p10"],
            risk_clauses=[clause_b],
        )
        result = consolidate_results([partial_a, partial_b])
        assert len(result.risk_clauses) == 1

    def test_different_titles_preserved(self):
        """Cláusulas con títulos diferentes se conservan todas."""
        clause_a = RiskClause(
            title="Cesión de datos", severity=Severity.HIGH, explanation="A"
        )
        clause_b = RiskClause(
            title="Modificación unilateral", severity=Severity.MEDIUM, explanation="B"
        )
        clause_c = RiskClause(
            title="Arbitraje obligatorio", severity=Severity.LOW, explanation="C"
        )
        partial = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p1", "p2", "p3", "p4", "p5"],
            risk_clauses=[clause_a, clause_b, clause_c],
        )
        result = consolidate_results([partial])
        assert len(result.risk_clauses) == 3

    def test_duplicate_keeps_higher_severity(self):
        """Cuando hay duplicados, se conserva la de mayor severidad."""
        clause_low = RiskClause(
            title="Recopilación de datos",
            severity=Severity.LOW,
            explanation="Versión leve",
        )
        clause_high = RiskClause(
            title="Recopilación de datos",
            severity=Severity.HIGH,
            explanation="Versión grave",
        )
        partial_a = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p1", "p2", "p3", "p4", "p5"],
            risk_clauses=[clause_low],
        )
        partial_b = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p6", "p7", "p8", "p9", "p10"],
            risk_clauses=[clause_high],
        )
        result = consolidate_results([partial_a, partial_b])
        assert len(result.risk_clauses) == 1
        assert result.risk_clauses[0].severity == Severity.HIGH

    def test_duplicate_keeps_higher_severity_reverse_order(self):
        """Orden inverso: HIGH primero, LOW después, conserva HIGH."""
        clause_high = RiskClause(
            title="Compartir datos",
            severity=Severity.HIGH,
            explanation="Grave",
        )
        clause_low = RiskClause(
            title="Compartir datos",
            severity=Severity.LOW,
            explanation="Leve",
        )
        partial_a = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p1", "p2", "p3", "p4", "p5"],
            risk_clauses=[clause_high],
        )
        partial_b = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p6", "p7", "p8", "p9", "p10"],
            risk_clauses=[clause_low],
        )
        result = consolidate_results([partial_a, partial_b])
        assert len(result.risk_clauses) == 1
        assert result.risk_clauses[0].severity == Severity.HIGH


class TestConsolidateResultsSummaryPoints:
    """Tests para selección de summary_points."""

    def test_exactly_five_summary_points(self):
        """Resultado siempre tiene exactamente 5 puntos."""
        partial = AnalysisResult(
            is_valid_terms=True,
            summary_points=["p1", "p2", "p3", "p4", "p5"],
            risk_clauses=[],
        )
        result = consolidate_results([partial])
        assert len(result.summary_points) == 5

    def test_selects_unique_points_from_multiple_partials(self):
        """Selecciona puntos únicos de múltiples parciales."""
        partial_a = AnalysisResult(
            is_valid_terms=True,
            summary_points=["a1", "a2", "a3", "a4", "a5"],
            risk_clauses=[],
        )
        partial_b = AnalysisResult(
            is_valid_terms=True,
            summary_points=["b1", "b2", "b3", "b4", "b5"],
            risk_clauses=[],
        )
        result = consolidate_results([partial_a, partial_b])
        assert len(result.summary_points) == 5
        # Los primeros 5 únicos son de partial_a
        assert result.summary_points == ["a1", "a2", "a3", "a4", "a5"]

    def test_deduplicates_identical_points(self):
        """Puntos idénticos entre parciales no se repiten."""
        partial_a = AnalysisResult(
            is_valid_terms=True,
            summary_points=["mismo", "p2", "p3", "p4", "p5"],
            risk_clauses=[],
        )
        partial_b = AnalysisResult(
            is_valid_terms=True,
            summary_points=["mismo", "p6", "p7", "p8", "p9"],
            risk_clauses=[],
        )
        result = consolidate_results([partial_a, partial_b])
        assert len(result.summary_points) == 5
        # "mismo" aparece solo una vez, luego se llenan con otros
        assert result.summary_points.count("mismo") <= 1


class TestConsolidateResultsIsValidTerms:
    """Tests para determinación de is_valid_terms por mayoría."""

    def test_majority_true(self):
        """2 True + 1 False → True."""
        partials = [
            AnalysisResult(
                is_valid_terms=True,
                summary_points=["p1", "p2", "p3", "p4", "p5"],
                risk_clauses=[],
            ),
            AnalysisResult(
                is_valid_terms=True,
                summary_points=["p6", "p7", "p8", "p9", "p10"],
                risk_clauses=[],
            ),
            AnalysisResult(
                is_valid_terms=False,
                summary_points=["p11", "p12", "p13", "p14", "p15"],
                risk_clauses=[],
            ),
        ]
        result = consolidate_results(partials)
        assert result.is_valid_terms is True

    def test_majority_false(self):
        """1 True + 2 False → False."""
        partials = [
            AnalysisResult(
                is_valid_terms=True,
                summary_points=["p1", "p2", "p3", "p4", "p5"],
                risk_clauses=[],
            ),
            AnalysisResult(
                is_valid_terms=False,
                summary_points=["p6", "p7", "p8", "p9", "p10"],
                risk_clauses=[],
            ),
            AnalysisResult(
                is_valid_terms=False,
                summary_points=["p11", "p12", "p13", "p14", "p15"],
                risk_clauses=[],
            ),
        ]
        result = consolidate_results(partials)
        assert result.is_valid_terms is False

    def test_all_true(self):
        """Todos True → True."""
        partials = [
            AnalysisResult(
                is_valid_terms=True,
                summary_points=[f"p{i}" for i in range(j * 5, j * 5 + 5)],
                risk_clauses=[],
            )
            for j in range(3)
        ]
        result = consolidate_results(partials)
        assert result.is_valid_terms is True

    def test_all_false(self):
        """Todos False → False."""
        partials = [
            AnalysisResult(
                is_valid_terms=False,
                summary_points=[f"p{i}" for i in range(j * 5, j * 5 + 5)],
                risk_clauses=[],
            )
            for j in range(3)
        ]
        result = consolidate_results(partials)
        assert result.is_valid_terms is False


class TestConsolidateResultsRejectionReason:
    """Tests para manejo de rejection_reason."""

    def test_first_non_none_rejection_reason(self):
        """Usa el primer rejection_reason no-None."""
        partials = [
            AnalysisResult(
                is_valid_terms=True,
                summary_points=["p1", "p2", "p3", "p4", "p5"],
                risk_clauses=[],
                rejection_reason=None,
            ),
            AnalysisResult(
                is_valid_terms=False,
                summary_points=["p6", "p7", "p8", "p9", "p10"],
                risk_clauses=[],
                rejection_reason="No es un documento de TyC",
            ),
        ]
        result = consolidate_results(partials)
        assert result.rejection_reason == "No es un documento de TyC"

    def test_all_none_rejection_reason(self):
        """Si todos son None, el resultado es None."""
        partials = [
            AnalysisResult(
                is_valid_terms=True,
                summary_points=[f"p{i}" for i in range(j * 5, j * 5 + 5)],
                risk_clauses=[],
                rejection_reason=None,
            )
            for j in range(2)
        ]
        result = consolidate_results(partials)
        assert result.rejection_reason is None


class TestConsolidateResultsEdgeCases:
    """Tests de edge cases."""

    def test_empty_list_returns_fallback(self):
        """Lista vacía retorna resultado de fallback."""
        result = consolidate_results([])
        assert result.is_valid_terms is False
        assert len(result.summary_points) == 5
        assert result.rejection_reason is not None

    def test_single_partial_returns_equivalent(self):
        """Un solo parcial retorna resultado equivalente."""
        clause = RiskClause(
            title="Test", severity=Severity.HIGH, explanation="Algo"
        )
        partial = AnalysisResult(
            is_valid_terms=True,
            summary_points=["a", "b", "c", "d", "e"],
            risk_clauses=[clause],
        )
        result = consolidate_results([partial])
        assert result.is_valid_terms is True
        assert result.summary_points == ["a", "b", "c", "d", "e"]
        assert len(result.risk_clauses) == 1
