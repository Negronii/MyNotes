# DOM: Document Object Model

The Document Object Model (DOM) represents a webpage so that programs can change the document structure, style, and content. The DOM represents the document as nodes and objects, which can be manipulated with scripting languages like JavaScript.

## Accessing Elements

### getElementById

Retrieves an element by its ID. This method returns a single element object.

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

Retrieves all elements with the specified tag name. This method returns an HTMLCollection, which is a pseudo-array (array-like object).

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

## Modern Methods (HTML5)

### getElementsByClassName

Retrieves all elements with the specified class name. This method returns an HTMLCollection.

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

Retrieves the first element that matches the specified CSS selector. This method returns a single element object.

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

Retrieves all elements that match the specified CSS selector. This method returns a NodeList, which is a collection of nodes.

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

- `onclick`: Triggered when an element is clicked.
- `onmouseover`: Triggered when the mouse pointer moves over an element.
- `onmouseout`: Triggered when the mouse pointer moves out of an element.
- `onkeydown`: Triggered when a key is pressed down.
- `onkeyup`: Triggered when a key is released.
- `onsubmit`: Triggered when a form is submitted.
- `onload`: Triggered when the page has loaded.
- `onresize`: Triggered when the window is resized.

**Example**

```javascript
btn.onclick = function () {
  // do something when the button is clicked
};
```

In this example, `onclick` is the event type that triggers the provided function when the button is clicked.

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

`element.innerText` returns or sets the text content of an element, excluding any HTML tags.

**Example**

```javascript
element.innerText = "2024-06-04";
```

This sets the inner text of the element to '2024-06-04'.

### `innerHTML`

`element.innerHTML` returns or sets the complete HTML content of an element, including HTML tags.

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

  // Alternatively, use 'this' keyword, which refers to the event function caller (btn)
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
   - Important for accessibility and SEO.
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
- Always include the `alt` attribute for better accessibility and SEO.
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

Custom attributes allow you to add extra information to HTML elements:

1. **HTML Built-in Attributes:**
   ```html
   <div id="test" index="1"></div>
   ```

2. **Accessing Attributes:**
   ```javascript
   var div = document.querySelector("#test");
   console.log(div.id); // 'test'
   console.log(div.getAttribute("index")); // '1'
   ```

3. **Setting Attributes:**
   ```javascript
   div.setAttribute("class", "box");
   div.setAttribute("index", "1");
   ```

4. **Removing Attributes:**
   ```javascript
   div.removeAttribute("index");
   ```

5. **Developer-defined Attributes:**
   - Must start with `data-`.
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

