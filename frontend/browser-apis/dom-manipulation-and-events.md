# DOM 事件如何传播，何时适合事件委托？

案例背景：用户打开 `https://example.test/reports?sort=recent#summary` 后，页面显示 May、April 两行和“最早优先”按钮。点击按钮要把 `oldest` 这个筛选意图交给应用，由应用更新地址和列表。按钮里面还可能有图标或文字节点；事件委托必须从真实事件目标找到所属按钮，并确认它属于这个工具栏。

## 一次点击沿哪些节点传播？

浏览器为事件确定传播路径后，监听器可以沿路径经历三个阶段：捕获阶段从外层祖先走向目标；目标阶段运行目标上的监听器；若事件的 `bubbles` 为真，冒泡阶段再从目标向祖先返回。不是所有事件都会冒泡，所以委托前要确认事件类型的传播约定。

~~~javascript
const button = document.querySelector('#sort-controls button[data-sort="oldest"]');
const label = button.querySelector("span");

document.body.addEventListener("click", () => console.log("body bubble"));
document.body.addEventListener("click", () => console.log("body capture"), { capture: true });
label.addEventListener("click", () => console.log("label target"));
button.addEventListener("click", () => console.log("button bubble"));

// 点击 span：body capture → span target → button bubble → body bubble
~~~

`event.target` 是最初的事件目标；`event.currentTarget` 是当前正在运行监听器的对象。若按钮里还有 `<svg>` 或 `<span>`，`target` 可能是它们；处理器应先找到最近的筛选按钮。Shadow DOM（影子 DOM）边界外的监听器可能看到被重定向的 `target`；事件的 `bubbles` 与 `composed` 标记影响事件能否穿过相应边界。

## 什么时候用父级监听器处理子控件？

事件委托让一个父级监听器处理多个后代控件，包括稍后插入的控件，因此不用逐一注册监听器。它适合事件会冒泡、父级确实拥有这些控件、目标匹配规则清楚的场景；它不会消除每次事件分发或处理器本身的计算。

~~~html
<h1 id="summary">Recent reports</h1>
<div id="sort-controls">
  <button type="button" data-sort="recent" aria-pressed="true"><span>Most recent</span></button>
  <button type="button" data-sort="oldest" aria-pressed="false"><svg aria-hidden="true"></svg><span>Oldest first</span></button>
</div>
<ol id="reports"><li data-id="may">May report</li><li data-id="april">April report</li></ol>
~~~

~~~javascript
const controls = document.querySelector("#sort-controls");

controls.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  const button = target?.closest("button[data-sort]");
  if (!button || !controls.contains(button)) return;

  const sortIntent = button.dataset.sort;
  console.log("Sort requested:", sortIntent); // 点击“最早优先”时得到 "oldest"
});
~~~

点击 `span` 或 `svg` 时，`closest()` 会从该后代向上找到带 `data-sort` 的按钮；`controls.contains(button)` 确认匹配结果没有越出工具栏。事件处理器交出的值是按钮声明的 `recent` 或 `oldest`；点击“最早优先”时输出 `oldest`。应用据此把查询参数写回 URL、切换按钮的 `aria-pressed`，并将列表行改成 April → May；这条状态转换见[每次 URL 变化都会加载新文档吗？](../browser/browser-navigation-and-history.md)。如果事件处理器要移除匹配元素再循环，先选择静态快照或合适的实时集合，避免移除节点改变下一次索引；见[如何选择 DOM 集合？](./dom-collections.md)。

## 默认动作与传播控制是两回事

按钮若位于表单中，点击可能触发表单提交；这是与事件传播分开的默认动作。`preventDefault()` 只在事件可取消且监听器不是 passive 时取消默认动作，它不会停止冒泡。`stopPropagation()` 阻止事件继续传到路径上后续对象；`stopImmediatePropagation()` 还会阻止当前对象上后续监听器运行。

如果滚动或触控监听器不需要取消浏览器默认滚动，设置 `{ passive: true }` 能表明这一点；passive 监听器调用 `preventDefault()` 无法取消默认动作。DOM 标准规定，未显式设置 `passive` 的 `touchstart`、`touchmove`、`wheel` 和 `mousewheel` 监听器，在 `Window`、`Document`、`documentElement` 或 `body` 上默认 passive 为 true；确实需要拦截时，应先按事件的 `cancelable` 状态判断，再显式设置 `{ passive: false }`。

## 移动端点击与手势策略

历史上的移动端 click 延迟有特定条件：部分浏览器曾等待判断一次触摸是否还会成为双击缩放手势。它不是今天所有浏览器、所有 viewport 或所有输入模式下的固定延迟。先设置符合设备宽度的 viewport；不要为了绕开历史延迟而禁止用户缩放。

