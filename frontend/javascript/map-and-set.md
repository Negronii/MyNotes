# 何时使用 Map、Set 或普通对象？

报表导入按输入顺序逐条读取业务记录；同一个 `reportId` 可能出现重试。程序既要用 `Map`（映射）保留同一 `reportId` 最后读到的记录，也要为某个对象实例保存临时状态。选择数据结构前，先确定“相同”指什么、键需要什么类型，以及数据是否要按插入顺序遍历。对象字段与身份的比较规则见[JavaScript 值如何转换、比较，并成为属性键？](./javascript-types.md)。

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

后文的覆盖策略只保留输入顺序最后读到的一条；若业务要比较事件时间或版本号，必须先按该规则判断是否覆盖，`Map.set` 不会自行判断哪条记录更新。

## 先按数据形状选择

| 结构 | 适合的数据 | 键、成员与顺序 |
|---|---|---|
| `Map`（映射） | 任意键值对、对象身份键、需要直接遍历或 `size` | 键可以是任意值；按首次插入顺序遍历 |
| `Set`（集合） | 唯一成员或反复进行成员查询 | 按插入顺序保存；成员按相等规则去重 |
| `Array`（数组） | 有位置、重复项或要按索引访问的数据 | 每个位置独立，即使值相同也可重复 |
| 普通对象 | 固定字段的记录，或确实需要字符串 / `Symbol` 属性键的字典 | 其他输入需先转换成字符串或 `Symbol`，转换也可能抛错；普通原型行为仍然存在 |

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

~~~javascript
const optionalValue = new Map([["cached", undefined]]);
[optionalValue.get("cached"), optionalValue.has("cached")]; // [undefined, true]
[optionalValue.get("missing"), optionalValue.has("missing")]; // [undefined, false]
~~~

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
rowById.get("r-104") === first; // true：此时记录的是首条输入
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

const specialNumbers = new Set([NaN, NaN, -0, +0]);
[...specialNumbers]; // [NaN, 0]：NaN 去重，零合并

const importedIds = new Set([first.reportId, retry.reportId]);
[...importedIds]; // ["r-104"]：按业务 ID 去重

const selectedRows = new Set([first, retry]);
selectedRows.size; // 2：对象身份不同
~~~

常用操作是 `add`、`has`、`delete`、`clear` 和 `size`。`keys()` 与 `values()` 产出相同成员；`entries()` 为 `Map` 兼容性产出 `[value, value]`；`forEach` 的参数为 `(value, value, set)`。

ECMAScript 2025 标准化 `Set` 的 `union`、`intersection`、`difference`、`symmetricDifference`、`isSubsetOf`、`isSupersetOf` 和 `isDisjointFrom`。运算接收者必须是真正的 `Set`；另一侧可用类 Set 对象（Set-like object），但要遵守成员接口：`size` 报告成员数，`has(value)` 判断成员，`keys()` 返回逐个产出成员的迭代器。

规范先把 `size` 转成数值，若为 `NaN` 就抛 `TypeError`；其余数值转为整数或无穷，结果为负就抛 `RangeError`。仅能被 `for...of` 读取的数组不满足这个接口，数组也没有成员语义所需的 `size` 和 `has`；而 `keys()` 直接返回一个数组也不行，因为该算法要求它返回迭代器对象。`Map` 满足这组接口并按键参与运算。面向旧运行时仍需检查支持。

~~~javascript
const enabled = new Set(["search", "export"]);
const available = new Set(["search", "export", "admin"]);

[...enabled.intersection(available)]; // ["search", "export"]
enabled.isSubsetOf(available); // true

const availableByName = new Map([["search", true], ["admin", true]]);
[...enabled.intersection(availableByName)]; // ["search"]：按 Map 的键判断

const requestedInOrder = new Set(["review", "export", "search"]);
const supported = new Set(["export", "review"]);
[...requestedInOrder.intersection(supported)]; // ["export", "review"]

const sameSizeRequest = new Set(["review", "export"]);
const sameSizeSupport = new Set(["export", "review"]);
[...sameSizeRequest.intersection(sameSizeSupport)]; // ["review", "export"]：同大小时按接收者顺序

const arrayAsKeys = {
  size: 2,
  has(value) { return supported.has(value); },
  keys() { return ["export", "review"]; },
};
try {
  requestedInOrder.intersection(arrayAsKeys);
} catch (error) {
  error.name; // "TypeError"：keys() 返回的是数组，不是迭代器对象
}
~~~

