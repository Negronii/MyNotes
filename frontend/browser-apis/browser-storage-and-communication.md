# 报表页面里的状态应该放在哪里？

案例背景：用户打开 `/reports/42?sort=recent#summary`，希望刷新后继续查看同一报表、复制链接分享当前排序，并在另一标签页改变偏好后看到更新。重开时，页面从路径取报表 ID、从查询参数还原 `sort`，然后通过 HTTP 请求服务端报表；片段 `#summary` 定位页面中的摘要。若返回快照仍是 `running`，页面拿到与快照一致的 `event_cursor` 后再订阅更新，见[流式报表恢复案例](./streaming-ux.md)。报表内容由服务端维护，可分享的筛选条件进入 URL，Web Storage (网页存储) 只保存客户端偏好或草稿。

| 状态 | 合适的所有者 | 原因 |
|---|---|---|
| 报表 42 的进度、最终状态和权限 | 服务端 API | 多设备共享且需要可信的业务记录；缓存只能用于显示，不能取代权威状态 |
| `sort=recent`、定位到 `#summary` | URL 查询参数与片段 | 刷新、复制和浏览器历史都能恢复这份视图状态 |
| 列密度、隐藏提示等小型偏好 | `localStorage` | 同源页面可读写，并可跨标签页保留；浏览器策略仍可能限制或清除它 |
| 未提交的本标签页筛选草稿 | `sessionStorage` | 适合随当前顶层浏览上下文存活，重载后还可恢复 |
| 登录会话标识 | 服务器管理的 Cookie | 符合域、路径、传输安全和请求凭证规则时会随请求发送 |

`localStorage` 和 `sessionStorage` 是同步的字符串键值 API；调用会占用当前 JavaScript 执行时间。它们不提供多键事务或条目级过期时间，也不适合作为大型结构化数据的数据库。Storage Standard 为这两个存储端点各建议 5 MiB 配额；这是规范建议，不保证用户代理一定能提供，写入也可能因配额或策略限制失败。较大的本地记录和需要原子提交的更新可用 IndexedDB 事务；`navigator.storage.estimate()` 只能给出近似使用量和配额，不能保证数据不会被策略拒绝或清除。

同源并不总表示顶层页面和嵌入式第三方页面共享同一个存储区：浏览器可限制第三方存储，存储分区也可能把嵌入上下文隔离。不要假设同一页面在顶层打开和放入 iframe 后能读到相同数据。

`sessionStorage` 通常按来源和顶层浏览上下文隔离，因而不同标签页各有一份，并能在同一标签页重载时保留。由带 opener 的页面新开的辅助浏览上下文，初始时可能收到 opener 的 sessionStorage 副本，之后两边各自变化；不要把这种初始复制当作共享存储。浏览器会话恢复等生命周期行为也由用户代理决定。

本地存储写入不是跨标签页锁。标签页 A 和 B 同时读取计数 4、各自加一并写回时，最终值可能仍为 5。值实际发生变化时，其他共享该存储区的文档会收到 storage event (存储事件)，写入者本身不会收到；若 `setItem()` 写入的字符串与原值相同，规范会提前返回，不派发事件。事件只是通知，不会把多步读改写变成事务。需要协作时，使用 IndexedDB 事务或明确的跨上下文协调协议。

> [!example] 用存储通知偏好变化
> 排序是 URL 状态，以下键只保存列密度。两个标签页分别运行这两段代码。示例假定 B 中该键尚未设置或原值为 `"false"`；A 监听其他文档的有效变化，B 调整偏好后写入。即使通知到达，A 也应把它当作“偏好有变化”的信号，再从存储读取值。
>
> 标签页 A：
>
> ~~~javascript
> const key = "reports:compact-columns";
> window.addEventListener("storage", event => {
>   if (event.storageArea === localStorage && event.key === key) {
>     applyCompactColumns(localStorage.getItem(key) === "true");
>   }
> });
> ~~~
>
> 标签页 B：
>
> ~~~javascript
> localStorage.setItem("reports:compact-columns", "true");
> ~~~

Web Storage 可被当前页面上的脚本读取；若 cross-site scripting (跨站脚本攻击，XSS) 进入页面，存储在其中的 bearer token (持有者令牌) 也可能被窃取。`HttpOnly` Cookie 不向普通页面脚本暴露，但浏览器会按 Cookie 规则自动附带它，服务端仍需设计 Cross-Site Request Forgery (跨站请求伪造，CSRF) 防护。`SameSite=None` Cookie 必须同时带 `Secure`。选用一种存储形式并不会自动解决认证与授权问题。

**延伸阅读：** [同一报表在多个标签页中怎样交换变化？](./browser-context-communication.md) 解释怎样通知其他标签页；[Web 安全与认证](../../engineering-foundations/security/web-security-and-authentication.md) 讨论 Cookie、XSS 与 CSRF。

> [!info]- 来源
> - `localStorage`、`sessionStorage` 的作用域、storage event (存储事件) 与访问策略：[WHATWG HTML Standard，Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html)，§12.2，2026-11-06 核对。
> - 浏览器配额、存储持久性和驱逐由实现与用户代理策略影响；`navigator.storage.estimate()` 返回近似值：[WHATWG Storage Standard](https://storage.spec.whatwg.org/)，2026-11-06 核对。
> - Web Storage 的 5 MiB 是每个存储端点的规范配额建议；Storage Standard 说明 storage key 的分区模型预期会演进：[WHATWG Storage Standard，§4.1–4.2](https://storage.spec.whatwg.org/#storage-endpoints)，2026-11-06 核对。
> - 用户代理可限制第三方文档对 `localStorage` 的访问：[WHATWG HTML Standard，Web Storage privacy](https://html.spec.whatwg.org/multipage/webstorage.html#user-tracking)，2026-11-06 核对。
> - 结构化本地记录与事务：[Indexed Database API 3.0](https://w3c.github.io/IndexedDB/)，2026-11-06 核对。
> - 已发布的 Cookie 存储与请求发送规则、`Secure`、`HttpOnly` 属性：[RFC 6265](https://www.rfc-editor.org/rfc/rfc6265.html)。
> - `SameSite` 属性及 `SameSite=None` 要求 `Secure`：当前 IETF 文稿 `draft-ietf-httpbis-rfc6265bis-22` 的 §4.1.2.7、§5.7；截至 2026-11-06，Datatracker 仍标记 RFC Editor「Final Approval Pending」，普通 RFC 发布页尚未提供：[IETF 文稿](https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-rfc6265bis/)，[官方流程状态](https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/)。
