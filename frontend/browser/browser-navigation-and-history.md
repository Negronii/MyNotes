# 每次 URL 变化都会加载新文档吗？

**案例：** 沿用[上一章](browser-basics.md)的报表页面。用户先打开 `https://example.test/reports?sort=recent#summary`，随后点“最早优先”，之后可能按浏览器的后退键。要让这三个时刻都显示正确的报表顺序，先要分清每次 URL 变化时，浏览器是在加载新文档、跳到片段位置，还是只改写当前文档的历史地址。

## URL 分量怎样对应到浏览器导航？

以本例地址为例，`https:` 是 scheme（方案），`example.test` 是 host（主机），`/reports` 是 path（路径），`?sort=recent` 是 query（查询），`#summary` 是 fragment（片段）。这个 HTTPS 地址的 origin（源）由 scheme、host 和 port 三者确定，省略的 port 取默认值 443。不是所有 URL 都有 `//authority`：`mailto:reports@example.test` 就没有 HTTP(S) 式主机与路径结构。

在脚本中，`location` 对象按这些分量暴露当前地址：`location.href` 读取完整 URL，给它赋值会触发导航；`protocol` 带结尾冒号，`host` 包含非默认端口，`hostname` 不含端口，`port` 是非默认端口或空字符串，`pathname` 是路径，`search` 保留开头的 `?`，`hash` 保留开头的 `#`。解析 URL 时用 `URL` 和 `URLSearchParams`，不要手动切分字符串。查询参数缺失时 `get()` 返回 `null`；存在时返回的总是字符串，例如 `"2026"` 不是数字。`getAll()` 可读同名多值，`set()` 替换同名值，`append()` 则追加一项；序列化时按 URL 查询参数规则编码。

同一标签页的会话历史可以包含不同 origin 的文档，因此 `history.back()`、`forward()` 和 `go()` 可能移到跨源页面。`history.go(n)` 按偏移量移动：正数向前、负数向后、`0` 重新加载当前页；超出范围则什么也不做。下文会讲到 `pushState()` / `replaceState()` 只能写入同源 URL，但这条限制只针对改写地址，并不意味着后退只能在同源历史项之间进行。

## 用 URL 参数表达排序状态

把排序写进 query，地址就能被复制、分享和后退恢复。本例只接受 `sort=recent` 和 `sort=oldest`；后面代码里的 `sortFromUrl()` 把缺失或未知的值都当作 `recent` 显示，直到用户选择另一种排序才写回 URL。写回时先从 `location.href` 解析现有地址，再只改 `sort`，所以路径、其他查询参数和 `#summary` 片段都保留；不过 `URLSearchParams` 会重新序列化整个查询，空格可能从 `%20` 变成 `+`。查询参数来自地址栏或外部链接，必须按业务允许的值校验；口令和访问令牌也不要放进 URL。

写回 URL 有多种方式，它们对文档和历史的影响不同：

| 操作 | 当前地址、文档与历史的结果 |
|---|---|
| 打开另一个地址：`<a>`、设置 `location.href`、调用 `location.assign()` | 通常加载另一个 `Document` 并留下新历史项；若目标含 fragment，且目标与当前 URL 除 fragment 外相同，则沿用当前 `Document` 并定位片段 |
| `location.replace(url)` | 替换当前历史项；是否沿用当前 `Document` 适用上一行的片段条件 |
| `location.reload()` | 重新加载当前文档，即使地址不变；不增加历史项，资源仍可能来自缓存 |
| `pushState(...)` | 保留当前 `Document` 并新增一项历史状态；调用本身不请求新文档 |
| `replaceState(...)` | 保留当前 `Document` 并修改当前历史项；调用本身不请求新文档 |

History API 的目标 URL 必须符合当前文档可改写 URL 的规则。对本例的 HTTPS 页面，可以改路径、查询和片段；scheme、username、password、host、port 要保持相同。`pushState()` 和 `replaceState()` 都不会请求新地址，调用本身也不会派发 `popstate` 或 `hashchange`。所以应用若要显示与新 URL 对应的内容，必须自己更新界面；若需要服务器上的其他资源，应正常导航或显式发出请求。本例的排序只需在客户端重排已有数据，因此选用 `pushState()`。

## 让排序状态跟随地址栏与前进后退

