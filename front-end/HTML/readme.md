# General

## Paths

### Absolute Path

An absolute path points directly to a location in the file system or web structure. It starts from the root directory or a full URL. While not commonly used in front-end development due to its rigidity, it's essential to understand its structure.

**Example:**
- File System: `/Users/r/Desktop/Front-end-learning/cat.jpeg`
- URL: `https://www.example.com/images/logo.gif`

### Relative Path

Relative paths are commonly used because they are flexible and easier to maintain. They define the path to a resource relative to the current file's location.

**Types:**
- **Same-level files:** In the same folder as the HTML file. Example: `filename.extension`
- **Lower-level files:** In a subfolder of the current folder. Example: `subfolder/filename.extension`
- **Upper-level files:** In the parent folder of the current folder. Example: `../filename.extension`
- **Two levels up:** Example: `../../filename.extension`

## Standard Stream

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
- Width and height settings are generally ineffective.
- Examples: `a`, `span`, `b`, `u`, `i`, `strong`, `em`, `img`.

### Inline-block Elements

Inline-block elements combine features of both inline and block-level elements. They allow setting of width and height while still flowing with inline content.

**Key Points:**
- Display inline with other elements.
- Allow width and height settings.
- Examples: `input`, `textarea`, `button`, `select`, `img`.

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

Sprites combine multiple images into one, reducing the number of server requests and improving load times.

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

For creating a banner with multiple images:

1. Use an unordered list (`<ul>`) with list items (`<li>`) for each image.
2. Position the list items using CSS.
3. Indicate the current image with a class like `.current`.

**Example:**
```html
<ul class="banner">
  <li class="current"><a href="#"><img src="image1.jpg" alt="Image 1"></a></li>
  <li><a href="#"><img src="image2.jpg" alt="Image 2"></a></li>
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

1. **Viewport Meta Tag:** Ensures proper scaling on mobile devices.
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

- **iPhone 6/7/8:** 375x667 logical resolution (750x1334 physical).
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
  if (!window.Promise) {
    // Load a Promise polyfill
    document.write('<script src="https://cdn.jsdelivr.net/npm/promise-polyfill@8/dist/polyfill.min.js"><\/script>');
  }
</script>
```

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
   - Declares the document type and version as HTML5. Ensures the browser renders the page correctly and consistently.

2. **HTML Tag:**
   ```html
   <html lang="en">
   ```
   - The `lang` attribute specifies the language of the document, which is important for accessibility and SEO.

3. **Head Section:**
   ```html
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Title</title>
   </head>
   ```
   - **Meta Tags:**
     - `charset="UTF-8"` ensures proper encoding of the document, supporting most characters.
     - `viewport` meta tag is crucial for responsive web design, ensuring the page scales correctly on different devices.
   - **Title Tag:**
     - The `title` tag specifies the page title, shown on the browser tab and in search engine results. It should be concise and relevant.

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
   - Provides a brief summary of the webpage content. It appears in search results below the title.

3. **Meta Keywords (Deprecated):**
   ```html
   <meta name="keywords" content="online shopping, best products, discounts, free shipping">
   ```
   - Historically used for specifying keywords, but now largely ignored by major search engines.

### Set Up Icon (Favicon)

