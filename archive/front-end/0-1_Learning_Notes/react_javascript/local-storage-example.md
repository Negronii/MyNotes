# How can a React component persist small client-side state? / React 组件如何持久化少量客户端状态？

`localStorage` stores strings in the browser, so objects need serialization. Read and parse stored data defensively; a lazy initializer that accesses `window` is browser-only and must be adapted for server rendering.

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

**Sources checked 2026-10-15** — [Render and Commit](https://react.dev/learn/render-and-commit), [State as a Snapshot](https://react.dev/learn/state-as-a-snapshot), [Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects), and [StrictMode](https://react.dev/reference/react/StrictMode).

**See also / 另见：** [Browser Storage and Communication / 浏览器存储与通信](../../../../frontend/browser-apis/browser-storage-and-communication.md) for storage scope and coordination.
