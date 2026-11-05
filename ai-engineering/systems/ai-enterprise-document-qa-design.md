# How do you design permission-aware enterprise document question answering? / 如何设计具备权限意识的企业文档问答？

**Core explanation / 核心解释：** Version and synchronize source documents, authenticate each caller, enforce their access before retrieval, and pass only selected evidence with source identity to generation. Validate citations and answer support, handle stale or conflicting material explicitly, and measure retrieval separately from answer quality. / 为来源文档保留版本并持续同步，认证调用者，在检索前执行其访问权限，只把筛选后的证据及来源身份交给模型生成。校验引用和答案依据，明确处理过期或冲突材料，并将检索质量与答案质量分开评估。

## Design: enterprise question answering over documents / 企业文档问答

**Clarify first:** Which user groups and repositories are in scope? How often do documents change? What is the source of truth for permissions? What answer freshness and citation behavior are required? What happens when evidence is missing or conflicting?

**Illustrative request path / 请求路径示意:**

~~~text
Document sources → parse and version → chunk and index
User query → authenticate → permission-aware retrieval
            → rank evidence → generate answer with source references
            → validate and return, or abstain/escalate
~~~

**Deep-dive topics:**

- **Ingestion and freshness:** retain source identifiers and versions; reprocess changed or deleted material and make indexing status observable.
- **Retrieval:** compare keyword, vector, or hybrid retrieval on representative questions. Tune chunking and reranking against recall, relevance, latency, and cost; there is no universal chunk size or top-k.
- **Authorization:** derive the caller's access from the trusted identity system and enforce it during retrieval, before evidence reaches the model. A prompt is not an access-control boundary.
- **Grounded answers:** carry source identifiers alongside retrieved passages. Validate that citations refer to retrieved evidence and evaluate whether claims are supported; asking for citations alone does not prove correctness.
- **Failure paths:** stale or empty results, permission-service outage, conflicting documents, malformed output, and model timeout should have explicit behavior.

**Evaluation and operations:** test retrieval and answer quality separately; include permission-boundary cases, updates and deletions, unanswerable questions, and citation checks. Monitor latency by stage, indexing freshness, retrieval metrics, answer support, abstentions, and access-control failures.

Lewis et al.'s RAG paper describes combining parametric generation with retrieved non-parametric memory; a production enterprise design must add current data ownership, authorization, and evaluation ([Lewis et al.](https://arxiv.org/abs/2005.11401)). See [RAG Architecture and Implementation / 检索增强生成](../rag/rag-architecture-and-implementation.md) for implementation detail.

### One worked budget and design choice / 一组预算推导与方案选择

Assume a fictional enterprise team has a pre-indexed policy corpus; employee questions include both natural-language policy questions and exact policy IDs; peak load is 6 queries per second; the p95 end-to-end target is 4 seconds; a hosted model API is allowed; and the team has no capacity allocated to operating GPU inference for this workload. These are interview assumptions, not observed traffic or latency.

One proposed latency budget is 0.2 s for authentication and request setup + 0.6 s for permission-aware retrieval + 2.5 s for model generation + 0.2 s for validation and response handling + 0.5 s reserved for network and queueing = 4.0 s. These are allocations to validate, not measured stage percentiles; the sum of component p95s is not itself a statistical p95 guarantee. Instrument each stage and load-test the composed service.

For a rough capacity check, use Little's Law L = λW for the mean number of requests in a stable system ([Little](https://doi.org/10.1287/opre.9.3.383)). Suppose the explicit design assumption is an admitted 6 requests/s and 1.2 s mean time spent in the model stage, including any internal wait. Then L = 6 × 1.2 = 7.2, or about 8 requests in flight in that stage. This is an average, not 8 active model slots or a replica count; queueing, bursts, and service limits need load tests with the real model, request lengths, and latency target. Size executing slots from measured service demand and the target utilization.

For these mixed exact-ID and natural-language questions, I would start with hybrid keyword and vector retrieval, enforce document permissions before context assembly, and evaluate retrieval and answer quality separately. Given the stated hosted-service permission and lack of capacity for operating GPU inference, I would put a hosted model behind that retrieval service, keep authorization outside the prompt, and bound queueing so overload does not silently consume the latency budget. If the data boundary changed, I would compare a private or self-hosted endpoint and include its operations cost; if retrieval or generation cannot fit the measured budget, I would revisit context selection, candidate ranking, and the model before relaxing answer-quality checks.

**Related design method / 相关设计方法：** [How do you turn an AI system design prompt into a defensible architecture? / 如何把 AI 系统设计题转化为有依据的架构？](./ai-system-design-interview-questions.md) covers the reusable scoping and trade-off sequence.
