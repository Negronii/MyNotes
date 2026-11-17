# Python 实例属性何时来自对象字典，何时变成描述符或绑定方法？

**承接前篇：** 在[前篇](python-fundamentals.md)中，报表 worker 从 CSV 中接受了 `evt-1` 和 `evt-3` 两条事件，存进 `Report("November", ...)` 的 `rows`；随后通过别名和浅拷贝修改共享的标签列表，第一条事件的 `tags` 最终变成 `['new', 'priority', 'reviewed', 'shared']`。本篇的代码可独立运行，会直接重建这两条记录。新的要求是：标题输入改为带空格的 `"  November  "`，读取 `report.title` 时应得到规范化后的 `November`，全是空白的标题则要拒绝。围绕这个要求，本篇解释两件事：普通类属性、描述符和实例字典里出现同名属性时由谁响应；同一个验证方法如何按多继承的顺序在几个类之间协作完成。

本篇只讨论普通类实例的显式读写，例如 `report.title`、`report.title = value` 和 `getattr(report, name)`。类对象本身的元类查找、特殊语法触发的隐式特殊方法查找，以及代理类的额外规则不属于这条路径。

下文常用的 method resolution order（方法解析顺序，MRO），是 Python 从对象的类出发、沿各基类查找属性时依次检查的类列表，可通过 `类名.__mro__` 查看。

![读取普通实例属性时从类 MRO、描述符和实例字典得到结果的分支](resources/python-attribute-lookup.svg)

图的前半部分是默认 `__getattribute__` 的查找链。只有这条链以 `AttributeError` 结束时，普通点号访问和两参数的 `getattr()` 才会进入末端的 `__getattr__` 回退。描述符的 getter 自己抛出 `AttributeError`，或者重写后的 `__getattribute__` 抛出这个错误，也都会走到这条回退路径，详见下文。

## 为什么同名实例键不会取代标题验证器？

descriptor（描述符）是其类型定义了 `__get__`、`__set__` 或 `__delete__` 的对象。要让点号访问自动调用它，描述符对象必须作为属性放在类字典中，或被实例类型的某个基类继承；把描述符对象放进实例字典只会得到那个普通对象。

下面的 `NonEmptyText` 对外提供 `title` 属性，实际值存在实例字典的 `_title` 键里。三个方法各有分工：`__set_name__` 在类创建时得知自己所属的类和属性名；`__get__` 在通过类访问时返回描述符本身，在通过实例访问时读取存储键；`__set__` 把校验交给实例的 `validate_title` 方法，校验通过后才写入规范化后的值。

这个实现要求使用它的实例有 `__dict__`，并提供 `validate_title` 方法；后面的 `Report` 满足这两个前提。

~~~python
class NonEmptyText:
    def __set_name__(self, owner, name):
        self.public_name = name
        self.storage_name = "_" + name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return instance.__dict__[self.storage_name]
        except KeyError:
            raise AttributeError(self.public_name) from None

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise TypeError("title must be text")
        normalized = instance.validate_title(value)
        instance.__dict__[self.storage_name] = normalized
~~~

这个描述符同时定义了 `__get__` 和 `__set__`，所以是 data descriptor（数据描述符）。读取时，如果沿类的 MRO 找到这样的属性，描述符的 getter 会先于 `report.__dict__` 生效；赋值时，默认的属性设置流程也会先调用它的 `__set__`。因此，即使实例字典里也有 `title` 键，普通的 `report.title` 仍由描述符决定结果。

下面重新定义 `Report`，并重建前篇的事件数据。`NonEmptyText.__set__` 调用的 `instance.validate_title` 是一个普通方法：类里的函数在经实例读取时会绑定到该实例（机制见后文“绑定方法”）。`Report.validate_title` 再通过 `super()` 依次进入审计、去空格和非空检查三个步骤。

~~~python
events = []

class FieldBase:
    def validate_title(self, value):
        events.append("FieldBase")
        if not value:
            raise ValueError("title must contain non-whitespace text")
        return value

class NormalizeMixin(FieldBase):
    def validate_title(self, value):
        events.append("NormalizeMixin.before")
        result = super().validate_title(value.strip())
        events.append("NormalizeMixin.after")
        return result

