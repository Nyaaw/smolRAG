import pytest

from smolrag.tools.read import ReadTool


@pytest.fixture
def project(tmp_path):
    """A project with a 5-line file, a subdir, and a secret outside the root."""
    proj = tmp_path / "proj"
    (proj / "src").mkdir(parents=True)
    (proj / "src" / "File.java").write_text("l0\nl1\nl2\nl3\nl4\n")
    (tmp_path / "secret.txt").write_text("topsecret\n")
    return proj


def test_read_whole_file(project):
    """No range reads the whole file with 1-based line numbers."""
    out = ReadTool(str(project)).execute(path="src/File.java")
    assert out == "1 l0\n2 l1\n3 l2\n4 l3\n5 l4"


def test_read_line_range(project):
    """start/end are 0-based inclusive; numbering restarts at 1."""
    out = ReadTool(str(project)).execute(path="src/File.java", start=1, end=3)
    assert out == "1 l1\n2 l2\n3 l3"


def test_read_start_only(project):
    """Omitting end reads to the end of the file."""
    out = ReadTool(str(project)).execute(path="src/File.java", start=3)
    assert out == "1 l3\n2 l4"


def test_read_end_clamped(project):
    """An end past EOF is clamped instead of erroring."""
    out = ReadTool(str(project)).execute(path="src/File.java", start=4, end=99)
    assert out == "1 l4"


def test_read_start_out_of_range(project):
    """A start past EOF returns an error message."""
    out = ReadTool(str(project)).execute(path="src/File.java", start=5)
    assert out == "Error: start line 5 is out of range (file has 5 lines)."


def test_read_negative_start(project):
    """A negative start returns an error message."""
    out = ReadTool(str(project)).execute(path="src/File.java", start=-1)
    assert out == "Error: start line -1 is negative."


def test_read_end_before_start(project):
    """end < start returns an error message."""
    out = ReadTool(str(project)).execute(path="src/File.java", start=3, end=1)
    assert out == "Error: end line 1 is before start line 3."


def test_read_missing_file(project):
    """A nonexistent path returns the not-found error."""
    out = ReadTool(str(project)).execute(path="src/Nope.java")
    assert out == "Error: file 'src/Nope.java' not found."


def test_read_directory(project):
    """Reading a directory returns the is-a-directory error."""
    out = ReadTool(str(project)).execute(path="src")
    assert out == "Error: 'src' is a directory, not a file."


def test_read_rejects_parent_traversal(project):
    """.. escaping the root is rejected before any file access."""
    out = ReadTool(str(project)).execute(path="../secret.txt")
    assert out == "Error: path '../secret.txt' escapes the project root."


def test_read_rejects_nested_parent_traversal(project):
    """Traversal hidden behind a valid prefix is still rejected."""
    out = ReadTool(str(project)).execute(path="src/../../secret.txt")
    assert "escapes the project root" in out
    assert "topsecret" not in out


def test_read_rejects_absolute_path_outside(project):
    """An absolute path outside the project is rejected."""
    target = str(project.parent / "secret.txt")
    out = ReadTool(str(project)).execute(path=target)
    assert "escapes the project root" in out
    assert "topsecret" not in out


def test_read_rejects_sibling_prefix_path(project, tmp_path):
    """A sibling dir sharing the root's name prefix is not treated as inside.

    Guards against the old startswith() check where '/x/proj-evil'
    passed the '/x/proj' prefix test.
    """
    evil = tmp_path / "proj-evil"
    evil.mkdir()
    (evil / "secret.txt").write_text("topsecret\n")
    out = ReadTool(str(project)).execute(path="../proj-evil/secret.txt")
    assert "escapes the project root" in out
    assert "topsecret" not in out


def test_read_rejects_symlink_escape(project):
    """A symlink inside the project pointing outside is rejected."""
    (project / "link.txt").symlink_to(project.parent / "secret.txt")
    out = ReadTool(str(project)).execute(path="link.txt")
    assert "escapes the project root" in out
    assert "topsecret" not in out
