from smolrag.actions.action import Action
from smolrag.vector import QdrantIndexer
from smolrag.vector.qdrant_client import _close_clients


class IndexAction(Action):
    """Index a project into a local Qdrant collection for BM25 retrieval."""

    name = "index"

    def run(self) -> None:
        indexer = QdrantIndexer(self.project_root)
        indexer.rebuild()
        _close_clients()
        print("Index built.")
