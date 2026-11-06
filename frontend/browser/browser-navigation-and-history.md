# 每次 URL 变化都会加载新文档吗？

案例背景：用户先打开 `https://example.test/reports?sort=recent#summary`，随后点“最早优先”并可能按浏览器后退。要让这三个时点显示正确的报表，先判断浏览器是在换文档、跳转片段，还是只更新当前文档的历史地址。

## URL 分量怎样对应到浏览器导航？

以本例地址为例，`https:` 是 scheme（方案），`example.test` 是 host（主机），`/reports` 是 path（路径），`?sort=recent` 是 query（查询），`#summary` 是 fragment（片段）。不是所有 URL 都有 `//authority`：`mailto:reports@example.test` 就没有 HTTP(S) 式主机与路径结构。

`location.href` 读取完整 URL，赋值会导航；`protocol` 带结尾冒号，`host` 包含非默认端口，`hostname` 不含端口，`port` 是非默认端口或空字符串，`pathname` 是路径，`search` 保留开头的 `?`，`hash` 保留开头的 `#`。用 `URL` 和 `URLSearchParams` 解析，不要手动切分字符串；查询参数缺失时 `get()` 返回 `null`，已存在的值是字符串，例如 `"2026"` 不是数字。`getAll()` 可读同名多值，`set()` 替换同名值，`append()` 则追加一项；序列化时按 URL 查询参数规则编码。

浏览器历史栈可以包含不同 origin（源）的文档，因此 `history.back()`、`forward()` 和 `go()` 可能遍历到跨源页面。`history.go(n)` 按偏移量移动历史项：正数向前、负数向后、零会重新载入当前页；超出范围则不动作。History API 对 `pushState()` / `replaceState()` 新 URL 的同源要求，不等于浏览器只能在同源历史项之间后退。

## 用 URL 参数表达筛选状态

本例只接受 `sort=recent` 和 `sort=oldest`；`sortFromUrl()` 会把缺失或未知值规范为 `recent`。写回时从 `location.href` 解析现有地址，再更新 `sort`，所以路径、其他查询参数和 `#summary` 片段仍在。查询参数来自地址栏或外部链接，必须按业务允许值校验，也不要把口令或访问令牌放进 URL。

| 需要的行为 | API / 行为 | 是否获取新文档 |
|---|---|---|
| 打开另一个地址并留下新历史项 | 点击 `<a>`、`location.href = url` 或 `location.assign(url)` | 通常换 `Document`；目标只是片段时可留在当前 `Document` |
| 打开地址并替换当前历史项 | `location.replace(url)` | 替换当前历史项；目标是否换 `Document` 仍取决于导航目标 |
| 重新载入当前地址 | `location.reload()` | 浏览器重新处理当前地址；资源是否来自缓存由加载过程决定 |
| 当前文档新增一项路由状态 | `history.pushState(state, "", sameOriginUrl)` | 否 |
| 修改当前历史项的路由状态 | `history.replaceState(state, "", sameOriginUrl)` | 否 |

History API 的目标 URL 必须符合当前文档可改写 URL 的规则；对本例的 HTTPS 页面，可以改路径、查询和片段，但不能改协议、主机或端口。`pushState()` 和 `replaceState()` 都不会发起该地址的网络请求，也不会因为调用本身派发 `popstate` 或 `hashchange`。应用若要显示与新 URL 对应的内容，仍须自己同步界面；目标是别的服务器资源时，应正常导航或显式发出请求。

## 让筛选状态跟随地址栏与前进后退

报表页面初始地址是 `/reports?sort=recent#summary`。这次服务器返回的 HTML 已包含 `h1#summary`、两个筛选按钮以及 May、April 两行；普通模块脚本由首帧示例头部的 `<script type="module" src="/reports.js"></script>` 引用。用户点击“最早优先”后，模块将查询参数改成 `sort=oldest`，并把已在客户端的数据按日期升序排进列表。若数据由服务器提供，更新 URL 后还需按该状态请求新结果，并处理加载、错误和过期响应。

~~~html
<!-- /reports?sort=recent 的服务端 HTML 初始状态 -->
<h1 id="summary">Recent reports</h1>
<img src="/report-summary.png" width="320" height="180" alt="Report summary">
<div id="sort-controls">
  <button type="button" data-sort="recent" aria-pressed="true"><span>Most recent</span></button>
  <button type="button" data-sort="oldest" aria-pressed="false"><svg aria-hidden="true"></svg><span>Oldest first</span></button>
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

