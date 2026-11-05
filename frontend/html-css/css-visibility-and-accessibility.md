# What changes when an element is visually hidden with CSS? / 用 CSS 隐藏元素时会发生什么变化？

Choose a hiding method by the state users should experience. `display: none` removes the box from layout and generally from the accessibility tree; `visibility: hidden` keeps layout space but suppresses visibility; `opacity: 0` makes a rendered box transparent while it can still receive focus and pointer input. Fading is only visual: also manage focus, input, and accessible state while the element is hidden. / 根据用户应体验的状态选择隐藏方式。`display: none` 会从布局中移除盒子，通常也从无障碍树中移除；`visibility: hidden` 保留布局空间但隐藏可见性；`opacity: 0` 让已布局的盒子透明，但它仍可能接收焦点和指针输入。淡出只改变视觉效果；元素隐藏时还要管理焦点、输入和无障碍状态。

| Behavior | `display: none` | `visibility: hidden` | `opacity: 0` |
|---|---|---|---|
| Layout space | Removed | Reserved | Reserved |
| Pointer activation | No rendered box to hit | Hidden | Can still receive input; pair with a deliberate input policy |
| Keyboard focus | Not focusable while hidden | Not focusable while hidden | May remain focusable |
| Accessibility tree | Generally omitted | Generally omitted | Usually remains exposed; inspect control semantics |
| Visual interpolation | Display changes discretely | Visibility changes discretely | Opacity interpolates |
| Children | Not rendered | Inherit hidden visibility, though a child may override it | Paint as one group; a child cannot undo parent transparency |

The element's opacity is not inherited, but opacity composites the element and its descendants as a group. A child set to `opacity: 1` cannot make itself visible through a parent at zero opacity.

```css
.is-removed { display: none; }
.is-space-preserved { visibility: hidden; }
.is-faded-out { opacity: 0; pointer-events: none; }
```

`pointer-events: none` does not remove an element from keyboard focus or the accessibility tree. When a dialog or menu closes, also move or restore focus and update its accessible state; do not rely on opacity alone to make the control unavailable.

## Can `display` transition while showing an element?

`display` is not interpolated like opacity. CSS Transitions can opt into a discrete display transition in supporting browsers. A starting style defines the entry state, and `transition-behavior: allow-discrete` enables the discrete transition:

```css
.panel {
  display: none;
  opacity: 0;
  transition: opacity 180ms ease, display 180ms allow-discrete;
}

.panel.is-open {
  display: block;
  opacity: 1;
}

@starting-style {
  .panel.is-open {
    opacity: 0;
  }
}
```

Check target-browser support. Move focus and update accessible state as soon as the close action occurs; do not leave a transparent control interactive while waiting for `display` to switch. For a reduced-motion preference, shorten or remove nonessential movement and fades.

**Specifications:** [CSS Display](https://www.w3.org/TR/css-display-3/), [CSS Color transparency](https://www.w3.org/TR/css-color-4/#transparency), [CSS Transitions Level 2](https://www.w3.org/TR/css-transitions-2/#transition-behavior-property), and [Media Queries: reduced motion](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion).
