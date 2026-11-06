# TypeScript 的 Promise 类型能保证什么？

本页原有的状态、构造、then/catch、链式调用、Promise.all、Promise.race 和 async/await 解释，现归入[回调、Promise 与 async 函数怎样组合异步工作？](../../../../frontend/javascript/asynchronous-javascript.md)。

该章保留本页最重要的边界：Promise<T> 与类型注解仅供编译期检查，编译后会擦除，不会在运行时验证服务端 JSON。要把外部值安全交给页面状态，先把它作为 unknown 处理并调用真正的结构校验器。计时器是浏览器或 Node.js 提供的宿主 API，也在 canonical 页面解释其 Promise 包装与取消边界。

> [!info]- 来源
> - TypeScript Handbook：[Erased Types](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types)。
> - Promise 与类型擦除的完整机制：[回调、Promise 与 async 函数怎样组合异步工作？](../../../../frontend/javascript/asynchronous-javascript.md#typescript-的-promise-类型能保证什么)。
