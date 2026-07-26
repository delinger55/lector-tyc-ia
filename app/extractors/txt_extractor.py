"""Extractor de texto para archivos de texto plano (.txt)."""

from app.core.exceptions import ExtractionError
from app.extractors.base import BaseExtractor


class TxtExtractor(BaseExtractor):
    """Extrae texto de archivos .txt.

    Intenta decodificar con UTF-8 primero, luego Latin-1 como fallback.
    """

    def extract(self, file_content: bytes) -> str:
        """Extrae texto del contenido binario de un archivo .txt.

        Args:
            file_content: Contenido binario del archivo de texto.

        Returns:
            Texto plano decodificado.

        Raises:
            ExtractionError: Si el archivo no puede decodificarse.
        """
        if not file_content:
            raise ExtractionError()

        # Intentar UTF-8 primero
        try:
            return file_content.decode("utf-8")
        except UnicodeDecodeError:
            pass

        # Fallback a Latin-1 (nunca falla, acepta cualquier byte)
        try:
            return file_content.decode("latin-1")
        except Exception as e:
            raise ExtractionError() from e
