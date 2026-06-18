import os
import re
from pathlib import Path

from smolrag.lsp.enrich.enrich import LanguageEnricher
from smolrag.lsp.javalspclient import JavaLSPClient
from smolrag.types import CodeSnippet

# Java-specific regex for class inheritance patterns

# Matches "class Foo extends Bar" or "class Foo extends Bar<Baz>"
_EXTENDS_RE = re.compile(r"\bclass\s+\w+.*?\bextends\s+(\w+(?:<[^>]+>)?)")

# Matches "class Foo implements A, B<C>" stopping at the next { or extends
_IMPLEMENTS_RE = re.compile(r"\bclass\s+\w+.*?\bimplements\s+([\w\s,.<>]+?)\s*(?:\{|extends)")

# LSP symbol kinds for Java class (5) and interface (11)
_CLASS_KINDS = (5, 11)


class JavaEnricher(LanguageEnricher):
    """Enrich Java code snippets with inheritance context via LSP.

    For each class snippet, finds its superclass and interfaces via
    regex on the source code, then retrieves the parent definitions
    through LSP ``workspace/symbol`` + ``document/symbol`` calls.

    Methods and fields that are not themselves class declarations
    are resolved to their containing class first."""

    def enrich(self, snippets: list[CodeSnippet]) -> list[CodeSnippet]:
        """Run inheritance enrichment on *snippets*.

        this method does not deduplicate (it may produce overlapping
        ranges when prepending parent class definitions)."""
        return self._enrich_inheritance(snippets)

    def _enrich_inheritance(
        self, snippets: list[CodeSnippet]
    ) -> list[CodeSnippet]:
        """For each snippet that is a class, prepend the code of its
        superclass and implemented interfaces (recursively, one level)."""
        enriched: list[CodeSnippet] = []

        for s in snippets:
            parent_names = self._extract_extends_implements(s)
            for name in parent_names:
                parent_snippets = self._lspclient.find_symbols(name)
                if parent_snippets:
                    enriched.extend(parent_snippets)
            enriched.append(s)

        return enriched

    def _extract_extends_implements(self, snippet: CodeSnippet) -> set[str]:
        """Parse a snippet's source code for ``extends`` and ``implements``
        clauses, returning the set of parent class/interface names.

        If the snippet is not itself a class/interface declaration
        (e.g. a method), first locates the containing class."""
        names: set[str] = set()

        code = snippet.code
        # If this snippet isn't a class/interface, try to find the enclosing one
        if "class " not in code and "interface " not in code:
            containing = self._find_containing_class(snippet)
            if containing:
                code = containing.code

        # "class Foo extends Bar" or "class Foo extends Bar<Baz>"
        for m in _EXTENDS_RE.finditer(code):
            # Strip generic type parameter (e.g. "Bar<Baz>" -> "Bar")
            names.add(m.group(1).split("<")[0])

        # "class Foo implements A, B<C>"
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
        """Given a snippet (e.g. a method), use LSP ``document/symbol``
        to find the smallest class or interface that contains its line range.

        Returns a CodeSnippet for that class, or None if not found."""
        abs_path = os.path.join(self._project_root, snippet.path)
        try:
            doc_syms, _ = self._lspclient.document_symbols(snippet.path)
        except Exception:
            return None

        parent = None
        parent_area = float("inf")
        for sym in doc_syms:
            kind = sym.get("kind", 0)
            if kind not in _CLASS_KINDS:
                continue
            rng = sym.get("range", {})
            sym_start = rng.get("start", {}).get("line", 0)
            sym_end = rng.get("end", {}).get("line", 0)
            # Check if the snippet falls inside this symbol's range
            if (
                sym_start <= snippet.start_line
                and sym_end >= snippet.end_line
            ):
                # Pick the tightest enclosing class (smallest area)
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
