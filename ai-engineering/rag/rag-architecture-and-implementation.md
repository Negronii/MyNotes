# 怎样从授权文档中检索并核验回答依据？

Retrieval-augmented generation（检索增强生成，RAG）把外部资料选入模型本轮输入，让回答能引用可更新、可核验的来源。它把“哪些资料可用、从哪里找到、怎样带进模型”变成应用责任；检索和引用仍需分别验证。

上一轮已从 `read_build_log` 的 `c1` 结果确认：构建 42 的 `reject_empty_name` 在 `unit-tests` 中期望 HTTP `400`、实际得到 `200`，进程退出状态为 `1`。现在开发者开启新一轮追问：“按当前 CI 手册，该构建该重跑吗？”以下 `CI-RETRY-v3`、`HTTP-CONTRACT-v1` 和 `CI-TEST-v1` 都是为解释流程而造的通用公开文档；它们不表示真实组织的规章，也不涉及私人或项目代码。RAG 要回答的是文档中的政策问题，日志仍是独立事实来源。[AI 服务如何将一条消息变成完整回答？](../systems/from-message-to-answer.md)

## 一条证据怎样从文档走到回答

下面的流程将索引更新、调用者范围、候选检索和回答核验分开。构建 42 的手册问题要先确定调用者能读哪些文档，再从有效版本中取段落；只有适用的段落进入上下文。

~~~mermaid
flowchart TD
    Docs["文档 · 版本 · 范围"] --> Parse["解析与切块"] --> Index["索引"]
    Caller["调用者 + build 42 问题"] --> Scope["授权与版本过滤"] --> Search["检索候选"]
    Index --> Search
    Search --> Rank["融合与重排"] --> Pack["按预算选证据"] --> Check["生成并核对引用"] --> Answer["回答或说明不足"]
    Change["新增、撤回、改权"] -.-> Parse
~~~

对构建 42 而言，读日志的工具调用属于按已知 `build_id` 直接查询；RAG 用在“当前手册怎么说”这类需要从文档库找适用段落的问题。两种结果进入同一个模型输入时，仍应保持日志记录 `c1` 与文档片段 ID 各自的来源。

## 更新、权限和版本先于排序

入库时，解析器应保留文档结构以及能解释段落的元数据。每个 chunk（文档块）至少能追溯到原文标识、版本、有效期、适用范围、标题路径和原文位置；用户问题可能跨多个版本或条件时，段落本身也要保留限定语。

假设样例文档为：

| 来源 | 状态 | 段落内容 |
|---|---|---|
| `CI-RETRY-v3#assertion-failure` | 当前，2026-10-01 生效 | 只可重试网络或工作节点中断；断言失败必须先调查，不自动重试。 |
| `CI-RETRY-v2#retry` | 已撤回，2026-10-01 前有效 | 旧版本允许任何失败构建重试一次。 |
| `HTTP-CONTRACT-v1#empty-name` | 当前 | 空名称请求应返回 HTTP `400`。 |
| `CI-TEST-v1#diagnosis` | 当前 | 检查失败测试、输入、预期与实际响应，并沿请求路径调查。 |

索引管道应按明确顺序处理变更：读取权威源的版本与范围，解析并重分块，生成或更新检索表示，确认新版本可用后撤下旧版本。删除、改权限和纠错都属于索引更新；只把新文件加进去会让旧片段继续参加排序。若检索仍返回已撤回的 `CI-RETRY-v2`，权威状态已是 `v3` 就应丢弃旧命中；若有效 `v3` 尚未同步，可从授权源补读，或说明暂时没有可用依据。需要即时撤权时，在模型见到内容之前按权威授权源重新检查命中片段，不能等待异步向量索引自行收敛。

> [!info] 索引状态和源状态是两份状态
> 托管检索服务可能异步处理新增文件，也可能在删除后短暂返回旧内容。OpenAI Retrieval 当前文档说明其向量存储（vector store）删除具有最终一致性。这个服务行为不代表每种数据库；应用应确认本次索引任务已完成，并针对撤权、删除和新版本生效设定自己的读权限边界。

调用者权限应由可信应用逻辑决定，授权和有效版本条件要带入每条检索查询。`tenant_id`、区域、文档状态或版本等字段能表达过滤，但只有元数据正确、条件不被绕过并按权威状态复核时才有意义。应用只把过滤、版本及必要授权复核都通过的片段交给融合、外部重排和模型；即使某段比当前手册更相关，只要超出开发者当前的访问范围，也不能进入候选。不能为凑足 `top-k`（前 k 个候选）放宽限制。

