from smolrag.actions import list_actions

from tests.helpers import patch_prompt


def test_index_action_builds_index(fixture_project, capsys):
    """Index the fixture project and verify the completion message."""
    IndexAction = {a.name: a for a in list_actions()}["index"]
    action = IndexAction(fixture_project)
    action.run()
    captured = capsys.readouterr()
    assert "Index built." in captured.out


def test_searchvector_finds_results(fixture_project, monkeypatch, capsys):
    """Index the fixture, then search for a term present in the code."""
    IndexAction = {a.name: a for a in list_actions()}["index"]
    IndexAction(fixture_project).run()

    SearchVectorAction = {a.name: a for a in list_actions()}["search-vector"]
    query_input = "eat"
    patch_prompt(monkeypatch, SearchVectorAction, query_input)
    SearchVectorAction(fixture_project).run()
    captured = capsys.readouterr()

    assert "## Retrieved code snippets:" in captured.out
    assert f"BM25 search '{query_input}'" in captured.out
    assert "```java" in captured.out
    # Animal.java: abstract eat() with Javadoc
    assert "public abstract void eat();" in captured.out
    assert "Actions performed when the animal eats." in captured.out
    # Mammal.java: eat() override with Javadoc and body
    assert "Mammals consume food through their mouth." in captured.out
    assert "public void eat()" in captured.out
    assert 'species + " is eating"' in captured.out
    assert "@Override" in captured.out


def test_searchvector_empty_query_shows_message(fixture_project, monkeypatch, capsys):
    """Empty query triggers the 'No query provided.' guard."""
    SearchVectorAction = {a.name: a for a in list_actions()}["search-vector"]
    patch_prompt(monkeypatch, SearchVectorAction, "")
    SearchVectorAction(fixture_project).run()
    captured = capsys.readouterr()
    assert "No query provided." in captured.out


def test_searchvector_no_index_shows_message(fixture_project, tmp_path, monkeypatch, capsys):
    """Search without a prior index build shows 'No results for'.

    Uses an isolated SMOLRAG_CACHE_DIR so indexes persisted by other
    tests (or previous runs) cannot leak into this one.
    """
    monkeypatch.setenv("SMOLRAG_CACHE_DIR", str(tmp_path))
    SearchVectorAction = {a.name: a for a in list_actions()}["search-vector"]
    query_input = "main"
    patch_prompt(monkeypatch, SearchVectorAction, query_input)
    SearchVectorAction(fixture_project).run()
    captured = capsys.readouterr()
    assert f"No results for '{query_input}'." in captured.out


def test_searchvector_nonsense_returns_empty(fixture_project, monkeypatch, capsys):
    """A nonsense query that matches nothing shows 'No results for'."""
    IndexAction = {a.name: a for a in list_actions()}["index"]
    IndexAction(fixture_project).run()

    SearchVectorAction = {a.name: a for a in list_actions()}["search-vector"]
    nonsense = "xyznonexistent123"
    patch_prompt(monkeypatch, SearchVectorAction, nonsense)
    SearchVectorAction(fixture_project).run()
    captured = capsys.readouterr()
    assert f"No results for '{nonsense}'." in captured.out


def test_searchvector_output_has_context_block_structure(fixture_project, monkeypatch, capsys):
    """The output follows the ContextBuilder markdown format and contains
    the full source code of matching files."""
    IndexAction = {a.name: a for a in list_actions()}["index"]
    IndexAction(fixture_project).run()

    SearchVectorAction = {a.name: a for a in list_actions()}["search-vector"]
    patch_prompt(monkeypatch, SearchVectorAction, "Cat")
    SearchVectorAction(fixture_project).run()
    captured = capsys.readouterr()

    assert "## Retrieved code snippets:" in captured.out
    assert "enhanced with RAG capabilities" in captured.out
    assert "```java" in captured.out
    assert "```" in captured.out
    # Full Cat class code including Javadoc, constructor, and methods
    assert "public class Cat extends Mammal implements Pet" in captured.out
    assert "Constructs a new Cat." in captured.out
    assert 'super("Felis catus", age, furColor)' in captured.out
    assert "public String getName()" in captured.out
    assert 'System.out.println("Meow")' in captured.out
    assert "Makes the cat scratch a surface." in captured.out
    assert 'System.out.println(name + " scratches the furniture")' in captured.out
