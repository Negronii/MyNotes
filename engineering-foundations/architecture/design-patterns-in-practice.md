# 页面编辑器何时需要设计模式？

案例使用一份合成的页面编辑器文档：当前修订为 12，已有 `heading-1` 和 `button-1`；编辑者从工具栏插入标题，画布与检查器都要看到新修订。**design pattern（设计模式）**给反复出现的对象协作方式命名，但模式不会替系统决定谁拥有文档、哪些规则只在发布时检查，或订阅何时结束。**GoF（Gang of Four，四人帮）**原著也把适用情境、约束、结果和取舍作为模式说明的一部分，并以文档编辑器作案例；它不是可机械套用的类图。

先找出哪种变化正在重复。如果一次普通函数调用或稳定的条件分支已经让修改范围清楚，多加对象、注册步骤和清理责任只会增加跳转。下面三个 JavaScript 代码块按出现顺序在同一模块中运行；工厂产出的 `heading` 会直接交给策略和状态所有者。

## 创建规则变多时，用工厂集中入口

工具栏、粘贴和快捷键都能创建标题。若每个入口都各自填写默认属性、分配 ID（标识符），节点形状会逐渐不一致。此时 **factory（工厂）**适合集中这些创建规则；最初通常只是一个函数。

~~~javascript
const defaults = new Map([
  ['heading', { text: '', level: 2 }],
  ['button', { label: '按钮', variant: 'primary' }],
]);

let nextId = 1;

function createNode(type) {
  const initialProps = defaults.get(type);
  if (!initialProps) throw new RangeError('unknown component type');
  if (!Number.isSafeInteger(nextId)) throw new RangeError('node ID counter exhausted');

  const id = 'node-' + nextId;
  nextId += 1;
  return { id, type, props: { ...initialProps }, children: [] };
}

const heading = createNode('heading');
console.log(JSON.stringify(heading));
try {
  createNode('constructor');
} catch (error) {
  console.log(error.name);
}
~~~

这段程序输出一个 `node-1` 标题草稿，文本初始为空、层级为 2；`createNode('constructor')` 输出 `RangeError`。空文本是编辑期默认值，后续策略会检查字段类型和层级，但不把发布要求塞进节点创建。`Map` 只接受显式注册的组件类型，因此不会把对象原型上的同名属性误当作可创建类型。若整个页面只有一处创建固定对象，直接写对象字面量更清楚。

这里的计数器只在本次运行中分配不重复的安全整数。刷新、跨窗口协作或多个写入者并发时，它不能保证全局唯一；持久化系统需由文档状态或专门的 ID 方案处理。对象创建后若未通过后续编辑校验，计数器也可能留下空号，这不影响唯一性。这个简单函数也不是 GoF 中的 **Factory Method（工厂方法）**或 **Abstract Factory（抽象工厂）**：前者让子类决定实例化哪个类，后者创建相关对象族；本例没有这类变化需求。

## 行为可互换时，用策略

当组件类型各自有不同的编辑期结构规则，而且新增规则需要避免挤进一个不断增长的条件块时，可以把校验行为放进类型对应的函数。**strategy（策略）**让调用方通过同一契约使用这些可替换的算法。

~~~javascript
const editableValidators = new Map([
  ['heading', node => {
    const errors = [];
    if (typeof node.props.text !== 'string') errors.push('标题文本必须是字符串');
    if (!Number.isInteger(node.props.level) || node.props.level < 1 || node.props.level > 6) {
      errors.push('标题层级必须是 1 到 6 的整数');
    }
    return errors;
  }],
  ['button', node => (
    typeof node.props.label === 'string' ? [] : ['按钮标签必须是字符串']
  )],
]);

function validateEditableNode(node) {
  const validate = editableValidators.get(node.type);
  return validate ? validate(node) : ['未知组件类型：' + node.type];
}

function previewDraftNode(node) {
  const errors = validateEditableNode(node);
  if (errors.length > 0) throw new TypeError('invalid draft node');
  return { type: node.type, props: { ...node.props } };
}

