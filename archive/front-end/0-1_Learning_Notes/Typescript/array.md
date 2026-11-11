# TypeScript 数组怎样从类型声明走到运行时遍历与变换？

**案例背景：** 一组测量值 `[1, 4, 9]` 要开平方，保留根值至少为 2 的项，再求总和。`number[]` 告诉 TypeScript 哪类值可以放进数组；编译后，遍历、空槽和修改仍由 JavaScript Array 决定。这里先走完这组数据，再查阅常用数组操作。关于筛选、排序、去重和浅复制的完整机制，见[数组怎样筛选、排序并保留对象身份？](../../../../frontend/javascript/arrays.md)。

## 声明了元素类型，为何还会读到 undefined？

```typescript
const holes: number[] = new Array<number>(3);
const values: number[] = [1, 4, 9];
const matrix: number[][] = [[0, 1, 2], [0, 1, 2]];
console.log(holes.length, 0 in holes, holes[0]); // 3, false, undefined
console.log(0 in [undefined], [undefined][0]);  // true, undefined
console.log(values[8]);                         // undefined
console.log(matrix.length, matrix[1]?.length); // 2, 3
console.log(Array.isArray(values), typeof values); // true, "object"
```

`number[]` 与 `Array<number>` 都表示元素类型为 `number`；它们只在编译时供 TypeScript 检查，编译后不会为每个位置加上运行时校验。`new Array<number>(3)` 运行时仍是 JavaScript 的 `new Array(3)`：长度为 3，但索引 0、1、2 都是 empty slot（空槽）。空槽与“索引存在、值为 `undefined`”不同；在原型链没有同索引属性时，`in` 可以区分两者，因为 `in` 也会沿原型链查找。构造器传入多个参数时语义又不同：`new Array(1, 2, 3)` 会把三个值装入数组，并非声明长度。类型声明也不保证索引一定存在；默认设置下 `values[8]` 静态类型仍为 `number`，实际读取却是 `undefined`。同时启用 `strictNullChecks` 和 `noUncheckedIndexedAccess`（`strict` 会启用前者）后，索引读取的静态类型才会包含 `undefined`；代码运行时仍需按需检查值。判断数组用 `Array.isArray`，因为 `typeof` 对数组和普通对象都返回 `"object"`。

## map 传入什么，结果存到哪里？

```typescript
const values = [1, 4, 9];
const roots = values.map((value, index, array) => {
  console.log(index, array === values); // 0/1/2；每次都是 true
  return Math.sqrt(value);
});
const largeRoots = roots.filter(root => root >= 2);
const total = largeRoots.reduce((sum, root) => sum + root, 0);
console.log(roots, largeRoots, total); // [1, 2, 3], [2, 3], 5

const users = [
  { id: 1, name: "John" },
  { id: 2, name: "Jane" },
  { id: 3, name: "Doe" }
];
const userNames: string[] = users.map(user => user.name);
console.log(userNames); // ["John", "Jane", "Doe"]
```

对测量值这条处理链，`map` 把各项变成根值并放进新数组，`filter` 按条件保留根值，`reduce` 把它们合成一个数：

| 步骤 | 本步输入 | 本步输出 | 结果在后续步骤中的作用 |
|---|---|---|---|
| `map` | `[1, 4, 9]` | `[1, 2, 3]` | 产生待筛选的根值 |
| `filter` | `[1, 2, 3]` | `[2, 3]` | 去掉小于 2 的根值 |
| `reduce` | `[2, 3]` 与初始和 `0` | `5` | 得到总和 |

上例的 `map` callback（回调函数）按位置接收元素、索引和原数组三个参数；只用元素时可以只写 `value`。若要用第三个参数，仍须保留第二个位置，可写成 `_index`。普通函数可通过 `map(callback, thisArg)` 指定回调的 `this`；箭头函数的 `this` 来自定义它时所在的词法作用域。同一处理链中的 `reduce` 回调则以 accumulator（累加器）为第一个参数、当前元素为第二个参数；本例从 `0` 开始，依次计算 `0 + 2 = 2`、`2 + 3 = 5`。

`map` 先记住开始时的长度，再按索引检查属性是否存在；自有属性和原型链上的同索引属性都算存在。开始后追加到原长度之外的元素不会被访问；访问前删除、届时也不再存在的索引会被跳过。普通空槽在原型链没有同索引属性时不会调用回调，结果相同位置仍为空槽。它本身创建新数组、不直接改输入，但回调可以改输入数组或其中共享的对象。筛选时，`filter` 会把通过的现存值依次放入结果，不保留原索引间隙。完整循环实现见[不用 map 怎样变换数组？](leetcode30days/Array/2635.%20Apply%20Transform%20Over%20Each%20Element%20in%20Array.md)和[不用 filter 怎样保留匹配项？](leetcode30days/Array/2634.%20Filter%20Elements%20from%20Array.md)。

