from multilspy.multilspy_config import Language

from smolrag.lsp.lspclient import LspClient


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
