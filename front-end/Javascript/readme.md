# DOM: Document Object Module

Every element is an object, and the document represents the entire HTML document.

## getElementByID

To retrieve an element in the document, we use the following syntax:

```javascript
<element name>.getElementById('<element id>')
```

For example:

```javascript
document.getElementById("time");
```

The return value is an object. To log the element object we retrieve, we can use:

```javascript
console.dir(<element object>)
```

## getElementByTagName

To retrieve elements by their tag name, we use the syntax:

```javascript
<element name>.getElementsByTagName('<tag name>')
```

For instance, if we want to retrieve `<li>` elements, we use:

```javascript
document.getElementsByTagName("li");
```

The return value is a pseudo array, which can be accessed using the following syntax:

```javascript
<returnObject>[<index>]
```

To traverse the returned elements, we can use a loop:

```javascript
for (let i = 0; i < <returnObject>.length; i++) {
  <returnObject>[i]
}
```

If no elements are found, an array with a length of 0 will be returned.

To retrieve the child elements within a parent tag, we can use the following approach:

```javascript
const ols = document.getElementsByTagName('ol');
const lis = ols[<index>].getElementsByTagName('li');
```

# Some get function only available in HTML5

## getElementsByClassName

```javascript
<element name>.getElementsByClassName('<class name>')
```

- Return a collection of elements.
- Example:

```javascript
var boxes = document.getElementsByClassName("box");
```

## querySelector

```javascript
document.querySelector("<selector>");
```

- Return the first element selected by the selector.
- Examples:

```javascript
var box = document.querySelector(".box");
var box = document.querySelector("#nav");
var box = document.querySelector("li");
```

- Useful in developing.

## querySelectorAll

```javascript
document.querySelectorAll("<selector>");
```

- Return all elements selected by the selector.
- Example:

```javascript
var boxes = document.querySelectorAll(".box");
```

- Useful in developing.

## document.body & document.documentElement

```javascript
var bodyEle = document.body; // get body element object
var htmlEle = document.documentElement; // get html element object
```

# Events introduction

Events consist of three parts: event source, event type, event handler.

- Event source: Which object triggered the event? Example:

```javascript
var btn = document.getElementById("btn");
```

- Event type: How to trigger the event? What is the event?
- Here is a list of some common HTML events:

  - onclick
  - onmouseover
  - onkeydown
  - onsubmit
  - ...
    (Note: Please provide specific event names for a more accurate list)

- Event handler: Define the function for the event type. Example:

```javascript
btn.onclick = function () {
  // do something
};
```

# Modify element attributes

`innerText` & `innerHTML`

- `element.innerText`: Returns the text content of an element, excluding any HTML tags, spaces, and newlines inside.

  - Example:
    ```javascript
    element.innerText = "2022-11-09"; // define the value
    ```
    This sets the inner text of the element to '2022-11-09'.

- `element.innerHTML`: Returns the complete HTML content of an element, including any HTML tags, spaces, and newlines inside.
  - Example:
    ```javascript
    element.innerHTML = "<strong>Today is:</strong> 2022-11-09";
    ```
    This sets the inner HTML of the element to '<strong>Today is:</strong> 2022-11-09'.

`input` attributes

- `<button>`: Represents a clickable button.
- `<input type="text" value="please enter">`: Represents a text input field with an initial value of 'please enter'.

```html
<script>
  var btn = document.querySelector("button");
  var input = document.querySelector("input");

  // Register the onclick event
  btn.onclick = function () {
    // Modify the input value
    input.value = "entered";

    // Disable the button, making it unclickable
    btn.disabled = true;

    // Alternatively, we can use 'this' keyword, which refers to the event function caller (btn)
    this.disabled = true;
  };

  input.onfocus = function () {
    // Event handler when the user clicks on the input
  };

  input.onblur = function () {
    // Event handler when the user clicks on the input and then clicks somewhere else
  };

  // Get the number of characters in the input value
  input.value.length;
</script>
```

## Image attributes

- `src`: Specifies the source URL of an image.
- `href`: Specifies the URL of a linked resource (typically used with anchor tags).
- `id`: Specifies a unique identifier for an element.
- `alt`: Specifies alternative text for an image, to be displayed if the image cannot be loaded.
- `title`: Specifies extra information about an element (typically displayed as a tooltip).

```javascript
img.src = "pic/pic.png";
```

## Inline Style modification

