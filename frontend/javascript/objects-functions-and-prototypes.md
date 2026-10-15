# Objects, Functions, and Prototypes / 对象、函数与原型

**Key terms / 关键词:** internal prototype 内部原型 · constructor 构造函数 · receiver 接收者 · property descriptor 属性描述符 · constructible 可构造

JavaScript objects delegate property lookup through an internal prototype link. Function call syntax determines the receiver for ordinary functions; arrow functions capture it lexically. These rules explain inheritance, this, new, and descriptors without assuming a particular engine memory layout. / JavaScript 对象通过内部原型链接委托属性查找。普通函数的调用语法决定接收者；箭头函数从词法作用域捕获接收者。这些规则可解释继承、this、new 和属性描述符，无需假设特定引擎的内存布局。

## Prototype lookup / 原型查找

Each ordinary object has an internal `[[Prototype]]` value, which may be null. If a property is not found on the object, lookup continues through that prototype chain. Use Object.getPrototypeOf and Object.create for explicit work with the chain. / 每个普通对象都有一个内部 `[[Prototype]]` 值，也可能为 null。对象上找不到属性时，会沿原型链继续查找。显式操作原型链时应使用 Object.getPrototypeOf 和 Object.create。

Many constructible function objects have an own property named `prototype`, which supplies the prototype for instances created by `new` when its value is an object. It is not present on every function: arrow functions and methods are not constructible and do not have it. The expression `__proto__` is a legacy accessor inherited from Object.prototype, not a special own property on every object. Prefer `Object.getPrototypeOf(obj)`. / 许多可构造函数对象都有名为 `prototype` 的自有属性；当其值为对象时，`new` 会将其用作实例原型。并非所有函数都有该属性：箭头函数和方法不可构造。表达式 `__proto__` 是从 Object.prototype 继承的历史访问器，并非每个对象都有的特殊自有属性。优先使用 `Object.getPrototypeOf(obj)`。

```javascript
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
```

```javascript
const ordinary = {};
Object.getPrototypeOf(ordinary) === Object.prototype; // true

const custom = Object.create({ greet: "hello" });
custom.greet; // inherited value

const dictionary = Object.create(null);
dictionary.toString; // undefined
```

