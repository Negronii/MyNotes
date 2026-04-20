# Setting Up a React Application

To create a new React application, you can use the `create-react-app` tool, which sets up everything you need for a React project automatically. This tool ensures you have the latest build settings and configurations, making it easier to start coding right away.

## Create React App

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

# Creating and Rendering React Elements

React elements are the building blocks of a React application. Here’s how you can create and render them.

## Basic Element Creation and Rendering

Assuming you have a `<div id="root"></div>` in your HTML:

```javascript
// Create a React element
const title = React.createElement("h1", null, "Hello React");

// Create a root from the DOM
const domContainer = document.getElementById("root");
const root = ReactDOM.createRoot(domContainer);

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
import ReactDOM from 'react-dom';
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
const root = ReactDOM.createRoot(domContainer);
root.render(<App />);
```

## Best Practices

1. **Component Naming**: Use PascalCase for component names (e.g., `Header`, `App`).
2. **File Structure**: Organize components into a `components` folder.
3. **Functional Components**: Prefer functional components over class components.
4. **Hooks**: Utilize React hooks for state management and side effects.
5. **Prop Types**: Use PropTypes for type-checking props.

### Example

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

# JSX Grammars

## Recommended JSX Formatting

1. **Use Parentheses for JSX**
   - Wrap HTML-like JSX code in parentheses for readability and to avoid automatic semicolon insertion issues.

2. **Functional Components**
   - Components are functions that return JSX. This is efficient as functions are not stored in RAM like variables.
   - Use UpperCamelCase for component names, e.g., `NavItem`, `HeaderIntro`.

3. **Single Root Node**
   - A React component must return a single root node. Use a `div` or React Fragment (`<>...</>`) to wrap multiple child nodes.

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
      object={{ author: "Ron", body: "hello" }}
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
    const fruitElement = fruits.map(item => <Fruit color={item.color} size={item.size} />);

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
    const fruitElement = fruits.map(item => <Fruit {...item} />);

    export default function App() {
      return <div>{fruitElement}</div>;
    }
    ```

  - While convenient, explicit prop passing is more readable and preferred for clarity.

## Event Listeners

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

  - Refer to the [React documentation](https://reactjs.org/docs/events.html#mouse-events) for more event types.

# State in React

Managing state in React is crucial for building dynamic and interactive applications. Let's explore how state works in React, including best practices and examples.

## State vs. Props

- **Props** are immutable and used to pass data from a parent component to a child component. They allow for component reusability.
- **State** refers to variables managed within a component that can change over time. It enables components to create and manage their own data.

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
  firstName: "Ron",
  lastName: "Xie",
  isFavorite: true,
});

function toggleFavorite() {
  setContact(prevContact => ({
    ...prevContact,
    isFavorite: !prevContact.isFavorite,
  }));
}
```

## State Feature: Re-rendering on Change

Updating state triggers a re-render of the component and all its descendants.

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
      <input
        type="text"
        placeholder="First Name"
        onChange={handleChange}
        name="firstName"
        value={formData.firstName}
      />
      <input
        type="text"
        placeholder="Last Name"
        onChange={handleChange}
        name="lastName"
        value={formData.lastName}
      />
      <input
        type="email"
        placeholder="Email"
        onChange={handleChange}
        name="email"
        value={formData.email}
      />
      <textarea
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

# Dealing with APIs in Modern Front-End Development

## Fetching Data (fetch, axios)

Fetching data from APIs is a common task in modern web development. Here are the best practices and methods using both `fetch` and `axios`.

### Using Fetch

The `fetch` API provides a simple interface for fetching resources. Here's an example of fetching data and storing it in a state:

```jsx
import React, { useEffect, useState } from 'react';

export default function Fetch() {
  const [starWarsData, setStarwarsData] = useState({});

  useEffect(() => {
    fetch("https://swapi.dev/api/people/1")
      .then(response => response.json())
      .then(data => setStarwarsData(data))
      .catch(error => console.error('Error fetching data:', error));
  }, []);

  return <div>{JSON.stringify(starWarsData, null, 2)}</div>;
}
```

### Using Axios

`axios` is a popular HTTP client that offers a more powerful and flexible approach to making HTTP requests.

```jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function Fetch() {
  const [starWarsData, setStarwarsData] = useState({});

  useEffect(() => {
    axios.get("https://swapi.dev/api/people/1")
      .then(response => setStarwarsData(response.data))
      .catch(error => console.error('Error fetching data:', error));
  }, []);

  return <div>{JSON.stringify(starWarsData, null, 2)}</div>;
}
```

### Avoiding Infinite Loops

When fetching data inside a component, it is crucial to avoid infinite loops. The following example demonstrates how to fetch data without triggering an infinite loop:

```jsx
import React, { useEffect, useState } from 'react';

export default function Fetch() {
  const [starWarsData, setStarwarsData] = useState({});

  useEffect(() => {
    fetch("https://swapi.dev/api/people/1")
      .then(response => response.json())
      .then(data => setStarwarsData(data))
      .catch(error => console.error('Error fetching data:', error));
  }, []); // Empty dependency array ensures this runs only once after the initial render

  return <div>{JSON.stringify(starWarsData, null, 2)}</div>;
}
```

## Managing Side Effects with `useEffect`

### What is a Side Effect?

A side effect is any operation that affects something outside the scope of the function being executed, such as:

- Modifying global variables
- Making API requests
- Manipulating the DOM
- Setting up subscriptions

### Using `useEffect` to Handle Side Effects

The `useEffect` hook in React allows you to perform side effects in function components. Here's the syntax and usage:

```jsx
import React, { useEffect, useState } from 'react';

export default function Fetch() {
  const [starWarsData, setStarwarsData] = useState({});
  const [count, setCount] = useState(1);

  useEffect(() => {
    fetch(`https://swapi.dev/api/people/${count}`)
      .then(response => response.json())
      .then(data => setStarwarsData(data))
      .catch(error => console.error('Error fetching data:', error));
  }, [count]); // Dependency array ensures this runs whenever `count` changes

  return (
    <div>
      <button onClick={() => setCount(prevCount => prevCount + 1)}>count++</button>
      {count}
      <pre>{JSON.stringify(starWarsData, null, 2)}</pre>
    </div>
  );
}
```

### Cleaning Up Side Effects

To avoid memory leaks and unwanted behavior, it is important to clean up side effects. You can do this by returning a cleanup function from `useEffect`:

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

## Using Local Storage

Local storage is a way to store data on the client's browser. Here are some best practices for using local storage in modern web development:

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
