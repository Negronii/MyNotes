# How do you traverse and mutate the DOM tree? / 如何遍历和修改 DOM 树？

DOM nodes form a parent-child tree. Select the intended node, create new elements explicitly, and insert, remove, or clone nodes through their parent relationship; this archived example also builds a table from structured data. / DOM 节点构成父子树。先选择目标节点，再显式创建元素，并通过父子关系插入、删除或克隆节点；本归档示例还用结构化数据动态生成表格。

## Node Operations in Modern Front-End Development

Node operations are essential for manipulating the DOM (Document Object Model). These operations allow you to find, create, manipulate, and remove elements within the DOM, making front-end development more dynamic and interactive.

## Node Types and Properties

Every node in the DOM has the following properties:

- `nodeType`: Represents the type of the node (element, attribute, text, etc.).
- `nodeName`: The name of the node (tag name for elements).
- `nodeValue`: The value of the node (for text nodes).

### Common Node Types

1. **Element Node (`nodeType = 1`):** Represents HTML elements.
   ```javascript
   let elementNode = document.createElement('div');
   console.log(elementNode.nodeType); // 1
   ```

2. **Attribute Node (`nodeType = 2`):** Represents attributes of elements.
   ```javascript
   let attributeNode = document.createAttribute('class');
   console.log(attributeNode.nodeType); // 2
   ```

3. **Text Node (`nodeType = 3`):** Represents text content within elements.
   ```javascript
   let textNode = document.createTextNode('Hello, World!');
   console.log(textNode.nodeType); // 3
   ```

## Accessing Parent Node

`node.parentNode` returns the closest parent node of the specified node. If there is no parent, it returns `null`.

**Example**

```html
<div class="box1">
  <div class="box2"></div>
</div>
```

```javascript
let box2 = document.querySelector('.box2');
console.log(box2.parentNode); // <div class="box1"></div>
```

## Accessing Child Nodes

1. **`parentNode.childNodes`:** Returns a live `NodeList` of child nodes, including element, text, and comment nodes. Attributes are not children.
   ```javascript
   let children = parentNode.childNodes;
   children.forEach(child => {
       if (child.nodeType === 1) {
           // Element node
       }
   });
   ```

2. **`parentNode.children`:** Returns a live HTMLCollection of only element child nodes.
   ```javascript
   let children = parentNode.children;
   ```

3. **`parentNode.firstChild` and `parentNode.lastChild`:** Return the first and last child nodes, respectively, regardless of type.
   ```javascript
   let firstChild = parentNode.firstChild;
   let lastChild = parentNode.lastChild;
   ```

4. **`parentNode.firstElementChild` and `parentNode.lastElementChild`:** Return the first and last element child nodes, respectively.
   ```javascript
   let firstElementChild = parentNode.firstElementChild;
   let lastElementChild = parentNode.lastElementChild;
   ```

### Example of Using `children`

```javascript
let div = document.querySelector('.box1');
console.log(div.children); // HTMLCollection of element children
console.log(div.children[0]); // First element child
console.log(div.children[div.children.length - 1]); // Last element child
```

## Accessing Sibling Nodes

1. **`node.nextSibling` and `node.previousSibling`:** Return the next and previous sibling nodes, respectively, regardless of type.
   ```javascript
   let nextSibling = node.nextSibling;
   let previousSibling = node.previousSibling;
   ```

2. **`node.nextElementSibling` and `node.previousElementSibling`:** Return the next and previous element sibling nodes, respectively.
   ```javascript
   let nextElementSibling = node.nextElementSibling;
   let previousElementSibling = node.previousElementSibling;
   ```

### Compatibility Workaround

For older browsers that do not support `nextElementSibling` and `previousElementSibling`:

```javascript
function getNextElementSibling(element) {
    let sibling = element.nextSibling;
    while (sibling && sibling.nodeType !== 1) {
        sibling = sibling.nextSibling;
    }
    return sibling;
}
```

## Creating Nodes

Creating nodes and appending them to the DOM is a fundamental operation.

**Example**

```html
<ul>
  <li>123</li>
</ul>
```

```javascript
let li = document.createElement('li'); // Create a new list item
li.textContent = 'New Item'; // Set text content
let ul = document.querySelector('ul');
ul.appendChild(li); // Append the new item to the list
```

### Result

```html
<ul>
  <li>123</li>
  <li>New Item</li>
</ul>
```

### Inserting Before a Node

```javascript
let li = document.createElement('li');
li.textContent = 'First Item';
let ul = document.querySelector('ul');
ul.insertBefore(li, ul.children[0]); // Insert before the first child
```

### Result

```html
<ul>
  <li>First Item</li>
  <li>123</li>
</ul>
```

## Removing Nodes

Removing nodes from the DOM is straightforward.

**Example**

