# 用户离开报表页时，分析事件怎样尽力发送？

analytics event (分析事件)记录页面使用情况，例如打开报表或改变筛选。它们可以帮助产品理解使用情况，但通常不决定报表本身是否正确。本文跟踪一个合成案例：用户打开 `/reports/42`，改变一次筛选，再导航到另一个完整页面。页面只把 `report_opened`、`filter_applied` 和受控页面代号放入内存队列；它既不收集筛选原文，也不把离页发送当作服务器已记账。

## 先限制采集内容和积压量

允许列表先限定事件名和页面代号，再限定每条事件的字段。案例中的两条事件只有事件 ID（标识符）、名称、页面代号和时间戳；搜索框原文、完整 URL、用户令牌和身份字段不进入载荷。选择退出可选采集时，停止新入队并清空应用内存中的未发送事件。已经交给浏览器的请求无法由这个开关撤回。

| 时点 | 页面内存队列 | 接下来发生什么 |
| --- | --- | --- |
| 打开 `/reports/42` | `report_opened` | 事件尚未离开页面 |
| 改变筛选 | `report_opened`、`filter_applied` | 载荷不含筛选值；两条仍在内存 |
| 10 秒定时器前离开当前文档 | 同上 | `visibilitychange` 到 `hidden` 时取出一批并尝试发送 |

队列最多保留 200 条；满时丢弃最旧的一条。达到 50 条时安排一次分批发送；10 秒定时器也会尝试一批。发送时先试 Beacon API（信标接口）；若接口不可用或拒绝排队，就尝试 Fetch API（资源获取接口）的 `keepalive`（页面环境结束后仍允许请求继续）选项。单看条数不能约束请求体大小，所以例子再把序列化后的请求体限制为 8 KiB。字段值来自固定允许列表，事件 ID 使用安全上下文中的 `crypto.randomUUID()` 生成 UUID（通用唯一标识符）v4，时间戳是数字；这组有界字段让每条事件都能放进空批次。若以后加入自由文本或其他字段，必须重新检查字节上限和过大单条的处理。

下面的实现把事件在入队时生成的 ID 保留在载荷中。`takeBatchBody()` 只在同时满足条数和 UTF-8 编码字节上限时取出事件；它在调用发送 API 前就把所选事件从内存队列移除，API 拒绝或网络失败后也不会自动放回。下面的合成运行假设用户已允许可选采集；生产页面应从实际同意状态调用启用函数，不要固定开启。

