# 弱集合与弱引用能保证什么？

报表界面要给某个记录对象附加“已选中”这样的状态，但不想因为这份附加数据让记录对象一直留在内存里。`WeakMap`（弱映射）可以按对象身份存这类元数据，而这条关联本身不会延长键对象的生命周期。不过它不会替你解除事件监听器等其他强引用；若关掉报表后旧行仍留在内存中，要另外查找实际的保留链。`WeakRef`（弱引用）和 `FinalizationRegistry`（最终化注册表）也不能保证资源被及时、必然地清理。普通 `Map`（映射）怎样以对象身份为键并强持有它，见[何时使用 Map、Set 或普通对象？](./map-and-set.md)。

本章用两条记录做示例：一次报表筛选中，首次请求的 `first` 和重试得到的 `retry` 业务 id 都是 `r-104`，但它们是两个不同的对象：

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

`WeakMap` 把“可被弱持有”的键与值关联起来。只要程序还通过其他路径持有键，就能用它读到关联值；一旦键不再被其他路径引用，这条关联不会让它继续存活。`WeakMap` 不提供 `size`、键枚举或 `forEach`：垃圾回收的时机不确定，若允许枚举，程序就能观察到键何时被回收，而这正是语言刻意不暴露的。

对象是最常见的键。从 ECMAScript 2023 起，非注册的 `Symbol`（符号）也可以作为弱键；用 `Symbol.for` 创建的注册 `Symbol` 则不能被弱持有。两者的区别在于：每次调用 `Symbol("row metadata")` 都创建一个新符号，即使描述相同身份也不同；而重复调用 `Symbol.for("shared")` 总是从全局注册表取回同一个符号，它永远可以被重新取得，所以不能作弱键。

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

注意 `rowMetadata` 中的值通过 `row` 属性反向引用了 `first`。弱映射按键是否可达来决定条目的去留：只要别处还持有 `first`，就能用 `rowMetadata.get(first)` 读回值；若外部所有强引用都断开，值对键的这条反向引用不会让二者互相保活。当然，本页的 `first` 变量本身就是一条强引用；若代码把 `rowMetadata.get(first)` 的返回值存进普通变量，也能沿它的 `row` 属性回到键，同样构成强引用。反过来，任何其他强引用路径（例如下一章中忘记移除的监听器）都会让键继续存活，`WeakMap` 不会替程序断开它。

`WeakMap` 适合给别的代码拥有的节点或类实例附加私有元数据：对象的生命周期由外部所有者决定，元数据也不需要单独列出。若需要列出、计数或集中管理缓存项，就用普通 `Map`，由它的所有者强引用这些对象并显式删除条目。

## WeakSet 只跟踪可弱持有的成员

`WeakSet`（弱集合）与 `WeakMap` 类似，按身份弱持有对象或非注册 `Symbol`，只提供 `add`、`has`、`delete`，没有遍历和 `size`。它适合标记别处拥有的对象是否已经处理过：

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

这里按对象身份区分记录，而不是按 `reportId` 或字段内容去重。若要按业务 id 去重，应改用普通 `Map` 或 `Set`，以明确选定的值作为键。

## WeakRef 和 FinalizationRegistry 不提供释放时限

`WeakMap` 和 `WeakSet` 只能按已有的键去查。`WeakRef` 则直接持有一个对目标的弱引用，目标可以是对象或非注册 `Symbol`。`deref()` 在目标还存活时返回目标，否则返回 `undefined`。若返回了目标，规范只保证它在当前这段同步执行期间不会被回收；宿主也许会保留更久，但代码不能依赖这一点。

规范的做法是维护一张临时保活列表（kept objects）：`deref()` 返回目标时，以及构造 `WeakRef` 时，都会把目标加入这张列表。浏览器在微任务检查点结束时清空它，而不是执行到 `await` 时就立即清空。因此，即使创建目标的函数已经返回、局部变量已经离开作用域，在同一段同步执行中首次 `deref()` 仍能拿到刚构造的目标（后面的 `makePendingRowRef` 示例就依赖这一点）。若跨异步等待后还要使用目标，应把 `deref()` 的结果存进普通局部变量，让这条强引用跨过等待。

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

