# How do JavaScript values convert, compare, and become property keys? / JavaScript 值如何转换、比较并成为属性键？

**Core answer / 核心回答：** JavaScript has seven primitive types; all other values are objects, including functions. Conversions are operation-specific, equality operators use different rules, and ordinary object properties accept only strings or symbols after key conversion. Objects assigned to variables retain identity rather than being copied. / JavaScript 有七种原始类型，其余值都是对象，包括函数。转换取决于具体操作，相等运算符采用不同规则，普通对象属性键经过转换后只能是字符串或 Symbol。赋值对象时保留的是身份，不是对象副本。

## Value types and useful facts / 类型与要点

| Type / 类型 | Useful fact / 要点 |
|---|---|
| undefined | Default value of an uninitialized var binding or a missing result / 未初始化 var 绑定或缺失结果的默认值 |
| null | Intentional absence; typeof null is the historical string "object" / 表示有意为空；typeof null 因历史兼容结果为 "object" |
| boolean | Falsy values include false, 0, -0, 0n, "", null, undefined, and NaN / 假值包括这些值 |
| number | IEEE 754 binary64; includes NaN and infinities / IEEE 754 binary64，包含 NaN 与无穷值 |
| bigint | Arbitrary-precision integers; cannot mix with Number arithmetic without conversion / 任意精度整数；算术运算不能直接与 Number 混用 |
| string | Immutable sequence of UTF-16 code units / 不可变的 UTF-16 码元序列 |
| symbol | Unique primitive value, often used as a property key / 唯一原始值，常用作属性键 |


