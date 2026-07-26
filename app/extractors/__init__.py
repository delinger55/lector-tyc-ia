"""Módulo de extractores de texto.

Provee una factory function para obtener el extractor adecuado
según la extensión del archivo.
"""

import os

from app.core.exceptions import InvalidFormatException
from app.extractors.base import BaseExtractor
from app.extractors.docx_extractor import DocxExtractor
from app.extractors.pdf_extractor import PdfExtractor

_EXTRACTORS: dict[str, type[BaseExtractor]] = {
    ".pdf": PdfExtractor,
    ".docx": DocxExtractor,
}


def get_extractor(filename: str) -> BaseExtractor:
    """Retorna el extractor adecuado según la extensión del archivo.

    Args:
        filename: Nombre del archivo (con extensión).

    Returns:
        Instancia del extractor correspondiente.

    Raises:
        InvalidFormatException: Si la extensión no es .pdf o .docx.
    """
    ext = os.path.splitext(filename)[1].lower()
    extractor_class = _EXTRACTORS.get(ext)
    if extractor_class is None:
        raise InvalidFormatException()
    return extractor_class()
