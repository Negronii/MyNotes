# 脚本如何影响 HTML 解析与文档就绪？

案例背景：报表服务器已返回标题、排序按钮和初始行，浏览器还在解析 HTML，并同时获取 `/reports.css` 与 `/reports.js`。用户想先看到正文；排序按钮应在处理器安装后才可用。下面按脚本获取、执行和文档就绪的先后关系判断哪些工作会挡住哪一步。

## 不同脚本属性怎样改变解析顺序？

表格说的是 HTML parser（HTML 解析器）插入的脚本；动态插入的脚本有不同默认调度，不能把它们混为一谈。

| 脚本形式 | 下载与解析的关系 | 运行时机与顺序 |
|---|---|---|
| 外部经典脚本，不带 `async` / `defer` | 主 parser 处理到脚本时可开始请求；浏览器也可能由推测解析更早请求资源。主 parser 到达该元素后转而处理脚本；资源或阻塞样式表尚未就绪时先等待 | 脚本同步执行完后 parser 才继续解析，保持文档顺序 |
| 外部经典脚本 `defer` | 与解析并行获取 | 解析完成后、`DOMContentLoaded` 前执行；多个 defer 脚本按文档顺序 |
| 外部经典脚本 `async` | 与解析并行获取 | 下载就绪后尽快执行；若解析还在进行，会暂时打断解析；不保证多个 async 脚本的顺序 |
| 普通模块脚本 | 模块文件及其 `import` 依赖与解析并行获取 | 默认在解析完成后按文档顺序开始求值；各模块依赖按依赖关系处理 |
| `async` 模块脚本 | 模块文件及其 `import` 依赖与解析并行获取 | 模块及其依赖就绪后尽快执行，不保证相对其他异步脚本的顺序 |
| 内联经典脚本，有无 `defer` | 没有外部文件要获取 | parser 到达该元素且没有待等的阻塞样式表时执行；没有 `src` 时 `defer` 不起延后作用 |

`defer` 适合依赖已解析文档、且需要保持外部经典脚本文档顺序的代码。`async` 适合执行不依赖解析结果或其他脚本的独立工作。模块脚本默认延后执行，给模块加 `async` 会改变这个选择。

## 为什么解析器有时必须停下来？

解析 HTML 就像按顺序读取标记并逐个建立节点。经典脚本能在节点还没建完时查询、修改文档，甚至用 `document.write()` 改变后续解析结果；浏览器不能一概把这种脚本当作与文档无关的文件而继续前进。因此，脚本获取可以和其他资源获取重叠，但脚本执行本身可能成为解析的依赖点。

样式表对脚本的影响不是浏览器先分析某段 JavaScript 是否调用了 `getComputedStyle()`。HTML 定义了脚本阻塞样式表集合：由 parser 创建、作为启用样式表处理、media 条件匹配且仍在等待中的 `style` / stylesheet `link`，可以进入该集合。后续要执行的同步 parser 脚本或延后脚本，会按这个集合判断是否等待；即便 `/reports.js` 只给按钮注册事件，也可能先等 `/reports.css`。

本例中由 parser 在 `<head>` 创建、已启用且 `media` 匹配的 stylesheet link 可能阻塞渲染，因此资源尚未就绪时首帧可能推迟。不是“所有 CSS 必须全部下载后才能开始任何绘制”，而是具体资源是否阻塞由渲染与脚本各自的条件决定。

以下 HTML 是报表页的初始结构。本节只跟踪 head 中的 CSS 与模块，以及正文排序控件和图片；标题片段锚点与图标形状不改变这段加载时序。

~~~html
<head>
  <link rel="stylesheet" href="/reports.css">
  <script type="module" src="/reports.js"></script>
</head>
<main>
  <h1 id="summary">Recent reports</h1>
  <img src="/report-summary.png" width="320" height="180" alt="Report summary">
  <div id="sort-controls">
    <button
      type="button"
      data-sort="recent"
      aria-pressed="true"
      disabled
    >
      <span>Most recent</span>
    </button>
    <button
      type="button"
      data-sort="oldest"
      aria-pressed="false"
      disabled
    >
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M8 13V3m-4 4 4-4 4 4" fill="none" stroke="currentColor"
              stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <span>Oldest first</span>
    </button>
  </div>
  <ol id="reports">
    <li data-id="may">May report</li>
    <li data-id="april">April report</li>
  </ol>
</main>
~~~

服务器已经输出 May → April 的初始顺序；外部模块 `/reports.js` 在 parser 完成后运行。两个按钮先以原生 `disabled` 状态输出，避免模块尚未安装处理器时把用户的点击静默丢掉。本例模块默认延后到解析结束才执行，因此 guard 走 `interactive` 分支，直接安装处理器；`loading` 分支适用于其他入口在文档仍解析时运行的脚本。

