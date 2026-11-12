# 如何让设计原则减少真实的修改成本？

以下用一个完全合成的页面编辑器案例说明：编辑者可以添加标题和按钮节点，编辑器负责校验节点配置、生成画布预览，并保存文档。现在产品提出新增图片节点，规定发布时必须填写非空 alt text（替代文本）。表单尚未填写时仍将字段保留为空字符串，编辑者可以预览并保存草稿；只有发布某个具体修订时，发布门禁才检查这项规则。本例把所有图片都列入这条合成发布政策；真实产品还需区分装饰图，装饰图适合使用空 `alt`。替代文本应随图片用途决定。

假设现有文档格式已能保存新节点的 `type` 与 `props`，不用改存储契约。节点仍保留稳定 `id`、`children`，文档有独立修订号；下面的最小示例只展开展示分发、预览和发布所需字段。若真实存储结构只允许固定类型，新类型也必须纳入存储契约。

设计原则是追踪变化传播的判断工具。先确认本次规则实际会改哪些代码，再看同一次改动是否迫使不相关的调用者、规则或发布单元一起变。抽象只有在它能缩小这种传播、且收益大于新边界的维护成本时才值得保留。

## 单一职责：按共同变化原因聚合

**Single Responsibility Principle (单一职责原则，SRP)** 不是要求一个类只能有一个方法，而是提醒我们不要把会因不同业务要求而变化的规则绑在一起。Robert C. Martin 将它表述为模块只有一个变化理由，并把变化理由连到提出需求的业务方或维护方。

回到编辑器：发布规则可能要求修订中的图片有非空替代文本；设计系统则可能要求画布改变图片圆角和阴影。前者属于指定修订是否可发布的规则，后者属于视觉呈现。如果画布渲染函数也检查发布用的非空 `alt`，未完成的草稿就无法预览；如果保存入口复用发布门禁，草稿也不能保存。按实际变化来源分开草稿结构校验与预览、发布修订的完整性检查，视觉样式改动便不会改变草稿能否编辑或预览。

反过来，不能因为类里有两个名词就机械拆分。若只有一个简单的预览函数，且校验与生成视图总是作为同一次规则变化，拆成数个接口、文件和对象只会增加追踪路径。先列出这次变更由谁提出、哪条保证要同步修改、哪些调用者只依赖其中一部分；只有共同变化的证据出现，职责边界才有依据。

## 开闭：为已知的变化点留扩展位置

**Open/Closed Principle (开闭原则，OCP)** 的目标是让一个相对稳定的模块可以沿已知变化点扩展，尽量不必改动它的核心。它并不要求代码永远不修改，也不能让未预料的需求自动适配。

假设当前渲染入口按 `heading`、`button` 类型分支；新增 `image` 时，这个入口必须再加一个分支。按类型校验也有同样的问题。若“增加组件类型”已成为反复发生的变化，可以把类型定义与校验、渲染行为登记在一个受约束的注册表中。调用方只查找对应定义，不必随着每种类型增加新的中央分支：

注册表为每种类型分别保存 `validateDraft`（草稿检查）、`render`（预览）和 `validatePublish`（发布检查）。统一入口先按 `type` 取定义，再调用当前阶段需要的行为。同一图片节点因此能得到下面两种结果：

| 图片修订 | 草稿检查 | 画布预览与草稿保存 | 发布该修订 |
| --- | --- | --- | --- |
| 13：`alt: ''` | 通过，字段类型完整 | 生成 `<img alt="">` 描述符；文档所有者保存修订 13 | 发布门禁拒绝 13；已发布修订仍为 12 |
| 14：`alt: '页面结构图'` | 通过，字段类型完整 | 预览同一节点的新属性；文档所有者保存修订 14 | 发布门禁接受 14，可切换活动发布版本 |

