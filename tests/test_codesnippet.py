import pytest
from smolrag.codesnippet import CodeSnippet


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
    snippet = CodeSnippet(code="dummy", path=path, start_line=start, end_line=end, total_lines=0, source="ignored")
    assert str(snippet) == expected_str


def test_to_action_output_no_parent():
    """to_action_output includes path, total lines, range, and source."""
    s = CodeSnippet(code="x", path="Foo.java", start_line=2, end_line=8, total_lines=40, source="LSP definition")
    assert s.to_action_output() == "Foo.java (40 lines)@2:8, source: LSP definition"


def test_to_action_output_with_parent():
    """to_action_output appends 'of <parent>' when a parent exists."""
    p = CodeSnippet(code="p", path="Base.java", start_line=0, end_line=5, total_lines=10, source="LSP")
    s = CodeSnippet(code="x", path="Foo.java", start_line=2, end_line=8, total_lines=40,
                    source="superclass or interface", parent=p)
    assert s.to_action_output() == "Foo.java (40 lines)@2:8, source: superclass or interface of Base.java@0:5"


def test_to_tool_output_header_only():
    """Default to_tool_output is a single header line without code."""
    s = CodeSnippet(code="a\nb", path="Foo.java", start_line=0, end_line=1, total_lines=2, source="LSP")
    assert s.to_tool_output() == "Foo.java (2 lines)@0:1"


def test_to_tool_output_with_symbol_metadata():
    """symbol_kind and symbol_name are appended to the header when set."""
    s = CodeSnippet(code="a", path="Foo.java", start_line=0, end_line=0, total_lines=1,
                    source="LSP", symbol_name="getBarkVolume", symbol_kind="method")
    assert s.to_tool_output() == "Foo.java (1 lines)@0:0 method getBarkVolume"


def test_to_tool_output_include_code():
    """include_code=True appends code numbered from the snippet's start_line."""
    s = CodeSnippet(code="a\nb", path="Foo.java", start_line=4, end_line=5, total_lines=10, source="LSP")
    assert s.to_tool_output(include_code=True) == "Foo.java (10 lines)@4:5\n4 a\n5 b"


@pytest.mark.parametrize(
    "code, start_line, expected",
    [
        ("", 0, ""),
        ("single", 0, "0 single"),
        ("a\nb\nc", 0, "0 a\n1 b\n2 c"),
        ("a\nb\nc", 10, "10 a\n11 b\n12 c"),
        ("x\n\ny", 3, "3 x\n4 \n5 y"),
    ],
    ids=["empty", "single-line", "multi-line", "offset", "blank-line"],
)
def test_with_line_numbers(code, start_line, expected):
    """with_line_numbers prepends absolute 0-based line numbers starting at start_line."""
    assert CodeSnippet.with_line_numbers(code, start_line) == expected
