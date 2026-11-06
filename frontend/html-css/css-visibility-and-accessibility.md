# 隐藏状态会怎样影响焦点与可访问性？

报表详情面板关闭时，用户不应看见它、Tab 不应进入里面，屏幕阅读器也不应继续把它当作当前可用内容。淡出只影响绘制；隐藏策略还要同时处理布局、指针、键盘焦点和 accessibility tree（无障碍树）。

## 几种隐藏方式留下什么？

| 状态 | 布局空间 | 指针命中 | 键盘焦点 | 无障碍树 |
| --- | --- | --- | --- | --- |
| `display: none`（不生成显示盒）或普通 HTML `hidden`（未被作者样式覆盖） | 移除 | 不绘制、不命中 | 隐藏期间不能聚焦 | 通常不暴露 |
| `visibility: hidden`（不可见） | 保留 | hidden 后代不命中；显式设为 `visible` 的后代可命中 | hidden 后代通常不能聚焦；visible 后代可以 | hidden 后代通常不暴露；visible 后代可能暴露 |
| `opacity: 0`（不透明度为零） | 保留 | 仍可能命中 | 仍可能聚焦 | 通常仍暴露 |
| `inert`（惰性子树） | 样式决定 | 子树不接收交互 | 子树不可聚焦 | 辅助技术通常忽略该子树；视觉仍由 CSS 决定 |
| `aria-hidden="true"`（辅助技术隐藏状态） | 样式决定 | 样式决定 | 不会自行禁用焦点 | 从辅助技术呈现中隐藏子树 |

`visibility:hidden` 只对仍保持隐藏值的盒子隐藏绘制和交互；后代显式设为 `visibility:visible` 后会重新绘制、参与指针命中，也可以接收焦点。父级 `visibility:hidden` 不等同于禁用整棵子树的 `inert`。

> [!info] HTML `hidden` 的两种状态
> 表中普通 `hidden` 指默认隐藏状态；如果作者规则把该元素的 `display` 改成可生成盒子的值，CSS 可以覆盖这项隐藏样式。`hidden="until-found"` 是另一种状态：内容仍隐藏，但保留布局盒，并可由页内查找或片段导航揭示；不要把它当作 `display:none` 的同义写法。

`opacity` 不继承；浏览器把元素及其后代作为透明绘制组处理，因此子元素设为 `opacity: 1` 也无法穿透父元素的 `opacity: 0`。pointer-events（指针命中行为）只影响指针，`pointer-events: none` 不会关闭键盘焦点或无障碍呈现。

> [!info] inert 与 aria-hidden 的责任不同
> HTML `inert` 属性让整个子树暂时退出常规用户交互和顺序焦点导航，也让辅助技术忽略它。`aria-hidden` 只改变无障碍树，不负责取消焦点；不要把它放在仍有可聚焦后代的区域上。

## 关闭面板时先处理焦点

打开时移除 `hidden` 和 `inert` 并更新触发按钮的 `aria-expanded`；关闭时若焦点还在面板内，先把焦点移回触发按钮，再同步设置 `inert`、`hidden` 和折叠状态。CSS transition 负责进入与退出的视觉淡变，交互状态不等动画事件；关闭期间重新打开时，只要重新设为打开状态，当前过渡就会反向到新目标。

~~~html
<button type="button" aria-controls="report-details" aria-expanded="false">
  查看详情
</button>
<section id="report-details" hidden inert>
  <h2>筛选结果详情</h2>
  <button type="button" data-close>关闭详情</button>
</section>
~~~

~~~css
#report-details {
  display: none;
  opacity: 0;
  transition: opacity 180ms ease, display 180ms allow-discrete;
}

#report-details:not([hidden]) {
  display: block;
  opacity: 1;
}

@starting-style {
  #report-details:not([hidden]) { opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  #report-details { transition-duration: 0s; }
}
~~~

