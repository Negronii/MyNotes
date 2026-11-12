# 怎样建模页面文档、编辑会话和发布快照？

回到前端架构篇的合成页面编辑器起点：资产 42 的页面当前是 revision (修订) 12，访客也从修订 12 的初始快照读取页面。文档里有标题 `heading-1` 和报名按钮 `button-1`。本篇继续用 `section-1` 根节点容纳它们，专门展示父子关系；其他编辑行为沿用同一组稳定 ID (标识符)。编辑者修改标题、重排组件、撤销、保存草稿，并发布审核后的版本。要避免选择或拖动时误写页面，也要让访客明确看到哪个已校验的修订。

三个生命周期分别是：可保存的页面文档、当前编辑会话里的临时状态、从某个文档修订及固定渲染依赖派生的公开快照。

## 文档树和编辑会话记录不同事实

文档保存页面事实：稳定节点 ID (标识符)、组件类型、属性、子节点和顶层顺序。会话保存当前选择、面板和拖动中的候选位置。代码用 `section-1` 作根节点，标题和按钮是它的两个孩子；根 ID 与子节点 ID 分开存放，所以重排兄弟节点只改 `section-1.children`，不必把节点对象从 ID 表里挪来挪去。

~~~javascript
const documentState = {
  schemaVersion: 1,
  revision: 12,
  rootIds: ['section-1'],
  nodes: {
    'section-1': {
      id: 'section-1', type: 'section',
      props: { label: '首页内容' }, children: ['heading-1', 'button-1'],
    },
    'heading-1': {
      id: 'heading-1', type: 'heading',
      props: { text: '首页', level: 1 }, children: [],
      style: { position: 'absolute', top: 100, left: 200 },
    },
    'button-1': {
      id: 'button-1', type: 'button',
      props: {
        label: '报名',
        action: { kind: 'navigate', pageId: 'form' },
      },
      children: [],
    },
  },
};

const editorSession = {
  selectedId: null,
  openPanel: 'inspector',
  dragPreview: null,
};
~~~

`rootIds` 表示顶层节点及其顺序；`nodes` 按 ID 索引，便于通过 `heading-1` 定位并局部更新。已提交树采用森林规则：根 ID 不重复，根节点不能同时是孩子；每条父子边只出现一次，每个非根节点只有一个父节点；所有节点能从某个根到达，且没有环。只检查 ID 唯一、引用存在和无环还不够：两个父节点可能同时引用同一个孩子，文档也可能留下无法从根到达的孤儿节点。若产品允许未挂入树中的新节点草稿，可暂存在会话里，提交前才要求完整树满足这些约束；本例没有实现新建节点流程。

较小编辑器也可用嵌套树，避免过早规范化，但仍要保持单父与根归属规则。示例不把光标或 `selectedId` 存进页面：切换选择不推进文档修订、不进入撤销历史，也不影响发布输出。这里选择把 `style` 类布局属性放进文档，因为产品要保存布局；若某种样式只服务于拖动中的临时预览，就应跟 `dragPreview` 一起留在会话。可保存和临时状态的边界取决于产品语义，而不是字段名。

## 稳定身份与命令使修改可追踪

数组下标会因插入和排序改变，不适合作为长期节点身份。稳定 ID 让检查器、历史记录和协作消息指向同一个节点。**command (命令)** 把用户意图表达成可验证操作，例如更新标题文本或移动一个兄弟节点；调用方不能直接修改状态所有者持有的对象。

先停在标题已经改成“欢迎”的 r13，看一次拖动还未提交时的状态。图中“标题”和“按钮”分别是 `heading-1` 与 `button-1`，两者始终属于 `section-1`。

~~~mermaid
flowchart TD
    Doc["文档 r13<br/>标题 → 按钮<br/>撤销深度 1"] -.->|读取已提交内容| View["画布临时投影<br/>按钮 → 标题"]
    Drag["会话 dragPreview<br/>候选：按钮 → 标题"] -.->|只替换本次显示顺序| View
    Drag -->|取消| Cancel["清空候选<br/>文档仍 r13<br/>撤销深度仍 1"]
    Drag -->|松手确认| Command["提交移动命令<br/>相同节点 ID<br/>moveSiblingAfter"]
    Command -->|结构校验通过| R14["文档 r14<br/>按钮 → 标题<br/>撤销深度 2<br/>清空候选"]
