# Lodash 何时适合处理报表列表，哪些方法会修改输入？

**案例背景。** 用户在 `/reports?sort=recent#summary` 看到 May、April 两份报表；切换到 oldest 后，完整顺序由服务端变成 April、May。这里用同一数据观察 Lodash 4.18.1 的三个常见行为：排序如何返回新数组、合并如何改变已有对象，以及延迟搜索调用时怎样保留正确的参数。完整远端排序归服务端是本例的选择；组件若拥有完整本地数据，也可以在本地排序。

## 排序逻辑应跟着数据来源走

这里约定服务端决定远端报表的完整顺序，返回值已经按 `recent` 或 `oldest` 排好；这是本例的数据归属选择，不是每个应用都必须服务端排序。若组件已经拥有完整的相关数据集，本地排序也成立。下面刻意切到只有 May、April 的本地数组，沿用同一数据来单独观察 Lodash 的返回值和对象身份；它不是上面那条远端查询路径。`_.orderBy` 按指定字段和方向返回新数组，不会改动传入的 recent 数组：

~~~javascript
const recent = [
  { id: "may", period: "May", month: "2026-05" },
  { id: "april", period: "April", month: "2026-04" }
];

const oldest = _.orderBy(recent, ["month"], ["asc"]);

oldest.map(report => report.period); // ["April", "May"]
recent.map(report => report.period); // ["May", "April"]
oldest[0] === recent[1]; // true：新数组仍共享 April 行对象
~~~

`_.sortBy` 同样返回新数组，按升序排列；要写清升降序或多个字段时用 `_.orderBy`。新数组只是行引用的新顺序，`oldest[0]` 仍是 `recent[1]` 那个 April 对象；改行对象会同时改到两边。若本例确实需要完整数据在组件内排序，就不要再让另一份排序状态和 URL 互相覆盖；而已经由路由 loader 返回顺序的数据，不需要再走这段本地转换。

## 深合并为什么会改到已有报表数据

`_.merge(target, ...sources)` 会递归合并并修改第一个参数，然后返回这个目标对象。数组按索引合并，不会拼接：

~~~javascript
const cached = {
  reports: [
    { id: "may", period: "May", owner: { team: "Ops" } },
    { id: "april", period: "April" }
  ]
};
const patch = {
  reports: [{ owner: { reviewed: true } }]
};

const changed = _.merge(cached, patch);
changed === cached; // true
cached.reports[0].owner.reviewed; // true
cached.reports.length; // 2，patch 的第 0 项合并进原第 0 项
~~~

把同一个引用传回 React state，可能因引用没变而跳过渲染；若 `cached` 还被请求缓存、其他组件或测试共享，也会一起看到被改的值。要建立新值，可以把新对象作为目标：

~~~javascript
const next = _.merge({}, cached, { reports: [{ owner: { reviewed: false } }] });
next !== cached; // true
next.reports !== cached.reports; // true：reports 数组也重新建立
next.reports[0].owner !== cached.reports[0].owner; // true：嵌套 owner 也重新建立
next.reports[0].id; // "may"：数组仍按索引合并
next.reports[0].owner.reviewed; // false
cached.reports[0].owner.reviewed; // true：原对象未被这次合并改写
next.reports.length; // 2
~~~

此例把数组中的对象也合并到新目标，因此 `reports` 与嵌套 `owner` 是新对象，原 `cached` 保持 `reviewed: true`。但它仍不会让数组按 ID 匹配；合并按索引进行。纯列表补项应显式拼接，例如 `[...cached.reports, newReport]`。`_.assign` 也会修改目标，只做浅层赋值。用库方法前，先看它返回哪个对象以及是否改变输入。

同一个 `patch.reports[0]` 会随当前排序改到不同报表：

| 正在合并的顺序 | 第 0 行 | 补丁结果落到 |
|---|---|---|
| recent：May、April | May | May 的 `owner.reviewed` |
| oldest：April、May | April | April 的 `owner.reviewed` |

如果补丁实际针对某个 `report.id`，先按 ID 找到那一行再更新，别把“第 0 行”当成报表身份。

需要写入嵌套路径时，`_.set` 也会原地修改目标：

~~~javascript
const draft = {};
const result = _.set(draft, "owner.team", "Ops");
result === draft; // true
draft.owner.team; // "Ops"
~~~

## 深路径默认值要区分缺失与 null

`_.get` 只在路径结果为 `undefined` 时采用默认值；如果接口明确返回 `null`，结果仍是 `null`：

~~~javascript
const missingOwner = { owner: {} };
const emptyOwner = { owner: { name: null } };