~~~javascript
const trigger = document.querySelector('[aria-controls="report-details"]');
const panel = document.querySelector("#report-details");
const closeButton = panel.querySelector("[data-close]");

function setDetailsOpen(open) {
  if (!open && panel.contains(document.activeElement)) trigger.focus();
  panel.inert = !open;
  panel.hidden = !open;
  trigger.setAttribute("aria-expanded", String(open));
}

trigger.addEventListener("click", () => setDetailsOpen(panel.hidden));
closeButton.addEventListener("click", () => setDetailsOpen(false));
~~~

这里的示例不等待 `transitionend` 才切换焦点、`inert` 或 `hidden`；所以减少动态效果时即时关闭也能完成，关闭过渡中重新打开也不会留下待执行的延时隐藏操作。

## display 也能参与离散过渡

`display` 不像 `opacity` 那样逐帧插值。CSS Transitions Level 2 允许在实现支持时用 `transition-behavior: allow-discrete` 参与离散切换，并用 `@starting-style` 定义新显示内容的起始样式。按 CSS Display Level 4 §2.9，从 `none` 进入其他显示值时，元素在过渡开始就生成显示盒；从其他值退出到 `none` 时，元素直到过渡结束才移出显示盒，所以可与透明度淡变配合。忽略过渡和动画这两个级联来源后，元素的 `display` 值若仍为 `none`，它就处于惰性状态；上面的例子在状态切换时也显式同步设置 `inert`，不等待淡变结束。

> [!info]- 来源
> - 显示盒生成和 <code>display</code>：W3C CSS Display Level 3，Candidate Recommendation Draft（2026-06-05），[CSS Display](https://www.w3.org/TR/css-display-3/)，检查于 2026-11-06。
> - <code>display</code> 离散过渡中生成/移除显示盒的时点与 inert 行为：W3C CSS Display Level 4，§2.9，Working Draft（2025-11-06），[Animating and Interpolating display](https://www.w3.org/TR/css-display-4/#display-animation)，检查于 2026-11-06。
> - `visibility` 的后代覆盖：W3C CSS Display Level 3，§4，Candidate Recommendation Draft（2026-06-05），[visibility](https://www.w3.org/TR/css-display-3/#visibility)，检查于 2026-11-06。
> - `opacity` 的非继承性、整组透明绘制和命中测试：W3C CSS Color Level 4，Candidate Recommendation Draft（2026-11-03），[CSS Color](https://www.w3.org/TR/css-color-4/)，检查于 2026-11-06。
> - `pointer-events` 对指针命中与顺序焦点导航的边界：W3C CSS Basic User Interface Level 4，Working Draft（2026-01-20），[CSS Basic User Interface](https://www.w3.org/TR/css-ui-4/)，检查于 2026-11-06。
> - `inert` 子树与交互：WHATWG HTML Living Standard（2026-11-05 更新），[Inert subtrees](https://html.spec.whatwg.org/multipage/interaction.html#inert-subtrees)，检查于 2026-11-06。
> - 普通 `hidden` 与 `until-found` 状态：WHATWG HTML Living Standard（2026-11-05 更新），[The `hidden` attribute](https://html.spec.whatwg.org/multipage/interaction.html#the-hidden-attribute)，检查于 2026-11-06。
> - `aria-hidden` 和 `aria-expanded` 状态：W3C WAI-ARIA 1.2，Recommendation（2023-06-06），[WAI-ARIA](https://www.w3.org/TR/wai-aria-1.2/)，检查于 2026-11-06。
> - 离散显示过渡：W3C CSS Transitions Level 2，Working Draft（2026-02-04），[transition-behavior](https://www.w3.org/TR/css-transitions-2/#transition-behavior-property)，检查于 2026-11-06。
> - 减少动态效果：W3C Media Queries Level 5，Working Draft（2026-02-19），[prefers-reduced-motion](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion)，检查于 2026-11-06。
> - 键盘操作和焦点管理：W3C WAI [ARIA APG Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)，检查于 2026-11-06。
