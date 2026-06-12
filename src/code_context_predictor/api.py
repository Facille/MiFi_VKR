"""Local HTTP API and demo UI for the predictor."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .model import CodeBlockPredictor
from .token_predictor import TokenPredictor


WEB_DIR = Path(__file__).resolve().parent / "web"


def run_server(model_path: str | Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    predictor = CodeBlockPredictor.load(model_path)
    token_predictor = TokenPredictor()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path in {"/", "/index.html"}:
                self._send_file(WEB_DIR / "index.html", "text/html; charset=utf-8")
                return
            if path == "/health":
                self._send_json({"status": "ok", "model": str(model_path)})
                return
            self.send_error(404)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path != "/predict":
                self.send_error(404)
                return
            payload = self._read_json()
            source = str(payload.get("source", ""))
            top_k = int(payload.get("top_k", 5))
            prefix = source.split("<CURSOR>", 1)[0] if "<CURSOR>" in source else source
            context = predictor.analyzer.analyze(prefix)
            predictions = predictor.predict_from_context(context, top_k=top_k)
            token_suggestions = token_predictor.predict_from_context(context, top_k=top_k)
            self._send_json(
                {
                    "context": {
                        "scope_kind": context.scope_kind,
                        "scope_path": list(context.scope_path),
                        "imports": list(context.imports),
                        "functions": list(context.functions),
                        "classes": list(context.classes),
                        "variables": list(context.variables),
                        "function_arguments": list(context.function_arguments),
                        "last_active_construct": context.last_active_construct,
                        "nesting_depth": context.nesting_depth,
                        "current_token_prefix": context.current_token_prefix,
                        "nearest_parent_block": context.nearest_parent_block,
                        "indentation": context.indentation,
                        "open_block": context.open_block,
                        "recent_signatures": list(context.recent_signatures),
                    },
                    "token_suggestions": [
                        {
                            "suggestion": item.suggestion,
                            "confidence": item.confidence,
                            "reason": item.reason,
                            "source": item.source,
                        }
                        for item in token_suggestions
                    ],
                    "predictions": [
                        {
                            "code": item.code,
                            "confidence": item.confidence,
                            "source": item.source,
                            "signature": item.signature,
                            "reason": item.reason,
                            "matched_features": item.matched_features,
                        }
                        for item in predictions
                    ]
                }
            )

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            return

        def _read_json(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            return json.loads(raw or "{}")

        def _send_json(self, payload: dict[str, object]) -> None:
            data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_file(self, path: Path, content_type: str) -> None:
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Serving predictor UI on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local predictor API and demo UI.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    run_server(args.model, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
