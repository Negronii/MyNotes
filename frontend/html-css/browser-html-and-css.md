# 脚本如何影响 HTML 解析与文档就绪？

案例背景：报表服务器已返回标题、筛选按钮和初始行，浏览器还在解析 HTML，并同时获取 `/reports.css` 与 `/reports.js`。用户要尽快看到内容，之后点击按钮时脚本也必须已经注册处理器。下面按脚本下载、执行、文档就绪的先后关系判断哪些工作会挡住哪一步。

## 不同脚本属性怎样改变解析顺序？

表格说的是 HTML parser（HTML 解析器）插入的脚本；动态插入的脚本有不同默认调度，不能把它们混为一谈。

| 脚本形式 | 下载与解析的关系 | 运行时机与顺序 |
|---|---|---|
| 外部经典脚本，不带 `async` / `defer` | parser 遇到时开始获取并暂停继续解析 | 资源可运行后在 parser 继续前执行，保持文档顺序 |
| 外部经典脚本 `defer` | 与解析并行获取 | 解析完成后、`DOMContentLoaded` 前执行；多个 defer 脚本按文档顺序 |
| 外部经典脚本 `async` | 与解析并行获取 | 下载就绪后尽快执行；若解析还在进行，会暂时打断解析；不保证多个 async 脚本的顺序 |
| 普通模块脚本 | 模块及依赖图与解析并行获取 | 默认延后到解析完成后执行，遵循模块依赖关系 |
| `async` 模块脚本 | 模块及依赖图与解析并行获取 | 模块图就绪后尽快执行，不保证相对其他异步脚本的顺序 |
| 内联经典脚本，有无 `defer` | 没有外部文件要获取 | parser 到达该元素且没有待等的阻塞样式表时执行；没有 `src` 时 `defer` 不起延后作用 |

`defer` 适合依赖已解析文档、且需要保持外部经典脚本文档顺序的代码。`async` 适合执行不依赖解析结果或其他脚本的独立工作。模块脚本默认延后执行，给模块加 `async` 会改变这个选择。

## 为什么解析器有时必须停下来？

解析 HTML 就像按顺序读取标记并逐个建立节点。经典脚本能在节点还没建完时查询、修改文档，甚至用 `document.write()` 改变后续解析结果；浏览器不能一概把这种脚本当作与文档无关的文件而继续前进。因此，脚本获取可以和其他资源获取重叠，但脚本执行本身可能成为解析的依赖点。

样式表对脚本的影响不是浏览器先分析某段 JavaScript 是否调用了 `getComputedStyle()`。HTML 定义了一个脚本阻塞样式表状态：样式表元素由 parser 创建时已启用、参与样式规则、媒体条件匹配且尚未加载完成，才会进入该文档的阻塞集合。后续要执行的同步 parser 脚本或延后脚本，会按这个集合判断是否等待；即便 `/reports.js` 只给按钮注册事件，也可能先等 `/reports.css`。

适用于当前媒体环境的外部样式表通常会阻止首次绘制。不是“所有 CSS 必须全部下载后才能开始任何绘制”，而是当前渲染和脚本执行各自要满足规范定义的样式依赖。

沿用报表页的 HTML：

~~~html
<head>
  <link rel="stylesheet" href="/reports.css">
  <script type="module" src="/reports.js"></script>
</head>
<main>
  <h1 id="summary">Recent reports</h1>
  <img src="/report-summary.png" width="320" height="180" alt="Report summary">
  <div id="sort-controls">
    <button type="button" data-sort="recent" aria-pressed="true"><span>Most recent</span></button>
    <button type="button" data-sort="oldest" aria-pressed="false"><svg aria-hidden="true"></svg><span>Oldest first</span></button>
  </div>
  <ol id="reports"><li data-id="may">May report</li><li data-id="april">April report</li></ol>
</main>
~~~

这段沿用首帧章的完整报表结构：服务器先输出 May → April 的行，`#summary` 是片段目标；外部模块 `/reports.js` 在 parser 完成后运行。

| 此刻的资源状态 | parser 与首帧 | 筛选处理器与就绪事件 |
|---|---|---|
| HTML 主体和 `/reports.css` 已就绪，模块图仍在下载，图片还未到 | parser 已建出标题、按钮和两行；样式可用时浏览器可在渲染机会绘出首帧；图片宽高让空位先保留 | `reports.js` 尚未运行，按钮还没有处理器，`DOMContentLoaded` 尚未触发 |
| `/reports.css` 仍是当前 parser 创建的阻塞样式表，模块图已就绪 | parser 仍可继续解析普通模块脚本后的 HTML；若当前样式表阻止渲染，首帧会等到样式依赖解除 | 普通模块仍要等解析结束、模块图就绪且文档没有阻塞脚本的样式表；脚本之后才能注册处理器，随后才排入 `DOMContentLoaded` |

在表格第一行的状态下，本页可以先显示标题与预渲染行；用户如果过早点击，页面还可能没有 listener。待模块图与阻塞样式表条件满足，`/reports.js` 运行并注册处理器。若图片较晚到，预留的宽高减少它到达后挤动文字的机会。

## `DOMContentLoaded` 和 `load` 分别说明什么？

`DOMContentLoaded` 在文档解析完成、parser 的延后脚本队列处理流程之后触发；普通 `defer` 脚本和没有异步模块依赖、且模块本身没有顶层 `await` 的模块代码会在此流程同步运行，因此可在事件前注册处理器。若模块使用顶层 `await`、依赖异步模块，或只启动一个异步请求并把后续工作放进 Promise 回调，应用的后续初始化可以晚于 `DOMContentLoaded`；因此这个事件不代表所有异步初始化已完成。它不等图片或 `async` 脚本完成。因为延后脚本可能等待脚本阻塞样式表，所以样式表也可能间接推迟这个事件。

`load` 要等文档中所有仍会延迟该事件的资源；普通图片、样式表、脚本和子框架可能在其中，懒加载资源通常不必挡住它。具体资源是否延迟 load 由 HTML 的加载算法定义。两种事件都不是“首帧已出现”或“按钮已可用”的指标。

两种事件都不能回答“用户什么时候第一次看到主要内容”或“筛选按钮现在是否可用”。首帧可以早于 `load`，而报表内容也可能已显示、模块脚本还没注册筛选处理器。反过来，`DOMContentLoaded` 触发后，一次长脚本任务仍会让点击处理器排队等待。可见时点和就绪事件的区别见[浏览器如何把 URL 变成第一帧？](../browser/browser-basics.md)；用户侧的加载与交互数据见[如何测量并诊断网页性能问题？](../performance/performance-metrics-and-analysis.md)。

> [!info]- 来源
> - 解析器插入的经典脚本、`async`、`defer` 与模块调度： [WHATWG HTML：脚本元素](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)，持续更新规范，脚本准备与执行算法章节。核对日期：2026-11-06。
> - 阻塞脚本样式表的判定状态： [WHATWG HTML：样式与脚本交互](https://html.spec.whatwg.org/multipage/semantics.html#has-a-style-sheet-that-is-blocking-scripts)，持续更新规范，media 匹配、启用与加载状态条件。核对日期：2026-11-06。
> - 延后脚本、模块脚本到 `DOMContentLoaded` / `load` 的顺序： [WHATWG HTML：解析结束](https://html.spec.whatwg.org/multipage/parsing.html#the-end)与[HTML 中调用脚本](https://html.spec.whatwg.org/multipage/webappapis.html#calling-scripts)，持续更新规范，解析结束、延后脚本队列和模块求值步骤。核对日期：2026-11-06。
