# 数组、Map、Set 和普通对象怎样选，空位和去重有哪些坑？

本章回答：一组记录该放进数组、`Map`、`Set` 还是普通对象，以及数组里的空位、去重、删除、排序和展平各按什么规则处理。读者手上有前两章的行数据 `first`、`retry` 和带空位的 `rows`，还有主线一的 May、April 两行；读完应能为“按 `id` 去重”“为某个行对象记状态”“按日期排序”各选出结构，并预测每个数组方法遇到空位时的结果。

## 案例：重复的行与缺失的位置

沿用主线一的报表页和前两章的数据：

~~~javascript
const owner = { id: "u-17", name: "Ada" };
const first = { id: "r-104", amount: 0, owner };
const retry = { id: "r-104", amount: 120, owner: { id: "u-17", name: "Ada" } };
const rows = [first, , retry]; // 索引 1 是空位
~~~

`first` 和 `retry` 是同一行 `r-104` 的两次响应，页面最终只该显示一条；`rows` 中间缺了一个位置。实际业务数组通常是稠密的，这里留空位是为了看清各个操作怎样对待缺失的索引。排序部分改用主线一的两行：

~~~javascript
const records = [
  { id: "r-104", date: "2026-05-01", label: "May report" },
  { id: "r-103", date: "2026-04-01", label: "April report" },
];
~~~

## 选结构前先问三件事

1. **“相同”指什么？** 按值、按对象身份，还是按某个业务字段（如 `id`）？
2. **键是什么类型？** 只有字符串，还是数字、对象也要作键并保持区分？
3. **要不要按位置或插入顺序访问？** 是否允许重复项？

| 结构 | 适合的数据 | 键、成员与顺序 |
|---|---|---|
| `Array`（数组） | 有位置、允许重复、按索引访问的数据 | 每个位置独立，相同的值可以重复出现 |
| `Map`（映射） | 任意类型键的键值对、以对象身份作键、需要 `size` 或直接遍历 | 键按 SameValueZero 匹配；按首次插入顺序遍历 |
| `Set`（集合） | 唯一成员、频繁的成员查询 | 成员按 SameValueZero 去重；按插入顺序遍历 |
| 普通对象 | 字段固定的记录；键本来就是字符串或 Symbol 的字典 | 其他键先转成字符串；默认继承 `Object.prototype` 的属性 |

