"""Tests para app/extractors/.

Incluye Property 3 (detección documento escaneado) y unit tests para
PdfExtractor, DocxExtractor y factory get_extractor.
"""

import io

import pytest
from docx import Document
from pypdf import PdfWriter

from app.core.exceptions import (
    ExtractionError,
    InvalidFormatException,
    ScannedDocumentException,
)
from app.extractors import get_extractor
from app.extractors.docx_extractor import DocxExtractor
from app.extractors.pdf_extractor import PdfExtractor


def _create_simple_pdf_bytes(text: str) -> bytes:
    """Genera un PDF con texto extraíble en el contenido de página.

    Usa pypdf PdfWriter con un stream de contenido directo que
    pypdf.PdfReader.extract_text() puede leer.
    """
    from pypdf.generic import (
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
    )

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    page = writer.pages[0]

    # Crear stream de contenido con operadores PDF de texto
    text_encoded = text.encode("latin-1", errors="replace").decode("latin-1")
    content = f"BT /F1 12 Tf 72 720 Td ({text_encoded}) Tj ET"
    stream = DecodedStreamObject()
    stream.set_data(content.encode("latin-1"))

    # Configurar font en resources
    if "/Resources" not in page:
        page[NameObject("/Resources")] = DictionaryObject()
    resources = page["/Resources"]
    if "/Font" not in resources:
        resources[NameObject("/Font")] = DictionaryObject()
    font_dict = DictionaryObject()
    font_dict[NameObject("/Type")] = NameObject("/Font")
    font_dict[NameObject("/Subtype")] = NameObject("/Type1")
    font_dict[NameObject("/BaseFont")] = NameObject("/Helvetica")
    resources["/Font"][NameObject("/F1")] = font_dict

    # Asignar contenido a la página
    page[NameObject("/Contents")] = writer._add_object(stream)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _create_docx_bytes(text: str) -> bytes:
    """Genera un archivo .docx en memoria con el texto dado."""
    doc = Document()
    # Dividir por líneas para crear párrafos
    for paragraph in text.split("\n"):
        if paragraph.strip():
            doc.add_paragraph(paragraph)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# --- Property 3: Detección de documento escaneado ---


class TestProperty3ScannedDocumentDetection:
    """Property 3: PDF con < 100 chars de texto → ScannedDocumentException."""

    def test_pdf_with_no_extractable_text_raises_scanned(self):
        """PDF sin texto extraíble (páginas en blanco) lanza ScannedDocumentException."""
        # PDF con página en blanco (0 caracteres de texto)
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        buffer = io.BytesIO()
        writer.write(buffer)
        blank_pdf = buffer.getvalue()

        extractor = PdfExtractor()
        with pytest.raises(ScannedDocumentException):
            extractor.extract(blank_pdf)

    def test_pdf_with_very_short_text_raises_scanned(self):
        """PDF con texto < 100 chars lanza ScannedDocumentException."""
        # Creamos un PDF con anotación que tiene texto corto
        short_text = "Hola mundo"  # 10 chars
        pdf_bytes = _create_simple_pdf_bytes(short_text)

        extractor = PdfExtractor()
        # El texto de anotaciones puede o no ser extraído por pypdf
        # dependiendo de la versión; lo importante es que si extract_text()
        # retorna < 100 chars, se lanza la excepción
        with pytest.raises(ScannedDocumentException):
            extractor.extract(pdf_bytes)


# --- Tests PdfExtractor ---


