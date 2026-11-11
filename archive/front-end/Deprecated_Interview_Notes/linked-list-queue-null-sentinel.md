# 数值队列的空值哨兵条件是什么？

`poll(): number | null` 只有在运行时不入队 `null` 时，才能单凭返回的 `null` 表示队列为空；空队列 `[]` 与只含 `null` 的队列 `[null]`，各调用一次 `poll()` 都会返回 `null`。启用 `strictNullChecks` 时，TypeScript 会在类型检查中拒绝把 `null` 或 `undefined` 传给 `number` 参数；关闭时二者都可通过类型检查，而类型检查不验证运行时输入。若允许入队 `null`，可先检查 `size > 0` 再同步调用 `poll()`，前提是两步之间队列状态未改变。实现和通用空状态不变量见[队列怎样同时维护头、尾和空状态？](../../../engineering-foundations/algorithms/queue-and-stack-representations.md#%E9%98%9F%E5%88%97%E6%80%8E%E6%A0%B7%E5%90%8C%E6%97%B6%E7%BB%B4%E6%8A%A4%E5%A4%B4%E3%80%81%E5%B0%BE%E5%92%8C%E7%A9%BA%E7%8A%B6%E6%80%81%EF%BC%9F)。
