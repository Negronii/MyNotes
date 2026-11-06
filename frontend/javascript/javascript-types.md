# JavaScript 值如何转换、比较，并成为属性键？

报表结果里，金额 0、缺失的数组位置、两个字段相同的记录，看起来都像“没有数据”或“同一条记录”；JavaScript 会按不同规则处理它们。本章从一次结果导入开始，先分清值与对象身份，再说明比较和属性键转换。后续章节沿用这组输入：

~~~javascript
const owner = { id: "u-17", name: "Ada" };
const first = { reportId: "r-104", amount: 0, owner };
const retry = {
  reportId: "r-104",
  amount: 120,
  owner: { id: "u-17", name: "Ada" },
};
const rows = [first, , retry]; // 第二个位置是空位；第三项是重试记录
~~~

业务字段 reportId 相同，表示两条输入记录描述同一业务实体；first 与 retry 仍是两个对象。它们的 owner 字段也指向内容相同、身份不同的对象。

## 值的类型决定哪些转换有意义

JavaScript 有七种 primitive types（原始值类型）：`undefined`（未定义值）、`null`（空值）、`Boolean`（布尔值）、`Number`（数值）、`BigInt`（大整数）、`String`（字符串）和 `Symbol`（符号）。`Symbol()` 每次调用都会产生新值；`Symbol.for(key)` 则会从全局注册表取回同一注册符号。其他值都是 `object`（对象），函数也属于对象。对象赋值复制的是对象引用值，两个变量可以指向同一个对象；这是一条语言行为规则，不意味着对象一定物理存放在某个特定内存区域。

| 类型 | 本章会用到的行为 |
|---|---|
| `undefined` | 缺少属性或越界读取的常见结果；也可显式存入属性 |
| `null` | 显式表示“当前没有对象”；历史兼容使 `typeof null` 返回 `"object"` |
| `Boolean` | 只有 `false` 为假值 |
| `Number` | `binary64`（二进制 64 位浮点）数值；包含 `NaN`、正负无穷和带符号的零 |
| `BigInt` | 任意精度整数；不能直接与 `Number` 混做算术 |
| `String` | 不可变的 UTF-16 `code unit` 序列 |
| `Symbol` | 唯一的原始值，可作为属性键 |

值的运行时存储位置和布局由引擎决定；reference type（引用类型）可用来简称对象按身份传递的语义，但不能据此推断栈、堆或指针布局。

## 真值转换不是数值转换

`0` 是假值，但空数组和空对象是真值；非空字符串 `"false"` 也是真值。`Number` 转换遵循另一套规则，因此输入含义重要时应显式转换。

对普通值，`Boolean(value)` 与 `!!value` 都执行真值转换。

~~~javascript
Boolean("false");  // true
Boolean([]);       // true
Boolean({});       // true

Number("");        // 0
Number(null);      // 0
Number(undefined); // NaN

Number.isNaN(NaN);  // true
Number.isNaN("x");  // false：不做隐式转换
~~~

浏览器里的历史对象 `document.all` 是例外：它带有标准附录定义的特殊行为，`Boolean(document.all)` 为 `false`，`typeof document.all` 为 `"undefined"`，且 `document.all == null` 为 `true`。这不是普通对象的真值规则，业务代码不应依赖它。

逻辑运算也不会自动把结果变成 `Boolean`。逻辑与 `&&` 返回某个操作数，因此 React 条件渲染中，`0 && <ItemList />` 的结果是 `0`，可能直接显示数字零；条件需要表达“条数大于零”时就写出比较条件。

~~~jsx
0 && <ItemList />; // 结果为 0

function ReportPanel({ validCount, rows }) {
  return validCount > 0 ? <ItemList items={rows} /> : null;
}
~~~

## 比较运算回答的是不同问题

strict equality（严格相等，`===`）不做跨类型强制转换；loose equality（宽松相等，`==`）遵循多条转换规则，包括 `null == undefined` 这一特殊情况。除非特意使用转换规则，通常优先用 `===`。对一般输入，`value == null` 是一种有意同时判断 `null` 与 `undefined` 的写法。

