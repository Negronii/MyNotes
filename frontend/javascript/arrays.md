# JavaScript 数组操作如何处理空位、修改与复制？

本章的例子是一次月报数据导入：同一张报表（`reportId` 为 `r-104`）被导入了两次，首条记录金额为 0，重试后的记录金额为 120。我们要把它们去重成一条，但该保留哪一条由业务规则决定；后文会比较“用 Map 保留最后一次写入”和“排序后保留每组首项”两种策略的不同结果。

数组 `rows` 的第二个位置故意留了一个 hole (空位)，即这个索引上根本没有元素。本章先用 `rows` 对照去重策略，再用短数组说明空位、删除、排序与展平，最后在复制一节回到 `rows` 和 `owner` 观察浅复制。

~~~javascript
const owner = { id: "u-17", name: "Ada" };
const first = { reportId: "r-104", amount: 0, owner };
const retry = {
  reportId: "r-104",
  amount: 120,
  owner: { id: "u-17", name: "Ada" },
};
const rows = [first, , retry];
~~~

`reportId` 相同，说明两条记录描述的是同一份业务报表，但 `first` 与 `retry` 在 JavaScript 里仍是两个不同的对象。它们的 `owner` 也是内容相同、身份不同的两个对象，复制一节会用 `first.owner` 说明浅复制共享嵌套对象。实际业务数据通常应是没有空位的稠密数组；这里留空位，是为了看清各个数组操作怎样对待缺失的索引。要注意区分三种情况：索引上没有元素（空位）、元素的值是显式 `undefined`、以及迭代器读取空位时产出的 `undefined`，它们在结构上不是一回事。

## 去重前先选“相同”的定义

对于原始值，`Set`（集合）按 `SameValueZero`（同值零）保留首次出现顺序。`NaN` 会和 `NaN` 合并，`+0` 与 `-0` 合并；对象按身份去重，字段相同但引用不同的对象仍会保留。相等规则和 `Map`（映射）/ `Set` 的键行为见[何时使用 Map、Set 或普通对象？](./map-and-set.md)。

~~~javascript
[...new Set([1, 1, NaN, NaN, -0, +0])]; // [1, NaN, 0]
[...new Set([{ id: 1 }, { id: 1 }])].length; // 2：对象身份不同
~~~

用 `filter` 配合 `indexOf` 也能保留每个值的首次出现，但 `indexOf` 使用严格相等（`===`），而 `NaN === NaN` 为 `false`，所以 `indexOf(NaN)` 总返回 `-1`，每个 `NaN` 都会被过滤掉。另外，`filter` 会跳过空位，空位不会出现在结果中。

~~~javascript
const values = [NaN, NaN, 1, 1];
values.filter((value, index) => values.indexOf(value) === index); // [1]
[...new Set(values)]; // [NaN, 1]
~~~

回到报表记录：`first` 和 `retry` 是不同对象，`Set` 会把两者都保留。要按业务字段判重，可以用 `Map` 以 `reportId` 为键，值为最后出现的记录。重复的 `reportId` 会让后一个对象替换旧值，但该键在 `Map` 中的遍历位置仍是首次插入时的位置：

~~~javascript
function uniqueByReportId(items) {
  const byId = new Map();
  items.forEach(item => byId.set(item.reportId, item));
  return [...byId.values()];
}

uniqueByReportId(rows); // [retry]
~~~

这里使用 `forEach`，空位不会被当成一条记录；若输入可能包含显式 `undefined`，仍需在业务边界另行校验。重复项按 `reportId` 保留最后版本，是一个业务策略，不是 `Map` 自动推断出来的“对象相等”。

如果结果允许改变顺序，也可以先排序副本，让相同的记录相邻，再逐个比较相邻项去重。这个策略保留的是“排序后每组的第一项”，与上面 Map 的“保留最后一次写入”不同：本例两条记录按 `reportId` 比较相等，而 `sort` 是稳定排序，会保持它们原来的先后顺序，所以结果保留 `first`（金额 `0`），Map 则保留 `retry`（金额 `120`）。

下面的 `uniqueSorted` 接收两个函数：`compare` 是排序比较器，`same` 判断两项是否算重复。比较器必须把所有相等项排到一起，`same` 也必须和 `compare` 认定同一批项相等。函数先用 `filter` 跳过空位；它假设原型链上没有补出缺失的索引、每个现存元素都是记录、没有显式 `undefined`，外部输入不满足时应先校验。

