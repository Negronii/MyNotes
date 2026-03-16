
# 0. Catalogue

### 1. Browser Basics
   - 1.1 Browser Core Components & Navigation Flow

### 2. HTML & CSS
   - 2.1 HTML & CSS Basics
   - 2.2 Box Model and BFC
   - 2.3 Flex & Grid Layout
   - 2.4 Browser - HTML & CSS Part
   - 2.5 DOM Properties
   - 2.6 CSS Interview Questions
   - 2.7 CSS Position, Display, and Animations

### 3. JavaScript Fundamentals
   - 3.1 Javascript Basics
   - 3.2 Javascript Types
   - 3.3 Map & Set in JS
   - 3.4 Memory in JS, WeakMap and WeakSet
   - 3.5 Array in JS
   - 3.6 ES6 New Methods
   - 3.7 Other JS
   - 3.8 Modern JavaScript Features

### 4. Advanced JavaScript
   - 4.1 Object, Function, and Prototype
   - 4.2 Scope & Closure
   - 4.3 Asynchronous JavaScript
   - 4.4 Iterators and Generators
   - 4.5 Error Handling

### 5. DOM & Browser APIs
   - 5.1 DOM Manipulation and Events
   - 5.2 Browser Storage and Communication
   - 5.3 Image Lazy Loading

### 6. TypeScript
   - 6.1 Advanced TypeScript

### 7. Event Loop & Runtime
   - 7.1 Event Loop
   - 7.2 Node.js Fundamentals
   - 7.3 Build Tools

### 8. Networking & Security
   - 8.1 HTTP Protocols and WebSockets
   - 8.2 Web Security and Authentication

### 9. React & Frameworks
   - 9.1 Virtual DOM and Framework Selection
   - 9.2 React Basics
   - 9.3 Advanced React
   - 9.4 Next.js

### 10. Data Structures & Algorithms
   - 10.1 Algorithms and Complexity
   - 10.2 Core Data Structures
   - 10.3 Practical Data Structure Implementations

### 11. Performance Optimization
   - 11.1 Performance Metrics and Analysis
   - 11.2 Rendering and Computation Optimization

### 12. Architecture & Design Patterns
   - 12.1 Software Design Principles
   - 12.2 Design Patterns in Practice

### 13. Libraries
   - 13.1 Lodash
   - 13.2 ahooks

### 14. Professional Skills
   - 14.1 Interview Tips
   - 14.2 Agile and Scrum

### 15. Frontend Testing
   - 15.1 Frontend Testing

### 16. Git & Version Control
   - 16.1 Git Essentials

# 1. Browser


## 1.1 Browser Basics

## Core Browser Components & Their Roles

### **1. Rendering Engine**

- **Engines**: Blink (Chrome, Edge), WebKit (Safari), Gecko (Firefox).
- **Critical Tasks**:
  - Parse HTML/CSS → DOM/CSSOM (with reentrant parsing for malformed HTML).
  - Combine DOM/CSSOM into **render tree** (excludes non-visual nodes like `<script>`, `<meta>`).
  - Handle **layout** (calculating exact position/size) and **paint** (filling pixels).
- **Example**: `display: none` removes element from render tree; `visibility: hidden` keeps it but hides.

### **2. JavaScript Engine**

- **Runtime**: V8 (Chrome), SpiderMonkey (Firefox), JavaScriptCore (Safari).
- **Key Concepts**:
  - JIT (Just-In-Time) Compilation: Converts JS to machine code during execution.
  - Event Loop & Callback Queue: Manages async operations (e.g., `setTimeout`, Promises).
  - Memory Heap & Call Stack: Tracks function execution and object allocations.

### **3. Networking Layer**

- **Optimizations**:
  - HTTP/2 multiplexing (parallel requests over a single TCP connection).
  - HSTS (Forced HTTPS), CORS preflight checks.
  - Browser cache strategies (`Cache-Control`, `ETag`).

### **4. Browser Storage**

- **Mechanisms**:
  - **SessionStorage**: Tab-specific, cleared on tab close.
  - **IndexedDB**: Transactional NoSQL for large datasets.
  - **Service Workers**: Cache API for offline-first strategies.

## URL Navigation to Page Render Flow

### **Phase 1: Resource Fetching**

- **DNS Lookup**:
  - Browser cache → OS cache → ISP’s recursive DNS resolver.
  - **Optimization**: `<link rel="dns-prefetch">` for early DNS resolution.
- **TCP Handshake**:
  - 3-way handshake (SYN, SYN-ACK, ACK). HTTPS adds TLS handshake (client/server hello, key exchange).
  - **HTTP/3**: Uses QUIC (UDP-based) to reduce latency.

### **Phase 2: Parsing & Critical Rendering Path**

1. **DOM Construction**:
   - Bytes → Characters → Tokens → Nodes → DOM Tree.
   - **Blockers**: `<script>` without `async/defer` pauses HTML parsing.
2. **CSSOM Construction**:
   - CSS rules are cascading; browsers build CSSOM tree for style computation.
   - **Flash of Unstyled Content (FOUC)**: Occurs if CSS blocks rendering.
3. **Render Tree**:
   - Combines DOM + CSSOM, excluding non-rendered nodes (e.g., `<head>`, `display: none`).

### **Phase 3: Layout, Paint, Composite**

- **Layout (Reflow)**:
  - Calculates exact position/size (e.g., % → pixels).
  - **Trigger**: Resizing, font changes, DOM manipulations.
- **Paint**:
  - Creates "paint records" for layers (e.g., background, text, borders).
- **Composite**:
  - Layers are combined in correct order (z-index, transforms).
  - **GPU Acceleration**: Offloads layer compositing to GPU (e.g., `transform: translateZ(0)`).

### **Performance Optimization Tactics**

- **Render-Blocking Mitigation**:
  - Inline critical CSS, defer non-critical JS.
  - Use `content-visibility: auto` to skip off-screen content rendering.
- **Network Optimizations**:
  - Preconnect (`<link rel="preconnect">`) for early TCP/TLS setup.
  - Lazy-load images (`loading="lazy"`), use modern formats (WebP/AVIF).
- **Runtime Efficiency**:
  - Debounce scroll/resize handlers to prevent layout thrashing.
  - Use `requestAnimationFrame` for visual updates.
- **Rehydration**: SSR → client-side JS attaches event listeners (e.g., React hydration).
- **Speculative Parsing**: Modern browsers pre-scan HTML to load resources (e.g., scripts, images) in advance.
- **Layout Thrashing**: Forced synchronous layouts (e.g., reading `offsetHeight` after DOM write) degrade performance. Use `FastDOM` or batch reads/writes.

# 2. HTML & CSS


## 2.1 HTML & CSS Basics

## CSS Units: Strategic Usage and Trade-offs

1. **Pixels (px):** Ideal for precise control (e.g., borders). Avoid for layout/typography to prevent accessibility issues with fixed sizing.
2. **Percent (%):** Context-dependent (e.g., `width: 50%` = 50% of parent). Use for grid layouts, but avoid nesting with % to prevent unexpected overflows.
3. **Ems (em):** Relative to parent `font-size` (or current element for non-`font-size`). Compounding in nested elements can cause scaling issues (e.g., `1.2em` in multiple nested lists).
4. **Rems (rem):** Root-relative. Preferred for scalable UIs. Set `html { font-size: 62.5%; }` for 1rem = 10px base (simplifies calculations while respecting user preferences).
5. **Viewport Units (vw/vh):**
   - **Caution**: `100vw` includes scrollbars (use `width: 100%` to avoid horizontal overflow).
   - **Mobile Consideration**: `vh` ignores dynamic browser UI (address bar), causing jank. Use `dvh` (dynamic viewport height) or JS for full-height elements.
6. **vmin/vmax**: Use for scaling elements proportionally (e.g., `width: 50vmin` ensures a square adjusts to the smaller viewport dimension).

## CSS Selectors: Specificity and Performance

### Specificity Hierarchy (Highest to Lowest)

1. **Inline Styles** > **IDs** > **Classes/Attributes/Pseudo-classes** > **Elements/Pseudo-elements**.
2. **Universal selector (`*`)** and combinators (e.g., `>`, `+`) have no specificity.
3. **`:not()`** adds no specificity, but its argument does (e.g., `div:not(.class)` = 1 element + 1 class).

### Critical Considerations

- **Avoid Overrides**: `#id.class` (1 ID + 1 class) beats `#id` (1 ID) in edge cases.
- **CSS-in-JS Scoping**: Libraries like styled-components generate unique class names to avoid specificity wars.
- **Cascade Layers (`@layer`)**: Control specificity by grouping styles into layers (e.g., `@layer base, components, utilities;`).

**Example: Specificity Battle**

```css
/* Specificity: 0,1,1 */
##sidebar .menu-item {
  color: red;
}

/* Specificity: 0,2,0 (WINS) */
.menu .menu-item.active {
  color: blue;
}
```

### Performance & Maintainability

- **Attribute Selectors**: Use `[data-state="active"]` for state-driven styling (decouples CSS from JS logic).
- **BEM Methodology**: `.block__element--modifier` reduces nesting and keeps specificity flat.
- **Critical CSS**: Prioritize above-the-fold content using selectors targeting key elements (e.g., `body > .header`).

## Responsive Design: Beyond Media Queries

- **Container Queries**: Style elements based on container size (e.g., `@container (width > 40em)`).
- **CSS Grid/Flexbox**: Use `fr` units and `minmax()` for intrinsic layouts (e.g., `grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))`).
- **CSS Variables with Media Queries**: Custom properties can be redefined inside media query blocks, allowing elements to reactively pick up new values at different breakpoints:

```css
:root {
  --columns: 1;
  --gap: 8px;
}
@media (min-width: 768px) {
  :root {
    --columns: 2;
    --gap: 16px;
  }
}
.grid {
  display: grid;
  grid-template-columns: repeat(var(--columns), 1fr);
  gap: var(--gap);
}
```

**Example: Modern Responsive Techniques**

```css
.card {
  container-type: inline-size;
}
@container (width > 400px) {
  .card {
    display: grid;
  }
}
```

## Inheritance in CSS

CSS inheritance works by allowing certain properties of a parent element to influence the same properties in its child elements, unless these properties are explicitly overridden. This means that if a style is defined for a parent element, the child elements will automatically adopt this style, following the "cascading" nature of CSS.

