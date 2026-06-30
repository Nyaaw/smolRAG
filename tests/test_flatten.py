import pytest
from smolrag.context_builder import _flatten as flatten

from .helpers import _cs


class TestFlatten:
    def test_empty_list(self):
        assert flatten([]) == []

    def test_all_roots_preserves_order(self):
        a = _cs("a", "a.java", 0, 0, source="lsp")
        b = _cs("b", "b.java", 0, 0, source="bm25")
        c = _cs("c", "c.java", 0, 0, source="lsp")
        result = flatten([a, b, c])
        assert result == [a, b, c]

    def test_depth_first_children_after_parent(self):
        a = _cs("a", "a.java", 0, 0, source="lsp")
        a1 = _cs("a1", "a1.java", 0, 0, source="superclass", parent=a)
        a2 = _cs("a2", "a2.java", 0, 0, source="superclass", parent=a)
        b = _cs("b", "b.java", 0, 0, source="lsp")
        result = flatten([a, a1, a2, b])
        assert result == [a, a1, a2, b]

    def test_depth_first_complex_tree(self):
        a = _cs("a", "a.java", 0, 0, source="lsp")
        a1 = _cs("a1", "a1.java", 0, 0, source="superclass", parent=a)
        a2 = _cs("a2", "a2.java", 0, 0, source="containing class", parent=a)
        b = _cs("b", "b.java", 0, 0, source="lsp")
        b1 = _cs("b1", "b1.java", 0, 0, source="superclass", parent=b)
        c = _cs("c", "c.java", 0, 0, source="bm25")
        r1 = _cs("r1", "r1.java", 0, 0, source="bm25")

        snippets = [a, a1, a2, b, b1, c, r1]
        result = flatten(snippets)
        codes = [s.code for s in result]
        assert codes == ["a", "a1", "a2", "b", "b1", "c", "r1"]

    def test_children_before_sibling_roots(self):
        a = _cs("a", "a.java", 0, 0, source="lsp")
        a1 = _cs("a1", "a1.java", 0, 0, source="superclass", parent=a)
        b = _cs("b", "b.java", 0, 0, source="lsp")

        result = flatten([a, a1, b])
        codes = [s.code for s in result]
        assert codes == ["a", "a1", "b"]

    def test_interleaved_children_follow_correct_parent(self):
        a = _cs("a", "a.java", 0, 0, source="lsp")
        a1 = _cs("a1", "a1.java", 0, 0, source="superclass", parent=a)
        b = _cs("b", "b.java", 0, 0, source="lsp")
        b1 = _cs("b1", "b1.java", 0, 0, source="superclass", parent=b)

        result = flatten([a, b, a1, b1])
        codes = [s.code for s in result]
        assert codes == ["a", "a1", "b", "b1"]

    def test_missing_parent_ignored(self):
        """Snippets whose parent is not in the list are treated as roots."""
        orphan = _cs("orphan", "orphan.java", 0, 0, source="superclass")
        orphan.parent = _cs("gone", "gone.java", 0, 0)
        b = _cs("b", "b.java", 0, 0, source="lsp")

        result = flatten([orphan, b])
        codes = [s.code for s in result]
        assert codes == ["orphan", "b"]

    def test_single_root_with_many_children_preserves_child_order(self):
        a = _cs("a", "a.java", 0, 0, source="lsp")
        a1 = _cs("a1", "a1.java", 0, 0, source="superclass", parent=a)
        a2 = _cs("a2", "a2.java", 0, 0, source="containing class", parent=a)
        a3 = _cs("a3", "a3.java", 0, 0, source="superclass", parent=a)

        result = flatten([a, a1, a2, a3])
        codes = [s.code for s in result]
        assert codes == ["a", "a1", "a2", "a3"]

    def test_avoids_cycles(self):
        a = _cs("a", "a.java", 0, 0, source="lsp")
        b = _cs("b", "b.java", 0, 0, source="superclass", parent=a)
        a.parent = b  # cycle: a -> b -> a

        result = flatten([a, b])
        codes = [s.code for s in result]
        assert len(codes) == 2
        assert set(codes) == {"a", "b"}