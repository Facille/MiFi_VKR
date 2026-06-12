"""Baseline methods for autocomplete evaluation."""

from __future__ import annotations

import keyword
from builtins import __dict__ as builtins_dict
from collections import Counter

from .templates import heuristic_predictions
from .types import CodeContext, Prediction, TokenSuggestion


class PrefixTokenBaseline:
    """Token baseline using only Python keywords and builtins."""

    def __init__(self) -> None:
        self.candidates = tuple(
            sorted(
                set(keyword.kwlist)
                | {
                    name
                    for name, value in builtins_dict.items()
                    if not name.startswith("_") and callable(value)
                }
            )
        )

    def predict(self, prefix: str, top_k: int = 5) -> list[TokenSuggestion]:
        if not prefix:
            return []
        return [
            TokenSuggestion(
                suggestion=candidate,
                confidence=0.5,
                reason=f"generic prefix match for '{prefix}'",
                source="prefix_baseline",
            )
            for candidate in self.candidates
            if candidate.startswith(prefix) and candidate != prefix
        ][:top_k]


class TemplateBlockBaseline:
    """Block baseline based only on syntactic templates."""

    def predict_from_context(self, context: CodeContext, top_k: int = 5) -> list[Prediction]:
        return heuristic_predictions(context)[:top_k]


class MostCommonSignatureBaseline:
    """Dataset baseline that predicts globally frequent block signatures."""

    def __init__(self, signature_counts: Counter[str]) -> None:
        self.signature_counts = signature_counts

    @classmethod
    def from_signatures(cls, signatures: list[str]) -> "MostCommonSignatureBaseline":
        return cls(Counter(signatures))

    def predict_signatures(self, top_k: int) -> list[str]:
        return [signature for signature, _ in self.signature_counts.most_common(top_k)]