##### Properties That Inherit by Default

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
.box1 {
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
.box2 {
  border: 1px solid #ccc;
  width: 100px; /* Fixed width */
  overflow: hidden; /* Hides text that overflows the container's bounds */
  display: -webkit-box; /* Displays the container as a webkit flex box */
  -webkit-box-orient: vertical; /* Sets the children's orientation to vertical */
  -webkit-line-clamp: 3; /* Limits the box to showing 3 lines of text, with overflow indicated by an ellipsis */
}
```

This method uses `-webkit-box`, `-webkit-box-orient`, and `-webkit-line-clamp` to achieve multi-line truncation. It's important to note that this approach is somewhat limited by its compatibility with only webkit-based browsers (e.g., Safari, Chrome). However, it's widely used due to its simplicity and effectiveness in most web scenarios.

## 2.2 Box Model and BFC

## Box Model

### Layers - inner most to outer most
- **Content**: The innermost part containing actual data like text, images, or videos.
- **Padding**: Space between the content and the border, affecting the element's inner whitespace without being visible itself.
- **Border**: A potentially visible boundary surrounding the padding (if any) and content. It can be styled in various ways.
- **Margin**: The outermost space around the element, separating it from adjacent elements.

### Padding and Margin
- **Syntax**: Both `padding` and `margin` properties can specify one to four values (clockwise from top: top, right, bottom, left):
  - **One value**: Applies the same spacing on all four sides.
  - **Two values**: Specifies top and bottom (first value), and left and right (second value).
  - **Three values**: Sets top (first value), left and right (second value), and bottom (third value).
  - **Four values**: Each value applies to a specific side, starting from the top and moving clockwise.
- **Individual Properties**: Use `padding-top`, `padding-right`, `padding-bottom`, `padding-left`, and similarly for margin, to affect specific sides.

### Border
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

- `display: table-cell;`
- `display: flex;`
- `display: inline-block;`
- `overflow: hidden;` (when value is not `visible`)
- `position: absolute;`
- `position: fixed;`

These properties, when applied, do not just alter the visual representation of elements but also define their interaction with the layout and surrounding elements in terms of floating and margin behaviors.

### Practical Applications of BFC

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

**Solution:** To prevent this margin overlap, encase the second section in a div that creates a new BFC:
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

## 2.3 Flex & Grid Layout

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

CSS Grid Layout is a two-dimensional layout system for the web. It lets you layout items into rows and columns.

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

## 2.4 Browser - HTML & CSS part

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

- **Batch Style Changes**  
  Group multiple style changes into a single class adjustment to reduce the number of reflows.

- **Minimize DOM Access**  
  Modify elements offscreen or within a document fragment to limit the impact on the actual DOM.

- **Leverage Block Formatting Context**  
  Using BFC properties can prevent elements from affecting each other’s layout, thus reducing reflows.

- **Optimize Event Handling**  
  Implement debouncing or throttling to manage events that cause frequent reflows, such as resizing or scrolling.

- **Prioritize CSS3 and `requestAnimationFrame`**  
  For animations, prefer CSS3 and `requestAnimationFrame` over JavaScript-driven animations to decrease both reflow and repaint occurrences.

## `<script>` Element

The `<script>` element in HTML is used to embed or reference executable JavaScript code within an HTML document.

### Basic Usage of `<script>`

1. **Embedding JavaScript:**

   ```html
   <script>
     // JavaScript code here
   </script>
   ```

2. **Referencing an External Script:**
   ```html
   <script src="path/to/script.js"></script>
   ```

### `defer` and `async` Attributes

Both `defer` and `async` attributes are used to control how scripts are loaded and executed, especially for scripts that are referenced from external files.

1. **`defer` Attribute:**
   - The `defer` attribute ensures that the script is executed only after the HTML document has been completely parsed.
   - Scripts with the `defer` attribute are executed in the order they appear in the document.

2. **`async` Attribute:**
   - The `async` attribute allows the script to be executed asynchronously as soon as it is available.
   - Scripts with the `async` attribute are executed as soon as they are downloaded, without waiting for the HTML parsing to complete.
   - The execution order is not guaranteed; scripts may execute in any order.

### When to Use `async` and `defer`

1. **`async`:**
   - Use `async` for scripts that are independent and do not rely on other scripts or the HTML structure.
   - Ideal for analytics scripts, ads, or any script that does not need to manipulate the DOM immediately.

2. **`defer`:**
   - Use `defer` for scripts that need to manipulate the DOM or depend on other scripts.
   - Suitable for scripts that need to maintain order and interact with the document content.

### Best Practices for `<script>` Element

1. **Store JavaScript in External Files:**
   For readability and maintainability, store JavaScript in external files rather than embedding it directly within HTML.
2. **Place `<script>` tags just before the closing `</body>` tag:**
   Ensure the HTML is fully loaded before any script runs.
3. **Minimize and Compress Scripts:**
   - Reduce size and improve load times. Use tools like UglifyJS, Terser.
4. **Use Non-Blocking JavaScript:**
   - Avoid blocking the rendering of the page by using `defer` or `async`.
   - Ensuring that the static content loads first.

## 2.5 DOM Properties

## Element Dimension Properties

### `offsetHeight` / `offsetWidth`

The total visible size of an element including padding, border, and scrollbar (if rendered). Excludes margin.

```
offsetHeight = content height + padding-top + padding-bottom + border-top + border-bottom + horizontal scrollbar height
```

### `clientHeight` / `clientWidth`

The visible content area plus padding, but excluding border, scrollbar, and margin. This represents the space actually available for content inside the element.

```
clientHeight = content height + padding-top + padding-bottom (no border, no scrollbar)
```

### `scrollHeight` / `scrollWidth`

The full size of an element's content, including the parts hidden by overflow. If the content fits within the element, `scrollHeight` equals `clientHeight`.

```
scrollHeight = total content height + padding (including overflowed content not visible on screen)
```

### Quick Comparison

```
┌─────────────────────────────────────── margin ───┐
│ ┌─────────────────────────────── border ────────┐ │
│ │ ┌──────────────────────── padding ──────────┐ │ │
│ │ │ ┌──────────────────── content ──────────┐ │ │ │
│ │ │ │                                       │ │ │ │
│ │ │ │                                       │ │ │ │
│ │ │ └───────────────────────────────────────┘ │ │ │
│ │ └───────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────┘

offsetHeight = border + padding + content + scrollbar
clientHeight = padding + content (no border, no scrollbar)
scrollHeight = padding + full content (including overflow)
```

### `scrollTop` / `scrollLeft`

The number of pixels the content has been scrolled vertically or horizontally. This property is both readable and writable, making it useful for programmatic scroll control.

```javascript
const el = document.getElementById('container');
console.log(el.scrollTop);
el.scrollTop = 0; // scroll back to top
```

### `offsetTop` / `offsetLeft`

The distance from the element's outer border to its `offsetParent`'s inner border. The `offsetParent` is the nearest positioned ancestor (an element with `position` other than `static`), or the `<body>` element if no positioned ancestor exists.

## `getBoundingClientRect()`

Returns a `DOMRect` object providing the size and position of an element relative to the viewport. This is the most reliable way to get an element's position for calculations involving scroll, visibility checks, or tooltip placement.

```javascript
const rect = element.getBoundingClientRect();
// rect.top     - distance from viewport top to element top
// rect.bottom  - distance from viewport top to element bottom
// rect.left    - distance from viewport left to element left
// rect.right   - distance from viewport left to element right
// rect.width   - element width (including border)
// rect.height  - element height (including border)
```

`rect.width` and `rect.height` are equivalent to `offsetWidth` and `offsetHeight`.

**Common use case -- checking if an element is in the viewport:**

```javascript
function isInViewport(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top < window.innerHeight &&
    rect.bottom > 0 &&
    rect.left < window.innerWidth &&
    rect.right > 0
  );
}
```

## 2.6 CSS Interview Questions

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

#### CSS Centering Techniques
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

## Retina Screen and 1px Lines Implementation
When designing for Retina displays, setting elements to 1px using CSS can result in lines that appear too thick, due to some mobile phones having a Device Pixel Ratio (DPR) of 2. This means 1 CSS pixel could use 2 physical pixels, making the line appear thicker than intended. Directly setting elements to 0.5px can lead to compatibility issues across different browsers. 

### Using CSS Pseudo-elements and Transform Property:  
To achieve the desired 1px line appearance on Retina screens, we can use CSS pseudo-elements combined with the `transform` property for optimization. 

```css
.box::before {
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
.box {
  box-shadow: 0 0 0 0.5px #d9d9d9;
}
```

This method applies a `box-shadow` that mimics a border, allowing for the adjustment of its thickness to achieve the desired 0.5px visual effect on Retina displays. It's a versatile approach that maintains the element's aesthetic, including when a border-radius is applied, ensuring the visual consistency of the design across high-resolution screens.

## How to Prevent 300ms Delay for Double Click to Zoom on Mobile Phones?
On mobile web applications, a common issue is the 300ms delay when users attempt to double-click (tap) to zoom. This delay was originally implemented to differentiate between a tap (single click) and a double-tap (double click). However, this can interfere with the responsiveness of web applications. In the past, developers used libraries like FastClick to circumvent this delay. Modern browsers have introduced ways to address this issue by detecting the site's responsiveness through meta tags.

To prevent the 300ms delay on mobile devices without relying on external libraries like FastClick, ensure your web application is using responsive design principles. Implement the following meta tag in your HTML:
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```
This meta tag informs the browser that your website is optimized for mobile devices, prompting it to disable the 300ms delay for a better user experience. This approach is preferred as it relies on standard responsive design practices rather than additional scripts, improving your website's performance and compatibility.

## 2.7 CSS Position, Display, and Animations

## CSS Position, Display, and Animations

### 1. CSS `position` Property

#### Overview

The `position` property determines how an element is positioned in the document flow and how it affects layout calculations.

#### `position: static` (default)

- Default behavior: element flows normally in document order
- `top`, `right`, `bottom`, `left`, and `z-index` have no effect

```css
.box {
  position: static;
}
```

#### `position: relative`

- Element remains in normal flow; space is reserved as if it were not positioned
- `top`, `right`, `bottom`, `left` offset the element from its original position
- Creates a new positioning context for absolutely positioned descendants

```css
.box {
  position: relative;
  top: 10px;
  left: 20px;
}
```

#### `position: absolute`

- Element is removed from normal flow; no space reserved
- Positioned relative to nearest **positioned ancestor** (ancestor with `position` other than `static`)
- If no positioned ancestor exists, positioned relative to the initial containing block (usually `html`)

```css
.parent {
  position: relative; /* Creates positioning context */
}

.child {
  position: absolute;
  top: 0;
  right: 0;
}
```

#### `position: fixed`

- Removed from normal flow; positioned relative to the **viewport**
- Stays in place during scroll (unless `transform`, `filter`, or `perspective` is applied to an ancestor, which creates a new containing block)

```css
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
}
```

#### `position: sticky`

- Hybrid: element starts in normal flow, then behaves like `fixed` once the scroll position crosses a specified threshold
- Requires at least one of `top`, `right`, `bottom`, `left` to be set

```css
.header {
  position: sticky;
  top: 0;
}
```

#### Stacking Context and `z-index`

- `z-index` controls stacking order along the z-axis only within the same stacking context
- Elements with `position` other than `static` create a stacking context when `z-index` is set (or `opacity` < 1, `transform`, `filter`, etc.)
- A stacking context isolates its children; a child's `z-index` cannot compare with elements outside its stacking context

```css
.layer-a {
  position: relative;
  z-index: 1;
}

.layer-b {
  position: relative;
  z-index: 2; /* Renders above layer-a */
}
```

---

### 2. `display: none` vs `visibility: hidden` vs `opacity: 0`

| Aspect | `display: none` | `visibility: hidden` | `opacity: 0` |
|--------|----------------|---------------------|--------------|
| **Space in layout** | No space; element removed from flow | Space reserved; layout unchanged | Space reserved; layout unchanged |
| **Event handling** | Not clickable; no pointer events | Not clickable; no pointer events | Clickable by default; receives events |
| **Accessibility** | Screen readers ignore | Screen readers ignore | Screen readers may still announce |
| **Transitions** | Cannot animate (no intermediate state) | Can animate `visibility` | Can animate `opacity` |
| **Reflow/repaint** | Causes reflow when toggled | Repaint only (no layout change) | Repaint only (no layout change) |
| **Child visibility** | Children hidden | Children inherit visibility | Children inherit opacity |

#### Additional Notes

- **`visibility: hidden`** — children can override with `visibility: visible` to become visible again
- **`opacity: 0`** — use `pointer-events: none` when you want to hide without receiving clicks
- **`display: none`** — best for conditional rendering (e.g., responsive toggles) since it fully removes the element from layout

```css
.hidden-flow { display: none; }
.hidden-space { visibility: hidden; }
.hidden-transparent { opacity: 0; pointer-events: none; }
```

---

### 3. CSS Transitions and Animations

#### Transitions

Transitions animate property changes from one state to another when a specified property changes.

**Shorthand syntax:**

```css
.element {
  transition: property duration timing-function delay;
}

/* Example */
.button {
  transition: background-color 0.3s ease-in-out 0.1s;
}
```

**Individual properties:**

| Property | Purpose |
|----------|---------|
| `transition-property` | Properties to animate (e.g., `all`, `color`, `transform`) |
| `transition-duration` | Length of transition (e.g., `0.3s`, `300ms`) |
| `transition-timing-function` | Easing curve (`ease`, `linear`, `ease-in`, `ease-out`, `cubic-bezier()`) |
| `transition-delay` | Delay before transition starts |

```css
.element {
  transition-property: transform, opacity;
  transition-duration: 0.3s, 0.2s;
  transition-timing-function: ease-out, linear;
  transition-delay: 0s, 0.1s;
}
```

#### `@keyframes` and `animation`

Keyframes define intermediate states for animation; `animation` applies them.

```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(10%); }
  100% { transform: translateX(0); }
}

.box {
  animation: fadeIn 0.5s ease-out forwards;
}
```

**Individual properties:**

| Property | Purpose |
|----------|---------|
| `animation-name` | Keyframes name |
| `animation-duration` | Length of one cycle |
| `animation-timing-function` | Easing per keyframe |
| `animation-delay` | Delay before start |
| `animation-iteration-count` | `1`, `infinite`, or number |
| `animation-direction` | `normal`, `reverse`, `alternate`, `alternate-reverse` |
| `animation-fill-mode` | `none`, `forwards`, `backwards`, `both` |
| `animation-play-state` | `running` or `paused` |

#### `transform` Properties

| Property | Effect |
|----------|--------|
| `translate(x, y)` | Move element |
| `translateX(x)` | Move horizontally |
| `translateY(y)` | Move vertically |
| `translateZ(z)` | Move on z-axis (requires 3D context) |
| `rotate(angle)` | Rotate 2D |
| `rotateX/Y/Z(angle)` | Rotate 3D |
| `scale(x, y)` | Resize |
| `scaleX(x)` / `scaleY(y)` | Resize per axis |

```css
.card {
  transform: translate(10px, 20px) rotate(5deg) scale(1.05);
}
```

#### GPU Compositing and Hardware Acceleration

- Animating `transform` and `opacity` typically triggers compositing (GPU layer) instead of layout/paint recalculations
- `will-change` hints to the browser that a property will change, allowing it to optimize ahead of time

```css
.animated {
  will-change: transform;
  transform: translateZ(0); /* Force GPU layer */
}
```

- **`transform: translateZ(0)`** — promotes a layer to the compositor without visible movement
- **Caution:** Overuse of `will-change` or `translateZ(0)` can increase memory pressure; use only where needed for performance

# 3. JavaScript 101


## 3.1 Javascript Basics

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

**Block Scope and Temporal Dead Zone (TDZ)**

The `let` keyword declares a block-scoped variable. Although `let` declarations are hoisted to the top of their block, they enter a **Temporal Dead Zone (TDZ)** from the start of the block until the declaration is reached. Accessing the variable within the TDZ throws a `ReferenceError`.

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

- Block-scoped: accessible only within the block where declared. (note `var` is function-scoped, so `var` can be used outside `if` or `for` blocks, but `let` cannot)
- Subject to the Temporal Dead Zone: the variable exists in scope but cannot be accessed until its declaration line is reached.
- Cannot be redeclared within the same block.

### `const` Declaration

**Block Scope and Immutable Binding**

`const` behaves like `let` in terms of block scope and the Temporal Dead Zone, but it requires that the variable be initialized at the time of declaration. Once set, the variable’s binding cannot be reassigned, although the content of mutable objects can still be altered.

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

### Best Practices

ECMAScript 6 introduced `let` and `const` to address the issues associated with `var` and provide more robust variable declaration options. Here are some best practices for using these declarations effectively:

1. Do not use `var` unless necessary, as `let` and `const` offer better scoping and error prevention.

## 3.2 Javascript Types

## Primitive Types
Primitive types are the most basic data types in JavaScript. They are immutable and have a fixed memory allocation size. The primitive types in JavaScript are:

1. **`undefined`**:
   - Represents an undefined value.
   - Default value of uninitialized variables.
   - Should not be explicitly assigned to a variable.
   - Example: `let x; console.log(x); // undefined`

2. **`null`**:
   - Represents an intentional absence of any object value.
   - Often used to indicate a deliberate non-value.
   - `typeof null` returns `'object'`, which is a historical artifact in JavaScript.
   - Example: `let y = null; console.log(y); // null`

3. **`boolean`**:
   - Represents a logical entity and can have two values: `true` and `false`.
   - Type conversion to boolean:
     - Strings: Only an empty string (`''`) is `false`; all other strings are `true`.
     - Numbers: `0`, `-0`, `NaN`, `null`, `undefined`, and `false` are `false`; all other numbers are `true`.
     - Objects: Any object that is not `null` or `undefined` is `true` (e.g., `{}` is `true`).
   - Example: `let isTrue = true; let isFalse = false;`

4. **`number`**:
   - Represents numeric values, following the IEEE 754 standard.
   - Special values: `Infinity`, `-Infinity`, and `NaN` (Not-a-Number).
   - `NaN` is unique: `NaN !== NaN`. Use `Number.isNaN()` to check for `NaN`.
   - Type conversion to number:
     - `Number('')` is `0`.
     - `Number('123')` is `123`.
     - `Number('abc')` is `NaN`.
     - `Number(true)` is `1`.
     - `Number(false)` is `0`.
     - `Number(null)` is `0`.
     - `Number(undefined)` is `NaN`.
     - `Number({})` is `NaN`.
   - Example: `let num = 42; let inf = 1/0; // Infinity`

5. **`string`**:
   - Represents a sequence of characters.
   - Immutable: once created, they cannot be changed.
   - Example: `let str = 'Hello, world!';`

6. **`symbol`** (added in ES6):
   - Represents a unique identifier.
   - Created using the `Symbol()` function.
   - Example: `let sym = Symbol('description');`
   - It is often used as an object property key to avoid name clashes, e.g. in function prototype method like .call, .apply, .bind.

7. **`bigint`** (added in ES11):
   - Represents whole numbers larger than `Number.MAX_SAFE_INTEGER`.
   - Created by appending `n` to the end of an integer or using the `BigInt` function.
   - Example: `let big = 123456789012345678901234567890n;`


## Explain the difference between primitive types and reference types
In JavaScript, primitive types and reference types are stored and accessed differently, which affects how they are used in programming.

Primitive types, such as `number`, `string`, `boolean`, `null`, `undefined`, `symbol`, and `bigint`, are stored directly in the variable's memory location, usually on the stack. This direct storage enables quick access and efficient memory management, particularly for simple, immutable values.

In contrast, reference types, like `object`, `array`, and `function`, are stored in the heap. When you create a reference type, the JavaScript engine allocates memory in the heap and stores the data there. The variable on the stack then holds a reference (or pointer) to that memory location. This means when you manipulate an object or an array, you're working through a reference. Any changes made to the object or array are reflected across all references to that object, as they all point to the same memory location in the heap.

### Example Question
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

**Outputs:**  

- `console.log(a.x)` prints `undefined`, because 'a' now points to `{n: 2}`, which does not have an 'x' property.
- `console.log(b.x)` prints `{n: 2}`, because 'b' still points to the original object, which now includes `x: {n: 2}`.


## Determining Variable Types in JavaScript

##### `typeof` Operator
**Overview:**
The `typeof` operator is a straightforward tool used to determine the primitive type of a variable. Note that `typeof` is an operator, like `+` or `-`, not a function.

**Examples and Usage:**
```javascript
console.log(typeof 1); // Output: 'number'
console.log(typeof 'test'); // Output: 'string'
console.log(typeof true); // Output: 'boolean'
console.log(typeof null) // Output: 'object', because null is a empty object reference!!!
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

**Symbol.hasInstance**
It use Symbol.hasInstance method to determine if a constructor object recognizes an object as its instance.
```javascript
function Foo() {}
let f = new Foo();
console.log(Foo[Symbol.hasInstance](f)); // Output: true
```
This attribute is defined in Function.prototype, so it can be used by all functions or constructors (classes).

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

## 3.3 Map & Set in JS

## `Map` Object

### Creating a Map

```javascript
let myMap = new Map();
```

### Setting Values

To add or update elements in a `Map`, use the `set` method.

```javascript
myMap.set('key1', 'value1');
myMap.set('key2', 'value2');
myMap.set(3, 'value3'); // Keys can be of any type
```

### Getting Values

To retrieve the value associated with a key, use the `get` method.

```javascript
let value1 = myMap.get('key1'); // 'value1'
let value2 = myMap.get('key2'); // 'value2'
let value3 = myMap.get(3);      // 'value3'
```

### Deleting Values

To remove an element from the `Map` by key, use the `delete` method.

```javascript
myMap.delete('key2'); // Removes the key-value pair with key 'key2'
```

### Clearing the Map

To remove all elements from the `Map`, use the `clear` method.

```javascript
myMap.clear(); // Empties the Map
```

### Checking for Existence

To check if a key exists in the `Map`, use the `has` method.

```javascript
let hasKey1 = myMap.has('key1'); // true or false
```

### Traversing a Map

You can traverse a `Map` using several methods:

1. **Using `for...of` loop:**

   ```javascript
   for (let [key, value] of myMap) {
       console.log(key, value);
   }
   ```

2. **Using `forEach` method:**

   ```javascript
   myMap.forEach((value, key) => {
       console.log(key, value);
   });
   ```

3. **Iterating over keys:**

   ```javascript
   for (let key of myMap.keys()) {
       console.log(key);
   }
   ```

4. **Iterating over values:**

   ```javascript
   for (let value of myMap.values()) {
       console.log(value);
   }
   ```

5. **Iterating over entries:**

   ```javascript
   for (let [key, value] of myMap.entries()) {
       console.log(key, value);
   }
   ```

### Example Usage

```javascript
let myMap = new Map();

// Adding elements
myMap.set('name', 'Alice');
myMap.set('age', 30);
myMap.set('job', 'developer');

// Getting elements
console.log(myMap.get('name')); // Alice
console.log(myMap.get('age'));  // 30

// Checking existence
console.log(myMap.has('job'));  // true

// Deleting an element
myMap.delete('age');

// Traversing the Map
myMap.forEach((value, key) => {
    console.log(`${key}: ${value}`);
});

// Clearing the Map
myMap.clear();
console.log(myMap.size); // 0
```

## JavaScript `Set` Object

The `Set` object is a collection of unique values. A value in a `Set` may only occur once; it is unique in the `Set`'s collection. The `Set` object lets you store unique values of any type, whether primitive values or object references.

### Key Methods

- **`add(value)`**: Adds a new element with the given value to the `Set`.
  ```javascript
  const mySet = new Set();
  mySet.add(1);
  mySet.add(5);
  mySet.add('some text');
  ```

- **`has(value)`**: Checks if the `Set` contains a specified value.
  ```javascript
  console.log(mySet.has(1)); // true
  console.log(mySet.has(3)); // false
  ```

- **`delete(value)`**: Removes the specified value from the `Set`.
  ```javascript
  mySet.delete(5);
  console.log(mySet.has(5)); // false
  ```

- **`clear()`**: Removes all elements from the `Set`.
  ```javascript
  mySet.clear();
  console.log(mySet.size); // 0
  ```

- **`size`**: Returns the number of values in the `Set`.
  ```javascript
  console.log(mySet.size); // 3 (if 3 elements were added)
  ```

### Traversing a `Set`

You can traverse a `Set` using various methods:

- **`for...of` Loop**: Iterates over the values of the `Set`.
  ```javascript
  for (let value of mySet) {
    console.log(value);
  }
  ```

- **`forEach` Method**: Executes a provided function once for each value in the `Set`.
  ```javascript
  mySet.forEach(value => {
    console.log(value);
  });
  ```

- **`values` Method**: Returns a new iterator object containing the values for each element in the `Set`.
  ```javascript
  const iterator = mySet.values();
  for (let value of iterator) {
    console.log(value);
  }
  ```

- **`keys` Method**: (Alias for `values` method) Returns a new iterator object containing the values for each element in the `Set`.
  ```javascript
  const iterator = mySet.keys();
  for (let value of iterator) {
    console.log(value);
  }
  ```

- **`entries` Method**: Returns a new iterator object containing an array of `[value, value]` for each element in the `Set`.
  ```javascript
  const iterator = mySet.entries();
  for (let entry of iterator) {
    console.log(entry);
  }
  ```

### Example Usage

```javascript
const mySet = new Set([1, 2, 3, 4]);

// Add values
mySet.add(5);
mySet.add(5); // Duplicate, will not be added

// Check for values
console.log(mySet.has(1)); // true
console.log(mySet.has(6)); // false

// Delete a value
mySet.delete(3);
console.log(mySet.has(3)); // false

// Traverse the Set
mySet.forEach(value => {
  console.log(value); // 1, 2, 4, 5
});

// Clear the Set
mySet.clear();
console.log(mySet.size); // 0

## 3.4 Memory in JS, WeakMap and WeakSet

## Explain how the stack and heap are used in memory management for frontend applications

### The stack
It operates on a Last In, First Out (LIFO) principle, efficiently managing function calls and primitive data types. When a function is invoked, its variables are pushed onto the stack, and upon the function's completion, they are removed. This system is particularly suitable for handling temporary, short-lived data. However, the stack's limited size means excessive usage can result in a stack overflow error.

### The heap
It's used for dynamic allocation, primarily for objects and complex data structures. Unlike the stack, the heap is a larger, unstructured memory pool that requires manual management. Memory allocation and deallocation in the heap are handled by the JavaScript engine, which includes tasks like object creation and garbage collection.

## WeakMap and WeakSet in JavaScript

WeakMap and WeakSet are specialized collections in JavaScript that store their elements weakly, meaning the elements do not prevent garbage collection. This makes them particularly useful for managing caches, tracking object references, and associating metadata with objects without affecting their lifecycle.

### WeakMap

A `WeakMap` is a collection of key-value pairs where the keys are objects and the values can be any arbitrary value. The key feature of a `WeakMap` is that it allows the garbage collection of its keys when there are no other references to them. Here are some important characteristics and best practices:

- **Automatic Garbage Collection**: If a key object in a `WeakMap` is no longer referenced elsewhere, it can be garbage-collected, and the corresponding value in the `WeakMap` will also be removed.

- **Non-Enumerability**: `WeakMap` keys are not enumerable, which means you cannot iterate over the keys or values of a `WeakMap`. This ensures that the data remains private and is not accidentally exposed.

- **Use Case for Private Data**: `WeakMap` is ideal for associating private data with objects. For example, you can use a `WeakMap` to store private properties for objects created within a closure, ensuring that these properties are only accessible through the `WeakMap`.

- **Memory Efficiency**: By allowing keys to be garbage-collected, `WeakMap` helps in managing memory efficiently, especially in scenarios where objects are created and discarded frequently.

**Example Usage:**  
```javascript
const privateData = new WeakMap();

class MyClass {
  constructor() {
    privateData.set(this, { secret: 'hidden' });
  }

  getSecret() {
    return privateData.get(this).secret;
  }
}

const instance = new MyClass();
console.log(instance.getSecret()); // 'hidden'

// When `instance` is no longer referenced, the key-value pair in `privateData` can be garbage-collected.
```

### WeakSet

A `WeakSet` is a collection of objects, where an object can be a member of the set only once. Similar to `WeakMap`, the objects in a `WeakSet` are held weakly, meaning they do not prevent garbage collection.

- **Automatic Garbage Collection**: Objects in a `WeakSet` that are no longer referenced elsewhere can be garbage-collected.

- **Non-Enumerability**: `WeakSet` does not provide methods to iterate over its elements, ensuring that the objects it contains are not exposed inadvertently.

- **Use Case for Tracking Objects**: `WeakSet` is useful for tracking objects without preventing their garbage collection. For example, you can use a `WeakSet` to keep track of which objects have been processed without risking memory leaks.

**Example Usage:**  
```javascript
const processedObjects = new WeakSet();

function process(obj) {
  if (!processedObjects.has(obj)) {
    // Process the object
    processedObjects.add(obj);
  }
}

const obj1 = {};
process(obj1);

// When `obj1` is no longer referenced, it can be garbage-collected, and will be removed from `processedObjects`.
```

### Summary

- **WeakMap**: Associates data with objects without preventing their garbage collection. Ideal for private data and caches.
- **WeakSet**: Tracks objects for presence checks without preventing their garbage collection. Useful for tracking the state of objects.

Both `WeakMap` and `WeakSet` are powerful tools for managing memory and ensuring efficient garbage collection in JavaScript applications. They help avoid memory leaks by not holding strong references to their keys or elements, making them suitable for scenarios where object lifecycles are dynamic and unpredictable.

## 3.5 Array in JS

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

### Concatenation
- **Method:** `concat()`
- **Description:** Joins two or more arrays, returning a new array without altering the originals.
- **Example:**
  ```javascript
  const array1 = ['a', 'b', 'c'];
  const array2 = ['d', 'e', 'f'];
  const newArray = array1.concat(array2);
  console.log(newArray);  // Output: ['a', 'b', 'c', 'd', 'e', 'f']
  ```

### Element Checking
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

### Filtering
- **Method:** `filter()`
- **Description:** Creates a new array with all elements that pass the test implemented by the provided function.
- **Example:**
  ```javascript
  const words = ['spray', 'limit', 'elite', 'exuberant', 'destruction', 'present'];
  const result = words.filter(word => word.length > 6);
  console.log(result);  // Output: ['exuberant', 'destruction', 'present']
  ```

### Mapping
- **Method:** `map()`
- **Description:** Creates a new array populated with the results of calling a provided function on every element in the calling array.
- **Example:**
  ```javascript
  const numbers = [1, 4, 9, 16];
  const roots = numbers.map(Math.sqrt);
  console.log(roots);  // Output: [1, 2, 3, 4]
  ```

### Sorting
- **Method:** `sort()`
- **Description:** Sorts the elements of an array in place and returns the array. The sort is not necessarily stable or in numerical order by default.
- **Example:**
  ```javascript
  const months = ['March', 'Jan', 'Feb', 'Dec'];
  months.sort();
  console.log(months);  // Output: ['Dec', 'Feb', 'Jan', 'March']
  ```

### Reversing
- **Method:** `reverse()`
- **Description:** Reverses the array in place. The first array element becomes the last, and the last array element becomes the first.
- **Example:**
  ```javascript
  const array1 = ['one', 'two', 'three'];
  array1.reverse();
  console.log(array1);  // Output: ['three', 'two', 'one']
  ```

### Conversion to String
- **Method:** `toString()`
- **Description:** Converts an array to a string of comma-separated array values.
- **Example:**
  ```javascript
  const array1 = [1, 2, 'a', '1a'];
  console.log(array1.toString());  // Output: '1,2,a,1a'
  ```

### Index Finding
- **Methods:**
  - `indexOf()`: Returns the first index at which a given element can be found in the array, or -1 if it is not present.
  - `lastIndexOf()`: Returns the last index at which a given element can be found in the array, or -1 if it is not present.
- **Examples:**
  ```javascript
  const beasts = ['ant', 'bison', 'camel', 'duck', 'bison'];
  console.log(beasts.indexOf('bison'));        // Output: 1
  console.log(beasts.lastIndexOf('bison'));   // Output: 4
  ```

## Array Flattening Function in JavaScript

### Recursive Approach
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

## 3.6 ES6 New Methods

## New Methods Introduced in ES6
### `Object.assign`
`Object.assign` is used to copy the values of all [[enumerable]] own properties from one or more source objects to a target object. It returns the target object. Note this is shallow copy. It will take later one for same property.

```javascript
const target = { a: 1, b: 2 };
const source = { b: 3, c: 4 };
const result = Object.assign(target, source);
// { a: 1, b: 3, c: 4 }

const obj1 = { a: 1, b: 2 };
const obj2 = { b: 3, c: 4 };
const merged = Object.assign({}, obj1, obj2);
// { a: 1, b: 3, c: 4 }
```

### `Object.is`

`Object.is` is used to determine whether two values are the same value. It is similar to the strict equality operator `===`, but there are some differences:
- `NaN` is considered the same as `NaN`.
- `+0` and `-0` are considered different.

```javascript
Object.is(NaN, NaN); // true
Object.is(+0, -0); // false
```

### `Object.keys`

`Object.keys` is used to return an array of a given object's own enumerable property names.

```javascript
const obj = { a: 1, b: 2, c: 3 };
const keys = Object.keys(obj);
// ['a', 'b', 'c']
```

### `Object.values`

`Object.values` is used to return an array of a given object's own enumerable property values.

```javascript
const obj = { a: 1, b: 2, c: 3 };
const values = Object.values(obj);
// [1, 2, 3]
```

### `Object.entries`

`Object.entries` is used to return an array of a given object's own enumerable property [key, value] pairs.

```javascript
const obj = { a: 1, b: 2, c: 3 };
const entries = Object.entries(obj);
// [['a', 1], ['b', 2], ['c', 3]]
```

These methods are useful for iterating over objects and working with their properties in various scenarios.

### `Array.from`

`Array.from` is used to create a new, shallow-copied Array instance from an array-like or iterable object. Optional parameters allow mapping each element through a function, transforming them during creation.

```javascript
const arrayLike = { 0: 'a', 1: 'b', length: 2 };
const arr = Array.from(arrayLike);
// ['a', 'b']
```

### `Array.of`

`Array.of` is used to create a new Array instance with a variable number of elements, regardless of number or type of the arguments. This method is especially useful when you want to create an array from a set of elements.

```javascript
const arr1 = Array.of(1, 2, 3);
// [1, 2, 3]

## 3.7 Other JS

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

## `==` vs `===`

- `==` (loose equality) performs **type coercion** before comparing. Values are converted to a common type.
- `===` (strict equality) compares both **value and type** without conversion.

```javascript
5 == '5';          // true  (string '5' coerced to number)
null == undefined; // true  (special rule)
0 == false;        // true  (false coerced to 0)
'' == false;       // true  (both coerced to 0)

5 === '5';          // false (different types)
null === undefined; // false (different types)
0 === false;        // false (different types)
```

Always use `===` unless you intentionally need type coercion (e.g., `value == null` to check for both `null` and `undefined`).

## The `!!` Operator

`!!` converts any value to its boolean equivalent. The first `!` coerces to boolean and negates; the second `!` negates back.

```javascript
!!'hello';    // true
!!0;          // false
!!null;       // false
!!undefined;  // false
!!NaN;        // false
!!'';         // false
!!{};         // true
!![];         // true
```

In React, `!!` prevents accidental rendering of falsy values like `0` or `''`:

```jsx
{!!list.length && <ItemList items={list} />}
```

Without `!!`, a `list.length` of `0` would render the literal `0` in the DOM instead of rendering nothing.

## 3.8 Modern JavaScript Features

## Modern JavaScript Features (ES2020+)

### 1. Optional Chaining (`?.`)

Short-circuits when the left-hand side is `null` or `undefined`, returning `undefined` instead of throwing.

#### Syntax

```javascript
obj?.prop
obj?.[expr]
func?.(args)
```

#### Use Cases

**Objects:**
```javascript
const user = { address: { city: 'NYC' } };
user?.address?.city;        // 'NYC'
user?.profile?.avatar;     // undefined (no error)
```

**Methods:**
```javascript
const obj = { greet: () => 'hi' };
obj.greet?.();             // 'hi'
obj.missing?.();           // undefined
```

**Arrays:**
```javascript
const arr = [1, 2, 3];
arr?.[0];                  // 1
arr?.[10];                 // undefined
```

**Nested optional access:**
```javascript
const data = { items: [{ name: 'a' }] };
data?.items?.[0]?.name;    // 'a'
```

---

### 2. Nullish Coalescing (`??`)

Returns the right-hand side only when the left-hand side is `null` or `undefined`. Unlike `||`, it does **not** treat `0`, `''`, or `false` as falsy.

| Left Value | `a \|\| b` | `a ?? b` |
|------------|------------|----------|
| `null`     | `b`        | `b`      |
| `undefined`| `b`        | `b`      |
| `0`        | `b`        | `0`      |
| `''`       | `b`        | `''`     |
| `false`    | `b`        | `false`  |
| `NaN`      | `b`        | `NaN`    |

**When to use each:**
- `??` — default values where `0`, `''`, or `false` are valid
- `||` — default when any falsy value should trigger fallback

```javascript
const count = 0;
count || 10;   // 10
count ?? 10;   // 0

const name = '';
name || 'Anonymous';   // 'Anonymous'
name ?? 'Anonymous';   // ''
```

---

### 3. Destructuring

#### Object Destructuring

```javascript
const { a, b } = obj;
const { a: alias, b = 10 } = obj;   // rename + default
const { a, ...rest } = obj;         // rest pattern
```

#### Array Destructuring

```javascript
const [first, second] = arr;
const [a, , c] = arr;               // skip element
const [x, ...tail] = arr;           // rest
const [a = 0, b = 0] = arr;        // defaults
```

#### Nested Destructuring

```javascript
const { user: { name, address: { city } } } = data;
const [[a, b], [c, d]] = nested;
```

#### Renaming

```javascript
const { name: userName, id: userId } = user;
```

#### Rest Pattern

```javascript
const { a, b, ...others } = obj;   // others = remaining props
const [head, ...rest] = arr;       // rest = remaining elements
```

---

### 4. Template Literals

#### Basic Interpolation

```javascript
const name = 'World';
`Hello, ${name}!`;
`2 + 2 = ${2 + 2}`;
```

#### Tagged Templates

The tag function receives an array of string segments and the interpolated values. Useful for sanitization, i18n, or DSLs.

```javascript
function tag(strings, ...values) {
  return strings.reduce((acc, str, i) => acc + str + (values[i] ?? ''), '');
}
tag`Hello ${'World'}!`;  // 'Hello World!'
```

**Signature:** `tag(strings: TemplateStringsArray, ...values: any[])`

---

### 5. Promise Combinators

| Method | Resolves when | Rejects when | Return type |
|--------|---------------|--------------|-------------|
| `Promise.all` | All fulfill | Any rejects | `[results]` or first rejection |
| `Promise.allSettled` | All settle (fulfill or reject) | Never | `[{status, value?}, {status, reason?}]` |
| `Promise.any` | Any fulfills | All reject | First fulfilled value or `AggregateError` |
| `Promise.race` | First settles (either way) | First rejects | First result or first rejection |

#### Behavior on Rejection

```javascript
// Promise.all — short-circuits on first rejection
Promise.all([p1, p2, p3]).catch(e => e);  // rejects with p1's error if p1 rejects

// Promise.allSettled — never rejects
Promise.allSettled([p1, p2, p3]).then(results => {
  // results: [{status:'fulfilled', value}, {status:'rejected', reason}, ...]
});

// Promise.any — rejects only if all reject (AggregateError)
Promise.any([p1, p2, p3]).then(v => v);   // first fulfilled value

// Promise.race — first to settle wins (fulfill or reject)
Promise.race([p1, p2, p3]);              // first result or first error
```

---

### 6. Newer APIs

#### `globalThis`

Cross-environment reference to the global object (browser `window`, Node `global`, workers `self`).

```javascript
globalThis.setTimeout === window.setTimeout;  // true in browser
```

#### `Array.at(index)`

Access by index; negative indices count from the end.

```javascript
const arr = [1, 2, 3];
arr.at(0);   // 1
arr.at(-1);  // 3
arr.at(-2);  // 2
```

#### `Object.hasOwn(obj, prop)`

Replaces `obj.hasOwnProperty(prop)`; avoids prototype lookup issues.

```javascript
const o = { a: 1 };
Object.hasOwn(o, 'a');       // true
Object.hasOwn(o, 'toString'); // false
```

#### `structuredClone(value)`

Deep clone of serializable values (no functions, symbols, or circular refs without special handling).

```javascript
const original = { a: 1, nested: { b: 2 } };
const copy = structuredClone(original);
copy.nested.b = 3;
original.nested.b;  // 2
```

---

### 7. Modules

#### CommonJS vs ES Modules

| Aspect | CommonJS | ES Modules |
|--------|----------|------------|
| Syntax | `require()`, `module.exports` | `import`, `export` |
| Loading | Synchronous | Asynchronous (static analysis) |
| Top-level `await` | No | Yes |
| Tree-shaking | Limited | Supported |
| `this` at top level | `exports` | `undefined` |

#### CommonJS

```javascript
const { foo } = require('./module');
module.exports = { bar };
```

#### ES Modules

```javascript
import { foo } from './module.js';
import * as ns from './module.js';
export { bar };
export default baz;
```

#### Dynamic `import()`

Returns a Promise; use for code-splitting or conditional loading.

```javascript
const load = async () => {
  const { default: Component } = await import('./Component.js');
  return Component;
};
```

**Key differences:** `import` is static (parsed at compile time); `import()` is dynamic and returns a Promise.

# 4. Advanced Javascript


## 4.1 Object, Function, and Prototype

## What is the JavaScript Prototype Chain? How is it Formed?
Javascript is sometimes referred to as a "prototype-based language" because it relies heavily on prototypal inheritance. The prototype chain is a mechanism that allows objects to inherit properties and methods from other objects. 

When a property or method is accessed on an object, JavaScript will first look for it on the object itself. If it's not found, it will look up the prototype chain to find the property or method on the object's prototype. This process continues up the chain until the property or method is found or until the end of the chain is reached.

The top of the prototype chain is the `Object.prototype` object, which includes common methods and properties like `toString` and `valueOf`. All objects in JavaScript inherit from `Object.prototype`, either directly or indirectly through the prototype chain. That's why you can call methods like `toString` on any object in JavaScript.

### Distinction Between Functions and Objects
JavaScript treats functions as first-class objects, meaning that every function in JavaScript is actually a special type of object. There are two key properties involved in the prototype chain mechanism: `prototype` and `__proto__`.

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

### Implementing a `bind` Function

The `bind` function in JavaScript is essential for setting the `this` context of a function explicitly. It ensures predictable function execution by setting `this` to a specific object, regardless of how the function is called.

#### Application of `bind`:

- **Returns a New Function**: Unlike `call` and `apply`, which execute the function immediately, `bind` returns a new function. When called, this new function has its `this` context and any initial arguments pre-set.
- **Binds `this` and Partial Arguments**: `bind` allows for the binding of the `this` context to an object and permits partial application of arguments, enabling some function arguments to be pre-filled and the rest supplied upon calling the bound function.
- **Arrow Function Limitation**: Arrow functions do not have their own `this` context but inherit it from the surrounding lexical context. Thus, using `bind` to change the `this` context of an arrow function is ineffective. However, `bind` can still be used to pre-fill parameters.
- **Use as a Constructor**: If a bound function is used as a constructor with the `new` keyword, `this` within the function body points to the new object being created. This is despite any explicit binding set by `bind`.
- **Normal Function Call**: In a regular function call scenario, `this` refers to the object that was bound using `bind`, which ensures a consistent context in callbacks and event handlers.

#### Implementation Strategy:

Implementing `bind` involves creating a new function that, upon invocation, calls the original function with a predetermined `this` context and a combination of pre-bound and newly provided arguments.

**Example:**
```typescript
function fn(a, b) {
    console.log(this, a, b);
}

const obj = { name: 'ronron' };
const boundFn = fn.bind(obj, 1); // Binds 'obj' as 'this' and '1' as the first argument
boundFn(2); // Output: { name: 'ronron' } 1 2
```

**Custom `bind` Implementation:**

```typescript
Function.prototype.myBind = function (context, ...preBoundArgs) {
    const originalFunction = this; // Capture the original function
    return function(...newArgs) {
        // Combine pre-bound arguments with new ones
        return originalFunction.apply(context, preBoundArgs.concat(newArgs));
    };
};
```

### Implementing `call` and `apply` Functions

`call` and `apply` are indispensable for immediate function invocation with an explicitly specified `this` context and arguments.

#### Binding `this`

- `bind`, `call`, and `apply` are all crucial for setting a function's `this` context in JavaScript.
- In contrast to `bind`, which returns a new function, `call` and `apply` invoke the function right away with a specified `this` context.
- The primary difference between `call` and `apply` lies in their handling of function arguments: `call` accepts an enumerated list of arguments, while `apply` expects an array of arguments.

#### Custom Implementation of `call` and `apply`

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

`class` in JavaScript is essentially syntactic sugar over the existing prototype-based inheritance and does not introduce a new object-oriented inheritance model. At its core, a class is just a special type of function, and thus `typeof ClassName === 'function'`.

## Hidden Classes

In JavaScript, **hidden classes** are an optimization mechanism primarily used to enhance the performance of property access in objects. They are an internal feature of the V8 engine (used by Chrome and Node.js) that helps speed up how properties are accessed by dynamically managing the structure of objects.

### How Hidden Classes Work

1. **Object Creation**: When you create an object, the JavaScript engine assigns a hidden class to that object, which contains layout information about its properties.

2. **Adding Properties**: When you add properties to an object, if these properties are added in a consistent order and manner, the JavaScript engine can reuse the existing hidden class or create a new one that reflects the object's structure.

3. **Optimized Access**: By using hidden classes, the JavaScript engine can quickly locate an object's properties without having to search through the entire object, making property access more efficient.

### Example

Consider the following code:

```javascript
function createPoint(x, y) {
    return { x: x, y: y };
}

const p1 = createPoint(1, 2);
const p2 = createPoint(3, 4);
```

In this example, both `p1` and `p2` will have the same hidden class because they have the same structure.

### Benefits of Hidden Classes

- **Shared Structure**: If multiple objects have the same properties and structure, they can share the same hidden class, improving performance.
- **Avoiding Dynamic Modifications**: Frequently adding or removing properties can lead to changes in hidden classes, which can degrade performance. Therefore, it’s best to determine an object’s structure as much as possible at creation time.

### Summary

Hidden classes are an internal mechanism used by JavaScript engines to optimize property access in objects. By designing object structures thoughtfully, you can leverage this mechanism to enhance the execution efficiency of your code.

## Why Define Class Functions in Constructor Prototype?

In JavaScript, using the prototype property of constructor functions to define methods offers substantial benefits in terms of efficiency, inheritance, and code manageability. This section delves into these advantages, supported by a structured, example-driven approach.

### Memory Efficiency
**Utilizing Prototypes**: Implementing methods on the prototype allows these methods to be shared among all instances of the constructor, rather than being duplicated within each instance. This approach significantly conserves memory, which is particularly advantageous in applications generating large numbers of instances, thereby enhancing overall performance.

### Inheritance Support
**Enabling Polymorphism**: Methods defined on the prototype facilitate inheritance across instances and derived classes. This capability is crucial for implementing polymorphic behaviors where methods can be overridden or extended in subclasses, enhancing code reusability and flexibility.

### Dynamic Updates
**Streamlining Code Maintenance**: Adding methods to the prototype ensures that they are instantly available to all existing instances. This feature allows for flexible and swift modifications to the behavior of applications without the need to recreate objects, simplifying ongoing maintenance.

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

## Data Attribute

### Data Property

- **[[configurable]]**: Indicates whether the property can be deleted or modified. If `false`, the property cannot be deleted or changed (except for its value if `writable` is `true`).
- **[[enumerable]]**: Indicates whether the property shows up in a `for...in` loop and `Object.keys` method.
- **[[writable]]**: Indicates whether the value of the property can be changed.
- **[[value]]**: The actual value of the property.

To change the attributes of a data property, you can use `Object.defineProperty` or `Object.defineProperties`.

**Example:**
```javascript
let obj = {};
Object.defineProperty(obj, 'name', {
  value: 'John',
  writable: false,
  configurable: true,
  enumerable: true
});
```

### Accessor Property

- **[[get]]**: A function that is called when the property is accessed. The function should return the value of the property.
- **[[set]]**: A function that is called when the property is assigned a value. The function receives the new value as an argument.
- **[[configurable]]**: Indicates whether the property can be deleted or modified.
- **[[enumerable]]**: Indicates whether the property shows up in a `for...in` loop and `Object.keys` method.

To change the attributes of an accessor property, you can use `Object.defineProperty` or `Object.defineProperties`.

**Example:**
```javascript
let obj = {
  _name: 'John'
};
Object.defineProperty(obj, 'name', {
  get() {
    return this._name;
  },
  set(value) {
    this._name = value;
  },
  configurable: true,
  enumerable: true
});
```

### GetOwnPropertyDescriptor

`Object.getOwnPropertyDescriptor(obj, prop)` returns the descriptor of the specified property of the object, containing details about the property such as its value, and its attributes like `configurable`, `enumerable`, `writable`, `get`, and `set`.

**Example:**
```javascript
let obj = {
  _name: 'John'
};

// Define a data property
Object.defineProperty(obj, 'name', {
  value: 'John',
  writable: false,
  configurable: true,
  enumerable: true
});

// Get the property descriptor
let descriptor = Object.getOwnPropertyDescriptor(obj, 'name');
// {
//   value: 'John',
//   writable: false,
//   configurable: true,
//   enumerable: true
// }
```

This method is useful for inspecting the attributes of a property to understand its configuration and behavior.

## 4.2 Scope & Closure

#### What is Scope in JavaScript?
Scope in JavaScript is a fundamental concept that determines the accessibility of variables, functions, and objects at various levels throughout your code. 

##### Types of Scope in JavaScript
JavaScript implements several layers of scope, each defining a distinct level of variable accessibility from the most general to the most specific: global, local (function), block, and module.

##### Global Scope
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

##### Local Scope (Function Scope)
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

##### Block Scope
Introduced with ES6, `let` and `const` provide block-level scope, which restricts variable access to the specific block where they are declared, such as within `if` statements or loops.

**Example of Block Scope**:
```javascript
if (true) {
    let blockScopedVariable = 'I am block scoped';
    console.log(blockScopedVariable); // Output: I am block scoped
}
console.log(blockScopedVariable); // Error: blockScopedVariable is not defined
```

##### Lexical Scope
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

##### Module Scope
With ES6 modules, scope is limited to the module itself, helping avoid global namespace pollution and fostering better modularity.

##### Scope Linking in JavaScript
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

#### What is Closure

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

##### Practical Applications of Closures

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

##### Memory Management and Closures

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


## 4.3 Asynchronous JavaScript

## Callback Functions

A callback is a function passed as an argument to another function, to be invoked when an asynchronous operation completes. Callbacks are the oldest pattern for handling asynchronous code in JavaScript.

```javascript
function fetchData(url, callback) {
  const xhr = new XMLHttpRequest();
  xhr.open('GET', url);
  xhr.onload = () => callback(null, xhr.responseText);
  xhr.onerror = () => callback(new Error('Request failed'));
  xhr.send();
}
```

**Callback Hell** arises when multiple asynchronous operations depend on each other, leading to deeply nested and hard-to-read code:

```javascript
getUser(userId, (user) => {
  getOrders(user.id, (orders) => {
    getOrderDetails(orders[0].id, (details) => {
      // deeply nested...
    });
  });
});
```

This nesting problem motivated the introduction of Promises.

## Promises

A **Promise** represents the eventual completion or failure of an asynchronous operation. It provides a cleaner alternative to callbacks by allowing chaining.

### States of a Promise

- **Pending**: Initial state; outcome not yet determined.
- **Fulfilled**: The operation completed successfully.
- **Rejected**: The operation failed.

A promise can only transition from pending to fulfilled or rejected, never backwards.

### Creating and Using Promises

```javascript
const promise = new Promise((resolve, reject) => {
  setTimeout(() => {
    resolve('Success!');
  }, 1000);
});

promise.then(value => {
  console.log(value); // 'Success!'
});
```

### Prototype Methods

- **`.then(onFulfilled, onRejected)`**: Registers callbacks for fulfillment and rejection. Returns a new promise, enabling chaining.
- **`.catch(onRejected)`**: Shorthand for `.then(undefined, onRejected)`. Catches any error thrown in the preceding chain.
- **`.finally(onSettled)`**: Runs after the promise settles regardless of outcome, useful for cleanup.

```javascript
fetchData('/api/users')
  .then(data => JSON.parse(data))
  .then(users => console.log(users))
  .catch(err => console.error(err))
  .finally(() => console.log('Done'));
```

### Static Methods

- **`Promise.all(iterable)`**: Resolves when all promises resolve; rejects if any one rejects.
- **`Promise.allSettled(iterable)`**: Waits for all promises to settle (fulfilled or rejected) and returns their outcomes.
- **`Promise.race(iterable)`**: Settles as soon as the first promise settles.
- **`Promise.any(iterable)`**: Resolves as soon as the first promise fulfills; rejects only if all reject (with an `AggregateError`).
- **`Promise.resolve(value)`** / **`Promise.reject(reason)`**: Create immediately settled promises.

```javascript
const p1 = fetch('/api/users');
const p2 = fetch('/api/posts');
const p3 = fetch('/api/comments');

Promise.all([p1, p2, p3]).then(([users, posts, comments]) => {
  // all three responses available
});
```

## Async / Await

`async` / `await` is syntactic sugar over Promises, making asynchronous code read like synchronous code.

- An `async` function always returns a Promise.
- `await` pauses execution inside an `async` function until the Promise resolves.

```javascript
async function loadUser(userId) {
  try {
    const user = await getUser(userId);
    const orders = await getOrders(user.id);
    const details = await getOrderDetails(orders[0].id);
    return details;
  } catch (err) {
    console.error('Failed:', err);
  }
}
```

### Parallel Execution with Async/Await

A common mistake is using `await` sequentially when the operations are independent:

```javascript
// Sequential (slow)
const users = await fetch('/api/users');
const posts = await fetch('/api/posts');

// Parallel (fast) -- start both, then await
const [users, posts] = await Promise.all([
  fetch('/api/users'),
  fetch('/api/posts')
]);
```

### `for await...of`

Iterates over async iterables, waiting for each Promise to resolve before proceeding. Useful for processing streams or ordered sequences of async data.

```javascript
async function processPromises() {
  const p1 = fetch('/api/1');
  const p2 = fetch('/api/2');
  const p3 = fetch('/api/3');

  for await (const response of [p1, p2, p3]) {
    const data = await response.json();
    console.log(data);
  }
}
```

Note that `for await...of` still starts all promises concurrently (if they were created before the loop). It only ensures the results are processed in order.

## Promise Execution Order and Microtasks

The event loop processes microtasks (Promise callbacks) before the next macrotask. When multiple promise chains exist, their `.then()` callbacks interleave in the microtask queue.

### Interleaved Execution

```javascript
Promise.resolve().then(() => {
  console.log(0);
}).then(() => {
  console.log(1);
});

Promise.resolve().then(() => {
  console.log(2);
}).then(() => {
  console.log(3);
});
// Output: 0 2 1 3
```

Each `.then()` schedules its callback as a microtask. After the first `.then()` of chain 1 runs (logs `0`), its next `.then()` is queued. But chain 2's first `.then()` (logs `2`) was already queued, so it runs next.

### Returning a Promise from `.then()` Adds Extra Microtask Ticks

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
});
// Output: 0 1 2 3 4
```

When `.then()` returns a Promise (not a plain value), the resolution requires additional microtask ticks before the next `.then()` in that chain can run.

## Currying

Currying transforms a function with multiple arguments into a sequence of functions that each take a single argument.

```javascript
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    }
    return function (...nextArgs) {
      return curried.apply(this, args.concat(nextArgs));
    };
  };
}

function sum(a, b, c) { return a + b + c; }

const curriedSum = curry(sum);
curriedSum(1)(2)(3);    // 6
curriedSum(1, 2)(3);    // 6
curriedSum(1)(2, 3);    // 6
```

Benefits include parameter reuse, partial application, and function composition -- all central to functional programming patterns.

## Implementing a Task Queue: `LazyMan`

A common interview problem that tests understanding of asynchronous task scheduling. The challenge is to build a chainable API that queues actions and executes them in order, with support for delayed execution.

```javascript
class LazyMan {
  constructor(name) {
    this.name = name;
    this.taskList = [];
    setTimeout(() => this.next(), 0);
  }

  eat(food) {
    this.taskList.push(() => {
      console.log(`eat ${food}`);
      this.next();
    });
    return this;
  }

  sleep(time) {
    this.taskList.push(() => {
      setTimeout(() => {
        console.log(`wake up after ${time}ms`);
        this.next();
      }, time);
    });
    return this;
  }

  next() {
    const fn = this.taskList.shift();
    fn && fn();
  }
}

const me = new LazyMan('ronron');
me.eat('apple').sleep(1000).eat('banana');
// eat apple → (1s delay) → wake up after 1000ms → eat banana
```

Key concepts demonstrated:
- **Method chaining** by returning `this` from each method.
- **Deferred execution**: The `setTimeout(0)` in the constructor delays `next()` until all synchronous chaining completes, so the full task list is built before execution begins.
- **Sequential async flow**: Each task calls `next()` only after it completes, creating an ordered pipeline.

## Arrow Functions: Limitations

Arrow functions provide concise syntax and lexically bind `this`, but cannot be used in every situation:

1. **No own `this`**: Arrow functions inherit `this` from their enclosing scope. They are unsuitable for object methods or event handlers where `this` should refer to the target.
   ```javascript
   const obj = {
     name: 'Alice',
     greet: () => console.log(this.name) // `this` is NOT obj
   };
   ```

2. **No `arguments` object**: Use rest parameters (`...args`) instead.

3. **Cannot be used as constructors**: Calling with `new` throws a `TypeError`.

4. **Not suitable for prototype methods**: The shared `this` won't refer to the instance.
   ```javascript
   function Person(name) { this.name = name; }
   Person.prototype.greet = () => console.log(this.name); // broken
   ```

## Understanding `['1', '2', '3'].map(parseInt)`

This classic interview question tests knowledge of how `map` passes arguments to its callback.

`Array.prototype.map` calls the callback with three arguments: `(element, index, array)`. Since `parseInt(string, radix)` accepts a second parameter for the radix:

```javascript
['1', '2', '3'].map(parseInt);
// Equivalent to:
// parseInt('1', 0)  → 1    (radix 0 defaults to base 10)
// parseInt('2', 1)  → NaN  (radix 1 is invalid)
// parseInt('3', 2)  → NaN  ('3' is not a valid binary digit)
// Result: [1, NaN, NaN]
```

To get the expected `[1, 2, 3]`, explicitly wrap the callback:
```javascript
['1', '2', '3'].map(s => parseInt(s, 10)); // [1, 2, 3]
// or simply:
['1', '2', '3'].map(Number); // [1, 2, 3]
```

## 4.4 Iterators and Generators

## Iterable and Iterator Protocol

### Iterable Protocol

An object is **iterable** if it implements the `[Symbol.iterator]` method, which returns an **iterator**. This protocol enables objects to work with `for...of` loops, spread syntax (`...`), destructuring, and `Array.from()`.

Built-in iterables include: Arrays, Strings, Maps, Sets, TypedArrays, the `arguments` object, and NodeLists.

### Iterator Protocol

An **iterator** is any object with a `next()` method that returns an object with:
- `value`: The next value in the sequence.
- `done`: A boolean indicating whether the sequence is complete.

```javascript
const arr = [10, 20, 30];
const iterator = arr[Symbol.iterator]();

iterator.next(); // { value: 10, done: false }
iterator.next(); // { value: 20, done: false }
iterator.next(); // { value: 30, done: false }
iterator.next(); // { value: undefined, done: true }
```

### Custom Iterable

To make any object work with `for...of`, define a `[Symbol.iterator]` method:

```javascript
class Range {
  constructor(start, end) {
    this.start = start;
    this.end = end;
  }

  [Symbol.iterator]() {
    let current = this.start;
    const end = this.end;
    return {
      next() {
        if (current <= end) {
          return { value: current++, done: false };
        }
        return { value: undefined, done: true };
      }
    };
  }
}

for (const num of new Range(1, 5)) {
  console.log(num); // 1, 2, 3, 4, 5
}

console.log([...new Range(3, 6)]); // [3, 4, 5, 6]
```

## Generators

Generators are functions that can pause and resume execution using the `yield` keyword. They automatically implement both the iterable and iterator protocols.

### Declaration and Basic Usage

A generator is declared with `function*` and returns a generator object when called. The function body does not execute until `next()` is called.

```javascript
function* countdown(n) {
  while (n > 0) {
    yield n;
    n--;
  }
}

const gen = countdown(3);
gen.next(); // { value: 3, done: false }
gen.next(); // { value: 2, done: false }
gen.next(); // { value: 1, done: false }
gen.next(); // { value: undefined, done: true }

// Works with for...of since generators are iterable
for (const val of countdown(3)) {
  console.log(val); // 3, 2, 1
}
```

### Passing Values into Generators

The argument to `next(value)` becomes the result of the `yield` expression inside the generator:

```javascript
function* conversation() {
  const name = yield 'What is your name?';
  const hobby = yield `Hello, ${name}! What is your hobby?`;
  return `${name} likes ${hobby}`;
}

const chat = conversation();
console.log(chat.next().value);          // 'What is your name?'
console.log(chat.next('Alice').value);   // 'Hello, Alice! What is your hobby?'
console.log(chat.next('coding').value);  // 'Alice likes coding'
```

### `yield*` -- Delegating to Another Iterable

`yield*` delegates iteration to another iterable or generator, flattening nested sequences:

```javascript
function* flatten(arr) {
  for (const item of arr) {
    if (Array.isArray(item)) {
      yield* flatten(item);
    } else {
      yield item;
    }
  }
}

console.log([...flatten([1, [2, [3, 4]], 5])]); // [1, 2, 3, 4, 5]
```

### Practical Use Cases

#### Lazy Evaluation

Generators produce values on demand, making them memory-efficient for large or infinite sequences:

```javascript
function* fibonacci() {
  let a = 0, b = 1;
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}

const fib = fibonacci();
fib.next().value; // 0
fib.next().value; // 1
fib.next().value; // 1
fib.next().value; // 2
fib.next().value; // 3
```

#### Unique ID Generator

```javascript
function* idGenerator(prefix = 'id') {
  let id = 0;
  while (true) {
    yield `${prefix}_${id++}`;
  }
}

const gen = idGenerator('user');
gen.next().value; // 'user_0'
gen.next().value; // 'user_1'
```

#### Async Flow Control (Historical)

Before `async/await`, generators combined with promise runners (like `co`) were used to write async code that looked synchronous. This is the historical predecessor to `async/await`:

```javascript
function* fetchUser(id) {
  const response = yield fetch(`/api/users/${id}`);
  const user = yield response.json();
  return user;
}

// A runner would call .next() with each resolved value
// Today, async/await has replaced this pattern entirely
```

### Generators vs Iterators

| Feature | Custom Iterator | Generator |
|---------|----------------|-----------|
| Syntax | Manual `next()` method | `function*` with `yield` |
| State management | Manual (closure variables) | Automatic (execution context preserved) |
| Code complexity | Higher for complex sequences | Simpler and more readable |
| Bidirectional data | Not built-in | `next(value)` passes data in |
| Early termination | Manual `return()` method | Built-in `return()` and `throw()` |

Generators are the preferred choice for most iteration scenarios due to their simpler syntax and automatic state management. Custom iterators are useful when you need fine-grained control or when implementing data structures.

## 4.5 Error Handling

## 4.5 Error Handling

### try/catch/finally

```javascript
try {
  riskyOperation();
} catch (error) {
  console.error(error.message);
} finally {
  cleanup(); // Always runs, even after return or throw
}
```

- **finally** executes regardless of whether the try block completes, throws, or returns. It runs before the error propagates or the return value is delivered.
- **Rethrowing**: Use `throw error` (not `throw`) to preserve the original stack trace.
- **Nested try/catch**: Inner catch can rethrow to outer; outer catch receives the error if inner doesn't handle it.

```javascript
try {
  try {
    throw new Error('inner');
  } catch (e) {
    console.log('inner caught');
    throw e; // Rethrow to outer
  }
} catch (e) {
  console.log('outer caught:', e.message);
}
```

---

### Custom Error Classes

Extend `Error` and call `super()` so `instanceof Error` and stack traces work correctly.

```javascript
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

// Usage
throw new ValidationError('Invalid email', 'email');

// instanceof checking
try {
  validate(input);
} catch (e) {
  if (e instanceof ValidationError) {
    showFieldError(e.field, e.message);
  } else {
    throw e;
  }
}
```

**Note**: `Object.setPrototypeOf(this, ValidationError.prototype)` fixes `instanceof` in some transpiled/bundled environments where the prototype chain can break.

---

### Promise Rejection Handling

#### .catch() chaining

```javascript
fetch('/api/data')
  .then(res => res.json())
  .catch(err => console.error('Fetch failed:', err))
  .then(data => process(data)); // Runs with undefined if catch ran
```

- A `.catch()` returns a resolved promise unless it rethrows.
- Chained `.then()` after `.catch()` receives the catch return value (or `undefined` if catch doesn't return).

#### async/await with try/catch

```javascript
async function loadData() {
  try {
    const res = await fetch('/api/data');
    const data = await res.json();
    return data;
  } catch (error) {
    console.error(error);
    throw error; // Reject the returned promise
  }
}
```

#### Unhandled rejection pitfalls

- Rejections not caught by `.catch()` or try/catch become **unhandled promise rejections**.
- In Node.js and browsers, these can trigger `unhandledrejection` and may cause process exit or console warnings.
- Always attach `.catch()` to promise chains or wrap async calls in try/catch.

```javascript
// BAD: unhandled rejection if fetch fails
async function bad() {
  const res = await fetch('/api'); // No try/catch
  return res.json();
}

// GOOD
async function good() {
  try {
    const res = await fetch('/api');
    return res.json();
  } catch (e) {
    handleError(e);
  }
}
```

---

### Global Error Handlers

#### window.onerror

```javascript
window.onerror = function(message, source, lineno, colno, error) {
  console.log(message, source, lineno, colno, error?.stack);
  return true; // Suppress default browser error UI
};
```

- **Parameters**: `message`, `source` (URL), `lineno`, `colno`, `error` (Error object, may be undefined).
- **Limitation**: Cross-origin scripts often yield `"Script error."` with no stack trace due to CORS. Use `Cross-Origin-Resource-Policy` or serve scripts same-origin for full details.

#### window.addEventListener('unhandledrejection')

Catches promise rejections that are never handled.

```javascript
window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled rejection:', event.reason);
  event.preventDefault(); // Prevent default console error
});
```

- `event.reason` is the rejection value (often an Error).
- `event.promise` is the rejected promise.

#### window.addEventListener('error')

Catches resource loading errors (images, scripts, stylesheets) that `onerror` does not.

```javascript
window.addEventListener('error', event => {
  if (event.target !== window) {
    console.error('Resource failed:', event.target.src || event.target.href);
  }
}, true); // Use capture phase
```

- Use `event.target !== window` to distinguish resource errors from script errors.
- Must use capture phase (`true`) for some resource errors.

---

### React Error Boundaries

Error boundaries catch JavaScript errors in the component tree and render a fallback UI. They are **class components only** — there is no hook equivalent.

```jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}
```

- **getDerivedStateFromError**: Sync, used to update state for fallback UI.
- **componentDidCatch**: For side effects (logging, reporting).
- Error boundaries do **not** catch: event handler errors, async code, SSR errors, or errors inside the boundary itself.
- For function components, use a library such as **react-error-boundary**:

```jsx
import { ErrorBoundary } from 'react-error-boundary';

<ErrorBoundary fallback={<div>Error!</div>} onError={logError}>
  <MyComponent />
</ErrorBoundary>
```

# 5. DOM & Browser APIs


## 5.1 DOM Manipulation and Events

## Deep Copy

### Why Not `JSON.stringify` + `JSON.parse`?

`JSON.parse(JSON.stringify(obj))` is a quick deep copy method but fails for:
- **Map and Set**: Converted to plain objects/arrays, losing their behavior.
- **Circular references**: `JSON.stringify` throws on cyclic structures.
- **Special objects**: Functions, `undefined`, `Date`, `RegExp`, and `Symbol` values are lost or incorrectly serialized.

### Implementing Deep Copy

A robust deep copy must handle all reference types and circular references using a `WeakMap` to track already-copied objects:

```typescript
function deepCopy(obj: any, map = new WeakMap()): any {
  if (obj === null || typeof obj !== 'object') return obj;
  if (map.has(obj)) return map.get(obj);

  let copy: any;

  if (obj instanceof Date) {
    copy = new Date(obj.getTime());
  } else if (obj instanceof RegExp) {
    copy = new RegExp(obj.source, obj.flags);
  } else if (obj instanceof Map) {
    copy = new Map();
    map.set(obj, copy);
    obj.forEach((value, key) => copy.set(key, deepCopy(value, map)));
  } else if (obj instanceof Set) {
    copy = new Set();
    map.set(obj, copy);
    obj.forEach(value => copy.add(deepCopy(value, map)));
  } else {
    copy = Array.isArray(obj) ? [] : {};
    map.set(obj, copy);
    Object.keys(obj).forEach(key => {
      copy[key] = deepCopy(obj[key], map);
    });
  }

  return copy;
}
```

`Date` and `RegExp` need special treatment because their internal state (timestamp, pattern/flags) is not stored as enumerable properties -- iterating over keys would produce an empty copy.

## Event Propagation

Events in the DOM propagate through three phases:

### 1. Capture Phase
The event travels from the document root down to the target element, passing through each ancestor. Useful for intercepting events before they reach their target.

### 2. Target Phase
The event reaches the element that triggered it. Listeners attached directly to the target execute here.

### 3. Bubble Phase
The event travels back up from the target to the document root. This is the default phase for most event listeners and enables **event delegation** -- attaching a single listener to a parent instead of many listeners to individual children.

```javascript
parent.addEventListener('click', (e) => {
  if (e.target.matches('.item')) {
    console.log('Item clicked:', e.target.textContent);
  }
});
```

### React's Synthetic Event System

React wraps native browser events in **SyntheticEvent** objects that behave identically across browsers. Instead of binding to individual DOM nodes, React uses event delegation at the root container. To handle an event during the capture phase, append `Capture` to the handler name (e.g., `onClickCapture`).

## EventBus Implementation

An EventBus decouples components by allowing them to communicate through events rather than direct references.

```typescript
class EventBus {
  private events: Record<string, Function[]> = {};

  on(event: string, listener: Function): void {
    if (!this.events[event]) this.events[event] = [];
    this.events[event].push(listener);
  }

  once(event: string, listener: Function): void {
    const wrapper = (...args: any[]) => {
      listener(...args);
      this.off(event, wrapper);
    };
    this.on(event, wrapper);
  }

  emit(event: string, ...args: any[]): void {
    this.events[event]?.forEach(listener => listener(...args));
  }

  off(event: string, listener: Function): void {
    if (this.events[event]) {
      this.events[event] = this.events[event].filter(l => l !== listener);
    }
  }
}
```

When using `off`, you must pass the same function reference that was passed to `on`. Anonymous functions cannot be unbound.

## Observer vs Publish-Subscribe

Both patterns enable reactive communication, but differ in coupling:

**Observer Pattern**: The subject directly knows its observers and notifies them. Example: DOM event listeners.

```javascript
button.addEventListener('click', handleClick);
```

**Publish-Subscribe Pattern**: A central event channel mediates between publishers and subscribers. Neither side knows about the other. Example: an EventBus.

```javascript
eventBus.on('user:login', updateUI);
eventBus.emit('user:login', { name: 'Alice' });
```

The Publish-Subscribe pattern is more decoupled but harder to debug since the flow is indirect.

## `requestAnimationFrame` vs `requestIdleCallback`

### `requestAnimationFrame`

Schedules a callback before the next repaint (~60fps = every 16ms). Use for visual updates and animations where frame timing matters.

```javascript
function animate() {
  element.style.transform = `translateX(${x++}px)`;
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
```

### `requestIdleCallback`

Schedules a callback during browser idle periods -- after the main thread has finished layout, paint, and input handling. Use for non-urgent work like analytics, prefetching, or background processing.

```javascript
requestIdleCallback((deadline) => {
  while (deadline.timeRemaining() > 0) {
    doBackgroundWork();
  }
});
```

React Fiber uses a similar concept: it splits rendering into small units of work and yields back to the browser between units, allowing high-priority tasks (like input handling) to interrupt rendering.

## Finding the Maximum in an Array

Multiple approaches with different trade-offs:

```javascript
// Spread operator -- clean but may stack overflow on huge arrays
Math.max(...arr);

// apply -- same limitation as spread
Math.max.apply(null, arr);

// reduce -- safe for any array size
arr.reduce((max, cur) => cur > max ? cur : max, arr[0]);
```

For arrays with millions of elements, the `reduce` approach is the safest since `Math.max` with spread/apply pushes all arguments onto the call stack.

## 5.2 Browser Storage and Communication

## Front-End Storage

### LocalStorage

Persistent key-value storage on the client, surviving browser restarts.

- **Capacity**: ~5MB per origin.
- **Lifetime**: Persists until explicitly cleared via script or by the user.
- **Access**: Synchronous, same-origin only. Not sent with HTTP requests.
- **Use cases**: User preferences, themes, cached application data.

### SessionStorage

Identical API to LocalStorage but scoped to a single browser tab.

- **Capacity**: ~5MB per origin.
- **Lifetime**: Cleared when the tab or window is closed.
- **Access**: Synchronous, same-origin, tab-specific.
- **Use cases**: Form state preservation during navigation, temporary SPA state.

### Cookies

Small pieces of data sent to the server with every HTTP request.

- **Capacity**: ~4KB per cookie.
- **Lifetime**: Configurable via `Expires` or `Max-Age`. Session cookies are cleared when the browser closes.
- **Access**: Automatically included in HTTP headers; accessible via `document.cookie`.
- **Security flags**: `HttpOnly` (no JS access), `Secure` (HTTPS only), `SameSite` (CSRF protection).
- **Use cases**: Session IDs, authentication tokens, server-side personalization.

### Choosing the Right Mechanism

| Feature | LocalStorage | SessionStorage | Cookies |
|---------|-------------|---------------|---------|
| Capacity | ~5MB | ~5MB | ~4KB |
| Sent with requests | No | No | Yes |
| Lifetime | Permanent | Tab session | Configurable |
| Server access | No | No | Yes |

Use LocalStorage for long-lived client-only data, SessionStorage for tab-scoped temporary data, and Cookies when the server needs to read the data.

## HTMLCollection vs NodeList

### HTMLCollection

- Returned by `getElementsByClassName`, `getElementsByTagName`, and the `.children` property.
- Contains only `Element` nodes.
- **Always live**: Automatically reflects DOM changes.

### NodeList

- Returned by `querySelectorAll` (static) and `childNodes` (live).
- Can contain any node type: `Element`, `Text`, `Comment`.
- May be live or static depending on how it was obtained.

### `.children` vs `.childNodes`

```html
<p id="p1">
    <em>hello</em> world <b>bold</b><!-- comment -->
</p>
```

- `p.children` → HTMLCollection: `[<em>, <b>]` (elements only)
- `p.childNodes` → NodeList: `[<em>, " world ", <b>, <!-- comment -->]` (all node types)

## Multi-Tab Communication

### 1. `localStorage` + `storage` Event

The simplest approach. When one tab writes to `localStorage`, other same-origin tabs receive a `storage` event.

```javascript
// Tab A: listen
window.addEventListener('storage', (e) => {
  if (e.key === 'message') {
    console.log('Received:', e.newValue);
  }
});

// Tab B: send
localStorage.setItem('message', JSON.stringify({ text: 'hello', ts: Date.now() }));
```

### 2. BroadcastChannel API

A cleaner API designed specifically for same-origin inter-tab messaging.

```javascript
const channel = new BroadcastChannel('app_channel');

// Tab A: listen
channel.onmessage = (e) => console.log('Received:', e.data);

// Tab B: send
channel.postMessage({ type: 'update', payload: { id: 1 } });
```

### 3. SharedWorker

A Web Worker shared across tabs from the same origin, capable of maintaining state and routing messages.

```javascript
// worker.js
const ports = new Set();
onconnect = (e) => {
  const port = e.ports[0];
  ports.add(port);
  port.onmessage = (msg) => {
    ports.forEach(p => { if (p !== port) p.postMessage(msg.data); });
  };
};
```

### 4. WebSockets

For real-time cross-origin communication routed through a server. All tabs connect to the same WebSocket server, which broadcasts messages. Suitable for chat apps, collaborative tools, and live dashboards.

## Iframe Communication with `postMessage`

`window.postMessage()` enables secure cross-origin communication between a page and its iframes.

```javascript
// Parent → Iframe
const iframe = document.getElementById('myIframe');
iframe.contentWindow.postMessage({ action: 'update' }, 'https://child-origin.com');

// Iframe → Parent
window.parent.postMessage({ status: 'ready' }, 'https://parent-origin.com');

// Receiving (both sides)
window.addEventListener('message', (e) => {
  if (e.origin !== 'https://trusted-origin.com') return;
  console.log('Received:', e.data);
});
```

Always validate `event.origin` to prevent cross-site scripting attacks. Never use `'*'` as the target origin in production.

## JS-Bridge

JSBridge is a communication layer between native mobile apps and JavaScript running inside a WebView. Since web content is sandboxed and cannot directly call native APIs, a bridge provides structured access to device features.

### URL Scheme Method

The native app registers a custom URL scheme. When the WebView navigates to a URL matching that scheme, the app intercepts the request and performs the corresponding native action.

```javascript
const bridge = {
  invoke(path, data, onSuccess, onError) {
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = `myapp://${path}?data=${encodeURIComponent(JSON.stringify(data))}`;
    document.body.appendChild(iframe);
    setTimeout(() => iframe.remove(), 100);
  },
  getLocation(onSuccess, onError) {
    this.invoke('api/location', {}, onSuccess, onError);
  }
};
```

### Global API Injection

The native side injects JavaScript objects into the WebView's global scope, exposing native functions directly.

```javascript
// Native side injects window.NativeBridge
const version = window.NativeBridge.getVersion();
```

The URL scheme approach is preferred for its flexibility and better handling of asynchronous responses.

## 5.3 Image Lazy Loading

## Native Lazy Loading

Modern browsers support the `loading` attribute on `<img>` and `<iframe>` elements:

```html
<img src="image.jpg" alt="Description" loading="lazy">
```

Values:
- `lazy`: Defers loading until the image approaches the viewport.
- `eager`: Loads immediately (default behavior).

This is the simplest approach and requires no JavaScript. Use it as the primary strategy, with JavaScript fallbacks for older browsers.

## JavaScript Fallback with `data-src`

For browsers without native lazy loading support, store the real URL in `data-src` and swap it into `src` when the element enters the viewport.

```html
<img src="placeholder.png" data-src="actual-image.jpg" alt="Description">
```

### Intersection Observer (Recommended)

The Intersection Observer API efficiently detects when elements enter or leave the viewport without the performance cost of scroll event listeners.

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
      observer.unobserve(img);
    }
  });
});

document.querySelectorAll('img[data-src]').forEach(img => {
  observer.observe(img);
});
```

