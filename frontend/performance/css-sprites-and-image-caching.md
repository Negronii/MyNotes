# When should small images be combined into a CSS sprite? / 何时应把多个小图片合并为 CSS Sprite？

A CSS sprite places several small images in one file and reveals each image with a fixed-size element and `background-position`. It can reduce separate image requests in some delivery setups, but couples cache invalidation and coordinates: changing one icon replaces the combined asset. With HTTP/2 multiplexing, request count alone is not enough reason to create a sprite; compare transfer bytes, cache reuse, and maintenance cost for the actual assets. / CSS Sprite 把多个小图放进一个文件，再通过固定尺寸元素和 `background-position` 显示其中一块。它在某些传输方式下可以减少独立图片请求，但会把缓存失效与坐标耦合起来：改动一个图标就要替换整个合并资源。HTTP/2 支持多路复用，仅凭请求数量不足以决定是否合并；应结合实际资源的传输字节、缓存复用和维护成本比较。

```css
.icon-edit {
  width: 16px;
  height: 16px;
  background-image: url("/icons.png");
  background-repeat: no-repeat;
  background-position: -32px -16px;
}
```

The offset exposes the desired sprite rectangle. Centralize coordinates or generate them as part of asset processing when the sprite has many entries. An independently cached icon can be a better fit when it changes often or is used on routes that should not download the full sprite.

HTTP/2 multiplexes streams over a connection, so multiple assets need not imply one connection per image. That does not make every request free or settle the trade-off: measure the emitted files and cache behavior. See [HTTP protocols and caching](../../engineering-foundations/networking/http-protocols-and-websockets.md) for the shared transport explanation.

**References:** [CSS Backgrounds and Borders: background positioning](https://www.w3.org/TR/css-backgrounds-3/#the-background-position), [HTTP/2 RFC 9113, streams and multiplexing](https://www.rfc-editor.org/rfc/rfc9113.html#name-streams-and-multiplexing).
