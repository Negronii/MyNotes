# 弱集合与弱引用能保证什么？

同一次报表筛选中，`first` 和 `retry` 都带业务 id `r-104`，却是两个对象。界面若要给某个对象身份附加选中状态，`WeakMap`（弱映射）可以存元数据，而不因这条关联本身延长键的生命周期。它不会替你解除监听器等其他强引用路径；若关窗后旧行还留在内存里，应另查实际保留链。`WeakRef`（弱引用）和 `FinalizationRegistry`（最终化注册表）也不能给确定的资源清理提供及时、必达的保证。普通 `Map`（映射）的身份键与强持有见[何时使用 Map、Set 或普通对象？](./map-and-set.md)。

本章的对象身份示例是两条同业务 id 的输入：

~~~javascript
const first = {
  reportId: "r-104",
  amount: 0,
  owner: { id: "u-17", name: "Ada" },
};
const retry = {
  reportId: "r-104",
  amount: 120,
  owner: { id: "u-17", name: "Ada" },
};
~~~

## WeakMap 关联数据，但不拥有键

`WeakMap` 把可弱持有的键与值关联起来。只要程序还通过其他路径持有键，就能用这个键读取关联值；如果键不再存活，这条关联不会把它救回来。`WeakMap` 不提供 `size`、键枚举或 `forEach`：回收时点不确定，枚举会让程序观察原本不能观察的弱键状态。

对象是最常见的键。ECMAScript 2023 起，非注册 `Symbol`（符号）也可作为弱键；`Symbol.for` 创建的注册 `Symbol` 不能弱持有。

每次调用 `Symbol("row metadata")` 都会创建一个新的符号，即使描述字符串相同，身份仍不同；重复调用 `Symbol.for("shared")` 则会从共享注册表中取回同一个符号。

~~~javascript
const rowMetadata = new WeakMap();

rowMetadata.set(first, { selected: true, row: first });
console.log(rowMetadata.get(first).selected, rowMetadata.get(first).row === first); // true true
console.log(rowMetadata.has(retry)); // false：业务 id 相同，键对象身份不同

const localSymbol = Symbol("row metadata");
rowMetadata.set(localSymbol, { source: "non-registered symbol" });

const sharedSymbol = Symbol.for("shared");
console.log(rowMetadata.has(sharedSymbol)); // false
try {
  rowMetadata.set(sharedSymbol, {});
} catch (error) {
  console.log(error.name); // TypeError：注册 Symbol 不能作弱键
}
~~~

`rowMetadata` 的值还反向引用了 `first`，但弱映射按键的可达性处理这条条目：只要别处仍持有 `first`，可以通过 `rowMetadata.get(first)` 读回值；若外部所有强路径都断开，键和值间的环不会单靠这条弱关联保活。本页仍可访问的 `first` 变量本身就是一条普通强路径；若代码把 `rowMetadata.get(first)` 的返回值保存到普通变量，之后也能沿该值的 `row` 属性回到键。反过来，任何其他强路径——例如下一章中的未移除监听器——仍会让键存活，WeakMap 不会替程序解除那条路径。

适合 `WeakMap` 的情况是给其他代码所有的节点或类实例保存私有附加元数据；对象生命周期由外部所有者决定，元数据不需要独立枚举。若要列出、计数或集中控制缓存项，就用普通 `Map`，并由其所有者强引用对象、显式删除条目。

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
console.log(processedRows.has(first)); // true
console.log(processedRows.has(retry)); // false：仍按对象身份区分

const symbolMarker = Symbol("non-registered marker");
processedRows.add(symbolMarker);
console.log(processedRows.has(symbolMarker)); // true
try {
  processedRows.add(Symbol.for("shared marker"));
} catch (error) {
  console.log(error.name); // TypeError：注册 Symbol 不可弱持有
}
~~~

这里按对象身份区分记录，不按 `reportId` 或字段内容去重。需要按业务 id 去重时应使用普通 `Map` 或 `Set`，并选择明确的键。

## WeakRef 和 FinalizationRegistry 不提供释放时限

`WeakRef` 的目标可以是对象或非注册 `Symbol`。`deref()` 在目标仍可用时返回目标，否则返回 `undefined`。如果返回了目标，规范只保证它在当前同步 ECMAScript 执行期间仍可用；宿主可能继续保活更久，但代码不能把这个延长当成保证。创建 `WeakRef` 时，构造函数也会把目标加入临时保活列表，所以本页后面的示例即使已离开 `pendingRow` 的局部作用域，刚构造完的目标仍能在同一次同步执行中首次 `deref()`。浏览器会在微任务检查点末尾清空这张列表；不是执行到 `await` 语法处就立即清空。跨异步任务若后续还要用目标，应把返回值保存在普通局部变量里，让这条强引用跨越等待。

~~~javascript
const weakRow = new WeakRef(first);
const row = weakRow.deref();

if (row !== undefined) {
  rowMetadata.set(row, { selected: true });
  console.log(row.reportId); // r-104：先检查，再在当前同步执行段使用
}

const weakSymbolTarget = Symbol("weak reference target");
console.log(new WeakRef(weakSymbolTarget).deref() === weakSymbolTarget); // true：非注册 Symbol 也可作目标
~~~