~~~

画布的临时投影不会写回文档。取消时清空候选，显示回到 r13 的文档顺序；确认时才由命令生成 r14。若移动命令被拒绝，文档与撤销栈都不变，候选仍留在会话里供处理。下面的表从最初 r12 继续到保存与发布，补齐每一步的状态。


| 用户动作 | 会话与画布 | 文档、历史和访客 |
|---|---|---|
| 初始页面 | `selectedId=null`、`dragPreview=null`；画布顺序为标题、按钮 | 文档 r12，`children=['heading-1','button-1']`；访客活动快照 r12 |
| 确认标题“欢迎” | 输入组件提交 `setText` | 文档到 r13，`heading-1` ID 不变；撤销历史增加一项，访客仍读 r12 |
| 选择标题 | `selectedId='heading-1'` | 文档仍 r13；撤销历史不变 |
| 拖到按钮后方，尚未松手 | `dragPreview` 保存 `section-1`、`heading-1`、`button-1` 和候选顺序；画布暂时按候选顺序预览 | 文档 children 仍是 `['heading-1','button-1']`，仍 r13；历史不变，访客仍读 r12 |
| 取消拖动 | 清空 `dragPreview`，画布回到文档顺序 | 文档 r13、历史和活动快照均不变 |
| 再拖一次并松手确认 | 用 `moveSiblingAfter('section-1','heading-1','button-1')` 提交相同 ID；成功后清空候选 | 文档到 r14，`children=['button-1','heading-1']`；历史增加一项，访客仍读 r12 |
| 撤销后重做 | 会话选择仍指向 `heading-1` | r15 恢复原顺序，r16 恢复重排；两个动作都新增修订，访客仍读 r12 |
| 保存 r16 | 保存该确切修订 | `savedDrafts` 保存 r16；活动快照仍 r12 |
| 明确请求发布 r16 | 发布服务重新校验已保存的 r16 | 通过后才原子切换活动指针 r12→r16，访客读取 r16 |
| 清空标题并提交 | 文档到 r17，活动快照仍为 r16 | 标题为空；撤销历史增加一项，已保存与已发布的 r16 不变 |
| 预览 r17 | 画布显示空标题 | 只读草稿，不改文档、历史或活动快照 |
| 保存 r17 | 保存该确切修订 | 活动快照仍 r16，访客仍读“欢迎” |
| 明确请求发布 r17 | 发布服务重新校验已保存的 r17 | 非空标题规则拒绝；活动快照和访客仍为 r16 |

下面的完整实现按顺序使用上方可见的初始输入。接受的文档命令、撤销和重做会生成新的单调修订号；选择、拖动和取消不会增加修订或修改撤销栈。

