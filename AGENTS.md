# AGENTS.md

## Project overview

**smolRAG** is a local code retrieval tool for large codebases. It combines
Language Server Protocol (Eclipse JDTLS) analysis with BM25 sparse keyword
indexing (Qdrant local mode + fastembed) to find relevant code snippets and
assemble them into a context block that can be pasted into any LLM.

This is a bachelor's degree final project (Data Engineering, ~450h). The
research question is: *how to work around LLM context window limits when dealing
with very large codebases.*

**Current phase**: a CLI tool with two modes:
- **static**: auto-discovered actions that call retrievers (LSP + BM25 vector),
  enrich results with inheritance context via LSP, and assemble a deduplicated
  markdown block for copy/paste into any LLM.
- **agentic**: a conversational agent loop that calls DeepSeek (via OpenAI
  library) with auto-discovered tools. The LLM can invoke tools (e.g. glob)
  to explore the codebase, with proper thinking-mode thread management
  (reasoning_content passthrough during tool-call turns).

**What is NOT built yet**: dense embeddings.

## Startup

Before working on the codebase, search for all TODO and FIXME markers across
`src/` and `tests/` using a fast search tool (e.g. grep, ripgrep).

## Project structure

```
smolRAG/
├── src/smolrag/                 # Main Python package
│   ├── __init__.py              # Re-exports main(), CodeSnippet, ContextBuilder
│   ├── __main__.py              # python -m smolrag entry point
│   ├── cli.py                   # CLI: --project, action dispatch, prompt_toolkit interactive menus
│   ├── agent.py                 # Agentic loop: stdin, DeepSeek + tools, thinking mode passthrough
│   ├── codesnippet.py           # CodeSnippet dataclass (unified retrieval result)
│   ├── config.py                # DeepSeek API config: loads ~/.config/smolrag/.env via python-dotenv
│   ├── context_builder.py       # ContextBuilder: flatten, token-limited format for LLMs
│   ├── dedup.py                 # dedup(): merges overlapping CodeSnippet ranges
│   ├── prompts/                 # Prompt text files loaded at import time
│   │   ├── agent_system.txt     # System prompt for the agentic loop (agent.py)
│   │   └── context_builder_system.txt # System prompt prepended by ContextBuilder
│   ├── tools/                   # Agent tools (auto-discovered by __init__.py)
│   │   ├── __init__.py          # Auto-scans for Tool subclasses
│   │   ├── tool.py              # Abstract Tool and LspTool base classes
│   │   ├── glob.py             # GlobTool: pattern-based file search within project
│   │   ├── read.py             # ReadTool: read file contents with optional line range
│   │   ├── lsp_document_symbols.py  # LspDocumentSymbolsTool: LSP document symbols in a file
│   │   ├── lsp_workspace_symbols.py # LspWorkspaceSymbolsTool: LSP workspace symbol search
│   │   ├── lsp_definition.py    # LspDefinitionTool: LSP go-to-definition (include_code defaults to True)
│   │   ├── lsp_hover.py          # LspHoverTool: LSP hover documentation (500 char limit)
│   │   └── lsp_references.py    # LspReferencesTool: LSP find-all-references
│   ├── actions/                 # Action plugins (auto-discovered by __init__.py)
│   │   ├── __init__.py          # Auto-scans for Action subclasses
│   │   ├── action.py            # Abstract Action base class
│   │   ├── 1_index.py           # IndexAction: chunk project, build Qdrant BM25 index
│   │   ├── 2_explain.py         # ExplainHybridAction: LSP + inheritance enrich + BM25
│   │   ├── 3_reafactor_cost.py  # RefactorCostAction: LSP + references + enrich + BM25
│   │   ├── 4_debug_stacktrace.py # DebugStacktraceAction: parse stacktrace, retrieve per unique class name
│   │   ├── 90_searchvector.py   # SearchVectorAction: BM25-only search
│   │   └── 91_searchlsp.py      # SearchLspAction: LSP-only search
│   ├── lsp/                     # LSP integration sub-package
│   │   ├── __init__.py          # Exports LspClient, JavaLSPClient, LanguageEnricher, JavaEnricher
│   │   ├── lspclient.py         # Abstract LspClient (ABC wrapping multilspy)
│   │   ├── javalspclient.py     # JavaLSPClient: 4 CodeSnippet-returning LSP methods + hover/completions
│   │   └── enrich/              # Language-specific enrichers
│   │       ├── __init__.py      # Exports LanguageEnricher, JavaEnricher
│   │       ├── enrich.py        # LanguageEnricher ABC: single abstract enrich_parent()
│   │       └── javaenrich.py    # JavaEnricher: inheritance context via LSP
│   └── vector/                  # Vector retrieval sub-package
│       ├── __init__.py          # Exports QdrantIndexer, QdrantRetriever, CodeChunker
│       ├── chunker.py           # CodeChunker: text files → CodeSnippet chunks
│       └── qdrant_client.py     # QdrantIndexer (BM25 embed + store), QdrantRetriever (search)
├── tests/                       # pytest test suite
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures (fixture_project, require_lsp)
│   ├── helpers.py               # Shared test helpers (_cs, _code, patch_prompt)
│   ├── test_dedup.py
│   ├── test_flatten.py
│   ├── test_codesnippet.py      # __str__, to_action_output, to_tool_output, with_line_numbers
│   ├── test_context_builder.py  # Formatting + token-limit cut
│   ├── e2e/
│   │   ├── test_static_e2e.py   # One test per action, calls DeepSeek API (costs money)
│   │   └── test_agent_e2e.py    # Two-turn agent session covering all 7 tools (costs money)
│   ├── integration/
│   │   ├── test_vector.py       # index + searchvector actions
│   │   ├── test_lsp.py          # search-lsp + explain actions (requires Java)
│   │   ├── test_javaenrich.py   # JavaEnricher against real JDTLS (requires Java)
│   │   └── test_javalspclient.py # definition_code / references_code, no-duplicates check (requires Java)
│   ├── tools/
│   │   ├── test_glob.py         # GlobTool patterns + path traversal guards
│   │   ├── test_read.py         # ReadTool ranges, errors, path traversal guards
│   │   └── test_registry.py     # list_tools() discovery + schema validity
│   ├── lsp/
│   │   └── test_lspclient.py    # read_code_range, _kind_name, URI/path helpers
│   ├── vector/
│   │   └── test_chunker.py      # Chunk splitting, overlap windows, skip dirs
│   └── fixtures/
│       └── java-sample/         # Minimal Maven project (inheritance, interfaces, pets)
├── pyproject.toml
├── README.md
├── .gitignore
└── .python-version              # Python 3.13
```

