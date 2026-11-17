# Python 的值、迭代器与资源生命周期如何工作？

**案例：** 一个报表 worker（工作进程）读取一份合成的 CSV（comma-separated values，逗号分隔值）文件，把状态为 `ready` 且数量为正的事件加入 11 月报表 `Report("November", source_rows)`。文件里第一条事件有一个带引号的字段跨了两行，最后一条事件的状态无效。本章跟着这份文件回答四个问题：变量名指向哪些对象；修改会不会被其他名字看到；生成器何时交出每一行；坏记录出现后，哪些状态保留下来、哪些资源被关闭。

![报表处理从 CSV 记录到部分结果和资源清理的流程](resources/python-report-pipeline.svg)

图中的 `for` 循环每向生成器要一个值，生成器才往前执行一段。前几行已经加入 `report.rows` 之后，后面的坏记录仍会抛出异常；异常离开 `with` 块时会关闭文件、清理临时目录，却不会撤销已经修改过的 Python 对象。

本章的 Python 代码块要按页面顺序在同一个进程里执行，后面的代码会沿用前面创建的 `Report` 实例和列表；解析阶段会把 `evt-1`、`evt-3` 加入这个列表。

## 创建 Report 时，名字绑定到什么？

Python 中的数据都由对象表示。每个对象有 identity（身份）、type（类型）和值。

- 身份在对象存续期间不变：`is` 判断两边是不是同一个对象，`id(obj)` 返回代表身份的整数。对象销毁后，另一个对象可能复用同一个 `id()`，所以它不能当作跨运行或长期保存的业务标识。
- 类型决定对象支持哪些操作、值可以取哪些范围。类型不像列表内容那样能随意原地修改，但也不是绝对不可改：在 CPython 3.11.13 中，`class A: pass` 和 `class B: pass` 的实例内存布局兼容；对 `obj = A()` 先保存 `saved_id = id(obj)`，再执行 `obj.__class__ = B`，会得到 `type(obj) is B` 且 `id(obj) == saved_id`。这种受限的赋值只改了对象的类型，并没有换成另一个对象。
- `==` 比较值是否相等，具体的相等规则可以由类型自己定义。

变量名只是 namespace（命名空间）中的一个绑定。赋值通常只是让名字指向某个对象，并不复制对象；多个名字指向同一个对象，称为 aliasing（别名）。普通类调用通常先由 `__new__` 取得实例，再由 `__init__` 初始化该实例；`__init__` 本身不负责创建新实例。下面的 `Report` 把标题和传入的列表存为实例属性：

~~~python
class Report:
    def __init__(self, title: str, rows: list[dict[str, object]]) -> None:
        self.title = title
        self.rows = rows

source_rows = []
report = Report("November", source_rows)
rows_alias = report.rows
print(report.rows is source_rows, rows_alias is source_rows)
~~~

输出是 `True True`：`report` 指向新建的 `Report` 实例，而 `source_rows`、`report.rows` 和 `rows_alias` 指向同一个列表对象。`self.rows = rows` 只保存对列表的引用，没有复制列表或其中的对象。这些普通属性绑定保存在实例的 `__dict__`（属性字典）里；本章的 `title` 读写还没有 descriptor（描述符）介入，下一篇会在同一个 `Report` 案例中加入这层机制。

## 生成器如何把一条记录交给报表？

Report 和行列表准备好之后，下一步是把 CSV 记录逐条交给它。iterable（可迭代对象）能提供迭代器；iterator（迭代器）每次返回一个值，没有下一个值时抛出 `StopIteration`，`for` 循环会自动处理这个结束信号。含有 `yield` 的函数是生成器函数：调用它只返回一个生成器对象，函数体要等 `for` 循环或 `next()` 来要下一个值时才执行。`list(generator)` 则会一口气取完所有产出存进列表，直到耗尽或遇到异常为止，也就失去了逐条处理的内存优势。生成器让处理方不必先把整份输入读成列表；但要注意，已经产生的副作用不会因为后面出错而自动回滚。