const invalidHeading = {
  ...heading,
  props: { ...heading.props, level: 8 },
};
console.log(JSON.stringify({
  headingErrors: validateEditableNode(heading),
  invalidHeadingErrors: validateEditableNode(invalidHeading),
  preview: previewDraftNode(heading),
}));
~~~

输出中空标题的编辑错误列表是 `[]`，同一 `node-1` 的 8 级变体返回 `['标题层级必须是 1 到 6 的整数']`；预览保留空文本和 2 级结构。状态所有者会直接调用 `validateEditableNode(node)`，而不是信任调用者另传一个错误列表。来自服务器或外部文件的节点，还要先通过通用结构解析；这里的策略只校验已解析节点的类型特有字段，也不负责授权。

编辑合法性与发布门槛必须由不同流程负责。当前空标题可保存为草稿并预览；本例的产品发布规则另要求标题非空，后面会让发布入口针对某个修订检查它。若类型和规则数量很少且稳定，`switch` 更直接；只有变化确实分散时，策略注册才值得承担额外维护。

## 多个视图订阅同一修订时，用观察者

插入命令传入前两节构造并校验过的同一个 `heading`。状态所有者在拒绝错误节点或接受合法草稿时都会自行调用策略；只有无错误时才创建修订并提交，再把已提交文档交给通知器。画布与检查器因此读到同一修订。**observer（观察者）**让状态主体管理多个接收者；文档仍由状态所有者持有，通知器只持有订阅。

![标题插入先经工厂和编辑策略；有效节点才提交新修订，错误分支保留原修订](resources/design-patterns-in-practice-node-insertion.svg)

