"""Token-level autocomplete for Python code."""

from __future__ import annotations

import keyword
from builtins import __dict__ as builtins_dict

from .analyzer import ContextAnalyzer
from .types import CodeContext, TokenSuggestion


class TokenPredictor:
    """Suggest the current token from keywords, builtins and context symbols."""

    def __init__(self) -> None:
        self.analyzer = ContextAnalyzer()
        self.keywords = tuple(sorted(keyword.kwlist))
        self.builtins = tuple(
            sorted(
                name
                for name, value in builtins_dict.items()
                if not name.startswith("_") and callable(value)
            )
        )

    def predict(self, source: str, top_k: int = 8, cursor_marker: str = "<CURSOR>") -> list[TokenSuggestion]:
        prefix = source.split(cursor_marker, 1)[0] if cursor_marker in source else source
        return self.predict_from_context(self.analyzer.analyze(prefix), top_k=top_k)

    def predict_from_context(self, context: CodeContext, top_k: int = 8) -> list[TokenSuggestion]:
        token_prefix = context.current_token_prefix
        if not token_prefix:
            return []

        candidates: list[tuple[str, str, float]] = []
        candidates.extend((item, "keyword", 0.78) for item in self.keywords)
        candidates.extend((item, "builtin", 0.74) for item in self.builtins)
        candidates.extend((item, "variable", 0.90) for item in context.variables)
        candidates.extend((item, "function", 0.88) for item in context.functions)
        candidates.extend((item, "class", 0.86) for item in context.classes)
        candidates.extend((item, "argument", 0.89) for item in context.function_arguments)
        candidates.extend((item, "import", 0.87) for item in context.imports)

        suggestions: dict[str, TokenSuggestion] = {}
        for candidate, source, base_confidence in candidates:
            if candidate == token_prefix or not candidate.startswith(token_prefix):
                continue
            confidence = base_confidence + prefix_bonus(token_prefix, candidate)
            suggestion = TokenSuggestion(
                suggestion=candidate,
                confidence=round(min(confidence, 0.99), 4),
                reason=f"matches current prefix '{token_prefix}' from {source}",
                source=source,
            )
            previous = suggestions.get(candidate)
            if previous is None or suggestion.confidence > previous.confidence:
                suggestions[candidate] = suggestion

        return sorted(
            suggestions.values(),
            key=lambda item: (item.confidence, len(item.suggestion) * -1),
            reverse=True,
        )[:top_k]


def prefix_bonus(prefix: str, candidate: str) -> float:
    """Small confidence bonus for more specific prefixes."""

    if not candidate:
        return 0.0
    ratio = len(prefix) / len(candidate)
    return min(0.12, ratio * 0.12)
