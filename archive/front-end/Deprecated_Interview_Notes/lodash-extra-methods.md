# Which less-common Lodash helpers are useful to recognize? / 哪些不常见的 Lodash 工具值得识别？

This version-scoped lookup retains Lodash 4.17.21 methods omitted from the maintained short catalog. Their return and mutation contracts should be checked before substituting a native expression. / 本版本参考补充了维护版简短目录未列出的 Lodash 4.17.21 方法；用原生表达式替换前应核对返回值和是否修改输入。

| Method | Contract |
|---|---|
| _.concat(array, ...values) | Returns a shallowly concatenated array; nested arrays supplied as values remain nested. |
| _.drop(array, n = 1) | Returns a slice after dropping the first n elements. |
| _.each(collection, iteratee) | Visits collection values and returns the original collection; it also has the _.forEach alias. |
| _.find(collection, predicate, fromIndex = 0) | Returns the first match or undefined; the start index applies to array search. |
| _.keys(object) | Returns own enumerable string-keyed property names. |
| _.times(n, iteratee) | Invokes an iteratee n times and returns the result array. |

~~~javascript
_.concat([1], 2, [3], [[4]]); // [1, 2, 3, [4]]
_.drop([1, 2, 3], 2); // [3]
_.times(3, String); // ['0', '1', '2']
~~~

The maintained [Lodash note](../../../frontend/libraries/lodash.md) is the canonical broad catalog. See the adjacent archive questions for nested merge mutation and the limited, runtime-local behavior of _.uniqueId.

**Version source / 版本来源:** [Lodash 4.17.21 API reference](https://github.com/lodash/lodash/blob/4.17.21/doc/README.md).
