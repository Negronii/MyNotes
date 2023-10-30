# Create react app (auto set up project, recommended)

To create a new React app, you can use the following commands:

```shell
npx create-react-app <app name>
cd <app name>
npm install
npm start
```

# Add dependencies as developing tool

To add dependencies as developing tools in your React project, you can use either `npm` or `yarn`. Here are the commands:

Using npm:

```shell
npm install <package name> --save-dev
```

Using yarn:

```shell
yarn add <package name> --dev
```

# Remove dependencies

If you want to remove a dependency from your React project, you can use the following commands:

Using npm:

```shell
npm uninstall <package name> --save
```

Using yarn:

```shell
yarn remove <package name>
```

# Create element and render

Assuming you have a `<div id="root"></div>` in the HTML body, you can create a React element and render it as follows:

```javascript
// Create a React element
// React.createElement(<element name>, <element property>, <innerHTML>)
const title = React.createElement("h1", null, "Hello React");

// Create a root from the DOM
const domContainer = document.getElementById("root");
const root = ReactDOM.createRoot(domContainer);

// Render the title we just created
// Parameter: React JSX element or innerHTML to render
root.render(title);
root.render(<p>Hello world</p>);
```

# Create element with class attribute

To create an element with a class name in HTML, you would use the following syntax:

```html
<h1 class="header">This is a JSX</h1>
```

In JSX, it would be written as:

```jsx
<h1 className="header">This is a JSX</h1>
```

You can also use variable values inside JSX:

```jsx
var welcome = "welcome to JSX";
<h1 className="header">Message: {welcome}</h1>;
```

Note that the attribute for specifying the class name in JSX is `className`, not `class`.

# JSX Structure

Example of recommended JSX format and structure

**in header.jsx:**

```jsx
function Header() {
  return (
    <div>
      <h1>hello</h1>
      <p> this is a JSX</p>
    </div>
  );
}

export default Header;
```

**In index.jsx:**

```jsx
import Header from "./components/Header";

function TempName() {
  return (
    <div>
      <Header />
      <h1>reason learn react</h1>
      <ol>
        <li>hirable</li>
        <li>h1 grade</li>
      </ol>
    </div>
  );
}

const domContainer = document.getElementById("root");
const root = ReactDOM.createRoot(domContainer);
root.render(<TempName />);
```

# Keys of recommended JSX formatting

- Use parentheses "()" to cover HTML.
- Because setting a variable header will take up RAM, but letting a function return it won’t do so.
- Such functions are called components, and it is recommended to use Upper-camel naming convention, e.g., NavItem, HeaderIntro.
- Note that we can only render one node here. The node could have children nodes, which is why the previous HTML is wrapped with a `div` element.
- When we want to use such functions, we can call `render` with `<ComponentName />`. It is the same as `root.render(React.createElement(TempName, null))`.
- Components can contain other components by using `<ComponentName />`.
- If the page will contain a large number of elements, it is recommended to create a function called `Page()` and divide the components into multiple functions. Add the components to the `Page` element and render only the `Page`, e.g.,

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

- Separating the components (e.g., Header) and the app can make the project structure more logical.

# JSX Grammars

In a React component JSX, we can use `<ul className="">` to set a class and use CSS to format the class.

## Image Styling

In images, if we use `<img src="..."/>`, the resource may be invalid if we are calling the function from another JavaScript file in a different directory. The solution is to import the image first, e.g.:

```javascript
import reactLogo from "../images/react-icon.png";
```

Then in usage, we can write:

```javascript
<img src={reactLogo} />
```

## Adding JavaScript in JSX

In React, anything inside `{}` will be interpreted as JavaScript, e.g.:

```javascript
const a = 10
<div>{a}</div>
```

will give `<div>10</div>`. We can even have JavaScript expressions inside (not recommended for messy code), e.g.:

```javascript
const date = new Date()
<div>It is {date.getHours() % 12} o'clock</div>
```

A better way is:

```javascript
const date = new Date()
const time = date.getHours() % 12
<div>It is {time} o'clock</div>
```

## Passing Parameters to Components (Component Reuse)

Example:

Using header:

```javascript
<Header
  cat="cat"
  boolean={true}
  val={2}
  object={{ author: "Ron", body: "hello" }}
/>
```

Header:

```javascript
function Header(props) {
  console.log(props);
  return (
    <div>
      <h1>hello {props.cat}</h1>
      <p> this is a JSX {props.head}</p>
    </div>
  );
}

export default Header;
```

Log:

```javascript
{ cat: "cat", boolean: true, val: 2, object: { author: "Ron", body: "hello" } }
```

Note: `props` stands for properties. We CANNOT pass props to native DOM elements (e.g. `<div>`), because they can only have properties defined by the HTML specification. We can also destructure props, e.g. `function Header({ head, cat }) {}`. We can pass JavaScript datatypes by containing data in parentheses.

