# 地址变了，浏览器什么时候加载新文档，界面状态何时该写进 URL？

本章沿用主线一的报表页（见[打开一个 URL 后，页面怎样变得可见又可交互？](from-url-to-interactive-page.md)），跟踪三个时刻：用户打开 `https://reports.example/reports/42?sort=recent#summary`；点“最早优先”；再按浏览器的后退键。三个时刻都要显示正确的行序，复制出去的链接也要让同事看到同样的排序。

要做到这一点，先要分清每次地址变化时浏览器做的是哪件事：加载一个新文档，跳到当前文档里的某个片段，还是只改写当前文档的历史地址。然后才能决定哪些界面状态该写进 URL、用哪种方式写。

## URL 由哪些分量组成，各交给谁

本节是全领域关于 URL 分量与分工的权威说明。

```text
https://reports.example/reports/42?sort=recent#summary
└─┬─┘   └──────┬──────┘└────┬────┘└─────┬────┘└───┬──┘
scheme       host         path        query   fragment
```

| 分量 | 本例 | 作用 |
|---|---|---|
| scheme (方案) | `https:` | 用什么协议取资源 |
| host (主机) | `reports.example` | 向哪台服务器要 |
| port (端口) | 省略，HTTPS 默认 443 | 服务器上的哪个端口 |
| path (路径) | `/reports/42` | 要哪份资源 |
| query (查询) | `?sort=recent` | 以什么参数看这份资源 |
| fragment (片段) | `#summary` | 文档里的哪个位置 |

origin (源)由 scheme、host、port 三者确定，本例是 `https://reports.example`。同源策略、存储分区、History API 能改写哪些 URL，都以 origin 为界。URL 里还可以有 username 和 password 分量，但不应使用。并非所有 URL 都有 `//主机/路径` 这种结构，例如 `mailto:reports@example.test` 就没有。

三个分量的分工决定了状态该放哪里：

- **path 标识资源。** `/reports/42` 和 `/reports/43` 是两份不同的报表。换 path 就是换资源，服务器按 path 路由。
- **query 是看这份资源的参数。** 排序、筛选、页码这类“同一份报表的不同视图”放在这里。query 随请求发给服务器，服务器可以据此输出已经排好序的 HTML；它也是 HTTP 缓存键的一部分，`?sort=recent` 和 `?sort=oldest` 是两条缓存记录。
- **fragment 只在浏览器里用。** 它不随请求发送，服务器看不到。浏览器用它定位文档里 `id` 匹配的元素；只改 fragment 不会加载新文档。

所以本例把排序放进 query：它是同一份报表的视图参数，分享链接时要带上，服务器也可以据此输出首屏。“定位到摘要”放进 fragment：它只关系到浏览器滚到哪里。全部界面状态（URL、查询缓存、全局 store、组件、服务端）怎样分配所有者，见[一份界面状态该由谁持有？](../ui-state/state-ownership-and-composition.md)。

## 在脚本里读写 URL：location、URL 与 URLSearchParams

`location` 对象按分量暴露当前地址：

| 属性 | 本例的值 | 说明 |
|---|---|---|
| `href` | 完整 URL | 赋值会触发导航 |
| `protocol` | `"https:"` | 带结尾冒号 |
| `host` / `hostname` | `"reports.example"` | `host` 含非默认端口，`hostname` 不含 |
| `port` | `""` | 非默认端口才有值 |
| `pathname` | `"/reports/42"` | |
| `search` | `"?sort=recent"` | 保留开头的 `?` |
| `hash` | `"#summary"` | 保留开头的 `#` |
| `origin` | `"https://reports.example"` | 只读 |

解析和修改 URL 用 `URL` 和 `URLSearchParams`，不要手动切字符串：

