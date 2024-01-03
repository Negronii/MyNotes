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

# Array Operations in TypeScript

## Declaration

- **Square Brackets Syntax**:
  ```typescript
  let fruits: string[] = ["apple", "banana", "cherry"];
  ```
- **Array Generic Syntax**:
  ```typescript
  let numbers: Array<number> = [1, 2, 3, 4, 5];
  ```

## Traversal Techniques

- **Using `for` loop**:

  ```typescript
  for (let i = 0; i < fruits.length; i++) {
    console.log(fruits[i]);
  }
  ```

- **Using `for..of` loop**:

  ```typescript
  for (let fruit of fruits) {
    console.log(fruit);
  }
  ```

- **Using `forEach` method**:

  ```typescript
  fruits.forEach((fruit) => console.log(fruit));
  ```

- **Using `map` for Transformation**:
  ```typescript
  let capitalizedFruits = fruits.map((fruit) => fruit.toUpperCase());
  console.log(capitalizedFruits);
  ```

## Destructuring

- **Example**:
  ```typescript
  let [firstFruit, secondFruit] = fruits;
  console.log(firstFruit); // apple
  console.log(secondFruit); // banana
  ```

## Common Methods

- **Filtering with `filter`**:

  ```typescript
  let longFruits = fruits.filter((fruit) => fruit.length > 5);
  console.log(longFruits); // ['banana', 'cherry']
  ```

- **Accumulation with `reduce`**:

  ```typescript
  let total = numbers.reduce((sum, number) => sum + number, 0);
  console.log(total); // 15
  ```

- **Finding Element with `find`**:
  ```typescript
  let foundFruit = fruits.find((fruit) => fruit.startsWith("b"));
  console.log(foundFruit); // banana
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
