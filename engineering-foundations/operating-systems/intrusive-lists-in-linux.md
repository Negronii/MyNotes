# Linux 内核为什么把链表节点嵌入对象？

假设内核要把一个 work item（工作项）放进待处理队列，同时还要把同一对象放进审计队列。Linux 内核的 `struct list_head` 是一对 `next`、`prev` 链接；把它作为成员嵌进工作项，就能让通用链表代码只修改链接，不必为每种关系再分配独立包装节点。

~~~mermaid
flowchart LR
    Ready["ready_head"] <-->|next / prev| ReadyA
    ReadyA["工作项 A.ready_link"] <-->|next / prev| ReadyB["工作项 B.ready_link"]
    ReadyB <-->|next / prev| Ready
    Audit["audit_head"] <-->|next / prev| AuditA["工作项 A.audit_link"]
    AuditA <-->|next / prev| Audit
    subgraph ItemA["同一个 work_item A"]
        ReadyA
        AuditA
        PayloadA["id 与工作数据"]
    end
~~~

`ready_link` 与 `audit_link` 是同一对象内的两个不同钩子，同一个钩子在同一时刻只能属于一张链表。图中的 head 也是 `struct list_head`，不是额外的业务对象；空表时它的 `next` 与 `prev` 都指向自身。

## container_of 怎样从钩子找到对象？

Linux 链表节点不是一个含 payload 指针的单独 wrapper。`struct list_head` 本身就放在被链接的结构体内；`container_of(ptr, type, member)` 根据成员偏移，概念上从钩子地址减去 `offsetof(type, member)`，还原出外层对象地址。`list_entry()` 建立在这一机制上，`list_for_each_entry()` 则直接让循环变量指向外层结构体。

~~~c
struct work_item {
    u64 id;
    struct list_head ready_link;
    struct list_head audit_link;
};

static LIST_HEAD(ready_items);

static void inspect_ready_items(void)
{
    struct work_item *item;

    list_for_each_entry(item, &ready_items, ready_link) {
        /* item 是外层 work_item，可读取 item->id。 */
    }
}
~~~

这要求传入的指针确实指向指定类型中的那个成员；成员名和外层类型必须匹配。`container_of` 做的是地址计算，不会寻找节点，也不消除遍历时读取 `next` 的依赖。对象插入链表后也不能随意移动或复制，否则链表中保存的钩子地址就不再指向有效成员。

上面的遍历片段只展示宏怎样把钩子还原成外层对象；它假设队列在遍历期间不会被并发修改，并且其中对象仍然存活。共享队列的锁定方式见下一个完整示例。

## 插入、遍历和摘除分别改变什么？

下面的内核风格代码让两个关系共用一个互斥锁。初始化发生在首次插入前；`list_add_tail` 把当前链接放在 head 之前，因此队列顺序与入队顺序一致。

~~~c
#include <linux/list.h>
#include <linux/mutex.h>
#include <linux/types.h>

struct work_item {
    u64 id;
    struct list_head ready_link;
    struct list_head audit_link;
};

static LIST_HEAD(ready_items);
static LIST_HEAD(audit_items);
static DEFINE_MUTEX(items_lock);

static void init_work_item(struct work_item *item)
{
    INIT_LIST_HEAD(&item->ready_link);
    INIT_LIST_HEAD(&item->audit_link);
}

static bool enqueue_ready(struct work_item *item)
{
    mutex_lock(&items_lock);
    /* 检查与插入共用一把锁，避免重复挂入同一钩子。 */
    if (!list_empty(&item->ready_link)) {
        mutex_unlock(&items_lock);
        return false;
    }
    list_add_tail(&item->ready_link, &ready_items);
    mutex_unlock(&items_lock);
    return true;
}

static bool record_for_audit(struct work_item *item)
{
    /* audit_link 独立于 ready_link，但同样只能加入一张表。 */
    mutex_lock(&items_lock);
    if (!list_empty(&item->audit_link)) {
        mutex_unlock(&items_lock);
        return false;
    }
    list_add_tail(&item->audit_link, &audit_items);
    mutex_unlock(&items_lock);
    return true;
}

static u64 sum_ready_ids(void)
{
    struct work_item *item;
    u64 total = 0;

    mutex_lock(&items_lock);
    list_for_each_entry(item, &ready_items, ready_link)
        total += item->id;
    mutex_unlock(&items_lock);
    return total;
}

