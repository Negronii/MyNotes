# 哪些 VS Code 与 Emmet 操作可以减少重复输入？

Emmet 将 HTML（HyperText Markup Language，超文本标记语言）与 CSS（Cascading Style Sheets，层叠样式表）缩写扩展成代码片段；它适合生成重复骨架，不能替你确认语义标签、无障碍名称或样式是否符合页面设计。先在建议列表查看展开预览，再插入编辑器，并根据当前语言模式、项目自定义代码片段和键位配置确认结果。下文也保留几种常用的 macOS 编辑器操作。

## HTML 缩写怎样生成标签结构？

在 VS Code 的 HTML 语言模式文件中，输入时先查看补全列表里的 Emmet 展开预览；例如在空白行输入 `ul>li{item $}*3`，选择展开建议并确认。表中结果按 VS Code 1.146.0 内置 Emmet 的默认规则整理；文件语言模式、当前父元素、自定义 snippet（代码片段）和扩展都可能影响建议。

| 缩写 | 常见展开结果 |
|---|---|
| `div` | 空的 `<div></div>` |
| `.red` | 无父标签上下文时为 `<div class="red"></div>` |
| `#one` | 带 `id="one"` 的 `div` |
| `p.red#one` | 带 class 和 id 的 `p` |
| `ul>li*3` | 含三个列表项的无序列表 |
| `ul>li{item $}*3` | 三个文本分别为 item 1、item 2、item 3 的列表项 |
| `!` | HTML 文档骨架 |

在列表、表格等父元素中，Emmet 会按上下文推断省略的标签；例如 `ul>.red` 中的 `.red` 会展开成列表项而不是 `div`。展开 `!` 时检查生成的语言、视口设置和标题值，再按页面实际信息修改。

## macOS 键位与 CSS 数值缩写有哪些常用操作？

CSS 缩写要在 CSS 语言模式文件的规则块内部展开：先写 `.card {}`，把光标放在花括号里的独立空白行，再输入 `bgc` 等缩写。以下是 VS Code 1.146.0 内置 Emmet 的默认展开；fuzzy search（模糊匹配）也可能为缩写找到候选，因此插入前仍应检查预览。

| 缩写 | 常见输出或默认展开 |
|---|---|
| `bgc` | `background-color: #fff;` |
| `bgi` | `background-image: url();`，光标停在括号内 |
| `bgr` | `background-repeat: no-repeat;` |
| `bgp` | `background-position: 0 0;` |
| `bg` | `background: #000;` |
| `ta` | `text-align: left;` |
| `pos` | `position: relative;` |
| `bd` | `border: 1px solid #000;` |
| `tac` | `text-align: center;` |
| `por` | `position: relative;` |

`tac` 与 `por` 在这个版本中有可直接确认的默认展开。其他属性值可在展开后修改，也可把光标放在属性值位置调用 CSS 补全。若建议列表未弹出，可手动触发建议或运行 **Emmet: Expand Abbreviation**。`emmet.triggerExpansionOnTab` 默认关闭；设置为 `true` 后，可用 Tab 展开缩写。`.vscode/settings.json` 的 `emmet.includeLanguages` 可为未默认支持的文件类型指定 Emmet 语法标识，但这不会增加该语言的语义分析能力。

在默认 macOS keymap（键位映射）中，`⌘+/` 切换行注释，`Option+Z` 切换自动换行，`Option+Shift+↓` 复制当前行；若选中内容，会复制选区涉及的整行，`Option+Click` 则添加光标。VS Code 支持改键和 keymap 扩展，键位还受系统键盘布局影响；若快捷键与这里不同，在 **Keyboard Shortcuts** 面板按命令名查当前绑定。

生成 HTML 骨架后，若项目中确实有 `/favicon.ico`，可在 `head` 中为页面声明图标：

~~~html
<link rel="icon" href="/favicon.ico">
~~~

数值缩写也在 CSS 规则块中展开：`w100+h100` 生成 `width: 100px;` 和 `height: 100px;`，`w100p` 生成 `width: 100%;`，`m10-20` 生成 `margin: 10px 20px;`。先核对预览中的单位，再插入。

分屏可以让 HTML 和 CSS 同时显示，方便对照两个文件；它只改变编辑器布局，不改变构建结果。

> [!info]- 来源
> - **VS Code Emmet：**[Emmet 支持、配置和展开预览](https://code.visualstudio.com/docs/languages/emmet)、[1.146.0 展开位置实现](https://github.com/microsoft/vscode/blob/1.146.0/extensions/emmet/src/abbreviationActions.ts#L436)。
> - **Emmet 缩写：**[HTML 缩写](https://docs.emmet.io/abbreviations/)、[隐式标签](https://docs.emmet.io/abbreviations/implicit-names/)、[CSS 缩写](https://docs.emmet.io/css-abbreviations/)、[默认 CSS snippets](https://github.com/emmetio/snippets/blob/master/css.json)。
> - **VS Code 键位：**[macOS 默认键位](https://code.visualstudio.com/docs/reference/default-keybindings)、[多光标选择](https://code.visualstudio.com/docs/editing/getting-started/tips-and-tricks#_multi-cursor-selection)、[键位自定义](https://code.visualstudio.com/docs/configure/keybindings)、[1.146.0 复制行实现](https://github.com/microsoft/vscode/blob/1.146.0/src/vs/editor/contrib/linesOperations/browser/copyLinesCommand.ts#L32)。
>
> 缩写与展开预览于 2026-11-13 使用 VS Code 1.146.0 内置 Emmet helper 核对；macOS 键位按同日的官方文档与版本化源码核对，未操作编辑器界面。项目自定义 snippet、扩展和 keymap 会改变行为。