### Scroll Event with Throttle (Legacy)

For environments without Intersection Observer, use scroll events with throttling to limit execution frequency:

```javascript
function throttle(fn, delay) {
  let timer = null;
  return function (...args) {
    if (timer) return;
    timer = setTimeout(() => {
      fn.apply(this, args);
      timer = null;
    }, delay);
  };
}

window.addEventListener('scroll', throttle(() => {
  document.querySelectorAll('img[data-src]').forEach(img => {
    if (img.getBoundingClientRect().top < window.innerHeight) {
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
    }
  });
}, 100));
```

## Performance Considerations

- Load above-the-fold images eagerly (`loading="eager"` or omit the attribute) to avoid layout shift.
- Use appropriately sized placeholder images or set explicit `width` and `height` on `<img>` elements to reserve space and prevent Cumulative Layout Shift (CLS).
- Combine lazy loading with modern image formats (WebP, AVIF) and `srcset` for responsive images.

# 6. TypeScript


## 6.1 Advanced TypeScript

## Utility Types

TypeScript provides built-in utility types for common type transformations.

### Transforming Object Types

**`Partial<T>`** -- Makes all properties optional.
```typescript
interface User { id: number; name: string; email: string; }

function updateUser(user: Partial<User>) { /* ... */ }
updateUser({ name: 'Alice' }); // valid
```

