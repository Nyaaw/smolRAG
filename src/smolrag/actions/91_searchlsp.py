from smolrag.actions.action import Action
from smolrag.lsp import JavaLSPClient
from smolrag.context_builder import ContextBuilder


class SearchLspAction(Action):
    """Search for symbols via LSP only (exact/camel-case prefix matching)."""

    name = "search-lsp"

    def run(self) -> None:
        client = JavaLSPClient(self.project_root)
        with client.start():
            query = input("Query: ").strip()
            if not query:
                print("No query provided.")
                return

            snippets = client.find_symbols(query)

        if not snippets:
            print(f"No results for '{query}'.")
            return

        builder = ContextBuilder()
        print(builder.build(query, snippets))
