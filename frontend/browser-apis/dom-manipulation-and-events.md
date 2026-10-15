**DOM Manipulation and Events / DOM 操作与事件**

DOM APIs expose tree mutation, events, and scheduling, but API guarantees differ from framework behavior and browser rendering choices. DOM 标准规定树与事件语义；框架事件系统和渲染性能细节另有版本与实现边界。

# How do you write a proper deep copy?

**Headline (30s):** JSON round-tripping only copies JSON-compatible data: it drops or changes values and rejects cycles. `structuredClone` handles cycles and supported built-in types; a handwritten clone is a domain-specific policy, not a universal deep-copy algorithm. **中文：** JSON 往返只适用于有限的数据形状；结构化克隆覆盖更多内建类型；手写克隆必须明确支持范围。

**Why interviewers ask this:** It tests your grasp of reference semantics, edge cases (cycles, special types), and whether you can design a recursive function with proper memoization.

## Why `JSON.parse(JSON.stringify(x))` is insufficient

- **Changed values:** a `Date` serializes to a string; a typical `Map` or `Set` becomes `{}`.
- **Unsupported values:** object properties whose values are `undefined`, functions, or symbols are omitted; such array entries become `null`; a top-level unsupported value can make parsing fail.
- **Circular references and `BigInt`:** `JSON.stringify` throws.

Reach for `structuredClone(value)` (see [`3.8 Modern JavaScript Features`](../javascript/modern-javascript-features.md)) for supported structured-cloneable values. Functions and DOM nodes are not cloneable, and cloning does not preserve arbitrary class behavior. Use a handwritten clone only for a deliberately bounded data model or a custom policy (for example, omitting selected fields).

## Handwritten deep copy

```javascript
function deepCopy(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value;
  if (seen.has(value)) return seen.get(value);

  let copy;
  if (value instanceof Date) {
    copy = new Date(value.getTime());
  } else if (value instanceof RegExp) {
    copy = new RegExp(value.source, value.flags);
    copy.lastIndex = value.lastIndex;
  } else if (value instanceof Map) {
    copy = new Map();
    seen.set(value, copy);
    for (const [key, item] of value) {
      copy.set(deepCopy(key, seen), deepCopy(item, seen));
    }
    return copy;
  } else if (value instanceof Set) {
    copy = new Set();
    seen.set(value, copy);
    for (const item of value) copy.add(deepCopy(item, seen));
    return copy;
  } else if (Array.isArray(value)) {
    copy = new Array(value.length);
  } else {
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) {
      throw new TypeError('Unsupported object type');
    }
    copy = Object.create(prototype);
  }

  seen.set(value, copy);
  if (value instanceof Date || value instanceof RegExp) return copy;

  // This example copies enumerable own string-keyed data in arrays/plain objects.
  for (const key of Object.keys(value)) {
    Object.defineProperty(copy, key, {
      value: deepCopy(value[key], seen),
      enumerable: true,
      writable: true,
      configurable: true,
    });
  }
  return copy;
}
```

This sample handles same-realm `Date`, `RegExp`, `Map`, `Set`, arrays, and plain objects with enumerable string keys. It does not preserve symbols, descriptors, accessors, arbitrary prototypes, or custom properties on the special built-ins. The `WeakMap` preserves cycles and repeated references; `Map` keys must be cloned as well as values.

```javascript
const trailingHoles = deepCopy([1, , ,]);
console.assert(trailingHoles.length === 3 && 0 in trailingHoles && !(1 in trailingHoles) && !(2 in trailingHoles));

const emptySparse = deepCopy(new Array(3));
console.assert(emptySparse.length === 3 && Object.keys(emptySparse).length === 0);
```

---

# How do DOM events propagate?

**Headline (30s):** Events with a propagation path can invoke capture listeners on the way to the target and bubble listeners on the way back. Whether an event bubbles or crosses a shadow boundary depends on its flags. Most `addEventListener` handlers use bubble mode by default. **中文：** 事件传播分捕获、目标和冒泡阶段，但是否冒泡、是否跨越 Shadow DOM 边界取决于事件标志。

## The three phases

1. **Capture** — capture listeners run along the path toward the target.
2. **Target** — listeners on the target run.
3. **Bubble** — if `event.bubbles` is true, bubble listeners run back along the path.

```javascript
document.body.addEventListener('click', () => console.log('body (bubble)'));
document.body.addEventListener('click', () => console.log('body (capture)'), { capture: true });
button.addEventListener('click', () => console.log('button'));

// Clicking the button logs:
// body (capture)  → capture phase
// button          → target
// body (bubble)   → bubble phase
```

