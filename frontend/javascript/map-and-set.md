# 何时使用 Map、Set 或普通对象？

报表导入有一列是业务记录，有些记录可能重试；程序既要用 `Map`（映射）按 `reportId` 找最新值，也要为某个对象实例保存临时状态。选择数据结构前，先确定“相同”指什么、键需要什么类型，以及数据是否要按插入顺序遍历。对象字段与身份的比较规则见[JavaScript 值如何转换、比较，并成为属性键？](./javascript-types.md)。

用一次导入中的两条记录说明这些选择：

~~~javascript
const owner = { id: "u-17", name: "Ada" };
const first = { reportId: "r-104", amount: 0, owner };
const retry = {
  reportId: "r-104",
  amount: 120,
  owner: { id: "u-17", name: "Ada" },
};
~~~

两条记录的 `reportId` 和 `owner` 字段内容相同，但记录对象和 `owner` 对象的身份都不同。

## 先按数据形状选择

| 结构 | 适合的数据 | 键、成员与顺序 |
|---|---|---|
| `Map`（映射） | 任意键值对、对象身份键、需要直接遍历或 `size` | 键可以是任意值；按首次插入顺序遍历 |
| `Set`（集合） | 唯一成员或反复进行成员查询 | 按插入顺序保存；成员按相等规则去重 |
| `Array`（数组） | 有位置、重复项或要按索引访问的数据 | 每个位置独立，即使值相同也可重复 |
| 普通对象 | 固定字段的记录，或确实需要字符串 / `Symbol` 属性键的字典 | 其他键会先转成字符串或 `Symbol`；普通原型行为仍然存在 |

## Map 的键按值或身份匹配

`Map` 键可以是任意值。相同对象身份能查到原条目；字段完全相同但分别创建的两个对象是不同键。数字 `7` 和字符串 `"7"` 也不同。更新已有键只替换值，不移动其遍历位置；删除后重新插入才会移到末尾。

~~~javascript
const byId = new Map();
byId.set(7, { name: "Ada" });
byId.set("7", { name: "Grace" });

byId.get(7); // { name: "Ada" }
byId.has(8); // false
byId.size; // 2

const firstKey = { id: "r-104" };
const copiedKey = { id: "r-104" };
const byObject = new Map([[firstKey, "selected"], ["next", "another"]]);

byObject.get(copiedKey); // undefined：字段相同，身份不同
byObject.set(firstKey, "reviewed");
[...byObject.keys()]; // [firstKey, "next"]：更新不移动位置
byObject.delete(firstKey);
byObject.set(firstKey, "reselected"); // 删除后再插入，位于末尾
[...byObject.keys()]; // ["next", firstKey]
~~~

`Map` 使用 `SameValueZero`（同值零）：`NaN` 与 `NaN` 匹配，`+0` 与 `-0` 视为同一个键；对象则按身份匹配。常用操作是 `set`、`get`、`has`、`delete`、`clear` 和 `size`。`keys()`、`values()`、`entries()` 返回迭代器；默认迭代器产出 `[key, value]`；`forEach` 的参数顺序为 `(value, key, map)`。

`get(key)` 返回 `undefined` 既可能表示没有该键，也可能表示键存在且保存了 `undefined`；需要区分这两种状态时，再用 `has(key)`。

默认 `Map` 迭代器会产出键值对，因此可直接解构遍历：

~~~javascript
const byName = new Map([["ada", { name: "Ada" }], ["grace", { name: "Grace" }]]);
for (const [id, person] of byName) {
  console.log(id, person.name);
}
~~~

例如，两个输入对象可以描述同一个 `reportId`，但其对象身份仍不同。按业务 id 索引要把字段作为键；若要区分具体对象实例，则直接以对象作键：

~~~javascript
const rowById = new Map();
rowById.set(first.reportId, first);
rowById.set(retry.reportId, retry);

rowById.get("r-104") === retry; // true：后一次写入替换值
rowById.size; // 1

