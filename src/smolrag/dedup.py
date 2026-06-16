from collections import OrderedDict

from smolrag.types import CodeSnippet


def dedup(snippets: list[CodeSnippet]) -> list[CodeSnippet]:
    """Merge overlapping :class:`CodeSnippet` entries within each file.

    When two snippets in the same file have intersecting line ranges,
    they are merged into a single snippet whose range is the union of
    the two and whose code is the concatenation of both (in original
    order)
    """
    files: OrderedDict[str, list[CodeSnippet]] = OrderedDict()
    for s in snippets:
        files.setdefault(s.path, []).append(s)

    result: list[CodeSnippet] = []
    for path, snippets_in_path in files.items():
        # stable sort by start_line, then end_line
        snippets_in_path.sort(key=lambda s: (s.start_line, s.end_line))
        merged = _merge_overlapping(snippets_in_path)
        result.extend(merged)

    return result


def _merge_overlapping(
    sorted_snippets: list[CodeSnippet],
) -> list[CodeSnippet]:
    """Merge a sorted-by-start_line list of same-file snippets.

    Walks the list left to right, accumulating adjacent or overlapping
    snippets into a single CodeSnippet.  When two ranges intersect, the
    shared prefix is stripped from the later snippet so no lines are
    duplicated in the concatenated code.
    """
    merged: list[CodeSnippet] = []
    current = sorted_snippets[0]

    for s in sorted_snippets[1:]:
        if s.start_line <= current.end_line:
            # Overlapping — strip the shared prefix from s so lines
            # that appear in both snippets are not duplicated.
            overlap_lines = current.end_line - s.start_line + 1
            s_lines = s.code.split("\n")
            tail = "\n".join(s_lines[overlap_lines:])
            current = CodeSnippet(
                code=current.code + "\n" + tail if tail else current.code,
                path=current.path,
                start_line=current.start_line,
                end_line=max(current.end_line, s.end_line),
            )
        else:
            # Non-overlapping — finalize current, start a new group.
            merged.append(current)
            current = s

    merged.append(current)
    return merged
