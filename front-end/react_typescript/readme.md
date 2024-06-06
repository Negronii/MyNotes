## Create React App with TypeScript Template

To create a React app with the TypeScript template, use the following command:

```bash
npx create-react-app react-ts --template typescript
```

This command sets up a new React project configured with TypeScript, providing type safety and enhanced development experience.

## TypeScript Configuration

To enable TypeScript to accept the `any` type, modify the `tsconfig.json` file by adding `"noImplicitAny": false` in the `compilerOptions` section. This configuration allows the use of the `any` type without compiler errors:

```json
{
    "compilerOptions": {
        "noImplicitAny": false,
        ...
    }
}
```

However, it's generally recommended to avoid using `any` and instead use specific types to maintain type safety and code quality.

## Creating a Component in TypeScript

Here's an example of a React component written in TypeScript:

```tsx
import React from "react";

interface RobotProps {
  id: number;
  name: string;
  email: string;
}

const Robot: React.FC<RobotProps> = ({ id, name, email }) => {
  return (
    <li>
      <img alt="robot" src={`https://robohash.org/${id}`} />
      <h2>{name}</h2>
      <p>{email}</p>
    </li>
  );
};

export default Robot;
```

### Key Points:

- `React.FC` is a generic type provided by React for defining function components. It includes type-checking for props and other component features.
- Defining the type of `React.FC` using an interface (e.g., `RobotProps`) ensures that prop types are validated by TypeScript.

## Using the Component in App.tsx

Here's how to use the `Robot` component in your main `App` component:

```tsx
import React from "react";
import robots from "./mockData/robots.json";
import Robot from "./components/Robot";

export default function App() {
  return (
    <ul>
      {robots.map((r) => (
        <Robot key={r.id} id={r.id} email={r.email} name={r.name} />
      ))}
    </ul>
  );
}
```

### Key Points:

- Use the `.map()` function to render a list of components.
- Always provide a `key` prop when rendering lists in React to ensure efficient updates.

## CSS in TypeScript

When using CSS modules with TypeScript, follow this approach:

1. **File Naming Convention:**

   Name your CSS files as `<component>.module.css`, ensuring that styles are scoped to the component.

2. **Importing CSS Modules:**

   Instead of importing CSS directly, import it as a module to avoid global style conflicts:

   ```tsx
   import styles from "./<component>.module.css";
   ```

3. **Declaring CSS Modules for TypeScript:**

   Create a file called `custom.d.ts` to declare CSS modules for TypeScript:

   ```tsx
   declare module "*.css" {
     const styles: { [className: string]: string };
     export default styles;
   }
   ```

4. **Using CSS Modules:**

   Apply CSS classes in JSX as follows:

   ```tsx
   <div className={styles.app}>
   ```

   For class names with hyphens, use:

   ```tsx
   <div className={styles['app-style']}>
   ```

## Project Structure and Media Import

### Recommended Project Structure:

- **assets/**: Directory for media files.
  - **images/**: Directory for images.
  - **fonts/**: Directory for fonts.
  - **icons/**: Directory for icons.

### Importing Media:

#### Importing Images:

To import an image:

```tsx
import logo from "./assets/images/logo.svg";
```

React automatically handles common image types (`.svg`, `.jpg`, `.jpeg`, `.png`), so no additional declaration is needed.

#### Importing Fonts:

1. **Add Font Files:**

   Place the font file in the `assets/fonts` directory.

2. **Declare Fonts in CSS:**

   Add the font in your global `index.css` or any global stylesheet:

   ```css
   @font-face {
     font-family: "Slidefu";
     src: local("Slidefu"), url("./assets/fonts/Slidefu-Regular-2.ttf") format("truetype");
   }
   ```

3. **Use Fonts in Components:**

   Apply the font in your component-specific CSS file:

   ```css
   h1 {
     font-family: "Slidefu";
     font-size: 72px;
   }
   ```

## Class in TypeScript

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

## State vs Props in Component Class

### Props
- **Definition**: Props (short for properties) are read-only attributes that are passed to components by their parent component.
- **Usage**: Used for passing data and event handlers down the component tree.
- **Immutability**: Props are immutable; they cannot be changed by the child component.

### State
- **Definition**: State is a built-in object that holds data that may change over the component's lifecycle.
- **Usage**: Used for managing internal component data that can change over time.
- **Mutability**: State is mutable; it can be updated using `setState()`.
- **Initialization**: State is typically initialized in the constructor.

### Key Differences
- **Source**: Props are passed from parent to child, whereas state is managed within the component.
- **Mutability**: Props are immutable, while state is mutable.

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

## Synchronization Problem in `setState()`

Since `setState()` is asynchronous, it can lead to issues when trying to update state based on the current state. To handle this, use the updater function form of `setState()`, which provides the previous state and props.

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
- **Callback**: The second argument is a callback function that is executed after the state has been updated.

Using this pattern ensures that state updates are based on the most recent state, avoiding potential synchronization issues.
# Event Handling

## The "this" Pointing Problem

In React class components, the `this` keyword can often be misinterpreted when used inside event handlers. By default, `this` inside an event handler will not refer to the class instance but to the function itself, leading to errors when attempting to access the class instance’s properties or methods.

### Incorrect Usage

The following code inside a class will trigger an error because `this` points to the function `handleClick`, not the class instance, resulting in no `setState` method being available:

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

  const handleClick = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    setIsHidden(!isHidden);
  };

  return <button onClick={handleClick}>Click me</button>;
};
```

## `e.target` and `e.currentTarget`

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

## Request Data in Lifecycle Methods

In class components, `componentDidMount()` is a lifecycle method that is invoked immediately after a component is mounted (inserted into the tree). It's a common place to initiate network requests to fetch data.

### Example

```tsx
class MyComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = { data: null };
  }

  componentDidMount() {
    fetch("https://api.example.com/data")
      .then(response => response.json())
      .then(data => this.setState({ data }));
  }

  render() {
    const { data } = this.state;
    return data ? <div>{data}</div> : <div>Loading...</div>;
  }
}
```

In functional components, the `useEffect` hook is used to handle side effects such as data fetching:

### Example with Hooks

```tsx
import React, { useState, useEffect } from 'react';

const MyComponent = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("https://api.example.com/data")
      .then(response => response.json())
      .then(data => setData(data));
  }, []); // The empty array ensures this effect runs only once after the initial render

  return data ? <div>{data}</div> : <div>Loading...</div>;
};
```

# Hooks

Hooks help to monitor processes and add state to functional components. They allow you to "hook" external code when the process requires side effects. Using hooks, you can substitute class components with functional components. Here are some frequently used hooks:

- `useState`: Manages state in a functional component.
- `useEffect`: Performs side effects in a functional component.
- `useReducer`: Manages state with complex logic.
- `useContext`: Accesses context in a functional component.

All hooks are named using the `useXXX` convention.

## useState

The `useState` hook allows you to add state to functional components. It returns an array with two elements: the current state and a function to update it.

### Example

```jsx
import React, { useState } from 'react';

const Counter: React.FC = () => {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>You clicked {count} times</p>
      <button onClick={() => setCount(count + 1)}>
        Click me
      </button>
    </div>
  );
};

export default Counter;
```

### Explanation

In the example above:
- `useState(0)` initializes the state variable `count` to 0.
- `setCount` is the function to update the state.

## useEffect

The `useEffect` hook lets you perform side effects in function components. It takes two arguments: a function and a dependency array. The function runs after the first render and after every update.

### Example

