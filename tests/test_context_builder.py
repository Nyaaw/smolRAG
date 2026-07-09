import pytest

from smolrag.context_builder import ContextBuilder
from smolrag.codesnippet import CodeSnippet

from tests.helpers import _cs


def test_heading_no_parent():
    """Heading for a root snippet is just its string representation."""
    s = _cs("foo", "A.java", 0, 5, "LSP search 'query'")
    assert ContextBuilder._heading(s) == "A.java@0:5, source: LSP search 'query'"


def test_heading_with_parent():
    """Heading for an enrichment child includes a reference to the parent."""
    parent = _cs("base", "A.java", 0, 5, "LSP search 'query'")
    child = _cs("derived", "B.java", 10, 15, "superclass or interface", parent=parent)
    assert ContextBuilder._heading(child) == "B.java@10:15, source: superclass or interface of A.java@0:5, source: LSP search 'query'"


def test_build_empty_snippets():
    """Output contains system prompt, query, and snippets header, but no code blocks."""
    result = ContextBuilder.build("Explain Cat", [])
    assert "You are a helpful assistant" in result
    assert "RAG" in result
    assert "## Explain Cat" in result
    assert "## Retrieved code snippets:" in result
    assert "```java" not in result


def test_build_single_snippet():
    """Single snippet produces one code block with correct heading."""
    s = _cs("int x = 1;", "Main.java", 0, 1, "LSP search 'Main'")
    result = ContextBuilder.build("Explain Main", [s])

    assert "## Explain Main" in result
    assert "### Main.java@0:1, source: LSP search 'Main'" in result
    assert "```java\nint x = 1;\n```" in result


def test_build_multiple_snippets():
    """Multiple snippets appear in DFS order, each with their own heading and code block."""
    a = _cs("code A", "A.java", 0, 1, "LSP search 'A'")
    b = _cs("code B", "B.java", 5, 6, "LSP search 'B'")
    c = _cs("code C", "C.java", 10, 11, "BM25 search 'C'")

    result = ContextBuilder.build("Explain all", [a, b, c])

    assert result.count("```java") == 3
    assert result.index("### A.java@0:1") < result.index("### B.java@5:6")
    assert result.index("### B.java@5:6") < result.index("### C.java@10:11")


def test_build_with_parent_child():
    """Child snippets follow their parent in DFS order, headings reflect lineage."""
    parent = _cs("class Animal {}", "Animal.java", 0, 5, "LSP search 'Animal'")
    child = _cs("class Mammal extends Animal {}", "Mammal.java", 0, 3,
                "superclass or interface", parent=parent)

    result = ContextBuilder.build("Explain Animal", [parent, child])

    assert "### Animal.java@0:5, source: LSP search 'Animal'" in result
    assert "### Mammal.java@0:3, source: superclass or interface of Animal.java@0:5, source: LSP search 'Animal'" in result
    pos_parent = result.index("class Animal {}")
    pos_child = result.index("class Mammal")
    assert pos_parent < pos_child


@pytest.mark.parametrize(
    "query",
    [
        "",
        "Short query",
        "Explain the following symbol: Cat",
        "Multi\nline\nquery",
    ],
    ids=["empty", "short", "explain-style", "multiline"],
)
def test_build_query_formats(query):
    """The query appears as a level-2 heading regardless of content."""
    s = _cs("code", "F.java", 0, 0, "test")
    result = ContextBuilder.build(query, [s])
    assert f"## {query}" in result


def test_build_system_prompt_contains_key_phrases():
    """The system prompt includes RAG terminology."""
    result = ContextBuilder.build("query", [])
    assert "RAG capabilities" in result
    assert "code snippets" in result


def test_build_code_fence_is_java():
    """Code blocks use java fence."""
    s = _cs("public class Foo {}", "Foo.java", 0, 0, "LSP")
    result = ContextBuilder.build("q", [s])
    assert "```java" in result
    assert "```" in result
    assert result.count("```java") == 1
