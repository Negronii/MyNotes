# 怎样判断目标浏览器或 Node.js 是否支持一项 JavaScript 特性？

**案例背景。** 月报页面已经拿到经过结构校验的 `ReportRow[]`，需要按状态把行分组。开发机上的 Chrome 能运行 `Object.groupBy`，但部署环境包含旧 WebView（嵌入式浏览器组件）；Node.js 服务也可能由不同主版本启动。要决定能否直接使用这项能力，不能只看它属于哪一版 ECMAScript：还要知道目标运行时何时实现、构建是否只转换语法、运行时 API 是否另有补丁，并在实际产物上检查。

本文沿同一组三行月报数据核对 `Object.groupBy`。它把规范版本、对象引用、同步迭代、异步输入、TypeScript 声明和 Vite 生产目标接成一条可复现的判断链。更一般的对象属性、数组复制、Promise 和模块加载机制仍由[JavaScript 值如何转换、比较，并成为属性键？](./javascript-types.md)、[JavaScript 数组操作如何处理空位、修改与复制？](./arrays.md)、[回调、Promise 与 async 函数怎样组合异步工作？](./asynchronous-javascript.md)和[ECMAScript 模块与 CommonJS 在语法、加载和运行时有什么不同？](./modules-and-host-boundaries.md)分别解释。

## ECMAScript 版本能告诉我们什么？

ECMAScript 版次（edition）定义语言和内建对象的标准行为；它不是浏览器、Node.js 或 WebView 的同步发布清单。`Object.groupBy` 被纳入 2024 年版规范，而 Chrome、Firefox 和 Safari 按各自发行节奏实现：厂商分别在 Chrome 117（2023-09）、Firefox 119（2023-10）、Safari 17.4（2024-03）的发布说明中记录它；三者都早于 ECMA-262 2024 于 2024-06-26 获批。这个先后关系说明“规范年份”和“运行时从哪一版可用”必须分开核对，不能从版次标签推出引擎支持下限。

| 运行环境 | 可核对的发行记录或运行时探针 | 能得出的结论 |
| --- | --- | --- |
| Chrome | Chrome 117 发布说明列出该方法 | 厂商记录 Chrome 117 已实现；不能据此推断嵌入式 WebView 跟随同版 Chrome，或所有设备都可升级到该版 |
| Firefox | Firefox 119 发布说明列出该方法 | 厂商记录 Firefox 119 已实现；项目仍须核对自己支持的运行版本 |
| Safari / WebKit | Safari 17.4 发布说明列出该方法 | 厂商记录 Safari 17.4 已实现；不能从 Chrome 版本推断 Safari 版本 |
| Node.js | 在目标 Node 进程运行 `node -p 'process.version + " " + typeof Object.groupBy'` | 这次探针在 Node 20.15.1 返回 `undefined`，在 22.22.3 与 26.13.0 返回 `function`；这些实测点不构成所有发行版的最低支持承诺 |

合成输入如下；`id`、`period` 和 `status` 已由上一数据边界检查过：

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

`Object.groupBy` 对同步可迭代值逐项调用回调，第二个实参是从 `0` 开始的迭代序号；回调返回值会转成对象属性键。本例按 `open`、`published`、`open` 的顺序访问三行，因此结果为：

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

方法新建了分组对象和各组数组，却没有复制行对象；`rows[0].title` 改为 `"May corrected"` 后，从 `groups.open?.[0]?.title` 读到同一修改。返回对象不继承 `Object.prototype`，所以不应调用 `groups.hasOwnProperty(...)`；检查组是否存在可用 `Object.hasOwn(groups, "open")`。例如本例结果为 `true`，即使分组对象没有原型。`rows.at(-1)` 仍按负索引取最后一行；`.at()` 和 `Object.hasOwn()` 分别来自 ES2022。上述都是运行语义，不是支持版本本身。

