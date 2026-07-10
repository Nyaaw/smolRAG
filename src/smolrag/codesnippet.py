from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CodeSnippet:
    """Unified result from any retrieval method (LSP, BM25, embeddings, etc.)."""

    code: str
    path: str
    start_line: int
    end_line: int
    source: str
    parent: CodeSnippet | None = None
    retrieval_depth: int = 0

    def __str__(self) -> str:
        base = f"{self.path}@{self.start_line}:{self.end_line}, source: {self.source}"
        if self.parent is not None:
            base += f" of {self.parent}"
        return base

    def to_tool_output(self, include_code: bool = False) -> str:
        """Compact representation for LLM tool responses.

        :param include_code: If True, append the source code after the header line.
        """
        result = f"{self.path}@{self.start_line}:{self.end_line} | {self.source}"
        if include_code:
            result += "\n" + self.code
        return result
