# 怎样为报表图标选择资源形式？

**案例背景。** 同一公开合成案例中，用户打开 `/reports/42` 并改变筛选；工具栏有“添加筛选条件”和“编辑报表”按钮，多个报表页还复用一组小型状态图标。添加筛选图标会随主题、焦点和禁用状态换色；编辑图标外形固定；不同页面会取用不同数量的状态图标。选择资源时，要同时看控件名称、图形是否要跟页面样式变化、页面会取用多少图、文件怎样缓存，以及一次更新会让哪些页面重新下载。

图形用 Scalable Vector Graphics（可缩放矢量图形，SVG）绘制时，页面会用 Cascading Style Sheets（层叠样式表，CSS）控制颜色与尺寸。常见载体是 inline SVG（行内 SVG）、独立 SVG 图片、CSS Sprite（CSS 雪碧图）和 icon font（图标字体）。没有一种形式能单凭“文件更少”或“矢量更清晰”胜出；先沿着这个报表站的一次选择看颜色与名称，再比较缓存单位和下载范围。

## SVG 怎样兼顾颜色、复用与替代文本？

“添加筛选条件”的颜色要跟随按钮状态，行内 SVG 可以直接受宿主页面的 CSS 控制。让形状使用 `currentColor`（当前文字颜色），它就沿用按钮的 `color`。按钮已有可见文字时，图标只是装饰，应从辅助技术呈现中隐藏：

~~~html
<button type="button" class="report-action">
  <svg class="report-action__icon" viewBox="0 0 16 16" aria-hidden="true">
    <path d="M7 2h2v5h5v2H9v5H7V9H2V7h5z" fill="currentColor" />
  </svg>
  <span>添加筛选条件</span>
</button>
~~~

~~~css
.report-action { color: #24547d; }
.report-action__icon { width: 1em; height: 1em; }
~~~

行内 SVG 的标记和所在 HyperText Markup Language（超文本标记语言，HTML）一起传输；它没有可供其他页面单独请求的资源 Uniform Resource Locator（统一资源定位符，URL）。若“编辑报表”图案固定而多个页面重复使用，可把它保存成独立 SVG，通过 `<img>` 使用同一 URL。宿主页面的 CSS 不能直接选择外部 SVG 文档里的路径，内部 `currentColor` 也不会继承按钮颜色。按钮已有可见文字时图片用 `alt=""`；图片本身承担信息时，才由 `alt` 提供替代文本：

~~~html
<button type="button">
  <img src="/assets/edit-report.svg" width="16" height="16" alt="">
  <span>编辑报表</span>
</button>
~~~

控件的名称应来自控件内的可见文字、图片替代文本，或显式关联的可访问名称；孤立的相邻文字不会自动成为控件名称。若无文字图标按钮承担操作名称，可把 `aria-label="编辑报表"` 放在按钮上，不要让图案本身成为唯一的说明。

## CSS Sprite 怎样裁出图集中的一格？

当多个小图总在同一组页面一起出现，可以把它们排进一张 sprite sheet（精灵图集），让固定尺寸的盒子只露出目标区域。假设图集是 `64 × 32px`，每格 `16 × 16px`，有 4 列、2 行：

图中的 `x`、`y` 是每格左上角坐标，以图集左上角为原点；数值单位均为 CSS px。右侧小盒子大小固定，移动的是它背后的整张背景图。

![将图集向左移动32、向上移动16后，第七格进入固定的16乘16视窗](resources/css-sprite-crop.svg)

> [!example] 第二行第三列的坐标
> 第七格位于 `x=32`、`y=16`，也就是第三列、第二行。把背景向左、向上移动这么多距离后，该格落进 `16 × 16px` 的视窗，所以定位写成 `-32px -16px`。

~~~css
.report-status__pending-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  background-image: url("/assets/report-icons.4f2a.svg");
  background-repeat: no-repeat;
  background-position: -32px -16px;
}
~~~

~~~html
<span class="report-status__pending-icon" aria-hidden="true"></span>
<span>等待处理</span>
~~~

