# How do input constraints and access patterns determine algorithm choice and complexity? / 输入约束与访问模式如何决定算法选择和复杂度？

Choose an algorithm by the invariant the input provides, then count the work and storage required as the input grows. Dynamic programming reuses overlapping states; binary search discards half of a sorted search range; two pointers move only when ordering proves a region cannot contain the answer. Big-O summarizes that growth under stated assumptions, while representation, allocation, memory locality, and runtime constants still affect elapsed time.

先利用输入所提供的不变量选择算法，再计算输入规模增长时所需的操作和存储。动态规划复用重叠子问题，二分查找利用有序性缩小搜索区间，双指针则只在排序等条件足以证明某一段不含答案时移动。Big-O 概括这些前提下的增长趋势；表示方式、分配、内存局部性和运行时常数仍会影响实际耗时。

Big-O leaves out cache locality, memory bandwidth, and dependent loads. See [Memory Hierarchy and Data Locality / 内存层次与数据局部性](../operating-systems/memory-hierarchy-and-data-locality.md) for the hardware costs that can change elapsed time without changing an operation's asymptotic bound.

## Match the technique to the input / 按输入约束选择方法

- When several states repeat and each can be defined from earlier ones, choose a [dynamic programming state and update order](dynamic-programming-state-and-order.md).
- When order rules out a group of candidates, use [binary search or two pointers](ordered-array-search.md) and prove why the discarded range is safe to ignore.
- If the job is reordering, inspect how [partition balance and copying change sorting cost](partitioning-and-sorting-costs.md).
- For text, choose [the units that define length and equality](text-units-and-algorithms.md) before analyzing a loop.

## Big-O reference

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

**See also:** [Core Data Structures](./core-data-structures.md) for trees and tries, and [Practical Data Structure Implementations](./practical-data-structure-implementations.md) for LRU caches and [queues and stacks](queue-and-stack-representations.md) for removal-order implementations.