## Render Only When a Property Exists

```javascript
export default function Joke(props) {
  return (
    <div>{props.setup && <h1>render only when props.setup is true</h1>}</div>
  );
}
```

The statement is the same as:

```javascript
<h1 style={{ display: props.setup ? "block" : "none" }}>
  render only when props.setup is true
</h1>
```

It will only render the statement when `props.setup = true`.

## JavaScript `.map()` Review

```javascript
const nums = [1, 2, 3, 4, 5];
const squared = nums.map(function (item) {
  return item * item;
});
```

`.map()` will call the function on each item in the array, and the return value will replace the item. We can also use the index of the current value:

```javascript
const squared = nums.map((cur, index) => {
  // do something
});
```

## Render Array in JSX

````javascript
const fruits = [{ color: "red", size: 15 }, { color: "orange", size: 10 }]
const fruitElement = fruits.map((item) => {
  return <Fruit color={item.color} size={item.size} />
})

export default function App() {
  return <div>{fruitElement}</div>
}
``

`

## HTML String with JavaScript String

```javascript
<img src={`../images/${image}`} />
````

Use backticks to cover the whole string and include the JavaScript string inside `${}`.

## Object Spread Syntax

```javascript
const fruits = [
  { color: "red", size: 15 },
  { color: "orange", size: 10 },
];
const fruitElement = fruits.map((item) => {
  return <Fruit {...item} />;
});
```

This is the same as above (`return <Fruit color={item.color} size={item.size}>`). This will send each property in `item` as props to the `Fruit` function. This is less recommended, as passing objects one by one explicitly is more straightforward to see what the props are.

## Event Listener

Note that the event listener is in lower camel case in React, not all in lowercase like plain JavaScript. For example, in React:

```javascript
<button onClick={function () {}}>button</button>
<button onMouseEnter={function () {}}>button</button>
```

Or we can define the function somewhere else and call it:

```javascript
export default function App() {
  function handleClick() {
    // do something
  }
  return <button onClick={handleClick}>button</button>;
}
```

For more event types, see [https://reactjs.org/docs/events.html#mouse-events](https://reactjs.org/docs/events.html#mouse-events). Note that we can only put event listeners on native DOM elements!

# State

Let's say we have an array of contents to render. When the array of content is updated, we wish the rendered contents to be updated. Therefore, we need to hook a state with the array and make React render update whenever the array is updated.

## State vs Props

Props should be immutable; it is the parameter for the component so that it can be reused. State refers to the variables managed by the component that should be changing, similar to variables defined in a function.

## How to use state

React.useState(param)

param: default value for the state

return: an array, [<state value>, <state setter function>]

e.g.

const [state, setState] = React.useState("yes")

// Now state is "yes," and setState is the set function

We often name state something meaningful, for example: [isImportant, setIsImportant]. Whenever we want to change the state, we call the function with the new value as a parameter.

e.g. setState(0) or setIsImportant(true), whatever you set for the function name).

When the new value has a dependency on the old value, we can pass a function as a parameter in setState. It can have a default parameter which is the old value.

E.g. we have 2 buttons, one to add one to minus one

```jsx
const [count, setCount] = React.useState(0);

export default function App() {
  function add() {
    // we can use a lambda function, most preferred
    setCount((prevCount) => prevCount + 1);
    // it is the same as
    // setCount(function(prevCount) {
    //    return prevCount + 1;
    // })
    // we can use set method directly, NOT preferred
    // setCount(count + 1);
  }

  function minus() {
    setCount((prevCount) => prevCount - 1);
  }

  return (
    <div>
      <button onClick={add}>plus</button>
      <h1>{count}</h1>
      <button onClick={minus}>minus</button>
    </div>
  );
}
```

## Array state example

E.g. we want to update the App component when the user clicks on a button to add a thing.

```jsx
export default function App() {
  const thingsArray = ["Thing 1", "Thing 2"];

  function addItem() {
    setThingsArray((prevState) => {
      return [...prevState, `Thing ${thingsArray.length + 1}`];
    });
  }

  // here key = {thing} is just to avoid warning, doesn’t matter
  const thingsElements = thingsArray.map((thing) => <p key={thing}>{thing}</p>);

  return (
    <div>
      <button onClick={handleClick}>button</button>
      {thingsElements}
    </div>
  );
}
```

## Modify a property in state object

```jsx
const [contact, setContact] = React.useState({
  firstName: "Ron",
  lastName: "Xie",
  isFavorite: true,
});

function changeFavorite() {
  setContact((prevState) => ({
    ...prevState,
    isFavorite: !prevState.isFavorite,
  }));
}
```

Explanation: To modify a property in the state object, we can use the `useState` hook to define the state and the `setContact` function to update it. In the `changeFavorite` function, we use the functional form of `setContact` to access the previous state (`prevState`) and create a new state object by spreading its properties (`...prevState`). We then modify the `isFavorite` property by toggling its value (`!prevState.isFavorite`).

## State feature - re-rendering on change

When we update the state using the `set` function, all components that use the state, including all parent components, will be re-rendered. For example, if the `App` component uses the `Count` component, and the `Count` component uses the state `[count, setCount]`, when we call `setCount`, both the `App` and `Count` elements will be re-rendered by React.

## Child change parent's state

Assuming we have a parent element with a React state and a function to set the state properly using the `setState` function, we can pass the function as a prop and set the `onClick` function in the child element's native DOM element.

Example:

In `App.js`:

```jsx
export default function App() {
  const [isImportant, setIsImportant] = React.useState(true);

  function changeState() {
    setIsImportant((prevState) => !prevState);
  }

  return <Count handleClick={changeState} />;
}
```

In `Count.js`:

```jsx
export default function Count(props) {
  return <button onClick={props.handleClick} />;
}
```

Explanation: In this example, the `App` component has a state variable `isImportant` and a function `changeState` to update it. The `changeState` function is passed as a prop `handleClick` to the `Count` component. Inside the `Count` component, we set the `onClick` event of a button to the `handleClick` prop, so when the button is clicked, the `changeState` function in the parent component (`App`) will be called.

## Passing state/data

Passing state/data directly from/to siblings is not possible in React. However, we can have a common parent element that holds the state and use props to pass it to the children. This way, if the parent state changes due to any child element, React will update the parent component and subsequently update its children.

## Setting style in React

In plain JavaScript, we often set styles using `document.querySelector('root').style.backgroundColor = xxx`. In React, we can achieve a similar effect by using a JavaScript object to define the styles and then apply them to native DOM elements.

```jsx
const styles = { backgroundColor: "black" };

return <div style={styles} />;
```

In some cases, we may want to have different styles for different occasions. For example, we can pass a `darkMode` prop to a component and present different colors based on its value:

```jsx
const styles = { backgroundColor: props.darkMode ? "black" : "white" };
```

## Find the object in Array State

Multiple children components can invoke a function in the parent component by passing the function in props. To determine which child component called the function, we can pass a unique ID in props and let the child call the function with

the unique ID as a parameter. This way, the parent component can identify which child is calling the function and update the state accordingly.

In `App.js`:

```jsx
const [boxes, setBoxes] = React.useState([
  { id: 1, on: false },
  { id: 2, on: false },
  { id: 3, on: true },
]);

function toggle(id) {
  setBoxes((prev) => {
    return prev.map((box) => {
      return box.id === id ? { ...box, on: !box.on } : box;
    });
  });
}

const boxesElements = boxes.map((box) => (
  <Box key={box.id} id={box.id} on={box.on} toggle={toggle} />
));

return <div>{boxesElements}</div>;
```

In `Box.js`:

```jsx
export default function Box(props) {
  const styles = { backgroundColor: props.on ? "black" : "white" };

  return (
    <div
      style={styles}
      className="box"
      onClick={() => props.toggle(props.id)}
    ></div>
  );
}
```

Explanation: In this example, the `App` component has an array state variable `boxes`, which contains objects with `id` and `on` properties. The `toggle` function is passed as a prop `toggle` to the `Box` component. Inside the `Box` component, we set the `onClick` event of a `div` element to call the `toggle` prop function with the corresponding `id`. The `toggle` function in the parent component (`App`) maps over the `boxes` array and toggles the `on` property of the matching object based on the provided `id`.

## Conditional Rendering

Conditional rendering in React allows you to conditionally render certain components or elements based on a condition. There are two common ways to perform conditional rendering in React:

1. Using the logical AND operator (`&&`):

   ```jsx
   {condition && <element>}
   ```

   If the `condition` is true, the `element` will be rendered. Otherwise, it will not be rendered.

2. Using the ternary operator (`? :`):
   ```jsx
   {condition ? <element1> : <element2>}
   ```
   If the `condition` is true, `element1` will be rendered. Otherwise, `element2` will be rendered.

Here's an example demonstrating conditional rendering:

```jsx
const [isShown, setIsShown] = React.useState(true);

return (
  <div>
    {isShown && <h1>Show context</h1>}
    <button
      onClick={() => {
        setIsShown((prev) => !prev);
      }}
    >
      {isShown ? "Hide" : "Show"}
    </button>
  </div>
);
```

In the above example, a header with the text "Show context" is rendered only when `isShown` is true. Clicking the button toggles the value of `isShown`, thereby showing or hiding the header based on the updated state.

## Forms and Inputs in React

