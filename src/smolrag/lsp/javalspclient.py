import os
from pathlib import Path, PurePath
from urllib.parse import unquote

from multilspy.multilspy_config import Language

from smolrag.lsp.lspclient import LspClient
from smolrag.types import CodeSnippet


class JavaLSPClient(LspClient):
    """LSP client for Java projects via Eclipse JDTLS."""

    @property
    def _language(self) -> Language:
        return Language.JAVA

    def document_symbols(self, relative_path: str):
        return self._lsp.request_document_symbols(relative_path)

    def workspace_symbols(self, query: str):
        return self._lsp.request_workspace_symbol(query)

    def definition(self, relative_path: str, line: int, column: int):
        return self._lsp.request_definition(relative_path, line, column)

    def references(self, relative_path: str, line: int, column: int):
        return self._lsp.request_references(relative_path, line, column)

    def hover(self, relative_path: str, line: int, column: int):
        return self._lsp.request_hover(relative_path, line, column)

    def completions(self, relative_path: str, line: int, column: int):
        return self._lsp.request_completions(relative_path, line, column)

    def find_symbols(self, query: str) -> list[CodeSnippet]:
        """Search for a symbol across the workspace and return its full code block.

        Uses ``workspace_symbols`` to locate matches, then ``document_symbols``
        on each matching file to obtain the complete range (comments + body).
        """
        matches = self._lsp.request_workspace_symbol(query)
        if not matches:
            return []

        # Group workspace matches by file (relative path)
        by_file: dict[str, list[dict]] = {}
        for m in matches:
            loc = m.get("location", {})
            uri = loc.get("uri", "")
            if not uri.startswith("file://"):
                continue
            abs_path = unquote(uri.replace("file://", ""))
            rel_path = str(PurePath(os.path.relpath(abs_path, self._project_root)))
            by_file.setdefault(rel_path, []).append(m)

        snippets: list[CodeSnippet] = []
        for rel_path, ws_symbols in by_file.items():
            doc_syms, _ = self._lsp.request_document_symbols(rel_path)
            # Index document symbols by name
            doc_by_name: dict[str, dict] = {s["name"]: s for s in doc_syms}

            abs_path = os.path.join(self._project_root, rel_path)
            try:
                lines = Path(abs_path).read_text().splitlines()
            except OSError:
                continue

            for ws in ws_symbols:
                doc = doc_by_name.get(ws["name"])
                if doc is None:
                    continue
                rng = doc["range"]
                start_line = rng["start"]["line"]
                end_line = rng["end"]["line"]
                code = "\n".join(lines[start_line : end_line + 1])
                snippets.append(
                    CodeSnippet(
                        code=code,
                        path=rel_path,
                        start_line=start_line,
                        end_line=end_line,
                    )
                )

        return snippets
