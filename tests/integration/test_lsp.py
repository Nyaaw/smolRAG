import pytest

from smolrag.actions import list_actions

pytestmark = [pytest.mark.lsp, pytest.mark.slow]


def test_search_lsp_finds_class(fixture_project, require_lsp, monkeypatch, capsys):
    """Search LSP for 'Cat' and verify the full class code with Javadoc."""
    SearchLspAction = {a.name: a for a in list_actions()}["search-lsp"]
    action = SearchLspAction(fixture_project)
    monkeypatch.setattr("builtins.input", lambda _: "Cat")
    action.run()
    captured = capsys.readouterr()

    assert "public class Cat extends Mammal implements Pet" in captured.out
    assert "A cat is a mammal that can be kept as a pet." in captured.out
    assert "Constructs a new Cat." in captured.out
    assert 'super("Felis catus", age, furColor)' in captured.out
    assert "public String getName()" in captured.out
    assert "return name;" in captured.out
    assert "public void makeSound()" in captured.out
    assert 'System.out.println("Meow")' in captured.out
    assert "Makes the cat scratch a surface." in captured.out
    assert 'System.out.println(name + " scratches the furniture")' in captured.out
    assert "```java" in captured.out


def test_search_lsp_finds_interface(fixture_project, require_lsp, monkeypatch, capsys):
    """Search LSP for 'Pet' and verify the full interface code with Javadoc."""
    SearchLspAction = {a.name: a for a in list_actions()}["search-lsp"]
    action = SearchLspAction(fixture_project)
    monkeypatch.setattr("builtins.input", lambda _: "Pet")
    action.run()
    captured = capsys.readouterr()

    assert "public interface Pet" in captured.out
    assert "Interface representing a pet with basic identifying and behavioural methods." in captured.out
    assert "Returns the name of this pet." in captured.out
    assert "String getName();" in captured.out
    assert "int getAge();" in captured.out
    assert "void makeSound();" in captured.out


def test_search_lsp_no_match_shows_message(fixture_project, require_lsp, monkeypatch, capsys):
    """Searching for a non-existent symbol shows the 'No results' message."""
    SearchLspAction = {a.name: a for a in list_actions()}["search-lsp"]
    action = SearchLspAction(fixture_project)
    monkeypatch.setattr("builtins.input", lambda _: "NoSuchClassXYZ")
    action.run()
    captured = capsys.readouterr()

    assert "No results for" in captured.out


def test_search_lsp_empty_query_shows_message(fixture_project, require_lsp, monkeypatch, capsys):
    """Empty query shows 'No query provided.'"""
    SearchLspAction = {a.name: a for a in list_actions()}["search-lsp"]
    action = SearchLspAction(fixture_project)
    monkeypatch.setattr("builtins.input", lambda _: "")
    action.run()
    captured = capsys.readouterr()

    assert "No query provided." in captured.out


def test_search_lsp_output_has_context_block(fixture_project, require_lsp, monkeypatch, capsys):
    """LSP search output follows ContextBuilder markdown format with real code."""
    SearchLspAction = {a.name: a for a in list_actions()}["search-lsp"]
    action = SearchLspAction(fixture_project)
    monkeypatch.setattr("builtins.input", lambda _: "Cat")
    action.run()
    captured = capsys.readouterr()

    assert "## Retrieved code snippets:" in captured.out
    assert "```java" in captured.out
    assert "public class Cat extends Mammal implements Pet" in captured.out
    assert "public Cat(String name, int age, String furColor)" in captured.out
    assert "public void scratch()" in captured.out
    assert 'System.out.println("Meow")' in captured.out


def test_explain_action_finds_class_with_inheritance(fixture_project, require_lsp, monkeypatch, capsys):
    """Full explain pipeline: index + LSP + BM25 + enrich + dedup + context.

    Verifies that the target class code is present and that inheritance
    enrichment pulls in parent class and interface definitions.
    """
    IndexAction = {a.name: a for a in list_actions()}["index"]
    IndexAction(fixture_project).run()

    ExplainAction = {a.name: a for a in list_actions()}["explain"]
    action = ExplainAction(fixture_project)
    monkeypatch.setattr("builtins.input", lambda _: "Cat")
    action.run()
    captured = capsys.readouterr()

    assert "Explain the following symbol: Cat" in captured.out
    assert "```java" in captured.out
    # Target class
    assert "public class Cat extends Mammal implements Pet" in captured.out
    assert "Constructs a new Cat." in captured.out
    assert 'System.out.println("Meow")' in captured.out
    # Inheritance enrichment: parent class Mammal
    assert "public abstract class Mammal extends Animal" in captured.out
    assert "Mammals consume food through their mouth." in captured.out
    # Inheritance enrichment: interface Pet
    assert "public interface Pet" in captured.out
    assert "String getName();" in captured.out
    assert "void makeSound();" in captured.out
