# How should I choose a frontend framework for a product? / 如何为产品选择前端框架？

**Core answer / 核心回答：** Start from the route's rendering, interaction, accessibility, and operational needs, then compare how candidate frameworks express updates and what the team can maintain. Prototype one representative feature and measure its real bottleneck; a virtual DOM label or a standalone benchmark does not predict project fit by itself. / 先从页面的渲染、交互、无障碍和运维需求出发，再比较候选框架如何表达更新以及团队能否长期维护。用一个有代表性的功能做原型，并测量真实瓶颈；虚拟 DOM 这一标签或单项基准测试本身都不能判断项目是否适合。


## How does reconciliation work, and does a Virtual DOM make an app faster? / React如何协调界面，虚拟DOM是否天然更快？

**Core answer / 核心回答：** React components describe the UI for a particular set of props and state. React compares the next element description with the previous one, then commits the necessary host changes. “Virtual DOM” is a useful shorthand for this model, not a speed guarantee: the cost depends on the component tree, update, browser work, and framework implementation. / React 组件根据当前 props 和 state 描述界面。React 将新的元素描述与之前的结果协调，再提交必要的宿主环境变更。“虚拟 DOM”是这种模型的常见简称，不代表它天然更快；实际成本取决于组件树、更新内容、浏览器工作和框架实现。

### A practical React model / React中的实用模型

1. **Render / 渲染：** React calls components to calculate the next UI description. Rendering should be pure; concurrent work may be restarted or discarded.
2. **Reconciliation / 协调：** React matches the new description to the previous tree. The exact type, position, and key rules that preserve or reset component state are explained in [React Basics / React基础](./react-basics.md); they should not be inferred from a generic “virtual DOM” slogan.
3. **Commit / 提交：** React applies the completed changes to the host tree, such as the DOM. Effects run in their documented phase; they are not part of render.

~~~jsx
{items.map(item => <ListItem key={item.id} item={item} />)}
~~~

The reconciler uses heuristics rather than a general-purpose minimum-edit tree algorithm. Treat complexity claims as implementation-specific; the useful question for framework choice is what work a representative update actually causes in the framework and browser.

### Where the model helps / 适用范围

Declarative rendering keeps UI descriptions aligned with state and lets the framework manage host updates. It can also add work for tiny isolated changes, and it does not remove browser layout, paint, or scripting costs. Use the browser and framework profilers to identify a real bottleneck before choosing a different rendering model.

React and Vue use virtual-tree reconciliation in their standard component models. Other approaches compile templates or update fine-grained dependencies. These are implementation choices, not a universal ranking.

## How do you choose a frontend framework? / 如何选择前端框架？

**Core answer / 核心回答：** Choose for the product's rendering and interaction needs, the team's ability to maintain it, required integrations, accessibility, deployment constraints, and the framework's support horizon. Evaluate a representative feature before migrating; popularity or a benchmark alone cannot predict project fit. / 根据产品的渲染与交互需求、团队维护能力、所需集成、无障碍要求、部署约束和框架支持周期来选择。迁移前先实现一个有代表性的功能；流行度或单项基准测试不足以判断项目是否适合。

| Decision factor | Questions to answer |
|---|---|
| Rendering and routing | Does the product need client-only navigation, server rendering, static output, or a mix? |
| Team and codebase | Which framework and language can the team debug, test, and upgrade? |
| Ecosystem | Are the needed router, form, data, accessibility, and build tools supported? |
| Operations | Can the chosen runtime, hosting model, and release process support it? |
| Migration cost | What working behavior, tests, and integrations would need to be replaced? |

TypeScript adds static checking and editor support, but its types are erased and do not validate runtime data. Consider the language and migration cost alongside project size and contributor turnover; there is no reliable “six-month” or “three-person” threshold.

**See also:** [React Basics / React基础](./react-basics.md) for element identity and component state; [Next.js / Next.js开发](./next-js.md) for router-specific rendering models.

**Sources checked 2026-10-15:** [React Reconciliation](https://legacy.reactjs.org/docs/reconciliation.html), [Vue Rendering Mechanism](https://vuejs.org/guide/extras/rendering-mechanism), [React: Render and Commit](https://react.dev/learn/render-and-commit), [React: Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), [TypeScript: erased structural types](https://www.typescriptlang.org/docs/handbook/typescript-for-oopers.html#erased-structural-types).
