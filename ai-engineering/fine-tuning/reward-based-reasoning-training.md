# 可验证奖励如何训练推理能力？

给模型一道可复算的小题：“4 盒各装 3 个螺丝，另有 2 个散装螺丝，共有多少个？”答案是 `4×3+2=14`。若训练提示要求模型把推理和答案分别放进 `<think>...</think>`、`<answer>...</answer>`，一个运行器可以检查最终数值和标记格式。下面先沿四条回答算分，再追踪分数怎样改变模型的下一次输出概率。

若要判断这类训练是否适合稳定的行为差距，可先读[何时应微调来弥补稳定的行为差距？](fine-tuning-strategies.md)；要设计独立验收，再读[如何判断 AI 系统是否满足任务契约？](../evaluation/llm-evaluation-methods.md)。

## 检查器判的是什么，没判的又是什么？

reinforcement learning with verifiable rewards（RLVR，可验证奖励强化学习）要求 reward（奖励）来自能独立复核的目标，例如参考答案比较、结构约束或程序测试。模型评委即使能输出分数，若它只是估计开放式质量或是否符合参考答案，也属于带误差的近似奖励；过程评审器同理，不能仅凭“会评分”就称为可验证结果。RLVR 仍属于 reinforcement learning（RL，强化学习）；其训练循环如下：

~~~mermaid
flowchart TD
    Q[数学题 q] --> S[旧策略采样 G 个回答]
    S --> V[结果与格式检查器判分]
    V --> A[在同题组内计算优势]
    A --> U[按裁剪策略更新当前模型]
    U --> N[下一批题继续采样]
    U -. 可选 Kullback–Leibler（KL）散度正则 .-> R[参考策略]
~~~

检查器必须针对明确目标设计；不同类型的检查器能支持不同强度的结论：

- **规则型 verifier（规则检查器/程序检查器）。** 数学任务可解析最终答案并检查等价性；代码任务可编译并运行预先定义的测试；结构任务可检查 schema（结构模式）和必需字段。在规则覆盖范围内，结果可重复、成本较低。编译成功或通过现有单测只说明满足这些检查，不证明程序对所有输入正确；答案解析器也可能漏掉等价表达或容忍错误。
- **学得的 verifier、评审模型或 reward model（奖励模型，RM）。** 可以用成对偏好训练 RM，也可以让模型对照参考答案判断简短答案是否正确。它能覆盖难以写成规则的质量，但分数是代理信号，受评分准则（rubric）、评审偏差和训练数据影响；这类模型分数可用于 model-based RL（基于模型奖励的强化学习），但如果无法独立复核评分本身，就不属于可验证奖励。策略越会优化该分数，越可能找出评审器漏洞。
- **process reward model（PRM，过程奖励模型）。** 它对推理步骤分别给分，可提供比最终答案更多的过程信号，但要先定义步骤边界、收集可靠步骤标签并检查评审器是否被利用。步骤切分和标注质量可能成为新的误差来源。

“可验证”描述检查目标能否被独立执行或复核，不意味着 formal verification（形式化验证）证明了模型程序的全部行为。outcome reward（结果奖励）与 process reward（过程奖励）描述“检查整段结果还是给中间步骤打分”，并不决定“奖励是否可验证”：程序可判最终答案，也可有带误差的模型评委给整段回答打分；PRM 可逐步评分，但标注和评审仍可能出错。若结果检查器只看最终答案，它没有逐步核对 chain-of-thought（CoT，思维链）；即使最终答案由程序精确判定，也不能因此推断轨迹中的每个中间推理都正确。

## 同题采样怎样转成组内优势？

给定题目 `q`，old policy（旧策略）`π_old` 会按当前生成分布采样 `G` 条 rollout（采样轨迹）`o₁,…,o_G`。每条回答是若干 token（词元）组成的序列；检查器只根据结果与格式给整条回答 reward（奖励）`r_i`。在 DeepSeek-R1-Zero 的规则奖励中，答案准确性 `r_acc` 和格式 `r_format` 等权相加；下表用一个单独设计的教学检查器演算同类的两个信号，不声称复刻 R1 的解析器：教学检查器可从带或不带标记的输出摘录中提取末尾数值，准确性与标记格式分别判分。四条回答如下：

