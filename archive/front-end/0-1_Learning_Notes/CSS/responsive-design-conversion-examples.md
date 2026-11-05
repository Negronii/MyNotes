# How can a fixed design be adapted to different viewport widths? / 如何让固定设计适配不同视口宽度？

This archived example uses media queries, a root-font-size scale for `rem`, and a pixel-to-viewport-width formula. It is one design-system strategy: choose the scaling rule from the product's layout constraints and preserve user zoom and readable text sizes. / 本归档示例用媒体查询、基于根字号的 `rem` 比例以及像素到视口宽度的换算公式。它只是设计系统的一种策略；应根据产品布局约束选择缩放方式，并保留用户缩放和可读字号。

## Responsive Website Development

## Media Queries

Media queries allow us to apply different CSS styles based on the characteristics of the user's device, such as its screen width, height, orientation, and resolution. This enables us to create responsive designs that adapt to different screen sizes and devices.

**Syntax**

The basic syntax for a media query is as follows:

```css
@media (media-feature) {
    selector {
        property: value;
    }
}
```

**Example**

```css
@media (width: 320px) {
    html {
        font-size: 32px;
    }
}
```

In this example, when the viewport width is exactly 320px, the font size of the `html` element is set to 32px.

### Common Media Features

1. **Width and Height:**
   ```css
   @media (max-width: 768px) {
       body {
           background-color: pink;
       }
   }

   @media (min-width: 1200px) {
       body {
           background-color: skyblue;
       }
   }
   ```
   - `max-width`: Applied when the viewport width is less than or equal to the specified value.
   - `min-width`: Applied when the viewport width is greater than or equal to the specified value.

2. **Orientation:**
   ```css
   @media (orientation: portrait) {
       body {
           font-size: 18px;
       }
   }

   @media (orientation: landscape) {
       body {
           font-size: 16px;
       }
   }
   ```
   - `orientation`: Determines whether the device is in portrait or landscape mode.

3. **Resolution:**
   ```css
   @media (min-resolution: 2dppx) {
       .icon {
           background-image: url("icon@2x.png");
       }
   }
   ```
   - `min-resolution`: Applied for devices with a minimum resolution.

### Responsive Font Size

This media-query example sets one size at and above a threshold; it does not scale proportionally with viewport width. For bounded fluid scaling, use a relative expression such as `clamp()` and test text zoom and narrow screens.

```css
@media (min-width: 375px) {
    html {
        font-size: 37.5px;
    }
}
```

At 375px and wider, this rule sets the root size to 37.5px. A fixed value at a minimum-width breakpoint is a step change, not continuous viewport scaling.

## Example of a Responsive Website

Using media queries to apply different background colors based on the viewport width:

```css
@media (min-width: 768px) {
    body {
        background-color: pink;
    }
}

@media (min-width: 992px) {
    body {
        background-color: green;
    }
}

@media (min-width: 1200px) {
    body {
        background-color: skyblue;
    }
}
```

**Explanation:**

- **Below 768px:** The `body` element has a default background color (e.g., white).
- **768px to 991px:** The `body` element has a pink background color.
- **992px to 1199px:** The `body` element has a green background color.
- **1200px and above:** The `body` element has a sky blue background color.

## Full Media Query Structure

A full media query consists of the `@media` keyword, media type, and media feature:

```css
@media media-type and (media-feature) {
    css-code
}
```

### Media Types

- `screen`: Used for computer screens, tablets, smartphones, etc.
- `print`: Used for printers.
- `speech`: Speech output media; it does not mean “screen reader.” Screen readers are assistive technology, not a media type.
- `all`: Suitable for all devices.

### Media Features

- `width`, `height`, `max-width`, `min-width`, `max-height`, `min-height`
- `orientation` (portrait or landscape)
- `resolution`, `aspect-ratio`, `color`, `color-index`, `monochrome`

## Linking Different CSS Files Based on Screen Width