这是“等待处理”状态旁的装饰图标。背景图本身不提供有意义的替代文本；状态文字承担说明。图标很多时，可以在构建阶段从源图和布局配置同时生成图集与坐标，避免手写偏移。若图片本身承载信息，应改用 `<img>` 提供替代文本，并按[图片与媒体资源加载规则](../browser-apis/image-lazy-loading.md)处理宽高、候选资源和加载时机。图集坐标一旦移动，每个引用这些坐标的页面都可能要改；更新一个格子也会更新整张图集资源。

## Sprite 是否一定比独立图片快？

先看浏览器缓存的对象：Hypertext Transfer Protocol（超文本传输协议，HTTP）缓存按请求目标 URL 等条件寻找可复用响应，同一 URL 只有在响应仍新鲜、验证成功或其他缓存条件允许时才能复用。若报表图标是公开且不含用户数据的静态资源，构建时可把内容摘要放进 URL，例如 `/assets/report-icons.4f2a.svg`。服务器首次成功响应这个新 URL 时，可以返回：

~~~http
HTTP/1.1 200 OK
Content-Type: image/svg+xml
Cache-Control: public, max-age=31536000, immutable
~~~

`Cache-Control` 是服务器随响应发送的字段。`max-age` 指定这份响应可新鲜复用的时间；`immutable` 扩展声明在新鲜期间不需要再次验证。图片内容改变时生成新的摘要 URL，再让页面或样式表引用新地址。若发布时删掉仍被旧页面引用的文件，旧页面仍会请求那个旧 URL，所以部署应保留旧哈希资源一段足够的时间。

验证器和新鲜时间解决不同问题。响应带 `ETag`（实体标签）时，缓存可以在响应变旧后发 `If-None-Match` 询问是否仍是同一份内容；服务器回 `304 Not Modified` 时复用已保存的正文，内容改变时回 `200 OK` 和新正文。`ETag` 本身不会让仍新鲜的旧响应提前发起验证。可变的同 URL 图标可以用较短的 `max-age` 限制旧内容最多直接复用多久，到期后配合 `ETag` 验证；也可以让服务器返回 `Cache-Control: public, no-cache` 和单独的 `ETag` 响应字段，让缓存保留正文、但每次复用前都联系服务器验证。`no-store` 则要求缓存不存储响应。

对照报表站的一次更新：把详情页 `/reports/42` 记作 A，它使用整组 8 格；把报表列表页记作 B，它只使用第 1 格；这次只改第 7 格。若图集按内容摘要生成新 URL，两个更新后的页面都指向新版整张图集。在同一浏览器缓存上下文里，A 或 B 先打开都会请求新版完整图集，后打开的页面可复用该 URL 的新鲜响应。若每格是独立的哈希图片，B 仍引用未变化的第 1 格 URL，可以复用缓存；A 只需取得改名后的第 7 格，其余七个仍可用原 URL。是否命中还取决于缓存分区、响应新鲜度和缓存是否仍保留该对象。

因此，图集减少的是多个图标共享时的资源数；它不会把一张雪碧图拆成可单独缓存的格子。若某个页面没有可复用的图集响应，即便它只露出一格，也需要请求整份图集。独立图片则可以只请求当前页面所需的 URL，并让未变化的图标继续命中缓存。

下面的本地浏览器对照只回答“请求哪些文件、缓存能否复用”，不把它当成所有站点的速度结论：

| 报表页加载的图标资源 | 冷缓存请求数 | 正文编码字节 | `transferSize` 合计 | 同一上下文热重载 |
|---|---:|---:|---:|---|
| 8 个独立 `16 × 16` SVG | 8 | 1,780 | 4,180 | 0 新请求；0 字节传输值 |
| 含 8 个图形的单张 SVG 图集 | 1 | 1,383 | 1,683 | 0 新请求；0 字节传输值 |
| 只取 1 个独立 SVG | 1 | 210 | 510 | 0 新请求；0 字节传输值 |
| 只用图集中的 1 格 | 1 | 1,383 | 1,683 | 0 新请求；0 字节传输值 |

