# 弱集合与弱引用能保证什么？

报表页面关闭后，某个记录对象只应由仍在使用它的界面持有。`WeakMap`（弱映射）可以把元数据关联到对象，而不单独延长键的生命周期；`WeakRef`（弱引用）和 `FinalizationRegistry`（最终化注册表）也不能提供及时、必达的清理保证。本章先界定“弱持有”，再说明它适合与不适合承担的责任。常规 `Map`（映射）的强引用与身份键见[何时使用 Map、Set 或普通对象？](./map-and-set.md)。

本章的对象身份示例是两条同业务 id 的输入：

~~~javascript
const first = { reportId: "r-104", amount: 0 };
const retry = { reportId: "r-104", amount: 120 };
~~~

## WeakMap 关联数据，但不拥有键

`WeakMap`（弱映射）把可弱持有的键与值关联起来。只要键仍从程序其他强引用路径可达，就能读取对应值；当键不再存活时，条目本身不会保住它。`WeakMap` 不提供 `size`、键枚举或 `forEach`，因为这些接口会让程序观察到不确定的回收时点。

对象是最常见的键。ECMAScript 2023 起，非注册 `Symbol`（符号）也可作为弱键；`Symbol.for` 创建的注册 `Symbol` 不能弱持有。

~~~javascript
const rowMetadata = new WeakMap();

rowMetadata.set(first, { selected: true, row: first });
rowMetadata.get(first); // { selected: true, row: first }
rowMetadata.has(retry); // false：键是另一个对象身份

const privateKey = Symbol("row metadata");
rowMetadata.set(privateKey, { source: "non-registered symbol" });

const sharedKey = Symbol.for("shared");
rowMetadata.has(sharedKey); // false
// rowMetadata.set(sharedKey, {}); // TypeError
~~~

`WeakMap` 条目只在键对象仍存活时提供关联值；即使值反向引用键，这条弱键关联也不会单独保住键。上例的 `rowMetadata` 若还有另一个强引用路径指向 `first`，键和其值仍可读；若其他路径都断开，条目本身不会使两者继续存活。不要把这条规则误解为“只要用 `WeakMap`，相关对象就一定能回收”。

适合 `WeakMap` 的情况是给其他代码所有的节点或类实例保存私有元数据；对象生命周期由外部所有者决定，元数据不需要独立枚举。若需要列出、计数或明确删除所有缓存项，普通 `Map` 加显式清理更合适。

## WeakSet 只跟踪可弱持有的成员

`WeakSet`（弱集合）按身份弱跟踪对象或非注册 `Symbol`，提供 `add`、`has`、`delete`，但没有遍历和 `size`。它适合标记由其他部分拥有的对象是否已经处理过：

~~~javascript
const processedRows = new WeakSet();

function processOnce(row) {
  if (processedRows.has(row)) return;
  processedRows.add(row);
  // 对这个对象身份执行一次处理
}

processOnce(first);
processedRows.has(first); // true
processedRows.has(retry); // false
~~~

这里按对象身份区分记录，不按 `reportId` 或字段内容去重。需要按业务 id 去重时应使用普通 `Map` 或 `Set`，并选择明确的键。

## WeakRef 和 FinalizationRegistry 不提供释放时限

`WeakRef`（弱引用）的目标可以是对象或非注册 `Symbol`（符号）。`deref()` 在目标仍可用时返回该目标，否则返回 `undefined`。成功取到目标后，规范要求该目标在当前 ECMAScript 代码执行完成前不被回收，因此同一次执行内可先检查再使用；之后是否仍存活不受保证。

~~~javascript
const weakRow = new WeakRef(first);
const row = weakRow.deref();

if (row !== undefined) {
  rowMetadata.set(row, { selected: true });
}

const weakSymbolTarget = Symbol("weak reference target");
new WeakRef(weakSymbolTarget).deref() === weakSymbolTarget; // true：非注册 Symbol 也可作为目标
~~~

`FinalizationRegistry`（最终化注册表）可在目标不可达后请求运行清理回调，但对象何时回收、回调何时运行都没有保证；回调可能延迟很久，程序退出前也可能永不运行。只要注册仍有效，注册表就强持有 `heldValue`；调用 `unregister(token)` 可以提前移除对应注册。目标本身不能直接作为 `heldValue`（会抛 `TypeError`）；若 `heldValue` 间接引用目标，这条强路径会使目标继续存活，回调也就无法因它不可达而运行。

~~~javascript
const registry = new FinalizationRegistry(label => {
  console.log("eventual cleanup hint:", label);
});

let temporaryRow = { reportId: "temporary" };
const unregisterToken = {};
registry.register(temporaryRow, "temporary row", unregisterToken);
// registry.register(temporaryRow, temporaryRow); // TypeError
// registry.register(temporaryRow, { row: temporaryRow }); // 注册合法，但 heldValue 会保住目标
temporaryRow = null;
registry.unregister(unregisterToken); // 可显式取消这条注册
~~~

因此，这些 API 适合不影响正确性的缓存提示、附加元数据或机会式清理；不适合释放文件、网络连接、锁、计费记录、UI 状态或任何要求及时发生的动作。需要确定结束时间时，由明确的所有者调用 `dispose`、`removeEventListener`、`clearInterval` 或对应的清理函数。

对象仍被保留时，应找出强引用链，而不是等待最终化。堆保留路径的诊断见[对象为什么在不再有用后仍留在内存中？](../runtime/javascript-garbage-collection-and-retained-objects.md)。

> [!info]- 来源
> - WeakMap / WeakSet 的键资格、弱键值关系和不可枚举约束：[ECMAScript 2026 §24.3–24.4](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - WeakRef 目标和构造：[ECMAScript 2026 §26.1.1.1](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-weak-ref-target)；`deref()` 保活当前代码执行：[§26.1.3.2](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-weak-ref.prototype.deref)。
> - FinalizationRegistry 注册目标、heldValue 和取消注册：[ECMAScript 2026 `FinalizationRegistry.prototype.register`](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-finalization-registry.prototype.register)；对象与注册表清理模型：[§26.2](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-finalization-registry-objects)、[§9.9](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-weakref-processing-model)。
> - 运行时实际核对：Node.js v26.11.1 / V8 14.6.202.34-node.37，2026-11-06；核对目标构造、键资格和同步 `deref()` 行为，不以一次运行推断最终化时序。