> [!example]- 注册表如何同时服务草稿预览、保存和发布
>
> ~~~javascript
> const definitions = new Map([
>   ['heading', {
>     validateDraft: node => (
>       typeof node.props.text === 'string' &&
>       Number.isInteger(node.props.level) && node.props.level >= 1 && node.props.level <= 6
>     ),
>     validatePublish: () => true,
>     render: node => ({ tag: 'h' + node.props.level, text: node.props.text }),
>   }],
>   ['button', {
>     validateDraft: node => typeof node.props.label === 'string',
>     validatePublish: () => true,
>     render: node => ({ tag: 'button', text: node.props.label }),
>   }],
>   ['image', {
>     validateDraft: node => (
>       typeof node.props.src === 'string' && typeof node.props.alt === 'string'
>     ),
>     validatePublish: node => node.props.alt.trim().length > 0,
>     render: node => ({ tag: 'img', src: node.props.src, alt: node.props.alt }),
>   }],
> ]);
>
> function definitionFor(node) {
>   if (
>     !node || typeof node !== 'object' || typeof node.id !== 'string' ||
>     typeof node.type !== 'string' || !node.props || typeof node.props !== 'object' ||
>     Array.isArray(node.props) || !Array.isArray(node.children)
>   ) throw new TypeError('invalid node structure');
>
>   const definition = definitions.get(node.type);
>   if (!definition) throw new RangeError('unsupported component type');
>   if (!definition.validateDraft(node)) throw new TypeError('invalid draft node');
>   return definition;
> }
>
> function renderNode(node) {
>   return definitionFor(node).render(node);
> }
>
> function commitDraft(document, node) {
>   definitionFor(node);
>   return {
>     ...document,
>     revision: document.revision + 1,
>     nodes: [...document.nodes, node],
>   };
> }
>
> function saveDraft(document, drafts) {
>   for (const node of document.nodes) definitionFor(node);
>   drafts.set(document.revision, document);
>   return document.revision;
> }
>
> let publishedRevision = 12;
> function publishRevision(revision, drafts) {
>   const document = drafts.get(revision);
>   if (!document) throw new RangeError('draft revision not found');
>   for (const node of document.nodes) {
>     const definition = definitionFor(node);
>     if (!definition.validatePublish(node)) throw new TypeError('publication requirements not met');
>   }
>   publishedRevision = revision;
>   return publishedRevision;
> }
>
> const revision12 = {
>   revision: 12,
>   nodes: [
>     { id: 'heading-1', type: 'heading', props: { text: '首页', level: 1 }, children: [] },
>     { id: 'button-1', type: 'button', props: { label: '报名' }, children: [] },
>   ],
> };
> const imageDraft = {
>   id: 'image-1', type: 'image',
>   props: { src: '/media/diagram.png', alt: '' }, children: [],
> };
> const drafts = new Map();
> const revision13 = commitDraft(revision12, imageDraft);
> const savedRevision13 = saveDraft(revision13, drafts);
> const preview13 = renderNode(imageDraft);
> let publicationError;
> try {
>   publishRevision(13, drafts);
> } catch (error) {
>   publicationError = error.name;
> }
> console.log(JSON.stringify({
>   preview13, savedRevision13, publicationError, publishedRevision,
> }));
>
> const completedImage = {
>   ...imageDraft,
>   props: { ...imageDraft.props, alt: '页面结构图' },
> };
> const revision14 = {
>   ...revision13,
>   revision: 14,
>   nodes: revision13.nodes.map(node => node.id === completedImage.id ? completedImage : node),
> };
> const savedRevision14 = saveDraft(revision14, drafts);
> const preview14 = renderNode(completedImage);
> const acceptedRevision = publishRevision(14, drafts);
> console.log(JSON.stringify({ preview14, savedRevision14, publishedRevision: acceptedRevision }));
> ~~~

`definitionFor` 先确认节点形状与编辑期契约。新增图片只需登记草稿字段规则、预览描述符与发布条件；统一的画布渲染、修订保存和发布遍历都从同一注册表读取定义，不必再增加 `image` 分支。登记仍是代码变更；OCP 的收益是避免修改所有既有调用路径。

草稿结构要求 `alt` 是字符串，因此表单未填写时存为 `''`，而不是缺少字段。`renderNode` 只执行草稿结构检查并返回可预览的 `<img>` 描述符；文档所有者把它保存为修订 13。发布者按修订号读取已保存的 13，再运行发布门禁，所以空 `alt` 会阻止公开，而不会撤销草稿保存。填写替代文本产生修订 14，预览与保存继续成功，发布检查才允许将活动发布修订推进到 14。代码输出中修订 13 的 `publishedRevision` 仍为 12。`drafts` 只是演示按修订读写的内存 Map；本例修改时新建对象，保存后不再改写旧对象。Map 自身不会复制或冻结对象，真实版本保存还需由文档持久化层落实。

