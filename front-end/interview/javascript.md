## Why 0.1 + 0.2 !== 0.3

This is a result of how computers handle binary floating-point arithmetic.

When you add these approximations, the tiny errors in their representation lead to results that are not exact, hence 0.1 + 0.2 results in something slightly different from 0.3. This is an issue inherent in IEEE 754 standard for floating-point arithmetic, which is used by most modern programming languages.

In practical terms, to compare floating-point numbers in such cases, a common approach is to check if they are close enough to each other, within a small tolerance, rather than expecting exact equality.

## What is the JavaScript Prototype Chain? How is it Formed?

### The Concept of the Prototype Chain

In JavaScript, every object has a property called `prototype`, which refers to another object. This `prototype` object has its own `prototype`, and so on, until an object with a `null` prototype is reached, which is the end of the prototype chain. The chain is formed through these `prototype` links between objects.

When you try to access a property or method of an object, JavaScript engine will first search on the object itself. If it doesn't find it, it will look into the object's prototype, then the prototype's prototype, and so on, up the chain until it either finds the property/method or reaches the end of the chain (`null` prototype).

### How the Chain is Formed

The prototype chain is established through the constructor function of an object. When an object is created using a constructor function (using the `new` keyword), the newly created object's internal `[[Prototype]]` (often accessible as `__proto__`) property is set to the prototype object of the constructor function. This links the object to its prototype, forming a part of the chain.

### Example to Illustrate

```javascript
function Person(name) {
  this.name = name;
}

Person.prototype.sayHello = function() {
  console.log(`Hello, my name is ${this.name}`);
};

const alice = new Person('Alice');

alice.sayHello(); // Outputs: Hello, my name is Alice
console.log(alice.__proto__ === Person.prototype); // true
console.log(Person.prototype.__proto__ === Object.prototype); // true
console.log(Object.prototype.__proto__); // null
```

In this example:
- `alice` is an instance of `Person`.
- `alice` inherits the `sayHello` method from `Person.prototype` via the prototype chain.
- The chain for `alice` looks like this: `alice` object --> `Person.prototype` --> `Object.prototype` --> `null`.
- This illustrates how `alice.sayHello()` is able to work: JavaScript searches `alice` for `sayHello`, doesn't find it, then moves up to `Person.prototype`, where it finds and executes the method.

## Array Flattening Function in JavaScript
Array flattening is the process of converting a nested array into a single-dimensional array. This is a common task in JavaScript to simplify array handling.
```ts
function arrayFlatten(arr: any[]): any[] {
    let flattenedArray = [];
    for (let i = 0; i < arr.length; i++) {
        if (Array.isArray(arr[i])) {
            flattenedArray = flattenedArray.concat(arrayFlatten(arr[i])); 
        } else {
            flattenedArray.push(arr[i]);
        }
    }
    return flattenedArray;
}
```

Second Implementation (Using `reduce`):   
This implementation is concise and correctly flattens the array using the `reduce` method combined with recursion.
```ts
function arrayFlatten(arr: any[]): any[]{
    return arr.reduce((prev, cur) => {
        return prev.concat(Array.isArray(cur) ? arrayFlatten(cur) : cur);
    }, []);
}
```

## Writing a `getType` Function in JavaScript
Determining the type of a variable accurately in JavaScript can be tricky due to the language's dynamic nature. The `typeof` operator, `instanceof` keyword, and `Object.prototype.toString.call()` method are commonly used techniques to identify variable types. e.g. `typeof 1` returns `'number'`, `typeof 'test'` returns `'string'`, and `typeof [1, 2, 3]` returns `'object'`. However, `typeof` has limitations, especially for reference types, where it returns `'object'` for arrays, null, and objects. To address this, the `Object.prototype.toString.call()` method provides a more detailed type check for reference types.
```ts
function getType(val: any): string {
    const type = typeof val;
    if (type !== 'object') {
        return type; // Returns 'number', 'string', 'boolean', etc.
    }
    // For objects, including arrays and null, use Object.prototype.toString
    return Object.prototype.toString.call(val).slice(8, -1).toLowerCase();
}
```

## What happens when you `new` an object, and how to simulate the `new` process with a method?

When the `new` keyword is used in JavaScript, it performs several actions behind the scenes to create a new instance of an object based on a constructor function. Here's what happens step by step, and how to simulate this process:

1. **Create an empty object** that inherits from the constructor function's prototype.
2. **Execute the constructor function** with the newly created object assigned to `this`.
3. **Return the new object** unless the constructor explicitly returns a different object.

