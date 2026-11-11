# HNSW 怎样逐层找近邻，怎样知道搜索得够不够？

Approximate nearest neighbor search（近似最近邻搜索，ANN）可用 Hierarchical Navigable Small World（分层可导航小世界，HNSW）图实现：高层节点较少，通常提供较长跳转；底层扩大搜索范围，再返回 top-k（最相近的 k 个候选）。它回答的是“怎样在指定距离函数下少比较一部分向量”，并不保证一定找到精确 top-k，也不负责授权。

以下用一份完全合成的 2 维 continuous integration（持续集成，CI）手册 embedding（嵌入向量）讲完建图、搜索与调参。实际 RAG 的向量维数会高得多；这组小坐标只为能手算距离，不是语义 embedding、性能基准或真实用户资料。

## 查询先需要一张怎样的图？

HNSW 为每个节点随机抽取最高层级，层级越高节点越少。每层节点集合是下一层的子集；各层边分别选择，因此某条高层边不保证也出现在下层。高层的节点更少，边通常跨越更远距离，可先走大步，再在底层仔细搜。层级来自概率抽样，不表示该向量“重要”或拥有更高权限。

本例选择 Euclidean distance（欧氏距离，L2），距离越小越近。查询向量 q=(0, 0)，六个手册块的玩具向量和归属如下；A 是最高层入口：

| 节点 | 向量 | 距离 q | 合成租户标签 | 最高层 |
|---|---:|---:|---|---:|
| A | (6, 0) | 6 | blue | 2 |
| B | (3, 0) | 3 | red | 1 |
| C | (1, 0) | 1 | blue | 1 |
| D | (0, 2) | 2 | red | 0 |
| E | (0, 4) | 4 | red | 0 |
| F | (0, 0.5) | 0.5 | blue | 0 |

固定的简化图如下。实线表示同层边，双向可走；虚线连接相邻层，下降时仍从同名节点继续，并不新增一条层内邻接边。这幅玩具图刻意让 A—B—C 在第 1 层和第 0 层重复，方便手算从上往下移动；一般 HNSW 不要求高层边在下层重现。真实 HNSW 还可能因邻居剪枝出现非对称邻接。

~~~mermaid
flowchart TB
    subgraph level2["第 2 层"]
        direction LR
        A2["A"]
    end
    subgraph level1["第 1 层"]
        direction LR
        A1["A"] --- B1["B"] --- C1["C"]
    end
    subgraph level0["第 0 层"]
        direction LR
        A0["A"] --- B0["B"] --- C0["C"] --- D0["D"] --- E0["E"]
        C0 --- F0["F"]
    end
    level2 -. "下降到同名节点" .-> level1
    level1 -. "下降到同名节点" .-> level0
~~~

节点层级逐层向下包含：A 在三层，B、C 在第 1 和第 0 层，D、E、F 只在第 0 层。入口 A 在第 2 层没有同层邻居；下降到第 1 层后，本例可沿 A—B—C 移动。各层边在一般 HNSW 中独立选择；图中的坐标、层级与边都是为本次推演固定的合成输入。

## 查询怎样从入口走到 top-k？

HNSW 查询分两段。上层做贪心下降：从当前入口检查同层邻居，只要邻居离 q 更近就移动过去，直到没有更近邻居，再带着当前节点降到下一层。每一层的入口只保留最佳节点，相当于 ef=1。

到底层后，搜索变成有界的 best-first（优先扩展当前最有希望候选）搜索。要分清两个优先队列：

- **候选队列 C_queue** 是按到 q 距离从小到大弹出的最小堆，保存接下来可扩展的节点。
- **结果队列 W** 是按距离从大到小维护的最大堆，最多保留 ef 个当前最好节点；堆顶就是暂留集合中最远的节点。
- **visited** 集合避免同一个图节点被反复扩展。弹出 C_queue 中最近节点后，若它比 W 当前最远节点更差，搜索就停止；否则检查邻居。只有当 W 未满或新邻居比 W 最远项更近时，新邻居才同时进入 C_queue 与 W。W 超出 ef 后只移除其中最远项；被 W 淘汰的节点仍可能留在 C_queue，之后仍可被扩展。

