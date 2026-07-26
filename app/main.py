"""Punto de entrada de la aplicación FastAPI."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.exceptions import AppBaseException
from app.routers.analyze import router

app = FastAPI(
    title="Lector de Términos y Condiciones con IA",
    version="1.0.0",
    description="Analiza documentos de términos y condiciones mediante IA.",
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="app/templates")

# Incluir router
app.include_router(router)


@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    """Handler global para excepciones de la aplicación.

    Convierte AppBaseException en respuestas JSON con código HTTP apropiado.
    - 400: errores de validación del usuario (formato, tamaño, escaneado, longitud, no-TyC)
    - 500: errores internos (LLM timeout, comunicación, análisis fallido)
    """
    error_codes_500 = {"LLM_TIMEOUT", "LLM_COMMUNICATION_ERROR", "ANALYSIS_FAILED"}

    status_code = 500 if exc.error_code in error_codes_500 else 400

    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )
