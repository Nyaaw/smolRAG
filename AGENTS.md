# AGENTS.md

## Project overview

**smolRAG** is a local code retrieval tool for large Java codebases. It combines
Language Server Protocol (Eclipse JDTLS) analysis with keyword indexing (BM25,
planned) to find relevant code snippets and assemble them into a context block
that can be pasted into any LLM.

This is a bachelor's degree final project (Data Engineering, ~450h). The
research question is: *how to work around LLM context window limits when dealing
with very large codebases.*

**Current phase**: a CLI tool where the user picks an action (e.g. "explain a
symbol"), the action calls retrievers (LSP, later Qdrant/BM25), and a
`ContextBuilder` assembles the results into a markdown block for copy/paste.

**What is NOT built yet**: the tooling server for agentic LLMs (phase 2), the BM25
indexer, the Qdrant vector store, any automated tests.

## Project structure

```
smolRAG/
├── src/smolrag/           # Main Python package
│   ├── __init__.py        # Re-exports main(), CodeSnippet, ContextBuilder
│   ├── __main__.py        # python -m smolrag entry point
│   ├── cli.py             # argparse-based CLI: --project, action dispatch
│   ├── types.py           # CodeSnippet dataclass (unified retrieval result)
│   ├── context_builder.py # ContextBuilder: formats CodeSnippets for LLMs
│   ├── actions/           # Action plugins (auto-discovered)
│   │   ├── __init__.py    # Auto-scans for Action subclasses
│   │   ├── action.py      # Abstract Action base class
│   │   └── 1_explain.py   # ExplainAction: find symbol, retrieve code, format
│   ├── lsp/               # LSP integration sub-package
│   │   ├── __init__.py    # Exports LspClient, JavaLSPClient
│   │   ├── lspclient.py   # Abstract LspClient (ABC wrapping multilspy)
│   │   └── javalspclient.py # JavaLSPClient: Eclipse JDTLS, find_symbols()
│   └── vector/            # Vector retrieval sub-package (placeholder)
│       ├── __init__.py
│       └── qdrant_client.py
├── extractor.py           # Reference: manual Java block extraction (unused)
├── pyproject.toml         # uv build config, depends on multilspy>=0.0.15
├── README.md
├── .gitignore
└── .python-version        # Python 3.13
```

## Setup commands

```bash
# Install dependencies (uses uv)
uv sync

# Run the CLI
uv run smolrag --project /absolute/path/to/java/project
```

## Build and test commands

```bash
# Verify the package builds and imports cleanly
uv run python -c "from smolrag import main, CodeSnippet, ContextBuilder"

# Verify actions are discovered
uv run python -c "from smolrag.actions import list_actions; print(list_actions())"

# Run a specific action directly
uv run smolrag --project /path/to/java/project 1-explain
```

There are no unit tests yet.

## Architecture

### Action system

Actions live in `src/smolrag/actions/` as separate files. Each file contains
one class that extends `Action` (from `action.py`) and sets a `name` attribute.
The `actions/__init__.py` auto-discovers them on import — just drop a new
`*.py` file and it's registered. No manual registration needed.

An action's `run()` method orchestrates the pipeline:
1. Collect user input (e.g. symbol name)
2. Call one or more retrievers (LSP, vector, BM25...)
3. Receive `CodeSnippet` objects
4. Pass them to `ContextBuilder.build()` for formatting
5. Print the result

### Retrievers

**LSP (`src/smolrag/lsp/`)**: Wraps `multilspy` (Microsoft's LSP client
library). The `LspClient` ABC handles server lifecycle. `JavaLSPClient`
specializes it for Eclipse JDTLS. The key high-level method is
`find_symbols(query: str) -> list[CodeSnippet]`:

1. `workspace_symbols(query)` — finds matching symbols across the project
2. `document_symbols(rel_path)` — gets full ranges (comments + body) on each
   matching file
3. Reads lines from disk and wraps them into `CodeSnippet` objects

**Vector (`src/smolrag/vector/`)**: Placeholder. Will wrap Qdrant for dense
embedding / BM25 sparse retrieval. Returns `CodeSnippet` objects like LSP does.

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

### ContextBuilder

Formats a `list[CodeSnippet]` into a markdown block intended for copy/paste
into an LLM chat. Headings, ` ```java ` code fences, file location indicators.

## Code style

- Python 3.13+
- Type hints on all function signatures
- No emojis in code or comments
- Standard `dataclasses` for data objects, `abc.ABC` for abstract classes
- Uses `uv` as the package manager and build system (`uv_build` backend)

## Dependencies

- **runtime**: `multilspy>=0.0.15` (LSP client library — handles Eclipse JDTLS download and communication)
- **build**: `uv_build>=0.11.10,<0.12.0`
- **planned**: `qdrant-client` (vector DB), `rank-bm25` (sparse retrieval)

## Key constraints

- Must work against large Java codebases (the project targets Apache Spark
  modules as test subjects)
- Requires Java 17+ and `JAVA_HOME` set for JDTLS to function
- Read-only — never modifies the target Java project
- Actions are **not** agents. They are deterministic scripts that produce
  context blocks for a human to paste into their LLM
