"""Módulo de extractores de texto.

Provee una factory function para obtener el extractor adecuado
según la extensión del archivo, y el extractor de URLs web.
"""

import os

from app.core.exceptions import InvalidFormatException
from app.extractors.base import BaseExtractor
from app.extractors.docx_extractor import DocxExtractor
from app.extractors.pdf_extractor import PdfExtractor
from app.extractors.txt_extractor import TxtExtractor
from app.extractors.web_extractor import WebUrlExtractor

_EXTRACTORS: dict[str, type[BaseExtractor]] = {
    ".pdf": PdfExtractor,
    ".docx": DocxExtractor,
    ".txt": TxtExtractor,
}


def get_extractor(filename: str) -> BaseExtractor:
    """Retorna el extractor adecuado según la extensión del archivo.

    Args:
        filename: Nombre del archivo (con extensión).

    Returns:
        Instancia del extractor correspondiente.

    Raises:
        InvalidFormatException: Si la extensión no es soportada.
    """
    ext = os.path.splitext(filename)[1].lower()
    extractor_class = _EXTRACTORS.get(ext)
    if extractor_class is None:
        raise InvalidFormatException()
    return extractor_class()


def get_web_extractor() -> WebUrlExtractor:
    """Retorna una instancia del extractor de URLs web."""
    return WebUrlExtractor()