授权边界与近似索引的内部扫描顺序是两回事。以 pgvector 的 [Hierarchical Navigable Small World（HNSW，分层可导航小世界）图搜索](hnsw-vector-index-search.md)为例，近似索引可能先找近邻再在同一 SQL 查询中应用 `WHERE`；匹配行比例低时，返回数和召回率会下降。SQL 条件限制返回哪些行，但共享近似索引的扫描还可能通过结果数量、分数或时延暴露其他租户文档的存在。需要更严格隔离时，应让搜索在获授权范围内进行，或按租户、信任域分离索引；不能把结果过滤等同于完整隔离。扫描数量、迭代扫描或按范围分区可能改善授权集合上的召回与时延；也可比较在小授权子集上精确搜索。

> [!warning] 检索相关性不会授予读取权限
> 未授权或已经撤回的片段，即使语义相关，也不能放进提示词。文档中的文字同样只是待解释的数据；恶意内容里写着“忽略上面的指令”不会因此成为系统指令，也不能批准工具动作。

## 分块要保留问题所需的限定关系

把一份长文拆成可检索段落，是为了缩小候选搜索与模型输入。块太小会把标题、条件或例外切走；块太大则让无关段落稀释相似度、占据上下文预算。构建 42 的失败原因和重试规则要来自不同资料，但每个片段都需保留足以判定适用范围的段落标题和限定句。

例如，下面这段必须作为一个逻辑块，或使它与相邻定义之间保留可追溯关系：

> [!example] 构建 42 的手册段落
> `CI-RETRY-v3 > Retry policy`：只可重试网络或工作节点（worker）中断；测试断言失败必须先调查，且不会自动重跑。该规则适用于当前公开 CI 手册版本 `v3`。

如果错误切分后只取到“网络或工作节点中断可重试”，没带出同一标题下的断言失败条款，这段就不能判断构建 42 这次断言失败应如何处理。应取回完整规则段，或载入同版本、同授权范围的父段落再核对；不能用旧版本或其他范围的段落补足缺失句。

按源结构分块能优先保住手册标题和条件；当一个章节远超检索单元上限时，再用递归边界或定长切分。语义分块可以尝试按主题边界组合句子，但它需要额外计算，并没有对所有文档稳定胜过简单方法。常见选择的代价如下：

| 方法 | 怎样切分 | 适合什么输入 | 主要代价 |
|---|---|---|---|
| 定长 | 按字符或分词器词元数切到上限，可设置相邻块重叠。 | 做可重复的基线，或上游文本缺少结构。 | 容易切断标题、条件、表格行或代码语义。 |
| 递归 | 依照段落、换行、句子、空格等分隔符逐级拆分。 | 有自然分隔符的一般文本。 | 实际长度不同，分隔优先级未必对应主题边界。 |
| 结构感知 | 按标题、页面、表格、代码结构或段落标记分组。 | 源格式已经表达了条件、字段关系或层级。 | 依赖解析质量；过长结构仍需后续拆分。 |
| 语义分块 | 按句子或段落的表示相似度估计主题边界。 | 结构边界不够且离线评估显示收益。 | 增加建索引成本；分组阈值和编码模型也要维护。 |

**先验证长度单位。** 字符数和分词器（tokenizer）计出的词元（token）数不能互换。LangChain 当前教程使用 `RecursiveCharacterTextSplitter`，默认示例以 `chunk_size=1000`、`chunk_overlap=200` 并保留原文字符偏移；同一数字若由按 token 计量的服务使用，表示的内容长度就不同。OpenAI Retrieval 当前文档的托管向量存储默认是每块最多 800 个 token、重叠 400 个 token；这是该服务的默认值，不是通用最佳配置。

~~~python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# documents 是已解析、保留来源信息的 Document 列表
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # 此教程的默认长度单位为字符
    chunk_overlap=200,     # 目标重叠字符数，实际相邻重叠量可不同
    add_start_index=True,  # 在各 Document.page_content 内记录字符偏移
)
chunks = splitter.split_documents(documents)
~~~

`add_start_index` 记录的是输入 `Document.page_content` 内的偏移；若每页作为独立 Document 输入，还要保留对应 `page` 元数据。`chunk_overlap=200` 是目标值，递归切分不保证每对相邻块恰好重叠 200 字符。重叠能保留切分边界附近的语境，也会重复索引内容并增加成本；把它当作待比较的参数，不是必开的修复项。块大小、重叠量和结构策略都应按带有人工标注依据的查询集评估，并检查条件是否留在块内、复合问题所需段落是否齐全、重复块是否挤占检索窗口。几项 2025–2026 研究对结构感知切分、语义切分和重叠给出不同结果；它们共同说明设置取决于目标语料、查询和模型，不能直接导出一个通用块长或重叠率。

