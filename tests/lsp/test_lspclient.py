import pytest

from smolrag.lsp import JavaLSPClient
from smolrag.lsp.lspclient import LspClient


def _offline_client(project_root: str = "/proj") -> JavaLSPClient:
    """A JavaLSPClient with no language server, for pure path helpers."""
    client = object.__new__(JavaLSPClient)
    client._project_root = project_root
    return client


class TestReadCodeRange:
    def test_reads_inclusive_range(self, tmp_path):
        f = tmp_path / "f.txt"
        f.write_text("a\nb\nc\nd\n")
        assert LspClient.read_code_range(str(f), 1, 2) == ("b\nc", 2, 4)

    def test_reads_single_line(self, tmp_path):
        f = tmp_path / "f.txt"
        f.write_text("a\nb\nc\n")
        assert LspClient.read_code_range(str(f), 1, 1) == ("b", 1, 3)

    def test_end_clamped_to_file_length(self, tmp_path):
        f = tmp_path / "f.txt"
        f.write_text("a\nb\n")
        assert LspClient.read_code_range(str(f), 0, 99) == ("a\nb", 1, 2)

    def test_clamped_end_preserves_line_count_invariant(self, tmp_path):
        f = tmp_path / "f.txt"
        f.write_text("a\nb\nc\n")
        code, end_line, _ = LspClient.read_code_range(str(f), 1, 42)
        assert len(code.splitlines()) == end_line - 1 + 1

    def test_start_out_of_range_returns_empty_with_total(self, tmp_path):
        f = tmp_path / "f.txt"
        f.write_text("a\nb\n")
        assert LspClient.read_code_range(str(f), 5, 9) == ("", 9, 2)

    def test_missing_file_returns_empty(self, tmp_path):
        assert LspClient.read_code_range(str(tmp_path / "nope.txt"), 0, 1) == ("", 1, 0)


class TestKindName:
    @pytest.mark.parametrize(
        "kind, expected",
        [
            (5, "class"),
            (6, "method"),
            (11, "interface"),
            (12, "function"),
            (13, "variable"),
        ],
    )
    def test_known_kinds(self, kind, expected):
        assert LspClient._kind_name(kind) == expected

    def test_none_returns_none(self):
        assert LspClient._kind_name(None) is None

    def test_unknown_kind_returns_none(self):
        assert LspClient._kind_name(9999) is None


class TestPathHelpers:
    def test_uri_to_abs_path(self):
        client = _offline_client()
        assert client._uri_to_abs_path("file:///proj/src/A.java") == "/proj/src/A.java"

    def test_uri_to_abs_path_unquotes_percent_encoding(self):
        client = _offline_client()
        assert client._uri_to_abs_path("file:///proj/my%20dir/A.java") == "/proj/my dir/A.java"

    def test_non_file_uri_returns_none(self):
        client = _offline_client()
        assert client._uri_to_abs_path("https://example.com/A.java") is None

    def test_abs_to_rel_path(self):
        client = _offline_client("/proj")
        assert client._abs_to_rel_path("/proj/src/A.java") == "src/A.java"
