# 浏览器怎样查询、更新 DOM 并响应用户输入？

案例背景：用户打开 `https://example.test/reports?sort=recent#summary` 后，页面已有 May、April 两行和“最早优先”按钮。用户点按钮里的文字或图标时，处理器要找到所属按钮，把 `oldest` 这个筛选意图交给应用；渲染时还要区分文字、表单当前值、HTML content attribute（HTML 内容属性）和 DOM property（DOM 对象属性）。Document Object Model (文档对象模型，DOM) 把 HTML 文档表示为节点树，JavaScript 可以查询这些节点、改写其状态，并响应输入事件。

## DOM 树里有哪些节点？

文档节点包含元素节点、文本节点和注释等；元素的 attribute（属性）描述元素状态，但 attribute 不是元素的子节点。常用的 `nodeType` 值如下：

| `nodeType` | 节点 | 报表页中的例子 |
|---:|---|---|
| 1 | 元素（Element） | `<ol>`、`<li>`、`<button>` |
| 2 | 属性（Attr） | `id="reports"`（有 `Attr` 对象，但不是树的子节点） |
| 3 | 文本（Text） | `May report` |

向上找父级时，`parentNode` 可返回任意节点父级：`<html>` 的 `parentNode` 是 Document，而 `parentElement` 只返回元素父级，所以 `<html>.parentElement` 为 `null`。`nodeName` 命名任意节点，`tagName` 只属于元素；`nodeValue` 读取单个 Text 节点的值，在 Element 上则为 `null`，读取元素后代文字应使用 `textContent`。若要查某行的下一个元素，使用 `nextElementSibling`；`nextSibling` 可能先遇到 HTML 换行空白对应的文本节点。同理，`firstChild` 与 `firstElementChild` 可能不是同一项。`childNodes` 包含文本、注释等节点，`children` 只包含元素；它们的集合更新规则见[修改 DOM 时，HTMLCollection 和 NodeList 会怎样变化？](./dom-collections.md)。选到具体控件后，再决定修改文本、attribute、DOM property 还是节点顺序。

## 修改内容、HTML 属性和 DOM 对象属性有何区别？

文本和标记要用不同接口。`textContent` 读取后代文本，赋值会用一个文本内容替换子树；`innerText` 读写渲染文本：读取时元素若未渲染，会退回到后代文本；若已渲染，结果会受显示状态影响；`innerHTML` 读取或解析 HTML 字符串。把纯文字放入 DOM 时使用 `textContent`；只有受信任或已净化的标记才作为 HTML 解析。

| 写法 | 控制什么 | 报表页上的用途 |
|---|---|---|
| `row.textContent = label` | 文字，不解析 HTML | 写入报表名称 |
| `row.innerText` | 渲染后的文字语义；未渲染时退回后代文本 | 读取渲染文本 |
| `row.innerHTML = markup` | 子树的 HTML 标记 | 只有模板可信或已净化时才插入标记 |
| `element.setAttribute(name, value)` | HTML 内容属性 | 设置 `data-report-id`、`alt`、`title` 等声明 |
| `element.classList`、`element.style` | class 集合与 inline style（内联样式） | 切换状态 class，或写入必要的单次内联样式 |

HTML content attribute（HTML 内容属性）通常表达标记中的初始值；对应 DOM property（DOM 对象属性）则暴露该元素当前的状态或类型化值。输入框说明了这个区别：

~~~html
<input id="sort-query" value="recent">
~~~

~~~javascript
const query = document.querySelector("#sort-query");
query.value = "oldest"; // 当前输入值

console.log(query.value); // "oldest"
console.log(query.getAttribute("value")); // "recent"，标记里的初始值
~~~

用户编辑或脚本设置 `value` 后，HTML 的 dirty value flag（值已修改标记）让 property 保留当前值；`value` attribute 仍用于初始值。对布尔 attribute（布尔属性，例如 `disabled`），只看是否存在：`setAttribute("disabled", "false")` 仍会禁用控件。要启用按钮，设 `button.disabled = false` 或移除该 attribute。

要更新筛选行的外观，`className = "selected"` 会整体替换 class 字符串；`classList.add()`、`remove()` 和 `toggle()` 改单个类。`element.style.backgroundColor` 写的是 inline style（内联样式）；CSS property 在 JavaScript 里通常使用 camelCase（小驼峰）。`data-report-id="may"` 可通过 `row.dataset.reportId` 读取与设置，`dataset` 中的值始终是字符串。图片的 `src` 选择资源，`alt` 提供替代文本（装饰图可用空值），`title` 是补充信息，不能替代 `alt`。