- `searchParams.get("sort")` 在参数缺失时返回 `null`；存在时返回的总是字符串，`?year=2026` 读出来是 `"2026"`，不是数字。
- `getAll()` 读同名的多个值；`set()` 替换所有同名值；`append()` 追加一项。
- 修改后，`URLSearchParams` 按 `application/x-www-form-urlencoded` 规则重新序列化**整个**查询串。例如 `?q=a%20b&sort=recent` 改了 `sort` 之后变成 `?q=a+b&sort=oldest`，没动过的 `q` 也从 `%20` 变成了 `+`。两种写法对它自己的解析器等价，但服务器若按别的规则解析，可能看到不同的值。
- 相对地址按当前 URL 解析：`new URL("?sort=oldest#summary", location.href)` 得到 `https://reports.example/reports/42?sort=oldest#summary`。

## 五种写地址的方式

| 操作 | 文档 | 历史 |
|---|---|---|
| 打开另一个地址：点击 `<a>`、给 `location.href` 赋值、调用 `location.assign()` | 通常加载新的 `Document`；若目标与当前 URL 只差 fragment，沿用当前文档，按片段导航处理 | 新增一项 |
| `location.replace(url)` | 同上 | 替换当前项 |
| `location.reload()` | 重新加载当前文档，即使地址没变；资源仍可能来自缓存 | 不增加 |
| `history.pushState(state, "", url)` | 保留当前文档，不发请求 | 新增一项 |
| `history.replaceState(state, "", url)` | 保留当前文档，不发请求 | 修改当前项 |

History API 只能把地址改成当前文档“可改写”的 URL：对本例的 HTTPS 页面，path、query、fragment 可以改，scheme、username、password、host、port 必须不变。`pushState()` 和 `replaceState()` 本身不派发 `popstate` 或 `hashchange`，也不加载或渲染任何东西。应用要显示与新地址对应的内容，必须自己更新界面；需要服务器上的其他资源时，应正常导航或显式发请求。

在历史中移动用 `history.back()`、`forward()` 和 `go(n)`：正数向前，负数向后，`go(0)` 重新加载当前页，超出范围什么也不做。同一标签页的会话历史可以包含不同 origin 的文档，所以这些方法可能移到跨源页面。“只能改写同源 URL”只限制 `pushState()`/`replaceState()` 写入的地址，不限制后退能到哪里。

`pushState` 还是 `replaceState`，看用户是否期望后退能撤销这次变化。排序是用户主动选择的视图，本例用 `pushState()`，后退回到上一种排序；输入框里每敲一个字都写一次地址时，用 `replaceState()` 更合适，否则历史里会堆满中间状态。

## 让排序跟随地址栏与前进后退

本例的行数据已在客户端的 `records` 数组里，排序只需重排已有数据，所以用 `pushState()` 记录地址，再由处理器主动重建列表。下面在主线一第一章的 `/reports.js` 上补三处：从 URL 读排序、点击时写地址、后退时按地址恢复。`records` 和 `renderReports(list, controls, sort)` 沿用上一版不变。

```javascript
function sortFromUrl() {
  return new URL(location.href).searchParams.get("sort") === "oldest"
    ? "oldest"
    : "recent";
}

function initializeReportControls() {
  const controls = document.querySelector("#sort-controls");
  const list = document.querySelector("#reports");
  if (!controls || !list) return;

  function chooseSort(sort) {
    if (sort !== "recent" && sort !== "oldest") return;
    if (sort === sortFromUrl()) return;
    const url = new URL(location.href);
    url.searchParams.set("sort", sort);
    history.pushState(null, "", url.href);
    renderReports(list, controls, sort);
  }

  controls.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const button = target?.closest("button[data-sort]");
    if (!button || !controls.contains(button)) return;
    chooseSort(button.dataset.sort);
  });
  window.addEventListener("popstate", () => {
    renderReports(list, controls, sortFromUrl());
  });

  renderReports(list, controls, sortFromUrl());
  for (const button of controls.querySelectorAll("button[data-sort]")) {
    button.disabled = false;
  }
}
// 末尾的 readyState 就绪检查与上一版相同
```

