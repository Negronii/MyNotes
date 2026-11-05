# How do Object and Array helper APIs copy or enumerate data? / Object 与 Array 辅助方法如何复制或枚举数据？

**Core answer / 核心回答：** Check which properties an API selects, whether it mutates an existing target, and whether an array input is treated as iterable or array-like. Similar-looking helpers can differ in ownership, symbols, getters, holes, and return values. / 选择 API 时要确认它读取哪些属性、是否修改已有目标，以及数组输入按可迭代对象还是类数组对象处理。外观相似的方法在属性归属、Symbol、getter、空位和返回值上可能不同。

## Object.assign: copy into an existing target / Object.assign：复制到已有目标

Object.assign(target, ...sources) copies each source’s own enumerable string and symbol properties into target, mutates and returns target, and lets later sources overwrite earlier properties. The copy is shallow. Reading a source may invoke getters; writing to the target may invoke setters. / Object.assign(target, ...sources) 把来源对象的自有可枚举字符串键和 Symbol 键复制到 target，修改并返回 target；后面的来源覆盖前面的属性。复制是浅拷贝。读取来源对象可能调用 getter，写入 target 可能调用 setter。

~~~javascript
const target = { a: 1, b: 2 };
Object.assign(target, { b: 3, c: 4 });
// target is { a: 1, b: 3, c: 4 }

const merged = Object.assign({}, defaults, overrides);
~~~

Object spread also makes a shallow copy, but creates own data properties on a new object. Object.assign writes to its existing target and can invoke target setters. / 对象展开同样进行浅拷贝，但会在新对象上创建自有数据属性。Object.assign 写入已有目标，可能调用目标 setter。

## What Object.keys, values, and entries include / Object.keys、values 和 entries 会包含什么

Object.keys was standardized in ES5; Object.values and Object.entries were added in ES2017. They select own, enumerable, string-keyed properties. Symbol-keyed properties are excluded. For ordinary objects, array-index string keys come first in ascending numeric order; other string keys follow creation order. This ordinary-object order is not a guarantee for proxies or every exotic object. / Object.keys 属于 ES5；Object.values 和 Object.entries 于 ES2017 加入。它们选择自有、可枚举、字符串键属性，不包含 Symbol 键。普通对象的数组索引字符串键先按数值升序排列，其余字符串键按创建顺序排列。代理和特殊对象不一定遵循普通对象顺序。

~~~javascript
const record = { name: "Ada", age: 36 };
Object.keys(record);   // ["name", "age"]
Object.values(record); // ["Ada", 36]

const keyOrder = {};
keyOrder["4294967296"] = "large integer, not an array index";
keyOrder["4294967295"] = "one past the maximum array index";
keyOrder["2"] = "array index";
Object.keys(keyOrder);
// ["2", "4294967296", "4294967295"]

for (const [key, value] of Object.entries(record)) {
  console.log(key, value);
}
~~~

For the exact ordinary-object own-key ordering, see [ECMAScript OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys). To distinguish own from inherited properties, see [Objects and Prototypes / 对象与原型](./objects-functions-and-prototypes.md).

Object.is applies SameValue equality: NaN equals itself, while +0 and -0 differ. For the comparison table and Map/Set’s SameValueZero rule, see [JavaScript Types / JavaScript 类型](./javascript-types.md). / Object.is 使用 SameValue 相等规则：NaN 与自身相等，而 +0 和 -0 不同。比较表及 Map/Set 的 SameValueZero 规则见 [JavaScript Types / JavaScript 类型](./javascript-types.md)。

## When Array.from and Array.of differ / Array.from 与 Array.of 有何区别

Array.from creates an array from an iterable or an array-like input and can map each value during creation. Array-like inputs are read by index, so a missing index becomes undefined in the result. Array.of treats every argument as an element, avoiding Array’s special single-number length behavior. / Array.from 可从可迭代对象或类数组对象创建数组，并能在创建时映射元素。类数组对象按索引读取，因此缺失索引会在结果中变成 undefined。Array.of 把每个参数都作为元素，避免 Array 对单个数字参数的长度特判。

~~~javascript
const arrayLike = { 0: "a", 1: "b", length: 2 };
Array.from(arrayLike); // ["a", "b"]

Array.from(new Set([1, 2, 2, 3])); // [1, 2, 3]
Array.from({ length: 3 }, (_, index) => index * 2); // [0, 2, 4]
Array.from([, "x"]); // [undefined, "x"]

Array(3);    // length 3 with three holes
Array.of(3); // [3]
Array.of(1, 2, 3); // [1, 2, 3]
~~~

Array.from accepts either an iterable or an array-like input, but those are different protocols. For iteration details, see [Iterators and Generators / 迭代器与生成器](./iterators-and-generators.md). Newer APIs such as Object.hasOwn and Array.prototype.at are listed in [Modern JavaScript Features / 现代 JavaScript 特性](./modern-javascript-features.md). The relevant methods are defined in the [ECMAScript fundamental objects](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html) and [indexed collections](https://tc39.es/ecma262/2025/multipage/indexed-collections.html) sections.
