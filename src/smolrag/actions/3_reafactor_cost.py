from smolrag.actions.action import Action
from smolrag.context_builder import ContextBuilder
from smolrag.dedup import dedup
from smolrag.lsp import JavaLSPClient, JavaEnricher
from smolrag.types import CodeSnippet
from smolrag.vector import QdrantRetriever


class RefactorCostAction(Action):
    """Estimate the cost of a refactoring by gathering the target symbol
    (LSP + BM25), all its references, and inheritance context."""

    name = "refactor-cost"

    def run(self) -> None:
        client = JavaLSPClient(self.project_root)
        retriever = QdrantRetriever(self.project_root)
        enricher = JavaEnricher(client, self.project_root)

        with client.start():
            target = input("Refactor target: ").strip()
            #TODO: replace with prompt_toolkit input

            if not target:
                print("No target provided.")
                return

            refactor = input("Refactor action: ").strip()
            #TODO: replace with prompt_toolkit input

            if not refactor:
                print("No refactor action provided.")
                return

            lsp_results = client.find_symbols(target)

            raw = lsp_results + retriever.search(target)
            raw = enricher.enrich_parent(raw)

            ref_snippets = self._find_references(client, lsp_results, target)
            all_snippets = dedup(raw + ref_snippets)

        if not all_snippets:
            print(f"No results for '{target}'.")
            return

        context_query = (
            "Evaluate the refactoring cost of the following refactoring query "
            "Don't write new code yet, only describe the refactoring plan and the impact "
            "on the rest of the codebase. "
            f"Refactor action: {refactor}\nTarget symbol: {target}"
        )
        print(ContextBuilder.build(context_query, all_snippets))

    @staticmethod
    def _find_references(
        client: JavaLSPClient,
        lsp_snippets: list[CodeSnippet],
        target: str,
    ) -> list[CodeSnippet]:
        """Find all references to every code snippet in *lsp_snippets*.

        For each snippet returned by
        :meth:`~smolrag.lsp.JavaLSPClient.find_symbols`, this calls the
        LSP ``textDocument/references`` request (using the snippet's
        start position) and wraps every reference location into a
        :class:`CodeSnippet`.
        """
        all_snippets: list[CodeSnippet] = []

        for s in lsp_snippets:
            # Step 1: ask the LSP for every reference to this symbol
            # across the entire workspace.
            refs = client.references(s.path, s.start_line, 0)

            # Step 2: convert each reference Location into a CodeSnippet,
            # then deduplicate the batch (same-file overlapping references
            # from the same symbol are merged).
            batch: list[CodeSnippet] = []
            for ref in refs:
                ref_uri = ref.get("uri", "")
                ref_abs = client._uri_to_abs_path(ref_uri)
                if ref_abs is None:
                    continue
                ref_rel = client._abs_to_rel_path(ref_abs)

                rng = ref["range"]
                start_line = rng["start"]["line"]
                end_line = rng["end"]["line"]

                code = client._read_code_range(ref_abs, start_line, end_line)
                if code is None:
                    continue

                batch.append(
                    CodeSnippet(
                        code=code,
                        path=ref_rel,
                        start_line=start_line,
                        end_line=end_line,
                        source=f"reference of '{target}'",
                        parent=s,
                        retrieval_depth=s.retrieval_depth + 1,
                    )
                )

            all_snippets.extend(batch)

        # Step 3: deduplicate across symbols (a reference may appear for
        # multiple symbols of the same name in the same file).
        return dedup(all_snippets)
