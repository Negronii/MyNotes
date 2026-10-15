# Python Fundamentals / Python基础

**Core model / 核心模型：** Python names are bindings to objects. A collection may be changed in place or a name may be rebound to another object; those are different operations. Function defaults are evaluated when the function is defined, iterators produce values as they are requested, and context managers define cleanup around a block. Type hints describe intent to static tools but do not validate runtime input. A virtual environment separates a project's installed packages from other environments. / Python 名称绑定到对象。集合可以被原地修改，名称也可以重新绑定到另一个对象，这是两种不同操作。函数默认值在函数定义时求值，迭代器按需产生值，上下文管理器则为代码块定义资源清理。类型提示表达意图并帮助静态工具检查，但不会在运行时验证输入。虚拟环境将项目安装的包与其他环境隔离。

**Key terms / 关键术语：** object / 对象；name binding / 名称绑定；mutable / 可变；immutable / 不可变；alias / 别名；shallow copy / 浅拷贝；default argument / 默认参数；iterable / 可迭代对象；iterator / 迭代器；generator / 生成器；exception / 异常；context manager / 上下文管理器；type hint / 类型提示；virtual environment / 虚拟环境。

## Collections and object references / 集合与对象引用

Lists and dictionaries are mutable: an operation such as `append` or item assignment changes that object. Strings and tuples are immutable. A tuple cannot have its slots replaced, although it can still contain a mutable object whose value changes. Sets keep unique elements and do not provide sequence indexing; dictionaries map keys to values and preserve insertion order in Python 3.7 and later.

A name does not contain a separate copy of the value. Assignment binds the name to an object, so two names can refer to the same mutable object. Mutating through either name is visible through the other. Rebinding one name changes only that name's binding. A shallow copy creates a new outer container while keeping references to nested objects; use a deeper copy or explicit reconstruction only when the nested values also need independent ownership.

~~~python
event = {"id": "evt-1", "tags": ["new"]}
alias = event
alias["tags"].append("priority")
print(event["tags"])  # ['new', 'priority']

outer_copy = event.copy()
outer_copy["id"] = "evt-copy"  # a different outer dictionary
outer_copy["tags"].append("shared")  # the nested list is still shared
print(event["tags"])  # ['new', 'priority', 'shared']

alias = {"id": "evt-2", "tags": []}  # only alias is rebound
print(event["id"])  # evt-1
~~~

## Calls, argument binding, and defaults / 调用、参数绑定与默认值

At a call, Python binds supplied argument values to parameters by position or keyword. A parameter receives a reference to the supplied object; the call does not copy a mutable argument. Mutating that object inside a function can therefore be observed by the caller, while assigning a new object to the local parameter only rebinds that local name.

Default expressions are evaluated once when Python executes the `def` statement. If the default is a list or dictionary and the function mutates it, later calls reuse that same object. Use `None` when it means “no value supplied,” then create per-call state inside the function. If `None` itself is a meaningful input, choose a separate sentinel.

