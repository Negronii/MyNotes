# JavaScript 数组操作如何处理空位、修改与复制？

2026 年 10 月月报导入两条 `reportId` 相同的记录：首条金额为 0，重试记录金额为 120；数组第二个位置刻意保留空位。本章先用这组报表行对照去重策略，再用短数组看空位、删除、排序与展平，在复制节回到 `rows` 和 `owner` 观察浅复制。选择哪条报表记录由业务规则决定：后文会比较 Map 保留最后一次写入与排序后保留组内首项的不同结果。

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

业务字段 `reportId` 相同，表示两条输入记录描述同一业务实体；`first` 与 `retry` 仍是两个对象。它们的 `owner` 字段也指向内容相同、身份不同的对象，后文用来说明浅复制共享嵌套对象。普通业务结果通常应使用稠密数组；这个空位用于辨别 JavaScript 操作的迭代契约。空位、显式 `undefined` 和数组迭代器返回的 `undefined` 不是同一个结构状态。

## 去重前先选“相同”的定义

对于原始值，`Set`（集合）按 `SameValueZero`（同值零）保留首次出现顺序。`NaN` 会和 `NaN` 合并，`+0` 与 `-0` 合并；对象按身份去重，字段相同但引用不同的对象仍会保留。相等规则和 `Map`（映射）/ `Set` 的键行为见[何时使用 Map、Set 或普通对象？](./map-and-set.md)。

~~~javascript
[...new Set([1, 1, NaN, NaN, -0, +0])]; // [1, NaN, 0]
[...new Set([{ id: 1 }, { id: 1 }])].length; // 2：对象身份不同
~~~

用 `indexOf` 过滤也能保留首次值，但 `indexOf` 使用严格相等，找不到 `NaN`；于是每个 `NaN` 都会因 `indexOf(NaN)` 返回 `-1` 而被过滤掉。`filter` 自身会跳过没有属性的位置。

~~~javascript
const values = [NaN, NaN, 1, 1];
values.filter((value, index) => values.indexOf(value) === index); // [1]
[...new Set(values)]; // [NaN, 1]
~~~

记录若按业务字段判重，用 `Map` 把字段映射到最后出现的对象。重复 `reportId` 的后一个对象替换值，而 `Map` 键的遍历位置仍取首次插入时的位置：

~~~javascript
function uniqueByReportId(items) {
  const byId = new Map();
  items.forEach(item => byId.set(item.reportId, item));
  return [...byId.values()];
}

uniqueByReportId(rows); // [retry]
~~~

这里使用 `forEach`，空位不会被当成一条记录；若输入可能包含显式 `undefined`，仍需在业务边界另行校验。重复项按 `reportId` 保留最后版本，是一个业务策略，不是 `Map` 自动推断出来的“对象相等”。

如果结果允许改变顺序，也可先排序副本，再对相邻项按同一业务等价关系去重。这个策略是“保留排序后每组首项”，不同于上面的 Map “保留最后一次写入”：当前输入的排序比较相等，稳定排序保留原顺序，所以结果会保留 `first`（金额 `0`），Map 结果则保留 `retry`（金额 `120`）。比较器必须把所有相等项排在一起；`same` 必须和 `compare` 表达同一组等价类。函数先用 `filter` 跳过普通空位；它假设原型链没有提供缺失索引，每个现存元素都是记录且不含显式 `undefined`，外部输入不满足时应先校验。

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

`filter` 已经创建稠密副本，`sort` 只改变这个副本的顺序；这段方法不会修改 `items`，无需再展开复制一次。当“保留首次顺序”重要时，不要用排序去重替代 Set 或 Map。

## 删除匹配项时，选择副本还是原地修改

若原数组还要给其他调用方使用，用 `filter` 返回新数组。下面两个写法分别展示直接检查排除列表，和排除列表较大时先建一次 `Set`；`includes` 与 `Set.has` 都按 `SameValueZero` 判断值，比较对象时按身份。这里的副本/原地差异按稠密数组说明；稀疏数组会产生另一种结果。

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

若调用方明确要求原地修改，可用 `splice`；删除后索引上的后续元素会左移，因此命中时不应递增索引。

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

连续多次 splice 可能让整体移动成本接近平方级；大批删除通常先构造结果或采用一次线性压缩实现。原地循环读取空位会得到 `undefined`，若排除列表含 `undefined`，该空位也会被当作命中项删除；filter 则不会为它调用回调。

## 空位怎样改变遍历结果

空位表示该索引没有自有属性；它不同于存在一个值为 `undefined` 的属性。多数数组回调方法用 `HasProperty`（属性存在性检查）检查索引，因此普通稀疏数组的空位会被跳过；若原型链上存在同索引属性，该属性也可能被访问。`find` 系列（查找方法）会按查找方向逐个读取索引，遇到第一个使回调返回真值的位置就立即停止；原型链没有同索引属性时，空位会以 `undefined` 传给回调。

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

数组回调中的索引存在性检查也会看到原型链上的属性，因此某个“空位”若继承到同索引值，就会被 `map` 等方法访问。`for...in` 枚举可枚举的字符串属性名，可能包含自定义或继承属性；`for...of` 消费数组迭代器，读出位置上的值，通常更适合数组数据。

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

`map` 和 `filter` 的回调都接收 `value`、`index`、`array`。把 `parseInt` 直接作为 `map` 回调会让索引被当作 `radix`；显式传入基数才能得到预期值。

