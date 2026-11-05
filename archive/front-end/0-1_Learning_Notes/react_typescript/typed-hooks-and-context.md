# How do typed Hooks and Context organize reusable React state? / 带类型的 Hook 与 Context 如何组织可复用 React 状态？

Hooks keep state and synchronization inside function components; Context exposes a value to a subtree, while a custom Hook packages reusable logic without sharing one state instance by itself. / Hook 在函数组件中管理状态与同步；Context 向子树提供值；自定义 Hook 封装可复用逻辑，但不会自动让多个调用共享同一份状态。

## Hooks / Hooks

Hooks let function components use React state, context, refs, and synchronization with external systems. They are an alternative component API, not a requirement to replace every class component. Common Hooks include:

- `useState`: Manages state in a functional component.
- `useEffect`: Performs side effects in a functional component.
- `useReducer`: Manages state with complex logic.
- `useContext`: Accesses context in a functional component.

Custom Hooks must start with `use`; they may call other Hooks at the top level. React 19's `use(usable)` API is the exception: it may appear in a condition or loop, while other Hooks must preserve call order. See [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks) and [`use`](https://react.dev/reference/react/use).

## `useState` / `useState`

The `useState` hook allows you to add state to functional components. It returns an array with two elements: the current state and a function to update it.

### Example

```tsx
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

## `useEffect` / `useEffect`

`useEffect` synchronizes with an external system after a commit. With no dependency list it runs after each commit; with a dependency list it runs after the initial commit and again when a listed value changes. React runs the previous cleanup before the next setup and when the component unmounts.

### Example

```tsx
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

## `useReducer` / `useReducer`

The `useReducer` hook is used for managing state with complex logic. It is an alternative to `useState` and is usually preferable when you have multiple state variables that rely on complex logic.

### Example

```tsx
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

## `useContext` / `useContext`

The `useContext` hook allows you to access the context in a functional component. It makes it easy to pass data through the component tree without passing props down manually at every level.

### Example

```tsx
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

1. **Keep Hooks at the Top Level**: Call Hooks at the top level of a component or custom Hook so their order is stable. The React 19 `use(usable)` API is the exception and may be called conditionally or in loops; see the Rules of Hooks link above.

2. **Use Multiple State Variables if Needed**: Instead of combining state variables, use multiple `useState` or `useReducer` calls.

3. **Optimize useEffect Dependencies**: Make sure the dependency array in `useEffect` is accurate to avoid unnecessary re-renders.

4. **Custom Hooks**: Create custom hooks to extract and reuse stateful logic across multiple components.

### Custom Hook Example

```tsx
import { useState, useEffect } from 'react';

const useFetch = (url: string) => {
  const [data, setData] = useState<unknown>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    setError(null);

    const fetchData = async () => {
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        if (!ignore) setData(result);
      } catch (e) {
        if (!ignore) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!ignore) setLoading(false);
      }
    };

    fetchData();
    return () => {
      ignore = true;
    };
  }, [url]);

  return { data, loading, error };
};

export default useFetch;
```

### Explanation

In the custom hook example above:
- `useFetch` encapsulates the logic for fetching data.
- It returns the fetched data, loading state, and any error encountered.

The cleanup ignores stale results when `url` changes or the component unmounts; it does not cancel the network request. Pass an `AbortSignal` when the underlying request must also be stopped. In React 18+ and 19, root StrictMode runs an additional Effect setup-and-cleanup cycle in development to expose incomplete cleanup; that development check is absent in production.

## Context and `useContext` / Context与`useContext`

### Introduction
Context provides a value to a subtree without passing it through every intermediate component. It can distribute shared state, but it does not itself define how that state is stored or updated; the provider owns that behavior.

### Creating Context

To create a context, you use the `createContext` function. This function takes an initial value and returns a context object.

```typescript
import { createContext } from "react";

const defaultContextValue = {
  username: "reader",
};

export const appContext = createContext(defaultContextValue);
```

Here, `defaultContextValue` is used only when a component has no matching provider above it in the tree.

### Providing Context

To use the context in child components, wrap the part of your component tree that needs access to the context with the `Provider` component of the context.

```tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { appContext } from "./context";

const defaultContextValue = {
  username: "reader",
};

const root = createRoot(document.getElementById("root") as HTMLElement);

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
  username: "reader",
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
import { createRoot } from "react-dom/client";
import { AppStateProvider } from "./AppState";
import App from "./App";

const root = createRoot(document.getElementById("root") as HTMLElement);

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

```tsx
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
- **Keep render pure**: Do not run side effects while rendering. A custom Hook may return an event handler or callback that updates state or performs another side effect when invoked; React allows side effects in event handlers and Effects. See [Components and Hooks must be pure](https://react.dev/reference/rules/components-and-hooks-must-be-pure) and [Responding to Events](https://react.dev/learn/responding-to-events).

#### Example
Here’s an example of a custom hook to handle adding items to a shopping cart:

```tsx
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

**Sources checked 2026-10-15:** React 19.2 [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks), [`use`](https://react.dev/reference/react/use), [Effects](https://react.dev/learn/synchronizing-with-effects), [StrictMode](https://react.dev/reference/react/StrictMode), and [React type definitions](https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/react/index.d.ts).
