"""Human-readable experiment reports."""

from __future__ import annotations

from pathlib import Path


def write_markdown_report(report: dict[str, object], path: str | Path) -> None:
    """Write a compact Markdown report for diploma materials."""

    split = report.get("data_split", {})
    block = report.get("block_prediction", {})
    token = report.get("token_completion", {})
    comments = report.get("comments", [])

    lines = [
        "# Evaluation Report",
        "",
        "## Data Split",
        "",
        table_from_mapping(split if isinstance(split, dict) else {}),
        "",
        "## Block Prediction",
        "",
        "### Model Signature Accuracy",
        "",
        table_from_mapping(nested(block, "model_signature_accuracy")),
        "",
        "### Model Exact Text Accuracy",
        "",
        table_from_mapping(nested(block, "model_exact_text_accuracy")),
        "",
        "### Template Baseline Signature Accuracy",
        "",
        table_from_mapping(nested(block, "template_baseline_signature_accuracy")),
        "",
        "## Token Completion",
        "",
        "### Model Accuracy",
        "",
        table_from_mapping(nested(token, "model_accuracy")),
        "",
        "### Prefix Baseline Accuracy",
        "",
        table_from_mapping(nested(token, "baseline_accuracy")),
        "",
        "## Comments",
        "",
    ]
    lines.extend(f"- {item}" for item in comments if isinstance(item, str))
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- The system uses a lightweight heuristic/statistical approach rather than training a large language model.",
            "- Embeddings are hashed TF-IDF vectors, not neural embeddings.",
            "- The current implementation focuses on Python.",
            "- Web integration is an IDE/autocomplete simulation, not a full IDE extension.",
            "- Results depend on the size and relevance of the training corpus.",
        ]
    )

    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def nested(payload: object, key: str) -> dict[str, object]:
    if isinstance(payload, dict) and isinstance(payload.get(key), dict):
        return payload[key]  # type: ignore[return-value]
    return {}


def table_from_mapping(payload: dict[str, object]) -> str:
    if not payload:
        return "| metric | value |\n|---|---|\n| n/a | n/a |"
    rows = ["| metric | value |", "|---|---|"]
    for key, value in payload.items():
        rows.append(f"| `{key}` | {value} |")
    return "\n".join(rows)