- **Favicon:**
  ```html
  <link rel="shortcut icon" href="favicon.ico" type="image/x-icon">
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
  - Unique within a page, used for styling and manipulating specific elements.
  - Should only be used once per page.

## Semantic Wrapping

Using semantic HTML elements improves accessibility, SEO, and readability:

1. **Block-Level Elements:**
   - Examples: `<div>`, `<p>`, `<h1>`, `<section>`, `<article>`, etc.
   - Act as containers for other elements.

2. **Nesting Rules:**
   - Avoid nesting block-level elements like `<p>` inside other block-level elements like `<div>`, `<h1>`, etc.
   - Example of incorrect nesting:
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

- `<div>`: Used as a container for other elements, often for styling purposes.
- `<span>`: Used to apply styles to inline text or elements.

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

If the heading has a start tag and an end tag, it must have a start tag and an end tag.

If the heading has a start tag and no end tag, it must have a start tag and no end tag.

## Heading Element `<h1></h1>`

```
<h1>title</h1>
...
<h6>title</h6>
```

The titles are bold, exclusive lines. The font size gets smaller as the number increases. In development, we can manage size in CSS, so always use `<h1>` for the main title, h2 for headings, and h3 for sub-headings. (Semantic tags)

## Paragraph element `<p></p>`

`<p>context</p>`

Exclusive lines. There is a space between tags.

## The Line Break element `<br>`

Produces a line break in the text (carriage-return). It helps break paragraphs where the division of lines is significant.

## The Thematic Break (Horizontal Rule) element `<hr>`

It represents a thematic break between paragraph-level elements and draws a horizontal line on the page.

## Font elements

`<b>context</b>` or `<strong>context</strong>`: bold

`<u>context</u>` or `<ins>context</ins>`: underline

`<i>context</i>` or `<em>context</em>`: italic

`<s>context</s>` or `<del>context</del>`: deleteline

All the font elements can be used inside paragraphs.

## Image element `<img src="">`

e.g. `<img src="./cat.jpeg" alt="pic of cat" title="so cute a cat" width="200" height="150">`

Must have a start tag and must not have an end tag.

Attribute: `<attribute name>="<value>"`

Useful attributes:
src: The path of the image. See General-Path for path info. `src="<path>"`

alt: Alternative text when the image fails to load. `alt="<text>"`

title: The text shown when mouse hovering the image. Not only images can use but also other elements. `title="<text>"`

Height and width:
width: Width of the image. `width="<integer>"`

height: Height of the image. `height="<integer>"`

If only one of the width or height is set, the other will be proportionally enlarged and reduced. If both are set, it may cause the picture to be deformed.

## Audio element `<audio src="" controls></audio>`

Useful attributes:
src: the path of the audio supports MP3. See General-path for more info.

controls: display playback controls, no attribute value required

autoplay: autoplay, no attribute value required

loop: loop playback, no attribute value required

e.g. `<audio src="hello.mp3" controls autoplay loop></audio>`

## Video element `<video src="" controls></video>`

Useful attributes:
src: path of the video, support mp4. See General-path for more info.

controls: display playback controls; no attribute value required

autoplay: autoplay, no attribute value required (Google Chrome must cooperate with muted to play automatically)

loop: loop playback, no attribute value required

muted: play muted

e.g. `<video src="hello.mp4" controls autoplay loop muted></video>`

## The Anchor element `<a href="landing page full path"></a>`

e.g. `<a href="https://www.google.com">open Google</a>`

**Output**
<a href="https://www.google.com">open Google</a>

The full path of the landing page:
The website contains https://www., e.g. https://www.baidu.com
or file path, e.g. filename.html
Or empty link: #, the function is that you don't know where to jump to in the early stage of development. You can use this instead of

changing it in the future.

Useful attributes:
target: the opening form of the target page, the value could be:
\_self: the default value, jump directly from the current page
\_blank: open in new window

e.g. `<a href="https://www.baidu.com" target="_blank">Open Baidu</a>`

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

**Best** Practices

- **Accessibility**: Use `<thead>`, `<tbody>`, and `<tfoot>` to group table sections. Provide clear and concise captions and headers.
- **Responsive Design**: Ensure tables are responsive using CSS (e.g., setting `overflow-x` to `auto` for small screens).

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
- Follow the top-left rule: merged cells should remain aligned to the top and left.

# HTML Form Elements

## The Input Element `<input>`

The `<input>` element is one of the most versatile and commonly used elements in HTML forms. It can be configured to accept different types of data through the `type` attribute.

### Useful `type` Values

#### `text`

A single-line text field. Line breaks are automatically removed from the input value.
```html
<input type="text">
```

**Output**
<input type="text">

#### `password`

A single-line text field whose value is obscured. It alerts the user if the site is not secure.
```html
<input type="password">
```

**Output**
<input type="password">

#### `radio`

A radio button allows a single value to be selected out of multiple choices with the same `name` value.
```html
<input type="radio" name="example"> Option 1
<input type="radio" name="example"> Option 2
```

**Output**
<input type="radio" name="example"> Option 1
<input type="radio" name="example"> Option 2

#### `checkbox`

A checkbox allows single values to be selected or deselected. Suitable when more than one answer can be selected.
```html
<input type="checkbox" name="example1"> Option 1
<input type="checkbox" name="example2"> Option 2
```

**Output**
<input type="checkbox" name="example1"> Option 1
<input type="checkbox" name="example2"> Option 2

#### `file`

A control that lets the user select a file. Use the `accept` attribute to define the types of files that the control can select.
```html
<input type="file" accept=".jpg, .jpeg, .png">
```

**Output**
<input type="file" accept=".jpg, .jpeg, .png">

#### `submit`

A button that submits the form.
```html
<input type="submit" value="Submit">
```

**Output**
<input type="submit" value="Submit">

#### `reset`

A button that resets the contents of the form to default values. Not recommended as it can lead to accidental data loss.
```html
<input type="reset" value="Reset">
```

**Output**
<input type="reset" value="Reset">


#### `button`

A push-button with no default behavior. Use JavaScript to add functionality.
```html
<input type="button" value="Click me" onclick="alert('Button clicked!')">
```

**Output**
<input type="button" value="Click me" onclick="alert('Button clicked!')">

### Common Attributes

#### `placeholder`

Provides a hint to the user of what can be entered in the field.
```html
<input type="text" placeholder="Enter your name">
```

**Output**
<input type="text" placeholder="Enter your name">

#### `name`

Groups radio buttons together so that only one can be selected at a time.
```html
<input type="radio" name="gender" value="male"> Male
<input type="radio" name="gender" value="female"> Female
```

**Output**
<input type="radio" name="gender" value="male"> Male
<input type="radio" name="gender" value="female"> Female

#### `checked`

Sets a checkbox or radio button to be selected by default.
```html
<input type="checkbox" name="subscribe" checked> Subscribe to newsletter
```

**Output**
<input type="checkbox" name="subscribe" checked> Subscribe to newsletter

#### `multiple`

Allows multiple files to be selected in a file input.
```html
<input type="file" name="files" multiple>
```

**Output**
<input type="file" name="files" multiple>

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
  <input type="checkbox" name="interest1" value="coding"> Coding
  <input type="checkbox" name="interest2" value="music" checked> Music<br><br>
  Upload files: <input type="file" name="files" multiple><br><br>
  <input type="submit" value="Submit">
  <input type="reset" value="Reset">
</form>
```

