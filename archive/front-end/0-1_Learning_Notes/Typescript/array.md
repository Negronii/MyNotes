# TypeScript 数组怎样从类型声明走到运行时遍历与变换？

**案例背景：** 一组测量值 `[1,4,9]` 要开平方，再保留根值至少为 2 的项，最后汇总。`number[]` 说明编译器允许放什么元素；真正如何分配、遍历和修改，仍由 JavaScript Array 决定。此页保留类型与常用方法的查阅例，完整的数据变换主线见[数组怎样筛选、排序并保留对象身份？](../../../../frontend/javascript/arrays.md)。

## 声明了元素类型，为何还会读到 undefined？

```typescript
const holes = new Array<number>(3);
const values: number[] = [1, 4, 9];
const matrix = [[0, 1, 2], [0, 1, 2]];
console.log(holes.length, 0 in holes); // 3, false
console.log(values[8]);               // undefined
console.log(matrix.length, matrix[1]?.length); // 2, 3
console.log(typeof values);           // "object"
```

`new Array(3)` 的单个数字表示长度；`new Array(1, 2, 3)` 则放入三个值。前者产生 empty slot（空槽），不等于显式填入三个 `undefined`。类型声明也不保证索引一定存在；开启 `noUncheckedIndexedAccess` 可让索引读取类型体现缺失可能性，运行时仍须处理它。判断数组用 `Array.isArray`，`typeof` 无法区分数组与普通对象。

## map 传入什么，结果存到哪里？

```typescript
const values = [1, 4, 9];
const roots = values.map((value, index, array) => {
  console.log(index, array === values); // 0/1/2，各次都是 true
  return Math.sqrt(value);
});
console.log(roots); // [1, 2, 3]

const users = [
  { id: 1, name: "John" },
  { id: 2, name: "Jane" },
  { id: 3, name: "Doe" }
];
const userNames: string[] = users.map(user => user.name);
// ["John", "Jane", "Doe"]
```

callback（回调函数）收到元素、索引、原数组三个位置参数。只需要第一个时可以只声明 `value`；要用第三个时可以把中间参数命名为 `_index`，不能改变它的参数位置。普通函数还可通过 `map(callback, thisArg)` 指定回调接收者；箭头函数的 `this` 来自词法作用域。

接着沿同一组数据走完处理：`roots.filter(x => x >= 2)` 得到 `[2,3]`，再用 `reduce((sum,x) => sum+x, 0)` 得到 5。映射改变各位置的值，筛选决定保留哪些值，归约将剩余值合成一个结果。

`map` 创建新数组，但回调仍可修改原数组或共享对象。它先记住初始长度，再逐个检查索引是否存在：不会处理后来追加到初始长度之外的项，访问前已删除的项会跳过。空槽会在结果相同位置留下空槽；`filter` 则把匹配值压紧。完整循环实现和原题见[不用 map 怎样变换数组？](leetcode30days/Array/2635.%20Apply%20Transform%20Over%20Each%20Element%20in%20Array.md)与[不用 filter 怎样保留匹配项？](leetcode30days/Array/2634.%20Filter%20Elements%20from%20Array.md)。

## 原地修改还是产生新值？

| 目的 | 方法与返回值 | 是否修改原数组 |
|---|---|---|
| 两端添加 | `push` / `unshift` 返回新长度 | 是 |
| 两端取走 | `pop` / `shift` 返回元素，空数组为 `undefined` | 是 |
| 反转、排序 | `reverse` / `sort` 返回原数组 | 是 |
| 插入、删除、替换 | `splice(start, deleteCount, ...items)` 返回删去的数组 | 是 |
| 拼接、切片 | `concat` / `slice` 返回浅层新数组 | 否 |
| 映射、筛选 | `map` / `filter` 返回新数组 | 方法本身不改输入，回调可能改 |
| 非修改排序或反转 | `toSorted` / `toReversed` | 否；仍是浅层副本 |

例如 `['a','b','c'].slice(1,3)` 得到 `['b','c']`，结束索引不含在内；`splice(1,1,'x','y')` 会改原数组并返回 `['b']`。数值排序写 `(a,b)=>a-b`，否则默认按字符串比较，`[3,10,2]` 会成为 `[10,2,3]`。`[[0,1],[2,3]].flat()` 展开一层；嵌套对象不会因此深复制。

## 遍历、判断和归约各返回什么？

| 问题 | 操作 | 本地例子 |
|---|---|---|
| 找索引 | `indexOf` / `lastIndexOf`；未找到 `-1` | `[1,2,3,2].lastIndexOf(2)` 为 3 |
| 是否全部/至少一个通过 | `every` / `some` | `[].every(fn)` 为 true；`[].some(fn)` 为 false |
| 对各项执行副作用 | `forEach` 返回 `undefined` | 参数同样是值、索引、数组 |
| 顺序累计 | `reduce` | `[1,2,3,4].reduce((sum,x)=>sum+x,0)` 为 10 |
| 从右累计 | `reduceRight` | `[[0,1],[2,3],[4,5]].reduceRight((a,x)=>a.concat(x))` 为 `[4,5,2,3,0,1]` |
| 显示为字符串 | `join` / `toString` / `toLocaleString` | `['Fire','Air','Water'].join(' - ')` 为 `Fire - Air - Water`；本地化结果依环境 |

没有初始值的 reduce 会用首个存在元素作为累加器；空数组或全空槽数组因此抛 `TypeError`。给出初始值也让 TypeScript 更容易明确累加器类型。

`forEach`、`map`、`reduce`、`every` 和 `some` 跳过不存在的索引；`for...of` 对普通空槽读出 `undefined`。需要提前 `break` 时用循环，不要把 `forEach` 当成可以中断的循环。数组解构 `const [first, second] = fruits` 按位置取值；栈则直接用 `push`/`pop`，但空栈与存入 `undefined` 的区别要另做返回契约，见[两个栈如何得到队列？](leetcode30days/queueWith2Stacks.md)。

> [!info]- 来源
> - 分配、空槽、回调与上述数组方法：[ECMAScript 2026 Indexed Collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)，Array constructor 与 Array.prototype 各对应小节，核对 2026-11-06。
> - 索引类型的缺失值提示：[TypeScript noUncheckedIndexedAccess](https://www.typescriptlang.org/tsconfig/noUncheckedIndexedAccess.html)。类型检查不替代运行时存在性检查。
