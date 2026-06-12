"""Lightweight code embeddings based on hashed TF-IDF features.

The implementation intentionally avoids external dependencies. It is not a
neural embedding model, but it gives the project a reproducible semantic vector
space for comparing code contexts and candidate blocks.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass, field


TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+|==|!=|<=|>=|->|[-+*/%]=?")


def code_terms(text: str) -> list[str]:
    """Tokenize code into terms suitable for vector comparison."""

    terms: list[str] = []
    for token in TOKEN_RE.findall(text):
        parts = split_identifier(token)
        terms.extend(parts or [token.lower()])
    return terms


def split_identifier(token: str) -> list[str]:
    """Split snake_case and camelCase names into normalized pieces."""

    token = token.strip("_")
    if not token:
        return []
    snake_parts = re.split(r"[_\W]+", token)
    parts: list[str] = []
    for part in snake_parts:
        if not part:
            continue
        camel = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", part).split()
        parts.extend(item.lower() for item in camel if item)
    return parts


@dataclass
class HashedTfidfEmbedder:
    """Small deterministic TF-IDF embedder using feature hashing."""

    dimensions: int = 256
    document_frequency: Counter[str] = field(default_factory=Counter)
    documents_seen: int = 0

    def fit(self, documents: list[str]) -> None:
        """Collect document frequencies from training documents."""

        for document in documents:
            terms = set(code_terms(document))
            if not terms:
                continue
            self.document_frequency.update(terms)
            self.documents_seen += 1

    def encode(self, text: str) -> tuple[float, ...]:
        """Encode text into a normalized dense vector."""

        counts = Counter(code_terms(text))
        if not counts:
            return tuple(0.0 for _ in range(self.dimensions))

        vector = [0.0] * self.dimensions
        total = sum(counts.values())
        for term, count in counts.items():
            index = stable_hash(term) % self.dimensions
            sign = -1.0 if stable_hash("sign:" + term) % 2 else 1.0
            tf = count / total
            df = self.document_frequency.get(term, 0)
            idf = math.log((1 + self.documents_seen) / (1 + df)) + 1.0
            vector[index] += sign * tf * idf

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return tuple(vector)
        return tuple(value / norm for value in vector)

    def to_dict(self) -> dict[str, object]:
        return {
            "dimensions": self.dimensions,
            "documents_seen": self.documents_seen,
            "document_frequency": dict(self.document_frequency),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "HashedTfidfEmbedder":
        return cls(
            dimensions=int(payload.get("dimensions", 256)),
            document_frequency=Counter(payload.get("document_frequency", {})),
            documents_seen=int(payload.get("documents_seen", 0)),
        )


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    """Return cosine similarity for normalized vectors."""

    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def stable_hash(text: str) -> int:
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big", signed=False)
