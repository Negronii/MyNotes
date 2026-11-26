# 怎样包装一个函数而不弄丢参数、this 和结果？

wrapper（包装器）是一个新函数：它调用原函数，并在调用前后加一种策略，比如固定部分参数、计时、只执行一次、缓存结果、推迟执行。上一章讲了闭包保存跨调用的状态、`this` 由调用形式提供；本章把两者用到包装器上。

每个包装器都要回答四个问题：实参何时凑齐，`this` 怎样转给原函数，返回值和异常怎样传出，闭包里存什么状态。本章按这四个问题依次看 currying（柯里化）、composition（组合）、计时包装、`once`、memoization（记忆化），最后是 debounce（防抖）和 throttle（节流）。

## rest 参数收集实参

rest parameter（剩余参数）把前面形参没接住的实参收集成数组。下面的函数只有 `...args`，所以收集全部实参；显式传入的 `undefined` 也算一个。

~~~javascript
function argumentsLength(...args) {
  return args.length;
}

argumentsLength();            // 0
argumentsLength(undefined);   // 1
argumentsLength({}, null, 3); // 3
~~~

返回的函数只有在以后要读外层绑定时才需要闭包状态。`createHelloWorld` 返回的函数不声明形参也能接收多余实参；它既不读实参也不读外层变量，所以既不需要 rest 参数也不需要闭包。

~~~javascript
function createHelloWorld() {
  return () => "Hello World";
}

createHelloWorld()({}, null, 42); // "Hello World"
~~~

## 柯里化与部分应用：实参分几次给

严格意义的 currying 把多参数函数变成一串单参数函数：`sum(a, b, c)` 变成 `curriedSum(a)(b)(c)`。partial application（部分应用）先固定一部分实参，返回等待其余实参的函数，不要求每次只给一个。

下面是常见的宽松版 `curry`：每次可以给一个或多个实参，凑够声明的个数才调用原函数。“声明的个数”取 `fn.length`，即 arity（元数）。

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
~~~

以 `curriedSum(1)(2)(3)` 为例，每一步返回的函数都用闭包保存已收集的实参（下称“前缀”）：

| 这次调用 | 已收集的实参 | 调用 `sum` 吗 | 返回值 |
| --- | --- | --- | --- |
| `curriedSum(1)` | `[1]` | 否，`sum.length` 是 `3`，还差两个 | 等待函数 |
| 上一步结果 `(2)` | `[1, 2]` | 否，还差一个 | 新的等待函数 |
| 上一步结果 `(3)` | `[1, 2, 3]` | 是，调用 `sum(1, 2, 3)` | `6` |

每次都用 `concat` 生成新数组，所以从同一前缀分出的多次调用互不影响：`const addOne = curriedSum(1)` 之后，`addOne(2, 3)` 得 `6`，`addOne(4, 5)` 得 `10`，两次都从 `[1]` 开始。这一步既是宽松柯里化，也是固定前缀的部分应用。不借助 `curry` 也能部分应用：`(b, c) => sum(1, b, c)`。

> [!warning] `fn.length` 不是可靠的参数契约
> `fn.length` 只数第一个带默认值的形参或 rest 参数**之前**的形参。`function f(a, b = 10) { return a + b; }` 的 `length` 是 `1`，所以 `curry(f)(2)` 立刻返回 `12`，不会等第二次调用。用 `curry` 之前先约定参数个数；占位符和可变参数函数要另定规则。

这个实现转发的是**凑齐参数那次**调用的 `this`，不保存早先部分调用的 `this`；凑齐时多出的实参也一并传给原函数。这些是该辅助函数自己的约定：

~~~javascript
function describeParts(prefix, period) {
  return this.name + ":" + prefix + "/" + period;
}

const partial = curry(describeParts).call({ name: "first" }, "daily");
partial.call({ name: "final" }, "May"); // "final:daily/May"
~~~

## 组合：上一步的输出接到下一步的输入

function composition（函数组合）按从右到左执行：`compose([f, g, h])(x)` 计算 `f(g(h(x)))`。列表为空时返回 identity function（恒等函数），原样返回输入。

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

