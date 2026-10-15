# JavaScript Variable Declarations / JavaScript 变量声明

**Key terms / 关键词:** binding 绑定 · function scope 函数作用域 · block scope 块级作用域 · hoisting 提升 · Temporal Dead Zone 暂时性死区

The main choice is whether a binding may be reassigned and how long it is visible. Prefer `const` when the binding stays fixed, use `let` when it must be reassigned, and recognize `var` when maintaining older code. / 选择声明方式时，重点看绑定是否需要重新赋值以及它的可见范围。绑定不需重新赋值时优先用 `const`，需要重新赋值时用 `let`，维护旧代码时识别 `var` 的作用域行为。

| Behavior / 行为 | `var` | `let` | `const` |
|---|---|---|---|
| Scope / 作用域 | Function scope; top-level context depends on script, module, or host / 函数作用域；顶层由脚本、模块或宿主决定 | Lexical block / 词法块 | Lexical block / 词法块 |
| Before declaration / 声明前访问 | Initialized to `undefined` when its binding is created / 绑定创建时初始化为 `undefined` | TDZ; access throws / TDZ，访问会抛错 | TDZ; access throws / TDZ，访问会抛错 |
| Same-scope redeclaration / 同作用域重复声明 | Often allowed for `var` / 通常允许 | Syntax error / 语法错误 | Syntax error / 语法错误 |
| Reassignment / 重新赋值 | Allowed / 允许 | Allowed / 允许 | Binding cannot be reassigned / 绑定不能重新赋值 |
| Initializer required / 是否必须初始化 | No / 否 | No / 否 | Yes / 是 |

## `var`: function scope / 函数作用域

A `var` declaration belongs to the nearest function scope, or the top-level variable environment provided by the current script, module, or host wrapper; a surrounding `if` or `for` block does not create a new `var` scope. The binding exists before the declaration executes and starts as `undefined`; its initializer still runs at its written position. / `var` 属于最近的函数作用域；若代码位于顶层，则属于当前脚本、模块或宿主包装器提供的顶层变量环境。外层的 `if` 或 `for` 块不会创建新的 `var` 作用域。绑定在声明执行前已经存在，初值为 `undefined`；初始化表达式仍在代码写出的位置执行。

```javascript
function example() {
  console.log(value); // undefined
  if (true) {
    var value = 10;
  }
  console.log(value); // 10
}
```

## `let` and `const`: lexical scope / 词法作用域

A lexical binding is in the Temporal Dead Zone from entry into its scope until its declaration is evaluated. The binding is not usable during that interval. `const` also requires an initializer and prevents reassignment of the binding; it does not freeze an object stored in that binding. / 词法绑定从进入作用域开始，到声明执行之前处于暂时性死区（TDZ），这段时间不能访问。`const` 还要求声明时初始化，并禁止重新赋值绑定；它不会冻结绑定所指向的对象。

```javascript
const settings = { theme: "light" };
settings.theme = "dark"; // allowed: the object is mutable
// settings = {};        // TypeError: the binding cannot be reassigned

{
  // console.log(count); // ReferenceError: still in the TDZ
  let count = 1;
}
```

At the top level, script, module, and host environments differ. In a classic browser script, a global `var` can create a property on the global object, while `let` and `const` create global lexical bindings instead. Do not assume this browser-script behavior for ES modules or Node modules. / 顶层行为会因脚本、模块和宿主环境而异。在浏览器经典脚本中，全局 `var` 可以在全局对象上创建属性，而 `let`、`const` 创建的是全局词法绑定。不要把该浏览器脚本行为直接套用到 ES 模块或 Node 模块。

**Interview answer / 面试回答:** `var` is function-scoped and initialized to `undefined` when its binding is created. `let` and `const` are block-scoped and inaccessible in the TDZ before declaration evaluation. `const` protects the binding from reassignment, not the referenced object from mutation. / `var` 是函数作用域，绑定创建时会初始化为 `undefined`。`let` 和 `const` 是块级词法作用域，声明执行前处于 TDZ。 `const` 保护的是绑定，不能阻止对象内容被修改。

See [ECMAScript declarations and environments](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html), including [Module Environment Records](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records), for the language rules. / 变量声明与环境记录规则见 [ECMAScript 声明和执行上下文规范](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html)，包括[模块环境记录](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records)。

Related: [Scope and Closure / 作用域与闭包](./scope-and-closure.md).
