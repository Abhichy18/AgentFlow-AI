from __future__ import annotations

from pathlib import Path

from langchain_community.docstore.document import Document
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.vectorstores import FAISS

VECTOR_DIR = Path("memory") / "faiss_index"
EMBEDDING_SIZE = 256


def _embeddings() -> FakeEmbeddings:
    return FakeEmbeddings(size=EMBEDDING_SIZE)


def build_vector_store(seed_notes: list[str]) -> None:
    if not seed_notes:
        seed_notes = ["No notes provided."]

    docs = [Document(page_content=note) for note in seed_notes]
    store = FAISS.from_documents(docs, _embeddings())
    VECTOR_DIR.parent.mkdir(parents=True, exist_ok=True)
    store.save_local(str(VECTOR_DIR))


def _load_store() -> FAISS:
    if not VECTOR_DIR.exists():
        build_vector_store(["Default productivity note."])

    return FAISS.load_local(
        str(VECTOR_DIR),
        _embeddings(),
        allow_dangerous_deserialization=True,
    )


def search_notes(query: str, k: int = 4) -> list[str]:
    store = _load_store()
    docs = store.similarity_search(query, k=k)
    return [d.page_content for d in docs]