## Setup commands

```bash
# Install dependencies (uses uv)
uv sync

# Run the CLI
uv run smolrag --project /absolute/path/to/project
```

## Build and test commands

```bash
# Verify the package builds and imports cleanly
uv run python -c "from smolrag import main, CodeSnippet, ContextBuilder"

# Verify actions are discovered
uv run python -c "from smolrag.actions import list_actions; print(list_actions())"

# Verify tools are discovered
uv run python -c "from smolrag.tools import list_tools; print(list_tools())"

# Run all non-LSP tests (fast, no Java needed)
uv run pytest tests/ -v -m "not lsp"

# Run all tests including LSP (needs Java 17+)
uv run pytest tests/ -v

# Run LSP tests only
uv run pytest tests/ -v -m lsp

# Run e2e tests (calls DeepSeek API, costs money, needs DEEPSEEK_API_KEY)
uv run pytest tests/e2e/ -v -s

# Run all tests except e2e (no cost)
uv run pytest tests/ -v -m "not e2e"

# Run integration tests only
uv run pytest tests/integration/ -v

# Run a specific action directly
uv run smolrag --project /path/to/project explain
```

## Architecture

### Action system

Actions live in `src/smolrag/actions/` as separate files. Each file contains
one class that extends `Action` (from `action.py`) and sets a `name` attribute.
The `actions/__init__.py` auto-discovers them on import — drop a new `*.py` file
and it's registered.

Filenames use a numeric prefix that controls the order in interactive menus.
Actions with a prefix >= 50 are considered debug-only.

Available actions:

| Name | File | Pipeline |
|------|------|----------|
| `index` | `1_index.py` | Walk project, chunk, embed BM25 into local Qdrant |
| `explain` | `2_explain.py` | LSP + BM25 → dedup → enrich → dedup → context |
| `refactor-cost` | `3_reafactor_cost.py` | LSP + BM25 → enrich → references via ``references_code`` → dedup → context |
| `debug-stacktrace` | `4_debug_stacktrace.py` | Parse stacktrace → LSP + BM25 per unique class name → dedup → context |
| `searchvector` | `90_searchvector.py` | BM25-only search (debug) |
| `search-lsp` | `91_searchlsp.py` | LSP-only search (debug) |