```jsx
import React, { useState, useEffect } from 'react';

const EffectDemo: React.FC = () => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    document.title = `You clicked ${count} times`;
  }, [count]);

  return (
    <div>
      <p>You clicked {count} times</p>
      <button onClick={() => setCount(count + 1)}>
        Click me
      </button>
    </div>
  );
};

export default EffectDemo;
```

### Explanation

In the example above:
- The function inside `useEffect` runs after every render where `count` changes.
- The dependency array `[count]` ensures the effect only runs when `count` changes.

## useReducer

The `useReducer` hook is used for managing state with complex logic. It is an alternative to `useState` and is usually preferable when you have multiple state variables that rely on complex logic.

### Example

```jsx
import React, { useReducer } from 'react';

type Action = { type: 'increment' } | { type: 'decrement' };

const reducer = (state: number, action: Action): number => {
  switch (action.type) {
    case 'increment':
      return state + 1;
    case 'decrement':
      return state - 1;
    default:
      return state;
  }
};

const Counter: React.FC = () => {
  const [count, dispatch] = useReducer(reducer, 0);

  return (
    <div>
      <p>{count}</p>
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
    </div>
  );
};

export default Counter;
```

### Explanation

In the example above:
- `useReducer(reducer, 0)` initializes the state to 0 and provides a `dispatch` function to update the state.
- The `reducer` function defines how the state changes in response to actions.

## useContext

The `useContext` hook allows you to access the context in a functional component. It makes it easy to pass data through the component tree without passing props down manually at every level.

### Example

```jsx
import React, { useContext, createContext } from 'react';

const CountContext = createContext(0);

const DisplayCount: React.FC = () => {
  const count = useContext(CountContext);
  return <div>{count}</div>;
};

const App: React.FC = () => {
  return (
    <CountContext.Provider value={10}>
      <DisplayCount />
    </CountContext.Provider>
  );
};

export default App;
```

### Explanation

In the example above:
- `createContext(0)` creates a context with a default value of 0.
- `useContext(CountContext)` retrieves the context value.

## Best Practices for Using Hooks

1. **Keep Hooks at the Top Level**: Always call hooks at the top level of your component. Avoid calling hooks inside loops, conditions, or nested functions.

2. **Use Multiple State Variables if Needed**: Instead of combining state variables, use multiple `useState` or `useReducer` calls.

3. **Optimize useEffect Dependencies**: Make sure the dependency array in `useEffect` is accurate to avoid unnecessary re-renders.

4. **Custom Hooks**: Create custom hooks to extract and reuse stateful logic across multiple components.

### Custom Hook Example

```jsx
import { useState, useEffect } from 'react';

const useFetch = (url: string) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(url);
        const result = await response.json();
        setData(result);
      } catch (e) {
        if (e instanceof Error) {
          setError(e.message);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [url]);

  return { data, loading, error };
};

export default useFetch;
```

### Explanation

In the custom hook example above:
- `useFetch` encapsulates the logic for fetching data.
- It returns the fetched data, loading state, and any error encountered.

Using hooks effectively can greatly simplify your code and make it more readable and maintainable. Always follow best practices to ensure optimal performance and scalability in your React applications.

## Context and useContext

### Introduction
In React, context provides a way to pass data through the component tree without having to pass props down manually at every level. This is useful for global data that many components need to access, such as user information, theme settings, or application state.

### Creating Context

To create a context, you use the `createContext` function. This function takes an initial value and returns a context object.

```typescript
import { createContext } from "react";

const defaultContextValue = {
  username: "Ron",
};

export const appContext = createContext(defaultContextValue);
```

Here, `defaultContextValue` provides a default value for the context. This value is used when a component does not have a matching `Provider` above it in the tree.

### Providing Context

To use the context in child components, wrap the part of your component tree that needs access to the context with the `Provider` component of the context.

```tsx
import React from "react";
import ReactDOM from "react-dom";
import { appContext } from "./context";

const defaultContextValue = {
  username: "Ron",
};

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);

root.render(
  <React.StrictMode>
    <appContext.Provider value={defaultContextValue}>
      <App />
    </appContext.Provider>
  </React.StrictMode>
);
```

### Consuming Context in Functional Components

In functional components, you can use the `useContext` hook to access the context value.

```tsx
import React, { useContext } from "react";
import { appContext } from "../context";

interface RobotProps {
  id: number;
  name: string;
  email: string;
}

const Robot: React.FC<RobotProps> = ({ id, name, email }) => {
  const value = useContext(appContext);

  return (
    <div className="card-container">
      <img alt="robot" src={`https://robohash.org/${id}`} />
      <h2>{name}</h2>
      <p>{email}</p>
      <p>username: {value.username}</p>
    </div>
  );
};

export default Robot;
```

### Consuming Context in Class Components

For class components, you can use the `Consumer` component of the context.

```tsx
import React, { Component } from "react";
import { appContext } from "../context";

class Robot extends Component {
  render() {
    return (
      <appContext.Consumer>
        {value => (
          <div className="card-container">
            <img alt="robot" src={`https://robohash.org/${this.props.id}`} />
            <h2>{this.props.name}</h2>
            <p>{this.props.email}</p>
            <p>username: {value.username}</p>
          </div>
        )}
      </appContext.Consumer>
    );
  }
}

export default Robot;
```

### Managing Global State with Context

To manage global state, you can create a context that holds both the state and the state updater function.

**Example: AppState.tsx**

```tsx
import React, { createContext, useState, PropsWithChildren } from "react";

interface AppStateValue {
  username: string;
  shoppingCart: { items: { id: number; name: string }[] };
}

const defaultContextValue: AppStateValue = {
  username: "Ron",
  shoppingCart: { items: [] },
};

export const appContext = createContext(defaultContextValue);
export const setStateContext = createContext<React.Dispatch<React.SetStateAction<AppStateValue>> | undefined>(undefined);

export const AppStateProvider: React.FC<PropsWithChildren<{}>> = (props) => {
  const [state, setState] = useState(defaultContextValue);

  return (
    <appContext.Provider value={state}>
      <setStateContext.Provider value={setState}>
        {props.children}
      </setStateContext.Provider>
    </appContext.Provider>
  );
};
```

### Using the Global State

Wrap your app in the `AppStateProvider` component to provide the global state to the entire application.

**index.tsx:**

```tsx
import React from "react";
import ReactDOM from "react-dom";
import { AppStateProvider } from "./AppState";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);

root.render(
  <React.StrictMode>
    <AppStateProvider>
      <App />
    </AppStateProvider>
  </React.StrictMode>
);
```

**robot.tsx:**

Add items to the shopping cart by using the `setStateContext`.

```tsx
import React, { useContext } from "react";
import { appContext, setStateContext } from "./AppState";

const Robot: React.FC<RobotProps> = ({ id, name, email }) => {
  const state = useContext(appContext);
  const setState = useContext(setStateContext);

  const addToCart = () => {
    if (setState) {
      setState((prevState) => {
        return {
          ...prevState,
          shoppingCart: {
            items: [...prevState.shoppingCart.items, { id, name }],
          },
        };
      });
    }
  };

  return (
    <div className="card-container">
      <img alt="robot" src={`https://robohash.org/${id}`} />
      <h2>{name}</h2>
      <p>{email}</p>
      <p>username: {state.username}</p>
      <button onClick={addToCart}>Add to Cart</button>
    </div>
  );
};

export default Robot;
```

**shoppingCart.tsx:**

Display the items in the shopping cart using the `appContext.Consumer`.

```tsx
import React, { useContext } from "react";
import { appContext } from "./AppState";
import { FiShoppingCart } from "react-icons/fi";

