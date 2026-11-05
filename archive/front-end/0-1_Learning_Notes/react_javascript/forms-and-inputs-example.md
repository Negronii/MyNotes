# How do controlled React inputs update a form object? / React 受控输入如何更新表单对象？

Keep each control's value in component state and handle its change event by replacing the relevant field. For checkboxes, read `checked`; for text-like controls, read `value`. Associate labels with their controls.

## Forms and Inputs in React

Handling forms and inputs with state in React:

```jsx
import React from "react";

export default function Form() {
  const [formData, setFormData] = React.useState({
    firstName: "",
    lastName: "",
    email: "",
    comment: "",
    isFriendly: true,
    employment: "",
    favColor: "",
  });

  function handleChange(e) {
    const { name, value, type, checked } = e.target;
    setFormData(prevFormData => ({
      ...prevFormData,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    console.log(formData); // Handle form submission logic
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="firstName">First name</label>
      <input
        type="text"
        id="firstName"
        placeholder="First Name"
        onChange={handleChange}
        name="firstName"
        value={formData.firstName}
      />
      <label htmlFor="lastName">Last name</label>
      <input
        type="text"
        id="lastName"
        placeholder="Last Name"
        onChange={handleChange}
        name="lastName"
        value={formData.lastName}
      />
      <label htmlFor="email">Email</label>
      <input
        type="email"
        id="email"
        placeholder="Email"
        onChange={handleChange}
        name="email"
        value={formData.email}
      />
      <label htmlFor="comment">Comment</label>
      <textarea
        id="comment"
        placeholder="Comment"
        onChange={handleChange}
        name="comment"
        value={formData.comment}
      />
      <input
        type="checkbox"
        id="isFriendly"
        checked={formData.isFriendly}
        onChange={handleChange}
        name="isFriendly"
      />
      <label htmlFor="isFriendly">Are you friendly?</label>
      <fieldset>
        <legend>Current employment status</legend>
        <input
          type="radio"
          id="unemployed"
          name="employment"
          value="unemployed"
          checked={formData.employment === "unemployed"}
          onChange={handleChange}
        />
        <label htmlFor="unemployed">Unemployed</label>
        <input
          type="radio"
          id="full-time"
          name="employment"
          value="full-time"
          checked={formData.employment === "full-time"}
          onChange={handleChange}
        />
        <label htmlFor="full-time">Full-time</label>
        <input
          type="radio"
          id="part-time"
          name="employment"
          value="part-time"
          checked={formData.employment === "part-time"}
          onChange={handleChange}
        />
        <label htmlFor="part-time">Part-time</label>
      </fieldset>
      <label htmlFor="favColor">What is your favorite color?</label>
      <select
        id="favColor"
        value={formData.favColor}
        onChange={handleChange}
        name="favColor"
      >
        <option value="">Choose a color</option>
        <option value="red">Red</option>
        <option value="blue">Blue</option>
        <option value="green">Green</option>
        <option value="yellow">Yellow</option>
      </select>
      <button type="submit">Submit</button>
    </form>
  );
}
```

In this form example, the state `formData` manages multiple inputs, including text fields, checkboxes, radio buttons, and a select dropdown. The `handleChange` function updates the state based on the input values. The `handleSubmit` function handles form submission, where you can add logic to send the form data to a backend.

**See also / 另见：** [Semantic HTML and accessibility / 语义化 HTML 与无障碍交互](../../../../frontend/html-css/html-and-css-basics.md) for labels and validation feedback.