| 回答 | 输出摘录 | 最终答案正确 | 标记格式正确 | `r_acc+r_format` |
| --- | --- | ---: | ---: | ---: |
| A | `15`，没有指定标记 | 0 | 0 | 0 |
| B | `14`，没有指定标记 | 1 | 0 | 1 |
| C | `<think>4×3=12；加2仍是12</think><answer>12</answer>` | 0 | 1 | 1 |
| D | `<think>4×3=12；12+2=14</think><answer>14</answer>` | 1 | 1 | 2 |

C 的过程虽有算术错误，只要结果奖励的检查器只验证最终答案 `12` 与格式，仍可能得到格式分；这不是逐步正确性标签。

R1 论文 §2.2 对数学准确性奖励举的是指定格式中的最终答案；格式奖励则明确要求推理放在 `<think>` 标记中。上表为了分开演算两项信号，允许摘录不带标记仍被教学解析器读出数值；不要把这条玩具解析规则当成 R1 的实现细节。

Group Relative Policy Optimization（GRPO，组相对策略优化）用同题回答的平均奖励作 baseline（基线），并通常按同题奖励标准差缩放 advantage（优势）：

$$
\bar r=\frac{1}{G}\sum_{i=1}^{G}r_i,\qquad
\hat A_i=\frac{r_i-\bar r}{s_r},\qquad
\hat A_{i,t}=\hat A_i
$$

这里 `s_r` 是这 `G` 个奖励的 standard deviation（标准差），`t` 是回答中的 token 位置。对结果监督，算法把同一标量优势 `\hat A_i` 广播给回答中的每个生成 token；它告诉优化器“这条轨迹相对同题其他轨迹表现如何”，不告诉它“哪一行推理出错”。实现通常会在分母加一个与裁剪参数不同的小常数 `\epsilon_{std}`，避免 `s_r=0` 时除零，但这不会为零方差组创造新信号。

这组奖励为 `[0,1,1,2]`，均值为 `(0+1+1+2)/4=1`。为方便手算，假设用总体标准差：

$$
s_r=\sqrt{\frac{(0-1)^2+(1-1)^2+(1-1)^2+(2-1)^2}{4}}
=\sqrt{0.5}\approx0.707.
$$

于是 A、B、C、D 的优势依次约为 `−1.414、0、0、+1.414`。D 相对组平均奖励较好，得到提高其轨迹概率的信号；A 相对较差，得到降低其轨迹概率的信号；B 和 C 落在均值上，按这次组内比较没有优势信号。该教学演算不声称复刻某个框架的标准差定义、奖励组合、掩码或 loss reduction（损失聚合），实现细节要按锁定版本检查。

## 概率比、裁剪与 KL 怎样约束参数更新？

设题目 `q` 下，旧策略采样出回答 D；在其已生成前缀 `o_{i,<t}` 后，旧策略给这个已采样 token 概率 `0.20`。更新后，当前策略在同一个 `q`、同一个前缀和同一个 token 上重新打分，得到 `0.26`。这两个已算出的概率构成 importance ratio（概率比）：

$$
\rho_{i,t}(\theta)=
\frac{\pi_\theta(o_{i,t}\mid q,o_{i,<t})}
{\pi_{\theta_{old}}(o_{i,t}\mid q,o_{i,<t})}
=\frac{0.26}{0.20}=1.30.
$$

proximal policy optimization（PPO，近端策略优化）的 clipped surrogate（裁剪代理目标）限制这次更新能从该 token 的优势中获得多少收益。设裁剪宽度 `\epsilon_{clip}=0.2`，裁剪区间为 `[1-\epsilon_{clip},1+\epsilon_{clip}]=[0.8,1.2]`。D 的优势是 `+1.414`：未裁剪项为 `1.30×1.414≈1.838`，裁剪项为 `1.20×1.414≈1.697`，目标取较小值。因此，该 token 的实际新旧概率比仍是 `1.30`；达到上界后只是这一个正优势项进入平台，其他 token、共享参数上的梯度和 KL 项仍可能改变模型概率。

裁剪不会硬性限制实际的新旧概率比，也不会把答案裁成正确或错误；它只改变 surrogate 中特定优势项的梯度。若优势为负，低于下界时也会出现相应的平台。裁剪范围过窄可能削弱很多 token 的学习信号，过宽则可能允许不稳定的大更新，必须用目标任务验证。

