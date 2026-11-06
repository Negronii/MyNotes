# What is the difference between an HTMLCollection and a NodeList? / HTMLCollection 与 NodeList 有什么区别？

Both are array-like collections of DOM nodes, but they differ in which nodes they contain and whether their view updates. An `HTMLCollection` contains elements and is live. A `NodeList` may include text and comment nodes; whether it is live depends on the API that returned it: `querySelectorAll()` is static, while `childNodes` is live. Choose from the returned API's contract, and avoid mutating a live collection while advancing forward through its indexes. / 两者都是类数组的 DOM 节点集合，但包含的节点类型和更新方式不同。`HTMLCollection` 只含元素且是实时集合。`NodeList` 可含文本和注释节点；是否实时取决于返回它的 API：`querySelectorAll()` 是静态集合，而 `childNodes` 是实时集合。应根据具体 API 的契约选择，并避免在正向按索引遍历时修改实时集合。

| Collection | Typical source | Contents | Update behavior |
|---|---|---|---|
| `HTMLCollection` | `getElementsByClassName()`, `getElementsByTagName()`, `children` | `Element` nodes only | Live |
| `NodeList` | `querySelectorAll()` | Matching elements | Static snapshot |
| `NodeList` | `childNodes` | Elements, text, comments, and other child nodes | Live |

~~~html
<p id="p1"><em>hello</em> world <b>bold</b><!-- comment --></p>
~~~

~~~javascript
const paragraph = document.querySelector("#p1");
const elements = paragraph.children;
const childNodes = paragraph.childNodes;
const snapshot = paragraph.querySelectorAll("*");
paragraph.append(document.createElement("i"));

elements.length;   // 3 elements: em, b, i
childNodes.length; // 5 nodes: em, text, b, comment, i
snapshot.length;   // still 2 members: em, b
~~~

A static list fixes which nodes are members. It does not freeze the node objects or their properties. Whitespace and comments can appear in `childNodes`; `tagName` belongs to elements, while all nodes have a `nodeName`.

Removing items from a live collection while incrementing the index shifts later entries underneath the loop. Iterate backward or take an explicit snapshot:

~~~javascript
for (const element of Array.from(container.getElementsByClassName("item"))) {
  element.remove();
}
~~~

Use `querySelectorAll()` when a static result is simpler to reason about. Use a live collection only when reflecting subsequent matching-tree changes is useful; “live” specifies observable data, not how often an engine recomputes it.

**See also:** [How do DOM events propagate?](./dom-manipulation-and-events.md) discusses event targets in a changing DOM.

**Specification:** [WHATWG DOM: `NodeList` and `HTMLCollection`](https://dom.spec.whatwg.org/#old-style-collections-node-list-and-htmlcollection), checked 2026-11-05.
