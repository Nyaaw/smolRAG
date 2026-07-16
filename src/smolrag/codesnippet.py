from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CodeSnippet:
    """Unified result from any retrieval method (LSP, BM25, embeddings, etc.)."""

    code: str
    path: str
    start_line: int
    end_line: int
    total_lines: int
    source: str
    parent: CodeSnippet | None = None
    retrieval_depth: int = 0
    symbol_name: str | None = None
    symbol_kind: str | None = None

    def __str__(self) -> str:
        return f"{self.path}@{self.start_line}:{self.end_line}"
    
    def to_action_output(self) -> str:
        """Complete representation used in context_manager.py, 
        
        """
        base = f"{self.path} ({self.total_lines} lines)@{self.start_line}:{self.end_line}, source: {self.source}"
        if self.parent is not None:
            base += f" of {self.parent}"
        return base

    def to_tool_output(self, include_code: bool = False) -> str:
        """Compact representation for LLM tool responses.

        :param include_code: If True, append the source code after the header line.
        """
        parts = [f"{self.path} ({self.total_lines} lines)@{self.start_line}:{self.end_line}"]
        if self.symbol_kind is not None:
            parts.append(self.symbol_kind)
        if self.symbol_name is not None:
            parts.append(self.symbol_name)
        result = " ".join(parts)
        if include_code:    
            result += "\n" + CodeSnippet.with_line_numbers(self.code, self.start_line)
        return result

    @staticmethod
    def with_line_numbers(code: str, start_line: int) -> str:
        """Prepend each line of *code* with its absolute 0-based line number
        in the source file, starting at *start_line*, followed by a space.
        """
        return "\n".join(f"{start_line + i} {line}" for i, line in enumerate(code.splitlines()))
