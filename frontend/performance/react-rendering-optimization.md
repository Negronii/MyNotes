# 如何测量并减少不必要的React工作？

**案例背景。** 报表页当前 URL 为 `/reports?sort=recent#summary`，服务端给 May、April 两行；选择 **Oldest first** 后，`sort=oldest` 让可见顺序变成 April、May。打开说明面板不改变报表数据；若这个按钮仍让大量行再次执行组件函数，可能有可优化的 React 工作；若主要时间发生在提交后的布局和绘制，memoization（记忆化）不会修复浏览器瓶颈。排序的 URL 与 Back 恢复由[浏览器历史栈机制](../browser/browser-navigation-and-history.md#让筛选状态跟随地址栏与前进后退)负责，本章代码聚焦面板更新与 React 成本测量。

~~~mermaid
flowchart TD
    A[重放实际交互] --> B{时间花在哪里？}
    B --> C[组件计算或列表变换]
    B --> D[提交DOM变化]
    B --> E[浏览器布局与绘制]
    C --> F[缩小状态影响范围或测量后缓存]
    D --> G[检查改变的节点和列表规模]
    E --> H[回到浏览器性能与CSS测量]
    F --> I[用同一交互复测]
    G --> I
    H --> I
~~~

## 先分清render和DOM变化

React 的 render（渲染）是组件计算下一份元素描述；render 可能没有产生任何 DOM 改动，但仍消耗 JavaScript 时间。React commit 才应用必要宿主变化；浏览器之后可能布局、绘制或合成。React DevTools Profiler（React 开发者工具性能面板）适合观察一次交互中哪些组件参与提交、render 耗时怎样变化；React 的 `<Profiler>` API 则可在指定子树中程序化记录这些时长。浏览器 Performance 面板用于看主线程脚本、样式、布局和绘制。围绕同一交互、同一数据和目标设备记录基线，再比较修改后的结果。

例如，若打开说明面板时 Profiler 显示每个 `ReportRow` 都计算了一遍，但行 props 和结果都未变，可以检查状态范围和组件边界；若 React 时间很短而布局成本明显，继续看[浏览器渲染测量](./performance-metrics-and-analysis.md)或[长列表](./rendering-and-computation-optimization.md)。单看 render 次数或控制台日志不能证明用户感知性能已经变好。

## React Compiler改变手工memo的默认做法

React Compiler（React 编译器）v1.0 已稳定，React 官方当前文档为 React 19.3。Compiler 是可选的构建期优化，启用后通常会自动缓存组件和 Hook 中可安全复用的工作，新代码一般不必先手写一层 `memo`、`useMemo`、`useCallback`。它是否覆盖某个文件取决于项目构建配置和可编译代码；不会把任意普通工具函数变成跨组件共享缓存。

未启用 Compiler 或需要明确边界时，这些 API 才由工程师手工使用：`memo` 可在 props 按 `Object.is` 比较相同的情况下跳过子组件更新；`useMemo` 缓存一次 render 中的计算值；`useCallback` 缓存函数引用。组件自身 state、所读 Context 等更新仍能触发 render。不要把缓存用于正确性、资源生命周期或语义身份；React 可在文档列出的情况下丢弃 `useMemo` 缓存。

下面只用本地 `reviewed` 状态演示对象身份如何影响更新；真实服务端保存采用[查询与乐观更新章节](../frameworks/react-server-state-and-optimistic-updates.md)的写入流程。

~~~jsx
import { memo, useCallback, useMemo, useState } from "react";

function ReportBoard({ initialReports }) {
  const [reports, setReports] = useState(initialReports);
  const [query, setQuery] = useState("");
  const [helpOpen, setHelpOpen] = useState(false);

  const visible = useMemo(
    () => reports.filter(report => report.title.includes(query)),
    [reports, query]
  );
  const toggleReviewed = useCallback(id => {
    setReports(current => current.map(report =>
      report.id === id ? { ...report, reviewed: !report.reviewed } : report
    ));
  }, []);

  return (
    <>
      <input value={query} onChange={event => setQuery(event.target.value)} />
      <button type="button" onClick={() => setHelpOpen(open => !open)}>
        {helpOpen ? "隐藏说明" : "显示说明"}
      </button>
      {helpOpen && <p>说明面板</p>}
      <ul>
        {visible.map(report => (
          <ReportRow key={report.id} report={report} onToggle={toggleReviewed} />
        ))}
      </ul>
    </>
  );
}

const ReportRow = memo(function ReportRow({ report, onToggle }) {
  return (
    <li>
      {report.title}
      <button type="button" onClick={() => onToggle(report.id)}>
        {report.reviewed ? "已读" : "标为已读"}
      </button>
    </li>
  );
});
~~~

这里假设 `reports` 以不可变方式更新，只创建发生变化的那一行对象。切换 `helpOpen` 时，`reports` 与 `query` 没变，`visible` 可复用；既有行对象和 `toggleReviewed` 引用也相同，于是未启用 Compiler 时 `memo` 可以跳过这些行。输入变动时过滤仍要重新计算；如果那次工作本身才是瓶颈，缓存身份不会减少算法扫描数据的成本。

## 用结果决定优化是否值得保留

为同一交互记录组件耗时、commit 数量、脚本和浏览器布局成本。检查 Compiler 的编译覆盖后，再比较它自动优化与手工 memoization 的收益；若手工缓存增加依赖复杂度却没有缩短交互，就删掉这层复杂度。稳定 key 用来保留行身份，不是性能 API；组件状态的范围则优先按所有权整理，见[如何组合组件与复用行为？](../frameworks/react-component-composition.md)。

用 CSS 隐藏已挂载面板时，它仍留在 React 树中，state 和 Effect 继续存在；条件移除会卸载组件并执行 cleanup，再显示时会创建新实例。二者应按生命周期和交互需求选择。Fragment 可免去多余 DOM 包装节点，但这本身不构成可测的性能结论。

> [!info]- 来源与版本核验（React 19.3；Compiler v1.0；2026-11-06）
> - React 文档当前版本及 Compiler 稳定状态：[Versions](https://react.dev/versions)、[React Compiler Introduction](https://react.dev/learn/react-compiler/introduction)，核验日期 2026-11-06；Compiler v1.0 于 2025-10-07 发布。
> - 编译器的自动缓存范围、建议先 profile、以及手工 memoization 的当前角色：[React Compiler Introduction](https://react.dev/learn/react-compiler/introduction)，React 19.3 文档。
> - `memo` 的比较、state/Context 更新和 Compiler 行为：[memo](https://react.dev/reference/react/memo)；计算值与函数引用：[useMemo](https://react.dev/reference/react/useMemo)、[useCallback](https://react.dev/reference/react/useCallback)，React 19.3 文档。
> - React DevTools 的 Profiler 面板：[React Developer Tools](https://react.dev/learn/react-developer-tools)，React 19.3 文档；指定子树的程序化性能分析：[Profiler](https://react.dev/reference/react/Profiler)，React 19.3 文档。浏览器阶段见[Performance Metrics and Analysis](./performance-metrics-and-analysis.md)。