You can link different CSS files for different screen widths using the `media` attribute in the `link` element:

```html
<link rel="stylesheet" href="styles-768.css" media="(min-width: 768px)">
<link rel="stylesheet" href="styles-992.css" media="(min-width: 992px)">
<link rel="stylesheet" href="styles-1200.css" media="(min-width: 1200px)">
```

**Explanation:**

- `styles-768.css` is applied when the viewport width is 768px or wider.
- `styles-992.css` is applied when the viewport width is 992px or wider.
- `styles-1200.css` is applied when the viewport width is 1200px or wider.

**Notes:**

- Media features should be written directly within parentheses.
- Quote attribute values that contain spaces; the shown media value can also be written with single quotes or, where valid HTML syntax permits, without quotes.

## Best Practices

1. **Mobile-First Approach:**
   - Write base styles for small screens first, and use media queries to add styles for larger screens.
   - Example:
     ```css
     body {
         font-size: 16px;
     }

     @media (min-width: 768px) {
         body {
             font-size: 18px;
         }
     }

     @media (min-width: 1200px) {
         body {
             font-size: 20px;
         }
     }
     ```

2. **Use Relative Units:**
   - Use relative units like `em`, `rem`, `%`, and `vh`/`vw` for more flexible and scalable designs.
   - Example:
     ```css
     .container {
         width: 80%;
         padding: 2rem;
     }
     ```

3. **Test Across Devices:**
   - Test your website on different devices and screen sizes to ensure it looks good and functions well on all of them.

4. **Performance Optimization:**
   - Minimize CSS file size and avoid using too many media queries.
   - Use CSS preprocessors like SASS or LESS to manage complex responsive designs more effectively.


## CSS Units and Responsive Design

## REM - Relative Unit

- **REM (Root EM):** A scalable unit in CSS used for type and spacing.
  - 1rem = Computed value of `font-size` of the root element (`<html>`).
  - Allows for scalable and consistent sizing across elements.

### Setting the Root Font Size
- Example:
  ```css
  html {
      font-size: 20px;
  }
  ```
  - All rem units will be relative to this computed root size. For instance, `2rem` is 40 CSS px here. A fixed pixel root size can limit user text-size preferences, so many sites leave the root size at its browser default.

### Usage in CSS
- Example:
  ```css
  .box {
      width: 5rem;  /* Equivalent to 100px if root font-size is 20px */
      height: 5rem; /* Equivalent to 100px if root font-size is 20px */
  }
  ```

**Advantages:**
- **Scalability:** Changing the root font size scales all rem-based elements proportionally.
- **Consistency:** Ensures a consistent design across different devices and resolutions.

## VW/VH - Viewport Units

### Definition and Usage
- **Viewport Width (vw) and Viewport Height (vh):**
  - `1vw` = 1% of the viewport width.
  - `1vh` = 1% of the large viewport height in current viewport-unit definitions. On mobile, browser UI can change the visible area; `svh`, `lvh`, or `dvh` can express the intended viewport size more directly.

**Example:**
  ```css
  .box {
      width: 50vw;  /* 50% of the viewport width */
      height: 30vh; /* 30% of the viewport height */
  }
  ```

**Advantages:**
- **Direct Responsiveness:** Automatically adjusts to the size of the viewport without additional media queries.
- **Flexibility:** Ideal for full-screen layouts and elements that need to scale directly with the viewport.

## PX to VW Conversion in Design

1. **Determine VW Size:**
   - If the design width is 1000px, 1vw would be 10px.
2. **Calculate VW Value:**
   - Formula: `(Value in px) / (Viewport width / 100)`
   - Example: For a 200px element in a 1000px viewport:
     ```css
     .element {
         width: 20vw;  /* 200px / (1000px / 100) = 20vw */
     }
     ```

**See also / 另见：** [HTML and CSS Basics / HTML 与 CSS 基础](../../../../frontend/html-css/html-and-css-basics.md) for modern responsive units and container-driven options.
