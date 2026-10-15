# Other JavaScript Topics / JavaScript 其他主题

**Key terms / 关键词:** strict mode 严格模式 · floating-point binary64 浮点数 · equality 相等比较 · truthiness 真值转换

This note collects a few distinct language details that are useful when reading or reviewing JavaScript: strict mode, floating-point comparison, equality, and boolean conversion. / 本笔记收录几项阅读或审查 JavaScript 时常用的语言知识：严格模式、浮点比较、相等比较与布尔转换。

## Strict mode / 严格模式

Strict mode changes selected language behaviors, including undeclared assignment, duplicate parameter names, and the default `this` value for a plain function call. ES modules and class bodies are automatically strict. A classic script can opt in with a directive; a function can opt in with a directive at the start of its body. / 严格模式会改变部分语言行为，包括未声明赋值、重复形参，以及普通函数调用时的默认 `this`。ES 模块和 class 函数体自动采用严格模式；经典脚本可在开头添加指令，函数也可在函数体开头添加指令。

```javascript
"use strict";
undeclaredName = 1; // ReferenceError

function inspectThis() {
  return this;
}
inspectThis(); // undefined in strict mode
```

Strict mode does not make `eval` safe, and class or module code is already strict. / 严格模式不会让 `eval` 变安全；class 和模块代码本身已经是严格模式。

Other recognizable differences include rejecting `with`, rejecting legacy octal numeric literals and duplicate parameter names in strict functions, and throwing rather than silently ignoring some writes to non-writable properties. / 其他常见差异包括禁止 `with`、禁止旧式八进制数字字面量和严格函数中的重复形参，以及对某些不可写属性的赋值由静默忽略改为抛错。

## Floating-point comparison / 浮点数比较

JavaScript Number uses IEEE 754 binary64. Many decimal fractions, including 0.1 and 0.2, have no exact finite binary representation, so arithmetic can produce a nearby representable value. The acceptable error depends on the domain and magnitude; choose a domain-specific tolerance instead of a universal epsilon. / JavaScript Number 使用 IEEE 754 binary64。许多十进制小数（如 0.1、0.2）无法用有限二进制位精确表示，因此计算结果可能是邻近的可表示值。可接受误差取决于领域和数值大小，应按具体场景设定容差，而不是套用统一 epsilon。

```javascript
0.1 + 0.2 === 0.3; // false
Math.abs((0.1 + 0.2) - 0.3) < 1e-12; // true for this scale and example
```

For money, use integer minor units when the currency’s rules allow it, or use a decimal arithmetic library with an explicit rounding policy. / 金额计算可在币种规则允许时使用整数最小单位，或使用明确指定舍入策略的十进制运算库。

## Equality: `==`, `===`, and `Object.is` / 相等比较

`===` avoids coercion between different types. `==` follows a set of conversion rules rather than one simple “convert both to the same type” rule; it includes the special `null == undefined` case. Prefer `===` unless coercion is an intentional part of the condition. / `===` 不会在不同类型之间进行隐式转换。`==` 遵循一组转换规则，不能简单概括为“双方都转成同一类型”；其中包括特殊规则 `null == undefined`。除非有意依赖转换规则，否则优先用 `===`。

```javascript
5 == "5";           // true
5 === "5";          // false
null == undefined;  // true
null === undefined; // false
NaN === NaN;        // false
Object.is(NaN, NaN); // true
Object.is(+0, -0);   // false
```

For ordinary values, the deliberate nullish check `value == null` matches `null` or `undefined`; use it only when both are meant to share a branch. `Object.is` differs from strict equality for NaN and signed zero; Map and Set use SameValueZero instead. / 对普通值而言，有意使用的空值判断 `value == null` 会匹配 `null` 或 `undefined`；仅在二者确实走同一分支时使用。`Object.is` 与严格相等对 NaN 和有符号零的处理不同；Map 与 Set 则使用 SameValueZero。

## Boolean conversion / 布尔转换

`Boolean(value)` and `!!value` both apply truthiness conversion. For ordinary values, empty strings, zero, `NaN`, `null`, `undefined`, and `false` are falsy; ordinary objects, including empty arrays and empty objects, are truthy. Choose either spelling according to the surrounding code style; no useful general speed claim follows from the syntax. / `Boolean(value)` 和 `!!value` 都执行真值转换。对普通值而言，空字符串、零、`NaN`、`null`、`undefined` 和 `false` 为假值；包括空数组和空对象在内的普通对象都是真值。按代码风格选择写法，不应据此作普遍性能判断。

Browser compatibility exception: `document.all` has the legacy `[[IsHTMLDDA]]` behavior: it is falsy, `typeof document.all` is `"undefined"`, and it loosely equals both nullish values (`document.all == null`). It is not an ordinary object. / 浏览器兼容性例外：`document.all` 具有历史 `[[IsHTMLDDA]]` 行为，会被判为假值，`typeof document.all` 为 `"undefined"`，且与两种空值都宽松相等（`document.all == null`）。它不是普通对象。

See [ECMAScript Annex B `[[IsHTMLDDA]]`](https://tc39.es/ecma262/2025/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot). / 详见 [ECMAScript 附录 B `[[IsHTMLDDA]]`](https://tc39.es/ecma262/2025/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot)。

When rendering with React, `&&` returns one of its operands rather than a Boolean. If the left operand is `0`, that `0` may be rendered. Use an explicit Boolean condition when the result should be either a component or nothing. / 在 React 中，`&&` 返回操作数之一，而不是布尔值。若左侧为 `0`，结果中的 `0` 可能被渲染。希望结果只能是组件或空内容时，应显式转换为布尔条件。

```jsx
{items.length > 0 && <ItemList items={items} />}
```

See React’s [conditional rendering documentation](https://react.dev/learn/conditional-rendering). / 详见 React 的[条件渲染文档](https://react.dev/learn/conditional-rendering)。

**Interview answer / 面试回答:** Strict mode removes selected legacy behaviors but is not a security sandbox. Number comparisons need domain-specific tolerance because decimal fractions may not be represented exactly. Use `===` by default; use `== null` only when intentionally matching nullish values. Ordinary objects are truthy, with the legacy browser `document.all` exception. / 严格模式移除部分历史行为，但不是安全沙箱。由于十进制小数可能无法精确表示，数值比较应按领域选择容差。默认使用 `===`；只有在有意匹配空值时才使用 `== null`。普通对象都是真值，浏览器历史兼容对象 `document.all` 是例外。

See [ECMAScript equality and coercion](https://tc39.es/ecma262/2025/multipage/abstract-operations.html) for the normative rules. / 相等与类型转换的规范规则见 [ECMAScript 抽象操作](https://tc39.es/ecma262/2025/multipage/abstract-operations.html)。
