# How can a frontend architecture divide presentation and behavior? / 前端架构怎样划分呈现与行为的职责？

Start by deciding who owns data, interaction, and the view. Components give the UI explicit inputs and outputs, and unidirectional data flow helps trace causes of state changes. Micro-frontends add a deployment and ownership boundary when teams need independent releases. / 先确定数据、交互和视图由谁负责。组件为界面定义明确的输入和输出，单向数据流有助于追溯状态变化的原因。团队需要独立发布时，微前端还会引入部署与所有权边界。

## What are common frontend architecture patterns?

These are common design shapes, not a required architecture. Choose based on product boundaries, change frequency, and team ownership.

### Component-based architecture

A UI can be composed from reusable components with explicit inputs and outputs. State and side effects may live in a component, a hook, or a separate service depending on its lifecycle and reuse needs; they are not inherently owned by every component.

### Unidirectional data flow

In the classic Flux model, actions pass through a dispatcher to stores, which notify views. Other state libraries use different contracts. The useful goal is to make state changes and their causes traceable; the particular library does not guarantee that by itself.

See [Advanced React](../../frontend/frameworks/advanced-react.md) for React-specific state and component patterns.

### Micro-frontends

Micro-frontends divide a frontend into parts that can have separate ownership or release paths. Integration can use build-time composition, runtime module loading, iframes, or web components, each with different isolation and deployment properties.

Reach for this when independent teams or release schedules are a concrete requirement and the organization can support the shared navigation, styling, accessibility, observability, and runtime boundaries. For a smaller application, a modular single frontend usually has less coordination and deployment overhead.

**See also:** [Design Patterns in Practice](./design-patterns-in-practice.md) for reusable patterns that can support these principles.

[Back to the main question / 返回主问题](software-design-principles.md).
