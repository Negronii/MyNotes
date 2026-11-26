# 用一个新 API 之前，怎样确认运行时真的支持？

开发机上的浏览器能跑某个新方法，不代表用户的浏览器、App 里的 WebView 或线上的 Node.js 进程也能跑。一项 API 能否直接用，要回答四个问题：它进入了哪一版规范？目标运行时从哪个版本起实现了它？构建工具补的是语法还是 API？实际发布的产物在目标环境里能否跑通？本章以 `Object.groupBy` 为例把这四个问题接成一条检查链，并说明转译、polyfill、运行时探测、TypeScript 的 `target` / `lib` 和 Vite 的构建目标各自管什么。

本章是主线三的支线。沿用主线一的报表页，行数据已经通过[外部数据的三步验证](./typescript-guarantees-and-runtime-validation.md)，现在要按状态把行分组。

## 规范版次能说明运行时支持吗？

不能。ECMAScript 的每一版（edition）规定语言和内建对象的标准行为，但它不是浏览器、Node.js 或 WebView 的发布计划。

`Object.groupBy` 被纳入 ECMAScript 2024。各浏览器却按自己的节奏实现：Chrome 117（2023-09）、Firefox 119（2023-10）和 Safari 17.4（2024-03）的发布说明分别记录了它，三者都**早于** ECMA-262 2024 在 2024-06-26 获批。所以“规范年份”和“运行时从哪个版本起可用”要分开核对，不能从版次推出引擎的最低版本。

| 运行环境 | 怎样核对 | 能得出的结论 |
| --- | --- | --- |
| Chrome | Chrome 117 发布说明列出该方法 | Chrome 117 起已实现；不能据此推断嵌入式 WebView 跟随同版 Chrome，或所有设备都能升级到该版 |
| Firefox | Firefox 119 发布说明 | Firefox 119 起已实现；项目仍要对照自己支持的版本 |
| Safari / WebKit | Safari 17.4 发布说明 | Safari 17.4 起已实现；不能从 Chrome 版本推断 Safari |
| Node.js | 在目标进程运行 `node -p 'process.version + " " + typeof Object.groupBy'` | 原稿实测 Node 20.15.1 返回 `undefined`，22.22.3 与 26.13.0 返回 `function`；这几个点不构成所有发行版的最低支持承诺 |

下表列出各版次的代表性 API，用来判断一项能力属于哪一年的规范。再强调一次：年份只回答“何时进入标准”，不回答“目标运行时何时实现”。

| 版次 | 代表 API 与要点 |
| --- | --- |
| ES5 | `Object.keys` 只返回自有、可枚举的字符串键，不含 `Symbol` 键 |
| ES2015 | `Object.assign` 修改传入的目标对象；`Object.is` 使用 SameValue 规则；`Array.from` 接收可迭代或类数组，`Array.of` 由各实参组成数组；`Promise.all`、`Promise.race` |
| ES2017 | `Object.values`、`Object.entries` 选取自有、可枚举的字符串键 |
| ES2020 | `Promise.allSettled` 在所有输入结算后返回各项状态；`globalThis` 是当前 realm 的全局 `this` 值，浏览器窗口中是 `WindowProxy`，Node.js 中是 Node 的全局对象 |
| ES2021 | `Promise.any` 在任一输入兑现时兑现，全部拒绝才以 `AggregateError` 拒绝 |
| ES2022 | `Array.prototype.at` 接受负索引；`Object.hasOwn` 检查自有属性 |
| ES2024 | `Object.groupBy` 按属性键分组，`Map.groupBy` 按 Map 键分组；`Promise.withResolvers` 一次拿到 Promise 和它的控制函数 |
| ES2025 | `Set` 的并、交、差、对称差与包含、不相交判断；`RegExp.escape` 转义要拼进正则的字面文本 |

这些 API 的语义各有权威章节：相等规则见[JavaScript 的值有哪些类型，“相等”又有几种？](./values-types-and-equality.md)，属性枚举见[读写一个属性时，JavaScript 沿什么规则查找、落在哪里？](./objects-properties-and-prototypes.md)，`Set` 运算见[数组、Map、Set 和普通对象怎样选，空位和去重有哪些坑？](./arrays-maps-and-sets.md)，Promise 组合器见[Promise 和 async 函数怎样传递值和失败？](./promises-and-async-functions.md)。

