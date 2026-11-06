# TypeScript 怎样描述 React props 与样式模块？

组件 props 是调用方必须满足的编译期接口。React 组件若接受 children，应把它明确写入 props；当前 React 类型中的 FunctionComponent 不会自动把 children 添加到接口。

~~~tsx
import type { ReactNode } from "react";

type RobotProps = {
  id: number;
  name: string;
  children?: ReactNode;
};

export function Robot({ id, name, children }: RobotProps) {
  return (
    <article className="robot">
      <img alt="" src={"https://robohash.org/" + id} />
      <h2>{name}</h2>
      {children}
    </article>
  );
}
~~~

CSS Module（CSS 模块）文件的导入同时需要构建工具处理样式，并需要 TypeScript 知道默认导出的类名映射形状。旧课程常用一个环境声明：

~~~typescript
// custom.d.ts
declare module "*.module.css" {
  const classes: Readonly<Record<string, string>>;
  export default classes;
}
~~~

~~~tsx
import styles from "./Robot.module.css";

export function RobotCard() {
  return <article className={styles.robotCard}>报表机器人</article>;
}
~~~

这个声明只告诉编译器“模块导出一组字符串类名”；它不生成 CSS、不保证类名确实存在，也不决定打包器如何处理文件。图片、字体和 SVG 的静态导入同样依赖项目的 bundler（打包器）及其资源规则；需要检查构建产物的路径和输出行为时，见[构建工具怎样把源码变成可发布产物？](../../../../frontend/tooling/build-tools.md)。

使用 noImplicitAny 可让 TypeScript 报告缺少注解而被推断为 any 的值，但它不会禁止显式 any。数据来自 API 或 JSON 时，props 类型也不会替代运行时解析，见[TypeScript 如何处理不可信 JSON？](../../../../frontend/typescript/advanced-typescript.md)。

> [!info]- 来源
> - 当前 React 函数组件类型与显式 children：[React TypeScript type definitions](https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/react/index.d.ts)，核对日期：2026-11-06。
> - noImplicitAny：[TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/#noImplicitAny)，TypeScript 官方文档，核对日期：2026-11-06。
> - 类型声明会被擦除，不能验证运行时值：[TypeScript Handbook — Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)，TypeScript 官方文档，核对日期：2026-11-06。
