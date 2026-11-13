"""Retrieve notes for Ask NaviCare.

The embeddings lesson compares texts with cosine similarity. This file does that
with a FAISS inner-product index over normalised term vectors, so search works
with no embedding API.

The retrieval lesson improves on a single flat chunk. Each note is split into a
larger parent chunk, then into smaller child chunks. Search uses the children.
The parent is what the answer is allowed to use, so the reply keeps the
surrounding context.
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


def redact_personal_data(text: str) -> str:
    """Strip obvious personal details before a note is stored.

    A real government dataset should go through CLOAK (cloak.gov.sg) first.
    This prototype only removes NRIC-style numbers and email addresses.
    """
    cleaned = re.sub(r"\b[STFGM]\d{7}[A-Z]\b", "[NRIC removed]", text, flags=re.I)
    cleaned = re.sub(r"\b[\w.+-]+@[\w.-]+\.\w+\b", "[email removed]", cleaned)
    return cleaned


def _chunks(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """Split on paragraphs, then overlap chunks the way the RAG practical does."""
    from rag_pipeline import _split_text

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        return _split_text(text, size, overlap)
    return _split_text("\n\n".join(paragraphs), size, overlap)


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
    """Parent chunks for context, child chunks for the similarity search."""
    rows: list[dict[str, str]] = []
    for document in _read_documents():
        parents = _chunks(document["text"], size=800, overlap=100)
        for parent_index, parent in enumerate(parents, start=1):
            children = _chunks(parent, size=220, overlap=40) or [parent]
            for child_index, child in enumerate(children, start=1):
                rows.append(
                    {
                        "name": document["name"],
                        "kind": document["kind"],
                        "part": str(parent_index),
                        "child": str(child_index),
                        "text": parent,
                        "search_text": child,
                    }
                )
    return rows


def _vectors(passages: list[dict[str, str]]) -> tuple[np.ndarray, dict[str, float]]:
    tokenised = [_tokenize(row.get("search_text") or row["text"]) for row in passages]
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


def retrieve(query: str, k: int = 3, min_score: float = 0.05) -> list[dict[str, str]]:
    """Return parent passages whose child chunks are closest to the question.

    Children are ranked by cosine similarity. A weak score is dropped, because a
    similar wording is not always a relevant note. Each parent is returned once,
    with the strongest child first.
    """
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
        scores, ids = index.search(query_vector, len(passages))
        chosen = [int(item) for item in ids[0] if int(item) >= 0]
        score_values = [float(item) for item in scores[0]]
    else:
        scores_row = (matrix @ query_vector.T).reshape(-1)
        chosen = list(np.argsort(-scores_row))
        score_values = [float(scores_row[item]) for item in chosen]
    best: dict[tuple[str, str], dict[str, str]] = {}
    for passage_id, score in zip(chosen, score_values):
        if score < min_score:
            continue
        source = passages[passage_id]
        key = (source["name"], source["part"])
        if key in best:
            continue
        child = source["search_text"].strip()
        parent = source["text"].strip()
        # The post-retrieval lesson puts the most relevant lines first.
        ordered = child if child == parent else f"{child}\n\n{parent}"
        best[key] = {
            "name": source["name"],
            "kind": source["kind"],
            "part": source["part"],
            "text": ordered,
            "score": f"{score:.3f}",
        }
        if len(best) >= k:
            break
    return list(best.values())


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
    cleaned = redact_personal_data(text).strip()[:MAX_UPLOAD_CHARS]
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
