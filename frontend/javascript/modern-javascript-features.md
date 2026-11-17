# 怎样判断目标浏览器或 Node.js 是否支持一项 JavaScript 特性？

**案例背景。** 月报页面已经拿到通过结构校验的报表行数组 `ReportRow[]`，需要按状态把行分组。开发机上的 Chrome 能运行 `Object.groupBy`，但部署环境里还有旧版 WebView（嵌入在 App 中的浏览器组件），Node.js 服务也可能以不同主版本启动。能否直接使用这个方法，不能只看它属于哪一版 ECMAScript，还要回答四个问题：目标运行时从哪个版本起实现了它？构建工具是否只转换语法？缺失的运行时 API 是否另有补丁？实际发布的产物在目标环境里能否跑通？

本文用同一组三行月报数据，依次核对规范版本、分组结果中的对象引用、同步迭代与异步输入、TypeScript 类型声明和 Vite 生产构建目标，把它们接成一条可复现的判断链。更一般的对象属性、数组复制、Promise 和模块加载机制分别见[JavaScript 值如何转换、比较，并成为属性键？](./javascript-types.md)、[JavaScript 数组操作如何处理空位、修改与复制？](./arrays.md)、[回调、Promise 与 async 函数怎样组合异步工作？](./asynchronous-javascript.md)和[ECMAScript 模块与 CommonJS 在语法、加载和运行时有什么不同？](./modules-and-host-boundaries.md)。

## ECMAScript 版本能告诉我们什么？

ECMAScript 的每一版（edition）规定语言和内建对象的标准行为，但它不是浏览器、Node.js 或 WebView 的发布计划。`Object.groupBy` 被纳入 2024 年版规范，而各浏览器按自己的节奏实现：Chrome 117（2023-09）、Firefox 119（2023-10）和 Safari 17.4（2024-03）的发布说明分别记录了它，三者都早于 ECMA-262 2024 在 2024-06-26 获批。可见“规范年份”和“运行时从哪个版本起可用”必须分开核对，不能从版次推出引擎的最低支持版本。

| 运行环境 | 可核对的发行记录或运行时探针 | 能得出的结论 |
| --- | --- | --- |
| Chrome | Chrome 117 发布说明列出该方法 | 厂商记录 Chrome 117 已实现；不能据此推断嵌入式 WebView 跟随同版 Chrome，或所有设备都可升级到该版 |
| Firefox | Firefox 119 发布说明列出该方法 | 厂商记录 Firefox 119 已实现；项目仍须核对自己支持的运行版本 |
| Safari / WebKit | Safari 17.4 发布说明列出该方法 | 厂商记录 Safari 17.4 已实现；不能从 Chrome 版本推断 Safari 版本 |
| Node.js | 在目标 Node 进程运行 `node -p 'process.version + " " + typeof Object.groupBy'` | 这次探针在 Node 20.15.1 返回 `undefined`，在 22.22.3 与 26.13.0 返回 `function`；这些实测点不构成所有发行版的最低支持承诺 |

下面是本文的合成输入。`id`、`period` 和 `status` 已在数据进入页面时校验过。代码按状态分组，记录回调被调用的顺序，并在分组后修改第一行的标题，用来观察分组结果是否复制了行对象：

~~~typescript
type ReportRow = {
  id: string;
  period: string;
  status: "open" | "published";
  title: string;
};

const rows: ReportRow[] = [
  {
    id: "r-101", period: "2026-05",
    status: "open", title: "May report",
  },
  {
    id: "r-102", period: "2026-04",
    status: "published", title: "April report",
  },
  {
    id: "r-103", period: "2026-03",
    status: "open", title: "March report",
  },
];

const callbackVisits: Array<[string, number]> = [];
const groups = Object.groupBy(rows, (row, index) => {
  callbackVisits.push([row.id, index]);
  return row.status;
});
rows[0].title = "May corrected";

const result = {
  openIds: (groups.open ?? []).map(row => row.id),
  publishedIds: (groups.published ?? []).map(row => row.id),
  callbackVisits,
  hasOpenGroup: Object.hasOwn(groups, "open"),
  sameRowReference: groups.open?.[0] === rows[0],
  titleThroughGroup: groups.open?.[0]?.title,
  nullPrototype: Object.getPrototypeOf(groups) === null,
};
console.log(JSON.stringify(result, null, 2));
~~~

`Object.groupBy` 同步遍历可迭代对象，对每一项调用回调，第二个参数是从 `0` 开始的序号；回调的返回值会被转换成属性键，作为组名。本例依次访问 `open`、`published`、`open` 三行，输出为：

