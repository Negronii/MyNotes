# Lodash 何时适合处理报表列表，哪些方法会修改输入？

**案例背景。** 用户在 `/reports?sort=recent#summary` 看到 May、April 两份报表。Uniform Resource Locator（统一资源定位符，URL）中的 `sort=recent` 让服务端返回 May、April；点击 **Oldest first** 后，地址的 `sort` 变为 `oldest`，服务端返回 April、May；按 Back 回到 recent 和 May、April。地址和请求属于路由层；Lodash 只转换已经交给它的数据，不拥有排序状态，也不会替代服务端查询。

~~~mermaid
flowchart LR
    A[URL sort=recent] --> B[服务端返回 May、April]
    B --> C[组件显示列表]
    C --> D[Oldest first 开始路由导航]
    D --> E[loader 读取 oldest 并返回数据]
    E --> F[结算后提交 oldest URL 与 April、May]
    F --> Back[Back 恢复 recent URL 并重跑路由数据]
    B -.本地拥有副本时才选此分支.-> G[本地列表]
    G --> H[orderBy 返回新数组]
    G --> I[merge 按索引原地合并]
~~~

## 排序逻辑应跟着数据来源走

真实应用让 `sort` 查询参数决定服务端顺序；同一列表不要再由组件状态保存一份排序，也不要在收到已经排好序的服务端结果后重复排序。若数据确实由当前组件本地排序，`_.orderBy` 会按指定字段和方向返回一个新数组，不会改动传入的 recent 数组：

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

`_.sortBy` 同样返回新数组，按升序排列；要写清升降序或多个字段时用 `_.orderBy`。新数组只是行引用的新顺序，`oldest[0]` 仍是 `recent[1]` 那个 April 对象；改行对象会同时改到两边。图中的分支表示组件确实拥有一份本地数据时才做本地转换，不表示服务端排序页还要二次排序。生产路由仍从 URL 发出排序请求，避免两套逻辑相互覆盖。

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
~~~

这个写法只改变目标引用，不会让数组按 ID 匹配；数组仍按索引合并。纯列表补项应显式拼接，例如 `[...cached.reports, newReport]`。`_.assign` 也会修改目标，只做浅层赋值。用库方法前，先看它返回哪个对象以及是否改变输入。

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
emptyOwner.owner?.name ?? "Unknown";          // "Unknown"
~~~

当报表确实允许“没有负责人”和“负责人字段未返回”表达不同状态时，这个差异会改变空态文案。字段路径固定时，原生可选链和显式回退值通常更直接。

## 其他方法先看返回值和边界

| 方法 | 对界面数据的实际契约 |
|---|---|
| `_.concat(array, ...values)` | 返回浅拼接的新数组；把传入数组展开一层，数组里再嵌套的数组保持嵌套。 |
| `_.drop(array, n = 1)` | 返回去掉前 `n` 项后的新切片。 |
| `_.find(collection, predicate, fromIndex = 0)` | 只找第一项；数组可从 `fromIndex` 开始，不会返回全部匹配行。 |
| `_.each(collection, iteratee)` | 遍历后返回原集合；`_.forEach` 是别名，不适合当作变换后的新列表。 |
| `_.keys(object)` | 返回对象自有、可枚举的字符串键，不含 Symbol（符号）键。 |
| `_.uniq(array)` | 返回保留首次出现顺序的新数组；若只需原生值集合，Set（集合）可能更清楚。 |
| `_.compact(array)` | 移除所有假值，包括 `0`、`false` 和空字符串；报表字段可能合法为 `0` 时不能用它清洗行。 |
| `_.times(n, iteratee)` | 调用迭代器 `n` 次并返回结果数组。 |

`_.uniqueId(prefix)` 只使用当前 Lodash 模块实例的递增计数器；结果受先前调用影响，不保证跨进程或多份模块全局唯一，也不是安全令牌。列表行优先用服务端稳定的 `report.id`；认证能力令牌应使用具备相应安全契约的生成器。