> [!example]- 完整可运行实现（需和上面的初始输入一起运行）
> 本实现使用上节可见的 `documentState` 与 `editorSession`。按页面顺序拼接两个 JavaScript 围栏运行；只复制本折叠围栏会缺少初始输入。
>
> ~~~javascript
> function clone(value) {
>   return structuredClone(value);
> }
>
> function freezeDeep(value) {
>   if (value && typeof value === 'object' && !Object.isFrozen(value)) {
>     for (const child of Object.values(value)) freezeDeep(child);
>     Object.freeze(value);
>   }
>   return value;
> }
>
> function validateDocument(document) {
>   const errors = [];
>   if (!document || typeof document !== 'object' || Array.isArray(document)) {
>     return ['document must be an object'];
>   }
>   if (document.schemaVersion !== 1) errors.push('unsupported schemaVersion');
>   if (!Number.isSafeInteger(document.revision) || document.revision < 0) {
>     errors.push('revision must be a non-negative safe integer');
>   }
>   if (!Array.isArray(document.rootIds)) errors.push('rootIds must be an array');
>   if (!document.nodes || typeof document.nodes !== 'object' || Array.isArray(document.nodes)) {
>     errors.push('nodes must be an ID map');
>   }
>   if (errors.length) return errors;
>
>   const ids = Object.keys(document.nodes);
>   const roots = document.rootIds;
>   const rootSet = new Set();
>   for (const id of roots) {
>     if (typeof id !== 'string') {
>       errors.push('rootIds must contain only string IDs');
>       continue;
>     }
>     if (rootSet.has(id)) errors.push('rootIds contains duplicates');
>     rootSet.add(id);
>     if (!Object.hasOwn(document.nodes, id)) {
>       errors.push('rootIds contains an unknown node');
>     }
>   }
>
>   const parents = new Map(ids.map(id => [id, 0]));
>   for (const [key, node] of Object.entries(document.nodes)) {
>     if (!node || typeof node !== 'object') {
>       errors.push(`node ${key} must be an object`);
>       continue;
>     }
>     if (node.id !== key) errors.push(`node key and id differ for ${key}`);
>     if (!Array.isArray(node.children)) {
>       errors.push(`children of ${key} must be an array`);
>       continue;
>     }
>     if (node.style !== undefined) {
>       if (!node.style || typeof node.style !== 'object' || Array.isArray(node.style)) {
>         errors.push(`style of ${key} must be an object`);
>       } else {
>         const allowedStyleKeys = new Set(['position', 'top', 'left']);
>         if (Object.keys(node.style).some(styleKey => !allowedStyleKeys.has(styleKey))) {
>           errors.push(`style of ${key} has an unknown property`);
>         }
>         if (!['absolute', 'relative'].includes(node.style.position)) {
>           errors.push(`style position of ${key} must be absolute or relative`);
>         }
>         for (const coordinate of ['top', 'left']) {
>           if (node.style[coordinate] !== undefined && !Number.isFinite(node.style[coordinate])) {
>             errors.push(`${coordinate} of ${key} must be finite`);
>           }
>         }
>       }
>     }
>     if (node.type === 'section') {
>       if (typeof node.props?.label !== 'string') errors.push(`section ${key} needs a string label`);
>     } else if (node.type === 'heading') {
>       if (typeof node.props?.text !== 'string') errors.push(`heading ${key} needs string text`);
>       if (!Number.isInteger(node.props?.level) || node.props.level < 1 || node.props.level > 6) {
>         errors.push(`heading ${key} level must be an integer from 1 to 6`);
>       }
>       if (node.children.length) errors.push(`heading ${key} cannot have children`);
>     } else if (node.type === 'button') {
>       if (typeof node.props?.label !== 'string') errors.push(`button ${key} needs a string label`);
>       if (node.props?.action?.kind !== 'navigate' || typeof node.props?.action?.pageId !== 'string') {
>         errors.push(`button ${key} needs a navigate action with pageId`);
>       }
>       if (node.children.length) errors.push(`button ${key} cannot have children`);
>     } else {
>       errors.push(`unknown component type for ${key}`);
>     }
>
>     const childSet = new Set();
>     for (const childId of node.children) {
>       if (typeof childId !== 'string') {
>         errors.push(`children of ${key} must contain only string IDs`);
>         continue;
>       }
>       if (childSet.has(childId)) errors.push(`${key} lists child ${childId} more than once`);
>       childSet.add(childId);
>       if (!parents.has(childId)) {
>         errors.push(`${key} refers to unknown child ${childId}`);
>       } else {
>         parents.set(childId, parents.get(childId) + 1);
>       }
>     }
>   }
>
>   for (const id of ids) {
>     const count = parents.get(id);
>     if (count > 1) errors.push(`node ${id} has more than one parent`);
>     if (rootSet.has(id) && count !== 0) errors.push(`root ${id} is also a child`);
>     if (!rootSet.has(id) && count === 0) errors.push(`node ${id} is neither root nor child`);
>   }
>
>   const colors = new Map();
>   function visitForCycle(id) {
>     if (!Object.hasOwn(document.nodes, id)) return;
>     const node = document.nodes[id];
>     if (!node || typeof node !== 'object') return;
>     if (colors.get(id) === 'gray') {
>       errors.push(`cycle reaches node ${id}`);
>       return;
>     }
>     if (colors.get(id) === 'black') return;
>     colors.set(id, 'gray');
>     const children = node.children;
>     if (Array.isArray(children)) {
>       for (const child of children) {
>         if (typeof child === 'string') visitForCycle(child);
>       }
>     }
>     colors.set(id, 'black');
>   }
>   for (const id of ids) visitForCycle(id);
>
>   const reachable = new Set();
>   function visitFromRoot(id) {
>     if (reachable.has(id) || !Object.hasOwn(document.nodes, id)) return;
>     const node = document.nodes[id];
>     if (!node || typeof node !== 'object') return;
>     reachable.add(id);
>     const children = node.children;
>     if (Array.isArray(children)) {
>       for (const child of children) {
>         if (typeof child === 'string') visitFromRoot(child);
>       }
>     }
>   }
>   for (const id of roots) {
>     if (typeof id === 'string') visitFromRoot(id);
>   }
>   for (const id of ids) {
>     if (!reachable.has(id)) errors.push(`node ${id} is unreachable from rootIds`);
>   }
>   return [...new Set(errors)];
> }
>
> let current = freezeDeep(clone(documentState));
> if (validateDocument(current).length) throw new TypeError('invalid initial document');
> const initialPublished = freezeDeep({
>   documentId: 'asset-42',
>   revision: current.revision,
>   schemaVersion: current.schemaVersion,
>   componentRegistryVersion: 'components-v1',
>   rendererVersion: 'renderer-v1',
>   document: clone(current),
> });
> let activeSnapshot = initialPublished;
> const revisions = new Map([[current.revision, current]]);
> const savedDrafts = new Map([[current.revision, current]]);
> const past = [];
> const future = [];
>
> function commit(candidate, label, historyMode = 'command') {
>   const next = clone(candidate);
>   next.revision = current.revision + 1;
>   const errors = validateDocument(next);
>   if (errors.length) return { ok: false, label, errors, revision: current.revision };
>
>   if (historyMode === 'command') {
>     past.push(clone(current));
>     future.length = 0;
>   }
>   current = freezeDeep(next);
>   revisions.set(current.revision, current);
>   return { ok: true, label, revision: current.revision };
> }
>
> function updateHeadingText(id, text) {
>   if (typeof id !== 'string') {
>     return { ok: false, errors: ['node ID must be a string'], revision: current.revision };
>   }
>   if (typeof text !== 'string') return { ok: false, errors: ['text must be a string'], revision: current.revision };
>   const node = current.nodes[id];
>   if (!node || node.type !== 'heading') {
>     return { ok: false, errors: ['heading does not exist'], revision: current.revision };
>   }
>   const next = clone(current);
>   next.nodes[id].props.text = text;
>   return commit(next, `setText(${id})`);
> }
>
> function selectNode(id) {
>   if (typeof id !== 'string' || !Object.hasOwn(current.nodes, id)) {
>     return { ok: false, errors: ['selected node ID must name an existing node'], revision: current.revision };
>   }
>   editorSession.selectedId = id;
>   return { ok: true, selectedId: id, revision: current.revision };
> }
>
> function reorderedSiblingIds(parentId, movingId, afterId) {
>   if (![parentId, movingId, afterId].every(id => typeof id === 'string')) {
>     return { ok: false, errors: ['move IDs must be strings'] };
>   }
>   const parent = current.nodes[parentId];
>   if (!parent || parent.type !== 'section') {
>     return { ok: false, errors: ['section does not exist'] };
>   }
>   const siblings = [...parent.children];
>   if (movingId === afterId || !siblings.includes(movingId) || !siblings.includes(afterId)) {
>     return { ok: false, errors: ['move requires two distinct current siblings'] };
>   }
>   const remaining = siblings.filter(id => id !== movingId);
>   const afterIndex = remaining.indexOf(afterId);
>   remaining.splice(afterIndex + 1, 0, movingId);
>   return { ok: true, children: remaining };
> }
>
> function startDrag(parentId, movingId, afterId) {
>   if (typeof movingId !== 'string' || editorSession.selectedId !== movingId) {
>     return { ok: false, errors: ['select the node before dragging it'], revision: current.revision };
>   }
>   const plan = reorderedSiblingIds(parentId, movingId, afterId);
>   if (!plan.ok) return { ...plan, revision: current.revision };
>   editorSession.dragPreview = { parentId, movingId, afterId, children: plan.children };
>   return { ok: true, dragPreview: clone(editorSession.dragPreview), revision: current.revision };
> }
>
> function cancelDrag() {
>   if (!editorSession.dragPreview) {
>     return { ok: false, errors: ['there is no drag preview to cancel'], revision: current.revision };
>   }
>   editorSession.dragPreview = null;
>   return { ok: true, cancelled: true, revision: current.revision };
> }
>
> function moveSiblingAfter(parentId, movingId, afterId) {
>   const plan = reorderedSiblingIds(parentId, movingId, afterId);
>   if (!plan.ok) return { ...plan, revision: current.revision };
>   const next = clone(current);
>   next.nodes[parentId].children = plan.children;
>   const result = commit(next, `move(${movingId}, after ${afterId})`);
>   if (result.ok) editorSession.dragPreview = null;
>   return result;
> }
>
> function dropDragPreview() {
>   const candidate = editorSession.dragPreview;
>   if (!candidate) {
>     return { ok: false, errors: ['there is no drag preview to commit'], revision: current.revision };
>   }
>   return moveSiblingAfter(candidate.parentId, candidate.movingId, candidate.afterId);
> }
>
> function undo() {
>   if (!past.length) return { ok: false, errors: ['nothing to undo'], revision: current.revision };
>   const target = past.pop();
>   future.push(clone(current));
>   return commit(target, 'undo', 'history');
> }
>
> function redo() {
>   if (!future.length) return { ok: false, errors: ['nothing to redo'], revision: current.revision };
>   const target = future.pop();
>   past.push(clone(current));
>   return commit(target, 'redo', 'history');
> }
>
> function preview(document, session = {}) {
>   const visible = [];
>   function visit(id) {
>     const node = document.nodes[id];
>     if (node.type === 'section') {
>       const order = session.dragPreview?.parentId === id
>         ? session.dragPreview.children
>         : node.children;
>       for (const childId of order) visit(childId);
>     } else if (node.type === 'heading') {
>       visible.push(`heading:${node.props.text}`);
>     } else if (node.type === 'button') {
>       visible.push(`button:${node.props.label}`);
>     }
>   }
>   for (const rootId of document.rootIds) visit(rootId);
>   return visible;
> }
>
> function saveDraft(revision) {
>   const document = revisions.get(revision);
>   if (!document) return { ok: false, error: 'revision not found' };
>   const errors = validateDocument(document);
>   if (errors.length) return { ok: false, errors };
>   savedDrafts.set(revision, freezeDeep(clone(document)));
>   return { ok: true, savedRevision: revision };
> }
>
> function publishRevision(revision) {
>   const document = savedDrafts.get(revision);
>   if (!document) return { ok: false, error: 'publish requires a saved revision', activeRevision: activeSnapshot.revision };
>   const errors = validateDocument(document);
>   if (errors.length) return { ok: false, errors, activeRevision: activeSnapshot.revision };
>   const emptyHeading = Object.values(document.nodes).find(
>     node => node.type === 'heading' && node.props.text.trim().length === 0,
>   );
>   if (emptyHeading) {
>     return { ok: false, error: `heading ${emptyHeading.id} must not be empty at publish`, activeRevision: activeSnapshot.revision };
>   }
>
>   const nextSnapshot = freezeDeep({
>     documentId: 'asset-42',
>     revision,
>     schemaVersion: document.schemaVersion,
>     componentRegistryVersion: 'components-v1',
>     rendererVersion: 'renderer-v1',
>     document: clone(document),
>   });
>   activeSnapshot = nextSnapshot;
>   return { ok: true, publishedRevision: activeSnapshot.revision };
> }
>
> function makeInvalidSharedChildExample() {
>   const invalid = clone(current);
>   invalid.nodes['section-2'] = {
>     id: 'section-2', type: 'section', props: { label: '重复引用' }, children: ['heading-1'],
>   };
>   invalid.rootIds.push('section-2');
>   return validateDocument(invalid);
> }
>
> function makeInvalidCycleExample() {
>   const invalid = clone(current);
>   invalid.nodes['heading-1'].children = ['section-1'];
>   return validateDocument(invalid);
> }
>
> function makeMalformedIdExamples() {
>   const badRoot = clone(documentState);
>   badRoot.rootIds = [{ toString: 0 }];
>   const badChild = clone(documentState);
>   badChild.nodes['section-1'].children = [{ toString: 0 }];
>   return {
>     rootErrors: validateDocument(badRoot),
>     childErrors: validateDocument(badChild),
>   };
> }
>
> function probeTree(mutator) {
>   const candidate = clone(documentState);
>   mutator(candidate);
>   return validateDocument(candidate);
> }
>
> function editorState() {
>   return {
>     selectedId: editorSession.selectedId,
>     dragPreview: clone(editorSession.dragPreview),
>     revision: current.revision,
>     children: [...current.nodes['section-1'].children],
>     undoDepth: past.length,
>     redoDepth: future.length,
>     activeRevision: activeSnapshot.revision,
>   };
> }
>
> console.log(JSON.stringify({
>   initialTreeErrors: validateDocument(current),
>   sharedChildErrors: makeInvalidSharedChildExample(),
>   cycleErrors: makeInvalidCycleExample(),
>   malformedIdErrors: makeMalformedIdExamples(),
> }));
> console.log(JSON.stringify(updateHeadingText('heading-1', '欢迎'))); // revision 13
> console.log(JSON.stringify({ selection: selectNode('heading-1'), state: editorState() }));
> console.log(JSON.stringify({
>   drag: startDrag('section-1', 'heading-1', 'button-1'),
>   canvas: preview(current, editorSession),
>   state: editorState(),
> }));
> console.log(JSON.stringify({
>   cancel: cancelDrag(),
>   canvas: preview(current, editorSession),
>   state: editorState(),
> }));
> console.log(JSON.stringify(startDrag('section-1', 'heading-1', 'button-1')));
> console.log(JSON.stringify({ drop: dropDragPreview(), canvas: preview(current, editorSession), state: editorState() })); // revision 14
> console.log(JSON.stringify(undo())); // revision 15, original order
> console.log(JSON.stringify(redo())); // revision 16, moved order restored
> console.log(JSON.stringify({ state: editorState(), canvas: preview(current, editorSession) }));
> console.log(JSON.stringify({ save: saveDraft(16), activeRevisionAfterSave: activeSnapshot.revision }));
> console.log(JSON.stringify({
>   publishRequest: 16,
>   result: publishRevision(16),
>   activeRevision: activeSnapshot.revision,
> }));
> console.log(JSON.stringify(updateHeadingText('heading-1', ''))); // revision 17
> console.log(JSON.stringify({
>   preview: preview(current),
>   save: saveDraft(17),
>   publishRequest: 17,
>   publish: publishRevision(17),
>   activeRevision: activeSnapshot.revision,
>   publicTitle: activeSnapshot.document.nodes['heading-1'].props.text,
> }));
>
> for (const [branch, mutate] of [
>   ['duplicate-root', doc => doc.rootIds.push('section-1')],
>   ['orphan-node', doc => { doc.nodes['orphan-1'] = { id: 'orphan-1', type: 'section', props: { label: '孤儿' }, children: [] }; }],
>   ['dangling-child', doc => doc.nodes['section-1'].children.push('missing-1')],
>   ['prototype-like-child', doc => doc.nodes['section-1'].children.push('constructor')],
>   ['duplicate-edge', doc => doc.nodes['section-1'].children.push('heading-1')],
>   ['invalid-child-list', doc => { doc.nodes['heading-1'].children = null; }],
>   ['invalid-heading-level', doc => { doc.nodes['heading-1'].props.level = 8; }],
> ]) {
>   console.log(JSON.stringify({ branch, errors: probeTree(mutate) }));
> }
> ~~~

