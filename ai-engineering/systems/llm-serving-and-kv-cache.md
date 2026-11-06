# How do KV cache and scheduling determine LLM serving capacity? / KV 缓存与调度怎样决定模型推理容量？

**Short answer / 简答** — Prefill creates the prompt’s per-layer K/V state. Decode reuses it and appends new K/V, so active sequence length and concurrency drive memory. Use a tiled attention kernel to reduce GPU memory traffic, page the persistent cache to reduce allocation waste, and schedule prefill and decode under a latency target. Measure which limit dominates before tuning. / 预填充生成提示词在各层的 K/V。增量解码读取旧状态并追加新 K/V，因此活跃序列的长度和并发数决定显存用量。用分块计算内核减少显存读写，用分页管理持久缓存减少分配浪费，再按时延目标调度 prefill 与 decode。先测量瓶颈在哪一层，再选优化。

**Key terms / 关键术语** · prefill / 提示预填充 · decode / 增量解码 · HBM / 高带宽显存 · KV cache / 键值缓存 · continuous batching / 连续批处理 · TTFT / 首词元时延 · ITL / 词元间时延

## What stays on the GPU between decode steps? / 解码步之间哪些数据留在 GPU？

[生成机制](../foundations/how-llms-work.md)中的因果注意力解释了可缓存的条件。Prefill 把提示输入各层，写出全部提示位置的 K、V，并由最后一个位置的 logits 得到第一个输出 token。下一步把该 token 送进模型。每层为它计算新的 Q、K、V。新的 Q 对缓存里的旧 K 和当前 K 打分，再对对应 V 求加权和。在标准因果设置下，旧位置不受未来 token 影响，可以沿用旧 K/V。旧 Q 已经用于旧位置自己的更新；后续位置的 attention 不读取它。每层所需的投影来自该层自己的输入与权重，因此要存各层的 K/V。

| 阶段 | 注意力典型形状，单条请求 | 常见成本 |
| --- | --- | --- |
| Prefill $T$ 个提示 token | 每个 query 头处理 $T$ 个 query 和 $T$ 个 key，带因果掩码 | 大量投影与 FFN 矩阵乘法，长序列的全量注意力计算和内存流量 |
| 带缓存的单步 decode | 每个 query 头只有 1 个 query，对长度 $C+1$ 的历史加当前 key/value 做注意力 | 读取模型权重和历史 K/V，追加当前 token 的 K/V。长前缀增大读取量，并发改变权重摊销和硬件利用率 |

