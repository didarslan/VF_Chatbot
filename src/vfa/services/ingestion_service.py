from typing import List, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_documents(docs: List[Document], chunk_size: int = 1500, chunk_overlap: int = 150) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(docs)

def make_document(text: str, metadata: Dict) -> Document:
    return Document(page_content=text, metadata=metadata)
