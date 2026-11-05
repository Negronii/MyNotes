# Which CSS units and responsive layout rules fit the available space? / 哪些 CSS 单位与响应式布局规则适合当前空间？

Choose a unit by its reference: CSS pixels for a stable CSS-space length, percentages for a property-specific containing-block relationship, font-relative units for text-scaled dimensions, and viewport units for viewport-sized regions. Choose the responsive layout mechanism by what the component can measure: Grid's intrinsic tracks for content-driven columns, media queries for viewport conditions, and container queries when a component should react to its own allocated width. / 根据参照选择单位：固定 CSS 空间尺寸使用 CSS 像素，容器关系使用百分比，随文字缩放的尺寸使用字体相对单位，视口区域使用视口单位。再根据布局约束选择响应式机制：内容驱动的列可用 Grid 内在轨道，视口条件可用媒体查询，组件需要响应自身可用宽度时可用容器查询。

## What does each unit measure?

| Unit | Reference | Useful for | Watch for |
|---|---|---|---|
| `px` | CSS reference pixel | Borders and precise spacing | It is not necessarily one physical device pixel |
| `%` | A reference defined by the property | Fluid sizes and offsets | Different properties can use different percentage bases |
| `em` | Usually the element's computed font size; on `font-size`, the inherited size | Spacing that should scale with text | Nested font-size declarations can compound |
| `rem` | Root element's font size | Consistent text-relative sizing across components | A fixed root size can ignore user text preferences |
| `vw` / `vh` | Large viewport dimensions | Viewport-relative sizing | Viewport is not always the available content box |
| `svh` / `lvh` / `dvh` | Small, large, and dynamic viewport heights | Full-height mobile UI with an explicit browser-chrome policy | Dynamic viewport dimensions can change as browser UI changes |
| `vmin` / `vmax` | Smaller / larger viewport dimension | A shape that should adapt to orientation | It chooses one viewport axis relationship, not a content width |

A CSS pixel is a reference unit. Browser zoom and device-pixel ratio affect how CSS lengths map to output pixels; writing `1px` does not promise a one-device-pixel stroke. For a property such as `width`, a percentage is generally resolved against a containing block; the percentage basis for other properties is defined separately. `em` usually follows the element's font size for non-`font-size` properties, while its own `font-size` resolves against the inherited font size. `rem` follows the root element.

The default `vh` corresponds to the large viewport. On devices with retractable browser controls, a `100vh` region can extend behind those controls. Use `svh` when fitting the small viewport matters or `dvh` when following the changing viewport matters. See [CSS Values and Units, viewport-relative lengths](https://www.w3.org/TR/css-values-4/#viewport-relative-lengths).

## How should a layout adapt?

| Constraint | Starting point | Example |
|---|---|---|
| Component responds to the viewport | Media query | Change design tokens at a breakpoint |
| Component responds to its own available width | Container query | Reflow a card within a sidebar or grid |
| Repeating columns should fit content without a fixed breakpoint | Intrinsic Grid sizing | `repeat(auto-fit, minmax(...))` |

A content-driven card grid can fit as many columns as the available width allows:

```css
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 1rem;
}
```

A component can instead respond to the width of its query container:

```css
.card-grid { container-type: inline-size; }

@container (width > 28rem) {
  .card { display: grid; grid-template-columns: 1fr 2fr; }
}
```

For site-wide tokens, define the breakpoint in one place and reuse the values:

```css
:root { --columns: 1; --gap: 0.5rem; }

@media (min-width: 48rem) {
  :root { --columns: 2; --gap: 1rem; }
}

.cards {
  display: grid;
  grid-template-columns: repeat(var(--columns), minmax(0, 1fr));
  gap: var(--gap);
}
```

Use the available containing block for ordinary full-width content. A child with `width: 100vw` can overflow when the viewport width includes a classic scrollbar while the content box does not. Grid's track choice and intrinsic minimums are covered in [Flexbox and Grid layout](./flex-and-grid-layout.md).

## When does a CSS hairline mean one device pixel?

A `1px` border is one CSS pixel; the output can cover more than one device pixel depending on device-pixel ratio, zoom, OS scaling, and subpixel alignment. At an effective 2× scale, a half-CSS-pixel painted line is nominally one device pixel, but rasterization and alignment still vary. Treat fractional widths as a visual technique to test on target devices, not a physical-pixel guarantee.

```css
.box { position: relative; }

.box::before {
  content: "";
  position: absolute;
  inset-inline: 0;
  bottom: 0;
  height: 1px;
  background: #d9d9d9;
  transform: scaleY(0.5);
  transform-origin: 0 100%;
}
```

For rounded edges, a fractional shadow is another technique to test:

```css
.box { box-shadow: 0 0 0 0.5px #d9d9d9; }
```

Both techniques depend on output scale and alignment. SVG also rasterizes to device pixels; it does not ensure a physical-pixel stroke.

**Specifications:** [CSS Values and Units Level 4](https://www.w3.org/TR/css-values-4/) defines reference pixels, font-relative and viewport-relative lengths; [CSSOM View](https://www.w3.org/TR/cssom-view-1/) defines `devicePixelRatio`; [CSS Containment Level 3](https://www.w3.org/TR/css-contain-3/#container-queries) defines size container queries; [CSS Grid Level 2](https://www.w3.org/TR/css-grid-2/) defines intrinsic track sizing.
