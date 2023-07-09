# General

## Path
- Absolute path (not commonly used): can directly reach the target location, starting from a drive letter or a full URL. E.g. `/Users/r/Desktop/Front-end learning/cat.jpeg`, `www.xxxx.cn/yy/logo.gif`
- Relative path (commonly used): start from the current file to find the file
  - Same-level files: in a folder with this HTML "filename.suffix"
  - Lower-level files: in another folder in the folder where HTML is located "Another_folder_name/filename.suffix"
  - Upper-level file: in the same folder as the folder where this HTML is located  "`../filename.suffix`" (`../` means to the upper-level directory)
  - Two levels up:  "`../../filename.suffix`" 

## Standard Stream
- Block-level elements, top-to-bottom, vertical layout, on a single line
- Inline elements or inline-block elements, from left to right, horizontal layout, automatic line splitting if there is not enough space

# Block-level Element
- A block-level element always starts on a new line, and the browsers automatically add some space (a margin) before and after the element.
- A block-level element always covers the entire width available (stretches out to the left and right as far as possible).
- The parent element's width is width, and the content stretches the height by default.
- Can set width and height
- Representative tags: `div`, `p`, `h` series, `ul`, `li`, `dl`, `dt`, `dd`, `form`, `header`, `nav`, `footer`

# Inline-level Element
- An inline element does not start on a new line.
- An inline element only takes up as much width as necessary.
- One line can display multiple.
- The content stretches the width and height by default
- Width and height cannot be set (can be set, but not valid)
- Representative tags: `a`, `span`, `b`, `u`, `i`, `s`, `strong`, `ins`, `em`, `del` ...

# Inline-block-level Element
- One line can display multiple
- Can set width and height
- Representing tags: `input`, `textarea`, `button`, `select`, `img` ...

# Project Structure
- The homepage of the website must be called `index.html`
- The project folder structure of the website: a `CSS` folder, an `image` folder, an `index.html`
- Layout: From outside to inside, from top to bottom, from left to right
- A typical root directory:
  - `favicon.ico`
  - `images` folder, for fixed pictures (logo, style modification pictures...),
  - `upload` folder, for non-fixed pictures (product pictures, promotional pictures...)
  - `index.html`
  - `HTML` folder
  - `LESS` folder
  - `CSS` folder
  - `lib` folder for icon font
  - `js` folder for javascript and flexible.js
  - `base.css` base common styles
  - `common.css` Repeated styles for multiple modules in this web page, such as head, bottom
  - `Index.css` Homepage style

```html
<link rel="stylesheet" href="./css/base.css">
<link rel="stylesheet" href="./css/common.css">
<link rel="stylesheet" href="./css/index.css">
```
Introduced in order, the externally linked style sheet will take effect

# Sprites
- Introduction to sprites: Many pictures in the project are combined into a big picture, this big picture is the sprite picture
- Advantages: reduce

 the number of server sending, reduce server pressure, improve the page loading speed
- Steps for usage:
  1. Create a box, set the size of the box to be the same as the thumbnail size
  2. Set the sprite as the background image of the box
  3. Modify the position of the background image, measure the coordinates of the upper left corner of the small image through pxcook, and set the negative values to the box's `background-position: x y;`

# bd and hd
When I don't know what class is called `<div class="hd"></div>`, `hd` means head, and similarly, `bd` means body

# Banner

<image src="banner.png">

For a banner picture like this, use `<ul> <li> <a> <img>` to put all the pictures, as many pictures as there are as many `<li>`
Then use the positioning to make the floating window on the left (`aside`)
The small dots below represent the current instead of hover. The solution is to add a `class = "current"` to `li`, and then select `.current` in CSS

# Mobile Web Basis
- The computer screen is large, usually in the centre of the version
- The mobile phone screen is small, the general width is 100%
- Google Chrome mobile phone simulator: right-click inspect, click
- Most mobile phone designs are based on iPhone 6, 7, 8 sizes, i.e., physical resolution 750\*1334 logical resolution 375\*667
- Percentage layout is also called flow layout, the effect is adaptive width, fixed height
- Sometimes the design drawing is 2 times the size. The way to judge is to see if the length is 1920. If so, select 2x in the design drawing option above pxcook

