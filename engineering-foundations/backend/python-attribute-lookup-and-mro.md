# Python 实例属性何时来自对象字典，何时变成描述符或绑定方法？

**案例：** 合成报表对象需要拒绝空标题；读者还要理解为什么直接往实例字典塞入同名键有时无效、有时能覆盖类属性。验证代码还组合了审计、规范化 mixin（混入类）与共同基类：调用 super() 时，问题不是“调用语法上写的父类”，而是“当前类 method resolution order（方法解析顺序，MRO）中的下一个实现”。

~~~mermaid
flowchart TD
    Get[读取 obj.name] --> MRO["在 type(obj) 的 MRO 找类属性"]
    MRO -->|找到候选| Data{候选是带 __get__ 的数据描述符?}
    MRO -->|没有候选| Dict
    Data -->|是| DGet[调用 descriptor.__get__]
    DGet -->|返回值| Result[返回值]
    DGet -->|抛 AttributeError| Hook{定义了 __getattr__?}
    Data -->|否| Dict{obj.__dict__ 有 name?}
    Dict -->|有| Instance[返回实例值]
    Instance --> Result
    Dict -->|没有，MRO 有类候选| Getter{候选有 __get__?}
    Dict -->|没有，MRO 无类候选| Hook{定义了 __getattr__?}
    Getter -->|是| CallGet[调用 descriptor.__get__]
    Getter -->|否| ClassValue[返回 MRO 中的类候选值]
    CallGet -->|返回值，函数会绑定实例| Result
    CallGet -->|抛 AttributeError| Hook
    ClassValue --> Result
    Hook -->|是| Fallback[调用 __getattr__]
    Hook -->|否| Raise[向调用方抛 AttributeError]
    Fallback --> Result
~~~

图按默认实例查找说明路径：若默认查找（包括实例字典）仍未找到属性，或候选描述符的 `__get__` 抛出 AttributeError，默认 `__getattribute__` 会抛 AttributeError；普通点号访问随后会调用类定义的 `__getattr__`，若没有该方法则把 AttributeError 交给调用方。实际项目若覆写 `__getattribute__`、使用特殊代理或 class/metaclass 属性访问，行为还会增加一层。本章只解释普通实例的属性读取和协作式多继承。

## 同名实例值为什么压不过一个字段验证器？

descriptor（描述符）是定义了 `__get__`、`__set__` 或 `__delete__` 的对象。描述符必须放在类属性上才参与点号访问。定义 `__set__` 或 `__delete__` 会让它成为 data descriptor（数据描述符）；本节的描述符还定义 `__get__`，因此读取时优先于实例字典。只有 `__get__` 的则是 non-data descriptor（非数据描述符），实例值可以把它盖住。

下面用一个数据描述符检查报表标题。`__set_name__` 在类创建时取得属性名；验证后的值存在实例字典的另一个键中，避免描述符递归调用自己。

