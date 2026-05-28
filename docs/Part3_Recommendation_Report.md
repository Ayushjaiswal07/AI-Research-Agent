# Part 3: Architecture Recommendation & Production Strategy

## 1. System Architecture Overview
The prototype implements a **Retrieval-Augmented Generation (RAG)** pipeline designed for asynchronous, high-throughput business research. 

The architecture decouples the orchestration layer from the LLM inference engine, ensuring that heavy I/O tasks (like web scraping and vector embedding) do not block the main server thread.

### The Pipeline Flow:
1. **API Gateway (FastAPI):** Receives typed requests and validates schemas.
2. **Intent Router:** Bypasses the heavy RAG pipeline for standard conversational queries to preserve API quotas.
3. **Knowledge Acquisition:** Dynamically scrapes target URLs and chunks text.
4. **Semantic Memory (ChromaDB):** Embeds chunks and retrieves the top-K most relevant snippets based on cosine similarity.
5. **Prompt Orchestrator:** Injects the retrieved context and formatting instructions into an XML-tagged system prompt.
6. **Inference (Gemini Flash):** Generates the final structured markdown report with inline citations.

---

## 2. Tool & Model Selection Reasoning

| Component | Technology | Engineering Rationale |
| :--- | :--- | :--- |
| **Orchestration** | `FastAPI` | Selected over Flask/Django for its native `asyncio` support and automatic OpenAPI (Swagger) documentation. Pydantic integration enforces strict payload validation (`min_length`), protecting upstream APIs from malformed data. |
| **Inference Engine** | `Gemini 2.0 Flash` | Selected over GPT-4o for its superior unit economics in "heavy-read" workflows. The massive context window allows the system to ingest unrefined web scrapes without complex summarization chains, drastically reducing Time-to-First-Token (TTFT). |
| **Vector Storage** | `ChromaDB` | Selected for the prototype due to its zero-configuration local deployment. It allows for rapid iteration of chunking strategies without incurring cloud database costs during the R&D phase. |

---

## 3. Production Scaling Strategy
While the prototype is functional, deploying this to an enterprise environment requires transitioning from a monolithic script to a distributed microservices architecture:

1. **Stateful Vector Migration:** Replace local `ChromaDB` with a managed cloud solution like **Pinecone** or **pgvector** to support high-concurrency multi-tenant reads and writes.
2. **Asynchronous Task Queues:** Move the `run_research` method into a **Celery worker + Redis** queue. Fast web requests should instantly return a `job_id`, allowing the frontend to poll for completion rather than holding HTTP connections open for 15+ seconds.
3. **Advanced Retrieval:** Upgrade from pure cosine similarity to a **Hybrid Search** model (BM25 Keyword + Vector Semantic) combined with a Cross-Encoder Re-ranker to maximize context precision.
4. **Observability:** Implement tracing tools like **LangSmith** or **Arize Phoenix** to monitor embedding drift, token usage per user, and generation latency.

---

## 4. Risks, Limitations & Mitigations

During prototype development, several system constraints were identified:

* **Network I/O Bottlenecks (`[WinError 10060]`):** * *Risk:* Synchronous LLM calls and web scrapers are highly susceptible to network timeouts or firewall drops.
  * *Mitigation:* The system implements exponential backoff and retry logic in the `generate_content` wrapper to gracefully handle transient network failures.
* **Context Dilution:**
  * *Risk:* Returning too many chunks from the vector database can cause the LLM to lose focus on the core instruction.
  * *Mitigation:* The Vector DB is strictly capped to return the top 5 chunks (`n_results=5`), and XML tags (`<retrieved_context>`) are used in the prompt to create hard semantic boundaries for the LLM.
* **Web Scraper Blocking:**
  * *Risk:* Standard HTTP requests are often blocked by corporate firewalls or Cloudflare.
  * *Mitigation for Production:* Integrate rotating residential proxies (e.g., BrightData) or Headless browser automation (Playwright) for robust data extraction.

---

## 5. Estimated Infrastructure Cost (Scale: 10,000 Reports/Month)
This architecture is optimized for low Operational Expenditure (OpEx). 

| Infrastructure | Purpose | Est. Monthly Cost |
| :--- | :--- | :--- |
| **Google Cloud (Gemini API)** | LLM Inference & Embedding Generation | ~$40 - $60 |
| **AWS AppRunner / Render** | Auto-scaling container hosting (API & Workers) | ~$25 - $50 |
| **Pinecone (Standard)** | Cloud Vector Database | ~$70 |
| **Proxy Service** | Unblocking web scrapers | ~$20 |
| **Total Estimated OpEx** | **End-to-end automated research** | **~$155 - $200 / month** |

*Conclusion: The system achieves an estimated cost of ~$0.02 per comprehensive research report, representing a massive ROI compared to manual analyst labor.*