Understanding the differences between `useCallback`, `useMemo`, and `.memo()` in React can be crucial for optimizing your application's performance. Here's a breakdown:

### `useCallback`

- **Purpose**: `useCallback` is used to memoize callback functions. This means it returns a memoized version of the callback that only changes if one of the dependencies has changed.
- **Usage**: Primarily used when you need to pass a function as a prop to a child component and you want to avoid unnecessary re-renders.
- **Example**:
  ```javascript
  const handleClick = useCallback(() => {
    // handle click
  }, [dependencies]);
  ```

### `useMemo`

- **Purpose**: `useMemo` is used to memoize values. It returns a memoized value that only changes if one of the dependencies has changed.
- **Usage**: Used when you have expensive calculations that you want to avoid re-calculating on every render unless the dependencies change.
- **Example**:
  ```javascript
  const memoizedValue = useMemo(() => {
    return computeExpensiveValue(a, b);
  }, [a, b]);
  ```

### `useMemo` vs. `useCallback`

- **Return Value**: `useMemo` returns a memoized value, while `useCallback` returns a memoized function.
- **Usage Context**: Use `useMemo` for memoizing the result of a calculation or a value, and `useCallback` for memoizing functions to prevent unnecessary re-renders of child components that rely on function props.

### `.memo()`

- **Purpose**: `React.memo()` is a higher-order component that memoizes a functional component. It helps to avoid re-rendering the component if its props have not changed.
- **Usage**: Used when you want to optimize functional components by skipping re-renders when the component's props remain the same.
- **Example**:
  ```javascript
  const MyComponent = React.memo((props) => {
    // component code
  });
  ```

### `useMemo` vs. `.memo()`

- **Usage Context**:
  - `useMemo` is used inside functional components to memoize values or results of computations.
  - `.memo()` is used to wrap a functional component to avoid re-renders if the props don't change.
- **Scope**:
  - `useMemo` is scoped to the component in which it is used. It helps in optimizing the internal calculations of that component.
  - `.memo()` is used to optimize the entire component by wrapping it, reducing unnecessary re-renders based on unchanged props.

### Summary

- **`useCallback`**: Memoizes functions to avoid unnecessary re-renders when functions are passed as props.
- **`useMemo`**: Memoizes values or results of computations to avoid re-calculations on every render.
- **`.memo()`**: Memoizes entire functional components to prevent re-renders if props haven't changed.

By understanding these tools and their appropriate contexts, you can effectively optimize your React applications for better performance.

Determining when to create a custom hook versus a normal function in React depends on the specific use case and the goals of reusability, state management, and side effects. Here are guidelines to help decide:

### When to Make Something a Hook

1. **State Management**:
   - If your function involves managing state with `useState`, `useReducer`, or any other stateful logic, it should be a hook.
   - Example: A hook to manage form inputs.
     ```javascript
     function useForm(initialState) {
       const [values, setValues] = useState(initialState);
       
       const handleChange = (event) => {
         const { name, value } = event.target;
         setValues({
           ...values,
           [name]: value,
         });
       };
       
       return [values, handleChange];
     }
     ```

2. **Side Effects**:
   - If your function involves side effects using `useEffect`, such as data fetching, subscriptions, or manually manipulating the DOM, it should be a hook.
   - Example: A hook to fetch data from an API.
     ```javascript
     function useFetch(url) {
       const [data, setData] = useState(null);
       const [loading, setLoading] = useState(true);
       
       useEffect(() => {
         fetch(url)
           .then(response => response.json())
           .then(data => {
             setData(data);
             setLoading(false);
           });
       }, [url]);
       
       return [data, loading];
     }
     ```

3. **Reusing Component Logic**:
   - When you have complex logic that you want to reuse across multiple components, encapsulating that logic in a custom hook can make it more reusable and maintainable.
   - Example: A hook to handle user authentication status.
     ```javascript
     function useAuth() {
       const [user, setUser] = useState(null);
       
       useEffect(() => {
         // Check if user is authenticated
         const loggedInUser = getUserFromSession();
         setUser(loggedInUser);
       }, []);
       
       return user;
     }
     ```