When working with forms in React, you can collect data from various inputs and manage their values using state. Here's an example of a form with multiple inputs and how to handle their changes:

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
    setFormData((prevState) => {
      return {
        ...prevState,
        [name]: type === "checkbox" ? checked : value,
      };
    });
  }

  function handleSubmit(event) {
    event.preventDefault();
    // Submit formData to the backend...
    // console.log(formData)
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
      <br />
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
        <br />
        <input
          type="radio"
          id="full-time"
          name="employment"
          value="full-time"
          checked={formData.employment === "full-time"}
          onChange={handleChange}
        />

        <label htmlFor="full-time">Full-time</label>
        <br />
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
      <br />
      <label htmlFor="favColor">What is your favorite color?</label>
      <select
        id="favColor"
        value={formData.favColor}
        onChange={handleChange}
        name="favColor"
      >
        <option value="red">Red</option>
        <option value="blue">Blue</option>
      </select>
      <br />
      <button type="submit">Submit</button>
    </form>
  );
}
```

In the above example, the form collects data from different inputs such as text fields, checkboxes, radio buttons, and a select dropdown. The `handleChange` function updates the `formData` state based on the input values. The `handleSubmit` function is called when the form is submitted, preventing the default form submission behavior. You can add your logic to handle form submission, such as sending the form data to the backend.

Remember to set the `value` prop of each input element equal to the corresponding state value (`formData.<fieldName>`) to establish the connection between the input and the state value.

# Deal with API

## Get the data (fetch, axios)

### Store data to state

```jsx
export default function Fetch() {
  const [starWarsData, setStarwarsData] = React.useState({});

  // fetch("https://swapi.dev/api/people/1")
  //     .then(r => r.json())
  //     .then(data => setStarwarsData(data))

  return <div>{JSON.stringify(starWarsData, null, 2)}</div>;
}
```

However, the following code will trigger an infinite loop. Fetch data -> set state -> React re-render component -> fetch data...

# Side Effect

The operations may cause side effects: all operations other than returning a value, e.g., modifying global variables, requesting data, modifying DOM elements, even requesting data.
Side effect refers to the same input but different output, e.g., requesting data from the backend, same API, same props but may get different data.

## useEffect()

[Official React documentation on useEffect()](https://reactjs.org/docs/hooks-effect.html)

`useEffect()` helps manage side effects (and avoid the infinite loop before).
Side effect refers to any code that affects an outside system, e.g., local storage, API calls, web sockets, syncing two states.
Data fetching, setting up a subscription, and manually changing the DOM in React components are all examples of side effects.

### How to use:

`useEffect(<a function>, <an array of dependencies>)`

Every time we render the component, it will compare the dependencies array with the dependencies array from the last render. If the value changed, it will run the function.

We can also call `useEffect(<a function>)` with no dependencies array. However, it is not recommended as it is almost the same as not putting it in `useEffect()`. The only change is it will be recalled in every re-render, not after re-render.

The code we put in `useEffect()` will be executed:

- After the component is rendered.
- After every re-render of the component (assuming no dependencies array).
- Will not run the effect when the values in the dependencies array remain the same since the last render.

So, if we hard code the array (e.g., [0] or []), the value will not change between re-renders, and therefore the function will never be called.
The function will be called when the data in the dependencies array changes.

An example of clicking on a button to increase the count and show the Star Wars data using the count as the index:

```jsx
import React from "react";

export default function Fetch() {
  const [starWarsData, setStarwarsData] = React.useState({});
  const [count, setCount] = React.useState(1);

  React.useEffect(() => {
    console.log(1);
    fetch(`https://swapi.dev/api/people/${count}`)
      .then((r) => r.json())
      .then((data) => setStarwarsData(data));
  }, [count]);

  return (
    <div>
      <button
        onClick={() => {
          setCount((prevState) => prevState + 1);
        }}
      >
        count++
      </button>
      {count}
      {JSON.stringify(starWarsData, null, 2)}
    </div>
  );
}
```

# Cleaning up side-effects

When the DOM element (or React component) is to be deleted, there might be side effects that cause memory leakage. For example, if you create a label and add a listener in `useEffect()`, you want to remove the listener (i.e., cleaning up) when you delete the entire element.

The solution is to return

a cleaning up function in `useEffect()`.

Example:

```jsx
React.useEffect(() => {
  function doSomething() {
    // Code for the side effect
  }

  // We add the event listener to window and want to clean it up after this element is deleted
  window.addEventListener("resize", doSomething);

  function cleaningUp() {
    window.removeEventListener("resize", doSomething);
  }

  return cleaningUp;
}, []);
```

# Local storage

Using local storage:

- `localStorage.getItem("<key>")`
- `localStorage.setItem("<key>", <value>)`

Note:

- The value must be a string. If you want to store an array or object, use `JSON.stringify(<value>)` to convert it to a string.
- To decode the stringified value, use `JSON.parse(<stringified value>)`.
- `JSON.stringify(null)` will return null.
