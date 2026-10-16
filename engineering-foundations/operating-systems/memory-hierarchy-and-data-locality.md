# Memory Hierarchy and Data Locality / 内存层次与数据局部性

Big-O describes how work grows, but data layout and dependency determine how quickly a processor can obtain that work. A contiguous scan often runs efficiently because its addresses are predictable and independent loads can overlap; a linked-list walk has a dependent pointer chain, but a cache miss does not automatically stop every part of the CPU.

复杂度描述工作量如何随输入增长，数据布局与依赖关系则影响处理器能多快拿到数据。连续扫描通常更容易利用预取、并行访存和 SIMD；链表遍历受逐节点地址依赖限制，但一次 Cache Miss 不等于整个 CPU 必然停摆。

## Key terms / 核心术语

| Term | Meaning |
|---|---|
| **Memory wall / 内存墙** | 处理器计算能力与内存供数能力之间逐渐拉大的差距，涉及延迟与带宽；它不是固定耗时，也不表示所有程序都受内存限制。 |
| **Latency / 延迟** | 从发出一次内存请求到数据可供使用所需的时间。 |
| **Bandwidth / 带宽** | 多个请求充分重叠时，单位时间能传输的数据量。 |
| **Cache line / 缓存行** | 缓存常用的数据传输与一致性维护粒度；具体大小依处理器而定。 |
| **Spatial locality / 空间局部性** | 访问靠近刚访问过地址的数据。一次缓存填充可能带入扫描很快会用到的相邻值。 |
| **Temporal locality / 时间局部性** | 短时间内重复使用同一数据，使它更可能仍留在缓存中。 |
| **Memory-level parallelism (MLP) / 内存级并行度** | 同时处于未完成状态的独立内存请求数量。 |