## 怎样生成、移动或克隆一组节点？

为单独演示如何从结构化数据建表，设一张学校成绩表固定按 Name、Subject、Grade 排列。对象字段顺序不是表格的列定义；三条记录应分别显示 Ron—Math—100、Jack—Calculus—70、Mar—Business—90：

~~~html
<table>
  <thead><tr><th>Name</th><th>Subject</th><th>Grade</th></tr></thead>
  <tbody id="students"></tbody>
</table>
~~~

~~~javascript
const students = [
  { name: "Ron", subject: "Math", grade: "100" },
  { name: "Jack", subject: "Calculus", grade: "70" },
  { name: "Mar", subject: "Business", grade: "90" },
];
const columns = ["name", "subject", "grade"];
const body = document.querySelector("#students");

for (const student of students) {
  const row = document.createElement("tr");
  for (const column of columns) {
    const cell = document.createElement("td");
    cell.textContent = student[column];
    row.append(cell);
  }
  body.append(row);
}
~~~

每个记录依照同一份 `columns` 产生三格，输入值只进入文本节点。`append()` 会把新节点追加到末尾；若传入已经在文档中的节点，它会将该节点移动到新位置。`insertBefore(node, reference)` 把节点放到参考节点前，`remove()` 将节点从树上移除。

`cloneNode(true)` 会复制节点及其后代结构和 attribute，但不会复制通过 `addEventListener()` 或 DOM property 绑定的 listener（监听器）。若源节点已有 `id`，直接克隆会让页面出现重复 ID；插入前应为副本及其后代生成唯一 ID，并同步更新指向这些 ID 的引用。需要监听行为时，在新节点上重新注册：

本例的源行只有根节点 `data-id="may"`，没有 `id` attribute 或带 ID 的后代。代码给副本新增一个 DOM `id`，同时保留 `data-id` 所表示的报表身份；如果源行已有 DOM ID，克隆后就必须替换副本的 ID。

~~~javascript
function handleReportClick(event) {
  console.log(event.currentTarget.dataset.id);
}

const source = document.querySelector('#reports [data-id="may"]');
const copy = source.cloneNode(true);
copy.id = "may-row-copy"; // 新增 DOM id；data-id 仍标识 May 报表
copy.addEventListener("click", handleReportClick);
document.querySelector("#reports").append(copy);
~~~

对同一元素给 `onclick` 属性赋新函数会替换先前的函数；多处代码都需监听时，用 `addEventListener()` 可以各自注册和移除 listener（监听器）。只需响应一次时可设 `{ once: true }`；若要提前移除，保留原函数引用，并使用相同 capture（捕获阶段）选项调用 `removeEventListener()`。也可把同一 `AbortSignal`（中止信号）交给多个监听器，结束该页面区域时调用 `abort()` 一并清理。

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

`event.target` 是最初的事件目标；`event.currentTarget` 是当前正在运行监听器的对象。普通函数监听器中的 `this` 也指向 `currentTarget`，箭头函数的 `this` 则保留词法绑定。若按钮里还有 `<svg>` 或 `<span>`，`target` 可能是它们；处理器应先找到最近的筛选按钮。Shadow DOM（影子 DOM）边界外的监听器可能看到被重定向的 `target`；事件的 `bubbles` 与 `composed` 标记影响事件能否穿过相应边界。输入框获得和失去焦点时分别派发 `focus` 与 `blur`，这两个事件不冒泡；父级要委托焦点变化时可监听会冒泡的 `focusin` 与 `focusout`。

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

## 拖动时怎样跟踪坐标并处理取消？

Pointer Events（指针事件）把鼠标、触摸和笔输入统一到 pointer 事件，但一次拖动不是只有 `pointermove`：它从 `pointerdown` 开始，可通过 `setPointerCapture(pointerId)` 把后续该 pointer 的事件留给手柄；正常释放由 `pointerup` 结束，系统接管手势时可能收到 `pointercancel`，捕获释放后会有 `lostpointercapture`。清理时按 `pointerId` 匹配当前拖动，避免另一根手指或旧事件结束错误手势。

坐标属性对应不同参照系：

