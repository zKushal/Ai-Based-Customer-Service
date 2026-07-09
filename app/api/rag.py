import sys
from pathlib import Path
# Ensure it can find the root project folder
sys.path.append(str(Path(__file__).parent.parent.parent))

import faiss
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.knowledge import KnowledgeBase

#region agent log
import json, time
from pathlib import Path as _DbgPath
try:
    _dbg_path = _DbgPath(__file__).parent.parent.parent / "debug-980d8b.log"
    _dbg_entry = {
        "sessionId": "980d8b",
        "runId": "pre-fix",
        "hypothesisId": "H1",
        "location": "app/api/rag.py:19",
        "message": "rag module imported",
        "data": {},
        "timestamp": int(time.time() * 1000),
    }
    with open(_dbg_path, "a", encoding="utf-8") as _f:
        _f.write(json.dumps(_dbg_entry) + "\n")
except Exception:
    pass
#endregion agent log

# Paths
FAISS_INDEX_PATH = Path(__file__).parent.parent.parent / "data" / "faiss.index"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Load embedding model once when the server starts
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

# Load FAISS index once when the server starts
if not FAISS_INDEX_PATH.exists():
    raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}. Did you run embedder.py?")
index = faiss.read_index(str(FAISS_INDEX_PATH))

def retrieve_context(query: str, k: int = 3) -> str:
    """Searches FAISS for relevant chunks, then fetches text from PostgreSQL."""
    
    # 1. Convert user question to vector
    query_vector = np.array([embeddings.embed_query(query)]).astype('float32')
    faiss.normalize_L2(query_vector)

    # 2. Search FAISS (returns Postgres IDs)
    distances, pg_ids = index.search(query_vector, k)
    pg_ids_list = pg_ids[0].tolist()
    
    # Filter out invalid IDs (FAISS returns -1 if not enough results)
    valid_ids = [pid for pid in pg_ids_list if pid != -1]
    if not valid_ids:
        return ""

    # 3. Fetch actual text from PostgreSQL
    db: Session = SessionLocal()
    try:
        chunks = db.query(KnowledgeBase.chunk_text).filter(
            KnowledgeBase.id.in_(valid_ids)
        ).all()
        
        # Combine the retrieved texts into one big string
        return "\n\n".join([chunk[0] for chunk in chunks])
    finally:
        db.close()