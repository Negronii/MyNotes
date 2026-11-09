# Python 的值、迭代器与资源生命周期如何工作？

**案例：** worker 读取账户报表的 CSV 分页，把有效行逐个送入后续处理。要避免意外共享行对象，不能把整份文件先展开到内存；遇到坏行时，还要关闭文件和临时目录。Python 名称绑定到对象，迭代器按需交付值，上下文管理器则界定资源清理。

~~~mermaid
flowchart LR
    File[CSV 文件] --> Iterator[生成器逐行读取]
    Iterator -->|有效行| Yield[交付一行给调用者]
    Iterator -->|后续格式错误| Error[抛出解析异常]
    Error --> Unwind[离开嵌套 with 块]
    Unwind --> Close[关闭文件并删除临时目录]
    Yield --> Partial[更早输出的行已经离开生成器]
~~~

图中从输入到输出是一条惰性流程：错误可能在已经产出部分结果后才出现，所以资源会清理，但副作用不会自动回滚。

## 名称、可变对象和浅拷贝怎样相互影响？

赋值通常是把名称绑定到对象，不是复制对象。列表和字典可变；同一列表被两个名称引用时，经任一名称原地修改，另一个名称看到的也是同一结果。把其中一个名称重新绑定到新字典，不会改变另一个绑定。浅拷贝会新建外层容器，但其中嵌套的可变对象仍可能共用。

字符串和元组不可原地替换其成员；不过，元组里仍可以放一个可变列表，再修改列表内容。set 保存唯一元素但不提供序列索引；字典把键映射到值，并从 Python 3.7 起保证保留插入顺序。CPython 的 id(obj) 当前以对象地址作为运行期身份值，但不能跨进程或运行期拿来标识账户、job 或数据库记录。

~~~python
event = {"id": "evt-1", "tags": ["new"]}
alias = event
alias["tags"].append("priority")
print(event["tags"])

outer_copy = event.copy()
outer_copy["id"] = "evt-copy"
outer_copy["tags"].append("shared")
print(event["tags"])

alias = {"id": "evt-2", "tags": []}
print(event["id"])
~~~

输出依次是 ['new', 'priority']、['new', 'priority', 'shared']、evt-1。若要隔离嵌套状态，应按所需字段显式重建，或在确有需要时深拷贝；不要把“拷贝了字典”理解为递归复制所有对象。

函数调用也传递对象引用。若函数原地修改传入列表，调用者能观察到修改；函数内部把形参改绑到新对象则不会替调用方重新绑定名称。函数默认表达式在执行 def 时求值一次，因此可变默认对象会被多次调用共用：

