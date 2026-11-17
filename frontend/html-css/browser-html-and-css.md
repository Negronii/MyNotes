# 脚本如何影响 HTML 解析与文档就绪？

案例背景：一个报表页的服务器已经返回了标题、两个排序按钮和初始的报表行。浏览器一边解析这段 HTML，一边下载样式表 `/reports.css` 和脚本 `/reports.js`。用户希望尽快看到正文；排序按钮则应等脚本装好点击处理器后才可用。下面按脚本的下载、执行和文档就绪三个环节，逐一判断哪项工作会挡住哪一步。

## 不同脚本属性怎样改变解析顺序？

下表只讨论 HTML parser（HTML 解析器）在解析过程中遇到的脚本。用 JavaScript 动态插入的脚本有另一套默认调度规则，不能混为一谈。

| 脚本形式 | 下载与解析的关系 | 运行时机与顺序 |
|---|---|---|
| 外部经典脚本，不带 `async` / `defer` | parser 遇到该元素时开始请求（浏览器也可能通过推测解析提前请求）；随后 parser 停下，等脚本资源和阻塞脚本的样式表就绪 | 脚本同步执行完，parser 才继续解析；多个脚本按文档顺序执行 |
| 外部经典脚本 `defer` | 与解析并行获取 | 解析完成后、`DOMContentLoaded` 前执行；多个 defer 脚本按文档顺序 |
| 外部经典脚本 `async` | 与解析并行获取 | 下载就绪后尽快执行；若解析还在进行，会暂时打断解析；不保证多个 async 脚本的顺序 |
| 普通模块脚本 | 模块文件及其 `import` 依赖与解析并行获取 | 默认在解析完成后按文档顺序开始求值；各模块依赖按依赖关系处理 |
| `async` 模块脚本 | 模块文件及其 `import` 依赖与解析并行获取 | 模块及其依赖就绪后尽快执行，不保证相对其他异步脚本的顺序 |
| 内联经典脚本，有无 `defer` | 没有外部文件要获取 | parser 到达该元素且没有待等的阻塞样式表时执行；没有 `src` 时 `defer` 不起延后作用 |

`defer` 适合需要完整 DOM、且多个外部经典脚本之间要保持文档顺序的代码。`async` 适合不依赖解析结果、也不依赖其他脚本的独立工作，例如统计脚本。模块脚本默认就像 `defer` 一样延后执行；给它加 `async` 则改为就绪即执行。

## 为什么解析器有时必须停下来？

上表中，只有不带 `async` / `defer` 的经典脚本会让 parser 停下等待，原因在于解析的工作方式。parser 按顺序读取标记、逐个建立节点；经典脚本却能在文档还没解析完时查询和修改它，甚至用 `document.write()` 改变后面的解析结果。浏览器无法事先断定某个脚本不会这样做，只好先执行它再继续解析。所以，脚本的下载可以和其他资源的下载并行，但脚本的执行可能成为解析必须等待的点。

样式表也会挡住脚本，因为脚本可能读取样式（例如调用 `getComputedStyle()`）。但浏览器并不会先分析脚本里是否真的读了样式，而是按规则统一处理：HTML 规范定义了一个“阻塞脚本的样式表”集合，由 parser 创建、处于启用状态、`media` 条件匹配且仍在加载中的 `<style>` 或 stylesheet `<link>` 都会进入该集合。之后要执行的同步脚本或延后脚本，只要这个集合非空就要等待。因此，即便 `/reports.js` 只是给按钮注册事件，也可能要先等 `/reports.css` 加载完。

样式表还会阻塞渲染。本例的 stylesheet `<link>` 由 parser 在 `<head>` 中创建、处于启用状态且 `media` 匹配，所以它加载完之前，首帧可能推迟。这并不等于“所有 CSS 都下载完才能开始绘制”：某个资源是否阻塞渲染、是否阻塞脚本，各有各的判定条件。

以下是报表页的初始 HTML。后文只跟踪 `<head>` 中的样式表和模块脚本，以及正文里的排序按钮和图片；标题的 `id` 和按钮中的 SVG 图标与加载顺序无关。

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

服务器输出的初始顺序是 May → April。两个按钮先带着原生 `disabled` 属性输出：模块还没装好处理器时，用户点了也没有反应，与其让点击被静默丢掉，不如明确显示为不可用。

