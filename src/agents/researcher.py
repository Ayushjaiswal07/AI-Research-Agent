import ollama
from src.config import settings
from src.tools.web_search import search_web
from src.tools.scraper import scrape_url
from src.rag.chunker import split_text
from src.rag.vector_store import VectorStoreManager
from src.agents.prompts import RESEARCHER_SYSTEM_PROMPT
import hashlib
import logging
import re

logger = logging.getLogger(__name__)

# ── Intent patterns ──────────────────────────────────────────────────────────

# User is asking about their own uploaded file
FILE_INTENT_PATTERNS = re.compile(
    r"\b(my file|the file|from the file|in the file|from my|in my|uploaded|attachment|document|list all|show all|what('s| is) in)\b",
    re.IGNORECASE,
)

# Casual conversation — answer directly without any retrieval
CONVERSATIONAL_PATTERNS = re.compile(
    r"^(hi+|hello+|hey+|thanks|thank you|ok|okay|great|cool|got it|nice|bye|good morning|good evening|good night|who are you|what can you do|what are you|help me|sup|what'?s up)\b.*$",
    re.IGNORECASE,
)

# General knowledge — LLM can answer from training, no retrieval needed
BRAIN_PATTERNS = re.compile(
    r"^(what is|what are|what was|what were|explain|define|who is|who was|who were|when did|when was|how does|how do|how did|why is|why does|why did|tell me about|describe|what does .* mean|give me an overview|give an overview|summarize what you know|what do you know about|can you explain|could you explain)\b",
    re.IGNORECASE,
)


