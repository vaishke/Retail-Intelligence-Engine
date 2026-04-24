import os
from functools import lru_cache

from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_DIMENSIONS = 384


@lru_cache(maxsize=1)
def _get_embedding_model():
    model_source = os.getenv("EMBEDDING_MODEL_PATH", EMBEDDING_MODEL_NAME)
    local_files_only = os.getenv("HF_LOCAL_FILES_ONLY", "false").lower() == "true"
    try:
        return SentenceTransformer(model_source)
    except OSError as exc:
        raise RuntimeError(
            "Embedding model is unavailable. Download "
            "'sentence-transformers/all-MiniLM-L6-v2' locally or set EMBEDDING_MODEL_PATH "
            "to a cached model directory before using vector recommendations."
        ) from exc


@lru_cache(maxsize=2048)
def _generate_cached_embedding(normalized_text: str):
    model = _get_embedding_model()
    vector = model.encode(normalized_text, normalize_embeddings=True)
    return [float(value) for value in vector.tolist()]


def generate_embedding(text: str):
    normalized_text = " ".join(str(text or "").split()).strip()
    if not normalized_text:
        raise ValueError("Text is required to generate an embedding.")

    embedding = _generate_cached_embedding(normalized_text)
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Unexpected embedding dimensions: expected {EMBEDDING_DIMENSIONS}, got {len(embedding)}"
        )
    return embedding
