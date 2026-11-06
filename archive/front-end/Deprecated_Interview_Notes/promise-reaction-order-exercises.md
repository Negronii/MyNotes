# Promise 处理器的顺序由什么决定？

本归档练习包含三段 Promise 链，关键差异是处理器返回普通值还是已完成的 Promise，以及多条链怎样交错。三段完整程序和在 Node.js v26.11.1 CommonJS 环境中逐段重放的输出，现归入[回调、Promise 与 async 函数怎样组合异步工作？](../../../frontend/javascript/asynchronous-javascript.md#promise-处理器为什么会交错)。

| 归档程序 | 重放输出 |
| --- | --- |
| 第一条链返回 Promise.resolve(4)，与另一条链交错 | 0 1 2 3 4 5 6 |
| 三条各含三段处理器的链 | 0 3 6 1 4 7 2 5 8 |
| 两条链分别返回已完成 Promise | 0 4 2 6 3 7 |

具体结果只对应相应程序和运行上下文；不要从输出推导统一的 tick 数或跨宿主调度顺序。

> [!info]- 来源
> - 原题程序与输出保存在本页对应的归档提交；规范依据：[ECMAScript 2027 Promise objects and jobs](https://tc39.es/ecma262/#sec-promise-objects)。
> - 本页输出于 Node.js v26.11.1 CommonJS 实际重放；浏览器宿主调度见[HTML event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)。
