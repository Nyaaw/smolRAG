# AGENTS.md

## Project overview

**smolRAG** is a local code retrieval tool for large codebases. It combines
Language Server Protocol (Eclipse JDTLS) analysis with BM25 sparse keyword
indexing (Qdrant local mode + fastembed) to find relevant code snippets and
assemble them into a context block that can be pasted into any LLM.

This is a bachelor's degree final project (Data Engineering, ~450h). The
research question is: *how to work around LLM context window limits when dealing
with very large codebases.*

**Current phase**: a CLI tool with auto-discovered actions that call retrievers
(LSP + BM25 vector), enrich results with inheritance context via LSP, and
assemble a deduplicated markdown block for copy/paste.

**What is NOT built yet**: the tooling server for agentic LLMs (phase 2),
dense embeddings.

## Startup

Before working on the codebase, search for all TODO and FIXME markers across
`src/` and `tests/` using a fast search tool (e.g. grep, ripgrep).

## Project structure

```
smolRAG/
├── src/smolrag/              # Main Python package
│   ├── __init__.py           # Re-exports main(), CodeSnippet, ContextBuilder
│   ├── __main__.py           # python -m smolrag entry point
│   ├── cli.py                # argparse-based CLI: --project, action dispatch
│   ├── types.py              # CodeSnippet dataclass (unified retrieval result)
│   ├── context_builder.py    # ContextBuilder: formats CodeSnippets for LLMs
│   ├── dedup.py              # dedup(): merges overlapping CodeSnippet ranges
│   ├── actions/              # Action plugins (auto-discovered by __init__.py)
│   │   ├── __init__.py       # Auto-scans for Action subclasses
│   │   ├── action.py         # Abstract Action base class
│   │   ├── 1_index.py        # IndexAction: chunk project, build Qdrant BM25 index
│   │   ├── 2_explain.py      # ExplainHybridAction: LSP + inheritance enrich + BM25
│   │   ├── 90_searchvector.py # SearchVectorAction: BM25-only search
│   │   └── 91_searchlsp.py   # SearchLspAction: LSP-only search
│   ├── lsp/                  # LSP integration sub-package
│   │   ├── __init__.py       # Exports LspClient, JavaLSPClient, LanguageEnricher, JavaEnricher
│   │   ├── lspclient.py      # Abstract LspClient (ABC wrapping multilspy)
│   │   ├── javalspclient.py  # JavaLSPClient: Eclipse JDTLS, find_symbols()
│   │   └── enrich/           # Language-specific enrichers
│   │       ├── __init__.py   # Exports LanguageEnricher, JavaEnricher
│   │       ├── enrich.py     # LanguageEnricher ABC: single abstract enrich()
│   │       └── javaenrich.py # JavaEnricher: inheritance context via LSP
│   └── vector/               # Vector retrieval sub-package
│       ├── __init__.py       # Exports QdrantIndexer, QdrantRetriever, CodeChunker
│       ├── chunker.py        # CodeChunker: text files → CodeSnippet chunks
│       └── qdrant_client.py  # QdrantIndexer (BM25 embed + store), QdrantRetriever (search)
├── tests/                     # pytest test suite
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures (fixture_project, require_lsp)
│   ├── test_dedup.py            # Tests for dedup() overlap merging (4 failures: known bug)
│   ├── test_types.py            # Tests for CodeSnippet.__str__
│   ├── test_context_builder.py  # Stub
│   ├── e2e/                     # End-to-end tests
│   │   ├── __init__.py
│   │   ├── test_vector.py       # E2E: index + searchvector actions
│   │   └── test_lsp.py          # E2E: search-lsp + explain actions (requires Java)
│   ├── actions/
│   │   └── test_action.py       # Stub
│   ├── lsp/
│   │   └── test_javaenrich.py   # Stub
│   ├── vector/
│   │   └── test_chunker.py      # Stub
│   └── fixtures/
│       └── java-sample/         # Minimal Maven project (inheritance, interfaces, pets)
├── pyproject.toml            # uv build config
├── README.md
├── .gitignore
└── .python-version           # Python 3.13
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

# Run all non-LSP tests (fast, no Java needed)
uv run pytest tests/ -v -m "not lsp"

# Run all tests including LSP (needs Java 17+)
uv run pytest tests/ -v

# Run LSP tests only
uv run pytest tests/ -v -m lsp

# Run E2E tests only
uv run pytest tests/e2e/ -v

# Run a single test by name
uv run pytest tests/e2e/test_vector.py::test_searchvector_finds_results -v

# Run a single test via keyword match
uv run pytest tests/e2e/ -v -k "empty"

# Run a specific action directly
uv run smolrag --project /path/to/project explain
```

