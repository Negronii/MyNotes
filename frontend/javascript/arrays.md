# How do JavaScript array operations differ on holes, mutation, and copying? / JavaScript 数组操作对空位、修改和复制有何差异？

**Core answer / 核心回答：** Choose an array operation by whether it reads values or keys, skips holes, mutates the receiver, consumes an iterator, or makes a shallow copy. These details affect the result even when two operations look like equivalent ways to “loop” or “copy.” / 选择数组操作时要看它遍历值还是键、是否跳过空位、是否修改原数组、是否消费迭代器，以及是否只做浅拷贝。即使两个操作看起来都在“遍历”或“复制”，细节也会影响结果。

## How can an array be deduplicated? / 如何对数组去重？

For primitive values, `[...new Set(values)]` keeps the first occurrence in iteration order. Set uses SameValueZero; see [Map and Set / JavaScript 中的 Map 与 Set](./map-and-set.md) for the equality rule and its limits. Objects compare by identity, so two different objects with the same fields remain distinct. / 对原始值，`[...new Set(values)]` 按迭代顺序保留首次出现的值。Set 使用 SameValueZero；相等规则及其边界见[Map 与 Set](./map-and-set.md)。对象按身份比较，因此字段相同但引用不同的对象仍会保留。

~~~javascript
[...new Set([1, 1, NaN, NaN, -0, +0])]; // [1, NaN, 0]
[...new Set([{ id: 1 }, { id: 1 }])].length; // 2: distinct references
~~~

For object deduplication by a field, a Map is concise. The last value for an id wins, while the key retains the order of its first insertion. / 按对象字段去重时可用 Map。相同 id 的最后一个对象胜出，但键的遍历位置按首次插入顺序保留。

~~~javascript
function uniqueById(items) {
  const byId = new Map();
  for (const item of items) byId.set(item.id, item);
  return [...byId.values()];
}
~~~

## Should I iterate keys or values? / 应遍历键还是值？

Use for...of for values from an iterable. Use for...in only when enumerating property names, usually on a plain object. A normal dense array’s own index keys are visited in ascending order, but for...in can also include custom and inherited enumerable string properties. / 用 for...of 遍历可迭代对象的值。for...in 用于枚举属性名，通常用于普通对象。普通稠密数组的自有索引键按升序访问，但 for...in 也可能包含自定义及继承的可枚举字符串属性。

~~~javascript
const values = [10, 20];
for (const key in values) console.log(key); // "0", "1"
for (const value of values) console.log(value); // 10, 20

const record = { name: "Ada", age: 36 };
for (const [key, value] of Object.entries(record)) {
  console.log(key, value); // own enumerable string-keyed properties
}
~~~

A hole is different from an own property whose value is undefined. for...of reads a hole as undefined; map and filter skip absent indices; for...in lists only existing enumerable properties. Avoid for...in when array positions are the data. / 空位不同于值为 undefined 的自有属性。for...of 读取空位会得到 undefined；map 和 filter 跳过不存在的索引；for...in 只列出现存可枚举属性。数组位置本身代表数据时不要用 for...in。