## 搜索输入可以延迟，排序导航不应延迟

Lodash 的 debounce（防抖）方法 `_.debounce` 会等最后一次调用后的等待时间过去再执行；`leading`、`trailing` 和 `maxWait` 会改变它何时运行。用它减少报表标题搜索的请求频率时，保留当前 URL 的 `sort`，并在组件卸载或输入控件销毁时取消尚未触发的调用：

~~~javascript
const scheduleReportSearch = _.debounce(
  (query, sort) => fetchReports({ sort, query }),
  300,
  { trailing: true, maxWait: 1000 }
);

function onSearchInput(query, currentUrlSort) {
  scheduleReportSearch(query, currentUrlSort);
}

function onSortNavigation(navigate) {
  scheduleReportSearch.cancel(); // 丢弃尚未开始的旧排序搜索
  navigate("/reports?sort=oldest#summary"); // 立即开始路由导航
}

function onSearchPanelUnmount() {
  scheduleReportSearch.cancel();
}
~~~

防抖函数要在一段组件生命周期内复用；排序处理器取消待发的搜索，再立即把导航交给路由。React Router Data Mode 会先加载目标数据，地址和历史项在结算时提交；这里的 `navigate` 只表示开始导航，不表示地址在点击瞬间提交。Back 则由浏览器选回 recent 历史项并触发路由加载。`cancel` 只撤销尚未触发的调用，不会中止已经发出的网络请求；真正停止传输需要请求服务配合 AbortSignal（请求取消信号）。

这段处理器只覆盖显式点击与卸载。Back/Forward 不会经过 `onSortNavigation`：若 oldest 下的搜索计时器尚未触发，Back 已提交 recent 后，它仍可能带着捕获的 oldest 发请求。接入真实路由时，应在每次已提交的 sort 改变时同样取消旧待发搜索，并用请求代次或查询键保护结果；已经启动的旧请求即便无法取消，也不能覆盖新条件下的列表。

同时开启 leading 和 trailing 时，trailing 只在等待窗口内发生多次调用后才会再执行；若调用方需要立即提交尚待执行的尾部输入，可用 `.flush()`：

~~~javascript
const search = _.debounce(fetchReports, 300, { leading: true, trailing: true });
search({ query: "O" });
search({ query: "Ops" }); // 窗口内第二次调用，结束时会执行 trailing
search.flush(); // 若 trailing 尚待执行，现在就执行
~~~

Lodash 的 throttle（节流）方法 `_.throttle` 则限制调用频率，适合按固定间隔响应滚动或连续事件，不等同于 debounce。若要理解这两种计时包装函数怎样用闭包保存 timer、最新参数和触发时刻，见[原生闭包如何实现定时防抖与首沿节流？](../javascript/scope-and-closure.md#定时回调怎样用闭包保留调度状态)。

## 何时优先用原生操作

路径明确时，原生可选链、`Array.prototype.flat`（数组扁平化）、Set 或对象展开常常更易读。需要 Lodash 的边界行为时，先核对版本和输入形状，再决定是否使用。按方法导入可以帮助构建器裁剪依赖，但最终包体还受模块格式和构建配置影响；要用生产产物测量，不能只凭写法推断体积。

相关内容见[现代 JavaScript 特性](../javascript/modern-javascript-features.md)与[前端性能测量](../performance/performance-metrics-and-analysis.md)。

> [!info]- 来源与版本核验（Lodash 4.18.1；2026-11-06）
> - 当前稳定版本及 4.18.1 发布记录：[Lodash Releases](https://github.com/lodash/lodash/releases)，2026-04-01。
> - 排序、深合并、数组按索引合并、对象路径、字符串、集合和计时方法：[Lodash 4.18.1 API 文档](https://github.com/lodash/lodash/blob/4.18.1/doc/README.md)。
> - 原生数组展平与空值运算符：[Array.prototype.flat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/flat)、[Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing)，核验日期 2026-11-06。