_.get(missingOwner, "owner.name", "Unknown"); // "Unknown"
_.get(emptyOwner, "owner.name", "Unknown");   // null
const name = emptyOwner.owner?.name;
name === undefined ? "Unknown" : name;         // null，保留接口明确返回的 null
name ?? "Unknown";                            // "Unknown"，null 也触发这个回退
~~~

当报表确实允许“没有负责人”和“负责人字段未返回”表达不同状态时，这个差异会改变空态文案。字段路径固定时，原生可选链和显式回退值通常更直接；只有业务也把 `null` 当成缺失时，才用 `??` 统一回退。

## 其他方法先看返回值和边界

| 方法 | 对界面数据的实际契约 |
|---|---|
| `_.concat(array, ...values)` | 返回浅拼接的新数组；把传入数组展开一层，数组里再嵌套的数组保持嵌套。 |
| `_.drop(array, n = 1)` | 返回去掉前 `n` 项后的新切片。 |
| `_.find(collection, predicate, fromIndex = 0)` | 返回第一条匹配项；数组可从 `fromIndex` 开始，不会返回全部匹配行。 |
| `_.each(collection, iteratee)` | 遍历后返回原集合；`_.forEach` 是别名，不适合当作变换后的新列表。 |
| `_.keys(object)` | 普通对象返回自有、可枚举的字符串键，不含 Symbol（符号）键；稀疏数组会把空位也列为数字索引，例如 `_.keys([, "April"])` 是 `["0", "1"]`，而 `Object.keys` 只给 `["1"]`。 |
| `_.uniq(array)` | 返回保留首次出现顺序的新数组；若只需原生值集合，Set（集合）可能更清楚。 |
| `_.compact(array)` | 移除输入数组中的所有假值，包括 `0`、`false` 和空字符串；清理指标值数组时会删掉可能合法的 `0`。报表行对象即使字段值为 `0` 仍是真值，不会因该字段被过滤。 |
| `_.times(n, iteratee)` | 调用迭代器 `n` 次并返回结果数组。 |

`_.uniqueId(prefix)` 只使用当前 Lodash 模块实例的递增计数器；结果受先前调用影响，不保证跨进程或多份模块全局唯一，也不是安全令牌。列表行优先用服务端稳定的 `report.id`；认证能力令牌应使用具备相应安全契约的生成器。

## 搜索输入可以延迟，排序导航不应延迟

搜索可以等待用户暂停输入，排序导航则应立即交给路由器。本例用 React Router v8.5.1 Data Mode（数据模式）：父级 loader（路由数据加载函数）从本次请求的 `request.url` 读取并校验目标 `sort`，读取完整列表后返回 `{ sort, reports }`。搜索 Hook（React 自定义钩子）只消费已经提交的 loader 数据中的 `sort`。Uniform Resource Locator（统一资源定位符，URL）保存排序，本地 `query` 保存搜索词；同一个搜索面板在查询参数导航中保持挂载，因此搜索词可跨排序保留。

先分清“导航目标”和“当前显示的数据”。点击 **Oldest first** 发起 PUSH（新增历史项）后，目标 loader 已收到 oldest，但等待期间浏览器地址、历史当前项、`useLocation()`、`useLoaderData()` 和列表仍属于 recent；`useNavigation().location` 才是等待中的 oldest。成功后，地址和 April、May 列表一起提交。Back / Forward 触发 POP（历史遍历）时，浏览器地址先变，已提交路由和列表暂留原值，等 loader 成功才换。这里采用默认的查询参数重验证，没有自定义 `shouldRevalidate` 跳过 sort 变化；完整导航时序见[React 路由怎样把地址映射到界面并加载数据？](../frameworks/react-routing-and-navigation.md)。

下图只比较 loader 成功返回后的两个已提交状态，等待阶段仍按上面的规则处理：

~~~mermaid
flowchart LR
    Recent["loader 成功后的已提交状态<br/>sort=recent<br/>May、April"]
    Oldest["loader 成功后的已提交状态<br/>sort=oldest<br/>April、May"]
    Recent -->|Oldest first，PUSH 成功| Oldest
    Oldest -->|Back，POP 成功| Recent
~~~

`_.debounce` 实现 debounce（防抖）：默认等最后一次调用后静默一段时间，再处理仍待执行的最后一次输入。`leading`（首沿）、`trailing`（尾沿）和 `maxWait`（最大等待时间）会改变触发时机。本例等待 300ms，同时设置 `maxWait: 1000`，避免一直输入就永远不发搜索。

