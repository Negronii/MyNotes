# What do weak collections and weak references guarantee? / 弱集合和弱引用能保证什么？

**Core answer / 核心回答：** WeakMap and WeakSet associate or track a key without making it strongly reachable through that entry. WeakRef and finalization callbacks are opportunistic: the language does not promise when collection or cleanup occurs. Use weak references to avoid ownership, never as a correctness-critical release schedule. / WeakMap 和 WeakSet 可关联或跟踪键，而不会通过该条目强持有键。WeakRef 和最终化回调只适合机会式行为：语言不保证回收或清理的时机。弱引用用于避免所有权，不可作为正确性关键的释放计划。

## What a WeakMap holds / WeakMap 持有和不持有什么

A WeakMap associates a weakly held key with a strongly held value. The entry does not by itself keep the key alive. WeakMap has no enumeration, size, or forEach because revealing which keys remain would expose nondeterministic garbage-collection timing. / WeakMap 将弱持有的键与强持有的值关联。条目本身不会使键保持存活。WeakMap 没有枚举、size 或 forEach，因为暴露仍存在的键会让程序观察不确定的垃圾回收时机。

Since ECMAScript 2023, keys may be objects or non-registered symbols. Symbol.for symbols are registered and cannot be weak keys. Older runtimes may support only object keys, so check the target runtime if symbol keys matter. / 自 ECMAScript 2023 起，键可为对象或非注册 Symbol。Symbol.for 创建的 Symbol 已注册，不能作为弱键。较旧运行时可能只支持对象键；需要 Symbol 键时应检查目标运行时支持。

~~~javascript
const metadata = new WeakMap();

function attachMetadata(node, info) {
  metadata.set(node, info);
}
function readMetadata(node) {
  return metadata.get(node);
}

const privateSymbol = Symbol("metadata");
metadata.set(privateSymbol, { source: "ES2023 non-registered symbol key" });

const registered = Symbol.for("shared");
metadata.has(registered); // false
// metadata.set(registered, {}); // TypeError
~~~

Typical uses include metadata keyed by objects owned elsewhere, or data associated with class instances without adding a public property. Even if the WeakMap value refers back to its key, the entry alone does not keep that key alive; another strong path to the key can still keep it alive. / 常见用途包括为其他代码持有的对象保存元数据，或为类实例关联数据而不添加公开属性。即使 WeakMap 的值又引用该键，条目本身也不会让键存活；其他强引用路径仍可能保留它。

## When WeakSet fits / 何时适合使用 WeakSet

WeakSet weakly tracks objects or non-registered symbols and supports membership operations, but no enumeration or size. It is useful for identity-based “seen” tracking when retaining the tracked value would be undesirable. / WeakSet 弱持有对象或非注册 Symbol，只提供成员操作，没有枚举或 size。若不希望跟踪操作延长对象生命周期，可用它按身份记录“已见过”的值。

~~~javascript
const processed = new WeakSet();

function processOnce(value) {
  if (processed.has(value)) return;
  processed.add(value);
  // perform work once for this identity
}
~~~

A normal Set or Map strongly retains members or keys. Use one when iteration, counting, or deterministic lifetime management matters. / 普通 Set 或 Map 会强持有成员或键；需要遍历、计数或确定生命周期时使用普通集合。

## What WeakRef and finalization cannot promise / WeakRef 与最终化不能承诺什么

WeakRef and FinalizationRegistry were standardized in ES2021. WeakRef.deref() returns its target if still available, otherwise undefined. FinalizationRegistry may schedule a cleanup callback after a target becomes unreachable. Neither collection time nor callback time is guaranteed, and the callback may not run before program exit. Do not use these APIs for correctness-critical resource release, accounting, or prompt UI updates. / WeakRef 和 FinalizationRegistry 于 ES2021 标准化。WeakRef.deref() 在目标仍可用时返回它，否则返回 undefined。FinalizationRegistry 可能在目标不可达后安排清理回调。回收和回调时机均无保证，程序退出前也可能不执行。不要用这些 API 处理正确性关键的资源释放、计数或及时 UI 更新。

If deref() returns a target, ECMAScript keeps it alive until the current job completes. This keeps behavior consistent within that job but does not promise that the target remains afterward. / deref() 返回目标后，ECMAScript 会使它至少存活到当前 job 结束，以保证该 job 内行为一致；这不承诺目标之后仍存活。

The [ECMAScript keyed collections](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-weakmap-objects) and [weak-reference specification](https://tc39.es/ecma262/2025/multipage/managing-memory.html) permit implementation-dependent collection latency. Reachability models and heap-diagnostic context are covered by [Event Loop and Host Scheduling / 事件循环与宿主调度](../runtime/event-loop.md).
