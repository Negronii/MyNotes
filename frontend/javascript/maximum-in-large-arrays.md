# What is a safe way to find a maximum in a huge array? / 如何安全地求超大数组中的最大值？

`Math.max(...values)` and `Math.max.apply(null, values)` expand every element into the call's argument list; an implementation may reject a very large list, and the limit is not portable. A loop or `reduce()` avoids the argument-list limit. Preserve the intended empty-array and non-number policy explicitly. / `Math.max(...values)` 和 `Math.max.apply(null, values)` 会把每个元素展开为函数实参；参数列表过大时实现可能拒绝调用，且没有可移植的固定上限。循环或 `reduce()` 不会遇到这个实参列表限制。应明确空数组及非数字输入的预期语义。

~~~javascript
function maxOfNumbers(values) {
  let max = -Infinity; // Math.max() with no arguments also returns -Infinity.
  for (const value of values) {
    max = Math.max(max, value);
  }
  return max;
}
~~~

For numeric inputs, the loop preserves `Math.max` semantics: an empty iterable yields `-Infinity` and any `NaN` makes the result `NaN`. If the product should reject empty input, coerce strings, or skip invalid values, validate that policy before the loop rather than relying on implicit conversion.

**See also:** [JavaScript Arrays / JavaScript 数组](./arrays.md) covers array iteration choices.

**Specification:** [ECMAScript: `Math.max`](https://tc39.es/ecma262/2026/#sec-math.max), checked 2026-11-05.
