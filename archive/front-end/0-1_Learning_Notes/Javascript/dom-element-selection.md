# How do you select elements from the DOM? / 如何从 DOM 中选择元素？

Choose a selection API based on whether you need one element, all matches, a live collection, or a static snapshot. Check the result before using it, because a selector may match nothing. / 根据需求选择 API：单个元素、全部匹配项、实时集合或静态快照。使用结果前先检查，因为选择器可能没有匹配项。

## JavaScript DOM and Browser APIs / JavaScript DOM 与浏览器 API

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

**See also / 另见：** [DOM Manipulation and Events / DOM 操作与事件](../../../../frontend/browser-apis/dom-manipulation-and-events.md) for the current event and DOM behavior model.