> [!example]- 实现：同一事件 ID、大小限制与尽力发送
>
> 完整样例只发送两个允许的事件。离页时取出它们；正文载荷不含筛选值。
>
> ~~~javascript
> const MAX_PENDING = 200;
> const BATCH_SIZE = 50;
> const MAX_BATCH_BYTES = 8 * 1024;
> const allowedNames = new Set([
>   "report_opened",
>   "filter_applied",
> ]);
> const allowedScreens = new Set([
>   "report_list",
>   "report_detail",
> ]);
> const queue = [];
> const encoder = new TextEncoder();
> let collectionEnabled = false;
> let flushScheduled = false;
>
> function setCollectionEnabled(enabled) {
>   collectionEnabled = enabled;
>   if (!enabled) queue.length = 0;
> }
>
> function takeBatchBody() {
>   const batch = [];
>   let body = "[]";
>   while (queue.length && batch.length < BATCH_SIZE) {
>     const candidate = [...batch, queue[0]];
>     const candidateBody = JSON.stringify(candidate);
>     if (encoder.encode(candidateBody).byteLength > MAX_BATCH_BYTES) break;
>     batch.push(queue.shift());
>     body = candidateBody;
>   }
>   return batch.length ? body : null;
> }
>
> function flushOneBatch() {
>   const body = takeBatchBody();
>   if (body === null) return;
>   const payload = new Blob([body], { type: "application/json" });
>   // 同源端点。true 只表示浏览器接受了排队，不是服务器确认。
>   if (navigator.sendBeacon?.("/analytics", payload)) return;
>   // Beacon 不可用或拒绝时尝试 Fetch；两者共用 keepalive 在途字节额度。
>   void fetch("/analytics", {
>     method: "POST",
>     body: payload,
>     keepalive: true,
>     credentials: "same-origin",
>   }).catch(() => {});
> }
>
> function scheduleFlush() {
>   if (flushScheduled) return;
>   flushScheduled = true;
>   setTimeout(() => {
>     flushScheduled = false;
>     flushOneBatch();
>     if (queue.length >= BATCH_SIZE) scheduleFlush();
>   }, 0);
> }
>
> function trackEvent(name, screen) {
>   if (
>     !collectionEnabled ||
>     !allowedNames.has(name) ||
>     !allowedScreens.has(screen)
>   ) return;
>   if (queue.length === MAX_PENDING) queue.shift();
>   queue.push({
>     id: crypto.randomUUID(),
>     name,
>     screen,
>     ts: Date.now(),
>   });
>   if (queue.length >= BATCH_SIZE) scheduleFlush();
> }
>
> setInterval(flushOneBatch, 10_000);
> document.addEventListener("visibilitychange", () => {
>   if (document.visibilityState === "hidden") flushOneBatch();
> });
>
> setCollectionEnabled(true);
> trackEvent("report_opened", "report_detail");
> trackEvent("filter_applied", "report_detail");
> ~~~

运行条件：代码假设用户已允许采集、页面运行在 HTTPS 或本机 loopback 等安全上下文，且 `/analytics` 与页面同源。复现离页分支时，应在 10 秒定时器触发前点击会加载新文档的普通链接，例如 `<a href="/help">帮助</a>`；只在单页应用内改路由不会触发这里的 `hidden` 处理器。

`visibilitychange` 到 `hidden` 是页面变为不可见的信号；它也会在切换标签或应用进入后台时出现，所以不代表用户永久离开。对于**同一文档内的单页应用路由切换**，文档仍可见，通常不会触发这个信号；如果产品需要在路由边界提交队列，应由路由层显式调用队列模块提供的分批函数，不能假定页面生命周期事件会替它运行。hidden 处理器每次只尝试一批；页面离开前队列余量可能来不及发送。达到门槛后的定时任务可以继续排下一批，但页面离开不保证这些后续任务都能运行。

## “已排队”不等于“已记录”

离开页面时可监听 `visibilitychange`，并在状态变为 `hidden` 时调用 Beacon API。规范要求浏览器在这个状态变化时安排已提交给它的信标请求；但浏览器进程随后仍可能被系统终止。`hidden` 只是一次尽力发送的时机，不能证明页面一定要关闭，也不能证明服务器收到数据。

`pagehide` 表示一个会话历史条目不再是当前页面；其 `persisted` 为 `true` 时，页面可能进入往返缓存（back-forward cache，BFCache），之后还能恢复。它也不是所有后台或关闭场景都能观察到的信号。不要用 `unload` 作为最后发送钩子；移动端进程被系统结束时，脚本可能没有机会再运行。

| 观察到的阶段 | 这能证明什么 | 不能证明什么 |
| --- | --- | --- |
| 事件进入 JavaScript 内存队列 | 本页面暂存了事件 | 页面销毁后还能恢复 |
| `sendBeacon()` 返回 `true` | 浏览器接受了请求排队 | 网络请求完成或服务器已处理 |
| 服务端日志出现请求 | 请求到达了这个服务端入口 | 事件已写入耐久存储或业务事务已提交 |
| 服务端按事件 ID 完成去重并提交 | 服务端按自己的事务契约记录了该事件 | 浏览器知道提交结果；Beacon 没有响应回调 |

