# How can a chainable API queue delayed tasks? / 链式 API 如何排队执行延后任务？

**Core answer / 核心回答：** A chainable task API can append closures to a queue and return the same builder object. Deferring the first step allows the synchronous chain to finish building before the queue starts. Each task advances the queue only after its own work completes. / 链式任务 API 可把闭包追加到队列并返回同一 builder 对象。延后首步执行可先让同步调用链构建完成；每个任务只在自身工作结束后推进队列。

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

new LazyMan("Ada").eat("fruit").sleep(10).eat("bread");
// eat fruit → wake up after 10ms → eat bread
~~~

The time unit is milliseconds. This is a teaching example, not a production queue: it does not define failure handling, cancellation, or behavior when a task never completes. / 时间单位为毫秒。这是教学示例，不是生产队列；它没有定义错误处理、取消方式或任务永不完成时的行为。

For standard Promise composition, rejection propagation, and concurrency, see [Asynchronous JavaScript / 异步 JavaScript](./asynchronous-javascript.md). Timer callback scheduling is host behavior; see [Event Loop and Host Scheduling / 事件循环与宿主调度](../runtime/event-loop.md).
