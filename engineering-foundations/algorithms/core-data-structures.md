# Core Data Structures / 核心数据结构

A tree organizes values through parent-child links. Complexity claims below assume the stated structure and operation; an unbalanced search tree or a search that must find a node by scanning does not get balanced-tree bounds.

数据结构决定数据的组织方式和常见操作的代价；选择时要看实际访问模式以及平衡、前驱链接等表示条件，不能把某种结构下的复杂度推广到所有实现。

## Tree traversals

For a binary tree, depth-first orders differ in when the current node is visited:

- **In-order / 中序**: left, node, right. This yields ascending values only when the tree satisfies the binary-search-tree ordering rule.
- **Pre-order / 前序**: node, left, right. Useful when serializing a tree with enough structure to recover its shape.
- **Post-order / 后序**: left, right, node. Useful when computing or releasing children before their parent.

### Kth smallest in a BST

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

## Trees and operation costs

| Structure | Indexed access / search | Insert or delete |
|---|---|---|
| Array | Index access O(1); value search O(n) | Middle insert/delete O(n) because elements move |
| Linked list | Finding by value or index O(n) | O(1) insertion at a known link; deletion needs the predecessor link (singly linked) or target node (doubly linked), otherwise O(n) worst case |
| Height-balanced BST | Search O(log n) | O(log n) |
| Unbalanced BST | Worst-case search O(n) | Worst-case O(n) |

A balanced search tree gives logarithmic operations by keeping height logarithmic. If insertions produce a chain, those operations degrade to linear time. Array access remains fast by index, while inserting into the middle shifts later elements.

These bounds do not capture cache locality or dependency chains. See [Memory Hierarchy and Data Locality / 内存层次与数据局部性](../operating-systems/memory-hierarchy-and-data-locality.md) for why contiguous scans can outperform pointer-based traversal and when a known-node list update is actually O(1).

---

## Self-balancing trees

### Red-Black Tree

A red-black tree is a binary search tree with coloring invariants that bound its height. Red nodes have black children, and every path from a node to a descendant leaf has the same black height; implementations also treat the root and leaf sentinels as black. These rules give O(log n) worst-case search, insertion, and deletion.

Java's `TreeMap` explicitly documents a red-black-tree implementation. C++ `std::map` specifies ordered associative behavior and logarithmic lookup, insertion, and key-removal bounds, but its standard does not prescribe a tree shape. Check the language and library documentation before inferring a product's internal structure: [Java `TreeMap`](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/TreeMap.html) and [C++ associative containers](https://eel.is/c++draft/associative.reqmts).

### B-Tree and B+ Tree

B-trees are multi-way search trees designed to reduce storage-page reads by keeping several keys in each node.

- In a B-tree, records or record references may be stored in internal nodes as well as leaves.
- In a B+ tree, internal nodes guide the search and records are stored at leaves; leaf links commonly support ordered range scans.

These are family descriptions, not a guarantee that every database index uses the same variant or layout. Check the database's manual for its index type and behavior.

---

## Trie (prefix tree)

A trie shares prefixes between keys. Lookup takes O(m) steps for a key of length m when each next edge can be selected in constant expected time; the cost depends on the node's child representation. Tries can use substantial memory when keys share few prefixes.

Use one when prefix traversal or prefix queries are central, such as autocomplete or routing tables; a hash map may be simpler for exact-key lookup.

---

## DOM tree traversal

A DOM tree is a hierarchy of Node objects. Pass an explicit visit callback and a node or null root. Snapshot each node's children before walking so the traversal has a clear view if callbacks mutate the DOM.

### DFS — depth-first search

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

### BFS — breadth-first search

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

## Array ↔ Tree conversion

Flat rows with parent identifiers can be transformed into a hierarchy for a tree UI or converted back for an API or database representation. This example expects unique IDs, one root whose parent ID is 0, and each other row to reference an existing parent.

### Array to tree

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

### Tree to array

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

**See also:** [Algorithms and Complexity](./algorithms-and-complexity.md) for searches and dynamic programming, and [Practical Data Structure Implementations](./practical-data-structure-implementations.md) for LRU caches, queues, and stacks.