All actions end with building a contextual query and passing it to
``ContextBuilder.build()`` for formatting.

### Retrievers

**LSP (`src/smolrag/lsp/`)**: Wraps `multilspy` (Microsoft's LSP client
library). The `LspClient` ABC handles server lifecycle and provides shared
file-I/O helpers and utility methods:

- ``_uri_to_abs_path(uri) -> str | None`` — converts a ``file://`` URI to an
  absolute filesystem path.
- ``_abs_to_rel_path(abs_path) -> str`` — converts an absolute path to a
  project-relative path.
- ``read_code_range(abs_path, start_line, end_line) -> tuple[str, int, int]`` — static method;
  reads lines [*start_line*, *end_line*] inclusive from disk and returns
  (code, end_line, total_lines). The returned *end_line* is clamped to the
  last line of the file, so a snippet built from it always satisfies
  ``len(code.splitlines()) == end_line - start_line + 1``, even when the LSP
  server reports a range past EOF. All callers must store the returned
  *end_line*, not the raw LSP value.
- ``_kind_name(kind) -> str | None`` — static method; maps an LSP SymbolKind
  integer to a lowercase name via ``lsprotocol.types.SymbolKind`` (e.g.
  ``5`` → ``"class"``). Returns ``None`` for unknown or ``None`` inputs.

``start()`` is a context manager that launches the LSP server and waits for a
``language/status`` ``ProjectStatus`` notification (up to 60 s timeout) before
yielding, so background Maven/Gradle import jobs finish.

`JavaLSPClient` specializes ``LspClient`` for Eclipse JDTLS. It also inherits
``LspClient._kind_name()``, a static method that maps LSP SymbolKind integers
to lowercase names (e.g. ``5`` → ``"class"``) via ``lsprotocol.types.SymbolKind``.
Four methods return ``list[CodeSnippet]`` with source code; ``hover`` and
``completions`` forward the raw LSP response:

- ``document_symbols_code(rel_path)`` — all symbols in a file. Populates
  ``symbol_name`` and ``symbol_kind`` on each snippet.
- ``workspace_symbols_code(query)`` — search workspaces for symbols matching
  *query*, uses ``document_symbols_code`` internally to get full ranges via
  location containment. Carries over ``symbol_name``/``symbol_kind`` from
  the workspace symbol result.
- ``definition_code(rel_path, line, col)`` — definition of the symbol at the
  given position
- ``references_code(rel_path, line, col)`` — all references to the symbol at
  the given position

``workspace_symbols_code``, ``definition_code``, and ``references_code``
deduplicate their results via deep equality (``snippet not in snippets``,
dataclass ``__eq__``), not ``id()``. This also covers fallback snippets built
from raw LSP ranges, e.g. two references on the same line
(``Cat cat = (Cat) pet;``) collapse into one snippet.

**Known LSP quirks**:
- JDTLS `workspace/symbol` does camel-case prefix matching (e.g. `"OutputRed"`
  finds `OutputRedirector`, but `"redirector"` does not). Use BM25 fallback for
  substring queries.

**Vector (`src/smolrag/vector/`)**: BM25 sparse retrieval via Qdrant local mode
(SQLite-backed, no server needed) + fastembed `Qdrant/bm25` model.

- **Chunker** (`chunker.py`): walks the project via `rglob("*")`, skips 16
  known build/vcs/tool dirs, detects text files via null-byte check (first 8KB),
  skips files >10MB and empty files. Chunks files ≤1000 lines as one snippet,
  splits larger files into 1000-line chunks with 100-line overlap.
- **QdrantIndexer** (`qdrant_client.py`): chunks project, embeds with BM25
  sparse vectors, stores in local Qdrant collection at
  ``{cache_root}/qdrant/{basename}_{hash[:8]}/`` where ``cache_root`` is
  ``SMOLRAG_CACHE_DIR`` if set, else ``platformdirs.user_cache_dir("smolrag")``.