表里没有 `structuredClone`，因为它是浏览器、Node.js 等宿主提供的 API，不属于任何 ECMAScript 版次，要按宿主自身的版本核对；它复制什么、拒绝什么，见[复制一个对象到底复制了什么？](./copying-and-object-graphs.md)。

## 先弄清 Object.groupBy 做什么

核对支持之前，先确认要用的行为。沿用报表页的 May（r-104）和 April（r-103）两行，再补一行合成的 March（r-102），让一个分组里有两行。代码按状态分组，记录回调被调用的顺序，并在分组之后改掉第一行的标题，观察分组结果是否复制了行对象：

```typescript
type ReportRow = {
  id: string;
  month: string;
  status: "open" | "published";
  title: string;
};

const rows: ReportRow[] = [
  { id: "r-104", month: "2026-05", status: "open", title: "May" },
  { id: "r-103", month: "2026-04", status: "published", title: "April" },
  { id: "r-102", month: "2026-03", status: "open", title: "March" },
];

const callbackVisits: Array<[string, number]> = [];
const groups = Object.groupBy(rows, (row, index) => {
  callbackVisits.push([row.id, index]);
  return row.status;
});
rows[0].title = "May corrected";

console.log(JSON.stringify({
  openIds: (groups.open ?? []).map(row => row.id),
  publishedIds: (groups.published ?? []).map(row => row.id),
  callbackVisits,
  hasOpenGroup: Object.hasOwn(groups, "open"),
  sameRowReference: groups.open?.[0] === rows[0],
  titleThroughGroup: groups.open?.[0]?.title,
  nullPrototype: Object.getPrototypeOf(groups) === null,
}, null, 2));
```

输出：

```json
{
  "openIds": ["r-104", "r-102"],
  "publishedIds": ["r-103"],
  "callbackVisits": [["r-104", 0], ["r-103", 1], ["r-102", 2]],
  "hasOpenGroup": true,
  "sameRowReference": true,
  "titleThroughGroup": "May corrected",
  "nullPrototype": true
}
```

从输出读出五条行为：

- **同步逐项调用。** 方法同步遍历可迭代对象，对每一项调用回调，第二个参数是从 0 开始的序号。本例依次访问 `open`、`published`、`open`。
- **组名是属性键。** 回调的返回值被转换成属性键。
- **不复制行对象。** 方法新建了分组对象和各组数组，数组里放的是原始行的引用。改掉 `rows[0].title` 后，从 `groups.open[0]` 读到的也是新值。
- **结果没有原型。** 分组对象不继承 `Object.prototype`，不能调用 `groups.hasOwnProperty(...)`，要用 `Object.hasOwn(groups, "open")`。注意 `Object.hasOwn` 本身来自 ES2022，同样需要核对目标运行时。
- **某组可能不存在。** TypeScript 把返回类型声明为 `Partial<Record<K, T[]>>`：`status` 的类型虽然包含 `"open"`，某次输入也可能一行 `open` 都没有，所以 `groups.open` 可能是 `undefined`，`?? []` 不是多余的。`callbackVisits` 标注元组数组类型，是为了避免严格模式下空数组被推断成隐式 `any[]`。

如果组名本身是对象、需要按对象身份区分，用 `Map.groupBy`：它返回 `Map`，组名不经过属性键转换，用 `map.get(key)` 取组。两种方法都同步遍历，都放原始引用。

### 异步输入和异步回调

两个方法都是同步的，遇到异步来源要先处理：

- 上游给的是 `Promise<ReportRow[]>` 时，先 `await` 得到数组，再分组。直接把 Promise 传进去会抛 `TypeError`，因为 Promise 不可迭代。
- 只支持异步迭代的来源（例如异步生成器）没有同步迭代接口，同样抛 `TypeError`。应先用 `for await...of` 收集，或边取边分组；异步迭代见[迭代器和生成器怎样按需产出值，提前退出时怎样清理？](./iterators-and-generators.md)。
- 回调写成 `async row => row.status` 时，返回值是 Promise，被转成属性键 `"[object Promise]"`，三行全落进同一组，而且不报错。

## 转译、polyfill 和运行时探测各补什么？

知道目标运行时可能缺少 `Object.groupBy` 后，要分清三种手段各补哪一块：