static void clear_ready_links(void)
{
    struct work_item *item;
    struct work_item *next;

    mutex_lock(&items_lock);
    list_for_each_entry_safe(item, next, &ready_items, ready_link)
        list_del_init(&item->ready_link);
    mutex_unlock(&items_lock);
}
~~~

`list_add_tail` 和 `list_del_init` 只需改动固定数量的链接，链表长度不会增加这部分指针操作的数量。但这不是整个操作的耗时保证：调用者可能还要扫描查找节点、取得锁、等待缓存或管理对象本身。`list_del_init` 只把该钩子从队列摘下并重新初始化；它既不释放 `work_item`，也不会摘掉同一对象的 `audit_link`。

`list_for_each_entry_safe` 会在循环体删除当前节点前保存下一游标，因此适合“遍历时删除当前项”。这里的 safe 不提供多线程同步。上例用同一把锁保护所有读写；锁的类型与持有范围要符合调用上下文。互斥锁只适用于可以睡眠的上下文。

若 ready 队列依次含有 A.id=4、B.id=7，而 audit 队列含 A，`sum_ready_ids()` 返回 11。`clear_ready_links()` 后 ready 总和变为 0，但 A 仍在 audit 队列，不能释放 A。

## 对象生命周期和并发访问由谁负责？

嵌入链表不会自动管理外层对象的生命周期。释放对象前，需要摘掉所有仍挂入链表的钩子，并确认没有其他读者或引用者还会访问对象。一个工作项在待处理队列中已摘除、但仍留在审计队列时，仍然不能释放。

普通链表操作本身不负责并发安全。多个线程或 CPU 并发修改同一链表时通常要用合适的锁；只有读多写少、允许读者暂时看到已移除项且能延迟销毁时，才考虑 RCU（read-copy-update，读-复制-更新）。RCU 读者在 `rcu_read_lock()` 与 `rcu_read_unlock()` 之间使用 `list_for_each_entry_rcu()`；写者用 `list_add_rcu()` / `list_del_rcu()`，并仍须由写锁或既有协议串行化相互竞争的写操作。删除后等 grace period（宽限期）结束才能回收对象，例如由 `call_rcu()` 延后释放。RCU 是读侧和生命周期协议，不是把普通 `list_for_each_entry_safe` 换个名字。

## 内嵌节点什么时候划算？

当对象由当前模块拥有、地址在入链期间稳定、一个对象需要参加多种频繁更新的关系，且减少独立包装节点的分配和查找有实际价值时，侵入式链表很合适。每种同时存在的关系仍需一个钩子，每个 `list_head` 仍有两个指针；设计并没有消除链接存储成本。

它也不会把对象放到物理连续的内存中。相邻链表节点可能远隔内存，遍历时仍要先取当前节点的 next 指针，再按它到达下一处数据。应把它看作简化关系表示和已知节点更新的办法，不要把它当作解决缓存局部性的办法。主要操作是顺序扫描时，连续数组往往更合适，具体比较见[为什么连续扫描往往比链表遍历快？](memory-hierarchy-and-data-locality.md)。

这也不是说所有非侵入式列表都会“给业务对象再包一层指针并分配两次”。C++ 标准规定 `std::list` 的容器语义与操作复杂度，不规定具体节点布局；以 GCC libstdc++ 为例，内部节点把 T 放在节点自带的对齐存储中。那是一个实现样本，不是所有 `std::list` 实现的布局保证。

**相关机制：** [数据结构怎样匹配访问方式，复杂度界何时成立？](../algorithms/core-data-structures.md)说明已知节点与查找前驱的复杂度差别；[内存层次如何改变实际访问成本？](memory-hierarchy-and-data-locality.md)比较连续读取与逐节点指针依赖。

> [!info]- 来源
> - Linux 链表结构、初始化、插入、遍历、删除与删除时遍历：[Linux 内核 Linked Lists in Linux](https://docs.kernel.org/core-api/list.html)，2026-11-06 核对。
> - list_add_tail、list_del_init 与 list_for_each_entry_safe 的当前实现和注释：[Linux mainline include/linux/list.h](https://github.com/torvalds/linux/blob/master/include/linux/list.h)，2026-11-06 核对。
> - RCU 链表的读写侧协议与延后释放：[Linux 内核 Using RCU to Protect Read-Mostly Linked Lists](https://docs.kernel.org/RCU/listRCU.html)，2026-11-06 核对。
> - std::list 标准不规定节点内存布局：[C++ 草案 list](https://eel.is/c++draft/list)；对照实现样本：[GCC libstdc++ stl_list.h](https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/bits/stl_list.h)。
