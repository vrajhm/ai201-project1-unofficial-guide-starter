import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DOCUMENTS_DIR = BASE_DIR / "documents"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "unofficial_guide"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