若第二项缺失，可声明 `const sparse = new Array<number>(3)`，再令 `sparse[0] = 1`、`sparse[2] = 9`。下面用 `[1, , 9]` 表示它的 JavaScript 运行时内容：`sparse.map(Math.sqrt)` 得到 `[1, , 3]`，空槽仍在原位置；接着经 `filter(root => root >= 2)` 得到压紧后的 `[3]`，以 `0` 为初始值 `reduce` 得到 `3`。

## 原地修改还是产生新值？

| 目的 | 方法与返回值 | 是否修改原数组 |
|---|---|---|
| 两端添加 | `push` / `unshift` 返回新长度 | 是 |
| 两端取走 | `pop` / `shift` 返回元素；空数组时为 `undefined` | 是 |
| 反转、排序 | `reverse` / `sort` 返回原数组 | 是 |
| 插入、删除、替换 | `splice(start, deleteCount, ...items)` 返回由删去元素组成的新数组 | 是 |
| 拼接、切片 | `concat` / `slice` 返回浅层新数组 | 否 |
| 映射、筛选 | `map` / `filter` 返回新数组；回调可能改输入 | 方法本身不改输入 |
| 非修改排序或反转 | `toSorted` / `toReversed` 返回浅层副本 | 否 |

例如 `['a', 'b', 'c'].slice(1, 3)` 得到 `['b', 'c']`，结束位置不包含在结果里。令 `items = ['a', 'b', 'c']`，`items.splice(1, 1, 'x', 'y')` 返回装着被删元素的数组 `['b']`，并使 `items` 变为 `['a', 'x', 'y', 'c']`。数值升序要写 `(a, b) => a - b`；不提供比较函数时会按字符串排序，所以 `[3, 10, 2]` 会成为 `[10, 2, 3]`。`[[0, 1], [2, 3]].flat()` 展开一层；数组副本仍是浅复制，嵌套对象不会随之深复制。

## 遍历、判断和归约各返回什么？

| 问题 | 操作 | 本地例子 |
|---|---|---|
| 找索引 | `indexOf` / `lastIndexOf`；未找到返回 `-1` | `[1, 2, 3, 2].lastIndexOf(2)` 为 3 |
| 判断全部或至少一个通过 | `every` / `some` | `[].every(fn)` 为 `true`；`[].some(fn)` 为 `false` |
| 对各项执行副作用 | `forEach` 返回 `undefined` | 参数同样是值、索引、数组 |
| 顺序累计 | `reduce` | `[1, 2, 3, 4].reduce((sum, x) => sum + x, 0)` 为 10 |
| 从右累计 | `reduceRight` | `[[0,1],[2,3],[4,5]].reduceRight((a,x) => a.concat(x))` 为 `[4,5,2,3,0,1]` |
| 显示为字符串 | `join` / `toString` / `toLocaleString` | `['Fire','Air','Water'].join(' - ')` 为 `Fire - Air - Water`；本地化结果依环境而异 |

没有初始值的 `reduce` 会从首个存在的索引取初值，自有属性和原型链上的同索引属性都计入；遍历范围内没有任何存在索引时才抛出 `TypeError`，例如普通空数组，或原型链也没有同索引属性的全空槽数组。显式给出初始值既定义了空数组的结果，也让 TypeScript 更容易确定累加器类型。

`forEach`、`map`、`reduce`、`every` 和 `some` 都跳过不存在的索引；普通空槽经 `for...of` 读取时得到 `undefined`。若循环需要提前 `break`，用 `for`、`for...of` 等语句式循环，`forEach` 回调里的 `return` 不会结束整个遍历。数组解构 `const [first, second] = fruits` 按位置取值；栈可以直接用 `push` / `pop`，但要区分“栈为空”和“栈里存着 `undefined`”，见[两个栈如何得到队列？](leetcode30days/queueWith2Stacks.md)。

> [!info]- 来源
> - TypeScript 的类型擦除及运行时行为：[TypeScript Handbook — Erased Types](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types)，核对 2026-11-12；索引读取可能为 `undefined` 的可选检查：[TypeScript TSConfig — `noUncheckedIndexedAccess`](https://www.typescriptlang.org/tsconfig/noUncheckedIndexedAccess.html)，核对 2026-11-12。
> - 数组构造、空槽、迭代回调和本文列出的方法：[ECMAScript 2026 Indexed Collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)，§23.1.1 Array 构造器、§23.1.3 Array.prototype 方法；核对 2026-11-12。