~~~json
{
  "openIds": ["r-101", "r-103"],
  "publishedIds": ["r-102"],
  "callbackVisits": [["r-101", 0], ["r-102", 1], ["r-103", 2]],
  "hasOpenGroup": true,
  "sameRowReference": true,
  "titleThroughGroup": "May corrected",
  "nullPrototype": true
}
~~~

方法新建了分组对象和各组数组，但没有复制行对象：`rows[0].title` 改成 `"May corrected"` 后，通过 `groups.open?.[0]?.title` 读到的也是新值。返回的分组对象没有原型，不继承 `Object.prototype`，所以不能调用 `groups.hasOwnProperty(...)`；检查某组是否存在要用 `Object.hasOwn(groups, "open")`，本例结果为 `true`。注意 `Object.hasOwn` 本身来自 ES2022，同样属于需要核对目标运行时的 API。

代码用 TypeScript 显式写出了行和回调记录的类型。TypeScript 把 `Object.groupBy` 的返回类型声明为 `Partial<Record<K, T[]>>`：即使 `status` 的类型包含 `"open"`，某次输入也可能一行 `open` 都没有，所以 `groups.open` 和 `groups.published` 都可能是 `undefined`。`?? []` 让“没有这一组”时得到空数组，并不是多余的类型绕行。`callbackVisits` 标注元组数组类型，则是为了避免严格模式下空数组被推断为隐式 `any[]`。

`Object.groupBy` 把回调结果转成属性键，适合本例这种字符串状态。如果组名本身是对象，需要按对象身份区分，就用 `Map.groupBy`：它返回 `Map`，组名不经过属性键转换，之后用 `map.get(key)` 取出对应的组。两种方法都同步遍历输入，并把原始行的引用放进分组数组。

下表列出各版次的代表性特性，便于判断一项能力属于哪一年的规范。年份只回答“何时进入标准”，不回答“目标运行时何时实现”：

| ECMAScript 版次 | 代表特性与边界 |
| --- | --- |
| ES5 | `Object.keys` 只返回自有、可枚举的字符串键，不返回 `Symbol` 键 |
| ES2015 | `Object.assign` 修改传入的目标对象；`Object.is` 使用 SameValue（同值）规则；`Array.from` 接收可迭代或类数组输入，`Array.of` 由各实参组成数组；Promise 的 `all`、`race` 结算语义见异步章节 |
| ES2017 | `Object.values` 和 `Object.entries` 选取自有、可枚举的字符串键 |
| ES2020 | `Promise.allSettled` 在所有输入都结算后返回各项状态；`globalThis` 是当前 realm（执行环境）的全局 `this` 值：在浏览器窗口中是 `WindowProxy`，在 Node.js 中是 Node 的全局对象 |
| ES2021 | `Promise.any` 在任一输入兑现时兑现，只有全部输入都拒绝时才以 `AggregateError` 拒绝 |
| ES2022 | `Array.prototype.at` 接受负索引；`Object.hasOwn` 检查自有属性 |
| ES2024 | `Object.groupBy` 按属性键分组，`Map.groupBy` 按 Map 键分组；`Promise.withResolvers` 创建 Promise 和它的控制函数 |
| ES2025 | `Set` 的并、交、差、对称差与包含/不相交判断；`RegExp.escape` 转义拼入正则表达式的字面文本 |

表里没有 `structuredClone`（结构化克隆），因为它是浏览器、Node.js 等宿主提供的 API，不属于任何 ECMAScript 版次。它能复制支持的 `Date`、`Map`、`Set` 等值，也保留循环引用和共享引用；函数不能克隆，自定义类原型不会保留，不支持的值会抛出结构化克隆错误（`DataCloneError`）。需要为月报编辑器隔离嵌套快照时，具体复制范围和代价见[如何安全地深拷贝 JavaScript 值？](./deep-copy-and-structured-clone.md)；不要假设结构化克隆一定比其他做法快。

## 语法转换、类型声明和 polyfill 有什么差别？

知道目标运行时可能缺少 `Object.groupBy` 后，下一步是弄清三种工具各自能补什么。transpiler（转译器）解决的是旧引擎读不懂新语法的问题，例如把箭头函数改写成普通函数；它通常不会往运行时里补上缺失的 `Object.groupBy`。`typeof Object.groupBy` 这类运行时检查，可以在代码成功解析后为缺失的 API 走另一条分支；但如果文件里有旧引擎无法解析的语法，整个文件在解析阶段就失败了，执行不到检查处，所以必须先做语法转换。

