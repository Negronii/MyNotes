# What do ahooks debounce and throttle Hooks return? / ahooks 的 debounce 与 throttle Hook 返回什么？

Value Hooks return a delayed or rate-limited value; function Hooks return controls for invoking and managing a callback. The defaults and return shape differ, so state them explicitly when porting an example. / 值型 Hook 返回延迟或限频后的值；函数型 Hook 返回调用和管理回调的控制方法。默认值和返回结构各不相同，移植示例时应明确说明。

| Hook | Return and documented defaults in the checked reference |
|---|---|
| useDebounce(value, options) | Debounced value; wait defaults to 1000 ms, leading false, trailing true, maxWait optional. |
| useThrottle(value, options) | Throttled value; wait defaults to 1000 ms, leading true, trailing true. |
| useDebounceFn(fn, options) | { run, cancel, flush }; same timing options as useDebounce. |
| useThrottleFn(fn, options) | { run, cancel, flush }; wait defaults to 1000 ms, leading and trailing true. |

~~~jsx
const { run, cancel, flush } = useDebounceFn(search, {
  wait: 500,
  maxWait: 2000,
});
// Call run from an event; cancel drops a pending call, flush invokes it now.
~~~

Specify wait and edge behavior when timing matters. Debounce and throttle do not imply network cancellation; canceling a pending callback does not stop a request that has already started.

**Source checked 2026-10-15:** [ahooks debounce Hooks](https://ahooks.js.org/hooks/use-debounce/) and [useThrottle](https://ahooks.js.org/hooks/use-throttle). See the maintained [ahooks note](../../../frontend/libraries/ahooks.md) for its short guidance.