# Browser Support Check
`caniuse.com`
Can be used to check if a browser supports a certain technology

For future javascript:
Data that may be modified in the future must be written in a separate tag
The written content does not need to copy and paste multiple contents, and all the data is replaced by the back-end

# HTTML Basis

## A Sample HTML Structure
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Titile</title>
</head>
<body>
</body>
</html>
```

- Line 1: Tell the browser the version of the web page; html means it is Version html5.
- Line 2: Tell the search engine and translator the web page's language. zh-CN is simplified Chinese; en is English.
- Line 3: the head section (invisible to end-user)
- Line 4: The encoding of the website only uses UTF-8 in web development
- Line 5:
- Line 6:
- Line 7: The title of the website, shown in the name bar in the browser, is also shown in the title part of the search engine results.
- Line 8: indicates it is the end of the head section
- Line 9: body part (the only visible part)
- Line 10: indicates it is the end of the body section
- Line 11: indicates it is the end of the HTML file

Sometimes we call tags "elements" or "labels"; they are the same thing.

## SEO: search engine optimisation
- Get your site to rank high on search sites
- Ranking of bidding
- The suffix of the file be .html

## Tag Semantics (with the correct tags in the right places)
Three main SEO tags:
- Title, e.g. `<title>京东(JD.COM)-正品低价、品质保障、配送及时、轻松购物！</title>`
- Description. e.g. `<meta name="description" content="京东JD.COM-专业的综合网上购物商城，为您提供正品低价的购物选择、优质便捷的服务体验。商品来自全球数十万品牌商家，囊括家电、手机、电脑、服装、居家、母婴、美妆、个护、食品、生鲜等丰富品类，满足各种购物需求。">`
- Keywords. e.g. `<meta name="Keywords" content="网上购物,网上商城,家电,手机,电脑,服装,居家,母婴,美妆,个护,食品,生鲜,京东">`

## Set up icon
- Icon: Small icon displayed on the left side of the title page
- e.g. `<link rel="shortcut icon" href="favicon.ico" type="image/x-icon">`

## Comment in HTML:
- `<!-- context -->`

## Class attribute
- All tags have a class attribute.
- Class names cannot start with a numeric underscore
- A tag can have multiple class names at the same time, separated by spaces
- e.g. `<div class="one two three">222</div>`

## id attribute
- All tags have an id attribute
- 'id' is unique on a page and cannot be repeated
- There can only be one 'id' attribute value on a tag
- e.g. `<div id="one">222</div>`

## Semantic wrapping
- Block

-level elements act as large containers that can be nested: text, block-level elements, inline-block elements, inline elements, etc.
- But: don't nest p, div, h, etc. elements in p tags.
- Reason: Because the semantics are inappropriate since the paragraph is already a paragraph, it cannot be a title, and the title is the same.
- The 'a' element can nest any element, but the 'a' tag cannot nest another 'a' tag

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

The full path of the landing page:
The website contains https://www., e.g. https://www.baidu.com
or file path, e.g. filename.html
Or empty link: #, the function is that you don't know where to jump to in the early stage of development. You can use this instead of

 changing it in the future.

Useful attributes:
target: the opening form of the target page, the value could be:
_self: the default value, jump directly from the current page
_blank: open in new window

e.g. `<a href="https://www.baidu.com" target="_blank">Open Baidu</a>`

# Unordered List

The unordered list `<ul>` is used to indicate the entire unordered list. It is used to wrap the `<li>` tags, and it only contains `<li>` tags.

- `<li>`: Represents each item of the list and contains the content of each line. Any content can be nested within it.

Example:
```html
<ul>
    <li>apple</li>
    <li>banana</li>
</ul>
```

Output:
<ul>
    <li>apple</li>
    <li>banana</li>
</ul>

# Ordered List

The ordered list `<ol>` represents the entire ordered list. It is used to wrap the `<li>` tags, and it only contains `<li>` tags.

- `<li>`: Represents each item of the list and contains the content of each line. Any content can be nested within it.

Example:
```html
<ol>
    <li>apple</li>
    <li>banana</li>
