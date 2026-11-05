# How do scripts affect HTML parsing and document readiness? / 脚本如何影响 HTML 解析与文档就绪？

A parser-inserted classic script without `async` or `defer` can pause HTML parsing while it is fetched and run; it may also wait for an earlier stylesheet when it can inspect style. `defer` and ordinary module scripts fetch while parsing continues, then execute after parsing in their specified order; `async` scripts execute when ready without preserving relative order. Choose a mode from the script's dependencies and required start time, not from one placement rule. / 未带 `async` 或 `defer` 的解析器插入经典脚本可能在获取和执行期间暂停 HTML 解析；如果脚本能读取样式，它也可能等待之前的样式表。`defer` 与普通模块脚本会在解析期间获取，再按相应顺序于解析完成后执行；`async` 脚本就绪后即执行，不保持相对顺序。应根据依赖关系和所需运行时机选择模式，而不是依赖单一的位置口诀。

## Script scheduling / 脚本调度

| Script | Fetch | Execution | Relative order |
|---|---|---|---|
| Parser-inserted classic, no scheduling attribute | Parser fetches it; parser pauses | When available and eligible to run | Parser order |
| External classic `defer` | In parallel with parsing | After parsing, before `DOMContentLoaded` | Document order among deferred classic scripts |
| External classic `async` | In parallel with parsing | As soon as available; parsing can pause to run it | Not preserved |
| Module without `async` | Module graph loads in parallel with parsing | Deferred until parsing is complete | Module and dependency rules |
| Module with `async` | Module graph loads in parallel | As soon as its graph is ready | Not preserved relative to other async work |
| Classic inline with `defer` | No fetch | Runs when parser reaches it | `defer` has no effect without `src` |

`DOMContentLoaded` fires after the document has been parsed and deferred and ordinary module scripts have executed; it does not wait for images or `async` scripts. A deferred script can itself wait for a stylesheet that blocks scripts, so stylesheet loading can delay that script and therefore `DOMContentLoaded`. `load` waits on a wider set of dependent resources. These milestones do not promise that every image is decoded or that the page is visually complete.

Use `defer` for ordered external classic scripts that need the parsed document. Use `async` for a script whose execution does not depend on other scripts or parser output. Module scripts are deferred by default; adding `async` changes that schedule. Dynamically inserted scripts have different defaults from parser-inserted ones, so state which case you mean.

## Why scripts can pause the parser / 脚本为何会暂停解析

A classic script can inspect or modify the document while the parser is constructing it; it can also write markup that changes parsing. The browser therefore cannot always continue as if the script were an independent resource. A parser-blocking script's fetch can overlap resource discovery and other downloads, but its execution creates a dependency point.

Stylesheets matter when a pending script can read style information: the browser may delay that script until a blocking stylesheet is available. This is why “all CSS must finish before first paint” is inaccurate; the relevant blocking relationships depend on the script and style state.

~~~html
<head>
  <link rel="stylesheet" href="/app.css">
  <script src="/app.js" defer></script>
</head>
~~~

Here HTML parsing and script fetching can proceed together. Once parsing ends, `app.js` executes before `DOMContentLoaded`; it can rely on the parsed document, but should not assume images have loaded.

**See also:** [How does a browser turn a URL into pixels?](../browser/browser-basics.md) places script scheduling in the navigation path; [When does browser JavaScript run relative to a frame?](../runtime/event-loop.md) explains tasks, microtasks, and rendering opportunities; [How should browser performance be measured and diagnosed?](../performance/performance-metrics-and-analysis.md) distinguishes readiness events from user-visible performance.

**Standards / 规范：** [WHATWG HTML: the script element and script preparation](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element); [WHATWG HTML: DOMContentLoaded](https://html.spec.whatwg.org/multipage/dom.html#the-end); checked 2026-11-05.
