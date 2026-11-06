# When should an AI application use a hosted API, self-hosting, edge, or hybrid deployment? / AI 应用何时应选托管 API、自托管、端侧或混合部署？

**Core explanation / 核心解释：** Compare deployment patterns against the same workload, task-quality bar, data boundary, peak demand, and operational requirement. Hosted inference can reduce serving work; self-hosting increases control while transferring capacity and on-call responsibility to the team; edge and hybrid patterns answer distinct device or data-boundary needs. No deployment label by itself establishes lower total cost or better privacy. / 应在同一工作负载、任务质量门槛、数据边界、峰值需求和运维要求下比较部署方式。托管推理可以减少服务维护；自托管增加控制力，也把容量和 on-call 责任交给团队；端侧和混合部署分别回应设备或数据边界需求。仅凭部署名称不能证明总成本更低或隐私更好。

**Key terms / 关键术语：** hosted API / 托管 API；self-hosted / 自托管；edge / 端侧；hybrid / 混合部署；total cost of ownership / 总拥有成本。

## API, self-hosted, edge, or hybrid — how do you pick a deployment pattern? / 托管 API、自托管、端侧或混合部署——如何选择？

| Pattern | Useful when | Costs and constraints |
|---|---|---|
| **Hosted API / 托管 API** | Managed inference and quick iteration fit the task. | Review provider terms, model lifecycle, feature support, rate limits, availability, and per-use cost. |
| **Self-hosted / 自托管** | Control over serving location, model version, and infrastructure is a real requirement. | The team owns capacity, scaling, security updates, model serving, observability, and on-call response. |
| **Edge / 端侧** | Offline use, local latency, or device-level data handling matters. | Compute, battery, memory, device coverage, updates, and supported model size constrain the design. |
| **Hybrid / 混合部署** | Distinct workloads need different data or serving boundaries. | Routing and duplicated operations add complexity; define fallback and consistent policy behavior. |

## How should total cost and operational fit be compared? / 如何比较总成本和运维适配？

A useful estimate is:

$$
\text{total cost} = \text{inference} + \text{compute and storage} + \text{engineering and operations} + \text{evaluation and controls}
$$

There is no universal spend threshold for switching to self-hosting. Estimate with actual traffic, peak demand, staffing, quality requirements, and the full operating burden. Edge and hybrid choices likewise depend on device and data constraints, not just a latency label.

The choice also depends on which model candidates meet the task contract. See [Model Selection and Ecosystem / 模型选择与生态](../foundations/model-selection-and-ecosystem.md) for comparing task quality, modality, deployment constraints, and measured routing. For the run identity and recovery behavior that should remain stable across deployment patterns, see [AI Application Architecture / AI 应用架构](ai-application-architecture.md).

For self-hosting, estimate the peak number and length of active sequences and then measure fit on the intended hardware. [GPU serving capacity / GPU 推理容量](llm-serving-and-kv-cache.md) shows how to size KV memory and compare batching under a latency target.

**Source boundary / 来源边界：** This note summarizes the deployment comparison already present in the AI Application Architecture source. Provider features, terms, prices, capacity, and availability are time- and workload-specific; verify the exact provider or serving stack when making a current deployment decision. It does not make a universal cost or privacy ranking.