以下是外部 `/reports.js` 的最小实现。本例只展示处理器何时安装、如何同步列表和按钮状态，不在这里重放 URL 与浏览器历史逻辑。

~~~javascript
const records = [
  { id: "may", date: "2026-05-01", label: "May report" },
  { id: "april", date: "2026-04-01", label: "April report" },
];

function renderReports(list, controls, sort) {
  const rows = [...records].sort((a, b) =>
    sort === "oldest" ? a.date.localeCompare(b.date) : b.date.localeCompare(a.date)
  );
  for (const button of controls.querySelectorAll("button[data-sort]")) {
    button.setAttribute("aria-pressed", String(button.dataset.sort === sort));
  }
  list.replaceChildren(...rows.map(({ id, label }) => {
    const item = document.createElement("li");
    item.dataset.id = id;
    item.textContent = label;
    return item;
  }));
}

function initializeReportControls() {
  const controls = document.querySelector("#sort-controls");
  const list = document.querySelector("#reports");
  if (!controls || !list) return;

  controls.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const button = target?.closest("button[data-sort]");
    if (!button || !controls.contains(button)) return;
    const sort = button.dataset.sort;
    if (sort !== "recent" && sort !== "oldest") return;
    renderReports(list, controls, sort);
  });

  renderReports(list, controls, "recent");
  for (const button of controls.querySelectorAll("button[data-sort]")) {
    button.disabled = false;
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeReportControls, { once: true });
} else {
  initializeReportControls();
}
~~~

下面前两行对照两种资源返回顺序：CSS 先完成、模块后到；或模块先到、CSS 仍在等待。两者都汇合到 parser 已结束、脚本可运行的阶段。

| 此刻的资源状态 | parser、DOM 与首帧 | 排序处理器与就绪事件 |
|---|---|---|
| 正文已解析为 DOM（此时 `readyState=interactive`），`/reports.css` 已就绪，`/reports.js` 或其 `import` 依赖仍在下载，图片未完成 | 浏览器可能先绘出标题和 May → April；图片的 320×180 尺寸先占位；按钮仍为 disabled | 排序监听器尚未安装，按钮不能触发；`DOMContentLoaded` 仍等待 deferred 模块 |
| 模块响应先返回，但 CSS 仍是阻塞脚本的样式表 | parser 仍可继续补全正文；完成解析后 `readyState` 变为 `interactive`，模块执行仍要等 CSS 解除阻塞 | 按钮继续 disabled；模块未运行，`DOMContentLoaded` 尚未触发 |
| parser 已结束（`readyState=interactive`），模块及其依赖已可执行，CSS 已解除阻塞 | 模块同步调用初始化函数，保留 May → April 初始顺序，随后启用两个按钮 | 排序监听器和初始 `aria-pressed=true/false` 已就绪；普通同步模块执行结束后才派发 `DOMContentLoaded` |
| 用户点已启用的 **Oldest first** | 不再解析 HTML；处理器按日期重建列表行 | `aria-pressed` 变为 `false/true`，顺序变为 April → May |

这条链把“有 DOM”“可绘制”和“处理器已绑定”分开：模块未运行时按钮仍不可用；同步绑定和初始渲染完成后才启用。若图片较晚到，预留的宽高减少它到达后挤动文字的机会。

## `DOMContentLoaded` 和 `load` 分别说明什么？

`DOMContentLoaded` 在 HTML parser 完成解析并处理延后脚本后派发到 `Document`。`document.readyState` 在 parser 停止时先变为 `interactive`，此时延后脚本仍可能等待模块脚本、其依赖或阻塞脚本的样式表。普通 `defer` 脚本在该流程同步执行；默认模块也在解析后开始求值。模块及其依赖均同步求值时，模块代码会在事件前执行完；模块遇到顶层 `await` 时，后续代码可在事件后继续，依赖含顶层 `await` 的模块也可能推迟导入方的代码。若初始化把后续工作放进 Promise 回调或异步请求，也可能晚于该事件。因此它不表示所有应用初始化已完成，也不等图片或 `async` 脚本完成。延后脚本可能等待脚本阻塞样式表，所以样式表也能间接推迟 `DOMContentLoaded`。

`load` 事件由 `Window` 的监听器接收；HTML 使用历史兼容的 target override，因此回调中 `event.currentTarget` 是 `window`，而 `event.target` 是 `document`。触发前，文档转入 `complete`，所有仍会延迟 `load` 的资源都已完成；普通图片、样式表、脚本和子框架可能在其中，懒加载资源通常不必挡住它。精确范围由 HTML 的加载算法决定。

