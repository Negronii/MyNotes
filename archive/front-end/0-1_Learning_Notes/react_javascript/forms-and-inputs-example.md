# React 受控表单怎样把输入写回组件状态？

本页保留旧课程中的文本框、文本区域、复选框、单选组和下拉框练习。控件值由 React state（状态）控制，变化处理器按字段名替换对象属性；checkbox（复选框）读取 checked，其余控件读取 value。

~~~tsx
import { useState, type FormEvent, type ChangeEvent } from "react";

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

  function updateText(
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) {
    const { name, value } = event.currentTarget;
    setValues(previous => ({ ...previous, [name]: value }));
  }

  function updateCheckbox(event: ChangeEvent<HTMLInputElement>) {
    const { name, checked } = event.currentTarget;
    setValues(previous => ({ ...previous, [name]: checked }));
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    console.log(values);
  }

  return (
    <form onSubmit={submit}>
      <label htmlFor="firstName">姓名</label>
      <input id="firstName" name="firstName" value={values.firstName} onChange={updateText} />

      <label htmlFor="comment">备注</label>
      <textarea id="comment" name="comment" value={values.comment} onChange={updateText} />

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
            onChange={updateText}
          />
          全职
        </label>
        <label>
          <input
            type="radio"
            name="employment"
            value="part-time"
            checked={values.employment === "part-time"}
            onChange={updateText}
          />
          兼职
        </label>
      </fieldset>

      <label htmlFor="color">颜色</label>
      <select id="color" name="color" value={values.color} onChange={updateText}>
        <option value="">请选择</option>
        <option value="blue">蓝色</option>
        <option value="green">绿色</option>
      </select>

      <button type="submit">提交</button>
    </form>
  );
}
~~~

用 value 或 checked 作为受控属性时，React state 是当前显示值的来源；单选按钮使用相同 name，点击新选项时把该选项的 value 写入 state。输入字段还需要可见且关联的 label、正确的文档语义与错误反馈，见[语义化 HTML 表单如何支持键盘与辅助技术用户？](../../../../frontend/html-css/accessible-html-forms.md#让控件名称提交值和动作明确)。state 更新快照和父子通信见[React 更新轮次](../../../../frontend/frameworks/react-basics.md#处理器读到的是本次界面的状态快照)与[组件状态归属](../../../../frontend/frameworks/react-component-composition.md#把状态放在共同使用者之上的最近一层)。

> [!info]- 来源
> - React 受控文本框、复选框、单选按钮和下拉框：[React input](https://react.dev/reference/react-dom/components/input)、[textarea](https://react.dev/reference/react-dom/components/textarea)、[select](https://react.dev/reference/react-dom/components/select)，React 19.3 文档，核对日期：2026-11-06。
> - 标签、fieldset、legend 与表单错误语义：[语义化 HTML 表单章节](../../../../frontend/html-css/accessible-html-forms.md)，WHATWG HTML 与 W3C WAI，核对日期：2026-11-06。