Beacon 是非阻塞的尽力传输。它自动使用 `keepalive`，不提供响应回调，也不允许调用者自定义请求头。普通 Fetch 请求默认不带 `keepalive`；文档销毁、Fetch 组结束时，尚未完成的普通请求可以被终止。样例只有在 Beacon 不存在或返回 `false` 时才改用 Fetch API 并设置 `keepalive: true`，使请求可以越过发起页面环境的销毁而继续处理。Fetch 的 Promise（异步结果对象）可能得到服务器响应，但页面离开后不能靠这个回调确认记录结果；`keepalive` 也不保证请求一定到达服务器。请求已被页面取消，也不代表服务端一定没读到正文：本地延迟响应测试中，普通 Fetch 的正文已到服务端，但导航后响应连接先关闭；keepalive Fetch 则等到了延迟的 `204` 响应。

Beacon 与 Fetch 的 `keepalive` 请求共享同一个 fetch group（Fetch 组）的在途请求体额度。Fetch 标准在 `contentLength + inflightKeepaliveBytes` 超过 64 KiB（65,536 字节）时拒绝请求；这计入尚未完成的其他 keepalive 请求，不只是当前这一批。因此样例的 8 KiB 是留有余量的应用上限，不是浏览器保证接受的大小；若其他请求占用了额度，8 KiB 请求仍可能被拒。此时回退到 Fetch 不能绕过限制。

同源 `/analytics` 端点让认证边界可见：Beacon 规范的凭证模式是 `include`，同源请求可带上适用的 Cookie；Fetch 样例明确选 `credentials: "same-origin"`。浏览器实测的同源测试请求携带了合成 Cookie `report_session=synthetic`。不要把身份令牌放进事件正文。若把端点改成跨源地址，JSON Blob 产生的 `Content-Type: application/json` 不符合 CORS 安全列表条件；预检缓存没有匹配项时，浏览器会先发不带凭证的 `OPTIONS`，成功后才发送实际 Beacon POST。实际 Beacon 的凭证模式固定为 `include`，服务端还需按规范回应允许的来源、凭证与请求头。Fetch 默认只发送同源凭证；跨源要显式设置 `include`，并满足 CORS 和 Cookie 的站点策略。

事件正文不放完整 URL，也不等于服务端看不到页面 URL：浏览器还可能在请求头中自动带 `Referer`。本地 Chromium `157.0.8103.51` 复现的同源请求，在页面没有设置 `Referrer-Policy` 时带上了来源页的路径与合成查询参数。若路径或查询串可能含敏感值，应通过文档响应头设置 `Referrer-Policy: strict-origin`（同源请求只发来源）或 `no-referrer`；`sendBeacon()` 不能单独改请求头，需在文档/站点策略处控制。Fetch 可设置单次 `referrerPolicy`，但两条发送路径都应遵守应用实际需要的策略。

样例在尝试发送前已把一批从内存队列取出。若 Beacon 返回 `false` 且 Fetch 因额度或网络失败而拒绝，这些事件不会自动回到队列；即使 Beacon 返回 `true`，异步请求也仍可能没有到达服务端。浏览器复现中，`sendBeacon()` 返回 `true` 后拦截并中止网络请求，服务端没有收到任何记录。

这属于可丢失的分析遥测。若数据丢失不可接受，需要另行实现持久化发件箱、重试与服务器确认。重试必须沿用入队时生成的同一个事件 ID；服务器为事件 ID 预先建立唯一约束，并在写入事务中按该键去重或执行幂等写入。浏览器不会按正文里的 ID 替应用去重：复现实验是应用代码**主动调用两次** Beacon，浏览器接受了两次，服务端看到了两个请求和两行原始事件；只有服务端按 ID 去重后，唯一事件数才是 1。这个实验说明重复提交需要服务端去重，不表示一次调用会被浏览器自行重发。当前样例不重试，因此可能丢失，但不会自行创建无限重试流。`setCollectionEnabled(false)` 只能清空尚在本地的队列，不能撤回已经交给浏览器的批次。