完整实现还验证了多父节点、环、重复根、孤儿、悬空引用和非法字段类型。两个分组同时引用 `heading-1` 会得到多父错误；`rootIds` 或 `children` 中出现对象而非字符串 ID 时，返回结构错误列表。

本例用整份内容快照保存 `past` 与 `future`，实现直观但会随历史长度和文档大小占用更多存储。逆命令或操作日志可减少重复内容，却必须为移动、删除和之后发生的变更正确定义反向操作；协作写入还要说明操作针对哪个基线。示例中的 `style` 是明确选择持久化的布局属性；若它只记录拖动中尚未确认的位置，就应放进会话而不是文档。

在本例中，`past` 与 `future` 保存可恢复的文档内容；每次恢复仍从当前最大修订号加一，所以撤销不会改写过去已保存的修订。保存 16 把确切修订副本放入 `savedDrafts`，但不会切换活动指针；只有显式请求发布 16 且门禁通过，访客才改读 r16。之后填写空标题并提交得到 r17，不会污染已保存的 16；r17 也不能覆盖已发布的 r16。撤销历史只在当前编辑会话中，保存档案与发布快照有独立生命周期；应用重启后恢复撤销能力需要另行持久化历史或命令日志。普通编辑预览调用 `preview(document)`，始终按文档顺序遍历；画布调用 `preview(document, editorSession)`，在拖动期间临时使用 `dragPreview.children` 生成画布描述。两种调用都不改文档，也不模拟浏览器布局或截图渲染。

