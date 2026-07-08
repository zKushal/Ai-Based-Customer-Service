"""
embedder.py
-----------
1. Gets chunks from chunker.py
2. Saves chunk TEXT to PostgreSQL
3. Saves VECTORS to local FAISS, mapped to the PostgreSQL IDs
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import os
import faiss
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings

# Imports from your project structure
from chunker import main as get_chunks
from app.core.database import SessionLocal      # <-- ADDED
from app.models.knowledge import KnowledgeBase  # <-- ADDED

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR = "data"
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")

# Using MiniLM for speed (384 dimensions)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2" 


def main():
    # 1. Get the chunks from your chunker
    print("Fetching chunks from chunker.py...")
    chunks = get_chunks()
    
    if not chunks:
        print("No chunks found. Exiting.")
        return

    # 2. Load the Embedding Model
    print(f"\n[Embeddings] Loading model: {EMBEDDING_MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    db = SessionLocal()
    try:
        pg_ids = []      
        all_vectors = [] 

        print("\n[Database] Saving chunks to PostgreSQL...")
        for i, chunk in enumerate(chunks):
            
            # 3. Save text to PostgreSQL (matches your new schema exactly)
            db_chunk = KnowledgeBase(
                source_title="SampleDocs.pdf",
                chunk_text=chunk.page_content
            )
            db.add(db_chunk)
            db.commit()
            db.refresh(db_chunk) # This grabs the auto-generated ID (1, 2, 3...)
            
            # 4. Store the ID and generate the vector
            pg_ids.append(db_chunk.id)
            vector = embeddings.embed_query(chunk.page_content)
            all_vectors.append(vector)
            
            # Print progress every 20 chunks
            if (i + 1) % 20 == 0:
                print(f"  -> Processed {i + 1}/{len(chunks)} chunks...")

        # 5. Prepare vectors for FAISS
        print("\n[FAISS] Building index...")
        vectors_np = np.array(all_vectors).astype('float32')
        
        # Normalize for Cosine Similarity
        faiss.normalize_L2(vectors_np)

        # 6. Build FAISS index mapped to PostgreSQL IDs
        dimension = vectors_np.shape[1]
        base_index = faiss.IndexFlatIP(dimension)
        index = faiss.IndexIDMap(base_index)
        
        # Link the math vectors to the PostgreSQL IDs
        index.add_with_ids(vectors_np, np.array(pg_ids))

        # 7. Save FAISS to disk
        os.makedirs(DATA_DIR, exist_ok=True)
        faiss.write_index(index, FAISS_INDEX_PATH)

        print(f"\n✅ SUCCESS!")
        print(f"  -> {len(pg_ids)} text chunks saved to PostgreSQL.")
        print(f"  -> {len(pg_ids)} vectors mapped to PG IDs and saved to {FAISS_INDEX_PATH}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()