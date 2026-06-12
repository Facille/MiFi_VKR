"""Public evaluator module used in the diploma architecture."""

from .evaluation import evaluate_predictor, write_report
from .reports import write_markdown_report

__all__ = ["evaluate_predictor", "write_markdown_report", "write_report"]
