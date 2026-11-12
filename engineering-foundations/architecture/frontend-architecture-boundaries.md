# 前端架构怎样划分呈现、交互和数据所有权？

以一个合成的页面编辑器为例：资产 `42` 当前是 revision (修订) 12，`section-1` 下有标题 `heading-1` 和报名按钮 `button-1`。为看清树关系，本篇将两个组件放进一个合成分组节点；关键是稳定 ID (标识符)、父子关系与修订边界，而不是这个容器类型。画布显示文档树，检查器修改当前节点，编辑预览读取当前草稿，访客读取已发布页面。架构要回答三件事：哪份状态可保存、谁能提交文档变更、哪些视图消费同一份结果。保存草稿不会发布；发布服务只在编辑者明确请求后校验选定的已保存修订，通过后才切换公开快照。

| 状态 | 初始值 | 生命周期 | 所有者 |
|---|---|---|---|
| 页面文档 | `revision=12`、`rootIds=['section-1']`、`section-1.children=['heading-1','button-1']` | 可保存、可撤销、可作为预览输入 | 文档状态所有者 |
| 编辑会话 | `selectedId=null`、`openPanel='inspector'`、`dragPreview=null` | 当前编辑器会话；不进入页面文档 | 编辑会话状态所有者 |
| 组件局部状态 | 输入焦点、光标与尚未确认的输入缓冲 | 当前组件挂载期间 | 对应输入组件 |
| 公开页面 | 活动指针为 `r12`，指向已发布的不可变快照 | 多个草稿修订并存时仍保持原发布版 | 发布服务与快照存储 |

完整的节点对象、命令、撤销和发布代码见[怎样建模页面文档、编辑会话和发布快照？](low-code-editor-data-model.md)。下面先追一次编辑如何改变文档，再看已保存修订怎样成为公开页面，最后讨论组件、模块与部署边界。

## 单向数据流让修改原因可追踪

**unidirectional data flow (单向数据流)** 让状态所有者把当前数据交给视图，视图通过事件或命令请求变化。检查器不能私下改写自己保存的节点副本；它应发出“把 `heading-1` 的 `text` 改成‘欢迎’”这样的意图，由文档所有者检查并产生新修订。若命令未通过校验，错误返回给发起方，当前文档修订保持不变。

下图的实线表示提交与后续显示，虚线表示读取已有状态。每次只处理一个命令；先改标题得到修订 13，再确认排序得到修订 14，具体值在图后的表中展开。

~~~mermaid
flowchart TD
    Input["用户确认修改<br/>setText / move"] --> Owner["文档所有者<br/>校验命令"]
    Current["当前文档修订"] -.->|作为校验依据| Owner
    Owner -->|通过| New["提交新修订<br/>标题：12 → 13<br/>排序：13 → 14"]
    Owner -->|拒绝| Error["返回错误<br/>文档修订不变"]
    New --> Views["画布 / 检查器<br/>读取当前文档"]
    New --> Preview["编辑预览<br/>只读取当前文档"]
    Session["编辑会话<br/>selectedId<br/>dragPreview"] -.->|辅助界面显示| Views
~~~

同一个修订 12 案例中，选择、输入、拖动预览和已提交修改走不同路径：

| 用户动作 | 会话或组件状态 | 文档结果 |
|---|---|---|
| 选中 `heading-1` | `selectedId` 变成 `heading-1` | 仍为修订 12，标题还是“首页” |
| 在检查器输入但未确认 | 输入组件暂存 `textDraft='欢迎'`，光标留在组件中 | 仍为修订 12 |
| 确认标题文案 | 发出 `setText('heading-1', '欢迎')` 命令 | 所有者校验后提交修订 13 |
| 拖动标题越过按钮 | `dragPreview` 记录 `section-1` 内候选顺序 | 仍为修订 13，树顺序不变 |
| 在画布放下并确认 | 发出移动命令；成功后清除 `dragPreview` | 所有者提交修订 14，子节点顺序变成 `['button-1','heading-1']` |

