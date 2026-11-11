# 何时应微调来弥补稳定的行为差距？

## 案例：日志助手反复给出错误标签

值班工程师希望构建日志助手，把失败日志归入稳定标签并用固定 JSON 结构输出，方便后续聚合。举例：输入 `Build 73 failed: connect ECONNREFUSED 10.0.0.8:5432`；团队约定的标签是 `database_connection_refused`，简短摘要是“构建进程无法连接数据库”。但模型有时把它标成 `database_timeout`，有时又在 JSON 前后附上说明文字。日志已包含分类所需的信号，错误在标签映射和输出行为，而不是少了当日外部事实。

先把指令、标签定义、示例、可用结构化输出和工作流改清楚，并在同一批代表性日志上建立基线。如果约束输出能解决 JSON 格式问题，就让应用用结构化输出保证格式；只有在标签误判等行为差距仍反复出现、且手头有经审查的正确示例时，才评估微调。按成因选择方法：

| 失败现象 | 先改变什么 | 何时进入微调评估 |
| --- | --- | --- |
| 缺少或变化中的服务事实 | 权威数据源、检索或 application programming interface（API，应用程序接口） | 微调不能代替数据刷新或权限检查；需要时把微调行为与检索组合。 |
| 指令、标签定义或流程不清 | 提示词、上下文、标签设计或工作流 | 只有这些因素稳定后还存在重复行为差距，训练样例也能表达正确行为时。 |
| 相同输入反复违反风格、分类或响应格式 | 先试更清楚的提示词与应用层结构约束 | 若特定任务行为仍稳定失败，可用代表性示范训练并用独立评估证明收益。 |

fine-tuning（微调）更新预训练模型的可训练参数，使目标示例所表达的行为在之后的调用中更常出现。权重并不是能按请求精确查询、保持实时或实施用户权限的数据库。外部证据仍需检索的来源时效和访问控制；可从[如何检索并使用经过授权的外部证据？](../rag/rag-architecture-and-implementation.md)了解应用如何提供证据。训练前应比较提示词基线与相关检索或工作流基线；只有数据代表目标行为、差距可重复且预期收益覆盖训练、部署和维护成本时，才值得继续。

## 标签差距应该更新哪些参数？

日志助手案例里，目标不是重写基础模型的所有能力，而是在不改变底座的前提下，调整选定投影矩阵，使模型更常把 `ECONNREFUSED` 映射到正确标签。这可以用 low-rank adaptation（LoRA，低秩适配）说明。若采用列向量记法，基础投影 `W` 将 `k` 维输入映到 `d` 维输出；LoRA 冻结 `W`，只训练两个小矩阵组成的增量：

$$
W' = W + \Delta W,\qquad \Delta W = BA
$$

其中 `A` 的形状是 `r × k`，`B` 是 `d × r`，所以增量 `BA` 的形状与 `W` 相同；`r` 是中间瓶颈宽度，也是 `BA` 秩的上限。由于 `A` 或 `B` 本身可能秩不足，`BA` 的实际秩可以小于 `r`；增量至多沿 `B` 的 `r` 个列方向调整。看一个可手算的小矩阵：设输入 `x=[1,2]ᵀ`、基础权重 `W=I`（单位矩阵，因此 `Wx=x`）、`r=1`、`A=[1,1]`、`B=[0.1,−0.2]ᵀ`。那么 `Ax=3`，`B(Ax)=[0.3,−0.6]ᵀ`，也就是 `W'x=Wx+B(Ax)=[1.3,1.4]ᵀ`。输入先经一维瓶颈，再投影回两维；真实网络里这只是某层的局部表示增量，不是直接把最终类别标签改成目标值。