transform(4);    // 37：4 → 6 → 36 → 37
compose([])(42); // 42
~~~

几个容易忽略的点：

- **接收者。** 循环先把步骤取到局部变量 `step` 再调用；若写成 `functions[i](value)`，数组 `functions` 会成为接收者。直接调用传入的 `this` 是 `undefined`，非严格步骤会按自己的规则换成全局对象。
- **异常。** 这是同步组合：某一步抛错立即退出循环，异常原样传给调用者，左侧剩余步骤不运行。
- **Promise。** 某一步返回 Promise 时，它把 Promise 对象原样交给下一步，不等待兑现值。步骤需要异步串接时，要显式选 Promise 链或 async/await 的组合方式。
- **成本。** 组合 `n` 个单参数函数，一次调用让每步各执行一次，额外空间是常数。步骤带副作用或不可交换时，顺序会改变结果。

## 包装通则：用 apply 转发，用 finally 收尾

计时包装器展示了包装器的基本写法：转发 `this` 和全部实参；无论原函数正常返回还是抛错，都报告耗时。

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

- **`fn.apply(this, args)` 转发接收者和实参。** 包装器本身是严格函数，所以被直接调用时收到的 `undefined` 会原样交给 `fn`，再由 `fn` 按自己的模式处理。若包装器是非严格函数，`undefined` 会先被换成全局对象，`apply` 就保不住原调用的接收者。
- **`finally` 覆盖返回和抛错两条路径。** 只要 `finally` 里的代码正常结束，原返回值或异常就继续向外传。`finally` 自己抛错或执行 `return`，会覆盖原结果。
- **只测同步时间。** `fn` 返回 Promise 时，`finally` 在 Promise 对象返回后就运行，不计异步操作完成前的时间；测完成耗时要按 Promise 的生命周期另写包装。

用 TypeScript 给包装器标注时，显式的 `this` 参数只向类型检查器描述接收者，编译后不多出运行时实参，见[泛型和工具类型怎样从已有类型推出新类型？](./typescript-generics-and-utility-types.md)。这里的“装饰”指用包装器加调用策略的设计模式，和 `@` 装饰器语法不是一回事，后者见[TypeScript 的两种装饰器模式有什么不同？](./typescript-decorators.md)。

## once：最多执行一次，失败也算一次

`once` 用闭包里的布尔值 `called` 记录是否调用过，并在调用目标**之前**就设为 `true`。第一次的返回值或异常原样传出，之后的调用都返回 `undefined`。

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

因为标志先于调用设好，首次调用抛错也算用掉了机会，不会重试；首次返回的 Promise 后来拒绝，同样不会重置标志：

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

“最多尝试一次”和“只允许成功一次”是两种策略。包装可能失败的操作时，先决定要哪一种。

## memoize：先定义缓存键和失败结果

memoization 缓存函数结果，命中时不再调用原函数。用之前先确认两点：相同的键确实可以复用同一个结果；跳过原调用的副作用可以接受。函数读取随时间变化的状态时，还需要失效策略。判断命中要看键**是否存在**，不看缓存值真假：`0`、`false`、`undefined` 都可能是有效结果，`Map.has` 能区分“没有这个键”和“缓存值是 `undefined`”。

下例假设输入契约是有限范围的整数实参（如 `0 ≤ a, b ≤ 10^5`），这时按顺序把实参用 `JSON.stringify` 序列化成键是安全的。键只含实参，所以只适用于结果不依赖 `this` 的函数；未命中时代码照样转发 `this`，但键并没有考虑它。

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

把这种键推广到任意值就会出错：

| 输入 | 序列化结果 | 问题 |
| --- | --- | --- |
| `[NaN]`、`[Infinity]`、`[undefined]`、`[null]` | 都是 `"[null]"` | 不同输入碰撞成同一键 |
| `[-0]` | `"[0]"` | `-0` 与 `0` 不再可分 |
| 对象实参 | 按当前内容序列化 | 对象身份丢失，之后修改对象也不会让旧键失效 |
| 含循环引用的对象 | 抛 `TypeError` | 包装器在调用原函数前就失败 |