~~~python
def unsafe_add(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

print(unsafe_add("first"))
print(unsafe_add("second"))

def add(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items

print(add("first"))
print(add("second"))
~~~

前两个结果会累积为 ['first'] 和 ['first', 'second']；修正后的调用分别得到 ['first'] 和 ['second']。若 None 本身也是有效输入，用单独 sentinel 表示“调用方未提供”。

## 迭代器和生成器如何控制读取量？

可迭代对象能提供迭代器；迭代器每次被请求时给出一个值，直到完成。生成器函数包含 yield，调用时返回一个保存执行位置的迭代器；循环或消费端每次请求下一值时，生成器才继续执行。这样可以逐行处理大文件，避免先构造完整结果列表；把生成器转成 list 则会立即消费并保存所有值。

~~~python
from collections.abc import Iterable, Iterator

Row = dict[str, str]

def ready_rows(rows: Iterable[Row]) -> Iterator[Row]:
    for row in rows:
        if row["status"] == "ready":
            yield row
~~~

惰性读取减少中间存储，也可以更早开始输出，但不会让一个多行事务自动具备原子性。如果第 500 条数据记录才有格式错误，而前 499 条已经写入其他系统，就必须由调用方决定这些部分结果能否保留；需要全有或全无时，先验证并暂存，或把修改置于合适的事务边界。

## 解析失败时资源和先前输出会怎样？

下面用合成 CSV 展示完整过程。生成器按 CSV 记录验证列数、状态值和整数数量；错误时读取 `csv.reader.line_num`，报告读到该记录时的物理文件行号，并保留原始异常。CSV 记录可能跨多行，所以不能用记录序号当文件行号。外层在文件与临时目录两个 with 块之外捕获异常。坏记录到来之前已经打印的报表行仍会保留，但两个资源都会在异常退出时关闭。

~~~python
import csv
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

Row = dict[str, str]

def ready_rows(source) -> Iterator[Row]:
    reader = csv.reader(source)
    try:
        headers = next(reader)
    except StopIteration:
        return

    required = {"id", "status", "count"}
    if not required.issubset(headers):
        raise ValueError("CSV header must include id, status, and count")

    for values in reader:
        line_number = reader.line_num
        if len(values) != len(headers):
            raise ValueError(
                f"CSV physical line {line_number}: column count does not match header"
            )
        row = dict(zip(headers, values))
        try:
            status = row["status"]
            if status not in {"ready", "queued"}:
                raise ValueError(f"unknown status {status!r}")
            count = int(row["count"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"CSV physical line {line_number}: status must be ready or queued, "
                "and count must be an integer"
            ) from error

        if status == "ready" and count > 0:
            yield row

def add_tag(row: Row, tag: str = "reviewed") -> Row:
    enriched = row.copy()
    enriched["tag"] = tag
    return enriched

CSV_TEXT = """id,status,count,note
evt-1,ready,3,"account
export"
evt-2,queued,1,skip
evt-3,unknown,2,bad-status
"""

try:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "events.csv"
        path.write_text(CSV_TEXT, encoding="utf-8")

        with path.open(encoding="utf-8", newline="") as source:
            for row in ready_rows(source):
                print(add_tag(row))
except ValueError as error:
    print(f"Rejected input: {error}")
~~~

本机以 CPython 3.11.13 重放，输出第一条 evt-1 记录，再报告 `CSV physical line 5` 的未知状态。该坏行是第 3 条数据记录；第一条 evt-1 记录跨文件第 2、3 两行，第二条 evt-2 在第 4 行，所以记录序号和物理行号不同。生成器是在消费者推进时运行，异常离开两个上下文后文件关闭，TemporaryDirectory 清除其目录。由于第一条结果已输出，资源清理不等同于撤回此前效果。

普通文件的 with 语句能在异常时关闭文件。上下文管理器会先进入代码块，退出时运行清理逻辑；若清理器选择抑制异常，还可改变异常传播，因此应检查实际管理器契约。需及时释放游标、文件或锁时，显式使用 with/finally，不依赖垃圾回收何时运行。

## 类型标注和虚拟环境分别保证什么？

type hint（类型提示）描述函数参数、结果或变量的预期形状，供读者、IDE 和静态类型检查器使用。Python 运行时默认不会因为注解不匹配而拒绝返回值；从网络、文件或数据库读入的 str 仍需解析、验证并转换为可信类型。若一个返回 int 的函数实际返回 str，静态检查器可以报告，但普通调用仍会拿到字符串。

~~~python
def declared_integer() -> int:
    return "still a string"

print(declared_integer())
~~~

本机输出 still a string。版本和实现也要分开说明：本文代码使用 Python 3.11 的语法和标准库行为；字典插入顺序从 Python 3.7 起是语言保证，CPython 3.6 中只是实现细节；CPython 的 id(obj) 目前表现为对象身份值，但不能把它当作跨进程、跨运行的业务标识。

虚拟环境隔离项目安装的包，不会安装或固定 Python 解释器本身。创建环境时选定解释器，再用该环境中的 Python 运行 pip，才能保证装包和执行指向同一环境。将上面的完整文件处理程序保存为 python-fundamentals-example.py。这个示例只依赖标准库，不需要额外安装：

~~~sh
python3.11 -m venv .venv
.venv/bin/python python-fundamentals-example.py
~~~

项目如需第三方库，应把依赖写入项目的 packaging 配置或依赖文件，再用 .venv/bin/python -m pip install -r requirements.txt 从该环境安装；可复现运行还取决于兼容的解释器版本、包版本和平台要求。Python 异步请求怎样选择运行边界见[异步 FastAPI 接口为什么仍会阻塞？](python-async-and-fastapi.md)；实例属性优先级、descriptor 与协作式多继承见[Python 实例属性何时来自对象字典，何时变成描述符或绑定方法？](python-attribute-lookup-and-mro.md)。

> [!info]- 来源
> - 名称绑定、对象可变性和字典顺序：[Python 3.11 Language Reference, Data model](https://docs.python.org/3.11/reference/datamodel.html#objects-values-and-types)，核对于 2026-11-06。
> - 默认参数只在函数定义时求值：[Python 3.11 Tutorial, Default Argument Values](https://docs.python.org/3.11/tutorial/controlflow.html#default-argument-values)，本例于 CPython 3.11.13 重放。
> - `csv.reader.line_num` 计源文件物理行，CSV 记录可跨多行：[Python 3.11 csv module](https://docs.python.org/3.11/library/csv.html#csv.csvreader.line_num)，多行记录例于 CPython 3.11.13 重放。
> - 迭代器、生成器与 StopIteration：[Python 3.11 Language Reference, Data model](https://docs.python.org/3.11/reference/datamodel.html#generator-functions)，CSV 例子于 CPython 3.11.13 重放。
> - with 退出时的资源清理：[Python 3.11 Language Reference, The with statement](https://docs.python.org/3.11/reference/compound_stmts.html#the-with-statement)。
> - 注解不作默认运行时验证：[Python 3.11 typing](https://docs.python.org/3.11/library/typing.html)，注解示例于 CPython 3.11.13 重放。
> - venv 与包安装：[Python 3.11 venv](https://docs.python.org/3.11/library/venv.html)、[Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/installing-packages/)，核对于 2026-11-06。
