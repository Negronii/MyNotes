# 前端架构怎样划分呈现、交互和数据所有权？

以下沿用合成的页面编辑器案例：画布显示文档树，检查器编辑当前节点属性，工具栏新增组件，预览页呈现访客看到的页面。如果各处各存一份节点数据，拖动或重命名就可能让它们失步。架构应先说明每份状态由谁拥有、哪些模块能发出修改，再决定组件怎样拆分或代码如何部署。

~~~mermaid
flowchart TD
    Select["选择节点"] --> Session["编辑会话：selectedId / dragPreview"]
    Drag["拖动中的候选位置"] --> Session
    Session --> CanvasPreview["画布显示选中和拖动预览"]
    Session --> Inspector["检查器显示当前节点属性"]
    Commit["确认属性修改或放下排序"] --> Intent["命令表达已提交的编辑"]
    Intent --> Owner["文档状态所有者"]
    Owner --> Revision["生成新的文档修订"]
    Revision --> Canvas["画布读取新文档"]
    Revision --> Inspector
    Revision --> Preview["预览器读取同一修订"]
~~~

文档节点属于可保存页面内容；当前选中项、拖动状态和面板属于编辑会话；焦点和输入光标等短暂状态通常留在组件内部。不是所有状态都要进全局状态存储，但每种状态都应有清楚的所有者。

## 单向数据流让修改原因可追踪

unidirectional data flow（单向数据流）让状态所有者把当前数据传给视图，视图通过事件或命令请求变化。检查器不私下改写画布节点副本，而是发出“把 `heading-1` 的 `text` 改成‘欢迎’”这样的意图。

以下沿用同一个修订 12 的页面案例；完整文档与会话输入见[修订 12 的文档与编辑会话数据](low-code-editor-data-model.md#文档树和编辑会话记录不同事实)，可运行命令代码也在那里。选择、拖动预览和已提交修改走不同路径：

| 事件 | 编辑会话 | 文档修订 |
|---|---|---|
| 选中 `heading-1` | `selectedId` 设为 `heading-1` | `revision` 仍为 12，文本仍是“首页” |
| 在检查器确认标题改为“欢迎” | `selectedId` 仍为 `heading-1` | 所有者校验后产生 `revision` 13 |
| 把 `heading-1` 拖到 `button-1` 后的预览 | `dragPreview` 记录候选位置 | `revision` 仍为 13，节点顺序不变 |
| 在画布放下并确认排序 | 清除 `dragPreview` | 独立命令产生 `revision` 14，`rootIds` 变为 `['button-1', 'heading-1']` |

所以拖动中的每个鼠标移动都不需要写入可保存文档；只有放下并接受排序变更时才提交文档命令。React 官方状态共享指南用“将共享状态提升到最近共同父级”解释这种所有权；其他框架可以用不同机制实现同样约束。经典 Flux 模型让 action（动作）经过 dispatcher（分发器）到 store（状态存储），再由 store 通知 view（视图）；其他状态库采用不同契约，重点是让状态变化及其原因可追踪。

## 组件与分层分别解决什么问题？

**component-based architecture（基于组件的架构）**按可复用视图和交互边界拆分 user interface（用户界面，UI）。`Canvas` 呈现画布，`Inspector` 编辑属性，`NodeView` 呈现一种节点类型。组件接口应写明输入输出：数据与回调怎样传入，选择、修改、删除等意图怎样传出。不是每个组件都要持有状态、调用服务并执行副作用。

分层则按职责分开状态管理、领域命令、持久化适配和视图。小编辑器可能只需要几个清楚模块；只有一层确实承载独立规则或依赖边界时，再拆成独立包或服务。为每个组件都造“控制器—服务—仓库”容易使跟踪简单操作变慢。

文档树顺序也不等于最终绘制顺序。浏览器布局和 CSS stacking context（堆叠上下文）参与绘制；若编辑器显示精确图层，需要把节点顺序、定位和堆叠上下文规则一并纳入模型。

## 何时微前端有实际收益？

**micro-frontend（微前端）**按业务或团队边界拆分可独立开发、集成、发布的部分。可以构建时组合、运行时加载、用 iframe 或 Web Components；隔离、依赖共享、导航和样式方式各不相同。

页面编辑器的检查器与画布若由同一团队同步发布，放在一个模块化应用更简单。若多支独立团队分别负责组件库、编辑器和资产管理，且确实需要独立发布，微前端可能减少协调阻塞。此时仍要定义路由、权限、设计系统、可访问性、错误处理、遥测、依赖版本和加载失败处理，否则集成成本会变成运行时故障。

微前端是组织与部署边界，不是把普通组件拆成多个项目的同义词。若主要问题是共享状态或数据流不清，先解决状态所有权通常更直接。

**延伸阅读：**[设计原则怎样帮助定位真实变化边界？](software-design-principles.md)、[页面编辑器何时需要设计模式？](design-patterns-in-practice.md)、[怎样建模页面文档、编辑会话和发布快照？](low-code-editor-data-model.md)。

> [!info]- 来源
> - 组件间共享状态的所有权：[React：Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)。
> - 堆叠上下文内的 CSS 绘制顺序：[W3C CSS 2.2, Appendix E](https://www.w3.org/TR/CSS22/zindex.html)。
> - 微前端的团队发布边界和集成权衡：[Martin Fowler, Micro Frontends](https://martinfowler.com/articles/micro-frontends.html)。