`[2, 3]` 和 `[3, 2]` 是不同键，即使结果相同。通用的记忆化必须先定义实参怎样比较、接收者身份算不算、可变输入怎么办、失败结果存不存，再选缓存结构。“相同”有哪几种定义，见[JavaScript 的值有哪些类型，“相等”又有几种？](./values-types-and-equality.md)。

失败语义来自代码顺序：先调用 `fn`，再写缓存。

- `fn` 同步抛错时 `cache.set` 不执行，下次同键调用会重试。
- `fn` 返回 Promise 时，Promise 对象立即入缓存，后续同键调用共享它；它后来拒绝也不会自动清除。用于异步请求时，要另定拒绝结果是否保留、何时过期或重试。
- 只包装 `fib` 的外层调用时，原始 `fib` 内部的递归调用不经过缓存。要缓存每个子问题，递归调用也得走记忆化后的函数或共享缓存。

## debounce 与 throttle：闭包里的计时状态

沿用主线一的报表页，本章给它加一个搜索框：用户停止输入后再按搜索词请求报表列表。排序按钮则不该延迟，点击就立即导航。

debounce（防抖）在一串连续调用停下、静默一段时间后，只执行最后一次；throttle（节流）限制执行频率。执行时机可以在 leading edge（首沿，一串调用的开头）、trailing edge（尾沿，一串调用结束后），或两者都要。两者都由返回的包装函数用闭包保存状态，区别在存什么、何时更新。

### 尾沿防抖与首沿节流的实现

示例中 `wait` 和 `interval` 都是正整数毫秒数。

~~~javascript
function debounce(fn, wait) {
  let timer;

  function debounced(...args) {
    const receiver = this;
    clearTimeout(timer);
    timer = setTimeout(() => {
      timer = undefined;
      fn.apply(receiver, args);
    }, wait);
  }

  debounced.cancel = function () {
    clearTimeout(timer);
    timer = undefined;
  };

  return debounced;
}

function throttleLeading(fn, interval) {
  let lastCallAt = null;

  return function (...args) {
    const now = performance.now();
    if (lastCallAt !== null && now - lastCallAt < interval) return;
    lastCallAt = now;
    return fn.apply(this, args);
  };
}
~~~

- **防抖存一个 `timer`。** 它属于某一次 `debounce(fn, wait)` 调用，被返回的 `debounced` 在多次调用间共享。每次调用 `debounced` 都新建本次的 `args` 和 `receiver`；旧计时器被清除，新计时器的回调读到的就是本次的接收者和参数，所以静默期结束时只执行最后一组输入。
- **节流存上次通过的时刻 `lastCallAt`。** 它用 `performance.now()` 这个单调时钟计算间隔，系统校时不影响差值。初值 `null` 表示“还没执行过”，即使时钟读数恰好是 `0`，第一次调用也会通过；差值正好等于 `interval` 时也放行。
- **节流先写 `lastCallAt` 再调用目标。** 目标同步重入时看到的是这次调用的时刻：未过间隔就被挡下；目标同步耗时已达到间隔才重入，则会通过。`interval` 为 `0` 时不限制同步重入，所以本节只讨论正间隔。

### 同一条时间线上两者怎样不同

下表是合成时间线：防抖等待和节流间隔都是 `100ms`；`debouncedSearch`、`throttledSearch` 分别包装同一个搜索函数，该函数记下接收者（`pageA`、`pageB`、`pageC` 代表不同接收者）和搜索词。每行把相同输入同时交给两个包装器。时刻按理想时钟推演，不是实测。

| 理想时刻 | 防抖包装器 | 首沿节流包装器 |
| ---: | --- | --- |
| `0ms` | 收到 `pageA, "A"`：设 `100ms` 计时 | 收到 `pageA, "A"`：立即执行，记下 `0` |
| `40ms` | 收到 `pageB, "B"`：清掉旧计时，重新等 `100ms` | 收到 `pageB, "B"`：丢弃，距上次通过 `40ms` |
| `110ms` | 收到 `pageC, "C"`：再次清掉旧计时，重新等 `100ms` | 收到 `pageC, "C"`：执行，距上次通过 `110ms` |
| `210ms` 起 | 无新调用时，以 `pageC, "C"` 执行 | 无新调用 |

