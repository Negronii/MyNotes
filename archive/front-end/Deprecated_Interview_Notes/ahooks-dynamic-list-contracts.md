# How does ahooks useDynamicList keep item identity through edits? / ahooks useDynamicList 如何在编辑时保持项目身份？

Use getKey(index) as the React key for hook-managed rows so insertions, removals, and moves do not make identity depend on the current position. Callbacks receive current indices; stable item identity and list position are separate concepts. / 对 Hook 管理的行使用 getKey(index) 作为 React key，使插入、删除和移动时的身份不依赖当前位置。回调接收当前索引；稳定项目身份与列表位置是不同概念。

The v3.10.0 reference lists these operations:

| Method | Arguments and behavior |
|---|---|
| insert | (index, item) inserts one item. |
| remove | (index) removes one item. |
| move | (oldIndex, newIndex) moves an item. |
| push / unshift | (item) adds at the end or beginning. |
| pop / shift | () removes the last or first item. |
| replace | (index, item) replaces one item. |
| merge | (index, items) inserts items at that position in this documented API. |
| resetList | (list) replaces the current list. |
| getKey / getIndex | Convert between a current index and the stable key. |
| sortList | Reorders supplied items to match the Hook's stable-key order, as used by the documented Ant Design integration. In v3.10.0 it also filtered all falsey values; v3.11.0 preserves `0`, `false`, and `''` while still removing `null` and `undefined`. |

The maintained [ahooks note](../../../frontend/libraries/ahooks.md) includes a runnable React example and the current key guidance; this page retains the full method catalog and version boundary omitted from its compact summary.

**Versioned sources / 版本来源:** [ahooks v3.10.0 source](https://github.com/alibaba/hooks/blob/v3.10.0/packages/hooks/src/useDynamicList/index.ts) and [API reference](https://github.com/alibaba/hooks/blob/v3.10.0/packages/hooks/src/useDynamicList/index.en-US.md) confirm that `merge(index, items)` inserts the supplied items at that position; [v3.11.0 source](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useDynamicList/index.ts) and [release notes](https://github.com/alibaba/hooks/releases/tag/v3.11.0) confirm the `sortList` falsey-value fix.
