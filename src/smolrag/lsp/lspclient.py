import json
import logging
import os
import sys
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Any
from urllib.parse import unquote

from lsprotocol.types import SymbolKind
from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig, Language
from multilspy.multilspy_logger import MultilspyLogger

from smolrag.codesnippet import CodeSnippet


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

_lsp_logger = logging.getLogger(__name__)
_lsp_logger.setLevel(
    os.environ.get("SMOLRAG_LOG_LEVEL", "WARNING").upper()
)


class LspClient(ABC):
    """Abstract base for language-specific LSP clients wrapping multilspy.

    Subclasses must define :attr:`_language` and implement all 7 LSP
    request methods.  Four methods return :class:`CodeSnippet` lists
    with source code; ``hover`` and ``completions`` forward the raw
    LSP response.
    """

    @property
    @abstractmethod
    def _language(self) -> Language:
        """The Language enum value for the target language."""
        ...

    @staticmethod
    def _kind_name(kind: int | None) -> str | None:
        if kind is None:
            return None
        try:
            return SymbolKind(kind).name.lower()
        except ValueError:
            return None

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
        self._project_ready = threading.Event()
        self._hook_notification_handler()

    def _hook_notification_handler(self) -> None:
        """Patch the server's ``on_notification`` to intercept ``language/status``.

        When the language server registers its ``language/status``
        notification handler, this wraps it to also detect
        ``ProjectStatus`` and signal that project import/build is
        complete via :attr:`_project_ready`.
        """
        server = self._lsp.language_server.server
        original = server.on_notification

        def patched(method, cb):
            if method == "language/status":
                async def wrapped(params):
                    if params.get("type") == "ProjectStatus":
                        self._project_ready.set()
                    await cb(params)
                original(method, wrapped)
            else:
                original(method, cb)

        server.on_notification = patched

    def _uri_to_abs_path(self, uri: str) -> str | None:
        """Convert a ``file://`` URI to an absolute filesystem path.

        :returns: Absolute path, or ``None`` if *uri* is not a file URI.
        """
        if not uri.startswith("file://"):
            return None
        return unquote(uri.replace("file://", ""))

    def _abs_to_rel_path(self, abs_path: str) -> str:
        """Convert an absolute filesystem path to a project-relative path."""
        return str(Path(abs_path).relative_to(self._project_root))
    
    @staticmethod
    def read_code_range(
        abs_path: str, start_line: int, end_line: int
    ) -> tuple[str, int]:
        """Read *abs_path* and return lines [*start_line*, *end_line*]
        inclusive as a single string, plus the total line count of the
        file.

        :returns: A tuple of (code, total_lines). *code* is empty if
            the file cannot be read or *start_line* is out of range.
        """
        try:
            lines = Path(abs_path).read_text().splitlines()
        except OSError:
            return "", 0
        total_lines = len(lines)
        end_line = min(end_line, total_lines - 1)
        if start_line >= total_lines:
            return "", total_lines
        return "\n".join(lines[start_line : end_line + 1]), total_lines

    @contextmanager
    def start(self) -> Generator["LspClient", None, None]:
        """Context manager that starts the LSP server.

        Waits for the ``ProjectStatus`` notification (up to a timeout)
        so that background Maven/Gradle import jobs finish before the
        first LSP request.

        Usage:
            with client.start():
                snippets = client.document_symbols_code("path/to/File.java")
        """
        self._project_ready.clear()
        print("Initializing Language Server...")
        with self._lsp.start_server():
            if not self._project_ready.wait(timeout=60):
                _lsp_logger.debug(
                    "Timed out waiting for ProjectStatus notification; "
                    "continuing anyway."
                )
            yield self

    @abstractmethod
    def document_symbols_code(self, relative_path: str) -> list[CodeSnippet]:
        """Get all symbols in a file as CodeSnippets with their source code.

        :param relative_path: Path relative to project root
        :returns: CodeSnippets with full source code for each symbol
        """
        ...

    @abstractmethod
    def workspace_symbols_code(self, query: str) -> list[CodeSnippet]:
        """Search for symbols across the workspace and return them as
        CodeSnippets with full source code.

        :param query: Symbol name to search for
        :returns: CodeSnippets with full source code for matching symbols
        """
        ...

    @abstractmethod
    def definition_code(
        self, relative_path: str, line: int, column: int
    ) -> list[CodeSnippet]:
        """Find where the symbol at the given position is defined and
        return the definition as a CodeSnippet with source code.

        :param relative_path: Path relative to project root
        :param line: 0-based line number
        :param column: 0-based column number
        :returns: CodeSnippets with full source code for the definition
        """
        ...

    @abstractmethod
    def references_code(
        self, relative_path: str, line: int, column: int
    ) -> list[CodeSnippet]:
        """Find all references to the symbol at the given position and
        return them as CodeSnippets with source code.

        :param relative_path: Path relative to project root
        :param line: 0-based line number
        :param column: 0-based column number
        :returns: CodeSnippets with full source code for each reference
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
