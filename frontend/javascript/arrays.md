# JavaScript Arrays / JavaScript 数组

**Key terms / 关键词:** iterable 可迭代对象 · sparse array 稀疏数组 · SameValueZero 相同值零 · shallow copy 浅拷贝

Arrays are ordered objects with indexed properties and an iterable interface. Choose an operation by its contract: iteration protocol, holes, mutation, and equality can change the result. / 数组是带索引属性并实现可迭代协议的有序对象。选择操作时要看清迭代协议、空位、是否修改原数组及相等规则，这些都会影响结果。

## Iterating keys or values / 遍历键还是值

Use `for...of` for values from an iterable. Use `for...in` only when enumerating property names, usually on a plain object. A normal dense array’s own index keys are visited in ascending order, but `for...in` can also include custom and inherited enumerable string properties. / 用 `for...of` 遍历可迭代对象的值；`for...in` 遍历属性名，通常用于普通对象。普通稠密数组的自有索引键按升序枚举，但 `for...in` 也可能包含自定义属性和原型链上的可枚举字符串属性。

```javascript
const values = [10, 20];
for (const key in values) console.log(key); // "0", "1"
for (const value of values) console.log(value); // 10, 20

const record = { name: "Ada", age: 36 };
for (const [key, value] of Object.entries(record)) {
  console.log(key, value); // own enumerable string-keyed properties
}
```

An array hole is different from an own property whose value is `undefined`: `for...of` reads a hole as `undefined`; methods such as `map` and `filter` skip absent indices. `for...in` lists only existing enumerable properties. Avoid using it when the array’s positional values are intended. / 数组空位不同于值为 `undefined` 的自有属性：`for...of` 读取空位时得到 `undefined`，而 `map`、`filter` 等方法会跳过不存在的索引。`for...in` 只列出现存的可枚举属性。需要按位置处理数组值时不要用它。