这里 $C$ 是这一轮之前已存的长度。对全量 dense attention，decode 单步在序列维上仍随历史长度增长。缓存避免重复为旧位置做投影和前向，不能免掉这一步对旧 K/V 的读取。Prefill 通常偏计算，低批量 decode 常受显存带宽限制，具体取决于模型、并发、长度、精度与硬件。 [Hugging Face Transformers 缓存机制](https://huggingface.co/docs/transformers/main/en/cache_explanation) · [Sarathi-Serve §§2–4](https://arxiv.org/abs/2403.02310)

## Estimate memory before admitting requests / 先估显存，再决定并发

对每层采用相同 K/V 形状、K 和 V 每元素占同样字节的普通全量注意力模型，单条序列的 KV 载荷约为

$$
\text{bytes} = 2 \cdot L \cdot T \cdot H_{kv} \cdot d_h \cdot b.
$$

$L$ 是层数，$T$ 是当前缓存长度，$H_{kv}$ 是实际存储的 KV 头数，$d_h$ 是头宽，$b$ 是每元素字节数。最前面的 2 对应 K 和 V。用 32 层、8 个 KV 头、头宽 128、BF16（2 bytes）的示例，得到 **128 KiB/token**。缓存到 8,192 token 时每条序列是 **1 GiB**，32 条同长度且没有前缀共享的序列就需要 **32 GiB** 的 KV 载荷。权重、临时激活、块尾空位和调度余量另算。张量并行可能拆分或复制部分状态，单卡预算应按实际分片和测量核对。

GQA 从模型结构上减少要存的 K/V 头。KV 量化从存储表示上减少每个元素的字节数，两者可以同时存在。KV 量化还涉及缩放参数、精度损失和内核支持，不能把存储比直接当吞吐比。滑动窗口、混合状态或潜变量注意力的持久状态不同，应按层核算。 [GQA §2](https://aclanthology.org/2023.emnlp-main.298/) · [KIVI §3](https://arxiv.org/abs/2402.02750) · [vLLM KV cache 配置](https://docs.vllm.ai/en/latest/api/vllm/config/cache/)

如果权重本身都放不进一张卡，分页只能减少缓存浪费。先比较能达到质量门槛的权重量化和多卡切分。**Tensor parallelism / 张量并行** 把同层的矩阵或注意力头分给多卡，层内需要交换或汇总结果。**Pipeline parallelism / 流水线并行** 把不同层放到不同卡上，阶段间传递激活，流水线未填满时会有空转。把模型装下以后，再按每卡的权重、KV 和临时缓冲预算接纳序列。分片策略要考虑互连带宽和 KV 头在各卡上的实际放置。 [vLLM 并行与扩展](https://docs.vllm.ai/en/latest/serving/parallelism_scaling/)

## Separate kernel work from cache allocation / 区分内核计算和缓存分配

**FlashAttention** 将 Q/K/V 分块，维护可增量合并的 softmax 统计量，避免把完整注意力分数矩阵写入 HBM。它针对一次 attention 运算的读写和临时显存，使用精确 dense attention 算法（浮点舍入可不同），也仍计算有效位置对。FlashAttention-4 进一步针对 Blackwell 的异步矩阵乘与流水线重叠优化，说明内核选择要看硬件和形状。 [FlashAttention §3](https://arxiv.org/abs/2205.14135) · [FlashAttention-4，2026](https://arxiv.org/abs/2603.05451)

**PagedAttention** 管理跨解码步骤持久存在的 KV 状态。借鉴操作系统分页，每个请求的逻辑 KV 块按 token 顺序增长，块表把它们映射到可不连续的显存物理块。支持这种布局的 attention 内核按表访问历史 K/V，服务端按需申请块。原论文 §4.3 的例子是每块四个 token，七个提示 token 分别使用物理块 7 和 1，后者还剩一格。下一次 decode 填这一格，再往后增长才需要申请新的块。请求完成后可归还块，共享前缀可引用同一份块；若两个分支要向同一个共享块写入不同内容，写时复制（copy-on-write）隔离这些修改。

~~~mermaid
flowchart LR
    L0["Logical block 0 · token 1–4"] --> P7["Physical block 7 · full"]
    L1["Logical block 1 · token 5–7"] --> P1["Physical block 1 · one free slot"]
    L2["Logical block 2 · when token 9 is processed"] -.-> P3["Another physical block"]
~~~

每个请求的最后一块仍可能有空位，块表与间接访问也有成本。好处是按实际长度增长，不必为每条请求预留连续的最大序列区。更多请求可以同时驻留并参与批处理。原论文报告的是其 2023 年工作负载和对照系统上的吞吐量与时延。其独立注意力内核的微基准也测到了额外延迟。现代引擎的分页思想仍可用，具体计算后端按模型、卡与引擎版本选择。vLLM 将原 CUDA 内核的设计页标为历史说明。 [Kwon et al., arXiv v1，§§4.2–4.5、§6](https://arxiv.org/html/2309.06180v1) · [§7.1、图 18(a)](https://arxiv.org/html/2309.06180v1#S7.SS1) · [vLLM 原 PagedAttention 内核说明](https://docs.vllm.ai/en/latest/design/paged_attention/)

## Tune the stage that misses its target / 优先调超出目标的阶段

| 观察到的限制 | 优先试什么 | 验证边界 |
| --- | --- | --- |
| 请求已到但 GPU 尚未开始工作 | 分开测排队、输入组装、分词和传输 | 只有分词确实占关键路径时，再换 tokenizer 后端或提高 CPU 处理能力。保持相同 token 序列和特殊词元规则。 |
| 冷请求的长 prompt 首 token 慢 | 用支持当前卡和模型的内核，减少无用输入，比较长 prefill 分块预算 | 记录 TTFT 和排队时间。把 prefill 切块可以让活跃 decode 插入，长 prompt 自己可能等更久。 |
| 重复的长 prompt 首 token 慢 | 让稳定的聊天模板或文档放在共同前缀，用引擎的 prefix cache | 检查复用 token 数和命中率。只复用语义上相同还不够，缓存要匹配实际 token 序列和模型状态。 |
| 活跃序列经常碰显存上限 | 先限制最大活跃长度和并发，再试支持的 KV 精度、合适的模型或更多设备 | 跟踪实际 KV 占用、抢占与重算。CPU offload 可用更慢的传输换容量，测长请求的尾部时延。 |
| 短请求吞吐低，GPU 利用不足 | 连续批处理在迭代之间补进新请求并移除已完成请求 | 同时观察排队和 p95 首 token，扩大批次也可能让单条请求等更久。 |
| Decode 的词元间隔过长 | 按输出长度、活跃序列数分桶。测带宽，再比较 KV 或权重量化、受支持的推测解码 | 推测解码先提议一批 token 再由目标模型验证。收益取决于接受率、批次和验证成本，需对质量与延迟共同回归。 |

vLLM V1 启用 chunked prefill 后把大 prefill 切成小块、与 decode 混合调度，并优先处理已排队的 decode。其 token 预算影响 TTFT 和词元间隔，参数应按服务流量测试。vLLM 的跨请求 prefix cache 用已完成块及其前缀身份做复用，适配器、多模态内容和租户隔离都要与部署一致。可使用独立缓存范围或引擎支持的租户盐值隔离共享。跨请求命中减少 prefill 工作，仍要生成新结果。应用层的响应缓存是另一种优化，命中后可能跳过整个模型调用。文档核对于 2026-11-06。 [vLLM Optimization and Tuning](https://docs.vllm.ai/en/stable/configuration/optimization/#chunked-prefill) · [vLLM v0.25.0 Prefix Caching](https://docs.vllm.ai/en/v0.25.0/design/prefix_caching/) · [vLLM Speculative Decoding](https://docs.vllm.ai/en/latest/features/speculative_decoding/)

若分块后长 prefill 仍影响 decode 时延，可以评估预填充与解码分池（prefill/decode disaggregation）。分池可以独立调整两边容量，但每条请求的 KV 状态要从 prefill worker 传给 decode worker。把传输与排队纳入 TTFT 和吞吐测试。DistServe 的收益来自论文测试的请求分布、互连与时延目标。 [DistServe](https://arxiv.org/abs/2401.09670)

做一组固定流量回放。记录模型版本、精度、GPU、输入和输出长度分布、并发与到达速率、冷暖缓存比例。比较 **TTFT**（请求到首词元）、**ITL**（输出词元之间的间隔）、端到端 p95、吞吐和满足时延目标的请求数。能处理更多请求但超出交互时延的批次没有解决交互负载的问题。测量由 [vLLM Benchmark CLI](https://docs.vllm.ai/en/latest/benchmarking/cli/) 示例和[应用级时延与成本](ai-latency-and-cost-optimization.md)分别覆盖服务内和端到端两层。
