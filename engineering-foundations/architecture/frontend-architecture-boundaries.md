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

## 怎样迁移微前端而不打断深链、身份与回退？

沿用一个合成的页面编辑器：文档 `assetId=42` 当前处于 `revision=12`，选中的节点是 `heading-1`。旧应用通过 `/editor/assets/42?panel=inspector&node=heading-1#canvas` 打开它，新入口使用 `/assets/42/edit?panel=inspector&node=heading-1#canvas`。路径和文档 ID 是本教学变体；页面文档与编辑会话状态仍按[编辑器数据模型](low-code-editor-data-model.md)的稳定节点 ID 和修订区分。`node=heading-1` 只是可恢复的界面选择，不会进入页面文档或修改 revision。新旧地址先并存，让旧书签、邮件链接和浏览器历史都有确定去向。

迁移时由同一个 shell（应用外壳）持有顶级路由、会话启动、公共导航与错误边界；路由注册表把旧路径交给 `EditorV1`，新路径先交给 `EditorV1`，再按用户 cohort（灰度分组）将一小部分流量映射至 `EditorV2`。两版可独立构建，但路由、参数和通用数据格式是容器与子应用之间的合同。路由决策须在挂载前作出：

| 地址或状态 | shell 的责任 | 子应用收到的输入 |
|---|---|---|
| 旧深链 `/editor/assets/42?panel=inspector&node=heading-1#canvas` | 迁移窗口内继续交给 V1；用户从页面主动打开新入口时才新增新路径 | `assetId=42`、`panel=inspector`、`node=heading-1`、`#canvas` |
| 新地址 `/assets/42/edit?panel=inspector&node=heading-1#canvas`，未进入 cohort | 路由仍由 `EditorV1` 处理，不让用户落入空白占位页 | 同一 `assetId` 与视图状态 |
| 同一新地址，进入 cohort | 动态加载 `EditorV2`，并显示加载或失败状态 | 同一 `assetId` 与视图状态，不另造一份身份 |
| 浏览器 Back / Forward | shell 独自响应 `popstate` 并重新匹配完整地址 | `panel` 和有效 `node` 从恢复的 URL 查询恢复；片段仍定位到 `#canvas` |

每个子应用只处理传给它的资源标识和视图状态，通过 shell 提供的 `navigate()` 或明确的同源链接请求跨边界导航。shell 是唯一的 history（历史记录）所有者，因此 V1/V2 不会各自安装互不知情的路由器、重复写 `pushState` 或抢先处理 Back。迁移窗口保留旧路由供旧书签与返回历史使用；用户从旧界面主动打开新入口时，shell 用 `pushState` 记录新路径，这样 Back 可回到原页面。若迁移窗口结束后需把旧路由作为别名改写到新路径，才用 `replaceState` 保留原有 query 与 fragment，避免用户按 Back 时在两个等价地址间循环。浏览器处理新地址的硬刷新请求时，静态宿主还须将已知前端路径回退到 shell HTML，同时仍把 `/api/` 请求交给 API 服务。

身份也由宿主边界明确归属。本例 shell 通过 `HttpOnly`、`Secure` 的同源会话 cookie 建立身份，给子应用 `assetId`、非敏感显示信息和受限的数据访问接口，不把访问令牌或会话凭据放入路由参数、DOM、共享状态广播或子应用的 prompt。V1 与 V2 都通过同源 API 读取 `/api/assets/42`；浏览器随请求带会话 cookie，服务端在每次读取和写入时验证当前主体是否能访问该资源。客户端允许显示哪个路由只决定可见页面，不能替代服务端资源鉴权。`node` 只在页面文档加载后与该 revision 的稳定节点 ID 对照；缺失或不存在的节点参数会清除选择并显示文档，而不是请求任意资源。若子应用部署到独立 origin（源），cookie、令牌和跨源身份方案要另外设计；不能假设同源会话自动跨域。

同一份页面文档以明确版本的 schema 交给 V1 和 V2。本轮只迁移入口，不修改文档字段或服务端数据协议，因此两版都能读取和写回 `revision=12` 的既有文档。若 V2 将来要写入新字段，只有在 V1 会原样保留未知字段、或迁移窗口的路由规则能保证旧版不会重新打开含新字段的数据时才可开放；仅仅让 V1 读入时忽略字段，不保证下一次保存时不会把它删掉。删除或重解释字段也要等 V1 不再负责读写。若当前 revision 仍是 12，V2 的未保存草稿不能只因它的动态 chunk 加载失败就被静默丢弃：在编辑开始前加载失败，shell 可以映射到 V1；编辑开始后若要切换实现，应先将草稿转换成共享会话格式或让用户留在当前编辑器处理，否则停止回退并保留草稿。服务端拒绝的未授权访问不应触发降级到另一个前端，避免把代码加载回退误当成授权绕过。

发布按路由逐步改变 owner：先让 shell 可加载两版并验证同一输入合同；再在限定 cohort 中把 `/assets/:assetId/edit` 分给 V2；确认直接深链与刷新、嵌套 query/fragment、V1↔V2 导航、Back/Forward、未授权资源拒绝、V2 chunk 加载失败和 V1 兼容读取都正确后才扩大分流。每个检查都对应一次可见状态变化，而不是只确认首页能挂载。若 V2 的加载率或错误率越过约定门槛，路由注册表将新地址恢复映射到 V1；保持该路径可用让已有书签和历史项继续打开旧实现。仍需保留两版 chunk 和向后兼容的数据合同，才可以在出现问题后真正回退，而不只是把 flag 改回去。

路由契约是微前端沟通的一种公开边界；改变 route schema 或版本映射时要与所有链接来源一起验收。实施过程借用[静态资源版本并存与入口回滚](../../frontend/tooling/build-tools.md)中的旧 chunk 保留规则；新旧服务端资源合同仍要遵循[HTTP API 的授权与条件更新契约](../backend/http-api-contracts.md)。

**延伸阅读：**[设计原则怎样帮助定位真实变化边界？](software-design-principles.md)、[页面编辑器何时需要设计模式？](design-patterns-in-practice.md)、[怎样建模页面文档、编辑会话和发布快照？](low-code-editor-data-model.md)。

> [!info]- 来源
> - 组件间共享状态的所有权：[React：Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)。
> - 堆叠上下文内的 CSS 绘制顺序：[W3C CSS 2.2, Appendix E](https://www.w3.org/TR/CSS22/zindex.html)。
> - 微前端的团队发布边界和集成权衡：[Martin Fowler, Micro Frontends](https://martinfowler.com/articles/micro-frontends.html)。
> - 路由作为容器与子应用之间的合同：[Martin Fowler, Micro Frontends, “Cross-application communication via routing”](https://martinfowler.com/articles/micro-frontends.html#Crossapplicationcommunicationviarouting)，核对日期 2026-11-09。
> - 同源历史写入、恢复与 `popstate`：[WHATWG HTML Standard, History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，持续更新规范，核对日期 2026-11-09。
