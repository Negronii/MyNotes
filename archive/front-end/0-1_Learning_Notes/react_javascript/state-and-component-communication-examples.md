# How do React components update and share local state? / React 组件如何更新和共享本地状态？

Use state for values that change the rendered output, update arrays and objects immutably, and lift shared values to the closest common parent. These worked examples preserve the archived JavaScript course's counter, list, object, callback, sibling, and conditional-rendering patterns.

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

**See also / 另见：** [Advanced React / React进阶](../../../../frontend/frameworks/advanced-react.md) explains ownership and communication choices; [React Basics / React基础](../../../../frontend/frameworks/react-basics.md) covers render and state timing.