~~~html
<meta name="viewport" content="width=device-width, initial-scale=1">
~~~

若某个控件不需要双击缩放，但仍应允许平移和双指缩放，可以对该控件使用 Pointer Events 的 `touch-action: manipulation`：

~~~css
#sort-controls button[data-sort] {
  touch-action: manipulation;
}
~~~

它让浏览器保留平移和连续缩放，同时不把双击缩放作为该元素上的手势。把规则限制在确实需要的控件，不要用 `touch-action: none` 全局封锁操作。原生 `<button>` 自带键盘激活；自制的 `role="button"` 还必须补足键盘行为。Chrome 的 viewport 诊断指出一个特定条件：初始视口未针对移动设备优化时，点击可能延后至多 300 毫秒；其他浏览器和输入设置会不同，不能把这个值当成所有移动端点击的固定时延。除非目标设备实测仍有兼容问题，不要同时在 touch-end 和 click 上触发同一动作，以免合成 click 与原生 click 重复执行。

## 把浏览器事件交给 React 时，交接什么？

若同一报表页由 React 管理，浏览器仍然派发 click；React 的 `onClick` handler 因这次点击触发，并把筛选意图 `oldest` 传给状态更新。事件处理器可从目标元素读取该值，也可由按钮各自的闭包传入。浏览器这一侧的输入是已发生的事件、当前 URL `sort=recent` 和当前 DOM；交给下一章的应用意图是“筛选变为 `oldest`”。React 章节从这个输入继续，讲 state 快照、组件重算和 commit 后需要的 DOM 变化。见[React 如何把用户操作变成更新后的界面？](../frameworks/react-basics.md)。React 管理的节点应由 React state 描述；若另用 DOM API 直接改它们，下一次 React commit 可能覆盖这些修改。

React 的 JSX 事件名和事件对象保留常用的 DOM 事件概念，`onClick` 默认冒泡、`onClickCapture` 对应捕获。事件委托的具体根节点属于 React 实现细节：React 17 将委托根从 `document` 移到了 React root container；早期 React DOM 还会池化 SyntheticEvent，React 17 起移除了池化，所以当前 React DOM 不需要为异步读取事件调用 `persist()`。React Native 的事件行为另有边界。

**延伸：**[浏览器如何把 URL 变成第一帧？](../browser/browser-basics.md)交代该页面的首帧和筛选入口；[每次 URL 变化都会加载新文档吗？](../browser/browser-navigation-and-history.md)展示同一点击如何更新历史地址和列表；[浏览器 JavaScript 何时运行，画面何时更新？](../runtime/event-loop.md)说明 click 处理器如何等待主线程并交接到渲染机会；[跨浏览上下文如何通信？](./browser-context-communication.md)讲跨文档消息；[JavaScript 事件总线怎样处理重入？](./event-bus-and-observer-patterns.md)讨论应用层发布/订阅。

> [!info]- 来源
> - 捕获、目标、冒泡、事件目标、默认动作及取消： [WHATWG DOM：事件分发](https://dom.spec.whatwg.org/#concept-event-dispatch)，Living Standard，事件分发算法；[WHATWG DOM：Event 接口](https://dom.spec.whatwg.org/#interface-event)，事件标记与取消行为。核对日期：2026-11-06。
> - `touch-action` 的手势边界： [Pointer Events Level 3](https://www.w3.org/TR/pointerevents3/#the-touch-action-css-property)，W3C Recommendation，`manipulation` 值与直接操控行为章节。核对日期：2026-11-06。
> - passive 默认值与取消行为： [WHATWG DOM：事件监听器](https://dom.spec.whatwg.org/#dom-addeventlistener)，Living Standard，passive 监听器与阻止默认动作章节。核对日期：2026-11-06。
> - React 事件处理器与事件阶段： [React：Responding to Events](https://react.dev/learn/responding-to-events)；React 17 将委托根移到 root container：[React 17：Changes to Event Delegation](https://legacy.reactjs.org/blog/2020/08/10/react-v17-rc.html#changes-to-event-delegation)；React 17 移除事件池：[React 17：No Event Pooling](https://legacy.reactjs.org/blog/2020/08/10/react-v17-rc.html#no-event-pooling)。核对日期：2026-11-06。
> - 移动端 viewport 诊断的适用条件： [Chrome Performance Insights：Optimize viewport for mobile](https://developer.chrome.com/docs/performance/insights/viewport)，Chrome DevTools 指标说明。核对日期：2026-11-06。
