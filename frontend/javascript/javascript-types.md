# JavaScript Types and Coercion / JavaScript 类型与类型转换

**Key terms / 关键词:** primitive 原始值 · object 对象 · coercion 隐式转换 · property key 属性键 · realm 执行领域

JavaScript has seven primitive types: `undefined`, `null`, `boolean`, `number`, `bigint`, `string`, and `symbol`. Other values are objects, including functions. A value’s language semantics are specified; whether an engine stores it on a stack, heap, or elsewhere is an implementation detail. / JavaScript 有七种原始类型：`undefined`、`null`、`boolean`、`number`、`bigint`、`string` 和 `symbol`。其他值都是对象，函数也属于对象。语言规范定义的是值的行为；引擎是否把值放在栈、堆或其他位置属于实现细节。

| Type / 类型 | Useful fact / 要点 |
|---|---|
| `undefined` | Default value of an uninitialized `var` binding or missing result / 未初始化的 `var` 绑定或缺失结果的默认值 |
| `null` | Intentional absence; `typeof null` is the historical string `"object"` / 表示有意为空；`typeof null` 因历史兼容结果为 `"object"` |
| `boolean` | Falsy values include `false`, `0`, `-0`, `0n`, `""`, `null`, `undefined`, and `NaN` / 假值包括这些值 |
| `number` | IEEE 754 binary64; includes `NaN` and infinities / IEEE 754 binary64，包含 `NaN` 与无穷值 |
| `bigint` | Arbitrary-precision integers; cannot be mixed with Number arithmetic without conversion / 任意精度整数；算术运算不能直接与 Number 混用 |
| `string` | Immutable sequence of UTF-16 code units / 不可变的 UTF-16 码元序列 |
| `symbol` | Unique primitive value, often used as a property key / 唯一原始值，常用作属性键 |

Objects and functions are mutable or callable according to their own behavior; “reference type” is a useful description of assignment and identity, not a guarantee about physical memory layout. / 对象和函数的可变性、可调用性由各自行为决定。“引用类型”可以帮助解释赋值与身份，但不代表固定的物理内存布局。

## Coercion essentials / 类型转换要点

Truthiness and numeric conversion are separate operations. Empty arrays and objects are truthy; `Number("")` and `Number(null)` are zero; `Number(undefined)` is `NaN`. Use explicit conversions where the input contract matters. / 布尔转换与数值转换是不同操作。空数组和空对象都是真值；`Number("")` 与 `Number(null)` 为 0；`Number(undefined)` 为 `NaN`。输入契约重要时应显式转换。

```javascript
Boolean("false"); // true: nonempty string
Boolean([]);      // true
Number("");       // 0
Number(null);     // 0
Number(undefined);// NaN

Number.isNaN(NaN); // true
NaN === NaN;       // false
Object.is(NaN, NaN); // true
Object.is(+0, -0);   // false
```

Use `x === null` to test specifically for null. `Number.isNaN(x)` tests NaN without first coercing non-number inputs. / 若要专门判断 null，使用 `x === null`。`Number.isNaN(x)` 不会先把非数值输入强制转换。

## Assignment and object identity / 赋值与对象身份

Assigning an object value to another binding makes both bindings refer to the same object. A property assignment evaluates and remembers its base object before evaluating the right side; it does not create an “undefined slot” in advance. / 把对象值赋给另一个绑定后，两个绑定会引用同一个对象。属性赋值会先求值并记录基对象，再求值右侧表达式；这时还不会提前创建一个值为 `undefined` 的属性槽。

```javascript
let a = { n: 1 };
const b = a;
a.x = a = { n: 2 };

a.x; // undefined
b.x; // { n: 2 }
```

Evaluation first captures the old object as the base of `a.x`. The right side then reassigns `a` to a new object; the final property write still targets the captured old object, which `b` references. / 求值先把旧对象记录为 `a.x` 的基对象；右侧随后把 `a` 重新绑定到新对象；最后写入仍作用于之前记录的旧对象，也就是 `b` 引用的对象。

## Choosing a type check / 如何选择类型判断方式

