import atexit
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    SparseVector,
    SparseVectorParams,
)
from fastembed import SparseTextEmbedding

from smolrag.types import CodeSnippet
from smolrag.vector.chunker import CodeChunker

COLLECTION_NAME = "smolrag_code"
SPARSE_VECTOR_NAME = "text"
EMBEDDING_MODEL = "Qdrant/bm25"

_clients: dict[str, QdrantClient] = {}


def _close_clients() -> None:
    for client in _clients.values():
        client.close()
    _clients.clear()


atexit.register(_close_clients)


def _get_client(storage_dir: str) -> QdrantClient:
    if storage_dir not in _clients:
        _clients[storage_dir] = QdrantClient(path=storage_dir)
    return _clients[storage_dir]


class QdrantIndexer:
    """Index Java/Scala source files as sparse vectors in a local Qdrant
    collection for BM25 retrieval."""

    def __init__(self, project_root: str) -> None:
        self._project_root = project_root
        storage_dir = str(Path(project_root) / ".smolrag" / "qdrant")
        Path(storage_dir).mkdir(parents=True, exist_ok=True)
        self._client = _get_client(storage_dir)

    def rebuild(self) -> None:
        """Chunk the entire project, delete any existing collection,
        and re-index from scratch."""
        chunker = CodeChunker()
        snippets = chunker.chunk_project(self._project_root)
        if not snippets:
            return

        self._ensure_collection()
        model = SparseTextEmbedding(model_name=EMBEDDING_MODEL)

        batch_size = 100
        for i in range(0, len(snippets), batch_size):
            batch = snippets[i : i + batch_size]
            texts = [s.code for s in batch]
            embeddings = list(model.embed(texts))

            points = [
                PointStruct(
                    id=i + j,
                    vector={
                        SPARSE_VECTOR_NAME: SparseVector(
                            indices=emb.indices.tolist(),
                            values=emb.values.tolist(),
                        )
                    },
                    payload={
                        "code": s.code,
                        "path": s.path,
                        "start_line": s.start_line,
                        "end_line": s.end_line,
                    },
                )
                for j, (s, emb) in enumerate(zip(batch, embeddings))
            ]
            self._client.upsert(collection_name=COLLECTION_NAME, points=points)

    def _ensure_collection(self) -> None:
        """Drop and recreate the sparse-vector collection.

        If a collection named ``COLLECTION_NAME`` already exists, delete
        it (including all indexed points).  Then create a fresh collection
        configured for sparse vectors only — no dense vector storage.
        """
        if self._client.collection_exists(COLLECTION_NAME):
            self._client.delete_collection(COLLECTION_NAME)
        self._client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={},
            sparse_vectors_config={
                SPARSE_VECTOR_NAME: SparseVectorParams(),
            },
        )


class QdrantRetriever:
    """Search indexed code chunks via BM25 sparse retrieval."""

    def __init__(self, project_root: str) -> None:
        storage_dir = str(Path(project_root) / ".smolrag" / "qdrant")
        self._client = _get_client(storage_dir)
        self._model = SparseTextEmbedding(model_name=EMBEDDING_MODEL)

    def search(self, query: str, limit: int = 10) -> list[CodeSnippet]:
        if not self._client.collection_exists(COLLECTION_NAME):
            return []

        embeddings = list(self._model.embed([query]))
        if not embeddings:
            return []

        emb = embeddings[0]
        results = self._client.query_points(
            collection_name=COLLECTION_NAME,
            query=SparseVector(
                indices=emb.indices.tolist(),
                values=emb.values.tolist(),
            ),
            using=SPARSE_VECTOR_NAME,
            limit=limit,
        )

        return [
            CodeSnippet(
                code=p.payload["code"],
                path=p.payload["path"],
                start_line=p.payload["start_line"],
                end_line=p.payload["end_line"],
            )
            for p in results.points
        ]