高层手算中，A 的距离为 6，往 B 移动后为 3，再往 C 移动后为 1；C 没有更近的第 1 层邻居。于是第 0 层从 C 开始，以 ef_search（查询时保留的候选数）=3 扩展：

| 步骤 | 操作 | 候选队列 C_queue（最近在前） | 结果队列 W（最远在前，最多 3 个） |
|---|---|---|---|
| 0 | 从节点 C 开始 | C(1) | C(1) |
| 1 | 展开节点 C，按图中邻接顺序发现 B(3)、D(2)、F(0.5)。W 原只有 C，先让 B、D 入队；F 入队后挤掉 W 最远的 B。B 仍留在候选队列。 | F(0.5), D(2), B(3) | D(2), C(1), F(0.5) |
| 2 | 展开 F，邻居节点 C 已访问。 | D(2), B(3) | D(2), C(1), F(0.5) |
| 3 | 展开 D，发现 E(4)，比 W 最远的 D(2) 还差，因此不加入。 | B(3) | D(2), C(1), F(0.5) |
| 4 | 弹出 B(3) 时，3 大于 W 当前最远距离 2，触发停止条件；不再展开 B。 | 空 | D(2), C(1), F(0.5) |
| 5 | 返回 W，按距离重新排序。 | — | F(0.5), C(1), D(2) |

B 的距离为 3；它先进入 C_queue 与 W，随后被 F 挤出 W，但仍留在 C_queue。等 F、D 均已展开，弹出的 B(3) 大于 W 最远距离 D(2)，搜索才停止。若请求 top-2，返回 F、C；若请求 top-3，则返回 F、C、D。扩大 ef_search 会让算法保留更大的底层搜索候选集合，而不是改变每个向量的距离。

> [!example]- 用 Python 复核固定图搜索结果
> 下面的小程序用固定图复算队列结果。它只实现单层候选搜索和高层贪心入口，不实现随机层级生成、数据库存储、并发建索引或论文中的邻居多样性启发式。
>
> ~~~python
> from heapq import heappop, heappush
>
> vectors = {
>     "A": (6.0, 0.0),
>     "B": (3.0, 0.0),
>     "C": (1.0, 0.0),
>     "D": (0.0, 2.0),
>     "E": (0.0, 4.0),
>     "F": (0.0, 0.5),
> }
> layers = [
>     {"A": ["B"], "B": ["A", "C"], "C": ["B", "D", "F"],
>      "D": ["C", "E"], "E": ["D"], "F": ["C"]},
>     {"A": ["B"], "B": ["A", "C"], "C": ["B"]},
>     {"A": []},
> ]
>
>
> def distance(name, query):
>     x, y = vectors[name]
>     qx, qy = query
>     return ((x - qx) ** 2 + (y - qy) ** 2) ** 0.5
>
>
> def greedy(query, entry, graph):
>     current = entry
>     while True:
>         closer = [
>             node for node in graph[current]
>             if distance(node, query) < distance(current, query)
>         ]
>         if not closer:
>             return current
>         current = min(closer, key=lambda node: distance(node, query))
>
>
> def search_layer(query, entry, graph, ef):
>     candidates = [(distance(entry, query), entry)]
>     results = [(-distance(entry, query), entry)]
>     visited = {entry}
>
>     while candidates:
>         current_distance, current = heappop(candidates)
>         worst_distance = -results[0][0]
>         if current_distance > worst_distance:
>             break
>
>         for neighbor in graph[current]:
>             if neighbor in visited:
>                 continue
>             visited.add(neighbor)
>             neighbor_distance = distance(neighbor, query)
>             worst_distance = -results[0][0]
>
>             if len(results) < ef or neighbor_distance < worst_distance:
>                 heappush(candidates, (neighbor_distance, neighbor))
>                 heappush(results, (-neighbor_distance, neighbor))
>                 if len(results) > ef:
>                     heappop(results)
>
>     return sorted(
>         ((-negative_distance, node) for negative_distance, node in results)
>     )
>
>
> def search(query, ef_search):
>     entry = "A"
>     for level in (2, 1):
>         entry = greedy(query, entry, layers[level])
>     return search_layer(query, entry, layers[0], ef_search)
>
>
> query = (0.0, 0.0)
> labels = {"A": "blue", "B": "red", "C": "blue",
>           "D": "red", "E": "red", "F": "blue"}
>
> for ef in (3, 4):
>     approximate = search(query, ef)
>     filtered = [node for _, node in approximate if labels[node] == "red"][:2]
>     print(ef, approximate, "red after filter:", filtered)
> ~~~
>
> 在此固定邻接表上，输出为 ef=3 时近似候选 F、C、D，过滤后只剩 D；ef=4 时候选为 F、C、D、B，过滤后为 D、B。下一节将这组人为图的结果与精确答案对照。它用于验证推演与程序一致，不是 pgvector 的基准成绩，也不代表其他 HNSW 实现必须按相同内部顺序访问节点。

