import json
import os
from typing import Callable

import requests
from dotenv import load_dotenv

load_dotenv()

SEMANTIC_DIR_NAME = ".semantic_memory"
META_FILENAME = "metadata.json"
INDEX_FILENAME = "index.tv"
DEFAULT_MODEL = "nomic-embed-text"
DEFAULT_LIMIT = 8


def is_enabled() -> bool:
    return os.getenv("SEMANTIC_MEMORY_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


def _semantic_dir(memory_dir: str) -> str:
    return os.path.join(memory_dir, SEMANTIC_DIR_NAME)


def _meta_path(memory_dir: str) -> str:
    return os.path.join(_semantic_dir(memory_dir), META_FILENAME)


def _index_path(memory_dir: str) -> str:
    return os.path.join(_semantic_dir(memory_dir), INDEX_FILENAME)


def _load_metadata(memory_dir: str) -> list:
    path = _meta_path(memory_dir)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _save_metadata(memory_dir: str, metadata: list) -> None:
    os.makedirs(_semantic_dir(memory_dir), exist_ok=True)
    with open(_meta_path(memory_dir), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def _optional_vector_modules():
    try:
        import numpy as np
        from turbovec import TurboQuantIndex
    except Exception as exc:
        return None, None, str(exc)
    return np, TurboQuantIndex, ""


def _normalize_vector(np, values: list):
    vector = np.asarray(values, dtype=np.float32)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError("embedding must be a non-empty 1D vector")
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return np.ascontiguousarray(vector.reshape(1, -1))


def embed_text(text: str, post: Callable = requests.post) -> list:
    model = os.getenv("SEMANTIC_MEMORY_MODEL", DEFAULT_MODEL)
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")

    try:
        response = post(
            f"{base_url}/api/embed",
            json={"model": model, "input": text},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings")
        if isinstance(embeddings, list) and embeddings:
            return embeddings[0]
    except requests.RequestException:
        pass

    response = post(
        f"{base_url}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    embedding = data.get("embedding")
    if not isinstance(embedding, list):
        raise ValueError("Ollama did not return an embedding")
    return embedding


def semantic_status(memory_dir: str) -> dict:
    np, TurboQuantIndex, error = _optional_vector_modules()
    metadata = _load_metadata(memory_dir)
    return {
        "enabled": is_enabled(),
        "available": bool(is_enabled() and np is not None and TurboQuantIndex is not None),
        "model": os.getenv("SEMANTIC_MEMORY_MODEL", DEFAULT_MODEL),
        "indexed_notes": len(metadata),
        "path": _semantic_dir(memory_dir),
        "error": error,
    }


def index_note(memory_dir: str, filename: str, title: str, content: str) -> dict:
    if not is_enabled():
        return {"indexed": False, "reason": "semantic memory disabled"}

    np, TurboQuantIndex, error = _optional_vector_modules()
    if np is None or TurboQuantIndex is None:
        return {"indexed": False, "reason": f"semantic dependencies unavailable: {error}"}

    try:
        vector = _normalize_vector(np, embed_text(f"{title}\n\n{content}"))
        semantic_dir = _semantic_dir(memory_dir)
        index_path = _index_path(memory_dir)
        os.makedirs(semantic_dir, exist_ok=True)

        if os.path.exists(index_path):
            index = TurboQuantIndex.load(index_path)
            expected_dim = index.dim
            if expected_dim is not None and expected_dim != vector.shape[1]:
                return {"indexed": False, "reason": "embedding dimension changed; rebuild semantic index"}
        else:
            bit_width = int(os.getenv("SEMANTIC_MEMORY_BIT_WIDTH", "4"))
            index = TurboQuantIndex(dim=vector.shape[1], bit_width=bit_width)

        index.add(vector)
        index.prepare()
        index.write(index_path)

        metadata = _load_metadata(memory_dir)
        metadata.append({
            "filename": filename,
            "title": title,
            "snippet": content.strip()[:500],
        })
        _save_metadata(memory_dir, metadata)
        return {"indexed": True}
    except Exception as exc:
        return {"indexed": False, "reason": str(exc)}


def search_semantic_memory(memory_dir: str, query: str, limit: int = DEFAULT_LIMIT) -> dict:
    query = (query or "").strip()
    if not query:
        return {"available": False, "results": [], "error": "empty query"}
    if not is_enabled():
        return {"available": False, "results": [], "error": "semantic memory disabled"}

    np, TurboQuantIndex, error = _optional_vector_modules()
    if np is None or TurboQuantIndex is None:
        return {"available": False, "results": [], "error": f"semantic dependencies unavailable: {error}"}

    index_path = _index_path(memory_dir)
    metadata = _load_metadata(memory_dir)
    if not metadata or not os.path.exists(index_path):
        return {"available": True, "results": [], "error": ""}

    try:
        index = TurboQuantIndex.load(index_path)
        vector = _normalize_vector(np, embed_text(query))
        k = min(max(1, limit), len(metadata), len(index))
        scores, indices = index.search(vector, k)
        results = []
        for score, index_position in zip(scores[0], indices[0]):
            if index_position < 0 or index_position >= len(metadata):
                continue
            item = dict(metadata[int(index_position)])
            item["score"] = float(score)
            results.append(item)
        return {"available": True, "results": results, "error": ""}
    except Exception as exc:
        return {"available": False, "results": [], "error": str(exc)}
