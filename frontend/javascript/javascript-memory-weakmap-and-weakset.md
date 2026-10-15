# JavaScript Memory, WeakMap, WeakSet, and WeakRef / JavaScript 内存、WeakMap、WeakSet 与 WeakRef

**Key terms / 关键词:** reachability 可达性 · weak key 弱键 · garbage collection 垃圾回收 · finalization 清理回调

JavaScript specifies object identity, reachability-related weak collection behavior, and observable results. It does not require values to live on a “stack” or “heap,” prescribe one garbage collector, or promise when collection occurs. Treat weak references as a way to avoid owning a key, never as a predictable cleanup schedule. / JavaScript 规定对象身份、弱集合相关行为和可观察结果，但不要求值存放在“栈”或“堆”中，不规定唯一的垃圾回收算法，也不保证何时回收。弱引用用于避免强持有某个键，不能当作可预测的清理计划。

## WeakMap / 弱映射

A WeakMap associates a weakly held key with a strongly held value. The entry does not by itself keep its key alive. It has no enumeration, `size`, or `forEach`, because exposing which keys remain would make garbage-collection timing observable. / WeakMap 把弱持有的键关联到强持有的值。该条目本身不会让键保持存活。它没有枚举、`size` 或 `forEach`，因为暴露哪些键仍存在会使垃圾回收时机变得可观察。

Since ECMAScript 2023, keys may be objects or non-registered symbols. `Symbol.for(...)` symbols are registered and cannot be weak keys. Older runtimes may support only object keys, so check the target runtime if symbol keys are needed. / 从 ECMAScript 2023 起，键可以是对象或非注册 Symbol。`Symbol.for(...)` 创建的注册 Symbol 不能作为弱键。较旧运行时可能只支持对象键；需要 Symbol 键时应检查目标运行时支持情况。

```javascript
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
```

Typical uses include metadata keyed by objects owned elsewhere, or data associated with class instances without creating a public property. The WeakMap entry does not by itself keep its key alive, even when the value refers back to the key; another strong path to the key, such as an externally retained value, can still keep it alive. / 常见用途包括为其他代码持有的对象保存元数据，或为类实例关联数据而不增加公开属性。WeakMap 条目本身不会让键保持存活，即使值又引用该键也是如此；但若存在其他强引用路径（例如值被外部继续持有），键仍会存活。

## WeakSet / 弱集合

A WeakSet weakly tracks objects or non-registered symbols and supports membership operations, but no enumeration or size. Use it for identity-based “seen” tracking when retaining the tracked value would be undesirable. / WeakSet 弱持有对象或非注册 Symbol，只提供成员操作，没有枚举或 size。若不希望跟踪操作本身延长对象生命周期，可用它按身份记录“已见过”的对象。

```javascript
const processed = new WeakSet();

function processOnce(value) {
  if (processed.has(value)) return;
  processed.add(value);
  // perform work once for this identity
}
```

A normal Set or Map strongly retains its members or keys. Use one when iteration, counting, or deterministic lifetime management matters. / 普通 Set 或 Map 会强持有成员或键。需要枚举、计数或确定生命周期时应使用普通集合。

## WeakRef and FinalizationRegistry / 弱引用与最终化注册表

`WeakRef` and `FinalizationRegistry` were standardized in ES2021. A WeakRef lets a program try to access a target without making that target strongly reachable through the reference. `deref()` returns the target if it is still available, otherwise `undefined`. A FinalizationRegistry may schedule cleanup after a target becomes unreachable. Neither the collection time nor the callback time is guaranteed; cleanup may be delayed or omitted before program exit. Do not use either API for correctness-critical resource release, accounting, or prompt UI updates. / `WeakRef` 和 `FinalizationRegistry` 于 ES2021 标准化。WeakRef 允许程序尝试访问目标，但不会通过该引用强持有目标。`deref()` 在目标仍可用时返回它，否则返回 `undefined`。FinalizationRegistry 可能在目标不可达后安排清理回调，但回收和回调时机都没有保证；程序退出前回调也可能未执行。不要把这些 API 用于正确性关键的资源释放、计数或及时 UI 更新。

If `deref()` returns a target, ECMAScript keeps it alive until the current job completes. This provides consistency within that job; it does not promise that the target remains afterward. / 如果 `deref()` 返回目标，ECMAScript 会使它至少存活到当前 job 结束，以保证该 job 内行为一致；这不承诺目标之后仍然存活。

See [ECMAScript keyed collections](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-weakmap-objects) and [weak references and finalization](https://tc39.es/ecma262/2025/multipage/managing-memory.html). The specification explicitly permits implementation-dependent collection latency. / 详见 [ECMAScript 键控集合规范](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-weakmap-objects) 和 [弱引用与最终化规范](https://tc39.es/ecma262/2025/multipage/managing-memory.html)。规范明确允许回收延迟由实现决定。

**Interview answer / 面试回答:** WeakMap and WeakSet let object identity be associated or tracked without the collection itself keeping the key alive. Their lack of enumeration prevents programs from depending on nondeterministic garbage-collection timing. WeakRef and finalization callbacks are likewise nondeterministic, so use them only for opportunistic behavior. / WeakMap 和 WeakSet 可关联或跟踪对象身份，而不会由集合本身强持有键。它们不能枚举，避免程序依赖不确定的垃圾回收时机。WeakRef 和最终化回调同样不确定，只适合可有可无的优化行为。

Related: [Map and Set / JavaScript 中的 Map 与 Set](./map-and-set.md); [Event Loop and Host Scheduling / 事件循环与宿主调度](../runtime/event-loop.md).