See the [ECMAScript for-in/for-of rules](https://tc39.es/ecma262/2025/multipage/ecmascript-language-statements-and-declarations.html#sec-for-in-and-for-of-statements). For iteration protocol details, see [Iterators and Generators / 迭代器与生成器](./iterators-and-generators.md).

## How do array methods treat holes and mutation? / 数组方法如何处理空位和原数组？

- map transforms each present index and returns a new array. It skips holes and preserves corresponding holes in its result.
- filter returns present values that pass the predicate. It skips holes and does not copy them.
- some and every stop when the answer is known; both skip holes. On an empty array, some is false and every is true.
- reduce folds present elements and skips holes. Supply an initial value when the empty-array case needs a defined result.
- concat returns a shallow new array and can consult Symbol.isConcatSpreadable. Spread syntax instead follows the iterable protocol.
- sort and reverse mutate the receiver; ES2023 toSorted and toReversed return copies. Sorting is stable since ES2019. Default sort compares string forms, not numeric values. The normative [Array.prototype.sort algorithm](https://tc39.es/ecma262/2025/multipage/indexed-collections.html#sec-array.prototype.sort) defines the default comparison and stability behavior.

~~~javascript
[1, 11, 2].sort(); // [1, 11, 2]: string ordering
[1, 11, 2].toSorted((a, b) => a - b); // [1, 2, 11]; original is unchanged

const sparse = [, "x"];
[...sparse]; // [undefined, "x"]: spread consumes the iterator
sparse.map(value => value); // [ <1 empty item>, "x" ]
sparse.filter(() => true); // ["x"]
sparse.flat(); // ["x"]: flat removes holes at flattened levels
~~~

The callback arity also matters: map passes value, index, and array. parseInt interprets its second parameter as a radix, so passing it directly changes the radix for later items. / 回调参数个数也会影响结果：map 传入值、索引和数组。parseInt 把第二个参数作为基数，因此直接传给 map 会让后续元素使用不同基数。

~~~javascript
["1", "2", "3"].map(parseInt); // [1, NaN, NaN]
["1", "2", "3"].map(text => parseInt(text, 10)); // [1, 2, 3]
["1", "2", "3"].map(Number); // [1, 2, 3]
~~~

The callback arguments are part of the [ECMAScript Array.prototype.map algorithm](https://tc39.es/ecma262/2025/multipage/indexed-collections.html#sec-array.prototype.map).

## How shallow are array and object copies? / 数组和对象复制有多浅？

Array spread consumes an iterable and copies yielded values shallowly. Nested objects remain shared. Object spread is separate: it copies an object’s own enumerable properties into a new object. / 数组展开会消费可迭代对象，并浅拷贝产出的值；嵌套对象仍然共享。对象展开则会把对象的自有可枚举属性复制到新对象。

~~~javascript
const original = [{ score: 1 }];
const copy = [...original];
copy[0].score = 2;
original[0].score; // 2: the nested object is shared

const merged = { ...defaults, ...overrides }; // later properties replace earlier ones
~~~

Transpilers can lower spread differently according to the target and helper settings. Do not treat output such as [].concat(value) as the language semantics: array spread consumes an iterator, while concat differs for sparse arrays and spreadable objects. / 转译器会按目标和辅助函数配置采用不同输出。不要把 [].concat(value) 之类的输出当作语言语义：数组展开消费迭代器，而 concat 对稀疏数组和可展开对象的处理不同。

## How should nested arrays be flattened? / 应如何展平嵌套数组？

flat(depth), standardized in ES2019, returns a shallowly flattened copy and defaults to depth 1. Use flat(Infinity) for arbitrary nesting; it removes holes at flattened levels and does not recursively flatten non-array iterables. / ES2019 标准化的 flat(depth) 返回浅层展平副本，默认深度为 1。任意深度可用 flat(Infinity)；它会移除被展平层级中的空位，不会递归展平非数组可迭代对象。

A recursive implementation makes the rule explicit but can exceed the call-stack limit on deeply nested input. This version visits every numeric position, so a hole becomes undefined, unlike flat. / 递归实现能直观表达规则，但极深输入可能超出调用栈限制。这个版本访问每个数值索引，因此空位会变为 undefined，与 flat 不同。

~~~javascript
function flattenNested(items) {
  const result = [];
  function append(list) {
    for (let i = 0; i < list.length; i++) {
      const value = list[i];
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

The historical iterative [].concat(...items) pattern flattens one level per pass. It can hit argument-count limits, repeatedly copy large arrays, and produce different sparse-array results from flat. It may return the original input when no nested array exists. / 传统迭代写法 [].concat(...items) 每轮展平一层，可能触发参数数量限制、反复复制大数组，且稀疏数组结果不同于 flat。若无嵌套数组，它还可能直接返回原输入。

~~~javascript
function flattenByLevels(items) {
  while (items.some(Array.isArray)) items = [].concat(...items);
  return items;
}
~~~

Prefer flat when its depth and hole semantics match the task. For Set/Map equality used by deduplication, see [Map and Set / JavaScript 中的 Map 与 Set](./map-and-set.md). That page owns the keyed-collection contract; this page keeps the array-specific decision and examples.

## Compute a maximum without expanding function arguments / 避免实参展开求最大值

`Math.max(...values)` and `Math.max.apply(null, values)` pass one argument per value. Engines can reject a very large argument list, and the cutoff is implementation-specific. A loop keeps a fixed-size call and makes the handling of empty input and invalid values visible. / 展开会把每个值传为一个函数实参。循环每次只传固定数量的参数，可以明确空输入和无效值的处理策略。

~~~javascript
function maxOfNumbers(values) {
  let max = -Infinity;
  for (const value of values) {
    max = Math.max(max, value);
  }
  return max;
}

maxOfNumbers([]);          // -Infinity
maxOfNumbers([7, NaN]);    // NaN
maxOfNumbers([, 7]);       // NaN, since array iteration visits the hole as undefined
~~~

If the product treats holes as absent, an explicit reducer callback skips them. Choose how to handle empty input and invalid numbers before computing a result. [ECMAScript `Math.max`](https://tc39.es/ecma262/2026/#sec-math.max)
