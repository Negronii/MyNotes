# Less 怎样把复用规则转换成浏览器可用的样式表？

Less 提供变量、嵌套和算术等源语言能力；浏览器最终读取的是编译器输出的CSS（Cascading Style Sheets，层叠样式表）。报表卡片可以把重复颜色和设计值放在 Less 变量里，但编译结果仍要与项目的根字号或视口缩放规则一致。

## 变量、嵌套和算术怎样转成 CSS？

下面保留一份宽 375px 的设计稿：根字号按每 `1rem = 37.5px` 设定，卡片宽度的 68px 设计值换算为 `68 / 37.5 = 1.81333rem`。

~~~less
@brand-color: #c35;
@design-root: 37.5; // 375px 设计宽度下约定的根字号，单位为 px。

.card {
  color: @brand-color;
  width: (68 / @design-root) * 1rem;

  .title {
    font-weight: bold;
  }

  &:hover {
    color: #99334d;
  }
}
~~~

Less 编译器输出的结果类似：

~~~css
.card {
  color: #c35;
  width: 1.813333rem;
}
.card .title {
  font-weight: bold;
}
.card:hover {
  color: #99334d;
}
~~~

根元素字号要由页面的缩放方案实际设置，否则 1.813rem 不一定对应设计稿中的 68 CSS 像素。若设计规范随视口宽度按比例缩放，也可以用视口单位表示同一个设计比例：

~~~less
@design-width: 375;

.card {
  width: (68 / @design-width) * 100vw;
}
~~~

这会得到约 `18.133vw`。只有在项目确实按 375px 设计宽度做等比缩放时，才适用这一换算；固定断点、自适应栅格或容器宽度规则可能要求不同的实现。

变量可以复用颜色、间距和设计 token；空格表示后代选择器，`&` 把父选择器放进当前选择器（如 `&:hover`、`&::before` 或 `&.active`）。括号让除法关系明确，编译后要检查实际单位和选择器范围。

Less 中 `//` 单行注释不会出现在 CSS 输出里，块注释会输出。`@import "tokens.less";` 可引入 Less 文件；`.css` 扩展名默认作为 CSS 导入语句保留。依赖特定导入模式时应显式查看编译结果。

## Easy LESS 怎样处理编辑器中的输出路径？

Easy LESS 是 VS Code 扩展，不是 Less 语言的一部分。扩展可以在保存时编译，并通过项目 `.vscode/settings.json` 的 `less.compile` 指定输出目录，例如：

~~~json
{
  "less.compile": {
    "out": "${workspaceFolder}/dist/css/"
  }
}
~~~

目录值保留结尾斜线时，扩展按此目录输出对应 CSS；完整文件路径如 `"out": "${workspaceFolder}/dist/app.css"` 则指定单个输出文件。导入用的 partial 若不需要单独生成 CSS，Easy LESS 支持在文件首行写 `// out: false`；这是扩展识别的设置注释，不是 Less 语言规则。项目也可在正式构建流水线中统一编译 Less，避免编辑器扩展和生产构建生成两套不同产物。

`out` 中的一般相对路径以当前 `.less` 源文件目录为基准；`${workspaceFolder}` 则显式以 VS Code 打开的工作区根目录为基准。多目录项目要先确认设置选的是文件相对路径还是工作区统一输出目录。

正式构建中怎样选择 loader、输出目录并检查资源，见[构建工具怎样把源码变成可发布产物？](../../../../frontend/tooling/build-tools.md)。

> [!info]- 来源
> - [Less 官方文档：变量、嵌套、算术与导入](https://lesscss.org/features/)
> - [Easy LESS 扩展说明与设置](https://github.com/mrcrowl/vscode-easy-less#readme)
>
> 37.5px 根字号、68px 设计值和视口比例沿用原稿算例；编译结果按公式复算。来源核对日期：2026-11-06。