The legacy Object.prototype.__proto__ accessor is documented as normative optional and legacy in ECMAScript. / ECMAScript 将历史 Object.prototype.__proto__ 访问器标为可选实现的历史特性，详见[规范](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html#sec-object.prototype.__proto__)。

## this is determined by the call / this 由调用方式决定

For an ordinary function, the call expression supplies the receiver. A method call obj.fn() supplies obj; a plain call to a strict function supplies undefined, while a plain sloppy-mode call substitutes the host’s global this value. In browser classic scripts that global is generally window; Node module wrappers have their own top-level conventions. / 对普通函数而言，调用表达式提供接收者。obj.fn() 这样的调用以 obj 为接收者；严格模式下普通函数调用的接收者是 undefined，非严格模式下则替换为宿主的全局 this。浏览器经典脚本中的全局对象通常是 window；Node 模块包装器有自己的顶层约定。

new creates a receiver; call/apply pass an explicit this value; bind creates a function with a bound receiver and leading arguments. A bound function used with new ignores its bound receiver, but keeps the bound arguments. Arrow functions use the surrounding this and cannot be rebound with call/apply/bind. / new 会创建接收者；call/apply 显式传入 this；bind 创建带绑定接收者和前置参数的新函数。绑定函数通过 new 调用时会忽略绑定接收者，但仍使用绑定参数。箭头函数使用外层 this，call/apply/bind 无法重新绑定它。

```javascript
const service = {
  url: "/data",
  fetch() { return this.url; }
};

service.fetch(); // "/data"
const detached = service.fetch;
detached(); // no longer uses service as its receiver

function describe(prefix, name) {
  return prefix + " " + name + " (" + this.role + ")";
}
describe.call({ role: "admin" }, "Hello", "Ada");
describe.apply({ role: "admin" }, ["Hello", "Ada"]);
const greetAdmin = describe.bind({ role: "admin" }, "Hello");
greetAdmin("Ada");
```

### Small binding exercise / 简化绑定练习

This helper demonstrates partial application for functions called with object receivers. It is not a replacement for Function.prototype.bind: native bind also handles constructor calls, constructibility, and function metadata. / 以下辅助函数演示对象接收者上的部分应用，并非 Function.prototype.bind 的替代品：原生 bind 还处理构造调用、可构造性和函数元数据。

```javascript
function bindForObjectReceiver(fn, receiver, ...leadingArgs) {
  return function (...laterArgs) {
    return fn.apply(receiver, [...leadingArgs, ...laterArgs]);
  };
}
```

Likewise, assigning a function to a temporary property can explain how a method call supplies this. This limited example only accepts an extensible object receiver and does not model primitive receivers or all exotic objects. A complete call/apply polyfill must also model strict functions, null/undefined, exceptions, and proxies. Use the built-ins in application code. / 把函数临时赋给对象属性可以说明方法调用如何提供 this。以下简化示例只接受可扩展对象接收者，不能处理原始值接收者或所有特殊对象。完整模拟 call/apply 还必须处理严格函数、null/undefined、异常和代理。应用代码应使用内置方法。

```javascript
function callWithObjectReceiver(fn, receiver, ...args) {
  if (receiver === null ||
      (typeof receiver !== "object" && typeof receiver !== "function")) {
    throw new TypeError("This example requires an object receiver");
  }
  const key = Symbol("temporary method");
  Object.defineProperty(receiver, key, { value: fn, configurable: true });
  try {
    return receiver[key](...args);
  } finally {
    delete receiver[key];
  }
}
```

## What new does / new 的行为

For a constructible function, new creates an object with the constructor’s effective prototype, calls the constructor with that object as this, and returns the explicit object/function result if one is returned. Primitive return values are ignored. Classes and built-ins have additional construction semantics. / 对可构造函数，new 会创建一个原型为构造函数有效原型的对象，以该对象作为 this 调用构造函数；若构造函数返回对象或函数，则返回该值，否则返回新对象。原始值返回会被忽略。class 和内置构造器还有额外语义。

The specification’s [`GetPrototypeFromConstructor`](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor) operation accepts any object-valued `prototype`, including a function, and otherwise uses the constructor realm’s intrinsic fallback. / 规范的 [`GetPrototypeFromConstructor`](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor) 会接受任何对象类型的 `prototype`（包括函数）；若不是对象，则使用构造函数所在 realm 的内置回退原型。

The following is a teaching model for ordinary constructors from the current realm; it is not a full polyfill for classes, bound functions, built-ins, proxies, or new.target. / 以下仅为当前 realm 中普通构造函数的教学模型，并非 class、绑定函数、内置构造器、代理或 new.target 的完整 polyfill。

```javascript
function emulateNew(fn, ...args) {
  const candidate = fn.prototype;
  const prototype =
    candidate !== null &&
    (typeof candidate === "object" || typeof candidate === "function")
      ? candidate
      : Object.prototype;
  const instance = Object.create(prototype);
  const result = fn.apply(instance, args);
  const isObject =
    result !== null &&
    (typeof result === "object" || typeof result === "function");
  return isObject ? result : instance;
}

function CallablePrototype() {}
function Example() {}
Example.prototype = CallablePrototype;
const example = emulateNew(Example);
Object.getPrototypeOf(example) === CallablePrototype; // true
```

## Methods and fields / 方法与字段

A function assigned in a constructor creates an own function property for each instance; a prototype method is shared through lookup. Choose based on per-instance state, identity, and behavior rather than assuming the prototype version is always faster. In class syntax, ordinary methods are placed on the prototype; instance fields create own properties on each instance; static methods and fields belong to the class constructor. / 在构造函数中赋值的函数会为每个实例创建自有函数属性；原型方法通过查找共享。应按实例状态、身份和行为选择，而不要假设原型方法一定更快。class 语法中的普通方法放在原型上；实例字段为每个实例创建自有属性；静态方法和字段属于类构造函数。

```javascript
class User {
  label = "member"; // own instance field
  greet() { return "Hi"; } // shared prototype method
  static category = "account"; // property on the class constructor
}

const user = new User();
Object.hasOwn(user, "label"); // true
Object.hasOwn(user, "greet"); // false
Object.hasOwn(User, "category"); // true
```

## Hidden classes are engine internals / 隐藏类属于引擎实现

V8 uses HiddenClasses (also called Maps) to track object shapes and optimize property access. Objects initialized with the same named properties in the same order can share a shape in V8. This is implementation-specific and may change; optimize object layouts only when profiling shows a real cost. / V8 使用 HiddenClasses（也称 Maps）跟踪对象形状并优化属性访问。在 V8 中，以相同顺序初始化相同命名属性的对象可能共享形状。这是实现细节，未来可能改变；只有性能分析显示确有成本时才优化对象布局。

The V8-specific mechanism and examples are described in [Fast properties in V8](https://v8.dev/blog/fast-properties). They are not ECMAScript guarantees. / V8 的具体机制与示例见 [V8 快速属性说明](https://v8.dev/blog/fast-properties)，这些不是 ECMAScript 保证。

## Static, instance, and prototype properties / 静态、实例与原型属性

Constructor properties, own instance properties, and prototype properties live on different objects. Own properties are found before inherited properties; a static property on the constructor is not part of an instance’s prototype lookup. / 构造函数属性、实例自有属性和原型属性属于不同对象。查找时先看自有属性，再看继承属性；构造函数上的静态属性不属于实例的原型查找链。

```javascript
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
```

## Property descriptors / 属性描述符

Own properties have attributes. Data properties use value and writable; accessor properties use get and set. Both kinds have enumerable and configurable. Object.defineProperty lets code set these explicitly. / 自有属性有属性特征。数据属性使用 value 和 writable；访问器属性使用 get 和 set。两类属性都有 enumerable 和 configurable。Object.defineProperty 可显式设置这些特征。

| Attribute / 特征 | Meaning / 含义 |
|---|---|
| value | Stored value / 存储值 |
| writable | Whether assignment may change a data property / 赋值是否可修改数据属性 |
| get / set | Accessor functions used on read or write / 读取或写入时调用的访问器函数 |
| enumerable | Included by own enumerable key APIs; for...in also walks the prototype chain / 自有可枚举键 API 会包含；for...in 还会遍历原型链 |
| configurable | Whether the property can generally be deleted or reconfigured / 通常能否删除或重新配置 |

```javascript
const record = {};
Object.defineProperty(record, "id", {
  value: 7,
  writable: false,
  enumerable: true,
  configurable: false
});

Object.getOwnPropertyDescriptor(record, "id");
// { value: 7, writable: false, enumerable: true, configurable: false }
```

An accessor can compute or validate a value on read or write. / 访问器可在读取或写入时计算或校验值。

```javascript
const profile = { _name: "John" };
Object.defineProperty(profile, "name", {
  get() { return this._name; },
  set(value) { this._name = value; },
  enumerable: true,
  configurable: true
});

profile.name; // "John" — calls the getter
profile.name = "Jo"; // calls the setter
profile._name; // "Jo"
```

An assignment to a non-writable property is ignored in sloppy code and throws in strict code. / 非严格代码中，对不可写属性赋值会被忽略；严格代码中会抛错。

**Interview answer / 面试回答:** Objects inherit through an internal prototype link. An object created by `constructorFn` normally inherits from that constructor’s object-valued `constructorFn.prototype`; this differs from `Function.prototype`, which function objects themselves typically inherit through their internal prototype link. `__proto__` is a legacy accessor. For ordinary functions, `this` follows the call form; arrows capture it lexically. `new` constructs an instance, and own properties shadow prototype properties. / 对象通过内部原型链接继承属性。由 `constructorFn` 创建的对象通常继承自其对象类型的 `constructorFn.prototype`；这与函数对象自身通常通过内部原型链接继承的 `Function.prototype` 不同。`__proto__` 是历史访问器。普通函数的 `this` 由调用方式决定；箭头函数从外层词法捕获。`new` 构造实例，自有属性会遮蔽原型属性。

See the [ECMAScript Object and Function sections](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html) for normative behavior. / 规范行为详见 [ECMAScript Object 与 Function 章节](https://tc39.es/ecma262/2025/multipage/fundamental-objects.html)。

Related: [JavaScript Types and Coercion / JavaScript 类型与类型转换](./javascript-types.md); [Scope and Closure / 作用域与闭包](./scope-and-closure.md).
