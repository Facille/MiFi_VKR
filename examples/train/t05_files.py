from pathlib import Path


def read_text(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        content = handle.read()
    return content


def write_text(path: Path, content: str):
    with path.open("w", encoding="utf-8") as handle:
        handle.write(content)
    return path
