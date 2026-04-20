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