</ol>
```

Output:
<ol>
    <li>apple</li>
    <li>banana</li>
</ol>

# Description List

The description list `<dl>` represents the entire description list. It is used to wrap the `<dt>` and `<dd>` tags, and it only contains `<dt>` and `<dd>` tags.

- `<dt>`: The Description Term element represents the title of the list. Any content can be nested within it.
- `<dd>`: The Description Details element represents each content in the list. Any content can be nested within it.


Example:
```html
<dl>
    <dt>Fruit</dt>
    <dd>Apple</dd>
    <dd>Pear</dd>
</dl>
```

Output:
<dl>
    <dt>Fruit</dt>
    <dd>Apple</dd>
    <dd>Pear</dd>
</dl>

## Table element
```
<table border="1" width="600" height="400">
    <caption>Fruit list</caption>
    <tr>
        <th>Fruit</th>
        <th>Weight</th>
        <th>Taste</th>
    </tr>
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
</table>
```

<table border="1">
    <caption>Fruit list</caption>
    <tr>
        <th>Fruit</th>
        <th>Weight</th>
        <th>Taste</th>
    </tr>
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
</table>

## Table structure (just for extension)
```
<thead> table head </thead>
<tbody> table body </tbody>
<tfoot> table foot </tfoot>
```

## Merge cells
- Top-left rule: merge up and down remains up, merge left and right remains left

Attribute name | Attribute value | Description
--- | --- | ---
rowspan | number of cells to merge | Merge vertically
colspan | number of cells to merge | Merge horizontally

```
<table border="1" width="600" height="400">
    <caption>Fruit list</caption>
    <tr>
        <th>Fruit</th>
        <th>Weight</th>
        <th>Taste</th>
    </tr>
    <tr>
        <td>Apple</td>
        <td rowspan="2">150g</td>
        <td>Good</td>
    </tr>
    <tr>
        <td>Pear</td>
        <td>Good</td>
    </tr>
</table>
```
<table border="1">
    <caption>Fruit list</caption>
    <tr>
        <th>Fruit</th>
        <th>Weight</th>
        <th>Taste</th>
    </tr>
    <tr>
        <td>Apple</td>
        <td rowspan="2">150g</td>
        <td>Good</td>
    </tr>
    <tr>
        <td>Pear</td>
        <td>Good</td>
    </tr>
</table>

```
<table border="1" width="600" height="400">
    <caption>Fruit list</caption>
    <tr>
        <th>Fruit</th>
        <th>Weight</th>
        <th>Taste</th>
    </tr>
    <tr>
        <td>Apple</td>
        <td>150g</td>
        <td>Good</td>
    </tr>
    <tr>
        <td>Pear</td>
        <td colspan="2">100g</td>
    </tr>
</table>
```

<table border="1">
    <caption>Fruit list</caption>
    <tr>
        <th>Fruit</th>
        <th>Weight</th>
        <th>Taste</th>
    </tr>
    <tr>
        <td>Apple</td>
        <td>150g</td>
        <td>Good</td>
    </tr>
    <tr>
        <td>Pear</td>
        <td colspan="2">100g</td>
    </tr>
</table>

## The Input (Form Input) element `<input>`

Useful attribute: `type`

### Useful 'type' values

#### `text`
The default value. A single-line text field. Line breaks are automatically removed from the input value. 
e.g. text: `<input type="text">`

#### `password`
A single-line text field whose value is obscured. Will alert the user if the site is not secure. 
e.g. password `<input type="password">`

#### `radio`
A radio button allows a single value to be selected out of multiple choices with the same `name` value. 
e.g. How are you going? `<input type="radio">Good.`

#### `checkbox`
A check box allows single values to be selected/deselected. Suitable for more than one answer can be selected.

#### `file`
A control that lets the user select a file. Use the `accept` attribute to define the types of files that the control can select.

#### `submit`
A button that submits the form.

#### `reset`
A button that resets the contents of the form to default values. Not recommended.

#### `button`
A push-button with no default behavior displays the `value` attribute's value, empty by default. Use JavaScript to add a function.

Common attributes when `type = "text"`: `placeholder`

#### `placeholder`
Text that prompts the user for input.
e.g. `<input type="text" placeholder="enter account name">`

Common attributes when `type = "radio"`: `name`

#### `name`
Grouping, those with the same name are grouped together, and only one of them can be selected at the same time.
e.g. gender:
```
<input type="radio" name="gender">male
<input type="radio" name="gender">female
```

Common attribute when `type = "radio"` or `type = "checkbox"`: `checked`

#### `checked`
Selected by default.
e.g. gender:
```
<input type="radio" name="gender">male
<input type="radio" name="gender" checked>female
```

Common attributes when `type = "file"`: `multiple`

#### `multiple`
Can upload multiple files at once.

All buttons (`submit`, `reset`, `button`) should be matched with the `form` tag. The usage is to wrap the `form` tag together.
```
<form action="">
  name: <input type="text">
  <br><br>
  password: <input type="password">
  <br><br>
  <input type="submit">
  <input type="reset">
