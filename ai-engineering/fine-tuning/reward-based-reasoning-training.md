# 可验证奖励如何训练推理能力？

给模型一道可以复算的小题：“4 盒各装 3 个螺丝，另有 2 个散装螺丝，一共有多少个？”答案是 `4×3+2=14`。如果训练提示要求模型把推理过程放进 `<think>...</think>`、把答案放进 `<answer>...</answer>`，一段程序就能自动检查最终数值和标记格式，并据此给回答打分。本文前半部分跟踪模型对这道题的四条回答，走完一次 GRPO（一种用同题多条回答互相比较来更新模型的强化学习算法）更新；后半部分再对照 DeepSeek-R1 的真实训练阶段，比较其他训练信号，并说明训练器配置和独立验收。

若要判断这类训练是否适合稳定的行为差距，可先读[何时应微调来弥补稳定的行为差距？](fine-tuning-strategies.md)；要设计独立验收，再读[如何判断 AI 系统是否满足任务契约？](../evaluation/llm-evaluation-methods.md)。

## 检查器判的是什么，没判的又是什么？

reinforcement learning with verifiable rewards（RLVR，可验证奖励强化学习）要求 reward（奖励）来自能独立复核的目标，例如与参考答案比对、检查结构约束或运行程序测试。模型评委即使能输出分数，如果它只是在估计开放式质量，或估计回答是否符合参考答案，给出的仍是带误差的近似奖励；过程评审器也一样，不能因为“会打分”就算作可验证的结果。RLVR 只规定奖励从哪里来，不限定用哪种策略优化算法。本文沿着一个训练批次追踪整个过程：每道题采样一组回答 → 检查器打分 → 组内计算优势 → clipped policy objective（裁剪策略目标）→ 反向传播与优化器更新。

检查器必须针对明确的目标设计；不同类型的检查器能支持的结论强弱不同：

- **规则型 verifier（规则检查器/程序检查器）。** 数学任务可以解析最终答案并判断是否等价；代码任务可以编译并运行预先定义的测试；结构化输出可以检查 schema（结构模式）和必需字段。在规则覆盖范围内，结果可重复、成本也低。但编译成功或通过现有单元测试，只说明满足了这些检查，不证明程序对所有输入都正确；答案解析器也可能漏判等价写法，或放过错误答案。
- **学得的 verifier、评审模型或 reward model（奖励模型，RM）。** RM 可以用成对偏好数据训练，也可以让一个模型对照参考答案判断简短答案是否正确。它能评价难以写成规则的质量，但分数只是代理信号，会受评分准则（rubric）、评审偏差和训练数据影响。这类分数可以用来做基于学得奖励模型的强化学习，但只要评分本身无法独立复核，就不算可验证奖励。策略越擅长优化这个分数，越可能钻到评审器的漏洞。
- **process reward model（PRM，过程奖励模型）。** 它给每个推理步骤分别打分，比只看最终答案提供更多过程信号；但要先定义步骤边界、收集可靠的步骤标签，并检查评审器是否被策略利用。步骤怎样切分、标注质量如何，都可能成为新的误差来源。

任务格式也会影响检查器的可靠性。DAPO 的 DAPO-Math-17K 数据构造把数学题的参考答案统一成整数，并相应改写问题，以降低公式解析器引入的奖励误差。借鉴这类做法时，工程上还要一起核验改写后的题意、参考整数与解析规则，确保奖励仍然检查预期目标。答案容易解析只说明检查器有稳定输入，不证明题目改写保留了原任务。

“可验证”指检查目标能被独立执行或复核，不代表用 formal verification（形式化验证）证明了程序的全部行为。outcome reward（结果奖励）和 process reward（过程奖励）是另一个维度，区分的是“给整段结果打分”还是“给中间步骤打分”，与奖励是否可验证无关：程序可以判最终答案，带误差的模型评委也可以给整段回答打分；PRM 可以逐步打分，但它的标注和评审照样可能出错。如果结果检查器只看最终答案，它就没有逐步核对 chain-of-thought（CoT，思维链）；即使最终答案由程序精确判定，也不能据此认为轨迹中的每一步推理都正确。

看起来会自我纠错的轨迹也要按实际证据判断。DAPO §4.4 的几何题示例展示模型在推导中回看二面角并尝试用坐标重新分析，但输出在新思路展开前就截断了，不能据此确认它完成了纠错或得到了正确答案。

两种监督的差别还体现在信号落到哪些 token 上。结果监督在回答结束时打一个分，再把这条回答的组内优势（下一节定义）原样分给它生成的每个 token；过程监督在每个推理步骤末尾打分，不同步骤位置的 token 可以得到不同的优势。本文先走完结果奖励这条主线，再用一个单独的合成例子说明过程奖励的计分粒度。

## 同题采样怎样转成组内优势？

先说明符号。模型在强化学习里叫 policy（策略），记作 `π_θ`，`θ` 是参数。给定题目 `q`，用采样时那一刻的参数快照 `π_{θ_old}`（旧策略）独立生成 `G` 条 rollout（采样轨迹）`o₁,…,o_G`。每条回答由一串 token（词元）组成。采样时要保存题目、实际生成的前缀、每一步选中的 token，以及旧策略给这个 token 的概率；之后更新时，当前策略会在相同前缀上重新计算同一个 token 的概率（两者之比在下一节使用）。

检查器根据结果和格式给每条完整回答一个奖励 `r_i`。DeepSeek-R1-Zero 的规则奖励把答案准确性 `r_acc` 和格式 `r_format` 等权相加。下表用一个专为教学设计的检查器演算这两类信号，并不复刻 R1 的解析器：它能从带标记或不带标记的输出中提取末尾的数值，准确性和标记格式分开判分。四条回答如下：

| 回答 | 输出摘录 | 最终答案正确 | 标记格式正确 | `r_acc+r_format` |
| --- | --- | ---: | ---: | ---: |
| A | `15`，没有指定标记 | 0 | 0 | 0 |
| B | `14`，没有指定标记 | 1 | 0 | 1 |
| C | `<think>4×3=12；加2仍是12</think><answer>12</answer>` | 0 | 1 | 1 |
| D | `<think>4×3=12；12+2=14</think><answer>14</answer>` | 1 | 1 | 2 |

