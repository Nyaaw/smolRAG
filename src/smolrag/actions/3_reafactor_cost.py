from prompt_toolkit import prompt

from smolrag.actions.action import Action
from smolrag.context_builder import ContextBuilder
from smolrag.dedup import dedup
from smolrag.lsp import JavaLSPClient, JavaEnricher
from smolrag.codesnippet import CodeSnippet
from smolrag.vector import QdrantRetriever


class RefactorCostAction(Action):
    """Estimate the cost of a refactoring by gathering the target symbol
    (LSP + BM25), all its references, and inheritance context."""

    name = "refactor-cost"
    description = "Estimates the cost of refactoring a symbol. The action can be described in natural langage."

    def run(self) -> None:
        client = JavaLSPClient(self.project_root)
        retriever = QdrantRetriever(self.project_root)
        enricher = JavaEnricher(client, self.project_root)

        with client.start():
            target = prompt("Refactor target: ").strip()

            if not target:
                print("No target provided.")
                return

            refactor = prompt("Refactor action: ").strip()

            if not refactor:
                print("No refactor action provided.")
                return

            lsp_results = client.workspace_symbols_code(target)

            raw = lsp_results + retriever.search(target)
            raw = enricher.enrich_parent(raw)

            ref_snippets: list[CodeSnippet] = []
            for s in lsp_results:
                #HACK: s.start_line, 0 can land on a comment.
                # this seems to work because the LS resolves to nearest identifier
                refs = client.references_code(s.path, s.start_line, 0)

                for ref in refs:
                    ref.source = "reference"
                    ref.parent = s
                    ref.retrieval_depth = s.retrieval_depth + 1

                ref_snippets.extend(refs)

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