下面的代码块接着上一段执行。生成器 `ready_rows` 检查 CSV 的表头、列数、状态和数量是否为整数，把 `tags` 按 `|` 拆成列表，只交出 `status == "ready"` 且 `count > 0` 的事件；状态为 `queued` 的事件虽然合法，也会被过滤掉。`csv.reader` 的 `line_num` 是已经读过的源文件物理行数；只要有一条记录的引号字段跨了多行，它就会大于记录序号。打开文本文件时传入 `newline=""`，是为了让 CSV 模块按自己的规则处理字段内的换行。

~~~python
import csv
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TextIO

def ready_rows(source: TextIO) -> Iterator[dict[str, object]]:
    reader = csv.reader(source)
    try:
        headers = next(reader)
    except StopIteration:
        return

    expected = ["id", "status", "count", "tags", "note"]
    if headers != expected:
        raise ValueError("unexpected CSV header")

    for values in reader:
        line_number = reader.line_num
        if len(values) != len(headers):
            raise ValueError(f"CSV physical line {line_number}: wrong column count")

        fields = dict(zip(headers, values))
        status = fields["status"]
        if status not in {"ready", "queued"}:
            raise ValueError(
                f"CSV physical line {line_number}: unknown status {status!r}"
            )
        try:
            count = int(fields["count"])
        except ValueError as error:
            raise ValueError(
                f"CSV physical line {line_number}: count must be an integer"
            ) from error

        row = {**fields, "count": count, "tags": fields["tags"].split("|")}
        if status == "ready" and count > 0:
            yield row

CSV_TEXT = (
    "id,status,count,tags,note\n"
    'evt-1,ready,3,new|priority,"account\n'
    'export"\n'
    "evt-2,queued,1,backlog,skip\n"
    "evt-3,ready,2,review,year-end\n"
    "evt-4,unknown,1,bad,invalid\n"
)

source = None
path = None
try:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "events.csv"
        path.write_text(CSV_TEXT, encoding="utf-8")
        with path.open(encoding="utf-8", newline="") as source:
            for row in ready_rows(source):
                report.rows.append(row)
except ValueError as error:
    print(f"Rejected input: {error}")

print(source.closed, path.exists())
print([row["id"] for row in report.rows])
print(repr(report.rows[0]["note"]))
~~~

本机以 CPython 3.11.13 执行上述代码块，解析阶段输出：

~~~text
Rejected input: CSV physical line 6: unknown status 'unknown'
True False
['evt-1', 'evt-3']
'account\nexport'
~~~

`for row in ready_rows(source)` 每要一个值，生成器就开始运行或从上次 `yield` 的位置恢复；控制顺序是：外层 `for` 向 `ready_rows` 要值，生成器再向 `csv.reader` 取一条 CSV 记录。

1. 第一次请求：先读表头，再取到占物理行 2–3 的 `evt-1`，它的 `note` 是含换行的 `'account\nexport'`。事件满足 `status == "ready" and count > 0`，生成器 `yield` 它，循环把它追加到报表。
2. 第二次请求：从上次 `yield` 处恢复，先取到合法但状态为 `queued` 的 `evt-2`，条件不满足；生成器继续向 `csv.reader` 取下一条，`yield` 满足条件的 `evt-3`。
3. 第三次请求：恢复后读到物理行 6 的 `evt-4`，状态 `unknown` 不合法，于是抛出异常，不再产出值。

生成器只是借用调用方已经打开的 `source`，不负责打开或关闭它。本例中，异常从循环中传出后，两个 context manager（上下文管理器）由内向外依次退出：内层的文件上下文关闭文件，外层的 `TemporaryDirectory` 删除临时目录，之后异常才被 `except` 捕获。打印的 `True False` 分别是 `source.closed` 和 `path.exists()`：`source` 这个名字仍指向那个已关闭的文件对象，`path` 也仍是一个 `Path` 值，只是它指向的位置已经不存在。

外面的 `report` 仍引用原来的列表，已经追加的两条记录不会因为资源退出而撤销。`with` 语句只负责调用上下文管理器的退出方法，退出时是否回滚由管理器自己的实现决定；这里的文件和临时目录清理都不会回滚列表修改。如果结果必须“全部成功或全部不生效”，应先验证并暂存，再在合适的事务边界一次提交。另外，自定义上下文管理器的 `__exit__` 可以返回真值来吞掉块内异常，也可能在清理失败时抛出新异常；所以判断错误能否到达外层 `except`，还要看退出方法怎么写。本例的两个管理器都在清理成功后让原异常继续传播。