- `typeof` is useful for primitives and functions, with the `null` quirk shown above. / `typeof` 适合判断原始值和函数，但要记住 null 的历史特例。
- `Array.isArray(value)` is the robust array check, including arrays from another realm. / `Array.isArray(value)` 能可靠识别来自其他 realm 的数组。
- By default, `instanceof` checks whether the RHS constructor’s `.prototype` occurs in the LHS value’s prototype chain ([`OrdinaryHasInstance`](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-ordinaryhasinstance)). Constructors from different realms normally have different prototype objects, so a foreign value can fail against the local constructor but pass against its own realm’s constructor. `Symbol.hasInstance` can customize the check. / 默认情况下，`instanceof` 检查右侧构造函数的 `.prototype` 是否出现在左侧值的原型链中（见 [`OrdinaryHasInstance`](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-ordinaryhasinstance)）。不同 realm 中的构造函数通常有不同原型对象，因此跨 realm 的值可能无法通过本地构造函数判断，却能通过其所属 realm 的构造函数判断。`Symbol.hasInstance` 可自定义该检查。
- `Object.prototype.toString.call(value)` is a useful built-in tag, not a definitive type oracle: `Symbol.toStringTag` can change the displayed tag. / `Object.prototype.toString.call(value)` 可读取内置标签，但不是绝对可靠的类型证明：`Symbol.toStringTag` 可以改变显示标签。

```javascript
typeof null; // "object"
Array.isArray([]); // true

const custom = { [Symbol.toStringTag]: "Array" };
Object.prototype.toString.call(custom); // "[object Array]" — a spoofable tag
```

For application validation, prefer a check for the behavior or data shape the code actually requires, rather than a generic display string. / 应用校验应检查代码实际依赖的行为或数据结构，不要只依赖通用类型字符串。

See [ECMAScript Object.prototype.toString](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-object.prototype.tostring) and its use of `Symbol.toStringTag`. / 详见 [ECMAScript Object.prototype.toString 规范](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-object.prototype.tostring)及其对 `Symbol.toStringTag` 的处理。

## Object property keys / 对象属性键

A property key is a string or a symbol. When another value is used in bracket notation, JavaScript applies `ToPropertyKey`: objects may run `Symbol.toPrimitive` or other conversion hooks before producing a string or symbol. This is more precise than saying every key simply calls `toString()`. / 属性键是字符串或 Symbol。方括号中使用其他值时，JavaScript 会执行 `ToPropertyKey`：对象可能先运行 `Symbol.toPrimitive` 等转换钩子，再得到字符串或 Symbol。因此“其他键都直接调用 `toString()`”并不准确。

```javascript
const record = {};
record[123] = "number";
record["123"]; // "number"

const key = { [Symbol.toPrimitive]: () => "account" };
record[key] = "Ada";
record.account; // "Ada"

const map = new Map();
map[{ id: 1 }] = "property key conversion";
map.set({ id: 1 }, "object identity key"); // Map does not coerce keys
```

Use `Map` when distinct object identities or uncoerced non-string keys matter. For plain-object dictionaries, use `Object.hasOwn` for ownership checks; `Object.create(null)` avoids an inherited prototype but still uses property-key conversion. / 需要区分对象身份或避免键转换时使用 `Map`。普通对象字典可用 `Object.hasOwn` 判断自有属性；`Object.create(null)` 可去掉继承原型，但仍会转换属性键。

**Interview answer / 面试回答:** JavaScript has seven primitive types. Objects are assigned and compared by identity, but stack-versus-heap layout is engine-specific. Use `typeof` for basic primitive checks, `Array.isArray` for arrays, and `instanceof` for a constructor’s prototype-chain relationship, accounting for realm-specific constructor identity. Object keys are strings or symbols after `ToPropertyKey` conversion. / JavaScript 有七种原始类型。对象按身份赋值和比较，但栈与堆的布局由引擎决定。基础类型判断可用 `typeof`，数组用 `Array.isArray`；使用 `instanceof` 判断构造函数的原型链关系时，应考虑 realm 中构造函数身份的差异。对象键经过 `ToPropertyKey` 后只能是字符串或 Symbol。

See [ECMAScript types and values](https://tc39.es/ecma262/2025/multipage/ecmascript-data-types-and-values.html) and [property key conversion](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-topropertykey). / 详见 [ECMAScript 类型和值](https://tc39.es/ecma262/2025/multipage/ecmascript-data-types-and-values.html) 与 [属性键转换](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-topropertykey)。

Related: [Map and Set / JavaScript 中的 Map 与 Set](./map-and-set.md); [Memory, WeakMap and WeakSet / JavaScript 内存、WeakMap 与 WeakSet](./javascript-memory-weakmap-and-weakset.md).
