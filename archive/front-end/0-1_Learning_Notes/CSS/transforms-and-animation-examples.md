# How do CSS transforms and animations create motion? / CSS Transform 与动画如何实现运动效果？

Transforms change an element's visual coordinate space; transitions interpolate between changed values, while keyframe animations define a sequence that can repeat and pause. The archived 3D cube and continuous-image examples below demonstrate those building blocks. / Transform 会改变元素的视觉坐标空间；transition 在属性值变化时插值，关键帧动画则定义可重复、可暂停的步骤。以下保留的 3D 立方体和连续图片示例展示这些基础。

## CSS Transforms

CSS transforms modify the visual coordinate space without changing the surrounding normal-flow layout. A non-`none` transform creates a stacking context and a containing block for absolutely and fixed-positioned descendants; it can also affect overflow. Transform lists compose into a matrix, so changing function order can change the result.

## Displacement (Translate)

- **Syntax:**
  ```css
  transform: translate(x, y);
  ```
- **Example:**
  ```css
  transform: translate(50px, 100px); /* Moves right by 50px and down by 100px */
  transform: translate(-50%, -100%); /* Moves by percentages of the transform reference box */
  ```
- **Single Axis:**
  ```css
  transform: translateX(50px); /* Moves right by 50px */
  transform: translateY(100px); /* Moves down by 100px */
  ```

## Rotation (Rotate)

- **Syntax:**
  ```css
  transform: rotate(angle);
  ```
- **Example:**
  ```css
  transform: rotate(45deg); /* Rotates 45 degrees clockwise */
  transform: rotate(-45deg); /* Rotates 45 degrees counter-clockwise */
  ```
- **Changing Transform Origin:**
  ```css
  transform-origin: center center; /* Default origin is the center */
  transform-origin: left top; /* Origin is the top-left corner */
  ```

## Scaling (Scale)

- **Syntax:**
  ```css
  transform: scale(x, y);
  ```
- **Example:**
  ```css
  transform: scale(1.5); /* Scales uniformly by 1.5 */
  transform: scale(1.5, 2); /* Scales x-axis by 1.5 and y-axis by 2 */
  ```
- **Single Axis:**
  ```css
  transform: scaleX(1.5); /* Scales x-axis by 1.5 */
  transform: scaleY(2); /* Scales y-axis by 2 */
  ```

## 3D Transformations

### Space Transformation

- **Syntax:**
  ```css
  transform: translate3d(x, y, z);
  ```
- **Example:**
  ```css
  transform: translate3d(50px, 100px, 200px); /* Moves in 3D space */
  ```

### Perspective Effect

- **Syntax:**
  ```css
  perspective: 1000px;
  ```
- **Use:** Applied to the parent element to create a perspective effect for its child elements.

### Space Rotation

- **Syntax:**
  ```css
  transform: rotateX(angle); /* Rotates around the x-axis */
  transform: rotateY(angle); /* Rotates around the y-axis */
  transform: rotateZ(angle); /* Rotates around the z-axis (same as rotate) */
  ```

### rotate3d

- **Syntax:**
  ```css
  transform: rotate3d(x, y, z, angle);
  ```
- **Example:**
  ```css
  transform: rotate3d(1, 1, 0, 45deg); /* Custom rotation axis */
  ```

## Stereoscopic Presentation (3D)

The following original example positions only front and back faces, so it is a two-sided flip-card demonstration rather than a complete six-face cube. A usable interactive version also needs keyboard-accessible controls and should not rely on hover alone.

- **Syntax:**
  ```css
  transform-style: preserve-3d;
  ```
- **Example:**
  ```html
  <style>
      .cube {
          position: relative;
          width: 200px;
          height: 200px;
          margin: 100px auto;
          transform-style: preserve-3d;
          transition: transform 2s;
      }
      .cube div {
          position: absolute;
          width: 200px;
          height: 200px;
          backface-visibility: hidden;
      }
      .cube .front {
          background-color: skyblue;
          transform: translateZ(100px);
      }
      .cube .back {
          background-color: green;
          transform: rotateY(180deg) translateZ(100px);
      }
      .cube:hover {
          transform: rotateY(180deg);
      }
  </style>

  <div class="cube">
      <div class="front"></div>
      <div class="back"></div>
  </div>
  ```

### Steps to Create a 3D Cube

1. Create a container and set `transform-style: preserve-3d;`.
2. Position child elements to form the faces of the cube.
3. Apply 3D transforms to position and rotate the faces as needed.
4. Use CSS transitions for smooth animations.

Animating `transform` or `opacity` can avoid repeated layout in suitable cases, but neither property guarantees a GPU-only path or a performance win. Rendering cost depends on the animated content, surface size, browser, and device; profile before adding transforms as an optimization.

## Animation

## When to Use Animation vs. Transition

### Transition
- **Use Case:** For simple changes with only start and end points.
- **Example:** Changing the background color of a button on hover.
- **Syntax:**
  ```css
  .button {
      transition: background-color 0.3s ease;
  }

  .button:hover {
      background-color: blue;
  }
  ```

