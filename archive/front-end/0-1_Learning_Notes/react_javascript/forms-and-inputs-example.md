# React 受控表单怎样把输入写回组件状态？

**案例背景。** 用户填写姓名和备注，选择是否允许联系、工作状态与颜色，然后提交这份本地表单。这里的受控输入由 React state（状态）提供当前显示值：文本框、文本区域和选择框使用 `value`，复选框用布尔值 `checked`；单选项的 `value` 表示选项值，`checked` 表示该项当前是否选中。每次 `onChange`（变化处理器）都在处理器内调用 setter（状态设置函数）安排更新，但不会原地改写本次 render（渲染）的 `values` 快照。此练习只演示界面状态与提交快照，不实现服务端保存或字段校验。React 的状态快照与父组件状态归属见[更新轮次](../../../../frontend/frameworks/react-basics.md#处理器读到的是本次界面的状态快照)和[组件状态归属](../../../../frontend/frameworks/react-component-composition.md#把状态放在共同使用者之上的最近一层)。

~~~tsx
import { useState, type ChangeEvent, type FormEvent } from "react";

type FormValues = {
  firstName: string;
  comment: string;
  friendly: boolean;
  employment: string;
  color: string;
};

const initialValues: FormValues = {
  firstName: "",
  comment: "",
  friendly: false,
  employment: "",
  color: "",
};

export function ExampleForm() {
  const [values, setValues] = useState(initialValues);

  function updateValue(
    event: ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) {
    const { name, value } = event.currentTarget;
    setValues(previous => ({ ...previous, [name]: value }));
  }

  function updateCheckbox(event: ChangeEvent<HTMLInputElement>) {
    const { checked } = event.currentTarget;
    setValues(previous => ({ ...previous, friendly: checked }));
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    console.log(values);
  }

  return (
    <form onSubmit={submit}>
      <label htmlFor="firstName">姓名</label>
      <input
        id="firstName"
        name="firstName"
        value={values.firstName}
        onChange={updateValue}
      />

      <label htmlFor="comment">备注</label>
      <textarea
        id="comment"
        name="comment"
        value={values.comment}
        onChange={updateValue}
      />

      <label htmlFor="friendly">
        <input
          id="friendly"
          name="friendly"
          type="checkbox"
          checked={values.friendly}
          onChange={updateCheckbox}
        />
        允许联系
      </label>

      <fieldset>
        <legend>工作状态</legend>
        <label>
          <input
            type="radio"
            name="employment"
            value="full-time"
            checked={values.employment === "full-time"}
            onChange={updateValue}
          />
          全职
        </label>
        <label>
          <input
            type="radio"
            name="employment"
            value="part-time"
            checked={values.employment === "part-time"}
            onChange={updateValue}
          />
          兼职
        </label>
      </fieldset>

      <label htmlFor="color">颜色</label>
      <select
        id="color"
        name="color"
        value={values.color}
        onChange={updateValue}
      >
        <option value="">请选择</option>
        <option value="blue">蓝色</option>
        <option value="green">绿色</option>
      </select>

      <button type="submit">提交</button>
    </form>
  );
}
~~~

文本框、文本区域和选择框从首次渲染起就提供字符串 `value`；选择框的空字符串对应“请选择”。复选框从首次渲染起就提供布尔值 `checked`。两个单选按钮共用 `name="employment"`，所以浏览器把它们作为一组；单选项的 `value` 是写回 state 的选项标识，`checked` 才决定每一项是否选中。这里的共享处理器读取 `event.currentTarget.name` 作为对象字段名、读取 `event.currentTarget.value` 作为新字符串；`name` 到 `FormValues` 属性的映射是这段代码的约定，不是 React 自动完成的。

具体看一次更新：初始 `employment` 是空字符串，两项单选都未选。假定用户先输入姓名“林”，那次事件安排更新后，下一次 render 会读到 `firstName: "林"`。随后用户点击“兼职”，`updateValue` 收到 `name: "employment"`、`value: "part-time"`；updater（更新函数）用前一份对象复制字段，只覆盖 `employment`，因此姓名仍为“林”。处理器内的 `values` 变量仍是本次 render 的快照；React 随后用新 state 再渲染，得到全职 `checked={false}`、兼职 `checked={true}`。复选框则由独立处理器读取 `checked` 布尔值并更新 `friendly`。

受控输入的 `onChange` 要在事件处理器中立即安排 state 更新；处理器当前拿到的 state 仍是本轮快照，setter 不会在原地改变它。若处理器没有安排更新，React 会继续按受控属性显示本轮快照中的旧值。输入应在生命周期内保持受控或非受控模式；从 `undefined`/`null` 切换到字符串等受控值会在开发环境触发警告；本例的文本框、文本区域和选择框始终传字符串，复选框始终传布尔值。复选框的业务状态是是否选中，因此读 `checked`，不把选项提交值混作这个布尔状态。

若用户输入“林”、备注“周五下午联系”、勾选“允许联系”、选“兼职”和“绿色”，提交处理器记录的对象是：

~~~json
{
  "firstName": "林",
  "comment": "周五下午联系",
  "friendly": true,
  "employment": "part-time",
  "color": "green"
}
~~~

`preventDefault()` 阻止这个教学表单按浏览器默认动作导航或刷新；`console.log` 只展示提交时的 state 快照。真实应用还要决定如何做输入校验、显示错误并保存数据。控件的可见标签、单选组名称和错误反馈语义见[语义化 HTML 表单如何支持键盘与辅助技术用户？](../../../../frontend/html-css/accessible-html-forms.md#让控件名称提交值和动作明确)。

> [!info]- 来源
> - 状态 setter 请求下一次 render，当前处理器读取本轮状态快照：[React — State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)，React 19.3 文档，核验日期：2026-11-12。
> - `value`/`checked` 使输入受控，且变化处理器要立即安排与控件当前值对应的状态更新：[React `<input>`](https://react.dev/reference/react-dom/components/input)，React 19.3 文档，核验日期：2026-11-12。
> - 受控多行文本框使用 `value` 和 `onChange`：[React `<textarea>`](https://react.dev/reference/react-dom/components/textarea)，React 19.3 文档，核验日期：2026-11-12。
> - 受控选择框由 `<select value>` 选择匹配 option，变化处理器更新该值：[React `<select>`](https://react.dev/reference/react-dom/components/select)，React 19.3 文档，核验日期：2026-11-12。
> - 标签控件、以共同 `name` 组成的单选组、fieldset 与 legend：[WHATWG HTML Standard — Forms](https://html.spec.whatwg.org/multipage/forms.html)，§4.10.1.1 “Writing a form's user interface”，Living Standard，核验日期：2026-11-12。
> - 表单标签关联及其为辅助技术提供控件名称的作用：[W3C WAI — Labeling Controls](https://www.w3.org/WAI/tutorials/forms/labels/)，核验日期：2026-11-12。
