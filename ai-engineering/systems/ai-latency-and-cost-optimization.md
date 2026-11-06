# How do you reduce AI application latency and cost without weakening task quality? / 如何在不损害任务质量的前提下降低 AI 应用的时延与成本？

**Core explanation / 核心解释：** First measure where end-to-end time and cost accumulate, then change one layer at a time against a fixed task-quality bar. Queueing, context assembly, retrieval, model input/output, tools, retries, and operations have different costs; token price alone is not total cost, and faster partial output is not necessarily faster completion. / 先测量端到端时间和成本分别累积在哪些环节，再以固定任务质量门槛为准逐层调整。排队、上下文组装、检索、模型输入与输出、工具、重试和运维成本各不相同；token 单价不等于总成本，更快看到部分输出也不代表更快完成。

**Key terms / 关键术语：** time to first token (TTFT) / 首 token 时延；queue time / 排队时间；response cache / 响应缓存；prompt cache / 提示缓存；continuous batching / 连续批处理；quantization / 量化；distillation / 蒸馏。

## How can you reduce latency and cost? / 如何降低时延与成本？

Measure queueing, context assembly, retrieval, model input and output, tools, and retries separately. Track latency distributions and TTFT alongside throughput, queue time, and cost per completed task. Hold the task-quality bar constant: a cheaper route that fails more often may increase retries, escalations, and human review.

The application architecture owns run status, deadlines, and recovery; see [How can a production AI run survive disconnections and worker failures? / 生产运行如何经受断连与故障？](ai-application-architecture.md). Define the success measure before comparing optimizations with [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md).

### Which optimization should you test? / 应先测试哪种优化？

- **Shorten or select context / 缩短或筛选上下文：** include relevant material and limit unnecessary history. Measure whether evidence or task quality is lost. See [Context Engineering Principles / 上下文工程原则](../context/context-engineering-principles.md).
- **Cache / 使用缓存：** exact-response or semantic response caches can avoid model work on a safe hit. Require compatible permissions, freshness, tenant, locale, and policy version. For example, “What is the refund policy in the US?” and “What is the refund policy in the EU?” can have similar embeddings but different correct answers. Similarity alone does not prove a response is reusable.
- **Route requests / 请求路由：** use a lower-cost candidate only for cases where it meets the measured quality bar. Include classifier errors, added latency, fallback frequency, and maintenance in the comparison. Candidate fit belongs to [Model Selection and Ecosystem / 模型选择与生态](../foundations/model-selection-and-ecosystem.md).
- **Inference batching / 推理批处理** — A serving engine can admit and retire sequences between decoding steps. [GPU serving capacity / GPU 推理容量](llm-serving-and-kv-cache.md) explains how that affects memory, throughput, and per-request latency. A provider's asynchronous Batch API is a job interface for requests that tolerate delayed completion. It exposes no live inference scheduling contract.
- **Quantization / 量化：** represent weights, and in some methods activations, with fewer bits. This can reduce model memory and data movement, and may improve inference speed when the hardware and kernels support the chosen format. Quantization error can affect quality, and lower precision does not guarantee faster end-to-end service; evaluate the exact model, quantizer, hardware, and workload.
- **Distillation / 蒸馏：** train a smaller student on outputs or softened targets from a larger teacher over chosen inputs. A student may reduce serving cost or latency, but can lose capabilities or fail outside the distillation set. Include teacher/data generation and evaluation in the cost, and test on held-out tasks before replacement.
- **Stream responses / 流式返回：** streaming can improve perceived responsiveness and TTFT; it does not necessarily reduce total generation time or work. The browser's treatment of partial output is covered in [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md).

Provider features such as prompt caching, batch jobs, context limits, and prices vary by model and API and can change. Verify current documentation for the exact deployment. Compare total cost, including inference, retrieval, storage, engineering, evaluation, and operations.

### A teaching calculation for cache cost / 缓存成本教学算例

Assume 1,000 model calls, each with 1,000 input tokens and 200 output tokens. For this arithmetic example only, assume uncached input costs $2 per million tokens, cached input costs $1 per million, and output costs $8 per million. These are invented teaching values, not current provider prices; ignore cache-write, storage, retrieval, and other fees.

Without caching, the token charge is:

$$
1{,}000 \times [(1{,}000 \times \$2) + (200 \times \$8)] / 1{,}000{,}000 = \$3.60.
$$

Suppose 400 calls share a 500-token prompt prefix and receive the assumed cached-input rate for that prefix. Prompt caching still processes the remaining input and generates all 200 output tokens. The assumed token charge becomes:

$$
600 \times \$0.0036 + 400 \times [\$0.0005 + \$0.001 + \$0.0016] = \$3.40.
$$

The $0.20 saving comes only from the lower rate on 400 × 500 cached input tokens. Output is still generated and billed.

An application-level response-cache hit is different: if 400 requests can safely reuse an exact, current response, those requests skip the model call, so the remaining 600 calls cost 600 × $0.0036 = $2.16 in token charges, before cache infrastructure costs. This assumes a valid exact hit; a semantic cache needs its own correctness and authorization checks.

OpenAI's [prompt caching documentation](https://developers.openai.com/api/docs/guides/prompt-caching), checked 2026-10-15, likewise describes reuse of a prompt prefix while the model still generates a new response. Supported models, rates, and cache rules are provider-specific and change.

**Sources / 来源：** OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), checked 2026-10-15. Frantar et al., [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers](https://arxiv.org/abs/2210.17323); Lin et al., [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration](https://arxiv.org/abs/2306.00978). Hinton et al., [Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531). Yu et al., [Orca: A Distributed Serving System for Transformer-Based Generative Models](https://www.usenix.org/conference/osdi22/presentation/yu), on iteration-level scheduling and selective batching. OpenAI, [Batch API](https://developers.openai.com/api/docs/guides/batch), checked 2026-10-15, documents its separate asynchronous job interface.