| 属性 | 参照系 | 适合回答的问题 |
|---|---|---|
| `clientX / clientY` | viewport（视口） | 指针现在相对当前可视区域在哪里 |
| `pageX / pageY` | 文档 | 指针在页面内容坐标中在哪里 |
| `screenX / screenY` | 屏幕 | 指针相对设备显示区域的位置 |

下面把一个报表卡片放进定位容器。移动用 client 坐标的差值；初始卡片位置来自同一个定位容器的 `offsetLeft` / `offsetTop`。本例假设容器没有 CSS 缩放或旋转，拖动时页面与容器也不滚动；在此条件下，视口坐标的位移对应卡片的 CSS 像素位移。若变换或滚动改变坐标参照系，就需先转换到同一坐标空间。

~~~html
<div id="report-canvas">
  <button id="movable-report" type="button" aria-describedby="move-report-help">
    May report
  </button>
</div>
<p id="move-report-help">鼠标或触摸拖动卡片；聚焦后也可用方向键移动。</p>
~~~

~~~css
#report-canvas {
  position: relative;
  width: 24rem;
  height: 12rem;
  border: 1px solid;
}

#movable-report {
  position: absolute;
  left: 0;
  top: 0;
  touch-action: none;
}
~~~

~~~javascript
const card = document.querySelector("#movable-report");
let drag = null;

card.addEventListener("pointerdown", (event) => {
  if (drag || !event.isPrimary || (event.pointerType === "mouse" && event.button !== 0)) return;
  drag = {
    pointerId: event.pointerId,
    x: event.clientX,
    y: event.clientY,
    left: card.offsetLeft,
    top: card.offsetTop,
  };
  card.setPointerCapture(event.pointerId);
});

card.addEventListener("pointermove", (event) => {
  if (!drag || drag.pointerId !== event.pointerId) return;
  card.style.left = (drag.left + event.clientX - drag.x) + "px";
  card.style.top = (drag.top + event.clientY - drag.y) + "px";
});

function finishDrag(event, canceled = false) {
  if (!drag || drag.pointerId !== event.pointerId) return;
  const start = drag;
  drag = null;
  if (canceled) {
    card.style.left = start.left + "px";
    card.style.top = start.top + "px";
  }
}

card.addEventListener("pointerup", finishDrag);
card.addEventListener("pointercancel", (event) => finishDrag(event, true));
card.addEventListener("lostpointercapture", (event) => finishDrag(event, true));

card.addEventListener("keydown", (event) => {
  const step = event.shiftKey ? 24 : 8;
  let dx = 0;
  let dy = 0;
  if (event.key === "ArrowLeft") dx = -step;
  else if (event.key === "ArrowRight") dx = step;
  else if (event.key === "ArrowUp") dy = -step;
  else if (event.key === "ArrowDown") dy = step;
  else return;

  event.preventDefault();
  card.style.left = (card.offsetLeft + dx) + "px";
  card.style.top = (card.offsetTop + dy) + "px";
});
~~~

卡片仍连接文档时，捕获让它在指针移出按钮后仍收到同一指针的移动与结束事件；正常抬起保留新位置，取消或捕获丢失则回到拖动起点。捕获目标脱离文档后，规范建议（SHOULD）把捕获目标改为 `document`，因此卸载时不能依赖卡片监听器收到 `lostpointercapture`。卸载区域时，应先清空拖动状态、释放捕获，再移除节点：

~~~javascript
function disposeCard() {
  const activeDrag = drag;
  drag = null;
  if (activeDrag && card.hasPointerCapture(activeDrag.pointerId)) {
    card.releasePointerCapture(activeDrag.pointerId);
  }
  card.remove();
}
~~~

`touch-action: none` 会禁止从卡片上开始的视口平移与缩放，所以只应放在确实需要拖动的小控件上；页面其余区域仍可正常滚动。另有 `contextmenu` 和 `selectstart` 的默认动作可在特定自定义交互上取消，但全页禁用菜单或选中文字会移除浏览器本身提供的操作，也不是安全机制。

## 窗口 resize、元素尺寸与 scroll 应监听在哪里？

`resize` 事件用于窗口/视口尺寸变化；若要响应某个报表容器自身的尺寸变化，使用 `ResizeObserver`（尺寸变化观察器）。`scroll` 应监听页面或实际发生滚动的容器；元素滚动时，把 listener 绑在该元素上，而不是假设它会冒泡到任意父级。两种事件都可能频繁触发，应让处理器只做该界面所需的更新。

