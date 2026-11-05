# How do JavaScript objects find and organize properties? / JavaScript 对象如何查找和组织属性？

**Core answer / 核心回答：** An object first checks its own properties, then follows its internal prototype link until a match or the end of the chain. Constructor prototypes supply a default prototype to instances created with new, while instance fields, prototype methods, static members, and property descriptors control where properties live and how they behave. / 对象先查自有属性，再沿内部原型链接向上查找，直到找到匹配属性或到达链尾。构造函数的 prototype 为 new 创建的实例提供默认原型；实例字段、原型方法、静态成员和属性描述符决定属性的位置与行为。

## How prototype lookup works / 原型查找如何工作

An ordinary object has an internal `[[Prototype]]` value, which may be null. If a property is missing from the object, lookup continues along this chain. Use Object.getPrototypeOf and Object.create when the chain must be inspected or created explicitly. / 普通对象有一个内部 `[[Prototype]]` 值，也可能为 null。对象上找不到属性时，查找会沿原型链继续。需要显式检查或创建原型链时，使用 Object.getPrototypeOf 和 Object.create。

Many constructible functions have an own property named prototype. When that value is an object, new uses it as the prototype for the created instance. It is distinct from Function.prototype, which function objects themselves normally inherit through their own internal prototype link. Arrow functions and methods are not constructible and do not have an own prototype property. The legacy __proto__ accessor is inherited from Object.prototype; prefer Object.getPrototypeOf. / 许多可构造函数有名为 prototype 的自有属性；若该值为对象，new 会把它用作新实例的原型。它不同于 Function.prototype，后者通常是函数对象自身通过内部原型链接继承的对象。箭头函数和方法不可构造，也没有自有 prototype 属性。历史访问器 __proto__ 从 Object.prototype 继承而来；优先使用 Object.getPrototypeOf。

~~~javascript
function Person(name) {
  this.name = name;
}
Person.prototype.greet = function () {
  return "Hello, " + this.name;
};

const ada = new Person("Ada");
ada.greet(); // "Hello, Ada"
Object.getPrototypeOf(ada) === Person.prototype; // true
Object.getPrototypeOf(Person.prototype) === Object.prototype; // true
Object.getPrototypeOf(Object.prototype); // null
~~~

Object.create lets code choose a prototype directly. A null-prototype object has no inherited toString method, which can be useful for dictionaries. / Object.create 可直接选择原型。null 原型对象没有继承 toString 方法，可用于字典。

~~~javascript
const ordinary = {};
Object.getPrototypeOf(ordinary) === Object.prototype; // true

const custom = Object.create({ greet: "hello" });
custom.greet; // inherited value

const dictionary = Object.create(null);
dictionary.toString; // undefined
~~~

The old Object.prototype.__proto__ accessor is a legacy, normative-optional feature in ECMAScript. / ECMAScript 将旧版 Object.prototype.__proto__ 访问器标记为历史且规范可选的特性，见[规范](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-object.prototype.__proto__)。

## Where instance, prototype, and static properties live / 实例、原型与静态属性分别在哪里

A function assigned inside a constructor becomes an own function property on each instance. A prototype method is found through the shared prototype. Class methods are placed on the prototype; class instance fields create own properties; static members belong to the class constructor itself. Choose based on state, identity, and behavior rather than assuming one placement is always faster. / 在构造函数中赋值的函数会成为每个实例上的自有函数属性；原型方法则通过共享原型查找。class 方法放在原型上，实例字段创建自有属性，静态成员属于 class 构造函数本身。应按状态、身份和行为选择，不要假设某一种布局总是更快。

~~~javascript
class User {
  label = "member";                // own instance field
  greet() { return "Hi"; }         // shared prototype method
  static category = "account";     // property on the class constructor
}

const user = new User();
Object.hasOwn(user, "label");      // true
Object.hasOwn(user, "greet");      // false
Object.hasOwn(User, "category");   // true
~~~

Own properties are checked before inherited ones; an own value can shadow a prototype method. Static properties on the constructor are not part of an instance’s prototype lookup. / 自有属性先于继承属性查找；自有值可以遮蔽原型方法。构造函数上的静态属性不属于实例的原型查找链。

~~~javascript
function Example() {
  Example.value = function () { return 1; };
  this.value = function () { return 2; };
}
Example.prototype.value = function () { return 3; };
Example.value = function () { return 4; };

Example.value(); // 4
const instance = new Example();
instance.value(); // 2: own property shadows the prototype method
Example.value(); // 1: constructor body replaced the static property
~~~

## How property descriptors affect reads and writes / 属性描述符如何影响读写

Own properties have attributes. A data property stores a value and may be writable; an accessor property uses getter and setter functions. Both kinds also have enumerable and configurable attributes. Object.defineProperty sets them explicitly. / 自有属性有属性特征。数据属性保存值并可设置是否可写；访问器属性通过 getter 和 setter 函数读写。两种属性都有 enumerable 和 configurable 特征，可由 Object.defineProperty 显式设置。

| Attribute / 特征 | Meaning / 含义 |
|---|---|
| value | Stored value / 存储值 |
| writable | Whether assignment may change a data property / 赋值是否能修改数据属性 |
| get / set | Functions used when reading or writing an accessor property / 访问器属性读写时调用的函数 |
| enumerable | Included in own-enumerable key APIs; for...in also walks the prototype chain / 自有可枚举键 API 会包含；for...in 还遍历原型链 |
| configurable | Whether the property can generally be deleted or reconfigured / 通常能否删除或重新配置 |

~~~javascript
const record = {};
Object.defineProperty(record, "id", {
  value: 7,
  writable: false,
  enumerable: true,
  configurable: false
});
Object.getOwnPropertyDescriptor(record, "id");
// { value: 7, writable: false, enumerable: true, configurable: false }
~~~

A setter can validate or normalize writes; a getter can compute a read. Assignment to a non-writable property is ignored in sloppy code and throws in strict code. / setter 可校验或规范写入值；getter 可在读取时计算。非严格代码对不可写属性的赋值会被忽略，严格模式则会抛错。

~~~javascript
const profile = { _name: "John" };
Object.defineProperty(profile, "name", {
  get() { return this._name; },
  set(value) { this._name = value; },
  enumerable: true,
  configurable: true
});

profile.name; // "John"
profile.name = "Jo";
profile._name; // "Jo"
~~~

## Which object shapes are engine-specific / 哪些对象形状细节属于引擎实现

V8 uses HiddenClasses (also called Maps) to track object shapes and optimize property access. Objects initialized with the same named properties in the same order can share a shape in V8. This is an implementation detail, not an ECMAScript guarantee; optimize layouts only when profiling identifies a real cost. / V8 使用 HiddenClasses（也称 Maps）跟踪对象形状并优化属性访问。在 V8 中，以相同顺序初始化相同命名属性的对象可能共享形状。这是实现细节，不是 ECMAScript 保证；只有性能分析发现实际成本时才优化布局。

See [Fast properties in V8](https://v8.dev/blog/fast-properties). For how a call supplies this and how new creates an instance, see [Function this and Binding / 函数 this 与绑定](./this-and-function-binding.md) and [Construction with new / 使用 new 构造对象](./construction-and-new.md).
