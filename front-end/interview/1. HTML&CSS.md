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

This example demonstrates responsive typography using rem units and media queries. The base font size is set on the `html` element, which the `rem` units reference. Media queries adjust the base font size for smaller screens, affecting all elements using `rem`. The `p` (paragraph) styling is also adjusted for smaller screens to ensure readability.

## Box Model Explanation

The CSS box model is a fundamental concept in web development that describes how the dimensions of each HTML element are calculated. The components of the box model, from outer to inner, are:

1. **Margin**: The outermost layer, which defines the space between the element's border and surrounding elements.
2. **Border**: The border that surrounds the padding and content. It's the boundary between the margin and the padding.
3. **Padding**: The space between the border and the content. It increases the space inside the element.
4. **Content**: The innermost area where the actual text, images, or other media are displayed.
5. **Box-sizing**: A property that determines how the width and height of an element are calculated. If set to `border-box`, the element's padding and border are included in the element's width and height. If set to `content-box`, the width and height only include the content, not the padding or border. 

## Differences Between offsetHeight, scrollHeight, and clientHeight

1. **offsetHeight**: The `offsetHeight` property measures the total visible height of an element, including padding, border, and the scroll bar on the element (if any), but excluding margins. It's the outermost height measurement that includes everything inside the margin.

2. **clientHeight**: The `clientHeight` property measures the visible content area (including padding) of an element but excludes the border, scrollbar, and margin. It's useful for getting the actual area available for the content inside an element.

3. **scrollHeight**: The `scrollHeight` property measures the total height of an element's content, including content not visible on the screen due to overflow. It includes padding but excludes borders, scrollbar, and margin. This is larger than the `clientHeight` if there's content that overflows outside the visible area.

### Sample Answer
The primary differences among `offsetHeight`, `scrollHeight`, and `clientHeight` relate to what they include in their calculations. `offsetHeight` includes the border, padding, and the vertical scrollbar (if present), making it the total outer height. `clientHeight` includes the padding and the viewable content height, but not the border or scrollbar. Lastly, `scrollHeight` measures the total height of the content, including what's not visible due to overflow, plus padding. These properties are essential for dynamically managing layouts, handling scrolling behavior, or adjusting elements based on their content size.

## Retina Screen and 1px Lines Implementation

When designing for Retina displays, setting elements to 1px using CSS can result in lines that appear too thick, due to some mobile phones having a Device Pixel Ratio (DPR) of 2. This means 1 CSS pixel could use 2 physical pixels, making the line appear thicker than intended. Directly setting elements to 0.5px can lead to compatibility issues across different browsers. To achieve the desired 1px line appearance on Retina screens, we can use CSS pseudo-elements combined with the `transform` property for optimization. 

Here's an improved and corrected example:

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

## What is the difference between `defer` and `async` attributes in `<script>` elements?

The `<script>` element can be used to include JavaScript in HTML documents. When scripts are loaded and executed, they can affect how quickly a page becomes interactive. The `defer` and `async` attributes provide different ways to control this behavior.

### `defer`
The `defer` attribute tells the browser to continue parsing the HTML document while the script is being downloaded asynchronously. The key point is that the script execution is deferred until the entire HTML document has been parsed. This means that scripts with `defer` will not run until the HTML parsing is complete, which is similar to placing a `<script>` tag at the end of the `<body>` element. However, `defer` ensures that scripts are executed in the order they appear in the document, which is not guaranteed when scripts are manually placed at the bottom of the `<body>`. 

### `async`
The `async` attribute also allows the script to be downloaded in parallel to HTML parsing. However, unlike `defer`, `async` scripts are executed as soon as they are downloaded, which could be before or after the HTML parsing is complete. This means the execution order of scripts is not guaranteed. `async` is best used for scripts that do not depend on other scripts and do not modify the DOM (Document Object Model).

### Difference between Prefetch and DNS-Prefetch

