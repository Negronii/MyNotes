# JavaScript DOM and Browser APIs / JavaScript DOM 与浏览器 API

**Core idea / 核心概念：** The DOM is a host-provided object model for a document; browser APIs such as events, timers, and `window` are also host APIs, not part of the ECMAScript language itself. / DOM 是宿主提供的文档对象模型；事件、计时器与 `window` 等浏览器 API 同样属于宿主接口，并非 ECMAScript 语言本身。 For current guides, see [DOM manipulation and events](../../../../frontend/browser-apis/dom-manipulation-and-events.md), [browser basics](../../../../frontend/browser/browser-basics.md), and the [event loop](../../../../frontend/runtime/event-loop.md).

The Document Object Model (DOM) represents a document as nodes and objects that JavaScript can inspect and modify.

## Accessing Elements

### getElementById

Retrieves the element with the given ID, or `null` if there is no match. HTML documents should use IDs uniquely.

**Syntax:**
```javascript
document.getElementById('<element id>')
```

**Example:**
```javascript
const timeElement = document.getElementById("time");
console.dir(timeElement);
```
- `document.getElementById("time")` retrieves the element with the ID `time`.
- `console.dir(timeElement)` logs the element object to the console.

### getElementsByTagName

Retrieves all elements with the specified tag name. It returns a live `HTMLCollection` (an array-like collection of elements).

**Syntax:**
```javascript
document.getElementsByTagName('<tag name>')
```

**Example:**
```javascript
const listItems = document.getElementsByTagName("li");

for (let i = 0; i < listItems.length; i++) {
  console.log(listItems[i]);
}
```

- `document.getElementsByTagName("li")` retrieves all `<li>` elements.
- The for loop iterates through the HTMLCollection and logs each `<li>` element.

**Accessing Child Elements:**
```javascript
const ols = document.getElementsByTagName('ol');
const lis = ols[0].getElementsByTagName('li');
```
- `ols[0]` accesses the first `<ol>` element.
- `ols[0].getElementsByTagName('li')` retrieves all `<li>` elements within the first `<ol>`.

## Modern Selection Methods / 现代选择器方法

### getElementsByClassName

Retrieves all elements with the specified class name. It returns a live `HTMLCollection`.

**Syntax:**
```javascript
document.getElementsByClassName('<class name>')
```

**Example:**
```javascript
const boxes = document.getElementsByClassName("box");
```
- `document.getElementsByClassName("box")` retrieves all elements with the class `box`.

### querySelector

Retrieves the first element that matches the specified CSS selector, or `null` if there is no match.

**Syntax:**
```javascript
document.querySelector('<selector>')
```

**Examples:**
```javascript
const firstBox = document.querySelector(".box");
const navElement = document.querySelector("#nav");
const firstListItem = document.querySelector("li");
```
- `document.querySelector(".box")` retrieves the first element with the class `box`.
- `document.querySelector("#nav")` retrieves the element with the ID `nav`.
- `document.querySelector("li")` retrieves the first `<li>` element.

### querySelectorAll

Retrieves all elements that match the specified CSS selector. This method returns a static `NodeList`; later document changes do not alter this list.

**Syntax:**
```javascript
document.querySelectorAll('<selector>')
```

**Example:**
```javascript
const allBoxes = document.querySelectorAll(".box");

allBoxes.forEach(box => {
  console.log(box);
});
```
- `document.querySelectorAll(".box")` retrieves all elements with the class `box`.
- `NodeList.forEach` is used to iterate over the NodeList and log each element.

## Document Properties

### document.body

Retrieves the `<body>` element.

**Example:**
```javascript
const bodyElement = document.body;
console.log(bodyElement);
```
- `document.body` gets the `<body>` element object.

### document.documentElement

Retrieves the `<html>` element.

**Example:**
```javascript
const htmlElement = document.documentElement;
console.log(htmlElement);
```
- `document.documentElement` gets the `<html>` element object.

## Best Practices

1. **Use `querySelector` and `querySelectorAll`:**
   - These methods are more flexible and support complex CSS selectors.
   - Example:
     ```javascript
     const mainHeader = document.querySelector('header.main-header');
     const activeItems = document.querySelectorAll('.menu-item.active');
     ```

2. **Cache DOM Queries:**
   - Repeated DOM queries can be expensive. Store references to elements that are accessed multiple times.
   - Example:
     ```javascript
     const menuItems = document.querySelectorAll('.menu-item');
     menuItems.forEach(item => {
       // Perform operations on each item
     });
     ```

