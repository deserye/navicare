"""Retrieve short passages from the sample notes and admin uploads.

The index is a FAISS inner-product index over normalised term vectors.
Retrieval does not call an external embedding API, so Ask NaviCare can show
source passages when no model key is configured.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np

try:
    import faiss
except ImportError:  # pragma: no cover - requirements include faiss-cpu
    faiss = None

PROJECT_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = PROJECT_DIR / "data" / "samples"
UPLOAD_DIR = PROJECT_DIR / "data" / "uploads"
TOKEN = re.compile(r"[a-z0-9]+")
MAX_UPLOAD_CHARS = 20_000


def _tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def _chunks(text: str, size: int = 700) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    pieces: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= size:
            current = f"{current}\n\n{paragraph}".strip()
        else:
            if current:
                pieces.append(current)
            current = paragraph[:size]
    if current:
        pieces.append(current)
    return pieces or [text.strip()]


def _read_documents() -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    for folder, kind in ((SAMPLE_DIR, "sample"), (UPLOAD_DIR, "upload")):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*")):
            if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                documents.append({"name": path.name, "kind": kind, "text": text})
    return documents


def _passages() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for document in _read_documents():
        for index, chunk in enumerate(_chunks(document["text"]), start=1):
            rows.append(
                {
                    "name": document["name"],
                    "kind": document["kind"],
                    "part": str(index),
                    "text": chunk,
                }
            )
    return rows


def _vectors(passages: list[dict[str, str]]) -> tuple[np.ndarray, dict[str, float]]:
    tokenised = [_tokenize(row["text"]) for row in passages]
    document_frequency: dict[str, int] = {}
    for tokens in tokenised:
        for token in set(tokens):
            document_frequency[token] = document_frequency.get(token, 0) + 1
    total = len(passages)
    weights = {
        token: math.log((total + 1) / (count + 1)) + 1
        for token, count in document_frequency.items()
    }
    vocabulary = {token: index for index, token in enumerate(sorted(weights))}
    matrix = np.zeros((total, len(vocabulary)), dtype=np.float32)
    for row_index, tokens in enumerate(tokenised):
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        for token, count in counts.items():
            column = vocabulary.get(token)
            if column is not None:
                matrix[row_index, column] = count * weights[token]
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return matrix / norms, weights


def _query_vector(query: str, weights: dict[str, float], width: int) -> np.ndarray:
    vocabulary = {token: index for index, token in enumerate(sorted(weights))}
    vector = np.zeros((1, width), dtype=np.float32)
    counts: dict[str, int] = {}
    for token in _tokenize(query):
        counts[token] = counts.get(token, 0) + 1
    for token, count in counts.items():
        column = vocabulary.get(token)
        if column is not None:
            vector[0, column] = count * weights[token]
    norm = float(np.linalg.norm(vector))
    if norm:
        vector /= norm
    return vector


def retrieve(query: str, k: int = 3) -> list[dict[str, str]]:
    """Return the closest sample or uploaded passages for a question."""
    question = (query or "").strip()
    if not question:
        return []
    passages = _passages()
    if not passages:
        return []
    matrix, weights = _vectors(passages)
    query_vector = _query_vector(question, weights, matrix.shape[1])
    if faiss is not None:
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        scores, ids = index.search(query_vector, min(k, len(passages)))
        chosen = [int(item) for item in ids[0] if int(item) >= 0]
        score_values = [float(item) for item in scores[0]]
    else:
        scores_row = (matrix @ query_vector.T).reshape(-1)
        chosen = list(np.argsort(-scores_row)[:k])
        score_values = [float(scores_row[item]) for item in chosen]
    results: list[dict[str, str]] = []
    for passage_id, score in zip(chosen, score_values):
        if score <= 0:
            continue
        row = dict(passages[passage_id])
        row["score"] = f"{score:.3f}"
        results.append(row)
    return results


def list_documents() -> list[dict[str, str]]:
    """List sample notes and files an admin has uploaded."""
    rows = []
    for document in _read_documents():
        rows.append(
            {
                "File": document["name"],
                "Kind": document["kind"],
                "Characters": str(len(document["text"])),
            }
        )
    return rows


def save_upload(filename: str, text: str) -> str:
    """Store a plain-text note uploaded by an admin. Returns the saved file name."""
    stem = Path(filename).name
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip(".-") or "note.txt"
    if not safe.lower().endswith((".txt", ".md")):
        safe = f"{safe}.txt"
    cleaned = text.strip()[:MAX_UPLOAD_CHARS]
    if not cleaned:
        raise ValueError("The uploaded file is empty.")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOAD_DIR / safe
    destination.write_text(cleaned, encoding="utf-8")
    return destination.name


def delete_upload(filename: str) -> bool:
    """Remove one admin upload. Sample notes are left in place."""
    path = UPLOAD_DIR / Path(filename).name
    if path.is_file() and path.parent == UPLOAD_DIR:
        path.unlink()
        return True
    return False
