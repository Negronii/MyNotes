## Create React App with TypeScript Template

To create a React app with the TypeScript template, use the following command:

```
npx create-react-app react-ts --template typescript
```

To enable TypeScript to accept the `any` type, add `"noImplicitAny": false` in the `compilerOptions` section of your `tsconfig.json` file:

```json
{
    "compilerOptions": {
        "noImplicitAny": false,
         ...
    }
}
```

## Component in TypeScript

Here's an example of a component written in TypeScript:

```tsx
import React from 'react';

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

Notes:
- `React.FC` is a function component type that allows TypeScript to handle input props.
- It's recommended to define the type of `React.FC` using an interface (e.g., `RobotProps`), so that we can access attributes in the `props` object using destructuring.


## Example of using component in App.tsx

```tsx
import React from 'react';
import robots from './mockData/robots.json';
import Robot from "./components/robots";

export default function App() {
  return (
    <ul>
      {robots.map(r => (
        <Robot id={r.id} email={r.email} name={r.name} />
      ))}
    </ul>
  );
}
```

Note: Use the `.map()` function to access all elements.

## CSS in TypeScript

CSS files should always be in the same directory as the `.tsx` file.
Naming: `<tsx file name>.module.css`

How to use:

Not suggested:
```tsx
import './<file name>.module.css';
```

However, we do not want the CSS styles to be global, as it breaks modules.

Recommended:
```tsx
import styles from './<file name>.module.css';
```

Now we will see TypeScript showing an error. We need to declare CSS files for TypeScript. Create a file called `custom.d.ts` and add the following code to declare:

```tsx
declare module "*.css" {
  const css: {
    [key: string]: string;
  };
  export default css;
}
```

Then go back to the `.tsx` file, and we can use stuff like `<div className={styles.app}>` to add styles. For style class names with a hyphen (`-`), we need to access them using `<div className={styles['app-style']}>`.

## Media import

Recommended project structure:
Have an "assets" directory inside the "src" directory to store media files.
In the assets directory, we prefer to classify assets by type, e.g., "images", "fonts", "icons".

Import media in JavaScript:

```tsx
import logo from './logo.svg';
```

Note that image types such as `.svg`, `.jpg`, `.jpeg`, `.png` are declared in `react-app.d.ts`, so we do not need to declare them.

Import `.ttf` fonts:

1. Find/download the font file and put it in `assets/fonts`. It should be `<fontname>.ttf`.
2. Then go to `index.css` to add global styles. Assuming the font name is "Slidefu":

```css
@font-face {
  font-family: "Slidefu";
  src: local("Slidefu"), url("./assets/fonts/Slidefu-Regular-2.ttf") format("truetype");
}
```

3. Then we can use the font in all CSS files. For example, we go to `app.module.css` and add:

```css
h1 {
  font-family: "Slidefu";
  font-size: 72px;
}
```

# Class in TypeScript

`React.Component` takes 3 parameters: `props`, `state`, and an optional self-defined data.

Example:

```tsx
import React from "react";
import styles from "./ShoppingCart.module.css";

interface Props {}

interface State {
    ishidden: boolean; // This is an attribute we defined, true when the cart is hidden
}

