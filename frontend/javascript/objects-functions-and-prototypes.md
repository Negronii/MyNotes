# JavaScript 对象如何查找属性并组织成员？

普通对象读取属性时，own property（自有属性）先于继承属性；若没有找到，语言会沿 `[[Prototype]]` 链继续查找。构造函数的 prototype 属性用于建立实例原型，函数对象自身的原型链则是另一条关系。property descriptor（属性描述符）说明属性保存一个值，还是在读取或写入时执行 getter/setter。

## 属性查找沿原型链进行

读取 `object.key` 时先检查自有属性。若没有匹配项，普通对象会沿原型链继续查找，直到找到属性或到达 `null`。`Object.hasOwn` 只检查自有属性；`in` 还会检查继承属性。

~~~javascript
const base = { kind: "report" };
const record = Object.create(base);
record.title = "Q4";

Object.hasOwn(record, "title"); // true
Object.hasOwn(record, "kind");  // false
"kind" in record;               // true
Object.getPrototypeOf(record) === base; // true
~~~

内部 `[[Prototype]]` 链接不是名为 `prototype` 的属性。许多可构造函数有自有的 `prototype` 属性，`new` 会用它作为实例的默认原型。函数对象自身则通过另一个内部链接继承，通常指向 `Function.prototype`。箭头函数和简洁方法不能用 `new` 调用，也没有自有 `prototype` 属性。需要检查原型时优先使用 `Object.getPrototypeOf`，而不是旧式 `__proto__` 访问器。

## 报表服务把实例状态与共享行为分开

案例背景：每个 `service` 都有独立的 `prefix` 和处理器。原型上只有一个共享的 `format` 方法。调用 `service.onReport` 会把 `service` 作为 `this`；处理器仍持有工厂创建的 `tag` 和 `calls` 绑定。

~~~javascript
function makeReportHandler(tag) {
  let calls = 0;
  return function onReport(report) {
    "use strict";
    calls += 1;
    return this.format(report, tag, calls);
  };
}

function ReportService(prefix) {
  this.prefix = prefix;                         // 自有数据属性
  this.onReport = makeReportHandler("daily"); // 自有函数属性，带有闭包状态
}

ReportService.prototype.format = function (report, tag, sequence) {
  return this.prefix + "/" + tag + ": " + report.title + " #" + sequence;
};

const service = new ReportService("Sales");
service.onReport({ title: "Q4" }); // "Sales/daily: Q4 #1"
service.onReport({ title: "Q4" }); // "Sales/daily: Q4 #2"
Object.hasOwn(service, "format"); // false；查找会沿原型找到 ReportService.prototype.format
Object.getPrototypeOf(service) === ReportService.prototype; // true
~~~

`service.prefix` 和 `service.onReport` 是自有属性，`service.format` 则从共享原型查找。这里 `ReportService` 函数的自有 `prototype` 对象成为实例的原型；它与函数对象自身的原型链不是同一概念。

`class` 语法同样将成员放在不同位置：实例字段创建自有属性，普通方法与访问器放在 class 原型上，静态成员属于 class 构造函数。

~~~javascript
class User {
  label = "member";                         // 实例自有字段
  get displayLabel() { return this.label; } // 原型上的访问器
  greet() { return "Hi"; }                  // 原型上的共享方法
  static category = "account";              // 构造函数上的属性
}

const user = new User();
Object.hasOwn(user, "label"); // true
Object.hasOwn(user, "greet"); // false
Object.hasOwn(Object.getPrototypeOf(user), "displayLabel"); // true
Object.hasOwn(User, "category"); // true
~~~

## 属性描述符决定读写是否执行代码

属性描述符分为保存值和可写标记的数据描述符，以及包含 getter/setter 的访问器描述符。两类描述符都有 `enumerable` 与 `configurable` 标记。使用 `Object.defineProperty` 新建属性时，未提供的标记默认为 `false`。更新同类型描述符时，未提供的字段保留原值；只有可配置属性才能在数据描述符与访问器描述符之间切换；切换时，旧类型专有字段会移除，新类型专有字段按默认值创建，但未提供的 `enumerable` 与 `configurable` 等共同字段仍保留。对象字面量中的普通数据属性默认可写、可枚举且可配置。

