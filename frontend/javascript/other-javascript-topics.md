A grab-bag of short interview-favorite JavaScript topics. Reach for this when someone asks about strict mode, floating-point math, equality operators, or the `!!` idiom.

## What does `'use strict';` do?

Strict mode enforces stricter parsing and error handling. Activate it by adding `'use strict';` at the top of a script or function. It has different semantics from regular code, aimed at improving reliability and performance. Modern modules (ES modules and classes) run in strict mode automatically.

### Features of strict mode

1. **Mandatory variable declarations.** Assigning to an undeclared variable throws `ReferenceError`, preventing accidental global creation from typos.
2. **Disallows `with` statements.** `with` creates unpredictable scope, hurts performance, and complicates debugging.
3. **Scoped `eval()`.** Declarations inside `eval` no longer leak into the surrounding scope, making `eval` marginally safer.
4. **Secure `this` binding.** A plain function call (not as a method) has `this === undefined`, instead of `this === window`. Prevents accidental global mutation.
5. **No duplicate parameter names.** `function f(a, a) {}` throws. Eliminates a class of typos.
6. **Immutable non-writable properties.** Writing to a non-writable property throws `TypeError` instead of silently failing.
7. **Restrictions on deleting.** `delete` on non-deletable properties throws, protecting language core.
8. **No octal literals.** `010` is a syntax error. Use `0o10` for octal explicitly; use `'\u0061'` instead of `'\141'` for escape sequences.

**Reach for it when:** working in non-module scripts or legacy code where strict mode isn't implicit. In ES modules, classes, and any modern tooling, strict mode is the default.

## Why doesn't `0.1 + 0.2 === 0.3`?

**Headline:** IEEE 754 floating-point can't represent `0.1` or `0.2` exactly in binary. The tiny representation errors accumulate, so `0.1 + 0.2` lands at `0.30000000000000004`.

To compare floating-point numbers safely, check whether they're within a small tolerance:

```javascript
const tolerance = 0.0001;
const sum = 0.1 + 0.2;
const target = 0.3;

if (Math.abs(sum - target) < tolerance) {
  console.log('Equal');
} else {
  console.log('Not Equal');
}
```

For currency calculations, avoid floating-point entirely — work in integer cents (or use a decimal library).

## What's the difference between `==` and `===`?

- `==` (loose equality) performs **type coercion** before comparing. Values are converted to a common type.
- `===` (strict equality) compares **value and type** without conversion.

```javascript
5 == '5';          // true  — string '5' coerced to number
null == undefined; // true  — special rule
0 == false;        // true  — false coerced to 0
'' == false;       // true  — both coerced to 0

5 === '5';          // false
null === undefined; // false
0 === false;        // false
```

**Rule of thumb:** always use `===`, with one common exception — `value == null` is a concise way to check for both `null` and `undefined` in one expression.

**Gotcha — "`==` with `NaN`":** `NaN == anything` is always `false`, including `NaN == NaN`. Use `Number.isNaN(x)` to detect it.

## What does `!!` do?

Converts any value to its boolean equivalent. The first `!` coerces to boolean and negates; the second `!` negates back.

```javascript
!!'hello';    // true
!!0;          // false
!!null;       // false
!!undefined;  // false
!!NaN;        // false
!!'';         // false
!!{};         // true
!![];         // true
```

### Why this matters in React

React renders the literal value `0` in the DOM but ignores `false`. So short-circuiting with `&&` can leak an unwanted `0`:

```jsx
{list.length && <ItemList items={list} />}
// when list is empty: renders `0` in the DOM
```

The fix is to coerce to boolean first:

```jsx
{!!list.length && <ItemList items={list} />}
// when list is empty: renders nothing
```

**Gotcha — `!!` vs. `Boolean()`:** Functionally identical — pick whichever your team's lint rules prefer. `!!` is slightly faster in micro-benchmarks, but the difference is irrelevant in practice.
