# Math / 数学函数

**Core idea / 核心概念：** `Math` is a built-in ECMAScript object; TypeScript types it but does not provide a separate runtime math library. / `Math` 是 ECMAScript 内置对象；TypeScript 为它提供类型，但不会提供另一套运行时数学库。 See [ECMAScript numbers and dates](https://tc39.es/ecma262/2025/multipage/numbers-and-dates.html).

`Math.max()` returns the largest of the supplied numbers. With no arguments it returns `-Infinity`; `Math.min()` returns `Infinity` with no arguments.

Frequently used functions:

1. **Math.max(...values)**: Returns the largest of zero or more numbers.
2. **Math.min(...values)**: Returns the smallest of zero or more numbers.
3. **Math.round(value)**: Rounds a number to the nearest integer; a half-way tie goes toward positive infinity (for example, `Math.round(-1.5) === -1`).
4. **Math.ceil(value)**: Rounds a number upward to its nearest integer.
5. **Math.floor(value)**: Rounds a number downward to its nearest integer.
6. **Math.abs(value)**: Returns the absolute value of a number.
7. **Math.sqrt(value)**: Returns the square root of a number.
8. **Math.pow(base, exponent)**: Returns the base to the exponent power, that is, base^exponent.
9. **Math.random()**: Returns a pseudo-random number in the half-open range `[0, 1)`; it can be `0` but is less than `1`.
10. **Math.sin(value)**, **Math.cos(value)**, **Math.tan(value)**: Trigonometric functions (sin, cos, tan).
11. **Math.log(value)**: Returns the natural logarithm (base e) of a number.

These functions are part of ECMAScript and are available in JavaScript hosts such as browsers and Node.js. For example: `Math.max(1, 2, 3)`.