class AuditMixin(FieldBase):
    def validate_title(self, value):
        events.append("AuditMixin.before")
        result = super().validate_title(value)
        events.append("AuditMixin.after")
        return result

class Report(AuditMixin, NormalizeMixin):
    title = NonEmptyText()
    category = "monthly"

    def __init__(self, title, rows):
        self.title = title
        self.rows = rows

    def validate_title(self, value):
        events.append("Report.validate_title")
        return super().validate_title(value)

    def __getattr__(self, name):
        events.append(f"__getattr__({name})")
        if name == "row_count":
            return len(self.rows)
        raise AttributeError(name)

    def publish(self):
        return f"Published {self.title} ({len(self.rows)} events)"

source_rows = [
    {
        "id": "evt-1",
        "status": "ready",
        "count": 3,
        "tags": ["new", "priority", "reviewed", "shared"],
        "note": "account\nexport",
    },
    {
        "id": "evt-3",
        "status": "ready",
        "count": 2,
        "tags": ["review"],
        "note": "year-end",
    },
]
report = Report("  November  ", source_rows)
print(Report.title is vars(Report)["title"])
print(vars(Report)["title"].storage_name)
print(report.title, report.__dict__["_title"])
print([row["id"] for row in report.rows])
print(events)
~~~

输出为 `True`、`_title`、`November November`、`['evt-1', 'evt-3']`，校验轨迹为 `Report.validate_title → AuditMixin.before → NormalizeMixin.before → FieldBase → NormalizeMixin.after → AuditMixin.after`。`__init__` 里的赋值 `self.title = title` 并没有把标题字符串直接放进 `report.__dict__`：它触发类上的数据描述符，先去掉空格，再由 `FieldBase` 检查结果非空，最后才写入 `_title`。`vars(Report)["title"]` 直接从类字典取出描述符对象；`Report.title` 则经过类属性访问，调用 `__get__(None, Report)`，本例中返回的也是描述符本身，所以第一行输出 `True`。

通过点号访问属性和直接修改字典，是两种不同的操作。下面先绕过描述符，直接往实例字典里写一个同名的 `title` 键，再用正常的赋值语法写入一个空白标题：

~~~python
report.__dict__["title"] = "forged instance value"
print(report.title, report.__dict__["title"], report.__dict__["_title"])

try:
    report.title = "   "
except ValueError as error:
    print(type(error).__name__, str(error))
print(report.title)
~~~

结果是 `November forged instance value November`，接着抛出 `ValueError title must contain non-whitespace text`，最后 `report.title` 仍为 `November`。直接写 `__dict__` 绕开了 `__set__`，但正常读取时仍先调用数据描述符，所以伪造的值不会被读出。不过，描述符只约束普通的属性访问流程，并不是防止任意代码篡改内部状态的安全机制。

## 实例字典、类属性和两种描述符怎样排优先级？

上一节的现象可以归纳成一般规则。默认读取实例属性时，Python 先沿 `type(obj).__mro__` 找到第一个定义了该名称的类属性（下表称“类候选”），再根据这个候选具备哪些描述符方法、以及实例字典里有没有同名键，决定返回什么。关键条件是“数据描述符，并且有 `__get__`”：只有这种能读取的数据描述符，才会在读取时压过实例字典里的同名值。

| 类 MRO 找到的候选 | 实例字典有同名键 | `obj.x` 的结果 |
| --- | --- | --- |
| 有 `__get__` 且有 `__set__` 或 `__delete__` 的数据描述符 | 有或没有 | 调用描述符的 `__get__` |
| 定义了 `__get__`、没有 `__set__` / `__delete__` 的非数据描述符 | 有 | 返回实例字典值 |
| 同一个非数据描述符 | 没有 | 调用描述符的 `__get__` |
| 没有 `__get__` 的类候选，包括只定义 `__set__` / `__delete__` 的描述符 | 有 | 返回实例字典值 |
| 没有 `__get__` 的类候选 | 没有 | 返回类候选本身 |
| 没有类候选 | 有 | 返回实例字典值 |
| 没有类候选 | 没有 | 默认查找抛 `AttributeError`，之后才尝试 `__getattr__` |

