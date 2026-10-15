# Reading, Debugging, and Reviewing Code / 阅读、调试与审查代码

**Core explanation / 核心解释：** Debugging and review start from expected behavior, then trace values and side effects through the actual call path. A minimal reproduction tests one falsifiable hypothesis; evidence points to the cause; the smallest coherent fix restores the lost behavior; a focused regression check distinguishes the fix from the failure. Read generated code and tests independently because both may share the same mistaken assumption. / 先写出可以观察的预期，再沿入口、调用者、依赖、数据访问和副作用追踪值，并用最小请求检验一个可证伪假设。证据指向哪一步丢掉了约束，就在那一步做最小一致修复，再用相反边界验证。生成代码和测试要分开读，尤其检查测试是否只覆盖 happy path；测试通过不能替代对需求的独立核对。

**Key terms / 关键术语：** expected behavior / 预期行为；entry point / 入口；call path / 调用路径；minimal reproduction / 最小复现；falsifiable hypothesis / 可证伪假设；root cause / 根因；regression check / 回归检查；generated change / 生成式改动。

## Follow one generated authorization bug / 跟踪一个生成式授权缺陷

Suppose a generated refactor changes a job lookup from the existing tenant-scoped query to `session.get(Job, job_id)`. Its generated test creates a job for `tenant-a` and reads it back as `tenant-a`; that test passes. The requirement, however, is that the current tenant may read only its own job. A matching owner read does not exercise that boundary.

Start with an observable expectation: after `tenant-a` creates a job, `tenant-b` requesting the same ID receives `404`, while `tenant-a` still receives `200`. Then follow the request rather than guessing from the response: the route reads `tenant_id` from the principal dependency, passes it to the database lookup, and serializes the returned job. The generated patch still receives `tenant_id`, but its new `session.get` lookup ignores it.

The minimal reproduction is one create and one read under a different tenant. If the response is `200`, the hypothesis “the database lookup no longer constrains the row by the current tenant” is supported. If the route rejects the second tenant earlier, or the lookup is tenant-scoped, the hypothesis is false and the next step is to inspect that earlier branch or another code path. This makes the hypothesis testable rather than a label attached after the fact.

The smallest coherent fix is to restore both predicates in the query:

~~~python
job = session.scalar(
    select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id)
)
~~~

The root cause is the lost tenant predicate, not response serialization or a missing test fixture. Keep the owner success path, add the cross-tenant `404` assertion, and retain the missing-principal, invalid-request, duplicate-create, and repeated-worker checks from [Software Testing Strategy / 软件测试策略](../testing/software-testing-strategy.md). Those nearby checks show that the fix did not break the surrounding route and persistence behavior. They do not prove production identity validation or broker semantics, which were not part of this reproduction.

## Read a generated change against the requirement / 对照需求独立阅读生成式改动

Read the requirement first and write down the expected outcomes before using the generated tests as a guide. Then inspect the changed route, its callers and dependencies, the query or transaction it reaches, and the error/response mapping. Compare the assertions with that expected behavior: in this case, a suite that tests only `tenant-a` cannot detect a missing tenant predicate, even if every generated test passes.

Run the minimal counterexample against the changed code, inspect the actual query and row returned, apply the narrow fix, then run the owner and non-owner cases plus relevant nearby checks. Read the new tests too: verify that they reach the changed route and real database boundary, that their fixtures establish the intended principal, and that they assert the required failure rather than only a happy-path response. For a database or delivery claim, identify the engine or broker the test actually used; a stubbed session or local function call is evidence only for that seam.

The review is complete when the observed failure, its cause, the changed behavior, and the regression evidence line up with the requirement. A model-written test passing is one observation, not independent proof that the requirement is complete. Keep the change as small as the cause allows: this example needs the missing query predicate and its negative regression assertion, not a new repository layer or review-management process.

**Interview answer / 面试回答：** I first state the expected behavior, trace the entry point through the relevant dependency and data access, and build the smallest request that can disprove my hypothesis. Here, the other tenant receives the row because the generated refactor drops the tenant condition. Restoring that condition and running both owner and non-owner requests is the focused fix and regression check. I read the generated implementation and tests independently because their shared assumptions can omit the same requirement. / 我先明确预期行为，再沿入口、依赖和数据访问追踪调用路径，并构造能够推翻假设的最小请求。这个例子中，另一租户读到了任务，是因为生成式重构删掉了租户条件。恢复该条件并分别运行所有者和非所有者请求，就是聚焦的修复与回归验证。我会独立阅读生成实现和测试，因为二者可能共享同一个遗漏假设。

**Sources checked 2026-10-15:** GitHub's official [reviewing proposed changes](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests) documentation describes inspecting commits and diffs, and its [review concepts](https://docs.github.com/en/pull-requests/concepts/giving-reviews) explain review feedback and deeper inspection. The reproduced tenant behavior and query correction are exercised in the linked synthetic API example; no personal project or generated artifact is used.
