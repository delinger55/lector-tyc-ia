"""Módulo de interfaz LLM.

Provee una factory function para obtener el analizador LLM
según la variable de entorno LLM_PROVIDER.
"""

from app.core.config import get_settings
from app.llm.base import AnalizadorLLM


def get_llm_analyzer() -> AnalizadorLLM:
    """Retorna el analizador LLM según el proveedor configurado.

    Returns:
        Instancia del analizador correspondiente al LLM_PROVIDER.

    Raises:
        ValueError: Si el proveedor configurado no está soportado.
    """
    settings = get_settings()

    if settings.llm_provider == "mock":
        from app.llm.mock_provider import MockLLMAnalyzer

        return MockLLMAnalyzer()
    elif settings.llm_provider == "openai":
        raise NotImplementedError(
            "OpenAI provider pendiente de implementación"
        )
    else:
        raise ValueError(
            f"Proveedor LLM no soportado: '{settings.llm_provider}'"
        )