这张读取表假定实例有 `__dict__`；若实例没有字典（例如使用了 `__slots__`），查找会跳过实例字典这一步。只要定义了 `__set__` 或 `__delete__` 就算数据描述符，即使没有 `__get__`；但没有 getter 的对象无法在读取时计算属性值，所以它压不过实例字典；实例字典里没有该键时，读到的就是类上的描述符对象本身。

赋值另有一套分派规则，不能套用上面的读取表。类候选定义了 `__set__` 时，`obj.x = value` 会调用它；setter 拒绝这个值时，异常向外传播。只定义了 `__delete__` 的数据描述符同样会拦截默认赋值，但因为没有 `__set__`，赋值会抛出 `AttributeError`，实例字典里已有的同名键也不会被替换。只有类上没有拦截这次赋值的数据描述符、并且实例有 `__dict__` 时，默认赋值才会写入实例字典；实例没有字典时，可能根本无法新增属性。

下面的 `DeleteOnly` 只实现删除协议。即使实例字典已有 `value`，点号赋值也会由类候选拦截并报错，旧值保持不变：

~~~python
class DeleteOnly:
    def __delete__(self, instance):
        pass

class Holder:
    value = DeleteOnly()

holder = Holder()
holder.__dict__["value"] = "kept"
try:
    holder.value = "new"
except AttributeError as error:
    print(type(error).__name__, str(error), holder.__dict__["value"])
~~~

CPython 3.11.13 输出 `AttributeError __set__ kept`。

常见的内置描述符也可以放进这张表。`@property` 是数据描述符。类里定义的普通函数是非数据描述符：读取 `report.publish` 时会调用函数的 `__get__`，得到一个 bound method（绑定方法），它的 `__self__` 是 `report`，`__func__` 是类字典里的那个函数。只有放在类上、经实例读取的函数才会这样绑定；把普通函数直接存进实例字典，读出来的仍是原函数，不会自动补上 `self`。正因为函数是非数据描述符，实例字典里的同名键可以遮住它；这也是为什么对单个实例做 monkey patch（运行时替换）只影响那一个实例。

~~~python
print(report.category)
report.category = "draft"
print(report.category, Report.category)

bound = report.publish
print(bound.__self__ is report, bound.__func__ is vars(Report)["publish"])
print(bound())
report.__dict__["publish"] = "temporary label"
print(report.publish)
del report.__dict__["publish"]
print(report.publish())
~~~

输出先是 `monthly`，之后是 `draft monthly`：普通类属性 `category` 在实例没有同名键时充当默认值；赋值则在实例字典里创建一个遮住它的同名值，类上的值不变。方法部分依次输出 `True True`、`Published November (2 events)`、`temporary label` 和恢复后的 `Published November (2 events)`。

最后看查找失败时的回退。每次显式读取属性，入口都是 `__getattribute__`，默认实现 `object.__getattribute__` 就包含上面那套描述符与实例字典的优先顺序。普通点号访问和两参数 `getattr(obj, "x")` 在外层还有一步：如果 `__getattribute__(self, name)` 抛出 `AttributeError`，就调用类上定义的 `__getattr__(self, name)`。这个错误可以来自默认查找，也可以来自重写后的 `__getattribute__`，或来自描述符的 `__get__`。如果类没有定义 `__getattr__`，或者回退方法也抛出 `AttributeError`，错误就传给调用方。重写 `__getattribute__` 会接管整条默认路径；若还想保留默认行为，应在实现里委托给 `object.__getattribute__(self, name)`，并避免在里面用 `self.other` 读取内部状态，否则会无限递归。

可以从 `row_count` 看出默认回退和直接调用的区别。`report.row_count` 与 `getattr(report, "row_count")` 都在默认查找失败后调用 `Report.__getattr__`；直接调用 `object.__getattribute__` 只做默认查找本身，不会自行调用回退。

~~~python
events.clear()
print(report.row_count, getattr(report, "row_count"))
try:
    object.__getattribute__(report, "row_count")
except AttributeError:
    print("direct object.__getattribute__: AttributeError")
print(events)
~~~

