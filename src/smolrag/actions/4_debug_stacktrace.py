import re

from smolrag.actions.action import Action
from smolrag.lsp import JavaLSPClient
from smolrag.vector import QdrantRetriever
from smolrag.context_builder import ContextBuilder
from smolrag.dedup import dedup

FRAME_RE = re.compile(
    r"^\s+at\s+([\w.$]+)\(([\w.$]+\.java):(\d+)\)"
)

class DebugStacktraceAction(Action):
    """Parse a Java stacktrace, retrieve code for each frame via LSP and BM25,
    and build a context block for debugging."""

    name = "debug-stacktrace"


    def run(self) -> None:
        client = JavaLSPClient(self.project_root)
        retriever = QdrantRetriever(self.project_root)

        with client.start():
            print("Paste the stacktrace (end with an empty line):")
            lines: list[str] = []
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)

            stacktrace = "\n".join(lines)
            if not stacktrace.strip():
                print("No stacktrace provided.")
                return

            frames = self._parse_frames(stacktrace)
            if not frames:
                print("No stack frames found in the input.")
                return

            seen: set[str] = set()
            for f in frames:
                simple = f["class"].split(".")[-1]
                seen.add(simple)

            raw: list = []
            for name in seen:
                raw.extend(client.find_symbols(name))
                raw.extend(retriever.search(name))

            snippets = dedup(raw)

        if not snippets:
            print("No code found for any frame in the stacktrace.")
            return

        context_query = (
            "Debug the following Java stacktrace. "
            "Analyze the retrieved code snippets to identify the root cause "
            "and suggest a fix.\n\n"
            f"```\n{stacktrace}\n```"
        )
        print(ContextBuilder.build(context_query, snippets))

    @staticmethod
    def _parse_frames(stacktrace: str) -> list[dict]:
        """Extract stack frames from a Java stacktrace string."""
        frames: list[dict] = []
        for line in stacktrace.split("\n"):
            m = FRAME_RE.match(line)
            if m:
                frames.append({
                    "class": m.group(1),
                    "file": m.group(2),
                    "line": int(m.group(3)),
                })
        return frames
