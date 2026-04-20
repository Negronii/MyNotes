# Map Operations

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
  - Object: No guaranteed order, especially for numeric keys.
- **API Methods**:
  - Map: Offers `set`, `get`, `has`, `delete`, etc.
  - Object: Uses dot or bracket notation for property access.
- **Performance**:
  - Map: Better for frequent addition/removal of key-value pairs.
  - Object: Optimized for static key set operations.

**Note on Key Choices**
Arrays and objects are compared by reference. Even if two arrays/objects have identical values, they're different unless they point to the same reference. Using `JSON.stringify(array/object)` can help create unique keys.

**Defining Types**

```javascript
let userRoles: Map<number, string> = new Map();
userRoles.set(1, "admin");
userRoles.set(2, "user");
```