C 在中间把 `4×3+2` 算成了 `12`，最终答案 `12` 与正确答案 `14` 不符。准确性奖励只核对最终数值，格式奖励则单独核对标记，两项都没有逐步验证推理过程。由于两项等权相加，答案正确但格式错的 B 与答案错误但格式正确的 C 总分都是 `1`。训练和验收报告应分别呈现正确性、格式和合计奖励，避免把不同失败混为一类。

R1 论文 §2.2 中，数学准确性奖励检查的是放在指定格式里的最终答案；格式奖励则明确要求把推理放在 `<think>` 标记里。上表为了把两项信号分开演算，允许教学解析器从不带标记的输出中读出数值；不要把这条玩具解析规则当成 R1 的实现细节。

有了四个奖励，下一步是把它们变成“每条回答该被加强还是削弱”的信号。Group Relative Policy Optimization（GRPO，组相对策略优化）以同一道题所有回答的平均奖励作为 baseline（基线），并通常再除以这组奖励的标准差，得到每条回答的 advantage（优势）：

$$
\bar r=\frac{1}{G}\sum_{i=1}^{G}r_i,\qquad
\hat A_i=\frac{r_i-\bar r}{s_r},\qquad
\hat A_{i,t}=\hat A_i
$$

这里 `s_r` 是这 `G` 个奖励的 standard deviation（标准差），`t` 是回答中的 token 位置。在结果监督下，算法把同一个标量优势 $\hat A_i$ 分给这条回答中的每个生成 token；它告诉优化器“这条轨迹比同题其他轨迹好还是差”，但不告诉它“哪一行推理错了”。实现通常会在分母上加一个小常数 $\epsilon_{std}$（与后文的裁剪参数无关），避免 `s_r=0` 时除以零；但这不会让零方差的组产生新信号。

四条回答的奖励是 `[0,1,1,2]`，均值为 `(0+1+1+2)/4=1`。为方便手算，这里用总体标准差：

$$
s_r=\sqrt{\frac{(0-1)^2+(1-1)^2+(1-1)^2+(2-1)^2}{4}}
=\sqrt{0.5}\approx0.707.
$$

于是 A、B、C、D 的优势依次约为 `−1.414、0、0、+1.414`。D 比组内平均好，得到“提高这条轨迹概率”的信号；A 比平均差，得到“降低这条轨迹概率”的信号；B 和 C 恰好等于均值，在这次组内比较中没有优势信号。这个演算不复刻任何框架的标准差定义、奖励组合、掩码或 loss reduction（损失聚合），实际实现要按锁定的版本核对。

## 概率比、裁剪与 KL 怎样约束参数更新？

优势只说明方向。GRPO 沿用 PPO 的概率比和裁剪代理目标。概率比比较同一已采样 token 在当前策略与旧策略下的概率。沿着会继续增加单项代理收益的方向越过阈值时，裁剪会让该项进入平台。若启用 KL 项，它还会惩罚当前策略偏离参考策略。

以 D 最终答案中的 `14` 为例，教学中假定它恰好是一个 token，它前面的前缀 `o_{i,<t}` 已包含之前的推理和 `<answer>` 标记。设旧策略给这个 token 的概率是 `0.20`；经过若干次参数更新后，当前策略在同一题目、同一前缀上给同一个 token 的概率变成 `0.26`。（这是专门用来演示“超出裁剪上界”的假设状态；后面的单 logit 推导会另设当前概率为 `0.22`，两者互不相干。）两个概率之比叫 importance ratio（概率比）：

$$
\rho_{i,t}(\theta)=
\frac{\pi_\theta(o_{i,t}\mid q,o_{i,<t})}
{\pi_{\theta_{old}}(o_{i,t}\mid q,o_{i,<t})}
=\frac{0.26}{0.20}=1.30.
$$

proximal policy optimization（PPO，近端策略优化）的 clipped surrogate（裁剪代理目标）限制一次更新能从某个 token 的优势中拿到多少收益。设裁剪宽度 $\epsilon_{clip}=0.2$，裁剪区间就是 $[1-\epsilon_{clip},1+\epsilon_{clip}]=[0.8,1.2]$。D 的优势是 `+1.414`：未裁剪项为 `1.30×1.414≈1.838`，裁剪项为 `1.20×1.414≈1.697`，目标取两者中较小的 `1.697`。这个值不再随参数变化，所以该项对参数的梯度为零：这个 token 的正优势不会再推动它的概率继续上升。注意，实际的新旧概率比仍然是 `1.30`；裁剪只是让这一项进入“平台”，其他 token、共享参数上的梯度和 KL 项仍可能继续改变它的概率。

所以裁剪并不硬性限制实际的概率比，也不会把答案“裁”成正确或错误；它只改变 surrogate 中特定优势项的梯度。优势为负时，概率比低于下界也会出现对应的平台。裁剪范围太窄，可能削弱大量 token 的学习信号；太宽，又可能放任不稳定的大幅更新，需要在目标任务上验证。

KL 项用到的参考策略和采样时的旧策略作用不同。旧策略 $\pi_{\theta_{old}}$ 是生成这一批回答的分布，出现在概率比的分母上。参考策略 $\pi_{ref}$ 在一段使用同一参考快照的更新期间保持固定，用来限制策略漂移。训练配方可以每隔若干步刷新参考快照，例如 DeepSeek-R1 报告每 400 步刷新一次（见后文）。Kullback–Leibler divergence（KL 散度）衡量两个概率分布的差异。例如参考分布为 `[0.9,0.1]`、当前分布为 `[0.8,0.2]` 时，以当前分布的概率为权重求和，得到

$$
D_{KL}([0.8,0.2]\Vert[0.9,0.1])
=0.8\ln\frac{0.8}{0.9}+0.2\ln\frac{0.2}{0.1}\approx0.044403\text{ nats}.
$$