| 手段 | 补什么 | 补不了什么 |
| --- | --- | --- |
| transpiler（转译器） | 旧引擎读不懂的**语法**，例如把箭头函数改写成普通函数 | 通常不会往运行时里补上缺失的内建 API |
| polyfill（兼容补丁） | 缺失的**内建 API**，在运行时把实现装上 | 新语法；解析失败时补丁代码根本执行不到 |
| 运行时探测，如 `typeof Object.groupBy === "function"` | 在代码成功解析后，为缺失的 API 走另一条分支 | 同上，文件里有旧引擎解析不了的语法时，整个文件在解析阶段就失败 |

所以顺序是：先用转译保证每个文件在目标引擎上能解析，再用 polyfill 或探测处理缺失的 API。

下面是只覆盖本例需求的窄回退（fallback）：输入只能是已验证的行数组，组名只能是字符串状态。原生方法存在时直接调用；缺失时创建无原型的分组对象，放入原始行的引用。

```typescript
function groupRowsByStatus(rows: ReportRow[]) {
  if (typeof Object.groupBy === "function") {
    return Object.groupBy(rows, row => row.status);
  }

  const groups: Partial<Record<ReportRow["status"], ReportRow[]>> =
    Object.create(null);
  for (const row of rows) {
    let bucket = groups[row.status];
    if (bucket === undefined) {
      bucket = [];
      groups[row.status] = bucket;
    }
    bucket.push(row);
  }
  return groups;
}

const fallbackGroups = groupRowsByStatus(rows);
console.log(JSON.stringify({
  open: (fallbackGroups.open ?? []).map(row => row.id),
  published: (fallbackGroups.published ?? []).map(row => row.id),
}));
// {"open":["r-104","r-102"],"published":["r-103"]}
```

要在缺少原生 API 的环境里试验，只保留类型定义、`rows` 和这段函数，不要带上上一节直接调用 `Object.groupBy` 的代码，否则程序会在那里中止。两条分支都应输出同样的分组；验证时检查实际分组内容，而不只是确认没有抛错。

这段回退不是完整的规范 polyfill：原生方法还接受其他同步可迭代值，回调键也可以是 `Symbol`。应用依赖这些行为时，应选用经过测试、实现完整契约的补丁，而不是把小回退扩展后就当它等价。

## tsconfig 的 target 和 lib 管什么？

TypeScript 配置里有两个选项和“目标环境”有关，它们都只作用于编译期：

- `target` 决定 `tsc` 输出 JavaScript 时把哪些**语法**降级。
- `lib` 决定类型检查器认为哪些标准库 **API 存在**。

