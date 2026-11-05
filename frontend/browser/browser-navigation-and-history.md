# Does every URL change load a new document? / 每次 URL 变化都会加载新文档吗？

No. A cross-document navigation switches to another `Document` and may fetch a response; a fragment navigation can add a session-history entry that shares the current document; `history.pushState()` and `replaceState()` update the current document's URL and history without fetching that address. Use the URL as the shareable source of route state, and synchronize the UI when the user traverses Back or Forward. / 不会。跨文档导航会切换到另一个 `Document`，并可能获取响应；片段导航可新增历史条目但仍共享当前文档；`history.pushState()` 和 `replaceState()` 则在当前文档内更新 URL 与历史记录，不会请求该地址。让 URL 保存可分享的路由状态，并在用户前进或后退时同步界面。

## Parse query state and choose an operation / 解析查询状态并选择操作

Create a `URL` from the current address instead of splitting strings on `?` and `&`. `searchParams.get()` reads one value, `getAll()` reads repeated values, `set()` replaces values with that name, and `append()` deliberately adds another pair. Serialization handles URL encoding. Query parameters are untrusted input: validate values and keep secrets out of URLs.

- Use an anchor or `location.assign(url)` for a normal navigation that should create a history entry. Use `location.replace(url)` when the current entry should be replaced.
- Use `pushState(state, "", url)` to add a same-document entry, or `replaceState(...)` to edit the current entry. The URL must be same-origin. These calls do not fetch the URL or fire `popstate` or `hashchange`.
- On Back/Forward traversal, handle `popstate` and derive the displayed route from `location` (and `event.state` when the application uses it). Fragment navigation is distinct: history traversal involving fragment changes can dispatch `popstate`; a fragment change can also dispatch `hashchange`.

This sorting example keeps its selected value and summary in step with the query string. It updates the view directly after `pushState`, then re-reads the address after history traversal.

~~~html
<label for="sort">Sort results</label>
<select id="sort">
  <option value="recent">Most recent</option>
  <option value="oldest">Oldest first</option>
</select>
<p id="summary"></p>

<script>
const sortSelect = document.querySelector("#sort");
const summary = document.querySelector("#summary");

function syncFromUrl() {
  const url = new URL(location.href);
  const sort = url.searchParams.get("sort") === "oldest" ? "oldest" : "recent";
  sortSelect.value = sort;
  summary.textContent = sort === "oldest" ? "Oldest results first" : "Most recent results first";
}

sortSelect.addEventListener("change", () => {
  const url = new URL(location.href);
  url.searchParams.set("sort", sortSelect.value);
  history.pushState(null, "", url.href);
  syncFromUrl();
});

window.addEventListener("popstate", syncFromUrl);
syncFromUrl();
</script>
~~~

A client-side router can use these same-document entries to change views, but it owns rendering and route restoration. Browser History API behavior is not the same as a document navigation, even when the visible URL changes.

**See also:** [React Router / React 路由](../frameworks/react-basics.md) builds client-side routes on browser history; [HTTP Protocols and WebSockets / HTTP 协议与 WebSocket](../../engineering-foundations/networking/http-protocols-and-websockets.md) covers network requests once navigation takes a fetching path.

**Standards / 规范：** [WHATWG URL Standard: `URLSearchParams`](https://url.spec.whatwg.org/#urlsearchparams-class); [WHATWG HTML: same-document navigation and History API](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-history-interface), checked 2026-11-05.
