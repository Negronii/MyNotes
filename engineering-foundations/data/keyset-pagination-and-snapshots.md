# 怎样无重复、无遗漏地分页读取一个还在变化的集合？

上一章的导出 worker 每页开一笔短事务、读完就归还连接；集合 API 也要把一个长列表分成多次请求返回。两者面对同一个问题：前一页和后一页之间，集合可能有行插入或删除。本章先说明按偏移翻页为什么会漏项，再给出键集分页的构造、集合 API 的分页契约、后台批量读取的页预算，最后讨论什么时候需要所有页来自同一个快照、代价是什么。

## 按偏移翻页为什么会漏项和重复？

`LIMIT 2 OFFSET 2` 的意思是“跳过排序后的前 2 行，再取 2 行”。偏移量记的是**位置**，不是读到了哪一行。位置在两次请求之间会移动：

- 集合里有报表 40、41、42，按 ID 升序、每页 2 条。第一页返回 `[40, 41]`。
- 读第二页之前，40 被删除。集合变成 `[41, 42]`，`OFFSET 2` 跳过这两行，第二页为空：42 被漏掉。
- 反过来，若在读第二页之前，排在前面的位置插入一行，原来的 41 被挤到第 3 位，第二页会再返回一次 41。

只要集合在翻页期间会变，按位置续读就既可能漏也可能重。偏移量还有成本问题：被跳过的行仍要在服务端算出来，偏移越大越慢。修法是记住“读到了哪一行”，从这一行之后继续。

## 键集分页：用最后一行的完整排序键续读

keyset pagination (键集分页) 把上一页最后一行的排序键当作游标，下一页只取排序键**严格大于**游标的行。这正是[有序数据怎样让二分查找和双指针安全排除候选？](../computation/ordered-search-and-two-pointers.md)里 upper_bound 的数据库版本：下一页从第一个大于游标的位置开始。

以导出 worker 读取 `account_events` 为例，按 `(occurred_at, event_id)` 排序：

~~~sql
SELECT event_id, occurred_at
FROM account_events
WHERE account_id = :account_id
  AND occurred_at >= :start_at AND occurred_at < :end_at
  AND (occurred_at, event_id) > (:after_time, :after_id)   -- 第一页省略这一行
ORDER BY occurred_at, event_id
LIMIT :limit;
~~~

`(occurred_at, event_id) > (:after_time, :after_id)` 是 row value comparison (行值比较)：先比第一列，相等时再比第二列，与 `ORDER BY occurred_at, event_id` 的字典序一致。时间范围取 Q2 的左闭右开区间 `[2026-04-01T00:00:00Z, 2026-07-01T00:00:00Z)`。范围、游标和页大小全部作为参数绑定。

这个构造要成立，排序键必须满足三个条件：

1. **完整排序键唯一。** `occurred_at` 可能重复，所以要接上唯一的 `event_id`。没有唯一的末位键，同一时刻的几行在页边界上没有确定的先后，游标无法区分“读过的”和“没读过的”。
2. **排序键非空。** NULL 在行值比较里得到 UNKNOWN，这些行会从续读条件中消失。
3. **排序键写入后不改。** 某行的键在扫描期间改变，它可能被读两次或一次也读不到。

游标取**本页最后一行按排序键顺序排列的字段**。上面的 SQL 返回列顺序是 `event_id, occurred_at`，构造游标时要按排序键重排成 `(occurred_at, event_id)`，不能把整行原样当游标。

> [!example] 页大小 2 时的游标
> 为了看清边界，把页大小从 100 缩到 2，SQL 不变。三行数据：`(event_id=100, 10:00)`、`(101, 10:00)`、`(102, 10:01)`。
>
> - 第一页返回 100、101，游标是最后一行的 `(10:00, 101)`。
> - 第二页条件 `(occurred_at, event_id) > (10:00, 101)`，只返回 102。这一页 1 行，少于页大小 2，这次查询之后没有更多行。
> - 若游标错取成 `(10:00, 100)`，第二页会返回 101、102，101 被重复读出。

行值比较要求各列同向排序。若排序是 `occurred_at DESC, event_id ASC` 这样混合方向，就要展开成 `occurred_at < :t OR (occurred_at = :t AND event_id > :id)`。查询要能沿索引顺序读取，索引列要覆盖过滤列和排序列，例如 `(account_id, occurred_at, event_id)`；列序怎样从过滤与排序推出，见[约束守住哪些规则，索引又怎样服务读取？](constraints-and-indexes.md)。

