"""Tests para app/services/chunking.py.

Incluye Property 5 (chunking preserva contenido) y unit tests.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.chunking import chunk_text


# --- Property 5: Chunking preserva contenido completo ---


class TestProperty5ChunkingPreservesContent:
    """Property 5: For any texto con párrafos, "\n\n".join(chunks) == text."""

    @settings(max_examples=200, deadline=None)
    @given(
        paragraphs=st.lists(
            st.text(
                alphabet=st.characters(
                    blacklist_characters="\n",
                    whitelist_categories=("L", "N", "P", "Z"),
                ),
                min_size=5,
                max_size=80,
            ),
            min_size=2,
            max_size=8,
        )
    )
    def test_round_trip_with_paragraphs(self, paragraphs: list[str]):
        """Texto con párrafos: concatenar chunks reproduce el original."""
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, threshold=100)
        reassembled = "\n\n".join(chunks)
        assert reassembled == text

    @settings(max_examples=200, deadline=None)
    @given(
        paragraphs=st.lists(
            st.text(min_size=1, max_size=80),
            min_size=2,
            max_size=10,
        )
    )
    def test_round_trip_from_paragraph_list(self, paragraphs: list[str]):
        """Paragraphs generados: concatenar chunks reproduce el original."""
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, threshold=100)
        reassembled = "\n\n".join(chunks)
        assert reassembled == text

    @settings(max_examples=200, deadline=None)
    @given(
        text=st.text(min_size=1, max_size=300)
    )
    def test_round_trip_any_text(self, text: str):
        """Cualquier texto: concatenar chunks reproduce el original."""
        chunks = chunk_text(text, threshold=50)
        reassembled = "\n\n".join(chunks)
        assert reassembled == text


# --- Unit Tests ---


class TestChunkTextUnit:
    """Unit tests para chunk_text."""

    def test_text_without_paragraphs_returns_single_chunk(self):
        """Texto sin '\\n\\n' retorna un solo chunk."""
        text = "Este es un texto sin separadores de párrafo."
        chunks = chunk_text(text, threshold=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_text_below_threshold_returns_single_chunk(self):
        """Texto con párrafos pero menor al threshold no se divide."""
        text = "Párrafo uno.\n\nPárrafo dos."
        chunks = chunk_text(text, threshold=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_text_at_exact_threshold_returns_single_chunk(self):
        """Texto exactamente en el umbral no se divide."""
        # Construir texto de exactamente threshold caracteres con párrafos
        part1 = "A" * 45
        part2 = "B" * 45
        text = f"{part1}\n\n{part2}"  # 45 + 2 + 45 = 92 chars
        chunks = chunk_text(text, threshold=92)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_text_exceeding_threshold_splits(self):
        """Texto que excede el threshold se divide en múltiples chunks."""
        paragraphs = [f"Párrafo número {i} con contenido." for i in range(10)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, threshold=100)
        assert len(chunks) > 1
        # Invariante
        assert "\n\n".join(chunks) == text

    def test_individual_paragraph_exceeding_threshold(self):
        """Párrafo individual mayor al threshold va como chunk solo."""
        long_paragraph = "X" * 200
        short_paragraph = "Y" * 10
        text = f"{short_paragraph}\n\n{long_paragraph}\n\n{short_paragraph}"
        chunks = chunk_text(text, threshold=50)
        # El párrafo largo debe estar en su propio chunk
        assert long_paragraph in chunks
        # Invariante
        assert "\n\n".join(chunks) == text

    def test_empty_text_returns_single_empty_chunk(self):
        """Texto vacío retorna lista con string vacío."""
        chunks = chunk_text("", threshold=100)
        assert chunks == [""]

    def test_chunks_respect_threshold(self):
        """Ningún chunk (salvo párrafo individual grande) excede el threshold."""
        paragraphs = ["Texto corto."] * 20
        text = "\n\n".join(paragraphs)
        threshold = 50
        chunks = chunk_text(text, threshold=threshold)
        for chunk in chunks:
            # Solo puede exceder si es un párrafo individual > threshold
            if "\n\n" in chunk or len(chunk.split("\n\n")) == 1:
                # Si es un solo párrafo, puede exceder (es inevitable)
                # Si tiene varios, no debe exceder
                parts = chunk.split("\n\n")
                if len(parts) > 1:
                    assert len(chunk) <= threshold

    def test_preserves_empty_paragraphs(self):
        """Párrafos vacíos (doble \\n\\n\\n\\n) se preservan."""
        text = "Inicio\n\n\n\nFin"
        # Esto es "Inicio", "", "Fin" cuando se divide por \n\n
        chunks = chunk_text(text, threshold=100)
        assert "\n\n".join(chunks) == text

    def test_multiple_chunks_content_order(self):
        """Los chunks mantienen el orden original del texto."""
        paragraphs = [f"P{i}" for i in range(1, 11)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, threshold=10)
        reassembled = "\n\n".join(chunks)
        assert reassembled == text
        # Verificar orden
        for i, p in enumerate(paragraphs):
            assert p in reassembled