前两次访问都得到 `2`，事件列表只记录两次 `__getattr__(row_count)`；直接调用 `object.__getattribute__` 抛出 `AttributeError`，没有额外调用 `__getattr__`。还有一种情形：查找找到了数据描述符，但 getter 因内部值缺失而抛出 `AttributeError`。这时默认查找同样以这个错误结束，外层的属性访问语法接着尝试 `__getattr__`，而不会回头去读实例字典里的同名值。

下面故意只调用 `Report.__new__` 而不运行 `__init__`，让 `_title` 缺失；同时在实例字典放入伪造的同名 `title` 键。描述符 getter 抛出 `AttributeError` 后，点号访问调用 `__getattr__("title")`；回退也抛错，所以最终仍是 `AttributeError`，字典里的伪造值没有被读出。这只用于显露查找分支，正常业务对象仍通过 `Report(...)` 初始化。

~~~python
events.clear()
incomplete = Report.__new__(Report)
incomplete.__dict__["title"] = "forged instance value"
try:
    incomplete.title
except AttributeError as error:
    print(type(error).__name__)
print(events)
~~~

本机输出是 `AttributeError` 和 `['__getattr__(title)']`。尽管 getter 出错之前 `incomplete.__dict__["title"]` 已经存在，错误仍直接转入 `__getattr__`，查找没有退回去读取实例字典里的同名键。

## 菱形继承中，`super()` 为什么会到达另一个 mixin？

回到第一节的校验轨迹：标题描述符调用的是绑定到当前 `Report` 实例的 `validate_title`，之后每一层都用 `super()` 交给下一层。不带参数的 `super()` 的查找起点是：在“实例实际类型的 MRO”中，找到“当前方法所在的类”，从它后面一个类开始继续查找；它不会固定跳到当前类定义里写的直接父类。所以，校验链的下一站由 MRO 决定。

![Report 的菱形继承结构、C3 线性化结果和 super 调用顺序](resources/python-super-mro.svg)

`Report(AuditMixin, NormalizeMixin)` 声明审计 mixin 在前、规范化 mixin 在后，两者都继承 `FieldBase`，构成菱形继承。Python 用 C3 线性化算法计算 MRO：它保留每个基类自身 MRO 中的顺序，也保留子类声明直接基类时的顺序，并让共同基类 `FieldBase` 在最终 MRO 中只出现一次。

记 `L(C)` 为类 `C` 的 MRO 列表，`merge(...)` 为下文描述的合并步骤，推导如下：

~~~text
L(AuditMixin) = [AuditMixin, FieldBase, object]
L(NormalizeMixin) = [NormalizeMixin, FieldBase, object]
L(Report) = [Report] + merge(
    [AuditMixin, FieldBase, object],
    [NormalizeMixin, FieldBase, object],
    [AuditMixin, NormalizeMixin],
)
~~~

merge 每一轮依次查看各列表的首项，选出第一个“不出现在任何列表尾部（即首项之后的部分）”的类，把它追加到结果中，并从所有以它开头的列表中移除它。先选 `AuditMixin`；从第一张线性化列表和直接基类列表同时移除它后，剩余序列为 `[FieldBase, object]`、`[NormalizeMixin, FieldBase, object]`、`[NormalizeMixin]`。此时 `FieldBase` 虽是第一张表的首项，却出现在第二张表的尾部，暂时不能选。选择 `NormalizeMixin` 后，也从以它开头的两张表同时移除，剩余为 `[FieldBase, object]`、`[FieldBase, object]` 和空表；于是依次选出 `FieldBase` 与 `object`。所以 `Report.__mro__` 是 `[Report, AuditMixin, NormalizeMixin, FieldBase, object]`。若某轮仍有剩余项却选不出合法候选，继承约束相互冲突，类定义会失败并抛出 `TypeError`。

所以本例的轨迹是 `Report.validate_title → AuditMixin.validate_title → NormalizeMixin.validate_title → FieldBase.validate_title`，`FieldBase` 是终点，不再向下委托。`AuditMixin` 里的 `super()` 从 `AuditMixin` 在 `Report` 实例 MRO 中的位置之后继续查找，所以到达的是 `NormalizeMixin`，而不是 `AuditMixin` 定义时写的父类 `FieldBase`。这要求每层 mixin 遵守共同约定：参数形式相互兼容，并在需要链条继续时调用 `super()`；任何一层漏掉这次调用，后面的步骤都会被跳过。