同一面板必须持续复用同一个 debounce 实例。每次输入更新参数和请求代次，不能在每次 `query` 变化时取消这个实例，否则 `maxWait` 也会被重置。只有清空输入、排序成功提交或组件卸载才取消旧计时器；请求代次同时让过时响应失效。

> [!example] maxWait 已处理的输入，不会被尾沿重复发送
> 假设第一次输入发生在 0ms，之后每隔 120ms 输入一次，依次为 `Ops 0`、`Ops 1`……。下表是计时到期顺序；真实事件循环可能推迟执行，不保证精准到毫秒。
>
> | 输入情况 | 1000ms 的 maxWait | 停止输入之后 |
> |---|---|---|
> | 共 9 次，最后一次在 960ms | 处理最后一词 `Ops 8` | 再静默 400ms 也不新增调用，因为没有待处理输入。 |
> | 共 12 次，最后一次在 1320ms | 先处理当时最新的 `Ops 8` | 后来又输入了新词，1620ms 的尾沿处理 `Ops 11`。 |
>
> 尾沿会处理最后一次输入，前提是它仍待执行，且下一次 maxWait 尚未先处理它。

把它接回报表页面，数据依次变化：

1. recent 的基础列表是 May、April。输入 `Ops` 后，计时器调用 `fetchReports({ sort: "recent", query: "Ops" })`；合成服务返回 `[May Ops, April Ops]`。只有请求代次及 `(committedSort, query)` 仍有效，结果才替代基础列表。
2. 点击 oldest 后立即导航。PUSH 等待期间，搜索仍属于当前 recent 页面。loader 成功提交 oldest 后，Hook 保留 `Ops`；Effect 清理旧计时器、使旧 recent 请求失效，再排入 `(oldest, Ops)`。等待搜索时先显示基础 April、May，得到当前结果后显示 `[April Ops, May Ops]`。
3. Back / Forward 也以成功提交的 sort 驱动重查，不能只观察排序按钮点击或地址栏。点击已提交的当前排序是空操作，不取消当前搜索，也不重复导航。

query 改变或 sort 提交后先清空旧结果。页面用 `searchResults ?? loaderReports` 选择当前搜索结果或基础列表，错误也按同一对 `(committedSort, query)` 匹配。

`_.debounce.cancel()` 只撤销尚未执行的调用，不中止已发出的网络请求；请求代次负责阻止旧响应写回当前界面。若还要停止浏览器传输，由调用方创建 `AbortController`，把 `controller.signal` 交给使用 `fetch` 的请求函数，并在排序提交或卸载时调用 `controller.abort()`。该请求函数需要接收并使用 signal。

> [!example]- React Hook 实现：复用计时器、按已提交排序重查、拒绝过时响应
>
> ~~~javascript
> import { useEffect, useRef, useState } from "react";
> import _ from "lodash";
> import { fetchReports } from "./report-api";
>
> function useReportSearch(committedSort, navigate) {
>   const [query, setQuery] = useState("");
>   const queryRef = useRef("");
>   const [searchResult, setSearchResult] = useState(null);
>   const [searchFailure, setSearchFailure] = useState(null);
>   const [searching, setSearching] = useState(false);
>   const requestGenerationRef = useRef(0);
>   const scheduleRef = useRef(null);
>   if (scheduleRef.current === null) {
>     scheduleRef.current = _.debounce(
>       async (queryAtInput, sortAtInput, generation) => {
>         try {
>           const reports = await fetchReports({ sort: sortAtInput, query: queryAtInput });
>           if (generation === requestGenerationRef.current) {
>             setSearchResult({ sort: sortAtInput, query: queryAtInput, reports });
>           }
>         } catch (error) {
>           if (generation === requestGenerationRef.current) {
>             setSearchFailure({ sort: sortAtInput, query: queryAtInput, error });
>           }
>         } finally {
>           if (generation === requestGenerationRef.current) setSearching(false);
>         }
>       },
>       300,
>       { trailing: true, maxWait: 1000 }
>     );
>   }
>   const scheduleReportSearch = scheduleRef.current;
>
>   useEffect(() => {
>     const generation = ++requestGenerationRef.current;
>     const latestQuery = queryRef.current;
>     setSearchResult(null);
>     setSearchFailure(null);
>     setSearching(Boolean(latestQuery));
>     if (latestQuery) scheduleReportSearch(latestQuery, committedSort, generation);
>     return () => {
>       requestGenerationRef.current += 1;
>       scheduleReportSearch.cancel();
>     };
>   }, [scheduleReportSearch, committedSort]);
>
>   function onSearchInput(nextQuery) {
>     queryRef.current = nextQuery;
>     setQuery(nextQuery);
>     setSearchResult(null);
>     setSearchFailure(null);
>     const generation = ++requestGenerationRef.current;
>     if (!nextQuery) {
>       scheduleReportSearch.cancel();
>       setSearching(false);
>       return;
>     }
>     setSearching(true);
>     scheduleReportSearch(nextQuery, committedSort, generation);
>   }
>
>   function onSortNavigation(nextSort) {
>     if (nextSort === committedSort) return; // 当前排序不再导航，也不取消当前搜索
>     navigate(`/reports?sort=${encodeURIComponent(nextSort)}#summary`); // 立即发起导航
>   }
>
>   const currentSearchResult =
>     searchResult?.sort === committedSort && searchResult?.query === query ? searchResult.reports : null;
>   const currentSearchError =
>     searchFailure?.sort === committedSort && searchFailure?.query === query ? searchFailure.error : null;
>
>   return {
>     query,
>     searchResults: currentSearchResult,
>     searchError: currentSearchError,
>     searching,
>     onSearchInput,
>     onSortNavigation
>   };
> }
> ~~~

