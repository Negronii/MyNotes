
# array.md

# Array Operations in TypeScript

## **Declaring an Array**
- Empty Array with Fixed Length:
  ```javascript
  const arr_1 = new Array(3);
  console.log(arr_1);     // [, , ]
  ```
- Typed Array with Fixed Length:
  ```javascript
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
   - **Example:** `console.log(emptyarr.pop());    // undefined, return undefined when array is empty`

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
   - **Type:** T
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
    - **Description:** Sorts the elements of an array in place and returns the sorted array.
    - **Example:** `const arr = [3, 1, 4, 1, 5]; console.log(arr.sort()); // Output: [1, 1, 3, 4, 5]`
    - **Example:** `numList.sort((a, b) => b - a); console.log(numList);       // [5, 4, 3, 1, 1] `

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
    - **Example:** `const arr = [1, 2, 3, 4, 5, 6]; console.log(arr.filter(num => num % 2 == 0)); // Output: [2, 4, 6]`

21. **reduce()**
    - **Type:** T
    - **Description:** Applies a function against an accumulator and each element in the array (from left to right) to reduce it to a single value.
    - **Example:** `const arr = [1, 2, 3, 4]; console.log(arr.reduce((acc, val) => acc + val, 0)); // Output: 10`

22. **reduceRight()**
    - **Type:** T
    - **Description:** Applies a function against an accumulator and each element in the array (from right to left) to reduce it to a single value.
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

- **Purpose**: Transforms each array element and returns a new array without altering the original array.
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
const stack = []
stack.push(200) //push an element
const num = stack.pop() //pop an element
stack.length // size of stack
```

# closure.md

# Closure

- A closure is formed when an inner function, defined within an outer function, references variables from the outer function's scope.
- Even after the outer function completes execution, the inner function maintains access to those variables due to closure.

**When to Use Closures?**

- Closures enable retrieval of "dead" values which have gone out of scope.
- They can be leveraged for:
  - Data privacy (private variables or functions).
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

   - `makeCounter` returns a function that closes over the `count` variable, effectively making it private.

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
       let progress = time / duration;
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

# math.md

In TypeScript, which is a superset of JavaScript, there isn't a dedicated `Math.max()` function in a separate Math library as in Java. However, JavaScript (and thus TypeScript) has a global `Math` object that provides various mathematical functions and constants, similar to Java's `Math` class.

The `Math.max()` function in TypeScript/JavaScript works quite similarly to Java's `Math.max()` method. It returns the largest of the zero or more numbers given as input parameters.

Here are some frequently used math functions available in TypeScript/JavaScript, similar to those in Java's `Math` class:

1. **Math.max(...values)**: Returns the largest of zero or more numbers.
2. **Math.min(...values)**: Returns the smallest of zero or more numbers.
3. **Math.round(value)**: Rounds a number to the nearest integer.
4. **Math.ceil(value)**: Rounds a number upward to its nearest integer.
5. **Math.floor(value)**: Rounds a number downward to its nearest integer.
6. **Math.abs(value)**: Returns the absolute value of a number.
7. **Math.sqrt(value)**: Returns the square root of a number.
8. **Math.pow(base, exponent)**: Returns the base to the exponent power, that is, base^exponent.
9. **Math.random()**: Returns a pseudo-random number between 0 and 1.
10. **Math.sin(value)**, **Math.cos(value)**, **Math.tan(value)**: Trigonometric functions (sin, cos, tan).
11. **Math.log(value)**: Returns the natural logarithm (base e) of a number.

These functions are part of the ECMAScript standard and are available in any environment that supports JavaScript, including browsers and Node.js environments. They are accessed through the `Math` object, e.g., `Math.max(1, 2, 3)`.
# promise.md

## Promises in TypeScript

**1. Introduction to Promises**

- Definition: Represents a future value.
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
```

**5. Chaining Promises**

- Chain multiple `.then()`.

```typescript
getNumber()
  .then((num) => num * 2)
  .then((result) => console.log(result));
```

**6. Promise Utility Functions**

- **6.1. Promise.all()**: Waits for all promises.

```typescript
Promise.all([promise1, promise2, promise3]).then((values) =>
  console.log(values)
);
```

- **6.2. Promise.race()**: First promise to resolve/reject.

```typescript
Promise.race([promiseA, promiseB]).then((value) => console.log(value));
```

**7. Async/Await**

- Syntactic sugar over Promises.

```typescript
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

- Both can be cancelled.

```typescript
let intervalId = setInterval(1000);
clearInterval(intervalId);
```

# string.md

# String

### 1. `length`
- **Description**: Get the length of the String object.
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
- **Description**: Returns the character at the specified position.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello";
  console.log(str.charAt(1)); // Output: "e"
  ```

### 4. `charCodeAt(index: number)`
- **Description**: Returns the Unicode of the character at the specified index. NaN if no character at the index.
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
  console.log(str1.localeCompare(str2)); // Output: -1
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
- **Description**: Returns the characters in a string

beginning at the specified location through the specified number of characters.
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
- **Description**: Converts a string to lowercase, considering the host's current locale.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "HELLO WORLD";
  console.log(str.toLocaleLowerCase('tr')); // Output: "hello world" (with Turkish locale)
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
- **Description**: Converts a string to uppercase, considering the host's current locale.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "hello world";
  console.log(str.toLocaleUpperCase('tr')); // Output: "HELLO WORLD" (with Turkish locale)
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
- **Description**: Converts Unicode values into characters.
- **Example**:
  ```javascript
  console.log(String.fromCharCode(72, 101, 108, 108, 111)); // Output: "Hello"
  ```

## Traverse String
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