参考策略与采样时的旧策略承担不同作用。旧策略 `\pi_{\theta_{old}}` 是产生本批回答的分布，出现在概率比的分母；参考策略 `\pi_{ref}` 是一个用于限制策略漂移的锚点。Kullback–Leibler divergence（KL 散度）衡量两个概率分布的差异，例如参考分布为 `[0.9,0.1]`、当前分布为 `[0.8,0.2]` 时，按当前分布对数值求和得到

$$
D_{KL}([0.8,0.2]\Vert[0.9,0.1])
=0.8\ln\frac{0.8}{0.9}+0.2\ln\frac{0.2}{0.1}\approx0.044403\text{ nats}.
$$

`nats` 是使用自然对数得到的单位；此二元分布在单个前缀上枚举两种可能，因而这里是精确求和的 KL。实际 RL 目标通常对题目和旧策略 rollout 求期望，GRPO 会用采样响应或 token 上的概率项估计 KL；DeepSeekMath 给出采样估计，R1 也把 sampled response 上的 KL 项写进目标。因此，不能把“精确遍历每个上下文的完整词表”当作所有 GRPO 实现的前提。`β=0` 时 KL 项关闭；非零 `β` 会增加贴近参考策略的约束，也会带来额外计算。

现在各项已经有了对应量：组内奖励决定优势，概率比比较新旧策略，裁剪限制 surrogate，KL 项约束相对参考策略的漂移。一个常见的 token 级 GRPO 最大化目标写作

$$
\mathcal{J}(\theta)=\mathbb{E}\left[
\frac{1}{G}\sum_{i=1}^{G}\frac{1}{|o_i|}
\sum_{t=1}^{|o_i|}
\left[
\min\!\left(\rho_{i,t}\hat A_i,
\operatorname{clip}(\rho_{i,t},1-\epsilon_{clip},1+\epsilon_{clip})\hat A_i\right)
-\beta\widehat D_{i,t}
\right]
\right].
$$

`\widehat D_{i,t}` 是在回答 `i` 的位置 `t`、沿同一已采样前缀计算的 KL 惩罚估计；本式将它和 surrogate 一起按 token、回答和题目聚合。它不是上面枚举两个候选得到的精确 KL，也不自动保证在旧策略采样与当前策略已经偏离时仍无偏。

这里最大化 `\mathcal{J}`；若训练器定义的是最小化损失，则对应最小化 `-\mathcal{J}`。该教学目标先对每条回答的 token 项取长度平均，再对组内回答取均值；最外层期望对题目和旧策略采出的回答组求平均。这只是一个讲解用的 reduction。论文写法和框架目标并不完全相同：DeepSeekMath 的 GRPO 公式写逐 token 概率比并按每条回答长度取均值；DeepSeek-R1 正文把策略比写成整条输出的概率比；TRL 和 verl 又提供不同的损失聚合、奖励标准化与 KL 配置。公式相同处说明策略更新机制，具体归约和超参数仍须按所用实现核对。

> [!info] 为什么结果分数会影响整条序列？
> 一条回答的对数概率可分解为各个条件 token 对数概率之和：`log π(o_i|q) = Σ_t log π(o_{i,t}|q,o_{i,<t})`。策略梯度沿这条计算链反向传播，所以一个终局奖励可以提高或降低整条采样轨迹的概率。它没有把标准答案写进参数，也没有给轨迹中每一步单独贴上正确或错误标签。

### GRPO 为什么不需要 critic（价值网络）？

PPO 常训练一个 critic（价值函数/价值网络）估计状态价值，再用它计算优势；对大语言模型来说，这通常需要额外模型和显存。GRPO 不拟合该价值网络，而是用同一道题的多条回答的奖励均值作基线，并可按组内标准差归一化。它省去了 critic，却需要为一道题生成多个回答、运行多次检查器；因此节省模型内存的代价是更多 rollout（采样轨迹）和判分开销。若检查器昂贵，或生成回答很长，这部分成本可能成为瓶颈。

## 哪些奖励组不给学习信号？