## 插入一个节点时，层级和邻居怎样变化？

假设新增节点 X 的向量为 (0, 1.4)，且这次抽样给它的最高层是第 1 层；在这个手算例子中层级是固定输入，不重新抽样。X 到已有节点的距离为：

| 候选 | 到 X 的 L2 距离 | 可用层 |
|---|---:|---:|
| D | 0.6 | 0 |
| F | 0.9 | 0 |
| C | √2.96 ≈ 1.720 | 1、0 |
| E | 2.6 | 0 |
| B | √10.96 ≈ 3.311 | 1、0 |
| A | √37.96 ≈ 6.161 | 2、1、0 |

本次固定 ef_construction=4（建图时保留的候选数）、M=2（邻接容量主参数；本例上层上限取 2 条边，底层上限另设）。插入从现有最高入口 A 开始，在第 2 层以 ef=1 贪心查找；随后第 1 层以 ef_construction=4 搜到 W={C(1.720), B(3.311), A(6.161)}。算法把这一层的 W 带作第 0 层的入口候选；以相同 ef_construction 搜索后，本图的 W={D(0.6), F(0.9), C(1.720), E(2.6)}。为能手算，暂把选邻简化为从候选中挑最近节点：

1. 第 1 层候选 W 为 C、B、A；按到 X 的距离选 C、B，给 X 建立这两条初始链接。
2. 把第 1 层的 W={C,B,A} 带到第 0 层继续搜索，得到 W={D,F,C,E}；按简化规则给 X 选 D、F。
3. 把新边加入已有节点的邻居列表。第 1 层节点 B 原有邻居 A、C，加 X 后有三个邻居。到 B 的距离分别为 d(B,C)=2、d(B,A)=3、d(B,X)=√10.96≈3.311；简化的最近邻剪枝保留 C、A，去掉 B→X。X→B 仍保留，所以这幅图会出现非对称邻接。
4. 原论文将底层连接数上限单独记作 Mmax0，并在实验设置中取 2M；这是底层参数选择，不是所有 HNSW 实现都必须满足的算法恒等式。pgvector v0.8.7 则固定底层上限为 2m=4。D 从 C、E 加到 C、E、X，仅三个连接，尚未超限。超过某层上限的已有邻居也要按实现的选邻启发式剪枝。

实际 HNSW 论文不只取最近 M 个点：启发式会检查候选彼此间的距离，让节点边分布到多个方向，减少“都连到同一簇”造成的导航困难。上面的最近邻剪枝是为解释超限发生时要重新选择链接而作的教学简化。真实系统会按其实现做邻居选择、连边和剪枝；M 不足或邻居选择不佳时，图可能更难到达局部簇，搜索就需提高底层候选数，代价是更多距离计算。

## 怎样比较 M、ef_construction 和 ef_search？

这三个参数分别改图结构、建图候选和查询候选，不能当作同一个“召回旋钮”：

| 参数 | 生命周期 | 改变什么 | 常见代价和方向 |
|---|---|---|---|
| M（pgvector 参数名 m） | 建图和插入 | HNSW 中控制邻接容量的主参数；原论文另以 Mmax0 表示底层上限。pgvector v0.8.7 对底层固定用 2m、其他层用 m。 | 较大 M 往往增加连通性和召回，也增加图边、索引内存、构建/插入工作；查询扩展节点时要比较更多邻居。 |
| ef_construction | 建图和插入 | 为新点找邻居时保留的动态候选数。 | 提高通常改善新边选择与后续召回，代价是较慢的索引构建和插入；建完后它不会直接增加每次查询的候选上限。 |
| ef_search | 每次查询 | 第 0 层查询时保留的动态候选数；不改已建图。 | 提高通常提升召回，代价是查询时延和距离计算更多；按请求复杂度可逐查询调整。 |

