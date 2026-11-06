# 链式接口如何先排队、再依次执行延后任务？

## 案例背景

面试题 LazyMan 要让调用者先写完一串链式命令，再按顺序打印吃饭与睡眠状态：

~~~javascript
new LazyMan("Ada").eat("fruit").sleep(10).eat("bread");
~~~

预期输出是 eat fruit、等待后输出 wake up after 10ms、最后输出 eat bread。关键是分开两个时序：同步方法先把任务加入对象自己的队列；宿主定时器稍后启动第一项；每项结束时显式推进下一项。

~~~mermaid
sequenceDiagram
  participant Caller as 同步调用者
  participant Queue as LazyMan 任务队列
  participant Timer as 宿主计时器
  Caller->>Queue: 构造并安排首轮 next
  Caller->>Queue: 加入 eat(fruit)
  Caller->>Queue: 加入 sleep(10)
  Caller->>Queue: 加入 eat(bread)
  Timer->>Queue: 首轮 next
  Queue->>Queue: 执行 eat，推进 next
  Queue->>Timer: 安排 10 ms 后继续
  Timer->>Queue: 打印醒来并推进 next
  Queue->>Queue: 执行 eat，队列结束
~~~

## 为什么构造时要延后第一项？

如果构造函数立即调用 next，方法链还没有来得及把 eat 和 sleep 放进队列。用 setTimeout 安排一个稍后的 next，让当前同步调用栈先跑完，三个方法就能先依次登记工作。延时为 0 也不是“立刻执行”：回调要等当前同步代码退出，并且实际执行时机由宿主调度。

下面的 tasks 是应用自己实现的任务队列，它保存闭包；它不是浏览器或 Node.js 的事件循环队列。

~~~javascript
class LazyMan {
  constructor(name) {
    this.name = name;
    this.tasks = [];
    setTimeout(() => this.next(), 0);
  }

  eat(food) {
    this.tasks.push(() => {
      console.log("eat " + food);
      this.next();
    });
    return this;
  }

  sleep(ms) {
    this.tasks.push(() => {
      setTimeout(() => {
        console.log("wake up after " + ms + "ms");
        this.next();
      }, ms);
    });
    return this;
  }

  next() {
    const task = this.tasks.shift();
    if (task) task();
  }
}
~~~

eat 与 sleep 都把一个函数压入 tasks，并返回 this，所以调用者还能继续链式调用。closure（闭包）在入队时记住当前的 food 或 ms。next 取出并执行队首函数；普通 eat 打印后马上调用 next，sleep 则设定计时器，在计时器回调中打印，再调用 next。

## 队列怎样推进到最终输出？

~~~javascript
new LazyMan("Ada").eat("fruit").sleep(10).eat("bread");
~~~

| 阶段 | 任务队列剩余项 | 正在执行的工作 | 下一步由谁触发 |
| --- | --- | --- | --- |
| 链式调用结束 | eat fruit、sleep 10、eat bread | 还未开始 | 构造函数安排的计时器 |
| 首轮 next | sleep 10、eat bread | eat fruit，打印后立即 next | 当前 JavaScript 调用 |
| 第二轮 next | eat bread | 安排 10 ms 定时器后返回 | 宿主定时器回调 |
| 定时器到期 | eat bread | 打印 wake up after 10ms，再 next | 当前 JavaScript 调用 |
| 最后一轮 next | 空 | eat bread，随后队列结束 | 当前 JavaScript 调用 |

输出顺序因此是：

> [!example] Ada 的三个排队命令
> 输入是 eat("fruit")、sleep(10)、eat("bread")。队列按入队顺序执行；sleep 在 10 ms 定时器回调中才调用 next，因此最后一项不会越过等待提前执行。
>
> ~~~text
> eat fruit
> wake up after 10ms
> eat bread
> ~~~

此处 next 的含义是“当前任务已完成，可以继续”，不是定时器、Promise 或浏览器内置的推进机制。若任务没有调用 next，队列就会停住；若在 sleep 期间加入任务，下一项仍等计时器完成。实际定时器可能晚于 10 ms，例子描述的是先后关系，不是精确时钟保证。

> [!info] 这段示例没有定义什么？
> 这是教学用的串行任务队列，没有规定任务抛错时如何恢复、如何取消等待中的计时器，也没有处理永不完成或重复推进。连续排入很多个同步 eat 任务会通过 next 递归推进，可能耗尽调用栈；队列已经清空后再加入任务也不会自动重新启动。生产队列要为这些状态另外定义契约，不能把本例当成已经具备这些保证。

如果任务本身要返回结果、并发组合或把失败交给调用链处理，应使用 Promise链或 async/await（异步函数和等待表达式）；见[回调、Promise 与 async 函数怎样组合异步工作？](./asynchronous-javascript.md)。本页只回答如何把链式命令转成按序推进的闭包队列。

> [!info]- 来源
> - setTimeout 的宿主调度、嵌套计时器限制及不精确时序：WHATWG HTML Living Standard（2026-11-05），[Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)。
> - “当前同步调用栈结束后回调才有机会运行”是宿主任务调度和 JavaScript run-to-completion（运行至完成）规则的应用说明；浏览器见[HTML event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)，Node 定时器见[Node.js v26.13.0 timers](https://nodejs.org/api/timers.html)。