这份代码用 TypeScript 显式写出输入行和回调记录的类型。`Object.groupBy` 的类型结果是 `Partial<Record<K, T[]>>`：即使 `status` 的静态类型包含 `"open"`，任意一组输入也可能一行都没有该状态，所以 `groups.open` 和 `groups.published` 都可能是 `undefined`。`?? []` 让“没有该组”也能安全地显示为空数组；它不是多余的类型绕行。`callbackVisits` 的元组类型则避免严格模式把空数组推成隐式 `any[]`。

`Object.groupBy` 把回调结果转成对象属性键，适合本例这种字符串状态。如果回调值需要按 `Map` 的键规则保存（例如对象标识），`Map.groupBy` 返回 `Map`，不把键转成属性键；对象键按对象身份区分，之后用 `map.get(key)` 读取对应组。两种方法都依次处理同步可迭代值，并把原行引用放入分组数组。

下表列出可用来定位规范版次的代表性特性；年份只回答“何时进入标准”，不回答“所有目标何时实现”：

| ECMAScript 版次 | 代表特性与边界 |
| --- | --- |
| ES5 | `Object.keys` 只返回自有、可枚举的字符串键，不返回 `Symbol` 键 |
| ES2015 | `Object.assign` 修改传入的目标对象；`Object.is` 使用 SameValue（同值）规则；`Array.from` 接收可迭代或类数组输入，`Array.of` 由各实参组成数组；Promise 的 `all`、`race` 结算语义见异步章节 |
| ES2017 | `Object.values` 和 `Object.entries` 选取自有、可枚举的字符串键 |
| ES2020 | `Promise.allSettled` 等所有输入都结算后返回各项状态；`globalThis` 是当前 Realm (执行域) 的全局 `this` 值。在浏览器的 Window 环境中，该值是 `WindowProxy`；Node.js 进程有自己的全局对象 |
| ES2021 | `Promise.any` 在组合器最先观察到任一输入履行时成功，只有全部拒绝才以 `AggregateError` 拒绝 |
| ES2022 | `Array.prototype.at` 接受负索引；`Object.hasOwn` 检查自有属性 |
| ES2024 | `Object.groupBy` 按属性键分组，`Map.groupBy` 按 Map 键分组；`Promise.withResolvers` 创建 Promise 和它的控制函数 |
| ES2025 | `Set` 的并、交、差、对称差与包含/不相交判断；`RegExp.escape` 转义拼入正则表达式的字面文本 |

`structuredClone`（结构化克隆）是浏览器、Node.js 等宿主暴露的 API，不该被标成某个 ECMAScript 版次。它能复制支持的 `Date`、`Map`、`Set` 等值，也保留循环引用和共享引用；函数不能克隆，自定义类原型不会保留，不支持的值会抛出结构化克隆错误（`DataCloneError`）。需要为月报编辑器隔离嵌套快照时，具体复制范围和代价见[如何安全地深拷贝 JavaScript 值？](./deep-copy-and-structured-clone.md)；不要假设结构化克隆一定比其他做法快。

## 语法转换、类型声明和 polyfill 有什么差别？

transpiler (转译器)处理的是解析器能否读懂源码中的语法，例如把箭头函数改写成旧语法。它通常不会把缺失的 `Object.groupBy` 凭空加入运行时。`typeof Object.groupBy` 这类运行时检查可以在代码已解析后分支处理缺失 API；若整个文件用了旧引擎无法解析的语法，执行不到检查处，必须先转换语法或提供兼容代码路径。

下面给出本例所需的窄回退：目标只接受已校验的行数组和字符串状态键。原生方法存在时调用它；缺失时创建无原型分组对象，并把原行引用放入对应数组。

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

