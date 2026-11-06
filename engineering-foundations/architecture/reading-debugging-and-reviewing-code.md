# 怎样用最小反例定位报表授权回归？

报表平台工程师收到一条跨租户访问回归：tenant-a 读自己的 report 42 应返回 200，tenant-b 猜中同一 ID 也只能得到 404。为了定位并修复回归，先把需求改写成可观察结果，再提出一个能被反例推翻的根因假设。若新改动让 B 得到 200，就沿主体、application programming interface（应用程序接口，API）路由、查询和序列化追踪请求，而不是先猜数据库或框架有问题。针对该边界的可运行测试见[测试如何证明报表服务改动？](../testing/software-testing-strategy.md)。

~~~mermaid
flowchart TD
    A[可信主体为 tenant-b，请求 report 42] --> B[主体依赖得到当前租户]
    B --> C[路由把主体交给数据查询]
    C --> D{查询同时限制租户与报表 ID？}
    D -->|否| E[返回其他租户的行]
    D -->|是| F[查无匹配行，返回 404]
~~~

这张图标出三处必须核对的交接：主体依赖是否正确给出当前租户，路由是否把它传入查询，查询是否把主体范围用于取行。一个响应状态只能提示失败发生了，不能单独证明是哪一处失效。

## 先把症状变成可证伪假设

假设一次自动化重构把原有的租户范围查询：

~~~python
report = session.scalar(
    select(Report).where(
        Report.report_id == report_id,
        Report.tenant_id == tenant_id,
    )
)
~~~

替换成按主键直接读：

~~~python
report = session.get(Report, report_id)
~~~

这个合成模型把 report_id 设成全局主键、tenant_id 设成资源所有者，所以 session.get(Report, report_id) 是合法的主键查找，但不会验证所有权。若真实表用复合主键，get 的参数应是相应的主键 tuple；具体形式要与真实 schema 对齐。原测试只以 tenant-a 创建并读取自己的报表，因此仍然通过。这个测试确认了所有者的成功路径，却没有测试访问边界。

先写出预期观察：

| 主体 | 请求 | 预期结果 |
|---|---|---|
| tenant-a | GET /api/reports/42 | 200，返回 report 42 |
| tenant-b | GET /api/reports/42 | 404，不泄露跨租户资源是否存在 |
| 无有效主体 | GET /api/reports/42 | 401，由认证入口拒绝 |

假设是“数据读取不再依据当前 tenant_id 限定行”。最小反例只需要一条归属 tenant-a 的 report 42 和一次可信主体 tenant-b 的读取。变更前若得到 200，这支持假设；若得到 404，则应检查主体解析、更早的拒绝分支、缓存或另一条路由。反例缩小调查范围，但只有看到查询缺少租户谓词并将其与这条行记录对应起来，才定位到数据库查询根因。

## 沿调用路径找出丢失的条件

从 API 路由向内读：

1. 确认请求经过哪一个公开入口，是否经过认证依赖。
2. 看依赖返回的主体来自已验证会话或 token（令牌），而非任意客户端字段。
3. 沿函数调用检查 report_id 和 tenant_id 是否都传到数据层。
4. 查看最终 SQL 或 object-relational mapping（对象关系映射，ORM）条件、行归属以及 cache（缓存）是否绕过了同一授权范围。
5. 查看错误映射和序列化，确认不存在“查无权限行却返回成功”之类的备用分支。

在这个合成例中，路由仍然拿到了 tenant_id，但 session.get 只按主键载入记录，没有使用 tenant_id。根因是查询丢失了范围条件。聚焦修正就是重新同时约束租户和资源：

~~~python
report = session.scalar(
    select(Report).where(
        Report.report_id == report_id,
        Report.tenant_id == tenant_id,
    )
)
~~~

然后重跑所有者和非所有者测试及同一入口的邻近检查。若成功响应缓存键仅包含 report_id，数据库查询正确也可能再次泄露；缓存命中必须在返回前执行同等范围检查。这类授权边界和后台任务执行时的复验条件见[如何逐次授权租户内的报表资源？](../security/web-security-and-authentication.md)。

## 独立阅读实现与测试

先从需求列预期结果，再读修改过的路由、调用者、依赖、SQL/事务和错误响应。之后阅读测试本身，判断它是否确实通过被修改的入口到达真实数据库，fixture（测试夹具）是否建立了正确主体，断言是否覆盖必须拒绝的访问。模型或生成式改动的实现与测试可能共享同一遗漏假设；全部通过也不代表遗漏的需求已被验证。

一个实际复核要把四项证据串起来：报告 42 的所有者/非所有者输入，观察到的状态码，改动前后的查询条件，以及回归断言。需要数据库约束或 broker（消息代理）的 redelivery（重投）结论时，再确认测试实际使用的引擎或 broker；模拟会话、本地重复调用和部署探针只能证明各自的接缝，不能外推到未执行的边界。

> [!example] 反例通过前后比较
> 变更前：tenant-b 请求 /api/reports/42 得到 200，支持“缺少租户范围”的假设；沿调用路径确认查询确实漏了 tenant 谓词，才定位到根因。
>
> 变更：查询从只按 report_id 读取，改为同时匹配 report_id 和主体的 tenant_id。
>
> 变更后：tenant-a 仍得到 200，tenant-b 得到 404，匿名请求得到 401。只有这些观察与需求一致，才说明当前回归已被修复；其他 query path、缓存和后台导出仍各有自己的边界。

在共享分支上保留小而聚焦的修复，用[Git 如何记录通过验收的改动？](../version-control/git-essentials.md)记录源码快照。评审时独立检查实际差异、需求边界和测试覆盖；具体的代码评审流程由团队自己的仓库政策规定。

> [!info]- 来源
> - GitHub 官方 [Reviewing proposed changes](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests) 与[Review concepts](https://docs.github.com/en/pull-requests/concepts/giving-reviews)，checked 2026-11-06：支持从差异和提交检查改动与评审意见；本文的最小反例是合成 API 的行为推演。
> - 租户授权的规范规则由[逐次授权报表资源](../security/web-security-and-authentication.md)承担；本篇只用该规则定位一次 SQL 条件遗漏，不重复完整认证和授权设计。
