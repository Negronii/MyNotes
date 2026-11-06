# WebView 怎样安全地开放原生能力并更新页面包？

案例背景：报表应用把页面放进原生应用的 WebView，页面需要请求宿主打开报表详情；页面脚本同时会随应用安装或网络更新。JavaScript bridge (原生桥接接口) 把页面输入送到宿主应用的权限边界，因此必须把“哪个页面能发消息”“消息能请求什么”“更新后的代码是否兼容”作为一条信任链来设计。

WebView 没有一个跨平台统一的原生桥接标准。Android 与 Apple WebKit 的 API、回调线程、来源信息和回复方式都不同；平台 API 只能提供边界线索，最终由宿主原生代码检查操作和授权。

## 一条消息怎样变成原生操作？

| 平台 | 消息入口 | 平台能提供的来源信息 | 重要边界 |
|---|---|---|---|
| Android WebView | 优先考虑 AndroidX `WebViewCompat.addWebMessageListener()` | 回调含 `sourceOrigin`、`isMainFrame` 和回复代理 | 注册时需设 `allowedOriginRules` 并在加载页面前安装；规则匹配 scheme (协议)、host (主机)、port (端口)，不匹配路径，而且匹配来源的子框架页面也可收到注入对象 |
| Android 旧版接口 | `addJavascriptInterface()` | 旧桥接对象没有可信的逐消息来源校验 | 标注 `@JavascriptInterface` 的方法可暴露给各内嵌框架页面；只适合严格控制且完全可信的内容，不能让不可信内容复用同一个 WebView |
| Apple WebKit | `WKScriptMessageHandler` 或带回复的 `WKScriptMessageHandlerWithReply` | `WKScriptMessage.frameInfo` 提供 `securityOrigin` 与 `isMainFrame` | 由宿主安装具名消息处理器；消息处理与回复是 WebKit API，不等同于 Android 的同步对象调用 |

AndroidX `WebViewCompat.addWebMessageListener()` 需要用 `WebViewFeature.isFeatureSupported()` 检查当前 WebView 是否支持。现代接口仍需检查来源和主框架页面：可信主机下的广告内嵌框架，或遭 cross-site scripting (跨站脚本攻击，XSS) 控制的页面脚本，也可能发消息。`allowedOriginRules` 不区分路径，例如允许 `https://reports.example` 也会匹配这个来源上的其他路径。只加载 HTTPS 并允许受控的页面，收到消息后再校验 origin (来源)、frame (框架页面)、操作名、schema (参数结构)、数据范围和调用者权限。回调通常在主线程执行，耗时工作应移交后台线程。

建议把应用自己的桥接契约做成窄的异步 remote procedure call (远程过程调用，RPC) 形状，例如 `{id, operation, payload}`，回复带同一 `id` 以及成功结果或错误码。定义允许的操作和参数、版本协商、取消、超时和权限拒绝；不要开放任意方法调用、JavaScript 求值或文件路径访问。确认来源只是信任的一部分，不能代替业务授权。

> [!example] 先检查消息，再处理一个允许的操作
> 以下是宿主侧伪代码，说明检查顺序，不是 Android 或 Apple 的可直接编译 API。`platformMetadata` 由原生平台回调提供，`untrustedBody` 才是网页发送的数据；页面不能靠在 body 中填来源或主 frame 来证明身份。示例只开放 `openReport`：宿主确认平台提供的受信来源和主 frame，再验证 `reportId`、检查当前用户权限，授权后才调用原生操作并回复。
>
> ~~~text
> platformMetadata = { sourceOrigin: platformOrigin, isMainFrame: platformFrameFlag }
> untrustedBody = { id: "req-17", operation: "openReport", payload: { reportId: 42 } }
>
> handle(platformMetadata, untrustedBody, reply):
>   reject unless trustedOrigin(platformMetadata.sourceOrigin)
>   reject unless platformMetadata.isMainFrame
>   message = parseAndValidate(untrustedBody)
>   reject unless message.operation == "openReport"
>   reject unless schemaValid(message.payload) and validReportId(message.payload.reportId)
>   reject unless authorize(currentNativeUser, "openReport", message.payload.reportId)
>   result = openReport(message.payload.reportId)
>   reply({ id: message.id, ok: true, payload: result })
> ~~~

Android 的来源和主 frame 信息来自 `WebMessageListener` 平台回调；Apple 宿主应从 `WKScriptMessage.frameInfo.securityOrigin` 与 `isMainFrame` 读取对应元数据。两者都不应从网页 body 取值。如果页面只需要浏览器已有能力，例如定位并展示地图，优先评估 Web API（如 `navigator.geolocation`）；浏览器可以按标准权限流程提示用户，减少原生接口暴露面。较旧的隐藏 iframe 自定义 URL scheme（例如 `myapp://api/location`）曾用于触发宿主拦截，但参数长度、回复通道、回调 ID 和错误处理都要自行实现；把它当成遗留兼容方案，不作为新桥接推荐。

