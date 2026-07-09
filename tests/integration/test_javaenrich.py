import pytest

from smolrag.lsp import JavaLSPClient, JavaEnricher
from smolrag.types import CodeSnippet

pytestmark = [pytest.mark.lsp, pytest.mark.slow]


def _enrich_one(fixture_project: str, snippet: CodeSnippet) -> list[CodeSnippet]:
    """Start LSP, enrich a single snippet, return results."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        enricher = JavaEnricher(client, fixture_project)
        return enricher.enrich_parent([snippet])


def test_enrich_class_with_single_parent(fixture_project, require_lsp):
    """Enriching Mammal (extends Animal) prepends Animal as an enrichment child."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        mammal_snippets = client.find_symbols("Mammal")
    mammal = [s for s in mammal_snippets if s.path.endswith("Mammal.java")][0]

    result = _enrich_one(fixture_project, mammal)
    assert mammal in result

    children = [s for s in result if s is not mammal]
    assert any("abstract class Animal" in s.code for s in children), \
        "enriched parents should include Animal"

    for s in children:
        assert s.source == "superclass or interface"
        assert s.parent is mammal


def test_enrich_class_with_extends_and_implements(fixture_project, require_lsp):
    """Enriching Cat (extends Mammal implements Pet) prepends both parents."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        cat_snippets = client.find_symbols("Cat")
    assert len(cat_snippets) == 1
    cat = cat_snippets[0]

    result = _enrich_one(fixture_project, cat)
    assert len(result) == 3

    parents = result[1:]
    parent_sources = {s.source for s in parents}
    assert parent_sources == {"superclass or interface"}

    parent_names = {s.path for s in parents}
    assert parent_names == {"src/main/java/com/example/Mammal.java", "src/main/java/com/example/Pet.java"}

    for s in parents:
        assert s.parent is cat


def test_enrich_class_with_no_inheritance(fixture_project, require_lsp):
    """Enriching Animal (root class, no extends) produces no enrichment children."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        animal_snippets = client.find_symbols("Animal")
    animal = [s for s in animal_snippets if s.path.endswith("Animal.java")][0]

    result = _enrich_one(fixture_project, animal)
    assert result == [animal]


def test_enrich_interface_no_super(fixture_project, require_lsp):
    """Enriching Pet (interface with no super-interfaces) produces no enrichment."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        pet_snippets = client.find_symbols("Pet")
    assert len(pet_snippets) == 1
    pet = pet_snippets[0]

    result = _enrich_one(fixture_project, pet)
    assert len(result) == 1
    assert result[0] is pet


def test_enrich_standalone_class(fixture_project, require_lsp):
    """Enriching Owner (class with no extends/implements) produces no enrichment."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        owner_snippets = client.find_symbols("Owner")
    assert len(owner_snippets) == 1
    owner = owner_snippets[0]

    result = _enrich_one(fixture_project, owner)
    assert len(result) == 1
    assert result[0] is owner


def test_enrich_method_finds_containing_class(fixture_project, require_lsp):
    """A method-only snippet should find its containing class and enrich with its parents."""
    method = CodeSnippet(
        code="""    public void scratch() {
        System.out.println(name + " scratches the furniture");
    }""",
        path="src/main/java/com/example/Cat.java",
        start_line=33,
        end_line=35,
        source="test fixture",
    )

    result = _enrich_one(fixture_project, method)
    assert len(result) == 3

    assert result[0] is method

    parents = result[1:]
    parent_paths = {s.path for s in parents}
    assert parent_paths == {"src/main/java/com/example/Mammal.java", "src/main/java/com/example/Pet.java"}

    for s in parents:
        assert s.source == "superclass or interface"
        assert s.parent is method


def test_enrich_method_standalone_class_no_inheritance(fixture_project, require_lsp):
    """A method from a class with no inheritance finds the containing class but no parents."""
    method = CodeSnippet(
        code="""    public void adopt(Pet pet) {
        pets.add(pet);
    }""",
        path="src/main/java/com/example/Owner.java",
        start_line=27,
        end_line=29,
        source="test fixture",
    )

    result = _enrich_one(fixture_project, method)
    assert len(result) == 1
    assert result[0] is method


def test_enrich_parent_references_correct(fixture_project, require_lsp):
    """Enriched children have source='superclass or interface' and parent pointing to the original."""
    client = JavaLSPClient(fixture_project)
    with client.start():
        cat_snippets = client.find_symbols("Cat")
    cat = cat_snippets[0]

    result = _enrich_one(fixture_project, cat)

    for s in result:
        if s is cat:
            continue
        assert s.source == "superclass or interface", f"expected enrichment source, got {s.source}"
        assert s.parent is cat, f"expected parent to be Cat snippet, got {s.parent}"
        assert s.code, "enriched child must have code"