The method to simulate the `new` process can be represented as follows:

```typescript
function _new(fn: Function, ...args: any[]): any {
    const obj = Object.create(fn.prototype); // Step 1
    const res = fn.apply(obj, args); // Step 2
    return res instanceof Object ? res : obj; // Step 3
}

// Test example
function Person(name: string) {
    this.name = name;
}
const person = _new(Person, 'Tom');
console.log(person.name); // Tom
```

### Understanding `class` as Syntactic Sugar

It's important to note that a `class` in JavaScript is essentially syntactic sugar over the existing prototype-based inheritance and does not introduce a new object-oriented inheritance model. At its core, a class is just a special type of function, and thus `typeof ClassName === 'function'`.

## Differences between `Object.create` and `{}`

Creating objects in JavaScript can be achieved in multiple ways, each with its own set of characteristics regarding prototype inheritance.

1. **Using `{}` (Object Literals)**: This is the most common way to create an object. The created object inherits from `Object.prototype`, making it an instance of Object.

    ```typescript
    const obj1 = {};
    console.log(obj1.__proto__ === Object.prototype); // true
    ```

2. **Using `Object.create(proto)`**: This method creates a new object with the specified object as its prototype. This allows for more flexibility in setting up the prototype chain.

    - **`Object.create(Object.prototype)`**: Creates a new object with `Object.prototype` as its prototype, similar to `{}`.
    - **`Object.create({name: 'Tom'})`**: Creates a new object with a custom object (`{name: 'Tom'}`) as its prototype, diverging from `Object.prototype`.

    ```typescript
    const obj2 = Object.create(Object.prototype);
    const obj3 = Object.create({name: 'Tom'});
    console.log(obj2.__proto__ === Object.prototype); // true
    console.log(obj3.__proto__ === Object.prototype); // false
    ```

## Depth-First Search (DFS) of a DOM Tree
Depth-First Search (DFS) is a method used to traverse or search a tree or graph data structure. The algorithm starts at the root node and explores as far as possible along each branch before backtracking. When applied to a DOM tree, DFS will visit each node in a manner that deeply explores a node's children before moving to its siblings.

### Code Example for DFS
The given TypeScript function `dfs` illustrates how DFS can be applied to a DOM tree. The `visitNode` function is used to log different types of nodes (Comment, Text, HTMLElement). In the `dfs` function, recursion is utilized to visit each node starting from the root, exploring all its child nodes deeply before moving to the next sibling.

```typescript
function visitNode(node: Node) {
    if (node instanceof Comment) {
        console.log('comment', node.textContent);
    }
    if (node instanceof Text) {
        const t = node.textContent.trim();
        if (t) {
            console.log('text', t);
        }
    }
    if (node instanceof HTMLElement) {
        console.log('element', node.tagName);
    }
}

function dfs(node: Node) {
    visitNode(node);
    node.childNodes.forEach((child) => {
        dfs(child);
    });
}
```

### Without Recursion
DFS can be implemented without recursion by using a stack to simulate the call stack of recursion. This approach avoids potential stack overflow errors that may occur with deep recursion. While recursion is more straightforward and readable, using a stack can be more efficient and safer for deep trees.

```typescript
function dfsWithoutRecursion(node: Node) {
    const stack = [node];
    while (stack.length) {
        const n = stack.pop();
        visitNode(n);
        Array.from(n.childNodes).reverse().forEach((child) => {
            stack.push(child);
        });
    }
}
```

## Breadth-First Search (BFS) of a DOM Tree
Breadth-First Search (BFS) is another method to traverse or search a tree or graph data structure. Unlike DFS, BFS explores all the neighbor nodes at the present depth prior to moving on to the nodes at the next depth level. Applied to a DOM tree, BFS will visit each node level by level.

### Code Example for BFS
The `bfs` function demonstrates how BFS can be applied to a DOM tree. It uses a queue to visit each node at the current level before moving to the nodes at the next level. This approach ensures that nodes are visited in a breadth-wise manner.

```typescript
function bfs(node: Node) {
    const queue = [node];
    while (queue.length) {
        const n = queue.shift();
        visitNode(n);
        n.childNodes.forEach((child) => {
            queue.push(child);
        });
    }
}
```

### Key Differences Between DFS and BFS
- **DFS** dives as deep as possible into the tree's branches before backtracking, which can be implemented either recursively or using a stack.
- **BFS** visits all nodes at the current level before moving to the next level, using a queue to keep track of the order.

