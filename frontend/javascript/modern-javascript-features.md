# Modern JavaScript Features / 现代 JavaScript 特性

**Key terms / 关键词:** optional chaining 可选链 · nullish coalescing 空值合并 · promise combinator Promise 组合方法 · structured clone 结构化克隆 · module 模块

This is a selected reference to commonly used standardized features, not a complete catalog of “modern JavaScript.” A feature’s edition and its runtime availability are separate questions: check the runtime or build target before relying on it. / 这里选列常用的标准化特性，并非“现代 JavaScript”完整目录。特性属于哪个版本与目标运行时是否支持是两个问题；依赖某项特性前应检查运行时或构建目标。

## Optional chaining and nullish coalescing / 可选链与空值合并

Optional chaining stops only when the value immediately before the chain is `null` or `undefined`; it does not test general falsiness. A missing root identifier still throws, and grouping ends a chain. / 可选链只在链上前一个值为 `null` 或 `undefined` 时短路，不判断一般假值。根标识符不存在时仍会抛错，括号分组也会结束链式短路。

```javascript
const user = { profile: null };
user.profile?.name; // undefined
const count = 0;
count?.toFixed(0); // "0"

const key = "value";
const object = { value: 1 };
object?.[key]; // 1
const maybeCall = undefined;
maybeCall?.(); // undefined

const settings = {};
settings.timeout ?? 1000; // 1000
settings.timeout || 1000; // 1000
0 ?? 1000; // 0
0 || 1000; // 1000
```

Use `??` when only nullish values should trigger a fallback; use `||` when all falsy values should. Parenthesize when mixing `??` with `||` or `&&`; unparenthesized mixing is a syntax error. / 只有 nullish 值应触发默认值时用 `??`；所有假值都应触发时用 `||`。`??` 与 `||` 或 `&&` 混用时应加括号，不加括号会产生语法错误。

## Destructuring, rest, and template literals / 解构、剩余项与模板字符串

Destructuring and template literals were standardized in ES2015; object rest/spread was standardized in ES2018. Destructuring reads properties or iterable values into bindings. Defaults apply when the extracted value is `undefined`, not for every falsy value. Object rest gathers remaining own enumerable properties; array rest consumes the remaining iterable values. / 解构和模板字符串属于 ES2015；对象剩余项/展开属于 ES2018。解构把属性或可迭代值读入绑定。默认值只在取出的值为 `undefined` 时生效，不适用于所有假值。对象剩余项收集其余自有可枚举属性；数组剩余项消费迭代器中的剩余值。

```javascript
const { name: displayName, active = true, ...extra } = user;
const [first, , ...tail] = ["a", "b", "c"];
const greeting = `Hello, ${displayName}!`
```

Tagged templates pass cooked string segments and interpolated values separately. They are useful for formatting or domain-specific processing; they do not sanitize input automatically. / 带标签模板会分别传入处理后的字符串片段和插值。它可用于格式化或特定领域处理，但不会自动净化输入。

## Promise combinators / Promise 组合方法

| Method / 方法 | Edition / 版本 | Fulfillment / 成功条件 | Rejection / 失败条件 |
|---|---|---|---|
| `Promise.all` | ES2015 | Every input fulfills / 全部成功 | An input rejects / 某项失败 |
| `Promise.allSettled` | ES2020 | Every input settles; returns each outcome / 全部结束并返回每项结果 | Normally does not reject for an input rejection / 不因某项输入拒绝而拒绝 |
| `Promise.any` | ES2021 | First input fulfills / 首个成功项 | All inputs reject; rejects with `AggregateError` / 全部失败时以 `AggregateError` 拒绝 |
| `Promise.race` | ES2015 | First settlement is fulfillment / 首个完成项成功 | First settlement is rejection / 首个完成项拒绝 |

The specification installs both fulfillment and rejection reactions for each input in [`PerformPromiseRace`](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace). / 规范中的 [`PerformPromiseRace`](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-performpromiserace) 会为每项输入同时安装成功和拒绝处理器。

`all`, `any`, and `race` settle the returned promise early when their condition is met, but do not cancel the other work. Passing promises usually starts their underlying operations before the combinator is called. Use an explicit cancellation mechanism, such as AbortController when supported by the API, if losing work should stop. / 当满足条件时，`all`、`any` 和 `race` 会提前完成返回的 Promise，但不会取消其他任务。传入的 Promise 通常已在调用组合方法前启动底层操作。若需停止未获胜的任务，应使用 API 支持的取消机制，例如 AbortController。

## Selected APIs and editions / 部分 API 与版本

