from pathlib import Path

from smolrag.types import CodeSnippet

CHUNK_LINES = 1000
OVERLAP_LINES = 100
MAX_FILE_SIZE_MB = 10
TEXT_SAMPLE_BYTES = 8192

SKIP_DIRS = {
    ".git",
    ".gradle",
    ".idea",
    ".m2",
    ".smolrag",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "generated-sources",
    "generated-test-sources",
    "node_modules",
    "out",
    "target",
    "vendor",
    "venv",
}


class CodeChunker:
    """Walk a project directory, detect plain-text files by content, and
    split them into :class:`CodeSnippet` chunks suitable for embedding and
    retrieval."""

    def chunk_project(self, project_root: str) -> list[CodeSnippet]:
        project_path = Path(project_root)
        snippets: list[CodeSnippet] = []

        for file_path in project_path.rglob("*"):
            if not file_path.is_file():
                continue
            parts = set(file_path.relative_to(project_path).parts)
            if parts & SKIP_DIRS:
                continue
            if not self._is_text_file(file_path):
                continue
            rel_path = str(file_path.relative_to(project_path))
            snippets.extend(self._chunk_file(file_path, rel_path))

        return snippets

    @staticmethod
    def _is_text_file(file_path: Path) -> bool:
        if file_path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            return False
        if file_path.stat().st_size == 0:
            return False
        try:
            with file_path.open("rb") as f:
                return b"\x00" not in f.read(TEXT_SAMPLE_BYTES)
        except OSError:
            return False

    @staticmethod
    def _chunk_file(file_path: Path, rel_path: str) -> list[CodeSnippet]:
        try:
            lines = file_path.read_text().splitlines()
        except OSError:
            return []

        total = len(lines)
        if total == 0:
            return []

        if total <= CHUNK_LINES:
            code = "\n".join(lines)
            return [
                CodeSnippet(
                    code=code,
                    path=rel_path,
                    start_line=0,
                    end_line=total - 1,
                )
            ]

        snippets: list[CodeSnippet] = []
        start = 0
        while start < total:
            end = min(start + CHUNK_LINES, total)
            code = "\n".join(lines[start:end])
            snippets.append(
                CodeSnippet(
                    code=code,
                    path=rel_path,
                    start_line=start,
                    end_line=end - 1,
                )
            )
            if end == total:
                break
            start = end - OVERLAP_LINES

        return snippets
