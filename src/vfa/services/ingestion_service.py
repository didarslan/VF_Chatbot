from __future__ import annotations

from typing import Dict, List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def make_document(text: str, metadata: Dict) -> Document:
    return Document(page_content=text, metadata=metadata)


def chunk_documents(docs: List[Document], chunk_size: int = 1500, chunk_overlap: int = 150) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(docs)

