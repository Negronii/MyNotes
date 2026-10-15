**HTML and CSS Basics / HTML 与 CSS 基础**

A compact reference for five CSS foundations that show up constantly in interviews: units, selectors/specificity, responsive techniques, inheritance, and text-overflow tricks. Reach for this when you need to refresh the vocabulary — for mechanism-heavy deep dives, cross-links are at the end of each section.

**中文：** 重点区分单位及其参照、级联优先级、属性继承、文本截断与语义 HTML 的职责边界。

## CSS Units — which to use when

| Unit | Relative to | Use for | Avoid for |
|---|---|---|---|
| `px` | CSS reference pixels | borders, precise spacing, sizing | treating them as device pixels |
| `%` | property-specific reference, often a containing block | fluid sizing | assuming every percentage uses the parent's width |
| `em` | parent `font-size` (or own, for non-`font-size`) | spacing relative to text | deep nesting (compounds) |
| `rem` | root `font-size` | scalable UIs, most typography | fine-grained per-component control |
| `vw` / `vh` | default (large) viewport size | viewport-relative layout | assuming `100vw` always equals the content box |
| `svh` / `lvh` / `dvh` | small / large / dynamic viewport height | choose based on browser UI behavior | assuming they are interchangeable |
| `vmin` / `vmax` | smaller / larger viewport dim | keeping elements square across orientations | anything that needs a single axis |

Usage notes:

- **`px`** — a CSS reference pixel, not necessarily one physical/device pixel. Page zoom and `devicePixelRatio` affect how CSS pixels map to the output surface; CSS px itself doesn't prevent page zoom.
- **`%`** — its reference depends on the property. For `width`, it is generally based on the containing block's width; percentages in other properties can resolve differently or remain unresolved until layout.
- **`em`** — for most properties, relative to the element's computed font size; in `font-size`, relative to the inherited font size. It compounds when nested font sizes are set in `em`.
- **`rem`** — relative to the root element's font size. Avoid resetting the root to a fixed pixel size when a design should follow user font preferences.
- **`100vw`** — viewport units are based on the viewport, not necessarily the available content box; classic scrollbars and root overflow settings can make a `100vw` child overflow horizontally. Use the containing block's `width: 100%` for ordinary full-width content.
- **`vh`** — the default `vh` maps to the large viewport. On devices with retractable browser UI it can extend behind that UI. `svh` fits the small viewport; `dvh` follows dynamic UI and can resize while scrolling.
- **`vmin` / `vmax`** — `50vmin` always references the smaller dimension, useful for square elements that adapt to orientation.

## CSS Selectors — specificity and performance

### Selector specificity

For selector specificity, compare the ID, class/attribute/pseudo-class, and type/pseudo-element columns from left to right. The cascade resolves origin, importance, context, attached styles, and cascade layer before specificity; specificity is not the only priority rule. Inline `style` attributes have a separate precedence step for declarations of the same importance.

For a simple author-style-sheet comparison, the tuple `(id, class, type)` is compared left-to-right: `(1, 0, 0)` > `(0, 2, 0)` even if the second selector has more classes. The universal selector (`*`) and combinators (`>`, `+`, `~`) carry zero specificity. `:not()`, `:is()`, and `:has()` take the specificity of their most specific argument; `:where()` contributes zero.

**Specificity battle example:**

```css
/* Specificity: (1, 1, 0) — wins, because ID weight dominates */
#sidebar .menu-item { color: red; }

/* Specificity: (0, 3, 0) — loses, even with more classes */
.menu .menu-item.active { color: blue; }
```

More classes don't overcome a single ID within the same cascade context. Importance, layer order, and origin can still decide which declaration participates.

**`:not()` detail:** `:not()` itself adds no specificity; its most-specific argument does. `div:not(.sidebar)` is `(0, 1, 1)` (class + element).

### Performance and maintainability tactics

- **Attribute selectors** — `[data-state="active"]` lets CSS react to JS state without class juggling.
- **BEM** (`.block__element--modifier`) — flat specificity, trivially overridable by a more specific class.
- **Cascade layers (`@layer`)** — organize styles (`@layer reset, components, utilities;`). For normal declarations, later layers win and unlayered author rules outrank layered author rules; for `!important`, layer order reverses. Specificity still matters within the winning layer.
- **CSS-in-JS** (styled-components, Emotion) — often generates classes, but it still participates in the same cascade and specificity rules.
- **Critical CSS** — inlining genuinely critical styles can reduce a render-blocking stylesheet dependency, but it adds bytes to HTML and should be measured against caching and delivery costs.

## Responsive design beyond media queries

Media queries still work, but modern CSS gives cleaner options for common cases:

- **Container queries** — style based on *container* size, not viewport. Lets a component respond to the space it's given, which is what you usually want inside a grid.

  ```css
  .card { container-type: inline-size; }

  @container (width > 400px) {
    .card { display: grid; grid-template-columns: 1fr 2fr; }
  }
  ```

- **Intrinsic sizing with Grid** — `minmax()` + `auto-fit` reflows without any media queries.

  ```css
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  }
  ```

- **CSS variables redefined per breakpoint** — the breakpoint lives in one place, and every element reacts to the change automatically.

  ```css
  :root { --columns: 1; --gap: 8px; }

  @media (min-width: 768px) {
    :root { --columns: 2; --gap: 16px; }
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(var(--columns), 1fr);
    gap: var(--gap);
  }
  ```

**See also:** [`2.3 Flex & Grid Layout`](./flex-and-grid-layout.md) for the full Grid / Flexbox reference.

## Semantic HTML and accessibility / 语义化 HTML 与无障碍交互

