# When should you use browser load, DOM ready, resize, or scroll events? / 何时使用 load、DOM ready、resize 或 scroll 事件？

`load` waits for dependent resources; `DOMContentLoaded` follows parsing and deferred/module script execution. `resize` and `scroll` report later viewport or document changes and can fire frequently, so keep handlers bounded and use an observer when it better fits the need. / `load` 等待相关资源；`DOMContentLoaded` 在解析及 defer/module 脚本执行后触发。`resize` 与 `scroll` 会报告后续视口或文档变化，触发可能很频繁，因此处理器应保持轻量，适合时可使用 Observer。

## Event reference / 事件参考

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

**See also / 另见：** [Event Loop / 事件循环](../../../../frontend/runtime/event-loop.md), [Browser Basics / 浏览器基础](../../../../frontend/browser/browser-basics.md), and [DOM Manipulation and Events / DOM 操作与事件](../../../../frontend/browser-apis/dom-manipulation-and-events.md).
