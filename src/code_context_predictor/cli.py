"""Command-line interface for the code context predictor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .api import run_server
from .evaluation import write_report
from .extractor import extract_blocks
from .model import CodeBlockPredictor
from .reports import write_markdown_report
from .token_predictor import TokenPredictor


DEMO_CORPUS = '''
def normalize_items(items):
    result = []
    for item in items:
        result.append(str(item).strip())
    return result


def read_text(path):
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()
    return content


class Repository:
    def __init__(self, root):
        self.root = root

    def exists(self):
        return self.root.exists()
'''


DEMO_SNIPPET = '''def clean_names(names):
    result = []
    for name in names:
        result.append(name.strip().lower())
    <CURSOR>
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="code-predictor",
        description="Analyze Python code context and predict the next block.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="train a model on Python files")
    train_parser.add_argument("--input", nargs="+", required=True, help="file or directory with .py files")
    train_parser.add_argument("--model", required=True, help="output JSON model path")

    predict_parser = subparsers.add_parser("predict", help="predict next block for a snippet")
    predict_parser.add_argument("--model", required=True, help="JSON model path")
    predict_parser.add_argument("--file", required=True, help="source file with <CURSOR> marker")
    predict_parser.add_argument("--top-k", type=int, default=5)
    predict_parser.add_argument("--cursor-marker", default="<CURSOR>")

    token_parser = subparsers.add_parser("complete-token", help="predict current token from prefix")
    token_parser.add_argument("--file", required=True, help="source file with <CURSOR> marker")
    token_parser.add_argument("--top-k", type=int, default=8)
    token_parser.add_argument("--cursor-marker", default="<CURSOR>")

    evaluate_parser = subparsers.add_parser("evaluate", help="evaluate on Python files")
    evaluate_parser.add_argument("--input", nargs="+", help="legacy path used as both train and test")
    evaluate_parser.add_argument("--train", nargs="+", help="training files or directories")
    evaluate_parser.add_argument("--test", nargs="+", help="held-out test files or directories")
    evaluate_parser.add_argument("--model", help="optional existing JSON model path")
    evaluate_parser.add_argument("--top-k", type=int, default=5)
    evaluate_parser.add_argument("--report", help="optional JSON report output path")
    evaluate_parser.add_argument("--markdown-report", help="optional Markdown report output path")
    evaluate_parser.add_argument("--token-cases", default="examples/token_cases.json")

    serve_parser = subparsers.add_parser("serve", help="run local API and web demo")
    serve_parser.add_argument("--model", required=True, help="JSON model path")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)

    subparsers.add_parser("demo", help="run an in-memory demonstration")

    args = parser.parse_args(argv)

    if args.command == "train":
        predictor = CodeBlockPredictor()
        predictor.train_from_paths(args.input)
        predictor.save(args.model)
        print(f"Saved model to {args.model}")
        print(f"Files seen: {predictor.files_seen}; blocks seen: {predictor.blocks_seen}")
        return 0

    if args.command == "predict":
        predictor = CodeBlockPredictor.load(args.model)
        source = Path(args.file).read_text(encoding="utf-8")
        predictions = predictor.predict(source, top_k=args.top_k, cursor_marker=args.cursor_marker)
        print_predictions(predictions)
        return 0

    if args.command == "complete-token":
        predictor = TokenPredictor()
        source = Path(args.file).read_text(encoding="utf-8")
        suggestions = predictor.predict(source, top_k=args.top_k, cursor_marker=args.cursor_marker)
        print_token_suggestions(suggestions)
        return 0

    if args.command == "evaluate":
        train_paths = args.train or args.input
        test_paths = args.test or args.input
        if not train_paths or not test_paths:
            raise SystemExit("evaluate requires --train and --test, or legacy --input")
        if args.model:
            predictor = CodeBlockPredictor.load(args.model)
        else:
            predictor = CodeBlockPredictor()
            predictor.train_from_paths(train_paths)
        report = predictor.evaluate_paths(
            test_paths,
            train_paths=train_paths,
            token_cases_path=args.token_cases,
            top_k=args.top_k,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.report:
            write_report(report, args.report)
            print(f"Saved report to {args.report}")
        if args.markdown_report:
            write_markdown_report(report, args.markdown_report)
            print(f"Saved Markdown report to {args.markdown_report}")
        return 0

    if args.command == "serve":
        run_server(args.model, host=args.host, port=args.port)
        return 0

    if args.command == "demo":
        predictor = CodeBlockPredictor()
        predictor.update(extract_blocks(DEMO_CORPUS))
        print("Snippet:")
        print(DEMO_SNIPPET.replace("<CURSOR>", "|"))
        print("Predictions:")
        print_predictions(predictor.predict(DEMO_SNIPPET, top_k=5))
        return 0

    return 2


def print_predictions(predictions) -> None:
    for index, prediction in enumerate(predictions, start=1):
        print(f"\n#{index} score={prediction.score:.3f} source={prediction.source} signature={prediction.signature}")
        print(f"reason: {prediction.rationale}")
        if prediction.metadata:
            print(f"matched_features: {json.dumps(prediction.metadata, ensure_ascii=False)}")
        print(prediction.text.rstrip())


def print_token_suggestions(suggestions) -> None:
    for index, suggestion in enumerate(suggestions, start=1):
        print(
            f"#{index} suggestion={suggestion.suggestion} "
            f"confidence={suggestion.confidence:.3f} source={suggestion.source}"
        )
        print(f"reason: {suggestion.reason}")


if __name__ == "__main__":
    raise SystemExit(main())
