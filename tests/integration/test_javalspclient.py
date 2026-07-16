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


def test_references_code_has_no_duplicates(fixture_project, require_lsp):
    """References to the Cat class contain no deep-equal duplicate snippets,
    even when one line holds multiple references (e.g. 'Cat cat = (Cat) pet;')."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        snippets = client.references_code(CAT, 5, 13)

    assert snippets
    for i, a in enumerate(snippets):
        for b in snippets[i + 1:]:
            assert a != b, f"duplicate snippets: {a.to_tool_output()}"


def test_definition_code_end_line_too_narrow(fixture_project, require_lsp):
    """FIXME: definition_code returns end_line only covering the declaration,
    not the full class/method body.

    Compare: document_symbols_code returns the full range (Cat class is
    lines 5–41 in Cat.java). definition_code may return only the declaration
    line.
    """
    client = JavaLSPClient(fixture_project)
    with client.start():
        def_snippets = client.definition_code(MAIN, 4, 8)
        doc_snippets = client.document_symbols_code(CAT)

    assert len(def_snippets) == 1
    def_range = def_snippets[0]

    cat_class = [s for s in doc_snippets if s.symbol_name == "Cat" and s.symbol_kind == "class"]
    assert len(cat_class) == 1
    doc_range = cat_class[0]

    if def_range.end_line < doc_range.end_line:
        print(f"\n  BAD: definition end_line={def_range.end_line}, "
              f"document_symbol end_line={doc_range.end_line} "
              f"(file has {doc_range.total_lines} lines)")
        assert False, (
            f"definition_code end_line ({def_range.end_line}) is narrower than "
            f"document_symbols_code ({doc_range.end_line}) — "
            f"FIXME confirmed: use document_symbols_code to fix end_lines"
        )
    else:
        print(f"\n  OK: definition end_line={def_range.end_line} >= document_symbol end_line={doc_range.end_line}")


def test_references_code_end_line_too_narrow(fixture_project, require_lsp):
    """FIXME: references_code returns end_line covering only the reference
    token, not the enclosing method/class.

    Compare: references to Cat.scratch() in Veterinarian.treat(Cat) should
    span the full treat() method (lines 49–53), but LSP references only
    return the single line containing the reference.
    """
    client = JavaLSPClient(fixture_project)
    with client.start():
        ref_snippets = client.references_code(CAT, 33, 16)
        doc_snippets = client.document_symbols_code(VET)

    vet_ref = [s for s in ref_snippets if s.path == VET]
    assert len(vet_ref) == 1
    ref_range = vet_ref[0]

    treat_cat_method = [s for s in doc_snippets
                        if s.symbol_name == "treat(Cat)" and s.symbol_kind == "method"]
    assert len(treat_cat_method) == 1
    doc_range = treat_cat_method[0]

    if ref_range.end_line < doc_range.end_line:
        print(f"\n  BAD: reference end_line={ref_range.end_line}, "
              f"document_symbol end_line={doc_range.end_line} "
              f"(file has {doc_range.total_lines} lines)")
        assert False, (
            f"references_code end_line ({ref_range.end_line}) is narrower than "
            f"document_symbols_code ({doc_range.end_line}) — "
            f"FIXME confirmed: use document_symbols_code to fix end_lines"
        )
    else:
        print(f"\n  OK: reference end_line={ref_range.end_line} >= document_symbol end_line={doc_range.end_line}")
