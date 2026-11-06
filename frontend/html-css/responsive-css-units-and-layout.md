# 哪些 CSS 单位与响应式布局规则适合当前空间？

单位先问“相对于什么”，断点再问“谁的尺寸或状态改变时需要重排”。报表页面通常用内容容器宽度和内在轨道适配列；媒体查询响应视口或用户偏好；容器查询让放在侧栏、主栏等不同区域的卡片按自身可用宽度调整。

## 常见尺寸单位各自参照什么？

| 单位 | 参照 | 常见用途 | 需要记住的边界 |
| --- | --- | --- | --- |
| <code>px</code> | CSS reference pixel | 边框、精确间距 | 不保证等于一个物理设备像素 |
| <code>%</code> | 属性定义的参照盒 | 流动宽度、偏移 | 每个属性的百分比基准需分别确认 |
| <code>em</code> | 通常是元素计算后的字号；用于 <code>font-size</code> 时参照继承字号 | 随文字缩放的局部间距 | 嵌套字号会复合 |
| <code>rem</code> | 普通声明和容器查询中取根元素计算字号；媒体查询中取初始字号 | 跨组件的一致文字相对尺寸 | 固定根字号会影响用户文字偏好；媒体断点按另一基准解析 |
| <code>vw</code> / <code>vh</code> | large viewport 的宽、高，即动态地址栏或工具栏收起时的视口 | 视口区域 | 视口不是普通内容盒；可能大于浏览器界面展开时的可见区 |
| <code>svh</code> / <code>lvh</code> / <code>dvh</code> | 小、大、动态视口高度 | 移动端全高界面 | 需选择是否随浏览器工具栏伸缩 |
| <code>vmin</code> / <code>vmax</code> | 视口短边 / 长边 | 随方向变化的形状 | 不表示内容容器宽度 |

例如根字号为浏览器默认的 <code>16px</code> 时，<code>1.5rem = 24px</code>；若显式把根字号设为 <code>20px</code>，则 <code>5rem = 100px</code>。<code>em</code> 在嵌套字号上可能逐层相乘；<code>rem</code> 统一参照根字号。固定根字号可能覆盖用户对基础文字大小的偏好，因此除非产品有明确缩放策略，通常保留浏览器根字号。CSS <code>1px</code> 是参考像素：缩放、设备像素比和栅格对齐都会影响最终绘制到多少个设备像素。

<code>100vw</code> 按视口宽度计算，在传统占位滚动条环境下可能比内容区宽，从而出现横向溢出。若目标是填满内容区，通常让块容器 <code>width: 100%</code> 或保持 <code>width: auto</code>，再由父级布局分配可用空间；若元素同时有 padding 或 border，使用 <code>box-sizing: border-box</code> 避免内容宽度之外再加边缘。

## 断点由视口还是组件决定？

| 需要响应的变化 | 起点 | 报表中的例子 |
| --- | --- | --- |
| 整个页面可用宽度或方向变化 | <code>@media</code> | 小视口将侧栏移到筛选表单上方 |
| 卡片自身分配宽度变化 | <code>@container</code> | 同一查询卡片在主栏横排，在窄侧栏竖排 |
| 重复卡片依内容自动换列 | Grid 内在轨道 | 可放几列就排几列，不硬编码设备名 |

桌面断点应服务于内容，不是按“手机/平板/桌面”名称机械设置。报表外框的侧栏与主栏在 <code>48rem</code> 及以下改为单列：

~~~css
.report-layout {
  display: grid;
  grid-template-columns: 14rem minmax(0, 1fr);
  gap: 1rem;
}

@media (max-width: 48rem) {
  .report-layout { grid-template-columns: minmax(0, 1fr); }
}
~~~

在媒体查询中，`rem` 按浏览器默认字号或用户字号偏好确定的初始值解析。按默认 `16px` 计算，`48rem = 768px`，`max-width` 包含等号；即使页面写了 `html { font-size: 20px; }`，这个视口断点仍为 `768px`，不是 `960px`。

若筛选栏按面板自身宽度重排，先建立 inline-size query container，再由容器宽度决定样式。为单独观察轨道，这里只取月份、地区和提交按钮三个项目；每个 label 包含自己的控件，使它们作为一组参与 Grid 布局，状态复选框不在这个精简例中：

~~~html
<section class="report-panel">
  <form class="report-filter" action="/reports" method="get">
    <label>月份 <input name="month" type="month" value="2026-10"></label>
    <label>地区
      <select name="region">
        <option value="">全部地区</option>
        <option value="north">北区</option>
      </select>
    </label>
    <button type="submit">筛选报表</button>
  </form>
</section>
~~~

~~~css
.report-panel { container-type: inline-size; }
.report-filter {
  display: grid;
  grid-template-columns: 1fr;
}

@container (inline-size > 30rem) {
  .report-panel > .report-filter {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    align-items: end;
  }
}
~~~

