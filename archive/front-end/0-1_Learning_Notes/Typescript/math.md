# JavaScript 的 Math 怎样处理舍入、范围和数值变换？

**案例背景：** 42 条记录、每页 20 条的列表需要计算页数和末页已有条数。查找极值、随机选数组索引和换算测量值，则是其他 Math 操作示例。Math 是 JavaScript 内置对象，TypeScript 只提供类型信息，没有额外创建一套运行时数学库。

## 页数为什么要向上取整？

记录总数和每页容量都用安全整数表示，总数非负、容量为正。42 / 20 = 2.1 表示两整页还剩一点，必须分配第三页，所以 `Math.ceil(42/20)` 为 3。末页已有 `42 - (3 - 1) * 20 = 2` 条；总数大于零时，这个公式能直接算末页条数。若 40 条正好整除，每页 20 条仍有 2 页，末页已有 `40 - (2 - 1) * 20 = 20` 条，并非空页。零条记录则按本例约定为零页、零条。对负数，向上和“离零更远”不是一回事：

| 输入 | floor：向负无穷 | ceil：向正无穷 | trunc：向零 | round：最近整数，平局向正无穷 |
|---|---|---|---|---|
| 1.5 | 1 | 2 | 1 | 2 |
| −1.5 | −2 | −1 | −1 | −1 |

> [!info] 数轴上的“上”指更大的数
> −1 比 −2 大。因此 `Math.round(-1.5)` 得 −1；不能把它解释为绝对值四舍五入后再恢复符号。`Math.round(-0.1)` 还会得到负零，可用 `Object.is(Math.round(-0.1), -0)` 检查。

## 最大、最小和随机范围怎样确定？

`Math.max(1,2,3)` 为 3，`Math.min(1,2,3)` 为 1；零参数时分别是 `-Infinity`、`Infinity`。它们可作为逐项取极值的初值，例如 `Math.max(-Infinity,3)` 与 `Math.min(Infinity,3)` 都得到 3；业务上的空集合往往仍需要“无结果”，不能把无穷当成真实测量值。`max/min` 成功完成所有参数的数值转换后，只要其中一个转换结果是 NaN，就返回 NaN。数组元素很多时，`Math.max(...values)` 或 `Math.min(...values)` 可能超过具体实现的实参数量上限；逐项归约不必一次展开全部参数。

`Math.random()` 返回 `[0,1)` 内近似均匀的随机或伪随机数。对一个短数组，`Math.floor(Math.random()*length)` 常用于选择有效索引，前提是 `length > 0`；ECMAScript 不保证它适合密码学，密码或令牌需要宿主提供的密码学随机 API，例如浏览器 Web Crypto 的 `crypto.getRandomValues`。

## 根号、幂、对数和角度各在变换什么？

| 需求 | 操作与例子 | 边界 |
|---|---|---|
| 距离零多远 | `Math.abs(-3)` 为 3 | 不保留方向 |
| 求平方根 | `Math.sqrt(9)` 为 3 | 当 `x < 0` 时返回 NaN |
| 求幂 | `Math.pow(2,3)` 或 `2 ** 3` 为 8 | Number 仍受浮点范围和精度限制 |
| 自然对数 | `Math.log(Math.E)` 约为 1 | log(0) 为 −Infinity，负数为 NaN |
| 三角函数 | `Math.sin` / `Math.cos` / `Math.tan` | 参数用弧度，180° 对应 π；浮点近似不保证理想恒等式逐位相等 |

例如角度 30° 先换成弧度，再计算 `Math.sin(30 * Math.PI / 180)`，结果约为 0.5。对数是在问“e 的几次幂得到这个值”；它不是默认的十进制对数，后者用 `Math.log10`。浮点误差与精确整数范围见[JavaScript 值怎样转换、比较与表示数字？](../../../../frontend/javascript/javascript-types.md)。

> [!info]- 来源
> - `ceil`、`floor`、`round`、`trunc` 的方向与负零：[ECMAScript 2026 §21.3.2.10](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.ceil)、[§21.3.2.16](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.floor)、[§21.3.2.29](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.round)、[§21.3.2.37](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.trunc)。
> - 极值的空参数和 NaN 结果：[ECMAScript 2026 §21.3.2.25 Math.max](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.max)、[§21.3.2.26 Math.min](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.min)。
> - 随机区间和近似均匀定义：[ECMAScript 2026 §21.3.2.28 Math.random](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.random)。该快照日期为 2026-03-31，核对 2026-11-12。
> - 绝对值、平方根、幂、自然/十进制对数：[ECMAScript 2026 §21.3.2.1 Math.abs](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.abs)、[§21.3.2.33 Math.sqrt](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.sqrt)、[§21.3.2.27 Math.pow](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.pow)、[§21.3.2.21 Math.log](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.log)、[§21.3.2.23 Math.log10](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.log10)。
> - 自然对数的底与 π 常量：[ECMAScript 2026 §21.3.1.1 Math.E](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.e)、[§21.3.1.6 Math.PI](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.pi)。
> - 三角函数：[ECMAScript 2026 §21.3.2.12 Math.cos](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.cos)、[§21.3.2.31 Math.sin](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.sin)、[§21.3.2.35 Math.tan](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.tan)。这些章节规定输入用弧度，结果为实现近似的 Number。
> - 浏览器密码学随机值：[W3C Web Cryptography API，Recommendation 2017-01-26，§10.2.1 `getRandomValues`](https://www.w3.org/TR/2017/REC-WebCryptoAPI-20170126/#Crypto-method-getRandomValues)。