代码用 `structuredClone` 与深度冻结表达状态所有者不把可变内部对象直接交给视图。快照值限于 JSON 形状；实际框架可以用不可变数据结构、序列化边界或受控更新实现同样的隔离。代码只模拟单个编辑会话，不包含两个编辑器同时写入时的版本比较，因此不能用它推断并发保存已经安全。示例里 `activeSnapshot` 的一次同步赋值只标出切换边界；多进程服务需要用数据库事务或等效的原子更新来切换持久化指针。

## `schema`（结构描述）描述形状，业务规则解释含义

组件注册表可为每种类型提供配置形状、渲染器和校验器。JSON Schema 2020-12 的 `type`、`required`、数组和数值约束可表达很多 JSON 结构条件；上面的 `validateDocument` 展示了跨节点关系，例如树必须只有一个父节点、所有节点要从根可达。这类整体图约束还要由应用代码或专门扩展实现。引用目标是否存在、用户是否有权操作、发布是否允许空标题，也属于结构类型以外的产品和服务端规则。

持久化载入时先解析结构并返回能定位到节点的错误；编辑命令再检查状态变更；发布服务对选定修订重新做结构、引用、权限与资源确认。浏览器里的即时校验能更早提示，但不能替代可信边界上的校验。渲染器也不应把无效节点静默隐藏成空白页，否则读者无法区分“内容本来为空”和“数据已损坏”。本例的编辑规则允许标题文本为空字符串，发布规则另要求非空；空标题可预览和保存，但发布该修订会失败。这个非空条件只是本例产品政策，不是通用页面文档规则。