下面是只覆盖本例需求的窄回退（fallback）：输入只能是已校验的行数组，组名只能是字符串状态。原生方法存在时直接调用；缺失时创建无原型的分组对象，把原始行的引用放进对应数组。

~~~typescript
function groupRowsByStatus(rows: ReportRow[]) {
  if (typeof Object.groupBy === "function") {
    return Object.groupBy(rows, row => row.status);
  }

  const groups: Partial<
    Record<ReportRow["status"], ReportRow[]>
  > = Object.create(null);
  for (const row of rows) {
    const status = row.status;
    let bucket = groups[status];
    if (bucket === undefined) {
      bucket = [];
      groups[status] = bucket;
    }
    bucket.push(row);
  }
  return groups;
}

const fallbackGroups = groupRowsByStatus(rows);
const fallbackIds = {
  open: (fallbackGroups.open ?? []).map(row => row.id),
  published: (fallbackGroups.published ?? []).map(row => row.id),
};
console.log(JSON.stringify(fallbackIds));
~~~

要在缺少原生 API 的环境中试验，只保留前面的类型定义和 `rows` 输入，再运行这段兼容函数；不要带上前面直接调用 `Object.groupBy` 的代码，否则程序会在那里报错中止。原生方法存在时走原生分支，缺失时走回退分支，两条分支都输出 `{ open: ["r-101", "r-103"], published: ["r-102"] }`。验证时应像这样检查实际分组内容，而不只是确认函数没有抛错。

这段回退只复现本例所需的数组输入和字符串组名，不是完整的规范 polyfill（兼容补丁）：原生方法也接受其他同步可迭代值，回调键还可以是 `Symbol`。若应用依赖这些行为，应选用经过测试、实现完整契约的补丁，而不是扩展这个小回退后就称其等价。

还要区分同步遍历与异步到达的数据。若上游给的是 `Promise<ReportRow[]>`，先在 `async` 函数中 `await` 得到数组，再调用 `groupRowsByStatus`，分组本身仍同步逐项进行。`Object.groupBy` 不会等待 Promise，也不能直接消费只支持异步迭代的来源（如异步生成器）：这类输入没有同步迭代接口，会抛 `TypeError`，应先用 `for await...of` 收集，或在取数时边取边分组。回调也必须是同步的：写成 `async row => row.status` 时回调返回的是 Promise，它会被转成属性键 `"[object Promise]"`，三行都落进同一组。异步组合器和取消边界见[回调、Promise 与 async 函数怎样组合异步工作？](./asynchronous-javascript.md)。

TypeScript 配置中的 `target` 和 `lib` 同样不能代替运行时检测。`target` 决定 `tsc` 输出 JavaScript 时把哪些语法降级；`lib` 决定类型检查器认为哪些标准库 API 存在。下面的配置带有 `noEmit: true`，只做类型检查、不输出文件；它演示语法目标仍为 ES2022 时，如何让类型检查器认识 `Object.groupBy`：

~~~json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2024", "DOM", "DOM.Iterable"],
    "strict": true,
    "noEmit": true
  }
}
~~~

用这个配置对前面的示例运行 `tsc --noEmit`，类型检查能通过，但旧浏览器里仍然没有这个方法。同理，在 `lib` 里加入 `"DOM"`、`"ES2024"` 或更高版本的声明，也不会让 Node.js 凭空拥有浏览器对象或新 API。可用的 `target` / `lib` 名称还取决于安装的 TypeScript 版本：截至 2026-11-17，`es2026` 由 2026-10-20 发布的 TypeScript 7.1 Beta 加入，而 Beta 仍是预发布版；`ESNext` 的含义随 TypeScript 版本变化，需要固定部署目标时不应使用它。

## Vite 的开发与生产目标分别由什么控制？

类型检查之外，前端还要看构建工具产出了什么。Vite 8.3 的开发服务器按需向浏览器提供原生 ECMAScript modules（ECMAScript 模块，ESM），并用 Oxc 转译源文件；开发时 `oxc.target` 默认为 `esnext`，几乎不做语法降级。生产环境的 `vite build` 则生成最终的 bundle（打包产物）。开发和生产是两条不同的路径，开发页面能运行，不代表发布产物也能。