写地址时先从 `location.href` 解析现有地址，只改 `sort`，所以 path、其他查询参数和 `#summary` 都保留。初始化时按 URL 渲染一次：若用户打开的是同事分享的 `sort=oldest` 链接，而服务器只会按 `recent` 输出，这一步会把列表改对。更好的做法是让服务器也按查询参数输出行和按钮状态，首屏就不会先显示错的顺序再跳变。

三个时刻加上前进：

| 时点 | 文档、历史与事件 | 地址与界面 |
|---|---|---|
| 初次打开 | 浏览器用收到的 HTML 创建 `Document`；模块初始化时读 URL | `sort=recent`；`aria-pressed` 为 `true`/`false`；May → April |
| 点“最早优先” | `pushState()` 在同一文档上新增历史项；不请求新 HTML，不派发 `popstate`/`hashchange`；处理器自己调用 `renderReports()` | `sort=oldest`；`false`/`true`；April → May |
| 后退 | 激活上一个同文档历史项，派发 `popstate`；`#summary` 没变，不派发 `hashchange` | 监听器读当前 URL，恢复 `sort=recent`、`true`/`false`、May → April |
| 前进 | 再激活 `sort=oldest` 那一项，派发 `popstate` | 恢复 `false`/`true`、April → May |

`pushState()` 的第一个参数可以保存一份可结构化克隆的状态，之后从 `popstate` 事件的 `event.state` 或随时从 `history.state` 读回。本例传 `null`，排序只从 URL 读，所以 `event.state` 是 `null`，也就不会出现 URL 和 state 说法不一的情况。

若用户继续后退、离开了这个文档，当前页面的 `popstate` 监听器就不再参与。浏览器可能从 back/forward cache 恢复整个旧页面，也可能重新加载它；页面怎样感知这两种情况，见[浏览器能把状态存在哪里，标签页和窗口之间怎样互相通知？](../ui-state/browser-storage-and-cross-context-messaging.md)。

## 只改片段时发生什么

普通导航只有在目标与当前 URL 除 fragment 外完全相同时，才走同文档的片段导航。在 `/reports/42?sort=oldest#summary` 上执行 `location.hash = "#reports"`：

1. 浏览器沿用当前 `Document`，新增一项历史记录，滚动到 `ol#reports`。
2. 同步派发 `popstate`（`event.state` 为 `null`）。本例的监听器会从 URL 重读排序并重建列表，顺序不变。
3. 再以一个排队的任务派发 `hashchange`。

本机 Chrome 157 在这条路径上观察到的顺序也是先 `popstate`、后 `hashchange`，与规范一致。

两个容易混淆的对照：

- 在 `/reports/42?sort=recent#summary` 上 `location.assign("?sort=oldest#summary")`：query 变了，即使保留了 `#summary`，也会导航到一个新的 `Document`。
- 用 `pushState()` 改成另一个片段：浏览器不滚动，调用本身也不派发 `popstate` 或 `hashchange`；只有之后通过前进后退回到这一项时，才按历史遍历的步骤处理。本例的排序历史项只改 query、保留 `#summary`，所以前进后退只触发 `popstate`。

客户端路由器也建立在这些历史项之上，但改地址和更新视图始终是两件事。路由器怎样在地址变化后加载数据、区分已提交和待定的导航，见[路由怎样把 URL 变成已提交的数据和界面？](../ui-state/routing-and-loaders.md)。

## 什么样的界面状态该写进 URL

写进 URL 的状态能被复制、分享、收藏和后退恢复，代价是它变成了公开的、来自外部的输入。设计时按四条处理：