class AIResearchAgent:
    def __init__(self):
        self.vector_store = VectorStoreManager()

    def _has_uploaded_docs(self) -> bool:
        collection = self.vector_store._get_collection()
        try:
            results = collection.get(where={"source_type": {"$eq": "upload"}})
            return len(results.get("ids", [])) > 0
        except Exception:
            return False

    def _get_all_upload_chunks(self):
        """Fetch every uploaded chunk directly — no semantic filtering."""
        collection = self.vector_store._get_collection()
        try:
            results = collection.get(where={"source_type": {"$eq": "upload"}})
            chunks = []
            for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
                chunks.append({"text": doc, "metadata": meta, "score": 0.0})
            return chunks
        except Exception as e:
            logger.warning(f"Failed to fetch all upload chunks: {e}")
            return []

    def _query_uploads(self, topic: str, n_results: int = 5):
        """Semantic search over uploaded chunks only."""
        collection = self.vector_store._get_collection()
        try:
            results = collection.query(
                query_texts=[topic],
                n_results=n_results,
                where={"source_type": {"$eq": "upload"}},
            )
            formatted = []
            if results and results["documents"] and results["documents"][0]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
                distances = results["distances"][0] if results["distances"] else [1.0] * len(docs)
                for doc, meta, dist in zip(docs, metas, distances):
                    formatted.append({"text": doc, "metadata": meta, "score": dist})
            return formatted
        except Exception as e:
            logger.warning(f"Upload semantic query failed: {e}")
            return []

    def _answer_from_brain(self, topic: str, conversational: bool = False) -> str:
        """Answer directly from the LLM with no retrieval at all."""
        if conversational:
            prompt = (
                "You are a helpful AI Research Assistant. "
                "Reply conversationally and briefly to the following message:\n\n"
                f"{topic}"
            )
        else:
            prompt = (
                "You are an expert AI Research Assistant. "
                "Answer the following question clearly and thoroughly using your own knowledge. "
                "Structure your response with markdown headings and bullet points where appropriate.\n\n"
                f"Question: {topic}"
            )
        try:
            response = ollama.generate(model=settings.OLLAMA_MODEL, prompt=prompt)
            return response["response"]
        except Exception as e:
            logger.error(f"Ollama brain error: {e}")
            return f"Error communicating with Ollama: {e}. Make sure Ollama is running (ollama serve)."

    def run_research(self, topic: str) -> str:
        print(f"\n🚀 Starting AI Research Agent for: '{topic}'")

        topic_stripped = topic.strip()

        # ── 0. Intent routing ────────────────────────────────────────────────

        # Path A: Conversational — reply casually, no retrieval
        if CONVERSATIONAL_PATTERNS.match(topic_stripped):
            print("\n💬 Conversational query — answering directly...")
            return self._answer_from_brain(topic, conversational=True)

        has_uploads = self._has_uploaded_docs()
        user_wants_file = bool(FILE_INTENT_PATTERNS.search(topic_stripped))

        # Path B: General knowledge — no uploads, no file intent, simple factual question
        if not has_uploads and not user_wants_file and BRAIN_PATTERNS.match(topic_stripped):
            print("\n🧠 General knowledge query — answering from model knowledge...")
            return self._answer_from_brain(topic, conversational=False)

        # Path C: Full RAG pipeline
        context_parts = []
        upload_sources = set()
        web_sources = set()

        # ── 1. Handle uploaded documents ────────────────────────────────────
        if has_uploads:
            if user_wants_file:
                print("\n📂 User is asking about uploaded file — fetching all chunks directly...")
                upload_docs = self._get_all_upload_chunks()
                skip_web = True
            else:
                print("\n📂 Querying uploaded knowledge base (semantic)...")
                upload_docs = self._query_uploads(topic, n_results=5)
                best_score = upload_docs[0]["score"] if upload_docs else 1.0
                print(f"   Best upload match score: {best_score:.3f}")
                skip_web = best_score < 0.4

            if upload_docs:
                block = "--- UPLOADED DOCUMENT CONTEXT ---\n"
                for i, doc in enumerate(upload_docs):
                    block += f"[Chunk {i+1}]\n{doc['text']}\n\n"
                    upload_sources.add(doc["metadata"].get("title", "Uploaded file"))
                context_parts.append(block)
        else:
            skip_web = False

        # ── 2. Web search ────────────────────────────────────────────────────
        if not skip_web:
            print("\n🔍 Searching the web...")
            self.vector_store.clear_web_documents()
            search_results = search_web(topic)

            if search_results:
                print("\n📚 Scraping and indexing web sources...")
                for res in search_results:
                    url = res["link"]
                    print(f"   -> {url}")
                    text = scrape_url(url)
                    if text:
                        chunks = split_text(text)
                        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                        self.vector_store.add_documents(chunks, {
                            "url": url,
                            "url_hash": url_hash,
                            "title": res["title"],
                            "source_type": "web",
                        })

                web_docs = self.vector_store.query_similarity(topic, n_results=5)
                if web_docs:
                    block = "--- WEB SEARCH CONTEXT ---\n"
                    for i, doc in enumerate(web_docs):
                        block += f"[Chunk {i+1}]\n{doc['text']}\n\n"
                        web_sources.add(doc["metadata"].get("url", ""))
                    context_parts.append(block)
            else:
                print("   No web results found.")

        # ── 3. Fallback to brain if retrieval found nothing ──────────────────
        if not context_parts:
            print("\n🧠 No retrieval results — falling back to model knowledge...")
            return self._answer_from_brain(topic, conversational=False)

        # ── 4. Build RAG prompt ──────────────────────────────────────────────
        combined_context = "\n".join(context_parts)

        if user_wants_file and not web_sources:
            system_note = """
IMPORTANT: The user is asking specifically about their uploaded file(s).
Answer ONLY from the UPLOADED DOCUMENT CONTEXT. Do not speculate or use outside knowledge.
Present the information exactly as found in the file — do not summarize away details like package names or version numbers.
"""
        else:
            system_note = """
IMPORTANT:
- You have context from uploaded documents and/or web search results.
- Prioritize the uploaded document context when it is relevant to the query.
- Use web context to supplement or fill gaps.
- If the uploaded document is not relevant to the query, answer using only web context.
- Clearly indicate which source each piece of information came from.
- Never hallucinate. If neither source answers the query, say so.
"""

        full_prompt = (
            f"{RESEARCHER_SYSTEM_PROMPT}\n{system_note}\n\n"
            f"RESEARCH TOPIC: {topic}\n\n{combined_context}"
        )

        # ── 5. Generate response ─────────────────────────────────────────────
        print(f"\n✍️  Generating response with Ollama ({settings.OLLAMA_MODEL})...")
        try:
            response = ollama.generate(model=settings.OLLAMA_MODEL, prompt=full_prompt)
            report = response["response"] + "\n\n---\n### 🔗 Sources\n"
            for src in upload_sources:
                report += f"* 📄 {src} *(uploaded document)*\n"
            for src in web_sources:
                if src:
                    report += f"* 🌐 {src}\n"
            return report

        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"Error communicating with Ollama: {e}. Make sure Ollama is running (ollama serve)."