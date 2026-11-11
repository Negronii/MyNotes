# 可验证奖励如何训练推理能力？

给模型一道可复算的小题：“4 盒各装 3 个螺丝，另有 2 个散装螺丝，共有多少个？”答案是 `4×3+2=14`。若训练提示要求模型把推理和答案分别放进 `<think>...</think>`、`<answer>...</answer>`，一个运行器可以检查最终数值和标记格式。前半篇沿四条回答走完一次 GRPO 更新；后半篇再对照 R1 的真实训练阶段、其他训练信号、训练器配置与独立验收。

若要判断这类训练是否适合稳定的行为差距，可先读[何时应微调来弥补稳定的行为差距？](fine-tuning-strategies.md)；要设计独立验收，再读[如何判断 AI 系统是否满足任务契约？](../evaluation/llm-evaluation-methods.md)。

## 检查器判的是什么，没判的又是什么？

reinforcement learning with verifiable rewards（RLVR，可验证奖励强化学习）要求 reward（奖励）来自能独立复核的目标，例如参考答案比较、结构约束或程序测试。模型评委即使能输出分数，若它只是估计开放式质量或是否符合参考答案，也属于带误差的近似奖励；过程评审器同理，不能仅凭“会评分”就称为可验证结果。RLVR 描述奖励的来源，不限定唯一策略优化算法。本文沿一条训练批次追踪机制：按题采样回答组 → 检查器给分 → 组内计算优势 → clipped policy objective（裁剪策略目标）→ 反向传播与优化器更新。

检查器必须针对明确目标设计；不同类型的检查器能支持不同强度的结论：

- **规则型 verifier（规则检查器/程序检查器）。** 数学任务可解析最终答案并检查等价性；代码任务可编译并运行预先定义的测试；结构任务可检查 schema（结构模式）和必需字段。在规则覆盖范围内，结果可重复、成本较低。编译成功或通过现有单测只说明满足这些检查，不证明程序对所有输入正确；答案解析器也可能漏掉等价表达或容忍错误。
- **学得的 verifier、评审模型或 reward model（奖励模型，RM）。** 可以用成对偏好训练 RM，也可以让模型对照参考答案判断简短答案是否正确。它能覆盖难以写成规则的质量，但分数是代理信号，受评分准则（rubric）、评审偏差和训练数据影响；这类分数可用于使用学得奖励模型训练策略的强化学习，但如果无法独立复核评分本身，就不属于可验证奖励。策略越会优化该分数，越可能找出评审器漏洞。
- **process reward model（PRM，过程奖励模型）。** 它对推理步骤分别给分，可提供比最终答案更多的过程信号，但要先定义步骤边界、收集可靠步骤标签并检查评审器是否被利用。步骤切分和标注质量可能成为新的误差来源。

“可验证”描述检查目标能否被独立执行或复核，不意味着 formal verification（形式化验证）证明了模型程序的全部行为。outcome reward（结果奖励）与 process reward（过程奖励）描述“检查整段结果还是给中间步骤打分”，并不决定“奖励是否可验证”：程序可判最终答案，也可有带误差的模型评委给整段回答打分；PRM 可逐步评分，但标注和评审仍可能出错。若结果检查器只看最终答案，它没有逐步核对 chain-of-thought（CoT，思维链）；即使最终答案由程序精确判定，也不能因此推断轨迹中的每个中间推理都正确。

结果监督在回答结束时打分，再把该回答的同一个组内优势广播给其生成 token；过程监督在推理步骤末端评分，并可让不同步骤位置的 token 得到不同优势。两种监督描述信号附着的位置；奖励来自规则检查还是有误差的学习型评审器，是另一个维度。本文先走完结果奖励的主线，再用独立合成例说明过程奖励的记分粒度。

## 同题采样怎样转成组内优势？

给定题目 `q`，旧策略快照 `π_{θ_old}` 从当时的生成分布独立采样 `G` 条 rollout（采样轨迹）`o₁,…,o_G`。采样时保留题目、实际生成前缀、选中的 token 和旧策略给该 token 的概率；更新时，当前策略会在相同前缀上重算同一个已采样 token 的概率。若刚开始重打分时当前参数仍等于旧快照，概率比为 `1`，但优势项仍可产生非零梯度。每条回答由 token（词元）组成；检查器根据结果与格式给整条回答 reward（奖励）`r_i`。在 DeepSeek-R1-Zero 的规则奖励中，答案准确性 `r_acc` 和格式 `r_format` 等权相加；下表用一个单独设计的教学检查器演算同类的两个信号，不声称复刻 R1 的解析器：教学检查器可从带或不带标记的输出摘录中提取末尾数值，准确性与标记格式分别判分。四条回答如下：

| 回答 | 输出摘录 | 最终答案正确 | 标记格式正确 | `r_acc+r_format` |
| --- | --- | ---: | ---: | ---: |
| A | `15`，没有指定标记 | 0 | 0 | 0 |
| B | `14`，没有指定标记 | 1 | 0 | 1 |
| C | `<think>4×3=12；加2仍是12</think><answer>12</answer>` | 0 | 1 | 1 |
| D | `<think>4×3=12；12+2=14</think><answer>14</answer>` | 1 | 1 | 2 |

C 的中间计算把 `4×3+2` 算成 `12`，所以 `12` 与正确答案 `14` 不符；若教学检查器分别核对最终数值与标记格式，C 只得格式分。这不是逐步正确性标签。

R1 论文 §2.2 对数学准确性奖励举的是指定格式中的最终答案；格式奖励则明确要求推理放在 `<think>` 标记中。上表为了分开演算两项信号，允许摘录不带标记仍被教学解析器读出数值；不要把这条玩具解析规则当成 R1 的实现细节。

