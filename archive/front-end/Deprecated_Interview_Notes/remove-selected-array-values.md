# How can selected values be removed from an array? / 如何从数组中移除指定值？

Use filter when the original array should stay unchanged; use in-place splice only when mutation is part of the caller's contract. If the removal list is large, build a Set once instead of scanning it for every element. / 应保留原数组时使用 filter；只有调用方契约要求原地修改时才用 splice。移除列表较大时先建 Set，避免为每个数组项反复扫描名单。

The functional source form is concise and keeps order, but includes inside filter can do O(n·m) comparisons for an input of length n and removal list of length m:

~~~javascript
const removeWithFilter = (items, ...excluded) =>
  items.filter(item => !excluded.includes(item));
~~~

For deliberate in-place mutation, do not advance the index after a match; the next value shifts into the removed position. Repeated removals can still make work quadratic:

~~~javascript
function removeInPlace(items, ...excluded) {
  let index = 0;
  while (index < items.length) {
    if (excluded.includes(items[index])) items.splice(index, 1);
    else index++;
  }
  return items;
}
~~~

For a large exclusion list, keep the input immutable while using Set membership:

~~~javascript
const removeWithSet = (items, ...excluded) => {
  const removed = new Set(excluded);
  return items.filter(item => !removed.has(item));
};
~~~

These examples remove matching primitive or identity-equal values. Removing objects by a field requires an explicit key comparison; see [JavaScript Arrays](../../../frontend/javascript/arrays.md).
