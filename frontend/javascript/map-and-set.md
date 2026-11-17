# 何时使用 Map、Set 或普通对象？

**案例背景：**报表导入按输入顺序逐条读取业务记录，同一个 `reportId` 可能因重试出现多次。程序有两类需求：按 `reportId` 只保留最后读到的那条记录；以及为某个具体的记录对象保存临时状态（例如是否被选中）。选择数据结构前，先确定三件事：“相同”指什么、键需要什么类型、是否要按插入顺序遍历。对象字段与身份的比较规则见[JavaScript 值如何转换、比较，并成为属性键？](./javascript-types.md)。

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

两条记录的 `reportId` 相同，`owner` 字段内容也相同，但两条记录是不同的对象，两个 `owner` 也是不同的对象。

后文的覆盖策略是“按输入顺序，后读到的覆盖先读到的”。若业务要按事件时间或版本号决定哪条更新，必须先自行比较再决定是否写入，`Map.set` 不会替你判断。

## 先按数据形状选择

| 结构 | 适合的数据 | 键、成员与顺序 |
|---|---|---|
| `Map`（映射） | 任意键值对、对象身份键、需要直接遍历或 `size` | 键可以是任意值；按首次插入顺序遍历 |
| `Set`（集合） | 唯一成员或反复进行成员查询 | 按插入顺序保存；成员按相等规则去重 |
| `Array`（数组） | 有位置、重复项或要按索引访问的数据 | 每个位置独立，即使值相同也可重复 |
| 普通对象 | 固定字段的记录，或键本来就是字符串 / `Symbol` 的字典 | 其他类型的键会先被转换成字符串或 `Symbol`，转换还可能抛错；默认继承 `Object.prototype` 上的属性 |

## Map 的键按值或身份匹配

`Map` 的键可以是任意值。用同一个对象作键能查到原条目；字段完全相同、但分别创建的两个对象是两个不同的键。数字 `7` 和字符串 `"7"` 也是不同的键。更新已有键只替换值，不改变它的遍历位置；删除后重新插入，才会移到末尾。

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

`Map` 用 `SameValueZero`（同值零）规则比较键：`NaN` 与 `NaN` 匹配，`+0` 与 `-0` 视为同一个键，对象按身份匹配。常用操作是 `set`、`get`、`has`、`delete`、`clear` 和 `size`。`keys()`、`values()`、`entries()` 返回迭代器；默认迭代器产出 `[key, value]`；`forEach` 的参数顺序为 `(value, key, map)`。

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

回到导入案例的两类需求：按业务 ID 保留最后一条记录时，用 `reportId` 字段作键；为具体记录对象保存状态时，直接用对象作键：

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

`Set` 保存不重复的成员，按插入顺序遍历；删除后再添加，成员会移到末尾。它同样用 `SameValueZero` 判断重复，因此 `NaN` 只保留一次，`+0` 与 `-0` 合并，而两个字段相同的对象仍是两个成员。

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

ECMAScript 2025 为 `Set` 加入了集合运算方法：`union`（并）、`intersection`（交）、`difference`（差）、`symmetricDifference`（对称差）、`isSubsetOf`、`isSupersetOf` 和 `isDisjointFrom`。调用方法的对象（接收者）必须是真正的 `Set`；参数可以是 Set-like object（类 Set 对象），但必须提供三个成员：`size` 报告成员数，`has(value)` 判断成员，`keys()` 返回逐个产出成员的迭代器。

规范会先检查这个接口：`size` 转成数值后为 `NaN` 就抛 `TypeError`，为负数就抛 `RangeError`；`has` 或 `keys` 不可调用也抛 `TypeError`。所以数组不能直接作参数：它虽然可用 `for...of` 遍历，却没有 `size` 和 `has`。`keys()` 直接返回数组也不行，算法要求它返回带 `next` 方法的迭代器对象。`Map` 满足这组接口，按键参与运算。这些方法自 2024 年起已在主流浏览器的当前版本中可用，面向旧运行时仍需检查支持。

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