export default class ShoppingCart extends React.Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            ishidden: false,
        };
    }

    render() {
        return (
            <div className={styles.cartContainer}>
                <button
                    className={styles.button}
                    onClick={() => {
                        this.setState({ ishidden: !this.state.ishidden });
                    }}
                >
                    Cart (2)
                </button>
                <div
                    className={styles.cartDropDown}
                    style={{ display: this.state.ishidden ? "none" : "block" }}
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

Simply add `<ShoppingCart />` in `app.tsx` to use the component.

# State vs Props in Component class

- Props is an external interface, whereas state is an internal interface.
- Props is used to pass data between components, while using state is for passing data inside a component.
- State can be seen as a private attribute of the component object. It is read-only, so we need to use `setState()` to update it. When `setState()` is invoked, React will render the component again.
- The constructor function is the only way to initialize state.
- Note that `setState()` is an asynchronous operation, so using state immediately after calling `setState()` may lead to synchronization problems.
- Props provide data from the parent component to the child component, which aligns with the React concept of a single data stream.
- Props are read-only.
- Using props in `.tsx` files is the same as in `.jsx` files.

# Synchronization Problem in `setState()`

Since `setState()` is an asynchronous operation, to ensure that something happens after the operation, we can use the following syntax:

```tsx
this.setState(
    (prevState, prevProps) => {
        // <state object>
    },
    () => {
        // Callback function
        console.log(`count is ${this.state.count}`);
    }
);
```

The first parameter is a function that can have two parameters: `prevState` and `prevProps`, which represent the previous state and previous props, respectively.
The callback function will be called immediately after `setState()` is executed.

Example:

```tsx
<button
    onClick={() => {
        this.setState(
            (prevState, prevProps) => {
                return { count: prevState.count + 1 };
            },
            () => {
                console.log(`count is ${this.state.count}`);
            }
        );
    }}
>
    Click me
</button>
```

# Event Handling

## The "this" Pointing Problem

The following code inside a class will trigger an error because "this" points to the function `handleClick`, not the class instance, resulting in no `setState` method being available:

```tsx
handleClick(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) {
    // do something with this, e.g.
    this.setState({ ishidden: !this.state.ishidden });
}
```

However, we can use a pointer function to avoid this issue:

```tsx
handleClick = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    this.setState({ ishidden

: !this.state.ishidden });
};
```

## `e.target` and `e.currentTarget`

- `e.target` refers to the element on which the event is occurring.
- `e.currentTarget` refers to the element that has the event handler for the event.

For example, if a button element contains a span element with words, and the button has an `onClick` attribute, when clicking on the words, `e.target` will be the span element, and `e.currentTarget` will be the button.

To distinguish the target, you can use:

```tsx
if ((e.target as HTMLElement).nodeName === "SPAN") {
    // do something, e.g. this.setState({ishidden: !this.state.ishidden})
}
```

# Request Data

`componentDidMount()` is invoked immediately after a component is mounted (inserted into the tree).

# Hooks

Hooks help to monitor processes and add state to functional components. They allow you to "hook" external code when the process requires side effects. Using hooks, you can substitute class components with functional components. Here are some frequently used hooks:

- `useState`: Manages state in a functional component.
- `useEffect`: Performs side effects in a functional component.
- `useReducer`: Manages state with complex logic.
- `useContext`: Accesses context in a functional component.

Note that all hooks are named using the `useXXX` convention.

## useState & useEffect

```jsx
import React, { useState, useEffect } from 'react';

const App: React.FC = (props) => {
  const [count, setCount] = useState<number>(0);
  const [robotGallery, setRobotGallery] = useState<any[]>([]);

  // Update document title when count changes
  useEffect(() => {
    document.title = `Clicked ${count} times`;
  }, [count]);

  // Fetch robot gallery data when component mounts
  useEffect(() => {
    fetch("https://jsonplaceholder.typicode.com/users")
      .then(result => result.json())
      .then(data => setRobotGallery(data));
  }, []);

  return (
    <div className={styles.app}>
      <button onClick={() => {
        setCount(count + 1);
      }}>
        Click me
      </button>
      <span>Count is {count}</span>
      <ShoppingCart />
      <div className={styles.robotList}>
        {robotGallery.map(r => (
          <Robot key={r.id} id={r.id} email={r.email} name={r.name} />
        ))}
      </div>
    </div>
  );
};

export default App;
```

## Use `await`/`async` in useEffect

You can define an async function inside `useEffect` and call it. Here's an example:

```jsx
useEffect(() => {
  const setData = async () => {
    const response = await fetch("https://jsonplaceholder.typicode.com/users");
    const data = await response.json();
    setRobotGallery(data);
  };

  setData();
}, []);
```

This is equivalent to the following code:

```jsx
useEffect(() => {
  fetch("https://jsonplaceholder.typicode.com/users")
    .then(result => result.json())
    .then(data => setRobotGallery(data));
}, []);
```

## Adding loading and error state

To add loading and error states, you can define the following state variables:

```jsx
const [loading, setLoading] = useState<boolean>(false);
const [error, setError] = useState<String>();
```

Before fetching data, set `loading` to `true`, and after setting the data, set `loading` back to `false`. Use a try-catch block to handle errors:

```jsx
useEffect(() => {
  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await fetch("https://jsonplaceholder.typicode.com/users");
      const data = await response.json();
      setRobotGallery(data);
      setLoading(false);
    } catch (e) {
      if (e instanceof Error) {
        setError(e.message);
      }
      setLoading(false);
    }
  };

  fetchData();
}, []);
```

## Conditional rendering

You can conditionally render components based on the loading and error states:

```jsx
{(!error || error !== "") && <div>Error: {error}</div>}

{!loading ? (
  <div className={styles.robotList}>
    {robotGallery.map(r => (
      <Robot key={r.id} id={r.id} email={r.email} name={r.name} />


    ))}
  </div>
) : (
  <h2>Loading</h2>
)}
```

## Context and useContext

To pass a parameter, we may use props to pass attributes to child nodes. However, if we want to share the props with child nodes of a child node, the complexity of rendering increases.

To create a context:
```typescript
const defaultContextValue = {
    username: "Ron"
}

export const appContext = createContext(defaultContextValue)
```

Use `createContext(<defined context value>)` to create the context, and then export it so that other `.tsx` files can import it.

To use the context in child nodes, wrap the desired child nodes with `<appContext.Provider value={defaultContextValue}></appContext.Provider>`.

In the child component, import the context:
```typescript
import { appContext } from "../index";
```

Declare `const value = useContext(appContext)`, and then `value.username = "Ron"` as expected.

If the component is not a functional component (e.g., a component class), we can let it render as follows:
```typescript
<appContext.Consumer>
  {value => {
    return ( /*elements*/ )
  }}
</appContext.Consumer>
```
Where `value` is the same as before.

## Example:

index.tsx:
```typescript
const defaultContextValue = {
    username: "Ron"
}

export const appContext = createContext(defaultContextValue)

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <appContext.Provider value={defaultContextValue}>
      <App />
    </appContext.Provider>
  </React.StrictMode>
);
```

Robots.tsx (where Robot is a child component of `<App />`):
```typescript
interface RobotProps {
    id: number,
    name: string,
    email: string
}

const Robot: React.FC<RobotProps> = ({id, name, email}) => {
    const value = useContext(appContext)
    return (
        <div className={styles.cardContainer}>
            <img alt="robot" src={`https://robohash.org/${id}`}/>
            <h2>{name}</h2>
            <p>{email}</p>
            <p>username: {value.username}</p>
        </div>
    )
}

