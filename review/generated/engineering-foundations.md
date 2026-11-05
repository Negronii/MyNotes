# Engineering Foundations

> Generated from the [engineering-foundations reading map](../../engineering-foundations/index.md). Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; source notes remain standard Markdown.

## 1. How do input constraints and access patterns determine algorithm choice and complexity? / 输入约束与访问模式如何决定算法选择和复杂度？

Choose an algorithm by the invariant the input provides, then count the work and storage required as the input grows. Dynamic programming reuses overlapping states; binary search discards half of a sorted search range; two pointers move only when ordering proves a region cannot contain the answer. Big-O summarizes that growth under stated assumptions, while representation, allocation, memory locality, and runtime constants still affect elapsed time.

先利用输入所提供的不变量选择算法，再计算输入规模增长时所需的操作和存储。动态规划复用重叠子问题，二分查找利用有序性缩小搜索区间，双指针则只在排序等条件足以证明某一段不含答案时移动。Big-O 概括这些前提下的增长趋势；表示方式、分配、内存局部性和运行时常数仍会影响实际耗时。

Big-O leaves out cache locality, memory bandwidth, and dependent loads. See [Memory Hierarchy and Data Locality / 内存层次与数据局部性](#10.%20Why%20are%20contiguous%20scans%20often%20faster%20than%20linked-list%20walks?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F) for the hardware costs that can change elapsed time without changing an operation's asymptotic bound.

### Match the technique to the input / 按输入约束选择方法

- When several states repeat and each can be defined from earlier ones, choose a [dynamic programming state and update order](#2.%20How%20do%20you%20choose%20a%20dynamic%20programming%20state%20and%20update%20order?%20/%20%E5%8A%A8%E6%80%81%E8%A7%84%E5%88%92%E6%80%8E%E6%A0%B7%E9%80%89%E6%8B%A9%E7%8A%B6%E6%80%81%E5%92%8C%E6%9B%B4%E6%96%B0%E9%A1%BA%E5%BA%8F%EF%BC%9F).
- When order rules out a group of candidates, use [binary search or two pointers](#3.%20How%20do%20ordered%20inputs%20enable%20binary%20search%20and%20two%20pointers?%20/%20%E6%9C%89%E5%BA%8F%E8%BE%93%E5%85%A5%E6%80%8E%E6%A0%B7%E6%94%AF%E6%8C%81%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%EF%BC%9F) and prove why the discarded range is safe to ignore.
- If the job is reordering, inspect how [partition balance and copying change sorting cost](#4.%20Why%20do%20partition%20choices%20change%20quicksort%20costs?%20/%20%E5%88%86%E5%8C%BA%E9%80%89%E6%8B%A9%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E6%94%B9%E5%8F%98%E5%BF%AB%E9%80%9F%E6%8E%92%E5%BA%8F%E7%9A%84%E4%BB%A3%E4%BB%B7%EF%BC%9F).
- For text, choose [the units that define length and equality](#5.%20Which%20units%20should%20a%20text%20algorithm%20count%20and%20compare?%20/%20%E6%96%87%E6%9C%AC%E7%AE%97%E6%B3%95%E5%BA%94%E6%8C%89%E4%BB%80%E4%B9%88%E5%8D%95%E4%BD%8D%E8%AE%A1%E6%95%B0%E5%92%8C%E6%AF%94%E8%BE%83%EF%BC%9F) before analyzing a loop.

### Big-O reference

| Complexity | Typical example | Condition |
|---|---|---|
| O(1) | Array index access | Indexed access, not search |
| O(1) average | Hash-table lookup | Expected under ordinary hash distribution |
| O(log n) | Binary search; balanced BST operation | Sorted input or bounded tree height |
| O(n) | Linear scan | One pass |
| O(n log n) | Merge sort; balanced quicksort | Quicksort can degrade to O(n²) |
| O(n²) | Nested scan; simple quadratic sort | Depends on input size and algorithm |
| O(2^n) | Naive recursive Fibonacci; subset enumeration | Exponential growth |
| O(n!) | Permutation enumeration | Factorial growth |

**See also:** [Core Data Structures](#6.%20Which%20data%20structure%20fits%20the%20access%20pattern,%20and%20when%20do%20its%20cost%20bounds%20hold?%20/%20%E5%93%AA%E7%A7%8D%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E9%80%82%E5%90%88%E5%BD%93%E5%89%8D%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F) for trees and tries, and [Practical Data Structure Implementations](#7.%20How%20can%20an%20LRU%20cache%20find%20an%20entry%20and%20update%20recency%20efficiently?%20/%20LRU%20%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E9%AB%98%E6%95%88%E6%89%BE%E5%88%B0%E6%9D%A1%E7%9B%AE%E5%B9%B6%E6%9B%B4%E6%96%B0%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F) for LRU caches and [queues and stacks](#8.%20How%20do%20FIFO%20and%20LIFO%20change%20the%20representation%20of%20pending%20work?%20/%20FIFO%20%E4%B8%8E%20LIFO%20%E6%80%8E%E6%A0%B7%E5%BD%B1%E5%93%8D%E5%BE%85%E5%A4%84%E7%90%86%E5%B7%A5%E4%BD%9C%E7%9A%84%E8%A1%A8%E7%A4%BA%EF%BC%9F) for removal-order implementations.
## 2. How do you choose a dynamic programming state and update order? / 动态规划怎样选择状态和更新顺序？

Define a state with all the information its transitions need, establish base cases, then compute prerequisites before dependent states. When an update reuses the same storage, its order determines which version a transition reads. / 状态要包含转移所需的信息，先确定初始条件，再按依赖顺序计算。复用同一份存储时，更新顺序决定转移读到哪个版本。

### Dynamic programming

**动态规划 / Dynamic programming** stores results for overlapping subproblems. Top-down memoization follows the recursive definition; bottom-up iteration computes states in dependency order and can often retain only the state still needed.

#### Fibonacci

For non-negative integer n, naive recursion repeats subproblems and takes O(2^n) time with O(n) call-stack space. The iterative form takes O(n) time and O(1) auxiliary space. These examples use Number; use BigInt when exact results beyond Number's safe-integer range are needed.

~~~javascript
function fibRecursive(n) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (n <= 1) return n;
  return fibRecursive(n - 1) + fibRecursive(n - 2);
}

function fib(n) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (n <= 1) return n;
  let previous = 0;
  let current = 1;
  for (let i = 2; i <= n; i++) {
    [previous, current] = [current, previous + current];
  }
  return current;
}
~~~

#### Climbing stairs (frog jump)

Count ordered sequences of allowed positive step sizes that sum to n. The empty sequence is one way to reach step 0. Require distinct positive integer steps; repeated entries would count the same step size more than once.

~~~javascript
function climbStairs(n, steps) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError('n must be a non-negative integer');
  if (!Array.isArray(steps) || steps.some(step => !Number.isInteger(step) || step <= 0)) {
    throw new TypeError('steps must contain positive integers');
  }
  if (new Set(steps).size !== steps.length) throw new RangeError('steps must be distinct');

  const ways = new Array(n + 1).fill(0);
  ways[0] = 1;
  for (let total = 1; total <= n; total++) {
    for (const step of steps) {
      if (total >= step) ways[total] += ways[total - step];
    }
  }
  return ways[n];
}
~~~

This counts order as meaningful: with steps [1, 2], reaching 3 has three sequences: 1+1+1, 1+2, and 2+1. Time is O(nk), where k is the number of allowed steps; space is O(n).

#### 0/1 Knapsack

Choose each item at most once to maximize value within a weight capacity. Iterate capacities downward so the current item cannot be selected again during the same pass.

~~~javascript
function knapsack(capacity, weights, values) {
  if (!Number.isInteger(capacity) || capacity < 0) throw new RangeError('capacity must be a non-negative integer');
  if (!Array.isArray(weights) || !Array.isArray(values) || weights.length !== values.length) {
    throw new TypeError('weights and values must be arrays of equal length');
  }
  if (weights.some(weight => !Number.isInteger(weight) || weight < 0)) {
    throw new RangeError('weights must be non-negative integers');
  }

  const best = new Array(capacity + 1).fill(0);
  for (let i = 0; i < weights.length; i++) {
    for (let remaining = capacity; remaining >= weights[i]; remaining--) {
      best[remaining] = Math.max(best[remaining], best[remaining - weights[i]] + values[i]);
    }
  }
  return best[capacity];
}
~~~

Time is O(nW) and space O(W), for n items and integer capacity W. The zero-filled state means the result may leave capacity unused; it assumes there is no required minimum value or exact-fill constraint.

---

[Back to the main question / 返回主问题](#1.%20How%20do%20input%20constraints%20and%20access%20patterns%20determine%20algorithm%20choice%20and%20complexity?%20/%20%E8%BE%93%E5%85%A5%E7%BA%A6%E6%9D%9F%E4%B8%8E%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%AE%97%E6%B3%95%E9%80%89%E6%8B%A9%E5%92%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%EF%BC%9F).
## 3. How do ordered inputs enable binary search and two pointers? / 有序输入怎样支持二分查找和双指针？

Use ordering to prove which candidates can be discarded. Binary search shrinks a range around a monotone decision. Two pointers use relationships between positions to rule out a whole set of pairs at each move. / 用有序性证明哪些候选可以排除。二分按单调判断缩小范围，双指针利用位置之间的关系，每次移动时排除一组组合。

### Binary search

Binary search locates a matching item in O(log n) time when the input is sorted in ascending order and comparisons are consistent. This version returns any matching index, or -1 for an empty array or a missing value.

~~~javascript
function binarySearch(values, target) {
  let left = 0;
  let right = values.length - 1;
  while (left <= right) {
    const middle = left + Math.floor((right - left) / 2);
    if (values[middle] === target) return middle;
    if (values[middle] < target) left = middle + 1;
    else right = middle - 1;
  }
  return -1;
}
~~~

For fixed-width integer languages, computing the midpoint as left + (right - left) / 2 avoids overflow in left + right. JavaScript array indices are far smaller than Number's exact-integer limit, but the difference form states the safer general pattern.

---

### Two pointers

**双指针 / Two pointers** uses two positions to reduce repeated scans when the input structure provides an ordering or movement invariant. It is not a general replacement for nested loops; the invariant must justify discarding part of the search space.

#### Two Sum on a sorted array

Returns a pair of indices or null when no pair exists. Equal values at different positions are valid.

~~~javascript
function twoSumSorted(values, target) {
  let left = 0;
  let right = values.length - 1;
  while (left < right) {
    const sum = values[left] + values[right];
    if (sum === target) return [left, right];
    if (sum < target) left++;
    else right--;
  }
  return null;
}
~~~

#### Move zeros to the end

Moves numeric zeroes in place while keeping the order of non-zero values. It returns the same mutated array.

~~~javascript
function moveZeros(values) {
  let next = 0;
  for (let i = 0; i < values.length; i++) {
    if (values[i] !== 0) {
      [values[next], values[i]] = [values[i], values[next]];
      next++;
    }
  }
  return values;
}
~~~

---

[Back to the main question / 返回主问题](#1.%20How%20do%20input%20constraints%20and%20access%20patterns%20determine%20algorithm%20choice%20and%20complexity?%20/%20%E8%BE%93%E5%85%A5%E7%BA%A6%E6%9D%9F%E4%B8%8E%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%AE%97%E6%B3%95%E9%80%89%E6%8B%A9%E5%92%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%EF%BC%9F).
## 4. Why do partition choices change quicksort costs? / 分区选择为什么会改变快速排序的代价？

Each partition groups values around a pivot. Balanced partitions keep the recursion shallow, while repeatedly skewed partitions make later calls process nearly the original input size. The representation also determines whether the algorithm copies data. / 分区按基准值分组。较均衡的分区使递归较浅，持续偏斜则让后续调用仍要处理接近原规模的数据。表示方式还会决定是否复制数据。

### Sorting

#### Quicksort

This array-building version is easy to inspect, but it is not in-place. With balanced partitions it takes O(n log n) time; an adversarial sequence of pivots can take O(n²) time and O(n) recursive stack space.

~~~javascript
function quickSort(values) {
  if (values.length <= 1) return values;
  const pivot = values[Math.floor(values.length / 2)];
  const lower = [];
  const equal = [];
  const higher = [];
  for (const value of values) {
    if (value < pivot) lower.push(value);
    else if (value > pivot) higher.push(value);
    else equal.push(value);
  }
  return [...quickSort(lower), ...equal, ...quickSort(higher)];
}
~~~

For application code, prefer the built-in sort with an explicit comparator for numeric data: `values.sort((a, b) => a - b)` mutates the array, while `values.toSorted((a, b) => a - b)` returns a sorted copy where supported. Without a comparator, array elements are compared as strings. ECMAScript requires stable sorting; the engine's specific sorting algorithm is an implementation detail. See [ECMAScript 2020, Array.prototype.sort](https://tc39.es/ecma262/2020/#sec-array.prototype.sort).

---

[Back to the main question / 返回主问题](#1.%20How%20do%20input%20constraints%20and%20access%20patterns%20determine%20algorithm%20choice%20and%20complexity?%20/%20%E8%BE%93%E5%85%A5%E7%BA%A6%E6%9D%9F%E4%B8%8E%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%AE%97%E6%B3%95%E9%80%89%E6%8B%A9%E5%92%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%EF%BC%9F).
## 5. Which units should a text algorithm count and compare? / 文本算法应按什么单位计数和比较？

Choose the unit from the behavior you need. Code units support storage indexing, code points represent Unicode values, and grapheme clusters better match many user-perceived characters. Formatting, comparison, and counting should use the same explicit assumptions. / 按任务选择单位。编码单元适合存储索引，码点表示 Unicode 值，字素簇更接近许多用户感知的字符。格式化、比较和计数都应明确所用假设。

### String algorithms

The examples iterate Unicode code points with `Array.from`; that keeps surrogate pairs together. A user-perceived character can contain multiple code points, so grapheme-aware text operations need segmentation and may also need normalization.

#### Palindrome check

~~~javascript
function isPalindrome(value) {
  const characters = Array.from(String(value));
  for (let left = 0, right = characters.length - 1; left < right; left++, right--) {
    if (characters[left] !== characters[right]) return false;
  }
  return true;
}
~~~

#### Longest consecutive character

Returns the first longest run. Empty input returns an empty character and length zero.

~~~javascript
function longestConsecutive(value) {
  const characters = Array.from(value);
  if (characters.length === 0) return { char: '', len: 0 };

  let bestChar = characters[0];
  let bestLength = 1;
  let currentLength = 1;
  for (let i = 1; i <= characters.length; i++) {
    if (i < characters.length && characters[i] === characters[i - 1]) {
      currentLength++;
    } else {
      if (currentLength > bestLength) {
        bestLength = currentLength;
        bestChar = characters[i - 1];
      }
      currentLength = 1;
    }
  }
  return { char: bestChar, len: bestLength };
}
~~~

#### Number formatting (thousand separators)

For display, use locale-aware formatting and specify a locale when output must be stable across machines. The manual version below accepts only strings containing an optional minus sign and decimal digits; use locale-aware formatting for numeric values and localized output.

~~~javascript
function formatNumber(value, locale = 'en-US') {
  return new Intl.NumberFormat(locale).format(value);
}

function formatIntegerThousands(text) {
  if (typeof text !== 'string' || !/^-?\d+$/.test(text)) throw new TypeError('expected an integer string');
  const sign = text.startsWith('-') ? '-' : '';
  const digits = sign ? text.slice(1) : text;
  return sign + digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
~~~

#### Switch ASCII letter case

This example changes only the English ASCII letters A-Z and a-z; other code points are preserved.

~~~javascript
function switchAsciiCase(value) {
  return Array.from(value, character => {
    const code = character.codePointAt(0);
    if (code >= 65 && code <= 90) return String.fromCodePoint(code + 32);
    if (code >= 97 && code <= 122) return String.fromCodePoint(code - 32);
    return character;
  }).join('');
}
~~~

---

[Back to the main question / 返回主问题](#1.%20How%20do%20input%20constraints%20and%20access%20patterns%20determine%20algorithm%20choice%20and%20complexity?%20/%20%E8%BE%93%E5%85%A5%E7%BA%A6%E6%9D%9F%E4%B8%8E%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%AE%97%E6%B3%95%E9%80%89%E6%8B%A9%E5%92%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%EF%BC%9F).
## 6. Which data structure fits the access pattern, and when do its cost bounds hold? / 哪种数据结构适合当前访问模式，复杂度界何时成立？

Operation cost follows from both the structure and how an operation reaches its target. Arrays provide constant-time indexed access but shift elements on middle insertion; linked lists update in constant time only when the needed link is already known; search trees need logarithmic height for logarithmic search. Traversal order and child representation matter too, and asymptotic bounds do not capture the cost of pointer chasing versus contiguous memory.

操作代价既取决于结构，也取决于操作如何找到目标。数组按下标访问为常数时间，但在中间插入时要移动元素；链表只有在已知所需链接时才能常数时间更新；搜索树只有保持对数高度，搜索才有对数界。遍历顺序和子节点表示也会影响选择，而渐进复杂度无法体现指针追逐与连续内存访问的实际差别。

### Tree traversals

For a binary tree, depth-first orders differ in when the current node is visited:

- **In-order / 中序**: left, node, right. This yields ascending values only when the tree satisfies the binary-search-tree ordering rule.
- **Pre-order / 前序**: node, left, right. Useful when serializing a tree with enough structure to recover its shape.
- **Post-order / 后序**: left, right, node. Useful when computing or releasing children before their parent.

#### Kth smallest in a BST

This iterative in-order traversal uses O(h) stack space for tree height h. It assumes node values are non-null numbers and the tree obeys the BST ordering rule. It returns null when k is invalid or the tree has fewer than k nodes.

~~~javascript
function kthSmallest(root, k) {
  if (!Number.isInteger(k) || k <= 0) return null;
  const stack = [];
  let node = root;

  while (node || stack.length) {
    while (node) {
      stack.push(node);
      node = node.left;
    }
    node = stack.pop();
    if (--k === 0) return node.val;
    node = node.right;
  }
  return null;
}
~~~

---

### Trees and operation costs

| Structure | Indexed access / search | Insert or delete |
|---|---|---|
| Array | Index access O(1); value search O(n) | Middle insert/delete O(n) because elements move |
| Linked list | Finding by value or index O(n) | O(1) insertion at a known link; deletion needs the predecessor link (singly linked) or target node (doubly linked), otherwise O(n) worst case |
| Height-balanced BST | Search O(log n) | O(log n) |
| Unbalanced BST | Worst-case search O(n) | Worst-case O(n) |

A balanced search tree gives logarithmic operations by keeping height logarithmic. If insertions produce a chain, those operations degrade to linear time. Array access remains fast by index, while inserting into the middle shifts later elements.

These bounds do not capture cache locality or dependency chains. See [Memory Hierarchy and Data Locality / 内存层次与数据局部性](#10.%20Why%20are%20contiguous%20scans%20often%20faster%20than%20linked-list%20walks?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F) for why contiguous scans can outperform pointer-based traversal and when a known-node list update is actually O(1).

---

### Self-balancing trees

#### Red-Black Tree

A red-black tree is a binary search tree with coloring invariants that bound its height. Red nodes have black children, and every path from a node to a descendant leaf has the same black height; implementations also treat the root and leaf sentinels as black. These rules give O(log n) worst-case search, insertion, and deletion.

Java's `TreeMap` explicitly documents a red-black-tree implementation. C++ `std::map` specifies ordered associative behavior and logarithmic lookup, insertion, and key-removal bounds, but its standard does not prescribe a tree shape. Check the language and library documentation before inferring a product's internal structure: [Java `TreeMap`](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/TreeMap.html) and [C++ associative containers](https://eel.is/c++draft/associative.reqmts).

#### B-Tree and B+ Tree

B-trees are multi-way search trees designed to reduce storage-page reads by keeping several keys in each node.

- In a B-tree, records or record references may be stored in internal nodes as well as leaves.
- In a B+ tree, internal nodes guide the search and records are stored at leaves; leaf links commonly support ordered range scans.

These are family descriptions, not a guarantee that every database index uses the same variant or layout. Check the database's manual for its index type and behavior.

---

### Trie (prefix tree)

A trie shares prefixes between keys. Lookup takes O(m) steps for a key of length m when each next edge can be selected in constant expected time; the cost depends on the node's child representation. Tries can use substantial memory when keys share few prefixes.

Use one when prefix traversal or prefix queries are central, such as autocomplete or routing tables; a hash map may be simpler for exact-key lookup.

---

### DOM tree traversal

A DOM tree is a hierarchy of Node objects. Pass an explicit visit callback and a node or null root. Snapshot each node's children before walking so the traversal has a clear view if callbacks mutate the DOM.

#### DFS — depth-first search

~~~javascript
function dfs(root, visit) {
  if (!root) return;
  visit(root);
  for (const child of Array.from(root.childNodes)) {
    dfs(child, visit);
  }
}

function dfsIterative(root, visit) {
  if (!root) return;
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    visit(node);
    const children = Array.from(node.childNodes);
    for (let i = children.length - 1; i >= 0; i--) {
      stack.push(children[i]);
    }
  }
}
~~~

#### BFS — breadth-first search

~~~javascript
function bfs(root, visit) {
  if (!root) return;
  const queue = [root];
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head];
    visit(node);
    for (const child of Array.from(node.childNodes)) {
      queue.push(child);
    }
  }
}
~~~

A queue implemented with repeated `Array.prototype.shift` can move all remaining elements on each removal and make a traversal quadratic. Advancing a head index keeps this traversal O(n) in the number of visited nodes, with O(n) queue space.

DFS is useful when depth-first order or a path is needed. BFS is useful for level order and shortest paths in an unweighted graph; a DOM tree has one unique path from the root to each node.

---

### Array ↔ Tree conversion

Flat rows with parent identifiers can be transformed into a hierarchy for a tree UI or converted back for an API or database representation. This example expects unique IDs, one root whose parent ID is 0, and each other row to reference an existing parent.

#### Array to tree

~~~javascript
function arrayToTree(rows) {
  if (!Array.isArray(rows)) throw new TypeError('rows must be an array');

  const nodes = new Map();
  for (const row of rows) {
    if (!row || nodes.has(row.id)) throw new RangeError('rows must have unique IDs');
    nodes.set(row.id, { ...row, children: [] });
  }

  const roots = [];
  for (const row of rows) {
    const node = nodes.get(row.id);
    if (row.parentId === 0) {
      roots.push(node);
      continue;
    }
    const parent = nodes.get(row.parentId);
    if (!parent) throw new RangeError('parent ID does not exist');
    parent.children.push(node);
  }

  if (roots.length !== 1) throw new RangeError('expected exactly one root');
  const root = roots[0];

  const seen = new Set();
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    if (seen.has(node)) throw new RangeError('rows contain a cycle');
    seen.add(node);
    for (const child of node.children) stack.push(child);
  }
  if (seen.size !== nodes.size) throw new RangeError('rows contain a disconnected cycle');
  return root;
}
~~~

The two passes take O(n) expected time and O(n) space with a map. Reserve ID 0 for the root marker, or change the marker to match the data format.

#### Tree to array

~~~javascript
function treeToArray(root) {
  if (!root) return [];
  const rows = [];
  const stack = [{ node: root, parentId: 0 }];
  while (stack.length) {
    const { node, parentId } = stack.pop();
    rows.push({ id: node.id, parentId, name: node.name });
    const children = node.children ?? [];
    for (let i = children.length - 1; i >= 0; i--) {
      stack.push({ node: children[i], parentId: node.id });
    }
  }
  return rows;
}
~~~

This conversion expects an acyclic tree with a single root. Preserve application-specific fields deliberately; this example emits only `id`, `parentId`, and `name`.

### Linked structure in React Fiber

React represents its work tree with Fiber nodes linked through fields such as `child`, `sibling`, and `return`. The nodes still form a tree; sibling pointers encode the ordered children. This structure lets the reconciler keep work units and progress between scheduling steps.

**Concurrent rendering is conditional.** React can pause or restart render work for updates using concurrent features such as transitions. An update rendered without such features can remain synchronous. React applies DOM mutations during commit after rendering work is ready, so do not describe every render or commit as freely interruptible. Fiber is an implementation detail; use React's public APIs rather than depending on its internal node layout.

See [React 18](https://react.dev/blog/2022/03/29/react-v18) for concurrent rendering behavior and [React's Fiber types](https://github.com/facebook/react/blob/main/packages/react-reconciler/src/ReactInternalTypes.js) for the illustrative implementation.

**See also:** [Algorithms and Complexity](#1.%20How%20do%20input%20constraints%20and%20access%20patterns%20determine%20algorithm%20choice%20and%20complexity?%20/%20%E8%BE%93%E5%85%A5%E7%BA%A6%E6%9D%9F%E4%B8%8E%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%AE%97%E6%B3%95%E9%80%89%E6%8B%A9%E5%92%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%EF%BC%9F) for searches and dynamic programming, and [Practical Data Structure Implementations](#7.%20How%20can%20an%20LRU%20cache%20find%20an%20entry%20and%20update%20recency%20efficiently?%20/%20LRU%20%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E9%AB%98%E6%95%88%E6%89%BE%E5%88%B0%E6%9D%A1%E7%9B%AE%E5%B9%B6%E6%9B%B4%E6%96%B0%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F) for LRU caches and [queues and stacks](#8.%20How%20do%20FIFO%20and%20LIFO%20change%20the%20representation%20of%20pending%20work?%20/%20FIFO%20%E4%B8%8E%20LIFO%20%E6%80%8E%E6%A0%B7%E5%BD%B1%E5%93%8D%E5%BE%85%E5%A4%84%E7%90%86%E5%B7%A5%E4%BD%9C%E7%9A%84%E8%A1%A8%E7%A4%BA%EF%BC%9F) for removal-order implementations.
## 7. How can an LRU cache find an entry and update recency efficiently? / LRU 缓存怎样高效找到条目并更新使用顺序？

An LRU cache has two jobs: find an entry by key and identify the least recently used entry to evict. An insertion-ordered map can provide both if each hit moves the key to the end. A separate map and doubly linked list make the same two responsibilities explicit. / LRU 缓存有两项工作：按键查找，以及找出最久未使用的条目进行淘汰。有插入顺序的映射在每次命中时把键移到末尾，就能承担这两项工作。映射加双向链表则显式分开这两个职责。

**Key terms / 关键术语** · recency / 使用新近程度 · eviction / 淘汰 · ordered map / 有序映射

### LRU Cache

**最近最少使用缓存 / Least Recently Used cache** evicts the least recently accessed entry when full.

#### Using `Map`

`Map` preserves insertion order. Deleting and reinserting a hit moves it to the newest position. This API supports arbitrary keys and values; use `has` to distinguish a stored `undefined` from a missing key. A zero-capacity cache remains empty.

~~~javascript
class LRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
    this.capacity = capacity;
    this.cache = new Map();
  }

  has(key) {
    return this.cache.has(key);
  }

  get(key) {
    if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }

  put(key, value) {
    if (this.capacity === 0) return;
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size === this.capacity) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}
~~~

Map operations are commonly treated as expected constant-time in application analysis, but the ECMAScript specification requires average access to be sublinear rather than promising a precise O(1) bound. This version is concise and avoids maintaining a second ordering structure.

#### Doubly linked list plus map

A linked list makes moving an existing entry to the front and evicting the tail a pointer update. The map locates each node. Both structures are needed to keep the operations efficient; using an ordinary object for arbitrary cache keys can collide with inherited property names.

~~~javascript
class ListNode {
  constructor(key, value) {
    this.key = key;
    this.value = value;
    this.prev = null;
    this.next = null;
  }
}

class LinkedLRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
    this.capacity = capacity;
    this.nodes = new Map();
    this.head = new ListNode(null, null);
    this.tail = new ListNode(null, null);
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  has(key) {
    return this.nodes.has(key);
  }

  get(key) {
    const node = this.nodes.get(key);
    if (!node) return undefined;
    this._remove(node);
    this._addToFront(node);
    return node.value;
  }

  put(key, value) {
    if (this.capacity === 0) return;
    const existing = this.nodes.get(key);
    if (existing) {
      existing.value = value;
      this._remove(existing);
      this._addToFront(existing);
      return;
    }

    if (this.nodes.size === this.capacity) {
      const oldest = this.tail.prev;
      this._remove(oldest);
      this.nodes.delete(oldest.key);
    }
    const node = new ListNode(key, value);
    this.nodes.set(key, node);
    this._addToFront(node);
  }

  _addToFront(node) {
    node.next = this.head.next;
    node.prev = this.head;
    this.head.next.prev = node;
    this.head.next = node;
  }

  _remove(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }
}
~~~

With a map that provides expected constant-time lookup, the linked-list version has expected O(1) get and put operations. Use the simpler map-based version when the linked-list mechanics are not part of the requirement.

Compare [FIFO and LIFO representations / 队列和栈的表示](#8.%20How%20do%20FIFO%20and%20LIFO%20change%20the%20representation%20of%20pending%20work?%20/%20FIFO%20%E4%B8%8E%20LIFO%20%E6%80%8E%E6%A0%B7%E5%BD%B1%E5%93%8D%E5%BE%85%E5%A4%84%E7%90%86%E5%B7%A5%E4%BD%9C%E7%9A%84%E8%A1%A8%E7%A4%BA%EF%BC%9F) when work is removed in arrival or nesting order. [ECMAScript Map](https://tc39.es/ecma262/2020/#sec-map-objects) specifies observable key iteration order.
## 8. How do FIFO and LIFO change the representation of pending work? / FIFO 与 LIFO 怎样影响待处理工作的表示？

Choose the removal order first. A stack removes the newest item and maps directly to an array end. A queue removes the oldest and needs a way to advance the front without moving every remaining element on each removal. / 先定取出顺序。栈取最新项，可以直接使用数组末尾。队列取最旧项，需要移动逻辑队首，而非每次搬动其余元素。

### Queue (FIFO)

**队列 / Queue** processes values in first-in, first-out order. This linked-list version throws on an empty read so every value, including `null` and `undefined`, remains distinguishable from the empty state.

~~~javascript
class Queue {
  constructor() {
    this.head = null;
    this.tail = null;
    this.length = 0;
  }

  get isEmpty() {
    return this.length === 0;
  }

  enqueue(value) {
    const node = { value, next: null };
    if (this.tail) this.tail.next = node;
    else this.head = node;
    this.tail = node;
    this.length++;
  }

  dequeue() {
    if (this.isEmpty) throw new RangeError('queue is empty');
    const value = this.head.value;
    this.head = this.head.next;
    if (!this.head) this.tail = null;
    this.length--;
    return value;
  }

  peek() {
    if (this.isEmpty) throw new RangeError('queue is empty');
    return this.head.value;
  }
}
~~~

Enqueue, dequeue, and peek take O(1) time. Array `shift` removes the first element but may move the remaining indexed elements, so a linked queue or a head index is preferable for a queue that grows large. Breadth-first traversal with a head index appears in [Core Data Structures](#6.%20Which%20data%20structure%20fits%20the%20access%20pattern,%20and%20when%20do%20its%20cost%20bounds%20hold?%20/%20%E5%93%AA%E7%A7%8D%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E9%80%82%E5%90%88%E5%BD%93%E5%89%8D%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F).

---

### Stack (LIFO)

**栈 / Stack** processes values in last-in, first-out order. An array provides a compact stack; this version also throws on empty `pop` or `peek` so stored `undefined` is not confused with an empty stack.

~~~javascript
class Stack {
  constructor() {
    this.items = [];
  }

  get isEmpty() {
    return this.items.length === 0;
  }

  push(value) {
    this.items.push(value);
  }

  pop() {
    if (this.isEmpty) throw new RangeError('stack is empty');
    return this.items.pop();
  }

  peek() {
    if (this.isEmpty) throw new RangeError('stack is empty');
    return this.items[this.items.length - 1];
  }
}
~~~

Array `push` and `pop` are the natural stack operations. Their exact growth costs are runtime implementation details; a dynamic array may occasionally resize.

[Back to the main question / 返回主问题](#7.%20How%20can%20an%20LRU%20cache%20find%20an%20entry%20and%20update%20recency%20efficiently?%20/%20LRU%20%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E9%AB%98%E6%95%88%E6%89%BE%E5%88%B0%E6%9D%A1%E7%9B%AE%E5%B9%B6%E6%9B%B4%E6%96%B0%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F).
## 9. When should work use a thread, process, or asynchronous I/O? / 何时选线程、进程或异步 I/O？

**Core model / 核心模型：** A process is an operating-system resource and protection boundary; a thread is an execution path inside a process. Threads share much of that process's memory and therefore need coordination when they update shared state. Concurrency means work overlaps in time; parallelism means work executes at the same time on multiple processing units. Asynchronous I/O can provide concurrency without assigning one thread to every waiting operation. / 进程是操作系统管理资源并隔离地址空间的边界；线程是在进程内执行指令的路径。线程共享进程中的许多内存，因此并发修改共享状态时需要协调。并发表示任务的执行时间重叠；并行表示多个处理单元同时执行任务。异步 I/O 可以在不为每个等待中的操作分配一个线程的情况下提高并发能力。

~~~mermaid
flowchart LR
    Wait[Many tasks waiting for I/O] --> Async[Async I/O lets one thread schedule progress]
    CPU[CPU-heavy work] --> Parallel[Worker thread or process for parallel execution]
    Shared{Must share mutable state?} -->|yes| Thread[Thread plus synchronization]
    Shared -->|no, or stronger isolation needed| Process[Separate process plus IPC]
~~~

**Key terms / 关键术语：** process / 进程；thread / 线程；address space / 地址空间；concurrency / 并发；parallelism / 并行；blocking I/O / 阻塞 I/O；non-blocking I/O / 非阻塞 I/O；asynchronous I/O / 异步 I/O；race condition / 竞态；deadlock / 死锁；cancellation / 取消。

### Process and thread / 进程与线程

| Aspect / 维度 | Process / 进程 | Thread / 线程 |
| --- | --- | --- |
| Memory / 内存 | Has its own virtual address space in the usual process model. Processes can explicitly map shared memory. / 通常拥有独立的虚拟地址空间；也可以显式映射共享内存。 | Threads in one process share its address space and global data; each thread has its own execution state and stack. / 同一进程中的线程共享地址空间和全局数据；每个线程有自己的执行状态和栈。 |
| Communication / 通信 | Uses an explicit boundary such as a pipe, socket, message, or shared mapping. / 通过管道、套接字、消息或共享映射等显式边界通信。 | Can pass references through shared memory, but concurrent access must follow a synchronization rule. / 可通过共享内存传递引用，但并发访问必须遵循同步规则。 |
| Typical choice / 常见选择 | Prefer when a fault or trust boundary matters, or work needs separate process lifetime. / 当故障或信任隔离、独立进程生命周期很重要时考虑使用。 | Prefer when work benefits from shared process state or CPU-parallel execution and the program can manage synchronization. / 当工作需要共享进程状态或 CPU 并行执行，且程序能管理同步时考虑使用。 |

These are useful defaults, not cost or isolation guarantees for every operating system. A process can deliberately share memory or handles; a thread does not automatically make CPU work faster. For Node-specific choices among its event loop, worker threads, and child processes, see [Node.js Fundamentals / Node.js基础](#18.%20How%20does%20Node.js%20schedule%20work%20across%20its%20event%20loop,%20workers,%20and%20processes?%20/%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F).

### Concurrency, parallelism, and I/O / 并发、并行与 I/O

Tasks are **concurrent** when their progress overlaps—for example, a server starts another request while the first waits for a response. They are **parallel** when instructions from both tasks execute at the same instant on separate cores or other processing units. A single event-loop thread can coordinate many waiting I/O operations, but a long synchronous callback still prevents that thread from running other callbacks. CPU parallelism needs another execution resource, such as a worker thread or process.

| I/O style / I/O 方式 | What the caller observes / 调用方观察到的行为 |
| --- | --- |
| Blocking / 阻塞 | The calling thread waits until the operation can make progress or completes. / 调用线程等待操作可以继续或完成。 |
| Non-blocking / 非阻塞 | An attempt returns promptly when it cannot proceed; the caller can wait for readiness or try again. A non-blocking result does not itself mean the full transfer completed. / 暂时无法继续时，调用立即返回；调用方可等待就绪或稍后重试。非阻塞返回本身不表示数据已经全部传输完成。 |
| Asynchronous / 异步 | The caller submits work and receives a later completion or callback. The runtime may use operating-system readiness, a completion facility, or a worker pool. “Async” describes the interface and scheduling relationship, not one universal implementation. / 调用方提交工作，随后接收完成通知或回调。运行时可能使用操作系统就绪通知、完成机制或工作线程池。“异步”描述接口与调度关系，并不对应唯一实现。 |

In Node.js, synchronous filesystem APIs block the event-loop thread. Callback- and promise-based filesystem APIs use libuv's thread pool except `fs.FSWatcher`; many network operations are driven by the operating system. Exact APIs have their own contracts. Async I/O therefore helps waiting workloads, but moving CPU-heavy JavaScript off the event loop requires workers or processes. See the [Event Loop / 事件循环](../../frontend/runtime/event-loop.md) note for scheduling details.

### Races and deadlocks / 竞态与死锁

A **race condition / 竞态** exists when the result depends on the timing or order of operations that access shared state. For example, an increment is a read–modify–write sequence: two workers can both read `10`, compute `11`, then each write `11`, losing one increment. Protect the invariant with a lock, an atomic operation, a single owner that processes messages, or a database constraint—whichever matches the boundary. In JavaScript, synchronous code in one event-loop turn runs to completion, but state can still change between `await` points; worker threads that share a `SharedArrayBuffer` need an explicit synchronization protocol.

A **deadlock / 死锁** occurs when tasks wait in a cycle. If worker A holds lock L1 and waits for L2 while worker B holds L2 and waits for L1, neither can continue. Consistent lock ordering and short critical sections prevent many such cycles. Avoid holding a lock while waiting on network or other unbounded work; a timeout can reveal a stuck wait, but does not by itself restore a partially changed invariant.

### Cancellation and cleanup / 取消与清理

Cancellation is a request to stop work, not proof that work has stopped or that its side effects were undone. Many APIs use cooperative cancellation: code checks a token, stops at a safe boundary, and releases resources or leaves shared state consistent. In POSIX threads, deferred cancellation is the default and takes effect at cancellation points; asynchronous cancellation can interrupt code while it holds a resource. Runtime and API contracts differ, so check whether the operation actually observes cancellation. In particular, cancelling a caller's wait does not retract a request that a remote service already accepted.

### A runnable shared-counter example / 可运行的共享计数示例

The two workers below share one integer. `Atomics.add` makes each read–modify–write increment one synchronized operation; after both workers exit, the expected count is `200000`. Without an atomic operation or another coordination rule, increments can be lost.

~~~javascript
const { Worker, isMainThread, workerData } = require('node:worker_threads');

if (isMainThread) {
  const shared = new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT);
  const workers = Array.from(
    { length: 2 },
    () => new Worker(__filename, { workerData: shared }),
  );

  const waitForExit = worker => new Promise((resolve, reject) => {
    worker.once('error', reject);
    worker.once('exit', code => {
      if (code === 0) resolve();
      else reject(new Error(`worker exited with code ${code}`));
    });
  });

  Promise.all(workers.map(waitForExit)).then(() => {
    console.log(Atomics.load(new Int32Array(shared), 0));
  }).catch(error => {
    console.error(error);
    process.exitCode = 1;
  });
} else {
  const counter = new Int32Array(workerData);
  for (let i = 0; i < 100_000; i++) Atomics.add(counter, 0, 1);
}
~~~

Verified with Node.js v26.11.1; observed output: `200000`. This checks one local runtime example, not performance scaling or every platform's worker implementation.

**Related notes / 相关笔记：** [Node.js Fundamentals / Node.js基础](#18.%20How%20does%20Node.js%20schedule%20work%20across%20its%20event%20loop,%20workers,%20and%20processes?%20/%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F) applies these process and worker boundaries to Node's APIs; [Event Loop / 事件循环](../../frontend/runtime/event-loop.md) explains how queued callbacks make progress on a JavaScript thread.

**Sources / 来源：** POSIX.1-2024 [General Information, process and thread model](https://pubs.opengroup.org/onlinepubs/9799919799/functions/V2_chap02.html); Linux [`pthreads(7)`](https://man7.org/linux/man-pages/man7/pthreads.7.html), for Linux/POSIX thread-sharing and cancellation-point details; Node.js v24 [worker_threads](https://nodejs.org/docs/latest-v24.x/api/worker_threads.html) and [filesystem](https://nodejs.org/docs/latest-v24.x/api/fs.html#threadpool-usage) documentation, checked 2026-10-15. The filesystem docs specify that callback and promise APIs except `fs.FSWatcher` use libuv's thread pool.
## 10. Why are contiguous scans often faster than linked-list walks? / 为什么连续扫描往往比链表遍历快？

Big-O describes how work grows, but data layout and dependency determine how quickly a processor can obtain that work. A contiguous scan often runs efficiently because its addresses are predictable and independent loads can overlap; a linked-list walk has a dependent pointer chain, but a cache miss does not automatically stop every part of the CPU.

复杂度描述工作量如何随输入增长，数据布局与依赖关系则影响处理器能多快拿到数据。连续扫描通常更容易利用预取、并行访存和 SIMD；链表遍历受逐节点地址依赖限制，但一次 Cache Miss 不等于整个 CPU 必然停摆。

~~~mermaid
flowchart LR
    A[Array element i] -->|known address| A2[Adjacent element i+1]
    A2 -->|regular access can prefetch and overlap| A3[Next independent load]
    L[Current list node] -->|load next pointer| P[Wait for pointer value]
    P -->|only then know address| L2[Next list node]
    L -->|cache miss| Other[Independent CPU work may still continue]
~~~

### Key terms / 核心术语

| Term | Meaning |
|---|---|
| **Memory wall / 内存墙** | 处理器计算能力与内存供数能力之间逐渐拉大的差距，涉及延迟与带宽；它不是固定耗时，也不表示所有程序都受内存限制。 |
| **Latency / 延迟** | 从发出一次内存请求到数据可供使用所需的时间。 |
| **Bandwidth / 带宽** | 多个请求充分重叠时，单位时间能传输的数据量。 |
| **Cache line / 缓存行** | 缓存常用的数据传输与一致性维护粒度；具体大小依处理器而定。 |
| **Spatial locality / 空间局部性** | 访问靠近刚访问过地址的数据。一次缓存填充可能带入扫描很快会用到的相邻值。 |
| **Temporal locality / 时间局部性** | 短时间内重复使用同一数据，使它更可能仍留在缓存中。 |
| **Memory-level parallelism (MLP) / 内存级并行度** | 同时处于未完成状态的独立内存请求数量。 |

Wulf 与 McKee 用“内存墙”描述处理器与内存性能差距的扩大。Intel 优化手册提出的实践方向是让访问尽量命中缓存，或隐藏足够多的延迟以利用内存带宽。两者相关但不同：**延迟**限制一条有依赖的访问链；**带宽**限制整体数据吞吐。 [Wulf 与 McKee（1995）](https://doi.org/10.1145/216585.216588)，[Intel® 64 和 IA-32 优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html)。

若一次流式循环平均为每项从内存传输 `s` 字节，可分配给它的有效带宽为 `B`，且循环已受带宽限制，则吞吐上限约为 `B / s` 项每秒。指针依赖链受另一种约束：当前节点到达后才能得知下一地址，因此单条遍历通常无法暴露同等数量的独立请求。这些关系用于识别瓶颈，不是精确耗时公式；缓存命中、计算量、其他请求和具体处理器都会改变结果。

### Why contiguous scans often work well / 连续扫描为什么常常高效

对连续数组区域，下一元素地址可由基址和下标计算。硬件预取器能识别许多规则访问模式；早先的读取尚未完成时，处理器也可能继续发出后续迭代中彼此独立的读取。如果操作、数据类型和编译条件合适，编译器还可用 SIMD 指令并行处理多个值。这些收益都有条件：步长不规则、分支多、指针别名难以排除、指令级并行度不足，或内存带宽已饱和时，预取和向量化都可能帮助有限。[Intel 优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html)、[Arm Cortex-A 系列程序员指南](https://documentation-service.arm.com/static/6893ad23e7f7ce6150e88d37)。

链表遍历要先读取当前节点，再从中得到下一节点地址（`node = node->next`）。在当前节点的链接到达之前，处理器通常不知道下一请求发往哪里。这种**指针追逐 / pointer chasing**形成依赖链，常限制单条遍历可利用的 MLP。普通流式预取器较难从中识别规律；特定设计也可能使用软件预取或专用硬件改善访问。

Cache Miss 仍可与独立工作重叠：支持乱序执行的核心可能先执行无关指令，其他独立读取或线程也可能已有请求在途。当缺失数据位于关键依赖路径上，且没有有用的独立工作可继续时，核心才会因等待而停顿。因此，长串依赖未命中会让链表遍历很慢，但不能推断每次 Miss 都冻结全部执行。Linux 官方文档也提醒，链表局部性较差；若简单数组已能满足需求，链表很少是更好的选择。[Linux：Linked Lists in Linux](https://www.kernel.org/doc/html/latest/core-api/list.html)。

### Complexity is not elapsed time / 复杂度不等于实际耗时

链表插入或删除只有在**已知相关节点或链接**时才是 O(1)。双向链表持有目标节点即可改动有限个指针；单向链表删除目标节点需要前驱，按位置插到某节点之前也需要前驱（除非表示方式另行提供）。按值或下标查找仍是 O(n)。创建节点还会经过分配器并产生内存流量，而复杂度表通常没有计入这些分配与缓存成本。

数组中间插入需要 O(n) 次元素移动，但移动范围连续规则；对适合的类型还可用优化过的批量操作。它是否快于分配链表节点并改写链接，取决于元素大小、移动成本、是否已知链表位置、分配器、数据是否在缓存中以及操作比例。因此，“链表 O(1) 插入总比数组 O(n) 插入快”不能作为普遍结论。

对象池可降低分配开销，也可能让对象更集中，但它不保证链接顺序与内存地址顺序一致。对象复用、插入顺序和池的设计共同决定实际遍历布局。

### Arrays in C, C++, and JavaScript / 各语言中的数组布局

在 C 中，普通数组的元素连续存储，多维数组按行优先布局（最后一维变化最快）；C++ `std::vector<T>`（专门化的 `vector<bool>` 除外）也保证连续存储。JavaScript `Array` 则由带特殊 `length` 行为的索引属性定义；语言规范不保证它采用同样的 C 式元素布局。引擎可以优化常见的稠密数组，具体表示因实现而异。以 V8 为例，它区分 packed 与 holey 等元素类型。[WG14 C23 草案](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3047.pdf)

JavaScript `TypedArray` 更接近数值数据布局：它以固定元素类型，在二进制数据缓冲区上提供数组式视图。但它仍由运行时管理；不能从 C 数组推断普通 JavaScript `Array` 的机器布局或优化方式。[C++ 草案：`vector`](https://eel.is/c++draft/vector)、[ECMAScript 2024：Indexed Collections](https://tc39.es/ecma262/2024/multipage/indexed-collections.html)、[V8：Elements kinds](https://v8.dev/blog/elements-kinds)。

An intrusive list can remove a separately allocated wrapper. Object placement and dependent loads still determine traversal cost. The Linux example explains [why the kernel embeds its list nodes / Linux 内核为何嵌入链表节点](#11.%20Why%20does%20the%20Linux%20kernel%20embed%20list%20nodes%20in%20their%20objects?%20/%20Linux%20%E5%86%85%E6%A0%B8%E4%B8%BA%E4%BB%80%E4%B9%88%E6%8A%8A%E9%93%BE%E8%A1%A8%E8%8A%82%E7%82%B9%E5%B5%8C%E5%85%A5%E5%AF%B9%E8%B1%A1%EF%BC%9F).

### Related performance surprises / 相关的性能反直觉现象

| 场景 | 机制与适用条件；可继续追问 |
|---|---|
| 小规模线性查找与二分 | 小型连续范围可简单顺序扫描；二分比较次数渐进更少，却跳跃访问不同位置。交叉点取决于数据规模、比较成本与缓存状态。实际输入规模和键分布是什么？ |
| 行遍历与列遍历 | 行优先布局中，遍历末维是连续访问；按列走会跨距访问。规则取决于语言及实际布局。循环顺序是否符合存储顺序？ |
| 伪共享 / False sharing | 不同 CPU 写同一一致性缓存行中的不同变量，也会让对方缓存副本失效。需要并发共享且至少一方写入；只有读取不构成此问题。能否用 `perf c2c` 找出争用缓存行？[Linux 伪共享指南](https://docs.kernel.org/kernel-hacking/false-sharing.html) |
| B+ 树与红黑树 | 面向页的 B+ 树在每页容纳多个分隔键，并通过叶页链接支持范围扫描；指针式红黑树通常每节点组织一个键。取舍取决于主要成本是存储页读取、内存缓存未命中还是更新。哪层存储与查询模式主导？[PostgreSQL B-tree 实现](https://www.postgresql.org/docs/current/btree.html) |
| 无分支与分支预测代码 | 去掉分支可能避开误预测，但也可能执行更多工作或引入数据依赖；预测稳定的分支反而更便宜。实际输入分布和生成指令是什么？ |
| 扁平与节点式哈希表 | 扁平表可把元数据与条目密集组织以便分组探测；节点式表更容易保持元素地址稳定，但常增加指针追逐。删除、扩容、负载因子和引用稳定性都重要。[Abseil Swiss Tables 设计](https://abseil.io/about/design/swisstables) |
| 结构体填充 | 对齐要求会插入填充字节并增大对象；字段顺序也可能影响空间，仍受 ABI 与访问模式约束。`sizeof` 与成员偏移是否显示出实际空间问题？ |
| 增加核心数 | 独立工作可扩展，直到共享内存带宽、一致性流量或同步争用成为瓶颈。增加核心后，负载是计算受限、带宽受限还是争用受限？[Intel 优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html)、[Linux 伪共享指南](https://docs.kernel.org/kernel-hacking/false-sharing.html) |

**Related notes / 相关笔记：** [Core Data Structures](#6.%20Which%20data%20structure%20fits%20the%20access%20pattern,%20and%20when%20do%20its%20cost%20bounds%20hold?%20/%20%E5%93%AA%E7%A7%8D%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E9%80%82%E5%90%88%E5%BD%93%E5%89%8D%E8%AE%BF%E9%97%AE%E6%A8%A1%E5%BC%8F%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%95%8C%E4%BD%95%E6%97%B6%E6%88%90%E7%AB%8B%EF%BC%9F) explains tree structure and list-operation bounds; [Practical Data Structure Implementations](#7.%20How%20can%20an%20LRU%20cache%20find%20an%20entry%20and%20update%20recency%20efficiently?%20/%20LRU%20%E7%BC%93%E5%AD%98%E6%80%8E%E6%A0%B7%E9%AB%98%E6%95%88%E6%89%BE%E5%88%B0%E6%9D%A1%E7%9B%AE%E5%B9%B6%E6%9B%B4%E6%96%B0%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F) shows an LRU cache locating a list node through a map before moving that known node.

### Sources / 来源

来源核实日期：**2026-10-16**。处理器手册描述特定架构与实现，不代表所有 CPU 都有相同缓存层次、预取行为、缓存行大小或内存级并行度。

- [Wulf 与 McKee，“Hitting the Memory Wall: Implications of the Obvious”（1995）](https://doi.org/10.1145/216585.216588) — 内存墙术语的提出背景与论述。
- [Intel® 64 和 IA-32 架构优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html) — 隐藏延迟、内存带宽、规则预取模式及特定架构优化。
- [Arm Cortex-A 系列程序员指南，Armv7-A](https://documentation-service.arm.com/static/6893ad23e7f7ce6150e88d37) — 缓存延迟隐藏、hit-under-miss 与乱序执行示例；内容特定于处理器系列，不是所有 Arm 实现的保证。
- [Linux 内核：Linked Lists in Linux](https://www.kernel.org/doc/html/latest/core-api/list.html) 与 [`include/linux/list.h`](https://github.com/torvalds/linux/blob/master/include/linux/list.h) — 循环双向结构、内嵌钩子、`container_of`、删除、安全遍历与并发说明。
- [Linux 内核：False Sharing](https://docs.kernel.org/kernel-hacking/false-sharing.html) — 一致性缓存行机制、成立条件与诊断方法。
- [C++ 草案：`vector`](https://eel.is/c++draft/vector) 和 [`list`](https://eel.is/c++draft/list) — 标准容器保证，以及哪些实现细节不能从标准推断。
- [WG14 C23 草案 N3047](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3047.pdf) — C 数组元素布局与多维数组行优先顺序。
- [GCC libstdc++ `stl_list.h`](https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/bits/stl_list.h) — 一个标准库实现中，链表节点将 `T` 存在自身节点内的对齐存储。
- [ECMAScript 2024：Indexed Collections](https://tc39.es/ecma262/2024/multipage/indexed-collections.html) 与 [V8：Elements kinds](https://v8.dev/blog/elements-kinds) — JavaScript Array 语义、TypedArray 数据缓冲视图，以及一种引擎的实现选择。
- [PostgreSQL：B-tree 索引](https://www.postgresql.org/docs/current/btree.html) 与 [Abseil：Swiss Tables](https://abseil.io/about/design/swisstables) — 页式树与密集哈希元数据的实际例子。
## 11. Why does the Linux kernel embed list nodes in their objects? / Linux 内核为什么把链表节点嵌入对象？

**Short answer / 简答** — An intrusive list embeds its link hook in the object, so generic operations manipulate the hook rather than a separately allocated wrapper. Linux's `struct list_head` stores `next` and `prev` links in a circular doubly linked list whose sentinel points to itself when empty. / **侵入式链表 / intrusive linked list** 把链接钩子直接嵌在被链接的对象里。Linux 的 `struct list_head` 保存 `next` 和 `prev`；通用链表操作直接修改这些钩子，不需要为每个成员关系另分配包装节点。Linux 实现是带哨兵的循环双向链表：空表的 `list_head` 指向自身。

### Recover the containing object / 还原外层对象

`container_of(ptr, type, member)` 可从内嵌钩子指针还原外层对象。概念上，它从钩子地址减去成员相对结构体起点的字节偏移 `offsetof(type, member)`。因此链表操作只需认识通用钩子，调用方再还原具体对象类型。[Linux：Linked Lists in Linux](https://www.kernel.org/doc/html/latest/core-api/list.html)、[Linux `list.h`](https://github.com/torvalds/linux/blob/master/include/linux/list.h)。

Conceptually, `container_of` recovers the enclosing object by subtracting the hook member's `offsetof` byte offset from the hook's address. This makes the link operations generic, but the recovered objects can still form a dependent pointer chain.

### Link ownership and object lifetime / 链接归属与对象生命周期

```c
#include <linux/list.h>
#include <linux/mutex.h>

struct job {
    unsigned long id;
    struct list_head ready_link;
    struct list_head audit_link;
};

static LIST_HEAD(ready_jobs);
static DEFINE_MUTEX(ready_jobs_lock);

/* Initialize both hooks before first insertion. */
static void init_job_links(struct job *job)
{
    INIT_LIST_HEAD(&job->ready_link);
    INIT_LIST_HEAD(&job->audit_link);
}

/* Caller owns job and ensures it is not already on ready_jobs. */
static void enqueue_job(struct job *job)
{
    mutex_lock(&ready_jobs_lock);
    list_add_tail(&job->ready_link, &ready_jobs);
    mutex_unlock(&ready_jobs_lock);
}

/* This iteration uses the same lock as every writer. */
static void inspect_jobs(void)
{
    struct job *job;

    mutex_lock(&ready_jobs_lock);
    list_for_each_entry(job, &ready_jobs, ready_link) {
        /* Use job->id. */
    }
    mutex_unlock(&ready_jobs_lock);
}

/* job must currently be linked; unlinking does not free it. */
static void dequeue_job(struct job *job)
{
    mutex_lock(&ready_jobs_lock);
    list_del_init(&job->ready_link);
    mutex_unlock(&ready_jobs_lock);
}
```

这段是 Linux 内核风格代码，不是可直接用于普通用户态的可移植 C。示例假定处于允许休眠的上下文，且所有访问 `ready_jobs` 的读者和写者都遵循同一互斥锁。一个钩子同一时刻只能挂入一张链表；`ready_link` 和 `audit_link` 是两种独立关系。摘除 `ready_link` 不会释放 `job`；释放对象前还要摘除其他有效钩子，并确保没有引用者或读者继续使用它。Linux 的 `list_for_each_entry_safe` 会预存下一游标，支持遍历时删除当前项；这里的“safe”不提供并发保护。并发访问通常需要锁；读多写少时可使用遵循正确生命周期与宽限期协议的 RCU 链表接口。[Linux 链表文档：删除与并发](https://www.kernel.org/doc/html/latest/core-api/list.html)。

### When does embedding help? / 何时适合把节点嵌入对象？

当已有对象需保持地址稳定、参与一种或多种频繁变化的关系，且减少每种关系额外包装节点有价值时，侵入式链表很实用。它提供通用链接操作，并通过多个钩子表示多个独立关系。但它**不会**让对象在物理内存中连续，也不会消除节点之间的指针依赖，因此不能解决内存墙。

也不要把非侵入式链表一概说成“对象再包一层指针并分配两次”。例如，`std::list<T>` 的容器元素本身就是 `T`；libstdc++ 的 `_List_node<T>` 将 `T` 放在节点内的对齐存储中，不是另分配一个用户对象再套包装节点，也不需要多追一次 `T*`。C++ 标准约束行为和复杂度，并不规定精确节点布局。[C++ 草案：`list`](https://eel.is/c++draft/list)、[GCC libstdc++ `stl_list.h`](https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/bits/stl_list.h)。

Embedding changes ownership and allocation. For traversal cost, see [memory hierarchy and data locality / 内存层次与数据局部性](#10.%20Why%20are%20contiguous%20scans%20often%20faster%20than%20linked-list%20walks?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F).
## 12. How do you reserve the last inventory unit safely? / 如何安全预留最后一个库存？

Read the invariant at the place where concurrent writes meet: update inventory only when availability remains positive, check that exactly one row changed, and create the reservation in the same transaction. A separate read followed by an unconditional write lets two requests act on the same old value. Enforce request identity with a unique constraint so a repeated logical request cannot reserve the same unit twice. / 在并发写入发生的数据库边界检查不变量：只有库存仍大于零时才更新，并确认恰好更新一行，再在同一事务中创建预留。先单独读取、再无条件写入会让两个请求都基于同一个旧值操作。用唯一约束维护请求身份，避免同一逻辑请求重复预留库存。

**Key terms / 关键术语：** conditional update / 条件更新；transaction / 事务；unique constraint / 唯一约束；idempotency key / 幂等键；rollback / 回滚。

~~~mermaid
flowchart TD
    Begin[Begin transaction] --> Update[Conditional update: available > 0]
    Update --> Count{Exactly one row changed?}
    Count -->|yes| Reserve[Insert reservation with unique request ID]
    Reserve --> Commit[Commit both changes]
    Count -->|no| Rollback[Rollback and report unavailable]
    Reserve -->|insert or constraint failure| Rollback
~~~

Assume an inventory table has one row per unique SKU. Do not read the count in the application and then issue an unconditional write: competing requests can both act on the same old value. Let the database perform the condition and decrement as one write:

~~~sql
BEGIN;

UPDATE inventory
SET available = available - 1
WHERE sku = ? AND available > 0;

-- Continue only if exactly one row was updated.
INSERT INTO reservations (request_id, sku) VALUES (?, ?);

COMMIT;
~~~

Continue only if the update changed exactly one row. Insert the reservation under a unique request ID in the same transaction; if no row changed or the insert fails, roll back. This protects the local invariant only under the selected engine's atomic-update and transaction semantics. A unique request constraint also prevents duplicate local reservations. It does not make an external payment or message publish atomic with the database; use a downstream idempotency contract or durable outbox for that boundary.

This example relies on the database transaction and row-update contract. The detailed meaning of isolation, MVCC, and WAL is in [Database transactions, isolation, and recovery / 数据库事务、隔离与恢复](#15.%20What%20do%20transaction%20isolation%20and%20WAL%20guarantee?%20/%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%20WAL%20%E5%88%86%E5%88%AB%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F). For the constraints and indexes used to express invariants and access paths, see [Database constraints and indexes / 数据库约束与索引](#14.%20How%20do%20database%20constraints%20and%20indexes%20shape%20data%20access?%20/%20%E6%95%B0%E6%8D%AE%E5%BA%93%E7%BA%A6%E6%9D%9F%E5%92%8C%E7%B4%A2%E5%BC%95%E5%A6%82%E4%BD%95%E5%A1%91%E9%80%A0%E6%95%B0%E6%8D%AE%E8%AE%BF%E9%97%AE%EF%BC%9F). For examples of how SQL NULL and outer joins affect query results, see [SQL NULLs, joins, and aggregates / SQL NULL、连接与聚合](#13.%20How%20do%20NULLs,%20joins,%20and%20grouping%20change%20SQL%20results?%20/%20NULL%E3%80%81%E8%BF%9E%E6%8E%A5%E4%B8%8E%E5%88%86%E7%BB%84%E4%BC%9A%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%20SQL%20%E6%9F%A5%E8%AF%A2%E7%BB%93%E6%9E%9C%EF%BC%9F).

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) explains how operation keys handle unknown request outcomes; [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#46.%20How%20would%20you%20design%20a%20durable%20account%20report?%20/%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F) applies job-key uniqueness and transactional outbox to asynchronous work.

**Sources and verification / 来源与验证：** PostgreSQL 18 [constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) and [transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html); SQLite [transactions](https://www.sqlite.org/lang_transaction.html) and [foreign keys](https://www.sqlite.org/foreignkeys.html). The conditional reservation transaction was run with Python sqlite3 against SQLite 3.51.0 with foreign-key enforcement enabled. This is evidence for that local SQLite run, not a universal concurrency guarantee.
## 13. How do NULLs, joins, and grouping change SQL results? / NULL、连接与分组会怎样改变 SQL 查询结果？

**How do NULL, outer joins, and grouping change a query result? / NULL、外连接和分组会怎样改变查询结果？** An ordinary comparison such as `=` or `<>` with `NULL` is UNKNOWN; null-aware predicates such as `IS NULL` and `IS DISTINCT FROM` have their own rules. Use `IS NULL` for missing values, and remember that `WHERE` keeps only TRUE. Put a right-side condition in `LEFT JOIN ... ON` when unmatched left rows must remain; a `WHERE` condition can remove those rows. `COUNT(*)` counts joined rows, `COUNT(column)` skips nulls, `WHERE` filters input rows, and `HAVING` filters completed groups. Inspect query plans with the chosen engine and version. / `=` 或 `<>` 这类普通比较遇到 `NULL` 时结果为 UNKNOWN；`IS NULL`、`IS DISTINCT FROM` 等空值判定或相异性谓词有各自的规则。缺失值应使用 `IS NULL`，并记住 `WHERE` 只保留 TRUE。若要保留没有匹配右表记录的左表行，应把右表条件放在 `LEFT JOIN ... ON` 中；放在 `WHERE` 中可能移除这些行。`COUNT(*)` 统计连接后的行数，`COUNT(column)` 跳过空值；`WHERE` 筛选分组前的输入行，`HAVING` 筛选已完成的分组。查询计划应使用所选数据库及其版本来检查。

~~~mermaid
flowchart LR
    Predicate[SQL comparison with NULL] --> Unknown[UNKNOWN]
    Predicate -->|ordinary non-null comparison| TrueFalse[TRUE or FALSE]
    Unknown --> Where[WHERE keeps only TRUE]
    TrueFalse --> Where
    Left[Left-side row] --> On{ON finds a match?}
    On -->|no| NullRow[Null-extended right columns]
    On -->|yes| Joined[Joined row]
    NullRow --> PostWhere{Post-join WHERE is TRUE?}
    Joined --> PostWhere
    PostWhere -->|no: FALSE or UNKNOWN| Drop[Row disappears]
~~~

**Key terms / 关键术语：** NULL / 空值；three-valued logic / 三值逻辑；LEFT JOIN / 左外连接；null-extended row / 空扩展行；aggregate / 聚合；HAVING / 分组筛选。

### SQL result semantics / SQL 查询结果语义

SQL predicates can evaluate to **TRUE, FALSE, or UNKNOWN**. An ordinary comparison such as `=` or `<>` with `NULL` evaluates to UNKNOWN; null-aware predicates such as `IS NULL` and `IS DISTINCT FROM` have their own rules. `WHERE` keeps only rows for which its predicate is TRUE. Use `IS NULL` to test for a missing value; `column = NULL` does not find it. The same rule explains why a right-table filter in `WHERE` can remove the null-extended rows of a `LEFT JOIN`. / SQL 谓词可以得出 **TRUE、FALSE 或 UNKNOWN**。`=` 或 `<>` 这类普通比较遇到 `NULL` 时结果为 UNKNOWN；`IS NULL`、`IS DISTINCT FROM` 等空值判定或相异性谓词有各自的规则。`WHERE` 只保留谓词为 TRUE 的行。用 `IS NULL` 检查缺失值；`column = NULL` 不会查到它。这个规则也解释了为什么 `WHERE` 中的右表筛选条件会移除 `LEFT JOIN` 生成的空扩展行。

Run this compact customer/order dataset in a fresh, separate teaching database/schema; it is independent of the earlier example, which also uses tables named `customers` and `orders` with a different schema. Ben's region and one order amount are `NULL`; Dia has no orders.

~~~sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    amount_cents INTEGER,
    status TEXT NOT NULL
);

INSERT INTO customers VALUES
    (1, 'Ava', 'North'),
    (2, 'Ben', NULL),
    (3, 'Cy', 'South'),
    (4, 'Dia', 'North');

INSERT INTO orders VALUES
    (101, 1, 1200, 'paid'),
    (102, 1, 800, 'pending'),
    (103, 2, NULL, 'paid'),
    (104, 3, 500, 'paid');
~~~

The first query returns no rows because `region = NULL` is UNKNOWN. `IS NULL` returns Ben; `region <> 'North'` returns only Cy because Ben's comparison is UNKNOWN. To include missing regions in that search, say so explicitly with `OR region IS NULL`.

~~~sql
SELECT name FROM customers WHERE region = NULL;
-- no rows

SELECT name FROM customers WHERE region IS NULL ORDER BY customer_id;
-- Ben

SELECT name FROM customers WHERE region <> 'North' ORDER BY customer_id;
-- Cy

SELECT name FROM customers
WHERE region <> 'North' OR region IS NULL
ORDER BY customer_id;
-- Ben
-- Cy
~~~

`LEFT JOIN` first preserves each left-side customer, putting `NULL` in the order columns when no matching order remains. A right-side predicate in `ON` limits which orders count as matches, so Dia is kept. The same predicate in `WHERE` is applied after the join; Dia's null-extended row does not pass `o.status = 'paid'`, so it disappears.

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.customer_id AND o.status = 'paid'
ORDER BY c.customer_id;
-- Ava | 101
-- Ben | 103
-- Cy  | 104
-- Dia | NULL

SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
ORDER BY c.customer_id;
-- Ava | 101
-- Ben | 103
-- Cy  | 104
~~~

`COUNT(*)` counts input rows; `COUNT(column)` counts only rows whose value in that column is not `NULL`. Aggregates such as `SUM` ignore null inputs and return `NULL` when a group has no non-null inputs. The grouped result makes the outer-join detail visible: Dia has one joined row, but no order ID; Ben has an order but no priced order.

~~~sql
SELECT COUNT(*) AS order_rows, COUNT(amount_cents) AS priced_orders
FROM orders;
-- 4 | 3

SELECT c.name,
       COUNT(*) AS joined_rows,
       COUNT(o.order_id) AS orders,
       COUNT(o.amount_cents) AS priced_orders,
       SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY c.customer_id;
-- Ava | 2 | 2 | 2 | 2000
-- Ben | 1 | 1 | 0 | NULL
-- Cy  | 1 | 1 | 1 | 500
-- Dia | 1 | 0 | 0 | NULL
~~~

`WHERE` filters rows before grouping; `HAVING` filters completed groups. This query keeps groups whose non-null total is at least 500 cents. Ben's sum is `NULL`, so the comparison is UNKNOWN and his group is not kept.

~~~sql
SELECT c.name, COUNT(o.order_id) AS orders, SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING SUM(o.amount_cents) >= 500
ORDER BY c.customer_id;
-- Ava | 2 | 2000
-- Cy  | 1 | 500
~~~



These result rules are shared by the examples' SQLite run; optimizer plans are not. Use the selected engine's `EXPLAIN` tool on representative data, and label any plan observation with its engine and version.


**Sources / 来源：** PostgreSQL 18 [SQL tutorial](https://www.postgresql.org/docs/18/tutorial-sql.html), [comparison predicates](https://www.postgresql.org/docs/18/functions-comparison.html), [table expressions and joins](https://www.postgresql.org/docs/18/queries-table-expressions.html), and [aggregate functions](https://www.postgresql.org/docs/18/functions-aggregate.html), checked 2026-10-15; SQLite [SELECT](https://www.sqlite.org/lang_select.html), [expressions](https://www.sqlite.org/lang_expr.html), and [aggregate functions](https://www.sqlite.org/lang_aggfunc.html). The customer/order result queries ran with Python sqlite3 against SQLite 3.51.0 with foreign-key enforcement enabled.
## 14. How do database constraints and indexes shape data access? / 数据库约束和索引如何塑造数据访问？

Constraints enforce durable invariants for every writer, while indexes maintain access paths the planner may choose when their cost is worthwhile. A unique or foreign-key rule protects correctness; an index can speed a representative query but consumes storage and adds write work. Inspect the chosen engine's plan on representative data rather than treating an index definition as a performance promise. / 约束为所有写入方强制执行持久不变量；索引维护执行计划器可能按成本选择的访问路径。唯一约束或外键保护正确性；索引可能加速有代表性的查询，但会占用存储并增加写入成本。应使用真实代表性数据检查所选数据库的计划，不能把创建索引当成性能保证。

**Key terms / 关键术语：** primary key / 主键；unique constraint / 唯一约束；foreign key / 外键；CHECK / 检查约束；B-tree index / B 树索引；query plan / 查询计划；EXPLAIN / 查询计划解释。

~~~mermaid
flowchart LR
    Query[Query and predicates] --> Planner[Database planner]
    Planner --> Estimate[Estimate cost from data and statistics]
    Estimate -->|useful path| Index[Index scan or lookup]
    Estimate -->|not useful| Scan[Table scan or other plan]
    Index --> Result[Rows in requested order]
    Scan --> Result
~~~

### Schema and constraints / 模式与约束

A relational schema defines tables, columns, types, and relationships. A **primary key** identifies a row; a **unique constraint** prevents duplicate key values; a **foreign key** requires a reference to an existing key (subject to the constraint's null and deferral rules); and `NOT NULL` and `CHECK` constrain allowed values. Put durable business invariants in database constraints as well as validating input in the application: another job, script, or service may write the same tables. Referential actions such as `ON DELETE CASCADE` encode an additional lifecycle rule and should match the data relationship.

The following SQL uses common table and constraint syntax. It describes customers and orders, ensures an order has a customer and a non-negative amount, and adds an access path for a customer's recent orders. The query asks for rows; the database decides whether and how to use the index. The `?` is a bound-parameter placeholder used by SQLite; other drivers use their own placeholder notation.

~~~sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    placed_at TEXT NOT NULL
);

CREATE INDEX orders_by_customer_and_time
    ON orders(customer_id, placed_at);

SELECT order_id, amount_cents, placed_at
FROM orders
WHERE customer_id = ?
ORDER BY placed_at DESC;
~~~

An index is a maintained access path, not a promise that every query will be faster. It uses storage and adds work to inserts, updates, and deletes. A multicolumn B-tree index is ordered by its leading columns, so `(customer_id, placed_at)` can support a lookup by customer and then a time ordering; the best plan still depends on the query, table size, data distribution, statistics, and database engine. Inspect a plan with that engine's `EXPLAIN` facility and compare it with representative data. In PostgreSQL, `EXPLAIN ANALYZE` executes the statement and reports observed work, while plain `EXPLAIN` shows the planner's estimated strategy. Plan output and choices are product- and version-specific.


**Sources and verification / 来源与验证：** PostgreSQL 18 [constraints](https://www.postgresql.org/docs/18/ddl-constraints.html), [indexes](https://www.postgresql.org/docs/18/indexes.html), and [EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html), checked 2026-10-15; SQLite [foreign keys](https://www.sqlite.org/foreignkeys.html), [query planner](https://www.sqlite.org/queryplanner.html), and [EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html). The schema/query example was run with Python sqlite3 against SQLite 3.51.0. For 1,000 synthetic orders, adding the composite index changed the observed plan from a table scan plus temporary sort to an index search. This is one planner observation, not a stable output contract.


**Related notes / 相关笔记：** [How do you reserve the last inventory unit safely? / 如何安全预留最后一个库存？](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F) applies a conditional update and a unique request key; [Database transactions, isolation, and recovery / 数据库事务、隔离与恢复](#15.%20What%20do%20transaction%20isolation%20and%20WAL%20guarantee?%20/%20%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E4%B8%8E%20WAL%20%E5%88%86%E5%88%AB%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%9F) explains the transaction boundary.
## 15. What do transaction isolation and WAL guarantee? / 事务隔离与 WAL 分别保证什么？

A database transaction gives statements one commit/rollback boundary. The isolation policy determines which concurrent changes a transaction may observe; MVCC is one way engines manage versions. Write-ahead logging lets recovery redo changes after a crash only within the database's durability and storage assumptions. Point-in-time recovery additionally needs a suitable base backup and required log history. Product, version, and configuration determine the exact guarantee. / 数据库事务为一组语句提供共同的提交或回滚边界；隔离策略定义事务能观察到哪些并发变更，MVCC 是数据库管理版本的一种机制。预写日志支持在崩溃后重做变更，但保证受数据库持久性和存储配置约束。时间点恢复还需要合适的基础备份和所需日志。具体保证取决于产品、版本与配置。

**Key terms / 关键术语：** transaction / 事务；isolation level / 隔离级别；MVCC / 多版本并发控制；write-ahead log (WAL) / 预写日志；crash recovery / 崩溃恢复；point-in-time recovery / 时间点恢复。

~~~mermaid
flowchart LR
    Tx[Transaction changes] --> Log[Append corresponding WAL records]
    Log --> Flush[Flush log under configured durability policy]
    Flush --> Commit[Report commit]
    Commit --> Page[Data pages may be written later]
    Crash[Crash] --> Recovery[Redo durable logged changes]
    Recovery --> Data[Database recovers committed state]
    Backup[Base backup plus archived log range] --> PITR[Point-in-time recovery]
~~~

### Transactions and isolation / 事务与隔离

A transaction gives a set of statements one commit or rollback boundary. **ACID** is a useful vocabulary, with each property still bounded by implementation and configuration:

- **Atomicity / 原子性:** the transaction's changes commit together or are rolled back together.
- **Consistency / 一致性:** constraints and application rules define valid states; the database does not invent the business rules.
- **Isolation / 隔离性:** concurrent transactions see behavior controlled by the isolation level and engine implementation.
- **Durability / 持久性:** a successful commit survives the failures covered by the database's configured durability and storage assumptions.

Consider reserving one remaining unit. Do not read the count in the application and then issue an unconditional write: concurrent requests can both act on the same old value. Prefer one conditional update, check that exactly one row changed, insert the reservation in the same transaction, and roll back if either step fails. The exact concurrency guarantee depends on the engine's atomic-update, locking, and isolation contract; verify it for the selected database.

~~~sql
BEGIN;

UPDATE inventory
SET available = available - 1
WHERE sku = ? AND available > 0;

-- Continue only if exactly one row was updated.
INSERT INTO reservations (request_id, sku) VALUES (?, ?);

COMMIT;
~~~

Assume `inventory.sku` is unique. If the update changes zero rows or the insert fails, roll back instead of committing. This example relies on the database's transaction and row-update semantics; unique constraints can also enforce that a `request_id` is not applied twice. A transaction cannot make a remote side effect atomic with the local database unless both participants share a protocol that provides that guarantee.

SQL isolation names are not a complete description of every engine's behavior. Common anomalies include a **dirty read** (seeing another transaction's uncommitted write), a **non-repeatable read** (seeing a changed row on a later read), a **phantom read** (a repeated predicate query returns a different set), and a **serialization anomaly** (the committed result cannot be explained by any serial ordering). Check the selected product's manual rather than transferring an isolation-level label from another database.

**PostgreSQL 18 example:** the default Read Committed level takes a new snapshot for each statement; Repeatable Read keeps a transaction snapshot and can abort a conflicting update; Serializable detects additional dependency patterns and can abort a transaction that must then be retried from the beginning. These are PostgreSQL behaviors, not universal definitions of those level names.

#### MVCC / 多版本并发控制

With **multi-version concurrency control (MVCC)**, a database keeps versions or visibility metadata so a statement or transaction can read a snapshot while concurrent transactions make changes. This can reduce reader–writer blocking, but does not remove write conflicts, explicit locks, or every wait. Engines that retain row versions need cleanup; PostgreSQL, for example, uses vacuuming to reclaim versions that are no longer visible, and long-running snapshots can delay that cleanup. MVCC is a concurrency-control mechanism, not a promise that all reads are lock-free or that every engine uses the same version rules.

### WAL and recovery boundaries / WAL 与恢复边界

The write-ahead rule is that changes to data pages are written only after the corresponding log records have been flushed to durable storage. A commit can be reported durable after the required log records are safely flushed under the configured policy; a later crash can then use the log to redo changes not yet copied into data pages. Settings that weaken synchronous commit or storage guarantees can weaken what a successful response means. WAL supports crash recovery; point-in-time recovery additionally requires a suitable base backup and the needed archived log range.

Recovery algorithms are product-specific. The archived database course keeps the detailed ARIES analysis, including the Dirty Page Table and its `recLSN` rule, in [Log-based Crash Recovery / 基于日志的崩溃恢复](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md). In ARIES, `recLSN` is the earliest log record that could have dirtied that page since it was last clean; it is not a universal WAL field or redo rule.

### Distributed database boundaries / 分布式数据库的边界

Two nearby concepts are useful boundaries, not a distributed-systems survey:

- **CAP:** during a network partition, a system cannot guarantee both linearizable consistency and an eventual response to every request at a non-failed node. Partition is the assumed failure; the trade-off is which operations may be rejected or may observe stale data. See Gilbert and Lynch's [CAP result](https://www.cs.princeton.edu/courses/archive/spring24/cos418/papers/cap.pdf) and the archived [CAP theorem / CAP 定理](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-distributed-consistency-and-nosql.md) discussion.
- **Two-phase commit (2PC):** a participant that has durably prepared and voted YES must wait for the coordinator's decision. A timeout after YES is not a safe local abort, so the participant can remain blocked until it learns that decision. 2PC coordinates an atomic commit decision; it does not itself provide transaction isolation. See PostgreSQL's [prepared-transaction documentation](https://www.postgresql.org/docs/18/sql-prepare-transaction.html) and the archived [2PC notes](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-two-phase-commit-and-replicated-data.md).

**Course material kept in the archive / 保留在归档中的课程内容：** the detailed RAID calculations, R-tree/spatial-index examples, snapshot-isolation exercises, and recovery derivations remain in [week 1 RAID calculations](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w1-redundancy-and-raid.md), [week 2 R-tree/spatial-index examples](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w2-spatial-indexes.md), [week 3 snapshot-isolation exercises](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w3-optimistic-snapshot-and-timestamp-concurrency.md), and [week 4 recovery derivations](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md). The active note provides the shared model; the course files preserve their derivations and exercises.


**Related notes / 相关笔记：** [How do you reserve the last inventory unit safely? / 如何安全预留最后一个库存？](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F) shows a conditional transaction for a local business invariant; [API timeout and safe retry / API 超时后的结果确认与安全重试](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) explains why a database transaction cannot atomically include an unrelated remote side effect; [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#46.%20How%20would%20you%20design%20a%20durable%20account%20report?%20/%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F) applies an outbox to the database-to-queue boundary.

**Sources / 来源：** PostgreSQL 18 [MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html), [transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [WAL introduction](https://www.postgresql.org/docs/18/wal-intro.html), [WAL configuration and recovery](https://www.postgresql.org/docs/18/wal.html), and [prepared transactions](https://www.postgresql.org/docs/18/sql-prepare-transaction.html), checked 2026-10-15; SQLite [transactions](https://www.sqlite.org/lang_transaction.html). The archived database course retains the detailed ARIES DPT/recLSN derivation and examples: [week 4 recovery](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md). CAP and 2PC are boundaries, not local transaction substitutes: see Gilbert and Lynch's [CAP result](https://www.cs.princeton.edu/courses/archive/spring24/cos418/papers/cap.pdf), PostgreSQL's [prepared transaction documentation](https://www.postgresql.org/docs/18/sql-prepare-transaction.html), and the archived [CAP](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-distributed-consistency-and-nosql.md) and [2PC course notes](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-two-phase-commit-and-replicated-data.md). The original ARIES method is Mohan et al., [ARIES](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging), with DPT and recLSN explained in the [CMU database recovery notes (pp. 1, 4–6)](https://15445.courses.cs.cmu.edu/fall2024/notes/21-recovery.pdf).
## 16. How does a browser request reach an HTTP response? / 浏览器请求如何到达 HTTP 响应？

> **核心解释 / Core idea：** HTTP定义客户端与服务器交换表示、状态和元数据的语义；TCP、QUIC等传输机制决定字节或流如何送达。HTTP版本改变了连接复用与多路复用方式，但不会让请求自动安全、可重试或跨域可读。
> **Core idea:** HTTP defines the semantics for exchanging representations, status, and metadata between clients and servers; transports such as TCP and QUIC determine how bytes or streams are delivered. HTTP versions change connection reuse and multiplexing, but do not by themselves make requests safe to retry or readable across origins.
>
> **面试简答 / Interview answer：** REST是约束式架构风格，HTTP方法语义决定重试边界；HTTP/1.1复用连接，HTTP/2在TCP上多路复用，HTTP/3基于QUIC流，浏览器CORS控制跨源读取。需要新建连接且没有可用地址时才需解析主机名；已有连接可直接复用，无须为每个请求重新查询。HTTPS还需TLS；DNS、连接、TLS与HTTP故障应分层判断。实时更新的协议选择单独见[轮询、SSE、流式Fetch与WebSocket](#17.%20When%20should%20a%20browser%20use%20polling,%20SSE,%20streaming%20Fetch,%20or%20WebSocket?%20/%20%E4%BD%95%E6%97%B6%E9%80%89%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F)。
> **Interview answer:** REST is a constrained style, and HTTP method semantics set retry boundaries. HTTP/1.1 reuses connections, HTTP/2 multiplexes over TCP, and HTTP/3 uses QUIC streams; browser CORS controls cross-origin reads. Resolve the name when a new connection needs an address; an existing usable connection can be reused without a fresh lookup. Apply TLS for HTTPS, and diagnose DNS, connection, TLS, and HTTP failures separately. Choose a live-update transport by direction and request contract; [the comparison note](#17.%20When%20should%20a%20browser%20use%20polling,%20SSE,%20streaming%20Fetch,%20or%20WebSocket?%20/%20%E4%BD%95%E6%97%B6%E9%80%89%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F) explains its recovery limits.

### REST与HTTP方法 / REST and HTTP methods

REST（Representational State Transfer，表述性状态转移）是架构风格，不等同于“把CRUD路径写成名词”。它约束客户端与服务器分离、无状态交互、可缓存响应、统一接口和分层系统等。HTTP API常用URI标识资源，并以方法表达操作；资源表示和状态码共同构成接口语义。[Fielding对REST的原始描述](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm) 与 [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) 分别说明架构约束与HTTP方法语义。

| 方法 Method | 常见用途 Typical use | 安全 Safe | 幂等 Idempotent |
|---|---|---:|---:|
| GET | 读取表示 Retrieve a representation | 是 Yes | 是 Yes |
| POST | 提交处理或创建资源 Submit processing or create a resource | 否 No | 通常否 Usually no |
| PUT | 创建或完整替换目标资源 Create or replace the target resource | 否 No | 是 Yes |
| PATCH | 按补丁文档修改资源 Apply partial modifications | 否 No | 不保证 Not guaranteed |
| DELETE | 删除目标资源 Delete the target resource | 否 No | 是 Yes |

“安全”指请求语义不要求服务器改变目标资源状态，并不表示没有日志、计数等附带效果。“幂等”指重复执行的预期效果等同于执行一次，不要求每次响应完全一样。例如，第一次DELETE可能返回200，之后返回404，但目标资源保持不存在。POST通常不幂等；若业务允许安全重试，API需要额外约定，例如幂等键或可识别的请求标识。[RFC 9110 §9](https://www.rfc-editor.org/rfc/rfc9110.html#section-9) 定义这些方法属性。

PUT表示创建或替换目标资源的状态；服务器可以拒绝不完整或不合规的表示，不能简单总结成“所有缺失字段必然清空”。PATCH携带描述局部修改的补丁文档；是否幂等取决于补丁操作和接口约定。[RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html) 说明PATCH的语义。

~~~http
GET    /posts
POST   /posts
GET    /posts/42
PUT    /posts/42
PATCH  /posts/42
DELETE /posts/42
~~~

不要只凭状态码类别判断能否重试。收到5xx只能说明服务器端或网关报告了错误；如果请求可能已经产生副作用，客户端盲目重发仍会重复操作。根据方法的安全/幂等语义、业务契约以及超时发生阶段作决定。

### HTTP消息、请求头与状态码 / HTTP messages, fields, and status codes

HTTP/1.x（尤其是HTTP/1.1）的文本报文由起始行、字段（常称headers）、空行以及可选消息体组成。[RFC 9112 §2.1](https://www.rfc-editor.org/rfc/rfc9112.html#section-2.1) 规定了这一线格式。HTTP/2和HTTP/3保留HTTP语义，但通过帧和字段块表达消息，并用伪首部承载方法、状态码等控制信息；它们没有HTTP/1.x的文本起始行与空行。[RFC 9113 §8.1](https://www.rfc-editor.org/rfc/rfc9113.html#section-8.1)、[§8.3](https://www.rfc-editor.org/rfc/rfc9113.html#section-8.3)、[RFC 9114 §4.1](https://www.rfc-editor.org/rfc/rfc9114.html#section-4.1)、[§4.3](https://www.rfc-editor.org/rfc/rfc9114.html#section-4.3)。字段传递内容格式、认证信息、缓存策略等元数据。以下是常见字段，具体是否出现取决于客户端、服务器和资源：

| 字段 Field | 常见方向 Direction | 作用 Purpose |
|---|---|---|
| Accept | 请求 Request | 客户端可处理的表示媒体类型 |
| Content-Type | 请求/响应 Request/response | 当前消息体的媒体类型，如application/json |
| Authorization | 请求 Request | 显式提供认证凭据，例如Bearer token |
| Cookie / Set-Cookie | 请求 / 响应 Request / response | 发送已有cookie / 要求浏览器保存或更新cookie |
| Cache-Control | 请求/响应 Request/response | 缓存策略和验证要求 |
| ETag | 响应 Response | 表示版本的验证器，可供条件请求使用 |
| Accept-Encoding | 请求 Request | 客户端支持的内容编码，如gzip、br |
| Accept-Language | 请求 Request | 客户端偏好的自然语言 |
| Content-Length | 请求/响应 Request/response | 在适用的消息中声明消息体长度 |

Cookie常用于保存会话标识，但它本身不是认证协议；服务器根据Cookie值查找会话并执行认证授权。Authorization是应用显式传递凭据的字段。浏览器Fetch不能由脚本手动设置Cookie请求字段，响应中的Set-Cookie也不会暴露给脚本读取；浏览器按cookie规则处理它们。[MDN Cookie字段](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cookie) 与 [MDN Set-Cookie字段](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie) 说明这一区别。

| 状态码范围 | 意义 Meaning | 示例 Examples |
|---|---|---|
| 1xx | 继续处理 Informational | 100 Continue |
| 2xx | 请求成功 Successful | 200 OK、201 Created、204 No Content |
| 3xx | 重定向或使用缓存结果 Redirection or cache validation | 301、302、304 |
| 4xx | 请求存在问题 Client error | 400、401、403、404 |
| 5xx | 服务器未能完成请求 Server error | 500、502、503 |

401表示请求缺少有效认证凭据或需要认证；403表示服务器理解请求但拒绝执行。304 Not Modified是条件GET/HEAD的缓存验证结果，表示客户端可复用已存表示；它不是普通的页面跳转。成功与否也不能只靠Fetch的Promise是否reject来判断：Fetch对404或500仍会兑现Promise，调用方应检查Response的status或ok属性。[MDN Fetch指南](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)。

### 缓存协商 / Cache validation

缓存可减少传输和等待，但必须区分“是否存储”和“使用前是否验证”。Cache-Control: max-age给出新鲜期；no-cache允许存储，但使用前需向源站验证；no-store要求缓存不要存储该响应。它们的语义不能互换。[RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html) 定义HTTP缓存。

常见的ETag协商流程：

1. 响应携带ETag，客户端缓存表示及验证器。
2. 缓存条目过期后，客户端发送If-None-Match并带上该验证器。
3. 若资源未变化，服务器返回304，客户端复用缓存表示；若已变化，服务器返回新表示及其验证器。

协商缓存避免重复传输未变化的内容，但是否允许存储仍由缓存策略和隐私要求决定。不要把no-cache写成“禁止缓存”。

### 浏览器请求API / Browser request APIs

XMLHttpRequest（XHR）仍用于维护旧代码或需要其事件接口的场景，例如上传进度；Fetch是现代浏览器常用的Promise API。两者都需要处理网络失败、取消和HTTP错误等情况。Fetch遇到HTTP 404/500不会自动抛出异常：

~~~javascript
const response = await fetch('/api/data');

if (!response.ok) {
  throw new Error('HTTP ' + response.status);
}

const data = await response.json();
~~~

XHR可以读取状态和响应文本，但应用通常还需自行解析JSON并处理网络错误。Axios是第三方HTTP客户端，常见特性包括响应数据转换、拦截器及可配置的错误判断；它的默认状态码判断通常接受2xx并将其他状态作为错误处理。选择哪种API应服从项目依赖与需求，而不是把某个库的行为误认为HTTP协议保证。[Axios响应结构](https://axios-http.com/docs/res_schema) 与 [Axios错误处理](https://axios-http.com/docs/handling_errors)。

### 网络分层与TCP / Network layers and TCP

OSI七层模型常用于定位概念；实际互联网套件也常按四层概括。不同教材对会话、表示、链路层的归并略有差别，模型是理解工具：

| OSI层 OSI layer | 常见概念 Examples |
|---|---|
| 7 应用 Application | HTTP、DNS、FTP |
| 6 表示 Presentation | 数据表示、编码；TLS常跨越应用与传输边界讨论 |
| 5 会话 Session | 会话管理概念 |
| 4 传输 Transport | TCP、UDP |
| 3 网络 Network | IP、ICMP |
| 2 数据链路 Data link | Ethernet、Wi-Fi链路 |
| 1 物理 Physical | 电缆、无线电信号 |

TCP提供有序、可靠的字节流，不保留应用程序一次write对应一次read的消息边界。应用协议要使用长度前缀、分隔符或固定长度等方式确定消息边界。所谓“粘包”不是TCP把消息粘坏，而是应用误把字节流当作消息队列。

建立连接通常经过SYN、SYN-ACK、ACK三个TCP段；正常关闭时，两个方向分别结束，常见情形会看到FIN与ACK组成的四段交换。但这不是固定的四个报文：ACK与FIN可能合并，双方同时关闭、异常复位等情况也不同。TCP状态与关闭过程见 [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html)。

### DNS名称解析与故障边界 / DNS resolution and failure boundaries

**核心解释 / Core explanation：** DNS把名称映射到资源记录，例如IPv4/IPv6地址。常见路径是客户端的本地解析器先查可用缓存；缓存未命中时，请求递归解析器。递归解析器再从缓存回答，或沿根、顶级域到权威服务器的委派查找记录。记录TTL限制缓存可保留该记录的时间；名称错误也可能被缓存。具体客户端可能命中浏览器/系统缓存、hosts文件或已有连接，因而每次请求不一定都走完整解析路径。

**Core explanation (English):** DNS maps names to records such as IP addresses. A local resolver checks available caches first; on a miss, a recursive resolver may follow referrals from the root through a top-level domain to an authoritative server. A record's TTL limits how long it may be cached, and negative answers may also be cached. Browser or system caches, a hosts file, or an already usable connection can bypass a fresh lookup for a particular request.

**面试简答 / Interview answer：** 先确认名称解析是否给出了可用地址，再按连接建立、TLS握手和HTTP响应分别定位错误。解析器可能返回名称错误或临时错误，也可能在上游无响应时超时；这些都发生在HTTP状态码出现之前。改DNS记录也不会立刻清除所有缓存副本，变更速度受已缓存TTL和解析器策略影响。

在浏览器导航中，缓存、Service Worker和连接复用可能绕过一次新的DNS查询；[Browser Basics / 浏览器基础](../../frontend/browser/browser-basics.md)介绍导航时的整体请求路径。DNS只提供名称解析结果，不负责传输加密；[Web Security and Authentication / Web安全与身份认证](#30.%20How%20do%20you%20prevent%20cross-tenant%20access%20across%20a%20web%20request?%20/%20%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20Web%20%E8%AF%B7%E6%B1%82%E8%B7%A8%E7%A7%9F%E6%88%B7%E8%AE%BF%E9%97%AE%EF%BC%9F)中的TLS说明解释了HTTPS验证服务器并保护传输的边界。

### HTTP/1.1、HTTP/2与HTTP/3 / HTTP versions

| 版本 Version | 连接与多路复用 Connection and multiplexing | 关键边界 Key caveat |
|---|---|---|
| HTTP/1.0 | 通常响应后关闭连接；后来出现Keep-Alive扩展 | 不是现代HTTP/1.1默认持久连接语义 |
| HTTP/1.1 | 默认持久连接，可复用多个请求/响应；同一连接的流水线响应仍按请求顺序返回 | 串行等待或有序响应可能增加延迟；浏览器可使用多个连接 |
| HTTP/2 | 在一个TCP连接上用多个流并发交换帧，使用HPACK压缩字段 | TCP要求字节有序；一个TCP段丢失可能阻塞该连接上尚未交付的数据 |
| HTTP/3 | 在QUIC连接上承载多个HTTP流；QUIC运行在UDP之上并提供可靠流 | 一个流丢失的数据不必阻塞其他流交付，但流仍受共享拥塞控制等连接级影响 |

HTTP/1.1连接默认持久，但持久连接不等于并行响应；RFC规定流水线响应按请求顺序发送。HTTP/2的应用层多路复用减少了每个请求单独占用连接的需要，却无法改变底层TCP有序字节流的传输层队头阻塞。HTTP/3把流建立在QUIC上：QUIC可在一个流丢包时继续交付其他可用流的数据，但仍共享连接的拥塞控制和部分流控资源。[RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html)、[RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html)、[RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html)、[RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)。

HTTP/3使用QUIC而不是“把HTTP直接放在UDP上”：QUIC本身提供连接管理、加密协商和可靠流。会话恢复时可能使用0-RTT数据，但该数据在某些路径上可被重放；有副作用的请求不能仅凭0-RTT就当成安全重试。[RFC 9001](https://www.rfc-editor.org/rfc/rfc9001.html)。

### CORS与浏览器同源策略 / CORS and the same-origin policy

源（origin）由协议、主机和端口共同确定。浏览器的同源策略限制页面读取其他源的响应；CORS（Cross-Origin Resource Sharing，跨源资源共享）让目标服务器通过响应字段声明哪些源可以读取。CORS不是身份认证或CSRF防护机制：符合简单请求条件的跨源请求可能已经发送，只是浏览器不把响应交给页面脚本，因此服务端仍必须验证权限和请求来源。[MDN CORS指南](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)。

~~~http
Access-Control-Allow-Origin: https://app.example
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
Vary: Origin
~~~

浏览器会对不满足CORS safelist的请求先发送OPTIONS预检，询问服务器是否允许目标方法和请求字段；服务器允许后，浏览器才发送实际请求。预检本身不携带凭据。若实际请求需要浏览器凭据，客户端要使用合适的credentials模式，服务端响应必须允许credentials并返回明确的来源，不能用Access-Control-Allow-Origin: *。服务端按Origin动态返回允许来源时，通常还要通过Vary: Origin告知缓存区分响应。

JSONP曾用script标签加载远程JavaScript并调用全局回调，通常限于GET和配合服务端输出；现在应把它看作遗留兼容方案。若前端和后端由同一团队控制，反向代理可以让浏览器请求同源地址，再由服务器转发到上游：

~~~nginx
location /api/ {
  proxy_pass http://backend-server:8080/;
}
~~~


**Related question / 相关问题：** [When should a browser use polling, SSE, streaming Fetch, or WebSocket? / 何时选轮询、SSE、流式 Fetch 或 WebSocket？](#17.%20When%20should%20a%20browser%20use%20polling,%20SSE,%20streaming%20Fetch,%20or%20WebSocket?%20/%20%E4%BD%95%E6%97%B6%E9%80%89%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F) compares live-update transports and disconnect recovery.

### 浏览器资源提示 / Browser resource hints

资源提示让浏览器提前处理可能重要的网络工作。它们是提示，浏览器可根据资源与连接状况调整或忽略：

| 提示 Hint | 用途 Purpose | 典型场景 Typical use |
|---|---|---|
| preload | 提前获取当前页面确定需要的关键资源 | 首屏字体、稍后才被发现的关键图片或脚本 |
| prefetch | 低优先级预取可能用于后续导航的资源 | 预测下一页 |
| dns-prefetch | 提前解析域名 | 后续可能访问的第三方域 |
| preconnect | 提前完成目标源连接准备 | 很快要使用的关键第三方源 |

~~~html
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="prefetch" href="/next-page.js">
<link rel="dns-prefetch" href="//analytics.example">
<link rel="preconnect" href="https://api.example">
~~~

preload应只用于当前页面确实需要的资源，并填写匹配的as类型；字体通常需要crossorigin，以便预加载与CSS字体请求使用一致的CORS模式，避免重复下载。preconnect只适合关键且即将使用的来源，过多提示会消耗连接资源。[web.dev资源提示指南](https://web.dev/learn/performance/resource-hints)。

### 相关主题 / Related notes

- [浏览器基础 / Browser Basics](../../frontend/browser/browser-basics.md)：浏览器的请求、渲染和安全边界。
- [Web安全与身份认证 / Web Security and Authentication](#30.%20How%20do%20you%20prevent%20cross-tenant%20access%20across%20a%20web%20request?%20/%20%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20Web%20%E8%AF%B7%E6%B1%82%E8%B7%A8%E7%A7%9F%E6%88%B7%E8%AE%BF%E9%97%AE%EF%BC%9F)：CORS之外的认证、Cookie与请求保护。
- [实时Web更新 / Real-time Web Updates](#17.%20When%20should%20a%20browser%20use%20polling,%20SSE,%20streaming%20Fetch,%20or%20WebSocket?%20/%20%E4%BD%95%E6%97%B6%E9%80%89%E8%BD%AE%E8%AF%A2%E3%80%81SSE%E3%80%81%E6%B5%81%E5%BC%8F%20Fetch%20%E6%88%96%20WebSocket%EF%BC%9F)：轮询、SSE、流式Fetch与WebSocket的选择和恢复边界。

DNS resolution and TTL behavior were checked against [RFC 1034](https://www.rfc-editor.org/rfc/rfc1034.html) on 2026-10-15.
## 17. When should a browser use polling, SSE, streaming Fetch, or WebSocket? / 何时选轮询、SSE、流式 Fetch 或 WebSocket？

**Core answer / 核心回答：** Choose by message direction, request shape, connection lifetime, and recovery contract. Polling is a series of ordinary HTTP requests; SSE/EventSource provides one-way server events over GET; Fetch streams allow a custom method, headers, body, and cancellation but leave parsing and reconnection to the application; WebSocket supports bidirectional messages and leaves reconnect/replay rules to the application. A reconnect is not recovery unless the server can replay from a retained cursor or the client can query authoritative state. / 根据消息方向、请求形状、连接生命周期和恢复契约选择方式。轮询是一系列普通 HTTP 请求；SSE/EventSource 通过 GET 单向发送服务端事件；Fetch 流允许自定义方法、请求头、请求体和取消信号，但解析和重连由应用负责；WebSocket 支持双向消息，重连和重放规则也由应用定义。若服务端不能按保留游标重放，或客户端不能查询权威状态，重新连接本身不等于恢复。
### WebSocket handshake and bidirectional messages / WebSocket 握手与双向消息

传统浏览器WebSocket使用HTTP/1.1 Upgrade握手：客户端发送Upgrade相关字段，服务器接受后以101 Switching Protocols切换协议；之后双方可在同一TCP连接上主动发送帧，而不再是普通HTTP请求/响应。WebSocket还有跨HTTP/2、HTTP/3的扩展连接方式，分别通过Extended CONNECT和HTTP/3的对应机制承载，因此不应把所有WebSocket描述为HTTP/1.1的TCP升级。[RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)、[RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)、[RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)。

WebSocket握手不是用CORS响应字段授权的Fetch请求。浏览器会带上Origin，服务器应按应用策略验证来源并认证连接；浏览器WebSocket构造器接受URL和可选子协议，不提供任意请求头参数。适用的Cookie可能参与握手，仍受Cookie规则约束。[MDN WebSocket构造器](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/WebSocket)。

Node.js 可用第三方 `ws` 库提供服务，浏览器使用内置 WebSocket API。示例向除发送者之外的已连接客户端广播，保留文本或二进制消息类型，并在连接关闭时清理集合。 [`ws` 广播示例](https://github.com/websockets/ws#server-broadcast)

~~~javascript
const { WebSocketServer, WebSocket } = require('ws');
const server = new WebSocketServer({ port: 3000 });
const clients = new Set();

server.on('connection', (socket) => {
  clients.add(socket);

  socket.on('message', (data, isBinary) => {
    for (const client of clients) {
      if (client !== socket && client.readyState === WebSocket.OPEN) {
        client.send(data, { binary: isBinary });
      }
    }
  });

  socket.on('close', () => clients.delete(socket));
});
~~~

浏览器端：

~~~javascript
const socket = new WebSocket('ws://localhost:3000');

socket.addEventListener('open', () => socket.send('Hello'));
socket.addEventListener('message', (event) => console.log('Received:', event.data));
socket.addEventListener('close', () => console.log('Disconnected'));
~~~

HTTP持久连接（keep-alive）可以在多个HTTP请求/响应间重用连接，但服务器仍需等待请求，不能在没有请求时任意推送HTTP响应。WebSocket提供双方都可发消息的通道；[ws项目文档](https://github.com/websockets/ws)是Node.js服务端实现示例。轮询、SSE和流式Fetch各自使用HTTP请求/响应，适用的方向与恢复能力见下表。

**Key terms / 关键术语：** polling / 轮询；Server-sent Events (SSE) / 服务端事件；EventSource / EventSource 接口；Fetch response stream / Fetch 响应流；WebSocket / WebSocket；replay cursor / 重放游标。

~~~mermaid
flowchart TD
    Direction{Which update direction?}
    Direction -->|occasional or client-controlled| Poll[Polling or long polling]
    Direction -->|server to client only| RequestShape{Need custom method, headers, or body?}
    RequestShape -->|no; GET and simple contract| SSE[SSE with EventSource]
    RequestShape -->|yes| Fetch[Fetch response stream]
    Direction -->|both directions| WS[WebSocket]
    Poll --> Resume[Define cursor, status lookup, or replay]
    SSE --> Resume
    Fetch --> Resume
    WS --> Resume
    Resume --> UI[Client reconstructs authoritative state]
~~~

### 轮询、SSE、流式Fetch与WebSocket / Polling, SSE, streaming Fetch, and WebSocket

| 方式 Transport | 方向与请求契约 Direction and request contract | 连接恢复 Recovery | 适用场景与边界 Fit and boundary |
|---|---|---|---|
| 轮询 Polling | 客户端按间隔发起普通HTTP请求；长轮询会让服务端暂挂一次请求直到有事件或超时。 | 客户端决定频率、退避和何时重试；若需续传，由API定义游标或事件ID。 | 实现简单、适合低频更新；短轮询带来请求开销，长轮询占用等待中的请求。 |
| SSE格式 + `EventSource` API | 服务端向客户端单向发送HTTP `text/event-stream`；EventSource用URL建立GET请求，可选择`withCredentials`。 | EventSource通常会在连接中断后自动重连；服务端可用HTTP 204告知客户端停止重连。带`id:`的事件会在后续重连请求中作为`Last-Event-ID`回传。服务器只有保留可重放的事件历史，才能按该ID续传。 | 适合单向事件；原生EventSource接口没有自定义请求头或请求体，不能把传输断线等同于事件已恢复。 |
| 流式Fetch / Fetch response stream | 一次Fetch请求在响应有body时提供可逐块读取的`Response.body`；请求可使用API允许的方法、请求头、请求体和取消信号。 | Fetch不会替应用实现SSE式自动重连或重放；应用解析协议帧并定义游标、重试和取消策略。 | 需要自定义请求契约或一次性POST后流式返回时合适；字节块不是消息边界。跨源读取仍受CORS约束。 |
| WebSocket | 握手后，客户端和服务端都能沿同一连接发送消息。应用收到的是完整消息，传输层可将一条消息拆成多个帧。 | 重连、身份过期、事件序号、确认和恢复均由应用协议定义。 | 双向低延迟交互合适；长期连接需要连接生命周期管理。浏览器构造器没有任意请求头参数，握手认证要按浏览器可用契约设计。 |

SSE既是`text/event-stream`线格式，也是浏览器EventSource接口的常见后端协议。线格式用UTF-8字段行表示事件，并以空行结束一条事件；常见字段为`event`、`data`、`id`和`retry`。例如：

~~~text
Content-Type: text/event-stream

event: progress
id: 42
data: {"stage":"working"}

~~~

`id`只提供重连游标；它本身不保存事件，也不保证服务器能重放断线期间的数据。EventSource接口只公开URL和凭据选项；当请求需要自定义Authorization头、非GET方法或请求体时，可用Fetch读取同一类流格式，但解析、重试和恢复都由应用实现。Fetch的响应体是`ReadableStream`；一次`read()`得到的块可能切在UTF-8字符或应用事件中间，所以要用增量解码器并按协议帧边界拼装，不要把每个块直接当成一个事件。

~~~javascript
const response = await fetch('/api/events', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ filter }),
  signal,
});
if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);

const reader = response.body.getReader();
const decoder = new TextDecoder();
let endedNormally = false;
let cancelAttempted = false;
try {
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      endedNormally = true;
      break;
    }
    // This parser placeholder returns false when the caller intentionally stops before EOF.
    if (parser.feed(decoder.decode(value, { stream: true })) === false) {
      cancelAttempted = true;
      await reader.cancel();
      break;
    }
  }
  if (endedNormally) parser.feed(decoder.decode());
} catch (error) {
  if (!cancelAttempted) {
    cancelAttempted = true;
    try {
      await reader.cancel(error);
    } catch {
      // Preserve the original parser or read error.
    }
  }
  throw error;
} finally {
  reader.releaseLock();
}
~~~

这里的`parser.feed`代表按已约定的线格式增量解析；示例约定它在调用方已获得所需完整结果、决定提前停止时返回`false`，代码随即取消未读响应体。若解析或读取抛错，也会尝试取消响应流；取消本身若失败，仍保留原始解析/读取错误，并在所有路径释放reader锁。若用户取消操作，传入的`AbortSignal`会取消Fetch。传输层提供请求契约、分块、结束和失败信号，不定义界面如何呈现部分内容，也不保证服务端任务状态能跨重连保留。选择时先回答四件事：消息方向是什么、请求是否要带方法/头/体、连接由谁关闭、恢复是否只需重连还是必须按游标重放。


**Related notes / 相关笔记：** [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#16.%20How%20does%20a%20browser%20request%20reach%20an%20HTTP%20response?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F) covers request methods, caches, CORS, DNS, and transport behavior; [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md) explains how the interface represents partial, reconnecting, cancelled, and terminal states; [AI Application Architecture / AI 应用架构](../../ai-engineering/systems/ai-application-architecture.md) uses persistent run state to recover after a client disconnect.

**Sources / 来源：** [RFC 6455, The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455.html), [RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html), [RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html), [WHATWG HTML Server-sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html), [WHATWG Fetch Standard](https://fetch.spec.whatwg.org/), [WHATWG Streams Standard](https://streams.spec.whatwg.org/), and [WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/) checked 2026-10-15. The SSE reconnection and HTTP 204 boundary was rechecked against the current WHATWG HTML standard on 2026-10-27. See also the MDN [WebSocket constructor](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/WebSocket) and the Node.js [ws implementation](https://github.com/websockets/ws).
## 18. How does Node.js schedule work across its event loop, workers, and processes? / Node.js 如何在事件循环、工作线程与进程之间调度工作？

**Core answer / 核心回答：** Use asynchronous APIs for I/O waits; one event-loop thread runs JavaScript callbacks and a long synchronous callback blocks it. Move CPU-heavy JavaScript to a bounded worker pool, and use child processes when process isolation matters. The choice changes memory sharing, communication, fault boundaries, and shutdown duties. A worker pool also needs a bounded admission policy; see [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F). / I/O 等待通常使用异步 API；JavaScript 回调在事件循环线程上运行，长时间同步回调会阻塞它。CPU 密集型 JavaScript 可交给有界 worker 池；需要进程隔离时可使用子进程。不同选择会改变内存共享、通信、故障边界与关闭责任。

**Key terms / 关键术语：** event loop / 事件循环；isolate / 隔离环境；worker thread / 工作线程；child process / 子进程；cluster / 多进程服务；IPC / 进程间通信。

### What's the difference between a process and a thread?

**进程 / Process** is an operating-system execution boundary with its own virtual address space. **线程 / Thread** is an execution path inside a process; threads can share process memory, so shared mutable data needs coordination.

Node has a JavaScript event-loop thread for each isolate, not one JavaScript thread for the whole machine. A worker thread runs JavaScript in another isolate in the same process. It can exchange messages, transfer an ArrayBuffer, or share a SharedArrayBuffer; shared memory requires explicit synchronization such as Atomics. A child process has a separate process address space and communicates through IPC or other operating-system channels.

Node also uses background mechanisms for asynchronous work: network I/O is commonly driven by the operating system, while selected APIs such as filesystem operations, cryptography, compression, and some name-resolution work use libuv's worker pool. Their JavaScript callbacks run on the event-loop thread. CPU-heavy JavaScript on that thread delays other callbacks.

For the reusable process/thread model of address spaces, shared resources, concurrency, I/O, and cancellation, see [Processes, Threads, and Concurrency / 进程、线程与并发](#9.%20When%20should%20work%20use%20a%20thread,%20process,%20or%20asynchronous%20I/O?%20/%20%E4%BD%95%E6%97%B6%E9%80%89%E7%BA%BF%E7%A8%8B%E3%80%81%E8%BF%9B%E7%A8%8B%E6%88%96%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F); this note applies it to Node's event loop and worker choices.

---

### How do you use multiple CPU cores in Node.js?

Choose based on the work and isolation needed:

- **Worker threads / 工作线程** run CPU-intensive JavaScript in parallel and can communicate by message or shared memory. Use a bounded worker pool for repeated tasks rather than creating one thread per small job.
- **Child processes / 子进程** run in separate process memory and provide stronger isolation; IPC messages are a boundary to account for.
- **Cluster / 多进程服务** starts multiple Node processes that can accept connections on the same server port. It is one deployment option for multi-core servers, not a guarantee of linear throughput scaling or balanced work.

Built-in asynchronous I/O is usually a better choice for I/O-bound work than worker threads. For process or worker choices and shared-state trade-offs, see the linked Node.js API documentation.

An external process manager is optional. PM2 is one choice for starting and observing clustered workers:

~~~bash
pm2 start app.js --name api -i max
pm2 list
pm2 monit
pm2 reload api
~~~

PM2 may fall back from a cluster reload to a restart if it cannot complete it. The application must handle shutdown and drain or close its own work; availability during reload is not guaranteed.

#### Child process example

This compact CommonJS example runs the same file in a child process and sends one task over the fork IPC channel. It is illustrative; production code also needs workload limits, error handling, and shutdown policy.

~~~javascript
const { fork } = require('node:child_process');

if (process.argv[2] === 'worker') {
  process.on('message', ({ n }) => {
    let a = 0;
    let b = 1;
    for (let i = 0; i < n; i++) [a, b] = [b, a + b];
    process.send({ result: a });
  });
} else {
  const child = fork(__filename, ['worker']);
  child.on('message', message => {
    console.log(message.result);
    child.disconnect();
  });
  child.send({ n: 10 });
}
~~~

#### Cluster example

Each worker is a separate process. Restarting workers, health checks, graceful shutdown, and shared session state are application or process-manager responsibilities; the cluster module does not make in-memory state shared.

~~~javascript
const cluster = require('node:cluster');
const http = require('node:http');
const { availableParallelism } = require('node:os');

if (cluster.isPrimary) {
  for (let i = 0; i < availableParallelism(); i++) cluster.fork();
  cluster.on('exit', (worker, code, signal) => {
    console.error('worker exited', worker.id, code, signal);
  });
} else {
  http.createServer((request, response) => {
    response.end('Hello');
  }).listen(8000);
}
~~~

Workers have separate heaps. If a session, cache, or connection map must be shared, choose a deliberate external store, routing strategy, or message-broadcast mechanism. A Redis store is one option, not a universal requirement.

---


**Related questions / 相关问题：** [Node.js event-loop phases and microtasks / Node.js 事件循环阶段与微任务](#19.%20How%20do%20Node.js%20event-loop%20phases%20and%20microtask%20queues%20interact?%20/%20Node.js%20%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E9%98%B6%E6%AE%B5%E4%B8%8E%E5%BE%AE%E4%BB%BB%E5%8A%A1%E9%98%9F%E5%88%97%E5%A6%82%E4%BD%95%E4%BA%A4%E4%BA%92%EF%BC%9F) explains host scheduling; [How do Node.js streams propagate backpressure? / Node.js 流如何传播背压？](#20.%20How%20do%20Node.js%20streams%20propagate%20backpressure?%20/%20Node.js%20%E6%B5%81%E5%A6%82%E4%BD%95%E4%BC%A0%E6%92%AD%E8%83%8C%E5%8E%8B%EF%BC%9F) explains chunk flow and cleanup; [How should a Node.js service drain on shutdown? / Node.js 服务如何排空并关闭？](#21.%20How%20should%20a%20Node.js%20service%20drain%20on%20shutdown?%20/%20Node.js%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E6%8E%92%E7%A9%BA%E5%B9%B6%E5%85%B3%E9%97%AD%EF%BC%9F) covers in-flight work and resource closure; [What does serverless leave to the application? / 无服务器计算仍要求应用负责什么？](#22.%20What%20does%20serverless%20leave%20to%20the%20application?%20/%20%E6%97%A0%E6%9C%8D%E5%8A%A1%E5%99%A8%E8%AE%A1%E7%AE%97%E4%BB%8D%E8%A6%81%E6%B1%82%E5%BA%94%E7%94%A8%E8%B4%9F%E8%B4%A3%E4%BB%80%E4%B9%88%EF%BC%9F) describes provider-managed execution environments.
**Sources / 来源：** Node.js v24 documentation for [worker threads](https://nodejs.org/docs/latest-v24.x/api/worker_threads.html), [child processes](https://nodejs.org/docs/latest-v24.x/api/child_process.html), [cluster](https://nodejs.org/docs/latest-v24.x/api/cluster.html), [filesystem](https://nodejs.org/docs/latest-v24.x/api/fs.html), [crypto](https://nodejs.org/docs/latest-v24.x/api/crypto.html), [zlib](https://nodejs.org/docs/latest-v24.x/api/zlib.html), and [DNS](https://nodejs.org/docs/latest-v24.x/api/dns.html); [PM2 Quick Start](https://pm2.keymetrics.io/docs/usage/quick-start/) and [cluster mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/), checked 2026-10-15.
## 19. How do Node.js event-loop phases and microtask queues interact? / Node.js 事件循环阶段与微任务队列如何交互？

Node runs JavaScript callbacks on an event-loop thread while libuv coordinates timers and I/O through phases. Node's next-tick queue and the Promise/queueMicrotask microtask queue are separate scheduling mechanisms; their order depends on where code runs. Give the Node version and execution context before stating an order. / Node 在事件循环线程上运行 JavaScript 回调，libuv 则通过多个阶段协调计时器和 I/O。Node 的 nextTick 队列与 Promise/queueMicrotask 微任务队列是不同的调度机制，执行上下文会影响它们的先后顺序。说明 Node 版本与执行位置后，再给出顺序规则。

**Key terms / 关键术语：** event-loop phase / 事件循环阶段；poll / 轮询阶段；microtask / 微任务；process.nextTick / nextTick 队列；CommonJS / CommonJS 模块；ES module / ES 模块；timer threshold / 计时器阈值。

~~~mermaid
    subgraph loop[libuv event-loop phases]
        Timers[Timers] --> Pending[Pending callbacks]
        Pending --> Poll[Poll: I/O]
        Poll --> Check[Check: setImmediate]
        Check --> Close[Close callbacks]
        Close --> Timers
    end
    Operation[Current JavaScript operation completes] --> Tick[Node drains nextTick queue]
    Tick --> Micro[Node drains microtask queue]
    Micro --> LoopNext[Event loop continues]
~~~

The diagram is a simplified loop outline. The idle and prepare phases are internal. A JavaScript operation's completion handling occurs around the loop and is not itself another libuv phase. ES module evaluation already runs within microtask processing, which explains why the top-level CommonJS and ES module examples below differ.

### What the event-loop phases do / 事件循环阶段各自做什么

| Phase | Main role |
|---|---|
| Timers | Run timer callbacks once their minimum delay threshold has passed; the requested delay is not an exact deadline. |
| Pending callbacks | Run certain I/O callbacks deferred from an earlier loop iteration. |
| Poll | Retrieve and process I/O events; it may wait for I/O when appropriate. |
| Check | Run callbacks scheduled with setImmediate. |
| Close callbacks | Run selected close events, such as a socket close after abrupt destruction. |
| Idle and prepare | Internal libuv phases. |

In libuv 1.45.0, used by Node.js 20 and later, timers run after poll on each loop iteration; earlier versions also ran timers before poll. This changes some timer/immediate timing relationships. At top level, do not rely on a fixed order between setTimeout(fn, 0) and setImmediate(fn). Inside an I/O callback, setImmediate runs in the check phase after poll; the official guide describes it as running before the timer in that situation.

~~~javascript
const fs = require('node:fs');

// At top level, the order can vary.
setTimeout(() => console.log('timeout'), 0);
setImmediate(() => console.log('immediate'));

// Inside an I/O callback, setImmediate runs in the check phase.
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timer after I/O'), 0);
  setImmediate(() => console.log('immediate after I/O'));
});
~~~

### How do nextTick and microtasks differ by module context? / nextTick 与微任务顺序如何受模块上下文影响？

The nextTick queue is drained after the current JavaScript operation finishes and before the event loop continues. Promise handlers and queueMicrotask callbacks use the microtask queue. In CommonJS top-level execution, nextTick callbacks run before Promise/queueMicrotask callbacks. ES module evaluation itself runs as microtask work, so its top-level Promise/queueMicrotask callbacks run before nextTick callbacks.

| Context | Ordering for the calls below |
|---|---|
| CommonJS top level | process.nextTick, Promise reaction, queueMicrotask |
| ES module top level | Promise reaction, queueMicrotask, process.nextTick |

~~~javascript
// Save as example.cjs
const { nextTick } = require('node:process');

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
// Checked output on Node.js v26.11.1:
// nextTick
// promise
// microtask
~~~

~~~javascript
// Save as example.mjs
import { nextTick } from 'node:process';

Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
// Checked output on Node.js v26.11.1:
// promise
// microtask
// nextTick
~~~

Current Node.js documentation marks process.nextTick as Legacy and recommends queueMicrotask for most userland deferrals. A recursively replenished nextTick queue can starve I/O because the loop cannot reach poll until the queue drains. Keep nextTick only when its particular scheduling boundary is required by existing API behavior.

One historical use is making a callback-based API consistently asynchronous, including validation errors, so the caller can finish setting up state before the callback runs. Another is emitting a readiness event on the next tick so callers can register a listener after construction:

~~~javascript
const { EventEmitter } = require('node:events');

function createEmitter() {
  const emitter = new EventEmitter();
  process.nextTick(() => emitter.emit('ready'));
  return emitter;
}

const emitter = createEmitter();
emitter.on('ready', () => console.log('ready'));
~~~

Use queueMicrotask for ordinary portable deferral unless the API depends on nextTick-specific ordering. These rules describe Node's host queues; they do not define browser scheduling. [Asynchronous JavaScript / 异步 JavaScript](../../frontend/javascript/asynchronous-javascript.md) covers Promise behavior outside Node's host phases.

**Related notes / 相关笔记：** [Node.js scheduling and worker choices / Node.js 调度与 worker 选择](#18.%20How%20does%20Node.js%20schedule%20work%20across%20its%20event%20loop,%20workers,%20and%20processes?%20/%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F) applies these host queues to server workloads; [Processes, Threads, and Concurrency / 进程、线程与并发](#9.%20When%20should%20work%20use%20a%20thread,%20process,%20or%20asynchronous%20I/O?%20/%20%E4%BD%95%E6%97%B6%E9%80%89%E7%BA%BF%E7%A8%8B%E3%80%81%E8%BF%9B%E7%A8%8B%E6%88%96%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F) explains the execution resources used for CPU work.

**Sources / 来源：** [Node.js event-loop phases and timer behavior](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick) and [Node.js v26 process.nextTick / queueMicrotask guidance](https://nodejs.org/api/process.html#when-to-use-queuemicrotask-vs-processnexttick), checked 2026-11-05. The CJS and ESM output examples were checked on Node.js v26.11.1; the libuv timer phase change is documented for libuv 1.45.0 (Node.js 20).
## 20. How do Node.js streams propagate backpressure? / Node.js 流如何传播背压？

**核心解释 / Core explanation：** A stream moves data in chunks from a producer to a consumer. A `Readable` supplies chunks; a `Writable` accepts them; a `Transform` reads and writes while changing them; a `Duplex` does both. When `writable.write(chunk)` returns `false`, stop producing until `'drain'` says writing can resume. `pipeline()` connects stages and propagates a slow consumer's backpressure upstream.

**中文说明：** 流按数据块从生产者流向消费者；`write()` 返回 `false` 时，生产者应暂停并等待 `'drain'` 再继续。`pipeline()` 会把下游变慢的背压传回上游。`highWaterMark` 是暂停阈值而非内存上限；单个大数据块、各阶段缓冲和链路外队列仍可能增加内存。读取端的 `'end'` 表示输入结束，写入端的 `'finish'` 表示 `end()` 后已处理已接收写入；`'close'` 表示资源关闭，`'error'` 表示失败。`destroy()` 用于中止或失败，额外拥有的游标等资源应在 `finally` 中释放；写入完成也不代表远端应用已处理数据或文件已持久化。

**Key terms / 关键术语：** Readable / 可读流；Writable / 可写流；Transform / 转换流；backpressure / 背压；highWaterMark / 暂停阈值；pipeline / 流水线。

~~~mermaid
    Source[Readable source] --> Transform[Transform stages]
    Transform --> Sink[Writable destination]
    Sink -->|write returns false| Pause[Pause the producer]
    Pause -->|drain| Sink
    Pause -->|pipeline propagates backpressure| Transform
~~~

**面试简答 / Interview answer：** If `write()` returns `false`, stop calling it until `'drain'`; continuing to submit chunks can grow the writable's queue and memory use. Use `pipeline()` for a source/transform/destination chain, or wait for `'drain'` in a manual producer. `highWaterMark` is a pause threshold, not a hard memory cap; a large chunk, transform buffers, or queues outside the pipeline can still use more memory.

~~~javascript
const { createWriteStream } = require('node:fs');
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');
const { createGzip } = require('node:zlib');

async function* rows() {
  for (let id = 1; id <= 10_000; id++) yield { id };
}

async function exportRows(signal) {
  const lines = (async function* () {
    for await (const row of rows()) yield `${JSON.stringify(row)}\n`;
  })();

  await pipeline(
    Readable.from(lines),
    createGzip(),
    createWriteStream('rows.ndjson.gz', { highWaterMark: 32 * 1024 }),
    { signal }
  );
}

const controller = new AbortController();
// The owner can call controller.abort(reason) to cancel the export.
exportRows(controller.signal).catch((error) => {
  console.error('export failed:', error.message);
});
~~~

Here the async generator produces one row at a time, and `pipeline()` resolves after the output finishes. If a stage errors or the signal aborts, the promise rejects and the pipeline destroys its participating streams. A producer that owns an extra resource, such as a database cursor, should release it in `finally`; pipeline cleanup cannot close resources hidden outside its stages. For manual writes, the same rule is `if (!writable.write(chunk)) await once(writable, 'drain')`.

The terminal signals describe different outcomes: a readable `'end'` means no more input chunks remain; a writable `'finish'` means its accepted writes have completed after `end()`; `'close'` reports resource closure when that stream emits it; `'error'` reports failure. Use `destroy(error)` to abort or fail a stream, not as a synonym for successful end-of-input. A writable finishing does not prove that a remote application processed the bytes or that a file is durable on storage.


**Sources / 来源：** The stream example and lifecycle behavior were checked against the version-pinned [Node.js v26.11.1 stream documentation](https://nodejs.org/download/release/v26.11.1/docs/api/stream.html) on 2026-10-15. This version boundary matters for code and API behavior; the conceptual backpressure rule is not a memory cap.

**Related notes / 相关笔记：** [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) applies the same bounded-work rule to requests, worker slots, and durable queues.
## 21. How should a Node.js service drain on shutdown? / Node.js 服务如何排空并关闭？

Graceful shutdown is an application lifecycle, not something the event loop or HTTP server performs for every dependency. On a shutdown signal, mark the instance unready and have each request handler reject work before enqueueing it; this also catches requests on already-open keep-alive connections. Then stop accepting connections, let tracked handlers and response streams finish, cancel work at the deadline, and close pools, workers, timers, and other owned resources after their users have stopped. Pass `workAbort.signal` to cancellable handlers and track accepted work so `waitForInFlightWork()` has a real completion condition.

**核心解释（中文）：** 收到关闭信号后先摘除就绪并拒绝新任务，再停止接入、等待已接收请求和后台工作排空；到期后发出协作取消并强制关闭 HTTP 连接。服务端关闭与跟踪任务都结算后，再回收它们使用的资源；即使其中一项失败，也要完成清理并报告错误，且在生命周期和清理报告结束前保留截止计时器。

**Key terms / 关键术语：** readiness / 就绪状态；in-flight work / 在途工作；graceful shutdown / 优雅关闭；deadline / 截止时间；cooperative cancellation / 协作式取消；owned resources / 应用拥有的资源。

~~~mermaid
    [*] --> Ready
    Ready --> Draining: SIGTERM; mark unready
    Draining --> Waiting: stop accepting new connections
    Waiting --> Closed: in-flight work and server close
    Waiting --> Deadline: deadline expires
    Deadline --> Cancel: abort cooperative work
    Cancel --> ForceClose: close remaining HTTP connections
    Closed --> Cleanup: release owned resources
    ForceClose --> Cleanup
    Cleanup --> [*]
~~~

~~~javascript
const workAbort = new AbortController();
let draining = false;

function rejectWhileDraining(res) {
  if (!draining) return false;
  res.writeHead(503, { Connection: 'close' });
  res.end();
  return true;
}
// Call first in each request handler: if (rejectWhileDraining(res)) return;

async function shutdown() {
  draining = true;
  markReadiness(false);

  const deadline = setTimeout(() => {
    workAbort.abort(new Error('shutdown deadline'));
    server.closeAllConnections();
  }, 10_000);

  const serverClosed = new Promise((resolve, reject) => {
    server.close((error) => error ? reject(error) : resolve());
  });

  try {
    const lifecycle = await Promise.allSettled([
      serverClosed,
      waitForInFlightWork(),
    ]);
    const lifecycleFailures = lifecycle.filter((result) => result.status === 'rejected');

    let cleanupFailure;
    let cleanupFailed = false;
    try {
      await closeOwnedResources();
    } catch (error) {
      cleanupFailed = true;
      cleanupFailure = error;
    }

    for (const { reason } of lifecycleFailures) {
      console.error('shutdown lifecycle failed:', reason);
      process.exitCode = 1;
    }
    if (cleanupFailed) {
      console.error('resource cleanup failed:', cleanupFailure);
      process.exitCode = 1;
    }
  } finally {
    clearTimeout(deadline);
  }
}

process.once('SIGTERM', () => {
  void shutdown().catch((error) => {
    console.error('shutdown failed:', error);
    process.exitCode = 1;
  });
});
~~~

`markReadiness`, `waitForInFlightWork`, and `closeOwnedResources` stand for application-owned health, task, and resource hooks. `waitForInFlightWork()` must settle only after tracked work has stopped using its dependencies; a rejection reports failed work, not permission to clean up while that work still runs. The referenced deadline timer stays active while `Promise.allSettled()` awaits both server close and tracked work, and the code still attempts owned-resource cleanup before reporting lifecycle or cleanup failures. Keep the timer referenced until it fires or shutdown cleanup finishes; `unref()` would allow Node to exit before its callback when no other handle keeps the event loop active. `server.close()` stops new connections and, in Node.js 26.11.1, closes idle connections while waiting for the rest. `closeAllConnections()` is the deadline's forceful HTTP(S) fallback; call it after `server.close()` as shown, and close upgraded WebSocket or HTTP/2 sessions through their own owners. The task abort is cooperative: if a handler ignores its signal or another handle keeps the process alive, the service supervisor must enforce the final hard stop. A signal listener also replaces Node's default signal exit behavior on supported POSIX systems, so the handler must complete or deliberately set a failure exit code.


**Sources / 来源：** The shutdown example and lifecycle behavior were checked against [Node.js v26.11.1 HTTP](https://nodejs.org/download/release/v26.11.1/docs/api/http.html) and [process](https://nodejs.org/download/release/v26.11.1/docs/api/process.html) documentation on 2026-10-15. The timer-reference behavior uses [Node.js v26.12.1 timers](https://nodejs.org/api/timers.html), checked 2026-10-27.

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) explains cancellation and ambiguous remote outcomes; [Queue delivery acknowledgements / 队列确认与重投](#38.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) explains why a consumer acknowledges only after its chosen durable boundary.
## 22. What does serverless leave to the application? / 无服务器计算仍要求应用负责什么？

Serverless lets a provider manage execution infrastructure through a function or managed runtime interface; servers still exist. The application still owns durable state, idempotency, resource cleanup, and correctness across retries. Limits, concurrency, billing, cold starts, and environment reuse depend on the selected provider and configuration. / 无服务器计算让服务商通过函数或托管运行时管理执行基础设施，但服务器仍然存在。应用仍需负责持久状态、幂等性、资源清理和跨重试的正确性。限制、并发、计费、冷启动与环境复用取决于具体服务商和配置。

**Key terms / 关键术语：** serverless / 无服务器计算；execution environment / 执行环境；cold start / 冷启动；ephemeral state / 临时状态。

### Provider-managed execution boundary / 服务商管理的执行边界

Timeouts, concurrency limits, billing, cold-start latency, and state-reuse behavior depend on the provider, product, runtime, region, and configuration. Do not treat in-memory state as durable or assume an execution environment is discarded after every invocation. For example, AWS Lambda documents that environments can be reused while advising applications to treat state as temporary and persist durable changes externally.

Serverless can suit event-triggered handlers or variable workloads when the provider's limits and cost model fit. Long-running work, persistent connections, predictable latency, and vendor-specific integrations require a comparison against other deployment models.

**Related notes / 相关笔记：** [Node.js runtime choices / Node.js 运行时选择](#18.%20How%20does%20Node.js%20schedule%20work%20across%20its%20event%20loop,%20workers,%20and%20processes?%20/%20Node.js%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E3%80%81%E5%B7%A5%E4%BD%9C%E7%BA%BF%E7%A8%8B%E4%B8%8E%E8%BF%9B%E7%A8%8B%E4%B9%8B%E9%97%B4%E8%B0%83%E5%BA%A6%E5%B7%A5%E4%BD%9C%EF%BC%9F) covers worker and process boundaries; [API timeout and safe retry / API 超时后的结果确认与安全重试](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) covers durable operation state and idempotent retries.

**Sources / 来源：** AWS Lambda [execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) and [application design](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html), checked 2026-10-15. Provider limits and runtime behavior change over time.
## 23. How do Python values, iterators, and resource lifetimes behave? / Python 的值、迭代器与资源生命周期如何工作？

**Core model / 核心模型：** Python names are bindings to objects. A collection may be changed in place or a name may be rebound to another object; those are different operations. Function defaults are evaluated when the function is defined, iterators produce values as they are requested, and context managers define cleanup around a block. Type hints describe intent to static tools but do not validate runtime input. A virtual environment separates a project's installed packages from other environments. / Python 名称绑定到对象。集合可以被原地修改，名称也可以重新绑定到另一个对象，这是两种不同操作。函数默认值在函数定义时求值，迭代器按需产生值，上下文管理器则为代码块定义资源清理。类型提示表达意图并帮助静态工具检查，但不会在运行时验证输入。虚拟环境将项目安装的包与其他环境隔离。

~~~mermaid
flowchart LR
    File[CSV file] --> Iterator[Generator reads one row at a time]
    Iterator -->|valid row| Yield[Yield row to consumer]
    Iterator -->|later malformed row| Error[Raise parsing error]
    Error --> Unwind[Exception unwinds nested with blocks]
    Unwind --> Close[Close file and remove temporary directory]
    Yield --> Partial[Earlier output may already have escaped]
~~~

**Key terms / 关键术语：** object / 对象；name binding / 名称绑定；mutable / 可变；immutable / 不可变；alias / 别名；shallow copy / 浅拷贝；default argument / 默认参数；iterable / 可迭代对象；iterator / 迭代器；generator / 生成器；exception / 异常；context manager / 上下文管理器；type hint / 类型提示；virtual environment / 虚拟环境。

### Collections and object references / 集合与对象引用

Lists and dictionaries are mutable: an operation such as `append` or item assignment changes that object. Strings and tuples are immutable. A tuple cannot have its slots replaced, although it can still contain a mutable object whose value changes. Sets keep unique elements and do not provide sequence indexing; dictionaries map keys to values and preserve insertion order in Python 3.7 and later.

A name does not contain a separate copy of the value. Assignment binds the name to an object, so two names can refer to the same mutable object. Mutating through either name is visible through the other. Rebinding one name changes only that name's binding. A shallow copy creates a new outer container while keeping references to nested objects; use a deeper copy or explicit reconstruction only when the nested values also need independent ownership.

~~~python
event = {"id": "evt-1", "tags": ["new"]}
alias = event
alias["tags"].append("priority")
print(event["tags"])  # ['new', 'priority']

outer_copy = event.copy()
outer_copy["id"] = "evt-copy"  # a different outer dictionary
outer_copy["tags"].append("shared")  # the nested list is still shared
print(event["tags"])  # ['new', 'priority', 'shared']

alias = {"id": "evt-2", "tags": []}  # only alias is rebound
print(event["id"])  # evt-1
~~~

### Calls, argument binding, and defaults / 调用、参数绑定与默认值

At a call, Python binds supplied argument values to parameters by position or keyword. A parameter receives a reference to the supplied object; the call does not copy a mutable argument. Mutating that object inside a function can therefore be observed by the caller, while assigning a new object to the local parameter only rebinds that local name.

Default expressions are evaluated once when Python executes the `def` statement. If the default is a list or dictionary and the function mutates it, later calls reuse that same object. Use `None` when it means “no value supplied,” then create per-call state inside the function. If `None` itself is a meaningful input, choose a separate sentinel.

~~~python
def unsafe_add(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

print(unsafe_add("first"))   # ['first']
print(unsafe_add("second"))  # ['first', 'second'] — same default list

def add(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items

print(add("first"))   # ['first']
print(add("second"))  # ['second']
~~~

### Iteration and generators / 迭代与生成器

An **iterable** can supply an iterator. An **iterator** returns its next value on request and signals completion with `StopIteration`; a `for` loop handles that protocol. A generator function uses `yield` to produce an iterator whose local state resumes at the next request. This lets a pipeline process one item at a time instead of first building a complete result list. The work, and any exception raised by that work, happens as the consumer advances the generator. A generator is usually one-pass; materializing it with `list(...)` consumes it and stores all produced values.

~~~python
from collections.abc import Iterable, Iterator

def ready_rows(rows: Iterable[dict[str, str]]) -> Iterator[dict[str, str]]:
    for row in rows:
        if row["status"] == "ready":
            yield row
~~~

Streaming reduces intermediate storage and can begin output early, but it does not make a whole operation atomic. If a later row is invalid, earlier rows may already have been emitted or acted on. Validate or stage first when the operation requires all-or-nothing effects.

### Exceptions and context managers / 异常与上下文管理器

Exceptions report that an operation could not complete normally. Catch one where the program can recover, translate it into a useful boundary error, or add context and re-raise it with `raise ... from error`. Avoid swallowing an exception when the caller still needs to know that work failed.

A context manager pairs setup and cleanup around a block. Once `__enter__` completes successfully, `__exit__` is called when the block ends, including when an exception leaves the block. A context manager may intentionally suppress an exception; ordinary file context managers close the file and allow the original error to continue. This is why file and temporary-directory lifetimes should be explicit rather than left to garbage collection.

### What type hints do and do not do / 类型提示的作用与边界

Annotations give readers and static analyzers a shared description of expected values and returns. A type checker can report a mismatch before execution, and an editor can use the information for navigation and completion. Python does not automatically reject a value because it conflicts with an annotation; data read from a file, database, or network still needs parsing and validation at that boundary. Runtime validation requires an explicit check or a library designed to perform it.

~~~python
def declared_integer() -> int:
    return "still a string"

print(declared_integer())  # Python returns the string; a type checker can flag it
~~~

### A small file-processing example / 小型文件处理示例

Save this as `python-fundamentals-example.py`. It filters synthetic CSV rows lazily, copies each selected row before adding a tag, and uses nested context managers to close the file and remove the temporary directory even if parsing raises an exception.

~~~python
import csv
from collections.abc import Iterable, Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

Row = dict[str, str]


def ready_rows(rows: Iterable[Row]) -> Iterator[Row]:
    for line_number, row in enumerate(rows, start=2):  # line 1 is the header
        try:
            status = row["status"]
            count = int(row["count"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"CSV row {line_number}: status and integer count are required"
            ) from error

        if status == "ready" and count > 0:
            yield row


def add_tag(row: Row, tag: str = "reviewed") -> Row:
    enriched = row.copy()  # a shallow copy is enough because values are strings
    enriched["tag"] = tag
    return enriched


CSV_TEXT = """id,status,count
evt-1,ready,3
evt-2,queued,1
evt-3,ready,nope
"""


def main() -> None:
    try:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.csv"
            path.write_text(CSV_TEXT, encoding="utf-8")

            with path.open(encoding="utf-8", newline="") as source:
                for row in ready_rows(csv.DictReader(source)):
                    print(add_tag(row))
    except ValueError as error:
        print(f"Rejected input: {error}")


if __name__ == "__main__":
    main()
~~~

Expected output:

~~~text
{'id': 'evt-1', 'status': 'ready', 'count': '3', 'tag': 'reviewed'}
Rejected input: CSV row 4: status and integer count are required
~~~

The first row is yielded before the generator reaches the malformed fourth CSV line. The example catches the parsing error outside both `with` blocks, so the file and temporary directory still close during exception unwinding. A real application that writes results to a database or calls a remote service must decide whether partial progress is acceptable and use a transaction or staging boundary when it is not.

### Language behavior, implementations, and versions / 语言语义、实现与版本

The examples use Python 3.11 syntax and the language behavior documented for Python 3.11. Names, mutability, default evaluation, iteration, and `with` cleanup are language/runtime contracts; they do not depend on CPython's internal object layout. Other details can be implementation-specific or change between Python versions. For example, dictionary insertion order is a language guarantee from Python 3.7; CPython 3.6 preserved it as an implementation detail. In CPython, `id(obj)` currently represents an object's memory address, but code should not treat an identity value as a durable identifier. Check the target interpreter and minimum supported version before relying on newer syntax or runtime behavior.

### Isolated environment and run command / 隔离环境与运行命令

A virtual environment gives a project its own package installation area; it does not install or pin the Python interpreter itself. Select the intended interpreter when creating the environment, and use that environment's Python to invoke `pip` so package installation and execution target the same environment. Declare third-party requirements in the project's packaging or dependency files. A dependency-free example needs no installation step.

On POSIX, from the directory containing the saved example, create an environment and run it with:

~~~sh
python3.11 -m venv .venv && .venv/bin/python python-fundamentals-example.py
~~~

For a project with a `requirements.txt`, install its declared packages with `.venv/bin/python -m pip install -r requirements.txt` before running the script. A virtual environment isolates packages, while repeatability still depends on selecting a compatible Python version and recording the project's dependency versions and platform requirements.

**Verified run / 运行验证：** The file-processing example ran with CPython 3.11.13 and printed the expected output above. This verifies the example on that interpreter; it is not a claim that every Python implementation or platform has identical implementation details.

**Related notes / 相关笔记：** [API Reliability and Asynchronous Delivery / API可靠性与异步交付](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) explains timeouts, cancellation, and safe retries. [Capacity and backpressure](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) covers bounded work.
Python-specific coroutine and framework behavior is explained in [Python Async and FastAPI Request Lifecycle / Python异步与FastAPI请求生命周期](#24.%20Why%20can%20an%20async%20FastAPI%20endpoint%20still%20block?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%E5%BC%82%E6%AD%A5%20FastAPI%20%E6%8E%A5%E5%8F%A3%E4%BB%8D%E4%BC%9A%E9%98%BB%E5%A1%9E%EF%BC%9F).
Application-level request, response, error, and pagination contracts are covered in [HTTP API Contracts / HTTP API契约](#26.%20How%20do%20you%20design%20a%20predictable%20HTTP%20API%20contract?%20/%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F).

**Sources / 来源：** Python 3.11 [Tutorial](https://docs.python.org/3.11/tutorial/) and [Language Reference](https://docs.python.org/3.11/reference/), including [objects and types](https://docs.python.org/3.11/reference/datamodel.html#objects-values-and-types), [function definitions](https://docs.python.org/3.11/reference/compound_stmts.html#function-definitions), [iterators and generators](https://docs.python.org/3.11/reference/datamodel.html#generator-functions), and [`with` statements](https://docs.python.org/3.11/reference/compound_stmts.html#the-with-statement); [`typing`](https://docs.python.org/3.11/library/typing.html); and the Python Packaging User Guide's [installing packages](https://packaging.python.org/en/latest/tutorials/installing-packages/) and [managing application dependencies](https://packaging.python.org/en/latest/tutorials/managing-dependencies/) tutorials. Checked 2026-10-15.

### Representative answers / 代表性回答

**How do mutability, argument binding, and defaults affect a function call? / 可变性、参数绑定与默认值如何影响函数调用？** Names bind to objects, so a caller and a parameter can refer to the same mutable object. An in-place mutation is visible through both references; rebinding the local parameter does not rebind the caller's name. Python evaluates a default expression when the function is defined, so a mutable default is shared across calls. Use `None` and allocate a fresh list or dictionary inside when each call needs independent state.

名称绑定到对象，因此调用方和形参可能引用同一可变对象。原地修改会通过两个引用都可见；在函数内部重新绑定形参不会改变调用方的名称绑定。Python 在函数定义时求值默认表达式，因此可变默认值会在多次调用间共享。若每次调用需要独立状态，使用 `None` 并在函数内部创建新列表或字典。

**How do iterators, generators, and context managers control work and resources? / 迭代器、生成器与上下文管理器如何控制工作和资源？** An iterator produces one value per request, and a generator packages that pull-based behavior with `yield` and saved execution state. That can avoid building an entire intermediate collection, but later errors may occur after earlier values have already been consumed. A context manager runs its exit behavior when a block ends, including during exception unwinding, so files and other resources have a clear cleanup boundary.

迭代器按请求产出一个值，生成器通过 `yield` 和保存的执行状态封装这种拉取式行为。这样可以避免构建整个中间集合，但后续错误可能在较早的值已经被消费后才发生。代码块退出时（包括异常展开期间），上下文管理器都会运行退出逻辑，因此文件等资源有明确的清理边界。

**What do Python type hints guarantee at runtime? / Python 类型提示在运行时保证什么？** By themselves, they guarantee nothing about the values passed or returned. They communicate expected shapes to humans and static tools. Programs still parse and validate untrusted or external data where it enters the application, and use explicit runtime checks when runtime enforcement is required.

类型提示本身不会在运行时保证输入值或返回值的类型。它们向读者和静态工具传达预期的数据形状。程序仍需在外部数据进入应用时解析与校验；需要运行时强制时，应添加显式检查或使用专门的校验库。
## 24. Why can an async FastAPI endpoint still block? / 为什么异步 FastAPI 接口仍会阻塞？

**Core idea / 核心模型：** `asyncio` lets one event-loop thread make progress on other tasks while the current task waits for asynchronous I/O. An `async def` declaration alone does not make blocking work asynchronous: choose `def` for synchronous libraries that block, and `async def` when awaited libraries can suspend. Tie every acquired resource to a clear cleanup boundary, and treat cancellation as a cooperative request to stop. / `asyncio`让事件循环线程在当前任务等待异步I/O时推进其他任务。仅仅声明`async def`不会让阻塞操作异步：使用同步阻塞库时可选择`def`，使用能通过`await`挂起的库时选择`async def`。资源应绑定明确的清理边界；取消是要求任务协作停止，而非强制终止。

**Key terms / 关键术语：** coroutine function / 协程函数；coroutine object / 协程对象；awaitable / 可等待对象；task / 任务；event loop / 事件循环；cooperative scheduling / 协作式调度；blocking I/O / 阻塞I/O；deadline / 截止时间；cancellation / 取消；yield dependency / `yield`依赖；worker thread / 工作线程。

### From `async def` to a running task / 从`async def`到运行中的任务

An `async def` **coroutine function** describes work. Calling it creates a **coroutine object**; it does not run the body. `await coro()` drives that coroutine as part of the current task. `asyncio.create_task(coro())` schedules it as a separate **Task**, so it can progress concurrently with other tasks. Keep and await created tasks; starting work without collecting its result makes failures and shutdown hard to control. In Python 3.11, `asyncio.TaskGroup` is a structured way to create related tasks and wait for them together.

An **awaitable** is any object accepted by `await`, including coroutine objects, Tasks, and Futures. During an incomplete await, the current task suspends and the event loop can run another ready task or service I/O. This is cooperative: code runs until it reaches a suspension point. A synchronous call such as `time.sleep()`, a blocking database driver, or a long CPU loop prevents the event-loop thread from serving other tasks during that call.

An `async def` function containing `yield` is an **async-generator function**; calling it returns an **async-generator object**, not a coroutine object. FastAPI manages that object's dependency lifecycle to run cleanup after yielding the resource.

### Choose the boundary by the library you call / 按所调用的库选择边界

For an awaited database or HTTP client, use an `async def` route and await its I/O. A synchronous `def` route or dependency that FastAPI calls is run in its worker thread pool, so a legacy synchronous client can fit that boundary. Conversely, a synchronous helper called directly from inside an `async def` route is just a normal function call; FastAPI does not automatically move that nested call to a thread.

`asyncio.to_thread()` is useful for blocking I/O that cannot yet be replaced, and it keeps the event loop available while the thread waits. It is not a general CPU-parallelism switch: in CPython, the GIL usually limits simultaneous execution of pure-Python CPU work. A process pool or separate worker can run CPU work in parallel, with serialization, startup, memory, and queueing costs. Native extensions that release the GIL and other Python implementations can differ; measure the actual workload. Bound thread/process concurrency so offloading does not merely move an unbounded queue; see [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) for admission and backpressure.

### Cancellation, deadlines, and cleanup / 取消、截止时间与清理

`Task.cancel()` arranges for `CancelledError` to be raised in the task at a later opportunity, commonly at an `await`. Use `try/finally` to release resources and normally let cancellation propagate after cleanup. Do not catch `BaseException` or suppress `CancelledError` as a generic error; structured concurrency and timeout scopes rely on cancellation being visible.

In Python 3.11, `asyncio.timeout(seconds)` cancels the current task when its time budget expires and raises `TimeoutError` outside the context manager. It is cooperative: a blocking synchronous function prevents the event loop from delivering that cancellation until the function returns. A timeout around `await asyncio.to_thread(...)` stops waiting in the coroutine but cannot forcibly stop a thread function already running. A client timeout also does not prove that a remote operation stopped or had no side effect. Pass remaining request budget to supported downstream calls and use the broader [API reliability guidance](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) for end-to-end deadlines and unknown outcomes.

FastAPI yield dependencies add a resource-lifetime decision: request scope remains open through response streaming, while function scope closes before the response is sent. The version-specific lifecycle, cleanup order, and disconnect caveat are explained in [FastAPI yield-dependency lifetime / FastAPI yield 依赖的资源生命周期](#25.%20How%20long%20should%20a%20FastAPI%20dependency%20stay%20open%20during%20a%20response?%20/%20FastAPI%20%E4%BE%9D%E8%B5%96%E5%BA%94%E5%9C%A8%E5%93%8D%E5%BA%94%E6%9C%9F%E9%97%B4%E4%BF%9D%E6%8C%81%E5%A4%9A%E4%B9%85%EF%BC%9F). The smoke check below verifies explicit cancellation and streaming cleanup for the versions listed below; it does not establish how every ASGI server handles a real network disconnect.

~~~mermaid
flowchart LR
    Sync[Blocking sync library] -->|def route or dependency| Pool[FastAPI worker thread pool]
    Async[Async library] -->|await| Loop[Event loop can run other tasks]
    Inline[Blocking call inside async route] -->|no suspension| Block[Event loop is blocked]
    CPU[Pure-Python CPU work] -->|bounded process pool or worker| Parallel[Other execution resource]
~~~

### Runnable request example / 可运行的请求示例

This small app has a sync settings dependency, an async resource dependency, an awaited route with a deadline, a streaming route that needs request-scoped cleanup, a deliberately bad blocking route, and a thread-offloaded I/O route. Save the complete block as `async_api_demo.py`; it is an executable smoke check rather than a production server.

~~~python
import asyncio
import threading
import time

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from httpx import ASGITransport, AsyncClient

trace = []
slow_started = []
quick_seen = []


def load_settings():
    # FastAPI runs a sync dependency it calls in its worker thread pool.
    return {"region": "demo", "thread": threading.get_ident()}


class Store:
    async def get(self, item_id: int, region: str):
        await asyncio.sleep(0)  # stand-in for an async driver wait
        return {"id": item_id, "region": region}


async def get_store():
    trace.append("open")
    try:
        yield Store()
    finally:
        trace.append("close")


app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(
    item_id: int,
    settings=Depends(load_settings),
    store=Depends(get_store, scope="function"),
):
    assert settings["thread"] != threading.get_ident()
    async with asyncio.timeout(0.5):
        return await store.get(item_id, settings["region"])


def blocking_io():
    time.sleep(0.06)
    return "done"


@app.get("/bad")
async def bad_route():
    slow_started.append(time.monotonic())
    blocking_io()  # blocks the event-loop thread
    return {"ok": True}


@app.get("/quick")
async def quick_route():
    quick_seen.append(time.monotonic())
    return {"ok": True}


@app.get("/offloaded")
async def offloaded_route():
    return {"result": await asyncio.to_thread(blocking_io)}


@app.get("/stream")
async def stream(store=Depends(get_store)):  # default yield scope is request
    async def body():
        trace.append("body")
        yield "x"

    return StreamingResponse(body(), media_type="text/plain")


@app.get("/wait")
async def wait_forever(store=Depends(get_store)):
    await asyncio.Event().wait()


async def check():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://example.test"
    ) as client:
        trace.clear()
        response = await client.get("/items/7")
        assert response.json() == {"id": 7, "region": "demo"}
        assert trace == ["open", "close"]  # function scope closes before send

        trace.clear()
        response = await client.get("/stream")
        assert response.text == "x"
        assert trace == ["open", "body", "close"]  # request scope covers body

        trace.clear()
        task = asyncio.create_task(client.get("/wait"))
        await asyncio.sleep(0.01)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError("request task was expected to be cancelled")
        assert trace == ["open", "close"]

        slow_started.clear()
        quick_seen.clear()
        bad = asyncio.create_task(client.get("/bad"))
        await asyncio.sleep(0)  # let /bad block before /quick is scheduled
        quick = await client.get("/quick")
        await bad
        assert quick.status_code == 200
        assert quick_seen[0] - slow_started[0] >= 0.05

        response = await client.get("/offloaded")
        assert response.json() == {"result": "done"}


asyncio.run(check())
~~~

The `/bad` route delays the next event-loop request because it calls a blocking helper directly. Use a synchronous route for a synchronous I/O stack, or explicitly offload a blocking call; when possible prefer a native async client. The `/items` route awaits I/O and receives the sync and async dependencies through FastAPI's respective boundaries. Its 0.5-second timeout is only a local teaching budget, not a recommended service-wide setting.

### Python and runtime versions / Python与运行时版本

`async`/`await` syntax is part of Python; `asyncio` is a standard-library API. This example was checked with **CPython 3.11.13**, FastAPI **0.128.0**, Starlette **0.47.2**, and HTTPX **0.28.1**. `asyncio.timeout()` and `asyncio.TaskGroup` require Python 3.11; `asyncio.to_thread()` requires Python 3.9+. CPython is one Python implementation, so GIL statements above are explicitly CPython-specific. Verify framework lifecycle options against the installed FastAPI version: newer live documentation may describe behavior absent in an older release.

### Interview answers / 面试回答

**Why can an `async def` endpoint still stall other requests? / 为什么`async def`接口仍会拖慢其他请求？** An async function only yields when it awaits an operation that actually suspends. Calling a synchronous network/file helper or doing a long CPU loop inline keeps the event-loop thread busy. I would use an async driver, a sync route/dependency that FastAPI can offload, or a bounded thread/process worker chosen for the workload; then I would measure queueing and latency.

异步函数只有在等待一个确实会挂起的操作时才让出执行权。在函数内直接调用同步网络/文件操作，或执行很长的CPU循环，都会占住事件循环线程。我会使用异步驱动、由FastAPI代为卸载的同步路由/依赖，或根据工作负载选择有界线程/进程工作池，并测量排队与延迟。

**What happens when a request is cancelled while it owns a resource? / 请求持有资源时被取消会怎样？** Cancellation is delivered cooperatively, so I put release logic in `finally` and let `CancelledError` propagate. For FastAPI `yield` dependencies I choose request scope if response streaming still consumes the resource, and function scope if cleanup should happen before sending the response. I would not assume a client timeout or disconnect proves remote work stopped; I would keep downstream deadlines and side-effect handling explicit.

取消通过协作方式传递，因此我会把释放逻辑放进`finally`并让`CancelledError`继续传播。若响应流仍要使用FastAPI的`yield`依赖，我会选择request scope；若资源应在响应发送前关闭，则选择function scope。我不会因为客户端超时或断开就认定远端工作已停止；下游截止时间与副作用处理仍需显式定义。

**Sources / 来源：** Python 3.11 [asynchronous generator functions](https://docs.python.org/3.11/reference/expressions.html#asynchronous-generator-functions), [`asyncio` tasks, cancellation, timeouts, and threads](https://docs.python.org/3.11/library/asyncio-task.html), [asyncio development guidance](https://docs.python.org/3.11/library/asyncio-dev.html), and [executor cancellation behavior](https://docs.python.org/3.11/library/concurrent.futures.html); FastAPI [async and sync route behavior](https://fastapi.tiangolo.com/async/), [yield dependency scopes](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/), and [streaming dependency lifetime](https://fastapi.tiangolo.com/advanced/advanced-dependencies/); version-pinned FastAPI [0.128.0 dependency resolver](https://github.com/fastapi/fastapi/blob/0.128.0/fastapi/dependencies/utils.py), checked 2026-10-15. Related: [Python Fundamentals / Python基础](#23.%20How%20do%20Python%20values,%20iterators,%20and%20resource%20lifetimes%20behave?%20/%20Python%20%E7%9A%84%E5%80%BC%E3%80%81%E8%BF%AD%E4%BB%A3%E5%99%A8%E4%B8%8E%E8%B5%84%E6%BA%90%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E5%A6%82%E4%BD%95%E5%B7%A5%E4%BD%9C%EF%BC%9F), [API Reliability and Asynchronous Delivery / API可靠性与异步交付](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F), [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#16.%20How%20does%20a%20browser%20request%20reach%20an%20HTTP%20response?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F), and [Database Fundamentals / 数据库基础](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F). [HTTP API Contracts / HTTP API契约](#26.%20How%20do%20you%20design%20a%20predictable%20HTTP%20API%20contract?%20/%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F) defines the request, response, and error shapes used by these handlers. [Data Access and Connection Pools / 数据访问与连接池](#28.%20How%20do%20you%20scope%20an%20ORM%20Session%20and%20diagnose%20pool%20exhaustion?%20/%20%E5%A6%82%E4%BD%95%E9%99%90%E5%AE%9A%20ORM%20Session%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E5%B9%B6%E8%AF%8A%E6%96%AD%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F) expands the resource example into database-session, transaction, and pool-lifetime choices.
## 25. How long should a FastAPI dependency stay open during a response? / FastAPI 依赖应在响应期间保持多久？

A yielded dependency is a resource scope: FastAPI enters it before using the route, then runs its cleanup after the chosen scope ends. With request scope, cleanup waits until the response body has been sent, so a streaming body can keep using the resource. With function scope, cleanup runs after the route function returns but before the response is sent; use it only when serialization and streaming no longer need the resource. / yield 依赖定义了资源作用域：FastAPI 在路由使用它之前进入依赖，并在所选作用域结束时清理资源。request scope 会等到响应体发送后再清理，因此流式响应可以继续使用该资源。function scope 在路由函数返回后、响应发送前清理资源；只有序列化和流式传输不再需要该资源时才适用。

**Key terms / 关键术语：** yield dependency / yield 依赖；request scope / 请求作用域；function scope / 函数作用域；streaming response / 流式响应；cleanup / 清理；disconnect / 连接断开。

~~~mermaid
    participant F as FastAPI
    participant R as Route
    participant D as Yield dependency
    participant B as Streaming body
    F->>D: Enter and acquire resource
    F->>R: Call route with resource
    R-->>F: Return response object
    alt function scope
        F->>D: Run cleanup before sending response
        F->>B: Send response body
    else request scope
        F->>B: Generate and send response body
        B->>D: Continue using resource
        F->>D: Run cleanup after response body
    end
~~~

### Choose scope from the last use / 按最后一次使用选择作用域

FastAPI 0.128.0 defaults yielded dependencies to request scope. An explicit function scope closes the dependency after the path operation function returns but before the response is sent. A streaming response that consumes a yielded dependency while its body is produced needs request scope; closing it at function return would end the resource too early.

The dependency's finally block runs during ordinary cleanup and when explicit task cancellation reaches the ASGI application. A network disconnect is not guaranteed to cancel every server task in the same way. Verify the behavior of the chosen ASGI server, response class, and deployment mode rather than inferring it from a client timeout.

The executable FastAPI smoke check in [Python Async and FastAPI Request Lifecycle / 为什么异步 FastAPI 接口仍会阻塞？](#24.%20Why%20can%20an%20async%20FastAPI%20endpoint%20still%20block?%20/%20%E4%B8%BA%E4%BB%80%E4%B9%88%E5%BC%82%E6%AD%A5%20FastAPI%20%E6%8E%A5%E5%8F%A3%E4%BB%8D%E4%BC%9A%E9%98%BB%E5%A1%9E%EF%BC%9F) compares function-scope cleanup, request-scope streaming, and explicit cancellation. It checks FastAPI 0.128.0, Starlette 0.47.2, and HTTPX 0.28.1; its explicit task cancellation case does not claim to cover every real disconnect path.

**Sources / 来源：** FastAPI [yield dependency scopes](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/) and [advanced dependencies and streaming responses](https://fastapi.tiangolo.com/advanced/advanced-dependencies/); version-pinned FastAPI [0.128.0 dependency resolver](https://github.com/fastapi/fastapi/blob/0.128.0/fastapi/dependencies/utils.py), checked 2026-10-15. The dependency scope and disconnect behavior are version and server specific.
## 26. How do you design a predictable HTTP API contract? / 如何设计可预期的 HTTP API 契约？

**Core idea / 核心模型：** An API contract makes a boundary predictable: it says which request shapes are accepted, which success representation is returned, and how clients recognize failures. Validate input at the boundary, keep response and error shapes intentional, and document pagination and evolution rules so clients do not infer behavior from implementation details. / API契约让接口边界可预期：明确接受哪些请求形状、成功时返回什么表示，以及客户端如何识别失败。在边界校验输入，明确设计响应与错误形状，并说明分页和演进规则，避免客户端依赖实现细节。

**Key terms / 关键术语：** request schema / 请求结构；response schema / 响应结构；boundary validation / 边界校验；problem details / 问题详情；machine-readable error / 机器可读错误；OpenAPI / OpenAPI描述；opaque cursor / 不透明游标；compatible evolution / 兼容演进。

### Separate HTTP semantics from API policy / 区分HTTP语义与API策略

An API contract sits above the transport: a route and method, its path/query/body inputs, response schemas, status outcomes, and pagination rules. HTTP defines the common message and status-code semantics; the API chooses the domain-specific representations and which status applies to each outcome. See [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#16.%20How%20does%20a%20browser%20request%20reach%20an%20HTTP%20response?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F) for method, status, and transport basics and [API Reliability and Asynchronous Delivery / API可靠性与异步交付](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) for timeouts, retries, and unknown write outcomes.

A type annotation helps the application and framework understand values; it is not proof that an untrusted request has the right shape or meaning. Define request models and constraints at the boundary. Return a deliberate response model as well. Structural validation can reject a missing field or out-of-range number, but it cannot decide permission, resource ownership, uniqueness under concurrency, or whether a business action is allowed. Those rules need trusted authorization and domain logic; durable uniqueness belongs at the data boundary (see [Database Fundamentals / 数据库基础](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F)).

[OpenAPI](https://spec.openapis.org/oas/latest.html) describes operations, inputs, response codes, media types, and schemas in a machine-readable document. In FastAPI, request models and `response_model` contribute generated schemas; custom error handlers must also be represented in each operation's declared responses, or the runtime response and published contract can diverge. OpenAPI documents a contract; it does not validate deployed behavior by itself.

~~~mermaid
flowchart LR
    Request[Request with path, query, and body] --> Validate[Validate shape and domain boundary]
    Validate -->|valid| Success[Documented success status and schema]
    Validate -->|invalid| Problem[Problem Details with stable type]
    Validate -->|permission or conflict| Outcome[Documented policy outcome]
    Outcome --> Problem
    Success --> OpenAPI[OpenAPI describes both]
    Problem --> OpenAPI
~~~

### Give failures a stable machine identity / 为错误提供稳定的机器标识

An API can use [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) with `Content-Type: application/problem+json`. Its `type` URI is the primary identifier for a problem category; `status` in the body must match the HTTP response; `title` and `detail` are human-readable. Clients should not parse prose in `detail`. Put any stable client-action data in documented extension fields, such as a small `errors` array with a field path and an application-owned code. Avoid echoing raw request values or internal exception text.

The following status mapping is one API's policy, not a universal template:

| Outcome | Example response | Meaning in this API |
|---|---|---|
| Valid create | `201` + `Item` | A new item was created and its representation is returned. |
| Invalid body/query | `422` + problem | The JSON shape or a declared value constraint failed. This sample groups boundary-validation failures here. |
| Missing item | `404` + problem | No item currently has the requested ID. |
| Duplicate name | `409` + problem | The requested create conflicts with the current collection state. |
| Unknown cursor | `400` + problem | The client supplied a continuation token this process does not recognize. |

RFC 9110 describes `422` for syntactically valid content whose instructions cannot be processed and `409` for a conflict with current resource state. A different API may separate malformed JSON syntax as `400`, use a different validation status, or choose another duplicate policy; document the actual behavior and keep it consistent. The transport note covers the status definitions.

### Cursor pagination / 游标分页

For the separate question of page limits, cursors, and completion signals, see [How does cursor pagination continue safely? / 游标分页如何安全续读？](#27.%20How%20does%20cursor%20pagination%20continue%20safely?%20/%20%E6%B8%B8%E6%A0%87%E5%88%86%E9%A1%B5%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E7%BB%AD%E8%AF%BB%EF%BC%9F).
### Runnable contract example / 可运行的契约示例

The API uses a synthetic inventory collection. A Pydantic before-validator strips string input before the field's length constraints run, so whitespace-only input cannot become an empty stored name. / API使用合成库存集合。Pydantic前置验证器先去除字符串两端空白，再执行字段长度约束，因此全空白输入不会变成已保存的空名称。 The complete script below validates request and query boundaries, exposes success and error schemas, and checks the resulting HTTP behavior and OpenAPI document. Save it as `api_contract_demo.py` and run it in an environment with FastAPI and its TestClient dependencies.

~~~python
import secrets

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from typing import Any

from pydantic import BaseModel, Field, field_validator

PROBLEM_BASE = "https://api.example/problems/"


class CreateItem(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    quantity: int = Field(ge=1, le=1000)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class Item(BaseModel):
    id: int
    name: str
    quantity: int


class Page(BaseModel):
    items: list[Item]
    next_cursor: str | None = None


class Problem(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    errors: list[dict[str, str]] | None = None


class ApiProblem(Exception):
    def __init__(self, status: int, kind: str, title: str, detail: str):
        self.status, self.kind, self.title, self.detail = status, kind, title, detail


def problem_content(description: str):
    return {
        "description": description,
        "content": {
            "application/problem+json": {"schema": Problem.model_json_schema()}
        },
    }


PROBLEM_RESPONSES = {
    400: problem_content("Unknown cursor"),
    404: problem_content("Item does not exist"),
    409: problem_content("Name already exists"),
    422: problem_content("Request validation failed"),
}
SEED = {
    1: Item(id=1, name="notebook", quantity=4),
    2: Item(id=2, name="pencil", quantity=8),
    3: Item(id=3, name="folder", quantity=2),
}
items = dict(SEED)
cursor_offsets: dict[str, int] = {}
next_id = 4
app = FastAPI()


def problem_response(status, kind, title, detail, **extensions):
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": PROBLEM_BASE + kind,
            "title": title,
            "status": status,
            "detail": detail,
            **extensions,
        },
    )


@app.exception_handler(ApiProblem)
async def api_problem_handler(request: Request, exc: ApiProblem):
    return problem_response(exc.status, exc.kind, exc.title, exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(part) for part in error["loc"]), "code": "invalid_value"}
        for error in exc.errors()
    ]
    return problem_response(
        422, "validation", "Request validation failed",
        "Correct the fields listed in errors and resubmit.", errors=errors,
    )


@app.get("/items", response_model=Page, responses=PROBLEM_RESPONSES)
async def list_items(limit: int = Query(default=2, ge=1, le=100), cursor: str | None = None):
    if cursor is None:
        offset = 0
    elif cursor in cursor_offsets:
        offset = cursor_offsets[cursor]
    else:
        raise ApiProblem(400, "invalid-cursor", "Invalid cursor", "Start a new listing.")

    ordered = [items[key] for key in sorted(items)]
    page = ordered[offset : offset + limit]
    next_cursor = None
    if offset + len(page) < len(ordered):
        next_cursor = secrets.token_urlsafe(12)
        cursor_offsets[next_cursor] = offset + len(page)
    return Page(items=page, next_cursor=next_cursor)


@app.get("/items/{item_id}", response_model=Item, responses=PROBLEM_RESPONSES)
async def get_item(item_id: int):
    if item_id not in items:
        raise ApiProblem(404, "not-found", "Item not found", "No item has this ID.")
    return items[item_id]


@app.post("/items", status_code=201, response_model=Item, responses=PROBLEM_RESPONSES)
async def create_item(payload: CreateItem):
    global next_id
    name = payload.name
    if any(item.name.casefold() == name.casefold() for item in items.values()):
        raise ApiProblem(409, "duplicate-name", "Name already exists", "Choose another name.")
    item = Item(id=next_id, name=name, quantity=payload.quantity)
    items[next_id] = item
    next_id += 1
    return item


def check():
    client = TestClient(app)
    first = client.get("/items?limit=2")
    assert first.status_code == 200 and len(first.json()["items"]) == 2
    cursor = first.json()["next_cursor"]
    assert cursor
    second = client.get("/items", params={"limit": 2, "cursor": cursor})
    assert second.status_code == 200
    assert [x["id"] for x in second.json()["items"]] == [3]
    second_body = second.json()
    assert "next_cursor" in second_body and second_body["next_cursor"] is None

    bad_page = client.get("/items?limit=101")
    assert bad_page.status_code == 422
    assert bad_page.headers["content-type"].startswith("application/problem+json")
    assert bad_page.json()["type"] == PROBLEM_BASE + "validation"
    assert bad_page.json()["errors"]

    malformed = client.post("/items", json={"name": "stapler", "quantity": 0})
    assert malformed.status_code == 422 and malformed.json()["type"] == PROBLEM_BASE + "validation"
    missing_field = client.post("/items", json={"name": "stapler"})
    assert missing_field.status_code == 422

    whitespace_name = client.post("/items", json={"name": "   ", "quantity": 1})
    assert whitespace_name.status_code == 422 and whitespace_name.json()["type"] == PROBLEM_BASE + "validation"

    created = client.post("/items", json={"name": " stapler ", "quantity": 2})
    assert created.status_code == 201 and created.json()["id"] == 4
    assert created.json()["name"] == "stapler"
    conflict = client.post("/items", json={"name": "Stapler", "quantity": 3})
    assert conflict.status_code == 409
    assert conflict.json()["type"] == PROBLEM_BASE + "duplicate-name"

    missing = client.get("/items/999")
    assert missing.status_code == 404
    assert missing.json()["type"] == PROBLEM_BASE + "not-found"
    invalid_cursor = client.get("/items?cursor=unknown-token")
    assert invalid_cursor.status_code == 400

    operation = app.openapi()["paths"]["/items"]["post"]
    assert operation["responses"]["201"]["content"]["application/json"]["schema"]
    assert operation["responses"]["409"]["content"]["application/problem+json"]["schema"]
    print("201 success trims names; invalid, missing, and whitespace-only input and limit 101 -> 422; missing item -> 404; duplicate -> 409")
    print("two pages contain 2+1 items; unknown cursor -> 400; final page includes next_cursor=null")
    print("OpenAPI", app.openapi()["openapi"], "documents JSON success and problem+json errors")


check()
~~~

The client reads a successful body according to `Item`/`Page`; on failure it checks the HTTP status and the stable problem `type`, then uses a documented extension such as `errors` to associate an issue with a field. It displays or logs `detail` for people without parsing it as a code. To continue, it passes a non-null `next_cursor` back unchanged and stops when the field's value is JSON `null`.

### Evolve the contract deliberately / 有计划地演进契约

Adding an optional response field is often compatible when clients ignore unknown fields, but generated clients and strict decoders can reject it. Removing or renaming a field, changing its type or meaning, making an optional request field required, changing a problem `type`, or changing pagination meaning can break callers. Treat these as contract changes: publish the compatibility policy, test representative old and new clients, and use a versioning or migration window when an incompatible change is necessary. There is no single mandatory versioning scheme.

### Interview answers / 面试回答

**How would you make an API failure usable by both a client and a person? / 如何让API错误同时适合程序与人阅读？** I would keep the HTTP status meaningful, return a stable problem `type`, and document the response media type and schema in OpenAPI. Human text can explain the immediate issue, but clients branch on the stable identifier or a documented extension rather than parsing that text. I would avoid reflecting secrets or exception details and test that runtime responses match the published schema.

我会让HTTP状态码有明确含义，返回稳定的问题`type`，并在OpenAPI中说明响应媒体类型和结构。人类可读文本可以解释当前问题，但客户端应根据稳定标识或有文档约定的扩展字段分支，而不是解析这段文本。我会避免回显机密或异常细节，并测试运行时响应是否符合已发布的结构。



**Sources / 来源：** [OpenAPI Specification, latest](https://spec.openapis.org/oas/latest.html); IETF [RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html); [RFC 9110 §15.5](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5) for 404, 409, and 422 semantics; Google [AIP-158, Pagination](https://google.aip.dev/158) as one pagination style; FastAPI [request bodies and validation](https://fastapi.tiangolo.com/tutorial/body/), [response models](https://fastapi.tiangolo.com/tutorial/response-model/), and [handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/); Pydantic 2.11 [field validators](https://docs.pydantic.dev/2.11/concepts/validators/), checked against a FastAPI 0.128.0 / Pydantic 2.11.7 runtime on 2026-10-15. In that installed runtime, `app.openapi()["openapi"]` returned `3.1.0`; the live OpenAPI `latest` document resolved to `3.2.1`, so the sample reports its actual generated version instead of assuming the framework emits the newest specification.

**Related notes / 相关笔记：** [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#16.%20How%20does%20a%20browser%20request%20reach%20an%20HTTP%20response?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F) covers the transport and generic status semantics; [Cursor pagination / 游标分页](#27.%20How%20does%20cursor%20pagination%20continue%20safely?%20/%20%E6%B8%B8%E6%A0%87%E5%88%86%E9%A1%B5%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E7%BB%AD%E8%AF%BB%EF%BC%9F) owns page-size, cursor, and end-of-list behavior; [API Reliability and Asynchronous Delivery / API可靠性与异步交付](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) covers timeouts, retries, and ambiguous side effects; [Database Fundamentals / 数据库基础](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F) covers durable uniqueness and transaction boundaries.
## 27. How does cursor pagination continue safely? / 游标分页如何安全续读？

**Core answer / 核心回答：** Bound each page, return an opaque continuation token, keep a deterministic order, and define how the token behaves when records change. The client passes a non-null token back unchanged and stops only when the response explicitly returns JSON null. Recheck authorization on every page; a cursor identifies where to continue, not who may read the data. / 限制每页大小，返回不透明的续读 token，使用确定排序，并说明记录变化时 token 的行为。客户端原样传回非空 token，只有响应明确返回 JSON null 时才停止。每一页都要重新授权；游标只标识从哪里继续，不证明调用者有读取权限。

**Key terms / 关键术语：** page size / 页大小；opaque cursor / 不透明游标；stable ordering / 稳定排序；terminal null / 结束标记；authorization / 授权。

~~~mermaid
flowchart LR
    Client[Client requests page] --> Auth[Authenticate and authorize this page]
    Auth --> Bound[Validate maximum page size]
    Bound --> Query[Fetch in stable order after cursor]
    Query --> More{More matching rows?}
    More -->|yes| Next[Return rows and opaque next_cursor]
    More -->|no| End[Return rows and next_cursor: null]
    Next --> Client
    End --> Stop[Client stops]
~~~


A list response should cap the number of returned records. This example accepts `limit` from 1 through 100, defaults it to 2 for the demonstration, and rejects a value above the maximum with a validation problem. Other API styles may clamp it to the maximum; [Google AIP-158](https://google.aip.dev/158) is one example that specifies coercion for oversized page sizes. The choice is policy: publish the default, maximum, and whether an oversized value is rejected or reduced.

This example includes `next_cursor` in every page: it is an opaque string when more results are available and JSON `null` at the end. Here, `null` is the terminal signal, so the client sends a non-null cursor back unchanged and stops when the value is null. A page may contain fewer rows than the requested limit without proving that the collection has ended. A token says where to continue, not who may read the rows: authenticate and authorize every page request. Use a stable order with a tie-breaker. If records can change during a long listing, define whether pages reflect a moving collection or a consistent snapshot.

The runnable example stores random cursor-to-offset mappings in memory for a tiny synthetic list. This makes the token opaque to the caller, but the token stops working after process restart and the in-memory list is not a scalable storage query. A production cursor needs a documented lifetime/consistency policy and a bounded storage query; the data-access design is separate from this note.


**How should a client know when a page is finished? / 客户端如何判断分页结束？** It should follow the server-issued opaque cursor and stop when `next_cursor` is present with JSON `null`; page length alone is not a reliable end signal. The API should bound the page size, order records deterministically, and re-check authorization for every page. Cursor lifetime and behavior during concurrent updates are explicit API choices.

客户端应原样传回服务端签发的不透明游标，并在`next_cursor`字段存在且值为JSON`null`时停止；单靠当前页长度不能可靠判断结束。API应限制页大小、按确定顺序排列记录，并对每一页重新授权。游标有效期以及并发更新时的行为都应作为明确的接口策略定义。

**Runnable example / 可运行示例：** [HTTP API Contracts / How do you design a predictable HTTP API contract?](#26.%20How%20do%20you%20design%20a%20predictable%20HTTP%20API%20contract?%20/%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F) contains the synthetic FastAPI cursor example and assertions. Its random in-memory cursor-to-offset table is intentionally not a production storage query: tokens expire at process restart and the data is not scalable.

**Sources / 来源：** Google [AIP-158, Pagination](https://google.aip.dev/158) is one pagination policy and specifies behavior for oversized page sizes; HTTP status and response contract conventions are described in [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) and [HTTP API Contracts / HTTP API契约](#26.%20How%20do%20you%20design%20a%20predictable%20HTTP%20API%20contract?%20/%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F). The parent note's tested cursor, terminal-null, authorization, and OpenAPI behavior remains tied to FastAPI 0.128.0 / Pydantic 2.11.7.
## 28. How do you scope an ORM Session and diagnose pool exhaustion? / 如何限定 ORM Session 作用域并诊断连接池耗尽？

**Core explanation / 核心解释：** An ORM session is a short-lived unit of work that tracks mapped objects and coordinates SQL within a transaction. Its lifetime, the transaction lifetime, and the database connection lifetime are related but distinct: a session may acquire a pooled connection only when it first needs the database, and commit or rollback returns that connection for reuse. / ORM Session 是短生命周期的工作单元，负责跟踪映射对象并协调事务中的 SQL。Session、事务和数据库连接的生命周期彼此相关但并不相同：Session 通常在首次访问数据库时才从连接池取连接，提交或回滚后会将连接归还以便复用。

**Key terms / 关键术语：** ORM mapping / ORM 映射；identity map / 身份映射；unit of work / 工作单元；session / 会话；transaction / 事务；connection checkout / 连接借出；connection pool / 连接池；pool timeout / 连接池等待超时。

### Generalize the existing EF Core example / 推广已有 EF Core 示例

The existing [ASP.NET Core note](../../archive/back-end/ASP.NET-Core.md) is a concrete reference for entity mapping, `DbContext` tracking, dependency-injection scope, and disposal. It shows that a `DbSet<T>` exposes an entity set rather than declaring a table, that the model controls mapping, and that `AddDbContext` is scoped by default in the typical request flow. When the scope ends, its `DbContext` is disposed. The reusable rule is to give each request or job a bounded unit of work, keep its tracked objects local to that unit, and dispose it when the work ends.

Keep four boundaries separate:

- **Session / `DbContext`:** identity map plus change tracking and query coordination for mapped objects. It is not a durable application cache or a database connection.
- **Transaction:** the atomic commit/rollback boundary for statements that must succeed together. A session can span more than one transaction if deliberately reused, so a request scope alone does not define atomicity.
- **Connection:** the driver-level handle used to talk to the database. It is commonly checked out lazily from a pool when a transaction executes SQL.
- **Pool:** process-local reuse and concurrency limit for those connections. Closing a checked-out connection normally returns it to the pool; it need not close the underlying network socket.

### One request, one bounded transaction / 一个请求与一个有界事务

This synchronous SQLAlchemy 2.0 example assumes `Customer` and `Order` are mapped classes. `session.begin()` commits on a clean exit and rolls back if an exception escapes. The outer session context closes the session on both paths.

~~~python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

engine = create_engine(
    database_url,
    pool_size=8,
    max_overflow=2,
    pool_timeout=2,
)

def place_order(customer_id: int, sku: str, quantity: int) -> int:
    with Session(engine) as session, session.begin():
        customer = session.get(Customer, customer_id)
        if customer is None:
            raise LookupError("customer not found")

        order = Order(customer_id=customer_id, sku=sku, quantity=quantity)
        session.add(order)
        session.flush()  # emits the INSERT inside this transaction
        order_id = order.id

    return order_id
~~~

The ORM operation still has an SQL contract: conceptually it emits an insert such as `INSERT INTO orders (customer_id, sku, quantity) VALUES (:customer_id, :sku, :quantity)`. For a report or a database-specific operation, make the SQL explicit and bind values rather than concatenating them:

~~~python
with Session(engine) as session:
    rows = session.execute(
        text("SELECT order_id, amount_cents FROM orders WHERE customer_id = :id"),
        {"id": customer_id},
    ).all()
~~~

Use an ORM for common mapping, relationship loading, and change tracking when its generated queries are clear. Use SQL directly when a bulk operation, specialized SQL feature, or plan shape needs explicit control. Either way, keep parameter binding and the same transaction/constraint rules; inspect generated or handwritten SQL with the selected database's plan tool.

The [Database Fundamentals / 数据库基础](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F) note explains SQL result semantics, constraints, query plans, transactions, and isolation independently of the ORM.

~~~mermaid
flowchart LR
    Request[Request or job begins] --> Session[Create short-lived Session]
    Session -->|first SQL| Checkout[Check out pooled connection]
    Checkout --> Work[Queries and writes]
    Work -->|success| Commit[Commit transaction]
    Work -->|error| Rollback[Rollback transaction]
    Commit --> Return[Return connection to pool]
    Rollback --> Return
    Return --> Close[Close Session]
~~~

### Follow the checkout and cleanup / 跟踪借出与清理

The request path is: create a fresh session → the first query or flush starts database work and checks out a connection → load or change mapped objects → commit on success or rollback on error → return the connection → close the session. SQLAlchemy sessions use autobegin by default, so a read can also open a transaction. A `Session` context manager closes the session; `Session.begin()` frames the transaction and handles rollback before propagating an exception. The official FastAPI SQL database example uses a generator dependency with `with Session(engine)` to provide one session per request.

Avoid holding an active transaction while waiting on a remote API, streaming a slow response, or doing other work that does not need the database. While a connection is checked out, another request may wait for a pool slot. If all slots are busy, the pool waits up to its configured timeout; then the request fails with a pool timeout. A forgotten session, unclosed result/connection, or transaction left open can therefore look like database slowness and eventually exhaust the pool. Observe checkout wait/timeouts, checked-out counts, and long transaction duration; increasing the pool without checking database capacity can move the queue into the database.

For a synchronous SQLAlchemy `QueuePool`, the maximum concurrent connections per process is `pool_size + max_overflow`. If an application has 4 replicas, 3 worker processes per replica, and a pool configured as 8 plus 2 overflow connections, the upper bound is `4 × 3 × (8 + 2) = 120` connections if every process fills its pool. Pools grow on demand rather than pre-opening all those connections. Compare the aggregate with the database's application budget and leave capacity for migrations, administration, and other services. This multiplication assumes each process owns its pool; SQLAlchemy warns against sharing live pooled connections across a process fork.

### Representative answer / 代表性面试回答

**How would you scope an ORM session and diagnose pool exhaustion? / 你会怎样限定 ORM Session 的作用域并排查连接池耗尽？**

Give each request a short-lived session and frame each write unit with one transaction. Commit on success; roll back on an exception; always close the session so checked-out connections return to the pool. The ORM tracks mapped state, while the database transaction defines atomicity and the pool controls concurrent connections. Compute the possible connection total across every replica and worker process, then inspect checkout waits and long-held transactions before changing pool size. Use parameterized SQL for operations where explicit query shape matters.

为每个请求创建短生命周期的 Session，并用一个事务界定每组需要原子完成的写入。成功时提交，异常时回滚，并始终关闭 Session，使借出的连接归还连接池。ORM 负责跟踪映射对象；数据库事务决定原子性；连接池限制并发连接数。先按所有副本和工作进程计算连接总上限，再检查连接等待和长事务，之后再决定是否调整连接池。需要明确查询形态时使用参数化 SQL。

**Sources and verification / 来源与验证：** SQLAlchemy 2.0 [Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) and [Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html), and the FastAPI [SQL (Relational) Databases tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/), checked 2026-10-15. The documented synchronous `Session`/transaction pattern and bounded pool behavior were exercised locally with SQLAlchemy 2.0.44 and SQLite 3.51.0: a successful block committed; an exception rolled back; session close reduced checked-out connections from one to zero; a second checkout against a full one-connection pool timed out, then succeeded after the first connection was returned. On 2026-10-27, the docs page identifies SQLAlchemy 2.0.55 as the current 2.0 docs build; the local verification above names the installed runtime version. No network database or asynchronous driver was used.


**Related notes / 相关笔记：** [Database Fundamentals / How do you reserve the last inventory unit safely?](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F) owns the engine's constraint and transaction semantics. [API timeout and safe retry / API 超时后的结果确认与安全重试](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) covers outcome and retry policy; pool growth and queue admission are sized in [the capacity and backpressure note](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F).
## 29. How do you cache database reads without losing freshness? / 如何缓存数据库读取并控制数据新鲜度？

**Core explanation / 核心解释：** In cache-aside, the database remains the source of truth: reads check the cache first and load the database on a miss; writes commit to the database and then invalidate the cached copy. A TTL bounds how long one cached value can live, but invalidation races and cache failures still need an explicit freshness and load policy. / 在 cache-aside 模式中，数据库仍是事实来源：读取先查缓存，未命中时再读取数据库；写入先提交数据库，然后使缓存副本失效。TTL 限制单个缓存值的存活时间，但失效竞态和缓存故障仍需要明确的新鲜度与负载策略。

**Key terms / 关键术语：** cache-aside / 旁路缓存；source of truth / 事实来源；time to live (TTL) / 存活时间；invalidation / 失效；cache stampede / 缓存击穿；negative caching / 负缓存；stale data / 陈旧数据。

### One record, one read/write lifecycle / 一个记录的读写过程

Suppose `products` is authoritative and the cache key is `product:42`. A typical read is:

1. `GET product:42`. On a hit, return the cached representation after applying the same authorization and response rules as a database read.
2. On a miss, query the primary database. If the product exists, cache the representation with a TTL, for example `SET product:42 "..." EX 30`, then return it.
3. If it does not exist, an optional short negative entry can reduce repeated misses: cache a “not found” sentinel for a few seconds. Keep this TTL shorter than the normal entry, and invalidate it when the product is created. Do not cache a database timeout or error as “not found.”

For a write, update the authoritative row and commit first; only then issue `DEL product:42`. The next read repopulates from the database. Redis `GET`, `SET ... EX`, `DEL`, and `TTL` are useful implementation primitives, but these commands do not make a Redis mutation atomic with the database transaction.

The [Database Fundamentals / 数据库基础](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F) note covers the constraints and transaction boundary that protect the source-of-truth write.

~~~mermaid
sequenceDiagram
    participant R as Reader
    participant C as Cache
    participant D as Database
    participant W as Writer
    R->>C: Cache miss
    R->>D: Read old value
    W->>D: Commit new value
    W->>C: Delete cached value
    R->>C: Fill old value after invalidation
    Note over C: Stale value now has a fresh TTL
~~~

#### Make the freshness window explicit / 明确新鲜度窗口

With a 30-second TTL, a value that was filled before an update can remain visible until its entry expires if the post-commit invalidation fails. But TTL is not an end-to-end consistency guarantee: a reader can load the old database value just before a concurrent write commits, then populate the cache after the writer's `DEL`; that stale fill receives a fresh TTL. Each entry's lifetime is bounded, but repeated or delayed stale fills can extend the period in which clients see stale data. If read-after-write freshness is required, bypass the cache for that read or use a versioned/ordered invalidation design; do not assume Redis alone coordinates the two stores.

Include every dimension that changes the returned value in the cache key, such as tenant or locale, and keep authorization checks outside an untrusted cached payload. The [AI response-cache explanation](../../ai-engineering/systems/ai-latency-and-cost-optimization.md) applies the same key-isolation and freshness discipline to exact or semantic response reuse. Semantic similarity cannot establish that data is current or authorized.

### Expiration bursts and cache outages / 集中过期与缓存故障

When a popular key expires, many requests can miss together and send duplicate reads to the database. Coalesce concurrent misses for the same key inside each application process, and add small random jitter to TTLs so many keys do not expire together. Local coalescing reduces one process to roughly one loader per key at a time; it does not coordinate other processes. A Redis-backed short lock is another option at higher fan-out, but it needs a bounded lease and wait, plus safe owner-only release.

A cache outage does not by itself corrupt the authoritative row. If a cache lookup fails, an application may read through to the database only within a deliberate bound: use a request deadline, cap concurrent fallback reads or apply admission control, and fail quickly when the database budget is exhausted. Otherwise a cache outage can turn every request into a database request and exhaust database connections. Serve stale cached data only when that endpoint has a stated maximum acceptable age; for authorization, balances, or other correctness-sensitive decisions, read the authoritative source or fail closed. Cache-fill and invalidation failures should be visible as operational errors rather than silently treated as valid data.

### Representative answer / 代表性面试回答

**How would you add a cache in front of a database, and what happens if Redis fails? / 如何在数据库前增加缓存，Redis 故障时应怎样处理？**

I would keep the database authoritative and use cache-aside: read the cache, load on a miss, write with a TTL, and invalidate only after a database write commits. I would choose the TTL from the endpoint's freshness requirement, account for the failed-invalidation and stale-fill windows, and coalesce concurrent misses for hot keys. If Redis fails, I would bound database fallback by deadlines and concurrency limits; cache loss should increase load, not silently change the source of truth. I would serve stale data only where its maximum age is acceptable.

我会让数据库保持事实来源，并采用 cache-aside：先读缓存，未命中时查数据库，写入缓存时设置 TTL，并只在数据库写入提交后执行失效。我会根据接口的新鲜度要求选择 TTL，考虑失效失败和陈旧回填窗口，并合并热点键的并发未命中请求。Redis 故障时，我会用截止时间和并发上限约束数据库回退；缓存丢失应增加负载，但不能悄悄改变事实来源。只有在业务明确接受最大陈旧时间时才提供旧值。

**Sources and verification / 来源与验证：** Redis [cache-aside](https://redis.io/docs/latest/develop/use-cases/cache-aside/) and [node-redis cache-aside example](https://redis.io/docs/latest/develop/use-cases/cache-aside/nodejs/), checked 2026-10-15. The official examples demonstrate cache-first reads, TTL-bearing writes, invalidation, and a short-lived stampede lock. The flow above is a generic application design; no Redis server was deployed, so Redis commands and outage behavior were not runtime-tested. TTL and `DEL` are implementation tools, not a cross-store consistency protocol.


**Related notes / 相关笔记：** [Web Security and Authentication / Web安全与身份认证](#30.%20How%20do%20you%20prevent%20cross-tenant%20access%20across%20a%20web%20request?%20/%20%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20Web%20%E8%AF%B7%E6%B1%82%E8%B7%A8%E7%A7%9F%E6%88%B7%E8%AE%BF%E9%97%AE%EF%BC%9F) owns principal and tenant authorization before cache lookup. [Data Access and Connection Pools / 数据访问与连接池](#28.%20How%20do%20you%20scope%20an%20ORM%20Session%20and%20diagnose%20pool%20exhaustion?%20/%20%E5%A6%82%E4%BD%95%E9%99%90%E5%AE%9A%20ORM%20Session%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E5%B9%B6%E8%AF%8A%E6%96%AD%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F) explains the connection budget used by bounded database fallback.
## 30. How do you prevent cross-tenant access across a web request? / 如何防止 Web 请求跨租户访问？

**身份认证 / Authentication** establishes which identity or credential is presenting a request. **授权 / Authorization** decides whether that identity may perform this action on this resource. Authentication alone does not grant every permission; enforce authorization on the server for each protected operation. Client checks can improve the interface but cannot decide access.

身份认证回答请求以谁的凭据发出，授权则逐项决定该身份能否访问资源或执行操作；浏览器编码、Cookie属性、CORS、CSRF和CSP处理的是不同边界，不能替代服务端授权或彼此替代。
**Key terms / 关键术语：** authenticated subject / 已认证主体；tenant membership / 租户成员关系；authorization / 授权；resource scope / 资源范围；tenant-scoped query / 租户范围查询；worker revalidation / worker 重新验证。

~~~mermaid
flowchart LR
    Credential[Validate credential] --> Subject[Authenticated subject]
    Subject --> Membership[Resolve current tenant membership]
    Membership --> Action[Authorize action and resource]
    Action --> Query[Tenant-scoped database query]
    Action --> Cache[Authorize before cache lookup]
    Action --> Job[Persist authorized job context]
    Job --> Queue[Queue carries only job ID]
    Queue --> Worker[Worker reloads job and rechecks membership]
    Worker --> Query
~~~

### Tenant-owned resources / 租户资源授权

Authentication yields a validated subject; it does not prove access to every tenant or object. Build a **principal / 请求主体** from the verified identity plus the user's current membership and permissions in the selected tenant. A tenant ID in a URL or request body is only a requested context: resolve it against trusted membership before constructing the principal. Enforce the resource and action together on every API path.

For one synthetic document service, the path is: verified credential → current tenant membership → `GET /documents/{id}` authorization → query constrained by both `tenant_id` and document ID → cache lookup scoped by tenant, subject, and document after authorization → optional job row storing the authorized tenant, requester, and document. The worker loads that canonical job row, rechecks current membership, and calls the same tenant-scoped data function. A worker's broad database role does not make a job payload or object ID trustworthy.

This standard-library example uses SQLite to exercise the API and worker data boundaries. The identity inputs below stand in for a principal produced by a real authentication layer; they are not token validation code.

```python
import sqlite3

db = sqlite3.connect(":memory:")
db.executescript("""
CREATE TABLE memberships (
    tenant_id TEXT NOT NULL, subject TEXT NOT NULL, role TEXT NOT NULL,
    PRIMARY KEY (tenant_id, subject)
);
CREATE TABLE documents (
    id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, body TEXT NOT NULL
);
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY, tenant_id TEXT NOT NULL,
    requester TEXT NOT NULL, document_id TEXT NOT NULL
);
INSERT INTO memberships VALUES ('tenant-a', 'alice', 'reader');
INSERT INTO memberships VALUES ('tenant-b', 'bob', 'reader');
INSERT INTO documents VALUES ('doc-a', 'tenant-a', 'A private sample');
INSERT INTO documents VALUES ('doc-b', 'tenant-b', 'B private sample');
""")

def principal_for(tenant_id, subject):
    # A requested tenant becomes trusted only after this current membership lookup.
    row = db.execute(
        "SELECT role FROM memberships WHERE tenant_id=? AND subject=?",
        (tenant_id, subject),
    ).fetchone()
    if row is None or row[0] not in {"reader", "admin"}:
        return None
    return {"tenant_id": tenant_id, "subject": subject, "role": row[0]}

def read_document(principal, document_id, cache):
    if principal is None or principal["role"] not in {"reader", "admin"}:
        raise PermissionError("no current read permission")
    key = (principal["tenant_id"], principal["subject"], document_id)
    if key not in cache:
        row = db.execute(
            "SELECT body FROM documents WHERE tenant_id=? AND id=?",
            (principal["tenant_id"], document_id),
        ).fetchone()
        if row is None:
            return None
        cache[key] = row[0]
    return cache[key]

def read_api(principal, document_id, cache):
    body = read_document(principal, document_id, cache)
    return (404, None) if body is None else (200, body)

def enqueue(principal, document_id, cache):
    if read_document(principal, document_id, cache) is None:
        raise PermissionError("cannot enqueue an unreadable document")
    cursor = db.execute(
        "INSERT INTO jobs (tenant_id, requester, document_id) VALUES (?, ?, ?)",
        (principal["tenant_id"], principal["subject"], document_id),
    )
    db.commit()
    return cursor.lastrowid

def run_job(job_id, cache):
    # The queue carries only an ID; tenant, actor, and object come from the stored job.
    job = db.execute(
        "SELECT tenant_id, requester, document_id FROM jobs WHERE id=?", (job_id,)
    ).fetchone()
    if job is None:
        raise PermissionError("unknown job")
    tenant_id, requester, document_id = job
    principal = principal_for(tenant_id, requester)  # current membership, not enqueue-time trust
    body = read_document(principal, document_id, cache)
    if body is None:
        raise PermissionError("job target is outside its tenant")
    return body

cache = {}
alice = principal_for("tenant-a", "alice")
bob = principal_for("tenant-b", "bob")
assert read_api(alice, "doc-a", cache) == (200, "A private sample")
assert read_api(bob, "doc-a", cache) == (404, None)  # API boundary
assert run_job(enqueue(alice, "doc-a", cache), cache) == "A private sample"

# Simulate a stale or malformed job row created through a privileged service path.
cursor = db.execute(
    "INSERT INTO jobs (tenant_id, requester, document_id) VALUES (?, ?, ?)",
    ("tenant-b", "bob", "doc-a"),
)
db.commit()
try:
    run_job(cursor.lastrowid, cache)
except PermissionError:
    pass  # worker boundary still rejects the cross-tenant object
else:
    raise AssertionError("worker exposed a cross-tenant document")
```

The query always carries the principal's tenant, and authorization runs before a cache hit. This example gives each principal a separate cache entry; a system with finer-grained permissions must check those permissions on cache hits and include every access-relevant scope or policy version in its cache design. Database row-level security or tenant-scoped credentials can add another boundary, but the application still needs correct authorization and job ownership.

Permission-aware retrieval uses the same boundary before evidence reaches a model; see [Retrieval-Augmented Generation / 检索增强生成](../../ai-engineering/rag/rag-architecture-and-implementation.md) for that application.

**Interview answer / 面试回答：**

> **EN:** I derive the subject from a validated credential, then resolve its current membership in the requested tenant. The API checks the action and scopes the database query by tenant and object ID. I authorize before cache lookup and carry only a server-created job ID into the queue; the worker reloads the job, rechecks membership, and uses the same scoped query. A service account's broad database access does not grant the caller cross-tenant access.
>
> **中文：** 我先从已验证的凭据得到用户身份，再校验其当前租户成员关系。API 同时检查操作权限，并用租户 ID 和对象 ID 限定查询；缓存命中前也要授权。队列只传递服务端创建的任务 ID，worker 重新读取任务、检查成员关系，并复用租户范围查询。服务账号拥有较广数据库权限，不代表调用者可以跨租户访问。

See [AWS Well-Architected SaaS Lens: Preventing cross-tenant access](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/preventing-cross-tenant-access.html) for the distinction between isolated resources and pooled resources that rely on runtime tenant scoping.

---


**Related questions / 相关问题：** [How do cookie sessions and OIDC tokens establish identity? / Cookie 会话与 OIDC 令牌如何建立身份？](#31.%20How%20do%20cookie%20sessions%20and%20OIDC%20tokens%20establish%20identity?%20/%20Cookie%20%E4%BC%9A%E8%AF%9D%E4%B8%8E%20OIDC%20%E4%BB%A4%E7%89%8C%E5%A6%82%E4%BD%95%E5%BB%BA%E7%AB%8B%E8%BA%AB%E4%BB%BD%EF%BC%9F) covers credentials and login; [Which web security control protects each browser boundary? / 哪种 Web 安全控制保护哪条浏览器信任边界？](#32.%20Which%20web%20security%20control%20protects%20each%20browser%20boundary?%20/%20%E5%93%AA%E7%A7%8D%20Web%20%E5%AE%89%E5%85%A8%E6%8E%A7%E5%88%B6%E4%BF%9D%E6%8A%A4%E5%93%AA%E6%9D%A1%E6%B5%8F%E8%A7%88%E5%99%A8%E4%BF%A1%E4%BB%BB%E8%BE%B9%E7%95%8C%EF%BC%9F) separates TLS, XSS, CSRF, CORS, and framing; [How do web services limit denial-of-service impact? / Web 服务如何限制拒绝服务的影响？](#33.%20How%20do%20web%20services%20limit%20denial-of-service%20impact?%20/%20Web%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%8B%92%E7%BB%9D%E6%9C%8D%E5%8A%A1%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F) covers bounded public work; [How do parameterized queries prevent SQL injection? / 参数化查询如何防止 SQL 注入？](#34.%20How%20do%20parameterized%20queries%20prevent%20SQL%20injection?%20/%20%E5%8F%82%E6%95%B0%E5%8C%96%E6%9F%A5%E8%AF%A2%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20SQL%20%E6%B3%A8%E5%85%A5%EF%BC%9F) and [How should passwords be stored against offline guessing? / 如何存储密码以抵抗离线猜测？](#35.%20How%20should%20passwords%20be%20stored%20against%20offline%20guessing?%20/%20%E5%A6%82%E4%BD%95%E5%AD%98%E5%82%A8%E5%AF%86%E7%A0%81%E4%BB%A5%E6%8A%B5%E6%8A%97%E7%A6%BB%E7%BA%BF%E7%8C%9C%E6%B5%8B%EF%BC%9F) cover server-side data and credential boundaries.

**See also / 另见：** [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#16.%20How%20does%20a%20browser%20request%20reach%20an%20HTTP%20response?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F) covers browser request and transport context; [Browser Storage and Communication / 浏览器存储与通信](../../frontend/browser-apis/browser-storage-and-communication.md) covers client storage and messaging risks.

**Sources / 来源：** [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [AWS SaaS Lens: Preventing cross-tenant access](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/preventing-cross-tenant-access.html). Security guidance checked 2026-10-15. The SQLite example uses synthetic identities and data; it is not credential-validation code.
## 31. How do cookie sessions and OIDC tokens establish identity? / Cookie 会话与 OIDC 令牌如何建立身份？

**Core answer / 核心回答：** A cookie usually carries an opaque session identifier that the server resolves; a bearer token carries a credential the resource server validates. OIDC adds an identity layer to OAuth, while the application still creates its own session and authorizes each protected action. Choose storage, lifetime, revocation, and callback checks for the client and threat model. / Cookie 通常承载由服务端解析的不透明会话标识；Bearer token 则携带资源服务器验证的凭据。OIDC 在 OAuth 上加入身份层，但应用仍要建立自己的会话，并逐项授权受保护操作。应按客户端和威胁模型设计凭据存储、生命周期、撤销与回调校验。

**Key terms / 关键术语：** session identifier / 会话标识；bearer token / Bearer 令牌；JWT / JSON Web Token；OIDC / OpenID Connect；authorization code / 授权码；PKCE / 授权码交换证明；state / 状态值；nonce / 随机数；refresh token / 刷新令牌。

### Cookies vs. tokens — which to use for authentication? / Cookie 会话与令牌应如何选择？

**Cookie 会话与令牌 / Cookie sessions and tokens** are transport and session choices, not two complete security models. Choose according to the clients, domain boundaries, revocation needs, and threat model.

A server-side session commonly works like this:

1. The user authenticates; the server creates a session and stores its state.
2. The server returns an opaque session identifier in a cookie.
3. The browser sends that cookie only when its domain, path, security, SameSite, and request rules match.
4. The server resolves the session and performs authorization for the requested action.

For a session cookie, consider:

- **HttpOnly** prevents page JavaScript from reading the cookie through APIs such as `document.cookie`. It does not stop injected JavaScript from making authenticated requests as the user.
- **Secure** limits transmission to secure channels such as HTTPS.
- **SameSite=Strict, Lax, or None** controls cookie sending in cross-site contexts. It is a site-level browser rule, not an origin or authorization boundary. Specify the value; browser defaults can vary. `SameSite=None` requires `Secure`.
- Cookie scope and size have implementation constraints; do not use `Domain` or `Path` as authorization checks.

A bearer token is presented by the client, commonly in an `Authorization: Bearer` header. A JWT is one token format: a signed JWT normally protects integrity, but its claims are readable unless it is encrypted. A valid signature proves that a trusted key signed the token; it does not by itself authorize every action. Verifiers must validate the expected algorithm, issuer, audience, token type, and time claims according to the application protocol. Use short-lived tokens and a deliberate rotation or revocation strategy where needed.

A JWT can carry claims without a per-request session lookup, but revocation and fresh permission changes then need an explicit design. The JWT format does not bypass browser origin rules or CORS. A token stored in browser-accessible storage can be read by injected JavaScript; an HttpOnly cookie reduces that direct theft path but still needs a CSRF design. Neither storage choice fixes XSS or authorization flaws.

---

### What is Single Sign-On (SSO), and how does it work?

**单点登录 / Single Sign-On** lets a user authenticate through an identity provider and establish sessions with multiple relying applications. Each application still validates the protocol response and applies its own authorization rules.

OAuth 2.0 is an authorization framework for delegated access; OAuth alone is not an authentication protocol. **OpenID Connect / OpenID Connect 身份层** builds an identity layer on OAuth 2.0 and defines the ID Token. An access token and an ID Token serve different purposes: do not treat either as proof for an unrelated audience.

In a typical redirect flow, the relying application creates a login request, the identity provider authenticates the user, and the application validates the response before creating its own session. Protocol details matter: validate the redirect target and issuer, and apply the relevant state, nonce, signature, and audience checks for the flow.

See [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html), [RFC 9700, OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html), and [RFC 8725, JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html).

#### Authorization-code + PKCE callback / 授权码 + PKCE 回调

When an application needs federated sign-in, OpenID Connect uses OAuth's authorization-code flow with the `openid` scope. Plain OAuth grants delegated API access; it does not define an ID Token or an authentication result for the client.

1. The client creates a one-time `code_verifier` and derives `code_challenge = BASE64URL(SHA-256(ASCII(code_verifier)))` using `S256`. It keeps the verifier with the browser's pending login transaction. It also normally creates an unpredictable `state` value bound to that browser transaction; an OIDC client may create a `nonce` if it wants to bind the returned ID Token to this request.
2. The client redirects the browser to the authorization endpoint with `response_type=code`, its `client_id`, an exactly registered `redirect_uri`, `scope=openid` (plus only the API scopes it needs), `state`, `code_challenge`, and `code_challenge_method=S256`. It includes `nonce` only if the flow uses it.
3. After authenticating the user and obtaining any required consent, the authorization server redirects to the registered callback with a short-lived, one-use authorization code and the `state` value, if sent. The callback checks and consumes its stored `state` before continuing. If the client uses multiple authorization servers, it also applies an issuer or equivalent mix-up defense.
4. The client sends the code, the same `redirect_uri`, and its original `code_verifier` to the token endpoint; a confidential client also authenticates there when required. The authorization server recomputes the challenge and rejects a code redemption whose verifier does not match. The code alone is therefore insufficient for an interceptor to redeem.
5. In the selected OIDC Authorization Code Flow, a successful token response includes an ID Token and an Access Token; a Refresh Token is optional. The client validates the ID Token before establishing its own session. The API validates the access token it receives separately.

These values solve different problems and are not all mandatory in every flow:

- **`state` / 请求状态** is an opaque value for correlating a redirect with the initiating browser transaction and often restoring a local return path. OAuth clients must prevent callback CSRF, but a literal `state` parameter is not the only permitted defense: RFC 9700 allows a client that has confirmed PKCE support to rely on PKCE for CSRF protection; in OIDC, `nonce` can also provide that protection. If the client sends `state`, it must bind and check it instead of trusting a callback value.
- **`nonce` / 随机数** binds an ID Token to an OIDC authentication request and helps detect replay. It is optional in the OIDC Authorization Code Flow; when sent, the provider must return it in the ID Token and the client must compare it. Other OIDC flows have different requirements.
- **`code_verifier` / PKCE验证值** is the secret the client keeps and later presents at the token endpoint. The authorization request carries only its derived challenge. RFC 9700 requires PKCE for public clients and recommends it for confidential clients; use `S256`, not a method that reveals the verifier.

**Token use and lifecycle / 令牌用途与生命周期：** An **ID Token / 身份令牌** tells the OIDC client about an authentication event; it is not an API credential. Validate it under the OIDC profile: exact expected issuer, a trusted audience containing this client's ID (and `azp` when applicable), expiration, a matching `nonce` when one was sent, and normally its signature with the configured algorithm and appropriate verification key. OIDC Core §3.1.3.7(6) permits a narrow exception in the Authorization Code Flow: if the client receives the ID Token by direct communication with the Token Endpoint and validates that endpoint's TLS server identity, it may use that TLS validation to validate the issuer instead of checking the token signature. The other ID Token checks still apply, and ID Tokens received through other paths require signature validation. An **access token / 访问令牌** is for a resource server. That server checks the expected issuer, its own API audience, expiration, and allowed scope/action; follow the issuer's contract, verifying the signature and claims for a JWT access-token profile or using the trusted introspection/lookup mechanism for an opaque token. Decoding a JWT is not validation.

A refresh token is presented to the authorization server's token endpoint to obtain a replacement access token; it is not sent to the API. Treat it as a high-value credential. RFC 9700 requires public clients to use refresh-token rotation or sender constraint. If the authorization server supports a revocation endpoint, a client can request revocation of a token; resource servers may learn of that change at different times. A locally verified, self-contained access token may remain accepted until its expiry unless the resource server also checks revocation state. Ending the application's own session and ending an identity-provider session are separate operations.

**Core idea / 核心要点：** OAuth authorization grants access to an API; OIDC tells a client who authenticated; the application still decides whether that identity may perform an action now. PKCE protects code redemption, and runtime authorization protects application data.

**Mechanism in Chinese / 机制要点：** PKCE 把授权码与客户端保留的 verifier 配对；state 关联回调与发起的登录事务，若发送就必须校验，而已确认支持 PKCE 的客户端可按 RFC 9700 依 PKCE 防回调 CSRF。OIDC Code Flow 的 nonce 可选，若发送则须与 ID Token 中的值匹配。客户端验证 ID Token 后建立自己的会话，API 则独立验证面向自身的 access token，并按当前主体、租户和权限做运行时授权。refresh token 只向授权服务器换取新 access token；撤销传播可能有延迟，应用会话、IdP 会话和 API 对已签发 access token 的接受边界要分别处理。

See [OpenID Connect Core 1.0, incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html), [RFC 9700, OAuth 2.0 Security Best Current Practice (January 2025)](https://www.rfc-editor.org/rfc/rfc9700.html), [RFC 7636, Proof Key for Code Exchange (September 2015)](https://www.rfc-editor.org/rfc/rfc7636.html), [RFC 7009, OAuth 2.0 Token Revocation (August 2013)](https://www.rfc-editor.org/rfc/rfc7009.html), and [RFC 8725, JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html).


**Related notes / 相关笔记：** [Cross-tenant authorization / 跨租户资源授权](#30.%20How%20do%20you%20prevent%20cross-tenant%20access%20across%20a%20web%20request?%20/%20%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20Web%20%E8%AF%B7%E6%B1%82%E8%B7%A8%E7%A7%9F%E6%88%B7%E8%AE%BF%E9%97%AE%EF%BC%9F) uses the validated subject to resolve current tenant membership; [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#16.%20How%20does%20a%20browser%20request%20reach%20an%20HTTP%20response?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F) covers cookie fields and browser-origin transport.

**Sources / 来源：** [OpenID Connect Core 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html), [RFC 9700, OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html), [RFC 7636, PKCE](https://www.rfc-editor.org/rfc/rfc7636.html), [RFC 7009, Token Revocation](https://www.rfc-editor.org/rfc/rfc7009.html), [RFC 8725, JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html), and [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html). Guidance checked 2026-10-15. The Authorization Code Flow ID Token validation exception was checked against OIDC Core on 2026-10-27.
## 32. Which web security control protects each browser boundary? / 哪种 Web 安全控制保护哪条浏览器信任边界？

These controls address different threats: TLS protects data in transit and authenticates a server; output handling prevents injected script from becoming active content; CSRF defenses protect cookie-authenticated actions; CORS controls whether browser script may read a cross-origin response; framing policy limits deceptive embedding. None substitutes for server-side authentication or authorization. / 这些控制处理不同威胁：TLS 保护传输并认证服务器；输出处理避免注入脚本成为活动内容；CSRF 防护保护使用 Cookie 凭据的操作；CORS 控制浏览器脚本能否读取跨源响应；框架策略限制欺骗性嵌入。它们都不能替代服务端身份认证或授权。

**Key terms / 关键术语：** TLS / 传输层安全；XSS / 跨站脚本；CSRF / 跨站请求伪造；CORS / 跨源资源共享；CSP / 内容安全策略；frame-ancestors / 可嵌入来源策略。

~~~mermaid
flowchart LR
    Network[Network attacker] -->|TLS| Channel[Confidential and integrity-protected channel]
    Untrusted[Untrusted output] -->|context encoding and sanitization| Page[Rendered page]
    CrossSite[Cross-site action with ambient cookie] -->|CSRF token and origin checks| StateChange[Authorized state change]
    OtherOrigin[Other origin script] -->|CORS response policy| Read[Browser may expose response]
    Frame[Deceptive framing site] -->|frame-ancestors| Embed[Allowed embedding only]
~~~

### How does HTTPS protect against man-in-the-middle attacks?

**HTTPS / TLS** protects data in transit against network eavesdropping and tampering when the connection is correctly configured and the client validates the server. In a certificate-authenticated TLS 1.3 handshake, key agreement derives traffic keys; the server's certificate and handshake signature authenticate the server's key. The server does not simply encrypt a session key with its public key as in older textbook handshake descriptions.

A client checks the certificate chain and that the certificate is valid for the requested hostname, then verifies the handshake. Certificate status and revocation handling depend on the client and deployment, so do not describe revocation checking as a universal guaranteed browser step. A trusted certificate does not authenticate the application's user; application authentication and authorization remain separate.

- **Symmetric cryptography / 对称密码** protects application traffic efficiently after handshake keys are established.
- **Public-key cryptography / 公钥密码** supports key agreement and authentication in the handshake; the TLS 1.3 suite and configuration determine the exact mechanisms.

See [RFC 8446, TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html).

---

### XSS (Cross-Site Scripting) — what is it, how do you prevent it?

**跨站脚本 / XSS** occurs when untrusted data is interpreted as active content in a page. Script that executes in an origin can read data available to that script and make requests from that origin; an HttpOnly cookie blocks direct cookie reading but does not stop such requests.

Use the defense that matches the output context:

1. Render plain text through framework APIs that treat it as text, and encode values for their HTML, attribute, URL, JavaScript, or CSS context.
2. If user-authored rich HTML is required, sanitize it with a maintained HTML sanitizer and keep the allowed markup narrow.
3. Avoid inserting untrusted strings into `innerHTML`, `document.write`, inline event handlers, `eval`, or `new Function`. Framework escape defaults do not protect deliberate raw-HTML escape hatches.
4. Add a carefully tested Content Security Policy as defense in depth. Nonce- or hash-based strict policies can restrict script execution; an allowlist such as `script-src 'self'` alone is not a universal XSS fix.

Before assigning an untrusted value to `href` or `src`, validate the complete URL's scheme and destination against the application's policy (for example, reject `javascript:`); output encoding for the attribute does not replace URL validation.

CSP can reduce the impact of some injection paths, but it does not replace safe rendering and sanitization. See OWASP's [XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) and [Content Security Policy](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html) guidance.

---

### CSRF (Cross-Site Request Forgery) — what is it, how do you prevent it?

**跨站请求伪造 / CSRF** abuses ambient browser credentials: a site can cause a browser to send some cross-site requests, and the browser may attach cookies that match the destination. The attacker often cannot read the response, but reading it is not required to cause a state change.

For state-changing cookie-authenticated requests, use an application-validated CSRF token or an equivalent well-reviewed pattern. Check the request origin where appropriate, and use SameSite as defense in depth. Do not mutate state on safe methods such as GET. SameSite=Lax still permits some top-level safe-method navigations, and sibling subdomains can be same-site; it does not replace authorization or every CSRF defense.

**SameSite=None requires Secure.** Also account for legitimate cross-site login and embedded flows rather than silently weakening checks. See the [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

---

### What is CORS?

**跨源资源共享 / Cross-Origin Resource Sharing (CORS)** is a browser protocol that controls when a script may read a cross-origin response. It is not authentication, authorization, or a general firewall: some cross-origin requests can still be sent even when browser JavaScript cannot read the response, and non-browser clients do not enforce CORS.

For a credentialed browser request, the client must opt in to credentials and the response must name an allowed origin rather than `Access-Control-Allow-Origin: *`, with `Access-Control-Allow-Credentials: true`. Preflight requests are checked separately. Use an explicit origin allowlist; reflecting arbitrary Origin values can expose credentialed responses.

CORS does not make an endpoint private. Authenticate and authorize the server request even if the intended browser client is the only one expected to call it. See the [WHATWG Fetch Standard, CORS protocol and credentials](https://fetch.spec.whatwg.org/#cors-protocol-and-credentials).

---

### Clickjacking — what is it, how do you prevent it?

**点击劫持 / Clickjacking** tricks a user into interacting with a page framed beneath or inside deceptive content. Use the CSP `frame-ancestors` directive to state which sites may embed the page; use `X-Frame-Options` where legacy client support requires it. These headers control framing, not user authorization.

For example, `Content-Security-Policy: frame-ancestors 'self'` permits framing by the same origin. Set a policy that fits legitimate embedding requirements and test the application paths that must remain embeddable.

---


**Related notes / 相关笔记：** [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#16.%20How%20does%20a%20browser%20request%20reach%20an%20HTTP%20response?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F) owns TLS handshake and CORS browser mechanics; [Cross-tenant authorization / 跨租户资源授权](#30.%20How%20do%20you%20prevent%20cross-tenant%20access%20across%20a%20web%20request?%20/%20%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20Web%20%E8%AF%B7%E6%B1%82%E8%B7%A8%E7%A7%9F%E6%88%B7%E8%AE%BF%E9%97%AE%EF%BC%9F) owns user identity and server-side permission checks.

**Sources / 来源：** [RFC 8446, TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html); OWASP [XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html), [Content Security Policy](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html), and [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html); [WHATWG Fetch, CORS protocol and credentials](https://fetch.spec.whatwg.org/#cors-protocol-and-credentials). Security guidance checked 2026-10-15.
## 33. How do web services limit denial-of-service impact? / Web 服务如何限制拒绝服务的影响？

Distributed denial-of-service attacks use traffic or expensive requests to exhaust network, service, or application resources. Mitigation depends on the attack layer and available capacity; no single application control guarantees protection. Use layered edge filtering and provider capacity, rate limits and quotas, caching where it is safe, bounded work, and monitoring. Application code can reject abusive work early, but large traffic floods need network and provider-level capacity as well. / 分布式拒绝服务攻击通过流量或高成本请求耗尽网络、服务或应用资源。缓解措施取决于攻击层级和可用容量，单一应用控制不能保证防护。应组合边缘流量过滤与服务商容量、速率限制和配额、安全场景中的缓存、有界工作及监控。应用代码可以尽早拒绝滥用请求，但大规模流量洪峰还需要网络和服务商层的容量。

**Key terms / 关键术语：** denial of service / 拒绝服务；rate limit / 速率限制；quota / 配额；admission control / 准入控制；bounded work / 有界工作。

**Sources / 来源：** CISA [Understanding and Responding to Distributed Denial-of-Service Attacks](https://www.cisa.gov/sites/default/files/2024-03/understanding-and-responding-to-distributed-denial-of-service-attacks_508c.pdf), checked 2026-11-05, for layered mitigation and rate limitation.

**Related notes / 相关笔记：** [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) explains worker slots, admission, and queue limits; [API timeout and safe retry / API 超时后的结果确认与安全重试](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) explains how retries can amplify overload.
## 34. How do parameterized queries prevent SQL injection? / 参数化查询如何防止 SQL 注入？

SQL injection happens when untrusted data is interpreted as part of SQL syntax. Validate input for usability, but make the security boundary at the server: parameterized queries supply values separately from SQL text. Identifiers or sort directions that cannot be bound as values must come from a fixed allowlist. Query parameterization prevents one class of command injection; authorization is a separate decision. / SQL 注入发生在不可信数据被解释为 SQL 语法的一部分时。输入校验可以改善可用性，但安全边界应在服务端：参数化查询把值与 SQL 文本分开提供。无法作为值绑定的标识符或排序方向必须来自固定白名单。参数化查询防止一类命令注入；授权仍是独立判断。

**Key terms / 关键术语：** parameterized query / 参数化查询；SQL syntax / SQL 语法；allowlist / 白名单；authorization / 授权；least privilege / 最小权限。

On the server, bind values instead of concatenating them into the query. An ORM helps only when its query path uses safe parameterization; raw query construction can still be vulnerable. Parameterization does not prove that the caller may read or modify the selected record. Give each database account only the tables and operations it needs; safe values do not justify connecting as an administrator.

The frontend can validate inputs for usability, but client-side checks are bypassable and are not a security boundary. Validate and authorize again where the server constructs the data operation.

**Related notes / 相关笔记：** [Database constraints and indexes / 数据库约束与索引](#14.%20How%20do%20database%20constraints%20and%20indexes%20shape%20data%20access?%20/%20%E6%95%B0%E6%8D%AE%E5%BA%93%E7%BA%A6%E6%9D%9F%E5%92%8C%E7%B4%A2%E5%BC%95%E5%A6%82%E4%BD%95%E5%A1%91%E9%80%A0%E6%95%B0%E6%8D%AE%E8%AE%BF%E9%97%AE%EF%BC%9F) explains engine-side data invariants; [Cross-tenant authorization / 跨租户资源授权](#30.%20How%20do%20you%20prevent%20cross-tenant%20access%20across%20a%20web%20request?%20/%20%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20Web%20%E8%AF%B7%E6%B1%82%E8%B7%A8%E7%A7%9F%E6%88%B7%E8%AE%BF%E9%97%AE%EF%BC%9F) explains authorization that parameter binding cannot provide.

**Sources / 来源：** OWASP [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html) and its [least-privilege guidance](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html#least-privilege), checked 2026-10-15.
## 35. How should passwords be stored against offline guessing? / 如何存储密码以抵抗离线猜测？

Store a salted password hash from a password-storage algorithm designed to make guessing expensive, such as Argon2id. A unique random salt is stored with each hash; it is not a secret. A fast digest such as SHA-256 alone is not a password-storage scheme. Use a maintained library and tune its cost for the deployment, then combine it with online attempt throttling. / 使用专为提高猜测成本而设计的密码存储算法保存带盐哈希，例如 Argon2id。每个哈希保存一个唯一随机 salt；salt 不是秘密。单独使用 SHA-256 这类快速摘要并非密码存储方案。使用维护良好的库并根据部署调节成本，再配合在线尝试限速。

**Key terms / 关键术语：** password hash / 密码哈希；salt / 盐；Argon2id / Argon2id 算法；pepper / 秘密 pepper；offline guessing / 离线猜测；rate limiting / 速率限制。

A pepper may add defense in depth when stored separately from the password database, but it is not a replacement for a suitable password hash. Keep the pepper in a secret store with its own rotation and access policy. Use password policy and attempt throttling to reduce online guessing as well.

**Related notes / 相关笔记：** [Web Security and Authentication / Web安全与身份认证](#30.%20How%20do%20you%20prevent%20cross-tenant%20access%20across%20a%20web%20request?%20/%20%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20Web%20%E8%AF%B7%E6%B1%82%E8%B7%A8%E7%A7%9F%E6%88%B7%E8%AE%BF%E9%97%AE%EF%BC%9F) covers the login/session context; [How do web services limit denial-of-service impact? / Web 服务如何限制拒绝服务的影响？](#33.%20How%20do%20web%20services%20limit%20denial-of-service%20impact?%20/%20Web%20%E6%9C%8D%E5%8A%A1%E5%A6%82%E4%BD%95%E9%99%90%E5%88%B6%E6%8B%92%E7%BB%9D%E6%9C%8D%E5%8A%A1%E7%9A%84%E5%BD%B1%E5%93%8D%EF%BC%9F) covers request rate and resource limits.

**Sources / 来源：** OWASP [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) and [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html), checked 2026-10-15.
## 36. A request timed out: how can I confirm its outcome and retry safely? / 请求超时后，如何确认操作结果并安全重试？

A timeout or disconnected connection means the caller did not receive a result; by itself, it does not show whether the server applied the operation. Give the operation a stable identity, persist that identity with the local effect in one transaction, and let the caller query the authoritative status or repeat the same request with the same key. Carry one end-to-end deadline through the work, bound retries, and treat cancellation as a request for work to stop rather than proof that a remote side effect was undone. / 超时或连接断开只表示调用方没有收到结果，本身不能说明服务端是否已经执行操作。为操作指定稳定标识，在一个事务中持久化该标识和本地效果，并让调用方查询权威状态，或使用相同 key 重试原请求。沿整条调用链传递同一个截止时间并限制重试次数；取消表示请求工作停止，不代表远端副作用已经撤销。

**Key terms / 关键术语：** timeout / 超时；deadline / 截止时间；unknown outcome / 结果未知；idempotency key / 幂等键；retry / 重试；backoff / 退避；jitter / 抖动；cancellation / 取消。

### Where a timeout leaves the caller / 超时后调用方处于什么状态

A **timeout** limits one wait or operation. An end-to-end **deadline** is the latest time the whole request may finish. Starting a new full timeout for each downstream call can let a multi-hop request run far beyond the caller's budget. Pass a deadline or remaining time downstream, reserve time for cleanup and the response, and choose limits from measured latency and the product's failure policy; there is no universal timeout value. Connection setup and response waiting may need separate limits when a client library treats them separately.

When a write is accepted but the response is lost, the caller's **outcome is unknown**. It cannot distinguish “the request never arrived” from “the effect committed and only the response was lost.” A **202 Accepted** response is a different, explicit contract: it says processing was accepted but is not complete. Return a stable operation or job URL so the client can query later; HTTP does not send a later response over the original connection. The endpoint's response and error shapes belong to [HTTP API Contracts / HTTP API契约](#26.%20How%20do%20you%20design%20a%20predictable%20HTTP%20API%20contract?%20/%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F), while method-level semantics belong to [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#16.%20How%20does%20a%20browser%20request%20reach%20an%20HTTP%20response?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F).

~~~mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant D as Database
    C->>A: Write with operation key
    A->>D: Commit effect and operation result together
    D-->>A: Commit completed
    A--xC: Response is lost
    Note over C: Outcome is unknown
    alt Read-only status lookup
        C->>A: Query the operation
        A->>D: Read recorded outcome
        D-->>A: Recorded result
        A-->>C: Return status and outcome
    else Retry under the same-key contract
        C->>A: Repeat the request with the same key
        A->>D: Match the key and fingerprint
        D-->>A: Recorded result for this write
        A-->>C: Return the recorded outcome
    end
~~~

This diagram follows a committed write whose reply was lost. A read-only status lookup can report that a key is absent and never starts the write. Only a retried write under its explicit idempotency contract can execute when the key is absent. If the effect is in another service, use that service's idempotency contract or a reconciliation path.

### Make a repeated request safe / 让重复请求安全

HTTP defines **idempotent methods** by the intended effect of multiple identical requests. That permits a client to retry an idempotent request after a communication failure, but does not erase other per-request side effects such as audit logging. A timeout alone is not a reason to automatically repeat a non-idempotent operation.

For a write that needs retry support, accept an **idempotency key** or operation ID and define its scope, retention window, and relationship to request parameters. Store a normalized-request fingerprint with the key. The service should return the recorded result for the same key and same request; reuse with different parameters should be rejected or handled by an explicitly documented rule. The deduplication record and the local database effect must share one atomic transaction boundary. A key stored separately from the effect can still permit duplicate work if a crash occurs between the two writes.

**Hypothetical example / 假设示例：** A refund service accepts a request, records the refund, then loses its response before the client deadline. The client cannot tell whether the refund committed. If it retries with the same operation key, the service can return the recorded refund result instead of issuing another refund—provided the key record and refund state were committed together and the service retains that record for the documented retry window. Without those assumptions, the caller must query or reconcile the outcome rather than blindly issue a second refund. This example is illustrative, not a provider contract.

### Bound retries by the remaining deadline / 按剩余截止时间约束重试

Retry only when a failure may be transient and the operation is safe to repeat, or when the client can determine the first attempt was not applied. Use a capped exponential schedule with randomized jitter to spread attempts rather than synchronizing them:

~~~text
cap(n)  = min(max_delay, base_delay × 2^n)
wait(n) = random value from 0 through cap(n)  # one full-jitter variant
~~~

The base delay, cap, attempt limit, and total retry budget are service choices derived from the deadline and downstream capacity, not universal defaults. Stop when the remaining deadline cannot fit another useful attempt. Avoid retries at several layers: if five layers each make three attempts, one logical request can create 3⁵ = 243 downstream attempts. One deliberate retry boundary is easier to bound and observe.

### Treat cancellation as cooperative / 把取消视为协作式信号

Cancellation tells work that its result is no longer needed. Propagate it to downstream calls and check it at safe points so unnecessary computation stops and resources are released. Support depends on each runtime and API; cancellation is often cooperative. It does not prove a remote service stopped or undid a side effect. A client disconnect can trigger a local cancellation signal in some frameworks, but the server must still rely on authoritative operation state to determine whether a write committed.

The account-report example shows the full durable contract: the client receives **202** and a status URL, retries return one job for the same scoped key, and the job record remains authoritative after disconnect. See [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#46.%20How%20would%20you%20design%20a%20durable%20account%20report?%20/%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F). For a durable AI run and its checkpoint/reconciliation boundary, see [AI Application Architecture / AI 应用架构](../../ai-engineering/systems/ai-application-architecture.md); for how a browser presents disconnect, reconnect, and final states, see [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md).

Observe the request boundary separately: accepted and rejected requests, deadline exhaustion, timeout and cancellation counts, idempotent replays and key conflicts, and final operation or job outcomes. These show whether users received a result, an explicit pending state, an overload response, or an unresolved outcome. Queue depth, oldest-message age, worker slots, redelivery, and acknowledgement signals belong to the corresponding capacity and broker boundaries.

Capacity and queue delivery are separate questions. [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) covers admission, backpressure, and the full synthetic report estimate. [Publisher confirms and consumer acknowledgements / 发布者确认和消费者确认分别证明什么？](#38.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) explains broker confirmation and redelivery boundaries.

**Related notes / 相关笔记：** [Data Access and Connection Pools / 数据访问与连接池](#28.%20How%20do%20you%20scope%20an%20ORM%20Session%20and%20diagnose%20pool%20exhaustion?%20/%20%E5%A6%82%E4%BD%95%E9%99%90%E5%AE%9A%20ORM%20Session%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E5%B9%B6%E8%AF%8A%E6%96%AD%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F) explains how request and transaction lifetimes borrow database connections; [Database Fundamentals / 数据库基础](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F) covers the constraints and transaction semantics that make a local deduplication boundary possible.

**Sources / 来源：** [RFC 9110 §9.2.2, Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) and [§15.3.3, 202 Accepted](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3), checked 2026-11-05; AWS Builders' Library, [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) and [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), checked 2026-10-15; gRPC guides to [Deadlines](https://grpc.io/docs/guides/deadlines/) and [Cancellation](https://grpc.io/docs/guides/cancellation/).
## 37. How do you size and bound an asynchronous work pipeline? / 如何估算并限制异步工作管线？

Size a pipeline by naming its system boundary, arrival rate, time in each stage, resource held by each unit of work, and maximum waiting work. Little's Law estimates average work in flight in a stable system; it does not promise peak throughput or tail latency. A queue gives work somewhere durable to wait, but only admission control and backpressure keep that wait bounded. / 估算管线时，要明确系统边界、到达速率、各阶段耗时、每个任务占用的资源和最大等待量。Little 定律估算稳定系统中的平均在途工作；它不承诺峰值吞吐量或尾部时延。队列让工作可以持久等待，但只有准入控制和背压才能限制等待规模。

**Key terms / 关键术语：** admission control / 准入控制；backpressure / 背压；in-flight work / 在途工作；queue age / 队列等待时长；Little's Law / Little 定律；connection pool ceiling / 连接池配置上限。

### Bound work before estimating replicas / 先限制工作量，再估算副本数

Bound in-flight requests, worker count, and every waiting queue. An unbounded queue turns overload into growing memory use and delay. When a bound is reached, choose an explicit policy: wait within the request deadline, reject, defer to durable storage, or shed work that can safely be dropped. Include queue wait in the request's latency budget and report overload distinctly from successful completion.

~~~mermaid
flowchart LR
    S[Submission] --> Rate{Rate budget available?}
    Rate -->|no| Reject[Reject without claiming acceptance]
    Rate -->|yes| Slots{Shared waiting slot available?}
    Slots -->|no| Reject
    Slots -->|yes| Reserve[Atomically reserve one job slot]
    Reserve --> Outbox[Outbox or durable queue]
    Outbox --> Start[Worker starts job]
    Start --> Release[Release reservation once]
    Outbox -->|publish retry or broker copy| Outbox
~~~

For a durable job, count the logical job once while it is in the outbox or waiting in the broker. Moving the same job between those systems does not consume a second waiting slot. Release the reservation through a guarded transition when the job starts or becomes terminal before starting. If a retry or lease recovery returns it to waiting, reserve a slot again before requeueing. The account-report case uses this rule and defines the database transitions in [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#46.%20How%20would%20you%20design%20a%20durable%20account%20report?%20/%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F).

Under steady-state conditions, Little's Law is:

~~~text
average work in flight = arrival rate × average time in system
~~~

The system boundary must include the queue if the arrival rate and elapsed time include queued work. For example, 40 requests/s × 0.2 s in the chosen system implies about 8 average in-flight requests. This is a planning check, not a universal concurrency cap: bursts, latency distributions, retries, and downstream limits still need measurement.

### Synthetic account-report sizing example / 合成账户报表容量估算

**Assumptions / 假设：** Consider a teaching workload with an average of 5 submissions/s and a 10-minute peak of 20/s. Each validated request is 8 KiB, and its submission transaction holds a database connection for 10 ms. A worker makes 12 sequential indexed reads, holding a database connection for 20 ms per read. Mean worker time is 6 s, the average report is 128 KiB, and job metadata is 2 KiB. These are synthetic inputs for arithmetic, not observed traffic, service measurements, an SLO, or a recommended default.

#### Estimate worker slots and admission / 估算 worker 槽位与准入

At the average arrival rate, mean worker concurrency is 5 jobs/s × 6 s = 30 jobs. At the stated peak, offered load would require 20 × 6 = 120 concurrent jobs if every request were admitted.

A plan with 4 worker replicas × 2 processes per replica × 8 active job slots per process has 64 slots. If the slots stayed full, the estimate is 64 / 6 = 10.67 jobs/s; at a planning utilization of 70%, it is 64 × 0.70 / 6 = 7.47 jobs/s. A 7 jobs/s token-bucket admission rate uses an estimated 7 × 6 / 64 = 65.6% of slots. These values are starting limits to test, not measured capacity guarantees.

Bound acceptance separately from waiting work. In this example, allow a sustained 7 submissions/s with a burst of 30 and at most 240 accepted-but-not-started jobs across the outbox and broker queue. Reserve one shared slot per job before returning **202 Accepted**; moving a job from outbox to broker does not count it twice. Release the reservation once when work starts or becomes terminal before starting. If all workers stop, the bound fills after a short interruption; once the waiting allowance is full or the rate limit is exhausted, return a documented overload response without claiming the request was accepted.

At 20 offered submissions/s for 600 s, 12,000 requests arrive. A token bucket admitting at most 7 × 600 + 30 = 4,230 in that interval leaves at least 7,770 not admitted, assuming the shared waiting allowance and other limits do not reject sooner. A rejected or ambiguous submission still follows the deadline and idempotency rules in [API timeout and safe retry / API 超时后的结果确认与安全重试](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F).

#### Budget database connections / 预算数据库连接

Budget every process-local pool, including overflow, before increasing replicas:

| Process group | Maximum calculation | Possible connections |
|---|---:|---:|
| API: 4 replicas, 2 processes each, pool 8 + overflow 2 | 4 × 2 × (8 + 2) | 80 |
| Workers: 4 replicas, 2 processes each, pool 8 + overflow 2 | 4 × 2 × (8 + 2) | 80 |
| Other services using the same database | Assumed allocation | 40 |
| Configured application total | 80 + 80 + 40 | 200 |
| Example database connection budget | Assumed total | 240 |
| Unallocated headroom | 240 − 200 | 40 |

This pool ceiling is not a prediction that 200 connections will be busy. Each report uses 12 sequential reads × 0.020 connection-seconds = 0.24 connection-seconds. That implies 5 × 0.24 = 1.2 average checked-out connections for report reads at the average arrival rate, or 20 × 0.24 = 4.8 if the offered peak were admitted; a 10 ms submission transaction adds 0.05 average or 0.2 at that peak. Query fan-out, connection hold time, and real pool behavior must be measured before treating these estimates as resource headroom. The application-level pool ceiling and its per-process scope are explained in [Data Access and Connection Pools / 数据访问与连接池](#28.%20How%20do%20you%20scope%20an%20ORM%20Session%20and%20diagnose%20pool%20exhaustion?%20/%20%E5%A6%82%E4%BD%95%E9%99%90%E5%AE%9A%20ORM%20Session%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E5%B9%B6%E8%AF%8A%E6%96%AD%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F).

#### Estimate result bytes and retention / 估算结果体量与留存

At 5 completed reports/s, 128 KiB per report produces 640 KiB/s of results. Seven days of output retention is:

~~~text
128 KiB × 5/s × 604,800 s ÷ 1,048,576 KiB/GiB ≈ 369 GiB
~~~

This is before compression, replication, and cleanup lag. Two KiB of metadata per job adds about 5.8 GiB per seven days before indexes.

At a sustained 7 completions/s, result volume averages 0.875 MiB/s; this is a long-run planning rate, not an instantaneous upper bound. The permitted 30-job burst could produce 3.75 MiB if all reports complete in one interval, and backlog drain can exceed the current admission rate. At a sustained 20 completions/s, the corresponding long-run result volume is 2.5 MiB/s. Measure result downloads separately from generation and retention.

#### Test the first bottleneck / 验证最先触顶的资源

Under these assumptions, worker slots bind before the estimated database connection count: peak demand needs 120 active jobs while the plan has 64 slots. That does not prove database CPU, storage I/O, or network has spare capacity.

Load-test the representative 8 KiB input, 12-read fan-out, and output sizes. Ramp average traffic, apply the 20/s burst, then test rate rejection, a full queue, slow reads, retries, and worker loss. Record request acceptance latency separately from job queue wait and completion time. Compare distributions such as p50, p95, and p99 for each user-visible stage; the 6 s mean belongs in the concurrency estimate, not as a p95 promise. Track sustained throughput, queue age, busy slots, database checkout wait and CPU, retained bytes, and completed-job outcomes against the service objective before changing pool size or replicas. [Observability, SLOs, and Incident Response / 可观测性、服务目标与事件响应](#39.%20How%20do%20you%20diagnose%20an%20API%20SLO%20violation?%20/%20%E5%A6%82%E4%BD%95%E8%AF%8A%E6%96%AD%20API%20SLO%20%E8%BF%9D%E7%BA%A6%EF%BC%9F) explains how to turn these signals into useful service indicators.

**How would you answer “How many workers do we need?” / 如何回答“需要多少个 worker？”** I would state the workload and service-time assumptions, use Little's Law for mean in-flight jobs, and compare that with a bounded worker plan and pool budget. Here the mean suggests 30 active jobs, but peak demand suggests 120; 64 slots and a 7/s admission limit are hypotheses to test under the expected payload and fan-out. I would measure queue age and stage latency distributions before adding replicas, because the first limit could move to the database or storage. / 我会先说明工作负载和处理时长假设，用 Little 定律估算平均在途任务，再与有界 worker 和连接池预算比较。此例平均负载约需 30 个并发任务，但峰值需求约为 120；64 个槽位和每秒准入 7 个是待压测的假设，应按预期 payload 和扇出测量队列等待及各阶段时延分布，再决定是否扩容，因为首个瓶颈也可能转移到数据库或存储。

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) covers deadline and unknown-outcome policy; [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#46.%20How%20would%20you%20design%20a%20durable%20account%20report?%20/%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F) applies these bounds to a complete service contract; [Queue delivery acknowledgements / 队列确认与重投](#38.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) covers broker delivery state; [AI System Design Interview Questions / AI 系统设计面试题](../../ai-engineering/systems/ai-system-design-interview-questions.md) has a different worked latency allocation and model-stage concurrency estimate.

**Sources / 来源：** Little and Graves, [“Little’s Law Deals with Queuing Systems”](https://web.eng.ucsd.edu/~massimo/ECE158A/Handouts_files/Little.pdf), in *Building Intuition* (2008), pp. 81–82, for the steady-state relation and system boundary; [Google SRE Workbook: Implementing SLOs](https://sre.google/workbook/implementing-slos/), checked 2026-10-15, for latency distributions and percentile-based indicators. The numeric workload and all capacity figures above are synthetic calculations from the stated assumptions.
## 38. What do publisher confirms and consumer acknowledgements prove? / 发布者确认和消费者确认分别证明什么？

A publisher confirm and a consumer acknowledgement cover different handoffs. A publisher confirm says the broker accepted a publish under its own configured rules; it does not say a consumer performed the business operation. A consumer acknowledgement tells the broker that the consumer reached the chosen processing boundary. If either confirmation is lost, work may be repeated, so make the business effect idempotent and acknowledge only after its durable outcome. / 发布者确认和消费者确认覆盖不同的交接边界。发布者确认表示 broker 按自身配置规则接受了消息，并不表示 consumer 已执行业务操作。消费者确认告诉 broker，consumer 已达到系统选定的处理边界。任一确认丢失都可能造成重复处理，因此业务效果应可幂等，并且只有在持久化业务结果后才确认消息。

**Key terms / 关键术语：** publisher confirm / 发布者确认；consumer acknowledgement / 消费者确认；redelivery / 重投；deduplication / 去重；ordering / 顺序；dead-letter queue / 死信队列。

~~~mermaid
sequenceDiagram
    participant P as Publisher
    participant B as Broker
    participant C as Consumer
    participant D as Business store
    P->>B: Publish message
    B-->>P: Confirm broker acceptance
    B->>C: Deliver message
    C->>D: Commit idempotent business effect
    D-->>C: Durable outcome
    C->>B: Acknowledge delivery
    Note over P,B: Lost confirm may cause publisher retry and duplicate publish
    Note over C,B: Crash after commit but before ack may cause redelivery
~~~

The sequence has two separate ambiguity windows. If the broker accepted a publish but its confirmation did not reach the publisher, the publisher may resend and create a duplicate. If the consumer commits its effect and then crashes before acknowledging, the broker may redeliver the message. If the consumer acknowledges before durable work, a crash can lose the work. The application therefore needs stable message or operation identity and an idempotent effect; queue delivery alone is not proof of business completion.

### Publisher confirmation / 发布者确认

Publisher confirms cover the publisher-to-broker boundary under the broker's rules. They do not know whether a consumer received, acknowledged, or completed the message. The publisher must also distinguish a broker confirmation from a routing guarantee: depending on broker and configuration, acceptance by an exchange may not mean that the message reached the intended queue.

With RabbitMQ, a publisher that has not received a confirm when a connection fails cannot know whether the message was accepted; retrying may duplicate it. For routable persistent messages, what the confirm means depends on the message and queue type; consult the configured queue's durability and replication semantics. A confirm is not a transaction across the publisher's database and the broker. Persisting business state and an outbox row together, then publishing from that outbox, handles that separate database-to-broker dual-write problem. The account-report implementation is in [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#46.%20How%20would%20you%20design%20a%20durable%20account%20report?%20/%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F).

### Consumer acknowledgement and redelivery / 消费者确认与重投

Choose the consumer's acknowledgement point from the business completion contract. If processing consists of a database update, make that update idempotent by message ID or operation key. A crash after database commit but before broker acknowledgement can then trigger redelivery without repeating the effect. The database commit and broker acknowledgement usually cannot share one local transaction, so this remaining duplicate window is expected.

With RabbitMQ 4.3 manual acknowledgements, an unacknowledged delivery is requeued when its channel or connection closes. Consumers must be ready for redelivery. This is a broker-specific behavior, not a universal queue rule. Acknowledging before durable work can lose work; acknowledging after durable work can cause redelivery if the acknowledgement is lost, so processing should tolerate duplicates.

A dead-letter queue makes repeatedly failed messages visible only if it is monitored and someone has defined whether to repair, retry, or discard them. Immediate requeue can create a hot retry loop, so define bounded attempts or delayed retry behavior. Keep the application operation's idempotency record and any relevant status query separate from the queue's delivery state.

### Preserve the order the business needs / 保留业务需要的顺序

Concurrent consumers may finish messages in a different order from delivery. A FIFO queue does not automatically serialize all effects across multiple consumers, retries, or partitions. If completion order is a correctness rule, define its scope—often per account or key—and enforce it with a single ordered partition, per-key sequence, conditional state transition, or serialization at the worker. Confirm the chosen broker's exact delivery and ordering contract.

Observe each boundary separately: publish attempts and confirms, unroutable messages, queue depth and oldest-message age, unacknowledged deliveries, retries and redeliveries, acknowledgements, dead-letter volume, and completed business outcomes. A growing oldest-message age indicates delay even while a queue continues accepting work. [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) explains how to constrain the work waiting behind those boundaries.

**Related notes / 相关笔记：** [API timeout and safe retry / API 超时后的结果确认与安全重试](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) covers ambiguous request outcomes and operation idempotency; [How would you design a durable account report? / 怎样设计可持久查询的账户报表？](#46.%20How%20would%20you%20design%20a%20durable%20account%20report?%20/%20%E6%80%8E%E6%A0%B7%E8%AE%BE%E8%AE%A1%E5%8F%AF%E6%8C%81%E4%B9%85%E6%9F%A5%E8%AF%A2%E7%9A%84%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%EF%BC%9F) applies outbox, attempt fencing, and post-outcome acknowledgement to a report job; [Database Fundamentals / 数据库基础](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F) covers the local transaction boundary used to persist business effects.

**Sources / 来源：** RabbitMQ 4.3, [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms) and [Reliability Guide](https://www.rabbitmq.com/docs/reliability), checked 2026-11-05. These references document RabbitMQ's confirm, manual-ack, redelivery, and publisher retry behavior; other brokers have different contracts.
## 39. How do you diagnose an API SLO violation? / 如何诊断 API SLO 违约？

**Core model / 核心模型:** Start from the outcome users need, measure it with a clear service-level indicator, and use correlated metrics, traces, and logs to find which stage is failing. Metrics show the aggregate shape; a trace follows one request across stages; logs explain specific events. / 从用户需要的结果开始，用明确定义的服务等级指标衡量它，再用相互关联的指标、追踪和日志定位故障阶段。指标显示整体趋势，追踪串起单个请求的各阶段，日志说明具体事件。

**Key terms / 关键术语:** service-level indicator (SLI) / 服务等级指标；service-level objective (SLO) / 服务等级目标；service-level agreement (SLA) / 服务等级协议；error budget / 错误预算；trace / 分布式追踪；span / 跨度；cardinality / 基数。

**Core answer / 核心回答：** SLI 是符合资格的用户请求中“好事件 / 总事件”的实测比例；SLO 是该比例在指定时间窗内应达到的目标；SLA 是对外业务协议，可能规定计量方式和未达标后果。例：30 天内 10,000 次有效请求中，9,940 次在 400 ms 内成功，SLI 为 99.4%；若 SLO 为 99.5%，错误预算是 `(1 − 99.5%) × 10,000 = 50` 次坏事件，实际 60 次即超出 10 次。告警后先确认用户影响和分母，再沿 trace 定位慢/失败阶段并查关联日志；根据证据缓解，以用户 SLI 和依赖信号验证恢复，并记录原因与后续改进。

~~~mermaid
flowchart LR
    Metrics[Metric shows user-impact window and scope] --> Trace[Representative trace locates slow or failed stage]
    Trace --> Logs[Correlated logs explain that event]
    Logs --> Mitigate[Choose evidence-based mitigation]
    Mitigate --> Verify[Verify user SLI and dependency recovery]
    Verify --> Learn[Record cause and follow-up]
~~~

### Follow one request through three signals / 用三种信号跟踪一个请求

Consider a generic catalog lookup: `client → API edge → catalog service → cache/database → response`. Instrument the boundaries that make up this user action. Propagate trace context across service calls so spans from the edge, service, and database client can be assembled into one trace. A span is one timed operation; parent-child spans show which sub-operation took time. Context propagation connects spans across process and network boundaries. [OpenTelemetry: traces](https://opentelemetry.io/docs/concepts/signals/traces/) and [context propagation](https://opentelemetry.io/docs/concepts/context-propagation/).

| Signal / 信号 | What it answers / 回答的问题 | Example for the lookup / 查询示例 |
|---|---|---|
| **Metrics / 指标** | Is the service broadly healthy, and when did behavior change? | Count eligible requests and failures; measure end-to-end duration, dependency duration, in-flight work, and resource saturation over time. Metrics aggregate measurements, so they are efficient for trends and alerts. |
| **Traces / 追踪** | Which stage made this particular request slow or unsuccessful? | One trace contains a root request span and child spans for cache and database work. Compare their durations and statuses to see where time accumulated. |
| **Logs / 日志** | What event or decision happened at that stage? | A structured record such as `cache_lookup=miss` or `database_timeout` adds event detail. Include the active `trace_id` and `span_id` when available so the record can be found from the trace. |

Start with the metric to find the affected time window, route, and outcome. Then inspect a representative slow or failed trace and follow its child spans. Use the trace and span identifiers to find detailed log events from the same request. For example, an edge metric may show that catalog lookups are slow, a trace may show most of one request's 700 ms elapsed in the database span, and a correlated log may show that the connection pool waited before timing out. The metric establishes scope, the trace locates the stage, and the log gives event detail. [OpenTelemetry: signals](https://opentelemetry.io/docs/concepts/signals/) describes the three signal types; its [logs guide](https://opentelemetry.io/docs/concepts/signals/logs/) describes correlating logs with active traces and spans.

Signals have different coverage. Metrics can remain useful when traces are sampled, but a missing trace is not proof that no request or failure occurred. Check telemetry freshness and instrumentation coverage before treating silence as recovery.

### Keep telemetry safe and bounded / 让遥测信息安全且有界

Use stable, low-cardinality metric dimensions such as route template (`/catalog/{itemId}`), response class, region, and dependency. Do not attach `request_id`, `trace_id`, user or tenant IDs, raw URL paths, search terms, prompts, or other per-request values to metric measurements. Every distinct dimension combination can create another time series and increase aggregation cost; OpenTelemetry's metrics guide warns that user IDs and raw paths can cause unbounded cardinality. [OpenTelemetry: metrics and cardinality limits](https://opentelemetry.io/docs/concepts/signals/metrics/).

Request and trace identifiers are useful correlation fields in logs and traces, where each record is already about an individual event or operation. Treat them as sensitive linkage data: restrict access and retention, and never log credentials, authorization headers, cookies, or raw user content just to make a failure searchable. Prefer stable route names and bounded result categories; redact or omit fields that are not needed to diagnose the service.

### Define a user outcome and its budget / 定义用户结果与预算

An **SLI** is a measured indicator of a service outcome, commonly a ratio of good events to eligible events. An **SLO** is the target for that indicator over a stated period. An **SLA** is an external business agreement that can specify measurement rules and consequences if commitments are missed; an internal SLO is not automatically an SLA. [Google SRE Workbook: Implementing SLOs](https://sre.google/workbook/implementing-slos/) defines event-based SLIs, explains error budgets, and distinguishes an SLA as a business contract.

**Synthetic example / 合成示例.** Suppose a catalog lookup service chooses the following request-based SLI over a rolling 30-day window:

- **Eligible events:** every authenticated, syntactically valid catalog lookup accepted at the public API edge. Exclude synthetic health checks. Keep service errors, timeouts, and requests with no completed response in the denominator.
- **Good event:** the edge completes a successful response in at most 400 ms from acceptance.
- **SLI:** good eligible events ÷ all eligible events.
- **SLO:** at least 99.5% of eligible events are good in the rolling 30-day window.

If the window contains 10,000 eligible lookups and 9,940 are good, the SLI is `9,940 ÷ 10,000 = 99.4%`. The error budget is `1 − 0.995 = 0.5%`, or `10,000 × 0.005 = 50` bad events for this traffic volume. The 60 bad events observed exceed that budget by 10. This event-based calculation weights each request equally; it does not prove every region or user group had the same experience. The chosen edge measurement also does not include the user's device or network after the edge completes its response. Google SRE recommends specifying both the user outcome and how it is measured, because measurement boundaries change what failures are visible.

The SLI must keep its denominator and eligibility rules stable: dropping timeouts or slow successes would make the number look better while excluding users who did not receive a timely result. Report request volume with the ratio, and inspect meaningful low-cardinality slices such as region or route when an overall number hides a localized failure.

### Alert, investigate, mitigate, and learn / 告警、调查、缓解与复盘

For the example SLO, a focused alert could fire when at least 100 eligible lookups occur in a rolling 10-minute window, fewer than 99% are good, and that condition persists for 5 minutes. A minimum event count reduces noise from tiny samples. The alert should carry the SLI numerator, denominator, time window, affected route/region, and links to the relevant metric and trace views. Page when this user-outcome condition holds; internal component signals help explain the cause.

When it fires:

1. **Confirm impact and scope.** Check event counts, SLI trend, error types, route/region, and recent changes. Make sure telemetry is arriving and the denominator still matches the SLI definition.
2. **Locate the stage.** Compare stage and dependency latency, errors, saturation, and in-flight work. Inspect affected traces, then use trace IDs to read the specific correlated logs. For asynchronous work, inspect queue age and depth as part of [capacity and backpressure](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F). [Broker delivery](#38.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) explains the acknowledgement boundary.
3. **Mitigate the user impact.** Choose the smallest safe action supported by evidence, such as rolling back a change that matches the onset or temporarily reducing load on a saturated dependency. Record the action and its expected effect; do not add retries blindly if they can amplify overload.
4. **Verify recovery.** Confirm that the user-facing SLI returns above the alert threshold with adequate traffic, and check the affected stage and dependency signals for continuing saturation or error growth. A quiet alert alone is not evidence that the service recovered.
5. **Follow up.** Record the user impact and time window, the causal mechanism, the mitigation, and a small set of owned changes to prevent recurrence or improve detection. Link the incident to relevant tests and telemetry gaps.

Use the SLO to guide tradeoffs. For AI-backed flows, pair [production signals](../../ai-engineering/systems/ai-production-observability-and-feedback.md) with task-quality measures from [LLM evaluation](../../ai-engineering/evaluation/llm-evaluation-methods.md). HTTP success and latency describe delivery. Task evaluation establishes whether generated answers are useful or correct.

### Sources / 来源

- OpenTelemetry's unversioned concept pages, checked 2026-10-15: [Signals](https://opentelemetry.io/docs/concepts/signals/) (last modified 2026-03-10), [Observability primer](https://opentelemetry.io/docs/concepts/observability-primer/) (2026-04-23), [Traces](https://opentelemetry.io/docs/concepts/signals/traces/) (2026-01-14), [Metrics](https://opentelemetry.io/docs/concepts/signals/metrics/) (2026-07-02), [Logs](https://opentelemetry.io/docs/concepts/signals/logs/) (2026-08-07), and [Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) (2026-08-10).
- [Google SRE Workbook, Chapter 2: Implementing SLOs](https://sre.google/workbook/implementing-slos/), checked 2026-10-15.
## 40. How do design principles reduce the cost of change without adding needless abstraction? / 设计原则如何降低变化成本而不过度抽象？

Design principles help identify where a likely change would force unrelated code to change. Use a principle when it points to a concrete coupling cost and a boundary that reduces it; adding interfaces, classes, or extension points without a real source of variation merely moves complexity around. **设计原则用于判断一次可能的变化会不会迫使无关代码跟着修改。只有当原则指出了具体耦合成本，并能据此建立有价值的边界时才应用；没有真实变化点却增加接口、类或扩展点，只会把复杂度挪到别处。**

### What are the SOLID principles, and what does each mean?

**SOLID / 面向对象设计原则** is a mnemonic for five related guidelines:

- **S — Single Responsibility Principle / 单一职责原则**: keep a module cohesive around one responsibility or axis of change.
- **O — Open/Closed Principle / 开闭原则**: make a stable part of the design extensible at expected variation points, rather than editing that core for every new case.
- **L — Liskov Substitution Principle / 里氏替换原则**: a subtype must preserve the behavioral expectations clients rely on from its base type.
- **I — Interface Segregation Principle / 接口隔离原则**: clients should depend only on the operations they need.
- **D — Dependency Inversion Principle / 依赖倒置原则**: high-level policy should not depend directly on low-level details; both should depend on abstractions where that boundary pays for itself.

These guidelines can help isolate changes, but applying all of them mechanically can produce needless interfaces and indirection.

#### Single Responsibility Principle (SRP)

A module should group behavior that changes for the same reason. This is not a rule that every method or data field needs a separate class.

~~~javascript
class UserRepository {
  async findById(id) { /* persistence details */ }
}

class UserPage {
  render(user) { /* presentation */ }
}
~~~

Separating persistence from presentation can help when those concerns change independently. A small component that performs a request and renders a result may still be cohesive if the application has no independent reason to change those pieces.

#### Open/Closed Principle (OCP)

An extension point is useful when a kind of variation is known and likely; it is not practical to close a system against every future change.

~~~javascript
class ShippingCalculator {
  constructor(strategy) {
    this.strategy = strategy;
  }

  calculate(pkg) {
    return this.strategy.calculate(pkg);
  }
}

class ExpressShipping {
  calculate(pkg) { return pkg.weight * 10; }
}

class StandardShipping {
  calculate(pkg) { return pkg.weight * 5; }
}
~~~

A new shipping policy can be supplied without changing the calculator, while the selection and shared contract still need maintenance. See [Strategy in practice](#42.%20When%20does%20a%20design%20pattern%20make%20change%20easier%20to%20understand%20and%20maintain?%20/%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E8%83%BD%E8%AE%A9%E5%8F%98%E5%8C%96%E6%9B%B4%E6%98%93%E7%90%86%E8%A7%A3%E5%92%8C%E7%BB%B4%E6%8A%A4%EF%BC%9F).

#### Liskov Substitution Principle (LSP)

A subtype should preserve the behavioral contract clients expect. For example, if a base type promises that every value can fly, a penguin subtype that throws from `fly` breaks that contract. A narrower abstraction such as `Bird` for shared bird behavior and `FlyingBird` for birds that can fly may model the domain more accurately.

#### Interface Segregation Principle (ISP)

Clients should not be forced to depend on operations they never use. In TypeScript, this can mean separating unrelated capabilities into small interfaces and composing them where needed; there is no universal field-count threshold.

#### Dependency Inversion Principle (DIP)

High-level policy and low-level details depend on an abstraction when that boundary reduces coupling. Constructor injection is one way to supply an implementation; **dependency injection is a technique, not the definition of DIP**.

~~~javascript
class NotificationService {
  constructor(sender) {
    this.sender = sender;
  }

  notify(message) {
    this.sender.send(message);
  }
}

class EmailSender {
  send(message) { /* send email */ }
}

class SmsSender {
  send(message) { /* send SMS */ }
}

const notifications = new NotificationService(new EmailSender());
~~~

The service can use another implementation or a test double through the same contract. Add an abstraction when the variation or test boundary is real.

---

### What are DRY, KISS, and YAGNI?

**DRY, KISS, and YAGNI / 不重复、保持简单、暂不实现未需功能** are practical heuristics. They help manage complexity but should not be interpreted as absolute prohibitions.

#### DRY (Don't Repeat Yourself)

Avoid duplicating the same rule or knowledge in places that must stay synchronized. Similar-looking code can represent different concepts, though; extracting it into one abstraction may couple changes that should remain independent.

#### KISS (Keep It Simple)

Prefer the simplest design that satisfies current requirements. A simple implementation is easier to explain and change; complexity should have a concrete payoff.

#### YAGNI (You Aren't Gonna Need It)

Do not build speculative features before a need is established. Keep the option to add an extension point when a real use case appears, and avoid confusing “not yet needed” with “never needed.”

---

See [frontend architecture boundaries](#41.%20How%20can%20a%20frontend%20architecture%20divide%20presentation%20and%20behavior?%20/%20%E5%89%8D%E7%AB%AF%E6%9E%B6%E6%9E%84%E6%80%8E%E6%A0%B7%E5%88%92%E5%88%86%E5%91%88%E7%8E%B0%E4%B8%8E%E8%A1%8C%E4%B8%BA%E7%9A%84%E8%81%8C%E8%B4%A3%EF%BC%9F) for presentation and deployment ownership examples.

Sources: [Robert C. Martin, The Open-Closed Principle](https://objectmentor.com/resources/articles/ocp.pdf), [Principles and Patterns](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf), and [Liskov and Wing, A Behavioral Notion of Subtyping](https://doi.org/10.1145/197320.197383).
## 41. How can a frontend architecture divide presentation and behavior? / 前端架构怎样划分呈现与行为的职责？

Start by deciding who owns data, interaction, and the view. Components give the UI explicit inputs and outputs, and unidirectional data flow helps trace causes of state changes. Micro-frontends add a deployment and ownership boundary when teams need independent releases. / 先确定数据、交互和视图由谁负责。组件为界面定义明确的输入和输出，单向数据流有助于追溯状态变化的原因。团队需要独立发布时，微前端还会引入部署与所有权边界。

### What are common frontend architecture patterns?

These are common design shapes, not a required architecture. Choose based on product boundaries, change frequency, and team ownership.

#### Component-based architecture

A UI can be composed from reusable components with explicit inputs and outputs. State and side effects may live in a component, a hook, or a separate service depending on its lifecycle and reuse needs; they are not inherently owned by every component.

#### Unidirectional data flow

In the classic Flux model, actions pass through a dispatcher to stores, which notify views. Other state libraries use different contracts. The useful goal is to make state changes and their causes traceable; the particular library does not guarantee that by itself.

See [Advanced React](../../frontend/frameworks/advanced-react.md) for React-specific state and component patterns.

#### Micro-frontends

Micro-frontends divide a frontend into parts that can have separate ownership or release paths. Integration can use build-time composition, runtime module loading, iframes, or web components, each with different isolation and deployment properties.

Reach for this when independent teams or release schedules are a concrete requirement and the organization can support the shared navigation, styling, accessibility, observability, and runtime boundaries. For a smaller application, a modular single frontend usually has less coordination and deployment overhead.

**See also:** [Design Patterns in Practice](#42.%20When%20does%20a%20design%20pattern%20make%20change%20easier%20to%20understand%20and%20maintain?%20/%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E8%83%BD%E8%AE%A9%E5%8F%98%E5%8C%96%E6%9B%B4%E6%98%93%E7%90%86%E8%A7%A3%E5%92%8C%E7%BB%B4%E6%8A%A4%EF%BC%9F) for reusable patterns that can support these principles.

[Back to the main question / 返回主问题](#40.%20How%20do%20design%20principles%20reduce%20the%20cost%20of%20change%20without%20adding%20needless%20abstraction?%20/%20%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99%E5%A6%82%E4%BD%95%E9%99%8D%E4%BD%8E%E5%8F%98%E5%8C%96%E6%88%90%E6%9C%AC%E8%80%8C%E4%B8%8D%E8%BF%87%E5%BA%A6%E6%8A%BD%E8%B1%A1%EF%BC%9F).
## 42. When does a design pattern make change easier to understand and maintain? / 何时使用设计模式能让变化更易理解和维护？

A design pattern names a recurring choice about construction, variation, notification, or ownership. Use it when the named boundary makes an actual change easier to localize or explain; then account for the added indirection and lifetime rules. A pattern does not remove a need to define scope, contracts, or authorization. **设计模式概括对象创建、行为变化、通知或所有权中的常见选择。只有当它能把真实变化收拢到更清晰的边界时才使用，并同时考虑新增的间接层和生命周期规则。模式不会替代对作用范围、契约和授权边界的定义。**

### When do you use the Factory pattern?

**工厂 / Factory** centralizes object creation when construction rules or the concrete type should not be repeated at call sites. A simple factory function is useful in JavaScript, but it is not automatically the GoF Factory Method or Abstract Factory pattern.

~~~javascript
function createButton(type) {
  if (type === 'primary') return new PrimaryButton();
  if (type === 'secondary') return new SecondaryButton();
  return new DefaultButton();
}
~~~

Use this when the creation decision belongs in one place or construction has meaningful setup. If construction is already a single uncomplicated expression, a factory can add little value.

---

### When do you use the Singleton pattern?

**单例 / Singleton** constrains access to one instance within a chosen scope. A class-level static instance, for example, is one per loaded class in a JavaScript realm; it is not automatically one instance across workers, processes, duplicated module copies, or machines.

~~~javascript
class Store {
  static instance;

  static getInstance() {
    if (!Store.instance) Store.instance = new Store();
    return Store.instance;
  }
}
~~~

Repeated calls to `getInstance()` share one instance through that accessor; because `Store` has a public constructor, `new Store()` can still create additional instances.

A shared cache, event bus, or connection pool may need one instance per process or module. Consider whether explicit dependency injection or a scoped shared instance is easier to test and reason about. A singleton's global access can hide dependencies and couple tests.

---

### When do you use the Strategy pattern?

**策略 / Strategy** puts interchangeable behavior behind a common contract. It is useful when callers must choose among algorithms or policies; a small conditional is often clearer when there is only one simple branch.

~~~javascript
const strategies = new Map([
  ['express', pkg => pkg.weight * 10],
  ['standard', pkg => pkg.weight * 5],
  ['overnight', pkg => pkg.weight * 20],
]);

function calculateShipping(name, pkg) {
  const strategy = strategies.get(name);
  if (!strategy) throw new RangeError('unknown shipping strategy');
  return strategy(pkg);
}
~~~

Adding a strategy can avoid changing the dispatcher, but the strategy contract and selection rules still need to be maintained. This can support the Open/Closed Principle when the variation is real; it does not make a design closed to every future change. See [Software Design Principles](#40.%20How%20do%20design%20principles%20reduce%20the%20cost%20of%20change%20without%20adding%20needless%20abstraction?%20/%20%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99%E5%A6%82%E4%BD%95%E9%99%8D%E4%BD%8E%E5%8F%98%E5%8C%96%E6%88%90%E6%9C%AC%E8%80%8C%E4%B8%8D%E8%BF%87%E5%BA%A6%E6%8A%BD%E8%B1%A1%EF%BC%9F).

---

### What's the difference between Observer and Publish-Subscribe?

**观察者 / Observer** and **发布订阅 / Publish-Subscribe** both route notifications. In the common distinction, an observer subject knows its observers and notifies them directly; a publish-subscribe broker routes messages by topic, so publishers and subscribers need not know each other. Real libraries can combine these arrangements, so use the concrete API's contract rather than relying on the label.

#### Observer

~~~javascript
class Subject {
  constructor() {
    this.observers = new Set();
  }

  subscribe(observer) {
    this.observers.add(observer);
    return () => this.observers.delete(observer);
  }

  notify(data) {
    for (const observer of this.observers) observer.update(data);
  }
}
~~~

The subject owns the subscriptions. Returning an unsubscribe function makes the lifetime of a listener explicit.

#### Publish-Subscribe

~~~javascript
class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(topic, listener) {
    const subscribers = this.listeners.get(topic) ?? new Set();
    subscribers.add(listener);
    this.listeners.set(topic, subscribers);
    return () => subscribers.delete(listener);
  }

  emit(topic, data) {
    for (const listener of this.listeners.get(topic) ?? []) listener(data);
  }
}

const eventBus = new EventBus();
eventBus.on('user:login', user => { /* update the UI with user data */ });
eventBus.emit('user:login', { name: 'Alice' });
~~~

A broker can reduce direct coupling, but distributed or global event buses can make the flow harder to trace. DOM `EventTarget` is observer-like: listeners register on a target that dispatches events.

See [DOM Manipulation and Events](../../frontend/browser-apis/dom-manipulation-and-events.md) for browser event APIs.

---

See [how to model an editable component tree](#43.%20How%20should%20a%20low-code%20editor%20store%20editable%20structure%20and%20published%20output?%20/%20%E4%BD%8E%E4%BB%A3%E7%A0%81%E7%BC%96%E8%BE%91%E5%99%A8%E6%80%8E%E6%A0%B7%E4%BF%9D%E5%AD%98%E5%8F%AF%E7%BC%96%E8%BE%91%E7%BB%93%E6%9E%84%E4%B8%8E%E5%8F%91%E5%B8%83%E7%BB%93%E6%9E%9C%EF%BC%9F) for a system-design example and [how roles control feature access](#44.%20How%20should%20roles%20control%20access%20to%20a%20feature?%20/%20%E8%A7%92%E8%89%B2%E6%80%8E%E6%A0%B7%E6%8E%A7%E5%88%B6%E5%AF%B9%E5%8A%9F%E8%83%BD%E7%9A%84%E8%AE%BF%E9%97%AE%EF%BC%9F) for a distinct authorization decision.
## 43. How should a low-code editor store editable structure and published output? / 低代码编辑器怎样保存可编辑结构与发布结果？

Keep an editable component tree with typed configuration and stable identity. Derive rendering and published output from that schema so editing, validation, and release can each use the representation appropriate to their lifecycle. / 维护带类型配置和稳定身份的可编辑组件树。渲染和发布结果从该结构派生，让编辑、校验和发布可以各自使用适合其生命周期的表示。

### Separate page content from the editing session / 分开页面内容与编辑会话

A page builder can model a document as a component tree, with each node carrying an ID, type, properties, style, and children. The editor can derive its canvas and side panels from that model, then serialize it for persistence.

~~~javascript
const component = {
  id: 'comp_001',
  type: 'Button',
  props: { text: 'Click me', variant: 'primary' },
  style: { position: 'absolute', top: 100, left: 200 },
  children: [],
};
~~~

Keep document order and visual stacking as explicit concepts. Child order can be one input to rendering, but CSS stacking contexts mean it is not universally equivalent to the final z-order; each stacking context is painted as a unit within its parent context ([CSS 2.2 visual formatting model](https://www.w3.org/TR/CSS22/zindex.html)).

Selection, hover, and panel state belong to the editing session. A selection change can update the inspector without editing the document, saving a draft, or adding an undo step.

~~~javascript
const editor = {
  document: { schemaVersion: 1, nodes: [component] },
  session: { selectedId: null },
};

function selectComponent(state, id) {
  return { ...state, session: { ...state.session, selectedId: id } };
}

const draftJson = JSON.stringify(selectComponent(editor, component.id).document);
~~~

- **Component registry / 组件注册表**: map a validated component type to its renderer and schema.
- **Layer order / 图层顺序**: define how siblings are ordered and translate that order into the chosen rendering model.
- **Undo and redo / 撤销与重做**: store inverse commands or immutable document snapshots; choose based on history size and operation complexity.
- **Collaboration / 协作**: a WebSocket transports updates, but does not resolve concurrent edits. A server-authoritative order, locks, operational transformation, or a CRDT may fit different conflict and offline requirements.

### Publish a validated revision / 发布已校验的修订

Validate a particular document revision against the registry and derive the public output from that revision. Keep the artifact or a versioned rendering recipe tied to its source revision so preview, release, and rollback can refer to the same content. Draft edits and session selections can then continue independently. [Design patterns and change boundaries / 设计模式与变化边界](#42.%20When%20does%20a%20design%20pattern%20make%20change%20easier%20to%20understand%20and%20maintain?%20/%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E8%83%BD%E8%AE%A9%E5%8F%98%E5%8C%96%E6%9B%B4%E6%98%93%E7%90%86%E8%A7%A3%E5%92%8C%E7%BB%B4%E6%8A%A4%EF%BC%9F)
## 44. How should roles control access to a feature? / 角色怎样控制对功能的访问？

Map roles to permissions and evaluate them for the actual request and resource. A menu can reflect what the user may do, while the service enforces the same policy for each action. / 把角色映射为权限，并针对实际请求与资源评估。界面菜单可以反映用户可执行的操作，服务仍需在每次操作时实施策略。

### How does Role-Based Access Control (RBAC) work?

**基于角色的访问控制 / Role-Based Access Control** associates permissions with roles and assigns users to roles. It is one authorization model; it does not determine whether a particular user may access every object of a type.

A relational model commonly includes:

- **User / 用户**: identity and credential reference.
- **Role / 角色**: named job or application role.
- **Permission / 权限**: action on a resource or capability.
- **UserRole / 用户角色**: many-to-many user-to-role assignment.
- **RolePermission / 角色权限**: many-to-many role-to-permission assignment.

A request is authenticated first, then the server checks whether the resulting subject may perform the requested action on the requested object. Check every protected operation and resource; hiding a button or trusting a client-supplied role is not authorization. Role changes simplify policy administration only when the application's permission model fits roles.

See [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) for authorization boundaries and [Design Patterns: Elements of Reusable Object-Oriented Software](https://www.informit.com/store/design-patterns-elements-of-reusable-object-oriented-software-9780201633610) for the original GoF catalog.

[Back to the main question / 返回主问题](#42.%20When%20does%20a%20design%20pattern%20make%20change%20easier%20to%20understand%20and%20maintain?%20/%20%E4%BD%95%E6%97%B6%E4%BD%BF%E7%94%A8%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F%E8%83%BD%E8%AE%A9%E5%8F%98%E5%8C%96%E6%9B%B4%E6%98%93%E7%90%86%E8%A7%A3%E5%92%8C%E7%BB%B4%E6%8A%A4%EF%BC%9F).
## 45. How can a minimal counterexample trace a regression to its root cause? / 如何用最小反例沿调用路径定位回归根因？

**核心回答 / Core answer：** Start with an observable expected outcome, trace the request through its entry point, dependencies, data access, and side effects, then build the smallest counterexample that can disprove a specific hypothesis. If the failure occurs at a lost tenant predicate, restore that predicate and test both owner and non-owner requests. Review the implementation and its tests independently: they can pass together while sharing the same missing assumption. / 先写出可观察的预期结果，再沿入口、依赖、数据访问和副作用追踪请求，并构造足以推翻某个具体假设的最小反例。如果故障来自丢失租户条件，就恢复该条件，并分别检查所有者与非所有者请求。实现和测试要独立审查：两者可能共享同一个遗漏假设，即使一起通过也不能证明需求已满足。

**Key terms / 关键术语：** expected behavior / 预期行为；entry point / 入口；call path / 调用路径；minimal reproduction / 最小复现；falsifiable hypothesis / 可证伪假设；root cause / 根因；regression check / 回归检查；generated change / 生成式改动。

### Follow one generated authorization bug / 跟踪一个生成式授权缺陷

Suppose a generated refactor changes a job lookup from the existing tenant-scoped query to `session.get(Job, job_id)`. Its generated test creates a job for `tenant-a` and reads it back as `tenant-a`; that test passes. The requirement, however, is that the current tenant may read only its own job. A matching owner read does not exercise that boundary.

Start with an observable expectation: after `tenant-a` creates a job, `tenant-b` requesting the same ID receives `404`, while `tenant-a` still receives `200`. Then follow the request rather than guessing from the response: the route reads `tenant_id` from the principal dependency, passes it to the database lookup, and serializes the returned job. The generated patch still receives `tenant_id`, but its new `session.get` lookup ignores it.

The minimal reproduction is one create and one read under a different tenant. If the response is `200`, the hypothesis “the database lookup no longer constrains the row by the current tenant” is supported. If the route rejects the second tenant earlier, or the lookup is tenant-scoped, the hypothesis is false and the next step is to inspect that earlier branch or another code path. This makes the hypothesis testable rather than a label attached after the fact.

The smallest coherent fix is to restore both predicates in the query:

~~~python
job = session.scalar(
    select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id)
)
~~~

The root cause is the lost tenant predicate, not response serialization or a missing test fixture. Keep the owner success path, add the cross-tenant `404` assertion, and retain the missing-principal, invalid-request, duplicate-create, and repeated-worker checks from [Software Testing Strategy / 软件测试策略](#47.%20How%20should%20test%20boundaries%20prove%20the%20failure%20risks%20that%20matter?%20/%20%E5%A6%82%E4%BD%95%E9%80%89%E6%8B%A9%E6%B5%8B%E8%AF%95%E8%BE%B9%E7%95%8C%E6%9D%A5%E8%AF%81%E6%98%8E%E5%85%B3%E9%94%AE%E6%95%85%E9%9A%9C%E9%A3%8E%E9%99%A9%EF%BC%9F). Those nearby checks show that the fix did not break the surrounding route and persistence behavior. They do not prove production identity validation or broker semantics, which were not part of this reproduction.

### Read a generated change against the requirement / 对照需求独立阅读生成式改动

Read the requirement first and write down the expected outcomes before using the generated tests as a guide. Then inspect the changed route, its callers and dependencies, the query or transaction it reaches, and the error/response mapping. Compare the assertions with that expected behavior: in this case, a suite that tests only `tenant-a` cannot detect a missing tenant predicate, even if every generated test passes.

Run the minimal counterexample against the changed code, inspect the actual query and row returned, apply the narrow fix, then run the owner and non-owner cases plus relevant nearby checks. Read the new tests too: verify that they reach the changed route and real database boundary, that their fixtures establish the intended principal, and that they assert the required failure rather than only a happy-path response. For a database or delivery claim, identify the engine or broker the test actually used; a stubbed session or local function call is evidence only for that seam.

The review is complete when the observed failure, its cause, the changed behavior, and the regression evidence line up with the requirement. A model-written test passing is one observation, not independent proof that the requirement is complete. Keep the change as small as the cause allows: this example needs the missing query predicate and its negative regression assertion, not a new repository layer or review-management process.

**Interview answer / 面试回答：** I first state the expected behavior, trace the entry point through the relevant dependency and data access, and build the smallest request that can disprove my hypothesis. Here, the other tenant receives the row because the generated refactor drops the tenant condition. Restoring that condition and running both owner and non-owner requests is the focused fix and regression check. I read the generated implementation and tests independently because their shared assumptions can omit the same requirement. / 我先明确预期行为，再沿入口、依赖和数据访问追踪调用路径，并构造能够推翻假设的最小请求。这个例子中，另一租户读到了任务，是因为生成式重构删掉了租户条件。恢复该条件并分别运行所有者和非所有者请求，就是聚焦的修复与回归验证。我会独立阅读生成实现和测试，因为二者可能共享同一个遗漏假设。

**Sources checked 2026-10-15:** GitHub's official [reviewing proposed changes](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests) documentation describes inspecting commits and diffs, and its [review concepts](https://docs.github.com/en/pull-requests/concepts/giving-reviews) explain review feedback and deeper inspection. The reproduced tenant behavior and query correction are exercised in the linked synthetic API example; no personal project or generated artifact is used.
## 46. How would you design a durable account report? / 怎样设计可持久查询的账户报表？

Start with the user's outcome and hard constraints, then choose the smallest architecture that satisfies them. This account report can outlive an HTTP request, so persist a job with a stable status URL. Commit the job, its outbox record, and one bounded waiting-slot reservation together; publish the job ID from the outbox; and let a worker write an immutable result for its attempt. Only a conditional database update for the current attempt can make that result visible. The same scoped idempotency key resolves a repeated submission to the same job, while a status lookup resolves a lost response. / 从用户要完成的结果和硬约束开始，再选择满足它们的最小架构。本账户报表可能超过一次 HTTP 请求的时限，因此应持久化 job 并返回稳定的状态 URL。在同一事务中提交 job、outbox 记录和一个有界等待槽；再由 outbox 发布 job ID，并由 worker 为当前 attempt 写入不可变结果。只有针对当前 attempt 的条件更新才能让结果对外可见。相同作用域的幂等键使重复提交回到同一个 job，状态查询则用来处理响应丢失。

**Key terms / 关键术语：** requirement / 需求；constraint / 约束；job / 任务；idempotency / 幂等性；transactional outbox / 事务型发件箱；conditional update / 条件更新；admission control / 准入控制；attempt fence / 尝试栅栏。

### Structure the design / 如何组织设计过程

Clarify the task and success criteria; state workload, latency, privacy, budget, and ownership constraints; trace the request and data paths; examine the risks that could change correctness or capacity; then specify evaluation, rollout, and rollback. This is a reusable discussion method, not a reason to add an unrelated component. See [AI System Design Interview Questions / AI 系统设计面试题](../../ai-engineering/systems/ai-system-design-interview-questions.md) for the longer checklist.

### Requirements and constraints / 需求与约束

A user asks for a CSV report over a bounded account time range. The report reads account activity, may take several seconds, and should remain retrievable for seven days even if the browser closes. Users can check progress and request cancellation. Reports are read-only: they do not change account activity. Validate and bound the input range and query to at most 12 sequential reads; reject an oversize request before accepting work.

Use the estimates in [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F): average 5 submissions/s and a 10-minute peak of 20/s; 6 s mean worker time; 8 KiB request; 12 sequential database reads; 128 KiB average result; and a seven-day result-retention target. These are teaching assumptions for comparing choices, not production measurements. The design constraints are: authorize every user-facing path; do not lose accepted work between the database and queue; bound waiting work and connection use; and preserve an explicit result or failure that can be queried after disconnect.

### API contract and data ownership / API 契约与数据所有权

One chosen API contract is:

~~~http
POST /v1/accounts/acct-17/reports
Idempotency-Key: report-demo-208
Content-Type: application/json

{"period":"2026-Q2","format":"csv"}

HTTP/1.1 202 Accepted
Location: /v1/jobs/job-demo-731

{"jobId":"job-demo-731","status":"queued","statusUrl":"/v1/jobs/job-demo-731"}
~~~

The **202** response means the request was accepted for processing; it does not say that processing completed or will necessarily succeed. **GET /v1/jobs/{jobId}** returns current job state; **DELETE /v1/jobs/{jobId}** records a cancellation request; and **GET /v1/jobs/{jobId}/result** returns the private result only after authorization and completion. The status resource tells the client the later outcome. If the original response is lost, [work out what the caller can confirm / 判断调用方能确认什么](#Where%20a%20timeout%20leaves%20the%20caller%20/%20%E8%B6%85%E6%97%B6%E5%90%8E%E8%B0%83%E7%94%A8%E6%96%B9%E5%A4%84%E4%BA%8E%E4%BB%80%E4%B9%88%E7%8A%B6%E6%80%81) before repeating the operation. This follows [HTTP API Contracts / HTTP API契约](#26.%20How%20do%20you%20design%20a%20predictable%20HTTP%20API%20contract?%20/%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F) for endpoint shapes and [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#16.%20How%20does%20a%20browser%20request%20reach%20an%20HTTP%20response?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F) for protocol semantics.

Scope an idempotency key to (account, requesting principal, key) and enforce that scope with a database unique constraint. First look up an existing key: return its job when the normalized-request fingerprint matches, and report a conflict when it differs. If absent, insert the job under the unique constraint, add the outbox row, and conditionally reserve a waiting slot in one transaction before commit. If a concurrent same-key insert wins, the loser rolls back before reserving, loads the existing job, and compares fingerprints; lookup-then-insert alone is racy. These are explicit choices for this example, not rules every API must use. Define the success and error schema as part of the service's endpoint contract.

Authenticate first, then check that the principal may create a report for the account in the path. A caller-supplied account ID selects a resource; it does not prove permission. Every later status, cancellation, and result request checks access to the job's stored account; knowing a job ID does not grant access. The worker uses a narrowly scoped service identity to read only the stored account and report range. See [Web Security and Authentication / Web安全与身份认证](#30.%20How%20do%20you%20prevent%20cross-tenant%20access%20across%20a%20web%20request?%20/%20%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20Web%20%E8%AF%B7%E6%B1%82%E8%B7%A8%E7%A7%9F%E6%88%B7%E8%AE%BF%E9%97%AE%EF%BC%9F) for the shared authorization boundary.

Store a job row with a stable job ID, account ID, requesting principal, validated normalized report parameters such as period/range/format, normalized request fingerprint, idempotency key, current status, creation/expiry times, cancellation request, attempt number and lease expiry, waiting-slot reservation state, private result reference, and a bounded error code. The parameters let a restarted worker rebuild its input; the fingerprint only compares requests and cannot recover them. Do not retain the raw request body or put sensitive filters in queue messages. A separate outbox row holds the job ID and publication state.

Use one database-backed counter for the 240 shared waiting-job reservations. Commit the new unique job, outbox row, and one slot reservation together only when the count is below 240; otherwise roll back and reject before **202**. If the unique-key insert loses a concurrent race, its transaction rolls back without consuming a slot before resolving the existing job. The reservation follows that logical job while it is unpublished in the outbox or waiting in the broker, so a broker copy does not consume another slot. A guarded state transition releases it once when a worker first starts the job or when it becomes terminal before starting. A retry or lease-expiry recovery that returns work to waiting must reserve a slot again before requeueing; if no slot is available, record a visible terminal failure instead of growing the backlog beyond the bound.

### Request, queue, and result path / 请求、队列与结果路径

~~~mermaid
flowchart LR
    C[Client submits report] --> A[Authenticate, authorize, validate bounded range]
    A --> T[One DB transaction]
    T --> J[Insert unique job]
    T --> O[Insert outbox row]
    T --> R[Reserve one shared waiting slot]
    J --> Commit[Commit]
    O --> Commit
    R --> Commit
    Commit --> Accepted[Return 202 with stable job ID and status URL]
    Commit --> Relay[Outbox relay publishes job ID]
    Relay --> Q[Durable queue]
    Q --> W[Worker conditionally claims attempt and releases waiting slot]
    W --> Read[Read stored parameters and authorized account pages]
    Read --> Obj[Write immutable object key for this attempt]
    Obj --> Conditional{Current attempt and not cancelled?}
    Conditional -->|yes| Visible[Commit terminal state and result reference]
    Conditional -->|no| CheckState{Cancellation or stale attempt?}
    CheckState -->|current attempt cancelled| Cancelled[Commit cancelled terminal state without result]
    CheckState -->|stale or already terminal| Hidden[Leave attempt object unreferenced]
    Visible --> Ack[Acknowledge queue delivery after durable outcome]
    Cancelled --> Ack
    Hidden --> Terminal{Job is already terminal?}
    Terminal -->|yes| Ack
    Terminal -->|no| Defer[Defer under the broker redelivery contract]
    C --> Status[Query job status or result through authorized API]
    Visible --> Status
~~~

This picture distinguishes three durable systems. The job and outbox rows share one database transaction; the queue confirms publication under its own rules; the private object is separate again and becomes visible only through the conditional job update. Acknowledgement follows the durable job outcome, not merely queue receipt. General broker confirmation and redelivery behavior is explained in [Publisher confirms and consumer acknowledgements / 发布者确认和消费者确认分别证明什么？](#38.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F).

#### Outbox publication and worker attempts / Outbox 发布与 worker 尝试

The job row and outbox row commit together. Otherwise a process can commit the job and crash before publishing it, or publish a message for a transaction that later rolls back. The relay retries publication and records delivery after broker confirmation. It may publish twice if it crashes after broker acceptance but before recording delivery, so the worker deduplicates by job ID rather than relying on a single delivery. This is the transactional-outbox trade-off: durable relay state avoids a database-plus-queue dual write, while duplicate handling and outbox cleanup remain necessary. A database transaction does not extend to the queue or object store.

Before doing work, a worker reloads the job and acknowledges a delivery immediately if the job is already terminal. If another unexpired attempt owns it, the worker does not start duplicate work and defers the delivery according to the broker's retry/redelivery contract. Otherwise a conditional update claims an eligible waiting job by incrementing its attempt number, setting a bounded lease, and releasing its reserved waiting slot. After a worker loss, recovery returns the job to waiting only after the lease expires and another slot is reserved; a redelivery cannot bypass that bound.

The attempt number fences late workers. Each claim writes to a create-only, never-reused object key containing both job ID and attempt number. A result becomes visible only when a conditional database update still matches the running job's current attempt, with cancellation not already requested, and commits the private object reference with the terminal state. If the update affects no row, that attempt lost and its object remains unreferenced for retention cleanup. When the allowed attempts are exhausted, conditionally record a terminal error for the current job so clients can see the failure.

For example, worker A claims attempt 1 and stalls until its lease expires. Worker B claims attempt 2, writes a different result key, and commits the completed state and attempt-2 reference. If A later resumes, its attempt-1 key cannot overwrite B's object, and its conditional job update no longer matches; the completed job short-circuits any later duplicate delivery. A crash after upload but before the conditional update similarly leaves only an unreferenced attempt object. Acknowledge the winning attempt after the durable outcome; queue delivery alone is not user-visible completion.

#### Cancellation and completion race / 取消与完成的竞态

Cancellation is a request, not proof that work stopped. The API records it; a worker checks between bounded pages and before publishing the result. Completion and cancellation can race, so both terminal transitions check the current attempt number and cancellation state. If the cancellation request wins before result commit, the current worker records a cancelled terminal state without a result reference; if the completion transition wins first, later cancellation cannot change the terminal outcome. A stale attempt cannot publish its object or change the job. Only the authoritative conditional transition determines the visible state.

### When to queue this work / 什么时候使用队列

If representative reports consistently fit within the caller's request deadline and an acceptable tail-latency target, a synchronous endpoint is simpler: validate, run the bounded reads, return the CSV, and remove the queue, outbox relay, worker deployment, status polling, and result cleanup lifecycle. Use the asynchronous path when a request may exceed that deadline, results must survive a disconnect, or measured bursts require work to be admitted and drained independently of API processes. The queue adds durable waiting and failure isolation, but also adds operational state and delay; it does not create processing capacity.

### Size and operate the design / 估算容量并运行设计

For this workload, use the 64 worker slots, 7/s sustained admission rate, 30-job burst, shared 240 accepted-but-not-started-job bound, and 200-connection application-pool ceiling from the linked sizing example rather than copying its arithmetic here. At sustained 20/s offered traffic, the service must reject work after its admission bound; accepting all of it would require about 120 concurrent workers at the assumed 6 s mean service time. Before changing the design, measure API acceptance latency, queue age and depth, active worker slots, job completion percentiles, database checkout wait and query time, object bytes retained, retries, cancellation outcomes, and completed reports. An old queue with rising oldest-message age is overload even if the API still accepts requests.

Deploy API, relay, and workers with compatible job schemas so old jobs can finish during a rollout. Retain result objects for seven days; delete expired objects and metadata under the chosen retention policy; and bound retries and deadlines so a bad report cannot occupy a worker forever. If the queue is unavailable, accepted-but-not-started jobs stay in the outbox and continue consuming the same reserved slots; once all 240 are reserved, reject new submissions before **202**. If the database is unavailable, the API cannot durably accept the job and must return an error rather than imply success. Roll out with health checks and a rollback path that accounts for jobs already accepted under the previous schema. For the arithmetic behind the worker, database, and retention budgets, see [Sizing and bounding asynchronous work / 如何估算并限制异步工作管线？](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F). For stage-level indicators and alerting, see [Observability, SLOs, and Incident Response / 可观测性、服务目标与事件响应](#39.%20How%20do%20you%20diagnose%20an%20API%20SLO%20violation?%20/%20%E5%A6%82%E4%BD%95%E8%AF%8A%E6%96%AD%20API%20SLO%20%E8%BF%9D%E7%BA%A6%EF%BC%9F).

**How would you answer “How would you design a report that may outlive an HTTP request?” / 如何回答“如何设计一个可能超过 HTTP 请求时限的报表任务？”** I would first confirm report size, response deadline, retention, access owner, and acceptable failure behavior. If measured tail latency fits the request budget, I would keep it synchronous. For the stated multi-second report, I would persist the job and outbox in one database transaction, return a stable status URL, and let a bounded worker create a private result. Retries use the scoped idempotency key, and each worker attempt writes a distinct immutable object. A guarded update makes only the current, non-cancelled attempt visible; acknowledge the queue message after the durable outcome. The client queries job state after disconnect rather than inferring completion from a response or message delivery. / 我会先确认报表规模、响应期限、留存期、数据所有者和可接受的失败行为。如果实测尾部时延满足请求预算，就保持同步。对于本例需要数秒的任务，我会在同一数据库事务中保存 job 与 outbox 并返回稳定的状态 URL，再由有界 worker 生成私有结果。重试使用有作用域的幂等键，每个 worker 尝试写入不同且不可变的对象。只有当前且未被取消的尝试可以通过条件更新让结果可见，并在持久化业务结果后确认队列消息；客户端断连后应查询 job 状态，而不能从响应或消息是否投递推断完成。

**Related notes / 相关笔记：** [API Reliability and Asynchronous Delivery / API超时后的结果确认与安全重试](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) owns unknown outcomes and safe retries; [Sizing and bounding asynchronous work / 容量估算与背压](#37.%20How%20do%20you%20size%20and%20bound%20an%20asynchronous%20work%20pipeline?%20/%20%E5%A6%82%E4%BD%95%E4%BC%B0%E7%AE%97%E5%B9%B6%E9%99%90%E5%88%B6%E5%BC%82%E6%AD%A5%E5%B7%A5%E4%BD%9C%E7%AE%A1%E7%BA%BF%EF%BC%9F) retains the detailed estimates; [Publisher confirms and consumer acknowledgements / 队列确认与重投](#38.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) explains broker-level confirmation boundaries; [HTTP API Contracts / HTTP API契约](#26.%20How%20do%20you%20design%20a%20predictable%20HTTP%20API%20contract?%20/%20%E5%A6%82%E4%BD%95%E8%AE%BE%E8%AE%A1%E5%8F%AF%E9%A2%84%E6%9C%9F%E7%9A%84%20HTTP%20API%20%E5%A5%91%E7%BA%A6%EF%BC%9F) covers endpoint and error conventions; [Data Access and Connection Pools / 数据访问与连接池](#28.%20How%20do%20you%20scope%20an%20ORM%20Session%20and%20diagnose%20pool%20exhaustion?%20/%20%E5%A6%82%E4%BD%95%E9%99%90%E5%AE%9A%20ORM%20Session%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E5%B9%B6%E8%AF%8A%E6%96%AD%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F) explains ORM sessions and process-local pool limits; [Database Fundamentals / 数据库基础](#12.%20How%20do%20you%20reserve%20the%20last%20inventory%20unit%20safely?%20/%20%E5%A6%82%E4%BD%95%E5%AE%89%E5%85%A8%E9%A2%84%E7%95%99%E6%9C%80%E5%90%8E%E4%B8%80%E4%B8%AA%E5%BA%93%E5%AD%98%EF%BC%9F) covers constraints and transaction semantics; [Web Security and Authentication / Web安全与身份认证](#30.%20How%20do%20you%20prevent%20cross-tenant%20access%20across%20a%20web%20request?%20/%20%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20Web%20%E8%AF%B7%E6%B1%82%E8%B7%A8%E7%A7%9F%E6%88%B7%E8%AE%BF%E9%97%AE%EF%BC%9F) owns identity and resource authorization; [HTTP Protocols and WebSockets / HTTP协议与WebSocket](#16.%20How%20does%20a%20browser%20request%20reach%20an%20HTTP%20response?%20/%20%E6%B5%8F%E8%A7%88%E5%99%A8%E8%AF%B7%E6%B1%82%E5%A6%82%E4%BD%95%E5%88%B0%E8%BE%BE%20HTTP%20%E5%93%8D%E5%BA%94%EF%BC%9F) owns transport and reconnect semantics; [AI Application Architecture / AI 应用架构](../../ai-engineering/systems/ai-application-architecture.md) shows a separate durable-run contract; [Streaming UX / 流式交互](../../frontend/browser-apis/streaming-ux.md) explains how the client surfaces stream and disconnect state; [Observability, SLOs, and Incident Response / 可观测性、服务目标与事件响应](#39.%20How%20do%20you%20diagnose%20an%20API%20SLO%20violation?%20/%20%E5%A6%82%E4%BD%95%E8%AF%8A%E6%96%AD%20API%20SLO%20%E8%BF%9D%E7%BA%A6%EF%BC%9F) covers stage-level production signals.

**Sources / 来源：** [RFC 9110 §15.3.3, 202 Accepted](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3); [PostgreSQL 18: Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html) for the database-local all-or-nothing boundary; [PostgreSQL 18: Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) for scoped uniqueness and [Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html) for concurrent transaction behavior; [AWS Prescriptive Guidance: Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) for dual-write failure and duplicate-publication boundaries; [Amazon S3 conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html) as one create-only object-write mechanism, not a requirement to choose S3; [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework) for workload requirements, operational focus, and starting with a simple design, checked 2026-10-15.
## 47. How should test boundaries prove the failure risks that matter? / 如何选择测试边界来证明关键故障风险？

**核心回答 / Core answer：** Choose the narrowest boundary that can exercise the failure condition: isolate a pure rule with a unit test, connect the real route and principal seam for API behavior, and let the selected database execute SQL for constraints and transactions. Use the configured broker or a deployed-like journey when delivery guarantees or assembled wiring are the risk. The FastAPI example below proves route behavior and local SQLite state transitions; it does not prove production identity, PostgreSQL behavior, broker redelivery, or external effects. / 选择能够触达故障条件的最小测试边界：纯规则用单元测试隔离；API 行为接入真实路由和主体接缝；约束与事务由所选数据库实际执行 SQL 验证。若风险在消息投递保证或部署后的组件装配，就纳入配置好的 broker 或近似生产的端到端链路。下方 FastAPI 示例能证明路由行为和 SQLite 本地状态变更，不能证明生产身份认证、PostgreSQL 行为、broker 重投或外部副作用。

**Key terms / 关键术语：** unit test / 单元测试；integration test / 集成测试；compatibility contract / 兼容性契约；end-to-end (E2E) test / 端到端测试；fixture / 测试夹具；test seam / 测试接缝；test double / 测试替身。

### Choose the boundary from the failure risk / 按故障风险选择测试边界

| Risk | Useful boundary | Evidence that boundary can provide |
|---|---|---|
| A pure rule maps input to the wrong result | Unit | The rule's inputs and outputs, with unrelated I/O absent. |
| A route validates the wrong shape, returns the wrong status, or skips tenant authorization | API integration | The actual router, request validation, dependency path, response serialization, and error mapping. An in-process client does not exercise a network socket or production identity provider. |
| Duplicate keys, rollback, or a conditional update violate a durable invariant | Database integration | The selected database engine executes the schema and statements. A mock session cannot prove a constraint or transaction. |
| An existing consumer can no longer read a response | Compatibility contract | Compare a pinned or published schema and representative consumer expectations with the provider's current output. Checking only a freshly generated schema does not prove compatibility with an older client. |
| A queue redelivery or acknowledgement order causes a duplicate or lost effect | Broker integration | The configured broker, acknowledgement mode, consumer, and durable store exercise the delivery boundary. Calling a handler twice tests its database behavior, not broker delivery guarantees. |
| Login, API, database, and worker wiring fail only when assembled | End-to-end | A controlled deployed-like journey with the actual selected services and identities. It is slower and narrower in number; use it for failures that depend on that wiring. |

These are complementary boundaries, not a required test-count pyramid. Keep quick, deterministic checks close to the risk, then add a higher-boundary check only when it proves something the lower one cannot. The existing [Frontend Testing / 前端测试](../../frontend/testing/frontend-testing.md) note owns Jest, component, browser, and frontend release examples; this note applies the same risk-and-feedback idea to API, persistence, and delivery boundaries.

### One job API with a database-backed worker / 一个带数据库 worker 的任务 API

The small example below creates a tenant-owned job. `POST /jobs` validates a request and gives the same tenant's request key a database uniqueness rule. `GET /jobs/{id}` scopes lookup by the current tenant. A worker delivery changes `pending` to `done` with one conditional database update; replaying the same job ID must not increment the effect counter twice.

The fixture creates a fresh in-memory SQLite database for each test and keeps it on one shared connection so the in-process test client and the test's database inspection see the same database. The `Session` dependency and worker's session-factory argument are deliberate seams: they control database lifetime while still executing real SQL against SQLite. `X-Tenant-ID` stands in for a principal supplied by trusted authentication middleware; it is a test input, not an authentication scheme to trust in a deployed service. For the general authorization rule, see [Web Security and Authentication / Web安全与身份认证](#30.%20How%20do%20you%20prevent%20cross-tenant%20access%20across%20a%20web%20request?%20/%20%E5%A6%82%E4%BD%95%E9%98%B2%E6%AD%A2%20Web%20%E8%AF%B7%E6%B1%82%E8%B7%A8%E7%A7%9F%E6%88%B7%E8%AE%BF%E9%97%AE%EF%BC%9F). The queue call is represented by calling the worker twice; no broker is present.

~~~python
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from sqlalchemy import Integer, String, UniqueConstraint, create_engine, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_key", name="uq_job_tenant_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(60), nullable=False)
    request_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(12), nullable=False, default="pending")
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class JobCreate(BaseModel):
    request_key: str = Field(min_length=1, max_length=64)
    payload: str = Field(min_length=1, max_length=200)


class JobView(BaseModel):
    id: int
    request_key: str
    state: str
    processed_count: int


def tenant_from_test_header(
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=401, detail="authentication required")
    return x_tenant_id


def get_session(request: Request):
    with request.app.state.session_factory() as session:
        yield session


def create_app() -> FastAPI:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    app = FastAPI()
    app.state.engine = engine
    app.state.session_factory = session_factory

    @app.post(
        "/jobs",
        status_code=201,
        response_model=JobView,
        responses={
            401: {"description": "Authentication required"},
            409: {"description": "Request key already exists for this tenant"},
        },
    )
    def create_job(
        body: JobCreate,
        tenant_id: Annotated[str, Depends(tenant_from_test_header)],
        session: Annotated[Session, Depends(get_session)],
    ):
        try:
            with session.begin():
                job = Job(
                    tenant_id=tenant_id,
                    request_key=body.request_key,
                    payload=body.payload,
                )
                session.add(job)
                session.flush()
                response = JobView(
                    id=job.id,
                    request_key=job.request_key,
                    state=job.state,
                    processed_count=job.processed_count,
                )
        except IntegrityError:
            raise HTTPException(status_code=409, detail="request key already exists")
        return response

    @app.get("/jobs/{job_id}", response_model=JobView)
    def read_job(
        job_id: int,
        tenant_id: Annotated[str, Depends(tenant_from_test_header)],
        session: Annotated[Session, Depends(get_session)],
    ):
        job = session.scalar(
            select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id)
        )
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return JobView(
            id=job.id,
            request_key=job.request_key,
            state=job.state,
            processed_count=job.processed_count,
        )

    return app


def deliver_job(session_factory, job_id: int) -> str:
    with session_factory() as session, session.begin():
        result = session.execute(
            update(Job)
            .where(Job.id == job_id, Job.state == "pending")
            .values(state="done", processed_count=Job.processed_count + 1)
        )
        if result.rowcount == 1:
            return "processed"
        return "duplicate" if session.get(Job, job_id) is not None else "missing"


@pytest.fixture
def app():
    application = create_app()
    yield application
    application.state.engine.dispose()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def headers(tenant_id: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id}


def test_api_schema_auth_and_tenant_scope(client):
    body = {"request_key": "daily-7", "payload": "sample"}
    assert client.post("/jobs", json=body).status_code == 401
    assert client.post(
        "/jobs", headers=headers("tenant-a"), json={"request_key": "", "payload": "x"}
    ).status_code == 422

    created = client.post("/jobs", headers=headers("tenant-a"), json=body)
    assert created.status_code == 201
    assert set(created.json()) == {"id", "request_key", "state", "processed_count"}
    assert created.json()["state"] == "pending"

    job_id = created.json()["id"]
    own_read = client.get(f"/jobs/{job_id}", headers=headers("tenant-a"))
    other_read = client.get(f"/jobs/{job_id}", headers=headers("tenant-b"))
    assert own_read.status_code == 200
    assert other_read.status_code == 404


def test_openapi_exposes_the_public_request_and_response_shape(client):
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/jobs"]["post"]
    assert {"201", "401", "409", "422"} <= set(operation["responses"])
    request_ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    response_ref = operation["responses"]["201"]["content"]["application/json"]["schema"]["$ref"]
    request_schema = schema["components"]["schemas"][request_ref.rsplit("/", 1)[1]]
    response_schema = schema["components"]["schemas"][response_ref.rsplit("/", 1)[1]]
    assert set(request_schema["properties"]) == {"request_key", "payload"}
    assert set(response_schema["properties"]) == {"id", "request_key", "state", "processed_count"}


def test_database_unique_constraint_rolls_back_duplicate_create(client, app):
    body = {"request_key": "daily-7", "payload": "sample"}
    first = client.post("/jobs", headers=headers("tenant-a"), json=body)
    duplicate = client.post("/jobs", headers=headers("tenant-a"), json=body)
    assert first.status_code == 201
    assert duplicate.status_code == 409

    with Session(app.state.engine) as session:
        count = session.scalar(select(func.count()).select_from(Job))
    assert count == 1


def test_replayed_worker_delivery_changes_database_once(client, app):
    created = client.post(
        "/jobs",
        headers=headers("tenant-a"),
        json={"request_key": "daily-8", "payload": "sample"},
    )
    job_id = created.json()["id"]

    assert deliver_job(app.state.session_factory, job_id) == "processed"
    assert deliver_job(app.state.session_factory, job_id) == "duplicate"
    result = client.get(f"/jobs/{job_id}", headers=headers("tenant-a"))
    assert result.json()["state"] == "done"
    assert result.json()["processed_count"] == 1
~~~

Extract that block into `test_jobs.py` and run `python -m pytest -q test_jobs.py`. The tests assert visible API behavior, the request and response schema exposed by this app, an actual SQLite uniqueness violation with rollback, and a repeated worker call against the same database. The OpenAPI assertion checks this version's declared shape; a compatibility gate should compare with a released schema or exercise a real supported consumer before claiming an older client remains compatible.

The database is SQLite 3.51.0 through SQLAlchemy 2.0.44. This is a real database engine and the test executes its unique constraint and transaction, but its locking, typing, SQL dialect, and concurrency behavior do not establish PostgreSQL behavior. `TestClient` exercises FastAPI through an in-process ASGI transport, not a live server, network, production authentication provider, or deployed application. `deliver_job` exercises a repeated database operation; it does not prove a broker's redelivery, acknowledgement, ordering, or outage guarantees. Those claims need a broker-backed integration test using the selected broker's configuration. External side effects such as email or payment also need an outbox or downstream idempotency boundary; this example changes only local database state. See [safe retries](#36.%20A%20request%20timed%20out:%20how%20can%20I%20confirm%20its%20outcome%20and%20retry%20safely?%20/%20%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E5%A6%82%E4%BD%95%E7%A1%AE%E8%AE%A4%E6%93%8D%E4%BD%9C%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) and [broker acknowledgements](#38.%20What%20do%20publisher%20confirms%20and%20consumer%20acknowledgements%20prove?%20/%20%E5%8F%91%E5%B8%83%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%88%86%E5%88%AB%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F) for the separate contracts. For the session and transaction lifecycle, see [Data Access and Connection Pools / 数据访问与连接池](#28.%20How%20do%20you%20scope%20an%20ORM%20Session%20and%20diagnose%20pool%20exhaustion?%20/%20%E5%A6%82%E4%BD%95%E9%99%90%E5%AE%9A%20ORM%20Session%20%E4%BD%9C%E7%94%A8%E5%9F%9F%E5%B9%B6%E8%AF%8A%E6%96%AD%E8%BF%9E%E6%8E%A5%E6%B1%A0%E8%80%97%E5%B0%BD%EF%BC%9F).

**Interview answer / 面试回答：** I start from the failure risk and choose the lowest boundary that can prove it. Here the API tests verify validation, public response shape, and tenant-scoped access; a real SQLite database verifies uniqueness and rollback; the repeated worker call verifies the local idempotent state transition. I would add a contract comparison for compatibility and a broker-backed test before claiming delivery or acknowledgement guarantees. / 我先从故障风险出发，选择能够证明该风险的最低边界。这个例子用 API 测试验证输入校验、公开响应结构和租户范围访问，用真实 SQLite 验证唯一性约束与回滚，再用重复 worker 调用验证本地幂等状态变更。要声称兼容既有客户端或消息投递确认语义，还需要契约对比和真实 broker 测试。

**Sources checked 2026-10-15:** [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/) and [testing dependencies with overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/) for in-process request checks and dependency seams; [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) for function-scoped setup and cleanup; SQLAlchemy 2.0 [constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html), [session transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), and [SQLite pooling](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads-or-coroutines); SQLite [CREATE TABLE and UNIQUE constraints](https://www.sqlite.org/lang_createtable.html) and [transactions](https://www.sqlite.org/lang_transaction.html). Runtime behavior was checked with the versions recorded above; the live FastAPI documentation is not a substitute for the named runtime check.
## 48. How do you integrate, revise, or recover Git history without losing work? / 如何在不丢失工作的前提下集成、修改或恢复 Git 历史？

Git stores snapshots behind movable branch references, while the working tree and index hold changes not yet committed. Choose merge or rebase based on whether others rely on the commits, and choose reset, revert, or reflog recovery according to which local or shared history state must change. These commands repair repository history and files; they do not roll back a deployed application, database migration, or external side effect. / Git 用提交保存快照，分支是可移动引用；工作区和暂存区保存尚未提交的修改。根据提交是否已被他人依赖选择合并或变基，再根据需要改变的是哪部分本地或共享历史选择 reset、revert 或 reflog 恢复。这些命令修复的是仓库历史和文件，不会回滚已部署应用、数据库迁移或外部副作用；生产恢复见[应用部署与持续交付](#51.%20How%20do%20you%20promote%20one%20validated%20artifact%20and%20recover%20each%20state%20layer%20safely?%20/%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B7%B2%E9%AA%8C%E8%AF%81%E4%BA%A7%E7%89%A9%E5%B9%B6%E5%88%86%E5%88%AB%E6%81%A2%E5%A4%8D%E5%90%84%E5%B1%82%E7%8A%B6%E6%80%81%EF%BC%9F)。

### Core commands

| Command | Purpose |
|---|---|
| `git init` | Create an empty repository in the current directory |
| `git clone <url>` | Copy a repository and its history |
| `git status` | Show branch and working-tree state |
| `git add <path>` | Stage changes for the next commit |
| `git diff` | Show unstaged changes; use `--staged` for staged changes |
| `git commit -m "message"` | Record the staged snapshot |
| `git log --oneline --graph --decorate` | Inspect recent history and branch references |

Stage deliberately. `git add .` stages changes under the current directory; `git add -A` stages additions, modifications, and deletions in the repository. Review `git diff --staged` before committing.

### Remote operations

~~~bash
git remote add origin <url>
git fetch origin
git push -u origin main
git pull
~~~

`git fetch` updates remote-tracking references without integrating them into the current branch. `git pull` fetches and then integrates the selected upstream using the configured or requested fast-forward, merge, or rebase behavior; inspect its options when the result matters. Fetch first when you want to review incoming commits before integrating them.

### Branching

~~~bash
git branch feature/login       # create a branch
git switch feature/login       # switch branches
git switch -c feature/login    # create and switch
git branch -d feature/login    # delete only when Git considers it merged
git branch -D feature/login    # force-delete the branch reference
~~~

A feature branch is one collaboration approach. A team can instead integrate small changes directly or use a release-branch strategy. Git Flow adds long-lived branches such as `develop`; it can suit scheduled releases but adds merging and coordination. Choose according to release and integration needs rather than treating one strategy as universal.

### Merge vs. rebase

#### `git merge`

Merge integrates another branch into the current branch. If possible, Git may fast-forward the current branch reference; otherwise it creates a merge commit that records both parent histories.

~~~bash
git switch main
git merge feature/login
~~~

~~~
A---B---C---M  main
     \     /
      D---E    feature/login
~~~

#### `git rebase`

Rebase replays commits onto a new base. The replayed commits have new IDs because their parent history changes.

~~~bash
git switch feature/login
git rebase main
~~~

~~~
A---B---C              main
         \
          D'---E'      feature/login
~~~

| Situation | A common choice | Why |
|---|---|---|
| Integrating work while keeping both branch histories visible | Merge | Records the integration point when a merge commit is created |
| Updating an unpublished local branch | Rebase | Replays local commits on the updated base |
| Commits others have already based work on | Coordinate before rebasing | Rebase changes commit IDs and requires collaborators to reconcile history |

A rebase can be useful on a shared branch only when the team coordinates the history rewrite and remote update. The practical rule is to avoid rewriting commits others may rely on.

### Resolving conflicts

When Git cannot combine edits automatically, it marks the affected file:

~~~
<<<<<<< HEAD
const timeout = 3000;
=======
const timeout = 5000;
>>>>>>> feature/login
~~~

1. Inspect the conflict and decide how the changes should combine.
2. Remove the conflict markers and edit the final content.
3. Stage the resolved path with `git add <path>`.
4. Finish with `git commit` after a merge, or `git rebase --continue` during a rebase.

Use `git merge --abort` or `git rebase --abort` to stop an integration that is still in progress.

### Useful commands

#### `git stash`

Save tracked working-tree changes temporarily when switching tasks or branches.

~~~bash
git stash push -m "work in progress"
git stash list
git stash apply       # keep the stash entry
git stash pop         # apply and remove the stash entry if successful
git stash drop        # discard a stash entry
~~~

Untracked files are not included by default; use `-u` when they should be included.

#### `git cherry-pick`

Apply the change introduced by a selected commit to the current branch, creating a new commit.

~~~bash
git cherry-pick <commit>
~~~

For a mistake in existing changes or commits, see [undo and recovery in Git / Git 撤销与找回](#49.%20How%20do%20you%20undo%20or%20recover%20a%20Git%20change%20safely?%20/%20%E6%80%8E%E6%A0%B7%E5%AE%89%E5%85%A8%E6%92%A4%E9%94%80%E6%88%96%E6%89%BE%E5%9B%9E%20Git%20%E6%94%B9%E5%8A%A8%EF%BC%9F).

### Pull request and code review workflow

A common workflow is to branch from the repository's integration branch, commit focused changes, push, open a pull request, review and revise, then merge using the repository's chosen method. The exact branch name and merge policy vary by project.

For commits, concise messages that describe the change help future readers. **Conventional Commits** is one optional convention, often paired with tooling that reads its prefixes:

~~~
feat(auth): refresh access tokens
fix(api): handle missing user
refactor(utils): extract date formatting
docs(readme): clarify setup
~~~

**See also:** [Agile and Scrum](#53.%20How%20does%20Scrum%20help%20a%20team%20inspect%20and%20adapt%20work?%20/%20Scrum%20%E5%A6%82%E4%BD%95%E5%B8%AE%E5%8A%A9%E5%9B%A2%E9%98%9F%E6%A3%80%E6%9F%A5%E5%B9%B6%E8%B0%83%E6%95%B4%E5%B7%A5%E4%BD%9C%EF%BC%9F) for team-process context, and [Frontend Testing](../../frontend/testing/frontend-testing.md) for CI checks in a pull request.

Sources: [Git pull](https://git-scm.com/docs/git-pull), [Git merge](https://git-scm.com/docs/git-merge), [Git rebase](https://git-scm.com/docs/git-rebase), [Git reset](https://git-scm.com/docs/git-reset), [Git revert](https://git-scm.com/docs/git-revert), [Git reflog](https://git-scm.com/docs/git-reflog), [Git stash](https://git-scm.com/docs/git-stash), and [Git cherry-pick](https://git-scm.com/docs/git-cherry-pick). Git manuals checked 2026-10-15.
## 49. How do you undo or recover a Git change safely? / 怎样安全撤销或找回 Git 改动？

Choose by where the change lives and whether other people already rely on it. Revert records a new change that undoes an existing commit. Reset moves a reference and can update local state. The reflog can help locate earlier local reference values. / 先看改动在哪里，以及别人是否已依赖它。revert 新增一个撤销已有提交的提交。reset 移动引用，也可能更新本地状态。reflog 可以帮助定位本地引用先前的位置。

#### `git reset` vs. `git revert`

In its commit form, `git reset` moves the current branch reference and optionally resets the index and working tree. The mode controls which state changes:

| Mode | Branch reference | Index | Tracked working-tree changes |
|---|---|---|---|
| `--soft` | Moves to target | Kept | Kept |
| `--mixed` (default) | Moves to target | Reset to target | Kept |
| `--hard` | Moves to target | Reset to target | Reset to target; conflicting tracked edits are discarded |

~~~bash
git reset --soft HEAD~1
git reset --mixed HEAD~1
git reset --hard HEAD~1
~~~

Use reset to adjust local history or staging when that is the intended scope. `--hard` replaces the working tree and index with the target state and may overwrite untracked files; check `git status` and preserve needed work first. It does not mean “delete every untracked file.”

`git revert <commit>` creates a new commit that applies the inverse of an earlier commit. It is often a better fit for undoing changes already shared in a branch, although conflicts may still need resolution. Reverting a merge commit requires selecting a mainline parent.

#### `git reflog`

The reflog records recent local updates to references such as `HEAD` and branch tips. It can help locate a commit after an accidental reset or branch deletion while the commit remains available.

~~~bash
git reflog
git branch recovery <commit>
~~~

Creating a branch preserves the recovered commit under a name; checking out a raw commit instead leaves HEAD detached. Reflogs are local and expire, so they are not a backup.

[Back to the main question / 返回主问题](#48.%20How%20do%20you%20integrate,%20revise,%20or%20recover%20Git%20history%20without%20losing%20work?%20/%20%E5%A6%82%E4%BD%95%E5%9C%A8%E4%B8%8D%E4%B8%A2%E5%A4%B1%E5%B7%A5%E4%BD%9C%E7%9A%84%E5%89%8D%E6%8F%90%E4%B8%8B%E9%9B%86%E6%88%90%E3%80%81%E4%BF%AE%E6%94%B9%E6%88%96%E6%81%A2%E5%A4%8D%20Git%20%E5%8E%86%E5%8F%B2%EF%BC%9F).
## 50. How do images, containers, volumes, and networks determine state and connectivity? / 镜像、容器、卷和网络如何决定状态留存与服务连通？

An image supplies the read-only filesystem and configuration template; a container adds a writable runtime layer; a volume stores data beyond container replacement; and a shared network gives services a path to reach one another. Port publishing exposes a container port through the host, while secrets belong in the build or runtime channel that needs them. The commands and Compose examples below show what survives removal and how services connect. / 镜像提供只读文件系统和配置模板，容器增加运行时可写层，卷让数据独立于容器替换而留存，共享网络则让服务彼此连通。端口发布通过宿主机暴露容器端口；密钥应只进入实际需要它的构建或运行时通道。下面的命令和 Compose 示例说明删除容器后什么会保留，以及服务如何通信。

Before starting a fresh `postgres:16` instance in the examples below, provide a non-empty `POSTGRES_PASSWORD` through the shell environment or a secret manager. The official image requires it to initialize an empty data directory; it can be passed at runtime without placing a credential in the image or source file. Changing the variable later does not rotate a password in an already initialized volume.

### Common operations

| Task | Command | Notes |
|---|---|---|
| Download an image | `docker pull redis:7` | Pin a tag or digest when repeatability matters; a tag may move. |
| List local images | `docker image ls` | Images can have multiple tags. |
| Create and start a container | `docker run --name cache -d redis:7` | Pulls the image if it is not available locally. |
| List running containers | `docker ps` | Add `-a` to include stopped containers. |
| Stop / start a container | `docker stop cache` / `docker start cache` | A stopped container still exists. |
| Read container logs | `docker logs cache` | Add `-f` to follow new output. |
| Run a command in a running container | `docker exec -it cache /bin/sh` | Run only when the image includes `/bin/sh`; minimal images may contain no shell. |
| Remove a stopped container | `docker rm cache` | `-f` also stops and removes a running container. |
| Remove an image | `docker image rm redis:7` | Refer to an image tag or image ID, not a container ID. |

Detached mode (such as `docker run -d`) returns the terminal while the container's main process runs. It does not supervise an application or guarantee that the container stays healthy. Use `docker ps` and `docker logs` to inspect it.

---

### Publish ports

A port mapping forwards a host port to a port in the container. This publishes a container service to the host network; it does not make the service healthy or authenticated.

~~~bash
docker run -d --name cache -p 127.0.0.1:6000:6379 redis:7
~~~

Binding to `127.0.0.1` limits host access to the local machine. Omitting the host IP generally publishes on all host interfaces, subject to the host and Docker networking configuration. Container-to-container traffic on a shared Docker network normally uses the container port directly, not a published host port.

---

### Networks

A user-defined bridge network lets attached containers communicate by container or service name through Docker's embedded DNS. Network membership controls which containers can connect at the Docker network layer; it is not application authentication or authorization.

~~~bash
docker network create app-net
docker run -d --name db --network app-net \
  --env POSTGRES_PASSWORD postgres:16
~~~

Only expose a host port when a process outside the network needs to connect. In Compose, services join a project network by default and can usually use each other's service names as hostnames.

---

### Volumes and persistent data

Container writable layers are removed with their containers. A **named volume / 命名卷** is managed by Docker and remains after the container is removed. A **bind mount / 绑定挂载** maps a host path into the container and is useful when both host and container need the files. A volume is not a backup; plan backups and restore tests separately.

Omitting the volume source creates an anonymous volume with a generated name; it normally persists after container removal but is not automatically reused by a later container.

~~~bash
docker volume create db-data
docker run -d --name db --env POSTGRES_PASSWORD \
  --mount type=volume,src=db-data,dst=/var/lib/postgresql/data postgres:16
~~~

The destination path belongs to the image or application, so check that product's documentation. Compose declares named volumes at the top level:

~~~yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
~~~

Compose normally preserves declared named volumes on `docker compose down`. Adding `-v` removes project volumes and their data; review that effect before using it.

---

### Compose

Compose describes a multi-container application in a YAML file. The default project network provides service-name discovery, so an application container can address the database as `db` on its container port. Publish a port only when the host or another external network needs access.

~~~yaml
services:
  app:
    build: .
    environment:
      DATABASE_HOST: db
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
~~~

~~~bash
docker compose up -d
docker compose ps
docker compose logs -f app
docker compose down
~~~

The current Compose Specification is used by Compose V2. Its top-level `version` field is obsolete and does not select a schema version. The older standalone `docker-compose` command is a legacy interface; use `docker compose` with the Compose CLI plugin.

---

### Dockerfile and image builds

A Dockerfile describes image build steps. `RUN` executes during build; `CMD` supplies a default command or arguments when a container starts; `ENTRYPOINT` defines the executable to run. A runtime command can override `CMD`.

~~~dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
CMD ["node", "dist/index.js"]
~~~

Build with `docker build -t my-app:1.0 .`. This example assumes a package lockfile. The build context is the set of files sent to the builder; use a `.dockerignore` file to exclude files such as local dependencies, version-control data, and secrets. Multi-stage builds keep build-only stages out of the final image unless files are copied from them. Copy only the runtime files and dependencies the application needs.

Do not put credentials in a Dockerfile's `ENV` or `ARG` values. Use a BuildKit secret mount for a credential needed during build; it is made available to the build instruction without baking it into the image. At runtime, Compose secrets can be granted to selected services and mounted as files; protect the source secret file and host.

~~~dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
~~~

~~~bash
docker build --secret id=npmrc,src=.npmrc -t my-app:1.0 .
~~~

To push an image to a registry, authenticate with that registry, tag the image with its repository address, and push the tag. These commands use placeholders; `docker login` prompts or uses configured credentials, which should not be committed:

~~~bash
docker login registry.example.com
docker tag my-app:1.0 registry.example.com/team/my-app:1.0
docker push registry.example.com/team/my-app:1.0
~~~

Sources: [official PostgreSQL image environment variables and secrets](https://github.com/docker-library/docs/blob/master/postgres/README.md#environment-variables), [Docker image and container concepts](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/), [Docker networking](https://docs.docker.com/engine/network/), [port publishing](https://docs.docker.com/engine/network/port-publishing/), [Docker volumes](https://docs.docker.com/engine/storage/volumes/), [Compose file reference](https://docs.docker.com/compose/compose-file/), [Compose variable interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/), [`docker run` environment variables](https://docs.docker.com/reference/cli/docker/container/run/#set-environment-variables--e---env), [Docker build secrets](https://docs.docker.com/build/building/secrets/), [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/), [`docker login`](https://docs.docker.com/reference/cli/docker/login/), [`docker tag`](https://docs.docker.com/reference/cli/docker/image/tag/), and [`docker push`](https://docs.docker.com/reference/cli/docker/image/push/). Docker documentation checked 2026-10-15.
## 51. How do you promote one validated artifact and recover each state layer safely? / 如何晋级已验证产物并分别恢复各层状态？

Build one immutable application artifact, test those exact bits, and promote the same artifact through staging to production with runtime configuration supplied separately. Readiness and gradual rollout protect traffic while error, latency, and saturation signals establish whether to stop or return to the last known-good application version. Persistent data and external effects have separate owners and recovery paths: image rollback cannot reverse a database migration, sent email, payment, or other completed action. / 构建一个不可变应用产物，验证这份确切产物，再把同一产物从预发环境晋级到生产，并单独注入运行时配置。就绪检查和渐进式放量保护流量，错误率、延迟和资源饱和信号决定是否暂停或恢复到上一个已知正常的应用版本。持久数据和外部副作用各有其所有者与恢复路径：镜像回滚不能撤销数据库迁移、已发送邮件、支付或其他已完成操作。

The [production request path and responsibility model](#52.%20How%20do%20deployment%20components%20carry%20a%20request%20and%20share%20responsibilities?%20/%20%E9%83%A8%E7%BD%B2%E7%BB%84%E4%BB%B6%E6%80%8E%E6%A0%B7%E6%89%BF%E6%8E%A5%E8%AF%B7%E6%B1%82%E5%B9%B6%E5%88%86%E6%8B%85%E8%81%8C%E8%B4%A3%EF%BC%9F) explains which components run the service and own its data. The following steps focus on how a tested artifact safely replaces the one serving traffic.

### One artifact from checks to production / 一个产物经过检查再到生产

Use one generic path and adapt the checks to actual regression risks:

~~~text
commit
  -> static/type checks -> unit and integration checks -> production build
  -> test the built artifact -> publish it with commit and content identity
  -> deploy that same artifact to staging -> smoke/browser check
  -> protected production gate -> gradual traffic shift -> observe and complete
~~~

Build once, then promote the same artifact. For a container, record and deploy its immutable digest rather than a mutable tag; for a static bundle, retain a checksum or release identifier with the emitted files. Rebuilding separately for staging and production weakens the claim that the tested bits are the deployed bits. If frontend configuration is compiled into the bundle, that bundle is environment-specific; a shared artifact needs safe public runtime configuration. Values shipped to a browser are public, never secrets.

Inject secrets at runtime from a secret store or protected deployment environment, and give the deployment identity only the permissions needed for its target. Keep non-secret environment configuration separate from the image. A deployment environment can also restrict source branches, protect production with approval, and scope access to environment secrets; these controls protect the release gate, while credentials still need rotation and least privilege.

Readiness is a traffic gate: an instance should receive requests only when it can serve its assigned work. Liveness is a restart signal for a process that cannot recover on its own. Exact probe behavior varies by platform; do not make liveness depend on every transient downstream service, since a database outage can then trigger a restart storm. Roll out gradually when the platform and workload permit it, watch a small set of error, latency, and saturation thresholds, and stop or redeploy the last known-good artifact when they cross the release limit. A green process probe alone does not prove the user journey works.

Database changes need an independent compatibility plan. A common expand-and-contract sequence adds a backward-compatible schema shape, deploys code that tolerates both shapes, backfills or dual-writes as needed, switches reads, and removes the old shape only after old code and the rollback window are gone. Run migrations as a controlled step rather than once per replica. Redeploying an older image does not reverse a schema migration, sent email, payment, or other external side effect; rollback may require a forward fix, an idempotent compensating action, or a tested restore plan. Restoring a backup can discard writes made after that backup, so it is a recovery decision rather than a routine application rollback.

For the frontend-specific type/test/build and critical-browser-check sequence, see [Frontend Testing / 前端测试](../../frontend/testing/frontend-testing.md). The existing [Docker Operations / Docker操作参考](#50.%20How%20do%20images,%20containers,%20volumes,%20and%20networks%20determine%20state%20and%20connectivity?%20/%20%E9%95%9C%E5%83%8F%E3%80%81%E5%AE%B9%E5%99%A8%E3%80%81%E5%8D%B7%E5%92%8C%E7%BD%91%E7%BB%9C%E5%A6%82%E4%BD%95%E5%86%B3%E5%AE%9A%E7%8A%B6%E6%80%81%E7%95%99%E5%AD%98%E4%B8%8E%E6%9C%8D%E5%8A%A1%E8%BF%9E%E9%80%9A%EF%BC%9F) note covers image construction and local container mechanics.

**Interview answer / 面试回答：** Start with the request/data path and trust boundaries, then choose the least operational runtime that meets workload constraints. Build and verify one immutable artifact, inject runtime configuration and secrets, release behind readiness and monitored thresholds, and keep schema or external-state recovery separate from image rollback. / 先画出请求和数据路径及信任边界，再按负载约束选择运维负担最低的运行时。构建并验证一个不可变产物，运行时注入配置和密钥，在就绪检查与监控阈值保护下发布，并把数据库和外部状态的恢复方案与镜像回滚分开。

**Sources checked 2026-10-15:** [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html); [AWS VPC network example](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-example-private-subnets-nat.html); [ECS task IAM roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html); [Application Load Balancer health checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html); [ECS deployment circuit breaker](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html); [Kubernetes v1.37 probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/); [Amazon RDS shared responsibility and query tuning](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/); [Amazon S3 access control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-management.html); [S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html); [Amazon SQS standard queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html); [SQS dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html); [AWS Fargate pricing dimensions](https://aws.amazon.com/fargate/pricing/); [Amazon RDS pricing](https://aws.amazon.com/rds/pricing/); [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/); [Docker Compose in production](https://docs.docker.com/compose/how-tos/production/); [Docker image digests](https://docs.docker.com/dhi/explore/security-concepts/digests/); [GitHub Actions deployment environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments); [CodeDeploy rollback behavior](https://docs.aws.amazon.com/codedeploy/latest/userguide/deployments-rollback-and-redeploy.html); [Vite static deployment](https://vite.dev/guide/static-deploy.html). AWS examples document one provider's current service boundaries and are not universal defaults; verify the selected provider, service, region, and configuration.
## 52. How do deployment components carry a request and share responsibilities? / 部署组件怎样承接请求并分担职责？

Trace compute, networking, and storage along the request path. Managed infrastructure can operate a component, while the application still defines its data, access, workload and recovery policy. / 沿请求路径定位计算、网络和存储。托管基础设施可以代为运行组件，应用仍需定义数据、权限、负载和恢复策略。

### Request and data path / 请求与数据路径

For a typical web application, the browser talks only to public entry points; server-side services reach databases, object storage, and queues through controlled routes and identities:

~~~text
Name lookup, before the connection:
Browser -- DNS query for app.example --> resolver
resolver -- CDN / load-balancer address --> Browser

HTTPS request:
Browser -- HTTPS --> CDN (optional) --> public load balancer
                                          |
                                          v
                                 private API compute
                                  /      |       \
                             database  objects    queue --> workers
~~~

The load balancer terminates or forwards HTTPS and sends requests only to configured targets. Compute runs the API and workers. A database stores structured state, object storage holds large files, and a queue separates work that can finish asynchronously. A browser may upload or download an object through a narrowly scoped, expiring signed URL; that does not require making the storage bucket public.

Network reachability and authorization are separate checks. A route table, firewall or security group decides which network paths exist; an identity and resource policy decides which actions a reachable principal may perform. A common layout exposes only the load-balancer listener, permits API traffic from the load balancer, and permits database traffic only from the API. Keep data services private where the provider supports it, and add controlled outbound access or private service endpoints only when required. A task or workload identity should receive only the actions and resources it needs; application users still need application-level authorization. / 网络可达不等于有权访问：网络规则控制通信路径，IAM 与资源策略控制主体能执行的操作。应用运行身份应只获得所需资源和操作权限；业务用户的授权仍由应用负责。

### Managed service and application responsibilities / 托管服务与应用责任

| Layer / 层 | Provider or platform manages / 平台管理 | Application team owns / 应用团队负责 |
|---|---|---|
| Compute / 计算 | Underlying hardware and, depending on the offer, host maintenance and scheduling. | Image or package, startup and shutdown behavior, resource limits, scaling policy, and application health. |
| Database / 数据库 | Database service infrastructure and only the backups, patching, and failover included in the selected configuration. | Schema and migrations, query and connection behavior, access grants, retention choices, and restore testing. |
| Object storage / 对象存储 | Storage service availability and documented durability mechanisms. | Object naming, privacy, retention/lifecycle, upload limits, and who receives a signed URL. |
| Queue / 队列 | Message storage and delivery within service guarantees and configured limits. | Idempotent processing, retry/backoff, poison-message handling, queue age, and dead-letter recovery. |

“Managed” removes some infrastructure work; it does not choose safe defaults for the workload. Read the service contract and configuration: automated backups, retention, public access, network placement, and failover behavior are often selectable. A managed database cannot fix an unindexed query or a connection storm, and a managed queue cannot make a non-idempotent consumer safe to retry.

Choose a runtime by workload constraints. A managed application platform or function service can reduce host operations for ordinary stateless APIs or bounded event-driven jobs, subject to its execution, startup, and networking limits. A managed container service fits long-running APIs and queue workers when packaging and process control matter. Use virtual machines when the workload needs host-level control or a legacy environment, and budget for operating-system patching and capacity management. Compare steady and peak load, required minimum capacity, startup/cold-start tolerance, execution duration, portability, and the team’s ability to operate the platform; “serverless” does not mean state-free or cost-free.

### Failure and cost model / 故障与成本模型

| Boundary / 边界 | Failure to plan for / 需要考虑的故障 | Cost or limit to watch / 成本或限制 |
|---|---|---|
| Load balancer and network / 负载均衡与网络 | Bad route or listener, no healthy targets, blocked egress, or an expired certificate. | Requests and processed bytes, public addresses, NAT gateways, and cross-zone or internet data transfer. |
| Compute / 计算 | Startup failure, crash loop, CPU/memory saturation, or slow scale-out. | Minimum replicas and CPU/memory time; autoscaling cannot create capacity instantly. |
| Database / 数据库 | Exhausted connections, lock contention, storage or I/O limits, or failover delay. | Provisioned compute, storage, I/O, replicas, and retained backups. |
| Object storage / 对象存储 | Permission errors, unavailable routes, unexpectedly public objects, or unbounded retention. | Stored bytes, requests/retrieval, lifecycle transitions, replication, and outbound transfer. |
| Queue and workers / 队列与工作进程 | Duplicate or delayed delivery, poison messages, or growing backlog. | Requests, retained messages, worker compute, and the delay before backlog drains. |

Track each boundary with a useful signal: request errors and latency at ingress, ready replica count and saturation for compute, connection/query pressure for the database, request errors and object growth for storage, and oldest-message age plus dead-letter count for a queue. Cost estimates should include idle minimums and peak headroom as well as per-use storage, requests, and data movement; a service with a low unit price can still be expensive when retries or egress multiply the workload.

[Back to the main question / 返回主问题](#51.%20How%20do%20you%20promote%20one%20validated%20artifact%20and%20recover%20each%20state%20layer%20safely?%20/%20%E5%A6%82%E4%BD%95%E6%99%8B%E7%BA%A7%E5%B7%B2%E9%AA%8C%E8%AF%81%E4%BA%A7%E7%89%A9%E5%B9%B6%E5%88%86%E5%88%AB%E6%81%A2%E5%A4%8D%E5%90%84%E5%B1%82%E7%8A%B6%E6%80%81%EF%BC%9F).
## 53. How does Scrum help a team inspect and adapt work? / Scrum 如何帮助团队检查并调整工作？

**核心回答 / Core answer：** Agile names values and principles that favor collaboration, usable software, customer feedback, and adapting to change; Scrum is one framework that gives a team accountabilities, events, artifacts, and commitments to inspect progress and adjust its next steps. Product Goals, Sprint Goals, and the Definition of Done orient decisions, while a Sprint Backlog plan can change as the Developers learn. A Sprint Review examines outcomes and next adaptations; it is not a release gate. The framework creates opportunities for feedback but does not guarantee good delivery by itself. / 敏捷描述重视协作、可用软件、客户反馈和响应变化的价值与原则；Scrum 则用职责、事件、工件和承诺，帮助团队检查进展并调整下一步。产品目标、Sprint 目标和完成定义为决策提供方向，Developers 可随着学习调整 Sprint Backlog 计划。Sprint Review 检视成果并讨论后续调整，它不是发布审批关卡。框架提供反馈机会，但本身不能保证交付效果。

### Agile principles

The Agile Manifesto values:

- Individuals and interactions over processes and tools.
- Working software over comprehensive documentation.
- Customer collaboration over contract negotiation.
- Responding to change over following a plan.

The items on the right still have value; the Manifesto gives greater weight to the items on the left. Its principles also emphasize frequent delivery, sustainable pace, technical excellence, simplicity, and regular reflection. How a team applies these ideas depends on its product, people, and constraints.

### Scrum framework

Scrum uses empiricism and lean thinking to help a Scrum Team generate value through adaptive solutions. Its defined structure is not a promise that adopting the framework will automatically improve delivery.

#### Roles

The Scrum Guide describes three **accountabilities / 职责** within one Scrum Team; these are responsibilities, not a required set of job titles.

##### Product Owner

Accountable for maximizing product value and effective Product Backlog management. The Product Owner may delegate backlog work but remains accountable for the result.

##### Scrum Master

Accountable for establishing Scrum as defined in the Guide and for the Scrum Team's effectiveness. This includes coaching, helping remove impediments, and supporting the wider organization in its use of Scrum; it does not make the Scrum Master the team's line manager.

##### Developers

The people who create a usable Increment during each Sprint. They create and adapt the Sprint Backlog plan, uphold the Definition of Done, and hold one another accountable as professionals.

#### Events

The five events are the **Sprint**, **Sprint Planning**, **Daily Scrum**, **Sprint Review**, and **Sprint Retrospective**. The Sprint is the container for the other events and activities.

##### Sprint

A fixed-length event of one month or less. Teams choose a duration that supports inspection and adaptation; two weeks is common in some teams but is not prescribed by Scrum. The Sprint Goal provides a coherent objective while allowing the exact work to be clarified as learning occurs.

##### Sprint Planning

The Scrum Team plans why the Sprint is valuable, what can be done, and how the selected work will be completed. The output includes a Sprint Goal and the Developers' plan in the Sprint Backlog.

##### Daily Scrum

A 15-minute event for the Developers to inspect progress toward the Sprint Goal and adapt their plan. The Guide does not require each person to answer a fixed set of status questions. Developers choose a format that serves the purpose and may meet more often as needed.

##### Sprint Review

The Scrum Team and stakeholders inspect the Sprint's outcome and discuss adaptations. It is a working session to inform what to do next, not only a demonstration.

##### Sprint Retrospective

The Scrum Team inspects how the last Sprint went with regard to people, interactions, processes, tools, and the Definition of Done, then identifies useful improvements. It is one of the Scrum events and occurs within the Sprint cadence.

#### Artifacts

| Artifact / 工件 | Commitment / 承诺 | Purpose |
|---|---|---|
| Product Backlog / 产品待办列表 | Product Goal / 产品目标 | An ordered source of work for evolving the product |
| Sprint Backlog / Sprint 待办列表 | Sprint Goal / Sprint 目标 | The Sprint Goal, selected Product Backlog items, and the Developers' plan |
| Increment / 增量 | Definition of Done / 完成定义 | A usable step toward the Product Goal that meets the shared quality measure |

The commitments focus the artifact without replacing it. Multiple Increments may be created during a Sprint; the Sprint Review is not a release gate.

### Common challenges

- **Treating Scrum as a status-report schedule:** the events exist to inspect and adapt work toward goals, not merely to report individual activity.
- **Treating the Sprint Backlog as an unchangeable contract:** the Developers adapt their plan as they learn, while working toward the Sprint Goal. The Product Owner and Developers can clarify and renegotiate scope without endangering that goal.
- **Skipping inspection and improvement:** omitting defined events loses their intended opportunities and means the team is not using the framework as described.
- **Assuming Scrum fits every problem:** choose a way of working that fits the product, feedback cycle, and organizational constraints. Regulated work can also use iterative development when its evidence and control requirements are built into the process.

**See also:** [Interview Tips](#54.%20How%20do%20you%20prepare%20behavioral%20answers%20with%20evidence%20you%20can%20support?%20/%20%E5%A6%82%E4%BD%95%E5%87%86%E5%A4%87%E6%9C%89%E4%BA%8B%E5%AE%9E%E4%BE%9D%E6%8D%AE%E3%80%81%E7%BB%8F%E5%BE%97%E8%B5%B7%E6%A0%B8%E5%AE%9E%E7%9A%84%E8%A1%8C%E4%B8%BA%E9%9D%A2%E8%AF%95%E5%9B%9E%E7%AD%94%EF%BC%9F) for discussing team practices accurately.

Sources: [The Scrum Guide, November 2020](https://scrumguides.org/scrum-guide.html) and the [Agile Manifesto](https://agilemanifesto.org/).
## 54. How do you prepare behavioral answers with evidence you can support? / 如何准备有事实依据、经得起核实的行为面试回答？

Begin with the role's needs and facts from your own experience. Shape one relevant example as context → action you personally took → result or other evidence; describe qualitative outcomes plainly and never invent a metric or someone else's story. Research current role, company, location, and compensation details before the conversation, state skill gaps honestly, and prepare questions that help you understand the work. / 从岗位需求和自己真实经历中的事实开始。选择一个相关例子，按背景 → 个人行动 → 结果或其他证据组织；定性结果应如实描述，不要编造指标或借用别人的故事。面试前调研当前岗位、公司、地点和薪酬信息，坦诚说明技能缺口，并准备能帮助自己了解工作的提问。

### Discussing strengths and weaknesses

#### Strengths

Choose a strength that matters for the role, then support it with one real example. A compact structure is **context → action you took → result or evidence**.

- “I work carefully with edge cases. In [specific situation], I [action I personally took], which led to [verifiable result].”
- “I learn unfamiliar tools by [specific method]. For example, I used that approach to [real task] and [what changed or what I learned].”

Replace each bracketed part with your own evidence. If the result is qualitative, describe what changed without inventing a metric.

#### Weaknesses

**诚实说明一个真实的发展方向，并说明正在采取的步骤。** Choose something you are actively improving and explain how you notice progress. Avoid presenting a disguised strength or claiming a weakness that would prevent you from doing the role's core work.

- “I am still developing [skill]. I have been improving it by [specific practice], and I can now [observable progress].”

### Salary expectations

- Research a current range for the role, seniority, location, and total compensation before the conversation.
- If you are ready to give a number, state a range and the assumptions behind it; leave room to discuss the full package.
- If the responsibilities are not yet clear, ask about the role's level and compensation range before giving a precise expectation.

### Why are you a good fit?

Connect the role's stated needs to evidence you actually have:

1. **Skills match / 技能匹配** — identify the relevant requirement.
2. **Evidence / 事实依据** — give a project, responsibility, or result that demonstrates it.
3. **Motivation / 求职动机** — explain which part of this role you want to work on.

Template: “This role needs [requirement]. In [real example], I [specific contribution] and [result or learning]. I am interested in applying that experience to [specific part of the role].”

### Company research

- Understand the product, users, and the role's team from current company materials.
- Connect your experience to a specific need instead of reciting company slogans.
- If you do not know a detail, say what you have learned so far and ask a focused question.

### Addressing lack of experience

State the gap plainly, then describe related experience and a realistic learning plan. Avoid guaranteeing that you will master an unfamiliar area by a fixed date unless you have a basis for that estimate.

Template: “I have not used [technology] in [relevant context]. I have used [related skill] for [real example], and I would start by [specific way to learn or validate the new system].”

### Questions to ask the interviewer

Prepare questions that help you understand the work. Choose the ones that remain unanswered by the conversation.

**About the role:**

- “What are the most important outcomes for this role in the first few months?”
- “What technical challenges would this person work on?”
- “How do you measure success for the position?”

**About the team:**

- “How does the team approach code review and knowledge sharing?”
- “How are technical decisions made, and who is involved?”

**About growth:**

- “What opportunities are there to deepen or broaden engineering skills?”
- “How does the team support progression for engineers?”

### Closing the interview

Thank the interviewer, restate a specific reason for your interest, and ask about the next step if it has not already been explained. If your questions were answered during the discussion, say so and use the remaining time for a follow-up.

**See also:** [Agile and Scrum](#53.%20How%20does%20Scrum%20help%20a%20team%20inspect%20and%20adapt%20work?%20/%20Scrum%20%E5%A6%82%E4%BD%95%E5%B8%AE%E5%8A%A9%E5%9B%A2%E9%98%9F%E6%A3%80%E6%9F%A5%E5%B9%B6%E8%B0%83%E6%95%B4%E5%B7%A5%E4%BD%9C%EF%BC%9F) for the current Scrum vocabulary used in team-process discussions.