Group Relative Policy Optimization（GRPO，组相对策略优化）用同题回答的平均奖励作 baseline（基线），并通常按同题奖励标准差缩放 advantage（优势）：

$$
\bar r=\frac{1}{G}\sum_{i=1}^{G}r_i,\qquad
\hat A_i=\frac{r_i-\bar r}{s_r},\qquad
\hat A_{i,t}=\hat A_i
$$

这里 `s_r` 是这 `G` 个奖励的 standard deviation（标准差），`t` 是回答中的 token 位置。对结果监督，算法把同一标量优势 $\hat A_i$ 广播给回答中的每个生成 token；它告诉优化器“这条轨迹相对同题其他轨迹表现如何”，不告诉它“哪一行推理出错”。实现通常会在分母加一个与裁剪参数不同的小常数 $\epsilon_{std}$，避免 `s_r=0` 时除零，但这不会为零方差组创造新信号。

这组奖励为 `[0,1,1,2]`，均值为 `(0+1+1+2)/4=1`。为方便手算，假设用总体标准差：

$$
s_r=\sqrt{\frac{(0-1)^2+(1-1)^2+(1-1)^2+(2-1)^2}{4}}
=\sqrt{0.5}\approx0.707.
$$

于是 A、B、C、D 的优势依次约为 `−1.414、0、0、+1.414`。D 相对组平均奖励较好，得到提高其轨迹概率的信号；A 相对较差，得到降低其轨迹概率的信号；B 和 C 落在均值上，按这次组内比较没有优势信号。该教学演算不声称复刻某个框架的标准差定义、奖励组合、掩码或 loss reduction（损失聚合），实现细节要按锁定版本检查。

## 概率比、裁剪与 KL 怎样约束参数更新？

以 D 最终答案中的 `14` 为例：教学中假定它恰好是一个 token，前缀 `o_{i,<t}` 已包含之前的推理与 `<answer>` 标记。假定旧策略给该 token 的概率为 `0.20`。在一次策略更新后的假设状态中，当前策略在同一个题目、前缀和 token 上重新打分为 `0.26`。这是一个已超过上裁剪界的独立示例；下文单 logit 推导会明确从另一个当前概率 `0.22` 的假设状态起算，`0.22` 不是由 `0.26` 倒退得到。两概率构成 importance ratio（概率比）：

$$
\rho_{i,t}(\theta)=
\frac{\pi_\theta(o_{i,t}\mid q,o_{i,<t})}
{\pi_{\theta_{old}}(o_{i,t}\mid q,o_{i,<t})}
=\frac{0.26}{0.20}=1.30.
$$

proximal policy optimization（PPO，近端策略优化）的 clipped surrogate（裁剪代理目标）限制这次更新能从该 token 的优势中获得多少收益。设裁剪宽度 $\epsilon_{clip}=0.2$，裁剪区间为 $[1-\epsilon_{clip},1+\epsilon_{clip}]=[0.8,1.2]$。D 的优势是 `+1.414`：未裁剪项为 `1.30×1.414≈1.838`，裁剪项为 `1.20×1.414≈1.697`，目标取较小值。因此，该 token 的实际新旧概率比仍是 `1.30`；达到上界后只是这一个正优势项进入平台，其他 token、共享参数上的梯度和 KL 项仍可能改变模型概率。

裁剪不会硬性限制实际的新旧概率比，也不会把答案裁成正确或错误；它只改变 surrogate 中特定优势项的梯度。若优势为负，低于下界时也会出现相应的平台。裁剪范围过窄可能削弱很多 token 的学习信号，过宽则可能允许不稳定的大更新，必须用目标任务验证。

参考策略与采样时的旧策略承担不同作用。旧策略 $\pi_{\theta_{old}}$ 是产生本批回答的分布，出现在概率比的分母；参考策略 $\pi_{ref}$ 是一个用于限制策略漂移的锚点。Kullback–Leibler divergence（KL 散度）衡量两个概率分布的差异，例如参考分布为 `[0.9,0.1]`、当前分布为 `[0.8,0.2]` 时，按当前分布对数值求和得到

$$
D_{KL}([0.8,0.2]\Vert[0.9,0.1])
=0.8\ln\frac{0.8}{0.9}+0.2\ln\frac{0.2}{0.1}\approx0.044403\text{ nats}.
$$

`nats` 是使用自然对数得到的单位；此二元分布在单个前缀上枚举两种可能，因而这里是精确求和的 KL。实际 RL 目标通常对题目和旧策略 rollout 求期望，GRPO 会用采样响应或 token 上的概率项估计 KL；DeepSeekMath 给出采样估计，R1 也把 sampled response 上的 KL 项写进目标。因此，不能把“精确遍历每个上下文的完整词表”当作所有 GRPO 实现的前提。`β=0` 时 KL 项关闭；非零 `β` 会增加贴近参考策略的约束，也会带来额外计算。

现在各项已经有了对应量：组内奖励决定优势，概率比比较新旧策略，裁剪限制 surrogate，KL 项约束相对参考策略的漂移。设题目 $q\sim\mathcal{D}$，并在给定 $q$ 后从旧策略快照独立采样回答 $o_1,\ldots,o_G$；记 $\mathbb{E}_{q,o_{1:G}}$ 为对这些题目和回答组求平均。可以分两步写出一个常见的 token 级 GRPO 最大化目标：先把位置 $(i,t)$ 的收益记为 $g_{i,t}$，再聚合整批数据。

