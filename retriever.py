import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, TOP_K
from ingest import build_chunks

_model: SentenceTransformer | None = None
_collection = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection


def embed_and_store(chunks: list[dict] | None = None) -> int:
    """Embed chunks and store them in ChromaDB. Returns number of chunks stored."""
    if chunks is None:
        chunks = build_chunks()

    collection = get_collection()
    if collection.count() > 0:
        return collection.count()

    model = get_model()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [c["metadata"] for c in chunks]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """Return top-k relevant chunks with distance scores and metadata."""
    collection = get_collection()
    model = get_model()
    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append(
            {
                "text": results["documents"][0][i],
                "source": results["metadatas"][0][i]["source"],
                "chunk_index": results["metadatas"][0][i]["chunk_index"],
                "distance": results["distances"][0][i],
            }
        )
    return chunks


if __name__ == "__main__":
    count = embed_and_store()
    print(f"Stored {count} chunks")
    for result in retrieve("Which dining hall has the shortest lunch wait?"):
        print(f"\n[{result['source']}] distance={result['distance']:.3f}")
        print(result["text"][:200])
