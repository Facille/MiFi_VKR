from pathlib import Path


def collect_files(root: Path):
    result = []
    for path in root.rglob("*"):
        if path.is_file():
            result.append(path)
    return result


def file_name(path: Path):
    return path.name
