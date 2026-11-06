# 修改 DOM 时，HTMLCollection 和 NodeList 会怎样变化？

案例背景：报表列表收到新结果后，界面要删除旧行并插入新行。Document Object Model (文档对象模型，DOM)的查询会返回 HTMLCollection（元素集合）或 NodeList（节点列表）；集合成员可能随树变化，也可能固定。若代码在遍历时修改实时集合，索引会移动，导致行被跳过。

| 来源 | 类型 | 包含什么 | 查询后发生 DOM 变更时 |
|---|---|---|---|
| `element.children`、`getElementsByClassName()` | `HTMLCollection` | 元素节点 | 实时反映当前树 |
| `element.querySelectorAll()` | `NodeList` | 匹配元素 | 静态成员列表 |
| `element.childNodes` | `NodeList` | 元素、文本、注释等子节点 | 实时反映当前树 |

因此，`NodeList` 不代表“静态”。需要根据具体查询 API 的契约判断；空白文本也会成为 `childNodes` 中的文本节点；通用节点应使用 `nodeName`，因为 `tagName` 只属于元素。`HTMLCollection` 和 `NodeList` 都不是普通数组，直接调用 `map()` 不可行，可用 `Array.from()` 创建数组快照。

> [!example] 正向删除实时集合会跳过一行
> 开始时列表按顺序是 `[r1, r2, r3]`。这些只是合成行 ID，与报表 ID、业务版本或事件游标无关。`children` 是实时集合：删掉索引 0 的 `r1` 后，`r2` 移到索引 0、`r3` 移到索引 1。循环把索引递增到 1，于是跳过 `r2`，下一轮删的是 `r3`。
>
> ~~~html
> <ul id="reports">
>   <li class="report" id="r1">报告 1</li>
>   <li class="report" id="r2">报告 2</li>
>   <li class="report" id="r3">报告 3</li>
> </ul>
> ~~~
>
> ~~~javascript
> const list = document.querySelector("#reports");
> const liveRows = list.children;
> const queriedRows = list.querySelectorAll(":scope > .report");
>
> for (let i = 0; i < liveRows.length; i += 1) {
>   liveRows[i].remove();
> }
> // 起初 r1、r2、r3；循环结束后 r2 仍在列表中。
> // queriedRows 仍有 3 个成员，但 queriedRows[0].isConnected 为 false。
> ~~~
>
> 若在这份原始列表上先复制成员，循环处理的就是固定顺序 `[r1, r2, r3]`，删除树节点不会改变待遍历数组。`querySelectorAll()` 的静态列表也仍有三个成员，但其中已移除节点的 `isConnected` 会变成 `false`：静态只固定列表成员，不冻结节点对象。以下是与上面错误循环二选一的写法，应从同一份初始列表开始。
>
> ~~~javascript
> for (const row of Array.from(liveRows)) row.remove();
> ~~~

实时集合适合反映 DOM 的当前成员，但不适合一边按递增索引遍历、一边改变成员；也可从后往前删。静态快照则适合一次查询后按成员执行任务。查询何时更新、节点本身是否仍连接到文档，是两个不同问题。实时描述的是可观察的成员结果，不承诺浏览器内部怎样、多久计算一次。

**延伸阅读：** [JavaScript 事件总线在监听器中重入时怎样保持顺序？](./event-bus-and-observer-patterns.md) 说明状态更新如何触发本地模块；[用户离开报表页时，分析事件怎样尽力发送？](../performance/analytics-event-delivery-on-navigation.md) 说明导航期间的遥测边界；[浏览器如何从输入到绘制界面？](../browser/browser-basics.md) 讨论 DOM 与后续渲染。

> [!info]- 来源
> - `NodeList`、`HTMLCollection` 的集合定义与 live/static 成员规则：[WHATWG DOM Standard，Old-style collections](https://dom.spec.whatwg.org/#old-style-collections-node-list-and-htmlcollection)，2026-11-06 核对。
> - `querySelectorAll()` 返回静态 `NodeList`，由其 API 规范定义：[WHATWG DOM Standard，ParentNode](https://dom.spec.whatwg.org/#dom-parentnode-queryselectorall)，2026-11-06 核对。