**延伸阅读：** [报表页面里的状态应该放在哪里？](../browser-apis/browser-storage-and-communication.md) 说明偏好与业务状态的归属；[流式报表断线重连后，界面怎样保留正确状态？](../browser-apis/streaming-ux.md) 说明不能和可丢弃分析数据混为一谈的业务消息；[WebView 怎样安全地开放原生能力并更新页面包？](../browser-apis/webview-javascript-bridge.md) 讨论混合应用中的宿主权限。

> [!info]- 来源
> - `sendBeacon()` 的返回值只表示浏览器成功排队；它没有响应回调，自动使用 `keepalive`，并在文档 `visibilityState` 变为 `hidden` 时安排传输：[W3C Beacon API](https://www.w3.org/TR/beacon/)，§3.1、§3.2，2026-11-12 核对。
> - Beacon 凭证模式、`Blob` 的 `Content-Type` 与 CORS 模式选择：[W3C Beacon API](https://www.w3.org/TR/beacon/)，§3.2，2026-11-12 核对。
> - keepalive 请求组的在途字节累计规则与 64 KiB 上限：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，“HTTP-network-or-cache fetch”中对 `inflightKeepaliveBytes` 的检查，2026-11-12 核对。
> - 文档 Fetch 组销毁时，未完成且未设 `keepalive` 的请求会被终止；keepalive 请求可在环境设置对象销毁后继续处理：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，§2.2.5、§2.4；HTML 文档销毁步骤：[WHATWG HTML Standard](https://html.spec.whatwg.org/multipage/document-lifecycle.html)，§7.5.10，2026-11-12 核对。
> - 跨源预检使用 `OPTIONS`，预检缓存决定是否要重新发起检查：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，§§3.3.2、4.8–4.10；Beacon 载荷类型与 CORS 选择：[W3C Beacon API](https://www.w3.org/TR/beacon/)，§3.2，2026-11-12 核对。
> - `visibilityState` 及页面可见性变化：[WHATWG HTML Standard](https://html.spec.whatwg.org/multipage/interaction.html#page-visibility)，Page visibility；`pagehide` 与文档生命周期顺序：[WHATWG HTML Standard](https://html.spec.whatwg.org/multipage/document-lifecycle.html)，Document lifecycle，2026-11-12 核对。
> - `hidden` 往往是移动端最后可靠观察到的生命周期状态；`pagehide` 可能伴随进入往返缓存，`unload` 不可靠：[Chrome for Developers, Page Lifecycle API](https://developer.chrome.com/docs/web-platform/page-lifecycle-api)，Developer recommendations for each state 和 Events，页面核对于 2026-11-12。
> - `crypto.randomUUID()` 生成 v4 UUID 且仅在安全上下文可用：[MDN Web Crypto API](https://developer.mozilla.org/en-US/docs/Web/API/Crypto/randomUUID)，2026-11-12 核对。
> - 同源 Cookie 与 Fetch credentials 行为、跨源凭证的 CORS 要求：[MDN, Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)，“Including credentials”，2026-11-12 核对。
> - 同源请求的 `Referer` 可含来源 URL 路径/查询串；`strict-origin` 仅发送 origin，`no-referrer` 不发送：[W3C Referrer Policy](https://www.w3.org/TR/referrer-policy/)，§§3.4–3.5、8.3，2026-11-12 核对；本页的同源合成请求核对了默认策略与 `strict-origin` 下的请求头。
> - 代码分支、导航期间的生命周期顺序、队列/额度/重复/凭证/Referer 实测：Chromium `157.0.8103.51`，本地 HTTP 页面与 Node 服务器；合成两事件在离页时成批 POST，回退、在途额度、主动重复提交、网络拦截以及 Referer 分支按正文所述逐项验证；这些观察仅限本地浏览器和合成环境，不代表跨浏览器送达保证。