3. **Use Event Delegation:**
   - Instead of adding event listeners to multiple elements, add a single event listener to a common parent.
   - Example:
     ```javascript
     document.querySelector('.menu').addEventListener('click', (event) => {
       if (event.target.matches('.menu-item')) {
         // Handle menu item click
       }
     });
     ```

# Events Introduction

Events are actions or occurrences that happen in the browser and can be detected and handled by JavaScript. They consist of three main parts: event source, event type, and event handler.

## Event Source

The event source is the object that triggers the event. For example, if a button is clicked, the button element is the event source.

### Example

```javascript
var btn = document.getElementById("btn");
```

Here, `btn` is the event source, which is a reference to the button element with the ID "btn".

## Event Type

Event type defines how the event is triggered and what kind of event it is. Here are some common HTML events:

- `click`: Dispatched when an element is clicked; `onclick` is a handler property/attribute.
- `mouseover` / `mouseout`: Mouse pointer enters or leaves an element (including descendant transitions).
- `keydown` / `keyup`: A key is pressed or released.
- `submit`: A form is submitted.
- `load`: A load-delaying resource or target has loaded.
- `resize`: A resizable object, commonly the window, changes size.

**Example**

```javascript
btn.onclick = function () {
  // do something when the button is clicked
};
```

In this example, `onclick` is the event-handler property; the event type is `click`.

## Event Handler

An event handler is a function that is executed when the event occurs. It defines the action to be performed in response to the event.

**Example**

```javascript
btn.onclick = function () {
  alert("Button clicked!");
};
```

Here, the event handler is a function that displays an alert message when the button is clicked.

## Modern Event Handling with addEventListener

Using `addEventListener` is the recommended way to handle events as it allows multiple event handlers for the same event and can be used to remove event listeners.

**Example**

```javascript
btn.addEventListener('click', function() {
  alert("Button clicked!");
});
```

You can also remove an event listener using `removeEventListener`.

**Example**

```javascript
function handleClick() {
  alert("Button clicked!");
}

btn.addEventListener('click', handleClick);

// To remove the event listener
btn.removeEventListener('click', handleClick);
```

# Modify Element Attributes

Modifying element attributes allows you to change the properties of HTML elements dynamically.

## `innerText` & `innerHTML`

### `innerText`

`element.innerText` reads or sets rendered text, without returning HTML markup. For text independent of rendering, use `textContent`.

**Example**

```javascript
element.innerText = "2024-06-04";
```

This sets the inner text of the element to '2024-06-04'.

### `innerHTML`

`element.innerHTML` reads or parses/sets the element's HTML markup. Do not assign untrusted strings to it; use `textContent` when inserting plain text.

**Example**

```javascript
element.innerHTML = "<strong>Today is:</strong> 2024-06-04";
```

This sets the inner HTML of the element to '<strong>Today is:</strong> 2024-06-04'.

## Input Attributes

Input attributes allow you to control the behavior and appearance of input elements.

**Example**

```html
<button>Click me</button>
<input type="text" value="Please enter">
```

```javascript
var btn = document.querySelector("button");
var input = document.querySelector("input");

// Register the onclick event
btn.onclick = function () {
  // Modify the input value
  input.value = "Entered";

  // Disable the button, making it unclickable
  btn.disabled = true;

  // In this regular event-handler function, `this` is the currentTarget (the button).
  this.disabled = true;
};

input.onfocus = function () {
  // Event handler when the user clicks on the input
  console.log("Input focused");
};

input.onblur = function () {
  // Event handler when the user clicks on the input and then clicks somewhere else
  console.log("Input blurred");
};

// Get the number of characters in the input value
console.log(input.value.length);
```

## Best Practices

1. **Use `addEventListener`**: Prefer using `addEventListener` for event handling to keep your code flexible and maintainable.
2. **Keep Functions Separate**: Define event handler functions separately to improve readability and reusability.
3. **Avoid Inline Event Handlers**: Avoid using inline event handlers in HTML. Instead, use JavaScript to attach event listeners.
4. **Accessibility**: Ensure interactive elements are accessible by using appropriate ARIA roles and properties.

## Image Attributes

Images in HTML are managed using the `<img>` tag. Here are some key attributes for handling images effectively:

1. **src**:
   - Specifies the source URL of an image.
   ```html
   <img src="images/example.png" alt="Example Image">
   ```
   - Example with JavaScript:
     ```javascript
     var img = document.querySelector("img");
     img.src = "images/new-image.png";
     ```

