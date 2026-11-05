# Which small ahooks state helper fits a simple UI state? / 简单界面状态适合哪个 ahooks 状态工具？

Use a helper when its state shape matches the UI: useBoolean for explicit boolean actions, useToggle for two values, useMap/useSet for collections, and useCreation for a dependency-based stable value. Use the Hook's action methods to update collections so React receives the intended state update. / 状态形状符合界面需求时再选工具：useBoolean 提供显式布尔操作，useToggle 管理两个值，useMap/useSet 管理集合，useCreation 按依赖复用稳定值。使用 Hook 的操作方法更新集合，以触发预期的 React 状态更新。

| Hook | Return shape and behavior in the archived reference |
|---|---|
| useBoolean(initialValue = false) | [state, { toggle, set, setTrue, setFalse }]. |
| useToggle(defaultValue, reverseValue?) | [state, { toggle, set, setLeft, setRight }]; setRight uses reverseValue or the inverse of defaultValue. |
| useMap(initialEntries?) | [map, { set, get, setAll, remove, reset }]; reset restores initial entries. |
| useSet(initialValues?) | [set, { add, remove, reset }]; reset restores initial values. |
| useCreation(factory, deps) | Reuses a created value until deps change; not a resource-lifecycle primitive or semantic cache guarantee. |

React documents useMemo as a performance optimization rather than a permanent semantic guarantee. Keep side effects out of a useCreation factory. For server-side persistence, see [Browser Storage and Communication](../../../frontend/browser-apis/browser-storage-and-communication.md); for React state ownership, see [Advanced React](../../../frontend/frameworks/advanced-react.md).

**Source checked 2026-10-15:** [ahooks useBoolean](https://ahooks.js.org/hooks/use-boolean), [useToggle](https://ahooks.js.org/hooks/use-toggle), [useMap](https://ahooks.js.org/hooks/use-map), [useSet](https://ahooks.js.org/hooks/use-set), and [useCreation](https://ahooks.js.org/hooks/use-creation).