若同一道题的全部回答奖励都相同，例如 `[1,1,1,1]` 或 `[0,0,0,0]`，则每个 `r_i - \bar r = 0`，所以优势全为零。给标准差分母加 `\epsilon_{std}` 能避免除以零，却不会改变分子为零的事实；对这道题来说，policy gradient（策略梯度）没有区分候选答案的信号。

这通常出现在过容易的题（所有采样都答对）或当前策略很难攻克的题（所有采样都答错）。Decoupled Clip and Dynamic Sampling Policy Optimization（DAPO，解耦裁剪与动态采样策略优化）的 dynamic sampling（动态筛组）会保留有正确也有错误回答的组，以减少二元准确率任务中零优势组占用有效 batch 的情况；这会改变进入更新的题目分布，需要监控覆盖面，不是所有任务都该采用的通用规则。只用结果奖励时，组内差异来自试验回答；有格式、长度或偏好等额外奖励时，即使正确性相同，奖励也可能不同，但增加的信号是否对齐任务目标仍需单独检查。

## 为什么回答长度和截断会改写训练权重？

原始 GRPO 常先把每条回答的 token 损失按自身长度平均，再对组内回答平均。设某条回答有 20 个 token、另一条有 200 个 token，若两条每 token 的优势和损失大小相近，前者每个 token 会乘约 `1/20`，后者会乘约 `1/200`。因此，短的正优势回答可得到更大的单位 token 权重；长的负优势回答则可能被摊薄。这是某种损失 reduction（聚合方式）的长度加权效应，不是“GRPO 一定喜欢长思维链”或“总是惩罚长答案”。

后续改法针对的偏差不同，应按自己的目标与 token 分布比较：

- **DAPO** 改为按累积 batch 中的有效 token 数聚合，让长回答里的 token 不会仅因回答长就被样本级平均稀释；这也会让长回答贡献更多总 token 项。它另以分开的上下裁剪幅度提高探索 token 的上调空间，并在其二元准确率设置中动态筛除同奖组。论文的示例取 `epsilon_low=0.2`、`epsilon_high=0.28`。这些选择服务于该论文的长 CoT 训练设置。
- **Dr.GRPO（GRPO 的论文修正版）** 讨论样本长度平均和按组奖励标准差归一化带来的回答长度与题目难度加权，并提出移除这两项归一化、用固定生成预算作分母。它改变了每题和每 token 的权重；论文论证与实验限于其 R1-Zero-style 设置，不意味着对所有任务都是默认最佳。

硬生成上限会截断回答。若检查器将未完成答案一律判错，训练可能把超长但接近正确的轨迹当作完整错误来惩罚，给策略带来噪声。DAPO 论文用截断样本 loss mask（损失掩码）和预期长度之后的软惩罚来处理这种情况。另一种做法是为任务定义经过验证的长度成本；若任务确实要求短回答，不能简单把长度惩罚当噪声丢弃。要判断截断样本是否可公平计分，应同时观察长度、终止原因、奖励和通过率。

## DeepSeek-R1-Zero 与最终 R1 有什么不同？

DeepSeek-R1 没有发明强化学习或 GRPO。GRPO 已由 DeepSeekMath 于 2024 年提出，R1 将其用于大规模 reasoning post-training（推理后训练）。R1-Zero 展示的是一种特定训练结果：在 DeepSeek-V3-Base 上不先做 supervised fine-tuning（SFT，监督微调），直接用规则型准确性和格式奖励训练策略。论文观察到响应变长、出现反思和探索行为；这些是该实验中的行为变化，不是每条推理链经过验证或模型获得类人的自我意识的证据。

DeepSeek-R1 是多阶段流程，不等于 R1-Zero。论文描述的主线如下：

~~~mermaid
flowchart TD
    B[DeepSeek-V3-Base] --> Z[R1-Zero 分支<br/>不先做 SFT；规则正确性与格式奖励做 GRPO]
    B --> S[收集数千条冷启动推理示范<br/>先做 SFT]
    S --> R[第一阶段推理 RL<br/>规则奖励 + 语言一致性奖励]
    R --> RS[拒绝采样与筛选<br/>约 600K 推理样例]
    RS -.筛选后的训练数据.-> D[约 800K 样例做第二次 SFT]
    B -->|重新从 Base 权重开始| D
    D --> M[第二阶段多目标 RL<br/>推理规则奖励 + 通用偏好/安全模型奖励]
    M --> F[DeepSeek-R1]
