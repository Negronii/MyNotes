# React with JavaScript / React 与 JavaScript

This course moves from project setup and JSX to props, state, controlled forms, Effects, and browser storage. / 本课程从项目配置和 JSX 开始，依次介绍 props、state、受控表单、Effect 与浏览器存储。

**Core model / 核心模型：** A component describes UI from the props and state snapshot for one render. A state update asks React to render again; React then commits only the host changes that are needed. / 组件根据某次 render 中的 props 和 state 快照描述 UI。state 更新会请求 React 再次 render，之后 React 只提交必要的宿主界面变更。

**Key terms / 关键词：** element 元素 · component 组件 · props 属性 · state 状态 · render 渲染 · commit 提交 · controlled input 受控输入 · Effect 外部同步

**See also / 另见：** [React Basics / React基础](../../../../frontend/frameworks/react-basics.md) for identity, lifecycle, and error boundaries; [Advanced React / React进阶](../../../../frontend/frameworks/advanced-react.md) for Hooks and memoization conditions.

## Setting Up a React Application / 配置React应用

The commands below preserve the Create React App (CRA) workflow used by this course. CRA is a legacy setup and no longer promises the latest build configuration; use it to recognize existing CRA projects, and follow the current React project-start guide when choosing a new setup.

### Create React App / Create React App

To create a new React app, use the following commands:

```shell
npx create-react-app <app-name>
cd <app-name>
npm start
```

- `npx create-react-app <app-name>`: Initializes a new React project.
- `cd <app-name>`: Navigates into the project directory.
- `npm start`: Starts the development server, opening the app in your default browser.

### Example

```shell
npx create-react-app my-react-app
cd my-react-app
npm start
```

## Adding Dependencies as Development Tools

Dependencies required only during development, such as testing libraries or build tools, should be added as development dependencies.

Using npm:

```shell
npm install <package-name> --save-dev
```

Using yarn:

```shell
yarn add <package-name> --dev
```

### Example

```shell
npm install eslint --save-dev
```

## Removing Dependencies

To remove a dependency from your project:

Using npm:

```shell
npm uninstall <package-name>
```

Using yarn:

```shell
yarn remove <package-name>
```

### Example

```shell
npm uninstall eslint
```

## Creating and Rendering React Elements / 创建并渲染React元素

React elements are the building blocks of a React application. Here’s how you can create and render them.

## Basic Element Creation and Rendering

Assuming you have a `<div id="root"></div>` in your HTML:

```javascript
import React from "react";
import { createRoot } from "react-dom/client";

// Create a React element
const title = React.createElement("h1", null, "Hello React");

// Create a root from the DOM
const domContainer = document.getElementById("root");
const root = createRoot(domContainer);

// Render the title we just created
root.render(title);
```

## Using JSX

JSX is a syntax extension for JavaScript that looks similar to HTML. It is recommended for defining UI elements in React.

### Creating an Element with a Class Attribute

In HTML:

```html
<h1 class="header">This is a JSX</h1>
```

In JSX:

```jsx
<h1 className="header">This is a JSX</h1>
```

### Using Variables in JSX

```jsx
const welcomeMessage = "Welcome to JSX";
<h1 className="header">Message: {welcomeMessage}</h1>;
```

## JSX Structure

Organize your components into separate files for better maintainability.

### Example Component Structure

**Header.jsx**

```jsx
function Header() {
  return (
    <header>
      <h1>Hello</h1>
      <p>This is a JSX</p>
    </header>
  );
}

export default Header;
```

**index.jsx**

```jsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import Header from './components/Header';

function App() {
  return (
    <div>
      <Header />
      <h1>Reasons to Learn React</h1>
      <ol>
        <li>Highly Employable</li>
        <li>Great for Building High-Quality Web Applications</li>
      </ol>
    </div>
  );
}

const domContainer = document.getElementById('root');
const root = createRoot(domContainer);
root.render(<App />);
```

## Best Practices

