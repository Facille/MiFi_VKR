"""Shared value objects for context analysis and prediction."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CodeContext:
    """Features extracted from the code prefix before the cursor."""

    prefix: str
    current_line: str
    previous_non_empty_line: str
    indentation: int
    cursor_line: int
    cursor_column: int
    scope_kind: str
    scope_path: tuple[str, ...] = field(default_factory=tuple)
    imports: tuple[str, ...] = field(default_factory=tuple)
    functions: tuple[str, ...] = field(default_factory=tuple)
    classes: tuple[str, ...] = field(default_factory=tuple)
    variables: tuple[str, ...] = field(default_factory=tuple)
    function_arguments: tuple[str, ...] = field(default_factory=tuple)
    names_in_scope: tuple[str, ...] = field(default_factory=tuple)
    recent_signatures: tuple[str, ...] = field(default_factory=tuple)
    tokens: tuple[str, ...] = field(default_factory=tuple)
    last_active_construct: str = ""
    nesting_depth: int = 0
    current_token_prefix: str = ""
    nearest_parent_block: str = ""
    open_block: bool = False

    @property
    def next_indentation(self) -> int:
        """Indentation expected for a newly inserted block."""

        return self.indentation + 4 if self.open_block else self.indentation


@dataclass(frozen=True)
class CodeBlock:
    """A statement-level code block extracted from a Python source file."""

    signature: str
    text: str
    indent: int
    parent_kind: str
    previous_signature: str
    path: str = ""
    line_start: int = 0
    line_end: int = 0
    tokens: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Prediction:
    """A ranked next-block prediction."""

    text: str
    score: float
    source: str
    signature: str
    rationale: str
    metadata: dict[str, str | int | float] = field(default_factory=dict)

    @property
    def code(self) -> str:
        """Compatibility alias for block prediction reports."""

        return self.text

    @property
    def confidence(self) -> float:
        """Compatibility alias for score."""

        return self.score

    @property
    def reason(self) -> str:
        """Compatibility alias for rationale."""

        return self.rationale

    @property
    def matched_features(self) -> dict[str, str | int | float]:
        """Feature matches used by the ranker."""

        return self.metadata


@dataclass(frozen=True)
class TokenSuggestion:
    """A token-level autocomplete suggestion."""

    suggestion: str
    confidence: float
    reason: str
    source: str