- Modify the style attributes of an element using JavaScript.
- Style attributes use lower camel case naming strategy (e.g., `backgroundColor` instead of `background-color`).
- To hide an element, set its `display` style property to `'none'`.

```javascript
var div = document.querySelector("div");

// Modify background color
div.style.backgroundColor = "pink";

// Hide the div
div.style.display = "none";
```

## Classname style modification

- Change the class name of an element. If the element already has a class name, it will be replaced.
- To keep the previous class name, separate multiple class names with a space.

```javascript
var div = document.querySelector("div");
div.className = "box";

// To keep the previous class name
div.className = "first second";
```

## Customized attributes

- Elements can have attributes defined by HTML built-in and by developers.
- To use HTML built-in attributes: `<elementName>.<attributeName>`
- To use all variables (including customized): `<elementName>.getAttribute('<attribute name>')`

Example:

```html
<div id="test" index="1"></div>
```

```javascript
var div = document.querySelector("div");
div.id; // returns 'test'
div.getAttribute("index"); // returns '1'
```

- Set built-in attributes: `<elementName>.<attributeName> = '<value>'`
- Set

all attributes: `<elementName>.setAttribute('<attributeName>', '<value>')`

Example:

```javascript
div.setAttribute("class", "box");
div.setAttribute("index", "1");
```

- Remove an attribute: `<elementName>.removeAttribute('<attributeName>')`

Example:

```javascript
div.removeAttribute("index");
```

- W3C Rule: Developer-defined attributes must start with `data-`, e.g., `data-index`.
- `dataset`: Stores all attributes starting with `data-`. Attribute names with `-` will be transferred to lower camel case naming, i.e., `data-test-attr` will be `dataset.testAttr`.

Example:

```html
<div id="test" data-index="1" data-test-attr="test"></div>
```

```javascript
var div = document.querySelector("div");
div.dataset.index; // returns '1'
div.dataset.testAttr; // returns 'test'
```

In development, `getAttribute` and `setAttribute` are more commonly used.

# Node operations

Node operations can make it easier to find the son elements of the elements. It has worse compatibility but easier to develop front-end. A node has `nodeType`, `nodeName`, `nodeValue`.

## Element node:

`nodeType = 1` (most useful)

## Attribute node:

`nodeType = 2`

## Text node:

`nodeType = 3` (text, space, newline)

# parentNode

`node.parentNode` // get the closest parent of this node, if there is no parent node return null

E.g.

```html
<div class="box1">
  <div class="box2"></div>
</div>
```

```javascript
var div = document.querySelector(".box2");
box2.parentNode; // will get div with class = box1
```

# Get child nodes

`<parentNode>.childNodes` // get a collection of all child nodes, including element, attribute, and text. Therefore, if we want to get all element nodes, we need a for loop and check if `child.nodeType == 1`

```javascript
var div = document.querySelector(".box1");
box2.childNodes; // will get div with class = box2
```

So, `childNodes` is not recommended.

`<parentNode>.children` // return all element children nodes, useful in development

`<parentNode>.firstChild` // return the first child node, whatever it is element, attribute, or text node.

`<parentNode>.lastChild` // return the last child node, whatever it is element, attribute, or text node.

`<parentNode>.firstElementChild` // return the first element child node

`<parentNode>.lastElementChild` // return the last element child node

However, both first and last element child have compatibility issues. Only IE9+ supports this.

```javascript
<parentNode>.children[0]  // return the first element child node, useful in development
<parentNode>.children[<parentNode>.children.length - 1]  // return the last element child node, useful in development
```

## Sibling nodes

`<node>.nextSibling` // return the next sibling node, whatever it is element, attribute, or text node. If cannot find, return null.

`<node>.previousSibling` // return the previous sibling node, whatever it is element, attribute, or text node. If cannot find, return null.

`<node>.nextElementSibling` // return the next element sibling node. If cannot find, return null.

`<node>.previousElementSibling` // return the previous element sibling node. If not found, return null.

However, both next and previous sibling element child have compatibility issues. Only IE9+ supports this.

So, to avoid compatibility issues, we can use:

```javascript
var el = element;
while (el = element.nextSibling) {
    if (el.nodeType == 1)
        // do something
}
// not found
return null;
```

## Create node

Create a node

Place it in a parent node

```javascript
var <elementName> = document.createElement('<tagName>') // create a dynamic node
node.appendChild(<child>) // append a child node at the end of a node, similar to after sudo element in CSS
```

e.g.

```html
<ul>
  <li>123</li>
</ul>
```

