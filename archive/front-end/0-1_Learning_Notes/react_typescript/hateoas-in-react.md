# React 客户端怎样使用 API 表示中的超媒体链接？

HATEOAS（Hypermedia as the Engine of Application State，超媒体作为应用状态引擎）是 REST 统一接口约束之一：客户端按媒体类型和关系名理解服务端表示，从中发现可用状态转移，而不是只靠资源 ID 拼出目标地址。本章沿着一个合成订单“ord-203”的交互，跟踪表示中的 self 与 cancel 如何引导下一步。GET 得到 awaiting-payment 的订单及其取消操作；用户点击后，客户端只按 API 声明的 POST 提交。服务端重新检查权限和订单状态，再用成功的新表示或冲突后的现状更新页面。链接描述的是可选关系，客户端仍须验证地址、方法与运行时数据。

~~~json
{
  "id": "ord-203",
  "status": "awaiting-payment",
  "links": [
    { "rel": "self", "href": "/api/orders/ord-203", "method": "GET" }
  ],
  "actions": [
    {
      "rel": "cancel",
      "href": "/api/orders/ord-203/cancel",
      "method": "POST"
    }
  ]
}
~~~

本例的 links 与 actions 是合成 API 自己定义的 JSON 合同，不是所有 JSON API 都自动遵守的通用 schema。这里 self 必须是 GET，cancel 必须是 POST；不能从关系名、URL 长相或按钮状态猜写入方法。解析器把网络数据保持为 unknown，只提取当前代码理解并验证过的关系。

如果媒体类型/API 合同把某个安全 GET 关系定义为普通导航，客户端可以把它渲染成 `<a>`；本例的 self 用于读取表示，cancel 会改变资源状态，所以显示为按钮。写操作若还需要请求体、媒体类型或幂等键，也必须由对应 API 合同说明，不能从关系名或地址形状推测。

JSON 是 API 响应输入；后面三个 TS/TSX 代码块按顺序组成同一份 TSX 模块。页面路由先用 readOrder("/api/orders/ord-203", window.location.origin) 取得 Order，再把它交给 OrderActions。

~~~tsx
import { useState } from "react";