These value categories are specified in [ECMAScript types and values](https://tc39.es/ecma262/2025/multipage/ecmascript-data-types-and-values.html). / 类型和值定义见 [ECMAScript 类型和值规范](https://tc39.es/ecma262/2025/multipage/ecmascript-data-types-and-values.html)。
Whether an engine stores values on a stack, heap, or elsewhere is an implementation detail. “Reference type” is useful shorthand for object identity and assignment, not a physical memory guarantee. / 值在栈、堆或其他位置存储属于引擎实现细节。“引用类型”适合描述对象身份和赋值语义，不是物理内存保证。

## Truthiness is not numeric conversion / 真值转换不等于数值转换

Empty arrays and objects are truthy. An empty string and zero are falsy, while the nonempty string "false" is truthy. Number conversion follows different rules: Number("") and Number(null) are 0; Number(undefined) is NaN. Use explicit conversion when the input contract matters. / 空数组和空对象是真值。空字符串和零是假值，而非空字符串 "false" 是真值。数值转换遵循另一套规则：Number("") 和 Number(null) 为 0，Number(undefined) 为 NaN。输入契约重要时应显式转换。

~~~javascript
Boolean("false"); // true
Boolean([]);      // true
Number("");       // 0
Number(null);     // 0
Number(undefined);// NaN

Number.isNaN(NaN);  // true
Number.isNaN("x"); // false: no coercion
~~~

For ordinary values, Boolean(value) and !!value both apply truthiness conversion. The legacy browser document.all exception has the special `[[IsHTMLDDA]]` behavior: it is falsy, typeof returns "undefined", and it loosely equals nullish values. It is not an ordinary object. / 对普通值而言，Boolean(value) 和 !!value 都执行真值转换。浏览器历史对象 document.all 具有特殊 `[[IsHTMLDDA]]` 行为：它是假值，typeof 返回 "undefined"，并且与 nullish 值宽松相等。它不是普通对象。

See [ECMAScript Annex B IsHTMLDDA](https://tc39.es/ecma262/2025/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot). / 详见 [ECMAScript 附录 B IsHTMLDDA](https://tc39.es/ecma262/2025/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot)。

Logical AND returns one of its operands, not a Boolean. In React, a numeric zero on the left can therefore render as zero; compare with zero explicitly when the result should be a component or nothing. / 逻辑与会返回其中一个操作数，而非布尔值。因此在 React 中，左侧数字 0 可能直接显示为 0；若结果应当是组件或空内容，就显式比较是否大于零。

~~~jsx
{items.length > 0 && <ItemList items={items} />}
~~~

See [React conditional rendering](https://react.dev/learn/conditional-rendering) and [Advanced React / React 进阶](../frameworks/advanced-react.md) for the rendered behavior.

## How equality rules differ / 相等比较规则有何差别

Strict equality === does not coerce across different types. Loose equality == follows several conversion rules, including the special null == undefined case; it is not simply “convert both sides to the same type.” Prefer === unless coercion is intentional. For ordinary values, value == null intentionally tests both null and undefined. / 严格相等 === 不会在不同类型间转换。宽松相等 == 遵循多条转换规则，包括 null == undefined 这一特殊情况；它并非简单地“把双方转成相同类型”。除非有意依赖转换，否则优先使用 ===。对普通值而言，value == null 可有意同时判断 null 和 undefined。

The normative equality and coercion operations are in [ECMAScript abstract operations](https://tc39.es/ecma262/2025/multipage/abstract-operations.html). / 规范的相等与转换操作见 [ECMAScript 抽象操作](https://tc39.es/ecma262/2025/multipage/abstract-operations.html)。

| Comparison / 比较 | NaN with itself / NaN 自身比较 | +0 with -0 / 有符号零比较 | Object values / 对象值 |
|---|---|---|---|
| === | false | equal / 相等 | identity / 身份 |
| Object.is (SameValue) | true | different / 不同 | identity / 身份 |
| Map/Set (SameValueZero) | same / 相同 | equal / 相等 | identity / 身份 |

~~~javascript
5 == "5";            // true
5 === "5";           // false
null == undefined;   // true
NaN === NaN;         // false
Object.is(NaN, NaN); // true
Object.is(+0, -0);   // false
new Set([NaN, NaN]).size; // 1
~~~

## Why decimal comparisons need a domain rule / 十进制数值比较为何需要场景规则

Number uses binary64, so many decimal fractions such as 0.1 and 0.2 do not have exact finite binary representations. Arithmetic may therefore produce a nearby representable result. The acceptable tolerance depends on the value’s scale and domain; there is no universal epsilon that is correct for every comparison. / Number 使用 binary64，0.1、0.2 等许多十进制小数都无法用有限二进制位精确表示，算术结果可能是邻近的可表示值。可接受容差取决于数值尺度和业务领域，不存在适用于所有比较的统一 epsilon。

~~~javascript
0.1 + 0.2 === 0.3; // false
Math.abs((0.1 + 0.2) - 0.3) < 1e-12; // true for this scale and example
~~~

For money, use integer minor units when the currency rules allow it, or use decimal arithmetic with an explicit rounding policy. / 金额计算可在币种规则允许时使用整数最小单位，或采用明确舍入规则的十进制运算。

## Object assignment preserves identity / 对象赋值保留身份

Assigning an object to another binding makes both bindings refer to the same object. In a property assignment, JavaScript evaluates and remembers the base object before it evaluates the right-hand side. / 把对象赋给另一绑定后，两者引用同一个对象。属性赋值会先求值并记录基对象，然后才求值右侧。

~~~javascript
let a = { n: 1 };
const b = a;
a.x = a = { n: 2 };

a.x; // undefined
b.x; // { n: 2 }
~~~

The left side captures the original object before the right side reassigns a. The final write still targets that captured original object, now also named b. / 左侧在右侧重新绑定 a 前就记录了旧对象；最终写入仍作用于该旧对象，此时它也由 b 引用。

Function arguments follow the same value rule: a parameter receives a copy of its argument value. When that value is an object reference, property mutation is visible through the caller’s reference, but assigning a different object to the parameter does not reassign the caller’s binding. / 函数实参同样按值传递：形参接收实参值的副本。若该值是对象引用，修改属性可通过调用方的引用观察到；但把形参重新赋为另一个对象不会重新绑定调用方变量。

~~~javascript
function update(count, profile) {
  count += 1;
  profile.name = "Grace";
  profile = { name: "Replacement" };
}

let count = 1;
const profile = { name: "Ada" };
update(count, profile);
count;        // 1: the primitive argument value was copied
profile.name; // "Grace": the object reference value was copied
~~~

## How to check a value’s type / 如何判断值的类型

- typeof is useful for primitives and functions, with the historical null result shown above.
- Array.isArray reliably recognizes arrays, including arrays from another realm.
- instanceof normally checks whether the constructor’s .prototype occurs in the value’s prototype chain. Constructors from separate realms normally have distinct prototype objects, so a foreign value can fail against the local constructor but pass against its own realm’s constructor. Symbol.hasInstance can customize the check.
- Object.prototype.toString.call(value) reports a built-in tag, but Symbol.toStringTag can change the displayed tag. It is not a definitive type proof.

~~~javascript
typeof null; // "object"
Array.isArray([]); // true

const custom = { [Symbol.toStringTag]: "Array" };
Object.prototype.toString.call(custom); // "[object Array]" — a spoofable tag
~~~

Validate the shape or behavior the program actually requires instead of relying on a generic display string. The normative [Object.prototype.toString](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-object.prototype.tostring) algorithm defines the built-in tag operation; the normative [OrdinaryHasInstance](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-ordinaryhasinstance) algorithm describes the default instanceof rule. / 应按程序实际需要验证结构或行为，不要只依赖通用显示字符串。规范的 [Object.prototype.toString](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-object.prototype.tostring) 算法定义内置标签操作；[OrdinaryHasInstance](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-ordinaryhasinstance) 描述默认 instanceof 规则。

## How bracket notation converts object keys / 方括号属性如何转换键

An ordinary property key is a string or a symbol. When another value is used inside brackets, JavaScript applies ToPropertyKey; an object can run Symbol.toPrimitive or other conversion hooks before producing a string or symbol. It is not accurate to say every key simply calls toString(). / 普通属性键是字符串或 Symbol。方括号中使用其他值时，JavaScript 执行 ToPropertyKey；对象可在生成字符串或 Symbol 前运行 Symbol.toPrimitive 等转换钩子。不能简单说所有键都会直接调用 toString()。

The [ToPropertyKey abstract operation](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-topropertykey) defines this conversion. / [ToPropertyKey 抽象操作](https://tc39.es/ecma262/2025/multipage/abstract-operations.html#sec-topropertykey)定义了这一转换。

~~~javascript
const record = {};
record[123] = "number";
record["123"]; // "number"

const key = { [Symbol.toPrimitive]: () => "account" };
record[key] = "Ada";
record.account; // "Ada"

const first = { id: 1 };
const second = { id: 1 };
record[first] = "overwritten key";
record[second]; // "overwritten key": both became the string "[object Object]"

const map = new Map();
map.set(first, "first identity");
map.set(second, "second identity"); // Map does not coerce object keys
~~~

Use Map when object identity or uncoerced non-string keys matter. Plain-object dictionaries still convert property keys; Object.create(null) removes inherited prototype behavior, and Object.hasOwn tests own membership safely. See [Map and Set / JavaScript 中的 Map 与 Set](./map-and-set.md). / 若需要对象身份或未经转换的非字符串键，使用 Map。普通对象字典仍会转换键；Object.create(null) 可去掉继承原型，Object.hasOwn 可安全判断自有属性。另见 [Map and Set / JavaScript 中的 Map 与 Set](./map-and-set.md).

**Related:** [Other JavaScript Topics / JavaScript 其他主题](./other-javascript-topics.md) covers strict mode; [Object and Array Methods / 对象与数组方法](./es6-new-methods.md) explains own enumerable keys and copying APIs.
