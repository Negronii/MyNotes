# Algorithms and Complexity / 算法与复杂度分析

Use this reference for common algorithmic patterns. The code states its input assumptions; Big-O describes growth with input size, not a promise about constant factors or a particular runtime.

先根据输入约束和不变量选择算法，再用时间与空间复杂度评估输入规模增长带来的成本；复杂度描述增长趋势，不等于实际耗时。

## Dynamic programming

**动态规划 / Dynamic programming** stores results for overlapping subproblems. Top-down memoization follows the recursive definition; bottom-up iteration computes states in dependency order and can often retain only the state still needed.

### Fibonacci

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

### Climbing stairs (frog jump)

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

### 0/1 Knapsack

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

## Binary search

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

## Two pointers

**双指针 / Two pointers** uses two positions to reduce repeated scans when the input structure provides an ordering or movement invariant. It is not a general replacement for nested loops; the invariant must justify discarding part of the search space.

### Two Sum on a sorted array

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

### Move zeros to the end

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

## Sorting

### Quicksort

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

## String algorithms

The examples iterate Unicode code points with `Array.from`; that keeps surrogate pairs together. A user-perceived character can contain multiple code points, so grapheme-aware text operations need segmentation and may also need normalization.

### Palindrome check

~~~javascript
function isPalindrome(value) {
  const characters = Array.from(String(value));
  for (let left = 0, right = characters.length - 1; left < right; left++, right--) {
    if (characters[left] !== characters[right]) return false;
  }
  return true;
}
~~~

### Longest consecutive character

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

### Number formatting (thousand separators)

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

### Switch ASCII letter case

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

**See also:** [Core Data Structures](./core-data-structures.md) for trees and tries, and [Practical Data Structure Implementations](./practical-data-structure-implementations.md) for LRU caches, queues, and stacks.