鼠标移动只改变会话里的候选位置。只有放下后才把命令交给文档所有者，因此撤销历史和保存任务不会记录几十次无意义的指针坐标。画布和检查器随后都从修订 14 读取，而不是分别维护一份副本。撤销也由文档所有者处理；它恢复先前的内容，但仍产生一个新的单调递增修订号，详见数据模型章节。

React 的状态共享指南以“把要协调的状态移动到最近共同父组件”解释了同一所有权思路；它不意味着所有状态都要搬到一个全局对象。其他框架可用不同机制，只要选中项、草稿输入与已提交文档的持有者仍清楚可辨。若浏览器端只是草稿缓存，服务端在保存时还要检查当前修订或版本条件，避免较旧客户端覆盖较新的提交；这一步属于持久化合同，不应由视图自行假定成功。

**从草稿到公开页面。** 编辑者可以保存修订 14，访客此时仍读取活动快照 r12。只有编辑者另外请求发布该已保存修订，发布服务才开始校验；通过后生成不可变快照，再原子切换活动指针。校验拒绝时，已保存草稿和线上页面仍是两份不同状态。

~~~mermaid
flowchart TD
    Saved["已保存 r14<br/>活动快照 r12"] -->|编辑者明确请求发布| Gate{"发布校验"}
    Gate -->|通过| Snapshot["生成不可变快照<br/>r14"]
    Snapshot --> Switch["原子切换<br/>活动指针到 r14"]
    Switch --> Public["访客读取 r14"]
    Gate -->|拒绝| Keep["不切换指针<br/>访客仍读取 r12"]
~~~

## 组件与分层分别解决什么问题？

**component-based architecture (基于组件的架构)** 按可复用视图和交互边界拆分 user interface (用户界面，UI)。`Canvas` 呈现文档树，`Inspector` 编辑选中节点的属性，`NodeView` 呈现一种节点类型。组件接口应说明数据和回调怎样传入，以及选择、修改、删除等意图怎样传出。视图不因被拆成组件就自动得到文档所有权。

分层则按职责分开交互状态、文档命令、持久化适配和视图。这个合成编辑器可先用少数模块：会话控制器持有 `selectedId` 与 `dragPreview`；文档所有者接受命令、校验结构与业务规则、产生修订；存储适配器保存一个指定修订；视图读取会话和文档投影。只有某层确实承载独立规则或依赖边界，才值得拆成独立包或服务。为每个组件都造“控制器—服务—仓库”会增加跨层跳转，却未必减少变化范围。

文档树的逻辑顺序也不等于最终绘制顺序。浏览器会依 CSS stacking context (层叠上下文) 和定位规则绘制；编辑器若要提供“置顶”，必须说明改的是树的兄弟顺序、同一层叠上下文内的层级，还是更高层渲染模型。单独重排 `children` 不保证节点覆盖另一个不同层叠上下文中的元素。

## 何时微前端有实际收益？

**micro-frontend (微前端)** 把前端的一部分按业务或团队边界独立开发、集成和发布。可以在构建时组合、运行时加载，也可以用 iframe 或 Web Components；它们在隔离、依赖共享、导航和样式方面各有成本。

若画布、检查器和资产面板由同一团队一起发布，放在一个模块化应用通常更直接；当前主要问题若是两处各存节点副本，拆成微前端只会把同步问题推到跨应用通信。若组件库、页面编辑器和资产管理由不同团队负责，确有独立发布节奏且集成合同稳定，拆分才可能减少发布协调。与此同时，运行时集成会增加路由、深链、身份传递、样式隔离、依赖版本、可访问性、故障处理和监控等合同；这些成本必须由独立发布带来的收益抵消。

微前端是组织与部署边界，不是把普通组件拆成多个项目的同义词。先解决文档状态由谁持有，再判断是否存在团队自治、独立部署或渐进迁移的实际需求。

## 怎样迁移微前端而不打断深链、身份与回退？