const ShoppingCart: React.FC = () => {
  const value = useContext(appContext);

  return (
    <div className="cart-container">
      <button className="button">
        <FiShoppingCart />
        <span>Cart ({value.shoppingCart.items.length})</span>
      </button>
      <div className="cart-drop-down">
        <ul>
          {value.shoppingCart.items.map((i) => (
            <li key={i.id}>{i.name}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default ShoppingCart;
```

### Higher-Order Components (HOC)

A Higher-Order Component (HOC) is a function that takes a component and returns a new component with additional props or behavior. HOCs are used for:

- **Code Reuse and Logic Abstraction**: Extracting and reusing logic across multiple components.
- **Conditional Rendering**: Encapsulating rendering logic that depends on specific conditions.
- **Props Manipulation**: Adding, modifying, or removing props passed to a component.
- **Lifecycle Management**: Adding side effects or lifecycle methods to a component.

#### Best Practices
- **Naming Convention**: Prefix HOCs with `with` to indicate their purpose, e.g., `withAuth`, `withLogging`.
- **Do Not Mutate Original Component**: Avoid modifying the original component. Instead, create and return a new one.
- **Pass All Props**: Ensure that all props are passed down to the wrapped component to maintain the original component's functionality.
- **Static Methods Copying**: Copy non-React static methods from the original component to the new one.

#### Example
Below is an example of a HOC that adds a function to handle adding items to a shopping cart:

```jsx
// withAddToCart.tsx
import React, { useContext } from 'react';

const withAddToCart = (WrappedComponent) => {
  return (props) => {
    const setState = useContext(setStateContext);

    const addToCart = (id, name) => {
      if (setState) {
        setState((prevState) => ({
          ...prevState,
          shoppingCart: {
            items: [...prevState.shoppingCart.items, { id, name }],
          },
        }));
      }
    };

    return <WrappedComponent {...props} addToCart={addToCart} />;
  };
};

export default withAddToCart;

// Robot.tsx
import React, { useContext } from 'react';
import withAddToCart from './withAddToCart';
import styles from './Robot.module.css';

export interface RobotProps {
  id: number;
  name: string;
  email: string;
  addToCart: (id: number, name: string) => void;
}

const Robot: React.FC<RobotProps> = ({ id, name, email, addToCart }) => {
  const value = useContext(appContext);

  return (
    <div className={styles.cardContainer}>
      <img alt="robot" src={`https://robohash.org/${id}`} />
      <h2>{name}</h2>
      <p>{email}</p>
      <p>username: {value.username}</p>
      <button onClick={() => addToCart(id, name)}>Add to cart</button>
    </div>
  );
};

export default withAddToCart(Robot);
```

### Custom Hooks

#### Definition and Purpose
Custom hooks are functions that start with `use` and allow you to encapsulate and reuse stateful logic across different components. They enable sharing logic that involves React's state or lifecycle features without using HOCs or render props.

#### Best Practices
- **Naming Convention**: Always start the custom hook's name with `use`, e.g., `useFetchData`, `useFormValidation`.
- **Single Responsibility**: Each custom hook should do one thing well and be as focused as possible.
- **Return Values**: Return an array or object containing values and functions that the component needs.
- **Avoid Side Effects in Return**: Do not include side effects (e.g., setting state) in the returned functions or values.

#### Example
Here’s an example of a custom hook to handle adding items to a shopping cart:

```jsx
// useAddToCart.tsx
import React, { useContext } from 'react';

export const useAddToCart = () => {
  const setState = useContext(setStateContext);

  const addToCart = (id, name) => {
    if (setState) {
      setState((prevState) => ({
        ...prevState,
        shoppingCart: {
          items: [...prevState.shoppingCart.items, { id, name }],
        },
      }));
    }
  };

  return addToCart;
};

// Robot.tsx
import React, { useContext } from 'react';
import { useAddToCart } from './useAddToCart';
import styles from './Robot.module.css';

export interface RobotProps {
  id: number;
  name: string;
  email: string;
}

const Robot: React.FC<RobotProps> = ({ id, name, email }) => {
  const value = useContext(appContext);
  const addToCart = useAddToCart();

  return (
    <div className={styles.cardContainer}>
      <img alt="robot" src={`https://robohash.org/${id}`} />
      <h2>{name}</h2>
      <p>{email}</p>
      <p>username: {value.username}</p>
      <button onClick={() => addToCart(id, name)}>Add to cart</button>
    </div>
  );
};

export default Robot;
```

## Simplified Imports Using `index.tsx`

Simplifying imports using `index.tsx` (or `index.ts`) files is a common practice in modern front-end development. This approach helps to clean up import statements, making the codebase more readable and maintainable. It centralizes exports in a single file, allowing for more concise and manageable import statements.

### Implementation

#### Directory Structure
Assuming you have a directory structure like this:
```
src/
├── components/
│   ├── header/
│   │   ├── Header.tsx
│   │   ├── index.ts
│   ├── footer/
│   │   ├── Footer.tsx
│   │   ├── index.ts
│   ├── index.ts
│   ├── App.tsx
```

#### `index.ts` in Subdirectories
In the `/header` directory, create an `index.ts` file to re-export the `Header` component:
```typescript
// src/components/header/index.ts
export * from './Header';
```

Similarly, in the `/footer` directory, create an `index.ts` file to re-export the `Footer` component:
```typescript
// src/components/footer/index.ts
export * from './Footer';
```

#### Centralized `index.ts` in Components Directory
In the `/components` directory, create an `index.ts` file to re-export all components:
```typescript
// src/components/index.ts
export * from './header';
export * from './footer';
```

#### Using Simplified Imports
In your `App.tsx` file, you can now import the `Header` and `Footer` components using a single import statement:
```tsx
// src/components/App.tsx
import { Header, Footer } from './components';

const App = () => (
  <div>
    <Header />
    <Footer />
  </div>
);

export default App;
```

### Benefits
- **Cleaner Imports:** Reduces the clutter in import statements.
- **Centralized Exports:** Easier to manage and update exports from a single file.
- **Improved Readability:** Makes the codebase more intuitive and easier to navigate.

### Example Project Structure
```plaintext
src/
├── components/
│   ├── header/
│   │   ├── Header.tsx
│   │   ├── index.ts
│   ├── footer/
│   │   ├── Footer.tsx
│   │   ├── index.ts
│   ├── index.ts
│   ├── App.tsx
```

## Using Ant Design

### Overview
Ant Design is a popular React UI framework that provides a rich set of high-quality components out of the box. It is widely used in enterprise applications due to its comprehensive design system and ease of use.

### Installation
To use Ant Design, you need to install the core library along with the icons package. Run the following command to install both:
```bash
npm install antd @ant-design/icons
```

### Using Components
After installation, you can start using Ant Design components in your project. Here is a basic example demonstrating the use of the `Layout`, `Typography`, `Input`, `Menu`, `Button`, and `Dropdown` components.

#### Example
```tsx
// src/components/Header.tsx
import React from 'react';
import { Layout, Menu } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';

const { Header } = Layout;

const AppHeader: React.FC = () => (
  <Header>
    <div className="logo" />
    <Menu theme="dark" mode="horizontal" defaultSelectedKeys={['1']}>
      <Menu.Item key="1" icon={<GlobalOutlined />}>Home</Menu.Item>
      <Menu.Item key="2">About</Menu.Item>
      <Menu.Item key="3">Contact</Menu.Item>
    </Menu>
  </Header>
);

export default AppHeader;
```

#### Integrating Ant Design in `App.tsx`
```tsx
// src/components/App.tsx
import React from 'react';
import { Layout, Typography } from 'antd';
import AppHeader from './header/Header';
import AppFooter from './footer/Footer';

const { Content } = Layout;
const { Title } = Typography;

const App: React.FC = () => (
  <Layout>
    <AppHeader />
    <Content style={{ padding: '0 50px' }}>
      <Title level={2}>Welcome to My App</Title>
      <p>This is a simple example of using Ant Design with React.</p>
    </Content>
    <AppFooter />
  </Layout>
);

export default App;
```

### Exploring Ant Design Components
For more examples and detailed documentation on how to use different Ant Design components, visit the [Ant Design Components Overview](https://ant.design/components/overview).

### Best Practices
- **Consistent Use of Ant Design Components:** Ensure consistency in design by leveraging Ant Design components across the application.
- **Theming and Customization:** Use Ant Design's theming capabilities to customize the appearance to match your brand.
- **Responsive Design:** Utilize the responsive grid system and other responsive components to ensure your application works well on different screen sizes.

# Routing in React

## Overview

Routing in React involves managing the navigation between different components and views in a React application by tracking the URL. This is crucial for building single-page applications (SPAs) where different views are rendered based on the URL path without reloading the entire page.

The `react-router` package is a popular library for implementing routing in React. It provides various components and hooks to manage navigation, URL parameters, and more.

## Installation

To install `react-router`, use the following command:

```bash
npm install react-router-dom@latest
```

## Key Components and Hooks

### `<BrowserRouter>`

- Uses the HTML5 History API to keep the UI in sync with the URL.
- Should be used at the root of your application.

### `<HashRouter>`

- Uses the URL hash (e.g., `example.com/#/path`) to keep the UI in sync with the URL.
- Useful for older browsers that do not support the HTML5 History API.

### `<Routes>` and `<Route>`

- `<Routes>` is a container for all your route definitions.
- `<Route>` defines a mapping between a URL path and a component.

### `<Link>`

- Used to create navigational links. It renders an `<a>` element that allows navigation without reloading the page.

### `useParams`

- A hook to access the dynamic parameters in the URL.

### `useNavigate`

- A hook to programmatically navigate to different routes.

### `useLocation`

- A hook to access the current location object, which contains information about the URL.

## Defining Routes

Example: Display the `HomePage` component when the URL path is `/`, `LoginPage` when it is `/login`, and so on. Show a "page not found" message if the URL does not match any defined routes.

```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './HomePage';
import LoginPage from './LoginPage';
import RegisterPage from './RegisterPage';
import DetailPage from './DetailPage';
import styles from './App.module.css';

function App() {
  return (
    <div className={styles.App}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/detail/:touristRouteId/:other" element={<DetailPage />} />
          <Route path="*" element={<h1>404 page not found, catch all</h1>} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
```

## Passing Parameters from URL

### Single Parameter

Example: Passing an ID as a parameter to the detail page.

In `App.tsx`:

```jsx
<Route path="/detail/:touristRouteId" element={<DetailPage />} />
```

In `DetailPage.tsx`:

```jsx
import { useParams } from 'react-router-dom';

export const DetailPage: React.FC = () => {
  const { touristRouteId } = useParams<{ touristRouteId: string }>();
  return <h1>Detail page, id: {touristRouteId}</h1>;
};
```

### Multiple Parameters

Example: Passing multiple parameters.

In `App.tsx`:

```jsx
<Route path="/detail/:touristRouteId/:other" element={<DetailPage />} />
```

In `DetailPage.tsx`:

```jsx
import { useParams } from 'react-router-dom';

type MatchParams = {
  touristRouteId: string;
  other: string;
};

export const DetailPage: React.FC = () => {
  const params = useParams<MatchParams>();
  return (
    <h1>
      Detail page, id: {params.touristRouteId}, other: {params.other}
    </h1>
  );
};
```

## Navigation

### Using `useNavigate`

Example:

```jsx
import { useNavigate } from 'react-router-dom';

const MyComponent: React.FC = () => {
  const navigate = useNavigate();

  const handleRegister = () => {
    navigate('/register');
  };

  return <button onClick={handleRegister}>Register</button>;
};
```

### Using `<Link>`

An alternative way is to use `<Link>` from `'react-router-dom'`:

```jsx
import { Link } from 'react-router-dom';

const MyComponent: React.FC = () => {
  return <Link to="/register">Register</Link>;
};
```

### Best Practices

1. **Use `<Link>` for Navigation:** It is preferred over `useNavigate` for simple navigational links because it creates a semantic `<a>` element and avoids the need for an additional event handler.
2. **Define Routes Clearly:** Group related routes together and define a clear structure to make the routing configuration easy to read and maintain.
3. **Handle 404s Gracefully:** Always include a catch-all route (`path="*"`) to handle unknown URLs and provide a user-friendly message or redirect.
4. **Use Hooks for Parameters and Navigation:** Utilize `useParams`, `useNavigate`, and `useLocation` hooks to access URL parameters and navigate programmatically within your components.

# Redux

Redux is a state management library often used with React to manage and centralize application state. It follows the principles of a unidirectional data flow and provides a predictable state container for JavaScript apps.

## Goal

The primary goal of Redux is to manage and centralize the state of an application, making the state more predictable and easier to manage.

## When to Use Redux

Redux is particularly useful in scenarios where:

- Multiple components need to share data.
- The state of the application can be accessed and updated from various parts of the application.
- There are complex state interactions that are difficult to manage with local component state.

Examples include:

- Global language switch
- Dark mode switch
- User authentication and global user data

## Redux Architecture

![Redux Architecture](redux_architecture.png)

## Core Concepts

### Actions

Actions are plain JavaScript objects that represent an intention to change the state. They are the only source of information for the store. Actions must have a `type` property that indicates the type of action being performed.

Example:

```tsx
export const CHANGE_LANGUAGE = "CHANGE_LANGUAGE";

export const changeLanguage = (language: string) => ({
  type: CHANGE_LANGUAGE,
  payload: language,
});
```

### Reducers

Reducers are pure functions that take the current state and an action as arguments and return a new state. They specify how the application's state changes in response to an action.

Example:

```tsx
import { CHANGE_LANGUAGE } from "./languageActions";

interface LanguageState {
  language: "en" | "zh";
  languageList: { name: string; code: string }[];
}

const initialState: LanguageState = {
  language: "zh",
  languageList: [
    { name: "中文", code: "zh" },
    { name: "English", code: "en" },
  ],
};

const languageReducer = (state = initialState, action): LanguageState => {
  switch (action.type) {
    case CHANGE_LANGUAGE:
      return { ...state, language: action.payload };
    default:
      return state;
  }
};

export default languageReducer;
```

### Store

The store is the object that brings actions and reducers together. It holds the application state and provides methods to access the state, dispatch actions, and register listeners.

Creating a store with Redux Toolkit:

```tsx
// store.ts
import { configureStore } from "@reduxjs/toolkit";
import languageReducer from "./language/languageReducer";

const store = configureStore({
  reducer: {
    language: languageReducer,
  },
});

export default store;
```

### Middleware

Middleware provides a third-party extension point between dispatching an action and the moment it reaches the reducer. It can be used for logging, crash reporting, or handling asynchronous actions.

Example using `redux-thunk`:

```bash
npm install redux-thunk
```

```tsx
// store.ts
import { configureStore } from "@reduxjs/toolkit";
import thunk from "redux-thunk";
import languageReducer from "./language/languageReducer";

const store = configureStore({
  reducer: {
    language: languageReducer,
  },
  middleware: [thunk],
});

export default store;
```

### Using Redux with React

#### Connecting a Component

To connect a React component to the Redux store, use the `useSelector` and `useDispatch` hooks from `react-redux`.

Install `react-redux`:

```bash
npm install react-redux
```

Example:

```tsx
// LanguageSwitcher.tsx
import React from "react";
import { useSelector, useDispatch } from "react-redux";
import { changeLanguage } from "./language/languageActions";

const LanguageSwitcher = () => {
  const language = useSelector((state) => state.language.language);
  const dispatch = useDispatch();

  const handleLanguageChange = (e) => {
    dispatch(changeLanguage(e.target.value));
  };

  return (
    <div>
      <select value={language} onChange={handleLanguageChange}>
        <option value="en">English</option>
        <option value="zh">中文</option>
      </select>
    </div>
  );
};

export default LanguageSwitcher;
```

### Combining Reducers

For larger applications, it is common to split the state and reducers into smaller, more manageable parts. These can be combined using `combineReducers`.

Example:

```tsx
import { combineReducers } from "@reduxjs/toolkit";
import languageReducer from "./language/languageReducer";
import themeReducer from "./theme/themeReducer";

const rootReducer = combineReducers({
  language: languageReducer,
  theme: themeReducer,
});

export default rootReducer;
```

### Using Redux DevTools

Redux DevTools is a powerful tool for debugging application state changes. To integrate it, use the `redux-devtools-extension` package.

```bash
npm install redux-devtools-extension
```

```tsx
// store.ts
import { configureStore } from "@reduxjs/toolkit";
import { composeWithDevTools } from "redux-devtools-extension";
import rootReducer from "./rootReducer";

const store = configureStore({
  reducer: rootReducer,
  enhancers: [composeWithDevTools()],
});

export default store;
```

# i18Next: A Comprehensive Guide

This guide will walk you through the process of setting up i18Next for your React application. i18Next is a powerful internationalization framework for JavaScript, compatible with React, and widely used in modern front-end development.

## Installation

To install i18Next and its React integration, run the following command in your terminal:

```bash
npm install react-i18next i18next --save
```

## Configuration

### Step 1: Create a Configuration File

1. Create a `configs.ts` (or `configs.js` for JavaScript) file in your project directory.

2. Import the necessary modules:

```tsx
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
```

### Step 2: Create Language JSON Files

1. Create language JSON files (e.g., `en.json` for English, `zh.json` for Chinese) in your project directory. These files will contain your translations.

### Step 3: Import Language JSON Files

1. Import the language JSON files into `configs.ts`:

```tsx
import translation_en from "./locales/en.json";
import translation_zh from "./locales/zh.json";
```

### Step 4: Set Up i18Next Configuration

1. Set up your i18Next configuration:

```tsx
const resources = {
  en: {
    translation: translation_en,
  },
  zh: {
    translation: translation_zh,
  },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "en",
    fallbackLng: "en", // Fallback language if the current language translation is not available
    interpolation: {
      escapeValue: false, // React already safes from XSS
    },
  });

export default i18n;
```

## Usage in React Components

### Class Components

1. Import the `withTranslation` higher-order component (HOC) and `WithTranslation` type from `react-i18next`:

```tsx
import { withTranslation, WithTranslation } from "react-i18next";
```

2. Add `WithTranslation` to your component's props type:

```tsx
class HeaderComponent extends React.Component<RouteComponentProps & WithTranslation, State> {
  ...
}
```

3. In your component's render function, extract the `t` function from the props. This function is used to translate your text:

```tsx
render() {
  const { t } = this.props;
  return (
    <div>
      <Typography.Text>{t("header.slogan")}</Typography.Text>
      <Dropdown.Button>
        {this.state.language === "en" ? "English" : "中文"}
      </Dropdown.Button>
    </div>
  );
}
```

4. Wrap your component with the `withTranslation` HOC when exporting:

```tsx
export const Header = withTranslation()(withRouter(HeaderComponent));
```

### Functional Components

1. In functional components, you can use the `useTranslation` hook instead of the `withTranslation` HOC:

```tsx
import { useTranslation } from "react-i18next";

export const Footer: React.FC = () => {
  const { t } = useTranslation();
  return (
    <Layout.Footer>
      <Typography.Title level={3} style={{ textAlign: "center" }}>
        {t("footer.detail")}
      </Typography.Title>
    </Layout.Footer>
  );
};
```

## Redux Integration

To ensure strong typing for your Redux actions, you can use action creators. Here's an example of how to do this for language-related actions:

### Action Creators

1. Define action types and creators:

```tsx
export const CHANGE_LANGUAGE = "change_language";

interface ChangeLanguageAction {
  type: typeof CHANGE_LANGUAGE;
  payload: "zh" | "en";
}

export type LanguageActionTypes = ChangeLanguageAction;

export const changeLanguageActionCreator = (
  languageCode: "zh" | "en"
): ChangeLanguageAction => ({
  type: CHANGE_LANGUAGE,
  payload: languageCode,
});
```

### Reducers

1. In your reducer, handle different actions by setting the action type to `LanguageActionTypes`:

```tsx
import i18n from "i18next";
import { CHANGE_LANGUAGE, LanguageActionTypes } from "./languageActions";

export interface LanguageState {
  language: "en" | "zh";
  languageList: { name: string; code: string }[];
}

const defaultState: LanguageState = {
  language: "en",
  languageList: [
    { name: "中文", code: "zh" },
    { name: "English", code: "en" },
  ],
};

export default (state = defaultState, action: LanguageActionTypes): LanguageState => {
  switch (action.type) {
    case CHANGE_LANGUAGE:
      i18n.changeLanguage(action.payload);
      return { ...state, language: action.payload };
    default:
      return state;
  }
};
```

### Usage in Components

1. Use `changeLanguageActionCreator` to create a strongly-typed action in your components:

```typescript
const menuClickHandler = (e: any) => {
  store.dispatch(changeLanguageActionCreator(e.key));
};
```

### Example Component

1. Here is how you might integrate everything in a sample component:

```tsx
import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { Menu } from "antd";
import { changeLanguageActionCreator } from "./languageActions";

const LanguageSwitcher: React.FC = () => {
  const dispatch = useDispatch();
  const language = useSelector((state: any) => state.language);

  const handleMenuClick = (e: any) => {
    dispatch(changeLanguageActionCreator(e.key));
  };

  return (
    <Menu onClick={handleMenuClick} selectedKeys={[language]}>
      <Menu.Item key="en">English</Menu.Item>
      <Menu.Item key="zh">中文</Menu.Item>
    </Menu>
  );
};

export default LanguageSwitcher;
```

# React-Redux Integration: Class and Function Components

This guide will walk you through the process of integrating React-Redux with both class and function components using modern best practices.

## Prerequisites

Before you start, make sure you have the React-Redux library installed. If not, you can install it using npm:

```bash
npm install react-redux
```

For TypeScript support, install the necessary types:

```bash
npm install @types/react-redux --save-dev
```

## React-Redux with Class Components

### Setting up the Provider

The `<Provider />` component makes the Redux store available to the rest of your app. Here’s how you set it up:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import store from "./redux/store";
import App from "./App";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>
);
```

### Connecting the Component

Use the `connect` function to connect your component to the Redux store. This involves defining `mapStateToProps` and `mapDispatchToProps` functions:

```tsx
import { connect } from "react-redux";
import { Dispatch } from "redux";
import { changeLanguageActionCreator } from "./redux/language/languageActions";
import { RootState } from "./redux/store";

const mapStateToProps = (state: RootState) => ({
  language: state.language,
  languageList: state.languageList,
});

const mapDispatchToProps = (dispatch: Dispatch) => ({
  changeLanguage: (code: "zh" | "en") => {
    const action = changeLanguageActionCreator(code);
    dispatch(action);
  },
});
```

### Modifying the Component

Modify the class component to receive props injected by `connect` and handle type definitions accordingly:

```tsx
import React from "react";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { withTranslation, WithTranslation } from "react-i18next";

class HeaderComponent extends React.Component<
  RouteComponentProps &
    WithTranslation &
    ReturnType<typeof mapStateToProps> &
    ReturnType<typeof mapDispatchToProps>
> {
  menuClickHandler = (e: any) => {
    this.props.changeLanguage(e.key);
  };

  render() {
    return (
      <div>
        <h1>{this.props.language}</h1>
        <button onClick={() => this.menuClickHandler({ key: 'en' })}>English</button>
        <button onClick={() => this.menuClickHandler({ key: 'zh' })}>中文</button>
      </div>
    );
  }
}

export const Header = connect(
  mapStateToProps,
  mapDispatchToProps
)(withTranslation()(withRouter(HeaderComponent)));
```

### Modifying the Store Type

Ensure your store is correctly typed to provide robust type checking and intellisense support:

```typescript
import { createStore } from "redux";
import languageReducer from "./redux/language/languageReducer";

const store = createStore(languageReducer);

export type RootState = ReturnType<typeof store.getState>;

export default store;
```

## React-Redux with Function Components

### Creating a hooks.ts File

Create a `hooks.ts` file to define custom hooks for accessing the Redux store:

```typescript
import { useSelector as useReduxSelector, TypedUseSelectorHook } from "react-redux";
import { RootState } from "./store";

export const useSelector: TypedUseSelectorHook<RootState> = useReduxSelector;
```

### Using useSelector and useDispatch

In functional components, use `useSelector` to access the state and `useDispatch` to dispatch actions:

```typescript
import React from "react";
import { useSelector } from "../../redux/hooks";
import { useDispatch } from "react-redux";
import { changeLanguageActionCreator } from "../../redux/language/languageActions";

export const Header: React.FC = () => {
  const language = useSelector((state) => state.language);
  const languageList = useSelector((state) => state.languageList);
  const dispatch = useDispatch();

  const menuClickHandler = (e: any) => {
    dispatch(changeLanguageActionCreator(e.key));
  };

  return (
    <div>
      <h1>{language}</h1>
      <button onClick={() => menuClickHandler({ key: 'en' })}>English</button>
      <button onClick={() => menuClickHandler({ key: 'zh' })}>中文</button>
    </div>
  );
};
```

In this setup, `useSelector` hooks access the Redux store state, and `useDispatch` dispatches actions. This approach simplifies state management in function components.

## Conclusion

This guide covers the integration of React-Redux with both class and function components using modern best practices. By following these steps, you can ensure a robust, type-safe, and scalable integration of Redux into your React application.

For more information and advanced usage, refer to the official [React-Redux documentation](https://react-redux.js.org/introduction/getting-started).

# Fetching Data with Axios

Axios is a popular HTTP client for making requests in JavaScript and TypeScript applications. It is particularly favored in modern front-end development for its ease of use, promise-based API, and compatibility with older browsers such as IE7. This guide covers the installation, usage, and best practices for using Axios, especially in a React environment.

## Installation

To install Axios, use the following command:

```bash
npm install axios
```

Alternatively, if you are using Yarn:

```bash
yarn add axios
```

## Basic Usage

### Performing GET Requests

Axios simplifies making HTTP GET requests. Here's a basic example:

```typescript
import axios from 'axios';

axios.get('https://api.example.com/data')
  .then(response => {
    console.log(response.data);
  })
  .catch(error => {
    console.error('Error fetching data:', error);
  });
```

### Performing POST Requests

Similarly, making a POST request is straightforward:

```typescript
import axios from 'axios';

const data = {
  key1: 'value1',
  key2: 'value2'
};

axios.post('https://api.example.com/data', data)
  .then(response => {
    console.log('Data posted successfully:', response.data);
  })
  .catch(error => {
    console.error('Error posting data:', error);
  });
```

## Example Usage in a React Component

Here is a comprehensive example of using Axios within a React component. This example demonstrates how to handle loading states, errors, and rendering fetched data.

```typescript
import React, { Component } from 'react';
import axios from 'axios';
import { Spin, Typography, Row } from 'antd';
import { withTranslation, WithTranslation } from 'react-i18next';
import ProductCollection from './ProductCollection';

interface State {
  loading: boolean;
  error: string | null;
  productList: any[];
}

class HomePageComponent extends Component<WithTranslation, State> {
  constructor(props: WithTranslation) {
    super(props);
    this.state = {
      loading: true,
      error: null,
      productList: []
    };
  }

  async componentDidMount() {
    try {
      const response = await axios.get('http://123.56.149.216:8080/api/productCollections');
      this.setState({
        loading: false,
        productList: response.data
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        this.setState({
          loading: false,
          error: error.message
        });
      }
    }
  }

  render() {
    const { t } = this.props;
    const { productList, loading, error } = this.state;

    if (loading) {
      return <Spin size="large" style={{ marginTop: 200, marginBottom: 200, marginLeft: 'auto', marginRight: 'auto', width: '100%' }} />;
    }

    if (error) {
      return <div>Error: {error}</div>;
    }

    return (
      <>
        <Row>
          <ProductCollection
            title={<Typography.Title level={3} type="warning">{t('home_page.hot_recommended')}</Typography.Title>}
            sideImage="path/to/sideImage1.jpg"
            products={productList[0]?.touristRoutes || []}
          />
          <ProductCollection
            title={<Typography.Title level={3} type="danger">{t('home_page.new_arrival')}</Typography.Title>}
            sideImage="path/to/sideImage2.jpg"
            products={productList[1]?.touristRoutes || []}
          />
          <ProductCollection
            title={<Typography.Title level={3} type="success">{t('home_page.domestic_travel')}</Typography.Title>}
            sideImage="path/to/sideImage3.jpg"
            products={productList[2]?.touristRoutes || []}
          />
        </Row>
      </>
    );
  }
}

export const HomePage = withTranslation()(HomePageComponent);
```

### Setting Default Headers

For headers that should be included in every request, you can set them globally in your `index.ts` or `index.js` file:

```typescript
import axios from 'axios';

axios.defaults.headers.common['x-icode'] = 'BF10F5C62A274A1C';
axios.defaults.baseURL = 'http://123.56.149.216:8080/api';
axios.defaults.timeout = 10000; // 10 seconds
```

### Handling Interceptors

Interceptors allow you to run your code or modify the request/response before they are handled by `then` or `catch`. This is useful for adding authorization tokens or logging responses.

```typescript
import axios from 'axios';

// Request Interceptor
axios.interceptors.request.use(
  config => {
    // Modify config before request is sent
    config.headers.Authorization = 'Bearer YOUR_TOKEN';
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response Interceptor
axios.interceptors.response.use(
  response => {
    // Any status code within the range of 2xx causes this function to trigger
    return response;
  },
  error => {
    // Any status codes outside the range of 2xx cause this function to trigger
    if (error.response.status === 401) {
      // Handle unauthorized error
    }
    return Promise.reject(error);
  }
);
```

## Error Handling

Handling errors properly ensures a better user experience. Here’s an example of how to handle errors with Axios:

```typescript
import axios from 'axios';

axios.get('https://api.example.com/data')
  .then(response => {
    console.log(response.data);
  })
  .catch(error => {
    if (axios.isAxiosError(error)) {
      console.error('Axios error:', error.message);
    } else {
      console.error('Unexpected error:', error);
    }
  });
```

# Redux vs MVC

## Introduction

### MVC (Model-View-Controller)

MVC is a design pattern commonly used for developing user interfaces. It divides an application into three interconnected components:

- **Model**: Manages the data and business logic.
- **View**: Handles the display of data.
- **Controller**: Manages the communication between the Model and the View.

### Redux

Redux is a predictable state container for JavaScript apps, commonly used with libraries like React for managing application state. It follows a unidirectional data flow architecture.

### Comparison

In MVC, managing state and render logic can become complex and difficult to maintain, especially as applications grow. Redux simplifies state management by providing a single source of truth and enforcing strict separation of concerns.

## Advantages of Redux over MVC

1. **Single Source of Truth**: The entire state of your application is stored in a single object tree within a single store.
2. **Predictable State Updates**: Actions and reducers make state transitions predictable.
3. **Easier Debugging**: Tools like Redux DevTools provide powerful capabilities to inspect every state and action.
4. **Middleware for Side Effects**: Middleware like Redux-Thunk and Redux-Saga manage asynchronous operations and side effects effectively.

## Best Practices

1. **Organize by Feature**: Instead of separating files by type (actions, reducers, etc.), organize them by feature for better maintainability.
2. **Immutable State**: Always return new objects from reducers to keep the state immutable.
3. **Normalized State Shape**: Avoid deeply nested state to simplify data manipulation and improve performance.
4. **Use Redux Toolkit**: Simplifies store setup and provides good defaults.

# Redux Store with Multiple Reducers

In a large application, it's common to split the reducer logic into multiple smaller reducers. These smaller reducers manage specific parts of the state and are combined into a single root reducer.

## Example: Redux Store with Multiple Reducers

```typescript
import { configureStore, combineReducers } from "@reduxjs/toolkit";
import languageReducer from "./language/languageReducer";
import recommendProductsReducer from "./recommendProducts/recommendProductsReducer";

const rootReducer = combineReducers({
  language: languageReducer,
  recommendProducts: recommendProductsReducer,
});

// Configure the store with the combined reducer
const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;

export default store;
```

## Using Selectors in React Components

Selectors are functions that extract specific pieces of state from the Redux store.

### Example: Using Selectors in a Component

```typescript
import { useSelector } from "react-redux";
import { RootState } from "./store";

const Header: React.FC = () => {
  const language = useSelector((state: RootState) => state.language.language);
  const languageList = useSelector((state: RootState) => state.language.languageList);

  return (
    <div>
      <h1>Current Language: {language}</h1>
      <ul>
        {languageList.map((lang) => (
          <li key={lang}>{lang}</li>
        ))}
      </ul>
    </div>
  );
};
```

# Redux-Thunk

Redux-Thunk is a middleware that allows Redux actions to handle asynchronous operations and side effects. It extends Redux's `dispatch` function to support function types, enabling more complex actions.

## Installation

First, install redux-thunk:

```bash
npm install redux-thunk
```

## Configuration

With Redux Toolkit, redux-thunk is included by default in the middleware pipeline. If you are using an older setup, you need to manually apply the middleware.

### Redux Toolkit Setup

```typescript
import { configureStore } from "@reduxjs/toolkit";
import rootReducer from "./reducers";

const store = configureStore({
  reducer: rootReducer,
});

export default store;
```

### Manual Setup (Without Redux Toolkit)

```typescript
import { createStore, applyMiddleware } from "redux";
import thunk from "redux-thunk";
import rootReducer from "./reducers";

const store = createStore(rootReducer, applyMiddleware(thunk));

export default store;
```

## Usage

To use Redux-Thunk, create action creators that return functions instead of action objects.

### Example: Thunk Action Creator

```typescript
import axios from "axios";
import { ThunkAction } from "redux-thunk";
import { RootState } from "../store";
import {
  fetchRecommendProductsStart,
  fetchRecommendProductsSuccess,
  fetchRecommendProductsFail,
} from "./actions";

export const fetchRecommendProducts = (): ThunkAction<void, RootState, unknown, any> => async (dispatch, getState) => {
  dispatch(fetchRecommendProductsStart());
  try {
    const { data } = await axios.get("http://example.com/api/products");
    dispatch(fetchRecommendProductsSuccess(data));
  } catch (error) {
    dispatch(fetchRecommendProductsFail(error));
  }
};
```

### Connecting Thunk Actions to Components

Dispatch the thunk action from your React component.

```typescript
import { useDispatch } from "react-redux";
import { useEffect } from "react";
import { fetchRecommendProducts } from "./actions";

const ProductList: React.FC = () => {
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(fetchRecommendProducts());
  }, [dispatch]);

  // Render component
};
```

# Redux Middleware

In Redux, middleware is a higher-order function that wraps the dispatch function, allowing you to execute code in between the action being dispatched and the action reaching the reducer. Middleware is commonly used for handling asynchronous actions, logging, error reporting, and more.

## Defining Middleware in Redux

Middleware in Redux can be defined using the following formula:

```typescript
const middleware = (store) => (next) => (action) => {
  // Middleware logic here
};
```

In this formula:

- `store` is the Redux store instance.
- `next` is the next middleware in the chain or the original `dispatch` function if the current middleware is the last one in the chain.
- `action` is the action being dispatched.

## Middleware Invocation

When an action is dispatched, the middleware will be invoked in the following manner:

```typescript
middleware(store)(next)(action);
```

This allows the middleware to interact with the `store`, perform operations before and after the action is dispatched, and then pass control to the next middleware or reducer.

## Example Middleware: Logging

Here's an example of a Redux middleware that logs the current state, the action being dispatched, and the state after the action has been dispatched:

```typescript
import { Middleware } from "redux";

export const actionLog: Middleware = (store) => (next) => (action) => {
  console.log("Current state:", store.getState());
  console.log("Dispatching action:", action);
  next(action);
  console.log("Next state:", store.getState());
};
```

In this example:

- Before the action is dispatched, the current state is logged.
- The action is then dispatched using `next(action)`.
- After the action is dispatched, the next state is logged.

## Using Middleware with Redux Toolkit

The `configureStore` function from Redux Toolkit simplifies the process of setting up middleware. Here is how you can add the `actionLog` middleware to your store:

```typescript
import { configureStore } from "@reduxjs/toolkit";
import rootReducer from "./reducers";
import { actionLog } from "./middlewares";

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(actionLog),
});
```

In this code:

- `getDefaultMiddleware` is a function provided by Redux Toolkit that returns the default list of middleware (like `redux-thunk`).
- The `concat` method is used to add the `actionLog` middleware to the list of default middleware.

## Asynchronous Actions with Middleware

Middleware is particularly useful for handling asynchronous actions. For example, the popular `redux-thunk` middleware allows you to write action creators that return a function instead of an action:

```typescript
import { ThunkAction } from "redux-thunk";
import { Action } from "redux";
import { RootState } from "./store";

// An example of an asynchronous action using redux-thunk
export const fetchUserData = (): ThunkAction<void, RootState, unknown, Action<string>> => async (dispatch) => {
  dispatch({ type: "FETCH_USER_REQUEST" });
  try {
    const response = await fetch("/api/user");
    const data = await response.json();
    dispatch({ type: "FETCH_USER_SUCCESS", payload: data });
  } catch (error) {
    dispatch({ type: "FETCH_USER_FAILURE", error });
  }
};
```

In this example:

- The `fetchUserData` action creator returns a function that performs an asynchronous fetch request.
- It dispatches different actions based on the success or failure of the request.

## Common Middleware Patterns

### Logging

Logging middleware can help you debug your Redux store by logging every action and state change:

```typescript
const logger: Middleware = (store) => (next) => (action) => {
  console.log('Dispatching:', action);
  let result = next(action);
  console.log('Next state:', store.getState());
  return result;
};
```

### Error Reporting

Error reporting middleware can catch errors in the dispatched actions and report them to an error tracking service:

```typescript
const errorReporter: Middleware = (store) => (next) => (action) => {
  try {
    return next(action);
  } catch (err) {
    console.error('Caught an exception!', err);
    // Report the error to an external service
    throw err;
  }
};
```

### Async Operations

Handling async operations, such as data fetching, is another common use case for middleware:

```typescript
const asyncMiddleware: Middleware = (store) => (next) => async (action) => {
  if (typeof action === 'function') {
    return action(store.dispatch, store.getState);
  }
  return next(action);
};
```

# HATEOAS: Hypertext As The Engine Of Application State

HATEOAS (Hypertext As The Engine Of Application State) is a constraint of the REST application architecture that implies that a client interacts with a network application entirely through hypermedia provided dynamically by application servers.

## Key Concepts

### Hypermedia Driven

HATEOAS allows the client to navigate the application state through hypermedia (links), making the client less dependent on the server's implementation. This means that the server provides all the information the client needs to understand how to interact with the application.

### Example Scenario

Consider an e-commerce application where a client makes a POST request to buy a product. The server should return not only the status of the request but also links (URLs) to:

- Get the details of the product.
- Cancel the purchase.
- Update the purchase details.

This way, the client does not need to hard-code these URLs; they are provided dynamically by the server. This decouples the client from the server and makes the application more flexible and easier to maintain.

### Implementation in React

If the backend returns an HTML string directly, you can insert it into a React component using the following code:

```typescript
<div dangerouslySetInnerHTML={{ __html: data }}></div>
```

**Note**: Be cautious when using `dangerouslySetInnerHTML` as it can expose your application to XSS (Cross-Site Scripting) attacks. Always sanitize the HTML content before inserting it.

# Redux Toolkit (RTK)

Redux Toolkit (RTK) is the official, recommended way to write Redux logic. It is designed to simplify common tasks like store setup, defining reducers, and handling immutable updates.

## Creating an App with RTK

You can create a new React app with Redux Toolkit using the following commands:

```sh
# Redux + Plain JS template
npx create-react-app my-app --template redux

# Redux + TypeScript template
npx create-react-app my-app --template redux-typescript
```

To install Redux Toolkit in an existing project, run:

```sh
npm install @reduxjs/toolkit
```

## createSlice

The `createSlice` function is the standard approach for writing Redux logic. It accepts an initial state, an object of reducer functions, and a "slice name", and automatically generates action creators and action types.

### Example Usage

Here's an example of how to use `createSlice`:

```typescript
import { createSlice, createAction, configureStore } from "@reduxjs/toolkit";
import { combineReducers } from "redux";

// Define actions using createAction
const incrementBy = createAction<number>("incrementBy");
const decrementBy = createAction<number>("decrementBy");

// Create a counter slice
const counterSlice = createSlice({
  name: "counter",
  initialState: 0,
  reducers: {
    increment: (state) => state + 1,
    decrement: (state) => state - 1,
    multiply: {
      reducer: (state, action) => state * action.payload,
      prepare: (value = 2) => ({ payload: value }), // default value is 2
    },
  },
  extraReducers: (builder) => {
    builder.addCase(incrementBy, (state, action) => state + action.payload);
    builder.addCase(decrementBy, (state, action) => state - action.payload);
  },
});

// Create a user slice
const userSlice = createSlice({
  name: "user",
  initialState: { name: "", age: 20 },
  reducers: {
    setUserName: (state, action) => {
      state.name = action.payload; // Using Immer to handle state mutations
    },
  },
  extraReducers: {
    [counterSlice.actions.increment.type]: (state) => {
      state.age += 1;
    },
  },
});

// Combine reducers
const rootReducer = combineReducers({
  counter: counterSlice.reducer,
  user: userSlice.reducer,
});

// Configure store
const store = configureStore({
  reducer: rootReducer,
  devTools: process.env.NODE_ENV !== 'production', // Enable Redux DevTools only in development
});

store.dispatch(counterSlice.actions.increment());
store.dispatch(counterSlice.actions.multiply(3));
store.dispatch(userSlice.actions.setUserName("Alice"));

console.log(store.getState());
```

## configureStore

The `configureStore` function simplifies the setup process for the Redux store. It is strongly recommended over the traditional `createStore` method.

### Options

The `configureStore` function accepts an options object with the following properties:

- **reducer**: A single reducer function or an object of slice reducers.
- **middleware**: An array of middleware functions or a function that returns the middleware array.
- **devTools**: A boolean or configuration object for Redux DevTools.
- **preloadedState**: The initial state.
- **enhancers**: Additional store enhancers.

### Example Usage

Here's an example of how to configure a Redux store:

```typescript
import { configureStore } from "@reduxjs/toolkit";
import { combineReducers } from "redux";
import logger from 'redux-logger';

const rootReducer = combineReducers({
  counter: counterSlice.reducer,
  user: userSlice.reducer,
});

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(logger),
  devTools: process.env.NODE_ENV !== 'production', // Enable Redux DevTools only in development
});

export type RootState = ReturnType<typeof store.getState>;
export default store;
```

## createAsyncThunk

The `createAsyncThunk` function simplifies handling asynchronous logic. It accepts a Redux action type string and a callback function that returns a promise. It generates promise lifecycle action types based on the provided action type prefix.

### Example Usage

Here's an example of how to use `createAsyncThunk`:

```typescript
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";

interface ProductDetailsState {
  loading: boolean;
  error: string | null;
  data: any;
}

const initialState: ProductDetailsState = {
  loading: false,
  error: null,
  data: null,
};

export const fetchProductDetails = createAsyncThunk(
  "productDetails/fetchProductDetails",
  async (productId: string) => {
    const response = await axios.get(`/api/products/${productId}`);
    return response.data;
  }
);

const productDetailsSlice = createSlice({
  name: "productDetails",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchProductDetails.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProductDetails.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
        state.error = null;
      })
      .addCase(fetchProductDetails.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export const { reducer: productDetailsReducer } = productDetailsSlice;
```

### Using in a Component

To use the `fetchProductDetails` thunk in a React component:

```typescript
import React, { useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { fetchProductDetails } from "./productDetailsSlice";
import { RootState } from "./store";

const ProductDetails = ({ productId }: { productId: string }) => {
  const dispatch = useDispatch();
  const { data, loading, error } = useSelector(
    (state: RootState) => state.productDetails
  );

  useEffect(() => {
    if (productId) {
      dispatch(fetchProductDetails(productId));
    }
  }, [productId, dispatch]);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error}</p>;

  return <div>{data && <p>{data.name}</p>}</div>;
};

export default ProductDetails;
```

### Custom useDispatch Hook

To handle type conflicts between `ReduxAsyncThunk` and `any` type at `const dispatch = useDispatch();`, define a custom hook for `useDispatch`:

```typescript
import { useDispatch as useReduxDispatch } from "react-redux";
import { AppDispatch } from "./store";

export const useDispatch = () => useReduxDispatch<AppDispatch>();
```

Then, import `useDispatch` from this custom hook file instead of directly from `react-redux`.