在缺少原生 API 的环境中，只保留上方的类型与 `rows` 输入，再运行这一段兼容函数；不要先执行前面的原生 `Object.groupBy` 调用，否则程序会在那里中止。原生能力存在时，该函数走原生分支。两条分支都得到 `{ open: ["r-101", "r-103"], published: ["r-102"] }`。它先用无原型对象存桶，再对相同三行按同一顺序放入对应组；这里的结果也展示了原生缺失时如何检查真实分组，而不是只确认函数没有抛错。

这段回退只复现本例所需的数组和字符串键契约，不是完整的规范 polyfill (兼容补丁)：原生方法也接受其他同步可迭代值，回调键还可以是 `Symbol`。若应用依赖这些行为，应选用经过测试、实现完整契约的补丁，而不是扩展这个小回退后就称其等价。

同步迭代与异步到达也要分开。若上一步给出 `Promise<ReportRow[]>`，先在 `async` 函数中 `await` 得到数组，再调用 `groupRowsByStatus`；分组过程仍同步逐项运行。`Object.groupBy` 不会等待一个 Promise，也不会直接消费只有异步迭代器的来源。对异步生成器要先用 `for await...of` 收集或在取数时增量分组；否则输入缺少同步迭代接口，会抛类型错误（`TypeError`）。回调也应保持同步：写成 `async row => row.status` 会返回 Promise，`Object.groupBy` 不会等待状态字符串；本例的普通 Promise 被转成 `"[object Promise]"` 这个属性键，所以三行会落进同一组。异步组合器和取消边界见[回调、Promise 与 async 函数怎样组合异步工作？](./asynchronous-javascript.md)。

TypeScript 配置中的 `target` 和 `lib` 也不是运行时检测。`target` 决定 `tsc` 生成 JavaScript 时把哪些语法降级；`lib` 决定类型检查器认为哪些标准库声明可用。下面的配置带有 `noEmit: true`，所以该命令只检查类型，不会生成语法降级后的文件；它演示的是在 ES2022 语法目标下让类型检查器看见 `Object.groupBy` 声明：

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

对上方完整的 TypeScript 示例运行 `tsc --noEmit`，这个配置会检查 `Object.groupBy` 调用和显式类型，却不会给旧浏览器补上该方法。反过来，给 `lib` 加入 `"DOM"`、`"ES2024"` 或更高声明也不会在 Node.js 中创建浏览器对象或新 API。实际支持的 `target` / `lib` 名称还取决于安装的 TypeScript 版本：截至 2026-11-13，TypeScript 7.1 Beta 已新增稳定的 `es2026` 名称，但 Beta 本身仍是预发布版；`ESNext` 会随 TypeScript 版本移动，固定部署目标时不应把它当作恒定版次。

## Vite 的开发与生产目标分别由什么控制？

Vite 8.3 的开发服务器按需提供原生 ECMAScript modules (ECMAScript 模块，ESM)，并用 Oxc 转译源文件；开发时 `oxc.target` 默认是 `esnext`，因此尽量少做语法降级。生产 `vite build` 则生成最终 bundle（打包产物）。开发和生产是两条执行路径，开发页面能运行不能代替检查发布产物。

Vite 8 的生产默认值是 `baseline-widely-available`，依据 2026-01-01 固定的 Baseline Widely Available（广泛可用基线）：Chrome / Edge 111、Firefox 114、Safari / iOS 16.4。可是 `Object.groupBy` 分别在 Chrome 117、Firefox 119、Safari 17.4 才由厂商发布说明明确列出。因此，Vite 默认目标的较早最低版本不能保证本例的原生分组 API。

这些构建选项处理不同的输出和运行路径：