防抖只执行了最后一次；首沿节流执行了第一次和间隔外的一次，丢掉了中间的 B。

### leading、trailing 与 maxWait

两种包装都可以扩展成可配置的首沿、尾沿：

- **只要尾沿**：一串调用结束、静默 `wait` 后执行最后一次输入。搜索框通常这样用。
- **只要首沿**：一串调用的第一次立即执行，之后在窗口内的调用被忽略。按钮防连点通常这样用。
- **首沿和尾沿都要**：第一次立即执行；窗口内若又有调用，窗口结束时再执行最后那次。窗口内只有一次调用时，尾沿不会重复执行它。

只用尾沿防抖时，用户一直输入就永远不触发。maxWait（最大等待时间）给出上限：从这串调用开始（或上次执行）算起，等满 `maxWait` 就先执行当时最新的输入，不再等静默。节流可以看成 `maxWait` 等于 `wait` 的防抖：连续调用期间每隔 `wait` 至少执行一次。

### cancel 和 flush 只管还没执行的调用

`cancel()` 撤销尚未执行的那次调用；`flush()`（若实现提供）让它立即执行。两者都不触及**已经执行**的调用。如果那次调用已经发出 `fetch`，`cancel` 撤不回它：

- 想让旧响应不写回界面，要给每次请求一个身份（如递增的请求代次），响应回来时核对，见[服务端数据怎样缓存、刷新和乐观更新，迟到的响应又归谁？](../ui-state/server-state-and-optimistic-updates.md)。
- 想停止浏览器传输，要把 `AbortController` 的 `signal` 交给 `fetch`，在需要时调用 `abort()`；这只结束客户端这一侧，撤不回服务端已开始的工作，见[取消、超时和并发上限各自停得住什么？](./cancellation-timeouts-and-concurrency.md)。

控件销毁时，移除事件监听器并调用 `cancel()`。

两个使用前提也由闭包状态决定：

- **同一组件要一直复用同一个包装实例。** 每次渲染都新建 `debounce(...)`，旧实例里的计时器就成了孤儿，每个实例只见过一次调用，防抖失效。
- **不要在每次输入时 `cancel`。** 那会清掉 `maxWait` 的计时起点。只在清空输入、排序成功提交或组件卸载这类“旧输入作废”的时点取消。

`setTimeout` 的延迟只是交给宿主安排计时任务，不保证回调在精确时刻运行；用 Node.js 26.13.0 的高分辨率时钟实测，有时会观察到比传入值略短的等待，而 Node.js 还会把小于 `1ms` 或大于 `2147483647ms` 的延迟当作 `1ms`、截掉小数部分（Node.js 规则，不能套到所有宿主）。计时器在事件循环里的语义见[事件循环怎样安排任务、微任务和渲染？](../browser/event-loop-tasks-and-rendering.md)。

## 实例：lodash 的 `_.debounce` 与 `_.throttle`

> [!info] 版本
> 本节按 lodash 4.18.1（2026-04-01 发布；2026-11-12 核对仍为最新稳定版）。下面的时刻用 lodash 4.18.1 源码配合假时钟复算。

`_.debounce(func, wait, options)` 默认只在尾沿执行；`options` 有 `leading`、`trailing`、`maxWait`，返回的函数带 `cancel()` 和 `flush()`。`_.throttle(func, wait, options)` 默认 `leading` 和 `trailing` 都为 `true`，实现上就是调用 `_.debounce`，并令 `maxWait` 等于 `wait`。

> [!example] maxWait 已处理的输入，不会被尾沿重复发送
> 搜索框用 `_.debounce(search, 300, { trailing: true, maxWait: 1000 })`。第一次输入在 `0ms`，之后每隔 `120ms` 输入一次，依次是 `Ops 0`、`Ops 1`……
>
> | 输入情况 | `1000ms` 时（maxWait 到期） | 停止输入之后 |
> |---|---|---|
> | 共 9 次，最后一次在 `960ms` | 执行最新的 `Ops 8` | 没有待执行输入，不再调用 |
> | 共 12 次，最后一次在 `1320ms` | 执行当时最新的 `Ops 8` | `1080`–`1320ms` 又有新输入；`1620ms`（最后输入后 `300ms`）尾沿执行 `Ops 11` |
>
> 尾沿只执行仍待执行的输入。第一种情况里 `Ops 8` 已被 maxWait 执行，尾沿就没有可做的事。