实测使用 Chromium `157.0.8103.51`、本机 Node HTTP/1.1 服务、8 个极小合成 SVG 和 `Cache-Control: public, max-age=86400, immutable`；分别新建干净浏览器上下文测冷缓存，再在原上下文热重载。字节来自 PerformanceResourceTiming（资源计时 API）：`encodedBodySize` 计响应正文；网络响应的 `transferSize` 是编码正文大小加规范定义的 `300` 字节响应头估值，本地缓存命中且无需网络验证时为 `0`。若缓存响应经过网络验证后复用，`transferSize` 按规范记为 `300` 字节估值。此值不是实际 HTTP 头、TLS 或链路字节的精确账单。本表只计图标资源，不含 HTML、CSS 或其他页面资源；它也没有测连接、内容压缩、Content Delivery Network（内容分发网络，CDN）、真实图形复杂度或页面延迟。它只展示同一配置下的资源粒度：页面取用全组时图集少 7 个请求；只取一格时，单张独立 SVG 少传约 `1,173` 个 `transferSize` 字节。热重载结果说明本次测试配置可复用缓存，并不保证资源一直留在缓存里。

现代协议也改变了“少一个请求”的意义。HTTP/2 允许多个资源流在同一 Transmission Control Protocol（传输控制协议，TCP）连接上交错传输，但 TCP 丢失字节时仍可能暂时挡住同一连接的后续数据；HTTP/3 用 QUIC 流承载请求，单个流受阻时其他流可以继续推进，但流仍共享连接的拥塞与连接级流量控制。资源请求数不再等于新建连接数，因此不能仅为减少文件请求就断言雪碧图更快。独立图标仍会带来各自的请求处理和响应头；图集则把未用图案的字节、变更频率与缓存失效绑在一起。实际选择时，若这组图标在多数报表页一起出现且共用更新节奏，可测图集；若路由只取少量图标或图标经常独立更新，独立资源可以只请求当前需要的 URL；若少量图案要随按钮状态换色，行内 SVG 更直接。

## 图标字体怎样保留可访问名称？

若报表站已经维护一套图标字体，字形也能用 CSS 控制颜色和尺寸。每个私用区码点只对配套字体有意义；字体载入失败时，字形可能缺失或显示替代符号。把字形当装饰，让按钮或链接文字承担功能名称：

~~~css
@font-face {
  font-family: "report-icons";
  src: url("/assets/report-icons.woff2") format("woff2");
}

.icon {
  font-family: "report-icons";
  font-size: 1.25rem;
  line-height: 1;
}
~~~

~~~html
<button type="button">
  <span class="icon" aria-hidden="true">&#xe900;</span>
  <span>编辑报表</span>
</button>
~~~

`aria-hidden="true"` 把纯装饰字形从辅助技术呈现中隐藏，按钮的可见文字仍提供名称。新系统若只为几个小图标引入一整套字体，会多一个字体资源和字形映射维护成本；字体文件还可能带入当前页面用不到的字形。为已有字体继续支付这项成本，取决于它是否已被页面使用、是否跨页面共享，以及是否能按实际使用子集构建。选择字体并不会自动解决无文字按钮的名称问题。

## 怎样只显示当前横幅？

雪碧图从同一张资源里裁出装饰性小图；横幅则按状态显示完整图片。图片角色不同，替代文本和请求时机也不同。下面先保留旧电商页面的归档截图；原图可见中秋活动文案、商品分类和左右切换箭头。接着的报表代码是另一个独立合成示例，只用 `.current` 显示一项，不是截图中的页面源码：

![归档电商横幅：中秋活动图，两侧有左右切换箭头，左侧列出商品分类](../../archive/front-end/0-1_Learning_Notes/HTML/banner.png)

下面的列表只有静态的选中项，没有把归档截图里的箭头纳入行为：

~~~html
<ul class="report-banner">
  <li class="current">
    <a href="/reports/monthly">
      <img src="/assets/monthly-banner.jpg" alt="查看月度订单报表">
    </a>
  </li>
  <li>
    <a href="/reports/quarterly">
      <img src="/assets/quarterly-banner.jpg" alt="查看季度订单报表">
    </a>
  </li>
</ul>
~~~

~~~css
.report-banner {
  position: relative;
  overflow: hidden;
  aspect-ratio: 16 / 5;
  margin: 0;
  padding: 0;
  list-style: none;
}
.report-banner li { position: absolute; inset: 0; display: none; }
.report-banner li.current { display: block; }
.report-banner img { display: block; width: 100%; height: 100%; object-fit: cover; }
~~~

