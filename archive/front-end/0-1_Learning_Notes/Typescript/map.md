# Map 怎样维护键身份、存在性和插入顺序？

**案例背景：** 用用户编号保存角色，并依次更新、删除和重新添加。需要区分“键不在表里”和“键存在但值为 undefined”，也需要知道更新是否改变顺序。Map 的键值契约适合这个问题；更完整的容器选择见[Map 与 Set 怎样维护身份与集合关系？](../../../../frontend/javascript/map-and-set.md)。

```typescript
const roles = new Map<number, string>();
roles.set(1, "admin");
roles.set(2, "user");
roles.set(1, "reader");
console.log([...roles]); // [[1,"reader"],[2,"user"]]
roles.delete(1);
roles.set(1, "admin");
console.log([...roles.keys()]); // [2,1]
console.log(roles.get(2), roles.has(2), roles.size); // "user", true, 2
```

更新已有键只换值，不移动位置；删除后重加才位于末尾。`get` 查不到返回 `undefined`，但键存在且值为 `undefined` 时也一样，所以存在性用 `has`。下面两行分别新建一个独立的 Map，查询键 `1`：

| Map 状态 | `get(1)` | `has(1)` |
|---|---|---|
| `new Map()` | `undefined` | `false` |
| `new Map([[1, undefined]])` | `undefined` | `true` |

在 strict TypeScript 中，`Map<K, V>.get` 的静态返回类型是 `V | undefined`；因此本例 `roles.get(2)` 的类型也是 `string | undefined`，即使运行时该键存在并取到 `"user"`。若 `V` 本身含 `undefined`，返回值类型同样无法说明是键缺失还是取到 `undefined`，要用 `has` 判断存在性。`delete` 返回是否确实删去键，`clear` 清空所有条目。

## 对象内容一样，为何查不到？

Map 采用 SameValueZero 键比较：NaN 与 NaN 匹配，正负零是同一键；对象按 object identity（对象身份）比较，实际是同一对象引用才匹配。`map.set({id:1}, value)` 后用另一个 `{id:1}` 查询，不是同一个键。需要按编号查就用编号；需要复合键则先定义稳定且无歧义的编码，`JSON.stringify` 并不是适用于循环对象等任意值的结构身份方案。

普通对象的键是字符串或 Symbol（符号）；Map 可以直接用对象、函数或原始值。普通对象自有键的顺序也有规则：array-index（数组索引）键按数值升序，其余字符串按创建顺序，最后的 Symbol 键也按创建顺序。选择应依据键语义和接口，不能用“对象无序”或“Map 永远更快”作判断。

## 两种遍历为何参数顺序不同？

```typescript
roles.forEach((value, key) => console.log(key, value));
for (const [key, value] of roles) console.log(key, value);
```

`forEach` 把 value 放在 key 前面；默认 iterator（迭代器）却产出 `[key,value]`。二者都跟随插入顺序。`keys()`、`values()`、`entries()` 分别返回对应的迭代器。它们不是冻结快照：遍历尚未完成时新增的键会追加到末尾并被访问，访问前删除的键会跳过。`forEach` 中已访问过的键若在遍历结束前删除后重加，会作为末尾的新条目再次访问。遍历时改容器会改变本轮访问范围；需要固定一轮输入时先复制条目。

> [!info]- 来源
> - 键相等、插入顺序、Map 方法契约与迭代期间新增/删除行为：[ECMAScript 2026，§24.1、§24.1.3.2–§24.1.3.12、§24.1.5.1](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-map-objects)。该快照日期为 2026-03-31；Map 要求平均访问时间次线性，但不保证所有操作均为常数时间。
> - 普通对象自有键顺序：[ECMAScript 2026，§10.1.11.1 OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys)。