~~~javascript
function uniqueSorted(items, compare, same) {
  const result = [];
  const presentItems = items.filter(() => true); // 跳过空位，结果已是稠密副本
  for (const item of presentItems.sort(compare)) {
    if (result.length === 0 || !same(result[result.length - 1], item)) {
      result.push(item);
    }
  }
  return result;
}

uniqueSorted(
  rows,
  (left, right) => left.reportId === right.reportId ? 0
    : left.reportId < right.reportId ? -1 : 1,
  (left, right) => left.reportId === right.reportId,
).map(item => item.amount); // [0]：排序策略保留组内首项
uniqueByReportId(rows).map(item => item.amount); // [120]：Map 策略保留最后一次写入
~~~

`filter` 已经生成了稠密副本，`sort` 只改变这个副本的顺序，所以函数不会修改 `items`，不必再额外复制一次。如果需要保持记录原来的出现顺序，就不要用排序去重代替 Set 或 Map。

## 删除匹配项时，选择副本还是原地修改

去重之后，另一个常见需求是删除指定的值。如果原数组还要给其他调用方使用，就用 `filter` 返回新数组。下面两种写法，一种每次直接在排除列表中查找，另一种在排除列表较大时先建一个 `Set`。`includes` 与 `Set.has` 都按 `SameValueZero` 比较，对象按身份比较。下面先按稠密数组说明副本与原地修改的区别，稀疏数组的不同结果放在本节末尾。

~~~javascript
const removeWithFilter = (items, ...excluded) =>
  items.filter(item => !excluded.includes(item));

const removeWithSet = (items, ...excluded) => {
  const removed = new Set(excluded);
  return items.filter(item => !removed.has(item));
};

removeWithFilter([1, 2, 1, 3], 1); // [2, 3]
removeWithSet([NaN, 1, NaN], NaN); // [1]
~~~

第一种在长度为 n 的输入和 m 个排除值下会做至多 n×m 次成员比较；第二种建立一次 Set，再逐项查询。规范只要求 Set 的平均访问时间相对集合大小为次线性，不保证所有引擎的精确常数或具体实现。若移除对象记录的业务 id，应先从记录读取 id，而不是把一个“字段相同”的新对象当成同一对象。

如果调用方明确要求原地修改，可以用 `splice`。删除一个元素后，后面的元素会左移一位，所以命中时索引不能加一，否则会漏检下一个元素。

~~~javascript
function removeInPlace(items, ...excluded) {
  let index = 0;
  while (index < items.length) {
    if (excluded.includes(items[index])) items.splice(index, 1);
    else index += 1;
  }
  return items;
}

const mutable = [1, 2, 1, 3];
removeInPlace(mutable, 1); // mutable 变为 [2, 3]

const sparseForRemoval = [, 1];
const filteredRemoval = sparseForRemoval.filter(value => value !== 1);
const splicedRemoval = sparseForRemoval.slice();
removeInPlace(splicedRemoval, 1);
filteredRemoval; // []：filter 跳过空位
splicedRemoval.length; // 1：splice 删除 1 后保留了原空位
0 in splicedRemoval; // false
~~~

每次 `splice` 都要移动后面的元素，连续删除很多项时总成本可能接近平方级；大批删除时，通常先构造结果数组，或用双指针一次线性压缩。上例也说明了稀疏数组的差异：原地循环读取空位得到 `undefined`，如果排除列表里有 `undefined`，空位也会被当作命中项删除；`filter` 则根本不会为空位调用回调。

## 空位怎样改变遍历结果

前两节已经看到 `forEach`、`filter` 会跳过空位，而按索引读取会得到 `undefined`。本节系统整理这种差异。空位指该索引上没有自有属性，不同于存在一个值为 `undefined` 的属性。多数带回调的数组方法会先用 `HasProperty`（属性存在性检查）判断索引是否存在，因此会跳过普通的空位；但 `HasProperty` 也查原型链，如果原型链上有同一索引的属性，它就会被访问。`find` 系列方法不做这个检查，而是按查找方向逐个读取索引，遇到第一个让回调返回真值的位置就停止；原型链上没有同索引属性时，空位以 `undefined` 传给回调。

下表按没有继承索引属性的普通数组描述空位结果。

