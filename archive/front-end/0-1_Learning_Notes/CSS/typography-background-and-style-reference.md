# Which CSS properties control text, backgrounds, and common visual details? / 哪些 CSS 属性用于控制文字、背景和常见视觉效果？

This compact catalog preserves the archived property examples for font, text, background, and common visual declarations. Use it as a lookup; for selectors, units, and responsive design concepts, see [HTML and CSS Basics / HTML 与 CSS 基础](../../../../frontend/html-css/html-and-css-basics.md). / 本页保留归档中的字体、文本、背景和常见视觉属性示例，适合作为查询表；选择器、单位和响应式设计见[HTML 与 CSS 基础](../../../../frontend/html-css/html-and-css-basics.md)。

## Font Properties

## Font Size

### Property: `font-size`
- **Value:** `<number>px`, `<number>em`, `<number>rem`
- **Example:**
  ```css
  p {
      font-size: 30px;
  }
  ```
- **Default Value:** Many user-agent defaults are 16 CSS px, but the user's settings and browser defaults can differ; `1rem` follows the root element's computed size.
- **Best Practices:**
  - Use relative units like `em` or `rem` for responsive design.
  - **Example:**
    ```css
    p {
        font-size: 1.5rem;
    }
    ```
  - `em` is relative to the font-size of the parent element.
  - `rem` is relative to the font-size of the root element (`<html>`).

## Font Weight

### Property: `font-weight`
- **Value:**
  - Keywords: `normal`, `bold`
  - Numeric: `1` to `1000`; many common font faces expose weights in 100-step increments.
- **Examples:**
  ```css
  p {
      font-weight: normal; /* equivalent to 400 */
      font-weight: bold;   /* equivalent to 700 */
      font-weight: 700;
  }
  ```
- **Best Practices:**
  - Use numeric values for more precise control over font weight.

## Font Style

### Property: `font-style`
- **Value:** `normal`, `italic`, `oblique`
- **Example:**
  ```css
  p {
      font-style: italic;
  }
  ```

## Font Family

### Property: `font-family`
- **Value:** A list of font family names
- **Example:**
  ```css
  div {
      font-family: Arial, Helvetica, sans-serif;
  }
  ```
- **Best Practices:**
  - Provide a fallback system font.
  - Always end with a generic family name like `serif`, `sans-serif`, `monospace`.

## Font Shorthand Property

### Property: `font`
- **Value:** `font: <style> <weight> <size>/<line-height> <family>;`
- **Example:**
  ```css
  p {
      font: italic 700 16px/1.5 Arial, sans-serif;
  }
  ```
- **Best Practices:**
  - Use shorthand for concise and readable CSS.
  - Ensure all necessary values are included to avoid unexpected inheritance.

## Text Indentation

### Property: `text-indent`
- **Value:** `<number>px`, `<number>em`
- **Example:**
  ```css
  p {
      text-indent: 1em;
  }
  ```
- **Best Practices:**
  - Use `em` for responsive indentation relative to the font size.

## Text Alignment

### Property: `text-align`
- **Value:** `left`, `right`, `center`, `justify`
- **Example:**
  ```css
  div {
      text-align: center;
  }
  ```
- **Best Practices:**
  - Center text within parent containers.
  - Use `justify` for a clean, aligned appearance in blocks of text.

## Text Decoration

### Property: `text-decoration`
- **Value:** `underline`, `line-through`, `overline`, `none`
- **Example:**
  ```css
  a {
      text-decoration: none;
  }
  ```
- **Best Practices:**
  - Use for adding or removing text decorations, especially links.

## Line Height

### Property: `line-height`
- **Value:** `<number>px`, `<multiple>`
- **Example:**
  ```css
  p {
      line-height: 1.5;
  }
  ```
- **Best Practices:**
  - Use relative values (`1.5`, `2`) for better scaling across different font sizes.
  - Use the shorthand `font` property for combined settings:
    ```css
    p {
        font: italic 700 16px/2 Arial, sans-serif;
    }
    ```

## Color and Background Color

### Properties: `color`, `background-color`
- **Value:** `<color name>`, `rgb(x, y, z)`, `rgba(x, y, z, o)`, `#hex`
- **Examples:**
  ```css
  p {
      color: red;
      background-color: rgba(255, 255, 255, 0.5);
  }
  ```
- **Best Practices:**
  - Use `rgba` for adding transparency.
  - Use `hex` for consistency and compactness.

## Background Properties

## Background Image

### Property: `background-image`
- **Value:** `url('<path>')`
- **Example:**
  ```css
  div {
      background-image: url('image/car.jpg');
  }
  ```
- **Best Practices:**
  - Use images for decorative purposes, ensuring accessibility is not hindered.

## Background Gradient

### Property: `background-image`
- **Value:** `linear-gradient(color1, color2, ...)`
- **Example:**
  ```css
  div {
      background-image: linear-gradient(pink, skyblue, pink);
  }
  ```
- **Best Practices:**
  - Use gradients for smooth color transitions.
  - Implement with pseudo-elements for hover effects:
    ```css
    .box::after {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-image: linear-gradient(transparent, rgba(0,0,0,.6));
        opacity: 0;
        transition: opacity 1s;
    }
    .box:hover::after {
        opacity: 1;
    }
    ```

