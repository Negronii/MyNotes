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
The stack in frontend memory management is a structured region of memory that operates on a Last In, First Out (LIFO) basis. It's used primarily for storing primitive data types and pointers to objects during function calls. When a function is called, its variables are pushed onto the stack, and they are popped off when the function exits. The stack is fast and efficient for managing function calls due to its structured nature but is limited in size. Overuse can lead to a stack overflow error. It's ideal for temporary, short-lived data.

## How does the heap function in memory management for frontend web applications?
In frontend applications, the heap is a key area of memory used for dynamic allocation, especially for storing objects and complex data structures. It's a less organized memory pool compared to the stack and is managed manually. 

In terms of structure, the heap can be visualized as a complete binary tree, where each parent node is smaller (in a min-heap) or larger (in a max-heap) than its children. 

The logical structure of the heap is a binary tree, but physically, it is often implemented as an array. This array-based implementation maximizes space usage due to continuous memory allocation. In the array, the first index is often ignored for convenience, with the heap starting from the second index. For any given index `i` in this array, the parent node can be found at `Math.floor(i/2)`, while the left and right children are located at `2 * i` and `2 * i + 1`, respectively. This structure allows efficient operations like insertion and removal, which are crucial for managing dynamic data in web applications.

## Explain the difference between primitive types and reference types

In JavaScript, primitive types (like `number`, `string`, `boolean`, `null`, `undefined`, `symbol`, and `bigint`) are stored directly in the location the variable accesses. They are stored in the stack, which provides quick access and efficient memory allocation. When you assign a primitive type to a variable, you're copying the value into that variable.

On the other hand, reference types (like `object`, `array`, and `function`) are stored in the heap, which is a larger pool of memory designed for storing larger, more complex data. Instead of storing the actual data in the variable on the stack, JavaScript stores a reference (or pointer) to the location in memory where the data is held. This means when you manipulate an object or an array, you're working with a reference to that data, not the actual data itself. Any changes made through one reference are seen by all other references because they all refer to the same underlying data in the heap.

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

### Ajax (Asynchronous JavaScript and XML)

1. **What it is**: Ajax is not a technology in itself, but a term that refers to the use of a group of technologies together. These technologies include HTML, CSS, JavaScript, the DOM, XML, XSLT, and most importantly, the XMLHttpRequest object. Ajax allows web pages to be updated asynchronously by exchanging small amounts of data with the server behind the scenes. This means it's possible to update parts of a web page, without reloading the whole page.

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

1. **What it is**: The Fetch API provides a more modern and powerful way to make web requests. It is a built-in window object in modern browsers, replacing the need to use the more complex XMLHttpRequest. Fetch returns Promises and is much cleaner and easier to use.

2. **Code Example**:
   ```javascript
   fetch('https://api.example.com/data')
     .then(response => response.json())
     .then(data => console.log(data))
     .catch(error => console.error('Error:', error));
   ```

### Axios

1. **What it is**: Axios is a popular, promise-based HTTP client for the browser and node.js. It provides a simple to use library in a small package with a very extensible interface. It's capable of making XMLHttpRequests from the browser and http requests from node.js, supports the Promise API, intercept request and response, transform request and response data, cancel requests, and automatic transforms for JSON data.

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

### Sample Interview Answer

Ajax, Fetch, and Axios are all related to making HTTP requests in web applications, but they differ in their approach and implementation.

- Ajax is a broad set of technologies that allows web applications to send and retrieve data from a server asynchronously without interfering with the display and behavior of the existing page. It mainly uses the `XMLHttpRequest` object for this purpose.
- The Fetch API is a modern interface in JavaScript that allows you to make HTTP requests. It's more powerful and flexible than Ajax's `XMLHttpRequest` and returns promises, making it easier to use in modern web applications.
- Axios is a third-party library that simplifies making HTTP requests. It provides a more user-friendly API and additional features like intercepting requests and responses, which are not natively available in Fetch.

In summary, while Ajax refers to a classical web development practice for asynchronous requests, Fetch and Axios are more modern approaches with Axios offering additional features and a simpler API over the native Fetch API.


## What is debouncing and what is throttling, what are the differences, and name use cases of each

**Debouncing**

Debouncing in the context of web development is a programming practice used to ensure that time-consuming tasks do not fire so often, which can be inefficient or harmful to performance. This is particularly useful in situations where some code is not only triggered by user actions but is also potentially triggered repeatedly or rapidly, like resizing windows or scrolling.