1. **Component Naming**: Use PascalCase for component names (e.g., `Header`, `App`).
2. **File Structure**: Organize components into a `components` folder.
3. **Functional Components**: Prefer functional components over class components.
4. **Hooks**: Utilize React hooks for state management and side effects.
5. **Prop Types**: In React 18 and earlier, PropTypes provided development-time checks for component props. React 19 silently ignores function-component `propTypes`; use TypeScript or another type checker for current component APIs. Component prop checks do not automatically validate untrusted API responses; validate those separately when needed. See the [React 19 upgrade guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide#removed-proptypes-and-defaultprops-for-functions).

### Historical Example (React 18 and Earlier) / React 18及更早版本的历史示例

```jsx
import PropTypes from 'prop-types';

function Greeting({ message }) {
  return <h1>{message}</h1>;
}

Greeting.propTypes = {
  message: PropTypes.string.isRequired,
};

export default Greeting;
```

## JSX Syntax and Composition / JSX语法与组合

## Recommended JSX Formatting

1. **Use Parentheses for JSX**
   - Wrap HTML-like JSX code in parentheses for readability and to avoid automatic semicolon insertion issues.

2. **Functional Components**
   - Function components return React elements from their inputs. Choose them for their component API and composition, not as a memory-saving trick.
   - Use UpperCamelCase for component names, e.g., `NavItem`, `HeaderIntro`.

3. **Single Root Node**
   - A component can return one React node, including a fragment (`<>...</>`). A fragment groups siblings without adding a DOM wrapper; React also accepts arrays of nodes.

4. **Rendering Components**
   - Use JSX syntax to render components: `<ComponentName />`.
   - This is equivalent to `React.createElement(ComponentName, null)`.

5. **Component Composition**
   - Components can contain other components: `<ComponentName />`.

6. **Page Component Example**
   - For pages with many elements, create a parent `Page` component that contains other components:

    ```jsx
    function Page() {
      return (
        <div>
          <Header />
          <MainContent />
          <Footer />
        </div>
      );
    }
    ```

   - This improves the structure and maintainability of the project.

## Styling Images in JSX

- **Importing Images**
  - Direct use of paths in `src` might fail due to relative paths. Import images at the top of your file:

    ```javascript
    import reactLogo from "../images/react-icon.png";
    ```

  - Use the imported variable in the JSX:

    ```jsx
    <img src={reactLogo} alt="React Logo" />
    ```

## Adding JavaScript in JSX

- **Embedding JavaScript**
  - Use `{}` to embed JavaScript expressions within JSX:

    ```jsx
    const a = 10;
    <div>{a}</div>
    ```

  - Avoid complex expressions directly in JSX for better readability:

    ```jsx
    const date = new Date();
    const time = date.getHours() % 12;
    <div>It is {time} o'clock</div>
    ```

## Passing Parameters to Components (Component Reuse)

- **Passing Props**
  - Pass data to components using props:

    ```jsx
    <Header
      cat="cat"
      boolean={true}
      val={2}
      object={{ author: "Example", body: "hello" }}
    />
    ```

  - Access props within the component:

    ```jsx
    function Header(props) {
      return (
        <div>
          <h1>Hello, {props.cat}</h1>
          <p>This is a JSX {props.head}</p>
        </div>
      );
    }
    ```

  - Destructure props for cleaner code:

    ```jsx
    function Header({ head, cat }) {
      return (
        <div>
          <h1>Hello, {cat}</h1>
          <p>This is a JSX {head}</p>
        </div>
      );
    }
    ```

## Conditional Rendering

- **Render Only When a Property Exists**
  - Use short-circuit evaluation for conditional rendering:

    ```jsx
    export default function Joke({ setup }) {
      return <div>{setup && <h1>Render only when setup is true</h1>}</div>;
    }
    ```

  - Alternatively, use ternary operators for conditional styles:

    ```jsx
    <h1 style={{ display: props.setup ? "block" : "none" }}>
      Render only when setup is true
    </h1>
    ```

## JavaScript `.map()` Review

- **Array Mapping**
  - Use `.map()` to transform arrays:

    ```javascript
    const nums = [1, 2, 3, 4, 5];
    const squared = nums.map(item => item * item);
    ```

  - Access array indices:

    ```javascript
    const squared = nums.map((cur, index) => {
      // do something
    });
    ```

## Render Array in JSX

- **Rendering Arrays**
  - Map array elements to JSX:

    ```jsx
    const fruits = [{ color: "red", size: 15 }, { color: "orange", size: 10 }];
    const fruitElement = fruits.map(item => <Fruit key={item.color} color={item.color} size={item.size} />);

    export default function App() {
      return <div>{fruitElement}</div>;
    }
    ```

## HTML String with JavaScript String

- **Template Literals**
  - Use backticks for template literals to include JavaScript expressions:

    ```jsx
    <img src={`../images/${image}`} alt="Dynamic Image" />
    ```

## Object Spread Syntax

- **Spreading Props**
  - Use the spread operator to pass all properties of an object as props:

    ```jsx
    const fruits = [
      { color: "red", size: 15 },
      { color: "orange", size: 10 },
    ];
    const fruitElement = fruits.map(item => <Fruit key={item.color} {...item} />);

    export default function App() {
      return <div>{fruitElement}</div>;
    }
    ```

  - While convenient, explicit prop passing is more readable and preferred for clarity.

## Event Handlers / 事件处理器

- **Event Handling**
  - React uses camelCase for event handlers:

    ```jsx
    <button onClick={() => {}}>Button</button>
    <button onMouseEnter={() => {}}>Button</button>
    ```

  - Define event handler functions separately for cleaner code:

    ```jsx
    export default function App() {
      function handleClick() {
        // do something
      }
      return <button onClick={handleClick}>Button</button>;
    }
    ```

  - These are React event-handler props, not calls to `addEventListener`. See the [React common component events reference](https://react.dev/reference/react-dom/components/common#events).

## State in React / React中的State

Managing state in React is crucial for building dynamic and interactive applications. Let's explore how state works in React, including best practices and examples.

## State vs. Props

- **Props** are inputs supplied by a parent. A child should treat them as read-only rather than mutate them.
- **State** is React-managed data that can change over time. Treat objects and arrays stored in state as immutable and pass a replacement value to the setter.

## How to Use State

To use state in a React component, we utilize the `useState` hook.

```jsx
const [state, setState] = React.useState(initialValue);
```

- `state` is the current state value.
- `setState` is the function used to update the state.
- `initialValue` is the default state value.

### Example

```jsx
const [isImportant, setIsImportant] = React.useState("yes");

// Now `isImportant` is "yes," and `setIsImportant` is the function to update it.
```

### Naming Conventions

Use meaningful names for state variables and their setters.

```jsx
const [isImportant, setIsImportant] = React.useState(true);
```

### Updating State

To update the state, call the setter function with the new value.

```jsx
setIsImportant(false);
```

When the new value depends on the previous state, pass a function to the setter.

```jsx
setIsImportant(prevIsImportant => !prevIsImportant);
```

### Example: Counter

```jsx
const [count, setCount] = React.useState(0);

function increment() {
  setCount(prevCount => prevCount + 1);
}

function decrement() {
  setCount(prevCount => prevCount - 1);
}

return (
  <div>
    <button onClick={increment}>+</button>
    <h1>{count}</h1>
    <button onClick={decrement}>-</button>
  </div>
);
```

## Array State Example

Updating state when an array changes:

```jsx
const [thingsArray, setThingsArray] = React.useState(["Thing 1", "Thing 2"]);

function addItem() {
  setThingsArray(prevThingsArray => [...prevThingsArray, `Thing ${prevThingsArray.length + 1}`]);
}

const thingsElements = thingsArray.map(thing => <p key={thing}>{thing}</p>);

return (
  <div>
    <button onClick={addItem}>Add Thing</button>
    {thingsElements}
  </div>
);
```

## Modifying a Property in a State Object

Updating a nested property in a state object:

```jsx
const [contact, setContact] = React.useState({
  firstName: "Alex",
  lastName: "Example",
  isFavorite: true,
});

function toggleFavorite() {
  setContact(prevContact => ({
    ...prevContact,
    isFavorite: !prevContact.isFavorite,
  }));
}
```

## State Feature: Rendering After an Update / State更新后的渲染

A state setter schedules a render using the next state snapshot. React may call descendant components while producing the next tree, but a render does not guarantee a DOM change; React commits only the changes required by the result.

## Child Component Updating Parent's State

Passing a function from a parent to a child component allows the child to update the parent's state.

### Example

In `App.js`:

```jsx
const [isImportant, setIsImportant] = React.useState(true);

function toggleImportant() {
  setIsImportant(prevIsImportant => !prevIsImportant);
}

return <ChildComponent handleClick={toggleImportant} />;
```

In `ChildComponent.js`:

```jsx
export default function ChildComponent({ handleClick }) {
  return <button onClick={handleClick}>Toggle Important</button>;
}
```

## Passing State/Data Between Siblings

State cannot be passed directly between sibling components. Instead, lift the shared state up to the closest common ancestor and pass it down as props.

## Setting Style in React

In React, styles are defined using JavaScript objects and applied to elements using the `style` attribute.

```jsx
const styles = { backgroundColor: "black" };

return <div style={styles}></div>;
```

Conditional styles based on props:

```jsx
const styles = { backgroundColor: props.darkMode ? "black" : "white" };
```

## Find the Object in Array State

Identifying which child component called a function by passing a unique identifier.

### Example

In `App.js`:

```jsx
const [boxes, setBoxes] = React.useState([
  { id: 1, on: false },
  { id: 2, on: false },
  { id: 3, on: true },
]);

function toggleBox(id) {
  setBoxes(prevBoxes => 
    prevBoxes.map(box => 
      box.id === id ? { ...box, on: !box.on } : box
    )
  );
}

const boxesElements = boxes.map(box => (
  <Box key={box.id} id={box.id} on={box.on} toggle={toggleBox} />
));

return <div>{boxesElements}</div>;
```

In `Box.js`:

```jsx
export default function Box({ id, on, toggle }) {
  const styles = { backgroundColor: on ? "black" : "white" };

  return <div style={styles} onClick={() => toggle(id)}></div>;
}
```

## Conditional Rendering

Render components conditionally using logical operators or ternary operators.

### Logical AND Operator

```jsx
{condition && <Component />}
```

### Ternary Operator

```jsx
{condition ? <ComponentA /> : <ComponentB />}
```

### Example

```jsx
const [isShown, setIsShown] = React.useState(true);

return (
  <div>
    {isShown && <h1>Show content</h1>}
    <button onClick={() => setIsShown(prev => !prev)}>
      {isShown ? "Hide" : "Show"}
    </button>
  </div>
);
```

## Forms and Inputs in React

Handling forms and inputs with state in React:

```jsx
import React from "react";

export default function Form() {
  const [formData, setFormData] = React.useState({
    firstName: "",
    lastName: "",
    email: "",
    comment: "",
    isFriendly: true,
    employment: "",
    favColor: "",
  });

  function handleChange(e) {
    const { name, value, type, checked } = e.target;
    setFormData(prevFormData => ({
      ...prevFormData,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    console.log(formData); // Handle form submission logic
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="firstName">First name</label>
      <input
        type="text"
        id="firstName"
        placeholder="First Name"
        onChange={handleChange}
        name="firstName"
        value={formData.firstName}
      />
      <label htmlFor="lastName">Last name</label>
      <input
        type="text"
        id="lastName"
        placeholder="Last Name"
        onChange={handleChange}
        name="lastName"
        value={formData.lastName}
      />
      <label htmlFor="email">Email</label>
      <input
        type="email"
        id="email"
        placeholder="Email"
        onChange={handleChange}
        name="email"
        value={formData.email}
      />
      <label htmlFor="comment">Comment</label>
      <textarea
        id="comment"
        placeholder="Comment"
        onChange={handleChange}
        name="comment"
        value={formData.comment}
      />
      <input
        type="checkbox"
        id="isFriendly"
        checked={formData.isFriendly}
        onChange={handleChange}
        name="isFriendly"
      />
      <label htmlFor="isFriendly">Are you friendly?</label>
      <fieldset>
        <legend>Current employment status</legend>
        <input
          type="radio"
          id="unemployed"
          name="employment"
          value="unemployed"
          checked={formData.employment === "unemployed"}
          onChange={handleChange}
        />
        <label htmlFor="unemployed">Unemployed</label>
        <input
          type="radio"
          id="full-time"
          name="employment"
          value="full-time"
          checked={formData.employment === "full-time"}
          onChange={handleChange}
        />
        <label htmlFor="full-time">Full-time</label>
        <input
          type="radio"
          id="part-time"
          name="employment"
          value="part-time"
          checked={formData.employment === "part-time"}
          onChange={handleChange}
        />
        <label htmlFor="part-time">Part-time</label>
      </fieldset>
      <label htmlFor="favColor">What is your favorite color?</label>
      <select
        id="favColor"
        value={formData.favColor}
        onChange={handleChange}
        name="favColor"
      >
        <option value="">Choose a color</option>
        <option value="red">Red</option>
        <option value="blue">Blue</option>
        <option value="green">Green</option>
        <option value="yellow">Yellow</option>
      </select>
      <button type="submit">Submit</button>
    </form>
  );
}
```

In this form example, the state `formData` manages multiple inputs, including text fields, checkboxes, radio buttons, and a select dropdown. The `handleChange` function updates the state based on the input values. The `handleSubmit` function handles form submission, where you can add logic to send the form data to a backend.

## Fetching Data with Effects / 使用Effect获取数据

### Fetching Data (`fetch`, Axios)

These examples show a one-time request and a changing request. Check `response.ok` because `fetch` resolves for HTTP error statuses; when a dependency changes, clean up the previous request so an older response cannot replace newer state.

#### Using Fetch

The `fetch` API provides a simple interface for fetching resources. Here's an example of fetching data and storing it in a state:

```jsx
import React, { useEffect, useState } from 'react';

export default function Fetch() {
  const [starWarsData, setStarwarsData] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadPerson() {
      try {
        const response = await fetch("https://swapi.dev/api/people/1", {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        setStarwarsData(await response.json());
      } catch (cause) {
        if (!controller.signal.aborted) {
          setError(cause instanceof Error ? cause.message : String(cause));
        }
      }
    }

    loadPerson();
    return () => controller.abort();
  }, []);

  if (error) return <p role="alert">{error}</p>;
  return <div>{JSON.stringify(starWarsData, null, 2)}</div>;
}
```

#### Using Axios

`axios` is a popular HTTP client that offers a more powerful and flexible approach to making HTTP requests.

```jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function Fetch() {
  const [starWarsData, setStarwarsData] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;

    axios.get("https://swapi.dev/api/people/1")
      .then(response => {
        if (!ignore) setStarwarsData(response.data);
      })
      .catch(cause => {
        if (!ignore) setError(cause instanceof Error ? cause.message : String(cause));
      });

    return () => {
      ignore = true;
    };
  }, []);

  if (error) return <p role="alert">{error}</p>;
  return <div>{JSON.stringify(starWarsData, null, 2)}</div>;
}
```

#### Avoiding Infinite Loops and Stale Results / 避免循环与过期结果

When a request depends on changing state, clean up the previous synchronization so a slower, older response cannot overwrite the latest result:

```jsx
import React, { useEffect, useState } from 'react';

export default function Fetch() {
  const [starWarsData, setStarwarsData] = useState(null);
  const [error, setError] = useState(null);
  const [personId, setPersonId] = useState(1);

  useEffect(() => {
    let ignore = false;

    async function loadPerson() {
      try {
        const response = await fetch(`https://swapi.dev/api/people/${personId}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (!ignore) {
          setStarwarsData(data);
          setError(null);
        }
      } catch (cause) {
        if (!ignore) setError(cause instanceof Error ? cause.message : String(cause));
      }
    }

    loadPerson();
    return () => {
      ignore = true;
    };
  }, [personId]);

  return (
    <div>
      <button onClick={() => setPersonId(id => id + 1)}>Next person</button>
      {error && <p role="alert">{error}</p>}
      <pre>{JSON.stringify(starWarsData, null, 2)}</pre>
    </div>
  );
}
```

## Managing Side Effects with `useEffect` / 使用`useEffect`管理副作用

### What is a Side Effect?

A side effect is any operation that affects something outside the scope of the function being executed, such as:

- Modifying global variables
- Making API requests
- Manipulating the DOM
- Setting up subscriptions

### Using `useEffect` to Handle Side Effects

`useEffect` synchronizes a component with an external system after a commit. With no dependency list, it runs after each commit; with a dependency list, it re-runs when a listed value changes. Cleanup runs before the next setup and when the component unmounts. This example keeps the browser document title synchronized with state; use an event handler for work caused directly by a user action, and derive values during render instead of copying them into state.

```jsx
import React, { useEffect, useState } from 'react';

