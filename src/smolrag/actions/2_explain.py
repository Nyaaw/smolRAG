from smolrag.actions.action import Action
from smolrag.lsp import JavaLSPClient, LspEnricher
from smolrag.vector import QdrantRetriever
from smolrag.context_builder import ContextBuilder
from smolrag.dedup import dedup


class ExplainHybridAction(Action):
    """Find a symbol via LSP, enrich with inheritance context,
    fill gaps with BM25, and build a context block."""

    name = "explain"

    def run(self) -> None:
        client = JavaLSPClient(self.project_root)
        retriever = QdrantRetriever(self.project_root)
        enricher = LspEnricher(client, self.project_root)

        with client.start():
            # FIXME: wait for the server to be fully initialized before proceeding. Or fix multilspy.
            import time
            time.sleep(5)
            symbol = input("Symbol name: ").strip()
            if not symbol:
                print("No symbol provided.")
                return

            lsp_snippets = client.find_symbols(symbol)
            lsp_snippets = enricher.enrich(lsp_snippets)
            bm25_snippets = retriever.search(symbol)

        snippets = dedup(lsp_snippets + bm25_snippets)

        if not snippets:
            print(f"No results for '{symbol}'.")
            return

        builder = ContextBuilder()
        print(builder.build(symbol, snippets))