</form>
```

Submit address in `action`
All buttons common attribute value: what name do you want to call
```
<input type="submit" value="free register">
<input type="button" value="free register">
```

## `button` element 

`<button></button>`

- Common attribute `type`. 
- Attribute value: `submit`, `reset`, `button`. The usage is the same as the `type` attribute of the `input` tag.
- Submit button by default in Google Chrome.
- The button is a double label, which is convenient to include other content, text, pictures, etc.
```
<button>I’m a button</button>
<button type="submit">I’m a submit button</button>
<button type="reset">I’m a reset button</button>
```

## `select`: drop-down menu labels

`<select></select>`: the entire drop-down menu labels, used to contain option labels
`<option></option>`: each item of the drop-down menu
`selected` attribute in `option` element: The default selection of the drop-down menu, if there is no selection,

 it will default to the first option
```
<select>
  <option>Beijing</option>
  <option>GuangZhou</option>
  <option>Shanghai</option>
  <option selected>Shenzhen</option>
</select>
```

## A multi-line text input control (text area) `<textarea></textarea>`

Useful attributes:
`cols`: the width of the visible part
`rows`: the number of visible lines of text
Drag the bottom-right corner can change the size, but it is best to use CSS to disable it in actual development.

## Label element `<label></label>`

Often used to bind the relationship between content and form element

Use method 1:
- Use label tags to wrap content
- Add an `id` attribute to the label tag
- Set the corresponding `id` attribute value to the `for` attribute of the label element

Use method 2:
- Use label tags to wrap content and form tags
- Delete the `for` attribute of the label tag

```
gender:
<input type="radio" name="gender" id="male"> <label for="male">male</label>
<label><input type="radio" name="gender"> female</label>
```

Semantic element `<div></div>` `<span></span>`

No semantics for these two layout elements. They can be used in other elements. Both do not have effects but can be added in CSS.

Elements with semantics (just for extension):
- `header`: web page header
- `nav`: web navigation
- `footer`: bottom of the page
- `aside`: sidebar
- `section`: area fast
- `article`: article

The mobile terminal uses more commonly and does not have any effect. Add the effect to CSS.


## Useful Character Entities:

| Result | Description         | Character Entity |
| ------ | ------------------- | ---------------- |
|        | Space               | `&nbsp;`         |
| <      | Lower than          | `&lt;`           |
| >      | Greater than        | `&gt;`           |
| "      | Quotation mark      | `&quot;`         |
| &      | Ampersand           | `&amp;`          |

These character entities are useful when working with HTML to represent special characters and prevent them from being interpreted as code or causing syntax errors. Here's a breakdown of each character entity:

- `&nbsp;`: Represents a non-breaking space, which is a space that will not be collapsed in HTML.
- `&lt;`: Represents the less than symbol (`<`), which is used in HTML tags and can be encoded to prevent it from being interpreted as the start of a tag.
- `&gt;`: Represents the greater than symbol (`>`), which is also used in HTML tags and can be encoded to prevent it from being interpreted as the end of a tag.
- `&quot;`: Represents the quotation mark (`"`), which is commonly used to enclose attribute values in HTML and can be encoded to avoid conflicting with the surrounding quotes.
- `&amp;`: Represents the ampersand symbol (`&`), which is used to start character entities in HTML itself. It needs to be encoded to avoid confusion with an actual character entity.

These character entities ensure that special characters are correctly rendered in HTML and help maintain proper syntax and formatting.

