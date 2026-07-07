from smolrag.actions.action import Action
from smolrag.vector import QdrantRetriever
from smolrag.context_builder import ContextBuilder


class SearchVectorAction(Action):
    """Search the BM25 index for code snippets matching a query."""

    name = "debug-searchvector"
    #TODO: add description for printing in choice menus

    def run(self) -> None:
        query = input("Query: ").strip()
        #TODO: replace with prompt_toolkit input

        if not query:
            print("No query provided.")
            return

        retriever = QdrantRetriever(self.project_root)
        snippets = retriever.search(query)

        if not snippets:
            print(f"No results for '{query}'.")
            return

        context_query = (
            "This is the retriever debug mode."
            "Transmit any problems you see with the retrieval tool to the user."
            f"the part being tested is the vector search, and the search query is: {query}"
        )
        print(ContextBuilder.build(context_query, snippets))
