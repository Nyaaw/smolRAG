from smolrag.types import CodeSnippet


def flatten(snippets: list[CodeSnippet]) -> list[CodeSnippet]:
    """Flatten a list of :class:`CodeSnippet` objects into depth-first
    order using their ``parent`` references.

    Snippets with ``parent is None`` are treated as roots and emitted
    first, each followed by its children (recursively).  Order among
    roots and among siblings is preserved from the input list.
    """
    result: list[CodeSnippet] = []
    visited: set[int] = set()

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
        if s.parent is None:
            _dfs(s)

    return result