export default function PageTitle() {
  const [count, setCount] = useState(1);

  useEffect(() => {
    document.title = `You clicked ${count} times`;
  }, [count]);

  return (
    <div>
      <p>You clicked {count} times</p>
      <button onClick={() => setCount(previous => previous + 1)}>Increment</button>
    </div>
  );
}
```

### Cleaning Up Side Effects

Remove subscriptions and listeners during cleanup. For requests, cleanup can ignore stale results as above; it does not itself abort network traffic. Pass an `AbortSignal` when stopping the request is also required.

```jsx
import React, { useEffect } from 'react';

export default function WindowResizeListener() {
  useEffect(() => {
    function handleResize() {
      console.log('Window resized');
    }

    window.addEventListener('resize', handleResize);

    // Cleanup function to remove the event listener
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []); // Empty dependency array ensures this runs only once

  return <div>Resize the window and check the console log</div>;
}
```

## Using Local Storage / 使用Local Storage

Local storage is a way to store data on the client's browser. Here are some best practices for using local storage in modern web development:

`localStorage` is available only in a browser. This lazy initializer assumes a browser-only app; in server-rendered apps, read storage after hydration and keep the server and initial client render consistent. `JSON.parse` can also throw if stored text is malformed.

### Storing and Retrieving Data

```jsx
import React, { useEffect, useState } from 'react';

export default function LocalStorageExample() {
  const [data, setData] = useState(() => {
    const savedData = localStorage.getItem('myData');
    return savedData ? JSON.parse(savedData) : {};
  });

  useEffect(() => {
    localStorage.setItem('myData', JSON.stringify(data));
  }, [data]);

  return (
    <div>
      <button onClick={() => setData({ ...data, newKey: 'newValue' })}>
        Add Data
      </button>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
```

### Notes on Local Storage

- Data stored in local storage must be a string. Use `JSON.stringify` to store objects or arrays.
- Use `JSON.parse` to retrieve and convert the string back to its original format.

In React 18+ and 19, a root wrapped in `<React.StrictMode>` gets an extra Effect setup-and-cleanup cycle in development. This check is absent in production; it exposes missing cleanup, while any network request already sent still needs an abort signal if it must be stopped.

**Sources checked 2026-10-15:** [React: Start a New React Project](https://react.dev/learn/start-a-new-react-project), [Render and Commit](https://react.dev/learn/render-and-commit), [State as a Snapshot](https://react.dev/learn/state-as-a-snapshot), [Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects), [StrictMode](https://react.dev/reference/react/StrictMode), [Common DOM Component Events](https://react.dev/reference/react-dom/components/common#events), and [input](https://react.dev/reference/react-dom/components/input), [textarea](https://react.dev/reference/react-dom/components/textarea), and [select](https://react.dev/reference/react-dom/components/select) references. React behavior was checked against React 19.2 documentation; the Create React App section is retained as a legacy setup example.