`intersection` 根据接收者大小与参数 `size` 报告值选择迭代来源：接收者大小小于或等于该值时按接收者顺序检查；接收者较大时按参数 `keys()` 的成员迭代器顺序检查。因此结果 Set 的插入顺序不一定沿用接收者。三对二的例子按 `supported` 的顺序产生；同大小的例子按接收者顺序产生。若结果顺序用于展示，应显式确定排序规则。

## 普通对象仍适合固定字段与字典

记录 `{ reportId, amount, owner }` 的属性有固定名称时，用普通对象表达最清楚。属性键只能是字符串或 `Symbol`；把数字或对象等其他值放在方括号中时，JavaScript 会先执行属性键转换。数字 `123` 和字符串 `"123"` 因而会撞到同一个属性；若对象无法转换成原始值，访问会抛 `TypeError`。`Object.create(null)` 仅去掉继承原型，不会改变键转换。

~~~javascript
const dictionary = Object.create(null);
dictionary[123] = "number";
dictionary["123"]; // "number"

const record = { reportId: "r-104", amount: 0 };
Object.hasOwn(record, "amount"); // true
Object.hasOwn(record, "toString"); // false

function lookupDictionary(key) {
  try {
    return dictionary[key];
  } catch (error) {
    return error.name;
  }
}
lookupDictionary(Object.create(null)); // "TypeError"：对象键无法转换成原始值
~~~

`Object.hasOwn` 可区分自有和继承属性，也不会因对象覆盖了 `hasOwnProperty` 而失效。需要精确说明哪些属性可枚举、如何复制，请看[JavaScript 值如何转换、比较，并成为属性键？](./javascript-types.md#枚举与复制属性时，先看%20API%20选中了什么)。

属性遍历顺序也与 `Map` 不同：`Object.keys` 先按数值顺序列出可枚举的自有数组索引键，再按创建顺序列出其他可枚举的自有字符串键；它不列 `Symbol` 键。若用对象表达字典，且处理结果依赖插入顺序，先确认代码实际采用的枚举 API 和键类型。

~~~javascript
const orderedObject = {};
orderedObject.z = "created first";
orderedObject["10"] = "index ten";
orderedObject["2"] = "index two";
Object.keys(orderedObject); // ["2", "10", "z"]
~~~

## 成本和生命周期也属于选择条件

规范要求 `Map`、`Set` 和弱集合的平均访问时间相对集合大小为次线性，但不规定具体哈希表或常数时间实现。总体成本还取决于外围算法：如果过滤 n 个数组项时每次都新建同一张查找表，建表成本会被重复支付。需要比较数组去重、批量移除和排序的结果时，见[数组操作怎样处理空位与复制？](./arrays.md)。

普通 `Map` 强持有当前条目中的键和值，`Set` 强持有当前成员。用 `Map.set` 替换已有键对应的值后，`Map` 不再因此持有被替换的旧值；删除条目也会解除该条目的持有。集合自身不再可达时，也不会仅靠内部引用让整个集合永久存活。对象实例的元数据若不应延长键对象寿命，可考虑 `WeakMap`（弱映射）；它不提供遍历、`size` 或确定的清理时间，详见[弱集合与弱引用能保证什么？](./javascript-memory-weakmap-and-weakset.md)。

> [!info]- 来源
> - Map / Set 可接受的键、成员比较、遍历与平均次线性访问要求：[ECMAScript 2026 §§24.1–24.2](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - `SameValueZero` 的定义：[ECMAScript 2026 §7.2.10](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-samevaluezero)。
> - Set 运算和 Set-like 参数契约：[ECMAScript 2025 §§24.2.1.2、24.2.4.5–24.2.4.16](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-getsetrecord)；`intersection` 按较小一侧遍历：[§24.2.4.9](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-set.prototype.intersection)。
> - 普通对象自有键顺序与 `Object.keys` 的筛选范围：[ECMAScript 2026 §10.1.11.1](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys) 与 [§20.1.2.19](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.keys)。
> - 普通对象属性键转换为字符串或 `Symbol`：[ECMAScript 2026 §7.1.19 `ToPropertyKey`](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-topropertykey)；强集合与弱集合的键值及可观察边界：[§§24.1–24.4](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - 本章代码核对：Node.js v26.13.0 / V8 14.6.202.34-node.40，2026-11-12。