4. **Custom Hooks Composing Other Hooks**:
   - If your function needs to use other hooks, it should itself be a hook. React hooks must be called within the context of a React function component or another custom hook.
   - Example: A hook that combines multiple hooks.
     ```javascript
     function useCombinedLogic() {
       const [state, setState] = useState(initialState);
       useEffect(() => {
         // some side effect
       }, [state]);
       
       return [state, setState];
     }
     ```

### When to Make Something Just a Normal Function

1. **Pure Functions**:
   - If your function is a pure function (i.e., it takes inputs and returns outputs without any side effects), it should remain a normal function.
   - Example: Utility functions.
     ```javascript
     function calculateSum(a, b) {
       return a + b;
     }
     ```

2. **Helper Functions**:
   - If your function is a simple helper that doesn't involve any React state or lifecycle, keep it as a normal function.
   - Example: Formatting a date.
     ```javascript
     function formatDate(date) {
       return new Date(date).toLocaleDateString();
     }
     ```

3. **Business Logic**:
   - Business logic that doesn't depend on React state or lifecycle methods should be in normal functions. This keeps your business logic separate and reusable across different contexts.
   - Example: Validating form input.
     ```javascript
     function validateEmail(email) {
       const re = /\S+@\S+\.\S+/;
       return re.test(email);
     }
     ```

4. **Static Data**:
   - If your function is providing static data or configuration, it should remain a normal function.
   - Example: Providing configuration options.
     ```javascript
     function getConfig() {
       return {
         apiUrl: 'https://api.example.com',
         timeout: 5000,
       };
     }
     ```

### Summary

- **Create a custom hook** when you need to manage state, handle side effects, or reuse complex component logic that involves hooks.
- **Use a normal function** for pure functions, helper functions, business logic that doesn't involve React state or lifecycle methods, and static data/configuration.

By following these guidelines, you can create well-structured, maintainable, and reusable React code.

### What is `Partial<>`?

`Partial<>` is a utility type in TypeScript that makes all properties of a given type optional. This is particularly useful when you want to create an object that doesn't need to have all the properties of a specific type defined.

### How to Use `Partial<T>` to Avoid the `as` Keyword

The `as` keyword in TypeScript is used for type assertions, where you tell the compiler to treat a value as a specific type. However, using type assertions can be unsafe because it bypasses type checking, which can lead to runtime errors.

Using `Partial<T>` helps avoid unnecessary type assertions by allowing the creation of objects that only partially conform to a type, without asserting their type explicitly.

### Example Usage of `Partial<T>`

Let's say you have an interface `User`:

```typescript
interface User {
  id: number;
  name: string;
  email: string;
}
```

If you want to create a function that updates user properties, but not necessarily all of them, you can use `Partial<User>`:

```typescript
function updateUser(user: User, updates: Partial<User>): User {
  return { ...user, ...updates };
}

// Usage
const user: User = { id: 1, name: 'John Doe', email: 'john.doe@example.com' };

const updatedUser = updateUser(user, { name: 'Jane Doe' });
// updatedUser is { id: 1, name: 'Jane Doe', email: 'john.doe@example.com' }
```

In this example, `updates` can have any subset of the properties defined in `User`, and you don't need to use the `as` keyword to cast the `updates` object.

### Why Avoid the `as` Keyword

1. **Type Safety**: Type assertions bypass TypeScript's type checking, potentially leading to runtime errors if the asserted type does not match the actual type.
   
   ```typescript
   const value: any = "Hello";
   const num = value as number; // This is unsafe and can cause runtime errors
   ```

2. **Maintainability**: Using type assertions can make code harder to maintain and understand, as future developers (or even you) might not easily understand why a certain type was asserted.

3. **Readability**: Excessive use of `as` can clutter your code and make it less readable, making it harder to follow the logic and type flow.

### Example of Avoiding `as` Keyword

Suppose you have a function to initialize a user object where some properties are optional:

```typescript
function initializeUser(user: Partial<User>): User {
  return {
    id: user.id ?? 0,
    name: user.name ?? 'Default Name',
    email: user.email ?? 'default@example.com',
  };
}

// Usage
const newUser = initializeUser({ name: 'Jane Doe' });
```

In this example, `initializeUser` accepts a `Partial<User>` object, ensuring type safety without the need for type assertions:

- `user.id ?? 0` ensures `id` is given a default value if not provided.
- `user.name ?? 'Default Name'` ensures `name` has a default value.
- `user.email ?? 'default@example.com'` does the same for `email`.

### Conclusion

Using `Partial<T>` allows you to work with objects that only partially conform to a type without resorting to type assertions. This maintains type safety, improves readability, and enhances maintainability by leveraging TypeScript's type system effectively. Avoiding the `as` keyword when possible ensures that your code benefits from TypeScript's compile-time checks, reducing the risk of runtime errors.

`useRequest` is a custom hook provided by the `ahooks` library, which is a set of high-quality and reliable React hooks designed to enhance the capabilities of React applications. `useRequest` is specifically designed for handling asynchronous operations, such as API requests, and it provides a standardized way to manage loading states, error handling, and success responses.

### Features of `useRequest`

- Simplifies the process of making API requests.
- Provides built-in support for managing loading states and error handling.
- Offers various configuration options for controlling request behavior.
- Supports caching, polling, and pagination out of the box.

### Basic Usage of `useRequest`

Here is a basic example of how to use `useRequest` in a React component:

```javascript
import React from 'react';
import { useRequest } from 'ahooks';
import axios from 'axios';

const fetchUser = (id) => {
  return axios.get(`https://jsonplaceholder.typicode.com/users/${id}`);
};

