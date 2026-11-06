# 怎样建模页面文档、编辑会话和发布快照？

以下用一个合成的通用页面编辑器案例：编辑者正在修改 revision 12 的首页，页面含标题和报名按钮；编辑者需要改文案、拖动排序、撤销修改并发布审核后的版本。若把页面内容、当前选中项、拖动中的临时位置和公开输出塞进同一对象，简单选择也可能触发保存和历史记录，发布时也难以确定实际使用哪个版本。

先分开三个生命周期：可保存文档、只服务当前编辑器会话的状态，以及从某个文档修订派生的发布快照。

~~~mermaid
flowchart TD
    Command["编辑命令"] --> Validate["按结构与业务规则校验"]
    Validate --> Document["页面文档 revision 13"]
    Document --> History["撤销 / 重做历史"]
    Document --> Preview["编辑预览"]
    Document --> PublishCheck["发布校验"]
    PublishCheck --> Snapshot["不可变快照 revision 13"]
    Snapshot --> PublicPage["访客页面"]
    Session["编辑会话：选中 ID / 面板"] --> Canvas["画布与检查器"]
    Document --> Canvas
~~~

## 文档树和编辑会话记录不同事实

文档要保存页面事实：节点稳定身份、组件类型、属性和子节点。编辑会话记录当前选择、焦点面板、拖动候选目标等短暂 UI 状态。

