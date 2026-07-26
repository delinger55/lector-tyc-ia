"""Proveedor mock de análisis LLM para desarrollo y pruebas."""

from app.llm.base import AnalizadorLLM
from app.schemas.analysis import AnalysisResult, RiskClause, Severity


class MockLLMAnalyzer(AnalizadorLLM):
    """Proveedor mock que retorna respuestas simuladas.

    Activable mediante LLM_PROVIDER=mock. Permite desarrollo y pruebas
    sin consumir créditos de API real.
    """

    async def analyze(self, text: str) -> AnalysisResult:
        """Retorna un AnalysisResult simulado con datos de ejemplo.

        Args:
            text: Texto a analizar (no se procesa realmente).

        Returns:
            AnalysisResult con 5 puntos de resumen y cláusulas de ejemplo.
        """
        return AnalysisResult(
            is_valid_terms=True,
            summary_points=[
                "El usuario acepta que sus datos personales sean recopilados para mejorar el servicio.",
                "La empresa puede modificar los términos en cualquier momento sin notificación previa.",
                "El usuario cede derechos de uso sobre el contenido que suba a la plataforma.",
                "La empresa no se hace responsable por pérdidas derivadas del uso del servicio.",
                "El usuario acepta recibir comunicaciones comerciales por correo electrónico.",
            ],
            risk_clauses=[
                RiskClause(
                    title="Modificación unilateral de términos",
                    severity=Severity.HIGH,
                    explanation=(
                        "La empresa puede cambiar las condiciones del servicio "
                        "sin avisarte, lo que significa que podrías estar aceptando "
                        "nuevas reglas sin saberlo."
                    ),
                    quote="Nos reservamos el derecho de modificar estos términos en cualquier momento.",
                ),
                RiskClause(
                    title="Cesión de derechos sobre contenido",
                    severity=Severity.MEDIUM,
                    explanation=(
                        "Al subir contenido a la plataforma, le das permiso a la "
                        "empresa para usarlo como quiera, incluso con fines comerciales."
                    ),
                    quote="El usuario otorga una licencia mundial, irrevocable y gratuita.",
                ),
                RiskClause(
                    title="Recopilación de datos para terceros",
                    severity=Severity.LOW,
                    explanation=(
                        "Tus datos básicos de uso pueden ser compartidos con "
                        "empresas asociadas para análisis estadístico."
                    ),
                ),
            ],
            rejection_reason=None,
        )
