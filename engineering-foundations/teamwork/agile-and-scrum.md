# Scrum 怎样让团队检查并调整工作？

假设团队正在开发页面编辑器，目标是让用户创建内容并安全发布。整个产品方向可能要数月才能实现，一个 Sprint（冲刺周期）只能完成其中一部分。因此团队要反复判断：手上的工作是否仍有价值，遇到阻碍时是否要调整计划。本章用这个案例说明 Scrum 怎样安排这种检查与调整。

Agile（敏捷）是一组强调协作、可用软件、客户合作和响应变化的价值观与原则；Scrum 是用于复杂工作的轻量框架，规定团队职责、事件、工件和承诺。框架中的目标、工件和完成定义（下文逐一介绍）共同给出方向与质量底线。Scrum 提供的是定期检查、及时调整的节奏，它本身不保证估算准确、交付质量或用户价值。

## 敏捷价值观不是一套固定流程

《敏捷软件开发宣言》强调四组价值：个体与互动高于流程与工具、可工作的软件高于详尽文档、客户合作高于合同谈判、响应变化高于遵循计划。宣言明确说右侧内容仍有价值，只是左侧更受重视；它并没有要求团队放弃文档、计划、流程或合同。宣言附带的十二条原则还强调可持续的开发节奏、持续追求技术卓越、保持简洁和定期反思。

因此，把敏捷理解成“不做计划”是误读：敏捷要求计划随反馈持续调整，而不是定下后不再检查。文档、验证记录和合规证据同样可以服务于快速而可靠的反馈。Scrum 是落实这些价值观的一种具体框架，下面从它的职责和工件讲起。

## Scrum 用目标和工件建立透明度

**Scrum Team（Scrum 团队）**包含 **Product Owner（产品负责人）**、**Scrum Master（Scrum 引导者）**和 **Developers（开发者）**三类职责。它们描述的是责任，不必对应固定职位。Product Owner 负责最大化产品价值并管理 Product Backlog（产品待办列表），可以把具体的整理工作交给别人，但仍对结果负责；Scrum Master 帮助团队按 Scrum 运作、提升有效性并协助解除障碍；Developers 负责创建可用增量、维护 Sprint Backlog 计划并达到 Definition of Done。

Scrum 有三个工件，每个工件对应一项承诺，承诺说明这个工件朝什么目标或按什么标准衡量：

| 工件 | 对应承诺 | 页面编辑器案例中的作用 |
|---|---|---|
| Product Backlog（产品待办列表） | Product Goal（产品目标） | 持续排序创建、编辑、预览和发布的工作，朝产品目标前进。 |
| Sprint Backlog（Sprint 待办列表） | Sprint Goal（Sprint 目标） | 包含目标、所选工作和 Developers 的执行计划；计划可随学习调整。 |
| Increment（增量） | Definition of Done（完成定义） | 与以往增量集成、满足产品质量标准的一步可用成果。 |

例如，Product Goal 可以是“让非开发者安全创建并发布简单页面”。一个 Sprint Goal 可以是“访客能查看含标题的公开发布页面”。这个产品的 Definition of Done 包含权限验证：公开页面可以访问，草稿和受限内容拒绝未授权访问。团队可将内容存储、页面预览和发布校验作为候选工作；只有满足完成定义并集成到产品中的部分才算 Increment。一个 Sprint 可以产出多个 Increment，前提是每一个都满足 Definition of Done。

## Sprint 事件让计划贴近现实

有了目标和工件，还需要固定的时间点去检查它们。Sprint 本身是一个长度固定、不超过一个月的事件，它容纳另外四个正式事件——Sprint Planning、Daily Scrum、Sprint Review、Sprint Retrospective——以及期间的全部开发工作。Scrum Guide 并未规定两周一轮；团队应选择既能稳定获得反馈、又不会拖慢调整的长度。

Sprint Planning（Sprint 计划会）回答三个问题：这个 Sprint 为什么有价值、可以做什么、怎样完成。全队共同定义 Sprint Goal；Developers 与 Product Owner 讨论后选择本轮纳入的 Product Backlog 项，并制定执行计划。Sprint 开始后，Developers 可以根据新信息调整 Sprint Backlog，必要时与 Product Owner 重新澄清和协商范围，目的是保住 Sprint Goal。

