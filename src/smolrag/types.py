from dataclasses import dataclass


@dataclass
class CodeSnippet:
    """Unified result from any retrieval method (LSP, BM25, embeddings, etc.)."""

    code: str
    path: str
    start_line: int
    end_line: int
    # TODO: add source of retrieval. for example: "LSP workplace search 'query'", "BM25 search 'query'", "parent of codesnippet file@24:50", "used in codesnippet other_file@1:12"

    def __str__(self) -> str:
        return f"{self.path}@{self.start_line}:{self.end_line}"