```javascript
var li = document.createElement("li");
var ul = document.querySelector("ul");
ul.appendChild(li);
```

Result will become `<ul><li>123</li><li></li></ul>`

```javascript
node.insertBefore(<child>, <indicated element>) // insert a child node before a node, similar to before

 sudo element in CSS
```

e.g.

```html
<ul>
  <li>123</li>
</ul>
```

```javascript
var li = document.createElement("li");
var ul = document.querySelector("ul");
ul.insertBefore(li, ul.children[0]);
```

Result will become `<ul><li></li><li>123</li></ul>`

Efficiency under a large amount of element creation: much faster than `innerHTML += "…"`

However, if we use an array to store string elements and use `<element>.innerHTML = <array>.join('')`, it will be faster than `createElement`

## Remove node

`<node>.removeChild(<child>)` // remove the child from node, return the deleted node

e.g.

```html
<ul>
  <li>a</li>
  <li>b</li>
  <li>c</li>
</ul>
<button></button>
```

```javascript
var ul = document.querySelector("ul");
var button = document.querySelector("button");
button.onclick = () => {
  if (ul.children.length > 0) ul.removeChild(ul.children[0]);
  else this.disabled = true;
};
```

## Clone node

`<node>.cloneNode()` returns the clone of the node. If we put no parameter or false, it will be a shallow copy with no child nodes. If we put true in the parameter, it will return a deep copy, i.e., `<node>.cloneNode(true)`

e.g.

```html
<ul>
  <li>a</li>
  <li>b</li>
  <li>c</li>
</ul>
<button></button>
```

```javascript
var ul = document.querySelector("ul");
var lili = ul.children[0].cloneNode();
ul.appendNode(lili);
```

## Dynamic table

E.g.

```html
<table>
  <thead>
    <th>name</th>
    <th>subject</th>
    <th>grade</th>
  </thead>
  <tbody></tbody>
</table>
```

```javascript
var mockData = [
  { name: "Ron", subject: "math", grade: "100" },
  { name: "jack", subject: "calculus", grade: "70" },
  { name: "Mar", subject: "bus", grade: "90" },
];
var body = document.querySelector("tbody");
for (var I = 0; I < mockData.length; I++) {
  var tr = document.createElement("tr");
  tbody.append(tr);
  for (var k in mockData[I]) {
    var td = document.createElement("td");
    td.innerHTML = mockData[I][k];
    tr.appendChild(td);
  }
}
```

Remember for object traverse:

```javascript
for (var k in obj) {
  // k is property name
  // obj[k] is property value
}
```

# Event Operations

## Register Event

The method recommended by w3c: `addEventListener`

```javascript
<eventTarget>.addEventListener(<type>, listener, [, useCapture]);
```

- **Type**: event type string, could be `click`, `mouseover` (no `on` here, not `onClick`)
- **Listener**: function to call when the event happens
- **useCapture**: optional, default is `false`

Example:

```javascript
btn = querySelector(button);
btn.onclick = () -> { //traditional way}
btn.addEventListener('click', () -> { // recommended way})
```

### What is the difference between the traditional way and event listener?

The traditional way can only call one function, or we need a wrapper to contain functions in sequence. However, with the event listener approach, the same event on the same element can have multiple listeners. For example:

```javascript
btn.addEventListener('click', () -> {alert(11)})
btn.addEventListener('click', () -> {alert(12)})
btn.addEventListener('click', () -> {alert(13)})
```

In this case, it will alert `11`, `12`, `13` in sequence.

## Remove Event

The method to remove an event listener: `removeEventListener`

```javascript
<eventTarget>.removeEventListener(<type>, listener);
```

Example for a single-use button:

```javascript
function fn() {
  alert(11);
  btn.removeEventListener("click", fn);
}

btn.addEventListener("click", fn); // note here! fn not fn(), no brackets
```

## DOM Event Stream

Event stream: the sequence of accepting events from the document.

When the document (page) detects an event, it will proceed to find which element listens to the event. The element listening to the event will tell the parent node until the document catches the event.

The traditional `onclick` and `onmouseover` trigger events at the bubbling stage.

Using `<eventTarget>.addEventListener(<type>, listener, true)` will trigger events at the capturing stage.

### What's the difference?

If at the capturing stage and both the father and son have a click event listener:

- The father's event will trigger first, then the son.

If at the bubbling stage and both the father and son have a click event listener:

- The son's event will trigger first, then the father.

## Event Object

```javascript
btn.onclick = function (event) {};
```

