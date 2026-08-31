"""Offline step: embed the job-description PDF into a local Chroma database."""
# Help: Lesson 23 - GenAI - NLP & Embedding & Retrieval (folder may be empty)
# Help: Lesson 22 - GenAI (DL) - LangChain (document loaders / chains)

import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.modules.config import CHROMA_DIR, PDF_PATH


def embed_pdf(pdf_path=PDF_PATH, persist_dir=CHROMA_DIR):
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing. Copy .env.example to .env.")

    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    loader = PyPDFLoader(str(pdf_path))
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(persist_dir),
    )

    print(f"Embedded {len(chunks)} chunks from {pdf_path} into {persist_dir}")
    return len(chunks)


def get_retriever(persist_dir=CHROMA_DIR, k=3):
    embeddings = OpenAIEmbeddings()
    store = Chroma(
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
    )
    return store.as_retriever(search_kwargs={"k": k})


def retrieve_job_info(query, persist_dir=CHROMA_DIR, k=3):
    """Search the job-description Chroma store and return matching text."""
    persist_path = Path(persist_dir)
    if not persist_path.exists() or not any(persist_path.iterdir()):
        return (
            "The job-description index has not been created yet. "
            "Run: python -m app.modules.embedding.embed_pdf"
        )

    retriever = get_retriever(persist_dir=persist_dir, k=k)
    documents = retriever.invoke(query)
    if not documents:
        return "No matching information was found in the job description."

    parts = []
    for doc in documents:
        parts.append(doc.page_content)
    return "\n\n".join(parts)


if __name__ == "__main__":
    embed_pdf()
