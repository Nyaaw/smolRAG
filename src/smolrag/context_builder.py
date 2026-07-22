from pathlib import Path

from smolrag.codesnippet import CodeSnippet

_MAX_CODE_TOKENS = 80_000
_CHARS_PER_TOKEN = 3

_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "context_builder_system.txt").read_text()

#TODO: ids for each codesnippet to make the snippets references in context more readable


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
            _SYSTEM_PROMPT,
            "",
            f"{query}",
            "",
            "## Retrieved code snippets:",
            "",
        ]
        for s in kept:
            parts.append(f"### {s.to_action_output()}")
            parts.append("")
            parts.append("```java")
            parts.append(s.code)
            parts.append("```")
            parts.append("")
        return "\n".join(parts)
