# Why does the Linux kernel embed list nodes in their objects? / Linux 内核为什么把链表节点嵌入对象？

**Short answer / 简答** — An intrusive list embeds its link hook in the object, so generic operations manipulate the hook rather than a separately allocated wrapper. Linux's `struct list_head` stores `next` and `prev` links in a circular doubly linked list whose sentinel points to itself when empty. / **侵入式链表 / intrusive linked list** 把链接钩子直接嵌在被链接的对象里。Linux 的 `struct list_head` 保存 `next` 和 `prev`；通用链表操作直接修改这些钩子，不需要为每个成员关系另分配包装节点。Linux 实现是带哨兵的循环双向链表：空表的 `list_head` 指向自身。

## Recover the containing object / 还原外层对象

`container_of(ptr, type, member)` 可从内嵌钩子指针还原外层对象。概念上，它从钩子地址减去成员相对结构体起点的字节偏移 `offsetof(type, member)`。因此链表操作只需认识通用钩子，调用方再还原具体对象类型。[Linux：Linked Lists in Linux](https://www.kernel.org/doc/html/latest/core-api/list.html)、[Linux `list.h`](https://github.com/torvalds/linux/blob/master/include/linux/list.h)。

Conceptually, `container_of` recovers the enclosing object by subtracting the hook member's `offsetof` byte offset from the hook's address. This makes the link operations generic, but the recovered objects can still form a dependent pointer chain.

## Link ownership and object lifetime / 链接归属与对象生命周期

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

## When does embedding help? / 何时适合把节点嵌入对象？

当已有对象需保持地址稳定、参与一种或多种频繁变化的关系，且减少每种关系额外包装节点有价值时，侵入式链表很实用。它提供通用链接操作，并通过多个钩子表示多个独立关系。但它**不会**让对象在物理内存中连续，也不会消除节点之间的指针依赖，因此不能解决内存墙。

也不要把非侵入式链表一概说成“对象再包一层指针并分配两次”。例如，`std::list<T>` 的容器元素本身就是 `T`；libstdc++ 的 `_List_node<T>` 将 `T` 放在节点内的对齐存储中，不是另分配一个用户对象再套包装节点，也不需要多追一次 `T*`。C++ 标准约束行为和复杂度，并不规定精确节点布局。[C++ 草案：`list`](https://eel.is/c++draft/list)、[GCC libstdc++ `stl_list.h`](https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/bits/stl_list.h)。

Embedding changes ownership and allocation. For traversal cost, see [memory hierarchy and data locality / 内存层次与数据局部性](memory-hierarchy-and-data-locality.md).
