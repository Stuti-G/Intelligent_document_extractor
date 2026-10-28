from src.rag import RAGEngine


class FakeVectorStore:
    def __init__(self):
        self.deleted = False

    def delete_collection(self):
        self.deleted = True

    def similarity_search(self, query, k=3):
        return []


def test_two_rag_engines_are_isolated(monkeypatch):
    created_collections = []
    stores = []

    monkeypatch.setattr(
        "src.rag.HuggingFaceEmbeddings",
        lambda **kwargs: object()
    )

    def fake_from_documents(**kwargs):
        created_collections.append(kwargs["collection_name"])
        store = FakeVectorStore()
        stores.append(store)
        return store

    monkeypatch.setattr(
        "src.rag.Chroma.from_documents",
        fake_from_documents
    )

    rag_a = RAGEngine()
    rag_b = RAGEngine()

    rag_a.index_document([])
    rag_b.index_document([])

    assert created_collections[0] != created_collections[1]

    rag_a.clear()

    assert stores[0].deleted is True
    assert stores[1].deleted is False

    rag_b.clear()
    assert stores[1].deleted is True