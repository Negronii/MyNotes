# How do you retrieve and use authorized external evidence in a grounded answer? / 怎样检索并使用经过授权的外部证据生成有依据的回答？

**Short answer / 简答** — Define what sources the caller may use, retrieve from the eligible corpus, and give the model a small set of traceable passages. Validate each material claim against those passages and abstain when the evidence is missing or conflicting. Measure candidate recall, evidence selection, and final answers separately so you can fix the stage that failed. / 先确定调用者能使用哪些来源，再从有资格的文档中检索，把少量可追溯的证据交给模型。用原文核对关键主张，证据不足或冲突时说明无法确定。分别衡量候选召回、证据组装和最终回答，才能知道该修哪一层。

## When to use retrieval, long context, or fine-tuning / 如何选择检索、长上下文或微调

These techniques solve different constraints and can be combined:

| Approach | Useful when | Main tradeoff |
|---|---|---|
| **RAG / 检索增强** | The application needs to select evidence from a source that is larger than one prompt, changes over time, or has source-level access rules. | Adds ingestion/synchronization and retrieval work. Retrieval can miss, return stale or conflicting material, or select content the generator does not use well. |
| **Long context / 长上下文** | The relevant material can be supplied together and the task benefits from reasoning across that material without a separate search step. | The model must still find and use the relevant parts. Context length, position effects, and input-token cost depend on the model and workload. |
| **Fine-tuning / 微调** | Repeated examples can teach a desired response pattern, task behavior, or format. | It does not by itself provide a reliable, current source of external facts. Use retrieval as well when answers must cite or reflect a maintained corpus. |

