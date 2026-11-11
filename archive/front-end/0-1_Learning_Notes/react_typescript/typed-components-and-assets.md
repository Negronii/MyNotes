# TypeScript 怎样描述 React props 与样式模块？

**案例背景。** 报表页要显示一张机器人信息卡：调用方传入数字 `id` 和名字 `name`，还可以把说明文字放进卡片。React 用 props（属性）把这些值传给组件；TypeScript 在检查 JSX 时对照调用处的 props 类型。标签间的段落成为 `props.children`；本例允许没有说明。`@types/react` 18+ 不再由 `React.FC`/`FunctionComponent` 自动添加 `children`，组件接收子节点且使用这些别名时，应在 props 类型中明确写出；React 17 的类型仍保留旧的隐式 `children` 行为。下面的 `Robot` 直接标注 `RobotProps`，所以接口始终显式写出 `children`；维护旧项目时，以锁文件中的 `@types/react` 版本为准。

下面示例采用 React 19、对应的 `@types/react` 类型与自动 JSX 转换。

~~~tsx
import type { ReactNode } from "react";
import styles from "./Robot.module.css";

type RobotProps = {
  id: number;
  name: string;
  children?: ReactNode;
};

export function Robot({ id, name, children }: RobotProps) {
  return (
    <article className={styles.robotCard}>
      <img alt="" src={"https://robohash.org/" + id} />
      <h2>{name}</h2>
      {children}
    </article>
  );
}

export function ReportCardExample() {
  return (
    <Robot id={7} name="Ada">
      <p>本月检查已完成</p>
    </Robot>
  );
}
~~~

调用处提供 `id: 7`、`name: "Ada"` 和一段说明；组件把它们组合成卡片，图片地址是 `https://robohash.org/7`，标题是 Ada，说明显示在标题下方。`children?: ReactNode` 允许省略整个标签内容。如果 API 要求调用方必须提供 `children` 属性，可写 `children: ReactNode`；但 `ReactNode`（React 可渲染节点）也接受 `undefined`、`null`、`false` 等空节点，因此必填属性不保证页面上出现可见子内容。任意普通 JavaScript 对象仍不是可渲染节点。

## CSS Module 的声明描述什么？

CSS Module（CSS 模块）文件中的类名会成为导入映射的键；构建工具生成实际 CSS，并为页面元素生成对应的类名字符串。上面的 `Robot` 用 `styles.robotCard` 取得 `.robotCard` 对应的生成类名。对应的 CSS 规则如下：

~~~css
/* Robot.module.css */
.robotCard {
  padding: 1rem;
  border-radius: 0.5rem;
}
~~~

Vite 的 `vite/client` 类型已声明常见静态资源和 CSS Module 导入；Vite 项目应启用这组类型，避免再复制一份相同的通配声明。对没有提供资源类型的构建工具，下面的 ambient module declaration（环境模块声明）展示 TypeScript 所需的模块形状；构建器仍须实际把 CSS 文件转换成映射。把它放在项目纳入编译的全局 `.d.ts` 文件中，文件顶层不要加 `import` 或 `export`，否则声明会成为模块扩充而不再声明任意 `*.module.css` 导入。

~~~typescript
// custom.d.ts

declare module "*.module.css" {
  const classes: Readonly<Record<string, string>>;
  export default classes;
}
~~~

这个声明只描述映射类型，不生成 CSS、不决定样式怎样注入页面或怎样打包。`Record<string, string>` 让 TypeScript 接受任意字符串类名键；开启 `noUncheckedIndexedAccess` 时，读取值的类型会是 `string | undefined`，但这种宽泛声明仍不能验证类名是否真的存在。拼错成 `styles.robotCar` 时，运行时映射中没有该键，读到的是 `undefined`。要让编译器核对每个类名，需要更精确的生成声明或其他项目类型方案。完整资源路径与构建产物见[构建工具怎样把源码变成可发布产物？](../../../../frontend/tooling/build-tools.md)。