**`Required<T>`** -- Makes all properties required (opposite of Partial).

**`Readonly<T>`** -- Makes all properties read-only.
```typescript
const user: Readonly<User> = { id: 1, name: 'Alice', email: 'a@b.com' };
user.name = 'Bob'; // Error: Cannot assign to 'name'
```

**`Pick<T, Keys>`** -- Selects a subset of properties.
```typescript
type UserPreview = Pick<User, 'id' | 'name'>;
```

**`Omit<T, Keys>`** -- Excludes a subset of properties.
```typescript
type UserWithoutEmail = Omit<User, 'email'>;
```

**`Record<Keys, T>`** -- Creates an object type with specified keys and value type.
```typescript
type Role = 'admin' | 'user' | 'guest';
const permissions: Record<Role, string[]> = {
  admin: ['read', 'write', 'delete'],
  user: ['read', 'write'],
  guest: ['read']
};
```

### Transforming Union Types

**`Exclude<Union, Excluded>`** -- Removes members from a union.
```typescript
type T = Exclude<'a' | 'b' | 'c', 'a'>; // 'b' | 'c'
```

**`Extract<Union, Extracted>`** -- Keeps only matching members.
```typescript
type T = Extract<'a' | 'b' | 'c', 'a' | 'b'>; // 'a' | 'b'
```