~~~

第一阶段先收集数千条更易读、对话式的冷启动推理样本，再用规则奖励继续强化推理，并加语言一致性奖励降低混语。rejection sampling（拒绝采样）阶段从第一阶段 checkpoint（检查点）为每题生成多个回答，保留正确轨迹；部分难以写规则的样本由 DeepSeek-V3 对照参考答案辅助判断，再过滤混语、过长段落或代码块等难读样例，形成约 600K 推理样本。另加入约 200K 非推理样本，重新从 DeepSeek-V3-Base 权重做第二次 SFT。这里由第一阶段 RL 传过来的是筛选后的数据；第二次 SFT 不直接沿用该 RL checkpoint 的权重。

论文将两条训练线的配置分开报告：R1-Zero 每题采样 16 条、`β=0.001`、每 400 步刷新参考模型；最大回答长度在第 8.2K 步之前为 32,768 token，之后增至 65,536。最终 R1 第一阶段推理 RL 也报告每题 16 条、`β=0.001`、每 400 步刷新参考模型，最大长度 32,768 token，并设 GRPO clip ratio `\epsilon_{clip}=10`。这些是论文的阶段配置，尤其 `10` 不是通用 clip 默认值。

第二阶段 RL 对推理题仍用规则奖励；对通用帮助性与安全性问题使用模型奖励：帮助性评估主要看最终摘要，安全性则检查整条响应。模型奖励用在通用偏好任务，不代表 R1-Zero 的推理训练用神经奖励模型逐步判对错。R1 作者报告帮助性奖励模型分数上升时，Codeforces 表现却下降，作为 reward hacking（奖励投机）的例子；作者放弃在大规模推理 RL 中使用神经过程奖励模型的理由包括过程步骤难定义、标注难扩展和模型本身可能被利用，但仍提出它们可用于重排或引导搜索。

## 哪种训练信号符合手头目标？

| 目标与可用数据 | 适合先试什么 | 主要代价与边界 |
| --- | --- | --- |
| 已知期望输出，能写出稳定示范 | supervised fine-tuning（SFT，监督微调） | 训练信号来自示范实际表达的行为；未见输入上的泛化需要独立验证。 |
| 有可靠的程序化结果检查，希望模型通过尝试发现更好的解题轨迹 | 在线 RLVR，例如 GRPO | 需要多次采样、稳定可复现的检查器、足够算力和独立验收；奖励只覆盖检查器所定义的目标。 |
| 有更强教师模型生成并筛选过的轨迹，希望小模型学会这些解法 | offline distillation（离线蒸馏）或 rejection-sampling SFT（拒绝采样后的 SFT） | 学生从固定轨迹模仿，不需要每轮再按学生当前策略 rollout；效果受教师质量、样例覆盖和筛选器限制。 |
| 有成对偏好标签，目标偏主观且不易精确程序化 | direct preference optimization（DPO，直接偏好优化）或其他偏好优化 | 学到的是标注偏好与训练目标，不是外部事实真值，也不是结果正确性的证明。 |

R1 的蒸馏例子属于离线监督：教师先产生推理回答，筛选后的固定回答用于 SFT，学生训练时不会每轮自己采样再按 verifier 更新。论文 Appendix F 的一个受限比较中，Qwen2.5-32B-Base 做超过 10K 步 RL 后得到的 Qwen2.5-32B-Zero，和 DeepSeek-R1-Distill-Qwen-32B 在 AIME 2024 的 pass@1（单次采样通过率）分别为 47.0% 和 72.6%。这个实验显示该教师轨迹在该基线、数据和评估协议下很有效，不能推出蒸馏总胜过 RL。R1 自身也将 SFT 与 RL 组合使用。

## 多教师在策略蒸馏又提供了什么训练信号？

离线 SFT 把固定教师回答当作目标 token；在线 RLVR 让学生自己采样回答、再用一个标量 reward 给轨迹分配优势。还有一种目标是：学生先在自己的 rollout 中走到某个 prefix（生成前缀），教师在这个相同前缀上提供整个词表的下一 token 分布，学生再对齐该分布。这称为 on-policy distillation（OPD，在策略蒸馏）：训练前缀由学生当前策略产生，因此训练覆盖学生实际会走到的状态；软分布则让教师可以给未采样到的 token 也提供信息。