下面用定时器任务展示异步等待：这次调用把刚构造的引用立即交给 `readAfterRefresh`，因此首次 `deref()` 与 `new WeakRef(pendingRow)` 仍在同一次同步执行里；若传入早已跨过任务边界的引用，首次读取本身也可能走 `undefined` 分支。这里先把成功取到的对象存入 `row`，让普通强引用跨过定时器等待；如果只保留弱引用，等待后再 `deref()` 可能拿到 `undefined`。

~~~javascript
function makePendingRowRef() {
  const pendingRow = { reportId: "r-105" };
  return new WeakRef(pendingRow);
}

async function readAfterRefresh(ref) {
  const row = ref.deref();
  if (row === undefined) return undefined;
  await new Promise(resolve => setTimeout(resolve, 0));
  return row.reportId; // row 是局部强引用
}

readAfterRefresh(makePendingRowRef()).then(id => {
  console.log("after await =", id); // r-105
});
~~~

`FinalizationRegistry`（最终化注册表）的 `register(target, heldValue[, token])` 会弱持有目标和符合资格的可选取消令牌（对象或非注册 `Symbol`）；注册表则在注册项仍有效时强持有 `heldValue`（暂存值）。若清理回调运行，它唯一收到的参数就是 `heldValue`，本例中为标签字符串。注册表不会强持有 token；本例的调用方可以单独保存令牌来取消注册，而不会经由注册表保活 `temporaryRow`。但如果 `heldValue` 本身或其属性又引用目标，这条强路径会让目标继续存活，回调也就无法因它不可达而运行。对象何时回收、回调何时运行都没有保证；回调可能延迟很久，程序退出前也可能永不运行。调用 `unregister(token)` 可以提前移除对应注册；目标本身不能直接作为 `heldValue`（会抛 `TypeError`）。

~~~javascript
const registry = new FinalizationRegistry(heldValue => {
  console.log("eventual cleanup hint:", heldValue);
});

let temporaryRow = { reportId: "temporary" };
const unregisterToken = {};
registry.register(temporaryRow, "temporary row", unregisterToken);
try {
  registry.register(temporaryRow, temporaryRow);
} catch (error) {
  console.log(error.name); // TypeError：heldValue 不能与 target 是同一个值
}
// registry.register(temporaryRow, { row: temporaryRow }); // 注册合法，但 heldValue 会保住目标
temporaryRow = null;
console.log(registry.unregister(unregisterToken)); // true：可显式取消这条注册
~~~

因此，这些 API 适合不影响正确性的缓存提示、附加元数据或机会式清理；不适合释放文件、网络连接、锁、计费记录、UI 状态或任何要求及时发生的动作。需要确定结束时间时，由明确的所有者调用 `dispose`、`removeEventListener`、`clearInterval` 或对应的清理函数。

如果这页的 `first` 在报表关闭后还活着，WeakMap 并不会清掉造成保留的其他路径。下一篇沿同一 `r-104` / `owner: Ada` 记录检查 `window` 上的 resize listener、闭包中的 `rows` 以及调用方持有的清理函数，再用堆快照找实际保留者：[对象为什么在不再有用后仍留在内存中？](../runtime/javascript-garbage-collection-and-retained-objects.md)。

> [!info]- 来源
> - `WeakMap` / `WeakSet` 的弱键关系、无枚举约束及对象/非注册 Symbol 资格：[ECMAScript 2026 §24.3–24.4](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)、[§9.13 `CanBeHeldWeakly`](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-canbeheldweakly)；非注册 Symbol 的资格在 [ECMAScript 2023 §9.14](https://tc39.es/ecma262/2023/multipage/executable-code-and-execution-contexts.html#sec-canbeheldweakly) 已纳入规范。
> - `WeakRef` 目标资格与构造：[ECMAScript 2026 §26.1.1.1](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-weak-ref-target)；构造与 `deref()` 都会加入临时保活列表：[§26.1.3.2](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-weak-ref.prototype.deref)、[§9.10 `ClearKeptObjects`](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-clearkeptobjects)、[§9.11 `AddToKeptObjects`](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-addtokeptobjects)。浏览器宿主在微任务检查点末清空 kept objects：[WHATWG HTML §8.1.7.3 Processing model](https://html.spec.whatwg.org/multipage/webappapis.html#perform-a-microtask-checkpoint)，核验于 2026-11-12。
> - `Symbol()` 每次构造的身份与共享注册表查找：[ECMAScript 2026 §20.4.1.1、§20.4.2.2](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-symbol.for)。
> - FinalizationRegistry 的 target、heldValue、可选弱 unregister token 及注册取消：[ECMAScript 2026 §26.2.3.2–3](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-finalization-registry.prototype.register)、[§9.12 `CleanupFinalizationRegistry`](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-cleanup-finalization-registry)、[§9.13 `CanBeHeldWeakly`](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-canbeheldweakly)、[§9.9.1 Objectives](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-weakref-processing-model)。
> - 本地重放：Node.js v26.13.0 / V8 14.6.202.34-node.40，2026-11-12；运行目标类型、符号键、同值 heldValue 异常和跨 `await` 的局部强引用示例，不触发 GC 或推断最终化时序。