现在从单应用切换到另一种合成部署情境：资产 42 当前仍为修订 12，旧入口 `/editor/assets/42?panel=inspector&node=heading-1#canvas` 要逐步迁到 `/assets/42/edit?panel=inspector&node=heading-1#canvas`。文档字段不变；`node=heading-1` 是可恢复的界面选择，不是文档内容，也不会推进 `revision`。新旧地址先并存，避免旧书签和历史项没有去向。

shell (应用外壳) 可以负责顶级路由、公共导航和错误边界。路由注册表先把两种地址都交给 `EditorV1`，再让 cohort (灰度分组) 中的一小部分用户把新地址路由到 `EditorV2`。这是一个合同选择：也可以让子应用共享同一个路由器或由构建入口组合，但不可让两个互不知情的路由器同时争抢浏览器历史。

| 地址或事件 | 外壳的路由选择 | 子应用输入 |
|---|---|---|
| 旧深链 | 迁移窗口内继续交给 V1 | `assetId=42`、`panel=inspector`、`node=heading-1`、`#canvas` |
| 新地址，未进 cohort | 先交给 V1，不呈现空白占位页 | 同一资源与视图状态 |
| 新地址，进入 cohort | 加载 V2，显示加载或失败状态 | 同一资源与视图状态 |
| 直接打开或刷新 | 完整 URL 匹配后等待所选子应用挂载 | 从 query 恢复选择；目标挂载后按 `#canvas` 定位 |
| Back / Forward | 根据浏览器恢复的完整 URL 重新匹配路由 | 从 query 恢复选择，并在目标挂载后恢复 URL fragment (片段) 定位 |

V1 与 V2 都应声明同一个 `id="canvas"` 目标。直接打开或刷新时，外壳先选定子应用，编辑器等目标节点随视图挂载后，再读取当前 `location.hash` 并定位到目标；不能假定异步加载的画布在浏览器首次处理 fragment 时已经存在。`pushState()` 和 `replaceState()` 只更新历史项和 URL，不会触发浏览器的 fragment 定位，所以发起导航的路由所有者应在视图挂载后调用同一恢复逻辑。Back / Forward 触发 `popstate` 后，应用重新读取完整 URL、恢复选择，并在目标挂载后定位。迁移验收要分别断言 `#canvas` 保留在 URL 中，以及画布确实进入视口；只检查 hash 不足以证明深链可用。

浏览器 History API (历史记录接口) 中，`pushState()` 会新增一条历史项，适合用户主动从旧入口进入新入口；`replaceState()` 替换当前历史项，适合旧路径已成为别名、且不希望 Back 在两个等价地址间循环时使用。应用在历史遍历时响应 `popstate` 并重新读取 URL；发起 `pushState()` 导航的路由所有者也要同步更新自身状态。改写旧路径时保留 query 与 fragment；服务端还要让前端深链回退到 shell HTML，同时继续把 `/api/` 交给 API (应用程序接口) 服务。

每个子应用通过明确的 `navigate()` 或同源链接请求跨边界导航。选中的 `node` 在文档加载后才与该修订的稳定节点 ID 对照；若节点不存在，就清除选择并显示页面，不把参数当成任意资源读取入口。

身份也要在部署边界定义。本例外壳使用同源会话 cookie，设置 `HttpOnly`、`Secure` 与适用的 `SameSite` 属性；给子应用传 `assetId`、非敏感显示数据和受限的数据访问接口，不把会话凭据放入路由、DOM 或共享状态广播。浏览器发出的资源读取与写入仍由服务端逐次验证当前主体是否获准访问该资产。客户端“能否显示该路由”不代替授权；服务端拒绝应以拒绝结果呈现，不要误判成代码加载失败再静默切换到另一版。本例 V1 与 V2 都在 shell 的同一页面运行，仍处在同一浏览器文档信任边界；仅从不同 origin 加载脚本不构成隔离。若子应用运行在另一 origin 的独立文档或 iframe 中，则需要单独设计跨源消息、身份、cookie 属性与 API 访问；它与同一页面加载远程脚本的边界不同。

