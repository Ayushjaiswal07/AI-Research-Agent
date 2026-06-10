# 🚀 AI-Powered Research Agent

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Model-Ollama%20Local%20LLM-black.svg)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI research agent built with a **Retrieval-Augmented Generation (RAG)** architecture. The system autonomously searches the web, ingests and indexes content semantically, and synthesizes structured research reports — all running **100% locally** using Ollama, with no API keys or cloud costs.

---

## 📸 Screenshots

### Research Interface
![AI Research Agent UI](docs/screenshots/agent_ui.png)
> Deep Research mode with smart intent routing and multi-source RAG scoring

### Backend API Docs
![FastAPI Swagger UI](docs/screenshots/backend.png)
> Interactive Swagger UI at `http://localhost:8000/docs`

### Workflow Diagram
![System Workflow](docs/screenshots/workflow.png)
> End-to-end pipeline from user query to structured research report

---

## 📑 Table of Contents

1. [System Architecture](#-system-architecture)
2. [Quick Start Guide](#-quick-start-guide)
3. [Intent Routing](#-intent-routing)
4. [AI Research & Evaluation](#-ai-research--evaluation)
5. [Tool Selection Reasoning](#-tool-selection-reasoning)
6. [Production Scaling Strategy](#-production-scaling-strategy)

---

## 🏗️ System Architecture

The backend is decoupled into a high-performance async API and a modular AI research agent, so heavy I/O tasks (web scraping, embedding) never block the main server thread.

### Pipeline Flow

1. **API Gateway (FastAPI):** Receives typed requests, validates schemas via Pydantic.
2. **Intent Router:** Classifies the query into one of three paths — conversational, general knowledge, or full RAG — before touching any retrieval pipeline.
3. **Knowledge Acquisition:** Searches the web via DuckDuckGo, scrapes target URLs, and chunks the text.
4. **Semantic Memory (ChromaDB):** Embeds chunks using `all-MiniLM-L6-v2` (local sentence-transformer) and retrieves the top-K most relevant snippets via cosine similarity.
5. **Prompt Orchestrator:** Injects retrieved context and formatting instructions into a structured system prompt.
6. **Inference Engine (Ollama):** Generates the final structured Markdown report — fully local, no API calls.

---

## ⚙️ Quick Start Guide

### Prerequisites

- **Python 3.10+**
- **Node.js v18+ & npm**
- **Ollama** installed and running — download from [ollama.com](https://ollama.com)

### 1. Pull the model

```bash
ollama pull qwen2.5:3b
```

Or use any other compatible model (see [Model Selection](#model-selection) below).

### 2. Backend Setup

```bash
# Clone and navigate to project root
cd ai_research_agent

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set OLLAMA_MODEL to your chosen model

# Start the FastAPI server
python main.py
```

> Backend runs on `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

> Frontend runs on `http://localhost:5173`.

### 4. Environment Variables

Create a `.env` file in the project root:

```env
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 🧭 Intent Routing

The agent uses a three-path intent router so it never fires the full RAG pipeline when it isn't needed:

| Query Type | Example | Path |
|---|---|---|
| 💬 Conversational | `"hi"`, `"who are you"`, `"thanks"` | Direct LLM reply — no retrieval |
| 🧠 General Knowledge | `"what is machine learning?"` | LLM answers from training data |
| 📂 File Query | `"what's in my document?"` | Vector search over uploads only |
| 🌐 Research Query | `"latest trends in AI agents"` | Web search → scrape → RAG → LLM |
| 📂🌐 Hybrid | Topic query when uploads exist | Vector search + web search → LLM |

---

## 🔬 AI Research & Evaluation

Multiple models and frameworks were evaluated. See [`docs/Part1_Research_Evaluation.md`](docs/Part1_Research_Evaluation.md) for the full analysis.

### Model Comparison

| Feature | Ollama (Local) | OpenAI GPT-4o | Google Gemini Flash |
|---|---|---|---|
| **Cost** | Free (local compute) | $2.50 / 1M tokens | $0.15 / 1M tokens |
| **Privacy** | ✅ 100% local | ❌ Data sent to OpenAI | ❌ Data sent to Google |
| **Context Window** | 8K–128K (model dependent) | 128K | 1M |
| **Setup** | Ollama + one pull command | API key | API key |
| **Best For** | Local dev, data sovereignty | Complex reasoning | High-throughput RAG |
| **Verdict** | 🏆 **Selected** | Premium cost | No offline use |

### Model Selection

Recommended models for this project (pick one based on your hardware):

| Model | VRAM | Speed | Quality |
|---|---|---|---|
| `qwen2.5:3b` | ~2 GB | ⚡⚡⚡ Fast | Good |
| `phi3:mini` | ~2.3 GB | ⚡⚡⚡ Fast | Good reasoning |
| `llama3.1:8b` | ~5 GB (partial offload) | ⚡⚡ Medium | Best quality |

```bash
# Pull your chosen model
ollama pull qwen2.5:3b    # recommended for 4GB VRAM
ollama pull phi3:mini     # alternative
ollama pull llama3.1:8b   # best quality, needs more RAM
```

---

## 🛠️ Tool Selection Reasoning

- **Orchestration (FastAPI):** Selected over Flask/Django for native `asyncio` support. Pydantic integration enforces strict payload validation, protecting the LLM pipeline from malformed data.
- **Inference Engine (Ollama):** Runs models entirely locally — zero API cost, zero data leakage, works offline. Swap models with a single `.env` change.
- **Embeddings (`all-MiniLM-L6-v2`):** Local sentence-transformer model via ChromaDB's built-in embedding function. No separate embedding API required.
- **Vector Storage (ChromaDB):** Zero-configuration local deployment. Supports selective clearing (web chunks vs. uploaded document chunks), enabling clean query isolation between sessions.
- **Web Search (DuckDuckGo):** No API key required. The `ddgs` library provides reliable search results for the research pipeline.

---

## 🚀 Production Scaling Strategy

See [`docs/Part3_Recommendation_Report.md`](docs/Part3_Recommendation_Report.md) for the full strategy. Key upgrades for production:

- **Vector Migration:** Replace local ChromaDB with Pinecone or pgvector for multi-tenant concurrency.
- **Async Task Queue:** Move `run_research` into Celery + Redis workers. Return a `job_id` immediately instead of holding the HTTP connection open.
- **Hybrid Retrieval:** Upgrade from cosine similarity to BM25 keyword + vector semantic search with a cross-encoder re-ranker for higher context precision.
- **Model Serving:** Replace Ollama with vLLM or TGI for production-grade throughput and batching.
- **Observability:** Add LangSmith or Arize Phoenix for tracing embedding drift, token usage, and generation latency per user.

---

## 📁 Project Structure

```
ai_research_agent/
├── main.py                  # FastAPI app entry point
├── run_agent.py             # CLI runner for quick testing
├── requirements.txt
├── .env                     # Your local config (not committed)
├── src/
│   ├── agents/
│   │   ├── researcher.py    # Core agent — intent routing + RAG pipeline
│   │   └── prompts.py       # System prompts
│   ├── api/
│   │   └── routes.py        # FastAPI route handlers
│   ├── rag/
│   │   ├── vector_store.py  # ChromaDB manager (singleton)
│   │   └── chunker.py       # Text splitting with natural break detection
│   ├── tools/
│   │   ├── web_search.py    # DuckDuckGo search wrapper
│   │   └── scraper.py       # URL scraper with anti-bot headers
│   └── config.py            # Pydantic settings
├── frontend/                # React + Vite UI
├── data/
│   └── chroma_db/           # Local vector store (auto-created)
└── docs/
    ├── Part1_Research_Evaluation.md
    └── Part3_Recommendation_Report.md
```

---

*Architected and engineered by Ayush Jaiswal.*
