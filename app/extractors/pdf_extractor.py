"""Extractor de texto para archivos PDF usando pypdf."""

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.exceptions import ExtractionError, ScannedDocumentException
from app.extractors.base import BaseExtractor


class PdfExtractor(BaseExtractor):
    """Extrae texto plano de archivos PDF.

    Usa pypdf para leer el contenido en memoria (BytesIO).
    Detecta documentos escaneados si el texto extraído tiene < 100 caracteres.
    """

    def extract(self, file_content: bytes) -> str:
        """Extrae texto de todas las páginas del PDF.

        Args:
            file_content: Contenido binario del archivo PDF.

        Returns:
            Texto plano concatenado de todas las páginas.

        Raises:
            ExtractionError: Si el PDF es corrupto o ilegible.
            ScannedDocumentException: Si el texto extraído tiene < 100 caracteres.
        """
        try:
            reader = PdfReader(io.BytesIO(file_content))
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            full_text = "\n".join(pages_text)
        except (PdfReadError, Exception) as e:
            raise ExtractionError() from e

        if len(full_text) < 100:
            raise ScannedDocumentException()

        return full_text