## Architecture

### Action system

Actions live in `src/smolrag/actions/` as separate files. Each file contains
one class that extends `Action` (from `action.py`) and sets a `name` attribute.
The `actions/__init__.py` auto-discovers them on import — just drop a new
`*.py` file and it's registered. No manual registration needed.

Available actions:

| Name | File | Description |
|------|------|-------------|
| `index` | `1_index.py` | Walk project, detect text files, chunk, embed BM25 into local Qdrant |
| `explain` | `2_explain.py` | Main action: LSP + inheritance enrich + BM25 fallback + dedup → context block |
| `debug-searchvector` | `90_searchvector.py` | BM25-only search (debug tool) |
| `search-lsp` | `91_searchlsp.py` | LSP-only search (debug tool) |

An action's `run()` method orchestrates the pipeline:
1. Collect user input (e.g. symbol name)
2. Call both retrievers (LSP, vector) to get raw results
3. Deduplicate the raw union (merge overlapping same-file ranges)
4. Enrich with language-specific context (e.g. inheritance via LSP)
5. Deduplicate again (enrichment may introduce new overlaps)
6. Pass to `ContextBuilder.build()` for formatting
7. Print the result

### Retrievers

**LSP (`src/smolrag/lsp/`)**: Wraps `multilspy` (Microsoft's LSP client
library). The `LspClient` ABC handles server lifecycle. `JavaLSPClient`
specializes it for Eclipse JDTLS. The key high-level method is
`find_symbols(query: str) -> list[CodeSnippet]`:

1. `workspace_symbols(query)` — finds matching symbols across the project (camel-case/prefix matching only)
2. `document_symbols(rel_path)` — gets full ranges (comments + body) on each
   matching file
3. Reads lines from disk and wraps them into `CodeSnippet` objects

**Known LSP quirks**:
- `multilspy.start_server()` yields after `ServiceReady` but BEFORE background
  Maven/Gradle import and build jobs finish. There is a 5-second `time.sleep()`
  workaround in `LspClient.start()`. The proper fix would be waiting for
  `language/status` with `ProjectStatus: OK`.
- JDTLS `workspace/symbol` does camel-case prefix matching (e.g. `"OutputRed"`
  finds `OutputRedirector`, but `"redirector"` does not). Use BM25 fallback for
  substring queries.

**Vector (`src/smolrag/vector/`)**: BM25 sparse retrieval via Qdrant local mode
(SQLite-backed, no server needed) + fastembed `Qdrant/bm25` model.

- **Chunker** (`chunker.py`): walks the project via `rglob("*")`, skips 17
  known build/vcs/tool dirs, detects text files via null-byte check (first 8KB),
  skips files >10MB and empty files. Chunks files ≤1000 lines as one snippet,
  splits larger files into 1000-line chunks with 100-line overlap.
- **QdrantIndexer** (`qdrant_client.py`): chunks project, embeds with BM25
  sparse vectors, upserts into local Qdrant collection stored in the OS
  application cache directory: ``{cache_root}/smolrag/qdrant/{basename}_{hash[:8]}/``.
  Uses `platformdirs` to detect the cache root (XDG on Linux,
  ``~/Library/Caches`` on macOS, ``%LOCALAPPDATA%`` on Windows). Overridable
  via ``SMOLRAG_CACHE_DIR`` env var.
- **QdrantRetriever** (`qdrant_client.py`): embeds query, searches collection,
  returns `list[CodeSnippet]`.
- Both share a cached `QdrantClient` instance (single file lock).
- Clients are closed at exit via `atexit` handler to avoid shutdown `ImportError` noise.

### Language enrichers (`src/smolrag/lsp/enrich/`)

The `LanguageEnricher` ABC defines a single abstract method `enrich(snippets) ->
list[CodeSnippet]`. Each language is a black box — no assumptions are made about
what enrichment means (inheritance, type resolution, interface satisfaction,
etc.). The caller is responsible for deduplication before and after.

**JavaEnricher** (`javaenrich.py`) enriches Java `CodeSnippet` results with
inheritance context:

- Extracts `extends`/`implements` from class declarations via regex
- For methods/fields not in a class declaration, finds the containing class via
  range containment in `document_symbols`
- Calls `find_symbols()` on each parent/interface name to retrieve their code
- Prepends parent code before the matched snippet

To add a new language, drop a `*enricher.py` file in `lsp/enrich/` with a class
that extends `LanguageEnricher` and implements `enrich()`.

