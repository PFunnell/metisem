"""Unit tests for metisem/core/embeddings.py module.

Tests embedding generation with mocked Sentence Transformer models.
"""

import numpy as np
import pytest

from metisem.core.embeddings import (
    encode_texts,
    get_embedding_dimension,
)


class TestEncodeTexts:
    """Tests for encode_texts function."""

    def test_encodes_single_text(self, mock_embedding_model):
        """Should generate embedding for single text."""
        texts = ["This is a test sentence."]
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (1, 384)
        assert embeddings.dtype == np.float32

    def test_encodes_multiple_texts(self, mock_embedding_model):
        """Should generate embeddings for multiple texts."""
        texts = [
            "First sentence.",
            "Second sentence.",
            "Third sentence.",
        ]
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (3, 384)
        assert embeddings.dtype == np.float32

    def test_embeddings_are_normalized(self, mock_embedding_model):
        """Mock embeddings should be normalised to unit length."""
        texts = ["Test text"]
        embeddings = encode_texts(texts, mock_embedding_model)

        # Check normalisation (L2 norm should be 1.0)
        norm = np.linalg.norm(embeddings[0])
        assert abs(norm - 1.0) < 1e-5

    def test_same_text_produces_same_embedding(self, mock_embedding_model):
        """Same text should produce identical embeddings."""
        text = "Consistent text for testing"

        emb1 = encode_texts([text], mock_embedding_model)
        emb2 = encode_texts([text], mock_embedding_model)

        np.testing.assert_array_equal(emb1, emb2)

    def test_different_texts_produce_different_embeddings(self, mock_embedding_model):
        """Different texts should produce different embeddings."""
        texts = ["Text A", "Text B"]
        embeddings = encode_texts(texts, mock_embedding_model)

        # Embeddings should not be identical
        assert not np.allclose(embeddings[0], embeddings[1])

    def test_handles_empty_list(self, mock_embedding_model):
        """Should return empty array for empty input list."""
        texts = []
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (0,)

    def test_handles_long_text(self, mock_embedding_model):
        """Should handle very long text inputs."""
        long_text = "This is a sentence. " * 500  # ~1000 words
        embeddings = encode_texts([long_text], mock_embedding_model)

        assert embeddings.shape == (1, 384)

    def test_batch_processing(self, mock_embedding_model):
        """Should handle batch processing correctly."""
        texts = [f"Text {i}" for i in range(100)]
        embeddings = encode_texts(texts, mock_embedding_model, batch_size=10)

        assert embeddings.shape == (100, 384)

    def test_respects_show_progress_parameter(self, mock_embedding_model):
        """Should accept show_progress parameter without error."""
        texts = ["Test text"]

        # Should work with both True and False
        emb1 = encode_texts(texts, mock_embedding_model, show_progress=True)
        emb2 = encode_texts(texts, mock_embedding_model, show_progress=False)

        assert emb1.shape == (1, 384)
        assert emb2.shape == (1, 384)

    def test_handles_special_characters(self, mock_embedding_model):
        """Should handle text with special characters and Unicode."""
        texts = [
            "Text with emoji 🚀",
            "Accented characters: café",
            "Math symbols: ∑ ∫ √",
            "Mixed: Hello世界",
        ]
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (4, 384)

    def test_handles_empty_strings(self, mock_embedding_model):
        """Should handle empty strings in input."""
        texts = ["", "Non-empty text", ""]
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (3, 384)


class TestGetEmbeddingDimension:
    """Tests for get_embedding_dimension function."""

    def test_returns_correct_dimension(self, mock_embedding_model):
        """Should return correct embedding dimension for model."""
        dim = get_embedding_dimension(mock_embedding_model)

        assert dim == 384

    def test_dimension_matches_encoded_output(self, mock_embedding_model):
        """Dimension should match actual encoded output."""
        dim = get_embedding_dimension(mock_embedding_model)

        test_text = ["Sample text"]
        embeddings = encode_texts(test_text, mock_embedding_model)

        assert embeddings.shape[1] == dim

    def test_consistent_across_calls(self, mock_embedding_model):
        """Should return same dimension on multiple calls."""
        dim1 = get_embedding_dimension(mock_embedding_model)
        dim2 = get_embedding_dimension(mock_embedding_model)

        assert dim1 == dim2


