# 怎样判断一个抽象值不值得引入？

本章回答：面对一条新需求，怎样判断该加一个接口、注册表或分层，还是直接改几行分支。答案是先看这次变化会传播到哪些代码，只有当一个抽象能缩小这种传播、而且收益大于维护新边界的成本时才引入它。SOLID、DRY、YAGNI 这些原则都是预测传播的工具，本章按“变化来了先看哪里”的顺序使用它们，而不是逐条背诵。

**案例。** 从[下一章](debugging-and-code-review.md)起，主线五跟随报表服务的一次修复发布，从缺陷一直走到生产。判断抽象却需要一个会反复增加类型的代码库，修一个读取缺陷的场景不合适，所以本章和两条支线改用一个合成的页面编辑器作独立案例。编辑器里有标题（`heading`）和按钮（`button`）两种节点，负责校验节点配置、在画布上预览、保存草稿和发布。页面当前公开的是 revision (修订) r16：分组 `section-1` 下依次是按钮 `button-1` 和标题 `heading-1`（这个状态怎样从 r12 编辑而来，见[页面编辑器的数据模型](page-editor-data-model.md)）。

新需求是增加图片节点（`image`），并规定**发布时**每张图片的 alt text (替代文本) 必须非空。编辑者还没填写时，`alt` 存为空字符串，草稿照样可以预览和保存。预期结果是：

- 插入 `image-1`、`alt` 为空，得到草稿 r17：可预览、可保存，发布 r17 被拒绝，访客仍看到 r16。
- 补上 `alt: '页面结构图'`，得到 r18：发布通过，访客看到 r18。

“所有图片都要非空 alt”是本例的产品约定。真实产品要区分用途：装饰图或与邻近文字重复的图片应使用空 `alt`。另假设现有存储格式已能保存任意 `type` 与 `props`，不必改存储契约。

## 一次需求会改到哪些地方？

在只支持标题和按钮的版本里，节点类型散落在五个入口：工具栏和粘贴创建节点时填默认属性；保存前检查草稿结构；画布按类型渲染预览；保存时遍历文档；发布门禁检查能否公开。代码按 `switch (node.type)` 分支，新增 `image` 就要在其中至少四处各加一个分支。

判断要不要引入抽象，先回答三个问题：

1. 这条需求实际要改哪些代码？
2. 这次改动会不会迫使不相关的调用者、规则或发布单元跟着改？
3. 新边界能不能缩小这种传播？缩小的部分是否大于维护这个边界的成本？

后面几节是这三个问题在不同位置的回答：职责按谁提出变化来划分，扩展点留给反复出现的变化，接口按调用者需要来切，重复要看是不是同一份知识。

## 按变化来源划分职责：草稿合法与可发布是两道检查

**Single Responsibility Principle (单一职责原则，SRP)** 并不要求一个类只有一个方法。Robert C. Martin 的表述是“一个模块只应有一个变化的理由”，而“理由”对应提出需求的那一方。编辑器里至少有三个来源：

- 编辑器本身定义草稿结构：`alt` 必须是字符串。
- 产品或合规方定义发布规则：发布时 `alt` 非空。
- 设计系统定义视觉呈现：图片的圆角和阴影。

如果把它们绑在一起，一方的变化就会打断另一方的工作。画布渲染函数若也检查发布用的非空 `alt`，未填完的草稿就无法预览；保存入口若复用发布门禁，草稿就无法保存。把“草稿结构检查与预览”和“发布前的完整性检查”分开，视觉样式改动也不会影响草稿能否编辑。分开之后，案例里的两个修订走出不同结果：

| 修订 | 草稿检查 | 预览与保存 | 发布该修订 |
| --- | --- | --- | --- |
| r17：`image-1` 的 `alt: ''` | 通过，字段类型完整 | 画布生成 `<img alt="">` 描述符；文档所有者保存 r17 | 发布门禁拒绝；公开版仍是 r16 |
| r18：`alt: '页面结构图'` | 通过 | 预览新属性；保存 r18 | 发布门禁接受；公开版切到 r18 |

