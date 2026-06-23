from smolrag.flatten import flatten
from smolrag.types import CodeSnippet


class ContextBuilder:
    """Formats a list of CodeSnippets into a context block for an LLM."""

    def build(self, query: str, snippets: list[CodeSnippet]) -> str:
        ordered = flatten(snippets)
        parts: list[str] = [
            "You are a helpful assistant, augmented with RAG capabilities. "
            "You will answer the user's request using the code snippets "
            "the RAG system retrieved for you.",
            "",
            f"## Query: {query}",
            "",
            "## Retrieved code snippets:",
            "",
        ]
        for s in ordered:
            parts.append(f"### {self._heading(s)}")
            parts.append("")
            parts.append("```java")
            parts.append(s.code)
            parts.append("```")
            parts.append("")
        return "\n".join(parts)

    @staticmethod
    def _heading(snippet: CodeSnippet) -> str:
        """Build a heading for *snippet* that includes its source and,
        for enrichment children, a reference to the parent snippet."""
        base = str(snippet)
        if snippet.parent is not None:
            base += f" of {snippet.parent}"
        return base
