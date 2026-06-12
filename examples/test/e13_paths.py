from pathlib import Path


def collect_python_files(root: Path):
    result = []
    for path in root.rglob("*.py"):
        if path.is_file():
            result.append(path)
    return result