**`NonNullable<T>`** -- Removes `null` and `undefined`.
```typescript
type T = NonNullable<string | null | undefined>; // string
```

### Extracting Function and Class Types

**`ReturnType<T>`** -- Extracts the return type of a function.
```typescript
function getUser() { return { id: 1, name: 'Alice' }; }
type User = ReturnType<typeof getUser>; // { id: number; name: string; }
```

**`Parameters<T>`** -- Extracts parameter types as a tuple.
```typescript
type P = Parameters<typeof getUser>; // []
```

**`InstanceType<T>`** -- Extracts the instance type from a class constructor.

**`ConstructorParameters<T>`** -- Extracts constructor parameter types as a tuple.

## Generics

Generics allow writing reusable code that works with multiple types while preserving type safety.

```typescript
function identity<T>(value: T): T {
  return value;
}

identity<string>('hello'); // type is string
identity(42);              // type inferred as number
```

### Generic Constraints

Use `extends` to restrict what types a generic can accept:

```typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: 'Alice', age: 30 };
getProperty(user, 'name');  // string
getProperty(user, 'phone'); // Error: 'phone' is not in keyof typeof user
```

### Generic Interfaces and Classes

```typescript
interface Repository<T> {
  getById(id: string): T;
  getAll(): T[];
  save(item: T): void;
}

class UserRepository implements Repository<User> {
  getById(id: string): User { /* ... */ }
  getAll(): User[] { /* ... */ }
  save(user: User): void { /* ... */ }
}
```

## Proxy

JavaScript `Proxy` wraps an object and intercepts operations like property access, assignment, and enumeration.

```javascript
const handler = {
  get(target, prop) {
    console.log(`Accessing ${prop}`);
    return Reflect.get(target, prop);
  },
  set(target, prop, value) {
    console.log(`Setting ${prop} = ${value}`);
    return Reflect.set(target, prop, value);
  }
};

const data = new Proxy({ count: 0 }, handler);
data.count;     // logs: Accessing count
data.count = 1; // logs: Setting count = 1
```

Use cases include change detection (reactive frameworks like Vue 3), validation, logging, and implementing default values.

### `Object.defineProperty` vs `Proxy`

`Object.defineProperty` defines getters/setters on individual properties (used in Vue 2). `Proxy` intercepts operations on the entire object, supporting dynamic property addition and more trap types. Vue 3 migrated from `defineProperty` to `Proxy` for this reason.

```javascript
Object.defineProperty(window, 'a', {
  get: function () {
    this.value = this.value || 0;
    return ++this.value;
  }
});
// a === 1 && a === 2 && a === 3 is true
```

## Decorators

Decorators attach metadata or modify behavior of classes, methods, or properties at declaration time. They follow the Aspect-Oriented Programming (AOP) pattern.

```typescript
function log(target: any, key: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.log(`Calling ${key} with`, args);
    return original.apply(this, args);
  };
}

class Calculator {
  @log
  add(a: number, b: number) { return a + b; }
}

new Calculator().add(1, 2); // logs: Calling add with [1, 2]
```

Class decorators receive the constructor and can add static properties or wrap the class:

```typescript
function sealed(constructor: Function) {
  Object.seal(constructor);
  Object.seal(constructor.prototype);
}

@sealed
class Greeter { /* ... */ }
```

Decorators are widely used in frameworks like Angular and NestJS for dependency injection, route definitions, and metadata annotation.

# 7. Event Loop & Runtime


## 7.1 Event Loop

## The Event Loop

JavaScript is single-threaded, meaning it can only execute one piece of code at a time. The event loop is the mechanism that enables non-blocking asynchronous execution despite this constraint.

### Execution Model

1. Execute all synchronous code on the **call stack**.
2. When the call stack is empty, drain the **microtask queue** completely.
3. Pick one task from the **macrotask queue**, execute it, then return to step 2.
4. Repeat.

### Microtasks vs Macrotasks

**Macrotasks**: `setTimeout`, `setInterval`, `setImmediate` (Node.js), I/O callbacks, UI rendering callbacks.

**Microtasks**: `Promise.then/catch/finally`, `async/await` continuations, `queueMicrotask()`, `MutationObserver`.

Microtasks always run before the next macrotask. This gives promise callbacks higher priority than timer callbacks.

### Example

```javascript
console.log('Start');

setTimeout(() => console.log('Timeout'), 0);

new Promise((resolve) => {
  console.log('Promise constructor');
  resolve();
}).then(() => console.log('Promise then'));

console.log('End');
```

Output:
```
Start
Promise constructor
End
Promise then
Timeout
```

The Promise constructor runs synchronously. The `.then()` callback is a microtask that runs before the `setTimeout` macrotask.

## Browser vs Node.js Event Loop

### Browser

The browser event loop runs on the main thread alongside DOM rendering. Between macrotasks, the browser may perform rendering steps (style calculation, layout, paint). This is why long-running synchronous code blocks the UI.

The cycle is: **macrotask → all microtasks → render → macrotask → ...**

### Node.js

Node.js organizes macrotasks into phases with different priorities:

1. **Timers**: `setTimeout`, `setInterval` callbacks.
2. **I/O Callbacks**: Network, stream, and TCP error callbacks.
3. **Idle/Prepare**: Internal operations.
4. **Poll**: Retrieves new I/O events.
5. **Check**: `setImmediate` callbacks.
6. **Close Callbacks**: `socket.on('close')` etc.

Between each phase, Node.js drains the microtask queue. `process.nextTick` callbacks have the highest priority among microtasks, executing before Promise callbacks.

```javascript
setTimeout(() => console.log('timeout'), 0);
setImmediate(() => console.log('immediate'));
process.nextTick(() => console.log('nextTick'));
Promise.resolve().then(() => console.log('promise'));
// Output: nextTick → promise → timeout/immediate (order of last two depends on timing)
```

## Garbage Collection

JavaScript engines automatically manage memory through garbage collection.

### Reference Counting

Tracks how many references point to each object. When the count reaches zero, the memory is freed. This method fails with **circular references** where two objects reference each other, keeping both alive indefinitely.

### Mark-and-Sweep (Modern Engines)

Used by V8 (Chrome, Node.js) and SpiderMonkey (Firefox). Starting from root references (global variables, call stack), the GC traverses all reachable objects and marks them. Unmarked objects are unreachable and collected. This solves the circular reference problem.

### Common Memory Leak Sources

- **Uncleared timers**: `setInterval` callbacks that reference closures.
- **Detached DOM nodes**: References to DOM elements that have been removed from the tree.
- **Closures**: Closures that unintentionally capture large scopes.
- **Global variables**: Accidental globals created without `let`/`const`.
- **Event listeners**: Listeners not removed when components unmount.

### Detecting Leaks

Use Chrome DevTools Performance tab to record memory usage over time. A steadily increasing heap without drops after GC cycles indicates a leak. The Memory tab provides heap snapshots for comparing object counts between points in time.

## 7.2 Node.js Fundamentals

## Process vs Thread

- **Process**: The OS's minimum unit for resource allocation. Each process has its own independent memory space.
- **Thread**: The smallest unit of execution within a process. Threads share their parent process's memory. JavaScript runs on a single thread but supports concurrency through the event loop and worker threads.

## Multiprocessing in Node.js

Single-threaded Node.js cannot fully utilize multi-core CPUs by default. Multiprocessing solves this by spawning additional processes.

### `child_process.fork()`

Creates a child process running a separate Node.js module. Parent and child communicate via IPC (Inter-Process Communication) using `send()` and `message` events.

```javascript
// main.js
const { fork } = require('child_process');

const child = fork('./compute.js');
child.send({ task: 'fibonacci', n: 40 });

child.on('message', (result) => {
  console.log('Result:', result);
});

// compute.js
process.on('message', (msg) => {
  if (msg.task === 'fibonacci') {
    const result = fib(msg.n);
    process.send(result);
  }
});
```

Use `fork` to offload CPU-intensive tasks (heavy computation, image processing) so the main process remains responsive.

### `cluster` Module

Creates worker processes that share server ports, enabling load balancing across CPU cores.

```javascript
const cluster = require('cluster');
const http = require('http');
const numCPUs = require('os').cpus().length;

if (cluster.isMaster) {
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
  cluster.on('exit', (worker) => {
    console.log(`Worker ${worker.process.pid} died, restarting...`);
    cluster.fork();
  });
} else {
  http.createServer((req, res) => {
    res.writeHead(200);
    res.end('Hello');
  }).listen(8000);
}
```

### PM2

In production, use PM2 for process management instead of manual clustering:

```bash
pm2 start app.js -i max   # fork one process per CPU core
pm2 list                   # view running processes
pm2 monit                  # real-time monitoring
pm2 reload app             # zero-downtime restart
```

PM2 handles automatic restarts on crashes, log management, and cluster mode with a simpler configuration than manual `cluster` usage.

## Serverless / Cloud Functions

Cloud functions (AWS Lambda, Google Cloud Functions, Vercel Edge Functions) run code without managing servers.

**Advantages over traditional deployment:**
- **Cost efficiency**: Pay only for execution time, not idle servers.
- **Auto-scaling**: Automatically handles traffic spikes.
- **Zero infrastructure management**: No patching, provisioning, or capacity planning.
- **Rapid deployment**: Push code directly without build pipelines for infrastructure.

**Trade-offs:**
- Cold start latency on first invocation.
- Execution time limits (typically 10-60 seconds).
- Stateless -- no persistent in-memory state between invocations.

Serverless is well-suited for API endpoints, webhooks, scheduled tasks, and event-driven processing.

## 7.3 Build Tools

## Webpack

Webpack is a static module bundler that analyzes dependencies and produces optimized bundles for the browser.

### Core Concepts

- **Entry**: The starting point(s) for dependency resolution (e.g., `./src/index.js`).
- **Output**: Where and how to emit the bundled files.
- **Loaders**: Transform non-JavaScript files (CSS, images, TypeScript) into modules Webpack can process.
- **Plugins**: Extend Webpack's capabilities (optimization, asset management, environment injection).
- **Mode**: `development` (fast builds, readable output) or `production` (minification, tree-shaking).

### Build Process

1. **Merge config**: Combine CLI arguments with configuration file settings.
2. **Initialize compiler**: Create the compiler instance, load plugins, call each plugin's `apply` method.
3. **Resolve entries**: Identify entry files and build a dependency graph.
4. **Apply loaders**: Transform source files through the loader chain.
5. **Output bundles**: Combine modules, perform optimizations (minification, code splitting), write output files.

### Loaders

Loaders process files from right to left (last in the `use` array runs first):

```javascript
module: {
  rules: [
    { test: /\.tsx?$/, use: ['babel-loader', 'ts-loader'] },
    { test: /\.css$/,  use: ['style-loader', 'css-loader'] },
    { test: /\.scss$/, use: ['style-loader', 'css-loader', 'sass-loader'] }
  ]
}
```

For `.tsx` files: `ts-loader` compiles TypeScript first, then `babel-loader` transpiles to ES5.

**Common loaders:**
- **JS/TS**: `babel-loader`, `ts-loader`
- **CSS**: `css-loader`, `style-loader`, `postcss-loader`, `sass-loader`
- **Assets**: `file-loader`, `url-loader`, `image-webpack-loader`

#### Writing a Custom Loader

A loader is a function that receives source code and returns transformed code:

```javascript
// loaders/strip-comments-loader.js
module.exports = function (source) {
  return source.replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, '');
};
```

Register it via `resolveLoader.modules` to resolve from a local directory.

### Plugins

Plugins hook into Webpack's compilation lifecycle through the `compiler.hooks` API.

**Common plugins:**
- `HtmlWebpackPlugin`: Generates HTML files with script/style injections.
- `MiniCssExtractPlugin`: Extracts CSS into separate files (replaces `style-loader` in production).
- `DefinePlugin`: Creates compile-time global constants (e.g., `process.env.NODE_ENV`).
- `TerserWebpackPlugin`: Minifies JavaScript output.
- `CleanWebpackPlugin`: Removes old build artifacts before each build.
- `HotModuleReplacementPlugin`: Enables HMR during development.

#### Writing a Custom Plugin

A plugin is a class with an `apply` method that receives the compiler:

```javascript
class BuildStatsPlugin {
  apply(compiler) {
    compiler.hooks.done.tapAsync('BuildStats', (stats, callback) => {
      const json = JSON.stringify(stats.toJson({ modules: false }), null, 2);
      require('fs').writeFileSync('build-stats.json', json);
      callback();
    });
  }
}
```

## Source Maps

Source maps map minified/bundled code back to original source files, enabling debugging in production.

Webpack's `devtool` option controls source map generation:

| Setting | Rebuild Speed | Quality | Use Case |
|---------|--------------|---------|----------|
| `eval` | Fastest | Generated code | Development |
| `eval-source-map` | Slow | Original source | Development (accurate) |
| `cheap-source-map` | Medium | Lines only | CI/staging |
| `source-map` | Slowest | Full quality | Production debugging |

**Best practices:**
- Development: `eval-source-map` for accurate debugging with reasonable rebuild speed.
- Production: `source-map` for error tracking services (Sentry, Bugsnag), but don't serve `.map` files publicly in proprietary projects.

## Corepack

Corepack is a Node.js tool (built-in since Node 16.10) that manages package manager versions (Yarn, pnpm) per-project.

```bash
corepack enable          # set up shims for yarn/pnpm
corepack prepare pnpm@latest --activate  # pin a specific version
```

When `packageManager` is specified in `package.json`, Corepack ensures the correct version is used automatically, preventing version mismatches across team members.

# 8. Networking & Security


## 8.1 HTTP Protocols and WebSockets

## RESTful API

REST (Representational State Transfer) uses standard HTTP methods to operate on resources identified by URLs:

| Method | Purpose | Idempotent |
|--------|---------|------------|
| GET | Retrieve a resource | Yes |
| POST | Create a new resource | No |
| PUT | Replace a resource entirely | Yes |
| PATCH | Partially update a resource | No |
| DELETE | Remove a resource | Yes |

Example for a blog API: `GET /posts`, `POST /posts`, `PUT /posts/1`, `DELETE /posts/1`.

## HTTP Headers

**Request headers:**
- `Accept`: MIME types the client accepts (e.g., `application/json`).
- `Authorization`: Credentials (e.g., `Bearer <token>`).
- `Content-Type`: Body format (e.g., `application/json`).
- `Cookie`: Stored cookies sent to the server.

**Response headers:**
- `Cache-Control`: Caching directives (`no-cache`, `max-age=3600`).
- `Content-Length`: Body size in bytes.
- `Set-Cookie`: Store a cookie on the client.

**Negotiation headers:**
- `Accept-Encoding`: Compression formats (`gzip`, `br`).
- `Accept-Language`: Preferred languages.

## HTTP Status Codes

| Range | Category | Common Codes |
|-------|----------|-------------|
| 1xx | Informational | 100 Continue |
| 2xx | Success | 200 OK, 201 Created, 204 No Content |
| 3xx | Redirection | 301 Moved Permanently, 302 Found, 304 Not Modified |
| 4xx | Client Error | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| 5xx | Server Error | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable |

## Ajax, Fetch, and Axios

### XMLHttpRequest (Ajax)

The original browser API for async HTTP requests. Callback-based and verbose.

```javascript
const xhr = new XMLHttpRequest();
xhr.open('GET', '/api/data');
xhr.onload = () => {
  if (xhr.status === 200) console.log(JSON.parse(xhr.responseText));
};
xhr.send();
```

### Fetch API

Native, promise-based API. Cleaner syntax but does not reject on HTTP error status codes (only on network failure).

```javascript
const response = await fetch('/api/data');
if (!response.ok) throw new Error(`HTTP ${response.status}`);
const data = await response.json();
```

### Axios

Third-party library with automatic JSON parsing, interceptors, request cancellation, and consistent behavior across browser and Node.js.

```javascript
const { data } = await axios.get('/api/data');
```

## OSI Model and TCP/IP

### OSI 7-Layer Model

| Layer | Name | Examples |
|-------|------|----------|
| 7 | Application | HTTP, FTP, DNS |
| 6 | Presentation | SSL/TLS, JPEG |
| 5 | Session | NetBIOS, RPC |
| 4 | Transport | TCP, UDP |
| 3 | Network | IP, ICMP |
| 2 | Data Link | Ethernet, MAC |
| 1 | Physical | Cables, hubs |

The **TCP/IP model** simplifies this into 4 layers: Link, Internet, Transport, Application.

## TCP Connection Lifecycle

### 3-Way Handshake (Connection Establishment)

1. Client → Server: **SYN** (with initial sequence number)
2. Server → Client: **SYN-ACK** (acknowledges and sends its own sequence number)
3. Client → Server: **ACK** (connection established)

### 4-Way Termination

1. A → B: **FIN** (A finished sending)
2. B → A: **ACK** (acknowledged)
3. B → A: **FIN** (B finished sending)
4. A → B: **ACK** (connection closed)

The 4-step process is needed because each direction closes independently -- B may still have data to send after receiving A's FIN.

### TCP Packet Sticking

TCP is stream-oriented, so multiple small writes may arrive as a single read. Solutions:
- **Length-prefixed messages**: Prepend each message with its byte length.
- **Delimiters**: Use a special character (e.g., `\n`) to mark message boundaries.
- **Fixed-length messages**: Pad each message to a fixed size.

## HTTP Version Evolution

| Version | Key Features |
|---------|-------------|
| HTTP/1.0 | New TCP connection per request |
| HTTP/1.1 | Keep-alive (persistent connections), chunked transfer, cache headers (`ETag`, `Cache-Control`) |
| HTTP/2 | Multiplexing (parallel requests over one connection), header compression (HPACK), server push |
| HTTP/3 | Built on QUIC (UDP-based), eliminates TCP head-of-line blocking, faster connection setup |

## CORS (Cross-Origin Resource Sharing)

Same-origin policy restricts requests to the same protocol + domain + port. CORS relaxes this restriction with server-side headers.

**Server response headers:**
```
Access-Control-Allow-Origin: https://example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
```

### Preflight Requests (OPTIONS)

For non-simple requests (e.g., `PUT`, `DELETE`, custom headers), the browser sends an `OPTIONS` request first to check if the server allows the actual request.

### CORS Workarounds

**JSONP**: Exploits `<script>` tags not being subject to same-origin policy. Limited to GET requests.

```html
<script>
  function handleData(data) { console.log(data); }
</script>
<script src="https://api.example.com/data?callback=handleData"></script>
```

**Reverse Proxy (Nginx):**
```nginx
location /api/ {
  proxy_pass http://backend-server:8080/;
}
```

## WebSocket

WebSocket provides full-duplex, bidirectional communication over a single persistent TCP connection. Unlike HTTP, either side can send messages at any time.

### Handshake

WebSocket starts as an HTTP request with an `Upgrade: websocket` header. The server responds with `101 Switching Protocols`.

### Server Example (Node.js)

