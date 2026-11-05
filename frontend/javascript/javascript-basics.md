# How do var, let, and const differ? / var、let 与 const 有什么区别？

**Core answer / 核心回答：** Choose a declaration by its scope and whether its binding must be reassigned. var is function-scoped and starts as undefined when its binding is created. let and const are block-scoped and cannot be read before their declaration initializes them. const prevents rebinding; it does not freeze an object. / 根据作用域和是否需要重新绑定来选择声明方式。var 是函数作用域，绑定创建时初值为 undefined。let 和 const 是块级作用域，声明初始化前不可访问。const 禁止重新绑定，但不会冻结对象。

| Behavior / 行为 | var | let | const |
|---|---|---|---|
| Scope / 作用域 | Function scope; top-level behavior depends on script, module, or host / 函数作用域；顶层由脚本、模块或宿主决定 | Lexical block / 词法块 | Lexical block / 词法块 |
| Before declaration / 声明前访问 | Binding exists and is initialized to undefined / 绑定已建立并初始化为 undefined | Temporal Dead Zone; access throws / 暂时性死区，访问会抛错 | Temporal Dead Zone; access throws / 暂时性死区，访问会抛错 |
| Same-scope redeclaration / 同作用域重复声明 | Often allowed for var / 通常允许 | Syntax error / 语法错误 | Syntax error / 语法错误 |
| Reassignment / 重新赋值 | Allowed / 允许 | Allowed / 允许 | Binding cannot be reassigned / 绑定不能重新赋值 |
| Initializer required / 是否必须初始化 | No / 否 | No / 否 | Yes / 是 |

## How scope and initialization differ / 作用域与初始化的差异

A var declaration belongs to the nearest function scope. An if or for block does not create a separate var binding. Its binding is initialized to undefined when the environment is created, but the initializer expression still runs at its written position. / var 属于最近的函数作用域，if 或 for 块不会为它创建独立绑定。环境创建时该绑定会初始化为 undefined，但初始化表达式仍在代码写出的位置执行。

~~~javascript
function example() {
  console.log(value); // undefined
  if (true) {
    var value = 10;
  }
  console.log(value); // 10
}
~~~

let and const belong to the nearest lexical block, including if, switch, loops, and a standalone brace block. Their bindings are established with the block but remain in the Temporal Dead Zone until declaration evaluation. The precise description is not “they are never hoisted”; it is that they cannot be accessed before initialization. / let 和 const 属于最近的词法块，包括 if、switch、循环和独立代码块。进入代码块时绑定已经建立，但在声明执行前仍处于暂时性死区。准确说法不是“它们不会提升”，而是初始化前不能访问。

~~~javascript
{
  // console.log(count); // ReferenceError: still in the TDZ
  let count = 1;
}

const settings = { theme: "light" };
settings.theme = "dark"; // allowed: the object can still mutate
// settings = {};        // TypeError: the binding cannot be reassigned
~~~

At the top level, a classic browser script, an ES module, and a Node module have different environments. In a classic browser script, global var can create a property on the global object, while top-level let and const create global lexical bindings instead. Do not apply that script behavior to modules. / 经典浏览器脚本、ES 模块和 Node 模块的顶层环境不同。在经典浏览器脚本中，全局 var 可在全局对象上创建属性；顶层 let 和 const 则创建全局词法绑定。不要把脚本行为套用到模块。

The declaration and environment rules are defined by the [ECMAScript specification](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html), including [module environment records](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records). For how outer lexical environments form the name-lookup chain and how a closure continues to access a binding, see [Scope and Closure / 作用域与闭包](./scope-and-closure.md).
