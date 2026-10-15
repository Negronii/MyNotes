# AI Engineering

> Generated from the [ai-engineering reading map](../../ai-engineering/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. How LLMs Work / 大语言模型如何工作

### How LLMs Work

This note prepares you to answer:

- Why are modern LLMs autoregressive, not masked like BERT?
- What's a token, and why don't LLMs just use words?
- Walk me through how a transformer generates one token
- How does temperature actually work, and how is it different from top-k and top-p?

---

#### Why are modern LLMs autoregressive, not masked like BERT?

**Headline (30s):** Modern LLMs are **autoregressive** — they predict the next token from left-to-right context under a causal mask (each position can't attend to future tokens). Masked models like BERT see **bidirectional** context and excel at embeddings and classification, but they can't generate text at inference time because generation requires producing tokens without seeing the "future" tokens you're about to produce.

**Why it's asked:** Tests whether you understand the training objective behind GPT / Claude / Llama vs. BERT, and why decoder-only architectures dominate modern generation.

**How it works:**

- **Autoregressive** (GPT, Claude, Llama, Mistral): at every position, the model predicts the next token. During training, a causal mask prevents each position from attending to tokens on its right. At inference, tokens are generated one at a time and appended to the sequence.
- **Masked** (BERT, RoBERTa, ALBERT): during training, random tokens are replaced with `[MASK]` and the model predicts them using both left and right context. At inference, there's no "future" text to condition on for generation.
- Autoregressive training matches the generation task (sequential, left-to-right), which is why it won out for chat, completion, and instruction-following.

**Common follow-ups:**

- "Why can't BERT generate?" — generation needs a model that can produce tokens without seeing future context. BERT was trained assuming it always has both sides, so at inference there's nothing to the right to condition on.
- "Decoder-only vs. encoder-decoder?" — decoder-only (GPT family) is simpler and scales well for generation. Encoder-decoder (T5, BART, original Transformer) is better for classic seq2seq tasks like translation where the input and output are distinct sequences.

**Gotcha:** Many candidates say "GPT uses attention" as the distinguishing feature — true, but BERT uses attention too. The actual distinguisher is the **causal mask**: that's what prevents future-token leakage during training and what makes the model generable at inference.

---

#### What's a token, and why don't LLMs just use words?

**Headline (30s):** Tokens are **subword units** built via Byte-Pair Encoding (BPE). The model never sees raw characters or words — only integer IDs from a fixed vocabulary (~30k–100k entries). Subwords handle unknown/rare words, keep the vocabulary tractable across many languages, and let common morphemes ("un-", "-ing") reuse across words.

**How BPE works:**

1. Start with a character-level vocabulary.
2. Find the most frequent pair of adjacent symbols.
3. Merge them into a new symbol; add to vocabulary.
4. Repeat until the vocabulary reaches the target size.

The result is a mix of whole words, subwords, and common character sequences.

**Example** (using GPT-4's `cl100k_base` tokenizer):

```
Input:  "The transformer architecture revolutionized NLP."
Tokens: ["The", " transformer", " architecture", " revolution", "ized", " N", "LP", "."]
```

Common words like "transformer" stay whole; less common ones like "revolutionized" split into morphemes ("revolution" + "ized"); rare acronyms like "NLP" split into characters.

**Rule of thumb:** ~1 token ≈ 0.75 words in English. Varies by language and text style.

**Vocabulary size by model:**

| Model | Vocabulary |
|---|---|
| BERT | ~30k |
| Llama 1 / 2 | 32k |
| Llama 3 | ~128k |
| GPT-2 / GPT-3 | ~50k |
| GPT-3.5 / GPT-4 (`cl100k_base`) | ~100k |

**Gotcha:** Don't count tokens by eyeballing character count. Use the model's actual tokenizer (e.g., `tiktoken` for OpenAI). Emojis, non-English characters, and rare symbols can each be several tokens — emoji-heavy or CJK input can eat your context budget much faster than the character count suggests.

---

#### Walk me through how a transformer generates one token

**Headline (30s):** Encode the prompt into token IDs → run a forward pass through a stack of self-attention + feed-forward layers → take the logits for the **last position** → softmax into a probability distribution over the full vocabulary → sample (or greedily pick) the next token → append to the sequence → repeat until a stop condition.

**How it works:**

- **Self-attention:** each token attends to every other token in the sequence and produces a weighted combination of their representations.
- **Multi-head attention:** multiple attention computations run in parallel so different heads can focus on different relationships (syntax, long-range dependencies, semantics). Outputs are concatenated and projected.
- **Positional encoding:** attention itself is permutation-invariant. Positional encodings (learned or sinusoidal) inject position info so the model knows token order.
- **Feed-forward + layer norm:** applied per token after attention. Two linear layers with a non-linearity (e.g., GELU), typically 4× the hidden dimension. Layer norm stabilizes training.
- **Stop conditions:** a stop sequence is produced (e.g., `"\n\n"`, `"Human:"`), the end-of-sequence token is sampled, or `max_tokens` is hit.

**Next-token loop:**

1. Encode prompt → token IDs.
2. Forward pass.
3. Logits for last position → softmax → probability distribution.
4. Sample (or argmax) the next token.
5. Append to the sequence.
6. Repeat until stop.

**Common follow-ups:**

- "Why is long context expensive?" — self-attention is **O(n²) in sequence length**. Doubling the context quadruples attention cost. This is the core scaling constraint for long-context models.
- "Encoder-decoder vs. decoder-only?" — modern LLMs are almost all decoder-only (simpler, scales better for generation). T5 and BART use encoder-decoder for classic seq2seq like translation.

**Gotcha:** Candidates often say attention cost scales with vocabulary size — wrong. Vocabulary only affects the final projection layer and the embedding table. The quadratic cost is in **sequence length**, which is why 1M-token context windows are expensive even with a small vocab.

---

#### How does temperature actually work, and how is it different from top-k and top-p?

**Headline (30s):** Temperature **scales logits before softmax** — `T=0` becomes deterministic greedy decoding, `T=1` is unchanged, `T>1` flattens the distribution (more random). **Top-k** restricts sampling to the k highest-probability tokens. **Top-p** (nucleus) samples from the smallest set of tokens whose cumulative probability ≥ p, adapting to the distribution's shape. You usually pick one of top-k / top-p and pair it with a temperature.

**How it works:**

- **Softmax with temperature:** `P(token_i) = exp(logit_i / T) / Σ exp(logit_j / T)`. Lower T sharpens toward the max; higher T flattens.
- **Temperature sweet spots:**
  - `0 – 0.3` — factual, structured output, code
  - `0.5 – 0.8` — balanced chat, creative writing
  - `1.0+` — exploratory, risk of incoherence
- **Top-k:** `k=1` is equivalent to greedy. `k=50` is a common default.
- **Top-p:** `p=0.9` typical. Adaptively shrinks the sampling set on peaky distributions and widens on flat ones, which top-k can't do.

##### Sampling parameters (reference)

| Parameter | What it does | Typical range |
|---|---|---|
| `temperature` | Scales logits before softmax. Lower = more deterministic. | 0 (greedy) to 2.0; 0.7 for chat |
| `top_p` | Nucleus sampling: smallest set with cumulative prob ≥ p | 0.1–1.0; 1.0 = no filtering |
| `top_k` | Sample only from top k tokens by probability | 1 (greedy) to 100 |
| `max_tokens` | Hard limit on tokens generated | Task-dependent; 100–4096+ |
| `stop` | Sequences that halt generation | `["\n\n", "Human:"]` |
| `frequency_penalty` | Penalize tokens by how often they appear in output | -2.0 to 2.0; 0 = no penalty |
| `presence_penalty` | Penalize tokens that have already appeared | -2.0 to 2.0; 0 = no penalty |

**Gotcha:** `temperature=0` is **not** guaranteed identical to `top_k=1` across providers. Some APIs still break ties stochastically at T=0; some rescale differently. For deterministic output, set temperature near 0 **and** fix the `seed` parameter if the provider supports it.
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

### Advanced Prompting Techniques

This note prepares you to answer:

- When should you use few-shot vs. zero-shot prompting?
- What is chain-of-thought, and when is it worth the extra tokens?
- What is self-consistency, and how is it different from CoT?
- What is the ReAct pattern, and why is it the default for tool-using agents?
- When should you chain prompts instead of using one?
- What is meta-prompting, and when does it pay off?

---

#### When should you use few-shot vs. zero-shot prompting?

**Headline (30s):** Default to **zero-shot** for simple, well-defined tasks with strong instruction-following models. Reach for **few-shot** when zero-shot is inconsistent, when the mapping is non-obvious, when you need a custom output format, or when edge cases matter. Few-shot costs tokens per call; zero-shot costs you in retries and format drift.

**How each works:**

- **Zero-shot:** only instructions, no examples.

```
Classify the sentiment of the following review as positive, negative, or neutral.
Review: "The product arrived late but the quality exceeded expectations."
```

- **Few-shot:** demonstrate expected input-output pairs so the model picks up the pattern.

```
Classify the sentiment of each review as positive, negative, or neutral.

Review: "Terrible experience, never buying again."
Sentiment: negative

Review: "Exactly what I needed. Fast shipping."
Sentiment: positive

Review: "It's okay. Nothing special."
Sentiment: neutral

Review: "The product arrived late but the quality exceeded expectations."
Sentiment:
```

**Few-shot for structured extraction:**

```python
def build_extraction_prompt(text: str) -> str:
    return """Extract the following fields from the text. Return JSON.

Example 1:
Text: "John Smith ordered 3 widgets on March 10. Total: $45.99."
Output: {"name": "John Smith", "quantity": 3, "date": "2024-03-10", "total": 45.99}

Example 2:
Text: "Jane Doe, 2 items, paid $120.00 on 3/15."
Output: {"name": "Jane Doe", "quantity": 2, "date": "2024-03-15", "total": 120.00}

Now extract from:
Text: """ + text
```

**Gotcha:** Few-shot examples should cover the **edges**, not the middle. Three easy examples teach the model less than one easy + one ambiguous + one near-miss, because near-misses are exactly where production fails.

---

#### What is chain-of-thought (CoT), and when is it worth the extra tokens?

**Headline (30s):** CoT elicits **intermediate reasoning tokens** before the final answer. The model "thinks aloud," which reduces errors on math, logic, and multi-step tasks by decomposing the problem and by surfacing the reasoning for debugging. Worth it for anything where the answer isn't a direct lookup — not worth it for simple classification where it just burns tokens.

**Two flavors:**

- **Zero-shot CoT** — add a trigger like "Let's think step by step" and let the model produce reasoning unguided.

```
A store sells apples for $2 each and oranges for $3 each. If I buy 4 apples and 2 oranges, how much do I pay? Let's think step by step.
```

- **Few-shot CoT** — show worked examples so the model learns the reasoning style you want.

```
Q: A shirt costs $25. There's a 20% discount. How much do I pay?
A: First, 20% of $25 = $5. So the discount is $5. $25 - $5 = $20. I pay $20.

Q: A book costs $40. There's a 15% discount. How much do I pay?
A: First, 15% of $40 = $6. So the discount is $6. $40 - $6 = $34. I pay $34.

Q: A laptop costs $800. There's a 25% discount. How much do I pay?
A:
```

**When it helps:**

- Multi-step math, logic, or deduction
- Problems where the answer depends on intermediate facts
- Any task where you want to audit the reasoning

**Gotcha:** On "reasoning" models (o1, Claude with extended thinking, etc.), **don't manually add "think step by step"** — the model already does internal chain-of-thought. Adding explicit CoT instructions can actually hurt performance by double-reasoning. Reserve explicit CoT for non-reasoning models.

---

#### What is self-consistency, and how is it different from CoT?

**Headline (30s):** Self-consistency generates **multiple reasoning paths** for the same question and takes the **majority answer**. It sits on top of CoT — CoT is one path, self-consistency is N paths with voting. Improves reliability on reasoning tasks where single-path errors are common, at the cost of N× prompt + N× response tokens.

**How it works:**

```
For each of the following 5 reasoning attempts, solve: "What is 17 * 23?"
Take the most common final answer.
```

| Attempt | Reasoning Path | Answer |
|---|---|---|
| 1 | 17×20=340, 17×3=51, 340+51=391 | 391 |
| 2 | 17×23 = (20-3)×23 = 460-69 = 391 | 391 |
| 3 | 17×23 ≈ 400... (error) | 391 |
| 4 | 17×23 = 391 | 391 |
| 5 | 17×23 = 391 | 391 |

**Majority answer:** 391.

**Tradeoffs:**

- **Pro:** smooths out single-path errors; improves reliability on reasoning-heavy tasks.
- **Con:** N× tokens, N× latency, N× cost.

Use when correctness matters more than speed (code generation, math, critical classification).

**Gotcha:** Majority vote only works when the correct answer is **dominant**. If the model is systematically biased toward a wrong answer (e.g., a common misconception), all N paths agree on the wrong answer and self-consistency confirms the mistake. Pair with a separate evaluator (LLM-as-judge or rule-based check) when stakes are high.

---

#### What is the ReAct pattern, and why is it the default for tool-using agents?

**Headline (30s):** **Re**asoning + **Act**ing. The model alternates between `Thought` (reason about next step), `Action` (tool call), and `Observation` (tool result), in a loop, until done. ReAct is the default tool-using agent pattern because the explicit Thought step reduces hallucination (model must justify each action) and Observations keep it grounded in real data instead of pattern-matching.

**Pattern structure:**

```
Thought: [reasoning about current state and next step]
Action: [tool_name]([args])
Observation: [tool result]

Thought: [reasoning based on observation]
Action: [tool_name]([args])
Observation: [tool result]

...

Thought: I now have enough information to answer.
Answer: [final response]
```

**Concrete example — flight lookup:**

```
User: What's the cheapest flight from NYC to LA next Tuesday?

Thought: I need to find flights. I'll search for flights from NYC airports to LA airports on the user's specified date.
Action: search_flights(origin="NYC", destination="LA", date="2024-03-19")
Observation: Found 3 flights: Delta $189, United $210, JetBlue $175

Thought: JetBlue at $175 is the cheapest. I'll present this to the user.
Answer: The cheapest flight from NYC to LA on Tuesday March 19 is JetBlue at $175.
```

**Why it works:**

- Explicit reasoning reduces hallucination — the model must justify each action.
- Observations ground the model in real data rather than pattern-matching.
- The loop naturally supports multi-step tool use without custom orchestration.

**Common follow-ups:**

- "How do you prevent infinite loops?" — cap max iterations (e.g., 10–20 turns) and add an exit condition on repeated identical actions.
- "How is this different from plain function calling?" — plain function calling is one turn: request → tool call → response. ReAct is the iterative loop on top, with explicit Thought steps.

**Gotcha:** Don't pollute the context with verbose Observations. If a tool returns 10KB of JSON, truncate or summarize before the next Thought — otherwise long agent runs degrade from context rot (see [3.1 Context Engineering → Context as a Finite Resource](#Why%20is%20context%20a%20finite%20resource,%20and%20what%27s%20%22lost-in-the-middle%22?)).

---

#### When should you chain prompts instead of using one?

**Headline (30s):** Use prompt chaining when a task has **clearly separable steps**, benefits from **programmatic gates** between them (validation, retry, branching), or when a single mega-prompt is so long it confuses the model. Each step's output feeds the next; gates catch failures early instead of propagating them downstream.

**Example — outline → validate → write:**

```
Step 1 (Generate Outline):
Given the topic "Introduction to RAG", produce a 5-section outline with bullet points per section.
Output format: JSON with keys "sections" (array of {title, bullets}).

Step 2 (Validate):
Check the outline for: (a) logical flow, (b) no redundant sections, (c) each section has 2-4 bullets.
If invalid, return {"valid": false, "issues": [...]}. If valid, return {"valid": true}.

Step 3 (Write Content):
Given the validated outline, write 200-300 words per section. Use markdown. Do not deviate from the outline.
```

**Programmatic gates:**

| Gate | Purpose |
|---|---|
| Validation | Reject malformed output before passing to next step |
| Filtering | Remove irrelevant content before expensive steps |
| Branching | Route to different chains based on classification |
| Retry | Re-run a step with corrected input on failure |

**Implementation sketch:**

```python
def chain_with_gate(topic: str) -> str:
    outline = llm_call(step1_prompt(topic))
    validation = llm_call(step2_prompt(outline))
    if not validation["valid"]:
        return retry_step1(topic, validation["issues"])
    return llm_call(step3_prompt(outline))
```

**Common follow-ups:**

- "How is this different from a ReAct agent?" — ReAct is model-directed: the LLM decides what to do next each turn. Chaining is developer-directed: you hard-code the sequence of prompts. Use chaining when the path is known, ReAct when it's emergent. See also [5.2 Orchestration Patterns → Prompt Chaining vs. Orchestrator-Workers](#8.%20Orchestration%20Patterns%20/%20%E7%BC%96%E6%8E%92%E6%A8%A1%E5%BC%8F).

**Gotcha:** Chaining multiplies failure modes — each step has its own failure rate, and errors compound. A 95% success rate per step means only 77% over 5 steps. Budget for retries at each gate, or fail loudly and log the failing step.

---

#### What is meta-prompting, and when does it pay off?

**Headline (30s):** Meta-prompting uses an LLM to **generate or improve prompts**. Pays off when you're at scale (many prompts to maintain), adapting prompts to new domains, or running A/B tests — anywhere the cost of the LLM-as-prompt-engineer is lower than paying a human to manually tune.

**Two modes:**

- **Prompt generation:**

```
You are a prompt engineer. Given this task description, produce a system prompt that would elicit high-quality responses from an LLM.

Task: Extract customer name, order ID, and complaint type from support emails. Output JSON. Handle typos and informal language.
```

- **Prompt improvement:**

```
Here is a prompt that sometimes produces incorrect outputs:
[original prompt]

Here are 3 examples where it failed:
[failure 1]
[failure 2]
[failure 3]

Revise the prompt to address these failure modes. Preserve the original intent. Output only the revised prompt.
```

**Optimization loop:**

1. Define success criteria (accuracy, format compliance, user satisfaction).
2. Generate N prompt variants via meta-prompting.
3. Evaluate each variant on a held-out set.
4. Select the best; feed failures back for another round.

**Gotcha:** Meta-prompting is **not** a replacement for human judgment. The optimizer can converge on prompts that game your eval but break in production, or produce brittle prompts that only work on the exact distribution of your held-out set. Treat it as prompt *exploration*, not prompt *optimization* — human review is still required before deploying.

**See also:** [2.1 Prompt Engineering Fundamentals](#3.%20Prompt%20Engineering%20Fundamentals%20/%20%E6%8F%90%E7%A4%BA%E5%B7%A5%E7%A8%8B%E5%9F%BA%E7%A1%80) for the 4 principles and 7-layer system prompt architecture.
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

### Fine-tuning Strategies

This note prepares you to answer:

- Should you fine-tune, or is prompting/RAG enough?
- Which fine-tuning method should you pick (LoRA vs. full vs. QLoRA)?
- How much data do you need, and what does "quality over quantity" actually mean?
- Walk me through a fine-tuning training pipeline
- How do you evaluate a fine-tuned model to know it worked?
- What is RLHF, and where does it fit?

---

#### Should you fine-tune, or is prompting/RAG enough?

**Headline (30s):** Climb the **escalation ladder** first — prompting → few-shot → RAG → fine-tuning. Fine-tuning is slow to iterate and expensive to maintain; only reach for it when cheaper approaches demonstrably fail, and only for the right *reason*. The golden rule: **fine-tune for behavior, RAG for knowledge.** If the model needs new facts, use RAG; if it needs to speak/act differently, fine-tune.

**The escalation ladder:**

| Step | Approach | Effort | When It Works |
|---|---|---|---|
| 1 | **Prompting** | Low | Simple tasks, general knowledge, one-off queries |
| 2 | **Few-shot examples** | Low | Pattern demonstration, format consistency |
| 3 | **RAG** | Medium | Knowledge gaps, up-to-date info, proprietary docs |
| 4 | **Fine-tuning** | High | Persistent behavior change, format enforcement, domain adaptation |

Try each in order. Move to the next only when the current approach demonstrably fails.

**Good reasons to fine-tune:**

- **Output format consistency** — need a specific JSON schema, tone, or structure that prompting cannot reliably enforce.
- **Domain-specific terminology/behavior** — legal, medical, or technical jargon; industry conventions.
- **Latency-sensitive applications** — a fine-tuned small model can outperform a prompted large model.
- **Cost optimization at scale** — smaller fine-tuned model is cheaper than repeatedly prompting a large one.
- **Proprietary behavior** — logic or style that cannot be expressed in prompts.

**Bad reasons to fine-tune:**

- **Model lacks knowledge** → use RAG instead. Fine-tuning bakes facts in fragile ways; RAG keeps them current and swappable.
- **Small dataset** → insufficient for meaningful adaptation; high overfitting risk.
- **Rapidly changing requirements** → fine-tuning is slow; prompts or RAG iterate faster.

**Tiebreaker question (to ask the interviewer):** "What do we need the model to do that prompting + RAG can't achieve?" If the answer is "know more facts," don't fine-tune. If it's "behave differently / follow a format reliably," fine-tune.

**Gotcha:** Teams fine-tune for knowledge because the problem feels like "the model doesn't know X." That's a knowledge problem — RAG. If you fine-tune, you've now locked the facts into the weights, which means re-fine-tuning every time the facts change. Expensive trap.

---

#### Which fine-tuning method should you pick? (LoRA vs. full vs. QLoRA)

**Headline (30s):** **LoRA is the default** — trains ~1% of parameters, good quality, moderate memory. Go to **QLoRA** (LoRA on a 4-bit quantized base) when GPU memory is tight. Reach for **full fine-tuning** only when LoRA plateaus for your task and you have the GPU budget, which is rare for LLMs.

**The tradeoff:**

| Method | Parameters Trained | Memory | Quality | Use Case |
|---|---|---|---|---|
| **Full fine-tuning** | All (~100%) | Very high | Highest | Rarely used with LLMs; requires massive GPU memory |
| **LoRA** (Low-Rank Adaptation) | ~1% (rank-decomposition matrices) | Moderate | High | Most popular; freeze base, train small adapters |
| **QLoRA** | ~1% on quantized base | Low | Good | LoRA + 4-bit quantized base; memory-constrained setups |
| **Adapters** | Small modules between layers | Low–Moderate | Good | Modular; swap adapters per task |
| **Prefix tuning** | Trainable vectors prepended to layers | Low | Good | Lightweight; minimal parameter updates |

**How LoRA works:**

```python
# Freeze base model, add low-rank matrices
# W' = W + ΔW, where ΔW = A @ B  (A: d×r, B: r×k, r << d,k)
# Only A and B are trained; W is frozen
```

- Freeze base model weights.
- Train small rank-decomposition matrices (typically r = 8–64).
- Merge adapters into base at inference for zero latency overhead.

**Decision rule:**

1. Start with LoRA. Rank 8–16 is a fine default.
2. If memory is the bottleneck (single consumer GPU, large base model), move to QLoRA.
3. If LoRA plateaus and you have the GPU budget, try full fine-tuning.
4. Adapters and prefix tuning are niche — reach for them when you need to swap specializations at runtime (one base, many adapters).

**Gotcha:** "Higher rank = better quality" is mostly a myth. Past r = 16–32, quality plateaus or regresses (overfitting on small datasets). Don't tune rank; tune data quality and learning rate first.

---

#### How much data do you need, and what does "quality over quantity" actually mean?

**Headline (30s):** **100–1000 high-quality examples** can be effective with LoRA — often more useful than 100k mediocre ones. The dataset has to be **diverse** (cover edge cases), **representative** (match production distribution), **correct** (labels are right), and **consistently formatted**. Bad data produces a model worse than the base.

**Data formats:**

**Instruction-response pairs** (instruction tuning):

```json
{
  "instruction": "Summarize the following contract clause.",
  "input": "The party of the first part...",
  "output": "The seller agrees to deliver..."
}
```

**Conversation format** (chat models):

```json
{
  "messages": [
    {"role": "user", "content": "What is the refund policy?"},
    {"role": "assistant", "content": "Refunds are available within 30 days..."}
  ]
}
```

**Data quality checklist:**

| Criterion | Description |
|---|---|
| **Diverse** | Covers edge cases and variations |
| **Representative** | Matches production distribution |
| **Correct** | Labels/answers are accurate |
| **Consistent format** | Same structure across examples |

**Synthetic data:** use a stronger model (GPT-4, Claude) to generate training data for a smaller model. Effective when human-labeled data is scarce, but validate quality — models generating training data inherit the generator's biases and errors.

**Gotcha:** "My dataset has 10,000 examples" is not a quality signal. A model trained on 10k near-duplicates learns a single pattern and fails on everything outside it. Coverage of the input distribution matters more than raw count.

---

#### Walk me through a fine-tuning training pipeline

**Headline (30s):** Six steps: **prepare dataset** (clean, format, split) → **choose base model and method** → **set hyperparameters** → **train and monitor loss** (watch for overfitting) → **evaluate on held-out set** → **deploy and monitor**. The dataset-preparation step usually dominates; training itself is a commoditized script for LoRA.

**The pipeline:**

1. **Prepare dataset** — format, clean, split train/validation (e.g., 90/10). Deduplicate. Verify label quality.
2. **Choose base model and method** — e.g., Llama 3 + LoRA. Pick the smallest base that might work; upgrade only if it underperforms.
3. **Set hyperparameters** — learning rate is method-dependent: ~1e-5–5e-5 for full fine-tuning (small updates), ~1e-4–5e-4 for LoRA (small param count tolerates a higher LR). Epochs 1–3 is typical; batch size as large as memory allows.
4. **Train and monitor loss** — watch training vs. validation loss. Validation loss rising = overfitting. Use early stopping.
5. **Evaluate on held-out set** — task-specific metrics, format compliance, no regression on general capabilities.
6. **Deploy and monitor** — A/B test, track latency, error rates, user feedback.

**Cost considerations:**

| Option | Approx. Cost | When It Makes Sense |
|---|---|---|
| **API fine-tuning** (OpenAI, Anthropic) | $8–$80+ per 1M tokens (varies by model) | Quick iteration, no infra; vendor lock-in |
| **Cloud GPU rental** (AWS, GCP, Lambda) | $1–$4/hr (A10G, A100) | Full control, custom models, one-off or batch jobs |
| **Local training** | Hardware cost only | Repeated experiments, data privacy, long-term savings |

- **API fine-tuning:** simplest; limited to vendor models and formats.
- **Cloud GPU:** flexible; requires MLOps and cost management.
- **Local:** highest upfront cost; best for sensitive data and heavy repeated usage.

**Gotcha:** Candidates skip the "monitor after deploy" step because training completed successfully. Fine-tuned models drift as user behavior drifts; the eval set you trained against becomes stale within months. Treat fine-tuning as the start of a monitoring commitment, not a shipping milestone.

---

#### How do you evaluate a fine-tuned model to know it worked?

**Headline (30s):** Four checks: **compare against the base model** on the same eval set (did fine-tuning actually help?), **check for regression** on general capabilities (math, reasoning — fine-tuning can degrade them), **test edge cases** and adversarial inputs, and **A/B test in production** where real users catch what offline evals miss.

**The four checks:**

- **Compare against base model** — same eval set, both models, show the delta. A fine-tuned model "works" only relative to what you started with.
- **Check for regression** on general capabilities — run math, reasoning, and safety benchmarks before and after. Specialization often degrades generalization.
- **Test edge cases and adversarial inputs** — prompt injections, malformed requests, boundary cases. Fine-tuned models can regress on safety.
- **A/B test in production** — offline evals predict, online usage confirms. Real-user satisfaction and task completion are the ultimate signals.

**Gotcha:** "Eval metric went up" alone is not proof of success. If your eval set drew heavily from your training distribution, you measured memorization, not generalization. Hold out a genuinely unseen eval slice — and ideally, gather one *after* training started, so contamination is physically impossible.

---

#### What is RLHF, and where does it fit?

**Headline (30s):** **Reinforcement Learning from Human Feedback** aligns models with human preferences *after* supervised fine-tuning. It's a three-step process: SFT on demonstrations → train a **reward model** on human pairwise preferences → optimize the policy against that reward model (PPO, or DPO as a simpler alternative). RLHF is what turns a capable model into a helpful one — responsible for most of the "feels aligned" behavior of ChatGPT-like models.

**The process:**

1. **SFT** (Supervised Fine-Tuning) — train on high-quality human demonstrations. This gives the model a baseline of the desired style.
2. **Reward model training** — humans rate pairs of model outputs (A better than B). Train a model to predict these preferences.
3. **PPO / DPO optimization** — optimize the policy against the reward model. PPO is the classic approach; DPO (Direct Preference Optimization) sidesteps the reward model by optimizing directly on preference pairs — simpler to implement.

**Why it matters:**

Alignment is what makes models helpful, harmless, and honest rather than merely capable. Without it, base models produce grammatical text that doesn't necessarily do what you want.

**What you're expected to know vs. do:**

- **Know conceptually** — what SFT, reward model, and PPO/DPO do; why SFT alone is insufficient.
- **Rarely run yourself** — full RLHF is expensive and data-hungry; most teams use RLHF'd base models (Claude, GPT-4, Llama Instruct) and add LoRA fine-tuning on top.

**Gotcha:** DPO is often taught as "simpler PPO" and picked for that reason, but it has its own failure modes (reward hacking, preference noise propagating directly into policy updates). If you're in an interview and asked "why DPO over PPO," cite implementation simplicity and avoiding reward model drift — not "DPO is better."

**See also:** [4.1 RAG Architecture and Implementation](#6.%20Retrieval-Augmented%20Generation%20%28RAG%29%20/%20%E6%A3%80%E7%B4%A2%E5%A2%9E%E5%BC%BA%E7%94%9F%E6%88%90) for when knowledge problems should be solved by retrieval instead of fine-tuning; [6.1 LLM Evaluation Methods](#10.%20LLM%20Evaluation%20Methods%20/%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E8%AF%84%E4%BC%B0%E6%96%B9%E6%B3%95) for how to build evals that measure whether fine-tuning actually worked.
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

### AI Application Architecture

This note prepares you to answer:

- What changes when you move an LLM app from prototype to production?
- How do you reduce inference latency and cost?
- How do you manage LLM costs at scale?
- What should you monitor in an LLM system?
- How do you design user feedback loops that actually improve the product?
- API, self-hosted, edge, or hybrid — how do you pick a deployment pattern?

---

#### What changes when you move an LLM app from prototype to production?

**Headline (30s):** The jump is massive and underestimated. Six dimensions all shift from "good enough for a demo" to "real-world-ready": error handling, scale, monitoring, cost management, security, and reliability. A prototype validates the approach; a production system has to withstand adversarial users, traffic spikes, and provider outages.

| Dimension | Prototype | Production |
|---|---|---|
| **Error handling** | Fail fast, manual recovery | Graceful degradation, retries, fallbacks |
| **Scale** | Single user, low throughput | Multi-tenant, high concurrency |
| **Monitoring** | Print statements, ad-hoc | Structured logging, metrics, alerts |
| **Cost management** | Ignored | Budgets, quotas, optimization |
| **Security** | Minimal | Auth, data isolation, PII handling |
| **Reliability** | Best-effort | SLAs, redundancy, failover |

**Don't skip the prototype.** Use it to validate the approach before investing in production infrastructure. A prototype that proves the core idea fails is cheaper than a production system built on a flawed assumption.

**Gotcha:** The biggest prototype-to-production failure isn't any single dimension; it's that teams treat the LLM as a stable dependency. LLMs silently drift (provider model updates, policy tweaks) in ways traditional APIs don't. Build eval, monitoring, and rollback *first* — you'll need them sooner than you think.

---

#### How do you reduce inference latency and cost?

**Headline (30s):** Six levers, from cheapest to most invasive: **streaming** (perceived latency only), **KV-cache** (reuse prefix computation), **semantic caching** (reuse full responses for similar queries), **request batching** (GPU throughput), **quantization** (smaller precision = faster, cheaper, slight quality loss), and **model distillation** (train a smaller model to mimic a bigger one). Stack in order of complexity; measure after each.

**The techniques:**

##### KV-cache

Reuse computed key-value pairs across requests with shared prefixes. Stable system prompts increase cache hit rate dramatically.

```python
# Requests with same system prompt share cached KV pairs
# Higher hit rate = fewer tokens recomputed = lower latency and cost
```

##### Semantic caching

Cache responses for semantically similar queries, not just exact matches. Use embedding similarity with a threshold.

```python
def get_cached_response(query: str, threshold: float = 0.95) -> str | None:
    query_embedding = embed(query)
    for cached in cache:
        if cosine_similarity(query_embedding, cached.embedding) >= threshold:
            return cached.response
    return None
```

##### Request batching

Group multiple requests to maximize GPU throughput. Trades per-request latency for overall throughput.

##### Quantization

Reduce model precision: FP32 → FP16 → INT8 → INT4. Tradeoff: lower memory and faster inference, slight quality loss. Common formats: GPTQ, AWQ, GGUF.

##### Model distillation

Train a smaller model to mimic a larger one. The smaller model is cheaper and faster in production; requires training effort upfront.

##### Streaming

Return tokens as they're generated for better perceived latency (time-to-first-token).

##### Comparison

| Technique | Latency Impact | Cost Impact | Complexity | Best For |
|---|---|---|---|---|
| KV-cache | High (prefix reuse) | High | Low | Repeated system prompts |
| Semantic caching | High (cache hits) | High | Medium | Similar user queries |
| Request batching | Neutral/negative | Medium | Medium | High-throughput batch workloads |
| Quantization | Medium (faster compute) | High | Medium | Self-hosted, memory-bound |
| Model distillation | High (smaller model) | High | High | Production at scale |
| Streaming | Perceived only (TTFT) | None | Low | Real-time UX |

**Gotcha:** Semantic caching with too loose a threshold (e.g., 0.85) serves wrong answers — two semantically similar queries can have different correct answers ("what's the refund policy for US?" vs. "for EU?"). Start at 0.95+ threshold, and always eval cache hits against fresh generations before shipping.

---

#### How do you manage LLM costs at scale?

**Headline (30s):** Four levers: **model routing** (cheap models for simple tasks, expensive only where needed), **token optimization** (shorter prompts, compressed context), **caching ROI** (measure and maximize hit rate), and **batch processing** (async APIs are often ~50% cheaper). Treat tokens-per-query as a KPI; track it across releases.

##### Model routing

Route by task complexity:

```
Simple (Haiku / small)      → classification, extraction, simple Q&A
Medium (Sonnet / mid)       → summarization, multi-step reasoning
Complex (Opus / large)      → creative writing, deep analysis, code generation
```

Classify the task first (cheap LLM call or rules), then route to the right size.

##### Token optimization

- Shorter prompts.
- Compressed context (summarization, selective retrieval).
- Efficient templates with minimal boilerplate.
- Measure **tokens-per-query** as a KPI per feature.

##### Caching ROI

Track hit rates. Even 50% hit rate can halve costs on cached paths.

##### Batch processing

Non-real-time tasks can use batch APIs (often ~50% cheaper than real-time).

##### Cost estimation example

| Component | Volume | Unit Cost | Monthly Cost |
|---|---|---|---|
| Input tokens (GPT-4) | 100M/month | $2.50/1M | $250 |
| Output tokens (GPT-4) | 20M/month | $10/1M | $200 |
| Cache hits (50%) | — | — | -$225 |
| **Net** | | | **$225** |

With semantic caching at 50% hit rate, effective cost drops by ~50%.

**Gotcha:** "Route everything to the cheap model" destroys quality on hard tasks, but "route everything to the expensive model" burns budget on easy ones. The sweet spot requires real data on task-complexity distribution — instrument your traffic before tuning the routing rules.

---

#### What should you monitor in an LLM system?

**Headline (30s):** Six categories: **latency** (P50/P95/P99, TTFT), **token usage** (per request, per user, total), **error rates** (API errors, timeouts, rate limits, malformed responses), **quality** (hallucination rate, task completion, satisfaction), **cost** (daily spend, cost/request), and **cache** (hit rate). Set alerts on thresholds and **quality drift** — LLM behavior changes silently over time.

##### Latency

- **P50, P95, P99** response times.
- **Time to first token (TTFT)** for streaming UX.

##### Token usage

- Input/output tokens per request.
- Total daily consumption.
- Tokens per user/session (catches runaway sessions).

##### Error rates

- API errors (4xx, 5xx).
- Timeouts.
- Rate limits.
- Malformed responses (parse failures, truncation).

##### Quality metrics

- Hallucination rate.
- User satisfaction scores.
- Task completion rate.

##### Quality drift

Model behavior can change over time due to provider updates or data drift. Track quality metrics week-over-week and alert on degradation.

##### Monitoring dashboard checklist

| Category | Metrics | Alerts |
|---|---|---|
| Latency | P50, P95, P99, TTFT | P99 > threshold |
| Throughput | Requests/sec, tokens/sec | Drops below baseline |
| Errors | Error rate by type | Error rate > 1% |
| Cost | Daily spend, cost/request | Budget threshold |
| Quality | Satisfaction, completion rate | Week-over-week decline |
| Cache | Hit rate | Hit rate < threshold |

**Gotcha:** Provider-side silent model updates are the hardest drift to catch. An "imperceptible" improvement upstream can change output format or tone enough to break your downstream parsers and regression test suite. Pin model versions explicitly (`gpt-4-0613` not `gpt-4`) whenever the provider allows, and run weekly evals on fixed test sets to catch drift.

---

#### How do you design user feedback loops that actually improve the product?

**Headline (30s):** Capture both **implicit signals** (time on response, follow-ups, acceptance rate) and **explicit feedback** (thumbs, ratings, corrections). Feed into an **RLHF flywheel** (preferences → reward model → improved model → deploy → repeat) or simpler update cycles. Design the feedback UX to minimize friction — a one-tap thumbs gets 100× more data than a form.

##### Implicit signals

- Time spent on response.
- Follow-up questions (indicates confusion).
- Acceptance / rejection of suggestions (autocomplete, code suggestions).

##### Explicit feedback

- Thumbs up/down.
- Star ratings.
- Correction submissions.

##### RLHF flywheel

1. Collect preferences (A vs. B, thumbs up/down).
2. Train reward model on preferences.
3. Improve base model (RLHF, DPO) or add fine-tuning.
4. Deploy improved model.
5. Repeat.

##### Designing feedback UX

| Principle | Implementation |
|---|---|
| Minimize friction | One-tap feedback (thumbs), not forms |
| Contextual timing | Prompt after action (after copy, after 5s) |
| Avoid survey fatigue | Sample users, limit frequency |
| Capture intent | Optional free-text for downvotes |
| Link to outcome | Correlate feedback with task success |

**Gotcha:** Explicit feedback is heavily biased — users who loved it don't bother; angry users always rate. Don't interpret "30% thumbs down" as "30% failure rate"; it's a skewed sample. Pair explicit feedback with implicit signals (retention, task completion, session length) for a real picture.

---

#### API, self-hosted, edge, or hybrid — how do you pick a deployment pattern?

**Headline (30s):** Start with **API** for speed to ship. Move to **self-hosted** once volume or data residency makes the math work (rough threshold: ~$10K/month API spend or strict compliance). Choose **edge** for latency-sensitive or offline use cases. Use **hybrid** when workloads split cleanly into "expensive hard" and "cheap simple/sensitive."

##### The tradeoff

| Pattern | Pros | Cons | When to Choose |
|---|---|---|---|
| **API-based** (OpenAI, Anthropic) | Fastest to ship, no infra management | Ongoing per-token cost, data sent to provider | MVP, low volume, rapid iteration |
| **Self-hosted** (vLLM, TGI, Ollama) | Full control, predictable cost at scale | Significant infra burden, data stays private | High volume, data sovereignty, cost optimization |
| **Edge deployment** | On-device inference, latency, privacy | Limited model size, device constraints | Mobile, offline, privacy-critical |
| **Hybrid** | API for complex + local for simple/sensitive | More moving parts | Mixed workload, cost + privacy balance |

##### Decision guide

- **API-based:** start here. Move off when cost or data concerns justify the switch.
- **Self-hosted:** volume > ~$10K/month API spend, or strict data residency requirements.
- **Edge:** latency-sensitive, offline-first, or device-level privacy.
- **Hybrid:** API for hard tasks, local model for simple/sensitive ones.

**Tiebreaker question (to ask the interviewer):** "What's the data residency requirement, and what's our expected monthly LLM spend?" These two answers narrow the pattern to one or two options.

**Gotcha:** Self-hosting math often looks attractive at volume but ignores the hidden costs — MLOps headcount, GPU availability risk, model update cadence, internal eval infrastructure. The break-even point is typically **later than you think**, not earlier. Get a real quote including people costs before committing.

**See also:** [3.1 Context Engineering → KV-Cache Optimization](#How%20do%20you%20use%20the%20KV%20cache%20to%20cut%20inference%20cost?) for the KV-cache mechanics; [1.2 Model Selection and Ecosystem](#2.%20Model%20Selection%20and%20Ecosystem%20/%20%E6%A8%A1%E5%9E%8B%E9%80%89%E6%8B%A9%E4%B8%8E%E7%94%9F%E6%80%81) for model choices behind the routing decisions.
## 14. AI System Design Interview Questions / AI系统设计面试题

### AI System Design Interview Questions

Capstone: how to structure answers to AI system design questions, plus three worked examples with probes and tradeoffs.

This note prepares you to answer:

- How do you structure an AI system design interview answer?
- What tradeoffs come up repeatedly in AI system design?
- Design a RAG-based enterprise Q&A system
- Design a customer support agent
- Design a code review assistant

---

#### The 5-step framework for AI system design questions

**Headline (30s):** Spend the first 5 minutes clarifying requirements; sketch the architecture in 10; deep-dive on 2–3 critical components for 15; spend 5 on tradeoffs and alternatives; close with 5 on scaling and monitoring. The trap is diving into implementation before nailing requirements — every interviewer has seen it.

**The five steps, as slots to memorize:**

##### Step 1: Requirements gathering (5 min)

- **Functional requirements:** what does the system do? Inputs, outputs, user flows.
- **Non-functional requirements:** latency, throughput, availability, consistency.
- **Scale:** users, documents, requests per second, data volume.
- **Constraints:** budget, compliance, existing infrastructure.

##### Step 2: High-level architecture (10 min)

- Draw components and data flow.
- Identify external systems (APIs, databases, queues).
- Show the request path end-to-end.

##### Step 3: Component deep-dive (15 min)

- Detail the 2–3 most critical components.
- Explain design choices and algorithms.
- Address edge cases and failure modes.

##### Step 4: Tradeoffs and alternatives (5 min)

- What you chose and why.
- Alternatives considered and why they were rejected.

##### Step 5: Scaling and monitoring (5 min)

- Horizontal vs. vertical scaling.
- Caching, sharding, async processing.
- Metrics, alerts, feedback loops.

**Gotcha:** Candidates skip Step 1 because it "feels slow." That's the fastest way to fail. Interviewers are testing whether you can scope the problem; rushing to architecture signals that you'll build the wrong thing in real life too. Use the 5 minutes.

---

#### Common tradeoffs

Reach for these framings when an interviewer asks "what are the tradeoffs?" — they cover most AI system design decisions.

| Tradeoff | Option A | Option B | Decision Factor |
|---|---|---|---|
| Latency vs. Quality | Smaller/faster model | Larger/better model | User tolerance |
| Cost vs. Accuracy | Fewer retrieval steps | More retrieval + re-ranking | Budget |
| Autonomy vs. Control | Full agent autonomy | Human-in-the-loop | Risk level |
| Real-time vs. Batch | Stream responses | Process in background | Use case |
| Privacy vs. Capability | Self-hosted model | API provider | Data sensitivity |

**Gotcha:** Don't present tradeoffs as "A is better." Interviewers want to hear "A when X, B when Y." Absolute claims flag shallow thinking; conditional claims show engineering judgment.

---

#### Design: RAG-based enterprise Q&A system

##### Requirements probes

- Who are the users? — Employees asking about internal docs (HR policies, engineering, product specs).
- Scale? — 10K employees, 100K documents.
- Latency target? — Sub-5s response time.
- Access control? — Yes, filter chunks by user permissions.

##### High-level architecture

```
Document Ingestion → Chunking → Embedding → Vector DB
                                              ↓
User Query → Query Service → Retrieval → LLM + Context → Response
```

##### Deep-dive (pick 2–3)

**Chunking strategy**

- Document-aware: respect sections, tables, lists.
- Preserve structure (headers, hierarchy).
- Overlap for continuity; typical chunk size 256–512 tokens.

**Retrieval**

- Hybrid: dense embeddings + BM25 for keyword recall.
- Re-ranking with cross-encoder for top-k (e.g., top 20 → top 5).
- **Access control:** filter by user permissions *before* returning chunks — critical for enterprise data.

**Citation generation**

- Attach source doc + chunk ID to each retrieved passage.
- Instruct LLM to cite sources in the answer.

##### Tradeoffs considered

- **Pure dense vs. hybrid:** pure dense misses rare jargon and specific IDs that matter in enterprise docs; hybrid costs slightly more but catches both.
- **Chunk size 256 vs. 512:** larger chunks give more context per retrieval but retrieve fewer distinct topics. Chose 512 for enterprise docs where context matters more than topic diversity.
- **Re-ranking top-20 vs. top-50:** top-50 catches more relevant chunks but doubles re-rank cost. Chose top-20 because retrieval recall is already high.

##### Scaling and monitoring

- Horizontal scaling of the retrieval service.
- Caching for frequent queries (query embedding → cached results).
- Async document indexing with a queue-based ingestion pipeline.
- Monitor: retrieval recall@k, faithfulness of answers to retrieved chunks, latency P95, access-control errors (should be zero).

##### Interviewer probes to prepare for

- "How do you handle a doc update?" → partial re-indexing; keep a version table; re-embed changed chunks only.
- "What if retrieval returns the wrong chunk?" → add citations, strengthen grounding prompt, and instrument faithfulness eval.
- "How do you onboard a new department?" → new docs flow through the same ingestion pipeline; permission filter tagged at ingest.

**Gotcha:** Candidates forget access control until asked — in enterprise Q&A, it's the **first** design question, not the last. A working RAG that leaks docs across permission boundaries is a security incident, not a shipped feature.

---

#### Design: Customer support AI agent

##### Requirements probes

- What's the automation target? — ~80% of queries handled automatically; escalate complex cases.
- Conversation shape? — Multi-turn.
- Tool surface? — Order DB, refund system, FAQ.
- Budget for failures? — Refunds are reversible (chargebacks) but costly; require confirmation.

##### High-level architecture

```
User → Routing Classifier → Agent (tools) → Response / Human Escalation
         ↓
    Tools: order lookup, refund processing, FAQ retrieval
```

##### Deep-dive (pick 2–3)

**Orchestration**

- Single agent with routing; the agent selects tools.
- A fast routing classifier does quick escalation detection (explicit "speak to human" requests, sentiment triggers).

**Tool design**

- **Read-only tools:** order lookup, FAQ retrieval — no confirmation needed.
- **Write tools (e.g., refund):** require explicit confirmation before execution.
- **Idempotency for refunds;** audit logs for all writes.

**Guardrails**

- Refund limits (amount, frequency) — hard-coded, not trusted to the model.
- PII protection: no raw SSN/CC in logs or responses.
- Blocked intents: legal advice, medical advice.

**Escalation triggers**

- Low confidence (< threshold).
- Customer frustration (sentiment, repeated "agent" requests).
- Sensitive topics (legal, complaints, executive escalation).

##### Tradeoffs considered

- **Full agent vs. workflow:** full agent adapts to novel queries but burns more tokens and introduces goal drift. Chose agent because queries are open-ended and fixed workflows would need dozens of branches.
- **Single agent vs. multi-agent manager pattern:** single agent is simpler; multi-agent adds isolation but handoff cost. Chose single for this volume; revisit if tool count exceeds ~15.

##### Scaling and monitoring

- **Resolution rate** (handled without human).
- **Escalation rate** (drift in either direction is bad).
- **CSAT / NPS.**
- **Cost per interaction** (API calls, tokens).
- **Max turns cap** on the agent loop; repeated-identical-action detection to break infinite loops.

##### Interviewer probes to prepare for

- "What happens if the refund tool fails mid-conversation?" → audit log captures attempt; inform user; retry path with idempotency key.
- "How do you prevent prompt injection via customer messages?" → tool-level privilege separation (refund requires explicit confirmation and bounded amount); output validation; monitor canary tokens.
- "What if the agent hallucinates a refund?" → the tool call schema is validated, so the model can only call `process_refund(order_id, amount)` with a real order_id it looked up first; business logic enforces bounds.

**Gotcha:** "The agent should be fully autonomous" is the wrong framing for support. Autonomous agents with refund access will eventually issue a refund they shouldn't. Design around the assumption of occasional failure: reversibility, audit logs, rate limits, and explicit confirmation on high-stakes actions.

---

#### Design: Code review assistant

##### Requirements probes

- What does it review? — Pull requests: bugs, improvements, style.
- Integration? — GitHub.
- Input shape? — Processes diffs.
- Noise tolerance? — Low; false positives train reviewers to ignore the bot.

##### High-level architecture

```
GitHub Webhook → PR Diff Parser → Context Builder → LLM Analysis → Inline Comments → GitHub API
                                      ↓
                    (relevant files, style guide, prior reviews)
```

##### Deep-dive (pick 2–3)

**Context engineering**

- Fit diff + relevant files within context window.
- Prioritize changed files and their callers.
- Truncate or summarize when over limit.

**Prompt design**

- Separate passes: bugs → style → security. Each pass is cheaper to get right than one mega-prompt.
- Structured output: severity, location, suggestion, code snippet.

**Avoiding false positives**

- Prefer **high precision over high recall** — silence is better than noise.
- Confidence thresholds; only surface high-confidence issues.
- Allow "dismiss" and feedback to tune thresholds over time.

**Large PRs**

- Chunk into logical units (by file or by feature).
- Review each chunk; aggregate and deduplicate comments.

##### Tradeoffs considered

| Dimension | Option A | Option B | Choice |
|---|---|---|---|
| Comment frequency | Fewer, high-signal | More, comprehensive | Balance noise vs. coverage |
| Confidence threshold | Strict | Lenient | Depends on team tolerance |
| Model selection | Fast model for style | Strong model for bugs | Use both for different passes |

##### Scaling and monitoring

- **Comment acceptance rate** (developers marking comments as helpful).
- **Dismissal rate** (inverse signal for noise).
- **Bug detection rate** on seeded bugs.
- **Cost per PR** reviewed.
- **Time from PR open to review** (latency matters for developer workflow).

##### Interviewer probes to prepare for

- "How do you know it's better than a human reviewer?" → don't claim it is; measure acceptance rate and bug detection rate, compare to no-bot baseline.
- "What if the style guide changes?" → style guide lives in the prompt or a retrieved doc; changes update a single source, not re-fine-tune.
- "How do you handle PRs with 5000 lines?" → chunk by file or feature; summarize unchanged files; skip generated code (lockfiles, etc.).

**Gotcha:** Code review assistants that optimize for recall become noise generators and get ignored. The binding constraint is **developer trust**. A reviewer that flags 30 things where only 5 matter trains developers to dismiss without reading — the bot is effectively off. Target precision first; recall is a ratchet to open up once the false-positive rate is low.

---

#### Practice tips

1. **Ask clarifying questions first** — don't assume scale, constraints, or priorities.
2. **Draw the architecture before diving in** — use a whiteboard or diagram; iterate.
3. **State assumptions explicitly** — "Assuming 1000 QPS," "Assuming documents are pre-indexed."
4. **Discuss tradeoffs, not just "the answer"** — show reasoning, not memorized solutions.
5. **Show awareness of cost, latency, and failure modes** — token cost, retries, fallbacks.
6. **Mention monitoring and feedback loops** — metrics, alerts, A/B tests, user feedback.

**See also:** [9.1 AI Application Architecture](#13.%20AI%20Application%20Architecture%20/%20AI%E5%BA%94%E7%94%A8%E6%9E%B6%E6%9E%84) for production concerns that back every answer; [4.1 RAG Architecture and Implementation](#6.%20Retrieval-Augmented%20Generation%20%28RAG%29%20/%20%E6%A3%80%E7%B4%A2%E5%A2%9E%E5%BC%BA%E7%94%9F%E6%88%90) for the RAG primitives you'll reach for in design questions; [5.1 Agent Fundamentals](#7.%20Agent%20Fundamentals%20/%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%9F%BA%E7%A1%80) for agent patterns.