export default Robot;
```

## Making context a component to manage global state

**Example AppState.tsx**
```typescript
import React, { createContext, PropsWithChildren, useState } from "react";

interface AppStateValue {
  username: string;
  shoppingCart: { items: { id: number; name: string }[] };
}

const defaultContextValue: AppStateValue = {
  username: "Ron",
  shoppingCart: { items: [] },
};

export const appContext = createContext(defaultContextValue);

// we can get the type by hovering mouse on setState
export const setStateContext = createContext<
  React.Dispatch<React.SetStateAction<AppStateValue>> | undefined
>(undefined);

// PropsWithChildren: the type of props in React.FC
// currently we don't have props, therefore leave the generic {}
export const AppStateProvider: React.FC<PropsWithChildren<{}>> = (props) => {
  const [state, setState] = useState(defaultContextValue);
  return (
    <appContext.Provider value={state}>
      {/*if some children need multiple contexts, just wrap one with another*/}
      <setStateContext.Provider value={setState}>
        {props.children}
      </setStateContext.Provider>
    </appContext.Provider>
  );
};
```

In `index.tsx`, we import and wrap the app in the `AppStateProvider` component:
```tsx
<AppStateProvider>
  <App />
</AppStateProvider>
```

In `robot.tsx`, we define a function to handle adding items to the cart:
```tsx
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
```

In `shoppingCart.tsx`, we use `appContext.Consumer` to wrap all elements within a function with a `value` parameter:
```tsx
<appContext.Consumer>
  {(value) => (
    <div className={styles.cartContainer}>
      <button className={styles.button} onClick={this.handleClick}>
        <FiShoppingCart />
        <span>Cart ({value.shoppingCart.items.length})</span>
      </button>
      <div
        className={styles.cartDropDown}
        // conditional render
        style={{ display: this.state.isHidden ? "none" : "block" }}
      >
        <ul>
          {value.shoppingCart.items.map((i) => (
            <li key={i.id}>{i.name}</li>
          ))}
        </ul>
      </div>
    </div>
  )}
</appContext.Consumer>
```

### HOC - Higher Order Component
- HOC is a function that returns a component.
- It can add functions to child components by wrapping them.
- It takes a component as input and outputs the component with added features.
- It helps with code/component reuse, conditional rendering, rendering logic, and catching component lifecycle.
- Naming convention: HOCs are typically defined starting with 'with', e.g., `withAddToCart`.
- Example:

```jsx
// addToCart.tsx
export const withAddToCart = (ChildComponent: React.ComponentType<RobotProps>) => {
    return props => {
        const setState = React.useContext(setStateContext);

        const addToCart = (id, name) => {
            if (setState) {
                setState(prevState => {
                    return {
                        ...prevState,
                        shoppingCart: {
                            items: [...prevState.shoppingCart.items, {id, name}]
                        }
                    };
                });
            }
        };

        // Then we pass the addToCart function to both components using props
        return <ChildComponent {...props} addToCart={addToCart}></ChildComponent>;
    };
}

