# Part 3: Architecture Recommendation & Production Strategy

## 1. System Architecture Overview

The prototype implements a **Retrieval-Augmented Generation (RAG)** pipeline designed for asynchronous research synthesis. The architecture decouples the orchestration layer from the LLM inference engine, ensuring that heavy I/O tasks (web scraping, vector embedding) do not block the main server thread.

All inference runs **100% locally** via Ollama — no external API calls, no data sent to third-party servers, no ongoing cost.

### Pipeline Flow

1. **API Gateway (FastAPI):** Receives typed requests and validates schemas via Pydantic.
2. **Intent Router:** Classifies the query into one of three paths before touching any retrieval pipeline:
   - 💬 **Conversational** — answers directly from the LLM (e.g. "hi", "who are you").
   - 🧠 **General Knowledge** — answers from the LLM's training data without web search (e.g. "what is RAG?").
   - 🌐📂 **Full RAG** — web search and/or vector search over uploaded documents, then generates from retrieved context.
3. **Knowledge Acquisition:** Searches the web via DuckDuckGo, scrapes target URLs, and chunks the text.
4. **Semantic Memory (ChromaDB):** Embeds chunks using a local sentence-transformer (`all-MiniLM-L6-v2`) and retrieves the top-K most relevant snippets via cosine similarity.
5. **Prompt Orchestrator:** Injects the retrieved context and formatting instructions into a structured system prompt.
6. **Inference (Ollama):** Generates the final structured Markdown report — fully local, no API key required.

---

## 2. Tool & Model Selection Reasoning

| Component | Technology | Engineering Rationale |
|---|---|---|
| **Orchestration** | `FastAPI` | Selected over Flask/Django for native `asyncio` support and automatic OpenAPI (Swagger) documentation. Pydantic integration enforces strict payload validation, protecting the pipeline from malformed data. |
| **Inference Engine** | `Ollama` | Runs open-weight models (Qwen, Llama, Phi, Mistral) entirely on local hardware. Zero API cost, zero data leakage, works offline. Models are swappable via a single `.env` change. |
| **Embedding Model** | `all-MiniLM-L6-v2` | Local sentence-transformer loaded by ChromaDB's built-in embedding function. No embedding API required — fast CPU inference with no external data transmission. |
| **Vector Storage** | `ChromaDB` | Zero-configuration local deployment. Supports selective clearing (web chunks vs. upload chunks), enabling clean source isolation between research sessions. |
| **Web Search** | `DuckDuckGo (ddgs)` | No API key required. Provides reliable search results for the research pipeline without any account setup. |
| **Scraper** | `requests + BeautifulSoup` | Lightweight, customisable. Browser-like headers bypass basic anti-bot protections. Strips nav, footer, and sidebar noise before chunking. |

---

## 3. Intent Routing Design

A key architectural decision is the three-path intent router in `src/agents/researcher.py`. Rather than running every query through the full RAG pipeline, the router classifies intent upfront:

```
Query
  ├── Conversational?  → LLM direct reply (no retrieval)
  ├── General knowledge + no uploads? → LLM from training data (no retrieval)
  └── Everything else → Full RAG pipeline
        ├── Has uploads + file intent? → Vector search only (skip web)
        ├── Has uploads + good vector match? → Vector search only (skip web)
        └── Default → Web search + vector search → LLM
```

This avoids unnecessary web scraping for simple questions, reduces latency significantly for conversational queries, and prevents irrelevant web context from polluting answers about uploaded documents.

---

## 4. Production Scaling Strategy

The prototype is functional as a single-user local tool. Deploying to a multi-tenant production environment requires these architectural upgrades:

1. **Stateful Vector Migration:** Replace local ChromaDB with a managed cloud solution — **Pinecone** (serverless, easiest) or **pgvector** (PostgreSQL extension, best for enterprises already using SQL) — to support high-concurrency reads and writes across multiple users.

2. **Asynchronous Task Queue:** Move `run_research` into a **Celery + Redis** worker queue. API requests should immediately return a `job_id`, with the frontend polling for completion — rather than holding an HTTP connection open for 15–60 seconds during scraping and inference.

3. **Model Serving at Scale:** Replace Ollama (single-user, local) with **vLLM** or **Text Generation Inference (TGI)** for production-grade throughput, continuous batching, and quantisation support on GPU clusters.

4. **Hybrid Retrieval:** Upgrade from pure cosine similarity to a **Hybrid Search** model combining BM25 keyword search with vector semantic search, plus a cross-encoder re-ranker to maximise context precision for complex queries.

5. **Observability:** Implement tracing with **LangSmith** or **Arize Phoenix** to monitor embedding drift, token usage per user, retrieval hit rates, and generation latency over time.

---

## 5. Identified Risks & Mitigations

| Risk | Description | Mitigation |
|---|---|---|
| **Network I/O Bottlenecks** | Web scraping and LLM generation are susceptible to timeouts | Error handling with graceful fallback to model knowledge if scraping/search fails |
| **Context Dilution** | Too many retrieved chunks cause the LLM to lose focus | Retrieval capped at `n_results=5`; structured prompt separates uploaded vs. web context with clear headers |
| **Web Scraper Blocking** | Cloudflare or corporate firewalls block HTTP requests | Browser-like headers implemented; for production, use rotating proxies (BrightData) or Playwright headless browser |
| **Context Window Limits** | Local models have 8K–128K context vs. 1M for cloud models | Chunk size (1000 chars) and retrieval count (5 chunks) tuned to stay within safe context limits for small models |
| **Model Compatibility** | Newer model architectures (Gemma4, some Llama3.2 variants) crash on older GPUs via Ollama | Tested stable models: `qwen2.5:3b`, `phi3:mini`, `mistral:7b`. Documented in README. |

---

## 6. Estimated Infrastructure Cost

### Local / Self-hosted (Current Setup)

| Component | Cost |
|---|---|
| Ollama + local model | Free |
| ChromaDB (embedded) | Free |
| DuckDuckGo search | Free |
| **Total** | **$0 / month** |

### Cloud Production (10,000 Reports/Month Estimate)

Assumes migration to a hosted LLM API and cloud infrastructure for scale:

| Infrastructure | Provider | Est. Monthly Cost |
|---|---|---|
| **LLM Inference** | Self-hosted vLLM on GPU VM (e.g. Vast.ai RTX 4090) | ~$80–120 |
| **App Hosting** | AWS AppRunner / Render (auto-scaling) | ~$25–50 |
| **Vector Storage** | Pinecone Serverless (~1M vectors) | ~$30 |
| **Web Search** | Serper.dev (10K queries) | ~$10 |
| **Total OpEx** | **10,000 automated research reports** | **~$145–210 / month** |

> At 10,000 reports/month, the system achieves an estimated cost of **~$0.015–0.021 per report**, representing a substantial ROI compared to manual analyst labour.

---

## 7. Conclusion

The current architecture achieves a strong balance of capability and practicality for a local research agent:

- **Zero ongoing cost** — no API fees, all inference is local.
- **Full data privacy** — nothing leaves the user's machine.
- **Portable** — runs on any developer laptop with a GPU, no cloud account required.
- **Modular** — the intent router, vector store, scraper, and LLM are loosely coupled and independently replaceable.

The production scaling path is clear: swap ChromaDB → Pinecone, Ollama → vLLM, and add Celery workers — without changing the core agent logic.
