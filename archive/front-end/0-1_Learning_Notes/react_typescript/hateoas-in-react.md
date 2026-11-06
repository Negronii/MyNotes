# React 客户端怎样使用 API 表示中的超媒体链接？

HATEOAS（Hypermedia as the Engine of Application State，超媒体作为应用状态引擎）让客户端从服务端表示中发现当前可用的状态转移。客户端仍须理解媒体类型和关系名；它只是不再仅靠资源 ID 拼出每个目标地址。通用 API 契约与报表详情链接示例见[如何设计可预期的 HTTP API 契约？](../../../../engineering-foundations/backend/http-api-contracts.md)。

旧课程的电商例子可以表示成订单详情链接和服务端当前允许的取消动作。此例约定 `href` 是同源站点根路径；若 API 用相对 URI，客户端应按响应 URI 的基址解析。只有 API 契约说明的安全 GET 链接适合直接渲染为普通导航链接；改变订单状态应按响应里定义的操作及方法提交。

~~~tsx
type ApiLink = { rel: string; href: string };
type ApiAction = { rel: string; href: string; method: "POST" | "DELETE" };
type Order = {
  id: string;
  links: ApiLink[];
  actions: ApiAction[];
};

declare function submitOrderAction(action: ApiAction): Promise<Order>;
declare function showActionError(message: string): void;

async function runOrderAction(
  action: ApiAction,
  onOrderUpdated: (order: Order) => void
) {
  try {
    onOrderUpdated(await submitOrderAction(action));
  } catch (cause) {
    showActionError(cause instanceof Error ? cause.message : String(cause));
  }
}

function OrderActions({
  order,
  onOrderUpdated,
}: {
  order: Order;
  onOrderUpdated: (order: Order) => void;
}) {
  const details = order.links.find(link => link.rel === "self");
  const cancel = order.actions.find(action => action.rel === "cancel");

  return (
    <section>
      {details && <a href={details.href}>查看订单</a>}
      {cancel && (
        <button type="button" onClick={() => void runOrderAction(cancel, onOrderUpdated)}>
          取消订单
        </button>
      )}
    </section>
  );
}
~~~

这里的 actions 字段是示例 API 明确约定的操作描述，并不是 HTML 或 HTTP 自动提供的通用 JSON schema。示例约定提交成功后返回更新后的订单表示，父组件通过 `onOrderUpdated` 替换旧表示，按钮会随新的 `actions` 更新。若服务端不返回 cancel 操作，客户端就不显示该动作；若返回的字段没有声明 method 和请求形状，客户端不能从 rel 名猜测写请求应怎么发。服务端收到操作请求时仍须重新校验身份、权限和当前订单状态，因为页面上的可见操作可能已过期。超媒体也不要求 API 返回 HTML，JSON 表示同样可以定义关系。

> [!info]- 来源
> - HATEOAS 是 REST 接口约束之一，客户端通过表示发现可用状态转移：[Roy Fielding, REST Dissertation, §5.1.5](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，2000；核对日期：2026-11-06。
> - HTTP GET 的安全方法语义：[IETF RFC 9110 §9.2.1](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.1)，2022-06；核对日期：2026-11-06。
