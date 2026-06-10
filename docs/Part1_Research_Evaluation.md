# Part 1: AI Research & Architectural Evaluation

## 1. Executive Summary

The objective of this research is to evaluate and select the optimal technology stack for an **AI-Powered Research Assistant**. The system requires a robust Retrieval-Augmented Generation (RAG) pipeline capable of ingesting live web data, semantically chunking it, and synthesizing it into structured research reports.

After evaluating multiple Foundation Models (FMs), orchestration frameworks, and vector databases, the selected stack is **Ollama (local LLM) + FastAPI + ChromaDB**. This combination prioritises **data sovereignty, zero API cost, and offline capability** while remaining flexible enough to swap models with a single configuration change.

---

## 2. Evaluation Methodology & Core KPIs

To move beyond hype, the evaluation was grounded in the following engineering and business metrics:

1. **Context Window Depth & Recall (NIAH):** Needle-in-a-Haystack retrieval accuracy across large document inputs.
2. **Unit Economics:** Cost per inference at scale — including both API pricing and infrastructure CapEx.
3. **Inference Latency (TTFT):** Time-to-First-Token, critical for preventing application hanging during synchronous web-scrape-to-generate pipelines.
4. **Data Privacy:** Whether model inference involves sending data to third-party servers.
5. **Infrastructure Overhead:** OpEx vs. CapEx considerations for production scaling.

---

## 3. Foundation Model (LLM) Analysis

### Candidate A: Ollama — Local Open-Weight Models

- **Models evaluated:** `qwen2.5:3b`, `phi3:mini`, `llama3.1:8b`, `mistral:7b`
- **Context Window:** 8K–128K tokens (model dependent)
- **Pros:**
  - **Zero cost per inference.** No per-token charges — only the fixed cost of local hardware.
  - **Absolute data privacy.** All inference happens on-device. No data is sent to any third party — critical for proprietary business research.
  - **No API key or internet connection required** for the inference step.
  - **Model flexibility.** Swap models with a single `.env` change (`OLLAMA_MODEL=...`).
  - **Active ecosystem.** Ollama supports 100+ models including Llama, Qwen, Gemma, Mistral, Phi, and DeepSeek families.
- **Cons:**
  - Context windows are smaller than frontier cloud models (8K–128K vs. 1M tokens).
  - Quality ceiling is lower than GPT-4o or Gemini Ultra for highly complex reasoning tasks.
  - Latency is hardware-dependent — slower on consumer GPUs than cloud inference APIs.

> **🏆 Selected for this project.** For a local research agent where privacy and zero ongoing cost are priorities, Ollama provides the best balance of capability and practicality.

---

### Candidate B: OpenAI (GPT-4o / GPT-4o-mini)

- **Context Window:** 128K tokens
- **Pros:**
  - Best-in-class zero-shot reasoning and structured output reliability.
  - Massive ecosystem, integrations, and predictable JSON-mode behaviour.
- **Cons:**
  - **Cost at scale:** GPT-4o costs $2.50/1M input tokens — roughly 16x more expensive than local inference.
  - All data is sent to OpenAI servers — unsuitable for sensitive business data.
  - Requires a paid API key and internet connectivity at all times.

---

### Candidate C: Google Gemini (Flash / Pro)

- **Context Window:** Up to 1M tokens
- **Pros:**
  - Industry-leading context window — can ingest entire PDF documents or multiple web scrapes without truncation.
  - Competitive pricing at $0.15/1M input tokens (Flash tier).
- **Cons:**
  - Data is sent to Google's servers — same privacy concern as OpenAI.
  - Requires a Google Cloud account and API key management.
  - Cannot be run offline.

---

## 4. Model Comparison Summary

| Feature | Ollama (Local) | OpenAI GPT-4o | Google Gemini Flash |
|---|---|---|---|
| **Inference Cost** | Free | $2.50 / 1M tokens | $0.15 / 1M tokens |
| **Data Privacy** | ✅ 100% local | ❌ Sent to OpenAI | ❌ Sent to Google |
| **Offline Support** | ✅ Yes | ❌ No | ❌ No |
| **Context Window** | 8K–128K | 128K | 1M |
| **Setup Complexity** | Low (one `ollama pull`) | Medium (API key) | Medium (API key) |
| **Model Flexibility** | ✅ 100+ models | ❌ OpenAI only | ❌ Google only |
| **Verdict** | 🏆 Selected | Premium option | High-throughput cloud |

---

## 5. Orchestration & Framework Evaluation

The orchestration layer connects the user, the database, and the LLM.

1. **LangChain / LlamaIndex:**
   - Excellent for rapid prototyping, but heavily abstracted. In production, these frameworks introduce opacity that makes debugging prompt injection or custom timeout behaviour difficult.

2. **No-Code (n8n / Make.com):**
   - Great for simple linear workflows (email → summarise → Slack). Building dynamic conversational RAG with custom chunking algorithms is severely limited by visual node editors.

3. **Custom FastAPI (Python) — Selected:**
   - Building a custom orchestration layer with FastAPI provides raw control over the async event loop (`asyncio`). It enables precise error handling, custom chunking algorithms, and strict Pydantic payload validation — critical for a reliable research pipeline.

---

## 6. Vector Database (Semantic Memory) Evaluation

RAG systems require semantic memory to search and inject relevant facts into the LLM context.

| Database | Deployment | Best For | Verdict |
|---|---|---|---|
| **ChromaDB** | Local / Embedded | Prototypes, zero-setup, local reads | ✅ **Selected (POC Phase)** |
| **Pinecone** | Serverless Cloud | Production scaling, millions of vectors, high concurrency | Recommended for production |
| **pgvector (PostgreSQL)** | Self-hosted / Cloud | Enterprises already using SQL; hybrid search | Best long-term enterprise option |

ChromaDB was selected for the prototype due to its zero-configuration embedded deployment. It supports selective document clearing (preserving uploaded file chunks while clearing web-scraped chunks between queries), which is a key feature of the agent's multi-source RAG architecture.

---

## 7. Embedding Model Selection

Rather than using a cloud embedding API, the project uses `all-MiniLM-L6-v2` — a local sentence-transformer model loaded directly by ChromaDB's built-in embedding function. This means:

- **No embedding API cost.**
- **No data sent externally** during the indexing step.
- **Fast local inference** — the 22M parameter model embeds chunks in milliseconds on CPU.

---

## 8. Architectural Recommendation & Conclusion

Based on the research above, the prototype uses a **fully local RAG architecture**:

1. **Frontend:** React + Vite (decoupled, responsive UI)
2. **Backend API:** FastAPI (async orchestration)
3. **Semantic Storage:** ChromaDB + `all-MiniLM-L6-v2` (local embedding + retrieval)
4. **Inference Engine:** Ollama (local LLM, zero API cost)

This stack prioritises **privacy, cost-efficiency, and portability**. By avoiding cloud APIs entirely, the system can run on any developer machine, process sensitive documents without data leakage, and operate indefinitely with zero ongoing cost.