2. **alt**:
   - Provides alternative text for an image if it cannot be displayed.
   - Supplies alternative text for assistive technology and for cases where the image is unavailable; search ranking is not its definition.
   ```html
   <img src="images/example.png" alt="A descriptive text about the image">
   ```

3. **title**:
   - Offers additional information about an element, typically shown as a tooltip.
   ```html
   <img src="images/example.png" alt="Example Image" title="This is an example image">
   ```

4. **id**:
   - Specifies a unique identifier for an element.
   ```html
   <img id="uniqueImage" src="images/example.png" alt="Example Image">
   ```

### Best Practices:
- Provide an appropriate `alt` value: descriptive text for informative images, or `alt=""` for decorative images.
- Use meaningful `alt` text that describes the content of the image.
- Use `title` for supplementary information but not as a replacement for `alt`.

## Inline Style Modification

Modifying the inline styles of elements using JavaScript can be powerful for dynamic styling:

1. **Accessing and Modifying Styles:**
   ```javascript
   var div = document.querySelector("div");
   
   // Modify background color
   div.style.backgroundColor = "pink";
   
   // Hide the div
   div.style.display = "none";
   ```
   - Style properties use camelCase in JavaScript (e.g., `backgroundColor` instead of `background-color`).

2. **Best Practices:**
   - Minimize inline style modifications to maintain separation of concerns.
   - Prefer CSS classes for consistent styling.

## Class Name Style Modification

Class names are a more flexible and maintainable way to apply styles:

1. **Changing Class Names:**
   ```javascript
   var div = document.querySelector("div");
   div.className = "box";
   ```

2. **Adding Multiple Classes:**
   ```javascript
   div.className = "first second";
   ```

3. **Best Practices:**
   - Use `classList` for more control over class manipulations:
     ```javascript
     div.classList.add("newClass");
     div.classList.remove("oldClass");
     div.classList.toggle("toggleClass");
     ```

## Custom Attributes

HTML data attributes (`data-*`) associate string data with elements and can be read through `dataset` or the attribute APIs.

1. **Custom data attributes:**
   ```html
   <div id="test" data-index="1"></div>
   ```

2. **Accessing Attributes:**
   ```javascript
   var div = document.querySelector("#test");
   console.log(div.id); // 'test'
   console.log(div.getAttribute("data-index")); // '1'
   ```

3. **Setting Attributes:**
   ```javascript
   div.setAttribute("class", "box");
   div.setAttribute("data-index", "1");
   ```

4. **Removing Attributes:**
   ```javascript
   div.removeAttribute("data-index");
   ```

5. **Developer-defined Attributes:**
   - An HTML custom data attribute uses the `data-` prefix.
   ```html
   <div id="test" data-index="1" data-test-attr="test"></div>
   ```

6. **Using `dataset`:**
   ```javascript
   var div = document.querySelector("#test");
   console.log(div.dataset.index); // '1'
   console.log(div.dataset.testAttr); // 'test'
   ```

7. **Best Practices:**
   - Use `data-` attributes for storing custom data.
   - Prefer `getAttribute` and `setAttribute` for handling non-standard attributes.

# Node Operations in Modern Front-End Development

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

# HTML Events and Event Handling

## Event Object

### Understanding the Event Object

In JavaScript, when an event occurs (e.g., a click or a keydown), an event object is created containing information about that event. Its properties and methods can be used while handling it.

### Example of Using the Event Object

```javascript
btn.onclick = function (event) {
    // event contains all information about the event
};
```

The event object (`event`) can be accessed within the event handler function. It provides information such as mouse coordinates for a click event or the key pressed for a keyboard event.

### Event Object Properties

- **`e.target` vs. `this`**:
  - `e.target` refers to the element that triggered the event.
  - `e.currentTarget` is the object whose listener is running. In a regular-function event listener, `this` has that value; an arrow function keeps lexical `this`.

  ```javascript
  btn.onclick = function (e) {
      console.log(e.target); // Element that was clicked
      console.log(e.currentTarget); // Object whose listener is running
      console.log(this);            // Same value for a regular-function listener
  };
  ```

### Preventing Default Actions

- **`e.preventDefault()`**: Prevents the default action associated with the event.
  ```javascript
  document.querySelector('a').addEventListener('click', function (e) {
      e.preventDefault(); // Prevents navigation
  });
  ```

### Stopping Event Propagation

