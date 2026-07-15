import pytest
from smolrag.dedup import dedup

from .helpers import _code, _cs


@pytest.mark.parametrize("snippets,expected", [
    pytest.param(
        [_cs(_code(0, 5), "f1", 0, 5), _cs(_code(0, 5), "f2", 0, 5)],
        [_cs(_code(0, 5), "f1", 0, 5), _cs(_code(0, 5), "f2", 0, 5)],
        id="different-files",
    ),
    pytest.param(
        [_cs(_code(0, 5), "f2", 0, 5), _cs(_code(0, 5), "f1", 0, 5)],
        [_cs(_code(0, 5), "f2", 0, 5), _cs(_code(0, 5), "f1", 0, 5)],
        id="file-order",
    ),
    pytest.param(
        [_cs(_code(0, 3), "f", 0, 3), _cs(_code(2, 5), "f", 2, 5)],
        [_cs(_code(0, 5), "f", 0, 5)],
        id="overlapping-multiline",
    ),
    pytest.param(
        [_cs(_code(0, 2), "f", 0, 2), _cs(_code(3, 5), "f", 3, 5)],
        [_cs(_code(0, 2), "f", 0, 2), _cs(_code(3, 5), "f", 3, 5)],
        id="adjacent-not-merged",
    ),
    pytest.param(
        [_cs(_code(0, 1), "f", 0, 1), _cs(_code(5, 6), "f", 5, 6)],
        [_cs(_code(0, 1), "f", 0, 1), _cs(_code(5, 6), "f", 5, 6)],
        id="non-overlapping",
    ),
    pytest.param(
        [_cs(_code(0, 10), "f1", 0, 10), _cs(_code(3, 5), "f1", 3, 5)],
        [_cs(_code(0, 10), "f1", 0, 10)],
        id="overlap-fully-contained",
    ),
    pytest.param(
        [_cs(_code(0, 5), "f", 0, 5), _cs(_code(3, 8), "f", 3, 8)],
        [_cs(_code(0, 8), "f", 0, 8)],
        id="overlap-single-line",
    ),
    pytest.param(
        [_cs(_code(0, 3), "f", 0, 3), _cs(_code(2, 6), "f", 2, 6), _cs(_code(5, 9), "f", 5, 9)],
        [_cs(_code(0, 9), "f", 0, 9)],
        id="overlap-chain",
    ),
    pytest.param(
        [_cs(_code(0, 3), "f", 0, 3), _cs(_code(2, 6), "f", 2, 6), _cs(_code(10, 15), "f", 10, 15)],
        [_cs(_code(0, 6), "f", 0, 6), _cs(_code(10, 15), "f", 10, 15)],
        id="overlap-mixed",
    ),
])
def test_dedup(snippets, expected):
    assert dedup(snippets) == expected


class TestDedupSourceAndParent:
    """Tests for source and parent inheritance during dedup merging."""

    def test_inherits_source_from_first(self):
        a = _cs(_code(0, 3), "f.java", 0, 3, source="lsp")
        b = _cs(_code(2, 5), "f.java", 2, 5, source="bm25")
        result = dedup([a, b])
        assert len(result) == 1
        assert result[0].source == "lsp"

    def test_inherits_parent_from_first(self):
        p = _cs("parent_code", "parent.java", 0, 0, source="parent")
        a = _cs(_code(0, 3), "f.java", 0, 3, source="lsp", parent=p)
        b = _cs(_code(2, 5), "f.java", 2, 5, source="bm25")
        result = dedup([a, b])
        assert len(result) == 1
        assert result[0].parent is p

    def test_fixes_up_parent_references_cross_file(self):
        parent = _cs(_code(0, 3), "parent.java", 0, 3, source="lsp")
        parent2 = _cs(_code(2, 6), "parent.java", 2, 6, source="bm25")
        child = _cs("child code", "child.java", 0, 0, source="superclass", parent=parent)

        result = dedup([parent, parent2, child])

        assert len(result) == 2
        merged = result[0]
        assert merged.path == "parent.java"
        c = result[1]
        assert c.path == "child.java"
        assert c.parent is merged

    def test_parent_unchanged_when_not_merged(self):
        p = _cs("parent_code", "parent.java", 0, 0, source="parent")
        a = _cs(_code(0, 3), "a.java", 0, 3, source="lsp", parent=p)
        b = _cs(_code(5, 7), "a.java", 5, 7, source="bm25")

        result = dedup([a, b])

        assert len(result) == 2
        assert result[0].parent is p
        assert result[1].parent is None