## Background Repeat

### Property: `background-repeat`
- **Value:** `repeat`, `no-repeat`, `repeat-x`, `repeat-y`
- **Examples:**
  ```css
  div {
      background-repeat: no-repeat;
  }
  ```

## Background Position

### Property: `background-position`
- **Value:** `left top`, `center center`, `50px 100px`
- **Examples:**
  ```css
  div {
      background-position: center;
  }
  ```

## Background Size

### Property: `background-size`
- **Value:** `cover`, `contain`, `number+px`, `percentage`
- **Examples:**
  ```css
  div {
      background-size: cover;
  }
  ```

## Background Shorthand Property

### Property: `background`
- **Syntax:** `background: <color> <image> <repeat> <position> <size>;`
- **Example:**
  ```css
  div {
      background: pink url('image1.jpg') no-repeat 50px 100px;
  }
  ```

## Other important styles

## List-style

Remove the dot at the beginning of the `li` tag:
```css
ul {
  list-style: none;
}
```
Note that CSS is added to `ul` instead of `li`.

## Attribute name: display
Attribute values: `block` (converted to block-level elements), `inline-block` (converted to inline-block elements), `inline` (converted to inline elements)
Converting to inline elements is rarely used, but the other two are commonly used.
e.g.
```css
div {
  width: 400px;
  height: 400px;
  display: inline-block;
}
```

## `input::placeholder{ }`

Control the placeholder style of the input:

## `vertical-align`

Baseline: There is a baseline for it in the layout of browser text type elements
Text Alignment Scenario: Solve the problem of vertical alignment of inline/inline-block elements
When the image and text are displayed in one line, the bottom is actually not aligned
Attribute name: `vertical-align`
Property value: `baseline` (default, baseline alignment), `top` (top alignment), `middle` (middle alignment), `bottom` (bottom alignment)
Inline block and inline-block alignment, inline-block and inline element alignment use this property

## `cursor`

Sets the style displayed when the mouse cursor is over an element
Property value: `default` (default small arrow), `pointer` (small hand, prompting the user to click), `text` (I-shaped, prompting that text can be selected), `move` (four arrows, prompting that you can move)

## `border-radius`

Scene: Make the border rounded, increase page details, and improve user experience
Property values: lengths or percentages; each corner can specify separate horizontal and vertical radii with a slash.
One value: All four corners use the same radius. e.g. `border-radius: 20px;`
Two values: top-left and bottom-right use the first value; top-right and bottom-left use the second.
Three values: top-left uses the first value; top-right and bottom-left use the second; bottom-right uses the third.
Four values: top-left, top-right, bottom-right, bottom-left. e.g. `border-radius: 10px 20px 40px 80px;`
Common scenes: draw a circle with a border and rounded corners
1. Create a square box
2. Set `border-radius: 50%;`
Common scene: draw a capsule
Create a rectangular box
2. Set `border-radius` to half the height of the box

## `overflow`

Content overflow part display effect
Overflow part: refers to the area where the content of the box exceeds the scope of the box

Property values:
- `visible` (default value, the overflow part is visible)
- `hidden` (the overflow part is invisible)
- `scroll` (creates a scroll container whether or not content currently overflows; visible scrollbar behavior varies by platform)
- `auto` (creates a scroll container and allows scrolling when needed)
- `clip` (clips overflow without creating a scroll container)

For a block box, `hidden`, `auto`, and `scroll` establish a new block formatting context; `clip` does not. `hidden` can clip shadows and menus, and `auto`/`scroll` can create scrolling, so use `display: flow-root` when the specific goal is float containment without clipping or scrolling.

## Visibility and display

Scenario: Make an element itself invisible. For example, the element is hidden after the mouse hover

Common properties:
- `visibility: hidden;` (placeholder hiding effect, not commonly used)
- `display: none;` (no placeholder hidden, commonly used)
`visibility: hidden` keeps the box's layout space; `display: none` removes the box from layout. With hidden content, also consider whether it should remain available to assistive technology and whether it can receive focus.
E.g. Mouse over to display the image
```css
img {display:none}
a:hover img {display:block}
```

## `opacity`

Element transparency; the element and its children are composited with that opacity. A value of `0` does not remove the box or automatically disable its pointer or keyboard interaction.
Scenario: Make an element transparent as a whole\
Attribute value: a number between 0 and 1, 1 means fully opaque, 0 means fully transparent\
`opacity` will make the element transparent as a whole, including its content and child elements

## `transition`

Transition - let the style of the element change slowly, often used with hover to enhance the interactive experience of the web page
Property values:
- Transition property: `all` (all transitionable properties) or a named property such as `width` (only that property).
- The duration of the transition: a time value such as `250ms` or `0.5s`.

Be careful:
- If multiple properties transition together, they can be separated by commas, e.g. `transition: width 1s, background-color 2s;`
- The transition needs to have different styles between the default state and the hover state in order to have a transition effect
- The transition property adds to the element itself that needs to be transitioned
- Put a shared transition on the base state when it should animate both on entry and on exit.
- If the transition is declared only in the hover state, it applies while entering that state; leaving it may snap back because the non-hover state has no transition declaration.
