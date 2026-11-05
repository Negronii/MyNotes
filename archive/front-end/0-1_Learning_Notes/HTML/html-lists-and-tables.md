# How should lists and tables represent structured HTML content? / 如何用列表和表格表示结构化 HTML 内容？

Use lists for grouped items and tables for data whose rows and columns have meaningful relationships. Table headers should identify their row or column scope so readers and assistive technology can interpret each cell. / 列表用于组合条目；表格用于行列关系有意义的数据。表头应标明对应行或列的范围，使读者和辅助技术能够理解单元格含义。

## HTML Lists and Tables

## Unordered List

An unordered list (`<ul>`) is used to create a list of items in no specific order. It is commonly used for bullet points.

**Syntax and Usage**

- **`<ul>`**: Wraps the entire unordered list.
- **`<li>`**: Represents each item within the list. It can contain any type of content, including other lists.

**Example**

```html
<ul>
  <li>Apple</li>
  <li>Banana</li>
</ul>
```

**Output**

<ul>
  <li>Apple</li>
  <li>Banana</li>
</ul>

**Best Practices**

- Use unordered lists for items that don't have a specific sequence.
- Keep the content of `<li>` items concise for readability.

## Ordered List

An ordered list (`<ol>`) is used to create a list of items in a specific order, typically numbered.

**Syntax and Usage**

- **`<ol>`**: Wraps the entire ordered list.
- **`<li>`**: Represents each item within the list.

**Example**

```html
<ol>
  <li>First item</li>
  <li>Second item</li>
</ol>
```

**Output**

<ol>
  <li>First item</li>
  <li>Second item</li>
</ol>

**Best** Practices

- Use ordered lists for steps, instructions, or any items that follow a specific order.
- Utilize the `type` attribute if a different numbering style is required (e.g., Roman numerals, letters).

## Description List

A description list (`<dl>`) is used to group terms and descriptions. It is useful for glossaries or lists of terms and definitions.

**Syntax and Usage**

- **`<dl>`**: Wraps the entire description list.
- **`<dt>`**: Represents a term or name.
- **`<dd>`**: Describes the term.

**Example**

```html
<dl>
  <dt>HTML</dt>
  <dd>HyperText Markup Language</dd>
  <dt>CSS</dt>
  <dd>Cascading Style Sheets</dd>
</dl>
```

**Output**

<dl>
  <dt>HTML</dt>
  <dd>HyperText Markup Language</dd>
  <dt>CSS</dt>
  <dd>Cascading Style Sheets</dd>
</dl>

**Best Practices**

- Use description lists for term-definition pairs to enhance readability and structure.
- Ensure terms and descriptions are clear and concise.

## Table

Tables are used to display data in a structured format with rows and columns. Modern best practices emphasize accessibility and responsiveness.

**Syntax and Usage**

```html
<table>
  <caption>Fruit List</caption>
  <thead>
    <tr>
      <th>Fruit</th>
      <th>Weight</th>
      <th>Taste</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Apple</td>
      <td>150g</td>
      <td>Good</td>
    </tr>
    <tr>
      <td>Pear</td>
      <td>100g</td>
      <td>Good</td>
    </tr>
  </tbody>
</table>
```

**Output**

<table border="1">
  <caption>Fruit List</caption>
  <thead>
    <tr>
      <th>Fruit</th>
      <th>Weight</th>
      <th>Taste</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Apple</td>
      <td>150g</td>
      <td>Good</td>
    </tr>
    <tr>
      <td>Pear</td>
      <td>100g</td>
      <td>Good</td>
    </tr>
  </tbody>
</table>

The raw Markdown-rendered table examples retain `border="1"` only to make their cells visible here. For page styling, use CSS borders rather than presentational HTML attributes.

**Best** Practices

- **Accessibility**: Use `<thead>`, `<tbody>`, and `<tfoot>` to group table sections. Provide clear and concise captions and headers.
- **Responsive Design**: On narrow screens, a wrapper with `overflow-x: auto` can keep a wide data table usable without forcing the whole page to scroll horizontally.

### Table Elements

- **`<caption>`**: Describes the table's content.
- **`<thead>`**: Groups the header content.
- **`<tbody>`**: Groups the body content.
- **`<tfoot>`**: Groups the footer content.
- **`<tr>`**: Represents a table row.
- **`<th>`**: Represents a table header cell.
- **`<td>`**: Represents a table data cell.

### Example with Merged Cells

**Syntax and Usage**

```html
<table>
  <caption>Fruit List</caption>
  <thead>
    <tr>
      <th>Fruit</th>
      <th>Weight</th>
      <th>Taste</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Apple</td>
      <td rowspan="2">150g</td>
      <td>Good</td>
    </tr>
    <tr>
      <td>Pear</td>
      <!-- The rowspan cell above occupies the Weight column in this row. -->
      <td>Good</td>
    </tr>
    <tr>
      <td>Banana</td>
      <td colspan="2">50g</td>
    </tr>
  </tbody>
</table>
```

**Output**

<table border="1">
  <caption>Fruit List</caption>
  <thead>
    <tr>
      <th>Fruit</th>
      <th>Weight</th>
      <th>Taste</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Apple</td>
      <td rowspan="2">150g</td>
      <td>Good</td>
    </tr>
    <tr>
      <td>Pear</td>
      <!-- The rowspan cell above occupies the Weight column in this row. -->
      <td>Good</td>
    </tr>
    <tr>
      <td>Banana</td>
      <td colspan="2">50g</td>
    </tr>
  </tbody>
</table>

**Best Practices for Merging Cells**

- Use the `rowspan` attribute to merge cells vertically.
- Use the `colspan` attribute to merge cells horizontally.
- A spanning cell occupies a rectangle starting at its row and column; following cells fill the remaining slots. Use CSS to control how the cell's content is visually aligned.
