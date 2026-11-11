# 每次 URL 变化都会加载新文档吗？

案例背景：用户先打开 `https://example.test/reports?sort=recent#summary`，随后点“最早优先”并可能按浏览器后退。要让这三个时点显示正确的报表，先判断浏览器是在换文档、跳转片段，还是只更新当前文档的历史地址。

## URL 分量怎样对应到浏览器导航？

以本例地址为例，`https:` 是 scheme (方案)，`example.test` 是 host (主机)，`/reports` 是 path (路径)，`?sort=recent` 是 query (查询)，`#summary` 是 fragment (片段)。本例 HTTPS 地址的 origin (源) 由 scheme、host 和 port 标识。不是所有 URL 都有 `//authority`：`mailto:reports@example.test` 就没有 HTTP(S) 式主机与路径结构。

`location.href` 读取完整 URL，赋值会导航；`protocol` 带结尾冒号，`host` 包含非默认端口，`hostname` 不含端口，`port` 是非默认端口或空字符串，`pathname` 是路径，`search` 保留开头的 `?`，`hash` 保留开头的 `#`。用 `URL` 和 `URLSearchParams` 解析，不要手动切分字符串；查询参数缺失时 `get()` 返回 `null`，已存在的值是字符串，例如 `"2026"` 不是数字。`getAll()` 可读同名多值，`set()` 替换同名值，`append()` 则追加一项；序列化时按 URL 查询参数规则编码。

浏览器历史栈可以包含不同 origin（源）的文档，因此 `history.back()`、`forward()` 和 `go()` 可能遍历到跨源页面。`history.go(n)` 按偏移量移动历史项：正数向前、负数向后、零会重新载入当前页；超出范围则不动作。History API 对 `pushState()` / `replaceState()` 新 URL 的同源要求，不等于浏览器只能在同源历史项之间后退。

## 用 URL 参数表达排序状态

本例只接受 `sort=recent` 和 `sort=oldest`；`sortFromUrl()` 将缺失或未知值按 `recent` 渲染，直到用户选择另一种排序才写入 URL。写回时从 `location.href` 解析现有地址，再更新 `sort`，所以路径、其他查询参数的值和 `#summary` 片段仍在；`URLSearchParams` 会重新序列化查询，空格可能从 `%20` 写成 `+`。查询参数来自地址栏或外部链接，必须按业务允许值校验，也不要把口令或访问令牌放进 URL。

| 操作 | 当前地址、文档与历史的结果 |
|---|---|
| 打开另一个地址：`<a>`、设置 `location.href`、调用 `location.assign()` | 通常加载另一个 `Document` 并留下新历史项；若目标含 fragment，且目标与当前 URL 除 fragment 外相同，则沿用当前 `Document` 并定位片段 |
| `location.replace(url)` | 替换当前历史项；是否沿用当前 `Document` 适用上一行的片段条件 |
| `location.reload()` | 重新加载当前文档，即使地址不变；不增加历史项，资源仍可能来自缓存 |
| `pushState(...)` | 保留当前 `Document` 并新增一项历史状态；调用本身不请求新文档 |
| `replaceState(...)` | 保留当前 `Document` 并修改当前历史项；调用本身不请求新文档 |

History API 的目标 URL 必须符合当前文档可改写 URL 的规则。对本例的 HTTPS 页面，可以改路径、查询和片段；scheme、username、password、host、port 要保持相同。`pushState()` 和 `replaceState()` 都不会发起该地址的网络请求，也不会因调用本身派发 `popstate` 或 `hashchange`。应用若要显示与新 URL 对应的内容，仍须自己同步界面；目标是别的服务器资源时，应正常导航或显式发出请求。

## 让排序状态跟随地址栏与前进后退

报表页面初始地址是 `/reports?sort=recent#summary`。浏览器用收到的 HTML 创建 `Document`，其中已有 `h1#summary`、两个排序按钮以及 May、April 两行；下面 HTML 示例中的普通模块脚本由 `<script type="module" src="/reports.js"></script>` 引用。本例把行数据放进客户端 `records` 数组，让 `renderReports()` 每次从 URL 状态重建行。若数据由服务器提供，更新 URL 后还需按该状态请求新结果，并处理加载、错误和过期响应。

~~~html
<!-- /reports?sort=recent 的服务端 HTML 初始状态 -->
<!-- 页面 head 中的客户端模块引用 -->
<script type="module" src="/reports.js"></script>
<h1 id="summary">Recent reports</h1>
<img src="/report-summary.png" width="320" height="180" alt="Report summary">
<div id="sort-controls">
  <button type="button" data-sort="recent" aria-pressed="true"><span>Most recent</span></button>
  <button type="button" data-sort="oldest" aria-pressed="false">
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
~~~

以下是 `/reports.js` 中的代码，不是 HTML 里的内联脚本：

