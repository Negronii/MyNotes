# 函数变换如何改变调用过程？

函数可以返回新函数，也可以被包装器改变一次调用的处理流程。本章依次看 rest parameter（剩余参数）、currying（柯里化）与 partial application（部分应用）、composition（组合）、decorator（装饰器）和 memoization（记忆化）。每种变换都从同几个问题入手：参数何时凑齐、`this` 怎样传递、返回值和异常怎样处理；讲到缓存时再讨论缓存键怎么定。

## 返回函数可以捕获状态，也可以不捕获

rest parameter 把前面形参没有接收的实参收集成一个数组；下面的函数只有 `...args`，所以它收集全部实参。显式传入 `undefined` 仍计为一个实参。返回函数只有在后续调用需要读取外层绑定时，才需要 closure（闭包）状态。

~~~javascript
function argumentsLength(...args) {
  return args.length;
}

argumentsLength();            // 0
argumentsLength(undefined);   // 1
argumentsLength({}, null, 3); // 3

function createHelloWorld() {
  return () => "Hello World";
}

const hello = createHelloWorld();
hello({}, null, 42); // "Hello World"；无需捕获状态
~~~

`createHelloWorld` 返回的函数没有声明形参，照样可以接收多余实参；它不读取这些实参，所以不需要 rest parameter。

## 柯里化把实参分到多次调用中提供

严格意义的 currying 把多参数函数变成一串每次只接收一个参数的函数，例如 `sum(a, b, c)` 变为 `curriedSum(a)(b)(c)`。partial application 则先固定一部分实参，返回一个等待其余实参的新函数，不要求每次只接收一个。下面是常见的宽松版 `curry` 辅助函数：每次可以提供一个或多个实参，凑够声明的个数后才调用原函数。“声明的个数”用 `fn.length` 表示，即 arity（元数）。它只适合简单的位置参数函数，不能当作通用的参数契约：`fn.length` 只数第一个带默认值的形参或 rest parameter 之前的形参。占位符和可变参数函数需要另定规则。

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

以 `curriedSum(1)(2)(3)` 为例，收集到的实参变化如下。每一步返回的函数都通过闭包保存当前已收集的实参（下称“前缀”）；由于每次都用 `concat` 生成新数组，从同一前缀分出的多次调用互不影响。

| 这次调用 | 当前收集到的实参 | 是否调用 `sum` | 返回值 |
| --- | --- | --- | --- |
| `curriedSum(1)` | `[1]` | 否，距离 `sum.length = 3` 还差两个 | 等待后续参数的函数 |
| 上一步结果 `(2)` | `[1, 2]` | 否，还差一个 | 新的等待函数 |
| 上一步结果 `(3)` | `[1, 2, 3]` | 是，调用 `sum(1, 2, 3)` | `6` |

不借助 `curry` 也能做部分应用：`const addOneDirect = (b, c) => sum(1, b, c)` 固定了第一个参数，`addOneDirect(2, 3)` 一次接收剩余两个参数，得到 `6`。用 `curry` 时，`const addOne = curriedSum(1)` 既是宽松柯里化的一步，也是一次固定前缀的部分应用：先调用 `addOne(2, 3)` 得到 `6`，再调用 `addOne(4, 5)` 得到 `10`，两次都从同一个 `[1]` 前缀开始。

`fn.length` 的局限会直接改变结果。对于 `function f(a, b = 10) { return a + b; }`，`f.length` 为 `1`，所以 `curry(f)(2)` 立即返回 `12`，不会等待第二次调用。这正是使用 `curry` 前必须先约定参数个数的原因。

上面 `describeParts` 的例子还说明了接收者的处理：这个实现转发的是凑齐参数那次调用的 `this`，不会保存第一次部分调用的 `this`。凑齐时若实参多于声明个数，多余的实参也会一并传给原函数。这些都是该辅助函数自己的约定。

## 组合把上一步输出接到下一步输入

function composition（函数组合）按从右到左的顺序执行：`compose([f, g, h])(x)` 计算 `f(g(h(x)))`。函数列表为空时返回 identity function（恒等函数），也就是原样返回输入。

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

组合 `n` 个单参数函数时，一次正常完成的调用会让每个步骤各执行一次，循环只占用常数额外空间。步骤之间不可交换或带副作用时，执行顺序会影响结果。这个 `compose` 是同步组合：某一步抛错会立即退出循环，把同一个异常传给调用者，左侧剩余步骤不会运行；某一步返回 Promise 时，它会把这个 Promise 对象原样交给下一步，不会等待兑现值。若步骤需要异步串接，应显式选择 Promise 链或 async/await 的组合契约。

循环先把步骤函数取到局部变量 `step`，再以 `step(value)` 形式直接调用；若写成 `functions[i](value)`，`functions` 数组会意外成为接收者。直接调用传入的 `this` 是 `undefined`；被调用的函数若是非严格函数，会按自身规则把它换成全局对象。

## 包装器转发一次调用并附加一种策略

wrapper（包装器）是一个新函数，它调用原函数，并在调用前后附加某种策略。以计时 decorator 为例：它应转发 `this` 和全部实参，并且无论原函数正常返回还是抛错都报告耗时。`finally` 恰好覆盖这两种情况；只要记录耗时的代码本身正常结束，原返回值或异常就会继续向外传递。若 `finally` 自己抛错或执行 `return`，就会覆盖原来的结果。

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