1. **`parentNode.childNodes`:** Returns a live collection of all child nodes, including element, attribute, and text nodes.
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

  for (const key in data) {
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
for (const key in obj) {
  // key is property name
  // obj[key] is property value
}
```

## Event Operations

### Registering Events

**Recommended Method by W3C**: `addEventListener`

```javascript
eventTarget.addEventListener(type, listener, useCapture);
```

- **Type**: Event type string, e.g., `click`, `mouseover`.
- **Listener**: Function to call when the event occurs.
- **useCapture**: Optional, defaults to `false`.

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

- **Capturing Phase**: Event starts from the document and traverses down to the target element.
- **Bubbling Phase**: Event bubbles up from the target element to the document.

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

In JavaScript, when an event occurs (e.g., a click or a keypress), an event object is created containing detailed information about the event. The event object provides various properties and methods that can be used to handle the event.

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
  - `this` refers to the element to which the event handler is attached.

  ```javascript
  btn.onclick = function (e) {
      console.log(e.target); // Element that was clicked
      console.log(this);     // Element to which the event handler is attached
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
    if (e.target.tagName === 'LI') {
        e.target.style.backgroundColor = 'pink'; // Change background of clicked <li>
    }
});
```

By attaching a single event listener to the `<ul>`, you can handle clicks on all `<li>` elements.

### Benefits of Event Delegation

- **Efficiency**: Reduces the number of event listeners, improving performance.
- **Dynamic Content**: Automatically handles dynamically added child elements.

## Mouse Events

### Disabling Right-Click Menu

- **`contextmenu` Event**: Used to disable the default context menu.
  ```javascript
  document.addEventListener('contextmenu', function (e) {
      e.preventDefault(); // Disables right-click menu
  });
  ```

### Disabling Text Selection

- **`selectstart` Event**: Used to disable text selection.
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
- **`keypress`**: Similar to `keydown`, but does not detect special keys like Shift, Ctrl, or Arrow keys.

### Example: Handling Keyboard Events

```javascript
document.addEventListener('keyup', function (e) {
    console.log(e.keyCode); // Outputs the ASCII value of the released key
});
```

### Best Practices

- Use `keyup` for actions that should be executed once, as holding down a key triggers continuous `keydown` and `keypress` events.
- When using `addEventListener`, omit the "on" prefix (e.g., use `'keyup'`, not `'onkeyup'`).

# Browser Object Model (BOM)

The Browser Object Model (BOM) allows interaction with the browser window and provides access to various browser-related objects and properties. It encompasses several objects that help manage and interact with the browser environment. While the BOM has some inconsistencies across different browsers, understanding its components is essential for web development.

## BOM Components

### 1. `window` Object

The `window` object is the top-level object in the BOM hierarchy. It represents the browser window and provides methods and properties for interacting with the browser.

- **Global Object:**
  All global JavaScript variables and functions are properties of the `window` object.

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
  Avoid naming variables as "name" because `window.name` is a special property used to store the name of the window.

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
  - `userAgent`: The user agent string of the browser.
  - `platform`: The platform on which the browser is running.

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

The `onload` event is triggered when the window is fully loaded, including the document, CSS, images, and other resources.

- **Using `onload` Property:**
  ```javascript
  window.onload = function() {
    console.log('Window fully loaded');
  };
  ```

- **Using `addEventListener`:**
  ```javascript
  window.addEventListener('load', function() {
    console.log('Window fully loaded');
  });
  ```

### 2. `DOMContentLoaded` Event

The `DOMContentLoaded` event is triggered when the HTML document is completely loaded and parsed, without waiting for stylesheets, images, and subframes to finish loading.

- **Example:**
  ```javascript
  document.addEventListener('DOMContentLoaded', function() {
    console.log('Document fully loaded and parsed');
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

The `scroll` event is triggered when the user scrolls the content of an element.

- **Example:**
  ```javascript
  window.addEventListener('scroll', function() {
    console.log('Page scrolled');
  });
  ```

# JavaScript Timer Functions

## Timer Functions

### `setTimeout`

The `setTimeout` function is used to schedule the execution of a function after a specified timeout. It takes two parameters: the function to be executed and the timeout duration in milliseconds. The `window` object can be omitted when calling this function.

**Syntax:**
```javascript
setTimeout(function, delay);
```

**Example:**
```javascript
setTimeout(function () {
    console.log("Executed after 2 seconds");
}, 2000);
```

**Storing the Timer ID:**
You can store the timer ID for later use by assigning the `setTimeout` function call to a variable. This is useful for clearing the timeout before it executes.

**Example:**
```javascript
var timer = setTimeout(function () {
    console.log("This will not be executed if clearTimeout is called");
}, 2000);
```

### `clearTimeout`

The `clearTimeout` function is used to cancel a timer that was previously set using `setTimeout`. It takes the timer ID as a parameter.

**Syntax:**
```javascript
clearTimeout(timerID);
```

**Example:**
```javascript
clearTimeout(timer);
```

### `setInterval`

The `setInterval` function is used to repeatedly invoke a function at a specified interval. It takes two parameters: the function to be executed and the interval duration in milliseconds.

**Syntax:**
```javascript
setInterval(function, interval);
```

**Example:**
```javascript
setInterval(function () {
    console.log("Executed every 2 seconds");
}, 2000);
```

**Storing the Interval ID:**
You can store the interval ID for later use by assigning the `setInterval` function call to a variable. This is useful for clearing the interval when you no longer need it.

**Example:**
```javascript
var interval = setInterval(function () {
    console.log("This will not be executed if clearInterval is called");
}, 2000);
```

### `clearInterval`

The `clearInterval` function is used to stop the execution of an interval that was previously set using `setInterval`. It takes the interval ID as a parameter.

**Syntax:**
```javascript
clearInterval(intervalID);
```

**Example:**
```javascript
clearInterval(interval);
```

### Best Practices

1. **Clear Unused Timers and Intervals:**
   Always clear timers and intervals that are no longer needed to avoid memory leaks and unexpected behavior.

2. **Use Named Functions:**
   Using named functions instead of anonymous functions makes your code more readable and easier to debug.

   **Example:**
   ```javascript
   function greet() {
       console.log("Hello!");
   }
   var timer = setTimeout(greet, 2000);
   clearTimeout(timer);
   ```

3. **Handle Scope Correctly:**
   Use arrow functions to preserve the `this` context inside the callback functions for `setTimeout` and `setInterval`.

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

# `this` Keyword Usage

The `this` keyword in JavaScript is dynamically scoped, meaning its value depends on how the function is called.

### Global Usage

In the global context, `this` refers to the `window` object.

**Example:**
```javascript
console.log(this); // Outputs the window object
```

### Timer Function Usage

In timer functions such as `setTimeout` and `setInterval`, `this` also points to the `window` object by default. To ensure `this` refers to the correct context, use arrow functions or bind the function.

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

When a function is invoked as a method of an object, `this` refers to the object that owns the method.

**Example:**
```javascript
var obj = {
    name: "Object",
    greet: function () {
        console.log(this.name); // Outputs "Object"
    }
};
obj.greet(); // Invoking the 'greet' method on object 'obj'
```

**Event Listener Example:**
```javascript
var btn = document.getElementById("myButton");
btn.onclick = function () {
    console.log(this); // Outputs the clicked button object
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

Asynchronous tasks allow multiple operations to occur simultaneously, improving efficiency and performance. This approach is like multitasking, where you can boil water and cut vegetables at the same time, rather than waiting for the water to boil before starting to cut vegetables.

### Implementing Asynchronous Tasks in JavaScript

Asynchronous tasks in JavaScript are commonly implemented using callback functions, Promises, or `async/await`. These methods allow JavaScript to perform non-blocking operations, meaning other tasks can run while waiting for an async operation to complete.

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

In this example, `boilWater` is asynchronous and uses `setTimeout` to simulate boiling water. Once the water is boiled, it calls the `cutVegetables` function.

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

JavaScript uses an event loop to manage synchronous and asynchronous tasks. The event loop allows JavaScript to perform non-blocking operations by offloading tasks to the browser's API (like timers and network requests), which then push the callback functions to the event queue once they are completed.

### Event Loop Process:

1. All synchronous tasks are executed first and placed in the call stack.
2. When an asynchronous task is encountered (e.g., `setTimeout`, HTTP request), it is offloaded and its callback function is registered in the event queue.
3. Once the call stack is empty, the event loop picks the oldest task from the event queue and pushes it to the call stack.
4. This cycle continues indefinitely.

### Pseudo Code Example:

```javascript
Queue syncTasks;
Queue asyncTasks;

for (task : tasks) {
    if (task.isSync()) {
        syncTasks.offer(task);
    } else {
        asyncTasks.offer(task);
    }
}

while (true) {
    while (!syncTasks.isEmpty()) {
        do(syncTasks.pop());
    }

    if (!asyncTasks.isEmpty()) {
        syncTasks.push(asyncTasks.poll());
    }
}
```

# URL and Location Object

## URL Structure

The URL structure consists of the following components:

```
<protocol>://<host:port>/<path>/<?query>#<fragment>
```

### Example URL

```
http://www.itcast.cn/index.html?name=andy&age=18#link
```

### Components Explained

1. **Protocol**: Specifies the protocol used, such as `http`, `https`, `ftp`, `mailto`, etc.
2. **Host**: Represents the hostname of the server.
3. **Port**: Optional component, defaults to 80 for HTTP if not specified. For HTTPS, it defaults to 443.
4. **Path**: Represents the directory or file path on the server.
5. **Query**: Parameters passed in the URL, starting with `?` and separated by `&`.
6. **Fragment**: Refers to a specific location or anchor within the page, starting with `#`.

## Location Object

The `location` object provides various properties to access and manipulate the URL components.

### Properties

- `location.href`: Gets or sets the entire URL.
- `location.protocol`: Returns the protocol (e.g., `http:` or `https:`).
- `location.host`: Returns the hostname and port (e.g., `www.itcast.cn:80`).
- `location.hostname`: Returns the hostname (e.g., `www.itcast.cn`).
- `location.port`: Returns the port number, or an empty string if not specified.
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

- `navigator.userAgent`: Returns the user agent string for the browser. Useful for detecting the browser or device type.
- `navigator.language`: Returns the preferred language of the user.
- `navigator.platform`: Returns the platform on which the browser is running (e.g., `Win32`, `MacIntel`).

### Example: Detecting Mobile Browsers

```javascript
var isMobile = /Mobi|Android/i.test(navigator.userAgent);
if (isMobile) {
    console.log("You are using a mobile browser.");
} else {
    console.log("You are using a desktop browser.");
}
```

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

- `element.offsetParent`: Returns the nearest positioned ancestor element. If none, it returns the body element.
- `element.offsetTop`: Returns the top position of the element relative to its offset parent.
- `element.offsetLeft`: Returns the left position of the element relative to its offset parent.
- `element.offsetWidth`: Returns the element's width, including padding and borders.
- `element.offsetHeight`: Returns the element's height, including padding and borders.

### Difference Between Style and Offset

#### Offset Properties

- Can retrieve values from any stylesheet (inline, internal, or external).
- Values are unitless.
- `offsetWidth` includes padding, border, and content.
- Offset properties are read-only.

#### Style Properties

- Can only retrieve inline style values.
- Values include units.
- `style.width` does not include padding and border.
- Style properties are readable and writable.

### Example: Getting the Coordinates Inside a Box

```javascript
element.addEventListener('mousemove', function (e) {
    var x = e.pageX - this.offsetLeft;
    var y = e.pageY - this.offsetTop;
    console.log('X coordinate inside the box: ' + x);
    console.log('Y coordinate inside the box: ' + y);
});
```

## Mouse drag

Mouse drag can be detected by combining `mousedown` and `mousemove` events.

Example:

```javascript
function doSomething(){
}

var title = querySelector(...)
title.addEventListener("mousedown", function(){
    document.addEventListener("mousemove", doSomething)
})

title.addEventListener("mouseup", function(){
    document.removeEventListener("mousemove", doSomething)
})
```