DeepSeek-V4 论文 v1 报告了一种多教师 OPD 流程。数学、代码、Agent、指令遵循等领域分别训练 specialist teacher（领域教师模型）：先用领域数据做 SFT，再用领域 prompt 与 GRPO 奖励做强化学习。之后，统一 student（学生模型）从自己的策略采样轨迹，按任务从相关教师的完整输出分布学习。十多个是整个训练系统的教师数量，不是每个前缀都要运行全部教师。该报告将这一阶段的 mixed RL 改为 OPD；它没有说 specialist 阶段也跳过 SFT/RL。

把来自不同任务的训练样本按适用教师分组，多教师目标可概括为

$$
\mathcal{L}_{OPD}(\theta)
=\sum_{j=1}^{M}w_j\,\mathbb{E}_{s\sim\mathcal{D}_j}\left[D_{KL}\!\left(
\pi_\theta(\cdot\mid s)\,\Vert\,\pi_{E_j}(\cdot\mid s)
\right)\right].
$$

`\mathcal{D}_j` 表示适用教师 `j` 的任务中，学生 rollout 实际走到的前缀分布；`π_θ` 是学生在该前缀的分布，`π_Ej` 是该教师在同一前缀上的分布，`w_j` 是教师权重。求和概括整个训练混合，不要求把每个前缀都交给所有教师。对每个学生前缀，目标先用学生和教师完整词表 logits 经 softmax（归一化指数函数）得到两张概率分布，再对全词表精确求和计算 reverse KL（反向 KL），方向为学生到教师；它不是只评估刚采样到的一个 token，也不是对最终回答打分后广播一个优势。DeepSeek-V4 报告认为，相较于只用学生刚采样的 token 估计 KL，全词表 logit 蒸馏在其系统中梯度方差更低、训练更稳定；这是该报告的方法选择，不能推为所有任务的通用结论。

看只有两个候选 token 的小分布：学生 `Q=(0.8,0.2)`，教师 `P=(0.9,0.1)`。学生到教师的方向是

$$
D_{KL}(Q\Vert P)=0.8\ln\frac{0.8}{0.9}+0.2\ln\frac{0.2}{0.1}
\approx0.044403\text{ nats}.
$$

反过来则是 `D_KL(P∥Q)=0.9 ln(0.9/0.8)+0.1 ln(0.1/0.2)≈0.036690 nats`。结果不同，因为 KL 对求和式左侧分布中的概率质量加权；因此不能把 `D_KL(student∥teacher)` 和 `D_KL(teacher∥student)` 当作可互换的“相似度”。两分布演算说明方向，不代表报告中的实测 loss 或质量增益。

| 机制 | 训练时的输入状态 | 提供的信号 | 与其他机制的区别 |
| --- | --- | --- | --- |
| 在线 RLVR / GRPO | 学生自己采样的完整回答 | RLVR 用可独立复核的规则分数；一般 GRPO 也可用模型奖励，但评委分数不因此变成可验证结果 | 依赖 reward 与采样组，不直接给每个词的教师分布。 |
| 离线 SFT / 轨迹蒸馏 | 固定收集的教师回答 | 每个目标 token 的 cross-entropy（交叉熵） | 学生不必在每个训练步骤自己 rollout；不会自动覆盖学生独有的前缀。 |
| 多教师 OPD | 学生自己 rollout 到的前缀 | 各教师在同前缀上的全词表分布与反向 KL | 信号是分布对齐，不是结果 reward 或固定答案 token。 |
| mixture of experts（MoE，混合专家）路由 | 同一个模型的一次前向计算 | 路由器选择内部 expert 子网络参与计算 | 这是模型架构；DeepSeek-V4 报告的 specialist teacher 是独立完整模型权重，并非 MoE 层里的 FFN 子网。 |

全词表 logits 的缓存成本也很大。V4 报告的实现按样本对应的教师索引组织数据，缓存该教师的末层 hidden state，再在训练时加载相应输出头重建词表分布；它避免为所有训练位置长期保存完整 logits，但仍需教师推理和输出头计算。