```javascript
const { WebSocketServer } = require('ws');
const wss = new WebSocketServer({ port: 3000 });
const clients = new Set();

wss.on('connection', (ws) => {
  clients.add(ws);
  ws.on('message', (msg) => {
    clients.forEach(client => {
      if (client !== ws && client.readyState === 1) {
        client.send(msg.toString());
      }
    });
  });
  ws.on('close', () => clients.delete(ws));
});
```

### Client Example

```javascript
const ws = new WebSocket('ws://localhost:3000');
ws.onopen = () => ws.send('Hello');
ws.onmessage = (e) => console.log('Received:', e.data);
ws.onclose = () => console.log('Disconnected');
```

### WebSocket vs HTTP Keep-Alive

HTTP keep-alive reuses TCP connections for multiple request-response pairs, but the server cannot initiate messages. WebSocket maintains a persistent connection where either side can push data at any time, making it ideal for chat, live dashboards, and collaborative editing.

## Resource Hints

| Directive | Purpose | When to Use |
|-----------|---------|-------------|
| `<link rel="preload">` | Fetch critical resource for current page | Fonts, above-the-fold images, key scripts |
| `<link rel="prefetch">` | Hint for next-page resources (low priority) | Resources for likely next navigation |
| `<link rel="dns-prefetch">` | Resolve DNS early | Third-party domains (CDNs, analytics) |
| `<link rel="preconnect">` | DNS + TCP + TLS handshake | High-priority third-party origins |

## 8.2 Web Security and Authentication

## Authentication: Cookies vs Tokens

### Cookie-Based Authentication

1. User logs in with credentials.
2. Server creates a session, stores it server-side, and sets a `Set-Cookie` header with the session ID.
3. Browser automatically sends the cookie with every subsequent request.
4. Server looks up the session by ID to authenticate.

**Characteristics:**
- Automatic transmission with every request (including CORS when `withCredentials` is set).
- ~4KB size limit.
- `HttpOnly` flag prevents JavaScript access, mitigating XSS cookie theft.
- `Secure` flag ensures transmission only over HTTPS.
- `SameSite` flag controls cross-origin sending (CSRF protection).

### Token-Based Authentication (JWT)

1. User logs in with credentials.
2. Server generates a signed JWT containing user claims and returns it in the response body.
3. Client stores the token (typically in memory or localStorage) and sends it via `Authorization: Bearer <token>` header.
4. Server verifies the token's signature without needing a session store.

**JWT advantages:**
- Stateless -- no server-side session storage needed.
- Works naturally across domains (no cookie same-origin restrictions).
- Self-contained -- carries user data in the payload.
- Scales easily in distributed/microservice architectures.

**Trade-offs:**
- Cannot be revoked before expiry without additional infrastructure (e.g., a token blocklist).
- Token size can be larger than a session ID cookie.

## Single Sign-On (SSO)

SSO allows users to authenticate once and access multiple systems without re-entering credentials.

**Flow:**
1. User accesses System A → no session found → redirect to SSO provider.
2. User authenticates at the SSO provider.
3. SSO provider issues a token/ticket and redirects back to System A.
4. System A validates the token with the SSO provider.
5. User accesses System B → SSO certificate already exists → automatic authentication.

Common protocols: SAML, OAuth 2.0, OpenID Connect.

## HTTPS and Man-in-the-Middle Attacks

### Encryption Types

- **Symmetric encryption**: Same key for encryption and decryption. Fast, used for bulk data transfer.
- **Asymmetric encryption**: Public key encrypts, private key decrypts. Slower, used for key exchange.

### HTTPS Key Exchange

1. Client receives the server's **public key** (inside an SSL/TLS certificate).
2. Client generates a random **session key**, encrypts it with the server's public key, and sends it.
3. Server decrypts with its **private key**.
4. Both sides use the session key for symmetric encryption of all subsequent data.

### MitM Attack Vector

An attacker intercepts the initial exchange and substitutes their own public key. The client unknowingly encrypts the session key for the attacker.

**Prevention**: TLS certificates issued by trusted Certificate Authorities (CAs). Browsers verify:
- The certificate is signed by a trusted CA.
- The domain matches the certificate's subject.
- The certificate has not expired or been revoked.

## Common Security Threats

### XSS (Cross-Site Scripting)

Injecting malicious scripts into pages viewed by other users. The script runs in the victim's browser with full access to the page's DOM and cookies.

**Prevention:**
- Escape all user-generated content before rendering (`<` → `&lt;`, `>` → `&gt;`).
- Use frameworks like React that escape output by default.
- Set `Content-Security-Policy` headers to restrict script sources.
- Use `HttpOnly` cookies to prevent JavaScript access to session tokens.

### CSRF (Cross-Site Request Forgery)

Tricks an authenticated user's browser into making unintended requests to a site where they are logged in.

**Prevention:**
- Include anti-CSRF tokens in forms and verify them server-side.
- Set `SameSite=Strict` or `SameSite=Lax` on cookies.
- Verify the `Origin` or `Referer` header on state-changing requests.

### Clickjacking

Overlays a transparent iframe on top of a legitimate page, tricking users into clicking hidden elements.

**Prevention:**
- Set `X-Frame-Options: SAMEORIGIN` (or `DENY`) to prevent framing.
- Use `Content-Security-Policy: frame-ancestors 'self'`.

### DDoS (Distributed Denial of Service)

Overwhelms servers with massive traffic from distributed sources (botnets).

**Prevention:** Cannot be solved purely in application code. Use CDN-based DDoS protection (Cloudflare, AWS Shield), rate limiting, and Web Application Firewalls (WAFs).

### SQL Injection

Injecting SQL through user input fields to manipulate database queries.

**Prevention:**
- Use parameterized queries / prepared statements.
- Validate and sanitize all user input.
- Apply the principle of least privilege to database accounts.

# 9. React & Frameworks


## 9.1 Virtual DOM and Framework Selection

## Virtual DOM

### How It Works

1. On data change, the entire UI is re-rendered as a **Virtual DOM** (a lightweight JavaScript object tree).
2. A **diffing algorithm** compares the new tree with the previous one.
3. Only the **minimal set of changes** is computed and applied to the real DOM in a batched update.

### Is Virtual DOM Fast?

Direct DOM manipulation (e.g., jQuery) can be faster for simple, isolated updates because it skips the diffing overhead. The Virtual DOM's advantage appears in complex applications with frequent state changes:

- **Batching**: Multiple state changes are combined into a single DOM update.
- **Minimal updates**: Only changed nodes are touched, avoiding full re-renders.
- **Developer efficiency**: Developers describe the desired UI state; the framework figures out the DOM operations.

The real value of Virtual DOM is not raw speed but **predictable performance at scale** combined with a component-based architecture that separates data from view logic.

## Choosing a Frontend Framework

There is no universally "best" stack. The decision depends on:

### Framework Choice

- **React / Next.js**: Best for large applications with complex state, rich interactivity, and a large ecosystem. Component-based, unidirectional data flow.
- **Vue / Nuxt.js**: Lower learning curve, excellent documentation, progressive adoption. Good for teams transitioning from jQuery or smaller projects.

### Language Choice

- **JavaScript**: Maximum flexibility, faster onboarding, largest ecosystem.
- **TypeScript**: Type safety, better refactoring support, fewer runtime bugs. Preferred for large teams and long-lived codebases.

### Decision Factors

- **Community maturity**: Size of ecosystem, frequency of updates, available talent.
- **Team experience**: Productivity is highest with familiar tools.
- **Learning cost**: TypeScript adds initial overhead but reduces long-term maintenance cost.
- **Project requirements**: SSR needs, mobile targets, performance constraints.

## 9.2 React Basics

## JSX

JSX is a syntax extension that lets you write HTML-like markup inside JavaScript. It is transpiled to `React.createElement()` calls:

```jsx
const element = <h1 className="title">Hello</h1>;
// Transpiles to:
const element = React.createElement('h1', { className: 'title' }, 'Hello');
```

Rules:
- Custom components must start with an **uppercase** letter.
- JavaScript expressions inside JSX use `{}`.
- JSX attributes use camelCase (`className`, `onClick`).

## React Diff Algorithm

React's reconciliation algorithm compares Virtual DOM trees efficiently:

1. **Same-level comparison**: Only nodes at the same tree depth are compared.
2. **Different element types**: If the root element changes (e.g., `<div>` → `<span>`), the entire subtree is replaced.
3. **Keys for lists**: When rendering lists, `key` props help React identify which items changed, were added, or removed. Keys should be stable and unique (use item IDs, not array indices).

```jsx
{items.map(item => (
  <ListItem key={item.id} data={item} />
))}
```

Using array indices as keys causes bugs when the list is reordered, filtered, or items are inserted in the middle.

## Component Lifecycle (Class Components)

### Mounting

`constructor` → `getDerivedStateFromProps` → `render` → `componentDidMount`

### Updating

`getDerivedStateFromProps` → `shouldComponentUpdate` → `render` → `getSnapshotBeforeUpdate` → `componentDidUpdate`

### Unmounting

`componentWillUnmount` -- clean up timers, subscriptions, and event listeners here.

### Error Handling

`getDerivedStateFromError` (update state to show fallback UI) and `componentDidCatch` (log error details).

## ErrorBoundary

A class component that catches rendering errors in its subtree and displays a fallback UI instead of crashing the entire app.

```jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) return <h1>Something went wrong.</h1>;
    return this.props.children;
  }
}
```

ErrorBoundary does **not** catch errors in event handlers, async code, or SSR. For those, use try/catch.

## `setState` Behavior

In React 17 and earlier:
- **Batched** (async) in React lifecycle methods and event handlers.
- **Synchronous** in `setTimeout`, Promises, and native DOM events.

In React 18+:
- **Automatic batching** in all contexts, including `setTimeout` and Promises. All `setState` calls within the same tick are batched into one re-render.

```javascript
// React 18 entry point
import { createRoot } from 'react-dom/client';
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## React Router

React Router provides declarative routing for SPAs.

```jsx
<BrowserRouter>
  <Routes>
    <Route path="/" element={<Home />} />
    <Route path="/posts/:postId" element={<Post />} />
  </Routes>
</BrowserRouter>
```

```jsx
function Post() {
  const { postId } = useParams();
  return <h1>Post {postId}</h1>;
}
```

**Router modes:**
- `BrowserRouter`: Uses the History API (`/path`). Requires server configuration to serve `index.html` for all routes.
- `HashRouter`: Uses URL hash (`/#/path`). Works without server configuration.
- `MemoryRouter`: In-memory, no URL changes. Used for testing and non-browser environments.

## SPA vs MPA

| Aspect | SPA | MPA |
|--------|-----|-----|
| Navigation | Client-side routing, no full reload | Full page reload per navigation |
| Initial load | Slower (downloads entire app bundle) | Faster (smaller per-page bundles) |
| SEO | Challenging (requires SSR/SSG) | Native SEO support |
| UX | Smooth, app-like transitions | Traditional page transitions |
| Complexity | Higher (state management, routing) | Lower per page |
| Examples | Gmail, Figma, Notion | News sites, e-commerce |

## 9.3 Advanced React

## Component Communication

### Parent → Child
- **Props**: The standard data flow. Parent passes data and callbacks as props.
- **Refs**: Parent accesses child DOM nodes or imperative methods via `ref`.
- **Context API**: Shares data across deeply nested components without prop drilling.

### Child → Parent
- **Callback props**: Parent passes a function; child calls it with data.
- **`forwardRef` + `useImperativeHandle`**: Child exposes specific methods to the parent via ref.
- **Event bubbling**: Native DOM events bubble up; parent listens on a wrapper element.

### Cross-Component
- **State management libraries**: Redux, Zustand, Jotai, MobX.
- **Custom hooks**: Share stateful logic between components.
- **Event systems**: Custom EventBus for decoupled communication.

## Hooks

### `useCallback`

Memoizes a function reference so it remains stable across renders. Prevents unnecessary re-renders of child components that depend on the callback.

```javascript
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);
```

### `useMemo`

Memoizes a computed value. Only recalculates when dependencies change.

```javascript
const sortedList = useMemo(() => {
  return items.sort((a, b) => a.name.localeCompare(b.name));
}, [items]);
```

### `React.memo`

Higher-order component that prevents re-rendering when props haven't changed (shallow comparison).

```javascript
const ExpensiveList = React.memo(({ items }) => {
  return items.map(item => <Item key={item.id} data={item} />);
});
```

Combine `React.memo` with `useCallback` for maximum effect: memo skips re-render only if prop references are stable.

### `useRef`

Returns a mutable ref object that persists across renders without causing re-renders when mutated.

```javascript
const inputRef = useRef(null);
const focusInput = () => inputRef.current.focus();

return <input ref={inputRef} />;
```

Use cases: DOM access, storing previous values, holding timer/interval IDs.

### `forwardRef`

Allows a parent to pass a `ref` through to a child's DOM element:

```javascript
const FancyInput = forwardRef((props, ref) => (
  <input ref={ref} className="fancy" {...props} />
));

// Parent
const ref = useRef(null);
<FancyInput ref={ref} />
```

### Custom Hooks vs Regular Functions

| Custom Hooks | Regular Functions |
|-------------|-------------------|
| Can use React hooks (`useState`, `useEffect`, etc.) | Cannot use hooks |
| Manage state and side effects | Pure computation or utilities |
| Re-run on every render | Called explicitly |
| Follow the `use` naming convention | Any naming |

```javascript
function useWindowSize() {
  const [size, setSize] = useState({ width: 0, height: 0 });
  useEffect(() => {
    const handler = () => setSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handler);
    handler();
    return () => window.removeEventListener('resize', handler);
  }, []);
  return size;
}
```

## Render Props

A pattern where a component receives a function as a prop that returns JSX, giving the consumer control over what to render:

```jsx
<MouseTracker render={({ x, y }) => (
  <p>Mouse position: {x}, {y}</p>
)} />
```

This pattern has been largely replaced by custom hooks, which achieve the same reusability with simpler syntax.

## Higher-Order Components (HOCs)

A function that takes a component and returns a new component with additional behavior:

```javascript
function withAuth(WrappedComponent) {
  return function AuthenticatedComponent(props) {
    const user = useAuth();
    if (!user) return <Redirect to="/login" />;
    return <WrappedComponent {...props} user={user} />;
  };
}

const ProtectedPage = withAuth(Dashboard);
```

HOCs are useful for cross-cutting concerns (auth, logging, error boundaries) but can lead to "wrapper hell." Custom hooks are often a cleaner alternative.

## Conditional Rendering Patterns

```jsx
// Ternary
{isLoggedIn ? <Dashboard /> : <Login />}

// Logical AND (renders nothing when false)
{showBanner && <Banner />}

// Early return
function Component({ data }) {
  if (!data) return <Loading />;
  return <Content data={data} />;
}

// Element variable
let content;
if (error) content = <Error />;
else if (loading) content = <Spinner />;
else content = <Data />;
return <div>{content}</div>;
```

## 9.4 Next.js

## Why Next.js Over Plain React

- **Server-Side Rendering (SSR)**: HTML generated per request for SEO and fast first paint.
- **Static Site Generation (SSG)**: Pre-built HTML at build time for maximum performance.
- **File-based routing**: Pages map directly to file paths, no manual route configuration.
- **API routes**: Backend endpoints inside the same project (`/pages/api/`).
- **Built-in optimizations**: Automatic code splitting, image optimization (`next/image`), font optimization.

## Rendering Strategies

### SSR (Server-Side Rendering)

HTML is generated on the server for each request. The client receives fully rendered HTML, then React **hydrates** it to make it interactive.

```javascript
export async function getServerSideProps(context) {
  const res = await fetch(`https://api.example.com/posts`);
  const posts = await res.json();
  return { props: { posts } };
}
```

**When to use**: Pages with frequently changing data that needs SEO (e.g., product pages, dashboards).

### SSG (Static Site Generation)

HTML is generated at **build time**. Pages are served as static files from a CDN.

```javascript
export async function getStaticProps() {
  const res = await fetch('https://api.example.com/posts');
  const posts = await res.json();
  return { props: { posts } };
}

export async function getStaticPaths() {
  const res = await fetch('https://api.example.com/posts');
  const posts = await res.json();
  return {
    paths: posts.map(post => ({ params: { id: post.id.toString() } })),
    fallback: false
  };
}
```

**When to use**: Content that rarely changes (blogs, docs, marketing pages).

### ISR (Incremental Static Regeneration)

Combines SSG with on-demand revalidation. Pages are statically generated but can be regenerated in the background after a specified interval.

```javascript
export async function getStaticProps() {
  const res = await fetch('https://api.example.com/posts');
  const posts = await res.json();
  return {
    props: { posts },
    revalidate: 60 // regenerate at most every 60 seconds
  };
}
```

**When to use**: Content that updates periodically but doesn't need real-time freshness (e-commerce catalogs, news feeds).

### Comparison

| Strategy | Build Time | Request Time | Freshness | SEO |
|----------|-----------|-------------|-----------|-----|
| CSR | Fast | Slow (JS renders) | Real-time | Poor |
| SSR | N/A | Moderate (server renders) | Real-time | Good |
| SSG | Slow | Fast (pre-built) | Stale until rebuild | Good |
| ISR | Moderate | Fast (cached) | Periodic | Good |

## Routing

### File-Based Routing

```
pages/
  index.js        →  /
  about.js         →  /about
  posts/[id].js    →  /posts/123
  [...slug].js     →  /docs/a/b/c
```

### Dynamic Routes

```jsx
import { useRouter } from 'next/router';

function Post() {
  const router = useRouter();
  const { id } = router.query;
  return <h1>Post {id}</h1>;
}
```

### Navigation

```jsx
import Link from 'next/link';

<Link href="/posts/1">Read Post</Link>

// Programmatic
const router = useRouter();
router.push('/posts/1');
```

Next.js **prefetches** linked pages in the background for instant client-side navigation.

## API Routes

Server-side endpoints defined inside the project:

```javascript
// pages/api/hello.js
export default function handler(req, res) {
  res.status(200).json({ message: 'Hello from Next.js' });
}
```

Supports all HTTP methods. Useful for form handling, proxying external APIs, and lightweight backend logic without a separate server.

# 10. Data Structures & Algorithms


## 10.1 Algorithms and Complexity

## Dynamic Programming

Dynamic programming (DP) solves problems by breaking them into overlapping subproblems and storing results to avoid redundant computation.

### Fibonacci

**Recursive** -- O(2^n) time, O(n) stack space. Exponential due to repeated subproblems.

```javascript
function fib(n) {
  if (n <= 1) return n;
  return fib(n - 1) + fib(n - 2);
}
```

**DP (iterative)** -- O(n) time, O(1) space.

```javascript
function fib(n) {
  if (n <= 1) return n;
  let prev = 0, curr = 1;
  for (let i = 2; i <= n; i++) {
    [prev, curr] = [curr, prev + curr];
  }
  return curr;
}
```

### Frog Jump (Climbing Stairs)

Count the number of ways to reach step `n` by jumping 1 or 2 steps at a time. Same recurrence as Fibonacci: `dp[i] = dp[i-1] + dp[i-2]`.

Generalized to variable step sizes:

```javascript
function climbStairs(n, steps) {
  const dp = new Array(n + 1).fill(0);
  dp[0] = 1;
  for (let i = 1; i <= n; i++) {
    for (const step of steps) {
      if (i >= step) dp[i] += dp[i - step];
    }
  }
  return dp[n];
}
```

### 0-1 Knapsack

Maximize total value without exceeding weight capacity. Each item can be used at most once. Iterate capacities in reverse to prevent reusing items.

```javascript
function knapsack(W, weights, values) {
  const dp = new Array(W + 1).fill(0);
  for (let i = 0; i < weights.length; i++) {
    for (let w = W; w >= weights[i]; w--) {
      dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
    }
  }
  return dp[W];
}
```

## Binary Search

O(log n). Requires a sorted array. Halves the search space each iteration.

```javascript
function binarySearch(nums, target) {
  let left = 0, right = nums.length - 1;
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (nums[mid] === target) return mid;
    if (nums[mid] < target) left = mid + 1;
    else right = mid - 1;
  }
  return -1;
}
```

## Two Pointers

### Two Sum (Sorted Array)

```javascript
function twoSum(nums, target) {
  let left = 0, right = nums.length - 1;
  while (left < right) {
    const sum = nums[left] + nums[right];
    if (sum === target) return [left, right];
    if (sum < target) left++;
    else right--;
  }
  return [-1, -1];
}
```

### Move Zeros to End (In-Place)

```javascript
function moveZeros(nums) {
  let insertPos = 0;
  for (let i = 0; i < nums.length; i++) {
    if (nums[i] !== 0) {
      [nums[insertPos], nums[i]] = [nums[i], nums[insertPos]];
      insertPos++;
    }
  }
}
```

## Sorting

### Quicksort

Average O(n log n), worst O(n^2). Choose a pivot, partition into smaller/larger subarrays, recurse.

```javascript
function quickSort(arr) {
  if (arr.length <= 1) return arr;
  const pivot = arr[Math.floor(arr.length / 2)];
  const left = [], mid = [], right = [];
  for (const x of arr) {
    if (x < pivot) left.push(x);
    else if (x > pivot) right.push(x);
    else mid.push(x);
  }
  return [...quickSort(left), ...mid, ...quickSort(right)];
}
```

## String Algorithms

### Palindrome Check

```javascript
function isPalindrome(n) {
  const s = String(n);
  let left = 0, right = s.length - 1;
  while (left < right) {
    if (s[left++] !== s[right--]) return false;
  }
  return true;
}
```

### Longest Consecutive Character

```javascript
function longestConsecutive(s) {
  let maxChar = '', maxLen = 0;
  let curLen = 1;
  for (let i = 1; i <= s.length; i++) {
    if (i < s.length && s[i] === s[i - 1]) {
      curLen++;
    } else {
      if (curLen > maxLen) {
        maxLen = curLen;
        maxChar = s[i - 1];
      }
      curLen = 1;
    }
  }
  return { char: maxChar, len: maxLen };
}
```

### Number Formatting (Thousand Separators)

```javascript
function formatNumber(n) {
  return n.toLocaleString();
}