截至 2026-11-09，pgvector v0.8.7 的 README 给出的默认值为 m=16、ef_construction=64、ef_search=40；同版源码接受 m 范围 2–100、ef_construction 范围 4–1000、ef_search 范围 1–1000，并在索引构建时要求 ef_construction ≥ 2 × m。这些是 **该版本 pgvector 的接口边界**，不是 HNSW 的通用常数。手算插入例取 ef_construction=4、m=2，正好满足该交叉约束。ef_search 的工程起点通常不低于所需 k，再按召回和时延实测上调；实际设置需检查目标数据库、模型版本、向量维数和工作负载。

固定查询向量、距离度量和授权条件后，在同一个可信授权集合 A(q) 上做精确与近似搜索。为区分“图索引近似得够不够准”和“检索是否找到人工标注的证据”，这里把前者叫 **索引 Recall@k**：令 Exact_k 为 A(q) 中精确最近的 min(k, |A(q)|) 条，ANN_k 为近似扫描并应用同一过滤条件后实际返回的近邻；则

$$
\operatorname{IndexRecall@k}(q)
=
\frac{|\operatorname{ANN}_k(q)\cap\operatorname{Exact}_k(q)|}{|\operatorname{Exact}_k(q)|}
$$

若授权集合不足 k 条，分母就是其中实际存在的精确近邻数；若集合为空，此指标未定义，应单独检查系统确实返回空集，并记为正确无结果的查询。第 k 位边界若有同距记录，只比较距离时可把同距项视为可互换并据此计分；若要求稳定记录 ID，则精确与近似排序应共用同一个 ID 二级键。索引 Recall@k 衡量近似结果与同一度量下精确 top-k 的一致性，不能表示这些结果对问题相关。

若查询 q 有人工标注的相关证据集 Relevant(q)，另算 **Evidence Recall@k（证据召回率）**：被评估检索方法返回的前 k 项（精确 top-k 或 ANN top-k）与 Relevant(q)∩A(q) 的交集大小，除以 Relevant(q)∩A(q) 的大小。它的理论上限为 min(k, |Relevant(q)∩A(q)|) / |Relevant(q)∩A(q)|；调索引前先判断目标 k 是否足以覆盖标注证据。若没有获授权的相关证据，应作为无答案案例单独评估拒答，而不混入这个比例。前者诊断图索引近似，后者同时受语料分块、embedding、距离与索引影响。

用于判断过滤影响时，Exact 与 ANN 都必须在同一授权集合内比较，不能拿全库精确 top-k 充当权限过滤后的答案。每次调参同时记录 P50/P95 查询时延、索引构建时间、索引大小和更新/插入成本。若精确检索对人工证据的 Evidence Recall@k 已低，问题更可能在分块、embedding 模型或距离契约；若精确检索证据召回高而近似索引的 Index Recall@k 低，再检查 HNSW 参数、过滤和扫描上限。不能靠无限调大 ef_search 修复错误向量。

对上面的图，red 标签的精确搜索集合是 D(2)、B(3)、E(4)，top-2 为 D、B。若只用 ef_search=3 得到 F、C、D，再由数据库过滤 red，最终只返回 D，因此这个合成过滤查询的索引 Recall@2 为 1/2；ef_search=4 留下 B 后返回 D、B，索引 Recall@2 为 1。未过滤时，精确 top-2 为 F、C，ef_search=3 的 top-2 也为 F、C，索引 Recall@2=1。一次小例子说明过滤分布怎样改变索引召回，并不证明更大的 ef 一定能解决生产中的所有过滤问题。

## 近似索引的过滤怎样影响召回和授权？

pgvector v0.8.7 文档说明：近似索引先扫描图，之后应用 WHERE 条件。若条件只匹配全表 10% 的行而 hnsw.ef_search=40，且扫描到的近邻标签分布近似全表，平均约 4 行通过过滤；若向量邻域与标签相关，实际通过数可能更高或更低；此时 LIMIT 10 可能返回不足 10 行。v0.8.0 起可启用 iterative index scans 继续走图，直到取够候选或到达 hnsw.max_scan_tuples 等资源边界。strict_order 保持距离排序；relaxed_order 可略微改变顺序以换取更好的过滤召回。大范围之外也可以按过滤值选择 partial index、分区或在小的授权子集上做精确搜索。

