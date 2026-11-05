# Which VS Code and Emmet shortcuts speed up markup work? / 哪些 VS Code 和 Emmet 快捷方式可以加快标记编写？

Emmet expands abbreviations into HTML and CSS snippets; inspect the editor preview because fuzzy matches and project snippets can change the expansion. Keyboard shortcuts depend on the selected keymap. / Emmet 将缩写扩展成 HTML 和 CSS 片段；模糊匹配和项目自定义片段可能改变结果，因此应检查编辑器预览。快捷键取决于当前键位映射。

## VS Code and Emmet / VS Code 与 Emmet

VS Code enables Emmet abbreviations in HTML and CSS by default for common file types. In an HTML file, ! can expand to a starter document. For example:

| Abbreviation | Typical HTML expansion |
|---|---|
| **div** | Empty div element |
| **.red** | Div with class red |
| **#one** | Div with id one |
| **p.red#one** | Paragraph with class red and id one |
| **ul>li*3** | A list with three list items |
| **ul>li{item $}*3** | Three list items containing item 1, item 2, and item 3 |

Common CSS abbreviations include these default snippets and shorter forms that Emmet may resolve through fuzzy search; inspect the editor preview:

| Abbreviation | Typical CSS expansion |
|---|---|
| **bgc** | `background-color: #fff;` |
| **bgi** | `background-image: url(...);` |
| **bgr** | `background-repeat: no-repeat;` with other repeat values available in the snippet choices |
| **bgp** | `background-position: 0 0;` |
| **bg** | `background: #000;` |
| **ta** | `text-align: left;` with center, right, and justify choices |
| **pos** | `position: relative;` with other position choices |
| **bd** | `border: 1px solid #000;` |
| **tac** *(fuzzy-search candidate)* | May resolve to `text-align: center;`; confirm the editor suggestion. |
| **por** *(fuzzy-search candidate)* | May resolve to `position: relative;`; confirm the editor suggestion. |

The checked default snippets provide `ta` and `pos` with the listed value choices. Emmet fuzzy search can match unknown abbreviations against predefined snippet names; inspect the editor preview before relying on a shorter form.

On the default macOS keymap, common editing actions include:

- **⌘+/** toggles a line comment.
- **Option+Z** toggles word wrap.
- **Option+Shift+Down** duplicates the current line or selection.
- **Option+Click** adds another cursor.

Keymaps can be changed. Check **Keyboard Shortcuts** if a binding differs. In a CSS file, **w100+h100** expands to `width: 100px; height: 100px;`; **w100p** expands to `width: 100%;`, and **m10-20** to `margin: 10px 20px;`. Emmet also accepts explicit units and multi-value shorthands. Inspect the suggestion preview when a project has custom snippets or editor settings.

A favicon can be declared in the document head:

~~~html
<link rel="icon" href="/favicon.ico">
~~~

Split the editor into panes when comparing related HTML and CSS files; the layout is an editor convenience, not a build requirement.

**References checked 2026-10-15** — [VS Code Emmet](https://code.visualstudio.com/docs/languages/emmet), [Emmet CSS abbreviations](https://docs.emmet.io/css-abbreviations/), [default CSS snippet definitions](https://github.com/emmetio/snippets/blob/master/css.json), [Emmet fuzzy search](https://docs.emmet.io/css-abbreviations/fuzzy-search/), [VS Code keyboard shortcuts](https://code.visualstudio.com/docs/getstarted/keybindings).