首沿、尾沿都开时，第一次立即执行；窗口内再有调用，尾沿才执行。需要立即提交尚待执行的尾部输入时调用 `flush()`：

~~~javascript
const search = _.debounce(fetchReports, 300, { leading: true, trailing: true });
search({ sort: "recent", query: "O" });   // 首沿立即执行
search({ sort: "recent", query: "Ops" }); // 窗口内第二次调用，尾沿待执行
search.flush();                           // 现在就执行 "Ops"
~~~

把上节的 `0/40/110ms` 时间线交给默认的 `_.throttle(search, 100)`，结果和手写的首沿节流不同：A 在 `0ms` 首沿执行；B 不会被丢弃，而在 `100ms` 尾沿执行；C 在 `110ms` 到达时已处在新窗口里，于 `210ms` 尾沿执行。要得到“只要首沿”的行为，需显式传 `{ trailing: false }`。

在 React 组件里，同一个 debounce 实例要跨渲染保存（例如放进 ref，只创建一次）。下面的 Hook 把本章规则放回报表页：排序由路由提交，Hook 只用已提交的 `committedSort`（已提交与待定导航的区别见[路由怎样把 URL 变成已提交的数据和界面？](../ui-state/routing-and-loaders.md)）；每次输入只更新参数和请求代次，不取消实例；清空输入、排序提交或卸载时才取消，并递增代次让旧响应作废。

> [!example]- React Hook：复用计时器、按已提交排序重查、拒绝过时响应
>
> 输入 `Ops` 后，计时器调用 `fetchReports({ sort: "recent", query: "Ops" })`，合成服务返回 `[May Ops, April Ops]`。点击“最早优先”会立即导航；loader 成功提交 `oldest` 后，Effect 清理旧计时器、作废旧的 recent 请求，再排入 `(oldest, Ops)`。等待期间页面显示 loader 给的基础列表 April、May，拿到当前结果后显示 `[April Ops, May Ops]`。Back / Forward 同样以成功提交的 sort 驱动重查。点击当前已提交的排序是空操作，不取消当前搜索。页面用 `searchResults ?? loaderReports` 在搜索结果和基础列表间选择；只有 `(committedSort, query)` 与当前一致的结果和错误才显示。
>
> ~~~javascript
> import { useEffect, useRef, useState } from "react";
> import _ from "lodash";
> import { fetchReports } from "./report-api";
>
> function useReportSearch(committedSort, navigate) {
>   const [query, setQuery] = useState("");
>   const queryRef = useRef("");
>   const [searchResult, setSearchResult] = useState(null);
>   const [searchFailure, setSearchFailure] = useState(null);
>   const [searching, setSearching] = useState(false);
>   const requestGenerationRef = useRef(0);
>   const scheduleRef = useRef(null);
>   if (scheduleRef.current === null) {
>     scheduleRef.current = _.debounce(
>       async (queryAtInput, sortAtInput, generation) => {
>         try {
>           const reports = await fetchReports({ sort: sortAtInput, query: queryAtInput });
>           if (generation === requestGenerationRef.current) {
>             setSearchResult({ sort: sortAtInput, query: queryAtInput, reports });
>           }
>         } catch (error) {
>           if (generation === requestGenerationRef.current) {
>             setSearchFailure({ sort: sortAtInput, query: queryAtInput, error });
>           }
>         } finally {
>           if (generation === requestGenerationRef.current) setSearching(false);
>         }
>       },
>       300,
>       { trailing: true, maxWait: 1000 }
>     );
>   }
>   const scheduleReportSearch = scheduleRef.current;
>
>   useEffect(() => {
>     const generation = ++requestGenerationRef.current;
>     const latestQuery = queryRef.current;
>     setSearchResult(null);
>     setSearchFailure(null);
>     setSearching(Boolean(latestQuery));
>     if (latestQuery) scheduleReportSearch(latestQuery, committedSort, generation);
>     return () => {
>       requestGenerationRef.current += 1;
>       scheduleReportSearch.cancel();
>     };
>   }, [scheduleReportSearch, committedSort]);
>
>   function onSearchInput(nextQuery) {
>     queryRef.current = nextQuery;
>     setQuery(nextQuery);
>     setSearchResult(null);
>     setSearchFailure(null);
>     const generation = ++requestGenerationRef.current;
>     if (!nextQuery) {
>       scheduleReportSearch.cancel();
>       setSearching(false);
>       return;
>     }
>     setSearching(true);
>     scheduleReportSearch(nextQuery, committedSort, generation);
>   }
>
>   function onSortNavigation(nextSort) {
>     if (nextSort === committedSort) return; // 当前排序不再导航，也不取消搜索
>     navigate(`/reports/42?sort=${encodeURIComponent(nextSort)}#summary`); // 立即导航
>   }
>
>   const currentSearchResult =
>     searchResult?.sort === committedSort && searchResult?.query === query ? searchResult.reports : null;
>   const currentSearchError =
>     searchFailure?.sort === committedSort && searchFailure?.query === query ? searchFailure.error : null;
>
>   return {
>     query,
>     searchResults: currentSearchResult,
>     searchError: currentSearchError,
>     searching,
>     onSearchInput,
>     onSortNavigation,
>   };
> }
> ~~~

