# React 本地状态的对象和数组怎样按身份更新？

这页保留旧课程里的列表追加、按 ID 切换对象字段和子组件回调练习。setter 接收 updater 时，React 用排队中的前一状态计算下一值；数组与对象要创建新容器，不能原地修改 state。一次事件读取状态快照的完整过程见[React 如何把一次用户操作变成界面更新？](../../../../frontend/frameworks/react-basics.md#处理器读到的是本次界面的状态快照)。

~~~tsx
import { useState } from "react";

type Box = { id: number; on: boolean };

function BoxList() {
  const [boxes, setBoxes] = useState<Box[]>([
    { id: 1, on: false },
    { id: 2, on: true },
  ]);

  function addBox() {
    setBoxes(previous => [
      ...previous,
      { id: Math.max(0, ...previous.map(box => box.id)) + 1, on: false },
    ]);
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
        <button
          key={box.id}
          type="button"
          aria-pressed={box.on}
          onClick={() => toggleBox(box.id)}
        >
          方块 {box.id}：{box.on ? "开" : "关"}
        </button>
      ))}
    </>
  );
}
~~~

toggleBox 通过稳定 ID 找到目标，而不是猜测“当前第几项”；列表重排后，状态仍跟随同一对象身份。若子组件也要改变这份状态，把 toggleBox 作为 prop 传下去；多个同级组件共享值时，由最近共同父组件持有 state，见[如何在 React 中组合组件与复用行为？](../../../../frontend/frameworks/react-component-composition.md#把状态放在共同使用者之上的最近一层)。只需隐藏或展示局部内容时，条件渲染模式见同章“组合组件与旧式逻辑复用接口”。