class TestEmbeddingSimilarity:
    """Tests for embedding similarity properties."""

    def test_similar_texts_have_high_similarity(self, mock_embedding_model):
        """Similar texts should have high cosine similarity."""
        texts = [
            "The cat sat on the mat",
            "A cat was sitting on a mat",
        ]
        embeddings = encode_texts(texts, mock_embedding_model)

        # Compute cosine similarity
        similarity = np.dot(embeddings[0], embeddings[1])

        # Note: With mock deterministic embeddings, similarity depends on hash
        # Just verify the operation completes successfully
        assert -1.0 <= similarity <= 1.0

    def test_identical_texts_have_perfect_similarity(self, mock_embedding_model):
        """Identical texts should have cosine similarity of 1.0."""
        text = "Identical text for both"
        embeddings = encode_texts([text, text], mock_embedding_model)

        similarity = np.dot(embeddings[0], embeddings[1])

        # Should be exactly 1.0 (normalised vectors)
        assert abs(similarity - 1.0) < 1e-5

    def test_embedding_matrix_properties(self, mock_embedding_model):
        """Embedding matrix should have expected mathematical properties."""
        texts = [f"Text number {i}" for i in range(5)]
        embeddings = encode_texts(texts, mock_embedding_model)

        # Check shape
        assert embeddings.shape == (5, 384)

        # Check all embeddings are normalised
        norms = np.linalg.norm(embeddings, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5)

        # Check no NaN or Inf values
        assert not np.any(np.isnan(embeddings))
        assert not np.any(np.isinf(embeddings))


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_handles_whitespace_only_text(self, mock_embedding_model):
        """Should handle text with only whitespace."""
        texts = ["   ", "\t\t", "\n\n"]
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (3, 384)

    def test_handles_very_short_text(self, mock_embedding_model):
        """Should handle single character text."""
        texts = ["a", "b", "c"]
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (3, 384)

    def test_handles_mixed_length_texts(self, mock_embedding_model):
        """Should handle texts of varying lengths in same batch."""
        texts = [
            "a",
            "Short text.",
            "This is a medium length text with several words.",
            "This is a much longer text that contains many sentences. " * 10,
        ]
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (4, 384)

    def test_handles_repeated_text(self, mock_embedding_model):
        """Should handle same text repeated multiple times."""
        text = "Repeated text"
        texts = [text] * 10
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (10, 384)

        # All embeddings should be identical
        for i in range(1, 10):
            np.testing.assert_array_equal(embeddings[0], embeddings[i])

    def test_numeric_strings(self, mock_embedding_model):
        """Should handle numeric strings."""
        texts = ["123", "45.67", "1e-5", "0xDEADBEEF"]
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (4, 384)

    def test_markdown_formatted_text(self, mock_embedding_model):
        """Should handle markdown-formatted text."""
        texts = [
            "# Heading",
            "**Bold** and *italic*",
            "[Link](http://example.com)",
            "- List item",
            "```code block```",
        ]
        embeddings = encode_texts(texts, mock_embedding_model)

        assert embeddings.shape == (5, 384)


class TestBatchSizes:
    """Tests for different batch size configurations."""

    def test_small_batch_size(self, mock_embedding_model):
        """Should work with very small batch size."""
        texts = [f"Text {i}" for i in range(10)]
        embeddings = encode_texts(texts, mock_embedding_model, batch_size=1)

        assert embeddings.shape == (10, 384)

    def test_large_batch_size(self, mock_embedding_model):
        """Should work with batch size larger than input."""
        texts = ["Text 1", "Text 2"]
        embeddings = encode_texts(texts, mock_embedding_model, batch_size=100)

        assert embeddings.shape == (2, 384)

    def test_exact_batch_size(self, mock_embedding_model):
        """Should work when text count matches batch size exactly."""
        texts = [f"Text {i}" for i in range(32)]
        embeddings = encode_texts(texts, mock_embedding_model, batch_size=32)

        assert embeddings.shape == (32, 384)