Vite 8 生产构建的默认目标是 `baseline-widely-available`，即按每个 Vite 大版本固定日期（Vite 8 为 2026-01-01）计算的 Baseline Widely Available（广泛可用基线）：Chrome / Edge 111、Firefox 114、Safari / iOS 16.4。而 `Object.groupBy` 要到 Chrome 117、Firefox 119、Safari 17.4 才可用。因此，满足 Vite 默认最低版本的浏览器不一定有这个原生方法。

Vite 和它的 legacy 插件里，有几个选项都与“目标浏览器”有关，但各自处理不同的产物：

| 选项 | 处理哪条路径 | 它决定什么 |
| --- | --- | --- |
| Vite `build.target` | 未启用 legacy 插件的主生产 JavaScript bundle | 控制语法转换目标；普通 Vite 不补齐缺少的内建 API |
| `@vitejs/plugin-legacy` 的 `targets` | 插件生成的 legacy chunks | 这些旧语法分块的转换目标；不会因此给现代模块分块加入同一组 API 补丁 |
| 插件的 `modernPolyfills` | 现代 JavaScript 路径 | 另生成现代补丁分块；默认是 `false`，显式指定数组可选择需要的补丁 |
| 插件的 `modernTargets` | 现代分块的语法目标，以及自动收集现代补丁时的检测目标 | 插件 8.2.4 会在客户端构建中覆盖 `build.target`；未显式设置时也使用插件自己的现代默认值。`modernPolyfills: true` 才按目标自动探测，显式补丁列表直接选择模块 |

例如，要让加载现代模块分块的浏览器在缺少该方法时也能运行，可显式选择 core-js 的对象分组补丁：

~~~javascript
import legacy from "@vitejs/plugin-legacy";

export default {
  plugins: [
    legacy({
      modernPolyfills: ["es.object.group-by"],
    }),
  ],
};
~~~

普通 `vite build` 不会自动装入这个补丁，只启用 legacy 分块也不够。插件 8.2.4 在页面里检测 ESM、动态导入、async generator 和 `import.meta.resolve` 等现代能力，全部通过的浏览器加载现代分块，否则加载旧分块（因此有些支持 ESM 的浏览器也会走旧分块）。问题在于：通过检测不代表浏览器有 `Object.groupBy`。若 `modernPolyfills` 保持默认的 `false`，现代路径仍可能在调用它时失败；只有显式指定的补丁被装入页面，现代路径才被覆盖。DOM 和其他宿主 API 需要另选对应的补丁。

未启用 legacy 插件时，Vite 生产构建用 `build.target` 决定语法输出目标，而不读取 `tsconfig.json` 的 `target`；构建时 `build.target` 优先于 `oxc.target`。无论目标写得多低，语法转换都不会让缺失的 `Object.groupBy` 出现。

所以对浏览器端有两种选择：提高最低支持版本；或继续支持旧环境，并提供与业务需求相符的局部回退或兼容补丁。两种做法都要在实际运行时检查分组结果。Node.js 端则按服务实际启动的 Node 版本核对，浏览器的 `build.target` 与服务器内建 API 无关。`package.json` 的 `engines.node` 可以声明兼容范围，但 npm 默认只把它当提示（除非启用 `engine-strict`）；它不会替部署平台选择 Node 版本，也不能证明进程里有某个 API。CI 应该用部署所选的 Node 版本实际启动代码，并运行同一个探针。

为验证上述说法，下面在 Chrome 157 中加载真实的 Vite 生产产物，并在模块执行前删除 `Object.groupBy`，人为制造“支持 ESM、但缺少该 API”的浏览器，观察实际执行哪份产物、能否得到两组结果：

| 生产产物 | 清除 API 后执行的路径 | 结果 |
| --- | --- | --- |
| 普通 Vite 8.3.8 `vite build` | 主现代模块分块 | 报 `Object.groupBy is not a function` |
| Vite 8.3.8 + legacy 插件 8.2.4，保留默认 `modernPolyfills: false` | 插件仍加载主现代模块分块 | 同样报错；插件生成旧语法分块并未修复这条路径 |
| 上项再设 `modernPolyfills: ["es.object.group-by"]` | 页面先加载现代补丁分块，再加载应用分块 | 得到 `open: ["r-101", "r-103"]` 和 `published: ["r-102"]` |

这项故障注入只模拟了“支持 ESM、但缺少该内建 API”这一个条件，用来说明构建配置如何分支；它没有在 Chrome 111、Safari 16.4 或任何厂商的 WebView 上运行，不能替代在目标设备上的验收。