**Output**
<form action="/submit" method="post">
  Name: <input type="text" name="name" placeholder="Enter your name"><br><br>
  Password: <input type="password" name="password"><br><br>
  Gender:
  <input type="radio" name="gender" value="male"> Male
  <input type="radio" name="gender" value="female" checked> Female<br><br>
  Interests:
  <input type="checkbox" name="interest1" value="coding"> Coding
  <input type="checkbox" name="interest2" value="music" checked> Music<br><br>
  Upload files: <input type="file" name="files" multiple><br><br>
  <input type="submit" value="Submit">
  <input type="reset" value="Reset">
</form>

## The `button` Element

The `<button>` element is used to create clickable buttons.

### Common Attribute

#### `type`

Defines the behavior of the button. It can be `submit`, `reset`, or `button`.

```html
<button type="submit">Submit</button>
<button type="reset">Reset</button>
<button type="button" onclick="alert('Button clicked!')">Click me</button>
```

**Output**
<button type="submit">Submit</button>
<button type="reset">Reset</button>
<button type="button" onclick="alert('Button clicked!')">Click me</button>

### Example Usage

```html
<button>I'm a button</button>
<button type="submit">I'm a submit button</button>
<button type="reset">I'm a reset button</button>
```
**Output**
<button>I'm a button</button>
<button type="submit">I'm a submit button</button>
<button type="reset">I'm a reset button</button>

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

**Output**
<select name="cities">
  <option value="beijing">Beijing</option>
  <option value="guangzhou">Guangzhou</option>
  <option value="shanghai">Shanghai</option>
  <option value="shenzhen" selected>Shenzhen</option>
</select>

### Common Attributes

#### `name`

Identifies the drop-down menu when the form is submitted.

```html
<select name="city">
  <option value="new-york">New York</option>
  <option value="los-angeles">Los Angeles</option>
</select>
```

**Output**
<select name="cities" multiple>
  <option value="beijing">Beijing</option>
  <option value="guangzhou">Guangzhou</option>
  <option value="shanghai">Shanghai</option>
  <option value="shenzhen">Shenzhen</option>
</select>

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

**Output**
<select name="cities" multiple>
  <option value="beijing">Beijing</option>
  <option value="guangzhou">Guangzhou</option>
  <option value="shanghai">Shanghai</option>
  <option value="shenzhen">Shenzhen</option>
</select>

### Selected Attribute

Specifies the default selected item in the drop-down list.

```html
<select>
  <option value="option1">Option 1</option>
  <option value="option2" selected>Option 2</option>
  <option value="option3">Option 3</option>
</select>
```

**Output**
<select>
  <option value="option1">Option 1</option>
  <option value="option2" selected>Option 2</option>
  <option value="option3">Option 3</option>
</select>

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

- Wrap the form element with a label tag.
- Add an `id` attribute to the form element.
- Set the `for` attribute of the label tag to the same value as the form element's `id`.

**Method 2: Wrapping the Form Element**

- Wrap both the form element and its content with a label tag.
- Omit the `for` attribute.

**Example**

```html
gender:
<input type="radio" name="gender" id="male"> <label for="male">male</label>
<label><input type="radio" name="gender"> female</label>
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