以下是 `/reports.js` 的最小实现，只展示处理器何时安装，以及如何同步列表和按钮状态，不涉及 URL 与浏览器历史。末尾的 `if` 是一段就绪检查（guard）：文档仍在解析（`readyState` 为 `loading`）时等 `DOMContentLoaded` 再初始化，否则立即初始化。本例的模块默认延后到解析结束才执行，此时 `readyState` 已是 `interactive`，所以总是走立即初始化的分支；`loading` 分支是为在解析期间就运行的其他入口准备的。

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

下表沿时间顺序列出页面状态。前两行对照两种资源返回顺序：CSS 先到、模块后到；或模块先到、CSS 还在加载。两种情况都会进入第三行：parser 已结束，模块可以运行。

| 此刻的资源状态 | parser、DOM 与首帧 | 排序处理器与就绪事件 |
|---|---|---|
| 正文已解析为 DOM（此时 `readyState=interactive`），`/reports.css` 已就绪，`/reports.js` 或其 `import` 依赖仍在下载，图片未完成 | 浏览器可能先绘出标题和 May → April；图片的 320×180 尺寸先占位；按钮仍为 disabled | 排序监听器尚未安装，按钮不能触发；`DOMContentLoaded` 仍等待 deferred 模块 |
| 模块响应先返回，但 CSS 仍是阻塞脚本的样式表 | parser 仍可继续补全正文；完成解析后 `readyState` 变为 `interactive`，模块执行仍要等 CSS 解除阻塞 | 按钮继续 disabled；模块未运行，`DOMContentLoaded` 尚未触发 |
| parser 已结束（`readyState=interactive`），模块及其依赖已可执行，CSS 已解除阻塞 | 模块同步调用初始化函数，保留 May → April 初始顺序，随后启用两个按钮 | 排序监听器和初始 `aria-pressed=true/false` 已就绪；普通同步模块执行结束后才派发 `DOMContentLoaded` |
| 用户点已启用的 **Oldest first** | 不再解析 HTML；处理器按日期重建列表行 | `aria-pressed` 变为 `false/true`，顺序变为 April → May |

这张表把“DOM 已建好”“可以绘制”和“处理器已绑定”三件事分开：模块没运行时按钮一直不可用，同步绑定和初始渲染完成后才启用。图片若到得较晚，HTML 中预先写好的宽高可以避免它加载后把文字挤开。

## `DOMContentLoaded` 和 `load` 分别说明什么？

上面的表格已经用到这两个事件，这里把它们各自保证什么说清楚。

`DOMContentLoaded` 在 HTML parser 完成解析、并执行完延后脚本后派发到 `Document`。顺序是：parser 停止时，`document.readyState` 先变为 `interactive`；这时延后脚本可能还在等模块文件、模块依赖或阻塞脚本的样式表；等它们依次执行完，才派发 `DOMContentLoaded`。由于延后脚本要等阻塞脚本的样式表，样式表也能间接推迟这个事件。

“执行完”只指脚本的同步部分。模块及其依赖都同步求值时，模块代码会在事件前全部跑完；模块里有顶层 `await` 时，`await` 之后的代码可能在事件之后才继续，依赖了含顶层 `await` 模块的代码也可能被推迟。初始化如果把后续工作放进 Promise 回调或网络请求，同样可能晚于该事件。所以 `DOMContentLoaded` 不代表应用初始化全部完成，它也不等待图片或 `async` 脚本。

`load` 事件在 `Window` 上监听。出于历史兼容，HTML 让这个事件的 target 指向文档，所以回调里 `event.currentTarget` 是 `window`，`event.target` 却是 `document`。触发前，`readyState` 已变为 `complete`，所有会延迟 `load` 的资源都已加载完成，通常包括普通图片、样式表、脚本和 iframe；懒加载的资源一般不会挡住它。确切范围由 HTML 规范的加载算法决定。

| 检查点与 `readyState` | 事件与监听位置 | 此时可依赖的条件 |
|---|---|---|
| parser 停止（`interactive`） | `readystatechange` 在 `Document` 上触发 | HTML 已解析完；延后脚本仍可能在执行或等待 |
| DOM 内容加载完（`interactive`） | `DOMContentLoaded` 在 `Document` 上触发 | parser 延后脚本已处理；图片和 `async` 脚本不作为此事件的等待条件，模块的异步延续仍可能继续 |
| `load`（`complete`） | 监听器在 `Window` 上运行；`event.target` 为 `Document` | 会延迟 load 的资源已完成；应用 API、hydration 或其他 Promise 仍可能未完成 |