包装器本身是严格函数，因此直接调用时收到的 `undefined` 会原样传给 `fn.apply`；被包装函数仍按自己的严格性决定如何处理它。若包装器是非严格函数，直接调用时 `this` 会先被换成全局对象，`apply` 就无法保留原调用的接收者。这个计时包装器只测同步执行时间。若 `fn` 返回 Promise，`finally` 会在 Promise 对象返回后立即运行，不会计入异步操作完成前的时间；测异步完成耗时需要按 Promise 生命周期另行包装。

用 TypeScript 给这类包装器标注时，显式的 `this` 参数只向类型检查器描述接收者，编译后不会多出一个运行时实参。

这里的“装饰器”指用包装器增加调用策略的设计模式，与 JavaScript 或 TypeScript 的 decorator syntax（`@` 装饰器语法）不是一回事；语法版本的可用位置和行为取决于所用的语言模式，见文末链接的 TypeScript 装饰器章节。

下一个包装器 `once` 让目标函数最多执行一次。它用闭包里的布尔变量 `called` 记录是否调用过，并且在调用目标函数之前就把它设为 `true`，所以第一次调用即使抛错也算用掉了机会。第一次的返回值或异常原样传出，之后的调用都返回 `undefined`。

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

若首次调用抛错，标志已经设好，下次不会重试目标函数；首次返回的 Promise 后来拒绝，也不会重置标志。这与“只允许成功一次”是不同的策略，包装可能失败的操作时要明确选哪一种。

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

## 记忆化在调用前增加缓存键策略

memoization 缓存函数结果，命中缓存时不再调用原函数。因此要先确认两点：相同缓存键确实可以复用同一个结果；跳过原调用的副作用是可以接受的。若函数读取随时间变化的状态，通常还需要失效策略。判断是否命中要看键是否存在，而不是缓存值是否为真值：`0`、`false`、`undefined` 都可能是有效结果。

以 LeetCode 2623 题为例，它只传入有限范围的整数实参：`sum(a, b)` 中 `0 ≤ a, b ≤ 10^5`，`fib(n)` 和 `factorial(n)` 中 `1 ≤ n ≤ 10`。因此该题可以把按顺序排列的整数实参用 `JSON.stringify` 序列化为键；这种编码不适用于任意 JavaScript 数值。`Map.has` 能区分“键不存在”和“缓存值是 `undefined`”。下例的缓存键只包含实参，因此只适用于结果不依赖 `this` 的函数；未命中时代码仍转发 `this`，但这不代表缓存键考虑了它。

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

序列化后的键保留实参顺序，因此 `[2, 3]` 和 `[3, 2]` 是不同键，即使函数返回相同结果。把这种键推广到任意 JavaScript 值时会遇到碰撞：`[NaN]` 与 `[Infinity]` 都会序列化为 `"[null]"`，`[-0]` 会序列化为 `"[0]"`；`[undefined]` 与 `[null]` 也都会序列化为 `"[null]"`。对象身份会丢失；依赖接收者的函数没有把 `this` 放入键；含循环引用的输入会在序列化时抛错。通用的记忆化必须先定义实参、接收者身份、可变输入和失败结果的处理方式，再决定缓存结构。

这个实现先调用 `fn`，再写缓存。若 `fn` 同步抛错，`cache.set` 不执行，下次同键调用仍会重试；若它返回 Promise，Promise 对象会立即入缓存，后续同键调用共享这个对象，即使它后来拒绝也不会自动清除。要把它用于异步请求，必须另外决定拒绝结果是否保留，以及何时过期或重试。

另外，如果只包装 `fib` 的外层调用，原始 `fib` 内部直接发起的递归调用不会经过缓存。要缓存每个子问题，递归调用也必须经过记忆化函数或共享内部缓存。

**相关机制：** [函数 `this` 与绑定](./this-and-function-binding.md) 解释包装器为什么用 `apply` 保留接收者；[作用域与闭包](./scope-and-closure.md) 解释 `once` 和记忆化保留的状态；[Map 与 Set](./map-and-set.md) 说明缓存键相等性和存在性；[TypeScript 装饰器](../typescript/decorators.md) 讲解装饰器语法。

> [!info]- 来源
> - 函数闭包和 length 属性：[ECMAScript Function Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects)（§10.2）、[Function length](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function-instances-length)（§20.2.4.1）。
> - 包装器转发接收者及参数：[ECMAScript Function.prototype.apply](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.apply)；缓存键示例中的存在检查和序列化：[Map.prototype.has](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-map.prototype.has)（§24.1.3.9）、[JSON.stringify](https://tc39.es/ecma262/2026/multipage/structured-data.html#sec-json.stringify)（§25.5.4）。
> - 计时示例的 API：[W3C High Resolution Time performance.now](https://www.w3.org/TR/hr-time-3/#dom-performance-now)；TypeScript 显式 this 参数：[TypeScript Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html#declaring-this-in-a-function)。
> - 特定题目输入契约和作者解法仍保留在 [Memoize](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2623.%20Memoize.md)、[Function Composition](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2629.%20Function%20Composition.md)、[Allow One Function Call](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2666.%20Allow%20One%20Function%20Call.md) 和 [Return Length of Arguments Passed](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2703.%20Return%20Length%20of%20Arguments%20Passed.md)。
