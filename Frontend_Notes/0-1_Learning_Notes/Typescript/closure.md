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
