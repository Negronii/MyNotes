```ts
class Stack<T> {
    private container: T[] = [];

    push(item: T) {
        this.container.push(item);
    }

    pop(): T | undefined {
        return this.container.pop();
    }

    isEmpty(): boolean {
        return this.container.length === 0;
    }
}

class QueueWithTwoStacks<T> {
    private stackIn: Stack<T> = new Stack<T>();
    private stackOut: Stack<T> = new Stack<T>();

    enqueue(item: T) {
        this.stackIn.push(item);
    }

    dequeue(): T | undefined {
        if (this.stackOut.isEmpty()) {
            while (!this.stackIn.isEmpty()) {
                const item = this.stackIn.pop();
                if (item !== undefined) {
                    this.stackOut.push(item);
                }
            }
        }
        return this.stackOut.pop();
    }

    isEmpty(): boolean {
        return this.stackIn.isEmpty() && this.stackOut.isEmpty();
    }
}

// Example usage
const queue = new QueueWithTwoStacks<number>();
queue.enqueue(1);
queue.enqueue(2);
console.log(queue.dequeue()); // Outputs 1
console.log(queue.dequeue()); // Outputs 2
console.log(queue.isEmpty()); // Outputs true
```