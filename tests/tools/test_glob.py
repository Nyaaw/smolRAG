import pytest

from smolrag.tools.glob import GlobTool


@pytest.fixture
def project(tmp_path):
    """A small project tree with one file planted outside the root."""
    proj = tmp_path / "proj"
    (proj / "src" / "sub").mkdir(parents=True)
    (proj / "src" / "A.java").write_text("class A {}\n")
    (proj / "src" / "sub" / "B.java").write_text("class B {}\n")
    (proj / "notes.md").write_text("notes\n")
    (tmp_path / "secret.txt").write_text("topsecret\n")
    return proj


def test_glob_recursive_pattern_sorted(project):
    """Recursive ** pattern finds nested files, one per line, sorted."""
    out = GlobTool(str(project)).execute(pattern="**/*.java")
    assert out.splitlines() == ["src/A.java", "src/sub/B.java"]


def test_glob_top_level_pattern(project):
    """Non-recursive pattern only matches at the project root."""
    out = GlobTool(str(project)).execute(pattern="*.md")
    assert out == "notes.md"


def test_glob_no_match_message(project):
    """A pattern matching nothing returns the no-match message."""
    out = GlobTool(str(project)).execute(pattern="**/*.py")
    assert out == "No files matched pattern '**/*.py'."


def test_glob_rejects_parent_traversal(project):
    """Patterns containing .. are rejected before globbing."""
    out = GlobTool(str(project)).execute(pattern="../*.txt")
    assert out == "Error: pattern '../*.txt' escapes the project root."
    assert "secret" not in out


def test_glob_rejects_nested_parent_traversal(project):
    """.. anywhere in the pattern is rejected, even if prefixed."""
    out = GlobTool(str(project)).execute(pattern="src/../../*.txt")
    assert "escapes the project root" in out


def test_glob_rejects_absolute_pattern(project):
    """Absolute patterns are rejected (glob would ignore root_dir)."""
    pattern = str(project.parent / "*.txt")
    out = GlobTool(str(project)).execute(pattern=pattern)
    assert "escapes the project root" in out
    assert "secret" not in out


def test_glob_filters_symlink_escape(project):
    """A symlink pointing outside the project is not listed."""
    (project / "link.txt").symlink_to(project.parent / "secret.txt")
    out = GlobTool(str(project)).execute(pattern="*.txt")
    assert out == "No files matched pattern '*.txt'."


def test_glob_keeps_symlink_inside_project(project):
    """A symlink resolving inside the project is still listed."""
    (project / "alias.md").symlink_to(project / "notes.md")
    out = GlobTool(str(project)).execute(pattern="*.md")
    assert out.splitlines() == ["alias.md", "notes.md"]