本例为突出类型分发而把 `nodes` 写成数组；完整的根节点顺序、ID 索引、样式及树约束见[页面文档和发布快照的数据模型](low-code-editor-data-model.md)。真实服务端仍应对发布请求重新检查其权威修订与输入，不依赖浏览器的即时检查。

如果只有一两个稳定类型，`switch` 通常更直观。注册表也有维护成本：类型、校验器与渲染器必须保持一致，错误处理和注册时机也需要约定。等到类型变更在多个入口重复扩散，再引入边界通常比提前设计插件系统更有证据。

## 里氏替换：子类型不能改变调用者依赖的行为

**Liskov Substitution Principle (里氏替换原则，LSP)** 讨论的是行为契约，而不只是继承关系或相同的方法名。若调用者依赖 `NodeRenderer.render(node)` 对每个满足已登记类型草稿契约的节点（包括未发布草稿）都能同步返回预览描述符，那么子类型也必须满足这份保证。

假设画布按同步的 `NodeRenderer.render(node)` 契约工作，现有实现 `DefaultNodeRenderer` 能为合法远程图片返回预览描述符。若把传给画布的实现换成它的子类型 `ImagePreviewRenderer`，而该子类型要求调用者先下载图片并对同一合法输入抛出“暂不支持”，画布便无法安全地用子类型替代原实现。这个子类型收紧了调用者的前置条件，违反了原契约。若当前仍要求同步返回，图片子类型可以返回 `<img>` 描述符，让画布或浏览器继续加载资源；若产品必须等待加载结果，就要共同修改 `render` 契约为异步结果，并让现有调用者处理加载状态，不能只在子类型里悄悄改变行为。

判断替换关系时，列清前置条件、后置保证、错误结果和状态不变量：子类型不能要求调用者额外准备条件，也不能撤回基类已经承诺的结果。Liskov 与 Wing 的形式化定义把这些可观察行为与类型不变量一并纳入；它帮助识别“看起来像一种节点、实际却不能安全替换”的设计。

## 接口隔离与依赖倒置：按调用者需要定义契约

**Interface Segregation Principle (接口隔离原则，ISP)** 针对调用者被迫依赖自己不用的能力。画布只需把节点渲染成视图；发布流程需要校验文档并持久化；如果两者都依赖一个同时含编辑、渲染、校验、存储和发布方法的大接口，任何一方的变化都可能拉动另一方重新编译、测试或部署。

可以按稳定的调用角色拆分契约，例如让画布依赖 `NodeRenderer`，让发布流程依赖 `DocumentValidator` 与 `DocumentWriter`。这不等于为每个类和每个调用点都新建专属接口；Martin 特别提醒接口也可能切得过细，造成数量和关系难以维护。

**Dependency Inversion Principle (依赖倒置原则，DIP)** 解决的是依赖箭头：发布模块定义自己需要的 `DocumentWriter` 契约，数据库适配器引用并实现它；运行时的组合入口把适配器交给发布流程，发布流程仍只调用 `writer.write(revision)`。依赖方向因此从数据库细节指向发布模块的契约，而不是发布策略直接依赖具体数据库驱动。

**dependency injection (依赖注入)** 可以把 `DocumentWriter` 传给发布流程，但它只是传递依赖的方式，不等于依赖倒置本身。若文档只写入一个很简单的内存对象，既无替换需求，也无测试隔离收益，再包几层接口并不会自动让设计更好。

## DRY、KISS 与 YAGNI 如何约束抽象？

