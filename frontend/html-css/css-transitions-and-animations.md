# When should CSS use a transition or a keyframe animation? / CSS 应在何时使用 transition 或关键帧动画？

A transition interpolates between two computed states after a property change, such as a hover or class toggle. A keyframe animation defines a sequence that can start independently, repeat, reverse, pause, or fill after its last keyframe. Prefer a transition for a simple state change; use keyframes for a multi-step or looping sequence. Respect reduced-motion preferences, and profile the actual effect instead of assuming a property is free to animate. / transition 在属性变化后于两个计算状态之间插值，例如 hover 或 class 切换。关键帧动画定义一段可独立启动、重复、反向、暂停或保留结束状态的序列。简单状态变化优先 transition；多阶段或循环序列使用关键帧。尊重减少动态效果偏好，并针对真实效果做性能分析，不要假定某属性动画没有成本。

## Transitions: move between states

```css
.button {
  background-color: navy;
  transition: background-color 180ms ease-out;
}

.button:hover {
  background-color: royalblue;
}
```

| Property | Role |
|---|---|
| `transition-property` | Which properties to transition, such as `opacity` or `transform` |
| `transition-duration` | Length of the interpolation |
| `transition-timing-function` | Easing curve, such as `ease-out` or `cubic-bezier(...)` |
| `transition-delay` | Wait before starting |

When multiple properties use different durations or delays, list their values in corresponding order:

```css
.card {
  transition-property: transform, opacity;
  transition-duration: 300ms, 200ms;
  transition-timing-function: ease-out, linear;
  transition-delay: 0ms, 100ms;
}
```

## Keyframes: define intermediate motion

```css
@keyframes slide-in {
  0%   { transform: translateX(-100%); }
  50%  { transform: translateX(10%); }
  100% { transform: translateX(0); }
}

.panel {
  animation: slide-in 420ms ease-out both;
}
```

| Property | Role |
|---|---|
| `animation-name` | Select the `@keyframes` rule |
| `animation-duration` | Length of one cycle |
| `animation-timing-function` | Easing for the cycle or keyframe segment |
| `animation-delay` | Wait before the first cycle |
| `animation-iteration-count` | Number of cycles or `infinite` |
| `animation-direction` | `normal`, `reverse`, `alternate`, or `alternate-reverse` |
| `animation-fill-mode` | Whether keyframe values apply before/after active motion |
| `animation-play-state` | `running` or `paused` |

CSS transforms can translate, rotate, and scale a box:

| Function | Effect |
|---|---|
| `translate(x, y)`, `translateX(x)`, `translateY(y)` | Move in 2D |
| `translateZ(z)`, `rotateX/Y/Z(angle)` | Move or rotate in 3D |
| `rotate(angle)` | Rotate in 2D |
| `scale(x, y)`, `scaleX(x)`, `scaleY(y)` | Resize visually |

```css
.card { transform: translate(10px, 20px) rotate(5deg) scale(1.05); }
```

## What does animation cost?

A change can require style recalculation, layout, paint, rasterization, and compositing. Animating `transform` or `opacity` can let an engine update presentation without repeating layout, but neither guarantees compositor-only or GPU work. Consult a trace and the [rendering pipeline](./rendering-pipeline-and-forced-layout.md) for the observed invalidation path.

`will-change` is a hint, not a command to promote a layer. Some hints can consume memory or change stacking/containing-block behavior. Use it only on a small region after profiling shows it helps, then remove the hint when no longer needed. `transform: translateZ(0)` is not a universal GPU switch and may affect stacking and containing blocks.

```css
@media (prefers-reduced-motion: reduce) {
  .panel,
  .card {
    animation-duration: 0.01ms;
    animation-iteration-count: 1;
    transition-duration: 0.01ms;
  }
}
```

This example reduces duration for selected motion. Choose a treatment that preserves necessary state feedback and avoids unexpected movement; not all motion should be removed indiscriminately.

**Specifications:** [CSS Transitions Level 2](https://www.w3.org/TR/css-transitions-2/), [CSS Animations Level 1](https://www.w3.org/TR/css-animations-1/), [CSS Transforms Level 1](https://www.w3.org/TR/css-transforms-1/), [CSS Will Change](https://www.w3.org/TR/css-will-change-1/), and [Media Queries: reduced motion](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion).
