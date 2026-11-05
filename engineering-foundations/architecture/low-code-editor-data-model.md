# How should a low-code editor store editable structure and published output? / 低代码编辑器怎样保存可编辑结构与发布结果？

Keep an editable component tree with typed configuration and stable identity. Derive rendering and published output from that schema so editing, validation, and release can each use the representation appropriate to their lifecycle. / 维护带类型配置和稳定身份的可编辑组件树。渲染和发布结果从该结构派生，让编辑、校验和发布可以各自使用适合其生命周期的表示。

## Separate page content from the editing session / 分开页面内容与编辑会话

A page builder can model a document as a component tree, with each node carrying an ID, type, properties, style, and children. The editor can derive its canvas and side panels from that model, then serialize it for persistence.

~~~javascript
const component = {
  id: 'comp_001',
  type: 'Button',
  props: { text: 'Click me', variant: 'primary' },
  style: { position: 'absolute', top: 100, left: 200 },
  children: [],
};
~~~

Keep document order and visual stacking as explicit concepts. Child order can be one input to rendering, but CSS stacking contexts mean it is not universally equivalent to the final z-order; each stacking context is painted as a unit within its parent context ([CSS 2.2 visual formatting model](https://www.w3.org/TR/CSS22/zindex.html)).

Selection, hover, and panel state belong to the editing session. A selection change can update the inspector without editing the document, saving a draft, or adding an undo step.

~~~javascript
const editor = {
  document: { schemaVersion: 1, nodes: [component] },
  session: { selectedId: null },
};

function selectComponent(state, id) {
  return { ...state, session: { ...state.session, selectedId: id } };
}

const draftJson = JSON.stringify(selectComponent(editor, component.id).document);
~~~

- **Component registry / 组件注册表**: map a validated component type to its renderer and schema.
- **Layer order / 图层顺序**: define how siblings are ordered and translate that order into the chosen rendering model.
- **Undo and redo / 撤销与重做**: store inverse commands or immutable document snapshots; choose based on history size and operation complexity.
- **Collaboration / 协作**: a WebSocket transports updates, but does not resolve concurrent edits. A server-authoritative order, locks, operational transformation, or a CRDT may fit different conflict and offline requirements.

## Publish a validated revision / 发布已校验的修订

Validate a particular document revision against the registry and derive the public output from that revision. Keep the artifact or a versioned rendering recipe tied to its source revision so preview, release, and rollback can refer to the same content. Draft edits and session selections can then continue independently. [Design patterns and change boundaries / 设计模式与变化边界](design-patterns-in-practice.md)
