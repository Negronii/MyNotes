# How does React Router v6 model routes and navigation? / React Router v6 如何建模路由与导航？

React Router v6 nests route elements under a router and uses components and hooks such as `Routes`, `Route`, `Link`, `useParams`, and `useNavigate`. This is a version-pinned archive reference; do not mix it with React Router v5 `withRouter` examples. / React Router v6 在 Router 下嵌套路由元素，并使用 `Routes`、`Route`、`Link`、`useParams` 和 `useNavigate` 等组件与 Hook。本页是版本限定的归档参考，不要与 React Router v5 的 `withRouter` 示例混用。

## Routing in React with React Router v6 / 使用React Router v6进行路由

## Overview

Routing maps URL changes to React UI. With client-side routing, matching navigation can update the view without a full document reload; a server-rendered or hybrid framework has different routing and rendering boundaries. These examples use the [React Router v6.3 API](https://github.com/remix-run/react-router/blob/v6.3.0/docs/api.md).

The examples use React Router v6.3's declarative API (`BrowserRouter`, `Routes`, `Route` with `element`, and navigation Hooks). Pin the version for this lesson; React Router v7 adds other modes and package guidance.

## Installation

To install `react-router`, use the following command:

```bash
npm install react-router-dom@6.3.0
```

## Key Components and Hooks

### `<BrowserRouter>`

- Uses the HTML5 History API to keep the UI in sync with the URL.
- Should be used at the root of your application.

### `<HashRouter>`

- Uses the URL hash (e.g., `example.com/#/path`) to keep the UI in sync with the URL.
- Useful when the hosting environment cannot serve the application entry point for arbitrary paths.

### `<Routes>` and `<Route>`

- `<Routes>` is a container for all your route definitions.
- `<Route>` defines a mapping between a URL path and a component.

### `<Link>`

- Used to create navigational links. It renders an `<a>` element that allows navigation without reloading the page.

### `useParams`

- A hook to access the dynamic parameters in the URL.

### `useNavigate`

- A hook to programmatically navigate to different routes.

### `useLocation`

- A hook to access the current location object, which contains information about the URL.

## Defining Routes

Example: Display the `HomePage` component when the URL path is `/`, `LoginPage` when it is `/login`, and so on. Show a "page not found" message if the URL does not match any defined routes.

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './HomePage';
import LoginPage from './LoginPage';
import RegisterPage from './RegisterPage';
import DetailPage from './DetailPage';
import styles from './App.module.css';

function App() {
  return (
    <div className={styles.App}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/detail/:touristRouteId/:other" element={<DetailPage />} />
          <Route path="*" element={<h1>404 page not found, catch all</h1>} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
```

## Passing Parameters from URL

### Single Parameter

Example: Passing an ID as a parameter to the detail page.

In `App.tsx`:

```tsx
<Route path="/detail/:touristRouteId" element={<DetailPage />} />
```

In `DetailPage.tsx`:

```tsx
import { useParams } from 'react-router-dom';

export const DetailPage: React.FC = () => {
  const { touristRouteId } = useParams<"touristRouteId">();
  if (!touristRouteId) return <p>Route parameter is missing.</p>;
  return <h1>Detail page, id: {touristRouteId}</h1>;
};
```

### Multiple Parameters

Example: Passing multiple parameters.

In `App.tsx`:

```tsx
<Route path="/detail/:touristRouteId/:other" element={<DetailPage />} />
```

In `DetailPage.tsx`:

```tsx
import { useParams } from 'react-router-dom';

type MatchParams = "touristRouteId" | "other";

export const DetailPage: React.FC = () => {
  const params = useParams<MatchParams>();
  if (!params.touristRouteId || !params.other) {
    return <p>Route parameters are missing.</p>;
  }
  return (
    <h1>
      Detail page, id: {params.touristRouteId}, other: {params.other}
    </h1>
  );
};
```

## Navigation

### Using `useNavigate`

Example:

```tsx
import { useNavigate } from 'react-router-dom';

const MyComponent: React.FC = () => {
  const navigate = useNavigate();

  const handleRegister = () => {
    navigate('/register');
  };

  return <button onClick={handleRegister}>Register</button>;
};
```

### Using `<Link>`

An alternative way is to use `<Link>` from `'react-router-dom'`:

```tsx
import { Link } from 'react-router-dom';

const MyComponent: React.FC = () => {
  return <Link to="/register">Register</Link>;
};
```

### Best Practices

1. **Use `<Link>` for Navigation:** It is preferred over `useNavigate` for simple navigational links because it creates a semantic `<a>` element and avoids the need for an additional event handler.
2. **Define Routes Clearly:** Group related routes together and define a clear structure to make the routing configuration easy to read and maintain.
3. **Handle 404s Gracefully:** Add a catch-all route (`path="*"`) when the app should render its own not-found UI for unknown paths.
4. **Use Hooks for Parameters and Navigation:** Utilize `useParams`, `useNavigate`, and `useLocation` hooks to access URL parameters and navigate programmatically within your components.

**Version reference / 版本参考：** [React Router v6.3.0 API](https://github.com/remix-run/react-router/blob/v6.3.0/docs/api.md).