Choose elements for their meaning and built-in behavior. Use headings to express the page outline, landmarks such as `<main>` and `<nav>` to identify regions, a `<button>` for an action, and an `<a href>` for navigation. Semantic controls provide keyboard and assistive-technology behavior that a styled `<div>` does not provide by default.

Give form controls programmatic labels with `<label for="…">` or a properly nested label. Give informative images useful alternative text; use `alt=""` for decorative images so they do not add noise to the text alternative. Do not use color or visual positioning as the only way to convey a required state or relationship.

Keep the source order meaningful. CSS can change visual placement without changing the underlying document sequence used by nonvisual presentation.

### Keyboard, focus, and validation feedback / 键盘、焦点与校验反馈

**Core answer / 核心回答：** Start with native HTML controls: a label gives an input its accessible name, and native buttons and fields already support expected focus and keyboard behavior. Keep keyboard focus visible. Describe errors in text, associate the text with its field using `aria-describedby`, and expose the invalid state with `aria-invalid`. ARIA adds meaning for assistive technology; it does not add focusability, keyboard activation, or validation behavior to a generic element. / 优先使用原生 HTML 控件：标签提供输入框的无障碍名称，原生按钮和表单字段自带预期的焦点与键盘行为。键盘焦点应清晰可见。错误要用文字说明，通过 `aria-describedby` 与字段关联，并用 `aria-invalid` 表达错误状态。ARIA 为辅助技术补充语义，但不会让普通元素自动获得焦点、键盘操作或校验行为。

This form keeps native constraints as the no-JavaScript fallback. Once its custom handler is installed, an invalid submission shows a text error, marks the field, and focuses it; the visible outline identifies where the keyboard user landed. The same error text is in the field's accessible description.

```html
<form id="subscribe" action="/subscribe" method="post">
  <label for="email">Email address</label>
  <input id="email" name="email" type="email" required
         aria-describedby="email-help email-error">
  <p id="email-help">Enter an address such as name@example.com.</p>
  <p id="email-error" hidden></p>
  <button type="submit">Subscribe</button>
</form>

<style>
  :focus { outline: 3px solid currentColor; outline-offset: 2px; }
</style>

<script>
const form = document.querySelector("#subscribe");
const email = form.elements.namedItem("email");
const error = document.querySelector("#email-error");

function clearError() {
  error.textContent = "";
  error.hidden = true;
  email.removeAttribute("aria-invalid");
}

email.addEventListener("input", () => {
  if (email.validity.valid) clearError();
});

form.addEventListener("submit", event => {
  if (email.validity.valid) {
    clearError();
    return;
  }

  event.preventDefault();
  error.textContent = email.validity.valueMissing
    ? "Enter an email address."
    : "Enter a valid email address.";
  error.hidden = false;
  email.setAttribute("aria-invalid", "true");
  email.focus();
});
form.noValidate = true; // use the custom path only after its handler is ready
</script>
```

Without JavaScript, the browser's `required` and `type="email"` constraints remain active. With JavaScript, Tab reaches the field and then the submit button; submitting an invalid value by keyboard returns focus to the field and exposes the associated error. Clear the error as the value becomes valid, and validate again on the server before accepting submitted data. This is a focused interaction pattern, not a conformance claim for an entire page.

## Inherited CSS properties

Some properties cascade to children by default; most do not. Knowing the short list saves you from reaching for `inherit` unnecessarily.

**Inherited by default:**

- **Font** — `font-family`, `font-size`, `font-style`, `font-weight`, `line-height`
- **Text formatting** — `text-align`, `text-indent`, `text-transform`, `text-shadow`
- **Spacing** — `letter-spacing`, `word-spacing`
- **Visibility** — `visibility`

Most layout / box-model properties (`margin`, `padding`, `border`, `width`, `height`, `display`, `position`) do **not** inherit; they usually apply to the element's own box.

`text-decoration` is not inherited. A decoration drawn by an ancestor can continue across descendant text, which can make it look inherited; changing the child's `text-decoration` does not simply override the ancestor's line.

## Truncating text with ellipsis

### Single-line truncation

```css
.box {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100px;
}
```

All three properties are needed: `nowrap` keeps text on one line, `overflow: hidden` hides the spill, `text-overflow: ellipsis` paints the `…`.

### Multi-line truncation

```css
.box {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
  width: 100px;
}
```

This is the legacy `-webkit-line-clamp` form, with the `-webkit-box` display and orientation declarations required by that syntax. CSS Overflow Module Level 4 specifies a `line-clamp` shorthand and also describes the legacy form for compatibility, but remains a Working Draft; check the exact behavior and support in target browsers before choosing a form.

**Specifications / guidance:** [HTML Standard](https://html.spec.whatwg.org/), [CSS Values and Units](https://www.w3.org/TR/css-values/), [CSS Selectors](https://www.w3.org/TR/selectors-4/), [CSS Cascading and Inheritance](https://www.w3.org/TR/css-cascade-5/), [CSS Display and visual ordering](https://www.w3.org/TR/css-display-3/#order-property), [CSS Text Decoration](https://www.w3.org/TR/css-text-decor-3/), [CSS Overflow Level 4](https://www.w3.org/TR/css-overflow-4/), [WAI page structure](https://www.w3.org/WAI/tutorials/page-structure/), [WAI form labels](https://www.w3.org/WAI/tutorials/forms/labels/), and [WAI image alternatives](https://www.w3.org/WAI/tutorials/images/).

**Accessibility sources checked 2026-10-15:** [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/) (including visible focus and text error identification), [WAI Forms: Notifications](https://www.w3.org/WAI/tutorials/forms/notifications/), [ARIA Authoring Practices Guide: Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/), and [ARIA Authoring Practices Guide: Read Me First](https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/) (ARIA 1.2 role and behavior guidance).