1. **读出来的值必须校验。** 查询参数来自地址栏或外部链接，可以是任何字符串。本例只接受 `recent` 和 `oldest`；服务器同样要校验，不能因为前端只会写这两个值就信任它。
2. **缺失和未知值要有默认解释。** `sortFromUrl()` 把缺失、未知的值（例如 `sort=other`）都当作 `recent` 显示，但不立即改写地址；点已选中的“最近优先”会提前返回，只有选另一种排序才写回。另一种做法是加载后用 `replaceState()` 把地址规范化成合法值，代价是用户看到的地址和他打开的不同。
3. **写回会重新序列化。** 用 `URLSearchParams` 改一个参数，会按它的规则重写整个查询串（见上文 `%20` 变 `+` 的例子）。依赖查询串原样不变的代码（例如拿完整查询串做签名）要单独处理。
4. **敏感值不进 URL。** 口令、访问令牌、会话标识不要放进 path 或 query：URL 会留在浏览器历史里，会写进服务器和代理日志；默认的 Referrer Policy（`strict-origin-when-cross-origin`）在跨源请求中只发送 origin，但页面若放宽策略，完整 URL 会经 `Referer` 头发给其他站点。会话标识该放在哪里，见[浏览器能把状态存在哪里？](../ui-state/browser-storage-and-cross-context-messaging.md)。

适合写进 URL 的，是“别人打开这个链接时也应该看到”的状态：资源标识、排序、筛选、页码、选中的标签页。只属于这次操作过程的状态（输入框里尚未提交的草稿、弹窗开合、悬停）不写进 URL。

## 可取消的倒计时跳转

前面的排序始终留在同一文档内。有时页面确实要离开当前文档，但想先给用户一个等待和取消的机会，例如显示“5 秒后打开 example.com”：

```html
<p id="countdown" role="status">5 秒后打开 example.com。</p>
<button id="cancel-navigation" type="button">取消</button>
```

```javascript
const message = document.querySelector("#countdown");
const cancel = document.querySelector("#cancel-navigation");
const deadline = performance.now() + 5000;
let shown = 5;

const timer = setInterval(() => {
  const remaining = Math.ceil((deadline - performance.now()) / 1000);
  if (remaining <= 0) {
    clearInterval(timer);
    cancel.disabled = true;
    message.textContent = "正在跳转…";
    location.assign("https://example.com/");
    return;
  }
  if (remaining !== shown) {
    shown = remaining;
    message.textContent = `${remaining} 秒后打开 example.com。`;
  }
}, 250);

cancel.addEventListener("click", () => {
  clearInterval(timer);
  message.textContent = "已取消跳转。";
  cancel.disabled = true;
});
```

计时器的间隔只是下限，回调可能因主线程繁忙或后台节流而晚到（规则见[事件循环怎样安排任务、微任务和渲染？](event-loop-tasks-and-rendering.md)）。所以代码不按回调次数减秒，而是每次用当前时间对照截止时刻重算剩余秒数，回调晚到也不会让跳转越推越迟；文字只在秒数变化时更新，`role="status"` 的读屏播报也不会每 250 ms 重复一次。

取消只在归零回调执行之前有效。归零回调一旦开始，它先禁用取消按钮、显示“正在跳转…”，再调用 `location.assign()`；此时 `clearInterval()` 撤销不了已经开始的导航。

## 地址与界面的交接

回到开头的三个时刻：首次打开时，服务器按 path 和 query 返回报表 42 的最近优先视图，浏览器用 `#summary` 定位；点排序时，`pushState()` 只改写同一文档的地址，新列表由应用自己生成；后退时，`popstate` 监听器按地址恢复顺序。地址能复制、能返回，又不会被误当成一次网络导航。

本章的方案靠手写的 `popstate` 监听器把 URL 映射回界面。数据要从服务器取、导航还要显示加载中和错误状态时，这套映射就交给路由器负责，见[路由怎样把 URL 变成已提交的数据和界面？](../ui-state/routing-and-loaders.md)。

到这里，主线一讲完了报表页怎样在浏览器里运行：首帧何时出现、点击何时生效、DOM 改动怎样变成像素、地址怎样跟上界面。同一份 HTML 表达了什么结构、键盘和读屏用户能否同样找到并操作这些按钮，由主线二的[页面结构怎样让所有人都能读懂和操作？](../html-css/semantic-structure-and-accessibility.md)接手。

