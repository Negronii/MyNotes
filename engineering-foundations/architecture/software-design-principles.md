# 如何让设计原则减少真实的修改成本？

以下用一个合成的通用页面编辑器案例说明原则：用户可以添加标题和按钮、拖动节点、预览并发布页面。需求可能增加新的组件类型，也可能改变保存方式、预览表现或权限规则。设计的关键不是提前把所有细节都变成接口，而是识别哪些变化会一起发生、哪些变化应彼此独立，然后只为高频或高代价的变化建立边界。

设计原则是判断边界的工具。若一个原则无法指出当前代码中哪种改动会扩散，以及边界如何缩小扩散范围，它就还没有给出引入抽象的理由。

~~~mermaid
flowchart TD
    Change["需求变化"] --> Question["会迫使哪些模块一起改？"]
    Question --> Evidence["重复规则 / 依赖方向 / 行为契约"]
    Evidence --> Boundary["建立最小而稳定的边界"]
    Boundary --> Cost["计算新增间接层与维护成本"]
    Cost --> Decision{"减少的修改成本<br/>是否大于新增成本？"}
    Decision -->|是| Keep["保留边界"]
    Decision -->|否| Simplify["直接实现，待真实变化出现"]
~~~

## 单一职责：按共同变化原因聚合

**Single Responsibility Principle（单一职责原则，SRP）**关注模块是否有多个彼此独立的变化原因，而不是类里是否只有一个方法。页面编辑器的节点持久化规则与画布阴影样式可能由不同需求驱动，因此可以归入文档存储与呈现模块。反过来，把每个字段都拆成类，会让理解一次简单修改要跳过许多文件。

判断时列出真实的变更来源：谁提出变化、哪条规则必须同步修改、哪些调用者只关心其中一部分。只有当这些来源相对独立，且当前耦合确实让修改变贵时，再拆分职责。

## 开闭：为已知的变化点留扩展位置

**Open/Closed Principle（开闭原则，OCP）**主张让稳定部分能在预期变化点扩展，而不是每增加一种情况都改动核心。它不是“永远不修改旧代码”，也无法预先关闭所有未来变化。

若编辑器已经支持标题、按钮两种组件，并且类型校验和渲染逻辑各不相同，可以把定义按类型注册。下面的 `renderNode` 只演示类型分发；调用前由通用文档 schema 确认 `node` 和 `props` 是对象、`type` 是字符串，注册表负责识别受支持类型并校验该类型字段：

~~~javascript
const definitions = new Map([
  ['heading', {
    validate: node => typeof node.props.text === 'string',
    render: node => ({ tag: 'h2', text: node.props.text }),
  }],
  ['button', {
    validate: node => typeof node.props.label === 'string',
    render: node => ({ tag: 'button', text: node.props.label }),
  }],
]);

function renderNode(node) {
  const definition = definitions.get(node.type);
  if (!definition) throw new RangeError('unsupported component type');
  if (!definition.validate(node)) throw new TypeError('invalid node');
  return definition.render(node);
}
~~~

新类型可以通过同一契约加入，渲染入口不必增加另一条类型分支。若现在只有一种节点，普通条件判断也许更清楚。扩展点仍需维护命名、契约和注册时机。

## 里氏替换：子类型不能改变调用者依赖的行为

**Liskov Substitution Principle（里氏替换原则，LSP）**关注行为契约：调用者依赖基类或接口的保证，替代实现也应满足。若渲染器承诺每个已注册组件都能渲染，某个“只供预览”的子类型不能在普通渲染时突然抛出未支持异常；可以把预览能力单独建模为接口或可选能力。

判断替换关系时要看前置条件、后置条件和不变量，不只是方法名与类型签名。若某个子类型要求调用者先做额外检查，它可能不属于同一可替换集合。Liskov 与 Wing 对行为子类型的描述强调，这是一种语义关系。

## 接口隔离与依赖倒置：按调用者需要定义契约

**Interface Segregation Principle（接口隔离原则，ISP）**要求按客户端实际使用的能力切分契约。画布只需要“把节点渲染成视图”，发布服务需要“校验并序列化文档”；若两者都被迫依赖包含编辑、渲染、保存和发布的大接口，修改与测试都会牵动无关能力。

**Dependency Inversion Principle（依赖倒置原则，DIP）**让高层策略和底层细节通过稳定契约协作。发布流程表达“保存已校验修订”，存储适配器负责具体数据库调用。**dependency injection（依赖注入）**可以把适配器传给流程，但它只是组织依赖的一种技术，不等同于依赖倒置。

只有在替换存储、隔离测试或改变部署方式是真实需求时，这条边界才值得存在。若应用只有一个简单内存存储，数层接口可能只增加跳转。

## DRY、KISS 与 YAGNI 如何约束抽象？

DRY（Don't Repeat Yourself，不重复同一知识）针对必须保持一致的规则重复，不要求所有相似代码都合并。标题文本和按钮标签都用字符串，不表示它们需要相同业务模型；但“组件类型是否允许发布”的规则若复制在预览与发布两处，就容易不一致。

KISS（Keep It Simple，保持简单）要求方案与当前问题的复杂度相称。YAGNI（You Aren't Gonna Need It，尚未需要的能力先不实现）提醒团队别为没有证据的未来需求造扩展接口。它们不要求忽略已发生的耦合：当一次变更反复影响多处，抽象收益就有了证据。

## 用变化案例决定边界

新增图片组件时，依次问：它是否有不同配置、校验或渲染语义？规则未来是否会独立变化？所有调用者是否都需要了解图片逻辑？注册表是否真的减少改动范围？若答案支持稳定变化点，注册表可能有用；若只是固定页面的一次分支，直接写条件更好。

[前端架构怎样划分呈现、交互和数据所有权？](frontend-architecture-boundaries.md)讨论状态归属；[页面编辑器何时需要设计模式？](design-patterns-in-practice.md)展示工厂、策略和通知怎样落实边界。

> [!info]- 来源
> - 行为子类型的契约基础：[Barbara Liskov 与 Jeannette Wing, A Behavioral Notion of Subtyping](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf)。
> - OCP、SRP 等面向对象原则讨论：[Robert C. Martin, Principles and Patterns](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。
