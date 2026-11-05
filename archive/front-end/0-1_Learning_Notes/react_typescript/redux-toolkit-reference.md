# How does Redux Toolkit reduce boilerplate in typed Redux apps? / Redux Toolkit 如何减少带类型 Redux 应用的样板代码？

Redux Toolkit provides `configureStore`, `createSlice`, and `createAsyncThunk` to assemble store, reducer, and request-lifecycle logic. This archived example is checked against the stated 2.11.0 documentation; update the version context when reusing it. / Redux Toolkit 提供 `configureStore`、`createSlice` 和 `createAsyncThunk` 来组织 store、reducer 与请求生命周期逻辑。本归档示例按文中标明的 2.11.0 文档核对；复用时应更新版本背景。

## Redux Toolkit / Redux Toolkit

Redux Toolkit is the official, recommended way to write Redux logic. It simplifies store setup, reducers, and immutable updates; the API examples below were checked against [Redux Toolkit 2.11.0](https://github.com/reduxjs/redux-toolkit/blob/v2.11.0/docs/usage/usage-with-typescript.md).

## Creating an App with RTK

These commands preserve the course's legacy CRA template setup; CRA is deprecated for new projects:

```sh
## Redux + Plain JS template
npx create-react-app my-app --template redux

## Redux + TypeScript template
npx create-react-app my-app --template redux-typescript
```

To install Redux Toolkit in an existing project, run:

```sh
npm install @reduxjs/toolkit
```

## createSlice

The `createSlice` function is the standard approach for writing Redux logic. It accepts an initial state, an object of reducer functions, and a "slice name", and automatically generates action creators and action types.

### Example Usage

Here's an example of how to use `createSlice`:

```typescript
import { createSlice, createAction, configureStore } from "@reduxjs/toolkit";
import { combineReducers } from "redux";

// Define actions using createAction
const incrementBy = createAction<number>("incrementBy");
const decrementBy = createAction<number>("decrementBy");

// Create a counter slice
const counterSlice = createSlice({
  name: "counter",
  initialState: 0,
  reducers: {
    increment: (state) => state + 1,
    decrement: (state) => state - 1,
    multiply: {
      reducer: (state, action) => state * action.payload,
      prepare: (value = 2) => ({ payload: value }), // default value is 2
    },
  },
  extraReducers: (builder) => {
    builder.addCase(incrementBy, (state, action) => state + action.payload);
    builder.addCase(decrementBy, (state, action) => state - action.payload);
  },
});

// Create a user slice
const userSlice = createSlice({
  name: "user",
  initialState: { name: "", age: 20 },
  reducers: {
    setUserName: (state, action) => {
      state.name = action.payload; // Using Immer to handle state mutations
    },
  },
  extraReducers: (builder) => {
    builder.addCase(counterSlice.actions.increment, (state) => {
      state.age += 1;
    });
  },
});

// Combine reducers
const rootReducer = combineReducers({
  counter: counterSlice.reducer,
  user: userSlice.reducer,
});

// Configure store
const store = configureStore({
  reducer: rootReducer,
  devTools: process.env.NODE_ENV !== 'production', // Enable Redux DevTools only in development
});

store.dispatch(counterSlice.actions.increment());
store.dispatch(counterSlice.actions.multiply(3));
store.dispatch(userSlice.actions.setUserName("Alice"));

console.log(store.getState());
```

## configureStore

The `configureStore` function simplifies the setup process for the Redux store. It is strongly recommended over the traditional `createStore` method.

### Options

The `configureStore` function accepts an options object with the following properties:

- **reducer**: A single reducer function or an object of slice reducers.
- **middleware**: An array of middleware functions or a function that returns the middleware array.
- **devTools**: A boolean or configuration object for Redux DevTools.
- **preloadedState**: The initial state.
- **enhancers**: Additional store enhancers.

### Example Usage

Here's an example of how to configure a Redux store:

```typescript
import { configureStore } from "@reduxjs/toolkit";
import { combineReducers } from "redux";
import logger from 'redux-logger';

const rootReducer = combineReducers({
  counter: counterSlice.reducer,
  user: userSlice.reducer,
});

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(logger),
  devTools: process.env.NODE_ENV !== 'production', // Enable Redux DevTools only in development
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export default store;
```

## createAsyncThunk

The `createAsyncThunk` function simplifies handling asynchronous logic. It accepts a Redux action type string and a callback function that returns a promise. It generates promise lifecycle action types based on the provided action type prefix.

### Example Usage

Here's an example of how to use `createAsyncThunk`:

```typescript
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";

interface ProductDetailsState {
  loading: boolean;
  error: string | null;
  data: { name: string } | null;
}

const initialState: ProductDetailsState = {
  loading: false,
  error: null,
  data: null,
};

export const fetchProductDetails = createAsyncThunk(
  "productDetails/fetchProductDetails",
  async (productId: string) => {
    const response = await axios.get<{ name: string }>(`/api/products/${productId}`);
    // The generic describes the expected payload; it does not validate the JSON at runtime.
    return response.data;
  }
);

const productDetailsSlice = createSlice({
  name: "productDetails",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchProductDetails.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProductDetails.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
        state.error = null;
      })
      .addCase(fetchProductDetails.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? "Request failed";
      });
  },
});

export const { reducer: productDetailsReducer } = productDetailsSlice;
```

### Using in a Component

To use the `fetchProductDetails` thunk in a React component:

This example assumes the store registers `productDetailsSlice.reducer` under the `productDetails` key; derive `RootState` and `AppDispatch` from that configured store.

```typescript
import React, { useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { fetchProductDetails } from "./productDetailsSlice";
import type { RootState, AppDispatch } from "./store";

const ProductDetails = ({ productId }: { productId: string }) => {
  const dispatch = useDispatch<AppDispatch>();
  const { data, loading, error } = useSelector(
    (state: RootState) => state.productDetails
  );

  useEffect(() => {
    if (productId) {
      dispatch(fetchProductDetails(productId));
    }
  }, [productId, dispatch]);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error}</p>;

  return <div>{data && <p>{data.name}</p>}</div>;
};

export default ProductDetails;
```

### Custom useDispatch Hook

To handle type conflicts between `ReduxAsyncThunk` and `any` type at `const dispatch = useDispatch();`, define a custom hook for `useDispatch`:

```typescript
import { useDispatch as useReduxDispatch } from "react-redux";
import { AppDispatch } from "./store";

export const useDispatch = () => useReduxDispatch<AppDispatch>();
```

Then, import `useDispatch` from this custom hook file instead of directly from `react-redux`.

**Sources checked 2026-10-15:** React 19.2 [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks), [`use`](https://react.dev/reference/react/use), [Effects](https://react.dev/learn/synchronizing-with-effects), [StrictMode](https://react.dev/reference/react/StrictMode), and [React type definitions](https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/react/index.d.ts); TypeScript 5.9.3 [`noImplicitAny`](https://www.typescriptlang.org/tsconfig/#noImplicitAny) and [erased types](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types); [React Router v6.3.0 API](https://github.com/remix-run/react-router/blob/v6.3.0/docs/api.md); [Redux Toolkit 2.11.0 TypeScript usage](https://github.com/reduxjs/redux-toolkit/blob/v2.11.0/docs/usage/usage-with-typescript.md); [React-Redux TypeScript usage](https://react-redux.js.org/using-react-redux/usage-with-typescript); [Axios error handling](https://axios-http.com/docs/handling_errors); [i18next interpolation](https://www.i18next.com/translation-function/interpolation); [Fielding's REST dissertation](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm).

**Reference checked 2026-10-15:** [Redux Toolkit 2.11.0 TypeScript usage](https://github.com/reduxjs/redux-toolkit/blob/v2.11.0/docs/usage/usage-with-typescript.md).
