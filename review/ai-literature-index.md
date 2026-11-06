# AI literature collection

Browse by the question you want to explore. Each source appears once, with its contribution and the notes that incorporate it. Follow the knowledge links for the explanation; chapter-end Sources blocks retain the evidence mapping and source details. Foundational papers are selected for mechanisms that remain useful, with their experimental scope retained in the notes.

- [Model computation and learning](#Model%20computation%20and%20learning)
- [Inference memory and serving](#Inference%20memory%20and%20serving)
- [Retrieval and tool-driven reasoning](#Retrieval%20and%20tool-driven%20reasoning)
- [Agent loops and accumulated improvements](#Agent%20loops%20and%20accumulated%20improvements)

## Model computation and learning

| Source and version | Contribution or reason to read | Integrated notes |
|---|---|---|
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762v7) · 2017 first published · arXiv v7 2023-08-02 | Combines multi-head attention (多头注意力), position-wise feed-forward networks (逐位置前馈网络), residual paths, and positional encoding in an encoder–decoder for translation. | [Model computation](../ai-engineering/foundations/how-llms-work.md) for QKV, FFNs, and their use in the decoder-only example. |
| [GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://aclanthology.org/2023.emnlp-main.298/) · EMNLP 2023 | Read for how sharing K/V heads changes attention and cache size, and how the paper converts multi-head checkpoints and evaluates further training. | [K/V sharing](../ai-engineering/foundations/how-llms-work.md#What%20changes%20when%20heads%20share%20K%20and%20V%3F), [serving capacity](../ai-engineering/systems/llm-serving-and-kv-cache.md). |
| [Transformer Feed-Forward Layers Are Key-Value Memories](https://aclanthology.org/2021.emnlp-main.446/) · EMNLP 2021 | Read for evidence about text-pattern associations and prediction effects in the FFNs studied, while keeping that interpretation scoped to the analyzed models. | [FFN behavior](../ai-engineering/foundations/how-llms-work.md#Transform%20each%20position%27s%20features). |
| [RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/html/2104.09864v5#S3) · First published 2021 · arXiv v5 2023-11-08 | Read for how rotating Q and K introduces relative-position dependence into their dot products. | [QKV and position](../ai-engineering/foundations/how-llms-work.md#Project%20each%20row%20into%20Q%2C%20K%2C%20and%20V). |
| [GLU Variants Improve Transformer](https://arxiv.org/html/2002.05202v1#S2) · arXiv v1 · 2020-02-12 | Read for the gated FFN computation behind SwiGLU; the paper evaluates particular Transformer variants rather than establishing a universal best activation. | [FFN gating](../ai-engineering/foundations/how-llms-work.md#Transform%20each%20position%27s%20features). |
| [Root Mean Square Layer Normalization](https://arxiv.org/abs/1910.07467v1) · arXiv v1 · 2019-10-16 | Read for how RMS-based rescaling controls a representation's scale and how it differs from centering-based normalization. | [Input normalization](../ai-engineering/foundations/how-llms-work.md#What%20enters%20the%20first%20block%3F). |
| [The Llama 3 Herd of Models](https://arxiv.org/html/2407.21783v3#S3) · 2024 · arXiv v3 2024-11-23 | Read as a concrete decoder-only architecture and training reference for RoPE, GQA, normalization, and gated FFNs. | [Model computation](../ai-engineering/foundations/how-llms-work.md), [service walkthrough](../ai-engineering/systems/from-message-to-answer.md). |
| [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751v2) · First published 2019 · arXiv v2 2020-02-14 | Read for nucleus sampling and temperature mechanics; open-ended generation experiments do not establish agent correctness. | [Token selection](../ai-engineering/foundations/how-llms-work.md#Score%20the%20vocabulary%20and%20select%20an%20ID), [choosing decoding settings](../ai-engineering/foundations/how-llms-work.md#How%20should%20an%20application%20choose%20decoding%20settings%3F). |

## Inference memory and serving

| Source and version | Contribution or reason to read | Integrated notes |
|---|---|---|
| [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180v1) · arXiv v1 · 2023-09-12 | Uses logical-to-physical KV blocks and sharing to reduce allocation waste and improve serving throughput in the evaluated workloads. | [Inference capacity](../ai-engineering/systems/llm-serving-and-kv-cache.md) for block allocation, cache reuse, and measurement. |

## Retrieval and tool-driven reasoning

| Source and version | Contribution or reason to read | Integrated notes |
|---|---|---|
| [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629v3) · 2022 first published · arXiv v3 2023-03-10 | Uses observations from task environments to adjust subsequent reasoning and actions, evaluated on specific question-answering and interactive tasks against task-specific baselines. | [Agent decision loop](../ai-engineering/agents/agent-fundamentals.md#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF) connects paper actions and observations to production tool contracts. |
| [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401v4) · 2020 first published · arXiv v4 2021-04-12 | Combines an updatable document index with a parametric generator and compares marginalizing document candidates per sequence and per token. | [Retrieval and grounded generation](../ai-engineering/rag/rag-architecture-and-implementation.md) connects the paper mechanism to evidence retrieval and answer acceptance. |

## Agent loops and accumulated improvements

| Source and version | Contribution or reason to read | Integrated notes |
|---|---|---|
| [Building agents: When to fold subagents into your main agent loop](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop) · Anthropic article · 2026-10-22 | Discusses folding specialist workflows that need shared context into one main loop with on-demand skills and tools, and when to keep independent workers. | [Orchestration](../ai-engineering/agents/orchestration-patterns.md) for structure choices; [context](../ai-engineering/context/context-engineering-principles.md) for on-demand loading and handoff loss; [evaluation](../ai-engineering/evaluation/llm-evaluation-methods.md) for migration comparisons. |
| [Scaling Discovery Requires Forgetting](https://arxiv.org/abs/2610.20563v1) · arXiv v1 · 2026-10-14 | Studies resets that clear session and candidate histories while retaining the best artifact and score in externally evaluated open-ended search. | [Context](../ai-engineering/context/context-engineering-principles.md) for retention and reset scope; [evaluation](../ai-engineering/evaluation/llm-evaluation-methods.md) for comparisons, budgets, and attribution limits. |
| [Harness²: Recursive Agent Harnessing for an Open World](https://arxiv.org/html/2610.14224v1) · arXiv v1 · 2026-10-09 | Iterates harnesses around frozen models through actual execution comparisons and accumulates retrievable improvement experience across tasks. | [Agent improvement](../ai-engineering/agents/agent-improvement-and-version-acceptance.md) for update targets and shared baselines; [context](../ai-engineering/context/context-engineering-principles.md) for experience reuse; [evaluation](../ai-engineering/evaluation/llm-evaluation-methods.md) for behavior comparisons and correctness. |
| [RSI-Anything: Unlocking Recursive Self-Improvement with World Models](https://arxiv.org/html/2610.13912v1) · arXiv v1 · 2026-10-09 | Proposes a framework that organizes recursive improvement around candidate outcome predictions, real feedback, and joint acceptance of a strategy and its predictor (预测器). | [Agent improvement](../ai-engineering/agents/agent-improvement-and-version-acceptance.md) for feedback and durable updates; [evaluation](../ai-engineering/evaluation/llm-evaluation-methods.md) for component and joint acceptance. |
| [GitSwarm: Decentralized Compounding Inference](https://arxiv.org/html/2610.04862v1) · arXiv v1 · 2026-10-04 | Uses persistent, branchable artifacts and explicit provenance so workers can reuse, verify, and combine prior work across attempts. | [Context](../ai-engineering/context/context-engineering-principles.md) for accumulated experience and provenance; [orchestration](../ai-engineering/agents/orchestration-patterns.md) for independent work and parallelism; [evaluation](../ai-engineering/evaluation/llm-evaluation-methods.md) for reuse evidence and causal benefit. |

Return to the [AI domain map](../ai-engineering/index.md) or [knowledge navigator](index.md). Read the notes together in the [AI continuous-reading document](generated/ai-engineering.md).
