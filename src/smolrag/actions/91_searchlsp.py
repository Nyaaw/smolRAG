from prompt_toolkit import prompt

from smolrag.actions.action import Action
from smolrag.lsp import JavaLSPClient
from smolrag.context_builder import ContextBuilder


class SearchLspAction(Action):
    """Search for symbols via LSP only (exact/camel-case prefix matching)."""

    name = "search-lsp"
    description = "DEBUG: Tests the LSP symbol search"

    def run(self) -> None:
        client = JavaLSPClient(self.project_root)
        with client.start():
            query = prompt("Query: ").strip()

            if not query:
                print("No query provided.")
                return

            snippets = client.workspace_symbols_code(query)

        if not snippets:
            print(f"No results for '{query}'.")
            return

        context_query = (
            "This is the retriever debug mode."
            "Transmit any problems you see with the retrieval tool to the user."
            f"the part being tested is the LSP search, and the search query is: {query}"
        )
        print(ContextBuilder.build(context_query, snippets))