`nats` 是用自然对数计算时的单位。这个例子只有两种可能的 token，可以逐一枚举，所以算出的是精确的 KL。真实词表很大，实际的 RL 目标对题目和旧策略 rollout 求期望，GRPO 用已采样的回答或 token 上的概率来估计 KL：DeepSeekMath 给出了这种采样估计，R1 也把采样回答上的 KL 项写进了目标。因此，不要以为所有 GRPO 实现都会对每个上下文精确遍历整个词表。KL 项在目标中乘以系数 `β`：`β=0` 时 KL 项关闭；`β` 非零时，模型受到贴近参考策略的约束，同时需要额外计算参考模型的概率。

现在各部分都有了对应的量：组内奖励决定优势，概率比比较新旧策略，裁剪限制 surrogate，KL 项约束相对参考策略的漂移。设题目 $q\sim\mathcal{D}$，并在给定 $q$ 后从旧策略快照独立采样回答 $o_1,\ldots,o_G$；记 $\mathbb{E}_{q,o_{1:G}}$ 为对这些题目和回答组求平均。可以分两步写出一个常见的 token 级 GRPO 最大化目标：先把位置 $(i,t)$ 的收益记为 $g_{i,t}$，再聚合整批数据。

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

这里 $\mathcal{D}$ 是题目分布；给定 $q$ 后，每条 $o_i$ 都从旧策略 $\pi_{\theta_{old}}(\cdot\mid q)$ 独立采样。$o_i$ 是组内第 $i$ 条 token 序列，$|o_i|$ 是其中参与目标计算的 token 数，$t$ 是 token 位置。式内显式对 token 和回答求和，外层期望再对题目和回答组取平均。训练要最大化 $\mathcal{J}$；如果训练器定义的是要最小化的损失，就最小化 $-\mathcal{J}$。这个教学目标先在每条回答内部对 token 项取长度平均，再对组内回答取平均；这只是一种便于讲解的 reduction。论文写法和各框架的目标并不完全相同：DeepSeekMath 的 GRPO 公式写逐 token 概率比并按每条回答长度取均值；DeepSeek-R1 正文把策略比写成整条输出的概率比；TRL 和 verl 又提供不同的损失聚合、奖励标准化与 KL 配置。公式相同处说明策略更新机制，具体归约和超参数仍须按所用实现核对。

下式采用 DeepSeekMath 的 token 级 sampled KL（采样 KL）写法：

$$
\begin{aligned}
\delta_{i,t}&=\log\pi_{ref}(o_{i,t}\mid q,o_{i,<t})
-\log\pi_{\theta}(o_{i,t}\mid q,o_{i,<t}),\\[6pt]
\widehat D_{i,t}&=\exp(\delta_{i,t})-\delta_{i,t}-1.
\end{aligned}
$$

DeepSeek-R1 正文 Eq. 2 对整条采样回答 $o_i$ 的概率比使用相同的标量变换。这与此处按 token、同一前缀计算的粒度不同。只有当 token 按当前策略 $\pi_{\theta}$ 采样时，$\exp(\delta)-\delta-1$ 的期望才对应完整的 $D_{KL}(\pi_{\theta}\Vert\pi_{ref})$。实际训练批次通常从旧策略采样，之后当前策略还会随更新移动，因此这批样本上的估计不能直接当作当前策略对整个词表计算出的 KL。

### 一个回答的优势怎样改变模型参数？

目标函数写好后，剩下的问题是它怎样变成参数更新。检查器给出的 reward 和组内 advantage 在这一步都是固定数值；梯度不会穿过答案解析器，策略也不是通过对检查器求导来更新的。对一个已采样 token，记 $p_\theta=\pi_\theta(o_{i,t}\mid q,o_{i,<t})$、$p_{old}=\pi_{\theta_{old}}(o_{i,t}\mid q,o_{i,<t})$。在裁剪未进入平台且不计 KL 时，将该 token 的单项目标记为 $\mathcal{J}_{i,t}=\rho_{i,t}\hat A_i$；其梯度为

$$
\nabla_\theta\mathcal{J}_{i,t}
=\frac{\hat A_i}{\pi_{\theta_{old}}(o_{i,t}\mid q,o_{i,<t})}
\nabla_\theta\pi_\theta(o_{i,t}\mid q,o_{i,<t})
=\rho_{i,t}\hat A_i\nabla_\theta\log\pi_\theta(o_{i,t}\mid q,o_{i,<t}).
$$

中间一步将概率比 $\rho=p_\theta/p_{old}$ 展开，最后一步使用 $\nabla\log p=(\nabla p)/p$；这里旧概率 $p_{old}$ 与组内优势 $\hat A_i$ 对 $\theta$ 固定。

接着用一个只有一个 logit 的教学例子，把梯度一直算到参数。假设这个 token 的当前概率是 $p_\theta=0.22$、旧策略概率是 $p_{old}=0.20$，组内优势为 $\hat A_i=1.414$（与前面 $0.26$ 的越界例子无关）。把目标 token 的 logit 设为参数 $\theta$，唯一竞争 token 的 logit 固定为 $0$，二元 softmax 就是

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