对象比较关注的是 identity（身份）：两个对象字段相同，也不会因此变成同一对象。

~~~javascript
first.reportId === retry.reportId; // true：业务字段相等
first === retry;                    // false：对象身份不同
first.owner === retry.owner;        // false：嵌套对象身份不同

5 == "5";              // true
5 === "5";             // false
null == undefined;     // true
~~~

几个常见比较规则的差别集中在 NaN、有符号零和对象上：

| 操作 | NaN 与自身 | +0 与 -0 | 对象 |
|---|---|---|---|
| === | 不相等 | 相等 | 按身份 |
| `Object.is`（SameValue，同值） | 相等 | 不同 | 按身份 |
| `Map`（映射） / `Set`（集合，SameValueZero，同值零） | 相等 | 相等 | 按身份 |

~~~javascript
NaN === NaN;                    // false
Object.is(NaN, NaN);            // true
Object.is(+0, -0);              // false
new Set([NaN, NaN, -0, +0]).size; // 2
~~~

`Map` 和 `Set` 使用 SameValueZero（同值零），所以它们既能识别重复 `NaN`，也会把 `+0` 和 `-0` 视为同一个键或成员。集合章节把这个规则用于报表索引和去重，见[何时使用 Map、Set 或普通对象？](./map-and-set.md)。

`Number` 采用 IEEE 754 `binary64`（二进制 64 位浮点）；`0.1` 和 `0.2` 这样的十进制小数通常没有精确的有限二进制表示。比较结果是否可接受需要由金额精度、容差和舍入规则共同决定，不能把某个固定 `epsilon`（误差容限）当作所有领域的通用答案。

~~~javascript
0.1 + 0.2 === 0.3; // false
Math.abs((0.1 + 0.2) - 0.3) < 1e-12; // 对这个量级的例子成立
~~~

金额可在币种规则允许时用最小单位整数表示，或使用明确舍入规则的十进制运算。

## 变量保存对象身份，不会自动复制对象

把对象赋给新变量后，两个绑定仍指向同一个对象。属性赋值会先求出并记录左侧的基对象，再求右侧；右侧即使重新绑定变量，也不会改变已记录的基对象。

~~~javascript
let a = { n: 1 };
const b = a;
a.x = a = { n: 2 };

a.x; // undefined
b.x; // { n: 2 }：写入落在先前记录的旧对象上
~~~

函数实参按值传递：形参拿到实参值的副本。实参若是原始值，修改形参不改调用方的绑定；若是对象，副本仍指向同一对象，所以属性变更可见，但重新给形参赋另一个对象不会重绑调用方变量。

~~~javascript
function update(count, profile) {
  count += 1;
  profile.name = "Grace";
  profile = { name: "Replacement" };
}

let count = 1;
const profile = { name: "Ada" };
update(count, profile);
count;        // 1
profile.name; // "Grace"
~~~

这也解释了浅拷贝为何会共享嵌套对象：新数组或新记录只复制了里面的对象引用。数组变异、复制和空位规则见[数组操作怎样处理空位与复制？](./arrays.md)；需要隔离整张对象图时见[如何安全地深拷贝 JavaScript 值？](./deep-copy-and-structured-clone.md)。

## 类型检查能回答什么，不能证明什么

- `typeof` 适合检查原始值和函数，但 `typeof null` 的历史结果是 "object"。
- `Array.isArray` 检查数组，也能识别来自另一个 realm（执行环境）的数组。
- `instanceof` 通常检查构造函数的 `prototype` 是否出现在对象原型链上。不同 realm 的构造函数拥有不同 prototype，因此本地 Array 检查另一个窗口创建的数组可能为 false；`Symbol.hasInstance` 还可以定制检查。
- `Object.prototype.toString.call(value)` 给出内建标签，但 `Symbol.toStringTag` 可以改变显示结果，标签不是类型证明。

~~~javascript
typeof null; // "object"
Array.isArray([]); // true

const misleading = { [Symbol.toStringTag]: "Array" };
Object.prototype.toString.call(misleading); // "[object Array]"，但它不是数组
~~~

应检查程序真正需要的形状或行为，而不是只依赖通用标签。

## 普通对象属性键会先转换