最后把检查顺序串起来。Vite 8 用 Oxc 转译 TypeScript 时只去掉类型、不做类型检查，而类型检查也证明不了运行时支持。因此需要类型诊断时另跑 `tsc --noEmit`；然后用声明支持的浏览器 / WebView 运行前端发布产物，用部署所选的 Node.js 版本启动服务入口，分别检查结果。`structuredClone` 等宿主 API 还要按宿主自身版本验证，不能由 ECMAScript 年份或 Vite 语法目标替代。

从源码到发布文件的构建步骤与部署检查见[构建工具怎样把源码变成可发布产物？](../tooling/build-tools.md)。

> [!info]- 来源
> - **规范版次与内建行为。** [ECMA-262 2024 §20.1.2.13 `Object.groupBy`](https://tc39.es/ecma262/2024/multipage/fundamental-objects.html#sec-object.groupby)规定逐项调用回调、迭代索引、属性键转换和无原型结果；[§24.1.2.1 `Map.groupBy`](https://tc39.es/ecma262/2024/multipage/keyed-collections.html#sec-map.groupby)规定结果为 `Map`，回调值作为 Map 键。ECMA-262 2024 于 2024-06-26 获批，见 [Ecma International 批准公告](https://ecma-international.org/news/ecma-international-approves-new-standards-9/)；[ECMA-262 2026](https://tc39.es/ecma262/2026/)是最新获批版次，Ecma International 于 2026-06-30 批准。
> - **全局对象。** [ECMA-262 2026 §19.1.1 `globalThis`](https://tc39.es/ecma262/2026/multipage/global-object.html#sec-globalthis)将初始值定义为当前 Realm 全局环境中的 `[[GlobalThisValue]]`；[HTML Standard 的 Window 环境](https://html.spec.whatwg.org/multipage/nav-history-apis.html#the-window-object)将其指向该浏览上下文的 `WindowProxy`。Node.js 的 [`globalThis`](https://nodejs.org/api/globals.html#global)指向 Node 全局对象。
> - **浏览器发行版。** [Chrome 117](https://developer.chrome.com/blog/new-in-chrome-117) 发布说明；[Firefox 119 开发者发布说明](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/119)；[WebKit Safari 17.4 发布说明](https://webkit.org/blog/15063/webkit-features-in-safari-17-4/)记录 Object.groupBy 与 Map.groupBy 的支持版本。
> - **TypeScript 7.0.2。** [target TSConfig](https://www.typescriptlang.org/tsconfig/target.html)控制 `tsc` 输出的语法降级；[lib TSConfig](https://www.typescriptlang.org/tsconfig/lib.html)提供内建 API 类型声明；[`lib.es2024.object.d.ts`](https://github.com/microsoft/TypeScript/blob/v7.0.2/src/lib/es2024.object.d.ts)把 `Object.groupBy` 返回类型声明为 `Partial<Record<K, T[]>>`；[TypeScript 7.1 Beta](https://devblogs.microsoft.com/typescript/announcing-typescript-7-1-beta/)发布于 2026-10-20，在该 Beta 中加入稳定的 `es2026` target / lib 名称。
> - **Vite 8.3 与 legacy 插件 8.2.4。** [Vite 的 TypeScript 转译](https://vite.dev/guide/features.html#typescript)与[生产浏览器目标](https://vite.dev/guide/build.html#browser-compatibility)；[legacy 插件 8.2.4 README](https://www.npmjs.com/package/@vitejs/plugin-legacy/v/8.2.4)中的 `targets`、`modernTargets`、`modernPolyfills` 和 [polyfill specifier](https://github.com/vitejs/vite/blob/main/packages/plugin-legacy/README.md#polyfill-specifiers)；[Vite `build.target`](https://vite.dev/config/build-options#build-target)。该例的三种产物以 Vite 8.3.8 / legacy 插件 8.2.4 构建并用 Chrome 157 实跑。
> - **Node.js 项目声明。** npm 11 [package.json 的 `engines` 字段](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/#engines)说明它默认只是提示，除非启用 `engine-strict`；真正要检查的是部署启动的进程。
> - **结构化克隆。** [HTML Standard：structured data](https://html.spec.whatwg.org/multipage/structured-data.html#structured-cloning)；[Node.js 26.13 structuredClone](https://nodejs.org/api/globals.html#structuredclonevalue-options)。
>
> 浏览器发行说明、ECMAScript 版次、TypeScript 类型、Vite 与插件选项按 2026-11-13 核验。Node 20.15.1、22.22.3 与 26.13.0 的探针是本次实跑记录，不据此推断其他补丁版本或 WebView。