发布失败只拒绝了这一次发布请求，不撤销已保存的 r17。浏览器里的即时提示只帮编辑者早发现问题；服务端收到发布请求时，仍要按服务端保存的那个修订重新检查，因为客户端检查可以被绕过。

反过来，也不能因为类里出现两个名词就机械拆分。若只有一个简单的预览函数，校验和生成视图总是因同一条规则一起变化，把它拆成几个接口和文件只会拉长追踪路径。拆分的依据是证据：这次变更由谁提出，哪条保证要同步修改，哪些调用者只依赖其中一部分。

## 变化点反复出现时，用注册表收拢分支

**Open/Closed Principle (开闭原则，OCP)** 的目标是：一个相对稳定的模块可以沿已知变化点扩展，而不必改动核心。它不要求代码永不修改，也不能让没预料到的需求自动适配。

如果“新增一种节点类型”已经反复发生，可以把每种类型的行为登记在一个受约束的注册表里。每项登记三种行为：`validateDraft`（草稿检查）、`render`（预览）和 `validatePublish`（发布检查）。入口只按 `type` 取定义，再调用当前阶段需要的那一项：

~~~javascript
const nodeTypes = new Map([
  ['heading', {
    validateDraft: n => typeof n.props.text === 'string' && Number.isInteger(n.props.level),
    render: n => ({ tag: `h${n.props.level}`, text: n.props.text }),
    validatePublish: () => [],
  }],
  ['image', {
    validateDraft: n => typeof n.props.src === 'string' && typeof n.props.alt === 'string',
    render: n => ({ tag: 'img', src: n.props.src, alt: n.props.alt }),
    validatePublish: n => (n.props.alt.trim() ? [] : [`${n.id}: alt must not be empty`]),
  }],
]);

function definitionFor(node) {
  const definition = nodeTypes.get(node.type);
  if (!definition) throw new RangeError(`unsupported type: ${node.type}`);
  if (!definition.validateDraft(node)) throw new TypeError(`invalid draft node: ${node.id}`);
  return definition;
}

const renderNode = node => definitionFor(node).render(node);             // 画布预览
const publishErrors = nodes =>                                           // 发布门禁
  nodes.flatMap(node => definitionFor(node).validatePublish(node));
~~~

对 r17 里的 `image-1`（`src: '/media/diagram.png'`、`alt: ''`），`renderNode` 返回 `{"tag":"img","src":"/media/diagram.png","alt":""}`，`publishErrors` 返回 `["image-1: alt must not be empty"]`；补上替代文本后，`publishErrors` 返回 `[]`。保存只对每个节点调用 `definitionFor`，所以只做草稿检查。

新增图片只需登记一项定义，画布、保存和发布都从同一个注册表读取，不必再各加一个 `image` 分支。登记本身仍是代码变更；OCP 的收益在于不必改动所有已有调用路径。

注册表也有成本：类型、校验器和渲染器必须保持一致，错误处理和注册时机要约定。如果只有一两个稳定的类型，`switch` 更直观。

## 替换实现时，子类型不能改变调用者依赖的行为

**Liskov Substitution Principle (里氏替换原则，LSP)** 讨论的是行为契约，不只是继承关系或相同的方法名。注册表里的 `render` 就是一份契约：画布依赖“只要节点通过草稿检查，`render(node)` 就同步返回预览描述符”。

假设有人为图片写了一个 `ImagePreviewRenderer` 替换默认实现，它要求调用者先下载图片，否则对同一个合法节点抛出“暂不支持”。这个实现加强了前置条件，画布无法安全地用它替换原实现。可行的做法有两种：

- 仍然同步返回 `<img>` 描述符，让浏览器自己加载资源。
- 如果产品确实要等加载结果，就把 `render` 契约整体改成异步，并让所有现有调用者处理加载状态。

