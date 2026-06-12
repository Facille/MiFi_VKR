from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from code_context_predictor.analyzer import ContextAnalyzer
from code_context_predictor.embeddings import HashedTfidfEmbedder, cosine_similarity
from code_context_predictor.evaluation import evaluate_predictor
from code_context_predictor.extractor import extract_blocks
from code_context_predictor.model import CodeBlockPredictor
from code_context_predictor.token_predictor import TokenPredictor


class ContextAnalyzerTest(unittest.TestCase):
    def test_detects_open_function_block(self):
        context = ContextAnalyzer().analyze("def load_data(path):\n")

        self.assertTrue(context.open_block)
        self.assertEqual(context.next_indentation, 4)
        self.assertEqual(context.previous_non_empty_line, "def load_data(path):")


class ExtractorTest(unittest.TestCase):
    def test_extracts_block_signatures(self):
        blocks = extract_blocks(
            "def normalize(items):\n"
            "    result = []\n"
            "    for item in items:\n"
            "        result.append(item)\n"
            "    return result\n"
        )

        signatures = [block.signature for block in blocks]
        self.assertIn("def", signatures)
        self.assertIn("assign", signatures)
        self.assertIn("for", signatures)
        self.assertIn("return", signatures)


class PredictorTest(unittest.TestCase):
    def test_predicts_return_after_assignment_from_training(self):
        predictor = CodeBlockPredictor()
        predictor.update(
            extract_blocks(
                "def normalize(items):\n"
                "    result = []\n"
                "    for item in items:\n"
                "        result.append(item)\n"
                "    return result\n"
            )
        )

        predictions = predictor.predict(
            "def clean(items):\n"
            "    result = []\n"
            "    for item in items:\n"
            "        result.append(item)\n"
            "    <CURSOR>\n",
            top_k=3,
        )

        self.assertTrue(any(prediction.signature == "return" for prediction in predictions))

    def test_template_predicts_function_body_without_training(self):
        predictions = CodeBlockPredictor().predict("def load_data(path):\n<CURSOR>", top_k=2)

        self.assertGreaterEqual(len(predictions), 1)
        self.assertTrue(predictions[0].text.startswith("    "))

    def test_boolean_if_body_prefers_return_true(self):
        predictions = CodeBlockPredictor().predict(
            "def is_positive(number):\n"
            "    if number > 0:\n"
            "        <CURSOR>\n",
            top_k=3,
        )

        self.assertEqual(predictions[0].text.strip(), "return True")

    def test_append_to_self_collection_prefers_len_return(self):
        predictions = CodeBlockPredictor().predict(
            "class TaskList:\n"
            "    def __init__(self):\n"
            "        self.tasks = []\n"
            "\n"
            "    def add(self, task):\n"
            "        self.tasks.append(task)\n"
            "        <CURSOR>\n",
            top_k=3,
        )

        self.assertEqual(predictions[0].text.strip(), "return len(self.tasks)")


class EmbeddingTest(unittest.TestCase):
    def test_related_code_has_positive_similarity(self):
        embedder = HashedTfidfEmbedder()
        embedder.fit(["return result", "result.append(item)", "path.open()"])

        left = embedder.encode("return result")
        right = embedder.encode("return results")

        self.assertGreater(cosine_similarity(left, right), 0)


class EvaluationTest(unittest.TestCase):
    def test_evaluation_report_contains_baseline(self):
        predictor = CodeBlockPredictor()
        source = (
            "def collect(items):\n"
            "    result = []\n"
            "    for item in items:\n"
            "        result.append(item)\n"
            "    return result\n"
        )
        predictor.update(extract_blocks(source))

        report = evaluate_predictor(predictor, [ROOT / "examples" / "sample_project.py"], top_k=3)

        self.assertIn("block_prediction", report)
        self.assertIn("model_signature_accuracy", report["block_prediction"])
        self.assertIn("template_baseline_signature_accuracy", report["block_prediction"])
        self.assertGreater(report["data_split"]["test_block_cases"], 0)


class TokenPredictorTest(unittest.TestCase):
    def test_completes_builtin_keyword_and_context_variable(self):
        predictor = TokenPredictor()

        builtin = predictor.predict("pri<CURSOR>", top_k=3)
        variable = predictor.predict("numbers = [1, 2, 3]\nnum<CURSOR>", top_k=3)

        self.assertTrue(any(item.suggestion == "print" for item in builtin))
        self.assertTrue(any(item.suggestion == "numbers" for item in variable))


if __name__ == "__main__":
    unittest.main()
