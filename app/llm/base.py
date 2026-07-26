"""Interfaz abstracta para proveedores de análisis LLM."""

from abc import ABC, abstractmethod

from app.schemas.analysis import AnalysisResult


class AnalizadorLLM(ABC):
    """Interfaz abstracta para proveedores de análisis LLM.

    Implementa el patrón Strategy para permitir intercambio
    de proveedores sin modificar la lógica de negocio.
    """

    @abstractmethod
    async def analyze(self, text: str) -> AnalysisResult:
        """Analiza texto de términos y condiciones.

        Args:
            text: Texto plano a analizar (fragmento o documento completo).

        Returns:
            AnalysisResult con resumen y cláusulas de riesgo.

        Raises:
            LLMTimeoutError: Si la llamada excede el timeout configurado.
            LLMCommunicationError: Si hay error de red/API.
        """
        ...
