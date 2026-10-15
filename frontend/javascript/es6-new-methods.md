# Object and Array Methods / 对象与数组方法

**Key terms / 关键词:** own property 自有属性 · enumerable 可枚举 · shallow copy 浅拷贝 · array-like 类数组对象

This is a focused reference for selected Object and Array methods and their edition boundaries. Newer additions such as Object.hasOwn and Array.at are covered in [Modern JavaScript Features / 现代 JavaScript 特性](./modern-javascript-features.md). / 本笔记选列部分 Object 与 Array 方法，并标明其版本边界。Object.hasOwn、Array.at 等后续新增方法见[现代 JavaScript 特性](./modern-javascript-features.md)。

## Object methods / Object 方法

### Object.assign(target, ...sources)

Copies enumerable own string and symbol properties from each source to target, mutates and returns target. Later sources overwrite earlier properties. The copy is shallow. Reading a source may invoke getters; writing to the target may invoke setters. / 把各个来源对象的自有可枚举字符串键和 Symbol 键复制到 target，修改并返回 target。后面的来源会覆盖前面的同名属性。该操作是浅拷贝；读取来源对象可能触发 getter，写入 target 可能触发 setter。

```javascript
const target = { a: 1, b: 2 };
Object.assign(target, { b: 3, c: 4 });
// target is { a: 1, b: 3, c: 4 }

const merged = Object.assign({}, defaults, overrides);
```

Object spread is often more concise, but is not identical in every detail: it creates own data properties in a new object, while Object.assign writes to its existing target and can invoke target setters. / 对象展开通常更简洁，但细节并非处处等价：展开会在新对象上创建自有数据属性；Object.assign 则写入已有目标对象，可能触发目标 setter。

### Object.is(a, b)

Uses SameValue equality. It differs from === for NaN and signed zero: / 使用 SameValue 相等规则。它对 NaN 和有符号零的处理与 === 不同：

```javascript
Object.is(NaN, NaN); // true
Object.is(+0, -0);   // false
NaN === NaN;         // false
+0 === -0;           // true
```

### Object.keys, Object.values, and Object.entries

Object.keys was standardized in ES5; Object.values and Object.entries were added in ES2017. They return an object’s own enumerable string-keyed property names, values, or pairs. Symbol-keyed properties are excluded. For ordinary objects, array-index string keys come first in ascending numeric order, followed by other string keys in creation order. This ordinary-object order is not a guarantee for proxies or every exotic object. / Object.keys 属于 ES5；Object.values 和 Object.entries 于 ES2017 加入。它们分别返回对象的自有可枚举字符串键、值或键值对数组。Symbol 键不会包含在结果中。对普通对象，数组索引字符串键先按数值升序排列，其余字符串键按创建顺序排列。代理或其他特殊对象不一定遵循普通对象的顺序。

```javascript
const record = { name: "Ada", age: 36 };
Object.keys(record);   // ["name", "age"]
Object.values(record); // ["Ada", 36]

const keyOrder = {};
keyOrder["4294967296"] = "large integer, not an array index";
keyOrder["4294967295"] = "one past the maximum array index";
keyOrder["2"] = "array index";
Object.keys(keyOrder); // ["2", "4294967296", "4294967295"]

for (const [key, value] of Object.entries(record)) {
  console.log(key, value);
}
```

For a plain dictionary, remember that own-property checks and inherited properties are different questions. See [JavaScript Types and Coercion / JavaScript 类型与类型转换](./javascript-types.md). / 普通对象作字典时，要区分自有属性与继承属性。详见[JavaScript 类型与类型转换](./javascript-types.md)。

## Array methods / Array 方法

### Array.from(arrayLikeOrIterable, mapFn?)

Creates a new array from an iterable or array-like input, optionally mapping each value as it is created. Array-like input is read by index, so a missing index is observed as undefined in the result. / 从可迭代对象或类数组输入创建新数组，并可在创建时映射元素。类数组输入按索引读取，因此缺失索引会在结果中表现为 undefined。

```javascript
const arrayLike = { 0: "a", 1: "b", length: 2 };
Array.from(arrayLike); // ["a", "b"]

Array.from(new Set([1, 2, 2, 3])); // [1, 2, 3]
Array.from({ length: 3 }, (_, index) => index * 2); // [0, 2, 4]

Array.from([, "x"]); // [undefined, "x"]
```

### Array.of(...items)

Creates an array from its arguments. It avoids the Array constructor’s special treatment of a single numeric argument as a requested length. / 根据参数创建数组，避免 Array 构造器把单个数字参数特殊解释为数组长度。

```javascript
Array(3);    // an array of length 3 with three holes
Array.of(3); // [3]
Array.of(1, 2, 3); // [1, 2, 3]
```

See [ECMAScript OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys) for the ordinary-object order, plus [fundamental objects](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html) and [indexed collections](https://tc39.es/ecma262/2025/multipage/indexed-collections.html) for the other methods. / 普通对象的属性顺序见 [ECMAScript OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys)；其他方法见 [基础对象](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html) 与 [索引集合](https://tc39.es/ecma262/2025/multipage/indexed-collections.html)。

**Interview answer / 面试回答:** Object.assign mutates its target and shallow-copies enumerable own string and symbol properties. Object.keys/values/entries inspect own enumerable string-keyed properties. Array.from accepts iterables and array-like objects; Array.of treats each argument as an element, including a single number. / Object.assign 会修改目标对象，并浅拷贝自有可枚举字符串键和 Symbol 键。Object.keys/values/entries 只处理自有可枚举字符串键。Array.from 接受可迭代对象和类数组对象；Array.of 把每个参数都作为元素，包括单个数字参数。

Related: [JavaScript Arrays / JavaScript 数组](./arrays.md); [Modern JavaScript Features / 现代 JavaScript 特性](./modern-javascript-features.md).
