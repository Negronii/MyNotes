# How can a React Effect synchronize with requests and browser state? / React Effect 如何与请求及浏览器状态同步？

An Effect is for synchronizing after a commit with an external system. Clean up subscriptions and prevent stale request results from replacing newer state; check `response.ok` for Fetch because HTTP error statuses do not reject the promise.

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

**See also / 另见：** [Advanced React / React进阶](../../../../frontend/frameworks/advanced-react.md) compares manual Effects with server-state queries; [Asynchronous JavaScript / 异步 JavaScript](../../../../frontend/javascript/asynchronous-javascript.md) covers Promise behavior.