// robot.tsx
export interface RobotProps {
    id: number,
    name: string,
    email: string,
    // Added addToCart in props type
    addToCart: (id, name) => void
}

const Robot: React.FC<RobotProps> = ({id, name, email, addToCart}) => {
    const value = useContext(appContext);

    return (
        <div className={styles.cardContainer}>
            <img alt="robot" src={`https://robohash.org/${id}`}/>
            <h2>{name}</h2>
            <p>{email}</p>
            <p>username: {value.username}</p>
            <button onClick={() => addToCart(id, name)}>Add to cart</button>
        </div>
    );
}

export default withAddToCart(Robot);

// robotDiscount.tsx
const RobotDiscount: React.FC<RobotProps> = ({id, name, email, addToCart}) => {
    const value = useContext(appContext);

    return (
        <div className={styles.cardContainer}>
            <img alt="robot" src={`https://robohash.org/${id}`}/>
            <h2>Discount good</h2>
            <h2>{name}</h2>
            <p>{email}</p>
            <p>username: {value.username}</p>
            <button onClick={() => addToCart(id, name)}>Add to cart</button>
        </div>
    );
}

export default withAddToCart(RobotDiscount);
```

### Customize and Define a Hook
- A hook should be named starting with 'use', e.g., `useAddToCart`.
- Example using a hook to achieve the functionality mentioned above:

```jsx
// addToCart.tsx
export const useAddToCart = () => {
    const setState = React.useContext(setStateContext);

    const addToCart = (id, name) => {
        if (setState) {
            setState(prevState => {
                return {
                    ...prevState,
                    shoppingCart: {
                        items: [...prevState.shoppingCart.items, {id, name}]
                    }
                };
            });
        }
    };

    return addToCart;
}

// robot.tsx
export interface RobotProps {
    id: number,
    name: string,
    email: string,
}

const Robot: React.FC<RobotProps> = ({id, name, email}) => {
    const value = useContext(appContext);
    const addToCart = useAddToCart();

    return (
        <div className={styles.cardContainer}>
            <img alt

="robot" src={`https://robohash.org/${id}`}/>
            <h2>{name}</h2>
            <p>{email}</p>
            <p>username: {value.username}</p>
            <button onClick={() => addToCart(id, name)}>Add to cart</button>
        </div>
    );
}

export default Robot;
```


## Simplified import using index.tsx
![Screenshot](src_screenshot.png)

In the `/footer` and `/header` directories, the `index.ts` files contain the following code:
```typescript
export * from './Header';
export * from './Footer';
```

In the `/component` directory, the `index.ts` file contains:
```typescript
export * from './header';
export * from './footer';
```

To use them in `App.tsx`, we can import `Header` and `Footer` like this:
```typescript
import { Header, Footer } from './components';
```

## Ant Design
To use Ant Design, you need to install the package and the icons by running the following command:
```bash
npm install antd @ant-design/icons
```

After installation, you can visit the [Ant Design Components Overview](https://ant.design/components/overview) for examples on how to use different components such as Layout, Typography, Input, Menu, Button, Dropdown, and the GlobalOutlined icon. You can also refer to the `Header.tsx` file in the ReactTravel project for an example.



# react-router
A package that supports routing in react. Routing refers to managing UI by tracking the URL, for example, showing search results when the URL is localhost:3000/search.

To install react-router, use the following command:
```
npm install react-router-dom@latest
```

- `<Link>` can render an `<a>` element.
- `<BrowserRouter>` implements router switch using the HTML5 API.
- `<HashRouter>` implements router switch using `window.location.hash`.

## Route by URL
Example: Display the `HomePage` component when the URL path is '/', `LoginPage` when it is 'login', and so on. Show a "page not found" message if the URL does not match any defined routes.

```jsx
import { BrowserRouter, Routes, Route } from "react-router-dom";

function App() {
    return (
        <div className={styles['App']}>
            <BrowserRouter>
                <Routes>
                    <Route path={'/'} element={<HomePage/>}></Route>
                    <Route path={'/login'} element={<LoginPage/>}></Route>
                    <Route path={'/register'} element={<RegisterPage/>}></Route>
                    <Route path={'/detail/:touristRouteId/:other'} element={<DetailPage/>}></Route>
                    <Route path={'*'} element={<h1>404 page not found, catch all</h1>}></Route>
                </Routes>
            </BrowserRouter>
        </div>
    );
}
```

## Passing parameter/s from URL
Example: Passing an ID as a parameter to the detail page.

In `app.tsx`:
```jsx
<Route path={'/detail/:touristRouteId'} element={<DetailPage/>}></Route>
```

In `details.tsx`:
```jsx
export const DetailPage: React.FC = () => {
    const params = useParams<"touristRouteId">();
    return (
        <h1>detail page, id: {params.touristRouteId}</h1>
    )
}
```

Example: Passing multiple parameters.

In `app.tsx`:
```jsx
<Route path={'/detail/:touristRouteId/:other'} element={<DetailPage/>}></Route>
```

In `details.tsx`:
```jsx
type MatchParams = {
    touristRouteId: string,
    other: string
}