## 文档顺序不等于全部绘制顺序

`section-1.children` 的顺序可以决定组件在图层面板中的逻辑顺序，但浏览器绘制还受 Cascading Style Sheets (层叠样式表，CSS) 定位、`z-index` 和 **stacking context (层叠上下文)** 影响。本例重排两个同级子节点只改变树顺序；若某组件创建了独立层叠上下文，把它在数组里移到另一个节点后面，不保证视觉上覆盖另一个上下文中的元素。若产品提供“置顶”或“置底”，需明确它改变的是树顺序、同一层叠上下文内的绘制级别，还是另一个独立渲染模型。

## 发布绑定确切修订，避免混入未校验草稿

发布服务先选出具体保存修订，再检查结构与组件属性、引用目标、当前用户权限和需要的外部资源，全部通过后才生成公开版本。草稿修订 17 为空标题时，本例发布入口拒绝它，`activeSnapshot` 仍指向修订 16；访客不会突然看到未通过发布规则的修订。产品可以设计不同的“保存即发布”流程，但要清楚哪些校验在编辑期、保存期和发布期执行，不能让同一条规则在一个入口允许、在另一个入口意外阻断。

下图并列展开先后的两次发布请求。左列开始时活动版是 r12；左列发布完成后，再编辑和保存 r17，才开始右列。保存操作本身都不改变活动指针。