| 选项 | 处理哪条路径 | 它决定什么 |
| --- | --- | --- |
| Vite `build.target` | 未启用 legacy 插件的主生产 JavaScript bundle | 控制语法转换目标；普通 Vite 不补齐缺少的内建 API |
| `@vitejs/plugin-legacy` 的 `targets` | 插件生成的 legacy chunks | 这些旧语法分块的转换目标；不会因此给现代模块分块加入同一组 API 补丁 |
| 插件的 `modernPolyfills` | 现代 JavaScript 路径 | 另生成现代补丁分块；默认是 `false`，显式指定数组可选择需要的补丁 |
| 插件的 `modernTargets` | 现代分块的语法目标，以及自动收集现代补丁时的检测目标 | 插件 8.2.4 会在客户端构建中覆盖 `build.target`；未显式设置时也使用插件自己的现代默认值。`modernPolyfills: true` 才按目标自动探测，显式补丁列表直接选择模块 |

例如，要让仍加载现代模块的浏览器也获得这一项 API，可显式选择 core-js 的对象分组补丁：

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

普通 `vite build` 不会自动装入这项补丁；仅启用 legacy chunks 也不够。插件 8.2.4 会检查 ESM、动态导入、async generator 和 `import.meta.resolve` 等现代能力，通过这组检测才走现代分块；某些已经支持 ESM 的浏览器仍会走旧分块。若 `modernPolyfills` 留在默认 `false`，现代路径仍可能在调用 `Object.groupBy` 时失败；显式补丁被装入页面后，才覆盖这条现代模块路径。DOM 和其他宿主 API 仍须另选对应补丁。

未启用 legacy 插件时，Vite 生产用 `build.target` 决定语法输出目标；Vite 不以 `tsconfig.json` 的 `target` 作为这个浏览器目标。开发时 `oxc.target` 默认是 `esnext`；构建时 `build.target` 优先于 `oxc.target`。目标名称本身不代替运行时特性检查：即使某一配置写了较低浏览器版本，语法转换也不会让缺失的 `Object.groupBy` 凭空出现。

对这组数据可以选择提高支持下限，或保留较旧环境并提供与业务契约相符的局部回退/兼容补丁；两条路径都要在实际运行时检查分组结果。Node.js 则按服务真正启动的 Node 版本核对，浏览器的 `build.target` 不决定服务器内建 API。`package.json` 的 `engines.node` 可记录声明的兼容范围，但 npm 默认将其作为提示，除非启用 `engine-strict`；它不会替部署器选择 Node 版本，也不证明该进程拥有某个 API。CI 应用部署所选 Node 版本实际启动代码，并运行同一探针。

下表中的浏览器运行把真实 Vite 生产 bundle 装进 Chrome 157，并在模块执行前清除 `Object.groupBy`。这刻意让有 ESM 的现代路径遇到缺失 API，检查它会执行哪一份产物、是否得到两组结果：

| 生产产物 | 清除 API 后执行的路径 | 结果 |
| --- | --- | --- |
| 普通 Vite 8.3.8 `vite build` | 主现代模块分块 | 报 `Object.groupBy is not a function` |
| Vite 8.3.8 + legacy 插件 8.2.4，保留默认 `modernPolyfills: false` | 插件仍加载主现代模块分块 | 同样报错；插件生成旧语法分块并未修复这条路径 |
| 上项再设 `modernPolyfills: ["es.object.group-by"]` | 页面先加载现代补丁分块，再加载应用分块 | 得到 `open: ["r-101", "r-103"]` 和 `published: ["r-102"]` |

这项故障注入只模拟“浏览器支持 ESM，但目标内建 API 不存在”这个条件，证明该构建配置如何分支；它没有在 Chrome 111、Safari 16.4 或任一厂商 WebView 上运行，因此不能替代目标设备验收。

Vite 8 使用 Oxc 转译 TypeScript，但转译不等于完整类型检查；本例的运行时支持也不能由类型检查证明。需要类型诊断时另跑 `tsc --noEmit`；随后用声明支持的浏览器/WebView 执行前端发布产物，用部署所选 Node.js 版本启动对应服务入口，分别检查结果。`structuredClone` 等宿主 API 还要按宿主自身版本验证，不能由 ECMAScript 年份或 Vite 语法目标替代。

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