Wulf 与 McKee 用“内存墙”描述处理器与内存性能差距的扩大。Intel 优化手册提出的实践方向是让访问尽量命中缓存，或隐藏足够多的延迟以利用内存带宽。两者相关但不同：**延迟**限制一条有依赖的访问链；**带宽**限制整体数据吞吐。 [Wulf 与 McKee（1995）](https://doi.org/10.1145/216585.216588)，[Intel® 64 和 IA-32 优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html)。

若一次流式循环平均为每项从内存传输 `s` 字节，可分配给它的有效带宽为 `B`，且循环已受带宽限制，则吞吐上限约为 `B / s` 项每秒。指针依赖链受另一种约束：当前节点到达后才能得知下一地址，因此单条遍历通常无法暴露同等数量的独立请求。这些关系用于识别瓶颈，不是精确耗时公式；缓存命中、计算量、其他请求和具体处理器都会改变结果。

## Why contiguous scans often work well / 连续扫描为什么常常高效

对连续数组区域，下一元素地址可由基址和下标计算。硬件预取器能识别许多规则访问模式；早先的读取尚未完成时，处理器也可能继续发出后续迭代中彼此独立的读取。如果操作、数据类型和编译条件合适，编译器还可用 SIMD 指令并行处理多个值。这些收益都有条件：步长不规则、分支多、指针别名难以排除、指令级并行度不足，或内存带宽已饱和时，预取和向量化都可能帮助有限。[Intel 优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html)、[Arm Cortex-A 系列程序员指南](https://documentation-service.arm.com/static/6893ad23e7f7ce6150e88d37)。

链表遍历要先读取当前节点，再从中得到下一节点地址（`node = node->next`）。在当前节点的链接到达之前，处理器通常不知道下一请求发往哪里。这种**指针追逐 / pointer chasing**形成依赖链，常限制单条遍历可利用的 MLP。普通流式预取器较难从中识别规律；特定设计也可能使用软件预取或专用硬件改善访问。

Cache Miss 仍可与独立工作重叠：支持乱序执行的核心可能先执行无关指令，其他独立读取或线程也可能已有请求在途。当缺失数据位于关键依赖路径上，且没有有用的独立工作可继续时，核心才会因等待而停顿。因此，长串依赖未命中会让链表遍历很慢，但不能推断每次 Miss 都冻结全部执行。Linux 官方文档也提醒，链表局部性较差；若简单数组已能满足需求，链表很少是更好的选择。[Linux：Linked Lists in Linux](https://www.kernel.org/doc/html/latest/core-api/list.html)。

## Complexity is not elapsed time / 复杂度不等于实际耗时

链表插入或删除只有在**已知相关节点或链接**时才是 O(1)。双向链表持有目标节点即可改动有限个指针；单向链表删除目标节点需要前驱，按位置插到某节点之前也需要前驱（除非表示方式另行提供）。按值或下标查找仍是 O(n)。创建节点还会经过分配器并产生内存流量，而复杂度表通常没有计入这些分配与缓存成本。

数组中间插入需要 O(n) 次元素移动，但移动范围连续规则；对适合的类型还可用优化过的批量操作。它是否快于分配链表节点并改写链接，取决于元素大小、移动成本、是否已知链表位置、分配器、数据是否在缓存中以及操作比例。因此，“链表 O(1) 插入总比数组 O(n) 插入快”不能作为普遍结论。

对象池可降低分配开销，也可能让对象更集中，但它不保证链接顺序与内存地址顺序一致。对象复用、插入顺序和池的设计共同决定实际遍历布局。

## Arrays in C, C++, and JavaScript / 各语言中的数组布局

在 C 中，普通数组的元素连续存储，多维数组按行优先布局（最后一维变化最快）；C++ `std::vector<T>`（专门化的 `vector<bool>` 除外）也保证连续存储。JavaScript `Array` 则由带特殊 `length` 行为的索引属性定义；语言规范不保证它采用同样的 C 式元素布局。引擎可以优化常见的稠密数组，具体表示因实现而异。以 V8 为例，它区分 packed 与 holey 等元素类型。[WG14 C23 草案](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3047.pdf)

JavaScript `TypedArray` 更接近数值数据布局：它以固定元素类型，在二进制数据缓冲区上提供数组式视图。但它仍由运行时管理；不能从 C 数组推断普通 JavaScript `Array` 的机器布局或优化方式。[C++ 草案：`vector`](https://eel.is/c++draft/vector)、[ECMAScript 2024：Indexed Collections](https://tc39.es/ecma262/2024/multipage/indexed-collections.html)、[V8：Elements kinds](https://v8.dev/blog/elements-kinds)。

## Intrusive lists in the Linux kernel / Linux 内核中的侵入式链表

**侵入式链表 / intrusive linked list** 把链接钩子直接嵌在被链接的对象里。Linux 的 `struct list_head` 保存 `next` 和 `prev`；通用链表操作直接修改这些钩子，不需要为每个成员关系另分配包装节点。Linux 实现是带哨兵的循环双向链表：空表的 `list_head` 指向自身。

An intrusive list embeds its link hook in the object, so generic operations manipulate the hook rather than a separately allocated wrapper. Linux's `struct list_head` stores `next` and `prev` links in a circular doubly linked list whose sentinel points to itself when empty.

`container_of(ptr, type, member)` 可从内嵌钩子指针还原外层对象。概念上，它从钩子地址减去成员相对结构体起点的字节偏移 `offsetof(type, member)`。因此链表操作只需认识通用钩子，调用方再还原具体对象类型。[Linux：Linked Lists in Linux](https://www.kernel.org/doc/html/latest/core-api/list.html)、[Linux `list.h`](https://github.com/torvalds/linux/blob/master/include/linux/list.h)。

Conceptually, `container_of` recovers the enclosing object by subtracting the hook member's `offsetof` byte offset from the hook's address. This makes the link operations generic, but the recovered objects can still form a dependent pointer chain.

```c
#include <linux/list.h>
#include <linux/mutex.h>

struct job {
    unsigned long id;
    struct list_head ready_link;
    struct list_head audit_link;
};

static LIST_HEAD(ready_jobs);
static DEFINE_MUTEX(ready_jobs_lock);

/* Initialize both hooks before first insertion. */
static void init_job_links(struct job *job)
{
    INIT_LIST_HEAD(&job->ready_link);
    INIT_LIST_HEAD(&job->audit_link);
}

/* Caller owns job and ensures it is not already on ready_jobs. */
static void enqueue_job(struct job *job)
{
    mutex_lock(&ready_jobs_lock);
    list_add_tail(&job->ready_link, &ready_jobs);
    mutex_unlock(&ready_jobs_lock);
}

/* This iteration uses the same lock as every writer. */
static void inspect_jobs(void)
{
    struct job *job;

    mutex_lock(&ready_jobs_lock);
    list_for_each_entry(job, &ready_jobs, ready_link) {
        /* Use job->id. */
    }
    mutex_unlock(&ready_jobs_lock);
}

/* job must currently be linked; unlinking does not free it. */
static void dequeue_job(struct job *job)
{
    mutex_lock(&ready_jobs_lock);
    list_del_init(&job->ready_link);
    mutex_unlock(&ready_jobs_lock);
}
```

这段是 Linux 内核风格代码，不是可直接用于普通用户态的可移植 C。示例假定处于允许休眠的上下文，且所有访问 `ready_jobs` 的读者和写者都遵循同一互斥锁。一个钩子同一时刻只能挂入一张链表；`ready_link` 和 `audit_link` 是两种独立关系。摘除 `ready_link` 不会释放 `job`；释放对象前还要摘除其他有效钩子，并确保没有引用者或读者继续使用它。Linux 的 `list_for_each_entry_safe` 会预存下一游标，支持遍历时删除当前项；这里的“safe”不提供并发保护。并发访问通常需要锁；读多写少时可使用遵循正确生命周期与宽限期协议的 RCU 链表接口。[Linux 链表文档：删除与并发](https://www.kernel.org/doc/html/latest/core-api/list.html)。

当已有对象需保持地址稳定、参与一种或多种频繁变化的关系，且减少每种关系额外包装节点有价值时，侵入式链表很实用。它提供通用链接操作，并通过多个钩子表示多个独立关系。但它**不会**让对象在物理内存中连续，也不会消除节点之间的指针依赖，因此不能解决内存墙。

也不要把非侵入式链表一概说成“对象再包一层指针并分配两次”。例如，`std::list<T>` 的容器元素本身就是 `T`；libstdc++ 的 `_List_node<T>` 将 `T` 放在节点内的对齐存储中，不是另分配一个用户对象再套包装节点，也不需要多追一次 `T*`。C++ 标准约束行为和复杂度，并不规定精确节点布局。[C++ 草案：`list`](https://eel.is/c++draft/list)、[GCC libstdc++ `stl_list.h`](https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/bits/stl_list.h)。

## Related performance surprises / 相关的性能反直觉现象

| 场景 | 机制与适用条件；可继续追问 |
|---|---|
| 小规模线性查找与二分 | 小型连续范围可简单顺序扫描；二分比较次数渐进更少，却跳跃访问不同位置。交叉点取决于数据规模、比较成本与缓存状态。实际输入规模和键分布是什么？ |
| 行遍历与列遍历 | 行优先布局中，遍历末维是连续访问；按列走会跨距访问。规则取决于语言及实际布局。循环顺序是否符合存储顺序？ |
| 伪共享 / False sharing | 不同 CPU 写同一一致性缓存行中的不同变量，也会让对方缓存副本失效。需要并发共享且至少一方写入；只有读取不构成此问题。能否用 `perf c2c` 找出争用缓存行？[Linux 伪共享指南](https://docs.kernel.org/kernel-hacking/false-sharing.html) |
| B+ 树与红黑树 | 面向页的 B+ 树在每页容纳多个分隔键，并通过叶页链接支持范围扫描；指针式红黑树通常每节点组织一个键。取舍取决于主要成本是存储页读取、内存缓存未命中还是更新。哪层存储与查询模式主导？[PostgreSQL B-tree 实现](https://www.postgresql.org/docs/current/btree.html) |
| 无分支与分支预测代码 | 去掉分支可能避开误预测，但也可能执行更多工作或引入数据依赖；预测稳定的分支反而更便宜。实际输入分布和生成指令是什么？ |
| 扁平与节点式哈希表 | 扁平表可把元数据与条目密集组织以便分组探测；节点式表更容易保持元素地址稳定，但常增加指针追逐。删除、扩容、负载因子和引用稳定性都重要。[Abseil Swiss Tables 设计](https://abseil.io/about/design/swisstables) |
| 结构体填充 | 对齐要求会插入填充字节并增大对象；字段顺序也可能影响空间，仍受 ABI 与访问模式约束。`sizeof` 与成员偏移是否显示出实际空间问题？ |
| 增加核心数 | 独立工作可扩展，直到共享内存带宽、一致性流量或同步争用成为瓶颈。增加核心后，负载是计算受限、带宽受限还是争用受限？[Intel 优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html)、[Linux 伪共享指南](https://docs.kernel.org/kernel-hacking/false-sharing.html) |

**Related notes / 相关笔记：** [Core Data Structures](../algorithms/core-data-structures.md) explains tree structure and list-operation bounds; [Practical Data Structure Implementations](../algorithms/practical-data-structure-implementations.md) shows an LRU cache locating a list node through a map before moving that known node.

## Sources / 来源

来源核实日期：**2026-10-16**。处理器手册描述特定架构与实现，不代表所有 CPU 都有相同缓存层次、预取行为、缓存行大小或内存级并行度。

- [Wulf 与 McKee，“Hitting the Memory Wall: Implications of the Obvious”（1995）](https://doi.org/10.1145/216585.216588) — 内存墙术语的提出背景与论述。
- [Intel® 64 和 IA-32 架构优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html) — 隐藏延迟、内存带宽、规则预取模式及特定架构优化。
- [Arm Cortex-A 系列程序员指南，Armv7-A](https://documentation-service.arm.com/static/6893ad23e7f7ce6150e88d37) — 缓存延迟隐藏、hit-under-miss 与乱序执行示例；内容特定于处理器系列，不是所有 Arm 实现的保证。
- [Linux 内核：Linked Lists in Linux](https://www.kernel.org/doc/html/latest/core-api/list.html) 与 [`include/linux/list.h`](https://github.com/torvalds/linux/blob/master/include/linux/list.h) — 循环双向结构、内嵌钩子、`container_of`、删除、安全遍历与并发说明。
- [Linux 内核：False Sharing](https://docs.kernel.org/kernel-hacking/false-sharing.html) — 一致性缓存行机制、成立条件与诊断方法。
- [C++ 草案：`vector`](https://eel.is/c++draft/vector) 和 [`list`](https://eel.is/c++draft/list) — 标准容器保证，以及哪些实现细节不能从标准推断。
- [WG14 C23 草案 N3047](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3047.pdf) — C 数组元素布局与多维数组行优先顺序。
- [GCC libstdc++ `stl_list.h`](https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/bits/stl_list.h) — 一个标准库实现中，链表节点将 `T` 存在自身节点内的对齐存储。
- [ECMAScript 2024：Indexed Collections](https://tc39.es/ecma262/2024/multipage/indexed-collections.html) 与 [V8：Elements kinds](https://v8.dev/blog/elements-kinds) — JavaScript Array 语义、TypedArray 数据缓冲视图，以及一种引擎的实现选择。
- [PostgreSQL：B-tree 索引](https://www.postgresql.org/docs/current/btree.html) 与 [Abseil：Swiss Tables](https://abseil.io/about/design/swisstables) — 页式树与密集哈希元数据的实际例子。
