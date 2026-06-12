from pathlib import Path


def file_exists(path: Path):
    if path.exists():
        return True
    return False
