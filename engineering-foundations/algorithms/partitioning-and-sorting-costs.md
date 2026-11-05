# Why do partition choices change quicksort costs? / 分区选择为什么会改变快速排序的代价？

Each partition groups values around a pivot. Balanced partitions keep the recursion shallow, while repeatedly skewed partitions make later calls process nearly the original input size. The representation also determines whether the algorithm copies data. / 分区按基准值分组。较均衡的分区使递归较浅，持续偏斜则让后续调用仍要处理接近原规模的数据。表示方式还会决定是否复制数据。

## Sorting

### Quicksort

This array-building version is easy to inspect, but it is not in-place. With balanced partitions it takes O(n log n) time; an adversarial sequence of pivots can take O(n²) time and O(n) recursive stack space.

~~~javascript
function quickSort(values) {
  if (values.length <= 1) return values;
  const pivot = values[Math.floor(values.length / 2)];
  const lower = [];
  const equal = [];
  const higher = [];
  for (const value of values) {
    if (value < pivot) lower.push(value);
    else if (value > pivot) higher.push(value);
    else equal.push(value);
  }
  return [...quickSort(lower), ...equal, ...quickSort(higher)];
}
~~~

For application code, prefer the built-in sort with an explicit comparator for numeric data: `values.sort((a, b) => a - b)` mutates the array, while `values.toSorted((a, b) => a - b)` returns a sorted copy where supported. Without a comparator, array elements are compared as strings. ECMAScript requires stable sorting; the engine's specific sorting algorithm is an implementation detail. See [ECMAScript 2020, Array.prototype.sort](https://tc39.es/ecma262/2020/#sec-array.prototype.sort).

---

[Back to the main question / 返回主问题](algorithms-and-complexity.md).