键集分页保证的是：**整个扫描期间一直存在、排序键没变的行，恰好返回一次。** 扫描期间插入的行，落在游标前面就读不到，落在后面就会读到；被删除的行可能已经读过，也可能不再出现。它保证游标一直前进，不保证结果等于某一时刻的集合。需要后者时，见本章最后一节。

## 集合 API 的分页契约

worker 直接查数据库，`LIMIT n` 返回少于 n 行就说明这条语句看到的结果已经取完。API 调用方看不到服务端的查询，只能依据契约判断。一个可依赖的分页契约规定以下几件事：

- **页大小。** 默认值和上限，例如默认 20、最大 100；下面的演示显式传 `limit=2`。
- **确定性排序。** 排序键唯一，同样的筛选每次得到同样的顺序。
- **显式结束信号。** 例如 `next_cursor` 是必返回字段，最后一页返回 JSON `null`。客户端只在看到结束信号时停止。
- **短页不等于结束。** 服务端可能因资源上限少返回几项，但仍给出游标；客户端只凭“这一页不满”就停，会漏项。
- **不透明游标。** 客户端原样传回，不解析也不拼接。续页可以在允许范围内改 `limit`；筛选条件或排序变了，就要从第一页重新开始。
- **游标绑定上下文。** 游标里（或服务端按游标查到的记录里）绑定筛选条件、授权范围、过期时间和最后一行的完整排序键。未知或过期的游标返回错误（例如 `400`），提示调用方从头开始。
- **每页重新授权。** 游标不是授权凭据；权限可能在两页之间被撤销。

下面是报表列表的两页（报表 40、41 及其标题是合成数据）：

~~~http
GET /v1/accounts/acct-17/reports?limit=2 HTTP/1.1
Accept: application/json
~~~

~~~json
{"items":[{"id":40,"title":"Weekly digest"},{"id":41,"title":"Monthly overview"}],"next_cursor":"opaque-token-A"}
~~~

~~~http
GET /v1/accounts/acct-17/reports?limit=2&cursor=opaque-token-A HTTP/1.1
Accept: application/json
~~~

~~~json
{"items":[{"id":42,"title":"Service health"}],"next_cursor":null}
~~~

第一页读到 41 为止，第二页 `[42]` 以 `null` 结束。若 `opaque-token-A` 背后存的是偏移量 2，第一节的删除场景照样会漏掉 42；存的是排序键“id > 41”，删除 40 不影响结果。

结束信号的写法因规范而异。Google AIP-158 规定最后一页的 `next_page_token` 为空字符串，并要求续页时除页大小外的参数与首页一致。选哪种写法都行，关键是写进契约、写进 schema（`next_cursor` 必填且允许 `null`），并作为兼容约束对待：改变结束标志会破坏已有调用方。错误怎样表示、契约怎样演进，见[怎样让调用方可靠地判断 API 的成功、失败和变化？](../services/api-contracts-errors-and-evolution.md)。前端长列表怎样使用这类游标，是[长列表的成本在哪里，分页和虚拟化各省掉什么？](../../frontend/delivery/long-lists-pagination-and-virtualization.md)的应用。

## 后台批量读取：页预算与“宁可失败不截断”

导出 worker 读的不是无限列表，而是一个有上限的范围：每页 100 行，页数预算 12，服务端硬上限也是 12，最多 1,200 行。参数从已授权、已持久化的任务记录里读取，不从队列消息正文里取。

~~~python
PAGE_SIZE = 100
MAX_PAGE_BUDGET = 12

def iter_job_pages(job_id):
    job = load_authorized_export_job(job_id)   # 从数据库读任务并复查权限
    if not 1 <= job.max_pages <= MAX_PAGE_BUDGET:
        raise InvalidJobBudget(job_id)
    after = None
    for page_number in range(1, job.max_pages + 1):
        rows = load_account_page(               # 每页一个新会话与短事务
            job.account_id, job.start_at, job.end_at,
            after=after, limit=PAGE_SIZE,
        )
        if len(rows) < PAGE_SIZE:
            yield rows
            return                              # 短页：这个范围读完了
        if page_number == job.max_pages:
            raise RangeExceeded(job_id)         # 第 12 页仍满：可能还有更多
        yield rows
        last = rows[-1]
        after = (last.occurred_at, last.event_id)
~~~

