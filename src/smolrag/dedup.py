from smolrag.types import CodeSnippet


def dedup(snippets: list[CodeSnippet]) -> list[CodeSnippet]:
    """Remove overlapping :class:`CodeSnippet` entries, preserving order.

    Two snippets overlap when they belong to the same file and their line
    ranges intersect.  The first occurrence wins, so place higher-quality
    results (e.g. LSP) before lower-priority results (e.g. BM25).
    """
    seen: list[tuple[str, int, int]] = []
    result: list[CodeSnippet] = []

    for s in snippets:
        overlaps = any(
            s.path == path and s.start_line <= end and s.end_line >= start
            for path, start, end in seen
        )
        if overlaps:
            continue
        seen.append((s.path, s.start_line, s.end_line))
        result.append(s)

    return result
