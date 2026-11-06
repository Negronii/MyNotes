# TypeScript 如何给 Context 与自定义 Hook 建立边界？

组件状态归属、Context 与自定义 Hook 解决的问题见[如何在 React 中组合组件与复用行为？](../../../../frontend/frameworks/react-component-composition.md)。本页保留购物车练习中的类型边界：Context 默认值写成 null，通过一个自定义 Hook 在使用位置检查 Provider 是否存在。

~~~tsx
import {
  createContext,
  useContext,
  useReducer,
  type PropsWithChildren,
} from "react";

type CartItem = { id: number; name: string };
type CartValue = {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  clearItems: () => void;
};

type CartAction =
  | { type: "itemAdded"; item: CartItem }
  | { type: "itemsCleared" };

function cartReducer(items: CartItem[], action: CartAction): CartItem[] {
  return action.type === "itemAdded" ? [...items, action.item] : [];
}

const CartContext = createContext<CartValue | null>(null);

export function CartProvider({ children }: PropsWithChildren) {
  const [items, dispatch] = useReducer(cartReducer, [] as CartItem[]);

  function addItem(item: CartItem) {
    dispatch({ type: "itemAdded", item });
  }

  function clearItems() {
    dispatch({ type: "itemsCleared" });
  }

  return (
    <CartContext value={{ items, addItem, clearItems }}>
      {children}
    </CartContext>
  );
}

export function useCart(): CartValue {
  const value = useContext(CartContext);
  if (value === null) {
    throw new Error("useCart 必须在 CartProvider 内调用");
  }
  return value;
}

export function AddRobotButton({ robot }: { robot: CartItem }) {
  const { addItem } = useCart();
  return (
    <button type="button" onClick={() => addItem(robot)}>
      加入购物车
    </button>
  );
}
~~~

`useReducer` 把购物车的状态转换集中到 `cartReducer`：`itemAdded` 在已有数组后追加一项，`itemsCleared` 返回空数组。`CartAction` 联合类型规定每种动作允许携带什么字段；`dispatch` 接收动作，React 再用当前状态计算下一状态。这份状态仍属于 `CartProvider` 组件，Context 负责向后代传递，并没有创建 Redux store。

createContext 的泛型描述 Provider 可能提供的值；Consumer hook 先检查 null，再返回已收窄类型。React 19 可直接把 Context 对象写成 Provider；旧 React 项目继续使用 `CartContext.Provider`。若 Hook 返回值依赖 Context，它不会自动让另一个 Hook 调用共用 state；共享实例来自同一个 Provider 持有的 state。类组件仍可用 `Context.Consumer` 读取，但新逻辑无需为类组件另写一套状态容器。

> [!info]- 来源
> - createContext、useContext 与通过 Provider 传值：[React createContext](https://react.dev/reference/react/createContext)、[Passing Data Deeply with Context](https://react.dev/learn/passing-data-deeply-with-context)，React 19.3 文档，核对日期：2026-11-06。
> - `useReducer` 的 state、dispatch 与纯 reducer 更新：[React useReducer](https://react.dev/reference/react/useReducer)，React 19.3 文档，核对日期：2026-11-06。
> - 自定义 Hook 复用逻辑但各次调用拥有自己的 Hook state：[Reusing Logic with Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks)，React 19.3 文档，核对日期：2026-11-06。
