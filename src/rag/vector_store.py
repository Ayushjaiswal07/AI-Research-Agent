import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self):
        # Initialize a persistent client (saves data to disk)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        
        # Use a local, free embedding function that runs entirely on your machine
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create our research collection
        self.collection = self.client.get_or_create_collection(
            name="research_documents",
            embedding_function=self.embedding_function
        )
        logger.info("ChromaDB local vector store initialized successfully.")

    def add_documents(self, chunks: List[str], metadata: Dict[str, Any]):
        """
        Adds text chunks to the vector database with tracking metadata.
        """
        if not chunks:
            return
            
        ids = [f"doc_{metadata.get('url_hash', 'raw')}_{i}" for i in range(len(chunks))]
        metadatas = [metadata for _ in chunks]
        
        logger.info(f"Upserting {len(chunks)} chunks into ChromaDB...")
        self.collection.upsert(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

    def query_similarity(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Queries the vector database for the most semantically relevant chunks.
        """
        logger.info(f"Querying vector store for: '{query}'")
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted_results = []
        if results and results['documents']:
            # Flatten the nested lists returned by ChromaDB queries
            docs = results['documents'][0]
            metas = results['metadatas'][0] if results['metadatas'] else [{}] * len(docs)
            distances = results['distances'][0] if results['distances'] else [0.0] * len(docs)
            
            for doc, meta, dist in zip(docs, metas, distances):
                formatted_results.append({
                    "text": doc,
                    "metadata": meta,
                    "score": dist # Lower distance means higher semantic similarity
                })
                
        return formatted_results

    def clear_database(self):
        """Reset collection to avoid mixing up historical research runs"""
        try:
            self.client.delete_collection(name="research_documents")
            self.collection = self.client.get_or_create_collection(
                name="research_documents",
                embedding_function=self.embedding_function
            )
            logger.info("Vector database cleared for fresh research run.")
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")