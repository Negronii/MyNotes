# How does JavaScript Proxy intercept object operations? / JavaScript Proxy 如何拦截对象操作？

**Core answer / 核心回答：** A Proxy pairs a target object with a handler. When code operates through the proxy, matching handler traps can intercept reads, writes, deletion, membership checks, and other operations; Reflect methods forward an operation with its normal semantics. Proxy is a JavaScript runtime feature, not a TypeScript type feature. / Proxy 将目标对象与 handler 配对。代码通过代理执行操作时，对应 trap 可拦截读取、写入、删除、成员检查等行为；Reflect 方法可按正常语义转发操作。Proxy 是 JavaScript 运行时功能，不是 TypeScript 类型特性。

~~~javascript
const handler = {
  get(target, property, receiver) {
    console.log("read", property);
    return Reflect.get(target, property, receiver);
  },
  set(target, property, value, receiver) {
    console.log("write", property);
    return Reflect.set(target, property, value, receiver);
  }
};

const data = new Proxy({ count: 0 }, handler);
data.count;    // logs "read", then returns 0
data.count = 1; // logs "write", then updates the target
~~~

Typical uses include reactive state, validation, and instrumentation. A proxy only observes operations that pass through it; a retained reference to the original target can bypass its traps. A proxy can intercept later-added properties, unlike defining a getter for each known property, but the object’s invariants and compatibility requirements still matter. / 常见用途包括响应式状态、校验和测量。代理只能观察经由代理执行的操作；若代码保留原始 target 的引用，就能绕过这些 trap。代理可以拦截后来添加的属性，而逐个定义 getter 做不到，但仍须考虑对象不变量和兼容性。

Vue 2 used property getters and setters for reactivity; Vue 3 uses proxies for reactive objects. This is an example of framework implementation, not a guarantee that every reactive system needs Proxy. / Vue 2 使用属性 getter 和 setter 实现响应式；Vue 3 的响应式对象使用代理。这是框架实现示例，不代表所有响应式系统都必须使用 Proxy。

Vue 2 used property getters and setters for reactivity, while Vue 3 uses proxies for reactive objects. See [Vue Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth). This framework example does not imply that every reactive system needs Proxy. / Vue 2 使用属性 getter 和 setter 实现响应式，Vue 3 则对响应式对象使用代理。详见 [Vue 响应式原理](https://vuejs.org/guide/extras/reactivity-in-depth)。框架示例不意味着所有响应式系统都必须使用 Proxy。

See [ECMAScript Proxy objects](https://tc39.es/ecma262/2025/multipage/proxy-object.html) for trap invariants and [Reflect](https://tc39.es/ecma262/2025/multipage/reflection.html) for forwarding operations.
