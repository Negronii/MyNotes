# RAG, Evaluation, and Production Safety Audit / RAG、评估与生产安全审计

本批三篇 AI 工程正文已完成全文、关键公开来源与双语表达审查，并通过最终内容审查；加上首批六篇，合计 62 篇中的 9 篇完成全文深审。审计范围仅限下列正文，不代表 AI 工程域或知识库其余内容已完成审查。

## 修订重点与公开证据

| 正文 | 修订重点 | 代表性公开依据 |
|---|---|---|
| [RAG Architecture and Implementation / 检索增强生成](../ai-engineering/rag/rag-architecture-and-implementation.md) | 分清语料处理、检索、证据组装与生成；把分块、召回和重排配置作为任务参数评估；说明检索证据、授权与回答正确性各自的边界。 | [DPR](https://arxiv.org/abs/2004.04906)、[BEIR](https://arxiv.org/abs/2104.08663)、[HyDE](https://arxiv.org/abs/2212.10496)、[OpenAI retrieval guide](https://developers.openai.com/api/docs/guides/retrieval)。 |
| [LLM Evaluation / 大语言模型评估方法](../ai-engineering/evaluation/llm-evaluation-methods.md) | 按任务定义成功条件与分母；区分检索、给定上下文后的生成及端到端结果；说明模型评委、人工一致性和公共基准各自能提供及不能提供的证据。 | [RAGAS](https://arxiv.org/abs/2309.15217)、[ARES](https://arxiv.org/abs/2311.09476)、[MT-Bench](https://arxiv.org/abs/2306.05685)、[HELM](https://arxiv.org/abs/2211.09110)。 |
| [AI Safety in Production / 生产环境 AI 安全](../ai-engineering/safety/ai-safety-in-production.md) | 将模型请求与应用授权分开；说明内容护栏、逐次授权、输出校验和沙箱的职责边界；按条件讨论持久记忆风险，并保留模型循环外的停止与人工接管路径。也保留无工具场景的内容审核、敏感输出脱敏和合成验证例。 | [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)、[OWASP LLM01:2026](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM01_PromptInjection.md)、[OWASP LLM03:2026](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md)、[OpenAI sandbox guide](https://developers.openai.com/api/docs/guides/agents/sandboxes)。 |

这些是正文引用的代表性公开来源，结论受各自研究、版本和适用范围限制；它们不构成所有系统的统一配置或质量保证。正文按任务、模型、语料、权限和部署环境限定结论。内容与来源审查已通过，文档和生成链接检查已完成。

## 核验范围与限制

已重新生成三份连续阅读文档；`python3 maintenance/build-reading-docs.py --check` 验证了领域地图、源文链接、生成链接与输出。两条旧 section fragment 已改为文件级相关链接；当前活跃 Markdown 中未发现指向这两条旧 fragment 的剩余入链。2026-10-15 在 Obsidian Reading Mode 定向抽查了 RAG 的三个相似度行内公式、RRF 块公式、代码、表格及中文可读性；连续阅读稿中的 RAG→Evaluation 导航和 review/index 第 5 项→RAG 正文的两次真实点击均通过。这是指定片段抽查，不是全库逐节原生验证，也不覆盖 Safety 全文的原生呈现。资料审查不代表复现了论文实验、运行了部署基准或完成了生产环境渗透测试。
