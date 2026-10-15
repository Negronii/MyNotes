# Full knowledge review / 全库知识审查

This audit records accepted content only. The fixed scope contains 116 existing substantive notes—53 active and 63 archived knowledge Markdown notes—plus exactly three new Engineering Foundations notes. Nine previously reviewed bodies are protected and excluded from this phase's count. Raw source and prompt packs, scripts, and attachments are outside the prose review scope and remain unchanged. This batch does not imply that the broader review is complete.

## Accepted work / 已验收内容

Accepted notes are grouped by domain:

### AI engineering / AI 工程

- [Model Selection and Ecosystem / 模型选择与生态](../ai-engineering/foundations/model-selection-and-ecosystem.md) retains task-scoped model selection, hosted/open-weight/hybrid tradeoffs, routing, and modality constraints while removing stale catalogs and universal price or ranking rules. The note cites [OpenAI model optimization](https://developers.openai.com/api/docs/guides/model-optimization) and the changing [OpenAI models documentation](https://developers.openai.com/api/docs/models).
- [Prompt Engineering Fundamentals / 提示工程基础](../ai-engineering/prompting/prompt-engineering-fundamentals.md) explains useful prompt context and output contracts, and separates prompt guidance from application-side authorization and validation. Its examples are synthetic. The note cites [OpenAI prompt guidance](https://developers.openai.com/api/docs/guides/model-optimization#write-effective-prompts) and [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

### Frontend / 前端

- [Virtual DOM and Framework Selection / 虚拟DOM与框架选择](../frontend/frameworks/virtual-dom-and-framework-selection.md) explains reconciliation, component identity, and practical framework-selection factors without promising a universal speed advantage or framework ranking. Sources include [React Render and Commit](https://react.dev/learn/render-and-commit), [React Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state), and the [Vue rendering mechanism](https://vuejs.org/guide/extras/rendering-mechanism).
- [Advanced TypeScript / TypeScript进阶](../frontend/typescript/advanced-typescript.md) keeps utility and generic relationships, Proxy behavior, TypeScript 5 standard decorators versus legacy decorators, and exhaustive union checking. Sources include [TypeScript utility types](https://www.typescriptlang.org/docs/handbook/utility-types.html), [generics](https://www.typescriptlang.org/docs/handbook/2/generics.html), and [TypeScript 5.0 decorators](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html#decorators).

At this checkpoint, 4 of the 116 existing substantive originals in this phase are accepted. The three new foundations notes and remaining originals are not yet recorded as complete.

## Validation / 核验范围

The existing reading-document generator and `--check` passed in an isolated staged-index snapshot for each accepted batch. Scoped checks of changed prose and navigation found no missing local Markdown/HTML/image targets or broken fragments, and no committed inbound fragment to the changed headings. These checks do not establish native rendering or framework behavior; targeted Obsidian samples remain for final integration.
