# How does Less turn reusable styles into CSS? / Less 如何把可复用样式转换为 CSS？

Less variables, nesting, and arithmetic are source-language conveniences; a compiler emits ordinary CSS for the browser. Inspect generated output and make the root-size or viewport scaling rule explicit. / Less 的变量、嵌套和算术是源语言便利功能；编译器会生成浏览器使用的普通 CSS。检查生成结果，并明确根字号或视口缩放规则。

## Less / Less 预处理器

Less is a CSS preprocessor. Nesting, variables, and arithmetic are compiled to ordinary CSS before the browser uses the stylesheet.

~~~less
@brand-color: #c35;
@design-root: 37.5; // A 375px-wide design whose root font size is 37.5px.

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

A Less compiler emits selectors and calculated values such as:

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

The pixel-to-rem calculation assumes that the document root font size follows the design scale. For example, 37.5 CSS pixels per rem at a 375px design width makes a 68px design measurement equal to about 1.813rem. The application still needs to set the root font size consistently.

- Nested selectors use a space to form descendants; the ampersand refers to the parent selector, as in &:hover, &::before, or &.active.
- Variables use @name: value;. Reuse them for repeated colors, spacing, and other design tokens.
- Less supports arithmetic. Parentheses make division explicit, and unit behavior should be checked in the generated CSS.
- // is a Less-only line comment and is omitted from the CSS output. Block comments are emitted.
- @import "tokens.less"; includes another Less file. The import path and build configuration determine which source is compiled.
- Easy LESS can compile on save and configure output through its `less.compile` VS Code setting. In the project `.vscode/settings.json`, for example, `"less.compile": { "out": "${workspaceFolder}/dist/css/" }` sends each file's CSS to that folder; keep the trailing slash. A specific path such as `"out": "${workspaceFolder}/dist/app.css"` names one output file. Paths are relative to the Less source unless expanded from `${workspaceFolder}`.
- For an imported Easy LESS partial that should not emit its own CSS file, put `// out: false` on the first line of that `.less` file. This is extension configuration, not Less language syntax; a build pipeline can instead compile Less as part of the application build.

For a design that scales with the viewport width, a ratio can be written directly in Less:

~~~less
@design-width: 375;
.box {
  width: (68 / @design-width) * 100vw;
}
~~~

This yields approximately 18.133vw for a 68px measurement in a 375px-wide design. Document the design viewport and formula near the conversion; avoid applying a fixed ratio when the project uses a different scaling rule.

**See also / 另见：** [Build Tools / 构建工具](../../../../frontend/tooling/build-tools.md) for loaders and build pipelines.
**References / 参考资料：** [Less documentation](https://lesscss.org/), [Easy LESS extension settings](https://github.com/mrcrowl/vscode-easy-less#readme).