下面的配置只做类型检查、不输出文件（`noEmit: true`），演示语法目标仍为 ES2022 时，怎样让类型检查器认识 `Object.groupBy`：

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2024", "DOM", "DOM.Iterable"],
    "strict": true,
    "noEmit": true
  }
}
```

用这份配置运行 `tsc --noEmit`，类型检查能通过，但旧浏览器里仍然没有这个方法。同样，往 `lib` 里加 `"DOM"` 或更高的 ES 版本，也不会让 Node.js 凭空拥有浏览器对象或新 API。`lib` 是对运行时的**声明**，不是**保证**。

可用的 `target` / `lib` 名称取决于安装的 TypeScript 版本。`ESNext` 的含义随 TypeScript 版本变化，需要固定部署目标时不应使用。

> [!info] 版本说明：es2026
> 截至 2026-11-17，`es2026` 这个 target / lib 名称由 2026-10-20 发布的 TypeScript 7.1 Beta 加入，Beta 仍是预发布版。

## 实例：Vite 的构建目标与 legacy 插件

> [!info] 版本范围
> 本节按 Vite 8.3 与 `@vitejs/plugin-legacy` 8.2.4 的文档整理，核对日期 2026-11-13。开发服务器和生产构建的整体差异、构建五阶段见[构建器怎样把源码变成可部署的文件？](../delivery/build-pipeline-and-bundling.md)，这里只看与 API 可用性有关的部分。

Vite 8 开发时用 Oxc 转译源文件，`oxc.target` 默认 `esnext`，几乎不做语法降级；生产构建 `vite build` 另走一条路径生成 bundle。开发页面能跑，不代表发布产物也能。

**默认目标不覆盖 `Object.groupBy`。** Vite 8 生产构建的默认目标是 `baseline-widely-available`，即按每个 Vite 大版本固定日期（Vite 8 为 2026-01-01）计算的 Baseline Widely Available：Chrome / Edge 111、Firefox 114、Safari / iOS 16.4。而 `Object.groupBy` 要到 Chrome 117、Firefox 119、Safari 17.4 才有。满足 Vite 默认最低版本的浏览器，不一定有这个原生方法。

**几个“目标”选项各管一条路径：**

| 选项 | 处理哪条路径 | 决定什么 |
| --- | --- | --- |
| Vite `build.target` | 未启用 legacy 插件时的主生产 bundle | 语法转换目标；不补齐缺少的内建 API。构建时优先于 `oxc.target`，也不读 `tsconfig.json` 的 `target` |
| 插件的 `targets` | 插件生成的 legacy 分块 | 这些旧语法分块的转换目标；不会给现代分块加入同一组 API 补丁 |
| 插件的 `modernPolyfills` | 现代 JavaScript 路径 | 另生成现代补丁分块；默认 `false`，显式写数组可选择需要的补丁 |
| 插件的 `modernTargets` | 现代分块的语法目标，以及自动收集现代补丁时的检测目标 | 插件 8.2.4 会在客户端构建中覆盖 `build.target`，未设置时用插件自己的现代默认值；`modernPolyfills: true` 才按目标自动探测，显式列表直接选模块 |

插件 8.2.4 在页面里检测 ESM、动态导入、async generator 和 `import.meta.resolve` 等现代能力：全部通过的浏览器加载现代分块，否则加载旧分块（所以有些支持 ESM 的浏览器也会走旧分块）。问题在于，通过检测不代表浏览器有 `Object.groupBy`。`modernPolyfills` 保持默认的 `false` 时，现代路径仍可能在调用处失败。要覆盖这条路径，就显式选择 core-js 的对象分组补丁：

```javascript
import legacy from "@vitejs/plugin-legacy";

