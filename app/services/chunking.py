"""Servicio de chunking: divide texto largo en fragmentos por párrafos.

Invariante clave: "\n\n".join(chunk_text(text)) == text
No se pierde ni se agrega contenido durante el chunking.
"""

from app.core.config import get_settings


def chunk_text(text: str, threshold: int | None = None) -> list[str]:
    """Divide texto en fragmentos por párrafos sin exceder el threshold.

    Estrategia:
    1. Dividir por doble salto de línea (párrafos)
    2. Agrupar párrafos consecutivos en chunks sin exceder threshold
    3. Cada chunk contiene párrafos completos (nunca corta a mitad)
    4. Si un párrafo individual excede el threshold, va como chunk solo

    Invariante: "\\n\\n".join(chunks) == text

    Args:
        text: Texto completo extraído.
        threshold: Umbral máximo de caracteres por chunk.
                   Si es None, usa el valor de configuración.

    Returns:
        Lista de fragmentos de texto.
    """
    if threshold is None:
        threshold = get_settings().chunking_threshold

    # Dividir por doble salto de línea (separador de párrafos)
    paragraphs = text.split("\n\n")

    chunks: list[str] = []
    current_chunk_parts: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph)
        # Calcular longitud si agregamos este párrafo al chunk actual
        # (incluyendo el separador "\n\n" entre partes)
        separator_length = 2 if current_chunk_parts else 0
        new_length = current_length + separator_length + paragraph_length

        if new_length <= threshold:
            # Cabe en el chunk actual
            current_chunk_parts.append(paragraph)
            current_length = new_length
        else:
            # No cabe: cerrar chunk actual (si tiene contenido) y empezar nuevo
            if current_chunk_parts:
                chunks.append("\n\n".join(current_chunk_parts))
            current_chunk_parts = [paragraph]
            current_length = paragraph_length

    # Agregar el último chunk pendiente
    if current_chunk_parts:
        chunks.append("\n\n".join(current_chunk_parts))

    return chunks
