# Scrum 怎样让团队检查并调整工作？

假设团队正在开发页面编辑器，目标是让用户创建内容并安全发布。产品方向可能需要数月才能实现，单个 Sprint（冲刺周期）只能完成其中一部分；团队需要不断判断工作是否仍有价值、遇到阻碍时是否要调整计划。

Agile（敏捷）是一组强调协作、可用软件、客户合作和响应变化的价值观与原则；Scrum 是用于复杂工作的轻量框架，规定团队职责、事件、工件和承诺。Product Goal（产品目标）、Product Backlog（产品待办列表）、Sprint Goal（Sprint 目标）、Sprint Backlog（Sprint 待办列表）、Increment（增量）与 Definition of Done（完成定义）在框架中共同提供方向与质量边界。框架创造检查与适应的节奏，但不会自动保证估算准确、交付质量或用户价值。

~~~mermaid
flowchart TD
    ProductGoal["Product Goal（产品目标）<br/>让非开发者安全创建并发布简单页面"] --> Backlog["有序的 Product Backlog（产品待办列表）"]
    Backlog --> Planning["Sprint Planning（Sprint 计划）<br/>为什么 / 做什么 / 怎样做"]
    Planning --> SprintGoal["Sprint Goal（Sprint 目标）<br/>访客能看到已发布标题页"]
    SprintGoal --> Work["Sprint Backlog（Sprint 待办列表）：所选工作与执行计划"]
    Work --> Daily["Daily Scrum（每日 Scrum）：检查进展并调整计划"]
    Daily --> Work
    Work --> Increment["符合 Definition of Done（完成定义）的可用 Increment（增量）"]
    Increment --> Review["Sprint Review（Sprint 评审）：检查结果并讨论下一步"]
    Review -->|产品方向与待办反馈| Backlog
    Review --> Retro["Sprint Retrospective（Sprint 回顾）：改进协作和质量"]
    Retro --> Planning
~~~

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

例如，Product Goal 可以是“让非开发者安全创建并发布简单页面”。一个 Sprint Goal 可以是“访客能看到包含标题的已发布页面”。团队可将存储节点、预览页面和最小校验作为候选工作；只有满足完成定义并整合到产品的部分才是 Increment。一轮 Sprint 中可以形成多个 Increment，只要每个都满足 Definition of Done 并集成到产品。

## Sprint 事件让计划贴近现实

Sprint 是一个月以内的固定长度事件，包含 Sprint Planning、Daily Scrum、Sprint Review、Sprint Retrospective 和全部工作活动；Sprint 容纳其余四个正式事件。Scrum Guide 不规定两周的固定节奏；团队选择能形成稳定检查与反馈、又不拖慢调整的长度。

Sprint Planning（Sprint 计划）讨论为什么这个 Sprint 有价值、可以做什么、如何完成。团队建立 Sprint Goal、选择适合的 Product Backlog 项，Developers 制定执行计划。进入 Sprint 后，Developers 可根据新信息调整 Sprint Backlog，并与 Product Owner 澄清和协商范围，以保护 Sprint Goal。

Daily Scrum（每日 Scrum）是 Developers 检查朝 Sprint Goal 的进展并调整计划的 15 分钟事件，不是每个人向主管轮流汇报昨日、今日和阻碍的固定格式。团队选择最能帮助协同工作的形式。

Sprint Review（Sprint 评审）是团队与利益相关者检查结果、讨论环境变化并协作决定下一步的工作会话。它不是发布审批关卡；符合 Definition of Done 的增量可按产品需要在 Review 前发布。Sprint Retrospective（Sprint 回顾）检查人际协作、流程、工具与质量，挑选可落实的改进。

## 遇到变化时，保护目标并重谈范围

若页面发布服务的权限校验失效，访客可能看到未授权内容，这会直接威胁“访客能看到已发布标题页”所要求的安全发布。Developers 应先确认影响、向 Product Owner 说明修复与复测所需工作，再共同判断是否延后非核心样式微调以保护 Sprint Goal。若目标本身已失去价值，Product Owner 可取消 Sprint，而不是要求团队继续假装原计划仍适用。

常见误区可从工件和事件的用途识别：

- 把 Sprint Backlog 当作冻结合同，会让计划无法反映实际学习。
- 把 Daily Scrum 当作人员考核汇报，会挤掉团队协作和适应计划的机会。
- 把 Sprint Review 当作单向演示或发布审批，会削弱共同检查和调整的目的。
- 只保留仪式名称、忽略透明、检查和适应，会失去框架的工作机制。

若使用 Scrum，应按其定义运行并检查结果；若不适合，也可采用其他匹配产品复杂度、反馈周期和约束的协作方式。

> [!info]- 来源
> - Scrum Guides 当前官方版本为 2020 年 11 月版；本文按其角色、事件、工件和承诺定义：[The Scrum Guide](https://scrumguides.org/scrum-guide.html)，[官方版本下载页](https://scrumguides.org/download.html)。
> - 敏捷价值观及左右两侧的关系：[Manifesto for Agile Software Development](https://agilemanifesto.org/)。
