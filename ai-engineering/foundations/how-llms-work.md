# How LLMs Work

This note prepares you to answer:

- Why are modern LLMs autoregressive, not masked like BERT?
- What's a token, and why don't LLMs just use words?
- Walk me through how a transformer generates one token
- How does temperature actually work, and how is it different from top-k and top-p?

---

## Why are modern LLMs autoregressive, not masked like BERT?

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

## What's a token, and why don't LLMs just use words?

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

## Walk me through how a transformer generates one token

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

## How does temperature actually work, and how is it different from top-k and top-p?

**Headline (30s):** Temperature **scales logits before softmax** — `T=0` becomes deterministic greedy decoding, `T=1` is unchanged, `T>1` flattens the distribution (more random). **Top-k** restricts sampling to the k highest-probability tokens. **Top-p** (nucleus) samples from the smallest set of tokens whose cumulative probability ≥ p, adapting to the distribution's shape. You usually pick one of top-k / top-p and pair it with a temperature.

**How it works:**

- **Softmax with temperature:** `P(token_i) = exp(logit_i / T) / Σ exp(logit_j / T)`. Lower T sharpens toward the max; higher T flattens.
- **Temperature sweet spots:**
  - `0 – 0.3` — factual, structured output, code
  - `0.5 – 0.8` — balanced chat, creative writing
  - `1.0+` — exploratory, risk of incoherence
- **Top-k:** `k=1` is equivalent to greedy. `k=50` is a common default.
- **Top-p:** `p=0.9` typical. Adaptively shrinks the sampling set on peaky distributions and widens on flat ones, which top-k can't do.

### Sampling parameters (reference)

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