Navigator 对象（浏览器环境信息接口）提供环境线索：`navigator.language` 是浏览器报告的首选语言，`navigator.platform` 是平台字符串，`navigator.userAgent` 是 user-agent 字符串（用户代理字符串）。语言不是国籍，平台或 user-agent 字符串也不能证明某个 API 可用；相关识别信息还会增加隐私暴露。页面需要容器尺寸能力时，直接检测 `ResizeObserver`，不按浏览器品牌猜测。

~~~javascript
const reportList = document.querySelector("#reports");
const lifetime = new AbortController();
let sizeObserver = null;

function recordViewportWidth() {
  if (reportList) {
    reportList.dataset.viewportWidth = String(window.innerWidth);
  }
}

if (reportList && typeof ResizeObserver === "function") {
  sizeObserver = new ResizeObserver(([entry]) => {
    if (!entry) return;
    reportList.dataset.containerWidth = String(Math.round(entry.contentRect.width));
  });
  sizeObserver.observe(reportList);
} else if (reportList) {
  window.addEventListener("resize", recordViewportWidth, { signal: lifetime.signal });
  recordViewportWidth();
}

function stopObservingReport() {
  lifetime.abort();
  sizeObserver?.disconnect();
}
~~~

检测到 `ResizeObserver` 时，更新来自实际报表容器；退回 `window.resize` 时只知道视口变化，父容器单独改变大小不会触发该回退。示例中的 `stopObservingReport()` 应由移除该页面区域的一方调用。

页面区域被移除时，用 `AbortController`（中止控制器）的 `signal` 一次清除绑定到该 signal 的事件监听器；`ResizeObserver` 则调用 `disconnect()` 停止观察。这些变化事件不同于初次解析用的 `DOMContentLoaded` / `load`；两者先后关系见[脚本如何影响 HTML 解析与文档就绪？](../html-css/browser-html-and-css.md)。

## 把浏览器事件交给 React 时，交接什么？

若同一报表页由 React 管理，浏览器仍然派发 click；React 的 `onClick` handler 因这次点击触发，并把筛选意图 `oldest` 传给状态更新。事件处理器可从目标元素读取该值，也可由按钮各自的闭包传入。浏览器这一侧的输入是已发生的事件、当前 URL `sort=recent` 和当前 DOM；交给下一章的应用意图是“筛选变为 `oldest`”。React 章节从这个输入继续，讲 state 快照、组件重算和 commit 后需要的 DOM 变化。见[React 如何把用户操作变成更新后的界面？](../frameworks/react-basics.md)。React 管理的节点应由 React state 描述；若另用 DOM API 直接改它们，下一次 React commit 可能覆盖这些修改。

React 的 JSX 事件名和事件对象保留常用的 DOM 事件概念，`onClick` 默认冒泡、`onClickCapture` 对应捕获。事件委托的具体根节点属于 React 实现细节：React 17 将委托根从 `document` 移到了 React root container；早期 React DOM 还会池化 SyntheticEvent，React 17 起移除了池化，所以当前 React DOM 不需要为异步读取事件调用 `persist()`。React Native 的事件行为另有边界。

**延伸：**[浏览器如何把 URL 变成第一帧？](../browser/browser-basics.md)交代该页面的首帧和筛选入口；[每次 URL 变化都会加载新文档吗？](../browser/browser-navigation-and-history.md)展示同一点击如何更新历史地址和列表；[浏览器 JavaScript 何时运行，画面何时更新？](../runtime/event-loop.md)说明 click 处理器如何等待主线程并交接到渲染机会；[跨浏览上下文如何通信？](./browser-context-communication.md)讲跨文档消息；[JavaScript 事件总线怎样处理重入？](./event-bus-and-observer-patterns.md)讨论应用层发布/订阅。

