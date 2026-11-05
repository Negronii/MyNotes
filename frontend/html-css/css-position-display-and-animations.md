# How do CSS positioning and stacking determine where an element appears? / CSS 定位与堆叠如何决定元素的显示位置？

Positioning answers where a box is anchored and whether it occupies normal-flow space; stacking contexts answer which painted group is in front. `relative` and `sticky` preserve the element's flow slot, while `absolute` and `fixed` remove it from normal flow. A large `z-index` only competes inside its stacking context, so coordinates, flow, and paint order must be debugged separately. / 定位决定盒子的锚点及其是否占据普通流空间；堆叠上下文决定绘制的分组谁在前。`relative` 和 `sticky` 保留元素的流位置，`absolute` 和 `fixed` 则脱离普通流。很大的 `z-index` 也只在自身堆叠上下文内参与排序，因此应分别排查坐标、文档流和绘制顺序。

## Position values

| Value | In normal flow? | Position reference | Typical scroll behavior |
|---|---|---|---|
| `static` | Yes | Normal flow; inset offsets do not apply | Moves with document |
| `relative` | Yes; original space stays reserved | Its normal-flow position | Moves with document |
| `absolute` | No | Nearest ancestor establishing an absolute-position containing block; otherwise initial containing block | Follows that containing block |
| `fixed` | No | Nearest fixed-position containing block, often the viewport | Stays at that containing block as document scrolls |
| `sticky` | Yes | Nearest scrollport in the inset axis, constrained by its containing block | Moves until constrained by sticky inset |

`relative` offsets the box visually without moving siblings. It also establishes an absolute-position containing block for descendants:

```css
.card { position: relative; }
.card__badge { position: absolute; inset-block-start: 0; inset-inline-end: 0; }
```

An ancestor with non-`static` positioning commonly establishes the absolute containing block. Other properties, including some transforms and containment values, can establish containing blocks too. A fixed element usually tracks the viewport, but an ancestor with transform, perspective, filter, or relevant containment/`will-change` values can establish a fixed-position containing block; a supposedly fixed descendant may then move with that ancestor.

`sticky` remains in flow and sticks relative to the nearest scrollport when an inset such as `top: 0` is set. An ancestor's overflow can establish the relevant scroll container even when it does not visibly scroll, so inspect the scroll-container chain if sticky behavior differs from expectation. The containing block limits how far the sticky box can move.

## Stacking contexts and `z-index`

Within a stacking context, stacking rules order its child contexts. A descendant cannot use a larger `z-index` to escape the ancestor context and compete directly with an outside sibling.

```css
.shell { position: relative; z-index: 1; }
.dialog { position: absolute; z-index: 9999; }
.other { position: relative; z-index: 2; }
```

Here `.dialog` remains inside `.shell`'s stacking context; the outside `.other` context can paint above the whole shell. Raise the relevant ancestor's stacking position or move the dialog to a context that can compete at the needed level.

A positioned box with a non-`auto` `z-index` creates a stacking context. Fixed and sticky boxes also create one. Other common context creators include opacity below 1, transforms, filters, isolation, and some containment or `will-change` values. Check the property's own rules before assuming a stacking or containing-block effect.

| Question | Relevant model |
|---|---|
| Why did this sibling move or overlap? | Normal flow and containing blocks |
| Why did this large z-index stay underneath? | Stacking-context hierarchy |
| Why did a float not increase its parent's height? | Block formatting context; see [BFC and flow containment](./bfc-and-flow-containment.md) |

**Specification:** [CSS Positioned Layout Level 3](https://www.w3.org/TR/css-position-3/) defines position, insets, sticky scrollports, and stacking behavior. See [BFC and flow containment](./bfc-and-flow-containment.md) for the separate flow boundary; [CSS visibility](./css-visibility-and-accessibility.md) for hidden-state effects; [CSS transitions and animations](./css-transitions-and-animations.md) for motion and profiling; and [rendering pipeline and forced layout](./rendering-pipeline-and-forced-layout.md) when a style change affects layout or paint.
