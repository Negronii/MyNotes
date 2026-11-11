# 雪碧图如何显示局部图片，横幅示例说明什么？

CSS Sprite（雪碧图）把小图排在同一张图集中，再移动背景图，只让目标区域出现在小盒子内。以一张按 `64 × 32 CSS px` 显示、每格 `16 × 16` 的图集为例：第二行第三列的左上角是 `(32, 16)`。在没有 padding 或 border 的 `16 × 16` 盒子中，设 `background-repeat: no-repeat`，并把背景定位为 `-32px -16px`，就会露出这一格。负值移动的是整张背景图，不是让元素本身向左上移动。缩放图集时，格子大小和偏移也要按同一比例调整。

图集坐标图与完整 CSS 见[CSS Sprite 怎样裁出图集中的一格](../../../../frontend/performance/css-sprites-and-image-caching.md#css-sprite-怎样裁出图集中的一格)。选择图集、独立图片还是 SVG，要同时比较资源复用、传输与更新成本；图集并不自动更快。

下方是旧横幅页面的静态截图：左侧有一项青绿色高亮的分类导航，右侧是中秋主题横幅和左右箭头。它不是上述图集；截图只能展示布局，不能说明箭头实际可操作。

![旧横幅页面截图：分类导航和中秋主题横幅，仅作静态布局参考](banner.png)

另一个独立的[报表横幅显示例子](../../../../frontend/performance/css-sprites-and-image-caching.md#旧横幅图展示的是静态选中项)用 CSS 隐藏普通横幅，只显示带 `.current` 的一张；它不是这张旧截图的源码，也不控制截图左侧的分类高亮。这个类名是示例约定，本身没有浏览器内置行为。真正切换时还要由交互逻辑更新选中项。只有显示规则，还没有实现轮播的切换与键盘操作；若加入自动轮播，还需要停止和恢复轮播的控制。图片的实际尺寸与加载时机可接着看[图片与媒体资源加载](../../../../frontend/browser-apis/image-lazy-loading.md)。

> [!info]- 来源
> - 背景定位、重复与缩放：[CSS Backgrounds and Borders Level 3 §2.4、§2.6、§2.9](https://www.w3.org/TR/css-backgrounds-3/#the-background-position)，Candidate Recommendation Draft，2024-03-11；核对于 2026-11-12。
> - 轮播的操作与焦点要求：[WAI-ARIA APG Carousel Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/carousel/)，核对于 2026-11-12。横幅原图保持不变，只用于说明已有静态布局。