## 下载更新包怎样进入桥接信任区？

下载的 HTML、JavaScript、CSS 与图片 bundle (资源包) 不是无权限的数据：只要在可调用桥接接口的 WebView 中执行，就可能请求宿主能力。因此资源包校验是桥接安全的一部分，但更新下载和消息授权仍是两套不同机制，不能用其中一套替代另一套。

一个最小可审查的更新流程可以是：

1. 应用启动时立即载入最后一个已验证版本；按新鲜度策略或用户请求在后台检查更新，不挡住启动。
2. 从允许的更新源获取小型更新 manifest (清单)，包含不可变包版本、支持的原生桥接 API 版本范围、资源清单、大小和完整性摘要。
3. 只从允许的包源下载；拒绝未授权的重定向，把包写入临时目录并完整校验后才候选安装。HTTPS 来源认证传输对端；若威胁模型包含 CDN 或更新源被攻陷，使用由原生应用内固定信任锚验证的发布者签名，不能把同一未认证源同时给的 hash (散列值) 当成独立身份验证。
4. 确认包满足当前桥接 bridge API (桥接接口) 的兼容条件，再原子切换到已验证目录；不接受半下载或半安装状态。
5. 保留上一版可用包。启动探测失败或启动崩溃达到策略阈值时回滚，并把下一次检查退避。

宿主本地资源的装载方式也会影响来源隔离。Android 官方建议用 `WebViewAssetLoader` 通过受控的 HTTP(S) 风格 origin (来源) 提供本地资源，并避免依赖 `file://`；它解决的是资源装载与同源行为，不会替你验证网络下载包的签名，也不等同于原生桥接接口的授权策略。Apple 平台需采用对应 WebKit 资源方案，不能照搬 Android 配置。

> [!example] 桥接接口版本不兼容时拒绝切换
> 当前应用只实现桥接接口 `2.0`，远端 manifest (清单) 声明新包最低要求 `2.1`。即使文件下载完整、hash (散列值) 匹配，也应保留旧包并延后切换；完整性证明“文件与清单相同”，不证明“页面和宿主能够协作”。

下载包中的密钥、会话数据和最终权限仍应留在原生安全存储或服务端。新页面获准调用原生桥接接口也不代表其所有代码都可信；为包更新和桥接操作分别记录版本、验证结果与授权决策，便于回滚和调查。

**延伸阅读：** [报表页面里的状态应该放在哪里？](./browser-storage-and-communication.md) 说明本地数据不应冒充服务端事实；[Web 安全与认证](../../engineering-foundations/security/web-security-and-authentication.md) 讨论来源、XSS 和授权边界。

> [!info]- 来源
> - AndroidX bridge API、来源规则、frame 信息、功能检测与回调线程：[Android Developers，Access native APIs with JavaScript bridge](https://developer.android.com/develop/ui/views/layout/webapps/native-api-access-jsbridge)，2026-11-06 核对。
> - 旧式 `addJavascriptInterface` 的 frame 暴露与桥接风险：[Android Developers，Insecure WebView native bridges](https://developer.android.com/privacy-and-security/risks/insecure-webview-native-bridges)，2026-11-06 核对。
> - Android 本地资源通过 `WebViewAssetLoader`、避免 `file://` 的建议：[Android Developers，Load in-app content](https://developer.android.com/develop/ui/views/layout/webapps/load-local-content)，2026-11-06 核对。
> - Apple WebKit 消息处理器与回复：[Apple Developer Documentation，WKScriptMessageHandler](https://developer.apple.com/documentation/webkit/wkscriptmessagehandler)；[WKScriptMessageHandlerWithReply](https://developer.apple.com/documentation/webkit/wkscriptmessagehandlerwithreply/usercontentcontroller%28_%3Adidreceive%3Areplyhandler%3A%29?language=objc)，2026-11-06 核对。
> - Apple 消息 frame 的 `isMainFrame`、`securityOrigin`：[Apple Developer Documentation，WKFrameInfo](https://developer.apple.com/documentation/webkit/wkframeinfo)；[WKScriptMessage.frameInfo](https://developer.apple.com/documentation/webkit/wkscriptmessage/frameinfo)，2026-11-06 核对。
> - Bundle 签名、兼容矩阵、原子切换与回滚是应用更新策略，不是 WebView 平台规范；本文把它们作为威胁模型驱动的设计建议。