| 操作 | 输入有空位时的行为 | 是否改动原数组 |
|---|---|---|
| `map` | 跳过空位，并在对应结果位置保留空位 | 否 |
| `filter` | 跳过空位，结果只包含通过的现存值 | 否 |
| `forEach`、`some`、`every`、`reduce` | 普通空位不调用回调；`reduce` 无初始值且没有现存项时抛错 | 否 |
| `find`、`findIndex`、`findLast`、`findLastIndex` | 按查找方向读取；普通空位作为 `undefined` 传给回调，命中后立即停止 | 否 |
| `for...of`、数组展开 | 消费数组迭代器；无继承索引属性时，空位读成 `undefined` | 否 |
| `flat` | 被展平层级中自身与原型链都不存在的索引不写入结果 | 否 |
| `sort`、`reverse`、`splice` | 操作原接收数组；稀疏结构可能改变 | 是 |
| `toSorted`、`toReversed`、`toSpliced` | 生成副本；被复制的空位若无继承索引值，会写成显式 `undefined` | 否 |

~~~javascript
const sparse = [, "x"];

Object.hasOwn(sparse, 0); // false：索引 0 没有自有属性
0 in sparse; // false：原型链上也没有索引 0
sparse[0]; // undefined
sparse.map(value => value); // [ <1 empty item>, "x" ]
sparse.filter(() => true); // ["x"]
const visited = [];
sparse.find((value, index) => {
  visited.push(index);
  return value === undefined;
});
visited; // [0]：空位读为 undefined 后命中，find 随即停止
[...sparse]; // [undefined, "x"]
Object.keys(sparse); // ["1"]
~~~

下面的例子演示原型链的影响：“空位”若从原型链继承到同索引的值，就会被 `map` 等方法访问。同一段代码还对比了 `for...in` 和 `for...of`：`for...in` 枚举可枚举的字符串属性名，可能包含自定义属性和继承属性；`for...of` 消费数组迭代器，按位置读出值，通常更适合遍历数组。

~~~javascript
const inheritedPrototype = Object.create(Array.prototype);
inheritedPrototype[0] = "from prototype";
const holeWithInheritedIndex = new Array(1);
Object.setPrototypeOf(holeWithInheritedIndex, inheritedPrototype);
Object.hasOwn(holeWithInheritedIndex, 0); // false：仍没有自有索引 0
0 in holeWithInheritedIndex; // true：原型链提供了索引 0
holeWithInheritedIndex[0]; // "from prototype"
holeWithInheritedIndex.map(value => value); // ["from prototype"]

const enumerableArray = [10, 20];
enumerableArray.note = "custom property";
const extraProperties = Object.create(Array.prototype);
extraProperties.label = "inherited property";
Object.setPrototypeOf(enumerableArray, extraProperties);

const keys = [];
for (const key in enumerableArray) keys.push(key);
keys; // ["0", "1", "note", "label"]

const values = [];
for (const value of enumerableArray) values.push(value);
values; // [10, 20]
~~~

`some` 和 `every` 在答案确定后会提前停止，也会跳过普通空位；空数组上 `some` 为 `false`，`every` 为 `true`。若需要判断“所有项都满足”但不接受空输入，需另行处理空数组。

~~~javascript
[].some(() => true); // false
[].every(() => false); // true
new Array(2).some(() => true); // false：空位不会调用回调
new Array(2).every(() => false); // true：所有空位都被跳过
~~~

最后一个与回调相关的陷阱：`map` 和 `filter` 的回调都接收 `value`、`index`、`array` 三个参数。把 `parseInt` 直接传给 `map` 时，索引会被当作第二个参数 `radix`（进制），`parseInt("2", 1)` 和 `parseInt("3", 2)` 都得到 `NaN`；显式传入进制才能得到预期值。

~~~javascript
["1", "2", "3"].map(parseInt); // [1, NaN, NaN]
["1", "2", "3"].map(text => parseInt(text, 10)); // [1, 2, 3]
["1", "2", "3"].map(Number); // [1, 2, 3]
~~~

## 从迭代器或类数组输入创建数组

`Array.from` 既能消费可迭代对象，也能按 `length` 和索引读取类数组对象（有 `length` 和数字索引、但不是数组的对象）；第二个参数是可选的映射函数，在创建时转换元素。它读取稀疏数组时走迭代器，空位被读成 `undefined`（原型链提供该索引时则是继承值），所以结果是稠密数组。数组展开也消费迭代器，结果相同，但不能处理不可迭代的类数组对象。

