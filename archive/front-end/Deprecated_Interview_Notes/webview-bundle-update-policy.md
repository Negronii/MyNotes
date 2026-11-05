# How should a WebView app update its downloadable web bundle? / WebView 应用如何更新可下载的网页资源包？

Treat the HTML, JavaScript, and CSS bundle as a versioned artifact with explicit compatibility and rollback policy. A slow network check should not block app startup, and a candidate bundle should not replace the last known-good version until validation succeeds. / 将 HTML、JavaScript 和 CSS 资源包视为带版本的产物，明确兼容与回滚策略。慢速网络检查不应阻塞应用启动；新包验证成功前不应替换最后一个可用版本。

A practical flow is:

1. Publish an immutable, versioned bundle with compatible native and API versions.
2. Fetch a small manifest according to freshness or user-triggered policy.
3. Download in the background, verify origin and integrity, and reject incompatible or partial bundles.
4. Switch versions atomically only after validation; retain the previous good bundle for rollback.
5. Keep authenticated data and privileged actions behind the native/server boundary. Loading local files through file:// does not itself provide security isolation.

The manifest format, signature, storage location, and rollback mechanism depend on the app's threat model and WebView platform. A bridge should expose only an allowlist of native operations and validate every payload; see [Browser Storage and Communication](../../../frontend/browser-apis/browser-storage-and-communication.md) for the JS-Bridge contract.
