# When does Lodash _.merge mutate nested data? / Lodash _.merge 何时会修改嵌套数据？

_.merge(target, ...sources) mutates and returns its first argument. It recursively combines arrays and plain objects; arrays at the same property are merged by index rather than concatenated. Pass a fresh destination when the inputs must remain unchanged. / _.merge(target, ...sources) 会修改并返回第一个参数。它递归合并数组与普通对象；同一属性下的数组按索引合并，而不是拼接。若要保留输入对象，应传入新的目标对象。

~~~javascript
const target = { items: [{ left: 1 }, { keep: true }] };
const source = { items: [{ right: 2 }, { add: true }] };

const result = _.merge({}, target, source);
// result.items is [{ left: 1, right: 2 }, { keep: true, add: true }]
// target and source remain unchanged because the destination was fresh.
~~~

_.assign is shallow and also mutates its target. Other array methods including _.pull, _.remove, and _.reverse mutate their receiver, so avoid applying them directly to immutable UI state. See the maintained [Lodash reference](../../../frontend/libraries/lodash.md).

**Version source / 版本来源:** [Lodash 4.17.21 documentation](https://github.com/lodash/lodash/blob/4.17.21/doc/README.md).
