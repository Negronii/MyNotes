# How did React 19 change function-component PropTypes? / React 19 如何改变函数组件的 PropTypes？

In React 18 and earlier, `propTypes` provided development-time prop checks for function components. React 19 silently ignores function-component `propTypes`; use TypeScript or another current type checker for component APIs. Prop checks do not validate untrusted JSON received at runtime; validate that data at the boundary. / React 18 及更早版本中，`propTypes` 可在开发时检查函数组件的 props。React 19 会静默忽略函数组件的 `propTypes`；当前组件 API 应使用 TypeScript 或其他类型检查器。组件 prop 检查不会验证运行时收到的不可信 JSON；应在数据边界校验。

## Historical React 18 example / React 18 历史示例

```jsx
import PropTypes from 'prop-types';

function Greeting({ message }) {
  return <h1>{message}</h1>;
}

Greeting.propTypes = {
  message: PropTypes.string.isRequired,
};

export default Greeting;
```

Keep this as a version-specific example when maintaining older React code. For current rendering, component identity, and state behavior, see [React Basics / React基础](../../../../frontend/frameworks/react-basics.md); for runtime JSON validation, see [How should TypeScript handle untrusted JSON? / TypeScript 应如何处理不可信 JSON？](../../../../frontend/typescript/advanced-typescript.md).

**Primary source:** [React 19 Upgrade Guide: removed `propTypes` and `defaultProps` for functions](https://react.dev/blog/2024/04/25/react-19-upgrade-guide#removed-proptypes-and-defaultprops-for-functions).