| 检查点与 `readyState` | 事件与监听位置 | 此时可依赖的条件 |
|---|---|---|
| parser 停止（`interactive`） | `readystatechange` 在 `Document` 上触发 | HTML 已解析完；延后脚本仍可能在执行或等待 |
| DOM 内容加载完（`interactive`） | `DOMContentLoaded` 在 `Document` 上触发 | parser 延后脚本已处理；图片和 `async` 脚本不作为此事件的等待条件，模块的异步延续仍可能继续 |
| `load`（`complete`） | 监听器在 `Window` 上运行；`event.target` 为 `Document` | 会延迟 load 的资源已完成；应用 API、hydration 或其他 Promise 仍可能未完成 |

这些事件和状态本身不报告首帧，也不追踪应用自己的初始化结果。本例正常执行同步初始化时，排序按钮确实在 `DOMContentLoaded` 前启用；异步初始化的应用则需要自己的就绪信号。

## 脚本晚到时，怎样避免错过 `DOMContentLoaded`？

`DOMContentLoaded` 是一次事件，不是以后可订阅的完成状态。若代码通过动态导入或延迟执行，在事件之后才注册监听器，处理器不会补发。前面 `/reports.js` 末尾的 guard 读取 `document.readyState`：仍是 `loading` 时订阅事件并一次性调用已完整定义的 `initializeReportControls()`；否则文档解析已结束，就立即初始化。同步执行的 JavaScript 不会被浏览器事件打断，因此状态检查和注册之间不会插入一次 `DOMContentLoaded` 派发。

`readyState` 的 `loading` 表示 HTML parser 仍在解析；`interactive` 表示解析已结束但延后脚本与子资源流程可能尚未完成；`complete` 表示文档已进入加载完成阶段。这个 guard 只保证 DOM 已可查询：若初始化依赖尚未执行的 defer/module 脚本副作用，应等待该脚本自己的就绪信号。文档状态也不代表报表 API 请求、React hydration 或其他应用异步初始化已经完成；若初始化包含这类异步工作，仍需单独表示并等待。

判断主要内容何时出现，要观察绘制；判断排序按钮是否可用，要看其初始化状态。首帧可以早于 `load`，而报表内容也可能已显示、模块脚本还没注册排序处理器。反过来，`DOMContentLoaded` 触发后，一次长脚本任务仍会让点击处理器排队等待。可见时点和就绪事件的区别见[浏览器如何把 URL 变成第一帧？](../browser/browser-basics.md)；用户侧的加载与交互数据见[如何测量并诊断网页性能问题？](../performance/performance-metrics-and-analysis.md)。

> [!info]- 来源
> - 解析器插入的经典脚本、`async`、`defer` 与模块调度：[WHATWG HTML：script processing model](https://html.spec.whatwg.org/multipage/scripting.html#script-processing-model)，Living Standard（2026-11-11 更新），外部/内联脚本、defer 模块列表与 async 集合。核对日期：2026-11-12。
> - parser 等待时允许浏览器推测获取后续资源：[WHATWG HTML：Speculative HTML parsing](https://html.spec.whatwg.org/multipage/parsing.html#speculative-html-parsing)，Living Standard（2026-11-11 更新）；这项预取优化的具体时机依实现而异。核对日期：2026-11-12。
> - 脚本阻塞样式表的条件：[WHATWG HTML：interactions of styling and scripting](https://html.spec.whatwg.org/multipage/semantics.html#interactions-of-styling-and-scripting)，Living Standard（2026-11-11 更新），parser 创建、样式表有效状态、media 匹配及阻塞集合。核对日期：2026-11-12。
> - 样式表链接可能阻塞渲染的条件：[WHATWG HTML：link type stylesheet](https://html.spec.whatwg.org/multipage/links.html#link-type-stylesheet) 与 [render-blocking mechanism](https://html.spec.whatwg.org/multipage/dom.html#render-blocking-mechanism)，Living Standard（2026-11-11 更新），parser 创建的 stylesheet link 可能 render-blocking；外链资源处理步骤检查 `media` 匹配与 render-blocking 状态。核对日期：2026-11-12。
> - 解析结束时的 `interactive`、延后脚本、`DOMContentLoaded` 与 `load` 派发：[WHATWG HTML：The end](https://html.spec.whatwg.org/multipage/parsing.html#the-end)，Living Standard（2026-11-11 更新），parser 结束、deferred script 队列、DOM content loaded 与窗口 load event。核对日期：2026-11-12。
> - `document.readyState` 的 `loading`、`interactive`、`complete` 及 `readystatechange`：[WHATWG HTML：Reporting document loading status](https://html.spec.whatwg.org/multipage/dom.html#reporting-document-loading-status)，Living Standard（2026-11-11 更新）。核对日期：2026-11-12。
> - 顶层 `await` 与模块依赖的异步求值：[ECMAScript 2027：Module evaluation](https://tc39.es/ecma262/#sec-moduleevaluation)，异步模块求值及其依赖关系。DOMContentLoaded / load 的触发顺序由上述 HTML 算法决定。核对日期：2026-11-12。
