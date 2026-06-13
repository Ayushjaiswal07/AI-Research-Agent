import ollama
from src.config import settings
from src.tools.web_search import search_web
from src.tools.scraper import scrape_url
from src.rag.chunker import split_text
from src.rag.vector_store import VectorStoreManager
from src.agents.prompts import RESEARCHER_SYSTEM_PROMPT
from src.memory.chat_memory import get_recent_context, append_turn
import hashlib
import logging
import re
from typing import List, Callable, Optional, Literal

logger = logging.getLogger(__name__)

FILE_INTENT_PATTERNS = re.compile(
    r"\b(my file|the file|from the file|in the file|from my|in my|uploaded|attachment|list all|show all|what('s| is) in|summarize (the |this )?file|summarize (the |this )?document)\b",
    re.IGNORECASE,
)

WEB_INTENT_PATTERNS = re.compile(
    r"\b(search (the |the web|online|internet)|web search|look (it )?up online|google|find online|search for|do a search|also search|search web|find on web)\b",
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

# Cosine DISTANCE thresholds (lower = more similar in ChromaDB)
# < 0.70  → file is relevant, use it
# >= 0.70 → file is not relevant, skip it
FILE_RELEVANCE_THRESHOLD = 0.70

# Below this score the file is highly relevant — skip web entirely
FILE_SKIP_WEB_THRESHOLD = 0.45


class AIResearchAgent:
    def __init__(self):
        self.vector_store = VectorStoreManager()

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

    def _query_uploads_semantic(
        self,
        topic: str,
        n_results: int = 5,
        selected_hashes: List[str] = None,
    ) -> List[dict]:
        """Always semantic search — never dump all chunks blindly."""
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

    def _get_all_upload_chunks(self, selected_hashes: List[str] = None) -> List[dict]:
        """Only for explicit 'list/summarize the file' requests."""
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

    def _enrich_query_for_web(self, topic: str, upload_sources: set) -> str:
        """
        If the file was relevant but also searching web, add context to the
        query so the search engine doesn't return unrelated results.
        E.g. "how does transformer work?" + uploaded AI paper
        → "how does transformer neural network model work? AI deep learning"
        """
        # If the query is short and ambiguous, let the LLM expand it
        if len(topic.split()) <= 6:
            try:
                expand_prompt = (
                    f"You are a search query optimizer. "
                    f"The user asked: \"{topic}\". "
                    f"Rewrite this as a precise web search query (max 10 words) "
                    f"that avoids ambiguity. Return ONLY the query, nothing else."
                )
                response = ollama.generate(model=settings.OLLAMA_MODEL, prompt=expand_prompt)
                enriched = response["response"].strip().strip('"').strip("'")
                if enriched and len(enriched) < 100:
                    return enriched
            except Exception:
                pass
        return topic

    def _do_web_search(self, topic: str, step: Callable, enrich: bool = False, upload_sources: set = None):
        """Run web search, scrape, index and return chunks + sources."""
        search_query = topic
        if enrich:
            step("🔎 Enriching search query for better web results...")
            search_query = self._enrich_query_for_web(topic, upload_sources or set())
            if search_query != topic:
                step(f"   📝 Enriched query: \"{search_query}\"")

        step(f"🔍 Searching the web via DuckDuckGo...")
        self.vector_store.clear_web_documents()
        search_results = search_web(search_query)
        web_sources    = set()

        if not search_results:
            step("   ⚠️ No web results found.")
            return [], web_sources

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
                step(f"   ⚠️ Could not scrape {url}")

        step(f"📊 Semantic search across {scraped_count} source(s)...")
        web_docs = self.vector_store.query_similarity(topic, n_results=5)
        if web_docs:
            step(f"   ✅ Retrieved {len(web_docs)} relevant chunk(s) from web.")
            for doc in web_docs:
                web_sources.add(doc["metadata"].get("url", ""))
        else:
            step("   ⚠️ No relevant web chunks found.")

        return web_docs, web_sources

    def _answer_from_brain(self, topic: str, conversational: bool, step: Callable) -> str:
        history_ctx = get_recent_context()
        if conversational:
            step("💬 Answering conversationally — no retrieval needed.")
            prompt = (
                "You are a helpful AI Research Assistant.\n"
                + (f"{history_ctx}\n\n" if history_ctx else "")
                + "Reply conversationally and briefly:\n\n" + topic
            )
        else:
            step("🧠 Answering from model knowledge — no retrieval needed.")
            prompt = (
                "You are an expert AI Research Assistant.\n"
                + (f"{history_ctx}\n\n" if history_ctx else "")
                + "Answer clearly and thoroughly using your own knowledge. "
                + "Use markdown headings and bullet points.\n\nQuestion: " + topic
            )
        step("⚙️ Generating response...")
        try:
            response = ollama.generate(model=settings.OLLAMA_MODEL, prompt=prompt)
            answer   = response["response"]
            append_turn(topic, answer)
            return answer
        except Exception as e:
            return f"Error communicating with Ollama: {e}. Make sure Ollama is running."

    def run_research(
        self,
        topic: str,
        selected_file_hashes: List[str] = None,
        source_mode: Literal['auto', 'web', 'file', 'both'] = 'auto',
        on_step: Optional[Callable[[str], None]] = None,
    ) -> str:

        def step(text: str):
            print(text)
            if on_step:
                on_step(text)

        step(f"🚀 Starting research for: \"{topic}\"")
        step(f"🎛️  Source mode: {source_mode.upper()}")

        history_ctx     = get_recent_context()
        if history_ctx:
            step("🗂️ Loaded previous conversation context.")

        topic_stripped  = topic.strip()
        context_parts   = []
        upload_sources  = set()
        web_sources     = set()
        user_wants_file = bool(FILE_INTENT_PATTERNS.search(topic_stripped))

        # ── EXPLICIT MODE: web ───────────────────────────────────────────────
        if source_mode == 'web':
            step("🌐 Web-only mode — skipping file retrieval.")
            web_docs, web_sources = self._do_web_search(topic, step, enrich=True)
            if web_docs:
                block = "--- WEB SEARCH CONTEXT ---\n"
                for i, doc in enumerate(web_docs):
                    block += f"[Chunk {i+1}]\n{doc['text']}\n\n"
                context_parts.append(block)

        # ── EXPLICIT MODE: file ──────────────────────────────────────────────
        elif source_mode == 'file':
            step("📂 File-only mode — skipping web search.")
            has_uploads = self._has_uploaded_docs(selected_file_hashes or None)
            if not has_uploads:
                return "⚠️ No uploaded files found. Please upload a document first."

            if user_wants_file:
                upload_docs = self._get_all_upload_chunks(selected_file_hashes or None)
            else:
                upload_docs = self._query_uploads_semantic(
                    topic, n_results=5,
                    selected_hashes=selected_file_hashes or None
                )
                best_score = upload_docs[0]["score"] if upload_docs else 1.0
                step(f"   📊 Best semantic match score: {best_score:.3f}")
                if best_score >= FILE_RELEVANCE_THRESHOLD:
                    step(f"   ⚠️ File may not be relevant to this query (score {best_score:.3f}). Consider switching to Web mode.")

            if upload_docs:
                step(f"   📄 Retrieved {len(upload_docs)} chunk(s) from uploaded document(s).")
                block = "--- UPLOADED DOCUMENT CONTEXT ---\n"
                for i, doc in enumerate(upload_docs):
                    block += f"[Chunk {i+1}]\n{doc['text']}\n\n"
                    upload_sources.add(doc["metadata"].get("title", "Uploaded file"))
                context_parts.append(block)
            else:
                return "⚠️ No content found in uploaded files matching your query."

        # ── EXPLICIT MODE: both ──────────────────────────────────────────────
        elif source_mode == 'both':
            step("🔀 Both mode — running semantic file retrieval AND web search.")

            has_uploads = self._has_uploaded_docs(selected_file_hashes or None)
            if has_uploads:
                step("📂 Searching uploaded documents (semantic)...")
                if user_wants_file:
                    upload_docs = self._get_all_upload_chunks(selected_file_hashes or None)
                    best_score  = 0.0
                else:
                    upload_docs = self._query_uploads_semantic(
                        topic, n_results=5,
                        selected_hashes=selected_file_hashes or None
                    )
                    best_score = upload_docs[0]["score"] if upload_docs else 1.0

                step(f"   📊 Best file match score: {best_score:.3f}")

                if upload_docs and best_score < FILE_RELEVANCE_THRESHOLD:
                    step(f"   ✅ File content relevant (score {best_score:.3f}) — including in context.")
                    block = "--- UPLOADED DOCUMENT CONTEXT ---\n"
                    for i, doc in enumerate(upload_docs):
                        block += f"[Chunk {i+1}]\n{doc['text']}\n\n"
                        upload_sources.add(doc["metadata"].get("title", "Uploaded file"))
                    context_parts.append(block)
                else:
                    step(f"   ℹ️ File not relevant (score {best_score:.3f}) — skipping file, searching web only.")
            else:
                step("   ⚠️ No uploaded files — running web search only.")

            web_docs, web_sources = self._do_web_search(
                topic, step,
                enrich=len(topic.split()) <= 6,
                upload_sources=upload_sources,
            )
            if web_docs:
                block = "--- WEB SEARCH CONTEXT ---\n"
                for i, doc in enumerate(web_docs):
                    block += f"[Chunk {i+1}]\n{doc['text']}\n\n"
                context_parts.append(block)

        # ── AUTO MODE ────────────────────────────────────────────────────────
        else:
            if CONVERSATIONAL_PATTERNS.match(topic_stripped):
                return self._answer_from_brain(topic, conversational=True, step=step)

            has_selected   = bool(selected_file_hashes)
            has_uploads    = self._has_uploaded_docs(selected_file_hashes if has_selected else None)
            user_wants_web = bool(WEB_INTENT_PATTERNS.search(topic_stripped))

            # Brain shortcut — no files, no web intent, simple factual question
            if (
                not has_selected and not has_uploads
                and not user_wants_web and not user_wants_file
                and BRAIN_PATTERNS.match(topic_stripped)
            ):
                return self._answer_from_brain(topic, conversational=False, step=step)

            run_web = user_wants_web or (not has_uploads and not has_selected)

            # File retrieval
            if has_uploads:
                if user_wants_file:
                    step("📂 User asked about file — fetching all chunks...")
                    upload_docs = self._get_all_upload_chunks(selected_file_hashes or None)
                    best_score  = 0.0
                else:
                    step("📂 Searching uploaded knowledge base (semantic)...")
                    upload_docs = self._query_uploads_semantic(
                        topic, n_results=5,
                        selected_hashes=selected_file_hashes if has_selected else None
                    )
                    best_score = upload_docs[0]["score"] if upload_docs else 1.0
                    step(f"   📊 Best file match score: {best_score:.3f}")

                if best_score < FILE_RELEVANCE_THRESHOLD:
                    relevance = (
                        "highly relevant — skipping web" if best_score < FILE_SKIP_WEB_THRESHOLD
                        else "relevant — will also search web"
                    )
                    step(f"   ✅ File is {relevance} (score {best_score:.3f}).")

                    block = "--- UPLOADED DOCUMENT CONTEXT ---\n"
                    for i, doc in enumerate(upload_docs):
                        block += f"[Chunk {i+1}]\n{doc['text']}\n\n"
                        upload_sources.add(doc["metadata"].get("title", "Uploaded file"))
                    context_parts.append(block)

                    # Only skip web if file is highly relevant AND user didn't ask for web
                    if best_score >= FILE_SKIP_WEB_THRESHOLD and not user_wants_web:
                        run_web = True   # moderate relevance → also search web
                    elif best_score < FILE_SKIP_WEB_THRESHOLD and not user_wants_web:
                        run_web = False  # highly relevant → file is enough
                else:
                    step(f"   ℹ️ File not relevant to this query (score {best_score:.3f}) — searching web.")
                    run_web = True

            if run_web:
                web_docs, web_sources = self._do_web_search(
                    topic, step,
                    enrich=len(topic.split()) <= 6,
                    upload_sources=upload_sources,
                )
                if web_docs:
                    block = "--- WEB SEARCH CONTEXT ---\n"
                    for i, doc in enumerate(web_docs):
                        block += f"[Chunk {i+1}]\n{doc['text']}\n\n"
                    context_parts.append(block)

        # ── Fallback ─────────────────────────────────────────────────────────
        if not context_parts:
            step("🧠 No relevant retrieval results — falling back to model knowledge...")
            return self._answer_from_brain(topic, conversational=False, step=step)

        # ── Build prompt ─────────────────────────────────────────────────────
        step("📝 Building prompt with retrieved context...")
        combined_context = "\n".join(context_parts)

        if upload_sources and not web_sources:
            system_note = f"Answer ONLY from the UPLOADED DOCUMENT CONTEXT (source: {', '.join(upload_sources)}). Do not speculate."
        elif web_sources and not upload_sources:
            system_note = "Answer based on the WEB SEARCH CONTEXT below. Cite sources clearly. Never hallucinate."
        else:
            system_note = (
                "You have context from BOTH uploaded documents AND web search results. "
                "Use document context first where relevant, supplement with web results. "
                "Label which source each point comes from. Never hallucinate."
            )

        history_block = f"\n{history_ctx}\n" if history_ctx else ""
        full_prompt   = (
            f"{RESEARCHER_SYSTEM_PROMPT}\n\n{system_note}"
            f"{history_block}\n\nRESEARCH TOPIC: {topic}\n\n{combined_context}"
        )

        # ── Generate ─────────────────────────────────────────────────────────
        step(f"✍️  Generating report with {settings.OLLAMA_MODEL}...")
        try:
            response = ollama.generate(model=settings.OLLAMA_MODEL, prompt=full_prompt)
            step("✅ Report generated successfully.")
            report = response["response"] + "\n\n---\n### 🔗 Sources\n"
            for src in upload_sources:
                report += f"* 📄 {src} *(uploaded document)*\n"
            for src in web_sources:
                if src:
                    report += f"* 🌐 {src}\n"
            append_turn(topic, response["response"])
            return report
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"Error communicating with Ollama: {e}. Make sure Ollama is running (ollama serve)."
