"""
chunker.py
----------
Loads the PDF from resources/, splits it into chunks, and prints a summary.
Uses pypdf directly + LangChain's RecursiveCharacterTextSplitter.
Avoids langchain_community to bypass DLL/policy issues on restricted systems.
"""

import os
import textwrap
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

RESOURCES_DIR = Path(__file__).parent / "resources"
PDF_PATH = RESOURCES_DIR / "SampleDocs.pdf"

CHUNK_SIZE = 1000        
CHUNK_OVERLAP = 200    



# ── Loader ────────────────────────────────────────────────────────────────────
def load_pdf(path: Path) -> list[Document]:
    """Load PDF pages as LangChain Documents."""
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    print(f"[PDF] Loading: {path.name}")
    reader = PdfReader(str(path))
    pages: list[Document] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append(
            Document(
                page_content=text,
                metadata={"source": path.name, "page": i + 1},
            )
        )

    print(f"  -> Loaded {len(pages)} page(s)")
    return pages


# ── Splitter ──────────────────────────────────────────────────────────────────
def chunk_documents(
    docs: list[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """Split a list of Documents into smaller overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
        add_start_index=True,
    )
    chunks = splitter.split_documents(docs)
    return chunks


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> list[Document]:
    pages = load_pdf(PDF_PATH)

    print(f"\n[Chunking] size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP} ...")
    chunks = chunk_documents(pages)
    print(f"  -> {len(chunks)} chunks created from {len(pages)} page(s)\n")

    # Preview first 3 chunks with clean formatting
    print("=" * 80)
    print("PREVIEW: FIRST 3 CHUNKS")
    print("=" * 80)

    for i, chunk in enumerate(chunks[:3], 1):
        page = chunk.metadata.get('page', '?')
        start = chunk.metadata.get('start_index', '?')
        length = len(chunk.page_content)

        # Print a clear header for each chunk
        print(f"\n▶ CHUNK {i} {'-' * 68}")
        print(f"  📄 Page: {page}  |  📍 Start Index: {start}  |  📏 Length: {length} chars")
        print("-" * 80)

        # Wrap the text at 80 characters so it doesn't overflow your terminal
        clean_text = chunk.page_content.strip()
        wrapped_text = textwrap.fill(clean_text, width=80)
        
        # Show the first 400 characters of the cleanly wrapped text
        preview = wrapped_text[:400]
        if len(wrapped_text) > 400:
            preview += "\n  ... [truncated]"
            
        print(preview)
        print("=" * 80 + "\n")

    return chunks


if __name__ == "__main__":
    main()