不能只在一个子类型里悄悄改变行为。判断能否替换时，列清前置条件、后置保证、错误结果和状态不变量：子类型不能要求调用者额外准备条件，也不能撤回基类已经承诺的结果。Liskov 与 Wing 的形式化定义把这些可观察行为与类型不变量一起纳入。

## 接口按调用角色切分，依赖指向策略一侧

**Interface Segregation Principle (接口隔离原则，ISP)** 针对的问题是：调用者被迫依赖自己用不到的能力。画布只需要把节点渲染成视图；发布流程需要校验文档并持久化。如果两者都依赖一个同时包含编辑、渲染、校验、存储和发布的大接口，任何一方的变化都可能拉着另一方重新编译、测试或部署。

按稳定的调用角色拆分：画布依赖 `NodeRenderer`，发布流程依赖 `DocumentValidator` 和 `DocumentWriter`。这不等于给每个类、每个调用点都新建专属接口；Martin 也提醒接口切得过细，数量和关系会变得难以维护。

**Dependency Inversion Principle (依赖倒置原则，DIP)** 调整的是依赖方向。发布模块自己定义需要的 `DocumentWriter` 契约，数据库适配器实现它；启动代码（组合入口）把适配器交给发布流程：

~~~javascript
// 发布模块：契约由使用方定义，只要求 write(snapshot)
async function publish(revision, { loadRevision, writer }) {
  const document = await loadRevision(revision);
  const errors = publishErrors(document.nodes);
  if (errors.length) return { ok: false, errors };
  await writer.write({ revision, document });
  return { ok: true, revision };
}

// 组合入口：把具体的数据库适配器交给发布流程
// publish(18, { loadRevision: drafts.load, writer: postgresSnapshotWriter });
~~~

依赖箭头因此从数据库细节指向发布模块的契约，而不是发布逻辑直接依赖某个数据库驱动。**dependency injection (依赖注入)** 只是把 `writer` 传进来的手段，不等于依赖倒置本身。如果文档只写进一个简单的内存对象，既没有替换需求，也没有测试隔离收益，再包几层接口并不会让设计更好。

## DRY 消除的是重复知识，不是相似代码