以学习率 $\eta=0.01$ 做 SGD 梯度上升：$\theta'=\theta+\eta\,\partial\mathcal{J}_{i,t}/\partial\theta\approx-1.253534$。再代回二元 softmax，$p'_\theta=\sigma(\theta')=e^{\theta'}/(e^{\theta'}+1)\approx0.222089$，即目标 token 的概率从 $0.220000$ 升到约 $0.222089$。这是一个忽略了其他 token、KL、梯度裁剪和优化器状态的一维示意。

真实模型中，本批每个有效 token 的优势项都对同一组共享参数求梯度，梯度沿共享计算图汇总后，由所选优化器更新启用训练的参数。一条序列的 log 概率等于各个条件 token 的 log 概率之和，所以 token 级的梯度合起来就是轨迹级的更新信号。更新后的参数成为下一批采样的旧策略，循环重新开始：采样时缓存旧策略对已选 token 的概率，更新时由当前策略在相同前缀上重算。若把目标写成要最小化的 loss，则用 $L=-\mathcal{J}$。完整矩阵反向传播和 AdamW/Muon 怎样把梯度变成参数值，见[训练梯度与优化器](../foundations/training-gradients-and-optimizers.md#AdamW%20%E5%92%8C%20Muon%20%E6%80%8E%E6%A0%B7%E4%BD%BF%E7%94%A8%E5%B7%B2%E7%BB%8F%E7%AE%97%E5%A5%BD%E7%9A%84%E6%A2%AF%E5%BA%A6)。

> [!info] 为什么结果分数会影响整条序列？
> 一条回答的概率是各个条件 token 概率相乘，取对数后连乘变成相加：`log π(o_i|q) = Σ_t log π(o_{i,t}|q,o_{i,<t})`。若暂时固定其他位置的条件概率，`14` 这一处从 `0.22` 升到约 `0.222089`，整条 D 的概率就乘上约 `0.222089/0.22 = 1.0095`。真实模型会通过共享参数同时改变多个位置，不能直接把这个倍率当成训练结果。终局奖励经这条计算链提供轨迹级更新信号，没有给每一步单独贴上正确或错误标签。

### GRPO 为什么不需要 critic（价值网络）？

PPO 通常要训练一个 critic（价值函数/价值网络）来估计状态价值，再用它计算优势；对大语言模型来说，这意味着额外的一个大模型和相应的显存。GRPO 不拟合价值网络，而是用同一道题多条回答的平均奖励作基线，并可以按组内标准差归一化。它省掉了 critic，却要为每道题生成多个回答、多次运行检查器；也就是说，省下的模型显存换成了更多的 rollout 和判分开销。若检查器昂贵，或生成回答很长，这部分成本可能成为瓶颈。

## 如果逐步评分，优势会怎样变化？

前面的主线只用了结果奖励。现在看第一节提到的另一种记分方式。DeepSeekMath 的 process supervision（过程监督）在每个推理步骤的末尾给分。论文把同一道题的整组回答中、所有步骤末尾的奖励放进同一个集合一起标准化。设 $index_i(j)$ 是回答 $i$ 中第 $j$ 步结束 token 的位置，$\tilde r_i^{index_i(j)}$ 是回答 $i$ 在该步骤末端的标准化奖励。每个 token 从所在步骤开始，累加该步及后续各步结束时的标准化奖励：

$$
\hat A_{i,t}^{process}=\sum_{j:\,index_i(j)\ge t}\tilde r_i^{index_i(j)}.
$$

用一组可复算的合成例子说明：四条回答各有两个推理步骤，每步原始得分为 0 或 2（见下表第二列）。先把每条回答的**原始步骤分之和**当作 outcome reward，得到 `[0,2,2,4]`；均值为 `2`，总体标准差为 `√2≈1.414`。结果监督用这四个总分计算优势。

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

GRPO 的优势来自组内比较，所以组内没有差异时就没有信号。如果同一道题的所有回答奖励都相同，例如 `[1,1,1,1]` 或 `[0,0,0,0]`，每个 $r_i - \bar r$ 都等于 0，优势全为零。给标准差分母加 $\epsilon_{std}$ 能避免除以零，但改变不了分子为零的事实，这组回答在 clipped surrogate 上的梯度仍为零。如果总目标里还有 KL、熵奖励或辅助损失，这些项仍可能提供梯度。

如果只按答对/答错给二元奖励，奖励全相同就意味着所有采样都答对或都答错，常见于太简单或当前策略还完全做不出来的题。如果还给格式等其他分量打分，准确性相同不一定意味着总奖励相同。Decoupled Clip and Dynamic Sampling Policy Optimization（DAPO，解耦裁剪与动态采样策略优化）提出的 dynamic sampling（动态筛组）在它的二元准确率设置中持续采样，丢掉全对和全错的组，只保留既有正确也有错误回答的组；这样零优势组就不会白白占用 batch，但进入更新的题目分布也随之改变。若任务还依赖格式、长度或偏好等奖励，以准确率作为筛组条件可能丢弃这些分量仍有差异的组，因此要检查筛选指标与奖励目标是否一致。

## 为什么回答长度和截断会改写训练权重？

前面的目标函数中，token 项怎样聚合（reduction）看似是实现细节，实际上决定了长回答和短回答各占多大权重。DeepSeekMath 的 GRPO 目标先在每条回答内对 token 项取平均，再对回答取平均：$\frac{1}{G}\sum_i\frac{1}{|o_i|}\sum_t \ell_{i,t}$，其中 $\ell_{i,t}$ 是位置 $(i,t)$ 上的单项目标。因此，长度为 20 和 200 的回答中，单个 token 的显式系数分别是 $1/(20G)$ 和 $1/(200G)$，去掉公共因子 $1/G$ 后就是 $1/20$ 和 $1/200$。不过整条轨迹的梯度还取决于各 token 的概率梯度和优势，不能只凭这个系数断言模型一定偏好短回答或长回答。DAPO 论文把长 CoT 中长回答的 token 信号容易被样本级平均稀释列为改动动机；Dr.GRPO 则分析样本长度和组内标准差归一化造成的样本权重变化。

后续改法针对的偏差不同，应按自己的目标与 token 分布比较：

- **DAPO** 把整个 batch 的有效 token 合在一起取平均，长回答因而贡献更多 token 项；它还把上、下裁剪幅度分开设置（Clip-Higher），给低概率的探索 token 更大的上调空间，并在二元准确率设置中动态筛组。论文的 Qwen2.5-32B 配方取 $\epsilon_{low}=0.2$、$\epsilon_{high}=0.28$，并给出 16,384-token 期望长度与额外 4,096-token 软惩罚区间。这些选择服务于论文的长 CoT 配方，不是通用推荐。
- **Dr.GRPO** 在 R1-Zero-like 训练研究中去掉每条回答的长度平均和组内奖励标准差缩放，用固定生成预算作分母。它改变了样本和 token 的梯度权重；论文论证与实验限于其设置。2026 年一篇理论预印本进一步指出，在其 outcome-reward 假设下，长度加权不可能同时保证梯度估计无偏、又让每条轨迹的有效贡献与长度无关。因此不要把“Done Right”读成对所有任务都消除长度偏差的结论。
- **GSPO** 把重要性比定义在整条序列的几何平均概率上并做序列级裁剪。Qwen 团队报告它缓解其 Qwen3 MoE 训练中的 expert 激活波动；这是一种后续公开方案和特定实验结果，不是 DeepSeek-R1 的算法，也不表示所有 MoE 模型都必须改用 GSPO。

长度还会以另一种方式影响训练：生成长度有硬上限，超出就会被截断。如果检查器把因截断而没写完的答案直接判错，优化器可能把“没机会写出结论”当成推理错误来惩罚。DAPO 论文先试验了屏蔽截断样本的损失，再在接近上限的长度区间加入逐渐加重的 soft overlong punishment（软超长惩罚）；其最终配置和各框架的实现要分别核对。如果任务确实要求简洁，长度成本也可以写进目标，但应基于可验证的需求来定义。至少要按正确/错误、长度和终止原因统计截断率与奖励，以免把长度偏好误当成质量提升。

## DeepSeek-R1-Zero 与最终 R1 有什么不同？

前面的机制都可以对应到 DeepSeek-R1 的真实训练流程。DeepSeek-R1 没有发明强化学习或 GRPO：GRPO 由 DeepSeekMath 于 2024 年提出，R1 把它用于大规模 reasoning post-training（推理后训练）。R1-Zero 展示的是一个特定的训练结果：在 DeepSeek-V3-Base 上不先做 supervised fine-tuning（SFT，监督微调），直接用规则型的准确性和格式奖励训练策略。论文观察到回答变长，并出现反思和探索行为；这些是该实验中的行为变化，既不说明每条推理链都经过验证，也不说明模型获得了类似人的自我意识。

R1-Zero 和 R1 是从同一底座出发的两条不同训练线，不能把 Zero 的“无预先 SFT”当成最终 R1 的完整配方。R1 的阶段边界和各阶段数据流见下表；后文再解释为什么奖励类型会随阶段变化。

| 训练线或阶段 | 数据与更新 | 该阶段的奖励/目标 |
| --- | --- | --- |
| R1-Zero | DeepSeek-V3-Base 直接进入 RL | 数学、代码、逻辑任务使用规则准确性与格式奖励做 GRPO，不先做 SFT。 |
| R1 冷启动与第一阶段 RL | 数千条冷启动推理示范先做 SFT，再进行推理 RL | 规则奖励；另加语言一致性奖励，缓解多语言混杂。 |
| R1 拒绝采样与第二次 SFT | 第一阶段 checkpoint 生成候选，筛出约 600K 推理样例并加入约 200K 通用样例；再从 Base 权重开始第二次 SFT | 这里传给 SFT 的是筛选数据，不是第一阶段 RL checkpoint 的参数。 |
| R1 第二阶段 RL | 从第二次 SFT 的权重继续训练 | 推理题使用规则奖励；通用帮助性与安全性任务使用模型奖励。 |

具体来说，第一阶段先收集数千条更易读、对话式的冷启动推理样本做 SFT，再用规则奖励继续强化推理，并加入语言一致性奖励，减少中英混杂。rejection sampling（拒绝采样）阶段用第一阶段 RL 得到的 checkpoint（检查点）为每道题生成多个回答，只保留正确的轨迹；部分难以写成规则的样本由 DeepSeek-V3 对照参考答案辅助判断，再过滤掉混杂语言、段落过长或含代码块等难读的样例，得到约 600K 条推理样本。再加入约 200K 条非推理样本，从 DeepSeek-V3-Base 权重重新做第二次 SFT。也就是说，第一阶段 RL 传给下一步的是筛选后的数据，第二次 SFT 并不沿用那个 RL checkpoint 的权重。

论文分别报告了两条训练线的配置：R1-Zero 每题采样 16 条、`β=0.001`、每 400 步刷新参考模型；最大回答长度在第 8.2K 步之前为 32,768 token，之后增至 65,536。最终 R1 第一阶段推理 RL 也报告每题 16 条、`β=0.001`、每 400 步刷新参考模型，最大长度 32,768 token，并设 GRPO clip ratio $\epsilon_{clip}=10$。这些是论文的阶段配置，尤其 `10` 不是通用 clip 默认值。

第二阶段 RL 对推理题仍用规则奖励；对通用的帮助性和安全性问题则用模型奖励：帮助性主要评估最终的总结部分，安全性则检查整条回答。模型奖励只用在通用偏好任务上，不代表 R1-Zero 的推理训练用神经奖励模型逐步判对错。R1 作者还报告了一个 reward hacking（奖励投机）的例子：帮助性奖励模型的分数在上升，Codeforces 上的表现却在下降。作者没有在大规模推理 RL 中使用神经过程奖励模型，理由包括推理步骤难以定义、步骤标注难以扩展、奖励模型本身可能被策略利用；但他们认为这类模型仍可用于重排候选或引导搜索。

较新的 DeepSeek-V4 技术报告又描述了 rubric-guided generative reward model（GRM，生成式奖励模型）：对难以用规则验证的任务，由一个生成式评审器按评分准则评估轨迹，而且这个评审器就是正在接受 RL 训练的 actor 本身。报告把它与传统的标量奖励模型区分开。它提供的是受准则约束的学习型评审信号，并不因此变成可验证奖励；这是 V4 报告里针对该模型的设计，不是对 R1-Zero 配方的追溯修改。

## 哪种训练信号符合手头目标？

R1 的流程把 SFT、RLVR 和模型奖励组合起来使用。这说明训练信号要按目标和手头的数据来选，下表做了归纳：

| 目标与可用数据 | 适合先试什么 | 主要代价与边界 |
| --- | --- | --- |
| 已知期望输出，能写出稳定示范 | SFT | 训练信号来自示范实际表达的行为；未见输入上的泛化需要独立验证。 |
| 有可靠的程序化结果检查，希望模型通过尝试发现更好的解题轨迹 | 在线 RLVR，例如 GRPO | 需要多次采样、稳定可复现的检查器、足够算力和独立验收；奖励只覆盖检查器所定义的目标。 |
| 有更强教师模型生成并筛选过的轨迹，希望小模型学会这些解法 | offline distillation（离线蒸馏）或 rejection-sampling SFT（拒绝采样后的 SFT） | 学生从固定轨迹模仿，不需要每轮再按学生当前策略 rollout；效果受教师质量、样例覆盖和筛选器限制。 |
| 有成对偏好标签，目标偏主观且不易精确程序化 | direct preference optimization（DPO，直接偏好优化）或其他偏好优化 | 学到的是标注偏好与训练目标，不是外部事实真值，也不是结果正确性的证明。 |

R1 的蒸馏属于离线监督：教师（R1）先生成推理回答，筛选后的固定回答用来对小模型做 SFT，学生训练时不会每轮自己采样、再按 verifier 的打分更新。论文 Appendix F 做了一个范围有限的比较：对 Qwen2.5-32B-Base 直接做超过 10K 步 RL 得到 Qwen2.5-32B-Zero，它在 AIME 2024 上的 pass@1（单次采样通过率）为 47.0%；用 R1 轨迹蒸馏得到的 DeepSeek-R1-Distill-Qwen-32B 为 72.6%。这说明在该基线、数据和评估协议下，强教师的轨迹非常有效，但不能推出蒸馏总是胜过 RL。R1 自身也是把 SFT 与 RL 组合使用的。

## 多教师在策略蒸馏又提供了什么训练信号？

上表的两种主要信号各有局限：离线 SFT 把固定的教师回答当作目标 token，学生只见过教师走过的前缀；在线 RLVR 让学生自己采样，但每条轨迹只得到一个标量 reward 换算的优势。on-policy distillation（OPD，在策略蒸馏）结合了两者：训练轨迹由学生用自己当前的策略生成，教师在这些学生前缀上提供蒸馏信号。具体用什么信号由实现决定。DeepSeek-V4 报告用完整词表的 logits 计算 reverse KL（反向 KL）；但全词表目标是该报告的实现选择，不是 OPD 的必要条件，报告也把它与既有工作中只用采样 token 估计 KL 的做法做了比较。

DeepSeek-V4 论文 v1 报告了一种多教师 OPD 流程。先为数学、代码等领域分别训练 specialist teacher（领域教师模型）：每个教师都是独立的完整模型，先用该领域数据做 SFT，再用该领域的 prompt 和奖励信号通过 GRPO 做强化学习。之后，一个统一的 student（学生模型）用自己的策略采样轨迹，并按任务向相应教师的完整输出分布学习。这个 OPD 阶段共用了十多位教师，但报告并不要求每个前缀都运行全部教师。论文用 OPD 取代的是“把多领域数据混合在一起做 RL”（mixed RL）的统一训练阶段；specialist 自身的 SFT 和 RL 并没有省掉。

以一道数学题为例，把训练和部署连起来看：

1. **按任务配教师。** 训练样本属于数学任务，因此使用完整的数学领域教师。选择发生在训练任务/样本尺度；这里的 teacher 是一套完整模型权重，不是某层 FFN 里的一个 expert 子网。
2. **由学生生成前缀。** student 接收题目提示词，从自己的策略 rollout（采样轨迹），走到一个前缀。
3. **教师在同一前缀上给分布。** 数学教师接收该 student prefix，对整个词表输出下一词元 logits；按 student 到 teacher 的 reverse KL 计算蒸馏目标，并用它更新统一 student 的参数。
4. **部署学生。** 线上运行已训练的 student，不需要继续调用领域教师。若 student 的架构含有 MoE，模型内部仍可在每个 token 到达 MoE FFN 子层时路由到若干 expert 子网。DeepSeek-V4 报告其初始若干 Transformer 层使用按输入 token ID 哈希的路由；这是模型前向中的 token 级 FFN 路由，不是按任务切换完整教师。

因此，教师选择决定“这条训练样本向哪一个完整领域模型学习”，MoE 路由决定“当前前向中的这个 token 经过哪些内部 FFN 子网”。二者粒度和对象都不同。

OPD 是否一定比直接做 GRPO 划算？2026 年 11 月 5 日的一篇预印本在 Qwen3 模型上比较了 reverse-KL OPD 与 GRPO。单域情形下：用外部已后训练的模型当 teacher 时，在相同 FLOP 预算下 OPD 的准确率通常更低，部分设置还出现回答变长；如果 teacher 就是学生自己经 GRPO 训练得到的 checkpoint，OPD 能用较少的蒸馏计算恢复该 checkpoint 的单域能力。多域情形的目标不同，是把各领域的 GRPO specialist 合并成一个 student：在数学与代码两域实验中，要达到与 joint GRPO（各领域样本混合训练）相同的准确率，把 specialist 训练和蒸馏都算进去，总 FLOPs 少 42%。这些结果限于该预印本的模型、数据、训练与评估设置。OPD 是否合适，要根据 teacher 与 student 的差距、部署目标和总计算成本来验收。

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

OPD 的多位教师只在训练时使用；学生把它们的能力吸收进自己的参数，推理时不需要再调用这十多个教师，也不需要部署一个在教师之间切换的路由器。报告给出了按教师重要性设权重的全词表方案，但没有给出可迁移到任意任务的通用权重或样本调度规则。应把它当作一种独立的蒸馏选项，与 RLVR、离线 SFT 对照比较，而不是所有训练任务的最佳方案。

## 当前训练器提供哪些可用控制？

前面讨论的组大小、标准差缩放、裁剪、KL、token 聚合和截断处理，在训练库里都对应具体的配置项。训练库的默认值只是某个实现版本的起点，不是适用于所有任务的推荐值。锁定版本后，应检查：奖励怎样合并、优势是否除以组内标准差、每条回答的 token 损失怎样聚合、概率比怎样裁剪、是否加载参考模型计算 KL，以及达到长度上限时哪些 token 参与 loss。

截至 2026-11-25，Hugging Face TRL 最新发布版是 `v1.18.2`（2026-11-19）。该 tag 的 `GRPOConfig` 默认值如下。标准 `GRPOTrainer` 中，`loss_type="dapo"` 采用全局 token 聚合；筛组、裁剪和长度处理仍需按实际 trainer 与 recipe 核对。TRL 的 GRPO 指南提供了用 `GRPOTrainer`、prompt（提示）数据集和数学准确性奖励函数训练的入门样例。要复现行为，应以版本 tag 下的配置和代码为准。

| TRL `v1.18.2` 参数 | 发布版默认值 | 应按任务检查什么 |
| --- | --- | --- |
| `beta` | `0.0` | 默认不加载参考模型、不加 KL 项。若要限制偏离参考策略，显式设非零值并记录内存与质量代价。 |
| `epsilon` | `0.2` | PPO-style ratio clip 的基础幅度；低概率探索 token 是否能获得足够上调空间要单独观察。 |
| `loss_type` | `"dapo"` | 在标准 `GRPOTrainer` 中选择全局有效 token 聚合。还提供 `"grpo"` 与 `"dr_grpo"` 等选项，reduction 会改变长短回答的权重。 |
| `scale_rewards` | `"group"` | 默认按组标准差缩放奖励。Dr.GRPO 风格配置还要考虑关闭这项缩放；只改 loss reduction 不等于复现论文算法。 |
| `mask_truncated_completions` | `False` | 默认仍将截断回答纳入损失。若任务不能公平评分未完成答案，可显式启用 mask，并监控丢弃比例和长度分布。 |

`AsyncGRPOTrainer` 另有 rollout 筛组逻辑：它会丢弃已评分的合计奖励全相同的组。这是该 trainer 独立实现的奖励筛选，不等同于 DAPO 论文的持续重采样机制，也不由 `loss_type` 这一设置单独决定。

`epsilon_high` 可以设置与下界不同的上裁剪幅度，未设置时沿用 `epsilon`；DAPO 在其特定实验中用 `0.28`，这不是 TRL 的通用默认值（`v1.18.2` 只在 `loss_type="cispo"` 时把未设置的 `epsilon_high` 默认为 `5.0`）。所用版本的这些字段应连同模型、奖励函数、数据划分、生成长度上限、随机种子和有效 batch 一起记入实验配置。

截至 2026-11-25，verl 最新发布版仍为 `v0.9.1`（2026-09-20）。它能运行 GRPO，但通用 `ppo_trainer.yaml` 默认 `algorithm.adv_estimator=gae`，即 generalized advantage estimation（GAE，广义优势估计），不是 GRPO；要跑 GRPO，需显式设为 `grpo`。同一 tag 中 `algorithm.norm_adv_by_std_in_grpo=true`，而 `algorithm.use_kl_in_reward=false`、`actor.use_kl_loss=false`，即把 KL 加进奖励和把 KL 作为单独损失项这两条路径默认都关闭；actor 的 `loss_agg_mode` 默认是 `token-mean`。`filter_groups.enable` 默认关闭，采用 DAPO 式筛组时要显式开启，并检查用来筛组的指标。基础 PPO 配置不等于 DAPO 论文的完整设置，要分别核对优势估计、奖励标准化、loss reduction 和两条 KL 路径。

固定版本的 verl DAPO recipe 提供线性增加的 Overlong Reward Shaping，并说明多数实验（包括表现最佳的实验）没有启用 Overlong Filtering，因为作者认为它与软超长奖励的作用有重叠。这是该 recipe 对实验实现的说明，不应外推为 DAPO 论文每次运行都采用同一组合。

TRL `v1.18.2` 和 verl `v0.9.1` 是截至 2026-11-25 核对过的发布版；新版本可能改变默认值或实现。一个可复现的训练说明至少应记录库的 tag/commit、模型 checkpoint、reward 函数与聚合权重、`G`、优势标准化和 `epsilon`、clip、loss reduction、KL 两项设置、完成长度及截断 mask。实验命令显示 `GRPO` 不能替代对这些配置的记录。

## 怎样独立验收训练结果？

训练样本上的 reward 上升，只说明策略更会满足优化目标，不能据此证明它能泛化。把同一套可靠的评分规则用在没有参与训练、调参或筛选的新题上，仍然是衡量该结果指标的有效方式。如果 reward 只检查数学答案，最终验收还应覆盖解析边界、等价答案、推理错误但答案碰巧正确、格式问题和没见过的题型；代码任务则要检查隐藏测试、边界输入、sandbox 隔离和副作用。通过现有 verifier 只说明通过了这组检查，还要审查 verifier 本身的覆盖范围和漏洞；单个分数也不能证明整体质量或安全性。

在确定方案之前，就要留出不参与训练、调参或筛选的独立任务集和隐藏测试。用相同的提示词、推理设置和采样预算比较训练前后的 checkpoint，按任务难度、回答长度、终止原因和失败类型分别报告分母和成功率，同时查看格式、重复、拒答、安全、时延和成本。如果目标包含帮助性、风格或开放式质量，应在训练用的偏好数据之外，使用盲评的人工样例或经过校准的评审器；评审模型的分数不能代替事实检查。如果发现候选靠格式、措辞或可预测的漏洞拿到高训练分，任务质量却下降，应先修复奖励或检查器，再在没有参与优化的验收集上重新测试。

正式训练前，先用小规模实验比较组大小、奖励组合、标准差缩放、clip、KL、loss reduction 和截断处理，确定后固定下来并记录选择理由。DAPO、Dr.GRPO 或原始 GRPO 的效果取决于任务奖励是否可信、回答长度分布、题目难度及实现细节，没有一个只凭算法名称就能得出的跨任务最佳配置。

> [!info]- 来源
> 下列来源映射到正文中的机制与实验。数值推演是教学合成值；训练器参数来自标明版本的官方文档或代码。
>
> - **GRPO、同题组优势与 PPO 对照。** Shao et al., *DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models*（arXiv:2402.03300v3，2024-04-27；§4.1.1–4.1.3〔采样 KL 估计见 Eq. 4〕、Appendix A.1.6），[v3 HTML](https://arxiv.org/html/2402.03300v3)。原始算法、结果/过程监督和 token 级目标。
> - **R1-Zero 奖励与完整 R1 流程。** DeepSeek-AI, *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning*（arXiv:2501.12948v2，2026-01-04；§2.1 Eq. 2（KL 估计）、§2.2–2.3、§3.1–3.2、Appendix B.3/B.4.2/B.5、F.1、G.2），[v2 HTML](https://arxiv.org/html/2501.12948v2)。支持准确性/格式奖励、奖励模型使用范围、训练阶段、reward hacking、过程奖励模型和蒸馏比较。
> - **DAPO。** Yu et al., *DAPO: An Open-Source LLM Reinforcement Learning System at Scale*（arXiv:2503.14476v2，2025-05-20；§§3.1–3.4 的算法改动、§3.5 的数据转换、§4.1 的训练设置与 §4.4 的案例轨迹），[v2 HTML](https://arxiv.org/html/2503.14476v2)。支持 Clip-Higher、动态筛组、token-level loss、超长奖励处理和答案格式转换；案例输出被截断，不能证明已成功纠错。结论限于该训练系统与实验。
> - **Dr.GRPO。** Liu et al., *Understanding R1-Zero-Like Training: A Critical Perspective*（arXiv:2503.20783v2，2025-10-06；§3.1–3.2），[v2 HTML](https://arxiv.org/html/2503.20783v2)。支持回答长度与题目难度加权分析及 Dr.GRPO 的固定预算分母方案。
> - **长度归一化的理论权衡。** Ding et al., *On the Impossibility of Unbiased and Length-Invariant Policy Optimization with Outcome Rewards*（arXiv:2607.23364v1，2026-07-25；§3、§4.1–4.4），[v1 HTML](https://arxiv.org/html/2607.23364v1)。在其 outcome-reward 设置和假设下，说明梯度无偏与轨迹长度不变贡献不能同时满足；这是理论预印本结论。
> - **GSPO。** Zheng et al., *Group Sequence Policy Optimization*（arXiv:2507.18071v2，2025-07-28；§4.1、§5.1、§5.3），[v2 HTML](https://arxiv.org/html/2507.18071v2)。支持几何平均序列概率比、序列级裁剪，以及 Qwen3-30B-A3B 冷启动实验中的 MoE expert 激活稳定性报告；结果限于论文设置。
> - **OPD 与 GRPO 的计算效率对照。** Liu et al., *Unpacking the Compute Efficiency of Strong-to-Weak OPD against GRPO*（arXiv:2611.08453v1，2026-11-05；§4–§6、Appendix E），[v1 HTML](https://arxiv.org/html/2611.08453v1)。比较外部 teacher 与 self-GRPO teacher 的 Qwen3 实验，并报告多域 specialist 合并的总 FLOPs；这是预印本证据，结果依赖其训练与评估设置。
> - **TRL 当前配置。** Hugging Face [TRL `v1.18.2` 发布记录](https://github.com/huggingface/trl/releases/tag/v1.18.2)（2026-11-19，截至 2026-11-25 为最新发布版）及其 [`grpo_config.py`](https://github.com/huggingface/trl/blob/v1.18.2/trl/trainer/grpo_config.py)、[`grpo_trainer.py`](https://github.com/huggingface/trl/blob/v1.18.2/trl/trainer/grpo_trainer.py#L3344-L3357) 和 [`async_grpo_trainer.py`](https://github.com/huggingface/trl/blob/v1.18.2/trl/trainer/async_grpo_trainer.py#L1812-L1850)。`GRPOConfig` 默认 `beta=0`、`epsilon=0.2`、`epsilon_high=None`（除 `loss_type="cispo"` 时改为 `5.0`）、`loss_type="dapo"`、`scale_rewards="group"`、`mask_truncated_completions=False`；标准 `GRPOTrainer` 的 DAPO loss 分支使用全局 token 归约，`AsyncGRPOTrainer` 另行丢弃已评分合计奖励全相同的组。配置于 2026-11-25 核对。
> - **verl 当前配置。** [verl `v0.9.1` 发布记录](https://github.com/verl-project/verl/releases/tag/v0.9.1)（2026-09-20）、[通用 PPO trainer 配置](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/config/ppo_trainer.yaml)、[actor 配置](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/config/actor/actor.yaml)、[GRPO 结果优势实现](https://github.com/verl-project/verl/blob/v0.9.1/verl/trainer/ppo/core_algos.py)。配置说明默认优势估计是 GAE、组奖励标准差归一化打开、两种 KL 路径关闭，actor 聚合默认 `token-mean`；实际训练还须检查所用 recipe 的覆盖值。
> - **verl DAPO recipe 的超长处理。** verl-project [`verl-recipe` 固定 commit `b27e321`](https://github.com/verl-project/verl-recipe/blob/b27e321a57427a23159c167ca12a7ea381a2453d/dapo/README.md#L146-L180)（§“Overlong Reward Shaping”和 FAQ）展示线性软惩罚，并说明大多数实验（包括表现最佳的一项）没有启用 Overlong Filtering。该说明只适用于此 recipe 与其记录的实验。
> - **DeepSeek-V4 奖励与多教师 OPD。** DeepSeek-AI, *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*（arXiv:2606.19348v1；§2.1、§4.2.1、§5.1.1–5.1.2、§5.2.2），[v1 HTML](https://arxiv.org/html/2606.19348v1)。支持初始 MoE 层的 token ID hash 路由、specialist 阶段 SFT+GRPO、难验证任务的 rubric-guided GRM，以及 student 前缀上的多教师 reverse KL 与全词表 logits 蒸馏。V4-Pro 的[固定版本 Gate 实现](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/model.py#L546-L584)区分按 token ID 查表与按当前表示打分后选择 expert 的路径；具体层数由配置决定。论文描述的是 V4 特定流程；不将其教师权重、按任务分配或生成式评审设计推广为通用规则。
