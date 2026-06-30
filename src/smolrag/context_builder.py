from smolrag.types import CodeSnippet

_MAX_CODE_TOKENS = 80_000
_CHARS_PER_TOKEN = 3


def _flatten(snippets: list[CodeSnippet]) -> list[CodeSnippet]:
    """Flatten *snippets* into depth-first order using ``parent`` references.

    Snippets with ``parent is None`` are treated as roots and emitted
    first, each followed by its children (recursively).  Snippets whose
    ``parent`` is not present in *snippets* (e.g. after dedup merged it
    away) are also treated as roots.  Unvisited snippets left after the
    initial root pass (e.g. cycles) are visited in a second pass.
    """
    result: list[CodeSnippet] = []
    visited: set[int] = set()
    snippet_ids: set[int] = {id(s) for s in snippets}

    def _dfs(snippet: CodeSnippet) -> None:
        oid = id(snippet)
        if oid in visited:
            return
        visited.add(oid)
        result.append(snippet)
        for child in snippets:
            if child.parent is snippet:
                _dfs(child)

    for s in snippets:
        if s.parent is None or id(s.parent) not in snippet_ids:
            _dfs(s)

    for s in snippets:
        if id(s) not in visited:
            _dfs(s)

    return result


def _tokens(code: str) -> int:
    return (len(code) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN


class ContextBuilder:
    """Formats a list of CodeSnippets into a context block for an LLM."""

    @staticmethod
    def build(query: str, snippets: list[CodeSnippet]) -> str:
        ordered = _flatten(snippets)

        # Horizontal cut: drop the deepest snippets until the token budget
        # is met.
        total_tokens = sum(_tokens(s.code) for s in ordered)
        if total_tokens > _MAX_CODE_TOKENS:
            candidates = sorted(ordered, key=lambda s: s.retrieval_depth, reverse=True)
            to_remove: set[int] = set()
            for s in candidates:
                total_tokens -= _tokens(s.code)
                to_remove.add(id(s))
                if total_tokens <= _MAX_CODE_TOKENS:
                    break
            kept = [s for s in ordered if id(s) not in to_remove]
        else:
            kept = ordered

        parts: list[str] = [
            "You are a helpful assistant, augmented with RAG capabilities. "
            "You will answer the user's request using the code snippets "
            "the retrieval system retrieved for you.",
            "",
            f"## {query}",
            "",
            "## Retrieved code snippets:",
            "",
        ]
        for s in kept:
            parts.append(f"### {ContextBuilder._heading(s)}")
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