~~~mermaid
flowchart TD
    R16["第一次发布<br/>已保存 r16<br/>标题：欢迎<br/>活动版 r12"] -->|明确请求发布 r16| Check16["校验通过<br/>生成不可变快照<br/>r16"]
    Check16 --> Switch16["原子切换<br/>活动指针<br/>r12 → r16"]
    Switch16 --> Public16["访客读取 r16<br/>标题：欢迎"]
    R17["第二次发布<br/>已保存 r17<br/>标题为空<br/>活动版 r16"] -->|明确请求发布 r17| Reject17["空标题校验失败<br/>不生成新快照<br/>不切换活动指针"]
    Reject17 --> Keep16["访客仍读取 r16<br/>标题：欢迎"]
~~~

快照记录 `documentId`、`revision`、`schemaVersion`、组件注册表版本和渲染器版本。只固定文档修订不足以复现画面：组件渲染代码或引用的外部图片发生变化后，旧修订可能重新渲染出不同内容。系统可固定这些依赖版本，也可保存确切构建产物并固定其外部资源引用。只有待校验的具体修订和所有会影响输出的依赖都确定后，才生成并原子切换活动快照指针。

草稿与公开版可以并存：修订 17 正在编辑，访客仍读取已接受的修订 16。失败发布不删除草稿或改写当前页面；若要回滚，只需把活动指针重新指向一个仍可用的既有快照。撤销则作用在编辑历史里，二者解决的是不同问题。

