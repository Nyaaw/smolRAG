import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator, Any

from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig, Language
from multilspy.multilspy_logger import MultilspyLogger


class _CleanHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            data = json.loads(record.getMessage())
            msg = f"{data['time']}  {data['level']:<5}  {data['caller_file']}:{data['caller_line']}  {data['message']}"
        except (json.JSONDecodeError, KeyError):
            msg = record.getMessage()
        sys.stderr.write(msg + "\n")


_multilspy_logger = logging.getLogger("multilspy")
_multilspy_logger.setLevel(
    os.environ.get("SMOLRAG_LOG_LEVEL", "WARNING").upper()
)
if not _multilspy_logger.handlers:
    _multilspy_logger.addHandler(_CleanHandler())


class LspClient(ABC):
    """Abstract base for language-specific LSP clients wrapping multilspy.

    Subclasses must define :attr:`_language` and implement all 7 LSP
    request methods, which can contain per-language response parsing.
    """

    @property
    @abstractmethod
    def _language(self) -> Language:
        """The Language enum value for the target language."""
        ...

    def __init__(self, project_root: str) -> None:
        """
        :param project_root: Absolute path to the root of the project.
        """
        self._project_root = project_root
        config = MultilspyConfig(code_language=self._language)
        logger = MultilspyLogger()
        self._lsp = SyncLanguageServer.create(
            config, logger, project_root, timeout=60
        )

    @contextmanager
    def start(self) -> Generator["LspClient", None, None]:
        """Context manager that starts the LSP server.

        Usage:
            with client.start():
                symbols = client.document_symbols("path/to/File.java")
        """
        with self._lsp.start_server():
            yield self

    @abstractmethod
    def document_symbols(self, relative_path: str) -> Any:
        """Get all symbols (classes, methods, fields) in a file.

        :param relative_path: Path relative to project root
        """
        ...

    @abstractmethod
    def workspace_symbols(self, query: str) -> Any:
        """Search for symbols across the entire workspace.

        :param query: Symbol name to search for
        """
        ...

    @abstractmethod
    def definition(self, relative_path: str, line: int, column: int) -> Any:
        """Find where the symbol at the given position is defined.

        :param relative_path: Path relative to project root
        :param line: 0-based line number
        :param column: 0-based column number
        """
        ...

    @abstractmethod
    def references(self, relative_path: str, line: int, column: int) -> Any:
        """Find all references to the symbol at the given position.

        :param relative_path: Path relative to project root
        :param line: 0-based line number
        :param column: 0-based column number
        """
        ...

    @abstractmethod
    def hover(self, relative_path: str, line: int, column: int) -> Any:
        """Get hover information (type, signature, docs) for the symbol.

        :param relative_path: Path relative to project root
        :param line: 0-based line number
        :param column: 0-based column number
        """
        ...

    @abstractmethod
    def completions(self, relative_path: str, line: int, column: int) -> Any:
        """Get code completions at the given position.

        :param relative_path: Path relative to project root
        :param line: 0-based line number
        :param column: 0-based column number
        """
        ...
