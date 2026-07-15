from pathlib import Path
from typing import Any

from multilspy.multilspy_config import Language

from smolrag.lsp.lspclient import LspClient
from smolrag.codesnippet import CodeSnippet


class JavaLSPClient(LspClient):
    """LSP client for Java projects via Eclipse JDTLS."""

    @property
    def _language(self) -> Language:
        return Language.JAVA

    def document_symbols_code(self, relative_path: str) -> list[CodeSnippet]:
        results, _ = self._lsp.request_document_symbols(relative_path)
        if not results:
            return []

        abs_path = str(Path(self._project_root) / relative_path)
        snippets: list[CodeSnippet] = []
        for r in results:
            rng = r.get("range", {})
            start_line = rng.get("start", {}).get("line", 0)
            end_line = rng.get("end", {}).get("line", 0)
            code, total_lines = LspClient.read_code_range(abs_path, start_line, end_line)
            if not code:
                continue
            snippets.append(
                CodeSnippet(
                    code=code,
                    path=relative_path,
                    start_line=start_line,
                    end_line=end_line,
                    total_lines=total_lines,
                    source="LSP document symbol",
                    symbol_name=r.get("name"),
                    symbol_kind=self._kind_name(r.get("kind")),
                )
            )
        return snippets

    def workspace_symbols_code(self, query: str) -> list[CodeSnippet]:
        results = self._lsp.request_workspace_symbol(query)
        if not results:
            return []

        by_file: dict[str, list[dict]] = {}
        for r in results:
            uri = r.get("location", {}).get("uri", "")
            abs_path = self._uri_to_abs_path(uri)
            if abs_path is None:
                continue
            rel_path = self._abs_to_rel_path(abs_path)
            by_file.setdefault(rel_path, []).append(r)

        snippets: list[CodeSnippet] = []
        for rel_path, ws_results in by_file.items():
            doc_snippets = self.document_symbols_code(rel_path)

            for r in ws_results:
                r_line = (
                    r.get("location", {})
                    .get("range", {})
                    .get("start", {})
                    .get("line", 0)
                )

                best: CodeSnippet | None = None
                best_size: int = 0
                for ds in doc_snippets:
                    if ds.start_line <= r_line <= ds.end_line:
                        size = ds.end_line - ds.start_line
                        if best is None or size < best_size:
                            best = ds
                            best_size = size

                if best is not None:
                    best.source = f"LSP workspace search '{query}'"
                    best.symbol_name = r.get("name", best.symbol_name)
                    kind_name = self._kind_name(r.get("kind"))
                    if kind_name is not None:
                        best.symbol_kind = kind_name
                    snippets.append(best)

        return snippets

    def definition_code(
        self, relative_path: str, line: int, column: int
    ) -> list[CodeSnippet]:
        results = self._lsp.request_definition(relative_path, line, column)
        if not results:
            return []

        snippets: list[CodeSnippet] = []
        for r in results:
            uri = r.get("uri", "")
            abs_path = self._uri_to_abs_path(uri)
            if abs_path is None:
                continue

            rng = r.get("range", {})
            start_line = rng.get("start", {}).get("line", 0)
            end_line = rng.get("end", {}).get("line", 0)

            code, total_lines = LspClient.read_code_range(abs_path, start_line, end_line)
            if not code:
                continue

            snippets.append(
                CodeSnippet(
                    code=code,
                    path=self._abs_to_rel_path(abs_path),
                    start_line=start_line,
                    end_line=end_line,
                    total_lines=total_lines,
                    source="LSP definition",
                )
            )

        return snippets

    def references_code(
        self, relative_path: str, line: int, column: int
    ) -> list[CodeSnippet]:
        results = self._lsp.request_references(relative_path, line, column)
        if not results:
            return []

        snippets: list[CodeSnippet] = []
        for r in results:
            uri = r.get("uri", "")
            abs_path = self._uri_to_abs_path(uri)
            if abs_path is None:
                continue

            rng = r.get("range", {})
            start_line = rng.get("start", {}).get("line", 0)
            end_line = rng.get("end", {}).get("line", 0)

            code, total_lines = LspClient.read_code_range(abs_path, start_line, end_line)
            if not code:
                continue

            snippets.append(
                CodeSnippet(
                    code=code,
                    path=self._abs_to_rel_path(abs_path),
                    start_line=start_line,
                    end_line=end_line,
                    total_lines=total_lines,
                    source="LSP reference",
                )
            )

        return snippets

    def hover(self, relative_path: str, line: int, column: int) -> Any:
        return self._lsp.request_hover(relative_path, line, column)

    def completions(self, relative_path: str, line: int, column: int) -> Any:
        return self._lsp.request_completions(relative_path, line, column)