## 词法、向量和混合检索怎样互补

**Lexical retrieval（词法检索）**按索引分析器生成的词项和相关性权重查找，BM25 是常用基线；它通常适合精确标识符、错误名和状态码。查询里的 `reject_empty_name` 或 HTTP `200` 应能找到包含相同字样的日志或 API 约定。需要可靠原样匹配时，应保留可直接查询的精确字段，不能把 BM25 排序等同于字段级精确查询。

**Dense retrieval（稠密检索）**把问题与段落编码成 embedding（嵌入向量），按相似度检索。它可能找到表达不同、含义相近的段落，例如用户说“测试响应不符合约定”，手册却写“空名称应返回 400”。问题向量和文档向量必须属于兼容的表示契约：维度、预处理及模型训练方式都要匹配。检索模型可以使用不同的查询和文档编码器，例如 Dense Passage Retrieval（DPR，稠密段落检索）的双编码器；不能仅凭两者是向量就假定可以比较。选择编码器时还应比较目标语种和任务、查询与文档输入格式、部署与隐私要求、输入上限、时延、费用及目标语料上的效果。若切换文档侧编码、维度、归一化或预处理会破坏兼容性，就要重编码受影响的文档向量并迁移索引；只改查询侧也须复核兼容性和召回。

假设查询向量为 $q$、块向量为 $d$，余弦相似度为

$$
\operatorname{cos}(q,d)=\frac{q\cdot d}{\lVert q\rVert\lVert d\rVert}.
$$

例如，$q=(1,0)$、$d=(2,0)$ 时，点积为 $2$，余弦为 $2/(1\times2)=1$：两向量方向相同，但点积受长度影响。若索引把二者都归一化，$d$ 变为 $(1,0)$，点积就与余弦同为 $1$。若索引使用欧氏距离，则

$$
\lVert q-d\rVert^2=\lVert q\rVert^2+\lVert d\rVert^2-2(q\cdot d).
$$

当两向量都归一化为单位长度时，平方欧氏距离为 $2-2\operatorname{cos}(q,d)$，所以按欧氏距离由小到大与按余弦相似度由大到小排序相同。距离或分数方向由索引配置决定，数值大小不能直接跨模型比较。

稀疏、稠密检索各取一组候选，合并后再排名，就是**Hybrid retrieval（混合检索）**的一种实现。它只在候选集合确实互补时增加召回；BM25 等词法排序分数与向量相似度往往不在同一尺度，不能未经校准直接相加。可用 Reciprocal Rank Fusion（RRF，倒数排名融合）只融合名次。对候选 $d$，令其在检索器 $i$ 的名次为 $r_i(d)$，则：

$$
\operatorname{RRF}(d)=\sum_i \frac{1}{k+r_i(d)}.
$$

以下名次和分数是为演算构造的检索示意，不是模型、索引或线上查询的测量结果。未出现在某个检索器截断列表中的候选，在该路 RRF 求和中贡献为 $0$。本例检索的问题是“构建 42 的 `reject_empty_name` 期望 HTTP 400、实际 HTTP 200，断言失败是否应自动重跑？”；`c1` 提供具体日志事实，文档检索分支查找当前手册规则、HTTP 合约和诊断步骤。所有结果先经过当前版本与授权范围过滤；$k=60$ 是本例的融合参数。

| 段落 | 词法名次 | 稠密名次 | RRF 计算 | 分数 |
|---|---:|---:|---|---:|
| `CI-RETRY-v3#assertion-failure` | 2 | 1 | $1/62+1/61$ | 0.032522 |
| `HTTP-CONTRACT-v1#empty-name` | 1 | 3 | $1/61+1/63$ | 0.032266 |
| `CI-TEST-v1#diagnosis` | 3 | 2 | $1/63+1/62$ | 0.032002 |

RRF 将当前重试规则排到最前，同时保留下一名的 HTTP 约定。一个 cross-encoder（交叉编码器）可以把查询与每个候选拼在一起打相关性分，再重排小集合。假设它给 HTTP 合约、重试规则和诊断说明分别打出 `0.91`、`0.76`、`0.55`；这些分数只是示意的相关性顺序，不是概率。本例中 HTTP 合约由第二名升到第一名，重试规则降到第二名。这种两阶段流程先扩大候选召回，再对较小候选集做精排，能改善排序但不能找回未召回的证据，且增加计算和时延。评估时应比较不同候选深度；若把所有候选都传给模型，且 Precision@$j$ 中 $j$ 等于候选总数，只改变顺序不会改变集合意义上的精确率；当 $j$ 小于候选总数时，改序可能改变该指标和进入上下文的证据；本例仅交换前两名，取前两项时的证据集合与 Precision@2 都不变。

