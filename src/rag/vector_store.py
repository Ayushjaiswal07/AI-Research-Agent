import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStoreManager:
    _instance = None  # Singleton so all callers share one client

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.client.get_or_create_collection(
            name="research_documents",
            embedding_function=self.embedding_function
        )
        self._initialized = True
        logger.info("ChromaDB local vector store initialized successfully.")

    def _get_collection(self):
        """Always fetch the collection fresh to avoid stale references after a clear."""
        return self.client.get_or_create_collection(
            name="research_documents",
            embedding_function=self.embedding_function,
        )

    def add_documents(self, chunks: List[str], metadata: Dict[str, Any]):
        if not chunks:
            return
        collection = self._get_collection()
        ids = [f"doc_{metadata.get('url_hash', 'raw')}_{i}" for i in range(len(chunks))]
        metadatas = [metadata for _ in chunks]
        logger.info(f"Upserting {len(chunks)} chunks into ChromaDB...")
        collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)

    def query_similarity(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        logger.info(f"Querying vector store for: '{query}'")
        collection = self._get_collection()
        results = collection.query(query_texts=[query], n_results=n_results)
        formatted_results = []
        if results and results['documents']:
            docs = results['documents'][0]
            metas = results['metadatas'][0] if results['metadatas'] else [{}] * len(docs)
            distances = results['distances'][0] if results['distances'] else [0.0] * len(docs)
            for doc, meta, dist in zip(docs, metas, distances):
                formatted_results.append({"text": doc, "metadata": meta, "score": dist})
        return formatted_results

    def clear_web_documents(self):
        """Remove only web-scraped chunks, preserving uploaded file chunks."""
        collection = self._get_collection()
        try:
            results = collection.get(where={"source_type": {"$ne": "upload"}})
            ids_to_delete = results.get("ids", [])
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                logger.info(f"Cleared {len(ids_to_delete)} web-scraped chunks, uploads preserved.")
            else:
                logger.info("No web-scraped chunks to clear.")
        except Exception as e:
            logger.warning(f"Could not selectively clear web docs: {e}")

    def clear_database(self):
        """Reset the entire collection (web + uploads)."""
        try:
            self.client.delete_collection(name="research_documents")
            self.client.get_or_create_collection(
                name="research_documents",
                embedding_function=self.embedding_function
            )
            logger.info("Vector database fully cleared.")
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")