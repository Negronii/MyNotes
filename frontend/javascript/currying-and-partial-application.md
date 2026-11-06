# 函数变换如何改变调用过程？

函数可以返回新函数，也可以由包装器改变一次调用的处理流程。本章沿调用过程看 rest parameter（剩余参数）、currying（柯里化）与 partial application（部分应用）、composition（组合）、decorator（装饰器）和 memoization（记忆化）：参数何时齐备、this 如何传递、返回值与异常如何处理；涉及缓存时再定义键策略。

## 返回函数可以捕获状态，也可以不捕获

rest parameter（剩余参数）会把所有实际传入的实参收集到数组中。显式传入 `undefined` 仍计为一个实参。返回函数只有在后续调用需要读取外层绑定时，才需要 closure（闭包）状态。

~~~javascript
function argumentsLength(...args) {
  return args.length;
}

argumentsLength();            // 0
argumentsLength(undefined);   // 1
argumentsLength({}, null, 3); // 3

function createHelloWorld() {
  return (..._args) => "Hello World";
}

const hello = createHelloWorld();
hello({}, null, 42); // "Hello World"；无需捕获状态
~~~

## 柯里化把实参分到多次调用中提供

currying（柯里化）把多参数函数变为一系列调用。partial application（部分应用）先提供一部分实参，再返回等待其余实参的函数。简单位置参数函数可用 `fn.length` 作为 arity（元数）约定，但它不代表通用参数契约：默认参数会截断报告长度，rest parameter 不计入长度。占位符和可变参数函数需要另定规则。

~~~javascript
function curry(fn) {
  "use strict";
  return function curried(...args) {
    if (args.length >= fn.length) return fn.apply(this, args);
    return function (...next) {
      return curried.apply(this, args.concat(next));
    };
  };
}

const sum = (a, b, c) => a + b + c;
const curriedSum = curry(sum);

curriedSum(1)(2)(3); // 6
curriedSum(1, 2)(3); // 6
curriedSum(1, 2, 3); // 6

function describeParts(prefix, period) {
  return this.name + ":" + prefix + "/" + period;
}

const partial = curry(describeParts).call({ name: "first" }, "daily");
partial.call({ name: "final" }, "Q4"); // "final:daily/Q4"
~~~

这个实现会转发补足参数那次调用的接收者，不会保存第一次部分调用的接收者。达到声明元数时，它也会保留多余实参。这些都属于该辅助函数的契约。

## 组合把上一步输出接到下一步输入

function composition（函数组合）从右向左执行：`compose([f, g, h])(x)` 计算 `f(g(h(x)))`。函数列表为空时返回 identity function（恒等函数），也就是原样返回输入。

~~~javascript
function compose(functions) {
  return function (value) {
    for (let i = functions.length - 1; i >= 0; i--) {
      const step = functions[i];
      value = step(value);
    }
    return value;
  };
}

const transform = compose([
  value => value + 1,
  value => value * value,
  value => 2 + value,
]);

transform(4); // 37: 4 -> 6 -> 36 -> 37
compose([])(42); // 42
~~~

对 `n` 个单输入函数，每次组合调用执行 `n` 次，循环仅使用常量额外空间。若操作不可交换或带副作用，执行顺序就很重要。

循环先把步骤函数取到局部变量，再裸调用，避免把 `functions` 数组意外作为接收者。裸调用提供 `undefined` 接收者；被调用函数若为非严格函数，仍会按自身规则将其转换为全局对象。

## 包装器转发一次调用并附加一种策略

wrapper（包装器）是调用原函数并附加策略的新函数。计时 decorator（装饰器）应转发 `this` 和全部实参、返回原函数结果，并在原函数抛错时仍报告耗时。`finally` 会处理正常返回和异常完成两种情况。

~~~javascript
function withTiming(fn) {
  "use strict";
  return function (...args) {
    const started = performance.now();
    try {
      return fn.apply(this, args);
    } finally {
      console.log((fn.name || "operation") + ": " +
        (performance.now() - started) + " ms");
    }
  };
}
~~~

包装器本身是严格函数，因此裸调用时收到的 `undefined` 会原样传给 `fn.apply`；被包装函数仍按自己的严格性决定如何处理它。若包装器在非严格模式下运行，裸调用时 `this` 会先变成全局对象，`apply` 就无法保留原调用的接收者语义。这个计时包装器只测同步执行时间。若 `fn` 返回 Promise，`finally` 会在 Promise 对象返回后立即运行，不会计入异步操作完成前的时间；测异步完成耗时需要按 Promise 生命周期另行包装。