一项 2026 年金融问答预印本在含文本和表格的基准上报告：混合检索加神经重排表现强，BM25 胜过所测稠密基线，HyDE 与多查询对精确数值题帮助有限。主比较按整篇文档检索；这些观察限于该基准、模型和测量方式，提示表格与精确数字任务应单独评估检索路径。

## 相同文本重复入库时怎样复用 embedding？

同一手册段落可能因重建索引、异步重试或被不同文档引用而重复送去编码。Embedding cache（嵌入缓存）保存的是“特定输入表示契约下算出的向量”，减少重复模型请求；它不是检索结果缓存，不保存某个问题的 top-k 列表，也不意味着两份来源可以合并。

以合成公开段落 CI-RETRY-v3#assertion-failure 为例。调用方先完成标题、模板和动态字段的拼装与预处理，再将实际交给编码器的完整文本作为 `canonical_text`。缓存键要散列这份实际输入；正文相同但标题或模板前缀不同，编码器看到的文本不同，就不能共用向量。只有完整输入字节与编码契约都一致，才可复用：

~~~text
K = SHA256(UTF8(JSON_ARRAY((
  cache_format_version,
  cache_scope,
  provider,
  endpoint,
  model_revision,
  input_role,
  output_dimension,
  text_canonicalization_version,
  preprocessing_version,
  normalization_version,
  SHA256(UTF8(canonical_text))
))))
~~~

键字段是应用的缓存契约，不是提供方要求的 API 参数。按固定顺序把字段序列化为 JSON 数组，再做 UTF-8 与摘要；JSON 会保留字段边界，也会转义字段值内的 NUL 字符。模型别名若会变更，要用明确模型版本或内部部署代次；同名模型更新、模型切换、维度改变、编码用途不同、规范化或清理逻辑改变，均应使键变化。对于 query/document 不对称的双编码器，角色必须区分；即使某端点今天对两种角色恰好返回相同形式，应用也不应把两种语义任务默认为同一个缓存空间。服务支持缩短输出维度时，维度也要进入契约并单独重建对应索引。

下面的函数假定调用方已依指定版本完成所有会改变编码器输入的标题、模板、动态字段拼装、文本清理与分块，并把实际送入编码器的最终文本原样传为 `canonical_text`；它只负责构造缓存键，不实现这些转换。

~~~python
import hashlib
import json