- **`e.stopPropagation()`**: Prevents the event from bubbling up the DOM tree.
  ```javascript
  document.querySelector('button').addEventListener('click', function (e) {
      e.stopPropagation(); // Prevents parent elements from receiving the event
  });
  ```

## Event Delegation

Event delegation allows you to attach a single event listener to a parent element to manage all child elements' events. This is more efficient than attaching event listeners to each child element individually.

### Example of Event Delegation

```html
<ul id="list">
    <li>Item 1</li>
    <li>Item 2</li>
    <li>Item 3</li>
</ul>
```

```javascript
document.getElementById('list').addEventListener('click', function (e) {
    const target = e.target && typeof e.target.closest === 'function'
      ? e.target.closest('li')
      : null;
    if (target && e.currentTarget.contains(target)) {
        target.style.backgroundColor = 'pink'; // Change background of clicked <li>
    }
});
```

By attaching a single event listener to the `<ul>`, you can handle clicks on all `<li>` elements.

### Benefits of Event Delegation

- **Efficiency**: Reduces the number of separately registered listeners; whether that improves performance depends on the interaction and workload.
- **Dynamic Content**: Automatically handles dynamically added child elements.

## Mouse Events

### Disabling Right-Click Menu

- **`contextmenu` Event**: `preventDefault()` suppresses the default menu; reserve it for interactions that require it, because it removes a browser affordance and is not a security control.
  ```javascript
  document.addEventListener('contextmenu', function (e) {
      e.preventDefault(); // Disables right-click menu
  });
  ```

### Disabling Text Selection

- **`selectstart` Event**: `preventDefault()` suppresses selection; use it only for a specific interaction that requires it, not as general page behavior.
  ```javascript
  document.addEventListener('selectstart', function (e) {
      e.preventDefault(); // Disables text selection
  });
  ```

## Mouse Event Attributes

- **`e.clientX`**: X coordinate relative to the viewable area of the browser.
- **`e.clientY`**: Y coordinate relative to the viewable area of the browser.
- **`e.pageX`**: X coordinate relative to the document.
- **`e.pageY`**: Y coordinate relative to the document.
- **`e.screenX`**: X coordinate relative to the screen.
- **`e.screenY`**: Y coordinate relative to the screen.

### Example: Moving an Element with the Mouse

```html
<style>
  .pic {
      position: absolute;
      top: 2px;
  }
</style>
<body>
  <img src="image.jpg" alt="Movable Image" class="pic">
</body>
```

```javascript
var pic = document.querySelector('.pic');
document.addEventListener('mousemove', function (e) {
    pic.style.left = e.pageX + 'px';
    pic.style.top = e.pageY + 'px';
});
```

## Keyboard Events

### Common Keyboard Events

- **`keyup`**: Triggered when a key is released.
- **`keydown`**: Triggered when a key is pressed.
- **`keypress`**: Legacy/deprecated; use `keydown` or `keyup` for keyboard interaction.

### Example: Handling Keyboard Events

```javascript
document.addEventListener('keyup', function (e) {
    console.log(e.key);  // Meaning of the key under the active keyboard layout
    console.log(e.code); // Physical key code/position
});
```

### Best Practices

- Use `keyup` for actions that should happen on release; a held key can produce repeated `keydown` events.
- `keyCode` and `which` are legacy/inconsistent; use `key` or `code` according to the question being answered.
- When using `addEventListener`, omit the "on" prefix (e.g., use `'keyup'`, not `'onkeyup'`).

# Browser Object Model (BOM)

“Browser Object Model” (BOM) is a common umbrella term for browser-facing objects such as `window`, `location`, `history`, and `navigator`; it is not one separate, uniformly defined object hierarchy.

## BOM Components

### 1. `window` Object

The `window` object represents a browser window and exposes browser APIs and properties for interacting with it.

- **Classic-script global bindings:**
  In a classic browser script, top-level `var` and function declarations can become `window` properties; top-level `let` and `const` do not. ES modules have their own top-level scope.

  ```javascript
  var x = 5;
  console.log(window.x); // Outputs: 5
  ```

- **Common Methods:**
  - `alert(message)`: Displays an alert box with a message.
  - `confirm(message)`: Displays a confirmation dialog box with OK and Cancel buttons.
  - `prompt(message, default)`: Displays a dialog box that prompts the user for input.

  ```javascript
  alert('Hello, world!');
  var userResponse = confirm('Do you agree?');
  var userInput = prompt('Please enter your name:', 'Guest');
  ```