Event is an object. If it is a click event, it will contain information like mouse coordinates. If it is a key-pressed event, it will contain which key is pressed.

The system will provide the event object for us; there's no need to pass it as a parameter. The event can be named `e`, `evt`, or `event`.

Compatibility issue: IE 6-8 does not support auto parameter passing; we can use `window.event` to access the event object.

`e.target` and `this` may be different. For example, when clicking on the son, the father's click event listener will also be triggered, but `e.target` refers to the son.

`e.preventDefault()` can be used to prevent the default actions, such as clicking on a link but not navigating. However, `preventDefault` has compatibility issues. Alternatively, we can let the listener function return `false` to achieve the same goal.

`e.stopPropagation()` is used to prevent further bubbling. If the son triggers the event, the father will not trigger it. This method also has compatibility issues, but we can use `e.cancelBubble = true`.

## Event Delegation

Example:

```javascript
<ul>
  <li>click to do something</li>
  <li>click to

 do something</li>
  <li>click to do something</li>
</ul>

var ul = document.querySelector('ul')
ul.addEventListener('click', (e) -> {
    // do something
    // e.target can get the li it is clicking on
    e.target.style.backgroundColor = 'pink'
})
```

We can register the event to the `ul` (parent node) and then use the target attribute of the event object to find the `li` element that was clicked. Because clicking on the `li` will bubble the event to the parent node `ul`, and the parent node `ul` has registered the event, it will trigger the event handler.

The advantage of event delegation over setting registered events for all `li` elements is that we only operate on the DOM once, improving efficiency.

# Mouse events

## Disable right click menu - `contextmenu`

`contextmenu` controls when to display the context menu and is often used to disable the default context menu.

```javascript
document.addEventListener("contextmenu", (e) => {
  e.preventDefault();
});
```

## Disable mouse selection - `selectstart`

`selectstart` event is used to disable mouse selection.

```javascript
document.addEventListener("selectstart", (e) => {
  e.preventDefault();
});
```

# Mouse event attributes

- `e.clientX`: X coordinate relative to the viewable area of the browser
- `e.clientY`: Y coordinate relative to the viewable area of the browser
- `e.pageX`: X coordinate relative to the document page
- `e.pageY`: Y coordinate relative to the document page
- `e.screenX`: X coordinate relative to the screen
- `e.screenY`: Y coordinate relative to the screen

Example: Moving a picture with the mouse

```html
<style>
  .pic {
    position: absolute;
    top: 2px; /* remember the absolute positioning requires a top value */
  }
</style>

<body>
  <img src="…" alt="" />
</body>
```

```javascript
var pic = document.querySelector("img");
document.addEventListener("mousemove", (e) => {
  // trigger when the mouse move ≥ 1px
  var x = e.pageX;
  var y = e.pageY;
  pic.style.left = x + "px";
  pic.style.top = y + "px";
});
```

# Keyboard events

- `onkeyup`: Triggered when a key is released (loosing).
- `onkeydown`: Triggered when a key is pressed down.
- `onkeypress`: Similar to `onkeydown`, but cannot identify function keys like shift or ctrl or arrows.

When using `addEventListener`, don't add "on" at the start of the word. For example, use `'keyup'` or `'keydown'`.

Example:

```javascript
document.addEventListener("keyup", (e) => {
  // e.keyCode to get the ASCII value of the pressed key, e.g., pressing number 1
  // then the keyCode = 49
});
```

For actions that we want to execute once, use `keyup`, since holding the key down will continuously trigger `keydown` and `keypress`.

# BOM - Browser Object Model

The Browser Object Model (BOM) allows interaction with the browser window and provides access to various browser-related objects and properties. However, it has worse compatibility across different browsers.

## BOM Includes

The BOM includes the following objects:

- `document`: Represents the current HTML document loaded in the browser.
- `location`: Provides information about the URL of the current document and allows navigation to other URLs.
- `navigation`: Represents the user's navigation history (back, forward, etc.).
- `screen`: Provides information about the user's screen or display.
- `history`: Represents the browser's session history.

## Window Object

The `window` object serves as an interface to interact with the browser and is a global object. All variables and functions become attributes and functions of the `window` object. For example, `window.document` refers to the document we use before.

Some other commonly used functions, such as `alert()` and `prompt()`, are also part of the `window` object.

It's important to note that `window.name` has a special attribute, so it's advisable to avoid setting a variable with the name "name."

Example:

```javascript
var i = 10;
console.log(i);
console.log(window.i);
```