export const DetailPage: React.FC = () => {
    const params = useParams<MatchParams>();
    return (
        <h1>detail page, id: {params.touristRouteId}, other: {params.other}</h1>
    )
}
```

Tip: `type` vs `interface`
In most cases, we can use both interchangeably. However, we can define a type like `type str = "str"`, but we cannot do the same with an interface.

## Navigation
Router navigation: `useNavigate()`

Example:
```jsx
import { useParams, useLocation, useNavigate } from "react-router-dom";

// Inside the functional component, use the hooks
const params = useParams();
const location = useLocation();
const navigate = useNavigate();

// This function is invoked by an onclick event, it can be shortened to () => navigate('/register')
function handleRegister() {
    // This will navigate from http://localhost:3000 to http://localhost:3000/register
    navigate('/register');
}
```

An alternative way is to use `<Link>` from `'react-router-dom'`:
```jsx
import { Link } from 'react-router-dom';

<Link to="/register">
    ...
</Link>
```

Both ways work, but `<Link>` is preferred as it is easier and shorter, and avoids adding an event to handle navigation

# Redux

All the data is stored in a 'store', and components subscribe to the store to retrieve the required data. The 'store' synchronously pushes data updates, similar to a publisher-subscriber system.

## Goal

The goal of Redux is to separate component data (state).

## When to use Redux?

Redux is used when:

- Components need to share data (state).
- There is a state that may be accessed from anywhere.
- Examples include language switch, dark mode switch, and globally shared user login data.

![Redux Architecture](reduce_architecture.png)

## Action

Actions are used to update data in the store.

## Reducer

Reducers are functions that help initialize, modify, and remove data in the store. They take the old state and the action as input and output the updated state to the store.

React components subscribe to the store.

If we want to modify data in the store, the component needs to use actions. Actions are sent to the store's middleware and then passed to the reducer. The reducer takes the old state and the action to update the data. This operation of sending actions is called 'dispatch'.

When the data is updated in reducers, the reducer publishes the updated data to components.

To install Redux, use the following command:
```
npm install redux
```

It's common to create a `/redux` folder in the `src` directory to manage all Redux files.

## Create Reducer

In `redux/languageReducer.ts`:

```typescript
interface LanguageState {
    language: 'en' | 'zh';
    languageList: { name: string; code: string }[];
}

const defaultState: LanguageState = {
    language: 'zh',
    languageList: [
        { name: "中文", code: 'zh' },
        { name: "English", code: 'en' }
    ]
};

// This is the reducer function, which takes the current state and an action to output the new state
export default (state = defaultState, action) => {
    if (action.type === "change_language") {
        const newState = { ...state, language: action.payload };
        return newState;
    }
};
```

## Create Store

```typescript
import { createStore } from "redux";
import languageReducer from "./languageReducer";

// createStore takes a reducer function as a parameter, so create the reducer first
const store = createStore(languageReducer);
export default store;
```

## Use Store in Class Component

```typescript
// Use store.getState() to set component state
constructor(props) {
    super(props);
    const storeState = store.getState();
    this.state = {
        language: storeState.language,
        languageList: storeState.languageList
    };
}
```

## Dispatch Action

Define the action name. Refer to [Redux documentation](https://redux.js.org/tutorials/fundamentals/part-3-state-actions-reducers#designing-actions) for more information on designing actions.

The action type is often set as an instruction name, e.g., "change_color", "set_username". Then, set the payload data to the store. Payload examples include "red" and "ruimingx".

Example:
```typescript
menuClickHandler = (e) => {
    const action = { type: "change_language", payload: e.key };
    store.dispatch(action);
};
```

# i18Next

Quick start guide: [link](https://react.i18next.com/guides/quick-start)

## Install

```bash
npm install react-i18next i18next --save
```

## Configuration

Create `configs.ts` file and import the necessary modules:

```typescript
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
```

Create language JSON files and import them into `configs.ts`:

```typescript
import translation_en from './en.json';
import translation_zh from './zh.json';
```

Copy the resources from the quick start website.