~~~javascript
Array.from(rows); // [first, undefined, retry]
Array.from(new Set(["paid", "review", "paid"])); // ["paid", "review"]
Array.from({ 0: "r-104", 1: "r-105", length: 2 }); // ["r-104", "r-105"]
Array.from({ length: 3 }, (_, index) => index * 2); // [0, 2, 4]

Array(3);    // 长度为 3 的稀疏数组
Array.of(3); // [3]：参数本身作为元素
Array.of(1, 2, 3); // [1, 2, 3]
~~~

类数组读取、可迭代对象和 `Array.from` 的差异也会出现在[HTMLCollection 与 NodeList 如何处理实时集合？](../browser-apis/dom-collections.md)的 DOM 集合快照中；迭代协议本身见[迭代器与生成器如何按需产出值？](./iterators-and-generators.md)。文本要按 Unicode 码点遍历时，`Array.from(string)` 也会消费字符串迭代器；用户感知字符可能由多个码点组成，还需另做分段，详见[文本算法应按什么单位计数和比较？](../../engineering-foundations/algorithms/text-units-and-algorithms.md)。

## 复制数组只复制一层

数组展开和 `slice` 会创建新数组，但新数组里存的仍是原来的对象引用；通过副本修改其中记录的属性，原数组也能看到这次修改。两者对空位的处理不同：对普通稀疏数组，`slice` 和 `concat` 保留空位，展开与 `Array.from` 通过迭代器读取，会把空位变成显式 `undefined`。

| 结果 | `Object.hasOwn(..., 1)` | 读取 `[1]` | 现存记录及 `owner` 是否仍共享 |
| --- | --- | --- | --- |
| `rows.slice()` | `false` | `undefined` | 是 |
| `[...rows]` | `true` | `undefined` | 是 |

~~~javascript
const slicedRows = rows.slice();
const spreadRows = [...rows];

Object.hasOwn(slicedRows, 1); // false：slice 保留这个空位
Object.hasOwn(spreadRows, 1); // true：展开写入显式 undefined
slicedRows[0] === rows[0]; // true：数组副本仍引用同一条记录
spreadRows[0].owner === rows[0].owner; // true：嵌套对象也共享
spreadRows[0].owner.name = "Grace";
rows[0].owner.name; // "Grace"：原数组仍可观察到同一对象的变化

const scoreRows = [{ score: 1 }];
const scoreCopy = [...scoreRows];
scoreCopy[0].score = 2;
scoreRows[0].score; // 2：副本中的对象仍与原数组共享
~~~

对象展开与数组展开使用不同的协议：数组展开消费迭代器，`Object.assign` 和对象展开读取自有可枚举属性。它们都只是浅复制；`Object.assign` 会调用目标对象的 `setter`，对象展开则直接定义新属性，见[JavaScript 值如何转换、比较，并成为属性键？](./javascript-types.md)。

`concat` 也返回浅复制的新数组，但它按 `Symbol.isConcatSpreadable` 决定是否展开参数，所以与数组展开并不总是等价：展开要求输入可迭代；`concat` 能展开设置了该符号的类数组对象，即使它不可迭代。

~~~javascript
const concatOnly = {
  0: "x",
  length: 1,
  [Symbol.isConcatSpreadable]: true,
};
[1].concat(concatOnly); // [1, "x"]
// [...concatOnly]; // TypeError：该对象没有迭代器
~~~

## 数组排序如何比较并处理原数组

`sort` 原地排序，不传比较函数时先把元素转成字符串再比较。自 ES2019 起规范要求排序稳定，即比较结果相等的元素保持原有相对顺序，前面的 `uniqueSorted` 就依赖这一点。`toSorted`（ES2023）使用相同的排序规则，但返回副本、不改原数组。要按数字大小排序，必须传入比较函数。

~~~javascript
[1, 11, 2].sort(); // [1, 11, 2]：默认按字符串比较
[1, 11, 2].toSorted((left, right) => left - right); // [1, 2, 11]：原数组不变
~~~

## flat、递归与逐层 concat 的空位结果

