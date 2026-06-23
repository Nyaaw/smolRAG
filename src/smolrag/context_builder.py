from smolrag.flatten import flatten
from smolrag.types import CodeSnippet


class ContextBuilder:
    """Formats a list of CodeSnippets into a context block for an LLM."""

    def build(self, query: str, snippets: list[CodeSnippet]) -> str:
        ordered = flatten(snippets)
        parts = [
            f"## Query: {query}\n",
            "The following code was found in the project:\n",
        ]
        for s in ordered:
            parts.append(f"### `{s}`\n")
            parts.append("```java")
            parts.append(s.code)
            parts.append("```\n")
        return "\n".join(parts)