## `onload` Event

The `onload` event is triggered when the window is fully loaded, including the document, CSS, images, and Flash content.

There are two ways to handle the `onload` event:

1. Using the `onload` property of the `window` object:

```javascript
window.onload = function () {
  // Code to be executed after the window is loaded
};
```

2. Using the `addEventListener` method of the `window` object:

```javascript
window.addEventListener("load", function () {
  // Code to be executed after the window is loaded
});
```

## `DOMContentLoaded` Event

The `DOMContentLoaded` event is triggered when the document is loaded, excluding external resources such as CSS, images, and Flash content. This event is useful when there are many images to load, and you want to perform certain actions before all the images are loaded.

Example:

```javascript
document.addEventListener("DOMContentLoaded", function () {
  // Code to be executed when the document is loaded
});
```

## `resize` Event

The `resize` event is triggered when the size of the browser window changes. This event is often used in responsive programming to adjust the layout or behavior of the page based on the window size.

There are two ways to handle the `resize` event:

1. Using the `onresize` property of the `window` object:

```javascript
window.onresize = function () {
  // Code to be executed when the window size changes
};
```

2. Using the `addEventListener` method of the `window` object:

```javascript
window.addEventListener("resize", function () {
  // Code to be executed when the window size changes
});
```

The `window.innerWidth` property can be used to obtain the current width of the browser window.

# Timer

The `setTimeout` function is used to schedule the execution of a function after a specified timeout. It takes two parameters: the function to be executed and the timeout duration in milliseconds. The function will be invoked once the specified timeout has elapsed. The `window` object can be omitted when calling this function.

Example:

```javascript
setTimeout(function () {}, 2000);
```

To store the timer ID for later use, you can assign the `setTimeout` function call to a variable.

Example:

```javascript
var timer = setTimeout(function () {}, 2000);
```

# clearTimer

The `clearTimer` function is used to cancel a timer that was previously set using `setTimeout`. It takes the timer ID as a parameter. The `window` object can be omitted when calling this function.

Example:

```javascript
clearTimer(timer);
```

# setInterval

The `setInterval` function is used to repeatedly invoke a function at a specified interval. It takes two parameters: the function to be executed and the interval duration in milliseconds. The function will be invoked every specified interval. The `window` object can be omitted when calling this function.

Example:

```javascript
setInterval(function () {}, 2000);
```

To store the interval ID for later use, you can assign the `setInterval` function call to a variable.

Example:

```javascript
var interval = setInterval(function () {}, 2000);
```

# clearInterval

The `clearInterval` function is used to stop the execution of an interval that was previously set using `setInterval`. It takes the interval ID as a parameter. The `window` object can be omitted when calling this function.

Example:

```javascript
clearInterval(interval);
```

# 'this' Keyword Usage

## Global Usage

In global usage, `this` refers to the `window` object. For example:

```javascript
console.log(this); // Outputs the window object
```

## Timer Function Usage

In timer functions such as `setTimeout` and `setInterval`, `this` also points to the `window` object, regardless of whether it is inside a button click listener function. For example:

```javascript
setInterval(function () {
  console.log(this); // Outputs the window object
}, 2000);
```

## Function Invocation Usage

When a function is invoked, `this` points to the object that invokes the function. For instance:

```javascript
var o = {
  sayHi: function () {
    console.log(this); // Outputs the object 'o'
  },
};
o.sayHi(); // Invoking the 'sayHi' method on object 'o'

btn.onclick = function () {
  console.log(this); // Outputs the clicked button object
};
```

## Constructor Method Usage

In a constructor method, `this` points to the instance object being created. For example:

```javascript
function Fun() {
  console.log(this); // Outputs the instance object
}
var fun = new Fun(); // Creating an instance of 'Fun'
```

# Async and Sync

## Synchronized

Synchronized tasks involve completing one thing entirely before moving on to the next thing. For example:

- Boil water
- Cut vegetables
- Cook

## Asynchronous (Async)

Async tasks involve doing multiple things simultaneously. For example:

- Boil water
- Cut vegetables (at the same time)
- Cook

Async tasks are implemented using callback functions. Callback functions can include:

- Normal events, e.g., click, resize
- Resource loading, e.g., load, error
- Timers, e.g., setInterval, setTimeout

JavaScript handles tasks by placing all synchronized tasks in an operation stack and executing them one by one on the main thread. When it encounters a callback function, it adds it to an async queue. After completing all tasks in the sync stack, JavaScript continues to retrieve a task from the async queue, adds it to the sync stack, and executes it. This process continues in a loop known as the event loop.

