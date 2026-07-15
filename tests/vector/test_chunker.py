from pathlib import Path

from smolrag.vector.chunker import CHUNK_LINES, OVERLAP_LINES, CodeChunker


def _chunk(tmp_path: Path, n: int) -> list:
    f = tmp_path / "F.java"
    f.write_text("\n".join(f"line{i}" for i in range(n)))
    return CodeChunker._chunk_file(f, "F.java")


def test_small_file_single_chunk(tmp_path):
    """A file under CHUNK_LINES produces one snippet covering all lines."""
    chunks = _chunk(tmp_path, 10)
    assert len(chunks) == 1
    c = chunks[0]
    assert (c.start_line, c.end_line, c.total_lines) == (0, 9, 10)
    assert c.path == "F.java"
    assert c.source == "file chunk"
    assert c.code == "\n".join(f"line{i}" for i in range(10))


def test_exactly_chunk_lines_single_chunk(tmp_path):
    """A file of exactly CHUNK_LINES lines is not split."""
    chunks = _chunk(tmp_path, CHUNK_LINES)
    assert len(chunks) == 1
    assert (chunks[0].start_line, chunks[0].end_line) == (0, CHUNK_LINES - 1)


def test_one_line_over_chunk_lines_splits_in_two(tmp_path):
    """CHUNK_LINES + 1 lines produce two overlapping chunks."""
    total = CHUNK_LINES + 1
    chunks = _chunk(tmp_path, total)
    assert [(c.start_line, c.end_line) for c in chunks] == [
        (0, CHUNK_LINES - 1),
        (CHUNK_LINES - OVERLAP_LINES, total - 1),
    ]


def test_large_file_window_boundaries(tmp_path):
    """A 2500-line file produces three windows stepping by CHUNK_LINES - OVERLAP_LINES."""
    chunks = _chunk(tmp_path, 2500)
    assert [(c.start_line, c.end_line) for c in chunks] == [
        (0, 999),
        (900, 1899),
        (1800, 2499),
    ]


def test_chunk_code_matches_line_range(tmp_path):
    """Each chunk's code contains exactly the lines its range declares."""
    total = 2500
    chunks = _chunk(tmp_path, total)
    for c in chunks:
        lines = c.code.splitlines()
        assert len(lines) == c.end_line - c.start_line + 1
        assert lines[0] == f"line{c.start_line}"
        assert lines[-1] == f"line{c.end_line}"
        assert c.total_lines == total


def test_consecutive_chunks_share_overlap(tmp_path):
    """The last OVERLAP_LINES lines of a chunk open the next chunk."""
    chunks = _chunk(tmp_path, 1500)
    assert len(chunks) == 2
    first, second = chunks
    assert first.end_line - second.start_line + 1 == OVERLAP_LINES
    assert first.code.splitlines()[-OVERLAP_LINES:] == second.code.splitlines()[:OVERLAP_LINES]


def test_last_chunk_ends_at_eof(tmp_path):
    """The final chunk always ends on the file's last line."""
    for total in (1001, 1500, 2500, 3700):
        chunks = _chunk(tmp_path, total)
        assert chunks[-1].end_line == total - 1


def test_chunk_project_walks_tree_and_skips_dirs(tmp_path):
    """chunk_project chunks nested text files but skips SKIP_DIRS."""
    (tmp_path / "src" / "sub").mkdir(parents=True)
    (tmp_path / "src" / "A.java").write_text("class A {}")
    (tmp_path / "src" / "sub" / "B.java").write_text("class B {}")
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "Gen.java").write_text("class Gen {}")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]")

    snippets = CodeChunker().chunk_project(str(tmp_path))
    paths = sorted(s.path for s in snippets)
    assert paths == ["src/A.java", "src/sub/B.java"]