## 改对象和改名字，影响范围有什么不同？

现在 `report.rows` 中已有 `evt-1` 和 `evt-3`。下图只展开第一条记录：实例的 `rows` 属性、`source_rows` 和 `rows_alias` 三条引用都指向同一个行列表；列表中的事件字典又引用一个标签列表。

![Report 实例、行列表、事件字典与标签列表的对象引用关系](resources/python-object-aliases.svg)

list 和 dict 是可变对象，原地追加或更新会改变同一对象的值；给名字重新赋值则只改变该名字的绑定。shallow copy（浅拷贝）只新建最外层容器，里面的成员仍是原来那些对象的引用：

~~~python
rows_alias[0]["tags"].append("reviewed")
copied_rows = report.rows.copy()
copied_rows[0]["tags"].append("shared")
print(report.rows[0]["tags"])

rows_alias = []
print(len(report.rows))
~~~

输出依次是 `['new', 'priority', 'reviewed', 'shared']` 和 `2`。第一行通过别名修改原列表中第一条事件的标签。`copy()` 新建了一个行列表，但 `copied_rows[0]` 和 `report.rows[0]` 仍指向同一个事件字典，字典中的 `tags` 也仍是同一列表；所以通过复制列表再修改嵌套标签，原报表也能观察到变化。最后把 `rows_alias` 改绑到新列表，不会替 `report.rows` 重新绑定。若需要独立修改标签，应重建对应的事件字典和 `tags` 列表；只有确实需要隔离整棵对象图时，再考虑 `deepcopy`（深拷贝）。

函数调用同样遵循这套规则：调用时为形参建立新的局部名字，让它们引用传入的对象。函数原地修改形参所指的列表，调用方能看到；函数把形参改绑到另一个列表，调用方的名字不受影响。另一个常见共享点是默认值：默认表达式在执行 `def` 时求值一次，后续调用会继续使用同一对象。

~~~python
def unsafe_add(item, items=[]):
    items.append(item)
    return items

print(unsafe_add("first"))
print(unsafe_add("second"))

