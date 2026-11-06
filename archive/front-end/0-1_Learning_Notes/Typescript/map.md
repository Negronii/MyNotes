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

更新已有键只换值，不移动位置；删除后重加才位于末尾。`get` 查不到返回 `undefined`，但 `new Map([[1, undefined]]).get(1)` 也一样，所以存在性用 `has`。`delete` 返回是否确实删去键，`clear` 清空所有条目。

## 对象内容一样，为何查不到？

Map 采用 SameValueZero 比较键：NaN 与 NaN 匹配，正负零是同一键，对象按 identity（身份）比较。`map.set({id:1}, value)` 后用另一个 `{id:1}` 查询，不是同一个键。需要按编号查就用编号；需要复合键则先定义稳定且无歧义的编码，`JSON.stringify` 并不是适用于循环对象等任意值的结构身份方案。

普通对象的键是字符串或 Symbol；Map 可以直接用对象、函数或原始值。普通对象自有键的顺序也有规则：array-index 键按数值升序，其余字符串按创建顺序，随后是 Symbol。选择应依据键语义和接口，不能用“对象无序”或“Map 永远更快”作判断。

## 两种遍历为何参数顺序不同？

```typescript
roles.forEach((value, key) => console.log(key, value));
for (const [key, value] of roles) console.log(key, value);
```

`forEach` 把 value 放在 key 前面；默认 iterator（迭代器）却产出 `[key,value]`。二者都跟随插入顺序。`keys()`、`values()`、`entries()` 分别给出需要的视图；这些不是冻结快照，遍历时修改容器须理解访问行为，需要固定一轮输入时先复制对应条目。

> [!info]- 来源
> - 键比较、插入顺序和方法契约：[ECMAScript 2026 Map Objects](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-map-objects)。规范要求平均次线性的访问，不承诺所有操作总是常数时间；核对 2026-11-06。
> - 普通对象键顺序：[ECMAScript OrdinaryOwnPropertyKeys](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryownpropertykeys)。
