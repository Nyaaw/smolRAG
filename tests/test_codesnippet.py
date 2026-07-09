import pytest
from smolrag.codesnippet import CodeSnippet


@pytest.mark.parametrize(
    "path, start, end, source, expected_str",
    [
        ("Foo.java", 0, 5, "LSP", "Foo.java@0:5, source: LSP"),
        ("src/main/Bar.java", 10, 25, "BM25: 'query'", "src/main/Bar.java@10:25, source: BM25: 'query'"),
        ("a/b/c.py", 0, 0, "file chunk", "a/b/c.py@0:0, source: file chunk"),
        ("file.txt", 100, 200, "superclass or interface of\nFoo.java@24:50", "file.txt@100:200, source: superclass or interface of\nFoo.java@24:50"),
    ],
    ids=["simple", "nested-path", "zero-range", "large-range"],
)
def test_codesnippet_str(path, start, end, source, expected_str):
    """CodeSnippet.__str__ formats as path@start:end, source."""
    snippet = CodeSnippet(code="dummy", path=path, start_line=start, end_line=end, source=source)
    assert str(snippet) == expected_str