普通对象的属性键只能是字符串或 `Symbol`。方括号里传入其他值时，JavaScript 会执行 `ToPropertyKey`（转成属性键）；对象可以通过 `Symbol.toPrimitive` 等钩子影响转换结果，因此不能简单概括为“总是调用 `toString`”。

~~~javascript
const dictionary = {};
dictionary[123] = "number key";
dictionary["123"]; // "number key"

const accountKey = {
  [Symbol.toPrimitive]: () => "account",
};
dictionary[accountKey] = "Ada";
dictionary.account; // "Ada"

dictionary[first] = "first object";
dictionary[retry]; // "first object"：两个对象默认都转成 "[object Object]"
~~~

如果键需要保持对象身份、数字与字符串必须区分，或需要任意类型的键，使用 `Map`。若普通对象确实是字典，可用 `Object.create(null)` 去掉继承原型行为，并用 `Object.hasOwn` 检查自有属性。键值集合的选择见[何时使用 Map、Set 或普通对象？](./map-and-set.md)。

## 枚举与复制属性时，先看 API 选中了什么

`Object.keys`、`Object.values` 和 `Object.entries` 读取对象的自有、可枚举、字符串键属性；`Symbol` 键不在结果中。普通对象的数组索引键先按数值升序排列，其他字符串键按创建顺序排列；`Proxy` 和特殊对象可能有不同的键顺序。`for...in` 还会遍历可枚举的继承字符串键，因此对象数据和数组索引应选不同的遍历方式。

~~~javascript
const record = { name: "Ada", age: 36 };
Object.keys(record);   // ["name", "age"]
Object.values(record); // ["Ada", 36]
Object.entries(record); // [["name", "Ada"], ["age", 36]]

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

`Object.assign(target, ...sources)` 把来源对象的自有可枚举字符串键和 `Symbol` 键浅复制到已有 target，修改并返回 target，后面的来源覆盖前面的属性。读取来源可能触发 getter，写入 target 可能触发 setter。对象展开也浅复制，但会在新对象上创建数据属性，不会写入传入的已有 target。

~~~javascript
const target = { a: 1, b: 2 };
Object.assign(target, { b: 3, c: 4 });
// target 是 { a: 1, b: 3, c: 4 }

const defaults = { retries: 2 };
const overrides = { retries: 4 };
const merged = { ...defaults, ...overrides };
// merged 是新对象；retries 为 4，defaults 不变
~~~

这些方法适合检查或组装属性记录，不会深拷贝嵌套对象。数组的复制、迭代输入与空位结果见[数组操作怎样处理空位与复制？](./arrays.md)；复杂对象图的隔离见[如何安全地深拷贝 JavaScript 值？](./deep-copy-and-structured-clone.md)。

## 缺失属性默认值与解构

读取嵌套字段时，optional chaining（可选链）运算符 `?.` 只在紧邻值为 `null` 或 `undefined` 时停止，不把 `0`、`false` 或空字符串当成缺失。根变量本身若未声明，使用 `?.` 仍会抛 `ReferenceError`；用括号结束一段链后，括号外的普通属性读取也不再受短路保护。

~~~javascript
const report = { profile: null, rows };
report.profile?.name; // undefined
report.rows[0]?.amount; // 0：合法的零值
report.rows[1]?.amount; // undefined：读取空位

const count = 0;
count?.toFixed(0); // "0"：零既非 null 也非 undefined

const key = "value";
({ value: 1 })?.[key]; // 1
const maybeCall = undefined;
maybeCall?.(); // undefined

const user = null;
user?.profile?.name; // undefined
// (user?.profile).name; // TypeError：括号结束了短路链
// undeclaredUser?.name; // ReferenceError：根标识符不存在
~~~

若只有缺省值应触发回退，使用 nullish coalescing（空值合并）运算符 `??`；`||` 会把所有假值都替换。它们在此沿用同一个报表值，因此金额 `0` 仍保留，而空位读取产生的 `undefined` 会触发默认值。`??` 与 `||` 或 `&&` 不能不加括号混用。

~~~javascript
report.rows[0].amount ?? 100; // 0
report.rows[0].amount || 100; // 100
report.rows[1]?.amount ?? 100; // 100
~~~

