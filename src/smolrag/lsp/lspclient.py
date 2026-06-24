import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path, PurePath
from typing import Generator, Any
from urllib.parse import unquote

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
        _multilspy_logger.setLevel(
            os.environ.get("SMOLRAG_LOG_LEVEL", "WARNING").upper()
        )
        self._lsp = SyncLanguageServer.create(
            config, logger, project_root, timeout=60
        )

    def _uri_to_abs_path(self, uri: str) -> str | None:
        """Convert a ``file://`` URI to an absolute filesystem path.

        :returns: Absolute path, or ``None`` if *uri* is not a file URI.
        """
        if not uri.startswith("file://"):
            return None
        return unquote(uri.replace("file://", ""))

    def _abs_to_rel_path(self, abs_path: str) -> str:
        """Convert an absolute filesystem path to a project-relative path."""
        return str(PurePath(os.path.relpath(abs_path, self._project_root)))

    def _read_code_range(
        self, abs_path: str, start_line: int, end_line: int
    ) -> str | None:
        """Read *abs_path* and return lines [*start_line*, *end_line*]
        inclusive as a single string.

        :returns: The extracted code, or ``None`` if the file cannot be
            read or *start_line* is out of range.
        """
        try:
            lines = Path(abs_path).read_text().splitlines()
        except OSError:
            return None
        end_line = min(end_line, len(lines) - 1)
        if start_line >= len(lines):
            return None
        return "\n".join(lines[start_line : end_line + 1])

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