DRY (Don't Repeat Yourself) 出自 Hunt 与 Thomas：每份知识在系统中只有一个清楚、权威的表示。判断标准是：一次需求变更是否必须在多个位置、以不同形式同步修改。

- **相似但不是同一知识。** 标题文本和按钮标签恰好都是字符串，含义却不同。把它们合成一个含糊的 `text` 字段，调用者反而更难判断含义。
- **同一知识被分头维护。** “哪些节点可以发布”若在编辑预览和发布流程里各写一份列表，两份迟早不一致。应找到这条政策的所有者，例如让两处都读注册表里的 `validatePublish`。
- **同一知识在两处执行。** 浏览器的即时提示和服务端的权威校验处在不同信任边界，必须分别执行。只要两处读取同一份规则定义，执行两次并不违反 DRY。

## 什么时候引入扩展点，什么时候拆掉它？

KISS (Keep It Simple) 要求方案与当前变化规模相称。YAGNI (You Aren't Gonna Need It) 提醒不要凭假想的插件需求预建多层接口：Martin Fowler 指出，未被使用的扩展点也会增加当下的复杂度。

在本例里，可以这样判断：

- **第一次新增类型、只有一处调用。** 直接加一个分支更简单。
- **多种类型接连要求修改同一批入口。** 引入注册表，把创建、校验和渲染的扩展集中到一处。
- **引入之后继续观察。** 每次新增是否真的只需登记一项定义？一致性问题是否只是从分支转移到了注册表和类型声明之间？扩展机制本身开始变复杂时，就重新评估这个边界。

## 组件和分层各解决什么问题？

前面讨论的是规则怎样组织，代码在界面和模块上怎样拆分是另外两个问题。

**component-based architecture (基于组件的架构)** 按可复用的视图和交互边界拆分界面：`Canvas` 呈现文档树，`Inspector` 编辑选中节点的属性，`NodeView` 呈现一种节点类型。组件接口要说明数据和回调怎样传入，选择、修改、删除等意图怎样传出。视图拆成组件，并不会因此获得文档的所有权。

分层按职责把交互状态、文档命令、持久化和视图分开。这个编辑器只需要少数几层：

- 会话控制器持有当前选择 `selectedId` 和拖动预览 `dragPreview`。
- 文档所有者接受命令，校验结构与业务规则，产生新修订。
- 存储适配器保存一个指定修订。
- 视图读取会话和文档的投影。

只有某一层确实承载独立的规则或依赖边界，才值得拆成独立的包或服务。给每个组件都配一套“控制器—服务—仓库”，会增加跨层跳转，却未必缩小变化范围。

## 本章产出与下一步

本章给出一套判断顺序：先列出一条需求会改到的代码，再按变化来源划分职责，只在变化反复出现时引入扩展点，并持续检查扩展点是否真的缩小了修改范围。页面编辑器的边界因此确定为：注册表负责按类型分发，草稿检查与发布门禁分开，文档所有者是唯一能产生修订的模块。

两条支线沿用同一个编辑器：[工厂、策略、观察者和单例各解决什么协作问题](design-patterns-in-practice.md)把“创建—校验—提交—通知”落实成对象协作；[页面编辑器怎样建模文档、编辑会话和发布快照？](page-editor-data-model.md)说明这三份数据怎样分开保存，r17 为什么不会混进公开页面。

主线接下来回到报表服务。设计决定了代码怎样分块，但缺陷仍会出现：下一章[怎样把一份缺陷报告变成可证伪的反例，并用证据审查修复？](debugging-and-code-review.md)从一份越权报告出发，讲怎样把症状写成可证伪的反例，沿调用路径找到丢失的条件。

> [!info]- 来源
> - **SRP 的“变化理由”对应提出需求的一方**（“按变化来源划分职责”）：Robert C. Martin, “The Single Responsibility Principle,” 2014-05-08，“What defines a reason to change?” 至结尾：[原文](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html)。
> - **OCP、LSP、DIP 与 ISP，以及接口切得过细的代价**（“注册表”“子类型”“接口”三节）：Robert C. Martin, “Design Principles and Design Patterns,” 2000，OCP pp. 4–8、LSP pp. 8–12、DIP pp. 12–14、ISP pp. 14–16：[PDF](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。把原则用到编辑器注册表、存储边界和调用者契约，是本章的合成案例。
> - **行为子类型：前后置条件与不变量**（“子类型不能改变调用者依赖的行为”）：Barbara H. Liskov, Jeannette M. Wing, “A Behavioral Notion of Subtyping,” *ACM TOPLAS* 16(6), 1994, pp. 1811–1841，§5.2：[PDF](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf)。
> - **DRY 是知识的单一权威表示**（“DRY 消除的是重复知识”）：Andy Hunt, Dave Thomas, *The Pragmatic Programmer*, 20th Anniversary Edition, Topic 9 “DRY—The Evils of Duplication”：[节选 PDF](https://media.pragprog.com/titles/tpp20/dry.pdf)。
> - **客户端检查只作即时反馈，服务端仍须权威校验**（“草稿合法与可发布是两道检查”“DRY”）：OWASP *Input Validation Cheat Sheet*，“Client-only checks”：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)。
> - **装饰图可用空 alt**（案例中的产品约定）：W3C WAI, “An alt Decision Tree”：[原文](https://www.w3.org/WAI/tutorials/images/decision-tree/)。
> - **YAGNI 与未使用扩展点的当下成本**（“什么时候引入扩展点”）：Martin Fowler, “Yagni”：[原文](https://martinfowler.com/bliki/Yagni.html)。
