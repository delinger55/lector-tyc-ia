"""Endpoints de la aplicación: página principal y análisis de documentos."""

import os
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.core.exceptions import (
    ExtractionError,
    FileTooLargeException,
    InvalidFormatException,
    TextTooLongException,
)
from app.extractors import get_extractor, get_web_extractor
from app.llm import get_llm_analyzer
from app.schemas.analysis import AnalysisResult
from app.services.analysis_pipeline import AnalysisPipeline

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Extensiones permitidas
_ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Renderiza la pantalla principal con formulario de carga y disclaimer."""
    return templates.TemplateResponse(request, "index.html")


@router.post("/api/v1/analyze", response_model=AnalysisResult)
async def analyze_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
) -> AnalysisResult:
    """Endpoint principal de análisis de documentos.

    Acepta un archivo subido (.pdf, .docx, .txt) O una URL de página web.
    Si se provee URL, se descarga y extrae el texto de la página.
    Si se provee archivo, se extrae según su formato.

    Args:
        file: Archivo subido por el usuario (opcional si se provee url).
        url: URL de página web a analizar (opcional si se provee file).

    Returns:
        AnalysisResult con resumen y cláusulas de riesgo.
    """
    settings = get_settings()
    file_content = None
    extracted_text = None

    try:
        if url and url.strip():
            # --- Flujo URL ---
            extracted_text = _extract_from_url(url.strip())
        elif file and file.filename:
            # --- Flujo archivo ---
            extracted_text = await _extract_from_file(file, settings)
        else:
            raise InvalidFormatException()

        # Validar longitud de texto
        word_count = len(extracted_text.split())
        if word_count > settings.max_words:
            raise TextTooLongException(max_words=settings.max_words)

        # Ejecutar pipeline de análisis
        analyzer = get_llm_analyzer()
        pipeline = AnalysisPipeline(analyzer)
        result = await pipeline.analyze_document(extracted_text)

        return result

    finally:
        del file_content
        del extracted_text


async def _extract_from_file(file: UploadFile, settings) -> str:
    """Extrae texto de un archivo subido.

    Args:
        file: Archivo subido.
        settings: Configuración de la app.

    Returns:
        Texto extraído del archivo.

    Raises:
        InvalidFormatException: Si la extensión no es soportada.
        FileTooLargeException: Si el archivo excede el límite.
    """
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise InvalidFormatException()

    file_content = await file.read()
    if len(file_content) > settings.max_file_size_bytes:
        raise FileTooLargeException(max_size_mb=settings.max_file_size_mb)

    extractor = get_extractor(filename)
    return extractor.extract(file_content)


def _extract_from_url(url: str) -> str:
    """Extrae texto de una URL web.

    Args:
        url: URL de la página a analizar.

    Returns:
        Texto extraído de la página.

    Raises:
        ExtractionError: Si la URL no puede descargarse o parsearse.
    """
    web_extractor = get_web_extractor()
    return web_extractor.extract(url)
