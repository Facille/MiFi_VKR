from pathlib import Path


def collect_python_files(root: Path):
    files = []
    for path in root.rglob("*.py"):
        files.append(path)
    return files


def read_file(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        content = handle.read()
    return content


def summarize_lengths(paths):
    result = {}
    for path in paths:
        result[path.name] = len(read_file(path))
    return result


class ProjectIndex:
    def __init__(self, root: Path):
        self.root = root

    def build(self):
        files = collect_python_files(self.root)
        return summarize_lengths(files)
