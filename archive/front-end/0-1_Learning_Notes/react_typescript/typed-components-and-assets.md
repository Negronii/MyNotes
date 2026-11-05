# How do you type React components and imported assets? / 如何为 React 组件和导入资源添加类型？

TypeScript checks declared component props and module shapes during type checking, but a type declaration does not validate runtime data. This archived reference retains the course setup, component props, CSS-module declaration, and asset examples. / TypeScript 在类型检查时校验组件 props 和模块形状，但类型声明不会验证运行时数据。本归档参考保留课程配置、组件 props、CSS Module 声明和资源示例。

## TypeScript Configuration / TypeScript配置

`noImplicitAny` controls whether TypeScript reports values that would otherwise receive an inferred `any`; it does not prohibit explicit `any`. Setting it to `true`, as below, catches missing annotations. See the TypeScript [`noImplicitAny` option](https://www.typescriptlang.org/tsconfig/#noImplicitAny).

```json
{
  "compilerOptions": {
    "noImplicitAny": true
  }
}
```

Prefer a specific type or `unknown` over `any`; narrow `unknown` before using its value.

## Creating a Component in TypeScript / 使用TypeScript定义组件

Here's an example of a React component written in TypeScript:

```tsx
import React from "react";

interface RobotProps {
  id: number;
  name: string;
  email: string;
}

const Robot: React.FC<RobotProps> = ({ id, name, email }) => {
  return (
    <li>
      <img alt="robot" src={`https://robohash.org/${id}`} />
      <h2>{name}</h2>
      <p>{email}</p>
    </li>
  );
};

export default Robot;
```

### Key Points:

- `React.FC` is a component type that checks the declared props. With current React type definitions, it does not add a `children` prop implicitly; declare children explicitly when part of the component API ([React types](https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/react/index.d.ts)).
- Defining the props type (e.g., `RobotProps`) lets TypeScript check component calls.

## Using the Component in App.tsx

Here's how to use the `Robot` component in your main `App` component:

```tsx
import React from "react";
import robots from "./mockData/robots.json";
import Robot from "./components/Robot";

export default function App() {
  return (
    <ul>
      {robots.map((r) => (
        <Robot key={r.id} id={r.id} email={r.email} name={r.name} />
      ))}
    </ul>
  );
}
```

### Key Points:

- Use the `.map()` function to render a list of components.
- Always provide a `key` prop when rendering lists in React to ensure efficient updates.

## CSS in TypeScript / TypeScript中的CSS

When using CSS modules with TypeScript, follow this approach:

1. **File Naming Convention:**

   Name your CSS files as `<component>.module.css`, ensuring that styles are scoped to the component.

2. **Importing CSS Modules:**

   Instead of importing CSS directly, import it as a module to avoid global style conflicts:

   ```tsx
   import styles from "./<component>.module.css";
   ```

3. **Declaring CSS Modules for TypeScript:**

   Create a file called `custom.d.ts` to declare CSS modules for TypeScript:

   ```tsx
   declare module "*.module.css" {
     const styles: { [className: string]: string };
     export default styles;
   }
   ```

4. **Using CSS Modules:**

   Apply CSS classes in JSX as follows:

   ```tsx
   <div className={styles.app}>
   ```

   For class names with hyphens, use:

   ```tsx
   <div className={styles['app-style']}>
   ```

## Project Structure and Media Import

### Recommended Project Structure:

- **assets/**: Directory for media files.
  - **images/**: Directory for images.
  - **fonts/**: Directory for fonts.
  - **icons/**: Directory for icons.

### Importing Media:

#### Importing Images:

To import an image:

```tsx
import logo from "./assets/images/logo.svg";
```

React does not load image files. Whether an image import works depends on the bundler and its TypeScript declarations; public assets can instead be referenced by URL.

#### Importing Fonts:

1. **Add Font Files:**

   Place the font file in the `assets/fonts` directory.

2. **Declare Fonts in CSS:**

   Add the font in your global `index.css` or any global stylesheet:

   ```css
   @font-face {
     font-family: "Slidefu";
     src: local("Slidefu"), url("./assets/fonts/Slidefu-Regular-2.ttf") format("truetype");
   }
   ```

3. **Use Fonts in Components:**

   Apply the font in your component-specific CSS file:

   ```css
   h1 {
     font-family: "Slidefu";
     font-size: 72px;
   }
   ```

**Sources checked 2026-10-15:** [TypeScript `noImplicitAny`](https://www.typescriptlang.org/tsconfig/#noImplicitAny), [React type definitions](https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/react/index.d.ts), [TypeScript type erasure](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types).
