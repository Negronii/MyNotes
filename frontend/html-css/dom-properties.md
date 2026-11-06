# 哪些网页几何接口能测量哪一种盒子？

Document Object Model（文档对象模型，DOM）提供多组几何 API，它们测量的盒子和坐标系不同。读布局偏移尺寸（`offset*`）或内客户区尺寸（`client*`），读滚动范围与偏移（`scroll*`），读包含 CSS transform（变换）后的视口矩形则用 `getBoundingClientRect()`（获取包围矩形）。一次几何读取可能迫使浏览器先完成尚未更新的样式或布局，但值已是最新时不一定产生新布局。

```text
┌────────────────────────── margin ──────────────────────────┐
│ ┌────────────────────── border ─────────────────────────┐ │
│ │ ┌────────────────── padding ───────────────────────┐  │ │
│ │ │ ┌────────────── content ──────────────────────┐  │  │ │
│ │ │ └────────────────────────────────────────────┘  │  │ │
│ │ └─────────────────────────────────────────────────┘  │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## 先按测量目标选择属性

| API | 返回内容 | 不包含或需留意 |
| --- | --- | --- |
| `offsetWidth` / `offsetHeight` | 整数布局尺寸，含 padding、border 和占空间的滚动条 | 不含 margin；不反映 CSS transform |
| `clientWidth` / `clientHeight` | padding 区域尺寸 | 不含 border 和占空间的滚动条 |
| `scrollWidth` / `scrollHeight` | 滚动区域尺寸，包含溢出的内容 | 不含 border；不是“用户一定能滚动”的保证 |
| `scrollLeft` / `scrollTop` | 当前滚动偏移 | 可写；某些布局中数值可为小数或超出熟悉范围 |
| `offsetLeft` / `offsetTop` | 相对 `offsetParent`（偏移父元素）的边缘位置 | 它不一定是直接父元素或最近定位祖先 |
| `getBoundingClientRect()` | 相对视口、包含 transform 后的边框矩形联合范围 | 不含 margin；返回读取时的快照 |

这些数字使用 CSS 像素，不是设备物理像素。占空间的滚动条会改变布局测量，覆盖式滚动条则可能不占空间；这取决于平台及浏览器设置。

## 用固定数字对照布局尺寸

假设一个内容盒宽 `320px`，左右 padding 各 `16px`，左右 border 各 `1px`，没有占空间的滚动条：

~~~css
.content-box {
  box-sizing: content-box;
  width: 320px;
  padding-inline: 16px;
  border: 1px solid;
}
~~~

> [!example] 内容盒尺寸的计算
> `offsetWidth = 320 + 16×2 + 1×2 = 354px`；`clientWidth = 320 + 16×2 = 352px`。前者含边框，后者含 padding 但不含边框。

把声明宽度改为 `box-sizing: border-box; width: 320px`，则内容宽度为 `320 − 16×2 − 1×2 = 286px`；在同样无滚动条的条件下，`clientWidth = 318px`、`offsetWidth = 320px`。

## 读滚动区域与当前偏移

`scrollHeight` / `scrollWidth` 表示滚动区域尺寸。溢出内容可能使它大于可见的 `clientHeight` / `clientWidth`：

~~~javascript
const hasVerticalOverflow = element.scrollHeight > element.clientHeight;
const currentY = element.scrollTop;
element.scrollTop = 0; // 回到顶部
~~~

`scrollTop` 和 `scrollLeft` 可写。反向书写方向、弹性滚动及缩放等情形会使数值不符合“非负整数”的简单假设。

在 standards mode（标准模式）下，根元素 `document.documentElement.scrollHeight` 特别返回视口滚动区域高度与视口高度的较大值；`clientHeight` 则是扣除占空间滚动条后的视口高度。对普通元素，`scrollHeight` 返回其自身滚动区域高度。

## offset 相对哪个父元素？

`offsetParent`（偏移父元素）由同名属性给出。`offsetTop` / `offsetLeft` 描述元素边框边缘相对该父元素 padding 边缘的位置；表格结构、固定定位、包含块和 Shadow DOM（影子 DOM）边界等都会影响返回的父元素。它不固定等同于最近的 `position` 祖先。

## 读变换后的视口矩形

`getBoundingClientRect()` 返回元素非空 client rect（客户端矩形）的最小包围矩形，坐标原点在当前视口左上角，尺寸受 transform 影响。行内内容跨多行时可能有多个 client rect，方法返回它们的联合矩形；结果是本次读取时的 DOMRect（DOM 矩形）快照。

~~~javascript
const rect = element.getBoundingClientRect();
// rect.top / bottom：相对视口顶部的上下边缘
// rect.left / right：相对视口左侧的左右边缘
// rect.width / height：变换后边框盒联合范围，单位为 CSS px
~~~

~~~text
视口左上角 (0, 0)
┌──────────────────────────────────────────────┐
│          ┌────── rect.left ──────┐            │
│          │ 元素 transform 后的外接矩形 │            │
│          └────────────────────────┘            │
└──────────────────────────────────────────────┘
~~~

以矩形判断是否与视口相交，只能说明几何区域有正面积交叠，无法判断元素是否被其他内容遮挡、是否透明或辅助技术是否可见。`getBoundingClientRect()` 对退化的零宽或零高元素也可能返回矩形，因此必须单独检查宽高。下面假设文档处于 standards mode；根元素的 `clientWidth`/`clientHeight` 表示扣除占空间滚动条后的视口尺寸。

~~~javascript
function overlapsViewport(element) {
  const rect = element.getBoundingClientRect();
  const root = document.documentElement;
  return rect.width > 0 && rect.height > 0 &&
    rect.bottom > 0 && rect.top < root.clientHeight &&
    rect.right > 0 && rect.left < root.clientWidth;
}
~~~

## 把写入和读取分批

偶尔读取一次几何属性时，选与问题相符的盒子和坐标系。滚动阈值通知或图片延迟加载优先使用 IntersectionObserver（相交观察器）[图片加载中的观察器示例](../browser-apis/image-lazy-loading.md)，而不是反复轮询矩形；观察器会异步报告相交状态，但不承诺完全不触发布局工作。

若先改样式再马上读几何值，浏览器可能同步完成待处理的样式或布局；循环交替执行写入和读取会重复付出这类成本。有关批量读取、批量写入的路径见[渲染流水线与强制布局](./rendering-pipeline-and-forced-layout.md)。

> [!info]- 来源
> - 元素布局尺寸、滚动 API、视口矩形：W3C CSSOM View，Working Draft（2025-09-16），[CSSOM View](https://www.w3.org/TR/cssom-view-1/)，检查于 2026-11-06。其中 [Element.scrollHeight](https://www.w3.org/TR/cssom-view-1/#dom-element-scrollheight) 说明根元素和普通元素的滚动高度规则。
> - 异步相交通知：W3C [Intersection Observer](https://www.w3.org/TR/intersection-observer/)，Working Draft（2023-10-18），检查于 2026-11-06。