> [!info]- 来源
> - **URL 分量、origin 与序列化（“URL 由哪些分量组成”）。** [WHATWG URL Standard，URL representation](https://url.spec.whatwg.org/#url-representation) 与 [origin](https://url.spec.whatwg.org/#origin)，Living Standard（2026-10-19 更新）；片段标识次级内容：[RFC 3986 §3.5](https://www.rfc-editor.org/rfc/rfc3986.html#section-3.5)。核对日期：2026-11-12。
> - **查询参数的读取、多值与重新序列化（“在脚本里读写 URL”）。** [WHATWG URL Standard，URLSearchParams](https://url.spec.whatwg.org/#urlsearchparams-class)，Living Standard（2026-10-19 更新）：`get()`、`getAll()`、`set()`、`append()` 与 form-urlencoded 序列化。`%20` → `+` 与相对地址解析的结果在 Node.js v26.13.1 的 WHATWG `URL` 实现中复核。核对日期：2026-11-12。
> - **`location` 分量与 `assign()`/`replace()`/`reload()`（“在脚本里读写 URL”“五种写地址的方式”）。** [WHATWG HTML，Location interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-location-interface)，Living Standard（2026-11-11 更新）。核对日期：2026-11-12。
> - **History API 可改写 URL 的条件、state 与历史遍历（“五种写地址的方式”“让排序跟随地址栏”）。** [WHATWG HTML，History interface](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface)，Living Standard（2026-11-11 更新）：同文档 URL 改写规则、`pushState()`/`replaceState()`、`go(delta)`。核对日期：2026-11-12。
> - **普通导航、片段导航与历史步骤（“五种写地址的方式”“只改片段时发生什么”）。** [WHATWG HTML，Navigation and session history](https://html.spec.whatwg.org/multipage/browsing-the-web.html#navigate)：[fragment navigations](https://html.spec.whatwg.org/multipage/browsing-the-web.html#navigate-fragid)、[URL and history update steps](https://html.spec.whatwg.org/multipage/browsing-the-web.html#url-and-history-update-steps)、[updating the document for a history step](https://html.spec.whatwg.org/multipage/browsing-the-web.html#update-document-for-history-step-application)（同文档时先派发 popstate，fragment 变化再排队派发 hashchange）、[reloading](https://html.spec.whatwg.org/multipage/browsing-the-web.html#apply-the-reload-history-step)。Living Standard（2026-11-11 更新），核对日期：2026-11-12。
> - **`popstate`/`hashchange` 事件（“只改片段时发生什么”）。** [WHATWG HTML，Event interfaces](https://html.spec.whatwg.org/multipage/nav-history-apis.html#event-interfaces)，Living Standard（2026-11-11 更新）；事件先后另以本机 Chrome 157 回放核对。核对日期：2026-11-12。
> - **query 是缓存键的一部分、敏感值不进 URL（“URL 由哪些分量组成”“什么样的界面状态该写进 URL”）。** 缓存键至少由请求方法和目标 URI 组成：[RFC 9111 §2](https://www.rfc-editor.org/rfc/rfc9111.html#section-2)；默认 Referrer Policy 为 `strict-origin-when-cross-origin`：[W3C Referrer Policy §3](https://w3c.github.io/webappsec-referrer-policy/#referrer-policies) 与 [WHATWG Fetch，default referrer policy](https://fetch.spec.whatwg.org/#concept-request-referrer-policy)，Editor’s Draft。本轮改写时对照原文核对。
> - **倒计时的文本更新与计时器（“可取消的倒计时跳转”）。** [WHATWG DOM，Node.textContent](https://dom.spec.whatwg.org/#dom-node-textcontent)；[WHATWG HTML，Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)，Living Standard（2026-11-11 更新）：超时是最早可运行时间。核对日期：2026-11-12。
