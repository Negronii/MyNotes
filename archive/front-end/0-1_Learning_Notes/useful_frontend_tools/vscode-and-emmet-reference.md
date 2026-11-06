# 哪些 VS Code 与 Emmet 操作可以减少重复输入？

Emmet 将HTML（HyperText Markup Language，超文本标记语言）与CSS（Cascading Style Sheets，层叠样式表）缩写扩展成代码片段；它适合生成重复骨架，不能替你确认语义标签、无障碍名称或样式是否符合页面设计。先看建议预览，再展开到编辑器，并根据项目的自定义 snippet（代码片段）与键位配置确认结果。

## HTML 缩写怎样生成标签结构？

Emmet 已内置于 VS Code，在 HTML、CSS、SCSS、Sass、Less、JSX 等常见文件类型中提供缩写和 snippet。输入时建议查看补全列表中的展开预览；在 HTML 文件里，`!` 常用于展开文档骨架。

| 缩写 | 常见展开结果 |
|---|---|
| `div` | 空的 `<div></div>` |
| `.red` | 带 `class="red"` 的 div |
| `#one` | 带 `id="one"` 的 div |
| `p.red#one` | 带 class 和 id 的段落 |
| `ul>li*3` | 含三个列表项的无序列表 |
| `ul>li{item $}*3` | 三个文本分别为 item 1、item 2、item 3 的列表项 |

CSS 缩写也可输出属性及默认值；fuzzy search（模糊搜索）还会把未知缩写按相近 snippet 名匹配。下表中的 `tac`、`por` 是可能匹配的候选，应以当前编辑器补全预览为准：

| 缩写 | 常见输出或候选 |
|---|---|
| `bgc` | `background-color: #fff;` |
| `bgi` | `background-image: url(...);` |
| `bgr` | `background-repeat: no-repeat;`，其他值可从建议中选 |
| `bgp` | `background-position: 0 0;` |
| `bg` | `background: #000;` |
| `ta` | `text-align: left;`，通常可从建议选其他值 |
| `pos` | `position: relative;`，通常可从建议选其他值 |
| `bd` | `border: 1px solid #000;` |
| `tac` / `por` | 可能模糊匹配到 `text-align: center` / `position: relative`；先核对预览 |

VS Code 的 `emmet.triggerExpansionOnTab` 可把 Tab 配成触发展开；若关闭，仍可从建议列表或命令面板运行 **Emmet: Expand Abbreviation**。`.vscode/settings.json` 里的 `emmet.includeLanguages` 可为未默认支持的文件类型指定 Emmet 语法标识，但扩展不了语义分析：Emmet 不知道新语言是否真的是 HTML 或 CSS。

## macOS 键位与 CSS 数值缩写有哪些常用操作？

在默认 macOS keymap（键位映射）中，常用操作包括 `⌘+/` 切换行注释、`Option+Z` 切换自动换行、`Option+Shift+↓` 复制当前行或选区、`Option+Click` 添加光标。CSS 文件中的 `w100+h100` 可展开为宽高各 100px，`w100p` 展开成宽度 100%，`m10-20` 展开成 `margin: 10px 20px`；缩写也可使用显式单位和多值写法。

VS Code 支持改键和 keymap 扩展，键位还受系统键盘布局影响；若快捷键与这里不同，在 **Keyboard Shortcuts** 面板按命令名查当前绑定。Favicon 仍由页面 head 中的 link 声明，例如：

~~~html
<link rel="icon" href="/favicon.ico">
~~~

分屏可在比较页面 HTML 与 CSS 时同时展示两个文件，它只改变编辑器布局，不改变构建结果。

> [!info]- 来源
> - [VS Code：Emmet 支持、配置和展开预览](https://code.visualstudio.com/docs/languages/emmet)
> - [Emmet：HTML 缩写参考](https://docs.emmet.io/abbreviations/)、[CSS 缩写与模糊搜索](https://docs.emmet.io/css-abbreviations/)、[默认 CSS snippets](https://github.com/emmetio/snippets/blob/master/css.json)
> - [VS Code：默认键位参考](https://code.visualstudio.com/docs/reference/default-keybindings)、[键位自定义](https://code.visualstudio.com/docs/configure/keybindings)
>
> 缩写与操作按官方当前文档、默认 snippet 与 macOS 键位资料复核；自定义 snippet、扩展和 keymap 会改变行为。核对日期：2026-11-06。
