import hashlib
from src.rag.chunker import split_text
from src.rag.vector_store import VectorStoreManager

def main():
    print("--- Testing RAG Processing pipeline ---")
    
    # 1. Sample heavy text block simulating web data
    sample_text = (
        "Large language models (LLMs) like Gemini 2.5 Flash utilize deep transformer architectures "
        "to process massive context sequences. Retrieval-Augmented Generation (RAG) significantly optimizes "
        "these models by inserting relevant source material dynamically into the system prompt. "
        "Vector databases like ChromaDB serve as the specialized indexing engine for RAG. They use "
        "mathematical embeddings to project clean text passages into multi-dimensional spatial vectors. "
        "When an agent encounters a problem, it evaluates the vector distance between the query "
        "and indexed document blocks, isolating the highest semantic matches for synthesis."
    )
    
    print(f"Original Text Length: {len(sample_text)} characters.")
    
    # 2. Test the text chunker
    chunks = split_text(sample_text, chunk_size=150, chunk_overlap=30)
    for idx, chunk in enumerate(chunks):
        print(f"  Chunk {idx+1}: \"{chunk}\" (Length: {len(chunk)})")
        
    # 3. Test the Vector Store
    db = VectorStoreManager()
    db.clear_database() # Start clean
    
    # Mock source metadata tracking
    url = "https://example.com/ai_architecture_brief"
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    metadata = {"url": url, "url_hash": url_hash, "topic": "AI Engineering"}
    
    db.add_documents(chunks, metadata=metadata)
    print("\n✅ Successfully indexed chunks into local ChromaDB.")
    
    # 4. Test Semantics query retrieval
    search_query = "How do vector databases help RAG pipelines?"
    print(f"\n--- Testing Semantic Search Query: '{search_query}' ---")
    
    matches = db.query_similarity(search_query, n_results=2)
    
    for i, match in enumerate(matches):
        print(f"\nMatch {i+1} (Vector Distance Score: {match['score']:.4f}):")
        print(f"  Text: \"{match['text']}\"")
        print(f"  Source metadata: {match['metadata']}")

if __name__ == "__main__":
    main()