import re
from pathlib import Path

from config import CHUNK_OVERLAP, CHUNK_SIZE, DOCUMENTS_DIR


def load_documents(documents_dir: Path = DOCUMENTS_DIR) -> list[dict]:
    """Load all .txt documents from the documents directory."""
    documents = []
    for path in sorted(documents_dir.glob("*.txt")):
        raw = path.read_text(encoding="utf-8")
        documents.append(
            {
                "source": path.name,
                "text": clean_text(raw),
            }
        )
    return documents


def clean_text(text: str) -> str:
    """Remove HTML artifacts, boilerplate, and normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", text)
    text = re.sub(r"(Share|Read more|Cookie Policy|Sign in|Subscribe)", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph boundaries."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_paragraph(paragraph, chunk_size, overlap))
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = paragraph

    if current:
        chunks.append(current.strip())

    return [c for c in chunks if c]


def _split_long_paragraph(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def build_chunks(documents: list[dict] | None = None) -> list[dict]:
    """Return chunk records with source metadata."""
    if documents is None:
        documents = load_documents()

    records = []
    for doc in documents:
        for index, chunk in enumerate(chunk_text(doc["text"])):
            records.append(
                {
                    "text": chunk,
                    "metadata": {
                        "source": doc["source"],
                        "chunk_index": index,
                    },
                }
            )
    return records


if __name__ == "__main__":
    docs = load_documents()
    chunks = build_chunks(docs)
    print(f"Loaded {len(docs)} documents, produced {len(chunks)} chunks")
    for sample in chunks[:5]:
        print(f"\n--- {sample['metadata']['source']} #{sample['metadata']['chunk_index']} ---")
        print(sample["text"][:300])