const metadataByRow = new Map([[first, { selected: true }]]);
metadataByRow.has(retry); // false：重试记录是另一个对象
~~~

## Set 按相等规则保留唯一值

`Set`（集合）保存唯一成员并按插入顺序遍历。删除后再次添加可以移动顺序。它也使用 `SameValueZero`（同值零），因此 `NaN` 只保留一次、有符号零合并，而两个对象即使字段相同仍是两个成员。

~~~javascript
const tags = new Set(["js", "runtime", "js"]);
tags.add("language");
tags.has("js"); // true
[...tags]; // ["js", "runtime", "language"]

const selectedRows = new Set([first, retry]);
selectedRows.size; // 2：对象身份不同
~~~

常用操作是 `add`、`has`、`delete`、`clear` 和 `size`。`keys()` 与 `values()` 产出相同成员；`entries()` 为 `Map` 兼容性产出 `[value, value]`；`forEach` 的参数为 `(value, value, set)`。

ECMAScript 2025 标准化 `Set` 的 `union`、`intersection`、`difference`、`symmetricDifference`、`isSubsetOf`、`isSupersetOf` 和 `isDisjointFrom`。参数可以是类 Set 对象：至少提供 `size`、`has()` 和 `keys()`；例如 `Map` 可按键参与这些运算。调用方法的接收者仍必须是 `Set`。面向旧运行时仍需检查支持。

~~~javascript
const enabled = new Set(["search", "export"]);
const available = new Set(["search", "export", "admin"]);

[...enabled.intersection(available)]; // ["search", "export"]
enabled.isSubsetOf(available); // true
~~~

## 普通对象仍适合固定字段与字典

记录 `{ reportId, amount, owner }` 的属性有固定名称时，用普通对象表达最清楚。若把对象当作任意键字典，必须记住属性键转换：对象键一般转成字符串，数字 `123` 和字符串 `"123"` 会撞到同一个属性；`Object.create(null)` 仅去掉继承原型，不会改变键转换。

~~~javascript
const dictionary = Object.create(null);
dictionary[123] = "number";
dictionary["123"]; // "number"

const record = { reportId: "r-104", amount: 0 };
Object.hasOwn(record, "amount"); // true
Object.hasOwn(record, "toString"); // false
~~~

`Object.hasOwn` 可区分自有和继承属性，也不会因对象覆盖了 `hasOwnProperty` 而失效。需要精确说明哪些属性可枚举、如何复制，请看[JavaScript 值如何转换、比较，并成为属性键？](./javascript-types.md#枚举与复制属性时先看-api-选中了什么)。

## 成本和生命周期也属于选择条件

规范要求 `Map`、`Set` 和弱集合的平均访问时间相对集合大小为次线性，但不规定具体哈希表或常数时间实现。总体成本还取决于外围算法：如果过滤 n 个数组项时每次都新建同一张查找表，建表成本会被重复支付。需要比较数组去重、批量移除和排序的结果时，见[数组操作怎样处理空位与复制？](./arrays.md)。

普通 `Map` 强持有键和值，`Set` 强持有成员，直到删除条目或集合自身不再可达。对象实例的元数据若不应延长键对象寿命，可考虑 `WeakMap`（弱映射）；它不提供遍历、`size` 或确定的清理时间，详见[弱集合与弱引用能保证什么？](./javascript-memory-weakmap-and-weakset.md)。

> [!info]- 来源
> - Map / Set 的插入顺序、SameValueZero 和集合运算：[ECMAScript 2026 §24.1–24.2](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - Map / Set 平均访问时间的规范下限：[ECMAScript 2026 §24.1–24.2 implementation requirements](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)；类 Set 参数的读取方式：[GetSetRecord](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-getsetrecord)。
> - SameValueZero 的定义：[ECMAScript 2026 §7.2.10](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-samevaluezero)。
> - 本章代码核对：Node.js v26.11.1 / V8 14.6.202.34-node.37，2026-11-06。