| 字段 | 作用 |
|---|---|
| `value`、`writable` | 存储值，以及赋值能否修改它 |
| `get`、`set` | 读取或写入时调用的函数 |
| `enumerable` | `Object.keys` 等只列出自有、可枚举的字符串键；`for...in` 还会沿原型链遍历可枚举字符串键 |
| `configurable` | 通常能否删除或重新配置 |

~~~javascript
const profile = { _name: "John" };
Object.defineProperty(profile, "name", {
  get() { return this._name; },
  set(value) { this._name = value; },
  enumerable: true,
  configurable: true,
});

profile.name;        // "John"；读取时调用 getter
profile.name = "Jo"; // 调用 setter
profile._name;       // "Jo"
~~~

更新描述符时，只有提供的字段会改变；从数据描述符切换为访问器描述符，或反向切换时，专属于旧类型的字段会消失。

~~~javascript
const descriptorDemo = {};
Object.defineProperty(descriptorDemo, "item", {
  value: 1, writable: true, enumerable: true, configurable: true,
});

Object.defineProperty(descriptorDemo, "item", { value: 2 });
const sameType = Object.getOwnPropertyDescriptor(descriptorDemo, "item");
[sameType.value, sameType.writable, sameType.enumerable, sameType.configurable];
// [2, true, true, true]

Object.defineProperty(descriptorDemo, "item", { get() { return 3; } });
const switchedToAccessor = Object.getOwnPropertyDescriptor(descriptorDemo, "item");
[descriptorDemo.item, typeof switchedToAccessor.get, switchedToAccessor.set,
  switchedToAccessor.enumerable, switchedToAccessor.configurable];
// [3, "function", undefined, true, true]

Object.defineProperty(descriptorDemo, "item", { value: 4 });
const switchedToData = Object.getOwnPropertyDescriptor(descriptorDemo, "item");
[switchedToData.value, switchedToData.writable,
  switchedToData.enumerable, switchedToData.configurable];
// [4, false, true, true]

Object.defineProperty(descriptorDemo, "fresh", { value: 1 });
const fresh = Object.getOwnPropertyDescriptor(descriptorDemo, "fresh");
[fresh.writable, fresh.enumerable, fresh.configurable]; // [false, false, false]
~~~

getter 是会执行的代码：读取属性可能产生副作用、抛错或继续读取其他属性。若 getter 是继承来的，读取时的接收者会成为它的 `this`；当读取经过 Proxy 时，这点很重要。setter 可以校验或规范写入。严格代码向不可写属性或只有 getter 的访问器赋值会抛出 `TypeError`；非严格代码中写入可能静默失败。

实例上的自有属性会先于同名原型方法找到。构造函数上的静态属性不属于实例的查找链。

~~~javascript
function Example() {
  Example.value = function () { return 1; };
  this.value = function () { return 2; };
}
Example.prototype.value = function () { return 3; };
Example.value = function () { return 4; };

Example.value(); // 4
const instance = new Example();
instance.value(); // 2：自有属性遮蔽原型方法
Example.value(); // 1：构造函数体替换了静态属性
~~~

`Object.create(null)` 会创建一个没有原型、也不会继承 `toString` 的字典对象。

~~~javascript
const dictionary = Object.create(null);
dictionary.toString; // undefined
~~~

V8 的隐藏对象形状及转换可以优化属性访问，但这是实现选择，不是 ECMAScript 保证；只有性能分析确认存在瓶颈时才应调整属性布局。

**相关机制：** [函数 `this` 与绑定](./this-and-function-binding.md) 说明方法调用如何提供接收者；[使用 `new` 构造对象](./construction-and-new.md) 跟进实例原型的选择；[Proxy 代理对象](./proxy.md) 解释被拦截的读取、getter 与写入。


> [!info]- 来源
> - 自有属性、原型查找与访问器 `receiver`：[ECMAScript OrdinaryGet](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryget)（§10.1.8.1）。
> - 描述符定义和默认属性标记：[ECMAScript Object.defineProperty](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.defineproperty)（§20.1.2.4）。
> - `Object.prototype.__proto__` 是规范标记为 Normative Optional（规范可选）和 Legacy（遗留）的特性：[ECMAScript 2026 Object.prototype.__proto__](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.prototype.__proto__)（§20.1.3.8）。
> - V8 的隐藏对象形状与属性访问优化：[V8 Fast Properties](https://v8.dev/blog/fast-properties)。
