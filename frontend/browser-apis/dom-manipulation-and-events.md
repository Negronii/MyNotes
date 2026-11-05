# How do DOM events propagate, and when does delegation work? / DOM 事件如何传播，何时适合事件委托？

For an event with a propagation path, listeners may run during capture on the way to the target, at the target, and during bubbling on the way back. Delegation uses a parent listener to handle matching descendants, so it requires an event that bubbles and target checks appropriate to the DOM structure. Default actions are separate from propagation: cancel with `preventDefault()` only when the event is cancelable and the listener is not passive. / 对具有传播路径的事件，监听器可在捕获阶段沿路径到达目标，在目标阶段运行，再在冒泡阶段沿路径返回。事件委托通过父级监听器处理匹配的后代元素，因此要求事件会冒泡，并且按 DOM 结构检查目标。默认动作与事件传播分开：只有事件可取消且监听器非 passive 时，`preventDefault()` 才能取消默认动作。

## Capture, target, and bubble / 捕获、目标与冒泡

1. **Capture:** capture listeners run from the path's outer nodes toward the target.
2. **Target:** listeners on the target run.
3. **Bubble:** if `event.bubbles` is true, bubble listeners run back through the path.

~~~javascript
document.body.addEventListener("click", () => console.log("body bubble"));
document.body.addEventListener("click", () => console.log("body capture"), { capture: true });
button.addEventListener("click", () => console.log("button"));

// Click button: body capture → button target → body bubble
~~~

`event.target` identifies the event target; `event.currentTarget` is the object whose listener is executing. Shadow DOM can retarget `target` for listeners outside the shadow tree, and the event's bubbling/composed flags determine which boundaries it crosses.

## Delegation / 事件委托

One parent listener can handle many controls, including descendants added later, without binding a handler to each child. Match a descendant from the event target and check the element type before calling element-specific APIs.

~~~javascript
parent.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  const item = target?.closest(".item");
  if (!item || !parent.contains(item)) return;
  console.log("Item clicked:", item.textContent);
});
~~~

Delegation is useful for many dynamic descendants, but does not reduce every kind of work; use it when the propagation model and ownership make the handler simpler.

## Default action, cancellation, and listener options / 默认动作、取消与监听器选项

`preventDefault()` cancels a cancelable event's default action; it does not stop propagation. `stopPropagation()` prevents the event from reaching later objects on the path, while `stopImmediatePropagation()` also prevents later listeners on the current object. A passive listener cannot cancel the default action, so use `{ passive: true }` for scroll/touch listeners that never need to cancel scrolling. The DOM Standard defines passive defaults for particular root-target `touchstart`/`touchmove`/`wheel`/`mousewheel` listeners; set the option explicitly when cancellation matters.

## React DOM boundary / React DOM 边界

React exposes familiar synthetic event properties and JSX handlers: `onClick` bubbles by default and `onClickCapture` runs in capture. Its internal delegation is a framework implementation detail; React 17 moved the delegation root from the document to the React root container. Do not infer DOM event behavior from a particular React version. Before React 17, React DOM pooled SyntheticEvent objects; React 17 removed pooling, so `persist()` is not needed in current React DOM. React Native has separate behavior.

**See also:** [How do browser contexts communicate?](./browser-context-communication.md) covers cross-document messaging; [When does browser JavaScript run relative to a frame?](../runtime/event-loop.md) covers rAF and idle scheduling; [How can a JavaScript event bus handle reentrancy?](./event-bus-and-observer-patterns.md) covers application-level pub/sub.

**Sources:** [WHATWG DOM event dispatch](https://dom.spec.whatwg.org/#concept-event-dispatch); [React event handlers](https://react.dev/learn/responding-to-events); [React 17 delegation change](https://react.dev/blog/2020/08/10/react-v17-rc#changes-to-event-delegation), checked 2026-11-05.