这些事件和状态本身不报告首帧，也不追踪应用自己的初始化结果。本例正常执行同步初始化时，排序按钮确实在 `DOMContentLoaded` 前启用；异步初始化的应用则需要自己的就绪信号。

## 脚本晚到时，怎样避免错过 `DOMContentLoaded`？

`DOMContentLoaded` 只派发一次，不是一个之后还能订阅的状态。代码若通过动态导入或延迟执行，在事件之后才注册监听器，处理器永远不会被调用。前面 `/reports.js` 末尾的就绪检查正是为此而写：读到 `document.readyState` 仍是 `loading` 时，注册一次性监听器，在事件触发时调用 `initializeReportControls()`；否则说明解析已结束，直接初始化。同步执行的 JavaScript 不会被浏览器事件打断，所以检查状态和注册监听器之间不会恰好插进一次 `DOMContentLoaded`。

回顾 `readyState` 的三个值：`loading` 表示 HTML parser 仍在解析；`interactive` 表示解析已结束，但延后脚本和子资源可能尚未完成；`complete` 表示文档已加载完成。这个就绪检查只保证 DOM 已可查询：若初始化依赖尚未执行的 defer/module 脚本副作用，应等待该脚本自己的就绪信号。文档状态也不代表报表 API 请求、React hydration 或其他应用异步初始化已经完成；若初始化包含这类异步工作，仍需单独表示并等待。

所以，判断主要内容何时出现要看绘制，判断排序按钮能否使用要看它的初始化状态，两者不能用同一个事件代替。首帧可以早于 `load`；报表内容已经显示时，模块也可能还没注册排序处理器。反过来，`DOMContentLoaded` 触发后，主线程上的一个长任务仍会让点击处理排队等待。可见时点和就绪事件的区别见[浏览器如何把 URL 变成第一帧？](../browser/browser-basics.md)；用户侧的加载与交互数据见[如何测量并诊断网页性能问题？](../performance/performance-metrics-and-analysis.md)。

> [!info]- 来源
> - 解析器插入的经典脚本、`async`、`defer` 与模块调度：[WHATWG HTML：script processing model](https://html.spec.whatwg.org/multipage/scripting.html#script-processing-model)，Living Standard（2026-11-11 更新），外部/内联脚本、defer 模块列表与 async 集合。核对日期：2026-11-12。
> - parser 等待时允许浏览器推测获取后续资源：[WHATWG HTML：Speculative HTML parsing](https://html.spec.whatwg.org/multipage/parsing.html#speculative-html-parsing)，Living Standard（2026-11-11 更新）；这项预取优化的具体时机依实现而异。核对日期：2026-11-12。
> - 脚本阻塞样式表的条件：[WHATWG HTML：interactions of styling and scripting](https://html.spec.whatwg.org/multipage/semantics.html#interactions-of-styling-and-scripting)，Living Standard（2026-11-11 更新），parser 创建、样式表有效状态、media 匹配及阻塞集合。核对日期：2026-11-12。
> - 样式表链接可能阻塞渲染的条件：[WHATWG HTML：link type stylesheet](https://html.spec.whatwg.org/multipage/links.html#link-type-stylesheet) 与 [render-blocking mechanism](https://html.spec.whatwg.org/multipage/dom.html#render-blocking-mechanism)，Living Standard（2026-11-11 更新），parser 创建的 stylesheet link 可能 render-blocking；外链资源处理步骤检查 `media` 匹配与 render-blocking 状态。核对日期：2026-11-12。
> - 解析结束时的 `interactive`、延后脚本、`DOMContentLoaded` 与 `load` 派发：[WHATWG HTML：The end](https://html.spec.whatwg.org/multipage/parsing.html#the-end)，Living Standard（2026-11-11 更新），parser 结束、deferred script 队列、DOM content loaded 与窗口 load event。核对日期：2026-11-12。
> - `document.readyState` 的 `loading`、`interactive`、`complete` 及 `readystatechange`：[WHATWG HTML：Reporting document loading status](https://html.spec.whatwg.org/multipage/dom.html#reporting-document-loading-status)，Living Standard（2026-11-11 更新）。核对日期：2026-11-12。
> - 顶层 `await` 与模块依赖的异步求值：[ECMAScript 2027：Module evaluation](https://tc39.es/ecma262/#sec-moduleevaluation)，异步模块求值及其依赖关系。DOMContentLoaded / load 的触发顺序由上述 HTML 算法决定。核对日期：2026-11-12。
