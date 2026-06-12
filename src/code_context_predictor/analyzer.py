"""Best-effort context analysis for code before the cursor."""

from __future__ import annotations

import ast
import io
import re
import tokenize

from .extractor import extract_blocks, nested_parent_kind, token_fingerprint
from .types import CodeContext


class ContextAnalyzer:
    """Extract structural and lexical features from a Python code prefix."""

    def analyze(self, prefix: str) -> CodeContext:
        prefix = prefix.lstrip("\ufeff")
        lines = prefix.splitlines()
        ends_with_newline = prefix.endswith(("\n", "\r\n"))
        current_line = "" if ends_with_newline else (lines[-1] if lines else "")
        previous_non_empty = self._previous_non_empty(lines, skip_current=not ends_with_newline)
        indentation = 0 if ends_with_newline else self._indentation(current_line)
        cursor_line = prefix.count("\n") + 1
        cursor_column = len(current_line) + 1
        open_block = self._opens_block(current_line) or (
            ends_with_newline and self._opens_block(previous_non_empty)
        )

        tree = self._parse_stable_prefix(prefix)
        scope_kind, scope_path = self._scope_at_cursor(tree, cursor_line)
        scope_kind = self._parent_kind_from_indentation(prefix, indentation) or scope_kind
        imports = self._imports_before_cursor(tree, cursor_line)
        symbol_table = self._symbols_before_cursor(tree, cursor_line)
        names = tuple(
            sorted(
                set(symbol_table["functions"])
                | set(symbol_table["classes"])
                | set(symbol_table["variables"])
                | set(symbol_table["function_arguments"])
            )
        )
        recent_signatures = self._recent_signatures(prefix, max_indent=indentation)
        tokens = token_fingerprint(prefix, limit=40)
        last_active_construct = self._last_active_construct(current_line, previous_non_empty, recent_signatures)
        nesting_depth = self._nesting_depth(tree)
        nearest_parent_block = self._nearest_parent_block(prefix, indentation)
        current_token_prefix = self._current_token_prefix(current_line)

        return CodeContext(
            prefix=prefix,
            current_line=current_line,
            previous_non_empty_line=previous_non_empty,
            indentation=indentation,
            cursor_line=cursor_line,
            cursor_column=cursor_column,
            scope_kind=scope_kind,
            scope_path=scope_path,
            imports=imports,
            functions=symbol_table["functions"],
            classes=symbol_table["classes"],
            variables=symbol_table["variables"],
            function_arguments=symbol_table["function_arguments"],
            names_in_scope=names,
            recent_signatures=recent_signatures,
            tokens=tokens,
            last_active_construct=last_active_construct,
            nesting_depth=nesting_depth,
            current_token_prefix=current_token_prefix,
            nearest_parent_block=nearest_parent_block,
            open_block=open_block,
        )

    @staticmethod
    def _indentation(line: str) -> int:
        return len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip(" "))

    @staticmethod
    def _opens_block(line: str) -> bool:
        return line.strip().endswith(":")

    @staticmethod
    def _previous_non_empty(lines: list[str], skip_current: bool) -> str:
        candidates = lines[:-1] if skip_current else lines
        for line in reversed(candidates):
            if line.strip():
                return line
        return ""

    @staticmethod
    def _parse_stable_prefix(prefix: str) -> ast.Module:
        lines = prefix.splitlines()
        for end in range(len(lines), -1, -1):
            candidate = "\n".join(lines[:end])
            stripped_candidate = candidate.rstrip()
            if stripped_candidate and stripped_candidate.endswith(":"):
                last_line = next((line for line in reversed(stripped_candidate.splitlines()) if line.strip()), "")
                block_indent = ContextAnalyzer._indentation(last_line) + 4
                candidate = stripped_candidate + "\n" + (" " * block_indent) + "pass"
            try:
                return ast.parse(candidate or "\n")
            except SyntaxError:
                continue
        return ast.parse("\n")

    @staticmethod
    def _scope_at_cursor(tree: ast.Module, cursor_line: int) -> tuple[str, tuple[str, ...]]:
        scopes: list[tuple[int, int, str, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = getattr(node, "lineno", 0)
                end = getattr(node, "end_lineno", start)
                if start <= cursor_line <= max(end, start):
                    kind = "class" if isinstance(node, ast.ClassDef) else "function"
                    scopes.append((start, end, kind, node.name))
        if not scopes:
            return "module", ()
        scopes.sort(key=lambda item: (item[0], item[1]))
        return scopes[-1][2], tuple(item[3] for item in scopes)

    @staticmethod
    def _parent_kind_from_indentation(prefix: str, indentation: int) -> str | None:
        if indentation <= 0:
            return None
        blocks = extract_blocks(prefix)
        parents = [block for block in blocks if block.indent < indentation]
        if not parents:
            return None
        return nested_parent_kind(parents[-1].signature)

    @staticmethod
    def _imports_before_cursor(tree: ast.Module, cursor_line: int) -> tuple[str, ...]:
        names: set[str] = set()
        for node in ast.walk(tree):
            if getattr(node, "lineno", cursor_line + 1) >= cursor_line:
                continue
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    names.add(alias.asname or alias.name)
        return tuple(sorted(names))

    @staticmethod
    def _symbols_before_cursor(tree: ast.Module, cursor_line: int) -> dict[str, tuple[str, ...]]:
        functions: set[str] = set()
        classes: set[str] = set()
        variables: set[str] = set()
        function_arguments: set[str] = set()
        for node in ast.walk(tree):
            if getattr(node, "lineno", cursor_line + 1) >= cursor_line:
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.add(node.name)
                for arg in list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs):
                    function_arguments.add(arg.arg)
                if node.args.vararg:
                    function_arguments.add(node.args.vararg.arg)
                if node.args.kwarg:
                    function_arguments.add(node.args.kwarg.arg)
            elif isinstance(node, ast.ClassDef):
                classes.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                variables.add(node.id)
            elif isinstance(node, ast.arg):
                function_arguments.add(node.arg)
        return {
            "functions": tuple(sorted(functions)),
            "classes": tuple(sorted(classes)),
            "variables": tuple(sorted(variables)),
            "function_arguments": tuple(sorted(function_arguments)),
        }

    @staticmethod
    def _recent_signatures(prefix: str, max_indent: int) -> tuple[str, ...]:
        blocks = extract_blocks(prefix)
        if blocks:
            visible_blocks = [block for block in blocks if block.indent <= max_indent]
            if visible_blocks:
                return tuple(block.signature for block in visible_blocks[-8:])
            return tuple(block.signature for block in blocks[-8:])

        signatures: list[str] = []
        try:
            tokens = tokenize.generate_tokens(io.StringIO(prefix).readline)
            for token in tokens:
                if token.type == tokenize.NAME and token.string in {
                    "def",
                    "class",
                    "if",
                    "for",
                    "while",
                    "with",
                    "try",
                    "return",
                    "import",
                    "from",
                }:
                    signatures.append("import" if token.string == "from" else token.string)
        except (IndentationError, tokenize.TokenError):
            pass
        return tuple(signatures[-8:])

    @staticmethod
    def _current_token_prefix(current_line: str) -> str:
        match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)$", current_line)
        return match.group(1) if match else ""

    @staticmethod
    def _last_active_construct(
        current_line: str,
        previous_non_empty: str,
        recent_signatures: tuple[str, ...],
    ) -> str:
        line = (current_line or previous_non_empty).strip()
        for keyword, signature in (
            ("async def ", "async_def"),
            ("def ", "def"),
            ("class ", "class"),
            ("if ", "if"),
            ("elif ", "if"),
            ("else", "if"),
            ("for ", "for"),
            ("while ", "while"),
            ("with ", "with"),
            ("try", "try"),
            ("except", "except"),
            ("return", "return"),
        ):
            if line.startswith(keyword):
                return signature
        return recent_signatures[-1] if recent_signatures else ""

    @classmethod
    def _nesting_depth(cls, tree: ast.AST) -> int:
        def walk(node: ast.AST, depth: int) -> int:
            child_depth = depth + 1 if isinstance(node, ast.stmt) else depth
            return max([depth, *(walk(child, child_depth) for child in ast.iter_child_nodes(node))])

        return walk(tree, 0)

    @staticmethod
    def _nearest_parent_block(prefix: str, indentation: int) -> str:
        blocks = extract_blocks(prefix)
        if not blocks:
            return ""
        candidates = [block for block in blocks if block.indent < indentation]
        if candidates:
            return candidates[-1].signature
        return blocks[-1].signature