~~~javascript
["1", "2", "3"].map(parseInt); // [1, NaN, NaN]
["1", "2", "3"].map(text => parseInt(text, 10)); // [1, 2, 3]
["1", "2", "3"].map(Number); // [1, 2, 3]
~~~

## 从迭代器或类数组输入创建数组

`Array.from` 可以消费可迭代对象，也可以按 `length` 和索引读取类数组对象；可选映射函数能在创建时转换元素。对没有继承索引的普通稀疏数组，迭代器读取空位得到 `undefined`，所以结果是稠密数组；如果原型链提供该索引，则读取继承值。数组展开也消费迭代器并产生同样的结果，但不能像 `Array.from` 一样处理只有 `length` 和索引的类数组对象。

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

数组展开和 `slice` 会创建新数组，但元素值仍是原来的对象引用；修改复制数组内的嵌套记录，原数组仍能观察到这次属性变更。对原型链没有同索引属性的普通稀疏数组，`slice` 和 `concat` 保留空位；展开与 `Array.from` 通过迭代读取时会把它变为 `undefined`。

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

对象展开与数组展开不是同一协议。数组展开消费迭代器；`Object.assign` 和对象展开读取自有可枚举属性。两者都只是浅复制，且对 `getter`、`setter` 的影响不同；见[JavaScript 值如何转换、比较，并成为属性键？](./javascript-types.md)。

`concat` 返回浅层新数组，还会检查 `Symbol.isConcatSpreadable`，所以数组展开与 `concat` 不总是等价：展开要求输入可迭代；`concat` 则可展开带有长度和索引的类数组对象。

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

`sort` 原地排序，默认按字符串形式比较；排序规范要求稳定，因此比较结果相等的元素仍保持原有相对顺序。ES2019 将稳定性要求纳入标准。`toSorted` 使用同类排序规则但返回副本；如要按数字升序，需传入比较函数。

~~~javascript
[1, 11, 2].sort(); // [1, 11, 2]：默认按字符串比较
[1, 11, 2].toSorted((left, right) => left - right); // [1, 2, 11]：原数组不变
~~~

## flat、递归与逐层 concat 的空位结果

`flat(depth)` 返回展平副本，默认只展平一层；`flat(Infinity)` 不设置展平层数上限，也不检测循环，应当用于无环的嵌套数组；极深嵌套仍可能超出引擎调用栈或资源限制。它会跳过被访问层级中原型链上也不存在的索引，不会递归展平 `Set` 之类的非数组可迭代对象。

~~~javascript
const sparseNested = [, [, 1]];
[].concat(...sparseNested); // [undefined, <1 empty item>, 1]
sparseNested.flat(Infinity); // [1]
~~~

旧式逐层 concat 的差别来自两步：外层展开消费迭代器，把没有继承值的外层空位变成 `undefined`；concat 随后浅复制嵌套数组时仍可保留其中空位。它还可能反复复制宽数组，或超过引擎的实参数量限制。

递归循环可清楚展示层级规则，但极深输入可能耗尽调用栈；这里按每个数值索引读取，因此没有继承同索引值时，空位变成 `undefined`，与 `flat` 不同。

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

迭代式 `[].concat(...items)` 每轮展平一层，可能命中参数数量限制、重复复制大数组，且空位行为与 `flat` 不同。如果输入没有嵌套数组，它会直接返回原输入，而非副本。循环只适用于无环、普通且嵌套数组可由 `concat` 默认展开的输入；若某个嵌套数组设置 `Symbol.isConcatSpreadable = false`，`some(Array.isArray)` 仍看到它，`concat` 却不展开它，循环将无法收敛。

~~~javascript
function flattenByLevels(items) {
  while (items.some(Array.isArray)) items = [].concat(...items);
  return items;
}
~~~

需要复杂嵌套展平时，先确认期望的层数、空位语义和是否要保留输入身份；这些都是接口行为，不只是性能选择。

## 大数组求最大值时避免展开成大量实参

`Math.max(...values)` 和 `Math.max.apply(null, values)` 都会把每个值变成一个函数实参。很大的输入可能超过引擎允许的参数数量，具体阈值由实现决定。循环每次只传固定数量参数，也能明示空数组和非法数值的策略。

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

如果业务把空位视为不存在，应使用会跳过空位的遍历并明确空输入结果；Number 无效值如何处理也应由调用方决定。

> [!info]- 来源
> - 数组方法对缺失索引的读取、HasProperty、回调参数、concat、flat、展开复制与排序：[ECMAScript 2026 §23.1.3 Indexed Collections](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)。
> - `concat` 与 `Symbol.isConcatSpreadable` 的展开规则：[ECMAScript 2026 §23.1.3.2 Array.prototype.concat](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.concat)；稳定排序：[ECMAScript 2026 §23.1.3.30 Array.prototype.sort](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)。
> - `for...in` 与 `for...of` 的枚举和迭代规则：[ECMAScript 2026 §14.7.5](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements)；数组迭代器的索引读取：[§23.1.3.38](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.values)。
> - `Object.hasOwn` 只检查对象自有属性，不查原型链：[ECMAScript 2026 §20.1.2.14](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.hasown)，访问于 2026-11-12。
> - Set 去重、SameValueZero 与平均访问时间：[ECMAScript 2026 §24.1–24.2 Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)；[§7.2.10 SameValueZero](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-samevaluezero)。
> - Math.max 和实参处理：[ECMAScript 2026 §21.3.2.25](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.max)。
> - 本章代码核对：Node.js v26.13.0 / V8 14.6.202.34-node.40，2026-11-12。