destructuring（解构）把属性或可迭代值绑定到局部变量。默认初始化仅在读到 `undefined` 时运行，所以不会覆盖合法零值、`false`、空字符串或 `null`。对象剩余项收集来源对象余下的自有可枚举属性，但只复制一层；数组解构按迭代器取值，空位读成 `undefined`，而省略绑定仍会向前消费一个值。

~~~javascript
const { amount: firstAmount = 100, owner: firstOwner, ...rowFields } = first;
// firstAmount 是 0；firstOwner 仍是 first.owner；rowFields 只创建浅层新对象

const { profile = { name: "Guest" } } = report;
profile; // null：默认值只处理 undefined

const [firstRow, , ...tail] = rows;
firstRow === first; // true
tail[0] === retry; // true：rest 收集剩余项，形成新数组
1 in rows; // false：被省略的项对应空位
~~~

数组解构和数组展开同样消费迭代器，空位的其他读取结果见[数组空位如何改变遍历结果？](./arrays.md#空位怎样改变遍历结果)；同一个属性是否缺失或显式为 `undefined`，也不能只靠读取结果区分。

## 模板标签收到值，但不会自动净化它

模板字面量（template literal）会把表达式插入文本。tagged template（带标签模板）调用函数时，会把固定文本片段和各个表达式值分开传入；标签函数可以做格式化或领域处理，但插入用户输入不会因此自动安全。

~~~javascript
function capture(strings, ...values) {
  return { strings: [...strings], values };
}

const untrusted = "<b>user text</b>";
capture`label: ${untrusted}`;
// strings 是 ["label: ", ""]；values 是 ["<b>user text</b>"]
~~~

标签函数需要按实际输出上下文选择转义或净化规则，不能把“使用了 tagged template”当作安全保证。报表文本进入 DOM 时的上下文边界见[报表标题进入 DOM 时如何避免 XSS？](../../engineering-foundations/security/web-browser-security-boundaries.md)。

> [!info]- 来源
> - 值类型、原始值与对象行为：[ECMAScript 2026 §6.1–6.2](https://tc39.es/ecma262/2026/multipage/ecmascript-data-types-and-values.html)。
> - 严格相等、SameValue、SameValueZero 和 ToPropertyKey：[ECMAScript 2026 §7.2.9–7.2.14、§7.1.19](https://tc39.es/ecma262/2026/multipage/abstract-operations.html)。
> - `document.all` 的历史例外：[ECMAScript 2026 Annex B IsHTMLDDA internal slot](https://tc39.es/ecma262/2026/multipage/additional-ecmascript-features-for-web-browsers.html#sec-IsHTMLDDA-internal-slot)。
> - `instanceof` 与 `Object.prototype.toString` 的检查行为：[ECMAScript 2026 §13.10.2 InstanceofOperator](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-instanceofoperator)、[§20.1.3.6 Object.prototype.toString](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.prototype.tostring)。
> - Object.keys / values / entries 与 Object.assign 的属性范围：[ECMAScript 2026 §20.1.2](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html)；普通对象的键顺序：[§10.1.11.1 OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys)。
> - 可选链与空值合并的短路条件、运算优先级：[ECMAScript 2026 §13.3.9 Optional Chains](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-optional-chains) 与 [§13.13 Binary Logical Operators](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-binary-logical-operators)。
> - 对象与数组解构默认值、剩余项和迭代读取：[ECMAScript 2026 §14.3.3 Destructuring Binding Patterns](https://tc39.es/ecma262/2026/multipage/ecmascript-language-statements-and-declarations.html#sec-destructuring-binding-patterns)；数组迭代器：[§23.1.3.38](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.values)。
> - 带标签模板调用参数的组成：[ECMAScript 2026 §13.3.11 Tagged Templates](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-tagged-templates)。
> - React 条件渲染中 0 会作为结果呈现：[React 文档 Conditional Rendering](https://react.dev/learn/conditional-rendering)，访问于 2026-11-06。
> - 本章代码核对：Node.js v26.11.1 / V8 14.6.202.34-node.37，2026-11-06。
