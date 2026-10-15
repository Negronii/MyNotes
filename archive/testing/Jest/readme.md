# Jest Reference / Jest参考

This note gives compact test, lifecycle, matcher, and mock examples. Jest behavior depends on the module system and transformer; examples that use CommonJS should not be generalized to native ESM.

**Core answer / 核心回答：** Keep each test focused on observable behavior: arrange its inputs, act once, and assert the result. Mock only boundaries that the test does not intend to exercise, and restore spies so state does not leak between tests. / 每个测试聚焦于可观察行为：准备输入、执行一次操作并断言结果。只模拟测试不准备覆盖的边界，并恢复 spy，避免状态泄漏到其他测试。

## Suites and cases / 测试套件与用例

describe groups related tests; test and its alias it define a case. Use clear names that describe behavior. Starting a name with “should” is a style choice, not a Jest requirement.

~~~javascript
function add(left, right) {
  return left + right;
}

function subtract(left, right) {
  return left - right;
}

describe('calculator', () => {
  test('adds two numbers', () => {
    expect(add(2, 3)).toBe(5);
  });

  test('subtracts a larger value', () => {
    expect(subtract(5, 10)).toBe(-5);
  });
});
~~~

Arrange–Act–Assert makes setup, behavior, and verification easy to scan. A small test may not need a separate variable for every phase.

Common file names include .test.js and .spec.js; the project’s Jest configuration determines which files are collected.

## Async tests / 异步测试

Return or await the Promise so Jest waits for the assertion. For rejected Promises, use the rejects matcher.

~~~javascript
test('loads a user', async () => {
  const user = await getUser(1);
  expect(user).toHaveProperty('id', 1);
});

test('reports a failed request', async () => {
  await expect(getUser(-1)).rejects.toThrow('not found');
});
~~~

A test that starts an asynchronous operation but neither awaits it nor returns its Promise can finish before the assertion runs.

## Setup and cleanup / 准备与清理

beforeAll and afterAll run once around a test scope; beforeEach and afterEach run around each test in that scope. Use cleanup hooks for resources that tests actually open.

~~~javascript
describe('temporary resource', () => {
  let resource;

  beforeAll(async () => {
    resource = await openResource();
  });

  afterAll(async () => {
    await resource.close();
  });

  beforeEach(async () => {
    await resource.clear();
  });

  test('stores a record', async () => {
    await resource.insert({ id: 1, name: 'Ada' });
    expect(await resource.count()).toBe(1);
  });
});
~~~

## Mock functions and spies / Mock 函数与 spy

### jest.fn

jest.fn creates a mock function whose calls and results can be inspected.

~~~javascript
const callback = jest.fn();
callback('saved');

expect(callback).toHaveBeenCalledWith('saved');
expect(callback).toHaveBeenCalledTimes(1);
~~~

### jest.mock in a CommonJS/transformed setup

This example uses CommonJS require with a test configuration that transforms or otherwise supports this mocking pattern. In Babel-transformed tests, jest.mock calls are hoisted by the Jest transformer, so the mock is registered before the module is required.

~~~javascript
jest.mock('./api', () => ({
  fetchUser: jest.fn(),
}));

const api = require('./api');
const { loadUser } = require('./userService'); // userService delegates to api.fetchUser

test('uses the API boundary', async () => {
  api.fetchUser.mockResolvedValue({ id: 1, name: 'Ada' });

  await expect(loadUser(1)).resolves.toEqual({ id: 1, name: 'Ada' });
});
~~~

A module mock replaces a dependency at the module boundary. The test should still assert the behavior of the code under test rather than only reasserting the mock configuration.

### Native ESM modules

Native ESM evaluates static imports before the test body, so the CommonJS-style hoisting example does not apply. Jest's documentation provides jest.unstable_mockModule followed by dynamic import for ESM mocking. The API name is marked unstable; check the Jest version and runtime configuration.

~~~javascript
import { jest } from '@jest/globals';

jest.unstable_mockModule('./api.js', () => ({
  fetchUser: jest.fn(),
}));

const { fetchUser } = await import('./api.js');
~~~

### jest.spyOn

jest.spyOn observes an existing object method and calls the original implementation by default. Provide a mock implementation or return value when the test needs replacement behavior. Restore the spy after use.

~~~javascript
const service = {
  greet: name => 'Hello ' + name,
};

const spy = jest.spyOn(service, 'greet').mockReturnValue('Hi Bob');

expect(service.greet('Bob')).toBe('Hi Bob');
expect(spy).toHaveBeenCalledWith('Bob');

spy.mockRestore();
~~~

mockRestore restores a spy created by jest.spyOn. Use clearAllMocks, resetAllMocks, or restoreAllMocks according to whether the test needs to clear call history, reset implementations, or restore replaced properties; these operations are not interchangeable.

## Common matchers / 常见 matcher

| Matcher | Use |
|---|---|
| **toBe(value)** | Compare with Object.is semantics. |
| **toEqual(value)** | Compare nested object or array values. |
| **toMatchObject(value)** | Check that an object contains the expected subset. |
| **toBeTruthy / toBeFalsy** | Check the Boolean coercion of a value. |
| **toBeNull / toBeUndefined** | Distinguish null from undefined. |
| **toContain(value)** | Check an array item or string substring. |
| **toHaveLength(n)** | Check a length property. |
| **toThrow(error)** | Check a synchronous function for a thrown error; pass the function, not its already-evaluated result. |
| **toHaveBeenCalled()** | Check that a mock or spy was called. |
| **toHaveBeenCalledWith(args)** | Check arguments recorded by a mock or spy. |

## Coverage / 覆盖率

Run Jest with the project’s configured coverage option, commonly --coverage. Coverage reports which statements, branches, functions, and lines ran; a high percentage does not prove that assertions check meaningful behavior or edge cases.

## References / 参考资料

- [Jest 30.0 documentation](https://jestjs.io/docs/30.0/getting-started)
- [Jest: ECMAScript Modules](https://jestjs.io/docs/30.0/ecmascript-modules)
- [Jest: The Jest Object](https://jestjs.io/docs/30.0/jest-object)
- [Jest: Mock Functions](https://jestjs.io/docs/30.0/mock-functions)
- [Frontend Testing / 前端测试](../../../frontend/testing/frontend-testing.md)
