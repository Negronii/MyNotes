# How do edition and runtime support affect JavaScript feature use? / 语言版本与运行时支持如何影响 JavaScript 特性的使用？

**Core answer / 核心回答：** A feature’s ECMAScript edition and support in the target runtime are separate facts. Syntax must parse in the target environment or be transformed; APIs also need runtime support or a suitable polyfill. Check the actual browsers, Node versions, and build target before relying on a feature. / 特性属于哪个 ECMAScript 版本，与目标运行时是否支持是两件事。语法必须能被目标环境解析或经过转换；API 也需要运行时实现或合适的 polyfill。依赖某项特性前要检查实际浏览器、Node 版本和构建目标。

## Selected APIs and edition boundaries / 部分 API 与版本边界

| Feature / 特性 | Edition or source / 版本或来源 | Boundary / 边界 |
|---|---|---|
| Object.keys | ES5 | Own enumerable string keys / 自有可枚举字符串键 |
| Object.assign, Object.is | ES2015 | Object.assign mutates its target; Object.is uses SameValue / Object.assign 会修改目标；Object.is 使用 SameValue |
| Object.values, Object.entries | ES2017 | Own enumerable string-keyed values or pairs / 自有可枚举字符串键的值或键值对 |
| Array.from, Array.of | ES2015 | Iterable/array-like conversion or argument list / 可迭代或类数组转换，或参数列表建数组 |
| Promise.all, Promise.race | ES2015 | Outcome semantics and cancellation limits: see [Asynchronous JavaScript / 异步 JavaScript](./asynchronous-javascript.md) / 完成条件和不取消其他操作见异步页 |
| Promise.allSettled | ES2020 | See [Asynchronous JavaScript / 异步 JavaScript](./asynchronous-javascript.md) / 见异步页的 Promise 比较表 |
| Promise.any | ES2021 | See [Asynchronous JavaScript / 异步 JavaScript](./asynchronous-javascript.md) / 见异步页的 Promise 比较表 |
| globalThis | ES2020 | Current realm’s global object; host-specific properties differ / 当前 realm 的全局对象；宿主属性不同 |
| Array.prototype.at | ES2022 | Supports negative offsets from the end / 支持从末尾反向计数 |
| Object.hasOwn | ES2022 | Own-property test works with null-prototype objects and overridden hasOwnProperty / 可用于 null 原型对象和被覆盖的 hasOwnProperty |
| structuredClone | Host API, not an ECMAScript edition feature / 宿主 API，不属于 ECMAScript 版本特性 | Structured-cloneable values, cycles, Map, Set, Date; not functions or custom class prototypes / 支持结构化克隆值、循环引用、Map、Set、Date；不支持函数或自定义类原型 |

The edition number does not establish that a particular browser or runtime build implements the feature. Syntax transforms also do not automatically supply missing built-in APIs. Verify the configured target and run checks in the actual runtime set. / 版本号并不能证明特定浏览器或运行时构建实现了该特性。语法转换也不会自动补齐缺少的内置 API。应核对配置目标，并在实际运行环境中检查。

~~~javascript
const values = ["first", "last"];
values.at(-1); // "last"

const options = Object.create(null);
options.enabled = false;
Object.hasOwn(options, "enabled"); // true
~~~

structuredClone is exposed by browsers and current Node releases, but it does not preserve custom class prototypes or clone functions; unsupported values can throw DataCloneError. Do not assume it is faster than another copying method. See the [HTML structured clone algorithm](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning) and [Node global API](https://nodejs.org/api/globals.html#structuredclonevalue-options). Sources checked 2026-10-15. / structuredClone 可由浏览器和当前 Node 版本使用，但不会保留自定义类原型或复制函数；不支持的值可能抛出 DataCloneError。不要假设它必然比其他复制方法快。见 [HTML 结构化克隆算法](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning) 与 [Node 全局 API](https://nodejs.org/api/globals.html#structuredclonevalue-options)。来源核对日期：2026-10-15。

For edition-specific language features, see the [ECMAScript 2025 specification](https://tc39.es/ecma262/2025/). / 版本相关语言特性见 [ECMAScript 2025 规范](https://tc39.es/ecma262/2025/)。

**See also:** [Optional Chaining and Destructuring / 可选链与解构](./javascript-types.md#%E7%BC%BA%E5%A4%B1%E5%B1%9E%E6%80%A7%E9%BB%98%E8%AE%A4%E5%80%BC%E4%B8%8E%E8%A7%A3%E6%9E%84) explains syntax semantics; [Modules and Host Boundaries / 模块与宿主边界](./modules-and-host-boundaries.md) explains ESM and CommonJS; [Object helpers / 对象辅助方法](./javascript-types.md#%E6%9E%9A%E4%B8%BE%E4%B8%8E%E5%A4%8D%E5%88%B6%E5%B1%9E%E6%80%A7%E6%97%B6%EF%BC%8C%E5%85%88%E7%9C%8B%20API%20%E9%80%89%E4%B8%AD%E4%BA%86%E4%BB%80%E4%B9%88) and [Array helpers / 数组辅助方法](./arrays.md#%E4%BB%8E%E8%BF%AD%E4%BB%A3%E5%99%A8%E6%88%96%E7%B1%BB%E6%95%B0%E7%BB%84%E8%BE%93%E5%85%A5%E5%88%9B%E5%BB%BA%E6%95%B0%E7%BB%84) covers property-copying and enumeration behavior.
