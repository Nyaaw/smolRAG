import pytest
from smolrag.types import CodeSnippet


@pytest.mark.parametrize(
    "path, start, end, expected_str",
    [
        ("Foo.java", 0, 5, "Foo.java@0:5"),
        ("src/main/Bar.java", 10, 25, "src/main/Bar.java@10:25"),
        ("a/b/c.py", 0, 0, "a/b/c.py@0:0"),
        ("file.txt", 100, 200, "file.txt@100:200"),
    ],
    ids=["simple", "nested-path", "zero-range", "large-range"],
)
def test_codesnippet_str(path, start, end, expected_str):
    """CodeSnippet.__str__ formats as path@start:end."""
    snippet = CodeSnippet(code="dummy", path=path, start_line=start, end_line=end)
    assert str(snippet) == expected_str