$$
\begin{aligned}
g_{i,t}(\theta)
&=\min\Bigl(\rho_{i,t}\hat A_i,\; \\
&\qquad\operatorname{clip}(\rho_{i,t},1-\epsilon_{clip},1+\epsilon_{clip})\hat A_i\Bigr)
-\beta\widehat D_{i,t}.
\end{aligned}
$$

$$
\mathcal{J}(\theta)=\mathbb{E}_{q,o_{1:G}}\left[
\frac{1}{G}\sum_{i=1}^{G}\frac{1}{|o_i|}
\sum_{t=1}^{|o_i|}g_{i,t}(\theta)
\right].
$$

$\widehat D_{i,t}$ 是在回答 `i` 的位置 `t`、沿同一已采样前缀计算的 KL 惩罚估计；本式将它和 surrogate 一起按 token、回答和题目聚合。它不是上面枚举两个候选得到的精确 KL，也不自动保证在旧策略采样与当前策略已经偏离时仍无偏。

这里 $\mathcal{D}$ 是题目分布，给定 $q$ 后每条 $o_i$ 都从旧策略 $\pi_{\theta_{old}}(\cdot\mid q)$ 独立采样；$o_i$ 是组内第 $i$ 条 token 序列，$|o_i|$ 是其纳入目标的 token 数，$t$ 是该回答中的 token 位置。式内已显式求和 token 与回答，外层期望对题目和旧策略采样的回答组取平均。这里最大化 $\mathcal{J}$；若训练器定义的是最小化损失，则对应最小化 $-\mathcal{J}$。该教学目标先对每条回答的 token 项取长度平均，再对组内回答取均值。这只是一个讲解用的 reduction。论文写法和框架目标并不完全相同：DeepSeekMath 的 GRPO 公式写逐 token 概率比并按每条回答长度取均值；DeepSeek-R1 正文把策略比写成整条输出的概率比；TRL 和 verl 又提供不同的损失聚合、奖励标准化与 KL 配置。公式相同处说明策略更新机制，具体归约和超参数仍须按所用实现核对。

下式采用 DeepSeekMath 的 token 级 sampled KL（采样 KL）写法：

$$
\begin{aligned}
\delta_{i,t}&=\log\pi_{ref}(o_{i,t}\mid q,o_{i,<t})
-\log\pi_{\theta}(o_{i,t}\mid q,o_{i,<t}),\\[6pt]
\widehat D_{i,t}&=\exp(\delta_{i,t})-\delta_{i,t}-1.
\end{aligned}
$$

DeepSeek-R1 正文 Eq. 2 对整条采样回答 $o_i$ 的概率比使用相同的标量变换；这与此处按 token、同一前缀计算的粒度不同。若此处的 token 按当前策略 $\pi_{\theta}$ 采样，这个非负形式的期望对应 $D_{KL}(\pi_{\theta}\Vert\pi_{ref})$；训练批次通常先按旧策略采样，更新过程中当前策略也会移动，因此不能把一次 sampled KL 数值等同于枚举当前策略的完整词表 KL。

### 一个回答的优势怎样改变模型参数？

检查器给出的 reward 和组内 advantage 在这一步被当作固定数值；策略不会通过对答案解析器求导来更新。对一个已采样 token，记 $p_\theta=\pi_\theta(o_{i,t}\mid q,o_{i,<t})$、$p_{old}=\pi_{\theta_{old}}(o_{i,t}\mid q,o_{i,<t})$。在裁剪未进入平台且不计 KL 时，将该 token 的单项目标记为 $\mathcal{J}_{i,t}=\rho_{i,t}\hat A_i$；其梯度为

$$
\nabla_\theta\mathcal{J}_{i,t}
=\frac{\hat A_i}{\pi_{\theta_{old}}(o_{i,t}\mid q,o_{i,<t})}
\nabla_\theta\pi_\theta(o_{i,t}\mid q,o_{i,<t})
=\rho_{i,t}\hat A_i\nabla_\theta\log\pi_\theta(o_{i,t}\mid q,o_{i,<t}).
$$

中间一步将概率比 $\rho=p_\theta/p_{old}$ 展开，最后一步使用 $\nabla\log p=(\nabla p)/p$；这里旧概率 $p_{old}$ 与组内优势 $\hat A_i$ 对 $\theta$ 固定。

接着用一个单 logit 教学例把它算到参数。假设该 token 的当前概率是 $p_\theta=0.22$、旧策略概率是 $p_{old}=0.20$，组内优势为 $\hat A_i=1.414$。这是独立于前面 $0.26$ 越界例的另一个假设状态。把目标 token 的 logit 设为 $\theta$、竞争 token 的 logit 固定为 $0$，二元 softmax 就是

$$
p_\theta=\sigma(\theta)=\frac{e^\theta}{e^\theta+1},\qquad
\frac{\partial p_\theta}{\partial\theta}=p_\theta(1-p_\theta),\qquad
\frac{\partial\log p_\theta}{\partial\theta}=1-p_\theta.
$$

先由假设概率反算参数：$\theta=\ln(0.22/0.78)\approx-1.265666$。于是概率比 $\rho=0.22/0.20=1.10$ 仍在裁剪区间 $[0.8,1.2]$ 内，未裁剪项的梯度为

$$
\frac{\partial\mathcal{J}_{i,t}}{\partial\theta}
=\frac{1.414}{0.20}[0.22(1-0.22)]
=1.10\times1.414\times(1-0.22)
\approx1.213212.
$$

