# HTML and Web Basics / HTML 与网页基础

**Key terms / 关键词：** HTML element（元素）, attribute（属性）, semantic markup（语义化标记）, form control（表单控件）.

**Core / 核心：** HTML structures content through elements, semantics, and content models; form controls expose named values for interaction and submission, while CSS controls presentation and cannot supply missing HTML semantics.
HTML 通过元素、语义和内容模型组织文档；表单控件以名称和值参与交互与提交，而 CSS 控制呈现，不能补上缺失的 HTML 语义。

These archived notes retain introductory examples and reference tables. For current focused notes, see [HTML and CSS basics](../../../../frontend/html-css/html-and-css-basics.md) and [browser HTML and CSS](../../../../frontend/html-css/browser-html-and-css.md).

## General

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

## CSS Display: Block, Inline, and Inline-block

“Block” and “inline” here describe common CSS `display` behavior, not categories that HTML elements permanently belong to. User-agent stylesheets provide defaults, which CSS can change; formatting details also depend on the surrounding formatting context. Replaced elements such as images have their own inline-level behavior, so the lists below are teaching examples rather than a complete current element taxonomy.

### Block-level Elements

Block-level elements occupy the entire width available, forcing a new line before and after the element. They are typically used for structuring the main parts of the document.

**Key Points:**
- Start on a new line.
- Stretch the full width of the parent container.
- Allow setting of width and height.
- Examples: `div`, `p`, `h1-h6`, `ul`, `li`, `dl`, `dt`, `dd`, `form`, `header`, `nav`, `footer`.

### Inline-level Elements

Inline elements occupy only the space bounded by the tags defining the element. They do not start on a new line and only take up as much width as necessary.

**Key Points:**
- Do not start on a new line.
- For non-replaced inline boxes, `width` and `height` do not set the inline box size; replaced inline elements such as images have intrinsic dimensions and can be sized.
- Examples: `a`, `span`, `b`, `u`, `i`, `strong`, `em`, `img`.

### Inline-block Elements

Inline-block elements combine features of both inline and block-level elements. They allow setting of width and height while still flowing with inline content.

**Key Points:**
- Display inline with other elements.
- Allow width and height settings.
- Examples in common user-agent styles: `input`, `textarea`, `button`, `select`.

## Project Structure

Organizing files in a clear, logical structure helps manage and maintain the project efficiently.

### Typical Project Structure

```
/project-root
  /css
    - base.css
    - common.css
    - index.css
  /images
  /upload
  /html
  /less
  /lib
  /js
    - main.js
  - index.html
  - favicon.ico
```

**Example:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Document</title>
  <link rel="stylesheet" href="./css/base.css">
  <link rel="stylesheet" href="./css/common.css">
  <link rel="stylesheet" href="./css/index.css">
</head>
<body>
  <!-- Content goes here -->
</body>
</html>
```

## Sprites

Sprites combine multiple images into one. They can reduce request count in some setups, but do not guarantee faster loading; image size, caching, compression, and how the assets are used also matter. This remains a useful technique for fixed icon sheets and legacy projects.

### Steps to Use Sprites

1. Create a container and set its size to the size of the desired sprite.
2. Set the sprite image as the background of the container.
3. Adjust the background position to display the correct part of the sprite.

**Example:**
```css
.sprite {
  width: 50px;
  height: 50px;
  background: url('sprite.png') no-repeat;
  background-position: -10px -20px; /* Adjust based on sprite position */
}
```

## Banner

For creating a banner with multiple images, this small CSS example shows a static selected slide. It does not implement rotation, controls, keyboard behavior, or an accessible carousel pattern. A production carousel needs visible controls, a way to pause automatic movement, and content that remains usable with assistive technology.

1. Use an unordered list (`<ul>`) with list items (`<li>`) for each image.
2. Position the list items using CSS.
3. Indicate the current image with a class like `.current`.

**Example:**
```html
<ul class="banner">
  <li class="current"><a href="image1.jpg"><img src="image1.jpg" alt="Image 1"></a></li>
  <li><a href="image2.jpg"><img src="image2.jpg" alt="Image 2"></a></li>
  <!-- Additional images -->
</ul>
```

```css
.banner {
  position: relative;
  overflow: hidden;
}
.banner li {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  display: none;
}
.banner li.current {
  display: block;
}
```

## Mobile Web Basics

### Responsive Design Principles

1. **Viewport Meta Tag:** Sets the layout viewport and initial scale used by mobile browsers; responsive CSS is still needed to adapt the layout.
   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   ```
