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
(LSP + BM25 vector), deduplicate results, and assemble a markdown block for
copy/paste.

**What is NOT built yet**: dense embeddings, LSP-based context enrichment
(inheritance, dependencies), the tooling server for agentic LLMs (phase 2),
automated tests.

## Project structure

```
smolRAG/
├── src/smolrag/              # Main Python package
│   ├── __init__.py           # Re-exports main(), CodeSnippet, ContextBuilder
│   ├── __main__.py           # python -m smolrag entry point
│   ├── cli.py                # argparse-based CLI: --project, action dispatch
│   ├── types.py              # CodeSnippet dataclass (unified retrieval result)
│   ├── context_builder.py    # ContextBuilder: formats CodeSnippets for LLMs
│   ├── dedup.py              # dedup(): removes overlapping CodeSnippet ranges
│   ├── actions/              # Action plugins (auto-discovered by __init__.py)
│   │   ├── __init__.py       # Auto-scans for Action subclasses
│   │   ├── action.py         # Abstract Action base class
│   │   ├── 1_index.py        # IndexAction: chunk project, build Qdrant BM25 index
│   │   ├── 2_explain.py      # ExplainHybridAction: LSP + BM25 + dedup
│   │   ├── 90_searchvector.py # SearchVectorAction: BM25-only search
│   │   └── 91_searchlsp.py   # SearchLspAction: LSP-only search
│   ├── lsp/                  # LSP integration sub-package
│   │   ├── __init__.py       # Exports LspClient, JavaLSPClient
│   │   ├── lspclient.py      # Abstract LspClient (ABC wrapping multilspy)
│   │   └── javalspclient.py  # JavaLSPClient: Eclipse JDTLS, find_symbols()
│   └── vector/               # Vector retrieval sub-package
│       ├── __init__.py       # Exports QdrantIndexer, QdrantRetriever, CodeChunker
│       ├── chunker.py        # CodeChunker: text files → CodeSnippet chunks
│       └── qdrant_client.py  # QdrantIndexer (BM25 embed + store), QdrantRetriever (search)
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

# Run a specific action directly
uv run smolrag --project /path/to/project explain
```

There are no unit tests yet.

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
| `explain` | `2_explain.py` | Main action: LSP search + BM25 fallback + dedup → context block |
| `debug-searchvector` | `90_searchvector.py` | BM25-only search (debug tool) |
| `search-lsp` | `91_searchlsp.py` | LSP-only search (debug tool) |

An action's `run()` method orchestrates the pipeline:
1. Collect user input (e.g. symbol name)
2. Call one or more retrievers (LSP, vector)
3. Deduplicate overlapping results
4. Pass to `ContextBuilder.build()` for formatting
5. Print the result

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
  workaround in the `explain` action. The proper fix would be waiting for
  `language/status` with `ProjectStatus: OK`.
- JDTLS `workspace/symbol` does camel-case prefix matching (e.g. `"OutputRed"`
  finds `OutputRedirector`, but `"redirector"` does not). Use BM25 fallback for
  substring queries.

**Vector (`src/smolrag/vector/`)**: BM25 sparse retrieval via Qdrant local mode
(SQLite-backed, no server needed) + fastembed `Qdrant/bm25` model.

- **Chunker** (`chunker.py`): walks the project via `rglob("*")`, skips 18
  known build/vcs/tool dirs, detects text files via null-byte check (first 8KB),
  skips files >10MB and empty files. Chunks files ≤1000 lines as one snippet,
  splits larger files into 1000-line chunks with 100-line overlap.
- **QdrantIndexer** (`qdrant_client.py`): chunks project, embeds with BM25
  sparse vectors, upserts into local Qdrant collection stored at
  `{project_root}/.smolrag/qdrant/`.
- **QdrantRetriever** (`qdrant_client.py`): embeds query, searches collection,
  returns `list[CodeSnippet]`.
- Both share a cached `QdrantClient` instance (single file lock).
- Clients are closed at exit via `atexit` handler to avoid shutdown `ImportError` noise.

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

`dedup(snippets: list[CodeSnippet]) -> list[CodeSnippet]` removes overlapping
ranges (same file, intersecting line ranges). First occurrence wins — place
higher-quality results (LSP) before lower-priority results (BM25).

### ContextBuilder

Formats a `list[CodeSnippet]` into a markdown block intended for copy/paste
into an LLM chat. Headings, ` ```java ` code fences, file location indicators.

### Logging

The multilspy logger is configured at `lspclient.py` module level:

- `SMOLRAG_LOG_LEVEL` env var controls level (default: `WARNING`)
- A custom `_CleanHandler` parses multilspy's JSON log lines and emits
  `TIME  LEVEL  CALLER:LINE  MESSAGE` format to stderr
- Set `SMOLRAG_LOG_LEVEL=DEBUG` in launch.json for full JDTLS logs

## Code style

- Python 3.13+
- Type hints on all function signatures
- No emojis in code or comments
- Standard `dataclasses` for data objects, `abc.ABC` for abstract classes
- Uses `uv` as the package manager and build system (`uv_build` backend)

## Dependencies

- **runtime**: `multilspy>=0.0.15`, `qdrant-client>=1.9.0`, `fastembed>=0.4.0`
- **build**: `uv_build>=0.11.10,<0.12.0`

## Key constraints

- Must work against large Java codebases (the project targets Apache Spark
  modules as test subjects)
- Requires Java 17+ and `JAVA_HOME` set for JDTLS to function
- Read-only — never modifies the target Java project
- Actions are **not** agents. They are deterministic scripts that produce
  context blocks for a human to paste into their LLM

## Known issues / FIXMEs

- The `explain` action has a `time.sleep(5)` workaround because multilspy
  yields before background build/index jobs finish (see `eclipse_jdtls.py:342`
  TODO). A proper fix would wait for `ProjectStatus: OK` notification.
- JDTLS `workspace/symbol` returns `None` or `[]` when the project has
  Maven/Gradle build errors that prevent full source indexing.
- `dedup()` is O(n²) — fine for small result sets but not for large ones.
- No dense embedding support yet; BM25 sparse only.
- No LSP-based context enrichment (inheritance, dependencies) yet.
