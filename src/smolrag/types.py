from dataclasses import dataclass


@dataclass
class CodeSnippet:
    """Unified result from any retrieval method (LSP, BM25, embeddings, etc.)."""

    code: str
    path: str
    start_line: int
    end_line: int

    def __str__(self) -> str:
        return f"{self.path}@{self.start_line}:{self.end_line}"
