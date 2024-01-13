## Promises in TypeScript

**1. Introduction to Promises**

- Definition: Represents a future value.
- States:
  - Pending: Initial state.
  - Fulfilled: Operation completed successfully.
  - Rejected: Operation failed.

**2. Creating a Promise**

- Use the Promise constructor.

```typescript
const promise = new Promise<string>((resolve, reject) => {
  setTimeout(() => {
    resolve("Promise is resolved!");
  }, 2000);
});
```

**3. Consuming a Promise**

- Use `.then()` for success and `.catch()` for errors.

```typescript
promise
  .then((value) => console.log(value))
  .catch((error) => console.error("Something went wrong:", error));
```

**4. Error Handling in Promises**

- Use "reject" for errors.

```typescript
const failingPromise = new Promise<string>((resolve, reject) => {
  setTimeout(() => reject(new Error("Promise failed!")), 2000);
});
```

**5. Chaining Promises**

- Chain multiple `.then()`.

```typescript
getNumber()
  .then((num) => num * 2)
  .then((result) => console.log(result));
```

**6. Promise Utility Functions**

- **6.1. Promise.all()**: Waits for all promises.

```typescript
Promise.all([promise1, promise2, promise3]).then((values) =>
  console.log(values)
);
```

- **6.2. Promise.race()**: First promise to resolve/reject.

```typescript
Promise.race([promiseA, promiseB]).then((value) => console.log(value));
```

**7. Async/Await**

- Syntactic sugar over Promises.

```typescript
async function main() {
  try {
    const number = await fetchNumber();
    console.log(number);
  } catch (error) {
    console.error("Error fetching number:", error);
  }
}
main();
```

**Intervals and Timeouts**

- Both can be cancelled.

```typescript
let intervalId = setInterval(1000);
clearInterval(intervalId);
```