DRY (Don't Repeat Yourself，不重复同一知识)要消除的是同一知识被多处独立维护的风险，不是让长得相似的代码必须合并。标题文本和按钮标签都恰好是字符串，却代表不同配置；把它们合成一个含糊的 `text` 字段可能让调用者更难判断含义。相反，如果“哪些节点可以发布”的同一政策被编辑预览与发布流程各自维护，两个列表就可能逐渐不一致，应找出真正的政策所有者或共同契约。用户端即时提示与服务端权威校验即使内容相似，也可能需要分别执行，因为它们处在不同信任边界。Hunt 与 Thomas 将 DRY 定义为让每份知识在系统中只有一个清楚且权威的表示；如果需求变更必须在多个位置以不同形式同步更新，就出现了重复知识。

KISS (Keep It Simple，保持简单)要求方案与当前变化规模相称。YAGNI (You Aren't Gonna Need It，尚未需要的能力先不实现)提醒我们不要仅凭假想的插件需求预建多层接口。若添加一种固定节点只需一条清楚的分支，直接写分支更易维护；如果同类需求已反复要求同时修改创建、校验和渲染入口，再把这些变化收拢到可验证的扩展点。

## 用变化案例决定边界

现在沿同一图片节点走一遍。草稿结构要求 `alt` 字段存在且是字符串；空字符串可以预览并保存。发布服务按明确修订读取草稿，再检查这项合成产品规则：本例要求每张图片发布时 `alt` 非空。

这条路径中，失败的是针对修订 13 的发布请求，不是编辑提交、画布渲染或草稿保存。浏览器中的即时提示只帮助编辑者尽早发现问题；发布服务仍需对选定修订权威校验，不能信任客户端已运行的检查。`alt` 规则仅为本例政策：装饰图或与邻近文本重复的图片可以用空 `alt`，真实产品应依据图片用途定义发布条件。

谁把通过草稿检查的插入请求提交为新修订？由文档所有者负责，编辑会话只表达变更意图；修订、撤销、保存和发布快照见[页面文档和发布快照的数据模型](low-code-editor-data-model.md)，状态由谁持有见[前端架构怎样划分呈现、交互和数据所有权？](frontend-architecture-boundaries.md)。[页面编辑器何时需要设计模式？](design-patterns-in-practice.md)再展示工厂、策略和观察者如何落实创建、校验与通知边界。

是否采用注册表，取决于变化轨迹：第一次新增类型且只有一处调用时，直接分支更简单；若多个类型连续要求改动同一批入口，注册表会让校验和渲染扩展集中。继续观察每次新增是否真只需一条定义、是否把一致性问题转移到了注册表和类型声明；当扩展机制本身开始变复杂，就应重新评估边界。

> [!info]- 来源
> - **SRP 的变化理由。** Robert C. Martin, “The Single Responsibility Principle,” 2014-05-08，讨论 Parnas 的变化决策封装和按变化请求来源划分模块：[原文](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html)，尤其是 “What defines a reason to change?” 至结尾。
> - **OCP、LSP、DIP 与 ISP。** Robert C. Martin, “Design Principles and Design Patterns,” 2000，OCP pp. 4–8、LSP pp. 8–12、DIP pp. 12–14、ISP pp. 14–16：[原文 PDF](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。文中把这些原则应用到页面编辑器的注册表、存储边界和调用者契约，是本章的合成工程案例。
> - **行为子类型。** Barbara H. Liskov 与 Jeannette M. Wing, “A Behavioral Notion of Subtyping,” *ACM Transactions on Programming Languages and Systems*, 16(6), 1994, pp. 1811–1841；第 5.2 节的不变量、方法前后置条件与约束规则：[论文 PDF](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf)。
> - **DRY。** Andy Hunt 与 Dave Thomas, *The Pragmatic Programmer: Your Journey to Mastery*, 20th Anniversary Edition, 第 9 节 “The Evils of Duplication”；DRY 要求每份知识在系统中有单一、清楚且权威的表示：[节选 PDF](https://media.pragprog.com/titles/tpp20/dry.pdf)。
> - **客户端与服务端校验。** OWASP *Input Validation Cheat Sheet* 的 “Client-only checks” 指出客户端检查适合即时反馈，但可被绕过；服务端仍须执行权威校验：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)。
> - **装饰图片替代文本。** W3C WAI 的 alt 决策树指出，装饰图或与邻近文字重复的图片可以使用空 `alt`；本例的非空发布规则是产品假设而非通用无障碍要求：[原文](https://www.w3.org/WAI/tutorials/images/decision-tree/)。
> - **YAGNI。** Martin Fowler 将 YAGNI 描述为暂不实现尚未需要的功能，并提醒未使用的扩展点会增加当前复杂度：[原文](https://martinfowler.com/bliki/Yagni.html)。
