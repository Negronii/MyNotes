# How does a React client follow hypermedia links from an API? / React 客户端如何跟随 API 提供的超媒体链接？

A hypermedia response advertises available transitions, and a client follows the link relation the server supplies instead of constructing every target URL itself. Use a safe link for navigation and an API-defined method for state-changing operations. / 超媒体响应会公布可用的状态转移，客户端按服务器提供的关系跟随链接，而不自行拼出所有目标 URL。导航使用安全链接；改变状态的操作应按 API 定义的方法发送。

## HATEOAS: Hypermedia as the Engine of Application State / 超媒体作为应用状态引擎

HATEOAS (Hypertext As The Engine Of Application State) is the REST interface constraint by which a client discovers application-state transitions through hypermedia in server representations. It is one of REST's interface constraints, alongside resource identification, manipulation through representations, and self-descriptive messages ([Fielding, REST dissertation, §5](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)).

## Key Concepts

### Hypermedia Driven

HATEOAS lets a client discover available transitions through links or action affordances in the server's representations. The client still understands the media type and link relations, but need not hard-code every target URL.

### Example Scenario

Consider an e-commerce application where a client makes a POST request to buy a product. The server can return the order representation and advertise available navigation or actions, such as:

- View the order details through a `self` or details link.
- A cancellation action when cancellation is currently allowed.
- An update action when editing is currently allowed.

The response can expose the transitions currently available for the order. A client follows a relation when present; it does not infer every target from the resource's identifier. The action's HTTP method and request shape must come from the API's advertised affordance or contract.

### Implementation in React

For example, a JSON representation can carry link relations that a component renders as ordinary links:

```tsx
type ApiLink = { rel: string; href: string };
type Order = { status: string; links: ApiLink[] };

function OrderDetailsLink({ order }: { order: Order }) {
  const self = order.links.find(link => link.rel === "self");
  return self ? <a href={self.href}>View order details</a> : null;
}
```

An ordinary `<a>` follows a `GET` link and is appropriate for safe navigation such as viewing details. Do not make it perform cancellation or another state change: expose that as an API-defined operation and send its declared method, for example from a button or form. [HTTP defines GET as a safe method](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.1). HATEOAS is a representation and navigation convention; it does not require returning HTML. Do not inject untrusted HTML with `dangerouslySetInnerHTML`; see [Web Security and Authentication / Web安全与身份验证](../../../../engineering-foundations/security/web-security-and-authentication.md) for the separate XSS boundary.
