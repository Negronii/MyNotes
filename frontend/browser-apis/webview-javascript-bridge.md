# How does a native app expose capabilities to WebView JavaScript? / 原生应用如何向 WebView JavaScript 暴露能力？

A JavaScript bridge is a host-app interface that lets code in a WebView request selected native operations; it is platform-specific, not a browser standard. Common designs include a native object injected into JavaScript, a message handler with an explicit reply path, or a legacy custom-URL interception scheme. Because bridge calls cross from page code into privileged host capabilities, expose only narrow operations to trusted content and validate every operation and argument on the native side. / JavaScript Bridge 是宿主应用提供给 WebView 页面代码的接口，让页面请求指定原生操作；它因平台而异，并非浏览器标准。常见设计包括注入 JavaScript 的原生对象、带显式回复路径的消息处理器，或较旧的自定义 URL 拦截方案。Bridge 会把页面代码连接到有权限的宿主能力，因此只向可信内容开放有限操作，并由原生端验证每个操作和参数。

## Platform APIs / 平台 API

Android's `addJavascriptInterface` exposes an annotated native object as a JavaScript interface. Android warns that it can grant JavaScript control over the host app; the object can be exposed to all frames, so do not expose it to untrusted content. Apple's `WKScriptMessageHandler` gives JavaScript a named message handler; the native delegate receives a message object with body and frame information, and newer reply handlers can return a response. These platform APIs have different lifecycles, threading and frame rules, so do not treat one sample as portable across WebViews.

## An illustrative JavaScript contract / JavaScript 接口示例

The following is a page-side sketch only. `NativeBridge` is supplied by the app and is not a standard web API.

~~~javascript
// The host app injects or registers this interface for trusted content.
window.NativeBridge.requestLocation((location) => {
  renderLocation(location);
});
~~~

A real contract should define operation names, argument and reply schemas, error behavior, cancellation, and whether calls are synchronous or asynchronous. Validate origin/frame identity and authorization on the native side; page-side checks alone cannot protect native capabilities. If untrusted pages can load, do not let them navigate inside a WebView that exposes a privileged bridge.

## Legacy custom-scheme pattern / 旧式自定义协议模式

An older design appends a hidden iframe with a URL such as `myapp://api/location?data=...` and lets the native host intercept the navigation. The URL carries encoded arguments but may hit platform length limits and has no direct reply; callbacks require a separate request identifier and return channel. Treat this as an implementation-specific legacy pattern, not a general WebView recommendation.

~~~javascript
const bridge = {
  invoke(path, data) {
    const iframe = document.createElement("iframe");
    iframe.hidden = true;
    iframe.src = "myapp://" + path + "?data=" +
      encodeURIComponent(JSON.stringify(data));
    document.body.appendChild(iframe);
    setTimeout(() => iframe.remove(), 100);
  },
  getLocation() {
    this.invoke("api/location", {});
  }
};
~~~

This sketch only shows the request side. A complete bridge needs a response channel, request identifiers, timeouts, error handling, and a native authorization check.

For a normal web page, use standard browser APIs such as `navigator.geolocation` when they fit; the browser mediates permission and device access.

**Sources checked 2026-11-05:** [Android Developers: WebView JavaScript interfaces and security warning](https://developer.android.com/develop/ui/views/layout/webapps/webview); [Android Developers: JS bridge guidance](https://developer.android.com/develop/ui/views/layout/webapps/native-api-access-jsbridge); [Apple Developer Documentation: WKScriptMessage](https://developer.apple.com/documentation/webkit/wkscriptmessage); [Apple Developer Documentation: message handler with reply](https://developer.apple.com/documentation/webkit/wkusercontentcontroller/addscriptmessagehandlerwithreply%28_%3Acontentworld%3Aname%3A%29).
