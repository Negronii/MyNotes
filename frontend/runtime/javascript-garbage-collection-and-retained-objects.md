# JavaScript 对象为何会在不再有用后仍留在内存中？

用户关闭报表后，如果旧结果还被全局事件处理器、计时器闭包或缓存引用，垃圾回收器仍能从程序根沿引用链找到它们。判断“业务上已过期”并不能让对象自动回收；需要断开不再需要的强引用。本章从报表监听器的保留路径解释原因，再给出诊断步骤。弱引用的语言保证见[弱集合与弱引用能保证什么？](../javascript/javascript-memory-weakmap-and-weakset.md)。

## 可达性是保留问题，不是对象之间是否成环

JavaScript 语言不规定某一种垃圾回收算法，也不承诺某个不可达对象何时被回收。以追踪式回收器为例，它从全局对象、活动执行状态等运行时根出发，沿强引用标记对象；循环引用本身不妨碍回收，仍可从根到达的对象则需要保留。V8 的 Orinoco 是一个具体实现，使用分代、并行、增量和并发工作；这些实现细节会变化，不构成 JavaScript 语言保证。这个模型帮助理解保留路径，但具体算法与时机由引擎决定。

下面的打开函数在报表打开期间创建 `rows`。若关闭报表时漏掉监听器清理，`window` 仍持有处理器，处理器闭包又持有 `rows` 和嵌套记录：

~~~javascript
function openReport(target) {
  const owner = { id: "u-17", name: "Ada" };
  const first = { reportId: "r-104", amount: 0, owner };
  const rows = [first];

  function render(currentRows) {
    console.log(currentRows.map(row => `${row.reportId}:${row.owner.name}`).join(", "));
  }

  function onResize() {
    render(rows);
  }

  target.addEventListener("resize", onResize);
  return () => target.removeEventListener("resize", onResize);
}

let releaseReport = openReport(window);
// 关闭报表时既移除监听器，也放弃持有清理闭包：
releaseReport();
releaseReport = null;
~~~

~~~mermaid
flowchart LR
  Window[window 根] --> Listener[resize 监听器]
  Listener --> Resize[onResize 闭包]
  Runtime[执行环境根] --> Handle[releaseReport 绑定]
  Handle --> Cleanup[清理闭包]
  Cleanup --> Resize
  Resize --> Rows[rows 数组]
  Rows --> Row[报表记录对象]
  Row --> Owner[嵌套 owner 对象]
~~~

图中记录已经不在当前界面，却仍沿 `window` → Listener → `onResize` → rows → Row 可达；`releaseReport` 绑定还经清理闭包指向同一个 `onResize`。调用清理函数只移除 `window` 的监听器路径，随后还要放弃持有清理闭包的绑定；其他引用仍需由各自所有者解除。

常见保留路径还包括：

- timeout、interval、订阅或未结束任务仍持有回调；回调闭包保留旧报表。
- 应用级 Map 缓存未删除条目，强持有键及关联值。
- 脱离 DOM 树且仍能从根到达的节点仍会被保留；仅有节点和自身监听器之间的引用环不足以证明泄漏。
- 调试器控制台、断点或堆分析工具暂时保留对象。

这些只是检查线索，必须沿实际对象的保留链确认，不能只凭“用了闭包”或“数组很大”就认定泄漏。

## 用重复操作和堆快照定位所有者

在浏览器中固定一组操作，例如打开报表、切换筛选、关闭报表，再重复数次。分别记录操作前后的 heap snapshot（堆快照），用比较视图查找反复留下的对象，再检查选中对象的 retainers（保留者）和到根的路径。

若路径来自 `window` 上的监听器，应由注册监听器的报表生命周期调用 `removeEventListener`；若来自应用缓存，则由缓存所有者删除条目；若来自定时器，创建它的生命周期应在关闭时调用 `clearInterval` 或 `clearTimeout`。清理点要与资源的真实所有权一致，而不是把 `FinalizationRegistry`（最终化注册表）当成释放按钮。

Chrome DevTools 堆快照可以显示对象到根的保留者，比较视图可检查打开再关闭是否持续留下对象。Node.js 也能生成 V8 堆快照检查服务端对象；两种工具呈现的细节是运行时诊断能力，不是 ECMAScript 语义。

> [!info]- 来源
> - 追踪式回收、根集合和不可达对象的实现示例：[V8 “Trash talk: the Orinoco garbage collector”](https://v8.dev/blog/trash-talk)，2018-08-14；这是当时的 V8 实现说明，不代表当前所有引擎。
> - `WeakRef` 与 `FinalizationRegistry` 不保证回收和清理时机：[ECMAScript 2026 §9.9 Processing Model](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-weakref-processing-model)。
> - 比较堆快照、检查保留者和脱离 DOM 节点：[Chrome DevTools 官方指南 “Record heap snapshots”](https://developer.chrome.com/docs/devtools/memory-problems/heap-snapshots)，访问于 2026-11-06。