type OrderAction = { href: string; method: "POST" };
type Order = {
  id: string;
  status: string;
  representationUri: string;
  selfHref: string;
  cancel?: OrderAction;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseOrder(value: unknown, representationUri: string): Order {
  if (
    !isRecord(value) ||
    typeof value.id !== "string" ||
    typeof value.status !== "string" ||
    !Array.isArray(value.links) ||
    !Array.isArray(value.actions)
  ) {
    throw new TypeError("订单表示不符合 API 合同");
  }

  const self = value.links.find(
    item => isRecord(item) && item.rel === "self",
  );
  if (
    !isRecord(self) ||
    typeof self.href !== "string" ||
    self.method !== "GET"
  ) {
    throw new TypeError("订单缺少安全 GET self 链接");
  }

  const cancel = value.actions.find(
    item => isRecord(item) && item.rel === "cancel",
  );
  if (cancel === undefined) {
    return {
      id: value.id,
      status: value.status,
      representationUri,
      selfHref: self.href,
    };
  }
  if (
    !isRecord(cancel) ||
    typeof cancel.href !== "string" ||
    cancel.method !== "POST"
  ) {
    throw new TypeError("取消操作不符合 API 合同");
  }

  return {
    id: value.id,
    status: value.status,
    representationUri,
    selfHref: self.href,
    cancel: { href: cancel.href, method: "POST" },
  };
}
~~~

路由已知初始订单 URI /api/orders/ord-203，所以首次读取以当前 origin 作为显式基址来解析本例的站点根相对 href。以后每份表示都保存实际响应 URI；其中的相对链接以这个响应 URI 为基址解析。例如响应 URI 为 https://shop.example/api/orders/ord-203 时，href 为 ord-203/cancel 会解析成 https://shop.example/api/orders/ord-203/cancel。最终得到的目标须与页面同源、路径位于 /api/ 下且没有 URL 用户名或密码。new URL() 会先按 URL 规则解析 ../ 等相对段，再供这些约束检查。

检查只覆盖准备发出的这个目标 URL。浏览器 Fetch 默认会跟随 HTTP 重定向，因此只检查第一跳不足以限制最终请求；本例的 GET、POST 和恢复 GET 都设 redirect: "error"，任何重定向都让 Fetch 失败，不会继续访问第二个目标。若某 API 合同确实需要重定向，必须另行定义受控的跳转校验策略，不能把下面的首跳检查说成最终 URL 检查。

~~~typescript
function checkedApiUrl(href: string, baseUri: string): string {
  const origin = window.location.origin;
  const target = new URL(href, baseUri);

  if (
    target.origin !== origin ||
    !target.pathname.startsWith("/api/") ||
    target.username !== "" ||
    target.password !== ""
  ) {
    throw new Error("API 链接超出当前站点的允许范围");
  }
  return target.href;
}

async function readOrder(
  href: string,
  baseUri: string,
  cacheMode: RequestCache = "default",
): Promise<Order> {
  const target = checkedApiUrl(href, baseUri);
  const response = await fetch(target, {
    method: "GET",
    credentials: "same-origin",
    cache: cacheMode,
    redirect: "error",
  });
  if (!response.ok) {
    throw new Error("读取订单失败：HTTP " + response.status);
  }

  const body: unknown = await response.json();
  return parseOrder(body, response.url || target);
}

type CancelResult =
  | { kind: "confirmed"; order: Order }
  | { kind: "conflict"; current: Order };

async function submitCancel(order: Order): Promise<CancelResult> {
  const action = order.cancel;
  if (!action) throw new Error("当前订单没有取消操作");

  const target = checkedApiUrl(action.href, order.representationUri);
  const response = await fetch(target, {
    method: action.method,
    credentials: "same-origin",
    redirect: "error",
  });

  if (response.status === 409) {
    const current = await readOrder(
      order.selfHref,
      order.representationUri,
      "no-store",
    );
    return { kind: "conflict", current };
  }
  if (response.status !== 200) {
    throw new Error("取消订单失败：HTTP " + response.status);
  }

  let updated: Order;
  try {
    const body: unknown = await response.json();
    updated = parseOrder(body, response.url || target);
  } catch {
    throw new Error("取消响应无法验证；操作结果需要重新读取确认");
  }
  if (
    updated.id !== order.id ||
    updated.status !== "cancelled" ||
    updated.cancel !== undefined
  ) {
    throw new Error("取消响应未满足 API 合同；操作结果需要重新读取确认");
  }

  return { kind: "confirmed", order: updated };
}
~~~

~~~tsx
function OrderActions({
  order,
  onOrderUpdated,
  onError,
}: {
  order: Order;
  onOrderUpdated(order: Order): void;
  onError(error: unknown): void;
}) {
  const [busy, setBusy] = useState(false);
  const [recoveryNeeded, setRecoveryNeeded] = useState(false);
  const [notice, setNotice] = useState("");

  async function cancel() {
    setBusy(true);
    setRecoveryNeeded(false);
    setNotice("");
    try {
      const result = await submitCancel(order);
      if (result.kind === "confirmed") {
        onOrderUpdated(result.order);
        setNotice("HTTP 200 与新订单表示确认取消已完成。");
      } else {
        onOrderUpdated(result.current);
        setNotice(
          "HTTP 409 表示取消未完成；页面已显示重新读取的当前状态 " +
            result.current.status + "。",
        );
      }
    } catch (cause) {
      setRecoveryNeeded(true);
      onError(cause);
    } finally {
      setBusy(false);
    }
  }

  async function refreshCurrent() {
    setBusy(true);
    setNotice("");
    try {
      const current = await readOrder(
        order.selfHref,
        order.representationUri,
        "no-store",
      );
      onOrderUpdated(current);
      setRecoveryNeeded(false);
      setNotice("当前订单表示已刷新；它不单独证明上次取消成功。");
    } catch (cause) {
      onError(cause);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      {order.cancel && (
        <button
          type="button"
          disabled={busy || recoveryNeeded}
          onClick={() => void cancel()}
        >
          取消订单
        </button>
      )}
      {recoveryNeeded && (
        <button
          type="button"
          disabled={busy}
          onClick={() => void refreshCurrent()}
        >
          重新读取订单状态
        </button>
      )}
      {notice && <p role="status">{notice}</p>}
    </section>
  );
}
~~~

这个例子的初始 GET 是 GET /api/orders/ord-203。解析后的 Order 保存表示响应 URI；后续 selfHref 与 cancel.href 都相对它解析，检查后才交给 fetch。credentials: "same-origin" 让 Fetch 按同源规则处理凭证；真正的身份、资源授权和当前状态仍由服务端对每次请求判断，按钮可见不是授权措施。

合成 API 约定取消成功只用 HTTP 200 加同一订单的新 JSON 表示确认；示例要求 id 仍是 ord-203、状态是 cancelled、并且不再有 cancel 操作。代码返回 kind: "confirmed" 才显示成功。onOrderUpdated 只负责把服务端表示放入界面，不能单独当作写入成功信号。

若 POST 收到 409，API 合同表示这次取消未完成；客户端以 cache: "no-store" 对 self 发安全 GET，并返回 kind: "conflict"。例如夹具中的服务端状态已变成 shipped，页面显示 shipped 且取消按钮消失，但这只是当前状态的观察，不是取消成功。冲突读取若失败，页面保持原表示并提供“重新读取订单状态”；这个恢复 GET 仍禁止重定向并绕过普通浏览器 HTTP 缓存。

这条缓存选择是必要的：本地缓存可能有初始 awaiting-payment 表示，响应却标为 private, max-age=600。POST 发往 /api/orders/ord-203/cancel，重读发往不同的 /api/orders/ord-203；RFC 9111 对成功的 unsafe 请求要求失效其目标 URI，但不会因此保证另一个 self URI 被失效。409 又是错误响应，不会触发那项成功响应失效规则。no-store 让 Fetch 不用浏览器 HTTP 缓存中的旧表示；本例假定这些请求没有被 Service Worker 合成或改写，Service Worker 是另一层缓存/拦截逻辑，需有自己的新鲜度合同。

网络失败、重定向被拒绝或 200 正文损坏时，客户端可能不知道服务器是否已经处理取消。组件不在失败后再次调用 POST，而是禁用旧取消按钮并提供只读 self 刷新；刷新后显示最新状态，但不能仅凭 cancelled 归因于刚才的请求。单次应用层 fetch 调用也不保证服务端只收到一次：在本文 Chrome 157 本地连接断开夹具中，服务端在处理一次逻辑 POST 后关闭连接，记录到两条 POST。若同一业务写入必须至多生效一次，服务端需要幂等键去重或原子状态转换等写入一致性规则；状态查询只能帮助客户端重新观察结果，不能单独防止重复副作用。不能把按钮回调或浏览器一次 Promise 当作传输层至多一次保证。

超媒体把当前可选状态转移放进表示，让客户端通过关系发现下一步资源；它不替代媒体类型/API 合同、运行时校验或授权，也不要求服务端返回 HTML。HTTP 的 GET “安全”指请求语义不要求源站改变状态，不意味着调用代码无需谨慎处理缓存、重定向或响应正文。安全读取与写入操作在通用 API 中的设计边界见[如何设计可预期的 HTTP API 契约？](../../../../engineering-foundations/backend/http-api-contracts.md)。

> [!info]- 来源
> - REST 的统一接口约束及客户端从表示发现后续状态转移：[Roy Fielding, REST Dissertation](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，§5.1.5、§5.3.3；2000。
> - GET 的安全语义、客户端对非幂等请求的自动重试建议、POST 方法语义、409 Conflict：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§9.2.1、§9.2.2、§9.3.3、§15.5.10；2022-06。
> - 相对 URL 的解析、URL 规范化和 origin：[WHATWG URL Standard](https://url.spec.whatwg.org/)，§4.4、§4.7、§6.1；Living Standard，核对日期：2026-11-13。
> - Fetch 默认 redirect mode 是 follow；redirect: "error" 在重定向时返回 network error；cache: "no-store" 将请求按没有 HTTP cache 的路径处理：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，Request 的 redirect mode、HTTP-redirect fetch、HTTP-network-or-cache fetch 与 cache mode；Living Standard，最后更新 2026-10-19，核对日期：2026-11-13。
> - 缓存复用条件、unsafe 请求写透与目标 URI 失效范围：[IETF RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html)，§4、§4.4；2022-06。
> - links/actions 的 JSON 字段、关系名、方法以及成功/冲突响应均是本章显式定义的合成 API 合同，不是 Fielding、RFC 或 Fetch 定义的通用 schema。
