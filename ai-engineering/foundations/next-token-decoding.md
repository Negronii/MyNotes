# How does a decoder choose the next token from model scores? / 解码器怎样根据模型分数选出下一个词元？

The model produces a logit for each vocabulary entry. The decoding rule either takes the highest score or samples from a probability distribution after applying the chosen controls. Temperature changes the distribution's shape, while top-k and top-p restrict the candidate set. / 模型为词表中的每项生成一个 logit。解码规则可以直接选最高分，也可以应用控制参数后从概率分布中采样。温度改变分布形状，top-k 和 top-p 则限制候选范围。

**Key terms / 关键术语** · logit / 未归一化分数 · greedy decoding / 贪心解码 · nucleus sampling / 核采样

## Temperature, top-k, and top-p / 温度、top-k 与 top-p

Given next-token logits \(z_i\), temperature \(T > 0\) changes their sharpness before softmax:

$$
P(i) = \frac{\exp(z_i/T)}{\sum_j \exp(z_j/T)}
$$

Lower \(T\) concentrates probability on high-scoring tokens; higher \(T\) flattens it. In the idealized limit as \(T\) approaches zero, selection approaches argmax, but API support and reproducibility behavior are provider- and model-specific.

- **Top-k / 前 k 项：** keep only the \(k\) highest-probability candidates, then decode from them.
- **Top-p / nucleus sampling / 核采样：** keep the smallest ranked set whose cumulative probability reaches \(p\), then decode from that set.
- **Greedy decoding / 贪心解码：** choose the highest-scoring candidate instead of sampling.

These controls change decoding behavior; none makes an answer more factual. Parameter availability and interactions vary. For example, the OpenAI Responses API reference checked on 2026-10-15 documents temperature and top_p and recommends changing one rather than both for that API; do not assume another provider exposes the same parameters. [Nucleus sampling paper](https://arxiv.org/abs/1904.09751), [OpenAI Responses API reference](https://developers.openai.com/api/reference/resources/responses/methods/create).

The chosen token extends the prefix used for the next iteration in [the generation loop / 生成循环](how-llms-work.md).
