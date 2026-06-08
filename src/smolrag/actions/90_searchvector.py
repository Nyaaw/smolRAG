from smolrag.actions.action import Action
from smolrag.vector import QdrantRetriever
from smolrag.context_builder import ContextBuilder


class SearchVectorAction(Action):
    """Search the BM25 index for code snippets matching a query."""

    name = "debug-searchvector"

    def run(self) -> None:
        query = input("Query: ").strip()
        if not query:
            print("No query provided.")
            return

        retriever = QdrantRetriever(self.project_root)
        snippets = retriever.search(query)

        if not snippets:
            print(f"No results for '{query}'.")
            return

        builder = ContextBuilder()
        print(builder.build(query, snippets))
