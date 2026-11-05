# What belongs in a semantic HTML document? / 语义化 HTML 文档应包含什么？

Start with a valid document shell and choose elements for their meaning. Metadata such as the page title, description, and favicon helps browsers and search results identify the page; headings and landmarks describe its content structure. / 从有效的文档骨架开始，并按语义选择元素。页面标题、描述和 favicon 等元数据帮助浏览器与搜索结果识别页面；标题层级和地标元素表达内容结构。

## HTML Basics

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
  - The browser can use the icon in its tab or bookmark UI. [HTML Standard on `rel="icon"`](https://html.spec.whatwg.org/multipage/links.html#rel-icon)

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

**See also / 另见：** [HTML and CSS Basics / HTML 与 CSS 基础](../../../../frontend/html-css/html-and-css-basics.md) for semantic HTML and accessibility.
