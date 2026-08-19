# Provider Notes

Provider behavior changes. Last reviewed: 2026-08-05. Re-check official documentation before relying on model-specific limits, prices, caching behavior, or syntax.

## Portable guidance

The following principles are broadly portable but still require task-specific evaluation:

- state the observable outcome and hard boundaries clearly;
- keep context relevant and remove repetition;
- use precise tool names and schemas;
- validate arguments and authorization at runtime;
- test positive, negative, edge, and recovery cases;
- measure outcomes before token or latency optimizations.

## OpenAI

Official references:

- Prompt/model guidance: https://developers.openai.com/api/docs/guides/latest-model
- GPT-5.6 prompt guidance: https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6
- Skill construction: https://developers.openai.com/plugins/build/skills
- Tool planning: https://developers.openai.com/plugins/plan/tools

Current guidance favors lean prompts, explicit autonomy boundaries, representative evaluations, and concise tool descriptions. Do not copy numerical improvements or model behavior into durable prompts without preserving the evaluated model, workload, and date.

## Anthropic

Official references:

- Skill authoring: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Claude Fable 5 prompting: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- Current prompting practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Tool engineering: https://www.anthropic.com/engineering/writing-tools-for-agents
- Agent evaluations: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

Current guidance emphasizes concise skills, progressive disclosure, task-appropriate freedom, high-signal tool results, and evaluation-driven iteration. Fable 5's improved instruction following often lets one brief instruction replace enumerated behaviors, while readability still matters more than raw brevity. Anthropic also recommends re-testing scaffolding created for older models because excessive prescription or inherited verification rules can waste work or degrade results.

## Z.AI GLM

Official references:

- GLM-4.5: https://docs.z.ai/guides/llm/glm-4.5
- GLM-4.7: https://docs.z.ai/guides/llm/glm-4.7
- Open-source inference and tool-call settings: https://github.com/zai-org/GLM-4.5

GLM model lines contain different sizes and reasoning modes. Current GLM-4.5 and GLM-4.7 documentation describes native tool use, structured output, and thinking controls, so do not assume every GLM needs a hand-written step-by-step plan. Benchmark lean and scaffolded profiles on the exact checkpoint and serving template. For agentic work, verify the documented tool-call parser, chat template, and reasoning-retention settings before changing prompt prose.

## DeepSeek

Official references:

- Reasoning model API: https://api-docs.deepseek.com/guides/reasoning_model
- DeepSeek-R1 model card and usage recommendations: https://github.com/deepseek-ai/DeepSeek-R1

Do not use “DeepSeek” as shorthand for a weak non-reasoning model. DeepSeek-R1 is a reasoning family with model-specific usage guidance; its published recommendations include putting instructions in the user prompt rather than adding a system prompt and using repeated trials for evaluation. Treat those directions as model-version-specific, not portable prompt law.

## Google Gemini

Official references:

- Prompt strategies: https://ai.google.dev/gemini-api/docs/prompting-strategies
- Function calling: https://ai.google.dev/gemini-api/docs/function-calling

Current guidance emphasizes direct structure, consistent delimiters, strong typing, bounded retry behavior, and evaluation of example count and active tool selection.

## MCP

Official references:

- Current specification: https://modelcontextprotocol.io/specification/latest
- Tool schema and annotations: https://modelcontextprotocol.io/specification/2025-11-25/schema

Treat `readOnlyHint`, `destructiveHint`, `idempotentHint`, and `openWorldHint` as descriptive hints. Keep hard guarantees in trusted runtime controls.

## Research cautions

- Instruction decomposition and sequential itemization improved results across several older GPT-2/GPT-3 sizes in Mishra et al.: https://aclanthology.org/2022.findings-acl.50/
- Few-shot gains are not monotonic with model size; one controlled task found added examples disproportionately benefited larger models: https://arxiv.org/abs/2212.01907
- Complex instruction compliance varies by constraint type, count, and position, so use decomposed graders rather than a single subjective score: https://aclanthology.org/2024.findings-acl.772/

These studies support testing decomposition and examples; they do not justify a universal “smaller model means longer prompt” rule.