### Animation
- **Use Case:** For more complex sequences involving multiple steps, intermediate states, and controllable animations.
- **Example:** Creating a loading spinner or a slideshow.
- **Syntax:**
  ```css
  @keyframes animationName {
      0% { /* initial state */ }
      50% { /* intermediate state */ }
      100% { /* final state */ }
  }

  .element {
      animation: animationName 2s infinite;
  }
  ```

## Defining Animation

### Keyframes
- **Syntax:**
  ```css
  @keyframes animationName {
      0% { /* from */ }
      100% { /* to */ }
      /* intermediate steps */
  }
  ```
- **Example:**
  ```css
  @keyframes changeWidth {
      0% {
          width: 200px;
      }
      30% {
          width: 300px;
      }
      100% {
          width: 800px;
      }
  }

  .box {
      width: 200px;
      height: 100px;
      background-color: pink;
      animation: changeWidth 1s;
  }
  ```

## Using Animation

### Animation Property Syntax
- **Comprehensive Syntax:**
  ```css
  animation: name duration timing-function delay iteration-count direction fill-mode play-state;
  ```
- **Order:** The properties can be swapped, and some can be ignored.

### Animation Timing Function
- **Values:**
  - `linear`: Uniform speed.
  - `ease`, `ease-in`, `ease-out`, `ease-in-out`: Various easing functions for smooth transitions.
  - `steps(number)`: Divides the animation into a set number of steps (useful for sprite animations).

### Animation Duration and Delay
- **Two Time-Values:**
  - First value: Duration of the animation.
  - Second value: Delay before the animation starts.

### Animation Iteration Count
- **Values:**
  - `number`: Specific number of repetitions.
  - `infinite`: Loops indefinitely.

### Animation Direction
- **Values:**
  - `normal`: Default, animation runs forward.
  - `reverse`: Runs animation backward.
  - `alternate`: Alternates between running forward and backward.
  - `alternate-reverse`: Alternates, starting backward.

### Animation Fill Mode
- **Values:**
  - `none`: Default, animation does not apply styles after finishing.
  - `forwards`: Retains the end state after completion.
  - `backwards`: Applies the starting state before the animation starts.
  - `both`: Applies both `forwards` and `backwards`.

### Animation Play State
- **Values:**
  - `running`: Default, the animation is playing.
  - `paused`: The animation is paused.

### Combining Multiple Animations
- **Syntax:**
  ```css
  animation: animation1, animation2, animation3;
  ```

## Comprehensive Example

### Continuous Scrolling Images

A box holding two identical three-image groups that scroll from right to left. The animation must move exactly one group's width so the second group takes the first group's place at the loop boundary.

#### HTML Structure
```html
<div class="carousel" role="group" aria-label="Featured images">
    <ul class="carousel-list">
        <li><img src="image1.jpg" alt="Image 1"></li>
        <li><img src="image2.jpg" alt="Image 2"></li>
        <li><img src="image3.jpg" alt="Image 3"></li>
        <!-- Duplicate group is visual only; do not announce it twice. -->
        <li aria-hidden="true"><img src="image1.jpg" alt=""></li>
        <li aria-hidden="true"><img src="image2.jpg" alt=""></li>
        <li aria-hidden="true"><img src="image3.jpg" alt=""></li>
    </ul>
</div>
```

#### CSS Styling
```css
.carousel {
    width: 100%;
    overflow: hidden;
}

.carousel-list {
    display: flex;
    width: 600%; /* Two groups of three slides; adjust for a different group size. */
    margin: 0;
    padding: 0;
    list-style: none;
    animation: scroll 10s linear infinite;
}

.carousel-list li {
    flex: 0 0 calc(100% / 6); /* Each item is one viewport wide in this six-item track. */
}

.carousel-list img {
    display: block;
    width: 100%;
    height: auto;
}

@keyframes scroll {
    0% {
        transform: translateX(0);
    }
    100% {
        transform: translateX(-50%); /* Exactly one of the two equal groups. */
    }
}
```

### Explanation
1. **Container with Overflow Hidden:**
   ```css
   .carousel {
       width: 100%;
       overflow: hidden;
   }
   ```
   - Ensures that only the visible part of the images is shown.

2. **Flexbox for Image List:**
   ```css
   .carousel-list {
       display: flex;
        width: 600%;
       animation: scroll 10s linear infinite;
   }
   ```
   - Flexbox arranges images in a row.
   - Width set to accommodate all images.

3. **Keyframes for Scrolling:**
   ```css
   @keyframes scroll {
       0% {
           transform: translateX(0);
       }
       100% {
           transform: translateX(-50%);
       }
   }
   ```
   - Animates the list from its original position to the left, creating a scrolling effect.

For users who request reduced motion, stop the animation and hide the duplicate items. A production carousel also needs an explicit pause control and interaction model.

```css
@media (prefers-reduced-motion: reduce) {
    .carousel-list { animation: none; }
    .carousel-list li[aria-hidden="true"] { display: none; }
}
```

**See also / 另见：** [CSS Position, Display, and Animations / CSS定位、显示与动画](../../../../frontend/html-css/css-position-display-and-animations.md) explains the current transition, animation, and compositing guidance.
