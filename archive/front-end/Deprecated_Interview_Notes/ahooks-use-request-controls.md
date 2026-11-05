# How do ahooks useRequest controls and cancellation work? / ahooks useRequest 的控制方法与取消语义是什么？

useRequest runs its Promise-returning service on mount by default; manual mode starts only when run or runAsync is called. run reports failures through the Hook's error callbacks, while runAsync returns a Promise for the caller to handle. cancel ignores the current result and can stop polling or queued work, but it does not abort a request already sent by the transport. / useRequest 默认在挂载时执行返回 Promise 的服务；manual 模式下只有调用 run 或 runAsync 才会开始。run 通过 Hook 的错误回调处理失败，runAsync 则返回 Promise 供调用方处理。cancel 会忽略当前结果并可停止轮询或排队工作，但不会中止已经发出的网络请求。

| Control | Contract in the archived v3.10.0 reference |
|---|---|
| manual | Skip automatic execution; wait for run or runAsync. |
| defaultParams | Parameters for the first automatic execution. |
| data, error, loading, params | Most recent request state; params is the argument array for the latest service call. |
| run(...params) | Start the request and return void; errors go through onError. |
| runAsync(...params) | Start the request and return a Promise; an ignored or superseded request rejects with ahooks CancelledError. |
| refresh / refreshAsync | Repeat the request using the last parameters. |
| mutate(data or updater) | Replace request data or derive it from the previous data. |
| onBefore / onSuccess / onError / onFinally | Observe service start, resolution, failure, and completion; cancelled work may be ignored before onFinally. |
| retryCount / retryInterval | In v3.10.0, configure retry count and delay. |

Call run from an event handler or a real Effect; calling it during render starts a side effect in the wrong lifecycle phase. This cancellation contract is separate from transport abort: pass an AbortSignal into the request service when the network operation itself must stop.

Version boundary: ahooks v2 used debounceInterval and throttleInterval request options; the v3.10.0 reference uses debounceWait and throttleWait. The v3 upgrade guide removed request options such as pagination, loadMore, formatResult, and fetchKey; use the dedicated list Hooks for those cases. Check the installed package version before relying on defaults or removed options.

**Sources checked 2026-10-15:** [ahooks useRequest guide](https://ahooks.js.org/hooks/use-request), [v3.10.0 request option types](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useRequest/src/types.ts), [v3.10.0 Fetch implementation](https://raw.githubusercontent.com/alibaba/hooks/v3.10.0/packages/hooks/src/useRequest/src/Fetch.ts), [v2-to-v3 upgrade guide](https://ahooks.js.org/guide/upgrade/). See the maintained [ahooks note](../../../frontend/libraries/ahooks.md) for the canonical current summary.
