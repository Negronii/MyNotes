# How can JavaScript update DOM content, attributes, and styles? / JavaScript 如何更新 DOM 内容、属性与样式？

Use `textContent` or an appropriate text API for text, DOM properties or attributes for element state, and class names for style changes. Treat HTML strings as markup only when their source is trusted or sanitized. / 文本使用 `textContent` 等文本 API；元素状态使用 DOM 属性或 attribute；样式变化优先通过 class 名表达。只有来源可信或经过清理时才把字符串作为 HTML 标记插入。

## Modify Element Attributes

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

**See also / 另见：** [DOM Manipulation and Events / DOM 操作与事件](../../../../frontend/browser-apis/dom-manipulation-and-events.md).
