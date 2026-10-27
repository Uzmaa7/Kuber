
---

## 📈 Performance Benchmarking & Optimization Report (Phase 1)

To ensure enterprise-grade efficiency, we benchmarked the system using a standardized test suite of **17 queries** comprising conversational dialogues, out-of-domain questions, and complex technical queries regarding Kubernetes (HPA, VPA, Metrics Server, and Redis Work Queues).

### 📊 Comparative Metrics Summary

| Metric | Naïve RAG (Baseline) | Optimized Agentic RAG (Phase 1) | Improvement / Delta |
| :--- | :--- | :--- | :--- |
| **Average Latency** | 11.23 sec | **9.02 sec** | **~19.7% Faster** |
| **Total Input Tokens** | 3,442 tokens | **900 tokens** | **📉 ~74% Reduction** |
| **Total Output Tokens** | 9,619 tokens | 11,659 tokens | *Richer contextual depth* |
| **Total Execution Cost** | $0.00628 | $0.00713 | *Optimized for precision* |

---

## 🛠️ Optimization Steps Implemented in Phase 1

1. **Agentic Query Routing (Planner Node):**
   * *Implementation:* Integrated a LangGraph state machine (`route_planner`) to classify incoming queries.
   * *Impact:* Conversational and out-of-domain queries (e.g., greetings, general questions) bypass the vector retrieval and document ingestion pipeline entirely, dramatically reducing input token payload sizes by **~74%**.

2. **Hybrid Search & Local Semantic Reranking:**
   * *Implementation:* Combined Qdrant Dense Vector search with Sparse BM25 keyword matching via Reciprocal Rank Fusion (RRF), coupled with local quantized ONNX cross-encoder reranking (**FlashRank**).
   * *Impact:* Filters out noisy documentation chunks and feeds only the top 5 high-precision chunks to the LLM, ensuring accurate syntax for complex YAML configurations and Kubernetes manifests.


## Phase 2: Security Rails & Out-of-Domain Guardrails (NeMo Guardrails)


### 📊 Comparative Metrics Summary

| Metric | Phase 0: Naïve RAG (Baseline) | Phase 1: Agentic Routing & Reranking | Phase 2: NeMo Guardrails Integration | Delta (Phase 0 → Phase 2) |
| :--- | :--- | :--- | :--- | :--- |
| **Average Latency** | 11.23 sec | 9.02 sec | **24.91 sec** | *Sequential gate overhead* |
| **Total Input Tokens** | 3,442 tokens | 900 tokens | **401 tokens** | **📉 ~88.3% Reduction** |
| **Total Output Tokens** | 9,619 tokens | 11,659 tokens | **5,043 tokens** | **📉 ~47.6% Reduction** |
| **Total Execution Cost** | $0.00628 | $0.00713 | **$0.00308** | **📉 ~50.9% Cost Savings** |




1. **Input/Output Safety & Off-Topic Gating:**
   * *Implementation:* Deployed NVIDIA NeMo Guardrails (`Colang` flows) powered by an intent classification gate model at the API entry point to intercept jailbreak attempts, general dialogue, and out-of-domain questions before touching the RAG graph.
2. **Cost vs. Latency Production Trade-off Analysis:**
   * *Impact on Tokens & Cost:* Early refusal of non-technical and off-topic queries slashed total input token consumption from **3,442 down to 401 tokens (~88.3% overall reduction)** and reduced total execution cost to **$0.00308 (~50.9% savings)** compared to baseline.
   * *Impact on Latency:* Introduced a sequential double-hop LLM overhead (gate evaluation prior to pipeline execution), raising average latency to **24.91 seconds**. This classic production trade-off highlights the necessity for asynchronous gate execution and semantic caching in high-throughput environments.


## Phase 3: Token & Output Control Optimization

### 📊 Comparative Metrics Summary