There is no universal token-count cutoff. Compare the methods on representative questions, including required evidence, source updates and permissions, answer quality, end-to-end latency, and cost. In one EMNLP 2024 comparison, long-context models had higher average performance when sufficiently resourced, while RAG cost less in that evaluated setting; this result is not a general ranking of all systems. Long-context models can also be position-sensitive on tested tasks. [Li et al.](https://arxiv.org/abs/2407.16833), [Liu et al.](https://arxiv.org/abs/2307.03172)

## Pipeline / 检索增强生成的流程

Follow one synthetic question through the system. A caller asks “What is the cancellation window for a self-serve annual plan in the EU?” The authoritative current EU policy says 14 calendar days. The caller can read both the current EU and US policies. A withdrawn EU revision used 30 days, and another tenant’s contract is outside the caller’s scope.

~~~mermaid
flowchart LR
    Source["Source document and version"] --> Index["Parse sections and index eligible passages"]
    Caller["Caller and question"] --> Scope["Compute authorization and policy scope"]
    Index --> Candidates["Retrieve candidates"]
    Scope --> Candidates
    Candidates --> Evidence["Rank, verify and assemble evidence"]
    Evidence --> Model["Generate with passage IDs"]
    Model --> Check["Check claims and citations"]
    Check --> Output["Return supported answer or abstain"]
~~~

1. **Index / 建索引.** Parse by section, keeping text and structural context such as table headers, product scope, and exceptions. Store document ID, version or effective date, section or offsets, and policy metadata for each passage. Synchronize edits, deletions, and permission changes. If revocation must take effect before the index catches up, recheck access against the authoritative policy before releasing text.
2. **Retrieve / 召回.** Compute the caller's authorized scope in trusted code. Apply authorization and effective-date constraints in each retrieval branch. Test which of the returned policies actually applies to the requested region and plan. The withdrawn revision and other tenant’s contract cannot become evidence. Search the eligible passages with a lexical baseline, a dense index when paraphrase matters, or both if evaluation shows the methods complement one another.
3. **Rank and assemble / 重排与组装.** Fuse rankings if using multiple retrievers, then consider a cross-encoder if useful candidates are being ranked below less applicable ones and evaluation shows a gain. Keep the most relevant passages with their source IDs and exact scope. If a chunk points at a parent section, check the parent’s access and version before adding it. The EU section gets priority over a broadly related billing FAQ. Fit the evidence to the token budget and preserve the qualification “self-serve annual.”
4. **Generate and check / 生成与核对.** Ask for an answer and passage IDs, then confirm that the cited passage really supports “14 calendar days” for the stated region and plan. An ID copied from the prompt is not proof of support. If only the US policy is present, report insufficient applicable evidence. When trusted passages conflict, apply a predefined authority/version rule or surface the conflict.

A missing passage at step 2 cannot be recovered by reranking at step 3. A retrieved passage can still be dropped by context assembly. Evidence that reaches the model can still be misread. Keeping the authorized candidate IDs, selected passage IDs, and output claims distinct makes those failures diagnosable. Treat the passages as data. Their text grants no additional permissions or tool authority.

## Embeddings and similarity / 向量表示与相似度

An embedding maps text to a vector for retrieval. Query and document encodings must follow a **compatible encoding contract / 兼容的编码契约**: their vector dimensions and learned space must support comparison, and each model’s query/document input format must be respected. This does not require identical encoder weights. Dense Passage Retrieval (DPR), for example, uses separate question and passage encoders. [Karpukhin et al.](https://arxiv.org/abs/2004.04906)

Changing document-side encoding, output dimensions, normalization, or preprocessing may require re-embedding or migrating the affected document vectors if they no longer meet the query/document contract. A query-side change alone does not necessarily require rebuilding the document index, but its compatibility and retrieval quality must be re-evaluated. Model choice should account for the language and task, query/document format, deployment and privacy constraints, input limits, latency, price, and performance on the target corpus. Avoid treating a model list or benchmark ranking as a permanent recommendation.

Common similarity measures are:

| Measure | Formula | Interpretation |
|---|---|---|
| **Cosine similarity / 余弦相似度** | $\frac{A \cdot B}{\lVert A \rVert \lVert B \rVert}$ | Compares vector direction and is invariant to vector magnitude. |
| **Dot product / 点积** | $A \cdot B$ | Depends on both direction and magnitude unless vectors are normalized. |
| **Euclidean distance / 欧氏距离** | $\lVert A-B \rVert_2$ | Measures distance; smaller values indicate closer vectors. |

The metric must match the model’s representation and the vector index configuration. For OpenAI’s normalized embeddings, cosine similarity and dot product produce the same ranking, and Euclidean distance also produces identical rankings; this equivalence should not be assumed for arbitrary embeddings. [OpenAI embeddings guide](https://developers.openai.com/api/docs/guides/embeddings)

## Chunking / 文档分块

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

## Dense, sparse, and hybrid retrieval / 稠密、稀疏与混合检索

**Dense retrieval / 稠密检索** embeds the query and chunks, then ranks chunks by vector similarity. It can match related phrasing even when wording differs, depending on the model and task. It can still miss exact identifiers, rare names, or relevant evidence.

**Sparse retrieval / 稀疏检索** ranks using lexical features. BM25 is a common term-based retriever and can be useful for exact strings such as error codes, product identifiers, and names. It may miss paraphrases whose vocabulary differs from the document.

**Hybrid retrieval / 混合检索** combines dense and sparse candidates or rankings. The methods can complement one another, but hybrid retrieval is not a universal default. A heterogeneous retrieval benchmark found BM25 to be a robust baseline; it also found that reranking and late-interaction systems performed strongly on average at higher computational cost. Results vary across tasks, so compare retrieval methods on the application’s queries. [BEIR](https://arxiv.org/abs/2104.08663)

**Reciprocal rank fusion / 倒数排名融合（RRF）** combines ordered lists. For a candidate $d$ with rank $r_i(d)$ in list $i$,

$$
\operatorname{RRF}(d)=\sum_i \frac{1}{k+r_i(d)}.
$$

A candidate contributes only from the lists that return it. In the example, lexical retrieval returns US, EU, FAQ and dense retrieval returns EU, Billing, US. With an illustrative $k=60$, EU scores $1/62+1/61$, above US at $1/61+1/63$. Fusion uses positions without calibrating a raw BM25 score against a cosine score. It sees only the returned candidate windows. Tune candidate depth, fusion and reranking on the same queries. [Cormack, Clarke & Büttcher](https://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf) · [Elasticsearch RRF reference](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)

A 2026 financial QA preprint compared ten approaches on text and tables. Its hybrid retrieval with cross-encoder reranking led its retrieval comparison, and BM25 was stronger than the tested dense baseline. That makes a good reason to test hybrid retrieval on mixed text and numeric questions. The main comparison indexed whole documents, so it does not settle passage size or performance on another corpus. [From BM25 to Corrective RAG, v1, §§III–IV](https://arxiv.org/html/2604.01733v1)

## Reranking / 重排

A **bi-encoder / 双编码器** independently encodes a query and each document, allowing document vectors to be indexed and searched efficiently. A **cross-encoder / 交叉编码器** processes a query-document pair together and returns a relevance score. Joint input permits a richer pairwise comparison, but scoring many candidates costs more than a vector lookup. Retrieval-plus-reranking is therefore a **recall then precision** pattern: retrieval proposes candidates, and reranking changes their order.

For example, a synthetic question about a sample policy might retrieve a broad candidate set, rerank those chunks against the question, then pass only a few supported passages to generation. Candidate depth and final context size are workload parameters. If evidence is not among the retrieved candidates, the reranker cannot add it. If reranking keeps the entire candidate set (candidate count equals final returned count), reordering alone does not change set-based precision@k, though it can affect rank-sensitive metrics and the order in which evidence reaches generation. Compare quality and latency across candidate depths instead of assuming a particular top-k is best. BEIR found strong average zero-shot performance for reranking architectures in its evaluated benchmark, with higher computational cost. [BEIR](https://arxiv.org/abs/2104.08663)

## Retrieval upgrades / 检索增强策略

Use these techniques to address a diagnosed failure, and evaluate each on the affected query set before combining them.

### Query transformation / 查询改写

Rewrite or expand a query when the user’s wording does not align with the corpus vocabulary or when a compound request needs clearer subqueries. Query expansion can run several variants and merge results. Rewriting can also alter the user’s intent, so retain the original query and compare retrieval outcomes.

### HyDE (Hypothetical Document Embeddings) / 假设文档嵌入

HyDE asks a language model to generate a hypothetical document in response to a query, embeds that hypothetical text, and uses the vector to retrieve real corpus documents. The generated document is a **retrieval intermediary, not answer evidence**; the original paper notes it may contain false details. HyDE was proposed for zero-shot dense retrieval when relevance labels are unavailable. It is not based on a general rule that short queries embed poorly near long passages. [Gao et al.](https://arxiv.org/abs/2212.10496)

### Parent-child retrieval / 父子分块检索

Embed and retrieve child passages, then return their parent section as context. This can recover nearby definitions or qualifications that are useful to interpret the child evidence. Deduplicate parent sections and keep the final context within a budget; evaluate whether the broader passages help the query set.

### Multi-step retrieval / 多步检索

For a question whose answer requires evidence from more than one source, retrieve an initial set, identify the unresolved relation or sub-question, and retrieve again. This can support multi-hop questions, but it adds retrieval or generation work. Stop when the needed evidence is present or when the remaining uncertainty should be reported rather than hidden by another search.

## Operations, evaluation, and failure diagnosis / 运行边界、评估与故障定位

### Access, freshness, and trust boundaries / 权限、新鲜度与信任边界

RAG does not make a corpus private. Compute the caller’s permissions in trusted application code and enforce them in the retrieval/data-access layer before evidence reaches the model. Metadata filters can express attributes such as tenant, region, source, or date, but correctness of the policy and its enforcement belongs to the application. Track document identity and version so updates, deletions, and permission revocations do not leave stale chunks available. The index is only as fresh as its synchronization and processing path. [OWASP LLM08:2025](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/), [OpenAI retrieval guide](https://developers.openai.com/api/docs/guides/retrieval)

A logical authorization filter and the search engine’s scan order are different concerns. In pgvector, a SQL `WHERE` condition still gates what rows can be returned, but approximate HNSW or IVFFlat may scan candidates before applying that filter. With selective filters, measure authorized recall and the count of eligible rows. If needed, test iterative scans, a scoped index or partition, or exact search over a small authorized subset. Never relax the policy to fill a candidate quota. [pgvector filtering and iterative scans](https://github.com/pgvector/pgvector#filtering)

Treat all retrieved text as untrusted content. A document can contain direct or indirect instructions that influence the model. Delimiters and prompts may reduce confusion, but they do not guarantee protection. Do not let a retrieved passage authorize a data access or tool action; enforce permissions and validate actions outside the model. [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/). For more on prompt injection and application boundaries, see [AI Safety in Production / 生产环境中的 AI 安全](../safety/ai-safety-in-production.md).

### Evaluation / 评估

Measure retrieval and generation separately, then compare the complete system:

- **Candidate recall / 候选召回.** Label the source passages needed for each question and identify the version and caller. Recall@K is the share of those passages found in the first K candidates. MRR describes the rank of the first relevant candidate and cannot establish that a multi-part answer has every necessary passage.
- **Evidence and generation / 证据与生成.** Track which needed passages survive assembly. Then assess factual correctness, support for each claim and citation, and whether the answer abstains when the passage is missing or conflicting. RAGChecker illustrates claim-level decomposition for retrieval and generation diagnosis. [RAGChecker §§3–4](https://arxiv.org/abs/2408.08067)
- **System / 系统.** Track end-to-end latency and cost along with revocation and tenant-isolation regressions. Keep cases where the relevant-looking passage is unauthorized, expired, or for the wrong plan. Re-run the same cases across the lexical baseline, dense retrieval, hybrid fusion and reranking. Change one stage and retain the simplest configuration that meets the acceptance bar.

RAGAS and ARES illustrate multi-dimensional evaluation, including context relevance, answer faithfulness, and answer relevance; they are evaluation frameworks, not a complete universal score. Automated judges are useful signals and should be checked against representative human-reviewed examples. See [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md). [RAGAS](https://arxiv.org/abs/2309.15217), [ARES](https://arxiv.org/abs/2311.09476)

### Diagnose from evidence / 根据证据定位故障

| Symptom | Inspect | Possible next step |
|---|---|---|
| The source does not contain the needed fact, or the current version is missing. | Source coverage, parsing, synchronization, deletion/version state. | Fix source ingestion or freshness; if the evidence is unavailable, report that limitation. |
| The evidence exists but is absent from retrieved candidates. | Caller filters, query interpretation, chunk boundaries, embedding/lexical retrieval, candidate recall. | Correct scope or ingestion first; then compare retrieval and chunking choices on the failing queries. |
| A useful candidate is retrieved but absent from the prompt. | Reranker order, deduplication, context assembly, and truncation. | Adjust ranking or evidence selection and verify that citations still map to source passages. |
| Evidence is in the prompt, but the answer is unsupported or contradicts it. | Conflicting passages, prompt instructions, model output, citation support, and whether the question is answerable. | Test prompt/model/evidence changes against the same cases; do not infer a specific internal cause from the answer alone. |

A practical debugging loop is: inspect the source and authorized candidates; inspect what reached the model; check answer claims against those passages; then change one retrieval or generation factor and evaluate the same cases. More context can add missing evidence or add noise, so “retrieve more” is a hypothesis to test, not a universal fix. Long-context performance can also depend on where relevant information appears. [Liu et al.](https://arxiv.org/abs/2307.03172)

## What carries forward from the original RAG paper? / 原始 RAG 论文留下什么？

Lewis 等人的 RAG 把可更新的非参数记忆（non-parametric memory）与参数化生成器结合起来。论文使用 DPR 检索 Wikipedia 向量索引，以 BART 生成，把检索到的文档当作潜变量。**RAG-Sequence** 对每篇文档分别计算整条答案的概率，再按文档权重求和。**RAG-Token** 对每个输出位置先按文档求和，再沿序列相乘。每种方法都按输入做一次 top-K 检索。RAG-Token 在自己的候选窗口内逐位置计算，逐词元改变文档贡献不等于逐词元重新检索。论文在当时的三项开放域问答上报告了相对基线的提升。 [Lewis et al., arXiv v4, §§2.1–2.5、§4.1 与表 1](https://arxiv.org/html/2005.11401v4)

今天的应用通常可独立更换检索器与生成模型，在生成前按权限和问题组装证据，再单独评估回答。值得继承的是把可更新证据与模型参数分离，以及测量检索和生成如何互相影响。业务权限、文档版本、重排和逐条引用验收是生产系统要另外实现的边界。

## Related notes / 相关笔记

- [Context Engineering Principles / 上下文工程原则](../context/context-engineering-principles.md) explains context budgets and how placement can affect use of evidence.
- [Fine-tuning Strategies / 微调策略](../fine-tuning/fine-tuning-strategies.md) discusses adapting model behavior and combining it with external knowledge.
- [LLM Evaluation Methods / 大语言模型评估方法](../evaluation/llm-evaluation-methods.md) covers evaluation datasets, metrics, and review methods.
- [AI Safety in Production / 生产环境中的 AI 安全](../safety/ai-safety-in-production.md) covers prompt injection, permission boundaries, and runtime controls.
