# How do React class lifecycles and Hooks request data? / React 类组件生命周期和 Hooks 如何请求数据？

Start a request at the framework lifecycle or from an Effect when synchronizing with an external system, then model loading, success, and failure. A type annotation describes expected data but does not validate a response at runtime. / 可在框架生命周期或用于外部同步的 Effect 中启动请求，并显式处理加载、成功和失败。类型标注只描述预期数据，不会在运行时验证响应。

## Request Data in Lifecycle Methods / 在生命周期中请求数据

In class components, `componentDidMount()` is a lifecycle method that is invoked immediately after a component is mounted (inserted into the tree). It's a common place to initiate network requests to fetch data. Root StrictMode can exercise a development-only mount, unmount, and mount sequence, so each mount below creates its own request controller; see the [React Component lifecycle reference](https://react.dev/reference/react/Component#componentdidmount).

### Example

```tsx
interface State {
  data: unknown;
  error: string | null;
}

class MyComponent extends React.Component<{}, State> {
  private controller: AbortController | null = null;

  state: State = { data: null, error: null };

  componentDidMount() {
    const controller = new AbortController();
    this.controller = controller;

    fetch("https://api.example.com/data", { signal: controller.signal })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then(data => {
        if (!controller.signal.aborted) this.setState({ data, error: null });
      })
      .catch(cause => {
        if (!controller.signal.aborted) {
          this.setState({ error: cause instanceof Error ? cause.message : String(cause) });
        }
      });
  }

  componentWillUnmount() {
    this.controller?.abort();
    this.controller = null;
  }

  render() {
    const { data, error } = this.state;
    if (error) return <p role="alert">{error}</p>;
    return data === null ? <p>Loading...</p> : <pre>{JSON.stringify(data, null, 2)}</pre>;
  }
}
```

In function components, an Effect can synchronize with a request. This example checks the HTTP status and ignores stale results during cleanup; it leaves response validation to application code because `response.json()` does not validate a TypeScript shape at runtime:

### Example with Hooks

```tsx
import React, { useState, useEffect } from 'react';

const MyComponent = () => {
  const [data, setData] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    async function load() {
      try {
        const response = await fetch("https://api.example.com/data");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result: unknown = await response.json();
        if (!ignore) {
          setData(result);
          setError(null);
        }
      } catch (cause) {
        if (!ignore) setError(cause instanceof Error ? cause.message : String(cause));
      }
    }

    load();
    return () => {
      ignore = true;
    };
  }, []);

  if (error) return <p role="alert">{error}</p>;
  return data === null ? <div>Loading...</div> : <pre>{JSON.stringify(data, null, 2)}</pre>;
};
```

**See also / 另见：** [Advanced React / React进阶](../../../../frontend/frameworks/advanced-react.md) for server-state ownership and stale-result coordination.