这段代码只决定哪项显示；它没有自动轮换、前后按钮、键盘模式或暂停控制，因此不构成完整轮播。真正的自动轮播需提供操作控制并照顾焦点、悬停和减少动态效果；连续移动图片的装饰演算见[何时使用过渡，何时使用关键帧动画？](../html-css/css-transitions-and-animations.md)。信息图片的宽高、候选文件与加载时机见[图片与媒体资源怎样加载并保持页面稳定？](../browser-apis/image-lazy-loading.md)。

这里的 CSS 只控制显示，不会推迟普通 `<img src>` 的请求。按 HTML 标准，图片默认立即获取；两个 URL 在 HTML 创建时就已提供，即使季度项是 `display: none`，浏览器仍可获取它。若需要由应用决定请求时机，初始状态不要设置真实 `src`，在选中该项时再设置。本页的 Chromium `157.0.8103.51` 小复现记录了隐藏的季度图片被请求并解码。

> [!info]- 来源
> - `<img>` 的替代文本与图片呈现边界：[WHATWG HTML Living Standard，Images](https://html.spec.whatwg.org/multipage/images.html#the-img-element)；外部 SVG 作为图像是独立文档、不会继承宿主属性：[W3C SVG 2，Embedded content](https://www.w3.org/TR/SVG/embedded.html)；核对于 2026-11-12。
> - `currentColor` 的计算与使用：[W3C CSS Color Module Level 4，2026-10-07 CRD，§4.4](https://www.w3.org/TR/2026/CRD-css-color-4-20261007/#valdef-color-currentcolor)；SVG 图形的 `color` 如何为 `fill` 提供 `currentColor`，以及行内 SVG 接受 HTML 文档继承值：[W3C SVG 2，§§13.2–13.3](https://www.w3.org/TR/SVG/single-page.html#ColorProperty)；核对于 2026-11-12。
> - `background-position` 的定位语法：[W3C CSS Backgrounds and Borders Module Level 3](https://www.w3.org/TR/css-backgrounds-3/#the-background-position)；核对于 2026-11-12。图例使用 4 列 × 2 行、每格 16px 的合成数据，偏移按该几何直接计算。
> - 背景图不提供替代文本、隐藏装饰并给控件名称：[W3C WAI-ARIA 1.2，`aria-hidden`](https://www.w3.org/TR/wai-aria-1.2/#aria-hidden)；[WAI Images Tutorial](https://www.w3.org/WAI/tutorials/images/)；轮播操作模式：[WAI-ARIA APG Carousel Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/carousel/)；核对于 2026-11-12。
> - 缓存键、新鲜度和 `max-age`：[IETF RFC 9111，HTTP Caching §§2、4.2](https://www.rfc-editor.org/rfc/rfc9111.html#section-4.2)，2022-06；`ETag` 验证、`no-cache` 与 `no-store`：[RFC 9111 §§4.3、5.2.2](https://www.rfc-editor.org/rfc/rfc9111.html#section-4.3)；不可变响应扩展：[IETF RFC 8246，§§2–3](https://www.rfc-editor.org/rfc/rfc8246.html#section-2)，2017-09；核对于 2026-11-12。哈希 URL 更新策略：[MDN HTTP Caching Guide，Cache Busting](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching#cache_busting)，访问于 2026-11-12。
> - HTTP/2 多路复用但仍受 TCP 队头阻塞影响：[IETF RFC 9113，§§1.2、5](https://www.rfc-editor.org/rfc/rfc9113.html#section-1.2)，2022-06；HTTP/3 的 QUIC 流、流间独立交付与连接级拥塞控制：[IETF RFC 9114，§§1.2、2](https://www.rfc-editor.org/rfc/rfc9114.html#section-1.2)，2022-06；QUIC 流级与连接级流量控制：[IETF RFC 9000，§4](https://www.rfc-editor.org/rfc/rfc9000.html#section-4)，2021-05；核对于 2026-11-12。
> - `PerformanceResourceTiming.transferSize`、`encodedBodySize` 的定义，网络响应的 300 字节估值与无网络缓存命中为 0：[W3C Resource Timing，2026-11-02 Candidate Recommendation Draft，§3.3](https://www.w3.org/TR/2026/CRD-resource-timing-20261102/#dom-performanceresourcetiming-transfersize)；实测条件和数值见上文本地浏览器对照。