`event.target` is the event's target; `event.currentTarget` is the object whose listener is currently running. Shadow DOM can retarget `target` for listeners outside a shadow tree.

### Default actions and listener options / 默认行为与监听器选项

Propagation and the browser's default action are separate. `preventDefault()` only cancels a cancelable event when called from a non-passive listener; it does not stop propagation. `stopPropagation()` stops the event reaching later objects on the path, while `stopImmediatePropagation()` also stops later listeners on the current object.

Use `{ passive: true }` for scroll/touch listeners that never cancel scrolling. In a passive listener, `preventDefault()` is ignored. The DOM Standard defines passive defaults for certain `touchstart`, `touchmove`, `wheel`, and `mousewheel` listeners on `Window`, `Document`, and document root/body targets; set the option explicitly when cancellation is required.

## Event delegation

For many child controls, one parent listener can handle bubbled events. Match a descendant of the event target; delegation only works for event types that bubble.

```javascript
parent.addEventListener('click', (e) => {
  const target = e.target instanceof Element ? e.target : null;
  const item = target?.closest('.item');
  if (!item) return;
  console.log('Item clicked:', item.textContent);
});
```

Benefits: fewer per-item registrations and dynamically added descendants need no rebinding. Choose based on the event's propagation behavior and the needed target checks.

## React's synthetic event system

React DOM exposes a **SyntheticEvent** with familiar event properties and JSX handlers for capture and bubble phases. Its internal delegation strategy is a framework implementation detail; React 17 changed the delegation root, so do not use one version's internals as a DOM rule.

Handler naming:

- `onClick` — bubble phase (default).
- `onClickCapture` — capture phase.

**Historical note — event pooling:** React DOM versions before 17 pooled SyntheticEvent objects; React 17 removed that behavior. `persist()` is not needed for current React DOM handlers. React Native has separate event behavior.

---

# Implement an EventBus / EventEmitter

**Headline (30s):** An EventBus stores listeners by event name. A `once` wrapper must remove itself before calling user code so recursion or a thrown error cannot make it run a second time. **中文：** 一次性监听器应在调用用户回调前注销，避免递归触发或异常导致重复调用。

```javascript
class EventBus {
  events = new Map();

  on(event, listener) {
    if (!this.events.has(event)) this.events.set(event, new Set());
    this.events.get(event).add(listener);
  }

  once(event, listener) {
    let fired = false;
    const wrapper = (...args) => {
      if (fired) return;
      fired = true;
      this.off(event, wrapper); // remove before user code, including recursive emits
      listener(...args);
    };
    this.on(event, wrapper);
  }

  emit(event, ...args) {
    // Snapshot listeners: changes during this emit affect the next emit.
    for (const listener of [...(this.events.get(event) ?? [])]) listener(...args);
  }

  off(event, listener) {
    const listeners = this.events.get(event);
    if (!listeners) return;
    listeners.delete(listener);
    if (listeners.size === 0) this.events.delete(event);
  }
}
```

**Reentrancy regression:** the outer `emit` keeps its listener snapshot while a nested `emit` uses the updated listener set. A later `once` wrapper can therefore still appear in the outer snapshot after the nested call removes it; its `fired` guard makes that second snapshot entry a no-op.

```javascript
const bus = new EventBus();
let firstCalls = 0;
let laterCalls = 0;
bus.once('x', () => { firstCalls += 1; bus.emit('x'); });
bus.once('x', () => { laterCalls += 1; });
bus.emit('x');
console.assert(firstCalls === 1 && laterCalls === 1);
```

**Gotcha — anonymous listeners:** `bus.on('x', () => {...})` can't be removed later because you don't have a reference to the function. Always save the reference if you'll need `off`.

**Contract of this small example:** a thrown listener stops the current `emit`; the listener snapshot means additions/removals during dispatch affect the next emission. A production emitter should document its error and mutation policy.

---

# Observer pattern vs. Publish-Subscribe

**Headline (30s):** Both are reactive messaging patterns, but they differ in coupling. **Observer**: the subject knows its observers directly (DOM events, RxJS subjects). **Publish-Subscribe**: a broker (event bus) sits between, so publishers and subscribers don't know about each other. Pub-Sub is more decoupled but harder to debug because the flow is indirect.

## Observer

```javascript
button.addEventListener('click', handleClick);
// button knows it has a listener called handleClick
```

