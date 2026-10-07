import logging
import math
from typing import List, Optional

from app.core.config import settings

log = logging.getLogger(__name__)


def _provider() -> str:
    p = (settings.EMBEDDING_PROVIDER or settings.LLM_PROVIDER).lower()
    return p if p in ("gemini", "ollama") else "none"


def model_name() -> str:
    p = _provider()
    default = {"gemini": "gemini-embedding-001", "ollama": "nomic-embed-text"}.get(p, "")
    return f"{p}:{settings.EMBEDDING_MODEL or default}"


def embed(texts: List[str], kind: str = "doc") -> Optional[List[List[float]]]:
    """Un vecteur par texte, ou None si les embeddings sont indisponibles (la recherche reste alors lexicale)."""
    p = _provider()
    if p == "none" or not texts:
        return None
    model = model_name().split(":", 1)[1]
    try:
        if p == "gemini":
            if not settings.GEMINI_API_KEY:
                return None
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            res = client.models.embed_content(
                model=model,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY" if kind == "query" else "RETRIEVAL_DOCUMENT",
                    output_dimensionality=768,
                ),
            )
            return [list(e.values) for e in res.embeddings]
        import ollama

        res = ollama.Client(host=settings.OLLAMA_HOST, timeout=120).embed(model=model, input=texts)
        return [list(v) for v in res.embeddings]
    except Exception:
        log.warning("Embeddings indisponibles", exc_info=True)
        return None


def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0