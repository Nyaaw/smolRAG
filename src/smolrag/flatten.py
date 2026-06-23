from smolrag.types import CodeSnippet


def flatten(snippets: list[CodeSnippet]) -> list[CodeSnippet]:
    """Flatten a list of :class:`CodeSnippet` objects into depth-first
    order using their ``parent`` references.

    Snippets with ``parent is None`` are treated as roots and emitted
    first, each followed by its children (recursively).  Snippets whose
    ``parent`` is not present in *snippets* (e.g. after dedup merged it
    away) are also treated as roots.  Unvisited snippets left after the
    initial root pass (e.g. cycles) are visited in a second pass.

    Order among roots and among siblings is preserved from the input list.
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
