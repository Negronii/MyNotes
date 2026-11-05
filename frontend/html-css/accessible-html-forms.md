# How do semantic HTML forms support keyboard and assistive-technology users? / 语义化 HTML 表单如何支持键盘与辅助技术用户？

Use native elements for their built-in meaning and behavior: a `label` gives a form control a programmatic name, a `button` supports keyboard activation, and an `a href` represents navigation. Keep focus visible; describe validation errors in text, associate them with the field, and focus the invalid field after a custom submission is rejected. ARIA adds information for assistive technology but does not create keyboard behavior or native validation. / 使用原生元素获得其内建语义与行为：`label` 为表单控件提供程序化名称，`button` 支持键盘激活，`a href` 表示导航。保持焦点可见；用文字描述校验错误并关联到字段，自定义提交被拒绝时将焦点移到无效字段。ARIA 为辅助技术提供信息，但不会创建键盘行为或原生校验。

Use heading levels to express structure, landmarks such as `main` and `nav` to identify regions, and `alt` text that conveys an informative image's purpose. Use empty alternative text (`alt=""`) for decorative images. Keep source order meaningful because CSS visual placement does not change document order for nonvisual presentation. Do not rely on color or position alone to communicate a required state.

This form keeps the browser's `required` and `type="email"` constraints as the no-JavaScript baseline. Once the custom handler is installed, it reports the invalid state in text, associates the error through `aria-describedby`, marks the field, and moves focus to it.

```html
<form id="subscribe" action="/subscribe" method="post">
  <label for="email">Email address</label>
  <input id="email" name="email" type="email" required
         aria-describedby="email-help email-error">
  <p id="email-help">Enter an address such as name@example.com.</p>
  <p id="email-error" hidden></p>
  <button type="submit">Subscribe</button>
</form>

<style>
  :focus { outline: 3px solid currentColor; outline-offset: 2px; }
</style>

<script>
const form = document.querySelector("#subscribe");
const email = form.elements.namedItem("email");
const error = document.querySelector("#email-error");

function clearError() {
  error.textContent = "";
  error.hidden = true;
  email.removeAttribute("aria-invalid");
}

email.addEventListener("input", () => {
  if (email.validity.valid) clearError();
});

form.addEventListener("submit", event => {
  if (email.validity.valid) {
    clearError();
    return;
  }

  event.preventDefault();
  error.textContent = email.validity.valueMissing
    ? "Enter an email address."
    : "Enter a valid email address.";
  error.hidden = false;
  email.setAttribute("aria-invalid", "true");
  email.focus();
});
form.noValidate = true; // Enable custom feedback after the handler is ready.
</script>
```

Before JavaScript installs the handler, the native constraints can reject an invalid submission. After installation, Tab reaches the input and button; invalid submission focuses the field and associates its visible error with the accessible description. The client check improves feedback, but the server must validate submitted values before accepting them. This is an example interaction, not a claim that one snippet makes an entire page conformant.

**Guidance:** [WAI form labels](https://www.w3.org/WAI/tutorials/forms/labels/), [WAI form notifications](https://www.w3.org/WAI/tutorials/forms/notifications/), [WAI image alternatives](https://www.w3.org/WAI/tutorials/images/), [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/) (focus visibility and identifying errors), and [ARIA Authoring Practices: keyboard interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/). Native semantics are defined by the [HTML Standard](https://html.spec.whatwg.org/).
