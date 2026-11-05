# How do ordered inputs enable binary search and two pointers? / 有序输入怎样支持二分查找和双指针？

Use ordering to prove which candidates can be discarded. Binary search shrinks a range around a monotone decision. Two pointers use relationships between positions to rule out a whole set of pairs at each move. / 用有序性证明哪些候选可以排除。二分按单调判断缩小范围，双指针利用位置之间的关系，每次移动时排除一组组合。

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

[Back to the main question / 返回主问题](algorithms-and-complexity.md).
