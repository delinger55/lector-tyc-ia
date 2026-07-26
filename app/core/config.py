"""Configuración de la aplicación cargada desde variables de entorno."""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Configuración central de la aplicación.

    Todas las variables se cargan desde el entorno o un archivo .env.
    """

    # LLM
    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_timeout_seconds: int = 30

    # Límites de archivo
    max_file_size_mb: int = 10
    max_words: int = 20_000

    # Chunking
    chunking_threshold: int = 12_000

    # Aplicación
    app_name: str = "Lector de Términos y Condiciones con IA"
    debug: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @property
    def max_file_size_bytes(self) -> int:
        """Tamaño máximo de archivo en bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @model_validator(mode="after")
    def validate_llm_config(self) -> "AppSettings":
        """Valida que LLM_API_KEY esté presente si el proveedor no es mock."""
        if self.llm_provider != "mock" and not self.llm_api_key:
            raise ValueError(
                f"LLM_API_KEY es requerida cuando LLM_PROVIDER='{self.llm_provider}'"
            )
        return self


@lru_cache
def get_settings() -> AppSettings:
    """Retorna la instancia cacheada de configuración."""
    return AppSettings()
