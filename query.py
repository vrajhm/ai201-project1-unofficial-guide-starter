from generator import generate_response
from retriever import embed_and_store, retrieve


def ask(question: str) -> dict:
    """End-to-end RAG: retrieve chunks, generate grounded answer, return sources."""
    embed_and_store()
    chunks = retrieve(question)
    answer = generate_response(question, chunks)
    sources = sorted({chunk["source"] for chunk in chunks})
    return {
        "answer": answer,
        "sources": sources,
        "chunks": chunks,
    }
