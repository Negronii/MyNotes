# How do typed class components model state and events? / 带类型的类组件如何表达 state 与事件？

A class component declares `Props` and `State` as generic parameters and updates state through `setState`, including an updater when the next value depends on the previous one. The examples are retained for legacy code and teaching. / 类组件通过 `Props` 和 `State` 泛型声明输入与内部状态，并通过 `setState` 更新；下一状态依赖前一状态时使用 updater。以下示例为旧代码维护和教学保留。

## Class in TypeScript / TypeScript中的类组件

In TypeScript, `React.Component` is a generic type that can take up to three parameters: `Props`, `State`, and an optional `Snapshot`. Using TypeScript with React ensures type safety, which helps catch errors during development.

### Example:

```tsx
import React from "react";
import styles from "./ShoppingCart.module.css";

interface Props {}

interface State {
  isHidden: boolean; // This is an attribute we defined, true when the cart is hidden
}

export default class ShoppingCart extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      isHidden: false,
    };
  }

  render() {
    return (
      <div className={styles.cartContainer}>
        <button
          className={styles.button}
          onClick={() => {
            this.setState({ isHidden: !this.state.isHidden });
          }}
        >
          Cart (2)
        </button>
        <div
          className={styles.cartDropDown}
          style={{ display: this.state.isHidden ? "none" : "block" }}
        >
          <ul>
            <li>robot 1</li>
            <li>robot 2</li>
          </ul>
        </div>
      </div>
    );
  }
}
```

To use this component in `app.tsx`:

```tsx
import React from "react";
import ShoppingCart from "./ShoppingCart";

const App = () => (
  <div>
    <h1>Welcome to the Robot Store</h1>
    <ShoppingCart />
  </div>
);

export default App;
```

## State vs. Props in a Class Component / 类组件中的State与Props

### Props
- **Definition**: Props (short for properties) are read-only attributes that are passed to components by their parent component.
- **Usage**: Used for passing data and event handlers down the component tree.
- **Read-only input**: A child should not mutate its props; the parent supplies new values through the next render.

### State
- **Definition**: State is a built-in object that holds data that may change over the component's lifecycle.
- **Usage**: Used for managing internal component data that can change over time.
- **Updates**: Treat state as read-only and use `setState()` to provide a replacement or an updater function.
- **Initialization**: State is typically initialized in the constructor.

### Key Differences
- **Source**: Props are passed from parent to child, whereas state is managed within the component.
- **Update path**: A child treats props as read-only; state changes go through `setState()` rather than direct mutation.

### Example:

```tsx
interface ParentProps {
  initialCount: number;
}

interface ParentState {
  count: number;
}

class ParentComponent extends React.Component<ParentProps, ParentState> {
  constructor(props: ParentProps) {
    super(props);
    this.state = {
      count: props.initialCount,
    };
  }

  render() {
    return (
      <div>
        <ChildComponent count={this.state.count} />
        <button
          onClick={() => this.setState({ count: this.state.count + 1 })}
        >
          Increment
        </button>
      </div>
    );
  }
}

interface ChildProps {
  count: number;
}

const ChildComponent: React.FC<ChildProps> = ({ count }) => (
  <div>Count: {count}</div>
);
```

## Updates Based on Previous Class State / 基于前一次类组件State更新

`setState()` queues an update; do not read `this.state` immediately after calling it and expect the new value. When the next value depends on the previous one, use the updater form, which receives the previous state and props.

### Syntax:

```tsx
this.setState(
  (prevState, prevProps) => {
    // Return the new state object
    return { ... };
  },
  () => {
    // Callback function executed after state update
    console.log(`State updated: ${this.state.someValue}`);
  }
);
```

### Example:

```tsx
interface State {
  count: number;
}

class Counter extends React.Component<{}, State> {
  constructor(props: {}) {
    super(props);
    this.state = {
      count: 0,
    };
  }

  increment = () => {
    this.setState(
      (prevState) => ({ count: prevState.count + 1 }),
      () => {
        console.log(`Count is now: ${this.state.count}`);
      }
    );
  };

  render() {
    return (
      <div>
        <p>Count: {this.state.count}</p>
        <button onClick={this.increment}>Increment</button>
      </div>
    );
  }
}
```

### Explanation:
- **Updater Function**: The first argument to `setState()` is a function that receives `prevState` and `prevProps`.
- **Callback**: The second argument runs after the update has been committed.

Using this pattern ensures that state updates are based on the most recent state, avoiding potential synchronization issues.
## Event Handling / 事件处理

## The "this" Pointing Problem

In a class component, an unbound instance method loses its receiver when React calls it as an event handler. In strict mode, `this` is `undefined`; it does not refer to the class instance.

### Incorrect Usage

The following method is not bound, so `this.setState` fails when the button calls it:

```tsx
class MyComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = { ishidden: false };
  }

  handleClick(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) {
    // Error: 'this' is undefined
    this.setState({ ishidden: !this.state.ishidden });
  }

  render() {
    return <button onClick={this.handleClick}>Click me</button>;
  }
}
```

### Correct Usage

To avoid this issue, we can use an arrow function, which binds `this` lexically, meaning `this` inside the arrow function will refer to the class instance:

```tsx
class MyComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = { ishidden: false };
  }

  handleClick = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    this.setState({ ishidden: !this.state.ishidden });
  }

  render() {
    return <button onClick={this.handleClick}>Click me</button>;
  }
}
```

In modern React development, it's recommended to use functional components with hooks whenever possible, as they provide a more concise and readable way to handle state and side effects.

### Using Functional Components with Hooks

```tsx
import React, { useState } from 'react';

const MyComponent = () => {
  const [isHidden, setIsHidden] = useState(false);

  const handleClick = () => {
    setIsHidden(previous => !previous);
  };

  return <button onClick={handleClick}>Click me</button>;
};
```

## `e.target` and `e.currentTarget` / 事件目标与监听元素

When handling events, it's important to distinguish between `e.target` and `e.currentTarget`:

- `e.target` refers to the element on which the event originally occurred. This is the deepest element that triggered the event.
- `e.currentTarget` refers to the element that has the event listener attached. This is useful when you have nested elements and you want to ensure that the handler is reacting to the correct element.

### Example

Consider a button element that contains a span element with text:

```tsx
const MyComponent = () => {
  const handleClick = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    console.log("e.target:", e.target);
    console.log("e.currentTarget:", e.currentTarget);

    if ((e.target as HTMLElement).nodeName === "SPAN") {
      // Do something if the span was clicked
      console.log("Span was clicked");
    }
  };

  return (
    <button onClick={handleClick}>
      <span>Click me</span>
    </button>
  );
};
```

When the span is clicked:

- `e.target` will be the `span` element.
- `e.currentTarget` will be the `button` element.

This allows you to differentiate the element that triggered the event from the element that is handling the event.

**See also / 另见：** [React Basics / React基础](../../../../frontend/frameworks/react-basics.md) for current state and lifecycle semantics.