## Drawbacks of Arrow Functions and Situations Where They Can't Be Used

Arrow functions, introduced in ES6, provide a concise syntax and lexically bind the `this` value, but they have limitations in certain scenarios:

### Arrow Functions and `this` Context
Arrow functions do not have their own `this` context; they inherit it from the enclosing lexical scope. This feature is beneficial in some cases, such as callbacks where maintaining `this` from the outer context is desired. However, it limits their usage in other scenarios:

1. **Dynamic Context Callback Functions**: In event handlers, the `this` context is expected to be the element triggering the event. Arrow functions do not suit this because they do not bind their own `this`.

   ```typescript
   const btn = document.getElementById('btn');
   btn.addEventListener('click', () => {
       console.log(this === window); // `this` refers to the window, not the button
       // `this.innerHTML` will not work as expected
   });
   ```

2. **Function Scope and `this`**: In regular functions, `this` refers to the function's execution context, but in arrow functions, it refers to the enclosing context.

   ```typescript
   function f1() {
       console.log(this); // refers to the function's execution context
   }

   const f2 = () => {
       console.log(this); // refers to the lexical scope's context
   };
   ```

### `arguments` Object and Rest Parameters
Arrow functions do not have an `arguments` object, unlike regular functions. This limitation can be circumvented using rest parameters.

```typescript
function f1() {
   // Access to `arguments` object
}

const f2 = (...args) => {
   // Use `args` as an alternative to `arguments`
};
```

### Object and Prototype Methods
Arrow functions are not suitable for defining object or prototype methods where `this` is expected to refer to the object itself.

1. **Object Methods**:
   ```typescript
   const obj = {
       name: 'aaa',
       getName: () => this.name // `this` does not refer to `obj`
   };

   obj.getName(); // Will not work as expected
   ```

2. **Prototype Methods**:
   ```typescript
   function MyObject() {
       this.name = 'aaa';
   }

   MyObject.prototype.getName = () => this.name; // `this` does not refer to the instance of `MyObject`

   const myObj = new MyObject();
   myObj.getName(); // Will not work as expected
   ```

### Constructors
Arrow functions cannot be used as constructors. They cannot be used with the `new` keyword as they do not have their own `this` context, nor do they have a prototype.

```typescript
const Foo = (name, age) => {
    this.name = name;
    this.age = age;
};

const f = new Foo('aa', 20); // TypeError: Foo is not a constructor
```

### Summary
While arrow functions offer concise syntax and are useful in many cases, especially for inline functions and callbacks, their inability to bind their own `this`, lack of an `arguments` object, and unsuitability for object methods, prototype methods, and constructors limit their applicability in certain JavaScript programming scenarios.

## Difference between `for..in` and `for..of` loops in JavaScript. 

### For...in Loop:
- The `for..in` loop iterates over all enumerable properties of an object.
- It is generally used for objects, where the loop iterates over the property keys of the object.
- For arrays, it iterates over the index values (keys) of the array.

```ts
const arr: number[] = [10, 20, 30]; // Array should be defined as number[]
for (let i in arr) {
    console.log(i); // Output: 0, 1, 2 (indexes)
}

const str: string = 'abc';
for (let i in str) {
    console.log(i); // Output: 0, 1, 2 (indexes)
}

const obj = {name: 'aaa', age: 30};
for (let i in obj) {
    console.log(i); // Output: name, age (keys)
}
```

### For...of Loop:
- The `for..of` loop iterates over iterable objects such as Arrays, Strings, Maps, NodeLists, and more.
- It is used to iterate over the values in these collections.
- It cannot be used directly on objects since they are not iterable.

```ts
const arr: number[] = [10, 20, 30];
for (let i of arr) {
    console.log(i); // Output: 10, 20, 30 (values)
}

const str: string = 'abc';
for (let i of str) {
    console.log(i); // Output: a, b, c (characters)
}

function fn(){
    for (let arg of arguments) {
        console.log(arg);
    }
}

fn(100, 200, 'aaa'); // Output: 100, 200, 'aaa'

const s1 = new Set([10, 20, 30]);
for (let i of s1) {
    console.log(i); // Output: 10, 20, 30 (Set values)
}

const m1 = new Map([
    ['x', 100],
    ['y', 200],
    ['z', 300]
]);
for (let [key, value] of m1) {
    console.log([key, value]); // Output: ['x', 100], ['y', 200], ['z', 300]
}
```

