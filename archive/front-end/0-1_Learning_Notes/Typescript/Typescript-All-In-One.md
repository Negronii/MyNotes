
# TypeScript All-in-One / TypeScript 综合笔记

**Core idea / 核心概念：** TypeScript type annotations are checked at compile time and erased from emitted JavaScript. The array, Map, string, Math, and Promise examples below describe JavaScript runtime or host APIs. / TypeScript 类型标注在编译期检查，并在生成的 JavaScript 中擦除；以下数组、Map、字符串、Math 与 Promise 示例描述的是 JavaScript 运行时或宿主 API。 See the [TypeScript handbook](https://www.typescriptlang.org/docs/handbook/2/basic-types.html), [JavaScript arrays](../../../../frontend/javascript/arrays.md), [Map and Set](../../../../frontend/javascript/map-and-set.md), and [asynchronous JavaScript](../../../../frontend/javascript/asynchronous-javascript.md).

# array.md

# Array Operations in TypeScript / TypeScript 数组操作

## **Declaring an Array**

`new Array<number>(3)` creates three empty slots (holes), not three explicit `undefined` values. Methods such as `map`, `forEach`, `reduce`, `every`, and `some` skip holes; `for...of` yields `undefined` for a hole.
- Empty Array with Fixed Length:
  ```javascript
  const arr_1 = new Array(3);
  console.log(arr_1);     // [, , ]
  ```
- Typed Array with Fixed Length:
  ```typescript
  const arr_2 = new Array<number>(3);
  console.log(arr_2);     // [, , ]
  ```
- Array with Initial Values:
  ```javascript
  const arr_3 = new Array(1, 2, 3);
  console.log(arr_3);     // [1, 2, 3]
  ```
- Type of Arrays:
  ```javascript
  // All return “object"
  console.log(typeof(arr_1), typeof(arr_2), typeof(arr_3));
  ```

## **Multi-Dimensional Array**
- Creating and Accessing:
  ```javascript
  const numList = [[0, 1, 2], [0, 1, 2]];
  console.log(numList);                   // [[0, 1, 2], [0, 1, 2]] 
  console.log(numList.length);            // 2
  console.log(numList[1] && numList[1].length);  // 3
  ```
- Flattening a Multi-Dimensional Array:
  ```javascript
  const arr = [1, 2, [3], [4]];
  const flattenedArray = arr.flat();
  console.log(flattenedArray); // [1, 2, 3, 4]
  ```

## **Get an Element from Array**
- Accessing Elements by Index:
  ```javascript
  const arr_1 = [1, 2, 3, 4];
  const arr_2 = [[1, 2, 3], [4, 5, 6]];
  console.log(arr_1[0], arr_2[1][0]);     // 1, 4
  // If index is wrong, returns undefined
  console.log(arr_1[5], arr_2[1][10]);    // undefined, undefined
  ```
- Finding Index of Elements:
  ```javascript
  // Example with arrObj and indexOf/lastIndexOf methods
  ```

## Frequent used APIs

`push`, `pop`, `shift`, `unshift`, `reverse`, `sort`, and `splice` mutate the array. `concat`, `slice`, `map`, and `filter` return new arrays; copies are shallow, so object elements still refer to the same objects.
1. **length**
   - **Type:** Number
   - **Description:** Returns the length of the array.
   - **Example:** `const arr = [1, 2, 3]; console.log(arr.length); // Output: 3`

2. **toString()**
   - **Type:** String
   - **Description:** Returns a string representation of the array.
   - **Example:** `const arr = [1, 2, 3]; console.log(arr.toString()); // Output: "1,2,3"`

3. **toLocaleString()**
   - **Type:** String
   - **Description:** Returns a localized string representing the array.
   - **Example:** `const arr = [1, 'a', new Date('21 Dec 1997 14:12:00 UTC')]; console.log(arr.toLocaleString());`

4. **push()**
   - **Type:** Number
   - **Description:** Adds new elements to the end of an array, and returns the new length.
   - **Example:** `const arr = [1, 2, 3]; arr.push(4); console.log(arr); // Output: [1, 2, 3, 4]`

5. **pop()**
   - **Type:** T | undefined
   - **Description:** Removes the last element from an array and returns it.
   - **Example:** `const arr = [1, 2, 3]; console.log(arr.pop()); // Output: 3`
   - **Example:** `const emptyarr: number[] = []; console.log(emptyarr.pop()); // undefined for an empty array`

6. **concat()**
   - **Type:** T[]
   - **Description:** Merges two or more arrays and returns a new array.
   - **Example:** `const arr1 = [1, 2]; const arr2 = [3, 4]; console.log(arr1.concat(arr2)); // Output: [1, 2, 3, 4]`

7. **join()**
   - **Type:** String
   - **Description:** Joins all elements of an array into a string and separates them with a specified separator.
   - **Example:** `const arr = ['Fire', 'Air', 'Water']; console.log(arr.join(" - ")); // Output: "Fire - Air - Water"`

8. **reverse()**
   - **Type:** T[]
   - **Description:** Reverses the order of the elements in an array.
   - **Example:** `const arr = [1, 2, 3]; console.log(arr.reverse()); // Output: [3, 2, 1]`

9. **shift()**
   - **Type:** T | undefined
   - **Description:** Removes the first element from an array and returns it.
   - **Example:** `const arr = [1, 2, 3]; console.log(arr.shift()); // Output: 1`

10. **unshift()**
    - **Type:** Number
    - **Description:** Adds one or more elements to the beginning of an array and returns the new length.
    - **Example:** `const arr = [2, 3]; arr.unshift(1); console.log(arr); // Output: [1, 2, 3]`

11. **slice()**
    - **Type:** T[]
    - **Description:** Returns a shallow copy of a portion of an array.
    - **Example:** `const arr = [1, 2, 3, 4, 5]; console.log(arr.slice(1, 3)); // Output: [2, 3]`

12. **sort()**
    - **Type:** this
    - **Description:** Sorts the elements of an array in place and returns it. Without a comparator, elements are sorted by their string forms; numeric arrays usually need a comparator.
    - **Example:** `const arr = [3, 1, 4, 1, 5]; console.log(arr.sort()); // Output: [1, 1, 3, 4, 5]`
    - **Example:** `const numList = [3, 10, 2]; console.log(numList.sort((a, b) => a - b)); // [2, 3, 10]`

13. **splice()**
    - **Type:** T[]
    - **Description:** Changes the contents of an array by removing or replacing existing elements and/or adding new elements.
    - **Example:** `const arr = [1, 2, 3, 4, 5]; arr.splice(2, 1, 'a', 'b'); console.log(arr); // Output: [1, 2, 'a', 'b', 4, 5]`

14. **indexOf()**
    - **Type:** Number
    - **Description:** Returns the first index at which a given element can be found in the array.
    - **Example:** `const arr = [1, 2, 3, 2, 1]; console.log(arr.indexOf(2)); // Output: 1`

15. **lastIndexOf()**
    - **Type:** Number
    - **Description:** Returns the last index at which a given element can be found in the array.
    - **Example:** `const arr = [1, 2, 3, 2, 1]; console.log(arr.lastIndexOf(2)); // Output: 3`

16. **every()**
    - **Type:** Boolean
    - **Description:** Checks if all elements in the array pass the test implemented by the provided function.
    - **Example:** `const arr = [1, 30, 39, 29, 10, 13]; console.log(arr.every(num => num < 40)); // Output: true`

17. **some()**
    - **Type:** Boolean
    - **Description:** Checks if any of the elements in the array pass the test implemented by the provided function.
    - **Example:** `const arr = [1, 2, 3, 4, 5]; console.log(arr.some(num => num >= 3)); // Output: true`

18. **forEach()**
    - **Type:** void
    - **Description:** Executes a provided function once for each array element.
    - **Example:** `const arr = ['a', 'b', 'c']; arr.forEach(element => console.log(element)); // Output: a b c`

19. **map()**
    - **Type:** U[]
    - **Description:** Creates a new array with the results of calling a provided function on every element in the calling array.
    - **Example:** `const arr = [1, 4, 9, 16]; console.log(arr.map(x => x * 2)); // Output: [2, 8, 18, 32]`

20. **filter()**
    - **Type:** T[]
    - **Description:** Creates a new array with all elements that pass the test implemented by the provided function.
    - **Example:** `const arr = [1, 2, 3, 4, 5, 6]; console.log(arr.filter(num => num % 2 === 0)); // Output: [2, 4, 6]`

21. **reduce()**
    - **Type:** accumulator type (inferred, or selected with the overload/generic)
    - **Description:** Applies a function against an accumulator and each element in the array (from left to right) to reduce it to a single value.
    - **Example:** `const arr = [1, 2, 3, 4]; console.log(arr.reduce((acc, val) => acc + val, 0)); // Output: 10`
    - Without an initial value, reducing an empty array (or an array with no present elements) throws a `TypeError`; an initial value makes the empty case well-defined.

22. **reduceRight()**
    - **Type:** accumulator type (inferred, or selected with the overload/generic)
    - **Description:** Applies a function against an accumulator and each element in the array (from right to left) to reduce it to a single value.
    - Without an initial value, reducing an empty array (or an array with no present elements) throws a `TypeError`.
    - **Example:** `const arr = [[0, 1], [2, 3], [4, 5]]; console.log(arr.reduceRight((acc, val) => acc.concat(val))); // Output: [4, 5, 2, 3, 0, 1]`

## **Array Traverse**
- For Loop:
  ```javascript
  let fruits = ['apple', 'banana', 'cherry'];
  for(let i = 0; i < fruits.length; i++) {
      console.log(fruits[i]);
  }
  ```
- For..of Loop:
  ```javascript
  for(let fruit of fruits) {
      console.log(fruit);
  }
  ```
- forEach Method:
  ```javascript
  fruits.forEach(fruit => {
      console.log(fruit);
  });
  ```
- Using forEach with Index and Array:
  ```javascript
  const numList = [1, 2, 3];
  numList.forEach((value, index, array) => {
      if (value % 2 === 0) {
          console.log(`Index: ${index} is even`);
      }
      console.log("Array contents: " + array.join("#")); 
  });
  ```
- map Method:
  ```javascript
  let capitalizedFruits = fruits.map(fruit => fruit.toUpperCase());
  console.log(capitalizedFruits);
  ```

## **Array Destructuring**
- Basic Destructuring:
  ```javascript
  let [firstFruit, secondFruit] = fruits;
  console.log(firstFruit); // Outputs: apple
  console.log(secondFruit); // Outputs: banana
  ```

## Deep Dive: `array.map()`

- **Purpose**: Builds a new result array from callback results without itself mutating the source; the callback can mutate the source, and an identity callback returns the same object references.
- **Syntax**:
  ```typescript
  array.map(callback(currentValue[, index[, array]])[, thisArg])
  ```
The square brackets [...] around index and array mean that these parameters are optional. So when you write a callback function for the map() method, you can choose to include or ignore these parameters.

The nested square brackets like [, index[, array]] signify that if you want to include array in your callback, you also need to include index. In other words, if you decide to use the array parameter in your callback, you can't skip the index parameter.
### Examples of `array.map()`

1. **Basic Usage**:

   ```typescript
   let numbers = [1, 4, 9];
   let roots = numbers.map(function (element, index, arr) {
     console.log(`element: ${element}, index: ${index}, array: ${arr}`);
     return Math.sqrt(element);
   });
   console.log(roots); // [1, 2, 3]
   ```

2. **Using TypeScript Types**:

   ```typescript
   let numbers: number[] = [1, 4, 9];
   let roots: number[] = numbers.map(
     (element: number, index: number, arr: number[]) => {
       console.log(`element: ${element}, index: ${index}, array: ${arr}`);
       return Math.sqrt(element);
     }
   );
   console.log(roots); // [1, 2, 3]
   ```

3. **Simplified with Arrow Functions**:

   ```typescript
   let numbers: number[] = [1, 4, 9];
   let roots: number[] = numbers.map((element) => Math.sqrt(element));
   console.log(roots); // [1, 2, 3]
   ```

4. **Mapping Array of Objects**:
   ```typescript
   interface User {
     id: number;
     name: string;
   }
   let users: User[] = [
     { id: 1, name: "John" },
     { id: 2, name: "Jane" },
     { id: 3, name: "Doe" },
   ];
   let userNames: string[] = users.map((user) => user.name);
   console.log(userNames); // ['John', 'Jane', 'Doe']
   ```


## Stack with array:
```ts
const stack: number[] = [];
stack.push(200) //push an element
const num = stack.pop() //pop an element
stack.length // size of stack
```

# closure.md

# Closure / 闭包

**Core idea / 核心概念：** A closure is a function together with access to the lexical bindings it uses. Those bindings can remain reachable after the outer call returns; they are not “dead” values. / 闭包是函数及其对所用词法绑定的访问；外层函数返回后，只要仍可达，这些绑定就会保留，而不是“已死亡”的值。 See [JavaScript scope and closures](../../../../frontend/javascript/scope-and-closure.md) and [ECMAScript function objects and execution contexts](https://tc39.es/ecma262/2025/multipage/executable-code-and-execution-contexts.html).

- A closure is formed when an inner function, defined within an outer function, references variables from the outer function's scope.
- Even after the outer function completes execution, the inner function maintains access to those variables due to closure.

**When to Use Closures? / 闭包的用途**

- Closures keep needed lexical bindings available to a returned function after the outer call finishes.
- They can be leveraged for:
  - Encapsulation through a function API (not a security boundary).
  - Partial function application.
  - Maintaining state in asynchronous code.
- The technical term for the closure's encompassing context is the "lexical environment".

**Usage Examples of Closures:**

1. **Private Variables and Functions:**

   ```javascript
   const makeCounter = () => {
     let count = 0;
     return () => {
       count++;
       console.log(count);
     };
   };

   let counter = makeCounter();
   counter(); // logs 1
   counter(); // logs 2
   counter(); // logs 3
   ```

   - `makeCounter` returns a function that closes over the `count` binding, so callers can change it only through the returned API.

2. **Partial Function Application:**

   ```javascript
   function add(x) {
     return function (y) {
       return x + y;
     };
   }

   let add5 = add(5);
   console.log(add5(3)); // logs 8
   ```

   - The `add()` function is partially applied with a value `x`, returning a new function that always adds `x` to its argument.

3. **Preserving State in Asynchronous Code:**

   ```javascript
   const animate = (element, from, to, duration) => {
     let start = performance.now();

     const update = () => {
       let time = performance.now() - start;
       let progress = Math.min(time / duration, 1);
       let value = from + (to - from) * progress;

       element.style.left = value + "px";

       if (progress < 1) {
         requestAnimationFrame(update);
       }
     };

     requestAnimationFrame(update);
   };

   let element = document.getElementById("my-element");
   animate(element, 0, 100, 1000);
   ```

   - The `animate()` function retains the state of variables across asynchronous animation frames using closure.

Closures are a fundamental aspect of JavaScript, enabling developers to manage and maintain variable states across different scopes and asynchronous operations.

# map.md

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

# math.md

# Math / 数学函数

**Core idea / 核心概念：** `Math` is a built-in ECMAScript object; TypeScript types it but does not provide a separate runtime math library. / `Math` 是 ECMAScript 内置对象；TypeScript 为它提供类型，但不会提供另一套运行时数学库。 See [ECMAScript numbers and dates](https://tc39.es/ecma262/2025/multipage/numbers-and-dates.html).

`Math.max()` returns the largest of the supplied numbers. With no arguments it returns `-Infinity`; `Math.min()` returns `Infinity` with no arguments.

Frequently used functions:

1. **Math.max(...values)**: Returns the largest of zero or more numbers.
2. **Math.min(...values)**: Returns the smallest of zero or more numbers.
3. **Math.round(value)**: Rounds a number to the nearest integer; a half-way tie goes toward positive infinity (for example, `Math.round(-1.5) === -1`).
4. **Math.ceil(value)**: Rounds a number upward to its nearest integer.
5. **Math.floor(value)**: Rounds a number downward to its nearest integer.
6. **Math.abs(value)**: Returns the absolute value of a number.
7. **Math.sqrt(value)**: Returns the square root of a number.
8. **Math.pow(base, exponent)**: Returns the base to the exponent power, that is, base^exponent.
9. **Math.random()**: Returns a pseudo-random number in the half-open range `[0, 1)`; it can be `0` but is less than `1`.
10. **Math.sin(value)**, **Math.cos(value)**, **Math.tan(value)**: Trigonometric functions (sin, cos, tan).
11. **Math.log(value)**: Returns the natural logarithm (base e) of a number.

These functions are part of ECMAScript and are available in JavaScript hosts such as browsers and Node.js. For example: `Math.max(1, 2, 3)`.
# promise.md

# Promises in TypeScript / TypeScript 中的 Promise

**Core idea / 核心概念：** A Promise is a JavaScript runtime object; TypeScript’s generic type parameter is erased and does not validate values at runtime. The Promise executor runs synchronously, while reactions run later as Promise jobs (microtasks in web hosts). / Promise 是 JavaScript 运行时对象；TypeScript 泛型参数会在编译后擦除，也不会在运行时验证值。Promise 执行器同步运行，后续处理函数作为 Promise 作业（Web 宿主中的微任务）稍后运行。 See [TypeScript’s handbook](https://www.typescriptlang.org/docs/handbook/2/basic-types.html), [asynchronous JavaScript](../../../../frontend/javascript/asynchronous-javascript.md), and the [ECMAScript Promise specification](https://tc39.es/ecma262/2025/multipage/control-abstraction-objects.html#sec-promise-objects).

**1. Introduction to Promises**

- Definition: Represents the eventual outcome of an asynchronous operation.
- States:
  - Pending: Initial state.
  - Fulfilled: Operation completed successfully.
  - Rejected: Operation failed.

**2. Creating a Promise**

- Use the Promise constructor.

```typescript
const promise = new Promise<string>((resolve, reject) => {
  setTimeout(() => {
    resolve("Promise is resolved!");
  }, 2000);
});
```

**3. Consuming a Promise**

- Use `.then()` for success and `.catch()` for errors.

```typescript
promise
  .then((value) => console.log(value))
  .catch((error) => console.error("Something went wrong:", error));
```

**4. Error Handling in Promises**

- Use "reject" for errors.

```typescript
const failingPromise = new Promise<string>((resolve, reject) => {
  setTimeout(() => reject(new Error("Promise failed!")), 2000);
});
failingPromise.catch((error) => console.error(error.message));
```

**5. Chaining Promises**

- Chain multiple `.then()`.

```typescript
function getNumber() {
  return Promise.resolve(21);
}

getNumber()
  .then((num) => num * 2)
  .then((result) => console.log(result));
```

**6. Promise Utility Functions**

- **6.1. `Promise.all()`**: Fulfills with values in input order when all inputs fulfill; rejects when an input first rejects. An empty input fulfills with `[]`. Rejection does not cancel the other operations.

```typescript
Promise.all([Promise.resolve(1), Promise.resolve(2), Promise.resolve(3)])
  .then((values) => console.log(values)); // [1, 2, 3]
```

- **6.2. `Promise.race()`**: Adopts the first input to settle (fulfill or reject); an empty input remains pending.

```typescript
Promise.race([Promise.resolve("first"), Promise.resolve("second")])
  .then((value) => console.log(value)); // "first"
```

**7. Async/Await**

- Syntactic sugar over Promises.

```typescript
async function fetchNumber(): Promise<number> {
  return 42;
}

async function main() {
  try {
    const number = await fetchNumber();
    console.log(number);
  } catch (error) {
    console.error("Error fetching number:", error);
  }
}
main();
```

**Intervals and Timeouts**

- Timer APIs are host-provided (browser and Node handle types differ). Pass a callback; cancellation clears the scheduled callback but does not stop work that has already started.

```typescript
const intervalId = setInterval(() => console.log("tick"), 1000);
clearInterval(intervalId);
```

`setInterval` is a host timer, not part of the ECMAScript Promise API. See the [WHATWG HTML timers section](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers) for browsers and [Node.js timers](https://nodejs.org/docs/latest-v24.x/api/timers.html) for Node.

# string.md

# String / 字符串

**Core idea / 核心概念：** JavaScript strings are sequences of UTF-16 code units; `.length` counts code units, not user-perceived characters. / JavaScript 字符串由 UTF-16 代码单元组成；`.length` 统计代码单元，不等于用户感知的字符数。 See [ECMAScript text processing](https://tc39.es/ecma262/2025/multipage/text-processing.html).

### 1. `length`
- **Description**: Returns the number of UTF-16 code units in the string.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str = "Hello";
  console.log(str.length); // Output: 5
  ```

### 2. `toString()`
- **Description**: Returns the string representation.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let strObj = new String("Hello");
  console.log(strObj.toString()); // Output: "Hello"
  ```

### 3. `charAt(pos: number)`
- **Description**: Returns the one-code-unit string at the specified index, or `""` when the index is out of range.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello";
  console.log(str.charAt(1)); // Output: "e"
  ```

### 4. `charCodeAt(index: number)`
- **Description**: Returns the UTF-16 code-unit value at the specified index, or `NaN` when the index is out of range.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str = "Hello";
  console.log(str.charCodeAt(1)); // Output: 101 (Unicode for 'e')
  ```

### 5. `concat(...strings: string[])`
- **Description**: Concatenates two or more strings and returns a new string.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str1 = "Hello";
  let str2 = " World";
  console.log(str1.concat(str2)); // Output: "Hello World"
  ```

### 6. `indexOf(searchString: string, position?: number)`
- **Description**: Returns the position of the first occurrence of a specified string.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str = "Hello World";
  console.log(str.indexOf("World")); // Output: 6
  ```

### 7. `lastIndexOf(searchString: string, position?: number)`
- **Description**: Returns the last occurrence of a specified string, searching backwards.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str = "Hello World, World";
  console.log(str.lastIndexOf("World")); // Output: 13
  ```

### 8. `localeCompare(that: string)`
- **Description**: Compares two strings in the current locale.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str1 = "a";
  let str2 = "b";
  const comparison = str1.localeCompare(str2);
  console.log(comparison < 0); // true when str1 sorts before str2 in the active locale
  ```

### 9. `match(regexp: string | RegExp)`
- **Description**: Finds matches of a regular expression in a string.
- **Return Type**: `RegExpMatchArray | null`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.match(/\bW\w+/)); // Output: ["World"]
  ```

### 10. `replace(searchValue: string | RegExp, replaceValue: string)`
- **Description**: Replaces text in a string, using a regular expression or search string.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.replace("World", "Everyone")); // Output: "Hello Everyone!"
  ```

### 11. `search(regexp: string | RegExp)`
- **Description**: Executes a search for a match in a string.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.search(/\bW\w+/)); // Output: 6
  ```

### 12. `slice(start?: number, end?: number)`
- **Description**: Extracts a section of a string and returns a new string.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.slice(6, 11)); // Output: "World"
  ```

### 13. `split(separator: string | RegExp, limit?: number)`
- **Description**: Splits a string into an array of substrings.
- **Return Type**: `string[]`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.split(" ")); // Output: ["Hello", "World!"]
  ```

### 14. `substr(start: number, length?: number)`
- **Description**: Legacy Annex B method; prefer `slice()` for new code. Returns up to `length` code units beginning at `start`.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.substr(1, 4)); // Output: "ello"
  ```

### 15. `substring(start: number, end?: number)`
- **Description**: Extracts characters from a string between two specified indices.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.substring(1, 5)); // Output: "ello"
  ```

### 16. `toLowerCase()`
- **Description**: Converts a string to lowercase letters.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "HELLO WORLD";
  console.log(str.toLowerCase()); // Output: "hello world"
  ```

### 17. `toLocaleLowerCase(locales?: string | string[])`
- **Description**: Converts a string to lowercase using the supplied locale, or the host default when omitted.
- **Return Type**: `string`
- **Example**:
  ```javascript
  console.log("I".toLocaleLowerCase('tr')); // Output: "ı"
  ```

### 18. `toUpperCase()`
- **Description**: Converts a string to uppercase letters.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "hello world";
  console.log(str.toUpperCase()); // Output: "HELLO WORLD"
  ```

### 19. `toLocaleUpperCase(locales?: string | string[])`
- **Description**: Converts a string to uppercase using the supplied locale, or the host default when omitted.
- **Return Type**: `string`
- **Example**:
  ```javascript
  console.log("i".toLocaleUpperCase('tr')); // Output: "İ"
  ```

### 20. `trim()`
- **Description**: Removes whitespace from both ends of a string.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "  Hello World!  ";
  console.log(str.trim()); // Output: "Hello World!"
  ```

### 21. `valueOf()`
- **Description**: Returns the primitive value of a String object.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let strObj = new String("Hello World");
  console.log(strObj.valueOf()); // Output: "Hello World"
  ```

### String Constructor
- **Description**: Allows creating a String object or converting a value to a string.
- **Usage**:
  ```javascript
  let strObj = new String("Hello");
  let str = String(123);
  ```

### `String.fromCharCode(...codes: number[])`
- **Description**: Converts UTF-16 code-unit values into a string. Use `String.fromCodePoint()` for Unicode code points above `0xFFFF`.
- **Example**:
  ```javascript
  console.log(String.fromCharCode(72, 101, 108, 108, 111)); // Output: "Hello"
  ```

## Traverse String

Indexing and `charAt()` use code units and can split surrogate pairs. `for...of` yields code points, but grapheme clusters (“user-perceived characters”) can span multiple code points ([Unicode Standard Annex #29](https://www.unicode.org/reports/tr29/)).

```javascript
const face = "😀";
console.log(face.length); // 2 UTF-16 code units
console.log([...face]);  // ["😀"]: one code point
console.log(String.fromCodePoint(0x1F600)); // "😀"
```
```ts
const str = "Hello"

let result: string[] = [];
for (let i = 0; i < str.length; i++) {
    let char = str.charAt(i);
    result.push(char);
}
// ["H", "e", "l", "l", "o"] 
console.log(result);	
```

```ts
const s = "Hello"
let result: string[] = [];
for (let char of s) {
    result.push(char);
}
// ["H", "e", "l", "l", "o"] 
console.log(result);	
```