const UserComponent = ({ userId }) => {
  const { data, error, loading, run } = useRequest(() => fetchUser(userId), {
    manual: true,
  });

  React.useEffect(() => {
    run();
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>User Info</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};

export default UserComponent;
```

### Returned Values from `useRequest`

When you call `useRequest`, it returns an object with several properties and methods that help you manage the state of your request. Here's a breakdown of the main returned values:

1. **data**: The response data from the request. Initially `undefined` until the request completes successfully.
2. **error**: The error object if the request fails. Initially `undefined` until the request encounters an error.
3. **loading**: A boolean that indicates whether the request is currently in progress.
4. **run**: A function to manually trigger the request. Useful when the request should not automatically start or if you want to re-run the request based on user actions or other events.
5. **params**: The parameters used for the request. Useful for understanding the context of the request.
6. **cancel**: A function to cancel the ongoing request.
7. **refresh**: A function to refresh the request, which is essentially re-running the request with the same parameters.
8. **mutate**: A function to manually update the data. Useful for optimistic updates or when you need to adjust the data without making another request.

### Configuration Options

The second parameter to `useRequest` is an options object where you can customize the behavior of the hook. Some key options include:

- **manual**: If `true`, the request will not automatically run when the component mounts. You need to call the `run` method to start the request.
- **onSuccess**: A callback function that gets called when the request is successful.
- **onError**: A callback function that gets called when the request fails.
- **onFinally**: A callback function that gets called when the request is finished, regardless of success or failure.
- **pollingInterval**: If provided, the request will be automatically re-run at the specified interval (in milliseconds).
- **debounceInterval**: If provided, the request will be debounced by the specified interval (in milliseconds).
- **throttleInterval**: If provided, the request will be throttled by the specified interval (in milliseconds).
- **refreshDeps**: An array of dependencies that will trigger the request to re-run when they change.

### Example with Configuration Options

Here is an example demonstrating some configuration options:

```javascript
import React from 'react';
import { useRequest } from 'ahooks';
import axios from 'axios';

const fetchUser = (id) => {
  return axios.get(`https://jsonplaceholder.typicode.com/users/${id}`);
};

const UserComponent = ({ userId }) => {
  const { data, error, loading, run, refresh } = useRequest(() => fetchUser(userId), {
    manual: true,
    onSuccess: (result) => {
      console.log('Request succeeded:', result);
    },
    onError: (err) => {
      console.error('Request failed:', err);
    },
    refreshDeps: [userId],
  });

  React.useEffect(() => {
    run();
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>User Info</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
      <button onClick={refresh}>Refresh</button>
    </div>
  );
};

export default UserComponent;
```

In this example, the `useRequest` hook is configured to manually trigger the request with the `run` method and to log messages on success or error. The request will automatically re-run whenever the `userId` prop changes, thanks to the `refreshDeps` option.

Lodash is a popular JavaScript utility library that provides a wide range of functions for common programming tasks, making it easier to work with arrays, objects, strings, and other types of data. Here are some frequently used Lodash functions, along with examples of how they can be used:

### 1. `_.chunk`

Splits an array into groups of a specified size.

```javascript
const _ = require('lodash');

const array = [1, 2, 3, 4, 5, 6];
const result = _.chunk(array, 2);
console.log(result); // [[1, 2], [3, 4], [5, 6]]
```

### 2. `_.compact`

Creates an array with all falsy values removed.

```javascript
const array = [0, 1, false, 2, '', 3];
const result = _.compact(array);
console.log(result); // [1, 2, 3]
```

### 3. `_.debounce`

Creates a debounced function that delays invoking the provided function until after a specified time has elapsed.

```javascript
const handleResize = _.debounce(() => {
  console.log('Resize event handled!');
}, 200);

window.addEventListener('resize', handleResize);
```

### 4. `_.cloneDeep`

Creates a deep clone of a value.

```javascript
const obj = { a: 1, b: { c: 2 } };
const clonedObj = _.cloneDeep(obj);
console.log(clonedObj); // { a: 1, b: { c: 2 } }
```

### 5. `_.merge`

Recursively merges own and inherited enumerable string keyed properties of source objects into the destination object.

```javascript
const object = { a: [{ b: 2 }, { d: 4 }] };
const other = { a: [{ c: 3 }, { e: 5 }] };

const result = _.merge(object, other);
console.log(result); // { a: [{ b: 2, c: 3 }, { d: 4, e: 5 }] }
```

### 6. `_.omit`

Creates an object composed of the own and inherited enumerable property paths of `object` that are not omitted.

```javascript
const object = { a: 1, b: '2', c: 3 };
const result = _.omit(object, ['a', 'c']);
console.log(result); // { b: '2' }
```

### 7. `_.pick`

Creates an object composed of the picked object properties.

```javascript
const object = { a: 1, b: '2', c: 3 };
const result = _.pick(object, ['a', 'c']);
console.log(result); // { a: 1, c: 3 }
```

### 8. `_.uniq`

Creates a duplicate-free version of an array.

```javascript
const array = [2, 1, 2];
const result = _.uniq(array);
console.log(result); // [2, 1]
```

### 9. `_.flatten`

Flattens `array` a single level deep.

```javascript
const array = [1, [2, [3, [4]], 5]];
const result = _.flatten(array);
console.log(result); // [1, 2, [3, [4]], 5]
```

### 10. `_.flattenDeep`

Recursively flattens `array`.

```javascript
const array = [1, [2, [3, [4]], 5]];
const result = _.flattenDeep(array);
console.log(result); // [1, 2, 3, 4, 5]
```

### 11. `_.groupBy`

Creates an object composed of keys generated from the results of running each element of `collection` through `iteratee`.

```javascript
const array = [6.1, 4.2, 6.3];
const result = _.groupBy(array, Math.floor);
console.log(result); // { '4': [4.2], '6': [6.1, 6.3] }
```

### 12. `_.orderBy`

Sorts `collection` by `iteratee` in specified orders.

```javascript
const users = [
  { 'user': 'fred',   'age': 48 },
  { 'user': 'barney', 'age': 34 },
  { 'user': 'fred',   'age': 40 },
  { 'user': 'barney', 'age': 36 }
];

const result = _.orderBy(users, ['user', 'age'], ['asc', 'desc']);
console.log(result);
// [
//   { 'user': 'barney', 'age': 36 },
//   { 'user': 'barney', 'age': 34 },
//   { 'user': 'fred', 'age': 48 },
//   { 'user': 'fred', 'age': 40 }
// ]
```

### 13. `_.get`

Gets the value at `path` of `object`. If the resolved value is `undefined`, the `defaultValue` is returned in its place.

```javascript
const object = { 'a': [{ 'b': { 'c': 3 } }] };

const result = _.get(object, 'a[0].b.c');
console.log(result); // 3
```

### 14. `_.set`

Sets the value at `path` of `object`. If a portion of `path` doesn't exist, it's created.

```javascript
const object = { 'a': [{ 'b': { 'c': 3 } }] };

_.set(object, 'a[0].b.c', 4);
console.log(object.a[0].b.c); // 4
```

### 15. `_.debounce`

Creates a debounced function that delays invoking the provided function until after a specified time has elapsed since the last time it was invoked.

```javascript
const saveInput = _.debounce((value) => {
  console.log('Saving data:', value);
}, 1000);

document.getElementById('input').addEventListener('input', (event) => {
  saveInput(event.target.value);
});
```

### Summary

These are some of the most commonly used Lodash functions that can help simplify and optimize JavaScript code. Lodash provides a comprehensive set of utilities, and knowing these frequently used functions can significantly enhance productivity and code quality in your projects.

`ahooks` is a popular library of React hooks designed to provide additional functionality and simplify common patterns in React development. Here are some of the frequently used hooks from `ahooks` and their purposes:

### Frequently Used `ahooks` Functions

1. **`useRequest`**
   - **Purpose**: Manage async operations (e.g., API requests) with built-in state handling for loading, success, and error states.
   - **Example**:
     ```javascript
     const { data, error, loading, run } = useRequest(fetchData);
     ```

2. **`useBoolean`**
   - **Purpose**: Simplify boolean state management with functions to toggle, set true, and set false.
   - **Example**:
     ```javascript
     const [state, { toggle, setTrue, setFalse }] = useBoolean(false);
     ```

3. **`useLocalStorageState`**
   - **Purpose**: Manage state that is synchronized with `localStorage`.
   - **Example**:
     ```javascript
     const [value, setValue] = useLocalStorageState('key', 'defaultValue');
     ```

4. **`useMemoizedFn`**
   - **Purpose**: Create a memoized function that remains stable across re-renders, avoiding the need to use `useCallback` repeatedly.
   - **Example**:
     ```javascript
     const memoizedFn = useMemoizedFn((a, b) => a + b);
     ```

5. **`useMount`**
   - **Purpose**: Run a function once when the component mounts.
   - **Example**:
     ```javascript
     useMount(() => {
       console.log('Component mounted');
     });
     ```

6. **`useUnmount`**
   - **Purpose**: Run a function once when the component unmounts.
   - **Example**:
     ```javascript
     useUnmount(() => {
       console.log('Component unmounted');
     });
     ```

7. **`useDebounceFn`**
   - **Purpose**: Create a debounced function to prevent it from being called too frequently.
   - **Example**:
     ```javascript
     const { run } = useDebounceFn(fetchData, { wait: 300 });
     ```

8. **`useThrottleFn`**
   - **Purpose**: Create a throttled function to limit the rate at which it is called.
   - **Example**:
     ```javascript
     const { run } = useThrottleFn(fetchData, { wait: 300 });
     ```

9. **`useInterval`**
   - **Purpose**: Manage setInterval in a React-friendly way.
   - **Example**:
     ```javascript
     useInterval(() => {
       console.log('Interval tick');
     }, 1000);
     ```

10. **`useTimeout`**
    - **Purpose**: Manage setTimeout in a React-friendly way.
    - **Example**:
      ```javascript
      useTimeout(() => {
        console.log('Timeout complete');
      }, 1000);
      ```

### Difference Between `useMemoizedFn`, `useCallback`, `useMemo`, and `memo`

- **`useMemoizedFn`**
  - **Purpose**: Provides a stable, memoized function reference that remains the same across re-renders.
  - **Usage**: Avoids re-creating functions, useful for event handlers and callbacks that don't need to change.
  - **Example**:
    ```javascript
    const memoizedFn = useMemoizedFn((a, b) => a + b);
    ```

- **`useCallback`**
  - **Purpose**: Returns a memoized version of the callback function that only changes if one of the dependencies has changed.
  - **Usage**: Avoids re-creating functions when passing them to child components or event handlers.
  - **Example**:
    ```javascript
    const handleClick = useCallback(() => {
      console.log('Clicked');
    }, []);
    ```

- **`useMemo`**
  - **Purpose**: Memoizes a value that is expensive to compute, re-computing it only when dependencies change.
  - **Usage**: Avoids unnecessary calculations on each render.
  - **Example**:
    ```javascript
    const memoizedValue = useMemo(() => {
      return expensiveComputation();
    }, [dependency]);
    ```

- **`React.memo`**
  - **Purpose**: A higher-order component that memoizes a functional component, preventing it from re-rendering if its props haven't changed.
  - **Usage**: Optimizes functional components to prevent unnecessary re-renders.
  - **Example**:
    ```javascript
    const MyComponent = React.memo(({ prop }) => {
      return <div>{prop}</div>;
    });
    ```

### Summary

- **`useMemoizedFn`**: Creates a stable, memoized function reference. Good for event handlers and callbacks that should not change.
- **`useCallback`**: Memoizes the callback function, re-creating it only when dependencies change. Good for passing stable function references to child components.
- **`useMemo`**: Memoizes a value, re-computing it only when dependencies change. Good for avoiding expensive calculations on every render.
- **`React.memo`**: Memoizes a functional component to prevent re-renders when props haven't changed. Good for optimizing functional components.

By understanding and using these hooks appropriately, you can optimize performance and manage side effects more effectively in your React applications.

The `corepack enable` command is part of Corepack, an experimental tool intended to manage JavaScript package managers like Yarn and pnpm. Corepack comes pre-installed with Node.js versions 16.10 and later, aiming to provide a unified way to handle these package managers without needing separate global installations.

### What does `corepack enable` do?

When you run `corepack enable`, it prepares your environment to use the package managers supported by Corepack—Yarn and pnpm—by setting up shims (proxy executables) that point to specific versions of these managers. These shims ensure that when you run a command like `yarn` or `pnpm`, the correct version of the package manager is invoked, based on the project's configuration, even if it isn't globally installed.

### How to use Corepack on a MacBook

Here are the steps to enable and use Corepack on a MacBook:

1. **Ensure Node.js is Installed**: First, make sure you have Node.js installed. If it's not installed, you can download and install it from [Node.js's official website](https://nodejs.org/). For macOS, the preferred way to install Node.js is via Homebrew:

   ```bash
   brew install node
   ```

   This will install the latest version of Node.js along with npm.

2. **Enable Corepack**:
   
   Open your terminal and run the following command to enable Corepack:

   ```bash
   corepack enable
   ```

   This command sets up the necessary shims for Yarn and pnpm. After running this, commands like `yarn` or `pnpm` will use the versions specified by Corepack.

3. **Verify Installation**:
   
   You can verify that Corepack is correctly set up by checking the versions of the package managers:

   ```bash
   yarn --version
   pnpm --version
   ```

   This will output the versions of Yarn and pnpm that Corepack will use.

### Dependencies

Corepack itself doesn't require any specific dependencies other than Node.js. It's integrated with Node.js and utilizes the existing system setup for Node.js and npm.

### Additional Configuration (if needed)

In some cases, you might need to configure Corepack to use specific versions of Yarn or pnpm, or manage versions differently. You can do this by modifying the `package.json` of your project or globally through configuration files.

### Troubleshooting

If you encounter issues with Corepack not behaving as expected, you might need to check the following:

- Ensure your Node.js version is compatible with Corepack (Node.js 16.10 or later).
- Check if Corepack is properly enabled by running `corepack --status`.
- Re-run `corepack enable` if the shims are not set correctly.

This setup provides a more controlled environment for managing package versions across different projects, which can be particularly useful in development environments where consistency is key.