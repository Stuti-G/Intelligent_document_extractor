from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document as LangchainDocument
from src.loaders import DocumentChunk
from src.config import EMBEDDING_MODEL_NAME

class RAGEngine:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        self.vector_store = None

    def index_document(self, chunks: List[DocumentChunk]):
        documents = [
            LangchainDocument(
                page_content=chunk.text,
                metadata={"page": chunk.page_number, "source": chunk.source_file}
            ) for chunk in chunks
        ]
        
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name="temp_doc_collection"
        )

    def retrieve(self, query: str, k: int = 3) -> List[LangchainDocument]:
        if not self.vector_store:
            return []
        return self.vector_store.similarity_search(query, k=k)

    def clear(self):
        if self.vector_store:
            self.vector_store.delete_collection()
            self.vector_store = None
