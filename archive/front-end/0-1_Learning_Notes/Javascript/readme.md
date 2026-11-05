# What do browser URL and navigation objects expose? / 浏览器 URL 与导航对象提供什么信息？

The `location` object exposes the current document URL and navigation operations; `URLSearchParams` parses query parameters, while `history` moves through same-origin session history. Treat user-agent parsing as a brittle heuristic. / `location` 提供当前文档 URL 和导航操作；`URLSearchParams` 用于解析查询参数；`history` 用于浏览同源会话历史。用户代理字符串解析只能视为脆弱的启发式判断。

This path remains the broader URL/property catalog linked from [Browser Basics / 浏览器基础](../../../../frontend/browser/browser-basics.md). For DOM selection, mutation, and input handling, see the focused pages below. / 此路径保留[浏览器基础](../../../../frontend/browser/browser-basics.md)所链接的扩展 URL/属性目录。DOM 选择、修改和输入处理见下方专题页。

## URL and Location Object

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

## Related topics / 相关主题

- [DOM selection / DOM 选择](dom-element-selection.md)
- [DOM attributes and style updates / DOM 属性与样式更新](dom-attributes-and-style-updates.md)
- [DOM tree traversal and mutation / DOM 树遍历与修改](dom-tree-traversal-and-mutation.md)
- [DOM event and input examples / DOM 事件与输入示例](dom-event-and-input-examples.md)
- [Browser lifecycle events / 浏览器生命周期事件](browser-lifecycle-events.md)
- [Asynchronous JavaScript / 异步 JavaScript](../../../../frontend/javascript/asynchronous-javascript.md) and [Event Loop / 事件循环](../../../../frontend/runtime/event-loop.md) for timers and task scheduling.
