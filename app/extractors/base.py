"""Clase base abstracta para extractores de texto."""

from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """Interfaz abstracta para extractores de texto de documentos.

    Cada formato de archivo (PDF, DOCX) implementa su propio extractor
    heredando de esta clase. El contenido se recibe como bytes (en memoria)
    porque el sistema es stateless y no persiste archivos en disco.
    """

    @abstractmethod
    def extract(self, file_content: bytes) -> str:
        """Extrae texto plano del contenido binario del archivo.

        Args:
            file_content: Contenido binario del archivo subido.

        Returns:
            Texto plano extraído del documento.

        Raises:
            ExtractionError: Si el archivo es corrupto o ilegible.
            ScannedDocumentException: Si el PDF no contiene texto extraíble.
        """
        ...
