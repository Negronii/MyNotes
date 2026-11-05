# How do DOM events support delegation and mouse interaction? / DOM 事件如何支持事件委托与鼠标交互？

Use event delegation when descendants produce a bubbling event that a parent can handle. Pointer dragging needs explicit start/move/end handling and should also consider pointer capture and non-mouse input in new interfaces. / 当后代元素产生可冒泡事件时，可由父元素通过事件委托处理。拖动交互需要明确处理开始、移动和结束；新界面还应考虑指针捕获和非鼠标输入。

## HTML Events and Event Handling

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

**See also / 另见** — [DOM Manipulation and Events / DOM 操作与事件](../../../../frontend/browser-apis/dom-manipulation-and-events.md) for propagation, listener options, and delegation. [W3C UI Events](https://w3c.github.io/uievents/) defines keyboard event types and properties.
