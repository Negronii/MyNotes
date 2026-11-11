# React 本地状态的对象和数组怎样按身份更新？

**案例背景。** 一个方块列表要能添加方块、切换每个方块的开关。`BoxList` 持有整组状态，`BoxItem` 收到当前方块并把点击意图回传给父组件：数据向下传，操作回调向上交。setter 使用前一份状态计算下一份；每次更新创建新数组，复用未改动的对象，只为被切换的目标对象或新添加的方块创建新对象，不在旧 state（状态）上原地修改。一次事件中的状态快照见[React 如何把一次用户操作变成界面更新？](../../../../frontend/frameworks/react-basics.md#处理器读到的是本次界面的状态快照)。

~~~tsx
import { useState } from "react";

type Box = { id: number; on: boolean };

type BoxItemProps = {
  box: Box;
  onToggle: (id: number) => void;
};

function BoxItem({ box, onToggle }: BoxItemProps) {
  return (
    <button
      type="button"
      aria-pressed={box.on}
      onClick={() => onToggle(box.id)}
    >
      方块 {box.id}：{box.on ? "开" : "关"}
    </button>
  );
}

function BoxList() {
  const [boxes, setBoxes] = useState<Box[]>([
    { id: 1, on: false },
    { id: 2, on: true },
  ]);

  function addBox() {
    setBoxes(previous => {
      const largestId = Math.max(
        0, ...previous.map(box => box.id)
      );
      return [...previous, { id: largestId + 1, on: false }];
    });
  }

  function toggleBox(id: number) {
    setBoxes(previous =>
      previous.map(box =>
        box.id === id ? { ...box, on: !box.on } : box
      )
    );
  }

  return (
    <>
      <button type="button" onClick={addBox}>添加方块</button>
      {boxes.map(box => (
        <BoxItem key={box.id} box={box} onToggle={toggleBox} />
      ))}
    </>
  );
}
~~~

初始列表为 `[{ id: 1, on: false }, { id: 2, on: true }]`。点击“方块 2”时，子组件调用父组件传来的 `onToggle(2)`。父组件的函数式 updater（更新函数）拿到队列中的上一份数组，用 `map` 创建新数组；只为 `id === 2` 的对象展开出新对象并翻转 `on`，方块 1 保持关闭，方块 2 也变成关闭。React 随后使用新数组 render（渲染）列表。

| 点击“方块 2”后的值 | 内容变化 | 与上一份状态的对象关系 |
|---|---|---|
| 外层 `boxes` 数组 | 元素仍为两个，第二项换成新对象 | 新数组 |
| `id: 1` 的方块 | `on` 仍为 `false` | 复用原对象 |
| `id: 2` 的方块 | `on: true → false` | 新对象，保留同一个 ID |

点击“添加方块”时，另一个 updater 同样从前一份数组找最大 ID，再返回包含新对象的数组；此时最大 ID 是 2，所以新增的是 `id: 3, on: false`，已有方块对象继续复用。使用 `previous` 是因为同一事件处理器中的状态变量仍是本轮 render 的快照，调用 setter 只是安排更新，不会当场改写该变量；updater 能按排队顺序基于最新前值计算。若从最大 ID 为 2 的状态出发，在同一事件处理器中连续安排两次添加，第二个 updater 会看到刚加入的 ID 3，从而生成 ID 4。

`id` 是数据里的身份字段，父组件用它定位要改的对象。`key` 是 React 用来匹配同级列表项、在重排时保留对应组件实例的提示；React 不会把 `key` 作为 `BoxItem` 的普通 prop 传入，所以子组件仍通过 `box.id` 报告点击对象。父组件用 `box.id` 定位要切换的对象，也把这个值作为该行的 React `key`；二者用途不同。若把数组下标当 key，插入或重排后，带有本地输入等组件状态的行可能会跟着位置错配。

把共享的 `boxes` 放在最近共同父组件，让每个 `BoxItem` 只展示自己的 `box` 并上报操作；不需要在子组件内复制一份 `on`，也不需要改全局状态。这个所有权与向下传值、向上回调的模式见[如何在 React 中组合组件与复用行为？](../../../../frontend/frameworks/react-component-composition.md#把状态放在共同使用者之上的最近一层)。

> [!info]- 来源与版本核验（React 19.3；2026-11-12）
> - 数组和数组内对象按不可变方式更新：[Updating Arrays in State](https://react.dev/learn/updating-arrays-in-state)，React 官方文档。
> - setter 的状态快照和 updater 队列语义：[State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)、[Queueing a Series of State Updates](https://react.dev/learn/queueing-a-series-of-state-updates)，React 官方文档。
> - 父子 props 与在共同父组件中共享状态：[Passing Props to a Component](https://react.dev/learn/passing-props-to-a-component)、[Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)，React 官方文档。
> - 稳定 key 在插入、删除和重排时帮助 React 对应列表项；key 不作为组件 prop：[Rendering Lists](https://react.dev/learn/rendering-lists)，React 官方文档。
> - 本地状态受组件类型、树中位置与 key 对应关系影响：[Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)，React 官方文档。
