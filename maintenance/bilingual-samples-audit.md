# 双语样板审计

## 范围与处理

完整阅读了旧稿，并在迁移完成后重写以下两篇；未扩展到其它主题：

- [作用域与闭包](../frontend/javascript/scope-and-closure.md)（旧稿：Frontend_Notes/4.2 Scope & Closure.md）
- [HTTP与WebSocket](../engineering-foundations/networking/http-protocols-and-websockets.md)（旧稿：Frontend_Notes/8.1 HTTP Protocols and WebSockets.md）

两篇均以中英双语标题、核心解释和面试简答开篇；细节以中文说明，保留必要英文术语、规范名和代码。保留了原稿中的词法作用域、闭包工厂、私有状态、循环回调、REST方法、请求API、TCP分层、CORS/JSONP/代理、WebSocket示例和资源提示。未添加学习状态或面试专用删减。

## 重点事实核验

- **作用域与闭包：** 核对词法环境、全局对象、脚本与模块顶层、var/let/const范围、暂时性死区、闭包读取绑定以及可达性与回收时机。修正“闭包读取创建时值”和“外层作用域所有局部变量必然保留”等过度概括。使用Node v26.11.1复现：外层返回后闭包读到更新后的值；var循环回调均读到最终值，let循环回调各读到独立迭代值。依据：[ECMAScript执行上下文](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html)、[MDN闭包](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)、[MDN全局对象](https://developer.mozilla.org/en-US/docs/Glossary/Global_object)、[MDN let](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let)。
- **HTTP格式、方法、缓存与状态：** 核对HTTP/1.1的起始行/字段/空行线格式，以及HTTP/2/3用帧、字段块和伪首部表达相同HTTP语义；同时核对REST约束、方法安全性/幂等性、PUT与PATCH语义、no-cache与no-store、304验证、Fetch对HTTP错误状态的Promise行为。修正“所有5xx都可安全重试”“PUT缺字段必然清空”等概括。依据：[RFC 9112 §2.1](https://www.rfc-editor.org/rfc/rfc9112.html#section-2.1)、[RFC 9113 §8.1](https://www.rfc-editor.org/rfc/rfc9113.html#section-8.1)、[§8.3](https://www.rfc-editor.org/rfc/rfc9113.html#section-8.3)、[RFC 9114 §4.1](https://www.rfc-editor.org/rfc/rfc9114.html#section-4.1)、[§4.3](https://www.rfc-editor.org/rfc/rfc9114.html#section-4.3)、[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)、[RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html)、[RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html)、[MDN Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)。
- **传输与跨源：** 核对HTTP/1.1持久连接、HTTP/2在TCP上的多路复用与传输层队头阻塞、HTTP/3/QUIC按流交付与共享拥塞控制、0-RTT重放风险、CORS预检和凭据规则、Cookie与Authorization分工、传统WebSocket升级及HTTP/2/3扩展连接。修正“一个请求一个HTTP/1.1连接”“CORS阻止请求发送”“WebSocket总是HTTP/1.1 TCP升级”等说法。依据：[RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html)、[RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html)、[RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html)、[RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)、[RFC 9001](https://www.rfc-editor.org/rfc/rfc9001.html)、[RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)、[RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)、[RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)、[MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)。

## 检查与边界

两篇的相对本地链接均能解析，代码围栏成对；闭包旧标题的两个常见fragment均由显式HTML锚点兼容。当前活跃笔记中没有发现指向这两篇特定fragment的入链，故未要求其它正文改动。

Firecrawl skill已阅读。Firecrawl仅用于发现来源；按主代理反馈连接器后续返回Unknown tool，未继续重试。事实核验直接基于ECMAScript、IETF RFC及MDN、Axios、ws、web.dev官方文档；无依赖安装。Node代码仅本地运行；未部署HTTP服务，也未在浏览器中实测CORS或WebSocket握手，相关说明以规范和平台文档为依据。

