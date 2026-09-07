# --- DNK-MRH-HEADER ---
# mrh_id: "tests/adapters/test_transformers_adapter.py"
# purpose: "Unit Test Suite for TransformersAdapter"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""Unit tests for Adapters: TransformersAdapter."""

from unittest.mock import MagicMock
import pytest
from adapters.transformers_adapter import TransformersAdapter


class TestTransformersAdapter:
    """Test suite for TransformersAdapter."""

    def test_init_default(self) -> None:
        """Test initialization with default parameters."""
        adapter = TransformersAdapter(model_name="gpt2", use_mock=True)
        assert adapter is not None
        assert adapter.model_name == "gpt2"
        assert adapter.task == "text-generation"

    def test_generate_text(self) -> None:
        """Test text generation with mock fallback."""
        adapter = TransformersAdapter(model_name="gpt2", task="text-generation", use_mock=True)
        result = adapter.generate(prompt="Hello, how are", max_new_tokens=50)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Hello, how are" in result

    def test_generate_text_with_pipeline_mock(self) -> None:
        """Test text generation with mocked pipeline object."""
        adapter = TransformersAdapter(model_name="gpt2", task="text-generation", use_mock=True)
        mock_pipeline = MagicMock(return_value=[{"generated_text": "Hello world"}])
        adapter._pipeline = mock_pipeline
        adapter.use_mock = False
        result = adapter.generate(prompt="Hello")
        assert result == "Hello world"
        mock_pipeline.assert_called_once()

    def test_classify_text(self) -> None:
        """Test text classification."""
        adapter = TransformersAdapter(model_name="distilbert-base-uncased", task="classification", use_mock=True)
        result = adapter.classify(text="I love this product!")
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_classify_text_zero_shot(self) -> None:
        """Test zero-shot classification."""
        adapter = TransformersAdapter(model_name="facebook/bart-large-mnli", task="zero-shot-classification", use_mock=True)
        result = adapter.classify(text="Sports game tonight", candidate_labels=["sports", "politics", "finance"])
        assert isinstance(result, dict)
        assert "sports" in result
        assert "politics" in result

    def test_classify_with_pipeline_mock(self) -> None:
        """Test classification with mocked pipeline object."""
        adapter = TransformersAdapter(model_name="distilbert", task="classification", use_mock=True)
        mock_pipeline = MagicMock(return_value=[[{"label": "POSITIVE", "score": 0.99}]])
        adapter._pipeline = mock_pipeline
        adapter.use_mock = False
        result = adapter.classify(text="Great!")
        assert result == {"POSITIVE": 0.99}

    def test_summarize_text(self) -> None:
        """Test text summarization."""
        adapter = TransformersAdapter(model_name="facebook/bart-large-cnn", task="summarization", use_mock=True)
        text = "Long text to summarize..." * 10
        result = adapter.summarize(text=text, max_length=100)
        assert isinstance(result, str)
        assert len(result) < len(text)

    def test_summarize_with_pipeline_mock(self) -> None:
        """Test summarization with mocked pipeline object."""
        adapter = TransformersAdapter(model_name="bart", task="summarization", use_mock=True)
        mock_pipeline = MagicMock(return_value=[{"summary_text": "Short summary"}])
        adapter._pipeline = mock_pipeline
        adapter.use_mock = False
        result = adapter.summarize(text="Very long text")
        assert result == "Short summary"

    def test_answer_question(self) -> None:
        """Test question answering."""
        adapter = TransformersAdapter(model_name="distilbert-base-cased-distilled-squad", task="qa", use_mock=True)
        result = adapter.answer_question(
            question="What is the capital of France?",
            context="Paris is the capital and largest city of France.",
        )
        assert "answer" in result
        assert result["answer"].lower() == "paris"
        assert "score" in result
        assert "start" in result
        assert "end" in result

    def test_answer_question_with_pipeline_mock(self) -> None:
        """Test question answering with mocked pipeline object."""
        adapter = TransformersAdapter(model_name="squad", task="qa", use_mock=True)
        mock_pipeline = MagicMock(return_value={"answer": "Paris", "score": 0.99, "start": 0, "end": 5})
        adapter._pipeline = mock_pipeline
        adapter.use_mock = False
        result = adapter.answer_question(question="Capital?", context="Paris")
        assert result == {"answer": "Paris", "score": 0.99, "start": 0, "end": 5}