OPD 的多位教师是训练时的来源；学生要吸收其能力进自己的参数，推理时不需要继续调用这十多个教师，也不等于部署一个 teacher 路由器。报告给出按教师重要性设权重的 full-vocabulary（全词表）方案，但没有给出可迁移到任意任务的通用权重或样本调度规则。它应作为独立的蒸馏选择与 RLVR、离线 SFT 对照，不应称为所有训练任务的最佳方案。

## 当前训练器提供哪些可用控制？

训练库的默认值是一个实现版本的起点，不是适用于所有任务的推荐答案。版本固定后，应检查奖励如何合并、优势是否除组内标准差、每个回答怎样聚合 token 损失、策略概率比如何裁剪、KL 项是否加载参考模型，以及到达长度上限时哪些 token 会参与 loss。

截至 2026-11-06，Hugging Face TRL 的 `v1.17.1` 发布版在 `GRPOConfig` 中提供下列控制。TRL 的 GRPO 指南也展示了用 `GRPOTrainer`、prompt（提示）数据集和数学准确性奖励函数训练的可执行入门样例；要复现行为，应依赖版本 tag 的配置与代码，不要仅靠无版本的网页说明。

| TRL `v1.17.1` 参数 | 发布版默认值 | 应按任务检查什么 |
| --- | --- | --- |
| `beta` | `0.0` | 默认不加载参考模型、不加 KL 项。若要限制偏离参考策略，显式设非零值并记录内存与质量代价。 |
| `epsilon` | `0.2` | PPO-style ratio clip 的基础幅度；低概率探索 token 是否能获得足够上调空间要单独观察。 |
| `loss_type` | `"dapo"` | 默认采用 DAPO 式 token 聚合。还提供 `"grpo"` 与 `"dr_grpo"` 等选项，reduction 会改变长短回答的权重。 |
| `scale_rewards` | `"group"` | 默认按组标准差缩放奖励。Dr.GRPO 风格配置还要考虑关闭这项缩放；只改 loss reduction 不等于复现论文算法。 |
| `mask_truncated_completions` | `False` | 默认仍将截断回答纳入损失。若任务不能公平评分未完成答案，可显式启用 mask，并监控丢弃比例和长度分布。 |

`epsilon_high` 可设置与下界不同的上裁剪幅度；DAPO 在其特定实验中用 `0.28`，不是 TRL 通用默认值。TRL 当前版本的字段组合应连同模型、奖励函数、数据划分、生成上限、随机种子和有效 batch 一起记入实验配置。

verl 的 `v0.9.1` 发布版也能做 GRPO，但其通用 `ppo_trainer.yaml` 默认 `algorithm.adv_estimator=gae`，即 generalized advantage estimation（GAE，广义优势估计），不是 GRPO；若要跑 GRPO，需显式设为 `grpo`。同一 tag 中 `algorithm.norm_adv_by_std_in_grpo=true`，而 `algorithm.use_kl_in_reward=false`、`actor.use_kl_loss=false`；actor 的 `loss_agg_mode` 默认是 `token-mean`。因此，verl 的基础 PPO 配置不能当作完整 GRPO 论文设置；要核对优势估计、奖励标准化、loss reduction 及两种 KL 路径各自的字段。`filter_groups.enable` 默认关闭，采用 DAPO 式筛组时还要显式配置及检查组筛选指标。

TRL `v1.17.1` 和 verl `v0.9.1` 是本节核对过的具体发布版；新版本可能改变默认值或实现。一个可复现的训练说明至少应记录库的 tag/commit、模型 checkpoint、reward 函数与聚合权重、`G`、优势标准化和 `epsilon`、clip、loss reduction、KL 两项设置、完成长度及截断 mask。不要用一个显示 `GRPO` 的命令行参数概括这些差异。

## 怎样独立验收训练结果？

训练样本上的 reward 上升只说明策略更会满足优化目标；不能据此证明泛化。把同一可靠评分规则应用在未参与训练、调参或筛选的新题上，仍是衡量该结果指标的有效方式。若 reward 只检查数学答案，最终验收还应覆盖解析边界、等价答案、错解侥幸答对、格式问题及未知题型；代码任务则要检查隐藏测试、边界输入、sandbox 隔离和副作用。通过现有 verifier 只说明通过该检查集，需检查 verifier 本身的覆盖和漏洞；一个分数也不能单独证明广义质量或安全性。

