"""Statistical next-block predictor for code autocomplete prototypes."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Iterable

from .analyzer import ContextAnalyzer
from .embeddings import HashedTfidfEmbedder, cosine_similarity
from .extractor import extract_blocks, reindent_block
from .templates import heuristic_predictions
from .types import CodeBlock, CodeContext, Prediction


class CodeBlockPredictor:
    """Trainable predictor based on context features and block transitions."""

    def __init__(self) -> None:
        self.analyzer = ContextAnalyzer()
        self.examples: Counter[tuple[str, str, str, str]] = Counter()
        self.token_index: dict[tuple[str, str, str, str], tuple[str, ...]] = {}
        self.embedder = HashedTfidfEmbedder()
        self.embedding_index: dict[tuple[str, str, str, str], tuple[float, ...]] = {}
        self.files_seen = 0
        self.blocks_seen = 0

    def train_from_paths(self, paths: Iterable[str | Path]) -> None:
        """Train on Python files under the provided files or directories."""

        all_blocks: list[CodeBlock] = []
        for file_path in iter_python_files(paths):
            source = file_path.read_text(encoding="utf-8")
            blocks = extract_blocks(source, path=str(file_path))
            if not blocks:
                continue
            all_blocks.extend(blocks)
            self.files_seen += 1
        self.update(all_blocks)

    def update(self, blocks: Iterable[CodeBlock]) -> None:
        """Add extracted blocks to the transition corpus."""

        blocks = list(blocks)
        self.embedder.fit([block.text for block in blocks])
        for block in blocks:
            key = (
                block.previous_signature,
                block.parent_kind,
                block.signature,
                block.text,
            )
            self.examples[key] += 1
            self.token_index[key] = block.tokens
            self.embedding_index[key] = self.embedder.encode(block.text)
            self.blocks_seen += 1

    def predict(self, source: str, top_k: int = 5, cursor_marker: str = "<CURSOR>") -> list[Prediction]:
        """Predict the next block for a source snippet containing an optional cursor marker."""

        prefix = source.split(cursor_marker, 1)[0] if cursor_marker in source else source
        context = self.analyzer.analyze(prefix)
        return self.predict_from_context(context, top_k=top_k)

    def predict_from_context(self, context: CodeContext, top_k: int = 5) -> list[Prediction]:
        """Rank statistical and template candidates for a prepared context."""

        candidates = self._statistical_candidates(context)
        candidates.extend(heuristic_predictions(context))
        return dedupe_and_sort(candidates, top_k=top_k)

    def save(self, path: str | Path) -> None:
        """Save the model as a portable JSON file."""

        payload = {
            "version": 1,
            "files_seen": self.files_seen,
            "blocks_seen": self.blocks_seen,
            "embedder": self.embedder.to_dict(),
            "examples": [
                {
                    "previous_signature": previous,
                    "parent_kind": parent,
                    "signature": signature,
                    "text": text,
                    "count": count,
                    "tokens": list(self.token_index.get((previous, parent, signature, text), ())),
                    "embedding": list(self.embedding_index.get((previous, parent, signature, text), ())),
                }
                for (previous, parent, signature, text), count in self.examples.items()
            ],
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "CodeBlockPredictor":
        """Load a model saved by :meth:`save`."""

        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        predictor = cls()
        predictor.files_seen = int(payload.get("files_seen", 0))
        predictor.blocks_seen = int(payload.get("blocks_seen", 0))
        predictor.embedder = HashedTfidfEmbedder.from_dict(payload.get("embedder", {}))
        for item in payload.get("examples", []):
            key = (
                item["previous_signature"],
                item["parent_kind"],
                item["signature"],
                item["text"],
            )
            predictor.examples[key] = int(item.get("count", 1))
            predictor.token_index[key] = tuple(item.get("tokens", ()))
            embedding = item.get("embedding")
            predictor.embedding_index[key] = tuple(embedding) if embedding else predictor.embedder.encode(key[3])
        return predictor

    def evaluate_paths(
        self,
        paths: Iterable[str | Path],
        top_k: int = 5,
        train_paths: Iterable[str | Path] | None = None,
        token_cases_path: str | Path | None = None,
    ) -> dict[str, object]:
        """Evaluate top-k signature hits on source files."""

        from .evaluation import evaluate_predictor

        return evaluate_predictor(
            self,
            list(paths),
            train_paths=list(train_paths or []),
            token_cases_path=token_cases_path,
            top_k=top_k,
        )

    def _statistical_candidates(self, context: CodeContext) -> list[Prediction]:
        if not self.examples:
            return []

        previous = context.recent_signatures[-1] if context.recent_signatures else "START"
        context_tokens = set(context.tokens[-20:])
        context_embedding = self.embedder.encode(context.prefix[-4000:])
        total_count = sum(self.examples.values())
        scored: list[Prediction] = []
        special_names = set(context.variables) | set(context.names_in_scope)
        current_function = context.scope_path[-1] if context.scope_path else ""

        for key, count in self.examples.items():
            previous_signature, parent_kind, signature, text = key
            if context.scope_kind != "module" and parent_kind == "module" and signature in {"def", "async_def", "class"}:
                continue
            score = math.log1p(count) / math.log1p(total_count)
            reasons: list[str] = [f"seen {count} time(s)"]

            if previous_signature == previous:
                score += 0.55
                reasons.append(f"previous signature matches '{previous}'")
            elif previous_signature == "START" and previous == "START":
                score += 0.22
                reasons.append("module or scope start")

            if parent_kind == context.scope_kind:
                score += 0.22
                reasons.append(f"scope matches '{context.scope_kind}'")
            elif context.scope_kind != "module":
                score -= 0.12
                reasons.append(f"scope differs from '{context.scope_kind}'")

            candidate_tokens = set(self.token_index.get(key, ()))
            overlap = len(candidate_tokens & context_tokens)
            if overlap:
                score += min(0.20, overlap * 0.035)
                reasons.append(f"{overlap} shared token(s)")

            semantic = cosine_similarity(context_embedding, self.embedding_index.get(key, ()))
            if semantic > 0:
                score += min(0.18, semantic * 0.18)
                reasons.append(f"semantic similarity {semantic:.2f}")

            if context.open_block and signature in {"docstring", "assign", "return", "pass", "raise", "if", "for"}:
                score += 0.08
                reasons.append("fits opened block indentation")

            matched_features: dict[str, str | int | float] = {
                "count": count,
                "previous_signature": previous_signature,
                "parent_kind": parent_kind,
                "semantic_similarity": round(semantic, 4),
            }

            text_terms = set(self.token_index.get(key, ()))
            for name, bonus in (("result", 0.08), ("total", 0.08), ("count", 0.06)):
                if name in special_names and name in text_terms:
                    score += bonus
                    reasons.append(f"uses context variable '{name}'")
                    matched_features[f"variable:{name}"] = 1

            if current_function:
                function_terms = set(current_function.lower().replace("_", " ").split())
                if function_terms & {token.lower() for token in text_terms}:
                    score += 0.06
                    reasons.append("matches current function name")
                    matched_features["function_name_match"] = current_function

            if context.last_active_construct and signature == context.last_active_construct:
                score += 0.05
                reasons.append(f"matches active construct '{context.last_active_construct}'")
                matched_features["last_active_construct"] = context.last_active_construct

            if context.imports and text_terms & set(context.imports):
                score += 0.05
                reasons.append("uses imported symbol")
                matched_features["import_overlap"] = len(text_terms & set(context.imports))

            if context.nesting_depth >= 4 and parent_kind != "module":
                score += 0.03
                matched_features["nesting_depth"] = context.nesting_depth

            scored.append(
                Prediction(
                    text=reindent_block(text, context.next_indentation),
                    score=round(score, 4),
                    source="model",
                    signature=signature,
                    rationale=", ".join(reasons),
                    metadata=matched_features,
                )
            )

        return scored


def iter_python_files(paths: Iterable[str | Path]) -> Iterable[Path]:
    """Yield Python files from paths in deterministic order."""

    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            yield from sorted(item for item in path.rglob("*.py") if item.is_file())


def dedupe_and_sort(candidates: list[Prediction], top_k: int) -> list[Prediction]:
    """Keep the highest-scoring unique prediction texts."""

    best: dict[str, Prediction] = {}
    for candidate in candidates:
        key = candidate.text.strip()
        if not key:
            continue
        previous = best.get(key)
        if previous is None or candidate.score > previous.score:
            best[key] = candidate
    return sorted(best.values(), key=lambda item: item.score, reverse=True)[:top_k]
