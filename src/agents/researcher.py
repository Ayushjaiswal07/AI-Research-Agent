from google import genai
from src.config import settings
from src.tools.web_search import search_web
from src.tools.scraper import scrape_url
from src.rag.chunker import split_text
from src.rag.vector_store import VectorStoreManager
from src.agents.prompts import RESEARCHER_SYSTEM_PROMPT
import hashlib
import logging

logger = logging.getLogger(__name__)



class AIResearchAgent:
    def __init__(self):
        # Initialize the official Gemini SDK client
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.vector_store = VectorStoreManager()
        
    def run_research(self, topic: str) -> str:
        print(f"\n🚀 Starting AI Research Agent for: '{topic}'")
        
        # 1. Clear previous memory for a fresh run
        self.vector_store.clear_database()
        
        # 2. Search the web
        print("\n🔍 Step 1: Searching the web...")
        search_results = search_web(topic)
        
        if not search_results:
            return "Task Failed: I couldn't find any search results for that topic."
            
        # 3. Scrape and index
        print("\n📚 Step 2: Reading and indexing sources...")
        for res in search_results:
            url = res['link']
            print(f"  -> Extracting data from: {url}")
            text = scrape_url(url)
            
            if text:
                chunks = split_text(text)
                # Create a simple hash to track the source URL
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                metadata = {"url": url, "url_hash": url_hash, "title": res['title']}
                self.vector_store.add_documents(chunks, metadata)
                
        # 4. Retrieve most relevant information
        print("\n🧠 Step 3: Analyzing data (Vector RAG retrieval)...")
        # We pull the top 5 most relevant chunks to give Gemini good context
        retrieved_docs = self.vector_store.query_similarity(topic, n_results=5)
        
        if not retrieved_docs:
            return "Task Failed: Could not extract meaningful text from the sources."
            
        # Build the context string for the prompt
        context = "RETRIEVED CONTEXT:\n"
        sources = set()
        for i, doc in enumerate(retrieved_docs):
            context += f"--- Snippet {i+1} ---\n{doc['text']}\n\n"
            sources.add(doc['metadata']['url'])
            
        # 5. Generate final report
        print("\n✍️ Step 4: Generating final report using Gemini 2.5 Flash...")
        
        # Combine the system prompt, the user topic, and the RAG context
        full_prompt = f"{RESEARCHER_SYSTEM_PROMPT}\n\nRESEARCH TOPIC: {topic}\n\n{context}"
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_prompt,
            )
            
            # Append the dynamic sources to the bottom of the report
            report = response.text + "\n\n---\n### 🔗 Sources Analyzed\n"
            for source in sources:
                report += f"* {source}\n"
                
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            return f"Error communicating with Gemini API: {e}"