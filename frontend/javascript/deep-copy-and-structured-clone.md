# 如何安全地深拷贝 JavaScript 值？

报表要保存一份可独立编辑的快照时，浅复制只会新建外层数组或对象，嵌套 `owner` 仍可能与当前界面共享。所谓“深拷贝”没有脱离数据模型的通用实现：先确认输入类型、循环引用、共享子对象、原型行为和所有权边界，再选择 `JSON`、`structuredClone`（结构化克隆）或范围受限的手写复制器。

复制建立新的对象图；它不回答两个值是否满足同一结构契约。若只需判断受限纯数据是否结构相等，见[JavaScript 如何按约定比较对象与数组？](./javascript-types.md#结构比较要把输入范围写成契约)。

## JSON 往返只适合 JSON 形状的数据

`JSON.parse(JSON.stringify(value))` 不是通用拷贝：

- `Date` 会变成字符串，`Map` 和 `Set` 通常变成空对象。
- 对象中值为 `undefined`、函数或 `Symbol` 的字符串键属性会被省略；`Symbol` 键属性也不参与 JSON 序列化。数组空位及这些不支持的值会变成 `null`。
- BigInt 和循环引用会使序列化抛错。
- 不会保留对象身份或原型、属性描述符等结构。

~~~javascript
JSON.stringify([, undefined, NaN]); // "[null,null,null]"
~~~

如果数据契约本来就是 JSON 值，序列化可能足够；否则应选能表达实际对象图的复制策略。

## structuredClone 复制对象图并保留图内关系

structured clone（结构化克隆）算法由 `structuredClone(value)` 调用，返回新对象图。它支持多种标准内建类型，也能处理循环引用和多处指向同一个子对象的关系。复制后的节点与输入节点身份不同，但克隆结果内部原先共享的引用仍共享。

这里特意换成两条本来就共享同一个 `owner` 的记录，用来观察克隆保留图内共享关系；这与前章字段相似但身份不同的 `first` / `retry` 是不同输入。

~~~javascript
const sharedOwner = { id: "u-17", name: "Ada" };
const report = {
  rows: [
    { reportId: "r-104", amount: 0, owner: sharedOwner },
    { reportId: "r-105", amount: 120, owner: sharedOwner },
  ],
  focusedOwner: sharedOwner,
};
report.self = report;

const snapshot = structuredClone(report);
snapshot !== report; // true
snapshot.self === snapshot; // true：循环关系保留
snapshot.rows[0].owner === snapshot.rows[1].owner; // true：共享子对象关系保留
snapshot.focusedOwner === snapshot.rows[0].owner; // true
snapshot.rows[0].owner !== sharedOwner; // true：与原对象图分离
~~~

标准没有承诺所有对象都可克隆，也不保留任意类行为。函数、`WeakMap`（弱映射）、`Symbol` 值和普通 DOM `Node` 没有相应的序列化步骤，会抛 `DataCloneError`；普通类实例则按普通对象数据克隆，原型和方法不会随对象图复制。若属性值依赖 `getter`，序列化会读取值，访问器本身不会作为访问器复制。其他平台对象也要检查该类型是否定义了序列化步骤。

~~~javascript
class ReportRow {
  constructor() {
    this.reportId = "r-104";
  }
  label() {
    return this.reportId;
  }
}

const classCopy = structuredClone(new ReportRow());
Object.getPrototypeOf(classCopy) === Object.prototype; // true
classCopy.label; // undefined：实例方法没有复制

function cloneErrorName(value) {
  try {
    structuredClone(value);
    return "cloned";
  } catch (error) {
    return error.name;
  }
}

cloneErrorName(() => {}); // "DataCloneError"
cloneErrorName(new WeakMap()); // "DataCloneError"
cloneErrorName(Symbol("value")); // "DataCloneError"
~~~

`structuredClone` 的 `transfer`（转移）选项会转移可转移对象的底层资源，而不是复制一份；被转移的原输入将不再可用。`ArrayBuffer` 是常见示例：

~~~javascript
const buffer = new ArrayBuffer(8);
const transferred = structuredClone({ buffer }, { transfer: [buffer] });

transferred.buffer.byteLength; // 8
buffer.byteLength; // 0：原 buffer 已分离
~~~

只有所有权确实要交给另一端时才转移；否则普通 `structuredClone` 会保留输入并创建复制品。

新建包装对象不总表示底层数据独立。环境允许 `SharedArrayBuffer`（共享数组缓冲区）时，结构化克隆会产生新包装对象，但它们仍指向同一块共享字节；要获得独立快照，应显式复制数据。

~~~javascript
const sharedBuffer = new SharedArrayBuffer(1);
const sharedCopy = structuredClone(sharedBuffer);
const sourceByte = new Uint8Array(sharedBuffer);
const copiedByte = new Uint8Array(sharedCopy);

sharedCopy !== sharedBuffer; // true：包装对象不同
sourceByte[0] = 42;
copiedByte[0]; // 42：底层字节仍共享
~~~

## 何时 JSON 与 structuredClone 都不符合契约

若应用类型有限且需要定制属性语义，可实现范围受限的复制器。下面的实现支持同 `realm`（执行环境）的基础 `Date`、`RegExp`、`Map`、`Set`、数组，以及原型为当前 realm `Object.prototype` 或 `null` 的普通对象；它只递归自有、可枚举的字符串键。数组上的自有可枚举字符串扩展属性也会复制；`Date`、`RegExp`、`Map`、`Set` 上的扩展属性会被忽略。不要输入这些内建类型的自定义子类：`instanceof` 分支会将其降为对应基础类型，丢失子类原型和方法。`RegExp.lastIndex` 在此实现中按原值赋给副本，因此输入契约限定它为普通数字位置，不能带一个需独立复制的对象值。

`seen` 用 `WeakMap`（弱映射）在递归子项之前记录当前对象与副本的映射：再次遇到同一节点时直接返回已登记的副本，因此能保留循环回指和图内共享身份。输入契约还需说明其他边界：函数和 `Symbol` 值原样返回，不会隔离；`Symbol` 键和非枚举属性被忽略；访问器属性会通过读取 `value[key]` 执行 getter，结果被写成普通数据属性，原描述符不会保留。

> [!example]- 一个有限范围的递归复制器实现
>
> ~~~javascript
> function deepCopy(value, seen = new WeakMap()) {
>   if (value === null || typeof value !== "object") return value;
>   if (seen.has(value)) return seen.get(value);
>
>   let copy;
>   if (value instanceof Date) {
>     copy = new Date(value.getTime());
>   } else if (value instanceof RegExp) {
>     copy = new RegExp(value.source, value.flags);
>     copy.lastIndex = value.lastIndex;
>   } else if (value instanceof Map) {
>     copy = new Map();
>     seen.set(value, copy);
>     for (const [key, item] of value) {
>       copy.set(deepCopy(key, seen), deepCopy(item, seen));
>     }
>     return copy;
>   } else if (value instanceof Set) {
>     copy = new Set();
>     seen.set(value, copy);
>     for (const item of value) copy.add(deepCopy(item, seen));
>     return copy;
>   } else if (Array.isArray(value)) {
>     copy = new Array(value.length);
>   } else {
>     const prototype = Object.getPrototypeOf(value);
>     if (prototype !== Object.prototype && prototype !== null) {
>       throw new TypeError("Unsupported object type");
>     }
>     copy = Object.create(prototype);
>   }
>
>   seen.set(value, copy);
>   if (value instanceof Date || value instanceof RegExp) return copy;
>
>   for (const key of Object.keys(value)) {
>     Object.defineProperty(copy, key, {
>       value: deepCopy(value[key], seen),
>       enumerable: true,
>       writable: true,
>       configurable: true,
>     });
>   }
>   return copy;
> }
> ~~~

~~~javascript
const trailingHoles = deepCopy([1, , ,]);
trailingHoles.length === 3; // true
0 in trailingHoles; // true
1 in trailingHoles; // false
2 in trailingHoles; // false

const emptySparse = deepCopy(new Array(3));
emptySparse.length === 3; // true
Object.keys(emptySparse); // []

const extendedArray = Object.assign([, 1], { note: "extra" });
deepCopy(extendedArray).note; // "extra"
~~~

这个实现不是通用库的替代品。只要输入可能带 getter、副作用、跨 realm 内建值、特殊宿主对象或未知原型，就应缩小输入契约或采用已定义这些类型行为的标准机制，而不是静默地产生错误的“副本”。

> [!info]- 来源
> - `structuredClone` 的深拷贝、可转移对象及转移后原值不可用：[WHATWG HTML Living Standard §2.7.11 Structured cloning API](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning-api)，更新时间 2026-11-05。
> - 可序列化平台对象的约束、循环和重复引用：[WHATWG HTML Living Standard §2.7.1](https://html.spec.whatwg.org/multipage/structured-data.html#serializable-objects) 与 [§2.7.4 StructuredSerializeInternal](https://html.spec.whatwg.org/multipage/structured-data.html#structuredserializeinternal)；DOM `Node` 的接口定义：[DOM Standard §4.4](https://dom.spec.whatwg.org/#interface-node)。
> - 对象属性读取（包括 getter 执行）及反序列化：[WHATWG HTML Living Standard §2.7.4](https://html.spec.whatwg.org/multipage/structured-data.html#structuredserializeinternal) 与 [§2.7.7 StructuredDeserialize](https://html.spec.whatwg.org/multipage/structured-data.html#structureddeserialize)。
> - `Date.prototype.getTime()` 的时间值读取：[ECMAScript 2026 §21.4.4.23](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-date.prototype.gettime)。
> - 本章代码核对：Node.js v26.11.1 / V8 14.6.202.34-node.37，2026-11-06。