~~~python
def unsafe_add(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

print(unsafe_add("first"))   # ['first']
print(unsafe_add("second"))  # ['first', 'second'] — same default list

def add(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items

print(add("first"))   # ['first']
print(add("second"))  # ['second']
~~~

## Iteration and generators / 迭代与生成器

An **iterable** can supply an iterator. An **iterator** returns its next value on request and signals completion with `StopIteration`; a `for` loop handles that protocol. A generator function uses `yield` to produce an iterator whose local state resumes at the next request. This lets a pipeline process one item at a time instead of first building a complete result list. The work, and any exception raised by that work, happens as the consumer advances the generator. A generator is usually one-pass; materializing it with `list(...)` consumes it and stores all produced values.

~~~python
from collections.abc import Iterable, Iterator

def ready_rows(rows: Iterable[dict[str, str]]) -> Iterator[dict[str, str]]:
    for row in rows:
        if row["status"] == "ready":
            yield row
~~~

Streaming reduces intermediate storage and can begin output early, but it does not make a whole operation atomic. If a later row is invalid, earlier rows may already have been emitted or acted on. Validate or stage first when the operation requires all-or-nothing effects.

## Exceptions and context managers / 异常与上下文管理器

Exceptions report that an operation could not complete normally. Catch one where the program can recover, translate it into a useful boundary error, or add context and re-raise it with `raise ... from error`. Avoid swallowing an exception when the caller still needs to know that work failed.

A context manager pairs setup and cleanup around a block. Once `__enter__` completes successfully, `__exit__` is called when the block ends, including when an exception leaves the block. A context manager may intentionally suppress an exception; ordinary file context managers close the file and allow the original error to continue. This is why file and temporary-directory lifetimes should be explicit rather than left to garbage collection.

## What type hints do and do not do / 类型提示的作用与边界

Annotations give readers and static analyzers a shared description of expected values and returns. A type checker can report a mismatch before execution, and an editor can use the information for navigation and completion. Python does not automatically reject a value because it conflicts with an annotation; data read from a file, database, or network still needs parsing and validation at that boundary. Runtime validation requires an explicit check or a library designed to perform it.

~~~python
def declared_integer() -> int:
    return "still a string"

print(declared_integer())  # Python returns the string; a type checker can flag it
~~~

## A small file-processing example / 小型文件处理示例

Save this as `python-fundamentals-example.py`. It filters synthetic CSV rows lazily, copies each selected row before adding a tag, and uses nested context managers to close the file and remove the temporary directory even if parsing raises an exception.

~~~python
import csv
from collections.abc import Iterable, Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

Row = dict[str, str]


def ready_rows(rows: Iterable[Row]) -> Iterator[Row]:
    for line_number, row in enumerate(rows, start=2):  # line 1 is the header
        try:
            status = row["status"]
            count = int(row["count"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"CSV row {line_number}: status and integer count are required"
            ) from error

        if status == "ready" and count > 0:
            yield row


def add_tag(row: Row, tag: str = "reviewed") -> Row:
    enriched = row.copy()  # a shallow copy is enough because values are strings
    enriched["tag"] = tag
    return enriched


CSV_TEXT = """id,status,count
evt-1,ready,3
evt-2,queued,1
evt-3,ready,nope
"""


def main() -> None:
    try:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.csv"
            path.write_text(CSV_TEXT, encoding="utf-8")

            with path.open(encoding="utf-8", newline="") as source:
                for row in ready_rows(csv.DictReader(source)):
                    print(add_tag(row))
    except ValueError as error:
        print(f"Rejected input: {error}")


if __name__ == "__main__":
    main()
~~~

Expected output:

~~~text
{'id': 'evt-1', 'status': 'ready', 'count': '3', 'tag': 'reviewed'}
Rejected input: CSV row 4: status and integer count are required
~~~

The first row is yielded before the generator reaches the malformed fourth CSV line. The example catches the parsing error outside both `with` blocks, so the file and temporary directory still close during exception unwinding. A real application that writes results to a database or calls a remote service must decide whether partial progress is acceptable and use a transaction or staging boundary when it is not.

## Language behavior, implementations, and versions / 语言语义、实现与版本

The examples use Python 3.11 syntax and the language behavior documented for Python 3.11. Names, mutability, default evaluation, iteration, and `with` cleanup are language/runtime contracts; they do not depend on CPython's internal object layout. Other details can be implementation-specific or change between Python versions. For example, dictionary insertion order is a language guarantee from Python 3.7; CPython 3.6 preserved it as an implementation detail. In CPython, `id(obj)` currently represents an object's memory address, but code should not treat an identity value as a durable identifier. Check the target interpreter and minimum supported version before relying on newer syntax or runtime behavior.

## Isolated environment and run command / 隔离环境与运行命令

A virtual environment gives a project its own package installation area; it does not install or pin the Python interpreter itself. Select the intended interpreter when creating the environment, and use that environment's Python to invoke `pip` so package installation and execution target the same environment. Declare third-party requirements in the project's packaging or dependency files. A dependency-free example needs no installation step.

On POSIX, from the directory containing the saved example, create an environment and run it with:

~~~sh
python3.11 -m venv .venv && .venv/bin/python python-fundamentals-example.py
~~~

For a project with a `requirements.txt`, install its declared packages with `.venv/bin/python -m pip install -r requirements.txt` before running the script. A virtual environment isolates packages, while repeatability still depends on selecting a compatible Python version and recording the project's dependency versions and platform requirements.

**Verified run / 运行验证：** The file-processing example ran with CPython 3.11.13 and printed the expected output above. This verifies the example on that interpreter; it is not a claim that every Python implementation or platform has identical implementation details.

**Related notes / 相关笔记：** [API Reliability and Asynchronous Delivery / API可靠性与异步交付](../reliability/api-reliability-and-async-delivery.md) explains timeout, cancellation, retries, and bounded work at network and queue boundaries; those correctness concerns also apply to Python services. Python-specific coroutine and framework behavior belongs in a separate async/API note.

**Sources / 来源：** Python 3.11 [Tutorial](https://docs.python.org/3.11/tutorial/) and [Language Reference](https://docs.python.org/3.11/reference/), including [objects and types](https://docs.python.org/3.11/reference/datamodel.html#objects-values-and-types), [function definitions](https://docs.python.org/3.11/reference/compound_stmts.html#function-definitions), [iterators and generators](https://docs.python.org/3.11/reference/datamodel.html#generator-functions), and [`with` statements](https://docs.python.org/3.11/reference/compound_stmts.html#the-with-statement); [`typing`](https://docs.python.org/3.11/library/typing.html); and the Python Packaging User Guide's [installing packages](https://packaging.python.org/en/latest/tutorials/installing-packages/) and [managing application dependencies](https://packaging.python.org/en/latest/tutorials/managing-dependencies/) tutorials. Checked 2026-10-15.

## Representative answers / 代表性回答

**How do mutability, argument binding, and defaults affect a function call? / 可变性、参数绑定与默认值如何影响函数调用？** Names bind to objects, so a caller and a parameter can refer to the same mutable object. An in-place mutation is visible through both references; rebinding the local parameter does not rebind the caller's name. Python evaluates a default expression when the function is defined, so a mutable default is shared across calls. Use `None` and allocate a fresh list or dictionary inside when each call needs independent state.

名称绑定到对象，因此调用方和形参可能引用同一可变对象。原地修改会通过两个引用都可见；在函数内部重新绑定形参不会改变调用方的名称绑定。Python 在函数定义时求值默认表达式，因此可变默认值会在多次调用间共享。若每次调用需要独立状态，使用 `None` 并在函数内部创建新列表或字典。

**How do iterators, generators, and context managers control work and resources? / 迭代器、生成器与上下文管理器如何控制工作和资源？** An iterator produces one value per request, and a generator packages that pull-based behavior with `yield` and saved execution state. That can avoid building an entire intermediate collection, but later errors may occur after earlier values have already been consumed. A context manager runs its exit behavior when a block ends, including during exception unwinding, so files and other resources have a clear cleanup boundary.

迭代器按请求产出一个值，生成器通过 `yield` 和保存的执行状态封装这种拉取式行为。这样可以避免构建整个中间集合，但后续错误可能在较早的值已经被消费后才发生。代码块退出时（包括异常展开期间），上下文管理器都会运行退出逻辑，因此文件等资源有明确的清理边界。

**What do Python type hints guarantee at runtime? / Python 类型提示在运行时保证什么？** By themselves, they guarantee nothing about the values passed or returned. They communicate expected shapes to humans and static tools. Programs still parse and validate untrusted or external data where it enters the application, and use explicit runtime checks when runtime enforcement is required.

类型提示本身不会在运行时保证输入值或返回值的类型。它们向读者和静态工具传达预期的数据形状。程序仍需在外部数据进入应用时解析与校验；需要运行时强制时，应添加显式检查或使用专门的校验库。
