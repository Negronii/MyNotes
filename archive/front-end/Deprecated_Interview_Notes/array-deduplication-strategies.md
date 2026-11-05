# How do array deduplication strategies differ? / 数组去重策略有什么区别？

Choose an equality rule before choosing an implementation. Set preserves first-seen order and uses SameValueZero; a field-keyed Map compares records by that field and keeps the latest value for a repeated key; a sort-based implementation changes order and needs matching comparison and equality functions. / 先确定相等规则，再选实现。Set 按 SameValueZero 保留首次出现顺序；按字段建键的 Map 用该字段比较记录，并在键重复时保留最后一个值；排序实现会改变顺序，且比较和相等函数必须一致。

A simple indexOf filter is a useful contrast: indexOf uses strict equality, so it removes every NaN; filter also skips sparse holes.

~~~javascript
const values = [NaN, NaN, 1, 1];
values.filter((value, index) => values.indexOf(value) === index); // [1]
[...new Set(values)]; // [NaN, 1]
~~~

For object records, the canonical [JavaScript Arrays](../../../frontend/javascript/arrays.md) note shows a Map keyed by the field that defines identity. When ordering is acceptable, sort a copy and keep one value per comparator-defined equivalence group. The comparator must put equivalent values together:

~~~typescript
function uniqueSorted<T>(
  items: T[],
  compare: (left: T, right: T) => number,
  same: (left: T, right: T) => boolean,
): T[] {
  const result: T[] = [];
  for (const item of [...items].sort(compare)) {
    if (result.length === 0 || !same(result[result.length - 1], item)) result.push(item);
  }
  return result;
}
~~~

The maintained [JavaScript Arrays](../../../frontend/javascript/arrays.md) note is canonical for Set/Map equality and complexity. These examples preserve the distinct indexOf/NaN and comparator-based variants. / Set/Map 相等规则和复杂度的规范解释见维护中的 [JavaScript 数组](../../../frontend/javascript/arrays.md)；本页保留 indexOf/NaN 与比较器变体。
