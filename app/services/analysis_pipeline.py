"""Pipeline de análisis: orquestador principal.

Decide entre análisis directo (textos cortos) y Map-Reduce (textos largos).
Maneja reintentos y validación de resultados.
"""

import asyncio
import logging

from app.core.config import get_settings
from app.core.exceptions import AnalysisValidationError, LLMTimeoutError
from app.llm.base import AnalizadorLLM
from app.schemas.analysis import AnalysisResult
from app.services.chunking import chunk_text
from app.services.consolidator import consolidate_results

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Orquestador del análisis de documentos.

    Decide entre análisis directo (textos cortos) y Map-Reduce
    (textos largos). Maneja reintentos y validación de resultados.
    """

    def __init__(self, analyzer: AnalizadorLLM):
        self.analyzer = analyzer
        self.settings = get_settings()

    async def analyze_document(self, text: str) -> AnalysisResult:
        """Pipeline completo de análisis.

        1. Evalúa longitud del texto
        2. Si > umbral: chunk → map (análisis por fragmento) → reduce
        3. Si <= umbral: análisis directo
        4. Valida resultado (5 summary_points)
        5. Reintenta una vez si validación falla

        Args:
            text: Texto plano extraído del documento.

        Returns:
            AnalysisResult validado.

        Raises:
            AnalysisValidationError: Si después de 2 intentos no hay 5 puntos.
            LLMTimeoutError: Si alguna llamada excede el timeout.
        """
        if len(text) > self.settings.chunking_threshold:
            result = await self._analyze_map_reduce(text)
        else:
            result = await self._analyze_with_retry(text)

        return result

    async def _analyze_with_retry(self, text: str) -> AnalysisResult:
        """Análisis directo con lógica de reintento.

        Intenta el análisis hasta 2 veces si el resultado no tiene
        exactamente 5 summary_points.

        Args:
            text: Texto a analizar.

        Returns:
            AnalysisResult validado.

        Raises:
            AnalysisValidationError: Si 2 intentos fallan en validación.
            LLMTimeoutError: Si la llamada excede el timeout.
        """
        for attempt in range(2):
            result = await self._call_llm(text)

            if len(result.summary_points) == 5:
                return result

            if attempt == 0:
                logger.warning(
                    "Primer intento retornó %d summary_points, reintentando...",
                    len(result.summary_points),
                )

        # Segundo intento también falló
        logger.error(
            "Dos intentos fallaron en producir 5 summary_points. "
            "Último resultado tenía %d puntos.",
            len(result.summary_points),
        )
        raise AnalysisValidationError()

    async def _analyze_map_reduce(self, text: str) -> AnalysisResult:
        """Análisis Map-Reduce para textos largos.

        1. Divide el texto en chunks
        2. Analiza cada chunk de forma independiente (Map)
        3. Consolida resultados parciales (Reduce)

        Args:
            text: Texto largo a analizar.

        Returns:
            AnalysisResult consolidado.

        Raises:
            LLMTimeoutError: Si algún chunk excede el timeout.
        """
        chunks = chunk_text(text, threshold=self.settings.chunking_threshold)

        # Map: analizar cada chunk de forma independiente
        tasks = [self._call_llm(chunk) for chunk in chunks]
        partial_results = await asyncio.gather(*tasks)

        # Reduce: consolidar resultados
        return consolidate_results(list(partial_results))

    async def _call_llm(self, text: str) -> AnalysisResult:
        """Llama al LLM con timeout configurado.

        Args:
            text: Texto a enviar al LLM.

        Returns:
            AnalysisResult del LLM.

        Raises:
            LLMTimeoutError: Si la llamada excede el timeout configurado.
        """
        try:
            result = await asyncio.wait_for(
                self.analyzer.analyze(text),
                timeout=self.settings.llm_timeout_seconds,
            )
            return result
        except asyncio.TimeoutError:
            raise LLMTimeoutError()
