# How do HTML character references represent reserved characters? / HTML 字符引用如何表示保留字符？

Use a named or numeric character reference when source text needs a character that would otherwise be parsed as markup, such as `&lt;` for `<` and `&amp;` for `&`. The reference is decoded in the document text; it is not a replacement for safe DOM text insertion. / 当源码需要表示可能被解析为标记的字符时，使用命名或数字字符引用，例如用 `&lt;` 表示 `<`、用 `&amp;` 表示 `&`。文档解析时会还原引用；它不能替代安全的 DOM 文本插入方式。

## Useful Character Entities

### Character Entities Table

| Result | Description    | Character Entity |
| ------ | -------------- | ---------------- |
|        | Space          | `&nbsp;`         |
| <      | Less than      | `&lt;`           |
| >      | Greater than   | `&gt;`           |
| "      | Quotation mark | `&quot;`         |
| &      | Ampersand      | `&amp;`          |

### Explanation

- **`&nbsp;`**: Represents a non-breaking space, which prevents automatic line breaks at its position.
- **`&lt;`**: Represents the less than symbol (`<`), preventing it from being interpreted as an HTML tag.
- **`&gt;`**: Represents the greater than symbol (`>`), preventing it from being interpreted as the end of an HTML tag.
- **`&quot;`**: Represents the double quotation mark (`"`), often used to encapsulate attribute values.
- **`&amp;`**: Represents the ampersand (`&`), used to start character entities.

### Usage Example

```html
<p>This is a paragraph with a special character: &amp;.</p>
```

## References

- [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/)
- [WHATWG HTML: Document base URLs](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#document-base-urls)
- [WHATWG HTML: Audio and video elements](https://html.spec.whatwg.org/multipage/media.html)
- [CSS Device Adaptation Level 1](https://www.w3.org/TR/css-device-adapt-1/)
- [W3C WAI: Images tutorial](https://www.w3.org/WAI/tutorials/images/)
- [W3C WAI: Forms labels tutorial](https://www.w3.org/WAI/tutorials/forms/labels/)
- [Google Search Central: Control snippets in search results](https://developers.google.com/search/docs/appearance/snippet)
- [Google Search Central: Meta tags it supports](https://developers.google.com/search/docs/crawling-indexing/special-tags)