class TestPdfExtractor:
    """Unit tests para PdfExtractor."""

    def test_extracts_text_from_valid_pdf(self):
        """Extrae texto correctamente de un PDF con contenido largo."""
        long_text = "Este es un documento de prueba con suficiente texto para superar el umbral de cien caracteres que necesitamos para validar correctamente."
        pdf_bytes = _create_simple_pdf_bytes(long_text)

        extractor = PdfExtractor()
        result = extractor.extract(pdf_bytes)
        assert len(result) >= 100
        assert "documento de prueba" in result

    def test_raises_extraction_error_for_corrupt_file(self):
        """Archivo corrupto (bytes aleatorios) lanza ExtractionError."""
        corrupt_bytes = b"esto no es un PDF valido en absoluto " * 10
        extractor = PdfExtractor()
        with pytest.raises(ExtractionError):
            extractor.extract(corrupt_bytes)

    def test_raises_extraction_error_for_empty_bytes(self):
        """Bytes vacíos lanzan ExtractionError."""
        extractor = PdfExtractor()
        with pytest.raises(ExtractionError):
            extractor.extract(b"")


# --- Tests DocxExtractor ---


class TestDocxExtractor:
    """Unit tests para DocxExtractor."""

    def test_extracts_text_from_valid_docx(self):
        """Extrae texto correctamente de un DOCX válido."""
        text = "Este es un párrafo de prueba.\nSegundo párrafo con más contenido."
        docx_bytes = _create_docx_bytes(text)

        extractor = DocxExtractor()
        result = extractor.extract(docx_bytes)
        assert "párrafo de prueba" in result
        assert "Segundo párrafo" in result

    def test_extracts_multiple_paragraphs(self):
        """Extrae todos los párrafos del documento."""
        paragraphs = [f"Párrafo número {i}" for i in range(1, 6)]
        text = "\n".join(paragraphs)
        docx_bytes = _create_docx_bytes(text)

        extractor = DocxExtractor()
        result = extractor.extract(docx_bytes)
        for p in paragraphs:
            assert p in result

    def test_raises_extraction_error_for_corrupt_file(self):
        """Archivo corrupto (bytes aleatorios) lanza ExtractionError."""
        corrupt_bytes = b"esto no es un archivo docx valido" * 5
        extractor = DocxExtractor()
        with pytest.raises(ExtractionError):
            extractor.extract(corrupt_bytes)

    def test_raises_extraction_error_for_empty_bytes(self):
        """Bytes vacíos lanzan ExtractionError."""
        extractor = DocxExtractor()
        with pytest.raises(ExtractionError):
            extractor.extract(b"")


# --- Tests Factory get_extractor ---


class TestGetExtractor:
    """Unit tests para factory get_extractor."""

    def test_returns_pdf_extractor_for_pdf(self):
        """Extensión .pdf retorna PdfExtractor."""
        extractor = get_extractor("documento.pdf")
        assert isinstance(extractor, PdfExtractor)

    def test_returns_pdf_extractor_case_insensitive(self):
        """Extensión .PDF (mayúscula) retorna PdfExtractor."""
        extractor = get_extractor("documento.PDF")
        assert isinstance(extractor, PdfExtractor)

    def test_returns_docx_extractor_for_docx(self):
        """Extensión .docx retorna DocxExtractor."""
        extractor = get_extractor("documento.docx")
        assert isinstance(extractor, DocxExtractor)

    def test_returns_docx_extractor_case_insensitive(self):
        """Extensión .DOCX (mayúscula) retorna DocxExtractor."""
        extractor = get_extractor("archivo.DOCX")
        assert isinstance(extractor, DocxExtractor)

    def test_raises_invalid_format_for_txt(self):
        """Extensión .txt lanza InvalidFormatException."""
        with pytest.raises(InvalidFormatException):
            get_extractor("archivo.txt")

    def test_raises_invalid_format_for_doc(self):
        """Extensión .doc (viejo Word) lanza InvalidFormatException."""
        with pytest.raises(InvalidFormatException):
            get_extractor("archivo.doc")

    def test_raises_invalid_format_for_no_extension(self):
        """Archivo sin extensión lanza InvalidFormatException."""
        with pytest.raises(InvalidFormatException):
            get_extractor("archivo")

    def test_raises_invalid_format_for_jpg(self):
        """Extensión .jpg lanza InvalidFormatException."""
        with pytest.raises(InvalidFormatException):
            get_extractor("imagen.jpg")
