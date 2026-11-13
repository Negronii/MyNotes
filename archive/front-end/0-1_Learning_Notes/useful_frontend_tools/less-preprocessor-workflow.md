# Less 怎样把复用规则转换成浏览器可用的样式表？

Less 提供变量、嵌套、算术和 mixin（混合）等源语言能力；浏览器最终读取的是编译器输出的 CSS（Cascading Style Sheets，层叠样式表）。报表卡片可以把重复颜色和边框声明放进 mixin，把设计数值放在变量里；编译结果仍要与项目的根字号或视口缩放规则一致。

## 变量、嵌套和算术怎样转成 CSS？

下面保留一份宽 375px 的设计稿：根字号按每 `1rem = 37.5px` 设定，卡片宽度的 68px 设计值换算为 `68 / 37.5 = 1.81333rem`。将代码保存为 `card.less`。输出按 Less 4.9.1 的默认 math 模式编译；Easy LESS 2.0.5 的依赖使用 Less 4.5.1，以下算例在两版默认模式下输出相同。`@design-root` 只是 Less 编译时参与计算的数值，不会设置浏览器中的根字号。

用 `.card-accent()` 定义一组可复用声明，再由两个选择器调用：

~~~less
@brand-color: #c35;
@design-root: 37.5; // 375px 设计宽度下约定的根字号，单位为 px。

.card-accent() {
  color: @brand-color;
  border: 1px solid @brand-color;
}

.card {
  .card-accent();
  box-sizing: border-box;
  width: (68 / @design-root) * 1rem;

  .title {
    font-weight: bold;
  }

  &:hover {
    color: #99334d;
  }
}

.notice {
  .card-accent();
}
~~~

Less 编译器把 mixin 中的声明放进每个调用处，得到可由浏览器读取的 CSS：

~~~css
.card {
  color: #c35;
  border: 1px solid #c35;
  box-sizing: border-box;
  width: 1.81333333rem;
}
.card .title {
  font-weight: bold;
}
.card:hover {
  color: #99334d;
}
.notice {
  color: #c35;
  border: 1px solid #c35;
}
~~~

根元素字号要由页面的缩放方案实际设置，否则 1.81333333rem 不一定对应设计稿中的 68 CSS 像素。若设计规范随视口宽度按比例缩放，也可以把下面的另一种写法保存为 `card-vw.less`，用视口单位表示同一设计比例：

~~~less
@design-width: 375;

.card-vw {
  width: (68 / @design-width) * 100vw;
  box-sizing: border-box;
}
~~~

按 Less 4.9.1 与 4.5.1 的默认 math 模式编译，上式输出 `18.13333333vw`。只有在项目确实按 375px 设计宽度做等比缩放时，才适用这一换算；固定断点、自适应栅格或容器宽度规则可能要求不同的实现。

变量可以复用颜色、间距和 design token（设计令牌）；空格表示后代选择器，`&` 把父选择器放进当前选择器（如 `&:hover`、`&::before` 或 `&.active`）。括号让默认 math 模式下的除法关系明确；若更改 Less 的 `math` 选项，应按该模式重新检查编译结果和单位。

Less 中 `//` 单行注释不会出现在 CSS 输出里；默认未压缩输出会保留块注释，压缩输出可以去掉它。`@import "tokens.less";` 可引入 Less 文件；`.css` 扩展名默认作为 CSS 导入语句保留。依赖特定导入模式时应显式查看编译结果。

## Easy LESS 怎样处理编辑器中的输出路径？

Easy LESS 是 VS Code 扩展，不是 Less 语言的一部分。扩展可以在保存时编译，并通过项目 `.vscode/settings.json` 的 `less.compile` 指定输出目录，例如：

~~~json
{
  "less.compile": {
    "out": "${workspaceFolder}/dist/css/"
  }
}
~~~

