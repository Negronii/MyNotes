# How does currying support partial application? / 柯里化如何支持部分应用？

**Core answer / 核心回答：** Currying transforms a function that accepts several arguments into a sequence of calls. Supplying fewer than the expected arguments returns another function; later calls complete the argument list. This supports partial application, but the arity rule must match the function’s contract. / 柯里化把接收多个参数的函数转换为一系列调用。参数不足时返回新函数，后续调用补齐参数，实现部分应用；但元数判断规则必须符合函数契约。

This compact implementation uses fn.length as arity and supports ordinary positional functions. Default parameters, rest parameters, placeholders, and other arity conventions need a different contract. / 这个简化实现用 fn.length 作为元数，仅支持普通位置参数函数。默认参数、剩余参数、占位符及其他元数约定需要另外定义。

~~~javascript
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) return fn.apply(this, args);
    return function (...next) {
      return curried.apply(this, [...args, ...next]);
    };
  };
}

const sum = (a, b, c) => a + b + c;
const curriedSum = curry(sum);
curriedSum(1)(2)(3); // 6
curriedSum(1, 2)(3); // 6
~~~

Currying transforms argument flow; it does not change how ordinary function this is supplied. See [Function this and Binding / 函数 this 与绑定](./this-and-function-binding.md).
