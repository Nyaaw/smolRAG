from collections import OrderedDict

from smolrag.codesnippet import CodeSnippet


def dedup(snippets: list[CodeSnippet]) -> list[CodeSnippet]:
    """Merge overlapping :class:`CodeSnippet` entries within each file.

    When two snippets in the same file have intersecting line ranges,
    they are merged into a single snippet whose range is the union of
    the two and whose code is the concatenation of both (in original
    order).  The merged snippet inherits ``source`` and ``parent`` from
    the first (highest-order) snippet in the group.

    After merging, any snippet whose ``parent`` referenced a merged-away
    original is updated to point to the final merged object.
    """
    orig_to_merged: dict[int, CodeSnippet] = {}

    files: OrderedDict[str, list[CodeSnippet]] = OrderedDict()
    for s in snippets:
        files.setdefault(s.path, []).append(s)

    result: list[CodeSnippet] = []
    for path, snippets_in_path in files.items():
        snippets_in_path.sort(key=lambda s: (s.start_line, s.end_line))
        merged = _merge_overlapping(snippets_in_path, orig_to_merged)
        result.extend(merged)

    _fixup_parents(result, orig_to_merged)
    return result


def _merge_overlapping(
    sorted_snippets: list[CodeSnippet],
    orig_to_merged: dict[int, CodeSnippet],
) -> list[CodeSnippet]:
    """Merge a sorted-by-start_line list of same-file snippets.

    Walks the list left to right, accumulating adjacent or overlapping
    snippets into a single CodeSnippet.  When two ranges intersect, the
    shared prefix is stripped from the later snippet so no lines are
    duplicated in the concatenated code.

    Records every original snippet's final merged counterpart in
    *orig_to_merged* so that ``parent`` references can be fixed up
    afterwards.
    """
    merged: list[CodeSnippet] = []
    current = sorted_snippets[0]
    group: list[CodeSnippet] = [current]

    def _finalize_group() -> None:
        for g in group:
            orig_to_merged[id(g)] = current

    for s in sorted_snippets[1:]:
        if s.start_line <= current.end_line:
            overlap_lines = current.end_line - s.start_line + 1
            s_lines = s.code.split("\n")
            tail = "\n".join(s_lines[overlap_lines:])
            current = CodeSnippet(
                code=current.code + "\n" + tail if tail else current.code,
                path=current.path,
                start_line=current.start_line,
                end_line=max(current.end_line, s.end_line),
                source=current.source,
                parent=current.parent,
                retrieval_depth=current.retrieval_depth,
                symbol_name=current.symbol_name,
                symbol_kind=current.symbol_kind,
            )
            group.append(s)
        else:
            _finalize_group()
            merged.append(current)
            current = s
            group = [current]

    _finalize_group()
    merged.append(current)
    return merged


def _fixup_parents(
    snippets: list[CodeSnippet],
    orig_to_merged: dict[int, CodeSnippet],
) -> None:
    """Redirect ``parent`` references that point to a merged-away
    original to the final merged snippet."""
    for s in snippets:
        if s.parent is None:
            continue
        pid = id(s.parent)
        if pid in orig_to_merged:
            s.parent = orig_to_merged[pid]