下面用定时器演示跨异步等待。`makePendingRowRef()` 返回的引用被立即交给 `readAfterRefresh`，所以首次 `deref()` 与 `new WeakRef(pendingRow)` 处在同一段同步执行中，一定能拿到目标；若传入的是早已跨过任务边界的引用，首次读取就可能得到 `undefined`。函数先把取到的对象存进局部变量 `row`，让这条强引用跨过定时器等待；如果只保留弱引用，等待后再 `deref()` 可能得到 `undefined`。

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

`FinalizationRegistry` 让程序在目标被回收后（可能）收到一次回调。`register(target, heldValue[, token])` 登记一个目标：注册表弱持有 `target` 和可选的取消令牌 `token`（须为对象或非注册 `Symbol`），并在注册有效期间强持有 `heldValue`（暂存值）。清理回调运行时，收到的唯一参数就是 `heldValue`，本例中是一个标签字符串。由于注册表不强持有令牌，调用方可以自己保存令牌用于取消注册，而不会通过注册表让 `temporaryRow` 保持存活。`heldValue` 则不同：目标本身不能直接作为 `heldValue`（会抛 `TypeError`）；若 `heldValue` 的某个属性引用了目标，这条强引用会让目标一直存活，回调也就永远不会因目标不可达而运行。调用 `unregister(token)` 可以提前取消对应的注册。即使一切写对，对象何时回收、回调何时运行也都没有保证：回调可能很久之后才运行，程序退出前也可能根本不运行。

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

因此，这些弱引用 API 适合不影响正确性的场景：缓存提示、附加元数据或“顺便”的清理；不适合用来关闭文件、网络连接、释放锁、写计费记录、更新 UI 状态，或任何必须及时发生的动作。需要确定的结束时机时，应由明确的所有者调用 `dispose`、`removeEventListener`、`clearInterval` 或对应的清理函数。

如果本页的 `first` 在报表关闭后仍然存活，`WeakMap` 不会替你清除让它存活的其他路径。下一篇沿用同一条 `r-104` / `owner: Ada` 记录，检查 `window` 上的 resize 监听器、闭包中的 `rows` 以及调用方持有的清理函数，并用堆快照找出实际的保留者：[对象为什么在不再有用后仍留在内存中？](../runtime/javascript-garbage-collection-and-retained-objects.md)。

> [!info]- 来源
> - `WeakMap` / `WeakSet` 的弱键关系、无枚举约束及对象/非注册 Symbol 资格：[ECMAScript 2026 §24.3–24.4](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)、[§9.13 `CanBeHeldWeakly`](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-canbeheldweakly)；非注册 Symbol 的资格在 [ECMAScript 2023 §9.14](https://tc39.es/ecma262/2023/multipage/executable-code-and-execution-contexts.html#sec-canbeheldweakly) 已纳入规范。
> - `WeakRef` 目标资格与构造：[ECMAScript 2026 §26.1.1.1](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-weak-ref-target)；构造与 `deref()` 都会加入临时保活列表：[§26.1.3.2](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-weak-ref.prototype.deref)、[§9.10 `ClearKeptObjects`](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-clearkeptobjects)、[§9.11 `AddToKeptObjects`](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-addtokeptobjects)。浏览器宿主在微任务检查点末清空 kept objects：[WHATWG HTML §8.1.7.3 Processing model](https://html.spec.whatwg.org/multipage/webappapis.html#perform-a-microtask-checkpoint)，核验于 2026-11-12。
> - `Symbol()` 每次构造的身份与共享注册表查找：[ECMAScript 2026 §20.4.1.1、§20.4.2.2](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-symbol.for)。
> - FinalizationRegistry 的 target、heldValue、可选弱 unregister token 及注册取消：[ECMAScript 2026 §26.2.3.2–3](https://tc39.es/ecma262/2026/multipage/managing-memory.html#sec-finalization-registry.prototype.register)、[§9.12 `CleanupFinalizationRegistry`](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-cleanup-finalization-registry)、[§9.13 `CanBeHeldWeakly`](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-canbeheldweakly)、[§9.9.1 Objectives](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-weakref-processing-model)。
> - 本地重放：Node.js v26.13.0 / V8 14.6.202.34-node.40，2026-11-12；运行目标类型、符号键、同值 heldValue 异常和跨 `await` 的局部强引用示例，不触发 GC 或推断最终化时序。
