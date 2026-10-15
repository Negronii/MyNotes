# Map and Set in JavaScript / JavaScript 中的 Map 与 Set

**Key terms / 关键词:** keyed collection 键控集合 · SameValueZero 相同值零 · insertion order 插入顺序 · set-like object 类 Set 对象

Use `Map` for key-value data when keys are not just fixed strings or symbols, or when direct iteration and a size property help. Use `Set` when uniqueness and membership are central. ECMAScript specifies observable ordering and equality, but not a particular hash-table implementation or constant-time performance. / 当键不只是固定字符串或 Symbol，或需要直接迭代与 size 属性时，可用 `Map` 保存键值数据；当重点是唯一性和成员判断时，可用 `Set`。ECMAScript 规定可观察到的顺序和相等规则，但不规定具体哈希表实现或恒定时间性能。

## Choosing a collection / 选择集合

- `Map`: keys may be any value; object keys use identity; entries iterate in insertion order. Updating an existing key does not move its position. Delete then reinsert to place it at the end. / `Map`：键可以是任意值；对象键按身份比较；条目按插入顺序迭代。更新已有键不会改变位置；删除后重新插入才会移到末尾。
- `Set`: stores unique values in insertion order. Deleting and adding a value again places it at the end. / `Set`：按插入顺序保存唯一值。删除后再次添加会移到末尾。
- Plain objects coerce property keys to strings or symbols and include prototype behavior unless created with a null prototype. For ordinary dictionaries, `Object.hasOwn` avoids an overridden `hasOwnProperty`; `Map` is often simpler when keys are dynamic. / 普通对象会把属性键转换为字符串或 Symbol；除非创建为 null 原型对象，否则还有原型行为。对象字典可用 `Object.hasOwn` 避免被覆盖的 `hasOwnProperty`；键动态时通常 Map 更简单。
- Arrays are suited to indexed, positional data. A Set is not a replacement when duplicate positions or random indexing matter. / 数组适合按索引排列的数据；若需要保留重复位置或随机索引，Set 不能替代数组。

Both Map and Set use SameValueZero for keys or members: NaN matches NaN, and +0 and -0 are treated as the same key. Objects compare by identity. / Map 和 Set 对键或成员使用 SameValueZero：NaN 与自身相同，+0 与 -0 被视为同一个键；对象按身份比较。

## Map / 映射

```javascript
const userById = new Map();
userById.set(7, { name: "Ada" });
userById.set("7", { name: "Grace" }); // number and string keys differ

userById.get(7); // { name: "Ada" }
userById.has(8); // false
userById.size; // 2

for (const [id, user] of userById) {
  console.log(id, user.name); // insertion order
}
```

Core methods are `set`, `get`, `has`, `delete`, `clear`, and the `size` property. `keys()`, `values()`, and `entries()` return iterators; the default iterator is `entries()`. `forEach` receives `(value, key, map)`. / 常用方法包括 `set`、`get`、`has`、`delete`、`clear`，以及 `size` 属性。`keys()`、`values()`、`entries()` 返回迭代器；默认迭代器等同于 `entries()`。`forEach` 的参数顺序是 `(value, key, map)`。

| Method / 方法 | Result / 返回值 |
|---|---|
| `set(key, value)` | The Map, for chaining / 返回 Map，可链式调用 |
| `get(key)` | Value or `undefined` / 值或 `undefined` |
| `has(key)` | Boolean / 布尔值 |
| `delete(key)` | Whether an entry was removed / 是否删除了条目 |
| `clear()` | Empties the Map / 清空 Map |

## Set / 集合

```javascript
const tags = new Set(["js", "runtime", "js"]);
tags.add("language");
tags.has("js"); // true
[...tags]; // ["js", "runtime", "language"]
```

Core methods are `add`, `has`, `delete`, `clear`, and the `size` property. `keys()` and `values()` produce the same values; `entries()` yields `[value, value]` for compatibility with Map iteration. `forEach` receives `(value, value, set)`. / 常用方法包括 `add`、`has`、`delete`、`clear`，以及 `size` 属性。`keys()` 和 `values()` 产出相同的值；为兼容 Map 迭代，`entries()` 产出 `[value, value]`。`forEach` 的参数顺序是 `(value, value, set)`。

| Method / 方法 | Result / 返回值 |
|---|---|
| `add(value)` | The Set, for chaining / 返回 Set，可链式调用 |
| `has(value)` | Boolean / 布尔值 |
| `delete(value)` | Whether a value was removed / 是否删除了值 |
| `clear()` | Empties the Set / 清空 Set |

## Set composition methods / Set 集合运算

ECMAScript 2025 standardized `union`, `intersection`, `difference`, `symmetricDifference`, `isSubsetOf`, `isSupersetOf`, and `isDisjointFrom`. They accept set-like inputs and return a Set or boolean as indicated by the method. Check runtime support when targeting older engines. / ECMAScript 2025 标准化了 `union`、`intersection`、`difference`、`symmetricDifference`、`isSubsetOf`、`isSupersetOf` 和 `isDisjointFrom`。这些方法接受类 Set 输入，并按方法返回 Set 或布尔值。面向较旧引擎时需确认运行时支持。

```javascript
const enabled = new Set(["search", "export"]);
const available = new Set(["search", "export", "admin"]);

[...enabled.intersection(available)]; // ["search", "export"]
enabled.isSubsetOf(available); // true
```

## Common patterns / 常见用法

```javascript
const unique = [...new Set([1, 2, 2, 3])]; // [1, 2, 3]

const right = new Set([2, 3, 4]);
const leftOnly = [...new Set([1, 2, 3])]
  .filter(value => !right.has(value)); // [1]
```

For repeated membership checks, build the lookup Set once rather than inside the filter callback. / 需要反复查询成员时，应先创建一次 Set，而不是在 filter 回调中重复创建。

**Interview answer / 面试回答:** Map preserves arbitrary key identity and insertion order; Set preserves unique values in insertion order. Both use SameValueZero, while plain object keys undergo property-key conversion. Their complexity depends on the implementation; the standard requires average sublinear access rather than a fixed O(1) guarantee. / Map 保留任意键的身份和插入顺序；Set 按插入顺序保存唯一值。二者使用 SameValueZero，普通对象键则会进行属性键转换。复杂度取决于实现；标准只要求平均访问优于线性，并不保证固定 O(1)。

See [ECMAScript keyed collections](https://tc39.es/ecma262/2025/multipage/keyed-collections.html) and [Set methods](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-set-objects). / 详见 [ECMAScript 键控集合规范](https://tc39.es/ecma262/2025/multipage/keyed-collections.html) 与 [Set 方法规范](https://tc39.es/ecma262/2025/multipage/keyed-collections.html#sec-set-objects)。

Related: [JavaScript Types and Coercion / JavaScript 类型与类型转换](./javascript-types.md); [Memory and weak collections / JavaScript 内存与弱集合](./javascript-memory-weakmap-and-weakset.md).
