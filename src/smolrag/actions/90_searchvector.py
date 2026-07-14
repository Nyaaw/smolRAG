from prompt_toolkit import prompt

from smolrag.actions.action import Action
from smolrag.vector import QdrantRetriever
from smolrag.context_builder import ContextBuilder


class SearchVectorAction(Action):
    """Search the BM25 index for code snippets matching a query."""

    name = "searchvector"
    description = "DEBUG: Tests the vector search"

    def run(self) -> None:
        query = prompt("Query: ").strip()

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
