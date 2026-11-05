# When should a UI use Lodash instead of a native JavaScript operation? / 界面何时应使用 Lodash 而不是原生 JavaScript？

**Core answer / 核心回答：** Use Lodash when its documented path, collection, or timing contract removes repeated edge-case code. For a simple known shape, prefer the native operation when it expresses the same behavior more clearly; compare the exact semantics and installed version before substituting. This page is a method lookup, not a claim that one option is always smaller or faster. / Lodash 的路径、集合或定时语义能减少重复的边界处理时可使用它。对象结构简单明确时，如果原生操作能更清晰表达相同行为，就优先考虑原生 API；替换前要核对具体语义和安装版本。本文用于查找方法，不表示某种选择总是更小或更快。

## Common utilities / 常用工具

### Arrays / 数组

| Signature | Behavior |
|---|---|
| _.chunk(array, size) | Split into groups of up to size items. |
| _.compact(array) | Remove false, null, 0, empty string, undefined, and NaN. |
| _.difference(array, values) | Keep values from the first array that are absent from the other array; returns a new array. |
| _.intersection(array, ...arrays) | Return values present in all arrays. |
| _.flatten(array) / _.flattenDeep(array) | Flatten one level / recursively flatten nested arrays. |
| _.uniq(array) | Return a new array with duplicate values removed. |

~~~javascript
_.chunk([1, 2, 3, 4], 2);          // [[1, 2], [3, 4]]
_.difference([2, 1], [2, 3]);     // [1]
_.intersection([1, 2], [2, 3]);   // [2]
_.flatten([1, [2, [3]]]);         // [1, 2, [3]]
~~~

Native Array.prototype.flat() defaults to depth 1; flat(Infinity) recursively flattens. That corresponds to the one-level and recursive distinction above, not a universal replacement for all Lodash collection semantics.

### Collections / 集合

| Signature | Behavior |
|---|---|
| _.filter(collection, predicate) | Return every matching value. |
| _.find(collection, predicate) | Return the first matching value, or undefined. |
| _.map(collection, iteratee) | Transform values in arrays or object collections. |
| _.reduce(collection, iteratee, accumulator) | Accumulate values into one result. |
| _.groupBy(collection, iteratee) | Build an object whose keys come from the iteratee and whose values are matching arrays. |
| _.sortBy(collection, iteratees) | Sort ascending by one or more criteria. |
| _.orderBy(collection, iteratees, orders) | Sort by criteria with explicit asc/desc directions. |

~~~javascript
_.groupBy([6.1, 4.2, 6.3], Math.floor); // { "4": [4.2], "6": [6.1, 6.3] }
_.orderBy(users, ["age", "name"], ["desc", "asc"]);
~~~

### Objects / 对象

| Signature | Behavior |
|---|---|
| _.get(object, path, defaultValue) | Read a deep path; use the default only when the resolved value is undefined. |
| _.set(object, path, value) | Create path segments as needed and mutate the target object. |
| _.merge(target, ...sources) | Recursively merge enumerable properties and mutate target. |
| _.assign(target, ...sources) | Shallow-assign own enumerable properties and mutate target. |
| _.pick(object, paths) / _.omit(object, paths) | Return a new object with selected / excluded paths. |
| _.cloneDeep(value) | Recursively clone values supported by Lodash's clone rules. |

~~~javascript
const city = _.get(user, "address.city", "Unknown");
const nullableCity = { address: { city: null } };
_.get(nullableCity, "address.city", "Unknown"); // null
nullableCity.address?.city ?? "Unknown";       // "Unknown"
~~~

The difference matters: Lodash's get default handles an absent path or undefined value, while JavaScript's nullish coalescing operator also falls back for null. For a statically known path, optional chaining plus an explicit fallback may be clearer.

### Strings / 字符串

| Signature | Example result |
|---|---|
| _.camelCase(string) | _.camelCase("Foo BAR") → "fooBar" |
| _.kebabCase(string) | _.kebabCase("fooBar") → "foo-bar" |
| _.snakeCase(string) | _.snakeCase("fooBar") → "foo_bar" |
| _.capitalize(string) | _.capitalize("hello") → "Hello" |
| _.startCase(string) | _.startCase("fooBar") → "Foo Bar" |

## Debounce and throttle / 防抖与节流

**Core answer / 核心回答：** Debounce delays work until calls stop for a wait period; throttle limits calls to at most once per interval. Leading, trailing, and maxWait options change the contract, so describe the configuration being used. / debounce 会等到调用静止一段时间后再执行；throttle 将执行限制为每个时间间隔至多一次。leading、trailing 和 maxWait 选项会改变具体行为，因此要说明配置。

~~~javascript
const debouncedSearch = _.debounce(search, 300, {
  trailing: true,
  maxWait: 1000
});

input.addEventListener("input", debouncedSearch);

// When the listener is removed or the component is disposed:
debouncedSearch.cancel();
~~~

Lodash's debounced function also has flush() to invoke a pending call immediately. When both leading and trailing are enabled, a trailing invocation occurs only if there was another call during the wait period. Throttled functions also expose cancel() and flush(). Review the exact leading/trailing settings when a delayed call must not run after unmount or navigation.

## When should you use Lodash? / 何时使用Lodash？

Use the library when its edge-case behavior or object/path API simplifies real code. For a known object shape, optional chaining may be clearer; for unique values, Set may fit; for deep cloning, choose an API only after checking its supported data types and semantics. Bundle impact depends on module format and build configuration. Use per-method imports where appropriate and measure the production output rather than assuming a specific size reduction.

**See also:** [Modern JavaScript Features / 现代JavaScript特性](../javascript/modern-javascript-features.md) for native alternatives such as structuredClone; [Performance Metrics and Analysis / 性能指标与分析](../performance/performance-metrics-and-analysis.md) for choosing debounce or throttle by workload.

**Sources checked 2026-10-15:** [Lodash 4.17.21 API source, including debounce and throttle](https://github.com/lodash/lodash/blob/4.17.21/doc/README.md), [Array.prototype.flat()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/flat), [Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing).
