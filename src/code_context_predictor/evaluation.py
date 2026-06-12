"""Evaluation helpers for autocomplete experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .analyzer import ContextAnalyzer
from .baselines import PrefixTokenBaseline, TemplateBlockBaseline
from .extractor import extract_blocks
from .model import CodeBlockPredictor, iter_python_files
from .token_predictor import TokenPredictor


@dataclass(frozen=True)
class BlockEvaluationCase:
    path: str
    line: int
    prefix: str
    expected_signature: str
    expected_text: str


@dataclass(frozen=True)
class TokenEvaluationCase:
    name: str
    source: str
    expected: str


def evaluate_predictor(
    predictor: CodeBlockPredictor,
    test_paths: list[str | Path],
    train_paths: list[str | Path] | None = None,
    token_cases_path: str | Path | None = None,
    top_k: int = 5,
    examples_limit: int = 8,
) -> dict[str, object]:
    """Evaluate block prediction and token completion on held-out data."""

    analyzer = ContextAnalyzer()
    block_cases = collect_block_cases(test_paths)
    train_signatures = collect_signatures(train_paths or [])
    token_cases = load_token_cases(token_cases_path) if token_cases_path else []

    model_signature_hits = {f"top_{k}": 0 for k in range(1, top_k + 1)}
    model_text_hits = {f"top_{k}": 0 for k in range(1, top_k + 1)}
    template_baseline_hits = {f"top_{k}": 0 for k in range(1, top_k + 1)}
    block_samples: list[dict[str, object]] = []

    template_baseline = TemplateBlockBaseline()

    for case in block_cases:
        context = analyzer.analyze(case.prefix)
        predictions = predictor.predict_from_context(context, top_k=top_k)
        template_predictions = template_baseline.predict_from_context(context, top_k=top_k)
        expected_text = normalize_text(case.expected_text)
        predicted_signatures = [prediction.signature for prediction in predictions]
        predicted_texts = [normalize_text(prediction.text) for prediction in predictions]
        template_signatures = [prediction.signature for prediction in template_predictions]

        for k in range(1, top_k + 1):
            if case.expected_signature in predicted_signatures[:k]:
                model_signature_hits[f"top_{k}"] += 1
            if expected_text in predicted_texts[:k]:
                model_text_hits[f"top_{k}"] += 1
            if case.expected_signature in template_signatures[:k]:
                template_baseline_hits[f"top_{k}"] += 1

        if len(block_samples) < examples_limit:
            block_samples.append(
                {
                    "file": case.path,
                    "line": case.line,
                    "expected_signature": case.expected_signature,
                    "model_predictions": [
                        {
                            "signature": prediction.signature,
                            "confidence": prediction.confidence,
                            "source": prediction.source,
                            "code": prediction.code.strip(),
                            "reason": prediction.reason,
                            "matched_features": prediction.matched_features,
                        }
                        for prediction in predictions[:3]
                    ],
                    "template_baseline": [
                        {
                            "signature": prediction.signature,
                            "confidence": prediction.confidence,
                            "code": prediction.code.strip(),
                        }
                        for prediction in template_predictions[:3]
                    ],
                }
            )

    token_report = evaluate_token_completion(token_cases, top_k=top_k)
    block_total = len(block_cases)
    model_block_accuracy = rates(model_signature_hits, block_total)
    template_block_accuracy = rates(template_baseline_hits, block_total)

    comments = []
    if template_block_accuracy.get("top_1", 0.0) > model_block_accuracy.get("top_1", 0.0):
        comments.append(
            "Template baseline is stronger on top-1 block signatures; this indicates the train corpus is still small."
        )
    token_model_top1 = token_report["model_accuracy"].get("top_1", 0.0)
    token_baseline_top1 = token_report["baseline_accuracy"].get("top_1", 0.0)
    if token_baseline_top1 > token_model_top1:
        comments.append(
            "Prefix token baseline is stronger on top-1 token completion; context ranking should be tuned."
        )
    if not comments:
        comments.append("The model is competitive with the configured baselines on the evaluated sample.")

    return {
        "data_split": {
            "train_files": len(list(iter_python_files(train_paths or []))),
            "test_files": len(list(iter_python_files(test_paths))),
            "train_block_signatures": len(train_signatures),
            "test_block_cases": block_total,
            "token_cases": len(token_cases),
        },
        "top_k": top_k,
        "block_prediction": {
            "model_signature_accuracy": model_block_accuracy,
            "model_exact_text_accuracy": rates(model_text_hits, block_total),
            "template_baseline_signature_accuracy": template_block_accuracy,
        },
        "token_completion": token_report,
        "comments": comments,
        "block_samples": block_samples,
    }


def evaluate_token_completion(cases: list[TokenEvaluationCase], top_k: int = 5) -> dict[str, object]:
    predictor = TokenPredictor()
    baseline = PrefixTokenBaseline()
    model_hits = {f"top_{k}": 0 for k in range(1, top_k + 1)}
    baseline_hits = {f"top_{k}": 0 for k in range(1, top_k + 1)}
    samples: list[dict[str, object]] = []

    for case in cases:
        context = predictor.analyzer.analyze(case.source.split("<CURSOR>", 1)[0])
        model_predictions = predictor.predict_from_context(context, top_k=top_k)
        baseline_predictions = baseline.predict(context.current_token_prefix, top_k=top_k)
        model_items = [item.suggestion for item in model_predictions]
        baseline_items = [item.suggestion for item in baseline_predictions]

        for k in range(1, top_k + 1):
            if case.expected in model_items[:k]:
                model_hits[f"top_{k}"] += 1
            if case.expected in baseline_items[:k]:
                baseline_hits[f"top_{k}"] += 1

        if len(samples) < 8:
            samples.append(
                {
                    "name": case.name,
                    "prefix": context.current_token_prefix,
                    "expected": case.expected,
                    "model": [item.__dict__ for item in model_predictions[:3]],
                    "baseline": [item.__dict__ for item in baseline_predictions[:3]],
                }
            )

    total = len(cases)
    return {
        "cases": total,
        "model_accuracy": rates(model_hits, total),
        "baseline_accuracy": rates(baseline_hits, total),
        "samples": samples,
    }


def collect_block_cases(paths: list[str | Path]) -> list[BlockEvaluationCase]:
    """Build leave-position block cases from Python files."""

    cases: list[BlockEvaluationCase] = []
    for file_path in iter_python_files(paths):
        source = file_path.read_text(encoding="utf-8")
        lines = source.splitlines()
        for block in extract_blocks(source, path=str(file_path)):
            if block.line_start <= 1:
                continue
            prefix = "\n".join(lines[: block.line_start - 1]) + "\n" + (" " * block.indent)
            cases.append(
                BlockEvaluationCase(
                    path=str(file_path),
                    line=block.line_start,
                    prefix=prefix,
                    expected_signature=block.signature,
                    expected_text=block.text,
                )
            )
    return cases


def collect_signatures(paths: list[str | Path]) -> list[str]:
    signatures: list[str] = []
    for file_path in iter_python_files(paths):
        source = file_path.read_text(encoding="utf-8")
        signatures.extend(block.signature for block in extract_blocks(source, path=str(file_path)))
    return signatures


def load_token_cases(path: str | Path) -> list[TokenEvaluationCase]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        TokenEvaluationCase(
            name=str(item["name"]),
            source=str(item["source"]),
            expected=str(item["expected"]),
        )
        for item in payload
    ]


def rates(hits: dict[str, int], total: int) -> dict[str, float]:
    if total == 0:
        return {key: 0.0 for key in hits}
    return {key: round(value / total, 4) for key, value in hits.items()}


def normalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def write_report(report: dict[str, object], path: str | Path) -> None:
    Path(path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
