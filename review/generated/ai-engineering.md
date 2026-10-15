# AI Engineering

> Generated from the [ai-engineering reading map](../../ai-engineering/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. How LLMs Work / 大语言模型如何工作

### How LLMs Work / 大语言模型如何工作

**Core explanation / 核心解释：** An autoregressive text-generating language model processes token IDs and repeatedly predicts a distribution for the next token. Many widely used generators use a Transformer decoder with causal self-attention, but model families differ in architecture, tokenizer, training, and decoding API. / 自回归文本生成模型把文本转换为 token ID，并反复预测下一个 token 的概率分布。许多常见生成模型使用带因果自注意力的 Transformer 解码器，但不同模型的结构、分词器、训练方式和解码接口各不相同。

**30-second answer / 30 秒回答**

- **English:** A tokenizer maps text to model-specific tokens. A causal language model uses the prompt and generated prefix to produce next-token scores; a decoding rule selects the next token, which is appended and processed again. The Transformer is a common architecture, while its exact blocks, position method, and serving optimizations vary.
- **中文：** 分词器把文本映射为特定模型的 token。因果语言模型根据提示和已生成前缀计算下一个 token 的分数，再由解码策略选出 token 并追加到序列中。Transformer 是常见架构，但具体模块、位置编码和服务端优化会因模型而异。

**Key terms / 关键术语：** token / 词元；tokenizer / 分词器；autoregressive / 自回归；causal mask / 因果掩码；logit / 未归一化分数；decoding / 解码；context window / 上下文窗口。

#### What is a token? / 什么是 token？

A tokenizer converts text into a sequence of model-specific units and their IDs. A unit can correspond to a whole word, part of a word, bytes, or another learned piece; whitespace and punctuation may be included in a token. The model's input is not a universal word vocabulary, and different tokenizers can split the same text differently.

#### How does BPE build subword tokens? / BPE 如何构建子词 token？

Byte pair encoding (BPE) is one family of subword tokenization methods, not a rule used by every tokenizer. In a common training procedure, text is represented as basic symbols, adjacent symbol pairs are counted, and frequent pairs are merged iteratively; the learned merge sequence builds a vocabulary that includes multi-symbol pieces. Exact variants differ, including whether the basic symbols are bytes or characters.

At encoding time, the tokenizer starts from the model's basic symbols and applies learned merge priorities to the input before mapping resulting pieces to IDs. A rare word can therefore be represented as several learned pieces rather than an unknown whole word. This is a model-specific encoding procedure; merge ranks, vocabulary, and token boundaries differ across tokenizers. See Sennrich et al. for a BPE-based subword method in machine translation.

**Concrete example / 具体例子。** With the cl100k_base encoding in tiktoken 0.12.0, the text “The transformer architecture revolutionized NLP.” becomes the token sequence [“The”, “ transformer”, “ architecture”, “ revolution”, “ized”, “ N”, “LP”, “.”] (8 tokens). This is one encoding's result, not a promise about every current model or the full serialized API request. Exact counts can also include message structure, tools, images, or other inputs; use the target model's tokenizer or token-counting API when the count matters. [OpenAI's token guide](https://developers.openai.com/api/docs/concepts) gives a rough English estimate, but it is not a substitute for counting the actual input.

#### Autoregressive generation and masked language models / 自回归生成与掩码语言模型

| Objective | What the model learns | Typical use |
|---|---|---|
| **Autoregressive / 自回归** | Predict the next token from preceding tokens, usually with a causal attention mask during training. | Left-to-right text generation and completion. |
| **Masked language modeling / 掩码语言建模** | Predict selected masked tokens using surrounding left and right context. | Bidirectional text representations and downstream understanding tasks. |

BERT is a well-known bidirectional masked-language model. It is not trained as a standard left-to-right next-token generator, but “cannot generate text” is too absolute: Wang and Cho formulate BERT as a Markov random field language model and describe a sampling procedure for generating sentences. That is an adapted procedure, not ordinary left-to-right decoding. Encoder-decoder models are another common design when input and output are distinct sequences, such as translation. [BERT](https://arxiv.org/abs/1810.04805); [Wang and Cho, BERT as a Markov random field language model](https://arxiv.org/abs/1902.04094); [Transformer](https://arxiv.org/abs/1706.03762).

#### What happens inside a Transformer block? / Transformer block 内部如何工作？

In the original Transformer, an attention sublayer forms queries, keys, and values from the token representations. A scaled dot product between a query and keys becomes weights after softmax; the model uses those weights to combine the corresponding values. A decoder's causal mask prevents a position from attending to later tokens.

Multi-head attention repeats attention with distinct learned projections, concatenates the head outputs, then projects the combined representation. This lets the block combine information from different learned representation subspaces; a head should not automatically be read as a human-defined concept.

Attention mixes information across positions. Position encodings supply order information. A position-wise feed-forward sublayer then transforms each position separately with shared weights. In the original architecture, residual connections wrap each sublayer and layer normalization follows it. Later Transformer variants change these details, so this is a common mechanism, not a specification for every model. See [Attention Is All You Need, §§3.1–3.5](https://arxiv.org/html/1706.03762v7).

#### How one generated token is produced / 如何生成一个 token

A simplified decoder-only generation pass is:

1. Encode the prompt as token IDs and map them to representations.
2. Process the sequence through attention and feed-forward blocks. Position information and a causal mask let each position use permitted context.
3. Project the final-position representation to **logits**, one score per candidate next token.
4. Convert scores into a distribution and select a token, for example by greedy selection or sampling.
5. Append the token and repeat until a stop condition, output limit, or another runtime condition is reached.

This is an explanatory sketch, not a specification of every model. Implementations may use different attention layouts, position schemes, normalization, output constraints, caching, or non-text input paths. A text token sequence also does not imply that images or audio are handled as ordinary words.

For standard dense self-attention, forming pairwise attention scores over a sequence of length n has quadratic dependence on n. This describes that operation, not necessarily the total latency or cost of a deployed model: feed-forward work, attention variants, hardware, batching, and caching also matter.

#### Temperature, top-k, and top-p / 温度、top-k 与 top-p

Given next-token logits z_i, temperature T > 0 changes their sharpness before softmax:

$$
P(i) = \frac{\exp(z_i/T)}{\sum_j \exp(z_j/T)}
$$

Lower T concentrates probability on high-scoring tokens; higher T flattens it. In the idealized limit as T approaches zero, selection approaches argmax, but API support and reproducibility behavior are provider- and model-specific.

- **Top-k / 前 k 项：** keep only the k highest-probability candidates, then decode from them.
- **Top-p / nucleus sampling / 核采样：** keep the smallest ranked set whose cumulative probability reaches p, then decode from that set.
- **Greedy decoding / 贪心解码：** choose the highest-scoring candidate instead of sampling.

These controls change decoding behavior; none makes an answer more factual. Parameter availability and interactions vary. For example, the OpenAI Responses API reference checked on 2026-10-15 documents temperature and top_p and recommends changing one rather than both for that API; do not assume another provider exposes the same parameters. [Nucleus sampling paper](https://arxiv.org/abs/1904.09751), [OpenAI Responses API reference](https://developers.openai.com/api/reference/resources/responses/methods/create).

#### Related notes / 相关笔记

- [Model Selection and Ecosystem / 模型选择与生态](#2.%20Model%20Selection%20and%20Ecosystem%20/%20%E6%A8%A1%E5%9E%8B%E9%80%89%E6%8B%A9%E4%B8%8E%E7%94%9F%E6%80%81) compares candidates against task requirements.
- [Context Engineering Principles / 上下文工程原则](#5.%20Context%20Engineering%20Principles%20/%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B%E5%8E%9F%E5%88%99) explains context limits, token cost, and prompt caching.

#### Sources / 来源

- Vaswani et al., [Attention Is All You Need](https://arxiv.org/abs/1706.03762).
- Devlin et al., [BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://arxiv.org/abs/1810.04805).
- Wang and Cho, [BERT has a Mouth, and It Must Speak: BERT as a Markov Random Field Language Model](https://arxiv.org/abs/1902.04094).
- Sennrich et al., [Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909).
- OpenAI, [Key concepts: Tokens](https://developers.openai.com/api/docs/concepts), checked 2026-10-15. The tokenization above was reproduced locally with Python 3.11.13 and tiktoken 0.12.0 using cl100k_base.
## 2. Model Selection and Ecosystem / 模型选择与生态

### Model Selection and Ecosystem / 模型选择与生态

**Core explanation / 核心解释：** Select a model for a defined task and deployment context, then compare candidates on representative examples and operating constraints. Model names, rankings, context limits, supported inputs, and prices change; a public benchmark or provider label is evidence to investigate, not a permanent selection rule. / 先明确任务和部署条件，再用有代表性的样本和运行约束比较候选模型。模型名称、排名、上下文限制、输入能力和价格都会变化；公开基准或供应商标签可以帮助缩小范围，但不能作为长期固定的选择规则。

**30-second answer / 30 秒回答**

- **English:** I define the quality bar and hard constraints first, then compare a small set of eligible models on the same held-out task set. I measure task quality, latency, total cost, tool or format reliability, and data-handling requirements. I choose the least costly option that meets the agreed bar, and re-evaluate routing or fallbacks against the same criteria.
- **中文：** 我先定义质量要求和硬性约束，再用同一组保留样本比较少量候选模型。我会测量任务质量、时延、总成本、工具或格式可靠性以及数据处理要求，选择能够达到约定标准且总成本合适的模型，并用相同标准评估路由和回退方案。

#### Start with the task contract / 从任务要求开始

Record what a successful result must do, what errors matter, and which operating conditions are fixed. Compare candidates on the same prompt, data, tools, and evaluation protocol where possible.

| Dimension | Questions to answer |
|---|---|
| **Task quality / 任务质量** | What counts as correct or useful? Which edge cases and refusal cases matter? |
| **Latency and availability / 时延与可用性** | Is the constraint about time to first response, full completion, or uptime? Which workload and region are representative? |
| **Cost / 成本** | Include input and output usage, retries, retrieval, hosting, support, and evaluation—not just one token rate. |
| **Inputs and outputs / 输入与输出** | Does the task require text, image, audio, or other modalities? Are schemas or tools supported for this exact model and API? |
| **Data handling / 数据处理** | What does the contract, configuration, retention policy, and deployment boundary allow? “Hosted” or “open-weight” alone does not answer this. |
| **Operations / 运维** | Who owns scaling, updates, monitoring, security patches, and incident response? |

Public benchmarks can help generate a shortlist when their task and protocol are relevant. They do not establish performance on a different prompt, data distribution, API configuration, or deployment. Keep an application-specific held-out set and report its sample scope and uncertainty; see [LLM Evaluation Methods / 大语言模型评估方法](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95).

#### Model tiers are shorthand, not a catalog / 模型档位只是简称，不是目录

Teams sometimes use labels such as **frontier**, **balanced**, and **fast** to describe rough cost/latency/capability tradeoffs within a provider's current catalog. Those labels are not shared standards: a “fast” model can be the better choice on a narrow task, and a “frontier” label does not prove quality on yours. Avoid copying an undated model list or treating a prior ranking as a current fact. Verify the exact model ID, supported API features, context limit, and pricing in the provider's current documentation when making a real selection.

#### Hosted API, open-weight, or hybrid? / 托管 API、开放权重还是混合部署？

| Approach | Potential advantages | Costs and constraints to compare |
|---|---|---|
| **Hosted API / 托管 API** | Quick access to managed inference and model updates; less serving infrastructure to operate. | Data flows and retention depend on the provider's terms and configuration; usage, rate limits, availability, and model lifecycle are provider-controlled. |
| **Open-weight deployment / 开放权重部署** | More control over serving location, model version, and infrastructure choices. | A weight license is not automatically an open-source license or permission for every use. The operator owns hardware, serving, security, scaling, and updates. |
| **Hybrid / 混合部署** | Different models or environments can serve distinct workload classes. | Adds routing, evaluation, observability, policy consistency, and failure paths across systems. |

Do not pick a hosting pattern from API spend alone. A useful estimate is:

$$
\text{total cost} \approx \text{inference usage} + \text{compute and storage} + \text{engineering and operations} + \text{evaluation and risk controls}
$$

Compare the same workload, quality target, peak traffic, and data constraints. A provider API may suit rapid iteration; self-hosting may suit a real data-control or workload need; edge deployment can help when offline operation or device constraints dominate. The break-even point depends on the actual workload and people costs.

#### Route by measured need / 按实测需求路由

Routing can send simple, low-risk requests to a cheaper model and reserve a more capable option for cases that benefit from it. First measure whether the router's errors, added latency, and maintenance are outweighed by the savings. Use a task-relevant fallback when routing confidence is insufficient, and ensure high-impact operations still pass application-side authorization. Do not label “classification,” “reasoning,” or “extraction” as automatically easy or hard across all models.

#### Multimodal capability / 多模态能力

“Multimodal” does not specify which input or output a model supports or how well it handles a task. Test the actual modality and input shape—such as a chart, scanned document, spoken utterance, or video sample—under the target API. Check model documentation for supported formats, limits, and feature combinations at the time of deployment.

#### Related notes / 相关笔记

- [AI Application Architecture / AI应用架构](#13.%20AI%20Application%20Architecture%20/%20AI%E5%BA%94%E7%94%A8%E6%9E%B6%E6%9E%84) covers routing, cost, monitoring, and deployment choices.
- [Context Engineering Principles / 上下文工程原则](#5.%20Context%20Engineering%20Principles%20/%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B%E5%8E%9F%E5%88%99) covers token budgets and provider-specific prompt caching.
- [Fine-tuning Strategies / 微调策略](#11.%20Fine-tuning%20Strategies%20/%20%E5%BE%AE%E8%B0%83%E7%AD%96%E7%95%A5) distinguishes behavior adaptation from maintained external knowledge.
- [RAG Architecture and Implementation / 检索增强生成](#6.%20Retrieval-Augmented%20Generation%20%28RAG%29%20/%20%E6%A3%80%E7%B4%A2%E5%A2%9E%E5%BC%BA%E7%94%9F%E6%88%90) covers current or access-controlled external evidence.

#### Sources / 来源

- OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), checked 2026-10-15. Its guidance treats prompting, context, fine-tuning, and evaluation as task-specific optimization levers rather than a universal linear ladder.
- For current OpenAI model IDs and feature support, consult the changing [Models documentation](https://developers.openai.com/api/docs/models), checked 2026-10-15.
## 3. Prompt Engineering Fundamentals / 提示工程基础

### Prompt Engineering Fundamentals / 提示工程基础

**Core explanation / 核心解释：** A useful prompt makes the task, necessary context, constraints, and expected output clear. Add examples or structure when they address a measured failure. Prompt text can guide model behavior, but it cannot enforce access control, guarantee factual accuracy, or replace validation in the application. / 有效提示词要清楚说明任务、必要背景、约束和输出要求。只有在它们能解决实测问题时，才增加示例或结构。提示词能引导模型，但不能执行访问控制、保证事实正确，也不能替代应用校验。

**30-second answer / 30 秒回答**

- **English:** I write instructions for a capable reader who does not know my application’s unstated rules. I provide relevant context, define what success and uncertainty look like, and specify the output contract. I test the prompt on representative and boundary cases; permissions and business rules remain enforced by code.
- **中文：** 我会把提示词写给一位聪明但不了解应用隐含规则的读者，补充必要背景，说明成功条件、不确定时的处理方式和输出约定，再用有代表性和边界样本评估。权限与业务规则仍由代码执行。

**Key terms / 关键术语：** instruction / 指令；context / 上下文；few-shot example / 少样本示例；output contract / 输出约定；structured output / 结构化输出；validation / 校验。

#### The “capable intern” heuristic / “能干的实习生”启发式

Treat the model as capable of using the information and tools actually supplied, but unaware of unstated product rules, source freshness, user permissions, or the format expected by a downstream system. State those requirements explicitly when they matter.

| Vague request | More useful instruction |
|---|---|
| “Handle the refund.” | “Look up the sample order, check the current refund policy, and explain the next step. The application must authorize any refund action before execution.” |
| “Classify the ticket.” | “Choose billing, technical, or general. If the message does not contain enough evidence, return needs_review.” |
| “Summarize the document.” | “Return three bullets about the decisions and open questions. Do not add claims absent from the supplied document.” |

These examples illustrate clarity; they do not imply that a prompt can verify an order, authorize a refund, or make a summary factually correct. The runtime must perform those checks.

#### A practical prompt checklist / 提示词检查清单

Include only what helps this task:

1. **Goal / 目标：** State the requested result and audience.
2. **Relevant context / 相关背景：** Supply rules, terminology, source material, or assumptions the model cannot infer.
3. **Inputs / 输入：** Identify the content to transform and delimit untrusted source text.
4. **Constraints / 约束：** Explain required coverage, exclusions, uncertainty handling, and what should trigger a question or handoff.
5. **Examples / 示例：** Add aligned positive, negative, or edge examples when they reduce ambiguity.
6. **Output contract / 输出约定：** Specify fields, format, length, language, and validation expectations.
7. **Tools and side effects / 工具与副作用：** Explain intended tool use, while the application independently enforces permissions and business conditions.

This list is an organizing aid, not a universal seven-layer prompt architecture. Some APIs distinguish system, developer, and user messages; use the roles and precedence defined by the exact API. Put dynamic data in the request context rather than hard-coding user records in reusable instructions.

#### Make constraints and examples useful / 让约束和示例真正有用

“Be concise” may be sufficient for a simple chat. A downstream parser may need a precise schema, while a support response may need an uncertainty path. More text is not automatically better: conflicting examples, repeated rules, or irrelevant context can hurt.

Use an example that demonstrates the intended boundary, not only the easiest typical input. If examples and instructions disagree, the model may follow the wrong pattern. Keep examples synthetic and avoid real customer records or secrets.

#### Structured output / 结构化输出

For machine-consumed output, prefer an API-supported schema-constrained mode when it fits the task. In the OpenAI API documentation checked on 2026-10-15, Structured Outputs supports schema adherence for supported schemas and models; JSON mode guarantees valid JSON syntax but not adherence to an application schema. Refusals, incomplete responses, unsupported schema features, and semantic errors still need handling. Schema conformance does not prove that a field is true, authorized, or safe to execute. If the chosen API cannot enforce the schema, parse, validate, and use a bounded retry or explicit failure path.

For human-readable output, headings, bullets, XML tags, or code fences can make sections easier to interpret. Delimiters help organize content; they are not a security boundary and do not guarantee valid machine output.

**Small output contract / 简单输出约定:**

~~~json
{
  "summary": "A short account of the supplied text",
  "category": "billing",
  "needs_review": false
}
~~~

Application code should check allowed categories and required fields, and verify any consequential claim against its source.

#### Optional organization pattern / 可选组织方式

Some teams group a long instruction by general-to-specific concerns. The following is a checklist, not a standard that every prompt needs:

| Section | What it contains |
|---|---|
| **Role and task context / 角色与任务背景** | Work setting and goal. |
| **Behavior / 行为** | Tone and response style. |
| **Tool guidance / 工具说明** | Intended use and limits of available tools. |
| **Procedure / 流程** | Steps that are useful to explain to the model. |
| **Output / 输出** | Format and length. |
| **Safety reminders / 安全提醒** | Human-readable reminders; code still enforces authorization and stop conditions. |
| **Request-specific context / 本轮背景** | Current task data and state, supplied only when needed. |

Do not put real names, ticket numbers, secrets, or private histories in a reusable prompt. Use a synthetic record when illustrating the format.

#### Related notes / 相关笔记

- [Advanced Prompting Techniques / 高级提示技巧](#4.%20Advanced%20Prompting%20Techniques%20/%20%E9%AB%98%E7%BA%A7%E6%8F%90%E7%A4%BA%E6%8A%80%E5%B7%A7) covers few-shot examples, reasoning cues, self-consistency, and workflows.
- [Context Engineering Principles / 上下文工程原则](#5.%20Context%20Engineering%20Principles%20/%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B%E5%8E%9F%E5%88%99) explains how to select and update the information for each inference.
- [AI Safety in Production / 生产环境中的 AI 安全](#12.%20AI%20Safety%20in%20Production%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84AI%E5%AE%89%E5%85%A8) explains why prompts cannot replace runtime authorization.

#### Sources / 来源

- OpenAI, [Model optimization: write effective prompts](https://developers.openai.com/api/docs/guides/model-optimization#write-effective-prompts), checked 2026-10-15.
- OpenAI, [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs), checked 2026-10-15. API behavior and supported schema features can change.
## 4. Advanced Prompting Techniques / 高级提示技巧

### Advanced Prompting Techniques / 高级提示技巧

**Core explanation / 核心解释：** Few-shot examples, reasoning prompts, self-consistency, tool loops, prompt chains, and prompt generation are optional methods for particular failure modes. They add tokens, calls, or control-flow complexity, so compare them with a simpler prompt and application-side checks on representative cases. Published results establish benefits only for the evaluated tasks and setups, not a general performance guarantee. / 少样本示例、推理提示、自一致性、工具循环、提示词链和提示词生成都是针对特定失败模式的可选方法。它们会增加 token、调用或控制流复杂度，因此应在有代表性的样本上与简单提示和应用校验做比较。论文结果只说明其评估任务和设置下的效果，不构成普遍性能保证。

**Key terms / 关键术语：** zero-shot / 零样本；few-shot / 少样本；chain-of-thought (CoT) / 思维链；self-consistency / 自一致性；ReAct / 推理与行动；prompt chaining / 提示词链；meta-prompting / 元提示。

#### When should you use few-shot vs. zero-shot prompting? / 何时使用少样本或零样本提示？

Start with a clear zero-shot instruction for a simple, well-defined task. Add a few examples when they resolve ambiguity, demonstrate a non-obvious label boundary, or show a required output format. Keep examples representative and include meaningful edge cases. More examples can consume context and can also bias the model toward an accidental pattern.

**Zero-shot / 零样本:**

~~~text
Classify the sentiment as positive, negative, or neutral.
Review: "The product arrived late, but the quality exceeded expectations."
Return one label.
~~~

**Few-shot / 少样本:**

~~~text
Classify each review as positive, negative, or neutral.
"Terrible experience, never buying again." → negative
"Exactly what I needed. Fast shipping." → positive
"It's okay. Nothing special." → neutral
"The product arrived late, but the quality exceeded expectations." →
~~~

For extraction, examples can demonstrate how a date or amount should be normalized. Keep them synthetic; validate required fields, allowed values, and source evidence in application code. Measure the example/no-example variants on the same held-out cases rather than assuming few-shot is more reliable.

#### What is chain-of-thought, and when is it useful? / 什么是思维链，何时有用？

Chain-of-thought (CoT) prompting asks for intermediate reasoning text before a final answer, often through examples or an instruction. Research found gains on some multi-step arithmetic and reasoning benchmarks under particular model and prompt conditions. The result is task- and model-dependent: asking for step-by-step text does not guarantee correct reasoning, and a written rationale is not proof that it faithfully describes the model's internal computation.

A small arithmetic illustration is 4 × $2 + 2 × $3 = $8 + $6 = $14. A model may give a concise answer, a worked explanation, or an incorrect derivation. Verify consequential arithmetic with code or another trusted method.

OpenAI's reasoning-model guidance, checked 2026-10-15, recommends trying a straightforward prompt first; asking for step-by-step reasoning can be unnecessary or counterproductive for those models. API behavior differs by provider and model, so evaluate the actual target rather than carrying a prompt recipe across systems.

#### What is self-consistency? / 什么是自一致性？

Self-consistency samples multiple candidate reasoning answers and aggregates their final answers, often by a majority vote. The research paper reported improvements on several tested reasoning benchmarks. It can help when the candidates make partly independent errors, but repeated samples can agree on the same wrong answer. Use a task-specific verifier for important results.

**Illustration, not model output / 示意，不是模型实测输出：** For 17 × 23, two valid decompositions are 17 × (20 + 3) = 340 + 51 = 391 and (10 + 7) × 23 = 230 + 161 = 391. If sampling several candidates, normalize equivalent answers before aggregation; voting does not replace checking.

Multiple samples increase token use and usually require more inference work. Exact cost and wall-clock impact depend on batching, provider behavior, and the selected model. Compare accuracy, latency, and cost with a single answer on the target task.

#### What is ReAct, and when should an application use a tool loop? / 什么是 ReAct，应用何时应使用工具循环？

ReAct is a research prompting pattern that interleaves a model's reasoning text, an action, and an observation from an environment. Its paper evaluated it on specific knowledge and interactive tasks. It is one design option for tasks that need successive observations and actions, not a universal default for tool use. A one-shot function call or a developer-controlled workflow may be simpler when the path is known.

**Synthetic flight-search illustration / 虚构的航班搜索示例:**

~~~text
User: Find the lowest listed fare from NYC to LA for next Tuesday.
Action: search_flights(origin="NYC", destination="LA", date=<resolved date>)
Observation: The search service returned three fares: $189, $210, and $175.
Answer: The lowest fare returned by that search was $175.
~~~

This example assumes a real search service would resolve airport codes, date, currency, freshness, and availability. The model must not invent those observations. The application should validate tool arguments, authorize side effects, limit tool access and turns, record outcomes, and stop safely on errors. Treat retrieved pages and tool output as untrusted input; see [Agent Fundamentals / 智能体基础](#7.%20Agent%20Fundamentals%20/%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%9F%BA%E7%A1%80), [Tool Design and Function Calling / 工具设计与函数调用](#9.%20Tool%20Design%20and%20Function%20Calling%20/%20%E5%B7%A5%E5%85%B7%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%87%BD%E6%95%B0%E8%B0%83%E7%94%A8), and [AI Safety in Production / 生产环境中的 AI 安全](#12.%20AI%20Safety%20in%20Production%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84AI%E5%AE%89%E5%85%A8).

#### When should you chain prompts? / 何时串联提示词？

Use a fixed prompt chain when the task has separable steps and code can validate, branch, retry, or stop between them. If the sequence is known, developer-controlled stages can be easier to inspect than an open-ended agent loop. Each model call can still be wrong; validate intermediate outputs and test the whole chain.

**Outline → validate → write / 大纲 → 校验 → 写作:**

1. Ask for an outline in a declared schema.
2. Parse it and check required sections and constraints in application code.
3. If valid, ask for a draft based on the outline; otherwise return an explicit failure or a bounded correction request.

~~~python
outline = call_model(make_outline_prompt(topic))
parsed = parse_schema(outline)
if not parsed.ok:
    return validation_error(parsed.issues)
if not deterministic_checks(parsed.value):
    return validation_error("outline violates required section rules")
return call_model(make_draft_prompt(parsed.value))
~~~

If five stages each succeed with probability 0.95 and failures are independent, the probability that all five succeed is 0.95⁵ ≈ 0.774. Real failures may be correlated, and retries or gates change the result; measure the actual workflow instead of treating this illustration as a reliability estimate.

#### What is meta-prompting? / 什么是元提示？

Meta-prompting uses a model to generate candidate instructions or revise an existing prompt in response to concrete failures. Treat either output as a candidate. Evaluate variants on development examples, inspect failures, and keep a final held-out set untouched until selection; repeated tuning against the same set can overfit it.

Automatic Prompt Engineer (APE) is one research approach to generating and selecting instruction candidates for evaluated tasks. The templates here are a lightweight human-directed workflow, not a reproduction of that method or its reported results.

**Candidate generation / 生成候选提示词:**

~~~text
Task: Classify a support message as billing, technical, or general.
Success: Choose the supported category; return needs_review when evidence is insufficient.
Inputs: Only the supplied message and category definitions.
Output: Return the category and needs_review as JSON.
Generate three materially different candidate instructions. For each, state which ambiguity it addresses. Do not claim the candidates have been tested.
~~~

**Failure-driven revision / 根据失败样例修订:**

~~~text
Current prompt:
[insert the current synthetic prompt]

Observed failure:
[insert a synthetic input and the incorrect output]

Expected behavior:
[state the correct output and why]

Revise only the instruction needed to address this failure. Preserve the task, output contract, and other constraints. Return the revised prompt and a short change note. This candidate still requires evaluation on examples not used to write it.
~~~

A practical loop is to define success criteria, generate or revise candidates, compare them on the same development set, review regressions and edge cases, then confirm the selected version on an untouched held-out set before deployment. Keep the evaluation data appropriate for the sensitivity and policy of the task.

#### Related notes / 相关笔记

- [Prompt Engineering Fundamentals / 提示工程基础](#3.%20Prompt%20Engineering%20Fundamentals%20/%20%E6%8F%90%E7%A4%BA%E5%B7%A5%E7%A8%8B%E5%9F%BA%E7%A1%80) covers clear instructions, examples, and output contracts.
- [Context Engineering Principles / 上下文工程原则](#5.%20Context%20Engineering%20Principles%20/%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B%E5%8E%9F%E5%88%99) covers the information available to each inference.
- [Agent Fundamentals / 智能体基础](#7.%20Agent%20Fundamentals%20/%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%9F%BA%E7%A1%80), [Orchestration Patterns / 编排模式](#8.%20Orchestration%20Patterns%20/%20%E7%BC%96%E6%8E%92%E6%A8%A1%E5%BC%8F), and [Tool Design and Function Calling / 工具设计与函数调用](#9.%20Tool%20Design%20and%20Function%20Calling%20/%20%E5%B7%A5%E5%85%B7%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%87%BD%E6%95%B0%E8%B0%83%E7%94%A8) cover runtime tool loops and control flow.

#### Sources / 来源

- Wei et al., [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903).
- Kojima et al., [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916).
- Wang et al., [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171).
- Yao et al., [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629).
- Zhou et al., [Large Language Models Are Human-Level Prompt Engineers](https://arxiv.org/abs/2211.01910), for the APE instruction-generation and selection approach.
- OpenAI, [Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices), checked 2026-10-15. These instructions describe OpenAI reasoning models and should not be generalized to other APIs.
- OpenAI, [Prompt generation](https://developers.openai.com/api/docs/guides/prompt-generation), checked 2026-10-15. This is an OpenAI-specific example of generating or revising prompt text, not evidence that a generated prompt performs better without task evaluation.
## 5. Context Engineering Principles / 上下文工程原则

### Context Engineering Principles | 上下文工程原则

**核心解释 / Core explanation：** 上下文工程（context engineering）是在每次模型推理时，选择、组织和更新模型可用的信息，以支持当前目标。Context engineering selects, organizes, and updates the information available to a model for each inference step.

**30 秒面试回答 / 30-second interview answer**

- **中文：** 提示工程主要优化指令；上下文工程还管理工具、对话历史、检索结果、执行观察和外部任务状态。上下文既受窗口、成本和时延限制，也可能因噪声、信息位置或过度压缩而降低有效性，因此要围绕任务评估结果，保留高价值信息并按需加载其余资料。
- **English:** Prompt engineering focuses on instructions; context engineering also manages tools, conversation history, retrieved evidence, observations, and external task state. Context is constrained by the window, cost, and latency, and its usefulness can fall with noise, position effects, or lossy compaction. I measure task outcomes, keep high-value information, and load the rest when needed.

#### 提示工程与上下文工程

**提示工程（prompt engineering）** 关注如何组织指令和示例。**上下文工程（context engineering）** 关注每次推理实际提供给模型的整套信息，包括系统与开发者指令、工具定义、历史消息、检索材料、工具观察和任务状态。两者相互依赖：好指令不能补救缺失证据，更多材料也不能替代清楚的指令。[Anthropic 的上下文工程文章](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)把上下文视为每次推理都需要重新整理的动态集合，并建议用任务结果评估信息配置。

#### Why is context a finite resource, and what's "lost-in-the-middle"?

**上下文资源有限，长文本的效能也会变化 / Context is finite, and long-context performance varies.**

模型能接收较长输入，不等于能同样可靠地使用任意位置的所有信息。上下文还受模型支持的窗口、输入成本、预填充时延、检索噪声与目标相关性影响。随着上下文增大，效果并非必然以一个固定速度下降，也没有适用于所有模型和任务的“30 轮”或 token 数阈值。

**Lost in the middle（中间迷失）** 是位置敏感性的一种实证现象。[Liu 等人的研究](https://arxiv.org/abs/2307.03172)在多文档问答和键值检索任务中观察到，模型对位于输入中部的信息有时不如位于开头或末尾的信息利用充分。它说明应在实际任务中测试长上下文与位置变化；不能据此断言所有模型总是更注意首尾，或某个 RAG 分块位置必然失败。

有效做法是选取足以完成当前子任务的高信号信息，给关键证据附来源或标识，并对模型、任务与提示结构做长上下文评估。注意力机制的理论复杂度不能单独证明某个系统会在特定上下文长度失效。

#### 管理持续增长的上下文

下面的“缩减、外置、隔离”是实用整理方法，不是必须采用的固定分类。多数长任务会组合使用：

| 方法 | 何时使用 | 需要保留什么 |
|---|---|---|
| **缩减（reduce）** | 重复历史、冗长工具输出挤占当前任务空间 | 目标、关键决定、未解决问题、失败状态、资源 ID 与可追溯来源 |
| **外置（offload）** | 原始资料太大或跨越多轮/会话 | 文件、数据库或其他持久状态中的原始内容；上下文只保留可再次读取的路径、查询或 ID |
| **隔离（isolate）** | 一个任务需要独立研究，或当前历史混杂多个职责 | 工作者的目标、权限、输入与输出契约；主流程接收结论、证据和不确定性 |

**摘要与压缩：** 摘要有损。先保留稍后可能影响决策的事实，再删去重复内容；“订单已退款”不一定足以支持追问，可能还要留下订单号、金额、状态依据与操作 ID。原始记录可通过外部引用重新读取时，摘要就不必承担永久记忆的职责。Anthropic 建议在长任务中用 compaction、持久笔记和子智能体，并提醒过度压缩会丢失之后才显得重要的信息。

**按需加载（just-in-time retrieval）：** 保留轻量引用，在需要时再读取文件、网页或数据库，而非预先加载全集。这减少无关 token，但每次探索需要额外工具调用，并依赖检索能力和可用权限。对经常需要的稳定资料，也可先加载摘要，再按需查原文。[Anthropic 对按需检索与混合策略有详细说明。](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

**隔离上下文：** 子智能体不会天然共享同一份记忆。清楚传递目标、必要背景和结果格式；需要一致决策时，明确由主 agent 汇总和核对。切分依据应是任务边界、权限或可验证的并行收益，而不是把完整历史复制给每个工作者。

#### How do you use the KV cache to cut inference cost?

**KV cache 与 prompt caching 是相关但不同的复用机制 / KV cache and prompt caching are related but distinct reuse mechanisms.**

**KV cache** 是自回归模型生成时保存先前 token 的 key/value 表示，以供同一次生成后续 token 使用。**Prompt caching（提示缓存）** 通常指推理服务在后续请求中重用相同前缀的计算。后者可降低特定服务和配置下的输入成本或首 token 时延；两者都不是模型的长期记忆，也不意味着缓存 token 在所有供应商中都按同一价格收费。

缓存规则依供应商、模型和 API 而异。以 [OpenAI 当前 API 文档](https://developers.openai.com/api/docs/guides/prompt-caching)为例，缓存匹配依赖渲染后的请求前缀和可用的缓存断点；工具名、描述、schema 或顺序变化可能让变化之后的前缀无法复用。改变前缀不等于每种服务都把整段历史全部丢弃，实际匹配边界、最小长度与生命周期需查对应文档。

- 将稳定指令和可复用资料放前面，把每次请求都会变的用户信息、时间戳放后面。
- 在 API 支持的状态模型中，追加消息通常比重写早期内容更利于复用；压缩或改写历史可能改变匹配前缀。
- 只有实测缓存命中率、总 token 成本与行为结果都合适时，才为缓存调整上下文布局。
- 若工具列表因权限变化而变，先保证能力配置正确；缓存优化不能成为保留过期权限的理由。

Manus 的[上下文工程经验](https://www.manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)展示了稳定前缀、追加式历史和确定性序列化对其部署缓存的价值。这些是实践经验；不能把其价格、命中率或框架实现直接当作其他 API 的现行保证。

#### 长任务中的目标、计划与失败记录

**目标重述（recitation）**：长循环会不断加入操作和观察。把精简的当前目标、已完成事项、下一步与阻塞项放到模型本轮可见的位置，并将权威状态保存在持久任务记录中，可降低目标在历史中被淹没的风险。

例如，维护一个短任务清单：完成登录校验修复；定位导致失败的输入；运行对应测试；记录仍未验证的路径。[Manus 公开了在其长循环中把 todo 写到近期上下文的做法](https://www.manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)，而 Anthropic 也描述了使用持久笔记追踪长任务进度。该模式是有用的设计启发，不意味着所有 agent 都需要每轮重写清单，也不支持一个通用的平均工具调用次数。

**保留有用的失败证据：** 若后续决策需要知道刚才做过什么，保留精简的“尝试动作 → 错误或观察 → 当前状态”。这能让模型看到重试为何失败，但不会更新模型参数；只有在下一次推理时实际提供的记录才可能影响决策。无关日志、敏感数据和巨大堆栈应按需外置，并保留查询引用。压缩历史时，不要把会影响安全重试或后续确认的失败状态删掉。

**历史会变成示例：** 上下文里重复的动作—观察模式可能影响模型下一步模仿什么。Manus 描述了在批量审核 20 份简历时观察到重复操作，并提出用结构化变体打破模式；这仍是该团队的实践假设，没有足够证据把“改变格式”当作普遍解决方案。保持规范、易解析的序列化通常更利于复现与缓存；若评测发现重复行为，先精简或组织历史，再用任务集比较不同表示，不要无依据地注入格式噪声。

#### 相关知识

- [智能体基础](#7.%20Agent%20Fundamentals%20/%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%9F%BA%E7%A1%80)：上下文、环境反馈和智能体执行循环如何连接。
- [工具设计与函数调用](#9.%20Tool%20Design%20and%20Function%20Calling%20/%20%E5%B7%A5%E5%85%B7%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%87%BD%E6%95%B0%E8%B0%83%E7%94%A8)：工具 schema 与执行结果也是上下文的一部分。
- [RAG 架构与实现](#6.%20Retrieval-Augmented%20Generation%20%28RAG%29%20/%20%E6%A3%80%E7%B4%A2%E5%A2%9E%E5%BC%BA%E7%94%9F%E6%88%90)：了解何时预先检索、何时按需检索。
## 6. Retrieval-Augmented Generation (RAG) / 检索增强生成

### Retrieval-Augmented Generation (RAG) / 检索增强生成

**Retrieval-augmented generation (RAG) / 检索增强生成** adds evidence from an external source to the context of a language model at request time. A retriever selects candidate evidence; the application assembles an authorized, relevant context; a generator produces an answer from that context. RAG connects a model’s **parametric memory / 参数化记忆** with **non-parametric memory / 外部可检索知识**. Its usefulness depends on the source, retrieval, context assembly, and the model’s use of evidence. It does not guarantee correctness, freshness, privacy, low latency, or low cost. [Lewis et al.](https://arxiv.org/abs/2005.11401)

**Interview answer / 面试简答：**

> **EN:** RAG retrieves external evidence for a query and supplies selected passages to a language model as context. Retrieval determines what evidence is available; generation determines how the model uses it. This can make external knowledge easier to update than model weights, but answer quality still depends on source coverage, access controls, retrieval, and evidence use. RAG does not guarantee a correct answer or lower total cost and latency.
>
> **中文：** RAG 根据查询从外部来源检索证据，再把筛选后的内容作为上下文交给语言模型。检索决定哪些证据可用，生成决定模型如何使用这些证据。它可以让外部知识比模型权重更容易更新，但回答质量仍取决于来源覆盖、访问控制、检索和模型对证据的使用；RAG 不保证答案正确，也不保证总成本或时延更低。

#### When to use retrieval, long context, or fine-tuning / 如何选择检索、长上下文或微调

These techniques solve different constraints and can be combined:

| Approach | Useful when | Main tradeoff |
|---|---|---|
| **RAG / 检索增强** | The application needs to select evidence from a source that is larger than one prompt, changes over time, or has source-level access rules. | Adds ingestion/synchronization and retrieval work. Retrieval can miss, return stale or conflicting material, or select content the generator does not use well. |
| **Long context / 长上下文** | The relevant material can be supplied together and the task benefits from reasoning across that material without a separate search step. | The model must still find and use the relevant parts. Context length, position effects, and input-token cost depend on the model and workload. |
| **Fine-tuning / 微调** | Repeated examples can teach a desired response pattern, task behavior, or format. | It does not by itself provide a reliable, current source of external facts. Use retrieval as well when answers must cite or reflect a maintained corpus. |

There is no universal token-count cutoff. Compare the methods on representative questions, including required evidence, source updates and permissions, answer quality, end-to-end latency, and cost. In one EMNLP 2024 comparison, long-context models had higher average performance when sufficiently resourced, while RAG cost less in that evaluated setting; this result is not a general ranking of all systems. Long-context models can also be position-sensitive on tested tasks. [Li et al.](https://arxiv.org/abs/2407.16833), [Liu et al.](https://arxiv.org/abs/2307.03172)

#### Pipeline / 检索增强生成的流程

A RAG request has two connected paths. The corpus path parses and indexes content; the query path retrieves evidence and uses it for generation. This note focuses on text corpora. A system can also fetch live records or call APIs at query time.

```text
Corpus path: source documents → parse and preserve metadata → split into chunks → encode and/or build lexical index
Query path: question + caller → authorization filter → retrieve candidates → optional reranking → assemble evidence → generate
```

Indexing is often asynchronous or performed ahead of user requests, but that is an implementation choice, not part of the definition of RAG. Preserve enough provenance to identify each chunk’s source and version. If source documents change, the application must synchronize those changes and define how it handles old versions, deletion, and revoked access.

A framework-neutral sketch of the query path:

```python
# Synthetic example: answer a question about a sample policy.
# The application computes and enforces this caller's scope.
query = "What is the sample policy's cancellation window?"
allowed_scope = authorization_scope(caller)
candidates = retrieve(query, scope=allowed_scope, limit=40)  # illustrative candidate count
ranked = rerank(query, candidates)
evidence = select_passages(ranked, limit=5)                  # illustrative passage count
answer = generate(query=query, context=evidence)             # also enforce the model's token budget
```

The limits above illustrate **wide candidate retrieval → reranking → finite evidence**; they are not recommended values. The example selects at most five passages and must also fit them within the model's token budget. Reranking can reorder only candidates already retrieved. If the needed passage is absent from the candidate set, reranking cannot recover it. The application should retain source metadata through assembly and validate any required citations separately. This sketch omits implementation details such as filtering syntax, source synchronization, and citation validation.

Treat retrieved text as untrusted input; the access and trust-boundary section below covers prompt injection and application-side controls.

#### Embeddings and similarity / 向量表示与相似度

An embedding maps text to a vector for retrieval. Query and document encodings must follow a **compatible encoding contract / 兼容的编码契约**: their vector dimensions and learned space must support comparison, and each model’s query/document input format must be respected. This does not require identical encoder weights. Dense Passage Retrieval (DPR), for example, uses separate question and passage encoders. [Karpukhin et al.](https://arxiv.org/abs/2004.04906)

Changing document-side encoding, output dimensions, normalization, or preprocessing may require re-embedding or migrating the affected document vectors if they no longer meet the query/document contract. A query-side change alone does not necessarily require rebuilding the document index, but its compatibility and retrieval quality must be re-evaluated. Model choice should account for the language and task, query/document format, deployment and privacy constraints, input limits, latency, price, and performance on the target corpus. Avoid treating a model list or benchmark ranking as a permanent recommendation.

Common similarity measures are:

| Measure | Formula | Interpretation |
|---|---|---|
| **Cosine similarity / 余弦相似度** | $\frac{A \cdot B}{\lVert A \rVert \lVert B \rVert}$ | Compares vector direction and is invariant to vector magnitude. |
| **Dot product / 点积** | $A \cdot B$ | Depends on both direction and magnitude unless vectors are normalized. |
| **Euclidean distance / 欧氏距离** | $\lVert A-B \rVert_2$ | Measures distance; smaller values indicate closer vectors. |

The metric must match the model’s representation and the vector index configuration. For OpenAI’s normalized embeddings, cosine similarity and dot product produce the same ranking, and Euclidean distance also produces identical rankings; this equivalence should not be assumed for arbitrary embeddings. [OpenAI embeddings guide](https://developers.openai.com/api/docs/guides/embeddings)

#### Chunking / 文档分块

A **chunk / 文档块** is a retrievable unit derived from a source document. Chunking trades retrieval precision against context completeness: small chunks can isolate evidence but lose nearby qualifications; large chunks preserve surrounding context but can include irrelevant material. The useful size depends on source structure, parser quality, query mix, embedding model, and the generator’s context budget. There is no generally optimal token size or overlap ratio; evaluate choices on representative queries. A 2025 ACL Findings study documents how segmentation choices affect RAG behavior, while a 2026 chunking preprint found different tradeoffs in one SPLADE/Mistral-8B/Natural Questions setup. [Wang et al.](https://aclanthology.org/2025.findings-acl.422/), [Bennani & Moslonka](https://arxiv.org/abs/2601.14123)

| Strategy | Mechanism | Useful when | Limitation |
|---|---|---|---|
| **Fixed-size / 定长分块** | Split at a character or tokenizer-token limit; optionally retain overlap at boundaries. | A simple, predictable baseline is needed. | May cut across a sentence, table, code block, or concept. State whether the limit is characters or tokens. |
| **Recursive / 递归分块** | Try separators in order (for example, section breaks, newlines, then spaces) until parts fit a target length. | Text has natural separators and a generic baseline is appropriate. | The resulting chunk sizes vary and the separator hierarchy may not match the source structure. |
| **Semantic / 语义分块** | Group nearby sentences or passages and split at a semantic boundary, often using embedding similarity. | Boundary coherence is a measured problem worth extra indexing work. | Similarity thresholds and model choice affect results; it is not automatically more accurate. |
| **Document-aware / 结构感知分块** | Split on source structure such as headings, pages, sections, tables, or code syntax. | Structure carries meaning or links evidence across a document. | Depends on successful parsing and may still need size limits or a fallback splitter. |

**Character-count example / 字符长度示例：** LangChain’s current Python documentation shows `RecursiveCharacterTextSplitter` from the separate `langchain_text_splitters` package. With its default length function, `chunk_size` and `chunk_overlap` count characters, not tokens. The values below mirror a documentation example and illustrate the API; they are not universal RAG settings. Use a tokenizer-aware length function if the target constraint is model tokens. [LangChain documentation](https://docs.langchain.com/oss/python/langchain/knowledge-base)

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # characters with the default length function
    chunk_overlap=200,     # characters retained across adjacent chunks
    add_start_index=True,  # preserve the source character offset
)
chunks = splitter.split_documents(documents)
```

Overlap can retain context across boundaries, but it also duplicates text and increases indexed content. Treat overlap as an evaluation parameter, not a mandatory fix. The right chunking choice can also depend on the query’s evidence shape; “query-dependent” does not mean document structure is irrelevant.

For the parent-child chunking design and its trade-offs, see “Parent-child retrieval / 父子分块检索” under Retrieval upgrades below.

#### Dense, sparse, and hybrid retrieval / 稠密、稀疏与混合检索

**Dense retrieval / 稠密检索** embeds the query and chunks, then ranks chunks by vector similarity. It can match related phrasing even when wording differs, depending on the model and task. It can still miss exact identifiers, rare names, or relevant evidence.

**Sparse retrieval / 稀疏检索** ranks using lexical features. BM25 is a common term-based retriever and can be useful for exact strings such as error codes, product identifiers, and names. It may miss paraphrases whose vocabulary differs from the document.

**Hybrid retrieval / 混合检索** combines dense and sparse candidates or rankings. The methods can complement one another, but hybrid retrieval is not a universal default. A heterogeneous retrieval benchmark found BM25 to be a robust baseline; it also found that reranking and late-interaction systems performed strongly on average at higher computational cost. Results vary across tasks, so compare retrieval methods on the application’s queries. [BEIR](https://arxiv.org/abs/2104.08663)

One fusion method is **Reciprocal Rank Fusion (RRF) / 倒数排名融合**. It combines rankings rather than directly combining raw scores:

$$
\operatorname{RRF}(d) = \sum_i \frac{1}{k + r_i(d)}
$$

Here, $r_i(d)$ is document $d$’s rank in result list $i$; a document absent from a list contributes nothing. RRF avoids requiring the raw score scales to match, but the smoothing constant $k$, retrieval depths, and systems being combined still affect the result. Treat it as a useful baseline and evaluate it against alternatives, not as a calibration-free guarantee. [Cormack, Clarke & Büttcher](https://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf)

#### Reranking / 重排

A **bi-encoder / 双编码器** independently encodes a query and each document, allowing document vectors to be indexed and searched efficiently. A **cross-encoder / 交叉编码器** processes a query-document pair together and returns a relevance score. Joint input permits a richer pairwise comparison, but scoring many candidates costs more than a vector lookup. Retrieval-plus-reranking is therefore a **recall then precision** pattern: retrieval proposes candidates, and reranking changes their order.

For example, a synthetic question about a sample policy might retrieve a broad candidate set, rerank those chunks against the question, then pass only a few supported passages to generation. Candidate depth and final context size are workload parameters. If evidence is not among the retrieved candidates, the reranker cannot add it. If reranking keeps the entire candidate set (candidate count equals final returned count), reordering alone does not change set-based precision@k, though it can affect rank-sensitive metrics and the order in which evidence reaches generation. Compare quality and latency across candidate depths instead of assuming a particular top-k is best. BEIR found strong average zero-shot performance for reranking architectures in its evaluated benchmark, with higher computational cost. [BEIR](https://arxiv.org/abs/2104.08663)

#### Retrieval upgrades / 检索增强策略

Use these techniques to address a diagnosed failure, and evaluate each on the affected query set before combining them.

##### Query transformation / 查询改写

Rewrite or expand a query when the user’s wording does not align with the corpus vocabulary or when a compound request needs clearer subqueries. Query expansion can run several variants and merge results. Rewriting can also alter the user’s intent, so retain the original query and compare retrieval outcomes.

##### HyDE (Hypothetical Document Embeddings) / 假设文档嵌入

HyDE asks a language model to generate a hypothetical document in response to a query, embeds that hypothetical text, and uses the vector to retrieve real corpus documents. The generated document is a **retrieval intermediary, not answer evidence**; the original paper notes it may contain false details. HyDE was proposed for zero-shot dense retrieval when relevance labels are unavailable. It is not based on a general rule that short queries embed poorly near long passages. [Gao et al.](https://arxiv.org/abs/2212.10496)

##### Parent-child retrieval / 父子分块检索

Embed and retrieve child passages, then return their parent section as context. This can recover nearby definitions or qualifications that are useful to interpret the child evidence. Deduplicate parent sections and keep the final context within a budget; evaluate whether the broader passages help the query set.

##### Multi-step retrieval / 多步检索

For a question whose answer requires evidence from more than one source, retrieve an initial set, identify the unresolved relation or sub-question, and retrieve again. This can support multi-hop questions, but it adds retrieval or generation work. Stop when the needed evidence is present or when the remaining uncertainty should be reported rather than hidden by another search.

#### Operations, evaluation, and failure diagnosis / 运行边界、评估与故障定位

##### Access, freshness, and trust boundaries / 权限、新鲜度与信任边界

RAG does not make a corpus private. Compute the caller’s permissions in trusted application code and enforce them in the retrieval/data-access layer before evidence reaches the model. Metadata filters can express attributes such as tenant, region, source, or date, but correctness of the policy and its enforcement belongs to the application. Track document identity and version so updates, deletions, and permission revocations do not leave stale chunks available. The index is only as fresh as its synchronization and processing path. [OWASP LLM08:2025](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/), [OpenAI retrieval guide](https://developers.openai.com/api/docs/guides/retrieval)

Treat all retrieved text as untrusted content. A document can contain direct or indirect instructions that influence the model. Delimiters and prompts may reduce confusion, but they do not guarantee protection. Do not let a retrieved passage authorize a data access or tool action; enforce permissions and validate actions outside the model. [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/). For more on prompt injection and application boundaries, see [AI Safety in Production / 生产环境中的 AI 安全](#12.%20AI%20Safety%20in%20Production%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84AI%E5%AE%89%E5%85%A8).

##### Evaluation / 评估

Measure retrieval and generation separately, then compare the complete system:

- **Retrieval:** Did the authorized candidate set contain the necessary evidence, and where was it ranked?
- **Generation:** Is the answer correct for the task, supported by the supplied evidence, responsive to the question, and appropriately abstaining when evidence is missing or conflicting?
- **System:** What are end-to-end latency and cost, including query transforms, embedding, retrieval, reranking, context tokens, and indexing/update work where relevant?

RAGAS and ARES illustrate multi-dimensional evaluation, including context relevance, answer faithfulness, and answer relevance; they are evaluation frameworks, not a complete universal score. Automated judges are useful signals and should be checked against representative human-reviewed examples. See [LLM Evaluation Methods / 大语言模型评估方法](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95). [RAGAS](https://arxiv.org/abs/2309.15217), [ARES](https://arxiv.org/abs/2311.09476)

##### Diagnose from evidence / 根据证据定位故障

| Symptom | Inspect | Possible next step |
|---|---|---|
| The source does not contain the needed fact, or the current version is missing. | Source coverage, parsing, synchronization, deletion/version state. | Fix source ingestion or freshness; if the evidence is unavailable, report that limitation. |
| The evidence exists but is absent from retrieved candidates. | Caller filters, query interpretation, chunk boundaries, embedding/lexical retrieval, candidate recall. | Correct scope or ingestion first; then compare retrieval and chunking choices on the failing queries. |
| A useful candidate is retrieved but absent from the prompt. | Reranker order, deduplication, context assembly, and truncation. | Adjust ranking or evidence selection and verify that citations still map to source passages. |
| Evidence is in the prompt, but the answer is unsupported or contradicts it. | Conflicting passages, prompt instructions, model output, citation support, and whether the question is answerable. | Test prompt/model/evidence changes against the same cases; do not infer a specific internal cause from the answer alone. |

A practical debugging loop is: inspect the source and authorized candidates; inspect what reached the model; check answer claims against those passages; then change one retrieval or generation factor and evaluate the same cases. More context can add missing evidence or add noise, so “retrieve more” is a hypothesis to test, not a universal fix. Long-context performance can also depend on where relevant information appears. [Liu et al.](https://arxiv.org/abs/2307.03172)

#### Related notes / 相关笔记

- [Context Engineering Principles / 上下文工程原则](#5.%20Context%20Engineering%20Principles%20/%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B%E5%8E%9F%E5%88%99) explains context budgets and how placement can affect use of evidence.
- [Fine-tuning Strategies / 微调策略](#11.%20Fine-tuning%20Strategies%20/%20%E5%BE%AE%E8%B0%83%E7%AD%96%E7%95%A5) discusses adapting model behavior and combining it with external knowledge.
- [LLM Evaluation Methods / 大语言模型评估方法](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95) covers evaluation datasets, metrics, and review methods.
- [AI Safety in Production / 生产环境中的 AI 安全](#12.%20AI%20Safety%20in%20Production%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84AI%E5%AE%89%E5%85%A8) covers prompt injection, permission boundaries, and runtime controls.
## 7. Agent Fundamentals / 智能体基础

### Agent Fundamentals | 智能体基础

**核心解释 / Core explanation：** 智能体（AI agent）让模型在明确边界内决定下一步，并依据工具或环境返回的结果继续任务。An AI agent lets a model choose task steps within defined boundaries and adapt to tool or environment feedback.

**30 秒面试回答 / 30-second interview answer**

- **中文：** 工作流由代码安排模型何时做什么；智能体把部分控制权交给模型，让它根据中间结果选择下一步。是否使用智能体取决于任务是否需要这种灵活性，以及它能否带来足以抵偿成本、延迟和新故障面的收益。
- **English:** A workflow uses code to define when the model acts; an agent gives the model some control to choose the next step from intermediate results. I use an agent only when that flexibility improves task outcomes enough to justify its cost, latency, and operational risk.

#### 智能体、工作流、聊天与 RAG

**智能体（AI agent）** 的定义并不完全统一。[Anthropic 将 workflow 与 agent 都放在 agentic systems 的范围内，并以控制流由代码预先定义还是由模型动态决定来区分；OpenAI 的定义也强调模型管理任务流程并按状态选择工具。](https://www.anthropic.com/engineering/building-effective-agents) [OpenAI 的 agent 指南](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) 因而，是否调用过工具、调用几次，不是可靠的唯一判据。

| 概念 | 核心特征 |
|---|---|
| **工作流（workflow）** | 程序定义步骤、顺序和分支；模型在指定节点完成分类、抽取或生成。 |
| **智能体（agent）** | 模型根据目标与观察结果选择工具或下一步；运行时负责执行、限制和停止。 |
| **聊天界面（chat interface）** | 用户交互形态，可以只是问答，也可以包在工作流或智能体外。 |
| **检索增强生成（RAG）** | 一种把检索内容交给模型的架构能力；它可以是单次流程中的一步，也可以供智能体迭代调用。 |

一次工具调用后返回，不足以判断系统是否“真正是 agent”；应描述模型实际拥有多少流程控制权。比如，客服退款可以由固定工作流处理合规检查，只让模型分类用户意图；如果系统需要调查多种来源、根据发现决定后续步骤，才可能值得交给智能体控制。

#### 选择工作流还是智能体

先用能满足成功标准的最简单结构，再通过实际任务评估是否需要更大自主性。Anthropic 将工作流的可预测性与智能体对开放式任务的适应性作了区分，也提醒智能体可能增加成本和累积错误；这是一种设计权衡，不是“分支超过某个数量就必须用 agent”的定律。

| 任务形状 | 较合适的起点 | 例子 |
|---|---|---|
| 步骤固定、输入类别有限、结果可验证 | 代码工作流 | 校验订单 → 计算退款金额 → 执行退款 → 发送回执 |
| 后续步骤依赖未知的中间发现 | 有预算与停止条件的智能体 | 调查复杂故障时，根据日志和测试结果决定继续查哪一处 |
| 大部分步骤固定，少数探索性任务开放 | 混合架构 | 固定工单流程中，允许智能体在“诊断”节点调查日志 |

评估时比较任务成功率、错误类型、总延迟、模型与工具成本、人工接管率。多轮运行可能更贵、更慢，但并不存在固定的“每多一步就按同一倍数增长”的通用比例；缓存、工具耗时、输出长度和模型价格都会改变结果。

#### 执行循环 / Agent loop

一个常见循环是：

1. **模型决定（decide）：** 根据当前目标、状态和可用能力，继续推理、请求工具、提问或结束。
2. **运行时执行（execute）：** 校验调用格式、授权范围与业务条件，再执行实际函数或外部操作。
3. **环境观察（observe）：** 取得成功结果、错误、部分结果或人工反馈。
4. **更新状态（update）：** 将有用观察与任务状态提供给下一次模型调用。
5. **停止或继续（stop or continue）：** 检查完成条件、预算、最大动作数、超时及是否需要人类判断。

函数调用只是模型提出的结构化请求；API、运行时或用户界面才会实际执行它。每次模型推理只能使用当前请求或已配置的会话状态，不能假定模型有未显式保存的持久记忆。

**退款例子：** 收集客户、订单和支持历史属于可并发的只读工作；退款金额必须在核实订单后计算，执行前还要通过权限与业务规则检查。若退款执行超时，结果可能未知；应先用操作 ID 查询是否已成功，再决定是否重试，而不是盲目重复写操作。具体工具契约见[工具设计与函数调用](#9.%20Tool%20Design%20and%20Function%20Calling%20/%20%E5%B7%A5%E5%85%B7%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%87%BD%E6%95%B0%E8%B0%83%E7%94%A8)。

停止条件应在系统里实现，而不只写在提示词里：完成、需要补充信息、转交人工、不可恢复的错误或预算耗尽都应有明确结果。最大轮数、总调用数、超时和费用上限能限制失控运行；监测重复调用可作为额外信号，但不能代替业务停止条件。

#### 可用动作空间 / Action space

工具是智能体能观察和改变环境的接口，也是系统的权限边界之一。优先提供用途清楚、彼此少重叠、能直接支持目标流程的能力；名称空间如 browser_search、file_read 有助于识别工具归属，但名称本身不构成安全控制。[Anthropic 的工具评估发现，不同命名方式对不同模型的影响有差异，建议按自己的任务评估。](https://www.anthropic.com/engineering/writing-tools-for-agents)

可用工具可能随任务阶段或用户权限变化。Manus 曾公开其系统以状态机和解码时 logits mask 控制特定工具；这是依赖模型与运行时能力的实现，不是所有托管 API 都能直接使用的通用技巧。工具列表变化也可能影响供应商的前缀缓存，但应以具体 API 的序列化和缓存规则为准。无论工具是否展示给模型，运行时都必须依据当前用户、租户和动作授权进行检查；对不可逆或高风险操作设置确认或人工审批。

#### 相关知识

- [编排模式](#8.%20Orchestration%20Patterns%20/%20%E7%BC%96%E6%8E%92%E6%A8%A1%E5%BC%8F)：选择顺序、并行、路由或多智能体结构。
- [上下文工程原则](#5.%20Context%20Engineering%20Principles%20/%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B%E5%8E%9F%E5%88%99)：管理长任务中的历史、外部状态与缓存。
## 8. Orchestration Patterns / 编排模式

### Orchestration Patterns | 编排模式

**核心解释 / Core explanation：** 编排（orchestration）决定任务由哪些模型调用或智能体完成，以及它们如何传递状态和结果。Orchestration defines which model calls or agents handle a task and how they pass state and results.

**30 秒面试回答 / 30-second interview answer**

- **中文：** 我先看步骤是否固定、子任务是否独立、后续任务是否依赖前序结果，再选择工作流或智能体模式。只有并行、上下文隔离、能力隔离等收益经评估足以覆盖通信、延迟和协调成本时，才拆成多个智能体。
- **English:** I choose an orchestration pattern based on whether steps are known, subtasks are independent, and later work depends on earlier results. I split into multiple agents only when measured gains in parallelism or capability and context isolation justify the coordination cost.

Anthropic 的模式目录区分固定路径的 workflow 与模型驱动的 agent，并强调模式可以组合，复杂度应由效果而不是新颖程度决定。[下列模式来源于其一手说明。](https://www.anthropic.com/engineering/building-effective-agents)

#### 固定流程：由代码决定控制流

| 模式 | 适用任务 | 机制与例子 |
|---|---|---|
| **提示链（prompt chaining）** | 子任务能按固定顺序拆分 | 摘要 → 抽取实体 → 起草答复；在边界加程序校验，避免错误直接传到下一步。 |
| **路由（routing）** | 输入类别对应不同处理路径 | 分类为退款、售前或技术支持，再交给对应流程。分类不确定时设置兜底或澄清路径。 |
| **并行化（parallelization）** | 子任务彼此独立，或需要多个尝试 | **分片（sectioning）**：同时总结文档不同章节；**投票（voting）**：多次独立评审后按预定义规则汇总。投票会增加调用成本，汇总规则也要针对错误类型评估。 |
| **评估器—优化器（evaluator–optimizer）** | 有清楚的质量标准，反馈确实能改进结果 | 生成代码 → 执行测试 → 根据测试失败修订。设定最大迭代数；若评估器与生成器共享偏差，增加测试或人工依据，不应假设换一个模型就能消除偏差。 |

这些名称表示常见结构，不是互斥的架构类别。路由可以进入提示链；并行工作可以由确定性代码派发；评估循环也可以嵌入较大的智能体任务。

#### 开放式任务：Orchestrator–workers

**编排者—工作者（orchestrator–workers）** 由一个编排者模型在运行时拆分不确定的子任务，派发给工作者，再综合结果。它适合无法事先列出完整子任务的工作，例如根据代码库和需求决定要检查哪些文件；如果任务边界已知，固定并行调用通常更简单。

典型流程：

1. 编排者明确目标与可验证的交付标准。
2. 工作者各自接收范围、必要上下文、权限和结果格式。
3. 可并发的任务同时运行；有依赖的步骤按序等待。
4. 编排者核对结果、处理冲突与缺口，再交付结论。

将工作交给另一个 agent 不会自动带来上下文隔离。要由运行时明确决定共享哪些会话状态、传递哪些证据、工作者可以访问哪些工具，以及主流程接收完整记录还是摘要。相关权衡见[上下文工程原则](#5.%20Context%20Engineering%20Principles%20/%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B%E5%8E%9F%E5%88%99)。

#### 多智能体：委托工具还是交接所有权

主流 SDK 采用不同命名，但可按谁负责最终答复来理解：

| 结构 | 谁保留用户交互控制权 | 适合场景 |
|---|---|---|
| **智能体作为工具（agents as tools）／管理者模式（manager pattern）** | 管理者调用专家，把返回结果纳入自己的答复 | 专家做边界明确的研究、分类或摘要；主 agent 需要比较并综合多个结果。 |
| **交接（handoff）** | 专家接管后续流程或用户对话 | 识别到明确专业领域后，由该专家负责处理。 |

例如，客服分类 agent 可将技术问题交给技术支持 agent；如果客服 agent 还必须比较订单状态、退款政策与支持历史，则可把这些调查工作委托为工具并保留最终答复权。[OpenAI 的编排文档以“交接”与“智能体作为工具”说明了这一控制权区别。](https://developers.openai.com/api/docs/guides/agents/orchestration)

不论哪种结构，都要约定交接输入、输出契约、状态归属、最大交接深度和失败回退。否则专家之间可能反复转交、丢失客户/订单 ID，或对同一副作用重复执行。

#### 什么时候拆分

拆分的理由是具体的任务边界，而不是某个工具数量阈值：

- **独立工作可并行：** 各自读取不同资料，最终可以汇总；确认没有共享写入冲突。
- **需要上下文隔离：** 专家只拿到完成子任务所需信息，主 agent 接收可核验摘要。
- **策略或权限应隔离：** 不同工作者拥有不同的知识范围、工具和访问权限。
- **单个上下文过于混杂：** 实测表明工具重叠、指令冲突或长历史降低了成功率。

额外 agent 会增加模型调用、数据传递、追踪和协调点。开始时先用单 agent 加清晰的工具和上下文；只有离线评估或生产观测显示分拆能改善质量、时延或可靠性，才保留复杂结构。不要把“15 个工具”或其他固定数写成普适分界线。

#### 提示模板仍是单 agent 的选项

面对角色、领域或策略不同但结构相似的任务，可使用一个明确模板传入少量、语义一致的变量，代替维护多份近似提示。变量过多或互相矛盾仍会让提示难以理解；应通过代表性输入评估模板，而不是只检查文本形式。

#### 运行与观测

对每个节点、工具调用、agent、重试与交接记录关联的任务 ID、输入输出引用、状态、延迟、错误与模型/工具用量。结果应能回答：任务是否完成，哪个步骤导致失败，实际执行了几次外部副作用，谁接管了用户流程。日志内容需符合数据保留和隐私要求。

#### 相关知识

- [智能体基础](#7.%20Agent%20Fundamentals%20/%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%9F%BA%E7%A1%80)：工作流与 agent 的控制流边界及运行循环。
- [工具设计与函数调用](#9.%20Tool%20Design%20and%20Function%20Calling%20/%20%E5%B7%A5%E5%85%B7%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%87%BD%E6%95%B0%E8%B0%83%E7%94%A8)：定义被编排结构调用的能力与执行边界。
## 9. Tool Design and Function Calling / 工具设计与函数调用

### Tool Design and Function Calling | 工具设计与函数调用

**核心解释 / Core explanation：** 函数调用（function calling / tool calling）让模型返回一个结构化的工具请求；应用负责校验、授权（authorization）、执行并把结果交回模型。Function calling lets a model return a structured tool request; the application validates, authorizes, executes it, and returns the result to the model.

**30 秒面试回答 / 30-second interview answer**

- **中文：** 工具调用不是模型直接运行代码。模型给出名称和参数后，运行时必须检查结构、权限和业务约束，执行相应函数，再把结果作为观察传回模型。好的工具接口用途明确、输入输出可读、错误可恢复，并针对副作用和重试设计保护。
- **English:** A tool call does not execute code by itself. After the model returns a tool name and arguments, the runtime must validate the shape, permissions, and business constraints, execute the function, and send its result back as an observation. A good tool has a distinct purpose, clear inputs and outputs, actionable errors, and safeguards for side effects and retries.

#### 函数调用的生命周期

以 provider-neutral 形式描述：

1. 应用将对话状态与本轮可用工具定义发送给模型。
2. 模型返回普通内容，或返回包含工具名称与参数的调用请求。
3. 应用解析请求，校验参数，并按当前用户和业务状态授权。
4. 应用执行函数，将成功、错误或部分结果返回模型。
5. 模型依据结果继续调用工具、交接，或生成答复。

[OpenAI 当前 API 指南](https://developers.openai.com/api/docs/guides/function-calling)将工具调用描述为模型请求与应用端执行之间的多步流程。具体消息格式、角色名称、工具选择模式和结构约束因 API 而异。结构化调用或严格 schema 可以减少格式错误，但不证明用户意图正确、权限充分、业务动作合理或外部操作已经成功。

#### 工具选择模式：OpenAI API 示例

OpenAI API 的 `tool_choice` 可控制模型是否以及如何选择函数。下表是该 API 的行为示例，参数名和语义不能直接假定适用于其他 provider：

| 模式 | 行为 |
|---|---|
| `auto` | 默认模式；模型可调用零个、一个或多个函数。 |
| `required` | 要求模型至少调用一个函数。 |
| 指定函数（forced function） | 要求调用某个具体函数，例如 `{"type":"function","name":"get_weather"}`。 |
| `none` | 模拟不提供函数时的行为，不调用函数。 |

并行工具调用是另一个维度：在 OpenAI API 中，`parallel_tool_calls: false` 可将单轮调用限制为零个或一个；支持的模型和组合仍以 API 文档为准。模型返回多个调用请求不等于应用必须并发执行，实际调度仍由运行时按依赖和副作用决定。工具选择也不授予业务权限，执行前仍要做授权检查。

#### 设计工具契约 / Tool contract

不要要求每个工具都填固定数量的说明槽。先确保开发者和模型都能理解以下契约：

| 说明 | 设计问题 |
|---|---|
| **职责与边界** | 这项工具具体完成什么？相似工具的分界在哪里？ |
| **输入** | 每个字段代表什么，格式/单位如何，什么条件下必填？ |
| **结果** | 哪些信息足以支持后续动作？是否需要返回可继续查询的标识符？ |
| **约束与副作用** | 读还是写？执行对象/范围是什么？何时需要确认？ |
| **错误与恢复** | 未找到、权限不足、限流、超时或部分成功时，应返回什么可操作信息？ |

例如，按订单 ID 查看具体内容用 get_order，按客户或时间搜索一批订单用 list_orders。不要让两个工具的用途重叠到只能靠模型猜；在描述中写清何时选择哪一个。字段名应表达业务含义，如 order_id，而不是含糊的 value；示例用真实格式，但不要放入用户数据。

返回结果应只包含下一步决策需要的信息。对于大集合，支持筛选、分页或范围读取，避免把无关数据全部塞回上下文。工具错误应说明发生了什么、是否已产生副作用，以及可安全采取的下一步。Anthropic 的[工具设计经验](https://www.anthropic.com/engineering/writing-tools-for-agents)特别强调清晰用途、低重叠、易读输入输出，以及用任务评估迭代工具设计；命名效果也因模型而异。

#### Schema、说明与业务校验

Schema 是输入输出的结构合同，说明文字则解释语义、格式、单位、相互依赖和操作边界。可以用 required、enum、数值范围、格式约束或提供商支持的严格结构化模式，减少格式错误。不要假设 schema 的 default 字段会由每个 runtime 自动填入；运行时需要明确实现默认值和业务验证。

以部分退款为例，refund_amount 的数值范围可以按订单状态和总额在服务端检查；refund_reason 可以有可选枚举；但“用户是否授权退款”并不是 JSON schema 能验证的。严格输出约束只解决结构层，仍需检查身份、资源归属、当前状态、业务规则和风险阈值。

#### 并发（concurrency）、依赖与副作用

并行有两个不同环节：模型或 API 可以在一个响应中提出多个工具调用；应用运行时决定哪些调用能同时执行。能力因模型和 API 参数而异。[OpenAI 的函数调用文档提供了并行函数调用及关闭该行为的选项](https://developers.openai.com/api/docs/guides/function-calling)，但这不意味着所有调用都适合并发。

- **可并行的只读工作：** 获取客户资料、列出订单、读取支持历史；这些调用互不依赖时可并行，结果齐备后再合并。
- **必须有序的动作：** 核实订单 → 计算退款 → 执行退款 → 确认结果。后一步依赖前一步结果。
- **并发写入：** 涉及同一订单、库存或账户时，要处理竞态、重复提交和部分失败，通常需服务端幂等性（idempotency）、版本条件或事务保护。

网络超时并不能证明写操作失败。给有副作用的动作使用操作 ID 或幂等键；对结果不明的调用先查询状态，再决定是否重试。模型的错误恢复建议是提示，服务端必须定义安全重试策略。

#### MCP 是什么 / Model Context Protocol

[Model Context Protocol（MCP）架构规范](https://modelcontextprotocol.io/docs/learn/architecture)定义了 host、client 与 server 如何发现彼此能力并通信。MCP 数据层基于 JSON-RPC，规范包含 tools、resources、prompts 等原语；传输层处理连接、消息与授权。它为应用发现和调用外部能力提供互操作协议，本身不负责模型推理、业务授权或工具执行质量。

MCP 减少每个 agent 平台都为每个服务单独定义连接协议的重复工作，但不是把所有集成成本从 N×M 自动变成 N+M：每个 server 仍需实现、认证、授权、版本兼容和任务评估。Host 决定暴露哪些能力，运行时仍要控制每个实际调用。

#### 相关知识

- [智能体基础](#7.%20Agent%20Fundamentals%20/%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%9F%BA%E7%A1%80)：工具属于动作空间，但授权必须由运行时执行。
- [编排模式](#8.%20Orchestration%20Patterns%20/%20%E7%BC%96%E6%8E%92%E6%A8%A1%E5%BC%8F)：并行与串行编排取决于任务依赖和副作用。
- [上下文工程原则](#5.%20Context%20Engineering%20Principles%20/%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B%E5%8E%9F%E5%88%99)：工具定义与结果也是模型上下文的一部分。
## 10. LLM Evaluation Methods / 大语言模型评估方法

### LLM Evaluation / 大语言模型评估方法

LLM evaluation measures whether a system meets a defined task contract on relevant examples, using evidence and criteria appropriate to that task. No single score captures task success, truth, source support, relevance, safety, and operating cost.

LLM 评估要先说明系统要完成什么、用哪些样本检验、依据什么判断。任务成功、事实正确、来源支持、相关性、安全性和运行成本是不同问题，不能压成一个分数。

#### Core answer / 核心回答

**English.** Define success for the task, then evaluate representative examples at the retrieval, generation, or agent level where the behavior occurs. Combine objective task checks with source or factual verification, a clearly anchored rubric or calibrated judge where quality is open-ended, and latency/cost measures. Keep a held-out regression set, report the denominator and uncertainty, and use live outcomes alongside offline tests.

**中文。** 先定义任务成功条件，再在检索、生成或 agent 端到端层级评估相关行为。可客观判定的部分用任务指标；开放质量用明确的评分准则或评分量表（rubric）、经人工校准的 judge，并单独核验事实和来源支持；同时记录延迟与成本。保留独立回归集，报告分母与波动，并结合离线测试和线上结果。

#### Define each dimension / 分别定义各评估维度

Faithfulness 和 groundedness 在论文与工具中用法不完全一致。评分准则或评分量表（rubric）应明确评估维度和证据锚点；需要对照真值的任务还应说明 ground truth（参考真值，如外部事实或标注答案）。评估来源忠实度时要指定来源/上下文，评估指令遵循时要列明请求中的约束。RAG 研究常将上下文相关性、答案对上下文的忠实度、答案相关性分别评估；这是有用的拆分方式，不是普遍完整的指标清单。[RAGAS](https://arxiv.org/abs/2309.15217) 与 [ARES](https://aclanthology.org/2024.naacl-long.20/) 使用相近但不完全相同的评估设置。

| Dimension / 维度 | Definition / 定义 | Does not establish / 不能据此推出 |
|---|---|---|
| Task success / 任务成功 | **EN:** Did the result meet explicit acceptance criteria? **中：** 输出是否满足明确的任务验收条件？ | **EN:** That every claim is true or safe. **中：** 不能证明每个说法都真实或安全。 |
| Factual correctness / 事实正确性 | **EN:** Are claims true against an appropriate external reference at the relevant time? **中：** 说法对照适当的外部依据、在相关时间点上是否为真？ | **EN:** That the supplied context supports them. **中：** 不能证明给定上下文支持这些说法。 |
| Source faithfulness or groundedness / 来源忠实度或依据充分性 | **EN:** Are claims supported by the specified source/context, without material contradiction? **中：** 说法是否由指定来源/上下文支持，且没有实质冲突？ | **EN:** That the source is current or correct. **中：** 不能证明来源本身及时或正确。 |
| Relevance / 相关性 | **EN:** Does the answer address the question or requested information? **中：** 答案是否回应问题或所需信息？ | **EN:** That it is correct, supported, or complete. **中：** 不能证明答案正确、有依据或完整。 |
| Instruction adherence / 指令遵循 | **EN:** Did it follow applicable format, scope, and constraints? **中：** 是否遵守适用的格式、范围和约束？ | **EN:** That it is factual. **中：** 不能证明内容属实。 |
| Operational quality / 运行质量 | **EN:** Does it meet latency, availability, and cost requirements? **中：** 是否满足延迟、可用性和成本要求？ | **EN:** That user task goals were met. **中：** 不能证明用户任务目标已达成。 |

“Hallucination / 幻觉”没有统一且公认的分类法。不同综述对 factuality 与 faithfulness 的关系和子类划分并不相同；某篇论文的 taxonomy 不能当作普遍的三分法。评估时应标记可观察的失败及其依据，例如：对照外部依据为假、给定上下文不支持、与上下文冲突，或不遵守指令。指令失败应明确测量；某篇研究是否把它归到 faithfulness 子类，取决于该文定义。[Ji et al., *Survey of Hallucination in Natural Language Generation*](https://arxiv.org/abs/2202.03629)；[Huang et al., *A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions*](https://doi.org/10.1145/3703155)（[arXiv](https://arxiv.org/abs/2311.05232)）。

**合成示例 / Synthetic example。** 给定的服务日程写着 5 月 10 日闭店，但权威的当前通知已将日期改为 5 月 12 日。复述 5 月 10 日的答案忠于给定日程，却在当前事实上错误。回答 5 月 12 日可能符合当前事实，却没有得到该日程支持。应分别评估来源支持与当前事实，并记录参照日期。

#### Choose metrics for the task / 按任务选择指标

| Metric family / 指标类型 | Good fit / 适用条件 | Boundary / 边界 |
|---|---|---|
| Accuracy, exact match, F1, executable tests / 准确率、精确匹配、F1、可执行测试 | 有明确标签、结构化输出或可辩护的预期结果时。代码通过率只说明指定测试集的结果。 | 标签或测试集可能遗漏其他质量维度或合理答案。 |
| BLEU, ROUGE / 参考文本重合度 | 翻译、摘要等任务中，参考文本重合度能作为有用的语料级信号时。BLEU 原用于机器翻译的快速、频繁评估；ROUGE 是一组参考摘要指标。[BLEU](https://research.ibm.com/publications/bleu-a-method-for-automatic-evaluation-of-machine-translation)、[ROUGE](https://aclanthology.org/W04-1013/)。 | 衡量词面重合，不是通用事实性或有用性指标。合理改写可能重合较少；仅有高重合分不能证明答案正确或相关。它们是特定任务工具，并非因历史较久就失效。 |
| Retrieval precision/recall and ranking measures / 检索精确率、召回率与排序指标 | 有相关文档或参考证据标注的检索阶段。Recall@k 可看所需证据是否出现在前 k 项；精确率/排序指标可看返回集合与顺序。 | 结果取决于候选集、相关性标注和 k。检索到相关内容不等于证据完整，也不等于最终答案有依据。 |
| Rubric or model-graded scores / rubric 或模型评审分数 | 没有唯一答案的开放任务，且评价标准可以明确写出并用例子校准时。 | judge 本身也是可能出错的模型；评分不是 ground truth（参考真值）。 |
| Latency, availability, and cost / 延迟、可用性与成本 | 作为运行约束，与任务结果一起报告，用于理解质量与成本的权衡。 | 不能替代任务质量。 |

不要把指标名称当成跨库统一标准。如果使用框架中的 faithfulness、context precision 或 answer relevance 分数，应固定框架版本并检查其输入和 rubric；名称相同的指标也未必可互换。本文不提供框架 API 用法。

#### Evaluate the pipeline at the right level / 在正确层级评估链路

对检索增强系统分阶段评估，才便于定位故障：

1. **Retrieval / 检索：** 候选集合是否包含所需证据？排序是否把它放在系统可用的位置？有相关文档或证据标注时，可据此评估。
2. **Generation given context / 给定上下文后的生成：** 回答是否回应问题、遵守指令、在需要时正确引用，且说法得到上下文支持？如果任务要求事实正确，还要单独核验外部事实。
3. **End-to-end agent / Agent 端到端：** Agent 是否通过合适的动作达到要求的环境状态？评估目标完成、工具/动作是否正确、有无有害副作用，以及延迟或成本。组件分数有助于定位问题，但不能证明端到端成功。像 [AgentBench](https://arxiv.org/abs/2308.03688) 这样的交互式 agent 基准在环境任务中评估 agent，而不只是评分孤立文本回答。

**Offline / 离线评估**用固定样本做受控比较和回归，便于复现；但可能漏掉当前流量、变化中的来源和线上用户结果。**Online / 线上观察或实验**反映部署行为，但结果可能延迟、不完整，或受模型以外因素影响。条件允许时两者结合：用线上证据发现变化与候选案例，经审查并去标识化或合成为适当样例，再纳入有版本记录的离线集。公开教学示例不要包含私人或用户来源数据。

#### LLM judges and human review / 模型评审与人工复核

Judge model 可按 rubric 评分、比较候选答案，或筛出待复核案例。提供问题、相关上下文或参考答案，以及带有可观察评分锚点的标准；要求评委给出评分依据。若要核对验收底线，使用逐项 pass/fail 检查或带明确锚点的评分准则；若问题是相对偏好，可用成对比较。成对比较只回答相对偏好，赢家未必满足验收底线。

研究发现的评委偏差包括位置、冗长偏好和自我偏好，但程度随任务和评委变化。[MT-Bench](https://arxiv.org/abs/2306.05685)、系统性的[位置偏差研究](https://arxiv.org/abs/2406.07791)和关于[自我偏好偏差的研究](https://arxiv.org/abs/2410.21819)说明应在目标评估任务上实际检验评委，不应假定某项缓解措施必然有效。可以随机或交换候选顺序并比较评分，按任务切片抽样复核；多评委或跨 provider 的增益仍需在校准集上验证。它们是诊断手段和可能的缓解措施，不保证评委彼此独立或判断正确。

当标准需要专业知识、任务主观或后果重大，或需要验证自动评委时，应安排人工复核。先用共同样例校准评审者、比较分歧；需要可靠参考结论时，对分歧案例进行裁定。一致性表示评审者在 rubric 下较一致，不代表 rubric 或标签正确。Judge 与单个人的分数一致，也不能单独证明 judge 准确。

需要外部事实时，尽可能对照适当、可信且及时的依据。评估来源忠实度时，应对照指定的上下文检查说法。NLI 分类器、再次检索和 self-consistency 可帮助筛选待检查内容，但都可能出错：多次回答一致不能证明为真，二次检索也可能返回过期或不相关来源。应报告检查了什么、依据何在，而不要把检测器分数写成事实已核实。

#### Build a comparable regression set / 建立可比较的回归集

- 定义符合条件的任务总体，并抽取常见样本、重要切片和已知失败类型。记录样例如何选择、标注和版本化；方便取得的样例集不一定有代表性。
- 将开发样例与用于最终比较的独立保留集分开，避免反复针对保留集调优。记录模型、提示词、检索语料/配置、评委和 rubric 的版本。
- 明确分母。例如，报告“所有符合条件的尝试中成功完成任务的比例”，并单独报告回答覆盖率。若任务要求拒答，正确拒答计为成功；未回答或不当拒答也应作为结果保留。如果 faithfulness 只在已回答样本上计算，应标明这是“已回答样本中的条件分数”，并同时报告回答覆盖率或任务完成率。
- 在相同协议下与基线比较。对于随机输出，重复足够次数以观察有实际意义的波动；报告样本数与不确定性，不要把微小分差说成确定结论。ARES 展示了一种将自动评委、人类标注样例与统计估计结合的方法，但不是每种评估都必须采用。[ARES](https://aclanthology.org/2024.naacl-long.20/)；另见 [Towards Reproducible LLM Evaluation](https://www.turing.ac.uk/sites/default/files/2025-11/towards_reproducible_llm_evaluation.pdf)。
- 只让快速检查拦截它有能力发现的问题；根据变更风险安排更完整的评估。线上失败在原因查明、数据适合保留后可进入回归集；盲目加入每起事件会造成重复、数据泄漏或隐私风险。

#### Use public benchmarks as evidence, not a deployment proxy / 公共基准是证据，不是上线代理

当任务、协议、模型访问方式和计分规则与问题相符时，公共基准可支持受控比较。像 [HELM](https://arxiv.org/abs/2211.09110) 这样的广泛评估也显示了多种场景与指标的价值；但它们不会自动代表某个具体部署任务。

检查基准覆盖范围、评估协议以及训练数据污染的可能性。污染测量及其影响取决于基准、模型和测量方法；分数提高或小幅上涨本身不能证明模型记住了测试集。[Sainz et al.](https://arxiv.org/abs/2310.18018)；[Singh et al.](https://arxiv.org/abs/2411.03923)。可用公开结果缩小候选范围，再用有代表性、记录版本且带独立保留集的任务样本比较入选系统。

#### Related notes / 相关笔记

- [RAG architecture and implementation](#6.%20Retrieval-Augmented%20Generation%20%28RAG%29%20/%20%E6%A3%80%E7%B4%A2%E5%A2%9E%E5%BC%BA%E7%94%9F%E6%88%90) — 了解检索、证据组装和生成机制，对应本文的 RAG 评估阶段。
- [AI safety in production](#12.%20AI%20Safety%20in%20Production%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84AI%E5%AE%89%E5%85%A8) — 了解需要单独设计任务检查的安全边界和生产控制。

#### Sources / 来源

关键定义与主张已在正文链接一手研究。补充来源：

- Liang et al., [*Holistic Evaluation of Language Models*](https://arxiv.org/abs/2211.09110).
- Zheng et al., [*Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*](https://arxiv.org/abs/2306.05685).
- Xia et al., [*Evaluation-Driven Development and Operations of LLM Agents: A Process Model and Reference Architecture*](https://arxiv.org/abs/2411.13768) — 提出连接离线与线上评估的流程模型，并不保证两者分数一致。
## 11. Fine-tuning Strategies / 微调策略

### Fine-tuning Strategies / 微调策略

**Core explanation / 核心解释：** Fine-tuning updates a pretrained model using examples or preferences to change task behavior. It is worth testing when a repeatable behavior gap remains after prompt, context, retrieval, and workflow improvements. It is not a reliable database for fresh or access-controlled facts; choose the method and data through held-out evaluation and account for training, serving, and maintenance. / 微调用示例或偏好更新预训练模型，以改变特定任务行为。当提示词、上下文、检索和工作流改进后仍存在稳定的行为差距，才值得评估微调。它不是可靠的实时或权限控制数据库；应通过保留集评估选择方法和数据，并计入训练、部署及维护成本。

**Key terms / 关键术语：** supervised fine-tuning (SFT) / 监督微调；LoRA / 低秩适配；QLoRA / 量化低秩适配；preference optimization / 偏好优化；RLHF / 基于人类反馈的强化学习；DPO / 直接偏好优化。

#### Should you fine-tune, or use prompting and retrieval? / 应微调，还是使用提示和检索？

First identify the error. Missing or changing facts call for an authoritative data source and retrieval or a direct API. Unclear instructions may be fixed with a prompt or workflow. A persistent style, label convention, or response pattern may be suitable for fine-tuning if examples can teach it and evaluation confirms the gain. These are useful starting points, not mutually exclusive categories.

Fine-tuning does not make facts stored in weights reliably addressable, current, or permission-aware. Retrieval still needs source freshness, access checks, and evidence validation. A fine-tuned model can also be paired with retrieval. [RAG Architecture and Implementation / 检索增强生成](#6.%20Retrieval-Augmented%20Generation%20%28RAG%29%20/%20%E6%A3%80%E7%B4%A2%E5%A2%9E%E5%BC%BA%E7%94%9F%E6%88%90) covers external evidence; [LLM Evaluation Methods / 大语言模型评估方法](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95) covers task evaluation.

Before training, compare a prompt-only baseline and any relevant retrieval or workflow baseline. Consider fine-tuning when the remaining gap is repeatable, the training data represents the target behavior, and the expected improvement justifies training, deployment, and future update work.

#### Which method should you choose? / 如何选择微调方法？

- **Full fine-tuning / 全量微调：** updates the base model's trainable weights. It offers broad adaptation capacity, with higher memory, compute, and artifact costs.
- **LoRA / 低秩适配：** freezes the base weights and trains low-rank matrices for selected weight updates. This reduces the number of trainable parameters; resulting quality and memory needs depend on model, rank, target modules, data, and training setup.
- **QLoRA / 量化低秩适配：** keeps a quantized base model frozen while training LoRA adapters. The QLoRA paper studies 4-bit quantization and memory-saving methods in a specific experimental setup; quantization and adapter choices still require task evaluation.
- **Adapters / 适配器：** add small trainable modules, often bottleneck layers within Transformer blocks, while the main model weights stay frozen.
- **Prefix tuning / 前缀微调：** learns continuous task-specific vectors that are supplied as prefix representations at Transformer layers; these are not ordinary visible text tokens.
- **Prompt tuning / 软提示微调：** learns a small set of continuous input-embedding vectors prepended to the input while keeping the model frozen. This differs from prompt engineering, which edits ordinary instruction text.

These methods alter different parts of a model's computation and have different trainer and serving support. Their results depend on the model, task, and implementation; compare them by evaluation rather than assuming one dominates.

A common LoRA parameterization writes an update as a product of two low-rank matrices:

$$
W' = W + \Delta W,\qquad \Delta W = BA
$$

Here, if W maps from input dimension k to output dimension d, A can have shape r × k and B shape d × r, with rank r smaller than k and d. This is a schematic form; implementations may scale or target different modules. Some serving stacks can merge adapters into the base weights, while other configurations keep adapter operations at inference. Verify the target stack instead of assuming zero latency overhead.

**One-matrix count illustration / 单个矩阵参数量示例:** Suppose one target projection is 4096 × 4096 and r = 8. The two LoRA matrices contain r(k + d) = 8(4096 + 4096) = 65,536 trainable values, while the original dense matrix has dk = 4096 × 4096 = 16,777,216 values. This compares one adapted matrix only; a model's total depends on how many layers and matrices are targeted, and the count alone predicts neither quality nor the whole model's trainable-parameter fraction.

There is no universal rank, method, or “default” that guarantees quality. Compare feasible approaches using the same data splits, task metrics, deployment constraints, and base model.

#### How much and what kind of data? / 需要多少数据，数据应是什么样？

There is no general example count that predicts success. A small clean set may reveal whether a behavior is learnable, while broader or rarer cases may need more coverage. Track which behaviors and input patterns each example represents; do not treat raw volume as evidence of quality.

Possible supervised example / 监督样例:

~~~json
{
  "messages": [
    {"role": "user", "content": "Summarize this sample clause: The supplier will deliver the parts by June 1."},
    {"role": "assistant", "content": "The supplier must deliver the parts by June 1."}
  ]
}
~~~

This is synthetic demonstration data, not legal advice or a recommended training format for every API. Follow the chosen trainer's current format and include only data you are authorized to use.

Review data for correctness, representative coverage, consistent labels, duplicates, sensitive information, and rights to use. Split training and evaluation data to reduce leakage; near-duplicates or examples from the same source can make a nominally held-out score misleading. Synthetic examples can expand coverage, but verify them because generation can introduce unsupported facts, errors, and bias.

#### A training and evaluation workflow / 训练与评估流程

1. **Define the failure and success criteria.** Record the current behavior, target behavior, operational constraints, and unacceptable regressions.
2. **Build and review examples.** Remove duplicates and unauthorized or sensitive material; check labels and coverage.
3. **Create separated data splits.** Separate training and validation examples, and reserve a representative final test set until the method and training controls are fixed. Document the split method and known leakage risks.
4. **Choose a base model and method.** Confirm current training support, data format, license or service terms, and serving compatibility.
5. **Train and tune a baseline experiment.** Track the learning rate and schedule, epoch count, effective batch size, gradient accumulation, training-data version, checkpoints, and validation results. These are experiment-specific controls, not portable defaults.
6. **Compare with the untuned baseline.** Use validation cases for iterative comparisons; after choices are fixed, compare the selected model with the baseline on the untouched test set. Report quality by important slices, format and tool behavior, safety outcomes, and regressions.
7. **Deploy cautiously and monitor.** Version the model and rollback path; monitor the same outcomes on real traffic, respecting data retention and consent rules.

A successful training job only shows that optimization ran. It does not establish better generalization. Do not call a score gain “memorization” or “generalization” without checking data overlap, task slices, and independent evidence.

The **learning rate** sets the scale of optimizer updates; a rate that is too large for a setup can destabilize learning, while one that is too small can fail to adapt within the chosen training budget. **Epochs** count passes over the training examples; more passes may improve fit or begin to overfit. **Batch size** controls how many examples contribute to an optimizer update, with memory and gradient-variance tradeoffs; gradient accumulation can change the effective batch without changing the per-device batch.

Use training data to fit weights, a validation split to compare training controls and support early stopping, and a final held-out test set only after choices are fixed. Repeatedly selecting against the final test set leaks it into development. Compare task outcomes and important slices against the untuned baseline; training and validation loss are useful signals, not substitutes for the target behavior.

#### What are SFT, RLHF, and DPO? / 什么是 SFT、RLHF 与 DPO？

**Supervised fine-tuning (SFT)** trains on desired responses or demonstrations. It can teach response patterns represented by the examples; it does not guarantee that the model follows every instruction or is safe in unseen situations.

In the InstructGPT research pipeline, human-written demonstrations were used for supervised fine-tuning, human preference comparisons trained a reward model, and reinforcement learning optimized the policy against that reward. This describes that paper's method, not every assistant model's training process.

**Direct Preference Optimization (DPO)** is a preference-learning method that optimizes from chosen and rejected responses without fitting a separate reward model in the same way as the classic RLHF pipeline. It still depends on preference data, a training objective, and modeling assumptions; it is not automatically more accurate or safer than PPO. Choose based on the available data, infrastructure, and evaluation.

Preference labels can be inconsistent or reflect the annotators and rubric. Evaluate the resulting model for the intended task and relevant failure cases; do not infer safety from a preference-training label alone.

#### Related notes / 相关笔记

- [RAG Architecture and Implementation / 检索增强生成](#6.%20Retrieval-Augmented%20Generation%20%28RAG%29%20/%20%E6%A3%80%E7%B4%A2%E5%A2%9E%E5%BC%BA%E7%94%9F%E6%88%90) covers retrieval for external and changing evidence.
- [LLM Evaluation Methods / 大语言模型评估方法](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95) covers held-out evaluation and failure analysis.
- [AI Safety in Production / 生产环境中的 AI 安全](#12.%20AI%20Safety%20in%20Production%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84AI%E5%AE%89%E5%85%A8) covers runtime controls that training does not replace.

#### Sources / 来源

- Hu et al., [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685).
- Dettmers et al., [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314).
- Houlsby et al., [Parameter-Efficient Transfer Learning for NLP](https://arxiv.org/abs/1902.00751); Li and Liang, [Prefix-Tuning](https://arxiv.org/abs/2101.00190); Lester et al., [The Power of Scale for Parameter-Efficient Prompt Tuning](https://arxiv.org/abs/2104.08691).
- Ouyang et al., [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155).
- Rafailov et al., [Direct Preference Optimization: Your Language Model is Secretly a Reward Model](https://arxiv.org/abs/2305.18290).
- OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), [Supervised fine-tuning](https://developers.openai.com/api/docs/guides/supervised-fine-tuning), [Direct preference optimization](https://developers.openai.com/api/docs/guides/direct-preference-optimization), and [Deprecations](https://developers.openai.com/api/docs/deprecations), checked 2026-10-15. The SFT/DPO pages describe OpenAI-specific methods, not general availability: the optimization page marks fine-tuning docs as legacy and says the platform is winding down. The deprecations page says organizations that had not previously run fine-tuning cannot create jobs; since 2026-07-02, organizations that have not run inference on a fine-tuned model in the prior 60 days also cannot create jobs. Active existing customers lose job creation on 2027-01-06, while inference continues until the base model is deprecated. Check current availability before treating OpenAI API fine-tuning as an option.
## 12. AI Safety in Production / 生产环境中的AI安全

### AI Safety in Production / 生产环境 AI 安全

**Definition / 定义.** Production AI safety is the application’s ability to limit harm when a model is wrong, manipulated, or asks to perform an unauthorized action. A model response is a proposal; the application and its runtime decide what data it may access, what actions may execute, and when execution must stop.  
生产环境 AI 安全，是指模型出错、受诱导或提出未授权动作时，应用能够限制实际影响。模型输出只是候选内容或动作；应用运行时负责决定数据访问、动作执行和停止条件。

**Key terms / 关键术语**

| Term / 术语 | Meaning / 含义 |
|---|---|
| **Prompt injection / 提示注入** | Untrusted content changes model behavior against the intended task or data boundary. / 不可信内容使模型行为偏离预期任务或数据边界。 |
| **Direct / indirect injection / 直接 / 间接注入** | The instruction arrives in the user’s own input, or in supplied content such as a document or tool result. / 指令来自用户输入，或嵌在随后提供的文档、工具结果等内容中。 |
| **Trust boundary / 信任边界** | Where the application independently decides whether data, a request, or an action is trusted or authorized. / 应用独立判断数据、请求或动作是否可信或已获授权的位置。 |
| **Least privilege / 最小权限** | Give each tool and execution environment only the data and capabilities required for its task. / 只向工具和执行环境提供完成任务所需的数据与能力。 |
| **Human handoff / 人工接管** | Pause a task and provide only the evidence and decision needed for a person to continue safely. / 暂停任务，仅提供人工安全继续处理所需的证据和待决事项。 |
| **Red teaming / 红队测试** | Adversarial testing that probes this application’s data and action boundaries. / 针对本应用数据与动作边界进行的对抗性测试。 |

**Interview answer / 面试简答.**  
**English:** I treat user and retrieved content as untrusted, and treat model tool calls as candidate requests whose authorization the application checks before execution. The application validates outputs for their next consumer, limits execution capabilities, and keeps a stop path outside the model loop. I test those boundaries against direct and indirect injection, review high-impact actions, and turn confirmed failures into regression cases.  
**中文：**我把用户输入和检索内容视为不可信数据，把模型工具调用视为候选请求，由应用校验授权后执行。应用按接收方校验输出、限制执行能力，并在模型循环外保留停止路径。我会针对直接和间接注入测试这些边界，对高影响动作设置人工介入，并将确认的问题加入回归集。

#### Threats and failure modes / 威胁与失效方式

A fluent answer can still be false or unsupported. Retrieval can provide useful evidence, but does not guarantee the model will use it correctly; retrieved text also does not grant permission to act. This note focuses on the resulting safety boundary. See [LLM Evaluation Methods](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95) for factuality and support measurement, and [RAG Architecture and Implementation](#6.%20Retrieval-Augmented%20Generation%20%28RAG%29%20/%20%E6%A3%80%E7%B4%A2%E5%A2%9E%E5%BC%BA%E7%94%9F%E6%88%90) for retrieval behavior. NIST describes confabulation as a GenAI risk; it does not treat grounding as a correctness guarantee ([NIST AI 600-1, §2.2](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)).

Prompt injection does not require a successful “system prompt override.” It is enough for untrusted content to alter behavior in a way that violates the intended task or data boundary. OWASP LLM01:2026 covers direct and indirect inputs, including user content, retrieved material, tool output, multimodal content, and persistent memory ([LLM01:2026 Prompt Injection](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM01_PromptInjection.md)).

| Path | Where the instruction comes from | Example |
|---|---|---|
| **Direct injection / 直接注入** | The user’s message. | A user asks the assistant to ignore the task and send a report to an unrelated destination. |
| **Indirect injection / 间接注入** | A document, webpage, image, or tool result supplied as data. | A retrieved page contains instructions to forward the conversation instead of being summarized. |

Separating instructions from quoted or retrieved content can reduce confusion, but prompts, string filters, and classifiers are not reliable authorization or execution boundaries. A filter may detect some attacks; it cannot decide whether a user owns a record or constrain a process’s filesystem and network access.

If an application writes user or retrieved content into persistent memory, that content can influence later sessions. Treat this as a conditional risk for systems with durable memory, not a requirement for every LLM application; OWASP discusses persistent memory as an injection surface and poisoning risk ([LLM01:2026](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM01_PromptInjection.md), [LLM05:2026 Data and Model Poisoning](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM05_DataModelPoisoning.md)). The test section gives one minimal cross-session regression case.

#### Trust boundaries and runtime controls / 信任边界与运行时控制

Treat a tool call as a request from the model, not as authorization. Before any side effect, the application should check the authenticated caller, target resource, requested scope, current business state, and any required approval. Repeat the check for each operation, including reads. Use narrowly scoped tools and credentials; an allowlist or valid JSON shape alone does not prove that the caller may perform the action. OWASP LLM03:2026 describes least privilege, user-context execution, and code-enforced mediation as controls for excessive agency ([LLM03:2026 Excessive Agency](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md)).

| Control / 控制措施 | Role / 作用 | Boundary / 边界 |
|---|---|---|
| **Prompt, filter, or classifier (content guardrail) / 提示词、过滤器或分类器（内容护栏/防护措施）** | Flags or reduces some risky inputs and outputs. / 标记或降低部分风险输入与输出。 | Does not authorize resource access or isolate execution. / 不负责资源授权或执行隔离。 |
| **Authorization / 授权** | Checks whether this caller may perform this action on this resource now; enforce it on every operation. / 逐次检查当前调用者能否对目标资源执行该动作。 | A model-selected tool or allowlist is not authorization. / 模型选择的工具或白名单本身不是授权。 |
| **Output validation / 输出校验** | Checks structure and business constraints, then encodes or sanitizes for the next consumer. / 校验结构与业务约束，并按下游接收方编码或净化。 | Does not prove factual truth or authorization, and does not isolate execution. / 不证明事实正确或授权成立，也不等于执行隔离。 |
| **Sandbox / 沙箱（执行隔离环境）** | When code runs, limits its actual filesystem, mounts, network, and credentials. / 代码运行时限制其实际文件系统、挂载、网络与可用凭据。 | Does not authorize business actions; its boundary depends on configuration. / 不负责业务授权，隔离范围取决于实际配置。 |

**Moderation / 内容审核** applies the application’s content policy; **data minimization or redaction / 数据最小化或脱敏** removes sensitive fields that are not needed from inputs or outputs. These constrain content, but do not grant access or replace context-specific output encoding. / 内容审核按应用策略限制内容；数据最小化或脱敏会从输入或输出中移除不必要的敏感字段。它们不授予访问权限，也不能替代针对下游语境的输出编码。 NIST describes privacy risks from GenAI data collection and processing (§2.4, [AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)).

High-impact or hard-to-reverse actions should pause for approval tied to the exact action and target. After approval, the application still rechecks authorization and business state before execution. Keep secrets outside model-visible content and execution environments where possible; sandbox protections depend on actual mounts, network rules, and credential exposure ([OpenAI Sandbox Agents](https://developers.openai.com/api/docs/guides/agents/sandboxes), [Sandbox security](https://developers.openai.com/api/docs/guides/agents-api/environments/security)). For tool schemas and execution contracts, see [Tool Design and Function Calling](#9.%20Tool%20Design%20and%20Function%20Calling%20/%20%E5%B7%A5%E5%85%B7%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%87%BD%E6%95%B0%E8%B0%83%E7%94%A8).

#### Stop and hand off / 停止与人工接管

Pause for a person when a configured failure threshold is reached, the requested resource or scope is unclear, a tool behaves unexpectedly, or an action’s impact warrants approval. A model’s own confidence statement is not a calibrated signal unless it has been validated for that use. OpenAI’s agent guide gives repeated failures and high-risk actions as examples of human-intervention triggers ([A Practical Guide to Building Agents, pp. 30–31](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)).

A handoff should include only what the reviewer needs: the user’s request, relevant evidence and its source, actions attempted and their results, and the decision still needed. Exclude credentials and unrelated sensitive context. Operational logs and traces should likewise contain only what is needed to investigate actions and outcomes, with access limited appropriately; NIST identifies privacy risks from GenAI data collection and processing (§2.4). Pause any pending side effect until the authorized decision is made.

The application needs a stop path outside the model loop. It should be able to stop new tool calls and retries, cancel an active run, and revoke or disable the affected capability. A prompt telling the model to stop is not a kill switch. Before resuming, reconcile actions that already completed and verify the current state. NIST AI 600-1 calls for post-deployment monitoring, incident response and recovery, and the ability to disengage or deactivate systems when outcomes are inconsistent with intended use (§§ MANAGE 2.3, 2.4, 4.1).

#### Test and monitor the boundaries / 测试与监控边界

Red teaming explores ways an attacker could cross this application’s specific data and action boundaries. Evaluation measures known cases; production monitoring observes what actually happened; none replaces the others. Test before release, after material changes to models, prompts, tools, data sources, or permissions, and after relevant incidents. NIST AI 600-1 calls for empirical evaluation and ongoing monitoring; the [Evaluation note](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95) covers measurement and regression design.

Keep regression cases tied to the application’s actual capabilities:

- **Direct injection:** a user asks for an action outside their granted scope; verify the runtime denies it even if the model proposes it.
- **Indirect injection:** retrieved content or a tool result asks the model to exceed the task; verify it cannot authorize a side effect.
- **Sensitive output and content policy (no tools required):** put a synthetic protected field in an isolated test context, request its disclosure, and separately test a policy-disallowed content prompt; verify the field is not revealed and the configured moderation behavior applies. Use no real personal data.
- **Output handling:** content that could be interpreted as markup or an instruction by the next consumer is safely handled there. OWASP LLM10:2026 recommends validating and sanitizing model output before downstream use ([LLM10:2026 Improper Output Handling](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM10_ImproperOutputHandling.md)).
- **Persistent memory, if present:** add a harmless injected instruction to isolated test memory; verify a later session cannot use it to trigger a restricted action or cross its intended scope, then delete the record and confirm its effect is gone.

Red-team findings should record the attack path, whether an unauthorized action or disclosure occurred, and the fix. Add a minimized case to regression tests when appropriate. In production, monitor tool invocations and denials, unexpected state changes, repeated failures, human overrides, and reports of harm; use these signals to investigate and update tests rather than treating any single rate as a target.
## 13. AI Application Architecture / AI应用架构

### AI Application Architecture / AI 应用架构

**Core explanation / 核心解释：** A production LLM application is a software system around a model call: it manages identity, context, tools, validation, timeouts, retries, cost, monitoring, and recovery. Choose optimizations and deployment boundaries from measured quality, workload, privacy, and operations requirements. / 生产级 LLM 应用是围绕模型调用构建的软件系统，需要管理身份、上下文、工具、校验、超时、重试、成本、监控与恢复。应根据实测质量、工作负载、隐私和运维要求选择优化与部署边界。

**Key terms / 关键术语：** latency / 时延；time to first token (TTFT) / 首 token 时延；routing / 路由；caching / 缓存；fallback / 回退；observability / 可观测性；feedback loop / 反馈闭环。

#### What changes from prototype to production? / 从原型到生产会发生什么变化？

A prototype tests whether an approach can solve a task. A production service must also handle concurrent users, malformed or incomplete responses, provider and tool failures, changing inputs, permissions, privacy, cost, and rollback. Design the surrounding controls before relying on the model in a consequential workflow.

~~~text
Request → authenticate and authorize → assemble context
        → model and/or tools → validate result → respond or escalate
        ↘ trace, metrics, and privacy-reviewed logs
~~~

For tool use, the application receives a proposed call and executes it only after its own argument checks and authorization. A model response or schema-constrained output does not itself grant access or establish that an action is valid. See [Tool Design and Function Calling / 工具设计与函数调用](#9.%20Tool%20Design%20and%20Function%20Calling%20/%20%E5%B7%A5%E5%85%B7%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%87%BD%E6%95%B0%E8%B0%83%E7%94%A8) and [AI Safety in Production / 生产环境中的 AI 安全](#12.%20AI%20Safety%20in%20Production%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84AI%E5%AE%89%E5%85%A8).

Useful production controls include explicit timeouts, bounded retries, idempotency for retried writes, cancellation, rate and budget limits, an error path, and a way to disable or roll back a model or prompt version. Retry only failures that can safely be retried; a timeout does not prove a write did not happen.

#### How can you reduce latency and cost? / 如何降低时延与成本？

First measure where time and cost accumulate: queueing, context assembly, retrieval, model input/output, tools, and retries. Then test a change against a fixed quality bar; savings that break the task are not an optimization.

- **Shorten or select context / 缩短或筛选上下文：** include relevant material and limit unnecessary history. Measure for lost evidence or task quality; see [Context Engineering Principles / 上下文工程原则](#5.%20Context%20Engineering%20Principles%20/%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B%E5%8E%9F%E5%88%99).
- **Use caching / 使用缓存：** exact-response or semantic caches can avoid work for repeat requests, but require freshness, permission, and key-isolation rules. For example, “What is the refund policy in the US?” and “What is the refund policy in the EU?” can have similar embeddings but different correct answers. Include relevant locale, tenant, permission, and policy-version boundaries in cache design; semantic similarity alone is not proof that a response is reusable.
- **Route requests / 请求路由：** use a lower-cost candidate only for cases where it meets the measured quality bar. Include classifier errors, added latency, fallback frequency, and maintenance in the comparison. See [Model Selection and Ecosystem / 模型选择与生态](#2.%20Model%20Selection%20and%20Ecosystem%20/%20%E6%A8%A1%E5%9E%8B%E9%80%89%E6%8B%A9%E4%B8%8E%E7%94%9F%E6%80%81).
- **Inference batching / 推理批处理：** a serving engine can combine work from concurrent requests into accelerator batches. Iteration-level or continuous batching can admit and retire sequences between token-generation steps, improving hardware utilization and aggregate throughput on suitable workloads. Queueing and batch formation can add per-request delay, so measure throughput, queue time, and latency together. This is distinct from an asynchronous provider Batch API, where requests are submitted as a job and results arrive later; that interface is for work that tolerates delayed completion, not a promise about how an inference engine batches live traffic.
- **Quantization / 量化：** represent weights, and in some methods activations, with fewer bits. This can reduce model memory and data movement, and may improve inference speed when the hardware and kernels support the chosen format. Quantization error can affect task quality, and lower precision does not guarantee faster end-to-end service; evaluate the exact model, quantizer, hardware, and workload.
- **Distillation / 蒸馏：** train a smaller student on outputs or softened targets from a larger teacher over chosen inputs. A student may reduce serving cost or latency, but can lose capabilities or fail outside the distillation set. Include teacher/data generation and evaluation in the cost, and test the student on held-out tasks before replacing the teacher.
- **Stream responses / 流式返回：** streaming can improve perceived responsiveness and time to first token; it does not necessarily reduce total generation time or work.

Provider features such as prompt caching, batch jobs, context limits, and pricing vary by model and API and can change. Verify current documentation for the exact deployment. Compare total cost, including inference, retrieval, storage, engineering, evaluation, and operations.

##### A teaching calculation for cache cost / 缓存成本教学算例

Assume 1,000 model calls, each with 1,000 input tokens and 200 output tokens. For this arithmetic example only, assume uncached input costs $2 per million tokens, cached input costs $1 per million, and output costs $8 per million. These are invented teaching values, not current provider prices; ignore cache-write, storage, retrieval, and other fees.

Without caching, the token charge is 1,000 × [(1,000 × $2) + (200 × $8)] / 1,000,000 = $3.60.

Suppose 400 calls share a 500-token prompt prefix and receive the assumed cached-input rate for that prefix. Prompt caching still processes the remaining input and generates all 200 output tokens. The assumed token charge becomes 600 × $0.0036 + 400 × [$0.0005 + $0.001 + $0.0016] = $3.40: the $0.20 saving comes only from the lower rate on 400 × 500 cached input tokens. The output is still generated and billed.

An application-level response-cache hit is different: if 400 requests can safely reuse an exact, current response, those requests skip the model call, so the remaining 600 model calls cost 600 × $0.0036 = $2.16 in token charges, before cache infrastructure costs. This calculation assumes a valid exact response hit; a semantic cache needs its own correctness and authorization checks. OpenAI's current [prompt caching documentation](https://developers.openai.com/api/docs/guides/prompt-caching), checked 2026-10-15, likewise describes reuse of a prompt prefix while the model still generates a new response; its supported models, rates, and cache rules are provider-specific and change.

#### How should an application monitor behavior? / 应用应监控哪些行为？

Track technical operation and task outcomes together. Useful measures include latency distributions and TTFT, throughput and queue time, errors and timeouts by stage, input/output usage, cost per completed task, tool success and authorization denials, cache hit correctness, task completion, escalation, and user feedback.

Set thresholds from the service's requirements and baseline; no universal error-rate or latency threshold fits every application. Record prompt, model, and relevant configuration versions so a change can be investigated. Keep logs proportionate: redact or avoid sensitive content and apply retention controls. Use sampled traces or derived metrics where full payload logging is unnecessary.

Model behavior, external data, prompts, and provider implementations can change. Re-run an evaluation set when a material component changes and compare results by important task slices; see [LLM Evaluation Methods / 大语言模型评估方法](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95). Maintain a rollback or fallback path when a release violates the product's agreed quality bar.

#### How can feedback improve the product? / 如何让反馈改进产品？

Collect explicit signals such as ratings or corrections and implicit signals such as task completion, accepted suggestions, repeated requests, and escalation. These signals are incomplete and biased: a rating reflects who chose to respond, while time spent can indicate either engagement or confusion. Interpret them alongside representative task evaluation and user research.

A practical loop is:

1. Capture feedback with the relevant task and version context, subject to privacy and retention rules.
2. Review a sample and classify the failure mode.
3. Fix the appropriate layer: source data, retrieval, prompt, tool, model choice, interface, or policy.
4. Test the change on held-out cases and monitor the relevant production outcome.
5. Keep or roll back the change based on the agreed criteria.

Preference data may inform fine-tuning or preference optimization, but a feedback button alone does not create a validated training signal. See [Fine-tuning Strategies / 微调策略](#11.%20Fine-tuning%20Strategies%20/%20%E5%BE%AE%E8%B0%83%E7%AD%96%E7%95%A5).

#### API, self-hosted, edge, or hybrid — how do you pick a deployment pattern?

Compare the same workload and quality bar across patterns, including data flow, service terms, operations, peak capacity, update ownership, and failure recovery.

| Pattern | Useful when | Costs and constraints |
|---|---|---|
| **Hosted API / 托管 API** | Managed inference and quick iteration fit the task. | Provider terms, model lifecycle, feature support, rate limits, availability, and per-use costs need review. |
| **Self-hosted / 自托管** | Control over serving location, version, and infrastructure is a real requirement. | The team owns capacity, scaling, security updates, model serving, observability, and on-call response. |
| **Edge / 端侧** | Offline use, local latency, or device-level data handling matters. | Compute, battery, memory, device coverage, updates, and supported model size constrain the design. |
| **Hybrid / 混合** | Distinct workloads need different data or serving boundaries. | Routing and duplicated operations add complexity; define fallback and consistent policy behavior. |

A useful comparison is:

$$
\text{total cost} = \text{inference} + \text{compute and storage} + \text{engineering and operations} + \text{evaluation and controls}
$$

There is no universal spend threshold for switching to self-hosting. Estimate with actual traffic, peak demand, staffing, quality requirements, and the full operating burden. Edge and hybrid choices likewise depend on device and data constraints, not just latency labels.

#### Related notes / 相关笔记

- [Model Selection and Ecosystem / 模型选择与生态](#2.%20Model%20Selection%20and%20Ecosystem%20/%20%E6%A8%A1%E5%9E%8B%E9%80%89%E6%8B%A9%E4%B8%8E%E7%94%9F%E6%80%81) covers candidate comparison and routing.
- [Context Engineering Principles / 上下文工程原则](#5.%20Context%20Engineering%20Principles%20/%20%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B%E5%8E%9F%E5%88%99) covers context budgets and caching.
- [LLM Evaluation Methods / 大语言模型评估方法](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95) covers offline and production evaluation.
- [AI Safety in Production / 生产环境中的 AI 安全](#12.%20AI%20Safety%20in%20Production%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84AI%E5%AE%89%E5%85%A8) covers runtime boundaries and controls.

#### Sources / 来源

- OpenAI, [Function calling](https://developers.openai.com/api/docs/guides/function-calling), checked 2026-10-15. Tool calls are proposed by the model and handled by application code.
- OpenAI, [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs), checked 2026-10-15. Schema adherence applies to supported schemas and models; semantic validation and failure handling remain application concerns.
- OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), checked 2026-10-15. Current capabilities and recommendations are API-specific and may change.
- Frantar et al., [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers](https://arxiv.org/abs/2210.17323); Lin et al., [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration](https://arxiv.org/abs/2306.00978).
- Hinton et al., [Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531).
- Yu et al., [Orca: A Distributed Serving System for Transformer-Based Generative Models](https://www.usenix.org/conference/osdi22/presentation/yu), for iteration-level scheduling and selective batching. OpenAI, [Batch API](https://developers.openai.com/api/docs/guides/batch), checked 2026-10-15, documents its separate asynchronous job interface.
## 14. AI System Design Interview Questions / AI系统设计面试题

### AI System Design Interview Questions / AI 系统设计面试题

Capstone: a reusable way to scope AI system design problems, compare alternatives, and explain three illustrative designs. The Q&A budget and traffic values below are explicitly hypothetical teaching assumptions, not production measurements or universal defaults. / 本篇提供 AI 系统设计题的通用拆解方法、权衡维度，以及三个示例方案。下方问答系统的时延与流量数字是明确标注的教学假设，并非生产测量值或通用默认值。

**Key terms / 关键术语：** requirements / 需求；data flow / 数据流；failure mode / 失败模式；trade-off / 权衡；evaluation / 评估；rollback / 回滚。

#### How should you structure an AI system design answer? / 如何组织 AI 系统设计回答？

Use the following sequence as a set of discussion slots, not a fixed interview timetable:

1. **Clarify the task.** Identify users, inputs and outputs, success criteria, unacceptable errors, data sensitivity, freshness, and human review needs.
2. **Establish constraints.** Ask about expected workload and peaks, latency and availability goals, budget, deployment boundary, existing systems, and operational ownership. State assumptions when information is unavailable.
3. **Draw the end-to-end path.** Include ingestion if needed, request handling, model or retrieval calls, tools, validation, response or escalation, storage, and observability.
4. **Deep-dive on the binding risks.** Choose two or three components whose failure would most affect correctness, privacy, latency, cost, or safety. Explain alternatives and failure handling.
5. **Explain evaluation and rollout.** Define offline cases, production measures, staged release, rollback, and who responds to incidents.

Do not invent scale or latency targets to fill silence. Ask for them or label an assumption, then show how the design would change if it differs.

#### Common trade-offs / 常见权衡

| Decision | Option A | Option B | What should drive it |
|---|---|---|---|
| Latency and cost | Smaller or fewer model calls | More capable model or additional checks | Measured task quality, workload, and response-time needs |
| Retrieval | Lower-cost candidate set | More recall or reranking work | Miss cost, corpus, and evaluation results |
| Autonomy | Model-directed tool loop | Fixed workflow or human review | Task variability, action risk, and control needs |
| Response mode | Immediate response | Queued or batch completion | User expectation and throughput |
| Deployment | Hosted service | Self-hosted or edge | Data boundary, operations, device, availability, and full cost |

Present each choice conditionally: explain when each option would fit, what evidence would change your decision, and how the alternative could be tested.

#### Design: enterprise question answering over documents / 企业文档问答

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

Lewis et al.'s RAG paper describes combining parametric generation with retrieved non-parametric memory; a production enterprise design must add current data ownership, authorization, and evaluation. See [RAG Architecture and Implementation / 检索增强生成](#6.%20Retrieval-Augmented%20Generation%20%28RAG%29%20/%20%E6%A3%80%E7%B4%A2%E5%A2%9E%E5%BC%BA%E7%94%9F%E6%88%90) for implementation detail.

##### One worked budget and design choice / 一组预算推导与方案选择

Assume a fictional enterprise team has a pre-indexed policy corpus; employee questions include both natural-language policy questions and exact policy IDs; peak load is 6 queries per second; the p95 end-to-end target is 4 seconds; a hosted model API is allowed; and the team has no capacity allocated to operating GPU inference for this workload. These are interview assumptions, not observed traffic or latency.

One proposed latency budget is 0.2 s for authentication and request setup + 0.6 s for permission-aware retrieval + 2.5 s for model generation + 0.2 s for validation and response handling + 0.5 s reserved for network and queueing = 4.0 s. These are allocations to validate, not measured stage percentiles; the sum of component p95s is not itself a statistical p95 guarantee. Instrument each stage and load-test the composed service.

For a rough capacity check, use Little's Law L = λW for the mean number of requests in a stable system. Suppose the explicit design assumption is an admitted 6 requests/s and 1.2 s mean time spent in the model stage, including any internal wait. Then L = 6 × 1.2 = 7.2, or about 8 requests in flight in that stage. This is an average, not 8 active model slots or a replica count; queueing, bursts, and service limits need load tests with the real model, request lengths, and latency target. Size executing slots from measured service demand and the target utilization.

For these mixed exact-ID and natural-language questions, I would start with hybrid keyword and vector retrieval, enforce document permissions before context assembly, and evaluate retrieval and answer quality separately. Given the stated hosted-service permission and lack of capacity for operating GPU inference, I would put a hosted model behind that retrieval service, keep authorization outside the prompt, and bound queueing so overload does not silently consume the latency budget. If the data boundary changed, I would compare a private or self-hosted endpoint and include its operations cost; if retrieval or generation cannot fit the measured budget, I would revisit context selection, candidate ranking, and the model before relaxing answer-quality checks.

#### Design: customer support assistant with tools / 带工具的客服助手

**Clarify first:** Which intents can be automated? Which actions change customer accounts or money? What policy and order systems are authoritative? Which requests require explicit consent or human review? What is the handoff path?

**Worked choice / 方案选择：** Suppose the supported flow is checking an order and requesting a refund, and policy disputes or tool failures need a person. I would use a fixed sequence: authenticate the customer; read the order and current policy; have application code check eligibility; show the proposed refund and ask for confirmation; call an idempotent refund operation; verify its result; then report the outcome or hand off. The sequence is predictable and changes financial state, so a fixed workflow makes authorization and stop points explicit. An agent loop would need evidence that dynamic tool choice materially helps before adding that control surface.

**Illustrative architecture / 架构示意:**

~~~text
Customer → intent and risk handling → assistant workflow
                                      ↙          ↘
                          read-only order/FAQ    bounded action tools
                                      ↘          ↙
                              validation → response or human handoff
~~~

**Tool and policy design:**

- Separate read-only lookup from actions that change state.
- Give the runtime—not the model—responsibility for identity, authorization, business limits, confirmation requirements, and final tool execution.
- Make retryable writes idempotent where the underlying system supports it; log the request outcome without exposing unnecessary personal data.
- Use a fixed workflow for a predictable sequence. Consider an agent loop only where dynamic tool selection adds value and can be bounded, observed, and stopped.
- Provide explicit handling for ambiguous intent, unavailable tools, policy conflicts, and user requests for a person.

**Evaluation and operations:** use reviewed examples for common intents, boundary cases, policy changes, tool failures, and escalation. Track task completion, human handoff, tool errors, unauthorized-action attempts, user feedback, and cost per resolved interaction. Treat the automation target as a product decision supported by evaluation, not a fixed percentage.

A tool-call schema can constrain the shape of a proposed call; the application must still check whether the user and action are permitted. See [Agent Fundamentals / 智能体基础](#7.%20Agent%20Fundamentals%20/%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%9F%BA%E7%A1%80), [Tool Design and Function Calling / 工具设计与函数调用](#9.%20Tool%20Design%20and%20Function%20Calling%20/%20%E5%B7%A5%E5%85%B7%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%87%BD%E6%95%B0%E8%B0%83%E7%94%A8), and [AI Safety in Production / 生产环境中的 AI 安全](#12.%20AI%20Safety%20in%20Production%20/%20%E7%94%9F%E4%BA%A7%E7%8E%AF%E5%A2%83%E4%B8%AD%E7%9A%84AI%E5%AE%89%E5%85%A8).

#### Design: code review assistant / 代码审查助手

**Clarify first:** Which languages and review types are in scope? Should findings be advisory or posted automatically? How is repository context selected? What level of false positives will developers tolerate? Which code or metadata may leave the repository boundary?

**Worked choice / 方案选择：** Suppose the team has low tolerance for noisy comments and wants a human to retain review authority. I would begin with advisory draft comments, require each finding to point to changed lines and cite the relevant code evidence, and suppress weak findings rather than posting every possible concern. I would not auto-approve or block a pull request. This favors developer trust and gives the team dismissal data before considering more automation.

**Illustrative architecture / 架构示意:**

~~~text
Pull request event → diff and repository context
                   → one or more review passes
                   → schema and location validation
                   → deduplicate and rank findings
                   → draft comments for human review
                   → collect feedback and measure outcomes
~~~

**Deep-dive topics:**

- **Context selection:** include changed lines, nearby code, relevant callers, and repository guidance as available. Record what was omitted when size limits require truncation.
- **Review passes:** separate correctness, security, and style checks when that makes evaluation or prompts clearer. Keep each pass tied to a defined review rubric.
- **Output validation:** require a finding category, explanation, location within the diff, and actionable suggestion; reject locations or structures that do not match the submitted change.
- **Noise management:** rank or suppress uncertain findings, show evidence, and make dismissal easy. The acceptable precision/recall balance depends on developer workflow and risk.
- **Large or generated changes:** segment by file or coherent unit, avoid irrelevant generated content, then deduplicate before presenting results.

**Evaluation and operations:** build a held-out set of reviewed changes with known issues and clean examples. Measure issue detection by category, false positives, location validity, developer acceptance or dismissal, cost per review, and delay added to the workflow. Compare against a no-assistant baseline; do not claim to outperform human review without evidence.

#### Practice / 练习

- Ask clarifying questions before fixing assumed scale or targets.
- Draw the request and data paths, including trust boundaries and failures.
- State assumptions and what evidence could change the design.
- Discuss quality, latency, cost, permissions, and operational ownership together.
- Explain how the system is evaluated, rolled out, monitored, and rolled back.

#### Related notes / 相关笔记

- [AI Application Architecture / AI 应用架构](#13.%20AI%20Application%20Architecture%20/%20AI%E5%BA%94%E7%94%A8%E6%9E%B6%E6%9E%84) covers production controls and deployment.
- [RAG Architecture and Implementation / 检索增强生成](#6.%20Retrieval-Augmented%20Generation%20%28RAG%29%20/%20%E6%A3%80%E7%B4%A2%E5%A2%9E%E5%BC%BA%E7%94%9F%E6%88%90) covers retrieval implementation and grounding.
- [LLM Evaluation Methods / 大语言模型评估方法](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95) covers evaluation design.
- [Agent Fundamentals / 智能体基础](#7.%20Agent%20Fundamentals%20/%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%9F%BA%E7%A1%80) covers runtime agent patterns.

#### Sources / 来源

- Lewis et al., [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401).
- OpenAI, [Function calling](https://developers.openai.com/api/docs/guides/function-calling) and [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs), checked 2026-10-15. These describe OpenAI API behavior; validate tool calls and application semantics in the target system.
- Little, [A Proof for the Queuing Formula: L = λW](https://doi.org/10.1287/opre.9.3.383), for the steady-state average-concurrency relation used in the hypothetical capacity check.
