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
from typing import List, Callable, Optional

logger = logging.getLogger(__name__)

# ── Intent patterns ──────────────────────────────────────────────────────────

FILE_INTENT_PATTERNS = re.compile(
    r"\b(my file|the file|from the file|in the file|from my|in my|uploaded|attachment|document|list all|show all|what('s| is) in)\b",
    re.IGNORECASE,
)

CONVERSATIONAL_PATTERNS = re.compile(
    r"^(hi+|hello+|hey+|thanks|thank you|ok|okay|great|cool|got it|nice|bye|good morning|good evening|good night|who are you|what can you do|what are you|help me|sup|what'?s up)\b.*$",
    re.IGNORECASE,
)

BRAIN_PATTERNS = re.compile(
    r"^(what is|what are|what was|what were|explain|define|who is|who was|who were|when did|when was|how does|how do|how did|why is|why does|why did|tell me about|describe|what does .* mean|give me an overview|give an overview|summarize what you know|what do you know about|can you explain|could you explain)\b",
    re.IGNORECASE,
)


class AIResearchAgent:
    def __init__(self):
        self.vector_store = VectorStoreManager()

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _has_uploaded_docs(self, selected_hashes: List[str] = None) -> bool:
        collection = self.vector_store._get_collection()
        try:
            if selected_hashes:
                results = collection.get(where={
                    "$and": [
                        {"source_type": {"$eq": "upload"}},
                        {"url_hash": {"$in": selected_hashes}},
                    ]
                })
            else:
                results = collection.get(where={"source_type": {"$eq": "upload"}})
            return len(results.get("ids", [])) > 0
        except Exception:
            return False

    def _get_all_upload_chunks(self, selected_hashes: List[str] = None):
        if selected_hashes:
            return self.vector_store.get_all_chunks_for_files(selected_hashes)
        collection = self.vector_store._get_collection()
        try:
            results = collection.get(where={"source_type": {"$eq": "upload"}})
            return [
                {"text": doc, "metadata": meta, "score": 0.0}
                for doc, meta in zip(results.get("documents", []), results.get("metadatas", []))
            ]
        except Exception as e:
            logger.warning(f"Failed to fetch all upload chunks: {e}")
            return []

    def _query_uploads(self, topic: str, n_results: int = 5, selected_hashes: List[str] = None):
        if selected_hashes:
            return self.vector_store.query_selected_files(topic, selected_hashes, n_results)
        collection = self.vector_store._get_collection()
        try:
            results = collection.query(
                query_texts=[topic],
                n_results=n_results,
                where={"source_type": {"$eq": "upload"}},
            )
            formatted = []
            if results and results["documents"] and results["documents"][0]:
                docs      = results["documents"][0]
                metas     = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
                distances = results["distances"][0] if results["distances"] else [1.0] * len(docs)
                for doc, meta, dist in zip(docs, metas, distances):
                    formatted.append({"text": doc, "metadata": meta, "score": dist})
            return formatted
        except Exception as e:
            logger.warning(f"Upload semantic query failed: {e}")
            return []

    def _answer_from_brain(self, topic: str, conversational: bool, step: Callable) -> str:
        if conversational:
            step("💬 Answering conversationally — no retrieval needed.")
            prompt = (
                "You are a helpful AI Research Assistant. "
                "Reply conversationally and briefly:\n\n" + topic
            )
        else:
            step("🧠 Answering from model knowledge — no retrieval needed.")
            prompt = (
                "You are an expert AI Research Assistant. "
                "Answer clearly and thoroughly using your own knowledge. "
                "Use markdown headings and bullet points.\n\nQuestion: " + topic
            )
        step("⚙️ Generating response...")
        try:
            response = ollama.generate(model=settings.OLLAMA_MODEL, prompt=prompt)
            return response["response"]
        except Exception as e:
            logger.error(f"Ollama brain error: {e}")
            return f"Error communicating with Ollama: {e}. Make sure Ollama is running."

    # ── Main entry point ─────────────────────────────────────────────────────

    def run_research(
        self,
        topic: str,
        selected_file_hashes: List[str] = None,
        on_step: Optional[Callable[[str], None]] = None,
    ) -> str:

        # Default no-op so we never have to guard on_step calls
        def step(text: str):
            print(text)
            if on_step:
                on_step(text)

        step(f"🚀 Starting research for: \"{topic}\"")

        topic_stripped = topic.strip()

        # ── 0. Intent routing ────────────────────────────────────────────────

        if CONVERSATIONAL_PATTERNS.match(topic_stripped):
            return self._answer_from_brain(topic, conversational=True, step=step)

        has_selected = bool(selected_file_hashes)
        has_uploads  = self._has_uploaded_docs(selected_file_hashes if has_selected else None)
        user_wants_file = bool(FILE_INTENT_PATTERNS.search(topic_stripped))

        if not has_selected and not has_uploads and not user_wants_file and BRAIN_PATTERNS.match(topic_stripped):
            return self._answer_from_brain(topic, conversational=False, step=step)

        context_parts  = []
        upload_sources = set()
        web_sources    = set()

        # ── 1. Uploaded documents ────────────────────────────────────────────
        if has_uploads:
            if user_wants_file or has_selected:
                label = (
                    f"📂 Fetching all chunks from {len(selected_file_hashes)} selected file(s)..."
                    if has_selected
                    else "📂 User asked about uploaded file — fetching all chunks..."
                )
                step(label)
                upload_docs = self._get_all_upload_chunks(selected_file_hashes or None)
                skip_web = True
            else:
                step("📂 Searching uploaded knowledge base (semantic search)...")
                upload_docs = self._query_uploads(topic, n_results=5)
                best_score  = upload_docs[0]["score"] if upload_docs else 1.0
                step(f"   ✅ Best match score: {best_score:.3f} {'(highly relevant)' if best_score < 0.4 else '(moderate relevance)'}")
                skip_web = best_score < 0.4

            if upload_docs:
                step(f"   📄 Retrieved {len(upload_docs)} relevant chunk(s) from uploaded document(s).")
                block = "--- UPLOADED DOCUMENT CONTEXT ---\n"
                for i, doc in enumerate(upload_docs):
                    block += f"[Chunk {i+1}]\n{doc['text']}\n\n"
                    upload_sources.add(doc["metadata"].get("title", "Uploaded file"))
                context_parts.append(block)
        else:
            skip_web = False

        if has_selected and not context_parts:
            return (
                "⚠️ The selected file(s) don't contain enough indexed content to answer your query. "
                "Try deselecting files or re-uploading them."
            )

        # ── 2. Web search ────────────────────────────────────────────────────
        if not skip_web:
            step("🔍 Searching the web via DuckDuckGo...")
            self.vector_store.clear_web_documents()
            search_results = search_web(topic)

            if search_results:
                step(f"   🌐 Found {len(search_results)} result(s). Scraping content...")
                scraped_count = 0
                for res in search_results:
                    url  = res["link"]
                    step(f"   ↳ Scraping: {url}")
                    text = scrape_url(url)
                    if text:
                        chunks   = split_text(text)
                        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                        self.vector_store.add_documents(chunks, {
                            "url":         url,
                            "url_hash":    url_hash,
                            "title":       res["title"],
                            "source_type": "web",
                        })
                        scraped_count += 1
                        step(f"   ✅ Indexed {len(chunks)} chunks from \"{res['title']}\"")
                    else:
                        step(f"   ⚠️ Could not scrape content from {url}")

                step(f"📊 Running semantic search across {scraped_count} indexed source(s)...")
                web_docs = self.vector_store.query_similarity(topic, n_results=5)
                if web_docs:
                    step(f"   ✅ Retrieved {len(web_docs)} relevant chunk(s) from web sources.")
                    block = "--- WEB SEARCH CONTEXT ---\n"
                    for i, doc in enumerate(web_docs):
                        block += f"[Chunk {i+1}]\n{doc['text']}\n\n"
                        web_sources.add(doc["metadata"].get("url", ""))
                    context_parts.append(block)
                else:
                    step("   ⚠️ Semantic search returned no relevant web chunks.")
            else:
                step("   ⚠️ No web results found. Falling back to model knowledge.")

        # ── 3. Fallback ──────────────────────────────────────────────────────
        if not context_parts:
            step("🧠 No retrieval results — falling back to model knowledge...")
            return self._answer_from_brain(topic, conversational=False, step=step)

        # ── 4. Build prompt ──────────────────────────────────────────────────
        step("📝 Building prompt with retrieved context...")
        combined_context = "\n".join(context_parts)

        if (user_wants_file or has_selected) and not web_sources:
            file_names  = ", ".join(upload_sources) if upload_sources else "the selected file(s)"
            system_note = f"""
IMPORTANT: The user is asking specifically about their uploaded file(s): {file_names}.
Answer ONLY from the UPLOADED DOCUMENT CONTEXT. Do not speculate or use outside knowledge.
Present information exactly as found in the document.
"""
        else:
            system_note = """
IMPORTANT:
- Prioritize the uploaded document context when relevant.
- Use web context to supplement or fill gaps.
- Clearly indicate which source each piece of information came from.
- Never hallucinate. If neither source answers the query, say so.
"""

        full_prompt = (
            f"{RESEARCHER_SYSTEM_PROMPT}\n{system_note}\n\n"
            f"RESEARCH TOPIC: {topic}\n\n{combined_context}"
        )

        # ── 5. Generate ──────────────────────────────────────────────────────
        step(f"✍️  Generating final report with {settings.OLLAMA_MODEL}...")
        try:
            response = ollama.generate(model=settings.OLLAMA_MODEL, prompt=full_prompt)
            step("✅ Report generated successfully.")
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
