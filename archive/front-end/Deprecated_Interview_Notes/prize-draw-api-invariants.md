# How should a prize-draw API enforce eligibility and inventory? / 抽奖 API 如何保证资格与库存？

The server owns eligibility, random selection, inventory reservation, and the authoritative result; the browser submits an entry and displays the response. Define idempotency and duplicate-entry rules so retries cannot create extra entries or over-allocate prizes. / 资格判断、抽取、库存预留和权威结果必须由服务端负责；浏览器只提交参与请求并展示结果。定义幂等与重复参与规则，避免重试创建额外记录或超发奖品。

## Request and result flow / 请求与结果流程

1. GET /draws/{drawId} returns public rules, schedule, and visible campaign status.
2. An authenticated user submits POST /draws/{drawId}/entries with a documented idempotency key. The service checks campaign state, account eligibility, and duplicate-entry policy.
3. One transaction or equivalent atomic workflow records the entry and result, then reserves limited inventory. Concurrent requests must not allocate beyond the available quantity. The draw algorithm and audit trail must meet the campaign's fairness and regulatory requirements.
4. GET /draws/{drawId}/entries/{entryId} returns the authoritative result and claim state. It must not expose another user's entry.
5. A winner submits POST /prizes/{prizeId}/claims; the service validates the winner, collects only needed delivery data, and records fulfillment.

User history and public prize details can use separate read endpoints. Administrative campaign and prize operations need stricter authorization. Analytics are untrusted reporting events and must not decide eligibility or prize outcomes.

## Invariants and failure behavior / 不变量与失败行为

The idempotency contract defines scope, retention, replay response, and behavior when the first response is unknown to the client. A unique constraint for one entry per user and campaign, plus a transaction or lock around inventory, are common enforcement tools; exact choices depend on database and consistency needs. Return explicit closed-campaign or conflict errors instead of asking the client to infer state from a generic failure.

Keep identity and object authorization at the server boundary. See [HTTP API Contracts](../../../engineering-foundations/backend/http-api-contracts.md), [System Design Fundamentals](../../../engineering-foundations/architecture/system-design-fundamentals.md), and [Web Security and Authentication](../../../engineering-foundations/security/web-security-and-authentication.md).
