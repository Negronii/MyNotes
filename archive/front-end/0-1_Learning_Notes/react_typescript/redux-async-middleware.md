# How do reducers, thunks, and middleware extend a Redux store? / reducer、thunk 和 middleware 如何扩展 Redux store？

Combine focused reducers into a root state shape, select typed state in components, and use middleware or thunks for work that must happen around dispatch. Redux Toolkit configures thunk by default; the manual setup is retained for older bare-Redux stores. / 把职责聚焦的 reducer 组合为根 state 结构，在组件中按类型读取状态，并通过 middleware 或 thunk 执行 dispatch 周边的工作。Redux Toolkit 默认配置 thunk；手动配置示例保留给旧式裸 Redux store。

## Redux Store with Multiple Reducers / 使用多个Reducer拆分Store

In a large application, it's common to split the reducer logic into multiple smaller reducers. These smaller reducers manage specific parts of the state and are combined into a single root reducer.

## Example: Redux Store with Multiple Reducers

```typescript
import { configureStore } from "@reduxjs/toolkit";
import { combineReducers } from "redux";
import languageReducer from "./language/languageReducer";
import recommendProductsReducer from "./recommendProducts/recommendProductsReducer";

const rootReducer = combineReducers({
  language: languageReducer,
  recommendProducts: recommendProductsReducer,
});

// Configure the store with the combined reducer
const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
```

## Using Selectors in React Components

Selectors are functions that extract specific pieces of state from the Redux store.

### Example: Using Selectors in a Component

```typescript
import { useSelector } from "react-redux";
import { RootState } from "./store";

const Header: React.FC = () => {
  const language = useSelector((state: RootState) => state.language.language);
  const languageList = useSelector((state: RootState) => state.language.languageList);

  return (
    <div>
      <h1>Current Language: {language}</h1>
      <ul>
        {languageList.map((lang) => (
          <li key={lang}>{lang}</li>
        ))}
      </ul>
    </div>
  );
};
```

## Thunks with Redux / Redux中的Thunk