def add(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

print(add("first"))
print(add("second"))
~~~

前两次 `unsafe_add` 共用默认列表，结果依次是 `['first']` 和 `['first', 'second']`。`add` 在每次没有传入列表时都新建一个，因此结果分别是 `['first']` 和 `['second']`。如果 `None` 也是有意义的输入，再用独立 sentinel（哨兵值）表示“未提供”。

“不可变”也只管对象本身这一层：字符串不能原地改写；元组不能替换自己的成员，但如果成员是列表，那个列表照样可以修改。顺带区分几种常见容器：`set` 保存不重复的元素，但没有下标；`dict` 把键映射到值，从 Python 3.7 起保持插入顺序是语言规范的保证（在 CPython 3.6 中只是实现细节）。另外，对象不可变并不意味着指向它的名字不能重新绑定。

## 类型提示和虚拟环境能保证什么？

前面的代码写了不少注解，但真正拦下坏数据的并不是它们。type hint（类型提示）里的 `TextIO`、`Iterator` 和返回类型，帮助读者、IDE 和静态类型检查器理解预期的数据形状；Python 运行时默认不会因为实际对象不符合注解就拒绝它。示例中的输入验证由表头检查、状态判断和 `int()` 转换执行，而不是由类型注解执行。文件也不应等垃圾回收时才关闭；`with` 语句使用上下文管理器（context manager）在确定的控制流边界执行关闭。

这份示例只用到 Python 标准库，把各代码块依次保存进同一个文件即可运行。virtual environment（虚拟环境）基于创建它时所用的那个 Python 解释器，只隔离项目安装的第三方包；它不会给项目另装一个不同版本的 Python。所以要在创建时就选定解释器，之后用环境里的 Python 来运行程序和安装依赖，例如：

~~~sh
python3.11 -m venv .venv
.venv/bin/python python-fundamentals-example.py
~~~

项目需要第三方依赖时，也使用同一个环境的解释器运行 `-m pip`，例如 `.venv/bin/python -m pip install httpx`；这样安装位置与程序运行环境一致。上面的 `.venv/bin/` 是 POSIX 环境路径。

本章用普通实例属性建立了 `Report` 对象和行列表的状态。下一篇沿用 `November` 报表及其事件数据，把 `title` 改成会验证输入的数据描述符，并说明属性读取、实例字典、绑定方法和多继承如何共同决定结果：[Python 实例属性何时来自对象字典，何时变成描述符或绑定方法？](python-attribute-lookup-and-mro.md)。若同类报表改由异步接口读取，等待 I/O 时如何不阻塞其他请求、资源要保持打开到什么时候，见[异步 FastAPI 接口为什么仍会阻塞？](python-async-and-fastapi.md)。

> [!info]- 来源
> - 对象身份、类型、可变性、不可变容器中的可变成员，以及不要依赖对象立即终结：[Python 3.15.2 Language Reference, Data model §3.1](https://docs.python.org/3.15/reference/datamodel.html#objects-values-and-types)，核对于 2026-11-12。受限 `__class__` 赋值须兼容 `__slots__`：[Python 3.15.2 Language Reference, `__slots__`](https://docs.python.org/3.15/reference/datamodel.html#object.__slots__)；固定实现 CPython 3.11.13 的兼容性检查和类型指针替换：[Objects/typeobject.c `compatible_for_assignment` / `object_set_class`](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L4715-L4869)。`id()` 在对象生命周期内唯一、恒定，生命周期不重叠的对象可能复用该值：[Python 3.15.2 Built-in Functions, `id`](https://docs.python.org/3.15/library/functions.html#id)；CPython 3.11.13 中它由对象指针转成整数：[Python/bltinmodule.c `builtin_id`](https://github.com/python/cpython/blob/v3.11.13/Python/bltinmodule.c#L1197-L1225)。
> - 类调用通常经 `__new__` 取得实例并由 `__init__` 初始化；名字可别名引用同一对象：[Python 3.15.2 Language Reference, Classes / Basic customization](https://docs.python.org/3.15/reference/datamodel.html#classes)，[Python 3.15.2 Tutorial, Classes §9.1](https://docs.python.org/3.15/tutorial/classes.html#a-word-about-names-and-objects)，核对于 2026-11-12。
> - 字典插入顺序从 3.7 起是语言保证，CPython 3.6 中是实现细节：[Python 3.15.2 Built-in Types, Dictionary](https://docs.python.org/3.15/library/stdtypes.html#dict)，核对于 2026-11-12。
> - 函数默认参数在函数定义时求值：[Python 3.15.2 Tutorial, Default Argument Values](https://docs.python.org/3.15/tutorial/controlflow.html#default-argument-values)，核对于 2026-11-12。
> - 生成器函数、`yield` 与按需迭代：[Python 3.15.2 Language Reference, Yield expressions](https://docs.python.org/3.15/reference/expressions.html#yield-expressions)，核对于 2026-11-12。
> - 多行 CSV 记录与 `reader.line_num` 的物理行计数、打开文件时的 `newline=""`：[Python 3.15.2 `csv` library](https://docs.python.org/3.15/library/csv.html#csv.csvreader.line_num)，本例于 CPython 3.11.13 重放。
> - `with` 语句的进入、退出和异常传播：[Python 3.15.2 Language Reference, The with statement](https://docs.python.org/3.15/reference/compound_stmts.html#the-with-statement)；文件流作为上下文管理器在块退出时关闭：[Python 3.15.2 `io.IOBase`](https://docs.python.org/3.15/library/io.html#io.IOBase)；临时目录上下文退出时清理：[Python 3.15.2 `tempfile.TemporaryDirectory`](https://docs.python.org/3.15/library/tempfile.html#tempfile.TemporaryDirectory) 和固定实现 [CPython 3.11.13 `Lib/tempfile.py`](https://github.com/python/cpython/blob/v3.11.13/Lib/tempfile.py#L857-L949)，本例记录了实际资源状态。
> - Python 运行时默认不强制函数和变量注解：[Python 3.15.2 `typing`](https://docs.python.org/3.15/library/typing.html)，核对于 2026-11-12。
> - 虚拟环境隔离包安装位置，并由创建命令选定基础解释器：[Python 3.15.2 `venv`](https://docs.python.org/3.15/library/venv.html)，核对于 2026-11-12。
