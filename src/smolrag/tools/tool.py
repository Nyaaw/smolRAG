from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from smolrag.lsp.lspclient import LspClient


class Tool(ABC):
    """Abstract base class for agent tools.

    Subclasses must set ``name``, ``description``, and ``parameters`` (JSON Schema)
    as class attributes, and implement ``execute()``.

    ``execute()`` receives keyword arguments matching the declared parameters
    and must return a plain string (result or error message).
    """

    name: str
    description: str
    parameters: dict

    def __init__(self, project_root: str) -> None:
        self.project_root = project_root

    @abstractmethod
    def execute(self, **kwargs: object) -> str:
        ...


class LspTool(Tool, ABC):
    """Abstract base for tools that need an LSP client.

    Subclasses receive the shared LSP client via constructor injection.
    """

    def __init__(self, project_root: str, lsp_client: LspClient) -> None:
        super().__init__(project_root)
        self._lsp_client = lsp_client
