# What does JavaScript strict mode change? / JavaScript 严格模式会改变什么？

**Core answer / 核心回答：** Strict mode turns selected legacy mistakes into errors and changes some function behavior, including the this value of a plain call. ES modules and class bodies are strict automatically. It is not a security sandbox and does not make eval safe. / 严格模式会把部分历史代码中的错误变成异常，并改变一些函数行为，包括普通调用中的 this 值。ES 模块和 class 函数体自动采用严格模式。严格模式不是安全沙箱，也不会让 eval 变安全。

A classic script can opt in with a "use strict" directive at the start of the script; an ordinary function can opt in with a directive at the beginning of its body. An assignment to an undeclared name then throws instead of creating an accidental global. A strict plain function call receives undefined as this. / 经典脚本可在开头用 "use strict" 指令启用严格模式；普通函数也可在函数体开头启用。此时给未声明名称赋值会抛错，而不会意外创建全局变量。严格模式下普通函数调用的 this 是 undefined。

~~~javascript
"use strict";

undeclaredName = 1; // ReferenceError

function inspectThis() {
  return this;
}
inspectThis(); // undefined
~~~

Other recognizable differences include rejecting with, rejecting legacy octal numeric literals and duplicate parameter names in strict functions, and throwing rather than silently ignoring some writes to non-writable properties. Class and module code is already strict, so an extra directive is unnecessary there. / 其他可识别的差异包括禁止 with、旧式八进制数字字面量和严格函数中的重复形参；对部分不可写属性的赋值也会抛错，而非静默忽略。class 和模块代码本来就是严格模式，无需额外指令。

These rules are part of the [ECMAScript strict mode code semantics](https://tc39.es/ecma262/2025/#sec-strict-mode-code). Strict mode changes only specified language behaviors. It does not validate input or impose a security boundary. / 这些规则属于 [ECMAScript 严格模式语义](https://tc39.es/ecma262/2025/#sec-strict-mode-code)。严格模式只改变规范明确列出的语言行为，不会验证输入，也不会建立安全边界。

For the strict-call effect on this, see [Function this and Binding / 函数 this 与绑定](./this-and-function-binding.md). For value conversion, truthiness, and equality, see [JavaScript Types / JavaScript 类型](./javascript-types.md).
