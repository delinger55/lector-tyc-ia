"""Esquemas Pydantic para el análisis de términos y condiciones.

Define el contrato de datos entre el LLM, los servicios internos y la API.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class Severity(str, Enum):
    """Nivel de severidad de una cláusula de riesgo."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskClause(BaseModel):
    """Cláusula identificada como riesgosa o sospechosa."""

    title: str
    severity: Severity
    explanation: str
    quote: Optional[str] = None


class AnalysisResult(BaseModel):
    """Resultado completo del análisis de un documento de TyC."""

    is_valid_terms: bool
    summary_points: list[str]
    risk_clauses: list[RiskClause]
    rejection_reason: Optional[str] = None

    @field_validator("summary_points")
    @classmethod
    def validate_summary_points_count(cls, v: list[str]) -> list[str]:
        """Garantiza que siempre haya exactamente 5 puntos de resumen."""
        if len(v) != 5:
            raise ValueError(
                f"summary_points debe contener exactamente 5 elementos, "
                f"recibió {len(v)}"
            )
        return v


class ErrorResponse(BaseModel):
    """Respuesta de error estandarizada para la API."""

    detail: str
    error_code: str
