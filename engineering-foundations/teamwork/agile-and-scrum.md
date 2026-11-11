# Scrum 怎样让团队检查并调整工作？

假设团队正在开发页面编辑器，目标是让用户创建内容并安全发布。产品方向可能需要数月才能实现，单个 Sprint（冲刺周期）只能完成其中一部分；团队需要不断判断工作是否仍有价值、遇到阻碍时是否要调整计划。

Agile（敏捷）是一组强调协作、可用软件、客户合作和响应变化的价值观与原则；Scrum 是用于复杂工作的轻量框架，规定团队职责、事件、工件和承诺。Product Goal（产品目标）、Product Backlog（产品待办列表）、Sprint Goal（Sprint 目标）、Sprint Backlog（Sprint 待办列表）、Increment（增量）与 Definition of Done（完成定义）在框架中共同提供方向与质量边界。框架创造检查与适应的节奏，但不会自动保证估算准确、交付质量或用户价值。

## 敏捷价值观不是一套固定流程

《敏捷软件开发宣言》强调四组价值：个体与互动高于流程与工具、可工作的软件高于详尽文档、客户合作高于合同谈判、响应变化高于遵循计划。右侧内容仍有价值；宣言表达的是左侧受到更高重视。它没有要求团队放弃文档、计划、流程或合同。十二条原则还提到可持续节奏、持续技术卓越、简洁与定期反思等做法。

把敏捷理解成“完全不做计划”会错过重点：计划应根据反馈持续调整，而不是一次承诺后就不再检查。文档、验证和法规证据也可以服务于快速而可靠的反馈。

## Scrum 用目标和工件建立透明度

**Scrum Team（Scrum 团队）**包含 **Product Owner（产品负责人）**、**Scrum Master（Scrum 引导者）**和 **Developers（开发者）**三类职责；它们是责任，不必对应固定职位。Product Owner 对产品价值和 Product Backlog 管理负责，可以委托待办列表的具体管理活动但仍对效果负责；Scrum Master 帮助团队按 Scrum 运作、提升有效性并协助解除障碍；Developers 负责创建可用增量、维护 Sprint Backlog 计划并达到 Definition of Done。

| 工件 | 对应承诺 | 页面编辑器案例中的作用 |
|---|---|---|
| Product Backlog（产品待办列表） | Product Goal（产品目标） | 持续排序创建、编辑、预览和发布的工作，朝产品目标前进。 |
| Sprint Backlog（Sprint 待办列表） | Sprint Goal（Sprint 目标） | 包含目标、所选工作和 Developers 的执行计划；计划可随学习调整。 |
| Increment（增量） | Definition of Done（完成定义） | 与以往增量集成、满足产品质量标准的一步可用成果。 |

例如，Product Goal 可以是“让非开发者安全创建并发布简单页面”。一个 Sprint Goal 可以是“访客能查看含标题的公开发布页面”。这个产品的 Definition of Done 包含权限验证：公开页面可以访问，草稿和受限内容拒绝未授权访问。团队可将内容存储、页面预览和发布校验作为候选工作；只有满足完成定义并整合到产品的部分才是 Increment。一轮 Sprint 中可以形成多个 Increment，只要每个都满足 Definition of Done 并集成到产品。

## Sprint 事件让计划贴近现实

Sprint 是一个月或更短的固定长度事件，包含 Sprint Planning、Daily Scrum、Sprint Review、Sprint Retrospective 和全部工作活动；Sprint 容纳其余四个正式事件。Scrum Guide 不规定两周的固定节奏；团队选择能形成稳定检查与反馈、又不拖慢调整的长度。

Sprint Planning（Sprint 计划）讨论为什么这个 Sprint 有价值、可以做什么、如何完成。全队共同定义 Sprint Goal；Developers 与 Product Owner 讨论后选择本轮纳入的 Product Backlog 项，并制定执行计划。进入 Sprint 后，Developers 可根据新信息调整 Sprint Backlog，并与 Product Owner 澄清和协商范围，以保护 Sprint Goal。

Daily Scrum（每日 Scrum）在 Sprint 的每个工作日举行，是 Developers 检查朝 Sprint Goal 的进展并调整计划的 15 分钟事件。Developers 自行选择形式，以形成下一天的可执行计划；不要求每个人向主管轮流汇报昨日、今日和阻碍。

在页面编辑器案例中，开发者发现公开页面已经能显示标题，但未登录访客也能打开草稿。Daily Scrum 让大家及时看见这个阻碍，并调整后续计划：先补权限校验，再同时复测“公开页面可访问”和“草稿被拒绝”。开发和验证可以持续形成可用成果。

~~~mermaid
flowchart TD
    G["Sprint Goal<br/>访客可查看<br/>公开页面"] --> W["执行计划<br/>构建与验证"]
    W --> D["Daily Scrum<br/>检查进展"]
    D -->|调整后续计划| W
    W --> I["可用 Increment<br/>满足完成定义"]
    I --> U["按需发布"]
~~~


Sprint Review（Sprint 评审）是团队与利益相关者检查结果、讨论环境变化并协作决定下一步的工作会话。它不是发布审批关卡；符合 Definition of Done 的增量可按产品需要在 Review 前发布。Sprint Retrospective（Sprint 回顾）检查人际协作、流程、工具与质量，挑选可落实的改进。

Sprint 临近结束时，Review 先检查产品结果与环境变化，Retrospective 随后检查工作方式并结束本轮 Sprint。两者为下一轮 Planning 提供不同的反馈。本例先通过两项权限复测、满足完成定义并将改动集成到产品；到了 Review，利益相关者试用页面编辑器后提出手机预览需求，Product Owner 据此调整待办优先级。在 Retrospective 中，团队发现权限验证安排得太晚，决定下一轮开发新发布功能时更早检查“允许访问”和“拒绝访问”两种情况；质量要求保持不变，改进的是发现问题的时机。

~~~mermaid
flowchart TD
    R["Sprint Review<br/>检查产品结果"] --> B["按需调整<br/>Product Backlog"]
    R -->|随后| T["Sprint Retrospective<br/>检查工作方式"]
    T --> M["选定改进"]
    B --> P["下一轮 Sprint Planning"]
    M --> P
~~~


## 遇到变化时，保护目标并重谈范围

前面的权限缺陷意味着成果尚未达到 Definition of Done。Developers 应先确认影响、向 Product Owner 说明修复与复测所需工作，再共同判断是否延后非核心样式微调，以在保持质量要求的前提下实现 Sprint Goal。修复后，两种权限结果都通过验证，页面才可以成为可用增量的一部分。若目标本身已失去价值，Product Owner 可取消 Sprint。

常见误区可从工件和事件的用途识别：

- 把 Sprint Backlog 当作冻结合同，会让计划无法反映实际学习。
- 把 Daily Scrum 当作人员考核汇报，会挤掉团队协作和适应计划的机会。
- 把 Sprint Review 当作单向演示或发布审批，会削弱共同检查和调整的目的。
- 只保留仪式名称、忽略透明、检查和适应，会失去框架的工作机制。

若使用 Scrum，应按其定义运行并检查结果；若不适合，也可采用其他匹配产品复杂度、反馈周期和约束的协作方式。

> [!info]- 来源
> - Scrum Guides 官方下载页在 2026-11-11 仍将 2020 年 11 月版列为当前版本；本文按其职责、事件、工件和承诺定义：[The Scrum Guide](https://scrumguides.org/scrum-guide.html)，[官方版本下载页](https://scrumguides.org/download.html)。
> - 敏捷价值观及左右两侧的关系：[Manifesto for Agile Software Development](https://agilemanifesto.org/)。