### Key Differences:
1. **Usage**: `for..in` is used to iterate over the keys of an object, whereas `for..of` is used to iterate over values of iterable objects.
2. **Applicability**: `for..in` works well with objects but is not ideal for arrays since the order of iteration is not guaranteed. `for..of` is ideal for arrays and other iterable objects.
3. **Type of Iterated Elements**: `for..in` iterates over keys (property names), while `for..of` iterates over values.

### Sample Answer:
The `for..in` loop in JavaScript is used to iterate over enumerable properties of an object, such as the keys of an object or the indices of an array. In contrast, the `for..of` loop is designed to iterate over the values of iterable objects like arrays, strings, Sets, Maps, and generator objects. The key difference lies in what they iterate over: `for..in` goes over keys/indexes, and `for..of` goes over values. `for..in` is typically used for objects, while `for..of` is more suitable for arrays and other iterable collections.

## What is and when to use `for await...of`
he for await...of statement is a feature in JavaScript that allows you to loop over asynchronous iterables—objects that you can iterate over asynchronously, such as Promises.

### Code example:
```ts
async function processPromises() {
    function createPromise(val) {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve(val);
            }, 1000);
        });
    }

    const p1 = createPromise(100);
    const p2 = createPromise(200);
    const p3 = createPromise(300);
    const list = [p1, p2, p3];

    // Iterating over an array of Promises and logging each resolved value
    // effect is same as:
    // Promise.all(list).then(res => console.log(res))
    for await (let res of list) {
        console.log(res);
    }

    // Performing asynchronous operations in sequence
    const arr = [100, 200, 300];
    for (let num of arr) {
        const res = await createPromise(num); // Ensure this code is inside an async function
        console.log(res);
    }
}

processPromises();
```

The `for await...of` loop is a powerful feature for handling asynchronous operations in JavaScript, providing a more intuitive and cleaner way to process sequences of Promises compared to chaining or using `Promise.all()`. It's particularly useful in scenarios where you need to maintain the order of operations or when working with streams of asynchronous data.

## What are the Features of JavaScript's Strict Mode?

Strict mode in JavaScript is an option that enables a restricted variant of JavaScript, enhancing error detection and overall code quality. It's activated by adding `'use strict';` at the beginning of a script or function.

### Features of Strict Mode

1. **Variables Must Be Declared**: Strict mode requires all variables to be declared before use. Usage of undeclared variables will result in a reference error, preventing accidental global variable creation.

2. **No `with` Statement**: The `with` statement is prohibited as it complicates the scope chain, making code optimization and debugging more difficult.

3. **Eval Scope Limitation**: Code within `eval()` is executed in its own scope, ensuring that variables or functions within `eval()` do not affect the surrounding scope.

4. **Controlled `this` Keyword Behavior**: In non-method functions, `this` is `undefined` instead of defaulting to the global object, reducing the risk of unintended references to the global scope.

5. **No Duplicate Parameter Names**: Functions cannot have parameters with the same name, aiding in the prevention of coding mistakes.

6. **Immutable Non-Writable Properties**: Assignments to non-writable properties result in an error, ensuring data integrity.

7. **Protection Against Deleting Fixed Properties**: Attempts to delete undeletable properties (like `Object.prototype`) trigger an error.

8. **No Octal Literals and Syntax**: Octal literals and escape sequences are disallowed, avoiding confusion with string data.

In conclusion, strict mode in JavaScript helps in writing safer and cleaner code by turning silent errors into throw errors, enforcing variable declarations, clarifying function scope, and preventing common coding pitfalls. These features significantly contribute to the robustness and maintainability of JavaScript code.

## Garbage Collection in JavaScript

Garbage collection in JavaScript is an automated process that identifies and frees up memory that is no longer being used by the application. This process is vital for preventing memory leaks and ensuring efficient memory usage. JavaScript implements garbage collection primarily through the following methods:

1. **Reference Counting**: In this method, the garbage collector counts the number of references to a value. When the reference count drops to zero, indicating that no part of the program is using that value, it is considered garbage and eligible for collection. However, reference counting has a significant limitation with circular references, where two objects reference each other, leading to memory leaks as their reference count never reaches zero.

2. **Mark-and-Sweep Algorithm**: Modern JavaScript engines, such as V8 (Chrome, Node.js) and SpiderMonkey (Firefox), use the Mark-and-Sweep algorithm. This method involves marking "roots" (variables directly referenced by the code being run, plus global variables). The garbage collector then traverses from these roots and marks all reachable objects. Objects not marked as reachable are considered unreachable and eligible for garbage collection. This approach effectively resolves the issue of circular references found in reference counting.

