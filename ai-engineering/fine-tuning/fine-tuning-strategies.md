# Fine-tuning Strategies / 微调策略

**Core explanation / 核心解释：** Fine-tuning updates a pretrained model using examples or preferences to change task behavior. It is worth testing when a repeatable behavior gap remains after prompt, context, retrieval, and workflow improvements. It is not a reliable database for fresh or access-controlled facts; choose the method and data through held-out evaluation and account for training, serving, and maintenance. / 微调用示例或偏好更新预训练模型，以改变特定任务行为。当提示词、上下文、检索和工作流改进后仍存在稳定的行为差距，才值得评估微调。它不是可靠的实时或权限控制数据库；应通过保留集评估选择方法和数据，并计入训练、部署及维护成本。

**Key terms / 关键术语：** supervised fine-tuning (SFT) / 监督微调；LoRA / 低秩适配；QLoRA / 量化低秩适配；preference optimization / 偏好优化；RLHF / 基于人类反馈的强化学习；DPO / 直接偏好优化。

## Should you fine-tune, or use prompting and retrieval? / 应微调，还是使用提示和检索？

First identify the error. Missing or changing facts call for an authoritative data source and retrieval or a direct API. Unclear instructions may be fixed with a prompt or workflow. A persistent style, label convention, or response pattern may be suitable for fine-tuning if examples can teach it and evaluation confirms the gain. These are useful starting points, not mutually exclusive categories.

Fine-tuning does not make facts stored in weights reliably addressable, current, or permission-aware. Retrieval still needs source freshness, access checks, and evidence validation. A fine-tuned model can also be paired with retrieval. [RAG Architecture and Implementation / 检索增强生成](../rag/rag-architecture-and-implementation.md) covers external evidence; [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md) covers task evaluation.

Before training, compare a prompt-only baseline and any relevant retrieval or workflow baseline. Consider fine-tuning when the remaining gap is repeatable, the training data represents the target behavior, and the expected improvement justifies training, deployment, and future update work.

## Which method should you choose? / 如何选择微调方法？

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

## How much and what kind of data? / 需要多少数据，数据应是什么样？

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

## A training and evaluation workflow / 训练与评估流程

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

## What are SFT, RLHF, and DPO? / 什么是 SFT、RLHF 与 DPO？

**Supervised fine-tuning (SFT)** trains on desired responses or demonstrations. It can teach response patterns represented by the examples; it does not guarantee that the model follows every instruction or is safe in unseen situations.

In the InstructGPT research pipeline, human-written demonstrations were used for supervised fine-tuning, human preference comparisons trained a reward model, and reinforcement learning optimized the policy against that reward. This describes that paper's method, not every assistant model's training process.

**Direct Preference Optimization (DPO)** is a preference-learning method that optimizes from chosen and rejected responses without fitting a separate reward model in the same way as the classic RLHF pipeline. It still depends on preference data, a training objective, and modeling assumptions; it is not automatically more accurate or safer than PPO. Choose based on the available data, infrastructure, and evaluation.

Preference labels can be inconsistent or reflect the annotators and rubric. Evaluate the resulting model for the intended task and relevant failure cases; do not infer safety from a preference-training label alone.

## Related notes / 相关笔记

- [RAG Architecture and Implementation / 检索增强生成](../rag/rag-architecture-and-implementation.md) covers retrieval for external and changing evidence.
- [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md) covers held-out evaluation and failure analysis.
- [AI Safety in Production / 生产环境中的 AI 安全](../safety/ai-safety-in-production.md) covers runtime controls that training does not replace.

## Sources / 来源

- Hu et al., [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685).
- Dettmers et al., [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314).
- Houlsby et al., [Parameter-Efficient Transfer Learning for NLP](https://arxiv.org/abs/1902.00751); Li and Liang, [Prefix-Tuning](https://arxiv.org/abs/2101.00190); Lester et al., [The Power of Scale for Parameter-Efficient Prompt Tuning](https://arxiv.org/abs/2104.08691).
- Ouyang et al., [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155).
- Rafailov et al., [Direct Preference Optimization: Your Language Model is Secretly a Reward Model](https://arxiv.org/abs/2305.18290).
- OpenAI, [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization), [Supervised fine-tuning](https://developers.openai.com/api/docs/guides/supervised-fine-tuning), [Direct preference optimization](https://developers.openai.com/api/docs/guides/direct-preference-optimization), and [Deprecations](https://developers.openai.com/api/docs/deprecations), checked 2026-10-15. The SFT/DPO pages describe OpenAI-specific methods, not general availability: the optimization page marks fine-tuning docs as legacy and says the platform is winding down. The deprecations page says organizations that had not previously run fine-tuning cannot create jobs; since 2026-07-02, organizations that have not run inference on a fine-tuned model in the prior 60 days also cannot create jobs. Active existing customers lose job creation on 2027-01-06, while inference continues until the base model is deprecated. Check current availability before treating OpenAI API fine-tuning as an option.