A debounced function will only execute after a certain amount of time has passed since it was last called. So, if the debounced function is attached to an event like scrolling, it will only execute after the user has stopped scrolling for a specified time.

**Throttling**

Throttling, like debouncing, is a technique to control how many times a function can be executed over time. It's used to ensure that the function is only called at every specified time interval. For example, if you have a function that fires on a scroll event and you throttle it to execute only once every 100 milliseconds, the function will execute at most 10 times per second, no matter how many times the scroll event fires.

**Differences between Debouncing and Throttling**

1. **Timing Control**: Debouncing is based on the principle of delaying the execution of a function until after some time has elapsed since the last time it was invoked. Throttling, on the other hand, ensures that a function is executed at regular intervals.

2. **Use Cases**: Debouncing is typically used in situations where you want to ensure that a function is not executed too frequently, but also don't care if there are delays in execution. Throttling is used when you need to guarantee a steady, consistent rate of execution.

3. **Behavior**: In debouncing, the function will only be executed after the triggering event has stopped for a defined period. In throttling, the function will execute at regular intervals regardless of how many times the user triggers the event.

**Use Cases**

1. **Debouncing**: A common use case for debouncing is in search bars. As a user types, you don't want to fire off an API request for every keystroke. Instead, you wait until the user pauses or stops typing before sending the request.

2. **Throttling**: Throttling is often used in scroll events. For example, if you have an infinite scroll feature on a website, you don't want to load more content every single pixel of scroll. Instead, you can throttle the scroll event to load more content at every certain interval of scrolling.

These techniques are crucial for optimizing performance and user experience in web applications.

In reality, we use **Lodash** library to achieve Debouncing and Throttling.

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

## What are the drawbacks of arrow functions and situations where they can't be used

Arrow functions do not have their own this context. They lexically bind their this value from the surrounding context. This is useful in some scenarios (like callbacks) but poses limitations in others.
It wont work in the dynamic context callback function
```ts
const btn = document.getElementById('btn');
btn.addEventListener('click', () => {
    // here, `this` is window, not button
    console.log(this === window);
    this.innerHTML = 'clicked'
})
```

```ts
function f1(){
    console.log(this) // will return this function
}

console.log(this)
const f2 = () => {
    console.log(this) // will return same value as above 'this' side effect scope, not the function itself
}
```

No arguments Object: Unlike regular functions, arrow functions do not have an arguments object. This can be circumvented by using rest parameters.
```ts
// continued from above
f1.call({x:100}) // this will work
f2.call({x:100}) // this not will work
```

Not Suitable for Object Methods: When used as methods in objects, this will not refer to the object itself but to the surrounding lexical context.
```ts
const obj = {
    name: 'aaa';
    getName = () => {
        return this.name
    }
}

obj.getName() // this wont work
```

Not Suitable for Prototype Methods: Similar to object methods, this in an arrow function used as a prototype method will not refer to the object instance.
```ts
const obj = {
    name: 'aaa';
}
obj.__proto__.getName = () => {
        return this.name
    }

obj.getName() // this wont work either
```

Cannot be Used as Constructors: Arrow functions cannot be used as constructor functions. They cannot be used with the new keyword since they don't have a this context.
```ts
const Foo = (name, age) => {
    this.name = name;
    this.age = age
}
const f = new Foo('aa', 20); // this wont work
```

### Sample answer: 
Arrow functions in JavaScript are beneficial for their concise syntax and lexical this binding, but they have limitations. They are not suitable as constructor functions, object methods, prototype methods, or in any scenario where the function needs its own this context. They also lack the traditional arguments object. These limitations make them less versatile in certain use cases, particularly in object-oriented programming.

## Describe TCP 3-way handshake and 4-way termination
### TCP 3-Way Handshake (Connection Establishment)
The TCP 3-way handshake is a process used in the TCP/IP protocol to establish a connection between a client and server.

1. **SYN**: The client sends a SYN (synchronize) packet to the server to initiate a connection. This packet contains an initial sequence number for the connection.
2. **SYN-ACK**: The server responds with a SYN-ACK (synchronize-acknowledge) packet. This acknowledgment packet confirms receipt of the SYN packet and includes the server's own initial sequence number.
3. **ACK**: The client sends an ACK (acknowledge) packet back to the server, acknowledging receipt of the server's SYN-ACK packet. This completes the handshake, and the connection is established.