The subject (`button`) maintains a list of observers and notifies them directly.

## Publish-Subscribe

```javascript
eventBus.on('user:login', updateUI);
eventBus.emit('user:login', { name: 'Alice' });
// Neither `updateUI` nor the emitter knows about each other
// The eventBus is the mediator
```

A topic string names the event channel; anyone can publish, anyone can subscribe.

**Rule of thumb:** Use Observer when there's a natural "owner" of the event (a DOM node, a data model). Use Pub-Sub when you want to decouple modules that shouldn't import each other.

---

# `requestAnimationFrame` vs. `requestIdleCallback` — when do you use each?

**Headline (30s):** `requestAnimationFrame` schedules visual work for a rendering opportunity. Its cadence follows the user agent and display; it is not a fixed 16 ms timer. `requestIdleCallback` offers an idle-time opportunity for non-critical work, but it can be delayed and needs a deliberate fallback when unavailable. **中文：** rAF 与绘制节奏关联；rIC 适合可延后任务，但两者都不是固定间隔定时器。

## `requestAnimationFrame`

```javascript
function animate() {
  element.style.transform = `translateX(${x++}px)`;
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
```

- Runs before a rendering update when the user agent schedules one; timing varies with refresh rate and page visibility.
- The first callback receives a high-resolution timestamp.

## `requestIdleCallback`

```javascript
function runIdleSlice(deadline) {
  if (!workQueue.length) return;

  // Process one bounded unit; a timeout is not permission to drain the queue.
  if (deadline.didTimeout || deadline.timeRemaining() > 0) {
    processNext(workQueue.shift());
  }

  if (workQueue.length) {
    requestIdleCallback(runIdleSlice, { timeout: 2000 });
  }
}

requestIdleCallback(runIdleSlice, { timeout: 2000 });
```

- `deadline.timeRemaining()` is the user agent's estimate of idle time remaining; do not treat it as a hard frame budget.
- `{ timeout }` asks the user agent not to leave the callback waiting indefinitely; `deadline.didTimeout` identifies that path.
- Keep each `processNext` unit bounded. A timeout callback still processes only one unit, then reschedules any remaining work.
- Feature-detect the API. `setTimeout` can be a functional fallback, but it is not an idle scheduler and gives no equivalent scheduling guarantee.

Framework schedulers may also split work and yield, but they are separate scheduling systems; do not equate React's scheduler with `requestIdleCallback`.

**Rule of thumb:**

- Must happen this frame? → `requestAnimationFrame`.
- Low priority, whenever the browser has idle time? → `requestIdleCallback` when available, with a fallback chosen for the task's guarantees.

---

# Finding the maximum in an array — which technique is safe for huge arrays?

**Headline (30s):** Spread and `apply` pass each array element as a function argument, so very large calls can exceed an implementation's argument limit. The limit varies; it is not a portable “100k” boundary. A loop or reduction avoids that argument-list limit. **中文：** 展开数组会形成大型实参列表，限制因实现而异；循环或归约不受该限制。

```javascript
// Concise, but very large argument lists may exceed an implementation limit
Math.max(...arr);
Math.max.apply(null, arr);

// Iterates without building a large argument list; for numeric arrays,
// an empty array matches Math.max() by producing -Infinity.
let max = -Infinity;
for (const value of arr) max = Math.max(max, value);
```

**Gotcha — input semantics:** `Math.max()` with no arguments returns `-Infinity`, and any `NaN` input makes its result `NaN`. If the application wants a different empty-input or non-number policy, handle that explicitly.

**See also:** [`5.3 Image Lazy Loading`](./image-lazy-loading.md) for Intersection Observer, [`7.1 Event Loop`](../runtime/event-loop.md) for the task/microtask scheduling model around browser callbacks.

**Standards and current docs / 规范与文档：** [WHATWG DOM events](https://dom.spec.whatwg.org/#concept-event-dispatch), [ECMAScript array objects](https://tc39.es/ecma262/multipage/indexed-collections.html), [WHATWG structured data](https://html.spec.whatwg.org/multipage/structured-data.html), [React DOM event handlers](https://react.dev/learn/responding-to-events), [React 17 event delegation change](https://react.dev/blog/2020/08/10/react-v17-rc#changes-to-event-delegation), [requestIdleCallback specification](https://w3c.github.io/requestidlecallback/), [Chrome `requestIdleCallback` guide](https://developer.chrome.com/blog/using-requestidlecallback), [CSSOM View](https://www.w3.org/TR/cssom-view-1/).
