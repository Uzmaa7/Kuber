
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