### Related Topics: Memory Management in JavaScript
- Understanding memory management is crucial for JavaScript developers, particularly for performance optimization.
- Developers should be aware of how different data types and structures affect memory usage.
- Profiling memory usage using browser tools can provide insights into how an application allocates and releases memory.

## Closures and Memory Leaks in JavaScript

Closures in JavaScript are not inherent sources of memory leaks. They are essential features that allow functions to access and remember variables from their lexical scope, even after the outer function has executed. However, if closures retain references to extensive scopes or objects longer than needed, they can contribute to memory leaks. This typically occurs when a closure, no longer in use, is still referenced in the code, preventing the garbage collector from freeing the memory of the scope's variables. Developers can prevent such issues by carefully managing the lifecycle of closures and ensuring they are dereferenced when no longer needed. This is particularly important in scenarios with loops or large objects.

### Related Topics: Efficient Use of Closures
- Closures are powerful for creating private variables and encapsulating functionality.
- Proper closure management involves understanding scope and closure lifecycles.
- In large applications, mindful use of closures can significantly impact performance and memory efficiency.

## Detecting Memory Leaks in JavaScript and React

To detect memory leaks in JavaScript and React, tools like the Chrome Developer Tools are invaluable. The Performance tab in these tools allows developers to record memory usage while interacting with the application. Observing the heap usage over time helps identify potential memory leaks, indicated by a continuous increase in memory usage without drops after garbage collection cycles. Common scenarios leading to memory leaks in React include:

- Unmanaged event listeners
- Uncleared timers
- Misuse of external libraries
- Improper handling of state and props

Preventing memory leaks involves proactive resource management, such as removing event listeners and clearing timers when components unmount.

### Related Topics: Best Practices for Avoiding Memory Leaks
- Regularly profile your application using browser development tools to monitor memory usage.
- Understand and apply lifecycle methods in React to clean up resources.
- Avoid common pitfalls like closures over large data sets, unmanaged event listeners, and global variables.

## WeakMap and WeakSet in JavaScript

WeakMap and WeakSet in JavaScript are collections that store objects weakly, meaning their elements are not prevented from being garbage-collected. 

- **WeakMap**: Allows associating data with objects without preventing their garbage collection. This is useful for private data or caches that do not interfere with the lifecycle of the objects. Ideal for situations where you want to avoid creating memory leaks by inadvertently retaining references to objects.

- **WeakSet**: Enables tracking a group of objects for presence checks without affecting their garbage collection. This is useful for tracking which objects have undergone a specific process without creating memory leaks.

### Related Topics: Use Cases for WeakMap and WeakSet
- WeakMap and WeakSet are particularly useful in scenarios where memory efficiency is crucial.
- They are often used in managing caches, tracking object references, and keeping metadata about objects without affecting their lifecycle.
- Understanding when to use WeakMap and WeakSet can significantly optimize memory usage in complex applications.

## Traverse an Array: `for` vs. `forEach` Performance

### Performance Comparison
When it comes to traversing an array in JavaScript, both `for` loops and the `forEach` method are commonly used. Each has its own strengths in terms of performance and readability. The primary distinction in their performance is attributed to the inherent differences in their implementation.

1. **Function Calls**: A `for` loop directly accesses each element in the array without additional overhead. In contrast, `forEach` uses a callback function for each element, introducing slight overhead due to the creation of a new execution context for each iteration.
2. **Flexibility and Optimization**: `for` loops offer greater flexibility, allowing the use of `break`, `continue`, and modification of the iteration index. This can lead to more optimized solutions in certain scenarios.

### Readability and Maintenance
Despite the potential speed advantage of `for` loops, `forEach` is often preferred for its readability and maintenance benefits. It provides a more declarative approach to iterating over arrays, improving code clarity and reducing the likelihood of common errors associated with `for` loops, like incorrect index usage.

### Practical Implications
In modern JavaScript engines, the performance gap between `for` and `forEach` is generally minimal for most practical applications. Thus, the decision to use one over the other should also consider factors like code readability, complexity of operations within the loop, and specific application requirements.

### Conclusion
While `for` loops can be faster due to lower overhead and greater optimization potential, the `forEach` method often offers more readable and maintainable code. The choice between the two should balance the need for performance with the benefits of cleaner and more expressive code, tailored to the specific needs of the project.