在方案确定前留出不参与训练、调参或筛选的独立任务集与隐藏测试。用相同提示词、模型推理设置和采样预算比较训练前后 checkpoint，按任务难度、长度、终止原因和失败类型报告分母与成功率，并一并看格式、重复、拒答、安全、时延和成本。若目标包含帮助性、风格或开放式质量，应在训练偏好集之外使用盲审人工样例或已校准评审器；模型评审器分数不能替代事实检查。发现候选用格式、措辞或可预测漏洞取得高训练分但任务质量下降时，应修复奖励或检查器，再从未参与优化的验收集重测。

训练前先小规模比较组大小、奖励组合、标准差缩放、clip、KL、loss reduction 和截断处理，固定并记录选择理由。DAPO、Dr.GRPO 或原始 GRPO 的效果取决于任务奖励是否可信、回答长度分布、题目难度及实现细节，没有一个只凭算法名称就能得出的跨任务最佳配置。

> [!info]- 来源
> 下列来源映射到正文中的机制与实验。数值推演是教学合成值；训练器参数来自标明版本的官方文档或代码。
>
> - **GRPO、同题组优势与 PPO 对照。** Shao et al., *DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models*（2024，§4.1、Appendix A.1.6），[论文](https://arxiv.org/html/2402.03300)。原始算法、结果/过程监督和 token 级目标。
> - **R1-Zero 奖励与完整 R1 流程。** DeepSeek-AI, *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning*（arXiv:2501.12948v2，2026-01-04；§2.1–2.3、§3.1–3.2、Appendix B.3/B.4.2/B.5、F.1、G.2），[v2 HTML](https://arxiv.org/html/2501.12948v2)。支持准确性/格式奖励、奖励模型使用范围、训练阶段、reward hacking、过程奖励模型和蒸馏比较。
> - **DAPO。** Yu et al., *DAPO: An Open-Source LLM Reinforcement Learning System at Scale*（arXiv:2503.14476v2，2025-05-20；§3.1–3.4、§4），[v2 HTML](https://arxiv.org/html/2503.14476v2)。支持 Clip-Higher、动态筛组、token-level loss 和截断处理；结论限于该训练系统与实验。
> - **Dr.GRPO。** Liu et al., *Understanding R1-Zero-Like Training: A Critical Perspective*（arXiv:2503.20783v2，2025-10-06；§3.1–3.2），[v2 HTML](https://arxiv.org/html/2503.20783)。支持回答长度与题目难度加权分析及 Dr.GRPO 的固定预算分母方案。
> - **TRL 当前配置。** Hugging Face [TRL `v1.17.1` 发布记录](https://github.com/huggingface/trl/releases/tag/v1.17.1)（2026-10-30）、[该 tag 的 `grpo_config.py`](https://github.com/huggingface/trl/blob/v1.17.1/trl/trainer/grpo_config.py)和[当前 GRPOTrainer 文档](https://huggingface.co/docs/trl/grpo_trainer)，截至 2026-11-06 核对。版本配置支持 `beta=0`、`epsilon=0.2`、`loss_type="dapo"`、`scale_rewards="group"`、`mask_truncated_completions=False`；无版本文档可能晚于 tag 更新。
> - **verl 当前配置。** [verl `v0.9.1` 发布记录](https://github.com/verl-project/verl/releases/tag/v0.9.1)（2026-09-20）、[通用 PPO trainer 配置](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/config/ppo_trainer.yaml)、[actor 配置](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/config/actor/actor.yaml)、[GRPO 结果优势实现](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/ppo/core_algos.py)。配置说明默认优势估计是 GAE、组奖励标准差归一化打开、两种 KL 路径关闭，actor 聚合默认 `token-mean`；实际训练还须检查所用 recipe 的覆盖值。
> - **DeepSeek-V4 多教师 OPD。** DeepSeek-AI, *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*（arXiv:2606.19348v1，2026-04-26；截至 2026-11-06 核对公开报告仍为 v1；§5.1.1–5.1.2、§5.2.2），[v1 HTML](https://arxiv.org/html/2606.19348v1)。支持 specialist 阶段 SFT+GRPO、student 前缀上的多教师 reverse KL 与全词表 logits 蒸馏。权重安排和通用路由规则不由该报告建立。
