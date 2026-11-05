# Which HTML elements represent text, media, and links? / 哪些 HTML 元素用于表示文本、媒体和链接？

Use elements according to their content and behavior: headings and paragraphs structure text, media elements expose playback controls, and anchors navigate to destinations. Resource paths may be absolute, root-relative, or document-relative. / 根据内容和行为选择元素：标题和段落组织文本，媒体元素提供播放控件，锚点导航到目标。资源路径可以是绝对路径、根相对路径或文档相对路径。

## Paths

### Absolute Path

An absolute filesystem path starts from a filesystem root. An absolute URL has a scheme and does not necessarily have a host (for example, `mailto:hello@example.com`); HTTP(S) URLs normally include a host. A root-relative URL starts at the site's origin but is not an absolute URL. Filesystem paths are examples only and are not directly usable as public web URLs unless the server maps them.

**Example:**
- File System: `/projects/site/images/cat.jpeg`
- URL: `https://www.example.com/images/logo.gif`

### Relative Path

Relative paths are commonly used because they are flexible and easier to maintain. In an HTML document, a relative URL resolves against the document's base URL (normally the page URL; a `<base>` element can change it).

**Types:**
- **Same-level files:** In the same folder as the HTML file. Example: `filename.extension`
- **Lower-level files:** In a subfolder of the current folder. Example: `subfolder/filename.extension`
- **Upper-level files:** In the parent folder of the current folder. Example: `../filename.extension`
- **Two levels up:** Example: `../../filename.extension`

## Basic tags

Most HTML elements have a start tag and an end tag. Void elements such as `<img>`, `<input>`, and `<br>` have a start tag but no end tag; do not write an XHTML-style closing slash as if it were required in HTML.

## Heading Element `<h1></h1>`

```
<h1>title</h1>
...
<h6>title</h6>
```

User-agent styles commonly render headings as bold block boxes with decreasing default sizes, but CSS can change their appearance. Choose heading levels for the document outline rather than their default font size; use a logical hierarchy for sections and subsections.

## Paragraph element `<p></p>`

`<p>context</p>`

Browsers commonly style paragraphs as block boxes with vertical margins. Those are CSS defaults, not whitespace added to the text by the HTML tags.

## The Line Break element `<br>`

Produces a line break in the text (carriage-return). It helps break paragraphs where the division of lines is significant.

## The Thematic Break (Horizontal Rule) element `<hr>`

It represents a thematic break between paragraph-level elements and draws a horizontal line on the page.

## Font elements

These elements are not interchangeable synonyms. Use CSS for purely visual styling; choose the HTML element that matches the meaning.

- `<b>context</b>` draws attention without adding importance; `<strong>context</strong>` indicates strong importance.
- `<u>context</u>` marks a non-textual annotation; `<ins>context</ins>` marks inserted content.
- `<i>context</i>` marks text in an alternate voice or technical term; `<em>context</em>` marks stress emphasis.
- `<s>context</s>` marks content that is no longer accurate or relevant; `<del>context</del>` marks deleted content.

These elements may appear in phrasing content, including inside paragraphs, when their semantics fit.

## Image element `<img src="">`

e.g. `<img src="./cat.jpeg" alt="pic of cat" title="so cute a cat" width="200" height="150">`

Must have a start tag and must not have an end tag.

Attribute: `<attribute name>="<value>"`

Useful attributes:
src: The path of the image. See the [Paths](#paths) section above for path types. `src="<path>"`

alt: Text alternative for the image's information or function, not merely a fallback for a failed download. Use `alt=""` when an image is decorative; when an image is the only content of a link, describe the link's purpose. `alt="<text>"`

title: Advisory text that some browsers may show as a tooltip; it is not a reliable replacement for alt text or a form label. Other elements can also have a `title` attribute. `title="<text>"`

Height and width:
width: Width of the image. `width="<integer>"`

height: Height of the image. `height="<integer>"`

When an image has intrinsic dimensions, setting only one dimension normally preserves its aspect ratio. Supplying both dimensions with a ratio that differs from the image can distort it; CSS `aspect-ratio` and `object-fit` provide additional layout/cropping controls.

## Audio element `<audio src="" controls></audio>`

Useful attributes:
src: the path of an audio resource. Playback depends on the format/codec and browser/platform support; provide `<source>` alternatives when the target browsers need them. See the [Paths](#paths) section above for path types.

controls: display playback controls, no attribute value required

autoplay: requests automatic playback; the user agent may not start playback under its autoplay policy. No attribute value is required.

loop: loop playback, no attribute value required

e.g. `<audio src="hello.mp3" controls autoplay loop></audio>`

## Video element `<video src="" controls></video>`

Useful attributes:
src: path of a video resource. MP4 is a container; playback depends on the codecs and browser/platform support. See the [Paths](#paths) section above for path types.

controls: display playback controls; no attribute value required

autoplay: requests automatic playback; browsers apply autoplay policies. Muted video is permitted by some browser policies, but playback is not guaranteed.

loop: loop playback, no attribute value required

muted: play muted

e.g. `<video src="hello.mp4" controls autoplay loop muted></video>`

## The Anchor element `<a href="destination"></a>`

e.g. `<a href="https://www.google.com">open Google</a>`

**Output**
<a href="https://www.google.com">open Google</a>

`href` can be an absolute URL such as `https://example.com/page`, a root-relative or document-relative path such as `/products` or `filename.html`, or a fragment such as `#section-id`.
`href="#"` points to the top of the current document and is not a neutral placeholder. Use a real destination for navigation, or a `<button>` for an action; a bare `#` can cause unwanted scrolling and history changes.

Useful attributes:
target: the opening form of the target page, the value could be:
\_self: the default value, jump directly from the current page
\_blank: request a new browsing context (often a tab); consider `rel="noopener"` when supporting older browsers or when explicitly severing access through `window.opener`.

e.g. `<a href="https://www.baidu.com" target="_blank" rel="noopener">Open Baidu</a>`
