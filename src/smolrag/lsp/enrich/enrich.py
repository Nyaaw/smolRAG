from abc import ABC, abstractmethod

from smolrag.lsp.lspclient import LspClient
from smolrag.types import CodeSnippet


class LanguageEnricher(ABC):
    """Abstract base for language-specific enrichment logic.

    Each language implements :meth:`enrich` as a black box —
    no assumptions are made about what enrichment means
    (inheritance, type resolution, interface satisfaction, etc.).
    """

    def __init__(self, lspclient: LspClient, project_root: str) -> None:
        self._lspclient = lspclient
        self._project_root = project_root

    @abstractmethod
    def enrich(self, snippets: list[CodeSnippet]) -> list[CodeSnippet]:
        """Enrich *snippets* with language-specific context."""
        ...