```html
<ul>
  <li>a</li>
  <li>b</li>
  <li>c</li>
</ul>
<button>Remove First Item</button>
```

```javascript
let ul = document.querySelector('ul');
let button = document.querySelector('button');
button.onclick = () => {
  if (ul.children.length > 0) {
    ul.removeChild(ul.children[0]); // Remove the first child
  } else {
    button.disabled = true; // Disable button if no more children
  }
};
```

## Cloning Nodes

Cloning nodes can be done using `cloneNode()`. This can be a shallow or deep clone.

**Example**

```html
<ul>
  <li>a</li>
  <li>b</li>
  <li>c</li>
</ul>
<button>Clone First Item</button>
```

```javascript
let ul = document.querySelector('ul');
let button = document.querySelector('button');
button.onclick = () => {
  let firstItem = ul.children[0].cloneNode(true); // Deep clone
  ul.appendChild(firstItem); // Append the cloned item
};
```

## Dynamic Table

### HTML Structure

```html
<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Subject</th>
      <th>Grade</th>
    </tr>
  </thead>
  <tbody></tbody>
</table>
```

- **`<table>`**: Represents the table element.
- **`<thead>`**: Contains the header row of the table.
- **`<tr>`**: Table row.
- **`<th>`**: Table header cell, providing column names.
- **`<tbody>`**: Contains the body rows of the table.

### JavaScript to Populate Table

```javascript
const mockData = [
  { name: "Ron", subject: "Math", grade: "100" },
  { name: "Jack", subject: "Calculus", grade: "70" },
  { name: "Mar", subject: "Business", grade: "90" }
];

const tbody = document.querySelector("tbody");

mockData.forEach(data => {
  const tr = document.createElement("tr");
  tbody.appendChild(tr);

  for (const key of Object.keys(data)) {
    const td = document.createElement("td");
    td.textContent = data[key];
    tr.appendChild(td);
  }
});
```

### Explanation

- **`forEach` Loop**: Iterates over `mockData` array.
- **`createElement`**: Creates new elements (`<tr>` and `<td>`).
- **`appendChild`**: Appends created elements to the parent element.
- **`textContent`**: Sets the text content of a `<td>` element.

### Object Traversal

```javascript
for (const key of Object.keys(obj)) {
  // key is an own enumerable string property name
  // obj[key] is that property's value
}
```

## Event Operations

### Registering Events

**Event listener API**: `addEventListener`

```javascript
eventTarget.addEventListener(type, listener, options);
```

- **Type**: Event type string, e.g., `click`, `mouseover`.
- **Listener**: Function to call when the event occurs.
- **Options**: Optional; a boolean selects capture mode (default `false`), or an options object can set `capture`, `once`, and `passive`.

**Example**

```javascript
const btn = document.querySelector("button");

// Traditional way
btn.onclick = () => {
  // Function to call on click
};

// Recommended way
btn.addEventListener('click', () => {
  // Function to call on click
});
```

### Differences Between Traditional Way and `addEventListener`

- **Traditional Way**: Can only assign one function to an event.
- **Event Listener Approach**: Allows multiple listeners for the same event.

### Example with Multiple Listeners

```javascript
btn.addEventListener('click', () => { alert(11); });
btn.addEventListener('click', () => { alert(12); });
btn.addEventListener('click', () => { alert(13); });
```

- Alerts `11`, `12`, and `13` in sequence.

### Removing Event Listener

**Method**: `removeEventListener`

```javascript
eventTarget.removeEventListener(type, listener);
```

### Example for Single-use Button

```javascript
function handleClick() {
  alert(11);
  btn.removeEventListener("click", handleClick);
}

btn.addEventListener("click", handleClick); // Note: function name without brackets
```

## DOM Event Flow

### Event Stream

- **Capturing Phase**: The event traverses the event path toward the target from the window/document side.
- **Target Phase**: Listeners registered on the target run.
- **Bubbling Phase**: Events whose `bubbles` flag is true travel back up the path.

### Example with Capturing and Bubbling

```javascript
const parent = document.querySelector(".parent");
const child = document.querySelector(".child");

parent.addEventListener("click", () => { alert("Parent Clicked"); }, true); // Capturing
child.addEventListener("click", () => { alert("Child Clicked"); }, false); // Bubbling
```

- **Capturing Phase**: Parent's event triggers first.
- **Bubbling Phase**: Child's event triggers first.

### Using `addEventListener` for Different Phases

```javascript
// Capturing phase
eventTarget.addEventListener(type, listener, true);

// Bubbling phase (default)
eventTarget.addEventListener(type, listener, false);
```

**See also / 另见：** [DOM Manipulation and Events / DOM 操作与事件](../../../../frontend/browser-apis/dom-manipulation-and-events.md) for event propagation and deep-copy distinctions.