同时开启首沿 `leading` 和尾沿 `trailing` 时，尾沿只在等待窗口内发生多次调用后才会再执行；若调用方需要立即提交尚待执行的尾部输入，可用 `.flush()`：

~~~javascript
const search = _.debounce(fetchReports, 300, { leading: true, trailing: true });
search({ sort: "recent", query: "O" });
search({ sort: "recent", query: "Ops" }); // 窗口内第二次调用，结束时会执行 trailing
search.flush(); // 若 trailing 尚待执行，现在就执行
~~~

Lodash 的 throttle（节流）方法 `_.throttle` 则限制调用频率，适合按固定间隔响应滚动或连续事件，不等同于 debounce。若要理解这两种计时包装函数怎样用闭包保存 timer、最新参数和触发时刻，见[原生闭包如何实现定时防抖与首沿节流？](../javascript/scope-and-closure.md#定时回调怎样用闭包保留调度状态)。

## 何时优先用原生操作

路径明确时，原生可选链、`Array.prototype.flat`（数组扁平化）、Set 或对象展开常常更易读。需要 Lodash 的边界行为时，先核对版本和输入形状，再决定是否使用。按方法导入可以帮助构建器裁剪依赖，但最终包体还受模块格式和构建配置影响；要用生产产物测量，不能只凭写法推断体积。

相关内容见[现代 JavaScript 特性](../javascript/modern-javascript-features.md)与[前端性能测量](../performance/performance-metrics-and-analysis.md)。

> [!info]- 来源与版本核验（Lodash 4.18.1、React Router 8.5.1；当前稳定版于 2026-11-12 核验）
> - 当前稳定版本及 4.18.1 发布记录：[Lodash 4.18.1 release](https://github.com/lodash/lodash/releases/latest)，发布于 2026-04-01；latest 在 2026-11-12 仍指向 4.18.1。
> - 排序、深合并、数组按索引合并、对象路径、集合和计时方法：[Lodash 4.18.1 API 文档](https://github.com/lodash/lodash/blob/4.18.1/doc/README.md)；[`_.debounce` 的 maxWait 与 cancel 说明](https://github.com/lodash/lodash/blob/4.18.1/doc/README.md#_debouncefunc-wait0-options)、[稀疏数组键枚举实现](https://github.com/lodash/lodash/blob/4.18.1/lodash.js#L2430)；本轮使用对应官方 4.18.1 source 执行例子。
> - React [`useRef`](https://react.dev/reference/react/useRef) 与 [`useEffect`](https://react.dev/reference/react/useEffect) 用于计时器和排序提交后的清理。React Router v8.5.1 Data Mode 的 [Data Loading](https://reactrouter.com/8.5.1/start/data/data-loading)、[Navigating](https://reactrouter.com/8.5.1/start/data/navigating)、[Pending UI](https://reactrouter.com/8.5.1/start/data/pending-ui) 与[默认 loader 重验证条件](https://reactrouter.com/8.5.1/start/data/route-object#shouldrevalidate)；浏览器 POP 地址变化依据 [HTML Standard 历史条目应用算法](https://html.spec.whatwg.org/multipage/browsing-the-web.html#update-document-for-history-step-application)。核验日期 2026-11-12。
> - 浏览器请求取消由 [AbortController.abort()](https://developer.mozilla.org/en-US/docs/Web/API/AbortController/abort) 触发，并由 [Fetch 使用 AbortSignal](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#canceling_a_request) 支持；取消请求的代码归发起请求的客户端。
> - 原生数组展平与空值运算符：[Array.prototype.flat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/flat)、[Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing)，原有核验日期 2026-11-06。