The ordering and inheritance behavior follows the [ECMAScript for-in/for-of rules](https://tc39.es/ecma262/2025/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements). / 顺序与继承行为遵循 [ECMAScript for-in/for-of 规范](https://tc39.es/ecma262/2025/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements)。

## Removing duplicates / 数组去重

For primitive values, `[...new Set(values)]` keeps the first occurrence in iteration order. Set uses SameValueZero: `NaN` matches `NaN`, and `+0` matches `-0`. Objects compare by identity, so two different objects with the same fields remain distinct. / 对原始值，`[...new Set(values)]` 会按迭代顺序保留首次出现的值。Set 使用 SameValueZero：`NaN` 与自身相同，`+0` 与 `-0` 相同。对象按引用身份比较，因此字段相同但引用不同的对象仍会保留。

```javascript
[...new Set([1, 1, NaN, NaN, -0, +0])]; // [1, NaN, 0]
[...new Set([{ id: 1 }, { id: 1 }])].length; // 2: distinct references
```

For object deduplication by a field, a Map is concise. In this example the last value for an id wins, while the key retains the order of its first insertion. / 按对象字段去重时可用 Map。以下实现中相同 id 的最后一个对象胜出，但键的遍历位置仍按首次插入顺序保留。

```javascript
function uniqueById(items) {
  const byId = new Map();
  for (const item of items) byId.set(item.id, item);
  return [...byId.values()];
}
```

A Set/Map approach is commonly linear in practical runtimes, but ECMAScript requires average access to be sublinear, not a specific O(1) implementation or end-to-end complexity. Linear `indexOf`/accumulator searches can be quadratic; choose them only when the input size or other requirements justify them. A sort-based approach changes order and needs a comparator whose equality matches the deduplication rule. / Set/Map 在常见运行时中通常表现为线性处理，但 ECMAScript 只要求平均访问复杂度优于线性，并未规定必须 O(1)，整体复杂度也取决于运行时。反复用 `indexOf` 或累加器查找可能达到平方复杂度。排序去重会改变顺序，且比较器的相等规则必须符合去重需求。

See the [ECMAScript keyed collections specification](https://tc39.es/ecma262/2025/multipage/keyed-collections.html) for Set and Map equality and ordering semantics. / Set 与 Map 的相等和顺序语义见 [ECMAScript 键控集合规范](https://tc39.es/ecma262/2025/multipage/keyed-collections.html)。

## Array methods: mutation and holes / 数组方法：修改行为与空位

- `map` transforms each present index and returns a new array; it skips holes and preserves those holes in the result. / `map` 转换每个已存在的索引并返回新数组；它跳过空位，结果中也保留对应空位。
- `filter` returns the present values that pass the predicate; holes are skipped and are not copied. / `filter` 返回通过判断的现存值；空位会跳过，也不会复制。
- `some` and `every` stop when the answer is known; both skip holes. On an empty array, `some` is false and `every` is true. / `some` 和 `every` 在结论已确定时停止；二者都会跳过空位。空数组上 `some` 为 false，`every` 为 true。
- `reduce` folds present elements; provide an initial value when the empty-array case matters. / `reduce` 折叠现存元素；若空数组也需有定义的结果，应提供初始值。
- `concat` returns a shallow new array and can consult `Symbol.isConcatSpreadable`; spread syntax follows the iterable protocol instead. / `concat` 返回浅拷贝新数组，并可能遵循 `Symbol.isConcatSpreadable`；展开语法则使用可迭代协议。
- `sort` and `reverse` mutate the receiver; `toSorted` and `toReversed` (ES2023) return copies. Sorting is stable since ES2019. Default `sort()` compares string forms, not numeric values. / `sort` 和 `reverse` 会修改原数组；ES2023 的 `toSorted`、`toReversed` 返回副本。ES2019 起排序稳定。默认 `sort()` 比较字符串形式，而非数值大小。

```javascript
[1, 11, 2].sort(); // [1, 11, 2] — lexicographic string ordering
[1, 11, 2].toSorted((a, b) => a - b); // [1, 2, 11]; receiver is unchanged

const sparse = [, "x"];
[...sparse]; // [undefined, "x"] — spread consumes the array iterator
sparse.map(value => value); // [ <1 empty item>, "x" ]
sparse.filter(() => true); // ["x"]
sparse.flat(); // ["x"] — flat removes holes at flattened levels
```

## Spread and copying / 展开与拷贝

Array spread consumes an iterable and copies its yielded values shallowly. Nested objects are still shared. Object spread is a separate operation: it copies an object’s own enumerable properties into a new object. / 数组展开会消费可迭代对象并浅拷贝其产出的值；嵌套对象仍然共享。对象展开是另一种操作：把对象的自有可枚举属性复制到新对象。

```javascript
const original = [{ score: 1 }];
const copy = [...original];
copy[0].score = 2;
original[0].score; // 2 — the nested object is shared

const merged = { ...defaults, ...overrides }; // later properties replace earlier ones
```

Transpilers may lower spread in different ways according to the target and helper settings. Do not treat one Babel output such as `[].concat(value)` as the language semantics: array spread uses the iterator, while `concat` has different behavior for sparse arrays and spreadable objects. / 转译器会按目标环境与配置选择不同实现。不要把某一种 Babel 输出（如 `[].concat(value)`）当作语言语义：数组展开消费迭代器，而 `concat` 对稀疏数组和可展开对象的处理不同。

## Flattening nested arrays / 展平嵌套数组

`flat(depth)` (ES2019) returns a shallowly flattened copy and defaults to depth 1. Use `flat(Infinity)` when arbitrary nesting is intended; it removes holes at levels it flattens and does not recursively flatten non-array iterables. / ES2019 的 `flat(depth)` 返回浅层展平副本，默认深度为 1。确实需要展平任意嵌套时可用 `flat(Infinity)`；它会移除被展平层级中的空位，不会递归展平非数组可迭代对象。

A recursive implementation makes the rule explicit, but can exceed the call-stack limit on deeply nested input. This version visits every numeric position, so a hole becomes `undefined`, unlike `flat`. / 递归实现能直观表达规则，但极深输入可能超出调用栈限制。以下版本逐个访问数值索引，因此空位会变成 `undefined`，与 `flat` 不同。

```javascript
function flattenNested(items) {
  const result = [];
  for (let i = 0; i < items.length; i++) {
    const value = items[i];
    if (Array.isArray(value)) result.push(...flattenNested(value));
    else result.push(value);
  }
  return result;
}

flattenNested([1, [2, [3]], 4]); // [1, 2, 3, 4]
[1, [2, [3]], 4].flat(Infinity); // [1, 2, 3, 4]
```

The historical iterative `[].concat(...items)` pattern flattens one level per pass. It can hit argument-count limits, repeatedly copy large arrays, and has different sparse-array behavior from `flat`; it may also return the original input when no nested array exists. / 传统迭代写法 `[].concat(...items)` 每轮展平一层，但可能触发参数数量限制、反复复制大数组，而且稀疏数组行为与 `flat` 不同；若没有嵌套数组，它还可能直接返回原数组。

```javascript
function flattenByLevels(items) {
  while (items.some(Array.isArray)) items = [].concat(...items);
  return items;
}
```

Prefer `flat` when its hole and depth semantics match the task. / 若 `flat` 的空位和深度语义符合需求，应优先使用。

**Interview answer / 面试回答:** `for...of` reads array values; Set deduplicates by SameValueZero while preserving first-seen order; array methods differ on holes and mutation; spread is shallow; and `flat` is the built-in flattening operation. / `for...of` 读取数组值；Set 按 SameValueZero 去重并保留首次出现顺序；数组方法对空位和原数组修改的行为不同；展开是浅拷贝；内置展平方法是 `flat`。
