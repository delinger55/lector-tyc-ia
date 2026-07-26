"""Endpoints de la aplicación: página principal y análisis de documentos."""

import os

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.core.exceptions import (
    FileTooLargeException,
    InvalidFormatException,
    TextTooLongException,
)
from app.extractors import get_extractor
from app.llm import get_llm_analyzer
from app.schemas.analysis import AnalysisResult
from app.services.analysis_pipeline import AnalysisPipeline

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Extensiones permitidas
_ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Renderiza la pantalla principal con formulario de carga y disclaimer."""
    return templates.TemplateResponse(request, "index.html")


@router.post("/api/v1/analyze", response_model=AnalysisResult)
async def analyze_document(file: UploadFile = File(...)) -> AnalysisResult:
    """Endpoint principal de análisis de documentos.

    Flujo:
    1. Validar extensión (.pdf, .docx)
    2. Leer contenido y validar tamaño
    3. Extraer texto
    4. Validar longitud de texto (max_words)
    5. Ejecutar pipeline de análisis
    6. Retornar AnalysisResult como JSON
    7. Limpiar referencias en memoria (finally)

    Args:
        file: Archivo subido por el usuario.

    Returns:
        AnalysisResult con resumen y cláusulas de riesgo.
    """
    settings = get_settings()
    file_content = None
    extracted_text = None

    try:
        # 1. Validar extensión
        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in _ALLOWED_EXTENSIONS:
            raise InvalidFormatException()

        # 2. Leer contenido y validar tamaño
        file_content = await file.read()
        if len(file_content) > settings.max_file_size_bytes:
            raise FileTooLargeException(max_size_mb=settings.max_file_size_mb)

        # 3. Extraer texto
        extractor = get_extractor(filename)
        extracted_text = extractor.extract(file_content)

        # 4. Validar longitud de texto
        word_count = len(extracted_text.split())
        if word_count > settings.max_words:
            raise TextTooLongException(max_words=settings.max_words)

        # 5. Ejecutar pipeline de análisis
        analyzer = get_llm_analyzer()
        pipeline = AnalysisPipeline(analyzer)
        result = await pipeline.analyze_document(extracted_text)

        # 6. Retornar resultado
        return result

    finally:
        # 7. Limpiar referencias en memoria
        del file_content
        del extracted_text