改变直接基类顺序会改变 MRO，也会改变同一套 `super()` 的执行顺序：

~~~python
print([cls.__name__ for cls in Report.__mro__])

class NormalizeFirst(NormalizeMixin, AuditMixin):
    pass

print([cls.__name__ for cls in NormalizeFirst.__mro__])
events.clear()
print(NormalizeFirst().validate_title("  November  "))
print(events)
~~~

`NormalizeFirst` 的 MRO 是 `[NormalizeFirst, NormalizeMixin, AuditMixin, FieldBase, object]`，同一输入仍规范化为 `November`，轨迹则变为 `NormalizeMixin.before → AuditMixin.before → FieldBase → AuditMixin.after → NormalizeMixin.after`。`NormalizeFirst` 只继承两个 mixin，没有 `Report.validate_title` 这一层，所以轨迹里也没有它；这段代码比较的是两个 mixin 的相对顺序。相对顺序随直接基类的声明顺序改变，而 `super()` 的规则本身不变。一个方法是否值得拆成多个 mixin 组合，要看这些步骤是否真的有可组合的共同约定；如果调用顺序很难讲清楚，改用显式组合对象，或直接按名字调用各个步骤，代码会更易读。

> [!info]- 来源
> - 描述符的定义、必须作为类属性才自动触发、`__set_name__`、实例读取优先级、函数绑定和 `super` 触发 descriptor binding：[Python 3.15.2 Descriptor Guide](https://docs.python.org/3.15/howto/descriptor.html)，Descriptor Protocol、Invocation from an Instance、Invocation from Super、Automatic Name Notification、Functions and Methods，核对于 2026-11-12。
> - 显式读取由 `__getattribute__` 处理；当它抛出 `AttributeError` 时外层 `__getattr__` 才回退，且 descriptor getter 的错误也可进入回退：[Python 3.15.2 Language Reference, Customizing Attribute Access](https://docs.python.org/3.15/reference/datamodel.html#customizing-attribute-access)，核对于 2026-11-12。
> - 类候选查找、默认实例属性查找：[Python 3.15.2 Language Reference, Custom Classes and Class Instances](https://docs.python.org/3.15/reference/datamodel.html#custom-classes)，核对于 2026-11-12。C3 线性化每轮选择候选首项并移除所有以它为首的列表项：[Python 3.15.2 MRO HOWTO](https://docs.python.org/3.15/howto/mro.html#the-c3-method-resolution-order)，核对于 2026-11-12。
> - 零参数 `super()` 从当前类之后沿实例类型的 MRO 查找；MRO 同时供 `getattr` 和 `super` 使用：[Python 3.15.2 Built-in Functions, `super`](https://docs.python.org/3.15/builtins/functions.html#super)，核对于 2026-11-12。
> - 固定实现 CPython 3.11.13 的数据描述符/实例字典/非数据描述符读取顺序与实例设置顺序：[Objects/object.c `_PyObject_GenericGetAttrWithDict` / `_PyObject_GenericSetAttrWithDict`](https://github.com/python/cpython/blob/v3.11.13/Objects/object.c#L1242-L1438)。默认设置路径见 [`_PyObject_GenericSetAttrWithDict`](https://github.com/python/cpython/blob/v3.11.13/Objects/object.c#L1390-L1425)。只实现 `__delete__` 的类候选也进入 descriptor setter 路径，缺少 `__set__` 时由描述符设置槽抛出错误：[Objects/typeobject.c `slot_tp_descr_set`](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L7822-L7839)。
> - 固定实现 CPython 3.11.13 的 `__getattribute__` / `__getattr__` 调度、`super_getattro` 的 MRO 后续查找、以及 C3 合并算法：[Objects/typeobject.c](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L7645-L7710)、[`super_getattro`](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L8812-L8883)、[`pmerge` / `mro_implementation`](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L1841-L2000)，本例在 CPython 3.11.13 重放。