- `globalThis` — ES2020 access to the current realm’s global object; its host-specific properties differ. / ES2020 提供当前 realm 的全局对象入口；其属性因宿主环境而异。
- `Array.prototype.at(index)` — ES2022 indexing with negative offsets from the end. / ES2022 索引方法，支持从末尾反向计数。
- `Object.hasOwn(object, key)` — ES2022 own-property test that works with null-prototype objects and overridden `hasOwnProperty`. / ES2022 自有属性判断，可用于 null 原型对象或覆盖了 `hasOwnProperty` 的对象。
- `structuredClone(value)` — a host API, not an ECMAScript edition feature. Browsers and current Node releases expose it ([Node global API](https://nodejs.org/api/globals.html#structuredclonevalue-options)). It clones structured-cloneable values and supports cycles and built-in data such as Map, Set, and Date. It does not preserve custom class prototypes or clone functions; unsupported values can throw `DataCloneError`. Do not assume it is faster than another method. / 这是宿主 API，不属于某个 ECMAScript 版本特性；浏览器和当前 Node 版本均提供该方法（见 [Node 全局 API](https://nodejs.org/api/globals.html#structuredclonevalue-options)）。它可复制结构化克隆支持的值，支持循环引用以及 Map、Set、Date 等内置数据；不会保留自定义类原型，也不能克隆函数；不支持的值可能抛出 `DataCloneError`。不要假设它必然比其他方法快。
- `Object.assign` and `Object.is` are ES2015. `Object.keys` is ES5; `Object.values` and `Object.entries` are ES2017. / `Object.assign` 和 `Object.is` 属于 ES2015。`Object.keys` 属于 ES5；`Object.values` 和 `Object.entries` 属于 ES2017。

```javascript
const values = ["first", "last"];
values.at(-1); // "last"

const options = Object.create(null);
options.enabled = false;
Object.hasOwn(options, "enabled"); // true
```

## Modules: language and host boundaries / 模块：语言与宿主边界

ECMAScript modules are part of the language: static `import` / `export`, module-scoped bindings, strict mode, and top-level `this === undefined`. Top-level await was standardized in ES2022. Dynamic `import()` returns a Promise and is supported by both Node module systems. CommonJS (`require`, `module.exports`) is Node’s module wrapper, not ECMAScript module syntax. / ECMAScript 模块属于语言规范：使用静态 `import` / `export`，绑定具有模块作用域，自动采用严格模式，顶层 `this === undefined`。顶层 await 于 ES2022 标准化。动态 `import()` 返回 Promise，Node 两种模块系统都可使用。CommonJS（`require`、`module.exports`）是 Node 的模块包装机制，不是 ECMAScript 模块语法。

These two `.mjs` files show static imports/exports and a dynamic import of the same module. / 以下两个 `.mjs` 文件演示静态导入/导出，以及对同一模块进行动态导入。

```javascript
// features.mjs
export const featureName = "search";
export default function createFeature() {
  return featureName;
}
```

```javascript
// app.mjs
import createFeature, { featureName } from "./features.mjs";
export { featureName };

createFeature(); // "search"
import("./features.mjs").then(({ featureName }) => featureName);
```

| Concern / 维度 | ECMAScript module / ES 模块 | Node CommonJS / Node CommonJS |
|---|---|---|
| Static syntax / 静态语法 | `import`, `export` | `require()`, `module.exports` |
| Top-level await / 顶层 await | Supported / 支持 | Not supported in a CJS wrapper / CJS 包装器中不支持 |
| Top-level `this` / 顶层 `this` | `undefined` | Node wrapper’s `exports` value / Node 包装器的 `exports` 值 |
| Tree shaking / Tree shaking | Depends on bundler and package metadata / 取决于打包器和包元数据 | Not guaranteed by the format / 模块格式不保证 |

A bundler may analyze ESM imports for tree shaking, but ESM syntax alone does not guarantee code removal. Node decides whether a file is ESM or CJS using extensions, package settings, or explicit input flags; browser module loading follows browser rules. / 打包器可以分析 ESM 导入以执行 tree shaking，但仅使用 ESM 语法不保证代码一定被移除。Node 会根据扩展名、包设置或显式输入参数确定文件属于 ESM 还是 CJS；浏览器模块加载则遵循浏览器规则。

**Interview answer / 面试回答:** Optional chaining checks nullish values, while `??` preserves valid falsy values. Promise combinators aggregate outcomes but do not cancel work. ESM is standardized JavaScript syntax; CommonJS is a Node module system, and bundler behavior such as tree shaking depends on tooling. / 可选链检查 nullish 值，`??` 会保留有效的假值。Promise 组合方法聚合结果，但不会取消任务。ESM 是标准 JavaScript 模块语法；CommonJS 是 Node 模块系统，tree shaking 等行为取决于工具链。

See the [ECMAScript language specification](https://tc39.es/ecma262/2025/) for edition-specific features and the [HTML structured clone algorithm](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning) for the host API. / 版本相关语言特性见 [ECMAScript 语言规范](https://tc39.es/ecma262/2025/)；宿主结构化克隆 API 见 [HTML 结构化克隆算法](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning)。

Related: [Object and Array Methods / 对象与数组方法](./es6-new-methods.md); [Asynchronous JavaScript / 异步 JavaScript](./asynchronous-javascript.md).
