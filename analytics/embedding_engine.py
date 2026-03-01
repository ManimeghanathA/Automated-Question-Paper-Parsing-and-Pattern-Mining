# ===============================
# EMBEDDING ENGINE
# ===============================

from sentence_transformers import SentenceTransformer
import numpy as np
from .config import EMBEDDING_MODEL

_model_instance = None

def get_model():
    global _model_instance
    if _model_instance is None:
        print(f"\n🔹 Loading Embedding Model: {EMBEDDING_MODEL}")
        _model_instance = SentenceTransformer(EMBEDDING_MODEL)
        print("✅ Embedding model loaded successfully.")
    return _model_instance


class EmbeddingEngine:
    def __init__(self):
        self.model = get_model()

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]

        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )