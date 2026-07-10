import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import faiss
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.knowledge import KnowledgeBase

FAISS_INDEX_PATH = Path(__file__).parent.parent.parent / "data" / "faiss.index"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

if not FAISS_INDEX_PATH.exists():
    raise FileNotFoundError(
        f"FAISS index not found at {FAISS_INDEX_PATH}. Did you run embedder.py?"
    )
index = faiss.read_index(str(FAISS_INDEX_PATH))


def retrieve_context(query: str, k: int = 3) -> tuple[str, float]:
    """Search FAISS and return matched context text plus the top similarity score."""
    query_vector = np.array([embeddings.embed_query(query)]).astype("float32")
    faiss.normalize_L2(query_vector)

    distances, pg_ids = index.search(query_vector, k)
    top_score = float(distances[0][0])

    pg_ids_list = pg_ids[0].tolist()
    valid_ids = [pid for pid in pg_ids_list if pid != -1]

    context_text = ""
    if valid_ids:
        db: Session = SessionLocal()
        try:
            chunks = db.query(KnowledgeBase.chunk_text).filter(
                KnowledgeBase.id.in_(valid_ids)
            ).all()
            context_text = "\n\n".join([chunk[0] for chunk in chunks])
        finally:
            db.close()

    return context_text, top_score
