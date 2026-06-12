from pathlib import Path


def load_lines(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    return [line.strip() for line in lines]


def save_lines(path: Path, lines):
    with path.open("w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line + "\n")
    return path


def ensure_directory(path: Path):
    if not path.exists():
        path.mkdir(parents=True)
    return path
