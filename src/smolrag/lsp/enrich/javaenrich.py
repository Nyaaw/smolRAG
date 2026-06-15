import os
import re
from pathlib import Path

from smolrag.lsp.enrich.enrich import LanguageEnricher
from smolrag.lsp.javalspclient import JavaLSPClient
from smolrag.types import CodeSnippet
from smolrag.dedup import dedup

_EXTENDS_RE = re.compile(r"\bclass\s+\w+.*?\bextends\s+(\w+(?:<[^>]+>)?)")
_IMPLEMENTS_RE = re.compile(r"\bclass\s+\w+.*?\bimplements\s+([\w\s,.<>]+?)\s*(?:\{|extends)")


class JavaEnricher(LanguageEnricher):
    """Enrich Java code snippets with inheritance context via LSP."""

    def enrich(self, snippets: list[CodeSnippet]) -> list[CodeSnippet]:
        result = list(snippets)
        result = self._enrich_inheritance(result)
        return dedup(result)

    def _enrich_inheritance(
        self, snippets: list[CodeSnippet]
    ) -> list[CodeSnippet]:
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
        names: set[str] = set()

        code = snippet.code
        if "class " not in code and "interface " not in code:
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