SameValueZero 是三种相等规则之一：`NaN` 等于自身，`+0` 与 `-0` 相同，对象只比身份，规则对照见[JavaScript 的值有哪些类型，“相等”又有几种？](values-types-and-equality.md#三种相等规则：===、Object.is%20与%20SameValueZero)。

案例的两类需求据此落到不同结构：页面要按 `id` 每行只留一条，用以 `id` 为键的 `Map`；要为某个具体行对象记“是否选中”，用以对象为键的 `Map`（或下文的 `WeakMap`）。

## 空位：没有元素、存了 undefined 与读出 undefined

先分清三件事：hole（空位）是该索引上根本没有自有属性；显式 `undefined` 是有属性、值为 `undefined`；读取空位时得到的 `undefined` 只是“查到原型链末端也没找到”的结果。三者读出来都是 `undefined`，结构上却不同。

数组方法按两类策略对待空位：

- **先检查再访问**：`map`、`filter`、`forEach`、`some`、`every`、`reduce` 等先用 `HasProperty` 检查索引是否存在，不存在就跳过。`HasProperty` 也查原型链，原型上若有同一索引，就会访问那个继承值。
- **直接按索引读或走迭代器**：`find` 系列、`for...of`、数组展开、`Array.from` 逐个读取索引，空位读成 `undefined`（原型链提供该索引时读到继承值）。

下表按没有继承索引属性的普通数组描述：

| 操作 | 遇到空位 | 改原数组？ |
|---|---|---|
| `map` | 跳过回调，结果对应位置仍是空位 | 否 |
| `filter` | 跳过，结果只含通过的现存值 | 否 |
| `forEach`、`some`、`every`、`reduce` | 不调用回调；`reduce` 无初始值且没有现存项时抛 `TypeError` | 否 |
| `find`、`findIndex`、`findLast`、`findLastIndex` | 按方向读取，空位以 `undefined` 传给回调，命中即停 | 否 |
| `for...of`、展开、`Array.from` | 走迭代器，空位读成 `undefined`，结果是稠密的 | 否 |
| `flat` | 被展平层级中的空位不写入结果 | 否 |
| `sort`、`reverse`、`splice` | 原地操作，稀疏结构可能改变 | 是 |
| `toSorted`、`toReversed`、`toSpliced`、`with` | 生成副本，空位写成显式 `undefined` | 否 |

~~~javascript
const sparse = [, "x"];

Object.hasOwn(sparse, 0);   // false：索引 0 没有自有属性
0 in sparse;                // false：原型链上也没有
sparse[0];                  // undefined
sparse.map(value => value); // [ <1 empty item>, "x" ]
sparse.filter(() => true);  // ["x"]

const visited = [];
sparse.find((value, index) => {
  visited.push(index);
  return value === undefined;
});
visited;                    // [0]：空位读成 undefined 后命中，find 随即停止

[...sparse];                // [undefined, "x"]
Object.keys(sparse);        // ["1"]
~~~

原型链能“补上”空位。下面第一段让原型提供索引 0；第二段对比 `for...in` 和 `for...of`：`for...in` 枚举可枚举的字符串属性名，会带上自定义属性和继承属性；`for...of` 按位置读值，遍历数组应该用它。

~~~javascript
const inheritedPrototype = Object.create(Array.prototype);
inheritedPrototype[0] = "from prototype";
const holeWithInheritedIndex = new Array(1);
Object.setPrototypeOf(holeWithInheritedIndex, inheritedPrototype);
Object.hasOwn(holeWithInheritedIndex, 0);   // false：仍没有自有索引 0
0 in holeWithInheritedIndex;                // true：原型链提供了它
holeWithInheritedIndex.map(value => value); // ["from prototype"]

const enumerableArray = [10, 20];
enumerableArray.note = "custom property";
const extraProperties = Object.create(Array.prototype);
extraProperties.label = "inherited property";
Object.setPrototypeOf(enumerableArray, extraProperties);

const keys = [];
for (const key in enumerableArray) keys.push(key);
keys;   // ["0", "1", "note", "label"]

const values = [];
for (const value of enumerableArray) values.push(value);
values; // [10, 20]
~~~

`some` 和 `every` 在答案确定后提前停止，也跳过空位。空数组上 `some` 为 `false`、`every` 为 `true`；全是空位的数组同理。业务若要求“全部满足且至少有一项”，要另判空：

~~~javascript
[].some(() => true);             // false
[].every(() => false);           // true
new Array(2).every(() => false); // true：两个空位都被跳过
~~~

## 去重先定义“相同”

对原始值，`Set` 按 SameValueZero 去重并保留首次出现的顺序；对象按身份去重：

~~~javascript
[...new Set([1, 1, NaN, NaN, -0, +0])];      // [1, NaN, 0]
[...new Set([{ id: 1 }, { id: 1 }])].length; // 2：两个对象
~~~

常见的 `filter` + `indexOf` 写法不等价：`indexOf` 用 `===`，`indexOf(NaN)` 永远返回 `-1`，所以每个 `NaN` 都被滤掉；`filter` 还会跳过空位。

~~~javascript
const values = [NaN, NaN, 1, 1];
values.filter((value, index) => values.indexOf(value) === index); // [1]
[...new Set(values)];                                             // [NaN, 1]
~~~

回到案例：`first` 和 `retry` 是两个对象，`Set` 会都留下。要按业务字段判重，就以 `id` 为键建 `Map`。重复的 `id` 让后来的记录替换旧值，但该键的遍历位置仍是首次插入时的位置：

~~~javascript
function uniqueById(items) {
  const byId = new Map();
  items.forEach(item => byId.set(item.id, item)); // forEach 跳过空位
  return [...byId.values()];
}

uniqueById(rows); // [retry]：保留最后一次写入
~~~

“同 `id` 保留最后一条”是本例的业务策略（重试结果更新），不是 `Map` 推断出来的对象相等。若要按版本号或时间决定哪条更新，必须先比较再决定是否 `set`。输入里若可能有显式 `undefined`，`forEach` 不会跳过它，要在边界另行校验。

结果允许改变顺序时，还可以先排序副本，让相同的记录相邻，再逐个比较相邻项。这个策略保留的是“排序后每组的第一项”。`sort` 是稳定排序，两条 `r-104` 比较结果相等，保持原来的先后，所以结果留下 `first`（金额 `0`），与 `Map` 策略留下 `retry`（金额 `120`）不同：

~~~javascript
function uniqueSorted(items, compare, same) {
  const result = [];
  const presentItems = items.filter(() => true); // 跳过空位，得到稠密副本
  for (const item of presentItems.sort(compare)) {
    if (result.length === 0 || !same(result[result.length - 1], item)) {
      result.push(item);
    }
  }
  return result;
}

const compareId = (left, right) =>
  left.id === right.id ? 0 : left.id < right.id ? -1 : 1;
const sameId = (left, right) => left.id === right.id;

uniqueSorted(rows, compareId, sameId).map(item => item.amount); // [0]
uniqueById(rows).map(item => item.amount);                      // [120]
~~~

`compare` 必须把所有算作重复的项排到一起，`same` 必须和 `compare` 认定同一批项相等。`filter` 已生成副本，`sort` 只重排这个副本，`items` 不受影响。函数假设每个现存元素都是记录、没有显式 `undefined`，外部输入不满足时先校验。需要保持原始出现顺序时，用 `Set` 或 `Map`，不要用排序去重。

## 删除匹配项：返回副本还是原地修改

原数组还要给别人用时，用 `filter` 返回新数组。排除值不多时直接 `includes`；排除列表大时先建 `Set`。`includes` 和 `Set.has` 都按 SameValueZero 比较：

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

长度为 n 的输入、m 个排除值时，第一种至多做 n×m 次比较；第二种建一次 `Set`，再逐项查询。规范只要求 `Set` 的平均访问时间相对集合大小是次线性的，不规定具体常数。按记录的业务 id 删除时，先从记录取出 id 再比较，不要拿一个“字段相同”的新对象去匹配。

调用方明确要求原地修改时，用 `splice`。删掉一个元素后，后面的元素左移一位，所以命中时索引不能加一，否则会漏检下一个：

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
~~~

每次 `splice` 都要移动后面的元素，大量删除时总成本可能接近平方级；批量删除时，先构造结果数组，或用双指针一次线性压缩。

稀疏数组上两种写法结果不同：`filter` 根本不为空位调用回调；按索引的循环把空位读成 `undefined`，排除列表里若有 `undefined`，空位也会被当成命中删掉。

~~~javascript
[, 1].filter(value => value !== 1);  // []：空位被跳过
removeInPlace([, 1], 1).length;      // 1：删掉 1，空位仍在
removeInPlace([, 1], undefined);     // [1]：空位读成 undefined，被删除
~~~

## 回调参数：map(parseInt) 为什么得到 NaN

`map`、`filter` 的回调都收到 `(value, index, array)` 三个参数。把 `parseInt` 直接传给 `map`，索引就被当成第二个参数 `radix`（进制）：`parseInt("1", 0)` 的进制 0 表示按默认规则，得到 `1`；`parseInt("2", 1)` 的进制 1 无效，得到 `NaN`；`parseInt("3", 2)` 里 `"3"` 不是二进制数字，也是 `NaN`。

~~~javascript
["1", "2", "3"].map(parseInt);                   // [1, NaN, NaN]
["1", "2", "3"].map(text => parseInt(text, 10)); // [1, 2, 3]
["1", "2", "3"].map(Number);                     // [1, 2, 3]
~~~

把任何多参数函数直接传给数组方法前，都要先确认它会怎样解读多出来的参数。

## 从可迭代对象或类数组创建数组

`Array.from` 既能消费可迭代对象，也能按 `length` 和数字索引读取 array-like object（类数组对象：有 `length` 和数字索引、但不是数组）。第二个参数是映射函数，在创建时转换元素。它读稀疏数组时走迭代器，结果是稠密的。数组展开也走迭代器，但不能处理不可迭代的类数组对象。

~~~javascript
Array.from(rows);                                // [first, undefined, retry]
Array.from(new Set(["paid", "review", "paid"])); // ["paid", "review"]
Array.from({ 0: "r-104", 1: "r-103", length: 2 }); // ["r-104", "r-103"]
Array.from({ length: 3 }, (_, index) => index * 2); // [0, 2, 4]
// [...{ 0: "r-104", length: 1 }];               // TypeError：不可迭代

Array(3);          // 长度为 3、全是空位的数组
Array.of(3);       // [3]：参数本身作为元素
Array.of(1, 2, 3); // [1, 2, 3]
~~~

DOM 查询返回的 `NodeList`、`HTMLCollection` 常用 `Array.from` 转成快照，见[怎样查询和修改 DOM，才拿到并改到预期的节点？](../browser/dom-queries-and-updates.md)；迭代协议本身见[迭代器和生成器怎样按需产出值，提前退出时怎样清理？](iterators-and-generators.md)。`Array.from(string)` 按 Unicode 码点拆分字符串，但用户感知的一个字符可能由多个码点组成，见[文本算法应按码元、码点还是字素簇处理？](../../engineering-foundations/computation/text-units-and-unicode.md)。

## 排序：默认按字符串比较

`sort` 原地排序。不传比较函数时，先把元素转成字符串再按 UTF-16 码元比较，所以数字排序必须传比较函数。`undefined` 一律排到最后，空位排在 `undefined` 之后。

~~~javascript
[1, 11, 2].sort();                        // [1, 11, 2]："11" < "2"
[10, 9, 1].sort();                        // [1, 10, 9]
[1, 11, 2].sort((left, right) => left - right); // [1, 2, 11]
[undefined, 3, , 1].sort();               // [1, 3, undefined, <1 empty item>]
~~~

自 ES2019 起规范要求排序稳定：比较结果相等的元素保持原有相对顺序，上一节的 `uniqueSorted` 就依赖这一点。ES2023 的 `toSorted` 用同样的规则，但返回副本、不改原数组。主线一的 `renderReports` 先写 `[...records]` 再 `sort`，正是为了不改 `records`；`toSorted` 一步做到：

~~~javascript
const oldest = records.toSorted((a, b) => a.date.localeCompare(b.date));
oldest.map(record => record.label); // ["April report", "May report"]
records.map(record => record.label); // ["May report", "April report"]：原数组不变
oldest[0] === records[1];            // true：只是新顺序，行对象仍共享
~~~

`date` 是 `YYYY-MM-DD` 格式的字符串，字典序与时间顺序一致，所以可以直接比较字符串。新数组只是行引用的新排列，改 `oldest[0]` 的属性，`records[1]` 也会变，这是浅复制的问题，见[复制一个对象到底复制了什么？](copying-and-object-graphs.md)。旧运行时是否支持 `toSorted`，见[用一个新 API 之前，怎样确认运行时真的支持？](feature-availability.md)；50,000 行排序的耗时怎样测，见[用户觉得慢时，怎样从指标走到证据？](../delivery/performance-metrics-and-diagnosis.md)。

## 展平：flat 与旧写法的空位差异

`flat(depth)` 返回展平后的新数组，默认展开一层；`flat(Infinity)` 不限层数，但不检测循环，只用于无环的嵌套数组，极深嵌套仍可能耗尽资源。它跳过被访问层级中的空位，也不展开 `Set` 等非数组可迭代对象。

`flat` 出现之前，常用 `[].concat(...items)` 展平一层。它的空位结果分两步产生：外层展开走迭代器，把外层空位变成 `undefined`；`concat` 复制嵌套数组时又保留了里面的空位。

~~~javascript
const sparseNested = [, [, 1]];
[].concat(...sparseNested);     // [undefined, <1 empty item>, 1]
sparseNested.flat(Infinity);    // [1]
[1, [2, [3]], 4].flat();        // [1, 2, [3], 4]
[1, [2, [3]], 4].flat(Infinity); // [1, 2, 3, 4]
~~~

另一种旧写法是递归循环。它按数字索引逐个读，空位变成 `undefined`，与 `flat` 不同；嵌套极深时可能耗尽调用栈：

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
flattenNested([, [, 1]]);        // [undefined, undefined, 1]
~~~

还可以反复执行 `[].concat(...items)`，每轮展平一层，直到没有嵌套数组：

~~~javascript
function flattenByLevels(items) {
  while (items.some(Array.isArray)) items = [].concat(...items);
  return items;
}
~~~

这种写法问题更多：每轮都复制整个数组，展开可能超过实参数量上限（见下一节），空位行为也与 `flat` 不同；输入本来没有嵌套时，它直接返回原数组而不是副本；某个嵌套数组若设了 `Symbol.isConcatSpreadable = false`，`some(Array.isArray)` 仍会发现它，`concat` 却不展开，循环永远不会结束。

展平的层数、空位语义和是否返回新数组都是接口行为，选写法前先定下来。

## 大数组不要展开成实参

`Math.max(...values)` 和 `Math.max.apply(null, values)` 都把每个元素变成一个函数实参。实参数量有引擎上限，数组很大时会抛 `RangeError`；阈值取决于引擎和栈大小，在 Node.js v26.13.1 下 120,000 个元素还能通过、150,000 个就抛错。用循环每次只传两个参数，还能写明空数组和非法值的处理：

~~~javascript
function maxOfNumbers(values) {
  let max = -Infinity;
  for (const value of values) {
    max = Math.max(max, value);
  }
  return max;
}

maxOfNumbers([]);        // -Infinity
maxOfNumbers([7, NaN]);  // NaN
maxOfNumbers([, 7]);     // NaN：迭代器把空位读成 undefined，转成数字是 NaN
~~~

业务若把空位视为不存在，就改用跳过空位的遍历（`forEach` 或 `reduce`）；空输入返回什么、遇到 `NaN` 怎么办，由调用方决定。`[].concat(...items)`、`push(...items)` 也有同样的上限。

## Map：键按 SameValueZero 匹配，位置按首次插入

`Map` 的键可以是任意值。数字 `7` 和字符串 `"7"` 是两个键；同一个对象作键能查回条目，字段相同但分别创建的对象是两个键。`NaN` 能作键并被查回，`+0` 和 `-0` 是同一个键。更新已有键只替换值，不改变遍历位置；删除后再插入，才移到末尾。

~~~javascript
const byId = new Map();
byId.set(7, { name: "Ada" });
byId.set("7", { name: "Grace" });
byId.get(7);  // { name: "Ada" }
byId.size;    // 2

const firstKey = { id: "r-104" };
const copiedKey = { id: "r-104" };
const byObject = new Map([[firstKey, "selected"], ["next", "another"]]);

byObject.get(copiedKey);          // undefined：字段相同，身份不同
byObject.set(firstKey, "reviewed");
[...byObject.keys()];             // [firstKey, "next"]：更新不移动位置
byObject.delete(firstKey);
byObject.set(firstKey, "reselected");
[...byObject.keys()];             // ["next", firstKey]：删后再插，位于末尾
~~~

常用操作是 `set`、`get`、`has`、`delete`、`clear` 和 `size`。`keys()`、`values()`、`entries()` 返回迭代器；默认迭代器产出 `[key, value]`，可以直接解构；`forEach` 的回调参数顺序是 `(value, key, map)`，与解构顺序相反。

`get(key)` 返回 `undefined` 时，可能是没有这个键，也可能是键存在且存了 `undefined`；要区分就用 `has`：

~~~javascript
const optionalValue = new Map([["cached", undefined]]);
[optionalValue.get("cached"), optionalValue.has("cached")];   // [undefined, true]
[optionalValue.get("missing"), optionalValue.has("missing")]; // [undefined, false]
~~~

回到案例的两类需求：

~~~javascript
const rowById = new Map();
rowById.set(first.id, first);
rowById.set(retry.id, retry);
rowById.get("r-104") === retry; // true：后一次写入替换值
rowById.size;                   // 1

const metadataByRow = new Map([[first, { selected: true }]]);
metadataByRow.has(retry);       // false：重试记录是另一个对象
~~~

## Set：成员语义与 ES2025 集合运算

`Set` 保存不重复的成员，按插入顺序遍历；删除后再添加，成员移到末尾。它同样用 SameValueZero 判重：

~~~javascript
const tags = new Set(["js", "runtime", "js"]);
tags.add("language");
[...tags];                                  // ["js", "runtime", "language"]
[...new Set([first.id, retry.id])];         // ["r-104"]：按业务 ID
new Set([first, retry]).size;               // 2：按对象身份
~~~

常用操作是 `add`、`has`、`delete`、`clear` 和 `size`。`keys()` 与 `values()` 产出相同成员；`entries()` 为了和 `Map` 兼容，产出 `[value, value]`；`forEach` 的参数是 `(value, value, set)`。

ECMAScript 2025 给 `Set` 加了集合运算：`union`（并）、`intersection`（交）、`difference`（差）、`symmetricDifference`（对称差）、`isSubsetOf`、`isSupersetOf`、`isDisjointFrom`。调用方法的对象（接收者）必须是真正的 `Set`；参数可以是 set-like object（类 Set 对象），但必须提供三个成员：

- `size`：转成数值后为 `NaN` 抛 `TypeError`，为负数抛 `RangeError`；
- `has(value)`：判断成员，不可调用抛 `TypeError`；
- `keys()`：返回带 `next` 方法的迭代器，不可调用抛 `TypeError`。

所以数组不能直接作参数：它能被 `for...of` 遍历，却没有 `size` 和 `has`。`Map` 满足这组接口，按键参与运算。

~~~javascript
const enabled = new Set(["search", "export"]);
const available = new Set(["search", "export", "admin"]);
[...enabled.intersection(available)]; // ["search", "export"]
enabled.isSubsetOf(available);        // true

const availableByName = new Map([["search", true], ["admin", true]]);
[...enabled.intersection(availableByName)]; // ["search"]：按 Map 的键

const requestedInOrder = new Set(["review", "export", "search"]);
const supported = new Set(["export", "review"]);
[...requestedInOrder.intersection(supported)]; // ["export", "review"]

const sameSizeRequest = new Set(["review", "export"]);
[...sameSizeRequest.intersection(supported)];  // ["review", "export"]

const arrayAsKeys = {
  size: 2,
  has(value) { return supported.has(value); },
  keys() { return ["export", "review"]; }, // 返回数组，不是迭代器
};
// requestedInOrder.intersection(arrayAsKeys); // TypeError
~~~

结果顺序取决于算法遍历哪一侧。`intersection` 遍历较小的一侧：接收者成员数不大于参数的 `size` 时，按接收者顺序逐个用参数的 `has` 检查；接收者更大时，改按参数 `keys()` 的顺序检查。所以 `requestedInOrder`（3 个）与 `supported`（2 个）求交按 `supported` 的顺序产出；两个同为 2 个成员的集合求交按接收者顺序。`arrayAsKeys` 报告的 `size` 为 2，小于接收者的 3，算法于是调用它的 `keys()`，因返回值不是迭代器而抛错。结果顺序要用于展示时，显式排序。

> [!info] 支持情况（MDN，核对于 2026-11-17）
> Set 运算方法自 2024 年 6 月起在主流浏览器当前版本中可用（Chrome 122、Firefox 127、Safari 17）。面向更旧的运行时，先按[用一个新 API 之前，怎样确认运行时真的支持？](feature-availability.md)的方法确认。

## 普通对象作字典

像 `{ id, amount, owner }` 这样字段固定的记录，用普通对象最清楚。拿它当字典时要记住两点。第一，键会先转成字符串或 Symbol：`123` 和 `"123"` 是同一个属性，两个不同的行对象会撞在 `"[object Object]"` 上，无法转成原始值的对象作键会抛 `TypeError`，规则见[读写一个属性时，JavaScript 沿什么规则查找、落在哪里？](objects-properties-and-prototypes.md#属性键只有字符串和%20Symbol)。第二，默认继承 `Object.prototype` 的属性，`"toString" in dictionary` 为 `true`。

不想要继承键时，用 `Object.create(null)` 创建字典，用 `Object.hasOwn` 检查自有属性；它不受对象覆盖 `hasOwnProperty` 或没有原型的影响。去掉原型不改变键转换规则。

遍历顺序也与 `Map` 不同：`Object.keys` 先按数值升序列出数组索引形式的键，再按创建顺序列出其他字符串键，且不列 Symbol 键：

~~~javascript
const orderedObject = {};
orderedObject.z = "created first";
orderedObject["10"] = "index ten";
orderedObject["2"] = "index two";
Object.keys(orderedObject); // ["2", "10", "z"]
~~~

所以用对象存 `{ "104": row, "103": row }` 这样以数字形式 ID 为键的字典时，遍历顺序是数值顺序，不是插入顺序。处理结果依赖插入顺序时，用 `Map`。

## 成本与生命周期也是选择条件

规范要求 `Map`、`Set` 和弱集合的平均访问时间相对集合大小是次线性的，但不规定必须用哈希表或做到常数时间。总成本还取决于外围算法：过滤 n 项时若每一项都重建一张同样的查找表，建表成本就付了 n 次。

`Map` 强引用当前条目的键和值，`Set` 强引用当前成员：只要集合可达，这些对象就不会被回收。替换某个键的值后，旧值不再被集合引用；删除条目也会解除引用。为对象记的元数据若不该延长对象的寿命，用 `WeakMap`（弱映射）；它不提供遍历、`size`，也没有确定的清理时间，见[对象什么时候能被回收，弱引用能帮什么、不能帮什么？](memory-reachability-and-weak-references.md)。

## Lodash 实例：先看返回值和是否修改输入

> [!info] 版本
> 本节以 Lodash 4.18.1（2026-04-01 发布）为准，示例在 npm 安装的 4.18.1 上复跑于 2026-11-26。

前面的原生规则讲清后，Lodash 的数组方法可以按同样两个问题检查：返回新数组还是原数组，判等和空位按什么规则。

`_.orderBy` 按指定字段和方向返回新数组，不改输入；`_.sortBy` 同样返回新数组，只按升序。和 `toSorted` 一样，新数组只是行引用的新顺序：

~~~javascript
const oldest = _.orderBy(records, ["date"], ["asc"]);
oldest.map(record => record.label);  // ["April report", "May report"]
records.map(record => record.label); // ["May report", "April report"]
oldest[0] === records[1];            // true：仍共享 April 行对象
~~~

报表页的排序方式由 URL 的 `sort` 决定。组件拿到完整数据时才适合本地排序；客户端只拿到分页中的一页时，本地排序只排了这一页，得不到正确的整体顺序。排序状态归谁，见[一份界面状态该由谁持有？](../ui-state/state-ownership-and-composition.md)。

| 方法 | 契约 |
|---|---|
| `_.uniq(array)` | 返回保留首次出现顺序的新数组，按 SameValueZero 判等，`_.uniq([1, 1, NaN, NaN, -0, 0])` 为 `[1, NaN, 0]`；只要原生值去重时，`[...new Set(array)]` 同样清楚 |
| `_.compact(array)` | 返回去掉所有假值的新数组，包括 `0`、`false`、`""`、`NaN`；清理指标数组时会删掉合法的 `0`。行对象本身是真值，不会因字段为 `0` 被删 |
| `_.keys(object)` | 普通对象返回自有可枚举字符串键；稀疏数组会把空位也列为索引，`_.keys([, "April"])` 为 `["0", "1"]`，而 `Object.keys` 只给 `["1"]` |
| `_.concat(array, ...values)` | 返回浅拼接的新数组；传入的数组只展开一层，`_.concat([1], [2, [3]], 4)` 为 `[1, 2, [3], 4]` |
| `_.drop(array, n = 1)` | 返回去掉前 `n` 项的新切片 |
| `_.find(collection, predicate, fromIndex = 0)` | 返回第一条匹配项，不返回全部匹配行 |
| `_.each(collection, iteratee)` | 遍历后返回原集合本身；`_.forEach` 是别名，不能当作变换后的新列表 |
| `_.times(n, iteratee)` | 调用 `iteratee` n 次并返回结果数组 |
| `_.uniqueId(prefix)` | 只用当前 Lodash 模块实例里的递增计数器（`row-1`、`row-2`……）；受先前调用影响，跨进程或多份模块不保证唯一，也不是安全令牌。列表行用服务端稳定的 `id` |

路径明确时，原生的可选链、`flat`、`Set`、`toSorted` 或对象展开通常更易读。按方法导入能帮构建器裁剪依赖，但最终包体还受模块格式和构建配置影响，要用生产产物测量，见[构建器怎样把源码变成可部署的文件？](../delivery/build-pipeline-and-bundling.md)。Lodash 的 `_.debounce` 见[怎样包装一个函数而不弄丢参数、this 和结果？](wrapping-functions.md)。

## 选好集合之后：副本里到底有什么

本章为案例选定了结构：按 `id` 去重用 `Map`，保留最后一次写入；为行对象记状态用以对象为键的 `Map` 或 `WeakMap`；排序用带比较函数的 `toSorted`，不改原数组。空位在“先检查”的方法里被跳过，在走迭代器的写法里变成 `undefined`。

多处结果都提醒了同一件事：`toSorted`、`orderBy`、`filter` 返回的新数组仍共享原来的行对象。下一章接着问：复制一个对象或数组时，究竟哪些节点是新的、哪些仍然共享？见[复制一个对象到底复制了什么？](copying-and-object-graphs.md)。

> [!info]- 来源
> - 数组方法对缺失索引的处理（`HasProperty` 检查、`find` 系列直接读取）、回调参数、`concat`、`flat`、`toSorted` 等副本方法（“空位”“回调参数”“展平”）：[ECMAScript 2026 §23.1.3 Properties of the Array Prototype Object](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)，含 [§23.1.3.2 concat](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.concat)、[§23.1.3.13 flat](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.flat)、[§23.1.3.34 toSorted](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.tosorted)。
> - 排序的默认字符串比较、稳定性、`undefined` 与空位的放置（“排序”）：[ECMAScript 2026 §23.1.3.30 Array.prototype.sort 与 §23.1.3.30.1 SortIndexedProperties](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)。
> - `for...in` 与 `for...of` 的枚举与迭代（“空位”）：[ECMAScript 2026 §14.7.5](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements)；数组迭代器按索引读取：[§23.1.3.38 Array.prototype.values](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.values)；`Object.hasOwn` 只查自有属性：[§20.1.2.14](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.hasown)，访问于 2026-11-12。
> - `Array.from`、`Array.of`（“从可迭代对象或类数组创建数组”）：[ECMAScript 2026 §23.1.2.1、§23.1.2.4](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.from)。
> - `Math.max` 的实参处理（“大数组不要展开成实参”）：[ECMAScript 2026 §21.3.2.25](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-math.max)；120,000 / 150,000 元素的阈值为本轮在 Node.js v26.13.1 / V8 14.6.202.34-node.40 实测，2026-11-26。
> - `Map`/`Set` 的键与成员比较、遍历顺序、平均次线性访问要求，以及强集合与弱集合的引用边界（“Map”“Set”“成本与生命周期”）：[ECMAScript 2026 §24.1–24.4 Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)；[§7.2.10 SameValueZero](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-samevaluezero)。
> - Set 运算与 set-like 参数契约、`intersection` 遍历较小一侧（“Set：成员语义与 ES2025 集合运算”）：[ECMAScript 2025 §24.2.1.2 GetSetRecord、§24.2.4.5–24.2.4.16](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-getsetrecord)、[§24.2.4.9 Set.prototype.intersection](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-set.prototype.intersection)。
> - Set 运算的浏览器支持（Chrome 122、Firefox 127、Safari 17，2024 年 6 月起 Baseline Newly available）：[MDN Set.prototype.intersection](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set/intersection)，核对于 2026-11-17。
> - 普通对象键顺序与键转换（“普通对象作字典”）：[ECMAScript 2026 §10.1.11.1 OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys)、[§20.1.2.19 Object.keys](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.keys)、[§7.1.19 ToPropertyKey](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-topropertykey)。
> - Lodash 方法契约（“Lodash 实例”）：[Lodash 4.18.1 release](https://github.com/lodash/lodash/releases/latest)（发布于 2026-04-01）、[Lodash 4.18.1 API 文档](https://github.com/lodash/lodash/blob/4.18.1/doc/README.md)、[稀疏数组键枚举实现](https://github.com/lodash/lodash/blob/4.18.1/lodash.js#L2430)，原稿核验 2026-11-12；本轮复跑 2026-11-26。
> - 本章其余示例在 Node.js v26.13.1 / V8 14.6.202.34-node.40 复跑，2026-11-26；原稿核对环境为 Node.js v26.13.0，2026-11-12。