| Metric | Naïve RAG (Baseline) | Optimized Agentic RAG (Phase 1) | NeMo Guardrails (Phase 2) | Phase 3: Token & Output Optimized | Delta (Phase 0 → Phase 3) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Total Queries** | - | - | - | **17 Queries** | — |
| **Average Latency** | 11.23 sec | 9.02 sec | 24.91 sec | **24.85 sec** | *(Sequential gate overhead)* |
| **Total Input Tokens** | 3,442 tokens | 900 tokens | 401 tokens | **📉 299 tokens** | **📉 ~91.3% Reduction** |
| **Total Output Tokens** | 9,619 tokens | 11,659 tokens | 5,043 tokens | **📉 627 tokens** | **📉 ~93.5% Reduction** |
| **Total Execution Cost** | $0.00628 | $0.00713 | $0.00308 | **📉 $0.00042** | **📉 ~93.3% Cost Savings** |


### Phase 3: Token & Output Control Optimization 🚀
1. **LLM System Prompt Constraints:** Enforced strict conciseness rules in the responder node prompt to eliminate conversational filler and keep technical explanations under 4 sentences.
2. **Deterministic Output (`temperature=0.0`):** Locked the temperature to zero to ensure consistent, focused, and repeatable technical YAML and CLI command generations.
3. **Chunk-Specific Prompting:** Configured the responder template to extract only relevant YAML manifests or commands rather than dumping entire document histories.
4. **Hard Token Limits (`max_tokens=600`):** Set a strict output token ceiling to prevent runaway latency, infinite generations, and excessive token bills.

---

## 🚀 Future Optimization Roadmap
- **Phase 3: Semantic Caching (Redis / Portkey AI Gateway):** Cache recurring and semantically identical queries to deliver sub-second (<100ms) response times and eliminate redundant LLM calls.
- **Phase 4: Async Guardrail Execution & Gateway Fallbacks:** Parallelize gate checks and leverage Portkey AI Gateway for smart model routing and rate-limit fallbacks.



LLM Gateway (Portkey) integration ke main 5 reasons:

Semantic Caching: Dynamic/Identical queries ko cache karke sub-second response time (~200ms) serve karne aur redundant LLM calls ko eliminate karne ke liye.

Fault Tolerance & Fallbacks: Primary provider (Groq) fail hone ya down hone par automatically backup model/provider par seamless failover karne ke liye.

Rate Limiting & Cost Control: TPM/RPM limits aur runaway agent loops se bachne ke liye API usage aur execution cost ko control me rakhna.

Retries & Resilience: Rate limit (HTTP 429) ya server errors (HTTP 503) par automatic retry logic run karke pipeline drop hone se bachana.

Auditing & Observability: Direct traces, token usage, cache status (HIT/MISS), aur per-request latency monitor karne ke liye.



## Phase 4: Semantic Caching (Redis)

### 1. What We Did:
We added Redis Semantic Caching to our chatbot. This means when a user asks a question that is worded differently but means the same thing as a previous question, the system instantly grabs the saved answer instead of doing extra work.

### 2. The Problem We Faced
Slow Speed on Cached Answers: Even when the cache found a match, the speed (latency) was still taking 4 to 5 seconds.

Why? The system was running safety checks (NeMo Guardrails) before checking the cache.

### 3. How We Fixed It
Smart Short-Circuiting: We updated the code so that the Redis cache check happens first. If a match is found, it skips everything else and replies instantly

Conditional Safety Checks: Safety checks now only run if the cache misses.


### 4. The Final Results
Super Fast Speed: Response time dropped from 5 seconds down to ~2.5 seconds (and sub-second for direct cache short-circuits).

100% Accuracy: Tested on 17 different paraphrased questions with a 100% match rate.

Zero Cost: Saves money and tokens by not repeating heavy AI and database calls for similar questions.


| Metric | Phase 3: Guardrails & Token Optimized | Phase 4: Cache HIT (Redis Semantic Hit) |
| :--- | :--- | :--- |
| **Total Queries** | 17 Queries | 17 Queries |
| **Average Latency** | 24.85 sec | 2.561s |
| **Total Input Tokens** | 299 tokens | 0 tokens (Bypassed) |
| **Total Output Tokens** | 627 tokens | 0 tokens (Cached) |
| **Total Execution Cost** | $0.00042 | $0.00000 |