`flat(depth)` 返回展平后的新数组，默认只展平一层；`flat(Infinity)` 不设置展平层数上限，也不检测循环，应当用于无环的嵌套数组；极深嵌套仍可能超出引擎调用栈或资源限制。它会跳过被访问层级中原型链上也不存在的索引，不会递归展平 `Set` 之类的非数组可迭代对象。

~~~javascript
const sparseNested = [, [, 1]];
[].concat(...sparseNested); // [undefined, <1 empty item>, 1]
sparseNested.flat(Infinity); // [1]
~~~

`flat` 出现之前，常用 `[].concat(...items)` 展平一层。它的空位结果分两步产生：外层展开消费迭代器，把外层空位变成 `undefined`；`concat` 随后复制嵌套数组，又保留了其中的空位。

另一种旧写法是递归循环，它清楚展示了逐层展平的过程，但嵌套极深时可能耗尽调用栈。下面的实现按数字索引逐个读取，所以空位会变成 `undefined`，这也与 `flat` 不同。

~~~javascript
function flattenNested(items) {
  const result = [];
  function append(list) {
    for (let index = 0; index < list.length; index += 1) {
      const value = list[index];
      if (Array.isArray(value)) append(value);
      else result.push(value);
    }
  }
  append(items);
  return result;
}

flattenNested([1, [2, [3]], 4]); // [1, 2, 3, 4]
[1, [2, [3]], 4].flat(Infinity); // [1, 2, 3, 4]
~~~

还可以反复执行 `[].concat(...items)`，每轮展平一层，直到没有嵌套数组。这种写法可能超过引擎的实参数量限制，会反复复制大数组，空位行为也与 `flat` 不同；输入本来没有嵌套数组时，它直接返回原数组而不是副本。它只适用于无环、且嵌套数组能被 `concat` 默认展开的输入：如果某个嵌套数组设置了 `Symbol.isConcatSpreadable = false`，`some(Array.isArray)` 仍会发现它，`concat` 却不展开它，循环永远不会结束。

~~~javascript
function flattenByLevels(items) {
  while (items.some(Array.isArray)) items = [].concat(...items);
  return items;
}
~~~

需要复杂嵌套展平时，先确认期望的层数、空位语义和是否要保留输入身份；这些都是接口行为，不只是性能选择。

## 大数组求最大值时避免展开成大量实参

上一节的 `concat(...items)` 已经提到实参数量限制，求最大值时也有同样问题。`Math.max(...values)` 和 `Math.max.apply(null, values)` 都会把每个元素变成一个函数实参，输入很大时可能超过引擎允许的参数数量，具体阈值由实现决定。用循环每次只传两个参数，还能明确空数组和非法数值的处理方式。

~~~javascript
function maxOfNumbers(values) {
  let max = -Infinity;
  for (const value of values) {
    max = Math.max(max, value);
  }
  return max;
}

maxOfNumbers([]); // -Infinity
maxOfNumbers([7, NaN]); // NaN
maxOfNumbers([, 7]); // NaN：数组迭代器把空位读成 undefined
~~~

如果业务把空位视为不存在，应改用会跳过空位的遍历（如 `forEach` 或 `reduce`），并明确空输入时返回什么；遇到 `NaN` 等无效数值该怎样处理，也应由调用方决定。

> [!info]- 来源
> - 数组方法对缺失索引的读取、HasProperty、回调参数、concat、flat、展开复制与排序：[ECMAScript 2026 §23.1.3 Indexed Collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)。
> - `concat` 与 `Symbol.isConcatSpreadable` 的展开规则：[ECMAScript 2026 §23.1.3.2 Array.prototype.concat](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.concat)；稳定排序：[ECMAScript 2026 §23.1.3.30 Array.prototype.sort](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)。
> - `for...in` 与 `for...of` 的枚举和迭代规则：[ECMAScript 2026 §14.7.5](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements)；数组迭代器的索引读取：[§23.1.3.38](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.values)。
> - `Object.hasOwn` 只检查对象自有属性，不查原型链：[ECMAScript 2026 §20.1.2.14](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.hasown)，访问于 2026-11-12。
> - Set 去重、SameValueZero 与平均访问时间：[ECMAScript 2026 §24.1–24.2 Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)；[§7.2.10 SameValueZero](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-samevaluezero)。
> - Math.max 和实参处理：[ECMAScript 2026 §21.3.2.25](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.max)。
> - 本章代码核对：Node.js v26.13.0 / V8 14.6.202.34-node.40，2026-11-12。