2. **Flexible Layouts:** Use percentages, flexbox, or grid layouts for adaptable designs.
3. **Media Queries:** Adjust styles based on device characteristics.
   ```css
   @media (max-width: 600px) {
     .container {
       flex-direction: column;
     }
   }
   ```

### Common Screen Sizes

- **Historical example:** iPhone 6/7/8 had a 375×667 logical CSS-pixel display (750×1334 device pixels at DPR 2); with a `width=device-width` viewport, that logical width is the layout viewport. Treat this as a pixels-and-scale example, not a current device target.
- **Adaptive Layout:** Use relative units like percentages and rem for layout.

### Development Tools

- **Chrome DevTools:** Inspect and simulate mobile devices.
- **Responsive Design Mode:** Adjust viewport size and test responsiveness.

## Browser Support Check

Use tools like [Can I Use](https://caniuse.com) to check compatibility of web technologies across different browsers.

**Example:**
```javascript
if ('fetch' in window) {
  // Use fetch API
} else {
  // Fallback for older browsers
}
```

## Future-proof JavaScript

Isolate experimental or polyfill-required code to ensure future compatibility.

**Example:**
```html
<script>
  function startApp() {
    // Start code that depends on Promise.
  }

  if (typeof window.Promise === "function") {
    startApp();
  } else {
    var script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/promise-polyfill@8/dist/polyfill.min.js";
    script.onload = startApp;
    script.onerror = function () {
      /* Report the failure through the application's error handling. */
    };
    document.head.appendChild(script);
  }
</script>
```

This loads the fallback before starting dependent code; in a real application, use the application's script loader and an actively maintained polyfill source.

# HTML Basics

## A Sample HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Title</title>
</head>
<body>
</body>
</html>
```

### Breakdown and Best Practices

1. **DOCTYPE Declaration:**
   ```html
   <!DOCTYPE html>
   ```
   - The modern `<!DOCTYPE html>` declaration selects standards mode; it does not encode a numbered HTML version. Omitting it can put browsers into quirks mode.

2. **HTML Tag:**
   ```html
   <html lang="en">
   ```
   - The `lang` attribute declares the language of the document's text, helping browsers, speech output, and assistive technology interpret it. It is not a search-ranking switch.

3. **Head Section:**
   ```html
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Title</title>
   </head>
   ```
   - **Meta Tags:**
     - `charset="UTF-8"` declares the document's character encoding; the file's bytes must actually be encoded as UTF-8.
     - The `viewport` meta tag sets the layout viewport and initial scale used on mobile devices; it does not make a fixed-width layout responsive by itself.
   - **Title Tag:**
     - The `title` element gives the document a title used by browser interfaces and as a possible input to search-result title links. Search engines may rewrite how it appears, so keep it concise and relevant.

4. **Body Section:**
   ```html
   <body>
   </body>
   </html>
   ```
   - Contains the visible content of the page.

### Explanation of Tags and Attributes

- **Tags:** Elements or labels used to structure a webpage.
- **Attributes:** Provide additional information about an element, usually in the form of name-value pairs.

## SEO: Search Engine Optimization

To improve the visibility of your site in search engine results, consider the following:

### Important SEO Tags

1. **Title Tag:**
   ```html
   <title>Example Website - Best Products Online</title>
   ```
   - The `title` should be descriptive and include relevant keywords.

2. **Meta Description:**
   ```html
   <meta name="description" content="Example Website offers the best products online with great discounts and free shipping.">
   ```
   - Provides a brief summary that a search engine may use for a result snippet; engines can instead generate a snippet from page content, and may show different snippets for different searches.

3. **Meta Keywords (not used by Google Search):**
   ```html
   <meta name="keywords" content="online shopping, best products, discounts, free shipping">
   ```
   - Google Search does not use this tag for indexing or ranking. It is generally unnecessary; do not confuse it with visible page content or other metadata.

### Set Up Icon (Favicon)

- **Favicon:**
  ```html
  <link rel="icon" href="favicon.ico" type="image/x-icon">
  ```
  - A small icon displayed in the browser tab, bookmark list, etc.

## Commenting in HTML

- **Comment Syntax:**
  ```html
  <!-- This is a comment -->
  ```
  - Comments are not displayed in the browser and are used to leave notes or explanations in the code.

## Class Attribute

- **Usage:**
  ```html
  <div class="container main-content"></div>
  ```
  - Allows styling and manipulation of elements using CSS and JavaScript.
  - Multiple classes can be applied to a single element, separated by spaces.

## ID Attribute

- **Usage:**
  ```html
  <div id="header"></div>
  ```
  - Used to identify an element for fragment navigation, CSS, or script access.
  - Each `id` value must be unique in the document; the `id` attribute itself can appear on many elements with different values.

## Semantic Wrapping

Semantic elements express document roles and structure, helping people and software understand the content. CSS display defaults do not determine which elements may be nested; follow each element's HTML content model.

1. **Common block-display examples:**
   - User-agent styles commonly display `<div>`, `<p>`, `<h1>`, `<section>`, and `<article>` as block boxes. CSS can change those display values.

2. **Nesting Rules:**
   - A `<p>` can contain phrasing content, not a `<div>` or another `<p>`; a `<div>` can contain paragraphs. A heading also accepts phrasing content, so do not put a `<div>` inside `<h1>`.
   - Invalid example: the parser closes the paragraph when it reaches the `<div>` start tag.
     ```html
     <p>This is a paragraph <div>This should not be here</div></p>
     ```
   - Correct usage:
     ```html
     <div>
         <p>This is a paragraph</p>
         <div>This is a separate block element</div>
     </div>
     ```

### Semantic Elements

- **Examples:**
  ```html
  <header>Header content</header>
  <nav>Navigation links</nav>
  <main>Main content</main>
  <footer>Footer content</footer>
  ```
  - Using these elements makes your HTML more meaningful and easier to understand.

## Semantic Elements vs. Non-Semantic Elements

### Non-Semantic Elements

- `<div>`: Generic flow-content container used when no more meaningful element fits; often used as a styling/layout hook.
- `<span>`: Generic phrasing-content container used when no more meaningful phrasing element fits; often used for styling.

### Semantic Elements

Semantic elements clearly describe their meaning in a way that is understandable to both the developer and the browser.

- **Examples:**
  - `<header>`: Defines the header section of a document or a section.
  - `<nav>`: Defines a set of navigation links.
  - `<footer>`: Defines the footer section of a document or a section.
  - `<aside>`: Defines content that is tangentially related to the content around it.
  - `<section>`: Defines a section in a document.
  - `<article>`: Defines an independent, self-contained content.

# Basic tags

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

# HTML Lists and Tables

## Unordered List

An unordered list (`<ul>`) is used to create a list of items in no specific order. It is commonly used for bullet points.

**Syntax and Usage**

- **`<ul>`**: Wraps the entire unordered list.
- **`<li>`**: Represents each item within the list. It can contain any type of content, including other lists.

**Example**

```html
<ul>
  <li>Apple</li>
  <li>Banana</li>
</ul>
```

**Output**

<ul>
  <li>Apple</li>
  <li>Banana</li>
</ul>

**Best Practices**

- Use unordered lists for items that don't have a specific sequence.
- Keep the content of `<li>` items concise for readability.

## Ordered List

An ordered list (`<ol>`) is used to create a list of items in a specific order, typically numbered.

**Syntax and Usage**

- **`<ol>`**: Wraps the entire ordered list.
- **`<li>`**: Represents each item within the list.

**Example**

```html
<ol>
  <li>First item</li>
  <li>Second item</li>
</ol>
```

**Output**

<ol>
  <li>First item</li>
  <li>Second item</li>
</ol>

**Best** Practices

- Use ordered lists for steps, instructions, or any items that follow a specific order.
- Utilize the `type` attribute if a different numbering style is required (e.g., Roman numerals, letters).

## Description List

A description list (`<dl>`) is used to group terms and descriptions. It is useful for glossaries or lists of terms and definitions.

**Syntax and Usage**

- **`<dl>`**: Wraps the entire description list.
- **`<dt>`**: Represents a term or name.
- **`<dd>`**: Describes the term.

**Example**

```html
<dl>
  <dt>HTML</dt>
  <dd>HyperText Markup Language</dd>
  <dt>CSS</dt>
  <dd>Cascading Style Sheets</dd>
</dl>
```

**Output**

<dl>
  <dt>HTML</dt>
  <dd>HyperText Markup Language</dd>
  <dt>CSS</dt>
  <dd>Cascading Style Sheets</dd>
</dl>

**Best Practices**

- Use description lists for term-definition pairs to enhance readability and structure.
- Ensure terms and descriptions are clear and concise.

## Table 

Tables are used to display data in a structured format with rows and columns. Modern best practices emphasize accessibility and responsiveness.

**Syntax and Usage**

```html
<table>
  <caption>Fruit List</caption>
  <thead>
    <tr>
      <th>Fruit</th>
      <th>Weight</th>
      <th>Taste</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Apple</td>
      <td>150g</td>
      <td>Good</td>
    </tr>
    <tr>
      <td>Pear</td>
      <td>100g</td>
      <td>Good</td>
    </tr>
  </tbody>
</table>
```

**Output**

<table border="1">
  <caption>Fruit List</caption>
  <thead>
    <tr>
      <th>Fruit</th>
      <th>Weight</th>
      <th>Taste</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Apple</td>
      <td>150g</td>
      <td>Good</td>
    </tr>
    <tr>
      <td>Pear</td>
      <td>100g</td>
      <td>Good</td>
    </tr>
  </tbody>
</table>

The raw Markdown-rendered table examples retain `border="1"` only to make their cells visible here. For page styling, use CSS borders rather than presentational HTML attributes.

**Best** Practices

- **Accessibility**: Use `<thead>`, `<tbody>`, and `<tfoot>` to group table sections. Provide clear and concise captions and headers.
- **Responsive Design**: On narrow screens, a wrapper with `overflow-x: auto` can keep a wide data table usable without forcing the whole page to scroll horizontally.

### Table Elements

- **`<caption>`**: Describes the table's content.
- **`<thead>`**: Groups the header content.
- **`<tbody>`**: Groups the body content.
- **`<tfoot>`**: Groups the footer content.
- **`<tr>`**: Represents a table row.
- **`<th>`**: Represents a table header cell.
- **`<td>`**: Represents a table data cell.

### Example with Merged Cells

**Syntax and Usage**

```html
<table>
  <caption>Fruit List</caption>
  <thead>
    <tr>
      <th>Fruit</th>
      <th>Weight</th>
      <th>Taste</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Apple</td>
      <td rowspan="2">150g</td>
      <td>Good</td>
    </tr>
    <tr>
      <td>Pear</td>
      <!-- The rowspan cell above occupies the Weight column in this row. -->
      <td>Good</td>
    </tr>
    <tr>
      <td>Banana</td>
      <td colspan="2">50g</td>
    </tr>
  </tbody>
</table>
```

**Output**

<table border="1">
  <caption>Fruit List</caption>
  <thead>
    <tr>
      <th>Fruit</th>
      <th>Weight</th>
      <th>Taste</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Apple</td>
      <td rowspan="2">150g</td>
      <td>Good</td>
    </tr>
    <tr>
      <td>Pear</td>
      <!-- The rowspan cell above occupies the Weight column in this row. -->
      <td>Good</td>
    </tr>
    <tr>
      <td>Banana</td>
      <td colspan="2">50g</td>
    </tr>
  </tbody>
</table>

**Best Practices for Merging Cells**

- Use the `rowspan` attribute to merge cells vertically.
- Use the `colspan` attribute to merge cells horizontally.
- A spanning cell occupies a rectangle starting at its row and column; following cells fill the remaining slots. Use CSS to control how the cell's content is visually aligned.

# HTML Form Elements

## The Input Element `<input>`

The `<input>` element is one of the most versatile and commonly used elements in HTML forms. It can be configured to accept different types of data through the `type` attribute.

### Useful `type` Values

#### `text`

A single-line text field. Line breaks are automatically removed from the input value.
```html
<input type="text">
```

#### `password`

A single-line text field whose displayed value is obscured. This does not encrypt the value or make an insecure connection safe; transport security and server-side handling are separate concerns.
```html
<input type="password">
```

#### `radio`

A radio button allows a single value to be selected out of multiple choices with the same `name` value.
```html
<input type="radio" name="example"> Option 1
<input type="radio" name="example"> Option 2
```

#### `checkbox`

A checkbox allows a value to be selected or deselected. Several checkboxes may be selected; give related choices the same `name` when the submitted form should send multiple values for one field, or distinct names when they are independent fields.
```html
<input type="checkbox" name="example1"> Option 1
<input type="checkbox" name="example2"> Option 2
```

#### `file`

A control that lets the user select a file. The `accept` attribute is a browser hint/filter for likely file types, not validation or a security boundary; validate uploaded files on the server.
```html
<input type="file" accept=".jpg, .jpeg, .png">
```

#### `submit`

A button that submits the form.
```html
<input type="submit" value="Submit">
```

#### `reset`

A button that resets the contents of the form to default values. Not recommended as it can lead to accidental data loss.
```html
<input type="reset" value="Reset">
```

#### `button`

A push-button with no default behavior. Use JavaScript to add functionality.
```html
<input type="button" value="Click me" onclick="alert('Button clicked!')">
```

### Common Attributes

#### `placeholder`

Provides a hint to the user of what can be entered in the field.
It does not replace a visible, programmatically associated label.
```html
<input type="text" placeholder="Enter your name">
```

#### `name`

Provides the form-field name used when submitting a control. Radio buttons with the same name form a group in which one choice can be selected; checkboxes can share a name when multiple values belong to one field.
```html
<input type="radio" name="gender" value="male"> Male
<input type="radio" name="gender" value="female"> Female
```

#### `checked`

Sets a checkbox or radio button to be selected by default.
```html
<input type="checkbox" name="subscribe" checked> Subscribe to newsletter
```

#### `multiple`

Allows multiple files to be selected in a file input.
```html
<input type="file" name="files" multiple>
```

### Example Usage

#### Basic Form with Input Elements

```html
<form action="/submit" method="post">
  Name: <input type="text" name="name" placeholder="Enter your name"><br><br>
  Password: <input type="password" name="password"><br><br>
  Gender:
  <input type="radio" name="gender" value="male"> Male
  <input type="radio" name="gender" value="female" checked> Female<br><br>
  Interests:
  <input type="checkbox" name="interest" value="coding"> Coding
  <input type="checkbox" name="interest" value="music" checked> Music<br><br>
  Upload files: <input type="file" name="files" multiple><br><br>
  <input type="submit" value="Submit">
  <input type="reset" value="Reset">
</form>
```

For a usable form, associate each control with a `<label>` (using a matching `for`/`id` pair or by wrapping the control). The text placed next to a control in this compact example is not itself a programmatic label.

## The `button` Element

The `<button>` element is used to create clickable buttons.

### Common Attribute

#### `type`

Defines the behavior of the button. It can be `submit`, `reset`, or `button`.
Inside a form, a `<button>` without a `type` defaults to submit; set the intended type explicitly.

```html
<button type="submit">Submit</button>
<button type="reset">Reset</button>
<button type="button" onclick="alert('Button clicked!')">Click me</button>
```

### Example Usage

```html
<button>I'm a button</button>
<button type="submit">I'm a submit button</button>
<button type="reset">I'm a reset button</button>
```

## The `select` Element

The `<select>` element is used to create a drop-down list.

### Structure

- `<select></select>`: The entire drop-down menu.
- `<option></option>`: Each item in the drop-down menu.

### Example Usage

```html
<select name="cities">
  <option value="beijing">Beijing</option>
  <option value="guangzhou">Guangzhou</option>
  <option value="shanghai">Shanghai</option>
  <option value="shenzhen" selected>Shenzhen</option>
</select>
```

### Common Attributes

#### `name`

Identifies the drop-down menu when the form is submitted.

```html
<select name="city">
  <option value="new-york">New York</option>
  <option value="los-angeles">Los Angeles</option>
</select>
```

#### `multiple`

Allows multiple selections within the drop-down list.

```html
<select name="cities" multiple>
  <option value="beijing">Beijing</option>
  <option value="guangzhou">Guangzhou</option>
  <option value="shanghai">Shanghai</option>
  <option value="shenzhen">Shenzhen</option>
</select>
```

### Selected Attribute

Specifies the default selected item in the drop-down list.

```html
<select>
  <option value="option1">Option 1</option>
  <option value="option2" selected>Option 2</option>
  <option value="option3">Option 3</option>
</select>
```

### A Multi-line Text Input Control (`<textarea></textarea>`)

**Useful Attributes**

- `cols`: Specifies the visible width of the text area in characters.
- `rows`: Specifies the visible number of lines in the text area.

**Best Practices**

- **Resizing:**
  - By default, users can resize the text area by dragging the bottom-right corner. However, it is often best to control resizing via CSS to maintain layout consistency.
  - Example:
    ```css
    textarea {
        resize: none; /* Disables resizing */
    }
    ```

### Label Element (`<label></label>`)

**Usage**

Labels are used to bind a text description to a form element, enhancing accessibility and usability.

**Method 1: Using `for` Attribute**

- Give the form control an `id`, then set the label's `for` attribute to that exact value. The control may sit inside the label or elsewhere in the document.

The `label` element should identify the control's purpose; adjacent text alone does not create that programmatic association.

**Method 2: Wrapping the Form Element**

- Wrap both the form element and its content with a label tag.
- Omit the `for` attribute.

**Example**

```html
gender:
<input type="radio" name="gender" id="male" value="male"> <label for="male">male</label>
<label><input type="radio" name="gender" value="female"> female</label>
```

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
