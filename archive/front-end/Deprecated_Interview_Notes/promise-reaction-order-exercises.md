# Promise 处理器的顺序由什么决定？

本归档练习包含三段使用 Promise 链的程序，关键差异是处理器返回普通值还是已履行的 Promise，以及多条链怎样交错。三段完整程序及原归档记录的 Node.js v26.11.1 CommonJS 历史输出，现归入[回调、Promise 与 async 函数怎样组合异步工作？](../../../frontend/javascript/asynchronous-javascript.md#promise-处理器为什么会交错)。本轮另在 Node.js v26.13.0 CommonJS 逐段复跑，输出相同。

| 归档程序 | 重放输出 |
| --- | --- |
| 第一条链的首个处理器返回 Promise.resolve(4)，与另一条处理器链交错 | 0 1 2 3 4 5 6 |
| 三条各含三段处理器的链 | 0 3 6 1 4 7 2 5 8 |
| 两条链的首个处理器各自返回已履行的 Promise | 0 4 2 6 3 7 |

具体结果只对应相应程序和运行上下文；不要从输出推导统一的 tick 数或跨宿主调度顺序。

> [!info]- 来源
> - 原题程序与原始 Node.js v26.11.1 CommonJS 输出保存在本页对应的归档提交；本轮将三段代码在 Node.js v26.13.0 CommonJS 分别重放，输出相同。规范依据为当前 [ECMA-262 / ECMAScript 2027 living draft](https://tc39.es/ecma262/#sec-promise-objects)，Draft ECMA-262 / 2026-11-08，Promise Objects and Jobs，访问于 2026-11-11。
> - 浏览器宿主调度见[HTML event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)。本页具体输出仍限定于各段程序及记录的 Node.js CommonJS 环境。
