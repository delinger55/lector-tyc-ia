"""Extractor de texto para archivos Word (.docx) usando python-docx."""

import io

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from app.core.exceptions import ExtractionError
from app.extractors.base import BaseExtractor


class DocxExtractor(BaseExtractor):
    """Extrae texto plano de archivos Word (.docx).

    Usa python-docx para leer el contenido en memoria (BytesIO).
    """

    def extract(self, file_content: bytes) -> str:
        """Extrae texto de todos los párrafos del documento Word.

        Args:
            file_content: Contenido binario del archivo .docx.

        Returns:
            Texto plano concatenado de todos los párrafos.

        Raises:
            ExtractionError: Si el archivo es corrupto o ilegible.
        """
        try:
            doc = Document(io.BytesIO(file_content))
            paragraphs_text = [p.text for p in doc.paragraphs if p.text]
            return "\n".join(paragraphs_text)
        except (PackageNotFoundError, Exception) as e:
            raise ExtractionError() from e
