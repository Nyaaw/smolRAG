# smolRAG

Local retrieval tool for large codebases. Combines Language Server Protocol
analysis (Eclipse JDTLS) with BM25 sparse keyword indexing (Qdrant local mode +
fastembed) to find relevant code snippets and assemble them into a context
block that can be pasted into any LLM. 

Also provides an agentic mode where an
LLM explores the codebase through auto-discovered tools.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (package manager)
- Java 17+ (`JAVA_HOME` set or `java` on `PATH`) — required for the LSP features
- A DeepSeek API key — required only for the agentic mode and e2e tests

## Running the program

```bash
# Install dependencies
uv sync

# Run the CLI against a Java project
uv run smolrag --project /absolute/path/to/project

# Run the CLI against the fixture (demo) Java project
uv run smolrag --project tests/fixtures/java-sample
```

## Index management

The BM25 index is stored at `{cache_root}/qdrant/{target_directory_name}_{hash}/`.

| OS      | Default cache root                               |
|----     |-------------                                     |
| Linux   | `~/.cache/smolrag/`                              |
| macOS   | `~/Library/Caches/smolrag/`                      |
| Windows | `C:\Users\<user>\AppData\Local\smolrag\Cache\`   |

```bash
uv run smolrag --project /path/to/project index
```

Rebuild the index whenever project files change.

## Configuration

Configuration is read from environment variables. Variables not already set
are loaded from a `.env` file in the config directory:

| OS      | Config file                            |
|----     |-------------                           |
| Linux   | `~/.config/smolrag/.env`               |
| macOS   | `~/.config/smolrag/.env`               |
| Windows | `C:\Users\<user>\.config\smolrag\.env` |

***Disclaimer: The program was only tested on Linux***

Create it manually:

```bash
mkdir -p ~/.config/smolrag
echo 'DEEPSEEK_API_KEY=sk-...' > ~/.config/smolrag/.env
```

| Variable                    | Default                    | Description                                                                      |
|----------                   |---------                   |-------------                                                                     |
| `SMOLRAG_CACHE_DIR`         | *(platform default)*       | Override the default cache root for the BM25 index.                              |
| `DEEPSEEK_API_KEY`          | *(none)*                   | DeepSeek API key. Required for agentic mode and e2e tests.                       |
| `DEEPSEEK_MODEL`            | `deepseek-v4-flash`        | Model name used by the agent.                                                    |
| `DEEPSEEK_BASE_URL`         | `https://api.deepseek.com` | API endpoint (OpenAI-compatible).                                                |
| `DEEPSEEK_THINKING`         | `1`                        | Thinking mode toggle. Set to `0` to disable.                                     |
| `DEEPSEEK_REASONING_EFFORT` | `high`                     | Chain-of-thought effort: `high` or `max`. Only applies when thinking is enabled. |

***Disclaimer: The program was only tested with Deepseek***

## Running the tests

```bash
# Fast tests, no Java needed
uv run pytest tests/ -v -m "not lsp"

# All tests except e2e (needs Java 17+)
uv run pytest tests/ -v -m "not e2e"

# e2e tests (calls the DeepSeek API, needs Java 17+ and DEEPSEEK_API_KEY)
# these are not assertions, the tester checks the output manually.
uv run pytest tests/e2e/ -v -s

# All tests (needs Java 17+ and DEEPSEEK_API_KEY)
uv run pytest tests/ -v

```

***Disclaimer: As of July 2026, the e2e test suite with default model settings (deepseek-v4-flash, with thinking set to high) costs around 1 cent.***


## LLM usage

The code in this repository was mainly generated with the assistance of AI
tools. I have reviewed it and take full responsibility for its content,
correctness, and behavior.
