# When does a JavaScript Proxy add value, and how is it different from a getter? / JavaScript Proxy 何时有用，它与 getter 有何不同？

A Proxy intercepts selected object operations through traps; it can validate writes or instrument reads, but its behavior is observable and it is not a transparent speed optimization. An accessor defines a getter or setter for a property; it does not intercept arbitrary operations on the object. / Proxy 通过 trap 拦截指定对象操作，可用于写入校验或读取监测，但会改变可观察行为，不是透明的性能优化。访问器为属性定义 getter/setter，并不会拦截对象上的任意操作。

~~~javascript
const product = new Proxy({ price: 10 }, {
  get(target, property, receiver) {
    console.log('read ' + String(property));
    return Reflect.get(target, property, receiver);
  },
  set(target, property, value, receiver) {
    if (property === 'price' && (!Number.isFinite(value) || value < 0)) {
      throw new RangeError('price must be a non-negative finite number');
    }
    return Reflect.set(target, property, value, receiver);
  },
});

product.price = 12;
product.price; // 12; the get trap also runs
~~~

One operation can trigger multiple traps: array.push(value) may assign an index and update length. Test operations relied on and preserve Proxy invariants. The archived getter illustration used a side effect on every read; it demonstrates that getters are property accessors, not Proxies, and is not a recommended application pattern.

For the JavaScript mechanism and Reflect forwarding, see [Advanced TypeScript: Proxy](../../../frontend/typescript/advanced-typescript.md). For design-pattern trade-offs, see [Design Patterns in Practice](../../../engineering-foundations/architecture/design-patterns-in-practice.md).

**Specification / 规范:** [ECMAScript Proxy objects](https://tc39.es/ecma262/2025/multipage/reflection.html#sec-proxy-objects).
