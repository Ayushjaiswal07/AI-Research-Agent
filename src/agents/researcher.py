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
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.vector_store = VectorStoreManager()  # Singleton — same instance as routes.py
        
    def run_research(self, topic: str) -> str:
        print(f"\n🚀 Starting AI Research Agent for: '{topic}'")
        
        # 1. Clear only web-scraped docs — preserve any uploaded files
        self.vector_store.clear_web_documents()
        
        # 2. Search the web
        print("\n🔍 Step 1: Searching the web...")
        search_results = search_web(topic)
        
        # 3. Scrape and index web results (if any)
        if search_results:
            print("\n📚 Step 2: Reading and indexing web sources...")
            for res in search_results:
                url = res['link']
                print(f"  -> Extracting data from: {url}")
                text = scrape_url(url)
                if text:
                    chunks = split_text(text)
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    metadata = {
                        "url": url,
                        "url_hash": url_hash,
                        "title": res['title'],
                        "source_type": "web",
                    }
                    self.vector_store.add_documents(chunks, metadata)
        else:
            print("\n⚠️  No web results found — will rely on uploaded documents only.")
                
        # 4. Retrieve most relevant information (web + uploads combined)
        print("\n🧠 Step 3: Analyzing data (Vector RAG retrieval)...")
        retrieved_docs = self.vector_store.query_similarity(topic, n_results=5)
        
        if not retrieved_docs:
            return "Task Failed: No relevant information found. Try uploading a document or rephrasing your query."
            
        # Build the context string for the prompt
        context = "RETRIEVED CONTEXT:\n"
        web_sources = set()
        upload_sources = set()
        for i, doc in enumerate(retrieved_docs):
            context += f"--- Snippet {i+1} ---\n{doc['text']}\n\n"
            meta = doc['metadata']
            if meta.get('source_type') == 'upload':
                upload_sources.add(meta.get('title', 'Uploaded file'))
            else:
                web_sources.add(meta.get('url', ''))
            
        # 5. Generate final report
        print("\n✍️ Step 4: Generating final report using Gemini 2.5 Flash...")
        full_prompt = f"{RESEARCHER_SYSTEM_PROMPT}\n\nRESEARCH TOPIC: {topic}\n\n{context}"
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_prompt,
            )
            
            report = response.text + "\n\n---\n### 🔗 Sources Analyzed\n"
            for source in upload_sources:
                report += f"* 📄 {source} *(uploaded document)*\n"
            for source in web_sources:
                if source:
                    report += f"* {source}\n"
                
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            return f"Error communicating with Gemini API: {e}"