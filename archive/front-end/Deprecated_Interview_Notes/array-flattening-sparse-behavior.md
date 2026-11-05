# Why can array flattening produce different sparse holes? / 为什么不同数组展平方式会产生不同空位？

Flattening is not only about nesting depth: the operation determines how sparse positions are treated. In the archived repeated one-level concat example, spreading the outer array turns its hole into undefined, while concat preserves a hole in the nested array; native flat removes holes at flattened levels. / 展平不仅涉及嵌套深度，具体操作也决定稀疏位置如何处理。旧版逐层 concat 示例中，展开外层数组会把空位变成 undefined，而 concat 会保留嵌套数组中的空位；原生 flat 会移除被展平层级中的空位。

~~~javascript
const sparse = [, [, 1]];
const oneLevel = [].concat(...sparse);
// oneLevel is [undefined, , 1]
sparse.flat(Infinity); // [1]
~~~

The maintained iterative example uses repeated one-level concat; its specific sparse-array edge is shown above. It can also repeatedly copy a wide array or hit an argument-count limit. Use the maintained [JavaScript Arrays](../../../frontend/javascript/arrays.md) explanation for ordinary depth and recursion choices. This page preserves the sparse-hole boundary and original iterative form. / 普通深度和递归选择见维护中的 [JavaScript 数组](../../../frontend/javascript/arrays.md)；本页保留空位边界与原迭代写法。

**References / 规范:** [ECMAScript indexed collections](https://tc39.es/ecma262/2025/multipage/indexed-collections.html) and [ES2019 flat](https://tc39.es/ecma262/2019/#sec-array.prototype.flat).
