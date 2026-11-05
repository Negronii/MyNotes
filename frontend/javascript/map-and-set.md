# When should I use Map, Set, or an object? / 何时应使用 Map、Set 或普通对象？

**Core answer / 核心回答：** Use Map for key-value data when keys may be arbitrary values or identity matters; use Set when uniqueness or repeated membership checks are central; use arrays for ordered positions and duplicates; use ordinary objects when property-key conversion and object-shaped data are intended. Map and Set preserve insertion order and compare keys or members with SameValueZero. / 键可以是任意值或身份重要时使用 Map；唯一性或反复成员查询是重点时使用 Set；需要位置顺序或重复值时使用数组；确实需要属性键转换和对象形状时使用普通对象。Map 和 Set 保留插入顺序，并用 SameValueZero 比较键或成员。

## Choose by data shape / 按数据形状选择

| Structure / 结构 | Use when / 适用场景 | Key or order behavior / 键与顺序 |
|---|---|---|
| Map | Arbitrary key-value pairs, object identity keys, direct iteration, or size / 任意键值、对象身份、直接遍历或 size | Any value can be a key; entries iterate in insertion order / 键可为任意值；条目按插入顺序遍历 |
| Set | Unique values or repeated membership checks / 唯一值或反复成员查询 | Values are unique and iterate in insertion order / 值唯一并按插入顺序遍历 |
| Array | Positional data, duplicates, indexed access / 位置数据、重复项、索引访问 | Each position is distinct / 每个位置都独立 |
| Object | Fixed string/symbol properties or object-shaped records / 固定字符串/Symbol 属性或对象记录 | Other keys convert to strings or symbols; prototype behavior applies unless null-prototype / 其他键转为字符串或 Symbol；除非为 null 原型，否则有原型行为 |

Ordinary dictionaries can use Object.hasOwn to distinguish own from inherited properties and avoid an overridden hasOwnProperty. Object.create(null) removes the inherited prototype but still applies property-key conversion. For that conversion rule, see [JavaScript Types / JavaScript 类型](./javascript-types.md). / 普通对象字典可用 Object.hasOwn 区分自有与继承属性，并避免被覆盖的 hasOwnProperty。Object.create(null) 去掉继承原型，但仍执行属性键转换。转换规则见 [JavaScript Types / JavaScript 类型](./javascript-types.md)。

## How Map compares keys and iterates / Map 如何比较键并遍历

A Map key can be any value. Object keys are compared by identity, not by their fields. Number and string keys differ. Updating an existing key changes its value but not its insertion position; deleting and reinserting moves it to the end. / Map 的键可以是任意值。对象键按身份比较，不按字段比较；数字键和字符串键不同。更新已有键的值不会改变插入位置；删除再插入会移动到末尾。

~~~javascript
const userById = new Map();
userById.set(7, { name: "Ada" });
userById.set("7", { name: "Grace" });

userById.get(7); // { name: "Ada" }
userById.has(8); // false
userById.size; // 2

for (const [id, user] of userById) {
  console.log(id, user.name); // insertion order
}

const first = { id: 1 };
const second = { id: 1 };
const byObject = new Map([[first, "first"]]);
byObject.get(second); // undefined: different object identity
~~~

Map uses SameValueZero: NaN matches NaN, and +0 and -0 represent the same key. Common methods are set, get, has, delete, clear, and size. keys(), values(), and entries() return iterators; the default iterator is entries(). forEach receives (value, key, map). / Map 使用 SameValueZero：NaN 与自身相同，+0 和 -0 表示同一个键。常用方法为 set、get、has、delete、clear 和 size。keys()、values() 和 entries() 返回迭代器；默认迭代器为 entries()。forEach 参数顺序为 (value, key, map)。

## How Set stores unique values / Set 如何保存唯一值

A Set stores unique values in insertion order. Delete then add a value to move it to the end. It uses SameValueZero, so NaN matches NaN, signed zeroes match, and objects are unique by identity. / Set 按插入顺序存储唯一值。删除后再次添加可把值移到末尾。它使用 SameValueZero：NaN 匹配 NaN，有符号零相同，对象按身份去重。

~~~javascript
const tags = new Set(["js", "runtime", "js"]);
tags.add("language");
tags.has("js"); // true
[...tags]; // ["js", "runtime", "language"]
~~~

Common methods are add, has, delete, clear, and size. keys() and values() produce the same values; entries() yields [value, value] for Map-iteration compatibility; forEach receives (value, value, set). / 常用方法为 add、has、delete、clear 和 size。keys() 与 values() 产出相同值；entries() 为兼容 Map 遍历产出 [value, value]；forEach 参数为 (value, value, set)。

## Set composition and complexity / Set 运算与复杂度

ECMAScript 2025 standardized union, intersection, difference, symmetricDifference, isSubsetOf, isSupersetOf, and isDisjointFrom. They accept set-like inputs and return a Set or Boolean as indicated. Check support when targeting older engines. / ECMAScript 2025 标准化了 union、intersection、difference、symmetricDifference、isSubsetOf、isSupersetOf 和 isDisjointFrom。它们接受类 Set 输入，并按方法返回 Set 或布尔值。面向旧引擎时应检查支持情况。

~~~javascript
const enabled = new Set(["search", "export"]);
const available = new Set(["search", "export", "admin"]);

[...enabled.intersection(available)]; // ["search", "export"]
enabled.isSubsetOf(available); // true

const right = new Set([2, 3, 4]);
const leftOnly = [...new Set([1, 2, 3])]
  .filter(value => !right.has(value)); // [1]
~~~

For repeated membership checks, build the lookup Set once rather than inside the filter callback. A Set-based array deduplication example and its order requirements belong in [JavaScript Arrays / JavaScript 数组](./arrays.md). / 需要反复查询成员时，应先创建一次 Set，不要在 filter 回调中反复创建。Set 数组去重示例及其顺序要求见 [JavaScript Arrays / JavaScript 数组](./arrays.md)。

ECMAScript requires average access to be sublinear, not a specific O(1) implementation. End-to-end cost also depends on the surrounding algorithm. See the [ECMAScript keyed collections specification](https://tc39.es/ecma262/2025/multipage/keyed-collections.html) and [Set methods](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-set-objects).
