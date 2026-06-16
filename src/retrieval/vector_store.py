from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions


class VectorStore:
    def __init__(self, collection_name: str = "documents", persist_directory: str = "data/chroma"):

        huggingface_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )

        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(name=collection_name, embedding_function=huggingface_ef)

    def add_documents(
        self,
        documents: list[str],
        ids: list[str] | None = None,
        metadatas: list[dict] | None = None,
    ):
        if ids is None:
            ids = [str(i) for i in range(len(documents))]
        self.collection.add(documents=documents, ids=ids, metadatas=metadatas)

    def similarity_search(self, query: str, k: int = 4):
        return self.collection.query(query_texts=[query], n_results=k)

    def count(self) -> int:
        return self.collection.count()

    def delete_collection(self):
        self.client.delete_collection(self.collection.name)
