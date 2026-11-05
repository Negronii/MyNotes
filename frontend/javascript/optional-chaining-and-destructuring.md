# How do optional access and destructuring handle missing values? / 可选访问和解构如何处理缺失值？

**Core answer / 核心回答：** Optional chaining stops only on null or undefined, nullish coalescing defaults only for those same values, and destructuring defaults apply only when the extracted value is undefined. These operators preserve meaningful falsy values such as 0, false, and the empty string. / 可选链只在 null 或 undefined 时短路，空值合并也仅对这两种值使用默认值，解构默认值则只在取出的值为 undefined 时生效。这些语法会保留 0、false 和空字符串等有效假值。

## Optional chaining and nullish coalescing / 可选链与空值合并

Optional chaining checks the value immediately before ?. It does not test general falsiness. A missing root identifier still throws, and grouping ends the chain. / 可选链检查 ?. 前紧邻的值，不判断一般假值。根标识符不存在时仍会抛错；括号分组会结束链式短路。

~~~javascript
const user = { profile: null };
user.profile?.name; // undefined

const count = 0;
count?.toFixed(0); // "0"

const key = "value";
const object = { value: 1 };
object?.[key]; // 1

const maybeCall = undefined;
maybeCall?.(); // undefined
~~~

Use ?? when only nullish values should trigger a fallback; use || when every falsy value should. Unparenthesized mixing of ?? with || or && is a syntax error. / 仅 nullish 值应触发默认值时使用 ??；所有假值都应触发时使用 ||。?? 与 || 或 && 不加括号混用会产生语法错误。

~~~javascript
const settings = {};
settings.timeout ?? 1000; // 1000
settings.timeout || 1000; // 1000
0 ?? 1000; // 0
0 || 1000; // 1000
~~~

## Destructuring defaults and rest / 解构默认值与剩余项

Destructuring reads object properties or iterable values into bindings. A default initializer runs only when the extracted value is undefined, not for null, false, zero, or an empty string. Object rest gathers remaining own enumerable properties; array rest consumes the remaining iterator values. / 解构会把对象属性或可迭代对象的值读入绑定。默认值仅在取出值为 undefined 时运行，不适用于 null、false、0 或空字符串。对象剩余项收集其余自有可枚举属性；数组剩余项消费迭代器中剩余的值。

~~~javascript
const user = { name: "Ada", active: false, role: "reader" };
const { name: displayName, active = true, ...extra } = user;
// displayName is "Ada"; active stays false; extra is { role: "reader" }

const [first, , ...tail] = ["a", "b", "c"];
// first is "a"; tail is ["c"]
~~~

Array destructuring depends on the iterable protocol, not numeric property names alone. See [Iterators and Generators / 迭代器与生成器](./iterators-and-generators.md).

## What tagged templates do not do / 带标签模板不会自动做什么

Template literals interpolate expressions into strings. A tagged template instead passes cooked string segments and interpolated values separately to a function. It can implement formatting or domain-specific processing, but it does not sanitize interpolated input automatically. / 模板字符串会把表达式插入字符串。带标签模板会把处理后的字符串片段和插值分别传给函数，可用于格式化或领域特定处理，但不会自动净化插值输入。

The syntax and defaulting rules here complement edition/API support in [Modern JavaScript Features / 现代 JavaScript 特性](./modern-javascript-features.md).