- **Special Properties:**
  `window.name` stores the browsing context's name; a local variable named `name` is independent of it.

  ```javascript
  window.name = 'myWindow';
  console.log(window.name); // Outputs: myWindow
  ```

### 2. `document` Object

The `document` object represents the current HTML document loaded in the browser. It provides methods and properties for accessing and manipulating the content of the document.

- **Example:**
  ```javascript
  console.log(document.title); // Outputs the title of the current document
  ```

### 3. `location` Object

The `location` object contains information about the current URL and provides methods for navigating to different URLs.

- **Common Properties:**
  - `href`: The entire URL.
  - `hostname`: The domain name of the web host.
  - `pathname`: The path and filename of the current page.
  - `search`: The query string of the URL.

- **Example:**
  ```javascript
  console.log(location.href); // Outputs the full URL
  location.href = 'https://www.example.com'; // Redirects to a new URL
  ```

### 4. `history` Object

The `history` object provides methods to interact with the browser's session history.

- **Common Methods:**
  - `back()`: Loads the previous URL in the history list.
  - `forward()`: Loads the next URL in the history list.
  - `go(n)`: Loads a specific URL from the history list.

  ```javascript
  history.back(); // Goes back to the previous page
  history.forward(); // Goes forward to the next page
  history.go(-2); // Goes back two pages
  ```

### 5. `navigator` Object

The `navigator` object contains information about the browser.

- **Common Properties:**
  - `userAgent`: A user-agent string; do not rely on parsing it to identify a browser or device.
  - `platform`: Platform information, which can be generic or privacy-reduced.

  ```javascript
  console.log(navigator.userAgent); // Outputs the user agent string
  console.log(navigator.platform); // Outputs the platform (e.g., Win32)
  ```

### 6. `screen` Object

The `screen` object provides information about the user's screen.

- **Common Properties:**
  - `width`: The width of the screen in pixels.
  - `height`: The height of the screen in pixels.

  ```javascript
  console.log(screen.width); // Outputs the screen width
  console.log(screen.height); // Outputs the screen height
  ```

## Events in BOM

### 1. `onload` Event

The window `load` event fires after resources that delay the event have loaded; some resources, such as lazy-loaded images, need not delay it.

- **Using `onload` Property:**
  ```javascript
  window.onload = function() {
    console.log('Load-delaying resources have finished loading');
  };
  ```

- **Using `addEventListener`:**
  ```javascript
  window.addEventListener('load', function() {
    console.log('Load-delaying resources have finished loading');
  });
  ```

### 2. `DOMContentLoaded` Event

`DOMContentLoaded` fires after parsing and deferred/module script execution. It does not wait for images or subframes; stylesheets can delay scripts that in turn delay this event.

- **Example:**
  ```javascript
  document.addEventListener('DOMContentLoaded', function() {
    console.log('Document parsed and deferred/module scripts executed');
  });
  ```

### 3. `resize` Event

The `resize` event is triggered when the size of the browser window changes.

- **Using `onresize` Property:**
  ```javascript
  window.onresize = function() {
    console.log('Window resized');
  };
  ```

- **Using `addEventListener`:**
  ```javascript
  window.addEventListener('resize', function() {
    console.log('Window resized');
  });
  ```

- **Example to Get Window Size:**
  ```javascript
  window.addEventListener('resize', function() {
    console.log('Width: ' + window.innerWidth + ', Height: ' + window.innerHeight);
  });
  ```

### 4. `scroll` Event

The `scroll` event fires when the scroll position of the document or a scrollable element changes, whether through user input or script.

- **Example:**
  ```javascript
  window.addEventListener('scroll', function() {
    console.log('Page scrolled');
  });
  ```

# JavaScript Timer Functions

## Timer Functions

### `setTimeout`

The browser-hosted `setTimeout` schedules a callback after a delay in milliseconds. The delay is a minimum scheduling threshold, not an exact execution time. The `window` object can be omitted in browser code.

**Syntax:**
```javascript
setTimeout(callback, delay);
```

**Example:**
```javascript
setTimeout(function () {
    console.log("Executed after 2 seconds");
}, 2000);
```

**Storing the timer handle:**
Store the host-provided handle returned by `setTimeout` if the pending callback may need to be cancelled.

**Example:**
```javascript
var timer = setTimeout(function () {
    console.log("This will not be executed if clearTimeout is called");
}, 2000);
```

### `clearTimeout`

`clearTimeout` cancels a pending timeout using its host-provided handle.

**Syntax:**
```javascript
clearTimeout(handle);
```