// Manual implementation
function formatNumber(n) {
  const s = String(n);
  let result = '';
  let count = 0;
  for (let i = s.length - 1; i >= 0; i--) {
    result = s[i] + result;
    if (++count % 3 === 0 && i > 0) result = ',' + result;
  }
  return result;
}
```

### Switch Letter Case

```javascript
function switchCase(s) {
  return s.split('').map(ch => {
    const code = ch.charCodeAt(0);
    if (code >= 65 && code <= 90) return String.fromCharCode(code + 32);
    if (code >= 97 && code <= 122) return String.fromCharCode(code - 32);
    return ch;
  }).join('');
}
```

## 10.2 Core Data Structures

## Tree Traversals

For a binary tree, three depth-first traversal orders exist:

- **In-order** (Left → Root → Right): Produces sorted output for BSTs.
- **Pre-order** (Root → Left → Right): Useful for copying/serializing trees.
- **Post-order** (Left → Right → Root): Useful for deletion (children before parent).

### Kth Smallest in a BST

In-order traversal visits BST nodes in ascending order. Stop at the kth node.

```javascript
function kthSmallest(root, k) {
  let count = 0, result = null;

  function inorder(node) {
    if (!node || result !== null) return;
    inorder(node.left);
    if (++count === k) { result = node.val; return; }
    inorder(node.right);
  }

  inorder(root);
  return result;
}
```

## Why Binary Trees?

| Structure | Access | Insert/Delete |
|-----------|--------|---------------|
| Array | O(1) | O(n) |
| Linked List | O(n) | O(1) |
| Balanced BST | O(log n) | O(log n) |

A balanced binary tree provides O(log n) for all operations -- the "best of both worlds" between arrays and linked lists. An unbalanced tree degrades to a linked list with O(n) operations.

## Self-Balancing Trees

### Red-Black Tree

A BST with coloring rules that ensure the tree remains approximately balanced after insertions and deletions. Properties:
- Each node is red or black.
- The root is black.
- No two consecutive red nodes on any path.
- All paths from root to leaf have the same number of black nodes.

Used in: `std::map` (C++), `TreeMap` (Java), Linux kernel scheduler.

### B-Tree / B+ Tree

Multi-way search trees optimized for disk I/O. Each node contains multiple keys and children, minimizing the number of disk reads needed.

- **B-Tree**: Keys and data in all nodes.
- **B+ Tree**: Data only in leaf nodes; leaves are linked for efficient range queries.

Used in: Database indexes (MySQL InnoDB, PostgreSQL), file systems.

## Trie (Prefix Tree)

A tree where each node represents a character. Paths from root to node spell prefixes. Checking if a string is a prefix takes O(m) time where m is the string length.

Use cases: Autocomplete, spell checking, IP routing tables.

## DOM Tree Traversal

### DFS (Depth-First Search)

```javascript
function dfs(node) {
  visit(node);
  node.childNodes.forEach(child => dfs(child));
}

// Iterative with stack
function dfsIterative(node) {
  const stack = [node];
  while (stack.length) {
    const n = stack.pop();
    visit(n);
    const children = Array.from(n.childNodes);
    for (let i = children.length - 1; i >= 0; i--) {
      stack.push(children[i]);
    }
  }
}
```

### BFS (Breadth-First Search)

```javascript
function bfs(node) {
  const queue = [node];
  while (queue.length) {
    const n = queue.shift();
    visit(n);
    n.childNodes.forEach(child => queue.push(child));
  }
}
```

## Array ↔ Tree Conversion

A common interview question that relates to how relational databases (flat rows) map to hierarchical UI structures (tree components).

### Array to Tree

```javascript
function arrayToTree(arr) {
  const map = new Map();
  let root = null;

  arr.forEach(item => map.set(item.id, { ...item, children: [] }));

  arr.forEach(item => {
    const node = map.get(item.id);
    if (item.parentId === 0) {
      root = node;
    } else {
      map.get(item.parentId)?.children.push(node);
    }
  });

  return root;
}
```

### Tree to Array

```javascript
function treeToArray(tree) {
  const result = [];
  function traverse(node, parentId) {
    result.push({ id: node.id, parentId, name: node.name });
    node.children?.forEach(child => traverse(child, node.id));
  }
  traverse(tree, 0);
  return result;
}
```

## 10.3 Practical Data Structure Implementations

## LRU Cache

Least Recently Used cache evicts the least recently accessed item when the cache reaches capacity. A common interview question that tests understanding of hash maps and ordering.

### Using Map (Insertion Order)

JavaScript `Map` maintains insertion order, which can be exploited for LRU behavior by deleting and re-inserting entries on access.

```javascript
class LRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.cache = new Map();
  }

  get(key) {
    if (!this.cache.has(key)) return -1;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }

  put(key, value) {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.capacity) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}
```

### Using Doubly Linked List + Hash Table

The classic O(1) implementation: a hash table for key lookup and a doubly linked list for ordering. Most recently used items move to the head; the tail is evicted when full.

```javascript
class ListNode {
  constructor(key, value) {
    this.key = key;
    this.value = value;
    this.prev = null;
    this.next = null;
  }
}

class LRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.map = {};
    this.head = new ListNode(0, 0);
    this.tail = new ListNode(0, 0);
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  get(key) {
    if (!(key in this.map)) return -1;
    const node = this.map[key];
    this._remove(node);
    this._addToHead(node);
    return node.value;
  }

  put(key, value) {
    if (key in this.map) {
      const node = this.map[key];
      node.value = value;
      this._remove(node);
      this._addToHead(node);
    } else {
      if (Object.keys(this.map).length >= this.capacity) {
        const lru = this.tail.prev;
        this._remove(lru);
        delete this.map[lru.key];
      }
      const newNode = new ListNode(key, value);
      this.map[key] = newNode;
      this._addToHead(newNode);
    }
  }

  _addToHead(node) {
    node.next = this.head.next;
    node.prev = this.head;
    this.head.next.prev = node;
    this.head.next = node;
  }

  _remove(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }
}
```

## Queue

FIFO (First In, First Out). Used in BFS, task scheduling, and message processing.

### Linked List Implementation

Array-based `shift()` is O(n) because elements must be moved. A linked list queue provides O(1) enqueue and dequeue.

```javascript
class Queue {
  constructor() {
    this.head = null;
    this.tail = null;
    this.length = 0;
  }

  enqueue(val) {
    const node = { val, next: null };
    if (this.tail) {
      this.tail.next = node;
    } else {
      this.head = node;
    }
    this.tail = node;
    this.length++;
  }

  dequeue() {
    if (!this.head) return null;
    const val = this.head.val;
    this.head = this.head.next;
    if (!this.head) this.tail = null;
    this.length--;
    return val;
  }
}
```

## Stack

LIFO (Last In, First Out). Used in DFS, undo/redo, expression parsing, and browser history.

```javascript
class Stack {
  constructor() {
    this.items = [];
  }
  push(val) { this.items.push(val); }
  pop() { return this.items.pop(); }
  peek() { return this.items[this.items.length - 1]; }
  isEmpty() { return this.items.length === 0; }
}
```

## Linked Lists in Frontend

React Fiber represents the component tree as a linked structure (child, sibling, return pointers) rather than a traditional tree. This enables:
- **Incremental rendering**: Work can be split into small units and spread across frames.
- **Priority-based scheduling**: High-priority updates (input, animations) can interrupt lower-priority rendering.
- **Pause and resume**: Rendering can yield to the browser for layout and paint, then resume.

# 11. Performance Optimization


## 11.1 Performance Metrics and Analysis

## Performance Metrics

### Core Web Vitals

| Metric | Description | Target |
|--------|-------------|--------|
| **FP** (First Paint) | First pixel rendered on screen | -- |
| **FCP** (First Contentful Paint) | First DOM content visible (text, image) | < 1.8s |
| **LCP** (Largest Contentful Paint) | Largest visible element rendered | < 2.5s |
| **FID** (First Input Delay) | Time from first interaction to response | < 100ms |
| **CLS** (Cumulative Layout Shift) | Visual stability during loading | < 0.1 |
| **DCL** (DOMContentLoaded) | DOM fully parsed, no stylesheets/images | -- |
| **Load** | Page and all resources fully loaded | -- |

The loading order is: FP → FCP → LCP → DCL → Load.

### Measuring with Chrome DevTools

- **Performance tab**: Record CPU, memory, network, and rendering. Enables screenshots at intervals to see exactly when content appears.
- **Network tab**: Request waterfall, timing breakdown, and size analysis.
- **React DevTools**: "Highlight updates when components render" shows unnecessary re-renders.

### Lighthouse

Automated auditing tool that scores Performance, Accessibility, Best Practices, and SEO.

```bash
npx lighthouse https://example.com --view --preset=desktop
```

Lighthouse provides actionable suggestions: use modern image formats (WebP/AVIF), eliminate render-blocking resources, reduce unused JavaScript, and set explicit image dimensions.

## Diagnosing Slow Pages

### Slow Loading

- Optimize server response time; use a CDN.
- Enable HTTP caching (`Cache-Control`, `ETag`).
- Route-based code splitting with `React.lazy` + `Suspense`.
- Compress assets (gzip, Brotli).
- Preload critical resources (`<link rel="preload">`).

### Slow Rendering

- Profile with DevTools to identify long tasks.
- Optimize API response times.
- Use SSR (Next.js) for content-heavy pages.
- Virtualize long lists.

### HTTP Caching

| Header | Purpose |
|--------|---------|
| `Cache-Control: max-age=31536000` | Cache for 1 year; use content hashing in filenames for cache busting |
| `ETag` | Version identifier; server returns 304 if unchanged |
| `Last-Modified` | Timestamp-based validation |

Strategy: Immutable assets (JS/CSS bundles with content hash) get long `max-age`. HTML gets `no-cache` with `ETag` to always revalidate.

## Debounce vs Throttle

### Debounce

Delays execution until a specified period of inactivity. Resets the timer on every call.

```javascript
function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
```

Use cases: search input, form validation, window resize handling.

### Throttle

Ensures a function runs at most once per interval, regardless of how often it's called.

```javascript
function throttle(fn, interval) {
  let lastTime = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastTime >= interval) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
}
```

Use cases: scroll handlers, mousemove tracking, rate-limited API calls.

| | Debounce | Throttle |
|---|---------|----------|
| Fires | After inactivity period | At regular intervals |
| Best for | Final value matters (search) | Steady updates matter (scroll) |

## First-Screen Optimization

1. **Route lazy loading**: Split SPA bundles per route; load on demand.
2. **SSR**: Pre-render HTML on the server for immediate content display.
3. **Above-the-fold prioritization**: Inline critical CSS, defer non-critical JS.
4. **Image optimization**: Lazy-load below-fold images; use `srcset` and modern formats.
5. **Pagination / infinite scroll**: Load data incrementally instead of all at once.

## Designing an Analytics SDK

An analytics SDK collects and reports user behavior data with minimal performance impact.

### Key Metrics

- **Page Views (PV)**: Track navigation using the History API.
- **Custom Events**: Business-specific interactions (button clicks, form submissions).
- **Performance Data**: `performance.timing` for load metrics.
- **Errors**: `window.onerror` and `unhandledrejection` for runtime errors.

### Reporting Strategy

Use `navigator.sendBeacon()` for reliable delivery (works during page unload). Fall back to image beacons (`new Image().src`) for broader compatibility.

```javascript
function report(url, data) {
  const body = JSON.stringify(data);
  if (navigator.sendBeacon) {
    navigator.sendBeacon(url, body);
  } else {
    new Image().src = `${url}?data=${encodeURIComponent(body)}`;
  }
}
```

Batch events and send periodically (e.g., every 10 seconds or on page unload) to reduce network overhead.

## 11.2 Rendering and Computation Optimization

## Virtual Scrolling

When rendering large datasets (thousands of rows), creating DOM nodes for every item causes severe performance issues. Virtual scrolling renders only the visible items plus a small buffer.

### How It Works

1. A container has a fixed height with `overflow: auto`.
2. A spacer element simulates the full content height.
3. Only items within the visible viewport (plus a few extra for smooth scrolling) are rendered.
4. On scroll, items are recycled: exiting items are removed and entering items are created.

### Libraries

- **React**: `react-virtualized`, `react-window`, `@tanstack/virtual`
- **Vue**: `vue-virtual-scroll-list`

The key trade-off: virtual scrolling adds implementation complexity but makes rendering performance independent of list size.

## React Performance Optimization

### CSS-Based Visibility Toggle

Use `display: none` to hide components without unmounting them, preserving their state and avoiding remount cost:

```jsx
<ExpensiveComponent style={{ display: isVisible ? 'block' : 'none' }} />
```

### Stable Keys in Lists

Always use unique, stable IDs as keys. Array indices cause incorrect reconciliation when items are reordered or filtered.

```jsx
{items.map(item => <Item key={item.id} data={item} />)}
```

### Fragments

Avoid unnecessary wrapper `<div>` elements that increase DOM depth:

```jsx
return (
  <>
    <Header />
    <Content />
  </>
);
```

### Avoid Inline Function Definitions

Inline arrow functions in JSX create new references on every render, bypassing `React.memo`:

```jsx
// Creates new function reference each render
<Button onClick={() => handleClick(id)} />

// Stable reference
const handleItemClick = useCallback(() => handleClick(id), [id]);
<Button onClick={handleItemClick} />
```

### `shouldComponentUpdate` / `PureComponent` / `React.memo`

**Class components:**
```javascript
shouldComponentUpdate(nextProps, nextState) {
  return nextProps.id !== this.props.id;
}
// Or extend React.PureComponent for automatic shallow comparison
```

**Function components:**
```javascript
const MemoizedComponent = React.memo(MyComponent);

// With custom comparator
const MemoizedComponent = React.memo(MyComponent, (prevProps, nextProps) => {
  return prevProps.id === nextProps.id;
});
```

### Performance Debugging Workflow

1. **Chrome DevTools Performance tab**: Record interactions, identify long tasks and excessive re-renders.
2. **React DevTools Profiler**: Visualize component render times and identify unnecessary renders.
3. **"Highlight updates"**: Enable in React DevTools to see which components re-render on state changes.
4. Isolate the problem: move state closer to where it's needed, split large components, and memoize expensive computations.

## CSS Performance Tips

### Shorthand Properties

```css
/* Verbose */
margin-top: 10px;
margin-right: 20px;
margin-bottom: 30px;
margin-left: 40px;

/* Shorthand */
margin: 10px 20px 30px 40px;
```

Shorthand properties reduce file size and improve parse time.

### CSS Sprites

Combine multiple small images into a single file and use `background-position` to display each one. Reduces HTTP requests (less relevant with HTTP/2 multiplexing but still useful for icon sets).

### `will-change`

Hints to the browser about upcoming transformations, allowing it to optimize compositing:

```css
.animated-element {
  will-change: transform, opacity;
}
```

Use sparingly -- applying `will-change` to too many elements wastes GPU memory.

# 12. Architecture & Design Patterns


## 12.1 Software Design Principles

## SOLID Principles

### Single Responsibility Principle (SRP)

A class or module should have only one reason to change. Each unit of code should do one thing well.

```javascript
// Violates SRP: handles both data fetching and rendering
class UserPage {
  fetchUser() { /* ... */ }
  renderUser() { /* ... */ }
}

// Follows SRP: separate concerns
class UserService { fetchUser() { /* ... */ } }
class UserView { render(user) { /* ... */ } }
```

### Open/Closed Principle (OCP)

Software entities should be open for extension but closed for modification. Add new behavior by writing new code, not changing existing code.

```javascript
// Closed for modification, open for extension
class ShippingCalculator {
  constructor(strategy) { this.strategy = strategy; }
  calculate(pkg) { return this.strategy.calculate(pkg); }
}

// Extend by adding new strategies, not modifying ShippingCalculator
class ExpressShipping { calculate(pkg) { return pkg.weight * 10; } }
class StandardShipping { calculate(pkg) { return pkg.weight * 5; } }
```

### Liskov Substitution Principle (LSP)

Subtypes must be substitutable for their base types without altering program correctness. If `Bird` has a `fly()` method, `Penguin extends Bird` should not throw an error on `fly()`.

### Interface Segregation Principle (ISP)

Clients should not be forced to depend on interfaces they do not use. Prefer many small, specific interfaces over one large general-purpose interface.

### Dependency Inversion Principle (DIP)

High-level modules should depend on abstractions, not concrete implementations. This enables swapping implementations without modifying consumers.

```javascript
// High-level module depends on an abstraction
class NotificationService {
  constructor(sender) { this.sender = sender; }
  notify(message) { this.sender.send(message); }
}

// Low-level implementations
class EmailSender { send(msg) { /* send email */ } }
class SmsSender { send(msg) { /* send SMS */ } }

new NotificationService(new EmailSender());
new NotificationService(new SmsSender());
```

## Other Key Principles

### DRY (Don't Repeat Yourself)

Every piece of knowledge should have a single, unambiguous representation. Extract repeated logic into shared functions or modules.

### KISS (Keep It Simple, Stupid)

Prefer the simplest solution that works. Complexity should be justified by concrete requirements, not anticipated future needs.

### YAGNI (You Aren't Gonna Need It)

Don't implement functionality until it's actually needed. Premature abstraction adds maintenance burden without delivering value.

## Frontend Architecture Patterns

### Component-Based Architecture

Modern frameworks (React, Vue) organize UIs as trees of reusable, self-contained components. Each component manages its own state and rendering logic.

### Flux / Unidirectional Data Flow

Data flows in one direction: Action → Dispatcher → Store → View. This predictability makes debugging and testing easier. Redux, Zustand, and MobX implement variations of this pattern.

### Micro-Frontends

Splitting a large frontend into independently deployable applications, each owned by a different team. Useful for large organizations where teams need autonomy. Trade-offs include increased infrastructure complexity and potential inconsistency.

## 12.2 Design Patterns in Practice

## Factory Pattern

A function that encapsulates object creation, hiding the `new` keyword and allowing the factory to return different types based on input.

```javascript
function createButton(type) {
  if (type === 'primary') return new PrimaryButton();
  if (type === 'secondary') return new SecondaryButton();
  return new DefaultButton();
}
```

Real-world examples: `React.createElement()`, jQuery's `$()`, `document.createElement()`.

## Singleton Pattern

Ensures only one instance of a class exists throughout the application, with a global access point.

```javascript
class Store {
  static instance;

  static getInstance() {
    if (!Store.instance) {
      Store.instance = new Store();
    }
    return Store.instance;
  }
}
```

Real-world examples: Redux/Vuex store, global event bus, database connection pool, `window` object.

## Strategy Pattern

Defines a family of algorithms, encapsulates each one, and makes them interchangeable. Eliminates complex conditional logic.

```javascript
const strategies = {
  express: (pkg) => pkg.weight * 10,
  standard: (pkg) => pkg.weight * 5,
  overnight: (pkg) => pkg.weight * 20
};

function calculateShipping(strategy, pkg) {
  return strategies[strategy](pkg);
}

calculateShipping('express', { weight: 3 }); // 30
```

Use cases: form validation rules, sorting algorithms, pricing tiers, authentication methods.

## Observer Pattern vs Publish-Subscribe

### Observer Pattern

The subject directly notifies its observers. Tight coupling between subject and observer.

```javascript
class Subject {
  constructor() { this.observers = []; }
  subscribe(observer) { this.observers.push(observer); }
  notify(data) { this.observers.forEach(obs => obs.update(data)); }
}
```

Example: DOM event listeners (`element.addEventListener`).

### Publish-Subscribe Pattern

A central event channel mediates between publishers and subscribers. Neither side knows about the other.

```javascript
const eventBus = new EventBus();
eventBus.on('user:login', updateDashboard);   // subscriber
eventBus.emit('user:login', { name: 'Alice' }); // publisher
```

Key difference: Observer has direct coupling (subject knows its observers). Pub-Sub has indirect coupling through an event channel, making it more flexible but harder to trace.

## System Design Examples

### Low-Code Platform Data Model

A drag-and-drop editor for building web pages requires a component model that supports:

- **Component registry**: Unique IDs, type, properties, styles, and children.
- **Layer management**: Z-index controlled via array ordering.
- **Undo/redo**: Command pattern with a history stack of state snapshots.
- **Real-time collaboration**: WebSocket-based state synchronization with conflict resolution.

```javascript
const component = {
  id: 'comp_001',
  type: 'Button',
  props: { text: 'Click me', variant: 'primary' },
  style: { position: 'absolute', top: 100, left: 200 },
  children: []
};
```

### RBAC (Role-Based Access Control)

A system where permissions are assigned to roles, and roles are assigned to users.

**Data models:**
- `User`: id, username, password_hash
- `Role`: id, role_name (e.g., admin, editor, viewer)
- `Permission`: id, permission_name (e.g., read, write, delete)
- `UserRole`: user_id, role_id (many-to-many)
- `RolePermission`: role_id, permission_id (many-to-many)

**Access check flow:**
```
User → UserRole → Role → RolePermission → Permission
```

This separation allows adding new roles or changing permissions without modifying user records or application code.

# 13. Libraries


## 13.1 Lodash

## Array Utilities

| Function | Description | Example |
|----------|-------------|---------|
| `_.chunk(arr, size)` | Split into chunks of `size` | `_.chunk([1,2,3,4], 2)` → `[[1,2],[3,4]]` |
| `_.compact(arr)` | Remove falsy values | `_.compact([0,1,false,2,'',3])` → `[1,2,3]` |
| `_.difference(arr, values)` | Elements in `arr` not in `values` | `_.difference([2,1],[2,3])` → `[1]` |
| `_.drop(arr, n)` | Remove first `n` elements | `_.drop([1,2,3], 2)` → `[3]` |
| `_.flatten(arr)` | Flatten one level | `_.flatten([1,[2,[3]]])` → `[1,2,[3]]` |
| `_.flattenDeep(arr)` | Flatten recursively | `_.flattenDeep([1,[2,[3]]])` → `[1,2,3]` |
| `_.uniq(arr)` | Remove duplicates | `_.uniq([1,1,2,3,3])` → `[1,2,3]` |
| `_.intersection(a, b)` | Common elements | `_.intersection([1,2],[2,3])` → `[2]` |

## Collection Utilities

| Function | Description |
|----------|-------------|
| `_.filter(col, predicate)` | Keep elements where predicate is truthy |
| `_.find(col, predicate)` | First matching element |
| `_.map(col, iteratee)` | Transform each element |
| `_.reduce(col, iteratee, acc)` | Reduce to single value |
| `_.groupBy(col, iteratee)` | Group by key |
| `_.sortBy(col, iteratees)` | Sort by one or more criteria |
| `_.orderBy(col, keys, orders)` | Sort with explicit asc/desc |

## Object Utilities

| Function | Description |
|----------|-------------|
| `_.get(obj, path, default)` | Safe deep property access |
| `_.set(obj, path, value)` | Set nested property |
| `_.merge(target, ...sources)` | Deep recursive merge |
| `_.omit(obj, paths)` | New object without specified keys |
| `_.pick(obj, paths)` | New object with only specified keys |
| `_.assign(target, ...sources)` | Shallow copy own properties |
| `_.cloneDeep(obj)` | Deep clone |

`_.get` is particularly valuable for safely accessing deeply nested properties without chaining optional chaining operators:

```javascript
const city = _.get(user, 'address.city', 'Unknown');
```

## Function Utilities

### `_.debounce(fn, wait, options)`

Delays invocation until `wait` ms after the last call. Options: `leading` (invoke on first call), `trailing` (invoke after wait), `maxWait` (maximum delay).

```javascript
const search = _.debounce(fetchResults, 300);
input.addEventListener('input', search);
```

### `_.throttle(fn, wait, options)`

Invokes at most once per `wait` ms. Options: `leading`, `trailing`.

```javascript
window.addEventListener('scroll', _.throttle(updatePosition, 100));
```

## String Utilities

| Function | Example |
|----------|---------|
| `_.camelCase('foo bar')` | `'fooBar'` |
| `_.kebabCase('fooBar')` | `'foo-bar'` |
| `_.snakeCase('fooBar')` | `'foo_bar'` |
| `_.capitalize('hello')` | `'Hello'` |
| `_.startCase('fooBar')` | `'Foo Bar'` |

## When to Use Lodash

Lodash is most valuable when:
- Working with deeply nested data structures (`_.get`, `_.set`, `_.merge`).
- Needing reliable debounce/throttle with edge options.
- Processing collections with complex transformations.

With modern JavaScript, many Lodash functions have native equivalents: `Array.prototype.flat()`, `Object.entries()`, optional chaining (`?.`), nullish coalescing (`??`). Evaluate whether native methods suffice before adding the dependency.

## 13.2 ahooks

## Overview

ahooks is a React hooks library providing production-ready hooks for common patterns: data fetching, state management, side effects, and UI interactions.

```bash
npm install ahooks
```

## Data Fetching

### `useRequest`

The core data fetching hook with built-in support for loading states, error handling, polling, debouncing, throttling, caching, retry, and pagination.

```javascript
import { useRequest } from 'ahooks';