训练时，cross-entropy loss（交叉熵损失）经模型计算图反向传播到 `A` 和 `B`，优化器逐步修改它们；基础矩阵 `W` 不接收参数更新。冻结并不切断上游梯度：如果 `x` 来自仍可训练的前一层，反向传播仍会用固定的 `W`（和 LoRA 分支）计算传回 `x` 的梯度。这里的区别见[一个矩阵怎样把梯度传给参数和输入](../foundations/training-gradients-and-optimizers.md#一个矩阵怎样把梯度传给参数和输入)。常见实现还会乘缩放因子 `α/r`，并可能在适配路径加入 dropout（随机失活）；本例为了便于手算省略这些配置。若目标权重的方向或存储转置与这里不同，矩阵形状会随实现转置，但可训练参数仍是低秩增量。

在 `4096 × 4096` 的单个投影矩阵上取 `r=8`，LoRA 矩阵共有 `r(k+d)=8(4096+4096)=65,536` 个可训练数值；原稠密矩阵有 `dk=4096×4096=16,777,216` 个数值。这仅比较单个目标矩阵。全模型的训练参数量取决于目标层数和矩阵数，不能凭一个矩阵的比例预测整模型的质量或训练显存。

**rank（矩阵秩）**决定这个增量能表达多少方向：较低的 `r` 参数和显存更少，但可能表达不了复杂的行为差距；较高的 `r` 容量更大，训练和部署成本也增加。应从可运行的小秩实验开始，用相同数据与留出样例比较，不存在保证质量的通用秩。

其他方法改动模型的不同部分。full fine-tuning（全量微调）更新全部可训练基础权重，适应容量较大但算力、内存和模型产物成本也高；quantized LoRA（QLoRA，量化低秩适配）冻结量化基础权重并训练 LoRA，QLoRA 论文在其特定实验中使用 4-bit 量化，不能推定任一量化、模型或任务都适用。adapter（适配器）在 Transformer 块中加入小型可训练模块；prefix tuning（前缀微调）学连续向量，作为各层的前缀表示输入 Transformer；prompt tuning（软提示微调）则在输入嵌入前加少量连续向量。后两者不是普通可见文本 token（词元），也不同于编辑指令文字的提示词工程。

有些服务栈能把适配器合并进基础权重，有些会在推理时保留额外运算；训练器和服务端支持也不同。选方法时应把是否需保留底座、可用显存、预期行为复杂度、训练产物和服务路径放到同一比较中，并以任务评估确认，而不是假定某一种参数高效微调必然胜过其他方法。

## 案例中的标签如何变成训练损失？

若错误行为已被归因到稳定的标签映射，训练数据就要把“输入信号”和“期望输出”配对。日志助手的一个合成监督样例如下：

~~~json
{
  "messages": [
    {"role": "user", "content": "Classify this build log using one approved category and return JSON only: Build 73 failed: connect ECONNREFUSED 10.0.0.8:5432"},
    {"role": "assistant", "content": "{\"category\":\"database_connection_refused\",\"summary\":\"构建进程无法连接数据库。\"}"}
  ]
}
~~~

supervised fine-tuning（SFT，监督微调）将期望回答分成目标 token（词元）序列 `y₁,…,y_N`。计算第 `j` 个 token 的目标时，模型接收输入 `x` 和训练样本中已知的正确前缀 `y_{<j}`，再预测 `y_j`；逐步喂入这些标注前缀的方式称为 teacher forcing（教师强制），不是先让模型自由生成前缀。常见的 cross-entropy（交叉熵）目标可写为

$$
L(\theta)=-\frac{1}{N}\sum_{j=1}^{N}\log\pi_\theta(y_j\mid x,y_{<j}).
$$

这是对每个目标 token 的负对数概率取平均。假设只看标签位置的两个候选词元 `[database_timeout, database_connection_refused]`，玩具 logits（未归一化分数）为 `[2,0]`，模型把错误候选放在前面。softmax（归一化指数函数）概率为 `[e²,1]/(e²+1)≈[0.880797,0.119203]`，目标 one-hot（独热向量）是 `[0,1]`，正确标签对应的损失为 `−ln(1/(e²+1))=ln(e²+1)≈2.126928`。对这两个候选分数的梯度是 `p−onehot(y)≈[+0.880797,−0.880797]`；梯度下降会降低错误候选的相对分数、提高正确候选的相对分数。实际共享参数还受其他 token 位置与样本的梯度影响，所以不能由这一项推断模型更新后的具体概率。真实输出有许多 JSON 与摘要 token，损失会覆盖整段目标回答；这个二候选小算例只解释梯度方向，不是实测模型数字。

梯度再沿模型的共享计算图回传到被选参数：全量微调会更新全部可训练权重；LoRA 会更新 `A`、`B`，基础矩阵保持冻结。也就是说，SFT 不会把一条日志作为可查询记录附加到模型中，而是用许多输入—目标对让模型的参数逐渐偏向它们共同表达的映射。新日志分布若与训练样本不同，已学到的标签映射仍可能失效。

不存在能预测成功的通用样本数。小而干净的数据集可以先验证目标行为是否可学；更广泛或罕见的错误类型需要更多覆盖。针对本例，应覆盖 `ECONNREFUSED` 的不同措辞、日志前后缀、允许标签的边界案例与相邻的 `timeout` 标签，避免只把同一行复制很多遍。不要把样本量当成质量证据。

> [!example] 摘要也可以作为监督目标
> 这是一个合成输入—输出对，用来说明 SFT 也可教摘要措辞；它不是法律建议，也不是所有训练器的通用格式。
>
> ~~~json
> {
>   "messages": [
>     {"role": "user", "content": "Summarize this sample clause: The supplier will deliver the parts by June 1."},
>     {"role": "assistant", "content": "The supplier must deliver the parts by June 1."}
>   ]
> }
> ~~~

数据审查要检查事实与标签是否正确、输入类型和失败切片是否有代表性、标注口径是否一致、重复样本、敏感信息，以及使用权。按日志来源、事故类别或时间段切分训练和评估集；同一次事故里的近重复日志若随机分到两侧，会让测试集看似独立却实际泄漏。合成数据可以扩充覆盖，但仍需检查错误事实、标签偏差和模板重复。

## 怎样组织训练、调参并验收？

1. **界定重复失败。** 记录当前行为、目标行为、运行约束和不能接受的回归。例如记录日志助手把 `ECONNREFUSED` 误判成 timeout 的比例，以及合法标签全集和 JSON 契约。
2. **先立无训练基线。** 固定基础模型、提示词、结构约束、检索和工作流；在代表性样本上量出错误类型和分母。任务若允许在应用层保证 schema，应同时评估这项控制。
3. **构建并审查样例。** 去重，排除未经授权或敏感的数据，检查标签、覆盖范围及目标 token 格式。
4. **拆分数据。** 训练集用来算梯度，验证集用来选训练轮数和其他控制；选择固定后，最终独立测试集才用于比较候选与基线。记录如何切分和可能的泄漏风险。
5. **固定模型与训练方法。** 确认基础模型、全量或参数高效方法、训练器版本、数据格式、许可条款，以及产物能否由目标服务加载。
6. **跑小实验并记录配置。** 记录学习率和调度、训练轮数、每卡批次、梯度累积、有效批次、数据版本、LoRA 秩与目标模块、检查点和验证指标。
7. **冻结方案后做独立比较。** 用相同输入与运行设置比较微调前后模型；检查整体成功率、重要标签切片、非法 JSON、安全、成本和时延。
8. **谨慎部署并监控。** 对模型和回滚路径做版本管理，遵守数据保留与同意规则，并继续观察相同业务结果。

训练任务成功完成，只说明优化过程运行了，不代表模型泛化变好。不能只凭一次分数上升就声称模型发生了记忆或泛化；还要检查样本重叠、任务切片和独立证据。

learning rate（学习率）决定优化器更新的尺度；对某个设置来说过大可能使训练不稳定，过小则可能在既定预算内学不到目标行为。epoch（训练轮数）表示完整遍历训练样本的次数；多训练几轮可能改善拟合，也可能开始过拟合。batch size（批次大小）控制一次优化更新综合多少样本，影响显存和梯度波动。若每卡微批次为 `b`、设备数为 `D`、gradient accumulation（梯度累积）步数为 `K`，在各步样本等权的常见设置下，有效批次近似 `bDK`。梯度累积让多次较小的前向与反向计算先累积梯度，再进行一次参数更新；若固定有效批次，增加 `K` 只会增加两次更新之间的微步数，不会改变按样本计算的更新频率。若保持 `b` 和 `D` 不变而增大 `K`，有效批次也增大，每轮数据对应的优化器更新数就会减少。样本长度不等时，还要查看训练器如何按 token 聚合损失。

训练集用来拟合权重，验证集用来比较训练控制并支持提前停止，最终留出测试集要等所有选择固定后再用。反复根据最终测试集调参，会让它泄漏进开发过程。训练损失和验证损失有助于诊断，却不能替代目标行为指标；应将结果与未微调基线比较，并检查重要切片。

## SFT、偏好优化和奖励训练怎样取舍？

supervised fine-tuning（SFT，监督微调）用期望回答或演示训练模型。它能教会示例实际表达的响应模式，但不能保证模型在未见场景中遵循所有指令或保持安全；生产环境仍需运行时控制，可参阅[生产环境中的 AI 安全](../safety/ai-safety-in-production.md)。

InstructGPT 研究中的 reinforcement learning from human feedback（RLHF，基于人类反馈的强化学习）流程先用人工撰写的演示做 SFT，再用人类偏好比较训练奖励模型，最后让强化学习优化策略来获得更高奖励。这描述的是该论文的方法，不代表所有助手模型的训练过程。

direct preference optimization（DPO，直接偏好优化）从同一提示下被选中和被拒绝的回答优化模型，不像经典 RLHF 流程那样先训练一个单独的奖励模型。它仍依赖偏好数据、目标函数和建模假设，不能据此推断 DPO 一定比 proximal policy optimization（PPO，近端策略优化）更准确或更安全。应根据数据、基础设施和评估结果选择。

reinforcement learning with verifiable rewards（RLVR，可验证奖励强化学习）适用于存在可靠程序检查或其他独立结果检查的任务；它和 SFT、离线蒸馏承担不同作用。以推理任务为例，[可验证奖励如何训练推理能力？](reward-based-reasoning-training.md)沿一道题讲清采样、判分、组内优势、策略更新、零方差奖励组和长度截断，并比较最终验收方式。偏好标签仍可能互相矛盾，或只反映标注者与 rubric（评分准则）的选择；偏好训练完成后，仍要用目标任务及相关失败案例评估，不能仅凭偏好标签判断安全。

> [!info]- 来源
> 下列来源分别支持微调方法、偏好训练和平台可用性。LoRA 参数示例及训练流程中的建议为教学演算或工程实践。
>
> - **低秩与参数高效微调。** Hu et al., [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)；Dettmers et al., [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314)；Houlsby et al., [Parameter-Efficient Transfer Learning for NLP](https://arxiv.org/abs/1902.00751)；Li and Liang, [Prefix-Tuning](https://arxiv.org/abs/2101.00190)；Lester et al., [The Power of Scale for Parameter-Efficient Prompt Tuning](https://arxiv.org/abs/2104.08691)。
> - **SFT 与 DPO。** Ouyang et al., [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155)；Rafailov et al., [Direct Preference Optimization: Your Language Model Is Secretly a Reward Model](https://arxiv.org/abs/2305.18290)。
> - **OpenAI API 上的可用性。** [Model optimization](https://developers.openai.com/api/docs/guides/model-optimization)、[Supervised fine-tuning](https://developers.openai.com/api/docs/guides/supervised-fine-tuning)、[Direct preference optimization](https://developers.openai.com/api/docs/guides/direct-preference-optimization)、[Reinforcement fine-tuning](https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning) 与 [Deprecations](https://developers.openai.com/api/docs/deprecations)，核对日期为 2026-11-06。OpenAI 正在逐步结束自助微调：2026-05-07 起，没有既往微调记录的组织不能创建训练任务；2026-07-02 起，过去 60 天未对微调模型运行推理的组织也不能创建新任务；现有合格用户可创建任务至 2027-01-06，或基础模型更早停服之日。微调模型推理会持续到其基础模型退役；先前训练文档仍在迁移，具体资格与模型时限应按官方页面核验。平台可用性仅适用于 OpenAI API，不是对通用微调方法的限制。