**Example:**
```javascript
clearTimeout(timer);
```

### `setInterval`

The browser-hosted `setInterval` repeatedly schedules a callback with a delay in milliseconds. Calls may be delayed, so this is not an exact clock; pass a callback as the first argument.

**Syntax:**
```javascript
setInterval(callback, delay);
```

**Example:**
```javascript
setInterval(function () {
    console.log("Executed every 2 seconds");
}, 2000);
```

**Storing the interval handle:**
Store the host-provided handle returned by `setInterval` so the interval can be cancelled when it is no longer needed.

**Example:**
```javascript
var interval = setInterval(function () {
    console.log("This will not be executed if clearInterval is called");
}, 2000);
```

### `clearInterval`

`clearInterval` cancels a pending interval using its host-provided handle.

**Syntax:**
```javascript
clearInterval(handle);
```

**Example:**
```javascript
clearInterval(interval);
```

### Best Practices

Timer APIs are host-provided, not ECMAScript language features. Browsers return numeric IDs; Node returns timer objects. Do not assume the delay is exact.

1. **Cancel pending work when needed:**
   Clear a timeout or interval handle when its callback is no longer wanted.

2. **Capture lexical `this`:**
   Use an arrow when a callback should use the enclosing `this` value; timer callback `this` otherwise depends on the host.

   **Example:**
   ```javascript
   class Example {
       constructor() {
           this.name = "Example";
       }

       startTimer() {
           setTimeout(() => {
               console.log(this.name); // 'this' refers to the Example instance
           }, 1000);
       }
   }

   const example = new Example();
   example.startTimer(); // Logs "Example" after 1 second
   ```

# `this` Keyword Usage / `this` 的绑定

`this` is a call-time binding for ordinary functions (not lexical/dynamic variable scope). Its value depends on the invocation form; arrow functions capture `this` lexically.

### Global Usage

At the top level of a classic browser script, `this` is `window`; at the top level of an ES module it is `undefined`. Other hosts have their own top-level rules.

**Example:**
```javascript
console.log(this); // `window` in a classic browser script; `undefined` in a module
```

### Timer Function Usage

Timer callback `this` is host-specific and is not a portable way to access the enclosing value. Use an arrow to capture lexical `this`, or `bind` the function to the desired receiver.

**Example with Arrow Function:**
```javascript
setTimeout(() => {
    console.log(this); // 'this' refers to the enclosing lexical context
}, 2000);
```

**Example with `bind`:**
```javascript
setTimeout(function () {
    console.log(this);
}.bind(this), 2000);
```

### Function Invocation Usage

When an ordinary function is called as `receiver.method()`, `this` is the call's receiver (`receiver`), even if the function was copied from another object.

**Example:**
```javascript
var obj = {
    name: "Object",
    greet: function () {
    console.log(this.name); // The call receiver is `obj`
    }
};
obj.greet(); // Invoking the 'greet' method on object 'obj'
```

**Event Listener Example:**
```javascript
var btn = document.getElementById("myButton");
btn.onclick = function () {
    console.log(this); // The currentTarget for this regular handler
};
```

### Constructor Method Usage

In a constructor function, `this` refers to the instance of the object being created.

**Example:**
```javascript
function Person(name) {
    this.name = name;
}

var person = new Person("Alice");
console.log(person.name); // Outputs "Alice"
```

### Best Practices

1. **Use Arrow Functions for Callbacks:**
   Arrow functions do not have their own `this` context; they inherit it from the parent scope.

2. **Bind Methods in Class Constructors:**
   When using ES6 classes, bind methods in the constructor to ensure `this` refers to the class instance.

   **Example:**
   ```javascript
   class Counter {
       constructor() {
           this.count = 0;
           this.increment = this.increment.bind(this);
       }

       increment() {
           this.count += 1;
           console.log(this.count);
       }
   }

   const counter = new Counter();
   document.getElementById("incrementBtn").addEventListener("click", counter.increment);
   ```

# Asynchronous and Synchronous Programming

## Synchronous Tasks

Synchronous tasks are operations that are executed one after another, where each task must complete before the next one begins. This is like following a step-by-step recipe where you cannot start the next step until the current one is finished.

### Example of Synchronous Tasks:

1. Boil water
2. Cut vegetables
3. Cook

In JavaScript, synchronous code is executed in the order it is written. If a task takes a long time, it will block the following tasks from executing until it is finished.

### Code Example:

```javascript
console.log('Boil water');
console.log('Cut vegetables');
console.log('Cook');
```

Output:
```
Boil water
Cut vegetables
Cook
```

In this example, each task is executed in sequence.

## Asynchronous Tasks

Asynchronous APIs let JavaScript continue while an operation is pending, then arrange a later continuation. This does not mean JavaScript code on one agent runs simultaneously; host work such as I/O may proceed independently.

### Implementing Asynchronous Tasks in JavaScript

Asynchronous control flow is commonly expressed with callbacks, Promises, or `async/await`. These patterns let code respond while host-managed work is pending. A Promise represents an outcome; it does not itself make an operation concurrent or cancel it.

### Callback Functions

A callback function is a function passed into another function as an argument, which is then executed inside the outer function.

**Example**:

```javascript
function boilWater(callback) {
    setTimeout(() => {
        console.log('Boil water');
        callback();
    }, 1000);
}

function cutVegetables() {
    console.log('Cut vegetables');
}

boilWater(cutVegetables);
```

In this example, browser `setTimeout` simulates a delay. The callback runs in a later task; no water-boiling work happens concurrently in JavaScript.

### Promises

Promises provide a cleaner, more powerful way to handle asynchronous operations. A Promise represents a value that may be available now, in the future, or never.

**Example**

```javascript
function boilWater() {
    return new Promise((resolve) => {
        setTimeout(() => {
            console.log('Boil water');
            resolve();
        }, 1000);
    });
}

function cutVegetables() {
    console.log('Cut vegetables');
}

boilWater().then(cutVegetables);
```

### Async/Await

`async/await` is syntactic sugar built on top of Promises, making asynchronous code look and behave more like synchronous code. 

**Example**:

```javascript
function boilWater() {
    return new Promise((resolve) => {
        setTimeout(() => {
            console.log('Boil water');
            resolve();
        }, 1000);
    });
}

async function prepareMeal() {
    await boilWater();
    console.log('Cut vegetables');
}

prepareMeal();
```

### JavaScript Event Loop

In browsers, the event loop coordinates host tasks, microtasks, and rendering opportunities. Host APIs determine when timers, network events, and other work become runnable; ECMAScript defines Promise jobs but not browser timer queues. See the [event-loop guide](../../../../frontend/runtime/event-loop.md).

### Event Loop Process:

1. A selected task (such as a script or timer callback) runs to completion.
2. The browser performs a microtask checkpoint, running queued Promise reactions until the microtask queue is empty.
3. When appropriate, the browser may update rendering, then select another runnable task from its host-managed task queues.

### Pseudocode Example (browser model):

```javascript
while (eventLoopIsRunning) {
    runOneRunnableTaskToCompletion();
    runMicrotasksUntilEmpty();

    if (renderingOpportunity()) {
        updateRendering();
    }
}
```

# URL and Location Object

## URL Structure

For a hierarchical URL, a common shape is shown below; not every scheme has an authority (for example, `mailto:` URLs).

```
scheme:[//authority]path[?query][#fragment]
```

### Example URL

```
http://www.itcast.cn/index.html?name=andy&age=18#link
```

### Components Explained

1. **Scheme**: Identifies the URL scheme, such as `http`, `https`, or `mailto`.
2. **Authority**: Optional; for HTTP(S) URLs it can include a host and port.
3. **Port**: Optional; HTTP and HTTPS use their default ports (80 and 443), which browsers commonly omit when serializing the URL.
4. **Path**: The path component; its interpretation depends on the scheme.
5. **Query**: Optional query component beginning with `?`; individual parameter conventions depend on the application.
6. **Fragment**: Optional component beginning with `#`, often used to identify a document location.

## Location Object

The `location` object provides various properties to access and manipulate the URL components.

### Properties

- `location.href`: Gets or sets the entire URL.
- `location.protocol`: Returns the protocol (e.g., `http:` or `https:`).
- `location.host`: Returns the hostname and a non-default port when present (e.g., `www.itcast.cn:8080`).
- `location.hostname`: Returns the hostname (e.g., `www.itcast.cn`).
- `location.port`: Returns the non-default port, or an empty string when the URL has no explicit non-default port.
- `location.pathname`: Returns the path (e.g., `/index.html`).
- `location.search`: Returns the query string (e.g., `?name=andy&age=18`).
- `location.hash`: Returns the fragment (e.g., `#link`).

### Methods

- `location.assign(url)`: Loads a new document.
- `location.replace(url)`: Replaces the current document with a new one (does not create a history entry).
- `location.reload()`: Reloads the current document.