以学习率 $\eta=0.01$ 做 SGD 梯度上升：$\theta'=\theta+\eta\,\partial\mathcal{J}_{i,t}/\partial\theta\approx-1.253534$。再代回二元 softmax，$p'_\theta=\sigma(\theta')=e^{\theta'}/(e^{\theta'}+1)\approx0.222089$，即目标 token 概率从 $0.220000$ 升到约 $0.222089$。这是忽略其他 token、KL、梯度裁剪和优化器状态的一维示意。真实模型把本批中每个有效 token 的优势项对同一共享参数求梯度，再沿共享计算图聚合，由所选优化器更新启用训练的参数；一条序列的 log 概率是这些条件 token log 概率之和，故 token 级梯度汇成轨迹级更新信号。本步更新后的参数会作为下一批生成的策略；采样时缓存旧策略对已选 token 的概率，随后当前策略在相同前缀上重算该 token 的概率。若把目标写成最小化 loss，则使用 $L=-\mathcal{J}$。完整矩阵反向传播和 AdamW/Muon 怎样把梯度变成参数值，见[训练梯度与优化器](../foundations/training-gradients-and-optimizers.md#adamw-和-muon-怎样使用已经算好的梯度)。

> [!info] 为什么结果分数会影响整条序列？
> 一条回答的概率是各个条件 token 概率相乘，取对数后连乘变成相加：`log π(o_i|q) = Σ_t log π(o_{i,t}|q,o_{i,<t})`。若暂时固定其他位置的条件概率，`14` 这一处从 `0.22` 升到约 `0.222089`，整条 D 的概率就乘上约 `0.222089/0.22 = 1.0095`。真实模型会通过共享参数同时改变多个位置，不能直接把这个倍率当成训练结果。终局奖励经这条计算链提供轨迹级更新信号，没有给每一步单独贴上正确或错误标签。

### GRPO 为什么不需要 critic（价值网络）？

PPO 常训练一个 critic（价值函数/价值网络）估计状态价值，再用它计算优势；对大语言模型来说，这通常需要额外模型和显存。GRPO 不拟合该价值网络，而是用同一道题的多条回答的奖励均值作基线，并可按组内标准差归一化。它省去了 critic，却需要为一道题生成多个回答、运行多次检查器；因此节省模型内存的代价是更多 rollout（采样轨迹）和判分开销。若检查器昂贵，或生成回答很长，这部分成本可能成为瓶颈。

## 如果逐步评分，优势会怎样变化？

DeepSeekMath 的 process supervision（过程监督）在每个推理步骤末端给分。论文将同一道题的回答组内所有步骤末端的奖励放在同一集合中标准化；设 $index_i(j)$ 是回答 $i$ 中第 $j$ 步结束 token 的位置，$\tilde r_i^{index_i(j)}$ 是回答 $i$ 在该步骤末端的标准化奖励。位置为 $t$ 的 token 会累计结束位置在 $t$ 或之后的步骤奖励：

$$
\hat A_{i,t}^{process}=\sum_{j:\,index_i(j)\ge t}\tilde r_i^{index_i(j)}.
$$

用四条两步回答做一组可复算的合成例。先把每条回答的**原始步骤分之和**作为 outcome reward，得到 `[0,2,2,4]`；均值为 `2`，总体标准差为 `√2≈1.414`。结果监督用这四个总分计算优势。

过程监督则把同题回答组的八个原始步骤分 `[0,0,0,2,2,0,2,2]` 放在一起，均值与总体标准差都为 `1`，所以每个原始步骤分减去 `1` 就得到它的标准化分数。两种计算的结果放在一起看：

| 回答 | 原始步骤分 | 原始总分 → 结果优势 | 标准化步骤分 | 第二步结束 token 的过程优势 |
|---|---|---|---|---|
| 1 | `[0,0]` | `0 → −1.414` | `[−1,−1]` | `−1` |
| 2 | `[0,2]` | `2 → 0` | `[−1,+1]` | `+1` |
| 3 | `[2,0]` | `2 → 0` | `[+1,−1]` | `−1` |
| 4 | `[2,2]` | `4 → +1.414` | `[+1,+1]` | `+1` |

第二步结束位置已经没有更晚的步骤，所以该 token 的过程优势只取第二步的标准化分数。第二条与第三条的结果优势都为 `0`，过程反馈却能区分它们第二步的方向。更早的 token 会按公式累计尚未结束的步骤分；例如在第一步结束位置，四条回答的累计值为 `−2、0、0、+2`，不能把这些标准化后的累计值误当成原始总分 `[0,2,2,4]`。

每条回答的步骤结束位置可以不同，`index_i(j)` 按该回答的 token 序列计数。使用过程优势时，把前面每个 token 目标中的 $\hat A_i$ 换成相应的 $\hat A_{i,t}^{process}$。该例用于解释结果/过程信号的粒度，不复刻特定模型的 PRM 或训练配方。

## 哪些奖励组不给学习信号？

若同一道题的全部回答奖励都相同，例如 `[1,1,1,1]` 或 `[0,0,0,0]`，则每个 $r_i - \bar r = 0$，所以优势全为零。给标准差分母加 $\epsilon_{std}$ 能避免除以零，却不会改变分子为零的事实；来自这组奖励优势的 clipped surrogate 梯度为零。若总目标另含 KL、熵奖励或辅助损失，它们仍可能提供梯度。

如果只按答对/答错给二元奖励，全同分组对应所有采样都答对或都答错，常见于过容易或当前策略很难攻克的题。若还给格式等分量打分，准确性相同不保证总奖励相同。Decoupled Clip and Dynamic Sampling Policy Optimization（DAPO，解耦裁剪与动态采样策略优化）的 dynamic sampling（动态筛组）会在其二元准确率设置中继续采样，筛掉全对、全错组，让保留组中既有正确也有错误回答；这减少零优势组占用有效 batch 的情况，但也改变了进入更新的题目分布。若任务还依赖格式、长度或偏好等奖励，以准确率作为筛组条件可能丢弃这些分量仍有差异的组，因此要检查筛选指标与奖励目标是否一致。

## 为什么回答长度和截断会改写训练权重？

DeepSeekMath 的 GRPO 目标先对每条回答的 token 项取均值，再对回答取均值：$\frac{1}{G}\sum_i\frac{1}{|o_i|}\sum_t \ell_{i,t}$。因此，长度为 20 和 200 的回答中，单个 token 的显式系数分别是 $1/(20G)$ 和 $1/(200G)$。忽略共同因子 $1/G$ 后分别为 $1/20$ 和 $1/200$；但完成轨迹的梯度还取决于各 token 的概率梯度与优势，不能只凭这个系数断言模型一定偏好短或长。DAPO 论文把长 CoT 中长回答的 token 信号容易被样本级平均稀释列为改动动机；Dr.GRPO 则分析样本长度和组内标准差归一化造成的样本权重变化。

后续改法针对的偏差不同，应按自己的目标与 token 分布比较：

- **DAPO** 按 batch 中的有效 token 数聚合，长回答会贡献更多 token 项；另以分开的上下裁剪幅度提高低概率探索 token 的上调空间，并在二元准确率设置中动态筛组。论文的 Qwen2.5-32B 配方取 $\epsilon_{low}=0.2$、$\epsilon_{high}=0.28$，并给出 16,384-token 期望长度与额外 4,096-token 软惩罚区间。这些选择服务于论文的长 CoT 配方，不是通用推荐。
- **Dr.GRPO** 在 R1-Zero-like 训练研究中去掉每条回答的长度平均和组内奖励标准差缩放，用固定生成预算作分母。它改变了样本和 token 的梯度权重；论文论证与实验限于其设置。2026 年一篇理论预印本进一步指出，在其 outcome-reward 假设下，长度加权不可能同时保证梯度估计无偏、又让每条轨迹的有效贡献与长度无关。因此不要把“Done Right”读成对所有任务都消除长度偏差的结论。
- **GSPO** 把重要性比定义在整条序列的几何平均概率上并做序列级裁剪。Qwen 团队报告它缓解其 Qwen3 MoE 训练中的 expert 激活波动；这是一种后续公开方案和特定实验结果，不是 DeepSeek-R1 的算法，也不表示所有 MoE 模型都必须改用 GSPO。

硬生成上限会截断回答。若检查器把因长度被截断的未完成答案直接判错，优化器可能把“没有机会输出结论”当作推理错误。DAPO 论文先测试屏蔽截断样本损失，再在长回答区间加入逐渐变强的 soft overlong punishment（软超长惩罚）；其最终配置及框架实现需分别核对。若任务确实要求简洁，长度成本也可以是目标的一部分，但应定义在可验证需求上。至少按正确/错误、长度和终止原因检查截断率与奖励，避免把长度偏好误当作质量提升。

## DeepSeek-R1-Zero 与最终 R1 有什么不同？

DeepSeek-R1 没有发明强化学习或 GRPO。GRPO 已由 DeepSeekMath 于 2024 年提出，R1 将其用于大规模 reasoning post-training（推理后训练）。R1-Zero 展示的是一种特定训练结果：在 DeepSeek-V3-Base 上不先做 supervised fine-tuning（SFT，监督微调），直接用规则型准确性和格式奖励训练策略。论文观察到响应变长、出现反思和探索行为；这些是该实验中的行为变化，不是每条推理链经过验证或模型获得类人的自我意识的证据。

R1-Zero 和 R1 是从同一底座出发的两条不同训练线，不能把 Zero 的“无预先 SFT”当成最终 R1 的完整配方。R1 的阶段边界和各阶段数据流见下表；后文再解释为什么奖励类型会随阶段变化。

| 训练线或阶段 | 数据与更新 | 该阶段的奖励/目标 |
| --- | --- | --- |
| R1-Zero | DeepSeek-V3-Base 直接进入 RL | 数学、代码、逻辑任务使用规则准确性与格式奖励做 GRPO，不先做 SFT。 |
| R1 冷启动与第一阶段 RL | 数千条冷启动推理示范先做 SFT，再进行推理 RL | 规则奖励；另加语言一致性奖励，缓解多语言混杂。 |
| R1 拒绝采样与第二次 SFT | 第一阶段 checkpoint 生成候选，筛出约 600K 推理样例并加入约 200K 通用样例；再从 Base 权重开始第二次 SFT | 这里传给 SFT 的是筛选数据，不是第一阶段 RL checkpoint 的参数。 |
| R1 第二阶段 RL | 从第二次 SFT 的权重继续训练 | 推理题使用规则奖励；通用帮助性与安全性任务使用模型奖励。 |

第一阶段先收集数千条更易读、对话式的冷启动推理样本，再用规则奖励继续强化推理，并加语言一致性奖励降低混语。rejection sampling（拒绝采样）阶段从第一阶段 checkpoint（检查点）为每题生成多个回答，保留正确轨迹；部分难以写规则的样本由 DeepSeek-V3 对照参考答案辅助判断，再过滤混语、过长段落或代码块等难读样例，形成约 600K 推理样本。另加入约 200K 非推理样本，重新从 DeepSeek-V3-Base 权重做第二次 SFT。这里由第一阶段 RL 传过来的是筛选后的数据；第二次 SFT 不直接沿用该 RL checkpoint 的权重。

论文将两条训练线的配置分开报告：R1-Zero 每题采样 16 条、`β=0.001`、每 400 步刷新参考模型；最大回答长度在第 8.2K 步之前为 32,768 token，之后增至 65,536。最终 R1 第一阶段推理 RL 也报告每题 16 条、`β=0.001`、每 400 步刷新参考模型，最大长度 32,768 token，并设 GRPO clip ratio $\epsilon_{clip}=10$。这些是论文的阶段配置，尤其 `10` 不是通用 clip 默认值。

第二阶段 RL 对推理题仍用规则奖励；对通用帮助性与安全性问题使用模型奖励：帮助性评估主要看最终摘要，安全性则检查整条响应。模型奖励用在通用偏好任务，不代表 R1-Zero 的推理训练用神经奖励模型逐步判对错。R1 作者报告帮助性奖励模型分数上升时，Codeforces 表现却下降，作为 reward hacking（奖励投机）的例子；作者放弃在大规模推理 RL 中使用神经过程奖励模型的理由包括过程步骤难定义、标注难扩展和模型本身可能被利用，但仍提出它们可用于重排或引导搜索。

DeepSeek-V4 技术报告在较新的配方中又描述了 rubric-guided generative reward model（GRM，生成式奖励模型）：针对难以用规则验证的任务，让生成式评审器评估轨迹，并直接对兼任评审器的 actor 做 RL。报告将其与传统标量奖励模型区分。它提供的是带准则约束的学习型评审信号，不因此变成规则可验证奖励；这是 V4 报告里的模型特定设计，不是 R1-Zero 配方的追溯改写。

## 哪种训练信号符合手头目标？

| 目标与可用数据 | 适合先试什么 | 主要代价与边界 |
| --- | --- | --- |
| 已知期望输出，能写出稳定示范 | supervised fine-tuning（SFT，监督微调） | 训练信号来自示范实际表达的行为；未见输入上的泛化需要独立验证。 |
| 有可靠的程序化结果检查，希望模型通过尝试发现更好的解题轨迹 | 在线 RLVR，例如 GRPO | 需要多次采样、稳定可复现的检查器、足够算力和独立验收；奖励只覆盖检查器所定义的目标。 |
| 有更强教师模型生成并筛选过的轨迹，希望小模型学会这些解法 | offline distillation（离线蒸馏）或 rejection-sampling SFT（拒绝采样后的 SFT） | 学生从固定轨迹模仿，不需要每轮再按学生当前策略 rollout；效果受教师质量、样例覆盖和筛选器限制。 |
| 有成对偏好标签，目标偏主观且不易精确程序化 | direct preference optimization（DPO，直接偏好优化）或其他偏好优化 | 学到的是标注偏好与训练目标，不是外部事实真值，也不是结果正确性的证明。 |

R1 的蒸馏例子属于离线监督：教师先产生推理回答，筛选后的固定回答用于 SFT，学生训练时不会每轮自己采样再按 verifier 更新。论文 Appendix F 的一个受限比较中，Qwen2.5-32B-Base 做超过 10K 步 RL 后得到的 Qwen2.5-32B-Zero，和 DeepSeek-R1-Distill-Qwen-32B 在 AIME 2024 的 pass@1（单次采样通过率）分别为 47.0% 和 72.6%。这个实验显示该教师轨迹在该基线、数据和评估协议下很有效，不能推出蒸馏总胜过 RL。R1 自身也将 SFT 与 RL 组合使用。

## 多教师在策略蒸馏又提供了什么训练信号？

离线 SFT 把固定教师回答当作目标 token；在线 RLVR 让学生自己采样回答、再用一个标量 reward 给轨迹分配优势。on-policy distillation（OPD，在策略蒸馏）的关键是学生用自己当前策略生成训练轨迹，教师在这些学生前缀上提供蒸馏信号；具体信号可按实现选取。DeepSeek-V4 报告采用完整词表 logits 计算 reverse KL（反向 KL），但全词表目标是该报告的实现选择，不是 OPD 的必要条件；报告将其与既有工作的采样 token KL 估计作方法比较。

DeepSeek-V4 论文 v1 报告了一种多教师 OPD 流程。数学、代码等领域分别训练 specialist teacher（领域教师模型）：每个教师是独立的完整模型，先用对应领域数据做 SFT，再用领域 prompt 与奖励信号，通过 GRPO 做强化学习。之后，统一 student（学生模型）从自己的策略采样轨迹，按任务从相关教师的完整输出分布学习。该 OPD 阶段使用十多位教师；报告没有要求每个前缀都运行全部教师。论文将这一阶段的 mixed RL 改为 OPD，并未说 specialist 阶段也跳过 SFT/RL。

以一道数学题为例，把训练和部署连起来看：

1. **按任务配教师。** 训练样本属于数学任务，因此使用完整的数学领域教师。选择发生在训练任务/样本尺度；这里的 teacher 是一套完整模型权重，不是某层 FFN 里的一个 expert 子网。
2. **由学生生成前缀。** student 接收题目提示词，从自己的策略 rollout（采样轨迹），走到一个前缀。
3. **教师在同一前缀上给分布。** 数学教师接收该 student prefix，对整个词表输出下一词元 logits；按 student 到 teacher 的 reverse KL 计算蒸馏目标，并用它更新统一 student 的参数。
4. **部署学生。** 线上运行已训练的 student，不需要继续调用领域教师。若 student 的架构含有 MoE，模型内部仍可在每个 token 到达 MoE FFN 子层时路由到若干 expert 子网。DeepSeek-V4 报告其初始若干 Transformer 层使用按输入 token ID 哈希的路由；这是模型前向中的 token 级 FFN 路由，不是按任务切换完整教师。

因此，教师选择决定“这条训练样本向哪一个完整领域模型学习”，MoE 路由决定“当前前向中的这个 token 经过哪些内部 FFN 子网”。二者粒度和对象都不同。

2026 年 11 月 5 日的一篇预印本在 Qwen3 配置中比较 reverse-KL OPD 与 GRPO：使用外部 post-trained teacher 时，在相同 FLOP 预算下，OPD 的准确率通常较低，且一些设置出现回答变长；若 teacher 是学生自己的 GRPO checkpoint，OPD 能以较少蒸馏计算恢复该 checkpoint 的单域能力。多域场景则有不同目标：把各域 GRPO specialist 合并成单个 student。该预印本的数学与代码两域实验，在达到 joint GRPO（按样本混合训练）相同准确率时，把 specialist 训练与蒸馏都计入的总 FLOPs 少 42%；这些结果限于其模型、数据、训练与评估设置，且是预印本证据。OPD 是否合适要按 teacher/student 差异、部署目标和总计算成本验收。

把来自不同任务的训练样本按适用教师分组，多教师目标可概括为

$$
\mathcal{L}_{OPD}(\theta)
=\sum_{j=1}^{M}w_j\,\mathbb{E}_{s\sim\mathcal{D}_j}\left[D_{KL}\!\left(
\pi_\theta(\cdot\mid s)\,\Vert\,\pi_{E_j}(\cdot\mid s)
\right)\right].
$$

$\mathcal{D}_j$ 表示适用教师 `j` 的任务中，学生 rollout 实际走到的前缀分布；`π_θ` 是学生在该前缀的分布，`π_Ej` 是该教师在同一前缀上的分布，`w_j` 是教师权重。当前更新把已采样前缀视为固定输入，通过学生在这些前缀上的输出分布求参数梯度；后续再用更新的学生采样。求和概括整个训练混合，不要求把每个前缀都交给所有教师。对每个学生前缀，目标先用学生和教师完整词表 logits 经 softmax（归一化指数函数）得到两张概率分布，再对全词表精确求和计算 reverse KL（反向 KL），方向为学生到教师；它不是只评估刚采样到的一个 token，也不是对最终回答打分后广播一个优势。DeepSeek-V4 报告认为，相较于只用学生刚采样的 token 估计 KL，全词表 logit 蒸馏在其系统中梯度方差更低、训练更稳定；这是该报告的方法选择，不能推为所有任务的通用结论。

看只有两个候选 token 的小分布：学生 `Q=(0.8,0.2)`，教师 `P=(0.9,0.1)`。学生到教师的方向是

$$
D_{KL}(Q\Vert P)=0.8\ln\frac{0.8}{0.9}+0.2\ln\frac{0.2}{0.1}
\approx0.044403\text{ nats}.
$$

反过来则是 $D_{KL}(P\Vert Q)=0.9\ln(0.9/0.8)+0.1\ln(0.1/0.2)\approx0.036690\text{ nats}$。结果不同，因为 KL 对求和式左侧分布中的概率质量加权；因此不能把 `D_KL(student∥teacher)` 和 `D_KL(teacher∥student)` 当作可互换的“相似度”。两分布演算说明方向，不代表报告中的实测 loss 或质量增益。

| 机制 | 训练时的输入状态 | 提供的信号 | 与其他机制的区别 |
| --- | --- | --- | --- |
| 在线 GRPO + 可验证奖励（RLVR） | 学生自己采样的完整回答 | 可验证奖励来自规则检查；一般 GRPO 也可用模型奖励，但评委分数不因此变成可验证结果 | 依赖 reward 与采样组，不直接给每个词的教师分布。 |
| 离线 SFT / 轨迹蒸馏 | 固定收集的教师回答 | 每个目标 token 的 cross-entropy（交叉熵） | 学生不必在每个训练步骤自己 rollout；不会自动覆盖学生独有的前缀。 |
| 多教师 OPD | 学生自己 rollout 到的前缀 | 教师在学生前缀上提供蒸馏信号；DeepSeek-V4 使用全词表分布与反向 KL | 信号是分布对齐，不是结果 reward 或固定答案 token。 |
| mixture of experts（MoE，混合专家）路由 | 同一次前向中，token 到达 MoE FFN 子层 | 路由器选择内部 expert 子网；DeepSeek-V4 报告初始若干 Transformer 层使用输入 token ID 哈希路由 | 这是模型架构；DeepSeek-V4 的 specialist teacher 是独立完整模型，并非 MoE 层里的 FFN 子网。 |

全词表 logits 的缓存成本也很大。V4 报告的实现按样本对应的教师索引组织数据，缓存该教师的末层 hidden state，再在训练时加载相应输出头重建词表分布；它避免为所有训练位置长期保存完整 logits，但仍需教师推理和输出头计算。

OPD 的多位教师是训练时的来源；学生要吸收其能力进自己的参数，推理时不需要继续调用这十多个教师，也不等于部署一个 teacher 路由器。报告给出按教师重要性设权重的 full-vocabulary（全词表）方案，但没有给出可迁移到任意任务的通用权重或样本调度规则。它应作为独立的蒸馏选择与 RLVR、离线 SFT 对照，不应称为所有训练任务的最佳方案。

## 当前训练器提供哪些可用控制？

训练库的默认值是一个实现版本的起点，不是适用于所有任务的推荐答案。版本固定后，应检查奖励如何合并、优势是否除组内标准差、每个回答怎样聚合 token 损失、策略概率比如何裁剪、KL 项是否加载参考模型，以及到达长度上限时哪些 token 会参与 loss。

截至 2026-11-12，Hugging Face TRL 的 `v1.17.1` 发布版在 `GRPOConfig` 中提供下列控制。TRL 的 GRPO 指南也展示了用 `GRPOTrainer`、prompt（提示）数据集和数学准确性奖励函数训练的可执行入门样例；要复现行为，应依赖版本 tag 的配置与代码，不要仅靠无版本的网页说明。

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
> - **GRPO、同题组优势与 PPO 对照。** Shao et al., *DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models*（arXiv:2402.03300v3，2024-04-27；§4.1.1–4.1.3〔采样 KL 估计见 Eq. 4〕、Appendix A.1.6），[v3 HTML](https://arxiv.org/html/2402.03300v3)。原始算法、结果/过程监督和 token 级目标。
> - **R1-Zero 奖励与完整 R1 流程。** DeepSeek-AI, *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning*（arXiv:2501.12948v2，2026-01-04；§2.1 Eq. 2（KL 估计）、§2.2–2.3、§3.1–3.2、Appendix B.3/B.4.2/B.5、F.1、G.2），[v2 HTML](https://arxiv.org/html/2501.12948v2)。支持准确性/格式奖励、奖励模型使用范围、训练阶段、reward hacking、过程奖励模型和蒸馏比较。
> - **DAPO。** Yu et al., *DAPO: An Open-Source LLM Reinforcement Learning System at Scale*（arXiv:2503.14476v2，2025-05-20；§3.1–3.4、§4），[v2 HTML](https://arxiv.org/html/2503.14476v2)。支持 Clip-Higher、动态筛组、token-level loss 和截断处理；结论限于该训练系统与实验。
> - **Dr.GRPO。** Liu et al., *Understanding R1-Zero-Like Training: A Critical Perspective*（arXiv:2503.20783v2，2025-10-06；§3.1–3.2），[v2 HTML](https://arxiv.org/html/2503.20783v2)。支持回答长度与题目难度加权分析及 Dr.GRPO 的固定预算分母方案。
> - **长度归一化的理论权衡。** Ding et al., *On the Impossibility of Unbiased and Length-Invariant Policy Optimization with Outcome Rewards*（arXiv:2607.23364v1，2026-07-25；§3、§4.1–4.4），[v1 HTML](https://arxiv.org/html/2607.23364v1)。在其 outcome-reward 设置和假设下，说明梯度无偏与轨迹长度不变贡献不能同时满足；这是理论预印本结论。
> - **GSPO。** Zheng et al., *Group Sequence Policy Optimization*（arXiv:2507.18071v2，2025-07-28；§4.1、§5.1、§5.3），[v2 HTML](https://arxiv.org/html/2507.18071v2)。支持几何平均序列概率比、序列级裁剪，以及 Qwen3-30B-A3B 冷启动实验中的 MoE expert 激活稳定性报告；结果限于论文设置。
> - **OPD 与 GRPO 的计算效率对照。** Liu et al., *Unpacking the Compute Efficiency of Strong-to-Weak OPD against GRPO*（arXiv:2611.08453v1，2026-11-05；§4–§6、Appendix E），[v1 HTML](https://arxiv.org/html/2611.08453v1)。比较外部 teacher 与 self-GRPO teacher 的 Qwen3 实验，并报告多域 specialist 合并的总 FLOPs；这是预印本证据，结果依赖其训练与评估设置。
> - **TRL 当前配置。** Hugging Face [TRL `v1.17.1` 发布记录](https://github.com/huggingface/trl/releases/tag/v1.17.1)（2026-10-30）、[该 tag 的 `grpo_config.py`](https://github.com/huggingface/trl/blob/v1.17.1/trl/trainer/grpo_config.py)和[当前 GRPOTrainer 文档](https://huggingface.co/docs/trl/grpo_trainer)，截至 2026-11-12 核对；发布记录页面上该版仍是最新发布版。版本配置支持 `beta=0`、`epsilon=0.2`、`loss_type="dapo"`、`scale_rewards="group"`、`mask_truncated_completions=False`；无版本文档可能晚于 tag 更新。
> - **verl 当前配置。** [verl `v0.9.1` 发布记录](https://github.com/verl-project/verl/releases/tag/v0.9.1)（2026-09-20）、[通用 PPO trainer 配置](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/config/ppo_trainer.yaml)、[actor 配置](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/config/actor/actor.yaml)、[GRPO 结果优势实现](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/ppo/core_algos.py)。配置说明默认优势估计是 GAE、组奖励标准差归一化打开、两种 KL 路径关闭，actor 聚合默认 `token-mean`；实际训练还须检查所用 recipe 的覆盖值。
> - **DeepSeek-V4 奖励与多教师 OPD。** DeepSeek-AI, *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*（arXiv:2606.19348v1；§2.1、§4.2.1、§5.1.1–5.1.2、§5.2.2），[v1 HTML](https://arxiv.org/html/2606.19348v1)。支持初始 MoE 层的 token ID hash 路由、specialist 阶段 SFT+GRPO、难验证任务的 rubric-guided GRM，以及 student 前缀上的多教师 reverse KL 与全词表 logits 蒸馏。V4-Pro 的[固定版本 Gate 实现](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/model.py#L546-L584)区分按 token ID 查表与按当前表示打分后选择 expert 的路径；具体层数由配置决定。论文描述的是 V4 特定流程；不将其教师权重、按任务分配或生成式评审设计推广为通用规则。
