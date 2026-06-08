import os
import re
from pathlib import Path

from smolrag.lsp.javalspclient import JavaLSPClient
from smolrag.types import CodeSnippet
from smolrag.dedup import dedup

_EXTENDS_RE = re.compile(r"\bclass\s+\w+.*?\bextends\s+(\w+(?:<[^>]+>)?)")
_IMPLEMENTS_RE = re.compile(r"\bclass\s+\w+.*?\bimplements\s+([\w\s,.<>]+?)\s*(?:\{|extends)")


class LspEnricher:
    """Enrich :class:`CodeSnippet` results with inheritance context
    extracted via LSP."""

    def __init__(self, client: JavaLSPClient, project_root: str) -> None:
        self._client = client
        self._project_root = project_root

    def enrich(self, snippets: list[CodeSnippet]) -> list[CodeSnippet]:
        """Run all enrichment passes and return deduplicated results."""
        result = list(snippets)
        result = self._enrich_inheritance(result)
        return dedup(result)  # remove any overlaps across passes

    def _enrich_inheritance(
        self, snippets: list[CodeSnippet]
    ) -> list[CodeSnippet]:
        """Find and prepend superclass/interface code for each class snippet."""
        enriched: list[CodeSnippet] = []

        for s in snippets:
            parent_names = self._extract_extends_implements(s)
            for name in parent_names:
                parent_snippets = self._client.find_symbols(name)
                if parent_snippets:
                    enriched.extend(parent_snippets)
            enriched.append(s)

        return enriched

    def _extract_extends_implements(self, snippet: CodeSnippet) -> set[str]:
        """Extract superclass and interface names from a class declaration."""
        names: set[str] = set()

        code = snippet.code
        # Check if this looks like a class/interface declaration
        if "class " not in code and "interface " not in code:
            # Try to find the containing class in the same file
            containing = self._find_containing_class(snippet)
            if containing:
                code = containing.code

        for m in _EXTENDS_RE.finditer(code):
            names.add(m.group(1).split("<")[0])

        imp_match = _IMPLEMENTS_RE.search(code)
        if imp_match:
            for part in imp_match.group(1).split(","):
                name = part.strip().split("<")[0]
                if name:
                    names.add(name)

        return names

    def _find_containing_class(
        self, snippet: CodeSnippet
    ) -> CodeSnippet | None:
        """Find the class/interface that contains *snippet* in the same file."""
        abs_path = os.path.join(self._project_root, snippet.path)
        try:
            doc_syms, _ = self._client.document_symbols(snippet.path)
        except Exception:
            return None

        parent = None
        parent_area = float("inf")
        for sym in doc_syms:
            kind = sym.get("kind", 0)
            if kind not in (5, 11):  # Class or Interface
                continue
            rng = sym.get("range", {})
            sym_start = rng.get("start", {}).get("line", 0)
            sym_end = rng.get("end", {}).get("line", 0)
            if (
                sym_start <= snippet.start_line
                and sym_end >= snippet.end_line
            ):
                area = (sym_end - sym_start) * (sym_end - sym_start)
                if area < parent_area:
                    parent_area = area
                    lines = Path(abs_path).read_text().splitlines()
                    code = "\n".join(lines[sym_start : sym_end + 1])
                    parent = CodeSnippet(
                        code=code,
                        path=snippet.path,
                        start_line=sym_start,
                        end_line=sym_end,
                    )

        return parent