- **QdrantRetriever** (`qdrant_client.py`): embeds query, searches collection,
  returns `list[CodeSnippet]`.
- Shared ``QdrantClient`` instance, closed at exit via ``atexit``.

### Language enrichers (`src/smolrag/lsp/enrich/`)

The `LanguageEnricher` ABC defines a single abstract method
`enrich_parent(snippets) -> list[CodeSnippet]`. Each language is a black box —
the caller is responsible for deduplication before and after.

**JavaEnricher** (`javaenrich.py`) enriches Java results with inheritance
context via its ``enrich_parent`` method:

- Extracts `extends`/`implements` from class declarations via regex.
- For non-class snippets, finds the containing class via
  ``document_symbols_code`` range containment.
- Calls ``workspace_symbols_code()`` on each parent/interface name to retrieve
  their code, prepending it before the matched snippet.

To add a new language, drop a `*enricher.py` file in `lsp/enrich/` with a class
that extends `LanguageEnricher` and implements `enrich_parent()`.

### CodeSnippet (unified result type)

Defined in `src/smolrag/codesnippet.py`. All retrievers return `list[CodeSnippet]`.

```python
@dataclass
class CodeSnippet:
    code: str        # The extracted source code
    path: str        # Relative path to project root
    start_line: int  # 0-based
    end_line: int    # 0-based, inclusive
    total_lines: int # Total lines in the source file
    source: str      # Describes where/how this snippet was retrieved
    parent: CodeSnippet | None = None  # Enrichment/reference origin (None for top-level)
    retrieval_depth: int = 0  # Distance from a direct retrieval root
    symbol_name: str | None = None  # LSP symbol name (e.g. "getBarkVolume")
    symbol_kind: str | None = None  # LSP symbol kind (e.g. "method", "class")

    def __str__(self) -> str:
        return f"{self.path}@{self.start_line}:{self.end_line}"

    def to_action_output(self) -> str:
        ...

    def to_tool_output(self, include_code: bool = False) -> str:
        ...

    @staticmethod
    def with_line_numbers(code: str, start_line: int) -> str:
        ...
```

``__str__`` is used by ``ContextBuilder`` for snippet headings. ``to_action_output()``
is used by actions to produce heading lines with file path, total lines, line range,
source, and optional parent. ``to_tool_output()`` is a compact representation for
LLM tool responses: a single header line (``path (N lines)@start:end`` followed by
optional ``symbol_kind`` and ``symbol_name``) with optional code appended below
when ``include_code=True``. Default is ``False`` to keep responses small.

``with_line_numbers(code, start_line)`` is a static utility that prepends each
line of *code* with its absolute 0-based line number in the source file,
starting at *start_line*. Used by ``ReadTool`` and ``to_tool_output()`` to
produce line-numbered output. All line and column numbers across the project
are 0-based, matching LSP conventions.

Source strings:

- **LSP**: ``"LSP workspace search '{query}'"``, ``"LSP document symbol"``,
  ``"LSP definition"``, ``"LSP reference"``
- **BM25 / vector**: ``"BM25 search '{query}'"``
- **Chunker**: ``"file chunk"``
- **JavaEnricher**: ``"superclass or interface"``, ``"containing class"``
- **RefactorCostAction**: ``"reference"``

The ``parent`` field forms a rootless tree. Top-level snippets have
``parent = None``. ``retrieval_depth`` starts at 0 for roots, +1 per enrichment
level, and is carried forward during dedup merges.

### Deduplication (`dedup.py`)

`dedup(snippets: list[CodeSnippet]) -> list[CodeSnippet]` merges overlapping
ranges (same file, intersecting line ranges) into a single snippet. Merged
snippets inherit ``source``, ``parent``, ``symbol_name``, and ``symbol_kind``
from the first (highest-order) snippet in the group. ``_fixup_parents()``
redirects parent references that pointed to a merged-away original to the
final merged object.

### ContextBuilder (`context_builder.py`)

Formats a `list[CodeSnippet]` into a markdown block for copy/paste into an LLM.
Tools use ``ContextBuilder.build(query, snippets)`` without instantiation.