把第一段代码保存为 `card.less` 后，目录值保留结尾斜线时，扩展按此目录输出 `dist/css/card.css`；完整文件路径如 `"out": "${workspaceFolder}/dist/app.css"` 则指定单个输出文件。若使用多根工作区，`${workspaceFolder}` 指的是当前 Less 文件所属的工作区文件夹；一般相对 `out` 路径以当前 `.less` 源文件所在目录为基准。导入用的 partial（局部样式文件）若不需要单独生成 CSS，Easy LESS 支持在文件首行写 `// out: false`；这是扩展识别的设置注释，不是 Less 语言规则。项目也可在正式构建流水线中统一编译 Less，避免编辑器扩展和生产构建生成两套不同产物。

不通过编辑器扩展时，也可在项目根目录运行命令行编译器：

~~~sh
mkdir -p dist/css
npx --yes --package less@4.9.1 lessc card.less dist/css/card.css
npx --yes --package less@4.9.1 lessc card-vw.less dist/css/card-vw.css
~~~

浏览器要加载生成后的 CSS，页面仍需引用输出文件。下面的独立测试页把 `html` 根字号固定为 37.5px；它只是让这组算例可复查，不代表项目必须采用这个字号。实际页面应按自己的缩放方案设置根字号。

~~~html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>html { font-size: 37.5px; }</style>
  <link rel="stylesheet" href="./dist/css/card.css">
  <link rel="stylesheet" href="./dist/css/card-vw.css">
</head>
<body>
  <div class="card"><span class="title">报表</span></div>
  <div class="notice">需要复用样式的提示</div>
  <div class="card-vw">按视口比例缩放的卡片</div>
</body>
</html>
~~~

在这个测试条件下，把视口设为 375px 或 450px，rem 卡片的边框盒都为 68px；视口版本在 375px 时为 68px，在 450px 时约为 81.6px。前者随固定根字号换算，后者直接随视口宽度同比缩放；项目若用不同的根字号、断点或容器规则，结果也会不同。

原课程还用一组文件名说明样式职责：`base.less` 或 `base.css` 放基础样式与重置；`normalize.less` 或 `normalize.css` 放浏览器样式归一化；`index.less` 或 `index.css` 放首页专属样式。`normalize` 可以减少部分默认样式差异，但不能保证处理所有浏览器兼容问题。这是课程中的组织示例，不是每个项目都必须采用的结构。Sass 是另一种预处理器；Webpack 中 Sass 与 PostCSS 的 loader（加载器）顺序见[构建工具章节的 Sass 配置](../../../../frontend/tooling/build-tools.md#Webpack%20%E7%9A%84%E6%A8%A1%E5%9D%97%E5%8A%A0%E8%BD%BD%E5%99%A8%E4%B8%8E%E6%8F%92%E4%BB%B6%E5%88%86%E5%88%AB%E5%A4%84%E7%90%86%E4%BB%80%E4%B9%88%EF%BC%9F)。

正式构建中怎样选择 loader、输出目录并检查资源，见[构建工具怎样把源码变成可发布产物？](../../../../frontend/tooling/build-tools.md)。

> [!info]- 来源
> - **Less 变量、混合、嵌套、算术与导入：**[Less Features 文档](https://lesscss.org/features/)、[混合（mixins）](https://lesscss.org/features/#mixins-feature)、[导入规则](https://lesscss.org/features/#import-atrules-feature)。
> - **CLI 与 math 模式：**[Less 命令行选项](https://lesscss.org/usage/#command-line-usage)、[Less math 选项](https://lesscss.org/usage/#less-options-math)。
> - **Easy LESS 2.0.5：**[版本说明](https://github.com/mrcrowl/vscode-easy-less/tree/v2.0.5#readme)、[依赖版本](https://github.com/mrcrowl/vscode-easy-less/blob/v2.0.5/package.json)、[输出路径实现](https://github.com/mrcrowl/vscode-easy-less/blob/v2.0.5/src/LessCompiler.ts)。
>
> Less 代码于 2026-11-13 以 4.9.1 命令行版本编译，并与 Easy LESS 2.0.5 所用的 Less 4.5.1 默认模式输出核对；同时复核了 Less 与 Easy LESS 的对应版本文档及实现。
