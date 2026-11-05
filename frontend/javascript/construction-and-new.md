# What does new do when it constructs an object? / new 构造对象时做了什么？

**Core answer / 核心回答：** For a constructible function, new creates a receiver whose prototype comes from the constructor’s effective prototype, calls the constructor with that receiver as this, then returns an explicit object or function result if supplied. A primitive return is ignored. / 对可构造函数，new 会创建一个原型取自构造函数有效 prototype 的接收者，以它作为 this 调用构造函数；若构造函数显式返回对象或函数，则返回该值，否则返回新接收者。原始值返回会被忽略。

~~~mermaid
flowchart LR
  A["Read effective constructor prototype"] --> B["Create receiver with that prototype"]
  B --> C["Call constructor with receiver as this"]
  C --> D{"Did it return an object or function?"}
  D -- "yes" --> E["Return explicit result"]
  D -- "no: undefined or primitive" --> F["Return created receiver"]
~~~

## Constructor and instance relationship / 构造函数与实例的关系

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
~~~

The prototype used for an instance is the constructor’s object-valued prototype property, not Function.prototype. If its prototype value is not an object, the language falls back to the appropriate intrinsic prototype; the exact fallback depends on the constructor’s realm. The specification’s [GetPrototypeFromConstructor](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor) accepts any object-valued prototype, including a function. / 实例所用原型来自构造函数的对象类型 prototype 属性，不是 Function.prototype。若该属性不是对象，语言会回退到相应内置原型；具体回退取决于构造函数所在 realm。规范的 [GetPrototypeFromConstructor](https://tc39.es/ecma262/2025/multipage/ordinary-and-exotic-objects-behaviours.html#sec-getprototypefromconstructor) 接受任何对象类型的 prototype，包括函数。

## Object returns replace the created receiver / 返回对象会替换新建接收者

~~~javascript
function ReturnsPrimitive() {
  this.created = true;
  return 1;
}
new ReturnsPrimitive(); // the new object with created: true

function ReturnsObject() {
  this.ignored = true;
  return { replacement: true };
}
new ReturnsObject(); // { replacement: true }
~~~

A teaching model for ordinary constructors from the current realm makes the main steps visible. It is not a full polyfill for classes, bound functions, built-ins, proxies, or new.target. / 以下普通当前 realm 构造函数教学模型展示主要步骤；它不是 class、绑定函数、内置构造器、代理或 new.target 的完整 polyfill。

~~~javascript
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
~~~

Classes and built-in constructors have additional construction semantics, so use new or class syntax in application code rather than this teaching helper. For property lookup and the roles of instance, prototype, and static members, see [Objects and Prototypes / 对象与原型](./objects-functions-and-prototypes.md).
