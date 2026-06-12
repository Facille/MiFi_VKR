"""Extraction of statement-level blocks from Python code."""

from __future__ import annotations

import ast
import io
import re
import tokenize
from collections.abc import Iterator

from .types import CodeBlock


IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def normalize_indentation(text: str) -> tuple[str, int]:
    """Remove the smallest common indentation from a block."""

    lines = text.splitlines()
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return "", 0
    indent = min(len(line) - len(line.lstrip(" ")) for line in non_empty)
    normalized = "\n".join(line[indent:] if len(line) >= indent else line for line in lines)
    return normalized.rstrip() + "\n", indent


def reindent_block(text: str, spaces: int) -> str:
    """Apply a target indentation to a normalized block."""

    prefix = " " * max(0, spaces)
    return "\n".join(prefix + line if line else line for line in text.rstrip("\n").splitlines()) + "\n"


def token_fingerprint(text: str, limit: int = 24) -> tuple[str, ...]:
    """Return a compact identifier fingerprint for ranking candidates."""

    try:
        stream = io.StringIO(text)
        tokens = tokenize.generate_tokens(stream.readline)
        identifiers = [
            token.string
            for token in tokens
            if token.type == tokenize.NAME and not token.string.startswith("__")
        ]
    except (IndentationError, tokenize.TokenError):
        identifiers = IDENTIFIER_RE.findall(text)
    return tuple(identifiers[-limit:])


def signature_for_node(node: ast.AST) -> str:
    """Map a Python AST node to an abstract block signature."""

    if isinstance(node, ast.AsyncFunctionDef):
        return "async_def"
    if isinstance(node, ast.FunctionDef):
        return "def"
    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return "import"
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return "assign"
    if isinstance(node, ast.Return):
        return "return"
    if isinstance(node, ast.If):
        return "if"
    if isinstance(node, (ast.For, ast.AsyncFor)):
        return "for"
    if isinstance(node, ast.While):
        return "while"
    if isinstance(node, (ast.With, ast.AsyncWith)):
        return "with"
    if isinstance(node, ast.Try):
        return "try"
    if isinstance(node, ast.ExceptHandler):
        return "except"
    if isinstance(node, ast.Raise):
        return "raise"
    if isinstance(node, ast.Assert):
        return "assert"
    if isinstance(node, ast.Match):
        return "match"
    if isinstance(node, ast.Expr):
        value = node.value
        if isinstance(value, ast.Call):
            name = call_name(value)
            return f"call:{name}" if name else "call"
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return "docstring"
        return "expr"
    if isinstance(node, (ast.Break, ast.Continue, ast.Pass)):
        return type(node).__name__.lower()
    return type(node).__name__.lower()


def call_name(call: ast.Call) -> str:
    """Best-effort dotted name for a call expression."""

    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = [func.attr]
        value = func.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return ""


def extract_blocks(source: str, path: str = "") -> list[CodeBlock]:
    """Extract code blocks from a Python source string."""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    blocks: list[CodeBlock] = []

    def text_for(node: ast.AST) -> tuple[str, int]:
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start)
        raw = "\n".join(lines[start - 1 : end])
        return normalize_indentation(raw)

    def walk_body(body: list[ast.stmt], parent_kind: str) -> Iterator[CodeBlock]:
        previous = "START"
        for node in body:
            signature = signature_for_node(node)
            text, indent = text_for(node)
            block = CodeBlock(
                signature=signature,
                text=text,
                indent=indent,
                parent_kind=parent_kind,
                previous_signature=previous,
                path=path,
                line_start=getattr(node, "lineno", 0),
                line_end=getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                tokens=token_fingerprint(text),
            )
            yield block
            previous = signature

            child_parent = nested_parent_kind(signature)
            for nested in nested_bodies(node):
                yield from walk_body(nested, child_parent)

    blocks.extend(walk_body(tree.body, "module"))
    return blocks


def nested_parent_kind(signature: str) -> str:
    """Scope label used for nested statements."""

    if signature in {"def", "async_def"}:
        return "function"
    if signature == "class":
        return "class"
    return signature


def nested_bodies(node: ast.AST) -> list[list[ast.stmt]]:
    """Return all statement lists nested inside a node."""

    bodies: list[list[ast.stmt]] = []
    for field_name in ("body", "orelse", "finalbody"):
        value = getattr(node, field_name, None)
        if isinstance(value, list) and value and all(isinstance(item, ast.stmt) for item in value):
            bodies.append(value)

    handlers = getattr(node, "handlers", None)
    if handlers:
        for handler in handlers:
            if isinstance(handler, ast.ExceptHandler):
                bodies.append(handler.body)

    cases = getattr(node, "cases", None)
    if cases:
        for case in cases:
            body = getattr(case, "body", None)
            if isinstance(body, list):
                bodies.append(body)

    return bodies