## 实例：ahooks 的防抖与节流 Hook

> [!info] 版本
> 本节按 ahooks v3.11.0（2026-10-27 发布；2026-11-12 核对仍为最新）。

ahooks 把同样的计时策略包成两类 Hook：一类延迟**值**，一类包装**函数**。

| Hook | 返回 | 默认时序 |
|---|---|---|
| `useDebounce(value, options)` | 延迟更新后的值 | `wait` 1000 ms，`leading` false，`trailing` true；`maxWait` 可选 |
| `useThrottle(value, options)` | 限频后的值 | `wait` 1000 ms，`leading` 与 `trailing` 都为 true |
| `useDebounceFn(fn, options)` | `{ run, cancel, flush }` | `wait` 1000 ms，`leading` false，`trailing` true |
| `useThrottleFn(fn, options)` | `{ run, cancel, flush }` | `wait` 1000 ms，`leading` 与 `trailing` 都为 true |

默认等待是 1000 ms，比搜索框常用的 300 ms 长，用时要显式传 `wait`。`useDebounce` 只返回一个延迟更新的值，本身不发请求；请求由依赖这个值的请求 Hook 发起，`useRequest` 的依赖刷新与取消契约见[服务端数据怎样缓存、刷新和乐观更新，迟到的响应又归谁？](../ui-state/server-state-and-optimistic-updates.md)。这里的 `cancel` 同样只取消尚未执行的调用，已发出的请求要另行管理。

`useRequest` 自带的选项在 v3 叫 `debounceWait` / `throttleWait`；维护 v2 项目时会遇到旧名 `debounceInterval` / `throttleInterval`。升级前核对实际依赖版本，不要混用两代选项。

## 包装异步函数时，策略要重新定义

本章的包装器都在同步调用上回答了四个问题：用 rest 参数收齐实参，用 `fn.apply(this, args)` 转发接收者，用 `finally` 保证收尾而不吞掉结果，用闭包保存 `called`、缓存或计时器这类状态。防抖与节流的闭包状态决定了 leading、trailing、maxWait 的时序，而 `cancel` / `flush` 只管还没执行的调用。

一旦原函数返回 Promise，这些策略就要重新定义：计时包装少算了异步时间，`once` 把拒绝也算作用掉的一次，`memoize` 缓存了可能拒绝的 Promise。Promise 怎样传递值和失败，见[Promise 和 async 函数怎样传递值和失败？](./promises-and-async-functions.md)。