const { data, loading, error, run } = useRequest(fetchUserData, {
  manual: false,             // auto-fetch on mount
  pollingInterval: 5000,     // poll every 5s
  debounceWait: 300,         // debounce requests
  retryCount: 3,             // retry on failure
  onSuccess: (data) => console.log(data),
  onError: (error) => console.error(error),
});
```

### `usePagination`

Extends `useRequest` for paginated data with automatic page state management.

```javascript
const { data, loading, pagination } = usePagination(fetchUsers, {
  defaultPageSize: 20,
});

// pagination.current, pagination.pageSize, pagination.total
// pagination.changeCurrent(2), pagination.changePageSize(50)
```

### `useInfiniteScroll`

Implements infinite scroll loading with threshold detection.

```javascript
const { data, loading, noMore } = useInfiniteScroll(
  (d) => fetchMoreItems(d?.nextCursor),
  { target: containerRef, threshold: 100 }
);
```

## State Hooks

### `useToggle` / `useBoolean`

```javascript
const [state, { toggle, setTrue, setFalse }] = useBoolean(false);
```

`useToggle` generalizes to any two values (not just booleans).

### `useMap` / `useSet`

State management for Map and Set data structures with convenient mutation methods.

```javascript
const [map, { set, remove, reset }] = useMap([['key1', 'value1']]);
set('key2', 'value2');
remove('key1');
```

### `useLocalStorageState`

State that automatically syncs with localStorage, handling serialization and error cases.

```javascript
const [theme, setTheme] = useLocalStorageState('theme', {
  defaultValue: 'light',
});
```

### `useLatest`

Returns a ref that always holds the latest value, solving stale closure issues in `setInterval` and `setTimeout` callbacks.

```javascript
const latestCount = useLatest(count);

useEffect(() => {
  const timer = setInterval(() => {
    console.log(latestCount.current); // always up-to-date
  }, 1000);
  return () => clearInterval(timer);
}, []);
```

## Performance Hooks

### `useMemoizedFn`

Like `useCallback` but without a dependency array. Returns a stable function reference that always calls the latest version of the function.

```javascript
const handleClick = useMemoizedFn(() => {
  console.log(count); // always reads latest count
});
```

Compared to `useCallback`: no dependency array means no stale closure bugs and no need to list dependencies.

### `useCreation`

A more reliable `useMemo` that guarantees referential stability and never recalculates unnecessarily.

### `useVirtualList`

Virtualizes long lists for performance, rendering only visible items.

```javascript
const { list, containerProps, wrapperProps, scrollTo } = useVirtualList(
  originalList,
  { itemHeight: 50, overscan: 5 }
);
```

## Lifecycle Hooks

### `useMount` / `useUnmount`

Cleaner alternatives to `useEffect` for mount-only or unmount-only logic.

```javascript
useMount(() => { console.log('mounted'); });
useUnmount(() => { console.log('unmounted'); });
```

### `useDebounce` / `useDebounceFn`

```javascript
const debouncedValue = useDebounce(searchTerm, { wait: 300 });
const { run: debouncedSearch } = useDebounceFn(search, { wait: 300 });
```

### `useThrottle`

```javascript
const throttledValue = useThrottle(scrollPosition, { wait: 100 });
```

## Dynamic Lists

### `useDynamicList`

Manages ordered lists with immutable operations and stable keys for rendering.

```javascript
const { list, push, remove, move, insert, getKey } = useDynamicList([
  { name: 'Alice' },
  { name: 'Bob' },
]);
```

Each item receives a stable key via `getKey(index)`, solving the key management problem for dynamic forms and sortable lists.

# 14. Professional Skills


## 14.1 Interview Tips

## Discussing Strengths and Weaknesses

### Strengths

Focus on qualities directly relevant to the role. Back each strength with a concrete example:

- "I'm detail-oriented -- in my last project, I caught a data race condition during code review that would have caused intermittent production failures."
- "I learn quickly -- I picked up TypeScript and implemented it across our codebase within two weeks of joining."

### Weaknesses

Choose genuine weaknesses that don't conflict with core job requirements, and show how you're addressing them:

- "I sometimes spend too long optimizing code before shipping. I've learned to set time-boxed goals and ship iteratively."
- "I'm not as experienced with backend systems, but I've been building side projects with Node.js to broaden my skills."

Avoid cliche answers like "I'm a perfectionist" or "I work too hard."

## Salary Expectations

- Research market rates for your role, level, and location before the interview.
- Express genuine interest in the role and team first: "I'm most interested in the technical challenges and growth opportunities."
- Provide a range rather than a fixed number: "Based on my research and experience, I'm looking at X–Y, but I'm open to discussion based on the full compensation package."
- If pressed early, it's acceptable to say: "I'd prefer to understand the role better before discussing numbers."

## "Why Are You a Good Fit?"

Structure your answer around three pillars:

1. **Skills match**: Map your technical skills to their requirements.
2. **Experience alignment**: Describe relevant projects and outcomes.
3. **Cultural fit**: Show understanding of their product, mission, or engineering culture.

"Your team is building a high-traffic React application with a focus on performance. I've spent the last two years optimizing rendering performance and implementing virtual scrolling at scale, which directly aligns with your challenges."

## Company Research

Show you've done your homework:

- Understand the company's product, market position, and recent developments.
- Connect your skills to their specific needs.
- If you're less familiar, be honest: "I've read about your recent launch of X. I'd love to learn more about the technical stack behind it."

## Addressing Lack of Experience

- Acknowledge that experience matters, then pivot to your strengths.
- Emphasize transferable skills, learning ability, and concrete examples of rapid ramp-up.
- "While I haven't worked with GraphQL in production, I've built several projects with it and understand the patterns. I'm confident I can be productive within the first sprint."

## Questions to Ask the Interviewer

**About the role:**
- "What does a typical day look like for someone in this role?"
- "What are the biggest technical challenges the team is facing right now?"
- "How do you measure success for this position in the first 6 months?"

**About the team:**
- "What's the team's approach to code review and knowledge sharing?"
- "How are technical decisions made -- is it top-down or consensus-driven?"

**About growth:**
- "What learning and development opportunities are available?"
- "What does the career progression path look like for engineers here?"

## Closing the Interview

- Thank the interviewer for their time and the conversation.
- Reiterate your interest: "This conversation has reinforced my excitement about the role. I'd love the opportunity to contribute to the team."
- Ask about next steps: "What does the rest of the process look like?"

## 14.2 Agile and Scrum

## Agile Development

### Core Principles

Agile is a development methodology focused on iterative delivery, continuous feedback, and adaptability. Key principles from the Agile Manifesto:

- **Working software** over comprehensive documentation.
- **Customer collaboration** over contract negotiation.
- **Responding to change** over following a rigid plan.
- **Individuals and interactions** over processes and tools.

### Agile in Practice

- Deliver working software in short iterations (1-4 weeks).
- Welcome changing requirements, even late in development.
- Business and development teams work together daily.
- Build projects around motivated individuals and trust them to deliver.
- Maintain a sustainable development pace.
- Regularly reflect and adjust processes.

### Benefits

- **Flexibility**: Adapt to changing requirements without derailing the project.
- **Quality**: Frequent testing and integration catch issues early.
- **Visibility**: Regular demos and retrospectives keep stakeholders informed.
- **Reduced risk**: Short iterations mean problems surface quickly.

## Scrum Framework

Scrum is the most widely used Agile framework. It defines roles, events, and artifacts for organizing iterative work.

### Roles

#### Product Owner
- Defines and prioritizes the product backlog.
- Represents stakeholder interests.
- Decides what to build and in what order.

#### Scrum Master
- Facilitates the Scrum process and removes impediments.
- Coaches the team on Scrum practices.
- Shields the team from external interruptions.
- Does **not** manage the team -- the team is self-organizing.

#### Development Team
- Cross-functional group that designs, builds, and tests the product.
- Typically 3-9 people.
- Self-organizing: the team decides how to accomplish sprint goals.

### Events

#### Sprint
A fixed time-box (usually 2 weeks) during which a potentially shippable increment is created.

#### Sprint Planning
The team selects backlog items for the sprint and breaks them into tasks. Outcome: a sprint goal and a sprint backlog.

#### Daily Standup
A 15-minute daily meeting where each member answers:
1. What did I do yesterday?
2. What will I do today?
3. Are there any blockers?

#### Sprint Review
End-of-sprint demo to stakeholders. Gather feedback and update the product backlog accordingly.

#### Sprint Retrospective
The team reflects on the sprint process:
- What went well?
- What could be improved?
- What actions will we take?

### Artifacts

- **Product Backlog**: Ordered list of everything needed in the product.
- **Sprint Backlog**: Items selected for the current sprint plus the plan for delivering them.
- **Increment**: The sum of all completed backlog items, in a usable state.

### Common Challenges

- **Scope creep**: Adding items mid-sprint undermines the sprint commitment. Use the backlog for new requests.
- **Resistance to change**: Teams accustomed to waterfall may struggle with iterative planning. Start with pilot teams and demonstrate results.
- **Skipping retrospectives**: Without reflection, the same problems recur. Retrospectives are not optional.

## 15.1 Frontend Testing

## 15.1 Frontend Testing

### 1. Testing Pyramid

The testing pyramid describes the ideal distribution of tests: many unit tests at the base, fewer integration tests in the middle, and fewest end-to-end tests at the top.

| Level | Count | Scope | Tools |
|-------|-------|-------|-------|
| **Unit** | Most | Single function/component in isolation | Jest, Vitest |
| **Integration** | Middle | Multiple units working together | Jest + RTL, Vitest + Testing Library |
| **E2E** | Fewest | Full app in real browser | Playwright, Cypress, Puppeteer |

- **Unit tests**: Fast, cheap, isolate logic. Test pure functions, utilities, individual component behavior.
- **Integration tests**: Verify components interact correctly with hooks, context, API mocks.
- **E2E tests**: Slow, expensive, catch real user flows. Use sparingly for critical paths.

---

### 2. Jest Fundamentals

#### describe, it/test

```javascript
describe('Calculator', () => {
  it('adds two numbers', () => {
    expect(1 + 2).toBe(3);
  });

  test('subtracts two numbers', () => {
    expect(5 - 3).toBe(2);
  });
});
```

`describe` groups tests; `it` and `test` are interchangeable.

#### Common Matchers

| Matcher | Use Case |
|---------|----------|
| `toBe(value)` | Strict equality (`===`). Use for primitives. |
| `toEqual(value)` | Deep equality. Use for objects/arrays. |
| `toBeTruthy()` / `toBeFalsy()` | Boolean coercion |
| `toBeNull()` / `toBeUndefined()` | Null/undefined checks |
| `toThrow()` / `toThrow(error)` | Exception assertion |
| `toContain(item)` | Array/string contains |
| `toHaveLength(n)` | Array/string length |
| `toMatch(regex)` | String matches regex |
| `toBeGreaterThan(n)` / `toBeLessThan(n)` | Number comparison |

```javascript
expect(2 + 2).toBe(4);
expect({ a: 1 }).toEqual({ a: 1 });
expect([1, 2, 3]).toContain(2);
expect(() => fn()).toThrow('error message');
```

#### Setup and Teardown

```javascript
describe('Database', () => {
  beforeAll(() => {
    // Run once before all tests in this block
  });

  afterAll(() => {
    // Run once after all tests
  });

  beforeEach(() => {
    // Run before each test
  });

  afterEach(() => {
    // Run after each test
  });
});
```

---

### 3. Mocking in Jest

#### jest.fn()

Creates a mock function. Tracks calls and return values.

```javascript
const mockFn = jest.fn();
mockFn(1, 2);
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledWith(1, 2);
expect(mockFn).toHaveBeenCalledTimes(1);

// Custom return
mockFn.mockReturnValue(42);
expect(mockFn()).toBe(42);
```

#### jest.mock()

Mocks an entire module. Hoisted to top of file.

```javascript
jest.mock('./api');

import { fetchUser } from './api';

test('uses mocked fetchUser', async () => {
  fetchUser.mockResolvedValue({ id: 1, name: 'Alice' });
  const user = await fetchUser();
  expect(user.name).toBe('Alice');
});
```

#### jest.spyOn()

Spies on an existing method without replacing the module. Can restore with `mockRestore()`.

```javascript
const spy = jest.spyOn(console, 'log').mockImplementation(() => {});
// ... test
spy.mockRestore();
```

#### Async Mocks

```javascript
const mockFetch = jest.fn();

mockFetch.mockResolvedValue({ data: 'success' });
mockFetch.mockRejectedValue(new Error('Network error'));

// For multiple calls
mockFetch
  .mockResolvedValueOnce({ page: 1 })
  .mockResolvedValueOnce({ page: 2 });
```

---

### 4. React Testing Library (RTL)

#### Philosophy

Test from the user's perspective: what they see and do. Avoid testing implementation details (state, props, internal methods).

#### Core API

```jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

render(<MyComponent />);

// Queries
screen.getByText('Submit');        // Throws if not found
screen.queryByText('Optional');    // Returns null if not found
screen.findByText('Async');        // Returns promise, waits for element
screen.getByRole('button', { name: /submit/i });
screen.getByTestId('custom-id');   // Last resort
```

#### Query Priority

1. `getByRole` — accessibility, user-facing
2. `getByLabelText` — forms
3. `getByPlaceholderText` — forms
4. `getByText` — non-interactive content
5. `getByDisplayValue` — form values
6. `getByAltText` — images
7. `getByTitle` — title attribute
8. `getByTestId` — when above fail

#### User Interactions

Prefer `userEvent` over `fireEvent` — simulates real user behavior (e.g., proper event order).

```jsx
import userEvent from '@testing-library/user-event';

// userEvent (preferred)
await userEvent.click(screen.getByRole('button'));
await userEvent.type(screen.getByLabelText('Email'), 'test@example.com');

// fireEvent (lower-level)
fireEvent.click(button);
fireEvent.change(input, { target: { value: 'text' } });
```

#### Async Utilities

```jsx
import { waitFor, findByRole } from '@testing-library/react';

// waitFor — retries until assertion passes or timeout
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});

// findBy* — shorthand for waitFor + getBy
const button = await screen.findByRole('button', { name: 'Submit' });
```

#### Example: Form Submission

```jsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm';

test('submits form with email and password', async () => {
  const onSubmit = jest.fn();
  render(<LoginForm onSubmit={onSubmit} />);

  await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
  await userEvent.type(screen.getByLabelText(/password/i), 'secret123');
  await userEvent.click(screen.getByRole('button', { name: /submit/i }));

  await waitFor(() => {
    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'secret123',
    });
  });
});
```

---

### 5. Testing Patterns

#### Arrange-Act-Assert (AAA)

Structure tests in three clear phases:

```jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('increments counter', async () => {
  // Arrange
  render(<Counter />);
  const button = screen.getByRole('button', { name: /increment/i });

  // Act
  await userEvent.click(button);

  // Assert
  expect(screen.getByText('1')).toBeInTheDocument();
});
```

#### Testing Async Operations

```jsx
import { render, screen } from '@testing-library/react';

test('loads user data', async () => {
  jest.spyOn(api, 'fetchUser').mockResolvedValue({ name: 'Alice' });

  render(<UserProfile userId={1} />);

  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  const name = await screen.findByText('Alice');
  expect(name).toBeInTheDocument();
});
```

#### Testing Custom Hooks with renderHook

```javascript
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

test('increments counter', () => {
  const { result } = renderHook(() => useCounter(0));

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});
```

#### Snapshot Testing

**When to use**: Stable UI components, regression for layout/structure.

**When not to use**: Frequently changing UI, large snapshots, testing behavior.

```jsx
import { render } from '@testing-library/react';

test('matches snapshot', () => {
  const { container } = render(<Header />);
  expect(container).toMatchSnapshot();
});
```

Prefer explicit assertions over snapshots when testing behavior. Update snapshots intentionally with `jest -u`.

## 16.1 Git Essentials

## Git Essentials

### Core Commands

| Command | Purpose |
|---|---|
| `git init` | Initialize a new repository |
| `git clone <url>` | Clone a remote repository |
| `git add <file>` | Stage changes (`git add .` for all) |
| `git commit -m "msg"` | Commit staged changes |
| `git status` | Show working tree status |
| `git log --oneline` | Compact commit history |
| `git diff` | Unstaged changes (`--staged` for staged) |

### Remote Operations

```bash
git remote add origin <url>
git push -u origin main        # first push, sets upstream
git push                       # subsequent pushes
git pull                       # fetch + merge
git fetch                      # download without merging
```

`git pull` = `git fetch` + `git merge`. Use `git fetch` when you want to inspect remote changes before integrating them.

### Branching

```bash
git branch feature/login       # create branch
git checkout feature/login     # switch to branch
git checkout -b feature/login  # create + switch (shorthand)
git switch -c feature/login    # modern alternative to checkout -b
git branch -d feature/login    # delete branch (safe — prevents deleting unmerged)
git branch -D feature/login    # force delete
```

#### Branching Strategies

**Feature Branches**: Each feature/bugfix gets its own branch off `main`. Merged back via PR.

**Git Flow** (simplified):
- `main` — production-ready code
- `develop` — integration branch
- `feature/*` — new features branch off `develop`
- `hotfix/*` — urgent fixes branch off `main`

### Merge vs Rebase

#### `git merge`

Combines branches by creating a **merge commit** that ties the two histories together. Non-destructive — original branch history is preserved.

```bash
git checkout main
git merge feature/login
```

```
A---B---C  (main)
     \       \
      D---E   M  (merge commit)
```

#### `git rebase`

Replays commits from one branch **on top of** another, creating a linear history. Rewrites commit hashes.

```bash
git checkout feature/login
git rebase main
```

```
A---B---C  (main)
         \
          D'---E'  (feature/login, rebased)
```

#### When to Use Each

| Scenario | Use |
|---|---|
| Merging a feature branch into `main` via PR | `merge` (preserves context) |
| Updating a feature branch with latest `main` | `rebase` (keeps history clean) |
| Shared/public branches | `merge` (never rebase shared branches) |
| Local-only branches | `rebase` (cleaner log) |

**Golden rule**: never rebase commits that have been pushed and shared with others.

### Resolving Merge Conflicts

When Git can't auto-merge, it marks conflicts in the file:

```
<<<<<<< HEAD
const timeout = 3000;
=======
const timeout = 5000;
>>>>>>> feature/login
```

Steps:
1. Open conflicted files, choose the correct code (or combine both)
2. Remove the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
3. `git add <file>` to mark as resolved
4. `git commit` (or `git rebase --continue` if rebasing)

### Useful Commands

#### `git stash`

Temporarily shelves uncommitted changes.

```bash
git stash                  # stash changes
git stash list             # see all stashes
git stash pop              # apply most recent stash and remove it
git stash apply            # apply without removing
git stash drop             # discard most recent stash
```

#### `git cherry-pick`

Apply a specific commit from another branch onto the current branch.

```bash
git cherry-pick <commit-hash>
```

#### `git reset` vs `git revert`

| | `git reset` | `git revert` |
|---|---|---|
| **What it does** | Moves HEAD backward, discarding commits | Creates a new commit that undoes a previous one |
| **History** | Rewrites history (destructive) | Preserves history (safe) |
| **Use case** | Undo local, unpushed commits | Undo a commit that's already pushed |

```bash
git reset --soft HEAD~1    # undo commit, keep changes staged
git reset --mixed HEAD~1   # undo commit, keep changes unstaged (default)
git reset --hard HEAD~1    # undo commit, discard all changes

git revert <commit-hash>   # create a new "undo" commit
```

#### `git reflog`

Shows a log of all HEAD movements — useful for recovering from accidental `reset --hard` or deleted branches.

```bash
git reflog
git checkout <lost-commit-hash>
```

### PR / Code Review Workflow

1. Create a feature branch from `main`
2. Make commits with clear, descriptive messages
3. Push the branch and open a Pull Request
4. Reviewers comment, request changes, or approve
5. Address feedback with new commits (avoid force-pushing during review)
6. Squash-merge or merge into `main`
7. Delete the feature branch

#### Commit Message Conventions

```
type(scope): short description

feat(auth): add JWT token refresh
fix(api): handle 404 in user endpoint
refactor(utils): extract date formatting
docs(readme): update setup instructions
```

Common types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`.