Vite 默认静态资源导入返回构建后的 URL；要把资源源码当字符串读入，可用它内置的 `?raw` 查询，无需另外安装转换插件：

~~~tsx
import svgSource from "./icon.svg?raw";
~~~

若要把 SVG 导入成 React 组件，则需采用相应的转换插件和匹配类型。图片、字体等常见静态资源的默认 URL 行为与 TypeScript 的导入声明是两件事，仍要确认项目使用的构建工具及其类型配置。

## props 类型不能验证外部数据

`noImplicitAny`（禁止隐式 `any`）会在 TypeScript 无法推断类型而要默认成 `any` 时报告错误；显式写出的 `any` 仍然允许，并绕过后续类型检查。TypeScript 在检查 JSX 调用时对照 props 类型，这些类型不会留在浏览器替外部数据做验证。例如 `{"id":"7","name":"Ada"}` 是合法 JSON（JavaScript 对象表示法），`JSON.parse` 能成功，但解析出的 `id` 是字符串，不能直接作为 `RobotProps` 中的数字。先把解析结果按不可信输入做运行时字段校验；只有校验得到数字 id 和字符串 name 后，才交给 `Robot`。具体如何解析见[收到不可信 JSON 后，TypeScript 怎样建立可信的类型？](../../../../frontend/typescript/advanced-typescript.md)。

> [!info]- 来源
> - 自动 JSX 转换让 JSX 无需单独导入 React 命名空间；React 19 要求使用该转换：[React 19 Upgrade Guide — New JSX Transform](https://react.dev/blog/2024/04/25/react-19-upgrade-guide#new-jsx-transform-is-now-required)，React 官方文档，核验日期：2026-11-12。
> - React props、`ReactNode` 和 `ReactElement` 的差别：[Using TypeScript — React](https://react.dev/learn/typescript)，React 官方文档，核验日期：2026-11-12。
> - React 18 类型迁移要求显式声明 `children`：[React 18 Upgrade Guide — Updates to TypeScript definitions](https://react.dev/blog/2022/03/08/react-18-upgrade-guide#updates-to-typescript-definitions)、[DefinitelyTyped #56210](https://github.com/DefinitelyTyped/DefinitelyTyped/pull/56210)；React 17 的旧类型行为：[DefinitelyTyped React 17 类型定义](https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/react/v17/index.d.ts)，核验日期：2026-11-12。
> - `noImplicitAny` 只报告推断出的隐式 `any`；`noUncheckedIndexedAccess` 让索引签名读取包含 `undefined`：[TypeScript TSConfig — noImplicitAny](https://www.typescriptlang.org/tsconfig/noImplicitAny.html)、[noUncheckedIndexedAccess](https://www.typescriptlang.org/tsconfig/#noUncheckedIndexedAccess)，TypeScript 官方文档，核验日期：2026-11-12。
> - 通配符环境模块声明及脚本环境中的声明语义：[TypeScript Modules Reference — Ambient modules](https://www.typescriptlang.org/docs/handbook/modules/reference#ambient-modules)，TypeScript 官方文档，核验日期：2026-11-12。
> - Vite CSS Module 和客户端类型：[Features — CSS Modules and Client Types](https://vite.dev/guide/features#client-types)、[Vite `client.d.ts`](https://github.com/vitejs/vite/blob/main/packages/vite/client.d.ts)，Vite 官方资料，核验日期：2026-11-12。
> - Vite 静态资源默认 URL 与 `?raw` 导入：[Static Asset Handling — Importing Asset as URL / Importing Asset as String](https://vite.dev/guide/assets#importing-asset-as-string)，Vite 官方文档，核验日期：2026-11-12。
> - TypeScript 类型只检查代码，不代替 JSON 运行时解析：[TypeScript 如何处理不可信 JSON？](../../../../frontend/typescript/advanced-typescript.md)。