### TCP 4-Way Termination (Connection Termination)
The 4-way termination process is used to gracefully close a TCP connection.

1. **FIN from Initiator**: The party wishing to terminate the connection (let's say A) sends a FIN (finish) packet to the other party (B), indicating it has finished sending data.
2. **ACK from Receiver**: B sends an ACK packet back to A, acknowledging the receipt of the FIN packet.
3. **FIN from Receiver**: After B has finished sending its remaining data, it sends its own FIN packet to A, indicating it too is ready to close the connection.
4. **ACK from Initiator**: A sends a final ACK packet to B, acknowledging the receipt of B's FIN packet. After this step, A can close the connection. B, upon receiving this final ACK, also closes the connection.

### Sample Answer
The TCP 3-way handshake is a method used in the TCP/IP protocol to establish a connection between two parties. It involves three steps: SYN, SYN-ACK, and ACK, ensuring both parties are ready to transmit data. On the other hand, the TCP 4-way termination process, also known as the 4-way handshake, is used for closing a connection. It involves four steps: a FIN packet from the initiator, an ACK from the receiver, a FIN from the receiver, and a final ACK from the initiator. This process ensures that both parties have completed transmitting all their data before the connection is closed.

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

### Box Model Explanation

The CSS box model is a fundamental concept in web development that describes how the dimensions of each HTML element are calculated. The components of the box model, from outer to inner, are:

1. **Margin**: The outermost layer, which defines the space between the element's border and surrounding elements.
2. **Border**: The border that surrounds the padding and content. It's the boundary between the margin and the padding.
3. **Padding**: The space between the border and the content. It increases the space inside the element.
4. **Content**: The innermost area where the actual text, images, or other media are displayed.
5. **Box-sizing**: A property that determines how the width and height of an element are calculated. If set to `border-box`, the element's padding and border are included in the element's width and height. If set to `content-box`, the width and height only include the content, not the padding or border. 

### Differences Between offsetHeight, scrollHeight, and clientHeight

1. **offsetHeight**: The `offsetHeight` property measures the total visible height of an element, including padding, border, and the scroll bar on the element (if any), but excluding margins. It's the outermost height measurement that includes everything inside the margin.

2. **clientHeight**: The `clientHeight` property measures the visible content area (including padding) of an element but excludes the border, scrollbar, and margin. It's useful for getting the actual area available for the content inside an element.

3. **scrollHeight**: The `scrollHeight` property measures the total height of an element's content, including content not visible on the screen due to overflow. It includes padding but excludes borders, scrollbar, and margin. This is larger than the `clientHeight` if there's content that overflows outside the visible area.

### Sample Answer
The primary differences among `offsetHeight`, `scrollHeight`, and `clientHeight` relate to what they include in their calculations. `offsetHeight` includes the border, padding, and the vertical scrollbar (if present), making it the total outer height. `clientHeight` includes the padding and the viewable content height, but not the border or scrollbar. Lastly, `scrollHeight` measures the total height of the content, including what's not visible due to overflow, plus padding. These properties are essential for dynamically managing layouts, handling scrolling behavior, or adjusting elements based on their content size.

## Explain difference between HTMLCollection and NodeList

The DOM represents a document as a tree structure where `Node` is the fundamental building block. All other entities like elements, text, and comments are derived from `Node`. This hierarchy is important to understand the relationship between different types of nodes and how they interact within the DOM tree.

- `Node`: The basic unit in the DOM tree, serving as a parent for more specific nodes.
- `Element`: Represents an element in the HTML document. It's a specific type of node that can have attributes and child nodes.
- `HTMLElement`: A further specialization of `Element` that represents elements specifically defined by HTML standards.
- `HTMLCollection` and `NodeList` are collections used to represent groups of nodes. However, they differ in what they contain and how they are updated:

  - `HTMLCollection`: A live collection that specifically contains `Element` nodes. It automatically updates when the DOM changes. It's commonly returned by methods like `document.getElementsByClassName` or the `.children` property of an element.
  - `NodeList`: A collection that can hold any type of `Node`, including `Element`, `Text`, and `Comment` nodes. Depending on how it's obtained, it can be live (automatically updating with the DOM) or static (not updating). For example, `NodeList` returned by `Node.childNodes` is live, while `NodeList` returned by `document.querySelectorAll` is static.

**Difference between HTMLCollection and NodeList:**

The primary difference between an `HTMLCollection` and a `NodeList` lies in the types of nodes they can contain and their dynamism in reflecting changes to the DOM:

1. **Node Types**: `HTMLCollection` is exclusively a collection of `Element` nodes, which are HTML elements. On the other hand, `NodeList` can contain any type of nodes, including `Element`, `Text` (text inside elements), and `Comment` nodes.

2. **Dynamism**: `HTMLCollection` is live, meaning it updates automatically to reflect changes in the DOM. If an element is added or removed, the `HTMLCollection` immediately reflects this change. However, not all `NodeList` objects are live; some (like those returned by `document.querySelectorAll`) are static snapshots of the DOM state at the time of their creation. Others, like the list returned by `.childNodes`, are live.

### `.children` vs `.childNodes`
Assume we got
```html
<p id='p1'>
    <em>hello</em> hello <b>bold</b><!-- comment -->
</p>
```

```ts
const p = document.getElementById('p1')
p.children // this is instance of HTMLCollection, not NodeList
// here p.children has em, has b, but does not have text like hello, bold, and the comment text
p.childNodes //this is a instance of NodeList
//here p.childNodes include em, text, b, comment, where text is the second hello
p.tagName // correct only if this p is an Element
p.nodeName // correct only if this p is a Node
```

### Sample answer
Both are collections used in the DOM to handle groups of nodes, but they differ mainly in two aspects: the types of nodes they can contain and whether or not they are live. `HTMLCollection` is a live collection that only includes `Element` nodes and automatically updates with the DOM, making it ideal for working with HTML elements directly. `NodeList`, however, can contain any type of nodes, including text and comments, and can be either live or static, offering more flexibility in handling various parts of the DOM.

## What are the features of JavaScript's strict mode?
Strict mode in JavaScript is a way to opt into a restricted variant of JavaScript. By invoking strict mode, you can make your code safer by eliminating some JavaScript silent errors, making them throw errors instead. This helps in debugging and writing "cleaner" code. It also prevents or throws errors for actions that are considered bad practices or that could lead to bugs in your JavaScript code.

Strict mode can be enabled by adding `'use strict';` at the beginning of a script or a function. The scope of strict mode depends on where it is declared. If it's declared at the top of a file, it applies to the entire script. If it's declared at the beginning of a function, it applies only to that function.

### Features of Strict Mode

1. **Variables Must Be Declared**: In strict mode, all variables must be declared before use. This means that if you try to use a variable without declaring it first, JavaScript will throw a reference error.

2. **The `with` Statement Is Not Allowed**: The `with` statement is forbidden in strict mode as it makes the scope ambiguous and the code harder to optimize and debug.

3. **Creates Eval Scope**: Code evaluated by `eval()` is executed in its own lexical scope in strict mode, meaning that variables or functions declared inside of an `eval()` statement are not created in the containing scope.

4. **`this` Keyword in Functions**: In strict mode, when a function is called without an explicit subject (i.e., without an object as context), the value of `this` is `undefined` rather than the global object (window in browsers). This helps avoid common mistakes like inadvertently referring to the global object.

5. **Duplicate Parameter Names Are Not Allowed**: In strict mode, you cannot have functions with duplicate named parameters, which can help avoid confusing bugs in your code.

6. **Assignments to Non-Writable Properties Throw an Error**: In non-strict mode, assigning a value to a non-writable property silently fails. In strict mode, it throws an error.

7. **Attempting to Delete Undeletable Properties Throws an Error**: In strict mode, trying to delete a property that cannot be deleted (like `Object.prototype`) will throw an error.

8. **Octal Syntax Is Not Allowed**: In strict mode, octal literals and octal escape sequences are not allowed, preventing errors related to ambiguous string data.

### Sample Answer

JavaScript's strict mode is a feature that allows developers to opt into a restricted variant of JavaScript, making it easier to write secure and robust code. By declaring `'use strict';` at the beginning of a script or function, we activate strict mode which enforces several constraints: variables must be declared before use, the `with` statement is disallowed, creating a more predictable scope for `eval()`, and ensuring `this` does not default to the global object in functions called without an explicit subject. Additionally, strict mode forbids duplicate parameter names in functions, throws errors for assignments to non-writable properties and undeletable properties, and disallows octal syntax. These features help prevent common coding pitfalls and enhance code quality by making certain errors more apparent during the development phase.

## Why send options request when using HTTP cross origin? 

1. **Same-Origin Policy**: This security measure is implemented by web browsers to prevent malicious websites from accessing resources and data hosted on another domain without permission. It ensures that scripts running on one page cannot make requests to another domain without explicit consent from the domain being requested.

2. **Cross-Origin Resource Sharing (CORS)**: To allow web pages to overcome the same-origin policy restrictions safely, CORS was introduced as a mechanism that enables secure cross-origin requests and data sharing. This is where the OPTIONS preflight request comes into play.

3. **OPTIONS Preflight Request**: Before sending an actual request (like GET, POST, PUT, DELETE), the browser sends an OPTIONS request to the server hosting the cross-origin resource. This preflight request checks if the actual request is safe to send by examining what HTTP methods and headers are allowed by the server for cross-origin requests.

4. **Cross-Origin Requests without Preflight**: Not all cross-origin requests trigger a preflight. Simple requests, or those that meet specific criteria (such as using only certain safe HTTP methods or headers), don't require an OPTIONS preflight. However, for most AJAX requests that might modify data on the server or involve credentials, a preflight check is mandatory.

### CORS solutions
**Solution 1**
```html
<!-- www.aaa.com Mx -->
<script>
    window.onSuccess = function (data) {
        console.log(data)
    }
</script>
<script src="https://www.bbb.com/api/getData"></script>
<!-- https://www.bbb.com/api/getData 返回了一段字符串： -->
'onSuccess({ errno: 0, data： { /* 数据内容 */ }})'
```
Utilizes a workaround by injecting a `<script>` tag from another origin. The script returns a function call as a string, which is then executed by the browser. This method circumvents the same-origin policy but is limited in use and doesn't involve an OPTIONS request.

**Solution 2 (prefered)**
```ts
// CORS 配置允许跨域（服务端）
response.setHeader ("Access-Control-Allow-Origin", "http://localhost: 8011")//或者 '*'
response.setHeader ("Access-Control-Allow-Headers", "X-Requested-With")
response.setHeader ("Access-Control-Allow-Methods", "PUT, POST, GET, DELETE, OPTIONS") 
response.setHeader ("Access-Control-Allow-Credentials", "true") // allow accept cookie
```
Properly configuring CORS on the server-side to explicitly allow cross-origin requests from certain origins, methods, and headers. This is the preferred and secure method to handle cross-origin requests, directly addressing the need for an OPTIONS preflight request to ensure security and compliance.

### Sample Answer

An OPTIONS request is sent as part of the CORS protocol to ensure secure communication between different origins. This preflight request is automatically initiated by the browser to verify whether the server supports the intended cross-origin request. It checks the server's policies on accepting requests from different origins, the methods allowed, and the headers that can be included in the actual request. This mechanism helps in mitigating potential security risks by ensuring that only permitted cross-origin requests are made, adhering to the server's access control policies. The use of an OPTIONS request is a critical step in the security model of the web, allowing developers to build web applications that can safely interact with resources across different domains.

## What is Restful API
RESTful APIs are architectural guidelines for designing networked applications. They rely on stateless, client-server communication, where operations are performed using standard HTTP methods. For managing a blog, RESTful APIs provide endpoints for creating (POST), deleting (DELETE), updating (PATCH or PUT), and querying (GET) blog posts. Each operation targets a specific resource, identified by a URL, and uses the appropriate HTTP method to convey the action. For updates, PUT replaces an entire resource, while PATCH modifies parts of it, making PATCH more suitable for updates where only a few fields change. This approach to API design promotes scalability, simplicity, and flexibility.

## How do JS do garbage collection and what is garbage collection
Garbage collection in JavaScript is a process that automatically identifies and frees up memory that is no longer in use by the application. This is crucial in preventing memory leaks and ensuring that the application uses memory efficiently. JavaScript's garbage collection mechanism can be understood through two primary methods:

1. **Reference Counting**: This is an older strategy where the garbage collector keeps track of how many references exist to a value. If the reference count drops to zero, meaning no part of your program is using that value anymore, it can be considered garbage and thus eligible for collection. However, this method has a significant drawback related to circular references. If two or more objects reference each other, they can create a loop that prevents their reference count from ever reaching zero, leading to memory leaks.

2. **Mark-and-Sweep Algorithm**: This is the more modern approach used by JavaScript engines like V8 (Chrome, Node.js) and SpiderMonkey (Firefox). The algorithm marks the "roots" (variables directly referenced by the code you're running plus global variables, like `window` in browsers). It then traverses from these roots and marks all reachable objects. Any object that is not marked as reachable by the end of this traversal is considered unreachable and can be garbage-collected. This approach effectively solves the circular reference problem found in the reference counting method.

### Sample Answer
Garbage collection in JavaScript is a critical process that automatically identifies and frees up memory that is no longer being used, preventing memory leaks and ensuring efficient memory use. Initially, JavaScript utilized a method known as reference counting, which tracked how many references were made to a particular value. However, this method had a significant limitation, particularly with circular references, where two objects reference each other, preventing their reference counts from ever reaching zero and thus not being eligible for garbage collection.

To overcome this, modern JavaScript engines now employ the Mark-and-Sweep algorithm. This method starts from root references, such as global variables or active ones in the current execution context, and marks all reachable objects. Any objects that are not marked during this process are considered unreachable and are cleared from memory. This approach is more efficient and avoids the pitfalls of circular references, ensuring that unused memory is reclaimed for future use, which is essential for the performance and reliability of web applications.

## Is closure a memory leak in JS?
Closures in JavaScript are not inherently sources of memory leaks; they are a fundamental part of the language's functionality, allowing functions to access and remember variables from their lexical scope even after the outer function has finished executing. However, closures can potentially lead to memory leaks if they retain references to large scopes or objects longer than necessary. This happens when a closure that is no longer needed still remains referenced in the code, preventing the JavaScript engine's garbage collector from freeing up the memory occupied by the scope's variables. To prevent such issues, it's important to be mindful of the lifecycle of closures and ensure they are dereferenced when no longer needed, especially in scenarios involving loops or large objects. This careful management of closures ensures efficient memory usage without sacrificing the powerful capabilities they provide in JavaScript programming.

## How to detect memory leak in JS? What are the scenarios in JS or React? 
To detect memory leaks in JavaScript and React, I primarily use the Chrome Developer Tools, particularly the Performance tab. By recording the memory usage while interacting with the application, I observe the heap usage over time. A continuous increase in memory usage without corresponding drops after garbage collection indicates a potential memory leak. Common scenarios in React involve unmanaged event listeners, uncleared timers, misuse of external libraries, and improper handling of state and props. Proactively managing resources, such as removing event listeners and clearing timers when components unmount, is crucial for preventing memory leaks.

## What is WeakMap WeakSet? What are the use cases?
In JavaScript, WeakMap and WeakSet are specialized collections that store objects weakly. This means they do not prevent their elements from being garbage-collected. A WeakMap allows us to associate data with an object in a way that doesn't prevent the object from being collected, making it ideal for private data or caches that do not interfere with garbage collection. Similarly, a WeakSet lets us track a group of objects for presence checks without affecting their lifecycles, useful for keeping track of which objects have undergone a certain process. Both are crucial for memory-efficient code, especially in applications with complex object graphs or those that require fine-grained control over memory and lifecycle management.

## Difference Between Browser and Node.js Event Loop:

JavaScript, being single-threaded, utilizes the event loop mechanism to handle asynchronous operations, enabling non-blocking execution. This is crucial in both browser and Node.js environments, yet the implementation and behavior of the event loop differ in each due to their distinct operational contexts and requirements.

### Micro-tasks and Macro-tasks:
- **Macro-tasks**: Operations like `setTimeout`, `setInterval`, and various web API calls. They are scheduled to run after the current script has completed and the micro-task queue is empty.
- **Micro-tasks**: Primarily related to promises, async/await operations. They execute immediately after the current script and before any subsequent macro-tasks, ensuring higher priority in execution.

### Browser Event Loop:
- The browser event loop shares the main thread with tasks like DOM rendering, necessitating efficient task management to prevent UI blocking.
- It operates with two types of task queues: macro-tasks and micro-tasks, with micro-tasks receiving execution priority right after the current task, even before moving to the next macro-task. This prioritization ensures that operations like promise resolutions are handled promptly, often before the next frame rendering.

### Node.js Event Loop:
- Node.js, though also single-threaded and relying on asynchronous execution, categorizes macro-tasks and micro-tasks with specific types and priorities, reflecting its backend operation focus, where UI blocking is not a concern but efficient handling of I/O operations is.
- **Macro-task types in Node.js**, ordered by priority, include:
  - **Timers**: `setTimeout`, `setInterval` for scheduling future tasks.
  - **I/O Callbacks**: Handling network, stream, and TCP errors.
  - **Idle/Prepare**: Internal Node.js engine tasks.
  - **Poll**: Retrieving new I/O events.
  - **Check**: Handling `setImmediate` callbacks.
  - **Close Callbacks**: Executing callbacks like `socket.on('close')`.

- **Micro-task types in Node.js**, include:
  - **`process.nextTick`**: Allows deferring execution of a callback until the current operation completes, with very high priority.
  - **Promise/async/await**: For handling asynchronous operations with promises.

- In Node.js, the event loop executes synchronized code first, then processes all micro-tasks (with `process.nextTick` having the highest priority), and then proceeds to execute macro-tasks, attending to micro-tasks in between as they arise.

### Sample Answer:
While the event loop mechanism in both the browser and Node.js is fundamentally similar, enabling asynchronous JavaScript execution in a single-threaded environment, there are notable differences in their implementation. In Node.js, macro-tasks and micro-tasks are specifically categorized with defined priorities, reflecting its backend focus on efficient I/O handling. Both environments execute synchronous tasks first, followed by micro-tasks due to their higher priority, and then macro-tasks. However, the browser's event loop is particularly designed to manage UI responsiveness by prioritizing micro-tasks to ensure smooth user experiences, while Node.js focuses on efficient I/O processing through its event loop structure.

## Is Virtual DOM (VDOM) fast? 
The concept of Virtual DOM (VDOM) is pivotal in modern web development, especially with frameworks like React and Vue. The Virtual DOM is essentially a lightweight copy of the real DOM (Document Object Model) represented as JavaScript objects. It was popularized by React but is now a common concept in various front-end frameworks due to its efficiency in updating the user interface.

### Understanding Virtual DOM and Its Performance

The question of whether the Virtual DOM is fast hinges on the context of the comparison. When you compare direct manipulation of the real DOM (as done with libraries like jQuery) to the process involving the Virtual DOM, direct DOM manipulation can be faster for singular, simple operations because it involves direct interaction with the browser's rendering pipeline. However, this speed comes at the cost of efficiency and scalability when dealing with complex applications.

The Virtual DOM introduces an abstraction layer that allows for a more declarative approach to defining UI components and their state changes. Here's a breakdown of how it works:
1. When data changes within an application, the entire UI is re-rendered in the Virtual DOM.
2. A diffing algorithm then compares the new Virtual DOM with a snapshot of the Virtual DOM from the last render cycle to determine the minimal set of changes needed to update the real DOM.
3. These changes are then efficiently batched and applied to the real DOM, minimizing direct manipulation and reflow/repaint costs.

### Advantages of Using Virtual DOM

- **Component-Based Architecture**: Both React and Vue utilize a component-based structure that encapsulates the UI and business logic into reusable pieces, making development more manageable and scalable.
- **Separation of Concerns**: By decoupling the data model from the UI (view), these frameworks enforce a design where the UI is a function of the state, promoting a more predictable flow of data and easier state management.
- **Efficiency in Development**: Developers can focus on state management and business logic, rather than direct DOM manipulations. This leads to more maintainable code and a faster development cycle.

### Sample Answer

Direct manipulation of the DOM, as seen in libraries like jQuery, can perform faster for individual, straightforward operations due to the absence of an intermediate layer. However, this approach lacks scalability and maintainability in complex applications. The Virtual DOM, while introducing an additional step in the rendering process, provides a more efficient and effective solution for dynamic web applications. It achieves this by:
1. Allowing data changes to trigger UI updates without manual DOM manipulation.
2. Utilizing a diffing algorithm to identify and apply only necessary changes to the real DOM.
3. Facilitating a component-based architecture that enhances code reusability and maintainability.

Thus, the Virtual DOM is not inherently faster than direct DOM manipulation in every case, but it offers a more suitable approach for building complex, interactive web applications. Its efficiency comes from reducing the amount of direct DOM manipulation required, leading to better performance in dynamic applications where state changes frequently.