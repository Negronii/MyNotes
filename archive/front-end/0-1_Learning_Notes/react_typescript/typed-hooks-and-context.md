# Context 与自定义 Hook 怎样建立类型边界？

课程购物车练习要让“加入机器人”和“查看购物车”两个组件使用同一份条目状态。Context（上下文）把值传给后代，Provider（提供者）规定这份值从哪一层开始提供；自定义 Hook（自定义钩子）useCart 集中检查消费者是否位于 Provider 内。下面代码采用 React 19、对应的 `@types/react` 类型与自动 JSX 转换，使用 `<CartContext value={...}>` 语法；在已创建的 React root（根节点）中渲染 `<CartExample />`，入口会把按钮和列表放进同一个 `CartProvider`。阅读时沿着“入口 → Provider 的 reducer（归约函数）状态 → 加入/清空 action（动作）→ 两个消费者更新”跟踪。迁入同样启用自动 JSX 转换、使用 `@types/react` 18.3 类型定义的 React 18 项目时，Provider 标签要写成 `<CartContext.Provider value={...}>` 和 `</CartContext.Provider>`。

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
  const { items, addItem } = useCart();
  const alreadyAdded = items.some(item => item.id === robot.id);

  return (
    <button
      type="button"
      disabled={alreadyAdded}
      onClick={() => addItem(robot)}
    >
      加入购物车
    </button>
  );
}

export function CartContents() {
  const { items, clearItems } = useCart();

  return (
    <section>
      <p aria-live="polite">
        {items.length === 0
          ? "购物车为空"
          : `购物车有 ${items.length} 件商品`}
      </p>
      <ul>
        {items.map(item => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
      <button
        type="button"
        disabled={items.length === 0}
        onClick={clearItems}
      >
        清空购物车
      </button>
    </section>
  );
}

export function CartExample() {
  const robot = { id: 7, name: "Ada" };

  return (
    <CartProvider>
      <AddRobotButton robot={robot} />
      <CartContents />
    </CartProvider>
  );
}
~~~

初次渲染时，`CartExample` 创建 id 7、名字 Ada 的合成条目。`CartProvider` 的 reducer 状态是 `[]`；`AddRobotButton` 与 `CartContents` 各自沿组件树向上寻找最近的 `CartContext` Provider。本例两者找到的是同一个 `CartProvider`，所以它们读取同一份 `CartValue`。若树里有更近的嵌套 Provider，消费者会改读那个 Provider 提供的值。此时界面显示“购物车为空”，加入按钮可用、清空按钮禁用。`createContext<CartValue | null>(null)` 的 `null` 是上方没有对应 Provider 时的默认值，不会随时间变成购物车状态。

点击“加入购物车”后，处理器派发 action（动作）`{ type: "itemAdded", item: { id: 7, name: "Ada" } }`。Reducer（归约函数）收到旧数组 `[]` 和 action，返回新数组 `[{ id: 7, name: "Ada" }]`，没有原地修改旧状态。Provider 以新数组形成新的 `{ items, addItem, clearItems }` 值；两个消费者各自从最近的 Provider 读新值，列表显示“Ada”。当前 `AddRobotButton` 通过 `items.some` 发现相同 id 后只禁用自己；`addItem` 每次仍会派发新增动作，reducer 每次都追加一项。若别的调用者重复派发同一个 id，数组中就会有重复 id；示例中的列表因此假设每个条目 id 唯一，避免重复 React key。清空按钮派发 `itemsCleared`，reducer 返回 `[]`，两个消费者更新回空状态。

## 类型边界在哪里？

`CartItem` 描述条目字段，`CartAction` 是判别联合类型：`itemAdded` 必须提供 `item`；`itemsCleared` 只需有 `type`，清空分支不读取别的字段。`cartReducer` 根据 `action.type` 选择追加新数组或返回空数组；`useReducer` 把状态与派发函数交给 `CartProvider`，实际状态归 Provider 所有。

`CartContext` 的类型允许 `CartValue` 或 `null`，因为消费者上方可能没有对应的 Provider。`useCart` 读到 `null` 时抛出指明缺少 Provider 的错误；非空分支由 TypeScript 缩窄为 `CartValue`，调用方不用重复空值判断，也不必用非空断言掩盖错误。

Context 对象只标识可提供、可读取的值，不自己保存变化中的状态。这里的共享状态来自同一个 `CartProvider` 中的 `useReducer`；消费者各自向上寻找最近 Provider，最近 Provider 相同时才读取同一份 state（状态）。`CartContext` 不是 Redux store（Redux 状态仓库），它只让组件树按最近 Provider 读取所提供的值。若自定义 Hook 自己调用 `useState`，不同组件分别调用该 Hook 会有独立 state。自定义 Hook 复用有状态逻辑，不自动共享 Hook 内部状态。

类组件也可通过 `Context.Consumer` 读取值；这只改变读取方式，不会让 Context 成为状态容器。这页聚焦客户端树中的购物车类型与状态边界。若状态由服务端拥有，放进 Context 不会自动提供查询缓存、刷新或请求协调；状态所有权与服务端数据的区别见[如何在 React 中组合组件与复用行为？](../../../../frontend/frameworks/react-component-composition.md)。

> [!info]- 来源
> - 自动 JSX 转换让 JSX 无需单独导入 React 命名空间；React 19 要求使用该转换：[React 19 Upgrade Guide — New JSX Transform](https://react.dev/blog/2024/04/25/react-19-upgrade-guide#new-jsx-transform-is-now-required)，React 官方文档，核验日期：2026-11-12。
> - Context 默认值、最近 Provider、值变化时订阅组件重新渲染，以及 Context 对象本身不保存数据：[createContext](https://react.dev/reference/react/createContext)、[useContext](https://react.dev/reference/react/useContext)，React 官方 API，核验日期：2026-11-12。
> - Reducer 接收当前状态与 action 并返回下一状态；reducer 应保持纯净、避免修改旧状态：[useReducer](https://react.dev/reference/react/useReducer)、[Extracting State Logic into a Reducer](https://react.dev/learn/extracting-state-logic-into-a-reducer)，React 官方文档，核验日期：2026-11-12。
> - React 19 使用 `<Context>` 作为 Provider；更早版本使用 `<Context.Provider>`：[createContext](https://react.dev/reference/react/createContext)、[React 19](https://react.dev/blog/2024/12/05/react-19)，React 官方文档，核验日期：2026-11-12。
> - 自定义 Hook 共享有状态逻辑而不共享每次调用的独立 state：[Reusing Logic with Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks)，React 官方文档，核验日期：2026-11-12。
> - `PropsWithChildren`、React 节点与 React 组件类型定义：[React type declarations](https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/react/index.d.ts)，DefinitelyTyped，核验日期：2026-11-12。