~~~javascript
const records = [
  { id: "may", date: "2026-05-01", label: "May report" },
  { id: "april", date: "2026-04-01", label: "April report" },
];
const list = document.querySelector("#reports");
const controls = document.querySelector("#sort-controls");

function sortFromUrl() {
  return new URL(location.href).searchParams.get("sort") === "oldest"
    ? "oldest"
    : "recent";
}

function renderReports(sort) {
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

function chooseSort(sort) {
  if (sort !== "recent" && sort !== "oldest") return;
  if (sort === sortFromUrl()) return;
  const url = new URL(location.href);
  url.searchParams.set("sort", sort);
  history.pushState(null, "", url.href);
  renderReports(sort);
}

controls.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  const button = target?.closest("button[data-sort]");
  if (!button || !controls.contains(button)) return;
  chooseSort(button.dataset.sort);
});
window.addEventListener("popstate", () => renderReports(sortFromUrl()));
renderReports(sortFromUrl());
~~~

`renderReports()` 先按 URL 状态选顺序，再同步两个按钮的 `aria-pressed`，最后用 `replaceChildren()` 写入行。初始服务器 HTML 已显示 May → April；用户点“最早优先”后，新地址是 `/reports?sort=oldest#summary`，按钮切成 `false/true`，行变为 April → May。这里创建的是新 `li` 节点；DOM 章将同一结果与移动既有行节点的做法对照。若用户分享一条 `sort=oldest` 深链，`reports.js` 的初次运行会按 URL 修正列表；要让首批 HTML 本身就显示正确顺序，服务器也应按查询参数生成行和按钮状态。若地址是未知值，例如 `sort=other`，本例只按 `recent` 显示；点已经选中的 “Most recent” 会提前返回，只有选另一种排序才会改写地址。

委托监听器用 `event.target.closest("button[data-sort]")` 从点击目标向上找按钮，因此点按钮内的文字或 SVG 图标都会进入同一处理器；`controls.contains(button)` 再确认匹配到的按钮属于这组控件。

| 时点 | 历史项、文档与事件 | 地址与报表 UI |
|---|---|---|
| 初次打开 | 浏览器用收到的 HTML 创建一个 `Document`；模块初次运行读取 URL。 | `sort=recent`；按钮为 `true/false`，列表为 May → April。 |
| 点击 **Oldest first** | `pushState()` 新增同一 `Document` 的历史项；不请求新 HTML，也不派发 `popstate` / `hashchange`。点击处理器自己调用 `renderReports()`。 | 地址变为 `sort=oldest`；按钮为 `false/true`，列表为 April → May。 |
| 浏览器 Back | 激活先前的同文档历史项并派发 `popstate`；`#summary` 没变，本例不涉及 `hashchange`。 | 监听器读取当前 URL，恢复 `sort=recent`、`true/false` 与 May → April。 |
| 浏览器 Forward | 再激活 `sort=oldest` 历史项并派发 `popstate`。 | 监听器再次从 URL 得到 oldest，恢复 `false/true` 与 April → May。 |

本例用 `pushState(null, "", url.href)` 添加新历史项并记录 URL，不把排序状态另存进 `history.state`；点击处理器再主动调用 `renderReports()`。因此本例 `popstate` 的 `event.state` 为 `null`，排序仍从当前 URL 读取。`pushState()` 也可在第一个参数中保存应用状态，其他应用可在 `popstate` 的事件对象中读取。若用户再后退离开这个文档，当前 listener 不接管另一文档的恢复或重新加载；浏览器处理的是另一条历史项及其页面状态。

只有目标 URL 与当前 URL 除 fragment 外完全相同，且目标含 fragment 时，普通导航才走同文档片段路径。以已有的 `ol#reports` 为例，从 `/reports?sort=oldest#summary` 执行 `location.hash = "#reports"` 会沿用当前 `Document`、增加一项历史记录并滚到列表。片段定位和滚动由浏览器完成，但本例的 `popstate` 监听器仍会从 URL 重读排序并重建列表，显示顺序不变。本机 Chrome 157 在该路径先派发 `popstate`（`state` 为 `null`），再派发 `hashchange`。反过来，从 `/reports?sort=recent#summary` 用 `location.assign("?sort=oldest#summary")` 改查询，即使保留 `#summary` 也会导航到另一个 `Document`。History API 调用 `pushState()` 改成另一个片段不会自动滚动，也不会因调用本身派发 `popstate` 或 `hashchange`；若用户稍后遍历该历史项，才按历史遍历步骤处理。本例的排序历史项只改 query、保留 `#summary`，Back/Forward 由 `popstate` 同步排序而不触发 `hashchange`。客户端路由器可以复用这些历史项，但 URL 变化与视图绘制是两项不同工作。