> [!info]- 来源
> - DOM 节点类型、树访问与 mutation、cloneNode 的复制范围：[WHATWG DOM：Node and node trees](https://dom.spec.whatwg.org/#interface-node)；[clone algorithm](https://dom.spec.whatwg.org/#concept-node-clone)，持续更新规范，Node 接口与节点复制算法。核对日期：2026-11-07。
> - `textContent`、事件监听器列表、`addEventListener()` 的 `signal` 选项与移除规则：[WHATWG DOM：Node.textContent](https://dom.spec.whatwg.org/#dom-node-textcontent)；[EventTarget](https://dom.spec.whatwg.org/#interface-eventtarget)，持续更新规范。核对日期：2026-11-07。
> - 表单 `input.value` 当前值、默认 attribute 与 dirty value flag，布尔 attribute 与 `disabled`：[WHATWG HTML：input element](https://html.spec.whatwg.org/multipage/input.html)，持续更新规范，common input attributes 与 value IDL attribute。核对日期：2026-11-07。
> - `innerText`、`data-*` 到 `dataset` 的 camelCase 映射、`title` 和 `style` 等全局属性：[WHATWG HTML：global attributes and text properties](https://html.spec.whatwg.org/multipage/dom.html)，持续更新规范，global attributes 与 innerText。核对日期：2026-11-07。
> - `img.src`、`alt` 替代文本与装饰图空 alt：[WHATWG HTML：The img element](https://html.spec.whatwg.org/multipage/embedded-content.html#the-img-element)，持续更新规范，img attributes 与 authoring requirements。核对日期：2026-11-07。
> - Navigator 的语言、平台和 userAgent 接口及减少可识别信息的隐私要求：[WHATWG HTML：Navigator object](https://html.spec.whatwg.org/multipage/system-state.html#the-navigator-object)，持续更新规范，NavigatorID 与 NavigatorLanguage。核对日期：2026-11-07。
> - 视口/页面坐标、窗口 `resize` 与页面/元素 `scroll` 事件：[CSSOM View Module Level 1](https://drafts.csswg.org/cssom-view/)，CSS Working Group Editor’s Draft，5 November 2026，MouseEvent coordinates、scrolling 和 resize 章节。核对日期：2026-11-07。
> - 观察元素尺寸及断开观察：[Resize Observer Module Level 1](https://www.w3.org/TR/resize-observer/)，W3C First Public Working Draft，11 February 2020；[CSSWG Editor’s Draft](https://drafts.csswg.org/resize-observer/)将其定义为元素尺寸观察 API。核对日期：2026-11-07。
> - pointer capture、捕获目标脱离文档时 SHOULD 迁移到 document、`pointercancel`、`lostpointercapture`、`touch-action` 与手势取消：[Pointer Events Level 3：Implicit release of pointer capture](https://www.w3.org/TR/pointerevents3/#implicit-release-of-pointer-capture)，W3C Recommendation，30 June 2026，pointer capture 与 direct manipulation sections。核对日期：2026-11-07。
> - `key`、`code`、`repeat` 以及不再推荐 `keypress`：[W3C UI Events](https://www.w3.org/TR/uievents/)，21 February 2026 Working Draft，KeyboardEvent interface 与 legacy keypress sections。核对日期：2026-11-07。
> - 捕获、目标、冒泡、事件目标、默认动作及取消： [WHATWG DOM：事件分发](https://dom.spec.whatwg.org/#concept-event-dispatch)，Living Standard，事件分发算法；[WHATWG DOM：Event 接口](https://dom.spec.whatwg.org/#interface-event)，事件标记与取消行为。核对日期：2026-11-07。
> - `touch-action` 的手势边界： [Pointer Events Level 3](https://www.w3.org/TR/pointerevents3/#the-touch-action-css-property)，W3C Recommendation，`manipulation` 值与直接操控行为章节。核对日期：2026-11-07。
> - passive 默认值与取消行为： [WHATWG DOM：事件监听器](https://dom.spec.whatwg.org/#dom-addeventlistener)，Living Standard，passive 监听器与阻止默认动作章节。核对日期：2026-11-07。
> - React 事件处理器与事件阶段： [React：Responding to Events](https://react.dev/learn/responding-to-events)；React 17 将委托根移到 root container：[React 17：Changes to Event Delegation](https://legacy.reactjs.org/blog/2020/08/10/react-v17-rc.html#changes-to-event-delegation)；React 17 移除事件池：[React 17：No Event Pooling](https://legacy.reactjs.org/blog/2020/08/10/react-v17-rc.html#no-event-pooling)。核对日期：2026-11-07。
> - 移动端 viewport 诊断的适用条件： [Chrome Performance Insights：Optimize viewport for mobile](https://developer.chrome.com/docs/performance/insights/viewport)，Chrome DevTools 指标说明。核对日期：2026-11-07。
