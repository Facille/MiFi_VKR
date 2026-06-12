"""Heuristic fallback predictions for common unfinished Python contexts."""

from __future__ import annotations

import re

from .extractor import reindent_block
from .types import CodeContext, Prediction


def heuristic_predictions(context: CodeContext) -> list[Prediction]:
    """Return template predictions derived only from the current context."""

    line = (context.current_line or context.previous_non_empty_line).strip()
    previous = context.previous_non_empty_line.strip()
    indent = context.next_indentation
    predictions: list[Prediction] = []
    append_match = re.search(r"(?P<target>(?:self\.)?[A-Za-z_][A-Za-z0-9_]*)\.append\(", previous)

    if append_match:
        target = append_match.group("target")
        if target.startswith("self."):
            predictions.append(
                _prediction(
                    f"return len({target})\n",
                    indent,
                    1.18,
                    "return",
                    f"previous line appends to {target}; method commonly returns collection size",
                    {"append_target": target},
                )
            )
        elif target in context.variables or target in context.names_in_scope:
            predictions.append(
                _prediction(
                    f"return {target}\n",
                    indent,
                    1.10,
                    "return",
                    f"previous line appends to {target}; function commonly returns accumulated collection",
                    {"append_target": target},
                )
            )

    if _inside_if_body(context) and _looks_like_boolean_function(context):
        predictions.append(
            _prediction(
                "return True\n",
                indent,
                1.16,
                "return",
                "boolean-style function inside positive condition",
                {"boolean_function": _current_function_name(context)},
            )
        )

    if _looks_like_function_header(line):
        predictions.append(
            _prediction(
                '"""TODO: describe behavior."""\nraise NotImplementedError\n',
                indent,
                0.62,
                "raise",
                "function header expects an indented implementation block",
            )
        )
        predictions.append(
            _prediction(
                "return None\n",
                indent,
                0.42,
                "return",
                "minimal function body fallback",
            )
        )
    elif _looks_like_class_header(line):
        predictions.append(
            _prediction(
                "def __init__(self) -> None:\n    pass\n",
                indent,
                0.58,
                "def",
                "class header commonly continues with an initializer",
            )
        )
    elif line.startswith("if __name__") and line.endswith(":"):
        predictions.append(
            _prediction(
                "main()\n",
                indent,
                0.55,
                "call:main",
                "module entry-point guard usually calls main",
            )
        )
    elif line.startswith(("if ", "elif ", "else")) and line.endswith(":"):
        predictions.append(_prediction("pass\n", indent, 0.38, "pass", "conditional block needs a body"))
    elif line.startswith(("for ", "while ")) and line.endswith(":"):
        predictions.append(_prediction("pass\n", indent, 0.36, "pass", "loop block needs a body"))
    elif line.startswith(("with ", "async with ")) and line.endswith(":"):
        predictions.append(_prediction("pass\n", indent, 0.34, "pass", "context manager block needs a body"))
    elif line.startswith("try") and line.endswith(":"):
        predictions.append(_prediction("pass\n", indent, 0.34, "pass", "try block needs a body"))
    elif context.scope_kind == "function" and "return" not in context.recent_signatures:
        predictions.append(
            _prediction("return None\n", indent, 0.22, "return", "function scope has no recent return")
        )
    else:
        predictions.append(_prediction("pass\n", indent, 0.12, "pass", "generic syntactic fallback"))

    return predictions


def _prediction(
    text: str,
    indent: int,
    score: float,
    signature: str,
    rationale: str,
    metadata: dict[str, str | int | float] | None = None,
) -> Prediction:
    return Prediction(
        text=reindent_block(text, indent),
        score=score,
        source="template",
        signature=signature,
        rationale=rationale,
        metadata=metadata or {},
    )


def _looks_like_function_header(line: str) -> bool:
    return bool(re.match(r"^(async\s+def|def)\s+\w+.*:\s*$", line))


def _looks_like_class_header(line: str) -> bool:
    return bool(re.match(r"^class\s+\w+.*:\s*$", line))


def _inside_if_body(context: CodeContext) -> bool:
    previous = context.previous_non_empty_line.strip()
    return context.last_active_construct == "if" or previous.startswith(("if ", "elif ", "else"))


def _looks_like_boolean_function(context: CodeContext) -> bool:
    name = _current_function_name(context)
    return name.startswith(("is_", "has_", "can_", "should_", "contains_", "exists_"))


def _current_function_name(context: CodeContext) -> str:
    if context.scope_path:
        return context.scope_path[-1]
    return context.functions[-1] if context.functions else ""
