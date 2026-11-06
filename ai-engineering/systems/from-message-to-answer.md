# How does an AI chat turn one message into a complete answer? / AI 聊天应用怎样把一条消息变成完整回答？

**Short answer / 简答：** The application assembles the input for the model. If the model requests an external action, the application checks the request, executes it when authorized, and returns the outcome for the next inference. In this example the browser displays text as it arrives and marks the answer complete on a success event for the same run. / 应用先组装模型的输入。如果模型提出外部操作请求，应用负责校验，仅在获准时执行，再把结果交给下一轮推理。在这个示例里，浏览器可以逐段展示文本，并在收到本次运行的成功终态后标记回答完成。

**Key terms / 关键术语：** inference / 推理；tool request / 工具请求；tool result / 工具结果；run ID / 运行标识；text delta / 文本增量；terminal event / 终态事件。

## Follow one message / 跟着一条消息走

假设一个聊天应用接到「为什么第 42 次构建失败了？」。聊天消息里没有构建日志，应用可以通过一个只读工具查询。下面用一次工具调用和两轮推理跟踪这条消息。

~~~mermaid
sequenceDiagram
    actor User
    participant Browser
    participant App as Chat application
    participant Model
    participant Logs as Build log store
    User->>Browser: Why did build 42 fail?
    Browser->>App: Submit message
    App->>Model: Message and available tool definitions
    Model-->>App: c1 asks to read build 42
    App->>App: Validate the call and authorize access
    App->>Logs: Read build 42
    Logs-->>App: unit-tests, exit 1
    App->>Model: Tool result for c1
    loop Answer text arrives
        Model-->>App: Answer delta using the result
        App-->>Browser: Text delta for r1
    end
    App-->>Browser: Complete r1
~~~

1. **Assemble the input / 组装本轮输入。** 应用识别当前用户，为这次运行分配 `r1`，再把问题、相关对话和允许提出请求的工具定义交给模型。`read_build_log` 的定义告诉模型可以按构建编号查询。日志正文仍在日志服务中。[每轮推理要看到哪些上下文](../context/context-engineering-principles.md)
2. **Generate a request / 生成工具请求。** 以仅解码器 Transformer 为例，分词器把输入转成词元 ID，模型从嵌入表取出向量，再用注意力混合位置之间的信息，用 FFN 变换每个位置的表示。语言模型输出层（LM head）给词表打分，解码逐步选出下一个词元。这个例子中，模型接口交给应用一个结构化工具请求 `c1`，参数为 `build_id=42`。[从词元到下一词元的张量变化](../foundations/how-llms-work.md)
3. **Check and execute / 校验并执行。** 应用检查工具名称、参数类型，以及当前用户是否能读取构建 `42`，通过后才访问日志服务。结果中的 `unit-tests` 和 `exit_code=1` 是这轮新获得的证据。授权检查放在实际读取之前，即使工具是只读的。[工具契约与应用端校验](../agents/tool-design-and-function-calling.md)
4. **Return evidence to the model / 把证据交回模型。** 应用把结果与调用标识 `c1` 关联，连同继续这轮对话所需的上下文发给模型。模型这时可以回答「第 42 次构建在 `unit-tests` 步骤以状态码 1 退出。要定位具体失败的断言，还需要更详细的日志。」如果任务需要下一次查询，应用的运行时（agent harness）可以根据新的工具请求继续这一循环。[智能体的动作与观察循环](../agents/agent-fundamentals.md#ReAct%20and%20the%20decision%20loop%20/%20ReAct%20%E4%B8%8E%E5%86%B3%E7%AD%96%E5%BE%AA%E7%8E%AF)
5. **Display and confirm / 展示并确认完成。** 应用把回答按文本增量发给浏览器。一个增量可以包含多个词元解码出的文本，浏览器可以批量更新界面。在这个示例协议里，浏览器收到 `r1` 的 `complete` 事件才把这一轮答复标记为完成。若连接先断开，已显示的文本可以保留，最终状态需要查询。[流式界面的状态与恢复](../../frontend/browser-apis/streaming-ux.md)

如果用户已经把足够的日志贴进消息，应用可以直接把这份证据放进本轮输入。如果证据散在可检索文档中，可以先从调用者有权访问的文档中选出相关段落，再让模型结合段落回答。[文档版本、检索与证据核对](../rag/rag-architecture-and-implementation.md)

这条主线采用应用执行自定义工具的方式。下文的标识、日志和事件是示例协议。两家公开 API 的文档分别描述了工具请求、应用执行和结果回传的具体格式。[OpenAI Function calling](https://developers.openai.com/api/docs/guides/function-calling#the-tool-calling-flow) · [Claude How tool use works](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works#the-agentic-loop-client-tools)

## Replay the handoffs / 复现交接过程

The two model turns are scripted. This Python example exercises tool authorization, the matched result, and the browser's completion rule offline. / 两轮模型输出用固定数据代替。运行下面的 Python 代码，可以离线观察工具授权、结果关联和界面的完成判定。

~~~python
LOGS = {42: {"step": "unit-tests", "exit_code": 1}}


def dispatch(call, readable_builds):
    call_id, name, build_id = call
    if name != "read_build_log" or type(build_id) is not int:
        return call_id, {"error": "invalid_request"}
    if build_id not in readable_builds:
        return call_id, {"error": "forbidden"}
    return call_id, LOGS.get(build_id, {"error": "not_found"})


def answer_events(readable_builds):
    call = ("c1", "read_build_log", 42)
    call_id, result = dispatch(call, readable_builds)
    assert call_id == call[0]
    if "error" in result:
        deltas = ("The build log is unavailable.",)
    else:
        deltas = (f"Build 42 stopped at {result['step']}", f" (exit {result['exit_code']}).")
    events = [("r1", "delta", text) for text in deltas]
    return [*events, ("r1", "complete", "")]


def visible(events):
    pieces = []
    for run_id, kind, value in events:
        if run_id == "r1" and kind == "delta":
            pieces.append(value)
        if run_id == "r1" and kind == "complete":
            return "".join(pieces), True
    return "".join(pieces), False


answer = "Build 42 stopped at unit-tests (exit 1)."
events = answer_events({42})
assert visible(events) == (answer, True)
assert visible(events[:-1]) == (answer, False)
assert visible(answer_events(set())) == ("The build log is unavailable.", True)
~~~

这里的 `complete` 表示这一轮答复已完整交付。明确告知无法读取日志，也可以是一条完整答复。

## Check your understanding / 闭卷自测

- **Retell / 复述。** From the message to the displayed answer, who knows the build failed at `unit-tests`, and at which step do they learn it? / 从消息发出到回答显示，哪些环节知道构建停在 `unit-tests`，它们分别在什么时候拿到这条信息？
- **Change one condition / 变式。** The user pastes the relevant log excerpt into the first message. Which handoff can disappear, and what still tells the browser that the answer is complete? / 用户在第一条消息中贴了足够的日志片段。哪些交接可以省掉？浏览器仍然凭什么判断回答已完成？