### CodeSnippet (unified result type)

Defined in `src/smolrag/types.py`. All retrievers return `list[CodeSnippet]`.

```python
@dataclass
class CodeSnippet:
    code: str        # The extracted source code
    path: str        # Relative path to project root
    start_line: int  # 0-based
    end_line: int    # 0-based, inclusive

    def __str__(self) -> str:
        return f"{self.path}@{self.start_line}:{self.end_line}"
```

### Deduplication (`dedup.py`)

`dedup(snippets: list[CodeSnippet]) -> list[CodeSnippet]` merges overlapping
ranges (same file, intersecting line ranges) into a single snippet whose range
is the union and whose code is the concatenation of the non-overlapping parts.
Snippets are grouped by file, sorted by start_line, then merged in a single
O(n log n) pass. Order across files is preserved (first file seen comes first).

### ContextBuilder

Formats a `list[CodeSnippet]` into a markdown block intended for copy/paste
into an LLM chat. Headings, ` ```java ` code fences, file location indicators.

### Logging

The multilspy logger is configured at `lspclient.py` module level:

- `SMOLRAG_LOG_LEVEL` env var controls level (default: `WARNING`)
- A custom `_CleanHandler` parses multilspy's JSON log lines and emits
  `TIME  LEVEL  CALLER:LINE  MESSAGE` format to stderr
- Set `SMOLRAG_LOG_LEVEL=DEBUG` in launch.json for full JDTLS logs

## E2E tests

End-to-end tests live under `tests/e2e/` and drive the action pipeline as a
black box: they instantiate the action, monkeypatch ``builtins.input`` with
a query, and assert on ``capsys`` output.

- **`test_vector.py`** — index + searchvector actions. Always run.
- **`test_lsp.py`** — search-lsp + explain actions. Marked
  ``@pytest.mark.lsp`` and ``@pytest.mark.slow``. Skip automatically when
  Java 17+ is not available.

Shared fixtures in ``tests/conftest.py``:

- ``fixture_project`` — absolute path to ``tests/fixtures/java-sample/``
- ``require_lsp`` — calls ``pytest.skip()`` if ``JAVA_HOME`` is not set or
  ``java -version`` reports < 17

## VSCode launch configurations

``.vscode/launch.json`` provides debug launch configs:

- **smolrag: explain java-sample fixture** — run the explain action on the fixture
- **pytest: all tests** — ``-m "not lsp"`` (fast, no Java)
- **pytest: all tests (including LSP)** — full suite
- **pytest: e2e tests only** — ``tests/e2e/``

## Code style

- Python 3.13+
- Type hints on all function signatures
- No emojis in code or comments
- Standard `dataclasses` for data objects, `abc.ABC` for abstract classes
- Uses `uv` as the package manager and build system (`uv_build` backend)
- RST style comments for each class and functions
- no use of "ASCII art" in comments (example: ------------- title ------------)
- No module-level docstrings or file-header comments; comments go only on
  functions, methods, and classes.
- Test code follows the same style: no docstrings at the top of test files,
  docstrings on test functions only when they add useful information.


## Dependencies

- **runtime**: `multilspy>=0.0.15`, `qdrant-client>=1.9.0`, `fastembed>=0.4.0`, `platformdirs>=4.0.0`
- **build**: `uv_build>=0.11.10,<0.12.0`

## Key constraints

- Must work against large Java codebases (the project targets Apache Spark
  modules as test subjects)
- Requires Java 17+ and `JAVA_HOME` set for JDTLS to function
- Read-only — never modifies the target Java project
- Actions are **not** agents. They are deterministic scripts that produce
  context blocks for a human to paste into their LLM

## Known issues / FIXMEs

- `LspClient.start()` has a `time.sleep(5)` workaround because multilspy
  yields before background build/index jobs finish (see `eclipse_jdtls.py:342`
  TODO). A proper fix would wait for `ProjectStatus: OK` notification.
- JDTLS `workspace/symbol` returns `None` or `[]` when the project has
  Maven/Gradle build errors that prevent full source indexing.
- No dense embedding support yet; BM25 sparse only.
- `_merge_overlapping` in `dedup.py` computes overlap from line ranges, not
  from actual code line counts. When a snippet has fewer code lines than its
  range indicates, inner code can be silently dropped. Realistic test data
  (where code lines match the range) masks this bug.
- 4/9 dedup unit tests fail due to this `_merge_overlapping` bug
  (`overlapping-multiline`, `overlap-single-line`, `overlap-chain`,
  `overlap-mixed`).