Redux Thunk lets dispatched functions perform asynchronous work and dispatch plain actions as results. Redux Toolkit includes thunk in `configureStore` by default; install and add it manually only when using a bare Redux store. The typed examples below use the `RootState` and `AppDispatch` from their matching thunk-enabled stores, following the [Redux TypeScript thunk guidance](https://redux.js.org/usage/usage-with-typescript#type-checking-redux-thunks).

## Installation

For a bare Redux store, install redux-thunk:

```bash
npm install redux-thunk
```

## Configuration

With Redux Toolkit, redux-thunk is included by default in the middleware pipeline. If you are using an older setup, you need to manually apply the middleware.

### Redux Toolkit Setup

```typescript
import { configureStore } from "@reduxjs/toolkit";
import rootReducer from "./reducers";

const store = configureStore({
  reducer: rootReducer,
});

// This store includes the default thunk middleware.
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export default store;
```

### Manual Setup (Without Redux Toolkit)

```typescript
import { createStore, applyMiddleware } from "redux";
import { thunk } from "redux-thunk";
import rootReducer from "./reducers";

const manualStore = createStore(rootReducer, applyMiddleware(thunk));

export type ManualRootState = ReturnType<typeof manualStore.getState>;
export type ManualAppDispatch = typeof manualStore.dispatch;
export default manualStore;
```

## Usage

To use Redux-Thunk, create action creators that return functions instead of action objects.

### Example: Thunk Action Creator

```typescript
import axios from "axios";
import type { ThunkAction } from "redux-thunk";
import type { UnknownAction } from "redux";
import type { RootState } from "../store";
import {
  fetchRecommendProductsStart,
  fetchRecommendProductsSuccess,
  fetchRecommendProductsFail,
} from "./actions";

export const fetchRecommendProducts = (): ThunkAction<Promise<void>, RootState, unknown, UnknownAction> => async (dispatch) => {
  dispatch(fetchRecommendProductsStart());
  try {
    const { data } = await axios.get("http://example.com/api/products");
    dispatch(fetchRecommendProductsSuccess(data));
  } catch (error) {
    dispatch(fetchRecommendProductsFail(error));
  }
};
```

### Connecting Thunk Actions to Components

Dispatch the thunk action from your React component.

```typescript
import { useDispatch } from "react-redux";
import type { AppDispatch } from "./store";
import { useEffect } from "react";
import { fetchRecommendProducts } from "./actions";

const ProductList: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    dispatch(fetchRecommendProducts());
  }, [dispatch]);

  // Render component
};
```

## Redux Middleware / Redux中间件

In Redux, middleware is a higher-order function that wraps the dispatch function, allowing you to execute code in between the action being dispatched and the action reaching the reducer. Middleware is commonly used for handling asynchronous actions, logging, error reporting, and more.

## Defining Middleware in Redux

Middleware in Redux can be defined using the following formula:

```typescript
const middleware = (store) => (next) => (action) => {
  // Middleware logic here
};
```

In this formula:

- `store` is the Redux store instance.
- `next` is the next middleware in the chain or the original `dispatch` function if the current middleware is the last one in the chain.
- `action` is the action being dispatched.

## Middleware Invocation

When an action is dispatched, the middleware will be invoked in the following manner:

```typescript
middleware(store)(next)(action);
```

This allows the middleware to interact with the `store`, perform operations before and after the action is dispatched, and then pass control to the next middleware or reducer.

## Example Middleware: Logging

Here's an example of a Redux middleware that logs the current state, the action being dispatched, and the state after the action has been dispatched:

```typescript
import { Middleware } from "redux";

export const actionLog: Middleware = (store) => (next) => (action) => {
  console.log("Current state:", store.getState());
  console.log("Dispatching action:", action);
  next(action);
  console.log("Next state:", store.getState());
};
```

In this example:

- Before the action is dispatched, the current state is logged.
- The action is then dispatched using `next(action)`.
- After the action is dispatched, the next state is logged.

## Using Middleware with Redux Toolkit

The `configureStore` function from Redux Toolkit simplifies the process of setting up middleware. Here is how you can add the `actionLog` middleware to your store:

```typescript
import { configureStore } from "@reduxjs/toolkit";
import rootReducer from "./reducers";
import { actionLog } from "./middlewares";

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(actionLog),
});
```

In this code:

- `getDefaultMiddleware` is a function provided by Redux Toolkit that returns the default list of middleware (like `redux-thunk`).
- The `concat` method is used to add the `actionLog` middleware to the list of default middleware.

## Asynchronous Actions with Middleware

Middleware is particularly useful for handling asynchronous actions. For example, the popular `redux-thunk` middleware allows you to write action creators that return a function instead of an action:

```typescript
import type { ThunkAction } from "redux-thunk";
import type { ManualRootState } from "./store";

// An example of an asynchronous action using redux-thunk
type FetchUserAction =
  | { type: "FETCH_USER_REQUEST" }
  | { type: "FETCH_USER_SUCCESS"; payload: unknown }
  | { type: "FETCH_USER_FAILURE"; error: unknown };

export const fetchUserData = (): ThunkAction<Promise<void>, ManualRootState, unknown, FetchUserAction> => async (dispatch) => {
  dispatch({ type: "FETCH_USER_REQUEST" });
  try {
    const response = await fetch("/api/user");
    const data = await response.json();
    dispatch({ type: "FETCH_USER_SUCCESS", payload: data });
  } catch (error) {
    dispatch({ type: "FETCH_USER_FAILURE", error });
  }
};
```

In this example:

- The `fetchUserData` action creator returns a function that performs an asynchronous fetch request.
- It dispatches different actions based on the success or failure of the request.

## Common Middleware Patterns

### Logging

Logging middleware can help you debug your Redux store by logging every action and state change:

```typescript
const logger: Middleware = (store) => (next) => (action) => {
  console.log('Dispatching:', action);
  let result = next(action);
  console.log('Next state:', store.getState());
  return result;
};
```

### Error Reporting

Error reporting middleware can catch errors in the dispatched actions and report them to an error tracking service:

```typescript
const errorReporter: Middleware = (store) => (next) => (action) => {
  try {
    return next(action);
  } catch (err) {
    console.error('Caught an exception!', err);
    // Report the error to an external service
    throw err;
  }
};
```

### Async Operations

Handling async operations, such as data fetching, is another common use case for middleware:

```typescript
const asyncMiddleware: Middleware = (store) => (next) => async (action) => {
  if (typeof action === 'function') {
    return action(store.dispatch, store.getState);
  }
  return next(action);
};
```

**See also / 另见：** [Redux Toolkit reference / Redux Toolkit 参考](redux-toolkit-reference.md).
