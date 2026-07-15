import pytest

from smolrag.lsp import JavaLSPClient

pytestmark = [pytest.mark.lsp, pytest.mark.slow]

MAIN = "src/main/java/com/example/Main.java"
CAT = "src/main/java/com/example/Cat.java"
VET = "src/main/java/com/example/Veterinarian.java"


def test_definition_code_resolves_class_usage(fixture_project, require_lsp):
    """Definition of 'Cat' used in Main.java resolves to the Cat class declaration."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        snippets = client.definition_code(MAIN, 4, 8)

    assert len(snippets) == 1
    d = snippets[0]
    assert d.path == CAT
    assert d.source == "LSP definition"
    assert "class Cat" in d.code
    assert d.start_line <= 5 <= d.end_line
    assert d.total_lines == 42


def test_definition_code_resolves_method_call(fixture_project, require_lsp):
    """Definition of the scratch() call in Veterinarian.java resolves to Cat.scratch()."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        snippets = client.definition_code(VET, 49, 12)

    assert len(snippets) == 1
    d = snippets[0]
    assert d.path == CAT
    assert d.source == "LSP definition"
    assert "scratch" in d.code


def test_references_code_finds_method_callers(fixture_project, require_lsp):
    """References to Cat.scratch() include the call inside Veterinarian.treat(Cat)."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        snippets = client.references_code(CAT, 33, 16)

    assert snippets
    assert all(s.source == "LSP reference" for s in snippets)
    vet_refs = [s for s in snippets if s.path == VET]
    assert len(vet_refs) == 1
    assert "cat.scratch()" in vet_refs[0].code


def test_references_code_finds_class_usages(fixture_project, require_lsp):
    """References to the Cat class span Main.java and Veterinarian.java."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        snippets = client.references_code(CAT, 5, 13)

    assert len(snippets) >= 3
    paths = {s.path for s in snippets}
    assert MAIN in paths
    assert VET in paths
    assert all(s.source == "LSP reference" for s in snippets)