> [!info]- 来源
> - rest 参数、函数闭包与 `length` 属性（“rest 参数收集实参”“柯里化与部分应用”）：[ECMAScript 2026 Function Objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ecmascript-function-objects)（§10.2）、[Function instances `length`](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function-instances-length)（§20.2.4.1）。
> - 包装器转发接收者与实参（“包装通则”及各实现）：[ECMAScript 2026 Function.prototype.apply](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.apply)；计时 API：[W3C High Resolution Time `performance.now()`](https://www.w3.org/TR/hr-time-3/#dom-performance-now)（Level 3，核对日期 2026-11-12）；TypeScript 显式 `this` 参数：[TypeScript Handbook: Declaring `this` in a Function](https://www.typescriptlang.org/docs/handbook/2/functions.html#declaring-this-in-a-function)。
> - 缓存键的存在检查与序列化（“memoize”）：[ECMAScript 2026 Map.prototype.has](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-map.prototype.has)（§24.1.3.9）、[JSON.stringify](https://tc39.es/ecma262/2026/multipage/structured-data.html#sec-json.stringify)（§25.5.4）。
> - 原始练习的题目契约与作者解法（rest 参数、组合、`once`、记忆化）：存档 [Return Length of Arguments Passed](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2703.%20Return%20Length%20of%20Arguments%20Passed.md)、[Function Composition](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2629.%20Function%20Composition.md)、[Allow One Function Call](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2666.%20Allow%20One%20Function%20Call.md)、[Memoize](../../archive/front-end/0-1_Learning_Notes/Typescript/leetcode30days/FunctionTransformations/2623.%20Memoize.md)。
> - 计时器延迟只是安排任务、Node.js 的延迟钳制（“cancel 和 flush 只管还没执行的调用”末段）：[WHATWG HTML Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)（Living Standard，核对日期 2026-11-12）、[Node.js Timers: `setTimeout`](https://nodejs.org/api/timers.html#settimeoutcallback-delay-args)（官方文档 26.13.1；略短等待为 Node.js 26.13.0 实测）。请求取消只停客户端：[WHATWG DOM Aborting ongoing activities](https://dom.spec.whatwg.org/#aborting-ongoing-activities)、[Fetch Standard: Aborting a fetch](https://fetch.spec.whatwg.org/#abort-fetch)、[MDN AbortController.abort()](https://developer.mozilla.org/en-US/docs/Web/API/AbortController/abort)。
> - lodash 实例（“实例：lodash 的 `_.debounce` 与 `_.throttle`”）：[Lodash 4.18.1 release](https://github.com/lodash/lodash/releases/latest)（2026-04-01 发布，2026-11-12 核对）；[`_.debounce` 的 leading/trailing/maxWait、cancel、flush 说明](https://github.com/lodash/lodash/blob/4.18.1/doc/README.md#_debouncefunc-wait0-options)；`_.throttle` 默认值及其委托 `_.debounce`、`maxWait: wait` 的实现：[lodash 4.18.1 `lodash.js`](https://github.com/lodash/lodash/blob/4.18.1/lodash.js)（`throttle` 函数）。maxWait 表与 `_.throttle` 时间线为 lodash 4.18.1 + 假时钟复算。Hook 例子用到的 React [`useRef`](https://react.dev/reference/react/useRef) 与 [`useEffect`](https://react.dev/reference/react/useEffect)，核对日期 2026-11-12。
> - ahooks 实例（“实例：ahooks 的防抖与节流 Hook”）：[useDebounce](https://ahooks.js.org/hooks/use-debounce/)、[useDebounceFn](https://ahooks.js.org/hooks/use-debounce-fn/)、[useThrottle](https://ahooks.js.org/hooks/use-throttle/)、[useThrottleFn](https://ahooks.js.org/hooks/use-throttle-fn/)；v3 `debounceWait` / `throttleWait`：[v3.11.0 useRequest option types](https://github.com/alibaba/hooks/blob/v3.11.0/packages/hooks/src/useRequest/src/types.ts)；v2 旧选项迁移：[ahooks upgrade guide](https://ahooks.js.org/guide/upgrade/)（2026-11-06）；版本：[ahooks v3.11.0 release](https://github.com/alibaba/hooks/releases/tag/v3.11.0)（2026-10-27 发布，2026-11-12 核对）。