export default {
  plugins: [
    legacy({
      modernPolyfills: ["es.object.group-by"],
    }),
  ],
};
```

DOM 和其他宿主 API 需要另选对应的补丁。

> [!example] 故障注入：哪份产物能在缺少 API 的浏览器里跑通
> 原稿在 Chrome 157 中加载真实的 Vite 8.3.8 生产产物，在模块执行前删除 `Object.groupBy`，人为制造“支持 ESM、但缺少该 API”的浏览器：
>
> | 生产产物 | 删除 API 后执行的路径 | 结果 |
> | --- | --- | --- |
> | 普通 `vite build` | 主现代模块分块 | 报 `Object.groupBy is not a function` |
> | 加 legacy 插件 8.2.4，`modernPolyfills` 保持 `false` | 仍是主现代模块分块 | 同样报错；旧语法分块没有修复这条路径 |
> | 再设 `modernPolyfills: ["es.object.group-by"]` | 先加载现代补丁分块，再加载应用分块 | 得到 `open` 与 `published` 两组 |
>
> 这项实验只模拟了“支持 ESM、缺少该内建 API”这一个条件，没有在 Chrome 111、Safari 16.4 或任何厂商的 WebView 上运行，不能替代目标设备上的验收。

所以浏览器端有两种选择：提高最低支持版本；或继续支持旧环境，提供与业务需求相符的局部回退或兼容补丁。两种做法都要在实际运行时检查分组结果。

## Node.js 端怎样确认？

服务端按服务实际启动的 Node 版本核对，浏览器的 `build.target` 与服务器内建 API 无关。

`package.json` 的 `engines.node` 可以声明兼容范围，但 npm 默认只把它当提示（除非启用 `engine-strict`）；它不会替部署平台选择 Node 版本，也不能证明进程里有某个 API。CI 应该用部署所选的 Node 版本实际启动代码，并运行同一个探针。

## 把检查串成一条链

对一个新 API，按这个顺序确认：

1. 查规范，确认要用的行为（同步还是异步、是否复制、结果有没有原型）。
2. 查每个目标运行时的发行记录，或在目标进程里运行探针；不从规范年份推断。
3. 确认构建管线只转换语法：Vite 用 Oxc 转译 TypeScript 时只去掉类型、不做类型检查，需要类型诊断时另跑 `tsc --noEmit`；而类型检查本身也证明不了运行时支持。
4. 缺失的 API 用局部回退或完整 polyfill 补上，并确认补丁真的进了会执行的那份产物。
5. 用声明支持的浏览器 / WebView 运行前端发布产物，用部署所选的 Node.js 版本启动服务入口，检查实际结果。

这条链的终点是构建产物在目标环境里的行为。产物怎样生成、怎样在发布前验证，由[构建器怎样把源码变成可部署的文件？](../delivery/build-pipeline-and-bundling.md)接着讲。

> [!info]- 来源
> - **规范版次与 `groupBy` 行为**（“规范版次能说明运行时支持吗”“先弄清 Object.groupBy 做什么”）：[ECMA-262 2024 §20.1.2.13 `Object.groupBy`](https://tc39.es/ecma262/2024/multipage/fundamental-objects.html#sec-object.groupby)（逐项调用回调、迭代索引、属性键转换、无原型结果）；[§24.1.2.1 `Map.groupBy`](https://tc39.es/ecma262/2024/multipage/keyed-collections.html#sec-map.groupby)（结果为 Map，回调值作 Map 键）。ECMA-262 2024 于 2024-06-26 获批：[Ecma International 公告](https://ecma-international.org/news/ecma-international-approves-new-standards-9/)；[ECMA-262 2026](https://tc39.es/ecma262/2026/) 于 2026-06-30 获批，为最新版次。
> - **`globalThis`**（版次表 ES2020 行）：[ECMA-262 2026 §19.1.1](https://tc39.es/ecma262/2026/multipage/global-object.html#sec-globalthis)；HTML Standard [Window 对象](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-window-object)（指向 `WindowProxy`）；Node.js [`globalThis`](https://nodejs.org/api/globals.html#global)。
> - **浏览器发行版**（运行环境表）：[New in Chrome 117](https://developer.chrome.com/blog/new-in-chrome-117)；[Firefox 119 for developers](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/119)；[WebKit Features in Safari 17.4](https://webkit.org/blog/15063/webkit-features-in-safari-17-4/)（`Object.groupBy` 与 `Map.groupBy`）。
> - **TypeScript `target` / `lib`**（“tsconfig 的 target 和 lib 管什么”、`Partial<Record<K, T[]>>`）：TSConfig [target](https://www.typescriptlang.org/tsconfig/target.html)、[lib](https://www.typescriptlang.org/tsconfig/lib.html)；[`lib.es2024.object.d.ts`（v7.0.2）](https://github.com/microsoft/TypeScript/blob/v7.0.2/src/lib/es2024.object.d.ts)；[Announcing TypeScript 7.1 Beta](https://devblogs.microsoft.com/typescript/announcing-typescript-7-1-beta/)（2026-10-20，加入 `es2026`）。
> - **Vite 8.3 与 legacy 插件 8.2.4**（实例节与故障注入）：[Vite TypeScript 转译](https://vite.dev/guide/features.html#typescript)、[生产浏览器兼容目标](https://vite.dev/guide/build.html#browser-compatibility)、[`build.target`](https://vite.dev/config/build-options#build-target)；[plugin-legacy 8.2.4 README](https://www.npmjs.com/package/@vitejs/plugin-legacy/v/8.2.4)（`targets`、`modernTargets`、`modernPolyfills`）、[polyfill specifiers](https://github.com/vitejs/vite/blob/main/packages/plugin-legacy/README.md#polyfill-specifiers)。故障注入为原稿以 Vite 8.3.8 / 插件 8.2.4 构建、Chrome 157 实跑。
> - **`engines` 字段**（“Node.js 端怎样确认”）：npm 11 [package.json `engines`](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/#engines)。
> - **`structuredClone` 属于宿主**：[HTML Standard: structured cloning](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning)；[Node.js structuredClone](https://nodejs.org/api/globals.html#structuredclonevalue-options)。
>
> 浏览器发行说明、ECMAScript 版次、TypeScript 类型、Vite 与插件选项按 2026-11-13 核验。Node 20.15.1、22.22.3 与 26.13.0 的探针是原稿实跑记录。本章改用 r-104 / r-103 / r-102 数据后，`groupBy` 输出、异步输入与异步回调的三条行为在 Node.js v26.13.1 上重新运行确认。
