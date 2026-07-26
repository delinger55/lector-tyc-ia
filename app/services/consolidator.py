"""Servicio de consolidación (fase Reduce del Map-Reduce).

Consolida múltiples AnalysisResult parciales en un único resultado final,
eliminando cláusulas de riesgo duplicadas o equivalentes.
"""

from difflib import SequenceMatcher

from app.schemas.analysis import AnalysisResult, RiskClause, Severity

# Orden de severidad para comparación (mayor valor = mayor prioridad)
_SEVERITY_ORDER = {
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
}


def _normalize_title(title: str) -> str:
    """Normaliza un título para comparación de duplicados."""
    return title.lower().strip()


def _titles_are_similar(title_a: str, title_b: str, threshold: float = 0.8) -> bool:
    """Determina si dos títulos son equivalentes por similitud.

    Dos títulos se consideran equivalentes si:
    - Sus versiones normalizadas son idénticas, o
    - Su ratio de similitud (SequenceMatcher) supera el threshold.

    Args:
        title_a: Primer título.
        title_b: Segundo título.
        threshold: Umbral de similitud (0.0 a 1.0). Default 0.8.

    Returns:
        True si los títulos son considerados equivalentes.
    """
    norm_a = _normalize_title(title_a)
    norm_b = _normalize_title(title_b)

    if norm_a == norm_b:
        return True

    ratio = SequenceMatcher(None, norm_a, norm_b).ratio()
    return ratio > threshold


def _deduplicate_clauses(clauses: list[RiskClause]) -> list[RiskClause]:
    """Elimina cláusulas duplicadas, conservando la de mayor severidad.

    Args:
        clauses: Lista de todas las cláusulas recopiladas.

    Returns:
        Lista deduplicada de cláusulas.
    """
    unique: list[RiskClause] = []

    for clause in clauses:
        is_duplicate = False
        for i, existing in enumerate(unique):
            if _titles_are_similar(clause.title, existing.title):
                # Duplicado encontrado: conservar la de mayor severidad
                if _SEVERITY_ORDER[clause.severity] > _SEVERITY_ORDER[existing.severity]:
                    unique[i] = clause
                is_duplicate = True
                break
        if not is_duplicate:
            unique.append(clause)

    return unique


def consolidate_results(partial_results: list[AnalysisResult]) -> AnalysisResult:
    """Consolida múltiples resultados parciales en uno final.

    Estrategia:
    1. Recopilar todas las risk_clauses de todos los fragmentos
    2. Deduplicar cláusulas por similitud de título
    3. Seleccionar 5 summary_points representativos (primeros 5 únicos)
    4. Determinar is_valid_terms por mayoría de fragmentos

    Args:
        partial_results: Lista de AnalysisResult de cada chunk.

    Returns:
        AnalysisResult unificado y deduplicado.
    """
    if not partial_results:
        return AnalysisResult(
            is_valid_terms=False,
            summary_points=["No se pudo analizar el documento."] * 5,
            risk_clauses=[],
            rejection_reason="No se obtuvieron resultados parciales.",
        )

    # 1. Recopilar todas las cláusulas de riesgo
    all_clauses: list[RiskClause] = []
    for result in partial_results:
        all_clauses.extend(result.risk_clauses)

    # 2. Deduplicar
    unique_clauses = _deduplicate_clauses(all_clauses)

    # 3. Seleccionar 5 summary_points representativos
    all_points: list[str] = []
    seen_normalized: set[str] = set()
    for result in partial_results:
        for point in result.summary_points:
            normalized = point.lower().strip()
            if normalized not in seen_normalized:
                seen_normalized.add(normalized)
                all_points.append(point)

    # Tomar los primeros 5 únicos; si no hay suficientes, rellenar
    if len(all_points) >= 5:
        selected_points = all_points[:5]
    else:
        # Rellenar con puntos repetidos si es necesario
        selected_points = all_points[:]
        while len(selected_points) < 5:
            selected_points.append(all_points[len(selected_points) % len(all_points)])

    # 4. is_valid_terms por mayoría
    valid_count = sum(1 for r in partial_results if r.is_valid_terms)
    is_valid = valid_count > len(partial_results) / 2

    # 5. rejection_reason: primer no-None encontrado
    rejection_reason = None
    for result in partial_results:
        if result.rejection_reason is not None:
            rejection_reason = result.rejection_reason
            break

    return AnalysisResult(
        is_valid_terms=is_valid,
        summary_points=selected_points,
        risk_clauses=unique_clauses,
        rejection_reason=rejection_reason,
    )
