# How do native HTML controls collect form input? / 原生 HTML 控件如何收集表单输入？

Build forms from native inputs, buttons, selects, textareas, and labels. The input `type` determines the control's purpose, while `name` supplies the submitted field name; associate each control with a visible label. / 用原生 input、button、select、textarea 和 label 构建表单。input 的 `type` 决定控件用途，`name` 提供提交字段名；每个控件都应关联可见标签。

## HTML Form Elements

## The Input Element `<input>`

The `<input>` element is one of the most versatile and commonly used elements in HTML forms. It can be configured to accept different types of data through the `type` attribute.

### Useful `type` Values

#### `text`

A single-line text field. Line breaks are automatically removed from the input value.
```html
<input type="text">
```

#### `password`

A single-line text field whose displayed value is obscured. This does not encrypt the value or make an insecure connection safe; transport security and server-side handling are separate concerns.
```html
<input type="password">
```

#### `radio`

A radio button allows a single value to be selected out of multiple choices with the same `name` value.
```html
<input type="radio" name="example"> Option 1
<input type="radio" name="example"> Option 2
```

#### `checkbox`

A checkbox allows a value to be selected or deselected. Several checkboxes may be selected; give related choices the same `name` when the submitted form should send multiple values for one field, or distinct names when they are independent fields.
```html
<input type="checkbox" name="example1"> Option 1
<input type="checkbox" name="example2"> Option 2
```

#### `file`

A control that lets the user select a file. The `accept` attribute is a browser hint/filter for likely file types, not validation or a security boundary; validate uploaded files on the server.
```html
<input type="file" accept=".jpg, .jpeg, .png">
```

#### `submit`

A button that submits the form.
```html
<input type="submit" value="Submit">
```

#### `reset`

A button that resets the contents of the form to default values. Not recommended as it can lead to accidental data loss.
```html
<input type="reset" value="Reset">
```

#### `button`

A push-button with no default behavior. Use JavaScript to add functionality.
```html
<input type="button" value="Click me" onclick="alert('Button clicked!')">
```

### Common Attributes

#### `placeholder`

Provides a hint to the user of what can be entered in the field.
It does not replace a visible, programmatically associated label.
```html
<input type="text" placeholder="Enter your name">
```

#### `name`

Provides the form-field name used when submitting a control. Radio buttons with the same name form a group in which one choice can be selected; checkboxes can share a name when multiple values belong to one field.
```html
<input type="radio" name="gender" value="male"> Male
<input type="radio" name="gender" value="female"> Female
```

#### `checked`

Sets a checkbox or radio button to be selected by default.
```html
<input type="checkbox" name="subscribe" checked> Subscribe to newsletter
```

#### `multiple`

Allows multiple files to be selected in a file input.
```html
<input type="file" name="files" multiple>
```

### Example Usage

#### Basic Form with Input Elements

```html
<form action="/submit" method="post">
  Name: <input type="text" name="name" placeholder="Enter your name"><br><br>
  Password: <input type="password" name="password"><br><br>
  Gender:
  <input type="radio" name="gender" value="male"> Male
  <input type="radio" name="gender" value="female" checked> Female<br><br>
  Interests:
  <input type="checkbox" name="interest" value="coding"> Coding
  <input type="checkbox" name="interest" value="music" checked> Music<br><br>
  Upload files: <input type="file" name="files" multiple><br><br>
  <input type="submit" value="Submit">
  <input type="reset" value="Reset">
</form>
```

For a usable form, associate each control with a `<label>` (using a matching `for`/`id` pair or by wrapping the control). The text placed next to a control in this compact example is not itself a programmatic label.

## The `button` Element

The `<button>` element is used to create clickable buttons.

### Common Attribute

#### `type`

Defines the behavior of the button. It can be `submit`, `reset`, or `button`.
Inside a form, a `<button>` without a `type` defaults to submit; set the intended type explicitly.

```html
<button type="submit">Submit</button>
<button type="reset">Reset</button>
<button type="button" onclick="alert('Button clicked!')">Click me</button>
```

### Example Usage

```html
<button>I'm a button</button>
<button type="submit">I'm a submit button</button>
<button type="reset">I'm a reset button</button>
```

## The `select` Element

The `<select>` element is used to create a drop-down list.

### Structure

- `<select></select>`: The entire drop-down menu.
- `<option></option>`: Each item in the drop-down menu.

### Example Usage

```html
<select name="cities">
  <option value="beijing">Beijing</option>
  <option value="guangzhou">Guangzhou</option>
  <option value="shanghai">Shanghai</option>
  <option value="shenzhen" selected>Shenzhen</option>
</select>
```

### Common Attributes

#### `name`

Identifies the drop-down menu when the form is submitted.

```html
<select name="city">
  <option value="new-york">New York</option>
  <option value="los-angeles">Los Angeles</option>
</select>
```

#### `multiple`

Allows multiple selections within the drop-down list.

```html
<select name="cities" multiple>
  <option value="beijing">Beijing</option>
  <option value="guangzhou">Guangzhou</option>
  <option value="shanghai">Shanghai</option>
  <option value="shenzhen">Shenzhen</option>
</select>
```

### Selected Attribute

Specifies the default selected item in the drop-down list.

```html
<select>
  <option value="option1">Option 1</option>
  <option value="option2" selected>Option 2</option>
  <option value="option3">Option 3</option>
</select>
```

### A Multi-line Text Input Control (`<textarea></textarea>`)

**Useful Attributes**

- `cols`: Specifies the visible width of the text area in characters.
- `rows`: Specifies the visible number of lines in the text area.

**Best Practices**

- **Resizing:**
  - By default, users can resize the text area by dragging the bottom-right corner. However, it is often best to control resizing via CSS to maintain layout consistency.
  - Example:
    ```css
    textarea {
        resize: none; /* Disables resizing */
    }
    ```

### Label Element (`<label></label>`)

**Usage**

Labels are used to bind a text description to a form element, enhancing accessibility and usability.

**Method 1: Using `for` Attribute**

- Give the form control an `id`, then set the label's `for` attribute to that exact value. The control may sit inside the label or elsewhere in the document.

The `label` element should identify the control's purpose; adjacent text alone does not create that programmatic association.

**Method 2: Wrapping the Form Element**

- Wrap both the form element and its content with a label tag.
- Omit the `for` attribute.

**Example**

```html
gender:
<input type="radio" name="gender" id="male" value="male"> <label for="male">male</label>
<label><input type="radio" name="gender" value="female"> female</label>
```
