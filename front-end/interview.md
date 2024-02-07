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

## heap VS binary search tree
- searching is slower than BST, the left and right node is not ordered so we cannot use binary search
- add/search is faster, saves time in balancing in overal
- both time complexity is at O(logn) level, which is height of tree

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

## Why 0.1 + 0.2 !== 0.3

This is a result of how computers handle binary floating-point arithmetic.

When you add these approximations, the tiny errors in their representation lead to results that are not exact, hence 0.1 + 0.2 results in something slightly different from 0.3. This is an issue inherent in IEEE 754 standard for floating-point arithmetic, which is used by most modern programming languages.

In practical terms, to compare floating-point numbers in such cases, a common approach is to check if they are close enough to each other, within a small tolerance, rather than expecting exact equality.

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

## Implement debouncing in typescript
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

## Implement a throttling function in JavaScript
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

## Why send options request when using HTTP cross origin?

### Understanding the Importance of OPTIONS Requests in Cross-Origin HTTP Communication

1. **Same-Origin Policy**: A fundamental security concept in web development, the same-origin policy restricts how a document or script loaded from one origin can interact with resources from another origin. This policy is implemented by web browsers to prevent potentially malicious scripts on one website from obtaining access to sensitive data on another website.

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

## How to Prevent 300ms Delay for Double Click to Zoom on Mobile Phones?
On mobile web applications, a common issue is the 300ms delay when users attempt to double-click (tap) to zoom. This delay was originally implemented to differentiate between a tap (single click) and a double-tap (double click). However, this can interfere with the responsiveness of web applications. In the past, developers used libraries like FastClick to circumvent this delay. Modern browsers have introduced ways to address this issue by detecting the site's responsiveness through meta tags.

To prevent the 300ms delay on mobile devices without relying on external libraries like FastClick, ensure your web application is using responsive design principles. Implement the following meta tag in your HTML:
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```
This meta tag informs the browser that your website is optimized for mobile devices, prompting it to disable the 300ms delay for a better user experience. This approach is preferred as it relies on standard responsive design practices rather than additional scripts, improving your website's performance and compatibility.

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

## Front-End Security Threats and Prevention Measures

### XSS (Cross-Site Scripting)
XSS attacks occur when an attacker injects malicious JavaScript code into a web application's output. The injected code executes within the victim's browser when they visit the compromised web page.

**Prevention:** Ensure the encoding or escaping of user input on both the front-end and back-end. For example, convert `<` to `&lt;` and `>` to `&gt;`. Modern JavaScript frameworks like React automatically escape HTML to safeguard against XSS, significantly reducing the risk.

### CSRF (Cross-Site Request Forgery)
In CSRF attacks, attackers trick users into executing unwanted actions on a web application where they're authenticated, leveraging the user's identity.

**Prevention:** Employ anti-CSRF tokens and set the `SameSite` attribute for cookies to `strict` to prevent cross-site request forgery. Limiting CORS (Cross-Origin Resource Sharing) and utilizing authentication mechanisms also bolster security.

### Clickjacking
Clickjacking tricks users into clicking on something different from what the user perceives, often by embedding a page as a transparent iframe.

**Prevention:** To prevent clickjacking, ensure that your website does not allow itself to be embedded in an iframe on another site by setting the `X-Frame-Options` header to `SAMEORIGIN`. Also, verify that `window.top.location.hostname` is the same as `window.location.hostname`; if not, redirect the user appropriately.

### DDoS (Distributed Denial of Service)
DDoS attacks flood a server with numerous requests to exhaust resources and bandwidth, rendering the service unavailable to legitimate users.

**Prevention:** DDoS protection is challenging to implement at the software level alone; employing cloud-based DDoS protection services or Web Application Firewalls (WAF) can help mitigate these attacks.

### SQL Injection
SQL Injection attacks occur when an attacker is able to insert or "inject" a SQL query via the input data from the client to the application.

**Prevention:** Safeguard against SQL Injection by validating and sanitizing all user inputs. Utilize prepared statements and parameterized queries to ensure the database executes only the intended queries, not the injected malicious code.

### Best Practices for Prevention
Implementing robust security measures on both the front-end and back-end is crucial for protecting web applications against these attacks. This includes validating user inputs, employing security headers, and adhering to secure coding practices. Regular security audits and updates can also significantly reduce vulnerabilities.

# Front-end Developer Interview Questions

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
