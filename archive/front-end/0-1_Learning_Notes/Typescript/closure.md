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
