# 页面编辑器何时需要设计模式？

沿用合成的页面编辑器案例，编辑者要创建标题、按钮等节点，为不同类型校验配置，通知画布和检查器刷新，并共享组件定义。**design pattern（设计模式）**为这些重复结构取名，但模式本身不会替你决定状态所有者、权限边界或对象生命周期。先说清问题，再看模式是否能让变化集中而仍容易跟踪。

模式有代价：额外类型、注册步骤、调用层和清理责任。若间接层没有减小真实修改范围，普通函数或条件分支更清楚。

## 创建规则变多时，用工厂集中入口

**factory（工厂）**把创建规则放在一处：生成稳定 ID、填入默认属性并拒绝未知类型。它通常先是一个函数，不必马上设计成复杂层级。这样的简单工厂函数不自动等同于《设计模式》中的 Factory Method（工厂方法）或 Abstract Factory（抽象工厂）模式。

~~~javascript
const defaults = new Map([
  ['heading', { text: '新标题', level: 2 }],
  ['button', { label: '按钮', variant: 'primary' }],
]);

let nextId = 1;

function createNode(type) {
  const initialProps = defaults.get(type);
  if (!initialProps) throw new RangeError('unknown component type');
  const id = 'node-' + nextId++;
  return { id, type, props: { ...initialProps }, children: [] };
}

const heading = createNode('heading');
// heading.id === 'node-1'; createNode('constructor') throws RangeError
~~~

多个入口若各自生成默认字段和 ID，很容易得到不一致节点，共用入口就有价值。若只在一处创建固定对象，直接写对象更简单。这里的 Number 计数器只在当前模块运行期间、且计数值仍处于安全整数范围时保证 ID 不重复；可持久化文档或协作编辑需要跨重启、跨窗口不冲突的 ID 生成方案。工厂生成的草稿并不代表权限或发布校验已经完成。

## 行为可互换时，用策略

**strategy（策略）**把不同算法放进同一调用契约。编辑器可按组件类型选择配置校验器；通用 schema 已先确认 node 是对象、type 是字符串且 props 是对象，这些策略只检查对应类型的特有字段并返回错误集合。

~~~javascript
const validators = new Map([
  ['heading', node => (
    typeof node.props.text === 'string' ? [] : ['标题文本必须是字符串']
  )],
  ['button', node => (
    typeof node.props.label === 'string' ? [] : ['按钮需要标签']
  )],
]);

function validateNode(node) {
  const validate = validators.get(node.type);
  return validate ? validate(node) : ['未知组件类型：' + node.type];
}

validateNode({
  id: 'button-1',
  type: 'button',
  props: { label: '发布' },
});
// []
~~~

调用者不需要理解每种组件的检查细节。新增策略是否真的避免集中式分支，取决于注册、类型管理和错误契约是否也统一。若规则少而稳定，普通 `switch` 可能更好。策略不能取代输入校验或授权检查。

## 多个视图订阅同一修订时，用观察者

**observer（观察者）**结构中，状态主体直接维护订阅者并通知变化。下面用 `DocumentNotifier`（文档通知器）只展示通知职责；文档数据仍由上游状态所有者持有。订阅者应能取消订阅，避免卸载视图继续被引用。浏览器 `EventTarget` 也是这种直接注册到目标对象的观察者式 API，见[DOM 事件与交互](../../frontend/browser-apis/dom-manipulation-and-events.md)。

~~~javascript
class DocumentNotifier {
  #listeners = new Set();

  subscribe(listener) {
    this.#listeners.add(listener);
    return () => this.#listeners.delete(listener);
  }

  notify(document) {
    for (const listener of this.#listeners) listener(document);
  }
}

const notifier = new DocumentNotifier();
const unsubscribe = notifier.subscribe(document => {
  console.log('画布收到修订', document.revision);
});

notifier.notify({ revision: 13 });
unsubscribe();
~~~

该循环是同步通知：若一个 listener 抛错，异常会向调用方传播，后续 listener 不会继续收到本轮通知；遍历期间新增或删除 listener 也遵循 Set 迭代器的实时行为。这个小例没有隔离回调异常或冻结订阅快照。

**publish-subscribe（发布订阅）**常通过主题或中介路由消息，让发布者不必掌握每个接收者。若插件要监听 `document:saved`，典型实现会从 `listenersByTopic.get(topic)` 取得 Set 并同步通知，其中每个 Set 保存该主题的订阅者；取消时从同一 Set 删除 listener。它可能减少直接依赖，但全局事件名和隐式调用会让修改来源难以追踪。简单父子组件回调已足够时，不用事件总线。实际 API 可能混合两种形式，应看订阅由谁持有、消息如何路由。

## 共享实例有明确范围时，才用单例

**singleton（单例）**让某个范围通过统一入口访问一个共享实例。例如一个编辑器应用实例可以持有一份组件注册表。在 JavaScript 中，模块变量通常由当前模块实例共享；worker、进程、重复加载的模块副本之间不自动共享同一个对象。

全局单例会隐藏依赖，也可能让多个编辑器或测试互相污染。显式创建 `EditorRuntime` 并传给使用者通常更易测试。必须说清“一份”是每个模块、应用、进程还是其他范围。若该类仍暴露公有构造器，调用者通常仍能直接创建额外实例，访问器并不会自动阻止这种创建。

## 用设计原则检查模式是否合适

工厂和策略可支持开闭原则，但若它们没有缩小修改范围，就不需要硬套。观察者让变化通知多个视图；依赖倒置要求高层编辑流程依赖通知契约，而非绑死具体全局总线。每个订阅者的生命周期也仍需明确。

新增图片节点时，工厂建立默认配置、校验策略检查属性、状态所有者接受“插入图片”命令，生成新修订后再通知画布。模式说明局部对象怎样协作；文档结构、撤销历史、发布版本与冲突处理见[页面文档和发布快照的数据模型](low-code-editor-data-model.md)。组件之间的数据所有权见[前端架构边界](frontend-architecture-boundaries.md)。

> [!info]- 来源
> - 工厂、策略、观察者等模式的适用情境和权衡：[Gamma、Helm、Johnson、Vlissides, Design Patterns: Elements of Reusable Object-Oriented Software](https://www.oreilly.com/library/view/design-patterns-elements/0201633612/)。
> - 模式与设计原则应服务于变化边界：[Robert C. Martin, Principles and Patterns](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。
> - Set 的实时迭代语义：[ECMAScript 2026, Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-set-iterator-objects)。
