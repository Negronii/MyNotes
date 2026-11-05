# How do you deep-copy a JavaScript value safely? / 如何安全地深拷贝 JavaScript 值？

Choose a copy policy from the value's data model. JSON round-tripping only supports JSON-shaped values; `structuredClone()` supports more built-in data and cycles but not functions, DOM nodes, or arbitrary class behavior. A handwritten clone should state a narrow contract and preserve cycles and repeated references with a `WeakMap`. / 应按数据模型选择复制策略。JSON 往返只支持 JSON 形状的数据；`structuredClone()` 支持更多内建类型和循环引用，但不支持函数、DOM 节点或任意类行为。手写克隆必须声明有限的支持范围，并通过 `WeakMap` 保留循环和重复引用。

## Why JSON round-tripping is limited / JSON 往返的限制

`JSON.parse(JSON.stringify(value))` changes or loses values: `Date` becomes a string; `Map` and `Set` typically become empty objects; object properties with `undefined`, functions, or symbols are omitted; array entries for unsupported values become `null`; and cycles or `BigInt` cause serialization to throw. For supported structured-cloneable data, use `structuredClone(value)`; see [Modern JavaScript Features / 现代 JavaScript 特性](./modern-javascript-features.md) for the platform API contract.

## A bounded handwritten clone / 有限范围的手写克隆

This example supports same-realm `Date`, `RegExp`, `Map`, `Set`, arrays, and plain objects with enumerable own string keys. It preserves sparse array holes, cycles, and repeated references. It deliberately rejects arbitrary prototypes and does not preserve symbols, descriptors, accessors, or custom properties on special built-ins.

~~~javascript
function deepCopy(value, seen = new WeakMap()) {
  if (value === null || typeof value !== "object") return value;
  if (seen.has(value)) return seen.get(value);

  let copy;
  if (value instanceof Date) {
    copy = new Date(value.getTime());
  } else if (value instanceof RegExp) {
    copy = new RegExp(value.source, value.flags);
    copy.lastIndex = value.lastIndex;
  } else if (value instanceof Map) {
    copy = new Map();
    seen.set(value, copy);
    for (const [key, item] of value) {
      copy.set(deepCopy(key, seen), deepCopy(item, seen));
    }
    return copy;
  } else if (value instanceof Set) {
    copy = new Set();
    seen.set(value, copy);
    for (const item of value) copy.add(deepCopy(item, seen));
    return copy;
  } else if (Array.isArray(value)) {
    copy = new Array(value.length);
  } else {
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) {
      throw new TypeError("Unsupported object type");
    }
    copy = Object.create(prototype);
  }

  seen.set(value, copy);
  if (value instanceof Date || value instanceof RegExp) return copy;

  for (const key of Object.keys(value)) {
    Object.defineProperty(copy, key, {
      value: deepCopy(value[key], seen),
      enumerable: true,
      writable: true,
      configurable: true,
    });
  }
  return copy;
}
~~~

The sparse-array fixtures ensure copying does not turn holes into explicit properties:

~~~javascript
const trailingHoles = deepCopy([1, , ,]);
console.assert(
  trailingHoles.length === 3 &&
  0 in trailingHoles &&
  !(1 in trailingHoles) &&
  !(2 in trailingHoles)
);

const emptySparse = deepCopy(new Array(3));
console.assert(emptySparse.length === 3 && Object.keys(emptySparse).length === 0);
~~~

This is a sample for a bounded data model, not a universal clone algorithm. A production copier must decide how to handle symbols, descriptors, getters, host objects, custom prototypes, and accessors with side effects.

**See also:** [Modern JavaScript Features / 现代 JavaScript 特性](./modern-javascript-features.md) defines `structuredClone`; [JavaScript Memory, WeakMap, WeakSet, and WeakRef](./javascript-memory-weakmap-and-weakset.md) covers weak-key lifetime.