**过滤条件不等于授权。** 应用必须根据可信身份计算租户、用户和文档访问条件，并在任何模型可见结果之前再验证返回记录。图过滤解决哪些行参与最终结果的问题；共享近似图的遍历和候选数还可能影响其他租户的召回、时延或可观察结果。若隔离要求更强，应按租户或信任域分索引/表/分区，并在数据库权限与查询路径上落实；不能只让调用方传 tenant_id 就认为已授权。已有 [RAG 授权、版本与索引状态](rag-architecture-and-implementation.md) 说明来源身份、授权和索引状态之间的责任边界。

两种任务的漏召回代价也不一样：

- **CI 手册 RAG**（Retrieval-Augmented Generation，检索增强生成）需要找到能支持回答的有效版本与条件。把检索结果与人工标注的规则块比较 Evidence Recall@k，并检查撤回版本、低频错误标识符、少量授权文档和过滤后不足 k 的情形。漏掉断言失败条款可能导致错误建议，因而要按业务质量门槛评估。
- **近重复文本去重** 只要正确找出超过相似度阈值的重复段落即可，不要求模型引用政策；漏检会留下重复内容，误报会把不同段落合并。评估应按重复对、阈值与精确确认规则衡量，不能把 RAG 的 top-k 召回门槛直接搬来。

## 相关笔记

- [怎样从授权文档中检索并核验回答依据？](rag-architecture-and-implementation.md)：提供 embedding、过滤、候选融合、证据版本与引用的完整 RAG 流程。
- [怎样测量并降低 AI 应用的时延与成本，同时守住任务质量？](../systems/ai-latency-and-cost-optimization.md)：帮助比较搜索延迟、缓存和每份成功任务成本。
- [怎样让模型 API 调用在限额、失败和截止时间内有界？](../systems/bounded-model-api-calls.md)：决定生成 embedding 所用请求如何排队、重试和停止。

> [!info]- 来源
> 本章固定的 A–F、X 节点、二维坐标、层级、租户标签和距离表均为合成教学输入；搜索结果由文中 Python 程序复算，不是大型语料 benchmark。
>
> - **HNSW 的多层结构、随机层级、双优先队列、贪心入口、ef 搜索和插入/剪枝。** Malkov & Yashunin，[“Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs,” arXiv v4](https://arxiv.org/pdf/1603.09320v4)，2018-08-14，pp. 3–5，Algorithms 1–5；参数与构建/查询时间权衡见 §§4.1–4.2、Figures 6–10。论文实验均限定于其数据集、实现与硬件，本章仅把机制用于手推。
> - **pgvector 近似索引、距离操作符、HNSW 参数、过滤和多租户影响。** pgvector，[v0.8.7 README](https://github.com/pgvector/pgvector/blob/v0.8.7/README.md)，核对于 2026-11-09，“Indexing”“HNSW”“Filtering”“Multitenancy”“Iterative Index Scans”；精确查询/近似查询取舍及过滤后数量以该版本文档为准。
> - **pgvector v0.8.7 参数的默认值、合法范围、交叉约束和层 0 度数。** [v0.8.7 src/hnsw.h](https://github.com/pgvector/pgvector/blob/v0.8.7/src/hnsw.h)、[src/hnsw.c](https://github.com/pgvector/pgvector/blob/v0.8.7/src/hnsw.c) 与 [src/hnswbuild.c](https://github.com/pgvector/pgvector/blob/v0.8.7/src/hnswbuild.c)，核对于 2026-11-09；m、ef_construction、ef_search 的范围与默认值、第 0 层 2M 上限及构建时 ef_construction ≥ 2 × m 的校验均按对应源码确认。其他 pgvector 版本和向量数据库可能采用不同约束。
> - **Recall 的 ANN 定义。** HNSW 原论文 v4 §1 将 recall 定义为找到的真实近邻数除以 K；本章将它具体写成相同查询、距离度量和授权过滤下 ANN top-k 与 Exact top-k 的交集比例。