浏览器首次收到 `.../reports?sort=recent#summary` 时，`#summary` 是浏览器用来定位的片段，服务器只处理路径与查询。排序点击改成 `sort=oldest` 后，仍是同一个 `Document`：浏览器不重新解析 `/reports`，应用继续负责产生新列表节点。这个边界让地址可复制、可返回，同时不把 History API 误解成网络导航。

## 定时导航怎样用文本更新并允许取消？

这个倒计时为普通文档导航留下等待和取消窗口。`setInterval(..., 1000)` 中的 1000 毫秒是请求间隔，不承诺每秒准时执行；主线程繁忙或浏览器对后台页面的计时器节流会让回调变晚。此代码按回调次数减秒，延迟会把实际跳转推迟；若需要按真实截止时刻倒数，应每次用当前时间重算剩余量。只有最后一次回调开始导航前点取消，清除定时器才能阻止跳转。一旦归零回调开始 `location.assign()`，取消按钮会先禁用并显示“正在跳转…”，`clearInterval()` 不能撤销已经开始的导航。

~~~html
<p id="countdown" role="status">5 秒后打开 example.com。</p>
<button id="cancel-navigation" type="button">取消</button>
~~~

~~~javascript
const message = document.querySelector("#countdown");
const cancel = document.querySelector("#cancel-navigation");
let seconds = 5;

const timer = setInterval(() => {
  seconds -= 1;
  if (seconds === 0) {
    clearInterval(timer);
    cancel.disabled = true;
    message.textContent = "正在跳转…";
    location.assign("https://example.com/");
    return;
  }
  message.textContent = seconds + " 秒后打开 example.com。";
}, 1000);

cancel.addEventListener("click", () => {
  clearInterval(timer);
  message.textContent = "已取消跳转。";
  cancel.disabled = true;
});
~~~

**延伸：** [DOM 事件如何传播，何时适合事件委托？](../browser-apis/dom-manipulation-and-events.md)解释点击处理器如何收到按钮事件；如果路由切换还要等待数据加载器并显示 pending/error 状态，见[React 路由怎样把地址映射到界面并加载数据？](../frameworks/react-routing-and-navigation.md)中的 Data Mode（数据模式）；组件状态更新见[React 如何把用户操作变成更新后的界面？](../frameworks/react-basics.md)。

> [!info]- 来源
> - URL 分量和序列化：[WHATWG URL Standard：URL representation](https://url.spec.whatwg.org/#url-representation)，Living Standard（2026-10-19 更新），URL record 组成。核对日期：2026-11-12。
> - 地址栏分量与 `assign()` / `replace()` / `reload()`：[WHATWG HTML：Location interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-location-interface)，Living Standard（2026-11-11 更新），`Location` API。核对日期：2026-11-12。
> - 普通导航、片段导航、URL/history 更新、历史步骤应用与刷新：[WHATWG HTML：Navigation and session history](https://html.spec.whatwg.org/multipage/browsing-the-web.html#navigate)，Living Standard（2026-11-11 更新），[fragment navigations](https://html.spec.whatwg.org/multipage/browsing-the-web.html#navigate-fragid)、[URL and history update steps](https://html.spec.whatwg.org/multipage/browsing-the-web.html#url-and-history-update-steps)、[updating the document for a history step](https://html.spec.whatwg.org/multipage/browsing-the-web.html#update-document-for-history-step-application)、[reloading](https://html.spec.whatwg.org/multipage/browsing-the-web.html#apply-the-reload-history-step)。核对日期：2026-11-12。
> - History API 可改写 URL 的组成条件、`pushState()` / `replaceState()` 与遍历：[WHATWG HTML：History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，Living Standard（2026-11-11 更新），同文档 URL 改写规则、state 与 delta traversal。核对日期：2026-11-12。
> - `popstate` / `hashchange` 的事件对象及相关事件步骤：[WHATWG HTML：Event interfaces](https://html.spec.whatwg.org/multipage/nav-history-apis.html#event-interfaces) 和上述 navigation / history-step 算法，Living Standard（2026-11-11 更新）；事件发生时机另以本机 Chrome 157 回放为准。核对日期：2026-11-12。
> - URL 查询参数的读取、重复值和序列化：[WHATWG URL Standard：URLSearchParams](https://url.spec.whatwg.org/#urlsearchparams-class)，Living Standard（2026-10-19 更新），`get()`、`getAll()`、`set()`、`append()` 与 form-urlencoded 序列化。核对日期：2026-11-12。
> - 倒计时的文本更新与计时器初始化/取消：[WHATWG DOM：Node.textContent](https://dom.spec.whatwg.org/#dom-node-textcontent)；[WHATWG HTML：Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)，Living Standard（2026-11-11 更新）。超时表示最早可运行时间，实际回调还要等待事件循环调度。核对日期：2026-11-12。