> [!example]- 状态提交、通知快照与指定修订的发布实现
>
> ~~~javascript
> class DocumentNotifier {
>   #listeners = new Set();
>
>   subscribe(listener) {
>     this.#listeners.add(listener);
>     return () => this.#listeners.delete(listener);
>   }
>
>   notify(document) {
>     const listeners = [...this.#listeners];
>     for (const listener of listeners) listener(document);
>   }
> }
>
> function freezeNode(node) {
>   return Object.freeze({
>     ...node,
>     props: Object.freeze({ ...node.props }),
>     children: Object.freeze([...node.children]),
>   });
> }
>
> function freezeDocument(document) {
>   return Object.freeze({
>     ...document,
>     nodes: Object.freeze(document.nodes.map(freezeNode)),
>   });
> }
>
> const state = {
>   current: freezeDocument({
>     revision: 12,
>     nodes: [
>       { id: 'heading-1', type: 'heading', props: { text: '首页', level: 1 }, children: [] },
>       { id: 'button-1', type: 'button', props: { label: '报名' }, children: [] },
>     ],
>   }),
> };
> const revisions = new Map([[12, state.current]]);
> const notifier = new DocumentNotifier();
> const received = [];
> const unsubscribeCanvas = notifier.subscribe(doc => received.push('canvas r' + doc.revision));
> const unsubscribeInspector = notifier.subscribe(doc => received.push('inspector r' + doc.revision));
> let notifying = false;
> let publishedRevision = 12;
>
> function commitEditableNode(node) {
>   if (notifying) return { ok: false, errors: ['通知期间不能同步提交编辑'] };
>   const errors = validateEditableNode(node);
>   if (errors.length > 0) return { ok: false, errors };
>
>   const exists = state.current.nodes.some(existing => existing.id === node.id);
>   const nodes = exists
>     ? state.current.nodes.map(existing => existing.id === node.id ? node : existing)
>     : [...state.current.nodes, node];
>   const next = freezeDocument({
>     ...state.current,
>     revision: state.current.revision + 1,
>     nodes,
>   });
>   state.current = next;
>   revisions.set(next.revision, next);
>
>   notifying = true;
>   try {
>     notifier.notify(next);
>   } finally {
>     notifying = false;
>   }
>   return { ok: true, revision: next.revision, nodeId: node.id };
> }
>
> function publishRevision(revision) {
>   const document = revisions.get(revision);
>   if (!document) throw new RangeError('draft revision not found');
>   for (const node of document.nodes) {
>     const errors = validateEditableNode(node);
>     if (errors.length > 0) return { ok: false, errors, publishedRevision };
>     if (node.type === 'heading' && node.props.text.trim().length === 0) {
>       return { ok: false, error: '标题发布时不能为空', publishedRevision };
>     }
>   }
>   publishedRevision = revision;
>   return { ok: true, publishedRevision };
> }
>
> console.log(JSON.stringify(commitEditableNode(invalidHeading)));
> console.log(JSON.stringify({ revision: state.current.revision, notifications: received.length }));
> console.log(JSON.stringify(commitEditableNode(heading)));
> console.log(JSON.stringify({
>   preview: previewDraftNode(state.current.nodes.find(node => node.id === heading.id)),
>   revision: state.current.revision,
>   notifications: received.join(', '),
> }));
> console.log(JSON.stringify(publishRevision(13)));
>
> const savedHeading13 = state.current.nodes.find(node => node.id === heading.id);
> const completedHeading = {
>   ...savedHeading13,
>   props: { ...savedHeading13.props, text: '首页标题' },
> };
> console.log(JSON.stringify(commitEditableNode(completedHeading)));
> console.log(JSON.stringify(publishRevision(14)));
> console.log(JSON.stringify({ notifications: received.join(', ') }));
> unsubscribeCanvas();
> unsubscribeInspector();
> ~~~

这段顺序执行的程序先以 8 级标题尝试提交：策略实际返回错误，状态仍是 revision 12，通知数为 0。工厂生成的空标题通过编辑校验，文档所有者才将它提交为 revision 13；画布得到预览描述符，画布和检查器都收到 `r13`。发布流程读取确切的 revision 13，因标题为空而拒绝，公开版本仍是 12。填写同一 `node-1` 后，状态所有者提交 revision 14，两个视图收到 `r14`，发布门禁再允许活动公开版本切换到 14。此处用活动修订号表示发布结果；实际不可变快照的创建与切换由相邻数据模型章节展开。

通知接收者列表在 `notify()` 开始时复制，因此本轮新增或取消订阅只影响后续通知；若回调在本轮中取消别人的订阅，该人仍会收到本轮已排定的通知。副本只固定接收者集合，不会保护文档内容。这里通过不可变更新和 `Object.freeze` 复制并冻结文档、节点、属性与子节点数组；画布和检查器只读修订。同步通知期间再次提交会被状态所有者拒绝，避免嵌套提交导致检查器先看到 `r14`、再看到旧的 `r13`。这段简化代码的属性是字符串和数字，实际含嵌套可变值时也要按其结构复制冻结或采用其他不可变约定。

一个监听器若抛错，异常会向提交调用者传播并停止当前快照中的后续监听器；文档修订已经在通知前提交，`finally` 会解除同步提交保护。若每个视图都必须收到通知，可在通知边界另行定义错误隔离或重试；这会改变当前错误语义，不必为本例另造事件队列。

![通知器把同一不可变修订送给画布和检查器；视图卸载时取消订阅](resources/design-patterns-in-practice-observer-lifecycle.svg)

订阅随视图生命周期结束：卸载时调用返回的取消函数。`Set` 本身按插入顺序保存不同监听器；本文使用快照，ECMAScript 的实时迭代规则只解释为何没有复制时删除下一位会跳过它、而新增项可能加入本轮。具体规则见来源条目中的 §§24.2.4.4、24.2.4.17–18 和 24.2.6.1。

浏览器的 `EventTarget` 也让对象直接管理监听器，并支持注册与移除；它是直接观察者式 API 的类比，但还有事件捕获、冒泡和取消语义。页面级事件分发细节见[浏览器怎样查询、更新 DOM 并响应用户输入？](../../frontend/browser-apis/dom-manipulation-and-events.md)；应用层消息总线与监听器重入见[JavaScript 事件总线在监听器中重入时怎样保持顺序？](../../frontend/browser-apis/event-bus-and-observer-patterns.md)。

**publish-subscribe（发布订阅）**把消息按主题交给中介路由；发布者只知道主题，不必知道具体接收者。例如中介可持有 `Map<topic, Set<listener>>`，订阅者收到返回的取消函数后从相同主题集合中移除自己。若多个独立插件要监听 `document:saved`，这种路由可能减少直接引用；但主题字符串和跨模块调用也会让消息来源更难追踪。画布和检查器天然属于这份文档，直接订阅文档通知器更容易沿着对象找到依赖；父子组件只有一个回调时，普通回调就够了。有多个接收者也不意味着必须创建全局事件总线。

## 共享实例有明确范围时，才用单例

若一个编辑器运行时要求所有面板使用同一份组件注册表，必须先说明“一份”指哪个范围。**singleton（单例）**组合了唯一实例与全局访问点；它不能自动保证浏览器所有标签、worker（工作线程）、进程或重复模块副本共享同一对象。

多数编辑器只需由每个应用组合入口创建一个 `EditorRuntime`，再把注册表传给画布、检查器和命令处理器。这样一个应用范围内确实共享同一实例，但测试可以独立创建另一个运行时。JavaScript 模块变量只在该模块实例范围共享；它不等于一个页面只有一个编辑器，更不保证不同模块副本共用实例。全局单例则隐藏依赖，容易让两个编辑器实例或不同测试相互污染。如果类的构造器仍公开，`getInstance()` 访问器也不能阻止调用方 `new` 出额外对象。只有全局访问点本身能解决明确问题时才承担这种耦合；否则显式创建和传递更容易观察生命周期。

## 用设计原则检查模式是否合适

沿着“插入空标题”流程检查责任边界：工厂只负责节点初值与 ID；编辑期策略负责节点结构；状态所有者对策略结果作决定并提交修订；观察者只通知已提交的只读状态；发布服务另行检查指定修订能否成为公开版本。发布失败不会撤销可以保存、预览和继续编辑的草稿。

添加一种新节点类型时，开发者可能仍要修改类型定义、渲染器和发布规则。工厂或策略不会自动兑现开闭原则；只有新变化能在局部扩展，并且调用契约仍稳定，修改范围才真的缩小。观察者省去逐个调用视图的依赖，但订阅清理、文档只读和错误传播仍需明确。上层流程依赖通知契约、下层通知器实现该契约，是依赖倒置的一种接法；模式应配合变化边界，而非成为新的清单。

本篇沿合成 revision 12 插入空标题走到 revision 13；[页面文档和发布快照的数据模型](low-code-editor-data-model.md)则从 revision 12 另行把 `heading-1` 文案从“首页”改为“欢迎”，得到它自己的 revision 13。两次操作是各自独立的教学路径，不表示同一文档连续从 revision 13 改到 revision 13。本篇用 `nodes` 数组聚焦对象协作，完整案例以 `rootIds` 和按 ID 索引的节点表保存文档树；撤销、持久化和发布快照契约见数据模型章节。组件数据由哪些前端对象拥有见[前端架构边界](frontend-architecture-boundaries.md)。

> [!info]- 来源
> - GoF 对模式适用情境、约束、结果与权衡的说明，及文档编辑器案例：[Gamma、Helm、Johnson、Vlissides, *Design Patterns: Elements of Reusable Object-Oriented Software*](https://www.oreilly.com/library/view/design-patterns-elements/0201633612/)。
> - `Set` 删除、默认值迭代入口与迭代器行为：[ECMAScript 2026, Keyed Collections, §§24.2.4.4、24.2.4.17–18、24.2.6.1](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-set-iterator-objects)，2026-11-12 核对。
> - `EventTarget` 的监听列表、注册、移除与事件分发：[WHATWG DOM Standard, §§2.7、2.9](https://dom.spec.whatwg.org/#interface-eventtarget)，2026-11-12 核对。
> - 设计原则与模式的关系：[Robert C. Martin, “Design Principles and Design Patterns” (2000), p. 4](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。