V1 和 V2 在迁移初期读取、写入相同版本的文档格式。若 V2 将来写入 V1 不认识的新字段，只有 V1 会原样保留它，或路由能确保旧版不再打开这些文档，才可开放；仅忽略未知字段可能让 V1 下次保存时把字段删除。删除或改变字段含义，也要等旧版不再负责读写。若 V2 加载失败发生在用户开始编辑之前，可安全把新地址映射回 V1；编辑开始之后若已有未保存草稿，就先转换并交接草稿，或留在当前编辑器给出错误，不能静默切回并丢失用户修改。

发布按路由逐步改变处理者：先验证 shell 可加载两版并保持同一输入合同；再把新地址的一小组 cohort 交给 V2；检查直接深链与刷新时 hash 保留和画布定位、query、Back / Forward、未授权请求、V2 代码块加载失败、V1/V2 文档兼容与草稿保留，再扩大分流。若 V2 的错误率越过预设门槛，将新地址重新交给 V1。有效回退还要求 V1 代码仍可加载，且 V1 兼容当前数据格式。只有把流量开关拨回去、却没有旧代码或兼容格式，并不能恢复服务。

路由格式是跨应用通信合同，改路径或参数时要更新所有链接来源和消费者。页面构建资源的版本并存与回滚见[构建工具怎样把源码变成可发布产物？](../../frontend/tooling/build-tools.md)；服务端读写仍遵循[如何设计可预期的 HTTP API 契约？](../backend/http-api-contracts.md)。

**延伸阅读：** [如何让设计原则减少真实的修改成本？](software-design-principles.md)、[页面编辑器何时需要设计模式？](design-patterns-in-practice.md)、[怎样建模页面文档、编辑会话和发布快照？](low-code-editor-data-model.md)。

> [!info]- 来源
> - **共享状态的所有权。** React，“Sharing State Between Components”，状态上提与每份状态唯一所有者：[原文](https://react.dev/learn/sharing-state-between-components)，2026-11-12 核对。
> - **绘制顺序。** W3C CSS 2.2，Appendix E “Elaborate description of Stacking Contexts”，绘制顺序和层叠上下文：[原文](https://www.w3.org/TR/CSS22/zindex.html)，2026-11-12 核对。
> - **独立团队发布的收益与集成成本。** Cam Jackson, “Micro Frontends,” 2019-06-19，Benefits、Integration approaches、Downsides 与 Operational and governance complexity：[原文](https://martinfowler.com/articles/micro-frontends.html)。
> - **路由作为跨应用通信合同。** 同上，“Cross-application communication via routing”：[原文](https://martinfowler.com/articles/micro-frontends.html#Crossapplicationcommunicationviarouting)。
> - **浏览器历史行为。** WHATWG HTML Living Standard，§7.2.5 “The `History` interface” 中 `pushState()`、`replaceState()` 与历史遍历：[原文](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，2026-11-12 核对。
> - **片段定位。** WHATWG HTML Living Standard，“Scrolling to a fragment” 规定 fragment 对应文档中的定位目标；异步子应用须在目标挂载后恢复定位：[原文](https://html.spec.whatwg.org/multipage/browsing-the-web.html#scrolling-to-a-fragment)，2026-11-12 核对。
> - **会话 cookie 属性。** OWASP Session Management Cheat Sheet，`Secure`、`HttpOnly` 与 `SameSite` 说明：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)，2026-11-12 核对。
> - **客户端反馈与服务端校验。** OWASP Input Validation Cheat Sheet，“Client-only checks”：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)，2026-11-12 核对。
> - **跨应用运行时与授权边界。** OWASP Micro Frontend Security Cheat Sheet，“Choose and Enforce Runtime Boundaries”说明远程脚本仍使用宿主页面权限、跨源 iframe 才建立 origin 边界；“Authorize Every Request on the Server”要求每次后端请求重新授权：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Micro_Frontend_Security_Cheat_Sheet.html)，2026-11-12 核对。