## 协作、传输与冲突解决需要分别设计

`WebSocket` 能传输编辑事件，却不会自动决定两人同时移动 `heading-1` 时谁先提交。单写者模型可由服务端按顺序处理命令；版本条件或锁能拒绝并发写入，但会增加冲突提示或等待。**operational transformation (操作转换，OT)** 按并发操作调整彼此内容以维护规定的一致性；**conflict-free replicated data type (无冲突复制数据类型，CRDT)** 只有在满足其数据类型的收敛条件后，才能让副本合并并最终收敛。两者仍需定义操作格式、删除与移动语义、版本兼容和树约束。

按离线需求、实时合并要求、服务端排序能力和审计要求选机制。即便采用 OT 或 CRDT，节点类型校验、树的父子约束和发布规则仍然需要执行。具体文档状态由谁持有见[前端架构怎样划分呈现、交互和数据所有权？](frontend-architecture-boundaries.md)；创建、局部校验和通知视图的实现见[页面编辑器何时需要设计模式？](design-patterns-in-practice.md)。设计模式篇的 `nodes` 数组只是聚焦对象协作的教学简化；本篇和前端架构篇展示完整 `rootIds` 与 ID 索引树。

> [!info]- 来源
> - **JSON 结构校验。** JSON Schema Draft 2020-12，Validation §6 的 `type`、`required`、数组和数值关键词；其用途包括验证 JSON 实例结构：[规范](https://json-schema.org/draft/2020-12/json-schema-validation)，2026-11-12 核对。
> - **绘制顺序。** W3C CSS 2.2，Appendix E “Elaborate description of Stacking Contexts”：[规范](https://www.w3.org/TR/CSS22/zindex.html)，2026-11-12 核对。
> - **前端共享状态。** React，“Sharing State Between Components”，共同所有者与状态上提：[原文](https://react.dev/learn/sharing-state-between-components)，2026-11-12 核对。
> - **客户端反馈与可信边界校验。** OWASP Input Validation Cheat Sheet，“Common Pitfalls · Client-only checks”建议浏览器校验用于即时反馈，服务端仍要校验输入：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html#common-pitfalls)，2026-11-12 核对。
> - **资源授权。** OWASP Authorization Cheat Sheet，“Validate the Permissions on Every Request”要求针对每个请求校验权限：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#validate-the-permissions-on-every-request)，2026-11-12 核对。
> - **副本收敛。** Shapiro 等，*Conflict-free Replicated Data Types*（2011），强最终一致性与状态/操作型 CRDT 的充分条件，§§2–3：[论文](https://perso.lip6.fr/Marc.Shapiro/papers/2011/CRDTs_SSS-2011.pdf)。
> - **并发操作转换。** Sun 等，*Achieving Convergence, Causality Preservation, and Intention Preservation in Real-Time Cooperative Editing Systems*（1998），OT 的一致性性质：[论文](https://www.cs.cityu.edu.hk/~jia/research/reduce98.pdf)。