~~~javascript
const documentState = {
  schemaVersion: 1,
  revision: 12,
  rootIds: ['heading-1', 'button-1'],
  nodes: {
    'heading-1': {
      id: 'heading-1',
      type: 'heading',
      props: { text: '首页', level: 1 },
      style: { position: 'absolute', top: 100, left: 200 },
      children: [],
    },
    'button-1': {
      id: 'button-1',
      type: 'button',
      props: { label: '报名', action: { kind: 'navigate', pageId: 'form' } },
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

`rootIds` 表示顶层顺序；`nodes` 按 ID 索引，便于定位和局部更新。示例采用已提交文档中的森林规则：根 ID 不重复，根节点不能同时作为子节点；每条父子边只出现一次，每个非根节点恰有一个父节点；所有节点都能从某个根到达，且不形成环。只检查 ID 唯一、引用存在和无环还不够，因为两个父节点仍可能引用同一个孩子，文档里也可能留下无法从根到达的孤儿节点。新节点在尚未挂到树上时可以先留在编辑会话的拖动草稿中，提交命令前再检查这些约束。

较小编辑器也可用嵌套树，避免过早规范化，但仍需保持相同的单父和根归属规则。示例中的 `style` 是产品选择持久化的布局配置；如果它只用于画布临时呈现，则应留在编辑会话。`selectedId` 是对节点的引用，不是节点属性；切换选择不推进文档修订、不进入撤销历史，也不影响发布内容。

## 稳定身份与命令使修改可追踪

数组下标会因插入和排序改变，不适合作为长期节点身份。稳定 ID 让检查器、历史记录与协作消息指向同一节点。**command（命令）**把用户意图表示为可检查操作，例如把 `heading-1` 的 `text` 改为“欢迎”。

下面的代码承接上节定义的完整 `documentState`，包括 `schemaVersion`、`rootIds`、标题样式和报名按钮；它只更新标题文本，不重新声明或裁剪初始文档。

~~~javascript
function updateNodeText(document, id, text) {
  const node = document.nodes[id];
  if (!node || node.type !== 'heading') {
    throw new RangeError('heading does not exist');
  }

  return {
    ...document,
    revision: document.revision + 1,
    nodes: {
      ...document.nodes,
      [id]: { ...node, props: { ...node.props, text } },
    },
  };
}

const revision13 = updateNodeText(documentState, 'heading-1', '欢迎');
// revision13 仍有 rootIds=[heading-1, button-1]，button-1 未变；只改标题并从 12 变为 13。
~~~

撤销和重做可以保存前后状态快照，也可以记录带逆操作的命令。快照简单但占更多存储；逆操作紧凑，却必须正确处理删除、移动和并发修改。输入字段可以每次击键更新，也可本地缓冲到失焦再提交；提交到文档的修改仍须经过一致验证路径。

## `schema`（结构描述）描述形状，业务规则解释含义

**component registry（组件注册表）**为每种类型提供配置形状、渲染器和可选校验器。`schema`（结构描述）可声明标题文本是字符串、按钮标签必填。JSON Schema 2020-12 可校验 JSON 结构，但应用还需检查引用页面是否存在、用户是否有权发布，或组件树是否允许特定父子关系。

未知类型、缺失 ID、非法属性和悬空引用都应在持久化或发布前给出可定位错误。客户端校验改善反馈，但授权应由可信服务端重新检查。不要让渲染阶段以空白组件静默掩盖无效文档。

## 文档顺序不等于全部绘制顺序

子节点顺序可定义图层面板中的逻辑顺序，但浏览器绘制还受定位、`z-index` 和 **stacking context（堆叠上下文）**影响。若产品提供“置顶”或“置底”，要定义它改的是节点顺序、同一堆叠上下文内的层级，还是更高层渲染模型。单独重排数组不能保证元素跨越 CSS 上下文覆盖另一个元素。

## 发布绑定确切修订，避免混入未校验草稿

发布服务应选择具体文档修订，执行结构校验、引用检查、权限检查和资源确认，再生成公开页面所需数据或制品。快照应记录 `documentId`、`revision`、`schema` 版本等来源。若构建期间只引用“当前文档”，草稿更新可能让未校验内容混入产物。仅固定文档修订还不足以重现输出：快照应同时固定组件注册表、渲染器和会影响页面的外部资源版本，或保存确切制品并封存/固定它引用的外部资源；否则重渲染或浏览仍可能读到新素材，显示效果随时间变化。

草稿修订和公开版本可并存：编辑生成 revision 14 时，访客仍看到已校验的 revision 13。发布完成后原子切换活动版本引用；回滚则重新指向已发布快照，而不是把旧内容复制进当前草稿。

## 协作、传输与冲突解决需要分别设计

`WebSocket` 能传输编辑事件，却不会自动决定两人同时移动同一节点时谁胜出。单写者模型可让服务端排序命令；锁能防并发但增加等待。operational transformation（操作转换，OT）通过转换并发操作维护规定的一致性；conflict-free replicated data type（无冲突复制数据类型，CRDT）可在满足其收敛条件时合并副本更新。两种方案都要求定义操作格式、冲突语义与版本兼容。

按离线需求、即时合并、服务端排序和审计要求选择机制。即便采用 CRDT，树结构约束、组件 schema 和发布校验仍然必要。协作是数据所有权与更新协议的一部分，不能因使用 WebSocket 就认为冲突已解决。

**相关机制：**[前端架构怎样划分状态所有权？](frontend-architecture-boundaries.md)说明谁持有文档与会话状态；[页面编辑器何时需要设计模式？](design-patterns-in-practice.md)说明创建、校验和通知的局部实现。

> [!info]- 来源
> - JSON Schema 2020-12 文档与校验规范：[JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)。
> - 堆叠上下文中的绘制顺序：[W3C CSS 2.2, Appendix E](https://www.w3.org/TR/CSS22/zindex.html)。
> - 组件共享状态的单一所有权示例：[React：Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)。
> - CRDT 的副本收敛条件：[Shapiro 等，Conflict-free Replicated Data Types（2011）](https://perso.lip6.fr/Marc.Shapiro/papers/2011/CRDTs_SSS-2011.pdf)。
> - OT 中并发操作转换与一致性属性：[Sun 等，Achieving Convergence, Causality Preservation, and Intention Preservation in Real-Time Cooperative Editing Systems（1998）](https://www.cs.cityu.edu.hk/~jia/research/reduce98.pdf)。