`renderReports()` 先按 URL 状态选顺序，再同步两个按钮的 `aria-pressed`，最后用 `replaceChildren()` 写入行。初始服务器 HTML 已显示 May → April；用户点“最早优先”后，新地址是 `/reports?sort=oldest#summary`，按钮切成 pressed，行变为 April → May。若用户分享一条 `sort=oldest` 深链，`reports.js` 的初次运行会按 URL 修正列表；要让首批 HTML 本身就显示正确顺序，服务器也应按查询参数生成行和按钮状态。

`pushState()` 只记录 URL；点击处理器主动调用 `renderReports()`，本例也不把应用状态重复存进 `history.state`。其他应用若把额外恢复信息放在 `state` 参数里，可以在 `popstate` 的 `event.state` 读取；本例将 URL 当作排序状态的唯一来源。接着用户在这两条共享同一个 `Document` 的历史项之间后退或前进时，浏览器派发 `popstate`，同一个仍在的监听器从当前 `location` 读回排序并恢复按钮与列表。再后退离开这个文档时，当前监听器并不接管另一文档的恢复或重新加载；浏览器处理的是另一条历史项及其页面状态。

通过地址栏、链接或 `location` 改变片段会执行片段导航，可让浏览器滚到 `#summary` 并建立历史项；这是浏览器导航行为，不需要应用重画列表。脚本调用 History API 改成另一个片段则不会自动滚动，也不会因为调用本身派发 `hashchange`；遍历相应历史项时，`popstate` 可能与片段变化事件共同出现。客户端路由器可以复用这些历史项，但 URL 变化与视图绘制是两项不同工作。

浏览器首次收到 `.../reports?sort=recent#summary` 时，`#summary` 是浏览器用来定位的片段，服务器只处理路径与查询。筛选点击改成 `sort=oldest` 后，仍是同一个 `Document`：浏览器不重新解析 `/reports`，应用继续负责产生新列表节点。这个边界让地址可复制、可返回，同时不把 History API 误解成网络导航。

## 定时导航怎样用文本更新并允许取消？

倒计时示例把剩余秒数写进文本节点，避免将动态内容按 HTML 解析。`setInterval(..., 1000)` 中的 1000 毫秒是请求间隔，不承诺每秒准时执行；主线程繁忙或计时器节流都可能让更新变晚。时间到后清除 interval（间隔定时器）再导航；点击取消会清除同一个定时器，后续不会继续倒数。

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
  message.textContent = seconds + " 秒后打开 example.com。";
  if (seconds === 0) {
    clearInterval(timer);
    location.assign("https://example.com/");
  }
}, 1000);

cancel.addEventListener("click", () => {
  clearInterval(timer);
  message.textContent = "已取消跳转。";
  cancel.disabled = true;
});
~~~

**延伸：** [DOM 事件如何传播，何时适合事件委托？](../browser-apis/dom-manipulation-and-events.md)解释点击处理器如何收到按钮事件；React 中 URL 与客户端导航如何映射到视图，见[React 路由如何把 URL 映射到视图？](../frameworks/react-routing-and-navigation.md)，组件状态更新见[React 如何把用户操作变成更新后的界面？](../frameworks/react-basics.md)。

> [!info]- 来源
> - URL 分量的定义及序列化：[WHATWG URL Standard：URL representation](https://url.spec.whatwg.org/#url-representation)，持续更新规范，URL record 组成。核对日期：2026-11-07。
> - `Location` 的地址分量、assign/replace/reload 操作：[WHATWG HTML：Location interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-location-interface)，持续更新规范，Location API。核对日期：2026-11-07。
> - History API 的同源 URL 检查与 session history 遍历：[WHATWG HTML：History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，持续更新规范，pushState/replaceState 与遍历算法。核对日期：2026-11-07。
> - 倒计时更新文本与停止定时器：[WHATWG DOM：Node.textContent](https://dom.spec.whatwg.org/#dom-node-textcontent)；[WHATWG HTML：Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)，持续更新规范，文本节点与 timer 初始化/取消步骤。核对日期：2026-11-07。
> - URL 查询参数的解析与序列化： [WHATWG URL Standard：URLSearchParams](https://url.spec.whatwg.org/#urlsearchparams-class)，持续更新规范，URLSearchParams 接口章节。核对日期：2026-11-07。
> - 片段导航、同文档导航、会话历史遍历、`pushState()`、`popstate` 与 `hashchange`： [WHATWG HTML：导航与会话历史](https://html.spec.whatwg.org/multipage/nav-history-apis.html)，持续更新规范，navigation、History interface 与事件章节。核对日期：2026-11-07。