~~~python
class NonEmptyText:
    def __set_name__(self, owner, name):
        self.storage_name = "_" + name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.__dict__.get(self.storage_name)

    def __set__(self, instance, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("title must contain non-whitespace text")
        instance.__dict__[self.storage_name] = value.strip()


class Report:
    title = NonEmptyText()

    def __init__(self, title):
        self.title = title

    def publish(self):
        return "published: " + self.title


report = Report("  Monthly summary  ")
print(report.title)
report.__dict__["title"] = "forged instance value"
print(report.title)
try:
    report.title = "   "
except ValueError as error:
    print(type(error).__name__, str(error))
~~~

CPython 3.11.13 的输出是：

~~~text
Monthly summary
Monthly summary
ValueError title must contain non-whitespace text
~~~

实例字典此时有 _title 和 title 两个键，但读取 report.title 会先找到类上的 NonEmptyText，再调用它的 `__get__`；名为 title 的字典值不会胜出。赋值 report.title=... 同样先调用 `__set__`，因此验证器能规范化有效输入并拒绝空白输入。这个写法适合字段校验、延迟加载或受控计算；要小心避免描述符内部写回自身管理的同名属性。

## 为什么方法会绑定 self，又为什么实例能临时覆盖？

类中定义的普通函数也是非数据描述符。读取 report.publish 时，函数的 `__get__` 将它绑定成方法对象，方法的 `__self__` 指向 report；调用 report.publish() 等价于把该实例作为第一个参数传入函数。

~~~python
bound = report.publish
print(bound.__self__ is report)
print(bound())
report.__dict__["publish"] = "temporary label"
print(report.publish)
~~~

输出依次是 True、published: Monthly summary 和 temporary label。函数属于非数据描述符，因此实例字典的 publish 值优先。类上的函数才会发生这种绑定；若把一个普通函数直接放进实例字典，它不会自动转成绑定方法。这个区别解释了测试中为何给一个实例临时赋值可以替换方法，以及为什么这类 monkey patch（运行时替换）只影响该实例。

普通属性查找可以用优先级表概括：

| 查找结果 | 实例字典有同名键 | 读取结果 |
| --- | --- | --- |
| 带 `__get__` 的数据描述符，例如 NonEmptyText | 有或没有 | 描述符的 `__get__` 结果 |
| 无类候选，或候选不是带 `__get__` 的数据描述符 | 有 | 实例字典中的值 |
| 有 `__get__` 的非数据描述符，例如方法函数 | 没有 | 调用 `__get__`；普通函数会绑定实例 |
| 没有 `__get__` 的类候选，例如普通值或只有 `__set__` 的描述符 | 没有 | 返回 MRO 中的类候选值/描述符对象 |
| 无类候选 | 没有 | 调用 `__getattr__`；若没有则抛 AttributeError |

如果默认查找未找到属性，或描述符的 `__get__` 抛出 AttributeError，点号访问还会调用类定义的 `__getattr__`；若没有这个方法，AttributeError 会传给调用方。只有定义 `__set__` 或 `__delete__` 的对象属于数据描述符；但只有同时有 `__get__` 时，它才会在读取时按数据描述符路径优先于实例字典。类属性查找、元类上的描述符与自定义 `__getattribute__` 的细节不在这张实例查找表内。

## 菱形继承中 super() 到底走向哪里？

假设标题检查接收字符串并由多个可组合的验证步骤构成：审计 mixin 记录验证执行顺序，规范化 mixin 去除首尾空格，共同基类作最终非空验证。两种 mixin 都继承 FieldBase，形成一个菱形：

~~~python
events = []


class FieldBase:
    def validate(self, value):
        events.append("FieldBase")
        if not value:
            raise ValueError("empty title")
        return value


class NormalizeMixin(FieldBase):
    def validate(self, value):
        events.append("NormalizeMixin.before")
        result = super().validate(value.strip())
        events.append("NormalizeMixin.after")
        return result


class AuditMixin(FieldBase):
    def validate(self, value):
        events.append("AuditMixin.before")
        result = super().validate(value)
        events.append("AuditMixin.after")
        return result


class MonthlyTitleField(AuditMixin, NormalizeMixin):
    def validate(self, value):
        events.append("MonthlyTitleField")
        return super().validate(value)


field = MonthlyTitleField()
result = field.validate("  Monthly summary  ")
print([cls.__name__ for cls in MonthlyTitleField.__mro__])
print(result)
for event in events:
    print(event)
~~~

运行输出：

~~~text
['MonthlyTitleField', 'AuditMixin', 'NormalizeMixin', 'FieldBase', 'object']
Monthly summary
MonthlyTitleField
AuditMixin.before
NormalizeMixin.before
FieldBase
NormalizeMixin.after
AuditMixin.after
~~~

C3 线性化算法的约束是保留每个父类自身的顺序，同时保留子类声明的直接父类顺序。可手推为：

~~~text
L(AuditMixin)        = [AuditMixin, FieldBase, object]
L(NormalizeMixin)    = [NormalizeMixin, FieldBase, object]
L(MonthlyTitleField) = [MonthlyTitleField] + merge(
    [AuditMixin, FieldBase, object],
    [NormalizeMixin, FieldBase, object],
    [AuditMixin, NormalizeMixin]
)
~~~

merge 每轮从输入列表左到右扫描，取第一个不在任何列表尾部中的首项；“尾部”指每个列表去掉首项后的剩余元素。取出的首项从它所在的各个列表中移除。先取 AuditMixin：它是第一条列表和直接父类顺序列表的首项，且不在任何列表尾部。移除后，第一条列表的首项 FieldBase 出现在第二条列表的尾部 `[FieldBase, object]`，所以暂不能取；接着选中第二条列表和直接父类列表的首项 NormalizeMixin。随后依次取 FieldBase、object。于是 MRO 是 MonthlyTitleField → AuditMixin → NormalizeMixin → FieldBase → object。

所以 MonthlyTitleField 内的 super() 找到 AuditMixin；AuditMixin 内的 super() 仍从实例真实类型 MonthlyTitleField 的 MRO 继续，下一站是 NormalizeMixin，而不是 AuditMixin 在定义时写出的直接基类 FieldBase。NormalizeMixin 再交给 FieldBase，基类只执行一次。依本例输入，执行序列为包装层、审计前置、规范化前置、基础检查、规范化收尾、审计收尾。

协作式 mixin 的每个实现都要遵守共同约定：接受兼容的参数，并在恰当位置调用 super()。若某个 mixin 直接返回而不继续调用，后续步骤会被截断；若不同实现对同名方法的参数约定不兼容，也无法可靠地串起来。多继承适用于确实需要按 MRO 组合的横切行为；若顺序与协作约定难以说清，组合对象或显式调用步骤通常更容易维护。

如果要继续看对象名称绑定、可变性、迭代器和资源生命周期，见[Python 的值、迭代器与资源生命周期如何工作？](python-fundamentals.md)。

> [!info]- 来源
> - 描述符类型、实例属性和类属性的读取优先级、函数方法绑定及 C3 MRO：[Python 3.11 Language Reference, Data Model](https://docs.python.org/3.11/reference/datamodel.html)，§3.3.2.3、§3.2.8.2，核对于 2026-11-09。
> - 描述符仅通过类属性触发、`__set_name__` 的用途：[Python 3.11 Descriptor HowTo Guide](https://docs.python.org/3.11/howto/descriptor.html)，Descriptor Protocol，核对于 2026-11-09。
> - 示例中的实例字典、描述符遮蔽与 MRO 调用次序已在 CPython 3.11.13 实跑；这里只检查普通实例属性，不声称覆盖自定义元类或 `__getattribute__`。
