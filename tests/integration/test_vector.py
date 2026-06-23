from smolrag.actions import list_actions


def test_index_action_builds_index(fixture_project, capsys):
    """Index the fixture project and verify the completion message."""
    IndexAction = list_actions()["index"]
    action = IndexAction(fixture_project)
    action.run()
    captured = capsys.readouterr()
    assert "Index built." in captured.out


def test_searchvector_finds_results(fixture_project, monkeypatch, capsys):
    """Index the fixture, then search for a term present in the code."""
    IndexAction = list_actions()["index"]
    IndexAction(fixture_project).run()

    SearchVectorAction = list_actions()["debug-searchvector"]
    query_input = "eat"
    monkeypatch.setattr("builtins.input", lambda _: query_input)
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
    SearchVectorAction = list_actions()["debug-searchvector"]
    monkeypatch.setattr("builtins.input", lambda _: "")
    SearchVectorAction(fixture_project).run()
    captured = capsys.readouterr()
    assert "No query provided." in captured.out


def test_searchvector_no_index_shows_message(fixture_project, monkeypatch, capsys):
    """Search without a prior index build shows 'No results for'."""
    SearchVectorAction = list_actions()["debug-searchvector"]
    query_input = "main"
    monkeypatch.setattr("builtins.input", lambda _: query_input)
    SearchVectorAction(fixture_project).run()
    captured = capsys.readouterr()
    assert f"No results for '{query_input}'." in captured.out


def test_searchvector_nonsense_returns_empty(fixture_project, monkeypatch, capsys):
    """A nonsense query that matches nothing shows 'No results for'."""
    IndexAction = list_actions()["index"]
    IndexAction(fixture_project).run()

    SearchVectorAction = list_actions()["debug-searchvector"]
    nonsense = "xyznonexistent123"
    monkeypatch.setattr("builtins.input", lambda _: nonsense)
    SearchVectorAction(fixture_project).run()
    captured = capsys.readouterr()
    assert f"No results for '{nonsense}'." in captured.out


def test_searchvector_output_has_context_block_structure(fixture_project, monkeypatch, capsys):
    """The output follows the ContextBuilder markdown format and contains
    the full source code of matching files."""
    IndexAction = list_actions()["index"]
    IndexAction(fixture_project).run()

    SearchVectorAction = list_actions()["debug-searchvector"]
    monkeypatch.setattr("builtins.input", lambda _: "Cat")
    SearchVectorAction(fixture_project).run()
    captured = capsys.readouterr()

    assert "## Retrieved code snippets:" in captured.out
    assert "augmented with RAG capabilities" in captured.out
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