规则选中 `.report-filter`；它沿祖先查找合格查询容器，由 `.report-panel` 提供尺寸。按根字号 `16px`，面板内容盒宽 `480px` 时仍用基础单列样式，`481px` 才改为三列；普通声明和容器查询里的 `rem` 使用根元素计算字号。若根字号改为 `20px`，这个容器阈值成为 `600px`。建立尺寸查询容器也会改变其尺寸计算约束，使用前应确认组件的布局用途。

## 用内容和实际宽度决定响应规则

以前端设计稿为 <code>1000px</code> 画布为例，某个图标宽 <code>200px</code> 对应 <code>200 / (1000 / 100) = 20vw</code>。这只是在该设计宽度下的换算；若图标在窄屏仍需保持可读尺寸，<code>20vw</code> 会继续缩小，通常应该用有上下限的 <code>clamp()</code>，或让布局在内容放不下时重排。

~~~css
.report-title { font-size: clamp(1.25rem, 2vw + 0.75rem, 2rem); }
~~~

根字号为 `16px` 时，这个式子分别在视口宽 `400px`、`600px`、`1200px` 得到 `20px`、`24px`、`32px`：两端值触及 `clamp()` 的下限和上限，中间值按视口连续变化。

不需要连续缩放时，用媒体查询表达台阶变化；需要适配组件大小时，用容器查询；内容自身适合决定列数时，可让 Grid 的最小轨道和最大轨道参与计算。相关固定轨道和内在最小尺寸见[Flexbox 与 Grid 布局](./flex-and-grid-layout.md)。

## 受限文本与行数裁切

单行省略号要同时满足：盒子有确定的可用宽度、文字不换行、溢出被裁切。<code>text-overflow</code> 只请求省略符号，不会替你限制宽度或隐藏溢出。Flex/Grid 直接子项目有自动最小尺寸；当裁切放在内层文字上时，外层项目可能需要 <code>min-inline-size: 0</code> 才会缩到轨道宽度。

~~~css
.toolbar { display: flex; }
.toolbar > .report-name {
  flex: 1 1 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
~~~

这里的 `overflow: hidden` 写在直接 Flex 项目上，会让自动主轴最小尺寸为零，因此无需再写 `min-inline-size: 0`。若把裁切改到项目内部的子元素，就在直接项目上设置该最小尺寸，允许它缩小后再由内层文字显示省略号。

多行摘要可用目标浏览器支持的行数裁切形式；若使用兼容语法，目标浏览器仍需验证：

~~~css
.report-summary {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}
~~~

裁切改变可见部分，不会删除文本值。关键信息应提供阅读或复制完整内容的办法；不要把省略号当作唯一披露方式。

## 细边框何时等于一个设备像素？

<code>1px</code> 是一个 CSS 像素，效果不必是一条物理设备像素宽的线。有效缩放约为 <code>2×</code> 时，<code>0.5 CSS px</code> 名义上接近一个设备像素，但最终栅格化还受对齐与缩放影响。分数线和阴影是视觉技巧，应在目标设备检查。

~~~css
.hairline {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
~~~

> [!info]- 来源
> - CSS reference pixel、字体相对单位和视口相对单位：W3C CSS Values and Units Level 4，§6，Working Draft（2024-03-12）：[CSS Values and Units](https://www.w3.org/TR/css-values-4/)，检查于 2026-11-06。
> - 媒体查询中 <code>rem</code> 的初始字号基准：W3C Media Queries Level 5，§1.3，Working Draft（2026-02-19）：[Media Queries Level 5](https://www.w3.org/TR/mediaqueries-5/#units)，检查于 2026-11-06。
> - 容器查询与 <code>@container</code>：W3C CSS Conditional Rules Level 5，§5，Working Draft（2025-10-30）：[CSS Conditional Level 5](https://www.w3.org/TR/css-conditional-5/#container-queries)，检查于 2026-11-06。
> - Flex/Grid 自动最小尺寸与轨道宽度：W3C CSS Flexible Box Layout Level 1，§4.5，Candidate Recommendation Draft（2025-10-14）；CSS Grid Layout Level 2，§12，Candidate Recommendation Draft（2025-03-26）：[Flexbox](https://www.w3.org/TR/css-flexbox-1/) · [Grid](https://www.w3.org/TR/css-grid-2/)，检查于 2026-11-06。
> - <code>text-overflow</code>：W3C CSS Overflow Level 3，§5.1，Working Draft（2025-10-07）；<code>line-clamp</code>：Level 4，§5.1，Working Draft（2023-03-21）。两者仍处于草案阶段，兼容实现需按目标环境确认：[CSS Overflow Level 3](https://www.w3.org/TR/css-overflow-3/) · [CSS Overflow Level 4](https://www.w3.org/TR/css-overflow-4/)，检查于 2026-11-06。
