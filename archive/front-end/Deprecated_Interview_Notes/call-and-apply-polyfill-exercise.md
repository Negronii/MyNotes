# How can call and apply be implemented with bounded receiver support? / 如何在受限接收者范围内实现 call 与 apply？

call and apply invoke immediately with an explicit receiver; call accepts separate arguments, while apply accepts an array-like list. This teaching implementation temporarily installs the function on an extensible ordinary object/function receiver and removes it in finally; it does not emulate built-in receiver conversion or exotic-object behavior. / call 和 apply 都会使用显式接收者立即调用函数；call 接受分开的参数，apply 接受类数组参数列表。此教学实现将函数临时放到可扩展的普通对象或函数接收者上，并通过 finally 清理；它不模拟内置方法的接收者转换或异质对象行为。

~~~javascript
Function.prototype.myCall = function(context, ...args) {
  if (context === null || (typeof context !== 'object' && typeof context !== 'function')) {
    throw new TypeError('This exercise requires an object receiver');
  }
  const key = Symbol('temporary call');
  Object.defineProperty(context, key, { value: this, configurable: true });
  try {
    return context[key](...args);
  } finally {
    delete context[key];
  }
};

Function.prototype.myApply = function(context, args) {
  const list = args == null ? [] : Array.prototype.slice.call(args);
  return this.myCall(context, ...list);
};

const receiver = { base: 10 };
function sum(a, b) { return this.base + a + b; }
sum.myCall(receiver, 1, 2); // 13
(function() { return arguments.length; }).myApply(receiver, []); // 0
~~~

The finally block removes the temporary key even if the called function throws. This does not cover primitive receivers, non-extensible or exotic objects, native function metadata, or every Proxy interaction. Prefer built-ins in production. / 即使被调用函数抛错，finally 也会删除临时属性。该实现不覆盖原始值接收者、不可扩展或异质对象、原生函数元数据或所有 Proxy 交互；生产代码应使用内置方法。

For the standard call-form model and bind behavior, see [Objects, Functions, and Prototypes](../../../frontend/javascript/objects-functions-and-prototypes.md).