报表页面初始地址是 `/reports?sort=recent#summary`。浏览器用收到的 HTML 创建 `Document`，其中已有 `h1#summary`、两个排序按钮以及 May、April 两行，并通过 `<script type="module" src="/reports.js"></script>` 加载客户端模块。为了简化，本例把行数据放在客户端的 `records` 数组里，由 `renderReports()` 每次根据 URL 中的排序重建列表。若数据要从服务器获取，更新 URL 后还需按新状态请求结果，并处理加载中、错误和过期响应。

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

`renderReports()` 先按 URL 状态选顺序，再同步两个按钮的 `aria-pressed`，最后用 `replaceChildren()` 写入行。初始服务器 HTML 已显示 May → April；用户点“最早优先”后，新地址是 `/reports?sort=oldest#summary`，按钮切成 `false/true`，行变为 April → May。这里创建的是新的 `li` 节点；另一种做法是移动已有的行节点，见[浏览器怎样查询、更新 DOM 并响应用户输入？](../browser-apis/dom-manipulation-and-events.md#什么时候用父级监听器处理子控件？)。若用户分享一条 `sort=oldest` 深链，`reports.js` 的初次运行会按 URL 修正列表；要让首批 HTML 本身就显示正确顺序，服务器也应按查询参数生成行和按钮状态。若地址是未知值，例如 `sort=other`，本例只按 `recent` 显示；点已经选中的 “Most recent” 会提前返回，只有选另一种排序才会改写地址。

委托监听器用 `event.target.closest("button[data-sort]")` 从点击目标向上找按钮，因此点按钮内的文字或 SVG 图标都会进入同一处理器；`controls.contains(button)` 再确认匹配到的按钮属于这组控件。

| 时点 | 历史项、文档与事件 | 地址与报表 UI |
|---|---|---|
| 初次打开 | 浏览器用收到的 HTML 创建一个 `Document`；模块初次运行读取 URL。 | `sort=recent`；按钮为 `true/false`，列表为 May → April。 |
| 点击 **Oldest first** | `pushState()` 新增同一 `Document` 的历史项；不请求新 HTML，也不派发 `popstate` / `hashchange`。点击处理器自己调用 `renderReports()`。 | 地址变为 `sort=oldest`；按钮为 `false/true`，列表为 April → May。 |
| 浏览器 Back | 激活先前的同文档历史项并派发 `popstate`；`#summary` 没变，本例不涉及 `hashchange`。 | 监听器读取当前 URL，恢复 `sort=recent`、`true/false` 与 May → April。 |
| 浏览器 Forward | 再激活 `sort=oldest` 历史项并派发 `popstate`。 | 监听器再次从 URL 得到 oldest，恢复 `false/true` 与 April → May。 |

本例用 `pushState(null, "", url.href)` 添加新历史项并记录 URL，不把排序状态另存进 `history.state`；点击处理器再主动调用 `renderReports()`。因此本例 `popstate` 的 `event.state` 为 `null`，排序仍从当前 URL 读取。应用也可以把状态放进 `pushState()` 的第一个参数，之后从 `popstate` 事件的 `event.state` 读回。若用户继续后退，离开了这个文档，当前页面的 `popstate` 监听器就不再参与；另一个文档的恢复或重新加载由浏览器负责。

片段变化与 History API 容易混淆，单独对比一下。普通导航只有在目标含 fragment、且与当前 URL 除 fragment 外完全相同时，才会走同文档的片段导航。以页面已有的 `ol#reports` 为例，在 `/reports?sort=oldest#summary` 上执行 `location.hash = "#reports"`，会沿用当前 `Document`、新增一项历史记录并滚动到列表。滚动由浏览器完成；本例的 `popstate` 监听器也会被触发，从 URL 重读排序并重建列表，顺序不变。本机 Chrome 157 在这条路径上先派发 `popstate`（`state` 为 `null`），再派发 `hashchange`，与规范的顺序一致。

反过来，在 `/reports?sort=recent#summary` 上用 `location.assign("?sort=oldest#summary")` 改查询，即使保留了 `#summary`，也会导航到一个新的 `Document`。而用 `pushState()` 改成另一个片段时，浏览器不会滚动，调用本身也不派发 `popstate` 或 `hashchange`；只有用户之后通过前进后退回到该历史项时，才按历史遍历的步骤处理。本例的排序历史项只改 query、保留 `#summary`，所以前进后退只触发 `popstate`，不触发 `hashchange`。客户端路由器也建立在这些历史项之上，但改 URL 和更新视图始终是两件事。

回到开头的三个时刻：首次打开时，服务器只处理路径和查询，`#summary` 由浏览器用来定位；点击排序改成 `sort=oldest` 后，仍是同一个 `Document`，浏览器不重新请求或解析 `/reports`，新列表由应用自己生成；后退时由 `popstate` 监听器按 URL 恢复顺序。这样地址既能复制、能返回，又不会把 History API 误当成网络导航。

## 定时导航怎样用文本更新并允许取消？

前面的排序始终留在同一文档内。有时页面确实要离开当前文档，但想先给用户一个等待和取消的机会，例如显示“5 秒后打开 example.com”。下面用倒计时文本加取消按钮实现。`setInterval(..., 1000)` 中的 1000 毫秒只是期望间隔，不保证每秒准时执行；主线程繁忙或浏览器对后台页面的计时器节流会让回调变晚。此代码按回调次数减秒，延迟会把实际跳转推迟；若需要按真实截止时刻倒数，应每次用当前时间重算剩余量。只有在归零回调执行之前点取消，清除定时器才能阻止跳转。归零回调一旦执行，会先禁用取消按钮、显示“正在跳转…”，再调用 `location.assign()`；此时 `clearInterval()` 已无法撤销已经开始的导航。

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

**延伸：** [DOM 事件如何传播，何时适合事件委托？](../browser-apis/dom-manipulation-and-events.md)解释点击处理器如何收到按钮事件；如果路由切换还要等待数据加载器并显示 pending/error 状态，见[React 路由怎样把地址映射到界面并加载数据？](../frameworks/react-routing-and-navigation.md)中的 Data Mode（数据模式）；组件状态更新见[React如何把一次用户操作变成界面更新？](../frameworks/react-basics.md)。

> [!info]- 来源
> - URL 分量和序列化：[WHATWG URL Standard：URL representation](https://url.spec.whatwg.org/#url-representation)，Living Standard（2026-10-19 更新），URL record 组成。核对日期：2026-11-12。
> - 地址栏分量与 `assign()` / `replace()` / `reload()`：[WHATWG HTML：Location interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-location-interface)，Living Standard（2026-11-11 更新），`Location` API。核对日期：2026-11-12。
> - 普通导航、片段导航、URL/history 更新、历史步骤应用与刷新：[WHATWG HTML：Navigation and session history](https://html.spec.whatwg.org/multipage/browsing-the-web.html#navigate)，Living Standard（2026-11-11 更新），[fragment navigations](https://html.spec.whatwg.org/multipage/browsing-the-web.html#navigate-fragid)、[URL and history update steps](https://html.spec.whatwg.org/multipage/browsing-the-web.html#url-and-history-update-steps)、[updating the document for a history step](https://html.spec.whatwg.org/multipage/browsing-the-web.html#update-document-for-history-step-application)、[reloading](https://html.spec.whatwg.org/multipage/browsing-the-web.html#apply-the-reload-history-step)。核对日期：2026-11-12。
> - History API 可改写 URL 的组成条件、`pushState()` / `replaceState()` 与遍历：[WHATWG HTML：History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，Living Standard（2026-11-11 更新），同文档 URL 改写规则、state 与 delta traversal。核对日期：2026-11-12。
> - `popstate` / `hashchange` 的事件对象及相关事件步骤：[WHATWG HTML：Event interfaces](https://html.spec.whatwg.org/multipage/nav-history-apis.html#event-interfaces) 和上述 navigation / history-step 算法，Living Standard（2026-11-11 更新）；事件发生时机另以本机 Chrome 157 回放为准。核对日期：2026-11-12。
> - URL 查询参数的读取、重复值和序列化：[WHATWG URL Standard：URLSearchParams](https://url.spec.whatwg.org/#urlsearchparams-class)，Living Standard（2026-10-19 更新），`get()`、`getAll()`、`set()`、`append()` 与 form-urlencoded 序列化。核对日期：2026-11-12。
> - 倒计时的文本更新与计时器初始化/取消：[WHATWG DOM：Node.textContent](https://dom.spec.whatwg.org/#dom-node-textcontent)；[WHATWG HTML：Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)，Living Standard（2026-11-11 更新）。超时表示最早可运行时间，实际回调还要等待事件循环调度。核对日期：2026-11-12。
