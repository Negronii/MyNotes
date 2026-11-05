# Why can HTMLCollection and NodeList change while you read them? / HTMLCollection 和 NodeList 为什么会在读取时变化？

`HTMLCollection` contains elements and is live; a `NodeList` can be live or static depending on the API that created it. `children` and `childNodes` reflect current children, while `querySelectorAll()` returns a static membership snapshot. Copy a live collection before iterating if the loop mutates the DOM. / `HTMLCollection` 只包含元素且为实时集合；`NodeList` 是否实时取决于创建它的 API。`children` 和 `childNodes` 反映当前子节点，而 `querySelectorAll()` 返回成员关系固定的静态快照。若循环会修改 DOM，先复制实时集合。

Given:

~~~html
<p id="message"><em>Hello</em> text <b>world</b><!-- note --></p>
~~~

~~~javascript
const message = document.querySelector('#message');

message.children;   // live HTMLCollection: em, b
message.childNodes; // live NodeList: em, text, b, comment

const snapshot = message.querySelectorAll('*'); // static NodeList: em, b
message.append(document.createElement('i'));
message.children.length;   // 3
message.childNodes.length; // reflects the new child
snapshot.length;           // still 2
~~~

Whitespace between tags creates text nodes, so `childNodes` is not an element-only list. `Element.children` is for child elements. `tagName` is available on elements; `nodeName` is available on every node, including text and comment nodes. The collections are array-like, not arrays; use `Array.from(collection)` when you need array methods or a stable snapshot. A live list can shift as you remove members, changing which index the loop reads next.

For event propagation and DOM mutation examples, see [DOM Manipulation and Events](../../../frontend/browser-apis/dom-manipulation-and-events.md). The [DOM Standard's old-style collections](https://dom.spec.whatwg.org/#old-style-collections-node-list-and-html-collection) specifies liveness and the collection interfaces.