Daily Scrum（每日站会）是 Sprint 每个工作日举行的 15 分钟事件，供 Developers 检查离 Sprint Goal 还有多远并调整计划。形式由 Developers 自定，产出是接下来一天可执行的计划；它不要求每人轮流向主管汇报“昨天做了什么、今天做什么、有什么阻碍”。

在页面编辑器案例中，开发者发现公开页面已经能显示标题，但未登录访客也能打开草稿。Daily Scrum 让大家及时看到这个问题，并调整后续计划：先补上权限校验，再一起复测“公开页面可访问”和“草稿被拒绝”。两项都通过后，这部分工作才算形成可用成果。

~~~mermaid
flowchart TD
    G["Sprint Goal<br/>访客可查看<br/>公开页面"] --> W["执行计划<br/>构建与验证"]
    W --> D["Daily Scrum<br/>检查进展"]
    D -->|调整后续计划| W
    W --> I["可用 Increment<br/>满足完成定义"]
    I --> U["按需发布"]
~~~


Sprint Review（Sprint 评审）是团队与利益相关者一起检查成果、讨论环境变化、共同决定下一步的工作会议。它不是发布审批关卡：满足 Definition of Done 的增量可以按产品需要在 Review 之前就发布。Sprint Retrospective（Sprint 回顾）则检查人员协作、流程、工具和质量，挑出能落地的改进。

Sprint 临近结束时先开 Review，检查产品和环境；再开 Retrospective，检查工作方式，并以此结束本轮 Sprint。两者给下一轮 Planning 提供不同方面的反馈。在本例中，权限修复已通过两项复测、满足完成定义并集成到产品；到了 Review，利益相关者试用页面编辑器后提出手机预览需求，Product Owner 据此调整待办优先级。在 Retrospective 中，团队发现权限验证安排得太晚，决定下一轮开发新发布功能时更早检查“允许访问”和“拒绝访问”两种情况；质量要求保持不变，改进的是发现问题的时机。

~~~mermaid
flowchart TD
    R["Sprint Review<br/>检查产品结果"] --> B["按需调整<br/>Product Backlog"]
    R -->|随后| T["Sprint Retrospective<br/>检查工作方式"]
    T --> M["选定改进"]
    B --> P["下一轮 Sprint Planning"]
    M --> P
~~~


## 遇到变化时，保护目标并重谈范围

回到 Daily Scrum 发现的草稿越权问题：它说明当时的成果还没有达到 Definition of Done。Developers 先确认影响范围，向 Product Owner 说明修复和复测需要多少工作，再一起决定是否推迟非核心的样式微调，从而在不降低质量要求的前提下实现 Sprint Goal。也就是说，可以重谈的是范围，不是完成定义。若目标本身已失去价值，只有 Product Owner 有权取消 Sprint。

对照工件和事件的本来用途，可以识别几种常见误用：

- 把 Sprint Backlog 当作冻结合同，会让计划无法反映实际学习。
- 把 Daily Scrum 当作人员考核汇报，会挤掉团队协作和适应计划的机会。
- 把 Sprint Review 当作单向演示或发布审批，会削弱共同检查和调整的目的。
- 只保留仪式名称、忽略透明、检查和适应，会失去框架的工作机制。

决定使用 Scrum，就按它的定义运行并检查效果；如果它不适合，也可以选择其他与产品复杂度、反馈周期和约束相匹配的协作方式。

> [!info]- 来源
> - Scrum Guides 官方下载页在 2026-11-11 仍将 2020 年 11 月版列为当前版本；本文按其职责、事件、工件和承诺定义：[The Scrum Guide](https://scrumguides.org/scrum-guide.html)，[官方版本下载页](https://scrumguides.org/download.html)。
> - 敏捷价值观及左右两侧的关系：[Manifesto for Agile Software Development](https://agilemanifesto.org/)。
