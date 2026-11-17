from __future__ import annotations

from typing import Protocol


class Embedder(Protocol):
    @property
    def dim(self) -> int: ...

    def embed_passages(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class SentenceTransformerEmbedder:
    """Multilingual sentence embeddings (default: multilingual-e5-small, works for Vietnamese)."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._is_e5 = "e5" in model_name.lower()  # e5 models expect "query: " / "passage: " prefixes

    def _get(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def dim(self) -> int:
        return int(self._get().get_sentence_embedding_dimension())

    def _encode(self, texts: list[str]) -> list[list[float]]:
        return self._get().encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        return self._encode([f"passage: {t}" for t in texts] if self._is_e5 else texts)

    def embed_query(self, text: str) -> list[float]:
        return self._encode([f"query: {text}" if self._is_e5 else text])[0]
