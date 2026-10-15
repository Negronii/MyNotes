# Caching and Redis / 缓存与 Redis

**Core explanation / 核心解释：** In cache-aside, the database remains the source of truth: reads check the cache first and load the database on a miss; writes commit to the database and then invalidate the cached copy. A TTL bounds how long one cached value can live, but invalidation races and cache failures still need an explicit freshness and load policy. / 在 cache-aside 模式中，数据库仍是事实来源：读取先查缓存，未命中时再读取数据库；写入先提交数据库，然后使缓存副本失效。TTL 限制单个缓存值的存活时间，但失效竞态和缓存故障仍需要明确的新鲜度与负载策略。

**Key terms / 关键术语：** cache-aside / 旁路缓存；source of truth / 事实来源；time to live (TTL) / 存活时间；invalidation / 失效；cache stampede / 缓存击穿；negative caching / 负缓存；stale data / 陈旧数据。

## One record, one read/write lifecycle / 一个记录的读写过程

Suppose `products` is authoritative and the cache key is `product:42`. A typical read is:

1. `GET product:42`. On a hit, return the cached representation after applying the same authorization and response rules as a database read.
2. On a miss, query the primary database. If the product exists, cache the representation with a TTL, for example `SET product:42 "..." EX 30`, then return it.
3. If it does not exist, an optional short negative entry can reduce repeated misses: cache a “not found” sentinel for a few seconds. Keep this TTL shorter than the normal entry, and invalidate it when the product is created. Do not cache a database timeout or error as “not found.”

For a write, update the authoritative row and commit first; only then issue `DEL product:42`. The next read repopulates from the database. Redis `GET`, `SET ... EX`, `DEL`, and `TTL` are useful implementation primitives, but these commands do not make a Redis mutation atomic with the database transaction.

The [Database Fundamentals / 数据库基础](../databases/database-fundamentals.md) note covers the constraints and transaction boundary that protect the source-of-truth write.

### Make the freshness window explicit / 明确新鲜度窗口

With a 30-second TTL, a value that was filled before an update can remain visible until its entry expires if the post-commit invalidation fails. But TTL is not an end-to-end consistency guarantee: a reader can load the old database value just before a concurrent write commits, then populate the cache after the writer's `DEL`; that stale fill receives a fresh TTL. Each entry's lifetime is bounded, but repeated or delayed stale fills can extend the period in which clients see stale data. If read-after-write freshness is required, bypass the cache for that read or use a versioned/ordered invalidation design; do not assume Redis alone coordinates the two stores.

Include every dimension that changes the returned value in the cache key, such as tenant or locale, and keep authorization checks outside an untrusted cached payload. The existing [AI response-cache explanation](../../ai-engineering/systems/ai-application-architecture.md) applies the same key-isolation and freshness discipline to exact or semantic response reuse; semantic similarity does not establish that data is current or authorized.

## Expiration bursts and cache outages / 集中过期与缓存故障

When a popular key expires, many requests can miss together and send duplicate reads to the database. Coalesce concurrent misses for the same key inside each application process, and add small random jitter to TTLs so many keys do not expire together. Local coalescing reduces one process to roughly one loader per key at a time; it does not coordinate other processes. A Redis-backed short lock is another option at higher fan-out, but it needs a bounded lease and wait, plus safe owner-only release.

A cache outage does not by itself corrupt the authoritative row. If a cache lookup fails, an application may read through to the database only within a deliberate bound: use a request deadline, cap concurrent fallback reads or apply admission control, and fail quickly when the database budget is exhausted. Otherwise a cache outage can turn every request into a database request and exhaust database connections. Serve stale cached data only when that endpoint has a stated maximum acceptable age; for authorization, balances, or other correctness-sensitive decisions, read the authoritative source or fail closed. Cache-fill and invalidation failures should be visible as operational errors rather than silently treated as valid data.

## Representative answer / 代表性面试回答

**How would you add a cache in front of a database, and what happens if Redis fails? / 如何在数据库前增加缓存，Redis 故障时应怎样处理？**

I would keep the database authoritative and use cache-aside: read the cache, load on a miss, write with a TTL, and invalidate only after a database write commits. I would choose the TTL from the endpoint's freshness requirement, account for the failed-invalidation and stale-fill windows, and coalesce concurrent misses for hot keys. If Redis fails, I would bound database fallback by deadlines and concurrency limits; cache loss should increase load, not silently change the source of truth. I would serve stale data only where its maximum age is acceptable.

我会让数据库保持事实来源，并采用 cache-aside：先读缓存，未命中时查数据库，写入缓存时设置 TTL，并只在数据库写入提交后执行失效。我会根据接口的新鲜度要求选择 TTL，考虑失效失败和陈旧回填窗口，并合并热点键的并发未命中请求。Redis 故障时，我会用截止时间和并发上限约束数据库回退；缓存丢失应增加负载，但不能悄悄改变事实来源。只有在业务明确接受最大陈旧时间时才提供旧值。

**Sources and verification / 来源与验证：** Redis [cache-aside](https://redis.io/docs/latest/develop/use-cases/cache-aside/) and [node-redis cache-aside example](https://redis.io/docs/latest/develop/use-cases/cache-aside/nodejs/), checked 2026-10-15. The official examples demonstrate cache-first reads, TTL-bearing writes, invalidation, and a short-lived stampede lock. The flow above is a generic application design; no Redis server was deployed, so Redis commands and outage behavior were not runtime-tested. TTL and `DEL` are implementation tools, not a cross-store consistency protocol.