Internally, ``_flatten()`` reorders snippets into depth-first order using
``parent`` references, so enrichment children immediately follow their parent.
``build()`` then applies a token limit (80 000 tokens, 3 chars = 1 token),
dropping deepest snippets first based on ``retrieval_depth``. Output: system
prompt, query heading, snippet headings (``snippet.to_action_output()``), and
`` ```java `` code fences.

### Logging

The multilspy logger is configured at `lspclient.py` module level:

- `SMOLRAG_LOG_LEVEL` env var controls level (default: `WARNING`)
- A custom `_CleanHandler` parses multilspy's JSON log lines and emits
  `TIME  LEVEL  CALLER:LINE  MESSAGE` format to stderr

### Agent workflow

``agent.py`` implements a conversational loop that calls DeepSeek through
the OpenAI library:

1. Creates a ``JavaLSPClient`` and enters ``client.start()`` (context manager),
   launching Eclipse JDTLS once for the session lifetime.
2. All registered ``Tool`` subclasses are instantiated. ``LspTool`` subclasses
   receive the shared LSP client via constructor injection; plain ``Tool``
   subclasses receive only ``project_root``.
3. Reads a user query from ``stdin``, sends it to DeepSeek with tool definitions.
4. Dispatches ``tool_calls`` to matching tools, returns results back to the
   model, repeats until no more tool calls.
5. Prints the model's final ``content`` and waits for the next query.
6. On exit (Ctrl+C/D or EOF), the ``with`` block closes and JDTLS shuts down.

### Tool system

Tools live in `src/smolrag/tools/`, auto-discovered on import (same pattern
as actions). Each `Tool` subclass defines ``name``, ``description``,
``parameters`` (JSON Schema draft-7), and ``execute(**kwargs) -> str``.

There are two base classes in ``tool.py``:

- **``Tool``** — plain tools. Constructor receives ``project_root``.
- **``LspTool(Tool)``** — tools that need an LSP client. Constructor
  receives ``project_root`` and ``lsp_client``. The agent creates a single
  ``JavaLSPClient`` at startup and injects it into every ``LspTool`` subclass.

Available tools:

| Name | File | Description |
|------|------|-------------|
| `glob` | `glob.py` | Pattern-based file search confined to the project directory (path traversal is prevented) |
| `read` | `read.py` | Read file contents with optional start/end line range (0-based, inclusive). Uses ``CodeSnippet.with_line_numbers`` for absolute 0-based line numbering. Path traversal is prevented. |
| `lsp-document_symbols` | `lsp_document_symbols.py` | LSP document symbols in a file (optional inline code via ``include_code``) |
| `lsp-workspace_symbols` | `lsp_workspace_symbols.py` | LSP workspace symbol search (optional inline code via ``include_code``) |
| `lsp-definition` | `lsp_definition.py` | LSP go-to-definition (``include_code`` defaults to ``True``) |
| `lsp-hover` | `lsp_hover.py` | LSP hover documentation and type info (truncated to 500 characters) |
| `lsp-references` | `lsp_references.py` | LSP find-all-references (optional inline code via ``include_code``) |

A tool must define three class attributes and one method:

``name`` --- unique identifier, used in the OpenAI function call schema
``description`` --- natural language description for the LLM to know when to call it
``parameters`` --- a JSON Schema (draft-7) ``object`` describing the tool's arguments
``execute(**kwargs) -> str`` --- executes the tool and returns a plain string (result or error message)

Tools receive ``project_root`` in their constructor (same pattern as
``Action``). ``LspTool`` subclasses additionally receive ``lsp_client``.
Errors are caught by the agent loop and returned as error
strings so the LLM can react to them.

The JSON schema for ``parameters`` must follow the OpenAI function-calling
format. The top-level ``type`` must be ``"object"``, with ``properties``
describing each argument and an optional ``required`` array:

```python
parameters = {
    "type": "object",
    "properties": {
        "pattern": {"type": "string", "description": "Glob pattern to match"},
    },
    "required": ["pattern"],
}
```

**Thinking mode passthrough** (``DEEPSEEK_THINKING=1``): ``reasoning_content``
must be passed back through ``response.choices[0].message`` during multi-turn
tool-call exchanges. The agent prints a truncated reasoning trace before the
final answer.

## DeepSeek API configuration

The ``src/smolrag/config.py`` module loads ``~/.config/smolrag/.env`` via
``python-dotenv`` (if the file exists). Already-set environment variables
take priority.

Exposed constants:

- ``DEEPSEEK_API_KEY`` — API key
- ``DEEPSEEK_MODEL`` — model name (default: ``deepseek-v4-flash``)
- ``DEEPSEEK_BASE_URL`` — API endpoint (default: ``https://api.deepseek.com``)
- ``DEEPSEEK_THINKING`` — thinking mode toggle (default: ``True``,
  set ``DEEPSEEK_THINKING=0`` to disable)
- ``DEEPSEEK_REASONING_EFFORT`` — chain-of-thought effort: ``"high"`` or
  ``"max"`` (default: ``"high"``, only applies when thinking is enabled)

Create ``~/.config/smolrag/.env`` manually:

```bash
mkdir -p ~/.config/smolrag
echo 'DEEPSEEK_API_KEY=sk-...' > ~/.config/smolrag/.env
# optional: DEEPSEEK_THINKING=0, DEEPSEEK_REASONING_EFFORT=max
```

## E2E tests

``tests/e2e/test_static_e2e.py`` runs each action against the fixture project,
sends the context block to DeepSeek, and prints the response.
``tests/e2e/test_agent_e2e.py`` runs a two-turn agent session exercising all 7
tools. Tests are marked ``@pytest.mark.e2e`` and skip when
``DEEPSEEK_API_KEY`` is not set. No assertions — human-validated.

## integration tests

``tests/integration/`` drives the action pipeline as a black box, patching
``prompt`` via ``tests.helpers.patch_prompt`` and asserting on ``capsys`` output.

- **`test_vector.py`** — index + searchvector. Always run.
- **`test_lsp.py`** — search-lsp + explain. Marked ``@pytest.mark.lsp``,
  ``@pytest.mark.slow``. Skips when Java 17+ is not available.
- **`test_javaenrich.py`** — JavaEnricher against real JDTLS. Marked
  ``@pytest.mark.lsp``, ``@pytest.mark.slow``.
- **`test_javalspclient.py`** — definition_code / references_code against
  JDTLS, including a no-duplicates check on references_code. Marked
  ``@pytest.mark.lsp``, ``@pytest.mark.slow``.

Shared fixtures in ``tests/conftest.py``:

- ``fixture_project`` — absolute path to ``tests/fixtures/java-sample/``
- ``require_lsp`` — skips if Java 17+ is not available

### Java sample fixture

``tests/fixtures/java-sample/`` is a minimal Maven project modelling a
veterinary domain. ``Main.java`` contains an intentional NPE on line 31 for
testing ``debug-stacktrace``. Compile and run with:

```bash
./mvnw compile && java -cp target/classes com.example.Main
```

## Code style

- Python 3.13+
- Type hints on all function signatures
- No emojis in code or comments
- Standard `dataclasses` for data objects, `abc.ABC` for abstract classes
- Uses `uv` as the package manager and build system (`uv_build` backend)
- RST style comments for each class and function
- No module-level docstrings or file-header comments
- Test code follows the same style

## Dependencies

- **runtime**: `multilspy>=0.0.15`, `qdrant-client>=1.9.0`, `fastembed>=0.4.0`, `platformdirs>=4.0.0`, `openai>=2.44.0`, `prompt-toolkit>=3.0.52`, `python-dotenv>=1.0.0`
- **build**: `uv_build>=0.11.10,<0.12.0`

## Key constraints

- Must work against large Java codebases (targets Apache Spark modules)
- Requires Java 17+ (``JAVA_HOME`` or ``java`` on ``PATH``) for JDTLS
- Read-only — never modifies the target Java project
- Actions are **not** agents. They are deterministic scripts that produce
  context blocks for a human to paste into their LLM

## Known issues / FIXMEs

- JDTLS `workspace/symbol` returns ``None`` or ``[]`` when the project has
  Maven/Gradle build errors that prevent full source indexing.
- No dense embedding support yet; BM25 sparse only.
- `_merge_overlapping` in `dedup.py` assumes a snippet's code line count
  matches its declared line range (``end_line - start_line + 1``). Snippets
  violating this invariant may have inner code silently dropped during merges.
  The invariant is enforced at the LSP boundary: ``read_code_range`` returns
  the effective (clamped) end line and all callers store it. The chunker and
  vector retriever produce consistent snippets by construction.
- LSP ``Range.end`` is character-exclusive; when ``end.character == 0`` the
  snippet may include one extra trailing line. Accepted as harmless.