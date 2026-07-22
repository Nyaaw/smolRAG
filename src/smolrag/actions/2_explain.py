from prompt_toolkit import prompt

from smolrag.actions.action import Action
from smolrag.lsp import JavaLSPClient, JavaEnricher
from smolrag.vector import QdrantRetriever
from smolrag.context_builder import ContextBuilder
from smolrag.dedup import dedup


class ExplainHybridAction(Action):
    """Find a symbol via LSP, enrich with inheritance context,
    fill gaps with BM25, and build a context block."""

    name = "explain"
    description = "Gets a symbol (function, class, interface, variable) by its name and explains it"

    def run(self) -> None:
        client = JavaLSPClient(self.project_root)
        retriever = QdrantRetriever(self.project_root)
        enricher = JavaEnricher(client, self.project_root)

        with client.start():
            query = prompt("Symbol name: ").strip()

            if not query:
                print("No query provided.")
                return

            raw = client.workspace_symbols_code(query) + retriever.search(query)
            snippets = dedup(enricher.enrich_parent(dedup(raw)))

        if not snippets:
            print(f"No results for '{query}'.")
            return

        context_query = f"## Explain the following symbol: {query}"
        print(ContextBuilder.build(context_query, snippets))