规则是：满页继续，短页结束；读到第 12 页仍满 100 行，就以“范围超限”失败。这条规则让**恰好 1,200 行**的范围也失败，因为第 12 页满页时无法知道有没有第 1,201 行。本例宁可保守失败，也不把可能被截断的结果标成完整。若契约要求接受恰好 1,200 行，就要另行探测下一行，例如最后一页多取一行。

失败时，调用方丢弃尚未发布的部分输出；只有迭代正常结束、产物已经写好，任务才算成功。部分输出怎样清理、任务状态怎样提交，属于主线四：worker 只有在持久状态确认成功之后才能确认任务完成，见[任务失败、被取消或 worker 失联后，怎样收尾而不重复也不留孤儿？](../services/job-retries-cancellation-and-cleanup.md)。

## 每页短事务，还是所有页同一个快照？

PostgreSQL 的 Read Committed 在每条语句开始时取快照。每页一笔短事务，意味着 12 页可能看到 12 个不同时间点的数据：一行在第 3 页读完之后插入到游标前面，后面的页不会回头拾取它。稳定的排序键只保证游标前进，不保证导出等于某一时刻的账户状态。

| 选择 | 得到什么 | 代价 |
| --- | --- | --- |
| 每页短事务（本例默认） | 连接只在每页查询期间占用；读完一页先还连接，再格式化、压缩、写出 | 各页时间点不同；只保证键集分页的“一直存在的行恰好一次” |
| 一笔有界的 Repeatable Read 事务覆盖所有页 | 所有页来自事务开始时的同一快照 | 一条连接从第一页一直占到最后一页结束，包括页与页之间的处理时间；长事务还会推迟旧行版本的清理 |
| 版本化快照（按快照版本或截至时间读取） | 每页仍可短事务，结果对应一个固定版本 | 数据模型要保存版本，读取要带版本条件 |

改成流式读取时尤其要算清第二种代价。若 worker 一直持有数据库游标，边读边把行推给压缩和写出，下游一慢，背压就沿管线传回读取端：读取暂停，但事务和连接还开着。于是“下游慢”直接变成“连接被占更久”，要计入连接池与 worker 执行槽的预算。背压怎样逐段传回源头，见[流怎样把“慢下来”逐段传回源头，中途失败又留下什么？](../runtime/stream-backpressure-and-partial-output.md)。确需同一快照时，明确选择有界长事务或版本化快照并核算代价，不要悄悄把短事务分页换成长游标。

跨 HTTP 请求的分页同理：若 API 承诺所有页来自固定快照，后续请求就必须继续读同一个快照，游标要带上快照版本或截至时间。

## 读对之后，重复读取交给缓存

本章给出无重复、无遗漏翻页的三件套：唯一、非空、不变的完整排序键；以最后一行排序键为游标的严格大于续读；带显式结束信号、绑定上下文并每页重新授权的分页契约。后台读取另有页预算和“宁可失败不截断”的完成规则，以及短事务与同一快照之间的明确取舍。读对之后，常被重复读取的展示数据还会放进缓存；下一章[加了缓存之后，读到的数据最多会旧多久？](caching-and-staleness.md)回答缓存值能落后数据库多久、怎样把这个时间写成可证明的上界。

> [!info]- 来源
> - `LIMIT`/`OFFSET` 需要唯一稳定排序，`OFFSET` 跳过的行仍要计算：[PostgreSQL 18, LIMIT and OFFSET](https://www.postgresql.org/docs/18/queries-limit.html)，§7.6；行值比较从左到右逐列比较：[Row Constructor Comparison](https://www.postgresql.org/docs/18/functions-comparisons.html#ROW-WISE-COMPARISON)，§9.25.5。核对于 2026-11-12。
> - 长事务持有的旧快照会阻止清理仍可能对它可见的旧行版本：[PostgreSQL 18, Routine Vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html)，§24.1.2 Recovering Disk Space，核对于 2026-11-26。
> - Read Committed 每条语句取快照、Repeatable Read 在事务内保持同一快照：[PostgreSQL 18, SET TRANSACTION](https://www.postgresql.org/docs/18/sql-set-transaction.html)，`ISOLATION LEVEL`，核对于 2026-11-12。
> - 不透明 page token、除页大小外续页参数须一致、最后一页 `next_page_token` 为空、短页不代表结束：[Google AIP-158, Pagination](https://google.aip.dev/158)，2019-02-18，Guidance，核对于 2026-11-12。
> - 偏移游标在删除后漏项、`[40, 41] → [42] + null` 两页回放、页大小 2 的游标例、12 页 × 100 行预算均为本章合成设定，结果为手算。