函数装饰器模式指用包装器增加调用策略；它与 JavaScript 或 TypeScript 的 decorator syntax（装饰器语法）不同，后者按各自约定修饰 class 元素。

单次调用包装器保存一个布尔绑定。应在调用目标函数前置位，因此第一次调用即使抛错也会消耗机会。后续调用返回 `undefined`；第一次的结果或异常原样传递。

~~~javascript
function once(fn) {
  "use strict";
  let called = false;
  return function (...args) {
    if (called) return undefined;
    called = true;
    return fn.apply(this, args);
  };
}

let calls = 0;
const onlyOnce = once(function (a, b, c) {
  calls += 1;
  return a + b + c;
});

onlyOnce(1, 2, 3); // 6
onlyOnce(2, 3, 6); // undefined
calls;             // 1
~~~

若首次调用抛错，标志已经置位，因此下次不会重试目标函数。这种策略不同于“只允许一次成功调用”；包装可能失败的操作时应明确选择。

~~~javascript
let attempts = 0;
const failOnce = once(function () {
  attempts += 1;
  throw new Error("failed");
});

try { failOnce(); } catch (error) { error.message; } // "failed"
failOnce(); // undefined
attempts;   // 1
~~~


TypeScript 的显式 `this` 参数只向类型检查器描述接收者，不会增加运行时实参。

## 记忆化在调用前增加缓存键策略

memoization（记忆化）会缓存结果。判断是否命中要检查键是否存在，而不是缓存值是否为真：`0`、`false`、`undefined` 都可能是有效结果。

`LeetCode 2623` 只接受有限整数实参：`sum(a, b)` 中 `0 ≤ a, b ≤ 10^5`，`fib(n)` 和 `factorial(n)` 中 `1 ≤ n ≤ 10`。因此该题可将有序整数实参元组序列化为键；这不是任意 JavaScript number 元组的通用编码。`Map.has` 可以区分键不存在和缓存值为 `undefined`。

~~~javascript
function memoizeNumeric(fn) {
  "use strict";
  const cache = new Map();
  return function (...args) {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  };
}

let evaluations = 0;
const add = memoizeNumeric(function (a, b) {
  evaluations += 1;
  return a + b;
});

[add(2, 2), add(2, 2), add(1, 2), evaluations];
// [4, 4, 3, 2]
~~~

序列化元组保留实参顺序，因此 `[2, 3]` 和 `[3, 2]` 是不同键，即使函数返回相同结果。超出该题的输入契约后会发生碰撞：`[NaN]` 与 `[Infinity]` 都会序列化为 `"[null]"`，`[-0]` 会序列化为 `"[0]"`；`[undefined]` 与 `[null]` 也都会序列化为 `"[null]"`。对象身份会丢失；依赖接收者的函数没有把 `this` 放入键；循环输入会在序列化时抛错。通用记忆化必须先定义实参、接收者身份、可变输入和失败结果的处理方式，再决定缓存结构。

只包装 `fib` 外层调用，不会缓存原始 `fib` 函数内部直接发起的递归调用。要缓存每个子问题，递归调用也必须经过记忆化函数或共享内部缓存。

**相关机制：** [函数 `this` 与绑定](./this-and-function-binding.md) 解释包装器为什么用 `apply` 保留接收者；[作用域与闭包](./scope-and-closure.md) 解释 `once` 和记忆化保留的状态；[Map 与 Set](./map-and-set.md) 说明缓存键相等性和存在性；[TypeScript 装饰器](../typescript/decorators.md) 讲解装饰器语法。


> [!info]- 来源
> - 函数闭包和 length 属性：[ECMAScript Function Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects)（§10.2）、[Function length](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function-instances-length)（§20.2.4.1）。
> - 包装器转发接收者及参数：[ECMAScript Function.prototype.apply](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.apply)；缓存键示例中的存在检查和序列化：[Map.prototype.has](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-map.prototype.has)（§24.1.3.9）、[JSON.stringify](https://tc39.es/ecma262/2026/multipage/structured-data.html#sec-json.stringify)（§25.5.4）。
> - 计时示例的 API：[W3C High Resolution Time performance.now](https://www.w3.org/TR/hr-time-3/#dom-performance-now)；TypeScript 显式 this 参数：[TypeScript Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html#declaring-this-in-a-function)。
> - 特定题目输入契约和作者解法仍保留在 [Memoize](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2623.%20Memoize.md)、[Function Composition](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2629.%20Function%20Composition.md)、[Allow One Function Call](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2666.%20Allow%20One%20Function%20Call.md) 和 [Return Length of Arguments Passed](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2703.%20Return%20Length%20of%20Arguments%20Passed.md)。