def embedding_cache_key(
    *,
    scope,
    provider,
    endpoint,
    model_revision,
    role,
    dimensions,
    canonicalization,
    preprocessing,
    normalization,
    canonical_text,
):
    canonical_bytes = canonical_text.encode("utf-8")
    text_digest = hashlib.sha256(canonical_bytes).hexdigest()
    fields = (
        "embedding-cache-v1",
        scope,
        provider,
        endpoint,
        model_revision,
        role,
        str(dimensions),
        canonicalization,
        preprocessing,
        normalization,
        text_digest,
    )
    encoded = json.dumps(
        fields,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
~~~

缓存命中后，向量值可以复用，但每份文档的索引记录仍独立：

| 数据 | 例子 | 是否由相同文本命中合并 |
|---|---|---|
| embedding 缓存项 | 缓存键、向量、编码契约版本、生成时间 | 可以复用向量值 |
| 文档块记录 | source_id、chunk_id、来源版本、标题位置、内容状态 | 不合并 |
| 授权与删除状态 | tenant、ACL/策略版本、可见范围、撤回状态 | 不从缓存继承 |

例如两个合成文档都包含同样的公共 CI 规则。只有二者经过标题、模板和动态字段处理后送给编码器的完整文本也相同，且缓存范围、模型修订、文档角色、维度和预处理版本都一致，才可读同一个向量值；但写入索引时仍须各存各的 source_id、chunk_id、版本和授权元数据。第二份文档因复用同一编码结果，不等于它自动获得第一份文档的权限或来源身份。

若规则来源改版，但经过全部字段拼装和预处理后送给编码器的 `canonical_text` 未变，可以复用向量，同时新增版本化索引记录；若标题、模板、动态字段或正文使实际输入改变，则摘要改变并重新编码。若模型、输出维度或预处理版本变了，缓存键自然不同，需要为新契约重新编码并在独立索引代次验证后切换。旧向量不能因为长度“看起来差不多”就混入新模型空间。若只改变 ACL 而文本和模型契约不变，向量计算本身可以不变，但必须立即更新或撤下索引记录上的 ACL；每次查询仍按可信调用者身份判断权限。缓存范围字段用于避免不同安全域误共享数据，不能作为授权证明。

向量是可还原或推测原文特征的派生数据，不能假定它比正文无敏感性。对敏感语料，缓存键可用密钥化摘要以减少低熵原文的字典猜测风险；日志仅记录不透明键或截断指纹，并按原文删除、保留和访问规则处理派生向量。权限撤销、来源删除或数据保留期到期时，应用仍要处置对应向量索引记录和缓存数据；命中缓存不代表可跳过删除流程。

实际收益按调用量核算：给每次 embedding 请求记录 cache_hit、向量契约版本和来源索引任务 ID；比较节省的 API 请求数与 Token、缓存查找/存储成本，以及索引构建耗时。缓存缺失时仍走[有界模型 API 调用](../systems/bounded-model-api-calls.md)的配额、重试与截止流程；写入索引时则按[HNSW 插入与近似搜索](hnsw-vector-index-search.md)管理向量空间、过滤和召回。

## 候选不全时怎样继续找

只有在候选缺少依据或复合问题缺少其中一环时才增加查询步骤；每一步都沿用相同的授权和版本过滤，并记录它解决哪个缺口。

| 失败信号 | 追加检索动作 | 需要防住的偏差 |
|---|---|---|
| 用户说法与文档术语不同，原查询没找到规则。 | 保留原查询，再扩展一个语义相近的表述；比较两组命中是否指向同一有效段落。构建 42 可把“该不该重跑”补成“断言失败 retry policy”。 | 改写可能改变问题范围，不能丢掉原查询或把改写本身当作事实。 |
| 查询表达较抽象、与相关段落措辞差异较大，稠密检索没有候选。 | Hypothetical Document Embeddings（HyDE，假设文档嵌入）先生成一段假想答案文本，将其仅用于计算检索向量，再从真实库里取回资料。 | 假想文本可能包含错误细节；它只用于找真实来源，绝不是回答证据。 |
| 子块命中，但定义、例外或适用条件不在块内。 | Parent-child retrieval（父子块检索）先取较小子块，再载入其父段落或标题；重新验证父段落的版本、范围和权限后去重组装。 | 父段可能过宽、重复或已撤回；不能因为子块命中就无条件附加父文档。 |
| 一个问题要先分类，再依赖分类查规则或例外。 | Multi-step retrieval（多步检索）先取得第一步证据，将剩余未回答部分写成子问题，再搜索一次；例如先确认是断言失败，再查该类失败的重试条款。 | 每步新查询可能累积误解；保留原问题，记录子问题到证据的链路，并在证据够用或明确无结果时停止。 |

HyDE 原论文把生成段落当作零样本稠密检索的中间表示，并明确指出其可含有虚假内容；不能以“模型生成得很像政策”来绕过来源核验。多步检索也只是在运行时改变查询路径，不会提升来源权限。

> [!example] 从候选到可引用证据
> 上下文章的 145-token 玩具预算计的是完整文本输入，且只放一段手册规则。本例另设 64-token 的证据子预算，只计算“来源 ID：段落正文”两段原文，不含消息封装或其他输入。用同一 `tiktoken 0.12.0` `cl100k_base` 编码时，重试规则为 40 token，HTTP 合约为 19 token，合计 59，能同时保留两段。
>
> - `CI-RETRY-v3#assertion-failure`：只可重试网络或工作节点中断；断言失败必须先调查，不自动重试。
> - `HTTP-CONTRACT-v1#empty-name`：空名称请求应返回 HTTP `400`。
>
> 本例因此将这两段实际交付模型，并排除候选 `CI-TEST-v1#diagnosis`。前一段支持本次断言失败不能自动重跑；后一段支持预期状态。每条主张都要映射到实际入模的证据 ID、版本和段落，而不能引用仅获授权或曾进入候选列表的材料。

## 证据组装、回答和失败定位

把检索段落放入上下文时，保留来源 ID、版本和适用范围。按证据预算挑选能支持必要主张的最小集合；查询“该不该重跑”需要 `CI-RETRY-v3` 的断言失败条款，不能只放一段通用“重新运行测试”说明。若选中的子块依赖父章节定义，要确认父章节版本和权限再添加。上下文篇的 145-token 完整文本输入预算与这里 64-token 证据子预算范围不同；增加 HTTP 合约是这个独立组装例子的明确预算假设。

将文档内容作为不可信数据提供给模型。系统提示可以要求它根据实际提供的证据回答、标出来源 ID、证据不足时停下，但这只能约束输出意图；模型可能误读或遗漏材料。应用应把每条主张映射到本轮真正交付模型的证据 ID、版本和段落，并确认它仍有效、获授权且确实支持该主张。只在授权候选里、却没有进入最终输入的片段不能被引用；`c1` 还必须能由应用运行记录绑定到构建 42 的原始日志。若两份仍有效且获授权的来源互相冲突，应按预先定义的权威性、适用范围和版本规则裁决；规则不能解决时，就展示冲突及对应段落并说明无法确定，不按检索分数任意选一份。引用标记存在，不等于来源真正支持了主张。

本例的主张—证据映射可以直接写入答案：“构建 42 的 `reject_empty_name` 期望 HTTP `400`、实际为 `200`〔运行记录中的 `c1`，绑定 `build_id=42`〕。按当前 `CI-RETRY-v3#assertion-failure`，断言失败必须先调查，不能自动重跑。当前 `HTTP-CONTRACT-v1#empty-name` 也规定空名称请求应返回 `400`。基于这条日志和合约，下一步可检查该请求的校验路径。”前三项分别由本轮实际打包的 `c1`、重试规则和 HTTP 合约支持；最后一句是由已核实事实引出的排查建议，不是证据直接证明的根因。

失败要按其发生阶段定位：

| 观察到的失败 | 检查哪里 | 下一步只针对该原因比较 |
|---|---|---|
| 当前来源没有事实，或新版本没有入库。 | 源文档、解析结果、版本状态和异步索引任务。 | 修复解析/同步，或说明没有可用依据。 |
| 依据存在，但候选中没有它。 | 授权和有效期过滤、chunk 边界、查询表达、embedding 契约、候选窗口。 | 先修范围或分块，再用同一查询集比较 BM25、稠密与混合检索。 |
| 候选中有证据，最终输入却没有。 | 融合、重排、去重、预算、截断和父块加载。 | 调整排序或组装，确认引用映射仍然准确。 |
| 证据进了上下文，答案仍不支持或引用错位。 | 实际输入段落、版本冲突、输出中的每条主张与引用。 | 保持检索结果，单独比较提示或模型变化。 |

要知道改动是否有效，应分别评估证据检索和回答生成。对固定查询集标出预期的 `doc_id`、版本与段落 ID，先看 Recall@k（前 $k$ 个候选召回率）是否取到所需依据，再看排序后的证据是否进入上下文；生成侧检查事实正确性、主张支持、引用准确和缺证时是否暂停。系统层还要统计索引新鲜度、权限拒绝、端到端时延和成本。评估集中应包括旧版本、无答案问题、空名称断言失败、工作节点中断、无权文档以及权限撤销；不能只用“答案流畅”当通过条件。RAGChecker 按主张粒度拆分检索和生成问题；Ragas、ARES 以不同方式评估上下文相关性、回答忠实度或相关性。这些自动化框架是诊断信号，应对代表性案例人工复核，并按应用的权限、更新与引用要求设验收条件，不能把框架分数当作通用合格线。[LLM 评估方法](../evaluation/llm-evaluation-methods.md)

## RAG、长上下文与微调的分工

| 方法 | 解决的约束 | 仍需应用处理的事 |
|---|---|---|
| RAG | 从大于单次输入、持续更新或按来源控制访问的文档集合中挑证据。 | 来源同步、授权过滤、版本和删除、召回与引用验证。 |
| 长上下文 | 允许把一批已知材料一起交给模型，适合需要跨材料比较的任务。 | 应用仍要选出有权使用的材料；窗口长度不保证模型可靠使用每一处内容。 |
| 微调 | 用重复训练样例改变模型的行为、风格或输出模式。 | 不能自动提供当前文档或执行访问规则；有引用需求仍需查询外部证据。 |

更大的上下文窗口只改变模型一次能接收多少输入，不会替应用选择调用者有权看的文档、同步撤回版本或按问题筛选证据。[长上下文注意力机制](../foundations/long-context-attention.md)解释模型内部如何表示、访问历史；模型窗口长短不是外部资料的授权与维护机制。若 corpus 很小、调用者可读全集且需要跨文档推理，把授权材料整体放入上下文可能合适；仍需应用层决定读哪些版本和如何核验。训练参数只在训练时更新；检索、输入组装和评估是运行时及验收环节，不能混称为“模型学会了最新政策”。[奖励信号如何用于推理训练](../fine-tuning/reward-based-reasoning-training.md)

跨运行的对话历史还要决定是否需要抽取偏好、事实或过程经验；memory 可以由 RAG 检索，原文 RAG 也能直接查历史。两者不是互斥架构。怎样比较加工后的记忆与原文检索，并计入建造、读取和回查成本，见[什么时候值得把历史加工成 Agent 记忆？](../context/agent-memory-design-and-evaluation.md)。

已有研究在公开问答集上给出不同的长上下文与 RAG 比较：一项 EMNLP 2024 评测在其资源配置下发现长上下文平均表现较高、RAG 计算成本较低；另一项 2025 复评报告了数据类型相关的差异，并指出问题与上下文相关性影响结果。它们使用的模型、任务、数据、预算与检索策略有限；应用应在自己的查询、权限和时延约束上比较，而不从论文推出统一优胜者。

## 原始 RAG 论文留下什么

Lewis 等人的 RAG 将可更新的非参数知识库与参数化生成器结合。论文的生成器使用 BART，检索器用 DPR 为问题选出 Wikipedia 段落，再将文档作为潜变量。**RAG-Sequence** 对每份候选文档分别计算整条答案的条件概率，再按文档权重汇合；**RAG-Token** 在每个输出位置分别汇合候选文档对该词元的概率，再对序列位置求积。两者都是根据输入问题检索一次文档集合，RAG-Token 的逐词元边缘化不表示每生成一个词元就重新查询索引。论文在当时的开放领域问答与事实核验任务上，相对其所比较的参数化生成器和检索基线报告改进。

可迁移的设计思想是把模型参数中的知识与能更新的外部证据配合使用，并观察检索对生成的影响。如今应用可以分别替换检索、排序与生成模块，还需把来源访问控制、版本更新、引用验证和运行时评估明确实现。这些工程责任不能归给原论文里的生成概率或单次检索步骤。

## 相关知识

- [上下文工程原则](../context/context-engineering-principles.md)：决定每次推理保留哪些历史、工具结果和文档段落，并管理压缩导致的信息损失。
- [长上下文注意力](../foundations/long-context-attention.md)：解释模型内部的历史表示与选择性访问，不替应用进行授权检索。
- [工具设计与函数调用](../agents/tool-design-and-function-calling.md)：解释如何执行读取日志、搜索文档等模型请求，并恢复不确定的工具状态。
- [AI 生产安全](../safety/ai-safety-in-production.md)：处理文档诱导、权限和运行时控制边界。

> [!info]- 来源
> 本章以一条不含私有资料的构建 42 合成案例演示端到端机制。名次、RRF 分数和交叉编码器示意分数均是手工演算值，不是测量结果。
>
> - **RAG 与长上下文、微调的工程分工。** 本节的流程综合了来源管理与运行时架构；以下来源分别支持 RAG 的文档检索原理、比较结论与索引行为。
> - **原始 RAG 检索—生成机制。** Lewis et al., [“Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” arXiv v4](https://arxiv.org/html/2005.11401v4), 2020，§§2.1–2.5、§4.1 与表 1；包含 RAG-Sequence/RAG-Token 定义和实验任务。
> - **稠密双编码器与 BM25 对照。** Karpukhin et al., [“Dense Passage Retrieval for Open-Domain Question Answering,” arXiv v3 / EMNLP 2020](https://arxiv.org/html/2004.04906v3)，§§2–3；只支持该论文所测的开放领域问答模型与数据。
> - **长上下文与检索增强的比较。** Li et al., [“Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study and Hybrid Approach,” arXiv v2 / EMNLP 2024](https://arxiv.org/html/2407.16833v2)，§§3–5；以及 Li et al., [“Long Context vs. RAG for LLMs: An Evaluation and Revisits,” arXiv v1](https://arxiv.org/html/2501.01880v1), 2024-12-27 提交，§§3–5。正文只概述各自评测结果，不将它们解释为跨数据集的固定排序。
> - **长上下文位置影响。** Liu et al., [“Lost in the Middle: How Language Models Use Long Contexts,” TACL 2024 / arXiv v3](https://arxiv.org/html/2307.03172v3)，§§3–4；研究中的任务与模型范围见上下文工程章来源映射。
> - **文档分块实验。** Wang et al., [“Document Segmentation Matters for Retrieval-Augmented Generation,” Findings of ACL 2025](https://aclanthology.org/2025.findings-acl.422/)，§§3–4；Qu et al., [“Is Semantic Chunking Worth the Computational Cost?” Findings of NAACL 2025](https://aclanthology.org/2025.findings-naacl.114/)，§§3–5；Bennani & Moslonka, [“A Systematic Analysis of Chunking Strategies for Reliable Question Answering,” arXiv v1](https://arxiv.org/html/2601.14123v1), 2026-01-20，§§2–3。最后一项为预印本；其对比之一使用 SPLADE、Ministral-8B-Instruct-2410 与 Natural Questions，测试的 10–20% overlap 未改善 BERTScore 或 exact match。
> - **递归分块示例、字符长度单位与偏移。** LangChain, [“Build a semantic search engine with LangChain”](https://docs.langchain.com/oss/python/langchain/knowledge-base) 和 [“Splitting recursively”](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter)，检查于 2026-11-06，`Load and split a PDF`、分隔符与长度计量段。参数 `1000`/`200` 是当前教程示例；实际代码应确认 package 版本与长度函数。
> - **混合候选和 RRF。** Thakur et al., [“BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models,” arXiv v4 / NeurIPS 2021](https://arxiv.org/abs/2104.08663)，§§3–5；Cormack, Clarke & Büttcher, [“Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods,” SIGIR 2009](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)，pp. 758–759。BEIR 的平均结果受其 18 个公开数据集和评估设置限制。
> - **索引权限过滤与近似扫描。** [pgvector 官方 README](https://github.com/pgvector/pgvector)，当前版 `Filtering` 与 `Iterative Index Scans`；只描述该实现。[OpenAI API Retrieval](https://developers.openai.com/api/docs/guides/retrieval)，检查于 2026-11-06，`Vector store file operations`、`Chunking`、`Attribute filtering`，用于托管索引异步处理、删除一致性和默认分块参数示例。
> - **向量搜索表示与输入。** [OpenAI API Vector embeddings](https://developers.openai.com/api/docs/guides/embeddings)，检查于 2026-11-06，向量归一化与相似度说明；DPR v3 §§2–3 支持问题和段落分别编码的通用示例。
> - **embedding API 的模型、维度、批量输入与 usage。** [OpenAI API Embeddings create reference](https://developers.openai.com/api/reference/resources/embeddings/methods/create)，检查于 2026-11-09；当前接口支持一个或多个输入，text-embedding-3 及更新模型支持可选 dimensions。缓存键中的 provider/model 修订、角色、维度及预处理版本是应用对表示兼容性的工程约定，不是 API 规定的缓存键格式。
> - **检索策略在文本与表格混合金融问题上的范围。** [“From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents,” arXiv v1](https://arxiv.org/html/2604.01733v1), 2026-04-02，摘要与 §§III–IV；T²-RAGBench 含 23,088 个问题与 7,318 份文档。主比较以平均约 920 token 的整篇文档为单位（§III-D），§IV-C 的消融比较融合方式与重排深度，分块消融仍列为未来工作；混合 RRF 加 Cohere Rerank 报告 Recall@5 0.816，BM25 在该基准强于所测 dense baseline，HyDE 与多查询对精确数值题表现较弱。该预印本数据和设置有限，本文不把结果外推为通用策略。
> - **假设文档仅用于检索。** Gao et al., [“Precise Zero-Shot Dense Retrieval without Relevance Labels,” arXiv v1](https://arxiv.org/abs/2212.10496), 2022-12-20，§§2–3；提出 HyDE 中间文本检索方法，并指出假想文档可能含有错误细节。
> - **检索与生成分开诊断。** Ru et al., [“RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented Generation,” arXiv v2](https://arxiv.org/abs/2408.08067), 2024-08-17，§§3–4；Es et al., [“Ragas: Automated Evaluation of Retrieval Augmented Generation,” arXiv v2](https://arxiv.org/abs/2309.15217v2), 2025-04-28，§§3–4；Saad-Falcon et al., [“ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems,” arXiv v2](https://arxiv.org/abs/2311.09476v2), 2024-03-31，§§3–4。三者的维度、评审器与校准方式不同；指标是辅助诊断框架，不代表本应用的唯一验收标准。
> - **检索段落中的恶意指令和向量数据边界。** OWASP GenAI Security Project, [LLM01:2026 Prompt Injection](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM01_PromptInjection.md) 与 [LLM09:2026 Vector and Embedding Weaknesses](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM09_VectorAndEmbeddingWeaknesses.md)，检查于 2026-11-06。分别支持不可信输入与权限的分界、共享相似度搜索的跨租户探测风险及按范围检索/隔离索引；不构成完整威胁模型。