上例的结果顺序有讲究。`intersection` 会遍历较小的一侧：接收者的成员数小于或等于参数的 `size` 时，按接收者顺序逐个用参数的 `has` 检查；接收者较大时，改按参数 `keys()` 的顺序逐个检查。所以结果的顺序不一定沿用接收者：`requestedInOrder`（3 个成员）与 `supported`（2 个成员）求交时按 `supported` 的顺序产出，两个同为 2 个成员的集合求交时按接收者顺序产出。最后的 `arrayAsKeys` 报告 `size` 为 2，小于接收者的 3，因此算法会调用它的 `keys()`，并因返回值不是迭代器而抛错。若结果顺序用于展示，应显式排序。

## 普通对象仍适合固定字段与字典

像 `{ reportId, amount, owner }` 这样字段名固定的记录，用普通对象表达最清楚。普通对象的属性键只能是字符串或 `Symbol`；把数字、对象等其他值放进方括号时，JavaScript 会先把它转换成属性键。因此数字 `123` 和字符串 `"123"` 会落到同一个属性上；对象若无法转换成原始值，访问会抛 `TypeError`。`Object.create(null)` 只是去掉了继承的原型，不会改变键转换规则。

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

`Object.hasOwn` 能区分自有属性和继承属性，对象即使覆盖了 `hasOwnProperty` 或没有原型，它也照常工作。哪些属性会被枚举、怎样复制，见[JavaScript 值如何转换、比较，并成为属性键？](./javascript-types.md#枚举与复制属性时，先看%20API%20选中了什么)。

普通对象的遍历顺序也与 `Map` 不同：`Object.keys` 先按数值升序列出数组索引形式的键，再按创建顺序列出其他字符串键，且不列 `Symbol` 键。若用对象当字典，而处理结果又依赖插入顺序，就要先确认用的是哪个枚举 API、键是什么形式。

~~~javascript
const orderedObject = {};
orderedObject.z = "created first";
orderedObject["10"] = "index ten";
orderedObject["2"] = "index two";
Object.keys(orderedObject); // ["2", "10", "z"]
~~~

## 成本和生命周期也属于选择条件

规范要求 `Map`、`Set` 和弱集合的平均访问时间相对集合大小是次线性的，但不规定必须用哈希表或做到常数时间。总成本还取决于外围算法：如果过滤 n 个数组项时每一项都重新建一张同样的查找表，建表成本就被重复支付了 n 次。需要比较数组去重、批量移除和排序的结果时，见[数组操作怎样处理空位与复制？](./arrays.md)。

生命周期也影响选择。`Map` 强引用当前条目的键和值，`Set` 强引用当前成员：只要集合还可达，这些对象就不会被垃圾回收。用 `Map.set` 替换某个键的值后，旧值不再被集合引用；删除条目也会解除对它的引用；集合本身不可达后，它和其中的条目可以一起被回收。如果为对象实例保存的元数据不应延长该对象的寿命，可考虑 `WeakMap`（弱映射）；它不提供遍历、`size` 或确定的清理时间，详见[弱集合与弱引用能保证什么？](./javascript-memory-weakmap-and-weakset.md)。

> [!info]- 来源
> - Map / Set 可接受的键、成员比较、遍历与平均次线性访问要求：[ECMAScript 2026 §§24.1–24.2](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - `SameValueZero` 的定义：[ECMAScript 2026 §7.2.10](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-samevaluezero)。
> - Set 运算和 Set-like 参数契约：[ECMAScript 2025 §§24.2.1.2、24.2.4.5–24.2.4.16](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-getsetrecord)；`intersection` 按较小一侧遍历：[§24.2.4.9](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-set.prototype.intersection)。
> - Set 运算方法在主流浏览器的支持（Chrome 122、Firefox 127、Safari 17，2024 年 6 月起成为 Baseline Newly available）：[MDN `Set.prototype.intersection`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set/intersection)，核对于 2026-11-17。
> - 普通对象自有键顺序与 `Object.keys` 的筛选范围：[ECMAScript 2026 §10.1.11.1](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys) 与 [§20.1.2.19](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.keys)。
> - 普通对象属性键转换为字符串或 `Symbol`：[ECMAScript 2026 §7.1.19 `ToPropertyKey`](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-topropertykey)；强集合与弱集合的键值及可观察边界：[§§24.1–24.4](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - 本章代码核对：Node.js v26.13.0 / V8 14.6.202.34-node.40，2026-11-12。
