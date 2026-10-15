# Map Operations / Map 操作

**Core idea / 核心概念：** A `Map` accepts keys of any type, compares them with `SameValueZero` (objects by identity), and iterates entries in insertion order. Setting an existing key updates its value without moving it; deleting and re-adding it places it at the end. / `Map` 的键可以是任意类型；比较采用 `SameValueZero`（对象按引用身份比较），迭代顺序为插入顺序。更新已有键不会改变其顺序；删除后重新添加会移到末尾。 See [JavaScript Map and Set](../../../../frontend/javascript/map-and-set.md) and [ECMAScript keyed collections](https://tc39.es/ecma262/2025/multipage/keyed-collections.html).

**1. Creating a Map**

```javascript
let myMap = new Map();
```

**2. Adding Entries**

```javascript
myMap.set("key1", "value1");
myMap.set("key2", "value2");
```

**3. Retrieving Entries**

```javascript
let value = myMap.get("key1"); // returns 'value1'
```

**4. Checking for a Key**

```javascript
let hasKey = myMap.has("key1"); // returns true
```

**5. Removing an Entry**

```javascript
myMap.delete("key1");
```

**6. Iterating Over a Map**

- Using forEach:
  ```javascript
  myMap.forEach((value, key) => {
    console.log(key, value);
  });
  ```
- Using for...of loop:
  ```javascript
  for (let [key, value] of myMap) {
    console.log(key, value);
  }
  ```

**7. Getting Size of the Map**

```javascript
let size = myMap.size; // returns 1 (after deleting 'key1')
```

**Differences Between Object and Map**

- **Key Types**:
  - Object: Only strings and symbols as keys.
  - Map: Allows any type, including functions, objects, and primitives.
- **Order of Keys**:
  - Map: Keys stay in insertion order.
  - Ordinary objects: Own property-key order is specified: array-index keys first in numeric order, then other strings in creation order, then symbols in creation order.
- **API Methods**:
  - Map: Offers `set`, `get`, `has`, `delete`, etc.
  - Object: Uses dot or bracket notation for property access.
- **Performance**:
  - Choose by key and API semantics; performance depends on workload and engine, so measure before making a performance claim.

**Note on Key Choices**
Objects and arrays used as `Map` keys compare by identity, not by contents: two separately created `{ id: 1 }` objects are distinct keys. `JSON.stringify` is not a general structural-key solution (for example, it can be ambiguous or fail for cyclic data); define a canonical key explicitly when value-based lookup is required.

**Defining Types**

```typescript
let userRoles: Map<number, string> = new Map();
userRoles.set(1, "admin");
userRoles.set(2, "user");
```