### Examples

#### Redirecting to Another Page

```javascript
var time = 5;
var div = document.querySelector("div");
setInterval(function () {
    if (time === 0) {
        location.href = "http://www.itcast.cn";
    } else {
        div.innerHTML = "You will be redirected to itcast.cn in " + time + " seconds";
        time--;
    }
}, 1000);
```

#### Extracting Query Parameters

```javascript
var searchParams = new URLSearchParams(location.search);
var name = searchParams.get('name'); // 'andy'
var age = searchParams.get('age'); // '18'
```

## Navigator Object

The `navigator` object provides information about the user's browser.

### Common Properties

- `navigator.userAgent`: Returns a user-agent string; parsing it for browser/device detection is brittle.
- `navigator.language`: Returns the preferred language of the user.
- `navigator.platform`: Returns the platform on which the browser is running (e.g., `Win32`, `MacIntel`).

### Example: A brittle user-agent heuristic

```javascript
var isMobile = /Mobi|Android/i.test(navigator.userAgent);
if (isMobile) {
    console.log("You are using a mobile browser.");
} else {
    console.log("You are using a desktop browser.");
}
```

User-agent matching is not dependable device detection. Prefer feature detection for the capability the page needs.

## History Object

The `history` object provides methods to navigate through the browser history.

### Methods

- `history.back()`: Equivalent to clicking the browser's back button.
- `history.forward()`: Equivalent to clicking the browser's forward button.
- `history.go(n)`: Navigates to a specific point in the browser history. A positive number moves forward, and a negative number moves backward.

### Example: Navigating the Browser History

```javascript
// Go back one page
history.back();

// Go forward one page
history.forward();

// Go back two pages
history.go(-2);

// Go forward two pages
history.go(2);
```

# Web Special Effects

## Offset Series

The offset series attributes provide information about the element's position, size, and relationship to its offset parent.

### Commonly Used Properties

- `element.offsetParent`: Returns the offset parent used for offset calculations; it can be `null`.
- `element.offsetTop`: Returns the layout offset from the top of its offset parent (or the initial containing block when there is no offset parent).
- `element.offsetLeft`: Returns the layout offset from the left of its offset parent (or the initial containing block when there is no offset parent).
- `element.offsetWidth`: Returns the element's width, including padding and borders.
- `element.offsetHeight`: Returns the element's height, including padding and borders.

### Difference Between Style and Offset

#### Offset Properties

- Report layout metrics, not the CSS value that produced them.
- Values are numeric CSS-pixel layout measurements.
- `offsetWidth` includes padding, border, and content.
- Offset properties are read-only.

#### Style Properties

- `element.style` reads and writes inline declarations; use `getComputedStyle(element)` for resolved style values.
- CSS length values such as `style.width` are strings and can include units.
- Whether the declared `width` includes padding and border depends on `box-sizing`; `offsetWidth` reports the rendered border-box width.
- Style properties are readable and writable.

### Example: Getting the Coordinates Inside a Box

```javascript
element.addEventListener('mousemove', function (e) {
    const rect = this.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    console.log('X coordinate from the border-box left: ' + x);
    console.log('Y coordinate from the border-box top: ' + y);
});
```

## Mouse drag

Mouse drag can be detected by combining `mousedown` and `mousemove` events.

Example:

```javascript
function doSomething(){
}

const title = document.querySelector(".title");
if (title) {
    title.addEventListener("mousedown", function () {
        document.addEventListener("mousemove", doSomething);
        // Listen on document so releasing outside the title also ends the drag.
        document.addEventListener("mouseup", function stopDragging() {
            document.removeEventListener("mousemove", doSomething);
        }, { once: true });
    });
}
```

## Standards and references / 标准与参考

- [WHATWG DOM Standard](https://dom.spec.whatwg.org/) — DOM nodes, collections, event targets, and event dispatch.
- [WHATWG HTML Standard](https://html.spec.whatwg.org/multipage/) — browser event loops, document readiness, and host timers.
- [WHATWG URL Standard](https://url.spec.whatwg.org/) — URL components, parsing, and serialization.
- [W3C UI Events](https://w3c.github.io/uievents/) — keyboard event interfaces and legacy event types.
- [CSSOM View Module](https://drafts.csswg.org/cssom-view/) — offset metrics and viewport rectangles.
- [ECMAScript 2025](https://tc39.es/ecma262/2025/multipage/) — language bindings, modules, functions, and runtime semantics.