Here's how JavaScript works in pseudo code:

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

# URL and Location object

The URL structure consists of the following components:

`<protocol>://<host:port>/<path>/<?query>#<fragment>`

Example URL: `http://www.itcast.cn/index.html?name=andy&age=18#link`

- **Protocol**: Specifies the protocol used, such as `http`, `ftp`, `mailto`, etc.
- **Host**: Represents the hostname of the server.
- **Port**: Optional component, defaults to 80 for HTTP if not specified.
- **Path**: Represents the directory or file path.
- **Query**: Parameters passed in the URL, starting with `?` and separated by `&`.
- **Fragment**: Refers to a specific location or anchor within the page.

## Location object

The `location` object provides various properties to access and manipulate the URL components.

- `location.href`: Gets or sets the entire URL.
- `location.host`: Returns the hostname, e.g., `www.itcast.cn`.
- `location.port`: Returns the port number, or an empty string if not specified.
- `location.pathname`: Returns the pathname.
- `location.search`: Returns the parameters.
- `location.hash`: Returns the fragment or anchor.

## `location.href`

This property is commonly used when we want to navigate to a different page.

Example usage:

```javascript
var div = querySelector("div");
var time = 5;
setInterval(function () {
  if (time == 0) {
    location.href = "www.itcast.cn";
  } else {
    div.innerHTML =
      "You will be navigated to itcast.cn in " + time + " seconds";
    time--;
  }
}, 1000);
```

## `location.search`

This property allows passing parameters from one page to another. We can use `location.href` to navigate to another page with a query.

Example:

- For the link `http://www.itcast.cn/index.html?name=andy`, `location.search` returns `?name=andy`.
- Use `substr` to extract the parameter: `var parameter = location.search.substr(1) // var parameter = 'name=andy'`.
- Split the parameter using `=` as the separator: `var arr = parameter.split('=')`. Now `arr[0] = name` and `arr[1] = andy`.

## Location methods

The `location` object provides methods to manipulate the browser location.

- `location.assign('<url>')`: Similar to changing `href`, it records the history so that the user can go back.
- `location.replace('<url>')`: Navigates without leaving a history entry, preventing the user from going back.
- `location.reload()`: Refreshes the current page.

## Navigator object

The `navigator` object provides information about the user's browser.

- `navigator.userAgent`: This feature can be used to detect whether the user is using a mobile or desktop browser. For more details, refer to this [Stack Overflow post](https://stackoverflow.com/questions/11381673/detecting-a-mobile-browser).

## History object

The `history` object provides methods to navigate through the browser history.

- `history.forward()`: Equivalent to clicking the forward button in the browser.
- `history.backward()`: Equivalent to clicking the back button in the browser.
- `history.go(<number>)`: Goes forward or backward in the history. Use negative numbers to go backward (`go(-1)`), positive numbers to go forward (`go(1)`), and so on.

# Web special effects

## Offset series

We can use the offset series attributes to get the element offset, location, size, etc.
The attributes do not have a unit.

## Frequent used attributes

`<element>.offsetParent` - returns the parent element with positioning. If no parent element has positioning, then it returns the body element.

`<element>.offsetTop` - returns the top offset of the parent element with positioning. If it does not have a parent element with positioning, it returns the top offset from the body element.

`<element>.offsetLeft` - returns the left border offset of the parent element with positioning. If it does not have a parent element with positioning, it returns the left offset from the body element.

`<element>.offsetWidth` - returns the width including padding, border, and content. The return value has no unit.

`<element>.offsetHeight` - returns the height including padding, border, and content. The return value has no unit.

## Difference between style and offset

### Offset

- It can get the style value from any stylesheet.
- The return value does not have a unit.
- `offsetWidth` includes padding + border + width.
- `offsetWidth` is read-only and cannot be assigned a value. If we want to get the width only, it is better to use `element.offsetWidth`.

### Style

- Style can only get inline style value. We cannot use `style.width` if it is written in a `<style>` element or an external file.
- `style.width` returns a string with a unit.
- `style.width` does not include padding and border.
- `style.width` is readable and writable. If we want to change the width, it is better to use `style`.

### Example: Get the coordinate inside the box

We can use the mouse move event.

Coordinate of X inside box = `e.pageX - this.offsetLeft`

Coordinate of Y inside box = `e.pageY - this.offsetTop`

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

# Client series

## Scroll series

Animation function packaging
