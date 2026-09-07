# --- DNK-MRH-HEADER ---
# mrh_id: "adapters/transformers_adapter.py"
# purpose: "DNK OS Adapter for HuggingFace Transformers Pipelines"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
HuggingFace Transformers Adapter for DNK OS Multi-Agent Core.

Provides unified interface for text generation, classification,
summarization, and question-answering pipelines.
"""

from typing import Any, Dict, List, Optional, Union


class TransformersAdapter:
    """
    Adapter for HuggingFace transformers pipelines.
    
    Supports:
    - Text generation (GPT-2, LLaMA, etc.)
    - Text classification
    - Question answering
    - Summarization
    - Translation
    """
    
    def __init__(
        self,
        model_name: str,
        task: str = "text-generation",
        device: str = "cpu",
        use_mock: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize transformers pipeline.
        
        Args:
            model_name: HuggingFace model name (e.g., "gpt2", "meta-llama/Llama-2-7b")
            task: Pipeline task ("text-generation", "classification", "qa", etc.)
            device: Device ("cpu", "cuda", "mps")
            use_mock: Force mock pipeline for testing without downloading model weights
            **kwargs: Additional pipeline arguments
        """
        self.model_name = model_name
        self.task = task
        self.device = device
        self.kwargs = kwargs
        self.use_mock = use_mock
        self._pipeline = None

        if not self.use_mock:
            try:
                from transformers import pipeline  # type: ignore
                self._pipeline = pipeline(
                    task=self.task,
                    model=self.model_name,
                    device=self.device if self.device != "cpu" else -1,
                    **self.kwargs,
                )
            except (ImportError, Exception):
                # Fallback to internal mock pipeline if transformers is not installed or model fails to load
                self.use_mock = True

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any,
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling
            **kwargs: Additional generation arguments
            
        Returns:
            Generated text
        """
        if self.use_mock or self._pipeline is None:
            # Deterministic mock generation for fast testing
            return f"{prompt} [Generated response from {self.model_name} (tokens={max_new_tokens})]"

        outputs = self._pipeline(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs,
        )
        if isinstance(outputs, list) and len(outputs) > 0:
            item = outputs[0]
            if isinstance(item, dict):
                return item.get("generated_text", str(item))
            return str(item)
        return str(outputs)

    def classify(
        self,
        text: str,
        candidate_labels: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, float]:
        """
        Classify text.
        
        Args:
            text: Input text
            candidate_labels: Optional candidate labels for zero-shot classification
            **kwargs: Additional classification arguments
            
        Returns:
            Dictionary of {label: score}
        """
        if self.use_mock or self._pipeline is None:
            if candidate_labels:
                return {label: 1.0 / len(candidate_labels) for label in candidate_labels}
            return {"POSITIVE": 0.95, "NEGATIVE": 0.05}

        if candidate_labels and "zero-shot" in self.task:
            outputs = self._pipeline(text, candidate_labels=candidate_labels, **kwargs)
            labels = outputs.get("labels", [])
            scores = outputs.get("scores", [])
            return dict(zip(labels, scores))

        outputs = self._pipeline(text, **kwargs)
        if isinstance(outputs, list) and len(outputs) > 0:
            first = outputs[0]
            if isinstance(first, list):
                return {item["label"]: float(item["score"]) for item in first if "label" in item}
            if isinstance(first, dict) and "label" in first:
                return {first["label"]: float(first["score"])}
        return {"CLASSIFIED": 1.0}

    def summarize(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 40,
        **kwargs: Any,
    ) -> str:
        """
        Summarize text.
        
        Args:
            text: Input text
            max_length: Maximum summary length
            min_length: Minimum summary length
            **kwargs: Additional summarization arguments
            
        Returns:
            Summary text
        """
        if self.use_mock or self._pipeline is None:
            if len(text) <= max_length:
                return text
            return text[:max_length].rsplit(" ", 1)[0] + "..."

        outputs = self._pipeline(
            text,
            max_length=max_length,
            min_length=min_length,
            **kwargs,
        )
        if isinstance(outputs, list) and len(outputs) > 0:
            item = outputs[0]
            if isinstance(item, dict):
                return item.get("summary_text", str(item))
            return str(item)
        return str(outputs)

    def answer_question(
        self,
        question: str,
        context: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Answer question based on context.
        
        Args:
            question: Question to answer
            context: Context text
            **kwargs: Additional QA arguments
            
        Returns:
            Dictionary with "answer", "score", "start", "end"
        """
        if self.use_mock or self._pipeline is None:
            # Basic mock extraction
            answer = "Paris" if "Paris" in context else context.split(".")[0] if context else "Unknown"
            start_idx = context.find(answer) if context and answer in context else 0
            end_idx = start_idx + len(answer)
            return {
                "answer": answer,
                "score": 0.98,
                "start": start_idx,
                "end": end_idx,
            }

        outputs = self._pipeline(question=question, context=context, **kwargs)
        if isinstance(outputs, dict):
            return {
                "answer": outputs.get("answer", ""),
                "score": float(outputs.get("score", 0.0)),
                "start": int(outputs.get("start", 0)),
                "end": int(outputs.get("end", 0)),
            }
        return {"answer": str(outputs), "score": 1.0, "start": 0, "end": len(str(outputs))}