#### Prefetch and Preload
- **Preload** is a directive used to instruct the browser to load a resource early in the page's lifecycle, because it will be needed soon. This is crucial for resources that are critical to the current page's content, ensuring they are loaded with higher priority. The syntax is `<link rel="preload" href="example.js" as="script">` (or as="style" for CSS files), indicating that the resource is important for the immediate page load.
- **Prefetch** is a hint to the browser that a resource might be needed in the future, but not on the current page. Resources prefetched are fetched and stored in the cache with low priority, during idle browser time, making them faster to load on subsequent page visits. The syntax is `<link rel="prefetch" href="example.js" as="script">`, suggesting the resource may be used in subsequent pages or actions.

#### DNS-Prefetch and Preconnect
- **DNS-Prefetch** is a way to resolve domain names (DNS lookups) before a user clicks on a link. This process reduces latency when the user navigates to the linked resource, as the DNS resolution step is already completed. The syntax for using it is `<link rel="dns-prefetch" href="//example.com">`. It's especially useful for third-party resources or any links that lead to different domains.
- **Preconnect** goes a step further than DNS-prefetch by not only resolving the domain name but also performing the TCP handshake and, if the protocol is HTTPS, the TLS negotiation. This fully prepares the browser for a future connection, reducing the connection establishment time. The syntax is `<link rel="preconnect" href="//example.com">`. Preconnect is more comprehensive than DNS-prefetch because it completes all the preliminary network steps, making the resource ready to be used with minimal delay.

### Summary
- Use **preload** for critical resources needed for the current page to ensure they are loaded quickly and with high priority.
- Use **prefetch** for resources that will be needed in subsequent page visits, to speed up their load time when the user navigates to those pages.
- Use **dns-prefetch** to resolve domain names ahead of time, reducing DNS lookup time for third-party resources or anticipated navigations.
- Use **preconnect** to fully prepare for a future connection, including DNS lookup, TCP handshake, and TLS negotiation, minimizing the latency for high-priority, cross-origin requests.

## How to handle text Overflow with Ellipsis in CSS? 

When working with web design and front-end development, managing text overflow elegantly ensures that the UI remains clean and user-friendly even when content exceeds its container's bounds. CSS provides mechanisms to handle single-line and multi-line text overflow scenarios, allowing text that doesn't fit in its container to be truncated and represented with an ellipsis (`...`). Here's how to achieve this:

### Single-line Text Overflow

For single-line text overflow, where you want text that exceeds the width of its container to end with an ellipsis, you can use the following CSS properties:

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

### Multi-line Text Overflow

Handling text overflow for multi-line scenarios, where you want to limit the text to a specific number of lines and display an ellipsis for overflow text, involves a bit more CSS, particularly leveraging webkit-specific properties:

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

## CSS Layout: Flexbox Solution for a Responsive Three-Div Setup

### Scenario Description
You have a large `div` element that contains three smaller `div` elements. The goal is to position these three child `div`s side by side — left, center, and right within the parent `div`. The left and right `div`s have a fixed width, while the center `div` should automatically adjust its width to occupy all remaining space.

### Solution and Explanation

To achieve this layout, you can use CSS Flexbox. Flexbox provides an efficient way to distribute space and align items within a container, even when their size is unknown or dynamic.

Here is a step-by-step guide to implement the described layout:

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

### Complete CSS Example

```css
.parent {
    display: flex;
}

.left, .right {
    width: 100px; /* Fixed width */
}

.center {
    flex-grow: 1; /* Occupies the remaining space */
}
```

### HTML Structure

```html
<div class="parent">
    <div class="left">Left</div>
    <div class="center">Center</div>
    <div class="right">Right</div>
</div>
```

### Key Takeaways

- **Flexbox** is a powerful layout tool in CSS that allows you to design complex layouts easily and responsively.
- The `flex-grow` property on a flex item allows it to expand and fill available space in a flex container, which is perfect for adaptive layouts.
- Setting the `display` property of a container to `flex` initiates a flex context, which then enables the use of Flexbox properties on its child elements.
