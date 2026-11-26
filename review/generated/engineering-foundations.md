# Engineering Foundations

> 本卷由[领域地图](../../engineering-foundations/index.md)及其中的 Markdown 正文生成。卷内链接按 Obsidian 标题跳转。修订内容请到对应的章节原文。

可从各分部首章开始阅读。

- [数据怎样表示，算法怎样利用顺序和状态，成本落在哪里？](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)
- [程序在一台机器上怎样并发、等待和释放资源？](#14.%20%E4%B8%80%E4%BB%BD%E5%B7%A5%E4%BD%9C%E8%AF%A5%E4%BA%A4%E7%BB%99%E8%BF%9B%E7%A8%8B%E3%80%81%E7%BA%BF%E7%A8%8B%E8%BF%98%E6%98%AF%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)
- [数据怎样存得对、读得快？](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)
- [服务之间怎样交换请求，并在失败和过载下保持正确？](#33.%20%E4%B8%80%E6%AC%A1%20HTTP%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%B5%8F%E8%A7%88%E5%99%A8%E5%88%B0%E8%BE%BE%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%8F%88%E5%B8%A6%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)
- [一次改动怎样从设计走到生产，并用证据说明它是对的？](#49.%20%E6%80%8E%E6%A0%B7%E5%88%A4%E6%96%AD%E4%B8%80%E4%B8%AA%E6%8A%BD%E8%B1%A1%E5%80%BC%E4%B8%8D%E5%80%BC%E5%BE%97%E5%BC%95%E5%85%A5%EF%BC%9F)

## 1. 选算法时，复杂度结论在什么条件下才成立？

一个复杂度结论只在两件事都写清楚时才成立：算法依赖的输入保证（例如“已按某个键排序”），以及计数用的成本模型（数什么操作、算最坏还是平均、哪些成本没算进去）。本章用一页有序事件说明怎样从输入保证走到选型，并统一主线一各章共用的成本口径。读者只需要会读循环和基本的 Big-O 记号。

### 案例：报表 42 的事件页

主线一的各章以一家 SaaS 的账户报表服务为背景。账户 `acct-17` 的用户 `user-17` 打开报表 42（标题 `Service health`），服务已从数据库取回这份报表的一页事件，共 1,024 条，放在内存数组里，按复合键 `(occurred_at, event_id)` 升序排列：先比发生时间，时间相同再比事件 ID。时间是同精度的 UTC ISO 8601 字符串（如 `2026-11-12T09:02:00.000Z`），事件 ID 定宽（如 `e03`）。

接口现在要回答一个问题：给定一个位置 `(09:02, e08)`，它在这一页里应排在第几条？为了能逐步看清，下文取出其中四条演示记录：

| 下标 | `occurred_at` | `event_id` |
|---:|---|---|
| 0 | 09:00 | `e07` |
| 1 | 09:02 | `e03` |
| 2 | 09:02 | `e11` |
| 3 | 09:05 | `e18` |

答案是下标 2：`(09:02, e08)` 排在 `(09:02, e03)` 之后、`(09:02, e11)` 之前。求这个位置的操作叫 `lower_bound`，它返回第一个不小于目标的键的下标。它的区间约定和逐步推导在[有序数据怎样让二分查找和双指针安全排除候选？](#7.%20%E6%9C%89%E5%BA%8F%E6%95%B0%E6%8D%AE%E6%80%8E%E6%A0%B7%E8%AE%A9%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%E5%AE%89%E5%85%A8%E6%8E%92%E9%99%A4%E5%80%99%E9%80%89%EF%BC%9F)，本章只用它的结果和探测次数。

本主线的案例标识符：

| 标识符 | 含义 |
|---|---|
| `acct-17`、`user-17`、报表 42（`Service health`） | 账户、主体、报表；工程基础各主线共用 |
| 1,024 条事件；`e07`/`e03`/`e11`/`e18`；目标 `(09:02, e08)` | 报表 42 的事件页，按 `(occurred_at, event_id)` 升序 |

有序查找一章沿用这个案例，数据结构一章借用这四条记录对比三种布局；其余各章换成更贴合各自机制的小例子。

### 选型从输入保证开始，而不是从题型开始

选一个算法，按下面的顺序回答五个问题：

1. **输入有什么保证、规模多大？** 本例：1,024 条，已按 `(occurred_at, event_id)` 升序，键唯一。
2. **要执行什么操作？** 本例：找一个位置，而不是判断某条记录是否存在，也不是重新排序。
3. **哪个方法能利用这项保证？** 有序让二分查找每次比较都能排除一半候选。
4. **代价是多少？** 时间、额外空间、分配和复制，按写明的成本模型计（见下文“成本口径”）。
5. **用边界输入复算。** 空页、目标比所有键都小或都大、目标恰好等于某个键、时间相同的多条记录。

第三步是核心：每一种高效方法都在消费一项输入保证，这项保证在算法里表现为一个 invariant (不变量)，即每一轮都保持为真的条件。有序数组上，每次中点比较能排除一半范围；动态规划靠子问题重叠，算过的状态直接复用；队列用一个头下标出队，不必搬移其余元素。缺了对应的保证，复杂度表里的数字就不适用：无序数组没有有意义的插入位置，只能线性扫描，或者先按同一比较规则排序，并把排序成本算进去。

保证还必须和比较规则逐字对应：

- **复合键有序不等于子字段有序。** 这一页按“时间加 ID”排序，`e03` 的时间晚于 `e07`，ID 却更小；只知道 `event_id` 时不能在这个数组上二分。按 ID 精确查找要另建索引，见[数组、链表、树和哈希表各靠什么找到目标、维护顺序？](#2.%20%E6%95%B0%E7%BB%84%E3%80%81%E9%93%BE%E8%A1%A8%E3%80%81%E6%A0%91%E5%92%8C%E5%93%88%E5%B8%8C%E8%A1%A8%E5%90%84%E9%9D%A0%E4%BB%80%E4%B9%88%E6%89%BE%E5%88%B0%E7%9B%AE%E6%A0%87%E3%80%81%E7%BB%B4%E6%8A%A4%E9%A1%BA%E5%BA%8F%EF%BC%9F)。
- **只比一部分字段会丢失位置。** 若比较器只看时间戳，`e03`、`e08`、`e11` 被视为相等，`lower_bound` 会返回 1（`e03` 之前），而不是正确的 2。
- **字符串比较能代替时间比较，靠的是格式保证。** 同精度的 UTC ISO 8601 字符串按字典序比较，结果与时间先后一致；定宽 ID 让 `e03 < e11` 的字典序与数值序一致。若 ID 不定宽，`"e11" < "e3"`，字典序就与数值序相反。排序规则、键字段或空值位置一旦改变，数据的排序和查找用的比较器必须一起改。

### Big-O 数的是什么

Big-O notation (大 O 记号) 描述输入规模增大时，某个成本单位的操作次数或额外空间的渐近上界，省略常数因子和低阶项。它本身不说明数的是哪种操作，所以每个结论都要先选定成本单位和参数：

- **成本单位。** 本例数“探测次数”，即读取一个数组元素并与目标比较一次。复合键比较器内部还会比较一到两个字段；若要数字段比较，就要另算。
- **规模参数。** `n` 是元素个数。默认一次键比较、一次整数加法是常数时间；若字符串长度、任意精度整数的位数或记录字段数随输入增长，就要把它们另列为参数（如字符串长度 `m`、位数 `b`）。本例的时间戳和 ID 都定长，所以一次比较可视为常数。
- **数值参数不是位数。** 0/1 背包的动态规划时间是 O(nW)，`W` 是容量的数值；而写下 `W` 只需约 log₂ W 位，所以 O(nW) 对输入长度来说是指数级的，称为伪多项式时间，见[动态规划怎样定义状态并安排更新顺序？](#12.%20%E5%8A%A8%E6%80%81%E8%A7%84%E5%88%92%E6%80%8E%E6%A0%B7%E5%AE%9A%E4%B9%89%E7%8A%B6%E6%80%81%E5%B9%B6%E5%AE%89%E6%8E%92%E6%9B%B4%E6%96%B0%E9%A1%BA%E5%BA%8F%EF%BC%9F)。

常见增长量各有成立条件：

| 增长量 | 典型例子 | 成立条件 |
|---|---|---|
| O(1) | 数组下标访问 | 下标已知且合法；按值查找不是常数时间 |
| 期望 O(1) | 哈希表查找 | 负载因子受控、哈希值分布良好；是期望界，不是最坏界 |
| O(log n) | 有序数组二分、平衡搜索树 | 数据按同一比较规则有序，或树高受不变量约束 |
| O(n) | 顺序扫描 | 每个元素检查常数次 |
| O(n log n) | 归并排序、堆排序；划分大致均衡的快速排序 | 快速排序划分偏斜时最坏 O(n²) |
| O(n²) | 两层全量扫描、插入排序 | 两层循环都随 n 线性增长 |
| O(2ⁿ) | 枚举全部子集、朴素递归 Fibonacci 的上界 | 按候选或搜索树节点计，每个节点常数工作 |
| O(n!) | 枚举全部排列 | 同上 |

最后两行只计搜索本身。如果还要把每个候选复制出来输出，输出成本另算：n 个元素的全部子集共含 n·2ⁿ⁻¹ 个元素（每个元素出现在一半子集里），全部排列共含 n·n! 个元素。

> [!example] 1,024 条事件：线性扫描 1,024 次，lower_bound 11 次
> 线性扫描找插入位置，最坏要把 1,024 条全部比较一遍，共 1,024 次探测。`lower_bound` 每次探测后，待查的元素至多剩下一半（向下取整），最坏路径是 1,024 → 512 → 256 → 128 → 64 → 32 → 16 → 8 → 4 → 2 → 1 → 0，共 11 次探测。例如目标小于所有键时，依次探测下标 512、256、128、64、32、16、8、4、2、1、0。一般地，n 个元素最多探测 ⌊log₂ n⌋ + 1 次。
>
> 按字段数，每次探测比较一到两个字段（时间不等时只比时间），所以 11 次探测至多 22 次字段比较。前提是页已按同一复合键排好序；若数据无序，只能线性扫描，或先排序再查，并把 O(n log n) 的排序成本计入。

### 成本口径：最坏、期望、均摊，规范保证与实现模型

主线一各章的复杂度都按本节的口径计，后续章节不再逐处声明。

#### 三种界各承诺什么

| 界 | 承诺 | 例子 | 什么时候不够 |
|---|---|---|---|
| worst case (最坏情况) | 任何输入、任何一次操作都不超过 | 平衡树的查找 O(log n) | — |
| expected (期望) | 在输入分布或随机选择的假设下平均不超过 | 哈希表查找期望 O(1)；随机选基准的快速排序期望 O(n log n) | 哈希分布差、对手构造输入时，单次可退化 |
| amortized (均摊) | 一串操作的总成本不超过上界，平均摊到每次 | 动态数组追加均摊 O(1) | 单次延迟有上限要求时，个别操作可达 O(n) |

均摊界最常见的来源是 geometric growth (几何扩容)：动态数组满时把容量翻倍，并把旧元素复制过去。从空数组连续追加 n 项，复制量是 1 + 2 + 4 + … 直到不足 n 的最大 2 的幂，总和小于 2n，所以每次追加均摊 O(1)；但触发扩容的那一次要复制当前全部元素，是 O(n)。哈希表扩容重分桶、环形缓冲区按倍数扩容都是同一种账。均摊界保证的是总量，不保证每一次都快。

#### 规范保证与实现模型

语言规范或 API 文档承诺的界，和“常见实现大约是这样”的分析模型是两回事。分析时可以用后者，但要写明用的是哪一个：

- **JavaScript `Map`/`Set`。** ECMAScript 只要求实现提供平均访问时间相对元素数“次线性”的结构，没有承诺 O(1)。主线一各章按常见哈希实现的模型，把一次 `Map`/`Set` 的查找、插入或删除记为期望（均摊）O(1)；键很长或比较代价随内容增长时另计键处理成本。
- **`Array.prototype.sort`。** 自 ECMAScript 2019 起，规范要求排序稳定，并规定了比较器必须给出一致的顺序；但它不规定排序算法、比较调用序列，也不承诺 O(n log n)。主线一各章写 “排序 O(n log n)” 时，按最坏 O(n log n) 的比较排序（如归并排序、堆排序）模型计，不是这个 API 的保证。
- **有序容器与哈希表的库契约。** Java `TreeMap` 在文档里写明基于红黑树并保证 O(log n)；C++ `std::map` 只规定操作复杂度，不规定树形；Java `HashMap` 的公共契约与 OpenJDK 的树化阈值也要分开看。这些实例在[数组、链表、树和哈希表各靠什么找到目标、维护顺序？](#2.%20%E6%95%B0%E7%BB%84%E3%80%81%E9%93%BE%E8%A1%A8%E3%80%81%E6%A0%91%E5%92%8C%E5%93%88%E5%B8%8C%E8%A1%A8%E5%90%84%E9%9D%A0%E4%BB%80%E4%B9%88%E6%89%BE%E5%88%B0%E7%9B%AE%E6%A0%87%E3%80%81%E7%BB%B4%E6%8A%A4%E9%A1%BA%E5%BA%8F%EF%BC%9F)。

#### 递归深度也是空间

递归每深入一层，就在调用栈上多占一帧；递归深度 d 的算法至少用 O(d) 栈空间。这份空间受运行时调用栈大小的限制，而不是受堆内存预算的限制：退化成链的树（h = n）、嵌套极深的输入、划分偏斜的快速排序，都可能让递归在数据还远未占满内存时就栈溢出。深度会随输入增长时，改用显式栈，把“待处理的工作”放进堆上的数组，见[待处理的工作该用队列还是栈，各怎样实现？](#%E6%98%BE%E5%BC%8F%E6%A0%88%E6%80%8E%E6%A0%B7%E4%BB%A3%E6%9B%BF%E9%80%92%E5%BD%92%EF%BC%9F)。

额外空间还包括复制和分配：是否允许原地修改输入、是否复制了数组或对象、输出本身占多少，都要分开写。例如返回一份排序副本需要 O(n) 输出空间，这与排序算法本身的辅助空间是两笔账。

#### 数值表示：安全整数与位数成本

“一次加法 O(1)”假设数值是固定宽度的。在 JavaScript 里这条假设有具体后果：

- **Number 只在安全整数范围内精确。** Number 是双精度浮点数，整数运算只有在每个中间结果都不超过 2⁵³ − 1（`Number.MAX_SAFE_INTEGER`，即 9,007,199,254,740,991）时才保证精确。Fibonacci 数 F(78) = 8,944,394,323,791,464 仍可精确表示，F(79) = 14,472,334,024,676,221 已经越界；溢出时结果先是悄悄失去精度，大到极点时两个有限的 `Number.MAX_VALUE` 相加得到 `Infinity`。主线一后续代码对输入和中间和做的 `Number.isSafeInteger` 检查，都是为了在越界时抛错而不是返回错误结果。
- **BigInt 精确，但位数进入成本。** BigInt 不会溢出，可一次 b 位的加法或比较要 O(b) 次位运算。F(n) 的位数随 n 线性增长（约 0.69n 位），所以用 BigInt 迭代算 F(n) 虽然只做 n − 1 次加法，位运算总量却是 Θ(n²)。长期递增的序号若用 BigInt，位数只随 log m 增长（m 是累计次数），比较成本通常可以忽略，但它不再是严格的常数。

### 大 O 不替代测量

大 O 只比较同一成本模型里的操作数，许多决定实际耗时的因素不在其中：

- 同样 O(n) 的遍历，连续数组的扫描往往比沿指针跳转的链表快，原因在缓存行和预取，见[同样是 O(n)，为什么连续扫描往往比链表遍历快？](#13.%20%E5%90%8C%E6%A0%B7%E6%98%AF%20O%28n%29%EF%BC%8C%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)。
- 均摊 O(1) 的插入，个别一次会因扩容而明显变慢。
- 数据在磁盘或 SSD 上时，主要成本变成读取了多少个存储页，而不是比较了多少次；数据库索引因此按页设计，见[数组、链表、树和哈希表各靠什么找到目标、维护顺序？](#%E6%95%B0%E6%8D%AE%E5%9C%A8%E7%A3%81%E7%9B%98%E4%B8%8A%E6%97%B6%EF%BC%8C%E4%B8%BA%E4%BB%80%E4%B9%88%E6%8C%89%E9%A1%B5%E8%AE%A1%E6%88%90%E6%9C%AC%EF%BC%9F)。

所以复杂度用来排除明显不合适的方案、预测规模增长的趋势；在两个渐近相同的方案之间做选择，要靠测量。

### 怎样写出一份可复核的选型

把前面的问题落成一段文字，别人就能复核它在什么条件下失效。报表 42 事件页的选型可以这样写：

- **输入保证：** 1,024 条，按 `(occurred_at, event_id)` 升序；时间同精度 UTC、ID 定宽，所以字符串比较与时间、ID 的顺序一致；完整键唯一。
- **操作：** 求目标 `(09:02, e08)` 的插入位置；空页返回 0，目标大于全部键时返回 n。
- **方法与成本：** `lower_bound`，最坏 11 次探测、至多 22 次字段比较，额外空间 O(1)。
- **失效条件：** 数据无序、比较器只比部分字段、ID 改为不定宽、空值规则改变，都要重新论证；无序时退回线性扫描，或先排序并把排序成本算进去。

写选型时，还要逐项检查这几类假设：

- 目标是定位、存在性判断还是排序？顺序由谁建立、用的是不是同一条比较规则？
- 有没有可复用的子问题？状态是否包含转移需要的全部信息？
- 是否允许原地修改？复制、分配、扩容和递归栈是否计入了内存预算？
- 空输入、重复键、相同排序值、零容量、超出安全整数的数和非 ASCII 文本会不会改变结果？

本章的产出是这样一份写明输入保证、所需操作和成本模型的选型。接下来的问题是：数据本身放在什么结构里，才能提供这些操作需要的定位方式和顺序？这由[数组、链表、树和哈希表各靠什么找到目标、维护顺序？](#2.%20%E6%95%B0%E7%BB%84%E3%80%81%E9%93%BE%E8%A1%A8%E3%80%81%E6%A0%91%E5%92%8C%E5%93%88%E5%B8%8C%E8%A1%A8%E5%90%84%E9%9D%A0%E4%BB%80%E4%B9%88%E6%89%BE%E5%88%B0%E7%9B%AE%E6%A0%87%E3%80%81%E7%BB%B4%E6%8A%A4%E9%A1%BA%E5%BA%8F%EF%BC%9F)回答。数据库索引（主线三）和服务里的有界队列（主线二、四）都直接沿用这里的选型方法和成本口径。

> [!info]- 来源
> - 二分查找只在输入已按同一键顺序排列时才能每次排除一半候选（“选型从输入保证开始”“1,024 条事件”）：[NIST Dictionary of Algorithms and Data Structures, binary search](https://xlinux.nist.gov/dads/HTML/binarySearch.html)。11 次探测、22 次字段比较、子集与排列的输出元素数由本页按区间更新和各候选长度求和复算。
> - 成本模型、最坏情况保证、随机化算法的期望保证、均摊分析，以及“resizing array 上任意 N 次操作总时间与 N 成正比”（“Big-O 数的是什么”“三种界各承诺什么”）：[Sedgewick & Wayne, *Algorithms*, 4th ed., §1.4 Analysis of Algorithms](https://algs4.cs.princeton.edu/14analysis/)，“Mathematical models”“Coping with dependence on inputs”两节；规模模型另见 [MIT 6.006 Spring 2020, Lecture 3: Sorting](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/6d1ae5278d02bbecb5c4428928b24194_MIT6_006S20_lec3.pdf)。
> - `Map`/`Set` 只要求平均访问时间次线性，不规定数据结构或 O(1) 上界（“规范保证与实现模型”）：[ECMAScript 2026, §24.1 Map Objects、§24.2 Set Objects](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - `Array.prototype.sort` 要求稳定、规定比较器一致性，比较调用序列由实现决定，不规定时间界（“规范保证与实现模型”）：[ECMAScript 2026, §23.1.3.30](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)；稳定性要求自 [ECMAScript 2019, §22.1.3.27](https://tc39.es/ecma262/2019/#sec-array.prototype.sort) 起。
> - `Number.MAX_SAFE_INTEGER` = 2⁵³ − 1（“数值表示”）：[ECMAScript 2026, §21.1.2.6](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)。F(78)、F(79) 与 `Number.MAX_VALUE + Number.MAX_VALUE === Infinity` 由本页用 Node.js v26.13.1 复算。
## 2. 数组、链表、树和哈希表各靠什么找到目标、维护顺序？

一种数据结构快不快，取决于它怎样找到目标、改动时要更新哪些链接、能不能保持顺序；同一组数据换一种访问方式，最合适的结构就可能不同。本章比较数组、链表、搜索树、B/B+ 树、哈希表和 Trie 这三方面的差别，以及各自复杂度界的前提。读者手上已有[首章](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)的选型步骤和成本口径（`Map`/`Set` 按期望 O(1) 计、均摊与最坏的区别）。

### 选结构先问三件事

沿用主线一的案例：报表 42 事件页里的四条演示记录，按 `(occurred_at, event_id)` 排序为 `e07`(09:00)、`e03`(09:02)、`e11`(09:02)、`e18`(09:05)。页面要按位置取第几条、按 `event_id` 找某一条、按时间顺序遍历，偶尔还要插入新到的事件。对每种结构问三件事：

1. **靠什么定位目标？** 下标、沿链接逐个走、按键比较选一侧，还是用哈希值算出位置？
2. **改动时更新什么？** 搬移后续元素、改几个相邻链接，还是重新平衡、重分桶？
3. **是否保持顺序？** 遍历时能不能直接得到键的顺序？

![同一批事件在数组、单链表和平衡搜索树中的布局，以及各自走到 e18 的路径](../../engineering-foundations/computation/resources/core-data-structures-representation-choice.svg)

图中三种结构各自找到 `e18`：数组知道下标 3 就直接读槽位；单链表从 `head` 沿 `next` 走三步；搜索树按同一复合键比较，目标 `(09:05, e18)` 先与根 `e11` 比较，大于它就走到右孩子。

| 结构 | 定位 | 插入、删除 | 顺序与前提 |
|---|---|---|---|
| 数组 | 已知下标 O(1)；按值扫描 O(n)；按该键排序后二分 O(log n) | 中间位置 O(n)，后续元素要搬移；末尾追加均摊 O(1) | 存放顺序即遍历顺序；连续存放，扫描局部性好 |
| 单链表 | 按值或位置 O(n) | 已持有前驱时 O(1)，否则先找前驱 | 保持插入顺序；删除需要前驱 |
| 双向链表 | 裸链表按值 O(n)，通常配外部索引 | 已持有节点时 O(1) | 每节点多存前后两个引用 |
| 平衡搜索树 | O(log n) | O(log n) | 中序遍历即键序；靠不变量限制树高 |
| 非平衡搜索树 | 最坏 O(n) | 最坏 O(n) | 递增插入会退化成链 |
| 哈希表 | 期望 O(1) | 期望 O(1)，扩容均摊 | 不保持键序；依赖哈希分布 |
| Trie | 长度 m 的键约 O(m) | 沿路径增删 | 共享前缀；选子边的成本与内存另计 |

### 复合键有序的数组，对子字段并不有序

这一页按“先时间、后 ID”排序，并不意味着 `event_id` 单独有序：`e03` 的时间晚于 `e07`，ID 却更小。所以：

- 用完整排序键 `(occurred_at, event_id)` 做精确查找或找边界，可以在数组上二分；比较器要怎样与字段类型、空值位置和排序规则对齐，见[有序数据怎样让二分查找和双指针安全排除候选？](#7.%20%E6%9C%89%E5%BA%8F%E6%95%B0%E6%8D%AE%E6%80%8E%E6%A0%B7%E8%AE%A9%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%E5%AE%89%E5%85%A8%E6%8E%92%E9%99%A4%E5%80%99%E9%80%89%EF%BC%9F)。
- 只知道 `event_id` 时不能二分。可以另建一个以 `event_id` 为键的哈希索引，按 ID 期望 O(1) 找到记录；代价是多一份内存，而且这个索引不提供时间顺序。
- 搜索树同理：它按复合键比较，查找时也必须给出完整的键。

数据库的复合索引有同样的性质：按 `(a, b)` 建的索引能按 `a` 或 `(a, b)` 定位，单给 `b` 就用不上这份顺序，见[约束与索引一章](#23.%20%E7%BA%A6%E6%9D%9F%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%A7%84%E5%88%99%EF%BC%8C%E7%B4%A2%E5%BC%95%E5%8F%88%E6%80%8E%E6%A0%B7%E6%9C%8D%E5%8A%A1%E8%AF%BB%E5%8F%96%EF%BC%9F)。

### 链表的 O(1) 只在已经拿到节点时成立

“链表插入删除 O(1)”有一个隐藏前提：手上已经有目标节点（双向链表）或它的前驱（单链表）。如果要先按值找到它，整个操作就是 O(n) 的扫描加 O(1) 的改链。所以链表很少单独用来按键查找；需要“按键找到节点、再 O(1) 移动它”时，要配一个从键到节点的哈希索引，这正是 LRU 缓存的结构，见[怎样同时按键查找并维护最近使用顺序？](#4.%20%E6%80%8E%E6%A0%B7%E5%90%8C%E6%97%B6%E6%8C%89%E9%94%AE%E6%9F%A5%E6%89%BE%E5%B9%B6%E7%BB%B4%E6%8A%A4%E6%9C%80%E8%BF%91%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F)。

链表还有一项渐近分析看不到的成本：节点分散在内存里，遍历时每一步都要等上一个节点的地址读出来才能访问下一个。连续数组的扫描因此往往更快，原因见[同样是 O(n)，为什么连续扫描往往比链表遍历快？](#13.%20%E5%90%8C%E6%A0%B7%E6%98%AF%20O%28n%29%EF%BC%8C%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)。

### 搜索树的成本按树高计

binary search tree (BST，二叉搜索树) 的每个节点把键分成两侧：左子树的键不大于它，右子树的键不小于它。查找、插入、删除都沿一条根到叶的路径走，所以成本是 O(h)，h 是树高。h 不会自动是 O(log n)：按复合键递增的顺序插入 `e07`、`e03`、`e11`、`e18`，每个新键都比已有的大，每次都挂在最右端，树退化成一条长度为 4 的链，查找最坏 O(n)。

balanced search tree (平衡搜索树) 用一条不变量限制树高。red-black tree (红黑树) 是常见的一种，规则是：

- 每个节点是红色或黑色，根和叶哨兵（空孩子）视为黑色；
- 红节点的孩子必须是黑色；
- 从任一节点到其后代叶哨兵的每条路径上，黑节点数相同。

最短路径全黑、最长路径红黑交替，所以最长路径不超过最短路径的两倍，树高为 O(log n)；插入或删除破坏规则时，用重新着色和旋转在 O(log n) 内恢复。于是搜索、插入、删除最坏都是 O(log n)。这些界把一次键比较算作常数；若字符串或复合键的比较成本随长度增长，还要乘上比较成本。

怎样按前序、中序、后序遍历一棵树，怎样用显式栈取中序第 k 小，又怎样把扁平的 `parentId` 记录安全地还原成树，见支线[怎样遍历一棵树，又怎样把扁平记录安全地还原成树？](#3.%20%E6%80%8E%E6%A0%B7%E9%81%8D%E5%8E%86%E4%B8%80%E6%A3%B5%E6%A0%91%EF%BC%8C%E5%8F%88%E6%80%8E%E6%A0%B7%E6%8A%8A%E6%89%81%E5%B9%B3%E8%AE%B0%E5%BD%95%E5%AE%89%E5%85%A8%E5%9C%B0%E8%BF%98%E5%8E%9F%E6%88%90%E6%A0%91%EF%BC%9F)。

> [!info] 实例：标准库有序容器的承诺不能互推（Java SE 25、C++ 标准草案）
> - **Java `TreeMap`**：API 文档写明基于红黑树，并保证 `containsKey`、`get`、`put`、`remove` 为 O(log n)。键按自然顺序或构造时给定的 `Comparator` 排序；`Comparator` 若与 `equals` 不一致，`TreeMap` 仍能工作，但违反 `Map` 接口的通用约定。
> - **C++ `std::map`**：按 `Compare` 的严格弱序维护唯一键。标准只规定操作复杂度，不规定底层用什么树：`find` 与不带位置提示的单元素 `insert` 为 O(log n)；`erase(iterator)` 均摊 O(1)；`erase(first, last)` 为 O(log n + k)，k 是被删元素数。
>
> 一种库的实现方式不能推出另一种库的保证：从“`std::map` 通常是红黑树”推不出标准承诺了树形，从 `TreeMap` 的文档也推不出别的语言的有序容器复杂度。

### 数据在磁盘上时，为什么按页计成本？

数据放在磁盘或 SSD 上时，一次读取的单位是一个存储页，读一页的代价远大于在内存里比较几次键。成本单位因此从“比较次数”变成“读了多少页”，二叉树就不合适了：它每个节点只有一个键，树高约 log₂ n，每下一层都可能多读一页。

- **B-tree (B 树)** 让每个节点容纳很多键和孩子，一个节点对应一页。分支数大，树就矮，从根到叶只需读少数几页。B 树的内部节点也可以保存记录或记录引用。
- **B+ tree (B+ 树)** 的内部节点只存导航用的键，叶节点保存记录或指向记录的条目，叶页按键顺序相互链接。找到范围的起点后，沿叶链顺序读下去就能完成范围扫描，不必回到上层。

具体数据库的页大小和索引布局以产品文档为准。索引列顺序怎样决定能否用上一份索引，见[约束与索引一章](#23.%20%E7%BA%A6%E6%9D%9F%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%A7%84%E5%88%99%EF%BC%8C%E7%B4%A2%E5%BC%95%E5%8F%88%E6%80%8E%E6%A0%B7%E6%9C%8D%E5%8A%A1%E8%AF%BB%E5%8F%96%EF%BC%9F)；InnoDB 聚簇索引与二级索引的布局见 [InnoDB 支线](#26.%20InnoDB%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%B4%A2%E5%BC%95%E8%AE%B0%E5%BD%95%E3%80%81%E6%97%A7%E7%89%88%E6%9C%AC%E5%92%8C%E6%97%A5%E5%BF%97%E5%A4%84%E7%90%86%E5%90%8C%E4%B8%80%E7%AC%94%E5%BA%93%E5%AD%98%E4%BA%8B%E5%8A%A1%EF%BC%9F)。

### 哈希表：不保序，换来期望常数时间的精确查找

如果只需按 `event_id` 精确查找、不需要顺序，哈希表通常比树快。它用键的哈希值选出一个桶，再在桶内处理冲突。不同的键可能落进同一个桶，这叫 collision (碰撞)。

- **期望 O(1) 的前提。** 桶内的平均条目数由 load factor (负载因子，条目数除以桶数) 决定。负载因子受控、哈希值分布良好时，查找和插入是期望 O(1)；分布很差时，大量键挤进少数桶，单次操作退化。若键的哈希和相等比较本身随内容长度增长，也要计入。
- **扩容是均摊的。** 条目数超过“容量 × 负载因子”时，表扩容并按新容量重新分桶。这一次要处理全部条目，是 Θ(n)；摊到一串插入上才是均摊常数。扩容能拆开一部分碰撞，但拆不开哈希值完全相同的键。
- **负载因子是空间与碰撞的取舍。** 负载因子高，桶少、省空间，但碰撞多；低则用更多桶换更少碰撞。遍历一张哈希表要走过所有桶，预留容量过大会让遍历变慢。
- **相等契约。** 相等的键必须有相同的哈希值，否则同一个键可能被放进两个桶。键放入表之后，若又修改了参与哈希或相等判断的字段，它就留在旧哈希值对应的桶里，之后按新值查找会找不到它。
- **不保序。** 哈希表适合按键精确查找，不提供按键顺序的遍历，也不支持“找第一个不小于目标的键”这类边界查询。

#### 实例：Java `HashMap` 的契约与 OpenJDK 的实现

Java SE 25 `HashMap` 的公共契约：允许一个 `null` 键和多个 `null` 值；不保证迭代顺序；不是线程安全的；哈希分布合理时 `get`/`put` 为常数时间；默认初始容量 16、负载因子 0.75，条目数超过两者之积就扩容；遍历时间与“容量 + 条目数”成正比。Java SE 17 的 API 在这些方面相同。它要求 `equals` 相等的对象 `hashCode` 也相等，这是上面相等契约在 Java 里的写法。

下面是 OpenJDK 源码的实现细节，不是 `Map` 接口的保证（OpenJDK 25u 与 17u 维护分支于 2026-11-11 对照，两者一致）：

- 计算桶下标前，先用 `h ^ (h >>> 16)` 把哈希高位扩散到低位，再取 `h & (容量 − 1)`。对扩散后的值 `h`：容量 16 时，`h = 1` 与 `h = 17` 都落在桶 1；扩容到 32 后，分别落在桶 1 和桶 17。
- 一个桶的链表过长时可能转成红黑树（树化），阈值 `TREEIFY_THRESHOLD = 8`；但表容量小于 `MIN_TREEIFY_CAPACITY = 64` 时，先扩容而不树化。

用普通 `putVal` 向链表桶追加节点的路径看：桶里已有 8 个碰撞节点、再追加第 9 个时，若表容量已达 64，这次 `put` 把该桶树化。若表从容量 16 开始、其中只有这些扩散后哈希值完全相同的键，第 9 个碰撞项触发扩容到 32，第 10 个触发扩容到 64，第 11 个才树化。若这些键只是在旧表中同桶而哈希值不同，扩容时可能分到不同的桶，计数就不同。这个计数只描述这条源码路径，不能推广到 `compute`/`merge`；树桶也不保证严格的 O(log n)：键实现 `Comparable` 时有助于区分哈希值相同的项，但哈希分布差仍会拖慢整体。

### 按前缀查找：Trie

trie (前缀树) 让共享前缀的键共用一条路径，适合“找所有以某前缀开头的键”。设 m 为键在遍历时的单元数（字节、码元或码点，取决于实现）：如果每一层都能以期望常数时间选出子边，查找约为 O(m)，与表里有多少个键无关；否则还要加上每个节点选子边的成本。子边用数组、哈希表还是有序列表表示，决定了选边成本和总内存：数组按符号直接取下标，但每个节点都要为整个字母表留槽。按什么文本单位建 Trie、前缀查询该选哈希、有序数组还是 Trie，见支线[文本算法应按码元、码点还是字素簇处理？](#9.%20%E6%96%87%E6%9C%AC%E7%AE%97%E6%B3%95%E5%BA%94%E6%8C%89%E7%A0%81%E5%85%83%E3%80%81%E7%A0%81%E7%82%B9%E8%BF%98%E6%98%AF%E5%AD%97%E7%B4%A0%E7%B0%87%E5%A4%84%E7%90%86%EF%BC%9F)。

### 本章产出与下一步

现在可以按访问方式为一组数据选结构：按位置读和顺序扫描用数组；已持有节点后的 O(1) 改链用链表，按键找节点要另配索引；需要键序和边界查询用平衡树，数据在外存时用 B+ 树；只要精确查找用哈希表；前缀查询用 Trie。每个界都带着它的前提：下标已知、持有节点、树高受控、哈希分布良好。

本章两条支线把这些结构组合起来：树的遍历与扁平记录还原（[支线](#3.%20%E6%80%8E%E6%A0%B7%E9%81%8D%E5%8E%86%E4%B8%80%E6%A3%B5%E6%A0%91%EF%BC%8C%E5%8F%88%E6%80%8E%E6%A0%B7%E6%8A%8A%E6%89%81%E5%B9%B3%E8%AE%B0%E5%BD%95%E5%AE%89%E5%85%A8%E5%9C%B0%E8%BF%98%E5%8E%9F%E6%88%90%E6%A0%91%EF%BC%9F)），哈希表加双向链表实现 LRU（[支线](#4.%20%E6%80%8E%E6%A0%B7%E5%90%8C%E6%97%B6%E6%8C%89%E9%94%AE%E6%9F%A5%E6%89%BE%E5%B9%B6%E7%BB%B4%E6%8A%A4%E6%9C%80%E8%BF%91%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F)）。主线的下一个问题是：待处理的工作按到达顺序或按“最近未完成”顺序取出时，该用队列还是栈，又怎样实现才不在出队时搬移元素？见[待处理的工作该用队列还是栈，各怎样实现？](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)。

> [!info]- 来源
> - 有序容器契约（“实例：标准库有序容器”）：[Java SE 25 TreeMap API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/TreeMap.html) 的 red-black tree、键序、`Comparator` 与 `equals` 一致性及 `containsKey`/`get`/`put`/`remove` 成本；[C++ draft, associative container requirements §23.2.7](https://eel.is/c++draft/associative.reqmts) 的 `find`/`insert`、`erase(iterator)` 与 `erase(first, last)` 复杂度。
> - 红黑树规则与树高 O(log n)、BST 退化（“搜索树的成本按树高计”）：[Sedgewick & Wayne, *Algorithms*, 4th ed., §3.2 Binary Search Trees](https://algs4.cs.princeton.edu/32bst/)（按序插入使树退化）、[§3.3 Balanced Search Trees](https://algs4.cs.princeton.edu/33balanced/)（红黑树高度不超过约 2 lg n）。
> - B+ 树结构（“数据在磁盘上时”）：[Silberschatz, Korth & Sudarshan, *Database System Concepts*, 7th ed., Chapter 14 slides](https://db-book.com/slides-dir/PDF-dir/ch14.pdf)，14.20–14.22：内部节点作导航，叶节点保存记录指针并按键顺序链接。
> - `HashMap` 公共契约、默认容量与负载因子、扩容、迭代成本（“实例：Java HashMap”）：[Java SE 25 HashMap API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/HashMap.html)；[Java SE 17 HashMap API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/HashMap.html)（2026-11-13 核对）。
> - 哈希扩散、`TREEIFY_THRESHOLD`、`MIN_TREEIFY_CAPACITY` 与 `putVal`/`treeifyBin` 路径：[OpenJDK 25u HashMap 源码](https://github.com/openjdk/jdk25u/blob/master/src/java.base/share/classes/java/util/HashMap.java)、[OpenJDK 17u HashMap 源码](https://github.com/openjdk/jdk17u/blob/master/src/java.base/share/classes/java/util/HashMap.java)，2026-11-11 对照；第 9～11 个碰撞项的计数按该路径推演。
## 3. 怎样遍历一棵树，又怎样把扁平记录安全地还原成树？

树的算法有两类常见问题：按什么顺序访问节点，以及拿到一张扁平的父子记录表时，怎样确认它真的构成一棵树（或一片森林）再还原出来。本章先讲深度优先的三种访问时机和用显式栈取二叉搜索树的第 k 小，再讲一般树的 DFS 与 BFS，最后讲扁平记录的两趟还原与森林不变量校验。读者手上已有[上一章](#2.%20%E6%95%B0%E7%BB%84%E3%80%81%E9%93%BE%E8%A1%A8%E3%80%81%E6%A0%91%E5%92%8C%E5%93%88%E5%B8%8C%E8%A1%A8%E5%90%84%E9%9D%A0%E4%BB%80%E4%B9%88%E6%89%BE%E5%88%B0%E7%9B%AE%E6%A0%87%E3%80%81%E7%BB%B4%E6%8A%A4%E9%A1%BA%E5%BA%8F%EF%BC%9F)的二叉搜索树定义与“成本按树高计”。遍历要用到队列和栈，本章只用两条结论：数组队列用递增的 head 下标出队，不用 `shift`；深度随输入增长时用显式栈代替递归。它们的实现和推导在主线的下一章[待处理的工作该用队列还是栈，各怎样实现？](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)。

本章用一棵四个节点的分类树作独立的小例子，因为主线一的事件页是一维有序数组，没有层级：根 `1`（根）下有 `2`（收入）和 `3`（支出），`2` 下有 `4`（工资）。复杂度按[首章的成本口径](#%E8%A7%84%E8%8C%83%E4%BF%9D%E8%AF%81%E4%B8%8E%E5%AE%9E%E7%8E%B0%E6%A8%A1%E5%9E%8B)计，`Map`/`Set` 操作记为期望 O(1)。

### 深度优先的三种访问时机

depth-first search (DFS，深度优先搜索) 沿一个分支走到底再回头。对二叉树，按“什么时候处理当前节点”分三种：

| 顺序 | 访问次序 | 典型用途 |
|---|---|---|
| 前序 | 节点、左、右 | 先输出父再输出子；配合空子树标记可以序列化一棵树 |
| 中序 | 左、节点、右 | 对 binary search tree (BST，二叉搜索树) 按键的非降序输出 |
| 后序 | 左、右、节点 | 先处理完子树再处理父：汇总子树大小、先释放子节点 |

一般树没有“中间”位置，只有前序和后序。分类树的前序是 1、2、4、3，后序是 4、2、3、1。

中序非降序是 BST 次序的必要条件，但不能证明实现自己的重复键约定成立。例如约定“相等的键只放右侧”时，根 2、左子 2、右子 3 的中序是 2、2、3，确实非降序，却把相等的键放在了左侧。要校验这种约定，得在递归时传下每个子树允许的键范围（含开闭），而不是只看中序结果。

### 用显式栈取 BST 中第 k 小

BST 的中序就是从小到大，所以第 k 小就是中序第 k 个节点。用显式栈做中序：先把从当前节点出发的整条左链压栈，弹出栈顶即下一个最小值，再转到它的右子树重复。

```javascript
function kthSmallest(root, k) {
  if (!Number.isInteger(k) || k <= 0) return null;
  const stack = [];
  let node = root;
  while (node || stack.length) {
    while (node) {            // 压入整条左链
      stack.push(node);
      node = node.left;
    }
    node = stack.pop();       // 中序的下一个节点
    if (--k === 0) return node.val;
    node = node.right;
  }
  return null;                // 节点不足 k 个
}
```

前提：节点值是有限数字、比较规则一致，树满足 BST 次序。重复值按节点分别计数；若实现把同值合并成一个节点并记录次数，选第 k 项时要把次数算进去。

> [!example] 栈怎样找出中序第 3 项
> 这里换成一棵合成的数值树，便于看序号：根 3，左子 1（1 的右子为 2），右子 4；取 k = 3。
>
> | 步骤 | 动作 | 栈（底 → 顶） | k |
> |---|---|---|---|
> | 1 | 压入左链 3、1 | 3, 1 | 3 |
> | 2 | 弹出 1，转到右子 2 | 3 | 2 |
> | 3 | 压入 2 后弹出，右子为空 | 3 | 1 |
> | 4 | 弹出 3，k 归零，返回 3 | — | 0 |
>
> 中序是 1、2、3、4，第三项确实是 3；k = 5 时遍历完全部节点仍未归零，返回 `null`。

成本：至多弹出 k 个节点；结束时栈里最多还有 h 个祖先（h 为树高），所以 push 至多 k + h 次，总时间 O(h + k)，最坏 O(n)；栈空间 O(h)。平衡树 h = O(log n)，退化成链时 h = O(n)。

### 遍历一般树：递归、显式栈与 head 下标 BFS

DOM (Document Object Model，文档对象模型) 这类一般树每个节点有任意多个孩子。下面三个函数都接收一个 `childrenOf(node)`，它返回该节点孩子的**一份数组快照**：对分类树是 `n => [...n.children]`，对 DOM 是 `n => Array.from(n.childNodes)`。

```javascript
function dfs(root, visit, childrenOf) {
  if (!root) return;
  visit(root);
  for (const child of childrenOf(root)) dfs(child, visit, childrenOf);
}

function dfsIterative(root, visit, childrenOf) {
  if (!root) return;
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    visit(node);
    const children = childrenOf(node);
    for (let i = children.length - 1; i >= 0; i--) stack.push(children[i]); // 逆序压栈，保持前序
  }
}

function bfs(root, visit, childrenOf) {
  if (!root) return;
  const queue = [root];
  for (let head = 0; head < queue.length; head++) { // head 下标出队，不用 shift
    const node = queue[head];
    visit(node);
    for (const child of childrenOf(node)) queue.push(child);
  }
}
```

对分类树，两种 DFS 都输出 1、2、4、3；breadth-first search (BFS，广度优先搜索) 一层一层访问，输出 1、2、3、4。显式栈版要把孩子从右到左压栈，才能按从左到右的顺序弹出，这条规则和“栈项存什么”见[显式栈怎样代替递归？](#%E6%98%BE%E5%BC%8F%E6%A0%88%E6%80%8E%E6%A0%B7%E4%BB%A3%E6%9B%BF%E9%80%92%E5%BD%92%EF%BC%9F)。BFS 用递增的 `head` 下标读队首，而不是反复 `shift`：后者对普通数组要前移全部后续元素，整次遍历可达 Θ(n²)，推导见[队列与栈一章](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)。树中每个节点从根出发只有一条路径，BFS 在这里只决定访问次序；在一般图上按边数求最短路，还要决定何时标记已访问，见[搜索状态图时，何时永久标记节点，何时必须回退？](#11.%20%E6%90%9C%E7%B4%A2%E7%8A%B6%E6%80%81%E5%9B%BE%E6%97%B6%EF%BC%8C%E4%BD%95%E6%97%B6%E6%B0%B8%E4%B9%85%E6%A0%87%E8%AE%B0%E8%8A%82%E7%82%B9%EF%BC%8C%E4%BD%95%E6%97%B6%E5%BF%85%E9%A1%BB%E5%9B%9E%E9%80%80%EF%BC%9F)。

**快照在 `visit` 之后取。** 三个函数都先调用 `visit(node)`，再读取 `node` 的孩子。所以回调对当前节点孩子的增删会反映在随后的快照里；已经取过快照的节点，之后再改它的孩子就看不到了。DOM 的 `childNodes` 是 live `NodeList`，会随文档变化；`Array.from` 把调用时刻的结果放进新数组，迭代的就是这份快照，而不是一边改一边读的活集合。

**成本。** 树在遍历中不变、每次 `visit` 和每次取快照都与孩子数成正比时，访问 n 个节点总时间 O(n)。空间要分开看：

- 递归 DFS 的调用栈深度是 O(h)，但每个尚未返回的帧还持有一份孩子数组，合计最坏 O(n)，例如根有 n − 1 个孩子时。
- 显式栈 DFS 的栈、BFS 的队列最坏也是 O(n)：前者在宽节点处一次压入全部孩子，后者的数组保留全部已入队节点。
- 递归深度受运行时调用栈限制，不受堆内存限制。来自外部的树可能很深，这时用显式栈版。

回调会改树时，按实际访问的节点数和回调成本另算。

### 扁平 parentId 记录：两趟还原成树

后端返回的分类通常是扁平的行，每行用 `parentId` 指向父分类，根的 `parentId` 是约定的标记值 0。行的顺序没有保证，子行可能先于父行出现。

本例的输入契约：每行是普通数据记录；`id` 是互不重复的正安全整数（0 留作根标记）；恰好一行 `parentId = 0`；其余行的父 ID 都必须存在。

转换分两趟，因为读到子行时父行可能还没出现：

1. **建索引。** 为每行建一个浅拷贝节点，带空的 `children`，按 `id` 放进 `Map`；遇到重复 ID 就报错。
2. **接父子。** 再按行序读一遍：`parentId = 0` 的是根；其余用 `Map.get(parentId)` 找到父节点，把节点引用追加到父的 `children`。找不到父节点、出现第二个根都报错。

![四行分类记录先按 id 建 Map，再按 parentId 把节点接到父节点下，得到以 1 为根的树](../../engineering-foundations/computation/resources/core-data-structures-array-to-tree.svg)

图中的输入故意打乱：`收入` 在根之前，`工资` 在 `支出` 之前。第二趟读到 ①时，根还没轮到，但它的节点已在 `Map` 里，所以 2 照样接到 1 下。

**顺序保留到哪一步。** 每个父节点的 `children` 按输入行序追加，所以同一父节点下的子项保持输入中的相对顺序：1 的孩子是 [2, 3]。不同父节点的行原先怎样交错，转换后不再记录。

**最后还要从根遍历一次。** 每行只有一个 `parentId` 字段，“单父”由表示本身保证；但父指针可能绕成环，例如 6 的父是 7、7 的父是 6。这两行各自的父都存在，前两趟查不出来。从根做一次 DFS 并比较到达的节点数即可：在单父、父都存在、根唯一的前提下，一个节点到不了根，当且仅当它在环上或挂在环下面。原因是沿父指针从任一节点往上走，要么到达根，要么永远走不出某个环；若环上某节点能从根到达，进入环的那一步会给它第二个父节点，与单父矛盾。

```javascript
function arrayToTree(rows) {
  if (!Array.isArray(rows)) throw new TypeError('rows must be an array');
  const nodes = new Map();
  for (const row of rows) {
    if (!row || !Number.isSafeInteger(row.id) || row.id <= 0) {
      throw new RangeError('id must be a positive safe integer');
    }
    if (nodes.has(row.id)) throw new RangeError(`duplicate id ${row.id}`);
    nodes.set(row.id, { ...row, id: row.id, parentId: row.parentId, children: [] });
  }

  let root = null;
  for (const row of rows) {
    const node = nodes.get(row.id);
    if (row.parentId === 0) {
      if (root) throw new RangeError(`second root ${row.id}`);
      root = node;
    } else {
      const parent = nodes.get(row.parentId);
      if (!parent) throw new RangeError(`parent ${row.parentId} of ${row.id} does not exist`);
      parent.children.push(node);
    }
  }
  if (!root) throw new RangeError('no root');

  const seen = new Set();
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    seen.add(node.id);
    for (const child of node.children) stack.push(child);
  }
  for (const id of nodes.keys()) {
    if (!seen.has(id)) throw new RangeError(`node ${id} is on or under a cycle`);
  }
  return root;
}
```

对图中的四行，`arrayToTree` 返回以 1 为根的树，`seen` 与 `Map` 都是 4 项。追加 `{id:6,parentId:7}`、`{id:7,parentId:6}` 后，前两趟都通过，可达性检查报告 `node 6 is on or under a cycle`。

**复制了什么。** 代码显式写回 `id` 和 `parentId`，即使这两个属性在原行里不可枚举，建索引和接父子用到的字段也不会丢；其他业务字段（如 `name`）要是自有可枚举属性，否则需显式复制。对象展开 `{ ...row }` 按规范的 CopyDataProperties 先取出每行的全部自有键、逐个检查描述符，再只复制可枚举属性，不递归复制属性值。

**成本。** 设 Q 为所有行的自有键总数（含不可枚举的），P 为其中可枚举的总数。建索引、接父子和可达性检查各是 O(n) 次 `Map`/`Set` 操作；浅拷贝扫描 O(Q)，复制出的属性占 O(P)。总时间期望 O(n + Q)，输出空间 O(n + P)。字段值的复制成本随内容长度增长时，另计字节数。

**反向转换按前序输出。** 把树写回扁平行时，用显式栈按前序输出，先父后子：

```javascript
function treeToArray(root) {
  if (!root) return [];
  const rows = [];
  const stack = [{ node: root, parentId: 0 }];
  while (stack.length) {
    const { node, parentId } = stack.pop();
    rows.push({ id: node.id, parentId, name: node.name });
    for (let i = node.children.length - 1; i >= 0; i--) {
      stack.push({ node: node.children[i], parentId: node.id });
    }
  }
  return rows;
}
```

对分类树输出 1、2、4、3 四行，而原始输入的行序是 2、1、4、3：父子关系和同父兄弟的次序都恢复了，原始的跨父交错顺序恢复不了。示例只输出 `id`、`parentId`、`name`，其他字段要显式复制；协议的根标记若不是 0，换成协议规定的值。

### 森林不变量：子节点列表表示要多查什么

另一种常见表示把父子关系记在父节点上：`rootIds` 列出顶层节点及其顺序，`nodes` 按 ID 索引，每个节点的 `children` 只存孩子的 ID。页面编辑器的文档就是这样建模的，见[页面编辑器怎样建模文档、编辑会话和发布快照？](#51.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)。分类树写成这种形式是：

```javascript
const doc = {
  rootIds: ['1'],
  nodes: {
    '1': { id: '1', name: '根',   children: ['2', '3'] },
    '2': { id: '2', name: '收入', children: ['4'] },
    '3': { id: '3', name: '支出', children: [] },
    '4': { id: '4', name: '工资', children: [] },
  },
};
```

它的好处是重排兄弟只改一个数组，按 ID 能直接定位节点；代价是“单父”不再由表示保证：任何节点的 `children` 都可以列出任何 ID。一份合法的 forest (森林)，即若干棵互不相交的树，要同时满足：

1. **引用有效。** 节点的键与它的 `id` 一致；`rootIds` 和 `children` 里只有字符串 ID，且都指向 `nodes` 的自有键。
2. **根不重复，且不作别人的孩子。**
3. **每条父子边只出现一次，每个非根节点恰有一个父节点。**
4. **全部节点都能从某个根到达。**
5. **没有环。**

只查“ID 唯一、引用存在、无环”不够：`3` 也列出 `4` 时，图里没有环，但 `4` 有两个父节点，编辑或渲染时会被处理两次；多出一个谁也不引用的 `5`，它也不在环上，却是从根到不了的孤儿。

#### 三步检查

- **父计数。** 对每条边给孩子的父计数加一（同一父节点重复列出的边只记一次，另报重复边），然后逐个节点判断：计数大于 1 是多父；根的计数大于 0 是“根也是孩子”；非根计数为 0 是“既不是根也不是孩子”。
- **三色 DFS 判环。** 所有节点起初为白色；进入一个节点时染灰，它的全部孩子处理完后染黑。灰色表示“在当前搜索路径上”，所以沿边遇到灰色节点，就是回到了路径上的祖先，构成环；遇到黑色节点只说明它已从别处探查过，比如共享的孩子，不是环。灰色是路径内的标记，黑色是全局标记，两种标记时机的一般规则见[搜索状态图时，何时永久标记节点，何时必须回退？](#%E6%A0%87%E8%AE%B0%E4%BB%80%E4%B9%88%E3%80%81%E4%BD%95%E6%97%B6%E6%A0%87%E8%AE%B0%EF%BC%9A%E5%9B%9B%E7%B1%BB%E6%90%9C%E7%B4%A2%E5%AF%B9%E7%85%A7)。
- **从根可达。** 从全部根出发遍历，最后没到达的节点逐个报告。

其实父计数和可达性已经足以拒绝每一个环：环若经过某个根，这个根就有了父节点；环若不经过根，从外面进入环的那一步会给某个环上节点第二个父节点，没有这一步则整个环从根到达不了。三色 DFS 的作用是诊断：它把错误报告成“环”，并指出环上的一个节点，而不是只留下“多父”或“不可达”让人自己推断原因。

每条错误都带上出错的节点 ID，调用方才能定位到具体节点，而不是只得到一个“文档无效”。

```javascript
const GRAY = 1, BLACK = 2;

function validateForest(doc) {
  const errors = [];
  const report = (code, nodeId) => errors.push({ code, nodeId });
  const nodes = doc?.nodes;
  if (!Array.isArray(doc?.rootIds) || !nodes || typeof nodes !== 'object' || Array.isArray(nodes)) {
    return [{ code: 'bad-shape', nodeId: null }];
  }
  const ids = Object.keys(nodes);
  const isNode = id => typeof id === 'string' && Object.hasOwn(nodes, id); // 挡住非字符串和 'constructor' 等原型键

  const roots = new Set();
  for (const id of doc.rootIds) {
    if (!isNode(id)) { report('unknown-root', String(id)); continue; }
    if (roots.has(id)) report('duplicate-root', id);
    roots.add(id);
  }

  const parentCount = new Map(ids.map(id => [id, 0]));
  const childrenOf = new Map();
  for (const id of ids) {
    const node = nodes[id];
    if (!node || node.id !== id || !Array.isArray(node.children)) {
      report('bad-node', id);
      childrenOf.set(id, []);
      continue;
    }
    const listed = new Set();
    for (const child of node.children) {
      if (!isNode(child)) { report('unknown-child', id); continue; }
      if (listed.has(child)) { report('duplicate-edge', id); continue; }
      listed.add(child);
      parentCount.set(child, parentCount.get(child) + 1);
    }
    childrenOf.set(id, [...listed]);
  }

  for (const id of ids) {                       // 父计数
    const count = parentCount.get(id);
    if (count > 1) report('multiple-parents', id);
    if (roots.has(id) && count > 0) report('root-is-child', id);
    if (!roots.has(id) && count === 0) report('neither-root-nor-child', id);
  }

  const color = new Map();                      // 三色 DFS，显式栈：栈帧记住下一个要看的孩子
  for (const start of ids) {
    if (color.has(start)) continue;
    color.set(start, GRAY);
    const stack = [{ id: start, next: 0 }];
    while (stack.length) {
      const frame = stack[stack.length - 1];
      const kids = childrenOf.get(frame.id);
      if (frame.next < kids.length) {
        const child = kids[frame.next++];
        if (color.get(child) === GRAY) report('cycle', child);
        else if (!color.has(child)) { color.set(child, GRAY); stack.push({ id: child, next: 0 }); }
      } else {
        color.set(frame.id, BLACK);
        stack.pop();
      }
    }
  }

  const reached = new Set(roots);               // 从根可达
  const pending = [...roots];
  while (pending.length) {
    for (const child of childrenOf.get(pending.pop())) {
      if (!reached.has(child)) { reached.add(child); pending.push(child); }
    }
  }
  for (const id of ids) if (!reached.has(id)) report('unreachable', id);
  return errors;
}
```

两处 DFS 都用显式栈，因为待校验的文档来自外部，嵌套深度不受控；三色 DFS 的栈帧除了节点，还要记住“下一个该看第几个孩子”，节点只有在全部孩子处理完、出栈时才染黑。节点数为 n、边数为 e 时，每个节点和每条边都只处理常数次，总时间期望 O(n + e)，额外空间 O(n + e)。

> [!example] 对分类树逐一改坏，各得到什么错误
> 每行都从上面合法的 `doc` 出发，只做一处改动（本页用 Node.js v26.13.1 运行上面的代码得到）：
>
> | 改动 | 返回的错误 |
> |---|---|
> | 不改 | `[]` |
> | `3.children` 加 `'4'`（共享孩子） | `multiple-parents 4` |
> | 新增 `5`，无人引用（孤儿） | `neither-root-nor-child 5`、`unreachable 5` |
> | `4.children` 加 `'2'`（回边） | `multiple-parents 2`、`cycle 2` |
> | `4.children` 加 `'1'`（环经过根） | `root-is-child 1`、`cycle 1` |
> | 新增 `6 → 7 → 6`（与根断开的环） | `cycle 6`、`unreachable 6`、`unreachable 7` |
> | `rootIds` 再加 `'1'` | `duplicate-root 1` |
> | `1.children` 再加 `'3'` | `duplicate-edge 1` |
> | `1.children` 加 `'9'`、`'constructor'` 或对象 | `unknown-child 1` |
>
> 每个带环的改动都同时触发了多父、根也是孩子或不可达中的一种，印证了上面“三色 DFS 用于诊断”的论证。

两种表示的分工可以对照着看：

| 不变量 | parentId 行 | 子节点列表 |
|---|---|---|
| 单父 | 表示保证（每行一个字段） | 要父计数 |
| 根不作孩子 | 表示保证（根的字段就是 0） | 要父计数 |
| 重复边 | 不可能出现 | 要查 |
| 引用存在 | 查父 ID | 查每个孩子 ID 与每个根 ID |
| 无环、全部可达 | 一次根遍历同时查出 | 父计数 + 根遍历拒绝，三色 DFS 诊断 |
| 兄弟顺序 | 只能取输入行序，或另存排序字段 | 由 `children` 数组显式记录 |

这些都是跨节点的整图约束，JSON Schema 这类逐节点的结构描述表达不了，需要应用代码检查；页面编辑器在每次提交命令和发布前调用的正是这组检查。

> [!info] 实例：React Fiber 为什么把树节点链接起来（2026-11-11 核对）
> React 内部的工作树不用 `children` 数组，而是每个 Fiber 节点用 `child` 指向第一个孩子、`sibling` 指向下一个兄弟、`return` 指向父节点。结构上仍是一棵树，只是同级孩子串成了链表。这样 reconciler (协调器) 处理完一个节点后，只要记住“下一个工作单元”是谁，就能暂停后再从这里继续，不必像递归 DFS 那样把进度留在调用栈里。
>
> 能暂停的只有 render 阶段，而且自 React 18 起只在使用 transition 等并发特性时才会让位给更紧急的更新；DOM 变更在 render 完成后的 commit 阶段一次性应用。Fiber 的字段布局是 React 的内部实现，应用代码应依赖公共 API。一次更新怎样走过 render 与 commit，见[React 怎样把一次用户操作变成界面更新？](../../frontend/ui-state/react-update-model.md)。

### 本章产出与回到主线

现在可以为树选遍历方式并估算成本：前序、中序、后序由“何时处理当前节点”决定，BST 中第 k 小用显式栈 O(h + k)；一般树的 DFS 逆序压栈、BFS 用 head 下标，空间最坏 O(n)，深树改用显式栈。拿到扁平记录时，先确定表示替你保证了哪些不变量，再把其余的查掉：parentId 行要查 ID 唯一、父存在、根唯一和从根可达；子节点列表还要查父计数和重复边，并用三色 DFS 把环报告出来。每条错误都定位到节点。

回到主线：树的遍历用到了队列和栈，下一个问题是它们本身怎样实现才不在出队时搬移元素、不把“空”和存入的 `null` 混淆，见[待处理的工作该用队列还是栈，各怎样实现？](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)。

> [!info]- 来源
> - DOM 子节点快照（“遍历一般树”）：[WHATWG DOM Standard, Interface NodeList](https://dom.spec.whatwg.org/#old-style-collections-nodelist)，`childNodes` 返回 live `NodeList`；[ECMAScript 2026, §23.1.2.1 `Array.from`](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.from) 把调用时的迭代结果放进新数组。
> - 对象展开的复制范围（“扁平 parentId 记录”）：[ECMAScript 2026, §7.3.25 CopyDataProperties](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-copydataproperties)，先取全部自有键并检查描述符，只复制可枚举属性，不递归复制值。
> - `Map`/`Set` 只要求平均次线性访问（各节成本）：[ECMAScript 2026, §24.1、§24.2](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)；本章按首章的期望 O(1) 模型计。
> - 防原型键（“三步检查”）：[ECMAScript 2026, `Object.hasOwn`](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-object.hasown) 只判断自有属性。
> - JSON Schema 的关键字作用于单个实例的结构（“两种表示的分工”）：[JSON Schema Draft 2020-12 Validation, §6](https://json-schema.org/draft/2020-12/json-schema-validation)，2026-11-12 核对。
> - React 阶段与并发（“实例：React Fiber”）：[Render and Commit](https://react.dev/learn/render-and-commit)；[React v18.0](https://react.dev/blog/2022/03/29/react-v18)，2022-03-29，并发渲染只在使用并发特性时启用；Fiber 字段见 [ReactInternalTypes.js](https://github.com/facebook/react/blob/main/packages/react-reconciler/src/ReactInternalTypes.js)，2026-11-11 核对。
> - kth 栈表、分类树的三种遍历次序、四行还原与反向输出、断开环的报错、森林改坏表：本页代码在 Node.js v26.13.1 上运行复算。
## 4. 怎样同时按键查找并维护最近使用顺序？

Least Recently Used cache (LRU 缓存，最近最少使用缓存) 满了就淘汰最久没被用过的一项。它要同时做两件事：按键快速找到缓存项，以及随时知道哪一项最久未用。单靠一种结构做不好：哈希表能按键找，却不记顺序；链表能记顺序，按键找却要 O(n)。本章先用 JavaScript `Map` 的插入顺序给出最短的实现，说明它的复杂度为什么证明不了，再用“哈希表 + 双向链表 + 哨兵”给出可以论证的 O(1) 版本。读者手上已有[上一章](#2.%20%E6%95%B0%E7%BB%84%E3%80%81%E9%93%BE%E8%A1%A8%E3%80%81%E6%A0%91%E5%92%8C%E5%93%88%E5%B8%8C%E8%A1%A8%E5%90%84%E9%9D%A0%E4%BB%80%E4%B9%88%E6%89%BE%E5%88%B0%E7%9B%AE%E6%A0%87%E3%80%81%E7%BB%B4%E6%8A%A4%E9%A1%BA%E5%BA%8F%EF%BC%9F)的结论：链表的 O(1) 改链只在已经拿到节点时成立，哈希表按键精确查找、不保序。

### 案例：容量为 2 的页面缓存

一个报表界面在前端缓存用户最近看过的页面。为便于手算，容量设为 2，涉及三个页面：

| 键 | 页面 |
|---|---|
| A | 账户 `acct-17` 报表 42 的某一游标页 |
| B | 同一账户报表 41 的页面 |
| C | 该账户首页 |

操作顺序：`put(A)`、`put(B)` 放满缓存；用户回到 A（`get(A)`）；界面检查 B 是否在缓存里（`has(B)`）；最后打开 C（`put(C)`）。期望结果：淘汰最久未用的 B，保留 A 和 C。

动手之前先约定哪些操作算一次“使用”，因为它决定了淘汰谁：

- 命中的 `get` 算使用，把该项移到最近端；
- `put` 算使用：新键插到最近端，已有键更新值并移到最近端；
- 未命中的 `get` 不改变任何顺序；
- `has` 只检查存在，不算使用。若把 `has(B)` 也算使用，B 就成了最近项，`put(C)` 会淘汰 A。

容量须为非负整数；容量为 0 时 `put` 什么也不保存。缓存最多 c 项时，空间为 O(c)。

### 最短的实现：`Map` 的插入顺序

`Map` 按插入顺序迭代，可以直接当作一条“最旧 → 最新”的队列：

- **刷新**：命中时先 `delete` 再 `set`，键就移到最新一端。只对已有键调用 `set` 会原位更新值，**不**改变位置，所以必须先删。
- **淘汰**：满容量插入新键时，`keys().next()` 给出最旧的键，删掉它。

```javascript
class LRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
    this.capacity = capacity;
    this.cache = new Map();
  }
  has(key) { return this.cache.has(key); }
  get(key) {
    if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }
  put(key, value) {
    if (this.capacity === 0) return;
    if (this.cache.has(key)) this.cache.delete(key);
    else if (this.cache.size === this.capacity) {
      this.cache.delete(this.cache.keys().next().value);
    }
    this.cache.set(key, value);
  }
}
```

> [!example] 容量为 2 的淘汰过程
> | 操作 | 最旧 → 最新 | 返回或淘汰 |
> |---|---|---|
> | `put(A, 页面42)` | A | — |
> | `put(B, 页面41)` | A, B | — |
> | `get(A)` | B, A | 页面 42 |
> | `has(B)` | B, A | `true`，顺序不变 |
> | `put(C, 首页)` | A, C | 淘汰 B |

**键与“未命中”。** 键的相等沿用 `Map` 的 SameValueZero：`NaN` 与自身匹配，`+0` 与 `-0` 是同一个键；对象键按引用比较，内容相同但新建的对象是另一个键。所以用对象描述页面时，先把它规范化成字符串再当键。`get` 未命中返回 `undefined`，与“存了 `undefined`”分不清，需要区分时先调 `has`；“空”的几种表示方式各有什么代价，见[队列与栈一章](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)。

### 为什么 `Map` 版的 O(1) 证明不了

这个版本行为正确，但它的复杂度没有规范保证，原因有三处：

- ECMAScript 只要求 `Map` 的平均键访问时间相对元素数次线性，不承诺 O(1)（主线一统一按期望 O(1) 的模型计，口径见[首章](#%E8%A7%84%E8%8C%83%E4%BF%9D%E8%AF%81%E4%B8%8E%E5%AE%9E%E7%8E%B0%E6%A8%A1%E5%9E%8B)）。
- 插入分支读取 `.size`：规范把这个 getter 描述为逐项统计未删除的条目，没有给出 O(1) 界，引擎可以另外维护计数，但这不是规范承诺。
- `keys().next()` 取最旧键：规范描述的迭代沿插入顺序前进、跳过已删除的项。若引擎用数组式结构存储，反复“删除再插入”可能留下许多待跳过的空位。

规范也说明这份逐项列表只是描述可观察行为的模型，不要求引擎照此实现。所以结论是“证明不了”，不是“一定慢”：实际代价取决于引擎。要得到能论证的 O(1)，就得自己维护顺序。

### 哈希表 + 双向链表：各管一件事

可论证的版本把两件事拆给两种结构：

- `Map` 只负责“键 → 链表节点”；
- 双向链表用 `prev`/`next` 维护新近顺序，表头一侧最近，表尾一侧最久。

为什么这样搭配：拿到节点之后，双向链表把它摘下或插到表头只改固定几个指针；单链表摘除节点需要前驱，而前驱要从头找。节点里还要存自己的键，因为淘汰时是从链表尾拿到节点，再凭 `node.key` 去删 `Map` 里的条目。

**不变量。** 每次操作结束后：

- `head` 与 `tail` 是不进 `Map` 的 sentinel (哨兵) 节点。非空时 `head.next` 是最近使用的节点，`tail.prev` 是最久未使用的节点；空时 `head.next === tail` 且 `tail.prev === head`。
- 每个真实节点在链上恰好出现一次，`Map` 里每个键恰好指向它的节点，两者条目数相同。

哨兵让“在头部插入”和“摘除任一节点”都只有一种写法：真实节点的前后总有一个节点（可能是哨兵），不必为空表、首节点、尾节点分别写分支。

```javascript
class ListNode {
  constructor(key, value) { this.key = key; this.value = value; this.prev = null; this.next = null; }
}

class LinkedLRUCache {
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) {
      throw new RangeError('capacity must be a non-negative integer');
    }
    this.capacity = capacity;
    this.nodes = new Map();
    this.head = new ListNode(null, null);
    this.tail = new ListNode(null, null);
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }
  has(key) { return this.nodes.has(key); }
  get(key) {
    const node = this.nodes.get(key);
    if (!node) return undefined;
    this.#unlink(node);
    this.#insertAfterHead(node);
    return node.value;
  }
  put(key, value) {
    if (this.capacity === 0) return;
    const existing = this.nodes.get(key);
    if (existing) {
      existing.value = value;
      this.#unlink(existing);
      this.#insertAfterHead(existing);
      return;
    }
    if (this.nodes.size === this.capacity) {
      const oldest = this.tail.prev;
      this.#unlink(oldest);
      this.nodes.delete(oldest.key);
    }
    const node = new ListNode(key, value);
    this.nodes.set(key, node);
    this.#insertAfterHead(node);
  }
  #insertAfterHead(node) {
    node.prev = this.head;
    node.next = this.head.next;
    this.head.next.prev = node;
    this.head.next = node;
  }
  #unlink(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }
}
```

调用约定与 `Map` 版相同。下图用同一组操作展示链表和 `Map` 索引；每行是一次操作后的状态，从 `head` 向右按“最近 → 最久”排列，方向与上一节的表相反。`has(B)` 不改变状态，没有单独画出。

![容量为 2 的 LRU 双向链表在 put(A)、put(B) 之后，经 get(A) 和 put(C) 的三种状态](../../engineering-foundations/computation/resources/practical-data-structure-implementations-lru-linked-order.svg)

- **`get(A)`**：`Map` 直接给出 A 的节点。`#unlink(A)` 把 A 的前驱 B 与后继 `tail` 连起来；此时 A 自己的 `prev`/`next` 还指着旧邻居，紧接着的 `#insertAfterHead(A)` 会覆盖它们。完成后 A 在 `head` 之后，B 成为 `tail.prev`。
- **`put(C)`**：缓存已满，`tail.prev` 直接给出最旧的 B；从链上摘下 B，再用 `B.key` 删掉 `Map` 条目；然后创建 C 的节点，登记进 `Map`，插到 `head` 之后。结果是 C、A，与 `Map` 版一致。

**成本。** 已知节点时，摘除和插到表头各改四个以内的指针，从 `tail.prev` 取最旧项是一次访问，这些链表步骤确定是 O(1)，与缓存大小无关。完整的 `get`/`put` 还包括 `Map` 的查找、插入、删除和读取 `.size`；按可扩容哈希表的模型，前三者期望均摊 O(1)，`.size` 按 O(1) 计，于是整次操作期望均摊 O(1)。空间 O(capacity)：每项多一个节点和两条链接。节点分配与垃圾回收的时间不在这个操作计数里。

| | 只用 `Map` | `Map` + 双向链表 |
|---|---|---|
| 刷新命中项 | 删除再重设，顺序由 `Map` 内部维护 | `Map` 定位节点，再改固定几个指针 |
| 满容量淘汰 | `.size` 与 `keys().next()`，都没有规范 O(1) 界 | `.size` 判满，`tail.prev` 即最旧节点 |
| 能论证的界 | 无，取决于引擎 | 期望均摊 O(1)（哈希模型下） |
| 代价 | 代码短、状态少 | 多一组指针和每项一次节点分配 |

**链表在这里为什么不慢。** 链表遍历慢，是因为每一步都要等上一个节点的 `next` 读出来，见[同样是 O(n)，为什么连续扫描往往比链表遍历快？](#13.%20%E5%90%8C%E6%A0%B7%E6%98%AF%20O%28n%29%EF%BC%8C%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)。LRU 从不遍历链表：`Map` 直接给出节点，每次操作只碰这个节点和它的两个邻居。若去掉 `Map` 改为沿链表找键，查找就回到 O(n)，指针追逐也回来了。

### 练习写法里的常见隐患

算法练习里常见一种只用数字键、不用 `Map` 的写法，有几处会改变结果的边界：

- **用 −1 表示未命中，却允许存 −1。** `get` 返回 −1 时分不清是“存的就是 −1”还是“没有这个键”。要么拒绝存哨兵值，要么返回带状态的结果，理由同[队列与栈一章](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)对“空”的讨论。
- **用普通对象当索引。** 属性名都会经 ToPropertyKey 变成字符串，所以数字 `1` 与字符串 `"1"` 是同一个键；没有用 `Object.create(null)` 建对象时，`"constructor"` 这类名字还会命中原型上的属性。`+0`/`-0` 合并、所有 `NaN` 合并则与 `Map` 相同。
- **把文本 ID 转成 Number。** 超出安全整数后不同的 ID 会舍入成同一个值：`Number("9007199254740993")` 得到 `9007199254740992`，与 `9007199254740992` 撞键。ID 应保持字符串。
- **不用哨兵。** 空表时 `head`、`tail` 都是 `null`，只有一个节点时二者指向同一节点；摘除和插入都要为这两种情况写分支，漏一处就会断链。

### 放进真实缓存前：键要包含授权范围

页面内容随账户、权限和查询条件变化时，缓存键必须包含这些维度（账户或授权范围、过滤器、游标），否则一份页面会被交给不该看到它的请求；命中缓存也不替代本次请求的授权检查。本例 A 与 B 只差报表号，但若同一浏览器换了账户登录，`report-42` 这样的短键就会把上一个账户的页面交出去。LRU 结构只决定“满了淘汰谁”，键的维度、写后失效和数据最多旧多久，见[加了缓存之后，读到的数据最多会旧多久？](#30.%20%E5%8A%A0%E4%BA%86%E7%BC%93%E5%AD%98%E4%B9%8B%E5%90%8E%EF%BC%8C%E8%AF%BB%E5%88%B0%E7%9A%84%E6%95%B0%E6%8D%AE%E6%9C%80%E5%A4%9A%E4%BC%9A%E6%97%A7%E5%A4%9A%E4%B9%85%EF%BC%9F)。

### 本章产出与回到主线

LRU 是“按键定位”和“维护顺序”两种需求的组合：`Map` 版靠插入顺序一并解决，行为正确但复杂度只能看引擎；哈希表 + 双向链表 + 哨兵把两件事分开，在哈希模型下每次 `get`/`put` 期望均摊 O(1)，并且先约定好哪些操作算“使用”。被淘汰的项再被读取时只是一次未命中，回源即可。

回到主线：LRU 用链表维护“最近”一端，队列和栈则只按到达先后取出。它们怎样实现才不在出队时搬移元素，见[待处理的工作该用队列还是栈，各怎样实现？](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)。

> [!info]- 来源
> - `Map` 的 SameValueZero 键相等、按插入顺序迭代、已有键 `set` 原位更新而删除后重设会追加到末尾、平均次线性访问要求、`.size` 按列表统计、逐项列表只是可观察语义模型（“最短的实现”“为什么 `Map` 版的 O(1) 证明不了”）：[ECMAScript 2026, §24.1、§24.1.3.3、§24.1.3.11–24.1.3.12、§24.1.5.1](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)。
> - 对象属性名经 ToPropertyKey 转换、安全整数上界（“练习写法里的常见隐患”）：[ECMAScript 2026, §7.1.19 ToPropertyKey](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-topropertykey)、[§21.1.2.6 `Number.MAX_SAFE_INTEGER`](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)。
> - 容量 2 的状态表、两种实现的淘汰结果、`has` 不刷新、`Number("9007199254740993")` 的舍入：本页代码在 Node.js v26.13.1 上运行复算。
## 5. 待处理的工作该用队列还是栈，各怎样实现？

待处理的工作按什么顺序取出，决定了用队列还是栈；选定之后，实现还要回答两个问题：出队时会不会搬移其余元素，以及“容器为空”怎样表示才不会和存进去的 `null`、`undefined` 混淆。本章依次给出链表队列、head 下标数组队列、环形缓冲区和数组栈，并说明显式栈怎样代替递归。读者手上已有[上一章](#2.%20%E6%95%B0%E7%BB%84%E3%80%81%E9%93%BE%E8%A1%A8%E3%80%81%E6%A0%91%E5%92%8C%E5%93%88%E5%B8%8C%E8%A1%A8%E5%90%84%E9%9D%A0%E4%BB%80%E4%B9%88%E6%89%BE%E5%88%B0%E7%9B%AE%E6%A0%87%E3%80%81%E7%BB%B4%E6%8A%A4%E9%A1%BA%E5%BA%8F%EF%BC%9F)对数组与链表定位、改链成本的比较，以及[首章](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)的均摊口径。

### 顺序要求决定用队列还是栈

本章用两个小例子，它们对顺序的要求正好相反：

- **通知消费者**要按到达顺序处理报表事件的通知：`e07` 先到就先处理，然后才是 `e03`。这是 first-in, first-out (FIFO，先进先出) 的 queue (队列)：从尾部加入，从头部取出。
- **表达式解析**处理 `f(a, g(b))` 时，每遇到左括号就记下它，遇到右括号就与最近一个尚未配对的左括号配对。这是 last-in, first-out (LIFO，后进先出) 的 stack (栈)：在同一端加入和取出。

两者的接口都很小（加入、取出、查看下一个、判空），难点在表示：队列要在两端操作，栈只用一端。

### 队列：怎样维护头、尾和空状态？

#### 链表队列

链表队列维护三个字段：`head` 指向最早入队的节点，`tail` 指向最新的节点，`length` 记项数。它的不变量是：

- 空队列时 `head` 与 `tail` 都是 `null`，`length` 为 0；
- 非空时 `tail.next` 是 `null`；
- 取出最后一项时，`head` 变成 `null`，`tail` 也必须同时清空，否则下一次入队会把新节点接到一个已经出队的节点后面。

![两个通知入队后依次出队；删除最后一项时 head 和 tail 都清空](../../engineering-foundations/computation/resources/queue-and-stack-representations-linked-queue.svg)

图中 `e07`、`e03` 两条通知先后入队、出队；第 4 步是上面第三条不变量。

```javascript
class LinkedQueue {
  constructor() {
    this.head = null;
    this.tail = null;
    this.length = 0;
  }
  get isEmpty() { return this.length === 0; }
  enqueue(value) {
    const node = { value, next: null };
    if (this.tail) this.tail.next = node;
    else this.head = node;
    this.tail = node;
    this.length++;
  }
  dequeue() {
    if (this.isEmpty) throw new RangeError('queue is empty');
    const value = this.head.value;
    this.head = this.head.next;
    if (!this.head) this.tail = null;
    this.length--;
    return value;
  }
  peek() {
    if (this.isEmpty) throw new RangeError('queue is empty');
    return this.head.value;
  }
}
```

`enqueue`、`dequeue`、`peek` 都只读写固定几个字段，单次 O(1)；这个界不计节点分配和垃圾回收的耗时。每项要多占一个节点和一个 `next` 引用。空队列上取值直接抛错，判空看 `length` 而不看值，所以 `null` 和 `undefined` 都能作为正常的队列值存入。

#### 用数组做队列：`shift` 为什么是 Θ(n²)，head 下标怎样避免它

JavaScript 里最省事的队列是普通数组，`push` 入队、`shift` 出队。问题在 `shift`：按 ECMAScript 规定的步骤，它要把下标 1 到末尾的每个元素逐个前移一格。对起初有 n 项、之后只出队的普通密集数组，出空整个队列的搬移次数是

(n − 1) + (n − 2) + … + 1 = n(n − 1)/2 = Θ(n²)。

这是规范步骤的抽象计数，引擎不一定真的做这么多次物理复制，但规范也没有承诺更好的界。

更稳妥的做法是不动数组，只让一个 `head` 下标向前走。不变量是：`head` 是 `[0, items.length]` 内的整数，有效队列项恰好是 `items[head..items.length)`；`head === items.length` 时队列为空。

- **出队**：先读 `items[head]`，再把这个槽设为 `undefined` 以释放它对对象的引用，最后 `head++`。一次读、一次写、一次加法，O(1)。
- **判空看下标，不看槽值。** 把槽设为 `undefined` 不会删除这个下标，只说明它已在有效区间之外；存进去的 `undefined` 仍在区间之内，照样能出队。
- **长期运行要压缩。** 只增加 `head` 时，底层数组只增不减。下面的实现在已消费的部分既达到数组长度一半、又不少于 `COMPACT_MIN = 1024` 项时，把剩余的 `items[head..)` 复制到新数组并把 `head` 归零；下限让小队列不必反复复制，代价是已清空的槽可能保留下来：它们要么少于 `COMPACT_MIN` 个，要么不超过剩余项数。每次压缩复制的项数 `items.length − head` 不超过 `head`，也就是自上次压缩以来出队的项数，所以压缩成本摊到每次出队上仍是 O(1)。

![head 从 index 0 推到 1、再推到长度 2；第二个存储值即使是 undefined 仍可出队](../../engineering-foundations/computation/resources/queue-and-stack-representations-head-index-queue.svg)

图中边界输入是 `[null, undefined]`：`head` 远低于压缩下限，所以不会压缩，从 0 推到 1、再到 2，两个值都正常出队，最后 `head` 等于长度，队列为空。

```javascript
const COMPACT_MIN = 1024;

class ArrayQueue {
  constructor() {
    this.items = [];
    this.head = 0;
  }
  get size() { return this.items.length - this.head; }
  enqueue(value) { this.items.push(value); }
  dequeue() {
    if (this.head === this.items.length) throw new RangeError('queue is empty');
    const value = this.items[this.head];
    this.items[this.head] = undefined;
    this.head++;
    if (this.head >= COMPACT_MIN && this.head * 2 >= this.items.length) {
      this.items = this.items.slice(this.head);
      this.head = 0;
    }
    return value;
  }
}
```

一次性的遍历（例如对一棵树或一张图做 BFS，队列用完即弃）只需要 `head` 下标，不必清槽和压缩：用 `for (let head = 0; head < queue.length; head++)` 读队首，循环里继续 `push` 新项即可。

#### 有界队列：环形缓冲区

链表每项分配一个节点，head 下标数组要靠压缩回收空间。如果队列有容量上限，可以改用 ring buffer (环形缓冲区)：一个长度为 `capacity` 的固定数组，槽位循环复用。它只存两个状态：

- `head`：队首所在的槽，取值 `[0, capacity)`；
- `size`：有效项数，取值 `[0, capacity]`。

第 j 项（0 ≤ j < size）在 `items[(head + j) % capacity]`，下一个写入位置 `tail = (head + size) % capacity`。出队读 head 槽、清空它，再令 `head = (head + 1) % capacity`、`size--`；入队写 tail 槽并 `size++`。两者都是常数次操作，O(1)。

关键在空与满的区分：队空和队满时，`tail` 都与 `head` 重合，所以不能用 `head === tail` 判断，只能看 `size`。用通知事件走一遍，状态写作 `(head, size, tail)`，`capacity = 4`（`e21` 是为演示绕回而加的合成事件）：

| 步骤 | 槽 0..3 | `(head, size, tail)` |
|---|---|---|
| `e07`、`e03`、`e11` 已在队 | `e07` `e03` `e11` 空 | (0, 3, 3) |
| 出队 `e07` | 空 `e03` `e11` 空 | (1, 2, 3) |
| 入队 `e18`，写入槽 3 | 空 `e03` `e11` `e18` | (1, 3, 0) |
| 入队 `e21`，绕回槽 0；队满 | `e21` `e03` `e11` `e18` | (1, 4, 1) |
| 依次读完四项 | 全空 | (1, 0, 1) |

最后两行 `head` 与 `tail` 都是 1，一个满、一个空，只有 `size` 能区分。

![容量为 4 的环形队列先出队 e07，再将 e18、e21 写入槽 3 和绕回后的槽 0；队满时 head 与 tail 都指向槽 1](../../engineering-foundations/computation/resources/queue-and-stack-representations-ring-buffer.svg)

队满时有两种策略：拒绝新项（下面的实现返回 `false`，让调用方决定等待、丢弃还是报错），或扩容。扩容按几何倍增时，触发的那一次要把全部项按逻辑顺序复制到新数组，O(capacity)，连续入队均摊 O(1)。服务里的等待队列通常选拒绝：队列有界，满了就把“慢下来”的信号还给生产者，而不是让内存无限增长；这条原则在服务层怎样落成 `429`/`503`，见[容量与准入一章](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)。

> [!example]- 可运行：固定容量的环形队列
> ```javascript
> class RingQueue {
>   constructor(capacity) {
>     if (!Number.isSafeInteger(capacity) || capacity <= 0) {
>       throw new RangeError('capacity must be a positive integer');
>     }
>     this.items = new Array(capacity);
>     this.head = 0;
>     this.size = 0;
>   }
>   get capacity() { return this.items.length; }
>   get tail() { return (this.head + this.size) % this.capacity; }
>   enqueue(value) {
>     if (this.size === this.capacity) return false;
>     this.items[this.tail] = value;
>     this.size++;
>     return true;
>   }
>   dequeue() {
>     if (this.size === 0) throw new RangeError('queue is empty');
>     const value = this.items[this.head];
>     this.items[this.head] = undefined;
>     this.head = (this.head + 1) % this.capacity;
>     this.size--;
>     return value;
>   }
> }
>
> const ring = new RingQueue(4);
> const state = () => `(${ring.head},${ring.size},${ring.tail})`;
> for (const id of ['e07', 'e03', 'e11']) ring.enqueue(id);
> console.log(state());                       // (0,3,3)
> ring.dequeue();         console.log(state()); // (1,2,3)
> ring.enqueue('e18');    console.log(state()); // (1,3,0)
> ring.enqueue('e21');    console.log(state()); // (1,4,1)
> console.log(ring.enqueue('e30'));           // false：队满
> while (ring.size) ring.dequeue();
> console.log(state());                       // (1,0,1)
> ```

#### “空”怎样表示，才不会和存入的值混淆

上面三种队列都在空时抛错，并且判空看计数或下标，而不看取出的值。这是接口设计的一部分：取值操作必须让调用方分清“取到了一个值”和“容器是空的”。常见做法有三种：

| 做法 | 例子 | 能否存 `null`/`undefined` | 调用方要做什么 |
|---|---|---|---|
| 空时抛错 | `dequeue()` 抛 `RangeError` | 能 | 先查 `isEmpty`/`size`，或捕获异常 |
| 返回哨兵值 | 空时 `poll()` 返回 `null` | 存 `null` 后就分不清 | 每次取之前先查 `size` |
| 返回带状态的结果 | `{ ok: true, value }` / `{ ok: false }`；或把值包进记录对象 | 能 | 只看返回值即可判断 |

哨兵值只有在它不可能是合法的存储值时才安全。例如一个只存数字的队列，空时 `poll()` 返回 `null`：如果有人把 `null` 入队，单看返回值就分不清是“取到了 `null`”还是“队列已空”。TypeScript 把参数写成 `number` 能否在编译期挡住 `null`，取决于是否开启 `strictNullChecks`；关闭时 `null` 和 `undefined` 可以赋给任何类型。想让调用方只看返回值就能判断，就返回带状态的结果，或在空时抛错。[堆一章的优先队列](#%E5%AE%9E%E7%8E%B0%EF%BC%9A%E4%B8%80%E4%BB%BD%E4%BA%8C%E5%8F%89%E5%A0%86%EF%BC%8C%E4%B8%89%E7%A7%8D%E7%94%A8%E6%B3%95)用的是第三种做法的变体：空堆返回 `null`，但每个任务都被包在记录对象里，任务值本身为 `null` 时返回的是一个非空的记录。

> [!example]- 对照：空时返回 `null` 哨兵的数字队列（TypeScript）
> ```typescript
> interface QueueNode { val: number; next: QueueNode | null; }
>
> class NullableNumberQueue {
>   private head: QueueNode | null = null;
>   private tail: QueueNode | null = null;
>   private length = 0;
>   offer(val: number): void {
>     const node: QueueNode = { val, next: null };
>     if (this.tail) this.tail.next = node;
>     else this.head = node;
>     this.tail = node;
>     this.length++;
>   }
>   poll(): number | null {           // 空时返回 null：调用方要先查 size
>     if (!this.head) return null;
>     const value = this.head.val;
>     this.head = this.head.next;
>     if (!this.head) this.tail = null;
>     this.length--;
>     return value;
>   }
>   get size(): number { return this.length; }
> }
> ```
> 开启 `strictNullChecks` 时，`offer(null)` 在编译期被拒绝；关闭时它能通过编译，`poll()` 的 `null` 就有了两种含义。

### 栈：怎样保留最近未完成的工作？

栈只在一端操作，用数组末端的 `push`/`pop` 即可。在几何扩容的动态数组模型下，`push` 偶尔因扩容复制而变慢，均摊 O(1)；末尾 `pop` 不移动其他元素，O(1)。和队列一样，下面的 `Stack` 在空时抛错，所以存进去的 `undefined` 不会被误当成空栈。

#### 括号匹配：栈顶就是最近一个未闭合的左括号

扫描文本时，左括号入栈；遇到右括号就看栈顶：栈顶正是最近一个尚未闭合的左括号，类型相符就弹出并记下这一对，否则不匹配。两种失败各有位置：遇到右括号时栈已空或类型不符，错在这个右括号；扫描结束栈里还有项，错在栈顶那个未闭合的左括号。

对 `f(a, g(b))`，各字符下标是 `f`0、`(`1、`a`2、`,`3、空格 4、`g`5、`(`6、`b`7、`)`8、`)`9：

![在 f(a, g(b)) 中，两个左括号依次 push，两个右括号按最近未完成项依次 pop](../../engineering-foundations/computation/resources/queue-and-stack-representations-nested-expression-stack.svg)

图中栈项按它开启的调用标成 `f(`、`g(`；代码里每项记录括号字符和下标。下标 1 的 `(` 入栈，下标 6 的 `(` 入栈；下标 8 的 `)` 弹出 6，得到一对 `[6, 8]`；下标 9 的 `)` 弹出 1，得到 `[1, 9]`，栈变空，匹配成功。

```javascript
class Stack {
  constructor() { this.items = []; }
  get isEmpty() { return this.items.length === 0; }
  push(value) { this.items.push(value); }
  pop() {
    if (this.isEmpty) throw new RangeError('stack is empty');
    return this.items.pop();
  }
  peek() {
    if (this.isEmpty) throw new RangeError('stack is empty');
    return this.items[this.items.length - 1];
  }
}

const OPEN_FOR = new Map([[')', '('], [']', '['], ['}', '{']]);

function matchBrackets(text) {
  const open = new Stack();
  const pairs = [];
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '(' || ch === '[' || ch === '{') {
      open.push({ ch, index: i });
    } else if (OPEN_FOR.has(ch)) {
      if (open.isEmpty || open.peek().ch !== OPEN_FOR.get(ch)) {
        return { ok: false, index: i };
      }
      pairs.push([open.pop().index, i]);
    }
  }
  if (!open.isEmpty) return { ok: false, index: open.peek().index };
  return { ok: true, pairs };
}

console.log(matchBrackets('f(a, g(b))')); // { ok: true, pairs: [ [ 6, 8 ], [ 1, 9 ] ] }
console.log(matchBrackets('f(a, g(b)'));  // { ok: false, index: 1 }：下标 1 的 ( 未闭合
console.log(matchBrackets('f(a])'));      // { ok: false, index: 3 }：] 与栈顶 ( 不符
```

每个字符至多入栈、出栈一次，n 个字符的文本总时间 O(n)，栈空间 O(嵌套深度)。返回的下标是 UTF-16 码元下标；括号都是 ASCII 字符，按码元扫描不会把它们拆错，但若要把位置报告给用户，就要考虑文本单位，见[文本算法应按码元、码点还是字素簇处理？](#9.%20%E6%96%87%E6%9C%AC%E7%AE%97%E6%B3%95%E5%BA%94%E6%8C%89%E7%A0%81%E5%85%83%E3%80%81%E7%A0%81%E7%82%B9%E8%BF%98%E6%98%AF%E5%AD%97%E7%B4%A0%E7%B0%87%E5%A4%84%E7%90%86%EF%BC%9F)。

#### 显式栈怎样代替递归？

括号匹配也可以写成递归下降：每遇到一个左括号就递归调用一次，处理完内层再返回。这样每层嵌套占一帧调用栈，而调用栈的大小由运行时限制，与可用内存无关。在 Node.js v26.13.1 的默认设置下，本页用一个每层递归一次的函数处理 20 万层嵌套的 `((…))`，抛出 `RangeError: Maximum call stack size exceeded`；上面的 `matchBrackets` 处理同一输入正常返回 20 万对。

把递归改成显式栈，就是把调用栈上隐含保存的东西搬到堆上的数组里：

- **栈项存“回来之后要继续做什么”。** 括号匹配只需记住左括号的类型和位置；树的遍历要记住节点，必要时还要记住下一个该处理的孩子或“子树是否已展开”。
- **压栈顺序决定访问顺序。** 栈后进先出，要按从左到右的顺序访问孩子，就把孩子从右到左压栈。
- **空间不变，限制变了。** 显式栈仍要 O(深度) 或更多空间，但它受堆内存约束，而不是受调用栈大小约束；深度随输入增长（退化成链的树、深嵌套的文档、偏斜的快速排序）时应改用显式栈。

递归 DFS 与显式栈 DFS 的对照代码、用显式栈取二叉搜索树的中序第 k 小，见[怎样遍历一棵树，又怎样把扁平记录安全地还原成树？](#3.%20%E6%80%8E%E6%A0%B7%E9%81%8D%E5%8E%86%E4%B8%80%E6%A3%B5%E6%A0%91%EF%BC%8C%E5%8F%88%E6%80%8E%E6%A0%B7%E6%8A%8A%E6%89%81%E5%B9%B3%E8%AE%B0%E5%BD%95%E5%AE%89%E5%85%A8%E5%9C%B0%E8%BF%98%E5%8E%9F%E6%88%90%E6%A0%91%EF%BC%9F)；图搜索中的回溯也沿用这里的规则，见[搜索状态图时，何时永久标记节点，何时必须回退？](#11.%20%E6%90%9C%E7%B4%A2%E7%8A%B6%E6%80%81%E5%9B%BE%E6%97%B6%EF%BC%8C%E4%BD%95%E6%97%B6%E6%B0%B8%E4%B9%85%E6%A0%87%E8%AE%B0%E8%8A%82%E7%82%B9%EF%BC%8C%E4%BD%95%E6%97%B6%E5%BF%85%E9%A1%BB%E5%9B%9E%E9%80%80%EF%BC%9F)。

### 本章产出与下一步

按顺序要求选结构：按到达处理用队列，处理最近未完成的工作用栈。队列在 JavaScript 里不用 `shift` 出队，而是用 head 下标（长期运行时清槽并压缩）或有界的环形缓冲区；判空一律看计数或下标，不看取出的值，空时抛错或返回带状态的结果。嵌套深度随输入增长时，用显式栈代替递归。

队列和栈只按到达先后取出。下一个问题是：任务不断加入、每次要取出优先级最高的一项时，怎样不必每次重新排序？见[不断加入任务时，怎样持续取出最高优先级？](#6.%20%E4%B8%8D%E6%96%AD%E5%8A%A0%E5%85%A5%E4%BB%BB%E5%8A%A1%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%8C%81%E7%BB%AD%E5%8F%96%E5%87%BA%E6%9C%80%E9%AB%98%E4%BC%98%E5%85%88%E7%BA%A7%EF%BC%9F)。

> [!info]- 来源
> - `Array.prototype.pop`/`push`/`shift` 的规范步骤（“用数组做队列”“栈”）：[ECMAScript 2026, §23.1.3.22–23、§23.1.3.27](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)；`shift` 对普通密集数组逐个前移后续下标。标准描述的是可观察步骤，不规定引擎做同样多次物理搬移。
> - 链表实现的栈与队列每次操作最坏常数时间、resizing array 实现任意 N 次操作总时间与 N 成正比（“链表队列”“有界队列”“栈”）：[Sedgewick & Wayne, *Algorithms*, 4th ed., §1.3 Bags, Queues, and Stacks](https://algs4.cs.princeton.edu/13stacks/)、[§1.4 Analysis of Algorithms](https://algs4.cs.princeton.edu/14analysis/)。
> - `strictNullChecks` 关闭时忽略 `null`/`undefined`、开启后作为独立类型检查（“‘空’怎样表示”）：[TypeScript TSConfig Reference: strictNullChecks](https://www.typescriptlang.org/tsconfig/strictNullChecks.html)。
> - 环形缓冲区状态表、`f(a, g(b))` 配对结果、20 万层嵌套的递归与显式栈对比：本页代码在 Node.js v26.13.1 上运行复算。
## 6. 不断加入任务时，怎样持续取出最高优先级？

任务不断到来、每次要取出当前最紧急的一项时，不必每次把全部任务重新排序：priority queue (优先队列) 只要求“插入”和“取出最高优先级”两个操作，binary heap (二叉堆) 只维护父子之间的顺序，就能让两者都在 O(log n) 内完成。本章讲堆序是什么、插入和取出怎样修复它、为什么一次建堆是线性的、同优先级的任务怎样按先到先出，以及怎样用一个固定大小的堆筛出 Top K。读者手上已有[上一章](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)的队列与“空”的表示，以及[首章](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)的成本口径。本章给出的二叉堆是工程基础里唯一的一份实现，图搜索中的 Dijkstra 算法也用它。

### 何时用优先队列，而不是排序

本章换一个独立的小例子：一个后台调度器不断收到待处理任务，每当有执行资源空出来，就取出当前最紧急的一项。如果每次取之前都把整个集合排序一遍，大部分工作花在重复整理那些顺序没变的旧任务上。

判断用哪一种：

- **元素持续到达，每次只要当前极值**：用优先队列。插入和取出各 O(log n)。
- **元素一开始全部已知，最终要完整排序**：直接排序一次更简单。
- **n 很大，只要前 K 名**：用容量为 K 的堆，只保留 K 个候选，见下文 Top K。

### 堆序：数组上的完全二叉树

本章用最大堆：优先级数值越大越紧急。二叉堆是一棵完全二叉树（除最后一层外都填满，最后一层从左向右填），按层从左到右存进数组。用 0 起始下标：

- 下标 `i` 的两个孩子是 `2i + 1` 和 `2i + 2`；
- `i > 0` 的父节点是 `floor((i − 1) / 2)`。

完全二叉树没有空洞，所以不需要指针，下标算术就能找到父子。

heap order (堆序) 只要求一件事：每个父项的优先级不低于它的孩子。比较关系可以传递，沿任何一条路径往上都不会变低，所以根就是全体的最高项。除此之外没有别的顺序：兄弟之间、不同子树之间都没有约定，数组整体也不是排好序的。

例子里有四个任务：A 和 B 的优先级都是 5，A 先到；C 的优先级是 8；D 的优先级是 2。按 A、B、C 的顺序插入后，树形和数组如下（`seq` 是到达序号，下文解释）：

![插入 C 后最大堆的树节点、数组下标和层序数组对应](../../engineering-foundations/computation/resources/heaps-and-priority-queues-array-tree.svg)

箭头只表示父子堆序。C(8) 在根；B(5) 在下标 1、A(5) 在下标 2，两者是兄弟，堆序不规定它们谁在左。

### 插入上浮，取出下沉

堆序被破坏只会发生在一条路径上，修复也只沿这条路径走：

- **插入（上浮）**：新项放在数组末尾，与父项比较；比父项高就交换，继续向上，直到父项不低于它或到达根。
- **取出（下沉）**：记下根，把末项移到根；它与两个孩子中较高的那个比较，孩子更高就交换，继续向下，直到不低于两个孩子或到达叶子。

完整走一遍。同优先级时到达较早者优先（规则见下一节）：

| 操作 | 堆数组（层序） | 发生的修复 |
|---|---|---|
| 插入 A(5) | [A(5)] | 只有根，无需调整 |
| 插入 B(5) | [A(5), B(5)] | B 与父项 A 同为 5，A 先到，不交换 |
| 插入 C(8) | [C(8), B(5), A(5)] | C 放在下标 2，高于父项 A，上浮到根 |
| 插入 D(2) | [C(8), B(5), A(5), D(2)] | D 放在下标 3，低于父项 B，留在原处 |
| 取出 | [A(5), B(5), D(2)] | 返回 C；末项 D 移到根，孩子 B、A 都高于 D，二者同为 5 而 A 先到，D 与右孩子 A 交换 |

n 个节点的完全二叉树高 `H = floor(log₂ n)`，上浮或下沉最多走 H 层。按元素比较和交换次数计，`push` 和 `pop` 都是 O(log n)，`peek` 只读根是 O(1)，堆占 n 个数组槽位。数组追加偶尔触发扩容，按[首章的均摊口径](#%E4%B8%89%E7%A7%8D%E7%95%8C%E5%90%84%E6%89%BF%E8%AF%BA%E4%BB%80%E4%B9%88)计为均摊 O(1)，不改变上面的界。

### 一次建堆为什么是 O(n)

如果元素一开始就全部已知，不必逐个 `push`（累计 O(n log n)），可以自底向上建堆（heapify）：把数组原样当成完全二叉树，从最后一个非叶节点 `floor(n/2) − 1` 开始，向根的方向逐个对每个节点做下沉。处理到某个节点时，它的两棵子树已经是堆，下沉一次就让以它为根的子树也成为堆。

总成本是线性的，因为大多数节点靠近叶子，只能下沉很少几层。高度为 h 的节点至多有 `ceil(n / 2^(h+1))` 个，每个最多下沉 h 层，所以总工作量不超过

Σ_{h=0..H} h · ceil(n / 2^(h+1)) = O(n)。

直观地说：一半节点是叶子，下沉 0 层；四分之一下沉至多 1 层；八分之一至多 2 层……级数 Σ h / 2^(h+1) 收敛到 1，乘以 n 仍是 O(n)。代价是必须一开始就拿到整批元素。

### 同优先级谁先出：次级键与严格弱序

只比较优先级的堆不保证同优先级任务的先后。上浮和下沉在相等时不交换，但取出时末项被移到根再下沉，会打乱同级项的相对位置。要得到“同优先级先到先出”，必须把到达顺序显式写进比较规则：入队时给每项附一个从 0 递增的 `sequence`，只在优先级相等时比较它，序号小的优先。稳定性完全来自这个次级键，而不是堆本身。

比较函数 `higher(a, b)`（a 是否应排在 b 之前）必须构成 strict weak ordering (严格弱序)：

- 没有元素比自身优先；
- 优先关系可传递：a 先于 b、b 先于 c，则 a 先于 c；
- 两项互不优先时视为同档，同档关系也可传递。

此外，元素留在堆中期间，它参与比较的字段不能改变。改了某个任务的优先级而不调整堆，堆序就可能在那一处被破坏，根不再一定是最高项；要么把它删掉重新插入，要么重建整个堆。

`sequence` 在下面的实现里用 BigInt，长期运行也不会越过安全整数上限；它的位数只随累计入队次数的对数增长，比较成本按[首章的数值口径](#%E6%95%B0%E5%80%BC%E8%A1%A8%E7%A4%BA%EF%BC%9A%E5%AE%89%E5%85%A8%E6%95%B4%E6%95%B0%E4%B8%8E%E4%BD%8D%E6%95%B0%E6%88%90%E6%9C%AC)视为近似常数。

### Top K：根是淘汰线

换一组输入：一次收到一批带分数的候选，只返回分数最高的 K 项，同分时先到者优先。思路是反过来用一个最多 K 项的最小堆，让根始终是保留集合里“最差”的一项（分数最低；同分时到得最晚）。根就是淘汰线：

- 堆未满 K 项时，直接插入候选；
- 堆满后，只有候选分数严格高于根时，才取出根、插入候选；与根同分的新候选直接丢弃，因为根比它先到。

依次读入 A(8)、B(5)、C(5)、D(7)、E(1)，K = 3：

| 读入 | 保留集合 | 根（淘汰线） | 动作 |
|---|---|---|---|
| A(8) | A | A(8) | 未满，插入 |
| B(5) | A、B | B(5) | 未满，插入 |
| C(5) | A、B、C | C(5) | 插入后已满；B、C 同分，较晚的 C 是淘汰线 |
| D(7) | A、D、B | B(5) | 7 高于根 5，取出 C、插入 D |
| E(1) | 不变 | B(5) | 1 不高于根，丢弃 |

最后把保留的三项按分数降序、同分按先后排序，得到 A、D、B。

设 `k' = min(K, n)`。扫描 n 个候选，每个至多引起一次规模不超过 k' 的堆调整，共 O(n log(k' + 1)) 次比较（加 1 只是让 k' = 1 时式子不为零，此时每次调整是常数，扫描为 O(n)）；最后对 k' 项排序，按比较排序模型 O(k' log(k' + 1))。同分项由序号明确定序，结果不依赖内置排序是否稳定。额外空间是 O(k')，不含调用方已持有的输入。同样的更新规则也适用于逐项到达的流式输入，全程只保留 K 个候选。若 K 接近 n 且最终要全部排好，直接排序更直接，见[分区怎样改变快速排序的时间和空间代价？](#8.%20%E5%88%86%E5%8C%BA%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E5%BF%AB%E9%80%9F%E6%8E%92%E5%BA%8F%E7%9A%84%E6%97%B6%E9%97%B4%E5%92%8C%E7%A9%BA%E9%97%B4%E4%BB%A3%E4%BB%B7%EF%BC%9F)。

### 实现：一份二叉堆，三种用法

实现分两层，各自的接口边界如下：

- **`BinaryHeap(higher)` 只管结构。** 比较规则由调用者注入，`higher` 不是函数时抛 `TypeError`。最大堆、最小堆、带次级键的稳定堆，都只是换一个 `higher`。
- **空堆返回 `null`，但不会和任务值混淆。** `StableMaxPriorityQueue` 把每个任务包成冻结的记录 `{ priority, sequence, value }` 再入堆，所以非空时 `peek()`/`pop()` 返回的总是一个记录对象；即使任务的 `value` 本身是 `null`，返回值也不是 `null`。这是[上一章“空”的表示](#%E2%80%9C%E7%A9%BA%E2%80%9D%E6%80%8E%E6%A0%B7%E8%A1%A8%E7%A4%BA%EF%BC%8C%E6%89%8D%E4%B8%8D%E4%BC%9A%E5%92%8C%E5%AD%98%E5%85%A5%E7%9A%84%E5%80%BC%E6%B7%B7%E6%B7%86)里“把值包进记录对象”的做法。冻结记录也防止调用方在堆中途改动比较字段。
- **`toArray()` 返回堆布局的浅拷贝，不是排序结果。** `topK` 拿到它之后还要再排序一次。
- **输入校验。** 优先级和分数必须是有限的 Number，`K` 必须是非负安全整数；`topK` 先校验整批输入再开始筛选，返回原对象的引用，不改写输入数组。`topK` 的序号是数组下标，不会越过安全整数，所以用普通 Number。

> [!example]- 可运行：二叉堆、稳定最大优先队列与 Top K
> ```javascript
> class BinaryHeap {
>   constructor(higher) {
>     if (typeof higher !== 'function') throw new TypeError('higher must be a function');
>     this.higher = higher;
>     this.items = [];
>   }
>   get size() { return this.items.length; }
>   peek() { return this.items.length === 0 ? null : this.items[0]; }
>   push(value) {
>     const items = this.items;
>     items.push(value);
>     let i = items.length - 1;
>     while (i > 0) {
>       const parent = Math.floor((i - 1) / 2);
>       if (!this.higher(items[i], items[parent])) break;
>       [items[i], items[parent]] = [items[parent], items[i]];
>       i = parent;
>     }
>   }
>   pop() {
>     const items = this.items;
>     if (items.length === 0) return null;
>     const root = items[0];
>     const last = items.pop();
>     if (items.length > 0) {
>       items[0] = last;
>       let i = 0;
>       while (true) {
>         const left = 2 * i + 1;
>         const right = left + 1;
>         let best = i;
>         if (left < items.length && this.higher(items[left], items[best])) best = left;
>         if (right < items.length && this.higher(items[right], items[best])) best = right;
>         if (best === i) break;
>         [items[i], items[best]] = [items[best], items[i]];
>         i = best;
>       }
>     }
>     return root;
>   }
>   toArray() { return this.items.slice(); }
> }
>
> class StableMaxPriorityQueue {
>   constructor() {
>     this.sequence = 0n;
>     this.heap = new BinaryHeap((a, b) =>
>       a.priority > b.priority ||
>       (a.priority === b.priority && a.sequence < b.sequence)
>     );
>   }
>   get size() { return this.heap.size; }
>   peek() { return this.heap.peek(); }
>   push(priority, value) {
>     if (!Number.isFinite(priority)) throw new TypeError('priority must be finite');
>     this.heap.push(Object.freeze({ priority, sequence: this.sequence, value }));
>     this.sequence += 1n;
>   }
>   pop() { return this.heap.pop(); }
> }
>
> function topK(values, k) {
>   if (!Array.isArray(values)) throw new TypeError('values must be an array');
>   if (!Number.isSafeInteger(k) || k < 0) throw new RangeError('k must be a non-negative safe integer');
>   for (const item of values) {
>     if (!item || !Number.isFinite(item.score)) {
>       throw new TypeError('values must contain items with finite scores');
>     }
>   }
>   if (k === 0 || values.length === 0) return [];
>   const worstFirst = (a, b) =>
>     a.score < b.score || (a.score === b.score && a.sequence > b.sequence);
>   const heap = new BinaryHeap(worstFirst);
>   for (let i = 0; i < values.length; i++) {
>     const candidate = { score: values[i].score, sequence: i, value: values[i] };
>     if (heap.size < k) {
>       heap.push(candidate);
>     } else if (candidate.score > heap.peek().score) {
>       heap.pop();
>       heap.push(candidate);
>     }
>   }
>   return heap.toArray()
>     .sort((a, b) => b.score - a.score || a.sequence - b.sequence)
>     .map(item => item.value);
> }
>
> const tasks = new StableMaxPriorityQueue();
> tasks.push(5, 'A');
> tasks.push(5, 'B');
> tasks.push(8, 'C');
> tasks.push(2, 'D');
> console.log(tasks.pop().value); // C
> console.log(tasks.pop().value); // A
> console.log(tasks.pop().value); // B
> console.log(tasks.pop().value); // D
> console.log(tasks.pop());       // null
>
> const scored = [
>   { id: 'A', score: 8 }, { id: 'B', score: 5 }, { id: 'C', score: 5 },
>   { id: 'D', score: 7 }, { id: 'E', score: 1 },
> ];
> console.log(topK(scored, 3).map(t => t.id)); // [ 'A', 'D', 'B' ]
> console.log(topK(scored, 0));                // []
> ```

### 本章产出与下一步

优先队列用于持续调度：堆只维护父子顺序，插入上浮、取出下沉，各 O(log n)；整批已知时自底向上建堆 O(n)；同级先后靠显式序号和严格弱序。固定大小的堆用于筛选：根是淘汰线，扫描 O(n log K)，只占 O(K) 空间。[图搜索中的 Dijkstra](#11.%20%E6%90%9C%E7%B4%A2%E7%8A%B6%E6%80%81%E5%9B%BE%E6%97%B6%EF%BC%8C%E4%BD%95%E6%97%B6%E6%B0%B8%E4%B9%85%E6%A0%87%E8%AE%B0%E8%8A%82%E7%82%B9%EF%BC%8C%E4%BD%95%E6%97%B6%E5%BF%85%E9%A1%BB%E5%9B%9E%E9%80%80%EF%BC%9F) 用这份堆按当前最短距离取出顶点。

堆只维护部分顺序。当数据整体有序时，可以做得更多：一次比较就排除一半候选，或者让两个指针从两端相向推进。下一个问题是：有序数据怎样让二分查找和双指针安全地排除候选？见[有序数据怎样让二分查找和双指针安全排除候选？](#7.%20%E6%9C%89%E5%BA%8F%E6%95%B0%E6%8D%AE%E6%80%8E%E6%A0%B7%E8%AE%A9%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%E5%AE%89%E5%85%A8%E6%8E%92%E9%99%A4%E5%80%99%E9%80%89%EF%BC%9F)。

> [!info]- 来源
> - 完全二叉树的数组表示、上浮与下沉、插入与删除极值的 O(log n) 界、自底向上 heapify 的线性比较次数（“堆序”“插入上浮，取出下沉”“一次建堆为什么是 O(n)”）：[Sedgewick & Wayne, *Algorithms*, 4th ed., §2.4 Priority Queues](https://algs4.cs.princeton.edu/24pq/)；该书用 1 起始下标，本页改为 0 起始，堆序相同。高度为 h 的节点数上界与求和由本页推导。
> - 用到达序号作次级键实现稳定优先队列（“同优先级谁先出”）：[*Algorithms*, 4th ed., §2.5 的 StableMinPQ.java](https://algs4.cs.princeton.edu/25applications/StableMinPQ.java.html)。
> - `Array.prototype.sort` 的比较器一致性与稳定性（“Top K”最终排序）：[ECMAScript 2026, §23.1.3.30](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)；复杂度按比较排序模型计，口径见首章。
> - 操作表、Top K 表与代码输出由本页在 Node.js v26.13.1 上运行复算。
## 7. 有序数据怎样让二分查找和双指针安全排除候选？

本章回答：数组有序时，二分查找和双指针凭什么一次排除一批候选，边界查找怎样写对，翻页游标为什么就是 `upper_bound`。沿用主线一的案例：报表 42 的事件页已经在内存里，1,024 条事件按 `(occurred_at, event_id)` 升序排列。[首章](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)算过，最坏情况下线性扫描要比较 1,024 次，`lower_bound` 只要 11 次探测；本章说明这 11 次探测为什么不会漏掉答案。

为了能逐轮手算，页面缩成四条演示记录，时间写成同精度的 UTC ISO 8601 字符串（表中只写时分）：

| 下标 | `occurred_at` | `event_id` |
|---:|---|---|
| 0 | `2026-11-12T09:00:00.000Z` | `e07` |
| 1 | `2026-11-12T09:02:00.000Z` | `e03` |
| 2 | `2026-11-12T09:02:00.000Z` | `e11` |
| 3 | `2026-11-12T09:05:00.000Z` | `e18` |

### 排除候选要靠三件事一致

二分查找每看一个中点，就要断定“中点一侧的元素全都不可能是答案”。这个断定要三件事同时成立：

1. **数据顺序**：数组已按某个比较器升序排好。
2. **比较器**：查找用的比较器与排序时的是同一个。它对同一对值总给出相同的正负号，结果可传递，能定义一致的顺序。
3. **返回约定**：调用方知道函数返回的是“某个相等项”“插入位置”还是“下一条”，并按约定使用。

事件页的比较器先比时间，时间相同再比 ID：

~~~javascript
function compareEvent(a, b) {
  if (a.occurred_at < b.occurred_at) return -1;
  if (a.occurred_at > b.occurred_at) return 1;
  if (a.event_id < b.event_id) return -1;
  if (a.event_id > b.event_id) return 1;
  return 0;
}
~~~

这里直接比较字符串，是因为时间都是 UTC、写法和小数位数相同，字典序就等于时间顺序；ID 都是定宽的 `eNN`，字典序也等于编号顺序。换成时区写法不一、小数位数不同的时间串，字典序就不再可靠。

复合键有序不等于每个字段单独有序。`e03` 的 ID 比 `e07` 小，但它发生得更晚，所以排在 `e07` 后面；按 `event_id` 单独看，这个数组并不升序，不能只拿 `event_id` 在上面二分。

> [!warning] 内存比较器必须与数据库排序一致
> 页面由数据库按 `ORDER BY occurred_at, event_id` 返回时，内存里的比较器必须与数据库的字段类型、空值排在前还是后、字符串排序规则（collation）完全一致。任何一项不同，数据库排好的顺序在比较器眼里就可能不是有序的，二分会悄悄给出错误位置。

### 精确查找：目标若存在，必在当前闭区间里

先用便于手算的数字数组说明最简单的形式。闭区间版本维护 `[left, right]`，不变量是“若目标存在，它一定在这个区间里”。区间变空，就说明目标不存在。

~~~javascript
function binarySearch(values, target, compare) {
  let left = 0;
  let right = values.length - 1;
  while (left <= right) {
    const middle = left + Math.floor((right - left) / 2);
    const order = compare(values[middle], target);
    if (order === 0) return middle;
    if (order < 0) left = middle + 1;
    else right = middle - 1;
  }
  return -1;
}
~~~

在 `[3, 7, 11, 15, 19, 23, 27]` 中查找 19，比较器取 `(a, b) => a - b`：

| 轮次 | 闭区间 | 中点下标 → 值 | 动作 |
|---|---|---|---|
| 1 | `[0,6]` | `3 → 15` | `15 < 19`，下标 0–3 都更小，`left = 4` |
| 2 | `[4,6]` | `5 → 23` | `23 > 19`，下标 5–6 都更大，`right = 4` |
| 3 | `[4,4]` | `4 → 19` | 命中，返回 4 |

查找 20 时前两轮相同；第三轮 `19 < 20`，`left = 5`，区间 `[5,4]` 为空，返回 -1。

每次比较至少舍弃一半候选，所以最多 O(log n) 次比较，额外空间 O(1)。有重复项时，这个版本返回任意一个相等项，不一定是第一个；要第一个，用下一节的 `lower_bound`。中点写成 `left + floor((right - left) / 2)`，是为了在定宽整数语言里避免 `left + right` 溢出；JavaScript 的数组长度到不了溢出范围，这样写只是便于移植。

同一个函数配上 `compareEvent` 就能在事件页上精确查找：`binarySearch(events, events[1], compareEvent)` 返回 1。

### 边界查找：lower_bound 与 upper_bound

翻页和插入需要的往往不是“某条记录在哪”，而是“边界在哪”。本领域统一用两个定义：

- `lower_bound(target)`：第一个键 `>= target` 的下标；所有键都小于目标时返回 `n`。
- `upper_bound(target)`：第一个键 `> target` 的下标；没有更大的键时返回 `n`。

> [!info] 半开区间约定
> `[start, end)` 包含满足 `start <= i < end` 的下标：长度是 `end - start`，`start = end` 时为空，相邻的 `[a, b)` 与 `[b, c)` 没有公共元素，位置 `b` 只属于后一个区间。边界查找、滑动窗口、扫描线和分页都按这个约定写，就不用再为“端点算不算”逐处加 ±1。

边界查找要分清两个区间：待探测的元素下标是半开区间 `[lo, hi)`，而答案可能落在闭区间 `[lo, hi]` 的任何位置，包括 `n`。初值 `lo = 0, hi = n`，不变量是：

- `[0, lo)` 里的键都 `< target`；
- `[hi, n)` 里的键都 `>= target`。

中点小于目标时，答案在 `mid` 右侧，令 `lo = mid + 1`；否则 `mid` 本身仍可能是答案，令 `hi = mid`，把它留作右边界。`lo = hi` 时，唯一可能的边界就是结果。`upper_bound` 只改一处：把“等于”也归到左侧，不变量变成 `[0, lo)` 都 `<= target`、`[hi, n)` 都 `> target`。

~~~javascript
function bound(values, target, compare, afterEquals = false) {
  let lo = 0;
  let hi = values.length;
  while (lo < hi) {
    const mid = lo + Math.floor((hi - lo) / 2);
    const order = compare(values[mid], target);
    if (order < 0 || (afterEquals && order === 0)) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}
~~~

`afterEquals` 为 `false` 时是 `lower_bound`，为 `true` 时是 `upper_bound`。在事件页上求 `lower_bound((09:02, e08))`，数组中没有与目标相等的项：

![四条按复合键排序的记录经过两次比较，lower_bound 返回插入位置 2](../../engineering-foundations/computation/resources/algorithms-and-complexity-search.svg)

| 状态 | 探测范围 | 候选边界 | 中点 | 比较与更新 |
|---|---|---|---|---|
| 第 1 轮 | `[0,4)` | `[0,4]` | 2：`(09:02, e11)` | 大于目标，`hi = 2`；下标 2 不再探测，但边界 2 仍保留 |
| 第 2 轮 | `[0,2)` | `[0,2]` | 1：`(09:02, e03)` | 小于目标，`lo = 2` |
| 结束 | `[2,2)` | `[2,2]` | — | 探测范围为空，返回 2 |

结果 2 表示：下标 0、1 的键都小于目标，从下标 2 的 `(09:02, e11)` 起都不小于目标。若比较器只比时间，`e03`、`e08`、`e11` 在它眼里都相等：第 2 轮比较 `e03` 时不再“小于目标”，`hi` 收到 1，最终返回 1，目标被错放到 `e03` 之前。

两个边界版本都从 `[0, n)` 开始，每轮待探测项至多剩一半，所以最多 O(log n) 次键比较、O(1) 额外空间。本例的键是定长字段，一次比较按 O(1) 计；键长随输入增长时，要另计每次比较的成本。

`lower_bound` 本身不表示“找到了”。要找第一条与目标相等的记录，先求 `pos`，再检查 `pos < n && compare(values[pos], target) === 0`；否则 `pos` 指向第一个更大的项，或者等于 `n`。

### 下一页从哪里开始：游标就是 upper_bound

分页时，cursor (游标) 是上一页最后一条记录的完整排序键，下一页应从严格大于游标的第一条开始，这正是 `upper_bound`。以游标 `(09:02, e03)` 为例：

| 调用 | 结果 | 含义 |
|---|---:|---|
| `bound(events, events[1], compareEvent)` | 1 | `lower_bound`：游标自己 |
| `bound(events, events[1], compareEvent, true)` | 2 | `upper_bound`：游标之后的第一条 |

严格边界只依赖排序键，不依赖游标那一行还在不在：即使 `e03` 已被删除，用同一完整排序键比较，仍能定位到第一条更大的记录。

这个结论有一个前提：完整排序键必须能唯一确定每条记录。若两条记录的完整键相同，而游标恰好停在两者之间，严格 `>` 会跳过后一条。所以排序键里要包含唯一的 tie-breaker (平局裁决键)，例子里就是 `event_id`；排序和游标条件都必须用上它。

这里求的只是已加载页内的边界。向数据库取下一页时，查询要用同样的过滤条件、同样的排序和同样严格的游标条件 `(occurred_at, event_id) > (游标时间, 游标 ID)`，否则内存里和数据库里对“下一条”的理解不同。数据库侧怎样用行值比较和索引实现这种翻页、集合在翻页期间变化时怎么办，见[怎样无重复、无遗漏地分页读取一个还在变化的集合？](#29.%20%E6%80%8E%E6%A0%B7%E6%97%A0%E9%87%8D%E5%A4%8D%E3%80%81%E6%97%A0%E9%81%97%E6%BC%8F%E5%9C%B0%E5%88%86%E9%A1%B5%E8%AF%BB%E5%8F%96%E4%B8%80%E4%B8%AA%E8%BF%98%E5%9C%A8%E5%8F%98%E5%8C%96%E7%9A%84%E9%9B%86%E5%90%88%EF%BC%9F)。

无序数组谈不上 lower 或 upper bound。只问某条记录在不在，可以线性扫描；要找有序边界，就得先按同一比较器排序，或改用能维持顺序的数据结构，并把建立有序表示的成本算进去。排序本身的代价见支线[分区怎样改变快速排序的时间和空间代价？](#8.%20%E5%88%86%E5%8C%BA%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E5%BF%AB%E9%80%9F%E6%8E%92%E5%BA%8F%E7%9A%84%E6%97%B6%E9%97%B4%E5%92%8C%E7%A9%BA%E9%97%B4%E4%BB%A3%E4%BB%B7%EF%BC%9F)。

### 双指针：每次移动都要证明跳过的不是答案

二分每步排除一半候选。two pointers (双指针) 用两个只向前或只向内移动的下标，每步至少排除一个候选，把嵌套循环降成一次扫描。它不能替代任意嵌套循环：每移动一次指针，都要说清“被跳过的候选为什么不可能是答案”。

#### 有序数组两数之和

问题：在升序数组中找两个不同下标，使对应值之和等于 `target`。本例假设值和两端之和都在 JavaScript 安全整数范围内（数值口径见[首章](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)）。

移动理由来自有序：

- 两端和小于 `target`：左端已经和剩余候选中最大的值相加仍然不够，它和其他任何右端配对只会更小，左端可以排除。
- 两端和大于 `target`：右端已经和剩余最小的值相加仍然太大，右端可以排除。

~~~javascript
function twoSumSorted(values, target) {
  let left = 0;
  let right = values.length - 1;
  while (left < right) {
    const sum = values[left] + values[right];
    if (sum === target) return [left, right];
    if (sum < target) left++;
    else right--;
  }
  return null;
}
~~~

输入 `[1, 2, 4, 7, 11]`，`target = 9`：

| 步骤 | `left`：值 | `right`：值 | 和 | 排除理由或结果 |
|---|---|---|---:|---|
| 1 | `0:1` | `4:11` | 12 | 过大；11 配任何剩余左值都过大，`right = 3` |
| 2 | `0:1` | `3:7` | 8 | 不足；1 配任何剩余右值都不足，`left = 1` |
| 3 | `1:2` | `3:7` | 9 | 命中，返回 `[1, 3]` |

不变量是“尚未排除的解，两个下标都在 `[left, right]` 内”。每轮至少移动一端，两指针相遇时候选为空，所以 O(n) 时间、O(1) 额外空间。循环条件 `left < right` 保证两个下标不同；值相同的不同下标也能成解，例如 `[2, 2]` 求 4。

数组无序时，极值论证不成立。未排序的 `[3, 1, 2]` 求 3，下标 `[1, 2]` 是解，但这段代码第一轮 3+2=5 过大、第二轮 3+1=4 仍过大，右指针左移两次后与左指针相遇，返回 `null`。先排序再用双指针也可以，但得到的是排序后数组的下标；需要原下标，就要在排序前记下原位置，并把排序成本算进去。

#### 读写指针：不靠排序的原地压缩

另一类双指针不依赖有序，靠的是两个下标划出的分段不变量。问题：把数组中的零移到末尾，保持非零值的相对次序，原地完成。

读指针 `i` 从左到右扫描，写指针 `next` 指向下一个非零值该写入的位置。处理下标 `i` 之前，数组分成三段：`[0, next)` 是已扫描的非零值，顺序与输入相同；`[next, i)` 全是零；`[i, n)` 还没扫描。

- 当前值是零：`next` 不动，这个零并入中间段。
- 当前值非零：与 `next` 处交换后 `next++`。若 `next < i`，非零值写到 `next`，原来那里的零换到 `i`；若 `next === i`，自己和自己交换，数组不变。

~~~javascript
function moveZeros(values) {
  let next = 0;
  for (let i = 0; i < values.length; i++) {
    if (values[i] !== 0) {
      [values[next], values[i]] = [values[i], values[next]];
      next++;
    }
  }
  return values;
}
~~~

以 `[0, 1, 0, 3, 12]` 为例：

| 处理下标 `i` | 处理前 `next` | 操作 | 处理后 | 新 `next` |
|---:|---:|---|---|---:|
| 0 | 0 | 值为 0，跳过 | `[0,1,0,3,12]` | 0 |
| 1 | 0 | 交换下标 0 与 1 | `[1,0,0,3,12]` | 1 |
| 2 | 1 | 值为 0，跳过 | `[1,0,0,3,12]` | 1 |
| 3 | 1 | 交换下标 1 与 3 | `[1,3,0,0,12]` | 2 |
| 4 | 2 | 交换下标 2 与 4 | `[1,3,12,0,0]` | 3 |

时间 O(n)，额外空间 O(1)。判定条件是严格不等于 0（`-0` 也算零）；若 `null`、空字符串也该当作“零”，要改写判定。数组若有空位，读到的 `undefined` 会被当成非零值移动，用之前要先定义这种情况的语义。把“非零”换成“小于基准”，这种读写指针就是排序分区的雏形。

### 有序之后：边界开始向前推进

本章产出三样东西：一个与排序规则一致的复合键比较器；按半开区间约定写出的 `lower_bound` 与 `upper_bound`；以及“游标 = 完整唯一排序键上的 `upper_bound`”这条翻页规则，主线三的键集分页直接用它。两条支线可按需读：排序本身的成本见[分区怎样改变快速排序的时间和空间代价？](#8.%20%E5%88%86%E5%8C%BA%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E5%BF%AB%E9%80%9F%E6%8E%92%E5%BA%8F%E7%9A%84%E6%97%B6%E9%97%B4%E5%92%8C%E7%A9%BA%E9%97%B4%E4%BB%A3%E4%BB%B7%EF%BC%9F)；比较对象换成用户输入的文本时，先要决定按什么单位比较，见[文本算法应按码元、码点还是字素簇处理？](#9.%20%E6%96%87%E6%9C%AC%E7%AE%97%E6%B3%95%E5%BA%94%E6%8C%89%E7%A0%81%E5%85%83%E3%80%81%E7%A0%81%E7%82%B9%E8%BF%98%E6%98%AF%E5%AD%97%E7%B4%A0%E7%B0%87%E5%A4%84%E7%90%86%EF%BC%9F)。

双指针的两端在这里都只在一个静态数组里移动。下一章[边界向前推进时，怎样维护一个有效窗口或活动区间？](#10.%20%E8%BE%B9%E7%95%8C%E5%90%91%E5%89%8D%E6%8E%A8%E8%BF%9B%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E7%BB%B4%E6%8A%A4%E4%B8%80%E4%B8%AA%E6%9C%89%E6%95%88%E7%AA%97%E5%8F%A3%E6%88%96%E6%B4%BB%E5%8A%A8%E5%8C%BA%E9%97%B4%EF%BC%9F)让两端沿到达顺序一起前进，并在边界移动时增量维护窗口和或活动数。

> [!info]- 来源
> - 二分查找在有序数组中比较中点并缩小区间（精确查找与边界查找）：[NIST Dictionary of Algorithms and Data Structures, “binary search”](https://xlinux.nist.gov/dads/HTML/binarySearch.html)。闭区间精确查找、半开边界查找的不变量、四条记录的两轮探测和数字数组的三轮表均按本页代码手算复核。
> - 双指针只在端点单向移动且每步排除成立时为线性扫描：[Antti Laaksonen, *Competitive Programmer’s Handbook*, “Two pointers method”](https://cses.fi/book/book.pdf)。两数之和的排除论证、无序反例与零值压缩状态表按本页代码复算。
> - 时间字符串字典序与时间顺序一致的条件（时区、`Z`/偏移写法和小数位数相同）：[RFC 3339 §5.1 “Ordering”](https://www.rfc-editor.org/rfc/rfc3339.html#section-5.1)。
## 8. 分区怎样改变快速排序的时间和空间代价？

[有序查找章](#7.%20%E6%9C%89%E5%BA%8F%E6%95%B0%E6%8D%AE%E6%80%8E%E6%A0%B7%E8%AE%A9%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%E5%AE%89%E5%85%A8%E6%8E%92%E9%99%A4%E5%80%99%E9%80%89%EF%BC%9F)的二分查找和相向双指针都假设数据已按同一比较器排好；数据无序时，要先付一笔排序成本。本章用 quicksort (快速排序) 说明这笔成本从哪里来：选一个 pivot (基准值)，把输入分成比它小、等于它、比它大的几部分，再递归处理两侧。每次分区后两侧的规模，决定了递归有多深、总共扫描多少元素、同时占用多少内存。

例子换成一组独立的小数组 `[5, 2, 4, 1, 3]`：事件页的复合键会让每一步都多出字段比较，看不清分区本身。

### 三路分区：小于、等于、大于各进一个桶

为了看清中间结果，下面写的是“构造版” quicksort：每次长度大于 1 的调用都新建 `lower`、`equal`、`higher` 三个数组，只递归处理 `lower` 与 `higher`，最后按三段顺序拼接。pivot 取当前数组中间下标处的值；这只是位置上的中间，不保证是数值上的中位数。

~~~javascript
function quickSort(values) {
  if (values.length <= 1) return values;
  const pivot = values[Math.floor(values.length / 2)];
  const lower = [];
  const equal = [];
  const higher = [];
  for (const value of values) {
    if (value < pivot) lower.push(value);
    else if (value > pivot) higher.push(value);
    else equal.push(value);
  }
  return [...quickSort(lower), ...equal, ...quickSort(higher)];
}
~~~

长度为 0 或 1 时直接返回原数组；更长时不修改输入，返回拼接出的新数组。

`[5, 2, 4, 1, 3]` 的中间下标是 2，pivot = 4。扫描过程中三个桶的变化：

| 扫描到 | lower（< 4） | equal（= 4） | higher（> 4） |
|---|---|---|---|
| 开始 | [] | [] | [] |
| 5 | [] | [] | [5] |
| 2 | [2] | [] | [5] |
| 4 | [2] | [4] | [5] |
| 1 | [2,1] | [4] | [5] |
| 3 | [2,1,3] | [4] | [5] |

pivot 自己一定进 `equal`，所以每次调用至少把一个元素移出子问题，两侧递归的输入严格变短，最终一定到达长度 0 或 1 的基例。接着递归处理两侧：

| 当前输入 | pivot（中间下标） | lower | equal | higher |
|---|---:|---|---|---|
| [2,1,3] | 1（下标 1） | [] | [1] | [2,3] |
| [2,3] | 3（下标 1） | [2] | [3] | [] |

自底向上拼接：`quickSort([2,3])` 得 `[2,3]`；`quickSort([2,1,3])` 得 `[...[], 1, ...[2,3]] = [1,2,3]`；回到第一层，`[...[1,2,3], 4, ...[5]] = [1,2,3,4,5]`。

### 分区要求输入构成一致的全序

`<` 和 `>` 能把每个值放进唯一正确的桶，前提是所有值之间有一致的全序。下面几种输入会悄悄破坏这一点：

- **`NaN`**：它与任何值做 `<`、`>` 都得 false，于是被放进 `equal`，混在 pivot 旁边输出；若 pivot 本身恰好是 `NaN`，所有值都进 `equal`，这一层原样输出、不再排序。
- **稀疏数组的空位**：`for...of` 把空位读成 `undefined`，比较时转成 `NaN`，结果同上。
- **混合类型**：数字与字符串等混在一起时会触发隐式转换，各桶不再对应一致的数值顺序。

`±Infinity` 能正常比较；`-0` 和 `+0` 互不小于也互不大于，会进同一个 `equal` 桶。所以这段代码要求输入是没有空位的普通数组，每项都是 `number` 且不是 `NaN`。

### 相等项多时，equal 桶省掉什么

上面的例子没有重复值。换成 `[4, 4, 4]`：一次扫描就把三项都放进 `equal`，两侧递归数组都为空，输出 `[4, 4, 4]`。相等项一旦进了 `equal` 就不再参与递归；数据中有大量相同值时，三路分区避免把同一批值反复送进下一层。

### 时间：看递推式，不只看递归深度

成本口径：统计读过的元素数、比较次数、数组槽位写入数和递归深度；一次数值比较按 O(1) 计，动态数组扩容按几何扩容的摊还模型计（口径见[首章](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)）。长度为 n 的调用扫描 n 项，每项至多比较两次，分区写入 n 项，拼接再复制 n 项，所以一次调用自身的工作是 Θ(n)。

令 `L`、`E`、`R` 分别为三个桶的长度，`L + E + R = n`。只有 `L` 和 `R` 继续递归，于是

`T(n) = T(L) + T(R) + Θ(n)`

三种情形给出不同结论：

| 分区情形 | 每层合计扫描 | 递归深度 | 总扫描量 |
|---|---|---|---|
| 值互不相同（`E = 1`），两侧大致平分 | 至多 n | Θ(log n) | Θ(n log n) |
| 每层固定比例的项进 `equal`，其余两侧大致平衡 | 按几何级数递减 | Θ(log n) | Θ(n) |
| 持续偏斜：每层只少一个值 | n, n−1, n−2, … | Θ(n) | Θ(n²) |

第二行说明不能只凭“深度 Θ(log n)”推出 Θ(n log n)：深度相同，每层的工作量却在缩小。极端情况下，全相等的输入一轮 Θ(n) 扫描就结束。

中间下标并不能防止第三行。合成输入 `[7, 5, 3, 1, 2, 4, 6]` 会让这段实现每次都恰好选中当前最小值：

| 当前输入 | 中点 pivot | 下一轮 higher |
|---|---:|---|
| [7,5,3,1,2,4,6] | 1 | [7,5,3,2,4,6] |
| [7,5,3,2,4,6] | 2 | [7,5,3,4,6] |
| [7,5,3,4,6] | 3 | [7,5,4,6] |
| [7,5,4,6] | 4 | [7,5,6] |
| [7,5,6] | 5 | [7,6] |
| [7,6] | 6 | [7] |

结果依然正确，是 `[1,2,3,4,5,6,7]`；但递推变成 `T(n) = T(n−1) + Θ(n)`，总扫描量 `n + (n−1) + … + 2 = Θ(n²)`，递归深度 Θ(n)。输入很大时，这样的深度还可能超出引擎的调用栈上限。

### 空间：写入总量、峰值和栈深分开算

构造版不是原地排序。分析内存要分开问三件事：整个运行过程一共写了多少槽位；同一时刻最多有多少槽位仍然可达；调用栈有多深。下表假设每个尚未返回的调用帧都还持有它用到的数组：

| 计数口径 | 分区近似平衡 | 持续偏斜 |
|---|---|---|
| 累计槽位写入 | 每层子数组合计 O(n)，共 O(log n) 层：O(n log n) | n + (n−1) + …：Θ(n²) |
| 峰值同时可达槽位 | 活动路径上的数组约为 n、n/2、n/4…，几何和 O(n) | 约为 n、n−1、n−2…，算术和可达 O(n²) |
| 递归帧数 | O(log n) | Θ(n) |

“峰值”是按调用帧仍引用数组估算的槽位数，不是引擎里实测的字节数；变量何时不再被引用、何时回收、数组容量怎样增长，都由运行时决定。

原地实现不建新数组。Sedgewick 与 Wayne 的 `Quick3way` 先随机打乱输入，再在原数组上做三路分区，额外空间只剩递归栈；打乱是为了让依赖输入次序的持续偏斜难以出现。它的下标维护不在本章展开。

### 实际代码用内置排序

日常代码直接调用语言的内置排序。ECMAScript 规定了 `Array.prototype.sort` 的比较器约定和稳定性，但不规定排序算法、比较次数、时间界或额外空间，所以“O(n log n)”只是按某种比较排序估算的成本，不是语言保证（各种保证的口径见[首章](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)）。`sort` 原地修改与 `toSorted` 返回副本的差别、省略比较器时按字符串比较的陷阱，见前端章节的[排序：默认按字符串比较](../../frontend/javascript/arrays-maps-and-sets.md#%E6%8E%92%E5%BA%8F%EF%BC%9A%E9%BB%98%E8%AE%A4%E6%8C%89%E5%AD%97%E7%AC%A6%E4%B8%B2%E6%AF%94%E8%BE%83)。

### 排序成本回到选型

本章产出一条判断：排序的时间和内存由每次分区的平衡程度决定，要分别报告总扫描量、峰值内存和栈深，而不是只写一个 O(n log n)。回到有序查找章，“先排序再二分”的总成本要把这一项算进去；数据只查一次时，线性扫描往往更便宜。主线接着读[边界向前推进时，怎样维护一个有效窗口或活动区间？](#10.%20%E8%BE%B9%E7%95%8C%E5%90%91%E5%89%8D%E6%8E%A8%E8%BF%9B%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E7%BB%B4%E6%8A%A4%E4%B8%80%E4%B8%AA%E6%9C%89%E6%95%88%E7%AA%97%E5%8F%A3%E6%88%96%E6%B4%BB%E5%8A%A8%E5%8C%BA%E9%97%B4%EF%BC%9F)，其中扫描线也要先付一次端点排序的成本。

> [!info]- 来源
> - 三路快速排序把小于、等于、大于基准的项分开，不再递归处理相等项；`Quick3way` 先打乱输入再原地分区：[Robert Sedgewick 与 Kevin Wayne, *Algorithms*, 4th ed., §2.3 “Quicksort”](https://algs4.cs.princeton.edu/23quicksort/index.php)。本页保留数组构造版和中点下标 pivot，用它说明额外数组与偏斜输入的代价；分区表、偏斜表与三种情形的递推按本页代码复算。
> - 空位与非数值比较的行为：[ECMAScript 2026 `%ArrayIteratorPrototype%.next`](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-%arrayiteratorprototype%.next)（按索引读取，空位读为 `undefined`）；[关系运算符](https://tc39.es/ecma262/2026/multipage/ecmascript-language-expressions.html#sec-relational-operators-runtime-semantics-evaluation)（`undefined` 转为 `NaN` 后比较为 false）；[`Number::lessThan`](https://tc39.es/ecma262/2026/multipage/ecmascript-data-types-and-values.html#sec-numeric-types-number-lessthan)（`NaN` 不形成小于关系）。
> - `Array.prototype.sort` 的比较器约定、稳定次序与由实现决定的比较调用序列，规范不规定时间界：[ECMAScript 2026 §23.1.3.30](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)；稳定性自 [ECMAScript 2019 §22.1.3.27](https://tc39.es/ecma262/2019/#sec-array.prototype.sort) 起要求。
## 9. 文本算法应按码元、码点还是字素簇处理？

[有序查找章](#7.%20%E6%9C%89%E5%BA%8F%E6%95%B0%E6%8D%AE%E6%80%8E%E6%A0%B7%E8%AE%A9%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%E5%AE%89%E5%85%A8%E6%8E%92%E9%99%A4%E5%80%99%E9%80%89%EF%BC%9F)的比较器面对的是定宽 ASCII 的事件 ID，“一个字符”没有歧义。用户输入的文本不同：同一段描述里可能有 emoji、组合重音和其他文字，JavaScript 的字符串下标、Unicode 码点和用户眼里的“一个字符”是三种不同的单位。本章用一个独立的小输入 `'A😀e\u0301'` 说明：计数、截取、比较和前缀搜索之前，要先定义按哪种单位处理、是否规范化、匹配契约是什么，再写算法。

### 一个“字符”有三种数法

- **UTF-16 code unit (UTF-16 码元)**：一个 16 位值。补充平面上的字符（如大多数 emoji）用一对 surrogate (代理) 编码，占两个码元。
- **Unicode code point (Unicode 码点)**：Unicode 给每个抽象字符的编号。一个代理对表示一个码点；组合重音本身也是一个独立码点。
- **extended grapheme cluster (扩展字素簇)**：用户感知的一个字符。组合重音通常和前面的基字符合成一个字素簇。

下图把 `'A😀e\u0301'` 按三种单位划分。方框的横向边界对齐 UTF-16 位置，不代表屏幕显示宽度；`◌́` 里的虚线圆只是为了让组合重音看得清。

![A、emoji 与组合重音在码元、码点、字素簇三种粒度下的分组](../../engineering-foundations/computation/resources/text-string-units.svg)

| 部分 | 码元 | 码点 | 字素簇 |
|---|---:|---:|---:|
| `A` | 1 | 1 | 1 |
| `😀`（U+1F600，代理对 `D83D DE00`） | 2 | 1 | 1 |
| `e` + U+0301 | 2 | 2 | 1 |
| 合计 | 5 | 4 | 3 |

三种计数都不等于存储大小。限制请求或字段的字节数，要按明确的编码（如 UTF-8）另算字节。

JavaScript 里三种单位各有对应的 API：

~~~javascript
const sample = 'A😀e\u0301';
sample.length;                                   // 5：UTF-16 码元数
Array.from(sample).length;                       // 4：按码点迭代
const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
Array.from(segmenter.segment(sample), p => p.segment); // ['A', '😀', 'é']
~~~

`Array.from` 和字符串迭代把有效的代理对合成一个元素，孤立的代理单独成为一个元素。`Intl.Segmenter` 的 grapheme 模式按 locale (语言环境) 和运行时实现的规则切字素簇。UAX #29 定义的默认扩展字素簇是可复现的规则，但允许语言或应用 tailor (定制)，所以某个运行时的输出不能等同于当前 UAX #29 每条边界规则。

> [!info] 实例版本
> 本章示例输出在 Node.js v26.13.1（ICU 79.1、Unicode 18.0、CLDR 49.0）上复算；其他运行时的国际化数据版本可能不同。

### 位置也按单位计：跨单位用下标会切坏文本

知道了三种长度，下一个问题是各种 API 返回的位置按哪种单位计：

| 表达式 | 返回值 | 位置单位 |
|---|---:|---|
| `sample.indexOf('e\u0301')` | 3 | 原字符串的码元偏移 |
| `Array.from(sample).indexOf('e')` | 2 | 码点数组下标 |
| Segmenter 分段记录的 `.index`（最后一段） | 3 | 原字符串的码元偏移 |
| 字素簇数组里 `'e\u0301'` 的下标 | 2 | 字素簇数组下标 |

`slice`、`substring` 按码元解释参数，所以码点数组或字素簇数组的下标不能直接传给它们。本例 `sample.slice(2)` 从 😀 的低代理 U+DE00 开始截取，切坏了 emoji；`slice(3)` 才从 `e\u0301` 开始。要在原文里高亮或替换某个元素，应保留原字符串偏移（例如 Segmenter 的 `.index`），或显式建立“数组下标 → 原偏移”的映射。

### 先决定是否规范化，并在明确的边界做

同一个用户可见字符可能有不同的码点序列。预组字符 é（U+00E9）与 `e` 加组合重音看起来相同，逐码点比较却不等：`'é' === 'e\u0301'` 为 false。Unicode 把这种关系叫 canonical equivalence (规范等价)；经 NFC（Normalization Form C）规范化后两者相等。

这是独立于单位的一项决定，按下面几条执行：

1. **决定比较是否按规范等价**。需要时，在明确的处理边界（例如写入键之前、比较之前）调用 `normalize('NFC')`，存入的键和查询走同一条处理链。
2. **不要无意改写原始输入**。要保留用户原文时，规范化的是副本。
3. **偏移只属于产生它的那份字符串**。`'e\u0301'.length` 是 2，`'é'.length` 是 1；规范化副本上的偏移不能直接套回原文。
4. **选对形式**。NFC/NFD 只处理规范等价；NFKC/NFKD 还合并兼容形式（如全角与半角字母），是否适用取决于任务，不能当作显示文本的通用清理。

> [!info] 数字显示：把本地化文本和精确数值分开
> - 显示数值用 `Intl.NumberFormat` 并显式指定 locale：`1234.5` 在 `en-US` 下是 `1,234.5`，在 `de-DE` 下是 `1.234,5`。输出随运行时的国际化数据版本变化，不能当作机器可解析的格式。
> - 精度在进格式化器之前就可能丢掉。`9007199254740993` 超过安全整数上限 2⁵³−1：直接传数字字符串或 BigInt `9007199254740993n`，输出 `9,007,199,254,740,993`；先 `Number('9007199254740993')` 再格式化，输出已是 `…992`。
> - 手写千分位正则 `/\B(?=(\d{3})+(?!\d))/g` 只适用于 ASCII 整数字符串；回溯引擎会在每个位置用前瞻重查后面的数字，不能断言线性。需要明确的线性处理，就从右向左每三位分组再拼接。

> [!info] 大小写：转换、语言规则和折叠是三件事
> - ASCII 大小写互换只适用于 A–Z、a–z，不是跨语言的大小写转换。
> - `toLowerCase()` 用 Unicode 默认小写映射，`toLocaleLowerCase(locale)` 按语言规则映射，两者都可能改变长度：`'İ'.toLowerCase()` 得到 `i` + U+0307 两个码点；`'I'.toLocaleLowerCase('tr')` 得到土耳其语无点 `ı`。
> - case folding (大小写折叠) 专为不区分大小写的比较设计，与转小写不同：`'ß'.toLowerCase()` 仍是 `ß`，Unicode 18 完整默认折叠却把它映射为 `ss`；`ﬃ` 折叠为 `ffi`，`ſ` 折叠为 `s`。ECMAScript 没有通用的 `caseFold()`。
> - 不区分大小写的匹配要先定用默认折叠还是特定语言规则，存储键与查询走同一条链，并规定折叠与规范化的先后和 Unicode 版本。折叠不保证保持规范化形式，契约要求 NFC 时折叠后还要再规范化一次。NFC 本身既不折叠大小写，也不去重音。

### 同一算法换单位，结论会反过来

回文判断是一种从两端向内收的双指针（排除论证见[有序查找章的双指针](#%E5%8F%8C%E6%8C%87%E9%92%88%EF%BC%9A%E6%AF%8F%E6%AC%A1%E7%A7%BB%E5%8A%A8%E9%83%BD%E8%A6%81%E8%AF%81%E6%98%8E%E8%B7%B3%E8%BF%87%E7%9A%84%E4%B8%8D%E6%98%AF%E7%AD%94%E6%A1%88)）。下面两个函数逻辑相同，只是元素单位不同：

~~~javascript
function isPalindrome(units) {
  for (let left = 0, right = units.length - 1; left < right; left++, right--) {
    if (units[left] !== units[right]) return false;
  }
  return true;
}

const byCodePoint = text => isPalindrome(Array.from(text));
const byGrapheme = (text, locale = 'en') => isPalindrome(
  Array.from(new Intl.Segmenter(locale, { granularity: 'grapheme' }).segment(text), p => p.segment)
);

const text = 'e\u0301x\u0301e';
byCodePoint(text); // true：码点序列 e, U+0301, x, U+0301, e 首尾对称
byGrapheme(text);  // false：字素簇 'é', 'x́', 'e' 首尾不同
~~~

是否规范化又是另一项独立决定：`'éxe\u0301'`（首字为预组 é）直接按字素簇比较为 false，因为 U+00E9 与 `e\u0301` 是不同的字符串；先 NFC 变成 `'éxé'` 后再比较为 true。两个函数都不做规范化，也不做大小写折叠。

成本：令 m 为码点数、g 为字素簇数、u 为码元数。码点版生成 m 项数组，至多比较 ⌊m/2⌋ 次，时间和空间 O(m)。字素簇版的分段耗时由 `Intl.Segmenter` 的实现决定，规范没有给出渐近界；分段之后，收集 g 段并按逐码元比较字符串的模型比较，合计 O(u + g)。

### 连续重复：按码点遍历，用结束哨兵结算最后一段

求最长的连续相同字符。按 UTF-16 下标遍历时，`'😀😀A'` 里每个 emoji 会被拆成两个不同的码元，算出的结果是错的；按码点遍历得到 😀、长度 2。

循环多跑一轮到 `i === characters.length`，这个结束哨兵强制结算最后一段；比较用严格大于，长度并列时保留先出现的那段：

~~~javascript
function longestConsecutive(value) {
  const characters = Array.from(value);
  if (characters.length === 0) return { char: '', len: 0 };
  let bestChar = characters[0];
  let bestLength = 1;
  let currentLength = 1;
  for (let i = 1; i <= characters.length; i++) {
    if (i < characters.length && characters[i] === characters[i - 1]) currentLength++;
    else {
      if (currentLength > bestLength) {
        bestLength = currentLength;
        bestChar = characters[i - 1];
      }
      currentLength = 1;
    }
  }
  return { char: bestChar, len: bestLength };
}
~~~

以 `'AABB'` 为例：

| i | 当前项 | 动作 | 当前段 | 最佳段 |
|---:|---|---|---|---|
| 初始 | A | 初始化 | A/1 | A/1 |
| 1 | A | 与前项相同，延长 | A/2 | A/1 |
| 2 | B | 结算 A，从 B 重新开始 | B/1 | A/2 |
| 3 | B | 延长 | B/2 | A/2 |
| 4 | 结束哨兵 | 结算 B；长度相同不覆盖 | — | A/2 |

时间与辅助空间都是 O(m)。

### Trie：按码点共享前缀，匹配契约决定结果

前缀搜索是文本单位与规范化一起起作用的地方：用户键入前缀，系统列出以它开头的标签。Trie (前缀树) 把每个键拆成一串单位，前缀相同的键沿同一条路径向下。本例每条边是一个 Unicode 码点；😀 是一条边，未规范化的组合重音则是另一条独立的边。

先定匹配契约。本例选 NFC：写入的键和查询前缀各自先作 NFC，再判断查询的码点序列是不是某个键的前缀。于是预组 `café` 与 `cafe\u0301` 是同一个键，枚举出的是规范化后的形式。这个选择改变了“前缀”的含义：原键 `'cafe\u0301'` 按原始字符串确实以 `'cafe'` 开头，但它 NFC 后是 `'café'`（末字为 U+00E9），所以用 `'cafe'` 查 Trie 得到 `[]`。NFC 也不折叠大小写，`Report` 不匹配 `report`；要不区分大小写、去重音或合并兼容字符，必须另外定义规则。

每个节点有一张“码点 → 子节点”的 Map 和一个 terminal (键结束) 标记。依次插入下列键后的路径：

| 插入键 | NFC 后的码点路径 | 完整键标记 |
|---|---|---|
| `re` | r → e | e 节点 |
| `report` | 共享 r → e，再接 p → o → r → t | t 节点 |
| `reporter` | 共享 `report`，再接 e → r | 最后的 r |
| `review` | 共享 r → e，再从 v 分支 | w 节点 |
| `café`，再 `cafe\u0301` | NFC 后都走 c → a → f → é | 第二次写入覆盖第一次的值 |
| `😀report` | 😀 → r → e → p → o → r → t | t 节点 |

只有 terminal 为 true 才是完整键；“路径存在”不等于“这段前缀本身是键”。所以 `re` 既是完整键，又有通向 `report` 和 `review` 的分支。

前缀枚举从前缀节点开始做 DFS：先输出当前节点，再访问后代，所以前缀本身若是键会最先出现。子边按 Map 的插入顺序访问，结果不是字典序。DFS 用显式栈（原因见[队列和栈章](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)），每一帧只从子边迭代器取下一条边，不先复制整张子边表。按上表顺序，`keysWithPrefix('re', 3)` 先输出 `re`，沿 p 分支输出 `report`、`reporter`，到 3 条就停，还没访问 v 分支的 `review`。

> [!example]- 可运行：码点 Trie
> ~~~javascript
> class TrieNode {
>   constructor() {
>     this.children = new Map();
>     this.terminal = false;
>     this.value = undefined;
>   }
> }
>
> class CodePointTrie {
>   constructor() { this.root = new TrieNode(); }
>
>   normalizeKey(key) {
>     if (typeof key !== 'string') throw new TypeError('key must be a string');
>     return key.normalize('NFC');
>   }
>
>   nodeFor(normalized) {
>     let node = this.root;
>     for (const codePoint of Array.from(normalized)) {
>       node = node.children.get(codePoint);
>       if (!node) return null;
>     }
>     return node;
>   }
>
>   insert(key, value) {
>     let node = this.root;
>     for (const codePoint of Array.from(this.normalizeKey(key))) {
>       if (!node.children.has(codePoint)) node.children.set(codePoint, new TrieNode());
>       node = node.children.get(codePoint);
>     }
>     node.terminal = true;
>     node.value = value;
>   }
>
>   lookup(key) {
>     const node = this.nodeFor(this.normalizeKey(key));
>     return node !== null && node.terminal ? { found: true, value: node.value } : { found: false };
>   }
>
>   keysWithPrefix(prefix, limit = 20) {
>     if (!Number.isSafeInteger(limit) || limit < 0) throw new RangeError('limit must be a non-negative safe integer');
>     const normalizedPrefix = this.normalizeKey(prefix);
>     const start = this.nodeFor(normalizedPrefix);
>     if (start === null || limit === 0) return [];
>
>     const results = [];
>     const path = [];
>     const stack = [{ node: start, entered: false, children: null }];
>     while (stack.length > 0 && results.length < limit) {
>       const frame = stack[stack.length - 1];
>       if (!frame.entered) {
>         frame.entered = true;
>         if (frame.node.terminal) {
>           results.push(normalizedPrefix + path.join(''));
>           if (results.length === limit) break;
>         }
>         frame.children = frame.node.children.entries();
>       }
>       const next = frame.children.next();
>       if (next.done) {
>         stack.pop();
>         if (stack.length > 0) path.pop();
>       } else {
>         const [codePoint, child] = next.value;
>         path.push(codePoint);
>         stack.push({ node: child, entered: false, children: null });
>       }
>     }
>     return results;
>   }
> }
>
> const trie = new CodePointTrie();
> trie.insert('re', 'prefix is also a complete key');
> trie.insert('report', 'report label');
> trie.insert('reporter', 'reporter label');
> trie.insert('review', 'review label');
> trie.insert('café', 'precomposed spelling');
> trie.insert('cafe\u0301', 'decomposed spelling replaces the same normalized key');
> trie.insert('😀report', 'emoji-prefixed key');
>
> console.log(trie.lookup('café'));             // { found: true, value: 'decomposed spelling replaces the same normalized key' }
> console.log('cafe\u0301'.startsWith('cafe')); // true：原始字符串前缀
> console.log(trie.keysWithPrefix('cafe'));     // []：NFC 后的码点前缀不匹配
> console.log(trie.keysWithPrefix('re', 3));    // ['re', 'report', 'reporter']
> console.log(trie.keysWithPrefix('rep', 10));  // ['report', 'reporter']
> console.log(trie.keysWithPrefix('', 2));      // ['re', 'report']：遍历顺序，不是字典序
> ~~~

### Trie 的成本：规范化单列，limit 不限制访问量

设 NFC 后的键有 m 个码点。插入和精确查找沿 m 条边各做一次 Map 操作，按哈希表期望 O(1) 的模型是期望 O(m)（Map 的规范保证与这个模型的差别见[首章](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)）；插入最多新建 m 个节点。

规范化成本单列为 `T_NFC`，不默认算进 O(m)：ECMAScript 只规定 `normalize` 的结果，不保证线性时间。

前缀枚举：设前缀有 p 个码点，DFS 实际访问 S 个节点，返回的键字符串共 U 个码元。不计规范化，期望时间 O(p + S + U)。`limit` 只限制返回条数，不限制访问的节点数：前缀下可能挂着很长的非完整键链，DFS 要走完它才遇到下一个 terminal。

### 前缀查询：哈希表、有序数组还是 Trie

| 方案 | 能做什么 | 代价 |
|---|---|---|
| 哈希表 | 完整键的精确查找 | 无法直接定位一组前缀候选 |
| 按与匹配契约一致的字典序排序的数组 | 同前缀的键连续：用 `lower_bound(前缀)` 找起点，顺序输出到不再匹配为止 | 插入要维持有序；排序规则必须与匹配契约一致 |
| Trie | 沿前缀直接定位，共享前缀只存一次 | 每个节点和子边 Map 都占内存；只有前缀查询足够频繁才值得 |

无论哪种方案，候选若要按语言习惯排序，还要另定 collation；Trie 的 Map 插入顺序不等于语言排序。

### 单位定下来之后

本章产出一份文本处理契约：按码元、码点还是字素簇计数与切分；位置用哪种偏移保存；在哪个边界作哪种规范化；大小写怎样折叠；前缀匹配比较的是哪种形式。有了它，文本也能像事件键一样交给有序查找、双指针和 Trie。主线接着读[边界向前推进时，怎样维护一个有效窗口或活动区间？](#10.%20%E8%BE%B9%E7%95%8C%E5%90%91%E5%89%8D%E6%8E%A8%E8%BF%9B%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E7%BB%B4%E6%8A%A4%E4%B8%80%E4%B8%AA%E6%9C%89%E6%95%88%E7%AA%97%E5%8F%A3%E6%88%96%E6%B4%BB%E5%8A%A8%E5%8C%BA%E9%97%B4%EF%BC%9F)。

> [!info]- 来源
> - String 的 `length` 是 UTF-16 码元数，字符串迭代按码点，`indexOf`/`slice` 使用码元偏移：[ECMAScript 2026, §22.1.3.9、§22.1.3.22、§22.1.3.36、§22.1.4.1](https://tc39.es/ecma262/2026/multipage/text-processing.html)。
> - Segmenter 的位置是原字符串码元下标，分段记录 `.index` 返回 `startIndex`：[ECMA-402 2026, §§19.6–19.7](https://tc39.es/ecma402/2026/#segmenter-objects)，特别是 §19.7.1 `CreateSegmentDataObject`。字素簇默认边界与可定制性：[UAX #29, Unicode 18.0.0, Revision 49](https://www.unicode.org/reports/tr29/tr29-49.html)，2026-09-01。
> - NFC 规范化 API：[ECMAScript 2026, §22.1.3.15 `String.prototype.normalize`](https://tc39.es/ecma262/2026/multipage/text-processing.html#sec-string.prototype.normalize)；规范等价、NFC/NFD 与 NFKC/NFKD：[UAX #15, Unicode 18.0.0, Revision 58, §§1.1–1.2](https://www.unicode.org/reports/tr15/tr15-58.html)，2026-08-12。
> - 大小写：`toLowerCase` 的默认映射与码点数可能变化：[ECMAScript 2026, §22.1.3.28](https://tc39.es/ecma262/2026/multipage/text-processing.html#sec-string.prototype.tolowercase)；`toLocaleLowerCase` 依语言环境：[ECMA-402 2026, §20.1.2](https://tc39.es/ecma402/2026/#sec-string.prototype.tolocalelowercase)；完整默认折叠（C+F 映射，U+00DF→`ss`、U+FB03→`ffi`、U+017F→`s`），以及折叠不保留规范化形式：[CaseFolding-18.0.0.txt](https://www.unicode.org/Public/18.0.0/ucd/CaseFolding.txt)、[UAX #44, Unicode 18.0.0, Revision 38](https://www.unicode.org/reports/tr44/tr44-38.html)。
> - 数字格式化：[ECMA-402 2026 §16 NumberFormat Objects](https://tc39.es/ecma402/2026/#numberformat-objects)，§16.5.16 `ToIntlMathematicalValue` 说明数值字符串与 BigInt 不先转成 Number；安全整数上限：[ECMAScript 2026 `Number.MAX_SAFE_INTEGER`](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)。
> - 运行复算环境：Node.js v26.13.1，ICU 79.1，Unicode 18.0，CLDR 49.0；只代表该运行时的输出。
> - Trie 的前缀路径、完整键标记和前缀枚举：[Sedgewick 与 Wayne, *Algorithms*, 4th ed., §5.2 “Tries”](https://algs4.cs.princeton.edu/52trie/)；作者的 `TrieST.java` 用 256 路扩展 ASCII，本页改用 Map 子边与码点。Map 迭代按插入顺序、访问只要求平均次线性：[ECMAScript 2026, §24.1 Map Objects](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-map-objects)。
## 10. 边界向前推进时，怎样维护一个有效窗口或活动区间？

[有序查找章](#7.%20%E6%9C%89%E5%BA%8F%E6%95%B0%E6%8D%AE%E6%80%8E%E6%A0%B7%E8%AE%A9%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%E5%AE%89%E5%85%A8%E6%8E%92%E9%99%A4%E5%80%99%E9%80%89%EF%BC%9F)的双指针在一个静态数组里从两端向内收。本章让边界沿时间或到达顺序向前推进，并在推进时增量维护一份状态：窗口里的和，或者此刻活动的任务数。例子是一条独立的合成事件流和一张预约表，要回答三个问题：

1. 连续 k 条事件中，哪一段的净变化最大？（固定宽度的 sliding window (滑动窗口)）
2. 处理耗时累计达到阈值的连续事件段，最短是哪一段？（可变宽度的滑动窗口）
3. 一批预约区间里，同一时刻最多有几个任务占用资源？（sweep line (扫描线)）

区间一律按半开约定 `[start, end)` 写，含义见有序查找章的[半开区间约定](#%E8%BE%B9%E7%95%8C%E6%9F%A5%E6%89%BE%EF%BC%9Alower_bound%20%E4%B8%8E%20upper_bound)。

### 三种方法各依赖什么输入保证

三者都随边界前进维护状态，但对输入的要求不同。先把约束集中写在这里，后文代码只保留会改变结论的检查：

| 方法 | 能否重排输入 | 正确性来自 | 输入前提 |
|---|---|---|---|
| 固定窗口 | 不能，“连续”指到达顺序 | 每步一进一出，窗口宽度不变 | 任意整数，可正可负 |
| 变长窗口 | 不能 | 两种指针移动都可证明不漏解 | **值必须非负**（这是正确性前提，不是输入清洗） |
| 扫描线 | 可以，先排序端点 | 同一时刻的端点按规则整组处理 | 每个区间 `start < end`；同一业务时刻的表示完全相同 |

三段代码都假设输入是稠密数组，数值是 JavaScript 安全整数，中间和也不越界（数值口径见[首章](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)）。业务值若是小数，应先换算成整数的最小单位（例如毫秒、分），而不是把带浮点误差的和当成精确值。

### 固定宽度窗口：移出一项，再加入一项

每条事件记录它对待处理任务数的净变化，任务完成时为负。数组 `[4, -2, 3, 5]`，求连续 3 条的最大净变化。第一段 `[0, 3)` 的和是 4 − 2 + 3 = 5。窗口右移一格得到 `[1, 4)`，不必重新求和：减去移出的 4，加上新进的 5，得 5 − 4 + 5 = 6。

| 窗口 | 下标:值 | 本轮计算 | 和 |
|---|---|---|---:|
| `[0, 3)` | 0:4、1:-2、2:3 | 4 − 2 + 3 | 5 |
| `[1, 4)` | 1:-2、2:3、3:5 | 5 − 4 + 5 | 6 |

~~~javascript
function maxFixedWindowSum(values, k) {
  if (!Number.isSafeInteger(k) || k <= 0) throw new RangeError('k must be a positive integer');
  if (values.length < k) return null; // 没有完整窗口
  let sum = 0;
  for (let i = 0; i < k; i++) sum += values[i];
  let best = sum;
  for (let right = k; right < values.length; right++) {
    sum += values[right] - values[right - k]; // 加入 right，移出 right-k
    if (sum > best) best = sum;
  }
  return best;
}

maxFixedWindowSum([4, -2, 3, 5], 3); // 6
maxFixedWindowSum([], 1);            // null
~~~

`right` 是本轮新加入项的下标；更新后 `sum` 等于窗口 `[right − k + 1, right + 1)` 的和，`best` 是已比较过的完整窗口中的最大和。宽度固定，所以这个做法不要求值非负。时间 O(n)，额外空间 O(1)。

### 变长窗口：两种移动都要能证明不漏解

第二个问题：按事件顺序，找耗时总和至少为 5 ms 的最短连续区间。输入 `[2, 1, 3, 2]`，值都非负，`target = 5`。每轮先加入 `values[right]`，当前窗口是 `[left, right + 1)`；只要和达标，就记录候选，再从左边移出一项，直到不再达标。

| 操作 | 窗口 | 和 | 决定 |
|---|---|---:|---|
| 加入下标 0 | `[0, 1)` | 2 | 未达标，继续扩展 |
| 加入下标 1 | `[0, 2)` | 3 | 未达标，继续扩展 |
| 加入下标 2 | `[0, 3)` | 6 | 达标，记录长度 3；移出下标 0 |
| 移出下标 0 | `[1, 3)` | 4 | 不达标，停止收缩 |
| 加入下标 3 | `[1, 4)` | 6 | 达标，长度 3 不短于已有候选，保留先前值；移出下标 1 |
| 移出下标 1 | `[2, 4)` | 5 | 仍达标，记录长度 2；移出下标 2 |
| 移出下标 2 | `[3, 4)` | 2 | 不达标，停止收缩 |

结果是 `[2, 4)`，即耗时 3 和 2，长度 2。

两个指针都只向前，要说明两种移动都不会跳过答案：

- **收缩可以在第一次不达标时停止**。固定 `right`，左端右移检查的是越来越短的后缀。值都非负，移除一项后和只会保持或变小；一旦低于阈值，再往右只会更小，不可能再达标。
- **`left` 不必回退**。`left` 越过某个起点 s，说明“以 s 开头、到当时 `right` 为止”的达标区间已经比较过；以 s 开头、结束得更晚的区间只会更长，不可能更优。

~~~javascript
function shortestWindowAtLeast(values, target) {
  if (!(target > 0)) throw new RangeError('target must be positive'); // 否则空窗口也“达标”
  for (const value of values) {
    if (value < 0) throw new RangeError('values must be non-negative'); // 正确性前提
  }
  let left = 0;
  let sum = 0;
  let best = null;
  for (let right = 0; right < values.length; right++) {
    sum += values[right];
    while (sum >= target) {
      const length = right + 1 - left;
      if (best === null || length < best.length) best = { start: left, end: right + 1, length };
      sum -= values[left];
      left++;
    }
  }
  return best;
}

shortestWindowAtLeast([2, 1, 3, 2], 5); // { start: 2, end: 4, length: 2 }
shortestWindowAtLeast([1, 2], 5);       // null
~~~

每项至多进入窗口一次、离开一次，时间 O(n)，额外空间 O(1)。长度相同的候选保留先找到的。

入口的非负检查不能省。假如绕过它，在 `[1, -1, 5]`、阈值 5 上照搬同样的移动：整段 `[0, 3)` 和为 5，记录长度 3；移出 1 后和变成 4，停止收缩，最终返回长度 3。而 `[2, 3)` 只含 5，长度 1 才是答案。有了负数，扩展可能让和变小，收缩可能让和变大，“收缩可以停止”的理由就不成立了。

### 扫描线：先排序端点，同一时刻整组处理

第三个问题的输入不是有序的事件流，而是一批不按开始时间排列的预约。三个合成任务：A = `[1, 4)`、B = `[2, 4)`、C = `[4, 6)`，传给函数时故意打乱成 C、A、B。区间半开：任务在开始时刻已占用资源，在结束时刻已释放，所以另一个任务可以恰好在这一刻开始，两者不算重叠。

扫描线把每个区间拆成开始、结束两个端点，按时刻排序后从小到大处理。同一时刻有多个端点时，整组处理：先减去在此结束的 `[a, t)`，再加上从此开始的 `[t, b)`，然后才更新峰值。处理完时刻 t 后，`active` 就是从 t 到下一个端点之前占用资源的任务数。

![A、B、C 三个半开预约区间在时间轴上的位置，以及各端点间的活动任务数](../../engineering-foundations/computation/resources/range-scans-and-active-sets-timeline.svg)

| 时刻 | 结束 | 开始 | 处理后活动数 | 峰值 |
|---:|---|---|---:|---:|
| 1 | — | A | 1 | 1 |
| 2 | — | B | 2 | 2 |
| 4 | A、B | C | 1 | 2 |
| 6 | C | — | 0 | 2 |

峰值是 2。若逐个处理时刻 4 的端点、每处理一个就更新峰值，先处理 C 的开始会让 `active` 暂时变成 3，答案被错误抬高。

~~~javascript
function maxConcurrentHalfOpen(intervals) {
  const events = [];
  for (const { start, end } of intervals) {
    if (!(start < end)) throw new RangeError('each interval must satisfy start < end');
    events.push({ time: start, kind: 1 }, { time: end, kind: -1 });
  }
  events.sort((a, b) => a.time - b.time);

  let active = 0;
  let peak = 0;
  for (let i = 0; i < events.length;) {
    const time = events[i].time;
    let starts = 0;
    let ends = 0;
    for (; i < events.length && events[i].time === time; i++) {
      if (events[i].kind === -1) ends++;
      else starts++;
    }
    active -= ends;   // [start, time) 到此结束
    active += starts; // [time, end) 从此开始
    peak = Math.max(peak, active);
  }
  return peak;
}

maxConcurrentHalfOpen([
  { name: 'C', start: 4, end: 6 },
  { name: 'A', start: 1, end: 4 },
  { name: 'B', start: 2, end: 4 }
]); // 2
~~~

分组依赖 `events[i].time === time` 精确相等。同一业务时刻必须用完全相同的数值表示；若时刻来自不同的浮点运算，先统一换算到同一刻度（如整数毫秒）再扫描。问题只问峰值，所以 `active` 只存数量；要列出此刻是哪些任务，才需要保存任务身份。

### 成本，以及三者和双指针的关系

| 方法 | 时间 | 额外空间 | 主导项 |
|---|---|---|---|
| 固定窗口 | O(n) | O(1) | 一次扫描 |
| 变长窗口 | O(n) | O(1) | 每项进出各一次 |
| 扫描线 | O(n log n) | O(n) | 2n 个端点的排序 |

扫描线生成端点和分组扫描各是 O(n)，总时间由排序决定。这里的 O(n log n) 按[首章](#%E8%A7%84%E8%8C%83%E4%BF%9D%E8%AF%81%E4%B8%8E%E5%AE%9E%E7%8E%B0%E6%A8%A1%E5%9E%8B)约定的比较排序模型计。

两种窗口本质上是有序查找章双指针的延伸：两个下标只向前，每次移动都附带“跳过的不是答案”的论证。差别在于论证的来源。窗口不能改变原序列，正确性来自指针移动的不变量；扫描线先重排端点，正确性来自半开端点的分组规则。

### 从一条序列到一张图

本章产出三种边界推进的写法及各自的前提：固定窗口靠一进一出，变长窗口靠非负值支撑的单调移动，扫描线靠排序后的同刻分组。它们都只沿一条序列前进，每个位置只访问常数次。状态之间一旦有分支和汇合（一个状态能走向多个后继，多条路线又汇到同一点），就得决定哪些状态已经处理过、何时可以永久标记，这是下一章[搜索状态图时，何时永久标记节点，何时必须回退？](#11.%20%E6%90%9C%E7%B4%A2%E7%8A%B6%E6%80%81%E5%9B%BE%E6%97%B6%EF%BC%8C%E4%BD%95%E6%97%B6%E6%B0%B8%E4%B9%85%E6%A0%87%E8%AE%B0%E8%8A%82%E7%82%B9%EF%BC%8C%E4%BD%95%E6%97%B6%E5%BF%85%E9%A1%BB%E5%9B%9E%E9%80%80%EF%BC%9F)的问题。

> [!info]- 来源
> - 固定与变长窗口的双指针推进、每个元素有限次进入和离开：[Antti Laaksonen, *Competitive Programmer’s Handbook*, 2018 draft, §8.1 “Two pointers method”、§8.3 “Sliding window minimum”](https://cses.fi/book/book.pdf)。本页的求和窗口按各自前提推导；负值失效例与三张状态表按本页代码复算。
> - 端点排序后维护活动集合的扫描线：[Sedgewick 与 Wayne, *Algorithms*, 4th ed. 配套网站, “Geometric Intersections”](https://algs4.cs.princeton.edu/93intersection/)，作者实现 [IntervalIntersection.java](https://algs4.cs.princeton.edu/93intersection/IntervalIntersection.java.html)。本页据此按半开预约区间分组端点，只统计活动数量。
> - `Array.prototype.sort` 的比较器约定与实现定义的比较序列，规范未规定 O(n log n)：[ECMAScript 2026, §23.1.3.30](https://tc39.es/ecma262/2026/multipage/indexed-collections.html#sec-array.prototype.sort)。
## 11. 搜索状态图时，何时永久标记节点，何时必须回退？

前几章的边界只沿一条序列前进。状态一旦能分叉、又能汇合，搜索就得回答两个问题：一个“状态”由什么确定；一个状态什么时候可以永久标记为“处理完了”，什么时候只能临时标记、回退时撤销。本章用一张独立的合成路网回答四个问题，它们的差别全在标记什么、何时标记。

### 案例：一张有环、有会合点的路网

站点 S 要把包裹送到 Z。路网是有向图：S 可到 A、B；A 与 B 都通往会合点 T；T 可以回到 S，也可以到 Z。T→S 这条回边让图里出现环，T 让两条路线汇合。

~~~mermaid
flowchart LR
    S((S)) --> A((A))
    S --> B((B))
    A --> T((T))
    B --> T
    T -.->|回边| S
    T --> Z((Z))
~~~

同一张图依次回答：

1. 跳数最少的路线是哪条？（BFS）
2. 不重复经过站点的路线有哪些？（回溯枚举简单路径）
3. 把边读作依赖时，能否排出执行顺序？（拓扑排序）
4. 给路段加上非负耗时后，代价最低的路线是哪条？（Dijkstra）

代码约定：图用 `Map<顶点 ID, 邻居数组>` 表示，每个顶点都是键（没有出边时对应空数组），邻居也必须是图中的键，邻居数组按给定顺序扫描。复杂度假设邻接表已建好，`Map`/`Set` 操作和堆的一次比较按期望 O(1) 计，短 ID 的处理成本视为常数；这个模型与规范保证的差别见[首章](#1.%20%E9%80%89%E7%AE%97%E6%B3%95%E6%97%B6%EF%BC%8C%E5%A4%8D%E6%9D%82%E5%BA%A6%E7%BB%93%E8%AE%BA%E5%9C%A8%E4%BB%80%E4%B9%88%E6%9D%A1%E4%BB%B6%E4%B8%8B%E6%89%8D%E6%88%90%E7%AB%8B%EF%BC%9F)。V 为顶点数，E 为边数。

### 先定状态键

搜索前先决定用什么代表一个状态，也就是 state key (状态键)：两个到达方式若对后续搜索完全等价，就该映射到同一个键。

- 在本例的 BFS 和 Dijkstra 里，站点 ID 就够了：从某站点出发能走哪些边、每条边多少代价，只取决于当前站点，与之前怎么走来无关。
- 如果持有的钥匙、剩余预算这类到达信息会改变后续可走的边，就必须把它们并入状态键，例如 `(站点, 钥匙集合)`。只按站点去重，会把实际不同的状态当成同一个，漏掉答案。
- 枚举简单路径时，一条路线是否合法取决于它已经经过哪些站点，这段历史不能并进全局键里，只能另用 `onPath` 记录当前分支。

[动态规划章](#12.%20%E5%8A%A8%E6%80%81%E8%A7%84%E5%88%92%E6%80%8E%E6%A0%B7%E5%AE%9A%E4%B9%89%E7%8A%B6%E6%80%81%E5%B9%B6%E5%AE%89%E6%8E%92%E6%9B%B4%E6%96%B0%E9%A1%BA%E5%BA%8F%EF%BC%9F)的“状态”是同一个概念：状态只记后续转移需要的信息。

### 标记什么、何时标记：四类搜索对照

四个问题都沿着边扩展候选状态，区别如下。后文每一节展开一行。

| 搜索 | 标记什么 | 何时标记 | 标记会撤销吗 | 前提 | 时间 |
|---|---|---|---|---|---|
| BFS（无权最短路） | 顶点已被发现，并记下首个父节点 | 首次**入队**时 | 不撤销，全局有效 | 只求最少边数 | O(V + E) |
| 回溯（枚举简单路径） | 顶点在当前路径上 | 进入分支时 | **返回时撤销** | 结果数可能指数级 | O(C + L)，见下文 |
| 拓扑排序（Kahn） | 每个顶点剩余的入度 | 前驱出队时减一，归零入队 | 不撤销 | 图无环 | O(V + E) |
| Dijkstra（非负权最短路） | 暂定距离；最终“已定型” | 暂定距离随松弛更新；最小项**出堆**时才定型 | 暂定距离可被改小，定型后不变 | 边权非负 | 惰性堆 O(V + E log E) |

最容易错的是把一行的标记规则搬到另一行：把 BFS 的全局 visited 用于枚举路径会漏路线；在 Dijkstra 里入堆就定型会得到非最优距离。

### BFS：首次入队时全局标记

breadth-first search (BFS，广度优先搜索) 用先进先出队列按层扩展：先处理距 S 一条边的顶点，再处理两条边的。队列里的顶点按发现距离非递减排列，所以一个顶点第一次被发现时，就已经找到了它的最少边数路径。之后再从别的路线到达它，不可能更短，可以全局去重。

用 `parent` 同时记录“已发现”和首个父节点，并在入队时就写入。如果等出队时才标记，同一个顶点可能被不同前驱重复排进队列。

| 处理的顶点 | 新发现的邻居 | 队列（队首→队尾） | `parent` 新增 |
|---|---|---|---|
| S | A、B | A、B | A←S，B←S |
| A | T | B、T | T←A |
| B | T 已发现 | T | — |
| T | S 已发现，Z | Z | Z←T |
| Z | 到达目标 | — | — |

从 Z 沿父节点回溯得到 S→A→T→Z，共 3 条边。若邻接表把 B 放在 A 前，会返回 S→B→T→Z；两条都是最少边数路径，返回哪条由邻接顺序决定。

~~~javascript
const routes = new Map([
  ['S', ['A', 'B']],
  ['A', ['T']],
  ['B', ['T']],
  ['T', ['S', 'Z']],
  ['Z', []]
]);

function shortestUnweightedPath(graph, start, target) {
  if (!graph.has(start) || !graph.has(target)) return null;
  const parent = new Map([[start, null]]); // 同时是全局 visited；所以 null 不能作顶点 ID
  const queue = [start];
  for (let head = 0; head < queue.length; head++) {
    const vertex = queue[head];
    if (vertex === target) break;
    for (const next of graph.get(vertex)) {
      if (parent.has(next)) continue;
      parent.set(next, vertex); // 入队时标记
      queue.push(next);
    }
  }
  if (!parent.has(target)) return null;
  const path = [];
  for (let v = target; v !== null; v = parent.get(v)) path.push(v);
  return path.reverse();
}

shortestUnweightedPath(routes, 'S', 'Z'); // ['S', 'A', 'T', 'Z']
~~~

起点或目标不存在、目标不可达时返回 `null`；起点等于目标时返回 `[start]`。每个顶点入队一次，每条边检查一次，时间 O(V + E)，额外空间 O(V)。出队用递增的 `head` 下标而不是 `shift`，队首前进时不搬移剩余元素，原因见[队列和栈章](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)。

全局 visited 在这里成立，是因为每个顶点只需保留一条最短路线的父节点。这不意味着一个顶点只能出现在一条合法路线上，下一节就是反例。

### 回溯：标记只属于当前路径，返回时撤销

要列出所有不重复经过站点的路线（simple path (简单路径)），S→A→T→Z 和 S→B→T→Z 都应输出。BFS 的 `parent` 只记住了 T 的第一个父节点 A；如果把全局 visited 用于路径枚举，T 经 A 标记后，经 B 到达 T 的分支会被错误剪掉。

backtracking (回溯) 沿候选边选下一站并递归扩展，返回上一层时撤销刚加入的站点。`onPath` 只表示“这个顶点在当前候选路径上”：它拒绝 T→S，因为 S 已在路径里；而回到 S 尝试 B 分支时，A 分支留下的 T 标记已经撤销，T 可以再次进入。

![两个分支中的 path 与 onPath 状态，以及返回时如何撤销标记](../../engineering-foundations/computation/resources/graph-search-and-backtracking-backtrack.svg)

~~~javascript
function allSimplePaths(graph, start, target) {
  const results = [];
  if (!graph.has(start) || !graph.has(target)) return results;
  const path = [start];
  const onPath = new Set([start]);

  function visit(vertex) {
    if (vertex === target) {
      results.push(path.slice());
      return;
    }
    for (const next of graph.get(vertex)) {
      if (onPath.has(next)) continue; // 只有本路径内重复才构成环
      onPath.add(next);
      path.push(next);
      visit(next);
      path.pop();
      onPath.delete(next); // 撤销，让别的分支复用 next
    }
  }

  visit(start);
  return results;
}

allSimplePaths(routes, 'S', 'Z'); // [['S', 'A', 'T', 'Z'], ['S', 'B', 'T', 'Z']]
~~~

结果用顶点序列区分路线，所以邻接数组里不能有重复邻居，否则同一路线会输出两次；若平行边本身代表不同路线，结果里还要记下走的是哪条边。

成本取决于搜索到的分支数，而不是图的大小。在完全有向图中，只算恰好经过全部 V−2 个中间顶点的简单路径就有 (V−2)! 条。令 C 为实际检查的候选边数、L 为复制到结果中的路径总长度，时间是 O(C + L)；即使最终结果很少，搜索也可能探索大量到不了目标的前缀。只需要一条路线时，不要枚举全部路线。递归栈、`path` 与 `onPath` 占 O(V)。图很深时可能超出调用栈，可改用显式栈保存递归状态（见[队列和栈章](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)），但回退时仍必须撤销 `onPath`。

### 拓扑排序：入度归零才可执行

topological sort (拓扑排序) 回答“这些依赖能否排成一个执行顺序”。把边 u→v 读作“u 必须先于 v 完成”。若 T→S 也是依赖，S→A→T→S 就成环：既要求 S 先于 T，又要求 T 先于 S，不存在合法顺序。若 T→S 只是回程路线，就从依赖图中删去它，剩下的是 directed acyclic graph (DAG，有向无环图)。

Kahn 算法为每个顶点维护尚未满足的入边数（入度）。入度为 0 表示现在可以执行；取出它后，每个后继解除一项依赖，归零的进入 ready 队列。删去 T→S 后：

| 操作 | ready 队列 | 输出 | 入度变化 |
|---|---|---|---|
| 初始化 | S | — | S=0，A=1，B=1，T=2，Z=1 |
| 取出 S | A、B | S | A、B：1→0 |
| 取出 A | B | S、A | T：2→1 |
| 取出 B | T | S、A、B | T：1→0 |
| 取出 T | Z | S、A、B、T | Z：1→0 |
| 取出 Z | — | S、A、B、T、Z | — |

~~~javascript
function topologicalOrder(graph) {
  const indegree = new Map(Array.from(graph.keys(), v => [v, 0]));
  for (const neighbors of graph.values()) {
    for (const next of neighbors) indegree.set(next, indegree.get(next) + 1);
  }
  const ready = Array.from(graph.keys()).filter(v => indegree.get(v) === 0);
  const order = [];
  for (let head = 0; head < ready.length; head++) {
    const vertex = ready[head];
    order.push(vertex);
    for (const next of graph.get(vertex)) {
      indegree.set(next, indegree.get(next) - 1);
      if (indegree.get(next) === 0) ready.push(next);
    }
  }
  return order.length === graph.size ? order : null; // null：不存在完整顺序
}

const dependencies = new Map([
  ['S', ['A', 'B']], ['A', ['T']], ['B', ['T']], ['T', ['Z']], ['Z', []]
]);
topologicalOrder(dependencies); // ['S', 'A', 'B', 'T', 'Z']
topologicalOrder(routes);       // null：T→S 使依赖成环
~~~

保留 T→S 时，S、A、B、T、Z 的初始入度是 1、1、1、2、1，ready 队列一开始就为空。返回 `null` 不等于给出了环：剩下的顶点里，S、A、B、T 在环上，Z 只是被环阻塞。

每个顶点和每条边各处理常数次，时间 O(V + E)，额外空间 O(V)。同一时刻入度为 0 的顶点可能不止一个，所以合法的拓扑序可能有多种；本实现的输出顺序取决于 Map 的键顺序和邻接表扫描顺序。业务要求特定顺序时，要显式加优先级规则（例如 ready 换成按优先级出队的堆），不能把任意一个拓扑序当成唯一答案。

### Dijkstra：出堆才定型，过期项跳过

回到路网本身（T→S 仍可走），给每条边加上非负耗时：S→A 为 1，S→B 为 4，A→T 为 6，B→T 为 1，T→S 为 2，T→Z 为 1。BFS 找到的 S→A→T→Z 只有 3 条边，代价却是 1 + 6 + 1 = 8；S→B→T→Z 代价 4 + 1 + 1 = 6。边数最少与代价最低是两个问题。

Dijkstra 算法用最小堆，每次取出暂定距离最小、尚未定型的顶点，对它的每条出边做 relaxation (松弛)：若 `dist[v] + weight < dist[w]`，就更新 w 的距离和前驱，并把新距离压入堆。这里用“惰性”写法：不修改堆中的旧项，距离改善后旧项留在堆里成为过期项，弹出时若其距离不等于当前 `dist`，直接跳过；再用 `settled` 集合保证每个顶点只处理一次。

| 弹出 | 更新 | 堆中待处理（可能含过期项） | 说明 |
|---|---|---|---|
| S:0 | A=1，B=4 | A:1、B:4 | 从源点展开 |
| A:1 | T=7 | B:4、T:7 | 暂时经 A |
| B:4 | T 从 7 改为 5 | T:5、T:7 | 新项入堆，T:7 过期 |
| T:5 | Z=6；S 已定型，跳过 T→S | Z:6、T:7 | Z:6 只是暂定 |
| Z:6 | — | T:7 | Z 此刻才定型 |
| T:7 | — | — | 7 ≠ dist[T]=5，跳过 |

最终距离 `S=0, A=1, B=4, T=5, Z=6`，最短路线 S→B→T→Z。注意 Z 在处理 T 时就有了距离 6，但那时只是入堆；要等 Z:6 作为最小的未定型项出堆，才能确认它是最优值。

**为什么出堆即可定型？** 反证：假设刚弹出的 v 还有一条更短的路线。沿这条路线从源点出发，找到第一条“起点 u 已定型、终点 x 未定型”的边。u 出堆时松弛过 u→x，所以堆中 x 的有效距离不超过这条路线到 x 的长度。边权非负，路线到 x 的前缀不超过整条路线，而整条路线比 `dist[v]` 短，所以 x 的有效项小于 `dist[v]`，x 应先于 v 出堆，矛盾。

这个论证依赖“前缀不超过整条路线”，负权边会破坏它。给图加一条 B→A、权重 −5：A 在距离 1 时已经定型；之后处理 B:4 时，经 B 到 A 的候选是 4 − 5 = −1，但 A 已定型而被跳过，错误地保留了 1。所以实现应先扫描全图，发现负权就拒绝；含负权的图改用 Bellman–Ford 等能处理负边的算法（前提是无负环），不能因为某个负权样例碰巧算对就继续用 Dijkstra。

> [!example]- 可运行：惰性 Dijkstra
> 依赖[堆章](#6.%20%E4%B8%8D%E6%96%AD%E5%8A%A0%E5%85%A5%E4%BB%BB%E5%8A%A1%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%8C%81%E7%BB%AD%E5%8F%96%E5%87%BA%E6%9C%80%E9%AB%98%E4%BC%98%E5%85%88%E7%BA%A7%EF%BC%9F)的二叉堆 `BinaryHeap(higher)`：构造时传入“谁优先”的比较函数，提供 `size`、`push(item)` 和 `pop()`（返回最优先项）。这里传 `(a, b) => a.distance < b.distance`，即最小堆。
>
> ~~~javascript
> function dijkstra(graph, source) {
>   for (const edges of graph.values()) {
>     for (const { to, weight } of edges) {
>       if (!Number.isSafeInteger(weight) || weight < 0) throw new RangeError('weights must be non-negative integers');
>       if (!graph.has(to)) throw new RangeError('every destination must be a graph vertex');
>     }
>   }
>   const distances = new Map(Array.from(graph.keys(), v => [v, Infinity]));
>   const previous = new Map();
>   const settled = new Set();
>   const heap = new BinaryHeap((a, b) => a.distance < b.distance);
>   if (!graph.has(source)) return { distances, previous };
>   distances.set(source, 0);
>   heap.push({ vertex: source, distance: 0 });
>
>   while (heap.size > 0) {
>     const { vertex, distance } = heap.pop();
>     if (distance !== distances.get(vertex) || settled.has(vertex)) continue; // 过期项
>     settled.add(vertex); // 出堆才定型
>     for (const { to, weight } of graph.get(vertex)) {
>       if (settled.has(to)) continue;
>       const candidate = distance + weight;
>       if (candidate < distances.get(to)) {
>         distances.set(to, candidate);
>         previous.set(to, vertex);
>         heap.push({ vertex: to, distance: candidate });
>       }
>     }
>   }
>   return { distances, previous };
> }
>
> function weightedPath({ distances, previous }, source, target) {
>   if (!(distances.get(target) < Infinity)) return null;
>   const path = [target];
>   while (path[path.length - 1] !== source) path.push(previous.get(path[path.length - 1]));
>   return path.reverse();
> }
>
> const weightedRoutes = new Map([
>   ['S', [{ to: 'A', weight: 1 }, { to: 'B', weight: 4 }]],
>   ['A', [{ to: 'T', weight: 6 }]],
>   ['B', [{ to: 'T', weight: 1 }]],
>   ['T', [{ to: 'S', weight: 2 }, { to: 'Z', weight: 1 }]],
>   ['Z', []]
> ]);
> const result = dijkstra(weightedRoutes, 'S');
> console.log(result.distances.get('Z'));         // 6
> console.log(weightedPath(result, 'S', 'Z'));     // ['S', 'B', 'T', 'Z']
> ~~~
>
> `weightedPath` 必须传入运行 `dijkstra` 时的同一个 source；目标不可达时返回 `null`。

成本：每个顶点定型一次并扫描一次出边，所以至多成功松弛 E 次；加上起点，惰性堆最多处理 E + 1 个项，时间 O(V + E log E)，空间 O(V + E)。支持 decrease-key (原地降低键值) 的索引优先队列让每个顶点在堆中只占一项，堆空间降到 O(V)，时间写作 O((V + E) log V)。无论哪种实现，距离表、前驱表、堆项和 `settled` 都必须对应同一张图、同一组边权。

### 状态和顺序都定下来之后

本章产出一条判断规则：先定状态键，再按问题选标记时机——全局最短层次用入队时永久标记，枚举合法路线用路径内标记并在回退时撤销，依赖顺序看入度，非负代价等出堆再定型。拓扑排序还给出一个事实：在无环的状态图上，按拓扑序处理每个状态时，它依赖的状态都已处理完。下一章[动态规划怎样定义状态并安排更新顺序？](#12.%20%E5%8A%A8%E6%80%81%E8%A7%84%E5%88%92%E6%80%8E%E6%A0%B7%E5%AE%9A%E4%B9%89%E7%8A%B6%E6%80%81%E5%B9%B6%E5%AE%89%E6%8E%92%E6%9B%B4%E6%96%B0%E9%A1%BA%E5%BA%8F%EF%BC%9F)正是利用这一点：状态图无环、子问题被反复请求时，按依赖顺序把每个状态算一次并存下来。

> [!info]- 来源
> - 邻接表遍历、BFS 按边数找最短路并在首次发现时记录父边：[Sedgewick 与 Wayne, *Algorithms*, 4th ed., §4.1 “Undirected Graphs”](https://algs4.cs.princeton.edu/41graph/)，作者实现 [BreadthFirstPaths.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/BreadthFirstPaths.java.html)；原理同样适用于本页的有向邻接表。
> - DAG 才有拓扑序与队列版拓扑排序：[*Algorithms*, 4th ed., §4.2 “Directed Graphs”](https://algs4.cs.princeton.edu/42digraph/)，作者实现 [TopologicalX.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/TopologicalX.java.html)。本页采用 Kahn 入度实现。
> - Dijkstra 的非负权前提、松弛与索引优先队列复杂度：[*Algorithms*, 4th ed., §4.4 “Shortest Paths”](https://algs4.cs.princeton.edu/44sp/)，作者实现 [DijkstraSP.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/DijkstraSP.java.html)；惰性重复入堆让堆项与边数同阶：[LazyDijkstraSP.java](https://algs4.cs.princeton.edu/44sp/LazyDijkstraSP.java.html)。
> - 四个问题的状态表、负权反例与输出均按本页代码复算。
## 12. 动态规划怎样定义状态并安排更新顺序？

dynamic programming (动态规划，DP) 把问题拆成有限个状态，每个状态只记录后续转移需要的信息；先写出递推关系和初值，再按依赖顺序把每个状态算一次。这里的“状态”就是[图搜索章](#%E5%85%88%E5%AE%9A%E7%8A%B6%E6%80%81%E9%94%AE)的状态键；状态之间“谁依赖谁”构成一张无环图，计算顺序就是它的一个拓扑序。如果为了省空间复用一个一维数组，还要清楚每个格子此刻存的是哪一轮的值。

本章用三个独立的小例子递进：Fibonacci 数列说明状态怎样消除重复计算；爬楼梯计数说明循环顺序怎样决定“算的是什么”；0/1 背包说明一维数组为什么要倒序更新，以及初值怎样切换问题的语义。

### 重叠子问题：记忆化或自底向上

如果多个递归分支会反复请求同一个子问题，有两种办法避免重算：memoization (记忆化) 把算过的结果存起来复用；自底向上迭代则按依赖顺序依次计算各状态。

Fibonacci 数列 F(0) = 0、F(1) = 1、F(n) = F(n−1) + F(n−2)。朴素递归每次调用分成两支，同一个 F(k) 被算很多次，时间上界 O(2ⁿ)，调用栈深度 O(n)。迭代版每个状态只算一次，并且 F(i) 只依赖前两个状态，所以任何时刻只需保留两个数：

~~~javascript
function fib(n) {
  if (n <= 1) return n;
  let previous = 0; // F(i-2)
  let current = 1;  // F(i-1)
  for (let i = 2; i <= n; i++) {
    [previous, current] = [current, previous + current];
  }
  return current;
}
~~~

进入第 i 轮前，`previous = F(i−2)`、`current = F(i−1)`；这一轮把二者同时推进为 F(i−1)、F(i)。解构赋值先用旧值算出右侧两项，再一起赋给左侧，所以不会读到半更新的值：

| i | 进入时 `(previous, current)` | 本轮之后 | 新的 `current` |
|---:|---|---|---:|
| 2 | (0, 1) | (1, 1) | F(2) = 1 |
| 3 | (1, 1) | (1, 2) | F(3) = 2 |
| 4 | (1, 2) | (2, 3) | F(4) = 3 |
| 5 | (2, 3) | (3, 5) | F(5) = 5 |

这里的 O(n) 数的是加法次数。只有每个数占固定宽度时，它才等于 O(n) 时间、O(1) 额外空间。JavaScript 的 Number 从 F(79) 起就越过安全整数上限、不再精确；换成 BigInt 能保持精确，但 F(n) 的位数随 n 线性增长，O(n) 次加法不再等于 O(n) 时间。两处数值与推导见[首章的数值口径](#%E6%95%B0%E5%80%BC%E8%A1%A8%E7%A4%BA%EF%BC%9A%E5%AE%89%E5%85%A8%E6%95%B4%E6%95%B0%E4%B8%8E%E4%BD%8D%E6%95%B0%E6%88%90%E6%9C%AC)。

### 计数：循环嵌套决定计的是什么

Fibonacci 的状态只有一个维度。爬楼梯再加一个选择：每步可以走 `steps` 中的任一步长，问恰好走到第 n 级有多少种走法。

定义 `ways[total]` 为“依次选择步长、总和恰为 total 的序列数”。`ways[0] = 1` 代表一步不走的空序列。以步长 `step` 结尾的序列数等于 `ways[total − step]`，把各步长的贡献相加即得 `ways[total]`。步长必须互不相同，否则重复的步长会把同一种选择算两次。

~~~javascript
function climbStairs(n, steps) {
  if (new Set(steps).size !== steps.length) throw new RangeError('steps must be distinct');
  const ways = new Array(n + 1).fill(0);
  ways[0] = 1;
  for (let total = 1; total <= n; total++) {   // 外层：目标总和
    for (const step of steps) {                // 内层：最后一步的步长
      if (total >= step) ways[total] += ways[total - step];
    }
  }
  return ways[n];
}
~~~

`steps = [1, 2]`、`n = 3` 时：

| total | 读到的状态 | 各步长贡献 | `ways[total]` |
|---:|---|---|---:|
| 0 | — | 空序列 | 1 |
| 1 | `ways[0] = 1` | step 1：1 | 1 |
| 2 | `ways[1] = 1, ways[0] = 1` | step 1：1；step 2：1 | 2 |
| 3 | `ways[2] = 2, ways[1] = 1` | step 1：2；step 2：1 | 3 |

3 种走法是 1+1+1、1+2、2+1；外层是总和，所以每条有序序列恰好在它的最后一步被加进一次，1+2 与 2+1 算两种。

把两层循环对调（外层遍历步长、内层递增遍历总和），计算的就变成“不计顺序的步长组合数”：每个组合只按步长在 `steps` 中的固定次序计一次，本例得到 2（{1,1,1}、{1,2}）而不是 3。同一个递推式，循环嵌套换了，答案的含义就换了。

边界：空步长数组时，`n = 0` 返回 1（空序列），`n > 0` 返回 0。设步长有 k 个，循环主体执行 n×k 次，`ways` 占 n+1 个槽位；加上步长去重，时间 O((n+1)(k+1))，空间 O(n+k)。

### 0/1 背包：一维数组为什么要倒序

爬楼梯中每个步长可以无限次使用；0/1 背包要求每件物品最多选一次，这个限制正是靠更新顺序保证的。

先用带物品轮次的二维表定义状态：`dp[i][c]` 为只考虑前 i 件物品、总重量不超过 c 时的最大价值，`dp[0][c] = 0`。第 i 件物品重量 w、价值 v：

`dp[i][c] = max(dp[i−1][c], dp[i−1][c−w] + v)`（`c >= w` 时；否则只取前一项）

选当前物品后，剩余容量 `c−w` 的子问题只能用之前的物品，这就是“每件最多一次”。

代码把上一行和当前行压进同一个数组 `best`：处理完前 i 件后，`best[c]` 应等于 `dp[i][c]`。关键是转移读取的 `best[c−w]` 必须还是上一行的值：

- **容量从大到小**：w > 0 时来源 `c−w` 比 c 小，本轮还没轮到它，读到的仍是上一行，当前物品不会被重复选。w = 0 时来源与目标是同一个槽，右侧读到的也是旧值。
- **容量从小到大**：当 `c−w >= w` 时，来源槽本轮已经更新过，可能已含当前物品，于是同一件物品被再选一次。整轮按升序做完，得到的是“每件可无限次选”的完全背包。

~~~javascript
function knapsack(capacity, weights, values) {
  const best = new Array(capacity + 1).fill(0);
  for (let i = 0; i < weights.length; i++) {
    for (let c = capacity; c >= weights[i]; c--) {
      best[c] = Math.max(best[c], best[c - weights[i]] + values[i]);
    }
  }
  return best[capacity];
}
~~~

例：容量 W = 4，两件物品的（重量, 价值）为 (2, 3)、(3, 4)。每格允许不装满：

| 已处理物品 | c=0 | c=1 | c=2 | c=3 | c=4 |
|---|---:|---:|---:|---:|---:|
| 无（初值） | 0 | 0 | 0 | 0 | 0 |
| (2, 3) | 0 | 0 | 3 | 3 | 3 |
| (2, 3)、(3, 4) | 0 | 0 | 3 | 4 | 4 |

最优价值 4：两件合重 5 装不下，只能选价值 4 的那件。若处理第一件时按容量升序更新，c = 2 时先写入 `best[2] = 3`，到 c = 4 再读这个已更新的值，算出 `best[4] = 6`，相当于把唯一一件物品用了两次。

### O(nW) 为什么叫伪多项式

n 件物品、整数容量 W 时，时间 O((n+1)(W+1))，一维数组空间 O(W+1)。这是 pseudo-polynomial (伪多项式) 复杂度：运行时间与 W 的**数值**成正比，而写下 W 只需约 log₂ W 位。按输入长度衡量，W 的编码每多一位，W 可取的最大值就翻倍，工作量也跟着翻倍，所以它不是多项式算法。W 也不能大到运行时无法分配容量数组。

### 初值和顺序决定问题的语义

同一段转移，换初值或换循环方向就换了问题：

| 变体 | 怎样改 | 理由 |
|---|---|---|
| 允许不装满（本例） | 全部初始化为 0 | “什么都不选”价值 0 是合法方案 |
| 必须恰好装满 | 除 `best[0] = 0` 外初始化为“不可达”哨兵，转移跳过不可达来源 | 只有从 0 出发、恰好凑满的状态才可达 |
| 每件可无限次选 | 容量从小到大更新 | 来源槽可以已含当前物品 |

还有几条边界：

- 价值可以为负，但零初值让“不选”合法，负价值物品不会被选。
- W = 0 时零重量物品仍会各处理一次，正价值的零重量物品各取一次。
- 可无限次选时，若有零重量、正价值的物品，最优值没有有限上界。
- 价值改用 BigInt 后，比较与加法的成本还取决于价值的位数。

### 转移次数之外的成本

本章产出一套设计步骤：定义只含必要信息的状态；写出递推与初值；按依赖顺序（状态图的拓扑序）安排循环；复用数组时确认每个读取拿到的是哪一轮的值。DP 的复杂度数的是转移次数，背包表和楼梯表都是在连续数组上的顺序扫描。同样 O(n) 的遍历，换成链表或分散的对象，真实耗时可以差很多，因为数据要从内存搬到 CPU。下一章[同样是 O(n)，为什么连续扫描往往比链表遍历快？](#13.%20%E5%90%8C%E6%A0%B7%E6%98%AF%20O%28n%29%EF%BC%8C%E4%B8%BA%E4%BB%80%E4%B9%88%E8%BF%9E%E7%BB%AD%E6%89%AB%E6%8F%8F%E5%BE%80%E5%BE%80%E6%AF%94%E9%93%BE%E8%A1%A8%E9%81%8D%E5%8E%86%E5%BF%AB%EF%BC%9F)讲复杂度没有数到的这部分成本。

> [!info]- 来源
> - 计数递推、有限容量背包的表格转移与状态定义：[Antti Laaksonen, *Competitive Programmer’s Handbook*, ch. 7 “Dynamic programming”, §7.1 “Coin problem”、§7.4 “Knapsack problems”](https://cses.fi/book/book.pdf)。本页把状态和循环次序具体化到一维数组；Fibonacci、楼梯与背包三张状态表、升序更新的反例按本页代码复算。
> - 背包时间随容量 W 的数值增长、按输入位数不是多项式：同上 §7.4 的 O(nW) 分析；伪多项式的定义按 W 的编码长度推出。
> - F(78) 与 F(79) 相对 `Number.MAX_SAFE_INTEGER` = 2⁵³−1 = 9,007,199,254,740,991 的位置：[ECMAScript 2026 `Number.MAX_SAFE_INTEGER`](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)，数值由 BigInt 复算。
## 13. 同样是 O(n)，为什么连续扫描往往比链表遍历快？

前面各章的复杂度都只数比较、转移或指针更新的次数。本章回答这些次数之外的成本：数据要从内存搬进 CPU，搬多少、何时才知道下一次该读哪里，决定了同样 O(n) 的两种遍历为什么耗时可以差很多。读完应能根据访问模式判断该选连续布局还是节点式布局，并知道 Linux 的侵入式链表省掉了什么、没有省掉什么。

例子独立于主线一的事件页，只为把内存位置画清楚：累计四个时长 `[4, 7, 1, 3]`，和为 15。一份存在数组里；另一份存在链表里，每个节点额外保存 `next` 指针。下文统一用一个教学布局：时长和指针各 8 B，链表节点无填充、共 16 B，cache line (缓存行) 为 64 B，地址都是合成值。图和算例只说明布局与传输量，不是性能测量。

### 复杂度数的是步数，不是搬运

两种遍历都访问 n 项，都是 O(n)。复杂度不表示处理器要传输多少字节、何时知道下一次读取的地址，也不表示要等多少次缓存未命中。

![数组的四个时长共享一条 64 B 缓存行；链表的四个节点各在不同缓存行，前一节点的 next 给出后一节点地址](../../engineering-foundations/computation/resources/memory-hierarchy-and-data-locality-access-layout.svg)

- **数组**：第 i 项地址等于基址加 i × 8 B，不必读完第 i 项就知道第 i+1 项在哪。四项相邻，落在同一条 64 B 缓存行里。
- **链表**：节点 A 的 `next` 是 `0x5080`。处理器要先取得 A 所在的缓存行，读到这个地址，才能发出读取节点 B 的请求；这次读取依赖上一次读取的结果。

> [!example] 同一缓存层的填充次数
> 假设图中涉及的缓存行起初都不在所观察的缓存层，也没有预取抢先填充：
> - 数组：1 次填充，64 B，已包含全部四个时长。
> - 链表：四个节点在四条不同的行，4 次填充，共 4 × 64 = 256 B，而真正用到的只有 4 × 16 = 64 B。
>
> 这只比较这一层的传输量，不是耗时比。链表行分散是人为假设：多个节点若落在同一行，后续节点可以复用那次填充，但仍要先读到当前节点的 `next` 才能确定下一个地址。数组跨越多行时也需要相应更多的填充。

### 延迟与带宽是两种约束

一次内存读取的 latency (延迟) 是从请求发出到数据可用的时间；bandwidth (带宽) 是单位时间能传送的数据量。读取命中 cache (缓存) 时，数据由相应的缓存层提供；未命中就要从更远的缓存层或主存取得。数据到达后，依赖它的指令才能执行。缓存的层数、容量、带宽和延迟随处理器和系统配置变化，代码不能假定固定数值。

两种约束对应两种瓶颈：

- **等得久**：一条依赖链上的每次读取都要等上一次的结果，延迟直接累加。
- **搬不动**：彼此独立的读取可以同时在途、重叠等待，但共享同一份带宽。流式循环若平均每项实际传输 s 字节、可用带宽 B 字节/秒，且已受带宽限制，吞吐上限约为 B/s 项/秒。这个估算不含计算时间，也预测不了一次依赖读取要等多久。

缓存按行取得数据，相邻字节会随同带回；之后访问相邻元素，就有机会直接命中，这是 spatial locality (空间局部性)。短时间内再次使用同一数据，它仍在缓存中的机会较高，这是 temporal locality (时间局部性)。缓存行也是 cache coherence (缓存一致性) 处理的常用粒度，后文的伪共享就发生在这一层。局部性只提高命中机会，不保证命中。

> [!info] 历史：memory wall
> Wulf 与 McKee 在 1995 年指出，处理器速度与内存供数能力的差距在不断扩大，称之为 memory wall (内存墙)。程序在关键路径上等数据或已达带宽上限时，再提高算术吞吐也未必能加速；工作集已在缓存里、或计算量占主导时，内存供数就不一定是瓶颈。

### 数组：下一个地址可以提前算出

~~~c
#include <stddef.h>
#include <stdint.h>

uint64_t sum_array(void) {
    uint64_t durations[] = {4, 7, 1, 3};
    size_t count = sizeof durations / sizeof durations[0];
    uint64_t total = 0;
    for (size_t i = 0; i < count; i++) {
        total += durations[i];
    }
    return total;
}
~~~

`&durations[i]` 的字节地址是基址加 i 乘元素大小。（C 的指针加法本身已按元素大小前进，不能再额外乘一次 `sizeof`。）

本例四项只占一条行，体现的是同一次填充内的空间复用。数组跨越多条行时，处理器不必等当前行返回就能算出后续地址：许多 hardware prefetcher (硬件预取器) 能识别这种规律并提前取数，处理器也可能让多个独立读取同时在途，这种能力常称为 memory-level parallelism (内存级并行，MLP)。

这些只是机会，不是保证。上面的 `total` 有逐次累加依赖；编译器是否展开循环、改用多个累加器，硬件能否同时发出多个读取，取决于编译结果、可用的请求资源和目标处理器。不能只凭代码外形承诺向量化或吞吐量。

### 链表：先拿到 next 才知道下一站

~~~c
#include <stddef.h>
#include <stdint.h>

struct event_node {
    uint64_t duration;
    struct event_node *next;
};

uint64_t sum_events(struct event_node *head) {   /* 假设无环、尾节点 next 为 NULL */
    uint64_t total = 0;
    for (struct event_node *node = head; node != NULL; node = node->next) {
        total += node->duration;
    }
    return total;
}
~~~

每轮从当前节点读 `next`；只有这个值可用后，程序才知道下一个节点的地址。这种 pointer chasing (指针追逐) 让整条链形成地址依赖：节点分散且各行都未命中时，demand load (按需读取) 只能一个接一个地发出，每个依赖都可能暴露一次完整的等待。

这不等于 CPU 整体停住。乱序执行的处理器仍可做链外的独立工作，其他线程或另一条独立的链也能产生在途请求；只是链上的依赖指令仍要等数据，处理器若没有别的就绪工作，等待就会拖慢整体进度。常见的顺序流预取器难以预测任意散布的指针链；部分处理器能识别固定步幅的地址模式，降低有效延迟；software prefetch (软件预取) 是否有益要对目标负载测量。

### 选数组还是链表：看操作、布局和分配

| 操作 | 数组 | 链表 |
|---|---|---|
| 按下标访问 | O(1) | O(n) |
| 按值查找 | O(n)，连续扫描；有序时可二分 | O(n)，指针追逐 |
| 中间插入或删除 | O(n) 移动，但移动范围连续，可用优化过的批量操作 | 已持有目标节点和所需链接时 O(1)；需先扫描定位时整体仍 O(n) |
| 分配 | 整块分配，扩容时整体搬移 | 每个节点一次分配；对象池能降低分配成本，但不保证链表顺序就是地址顺序 |

所以，主要工作是按顺序扫描时，连续数组常是更好的起点；系统频繁改动已知节点、要求节点地址稳定，或同一对象要参加多个关系时，链表才可能更合适。节点大小、未命中次数、锁竞争和访问顺序都会改变实际成本，结论要用代表性的数据规模和访问模式测量。Linux 内核文档也提醒，能满足需求的简单数组通常有更好的数据局部性。

“频繁改动已知节点”的典型例子是 LRU 缓存：哈希表按键直接给出节点，节点又持有前驱和后继，所以把它移到最近使用端只需有限次链接更新；没有这个索引而要遍历链表找键，查找仍是 O(n)，指针追逐也没有消失。完整结构见[怎样同时按键查找并维护最近使用顺序？](#4.%20%E6%80%8E%E6%A0%B7%E5%90%8C%E6%97%B6%E6%8C%89%E9%94%AE%E6%9F%A5%E6%89%BE%E5%B9%B6%E7%BB%B4%E6%8A%A4%E6%9C%80%E8%BF%91%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F)；各结构靠什么定位、怎样维护顺序，见[数组、链表、树和哈希表各靠什么找到目标、维护顺序？](#2.%20%E6%95%B0%E7%BB%84%E3%80%81%E9%93%BE%E8%A1%A8%E3%80%81%E6%A0%91%E5%92%8C%E5%93%88%E5%B8%8C%E8%A1%A8%E5%90%84%E9%9D%A0%E4%BB%80%E4%B9%88%E6%89%BE%E5%88%B0%E7%9B%AE%E6%A0%87%E3%80%81%E7%BB%B4%E6%8A%A4%E9%A1%BA%E5%BA%8F%EF%BC%9F)。

### 实例：各语言的“数组”保证什么布局

写下“数组”不等于得到连续内存。以下按各语言标准或实现文档核对（2026-11-11）：

| 语言或类型 | 布局保证 |
|---|---|
| C 数组 | 元素连续；多维数组按行优先排列 |
| C++ `std::vector<T>`（`T` 非 `bool`） | 连续存储 |
| C++ `std::vector<bool>` | 专门化，不属于上面的连续保证 |
| C++ `std::list<T>` | 标准只规定操作、迭代器与复杂度，不规定节点布局 |
| JavaScript `Array` | 规范只定义索引属性、长度和操作行为，不承诺连续存储；V8 用 packed、holey 等元素种类优化常见数组，这是实现状态，不是语言承诺 |
| JavaScript `TypedArray` | 以固定数值类型查看 `ArrayBuffer` 的一段字节；程序仍无法据此推断物理地址或缓存行 |

### 访问模式还影响哪些选择

同一视角能解释许多看似无关的选择。它们是定位瓶颈的线索，不是脱离负载的通用结论：

| 选择 | 访问模式上的差别 |
|---|---|
| 行遍历与列遍历 | C 按行优先存放二维数组，按最后一维顺序扫描地址连续；按列扫描是跨距读取，缓存利用率更低 |
| false sharing (伪共享) | 多个核心访问同一缓存行、且至少一方写入时，彼此独立的字段也会引起一致性流量；纯并发读取不构成伪共享。Linux 的 `perf c2c` 可定位被争用的行，再对照结构布局 |
| B-tree 与红黑树 | B-tree 的一页存放许多键，一次页读取排除大量候选；指针式红黑树逐节点追逐。以 PostgreSQL 为例，B-tree 叶页还用右兄弟链接支持有序范围扫描；数据库侧见[约束与索引章](#23.%20%E7%BA%A6%E6%9D%9F%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%A7%84%E5%88%99%EF%BC%8C%E7%B4%A2%E5%BC%95%E5%8F%88%E6%80%8E%E6%A0%B7%E6%9C%8D%E5%8A%A1%E8%AF%BB%E5%8F%96%EF%BC%9F) |
| 扁平与节点式哈希表 | 扁平表（如 Abseil Swiss Tables）把元数据密集存放、分组探测；节点式表把值放在独立节点，较易保持元素地址稳定，但查找多一次间接访问 |
| 无分支代码与可预测分支 | 去掉分支可能增加无效工作或数据依赖；分支预测稳定时，保留分支也可能更快 |

### 侵入式链表：把节点嵌进对象之后，生命周期由谁管？

链表有时是对的选择。Linux 内核为此用了一种不同的链表写法，值得单独看它省掉了什么、又把哪些责任留给了调用者。

**钩子嵌在对象里。** `struct list_head` 只含 `next`、`prev` 两个指针。把它作为成员嵌进业务对象，通用链表代码只修改这些指针，不必为对象参加的每种关系另外分配一个包装节点。表头本身也是一个 `list_head`，充当环形双向链表的哨兵；空表时它的两个指针都指向自己。

设一个工作项要同时放进待处理队列和审计队列：

~~~c
struct work_item {
    u64 id;
    struct list_head ready_link;  /* 待处理队列的钩子 */
    struct list_head audit_link;  /* 审计队列的钩子 */
};
~~~

每种同时存在的关系需要一个钩子，每个钩子仍是两个指针，所以链接的存储成本并没有消失。链中的指针指向嵌入的钩子，而不是对象起始地址。按教学布局（指针和 `u64` 各 8 B、无填充），工作项 A 位于 `0x1000`，`ready_link` 在 `0x1008`，`audit_link` 在 `0x1018`：

![64 位无填充教学模型中 work_item A 的字段地址、成员偏移与 container_of 地址还原](../../engineering-foundations/computation/resources/intrusive-lists-in-linux-object-layout.svg)

**`container_of` 从钩子找回对象。** `container_of(ptr, type, member)` 概念上从钩子地址减去 `offsetof(type, member)`：`0x1008 − 8 = 0x1000`，`0x1018 − 24 = 0x1000`。`list_entry()` 和 `list_for_each_entry()` 都建立在它之上，后者让循环变量直接指向外层对象。它只是地址计算：要求传入的指针确实指向该类型的那个成员，不会查找节点，也不消除遍历时读取 `next` 的依赖。它是内核宏，不是标准 C；当前 mainline 的 `container_of()` 会丢掉 `const`，新代码优先用 `container_of_const()`。

**插入和摘除只改固定数量的链接。** 下图是 A、B 依次尾插 ready 队列、A 同时在 audit 队列，然后依次摘下 A、B 的 ready 钩子时的状态：

![A 与 B 入队后 ready 和 audit 两个双向环，以及依次摘除 A.ready、B.ready 后的中间与最终状态](../../engineering-foundations/computation/resources/intrusive-lists-in-linux-ring-transitions.svg)

`list_add_tail` 和 `list_del_init` 改动的指针数与链表长度无关，但这不是整个操作的耗时保证：查找节点、取锁、等缓存都要另算。`list_del_init` 只把这个钩子摘下并重置为自指；它不释放对象，也不碰同一对象的 `audit_link`，所以图中 A 摘下 ready 后仍在 audit 环里。

使用时有几条规则，违反任一条都会留下悬空指针或数据竞争：

- **入链期间对象不能搬移。** 邻居保存的是钩子地址，对象一挪，邻居仍指向旧地址。浅拷贝也不会把副本加入链表：A、B 已依次入 ready 时，A 的副本得到 `next = 0x2008`（B 的钩子）、`prev = 0x8000`（表头），但链中没有谁指向副本。副本要独立使用，先对它的每个钩子调用 `INIT_LIST_HEAD`，再分别入链。
- **“钩子自指”判断未入链，只在同一把锁下成立。** 初始化或 `list_del_init` 后钩子自指，入链后指向邻居，所以可以用 `list_empty(&item->ready_link)` 防止重复挂入；前提是所有插入和摘除都持同一把锁。它也回答不了“这个对象在哪张表里”。
- **safe 迭代不等于并发安全。** `list_for_each_entry_safe` 预先保存下一个游标，让循环体可以删除当前项；它不防并发修改，也不保证保存的下一个节点在被别人释放后仍可访问。所有读写要由同一把合适的锁保护；mutex 可睡眠，不能用在中断上下文。
- **链表不管对象的生命周期。** 释放对象前，要摘掉它所有仍挂着的钩子，并确认没有别的读者或引用者。只从 ready 摘下、仍在 audit 里的工作项不能释放；锁也不会替还在等锁的参数保活，需要调用者的所有权或引用计数。
- **RCU 摘除后的钩子在宽限期内不能复用。** 读多写少时，RCU (read-copy-update，读-复制-更新) 让读者在 `rcu_read_lock()`/`rcu_read_unlock()` 之间用 `list_for_each_entry_rcu()` 遍历而不持写者的锁，写者之间仍须串行，读者可能短暂看到刚删除的项。`list_del_rcu()` 摘除后保留 `next` 供在途读者继续前进（`prev` 被标为 poison），所以不能立刻 `INIT_LIST_HEAD`、重新插入或释放；要等 `synchronize_rcu()` 返回，或 `call_rcu()` 登记的回调在宽限期后执行，才能回收或复用。要保持尾插顺序用 `list_add_tail_rcu()`（`list_add_rcu()` 插在表头之后）。

**什么时候划算，以及它不解决什么。** 对象由当前模块拥有、入链期间地址稳定、要参加多种频繁更新的关系，且省掉包装节点的分配有实际价值时，侵入式链表很合适。但它不会把对象放进连续内存：相邻节点可能相隔很远，遍历仍要先取 `next` 再去下一处，指针追逐一点没少。它简化的是关系表示和已知节点的更新，不是缓存局部性；主要操作是顺序扫描时，仍应先考虑数组。

另外，非侵入式链表也不一定“每个元素分配两次”：C++ 标准只规定 `std::list` 的语义与复杂度，以 GCC 15.2 的 libstdc++ 为例，元素直接存放在节点自带的对齐存储里。这是一个实现样本，不是所有实现的保证。

### 主线一的产出：一份带成本模型的选型

到这里，主线一给出的选型要写明四件事：输入提供什么保证（有序、非负、无环、子问题重叠）；需要哪些操作；复杂度在哪种成本模型下成立（最坏、期望还是均摊，规范保证还是实现模型）；以及比较次数之外，数据布局会让真实耗时落在哪里。主线三的索引直接用到这些结论：B-tree 用页读取而不是指针追逐计成本，复合索引的列序就是复合键比较器的顺序，见[约束守住哪些规则，索引又怎样服务读取？](#23.%20%E7%BA%A6%E6%9D%9F%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%A7%84%E5%88%99%EF%BC%8C%E7%B4%A2%E5%BC%95%E5%8F%88%E6%80%8E%E6%A0%B7%E6%9C%8D%E5%8A%A1%E8%AF%BB%E5%8F%96%EF%BC%9F)。主线二从单个进程的执行开始，问的是程序怎样并发、等待和释放资源，见[一份工作该交给进程、线程还是异步 I/O？](#14.%20%E4%B8%80%E4%BB%BD%E5%B7%A5%E4%BD%9C%E8%AF%A5%E4%BA%A4%E7%BB%99%E8%BF%9B%E7%A8%8B%E3%80%81%E7%BA%BF%E7%A8%8B%E8%BF%98%E6%98%AF%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)。

> [!info]- 来源
> - 内存墙：[Wulf 与 McKee, “Hitting the Memory Wall: Implications of the Obvious” (1995)](https://doi.org/10.1145/216585.216588)。
> - C 数组连续存储、下标语义与指针加减按元素前进：[WG14 N3220, ISO/IEC 9899:2024 工作草案](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf)，§6.2.5、§6.5.3.2、§6.5.7。
> - 缓存层级、规则访问预取、指针追逐与独立读取重叠（含固定步幅指针追逐示例）：[Intel 64 and IA-32 Architectures Optimization Reference Manual, 248966-050US](https://cdrdv2-public.intel.com/821612/248966-Optimization-Reference-Manual-V1-050.pdf)，§9.5.2–9.5.4；属于该微架构的说明，不是所有 CPU 的固定行为。
> - 简单数组与链表的数据局部性权衡、内嵌 `list_head`、`container_of()`、尾插、遍历、摘除与并发注意事项：[Linux 内核 “Linked Lists in Linux”](https://docs.kernel.org/core-api/list.html)，2026-11-11 核对。
> - `list_head` 结构、自指初始化、`list_add_tail`、`list_del_init`、`list_for_each_entry_safe`：[Linux mainline `include/linux/types.h`](https://github.com/torvalds/linux/blob/master/include/linux/types.h)、[`include/linux/list.h`](https://github.com/torvalds/linux/blob/master/include/linux/list.h)；`container_of()` 与 `container_of_const()`：[`include/linux/container_of.h`](https://github.com/torvalds/linux/blob/master/include/linux/container_of.h)；均为 2026-11-11 的 mainline。
> - mutex 可睡眠、不能用于中断上下文：[Linux 内核 “Generic Mutex Subsystem”](https://docs.kernel.org/locking/mutex-design.html)，2026-11-11 核对。
> - RCU 读者可能看到并发增删的项、写者串行化、宽限期后回收：[Linux 内核 “Using RCU to Protect Read-Mostly Linked Lists”](https://docs.kernel.org/RCU/listRCU.html)，Examples 1、2、4；`list_add_rcu`/`list_add_tail_rcu` 插入位置、`list_del_rcu` 保留 `next` 并标记 `prev`：[Linux mainline `include/linux/rculist.h`](https://github.com/torvalds/linux/blob/master/include/linux/rculist.h)；2026-11-11 核对。
> - 伪共享的并发读写条件与 `perf c2c` 的用途：[Linux 内核 “False Sharing”](https://docs.kernel.org/kernel-hacking/false-sharing.html)，2026-11-11 核对。
> - `std::vector`（非 `bool`）连续保证与 `std::list` 操作契约：[C++ 工作草案 vector.overview](https://eel.is/c++draft/vector.overview)、[list.overview](https://eel.is/c++draft/list.overview)，2026-11-11 核对；GCC 15.2.0 的 list 节点用对齐存储保存 T：[libstdc++ `stl_list.h`](https://github.com/gcc-mirror/gcc/blob/releases/gcc-15.2.0/libstdc%2B%2B-v3/include/bits/stl_list.h)。
> - JavaScript `Array` 的语言级索引语义与 `TypedArray` 对 `ArrayBuffer` 的视图：[ECMAScript 2026 Indexed Collections §23.1–23.2](https://tc39.es/ecma262/2026/multipage/indexed-collections.html)、[Structured Data §25.1](https://tc39.es/ecma262/2026/multipage/structured-data.html)；V8 元素种类：[V8 “Elements kinds”](https://v8.dev/blog/elements-kinds)，2025-02-28 更新。
> - PostgreSQL 18 B-tree 的索引页、叶页与有序范围扫描：[B-Tree Indexes §65.1.4.1](https://www.postgresql.org/docs/18/btree.html)、[nbtree README（REL_18_STABLE）](https://github.com/postgres/postgres/blob/REL_18_STABLE/src/backend/access/nbtree/README)；只适用于 PostgreSQL。
> - 扁平与节点式哈希表的布局与地址稳定性：[Abseil Swiss Tables Design Notes](https://abseil.io/about/design/swisstables)，2026-11-11 核对。
## 14. 一份工作该交给进程、线程还是异步 I/O？

本章回答：一段工作在等待 I/O 或占用 CPU 时，应该交给异步 I/O、有界线程池还是独立进程；取消一段在途工作时，哪些信号能说明它真的停了。读者手上只需要本科操作系统课里的进程、线程和系统调用概念。本章也建立主线二的案例，后面各章都在同一个进程里继续追问：怎样共享状态、怎样调度回调、怎样传播背压、怎样停机。

### 案例：一次导出要等什么、算什么

账户报表服务里有一个 worker 进程，正在执行导出任务 `job-demo-731` 的 attempt (执行尝试) 1：把账户 `acct-17` 的报表 42 导出成压缩 CSV。这个任务怎样被受理、领取和确认属于主线四，本主线把“worker 已经拿到 attempt 1”当作给定输入。worker 要做的事按顺序是：

| 阶段 | 做什么 | 主要在等什么 |
| --- | --- | --- |
| 读取 | 异步生成器包装数据库游标，每次取一页，每页最多 100 行，最多 12 页 | 网络 I/O：等数据库返回 |
| 格式化 | 把一行转成一条 CSV 文本 | 很短的 CPU 工作 |
| 压缩 | 默认用 Node 内置的 zlib gzip；对照方案是一个自建的同步增量压缩器 | CPU |
| 写出 | 写入用 `mkdtemp` 新建、本 attempt 独占的临时目录 | 文件 I/O |
| 发布 | 关闭临时文件，再 `rename` 到同一文件系统上按 job 和 attempt 区分的路径 | 文件系统元数据操作 |

同一服务的 API 进程还有另一类工作：把 `acct-17` 的三行 CSV 直接流给一个 HTTP 响应，这是请求内的工作，请求结束它就结束。停机一章会回放这条响应：默认每行间隔 100 ms，加 `--slow` 时每行 600 ms，进程内部的停机截止时间为 1 s。部署平台最终会给这些进程发 `SIGTERM`，平台侧的时限见[服务该跑在哪种运行时上，平台怎样启动、探测和停止它？](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)。

以上数值都是教学用的合成参数。本章要回答的第一个问题是：读取、压缩、写出这几个阶段各该放在哪种执行资源上。

### 进程和线程各划出什么边界？

在常见的操作系统模型里，process (进程) 是资源与保护边界，通常拥有自己的虚拟地址空间；thread (线程) 是进程内的一条执行路径。同一进程的线程共享堆、全局数据和大多数打开的句柄，但各有自己的寄存器状态和栈。

进程之间通常靠管道、套接字、消息或显式映射的共享内存通信。Linux 的 `mmap(MAP_SHARED)` 可以让两个进程看到同一块内存，所以“进程之间什么都不共享”并不准确；准确的说法是，进程默认不共享地址空间，要共享就得显式安排。

独立地址空间也不等于权限隔离。`fork()` 出来的子进程会继承父进程的用户身份和打开的文件描述符；父进程能读的文件、能连的网络，子进程照样能访问。运行不可信代码时，要另用操作系统策略（如 Linux Landlock）缩减它能访问的文件和网络。

### 并发和并行有什么区别？

concurrency (并发) 指多个任务在重叠的时间段内都有进展；只有一个处理单元时，调度器靠交替运行做到这一点。parallelism (并行) 指多个处理单元在同一时刻各自执行指令。

单线程的事件循环能做到并发：一个请求在等数据库时，线程去处理另一个请求。但它做不到并行，而且一段很长的同步计算会把这条线程整个占住，其他任务都只能等。CPU 计算能否并行，取决于语言运行时是否允许多段代码同时执行、数据怎样在执行者之间交接，以及负载是否大到值得拆分。

### 阻塞、非阻塞和异步 I/O 各指什么？

三种说法描述的是调用方与操作之间的关系：

- blocking I/O (阻塞 I/O)：调用线程一直等到操作完成或可以继续，例如普通的 `read()`。
- non-blocking I/O (非阻塞 I/O)：暂时不能继续时立即返回，例如返回 `EAGAIN`，意思只是“目前没有数据”，调用方要稍后再试，通常配合 `poll()` 这类就绪通知使用。
- async I/O (异步 I/O)：调用方提交操作后先去做别的事，稍后收到完成结果。

“异步”描述的是调用关系，不说明底层由谁执行。网络 I/O 可以由操作系统的就绪通知驱动，不需要为每个连接配一个线程；Node.js 的回调式和 Promise 式文件系统 API（`fs.FSWatcher` 除外）则在 libuv 的线程池里执行，只是调用方不必原地等。

同理，`await` 本身不创建线程，也不会把表达式搬到后台。被等待的 Promise 尚未结算时，`async` 函数挂起，把控制权交还事件循环；结算后，函数剩余部分回到原来的执行线程继续运行。所以“函数返回 Promise”不能说明工作在别的线程上完成，要查具体 API 的文档。

如果运行时没有合适的异步 API，可以把同步调用放进有界的阻塞线程池，让请求线程腾出来。这只是让池里的一个线程代为等待，底层调用并没有变成异步操作。I/O 阶段的选择可以归结为：

~~~mermaid
flowchart TD
    IOWait[I/O 阶段] --> HasAsync{运行时有合适的<br/>异步 API？}
    HasAsync -->|有| AsyncAPI[用异步 API<br/>等待期间事件循环<br/>处理其他工作]
    HasAsync -->|没有| BlockingPool[放进有界线程池<br/>每个等待<br/>占一个池线程]
    AsyncAPI --> Limit[限制在途操作<br/>连接、缓冲和队列]
    BlockingPool --> Limit
~~~

两条路最后都要设上限：异步等待不占线程，但每个在途操作仍占着连接和缓冲区。

### 三种执行资源各要你负责什么？

| 执行资源 | 适合的工作 | 你要承担的责任 |
| --- | --- | --- |
| 异步 I/O | 运行时为数据库、网络或文件提供了适用的异步 API | 在途操作仍占连接和缓冲区，必须限制并发数；同步代码仍会卡住事件循环 |
| 有界线程池 / 工作线程 | 运行时能并行执行的 CPU 转换；或把同步阻塞调用移出请求线程 | 线程共享进程地址空间，共享的可变状态要同步；阻塞调用一直占着一个池线程；线程数和排队数都要有上限 |
| 独立进程 | 需要独立生命周期、故障边界或地址空间的计算 | 消息序列化、独立内存和启动成本；要自己管理退出；子进程默认继承父进程的身份与句柄，不是沙箱 |

### CPU 工作该放在哪里？

CPU 工作的放置先看要满足哪种目标。三种目标可能同时出现，每一种都要逐项验证：

| 目标 | 可选路径 | 必须验证的条件 |
| --- | --- | --- |
| 独立的故障或地址空间边界 | 独立进程 | 进程边界能否隔开所需的故障或内存；不可信代码的权限要另外限制；跨进程交接数据的成本 |
| 满足响应预算，不要求跨核 | 先把工作拆成短片段并在片段间让出；不达标再用工作线程；仍不达标再评估独立进程 | 单个片段能否落在预算内；工作线程能否让响应路径及时获得调度（即使没有并行也可能有用）；进程方案在当前负载下能否达标 |
| 必须跨核并行 | 能真正并行执行这类工作的线程；否则用多进程 | 运行时是否真的并行执行；机器有没有可用的处理单元和 CPU 配额；数据交接成本；若同时有响应预算，两项都要满足 |

无论选哪条路，都要限制作业入口和在途数据量；用了线程池或进程池，还要限制执行槽数和排队任务数。

工作线程把 CPU 计算移出事件循环线程后，即使运行时不能让两段代码同时在多个处理单元上执行，调度器仍会交替运行它们，响应路径因此有机会及时执行。这改善的是获得调度的机会，不保证达到某个延迟预算。

**回到 `job-demo-731`。** 读取页面主要在等网络，留在事件循环上用异步 API。压缩是 CPU 工作，有两种做法：

- 默认做法用 Node 内置的异步 zlib gzip。它本身就在 libuv 线程池里执行，不占事件循环，代价是和同进程里其他文件、DNS、加密操作共用同一个池。
- 对照做法是一个自建的同步增量压缩器，它有内部状态，必须按顺序逐页喂给同一个执行者。按上表核对：这个任务不要求跨核，也不需要隔离可能崩溃的本地库；本例假设即使把压缩拆成最短的可接受片段，单个片段仍超出事件循环的响应预算，所以把它交给 Node 的 `worker_threads`。目的在于让事件循环保持响应，不是提高吞吐。

这个对照方案的完整协议（每页确认、收尾、归还 worker 槽）在 [Node 的执行位置一章](#17.%20Node.js%20%E7%9A%84%E5%B7%A5%E4%BD%9C%E5%AE%9E%E9%99%85%E5%9C%A8%E5%93%AA%E4%B8%AA%E7%BA%BF%E7%A8%8B%E6%88%96%E8%BF%9B%E7%A8%8B%E4%B8%8A%E6%89%A7%E8%A1%8C%EF%BC%9F)；默认方案的流水线与背压在[流一章](#20.%20%E6%B5%81%E6%80%8E%E6%A0%B7%E6%8A%8A%E2%80%9C%E6%85%A2%E4%B8%8B%E6%9D%A5%E2%80%9D%E9%80%90%E6%AE%B5%E4%BC%A0%E5%9B%9E%E6%BA%90%E5%A4%B4%EF%BC%8C%E4%B8%AD%E9%80%94%E5%A4%B1%E8%B4%A5%E5%8F%88%E7%95%99%E4%B8%8B%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 取消能证明什么？

worker 执行到一半时，可能收到取消：用户取消了 job、请求超时，或进程要停机。不论在哪个运行时，**取消只是一个请求**：它请求任务协作停止，并不证明任务已经结束，更不证明任务的副作用没有发生。

收到取消的代码要做三件事：按 API 规定的方式观察取消信号；从这一刻起不再提交新的副作用；在 `finally` 或等价的清理路径里释放自己拥有的资源。

POSIX 线程把“请求”和“结束”分得很清楚，可以作为参照：

- 新线程默认启用 deferred cancellation (延迟取消)，取消请求只在取消点处理；线程可以改成异步取消（可能在任意时刻处理），也可以暂时禁用取消。
- `pthread_cancel()` 返回成功，只说明取消请求已经排入，不说明线程已经终止。
- 对 joinable 线程调用 `pthread_join()` 会等它终止。`pthread_join()` 返回 `0` 只说明 join 成功；要确认线程是因取消而结束，还得看它的退出值是否等于 `PTHREAD_CANCELED`。

应用层的取消通常更弱：被取消的往往只是**等待方**。调用方不再等某个 Promise、某个线程或某个远端请求，底层的线程、数据库操作或远端请求却可能继续运行；已经提交的写入也不会因此回滚。由此得到几条跨运行时的规则：

- 计时器到点只是安排一段代码运行，不会中断正在运行的回调，也不会取消尚未完成的数据库查询；要取消底层操作，必须用该驱动或服务提供的取消机制。
- 调用方放弃 `await` 不会取消底层操作；Node 的 `AbortSignal` 也只对接收并处理它的 API 生效。
- Python 的 `Task.cancel()` 只在协程内部抛入 `CancelledError`；`asyncio.to_thread()` 中已经开始运行的线程不会被杀掉。
- 一次写入是否真的发生，以持久化的业务结果为准，不能把“本地任务已取消”记成“操作没有发生”。

在 `job-demo-731` 里，这意味着：取消请求到达后，worker 要先停止拉取新页，再等在途的查询、压缩和文件写入各自给出结束信号，才能释放它们占用的资源；取消一次文件写入后，临时文件里可能已经留下部分数据。各运行时的具体行为在各自章节：Node 的计时器见[事件循环一章](#16.%20Node.js%20%E7%9A%84%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E6%80%8E%E6%A0%B7%E5%AE%89%E6%8E%92%E8%AE%A1%E6%97%B6%E5%99%A8%E3%80%81I/O%20%E5%9B%9E%E8%B0%83%E5%92%8C%E5%BE%AE%E4%BB%BB%E5%8A%A1%EF%BC%9F)，worker 收不到取消消息的情形见 [Node 执行位置一章](#17.%20Node.js%20%E7%9A%84%E5%B7%A5%E4%BD%9C%E5%AE%9E%E9%99%85%E5%9C%A8%E5%93%AA%E4%B8%AA%E7%BA%BF%E7%A8%8B%E6%88%96%E8%BF%9B%E7%A8%8B%E4%B8%8A%E6%89%A7%E8%A1%8C%EF%BC%9F)，Python 的取消见 [asyncio 一章](#18.%20%E5%BC%82%E6%AD%A5%20FastAPI%20%E6%8E%A5%E5%8F%A3%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BB%8D%E4%BC%9A%E9%98%BB%E5%A1%9E%EF%BC%8C%E5%8F%96%E6%B6%88%E5%92%8C%E8%B5%84%E6%BA%90%E5%8F%88%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%EF%BC%9F)，流的取消与部分输出见[流一章](#20.%20%E6%B5%81%E6%80%8E%E6%A0%B7%E6%8A%8A%E2%80%9C%E6%85%A2%E4%B8%8B%E6%9D%A5%E2%80%9D%E9%80%90%E6%AE%B5%E4%BC%A0%E5%9B%9E%E6%BA%90%E5%A4%B4%EF%BC%8C%E4%B8%AD%E9%80%94%E5%A4%B1%E8%B4%A5%E5%8F%88%E7%95%99%E4%B8%8B%E4%BB%80%E4%B9%88%EF%BC%9F)。浏览器端 Promise 与 `AbortSignal` 的语义见前端的[取消、超时与并发](../../frontend/javascript/cancellation-timeouts-and-concurrency.md)。持久 job 的取消要通过持久状态裁决，见主线四的[任务失败、被取消或 worker 失联后，怎样收尾而不重复也不留孤儿？](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)。

### 下一步：多个执行者共享状态时

到这里，导出的各阶段都有了执行位置：页面读取用异步 I/O，压缩交给线程池或工作线程，独立进程留给需要故障或地址空间边界的工作；取消被当作请求，结束要看各资源自己的完成信号。一旦有两个执行者同时修改同一份状态（两个 worker 更新同一个计数，取消和发布同时想改 job 的状态），就会出现新问题：结果取决于谁先谁后。下一章讨论[多个执行者怎样共享状态而不丢更新、不互相卡死](#15.%20%E5%A4%9A%E4%B8%AA%E6%89%A7%E8%A1%8C%E8%80%85%E5%85%B1%E4%BA%AB%E7%8A%B6%E6%80%81%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%B8%8D%E4%B8%A2%E6%9B%B4%E6%96%B0%E3%80%81%E4%B8%8D%E4%BA%92%E7%9B%B8%E5%8D%A1%E6%AD%BB%EF%BC%9F)。

> [!info]- 来源
> - 进程与线程的边界：`fork()` 后父子进程内存空间分离，`mmap()` 的 `MAP_SHARED` 建立显式共享映射：[Linux man-pages 6.19, fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)，Description；[mmap(2)](https://man7.org/linux/man-pages/man2/mmap.2.html)，`MAP_SHARED` / `MAP_PRIVATE`；2026-11-11 核对。
> - 同一进程的 POSIX 线程共享全局数据与堆、各有栈与线程状态：[Linux man-pages 6.19, pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html)，2026-11-11 核对。
> - 子进程继承凭据和打开的文件描述符；用 OS 策略限制文件与网络访问：[fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)，Description；[Linux kernel, Landlock](https://docs.kernel.org/userspace-api/landlock.html)，2026-11-11 核对。
> - 阻塞 `read`、非阻塞时返回 `EAGAIN`、`poll` 等待就绪、提交后收到完成通知：[read(2)](https://man7.org/linux/man-pages/man2/read.2.html)、[poll(2)](https://man7.org/linux/man-pages/man2/poll.2.html)、[aio(7)](https://man7.org/linux/man-pages/man7/aio.7.html)，2026-11-11 核对。
> - Node 回调式与 Promise 式文件 API（`fs.FSWatcher` 除外）使用 libuv 线程池：[Node.js v26.13.0, File system, Threadpool usage](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#threadpool-usage)，2026-11-11 核对。
> - Node 异步 zlib API 在内部线程池执行，同步 API 除外：[Node.js v26.13.0, Zlib, Threadpool usage](https://nodejs.org/download/release/v26.13.0/docs/api/zlib.html#threadpool-usage-and-performance-considerations)，2026-11-12 核对。
> - `worker_threads` 面向 CPU 密集型 JavaScript，I/O 优先使用内置异步 API：[Node.js v26.13.0, Worker threads](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html)，2026-11-12 核对。
> - 延迟与异步线程取消、取消请求不等于终止：[Linux man-pages 6.19, pthread_cancel(3)](https://man7.org/linux/man-pages/man3/pthread_cancel.3.html)，2026-11-11 核对。
> - joinable 线程的终止状态与 `PTHREAD_CANCELED`：[Linux man-pages 6.19, pthread_join(3)](https://man7.org/linux/man-pages/man3/pthread_join.3.html)，2026-11-11 核对。
## 15. 多个执行者共享状态时，怎样不丢更新、不互相卡死？

本章回答两个问题：两个执行者同时修改同一份状态时，为什么会丢掉一次更新，应该用什么规则避免；多个执行者互相等待时，什么情况才真的构成死锁，怎样预防。读者手上有[上一章](#14.%20%E4%B8%80%E4%BB%BD%E5%B7%A5%E4%BD%9C%E8%AF%A5%E4%BA%A4%E7%BB%99%E8%BF%9B%E7%A8%8B%E3%80%81%E7%BA%BF%E7%A8%8B%E8%BF%98%E6%98%AF%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)的结论：线程共享进程地址空间，进程默认不共享，异步等待不占线程。

主线二的导出案例里，共享状态出现在 `job-demo-731` 的协调代码中：取消和发布都想改这次 attempt 的状态。那个裁决要等流一章讲完部分输出后才看得清，所以本章先换一个更小的独立例子：两个 worker 线程各把同一个计数器加 100,000 次，最后应该得到 200,000。

### 读-改-写为什么会丢更新？

race condition (竞态) 指结果取决于并发操作的先后顺序。`count += 1` 看起来是一条语句，实际上是三步：读出当前值、加一、写回。若两个线程都先读到 10，再各自写回 11，最终是 11，预期的 12 少了一次。这种错误叫 lost update (丢更新)。

在 Node 里，两个 `worker_threads` 默认不共享普通对象；要让它们改同一个计数器，必须用 `SharedArrayBuffer` 显式共享一块内存。下面的程序让两个 worker 各加 100,000 次：

~~~javascript
// 保存为 counter.cjs；node counter.cjs plain 或 node counter.cjs atomic
const { Worker, isMainThread, workerData } = require('node:worker_threads');

if (isMainThread) {
  const shared = new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT);
  const mode = process.argv[2] ?? 'atomic';
  const workers = Array.from({ length: 2 }, () =>
    new Worker(__filename, { workerData: { shared, mode } }));
  Promise.all(workers.map(worker => new Promise((resolve, reject) => {
    worker.once('error', reject);
    worker.once('exit', code => code === 0 ? resolve() : reject(new Error(`exit ${code}`)));
  }))).then(() => console.log(Atomics.load(new Int32Array(shared), 0)));
} else {
  const counter = new Int32Array(workerData.shared);
  for (let i = 0; i < 100_000; i++) {
    if (workerData.mode === 'plain') counter[0]++;    // 读、加一、写回三步
    else Atomics.add(counter, 0, 1);                 // 一次不可分割的读-改-写
  }
}
~~~

`plain` 模式每次运行的结果都可能不同，多数运行小于 200,000（例如 162,339），偶尔恰好等于 200,000。恰好正确的那一次并不说明代码没问题，只说明这一次两个线程的交错没有撞上。`atomic` 模式用 `Atomics.add` 把读-改-写变成一个不可分割的操作，每次都输出 200,000。这个程序只验证正确性，不说明多开 worker 会让计数变快。

### 共享不变量要选哪种所有权规则？

修复丢更新，不是给每处修改都“加点同步”，而是为每个共享不变量明确选定**一种**所有权规则：谁有权修改它，修改怎样被串行化。

| 所有权规则 | 怎样避免丢更新 | 适用范围与限制 |
| --- | --- | --- |
| 锁（mutex） | 同一时刻只有持锁者执行临界区 | 只在共享同一把锁的执行者之间有效；持锁时间越长，等待越多，还可能形成死锁（见下一节） |
| 原子操作 | 硬件或运行时保证一次读-改-写不可分割 | 只适合能用单个原子操作表达的小状态，例如计数、标志位 |
| 单写者消息循环 | 只有一个执行者能改状态，其他执行者发消息请求修改，由它按顺序处理 | Node 事件循环天然是单写者：同一线程上的回调不会交错执行；代价是所有修改都排在这个循环上 |
| 数据库约束与条件写 | 数据库在一条语句内检查条件并修改，返回受影响行数，由数据库裁决谁赢 | 适合跨进程、跨副本的持久状态；需要按语句设计条件，并把返回行数当作业务判断 |

单写者规则有一个容易漏掉的前提：读、改、写必须在同一段同步代码里完成。若先读出状态、`await` 一次查询、再写回，等待期间别的回调可以插进来改同一份状态，丢更新照样发生。

表中最后一行（数据库约束与条件写）之所以必要，是因为进程内的锁只对共享这把锁的线程有效。服务通常运行多个副本，job 状态这类保存在数据库里的共享状态，别的副本根本看不到你的锁。主线三的结论是：把条件写进 `UPDATE ... WHERE` 本身，让数据库在同一条语句里检查并修改，返回 0 行就说明别人已经先改了，见[两个请求争夺最后一件库存时，怎样保证只预留一次？](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。跨副本还有一个更隐蔽的问题：一个 worker 的租约过期后，它自己可能还在运行并试图写结果；主线四用一个单调递增的 attempt 编号，在提交结果时检查“我仍是当前 attempt”，挡住旧执行者，见[怎样保证一个任务同一时刻只由一个 worker 推进？](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)。

回到 `job-demo-731`：取消与发布由同一事件循环上的一个协调者串行裁决，这就是单写者规则；它保护的是进程内的 attempt 状态。job 在数据库里的状态则交给条件写和 attempt 栅栏。

### 等待环何时才构成死锁？

另一类共享问题是互相等待。为了判断，先把“谁在等谁”画成图。

**每类资源只有一个实例时，看 wait-for graph (等待图)。** 节点是线程，边 A→B 表示 A 在等 B 持有的资源。下面 A 持有 R1、等 R2，B 持有 R2、等 R1，形成环 A→B→A：

~~~mermaid
flowchart LR
    A[线程 A<br/>持有 R1] -->|等待 R2| B[线程 B<br/>持有 R2]
    B -->|等待 R1| A
~~~

如果等待不会超时、不会被取消，线程也不会在等待中放弃已持有的资源，而且每类资源只有一个互斥实例，那么等待图中出现环就**证明**发生了 deadlock (死锁)。

**资源有多个可互换实例时，看 resource-allocation graph (资源分配图)。** 节点分为线程和资源类型，资源类型节点内标出各个实例；请求边表示等待，分配边表示持有。这时图里有环只是死锁的必要线索，不足以证明死锁。设 R1 只有一个实例，R2 有两个可互换的实例 R2a、R2b：

~~~mermaid
flowchart LR
    A[线程 A] -->|请求任一 R2| R2[(R2：R2a、R2b)]
    R2 -->|R2a 分配给| B[线程 B]
    R2 -->|R2b 分配给| C[线程 C<br/>不等待任何资源]
    B -->|请求| R1[(R1)]
    R1 -->|分配给| A
~~~

A→R2→B→R1→A 构成环，但 C 不等待任何资源，能独立完成。C 归还 R2b 后，A 拿到 R2b 继续执行并释放 R1，B 随后也能继续。曾经出现的环自行解开了。

经典资源模型（Coffman 等，1971）列出死锁的四个必要条件：

1. mutual exclusion (互斥)：资源一次只能由一个执行者持有。
2. hold and wait (持有并等待)：执行者持有资源的同时等待别的资源。
3. no preemption (不可抢占)：资源不会被系统强行收回，只能由持有者主动释放。这里说的是资源，不是“操作系统调度器不能抢占线程”。
4. circular wait (循环等待)：存在一个等待环。

破坏其中任意一个条件，就能预防这类死锁；但在多实例资源下，四个条件同时出现仍不保证已经死锁，上面的 R2 例子就是如此。

### 等待 Promise 为什么不是资源环，怎样预防死锁？

这四个条件不是用来给任意“慢请求”打勾的清单。请求在等 I/O，或者一个 Promise 尚未完成，本身并不构成资源等待环。例如浏览器里等待 `fetch` 的 Promise 不持有 DOM 的独占锁，事件循环在它 pending 期间照样运行其他代码。判断前先找出真实的资源与依赖关系。

但应用照样可能停住，原因换成了别的：真实的依赖环（A 等 B 的结果，B 又等 A 的结果）、永不完成的 Promise，或资源耗尽。最常见的资源耗尽是连接池：每个请求都持有一个连接，又在等另一个连接，池用完后所有请求一起等，直到池等待超时。怎样找到占着连接的人，见[池超时之后，怎样找到占着连接的人？](#%E6%B1%A0%E8%B6%85%E6%97%B6%E4%B9%8B%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%89%BE%E5%88%B0%E5%8D%A0%E7%9D%80%E8%BF%9E%E6%8E%A5%E7%9A%84%E4%BA%BA%EF%BC%9F)。

预防锁环的做法有三条：

- 需要多把锁时，所有代码按同一个全局顺序获取，破坏循环等待。
- 缩短临界区，减少持锁时间。
- 不要在持锁期间等待时长不确定的网络调用。

### 下一步：单写者循环怎样排队

本章的产出是一条规则：每个共享不变量只选一种所有权规则，进程内状态用锁、原子操作或单写者循环，跨副本的持久状态交给数据库条件写和 attempt 栅栏；死锁先按资源实例数选对图，再判断环是否足以证明。Node 选择的是单写者路线：一条线程、一个事件循环，回调一个接一个地运行。下一章看这个循环[怎样安排计时器、I/O 回调和微任务](#16.%20Node.js%20%E7%9A%84%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E6%80%8E%E6%A0%B7%E5%AE%89%E6%8E%92%E8%AE%A1%E6%97%B6%E5%99%A8%E3%80%81I/O%20%E5%9B%9E%E8%B0%83%E5%92%8C%E5%BE%AE%E4%BB%BB%E5%8A%A1%EF%BC%9F)。

> [!info]- 来源
> - `SharedArrayBuffer` 共享内存、`Atomics` 原子操作与 worker 间结构化克隆：[Node.js v26.13.0, Worker threads](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html)，2026-11-12 核对；计数程序 `atomic` 模式于 v26.13.0 与 v26.13.1 输出 200000，`plain` 模式于 Node.js v26.13.1 多次运行，多数小于 200000。
> - 共享字节区须用原子操作或明确交接访问权：[ECMAScript Shared Memory Guidelines](https://tc39.es/ecma262/multipage/memory-model.html#sec-shared-memory-guidelines)，2026-11-12 核对。
> - 死锁的互斥、持有并等待、不可抢占、循环等待四条件，单实例与多实例资源图中环的含义：[Coffman, Elphick, and Shoshani (1971), “System Deadlocks,” pp. 70–73](https://uobdv.github.io/Design-Verification/Supplementary/System_Deadlocks-Four_necessary_and_sufficient_conditions_for_deadlock.pdf)，2026-11-11 核对。
## 16. Node.js 的事件循环怎样安排计时器、I/O 回调和微任务？

本章回答：Node.js 只有一条 JavaScript 主线程，它怎样在计时器、I/O 回调、`setImmediate`、`process.nextTick` 和 Promise 回调之间决定下一个运行谁；哪些顺序可以依赖，哪些只是某次运行的偶然结果。读者手上有前两章的结论：异步 I/O 让等待不占线程，事件循环是一个单写者循环，回调之间不会交错。

沿用主线二的案例：`job-demo-731` 所在 worker 进程的主线程上，异步生成器向数据库要一页数据，等待期间线程去处理别的回调；这一页返回时，驱动的 I/O 回调被安排回主线程。为了能离线运行，下面的演示用 `fs.readFile` 读取脚本自身来代表“一页数据就绪”，用 `node` 直接运行的脚本（CLI 主模块）顶层代码代表发起读取的那段同步代码。浏览器的事件循环有自己的 task 与渲染规则，见前端的[浏览器事件循环](../../frontend/browser/event-loop-tasks-and-rendering.md)，不能把下面的阶段图套过去。

### 一条线程怎样同时照看许多 I/O？

主 JavaScript 线程一次只运行一个同步调用栈。代码调用异步 I/O API 时，只是登记“完成后运行哪个回调”，然后立即返回；数据就绪后，Node 把对应的回调安排回这条线程，等当前调用栈清空后再运行它。底层 I/O 由驱动、操作系统和 libuv（Node 使用的跨平台 I/O 库）完成；某个数据库驱动具体怎样传输数据，不能仅凭它返回 Promise 推断。

因此有两个直接后果：一个回调开始运行后，计时器和其他 I/O 回调都不能打断它；回调之间谁先谁后，由事件循环的阶段和检查点决定。

### 事件循环分哪几个阶段？

libuv 的事件循环反复经过下面几个阶段，每个阶段处理一类回调。表只说明各阶段的职责，不是每一轮的精确时间线：

| 阶段 | 职责 |
| --- | --- |
| timers (计时器) | 运行已经越过时间门槛的 `setTimeout` / `setInterval` 回调；越过门槛后仍要等到调度机会 |
| pending callbacks (待处理回调) | 运行少数被推迟到下一轮的系统回调 |
| idle、prepare | libuv 内部阶段，不运行一般应用代码 |
| poll (轮询) | 处理大多数 I/O 回调；没有可运行的回调时，可能在这里等待新事件 |
| check (检查) | 运行 `setImmediate` 排入的回调 |
| close callbacks (关闭回调) | 处理部分 handle 的关闭事件 |

计时器的毫秒数是门槛，不是精确时钟。Node 把 `setTimeout(fn, 0)` 当作 1 ms 门槛处理；计时器不会切断正在运行的回调，也不保证在指定的那一毫秒运行。

> [!info] 版本差异：到期计时器在哪里检查
> 从 libuv 1.45.0 起（随 Node.js v20.3.0 引入），默认循环模式在 poll 之后检查到期计时器；为兼容旧行为，进入循环前仍有一次预检查。更早的版本在每轮 poll 之前也会检查。本章的演示在 Node.js v26.13.1 上运行。

### nextTick 和微任务在什么时候运行？

`process.nextTick()` 的回调进入 Node 管理的 nextTick 队列；Promise 的 reaction（`then` 等处理回调）和 `queueMicrotask()` 共用 JavaScript 的 microtask (微任务) 队列。这两个队列不是 libuv 阶段，它们在**调度检查点**被清空。

检查点出现在：Node 派发的一个 JavaScript 回调返回、Node 重新拿回控制权的时候。这时 Node 先清空 nextTick 队列，再清空微任务队列，然后才继续调度下一个回调。检查点不只在阶段之间出现，同一阶段的两个回调之间也有；而普通 JavaScript 函数 `return` 给它的调用方，仍在同一个调用栈内，不触发检查点。

同一个 check 阶段里排了两个 `setImmediate`：

~~~javascript
setImmediate(() => {
  console.log('immediate 1');
  process.nextTick(() => console.log('nextTick'));
  queueMicrotask(() => console.log('microtask'));
});
setImmediate(() => console.log('immediate 2'));
~~~

输出是 `immediate 1 → nextTick → microtask → immediate 2`：第一个回调返回后，Node 先清空两个队列，才运行第二个 immediate。

### setImmediate 和 0 ms 计时器谁先？

把“一页数据就绪”的 I/O 回调和这些队列放在一起看。下面的脚本在顶层和 I/O 回调里各排一组工作：

~~~javascript
// 保存为 io-demo.cjs；node io-demo.cjs
const fs = require('node:fs');
console.log('main module starts');
process.nextTick(() => console.log('nextTick (top level)'));
Promise.resolve().then(() => console.log('Promise reaction (top level)'));
setTimeout(() => console.log('timeout (top level)'), 0);
setImmediate(() => console.log('immediate (top level)'));

fs.readFile(__filename, error => {
  if (error) return console.log('read failed');
  console.log('I/O callback: page ready');
  process.nextTick(() => console.log('nextTick from I/O'));
  Promise.resolve().then(() => console.log('Promise from I/O'));
  queueMicrotask(() => console.log('queueMicrotask from I/O'));
  setTimeout(() => console.log('timer from I/O'), 0);
  setImmediate(() => console.log('immediate from I/O'));
});
~~~

可以依赖的只有下面这些局部顺序：

- 顶层同步代码跑完后，先输出 `nextTick (top level)`，再输出 `Promise reaction (top level)`。
- I/O 回调返回后，先清空它排入的 nextTick，再按入队顺序清空 Promise 和 `queueMicrotask`。
- 同一个 I/O 回调排入的 immediate，一定先于它排入的 0 ms 计时器：I/O 回调在 poll 阶段运行，同一轮接下来就是 check 阶段，计时器要等后面的 timers 检查。

其余顺序都不保证。CLI 主模块顶层的 timeout 与 immediate 谁先，取决于进入循环时是否已经过了 1 ms 门槛；文件读取何时完成，又决定它们排在 I/O 回调之前还是之后。同一脚本多次运行，`timeout (top level)` 有时排在 I/O 回调之前、有时排在 `immediate (top level)` 之后；`immediate (top level)` 也可能出现在 I/O 回调之前或之后。一次运行记录只是一种可能的交错，不是固定序列。

![I/O 回调返回后，经调度检查点、check 阶段再到 timer 的局部流程](../../engineering-foundations/runtime/resources/node-event-loop-io-phases.svg)

图只放大 I/O 回调 → 检查点 → check → timer 这一段交接，不表示所有阶段都只走这条路径。

### 长同步回调对计时器做了什么？

计时器只负责“到点后安排一段代码”。如果事件循环正在运行一个长同步回调，计时器只能等它结束：

~~~javascript
const t0 = Date.now();
setTimeout(() => console.log('100 ms timer ran at', Date.now() - t0, 'ms'), 100);
setTimeout(() => {
  const end = Date.now() + 120;
  while (Date.now() < end) {}          // 120 ms 的同步计算
  console.log('sync callback finished at', Date.now() - t0, 'ms');
}, 0);
~~~

一次运行输出 `sync callback finished at 121 ms`，随后才是 `100 ms timer ran at 122 ms`：100 ms 的门槛早已越过，计时器回调仍要等 120 ms 的同步回调跑完。

这说明了计时器不能做什么：它不会中断回调，也不会取消尚未完成的数据库查询。判断请求是否超时，要用明确的 deadline (截止时间)；要取消底层操作，必须调用驱动支持的取消机制。“取消只是请求”的跨运行时原则见[主线二首章](#%E5%8F%96%E6%B6%88%E8%83%BD%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

### nextTick 与 Promise 微任务谁先？

“nextTick 先于 Promise”只在特定执行上下文里成立。在直接运行的 CommonJS (CJS) 主模块里：

~~~javascript
// queues.cjs
const { nextTick } = require('node:process');
Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
~~~

输出 `nextTick → promise → microtask`：同步入口返回后的检查点先清空 nextTick，再清空微任务；Promise 与 `queueMicrotask` 在同一个先进先出的队列里，按登记顺序运行。

如果此刻**正在处理微任务**，顺序就反过来了。下面的微任务 A 在运行时又排入了 nextTick X、Promise B 和微任务 C：

~~~javascript
Promise.resolve().then(() => {
  console.log('microtask A');
  process.nextTick(() => console.log('nextTick X'));
  Promise.resolve().then(() => console.log('microtask B'));
  queueMicrotask(() => console.log('queueMicrotask C'));
});
~~~

输出 `microtask A → microtask B → queueMicrotask C → nextTick X`：当前微任务队列要先清空，Node 才回头处理新排入的 nextTick。

![直接运行 CJS 与 ESM 入口时的队列顺序，以及嵌套微任务示例](../../engineering-foundations/runtime/resources/node-event-loop-queue-contexts.svg)

#### 进阶：ESM 入口与 `require(esm)`

把 `queues.cjs` 原样改写成 ES module (ESM)：

~~~javascript
// queues.mjs
import { nextTick } from 'node:process';
Promise.resolve().then(() => console.log('promise'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
~~~

直接运行 `node queues.mjs` 输出 `promise → microtask → nextTick`。原因与上面的嵌套例子相同：ESM 入口模块是在微任务处理过程中求值的，模块代码排入的微任务先于 nextTick。

但扩展名并不独自决定执行上下文。在 CJS 主模块里同步加载同一个文件：

~~~javascript
// require-esm-context.cjs，与 queues.mjs 放在同一目录
require('./queues.mjs');
console.log('CJS require returned');
~~~

输出 `CJS require returned → nextTick → promise → microtask`：这次 `queues.mjs` 在 CJS 的同步调用栈里求值，回到了 CJS 的顺序。同步 `require(esm)` 只适用于不含顶层 `await` 的 ESM 依赖图。

### 还该用 process.nextTick 吗？

Node.js v26 把 `process.nextTick()` 标为 Legacy (历史遗留)，建议多数用户代码改用 `queueMicrotask()`。原因有两个：

- `queueMicrotask()` 在浏览器等其他 JavaScript 环境里行为一致。
- 递归调用 `nextTick` 会让 Node 一直忙于清空 nextTick 队列，迟迟进不了 poll 阶段，I/O 回调因此无法推进。

旧代码里仍会见到 nextTick 的两种用法：工厂函数先返回一个事件发射器，再在当前调用栈退栈后发出 `ready`，让调用方来得及注册监听器；回调式 API 用它延后交付同步发现的参数错误。下面是第一种：

~~~javascript
const { EventEmitter } = require('node:events');

function createEmitter() {
  const emitter = new EventEmitter();
  process.nextTick(() => emitter.emit('ready'));
  return emitter;
}

createEmitter().on('ready', () => console.log('ready'));
~~~

旧库可能依赖 nextTick 特有的顺序或额外参数，迁移时要先确认这些调用契约。新代码若只想让一段代码在当前同步代码之后立刻运行，用 `queueMicrotask()`。

### 下一步：哪些工作不在这条线程上

本章的产出是一组可依赖的顺序规则：回调之间不会互相打断；每个回调返回后先清 nextTick 再清微任务（正在处理微任务时例外）；同一个 I/O 回调排入的 immediate 先于 0 ms 计时器；其余跨阶段的先后不作保证；计时器不取消任何操作。这条线程只负责运行 JavaScript 回调，真正的文件读写、压缩和 DNS 查询可能发生在别处。下一章回答 [Node.js 的工作实际在哪个线程或进程上执行](#17.%20Node.js%20%E7%9A%84%E5%B7%A5%E4%BD%9C%E5%AE%9E%E9%99%85%E5%9C%A8%E5%93%AA%E4%B8%AA%E7%BA%BF%E7%A8%8B%E6%88%96%E8%BF%9B%E7%A8%8B%E4%B8%8A%E6%89%A7%E8%A1%8C%EF%BC%9F)。

> [!info]- 来源
> - 阶段职责、poll 对 I/O 与计时器的调度、CLI 主模块与 I/O 回调中 timer/immediate 的顺序、nextTick 检查点：[Node.js Learn, The Node.js Event Loop](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick)，2026-11-12 核对。
> - libuv 1.45.0 改变计时器检查位置，并由 Node.js v20.3.0 引入：[Node.js v20.3.0 release notes](https://nodejs.org/en/blog/release/v20.3.0)；同上 Learn 文档，2026-11-12 核对。
> - libuv 循环阶段，网络 I/O 回调在循环线程上运行：[libuv Design overview, The I/O loop](https://docs.libuv.org/en/v1.x/design.html#the-i-o-loop)，2026-11-12 核对。
> - `setTimeout` 小于 1 的 delay 按 1 处理，计时器不保证准点：[Node.js v26.13.0, Timers, `setTimeout()`](https://nodejs.org/download/release/v26.13.0/docs/api/timers.html#settimeoutcallback-delay-args)，2026-11-12 核对。
> - `process.nextTick()` 的 Legacy 状态、额外参数与递归饿死 I/O；CJS 与 ESM 的队列顺序：[Node.js v26.13.0, Process, `process.nextTick()`](https://nodejs.org/download/release/v26.13.0/docs/api/process.html#processnexttickcallback-args)、[When to use queueMicrotask vs process.nextTick](https://nodejs.org/download/release/v26.13.0/docs/api/process.html#when-to-use-queuemicrotask-vs-processnexttick)，2026-11-12 核对。
> - 同步 `require()` 加载 ESM 的条件（无顶层 `await`）：[Node.js v26.13.0, Modules, Loading ECMAScript modules using require()](https://nodejs.org/download/release/v26.13.0/docs/api/modules.html#loading-ecmascript-modules-using-require)，2026-11-12 核对。
> - 本章各段代码的输出：于 Node.js v26.13.0 与 v26.13.1 运行；`io-demo.cjs` 顶层 timeout 与 immediate 相对 I/O 回调的位置在不同运行间变化，其余局部顺序一致。
## 17. Node.js 的工作实际在哪个线程或进程上执行？

本章回答：一个 Node.js 服务里，网络等待、文件读写、压缩、普通 JavaScript 计算分别在哪个线程或进程上执行；把 CPU 工作交给 `worker_threads`、子进程或 cluster 时，数据怎样传过去，取消和容量又怎样计算。读者手上有[上一章](#16.%20Node.js%20%E7%9A%84%E4%BA%8B%E4%BB%B6%E5%BE%AA%E7%8E%AF%E6%80%8E%E6%A0%B7%E5%AE%89%E6%8E%92%E8%AE%A1%E6%97%B6%E5%99%A8%E3%80%81I/O%20%E5%9B%9E%E8%B0%83%E5%92%8C%E5%BE%AE%E4%BB%BB%E5%8A%A1%EF%BC%9F)的事件循环模型：一条主线程按阶段和检查点运行回调。

沿用主线二的案例。`job-demo-731` 的 attempt 1 逐页读取报表 42 的数据（每页最多 100 行、最多 12 页），压缩后写入临时文件。本章先说明默认方案（内置 gzip）里各步在哪里执行，再展开对照方案：自建的同步增量压缩器放进 `worker_threads` 后，主线程和 worker 之间要遵守怎样的协议。

### await 之后的代码在哪里继续？

Node.js 进程里每个 JavaScript isolate (隔离环境) 都有自己的 JavaScript 执行线程和事件循环。主线程是一个 isolate，每个 `worker_threads` 又是一个。

`await` 不会把工作搬到别的线程。被等待的 Promise 结算后，`async` 函数的剩余部分作为 JavaScript 工作回到发起它的那个 isolate 继续运行。网络读取失败时，驱动的 Promise 被拒绝，异常也在同一个 isolate 里处理。Node 不会自动重试，调用方不再等待时也不会自动取消底层操作；连接能否取消、怎样释放，由驱动和应用的契约决定（原则见[主线二首章的取消一节](#%E5%8F%96%E6%B6%88%E8%83%BD%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)）。

### 各类 API 实际在哪里执行？

工作在哪里执行，要看调用的是哪个 API。下表合并了常见的几类路径（Node.js v26.13.0）：

| 工作或 API | 等待或计算发生在哪里 | 回调在哪里继续 | 占用什么、要注意什么 |
| --- | --- | --- | --- |
| 网络 socket、本例假设的异步数据库驱动 | 操作系统的异步 socket 机制（就绪通知或完成通知，取决于平台）；数据传输期间主调用栈不必等待 | 发起操作的 isolate 的事件循环 | 不占线程，但在途请求占连接和缓冲区；驱动若另有实现，以驱动文档为准 |
| `node:fs` 回调式与 Promise 式 API（`fs.FSWatcher` 除外）、`dns.lookup()`、`crypto.pbkdf2()` / `scrypt()` / 回调式 `randomBytes()` 等、异步 `node:zlib` | libuv threadpool (线程池) | 提交任务的那个事件循环 | 任务全程占一个池线程，阻塞在系统调用里的时间也算；排队任务要等空闲线程；长任务会拖慢同池的其他 API |
| 普通同步 JavaScript | 当前 isolate 的线程；Node 不会因为它耗 CPU 就自动搬走 | 运行完之前，同一事件循环不能运行别的回调 | 长计算直接推迟所有回调和计时器 |
| `node:worker_threads` | 应用创建的工作线程，运行 JavaScript，可与主线程并行 | 结果作为消息，在接收方的事件循环里处理 | 每个 worker 有自己的 isolate 和堆；线程数、排队任务和输入字节都要有上限 |
| `child_process.fork()` | 新的 Node.js 进程 | 父进程通过 IPC 消息收到结果 | 启动、内存和序列化成本；地址空间独立，但不是权限沙箱 |
| `node:cluster` | 多个 Node.js 进程共同对外提供服务 | 各进程各自的事件循环 | 每个进程有自己的堆、缓存和连接池；按连接分配，不按请求 |

libuv threadpool 和应用创建的 `worker_threads` 不是同一个池。Node.js v26.13.0 自带 libuv 1.52.1，这个线程池由同一进程内的所有事件循环共享，只执行特定 Node API 和 native addon 提交的工作，不执行任意 JavaScript。DNS 是常见的分界：`dns.lookup()` 用这个池，`dns.resolve()` 直接发异步 DNS 网络请求，不占池。反过来，`worker_threads` 也不是处理网络等待的捷径，网络等待用内置的异步 API 更合适。

按这张表，`job-demo-731` 的默认方案是：等数据库返回在主线程的事件循环上；收到的字节在主 isolate 里由驱动解析成报表行；内置 gzip 压缩和临时文件写入都在 libuv threadpool 里执行，完成回调回到主事件循环。

### 该把计算放在哪种执行资源上？

| 选择 | 适合什么工作 | 成本与条件 |
| --- | --- | --- |
| 主事件循环上的异步 API | 已有合适异步 API 的数据库、网络等 I/O 等待 | 让出调用栈不代表在途操作和缓冲区消失 |
| libuv threadpool 里的 API | Node 明确放进这个池的文件、DNS、加密和压缩操作 | 共享有限的池线程；它不是能任意提交 JavaScript 的应用工作池 |
| `worker_threads` | CPU 密集型 JavaScript，且值得承担消息传递和线程管理成本 | 同进程里的另一条 JavaScript 线程；要限制线程数、排队任务和输入字节 |
| `child_process` | 需要独立进程生命周期、地址空间或更强故障边界的工作 | 启动、内存和 IPC 成本；进程边界本身不限制权限 |
| `cluster` | 多个 Node 进程共同提供 HTTP/TCP 服务 | 进程间不共享会话和缓存；吞吐不保证随进程数线性增长 |

对照方案换掉了内置 gzip：自建的同步增量压缩器每处理一页都要占用超过主线程响应预算的 CPU 时间，所以放进 `worker_threads`。如果改回内置的异步 zlib，计算就回到 libuv threadpool，占用的是另一种共享资源。

多个导出任务同时到达时，不能每来一个就新建一个 worker。应使用大小固定的 worker pool (工作线程池) 加有界等待队列；队列满时，由服务明确选择拒绝、等待，还是向上游施加背压。有界等待队列可以用环形缓冲区或头下标实现，避免 `shift()` 逐个搬移元素的成本，见[待处理的工作该用队列还是栈，各怎样实现？](#5.%20%E5%BE%85%E5%A4%84%E7%90%86%E7%9A%84%E5%B7%A5%E4%BD%9C%E8%AF%A5%E7%94%A8%E9%98%9F%E5%88%97%E8%BF%98%E6%98%AF%E6%A0%88%EF%BC%8C%E5%90%84%E6%80%8E%E6%A0%B7%E5%AE%9E%E7%8E%B0%EF%BC%9F)；整条异步管线各段的容量怎样估算，见[一条异步管线能接多少工作，超出时在哪里拒绝？](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)。

### 主线程和 worker 之间怎样传数据？

worker 有自己的 isolate 和普通堆，主线程里的普通对象不会因为同处一个地址空间就对它可见；但两者仍属同一个操作系统进程，共享进程的生命周期和身份。双方用 `postMessage()` 传数据，有三种方式：

- 普通可克隆值经 structured clone (结构化克隆) 复制一份。发送 `Buffer` 时，接收方得到的是 `Uint8Array`，需要 Buffer API 时在接收侧再转换。
- 把可转移的 `ArrayBuffer` 放进 transfer list (转移列表)，就把这块内存的所有权交给对方，发送方原来的视图随即不可用。转移的内存必须由本次任务独占，例如单独分配的 `new ArrayBuffer(n)`；不要转移池化 `Buffer`（Node 从共享内存池中切出的小 Buffer）的 `.buffer`，它通常不能转移，克隆时还可能把整个池一起复制。
- 只有 `SharedArrayBuffer` 让双方访问同一块字节。可能同时访问时，要用 `Atomics` 同步，或用消息明确交接访问权（见[共享状态一章的所有权规则](#%E5%85%B1%E4%BA%AB%E4%B8%8D%E5%8F%98%E9%87%8F%E8%A6%81%E9%80%89%E5%93%AA%E7%A7%8D%E6%89%80%E6%9C%89%E6%9D%83%E8%A7%84%E5%88%99%EF%BC%9F)）。

![一个 Node.js 进程内主线程与工作线程的数据所有权，以及与进程边界的区别](../../engineering-foundations/runtime/resources/node-js-fundamentals-thread-ownership.svg)

无论复制还是转移，消息数量、数据量和等待队列都要受控。`job-demo-731` 每次发给 worker 的是一页报表行，最多 100 行，大小有界。

### 有状态的压缩怎样逐页交给 worker？

自建压缩器有内部状态，同一个 job 的各页必须按顺序交给同一个 worker。主线程上推进 job 状态的代码称为协调者；它与 worker 遵守下面的协议，使在途输入最多只有一页：

1. **占槽。** job 从有界等待队列取出、分到一个 worker 槽后，就固定在这条线程上；还在排队的 job 不占槽。等待读库或写文件时 worker 可能空闲，但这个运行中的 job 仍占着槽。
2. **逐页处理。** 协调者读到一页后发给 worker。worker 同步压缩这一页，按顺序回传零个或多个压缩块，再单独发一条 `batchDone`。完成确认与块数无关，所以一页没有产出字节也能正常结束。
3. **写完再取下一页。** 协调者按顺序提交这一页输出的异步文件写入；只有写入全部完成**并且**收到 `batchDone`，才请求下一页。这比普通的流背压更严格：流的 `write()` 返回 `true` 只说明可以继续提交，返回 `false` 才需要等 `drain`（流一章细讲），而这里要求本页写入已经完成。写入完成也不等于数据已持久落盘。
4. **收尾与归还槽。** 游标读到末尾后，协调者通知同一个 worker flush 压缩流。worker 发完全部尾块、清除这个 job 的压缩状态后，发出 `streamFinished`，表示它不会再产出字节；协调者收到后才把槽归还线程池。写入方确认所有尾块（也可能没有尾块）都已写完，才关闭临时文件。

![job-demo-731 的一页数据从异步数据库等待、主事件循环到 CPU 工作线程的一种可能交错](../../engineering-foundations/runtime/resources/node-js-fundamentals-acct17-runtime-sequence.svg)

图是一种可能的交错，不按时间比例。读图时注意三点：socket 通知只说明字节到了，驱动还要在主 isolate 里解析出一页报表行，`cursor.next()` 的 Promise 才结算；worker 压缩或 libuv 池写文件期间，主事件循环仍可运行其他回调；worker 的消息和写入的完成回调，都要等对应的事件循环轮到它们才执行。临时文件写完后怎样发布、发布与取消同时到达时谁说了算，见[流一章的发布裁决](#%E4%B8%AD%E9%80%94%E5%A4%B1%E8%B4%A5%E7%95%99%E4%B8%8B%E4%BB%80%E4%B9%88%EF%BC%9A%E9%83%A8%E5%88%86%E8%BE%93%E5%87%BA%E4%B8%8E%E5%8F%91%E5%B8%83%E8%A3%81%E5%86%B3)。

### worker 为什么收不到取消消息？

取消一个正在压缩的 job 时，协调者会给 worker 发一条 `stop` 消息。但 worker 正在执行同步 JavaScript 时，它自己的消息回调也要等当前回调返回才能运行。如果 worker 在一次同步调用里连续处理所有片段，只在片段之间检查一个“由消息回调设置的变量”，它永远看不到新值，因为消息回调根本没有机会运行。

让取消生效有两种办法：

- 在片段之间把控制权交还事件循环，例如 `await setImmediate()`（来自 `node:timers/promises`），让消息回调有机会运行。
- 协调者对一块 `SharedArrayBuffer` 执行 `Atomics.store()` 设置停止标志，worker 在片段之间用 `Atomics.load()` 检查。这种方式不需要让出事件循环。

> [!example]- 可运行的对照：三种 worker 停止方式
> 每段约 20 ms 的同步计算代表一片压缩工作，主线程在 50 ms 时同时发出 `stop` 消息并设置共享标志。
>
> ~~~javascript
> // 保存为 worker-stop.cjs；node worker-stop.cjs none|yield|atomics
> const { Worker, isMainThread, parentPort, workerData } = require('node:worker_threads');
> const { setImmediate: yieldToLoop } = require('node:timers/promises');
>
> function compressSegment() {
>   const end = Date.now() + 20;
>   while (Date.now() < end) {}
> }
>
> if (isMainThread) {
>   const stop = new Int32Array(new SharedArrayBuffer(4));
>   const worker = new Worker(__filename, { workerData: { mode: process.argv[2], stop } });
>   worker.on('message', message => { console.log(message); worker.terminate(); });
>   setTimeout(() => {
>     worker.postMessage('stop');
>     Atomics.store(stop, 0, 1);
>   }, 50);
> } else {
>   const { mode, stop } = workerData;
>   let stopRequested = false;
>   parentPort.on('message', message => { if (message === 'stop') stopRequested = true; });
>   (async () => {
>     for (let segment = 1; segment <= 20; segment++) {
>       compressSegment();
>       if (mode === 'atomics' && Atomics.load(stop, 0) === 1) {
>         return parentPort.postMessage(`stopped after segment ${segment} (Atomics)`);
>       }
>       if (mode === 'yield') await yieldToLoop();
>       if (stopRequested) return parentPort.postMessage(`stopped after segment ${segment} (message)`);
>     }
>     parentPort.postMessage('finished all 20 segments');
>   })();
> }
> ~~~
>
> 在 Node.js v26.13.1 上，`none` 模式跑完全部 20 段才结束，消息回调始终没有运行；`yield` 和 `atomics` 模式都在几段之后停下。具体段数取决于 worker 启动耗时。

无论哪种办法，worker 都只能在当前片段结束后响应，所以“停止确认”要在片段结束、压缩状态清理之后才发出，协调者收到确认才归还槽。

worker 的故障边界也有限：worker 抛出未捕获的 JavaScript 错误时，父线程可以通过 `Worker` 的 `error` 事件处理；但 worker 不是独立进程，native 代码崩溃会波及整个进程。

### 子进程给了哪些隔离？

需要更强的隔离时，可以把计算交给子进程。`child_process.fork()` 启动一个新的 Node.js 进程并建立 IPC (进程间通信) 通道。它不是 POSIX 的 `fork(2)`，不会复制正在运行的父进程内存。`send()` 发出的消息先序列化，再在另一侧解析，默认格式是 JSON；传较大的数据批次时，序列化和复制都有成本。也可以显式传递受支持的 socket 或其他 handle (句柄)。

子进程有独立的地址空间，但如果不另行设置运行身份和操作系统策略，父进程用户能访问的资源它照样能访问；进程边界也不会自动隔开磁盘、网络、CPU 配额或数据库连接额度。

> [!example]- 可运行的最小示例：父子进程交换一条计算请求
> ~~~javascript
> // 保存为 report-child.cjs；node report-child.cjs
> const { fork } = require('node:child_process');
>
> function fib(n) {
>   let a = 0;
>   let b = 1;
>   for (let i = 0; i < n; i++) [a, b] = [b, a + b];
>   return a;
> }
>
> if (process.argv[2] === 'worker') {
>   process.on('message', ({ n }) => process.send({ result: fib(n) }));
> } else {
>   const child = fork(__filename, ['worker']);
>   child.once('error', error => { console.error(error); process.exitCode = 1; });
>   child.once('message', ({ result }) => { console.log(result); child.disconnect(); });
>   child.send({ n: 10 });
> }
> ~~~
>
> 输出 `55`。它只展示请求与结果消息的往返，计算量太小，不能说明进程能加速；也没有排队上限、重复任务保护或进程监管者的重启策略。

### cluster 怎样分配连接，容量怎样按进程相乘？

前面两种方式是把一段计算交出去；`cluster` 解决另一个问题：让多个 Node 进程一起对外提供服务。cluster 的 worker 是子进程，不是 `worker_threads`。

除 Windows 外，cluster 默认采用 round-robin (轮询)：primary (主进程) 在监听端口上接收新的 TCP 连接，再依次交给一个 worker；Windows 默认由各 worker 自行接受连接。分配单位是连接，不是 HTTP 请求：同一条持久连接上的多个请求都落到同一个进程。登录会话和缓存不会在 worker 之间共享，需要共享时用进程外存储或明确的通信协议。

![child_process.fork 的序列化消息边界，以及 cluster 默认轮询时由 primary 分发连接](../../engineering-foundations/runtime/resources/node-js-fundamentals-process-cluster.svg)

~~~javascript
// 保存为 cluster-report.cjs；node cluster-report.cjs
const cluster = require('node:cluster');
const http = require('node:http');
const { availableParallelism } = require('node:os');

const configuredLimit = 2;    // 教学配置
const workerCount = Math.min(availableParallelism(), configuredLimit);

if (cluster.isPrimary) {
  for (let i = 0; i < workerCount; i++) cluster.fork();
  cluster.on('exit', (worker, code, signal) => {
    console.error('worker exited', worker.id, code, signal);
  });
} else {
  http.createServer((request, response) => {
    response.end(`report API served by process ${process.pid}`);
  }).listen(8000);
}
~~~

示例中 worker 退出时只记日志：Node 不会自动补起退出的进程，也不替你决定重启退避策略。Node 文档建议用 `os.availableParallelism()` 而不是 `os.cpus().length` 估算可用并行度；实际进程数还要按容器 CPU 配额、请求时延和每个进程的连接池等总资源决定。每个进程有独立的 JavaScript 堆、缓存和池，进程越多内存需求通常越高，不过操作系统可能让进程共享只读内存页，所以不一定严格成倍增长。

容量要按“每进程”计数再相乘。本例运行 2 个 cluster worker，每个配 2 个 CPU 工作线程槽、最多 5 个数据库连接，整个服务的配置上限就是 2 × 2 = 4 个计算槽、2 × 5 = 10 个数据库连接。4 个槽不保证有 4 个处理器核心能同时运行它们；如果共享的 CPU 配额或数据库容量更小，请求仍会排队。连接总数是否超过数据库允许的上限，按[整套部署最多会开多少数据库连接？](#%E6%95%B4%E5%A5%97%E9%83%A8%E7%BD%B2%E6%9C%80%E5%A4%9A%E4%BC%9A%E5%BC%80%E5%A4%9A%E5%B0%91%E6%95%B0%E6%8D%AE%E5%BA%93%E8%BF%9E%E6%8E%A5%EF%BC%9F)的连接预算核对。用 PM2 这类进程管理器管理多个实例时的停止信号与超时，见[服务该跑在哪种运行时上，平台怎样启动、探测和停止它？](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)。

### 下一步：同样的问题在 Python 里

本章的产出是一张执行位置表和一份有界的 worker 槽协议：网络等待留在事件循环，文件、DNS、加密、压缩按 API 进入 libuv threadpool，CPU 密集的 JavaScript 进入固定大小的 worker 池，一页一确认、收尾确认后才归还槽；容量按每进程的槽和连接相乘。如果服务用 Python 写，同样的问题换了一套规则：`async def` 路由为什么仍会卡住事件循环，取消和资源怎样收尾，见[下一章](#18.%20%E5%BC%82%E6%AD%A5%20FastAPI%20%E6%8E%A5%E5%8F%A3%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BB%8D%E4%BC%9A%E9%98%BB%E5%A1%9E%EF%BC%8C%E5%8F%96%E6%B6%88%E5%92%8C%E8%B5%84%E6%BA%90%E5%8F%88%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%EF%BC%9F)。

> [!info]- 来源
> - `worker_threads` 的 CPU 用途、`postMessage` 的结构化克隆、转移列表与 `SharedArrayBuffer`：[Node.js v26.13.0, Worker threads](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html)、[`worker.postMessage()`](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html#workerpostmessagevalue-transferlist)，2026-11-12 核对。
> - 转移后发送方视图失效、池化 Buffer 不能直接转移、Buffer 接收为 Uint8Array：[Node.js v26.13.0, Worker threads, Considerations when transferring TypedArrays and Buffers](https://nodejs.org/download/release/v26.13.0/docs/api/worker_threads.html#considerations-when-transferring-typedarrays-and-buffers)，2026-11-12 核对。
> - 多线程共享字节区的同步：[ECMAScript Shared Memory Guidelines](https://tc39.es/ecma262/multipage/memory-model.html#sec-shared-memory-guidelines)，2026-11-12 核对。
> - 异步文件 API、`dns.lookup()` 与 `dns.resolve()` 的不同实现、`crypto.pbkdf2()` / `scrypt()` 等与异步 zlib 使用 libuv 线程池：[Node.js v26.13.0, File system](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#threadpool-usage)、[DNS, Implementation considerations](https://nodejs.org/download/release/v26.13.0/docs/api/dns.html#implementation-considerations)、[Crypto](https://nodejs.org/download/release/v26.13.0/docs/api/crypto.html)、[Zlib](https://nodejs.org/download/release/v26.13.0/docs/api/zlib.html#threadpool-usage-and-performance-considerations)，2026-11-12 核对。
> - libuv 线程池由进程内所有事件循环共享，完成回调回到事件循环：[libuv 1.x, Thread pool work scheduling](https://docs.libuv.org/en/v1.x/threadpool.html)；Node.js v26.13.0 自带 libuv 1.52.1：[`deps/uv/include/uv/version.h`](https://github.com/nodejs/node/blob/v26.13.0/deps/uv/include/uv/version.h)、[Node.js 发布索引](https://nodejs.org/dist/index.json)，2026-11-16 核对。
> - `Writable.write()` 的 `true` / `false` 与 `drain`：[Node.js v26.13.0, Stream, `writable.write()`](https://nodejs.org/download/release/v26.13.0/docs/api/stream.html#writablewritechunk-encoding-callback)，2026-11-12 核对。
> - 让出事件循环的 Promise 版 `setImmediate()`：[Node.js v26.13.0, Timers](https://nodejs.org/download/release/v26.13.0/docs/api/timers.html#timerspromisessetimmediatevalue-options)，2026-11-12 核对；三种停止方式的对照脚本于 Node.js v26.13.1 运行。
> - `child_process.fork()` 启动新 Node 实例、IPC 序列化与默认 JSON：[Node.js v26.13.0, Child processes, `fork()`](https://nodejs.org/download/release/v26.13.0/docs/api/child_process.html#child_processforkmodulepath-args-options)，示例于该版本重放输出 `55`。
> - cluster 共享端口、连接调度方式与进程内状态不共享：[Node.js v26.13.0, Cluster, How it works](https://nodejs.org/download/release/v26.13.0/docs/api/cluster.html#how-it-works)，2026-11-12 核对。
> - `availableParallelism()` 与 `os.cpus().length` 的区别：[Node.js v26.13.0, OS](https://nodejs.org/download/release/v26.13.0/docs/api/os.html#osavailableparallelism)，2026-11-12 核对。
## 18. 异步 FastAPI 接口为什么仍会阻塞，取消和资源又怎样收尾？

本章回答三个问题：`async def` 写的 FastAPI 接口为什么仍可能卡住整个事件循环；任务被取消或超时时，协程、线程和远端操作各自会怎样；数据库会话这类资源应该保持打开到什么时候。读者手上有前几章的 Node 模型：一条线程上的事件循环只在让出点切换，取消只是请求，CPU 工作要交给有界的线程或进程。Python 的 asyncio 在这些原则上相同，具体规则不同。

**案例。** 同一个报表服务的 API 也有 Python 实现。FastAPI 路由为账户 `acct-17` 分三页读取报表数据：第 1 页还没返回时，处理这个请求的 Task 挂起；如果此时有一个 `/health` 请求已经可以处理，同一个事件循环就先处理它。下面的演示用合成等待代替数据库：异步读取每页等 40 ms，同步读取每页阻塞 60 ms。版本：CPython 3.11.13、FastAPI 0.128.0、Starlette 0.47.2、AnyIO 4.12.1。

### 协程什么时候让出事件循环？

调用 `async def` 函数并不立即执行函数体，而是先得到一个 coroutine object (协程对象)。FastAPI 在为请求创建的 Task 里调用路由，由 event loop (事件循环) 驱动这个 Task 运行。Task 是事件循环推进协程的调度单位；同一个事件循环上，同一时刻只有一个 Task 在执行代码。

只有当 Task 等待一个尚未就绪的 Future（异步结果对象）或 I/O 而挂起时，事件循环才有机会推进其他就绪的 Task。这就是 asyncio 的让出点。由此有三点推论：

- `await` 不保证每次都切换任务：被等待的对象已经就绪时，当前 Task 可以直接继续。
- `async def` 不会把函数放到别的线程执行。
- 在协程里直接调用 `time.sleep()`、同步数据库驱动或长时间的 Python 计算时，没有任何让出点，事件循环要等它返回才能处理其他任务。

![异步等待与直接同步调用对事件循环的影响](../../engineering-foundations/runtime/resources/python-async-await-scheduling.svg)

### FastAPI 里各种写法在哪里执行？

| 写法 | 执行位置 | 要注意什么 |
| --- | --- | --- |
| 在 `async def` 里 `await` 原生异步数据库或 HTTP API | 事件循环线程；I/O 未完成时挂起当前 Task | 这是报表分页的主路径 |
| 在 `async def` 里直接调用同步辅助函数 | 事件循环线程 | FastAPI 不会拦截你自己调用的普通函数，整个循环被占住 |
| 把路由或依赖本身声明为 `def` | FastAPI/Starlette 通过 AnyIO 的工作线程执行 | 线程容量有限，超出的调用排队等待 |
| 在异步路由里用 `asyncio.to_thread()` 运行短时阻塞 I/O | asyncio 默认 executor (执行器) 的线程 | 容量与 AnyIO 的限额分开配置 |
| 把纯 Python 的 CPU 密集工作交给有界进程池或独立 worker 进程 | 其他进程 | 能多核并行；要承担进程调度、序列化和内存成本 |

在这个案例里：`/reports/acct-17` 每等一页都让出事件循环；`/blocking/acct-17` 在路由里直接执行三次同步读取，事件循环要等 3 × 60 = 180 ms 的合成阻塞结束才能处理 `/health`。`/offloaded` 把同一个同步函数放进 asyncio 默认 executor，`/sync-route` 由 FastAPI 交给 AnyIO 工作线程；这两条路都让事件循环继续运行，但各自占用不同的线程容量，而且把工作挪到线程上并不减少下游数据库或文件操作本身的开销。`/reports` 还通过 `Depends(load_settings)` 用了一个普通 `def` 依赖：由 FastAPI 调用的同步依赖会进入 AnyIO 工作线程，这和在 `async` 路由里自己调用同步函数是两回事。

> [!example]- 可运行示例：四种写法
> ~~~python
> import asyncio
> import time
>
> from fastapi import Depends, FastAPI
>
> app = FastAPI()
>
> async def fetch_page(account: str, page: int) -> dict[str, object]:
>     await asyncio.sleep(0.04)  # 合成的异步 I/O 等待
>     return {"account": account, "page": page}
>
> def fetch_page_sync(account: str, page: int) -> dict[str, object]:
>     time.sleep(0.06)  # 合成的同步阻塞
>     return {"account": account, "page": page}
>
> async def read_pages_async(account: str) -> list[dict[str, object]]:
>     rows = []
>     for page in range(1, 4):
>         rows.append(await fetch_page(account, page))
>     return rows
>
> def read_pages_sync(account: str) -> list[dict[str, object]]:
>     return [fetch_page_sync(account, page) for page in range(1, 4)]
>
> def load_settings() -> dict[str, str]:
>     return {"region": "demo"}
>
> @app.get("/reports/{account}")
> async def report(account: str, settings: dict[str, str] = Depends(load_settings)):
>     return {"region": settings["region"], "rows": await read_pages_async(account)}
>
> @app.get("/blocking/{account}")
> async def blocking_report(account: str):
>     return {"rows": read_pages_sync(account)}
>
> @app.get("/offloaded/{account}")
> async def offloaded_report(account: str):
>     return {"rows": await asyncio.to_thread(read_pages_sync, account)}
>
> @app.get("/sync-route/{account}")
> def sync_route(account: str):
>     return {"rows": read_pages_sync(account)}
>
> @app.get("/health")
> async def health():
>     return {"status": "ok"}
> ~~~

### 交给线程的同步代码，容量有多大？

Starlette 用 AnyIO 运行同步路由、同步依赖和它自己的部分内部同步操作，这些调用共用 AnyIO 默认的 worker thread limiter：40 个并发令牌（AnyIO 4.12.1）。几点含义：

- 40 是上限，不是需要填满的目标。调高它会让更多线程同时执行，线程本身和下游数据库的压力都会上升，要按每个进程的线程与连接预算评估。
- asyncio 默认 executor 不受这个限额约束，`to_thread()` 用的是另一份容量。
- 并发上限只限制同时运行的调用数，不限制排队数。排队长度要按资源预算另设，并在入口做准入控制（全局的准入与拒绝见[一条异步管线能接多少工作，超出时在哪里拒绝？](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)）。

### 线程能让 CPU 工作并行吗？

在默认的 CPython 构建里，Global Interpreter Lock (全局解释器锁，GIL) 使多个普通 Python 线程通常不能同时执行 Python 字节码。所以把 CPU 密集的纯 Python 函数放进 `asyncio.to_thread()`，只是不再直接占住事件循环，通常得不到多核并行；这类工作更适合交给进程池或独立的 worker 进程。

> [!info] 版本说明：free-threaded 构建
> CPython 3.13 起提供可选的 free-threaded (自由线程) 构建，3.14 起进入正式支持阶段（PEP 779），但仍需单独选择，默认构建依然带 GIL。某些扩展模块可能在 free-threaded 构建里重新启用 GIL；实际收益和线程安全要按所用解释器和依赖逐一验证。本章示例使用默认构建的 CPython 3.11。

### 怎样显式并发，会话怎样隔离？

回到分页：`await fetch_page(...)` 写在循环里，仍是一页一页顺序读取，`await` 不会自动创建并发任务。要并发查询多个页面，必须显式创建子 Task：`asyncio.create_task()`，或 Python 3.11 引入的 TaskGroup (任务组) 的 `create_task()`。创建者负责收集结果、等待子任务结束；TaskGroup 会在退出 `async with` 块之前等待组内任务全部完成。不要留下无人管理的后台 Task。

并发的 Task 不能共用同一个 SQLAlchemy `AsyncSession`：会话不是并发安全的，每个 Task 要有自己的会话；请求和 worker 的每次 attempt 也应各自持有短生命周期的会话。会话借出连接的时长怎样决定连接池的容量，见[ORM 会话怎样借用连接，连接池为什么会耗尽？](#28.%20ORM%20%E4%BC%9A%E8%AF%9D%E6%80%8E%E6%A0%B7%E5%80%9F%E7%94%A8%E8%BF%9E%E6%8E%A5%EF%BC%8C%E8%BF%9E%E6%8E%A5%E6%B1%A0%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E8%80%97%E5%B0%BD%EF%BC%9F)。

### 吞掉 CancelledError 会怎样？

客户端断开、超时或停机时，正在运行的 Task 会被取消。`Task.cancel()` 只是发出取消请求：事件循环在下一次调度这个 Task 时，向协程内部抛入 `CancelledError`。正确的处理方式是在 `finally` 里关闭游标、会话或临时文件，然后让 `CancelledError` 继续向外传播，使调用方按“已取消”处理。

如果捕获 `CancelledError` 后正常返回，取消就被吞掉了，后果是三处判断同时出错：

- 调用方看到的是正常结果，而不是取消。
- 若这次取消来自 `asyncio.timeout()`，超时作用域会正常退出，不抛 `TimeoutError`。
- TaskGroup 会把这个子任务当作正常完成，打乱调用方预期的取消流程。

~~~python
import asyncio

async def swallow():
    try:
        await asyncio.sleep(1)
    except asyncio.CancelledError:
        return "cleanup done, cancellation swallowed"

async def propagate():
    try:
        await asyncio.sleep(1)
    finally:
        print("cleanup done")

async def main():
    async with asyncio.timeout(0.01):
        print(await swallow())
    print("timeout scope exited normally")

    try:
        async with asyncio.timeout(0.01):
            await propagate()
    except TimeoutError:
        print("TimeoutError")

asyncio.run(main())
~~~

CPython 3.11.13 输出 `cleanup done, cancellation swallowed`、`timeout scope exited normally`、`cleanup done`、`TimeoutError`：吞掉取消的版本让超时“消失”了；在 `finally` 里清理后让取消传播的版本，超时照常报告。

### asyncio.timeout 为什么打不断同步阻塞？

`asyncio.timeout(秒数)` 也是靠事件循环调度一次取消来实现的。如果一个同步函数堵住了事件循环，截止时间到了，负责取消的回调也无法运行。

在 CPython 3.11.13 上运行：用 `asyncio.timeout(0.01)` 包住 `time.sleep(0.05)`，代码约 0.05 s 后正常离开作用域，没有 `TimeoutError`。阻塞调用返回后，只有协程还在作用域内**等待一个尚未就绪的异步操作**，迟到的取消才有机会生效：紧接着 `await asyncio.sleep(0)` 仍然正常退出，换成等待一段正时长（如 `await asyncio.sleep(0.001)`）才抛出 `TimeoutError`。

所以超时不是中断任意同步函数的机制，这一点与 Node 的计时器相同（见[事件循环一章](#%E9%95%BF%E5%90%8C%E6%AD%A5%E5%9B%9E%E8%B0%83%E5%AF%B9%E8%AE%A1%E6%97%B6%E5%99%A8%E5%81%9A%E4%BA%86%E4%BB%80%E4%B9%88%EF%BC%9F)）。

### 取消等待 to_thread 的 Task，线程会怎样？

取消一个正在等待 `asyncio.to_thread(blocking_call)` 的 Task，只是异步调用方不再等待。函数若已在线程里运行，Python 不会强行杀掉这个线程；只有还在 executor 队列里、尚未开始的工作，才可能在执行前被取消。

线程可能仍在使用文件、连接或其他资源，所以释放连接池、关闭共享句柄之前，要先确认线程已经结束。需要让线程协作停止时，给 `asyncio.to_thread()` 的函数传入一个 `threading.Event` 作为停止信号并定期检查；在 AnyIO 工作线程里，可以调用 `from_thread.check_cancelled()` 做协作式检查。

远端操作同样不受本地取消影响。客户端超时或断线时，一次写操作可能没到服务端，可能已回滚，也可能已提交而响应丢失；调用方只能通过权威状态查明结果，不能把断线当作失败。主线四的结论是：用同一个幂等键重放请求，取回同一操作的当前状态，见[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

### yield 依赖应该何时释放资源？

取消之外，资源还有“何时关闭”的问题。带 `yield` 的依赖适合把资源的打开和清理写在一起：`yield` 之前打开数据库会话或游标，`yield` 之后（通常在 `finally` 里）清理。清理时点由依赖的作用域决定：

- 默认 request scope (请求作用域)：FastAPI 调用路由前打开资源，在应用发送完响应正文后清理。“发送完”指 ASGI 的最后一个 `http.response.body` 事件（`more_body=False`）已经发出，不代表客户端已经收齐所有字节。
- `Depends(scope="function")`（FastAPI 0.121.0 起支持）：function scope (函数作用域)，在路由函数返回之后、响应发送之前清理。

两者的差别在响应体的生成方式不同时才显现。返回小型 JSON 时，路由函数内已经读完所需数据，function scope 可以提前释放资源，缩短占用时间。返回 `StreamingResponse` 时，正文生成器要在路由返回**之后**才逐块读取数据库游标；若用 function scope，路由一返回资源就被关闭，后续读取会失败。所以流式响应应让 request scope 覆盖整个正文发送过程，并在依赖的 `finally` 里清理，无论正文正常发完、被中止还是出错。

![FastAPI yield 依赖作用域与响应正文的关系](../../engineering-foundations/runtime/resources/python-fastapi-yield-lifetimes.svg)

下面的最小应用验证这个边界。`Store` 是合成对象：`close()` 之后再调用 `read_row()` 会抛 `RuntimeError`，这是教学用的资源契约，不代表某个数据库驱动的异常类型。

~~~python
import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

class Store:
    def __init__(self) -> None:
        self.closed = False

    async def read_row(self) -> bytes:
        await asyncio.sleep(0)
        if self.closed:
            raise RuntimeError("Store is closed")
        return b"acct-17,42\n"

    async def close(self) -> None:
        self.closed = True

async def get_store() -> AsyncIterator[Store]:
    store = Store()
    try:
        yield store
    finally:
        await store.close()

@app.get("/row")
async def read_row(store: Annotated[Store, Depends(get_store, scope="function")]):
    row = await store.read_row()
    return {"row": row.decode().strip()}

@app.get("/stream")
async def stream_rows(store: Annotated[Store, Depends(get_store)]):
    async def body():
        yield b"account,report_id\n"
        yield await store.read_row()

    return StreamingResponse(body(), media_type="text/csv")
~~~

用合成 `Store` 记录 ASGI 事件顺序：`/row` 是 `open → read → close → 发送 JSON`；`/stream` 是 `open → 发送 CSV 表头 → 读取 Store → 发送正文结束 → close`。把 `/stream` 的依赖改成 `scope="function"` 再运行，顺序变成 `open → close → response.start(200) → CSV 表头 → read 抛 RuntimeError`，最后一帧正文也没有发出。

### 下一步：需要可查询的结果时

本章的产出是一组 Python 侧的规则：同步代码在 `async def` 里会卡住事件循环，要么换成异步 API，要么交给有上限的线程或进程；取消在 `finally` 里清理后必须继续传播；超时打不断同步阻塞，取消 `to_thread` 只停止等待；资源的作用域要覆盖它最后一次被使用的时刻。

直接流式响应把连接、游标和请求的生命周期绑在一起，客户端断开后也留不下可查询的结果。报表需要在后台可靠生成、稍后再下载时，应改用持久受理的 job：受理时写入持久记录，worker 的每次 attempt 重新获取会话和连接，见[耗时任务怎样被持久受理，并保证一定会被唤醒？](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)。

本主线接下来回到 Node 的导出流水线，看[流怎样把“慢下来”传回源头](#20.%20%E6%B5%81%E6%80%8E%E6%A0%B7%E6%8A%8A%E2%80%9C%E6%85%A2%E4%B8%8B%E6%9D%A5%E2%80%9D%E9%80%90%E6%AE%B5%E4%BC%A0%E5%9B%9E%E6%BA%90%E5%A4%B4%EF%BC%8C%E4%B8%AD%E9%80%94%E5%A4%B1%E8%B4%A5%E5%8F%88%E7%95%99%E4%B8%8B%E4%BB%80%E4%B9%88%EF%BC%9F)。对 Python 对象模型本身（名字绑定、生成器、`with`、描述符与 MRO）有疑问的读者，可以先读支线[Python 的名字、对象和属性按什么规则工作](#19.%20Python%20%E7%9A%84%E5%90%8D%E5%AD%97%E3%80%81%E5%AF%B9%E8%B1%A1%E5%92%8C%E5%B1%9E%E6%80%A7%E6%8C%89%E4%BB%80%E4%B9%88%E8%A7%84%E5%88%99%E5%B7%A5%E4%BD%9C%EF%BC%9F)。

> [!info]- 来源
> - `async def` 返回协程、Task 等待 Future 时挂起、事件循环一次运行一个 Task；TaskGroup：[Python 3.11, Coroutines and Tasks](https://docs.python.org/3.11/library/asyncio-task.html#coroutines)，§Coroutines、§Task Object、[§Task Groups](https://docs.python.org/3.11/library/asyncio-task.html#task-groups)，2026-11-12 核对；调度示例于 CPython 3.11.13 重放。
> - `asyncio.timeout()` 通过取消当前 Task 实现，`asyncio.to_thread()` 在独立线程运行：[Python 3.11, Coroutines and Tasks, §Timeouts、§Running in Threads](https://docs.python.org/3.11/library/asyncio-task.html#timeouts)；已开始运行的 Future 不能被 `cancel()` 终止：[concurrent.futures, `Future.cancel()`](https://docs.python.org/3.11/library/concurrent.futures.html#concurrent.futures.Future.cancel)，2026-11-12 核对；阻塞超时分支与吞掉 `CancelledError` 的对照示例于 CPython 3.11.13 运行。
> - `to_thread()` 使用默认线程执行器，CPU 工作可用进程池：[Python 3.11, Event Loop, Executing code in thread or process pools](https://docs.python.org/3.11/library/asyncio-eventloop.html#executing-code-in-thread-or-process-pools)，2026-11-12 核对。
> - 不能强杀已运行线程，`threading.Event` 作停止信号：[Python 3.11, threading, Event objects](https://docs.python.org/3.11/library/threading.html#event-objects)；AnyIO 工作线程的 `from_thread.check_cancelled()`：[AnyIO, Working with threads, Reacting to cancellation in worker threads](https://anyio.readthedocs.io/en/stable/threads.html)，2026-11-12 核对。
> - FastAPI 的同步路由和同步依赖在线程池执行，直接调用的普通函数不受影响：[FastAPI, Concurrency and async / await, Very Technical Details](https://fastapi.tiangolo.com/async/)，FastAPI 0.128.0、Starlette 0.47.2、AnyIO 4.12.1 行为于 2026-11-12 核对。
> - Starlette 用 AnyIO 运行同步端点、依赖与内部同步操作，默认 40 tokens：[Starlette, Thread Pool, Concurrency Limitations](https://starlette.dev/threadpool/#concurrency-limitations)；AnyIO 限额不影响 asyncio 默认 executor：[AnyIO, Working with threads, Adjusting the default maximum worker thread count](https://anyio.readthedocs.io/en/stable/threads.html)，2026-11-12 核对。
> - 默认 CPython 的 GIL、free-threaded 构建与扩展模块重新启用 GIL：[Python support for free threading](https://docs.python.org/3/howto/free-threading-python.html)，§Installation、§The global interpreter lock in free-threaded Python；3.14 正式支持：[PEP 779](https://peps.python.org/pep-0779/)，§Abstract，2026-11-12 核对。
> - SQLAlchemy 2.0 的 `AsyncSession` 不可在并发 Task 间共享：[Using AsyncSession with Concurrent Tasks](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncsession-with-concurrent-tasks)，2026-11-12 核对。
> - `yield` 依赖默认 request scope，function scope 在路由返回后、响应发送前退出：[FastAPI, Dependencies with yield, Early exit and scope](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)；scope 参数自 [FastAPI 0.121.0](https://fastapi.tiangolo.com/release-notes/#01210) 加入；在 FastAPI 0.128.0、Starlette 0.47.2 上以本机 ASGI trace 核对，2026-11-12。
> - Starlette 0.47.2 的 `StreamingResponse` 逐块发送正文，断连或发送错误会结束流生成任务：[pinned responses.py](https://github.com/Kludex/starlette/blob/0.47.2/starlette/responses.py#L220-L278)，2026-11-12 核对；trace 不是 TCP 断线测试。
> - ASGI 最后一个 `http.response.body` 以 `more_body=False` 表示应用已发完正文：[ASGI HTTP, Response Body](https://asgi.readthedocs.io/en/stable/specs/www.html#response-body-send-event)，2026-11-12 核对。
## 19. Python 的名字、对象和属性按什么规则工作？

这是挂在 [asyncio 一章](#18.%20%E5%BC%82%E6%AD%A5%20FastAPI%20%E6%8E%A5%E5%8F%A3%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BB%8D%E4%BC%9A%E9%98%BB%E5%A1%9E%EF%BC%8C%E5%8F%96%E6%B6%88%E5%92%8C%E8%B5%84%E6%BA%90%E5%8F%88%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%EF%BC%9F)后的支线，回答 Python 写服务时最常绊倒人的两组规则：名字、对象和资源之间是什么关系（修改会被谁看到，生成器何时执行，`with` 清理了什么）；读写 `obj.attr` 时，实例字典、类属性、描述符和多继承按什么顺序决定结果。主线二不依赖本章，读者遇到这些问题时再来查。

本章用一个独立的小例子，与主线二的 Node 导出无关：一个报表 worker 读取一份合成的 CSV 事件文件，把状态为 `ready` 且数量为正的事件加入月度报表 `Report("November", rows)`。文件里第一条事件有一个带引号的字段跨了两行，最后一条事件的状态无效。第二节给标题加上验证：输入 `"  November  "` 时读出规范化后的 `November`，全是空白的标题要拒绝。示例在 CPython 3.11.13 上运行。

### 名字、对象与资源

#### 名字绑定到什么，修改会被谁看到？

Python 的数据都由对象表示，每个对象有 identity (身份)、type (类型) 和值：

- 身份在对象存续期间不变。`is` 判断两边是不是同一个对象；`id(obj)` 返回代表身份的整数，但对象销毁后，另一个对象可能复用同一个 `id()`，所以它不能当作跨运行或长期保存的业务标识。
- 类型决定对象支持哪些操作、值可以取哪些范围。
- `==` 比较值是否相等，规则可以由类型自己定义。

变量名只是 namespace (命名空间) 里的一个绑定。赋值让名字指向某个对象，不复制对象；多个名字指向同一个对象叫 aliasing (别名)。由此可以推出整套引用模型：

- 对可变对象（list、dict 等）原地修改，所有指向它的名字都能看到变化；给名字重新赋值，只改变这一个名字的绑定，别的名字不受影响。
- shallow copy (浅拷贝) 只新建最外层容器，里面的成员仍是原来那些对象的引用。要独立修改嵌套数据，就重建对应的内层对象；只有确实需要隔离整棵对象图时才用 `deepcopy`。
- 函数调用为形参建立新的局部名字，指向传入的对象。函数原地修改形参所指的列表，调用方能看到；函数把形参改绑到另一个列表，调用方的名字不变。
- 默认参数的表达式在执行 `def` 时只求值一次，后续调用共用同一个对象，所以可变默认值会在调用之间累积。
- “不可变”只管对象本身这一层：字符串不能原地改写；元组不能替换自己的成员，但成员若是列表，那个列表照样能改。对象不可变也不妨碍指向它的名字重新绑定。

普通类调用通常先由 `__new__` 取得实例，再由 `__init__` 初始化这个实例；`__init__` 不负责创建实例。下面的 `Report` 把传入的列表存为实例属性，再看别名、浅拷贝和改绑各影响到哪里：

~~~python
class Report:
    def __init__(self, title, rows):
        self.title = title
        self.rows = rows

source_rows = []
report = Report("November", source_rows)
rows_alias = report.rows
print(report.rows is source_rows, rows_alias is source_rows)   # True True

report.rows.append({"id": "evt-1", "tags": ["new", "priority"]})
rows_alias[0]["tags"].append("reviewed")
copied_rows = report.rows.copy()
copied_rows[0]["tags"].append("shared")
print(report.rows[0]["tags"])   # ['new', 'priority', 'reviewed', 'shared']

rows_alias = []
print(len(report.rows))         # 1
~~~

`self.rows = rows` 只保存了对列表的引用，所以 `source_rows`、`report.rows`、`rows_alias` 是同一个列表。`copy()` 新建了一个行列表，但 `copied_rows[0]` 和 `report.rows[0]` 仍是同一个事件字典，字典里的 `tags` 也是同一个列表，所以通过副本修改嵌套标签，原报表也能看到。最后把 `rows_alias` 改绑到新列表，`report.rows` 不受影响。这些普通属性保存在实例的 `__dict__` 里。

![Report 实例、共享的行列表、copy() 新建的外层列表、事件字典与标签列表的对象引用关系](../../engineering-foundations/runtime/resources/python-object-aliases.svg)

可变默认参数的累积：

~~~python
def unsafe_add(item, items=[]):
    items.append(item)
    return items

print(unsafe_add("first"), unsafe_add("second"))   # ['first', 'second'] ['first', 'second']

def add(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

print(add("first"), add("second"))                 # ['first'] ['second']
~~~

两次 `unsafe_add` 返回的是同一个默认列表，打印时它已含两项。`add` 在没有传入列表时每次新建一个。如果 `None` 本身是有意义的输入，就另用一个独立的 sentinel (哨兵值) 表示“未提供”。

顺带区分两种容器：`set` 保存不重复的元素，没有下标；`dict` 把键映射到值，从 Python 3.7 起保持插入顺序是语言规范的保证（在 CPython 3.6 中只是实现细节）。

> [!info] 类型也不是绝对不可改
> 在 CPython 3.11.13 中，`class A: pass` 和 `class B: pass` 的实例内存布局兼容。对 `obj = A()` 先记下 `saved_id = id(obj)`，再执行 `obj.__class__ = B`，会得到 `type(obj) is B` 且 `id(obj) == saved_id`。这种受限的赋值只改了对象的类型，并没有换成另一个对象；两个类的布局（包括 `__slots__`）不兼容时会被拒绝。

#### 生成器怎样按需交出记录？

iterable (可迭代对象) 能提供 iterator (迭代器)；迭代器每次返回一个值，没有下一个值时抛出 `StopIteration`，`for` 循环自动处理这个结束信号。含有 `yield` 的函数是生成器函数：调用它只返回一个生成器对象，函数体要等 `for` 或 `next()` 要下一个值时才执行，执行到下一个 `yield` 就暂停。`list(generator)` 则一口气取完所有产出，也就失去了逐条处理的内存优势。

这和 Node 流里的“按需源”是同一个思路：消费方要一个，生产方才做一个，背压因此能传回源头（见[流一章的按需源](#%E6%BA%90%E5%A4%B4%E6%80%8E%E6%A0%B7%E6%8C%89%E9%9C%80%E7%94%9F%E4%BA%A7%EF%BC%9F)）。

下面的生成器 `ready_rows` 借用调用方已经打开的文件，检查表头、列数、状态和数量，只交出 `status == "ready"` 且 `count > 0` 的事件；状态为 `queued` 的事件合法，但被过滤掉。

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
    if headers != ["id", "status", "count", "tags", "note"]:
        raise ValueError("unexpected CSV header")
    for values in reader:
        line = reader.line_num
        if len(values) != len(headers):
            raise ValueError(f"CSV physical line {line}: wrong column count")
        fields = dict(zip(headers, values))
        status = fields["status"]
        if status not in {"ready", "queued"}:
            raise ValueError(f"CSV physical line {line}: unknown status {status!r}")
        try:
            count = int(fields["count"])
        except ValueError as error:
            raise ValueError(f"CSV physical line {line}: count must be an integer") from error
        if status == "ready" and count > 0:
            yield {**fields, "count": count, "tags": fields["tags"].split("|")}

CSV_TEXT = (
    "id,status,count,tags,note\n"
    'evt-1,ready,3,new|priority,"account\n'
    'export"\n'
    "evt-2,queued,1,backlog,skip\n"
    "evt-3,ready,2,review,year-end\n"
    "evt-4,unknown,1,bad,invalid\n"
)

rows = []
source = path = None
try:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "events.csv"
        path.write_text(CSV_TEXT, encoding="utf-8")
        with path.open(encoding="utf-8", newline="") as source:
            for row in ready_rows(source):
                rows.append(row)
except ValueError as error:
    print(f"Rejected input: {error}")

print(source.closed, path.exists())
print([row["id"] for row in rows])
print(repr(rows[0]["note"]))
~~~

输出：

~~~text
Rejected input: CSV physical line 6: unknown status 'unknown'
True False
['evt-1', 'evt-3']
'account\nexport'
~~~

外层 `for` 每要一个值，生成器就从上次 `yield` 处恢复，再向 `csv.reader` 取一条记录：

1. 第一次请求：读表头，再取到占物理行 2–3 的 `evt-1`（`note` 字段含换行）。它满足条件，生成器 `yield`，循环把它追加到 `rows`。
2. 第二次请求：取到合法但状态为 `queued` 的 `evt-2`，不满足条件，生成器继续取下一条，`yield` 满足条件的 `evt-3`。
3. 第三次请求：读到物理行 6 的 `evt-4`，状态不合法，抛出 `ValueError`，不再产出。

![for 循环每次请求驱动 CSV 生成器前进一段，以及异常后资源与对象状态的去向](../../engineering-foundations/runtime/resources/python-report-pipeline.svg)

> [!info] CSV 解析的两个落地细节
> `csv.reader` 的 `line_num` 是已经读过的源文件**物理行数**；只要有一条记录的引号字段跨了多行，它就大于记录序号，所以错误信息写的是“physical line 6”。打开文件时传 `newline=""`，是为了让 `csv` 模块按自己的规则处理字段内的换行。

#### with 清理了资源，没有撤销什么？

上例打印的 `True False` 分别是 `source.closed` 和 `path.exists()`。异常离开 `for` 后，两个 context manager (上下文管理器) 由内向外退出：内层关闭文件，外层的 `TemporaryDirectory` 删除临时目录，然后异常才被 `except` 捕获。`source` 这个名字仍指向那个已关闭的文件对象，`path` 也仍是一个 `Path` 值，只是它指向的位置已经不存在。

但 `rows` 里已经追加的 `evt-1`、`evt-3` 没有被撤销。`with` 只负责调用上下文管理器的退出方法，退出时是否回滚由管理器自己决定；文件和临时目录的清理都不会回滚列表修改。结果必须“全部成功或全部不生效”时，应先验证并暂存，再在合适的事务边界一次提交。

还要注意，自定义上下文管理器的 `__exit__` 可以返回真值来吞掉块内异常，也可能在清理失败时抛出新异常；错误能否到达外层 `except`，要看退出方法怎么写。本例的两个管理器都在清理成功后让原异常继续传播。资源也不应等垃圾回收再关闭，`with` 把关闭放在确定的控制流边界上。

> [!info] 类型提示与虚拟环境各保证什么
> type hint (类型提示) 帮助读者、IDE 和静态类型检查器理解预期的数据形状；Python 运行时默认不会因为实际对象不符合注解就拒绝它。上例真正拦下坏数据的是表头检查、状态判断和 `int()` 转换。
>
> virtual environment (虚拟环境) 基于创建它时所用的 Python 解释器，只隔离项目安装的第三方包，不会另装一个不同版本的 Python。所以要在创建时选定解释器，之后用环境里的解释器运行程序和安装依赖（POSIX 路径）：
>
> ~~~sh
> python3.11 -m venv .venv
> .venv/bin/python -m pip install httpx
> .venv/bin/python app.py
> ~~~

### 属性查找与 MRO

本节只讨论普通类实例的显式读写：`report.title`、`report.title = value` 和 `getattr(report, name)`。类对象本身的元类查找、特殊语法隐式触发的特殊方法查找，不在这条路径上。代码沿用同一个 `Report` 例子，但重新定义了类，不依赖上一节的运行状态；完整可运行脚本在本节末尾。

method resolution order (方法解析顺序，MRO) 是 Python 从对象的类出发、沿基类查找属性时依次检查的类列表，可以用 `类名.__mro__` 查看。

#### 描述符怎样接管 title 的读写？

descriptor (描述符) 是类型定义了 `__get__`、`__set__` 或 `__delete__` 的对象。只有放在类字典里（或被实例类型的某个基类继承）时，点号访问才会自动调用它；把描述符对象放进实例字典，读出来的只是那个普通对象。

`NonEmptyText` 对外提供 `title`，实际值存在实例字典的 `_title` 键里：

~~~python
class NonEmptyText:
    def __set_name__(self, owner, name):        # 类创建时得知自己的属性名
        self.public_name = name
        self.storage_name = "_" + name

    def __get__(self, instance, owner=None):
        if instance is None:                     # 经类访问时返回描述符本身
            return self
        try:
            return instance.__dict__[self.storage_name]
        except KeyError:
            raise AttributeError(self.public_name) from None

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise TypeError("title must be text")
        instance.__dict__[self.storage_name] = instance.validate_title(value)
~~~

它同时定义了 `__get__` 和 `__set__`，是 data descriptor (数据描述符)。`Report` 把它放在类上，并提供 `validate_title`。这个方法经过三个 mixin 协作完成审计、去空格和非空检查（协作顺序见本节最后两小节）：

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

report = Report("  November  ", [{"id": "evt-1"}, {"id": "evt-3"}])
~~~

`__init__` 里的 `self.title = title` 没有把字符串直接放进 `report.__dict__`，而是触发类上的数据描述符：去掉空格、检查非空，最后写入 `_title`。于是 `report.title` 和 `report.__dict__["_title"]` 都是 `November`。`Report.title is vars(Report)["title"]` 为 `True`：前者经类访问调用 `__get__(None, Report)`，本例返回描述符本身；后者直接从类字典取出它。

点号访问和直接改字典是两种操作。绕过描述符直接写一个同名键，再用正常赋值写入空白标题：

~~~python
report.__dict__["title"] = "forged"
print(report.title, report.__dict__["title"])   # November forged
report.title = "   "                           # ValueError: title must contain non-whitespace text
print(report.title)                             # November
~~~

直接写 `__dict__` 绕开了 `__set__`，但读取时数据描述符先于实例字典生效，伪造的值读不出来；正常赋值走 `__set__`，空白标题被拒绝，原值不变。描述符只约束普通的属性访问流程，不是防止任意代码篡改内部状态的安全机制。

#### 实例属性按什么优先级读取？

默认读取 `obj.x` 时，Python 先沿 `type(obj).__mro__` 找到第一个定义了 `x` 的类属性（下表称“类候选”），再根据这个候选有哪些描述符方法、实例字典里有没有同名键，决定返回什么：

| 类 MRO 找到的候选 | 实例字典有同名键 | `obj.x` 的结果 |
| --- | --- | --- |
| 有 `__get__`，且有 `__set__` 或 `__delete__`（可读的数据描述符） | 有或没有 | 调用描述符的 `__get__` |
| 有 `__get__`，没有 `__set__` / `__delete__`（非数据描述符） | 有 | 返回实例字典的值 |
| 同上的非数据描述符 | 没有 | 调用描述符的 `__get__` |
| 没有 `__get__` 的类候选，包括只定义 `__set__` / `__delete__` 的描述符 | 有 | 返回实例字典的值 |
| 没有 `__get__` 的类候选 | 没有 | 返回类候选本身 |
| 没有类候选 | 有 | 返回实例字典的值 |
| 没有类候选 | 没有 | 默认查找抛 `AttributeError`，之后才尝试 `__getattr__` |

表假定实例有 `__dict__`；实例没有字典（例如用了 `__slots__`）时，跳过实例字典这一步。

![读取普通实例属性时从类 MRO、描述符和实例字典得到结果的分支](../../engineering-foundations/runtime/resources/python-attribute-lookup.svg)

#### 赋值为什么另有一套分派？

赋值不套用读取表。类候选定义了 `__set__` 时，`obj.x = value` 调用它，setter 拒绝时异常向外传播。只定义了 `__delete__` 的数据描述符同样会拦截默认赋值，但因为没有 `__set__`，赋值抛出 `AttributeError`，实例字典里已有的同名键也不会被替换。只有类上没有拦截赋值的数据描述符、并且实例有 `__dict__` 时，默认赋值才写入实例字典；实例没有字典时，可能根本无法新增属性。

~~~python
class DeleteOnly:
    def __delete__(self, instance):
        pass

class Holder:
    value = DeleteOnly()

holder = Holder()
holder.__dict__["value"] = "kept"
holder.value = "new"          # AttributeError: __set__
print(holder.value)           # kept
~~~

赋值被拦截并报错，旧值不变；而读取时 `DeleteOnly` 没有 `__get__`，按读取表第四行返回实例字典里的 `kept`。

#### 方法为什么会自动绑定 self？

类里定义的普通函数是非数据描述符。读取 `report.publish` 时调用函数的 `__get__`，得到一个 bound method (绑定方法)：它的 `__self__` 是 `report`，`__func__` 是类字典里的那个函数。只有放在类上、经实例读取的函数才会绑定；把函数直接存进实例字典，读出来的仍是原函数，不会自动补上 `self`。

因为函数是非数据描述符，实例字典里的同名键可以遮住它，这正是对单个实例做 monkey patch (运行时替换) 只影响那一个实例的原因。普通类属性也一样，在实例没有同名键时充当默认值：

~~~python
report.category = "draft"
print(report.category, Report.category)    # draft monthly

bound = report.publish
print(bound.__self__ is report, bound.__func__ is vars(Report)["publish"])   # True True
print(bound())                              # Published November (2 events)
report.__dict__["publish"] = "temporary label"
print(report.publish)                       # temporary label
del report.__dict__["publish"]
print(report.publish())                     # Published November (2 events)
~~~

#### __getattribute__ 与 __getattr__ 怎样分工？

每次显式读取属性，入口都是 `__getattribute__`；默认实现 `object.__getattribute__` 包含上面那张优先级表。普通点号访问和两参数的 `getattr(obj, "x")` 外面还有一层：`__getattribute__` 抛出 `AttributeError` 时，调用类上定义的 `__getattr__(self, name)`。

- 这个 `AttributeError` 可以来自默认查找，也可以来自重写后的 `__getattribute__`，或来自描述符的 `__get__`。
- 类没有定义 `__getattr__`，或回退方法也抛 `AttributeError`，错误传给调用方。
- 直接调用 `object.__getattribute__` 只做默认查找，不会自行调用回退。
- 重写 `__getattribute__` 会接管整条默认路径。要保留默认行为，在实现里委托给 `object.__getattribute__(self, name)`，并避免在里面用 `self.other` 读取内部状态，否则会无限递归。

~~~python
events.clear()
print(report.row_count, getattr(report, "row_count"))   # 2 2
object.__getattribute__(report, "row_count")            # AttributeError，不调用 __getattr__
print(events)        # ['__getattr__(row_count)', '__getattr__(row_count)']
~~~

描述符 getter 出错时也一样走回退，而不会回头读实例字典。下面故意只调用 `Report.__new__` 而不运行 `__init__`，让 `_title` 缺失，同时在实例字典放一个同名的 `title` 键：

~~~python
events.clear()
incomplete = Report.__new__(Report)
incomplete.__dict__["title"] = "forged"
incomplete.title     # AttributeError
print(events)        # ['__getattr__(title)']
~~~

getter 抛出 `AttributeError` 后，点号访问转入 `__getattr__("title")`；回退也抛错，最终仍是 `AttributeError`，字典里的伪造值没有被读出。这只用来显露查找分支，正常对象仍通过 `Report(...)` 初始化。

#### MRO 怎样从多继承中算出来？

`Report(AuditMixin, NormalizeMixin)` 声明审计 mixin 在前、规范化 mixin 在后，两者都继承 `FieldBase`，构成菱形继承。Python 用 C3 linearization (C3 线性化) 计算 MRO：保留每个基类自身 MRO 里的顺序，也保留子类声明直接基类的顺序，并让共同基类只出现一次。

记 `L(C)` 为类 `C` 的 MRO：

~~~text
L(AuditMixin)     = [AuditMixin, FieldBase, object]
L(NormalizeMixin) = [NormalizeMixin, FieldBase, object]
L(Report) = [Report] + merge(
    [AuditMixin, FieldBase, object],
    [NormalizeMixin, FieldBase, object],
    [AuditMixin, NormalizeMixin],
)
~~~

merge 每一轮依次查看各列表的首项，选出第一个“不出现在任何列表尾部（首项之后的部分）”的类，把它追加到结果里，并从所有以它开头的列表中移除：

1. 选 `AuditMixin`。剩余 `[FieldBase, object]`、`[NormalizeMixin, FieldBase, object]`、`[NormalizeMixin]`。
2. `FieldBase` 是第一张表的首项，但出现在第二张表的尾部，暂时不能选；选 `NormalizeMixin`。剩余 `[FieldBase, object]`、`[FieldBase, object]` 和空表。
3. 依次选出 `FieldBase`、`object`。

所以 `Report.__mro__` 是 `[Report, AuditMixin, NormalizeMixin, FieldBase, object]`。若某轮还有剩余项却选不出合法候选，继承约束相互冲突，类定义失败并抛出 `TypeError`。例如 `class Bad(FieldBase, AuditMixin)` 要求 `FieldBase` 排在 `AuditMixin` 之前，而 `AuditMixin` 自己的 MRO 要求相反，CPython 报 `Cannot create a consistent method resolution order (MRO) for bases FieldBase, AuditMixin`。

#### super() 为什么会到达另一个 mixin？

不带参数的 `super()` 从“实例实际类型的 MRO”里找到“当前方法所在的类”，再从它**后面一个类**开始查找；它不会固定跳到当前类定义时写的直接父类。

所以标题校验的轨迹是 `Report.validate_title → AuditMixin.before → NormalizeMixin.before → FieldBase → NormalizeMixin.after → AuditMixin.after`。`AuditMixin` 里的 `super()` 到达的是 `NormalizeMixin`，而不是它定义时写的父类 `FieldBase`，因为在 `Report` 实例的 MRO 里，`AuditMixin` 后面就是 `NormalizeMixin`。`FieldBase` 是终点，不再向下委托。

![Report 的菱形继承结构、C3 线性化结果和 super 调用顺序](../../engineering-foundations/runtime/resources/python-super-mro.svg)

改变直接基类的顺序，就改变了 MRO，也改变了同一套 `super()` 的执行顺序：

~~~python
class NormalizeFirst(NormalizeMixin, AuditMixin):
    pass

print([cls.__name__ for cls in NormalizeFirst.__mro__])
# ['NormalizeFirst', 'NormalizeMixin', 'AuditMixin', 'FieldBase', 'object']
events.clear()
print(NormalizeFirst().validate_title("  November  "), events)
# November ['NormalizeMixin.before', 'AuditMixin.before', 'FieldBase', 'AuditMixin.after', 'NormalizeMixin.after']
~~~

`NormalizeFirst` 只继承两个 mixin，没有 `Report.validate_title` 这一层，所以轨迹里也没有它。两个 mixin 的相对顺序随基类声明顺序改变，`super()` 的规则本身不变。

这种协作要求每层 mixin 遵守共同约定：参数形式相互兼容，并在需要链条继续时调用 `super()`；任何一层漏掉这次调用，后面的步骤都会被跳过。如果调用顺序很难讲清楚，改用显式组合对象，或直接按名字调用各个步骤，代码会更易读。

> [!example]- 本节完整可运行脚本
> ~~~python
> events = []
>
> class NonEmptyText:
>     def __set_name__(self, owner, name):
>         self.public_name = name
>         self.storage_name = "_" + name
>
>     def __get__(self, instance, owner=None):
>         if instance is None:
>             return self
>         try:
>             return instance.__dict__[self.storage_name]
>         except KeyError:
>             raise AttributeError(self.public_name) from None
>
>     def __set__(self, instance, value):
>         if not isinstance(value, str):
>             raise TypeError("title must be text")
>         instance.__dict__[self.storage_name] = instance.validate_title(value)
>
> class FieldBase:
>     def validate_title(self, value):
>         events.append("FieldBase")
>         if not value:
>             raise ValueError("title must contain non-whitespace text")
>         return value
>
> class NormalizeMixin(FieldBase):
>     def validate_title(self, value):
>         events.append("NormalizeMixin.before")
>         result = super().validate_title(value.strip())
>         events.append("NormalizeMixin.after")
>         return result
>
> class AuditMixin(FieldBase):
>     def validate_title(self, value):
>         events.append("AuditMixin.before")
>         result = super().validate_title(value)
>         events.append("AuditMixin.after")
>         return result
>
> class Report(AuditMixin, NormalizeMixin):
>     title = NonEmptyText()
>     category = "monthly"
>
>     def __init__(self, title, rows):
>         self.title = title
>         self.rows = rows
>
>     def validate_title(self, value):
>         events.append("Report.validate_title")
>         return super().validate_title(value)
>
>     def __getattr__(self, name):
>         events.append(f"__getattr__({name})")
>         if name == "row_count":
>             return len(self.rows)
>         raise AttributeError(name)
>
>     def publish(self):
>         return f"Published {self.title} ({len(self.rows)} events)"
>
> report = Report("  November  ", [{"id": "evt-1"}, {"id": "evt-3"}])
> print(Report.title is vars(Report)["title"], vars(Report)["title"].storage_name)
> print(report.title, report.__dict__["_title"])
> print(events)
>
> report.__dict__["title"] = "forged"
> print(report.title, report.__dict__["title"])
> try:
>     report.title = "   "
> except ValueError as error:
>     print(type(error).__name__, error, "|", report.title)
>
> report.category = "draft"
> print(report.category, Report.category)
> bound = report.publish
> print(bound.__self__ is report, bound.__func__ is vars(Report)["publish"], bound())
> report.__dict__["publish"] = "temporary label"
> print(report.publish)
> del report.__dict__["publish"]
> print(report.publish())
>
> events.clear()
> print(report.row_count, getattr(report, "row_count"))
> try:
>     object.__getattribute__(report, "row_count")
> except AttributeError:
>     print("direct object.__getattribute__: AttributeError")
> print(events)
>
> events.clear()
> incomplete = Report.__new__(Report)
> incomplete.__dict__["title"] = "forged"
> try:
>     incomplete.title
> except AttributeError as error:
>     print(type(error).__name__, events)
>
> class DeleteOnly:
>     def __delete__(self, instance):
>         pass
>
> class Holder:
>     value = DeleteOnly()
>
> holder = Holder()
> holder.__dict__["value"] = "kept"
> try:
>     holder.value = "new"
> except AttributeError as error:
>     print(type(error).__name__, error, holder.__dict__["value"])
> print(holder.value)
>
> print([cls.__name__ for cls in Report.__mro__])
>
> class NormalizeFirst(NormalizeMixin, AuditMixin):
>     pass
>
> print([cls.__name__ for cls in NormalizeFirst.__mro__])
> events.clear()
> print(NormalizeFirst().validate_title("  November  "), events)
>
> try:
>     class Bad(FieldBase, AuditMixin):
>         pass
> except TypeError as error:
>     print(error)
> ~~~

### 回到主线

本支线的产出是两张可查的规则：名字只是绑定，原地修改对所有别名可见，浅拷贝只复制一层，`with` 清理资源但不回滚对象状态；属性读取按[优先级表](#%E5%AE%9E%E4%BE%8B%E5%B1%9E%E6%80%A7%E6%8C%89%E4%BB%80%E4%B9%88%E4%BC%98%E5%85%88%E7%BA%A7%E8%AF%BB%E5%8F%96%EF%BC%9F)决定，赋值另有分派，`super()` 沿实例类型的 MRO 前进。主线二接下来回到 Node 的导出流水线：[流怎样把“慢下来”逐段传回源头](#20.%20%E6%B5%81%E6%80%8E%E6%A0%B7%E6%8A%8A%E2%80%9C%E6%85%A2%E4%B8%8B%E6%9D%A5%E2%80%9D%E9%80%90%E6%AE%B5%E4%BC%A0%E5%9B%9E%E6%BA%90%E5%A4%B4%EF%BC%8C%E4%B8%AD%E9%80%94%E5%A4%B1%E8%B4%A5%E5%8F%88%E7%95%99%E4%B8%8B%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - 对象的身份、类型与值，可变性，不可变容器中的可变成员，不要依赖对象立即终结：[Python 3.15.2 Language Reference, Data model §3.1](https://docs.python.org/3.15/reference/datamodel.html#objects-values-and-types)，2026-11-12 核对。
> - `id()` 在对象生命周期内唯一且恒定，生命周期不重叠的对象可能复用：[Built-in Functions, `id`](https://docs.python.org/3.15/library/functions.html#id)；受限 `__class__` 赋值须布局兼容：[Data model, `__slots__`](https://docs.python.org/3.15/reference/datamodel.html#object.__slots__)，并于 CPython 3.11.13 验证（实现：[Objects/typeobject.c `compatible_for_assignment` / `object_set_class`](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L4715-L4869)）。
> - 类调用经 `__new__` 取得实例、`__init__` 初始化；名字与别名：[Data model, Basic customization](https://docs.python.org/3.15/reference/datamodel.html#classes)、[Tutorial §9.1](https://docs.python.org/3.15/tutorial/classes.html#a-word-about-names-and-objects)，2026-11-12 核对。
> - 默认参数在定义时求值：[Tutorial, Default Argument Values](https://docs.python.org/3.15/tutorial/controlflow.html#default-argument-values)；字典插入顺序自 3.7 起是语言保证：[Built-in Types, dict](https://docs.python.org/3.15/library/stdtypes.html#dict)，2026-11-12 核对。
> - 生成器函数与 `yield`：[Language Reference, Yield expressions](https://docs.python.org/3.15/reference/expressions.html#yield-expressions)；`reader.line_num` 的物理行计数与 `newline=""`：[`csv` library](https://docs.python.org/3.15/library/csv.html#csv.csvreader.line_num)，2026-11-12 核对；CSV 示例于 CPython 3.11.13 重放。
> - `with` 的进入、退出与异常传播：[Language Reference, The with statement](https://docs.python.org/3.15/reference/compound_stmts.html#the-with-statement)；文件在块退出时关闭：[`io.IOBase`](https://docs.python.org/3.15/library/io.html#io.IOBase)；临时目录退出时清理：[`tempfile.TemporaryDirectory`](https://docs.python.org/3.15/library/tempfile.html#tempfile.TemporaryDirectory)，2026-11-12 核对。
> - 运行时默认不强制注解：[`typing`](https://docs.python.org/3.15/library/typing.html)；虚拟环境隔离包并由创建命令选定解释器：[`venv`](https://docs.python.org/3.15/library/venv.html)，2026-11-12 核对。
> - 描述符的定义、须作为类属性才自动触发、`__set_name__`、实例读取优先级、函数绑定：[Python 3.15.2 Descriptor Guide](https://docs.python.org/3.15/howto/descriptor.html)，Descriptor Protocol、Invocation from an Instance、Automatic Name Notification、Functions and Methods，2026-11-12 核对。
> - `__getattribute__` 抛 `AttributeError` 时才回退到 `__getattr__`，描述符 getter 的错误也可进入回退：[Data model, Customizing Attribute Access](https://docs.python.org/3.15/reference/datamodel.html#customizing-attribute-access)；类候选与默认实例属性查找：[Data model, Custom classes](https://docs.python.org/3.15/reference/datamodel.html#custom-classes)，2026-11-12 核对。
> - CPython 3.11.13 的读取与赋值顺序（含只实现 `__delete__` 时赋值报 `__set__` 缺失）：[Objects/object.c `_PyObject_GenericGetAttrWithDict` / `_PyObject_GenericSetAttrWithDict`](https://github.com/python/cpython/blob/v3.11.13/Objects/object.c#L1242-L1438)、[Objects/typeobject.c `slot_tp_descr_set`](https://github.com/python/cpython/blob/v3.11.13/Objects/typeobject.c#L7822-L7839)。
> - C3 线性化：[Python 3.15.2 MRO HOWTO](https://docs.python.org/3.15/howto/mro.html#the-c3-method-resolution-order)；零参数 `super()` 沿实例类型 MRO 从当前类之后查找：[Built-in Functions, `super`](https://docs.python.org/3.15/library/functions.html#super)，2026-11-12 核对。
> - 第二节完整脚本（含 `Bad` 冲突例与 `holder.value` 读取）于 CPython 3.11.13 运行，输出与正文一致。
## 20. 流怎样把“慢下来”逐段传回源头，中途失败又留下什么？

本章回答：Node.js 的流怎样让写得慢的一端把“慢下来”逐段传回数据源，使内存保持有界；流结束时各个完成信号分别证明了什么；取消或出错时，已经写出的部分数据和临时文件该怎样处理，谁来裁决这次导出算不算成功。读者手上有前几章的结论：文件写入和内置 gzip 在 libuv threadpool 里执行，取消只是请求。

沿用主线二的案例，这次看默认方案。`job-demo-731` 的 attempt 1 用一条 Node 原生管线导出报表 42：

~~~text
异步生成器（包装数据库游标，每页最多 100 行，最多 12 页）
  → Readable.from()  → createGzip()  → createWriteStream(临时文件)
  → 关闭后 rename 到 job 与 attempt 专属的路径
~~~

### write() 返回 false 意味着什么？

先认识四种流：Readable (可读流) 产生数据块，Writable (可写流) 接收数据块，Duplex (双工流) 的可读和可写两侧各自独立，Transform (转换流) 是一种 Duplex，从一侧接收输入、从另一侧输出转换后的块。gzip 就是一个 Transform。

backpressure (背压) 的契约落在 `Writable.write(chunk)` 的返回值上。对处于正常可写状态的 Writable：

- `write(chunk)` 总会先接收当前块。
- 返回 `true`：可以继续提交。它不表示这个块已经写完。
- 返回 `false`：当前块已被接收，但内部写缓冲已达到 `highWaterMark` (缓冲阈值)。这时应停止提交后续的块，等 `drain` 事件再继续。
- `drain` 只表示底层已经消化到可以恢复写入，不证明文件已持久化，也不证明远端应用收到了数据。

如果流已经结束、被销毁或出错，`false` 不再保证当前块被接收，之后也不保证会有 `drain`；这时要处理 `error`、`close` 或管线的失败结果，而不是一直等 `drain`。

下面的演示把阈值调到 64 字节，接收方每块处理 10 ms，手写循环遵守 `false` / `drain` 契约：

~~~javascript
// 保存为 write-drain.cjs；node write-drain.cjs
const { Writable } = require('node:stream');

const sink = new Writable({
  highWaterMark: 64,
  write(chunk, encoding, callback) { setTimeout(callback, 10); },
});
const rows = Array.from({ length: 6 }, (_, i) =>
  `r${String(i + 1).padStart(2, '0')},acct-17,report-42\n`);   // 每行 22 字节

let i = 0;
function writeMore() {
  while (i < rows.length) {
    const ok = sink.write(rows[i]);
    console.log(`write ${rows[i].trim()} -> ${ok}, buffered=${sink.writableLength}`);
    i++;
    if (!ok) {
      sink.once('drain', () => { console.log('drain'); writeMore(); });
      return;
    }
  }
  sink.end(() => console.log('finish'));
}
writeMore();
~~~

在 Node.js v26.13.1 上，前两行返回 `true`（缓冲 22、44 字节），第三行使缓冲达到 66 字节、返回 `false`；循环停下，等到 `drain` 后再写第四行。6 行共触发两次 `false` 和两次 `drain`，最后输出 `finish`。

### highWaterMark 管哪一段、按什么计量？

`highWaterMark` 是**每个流队列各自**的阈值：Readable 用它决定是否继续向源头拉数据，Writable 用它告诉上游是否该暂停交块。它不是整条管线的内存硬上限。

计量单位取决于队列里存的是什么：

- 存 Buffer 时按字节计。Writable 默认会把字符串转成 Buffer。
- 存 JavaScript 字符串时按 UTF-16 code unit (码元) 计，例如 Readable 调用了 `setEncoding()`，或 Writable 设置了 `decodeStrings: false`。
- object mode (对象模式) 下按对象个数计。`Readable.from()` 默认使用对象模式；本章明确设置 `objectMode: false`，让每行 CSV 文本按字节流处理。

Readable 和 Writable 各有一个队列，Transform 则分别维护写侧和读侧两份缓冲。估算一条管线的内存时，要把每段的阈值、单个特别大的块、驱动的预取，以及管线之外的队列都算进去。还要注意，背压只能让**按需生产**的源头慢下来：如果生产者另有后台预取，或者事先把全部行装进了数组，流无法自动限制那部分工作。

### 背压怎样逐段传回源头？

用 `pipe()` 或 `pipeline()` 连接的流之间，背压在相邻两段之间一段一段地传。以 `Readable → gzip Transform → 文件 Writable` 为例：

1. 文件 Writable 的 `write(chunk)` 返回 `false`，Node 暂停它的直接上游，也就是 gzip 的读侧。
2. gzip 继续产生的输出留在自己的读缓冲里；读缓冲积压到阈值后，gzip 延后处理新的输入，写侧的消化随之变慢。
3. gzip 的写侧还能吸收已经在途的数据；等它的队列也到达阈值，`Transform.write()` 才返回 `false`，于是更上游的 Readable 被暂停，不再向生成器要下一行。

`drain` 也是逐段恢复的：先让直接上游恢复，缓冲逐段消退后各段继续工作。这不是末端一次性向整条管线广播“暂停”。

![write(chunk) 返回 false 先暂停直接上游的读侧，Transform 两侧缓冲分别积压后再向更早一段施加背压](../../engineering-foundations/runtime/resources/node-stream-backpressure-and-cleanup-buffer-flow.svg)

`pipeline()` 替你遵守相邻流之间的 `false` / `drain` 契约，并统一处理错误和结束；手写 `write()` 循环则必须自己遵守。但 `pipeline()` 不会给管线之外的任务队列、数据库预取或远端副作用设上限。

### 源头怎样按需生产？

背压要发挥作用，源头必须是“要一行才产一行”。`job-demo-731` 把数据库游标包装成一个异步生成器：每次向数据库要一页，逐行格式化成 CSV 文本 `yield` 出去；`Readable.from()` 只在下游需要时才向生成器要下一行，生成器不另外保存整份 CSV。生成器在 `finally` 里关闭游标。分页规则是：一页不足 100 行就说明数据读完；第 12 页仍然满页，就以“范围超限”失败，而不是静默截断。

下面的演示去掉数据库和 gzip，只看源头被拉取的节奏。生成器产出 200 行，接收方每行处理 1 ms，记录“已产出 − 已接收”的最大差值：

~~~javascript
// 保存为 pull-on-demand.cjs；node pull-on-demand.cjs [default]
const { Readable, Writable } = require('node:stream');
const { pipeline } = require('node:stream/promises');

const small = process.argv[2] !== 'default';
let produced = 0;
let consumed = 0;
let maxGap = 0;

async function* csvRows() {
  for (let n = 1; n <= 200; n++) {
    produced++;
    maxGap = Math.max(maxGap, produced - consumed);
    yield `row-${n},acct-17,42\n`;
  }
}

const sink = new Writable({
  ...(small ? { highWaterMark: 64 } : {}),
  write(chunk, encoding, callback) { consumed++; setTimeout(callback, 1); },
});

pipeline(
  Readable.from(csvRows(), { objectMode: false, ...(small ? { highWaterMark: 64 } : {}) }),
  sink,
).then(() => console.log({ produced, consumed, maxGap }));
~~~

两段阈值都设为 64 字节时（Node.js v26.13.1），生成器最多只领先接收方 7 行：它几乎是被一行一行拉着走的。去掉这两个设置（参数 `default`）后，Writable 的默认阈值是 64 KiB，200 行共约 3.7 KB 的文本一次就装得下，`maxGap` 变成 199：生成器在接收方处理第一行时就产出了全部数据。两次运行用的是同一个按需源，差别完全来自阈值，这正说明阈值是每段各自的缓冲额度。

背压还有一个容易忽略的代价。如果生成器在整个导出期间一直持有同一个数据库游标，**下游背压会让持有游标的事务和连接一起变长**：文件写得慢，游标就停在那里，连接一直借着不还。这段时间必须计入连接池和 worker 槽的预算。另一种做法（也是主线三分页一章采用的默认）是每页用一个短事务，读完一页就归还连接，代价是各页不再来自同一个数据库快照。两种做法怎样取舍、分页游标怎样设计，见[怎样无重复、无遗漏地分页读取一个还在变化的集合？](#29.%20%E6%80%8E%E6%A0%B7%E6%97%A0%E9%87%8D%E5%A4%8D%E3%80%81%E6%97%A0%E9%81%97%E6%BC%8F%E5%9C%B0%E5%88%86%E9%A1%B5%E8%AF%BB%E5%8F%96%E4%B8%80%E4%B8%AA%E8%BF%98%E5%9C%A8%E5%8F%98%E5%8C%96%E7%9A%84%E9%9B%86%E5%90%88%EF%BC%9F)。

### 各完成信号分别证明什么？

正常路径上，生成器读到不满 100 行的最后一页后返回，`finally` 关闭游标，然后不再产出。但“最后一行已送进 gzip”并不说明文件完整。下图按时间顺序列出从源结束到任务成功之间能观察到的每个信号，以及它证明和不证明什么：

![源 end、gzip 尾块、finish、可选 sync、close 各只证明一段；pipeline Promise 只证明管线正常完成；rename 后仍要协调者按 attempt 条件提交结果引用才算任务成功](../../engineering-foundations/runtime/resources/node-stream-completion-signals.svg)

本例的文件流默认自动关闭，所以图中的可选 `sync()` 要在关闭前另行安排。目标是 HTTP 响应或对象存储时，用相应协议或 SDK 的确认定义；服务器本地的响应流完成，不等于客户端收到并保存了全部字节。图下半部分的 `rename` 与条件提交，在下面“中途失败”一节展开。

### 取消一条流会停下什么？

取消走另一条路径。`pipeline(..., { signal })` 在信号触发时销毁仍参与管线的流，并以 `AbortError` 拒绝。它停下的只是流本身：

- 不再沿流发送数据，但已交给文件系统或远端的字节不会被撤回。
- 不会自动取消不属于流的数据库请求。若取消时生成器正在等 `cursor.next()` 或下一页，而驱动不支持取消，只有等这次查询返回，代码才能检查 signal 并进入 `finally`。
- `finally` 里等待 `cursor.close()` 返回，只说明调用并等待了关闭，不证明游标和连接已成功释放；连接的所有者要按驱动的结果确认状态，不能在查询还在进行时提前归还连接。

本章末尾的导出脚本用 `--abort-replay` 回放了这种情形：第一页查询开始后一直挂起，20 ms 时请求取消，100 ms 时查询才返回。日志顺序是：查询开始、请求取消、查询返回、游标关闭、管线以 `AbortError` 结束。也就是说，`finally` 和 `AbortError` 都出现在 100 ms 查询返回之后，而不是 20 ms 发出取消的时候。真实驱动有没有可用的取消 API、取消何时确认，要以驱动的契约为准。

### 中途失败留下什么：部分输出与发布裁决

**部分输出。** 文件写流遇到取消或错误时，已经写出的部分内容仍可能留在文件里。整块写入也一样：用 `AbortSignal` 取消 `fsPromises.writeFile()`，只会尽力取消内部缓冲，部分数据仍可能已写入文件。所以 attempt 1 一开始就用 `mkdtemp()` 建一个本 attempt 独占的临时目录，只往里写；管线失败且流已停止后，删除的也只是这个目录，不会碰到别的 attempt 或别的 job。

**发布要和取消串行裁决。** 临时文件写完、关闭之后，还要 `rename` 到最终路径。临时目录与最终路径必须在同一文件系统上：Linux 的 `rename` 在同一文件系统内是原子的，目标已存在时会被原子替换，所以最终路径按 job 和 attempt 区分，例如 `jobs/job-demo-731/attempt-1/report-42.csv.gz`，不会替换别人的文件。

取消可能在任何阶段到达。worker 进程里推进这次 attempt 的协调者运行在同一个事件循环上，由它串行裁决取消和发布，谁先被接受就走谁的路径（这是[共享状态一章](#%E5%85%B1%E4%BA%AB%E4%B8%8D%E5%8F%98%E9%87%8F%E8%A6%81%E9%80%89%E5%93%AA%E7%A7%8D%E6%89%80%E6%9C%89%E6%9D%83%E8%A7%84%E5%88%99%EF%BC%9F)的单写者规则）：

~~~mermaid
stateDiagram-v2
    [*] --> running
    running --> publishing: 文件已关闭，紧接着提交 rename
    running --> cancelling: 取消先被接受
    publishing --> published: rename 成功
    publishing --> publish_failed: rename 失败
    cancelling --> cancelled: 在途工作都已结束、临时目录已删除
~~~

- **取消先到**（仍在 `running`）：转到 `cancelling`，不再提交 `rename`。停止拉取新页，按游标契约请求取消并丢弃迟到的行，等查询取消或结束；用 worker 方案时，若槽还没归还，就请求 worker 停止，等到 `streamFinished` 或停止确认后归还一次。再等已提交的文件写入结束，关闭并删除临时目录，最后标为 `cancelled`。
- **发布先到**：文件关闭后，协调者把状态从 `running` 转到 `publishing`，紧接着提交 `rename`，中间不等待任何其他事件。之后到达的取消不能覆盖结果，attempt 保持 `publishing`，直到 `rename` 的 Promise 给出真实的成功或失败。

**本地发布不等于任务成功。** 本地 `rename` 和对象存储上传一样，只让产物就位；任务是否成功，由完成信号图最后一格的条件提交裁决。这次条件提交怎样写、为什么能挡住旧 attempt，见[怎样保证一个任务同一时刻只由一个 worker 推进？](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)。

**崩溃留下的残余。** 取消和普通错误路径上的本地清理，覆盖不了进程崩溃或被强杀：临时目录或已上传的私有对象可能遗留下来。它们要由独立的回收方在持久状态确认安全后删除，删除条件见[任务失败、被取消或 worker 失联后，怎样收尾而不重复也不留孤儿？](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)。如果一次远端写入结果未知，不能因为本地 Promise 被取消就假设远端没有生效，要用专属对象键、幂等标识或服务端状态查询来确认。

> [!example]- 可运行的导出脚本：分页源、gzip、临时目录与发布
> 合成游标为 `acct-17` 的报表 42 返回 250 行，分三页（100、100、50）。`exportRoot` 用一个新建的临时目录代替真实的导出根目录，临时目录和最终路径都在它下面，因此位于同一文件系统。这份几 KB 的输出在默认阈值下不会触发 `false` / `drain`，背压要看前面两段演示。
>
> ~~~javascript
> // 保存为 export-job.cjs；node export-job.cjs [--abort-replay]
> const { createWriteStream } = require('node:fs');
> const { mkdtemp, mkdir, rename, rm } = require('node:fs/promises');
> const { Readable } = require('node:stream');
> const { pipeline } = require('node:stream/promises');
> const { createGzip } = require('node:zlib');
> const { tmpdir } = require('node:os');
> const { join } = require('node:path');
>
> const PAGE_SIZE = 100;
> const MAX_PAGES = 12;
>
> function openCursor() {
>   let next = 1;
>   return {
>     async fetchPage() {
>       const rows = [];
>       while (rows.length < PAGE_SIZE && next <= 250) {
>         rows.push({ id: `r${next++}`, account: 'acct-17', value: 1 });
>       }
>       return rows;
>     },
>     async close() { console.error('cursor closed'); },
>   };
> }
>
> function openPendingCursor(controller) {
>   return {
>     fetchPage() {
>       console.error('1 fetchPage started; query pending');
>       setTimeout(() => { console.error('2 abort requested'); controller.abort(); }, 20);
>       return new Promise(resolve =>
>         setTimeout(() => { console.error('3 query returned'); resolve([]); }, 100));
>     },
>     async close() { console.error('4 cursor closed'); },
>   };
> }
>
> function csvCell(value) {
>   const text = String(value);
>   return /[",\r\n]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
> }
>
> async function* csvLines(cursor, signal) {
>   try {
>     yield 'id,account,value\n';
>     for (let page = 1; page <= MAX_PAGES; page++) {
>       const rows = await cursor.fetchPage();
>       signal.throwIfAborted();
>       for (const row of rows) yield [row.id, row.account, row.value].map(csvCell).join(',') + '\n';
>       if (rows.length < PAGE_SIZE) return;
>     }
>     throw new Error('report exceeds 12 pages');
>   } finally {
>     await cursor.close();
>   }
> }
>
> async function runAttempt({ exportRoot, signal, cursor }) {
>   const tempDir = await mkdtemp(join(exportRoot, '.tmp-job-demo-731-attempt-1-'));
>   const tempPath = join(tempDir, 'report-42.csv.gz.part');
>   try {
>     await pipeline(
>       Readable.from(csvLines(cursor, signal), { objectMode: false }),
>       createGzip(),
>       createWriteStream(tempPath),
>       { signal },
>     );
>     const finalDir = join(exportRoot, 'jobs', 'job-demo-731', 'attempt-1');
>     await mkdir(finalDir, { recursive: true });
>     const finalPath = join(finalDir, 'report-42.csv.gz');
>     await rename(tempPath, finalPath);
>     return finalPath;
>   } finally {
>     await rm(tempDir, { recursive: true, force: true });
>   }
> }
>
> async function main() {
>   const abortReplay = process.argv.includes('--abort-replay');
>   const controller = new AbortController();
>   const exportRoot = await mkdtemp(join(tmpdir(), 'exports-'));
>   const cursor = abortReplay ? openPendingCursor(controller) : openCursor();
>   try {
>     console.log(await runAttempt({ exportRoot, signal: controller.signal, cursor }));
>   } catch (error) {
>     console.error('attempt stopped:', error.name);
>     if (!(abortReplay && error.name === 'AbortError')) process.exitCode = 1;
>   }
> }
>
> main();
> ~~~
>
> 正常运行时打印最终路径；`gzip -dc < 该路径` 得到表头加 250 行数据。`--abort-replay` 时 stdout 没有产物路径，stderr 依次是 1–4 四行日志和 `attempt stopped: AbortError`，退出码为 0，临时目录已删除。脚本没有实现协调者的状态机和数据库条件提交，它只演示流、清理和本地 `rename`。

### 下一步：进程本身要停下时

本章的产出是：背压沿相邻流逐段传回按需生产的源头，阈值是每段各自的额度；`end`、`finish`、`close`、`pipeline` fulfilled 各只证明一段，持久化另需 `fsync` 或协议确认；取消只停下流本身，部分输出留在本 attempt 的临时目录里，发布与取消由同一个协调者串行裁决，任务成败由按 attempt 的条件提交决定。平台发来 `SIGTERM` 时，这条管线、API 进程里的请求流和 worker 的 attempt 要一起被有序地停下，见下一章[服务进程收到停止信号后怎样排空工作](#21.%20%E6%9C%8D%E5%8A%A1%E8%BF%9B%E7%A8%8B%E6%94%B6%E5%88%B0%E5%81%9C%E6%AD%A2%E4%BF%A1%E5%8F%B7%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%8E%92%E7%A9%BA%E5%B7%A5%E4%BD%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%80%80%E5%87%BA%EF%BC%9F)。

> [!info]- 来源
> - `write()` 返回 `false` 后停止写入直到 `drain`；`highWaterMark` 是阈值；字节、字符串、对象模式的计量单位：[Node.js v26.13.1, Stream, Buffering](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#buffering)、[`writable.write()`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#writablewritechunk-encoding-callback)、[`'drain'`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#event-drain)，2026-11-12 核对。
> - `pipeline()` 的 Promise、`AbortSignal` 销毁流、流 API 不涵盖外部数据库请求：[Node.js v26.13.1, Stream, Promises API](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#streams-promises-api)，2026-11-12 核对。
> - `Readable.from()` 与对象模式、`'end'`、Transform 输出块数与 `_flush()` 尾块、Writable `'finish'` 与 `'close'`：[Node.js v26.13.1, Stream, `Readable.from()`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#streamreadablefromiterable-options)、[`'end'`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#event-end)、[`'finish'`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#event-finish)、[`'close'`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#event-close)、[`_flush()`](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#transform_flushcallback)，2026-11-12 核对。
> - gzip 是 Transform，异步 zlib 使用内部线程池，结束压缩流才完成 gzip 成员：[Node.js v26.13.1, Zlib](https://nodejs.org/download/release/v26.13.1/docs/api/zlib.html#zlib)、[Threadpool usage](https://nodejs.org/download/release/v26.13.1/docs/api/zlib.html#threadpool-usage-and-performance-considerations)、[Flushing](https://nodejs.org/download/release/v26.13.1/docs/api/zlib.html#flushing)，2026-11-12 核对。
> - `mkdtemp()` 建唯一临时目录；文件写流默认自动关闭；`fs.rm()` 与 `filehandle.sync()`：[Node.js v26.13.1, File system, `fsPromises.mkdtemp()`](https://nodejs.org/download/release/v26.13.1/docs/api/fs.html#fspromisesmkdtempprefix-options)、[`fs.createWriteStream()`](https://nodejs.org/download/release/v26.13.1/docs/api/fs.html#fscreatewritestreampath-options)、[`fs.rm()`](https://nodejs.org/download/release/v26.13.1/docs/api/fs.html#fsrmpath-options-callback)、[`filehandle.sync()`](https://nodejs.org/download/release/v26.13.1/docs/api/fs.html#filehandlesync)，2026-11-12 核对。
> - `fsPromises.writeFile()` 的 `AbortSignal` 只尽力取消内部缓冲，部分数据可能已写入：[Node.js v26.13.0, File system, `fsPromises.writeFile()`](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#fspromiseswritefilefile-data-options)，2026-11-12 核对，并于 Node.js v26.13.0 单独复现。
> - `fsPromises.rename()` 在 Promise 成功时完成改名；Linux 要求同一文件系统，目标已存在时原子替换：[Node.js v26.13.0, `fsPromises.rename()`](https://nodejs.org/download/release/v26.13.0/docs/api/fs.html#fspromisesrenameoldpath-newpath)、[Linux man-pages, rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html)，2026-11-12 核对。
> - 本章的 `write-drain.cjs`、`pull-on-demand.cjs`、`export-job.cjs` 均于 Node.js v26.13.1 运行；取消时等待挂起查询的现象只是对本页合成游标的观察，不推广到任何数据库驱动。
## 21. 服务进程收到停止信号后，怎样排空工作并安全退出？

本章回答：部署平台给进程发来 `SIGTERM` 之后，进程应该按什么顺序拒绝新工作、等待在途工作、关闭各类资源，最后自己退出；哪些“已完成”的信号足以让它关掉某项依赖，哪些不够。读者手上有前几章的结论：取消只是请求，流的各个完成信号只证明一段，发布与取消由同一个协调者串行裁决。本章是主线二的最后一章。

### 收到 SIGTERM 时，手上有哪两类工作？

沿用主线二的案例。平台要滚动发布新版本，给报表服务的两个进程都发了 `SIGTERM`（部署系统要求进程终止时最常发的信号）：

- **API 进程**正把 `acct-17` 的三行 CSV 逐行流给一个 HTTP 响应。这是请求内的工作，所有者是这次请求：请求取消，流就随之结束，不留下需要以后查询的结果。
- **worker 进程**正在执行 `job-demo-731` 的 attempt 1。这个 job 已经被持久受理，所有者是持久的 job 记录和队列：最初发起导出的 HTTP 请求早已结束，客户端断开或这次停机都不能把它当作“已取消”。

两类工作的所有者不同，停机时的处理也不同：请求内的流可以在截止时间到时协作取消；持久作业则要么在预算内做完，要么不确认、交给恢复路径接手。下面先讲 API 进程，再讲 worker。

### 为什么先拒绝新工作，再关连接？

停止接活和关闭连接之间有时间差，顺序反了就会丢请求或接下做不完的工作。API 进程收到信号后按这个顺序做：

1. **同步关闸。** 在信号处理里同步设置 `draining = true`，再把 readiness (就绪状态) 标为 false。
2. **handler 自查。** 负载均衡器或编排器发现实例不就绪需要一段时间，这期间仍可能有新请求进来；所以 handler 在开始新报表或产生副作用之前，自己检查 `draining`。已建立的 keep-alive 连接上也可能来新请求，对它们直接回 `503` 并带 `Connection: close`。
3. **停止接受新连接。** 调用 `server.close()`。从 Node.js v19 起，它还会顺带关闭调用时处于空闲状态的连接，正在进行的响应可以继续写完。
4. **补关刚变空闲的连接。** 在途 handler 全部结束后，再调用一次 `server.closeIdleConnections()`，关掉那些在关停期间刚变空闲的 keep-alive 连接。不补这一次，HTTP 的关闭回调可能一直拖到截止时间。

### HTTP 关闭完成为什么不等于工作结束？

`server.close()` 的回调只说明它管理的普通 HTTP 连接都已收尾，不能证明已经启动的 handler、数据库游标、worker、文件写入或后台任务都已停下。反过来，到截止时间调用 `server.closeAllConnections()` 能强行关闭 HTTP(S) 连接，却不会取消 handler 正在等的查询或 CPU 工作。

所以进程要分别等两件事：HTTP 关闭完成，以及在途的应用工作全部结束。`closeAllConnections()` 要放在 `server.close()` 之后调用，以免关停期间又进来新连接。服务若还提供 WebSocket 或 HTTP/2，要由对应协议的 server 或 session 的管理方负责停止接收、关闭会话并确认结束，普通 HTTP Server 的回调管不到它们。

### 关停代码怎样组织？

下面的回放让 API 进程把 `acct-17` 的三行 CSV 流给当前客户端，用可取消的计时器代替数据库查询：默认每行间隔 100 ms，加 `--slow` 时每行 600 ms；内部截止时间 1 s。这些是为走到不同分支而选的教学参数。真实驱动若不支持取消，在途查询完成之前不能关闭它所用的连接池。

实现的要点有五个，代码在其后折叠：

- **跟踪完整的 handler Promise。** `inFlight` 登记的是每个 handler 的完整 Promise，包括流结束和 `finally` 里的清理；等待它们才知道应用工作是否结束。
- **客户端断开即取消本请求。** 响应的 `close` 事件在正文写完前触发时，中止这次请求的 `AbortController`。
- **截止时间先协作取消，再强关连接。** 到 1 s 时，先对所有在途请求发出取消，再调用 `closeAllConnections()`。
- **两项等待都结算后才清理依赖。** HTTP 关闭和在途 handler 都结算后，才关闭共享依赖；任一项失败，就保留依赖并记录失败退出码。只有本请求的 signal 已经触发时，才把 `AbortError` 或 `ERR_STREAM_PREMATURE_CLOSE` 当作预期的停止。
- **重复信号复用同一次关停。** `shutdown()` 返回同一个 `shutdownPromise`，第二个 `SIGTERM` 不会再启动一遍流程，也不会触发 Node 默认的信号退出。

![SIGTERM 后同步关闸并停止接收；并行等待 HTTP 关闭与请求工作；内部截止时间先取消再等清理；supervisor 的硬截止覆盖整个过程](../../engineering-foundations/runtime/resources/node-service-shutdown-lifecycle.svg)

> [!example]- 可运行的关停回放
> ~~~javascript
> // 保存为 shutdown-demo.cjs；node shutdown-demo.cjs [--slow]
> const http = require('node:http');
> const { Readable } = require('node:stream');
> const { pipeline } = require('node:stream/promises');
> const { setTimeout: sleep } = require('node:timers/promises');
>
> const rowDelayMs = process.argv.includes('--slow') ? 600 : 100;
> const rows = ['event-1,acct-17,12', 'event-2,acct-17,8', 'event-3,acct-17,-2'];
> const inFlight = new Set();
> const requestControllers = new Set();
> let draining = false;
> let shutdownPromise;
>
> function track(promise) {
>   inFlight.add(promise);
>   promise.then(() => inFlight.delete(promise), () => inFlight.delete(promise));
>   return promise;
> }
>
> async function waitForInFlight() {
>   while (inFlight.size > 0) await Promise.allSettled([...inFlight]);
> }
>
> async function* acct17Csv(signal) {
>   try {
>     yield 'id,accountId,amount\n';
>     for (const row of rows) {
>       await sleep(rowDelayMs, undefined, { signal });
>       signal.throwIfAborted();
>       yield row + '\n';
>     }
>   } finally {
>     console.log('report source cleanup complete');
>   }
> }
>
> async function handleRequest(request, response) {
>   if (draining) {
>     response.writeHead(503, { Connection: 'close' });
>     response.end('service draining');
>     return;
>   }
>   if (request.method !== 'GET' || request.url !== '/reports/acct-17.csv') {
>     response.writeHead(404, { Connection: 'close' });
>     response.end('not found');
>     return;
>   }
>
>   const controller = new AbortController();
>   requestControllers.add(controller);
>   const abortOnPrematureClose = () => {
>     if (!response.writableFinished) controller.abort(new Error('client disconnected'));
>   };
>   response.once('close', abortOnPrematureClose);
>
>   try {
>     response.writeHead(200, { 'Content-Type': 'text/csv; charset=utf-8' });
>     await pipeline(
>       Readable.from(acct17Csv(controller.signal), { objectMode: false }),
>       response,
>       { signal: controller.signal },
>     );
>   } catch (error) {
>     const cancelledClose = controller.signal.aborted && error.code === 'ERR_STREAM_PREMATURE_CLOSE';
>     if (error.name !== 'AbortError' && !cancelledClose) throw error;
>     console.log('report response stopped:', error.message);
>   } finally {
>     response.off('close', abortOnPrematureClose);
>     requestControllers.delete(controller);
>   }
> }
>
> const server = http.createServer((request, response) => {
>   track(handleRequest(request, response)).catch(error => {
>     console.error('request failed:', error);
>     process.exitCode = 1;
>     if (!response.destroyed) response.destroy(error);
>   });
> });
>
> function markReadiness(ready) {
>   console.log('ready:', ready);
> }
>
> async function closeOwnedResources() {
>   // 本回放没有外部资源；生产在这里逐个等待资源所有者确认释放。
>   console.log('resource cleanup complete');
> }
>
> const listening = new Promise((resolve, reject) => {
>   const onListening = () => { server.off('error', onError); resolve(); };
>   const onError = error => { server.off('listening', onListening); reject(error); };
>   server.once('listening', onListening);
>   server.once('error', onError);
> });
> listening.catch(error => {
>   console.error('server startup failed:', error);
>   process.exitCode = 1;
> });
> server.listen(0, '127.0.0.1', () => {
>   if (!draining) markReadiness(true);
>   console.log('listening:', server.address().port);
> });
>
> function shutdown(signal) {
>   if (shutdownPromise) return shutdownPromise;
>   draining = true;
>   markReadiness(false);
>   console.log('received:', signal);
>
>   const deadline = setTimeout(() => {
>     console.log('deadline: abort in-flight request streams and close HTTP connections');
>     for (const controller of requestControllers) controller.abort(new Error('shutdown deadline'));
>     server.closeAllConnections();
>   }, 1_000);
>
>   const serverClosed = listening.then(() => new Promise((resolve, reject) => {
>     server.close(error => (error ? reject(error) : resolve()));
>   }));
>
>   shutdownPromise = (async () => {
>     try {
>       const workResults = await Promise.allSettled([waitForInFlight()]);
>       server.closeIdleConnections();
>       const httpResults = await Promise.allSettled([serverClosed]);
>       const failures = [...workResults, ...httpResults].filter(r => r.status === 'rejected');
>       if (failures.length > 0) {
>         for (const failure of failures) console.error('shutdown wait failed:', failure.reason);
>         process.exitCode = 1;
>         return;                       // 无法确认 HTTP 或应用工作已结束：保留依赖
>       }
>       clearTimeout(deadline);
>       try {
>         await closeOwnedResources();
>       } catch (error) {
>         console.error('resource cleanup failed:', error);
>         process.exitCode = 1;
>       }
>     } finally {
>       clearTimeout(deadline);
>     }
>   })();
>   return shutdownPromise;
> }
>
> function onShutdown(signal) {
>   shutdown(signal).catch(error => {
>     console.error('shutdown failed:', error);
>     process.exitCode = 1;
>   });
> }
>
> process.on('SIGTERM', onShutdown);
> process.on('SIGINT', onShutdown);
> ~~~

在 Node.js v26.13.1 上，让一个客户端请求这份 CSV，在它收到第一个响应块（表头）后立即向服务进程发送 `SIGTERM`，结果如下：

- **默认模式（每行 100 ms）**：三行约 300 ms 发完，在 1 s 截止时间之前。客户端收到完整的 CSV；生成器清理、HTTP 关闭和资源清理都在截止时间前完成，退出码为 0。
- **`--slow` 模式（每行 600 ms）**：第一行在约 600 ms 发出，第二行要到约 1,200 ms，晚于截止时间。客户端只收到表头和 `event-1`；截止时间到时进程发出取消并强关连接，生成器执行 `finally`，管线以 `ERR_STREAM_PREMATURE_CLOSE` 结束，handler 随后全部结算，进程仍以 0 退出。
- **重复信号**：慢模式下间隔 150 ms 连发两次 `SIGTERM`，两次拿到的是同一个 `shutdownPromise`，流程只走一遍，退出码为 0。

去掉第 4 步那次补调的 `closeIdleConnections()` 做对照，正文仍完整送达，但 HTTP 的关闭回调一直拖到了 1 s 截止时间。

### 各类资源等到什么状态才能关闭？

“收到信号”“连接断了”和“任务结束”是三件不同的事。回放里两项等待都结算，只证明 HTTP 关闭和 handler 的 Promise 都已结算，而 `waitForInFlight()` 并不要求 handler 本身成功。生产环境还要等每项资源的所有者确认释放成功；清理失败或状态未知时，就不要关闭仍可能在用的那项依赖。各类资源要等到的状态如下：

| 资源或副作用 | 等到什么状态才能关闭或归还 | 不能据此推出什么 |
| --- | --- | --- |
| HTTP listener 与普通 HTTP(S) 连接 | `server.close()` 的回调；超时的强制路径可以不等回调，在 `server.close()` 之后调用 `closeAllConnections()` | 响应被强制关掉，不代表 handler 里的 JavaScript、查询或 worker 已结束；WebSocket、HTTP/2 由各自的 server 或 session 关闭并确认 |
| 请求内的 CSV 流 | `pipeline()` 结算：fulfilled 是正常结束，rejected 是失败或取消路径已收尾，本例生成器也已完成 `finally` | 已发出的部分字节不能撤回；也不证明客户端完整读取或保存了正文 |
| 数据库游标与连接 | 挂起的 `next()` 返回，或驱动确认已取消，然后关闭游标、释放连接 | Node 的 `AbortSignal` 不会自动变成任意驱动的取消请求 |
| worker 与批次 | 当前页的写出、尾块或停止确认已到达，压缩状态已清除，槽按协议归还一次 | 发出取消消息或关闭 HTTP socket，不等于 worker 已停 |
| 临时文件与发布 | 文件流结束并关闭；若已进入发布，以 `rename` 的真实成功或失败为准 | 写入被本地取消，不能证明文件或远端没有副作用 |
| 已持久受理的 job（如 `job-demo-731`） | 停止领取新 job；当前 attempt 在预算内完成，或清理后不确认、交给恢复路径 | API 客户端断开不撤销已持久受理的 job |

handler 的 Promise 结算，本身不是资源已释放的证明。

### 持久作业在关停中怎样处理？

worker 进程收到 `SIGTERM` 后，第一步是让队列消费者**停止领取**新 job，这对应 API 进程的“先关闸”。broker 已经预先推给 worker、还没开始处理的投递不算在途工作：显式退回 broker，或随连接关闭由 broker 重新入队。然后看手上的 attempt 1：

- **能在预算内做完，就做完。** 读完剩余页、压缩、写出、发布，由协调者按 attempt 条件提交结果，再确认这条消息。
- **做不完，就不确认。** 若策略要求到截止时间就取消，由同一个协调者依次停止拉取新页、取消查询并等它结束、等 worker 的停止或收尾确认以及已提交的写入完成，然后清理本 attempt 的临时目录。之后**不发 ACK**，进程退出。

主线四的结论是：未完成的 attempt 不发 ACK，消息会被重新投递；租约到期后，由恢复者按持久状态接管，旧 attempt 迟到的结果因 attempt 编号不匹配而写不进去。断开的连接不等于取消了 job，协调者不能把请求连接关闭误记为 job 已取消。领取、租约与栅栏见[怎样保证一个任务同一时刻只由一个 worker 推进？](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)，ACK 的时机见[发布确认、消费者确认和业务完成各证明什么？](#44.%20%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

停机时取消与发布仍可能竞争，裁决规则不变：attempt 还在 `running` 且取消先被接受，就不提交发布；已进入 `publishing` 并提交了 `rename`，就等真实结果，晚到的取消不能覆盖它（见[流一章的发布裁决](#%E4%B8%AD%E9%80%94%E5%A4%B1%E8%B4%A5%E7%95%99%E4%B8%8B%E4%BB%80%E4%B9%88%EF%BC%9A%E9%83%A8%E5%88%86%E8%BE%93%E5%87%BA%E4%B8%8E%E5%8F%91%E5%B8%83%E8%A3%81%E5%86%B3)）。若进程在提交 `rename` 后被强杀，结果未知；重启后要按 job ID、attempt 专属路径和持久状态核对，或幂等地重试，不能凭进程退出推断“肯定没发布”。客户端已经收到部分流响应，也不能回滚先前已提交的数据库或对象存储副作用。

### 内部截止时间与外部硬截止怎样分工？

进程内部的截止时间（回放里的 1 s）和外部 supervisor（部署管理器、编排器等负责强停进程的一方）的硬截止各管一段：

- 内部截止时间决定何时从“等待自然结束”转为“协作取消”。它必须早于 supervisor 的硬截止，中间留出按实测清理时长确定的余量，用来完成停止接单、协作取消、查询与 worker 清理、文件关闭和资源池关闭。
- 内部计时器依赖事件循环；同步代码长时间阻塞时，它也不能准时触发（见[事件循环一章](#%E9%95%BF%E5%90%8C%E6%AD%A5%E5%9B%9E%E8%B0%83%E5%AF%B9%E8%AE%A1%E6%97%B6%E5%99%A8%E5%81%9A%E4%BA%86%E4%BB%80%E4%B9%88%EF%BC%9F)）。
- supervisor 到硬截止后可以强杀进程（如 `SIGKILL`）。强杀不能替代持久任务的恢复，也不能替代对未知副作用的对账。

在支持这些信号的 POSIX 系统上，注册 `SIGTERM` 或 `SIGINT` 监听器会移除 Node 对相应信号的默认退出行为，应用要自己走完关停流程。几条实现规则：

- 不要在清理之前直接调用 `process.exit()`；用 `process.exitCode` 记录失败，让已关闭的 handle 自然结束进程。
- 截止时间计时器保持引用（不调用 `unref()`），避免事件循环空闲时进程在它触发之前就退出。
- 不响应取消的请求仍持有数据库连接时，等待会继续；不能为了按时退出而提前关闭仍在使用的依赖，宁可交给外部硬截止。

PM2、Kubernetes、ECS 各自发什么信号、默认等多久，以及平台怎样先摘流量再停进程，见[服务该跑在哪种运行时上，平台怎样启动、探测和停止它？](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)。

### 本主线的产出：一个能被安全停止的进程

主线二到此得到一个资源有界、能被安全停止的进程：执行位置按 I/O 和 CPU 分开，每个池、槽、队列和缓冲都有上限；共享状态各有一种所有权规则；背压把“慢下来”传回源头；取消被当作请求，每项资源等到可证明的完成状态才释放；停机时先拒绝新工作，再排空，持久作业做不完就不确认，交给恢复路径。

这些上限都按“每进程”计数，跨进程、跨副本时要相乘再核对：连接池的总连接数、worker 的总执行槽。而跨副本的共享状态和持久完成，进程内的锁和协调者都管不到，要交给数据库。主线三从这里接手：两个请求同时抢最后一件库存时，怎样把条件附着在写语句上，只预留一次，见[两个请求争夺最后一件库存时，怎样保证只预留一次？](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。

> [!info]- 来源
> - `server.close()` 停止接受新连接，并自 Node.js v19 起关闭调用时的空闲连接；`server.closeIdleConnections()`：[Node.js v26.13.1, HTTP, `server.close()`](https://nodejs.org/download/release/v26.13.1/docs/api/http.html#serverclosecallback)、[`server.closeIdleConnections()`](https://nodejs.org/download/release/v26.13.1/docs/api/http.html#servercloseidleconnections)，2026-11-12 核对。
> - `server.closeAllConnections()` 关闭现有 HTTP(S) 连接，应在 `server.close()` 之后调用；不负责 WebSocket 等其他协议，HTTP/2 由自己的 session 收尾：[Node.js v26.13.1, HTTP, `server.closeAllConnections()`](https://nodejs.org/download/release/v26.13.1/docs/api/http.html#servercloseallconnections)，2026-11-12 核对。
> - 注册 `SIGTERM` / `SIGINT` 监听器会移除默认处理：[Node.js v26.13.1, Process, Signal events](https://nodejs.org/download/release/v26.13.1/docs/api/process.html#signal-events)，2026-11-12 核对。
> - 活动的 `Timeout` 默认保持事件循环运行，`unref()` 后进程可能先退出：[Node.js v26.13.1, Timers, `timeout.unref()`](https://nodejs.org/download/release/v26.13.1/docs/api/timers.html#timeoutunref)，2026-11-12 核对。
> - 带 `AbortSignal` 的 `pipeline()` 销毁管线流并以 `AbortError` 结束，只有接收该 signal 的操作才会协作取消：[Node.js v26.13.1, Stream, Promises API](https://nodejs.org/download/release/v26.13.1/docs/api/stream.html#streams-promises-api)，2026-11-12 核对。
> - 关停回放：默认、`--slow`、重复信号与去掉补调 `closeIdleConnections()` 的对照，于 Node.js v26.13.0 与 v26.13.1 运行，结果一致。
## 22. 两个请求争夺最后一件库存时，怎样保证只预留一次？

进程内的锁只管得到一个进程；多个服务副本共同读写的数据，要交给数据库裁决，这是[主线二结尾](#21.%20%E6%9C%8D%E5%8A%A1%E8%BF%9B%E7%A8%8B%E6%94%B6%E5%88%B0%E5%81%9C%E6%AD%A2%E4%BF%A1%E5%8F%B7%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%8E%92%E7%A9%BA%E5%B7%A5%E4%BD%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%80%80%E5%87%BA%EF%BC%9F)留下的问题。两个请求同时想拿走最后一件库存，其中一个还可能是另一个的重试。本章回答两件事：怎样让数据库替我们裁决“谁拿到”，以及怎样让同一操作的重试取回原结果，而不是再扣一次。读者需要知道 `SELECT`、`UPDATE`、`INSERT` 和事务的基本写法；隔离级别的完整规则在[事务与隔离一章](#24.%20%E4%BA%8B%E5%8A%A1%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%8C%E5%B9%B6%E5%8F%91%E4%BA%8B%E5%8A%A1%E5%90%84%E8%83%BD%E7%9C%8B%E8%A7%81%E4%BB%80%E4%B9%88%EF%BC%9F)，这里只用到其中一条。

### 案例：最后一件 SKU-7

本主线用一个合成的库存案例贯穿，数据与标识都是教学选择：

| 标识 | 含义 |
|---|---|
| `acct-17`、`user-17` | 发起预留的账户与 principal (主体，即已认证的调用者) |
| `SKU-7`，`available = 1` | 要预留的商品，只剩一件；后文有一个变体把初值改成 2 |
| `reserve-demo-208` | 客户端为这次预留生成的 idempotency key (幂等键)，重试时保持不变 |
| 请求 A、B | A 是首次尝试；B 可能是同一请求的并发重放，也可能是别的操作 |

数据库要同时守住两条规则：

1. 不同的操作不能把库存扣成负数。
2. 同一账户、同一主体、同一幂等键（合起来称作用域键）最多提交一条预留记录。

本主线的 SQL 和并发时序都以 **PostgreSQL 18、Read Committed (读已提交)** 为准；换数据库时哪些结论会变，见文末的方言说明和 [InnoDB 支线](#26.%20InnoDB%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%B4%A2%E5%BC%95%E8%AE%B0%E5%BD%95%E3%80%81%E6%97%A7%E7%89%88%E6%9C%AC%E5%92%8C%E6%97%A5%E5%BF%97%E5%A4%84%E7%90%86%E5%90%8C%E4%B8%80%E7%AC%94%E5%BA%93%E5%AD%98%E4%BA%8B%E5%8A%A1%EF%BC%9F)。

### 先读后写为什么会超卖？

设想两个不同的操作各自先执行 `SELECT available`，都读到 1，再各自把库存写成 0 并插入自己的预留记录。最终库存是 0，看上去没错，却有两个调用方都收到了“预留成功”。

问题在于读取只观察了当时的值。“库存仍大于零”这个条件没有附着到之后的写入上，第二个写入者写的时候，条件早已不成立。修法是把条件放进写语句本身：`UPDATE ... WHERE available > 0`。数据库在执行这条写入时检查条件，检查与修改不可分割。

### 两张表各守住什么？

~~~sql
CREATE TABLE inventory (
    sku TEXT PRIMARY KEY,
    available INTEGER NOT NULL CHECK (available >= 0)
);

CREATE TABLE reservations (
    account_id TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    sku TEXT NOT NULL REFERENCES inventory(sku),
    status TEXT NOT NULL CHECK (status IN ('reserved', 'cancelled')),
    PRIMARY KEY (account_id, principal_id, idempotency_key)
);

INSERT INTO inventory VALUES ('SKU-7', 1);
~~~

- `inventory.sku` 是主键，每个 SKU 只有一行，所以下文的条件 `UPDATE` 最多命中一行。
- `available` 同时声明 `NOT NULL` 和 `CHECK (available >= 0)`。只写 `CHECK` 不够：表达式结果为 NULL 时 CHECK 也算通过，未知库存会被放进来。
- `reservations` 的复合主键就是作用域键，同一作用域键最多一行。
- 外键让预留只能指向存在的 SKU。

这些约束对所有写入方生效，不依赖每段应用代码都记得检查。每类约束的盲区、检查时机和它们自动建立的索引，见[约束守住哪些规则，索引又怎样服务读取？](#23.%20%E7%BA%A6%E6%9D%9F%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%A7%84%E5%88%99%EF%BC%8C%E7%B4%A2%E5%BC%95%E5%8F%88%E6%80%8E%E6%A0%B7%E6%9C%8D%E5%8A%A1%E8%AF%BB%E5%8F%96%EF%BC%9F)。

### 同一操作怎样被认出来？

幂等键让服务把“同一操作的重试”与“一次新的操作”区分开。本章给出的幂等记录契约是全领域的权威定义，主线四的导出任务和 webhook 收件箱都沿用它：

1. **作用域键是 `(账户, 主体, 幂等键)`。** 键只在这个范围内唯一。别的主体即使猜到同一个键字符串，也落在另一个作用域里，读不到这里的结果。
2. **请求指纹识别意图。** request fingerprint (请求指纹) 是规范化后业务参数（这里是 SKU 与数量等）的稳定摘要。同一个键配上不同参数，说明调用方复用了键却换了意图。
3. **只有成功提交才占用键。** 预留记录与库存扣减一起提交；库存不足时整笔回滚，不留下记录，也就不占键。
4. **同键同指纹返回该记录的当前状态。** 记录之后被取消，重放就返回 `cancelled`，不会重新扣库存，也不会把它“复活”。取消不释放这个作用域键。
5. **同键异指纹返回冲突。** 不能把旧结果解释成新意图。
6. **不逐字节重放首个响应。** 服务承诺恢复的是同一条业务记录和它的效果；状态码、时间戳或响应字节可以与第一次不同。

第 3 条是一个取舍。它让契约最小：失败不留痕，补货后同一个 POST 可以成功。代价是失败没有一条可供永久重放的“失败结果”，后文[同一个键换了 SKU，为什么没有冲突？](#%E5%90%8C%E4%B8%80%E4%B8%AA%E9%94%AE%E6%8D%A2%E4%BA%86%20SKU%EF%BC%8C%E4%B8%BA%E4%BB%80%E4%B9%88%E6%B2%A1%E6%9C%89%E5%86%B2%E7%AA%81%EF%BC%9F)会看到它留下的边界。

记录还必须在服务承诺的重放窗口内保留，窗口过后旧键怎样处理（墓碑），属于请求协议的一部分，见[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。HTTP 方法本身的幂等语义是另一回事：`POST` 不是幂等方法，给它加幂等键是应用层的去重约定，二者不能互相代替，见[一次 HTTP 请求怎样从浏览器到达服务，又带回什么？](#33.%20%E4%B8%80%E6%AC%A1%20HTTP%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%B5%8F%E8%A7%88%E5%99%A8%E5%88%B0%E8%BE%BE%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%8F%88%E5%B8%A6%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info] 应用实例
> AI 运行受理时把调用者、资源范围、键与请求摘要绑定成唯一的 `runId`，用的就是这套契约，见[请求受理后，怎样保证任务最终被执行且不被两个 worker 同时推进？](../../ai-engineering/runs/accepting-queuing-and-claiming-runs.md)。

### 一次预留怎样执行？

下图是一次预留从受理到下结论的完整流程：成功路径是条件 `UPDATE` 恰好 1 行、`INSERT` 成功、`COMMIT`；两条失败路径（`UPDATE` 零行、`INSERT` 撞上复合主键）汇到同一个回滚加回查，结论只有底部三种。本节和后两节分别展开预查与事务、并发排队、失败后的回查。

~~~mermaid
%%{init: {"flowchart": {"wrappingWidth": 360}}}%%
flowchart TD
    A["重新授权：user-17 能为 acct-17 预留<br/>规范化参数，计算请求指纹"] --> P
    P{{"预查作用域键（快路径）"}}
    P -- 同指纹 --> RS["返回记录当前状态<br/>reserved 或 cancelled"]
    P -- 异指纹 --> CF["幂等键冲突"]
    P -- "未命中：只说明快照里<br/>没有已提交记录" --> U
    U{{"BEGIN READ COMMITTED<br/>条件 UPDATE 库存，返回几行？"}}
    U -- 多于 1 行 --> BUG["schema 没维持每个 SKU 一行<br/>当缺陷处理，不能当成功"]
    U -- 恰好 1 行 --> I{{"INSERT 预留记录"}}
    I -- 成功 --> C["COMMIT<br/>扣减与记录同时可见"]
    U -- "0 行：SKU 不存在或已售罄" --> RB
    I -- 撞上复合主键 --> RB
    RB["整笔 ROLLBACK"] --> Q{{"新事务按作用域键回查"}}
    Q -- 同指纹 --> RS
    Q -- 异指纹 --> CF
    Q -- 没有已提交记录 --> F["本次库存失败（不存在或售罄）<br/>不保证之后没人提交同键记录"]
~~~

API 先按当前认证结果确认 `user-17` 有权为 `acct-17` 预留，再规范化参数、计算指纹，然后可以先查一次已有记录：

~~~sql
SELECT request_fingerprint, sku, status
FROM reservations
WHERE account_id = $1 AND principal_id = $2 AND idempotency_key = $3;
-- $1 = acct-17，$2 = user-17，$3 = reserve-demo-208
~~~

`$1`、`$2` 是 PostgreSQL 的位置参数，由驱动**按每条语句分别绑定**，编号不跨语句共享；下文每条 SQL 的注释只写它自己的绑定。

这次预查只是快路径。没命中只说明这条语句的快照里没有**已提交且可见**的记录，原事务可能还没提交，所以预查不能代替后面的裁决。

预查未命中时，服务在一个事务里条件扣减并写入记录：

~~~sql
BEGIN ISOLATION LEVEL READ COMMITTED;

UPDATE inventory
SET available = available - 1
WHERE sku = $1 AND available > 0
RETURNING available;
-- $1 = SKU-7。恰好返回一行才继续；返回零行则 ROLLBACK，不执行 INSERT。

INSERT INTO reservations
    (account_id, principal_id, idempotency_key, request_fingerprint, sku, status)
VALUES ($1, $2, $3, $4, $5, 'reserved');
-- $1 = acct-17，$2 = user-17，$3 = reserve-demo-208，$4 = fingerprint-A，$5 = SKU-7

COMMIT;
~~~

`RETURNING` 只返回实际被更新的行，值是更新后的新值。库存从 1 扣到 0 时，它返回**一行，值为 0**；“返回零行”才表示没有可扣的库存。

### 条件 UPDATE 怎样让并发请求排队？

条件 `UPDATE` 的返回行数就是业务判断，这是本领域条件写的 SQL 层权威规则：恰好 1 行说明扣减已在本事务内生效，继续写记录；0 行说明 SKU 不存在或库存已为 0，走失败路径；多于 1 行说明实际 schema 没有维持“每个 SKU 一行”，是缺陷而不是成功。

两个请求并发时，排队靠的是行锁。下图是 A 先拿到 `SKU-7` 行锁的情形：

![SKU-7 的已提交库存、A 的事务内版本、B 的行锁等待与重检](../../engineering-foundations/data/resources/database-fundamentals-inventory-row-lock.svg)

*A 未提交的 0 和预留记录对别人不可见；B 在行锁上等待，A 结束后按结果重检条件。*

1. A 的 `UPDATE` 把库存改成 0，并持有这一行的锁。这个 0 只在 A 的事务内可见，A 插入的预留记录也一样。
2. B 的 `UPDATE` 找到同一行，发现它正被 A 修改，于是等待。
3. A 提交，库存 0 与 `reserve-demo-208` 记录同时对外可见。
4. B 醒来后，PostgreSQL 在 Read Committed 下对**最新提交的行版本**重新求值 `WHERE available > 0`。条件为假，B 的 `UPDATE` 返回零行，B 不执行 `INSERT`。

如果 A 不是提交而是回滚，它的扣减和记录一起撤销。B 重检的是原值 1，条件成立，B 扣减、写记录并成为唯一的提交者。所以行锁释放本身不说明前一个请求成功了，结果取决于它最终提交还是回滚。

Read Committed 的这一行为（等锁后在新版本上重检条件）让一条条件 `UPDATE` 就能表达“库存不低于零”。在 Repeatable Read 下，同样的时序里 B 会以序列化失败中止，处理方式不同，见[一笔事务失败后，该回滚、重试还是回查？](#%E4%B8%80%E7%AC%94%E4%BA%8B%E5%8A%A1%E5%A4%B1%E8%B4%A5%E5%90%8E%EF%BC%8C%E8%AF%A5%E5%9B%9E%E6%BB%9A%E3%80%81%E9%87%8D%E8%AF%95%E8%BF%98%E6%98%AF%E5%9B%9E%E6%9F%A5%EF%BC%9F)。

### 零行或唯一冲突之后怎样下结论？

预留事务有两条失败路径：条件 `UPDATE` 返回零行；或 `INSERT` 撞上复合主键。两条路径的处理相同，这是本领域唯一裁决的权威规则：

1. **整笔回滚。** 不能留下已执行的库存扣减。PostgreSQL 中，唯一约束报错还会使当前事务进入失败状态，之后的语句都会被拒绝，只能 `ROLLBACK`（或回到报错前建立的 savepoint）。
2. **开新事务按作用域键回查。** 新事务拿到新的语句快照，能看到在此期间提交的记录。

~~~sql
ROLLBACK;

BEGIN ISOLATION LEVEL READ COMMITTED;
SELECT request_fingerprint, sku, status
FROM reservations
WHERE account_id = $1 AND principal_id = $2 AND idempotency_key = $3;
-- $1 = acct-17，$2 = user-17，$3 = reserve-demo-208
COMMIT;
~~~

API 在已重新授权的作用域内比较指纹，得到流程图底部三个结局之一。“没有已提交记录”只说明这条回查语句的快照里没有，不保证另一个事务稍后不会提交同键记录。失败不占键，所以同一个 POST 在补货后可以成功。若要区分“SKU 不存在”和“售罄”，可以再读一次库存，但那次读取只反映当时的状态。

> [!warning] `ON CONFLICT DO NOTHING` 插入零行，也要用新快照去读胜者
> 有些写法用 `INSERT ... ON CONFLICT DO NOTHING RETURNING ...` 代替捕获唯一冲突异常。PostgreSQL 文档明确指出：Read Committed 下，这条语句可能因为另一个事务的结果而放弃插入，而那个结果对本语句的快照并不可见。所以“插入了零行”不等于“本语句已经看见了胜者”，胜者要用后续语句的新快照去读。在本例里，`INSERT` 之前已经扣过库存，插入零行时仍要整笔回滚，再按上面的步骤回查。

### 库存还有余量时，谁挡住重复的同一操作？

上面的时序里，B 在库存这一关就失败了，唯一约束没有出场。为了单独观察唯一约束，把 `SKU-7` 的初始库存**只改成 2**，A、B 仍是完全相同的请求：同账户、主体、SKU、幂等键和 `fingerprint-A`。

![初始库存为 2 时，同一请求的 B 临时扣减后撞上唯一键并整笔回滚](../../engineering-foundations/data/resources/database-fundamentals-idempotency-unique-conflict.svg)

*B 在事务内把库存扣到 0，插入时撞上复合主键；整笔回滚后库存回到 1，A 的记录不变。*

1. A 把库存从 2 扣到 1，写入预留记录并提交。
2. B 等到行锁后在新值 1 上重检，条件仍成立，于是在自己的事务里把库存从 1 扣到 0。
3. B 插入同一作用域键，复合主键拒绝第二条记录。
4. B 整笔回滚：库存恢复为已提交的 1，A 的记录还在。新事务回查读到同键同指纹的 A 记录，API 返回它的当前状态。

**不能只撤销 `INSERT`。** 例如用 savepoint 只回滚插入、再照常 `COMMIT`，B 的临时扣减就会留在库里：一次重放凭空多扣了一件库存。

这个单 SKU 时序里，两个 `UPDATE` 先在库存行锁上串行化；B 走到 `INSERT` 时 A 已经提交，所以唯一冲突立刻判定。换一种写法，比如先插记录再扣库存，B 的唯一性检查可能遇到 A 尚未提交的同键行；这时 B 会等 A 结束，A 提交则报冲突，A 回滚则 B 插入成功。两种顺序下，安全性都来自原子事务、复合主键和整笔回滚，而不是“预查时没有记录”。

### 同一个键换了 SKU，为什么没有冲突？

前面的 A、B 请求同一个 SKU，所以总会先在同一行库存锁上排队。如果复用同一个键却请求不同的 SKU，就没有共同的锁。假设 A 正在事务里预留有货的 `SKU-7`，尚未提交；B 复用 `reserve-demo-208`，却改成请求无货的 `SKU-8`。SKU 是业务参数，B 的指纹与 A 不同。

| 时点 | A：`SKU-7` | B：`SKU-8`，复用同一键 | 结果 |
|---|---|---|---|
| A 尚未提交 | 事务内 1 → 0，记录未提交 | 预查看不到任何记录 | 预查无法判断 A 的状态 |
| B 扣减 | 仍持有 `SKU-7` 行锁 | `SKU-8` 库存为 0，`UPDATE` 返回零行 | B 没碰 `SKU-7`，也没执行 `INSERT` |
| B 回查 | 记录仍未提交 | 新事务仍看不到记录 | B 返回“无库存”；A 随后照常提交 |

B 没有走到 `INSERT`，从未占用这个键，所以既不会等 A，也不会被判为参数冲突。之后 B 若用同一个键再提交一次 `SKU-8` 的请求，预查就会看到 A 的 `SKU-7` 记录，因指纹不同返回冲突。反过来，如果 `SKU-8` 有货，B 会走到 `INSERT`，在唯一性检查处等待 A：A 提交则 B 撞键，A 回滚则 B 成功。

复合主键只在真正写入 `reservations` 时裁决，不会预先锁住所有使用这个键的请求。如果产品要求“同一个键第一次到达就固定结果，包括失败”，最小的成功记录模式做不到，需要另设前置占键协议：请求一到就以作用域键插入一条“处理中”记录并提交，后续请求在这条记录上裁决。这是另一套契约，不能从本章的事务推出来。

### 响应丢失时，记录怎样认出原操作？

一次 POST 超时只说明客户端没收到响应。它分不清请求没到、事务回滚、事务仍在执行，还是已经提交但响应丢在了路上。设想最后一种：数据库已同时保存 `SKU-7.available = 0` 和作用域键为 `(acct-17, user-17, reserve-demo-208)`、指纹为 `fingerprint-A` 的预留记录，客户端却处在 unknown outcome (未知结果)。

![浏览器、API 与 PostgreSQL 之间的提交、响应丢失与原 POST 重放](../../engineering-foundations/data/resources/database-fundamentals-response-loss-replay.svg)

*提交后响应丢失；客户端用同一键、同一参数重放原 POST，API 读出已有记录而不再扣减。*

客户端重放原 POST，带同一个键和原参数。API 重新授权，按作用域键读记录并核对指纹，返回这条预留的当前状态。能做到这一点有一个前提：**库存扣减和预留记录在同一个事务里提交。** 如果扣减先提交、记录随后另写，进程可能恰好在两步之间崩溃。这时重试找不到记录，库存却已被扣走：没补货时会误报“无库存”，补了货还会再扣一次。

客户端何时重放、查不到记录时为什么不能判定失败、只读查询为什么不能悄悄启动原操作、重放窗口怎样定，属于请求协议，权威在[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

这个事务只覆盖本数据库。远端支付或发消息不能放进同一笔提交；常见做法是把待发指令作为 outbox 记录与本地效果一起提交，由后台进程投递，远端仍要按自己的业务键去重。为什么事务管不到远端，见[事务能保证什么，并发事务各能看见什么？](#24.%20%E4%BA%8B%E5%8A%A1%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%8C%E5%B9%B6%E5%8F%91%E4%BA%8B%E5%8A%A1%E5%90%84%E8%83%BD%E7%9C%8B%E8%A7%81%E4%BB%80%E4%B9%88%EF%BC%9F)；outbox 的完整机制见[耗时任务怎样被持久受理，并保证一定会被唤醒？](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)。而数据库确认了 `COMMIT` 之后崩溃，这条记录靠什么留下来，见[数据库确认提交后崩溃，靠什么恢复？](#25.%20%E6%95%B0%E6%8D%AE%E5%BA%93%E7%A1%AE%E8%AE%A4%E6%8F%90%E4%BA%A4%E5%90%8E%E5%B4%A9%E6%BA%83%EF%BC%8C%E9%9D%A0%E4%BB%80%E4%B9%88%E6%81%A2%E5%A4%8D%EF%BC%9F)。

### 换到抽奖：两条唯一约束怎样分别裁决？

抽奖也是“名额有限、每人只能参与一次”。同一套做法可以照搬：条件写守住数量，成功结果与操作键同事务提交，唯一约束裁决重复写入。新问题是：一张表上有两条唯一约束，各自的冲突含义不同。

公开只读的 `GET /draws/{campaignId}` 返回活动规则、时间和状态；已认证的参与者用 `POST /draws/{campaignId}/entries` 报名。参与表这样建：

~~~sql
CREATE TABLE draw_entries (
    entry_id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('won', 'no-prize')),
    CONSTRAINT draw_entries_one_per_principal UNIQUE (campaign_id, principal_id)
);
~~~

`UNIQUE (campaign_id, principal_id)` 让同一个人换了键并发报名，也只能留下一条参与记录。作用域键是 `(campaign_id, principal_id, idempotency_key)`，由于前两列已唯一，按作用域键回查就是在这一行上核对键和指纹。

处理顺序：

1. 先验证当前主体的权限，再按作用域键查已有操作。同键同指纹返回已保存的抽取结果和领奖状态，即使活动已关闭；同键异指纹返回键冲突。
2. 查不到时，才检查活动是否开放（关闭则返回明确的 `campaign-closed`）和参与资格，再在事务里写参与记录。
3. 插入遇到唯一冲突时，先整笔回滚。

两种冲突在 PostgreSQL 里都是 SQLSTATE `23505`，错误码分不出它们，**要读错误诊断里的约束名**：

| 冲突的约束 | 含义 | 处理 |
|---|---|---|
| `draw_entries_one_per_principal` | 这个人已有参与记录 | 新事务按作用域键回查：同键同指纹 → 同一 POST 的并发重放，返回该结果；同键异指纹 → 键冲突；键不匹配 → “已经参与” |
| `draw_entries_pkey`（`entry_id`） | 生成的参与 ID 撞了，例如 ID 生成器出错 | 与重放无关，不走回查；按内部错误处理或换新 ID 重试 |

这样换键重试不会被当成同一次抽奖，并发的同键重放又能取回已提交的结果。库存例里 `reservations` 只有一条唯一约束（主键即作用域键），同样应确认冲突来自 `reservations_pkey` 再进入回查。

抽奖还要事先定义“报名已接受但奖品已发完”算什么。本例把它定义为已完成的未中奖结果：同一事务保存参与记录和权威的 `no-prize`，之后同键重放仍取回它，不会重抽。若活动改为“奖品不足就拒绝报名”，那次尝试就不保存结果、不占键，两种语义只能选一种。有限奖品的扣减、参与记录、中奖结果和待领取状态必须同事务提交；随机性与审计要符合活动承诺；统计事件不能决定资格或中奖结果。操作记录同样要在重放窗口内保留。

结果读取与领奖是独立的受权接口：`GET /draws/{campaignId}/entries/{entryId}` 只向结果所有者返回本人结果与领取状态；`POST /prizes/{prizeId}/claims` 再验证中奖记录的所有者，只收集履约需要的资料。活动管理接口的权限要比公开读取和本人参与更严。

> [!info] SQL 方言边界（核对于 2026-11-11）
> - 参数语法：PostgreSQL 用 `$1`、`$2`；SQLite 另有 `?`、`?NNN` 和命名参数，需按方言转换。
> - 失败后的事务范围：PostgreSQL 报错使整个事务进入失败状态；SQLite 默认的 ABORT 策略和 InnoDB 的重复键错误都只撤销失败语句，之前的扣减仍在事务里，所以“整笔回滚”必须由应用显式执行，见[约束何时检查](#%E7%BA%A6%E6%9D%9F%E4%BD%95%E6%97%B6%E6%A3%80%E6%9F%A5%EF%BC%8C%E5%A4%B1%E8%B4%A5%E5%90%8E%E4%BA%8B%E5%8A%A1%E9%87%8C%E8%BF%98%E5%89%A9%E4%BB%80%E4%B9%88%EF%BC%9F)。
> - SQLite 对照表：外键默认关闭，每条连接都要启用；普通表的类型声明不等同 PostgreSQL 的强类型，可用 SQLite 3.37 起的 `STRICT` 表或额外检查。

### 条件写与唯一裁决之后，还缺什么？

本章产出三件可复用的东西：附着在写语句上的条件 `UPDATE`，以返回行数作业务判断；按作用域键和指纹识别同一操作的幂等记录契约；零行或唯一冲突后整笔回滚、新事务回查的裁决流程。主线四用它们实现导出任务的幂等受理、worker 的条件领取和以 attempt 为代次的栅栏。

还有三个问题留给后面。约束到底能守哪些规则、索引怎样让回查和列表读得快，是[下一章](#23.%20%E7%BA%A6%E6%9D%9F%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%A7%84%E5%88%99%EF%BC%8C%E7%B4%A2%E5%BC%95%E5%8F%88%E6%80%8E%E6%A0%B7%E6%9C%8D%E5%8A%A1%E8%AF%BB%E5%8F%96%EF%BC%9F)；事务在 Read Committed 之外的隔离级别下会看到什么、跨多行的规则为什么条件写也守不住，是[事务与隔离](#24.%20%E4%BA%8B%E5%8A%A1%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%8C%E5%B9%B6%E5%8F%91%E4%BA%8B%E5%8A%A1%E5%90%84%E8%83%BD%E7%9C%8B%E8%A7%81%E4%BB%80%E4%B9%88%EF%BC%9F)；`COMMIT` 确认后数据库崩溃，记录靠什么留下，是[预写日志与恢复](#25.%20%E6%95%B0%E6%8D%AE%E5%BA%93%E7%A1%AE%E8%AE%A4%E6%8F%90%E4%BA%A4%E5%90%8E%E5%B4%A9%E6%BA%83%EF%BC%8C%E9%9D%A0%E4%BB%80%E4%B9%88%E6%81%A2%E5%A4%8D%EF%BC%9F)。

> [!info]- 来源
> - **Read Committed 的语句快照；并发 `UPDATE` 等待前一个更新者，提交后在新行版本上重检 `WHERE`，回滚则基于原行继续；`ON CONFLICT DO NOTHING` 在 Read Committed 下可能因快照不可见的结果而不插入**（“条件 UPDATE 怎样让并发请求排队？”“零行或唯一冲突之后怎样下结论？”）：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.1，核对于 2026-11-11。
> - **`UPDATE ... RETURNING` 只返回实际更新的行；位置参数在各自的语句内绑定**（“一次预留怎样执行？”）：[PostgreSQL 18, UPDATE](https://www.postgresql.org/docs/18/sql-update.html)；[PREPARE](https://www.postgresql.org/docs/18/sql-prepare.html)，核对于 2026-11-11。
> - **主键、唯一、外键、CHECK 与 NOT NULL 的行为，CHECK 对 NULL 放行**（“两张表各守住什么？”）：[PostgreSQL 18, Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)，§5.5.1–5.5.5，核对于 2026-11-11。
> - **事务全有或全无、提交时一同可见；报错后须回滚或回到 savepoint**（“零行或唯一冲突之后怎样下结论？”“库存还有余量时……”）：[PostgreSQL 18, Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html)，§3.4；[ROLLBACK](https://www.postgresql.org/docs/18/sql-rollback.html)，核对于 2026-11-11。
> - **竞争插入同一唯一键时等待对方提交或回滚再裁决**（“库存还有余量时……”“同一个键换了 SKU……”）：[PostgreSQL 18, INSERT](https://www.postgresql.org/docs/18/sql-insert.html)；[Index Uniqueness Checks](https://www.postgresql.org/docs/18/index-unique-checks.html)，§63.5，核对于 2026-11-11。本章单 SKU 时序是“行锁先串行化、插入时胜者已提交”这一具体路径。
> - **主键与唯一冲突同为 SQLSTATE `23505`，错误诊断带约束名**（“换到抽奖……”）：[PostgreSQL 18, Error Codes](https://www.postgresql.org/docs/18/errcodes-appendix.html)，Appendix A；约束名字段见 [libpq, PQresultErrorField](https://www.postgresql.org/docs/18/libpq-exec.html) 的 `PG_DIAG_CONSTRAINT_NAME`，核对于 2026-11-11。
> - **幂等方法的定义：重复请求的预期效果等同于一次**（“同一操作怎样被认出来？”）：[RFC 9110, §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)，核对于 2026-11-11。RFC 不规定本例的记录、指纹或取消后的当前状态，这些是本章声明的 API 契约。
> - **SQLite 外键默认关闭、`STRICT` 表、参数语法、ABORT 冲突策略的语句级回滚**（“SQL 方言边界”）：[Foreign Key Support](https://www.sqlite.org/foreignkeys.html)，§1–2；[STRICT Tables](https://www.sqlite.org/stricttables.html)；[SQL Language Expressions](https://www.sqlite.org/lang_expr.html)，§Parameters；[The ON CONFLICT Clause](https://www.sqlite.org/lang_conflict.html)，核对于 2026-11-11。
## 23. 约束守住哪些规则，索引又怎样服务读取？

上一章靠主键、`CHECK` 和复合主键守住了库存与预留记录。本章把这两类数据库对象分开讲清：constraint (约束) 是所有写入方都必须遵守的数据规则，违反就拒绝写入；index (索引) 是需要额外维护的访问结构，查询用不用它由计划器按成本决定。前者关乎正确性，后者关乎成本，二者常被一起建立，却回答不同的问题。

### 教学 schema 里有哪些表？

本章沿用主线三的库存案例，并补两张表：父表 `accounts`，让账户也能被外键引用；以及一张 `report_jobs` 任务表，因为讲索引需要一个“按账户列出最近记录”的读取，而库存表没有这种查询。这是一套独立的教学 schema，不要在已经建过同名表的库里原样重跑。SQL 以 PostgreSQL 18 为准。

~~~sql
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY
);

CREATE TABLE inventory (
    sku TEXT PRIMARY KEY,
    available INTEGER NOT NULL CHECK (available >= 0)
);

CREATE TABLE reservations (
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    principal_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    sku TEXT NOT NULL REFERENCES inventory(sku),
    status TEXT NOT NULL CHECK (status IN ('reserved', 'cancelled')),
    PRIMARY KEY (account_id, principal_id, idempotency_key)
);

CREATE TABLE report_jobs (
    job_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    principal_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')
    ),
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT report_jobs_idempotency_scope_key
        UNIQUE (account_id, principal_id, idempotency_key)
);
~~~

![四张表的键与约束：账户和库存是父表，预留与任务通过外键引用它们](../../engineering-foundations/data/resources/database-constraints-and-indexes-schema.svg)

*`reservations` 以作用域键为主键；`report_jobs` 另有任务 ID 主键，作用域键是单独的唯一约束；两张表的 `principal_id` 都没有外键。*

`principal_id` 只是存下来的作用域值，没有主体表外键。认证和授权不会因为这一列或某个外键而自动完成。

### 每类约束守住什么，守不住什么？

| 要保护的事实 | 约束 | 能保证 | 守不住 |
|---|---|---|---|
| 每个账户、SKU、任务只对应一行 | `PRIMARY KEY` | 唯一且非空的行标识；即使没写 `NOT NULL`，PostgreSQL 主键列也拒绝 NULL | — |
| 库存是已知的非负数 | `NOT NULL` + `CHECK (available >= 0)` | 两者并用才拒绝负数和未知值 | 单独的 `CHECK` 放行 NULL |
| 子记录引用存在的父行 | `REFERENCES` | 引用的账户或 SKU 必须存在；默认删除动作是 `NO ACTION`，级联要显式声明 | — |
| 一个作用域键最多一条记录 | 复合主键或 `UNIQUE` | 第二条同键记录被拒绝 | 不规定重放该返回什么，那是上一章的契约 |
| 状态取自允许的集合 | `CHECK (status IN (...))` | 当前值合法 | 不验证 `queued → running → succeeded` 这类转移顺序 |

两条盲区最常导致错误结论：

- **CHECK 对 NULL 放行。** CHECK 的结果为真或为 NULL 都算通过，所以 `CHECK (available >= 0)` 遇到 `available = NULL` 时求值为 NULL，写入成功。要拒绝未知值，必须同时声明 `NOT NULL`。这是本领域这条规则的权威位置。
- **CHECK 只看当前这一行。** 它不能可靠表达跨行或跨表的规则，例如“同一班次至少一人值班”。这类规则要靠唯一约束、外键，或把需要协调的写入放进合适的事务协议，见[写偏差与三种修法](#%E4%B8%BA%E4%BB%80%E4%B9%88%E7%A8%B3%E5%AE%9A%E5%BF%AB%E7%85%A7%E4%BB%8D%E4%BC%9A%E7%A0%B4%E5%9D%8F%E8%B7%A8%E8%A1%8C%E8%A7%84%E5%88%99%EF%BC%9F)。

### 键约束会自动建哪些索引？

- **主键和唯一约束自动建立唯一 B-tree 索引。** 不要再为同样的列重复建一个。`reservations` 的主键和 `report_jobs_idempotency_scope_key` 都以 `account_id` 开头，按账户前缀查找可以直接用它们。
- **外键不会为子表的外键列自动建索引。** 外键检查用的是父表主键或唯一键上的索引。反方向，删除或更新父行时，数据库要在子表里找引用它的行：`reservations` 的主键以 `account_id` 开头，删账户时的子行检查能用上它；`reservations.sku` 却不在任何索引的前导位置。如果要按 SKU 查预留，或常删改库存 SKU 而子行很多，就要按负载评估单独的 `reservations(sku)` 索引。
- **`UNIQUE` 默认把 NULL 看作互不相同。** 两行 `(acct-17, NULL)` 不算重复。要把 NULL 当成相同值，可以用 `UNIQUE NULLS NOT DISTINCT`。本例的唯一键每列都是 `NOT NULL`，没有这个歧义。

### 约束何时检查，失败后事务里还剩什么？

本例的约束都没有声明 `DEFERRABLE`，所以是立即检查：每行插入或更新时就检查，而不是等到 `COMMIT`。`CHECK` 和 `NOT NULL` 总是立即检查。

检查失败后，事务里还剩什么，不同数据库不一样：

| 数据库 | 一条语句违反约束后 | 应用要做什么 |
|---|---|---|
| PostgreSQL | 整个事务进入失败状态，后续语句都被拒绝 | `ROLLBACK`，或回到报错前建立的 savepoint |
| SQLite（默认 ABORT 策略） | 只撤销失败语句的更改，之前语句的更改还在事务里 | 需要全有或全无时，显式回滚整笔 |
| MySQL InnoDB（重复键） | 通常只回滚失败语句 | 同上，见 [InnoDB 支线](#%E9%87%8D%E5%A4%8D%E9%94%AE%E9%94%99%E8%AF%AF%E5%90%8E%EF%BC%8C%E4%BA%8B%E5%8A%A1%E9%87%8C%E8%BF%98%E5%89%A9%E4%BB%80%E4%B9%88%EF%BC%9F) |

上一章要求“零行或唯一冲突后整笔回滚”，原因就在这里：在后两种数据库里，失败语句之前的库存扣减仍在事务中，不显式回滚就可能被提交。唯一冲突怎样按约束名翻译成“重放、冲突或内部错误”，见[换到抽奖：两条唯一约束怎样分别裁决？](#%E6%8D%A2%E5%88%B0%E6%8A%BD%E5%A5%96%EF%BC%9A%E4%B8%A4%E6%9D%A1%E5%94%AF%E4%B8%80%E7%BA%A6%E6%9D%9F%E6%80%8E%E6%A0%B7%E5%88%86%E5%88%AB%E8%A3%81%E5%86%B3%EF%BC%9F)。

### 复合索引的列序怎样定？

调用方已获准查看 `acct-17` 的全部任务，现在要读这个账户最近的 20 个任务；创建时间相同时用任务 ID 定一个稳定顺序：

~~~sql
CREATE INDEX report_jobs_by_account_recent
    ON report_jobs (account_id, created_at DESC, job_id DESC);

SELECT job_id, status, created_at
FROM report_jobs
WHERE account_id = $1          -- $1 = acct-17
ORDER BY created_at DESC, job_id DESC
LIMIT 20;
~~~

B-tree 按复合键的字典序排列：先比 `account_id`，相同再比 `created_at`，再比 `job_id`。所以列序从查询的过滤和排序推导，这是本领域复合索引列序的权威规则：

| 索引列 | 在查询里的作用 | 边界 |
|---|---|---|
| `account_id` | 等值条件直接定位这个账户的一段连续键区间 | 前导列等值条件最直接；PostgreSQL 18 的多列 B-tree 也能利用非前导列条件或 skip scan，只是通常不如前导列有效 |
| `created_at DESC` | 在账户区间内按时间从新到旧读出 | 匹配的索引可以省掉排序，但计划器仍会和“顺序扫描加排序”比成本 |
| `job_id DESC` | 同一时刻的任务有确定顺序 | 排序方向须与索引整体一致或整体相反；B-tree 可以反向扫描，`(account_id, created_at, job_id)` 升序索引同样能服务这个查询，但服务不了 `created_at DESC, job_id ASC` |
| `status` | 只在输出里 | 索引不含它，要回表取值，这不是覆盖该查询的索引 |

`created_at` 用 `TIMESTAMPTZ` 才能按时间点正确排序：带时区的输入被换算后按 UTC 存储，原时区标签不保留，输出按会话时区显示。把混合格式的本地时间文本存进字符串列，字典序就不等于时间顺序。

同一套“完整排序键必须唯一”的要求，后面会用在键集分页的游标上，见[怎样无重复、无遗漏地分页读取一个还在变化的集合？](#29.%20%E6%80%8E%E6%A0%B7%E6%97%A0%E9%87%8D%E5%A4%8D%E3%80%81%E6%97%A0%E9%81%97%E6%BC%8F%E5%9C%B0%E5%88%86%E9%A1%B5%E8%AF%BB%E5%8F%96%E4%B8%80%E4%B8%AA%E8%BF%98%E5%9C%A8%E5%8F%98%E5%8C%96%E7%9A%84%E9%9B%86%E5%90%88%EF%BC%9F)。B-tree 为什么适合按页读取，见[数组、链表、树和哈希表各靠什么找到目标、维护顺序？](#2.%20%E6%95%B0%E7%BB%84%E3%80%81%E9%93%BE%E8%A1%A8%E3%80%81%E6%A0%91%E5%92%8C%E5%93%88%E5%B8%8C%E8%A1%A8%E5%90%84%E9%9D%A0%E4%BB%80%E4%B9%88%E6%89%BE%E5%88%B0%E7%9B%AE%E6%A0%87%E3%80%81%E7%BB%B4%E6%8A%A4%E9%A1%BA%E5%BA%8F%EF%BC%9F)。

### 索引什么时候值得？

- **`LIMIT` 让匹配的索引可以提前停。** 计划器选了上面的索引时，执行器收集到 20 条可见结果就可以停止取行。它不保证只读前 20 个物理索引项：MVCC 可见性等条件可能让它检查更多项。
- **读取比例大时，顺序扫描可能更便宜。** 如果查询要读整表的很大一部分，顺序读表再排序常比沿索引逐条跳回表便宜。
- **每个索引都有持续成本。** 它占磁盘和缓存，每次写入都要维护它，之后还要清理。字段越多不等于越快。
- **用真实数据验证。** 在目标数据库上，用真实数据量和统计信息看 `EXPLAIN`。`EXPLAIN ANALYZE` 会真的执行语句，评估带写入的语句时它真会改数据。

### 计划器为什么有时不用已建的索引？

计划器比较各条访问路径的估算成本，索引存在不等于一定被选中。下面两个实例是本地运行的计划输出（版本见标题，与本章依据的 PostgreSQL 18 文档不同），只用来说明计划会随数据量和统计信息变化；没有测量耗时。

> [!example]- 实例：两行表上已有匹配索引，仍选顺序扫描（本地 PostgreSQL 14.24）
> 在上面的 `report_jobs` 中只插入两行，并收集统计：
>
> ~~~sql
> INSERT INTO accounts VALUES ('acct-17');
> INSERT INTO report_jobs VALUES
>     ('job-a1', 'acct-17', 'user-17', 'key-1',
>      'fingerprint-1', 'queued', '2026-11-10 12:00:00+00'),
>     ('job-a2', 'acct-17', 'user-17', 'key-2',
>      'fingerprint-2', 'running', '2026-11-11 12:00:00+00');
> ANALYZE report_jobs;
>
> EXPLAIN (COSTS OFF)
> SELECT job_id, status, created_at
> FROM report_jobs
> WHERE account_id = 'acct-17'
> ORDER BY created_at DESC, job_id DESC
> LIMIT 20;
> ~~~
>
> 实际计划：
>
> ~~~text
> Limit
>   ->  Sort
>         Sort Key: created_at DESC, job_id DESC
>         ->  Seq Scan on report_jobs
>               Filter: (account_id = 'acct-17'::text)
> ~~~
>
> 匹配过滤和排序的索引已经存在，计划器估算后仍选了 `Seq Scan → Sort`。

> [!example]- 实例：1,000 个合成订单上建索引前后的计划（本地 SQLite 3.51.0）
> 这是一张独立的教学表，与 [SQL 空值章](#27.%20%E7%A9%BA%E5%80%BC%E3%80%81%E5%A4%96%E8%BF%9E%E6%8E%A5%E5%92%8C%E5%88%86%E7%BB%84%E4%BC%9A%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E4%B8%80%E5%BC%A0%E6%B1%87%E6%80%BB%E8%A1%A8%E7%9A%84%E7%BB%93%E6%9E%9C%EF%BC%9F)里的同名表结构不同。`customer_id = n % 100`，所以 `customer_id = 17` 恰好对应 10 行（`order_id` 为 17、117、……、917）。
>
> ~~~sql
> PRAGMA automatic_index = OFF;
> CREATE TABLE orders (
>     order_id INTEGER PRIMARY KEY,
>     customer_id INTEGER NOT NULL,
>     amount_cents INTEGER NOT NULL,
>     placed_at INTEGER NOT NULL
> );
> WITH RECURSIVE seq(n) AS (
>     VALUES(1)
>     UNION ALL
>     SELECT n + 1 FROM seq WHERE n < 1000
> )
> INSERT INTO orders SELECT n, n % 100, n * 25, n FROM seq;
>
> EXPLAIN QUERY PLAN
> SELECT order_id, amount_cents, placed_at
> FROM orders WHERE customer_id = 17 ORDER BY placed_at DESC;
> -- SCAN orders；USE TEMP B-TREE FOR ORDER BY
>
> CREATE INDEX orders_by_customer_and_time ON orders(customer_id, placed_at);
>
> EXPLAIN QUERY PLAN
> SELECT order_id, amount_cents, placed_at
> FROM orders WHERE customer_id = 17 ORDER BY placed_at DESC;
> -- SEARCH orders USING INDEX orders_by_customer_and_time (customer_id=?)
> ~~~
>
> 无索引时全表 `SCAN`，再用临时 B-tree 排序；建了 `(customer_id, placed_at)` 后，改为在 `customer_id = 17` 的区间里按索引 `SEARCH`，并反向读取以满足 `placed_at DESC`，临时排序消失。查询要取 `amount_cents`，索引不含该列，所以仍不是覆盖索引。`EXPLAIN QUERY PLAN` 的输出面向调试，格式可能随版本变化。

### 约束和索引之后，下一个问题

本章产出两条可复用的规则：约束按“能保证什么、守不住什么”选用，其中 `CHECK` 必须配 `NOT NULL`，跨行规则不能交给 `CHECK`；复合索引的列序从过滤和排序推导，再用真实计划验证。约束只裁决单条写入能否成立；多条语句放进一个事务后，各个事务能看到别人的哪些写入、失败后该回滚还是重试，是[事务能保证什么，并发事务各能看见什么？](#24.%20%E4%BA%8B%E5%8A%A1%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%8C%E5%B9%B6%E5%8F%91%E4%BA%8B%E5%8A%A1%E5%90%84%E8%83%BD%E7%9C%8B%E8%A7%81%E4%BB%80%E4%B9%88%EF%BC%9F)的问题。

> [!info]- 来源
> - **主键、唯一、外键与删除动作、CHECK 对 NULL 放行、CHECK 只看当前行、`NULLS NOT DISTINCT`、外键列不自动建索引**（“每类约束守住什么……”“键约束会自动建哪些索引？”）：[PostgreSQL 18, Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)，§5.5，核对于 2026-11-11。
> - **`TIMESTAMPTZ` 的输入换算、UTC 存储与按会话时区显示**（“复合索引的列序怎样定？”）：[PostgreSQL 18, Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html)，§8.5，核对于 2026-11-11。
> - **可延迟约束与立即检查**（“约束何时检查……”）：[PostgreSQL 18, SET CONSTRAINTS](https://www.postgresql.org/docs/18/sql-set-constraints.html)；**报错后的失败事务与 `ROLLBACK`/savepoint**：[Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html)，§3.4；[ROLLBACK](https://www.postgresql.org/docs/18/sql-rollback.html)，核对于 2026-11-11。
> - **SQLite 默认 ABORT 只撤销失败语句**（“约束何时检查……”）：[SQLite, The ON CONFLICT Clause](https://www.sqlite.org/lang_conflict.html)，核对于 2026-11-11。
> - **多列 B-tree 的前导列、非前导列条件与 skip scan**（“复合索引的列序怎样定？”）：[PostgreSQL 18, Multicolumn Indexes](https://www.postgresql.org/docs/18/indexes-multicolumn.html)，§11.3；**索引顺序、反向扫描与 `ORDER BY`/`LIMIT`**：[Indexes and ORDER BY](https://www.postgresql.org/docs/18/indexes-ordering.html)，§11.4，核对于 2026-11-11。
> - **索引维护成本、计划器取舍、`EXPLAIN` 与 `EXPLAIN ANALYZE` 会实际执行**（“索引什么时候值得？”）：[PostgreSQL 18, Indexes Introduction](https://www.postgresql.org/docs/18/indexes-intro.html)，§11.1；[EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)，核对于 2026-11-11。
> - **SQLite 的 `SCAN`/`SEARCH` 输出与格式边界、多列索引同时筛选与排序**（SQLite 实例）：[EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)；[Query Planning](https://www.sqlite.org/queryplanner.html)，§§2.2、3.1，核对于 2026-11-11。
## 24. 事务能保证什么，并发事务各能看见什么？

前两章已经用一笔事务把库存扣减和预留记录绑在一起，并依赖 Read Committed 的一条行为让并发请求排队。本章把事务本身讲清：它承诺哪几件事、失败时该回滚、重试还是回查，各隔离级别让并发事务看见什么，以及为什么即使快照稳定，跨多行的规则仍会被破坏。库存的并发时序不再重讲，只引用[第一章](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)的结论：A 先扣减并提交，同一请求的重放 B 等锁、重检、零行，回滚后在新事务读到 A 的记录。SQL 以 PostgreSQL 18 为准。

### ACID 各描述什么边界？

transaction (事务) 把多条语句放进同一次提交或回滚。ACID 是描述这个边界的四个词，每一项都受数据库实现、配置和底层存储约束：

- **atomicity (原子性)**：同一事务里的写入一起提交，或一起被回滚撤销。库存扣减和预留记录要么都在，要么都不在。
- **consistency (一致性)**：合法状态由约束和应用规则定义。事务不会自己发明业务不变量；`available >= 0` 是 `CHECK` 写出来的，不是事务带来的。
- **isolation (隔离性)**：并发事务按隔离级别观察或等待彼此的写入。级别不同，看到的东西不同，下文逐级说明。
- **durability (持久性)**：成功提交能扛住配置与存储所承诺范围内的故障。异步提交或不兑现刷盘的存储会缩小这个范围，见[下一章](#25.%20%E6%95%B0%E6%8D%AE%E5%BA%93%E7%A1%AE%E8%AE%A4%E6%8F%90%E4%BA%A4%E5%90%8E%E5%B4%A9%E6%BA%83%EF%BC%8C%E9%9D%A0%E4%BB%80%E4%B9%88%E6%81%A2%E5%A4%8D%EF%BC%9F)。

### 一笔事务失败后，该回滚、重试还是回查？

事务失败不是一种情况。三类失败的处置不同，混用会出错，这是本领域的权威规则：

| 失败类型 | 典型信号 | 处置 |
|---|---|---|
| 约束或其他数据库错误 | 唯一冲突、外键违规、CHECK 失败 | 显式 `ROLLBACK`，不能继续 `COMMIT`；按错误类别报告或进入业务裁决 |
| 序列化失败 | SQLSTATE `40001`（Repeatable Read 或 Serializable 下） | 从事务**开头**重试整笔事务，包括最初的读取 |
| 提交结果未知 | `COMMIT` 发出后连接断开或响应丢失 | 不当作失败；保留**原幂等键和原指纹**回查，或沿原来的条件更新与唯一约束路径重试 |

第一类在库存例里已有完整流程：零行或唯一冲突后整笔回滚，新事务按作用域键回查，见[零行或唯一冲突之后怎样下结论？](#%E9%9B%B6%E8%A1%8C%E6%88%96%E5%94%AF%E4%B8%80%E5%86%B2%E7%AA%81%E4%B9%8B%E5%90%8E%E6%80%8E%E6%A0%B7%E4%B8%8B%E7%BB%93%E8%AE%BA%EF%BC%9F)。PostgreSQL 报错后事务处于失败状态，再发 `COMMIT` 也只会得到回滚。

第二类必须从头重试，因为整笔事务的决策都建立在旧快照上。只重放失败的那条语句，会沿用已经失效的读取结果。

第三类最容易处理错。`COMMIT` 可能已经在数据库里生效，只是确认没送回来。回查到同键同指纹的记录，就确认它已提交；查不到只说明这次查询没看到提交记录，原事务可能仍在提交中。此时**不能换一个新键**再做一次：新键会让唯一约束把它当成另一项操作，原事务若已提交，就成了两次预留。请求层面怎样在这种状态下停住并稍后重放，见[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

### 各隔离级别挡住哪些并发现象？

隔离级别按“禁止哪些现象”定义：

- dirty read (脏读)：读到另一个事务尚未提交的写入。
- non-repeatable read (不可重复读)：同一事务重读一行，看到别的事务在此期间提交的新值。
- phantom read (幻读)：同一条件的查询再执行一次，满足条件的行集合因别的提交而变了。
- serialization anomaly (序列化异常)：一组都成功提交的事务，其结果无法用任何一种逐个串行执行的顺序解释。

SQL 标准规定每个级别**至少**要防住什么，实现可以更强。PostgreSQL 18 的对照如下：

| 级别 | 脏读 | 不可重复读 | 幻读 | 序列化异常 |
|---|---|---|---|---|
| Read Uncommitted | 不发生（行为等同 Read Committed） | 可能 | 可能 | 可能 |
| Read Committed（默认） | 不发生 | 可能 | 可能 | 可能 |
| Repeatable Read | 不发生 | 不发生 | 不发生（标准允许，PostgreSQL 不发生） | 可能，例如写偏差 |
| Serializable | 不发生 | 不发生 | 不发生 | 不发生 |

### 快照从什么时候开始？

同名级别的行为取决于快照的粒度。PostgreSQL 的两档：

- **Read Committed：每条语句一个新快照。** 语句只看到它开始前已提交的数据。并发更新同一行时，后来者等前者结束；前者提交后，后来者在新行版本上重检 `WHERE`，前者回滚则对原行继续。库存的条件 `UPDATE` 正是靠这一点：B 重检时看到 0，返回零行。
- **Repeatable Read：整笔事务一个快照。** 快照始于事务中第一条非事务控制语句（`BEGIN` 不算）。之后等待别的事务也不会刷新它。若事务要修改的行在它的快照之后已被别的事务提交修改，语句以 `40001` 失败。

同样的库存时序换成 Repeatable Read：B 的 `UPDATE` 等到 A 提交后，不是重检条件，而是直接失败。按上一节的规则，B 从头重试整笔事务；新快照里库存是 0，`UPDATE` 返回零行，后面走回查，结局与 Read Committed 相同，只是多了一次重试。

隔离级别的名字不说明实现。MySQL InnoDB 也有 Repeatable Read，但它的普通读用首次一致性读的快照，`UPDATE` 却读最新版本，同一时序里 B 得到的是“影响 0 行”而不是 `40001`，见 [InnoDB 支线](#26.%20InnoDB%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%B4%A2%E5%BC%95%E8%AE%B0%E5%BD%95%E3%80%81%E6%97%A7%E7%89%88%E6%9C%AC%E5%92%8C%E6%97%A5%E5%BF%97%E5%A4%84%E7%90%86%E5%90%8C%E4%B8%80%E7%AC%94%E5%BA%93%E5%AD%98%E4%BA%8B%E5%8A%A1%EF%BC%9F)。

> [!info] MVCC 不等于“读写都不用等”
> multi-version concurrency control (多版本并发控制，MVCC) 让快照读按可见性规则选择行版本。PostgreSQL 更新一行时写入新的 tuple 版本，旧快照仍能读到对它可见的旧版本，因此读不必等写。但写写冲突仍要等：B 更新 A 正在改的库存行时照样排队，Repeatable Read 下还会失败；`FOR UPDATE` 等显式锁和其他资源等待也都还在。旧版本也要清理：PostgreSQL 的 VACUUM 回收不再对任何活动快照可见的旧 tuple，长期持有旧快照会拖延清理。

### 为什么稳定快照仍会破坏跨行规则？

库存规则只涉及一行，条件 `UPDATE` 就够了。规则跨越多行时，即使每个事务看到的都是稳定快照，也会出错，这叫 write skew (写偏差)。下面换一个独立的小例子，因为库存案例只有一行，演示不出它。

排班表里医生甲、乙各一行，规则是同一班次**至少一人值班**。两笔事务各关闭一人，交错如下：

~~~mermaid
sequenceDiagram
    participant T1
    participant DB as 排班表（甲、乙各一行）
    participant T2
    Note over T1,T2: 两笔都是 Repeatable Read，快照里甲、乙都在岗
    T1->>DB: 查在岗人数
    DB-->>T1: 2 人
    T2->>DB: 查在岗人数
    DB-->>T2: 2 人（同样的快照内容）
    T1->>DB: 关闭甲的值班（只改甲行）
    T2->>DB: 关闭乙的值班（只改乙行）
    T1->>DB: COMMIT
    DB-->>T1: 成功
    T2->>DB: COMMIT
    DB-->>T2: 成功：两笔改的是不同行，没有写写冲突
    Note over DB: 结果：没人值班
~~~

`CHECK` 帮不上忙，因为它只看当前这一行。修法取决于规则的形状，这是本领域写偏差修法的权威位置：

**修法一：把规则物化成一行，再用条件写守住。** 给班次加一行值班人数，关闭某人值班时先条件扣减，计数行和医生行在同一事务里更新：

~~~sql
UPDATE shift_coverage
SET on_call = on_call - 1
WHERE shift_id = $1 AND on_call > 1;
-- $1 = 班次 ID。恰好一行才继续更新医生行；零行说明只剩一人，拒绝关闭。
~~~

跨行规则由此变成单行上的条件，两个并发事务在这一行上排队：

~~~mermaid
sequenceDiagram
    participant T1
    participant DB as shift_coverage 计数行
    participant T2
    Note over T1,T2: 修法一，Read Committed：先条件扣减计数行
    T1->>DB: UPDATE ... SET on_call = on_call - 1 WHERE on_call > 1
    DB-->>T1: 1 行（2 → 1），T1 持有行锁
    T2->>DB: 同一条 UPDATE
    Note over DB: T2 在计数行上等待
    T1->>DB: 关闭甲（更新甲行），COMMIT
    DB-->>T2: 在新版本 on_call = 1 上重检条件：0 行
    Note over T2: 拒绝关闭乙
~~~

**修法二：Read Committed 下所有写方先锁同一控制行，再用下一条语句检查。** 关键在 T2 拿到锁之后的**下一条** `SELECT`：

~~~mermaid
sequenceDiagram
    participant T1
    participant DB as 班次控制行与排班表
    participant T2
    Note over T1,T2: 修法二，Read Committed：所有写方先锁同一控制行
    T1->>DB: SELECT 班次行 FOR UPDATE
    DB-->>T1: 取得锁
    T2->>DB: SELECT 班次行 FOR UPDATE
    Note over DB: T2 在锁上等待
    T1->>DB: 查在岗人数（2），关闭甲，COMMIT
    DB-->>T2: 取得锁
    T2->>DB: 下一条 SELECT 取新快照，查在岗人数
    DB-->>T2: 只剩乙 1 人
    Note over T2: 拒绝关闭乙
~~~

这个方案依赖“每条语句一个新快照”，Repeatable Read 的快照不随等待刷新，不能照搬。所有改这条规则的写入路径都必须先锁同一行，漏一条就失效。

**修法三：所有维护这条规则的事务都用 Serializable。** PostgreSQL 会检测到这组事务无法串行解释，让其中一笔以 `40001` 失败，失败方从头重试：

~~~mermaid
sequenceDiagram
    participant T1
    participant DB as 排班表
    participant T2
    Note over T1,T2: 修法三：所有维护这条规则的事务都用 Serializable
    T1->>DB: 查在岗人数（2），关闭甲
    T2->>DB: 查在岗人数（2），关闭乙
    T1->>DB: COMMIT
    DB-->>T1: 成功
    T2->>DB: 继续执行或 COMMIT
    DB-->>T2: 40001：这组事务无法串行解释
    Note over T2: 回滚，从头重试整笔事务<br/>（哪一笔、在哪条语句失败由数据库决定，这里画成 T2）
    T2->>DB: 新事务：查在岗人数
    DB-->>T2: 只剩乙 1 人
    Note over T2: 放弃关闭
~~~

保护只在参与的事务都运行 Serializable 时成立；只重试最后一条 `UPDATE` 会沿用旧决策，仍然错。

| 修法 | 适用 | 代价 |
|---|---|---|
| 物化为单行计数 + 条件写 | 规则能归结为一个数 | 多维护一行，所有写方都要同时更新它 |
| 先锁控制行（Read Committed） | 规则复杂但有自然的“控制行” | 写入在控制行上串行化；每条写路径都要遵守 |
| 全部 Serializable + 整笔重试 | 规则难以物化，写方都可控 | 要处理 `40001` 重试，冲突多时吞吐下降 |

### 事务管不到哪些副作用？

上面的手段都只作用于本数据库。事务里不要做两件事：

- **执行无法撤销的远端操作**，例如调用支付。回滚撤不回远端的扣款，提交结果未知时也不知道远端做了没有。
- **直接发布消息。** 先发后提交，消息可能指向一笔后来回滚的记录；先提交后发，进程可能在两步之间崩溃，消息永远没发。

做法是在同一事务里写一条 outbox 记录，与业务修改一起原子提交，提交后由后台进程投递；投递仍可能重复，消费者要去重。这个机制的完整推导在[耗时任务怎样被持久受理，并保证一定会被唤醒？](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)，远端操作本身怎样去重和对账，在[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

事务里也不要等长时间的网络调用。事务持有的行锁和连接会在这段时间里一直被占着，其他请求排队，连接池也会被耗尽，见[ORM 会话怎样借用连接，连接池为什么会耗尽？](#28.%20ORM%20%E4%BC%9A%E8%AF%9D%E6%80%8E%E6%A0%B7%E5%80%9F%E7%94%A8%E8%BF%9E%E6%8E%A5%EF%BC%8C%E8%BF%9E%E6%8E%A5%E6%B1%A0%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E8%80%97%E5%B0%BD%EF%BC%9F)。

### 提交确认之后还剩什么问题？

本章产出：事务失败的三类处置（尤其是提交结果未知时保留原键回查、不换新键）；各隔离级别的快照粒度和它们挡住的现象；写偏差的三种修法；以及“事务只管本库”这条边界。隔离讨论的是并发事务之间的可见性。另一个问题是：数据库已经确认了 `COMMIT`，随即崩溃，这次提交凭什么还在？这是[数据库确认提交后崩溃，靠什么恢复？](#25.%20%E6%95%B0%E6%8D%AE%E5%BA%93%E7%A1%AE%E8%AE%A4%E6%8F%90%E4%BA%A4%E5%90%8E%E5%B4%A9%E6%BA%83%EF%BC%8C%E9%9D%A0%E4%BB%80%E4%B9%88%E6%81%A2%E5%A4%8D%EF%BC%9F)的问题。

> [!info]- 来源
> - **隔离现象的定义、标准与 PostgreSQL 18 级别对照（Read Uncommitted 等同 Read Committed、Repeatable Read 不发生幻读）、Read Committed 每语句快照与等锁后重检、Repeatable Read 快照起点与 `40001`、Serializable 检测与整笔重试**（“各隔离级别……”“快照从什么时候开始？”“为什么稳定快照……”）：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2、Table 13.1，核对于 2026-11-12。
> - **`COMMIT` 使改动对其他会话可见并按持久策略保留**（“ACID 各描述什么边界？”）：[PostgreSQL 18, COMMIT](https://www.postgresql.org/docs/18/sql-commit.html)；**报错后事务失败、须回滚**：[Transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html)，§3.4，核对于 2026-11-12。
> - **MVCC 快照可见性与 VACUUM 清理旧版本**（MVCC 说明）：[PostgreSQL 18, Introduction to MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html)，§13.1；[Routine Vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html)，§24.1.2，核对于 2026-11-12。
> - **InnoDB 同名级别的快照读与锁定读**（“快照从什么时候开始？”的对照）：[MySQL 8.4, Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)，§17.7.2.1，核对于 2026-11-12。
## 25. 数据库确认提交后崩溃，靠什么恢复？

上一章讨论的是并发事务之间能看见什么；本章换一个问题：数据库已经对 `COMMIT` 回了确认，随即断电或进程崩溃，这次提交凭什么还在，没提交的修改又为什么不会冒出来。答案是 write-ahead log (预写日志，WAL)。本章以 PostgreSQL 18 本地单节点为例讲它怎样把“提交确认”和“数据页写回”分开、崩溃后怎样恢复，以及恢复到过去某个时点还需要什么。

### 提交为什么不必等数据页写回？

一笔事务改的行散落在不同的数据页上。如果每次提交都要把所有受影响的数据页同步写到磁盘，提交就要等多次随机写。WAL 用一条规则避开这个代价，这是本领域 WAL 的权威定义：

> **先把修改记入日志并持久化，才允许对应的数据页写回持久存储。**

由此得到提交路径：

1. 事务修改库存行和预留行，在内存里生成相应的 WAL 记录。
2. `COMMIT` 时追加一条提交记录。
3. 提交所需的 WAL 持久化之后，服务端才确认提交成功。
4. 数据页可以在提交之前或之后写回，唯一的要求是：写回某页之前，与它相关的 WAL 已经持久。

日志是顺序追加的，持久化一段连续日志比写回散落的数据页便宜；并发的小事务还可以共用一次 WAL 刷盘，即 group commit (组提交)。

![同步提交先持久化所需 WAL，数据页可在提交前后独立写回](../../engineering-foundations/data/resources/d4-postgresql-wal-commit.svg)

*提交确认只等 WAL 持久；数据页写回与确认无先后约束，只要求晚于对应 WAL。*

这张图和下文的恢复结论都基于同一组前提，只在这里说一次：

- `synchronous_commit = on`（默认），服务端在确认前等待提交所需的 WAL 刷到本地持久存储；
- `fsync = on`，数据库确实发出刷盘请求；
- 文件系统、控制器和设备如实兑现刷盘，而不是只写进易失缓存就报告完成。

任何一条不成立，“已确认就一定能恢复”都不再成立。例如把 `synchronous_commit` 设为 `off`，确认不再等 WAL 刷盘，提交延迟变短，代价是数据库崩溃时可能丢掉最近几笔**已经确认过**的事务（不会损坏其他已提交数据）。下游若已按成功响应执行了外部动作，就要能承受这段风险。

图里还有一个容易忽略的点：确认本身也可能在返回途中丢失。客户端收不到确认，不等于没提交，这属于上一章的“提交结果未知”，要按原键回查，见[一笔事务失败后，该回滚、重试还是回查？](#%E4%B8%80%E7%AC%94%E4%BA%8B%E5%8A%A1%E5%A4%B1%E8%B4%A5%E5%90%8E%EF%BC%8C%E8%AF%A5%E5%9B%9E%E6%BB%9A%E3%80%81%E9%87%8D%E8%AF%95%E8%BF%98%E6%98%AF%E5%9B%9E%E6%9F%A5%EF%BC%9F)。

### 崩溃后，恢复怎样决定哪些修改可见？

沿用库存案例的初始状态：`SKU-7.available = 1`，没有 `reserve-demo-208` 的记录；A、B 是这件库存上全部的写入尝试，期间没有别的库存写者。这个前提让“恢复后看到什么”能完全归因到 A、B 的提交状态；若另有写者，库存值就不能这样解读。

![PostgreSQL 崩溃恢复：重放 WAL 后按提交状态决定可见结果](../../engineering-foundations/data/resources/d4-postgresql-wal-crash.svg)

*重放页面修改不等于事务已提交；可见结果取决于有没有持久的提交记录。*

启动恢复从最近的检查点起重放所需的 WAL，把尚未写回的页面修改补上。然后分两种情况：

- **有一笔尝试的提交记录已持久。** 库存只有一件，A、B 至多一笔能提交。即使数据页还没写回，重放也会补出库存扣减和那条预留记录。恢复后读到 `available = 0` 和一条 `reserved` 记录。
- **A、B 都没有持久的提交记录。** 重放仍可能把它们的页面修改写进数据页，但重放本身不等于提交。PostgreSQL 的行版本是否可见，取决于写入它的事务是否已提交；没提交的新库存版本和预留行对查询不可见，不需要把页面改回去。恢复后读到 `available = 1`，没有预留记录。

> [!example] 一次提交后立即崩溃，怎样检查结果
> 恢复后若读到 `available = 0` 和 `reserve-demo-208` 的 `reserved` 记录，说明其中一笔已持久提交，即使崩溃时数据页尚未写回；若读到 `available = 1` 且没有记录，说明两笔都没有持久提交。若 API 在收到提交确认前就失联，查到同键记录可以确认成功；暂时查不到不证明原事务已经结束，要保留原键处理。HTTP 响应不是数据库的提交记录。

这是单节点本地崩溃恢复。它保护的是“这台机器的进程或电源出故障”；整块盘损坏、机房故障这类跨故障域的问题，要靠复制与备份。

### 恢复到过去某个时点还需要什么？

WAL 不是 point-in-time recovery (时间点恢复，PITR) 的全部材料。要把库恢复到过去某一时刻，需要：

1. 一份适用的 base backup (基础备份)；
2. 从这份备份的起点到目标时刻**连续、完整**的 WAL 归档。

中间缺了一段 WAL，就不能从这份备份跨过缺口恢复到之后的时刻。缺口之后若另有一份适用的基础备份，就从那份备份开始一个新的可恢复范围。

> [!info] 实例：其他引擎各有自己的日志
> SQLite 有自己的回滚日志和 WAL 模式及其配置，不能把 PostgreSQL 的文件布局和恢复步骤直接套用。MySQL InnoDB 用 redo、undo 和 binlog 三种日志协作，崩溃时按 binlog 里的事务标识决定提交或回滚，见[InnoDB 怎样用索引记录、旧版本和日志处理同一笔库存事务？](#26.%20InnoDB%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%B4%A2%E5%BC%95%E8%AE%B0%E5%BD%95%E3%80%81%E6%97%A7%E7%89%88%E6%9C%AC%E5%92%8C%E6%97%A5%E5%BF%97%E5%A4%84%E7%90%86%E5%90%8C%E4%B8%80%E7%AC%94%E5%BA%93%E5%AD%98%E4%BA%8B%E5%8A%A1%EF%BC%9F)。

> [!info]- 课程背景：ARIES 怎样确定重做和撤销的范围
> ARIES 是经典的 WAL 恢复算法，分三个阶段：
> - **analysis (分析)**：建立 dirty page table (脏页表)，记录崩溃时可能未写回的脏页。每页的 recLSN 是该页自上次干净以来可能需要 REDO (重做) 的最早日志位置；所有页中最小的 recLSN 就是 REDO 的起点。注意它是重做的起点，不是分析阶段要扫描的最早日志位置。
> - **redo**：从起点开始 repeat history (重演历史)，把所有记录过的修改重做一遍，包括未提交事务的修改。
> - **undo**：撤销崩溃时未完成的 loser 事务。
>
> 这是通用的课程算法。PostgreSQL 和 InnoDB 都使用预写日志，但都不按原版 ARIES 执行恢复；上文 PostgreSQL 不撤销页面、而靠提交状态判断可见性，就是一处差别。逐步推演的例题见[WAL 与 ARIES 的逐步恢复例题](../../archive/uni-subjects/COMP90050ADBS/condensed-note-w4-wal-and-aries-recovery.md)。

### 存得对之后，怎样读得对？

本章产出：WAL 把提交确认与数据页写回分开，提交只等日志持久；这个保证依赖同步提交、`fsync` 和设备如实刷盘；崩溃恢复按持久提交记录决定可见结果，重放不等于提交；PITR 还需要基础备份和连续的 WAL 归档。

到这里，写入路径上的保证已经齐了：条件写和唯一约束裁决并发，事务界定原子性与可见性，WAL 让确认过的提交扛过崩溃。想看同一笔库存事务在另一个引擎里怎样落地，可以读 [InnoDB 支线](#26.%20InnoDB%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%B4%A2%E5%BC%95%E8%AE%B0%E5%BD%95%E3%80%81%E6%97%A7%E7%89%88%E6%9C%AC%E5%92%8C%E6%97%A5%E5%BF%97%E5%A4%84%E7%90%86%E5%90%8C%E4%B8%80%E7%AC%94%E5%BA%93%E5%AD%98%E4%BA%8B%E5%8A%A1%EF%BC%9F)。主线接下来转向读取路径：数据存对了，一条汇总查询仍可能因为空值、外连接和分组粒度算错，见[空值、外连接和分组会怎样改变一张汇总表的结果？](#27.%20%E7%A9%BA%E5%80%BC%E3%80%81%E5%A4%96%E8%BF%9E%E6%8E%A5%E5%92%8C%E5%88%86%E7%BB%84%E4%BC%9A%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E4%B8%80%E5%BC%A0%E6%B1%87%E6%80%BB%E8%A1%A8%E7%9A%84%E7%BB%93%E6%9E%9C%EF%BC%9F)。

> [!info]- 来源
> - **WAL 先于相关数据页持久、提交只需刷 WAL、崩溃后重放、基础备份加连续日志的时间点恢复**（“提交为什么不必等数据页写回？”“崩溃后……”）：[PostgreSQL 18, WAL Introduction](https://www.postgresql.org/docs/18/wal-intro.html)，§28.3，核对于 2026-11-12。
> - **同步与异步提交的确认差异；`synchronous_commit = off` 可能丢失最近确认的事务但不破坏一致性**（同上）：[PostgreSQL 18, Asynchronous Commit](https://www.postgresql.org/docs/18/wal-async-commit.html)，§28.4；**检查点、刷页与组提交相关配置**：[WAL Configuration](https://www.postgresql.org/docs/18/wal-configuration.html)，§28.5，核对于 2026-11-12。
> - **PITR 需要基础备份与连续 WAL 归档**（“恢复到过去某个时点……”）：[PostgreSQL 18, Continuous Archiving and Point-in-Time Recovery](https://www.postgresql.org/docs/18/continuous-archiving.html)，§25.3，核对于 2026-11-12。
> - **行版本可见性取决于事务提交状态**（“崩溃后……”）：[PostgreSQL 18, Introduction to MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html)，§13.1，核对于 2026-11-12。
> - **SQLite 的独立事务与 WAL 机制**（实例）：[SQLite Transactions](https://www.sqlite.org/lang_transaction.html)；[Write-Ahead Logging](https://www.sqlite.org/wal.html)，核对于 2026-11-12。
> - **ARIES 的分析、重做、撤销与 recLSN**（课程背景）：[Mohan et al., ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging](https://research.ibm.com/publications/aries-a-transaction-recovery-method-supporting-fine-granularity-locking-and-partial-rollbacks-using-write-ahead-logging)，ACM TODS 1992。
## 26. InnoDB 怎样用索引记录、旧版本和日志处理同一笔库存事务？

本支线把主线三的库存事务搬到 MySQL 的 InnoDB 存储引擎上。前几章用 PostgreSQL 讲清了条件写、隔离级别和 WAL；同样的名字在 InnoDB 里由不同的部件实现：读取走聚簇索引或二级索引，旧版本靠 undo log 重建，锁落在索引记录上，崩溃恢复要协调 redo log 与 binlog 两套日志。读完本章，读者能判断一次 InnoDB 读写会看到哪个版本、锁住哪段索引，以及崩溃后一笔提交是保留还是回滚。

> [!info] 版本基线（核对于 2026-11-12，版本状态核对于 2026-11-16）
> 本章以 MySQL 8.4 LTS 的 InnoDB 为准，并与 2026-04-21 发布的 9.7 LTS 手册交叉核对过快照、锁和 binlog 恢复机制。Innovation 系列已改用日历版本号（例如 2026-10-20 发布的 26.10.0），本章不涉及。8.4 中普通事务的默认隔离级别是 `REPEATABLE READ`，示例仍显式设定；单条独立语句以 `autocommit=1` 执行，需要跨语句持锁的片段显式开启事务。

### 案例：同一笔预留搬到 InnoDB

沿用主线三的案例：`SKU-7`（这里用 `sku_id = 7` 表示）只剩一件，没有 `reserve-demo-208` 的记录；账户 `acct-17`、主体 `user-17` 只是预留的作用域，不划分库存。请求 A 是首次尝试，B 是同一请求的并发重放，二者的幂等键都是 `reserve-demo-208`，指纹都是 `fingerprint-A`，顺序与第一章相同：A 先扣减并提交。

为了看清“旧快照”和“当前值”的区别，这里让 B 多做一步：B 先开一个 `REPEATABLE READ` 事务，用普通 `SELECT` 读了一次库存（看到 1，相当于一次预查），然后 A 才扣减提交。B 之后还能读到 1，但它还能扣吗？

> [!example]- 示例表结构和初始数据
> ~~~sql
> CREATE TABLE inventory (
>     sku_id INT NOT NULL PRIMARY KEY,
>     warehouse_id VARCHAR(16) NOT NULL,
>     available INT NOT NULL CHECK (available >= 0),
>     note VARCHAR(64) NOT NULL
> ) ENGINE = InnoDB;
>
> CREATE INDEX inventory_by_warehouse_stock
>     ON inventory (warehouse_id, available);
>
> CREATE TABLE reservations (
>     account_id VARCHAR(32) NOT NULL,
>     principal_id VARCHAR(32) NOT NULL,
>     idempotency_key VARCHAR(64) NOT NULL,
>     request_fingerprint CHAR(64) NOT NULL,
>     sku_id INT NOT NULL,
>     status VARCHAR(16) NOT NULL,
>     PRIMARY KEY (account_id, principal_id, idempotency_key),
>     FOREIGN KEY (sku_id) REFERENCES inventory(sku_id)
> ) ENGINE = InnoDB;
>
> INSERT INTO inventory VALUES
>     (5,  'W-2', 2, 'point-query neighbor'),
>     (7,  'W-1', 1, 'last unit'),
>     (9,  'W-2', 2, 'point-query neighbor'),
>     (10, 'W-1', 5, 'range example'),
>     (11, 'W-1', 4, 'range example'),
>     (13, 'W-2', 2, 'range example'),
>     (20, 'W-2', 1, 'range example');
> ~~~
>
> `fingerprint-A` 只是符号标签；实际指纹应是规范化业务参数的稳定摘要。

### 一次读取先走哪棵索引？

一次读写会看到什么、锁住什么，先取决于它走哪棵索引。

- InnoDB 的主键组织为 clustered index (聚簇索引)：叶记录保存整行。
- 每个 secondary index (二级索引) 的叶项保存二级键列和该行的主键。查询若还要非索引列，就拿叶项里的主键回聚簇索引取行。

![InnoDB 主键点查与二级索引的候选访问路径](../../engineering-foundations/data/resources/d4-innodb-index-path.svg)

*主键点查直接得到整行；二级索引可以在字段层面覆盖查询，但可见性检查仍可能回聚簇记录。*

`WHERE sku_id = 7` 是完整主键点查，直接找到聚簇索引里的整行。按仓库筛库存时，`WHERE warehouse_id = 'W-1' AND available >= 1` 可能走 `(warehouse_id, available)` 二级索引；若只取 `sku_id, available`，这些列都在二级项里，字段层面可以覆盖。

字段齐全并不保证不回表。二级项已被标记删除，或二级索引页含有快照之后的更新时，InnoDB 要回到聚簇记录核对 MVCC 可见性，需要旧值时再由 undo 重建。本例中，A 把 `SKU-7` 的 `available` 从 1 改成 0 后，二级项 `(W-1, 1, 7)` 被标记删除；B 的旧快照即使只取 `sku_id, available`，也可能按主键回聚簇索引取回旧值。若还要 `note`，无论如何都要回表。索引是否真被使用取决于谓词、统计信息、数据分布和投影列，排查时看 `EXPLAIN`，不要从 `WHERE` 子句猜计划。

### 普通读为什么还能看见已被扣走的库存？

InnoDB 的 consistent read (一致性读) 用 read view (读视图) 决定能看见哪些版本：

- `REPEATABLE READ` 下，同一事务的普通 `SELECT` 都使用**第一次一致性读**建立的快照；`READ COMMITTED` 下每次一致性读都取新快照。
- 别的事务之后改了行，undo log (回滚日志) 保留着重建旧版本所需的信息，普通读据此仍返回旧值。普通读也看得见本事务自己之前的修改。
- 普通 `SELECT` 不锁被读的行，别的事务照样可以更新。

锁定读和写语句不服从这个快照。`SELECT ... FOR UPDATE` 是 current read (当前读)：读最新的已提交版本，并取得排他锁；`UPDATE` 同样按当前版本加锁和判断条件。按固定顺序推演：

~~~sql
-- 会话 B（同一请求的重放）：先建立一致性读视图
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT available FROM inventory WHERE sku_id = 7;
-- 1；这是 B 之后所有普通 SELECT 的快照时点

-- 会话 A（首次尝试）：条件扣减并保存操作记录
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
UPDATE inventory SET available = available - 1
WHERE sku_id = 7 AND available > 0;
-- 影响 1 行，应用才继续 INSERT；影响 0 行则 ROLLBACK
INSERT INTO reservations
    (account_id, principal_id, idempotency_key, request_fingerprint, sku_id, status)
VALUES ('acct-17', 'user-17', 'reserve-demo-208', 'fingerprint-A', 7, 'reserved');
COMMIT;

-- 会话 B 继续原事务
SELECT available FROM inventory WHERE sku_id = 7;
-- 普通一致性读：沿旧读视图，仍是 1
SELECT available FROM inventory WHERE sku_id = 7 FOR UPDATE;
-- 当前读：最新值是 0，并锁住这条索引记录
UPDATE inventory SET available = available - 1
WHERE sku_id = 7 AND available > 0;
-- 影响 0 行：不能按快照里的 1 再扣一次，也不插入记录
ROLLBACK;

-- B 回滚后，用新事务按作用域键回查
START TRANSACTION;
SELECT request_fingerprint, sku_id, status
FROM reservations
WHERE account_id = 'acct-17' AND principal_id = 'user-17'
  AND idempotency_key = 'reserve-demo-208';
COMMIT;
-- 读到 A 的同指纹记录，返回它的当前状态
~~~

![B 的旧快照读、当前锁定读和条件更新分别看到的值](../../engineering-foundations/data/resources/d4-innodb-snapshot-current-read.svg)

*普通读沿旧快照返回 1；`FOR UPDATE` 和 `UPDATE` 检查 A 提交后的当前值 0。*

快照里的 1 只是“普通读仍可见的版本”，不是可以再扣的库存。只要 B 的快照还可能需要这个旧值，对应的 update undo 就不能被清理。B 的 `UPDATE` 影响 0 行，于是回滚并回查，按第一章的契约下结论：同键同指纹返回 A 的结果，同键异指纹返回冲突；回查为空时，同键的竞争事务可能尚未结束，不能据此断定对方失败。若 B 与 A 本是不同的键，B 查不到自己的键，报告本次库存不足。

若 A 尚未提交时 B 就执行 `FOR UPDATE`，B 会等 A 结束：在本例没有其他写入的前提下，A 提交则 B 看到 0，A 回滚则看到 1。

与 PostgreSQL 对照：同样叫 Repeatable Read，PostgreSQL 里 B 的 `UPDATE` 会因为这行在它的快照之后被并发修改而以 `40001` 失败，要整笔重试；InnoDB 的 `UPDATE` 直接读当前版本，结果是影响 0 行。两条路径最后都走到回查，但应用要处理的信号不同，见[快照从什么时候开始？](#%E5%BF%AB%E7%85%A7%E4%BB%8E%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%BC%80%E5%A7%8B%EF%BC%9F)。另外，通常不要在 `REPEATABLE READ` 的同一事务里随意混用快照读和锁定读；这里混用只是为了展示两条读取路径为什么得出不同的值。

### 重复键错误后，事务里还剩什么？

换成第一章“库存还有余量”的变体：B 已在事务里把库存扣了一件，`INSERT` 却撞上复合主键。InnoDB 遇到重复键错误时**通常只回滚这条失败语句**，前面成功的库存 `UPDATE` 仍留在事务里。这与 PostgreSQL 不同，后者报错后整个事务进入失败状态。

所以在 InnoDB 上，应用必须先显式 `ROLLBACK` 整笔尝试，撤销那次扣减，再用新事务按作用域键回查、比较指纹。其他约束或写入错误也一样：整笔回滚，按具体错误返回，不能沿失败路径照常 `COMMIT`。

### 唯一命中和范围扫描为什么锁的范围不同？

上面的 `FOR UPDATE` 和 `UPDATE` 都要加锁。InnoDB 的行锁实际落在**索引记录**上，所以锁住多大范围，取决于语句走哪棵索引、是点查还是范围扫描：

- 完整唯一索引的等值条件只命中一条已存在的记录时，通常只锁这条索引记录，不锁它前面的间隙。
- 排他搜索经由二级索引完成时，InnoDB 还会锁对应的聚簇索引记录。
- 复合唯一索引只给了部分键列，就不是完整唯一命中，可能要扫描并锁住一段索引范围。

下面两个独立示例与库存时序无关，会话 A 先持锁，B 后到：

~~~sql
-- 示例一：完整主键点查，只锁 sku_id = 7 这条记录
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT available FROM inventory WHERE sku_id = 7 FOR UPDATE;
ROLLBACK;

-- 示例二：主键范围扫描
-- 会话 A
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT sku_id FROM inventory FORCE INDEX (PRIMARY)
WHERE sku_id BETWEEN 10 AND 20
FOR UPDATE;
-- 命中 10、11、13、20；A 暂不结束事务

-- 会话 B（autocommit=1 的单条 INSERT）
INSERT INTO inventory VALUES (15, 'W-1', 2, 'insert in protected gap');
-- 等待：15 落在被锁住的间隙里

-- 会话 A
COMMIT;
-- A 释放范围锁后，B 的 INSERT 才继续并提交
~~~

![完整唯一点查的记录锁与范围扫描的 next-key 锁](../../engineering-foundations/data/resources/d4-innodb-lock-interval.svg)

*点查只锁记录 7，6 和 8 仍可插入；范围扫描在记录 20 上的 next-key 锁覆盖 (13, 20]，插入 15 要等待。*

在这个 `REPEATABLE READ` 主键范围里，记录 20 上的 next-key lock (临键锁) 由记录锁加上它前面的 gap lock (间隙锁) 组成，保护 `(13, 20]`。15 落在这个区间，所以 B 要等 A 提交或回滚。间隙锁只阻止冲突的插入，不等于锁了整张表。

`READ COMMITTED` 下的搜索和扫描通常不用间隙锁，但外键检查和重复键检查仍可能用。具体锁范围取决于实际扫描的索引、谓词和计划；遇到锁等待，先用 `EXPLAIN` 确认访问路径，再看 InnoDB 的锁信息。

### 崩溃时 redo 和 undo 各做什么？

前面讲的是运行中的并发；下面看提交途中崩溃后，重启恢复怎样决定事务的去留。两种日志分工不同：

- **redo log (重做日志)** 记录页面修改，用于把尚未写回表空间的变更前滚。它也可能记录了后来被判为未提交的事务的修改。
- **undo log** 一方面供一致性读重建旧版本，另一方面用于撤销未完成的事务。

因此，“redo 重放过页面变化”不等于“这笔业务事务已经提交”。这与[主线 WAL 章](#25.%20%E6%95%B0%E6%8D%AE%E5%BA%93%E7%A1%AE%E8%AE%A4%E6%8F%90%E4%BA%A4%E5%90%8E%E5%B4%A9%E6%BA%83%EF%BC%8C%E9%9D%A0%E4%BB%80%E4%B9%88%E6%81%A2%E5%A4%8D%EF%BC%9F)的结论相同；不同的是，PostgreSQL 靠提交状态让未提交版本不可见，InnoDB 则用 undo 把未完成事务撤回去。

### binlog 与 InnoDB 怎样对同一笔提交达成一致？

开启 binary log (二进制日志，binlog) 后，一笔提交要同时落在两套日志里：InnoDB 的 redo 和服务器层的 binlog。若只落了一边，复制与时间点恢复看到的历史就会与本库不一致。MySQL 用内部的 XA two-phase commit (两阶段提交) 协调二者。这是服务器内部使用的协议，不是应用发出的 `XA` SQL 语句。

本节的前提：binlog 已启用，`innodb_flush_log_at_trx_commit = 1`，`sync_binlog = 1`，且文件系统、控制器和设备如实兑现刷盘。A 这笔事务的提交顺序：

![库存更新、prepare、redo 持久化、binlog 同步与 InnoDB 提交的五步顺序](../../engineering-foundations/data/resources/d4-mysql-binlog-crash-recovery.svg)

*prepare 只进日志缓冲；组提交先持久化 redo，再写并同步 binlog 与 XID，最后引擎提交。*

1. 更新库存、插入预留记录，产生相应的 redo 与 undo。
2. InnoDB `PREPARE`：准备记录追加到 redo 日志缓冲。这一步本身还不表示已持久化。
3. 组提交的刷新阶段先持久化 prepare 记录及此前的 redo。
4. 把完整的事务和 transaction identifier (事务标识，XID) 写入 binlog 并同步到磁盘。到这里，完整有效的提交证据已经持久。
5. InnoDB 完成提交。

图中只追踪 A 这一笔事务；同组的多笔事务可以共用日志刷盘。客户端可能在第 4 步之后、收到响应之前断线，所以客户端是否收到 `COMMIT` 响应不是恢复的依据。

恢复时，redo 先恢复页面和可恢复的事务状态，再以 binlog 里是否有完整、有效、持久的 XID 作决定。从独立初态 `available = 1`、无 `reserve-demo-208` 记录出发，并假定只有 A 修改这件库存：

![崩溃后按是否存在完整有效的持久 XID 完成提交或回滚](../../engineering-foundations/data/resources/d4-mysql-crash-decision.svg)

*有完整有效的持久 XID 就完成提交；没有就用 undo 回滚，库存与预留记录始终一起保留或一起消失。*

| 崩溃时可恢复的提交证据 | 恢复路径 | 恢复后的业务状态 |
|---|---|---|
| binlog 里已有完整、持久、可恢复的事务和 XID（客户端可能没收到响应） | redo 恢复页面修改；事务仍处于 prepared 时，MySQL 通知 InnoDB 完成提交；已完成的提交保持不变 | `available = 0`，预留记录存在；重放查询可确认结果 |
| 没有完整有效的持久 XID，包括第 4 步途中崩溃、未留下有效 XID 的情形 | redo 可先重放页面修改；未提交事务用 undo 回滚；不在有效 XID 集合中的 prepared 事务也回滚 | `available = 1`，没有该预留记录 |

### 恢复结论在什么配置下可信？

上表两条分支都依赖本节开头的刷盘条件：

- `innodb_flush_log_at_trx_commit = 1`：事务提交时写入并刷新 redo。
- `sync_binlog = 1`：binlog 同步到磁盘。
- 设备如实刷盘。设备谎报刷盘、整盘损坏或整个故障域丢失，都要靠备份与复制策略处理。

恢复后的几个运行细节：

- MySQL 可以在 redo 应用完后就接受新连接，未完成事务的回滚可能在后台继续，期间新事务仍可能在这些行上遇到锁等待。
- 时间点恢复仍需要一份合适的备份和其后连续的 binlog；redo 和 undo 不能代替备份。
- 这套 XID 协调是 MySQL 的具体实现，不能因为同样使用预写日志，就把它当成 PostgreSQL 或课程里 ARIES 的同一算法。

### 哪些结论在 InnoDB 上变了，哪些没变？

本支线把主线三的几条结论落到 InnoDB 上：快照里的旧值不能用来扣减，扣减要靠当前读和条件 `UPDATE` 的影响行数；重复键错误只撤销失败语句，整笔回滚必须由应用显式执行；锁范围由访问路径决定；崩溃恢复以 binlog 中完整有效的 XID 决定提交去留。主线接下来转向读取：[空值、外连接和分组会怎样改变一张汇总表的结果？](#27.%20%E7%A9%BA%E5%80%BC%E3%80%81%E5%A4%96%E8%BF%9E%E6%8E%A5%E5%92%8C%E5%88%86%E7%BB%84%E4%BC%9A%E6%80%8E%E6%A0%B7%E6%94%B9%E5%8F%98%E4%B8%80%E5%BC%A0%E6%B1%87%E6%80%BB%E8%A1%A8%E7%9A%84%E7%BB%93%E6%9E%9C%EF%BC%9F)

> [!info]- 来源
> - **版本基线**（版本说明）：MySQL 8.4 LTS 手册与 9.7 手册交叉核对；[Changes in MySQL 9.7.0 (2026-04-21)](https://dev.mysql.com/doc/relnotes/mysql/9.7/en/news-9-7-0.html)；[MySQL 26.10.0 Release Notes](https://dev.mysql.com/doc/relnotes/mysql/26.10/en/news-26-10-0.html)，版本状态核对于 2026-11-16。
> - **聚簇索引存整行、二级索引叶项含二级键与主键**（“一次读取先走哪棵索引？”）：[MySQL 8.4, Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)，§17.6.2.1；**二级项删除标记或页内较新更新时回聚簇核对可见性，覆盖索引只说明字段齐全**：[InnoDB Multi-Versioning](https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html)，§17.3，核对于 2026-11-12。
> - **`CHECK (available >= 0)` 的约束语义**（示例表）：[MySQL 8.4, CHECK Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html)，§15.1.20.6。
> - **REPEATABLE READ 用首次一致性读的快照、READ COMMITTED 每次新快照、普通读与 DML/锁定读看到不同状态**（“普通读为什么还能看见……”）：[MySQL 8.4, Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html)，§17.7.2.3；[Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)，§17.7.2.1（9.7 同节交叉核对）；**`FOR UPDATE` 读最新可用记录并持锁到事务结束**：[Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html)，§17.7.2.4；**undo 支持旧版本重建**：[Undo Logs](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-logs.html)，§17.6.6，核对于 2026-11-12。
> - **PostgreSQL 同名级别的不同行为**（对照）：[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.2。
> - **重复键错误通常只回滚失败语句**（“重复键错误后……”）：[MySQL 8.4, InnoDB Error Handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-error-handling.html)，§17.20.5，核对于 2026-11-12。
> - **记录锁、间隙锁、next-key 锁，完整唯一命中与范围扫描，READ COMMITTED 的例外**（“唯一命中和范围扫描……”）：[MySQL 8.4, InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html)，§17.7.1；**各语句的锁范围、经二级索引的排他搜索锁对应聚簇记录**：[Locks Set by Different SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)，§17.7.3，核对于 2026-11-12。
> - **redo 前滚、不完整事务后台回滚、恢复后提前接受连接**（“崩溃时 redo 和 undo……”“恢复结论……”）：[MySQL 8.4, InnoDB Recovery](https://dev.mysql.com/doc/refman/8.4/en/innodb-recovery.html)，§17.18.2；[Redo Log](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html)，§17.6.5；**用完整备份后的 binlog 做时间点恢复**：[Point-in-Time Recovery Using Binary Log](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-binlog.html)，§9.5.1。
> - **binlog 与 InnoDB 的内部 XA 两阶段提交、恢复时扫描完整 XID 并完成 prepared 事务**（“binlog 与 InnoDB 怎样……”）：[MySQL 8.4, The Binary Log](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html)，§7.4.4（9.7 同节交叉核对）。`prepare()` 先写日志缓冲、组提交刷新阶段先刷引擎日志，依据 MySQL 8.4.13 源码 [sql/binlog.cc](https://github.com/mysql/mysql-server/blob/mysql-8.4.13/sql/binlog.cc) 与 [storage/innobase/handler/ha_innodb.cc](https://github.com/mysql/mysql-server/blob/mysql-8.4.13/storage/innobase/handler/ha_innodb.cc)。**两个刷盘参数与设备假设**：[InnoDB System Variables](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html) 的 `innodb_flush_log_at_trx_commit`；**同组事务共用 binlog 同步**：[Binary Logging Options and Variables](https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html) 的 `binlog_group_commit_sync_delay` 与 `sync_binlog`，核对于 2026-11-12。
## 27. 空值、外连接和分组会怎样改变一张汇总表的结果？

前几章讲写路径：条件写、约束、事务和日志保证数据存得对。从本章起转向读路径的第一件事：一条汇总查询的结果由什么决定。答案往往不在索引或性能，而在三处语义：NULL 参与比较时得到“未知”，外连接会补出并不存在的行，聚合与分组决定每个数字在数什么。本章用一张四位客户、四笔订单的小表，把每条查询的中间行都摆出来手算。

### 案例：四位客户、四笔订单

本章换成一个独立的小例子，因为要逐行手算中间结果，主线三的库存案例行数太少、也没有可分组的维度。表与数据都是合成的教学输入，省略了账户列和授权过滤；语义按 PostgreSQL 18 文档说明。

~~~sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    region      TEXT
);

CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    amount_cents INTEGER,
    status       TEXT NOT NULL
);

INSERT INTO customers VALUES
    (1, 'Ava', 'North'),
    (2, 'Ben', NULL),
    (3, 'Cy',  'South'),
    (4, 'Dia', 'North');

INSERT INTO orders VALUES
    (101, 1, 1200, 'paid'),
    (102, 1,  800, 'pending'),
    (103, 2, NULL, 'paid'),
    (104, 3,  500, 'paid');
~~~

四位客户各带一个特点：Ava 有两笔订单（一笔已付、一笔待付）；Ben 的地区未知，他唯一一笔订单的金额也未知；Cy 有一笔已付订单；Dia 没有订单。目标是一张“每位客户的订单数与金额合计”汇总表。

### 一条查询按什么顺序产生结果？

解释 SQL 结果时，按 logical processing order (逻辑处理顺序) 追踪：

1. `FROM` / `JOIN` 产生行；
2. `WHERE` 逐行筛选；
3. `GROUP BY` 把剩下的行合成组；
4. 聚合函数为每组算出一个值；
5. `HAVING` 逐组筛选；
6. 计算 `SELECT` 列表，再按 `ORDER BY` 排序、按 `LIMIT` 截取。

这是语义顺序，不是执行顺序。PostgreSQL 的计划器可以选择任何物理计划，只要结果与这个顺序算出的相同。本章的每个陷阱，都是某个条件或计数被放到了错误的阶段。

### NULL 参与比较时为什么既不真也不假？

SQL 用 three-valued logic (三值逻辑)：比较的结果可以是 TRUE、FALSE 或 UNKNOWN。NULL 表示“值未知”，所以 `NULL = NULL` 和 `NULL <> 'North'` 都是 UNKNOWN。`WHERE` 只保留结果为 TRUE 的行，UNKNOWN 与 FALSE 一样被丢弃。

~~~sql
SELECT name FROM customers WHERE region = NULL;
-- 空结果：每一行的比较都是 UNKNOWN

SELECT name FROM customers WHERE region IS NULL;
-- Ben

SELECT name FROM customers WHERE region <> 'North';
-- Cy；Ben 的比较是 UNKNOWN，被丢弃
~~~

判断是否为空要写 `IS NULL`。空字符串 `''` 是已知的空文本，`'' IS NULL` 为 FALSE，不能拿它代替 NULL。

### 先决定“未知”算不算进去

NULL 出现在条件或数值里时，查询本身无法替你决定它的业务含义。写谓词或聚合之前，先回答两个问题。

**筛选时，未知值要不要纳入？** 问题若是“不是 North，或地区未知”，就要把 UNKNOWN 显式变成 TRUE：

| region | `<> 'North'` | `IS NULL` | 二者 `OR` | `WHERE` 保留？ |
| --- | --- | --- | --- | --- |
| North | FALSE | FALSE | FALSE | 否 |
| South | TRUE | FALSE | TRUE | 是 |
| NULL（Ben） | UNKNOWN | TRUE | TRUE | 是 |

~~~sql
SELECT name FROM customers
WHERE region <> 'North' OR region IS NULL;
-- Ben, Cy

SELECT name FROM customers
WHERE region IS DISTINCT FROM 'North';
-- Ben, Cy
~~~

`IS DISTINCT FROM` 把 NULL 当作一个可比较的状态：NULL 与 `'North'` 不同，结果为 TRUE；两个 NULL 互不“distinct”。问题若是“地区已知且不是 North”，就只用 `<>`，结果只有 Cy。

**计算时，缺失的数值能不能当成 0？** Ben 那笔订单的金额为 NULL，可能是尚未计价、上游未回填，也可能是数据错误。自动当成 0 会把“未知”和“确实为零”混为一谈。只有报表定义明确规定“没有金额就按零贡献”时，才用 `COALESCE(amount_cents, 0)` 或 `COALESCE(SUM(amount_cents), 0)`；否则保留 NULL，让读者能区分两者。

### 外连接的条件放在 ON 还是 WHERE？

`LEFT JOIN` (左外连接) 先用 `ON` 判断左右两行是否相配；左表某行一个匹配也没有时，仍保留它，并把右表的列补成 NULL。

问题：“列出每位客户及其已付款订单，没有已付款订单的客户也要列出。”付款条件属于“怎样算匹配”，应放进 `ON`：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o
  ON o.customer_id = c.customer_id AND o.status = 'paid'
ORDER BY c.customer_id;
~~~

若先按客户号连接全部订单，再在 `WHERE` 里筛 `o.status = 'paid'`，筛选就发生在补 NULL 之后：

~~~sql
SELECT c.name, o.order_id
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.status = 'paid'
ORDER BY c.customer_id;
~~~

| 条件位置 | 结果行 | 原因 |
| --- | --- | --- |
| `ON` | Ava–101、Ben–103、Cy–104、Dia–NULL（4 行） | Ava 的 102 是 pending，不匹配；Dia 没有已付订单，保留为补 NULL 的一行 |
| `WHERE` | Ava–101、Ben–103、Cy–104（3 行） | Dia 补出的 `o.status` 是 NULL，与 `'paid'` 比较为 UNKNOWN，被 `WHERE` 丢弃 |

条件移到 `WHERE` 后，外连接实际退化成“只保留有已付订单的客户”。对内连接，两种写法结果相同；差别只出现在外连接，因为只有外连接会在 `ON` 与 `WHERE` 之间补出 NULL 行。两条查询的结果都是“连接行”，不是客户去重列表：某位客户出现几次，取决于有几笔订单符合条件。

汇总表要统计 paid 和 pending 两种订单，所以分组查询连接**全部**订单。下面的中间结果有 5 行：

~~~sql
SELECT c.customer_id, c.name, o.order_id, o.amount_cents, o.status
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
ORDER BY c.customer_id, o.order_id;
~~~

| customer_id | name | order_id | amount_cents | status |
| ---: | --- | ---: | ---: | --- |
| 1 | Ava | 101 | 1200 | paid |
| 1 | Ava | 102 | 800 | pending |
| 2 | Ben | 103 | NULL | paid |
| 3 | Cy | 104 | 500 | paid |
| 4 | Dia | NULL | NULL | NULL |

Ava 两行，对应两笔真实订单。Dia 那一行是外连接补出来的，不是订单。下一节的计数都要从这 5 行出发。

### COUNT 和 SUM 各在数什么？

聚合函数的统计对象不同：

- `COUNT(*)` 数行，不看任何列是否为空；
- `COUNT(expr)` 只数 `expr` 非空的行；
- `SUM(expr)` 只加非空输入；一个组里没有任何非空输入时，结果是 NULL，不是 0。

先看原始 `orders` 表：

~~~sql
SELECT COUNT(*)            AS order_rows,
       COUNT(amount_cents) AS priced_orders,
       SUM(amount_cents)   AS total_cents
FROM orders;
-- 4 | 3 | 2500
~~~

四行订单中三笔有金额，已知金额合计 `1200 + 800 + 500 = 2500`。Ben 的 NULL 金额既不计入 `priced_orders`，也不加进总和。

再在上一节的 5 行上按客户分组：

~~~sql
SELECT c.name,
       COUNT(*)              AS joined_rows,
       COUNT(o.order_id)     AS orders,
       COUNT(o.amount_cents) AS priced_orders,
       SUM(o.amount_cents)   AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY c.customer_id;
~~~

| 客户 | 连接行 | 订单数 | 有金额订单 | 合计（分） |
| --- | ---: | ---: | ---: | ---: |
| Ava | 2 | 2 | 2 | 2000 |
| Ben | 1 | 1 | 0 | NULL |
| Cy | 1 | 1 | 1 | 500 |
| Dia | 1 | 0 | 0 | NULL |

Dia 的 `COUNT(*)` 是 1，因为补 NULL 的那一行也是一行；要数真实订单，必须数订单表的非空主键 `o.order_id`，得到 0。Ben 有一笔订单却没有金额，合计为 NULL。Ben 和 Dia 的合计都是 NULL，但原因不同：前者是金额未知，后者是没有订单。报表若要把它们显示为 0，由报表定义决定，见[先决定“未知”算不算进去](#%E5%85%88%E5%86%B3%E5%AE%9A%E2%80%9C%E6%9C%AA%E7%9F%A5%E2%80%9D%E7%AE%97%E4%B8%8D%E7%AE%97%E8%BF%9B%E5%8E%BB)。

还要区分“组里没有非空值”和“根本没有组”。下表的输入都已经过 `WHERE`：

| `WHERE` 之后的输入 | 分组与输出 | `COUNT(*)` / `COUNT(amount_cents)` | `SUM(amount_cents)` |
| --- | --- | ---: | ---: |
| 没有行 | 无 `GROUP BY`：全局聚合仍输出一行 | 0 / 0 | NULL |
| 没有行 | 按 `customer_id` 分组：没有组，没有输出行 | — | — |
| 一笔订单，金额 NULL | 一组 | 1 / 0 | NULL |
| 一笔订单，金额 0 | 一组 | 1 / 1 | 0 |

例如直接查 `orders WHERE customer_id = 4` 时没有输入行；汇总表里 Dia 之所以有组，是 `LEFT JOIN` 先为她造出了一行。

并非所有聚合都忽略 NULL。PostgreSQL 的 `array_agg` 会把 NULL 收进数组；用到其他聚合时，先查它对 NULL 的规则。

### 多连一张子表，金额为什么变大？

本例客户到订单只有一层，每笔订单只进入所属客户的组一次。再连一张“每笔订单可有多行”的子表，同一笔订单就会被复制成多行，这叫 fan-out (扇出)。

单独演示：只取 Ava 的两笔订单，配三条合成的标签关联（它们不属于上面的表）。

~~~sql
WITH ava_orders(order_id, amount_cents) AS (
    VALUES (101, 1200), (102, 800)
), order_tags(order_id, tag) AS (
    VALUES (101, 'priority'), (101, 'gift'), (102, 'gift')
)
SELECT COUNT(o.order_id)          AS joined_order_rows,
       COUNT(DISTINCT o.order_id) AS orders,
       SUM(o.amount_cents)        AS naive_total_cents
FROM ava_orders AS o
JOIN order_tags AS t USING (order_id);
-- 3 | 2 | 3200
~~~

订单 101 有两个标签，它的 1,200 分出现两次；102 有一个标签，800 分出现一次。连接后的和是 `1200 × 2 + 800 = 3200`，真实总额仍是 2,000。

`COUNT(DISTINCT order_id)` 在这里能数回 2 笔订单，但 `SUM(DISTINCT amount_cents)` 不是通用修复：两笔不同订单可能恰好金额相同，去重会把其中一笔吃掉。安全的做法是先把每张子表分别汇总到目标粒度（这里是每位客户至多一行），再连接这些汇总结果。

### WHERE 筛行，HAVING 筛组

`WHERE` 在分组前过滤连接产生的行；`HAVING` 在聚合之后过滤组，所以只有 `HAVING` 能引用 `SUM(...)` 这样的组值。下面只保留合计至少 500 分的客户：

~~~sql
SELECT c.name,
       COUNT(o.order_id)   AS orders,
       SUM(o.amount_cents) AS total_cents
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
HAVING SUM(o.amount_cents) >= 500
ORDER BY c.customer_id;
~~~

| 客户 | orders | total_cents | 保留原因 |
| --- | ---: | ---: | --- |
| Ava | 2 | 2000 | 2000 ≥ 500 |
| Cy | 1 | 500 | 边界值满足 `>=` |

Ben 和 Dia 的合计是 NULL，`NULL >= 500` 为 UNKNOWN，`HAVING` 同样只留 TRUE，两组都被排除。

写一张汇总表时，按这个顺序定条件：先确定统计粒度（每行是客户还是订单），再确定缺失值的业务含义，再确定哪些状态参与；然后把“怎样算匹配”放进 `ON`，把“哪些行参与”放进 `WHERE`，把“哪些组输出”放进 `HAVING`。

> [!info] 实例：方言与兼容开关（PostgreSQL 18、SQLite 3.51，核对于 2026-11-12）
> - PostgreSQL 的 `transform_null_equals` 默认关闭，上文 `region = NULL` 返回空结果就是按默认值说的。打开后，它只把字面量写法 `expr = NULL` 或 `NULL = expr` 改写成 `expr IS NULL`，不影响其他比较；显式写 `IS NULL` 不依赖这个开关。
> - 本章的四客户查询曾在 SQLite 3.51.0 上复现。SQLite 从 3.39.0 起支持 `IS DISTINCT FROM`；更早的版本用 `region <> 'North' OR region IS NULL` 表达同一含义。

### 查询写对之后，它怎样在应用里执行？

本章给出一张汇总查询的检查顺序：NULL 进入比较得 UNKNOWN、被 `WHERE` 和 `HAVING` 丢弃；外连接的匹配条件放 `ON`；按真实主键计数；先汇总子表再连接。查询写对之后，它要在应用里经由 ORM 会话借一条数据库连接才能执行；下一章[ORM 会话怎样借用连接，连接池为什么会耗尽？](#28.%20ORM%20%E4%BC%9A%E8%AF%9D%E6%80%8E%E6%A0%B7%E5%80%9F%E7%94%A8%E8%BF%9E%E6%8E%A5%EF%BC%8C%E8%BF%9E%E6%8E%A5%E6%B1%A0%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E8%80%97%E5%B0%BD%EF%BC%9F)从这里接手，讲连接何时借出、何时归还，以及占得太久时池怎样耗尽。

> [!info]- 来源
> - 逻辑处理阶段（FROM、WHERE、GROUP BY、HAVING 的表转换）与外连接的匹配、补 NULL、`ON` 与 `WHERE` 的差别（含“对内连接无关、对外连接影响很大”）：[PostgreSQL 18, Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html)，§7.2.1–7.2.3；`SELECT` 列表之后再排序：[Sorting Rows](https://www.postgresql.org/docs/18/queries-order.html)，§7.5；物理计划可与逻辑顺序不同：[Planner/Optimizer](https://www.postgresql.org/docs/18/planner-optimizer.html)，§51.5；SQLite 对应语义：[SELECT](https://www.sqlite.org/lang_select.html)，§2。核对于 2026-11-12。
> - NULL 比较得 UNKNOWN、`IS NULL`、`IS DISTINCT FROM`：[PostgreSQL 18, Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html)，§9.2；SQLite 3.39.0 加入 `IS DISTINCT FROM`：[SQLite Release 3.39.0](https://www.sqlite.org/releaselog/3_39_0.html)。核对于 2026-11-12。
> - `transform_null_equals` 默认关闭、只改写与字面量 NULL 的 `=` 比较：[PostgreSQL 18, Version and Platform Compatibility](https://www.postgresql.org/docs/18/runtime-config-compatible.html#GUC-TRANSFORM-NULL-EQUALS)，§19.13.2，核对于 2026-11-12。
> - `COUNT(*)`、`COUNT(expr)`、`SUM` 只处理非空输入、无非空输入时返回 NULL、`array_agg` 收入 NULL：[PostgreSQL 18, Aggregate Functions](https://www.postgresql.org/docs/18/functions-aggregate.html)，§9.21；SQLite [Built-in Aggregate Functions](https://www.sqlite.org/lang_aggfunc.html)。核对于 2026-11-12。
> - 四客户数据、扇出标签与各结果表为本章合成输入，结果已手算并在 SQLite 3.51.0 复现。
## 28. ORM 会话怎样借用连接，连接池为什么会耗尽？

上一章把查询写对了；查询要真正执行，还得在应用里借到一条数据库连接。本章回答三件事：ORM 会话、事务、连接和连接池各管什么；一条连接在什么时刻借出、什么时刻归还；连接被占得太久时池怎样耗尽，事后怎样找到占着连接的人，以及整套部署最多会开多少连接。

本章用 SQLAlchemy 2.0 与 PostgreSQL 18 作实例（文档核对于 2026-11-12）。四种边界在任何 ORM 里都存在，换框架时要重新找到它们各自的结束点；某个框架默认的 Web 请求作用域不是数据库本身的规则。

### 案例：一次报表读取与一个分页导出 worker

同一个服务里有两条访问数据库的路径，都属于账户 `acct-17`：

- **请求读取** `load_report`：HTTP 请求读取报表 42 的少数字段，返回给调用方。
- **分页导出**：后台 worker 按页读取该账户一个季度的活动记录，每页 100 行、最多 12 页。怎样翻页不重不漏留给下一章，本章只看它怎样借还连接。

池配置是教学设定：每个服务进程一个池，`pool_size=8`、`max_overflow=2`、`pool_timeout=2`（秒）。

### 会话、事务、连接与连接池各管什么？

“数据库慢”可能指这四层中任何一层在等。先把它们分开：

| 边界 | 保存什么 | 生命周期 |
| --- | --- | --- |
| ORM 会话（SQLAlchemy `Session`） | 本次工作加载或新增的对象、identity map (身份映射)、待写入的变更 | 一次请求或一页工作；不跨请求共享 |
| 事务 | 一组 SQL 的原子边界：一起提交或一起回滚 | 从开始到 COMMIT 或 ROLLBACK |
| 连接 | 与数据库服务器的一条通信通道，承载事务 | 由池借出给一个事务，事务结束后归还 |
| 连接池（SQLAlchemy `Engine` 内的池） | 可复用的空闲连接，以及同时借出数量的上限 | 每个进程一个，长期存在 |

身份映射保证同一会话里同一主键对应同一个 Python 对象。它不是查询缓存：不会缓存任意查询结果，也不该跨请求共享。

ORM 会话是可变的事务状态，不能被并发的执行者共用：并发线程各用自己的 `Session`，并发的 asyncio Task 各用自己的 `AsyncSession`。不要把某个线程里的会话留给之后的请求。

### 连接在什么时候借出，什么时候归还？

`Engine` 在每个进程里创建一次，长期保存方言、建连方式和这个进程的连接池。会话创建时并不占连接；它第一次真正需要和数据库通信时才向池借一条——通常是执行第一条 SELECT，调用 `Session.connection()` 也会在业务 SQL 之前借出。事务结束时连接归还池。

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 320}}}%%
flowchart TD
    Start[创建局部会话并开始事务] --> Need[第一次需要与数据库通信]
    Need --> Pool{"在 pool_timeout 内<br/>借到连接？"}
    Pool -->|"是：取空闲连接、<br/>按需新建或等到归还"| Q[执行 SQL，在事务内取完结果]
    Pool -->|否：等待超时| Timeout[本次访问失败<br/>业务 SQL 未发出，没有连接可归还]
    Q -->|成功| C[COMMIT]
    Q -->|异常| R[ROLLBACK]
    C --> Close[连接归还池；关闭会话]
    R --> Close
```

几个时点容易混淆：

- **flush 不是提交。** `flush()` 把会话里待写入的变更发成 SQL，但仍在当前事务内。数据库在 INSERT 时生成的主键，flush 后通常已能在对象上读到；事务若随后回滚，这一行仍不存在。
- **flush 出错后，会话要先清理。** 异常从 `session.begin()` 上下文传播出去时，事务自动回滚。若代码捕获异常后还想复用同一个会话，必须先显式回滚，或关闭并丢弃它。
- **close 不是关库。** `Session.close()` 结束未完成的事务并归还连接，数据库服务器不受影响。
- **一个会话可以先后跑多笔事务，**但每笔都有自己的结束点，连接在每笔结束时归还。

### 一次请求怎样有界地读数据库？

下面是 `load_report` 的同步写法。`Report` 已映射；`require_account_permission` 是示意的授权函数，不是 SQLAlchemy API。

~~~python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=8,
    max_overflow=2,
    pool_timeout=2,
)

def load_report(principal_id: str, requested_account_id: str, report_id: int):
    account_id = require_account_permission(
        principal_id, requested_account_id, action="report:read"
    )
    with Session(engine) as session, session.begin():
        report = session.scalar(
            select(Report).where(
                Report.account_id == account_id,
                Report.id == report_id,
            )
        )
        if report is None:
            return None
        return {"id": report.id, "status": report.status, "version": report.version}
~~~

这段代码有四个有意的选择：

1. **先授权，再按可信的账户范围和报表 ID 一起查。** 只按报表 ID 取数会越过账户边界；为什么每次请求都要重新授权，见[服务怎样逐次确认这个主体能对这份资源做这个动作？](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)。
2. **`session.begin()` 给事务一个明确的结束点。** 正常离开时提交，异常离开时回滚，外层 `with Session(...)` 随后关闭会话。只读请求虽然没有写入要提交，显式结束事务仍能让连接在响应发回之前就归还，而不是等到对象被回收。
3. **在提交前复制出响应字段。** SQLAlchemy 默认在提交时让已加载对象的属性过期（`expire_on_commit`）。提交后会话仍打开时读 `report.status`，会再发一次查询、再借一次连接；会话关闭后再读，则可能抛 `DetachedInstanceError`。返回普通字典，就不会把懒加载带出事务边界。
4. **检查 ORM 实际发出的 SQL。** ORM 适合表达实体关系和变更跟踪；批量操作或数据库特有的查询可以直接用参数化 SQL。无论哪种写法，查询计划、唯一约束和隔离语义都由数据库针对实际语句决定。

分页导出 worker 用同样的形状：**每读一页就开一个新会话和一笔短事务**，取完这一页立刻提交并归还连接，再去格式化、压缩和写出。这样连接只在查询期间被占用。代价是各页可能看到不同时间点的数据，下一章讨论这是否可以接受。

### 长时间持有连接怎样让池耗尽？

申请连接的路径是：池里有空闲连接就直接借；没有空闲但借出数仍低于上限，就新建一条；已到上限，调用者就排队等待，最多等 `pool_timeout`。等待超时发生在**借出之前**——业务 SQL 还没发出，也没有连接可归还。

借出之后，到事务结束归还之前，这条连接一直被占着。占用它的不只是 SQL：事务内等待远端 HTTP、边持有事务边发送长响应、排队等别的资源、做与数据库无关的 CPU 工作，都算。

> [!example] 一条连接怎样让 10 ms 的查询在发出之前超时
> 合成配置：`pool_size=1`、`max_overflow=0`、`pool_timeout=2` 秒。
>
> - `t=0`：请求 A 借到唯一的连接，查完报表后，仍在事务内等一个远端服务，远端要 3 秒。
> - `t=0.1`：请求 B 到达并申请连接。它的 SQL 只需 10 ms，但连接被 A 占着，B 开始排队。
> - `t≈2.1`：B 等满 2 秒，池等待超时。B 的 SQL 一次也没执行。
> - `t=3`：A 结束事务并归还连接，B 已经失败。
>
> 修复方法是缩短持有：在发起远端调用之前结束数据库事务，或把远端等待移出事务。调大 `pool_timeout` 只是让 B 等得更久。

### 池超时之后，怎样找到占着连接的人？

超时的请求 B 本身没有借到连接，它的日志里找不到“是谁占着”。要事后定位，需要事先记录借还事件，再按下面的步骤查。

**事先要记录的数据：**

- 每次申请连接：request 或 job attempt 的 ID、进程标识、池标识、申请时刻。计时从可能借出连接的那个调用之前开始。
- 每次成功借出（checkout）与归还（checkin）：连接标识、时刻、借出时的持有者 attempt ID。若要和数据库侧对照，再记下连接对应的 PostgreSQL backend PID。
- 三种失败分开计数：物理建连失败、池等待超时、SQL 执行超时。

**事后定位的步骤：**

1. 在 B 所在的**同一进程、同一个池**里，找出 B 等待期间处于借出状态、尚未归还的所有连接，包括 B 开始等待之前就已借出的连接。
2. 按这些连接的持有者 attempt ID 查应用 trace，看它们借出后在做什么。
3. 需要数据库侧证据时，用 backend PID 关联 `pg_stat_activity`，按下表判断。

| 观察 | 判断 | 下一步 |
| --- | --- | --- |
| 申请到超时很久、借出数达到上限、B 没有任何 SQL 事件 | B 排在池里，没有发出 SQL | 按上面的步骤找持有者 |
| 持有者借出到归还很久；`pg_stat_activity` 显示 `idle in transaction`、`wait_event_type = 'Client'`，且 `xact_start` 很早 | 事务开着，数据库在等客户端发下一条命令；应用可能在事务里等远端或在发送响应 | 对照同一 trace 的远端等待区间，收窄事务 |
| SQL 已开始，执行期间 `wait_event_type = 'Lock'` | SQL 在等数据库锁 | 先找阻塞事务和被锁的资源，不要先扩大池 |
| 等待普遍偏高，但多数连接的借出时长很短，且同时借出已到上限 | 每次占用都短，只是同时到达的请求超过了池的并发 | 限制 API 或 worker 的并发，或在数据库总连接预算内调整池 |

查询慢、N+1 查询、锁等待、事务里调用远端、遗漏结束事务，都会拉长上表中的某一段。两条处理原则：

- **重试会再申请连接。** 池已饱和时不设截止时间地重试只会加长队列；应按请求或 job 的总预算拒绝、延后或失败。
- **池超时不是空结果。** 它是一次失败，不能改写成“没有数据”返回给调用方。

> [!info] 实例：SQLAlchemy 2.0 的池事件
> `PoolEvents.checkout` 只在连接**成功**借出时触发，所以超时的 B 没有 checkout 事件，不能拿 B 的 attempt ID 直接找到 A，只能按上面第 1 步按时间区间找。`PoolEvents.checkin` 标记归还；`PoolEvents.connect` 标记一条物理连接建成，能说明某次 checkout 伴随了新建连接，但单个事件量不出建连耗时——需要时在驱动的物理 connect 调用前后各计一次时。

### 整套部署最多会开多少数据库连接？

每个服务进程通常有自己的 `Engine` 和池，所以连接数要按进程和副本求和：

**连接预算 = 副本数 × 每副本进程数 × (pool_size + max_overflow)**

本例 4 个副本、每副本 3 个服务进程，每个池 `pool_size=8`、`max_overflow=2`：`4 × 3 × (8 + 2) = 120`。这是所有池同时借满时的配置上限，不是当前已打开的物理连接数。API、worker、迁移任务以及其他服务连的是同一个数据库，它们的预算要加在一起，再给管理连接和故障恢复留出余量。缓存故障导致的回源、以及异步管线的执行槽，都要放进这同一份预算。

两个参数的含义要准确：

- `pool_size` 是池可以**保留的空闲连接数**；`max_overflow` 是超过它之后还允许**同时多借出**的连接数。两者之和限制同时借出的峰值。
- 连接池按需建连，创建 `Engine` 时不会预先打开所有连接。
- 连接没有永久的“基数”或“overflow”身份。归还时若空闲队列还有位置，这条连接就被保留，不论它当初是不是额外借出的；队列满了，这次归还的连接才被关闭。

不要跨 `fork` 共享父进程已经打开的连接，两个进程会在同一条套接字上交错收发。做法二选一：在每个子进程里创建 `Engine`；或在子进程初始化时对继承来的 `Engine` 调用 `engine.dispose(close=False)`，丢弃继承的池而不关闭父进程的连接，让子进程建自己的池。

### 连接预算交给容量规划，翻页交给下一章

本章给出连接的借还时点、池耗尽的诊断步骤，以及**连接预算 = 副本 × 进程 × (pool_size + max_overflow)**；主线四的容量规划直接用这个公式，见[一条异步管线能接多少工作，超出时在哪里拒绝？](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)。分页导出 worker 每页一笔短事务、读完即还连接；下一章[怎样无重复、无遗漏地分页读取一个还在变化的集合？](#29.%20%E6%80%8E%E6%A0%B7%E6%97%A0%E9%87%8D%E5%A4%8D%E3%80%81%E6%97%A0%E9%81%97%E6%BC%8F%E5%9C%B0%E5%88%86%E9%A1%B5%E8%AF%BB%E5%8F%96%E4%B8%80%E4%B8%AA%E8%BF%98%E5%9C%A8%E5%8F%98%E5%8C%96%E7%9A%84%E9%9B%86%E5%90%88%EF%BC%9F)回答它怎样翻页才不重不漏、什么时候值得为同一快照长期占住一条连接。

> [!info]- 来源
> - 会话的身份映射、工作单元、flush/commit/rollback、close 归还连接，`Session` 不是查询缓存，`Session`/`AsyncSession` 不能被并发线程或 Task 共享：[SQLAlchemy 2.0, Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)，`What does the Session do?`、`Flushing`、`Closing`、`Is the Session a cache?`、`Is the Session thread-safe?`，核对于 2026-11-12。
> - 提交时属性过期与事务边界：[Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#managing-transactions)；`Session.connection()` 借出连接的时点：[Session API](https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.connection)。核对于 2026-11-12。
> - `QueuePool` 参数、按需建连、`pool_size + max_overflow` 并发上限、fork 后不共享连接与 `dispose(close=False)`：[SQLAlchemy 2.0, Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)，`Connection Pool Configuration`、`QueuePool`、`Using Connection Pools with Multiprocessing or os.fork()`，核对于 2026-11-12。归还时按空闲队列容量决定保留或关闭，对照 [SQLAlchemy 2.0.44 QueuePool 实现](https://github.com/sqlalchemy/sqlalchemy/blob/rel_2_0_44/lib/sqlalchemy/pool/impl.py#L129-L166)。异步 Engine 使用兼容 asyncio 的池实现，本章代码是同步路径。
> - 池事件：[PoolEvents.checkout](https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.PoolEvents.checkout)、[PoolEvents.checkin](https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.PoolEvents.checkin)、[PoolEvents.connect](https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.PoolEvents.connect)；池达到上限后的等待超时：[SQLAlchemy 2.0 Error Messages, QueuePool limit … reached](https://docs.sqlalchemy.org/en/20/errors.html#queuepool-limit-of-size-x-overflow-y-reached-connection-timed-out-timeout-z)。核对于 2026-11-12。
> - `pg_stat_activity` 的 `state`、`xact_start`、`wait_event_type` 字段与 `idle in transaction`、`Client`、`Lock` 等取值：[PostgreSQL 18, The Cumulative Statistics System](https://www.postgresql.org/docs/18/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW)，§27.2.3，核对于 2026-11-12。
> - 池配置、副本与进程数、一槽连接时间线为本章合成设定，数值为手算。
## 29. 怎样无重复、无遗漏地分页读取一个还在变化的集合？

上一章的导出 worker 每页开一笔短事务、读完就归还连接；集合 API 也要把一个长列表分成多次请求返回。两者面对同一个问题：前一页和后一页之间，集合可能有行插入或删除。本章先说明按偏移翻页为什么会漏项，再给出键集分页的构造、集合 API 的分页契约、后台批量读取的页预算，最后讨论什么时候需要所有页来自同一个快照、代价是什么。

### 按偏移翻页为什么会漏项和重复？

`LIMIT 2 OFFSET 2` 的意思是“跳过排序后的前 2 行，再取 2 行”。偏移量记的是**位置**，不是读到了哪一行。位置在两次请求之间会移动：

- 集合里有报表 40、41、42，按 ID 升序、每页 2 条。第一页返回 `[40, 41]`。
- 读第二页之前，40 被删除。集合变成 `[41, 42]`，`OFFSET 2` 跳过这两行，第二页为空：42 被漏掉。
- 反过来，若在读第二页之前，排在前面的位置插入一行，原来的 41 被挤到第 3 位，第二页会再返回一次 41。

只要集合在翻页期间会变，按位置续读就既可能漏也可能重。偏移量还有成本问题：被跳过的行仍要在服务端算出来，偏移越大越慢。修法是记住“读到了哪一行”，从这一行之后继续。

### 键集分页：用最后一行的完整排序键续读

keyset pagination (键集分页) 把上一页最后一行的排序键当作游标，下一页只取排序键**严格大于**游标的行。这正是[有序数据怎样让二分查找和双指针安全排除候选？](#7.%20%E6%9C%89%E5%BA%8F%E6%95%B0%E6%8D%AE%E6%80%8E%E6%A0%B7%E8%AE%A9%E4%BA%8C%E5%88%86%E6%9F%A5%E6%89%BE%E5%92%8C%E5%8F%8C%E6%8C%87%E9%92%88%E5%AE%89%E5%85%A8%E6%8E%92%E9%99%A4%E5%80%99%E9%80%89%EF%BC%9F)里 upper_bound 的数据库版本：下一页从第一个大于游标的位置开始。

以导出 worker 读取 `account_events` 为例，按 `(occurred_at, event_id)` 排序：

~~~sql
SELECT event_id, occurred_at
FROM account_events
WHERE account_id = :account_id
  AND occurred_at >= :start_at AND occurred_at < :end_at
  AND (occurred_at, event_id) > (:after_time, :after_id)   -- 第一页省略这一行
ORDER BY occurred_at, event_id
LIMIT :limit;
~~~

`(occurred_at, event_id) > (:after_time, :after_id)` 是 row value comparison (行值比较)：先比第一列，相等时再比第二列，与 `ORDER BY occurred_at, event_id` 的字典序一致。时间范围取 Q2 的左闭右开区间 `[2026-04-01T00:00:00Z, 2026-07-01T00:00:00Z)`。范围、游标和页大小全部作为参数绑定。

这个构造要成立，排序键必须满足三个条件：

1. **完整排序键唯一。** `occurred_at` 可能重复，所以要接上唯一的 `event_id`。没有唯一的末位键，同一时刻的几行在页边界上没有确定的先后，游标无法区分“读过的”和“没读过的”。
2. **排序键非空。** NULL 在行值比较里得到 UNKNOWN，这些行会从续读条件中消失。
3. **排序键写入后不改。** 某行的键在扫描期间改变，它可能被读两次或一次也读不到。

游标取**本页最后一行按排序键顺序排列的字段**。上面的 SQL 返回列顺序是 `event_id, occurred_at`，构造游标时要按排序键重排成 `(occurred_at, event_id)`，不能把整行原样当游标。

> [!example] 页大小 2 时的游标
> 为了看清边界，把页大小从 100 缩到 2，SQL 不变。三行数据：`(event_id=100, 10:00)`、`(101, 10:00)`、`(102, 10:01)`。
>
> - 第一页返回 100、101，游标是最后一行的 `(10:00, 101)`。
> - 第二页条件 `(occurred_at, event_id) > (10:00, 101)`，只返回 102。这一页 1 行，少于页大小 2，这次查询之后没有更多行。
> - 若游标错取成 `(10:00, 100)`，第二页会返回 101、102，101 被重复读出。

行值比较要求各列同向排序。若排序是 `occurred_at DESC, event_id ASC` 这样混合方向，就要展开成 `occurred_at < :t OR (occurred_at = :t AND event_id > :id)`。查询要能沿索引顺序读取，索引列要覆盖过滤列和排序列，例如 `(account_id, occurred_at, event_id)`；列序怎样从过滤与排序推出，见[约束守住哪些规则，索引又怎样服务读取？](#23.%20%E7%BA%A6%E6%9D%9F%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%A7%84%E5%88%99%EF%BC%8C%E7%B4%A2%E5%BC%95%E5%8F%88%E6%80%8E%E6%A0%B7%E6%9C%8D%E5%8A%A1%E8%AF%BB%E5%8F%96%EF%BC%9F)。

键集分页保证的是：**整个扫描期间一直存在、排序键没变的行，恰好返回一次。** 扫描期间插入的行，落在游标前面就读不到，落在后面就会读到；被删除的行可能已经读过，也可能不再出现。它保证游标一直前进，不保证结果等于某一时刻的集合。需要后者时，见本章最后一节。

### 集合 API 的分页契约

worker 直接查数据库，`LIMIT n` 返回少于 n 行就说明这条语句看到的结果已经取完。API 调用方看不到服务端的查询，只能依据契约判断。一个可依赖的分页契约规定以下几件事：

- **页大小。** 默认值和上限，例如默认 20、最大 100；下面的演示显式传 `limit=2`。
- **确定性排序。** 排序键唯一，同样的筛选每次得到同样的顺序。
- **显式结束信号。** 例如 `next_cursor` 是必返回字段，最后一页返回 JSON `null`。客户端只在看到结束信号时停止。
- **短页不等于结束。** 服务端可能因资源上限少返回几项，但仍给出游标；客户端只凭“这一页不满”就停，会漏项。
- **不透明游标。** 客户端原样传回，不解析也不拼接。续页可以在允许范围内改 `limit`；筛选条件或排序变了，就要从第一页重新开始。
- **游标绑定上下文。** 游标里（或服务端按游标查到的记录里）绑定筛选条件、授权范围、过期时间和最后一行的完整排序键。未知或过期的游标返回错误（例如 `400`），提示调用方从头开始。
- **每页重新授权。** 游标不是授权凭据；权限可能在两页之间被撤销。

下面是报表列表的两页（报表 40、41 及其标题是合成数据）：

~~~http
GET /v1/accounts/acct-17/reports?limit=2 HTTP/1.1
Accept: application/json
~~~

~~~json
{"items":[{"id":40,"title":"Weekly digest"},{"id":41,"title":"Monthly overview"}],"next_cursor":"opaque-token-A"}
~~~

~~~http
GET /v1/accounts/acct-17/reports?limit=2&cursor=opaque-token-A HTTP/1.1
Accept: application/json
~~~

~~~json
{"items":[{"id":42,"title":"Service health"}],"next_cursor":null}
~~~

第一页读到 41 为止，第二页 `[42]` 以 `null` 结束。若 `opaque-token-A` 背后存的是偏移量 2，第一节的删除场景照样会漏掉 42；存的是排序键“id > 41”，删除 40 不影响结果。

结束信号的写法因规范而异。Google AIP-158 规定最后一页的 `next_page_token` 为空字符串，并要求续页时除页大小外的参数与首页一致。选哪种写法都行，关键是写进契约、写进 schema（`next_cursor` 必填且允许 `null`），并作为兼容约束对待：改变结束标志会破坏已有调用方。错误怎样表示、契约怎样演进，见[怎样让调用方可靠地判断 API 的成功、失败和变化？](#37.%20%E6%80%8E%E6%A0%B7%E8%AE%A9%E8%B0%83%E7%94%A8%E6%96%B9%E5%8F%AF%E9%9D%A0%E5%9C%B0%E5%88%A4%E6%96%AD%20API%20%E7%9A%84%E6%88%90%E5%8A%9F%E3%80%81%E5%A4%B1%E8%B4%A5%E5%92%8C%E5%8F%98%E5%8C%96%EF%BC%9F)。前端长列表怎样使用这类游标，是[长列表的成本在哪里，分页和虚拟化各省掉什么？](../../frontend/delivery/long-lists-pagination-and-virtualization.md)的应用。

### 后台批量读取：页预算与“宁可失败不截断”

导出 worker 读的不是无限列表，而是一个有上限的范围：每页 100 行，页数预算 12，服务端硬上限也是 12，最多 1,200 行。参数从已授权、已持久化的任务记录里读取，不从队列消息正文里取。

~~~python
PAGE_SIZE = 100
MAX_PAGE_BUDGET = 12

def iter_job_pages(job_id):
    job = load_authorized_export_job(job_id)   # 从数据库读任务并复查权限
    if not 1 <= job.max_pages <= MAX_PAGE_BUDGET:
        raise InvalidJobBudget(job_id)
    after = None
    for page_number in range(1, job.max_pages + 1):
        rows = load_account_page(               # 每页一个新会话与短事务
            job.account_id, job.start_at, job.end_at,
            after=after, limit=PAGE_SIZE,
        )
        if len(rows) < PAGE_SIZE:
            yield rows
            return                              # 短页：这个范围读完了
        if page_number == job.max_pages:
            raise RangeExceeded(job_id)         # 第 12 页仍满：可能还有更多
        yield rows
        last = rows[-1]
        after = (last.occurred_at, last.event_id)
~~~

规则是：满页继续，短页结束；读到第 12 页仍满 100 行，就以“范围超限”失败。这条规则让**恰好 1,200 行**的范围也失败，因为第 12 页满页时无法知道有没有第 1,201 行。本例宁可保守失败，也不把可能被截断的结果标成完整。若契约要求接受恰好 1,200 行，就要另行探测下一行，例如最后一页多取一行。

失败时，调用方丢弃尚未发布的部分输出；只有迭代正常结束、产物已经写好，任务才算成功。部分输出怎样清理、任务状态怎样提交，属于主线四：worker 只有在持久状态确认成功之后才能确认任务完成，见[任务失败、被取消或 worker 失联后，怎样收尾而不重复也不留孤儿？](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)。

### 每页短事务，还是所有页同一个快照？

PostgreSQL 的 Read Committed 在每条语句开始时取快照。每页一笔短事务，意味着 12 页可能看到 12 个不同时间点的数据：一行在第 3 页读完之后插入到游标前面，后面的页不会回头拾取它。稳定的排序键只保证游标前进，不保证导出等于某一时刻的账户状态。

| 选择 | 得到什么 | 代价 |
| --- | --- | --- |
| 每页短事务（本例默认） | 连接只在每页查询期间占用；读完一页先还连接，再格式化、压缩、写出 | 各页时间点不同；只保证键集分页的“一直存在的行恰好一次” |
| 一笔有界的 Repeatable Read 事务覆盖所有页 | 所有页来自事务开始时的同一快照 | 一条连接从第一页一直占到最后一页结束，包括页与页之间的处理时间；长事务还会推迟旧行版本的清理 |
| 版本化快照（按快照版本或截至时间读取） | 每页仍可短事务，结果对应一个固定版本 | 数据模型要保存版本，读取要带版本条件 |

改成流式读取时尤其要算清第二种代价。若 worker 一直持有数据库游标，边读边把行推给压缩和写出，下游一慢，背压就沿管线传回读取端：读取暂停，但事务和连接还开着。于是“下游慢”直接变成“连接被占更久”，要计入连接池与 worker 执行槽的预算。背压怎样逐段传回源头，见[流怎样把“慢下来”逐段传回源头，中途失败又留下什么？](#20.%20%E6%B5%81%E6%80%8E%E6%A0%B7%E6%8A%8A%E2%80%9C%E6%85%A2%E4%B8%8B%E6%9D%A5%E2%80%9D%E9%80%90%E6%AE%B5%E4%BC%A0%E5%9B%9E%E6%BA%90%E5%A4%B4%EF%BC%8C%E4%B8%AD%E9%80%94%E5%A4%B1%E8%B4%A5%E5%8F%88%E7%95%99%E4%B8%8B%E4%BB%80%E4%B9%88%EF%BC%9F)。确需同一快照时，明确选择有界长事务或版本化快照并核算代价，不要悄悄把短事务分页换成长游标。

跨 HTTP 请求的分页同理：若 API 承诺所有页来自固定快照，后续请求就必须继续读同一个快照，游标要带上快照版本或截至时间。

### 读对之后，重复读取交给缓存

本章给出无重复、无遗漏翻页的三件套：唯一、非空、不变的完整排序键；以最后一行排序键为游标的严格大于续读；带显式结束信号、绑定上下文并每页重新授权的分页契约。后台读取另有页预算和“宁可失败不截断”的完成规则，以及短事务与同一快照之间的明确取舍。读对之后，常被重复读取的展示数据还会放进缓存；下一章[加了缓存之后，读到的数据最多会旧多久？](#30.%20%E5%8A%A0%E4%BA%86%E7%BC%93%E5%AD%98%E4%B9%8B%E5%90%8E%EF%BC%8C%E8%AF%BB%E5%88%B0%E7%9A%84%E6%95%B0%E6%8D%AE%E6%9C%80%E5%A4%9A%E4%BC%9A%E6%97%A7%E5%A4%9A%E4%B9%85%EF%BC%9F)回答缓存值能落后数据库多久、怎样把这个时间写成可证明的上界。

> [!info]- 来源
> - `LIMIT`/`OFFSET` 需要唯一稳定排序，`OFFSET` 跳过的行仍要计算：[PostgreSQL 18, LIMIT and OFFSET](https://www.postgresql.org/docs/18/queries-limit.html)，§7.6；行值比较从左到右逐列比较：[Row Constructor Comparison](https://www.postgresql.org/docs/18/functions-comparisons.html#ROW-WISE-COMPARISON)，§9.25.5。核对于 2026-11-12。
> - 长事务持有的旧快照会阻止清理仍可能对它可见的旧行版本：[PostgreSQL 18, Routine Vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html)，§24.1.2 Recovering Disk Space，核对于 2026-11-26。
> - Read Committed 每条语句取快照、Repeatable Read 在事务内保持同一快照：[PostgreSQL 18, SET TRANSACTION](https://www.postgresql.org/docs/18/sql-set-transaction.html)，`ISOLATION LEVEL`，核对于 2026-11-12。
> - 不透明 page token、除页大小外续页参数须一致、最后一页 `next_page_token` 为空、短页不代表结束：[Google AIP-158, Pagination](https://google.aip.dev/158)，2019-02-18，Guidance，核对于 2026-11-12。
> - 偏移游标在删除后漏项、`[40, 41] → [42] + null` 两页回放、页大小 2 的游标例、12 页 × 100 行预算均为本章合成设定，结果为手算。
## 30. 加了缓存之后，读到的数据最多会旧多久？

上一章把数据库读取做对了；常被重复读取的展示数据还会放进 Redis 这类缓存，以减少数据库查询。缓存命中的值可能落后于数据库，所以这一章要回答：缓存键要包含什么，写入后怎样让缓存失效，为什么设了 TTL 仍可能旧得更久，在什么条件下才能写出“最多旧多久”的上界，以及热门键过期、Redis 故障时怎样不把数据库压垮。

### cache-aside：应用怎样读写缓存

cache-aside (旁路缓存) 由应用自己协调缓存和数据库：

- **读：** 先 `GET` 缓存；命中就用缓存值。未命中就读数据库，再用 `SET key value EX 秒数` 回填，给条目一个 TTL (time to live，存活时间)。
- **写：** 在数据库事务里更新并提交，然后 `DEL` 受影响的缓存键，让下一次读取回源。

数据库始终是权威来源，缓存只是一份可能落后的副本。这决定了哪些读取能走缓存：允许短暂陈旧的展示读取可以；后台任务的状态和结果引用、授权决定、余额这类必须反映当前事实的读取，直接读权威库。

错误也不能混进“未命中”或“不存在”：数据库报错、缓存报错都不能伪装成 `not-found` 返回；缓存回填失败时，已经从数据库读到的结果照常返回，只记录这次回填失败。

### 案例：报表 42 的语言变体

报表 42 属于账户 `acct-17`，展示内容按语言生成，同一种语言的表示可以由多个获准的主体共享。中文表示的缓存键是：

~~~text
report:v1:acct-17:42:zh-CN
~~~

`v1` 是缓存表示格式的版本，之后依次是账户、报表和语言。数据库里报表的版本号会从 v3 更新到 v4。下文的 TTL 取 30 秒；它和各时刻都是教学设定，不是线上推荐值或测量结果。

### 缓存键要覆盖哪些维度？

**规则：缓存键必须覆盖所有会改变这份表示的输入。** 本例的表示随账户、报表、语言和格式版本变化，所以四者都进键。漏掉任一维度，一份表示就会被交给不该拿到它的请求，例如把 `en-US` 的内容返回给要 `zh-CN` 的读者，或把 `acct-17` 的内容返回给别的账户。

缓存键不是授权凭据。每次请求都先验证当前主体能否读取 `acct-17` 的报表 42，再查缓存；命中只省掉数据库读取，不省掉授权检查。为什么每次都要重新授权，见[服务怎样逐次确认这个主体能对这份资源做这个动作？](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)。

共享表示与按主体过滤的表示要区别对待：

- **缓存共享表示（本例）：** 缓存值不含主体专属字段。若有字段要按当前权限隐藏，命中路径与回源路径在返回前应用**同一个**权限投影。
- **缓存已按主体过滤的最终响应：** 键还必须包含主体和权限版本；权限变化时，旧表示要随之失效。

### 能不能缓存“不存在”？

可以，但有前提。只有数据库**明确确认**报表不存在时，才短时缓存一个 `not-found`，这叫 negative caching (负缓存)。查询出错、超时都不是“不存在”。

创建报表时，要删除它所有语言的负缓存键。即使这样，创建之前就已开始的一次未命中读取，仍可能在创建之后才把“不存在”回填进缓存。这和后文“TTL 为什么不是一致性保证”一节的旧值回填是同一种竞态，同样受后文的 D + T 条件约束。

### 写入后先提交还是先删缓存？

**规则：先提交数据库事务，再删除该资源的所有表示键。**

先删后提交会制造确定的旧值：键被删后、事务提交前，并发读者未命中，从数据库读到的仍是 v3（v4 尚未提交，对它不可见），于是把 v3 回填进缓存；事务随后提交 v4，缓存里却留着 v3，直到 TTL 到期。

先提交再删避免了这个顺序，但还要做到两点：

- **删全所有变体。** 删除该账户、该报表的所有语言表示和负缓存键，而不只是当前请求的 `zh-CN`。语言集合有界时可以逐一生成键；存在按主体过滤的表示时，还要覆盖它们。
- **补上两系统之间的缺口。** 数据库提交和 Redis `DEL` 属于两个系统，没有一个事务能让它们原子地一起成功。提交后进程崩溃或 `DEL` 失败，旧条目会一直留到被删除、被淘汰或到期。解决办法是 transactional outbox (事务发件箱，之后简称 outbox)：把“报表 42 已变更”的失效意图和业务更新写在同一个数据库事务里，再由 relay (中继) 反复尝试删除，直到成功。这样失效一定会发生，但 relay 成功之前旧值仍可命中。outbox 的完整机制见[耗时任务怎样被持久受理，并保证一定会被唤醒？](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)。

先提交再删仍挡不住一种情况：删除之前就已读到旧值、删除之后才回填的读取。下一节专门看它。

### TTL 为什么不是一致性保证？

`SET ... EX 30` 每次都会给键设置一个新的 30 秒期限，计时从这次 `SET` 开始，而不是从数据库提交开始。所以 TTL 限制的是“这一条缓存条目从写入起保留多久”，不能单独证明缓存值距数据库最新提交不超过 30 秒。

一条具体的时序（相对秒数）：

1. `t=0`：读者 R 缓存未命中，从数据库读到 v3，还没来得及回填。
2. `t=1`：写者 W 提交 v4，随后 `DEL` 缓存键。键此时为空，但 R 内存里的 v3 收不回来。
3. `t=3`：R 把 v3 写进空键，`EX 30` 从此刻开始计时。
4. 若没有其他写入，键约在 `t=33` 到期。从 `t=1` 提交 v4 算起，旧值 v3 可被命中将近 `(3 + 30) − 1 = 32` 秒。

![在途读取在写入失效后回填旧版本 v3，并从回填时刻重新开始 30 秒 TTL](../../engineering-foundations/data/resources/caching-and-redis-stale-refill-timeline.svg)

把 TTL 改短，只是缩短第 4 步的长度，不改变第 2、3 步的顺序。

### 陈旧上界 D + T 在什么条件下成立？

要把上面这一条时序推广成“任意时序下最多旧多久”，需要两个上限。

**D：提交之后，旧表示仍可能被成功写入缓存的最长时间。** D 必须覆盖所有可能读到旧值并回填的路径：

- 读到旧值的来源，例如提交前开始的事务快照、尚未同步的只读副本；
- 应用里的排队、重试，以及 Redis 接受写入前的延迟；
- 截止时间之后才到达的旧写入：只给请求设截止时间不够，迟到的回填必须被丢弃或被拒绝。

**T：所有可能含旧值的键的期限上限。** 需要同时满足：

- 每次成功写入都设置不超过 T 的 TTL；
- 提交时已经存在的旧条目，剩余 TTL 也不超过 T；
- 命中不续期，不用滑动过期，也不用保留旧期限的写法把某个条目的期限延长到超过 T。

满足这两个条件时：提交后的任何旧回填不晚于提交后 D 发生，再存活至多 T；提交时已有的旧条目至多再存活 T。所以**最后一次旧值命中不晚于提交后 D + T**。这个上界是在同一个正常推进的时钟下、按过期检查的粒度说的，不是计入时钟误差的墙钟承诺。

本例只看 `zh-CN` 一个表示：D = 3 − 1 = 2 秒，T = 30 秒，D + T = 32 秒，与上一节的时序一致。多种语言时，D 与 T 要覆盖所有变体及其回填路径。

反过来，**若无法证明 D 有上限，TTL 不提供任何全程的陈旧上界。** 例如回填可能被无限重试，或者回填来源是延迟没有上限的副本。

### 版本号和 read-your-writes 能保证什么？

给缓存值带上版本号，并拒绝用低版本覆盖高版本，能防止缓存被一次迟到的旧写入**降级**，但不能证明缓存值就是数据库当前版本：

- v4 已提交、失效尚未执行时，缓存里仍是 v3，读者直接命中 v3，版本比较根本没有发生；
- `DEL` 之后键为空，没有 v4 可供比较，迟到的 v3 回填照样成功；
- 版本标记若也放在可淘汰的缓存里，它可能和值一起被淘汰。

read-your-writes (读己之写) 只保证一个请求方看得到**自己**刚提交的写入：请求带上自己刚提交的版本号 v4，读取时绕过缓存，或只接受不低于 v4 的缓存值。它不保证读到别人更新的写入。

要让每个请求都读到当前版本，只有两条路：走一条能看到该提交的权威读取；或在读取时取得一个与数据库提交一致的持久版本门槛，只接受不低于门槛的缓存值。这个门槛必须覆盖空键、淘汰和所有表示变体；门槛若是异步更新的，从提交到门槛更新之间仍有旧值窗口。单靠 Redis 的 TTL 与版本比较做不到这一点。前端查询缓存在保存成功后仍可能读到旧数据，是同一问题的应用，见[服务端数据怎样缓存、刷新和乐观更新，迟到的响应又归谁？](../../frontend/ui-state/server-state-and-optimistic-updates.md)。

### 怎样测量缓存实际有多旧？

缓存条目的写入时刻（fill time）只能量出条目已驻留多久，不是数据年龄：上面的 v3 在 `t=3` 才写入，但它从 `t=1` 起就已过时。Redis 的 `TTL` 命令报告的是剩余寿命，同样不是数据年龄。

要量陈旧度，就抽样比较缓存表示里的版本或 `updated_at` 与权威库的当前值，记录出现差异的时刻和差异持续的时间。只记录 fill time 时，不要把它标成“数据年龄”或“陈旧窗口”。同时监控每个表示变体的失效结果：`DEL` 失败的键会留到被删除、淘汰或到期。

### 热门键过期时，怎样避免回源放大？

一个热门键过期的瞬间，100 个并发请求可能同时未命中、各自查一次数据库，一次正常读取被放大成 100 次。

- **TTL 加随机抖动**能把许多不同键的到期时间错开，但拆不散同一个热门键在同一刻到期的请求。
- **single-flight (单飞请求合并)**：同一进程内的同键请求只让一个调用者回源，其他调用者等它的结果。它不协调其他进程。
- **跨进程的租约锁**：尽力让所有进程只有一个回源者。步骤如下：
  1. `GET` 未命中后，用 `SET lock-key unique-token NX PX lease-ms` 领锁。`NX` 表示只在锁键不存在时写入，`PX` 以毫秒设期限；`unique-token` 每次领取都重新生成。
  2. 领到锁后**再 `GET` 一次缓存**：前一位持有者可能刚回填完并释放了锁。复查命中就直接用（照样按当前权限生成响应），释放自己的锁，不再查库。只有复查仍未命中才回源并回填。
  3. 没领到锁的调用者在请求截止时间内重查缓存；拿不到值就按回源预算等待、失败或回退。
  4. 释放锁必须**原子地**比较 token 并只删除自己的锁。不能先 `GET` 比对、再单独 `DEL`：两步之间租约可能到期、被别人领走，旧持有者会删掉新锁。

这把锁只减少重复工作，不保证正确性：一次加载若超过租约期限，第二个加载者就会开始。需要保证“同一时刻只有一个执行者生效”时，要靠在提交处检查单调递增代次的 fencing (栅栏)，见[怎样保证一个任务同一时刻只由一个 worker 推进？](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)。

### 内存满或 Redis 不可达时怎么办？

**淘汰只是未命中。** Redis 达到内存上限后，按所选 eviction (淘汰) 策略在 TTL 到期前移除键，读者照常未命中、回源。淘汰策略背后的数据结构见[怎样同时按键查找并维护最近使用顺序？](#4.%20%E6%80%8E%E6%A0%B7%E5%90%8C%E6%97%B6%E6%8C%89%E9%94%AE%E6%9F%A5%E6%89%BE%E5%B9%B6%E7%BB%B4%E6%8A%A4%E6%9C%80%E8%BF%91%E4%BD%BF%E7%94%A8%E9%A1%BA%E5%BA%8F%EF%BC%9F)。若配置为 `noeviction`，新写入可能直接报错；这时已从数据库读到的结果照常返回，只记录回填失败。

**不可达不是未命中。** Redis 连接失败时，`GET` 报的是错误。可以回源，但要有上限：在请求截止时间、回源并发上限和数据库连接预算之内；超出就返回暂时不可用。所有进程同时回源会迅速吃满连接池，回源流量要按[ORM 会话怎样借用连接，连接池为什么会耗尽？](#28.%20ORM%20%E4%BC%9A%E8%AF%9D%E6%80%8E%E6%A0%B7%E5%80%9F%E7%94%A8%E8%BF%9E%E6%8E%A5%EF%BC%8C%E8%BF%9E%E6%8E%A5%E6%B1%A0%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E8%80%97%E5%B0%BD%EF%BC%9F)里的连接预算核算。只有确实另存了本地快照、端点允许返回陈旧数据、并且能核对快照年龄时，才考虑在 Redis 故障期间返回快照。

要分辨“缓存缺失”和“数据库变慢”，分开观测命中、未命中、Redis 命令失败、淘汰次数、回源量和连接池等待时间。

> [!info] 实例：本章用到的 Redis 命令（Redis 8.4，核对于 2026-11-12）
> - `SET key value EX 秒数` / `PX 毫秒数` 设期限；成功的 `SET` 默认丢弃旧 TTL。Redis 6.0 起的 `KEEPTTL` 选项保留旧期限——这正是 T 的条件要防的“保留超过 T 的旧期限”。
> - `NX` 只在键不存在时写入；`TTL` 返回剩余寿命。
> - 比较 token 后删除：Redis 8.4 新增 `DELEX lock-key IFEQ unique-token`；更早的版本用 Lua 脚本在服务端原子完成比较与删除。
> - Redis 8.4 源码在 `now > when` 时才判定键过期，所以恰好在到期毫秒仍可能读到值；上文因此写“约 `t=33` 到期”。

### 缓存挡不住写入与数据总量

本章给出缓存的四条规则：键覆盖表示的全部影响因素，且命中不替代授权；先提交再删全所有变体，用 outbox 让失效可重试；陈旧上界是 D + T，并且只有 D 有界时才成立；版本比较只防降级，read-your-writes 只保证自己的写。缓存挡掉了重复读取，但写入和数据总量仍落在一个数据库上。下一章[单库接近上限时，怎样选分片键并区分总容量不足与热点？](#31.%20%E5%8D%95%E5%BA%93%E6%8E%A5%E8%BF%91%E4%B8%8A%E9%99%90%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E9%80%89%E5%88%86%E7%89%87%E9%94%AE%E5%B9%B6%E5%8C%BA%E5%88%86%E6%80%BB%E5%AE%B9%E9%87%8F%E4%B8%8D%E8%B6%B3%E4%B8%8E%E7%83%AD%E7%82%B9%EF%BC%9F)回答单库到顶时怎样切分。

> [!info]- 来源
> - cache-aside 的未命中回源、回填、写后失效、TTL 与热门键并发回源：[Redis, Cache-aside](https://redis.io/docs/latest/develop/use-cases/cache-aside/)，`Why the problem is hard`、`How Redis supports the solution`，核对于 2026-11-12。在途旧值回填竞态与 D + T 推导是本章按明确事件顺序推出的应用条件，不是 Redis 的承诺。
> - `SET` 的 `EX`、`PX`、`NX`、`KEEPTTL`（6.0 起）与默认丢弃旧 TTL：[Redis, SET](https://redis.io/docs/latest/commands/set/)；删除与剩余寿命：[DEL](https://redis.io/docs/latest/commands/del/)、[TTL](https://redis.io/docs/latest/commands/ttl/)。核对于 2026-11-12。
> - 内存上限、淘汰策略、`noeviction` 下拒绝写入、用 `INFO` 查看淘汰与拒绝计数：[Redis, Key eviction](https://redis.io/docs/latest/develop/reference/eviction/)，`Using maxmemory`、`Eviction policies`、`Using the INFO command`，核对于 2026-11-12。
> - 单实例 `SET ... NX PX` 锁、唯一 token、比较 token 后释放、Redis 8.4 的 `DELEX ... IFEQ` 与更早版本的 Lua 做法：[Redis, Distributed Locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)，`Correct Implementation with a Single Instance`，核对于 2026-11-12。“领锁后复查缓存”是本章增加的应用步骤，不是锁命令语义。
> - 过期判定 `now > when`：[Redis 8.4.0 `keyIsExpired`](https://github.com/redis/redis/blob/8.4.0/src/db.c#L2475-L2483)。
> - D 要覆盖的旧值来源：旧事务快照在 Repeatable Read 下继续看见事务开始前的版本，[PostgreSQL 18, Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2；副本未同步时回源可能填入旧值，[Microsoft, Caching guidance](https://learn.microsoft.com/en-us/azure/architecture/best-practices/caching#caching-and-eventual-consistency)，`Caching and eventual consistency`。核对于 2026-11-12。
> - 在途旧回填覆盖新值、版本记录随键淘汰而丢失：[Meta, Cache made consistent](https://engineering.fb.com/2022/06/08/core-infra/cache-made-consistent/)，开头的失效竞态与 version field 反例，2022-06-08。它支持“版本比较不等于最新读取”，不提供本例的强一致协议。
> - 缓存失效与数据库更新的双写缺口、outbox 把两者写进同一事务并处理重复：[AWS, Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)，`Intent`、`Motivation`、`Issues and considerations`，核对于 2026-11-12。
> - 缓存键、TTL 30 秒、v3/v4 与时间线数值为本章合成设定，32 秒为手算，未连接 Redis 实测。
## 31. 单库接近上限时，怎样选分片键并区分总容量不足与热点？

前几章的事务、约束和缓存都假设数据在一个数据库里。单库的安全容量或维护窗口不够用时，就要把数据切到多个库。本章回答两类问题：怎样选分片键，切开之后哪些保证还在、哪些操作变贵；以及扩容前怎样判断瓶颈到底是总容量不足、负载分布偏斜，还是一个热键。把一个账户真正搬到新库而不出现两个写入者，留给本章的支线。

### 案例：一个按账户分库的报表服务

一个合成的报表服务按账户保存报表、作业状态和幂等结果。账户 `acct-17` 的数据在节点 B 上。B 的写负载已超过安全目标，团队考虑加一个节点 D，并把部分账户搬过去。下文的节点、哈希值和负载数字都是为手算选的教学输入。

### 分片键决定哪些操作仍是本地事务

shard key (分片键) 决定一行数据住在哪个库。它同时决定三件事：

- **路由：** 带着分片键的请求能直接找到目标库。
- **事务边界：** 只有同一个库里的写入能由一笔本地事务原子提交。
- **唯一性范围：** 唯一约束只在一个库内裁决。

本例选 `account_id`。按账户列出报表、查询幂等结果、改作业状态都能直接定位；报表 42、相关作业和该账户的操作记录在同一个库里，账户内的一组更新仍由一笔本地事务提交。主线前几章的条件写和唯一裁决因此在账户内照常成立。

唯一性要按新范围重写。作业编号只需在账户内唯一时，约束要带上分片键：`UNIQUE (account_id, job_id)`。若要求跨所有账户全局唯一，就需要可验证的全局命名空间、独立的 ID 分配器，或调用方提供的全局唯一键。每个库各有一条 `UNIQUE (job_id)`，只保证**单库内**唯一，裁决不了两个库之间的冲突。

### 逻辑分片、物理节点与复制各解决什么？

三个概念经常被混用：

| 概念 | 是什么 | 改变它意味着什么 |
| --- | --- | --- |
| logical shard (逻辑分片) | 按分片键划出的一段数据范围，及其当前的写所有者 | 重映射：某些账户换到另一个逻辑分片 |
| physical node (物理节点) | 实际承载数据库实例的机器或服务端点 | 一个节点可以承载多个逻辑分片；换主实例不改变账户归属 |
| replication (复制) | 同一份数据的冗余副本 | 提供故障切换和读扩展，不分摊写入 |

分片把不同键的主数据分开，扩展可承载的数据量和不同键的写入总量。复制在单写者拓扑下只增加读副本：再多的只读副本，也不会把同一个热账户的写入摊到更多主实例上。多主或基于共识的系统有各自的写入与冲突协议，换用它们也不能省掉支线里那种所有权约定。

### 分片之后，哪些请求变贵，哪些保证消失？

**不带分片键的请求。** 请求只带报表 ID 时，服务要先通过资源目录查出它属于哪个账户，或者让 ID 本身带上可验证的路由信息。否则只能 scatter-gather (散播后汇总)：把请求发给所有分片再合并结果，尾延迟和失败概率都随参与分片数增长。

**路由不是授权。** 路由只回答“数据在哪”，不回答“这个主体能不能碰它”。服务仍要根据认证主体和资源关系验证对 `acct-17` 报表 42 的权限；路由目录不是授权名单，路由缓存命中也不能跳过授权。

**跨分片写没有单一 COMMIT。** 一条 SQL `COMMIT` 只覆盖一个数据库。要原子地改两个库，就得引入协调：

- two-phase commit (两阶段提交，2PC)：协调者先让各参与者 prepare 并投票，再统一下达提交或回滚。投了赞成票、进入 prepared 状态的参与者会一直持有锁，直到获知全局决定；协调者此时故障，参与者就只能等。
- CAP 定理给出更根本的边界：网络分区时，系统不能同时保证 linearizability (线性一致性) 与 availability (可用性，即每个非故障节点收到的请求最终都得到响应)。

2PC 与 CAP 都不能替代单库内的约束、隔离和日志恢复，它们只说明跨节点时还剩什么。实际可选的路有三条：用分片键把必须一起提交的数据放在同一个库（首选）；选用有明确故障恢复语义的协调事务；或者重新划分业务边界，改成可恢复的分步流程，例如由 outbox 驱动后续步骤（见[耗时任务怎样被持久受理，并保证一定会被唤醒？](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)）。

### 加节点时要搬多少数据？

映射函数决定扩容时多少键换库。用一个可手算的合成映射比较：设 `h(acct-n) = n`，这不是生产哈希函数，只为让算术透明。

**固定取模。** 三个分片时余数 0/1/2 对应 A/B/C；加入 D 后按 4 取模，余数 0/1/2/3 对应 A/B/C/D。

| 账户 | `h` | `% 3` | `% 4` |
| --- | ---: | --- | --- |
| `acct-17` | 17 | 2 → C | 1 → B |
| `acct-20` | 20 | 2 → C | 0 → A |
| `acct-21` | 21 | 0 → A | 1 → B |
| `acct-35` | 35 | 2 → C | 3 → D |
| `acct-49` | 49 | 1 → B | 1 → B |
| `acct-52` | 52 | 1 → B | 0 → A |
| `acct-65` | 65 | 2 → C | 1 → B |
| `acct-70` | 70 | 1 → B | 2 → C |
| `acct-82` | 82 | 1 → B | 2 → C |

九个键里八个换了目标，只有 `acct-49` 的余数不变。取模容易计算，适合分片数长期稳定、或能整体重建数据的系统；代价是分片数一变，大批键重新映射。

**一致性哈希。** consistent hashing (一致性哈希) 把节点和键都放到一个环形哈希空间上，键归顺时针方向遇到的第一个节点，即每个节点负责 `(前一个 token, 自己的 token]`。下图用 0–99 的玩具环（原有 token A=0、B=33、C=66）回答：加入 D=20 后，同一组键里哪些换了节点。

![0–99 环上加入 D=20 后，D 只接管 (0, 20]，键 17 与 20 从 B 改归 D，其余键归属不变；取模从 %3 改为 %4 时九个键中八个换目标](resources/sharding-hash-ring-add-node.svg)

只有 17 与 20 搬家，2/9；同一组键在取模下搬 8/9。本例的放置采用这个环，所以 `acct-17` 现在在 B 上，加入 D 后它落进 D 的区间（取模表只用来比较规则）。这个比例只说明映射规则的差别，不是负载实测：实际搬多少数据还取决于键的真实分布和每个键的数据量。

节点只有少数 token 时，各自负责的区间可能很不均匀。virtual node (虚拟节点) 让一个物理节点在环上占多个 token，通常能缩小区间大小的偏差，但不能保证真实数据量和请求负载均匀。环给出的只是候选位置，不会自动切换账户的权威路由；数据搬完并验证之后，才能逐账户改路由，见支线。

### 哈希分片还是范围分区？

| 方式 | 擅长 | 代价 |
| --- | --- | --- |
| 哈希分片 | 按离散键点查；把许多键均匀摊开 | 打散键的范围局部性，范围扫描要访问多个分片 |
| range partitioning (范围分区) | 范围扫描、局部排序、按范围归档 | 递增的时间戳或编号会集中写到当前边界所在的分区 |

不能只问哪种函数“更均匀”。先看请求是否都带分片键、事务需要覆盖什么范围、有没有排序和范围扫描的需求、实际热点在哪，再选能保留主要访问路径的映射。

### 该重平衡、加节点，还是拆开热键？

扩容前分开看三个量：**所有分片的总负载、每个分片的负载、每个分片里最重的单个键的负载。** 平均值会掩盖偏斜；数据行数也不等于资源消耗，生成报表的写入、状态轮询和索引维护代价各不相同。

下面只用写工作量做一笔合成算例。`1 work` 是一个等成本的标准化写请求；经压测，每个物理节点暂以 `1,200 work/s` 作为安全目标。

| 物理节点 | 当前写工作量 | 其中 `acct-17` | 把 `acct-17` 移到新节点 D 后 |
| --- | ---: | ---: | ---: |
| A | 700 work/s | — | 700 work/s |
| B | 1,600 work/s | 1,000 work/s | 600 work/s |
| C | 700 work/s | — | 700 work/s |
| D（新） | — | — | 1,000 work/s |
| 合计 | 3,000 work/s | — | 3,000 work/s |

搬走 `acct-17` 后，总量仍是 `700 + 600 + 700 + 1,000 = 3,000 work/s`，峰值从 1,600 降到 1,000，四个节点都低于 1,200。扩容在这里解决的是**分布偏斜**，没有减少任何请求的成本，也没有减少总工作量。若 D 的安全目标只有 900 work/s，整个账户搬过去仍然超限，就要换容量更大的目标，或者进一步拆分账户。

按观测到的形态判断：

| 形态 | 更可能的瓶颈 | 下一步 |
| --- | --- | --- |
| 多数分片都接近 CPU、I/O、连接或存储的安全上限 | 总容量不足，或单请求成本太高 | 先降请求和索引成本，再加节点或分片；只读副本只帮助允许读副本的流量 |
| 只有一两个分片超限，过热分散在很多键上 | 分配不均，或分区边界不合适 | 移动部分逻辑分片或范围；搬前确认目标在同一资源口径下有余量 |
| 一个账户、设备或时间键独占大部分工作量 | 单热键：加节点、虚拟节点都只是把整个键送给另一个所有者 | 能否在实体内部再按报表或事件切分；不能就限流、缓存、排队或给它独立容量 |
| 存储占满但请求量不高，体积集中在少数账户或范围 | 数据放置或保留策略 | 按字节数、索引体积和增长率估算；必要时归档或调整分区，不用 QPS 代替容量依据 |

单热键有一个拆不掉的上限：一个账户只有一个写所有者。给热账户单独一个分片只能隔离它对邻居的影响，不能让它的写入超过单个所有者的能力。要拆账户内部的键，就得重新决定账户级汇总、幂等唯一性、外键和跨子键事务由谁协调。

生产中的判断依据要按时间窗收集：每个物理节点和逻辑分片的 CPU、I/O、连接数、事务延迟、读写量、数据体积，以及 p95/p99 延迟、限流和锁等待；再用目标负载和安全余量压测，而不是把某一次峰值直接当成容量常数。

### 搬走 acct-17，再进入服务之间的请求

本章给出分片设计的三个结论：分片键同时决定路由、事务边界和唯一性范围；跨分片写没有单一 COMMIT；扩容前按总负载、分片负载、单键负载区分总容量不足、分布偏斜和单热键。算例的结论是把 `acct-17` 从 B 搬到 D。怎样搬才能保证任一时刻只有一个库接受它的写入，见本章支线[把一个账户搬到新分片时，怎样保证任一时刻只有一个写入者？](#32.%20%E6%8A%8A%E4%B8%80%E4%B8%AA%E8%B4%A6%E6%88%B7%E6%90%AC%E5%88%B0%E6%96%B0%E5%88%86%E7%89%87%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%BB%BB%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E6%9C%89%E4%B8%80%E4%B8%AA%E5%86%99%E5%85%A5%E8%80%85%EF%BC%9F)。

主线三到此结束。它交给主线四的是条件更新、唯一裁决和事务边界：服务之间交换请求时，幂等、任务领取和栅栏都建立在它们之上。主线四从[一次 HTTP 请求怎样从浏览器到达服务，又带回什么？](#33.%20%E4%B8%80%E6%AC%A1%20HTTP%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%B5%8F%E8%A7%88%E5%99%A8%E5%88%B0%E8%BE%BE%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%8F%88%E5%B8%A6%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)开始。

> [!info]- 来源
> - 一致性哈希的环分配与虚拟节点改善负载偏斜：[DeCandia 等, Dynamo: Amazon’s Highly Available Key-value Store, SOSP 2007](https://cdn.amazon.science/ac/1d/eb50c4064c538c8ac440ce6a1d91/dynamo-amazons-highly-available-key-value-store.pdf)，§4.2，pp. 199–200。本章玩具环的区间 `(前一 token, 当前 token]` 是为手算选择的边界约定；Dynamo 以“位置大于键的第一个节点”定义归属，正好落在 token 上的键可能归属不同。九个键点为合成输入。
> - 逻辑分片与物理数据库服务器、分片与复制是不同维度：[Vitess 24.0, Sharding](https://vitess.io/docs/24.0/reference/features/sharding/)，核对于 2026-11-13。
> - 2PC 中 prepared 事务持续持锁，需由外部协调器最终发出 `COMMIT PREPARED` 或 `ROLLBACK PREPARED`：[PostgreSQL 18, PREPARE TRANSACTION](https://www.postgresql.org/docs/18/sql-prepare-transaction.html)，Description 与 Caution，核对于 2026-11-12。CAP 的形式化与证明：[Gilbert and Lynch, Brewer’s conjecture and the feasibility of consistent, available, partition-tolerant web services](https://www.cs.princeton.edu/courses/archive/spring24/cos418/papers/cap.pdf)。
> - 访问集中于少数分区键会形成热点，热点容量不能由总吞吐推断：[Amazon DynamoDB, Designing partition keys to distribute your workload](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-uniform-load.html)，核对于 2026-11-13。只佐证分区键偏斜的通用现象，不套用 DynamoDB 的具体容量限制。
> - 取模与环的映射表、work/s 负载表为本章合成数据，数值为手算，不是产品容量或实测。
## 32. 把一个账户搬到新分片时，怎样保证任一时刻只有一个写入者？

上一章的容量算例决定把 `acct-17` 从节点 B 搬到新节点 D。搬迁期间 B 和 D 都存着这个账户的数据，难点是任何时刻都只能有一个库接受它的业务写入：两个库同时开放，同一个幂等键可能在两边各生效一次，两边的数据从此分叉。本章给出一套教学用的搬迁协议，说明每一步保证什么、出错时能不能退回旧库。

它用的是[栅栏原理](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)：给写权限一个只增不减的代次，并在**提交处**检查代次，旧代次的写入就无法生效。原理的权威说明在主线四的任务领取章；这里只讲分片搬迁特有的部分——数据怎样无缝追平、源端怎样冻结、目录怎样切换、何时可以回退。

### 搬迁的四步与两个要分开的问题

协议把两个问题分开管理：**数据副本什么时候完整**，与**谁获准写入**。前者靠快照加变更流追平并验证，后者靠所有权记录与代次。四步如下：

1. 以一致快照 S 为起点，把 `acct-17` 的数据回填到 D。
2. 捕获 S 之后 B 上提交的所有变更，按顺序应用到 D，让 D 追平。
3. 在 B 的所有权记录上冻结写入口，并在日志里留下屏障位置 L。
4. D 应用到 L 并通过校验后，用条件更新把路由目录切到新代次，再开放 D。

整个过程没有让应用同时向 B 和 D 双写。真正的互斥来自每个写入口都在事务里检查所有权，而不是路由缓存更新得够快。

### 所有权记录：owner、epoch 与本地状态

**路由目录**为每个账户记录权威的 owner (写所有者) 和单调递增的 epoch (路由代次)，写作 `owner/epoch`：`B/7` 表示 owner 为 B、代次为 7。请求携带目标分片和代次；路由缓存只是位置提示，不能自行授权。

**每个分片**还有一张可在事务里加锁的本地所有权表：

~~~text
account_ownership(account_id, owner_shard, epoch, candidate_id, state)
~~~

本章用到的名词：

- **prepare (准备候选)**：在目标分片插入一行 `closed` 状态的所有权记录，为某个 owner/epoch 预留位置，但还不接受业务写。
- **`candidate_id`**：每次 prepare 生成的不可变标识，用来区分同一 owner/epoch 下的不同候选，例如 `C8`。
- **目录 CAS**：compare-and-swap (比较并交换)。只有目录当前值仍等于预期旧值（如 `B/7`）时才写入新值，否则失败；并发的几次切换因此只有一个成功。
- **`decision_id`**：CAS 成功时一并写入目录的决策标识，例如 `K8`。目标分片只有拿到与之匹配的决策才能开门。

本地状态只有三种：`open` 接受业务写，`closed` 是已准备、未开放的候选，`frozen` 是这一代的终态。下图回答一行所有权记录能怎样变化；图中没有的转换都不允许，例如 `frozen` 回到 `open`，或 `open` 退回 `closed`。

```mermaid
stateDiagram-v2
    direction TB
    state "进入本代之前" as Before {
        state "此分片无该账户的行" as None
        state "较低代次 frozen" as LowFrozen
    }
    state "closed：已准备的候选<br/>(owner, epoch, candidate_id)" as Closed
    state "open：接受业务写" as Open
    state "frozen：本代终态" as Frozen

    None --> Open: 首次初始化<br/>权威目录唯一指定初始 owner
    None --> Closed: prepare<br/>由当前权威代次授权
    LowFrozen --> Closed: prepare<br/>新 epoch 高于持久下限
    Closed --> Closed: 相同 prepare 重试<br/>读回同一候选
    Closed --> Open: 开门<br/>匹配目录 CAS 写入的 decision_id
    Closed --> Frozen: 同行条件更新<br/>（如已确认 CAS 落败）
    Open --> Frozen: 同行条件更新<br/>等持锁业务事务结束
    note right of Frozen
        不再回到 closed 或 open；
        下一次 prepare 写入更高 epoch，
        这一行就成为上方的“较低代次 frozen”
    end note
```

图上的边还有几条容易漏掉的条件：

- 首次初始化只适用于此分片从未有过该账户的行；后续迁移不能伪装成首次初始化。
- 开门命令必须同时匹配账户、owner、epoch、`candidate_id` 和目录里的 `decision_id`。只看到 owner/epoch 相同不构成授权。
- 冻结与业务写作用在同一行上，所以原为 `open` 时，冻结要等已持锁的业务事务结束才完成（见下一节）。

除了“同代 `frozen` 不回退”，还有两条不变量让旧代次无法复活：

- **行不可删，epoch 不复用。** 曾经建过的行（或等价的代次下限）要保留；任何可能被提升为写主的副本都必须带着它，或在提升后、对外开放前重新从权威端核对。
- **未发布的 `closed` 候选不能被新 prepare 随意覆盖。** 先从权威目录确认它已在 CAS 竞争中不可逆地落败，再把该行冻结，才能准备更高代次。目录离开任何已发布的 owner/epoch 之前，该 owner 必须已在本地冻结且冻结已持久。

#### 每笔业务写怎样检查所有权

每笔业务事务先在本地所有权行上取得一个**与其他业务写兼容、但与冻结更新冲突**的锁，检查状态，再在**同一个事务里**写业务数据。检查和写入若分在两个事务里，冻结就可能插进两者之间。以 PostgreSQL 18 为例（应用伪码，查询与更新必须在同一连接、同一事务）：

```text
BEGIN ISOLATION LEVEL READ COMMITTED
row = SELECT owner_shard, epoch, state
      FROM account_ownership
      WHERE account_id = $1
      FOR SHARE
if row_count != 1 or row != (B, 7, open):
    ROLLBACK
    reject, or refresh the authoritative route
else:
    UPDATE reports SET status = $2
     WHERE account_id = $1 AND report_id = $3
    if this transaction creates a new business effect:
        INSERT local_business_commits(account_id, owner, epoch, operation_key)
        VALUES ($1, 'B', 7, $4)
    COMMIT
```

`FOR SHARE` 让多笔业务事务可以同时持锁，而冻结用的 `UPDATE` 要等它们全部结束。在 Read Committed 下，等到并发更新提交后，加锁语句返回的是更新后的行版本，所以应用必须在拿到锁之后再检查状态。若改用互斥锁，账户内所有写入都会被串行化，本协议不需要付这个代价。

`local_business_commits` 是本协议的**本地提交账本**：每产生一个新的业务效果，就在同一个事务里记一行 `(账户, 本地 owner, epoch, 操作键)`。重复请求若只是读到已有的幂等结果，不算新提交。账本不随业务数据复制到目标；它只记本地产生的效果，回退时用来判断目标是否已经被写过。

![写请求先解析账户并授权，再按 owner/epoch 路由，由分片内所有权行决定接受、刷新或暂停](../../engineering-foundations/data/resources/i7-sharding-request-route.svg)

### 快照 S 与变更流：怎样无缝追平

consistent snapshot (一致快照) S 包含源端截至 S 的一致数据；从同一个 S 开始，源端之后提交的所有变更都被保留下来。D 在验收前是候选副本，不接受应用的业务写。

![快照 S 提供回填基线，S 之后的变更在基线完成后按源端顺序重放到 D](../../engineering-foundations/data/resources/i7-snapshot-cdc.svg)

要做到无缝，需要满足三条：

1. **没有复制缺口。** 快照 S 和 change data capture (变更数据捕获，CDC) 的起点必须属于同一份复制约定。源端在快照期间继续服务时，S 之后的变更要可靠保留到目标追上；复制槽、日志保留空间或 CDC 缓冲一旦丢了必要的区间，“后来重新连上”不等于没有缺口，必须重建快照或重新建立起点。还要监控消费积压和源端剩余空间：复制槽会阻止尚需的日志被清理，长期不推进会占满磁盘。
2. **旧快照不能覆盖较新的变更。** 本例先完成 `acct-17` 在 S 中的基线回填，再从 S 按源端事务顺序应用变更。若为缩短时间而并行回填和重放，就必须用行版本或日志位置证明旧快照行不会晚于新变更写入目标；两个任务同时跑本身不构成顺序保证。
3. **复制完整的业务效果。** CDC 要包含该账户的插入、更新和删除，保留稳定主键和事务顺序，每条变更都带有能定位到账户的键列。重复投递按源位置或等价的变更标识去重。所有权行属于迁移控制，不当成普通业务表复制；D 的候选所有权由切换流程单独准备。

追平的日志位置里可能夹着别的账户的事件，但这次只应用 `acct-17` 的数据。这要求应用的事务以账户为边界：若一笔源事务原子地改了多个账户，协议把它拆开应用后，那笔事务的原子性就丢了，需要重新设计事务边界或改用能保留原子性的协调方案。

> [!info] 实例：PostgreSQL 18 的逻辑解码（核对于 2026-11-13）
> logical decoding (逻辑解码) 的复制槽可以导出一个与变更流衔接的一致快照；日志位置用 LSN (log sequence number，日志序列号) 表示，是 WAL 中的位置。槽会保留后续所需的 WAL，但崩溃重启后可能重发变更，消费者要自己去重。UPDATE 与 DELETE 能否带出旧行的列，取决于表的 replica identity (复制标识) 设置。这些只是快照与日志衔接的一种实现；账户目录、账户过滤和代次栅栏不是 PostgreSQL 自带的迁移功能。

### 冻结源端：同一行上的兼容锁与冲突锁

D 接近追平时，先让 B 的入口停止接收**新的**业务事务，免得队列继续变长。但入口关闭并不会让已经准入、正在执行或正在等所有权行锁的事务消失；它们必须由数据库来排序。

冻结事务更新同一行所有权记录：

```text
BEGIN
changed = UPDATE account_ownership
          SET state = 'frozen'
          WHERE account_id = $1
            AND owner_shard = 'B' AND epoch = 7 AND state = 'open'
          RETURNING account_id
if changed != exactly one account_id:
    ROLLBACK
    reread the authoritative state; do not claim B/7 was frozen
else:
    emit the barrier message (next section) in this same transaction
    COMMIT
```

这条 `UPDATE` 要等所有已持 `FOR SHARE` 锁的业务事务提交或回滚。它提交之后，排在后面的业务事务读到 `frozen` 并回滚。于是数据库给出一个确定的先后：每笔业务写要么在冻结之前提交，要么根本不提交。请求更早到达 API 不等于更早获得数据库写权。

![停止准入后，业务事务 op-9 与冻结事务在同一所有权行上排序](../../engineering-foundations/data/resources/i7-freeze-barrier.svg)

### 屏障位置 L：怎样证明目标已包含所有已提交写

冻结只说明 B 之后不会再有新提交；还要证明 D 已经拿到冻结之前的所有提交。做法是在冻结事务里同时写一条**事务性逻辑消息**，它与冻结状态一起提交。这条消息所在源事务的**提交位置**定义为 L。由于冻结排在所有已提交的 B/7 业务写之后，日志流里的 L 也排在它们之后。

判断依据只有一个：**D 连续应用的源端位置到达 L**。低复制延迟、估算的复制百分比、某台服务器当前的 LSN、源端行数都不够。即使 D 过滤掉了其他账户的变更，也要推进它已连续消费到的源端位置；D 从 S 之后尚未应用的部分继续追到 L，不重新全量重放。

D 应用每笔源事务时，把业务效果、复制来的幂等结果和“已连续应用到哪里”的检查点放在**同一个目标事务**里提交。检查点只有随事务提交后，才代表这些效果已持久可见。

> [!example] op-9 与冻结的两种先后
> 快照 S 中报表 42 仍是 `queued`。之后请求 `op-9` 在 B/7 的一笔业务事务里把它改为 `ready`，并在同一事务写入该操作的幂等结果。
>
> - **op-9 先拿到共享锁并提交：** 冻结要等它结束，L 在它之后。D 追到 L 时，已在同一目标事务里应用了 `ready`、复制了幂等结果并推进了检查点。D/8 开放后，`op-9` 的超时重试读到已复制的幂等结果，不会再生成一份业务效果。
> - **冻结先拿到锁：** `op-9` 读到 `frozen` 并回滚，B 上没有 `ready` 更新，也没有幂等结果；它的重试最终到 D 上正常执行。

L 是日志位置，不是时钟时刻，到达 L 也不单独证明数据正确。之后还要核对业务不变量：迁移范围的主键覆盖无缺口；报表 42 及其作业、幂等记录在 D 上可查；账户内唯一约束成立；按大小和风险核对行数、按稳定主键范围计算的摘要或校验和、关键聚合值。只比总行数，“缺一行、多一行”会互相抵消。任何一项不符，B 保持冻结（或在安全条件下恢复为唯一写者），绝不开放 D 让它边写边追。

### 切换目录并开放目标

D 追到 L 后，按以下顺序切换：

1. **准备候选。** 在 D 上 prepare `D/8/closed`，候选标识 `C8`。D 仍不接受业务写。
2. **封住复制写入并终验。** 关闭 C8 的回填与 CDC 写入口，排空已开始的复制事务；之后到达或重放的 C8 复制事务要被 D 的写资格检查拒绝。确认数据不再变化后，做最终完整性校验。
3. **目录 CAS。** 以完整当前值 `B/7` 为预期值，原子写入 `D/8 + C8 + decision_id=K8`。CAS 未命中时不发开门命令，而是重读权威目录；确认这个候选已不可逆地落败后，在 D 上冻结这一行，再准备更高代次。
4. **开放目标。** CAS 成功，或应答丢失但从权威目录确认 K8 已生效后，才执行条件更新 `D/8/closed/C8 → D/8/open/C8` 并记录 K8。这次更新必须同时匹配账户、owner、epoch、candidate 和 K8。

B/7 在第 3 步之前已经冻结，所以切换前后会有一小段时间**没有写者**。这是有意的：拿不到确切的开门决策就保持 `closed`，宁可短暂不可写，也不让两个库同时开放。

切换后，请求可能拿着旧路由到达 B：

- B 本地已是 `frozen`，拒绝写入。
- 入口能查到权威目录、确认 owner/epoch 已变时，返回 stale-route (路由过期)，客户端刷新路由后重试。
- B 只知道自己被冻结、查不到目录时，返回可重试的暂时不可用；目标与代次匹配但本地仍为 `closed` 时也一样。这两种情况都不能报 stale-route。
- 超时的非幂等请求不能因为刷新了路由就换个库重放，仍要沿用原来的稳定操作键查询结果或安全重试，每次重试照常授权。原因见[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)：超时意味着原请求可能已经提交。

这套栅栏只管写。按旧缓存仍读 B 的请求不会被拦截，也没有新鲜度保证；副本读的延迟、旧路由读的处理、read-your-writes 要由单独的读取契约规定。一次陈旧读的结果也不能用来证明旧库没有提交。

### 出错时能不能退回旧库？

能否安全回到 B，只取决于一件事：**D 是否已经产生过业务提交**。按失败发生的阶段：

| 失败时的状态 | 能否回 B | 做法 |
| --- | --- | --- |
| B/7 冻结之前（快照、捕获或回填失败） | B 本来就是唯一写者 | 停止并重建候选 D。只有能证明 CDC 区间没丢时才从原位置续跑，否则重建快照与起点 |
| B/7 已冻结，目录仍是 `B/7` | 可以，但只认 CAS 的赢家 | D/8 与 B/8 都只能是 `closed` 候选，各自的 CAS 都要求目录当前为 B/7。谁的 CAS 先成功，就只用那个决策开放谁；输家先确认落败，再冻结自己那一行，才能准备更高代次 |
| 目录已是 `D/8`，D/8 账本确认为零 | 可以 | 先在 D 上执行 `closed\|open → frozen`（若为 open，冻结会等持锁的业务事务结束）。冻结提交后，从 D 的权威写主新鲜读取 epoch 8 的本地账本，确认为零。B 上若还有 `closed` 候选，先确认它已落败并冻结；再在 B 上 prepare `B/9/closed`，目录 CAS `D/8 → B/9` 成功后用这个决策开放 B/9 |
| 目录已是 `D/8`，账本有提交或无法确认 | 不能直接回 B | B 已经陈旧。保持 D 为权威并向前修复；或先把 D 的新提交反向追平到 B、核验后再切。只需在 D 上恢复服务时，也经目录决定开放 `D/9`，不重新打开已冻结的 D/8 |

第三、四行的关键是“未知不按零处理”。账本缺失，或无法确认写主保留了所有可能已提交的效果（包括数据库已提交、客户端却没收到回执的事务），结论就是“未知”，按有提交对待。D/8 一旦冻结就是同代终态，迟到的开门命令（还拿着 K8）与冻结在同一行竞争：冻结先赢，开门条件失败；开门先赢，冻结会等它放进来的业务事务排空，再成为终态。

![目录切换与目标开门分开提交；安全回退取决于目标是否已有业务提交](../../engineering-foundations/data/resources/i7-owner-cutover-rollback.svg)

> [!info] 实例：Vitess 24.0 的重分片流程（核对于 2026-11-13）
> Vitess 的稳定文档把重分片拆成创建工作流、监控、用 VDiff 核对数据、`SwitchTraffic` 切流和完成清理，也支持反向切流。产品可能接管复制、路由、写缓冲或验证中的不同部分；本章的所有权行、CAS 条件和零提交回退规则是教学协议，不是 Vitess 的同名 API。采用产品流程时，仍要按版本确认每一步实际保证的状态。

### 单写者搬迁是栅栏原理的一个实例

本章产出一套单写者搬迁协议：所有权行与单调 epoch 决定谁能写，同一行上的兼容锁与冲突锁把冻结变成事务屏障，屏障位置 L 加业务校验证明目标完整，目录 CAS 加精确决策开门，回退只在目标零提交时才可行。它是栅栏原理的一个实例；同一原理在任务领取中的权威说明见[怎样保证一个任务同一时刻只由一个 worker 推进？](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)。主线四从[一次 HTTP 请求怎样从浏览器到达服务，又带回什么？](#33.%20%E4%B8%80%E6%AC%A1%20HTTP%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%B5%8F%E8%A7%88%E5%99%A8%E5%88%B0%E8%BE%BE%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%8F%88%E5%B8%A6%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)开始。

> [!info]- 来源
> - 快照与逻辑复制流衔接、复制槽保留 WAL 并可能在崩溃后重发、消费者去重：[PostgreSQL 18, Logical Decoding Concepts](https://www.postgresql.org/docs/18/logicaldecoding-explanation.html)，§47.2；UPDATE/DELETE 旧行列取决于 replica identity：[Logical Decoding](https://www.postgresql.org/docs/18/logicaldecoding.html)，§47 开篇；LSN 与 WAL 位置：[WAL Internals](https://www.postgresql.org/docs/18/wal-internals.html)，§28.6；复制进度跟踪：[Replication Progress Tracking](https://www.postgresql.org/docs/18/replication-origins.html)，§48。核对于 2026-11-13。
> - 事务性逻辑消息 `pg_logical_emit_message(true, …)`：[System Administration Functions](https://www.postgresql.org/docs/18/functions-admin.html#FUNCTIONS-REPLICATION)，§9.28.6；`pgoutput` 需启用 `messages` 选项才输出这类消息：[Logical Streaming Replication Protocol](https://www.postgresql.org/docs/18/protocol-logical-replication.html)，§54.5。核对于 2026-11-13。
> - 行级锁阻塞冲突的更新直到持锁事务结束、`FOR SHARE` 与更新冲突：[PostgreSQL 18, Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html)，§13.3.2；Read Committed 下等待后返回并重检更新后的行版本：[Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)，§13.2.1。核对于 2026-11-13。
> - Vitess 重分片、VDiff、切流与反向切流：[Vitess 24.0, Reshard](https://vitess.io/docs/24.0/reference/vreplication/reshard/)，核对于 2026-11-13。
> - 所有权表、状态转换、本地提交账本、目录 CAS 与回退规则是本章定义的教学协议，不是 PostgreSQL 或 Vitess 的功能；B/7、D/8、C8、K8、L、op-9 为本章合成标识。
## 33. 一次 HTTP 请求怎样从浏览器到达服务，又带回什么？

本章跟着一次报表读取，从页面发出 `GET` 走到页面拿到可用的结果。途中要分清几件事：HTTP 语义规定了什么，连接和 TLS 各证明什么，状态码和客户端 API 又怎样判定这次请求的结局。读者只需要 TCP/IP 分层的本科常识。本章同时建立主线四的贯穿案例，后面的缓存、会话、授权、API 契约和条件写都沿用它。

### 案例：账户报表服务里的一次读取

一家 SaaS 公司提供账户报表服务。账户 `acct-17`（本主线说的“账户”就是租户）里有 principal (主体) `user-17`，他是该账户的成员，持有 `report:read` 和 `report:export` 两项权限。报表 42 的标题是 `Service health`。本主线的主机、账户、权限和报文都是合成的教学数据，这一点只在这里说明一次。

| 主机 | 角色 |
| --- | --- |
| `https://reports.example.test` | 报表页面，以及服务于页面的后端 BFF（backend for frontend）。BFF 把同源的 `/v1/` 请求转发到 API 的同名路径 |
| `https://api.reports.example.test` | 报表 API，按账户保存报表并做最终授权 |

`user-17` 已经登录，打开报表页。页面脚本发出同源请求 `GET /v1/accounts/acct-17/reports/42`。浏览器自动附上会话 Cookie，BFF 查到会话后带着 API 访问令牌把请求转给 API。用户要的结果很简单：只要他此刻仍有权读这份报表，就看到它的当前内容。

后续各章在这次读取上加条件：[缓存章](#34.%20%E4%B8%80%E4%BB%BD%20HTTP%20%E5%93%8D%E5%BA%94%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%8F%AF%E4%BB%A5%E7%9B%B4%E6%8E%A5%E5%A4%8D%E7%94%A8%EF%BC%8C%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%BF%85%E9%A1%BB%E5%9B%9E%E6%BA%90%E7%A1%AE%E8%AE%A4%EF%BC%9F)让浏览器带着已存版本回源验证；[会话章](#35.%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E5%B8%A6%E4%B8%8A%E5%8F%AF%E4%BF%A1%E7%9A%84%E8%BA%AB%E4%BB%BD%EF%BC%8C%E6%B5%8F%E8%A7%88%E5%99%A8%E5%8F%88%E6%9B%BF%E6%9C%8D%E5%8A%A1%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%BE%B9%E7%95%8C%EF%BC%9F)说明 Cookie 和令牌怎样变成可信主体；[授权章](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)引入另一个账户的主体，看服务端怎样拒绝；[条件写章](#38.%20%E4%B8%A4%E4%B8%AA%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%90%8C%E6%97%B6%E4%BF%AE%E6%94%B9%E5%90%8C%E4%B8%80%E8%B5%84%E6%BA%90%E6%97%B6%EF%BC%8CAPI%20%E6%80%8E%E6%A0%B7%E9%98%B2%E6%AD%A2%E4%BA%92%E7%9B%B8%E8%A6%86%E7%9B%96%EF%BC%9F)让两位编辑者同时修改报表 42。导出报表那条异步路线从[未知结果章](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)开始。

### HTTP 的含义和线上格式是两层

HTTP 先是一套语义：方法表达调用方想对目标资源做什么，目标 URI 标识资源，字段携带元数据，状态码说明这次处理的结果类别，正文承载资源的一种表示。这些含义由 RFC 9110 统一规定。HTTP/1.1、HTTP/2、HTTP/3 是三种线上格式，各自决定字段和正文怎样编码、一条连接上怎样并发多个请求。

同一个 `GET → 200 + JSON` 可以由三个版本中的任何一个承载，应用看到的方法、状态码和表示都一样。所以讨论“这个请求能否重试”“这个响应能否缓存”时，看的是语义层；讨论“丢一个包谁要等”时，才看版本和传输层。本章先讲语义，再讲连接，最后回到页面怎样判定结果。

### 请求怎样说明“想要什么”

下面用 HTTP/1.1 的文本格式展示这次请求。HTTP/2 和 HTTP/3 传输同样的语义，只是线上没有这段逐行文本：

~~~http
GET /v1/accounts/acct-17/reports/42 HTTP/1.1
Host: reports.example.test
Accept: application/json
Accept-Language: zh-CN, en;q=0.8
Cookie: __Host-session=<opaque-session-id>
~~~

页面只写了方法、路径和偏好；`Cookie` 由浏览器按 Cookie 规则附上，网页脚本不能自己设置这个字段。响应节选如下（省略 `Date` 等与本节无关的字段，缓存相关字段下一章再讲）：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Language: zh-CN
Content-Length: 134
Vary: Accept-Language

{"id":42,"title":"Service health","status":"ready","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

服务端返回的是 representation (表示)：按本次请求选定的媒体类型、语言等形式，不必等于数据库里的一行。请求和响应的协商字段成对出现：

| 请求字段：调用方想要 | 响应字段：实际给了 | 说明 |
| --- | --- | --- |
| `Accept` | `Content-Type` | 媒体类型。请求若带正文，请求里的 `Content-Type` 描述的是请求正文 |
| `Accept-Encoding` | `Content-Encoding` | `gzip`、`br` 等内容编码；解码后仍是同一媒体类型 |
| `Accept-Language` | `Content-Language` | 自然语言；服务器不一定有首选语言的版本 |

`Vary: Accept-Language` 告诉缓存：这份表示随请求的 `Accept-Language` 而变，只有新请求的该字段与存储时匹配，才能复用它。`Content-Length: 134` 是上面 JSON 的 UTF-8 字节数；在持久连接上，接收方靠它知道正文在哪里结束。

### 方法的两个性质：安全与幂等

方法语义里最常被依赖的是两个性质，全领域都以这里的定义为准。

- **safe method (安全方法)**：调用方预期它只读取，不改变目标资源的状态。服务端仍可以记访问日志一类的附带效果，但调用方不为它们负责。
- **idempotent method (幂等方法)**：同一请求重复执行多次，预期的服务器效果与执行一次相同。它不要求每次响应相同：第一次 `DELETE` 回 `204`，第二次回 `404`，资源最终都不存在。

| 方法 | 安全 | 幂等 | 备注 |
| --- | --- | --- | --- |
| `GET`、`HEAD` | 是 | 是 | 可被缓存、预取 |
| `PUT` | 否 | 是 | 正文描述成功后目标资源应呈现的状态；未提交的字段是否清空由资源契约决定 |
| `DELETE` | 否 | 是 | 重复删除不改变最终结果 |
| `PATCH` | 否 | 由补丁格式和 API 契约决定 | 见[条件写章](#412%20%E4%B9%8B%E5%90%8E%E5%AE%A2%E6%88%B7%E7%AB%AF%E6%80%8E%E4%B9%88%E5%8A%9E) |
| `POST` | 否 | 默认不保证 | 要靠应用层的 idempotency key (幂等键) |

这两个性质决定了哪些请求可以被别人替你多发一次。浏览器和爬虫可以预取安全方法；连接在读到响应前断开时，客户端可以自动重试幂等请求，却不能自动重试 `POST`。性质只说明“重复执行是否安全”，不说明“上一次执行到底有没有提交”。一个写请求在连接中断前可能已经生效，要确认它，得靠稳定的操作标识回查，见[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

> [!info] HTTP 方法与 REST 不是一回事
> REST（Representational State Transfer）是 Fielding 提出的一组架构约束：客户端与服务端分离、无状态交互、可缓存、统一接口、分层系统，以及可选的按需代码。统一接口又要求用资源标识目标、通过表示操纵资源、消息自描述、以超媒体驱动状态转移。用了 HTTP 方法和 JSON 不等于满足这些约束；要称 REST 风格，得逐条检查。超媒体链接的契约前提见 [API 契约章](#%E8%BF%94%E5%9B%9E%E7%9A%84%E9%93%BE%E6%8E%A5%E8%83%BD%E6%9B%BF%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%81%9A%E4%BB%80%E4%B9%88)。

### 字段只描述意图：认证、授权和 CORS 各管一段

请求字段说的是“想要什么”，“能不能拿”要另外判断，而且分三处判断：

- `Cookie` 或 `Authorization` 只携带认证信息。服务端据此确认请求代表谁，见[会话章](#35.%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E5%B8%A6%E4%B8%8A%E5%8F%AF%E4%BF%A1%E7%9A%84%E8%BA%AB%E4%BB%BD%EF%BC%8C%E6%B5%8F%E8%A7%88%E5%99%A8%E5%8F%88%E6%9B%BF%E6%9C%8D%E5%8A%A1%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%BE%B9%E7%95%8C%EF%BC%9F)。
- 认出主体以后，API 还要按当前主体、账户和资源逐次检查这个动作是否允许，见[授权章](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)。路径里的 `acct-17` 和 `42` 是调用方选的值，不是权限证明。
- 页面脚本跨源读取响应时，浏览器还按 CORS 规则决定脚本能不能读到响应。CORS 允许读取，不等于这个用户有权读报表，见[会话章的跨源读取一节](#%E8%B7%A8%E6%BA%90%E8%AF%BB%E5%8F%96%EF%BC%9A%E8%AF%B7%E6%B1%82%E5%88%B0%E8%BE%BE%E5%92%8C%E5%93%8D%E5%BA%94%E5%8F%AF%E8%AF%BB%E6%98%AF%E4%B8%A4%E4%BB%B6%E4%BA%8B)。

本例的请求与页面同源，发往 BFF，所以不涉及 CORS；认证和授权两步一步都不能少。

### 发到网络之前：四层快路径

页面调用 `fetch()` 之后，请求不一定马上上网。下图是这次读取的完整去程：请求先穿过 Service Worker、浏览器 HTTP 缓存、连接池和 DNS 四层彼此独立的快路径，需要时再建连，经 BFF 和第二段 TLS 到达 API。本节和后两节依次展开快路径、建连和 TLS。

![页面 fetch() 依次经过 Service Worker、HTTP 缓存、连接池和 DNS，再建立连接，经 BFF 与第二段 TLS 到达 API；右侧标出各层命中时的短路和 TLS 证明与不知道的内容](../../engineering-foundations/services/resources/http-request-outbound-path.svg)

命中其中一层，不代表其他几层也命中。几点图上放不下：

- Service Worker 是页面注册的脚本，可以拦截、合成或继续转发请求；本例假设它原样转发。
- HTTP 缓存怎样决定复用、回源验证或走网络，见[下一章](#34.%20%E4%B8%80%E4%BB%BD%20HTTP%20%E5%93%8D%E5%BA%94%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%8F%AF%E4%BB%A5%E7%9B%B4%E6%8E%A5%E5%A4%8D%E7%94%A8%EF%BC%8C%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%BF%85%E9%A1%BB%E5%9B%9E%E6%BA%90%E7%A1%AE%E8%AE%A4%EF%BC%9F)。
- 本地没有仍有效的 DNS 记录时才问递归解析器；递归解析器也可能从缓存回答，或者沿 DNS 委派逐级查询。记录的 TTL（time to live）限定缓存时长。

连接和地址记录的生命周期互不约束：连接关闭后地址可能仍在缓存里；DNS 记录过期也不要求关闭现有连接。

> [!info] 资源提示提前准备的是哪一层
> HTML 的资源提示让页面提前做上面某一层的工作。`preload` 尽早取得当前页面确定要用的关键资源；`prefetch` 以低优先级准备后续导航可能用到的资源；`preconnect` 提前解析域名并建立连接；`dns-prefetch` 只提前查域名。浏览器按自身策略处理提示，不保证照办；连接提示占用连接和网络资源，只适合很快就会访问的来源。
>
> ~~~html
> <link rel="preload" href="/fonts/main.woff2" as="font" crossorigin>
> <link rel="prefetch" href="/next-page.js">
> <link rel="preconnect" href="https://api.reports.example.test">
> <link rel="dns-prefetch" href="//api.reports.example.test">
> ~~~

### 建立连接：TCP、QUIC 与版本协商

没有可复用的连接时，浏览器要新建一条。HTTP/1.1 和 HTTP/2 跑在 TCP 上，HTTP/3 跑在 QUIC 上。

**TCP 给应用一条有序、可靠的字节流。** 建连时客户端发 SYN 同步初始序号，服务端回 SYN-ACK 确认并给出自己的初始序号，客户端再回 ACK。这条字节流不保留消息边界：一次 `write()` 不对应对端的一次 `read()`。所谓“粘包”，其实是把字节流误当成了消息队列；应用协议必须自己用长度、分隔符等规则划分消息。关闭时两个方向可以分别结束，一方关闭发送后另一方仍能继续发数据，所以常见的“四次挥手”图不代表每次都恰好有四个独立报文。

**QUIC 在 UDP 上实现自己的连接和多条可靠流，并把 TLS 1.3 的密钥协商并入建连**，不做 TCP 三次握手。

**版本靠协商确定。** HTTPS 上的 HTTP/2 通过 TLS 的 ALPN（Application-Layer Protocol Negotiation）选出 `h2`。HTTP/3 端点通常由 `Alt-Svc` 等方式告知，浏览器随后尝试 QUIC；若网络阻断 UDP，客户端应退回 TCP 上的版本。复用连接时，这些步骤都已在早先完成。

传输层只负责把字节可靠地送到对端。它不验证用户身份，不做授权，也不能确认一个超时的业务操作是否已经提交。

### TLS 证明什么

HTTPS 在 HTTP 之下用 TLS 保护连接。它的证明范围在全领域以这里为准：

- **证明了什么。** 浏览器验证服务器证书中的身份与访问的主机名相符，并且握手成功之后，TLS 保护这条连接上后续应用数据的机密性和完整性。证书身份匹配说明客户端连到了预期的服务端。
- **依赖什么。** 证书撤销状态取决于客户端采用的机制及其数据新鲜度，例如浏览器自己分发的撤销列表；不能假设浏览器在每个请求上都实时查询撤销状态。
- **不知道什么。** TLS 不知道这次请求代表 `user-17`，也不判断报表 42 属于哪个账户。HTTPS 完全正常时，BFF 仍须验证会话，API 仍须逐次授权；本例两段 TLS 各自只证明自己那一跳，API 靠 BFF 附上的访问令牌知道请求代表谁（见上文去程图）。
- **失败长什么样。** 证书错误、主机名不匹配或握手失败时，根本没有 HTTP 响应：浏览器终止连接或显示证书错误，页面得到的是网络错误，不是 API 返回的 `500`。

#### 0-RTT 早期数据可以被重放

TLS 1.3 恢复连接时，客户端可以选择发送 0-RTT（zero round-trip time）early data (早期数据)，在握手完成前就把请求送出去。代价是早期数据可能被攻击者截获后重放。HTTP 的规则因此是：客户端没有额外信息时，只把安全方法放进早期数据，不发送不安全或安全性未知的方法。服务端对每个资源仍要判断能否提前处理，可以推迟处理、部署防重放措施，或者回 `425 Too Early` 让客户端在握手完成后重发。安全方法也可能有附带效果；有不可重复副作用的接口，仍须靠应用层去重。连接恢复机制不保证业务操作只执行一次。

### 三个 HTTP 版本怎样承载同一请求

连接就绪后，请求按协商出的版本编码发出。三个版本都能表达本例的 `GET`、目标 URI、协商字段和响应状态；区别在帧格式、一条连接上怎样并发，以及丢包时谁要等。

![同一 HTTP 语义在 HTTP/1.1、HTTP/2、HTTP/3 中的帧与传输承载](../../engineering-foundations/services/resources/http-version-layers.svg)

- **HTTP/1.1** 用文本起始行和字段，正文本身可以是二进制。消息有没有正文、正文在哪里结束，由方法、状态码、`Content-Length`、分块传输编码或关闭连接等规则确定。持久连接可以复用，但没有流多路复用：流水线可以连发多个请求，服务器仍须按请求顺序返回响应，前一个响应慢，后一个就得等。客户端也可以开多条连接并发。持久连接只复用请求—响应通道，不意味着服务端能在没有请求时主动推送响应。
- **HTTP/2** 把字段块和正文装进二进制 `HEADERS`、`DATA` 等帧，用流 ID 区分并发的请求—响应，用 HPACK 压缩字段块。不同流的帧在同一条 TCP 连接上交错，应用不必等前一个响应结束。它有逐流和整条连接两级流量控制，额度耗尽时相应的发送等待补额。但 TCP 要求按字节序交付：较早的段丢失时，后面已到的字节也要等重传补齐，这条连接上的多个 HTTP/2 流可能一起停住。
- **HTTP/3** 保持同一语义，把帧放到 QUIC 流上，用 QPACK 压缩字段块。QUIC 对每条流单独做可靠交付和流量控制，连接总量也有额度；拥塞控制则由整条连接共享。

![同一连接丢失一段数据时，HTTP/2 与 HTTP/3 中哪些流要等待](../../engineering-foundations/services/resources/http-head-of-line.svg)

图中 HTTP/2 一侧，报表帧和图片帧混在同一 TCP 字节流里；片段 2 丢失后，TCP 不会把它后面的字节先交给 HTTP/2。HTTP/3 一侧假设报表流的数据和流结束标志 FIN 都已到达、所需的 QPACK 表项也已到达，而图片流有缺口；这时报表可以先交付，不受图片流拖累。反过来，报表流自身有缺口或缺 QPACK 表项时，它照样不能完成。所以 HTTP/3 缓解了跨流的等待，但没有消除共享的网络瓶颈。

这里有两种不同层次的 head-of-line blocking (队头阻塞，HOL)：HTTP/1.1 流水线的等待来自应用协议要求按序响应；HTTP/2 的跨流等待来自共享 TCP 的按序交付。

### 消息在哪里结束：分帧、内容编码与应用消息

“一个响应在哪里结束”和“一条应用消息在哪里结束”是三层不同的问题，不要混用：

| 层次 | 例子 | 回答的问题 |
| --- | --- | --- |
| HTTP 消息分帧 | HTTP/1.1 的 `Content-Length` 或 `Transfer-Encoding: chunked`；HTTP/2 最后一个 `HEADERS` 或 `DATA` 帧上的 `END_STREAM`；HTTP/3 中 QUIC 流发送方向的 FIN | 这条 HTTP 消息到哪里结束 |
| 表示的内容编码 | `Content-Encoding: gzip`、`br` | 正文是否压缩过；解码前后媒体类型相同 |
| 应用消息边界 | SSE 的空行、WebSocket 的消息、自定义长度前缀 | 应用自己的一条事件或记录到哪里结束 |

HTTP/2 和 HTTP/3 不使用 HTTP/1.1 的 transfer-coding；它们的 `DATA` 帧也不一定代表响应结束。TCP 的字节流边界、QUIC 的流边界都不是 SSE 或 WebSocket 消息的边界，应用协议要自己解释帧、分隔符或事件。持续推送的消息怎样切分，见[实时通道支线](#39.%20%E6%9C%8D%E5%8A%A1%E7%AB%AF%E8%A6%81%E6%8C%81%E7%BB%AD%E6%8E%A8%E9%80%81%E6%9B%B4%E6%96%B0%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E9%80%89%E9%80%9A%E9%81%93%EF%BC%8C%E6%96%AD%E7%BA%BF%E5%90%8E%E5%8F%88%E6%80%8E%E6%A0%B7%E6%8E%A5%E4%B8%8A%EF%BC%9F)。

### 状态码只描述这一次请求

服务端（本例是 API，经 BFF 转回）完成认证和授权，读取资源，再选择状态码和表示。状态码只给出这次 HTTP 请求的结果类别，不描述整个业务生命周期，也不代表正文已经完整到达。

| 类别与常见含义 | 需要留意 |
| --- | --- |
| **`1xx`** 中间信息，如 `100 Continue` | 不是最终结果 |
| **`2xx`** `200` 返回当前表示；`201` 已创建资源；`202` 已受理、尚未完成 | `202` 不说明作业会成功，受理语义见[耗时任务怎样被持久受理？](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F) |
| **`3xx`** 如 `304` 表示条件请求可复用已存表示 | `304` 没有正文，只用于条件 `GET`/`HEAD` |
| **`4xx`** `400` 请求无效；`401` 缺少或无效凭据；`403` 拒绝；`404` 不存在或按策略隐藏；`409` 冲突；`429` 请求过多 | `401` 必须带适用的 `WWW-Authenticate` 质询；`403` 与隐藏式 `404` 的选择见[授权章](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F) |
| **`5xx`** `500` 未预期的服务端错误；`502` 上游响应无效；`503` 暂时不能处理；`504` 网关等上游超时 | 它们来自服务端或网关；客户端自己等到超时，没有任何状态码 |

本例中，`user-17` 仍有权限时，API 回 `200` 和上面的表示；请求没有带有效凭据时回 `401` 加 `WWW-Authenticate`。各错误怎样写成可判定的正文、多个错误同时成立时先报哪个，见 [API 契约章](#37.%20%E6%80%8E%E6%A0%B7%E8%AE%A9%E8%B0%83%E7%94%A8%E6%96%B9%E5%8F%AF%E9%9D%A0%E5%9C%B0%E5%88%A4%E6%96%AD%20API%20%E7%9A%84%E6%88%90%E5%8A%9F%E3%80%81%E5%A4%B1%E8%B4%A5%E5%92%8C%E5%8F%98%E5%8C%96%EF%BC%9F)。

### 页面什么时候才算拿到结果

状态码到达，页面还不一定能用这个结果。`fetch()` 收到任何 HTTP 响应都会兑现，`404`、`500` 也一样，所以页面要检查 `response.ok` 或 `status`；响应头到达后，读取正文仍可能因断连、解码失败或 JSON 语法错误而失败。这些判定的完整规则见[fetch 履行不等于请求成功](../../frontend/javascript/promises-and-async-functions.md#fetch%20%E5%B1%A5%E8%A1%8C%E4%B8%8D%E7%AD%89%E4%BA%8E%E8%AF%B7%E6%B1%82%E6%88%90%E5%8A%9F)。其他客户端各有自己的边界：Axios 默认按 `validateStatus` 决定非 2xx 是否进入错误分支；XMLHttpRequest 的 `load` 只表示请求完成，不表示状态码是 2xx。浏览器 API、客户端库和协议的成败判定不能互相代替。

### 下一步：这份 200 能不能被缓存复用？

本章交出的是一次完整读取的分层视图：请求用方法和协商字段表达意图；方法的安全性和幂等性决定谁可以替你重发；连接与 TLS 只证明字节送到了预期主机；状态码只说明这一次请求；页面还要自己判定正文是否完整可用。下一章从这份 `200` 出发：浏览器把它存进私有缓存以后，什么时候可以直接用，什么时候必须带着版本标识回源确认，以及确认时服务端为什么要先授权再比版本。

> [!info]- 来源
> - HTTP 语义、表示与内容协商、方法的安全与幂等性及自动重试、状态码、`401` 质询（“HTTP 的含义和线上格式是两层”“请求怎样说明‘想要什么’”“方法的两个性质”“状态码只描述这一次请求”）：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，2022-06，§3、§6–§9（§9.2.1–§9.2.2）、§11.6.1、§12、§15；核对于 2026-11-12。
> - HTTP/1.1 消息语法、正文定界、持久连接与流水线：[IETF RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html)，2022-06，§2、§6、§9；HTTP/2 流、帧、流量控制与 TCP 队头阻塞：[IETF RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html)，2022-06，§1、§3–§6；HTTP/3 与 QUIC 流的映射：[IETF RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html)，2022-06，§1–§4。均核对于 2026-11-12。
> - HPACK：[IETF RFC 7541](https://www.rfc-editor.org/rfc/rfc7541.html)，2015-05，§1–§2；QPACK 与动态表阻塞：[IETF RFC 9204](https://www.rfc-editor.org/rfc/rfc9204.html)，2022-06，§1–§2.1.2。
> - TCP 建连、字节流与半关闭（“建立连接”）：[IETF RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html)，2022-08，§3、§3.5–§3.6.1；QUIC 流与流量控制：[IETF RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)，2021-05，§2–§4；连接级拥塞控制：[IETF RFC 9002](https://www.rfc-editor.org/rfc/rfc9002.html)，2021-05，§7；QUIC 中的 TLS：[IETF RFC 9001](https://www.rfc-editor.org/rfc/rfc9001.html)，2021-05，§4–§5。均核对于 2026-11-12。
> - TLS 1.3 的握手认证、数据机密性与完整性、早期数据重放（“TLS 证明什么”“0-RTT”）：[IETF RFC 9846, TLS 1.3](https://www.rfc-editor.org/info/rfc9846/)，2026-07，§1.2、§2、§4.5、§5.2、§8；该版本已取代 RFC 8446。服务身份与访问名称匹配：[IETF RFC 9525](https://www.rfc-editor.org/rfc/rfc9525.html)，2023-11，§1.1、§6；证书撤销没有通用的完整高效检查方案：[IETF RFC 9325](https://www.rfc-editor.org/rfc/rfc9325.html)，2022-11，§7.5；浏览器端撤销数据的一个实例：[Chromium CRLSets](https://www.chromium.org/Home/chromium-security/crlsets/)。HTTP 早期数据与 `425 Too Early`：[IETF RFC 8470](https://www.rfc-editor.org/rfc/rfc8470.html)，2018-09，§2–§5。均核对于 2026-11-12。
> - DNS 委派与解析器缓存（“发到网络之前”）：[IETF RFC 1034](https://www.rfc-editor.org/rfc/rfc1034.html)，1987-11，§4–§5；DNS 负缓存：[IETF RFC 2308](https://www.rfc-editor.org/rfc/rfc2308.html)，1998-03，§3–§5。
> - Fetch 的 Service Worker、HTTP 缓存与连接获取分层，脚本不能设置 `Cookie`：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，Living Standard，2026-10-19 版，核对于 2026-11-12。XMLHttpRequest 事件：[WHATWG XMLHttpRequest Standard](https://xhr.spec.whatwg.org/)，Living Standard，2026-11-11 版；Axios 非 2xx 与 `validateStatus`：[Axios Handling Errors](https://axios-http.com/docs/handling_errors)，核对于 2026-11-12。
> - `429 Too Many Requests`：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，2012-04，§4。资源提示：[WHATWG HTML Living Standard, Link types](https://html.spec.whatwg.org/multipage/links.html#linkTypes)，§4.6.8.5、§4.6.8.18–§4.6.8.20，核对于 2026-11-12。
> - REST 约束（callout）：[Roy T. Fielding, Architectural Styles and the Design of Network-based Software Architectures](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，2000，第 5 章。
## 34. 一份 HTTP 响应什么时候可以直接复用，什么时候必须回源确认？

上一章的读取拿到了报表 42 的 `200`。本章回答浏览器把它存下来以后的事：缓存凭哪三个条件决定直接复用，常见的 `Cache-Control` 指令各自允许什么，回源验证时服务端怎样先授权再比版本，以及页面最终看到的是什么。本章是全领域 HTTP 缓存语义的权威位置；应用层数据缓存（Redis 一类）另见[加了缓存之后，读到的数据最多会旧多久？](#30.%20%E5%8A%A0%E4%BA%86%E7%BC%93%E5%AD%98%E4%B9%8B%E5%90%8E%EF%BC%8C%E8%AF%BB%E5%88%B0%E7%9A%84%E6%95%B0%E6%8D%AE%E6%9C%80%E5%A4%9A%E4%BC%9A%E6%97%A7%E5%A4%9A%E4%B9%85%EF%BC%9F)。

### 沿用的案例：浏览器私有缓存里存着 v7

沿用[主线四的报表读取案例](#%E6%A1%88%E4%BE%8B%EF%BC%9A%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E9%87%8C%E7%9A%84%E4%B8%80%E6%AC%A1%E8%AF%BB%E5%8F%96)。本章补上上一章省略的两个响应字段：API 给报表 42 当前的表示生成了强 ETag（entity tag，实体标签）`"report-42-v7"`，并声明了缓存策略：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Language: zh-CN
ETag: "report-42-v7"
Cache-Control: private, no-cache
Vary: Accept-Language

{"id":42,"title":"Service health","status":"ready","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

ETag 是服务端给资源某一版本的表示起的不透明标识，只比较相等，不按字符串推断新旧。浏览器把这份响应存进自己的私有 HTTP 缓存。之后页面再次请求报表 42 时，缓存要决定：直接交出这份 v7，还是先问服务器 v7 是否仍是当前版本。

### 缓存复用前要回答的三个问题

缓存（浏览器缓存、CDN 或代理）收到请求时，按三个问题判断能否用已存的响应代替网络：

1. **能不能存。** 响应带 `no-store` 就不存；共享缓存还要遵守 `private` 等限制。其余响应按状态码和指令判断。
2. **缓存键是否匹配。** 缓存通常按请求方法和目标 URI 区分响应；响应里的 `Vary` 再列出影响表示的请求字段。本例的 `Vary: Accept-Language` 意味着英文偏好的请求不能拿走中文表示。
3. **是否仍新鲜。** `max-age=60` 表示响应的 age（年龄，自源站生成以来经过的时间）小于 60 秒时新鲜；恰好 60 秒时已经不新鲜。

三个问题都答“是”，且没有指令要求先验证，缓存可以完全不联系服务器，直接交出存储的响应。响应不再新鲜，或指令要求每次验证时，缓存发 conditional request (条件请求)：把存储的 ETag 放进 `If-None-Match` 问服务器。“已过期”也不等于“绝不能交出”，有些指令或配置明确允许在特定情况下使用过期响应。

验证器和新鲜期管不同的事：ETag 只在需要验证时才用；仍新鲜的响应不会因为带了 ETag 就提前回源。缓存键和验证器必须覆盖 API 实际协商的所有维度，但它们都不是对象权限检查。

### 常用指令各允许什么

| 指令 | 含义 | 常见误解 |
| --- | --- | --- |
| `max-age=N` | age 小于 N 秒时新鲜，可不问源站直接复用 | 以为过期就绝不能用；有些指令或配置允许使用特定的过期响应 |
| `no-cache` | 可以存，但每次复用前都必须先向源站验证 | 以为是“不要缓存” |
| `no-store` | 不要存储这次请求和响应 | 以为能单独保证隐私；它只约束合规缓存的存储行为 |
| `private` | 只允许浏览器这类私有缓存存，共享缓存不得存 | 以为它做了用户间授权隔离或内容保密 |
| `public` | 允许共享缓存存储，即使响应按默认规则不可存，例如请求带了 `Authorization` | 以为“public”管的是谁能访问；它只放宽存储许可 |
| `immutable` | 新鲜期内表示不会变化，浏览器无需验证，用户普通刷新时也不必发条件请求 | 以为内容从此永不过期；它只在新鲜期内生效 |

`private` 对本例很关键。浏览器到 BFF 的请求靠 `Cookie` 认证，不带 `Authorization`；若 BFF 前面有 CDN 或共享代理，而响应没有声明 `private` 或 `no-store`，一个用户的可缓存响应就可能被共享缓存存下，再交给另一个用户。

本例选 `private, no-cache`：允许浏览器存，但每次复用前都回源，于是每次复用都会经过一次服务端授权。

### 回源验证：If-None-Match 与 304 的完整路径

页面用默认缓存模式再次 `fetch()` 报表 42。页面只发普通 `GET`，HTTP 缓存发现存储的响应要求验证，便在网络请求上自动加 `If-None-Match: "report-42-v7"`。

![报表读取经缓存验证到达服务，再按授权与版本得到 304、200 或拒绝，并交回页面](../../engineering-foundations/services/resources/http-request-route.svg)

图上排是请求：Service Worker 原样转发，浏览器按 Cookie 规则附上会话凭据，缓存加上验证字段，连接层复用或新建连接。服务端按固定顺序处理：

1. **先确认主体和权限。** BFF 验证会话，API 确认 `user-17` 当前仍能读 `acct-17` 的报表 42。权限已撤销时，服务端按隐私策略回 `403` 或隐藏式 `404`（选择见[授权章](#%E9%9A%90%E8%97%8F%E5%BC%8F%20404%20%E8%BF%98%E6%98%AF%20403)）。缓存不能用旧的成功正文绕过这一步。
2. **再比较版本。** 权限通过后，服务端看被选中的表示是否仍匹配 `"report-42-v7"`。`If-None-Match` 用弱比较，标签的弱标记不影响结果。
3. **按结果回复。**
   - 表示未变：回无正文的 `304 Not Modified`，并带上 `200` 时本会发送的 `ETag`、`Cache-Control`、`Vary` 等字段，供缓存更新存储的元数据。
   - 表示已变：回新的 `200`、新正文和新 ETag，例如报表被编辑后的 `"report-42-v8"`。

~~~http
HTTP/1.1 304 Not Modified
ETag: "report-42-v7"
Cache-Control: private, no-cache
Vary: Accept-Language
~~~

图下排是结果怎样交回页面。网络上是 `304` 时，缓存先用它更新存储的响应，再把存储的 `200` 和原正文交给页面，所以页面看到的是 `200` 加 v7 正文，而不是 `304`。网络上是 `200` 时，缓存保存新表示，页面得到新正文。被拒绝时，页面进入错误分支，不会拿旧正文冒充成功。

#### 脚本手动加 If-None-Match 会改变缓存模式

页面脚本若在默认缓存模式的请求里自己写 `If-None-Match`，Fetch 会把这次请求的缓存模式改成 `no-store`，走的就不是上面的自动验证路径。此时网络上的 `304` 会原样成为页面看到的 `304`：`response.ok` 为 `false`，也没有旧正文自动拼回来。通常应让浏览器缓存管理验证；只有应用明确要自己保存表示、自己处理 `304` 时，才手动设置验证字段。

### 新鲜期内撤权，缓存仍可能交出旧正文

把策略换成 `private, max-age=60`，情况就变了：在这 60 秒内，浏览器可以不问服务器直接复用正文。若 `user-17` 在第 10 秒被移出 `acct-17`，他在接下来的 50 秒里仍可能看到 v7，因为这期间根本没有请求到达服务端，也就没有授权检查。

所以新鲜期就是“撤权最多晚多久生效”的上限。需要每次复用都重新确认访问权，就选每次验证（`no-cache`）；内容敏感到不该留在设备上，就选 `no-store`，代价是失去 `304` 省下的传输。不论哪种策略，API 的授权检查都是最终边界。

### 用户范围的响应怎样写缓存字段

按用户或账户变化的响应，要显式声明缓存策略，不能依赖默认行为：

- **成功表示。** 至少 `private`，挡住共享缓存。本例报表 42 的 `200` 用 `private, no-cache`。
- **隐藏式 `404` 和其他授权结果。** RFC 9110 允许缓存对 `404` 做启发式缓存，状态码本身挡不住存储。本例对隐藏式 `404`、`401`、`403` 这类按主体变化的结果设 `Cache-Control: private, no-store`，避免旧的拒绝结果在权限变化后继续被复用。
- **`Vary: Origin`。** API 若按请求来源动态选择 CORS 的 `Access-Control-Allow-Origin`，要加 `Vary: Origin`，让缓存区分不同来源的表示。它只区分来源，不区分同一来源下的不同用户，不保护私有数据（CORS 见[会话章的跨源读取一节](#%E8%B7%A8%E6%BA%90%E8%AF%BB%E5%8F%96%EF%BC%9A%E8%AF%B7%E6%B1%82%E5%88%B0%E8%BE%BE%E5%92%8C%E5%93%8D%E5%BA%94%E5%8F%AF%E8%AF%BB%E6%98%AF%E4%B8%A4%E4%BB%B6%E4%BA%8B)）。
- **ETag 与 `Vary` 一致。** ETag 应按被选中的那份表示生成；语言、媒体类型或内容编码不同的表示，要有可区分的标签，并与 `Vary` 和验证逻辑保持一致。强 ETag 的生成规则见[条件写章](#%E5%BC%BA%20ETag%20%E6%80%8E%E6%A0%B7%E6%A0%87%E8%AE%B0%E4%B8%80%E4%B8%AA%E7%89%88%E6%9C%AC)。

公开的静态资源走另一种策略：把内容摘要放进文件名，同一 URL 永远对应同一内容，于是可以设很长的 `max-age` 并加 `immutable`；入口 HTML 则每次验证。这套发布做法见[发布新版本时，怎样让缓存和还开着的旧页面都不出错？](../../frontend/delivery/hashed-release-and-caching.md)。

### 下一步：服务端凭什么认定请求来自 user-17？

本章交出的是一条可验证的复用规则：缓存只在能存、键匹配、仍新鲜三者都成立时直接复用；否则带 ETag 回源，服务端先授权、再比版本，页面在自动验证时看到的是原 `200`。新鲜期决定了撤权最晚何时生效，用户范围的响应要用 `private` 或 `no-store` 挡住共享缓存。

整条路径的第一步“先确认主体”还是黑盒：浏览器带来的 Cookie 怎样变成可信的 `user-17`，浏览器又替服务守住了哪些边界，见下一章[请求怎样带上可信的身份，浏览器又替服务守住哪些边界？](#35.%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E5%B8%A6%E4%B8%8A%E5%8F%AF%E4%BF%A1%E7%9A%84%E8%BA%AB%E4%BB%BD%EF%BC%8C%E6%B5%8F%E8%A7%88%E5%99%A8%E5%8F%88%E6%9B%BF%E6%9C%8D%E5%8A%A1%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%BE%B9%E7%95%8C%EF%BC%9F)。

> [!info]- 来源
> - 缓存三问、缓存键与 `Vary`、新鲜度与 age、验证、`max-age`、`no-cache`、`no-store`、`private`、`public`，以及带 `Authorization` 请求的共享缓存存储限制（“缓存复用前要回答的三个问题”“常用指令各允许什么”）：[IETF RFC 9111, HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)，2022-06，§2、§3（含 §3.5）、§4.2–§4.3、§5.2.2；`private` 与 `no-store` 的隐私限制见 §5.2.2.5、§5.2.2.7、§7.3；核对于 2026-11-12。
> - `immutable`：[IETF RFC 8246, HTTP Immutable Responses](https://www.rfc-editor.org/rfc/rfc8246.html)，2017-09，§2–§3。
> - ETag、`If-None-Match` 的弱比较、`304` 必须携带的字段、`404` 可启发式缓存（“回源验证”“用户范围的响应”）：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，2022-06，§8.8.3、§13.1.2、§15.1、§15.4.5、§15.5.5；核对于 2026-11-12。
> - 默认缓存模式下自动验证、`304` 经缓存更新后交出存储响应、请求带条件字段时缓存模式改为 `no-store`（“脚本手动加 If-None-Match”）：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，Living Standard，2026-10-19 版，HTTP-network-or-cache fetch；核对于 2026-11-12。
## 35. 请求怎样带上可信的身份，浏览器又替服务守住哪些边界？

上一章的回源验证第一步是“先确认主体”。本章打开这一步：浏览器带来的 Cookie 怎样经过登录、会话和令牌变成可信的 `user-17`，以及浏览器的几种安全控制各守哪条边界。本章产出的是“可信主体”；它不回答这个主体能否读写报表 42，那是[下一章逐次授权](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)的事。浏览器的控制也一样：它们都不授予任何访问权。

沿用[主线四的报表读取案例](#%E6%A1%88%E4%BE%8B%EF%BC%9A%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E9%87%8C%E7%9A%84%E4%B8%80%E6%AC%A1%E8%AF%BB%E5%8F%96)，本章补充三个标识：

- IdP（Identity Provider，身份提供方）的固定签发者是 `https://idp.identity.test`，BFF 在它那里登记的 client ID 是 `reports-bff-client`。
- IdP 签发的 ID Token 里，`iss` 是 `https://idp.identity.test`，代表这个人的 `sub` 是 `idp-user-4821`；应用把 `(iss, sub)` 映射到本地账户 `user-17`。
- `https://legacy.example.test` 是同一可注册域下的旧子域，由不可信的一方控制，用来检验“同站”是否等于可信。

### 会话与令牌：谁在请求

#### 登录涉及的四种凭据

一次 OIDC（OpenID Connect）登录会产生几种凭据，它们由不同的一方持有，发给不同的接收方，回答不同的问题：

| 凭据 | 谁持有、发给谁 | 接收方验证什么 | 证明什么，不证明什么 |
| --- | --- | --- | --- |
| 会话 Cookie | 浏览器发给 `reports.example.test` | BFF 用不透明 ID 查找仍有效的服务端会话 | 让 BFF 找到本地会话；不证明任何 API 权限 |
| ID Token (身份令牌) | IdP 的 Token Endpoint 发给 BFF；可选的 IdP 退出时，作为提示随浏览器顶层请求发回 IdP | 签发者、受众是本 client、时效、本次登录的 `nonce` | 把 IdP 的认证结果交给登录客户端；不替 API 授权 |
| Access Token (访问令牌) | BFF 用 `Authorization: Bearer …` 发给 API | 签名或状态、签发者、API 受众、时效、scope | 取得调用 API 的资格；不替代 API 对账户和报表的本地授权 |
| Refresh Token (刷新令牌) | BFF 只发给 IdP 的 Token Endpoint 和撤销端点 | client、grant、有效期、轮换或绑定状态 | 换取新的 Access Token；永不进入浏览器或 API |

本例选 BFF 架构：Access Token 和 Refresh Token 都留在服务端，浏览器日常只持有一个不透明的会话 Cookie。

#### 服务端会话 Cookie 怎样设计

登录成功后，BFF 生成一个新的随机会话 ID，在服务端保存会话记录，再让浏览器以后带回这个 ID：

~~~http
Set-Cookie: __Host-session=<random-opaque-id>; Path=/; Secure; HttpOnly; SameSite=Lax
~~~

会话 Cookie 的设计规则在全领域以这里为准：

| 规则 | 做法 | 理由 |
| --- | --- | --- |
| ID 只是查找键 | 用密码学安全随机数生成器生成，至少 128 位熵；不含 `user-17`、角色或账户 | 身份和权限存在服务端，不能从 ID 解码或伪造 |
| `__Host-` 前缀 | 要求同时带 `Secure`、`Path=/`，且不带 `Domain` | Cookie 只属于设置它的主机，子域不能扩大或覆盖它的作用域 |
| `Secure` | 只经 HTTPS 发送 | 不在明文链路上暴露 |
| `HttpOnly` | 脚本不能通过 `document.cookie` 读取 | 挡住 XSS 直接读值；挡不住脚本借浏览器发请求 |
| `SameSite` | 本例用 `Lax` | 限制部分跨站请求携带 Cookie；不能代替 CSRF 防护（见[第二节](#Cookie%20%E8%87%AA%E5%8A%A8%E5%8F%91%E9%80%81%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E9%98%B2%E6%AD%A2%E4%BC%AA%E9%80%A0%E5%8F%98%E6%9B%B4%EF%BC%9F)） |
| 有 Cookie 不等于已认证 | 每次请求都查服务端记录的过期时间、撤销状态和账户状态 | Cookie 只是 HTTP 字段，也可以装偏好一类的非身份数据 |
| 权限变化时换 ID | 登录成功、密码重置、权限等级变化时销毁旧 ID、签发新 ID | 防会话固定：攻击者预先塞给浏览器的匿名 ID 不能在登录后继续有效 |
| 超时由服务端执行 | 空闲超时和绝对超时都记在服务端 | 浏览器端的过期时间可被篡改或复制 |
| 退出先撤服务端 | 先撤销服务端会话记录，再让浏览器删 Cookie | 删 Cookie 只停止以后的自动发送，已被复制的旧 ID 要靠服务端拒绝 |

这个 Cookie 由 `reports.example.test` 设置并只限该主机，浏览器不会把它发给 `api.reports.example.test`。它只认证到 BFF；BFF 从服务端会话取出 API 访问令牌，再由自己调用 API。

`SameSite` 的取舍：面向 BFF 的会话 Cookie，RFC 10017 建议用 `Strict`。本例为了让用户从外部链接点进来时仍处于登录态，选了 `Lax`，于是必须对所有改变状态的请求（包括退出）校验会话绑定的 CSRF token，并精确比对 `Origin`。部署若能用 `Strict`，要按实际登录回跳路径验证体验；无论哪种，同站的兄弟子域都能发起请求，不能只靠 SameSite。登录流程里的匿名事务 Cookie 必须用 `Lax`：IdP 回调是跨站的顶层 `GET`，`Strict` 的 Cookie 不会随它带回。确需在跨站嵌入请求中携带 Cookie 时，`SameSite=None` 必须与 `Secure` 同用，浏览器的第三方 Cookie 策略仍可能阻止它。

#### Bearer 令牌：不透明令牌与 JWT

bearer token (持有者令牌) 是可重放的凭据：谁拿到，谁就能在有效期内使用。Access Token 有两种常见形态，撤销后多久被 API 察觉也不同：

- **不透明令牌**：API 调 introspection（令牌状态查询）询问 IdP。API 往往缓存查询结果；缓存越久，撤销后令牌仍被接受的窗口越长。
- **JWT（JSON Web Token）**：API 离线验证签名和声明，不必每次回 IdP。验证项包括受信密钥、允许的算法、`iss`、`aud`、令牌用途、有效期和 scope。代价是已撤销的 JWT 通常会一直被接受到过期，除非 API 另做撤销查询或拒绝列表。

JWT 是一种声明格式，不是“已验证身份”的同义词。签名只证明声明没被篡改、由受信签发者签出；载荷通常可被任何人读取，签名不提供保密性。只做 Base64URL 解码不是验签。ID Token 和 Access Token 即使都是 JWT，也要各自检查自己的受众和用途，不能互换使用。

#### BFF 还是浏览器内客户端

BFF 让令牌留在服务端。它用会话 Cookie 找到该用户的令牌集合，再把 Access Token 附到固定的 API 请求上。BFF 必须限制可代理的主机、路径和方法，否则调用方可以让它把用户令牌带到任意目标。`HttpOnly` 让脚本读不到 Cookie，却挡不住页面里的恶意脚本借浏览器会话向 BFF 发请求，所以 BFF 仍须防 XSS 和 CSRF。

另一种做法是让浏览器里的脚本直接当 OAuth 客户端。它是 public client (公开客户端)：代码在用户设备上运行，藏不住静态密钥，必须用授权码加 PKCE。把 Access Token 放进 `localStorage` 这类脚本可读的存储，一次 XSS 就能把它读走并外传。授权服务器若给公开客户端发 Refresh Token，必须用发送者约束或每次使用后轮换，以便检测重放。

#### 授权码登录：每一步防什么

OAuth 2.0 是授权框架；只有请求 `openid` scope 并按 OIDC 规则验证 ID Token，客户端才得到身份断言。本例的 BFF 是 confidential client (机密客户端)，API 是资源服务器，IdP 是固定的信任方。

下图是登录的完整往返，编号与下面的要点对应：

```mermaid
%%{init: {"sequence": {"width": 170, "actorMargin": 30, "mirrorActors": false}}}%%
sequenceDiagram
    participant B as 浏览器
    participant F as BFF
    participant A as IdP 授权端点
    participant T as IdP Token Endpoint
    B->>F: 访问登录入口
    Note over F: ① 建事务记录：<br/>state、nonce、<br/>code_verifier、预期 iss、<br/>精确回调地址、未使用标记
    F-->>B: ② 302 到 IdP<br/>Set-Cookie: __Host-oidc-tx<br/>参数：code_challenge（S256）、<br/>state、nonce、redirect_uri
    B->>A: 授权请求
    Note over B,A: 用户在 IdP 完成认证
    A-->>B: 302 到回调：code、state、iss
    B->>F: ③ GET /oidc/callback<br/>（code、state、iss）<br/>带 __Host-oidc-tx
    Note over F: iss 精确等于预期；<br/>凭 Cookie 找到事务；<br/>原子条件更新：state 匹配、<br/>未过期、未消费 → 已消费
    F->>T: ④ code、code_verifier、<br/>相同 redirect_uri、<br/>客户端认证
    Note over T: code 未用过，<br/>绑定本 client 与回调，<br/>PKCE 匹配
    T-->>F: ID Token、Access Token<br/>（可能还有 Refresh Token）
    Note over F: ⑤ 验证 ID Token（含 nonce），<br/>按 (iss, sub) 绑定 user-17
    F-->>B: ⑥ Set-Cookie: __Host-session<br/>（全新 ID）<br/>销毁匿名上下文<br/>与登录前的会话 ID
```

图上没写出的条件，以及每一步防的是什么：

1. **开始事务。** issuer、各端点、client ID 和回调 `https://reports.example.test/oidc/callback` 都取自受信配置并精确登记；事务记录短期有效，`__Host-oidc-tx` 的属性是 `Path=/; Secure; HttpOnly; SameSite=Lax`。防的是让请求参数决定 IdP 或回调地址，并把回调绑定到发起登录的那个浏览器。
2. **发起授权。** `code_verifier` 由 32 个新随机字节生成，无填充 Base64URL 编码后是 43 个字符；`code_challenge = BASE64URL(SHA-256(ASCII(code_verifier)))`。授权请求还带 `response_type=code`、`client_id` 和 `scope=openid reports.read`。必须显式发送 `code_challenge_method=S256`：省略时 RFC 7636 的默认值是 `plain`，不会自动用 SHA-256。`reports.read` 只是向 API 请求的权限范围，不证明 `user-17` 属于 `acct-17`。
3. **回调校验。** `iss` 必须存在（本例 IdP 元数据声明支持 RFC 9207，错误响应也要带 `iss`），`__Host-oidc-tx` 必须存在。`iss` 防多授权服务器的 mix-up 攻击；原子消费防并发回调重复兑换。任一项失败就停止，不兑换 code，不建会话。
4. **兑换 code。** 经已验证的 TLS 连接调用 Token Endpoint，发送 `grant_type=authorization_code`。截获 code 的人没有 verifier，兑换不了。
5. **验证身份并绑定账户。** 逐项规则见下一小节；防的是 ID Token 被替换或重放。
6. **建立新会话。** 服务端保存身份、会话 ID、有效期与 API grant 的关联；全新的会话 ID 防会话固定。

三个随机值各管一件事，不能互相代替：PKCE 把 code 的兑换绑定到这次事务；`state` 把浏览器回调绑回发起它的事务；`nonce` 把 ID Token 绑回这次认证。RFC 9700 允许在确认授权服务器支持 PKCE 时只靠 PKCE 防护回调的 CSRF；本例仍显式检查 Cookie、`state` 和 `nonce`。这些协议端点的保护，也不能代替报表业务变更请求的 CSRF 检查。

回调端点要尽量小。授权响应里的 code 可能留在浏览器历史、代理日志或 Referer 里，所以回调页不加载第三方脚本、图片和链接，设置 `Referrer-Policy: no-referrer`，日志不记录 code、`state`、令牌或 Cookie，成功后立即转到不含敏感参数的固定页面。若要回到用户原来的路径，只接受服务端允许的站内路径，不能形成开放重定向。固定回调、一次性 code、PKCE 和事务过期缩短了泄漏后的可用时间，但“浏览器绝不会留下回调 URL”不是可依赖的保证。

#### 验证 ID Token 并绑定本地账户

第 5 步在使用 ID Token 中的身份之前，按 OIDC 规则逐项验证：

- 签名和受信算法；
- `iss` 精确等于 `https://idp.identity.test`；
- `aud` 只含 `reports-bff-client`（另一部署若允许额外受众，必须逐个列入信任配置，其他值一律拒绝）；
- 有效期，以及与事务记录相同的 `nonce`；
- 若请求带了 `max_age`，还要检查 `auth_time`。

通过后，用稳定键 `(iss, sub)` 查本地绑定：只有查到 `(https://idp.identity.test, idp-user-4821) → user-17`，才认定这是 `user-17`。不要凭可能变化或未经验证的 email 自动合并账户。把一个 IdP 账户链接到已登录的本地账户时，还要求该本地账户近期有效认证并明确确认，再建立唯一的 `(iss, sub)` 绑定。

ID Token 只用来让 BFF 确认身份。IdP 没有给报表 API 签发受众和 scope 都匹配的 Access Token 时，BFF 不得把 ID Token 或其他受众的令牌送给 API。

> [!info] 单点登录不会替每个应用建立本地会话
> IdP 的 SSO（Single Sign-On，单点登录）会话能让同一浏览器访问其他已登记应用时免于重新输入密码，但 IdP 的策略、同意要求或认证时效仍可能要求再次交互。每个应用都要独立校验自己的回调、验证 ID Token、绑定本地身份、创建自己的会话。一个应用退出本地会话，不会结束 IdP 的 SSO 会话，也不会让其他应用一并退出。

> [!info] Token Endpoint 的窄例外
> OIDC Core 允许一个例外：授权码流程中，客户端经已验证的 TLS 连接直接从 Token Endpoint 收到的 ID Token，可以用 TLS 的服务器认证代替签名校验。从浏览器、其他 API 或任何不可信渠道拿到的 ID Token 不适用这条例外。

#### 调用、刷新与三种撤销

**调用 API。** 浏览器向 BFF 发只读 `GET`，自动带上 `__Host-session`；安全方法不改状态，所以不需要 CSRF token。BFF 查到有效会话后，按 Token Endpoint 返回的 `expires_in`（或经验证的令牌到期声明）维护本地到期时间；未到期才把 bearer 发给 API，已到期则先刷新，此时 API 请求还没发出。API 仍是最终验证者：它验证 Access Token，把令牌代表的主体映射为 `user-17`，再按当前成员关系、报表归属和动作授权。

**刷新令牌。** 刷新有两个竞争要处理：多个请求同时发现令牌到期，以及刷新进行中用户退出了。

1. BFF 以 grant 为单位取得刷新锁，或把并发请求合并到同一次进行中的刷新；其他进程上的请求等刷新结束后重读会话，避免同一个旧 Refresh Token 被并发提交。
2. 持锁者经可信 TLS 连接、以机密客户端认证向 Token Endpoint 发送 Refresh Token。
3. 成功时，在释放锁之前以“会话仍有效，且 grant 版本与发起刷新时相同”为条件，原子写回新的 Access Token；IdP 若轮换了 Refresh Token，也在同一次更新里替换。条件不成立就丢弃结果、停止本次调用，迟到的刷新响应不能复活已退出或已撤销的会话。
4. 只有条件写回成功后，才用新令牌第一次发送原来的 API 请求。

刷新失败要按原因处理。没有 Refresh Token，或 IdP 明确返回 `invalid_grant`（grant 已失效、过期或撤销），本例停止 API 调用并要求重新授权；本例的 grant 与会话绑定，失效 grant 也结束这条令牌会话。网络超时、`5xx` 或其他不表示 grant 失效的结果，只让本次调用失败：不能据此推断 grant 失效，也不要盲目重发旧 Refresh Token。

![Access Token 到期时 BFF 在服务端加锁刷新，按 invalid_grant、成功与超时分支处理](../../engineering-foundations/services/resources/web-sessions-and-oidc-refresh.svg)

**三种撤销是三件事。** “退出”可能指三种不同的操作，撤销的对象和可见性各不相同：

| 操作 | 撤销什么 | 什么仍可能有效 |
| --- | --- | --- |
| 撤销本地会话 | BFF 的服务端会话记录；随后清除 Cookie | 已签发给 BFF 的令牌在 IdP 侧仍有效，除非另行撤销 |
| 撤销 Refresh Token | 向 IdP 撤销端点提交 RFC 7009 撤销请求 | 同一 grant 已签发的 Access Token：IdP 是否一并撤销由 IdP 决定；离线验证 JWT 的 API 通常接受到令牌过期 |
| 结束 IdP 的 SSO 会话 | 顶层导航到 IdP 的 `end_session_endpoint` | 其他应用的本地会话，除非另配前通道或后通道退出联动 |

RFC 7009 的撤销响应语义在全领域以这里为准：`200` 只表示请求被处理，不说明令牌在撤销前一定有效，也不说明它刚刚才失效；`503` 表示客户端应假定令牌仍然有效，可以稍后重试。撤销 Refresh Token 不等于撤销已经签发的 JWT Access Token。API 若每次查询令牌状态，可在 IdP 撤销生效后拒绝；introspection 结果被缓存时会有观察延迟。API 对 `acct-17` 报表的授权仍由 API 按自己的数据作出，不会因为浏览器删了 Cookie 而失效。

本例的退出流程：

1. 页面用 `fetch` 向 BFF 发 `POST /logout`，带会话 Cookie、自定义 CSRF 头和精确的 `Origin`；BFF 先完成这些校验。
2. 若本次要请求 IdP 退出，BFF 从活动会话取出已验证的 ID Token 作为 `id_token_hint`，为一次性退出 `state` 建短期事务；若要撤销上游令牌，先保存要提交的 Refresh Token。
3. 撤销服务端本地会话。此后即使旧 Cookie 被复制，服务端也拒绝它。
4. 响应 `200` JSON：清除 `__Host-session`，设置 host-only 的 `__Host-oidc-logout-tx`（`Secure; HttpOnly; Path=/; SameSite=Lax`），并返回用受信 IdP 元数据中 HTTPS `end_session_endpoint` 拼好的退出地址，含 `id_token_hint`、精确登记的 `post_logout_redirect_uri` 和 `state`。不请求 IdP 退出时，只清 Cookie 并返回已退出状态。
5. 页面执行 `window.location.assign(logoutUrl)` 做顶层导航。`fetch` 自己跟随 302/303 只处理那次 fetch 的重定向，不会把当前页面带到 IdP。
6. IdP 回跳到登记的地址（顶层 `GET`，`Lax` 的事务 Cookie 随之带回），BFF 用 Cookie 找到事务，精确比对并原子消费 `state`。
7. 独立地，BFF 可经 HTTPS 以机密客户端凭据向 IdP 撤销端点提交 Refresh Token。远端不可用不影响本地会话已撤销，但不能宣称上游令牌已即时撤销。

`id_token_hint` 只发给固定的 IdP 退出端点，不发给 API，也不是 API 凭据；页面和回调使用 `Referrer-Policy: no-referrer`。单个应用退出不构成全局退出。

![本地退出、可选的 IdP SSO 退出与单独的令牌撤销各自产生的结果](../../engineering-foundations/services/resources/web-sessions-and-oidc-logout.svg)

#### 本地密码：慢哈希与在线限速

应用自己验证密码时，数据库存的是带随机盐的专用密码哈希及其算法和成本参数，不存明文，也不用快速通用散列。两种防护针对不同攻击：数据库泄漏后，攻击者能离线反复猜，Argon2id 这类慢哈希用内存和计算成本让每次猜测更贵；在线登录入口则靠限速挡住在线猜测。OWASP 当前给出的 Argon2id 基线示例是 19 MiB 内存、2 次迭代、并行度 1，部署应按自己的硬件和并发调优，不要把最低示例当目标。salt 不需要保密；可选的 pepper 是数据库之外的服务端秘密，需要保护、轮换和恢复方案。

密码验证成功后，同样要销毁匿名会话 ID、签发新的随机 ID、建立有服务端超时的本地会话。它只代表本地认证，不会凭空产生 ID Token、OAuth grant 或 API Access Token。

### 浏览器边界：各守什么、都不授予什么

会话把请求连到了可信主体。浏览器另有几种安全控制，各自只守一条边界。下表是本节的总览，后面逐条展开：

| 边界 | 控制与成立条件 | 失败时会怎样 | 它不负责什么 |
| --- | --- | --- | --- |
| 网络链路 | HTTPS 证书身份匹配 + TLS 保护（见 [TLS 证明什么](#TLS%20%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88)） | 连接终止或显示证书错误；退回明文则链路保护消失 | 识别应用用户，判断能否读报表 |
| 页面解释数据 | 按目标上下文使用安全的 DOM 接口或编码；富文本另行消毒 | 不可信标记被 HTML 解析，生成元素、事件处理器或脚本 | 限制已经在运行的同源脚本 |
| Cookie 自动发送 | 状态变更前，服务端校验 CSRF token 或精确来源 | Cookie 仍随请求到达；防护漏掉时伪造操作进入业务逻辑 | 认证本身、对象授权、脚本注入 |
| 跨源读取 | 预检允许本次方法与请求头；实际响应的来源与凭据字段匹配 | 预检失败则不发实际请求；实际响应检查失败则脚本读不到 | 拦住所有请求、管住非浏览器客户端、授权报表 |
| 页面嵌入 | 响应的 CSP `frame-ancestors` 允许每一层祖先来源 | 浏览器拒绝在该框架中呈现页面 | API、附件和后台任务的服务端权限 |

#### 不可信报表标题怎样安全显示？

XSS（Cross-Site Scripting，跨站脚本）发生在不可信数据变成可执行内容的时候。假设报表 42 的标题被改成了 `<img src=x onerror=alert(1)>`。`textContent` 把整串当普通字符放进标题元素；`innerHTML` 则把它交给 HTML 片段解析器，生成一个 `img` 元素和 `onerror` 处理器。图片加载失败、又没有有效策略拦住内联处理器时，`alert(1)` 就会运行。

![同一标题经 textContent 成为文本，经 innerHTML 被解析为带事件处理器的图像元素](../../engineering-foundations/services/resources/web-browser-security-boundaries-xss.svg)

安全显示的规则按入口分：

- **普通文本**：用框架默认的文本插值或普通元素的 `textContent`。
- **HTML 属性**：固定元素名和属性名，用该属性上下文对应的编码。属性编码不检查 URL 的语义，`javascript:` 这类地址要另行校验。
- **不要拼进去的地方**：脚本、事件处理器、CSS 规则、标签名、属性名。
- **富文本**：只有产品确实支持用户撰写富文本时，才用维护中的 HTML 消毒器过滤允许的元素和属性；清理之后再改写内容可能重新引入风险。
- **执行入口**：框架的 raw HTML 入口同样需要上述检查；不要把不可信字符串交给 `document.write`、`eval` 或 `new Function`，文本插值的安全性不会传递到这些入口。

CSP（Content Security Policy）的脚本指令可以限制内联脚本和脚本来源，降低某些注入的可利用性。它是纵深防御，不能让 `innerHTML` 变成安全的文本接口。恶意脚本一旦在 `reports.example.test` 上运行，就能以页面的身份调用 BFF；`HttpOnly` 只让它读不到 Cookie 值，挡不住它调用 `fetch` 让浏览器代发 Cookie。所以注入点必须修复，服务端也必须逐次授权。

#### origin 与 site：同站子域不可信

origin (源) 由协议、主机和端口组成。site (站点) 按 schemeful site 判定：比较协议和可注册域，不比较端口，同一可注册域下的 HTTPS 子域属于同站。于是 `https://legacy.example.test` 和 `https://reports.example.test` 是不同 origin，却是同 site；`api.reports.example.test` 也和它们同站。

子域可以由不同团队、其他客户或旧系统控制，“同站”不能当作同源或可信身份。`__Host-` 前缀保证旧子域不能把会话 Cookie 的作用域扩大或覆盖到 `reports.example.test`；但用户登录后，浏览器只要主机、路径、`Secure` 和 SameSite 等条件匹配，就会把 Cookie 自动附到发往 `reports.example.test` 的请求上。控制旧子域的人不必读到 Cookie，就可能借用户的现有会话发请求。

#### Cookie 自动发送时，怎样防止伪造变更？

CSRF（Cross-Site Request Forgery，跨站请求伪造）利用浏览器自动携带的登录凭据，让别的页面发起用户并不想要的变更。为展示状态变化，设 BFF 有一个书签端点：`user-17` 可以把报表 42 置顶到自己的书签，初始 `pinned=false`，端点接受表单编码 `pinned=true`。用户直接打开了旧子域的页面，它提交了一个普通表单：

~~~html
<form action="https://reports.example.test/v1/accounts/acct-17/reports/42/bookmark" method="post">
  <input name="pinned" value="true">
</form>
<script>document.forms[0].submit();</script>
~~~

两个页面都是 HTTPS 且同站，所以即使会话 Cookie 是 `SameSite=Lax`，这个同站表单 POST 照样带着 Cookie。表单编码属于浏览器可以直接提交的格式，不需要 CORS 预检。攻击页面不需要读回响应，副作用就可能已经发生。

![同站旧子域的表单 POST 带着会话 Cookie 到达 BFF；来源校验拦下变更，漏检则书签被置顶](../../engineering-foundations/services/resources/web-browser-security-boundaries-csrf.svg)

BFF 的处理顺序是：先从会话 Cookie 得到 `user-17`，再检查这个主体能否执行书签操作，然后在变更之前做防伪校验。应用要选定一种策略，并在所有变更接口上贯彻：

- **会话绑定的 CSRF token**：服务端为每个已登录会话生成随机值，放在页面启动数据里；页面在非安全方法的自定义请求头中回传，BFF 与服务端会话里的值比较。攻击页面跨源读不到这个值。传统表单若用 token 作主要校验，必须把有效 token 放进表单。
- **精确来源校验**：只接受精确的 `https://reports.example.test`，拒绝缺失、`null` 或不匹配的 `Origin`。

本例因为会话 Cookie 选了 `Lax`，两者都做：所有状态变更（含退出）既校验 token，也精确比对 `Origin`。图中旧子域的 `Origin` 不匹配，请求在变更前被拒，书签保持 `pinned=false`；漏掉检查的实现则会把它改成 `true`。通过校验只说明请求过了这道防伪检查，不证明用户确实想做这件事。OIDC 的 `state` 只保护登录回调，不能拿来代替应用的 CSRF token。

SameSite 的局限要记清：

- `Lax` 通常会限制真正跨站的不安全方法请求，但允许符合规则的跨站顶层安全方法导航带 Cookie。所以 `GET` 等安全方法绝不能改状态。
- `Lax` 和 `Strict` 都不拦同站子域发起的请求，上面的表单就是例子。
- `SameSite=None` 必须配 `Secure`，而且应用仍须单独防 CSRF。
- 同源 XSS 已经执行时，恶意脚本能读出页面里的 token、调用正常接口。CSRF token 不是 XSS 的修复。

#### 跨源读取：请求到达和响应可读是两件事

same-origin policy (同源策略，SOP) 默认限制的是页面脚本**读取**另一个 origin 的响应，而不是阻止请求**发出**。上一节的表单 POST 就是证据：它跨源到达了服务器，只是攻击页面读不到响应。CORS（Cross-Origin Resource Sharing）是对“读取”这一限制的受控放行。理解 CORS 先记住这条区分：一个请求可能已经到达并执行，而脚本仍然读不到结果。

本例的页面经同源 BFF 访问 API，不需要 CORS。为说明 CORS，看一个变体部署：页面脚本从 `https://reports.example.test` 直接跨源调用 `https://api.reports.example.test`，API 自己设置了一个 host-only 会话 Cookie `__Host-api-session`。

~~~javascript
const response = await fetch('https://api.reports.example.test/v1/accounts/acct-17/reports/42', {
  credentials: 'include',
  headers: { 'X-Report-View': 'compact' },
});
~~~

跨源 Fetch 默认不带目标源的 Cookie，这里显式用了 `credentials: "include"`。`X-Report-View` 不在 CORS 的安全请求头列表里，于是这次请求要过两道检查。

**第一道：预检。** 没有可用的预检缓存时，浏览器先发一个不带用户 Cookie 的 `OPTIONS`，问 API 是否允许这个来源、方法、请求头和凭据模式：

~~~http
OPTIONS /v1/accounts/acct-17/reports/42 HTTP/1.1
Origin: https://reports.example.test
Access-Control-Request-Method: GET
Access-Control-Request-Headers: x-report-view

HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://reports.example.test
Access-Control-Allow-Methods: GET
Access-Control-Allow-Headers: X-Report-View
Access-Control-Allow-Credentials: true
Vary: Origin
~~~

![带自定义头的跨源 Fetch 先发不带 Cookie 的 OPTIONS；预检通过才发实际 GET，否则 Fetch 拒绝](../../engineering-foundations/services/resources/web-browser-security-boundaries-cors.svg)

预检不通过，浏览器就不发这个带自定义头的实际请求，`fetch` 以 `TypeError` 拒绝。

**第二道：实际响应。** 预检通过后，浏览器发实际 `GET`。两个 HTTPS 子域同站，Cookie 其余条件也满足，所以请求带上 `__Host-api-session`。API 照常认证 Cookie，确认 `user-17` 当前属于 `acct-17` 且有 `report:read`，再按账户和 ID 读报表 42。只有在允许分享结果时，实际响应才带上匹配的 CORS 字段：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: https://reports.example.test
Access-Control-Allow-Credentials: true
Vary: Origin
~~~

![实际 GET 已到达 API 并经过身份与资源授权；响应的 CORS 字段再决定脚本能否读到状态和正文](../../engineering-foundations/services/resources/web-browser-security-boundaries-cors-response.svg)

带凭据的请求，响应必须给出精确的允许来源和小写字面值 `true`，不能用 `Access-Control-Allow-Origin: *`。实际响应缺少或不匹配这两个字段时，即使服务器已经返回 `200`、请求也已完成读取，`fetch` 仍以 `TypeError` 拒绝，脚本看不到状态和正文。反过来，隐藏式 `404` 若要让页面识别，也得带上可读的 CORS 字段；这时 `fetch` 正常返回 `Response`，`status === 404`、`ok === false`，不是 CORS 造成的网络错误。

两道检查的失败都不能代替 API 的认证和授权：预检失败的请求没发出，但没有预检的简单请求（如上一节的表单）会先到服务器。CORS 是浏览器把跨源响应分享给脚本的协议，不是网络防火墙，管不住 `curl` 这类客户端，也不替服务端授权。`Vary: Origin` 与私有数据的缓存字段见[缓存章](#%E7%94%A8%E6%88%B7%E8%8C%83%E5%9B%B4%E7%9A%84%E5%93%8D%E5%BA%94%E6%80%8E%E6%A0%B7%E5%86%99%E7%BC%93%E5%AD%98%E5%AD%97%E6%AE%B5)。像本例主线那样把 API 反向代理到页面同源的路径下，可以省去这次协商；会话必须建立在页面主机上，因为 API 主机的 host-only Cookie 不会发给页面主机。

> [!info] Fetch 对 Cookie 字段的边界
> `Cookie` 请求字段由浏览器按目标 URL 和 Cookie 规则管理，网页脚本不能用 Fetch 或 XHR 手动设置。`Set-Cookie` 是禁止暴露给脚本的响应字段，加 `Access-Control-Expose-Headers` 也读不到，与 Cookie 是否 `HttpOnly` 无关。

#### 页面能被谁嵌入？

clickjacking (点击劫持) 把真实页面放进攻击者控制的框架里，诱导用户点错位置。报表页用响应头限制哪些祖先来源可以嵌入它：

~~~http
Content-Security-Policy: frame-ancestors 'self'
~~~

这里只允许同源祖先；任何一层祖先来源不匹配，浏览器就拒绝在该框架里呈现报表。`frame-ancestors` 必须用响应头发送，写在 `meta` 元素里不生效。需要兼容旧客户端时，可另行评估 `X-Frame-Options`，并在目标浏览器上验证。嵌入控制只防报表界面被伪装成按钮，不阻止攻击者直接请求 API，也不替 API 检查报表 42 的权限。WebSocket 握手的来源校验见[实时通道支线](#WebSocket%20%E6%80%8E%E6%A0%B7%E5%BB%BA%E7%AB%8B%E8%BF%9E%E6%8E%A5%E5%B9%B6%E6%8C%81%E7%BB%AD%E6%8E%88%E6%9D%83)。

#### 同一页面加载的远程脚本共享宿主权限

前端按团队拆成独立部署的部分（例如微前端）时，信任边界取决于运行位置，而不是脚本从哪里下载。在同一页面加载的远程脚本，与宿主共享同一文档的全部权限；从另一个 origin 下载脚本不构成隔离。只有跨源 iframe 或另一 origin 的独立文档才建立 origin 边界，那时要单独设计跨源消息、身份和 API 访问。同页的子应用之间，只传资源 ID、非敏感显示数据和受限的数据访问接口，不把会话凭据放进路由、DOM 或共享状态广播。客户端“能显示某个路由”不代替服务端授权；服务端的拒绝要按拒绝呈现，不要误判成代码加载失败、再静默切到另一个版本。

### 下一步：可信主体交给逐次授权

本章交出两样东西。第一，一个可信主体：BFF 通过会话 Cookie 找到服务端会话，会话里是经 OIDC 验证并按 `(iss, sub)` 绑定的 `user-17`，以及只在服务端使用的 API 令牌；API 再从 Access Token 认出同一主体。第二，一张边界清单：TLS、安全呈现、CSRF 防护、CORS 和 `frame-ancestors` 各守一条边界，没有一项授予访问权。

接下来的问题是：这个主体能不能对 `acct-17` 的报表 42 做这个动作？路径里的账户号和报表号仍是未可信输入。见[服务怎样逐次确认这个主体能对这份资源做这个动作？](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)

> [!info]- 来源
> - 会话 Cookie 属性、`__Host-` 前缀与 SameSite 发送条件（“服务端会话 Cookie 怎样设计”“origin 与 site”“CSRF”）：[IETF RFC 6265](https://www.rfc-editor.org/rfc/rfc6265.html)，§4–§5；[draft-ietf-httpbis-rfc6265bis-22](https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-rfc6265bis-22)，2025-12，§4.1.2.5–§4.1.3.2、§5.6.7、§8.8。核对于 2026-11-13：后者仍是 Internet-Draft，尚未作为 RFC 发布。
> - BFF 架构、服务端令牌、会话 Cookie 建议（含 `Strict`）、刷新与 CSRF 要求（“BFF 还是浏览器内客户端”“SameSite 的取舍”）：[IETF RFC 10017, OAuth 2.0 for Browser-Based Applications](https://www.rfc-editor.org/rfc/rfc10017.html)，BCP 212，2026-08，§6.1.1–§6.1.3。
> - 会话 ID 熵、权限变化后轮换、服务端失效与超时：[OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)，Session ID Entropy、Renew the Session ID After Any Privilege Level Change、Session Expiration；核对于 2026-11-12。
> - 不透明令牌 introspection：[IETF RFC 7662](https://www.rfc-editor.org/rfc/rfc7662.html)，§2.2；JWT 验证算法与用途隔离：[IETF RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html)，§3；Bearer 请求头：[IETF RFC 6750](https://www.rfc-editor.org/rfc/rfc6750.html)，§2.1。
> - 授权码请求与兑换（“授权码登录”）：[IETF RFC 6749](https://www.rfc-editor.org/rfc/rfc6749.html)，§4.1.1–§4.1.4；PKCE 与 `S256`、默认 `plain`、verifier 长度：[IETF RFC 7636](https://www.rfc-editor.org/rfc/rfc7636.html)，§4.1–§4.3、Appendix B；`iss` 参数防 mix-up：[IETF RFC 9207](https://www.rfc-editor.org/rfc/rfc9207.html)，§2；资源指示：[IETF RFC 8707](https://www.rfc-editor.org/rfc/rfc8707.html)，§2；精确回调、state/PKCE、code 与 Referer 泄漏、开放重定向、受众限制、公开客户端的 Refresh Token 保护：[IETF RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)，2025-01，§2.1–§2.3、§4.1–§4.5、§4.11、§4.14。
> - ID Token 验证、可依赖的 claim、Token Endpoint 的 TLS 例外（“验证 ID Token 并绑定本地账户”）：[OpenID Connect Core 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html)，2023-12-15，§3.1.2.1、§3.1.3.7、§5.7；联邦账户不按 email 自动合并、链接前要求本地认证：[OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)，Secure Federated Account Linking；核对于 2026-11-12。
> - RP 发起的退出、`id_token_hint` 与 `post_logout_redirect_uri`（“三种撤销”）：[OpenID Connect RP-Initiated Logout 1.0](https://openid.net/specs/openid-connect-rpinitiated-1_0-final.html)，§2–§3；令牌撤销与 `200`/`503` 语义：[IETF RFC 7009](https://www.rfc-editor.org/rfc/rfc7009.html)，§2。
> - Argon2id 参数、盐与 pepper（“本地密码”）：[OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)，Argon2id、Peppering；核对于 2026-11-12。
> - origin 与 schemeful site（“origin 与 site”）：[WHATWG HTML Standard, Origins](https://html.spec.whatwg.org/multipage/browsers.html#origins)，Living Standard，§7.1.1，核对于 2026-11-12。
> - 安全 DOM 接口、上下文编码、危险上下文、富文本消毒、CSP 纵深防御（“不可信报表标题怎样安全显示？”）：[OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)，Safe Sinks、Output Encoding、Dangerous Contexts、HTML Sanitization、Other Controls；核对于 2026-11-12。
> - Synchronizer token、请求头回传、精确 Origin 校验与 SameSite 的局限（“CSRF”）：[OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)，Synchronizer Token Pattern、Using Standard Headers to Verify Origin、Limitations of SameSite；核对于 2026-11-12。
> - 预检、CORS 凭据与实际响应检查、`Cookie`/`Set-Cookie` 字段限制（“跨源读取”）：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/#cors-protocol)，Living Standard，2026-10-19 版，§2.2.2、§3.1、§3.3.1–§3.3.5、§4.8–§4.10。
> - `frame-ancestors` 的祖先匹配与 `meta` 不生效（“页面能被谁嵌入？”）：[W3C Content Security Policy Level 3](https://www.w3.org/TR/CSP3/#directive-frame-ancestors)，Working Draft，2026-10-27，§6.4.2。
> - 远程脚本共享宿主权限、跨源 iframe 才建立 origin 边界、服务端逐次授权（“同一页面加载的远程脚本”）：[OWASP Micro Frontend Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Micro_Frontend_Security_Cheat_Sheet.html)，Choose and Enforce Runtime Boundaries、Authorize Every Request on the Server；核对于 2026-11-12。
## 36. 服务怎样逐次确认这个主体能对这份资源做这个动作？

上一章交出了可信主体：BFF 从会话认出 `user-17`，API 从 Access Token 认出同一主体。本章回答剩下的问题：这个主体此刻能不能对这份资源执行这个动作。authentication (认证) 确认请求代表谁，authorization (授权) 判断这个主体现在能否对指定资源做指定动作。本章是逐次授权的权威位置：一套五步骨架，以及它在数据库查询、应用缓存和后台任务上的落点。

### 案例：同一条路径，不同的主体

沿用[主线四的报表读取案例](#%E6%A1%88%E4%BE%8B%EF%BC%9A%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E9%87%8C%E7%9A%84%E4%B8%80%E6%AC%A1%E8%AF%BB%E5%8F%96)，本章引入另一个账户的主体 `user-29`：他属于账户 `acct-29`，已经正常登录，与 `acct-17` 没有任何成员关系；`acct-29` 有自己的报表 73（`Usage summary`）。账户 `acct-17` 里没有报表 43，它用来对照“不存在”。两个账户的角色如下：

| 角色 | 允许的动作 | 本例谁持有 |
| --- | --- | --- |
| `viewer` | `report:read` | `user-29` 在 `acct-29` |
| `analyst` | `report:read`、`report:export` | `user-17` 在 `acct-17` |

几次请求和本例的结果：

| 请求 | 当前数据 | 结果 |
| --- | --- | --- |
| `user-17` 读 `GET /v1/accounts/acct-17/reports/42` | 是 `acct-17` 的 `analyst`，报表 42 属于 `acct-17` | `200`，返回 `Service health` |
| `user-17` 读 `acct-17` 的报表 43 | 成员关系有效，但 `acct-17` 没有 43 | `404` |
| `user-29` 读 `acct-17` 的报表 42 | 没有 `acct-17` 的成员关系 | 与报表 43 完全相同的 `404` |
| `user-29` 读 `acct-29` 的报表 42 | 是 `acct-29` 的成员，但 42 不属于 `acct-29` | `404`，不会去读 `acct-17` 的 42 |
| 没有有效会话的请求 | — | `401` 加 `WWW-Authenticate` |
| `user-17` 被移出 `acct-17` 后重读，或他提交的导出任务开始执行 | 成员关系已撤销 | API 回 `404`；任务以 `authorization_revoked` 失败 |

### 认证之后，请求里的一切仍是输入

“已登录”只说明主体是谁，不说明他能读这份报表。路径、查询参数、正文、缓存键、队列消息里出现的用户 ID、账户 ID、角色名和报表编号，都是调用方或上游写进去的值，不能自己证明权限。`GET /v1/accounts/acct-17/reports/42` 里的 `acct-17` 是调用方选择的范围，`42` 是调用方选择的资源编号；服务端要用自己的当前数据核实二者。

### 逐次授权的五步

每个请求都按下面五步检查，全领域以这里的骨架为准，本章后续各节逐步展开：

1. **从凭据得到可信主体。** 认证层把会话或访问令牌映射为主体（见[上一章](#%E4%BC%9A%E8%AF%9D%E4%B8%8E%E4%BB%A4%E7%89%8C%EF%BC%9A%E8%B0%81%E5%9C%A8%E8%AF%B7%E6%B1%82)）。不要把请求头或正文里的 `user_id` 当作登录结果。
2. **查主体在所选账户里的当前成员关系。** 路径里的 `acct-17` 只是用户选的范围；一个人可以在不同账户有不同角色，客户端报来的账户和角色都不能代替服务端当前状态。
3. **把动作和对象一起检查，默认拒绝。** `analyst` 能 `report:read` 和 `report:export`，不因此获得 `report:edit` 或成员管理；没有明确授予的动作一律拒绝。
4. **按账户限定读取对象。** 数据按 `(account_id, report_id)` 过滤。不要先按全局编号把对象装进内存，再靠隐藏链接、难猜的 ID 或界面隐藏完成授权。
5. **旁路走同一条件。** 应用缓存、附件、导出结果、后台任务，每一条旁路都要确认同样的条件确实生效。worker 的服务账号按最小权限配置，只限制 worker 自己能调用什么服务，不能代替对最终用户的资源授权。

![已验证主体与调用方路径各自进入检查：查当前成员与动作，通过后才按账户取数](../../engineering-foundations/services/resources/web-security-and-authentication-request.svg)

### 角色能给什么，资源检查还要补什么

RBAC（Role-Based Access Control，基于角色的访问控制）用 `viewer`、`analyst` 这样的角色归纳允许的动作，适合表达账户成员的常见权限，对应第 3 步的“动作”。它有两个盲区：角色不能证明报表 42 属于当前账户，那是第 4 步的事；角色也挡不住成员关系变旧，那要求第 2 步每次都查当前数据。产品若加入单份报表分享、部门属性或其他关系条件，就要把这些条件加进对象访问判断，这类做法通常称 ABAC（基于属性）或 ReBAC（基于关系）的访问控制。

### 隐藏式 404 还是 403

请求被拒时返回哪个状态码，是一项策略选择，全领域以这里的规则为准：

- **先认证。** 没有有效凭据就回 `401`，并带适用的 `WWW-Authenticate` 质询，例如 `Bearer realm="reports"`。认证先于一切，所以未认证的请求即使带了非数字的报表 ID，也回 `401`，而不是参数错误。
- **对象不可见时隐藏存在性。** 主体没有所选账户的成员关系、没有读权限，或者报表在该账户内不存在，统一回 `404`，状态码、Problem `type` 和中性的 `detail` 完全相同。本例 `user-29` 读 `acct-17` 的报表 42，与 `user-17` 读不存在的报表 43 得到同一个响应，`user-29` 无法据此猜出 42 存在。
- **存在性已无需隐藏时用 `403`。** 主体已经能看到这个对象，只是缺少某个动作的权限，例如 `viewer` 请求导出自己能读的报表 73，回 `403` 说明“已识别身份，但拒绝这个动作”。允许披露资源存在的端点也可以一律用 `403`。

~~~http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json
Cache-Control: private, no-store

{"type":"https://api.reports.example.test/problems/not-found","title":"Report not found","status":404,"detail":"No report is visible under this identifier."}
~~~

隐藏式 `404` 是用户范围的结果，要显式禁止存储，理由见[缓存章](#%E7%94%A8%E6%88%B7%E8%8C%83%E5%9B%B4%E7%9A%84%E5%93%8D%E5%BA%94%E6%80%8E%E6%A0%B7%E5%86%99%E7%BC%93%E5%AD%98%E5%AD%97%E6%AE%B5)。隐藏规则还决定了多个错误同时成立时的顺序：一个隐藏对象即使带着过时的版本标签，也先回 `404`，不能用 `412` 暗示它存在，完整的优先级见[API 契约章](#%E5%A4%9A%E4%B8%AA%E9%94%99%E8%AF%AF%E5%90%8C%E6%97%B6%E6%88%90%E7%AB%8B%E6%97%B6%E5%85%88%E6%8A%A5%E5%93%AA%E4%B8%AA)。

### 按账户过滤读取：参数绑定和主键都不是授权

第 4 步的查询把账户和报表编号分别作为绑定参数传入（`?` 是 SQLite 的占位符，其他驱动写法不同）：

~~~sql
SELECT id, title, body
FROM reports
WHERE account_id = ? AND id = ?;
~~~

参数绑定和授权解决两个不同的问题。参数绑定防止输入改写 SQL 语法；授权决定当前主体能否读取绑定后的那一行。绑定了参数、却只按 `id = 42` 读，照样越权；做了授权、却拼接 SQL，照样会被注入。动态排序字段这类标识符通常不能作为普通参数绑定，要从固定的允许列表里选。

只按全局主键取对象是常见漏洞：ORM 的“按主键获取”一类接口只看 ID，不会替你加账户条件。主线五的调试章就以这样一次回归建案，见[怎样把一份缺陷报告变成可证伪的反例？](#52.%20%E6%80%8E%E6%A0%B7%E6%8A%8A%E4%B8%80%E4%BB%BD%E7%BC%BA%E9%99%B7%E6%8A%A5%E5%91%8A%E5%8F%98%E6%88%90%E5%8F%AF%E8%AF%81%E4%BC%AA%E7%9A%84%E5%8F%8D%E4%BE%8B%EF%BC%8C%E5%B9%B6%E7%94%A8%E8%AF%81%E6%8D%AE%E5%AE%A1%E6%9F%A5%E4%BF%AE%E5%A4%8D%EF%BC%9F)。若把主键改成复合键 `(account_id, id)`，让编号按账户分区，它也只约束数据形状，不判断当前用户能否读这一行；查询仍要保留两个谓词，队列里的任务引用也按同一组身份解析。

### 旁路一：应用缓存先授权，再查缓存

这里说的是服务端的应用数据缓存，不是浏览器或共享 HTTP 缓存。API 先重查当前成员关系和 `report:read`，只有通过后，才用包含账户和主体的键查缓存，例如 `(acct-17, user-17, 42)`；未命中时按账户和 ID 执行 SQL，只有读到属于该账户的行，才填充同一范围的缓存。缓存键限制了副本的范围，但它本身不是授权凭据：撤权后旧正文可能还在缓存里，API 照样在查缓存之前回 `404`。

缓存命中还依赖对象身份不变。系统若允许删除、迁移报表或复用编号，命中前必须核验仍是同一个对象及其当前访问规则，或在变更时可靠地让相关副本失效。缓存键要包含哪些维度、写后多久失效，见[加了缓存之后，读到的数据最多会旧多久？](#30.%20%E5%8A%A0%E4%BA%86%E7%BC%93%E5%AD%98%E4%B9%8B%E5%90%8E%EF%BC%8C%E8%AF%BB%E5%88%B0%E7%9A%84%E6%95%B0%E6%8D%AE%E6%9C%80%E5%A4%9A%E4%BC%9A%E6%97%A7%E5%A4%9A%E4%B9%85%EF%BC%9F)。

### 旁路二：导出任务在受理和执行时各授权一次

导出是一项单独的动作，需要 `report:export`，不能从 `report:read` 推出。`user-17` 提交 `POST /v1/accounts/acct-17/reports` 请求导出报表 42 时：

1. **受理前授权。** 按五步检查 `user-17` 能否在 `acct-17` 导出报表 42，再检查时间范围、格式、页数等上限，把影响执行的参数规范化。从参数已能判定超限的，在受理前就拒绝。
2. **服务端保存可信任务记录。** 记录请求人、账户、动作和报表编号。队列消息只携带任务 ID；worker 按 ID 取回记录，不把消息正文当作这些字段的权威来源。任务 ID 只是定位值，不是权限凭据。
3. **执行时重查当前权限。** 本例选择“执行时仍须有权限”：worker 用自己的服务身份读数据之前，按记录的主体和账户重查当前成员关系与 `report:export`。权限已撤销时不读数据，直接提交一个明确的失败结果 `authorization_revoked`。

![导出任务受理前授权并保存记录；队列只传任务 ID；worker 执行前重查权限，撤权则拒绝](../../engineering-foundations/services/resources/web-security-and-authentication-worker.svg)

“当前”指 worker 检查时读到的成员状态。若生产环境的读副本或授权缓存会滞后，撤权最晚多久生效要明确写出；已通过检查的执行是否中途停止，也要按产品定义。另一种产品选择是“已受理的任务继续执行”，那就必须持久保存一份可审计的受理授权决定，并写明后续读取、导出这些副作用还受哪些控制。

任务受理之后还有几个端点，每个都单独授权：查询状态、请求取消、下载结果，都要检查调用者对这个任务和结果的当前访问权，路径里的账户号和任务 ID 不是凭据。下载若改用预签名 URL，它就成了持有者凭据：谁拿到链接，谁就能在有效期内下载，服务端不再逐次检查身份，见[服务该跑在哪种运行时上，平台怎样启动、探测和停止它？](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)。任务怎样被持久受理、唤醒和执行，从[未知结果章](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)开始讲。

### 实例：用 SQLite 复现五步与撤权

下面的复现用 Python 3.11 标准库 `sqlite3` 和合成数据，把开头的结果表逐行变成断言。`verified_subject` 视为认证中间件已经验证的主体，复现不实现 Cookie 或签名令牌；路径里的账户值仍是调用方输入，只有成员查询通过后才成为有效范围。直接函数调用代替了队列投递。

> [!example]- SQLite 授权、隐藏式 404、403 与撤权复现
>
> ~~~python
> import sqlite3
>
> db = sqlite3.connect(":memory:")
> db.executescript("""
> CREATE TABLE memberships (
>     account_id TEXT NOT NULL, subject TEXT NOT NULL, role TEXT NOT NULL,
>     PRIMARY KEY (account_id, subject)
> );
> CREATE TABLE reports (
>     id INTEGER PRIMARY KEY, account_id TEXT NOT NULL,
>     title TEXT NOT NULL, body TEXT NOT NULL
> );
> CREATE TABLE jobs (
>     id INTEGER PRIMARY KEY, account_id TEXT NOT NULL, requester TEXT NOT NULL,
>     action TEXT NOT NULL, report_id INTEGER NOT NULL
> );
> INSERT INTO memberships VALUES ('acct-17', 'user-17', 'analyst');
> INSERT INTO memberships VALUES ('acct-29', 'user-29', 'viewer');
> INSERT INTO reports VALUES (42, 'acct-17', 'Service health', 'Synthetic data A');
> INSERT INTO reports VALUES (73, 'acct-29', 'Usage summary', 'Synthetic data B');
> """)
>
> ROLE_ACTIONS = {
>     "viewer": {"report:read"},
>     "analyst": {"report:read", "report:export"},
> }
>
> def principal_for(account_id, verified_subject):
>     # verified_subject 来自认证中间件，绝不来自请求正文；account_id 来自路径，仍是输入。
>     if verified_subject is None:
>         return None
>     row = db.execute(
>         "SELECT role FROM memberships WHERE account_id=? AND subject=?",
>         (account_id, verified_subject),
>     ).fetchone()
>     return None if row is None else {"account_id": account_id, "subject": verified_subject, "role": row[0]}
>
> def permits(principal, action):
>     return principal is not None and action in ROLE_ACTIONS.get(principal["role"], set())
>
> def load_report(principal, report_id):
>     row = db.execute(
>         "SELECT title, body FROM reports WHERE account_id=? AND id=?",
>         (principal["account_id"], report_id),
>     ).fetchone()
>     return None if row is None else {"title": row[0], "body": row[1]}
>
> def read_api(account_id, verified_subject, report_id):
>     if verified_subject is None:
>         return (401, None)
>     principal = principal_for(account_id, verified_subject)
>     if not permits(principal, "report:read"):
>         return (404, None)          # 隐藏式 404：与不存在的报表相同
>     report = load_report(principal, report_id)
>     return (404, None) if report is None else (200, report)
>
> def submit_export(account_id, verified_subject, report_id):
>     principal = principal_for(account_id, verified_subject)
>     if not permits(principal, "report:read") or load_report(principal, report_id) is None:
>         return (404, None)          # 看不到的报表：隐藏存在性
>     if not permits(principal, "report:export"):
>         return (403, None)          # 已能读到报表，存在性无需隐藏
>     cur = db.execute(
>         "INSERT INTO jobs (account_id, requester, action, report_id) VALUES (?, ?, ?, ?)",
>         (account_id, verified_subject, "report:export", report_id),
>     )
>     db.commit()
>     return (202, cur.lastrowid)     # 队列消息只带这个 job ID
>
> def run_export(job_id):
>     job = db.execute(
>         "SELECT account_id, requester, action, report_id FROM jobs WHERE id=?", (job_id,)
>     ).fetchone()
>     if job is None:
>         return "failed:unknown_job"
>     account_id, requester, action, report_id = job
>     principal = principal_for(account_id, requester)   # 执行时按记录重查当前权限
>     if not permits(principal, action):
>         return "failed:authorization_revoked"
>     report = load_report(principal, report_id)
>     return "failed:target_missing" if report is None else "succeeded"
>
> assert read_api("acct-17", "user-17", 42) == (200, {"title": "Service health", "body": "Synthetic data A"})
> assert read_api("acct-17", "user-17", 43) == (404, None)
> assert read_api("acct-17", "user-29", 42) == read_api("acct-17", "user-17", 43)
> assert read_api("acct-29", "user-29", 42) == (404, None)    # 不会去读 acct-17 的 42
> assert read_api("acct-29", "user-29", 73)[0] == 200
> assert read_api("acct-17", None, 42) == (401, None)
> assert submit_export("acct-29", "user-29", 73) == (403, None)  # viewer 能读不能导出
> assert submit_export("acct-17", "user-29", 42) == (404, None)  # 别的账户：隐藏
>
> status, done_job = submit_export("acct-17", "user-17", 42)
> assert status == 202 and run_export(done_job) == "succeeded"
> status, pending_job = submit_export("acct-17", "user-17", 42)
> assert status == 202
>
> db.execute("DELETE FROM memberships WHERE account_id='acct-17' AND subject='user-17'")
> db.commit()
> assert read_api("acct-17", "user-17", 42) == (404, None)
> assert run_export(pending_job) == "failed:authorization_revoked"
> print("acct-17/42: user-17 -> 200; 43 and user-29 -> same 404; no session -> 401")
> print("viewer export -> 403; cross-account export -> 404; pending export after revocation -> failed:authorization_revoked")
> ~~~
>
> 运行输出：
>
> ~~~text
> acct-17/42: user-17 -> 200; 43 and user-29 -> same 404; no session -> 401
> viewer export -> 403; cross-account export -> 404; pending export after revocation -> failed:authorization_revoked
> ~~~

### 下一步：把这些结果写成调用方能依赖的契约

本章交出的是一套每次请求都执行的判定：五步骨架把可信主体、当前成员关系、动作、账户内的对象和所有旁路连在一起；拒绝时，不可见的对象一律回相同的隐藏式 `404`，已可见对象缺少动作权限才回 `403`；后台任务在受理和执行时各授权一次。

调用方还需要知道这些结果长什么样：错误正文怎样让程序可靠判断，`401`、`404`、`415`、`422` 同时成立时先报哪个，API 改版时什么算兼容。见[怎样让调用方可靠地判断 API 的成功、失败和变化？](#37.%20%E6%80%8E%E6%A0%B7%E8%AE%A9%E8%B0%83%E7%94%A8%E6%96%B9%E5%8F%AF%E9%9D%A0%E5%9C%B0%E5%88%A4%E6%96%AD%20API%20%E7%9A%84%E6%88%90%E5%8A%9F%E3%80%81%E5%A4%B1%E8%B4%A5%E5%92%8C%E5%8F%98%E5%8C%96%EF%BC%9F)

> [!info]- 来源
> - 默认拒绝、最小权限、每次请求校验、对象级授权、ABAC/ReBAC 相对 RBAC 的优势、ID 被猜中也不能访问（“逐次授权的五步”“角色能给什么”）：[OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)，Deny by Default、Validate the Permissions on Every Request、Prefer Attribute and Relationship Based Access Control over RBAC、Ensure Lookup IDs Are Not Accessible Even When Guessed or Cannot Be Tampered With；核对于 2026-11-12。
> - 多租户隔离与租户上下文：[AWS Well-Architected SaaS Lens, Preventing cross-tenant access](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/preventing-cross-tenant-access.html)，核对于 2026-11-12；这是云厂商的架构指导，不是通用标准。
> - `401` 必须带 `WWW-Authenticate`、`403` 语义、可用 `404` 隐藏禁止访问的资源、`404` 可启发式缓存（“隐藏式 404 还是 403”）：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，2022-06，§11.6.1、§15.5.2、§15.5.4–§15.5.5；`private` 与 `no-store`：[IETF RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html)，§5.2.2.5、§5.2.2.7；核对于 2026-11-12。
> - SQL 参数绑定与动态标识符允许列表（“按账户过滤读取”）：[OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)，Primary Defenses；Python 3.11 `sqlite3` 的 `?` 占位符：[Python 3.11 sqlite3 documentation](https://docs.python.org/3.11/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries)；SQLite 复合主键：[SQLite CREATE TABLE](https://www.sqlite.org/lang_createtable.html#the_primary_key)，§3.5；均核对于 2026-11-12。
> - 后台任务“执行时仍须有权限”、导出需单独授权、各端点分别授权，是本例选定的策略；队列协议不替应用决定以受理时还是执行时的权限为准。复现代码在本机 Python 3.11.13 运行通过。
## 37. 怎样让调用方可靠地判断 API 的成功、失败和变化？

前几章讲了一次请求怎样被识别和授权；本章讲 API 怎样把结果交代给调用方，让程序而不是人来判断成功和失败。内容依次是：契约约定了哪几层，错误正文怎样设计，几种错误同时成立时先报哪个，常见失败映射到哪个状态码，OpenAPI 描述怎样与运行时行为核对，以及 API 改版时什么算兼容。

### 契约约定什么

HTTP 提供通用的方法和状态语义（见[第一章](#33.%20%E4%B8%80%E6%AC%A1%20HTTP%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%B5%8F%E8%A7%88%E5%99%A8%E5%88%B0%E8%BE%BE%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%8F%88%E5%B8%A6%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)）；API 契约在其上约定领域输入、表示结构、错误类别、分页规则和兼容政策。契约有几层载体：说明文档、代码里的类型、OpenAPI 描述和运行中的实现。它们彼此独立，写出 schema（结构模式）不证明部署的行为符合它，后文专门讲怎样核对。

沿用[主线四的报表读取案例](#%E6%A1%88%E4%BE%8B%EF%BC%9A%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E9%87%8C%E7%9A%84%E4%B8%80%E6%AC%A1%E8%AF%BB%E5%8F%96)。API 为报表定义了两种明确的 JSON 形状：

- **详情表示**：`GET /v1/accounts/acct-17/reports/42` 返回，带强 ETag `"report-42-v7"`，必有 `id`、`title`、`status`、`delivery`；可选的 `note` 没有值时省略，不输出 JSON `null`。

  ~~~json
  {"id":42,"title":"Service health","status":"ready","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
  ~~~

- **摘要表示**：集合列表里的每一项，只有 `id`、`title`、`status`。列表怎样分页、怎样给出结束信号，见[键集分页章](#29.%20%E6%80%8E%E6%A0%B7%E6%97%A0%E9%87%8D%E5%A4%8D%E3%80%81%E6%97%A0%E9%81%97%E6%BC%8F%E5%9C%B0%E5%88%86%E9%A1%B5%E8%AF%BB%E5%8F%96%E4%B8%80%E4%B8%AA%E8%BF%98%E5%9C%A8%E5%8F%98%E5%8C%96%E7%9A%84%E9%9B%86%E5%90%88%EF%BC%9F)。

为演示创建类请求的错误，本章再加一个端点：`POST /v1/accounts/acct-17/views` 为报表保存一个命名视图，正文是 `{"name":"Weekly","reportId":42}`；名称原样不超过 60 个字符、去掉首尾空白后不能为空，同一账户内不区分大小写地唯一。成功时回 `201 Created` 和 `Location`。创建资源的 `201` 与受理作业的 `202` 怎样区分，见[耗时任务怎样被持久受理？](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)。

### 错误正文：Problem Details

错误正文的机器可判定契约在全领域以这里为准。API 用 RFC 9457 的 Problem Details，媒体类型为 `application/problem+json`：

~~~http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{"type":"https://api.reports.example.test/problems/not-found","title":"Report not found","status":404,"detail":"No report is visible under this identifier."}
~~~

- **程序依赖 `type`。** 调用方按稳定的 `type` URI 或约定的扩展错误码分支，不解析给人看的 `title` 和 `detail`。改 `type` 等于改契约。
- **`status` 与 HTTP 状态一致。** 正文若带 `status`，它必须等于实际的 HTTP 状态码。
- **扩展字段放机器需要的细节。** 例如校验失败时用 `errors` 列出字段路径和稳定错误代码。
- **不泄漏内部信息。** 不回显秘密、异常栈或 SQL 文本。

### 多个错误同时成立时先报哪个

一个请求可能同时犯好几个错：没登录、对象不可见、媒体类型不对、正文写坏了、版本标签过时。返回哪一个本身就是契约，全领域只在这里规定。原则是：不处理正文就能确定的失败先报，而且不能让后面的错误泄漏前面要隐藏的信息。

1. **认证（`401`）。** 没有有效凭据，先回 `401`。所以未认证的请求即使报表 ID 不是整数，也回 `401` 而不是 `422`。
2. **对象可见性（隐藏式 `404`）。** 主体看不到所选账户或对象时回 `404`。隐藏对象即使带着过时的 `If-Match`，也回 `404`，不能用 `412` 暗示对象存在（隐藏规则见[授权章](#%E9%9A%90%E8%97%8F%E5%BC%8F%20404%20%E8%BF%98%E6%98%AF%20403)）。
3. **不支持的媒体类型（`415`）。** 已认证且对象可见时，`Content-Type` 不受支持在读取正文前就能确定，所以先于正文解析错误，也先于 `412` 和 `428`。
4. **正文无法解析（`400`）。**
5. **其余由端点定义。** 字段级校验（`422`）、前置条件（`412`/`428`）、状态冲突（`409`）之间的顺序，由各端点自己规定。

会受理异步作业的端点还有准入拒绝（`429` 速率令牌不足、`503` 等待槽已满，见[容量章](#%E5%87%86%E5%85%A5%E3%80%81%E8%83%8C%E5%8E%8B%E4%B8%8E%E6%8B%92%E7%BB%9D%E6%80%8E%E6%A0%B7%E5%AF%B9%E5%BA%94%E5%88%B0%E5%93%8D%E5%BA%94%EF%BC%9F)）。本 API 把它们排在上面各项和幂等裁决之后：请求必须先是一个合法、可见、而且是**新**的意图，才去竞争额度，所以同键同指纹的重放即使赶上额度耗尽，也照常返回原 job 的当前状态。令牌和等待槽同时不足时先报 `429`。

RFC 9110 的条件请求优先级只约束第 1–3 步这类不需要处理正文就能确定的失败，并不要求所有字段级领域校验都排在 `If-Match` 之前。数据库层的并发不变量，仍由原子写入负责。

### 常见失败映射到哪个状态码

下表是本 API 的映射政策。它不是所有服务都必须采用的唯一一张表，但一旦公开，就是调用方可以依赖的契约：

| 条件 | 结果 | 约定与链接 |
| --- | --- | --- |
| 报表存在，身份与资源权限都通过 | `200` + 详情表示 | — |
| 缺少有效凭据，即使 ID 不是整数 | `401` | 带 `WWW-Authenticate`，例如 `Bearer realm="reports"` |
| 对象不存在，或主体无权看到；即使带陈旧 `If-Match` | `404` | 两种情况 `type` 与详情相同；与 `403` 的取舍见[授权章](#%E9%9A%90%E8%97%8F%E5%BC%8F%20404%20%E8%BF%98%E6%98%AF%20403) |
| 对象可见，但缺少某个动作的权限 | `403` | 同上 |
| JSON 语法无效，例如正文 `{` | `400` | 说明内容无法解析 |
| `Content-Type` 不受端点支持 | `415` | 补丁类端点用 `Accept-Patch` 公布接受的格式；创建视图只收 `application/json` |
| 能解析，但字段值、路径 ID 或范围不合契约 | `422` | 指出字段路径和错误代码；本 API 把非整数路径 ID 也归为 `422` |
| 与当前状态冲突，例如视图重名 | `409` | 告诉调用方怎样刷新或解决冲突 |
| `If-Match` 不匹配或是弱标签 | `412` | 见[条件写章](#412%20%E5%92%8C%20428%20%E5%90%84%E8%AF%B4%E6%98%8E%E4%BB%80%E4%B9%88) |
| `If-Match` 语法错误，或端点不接受的 `*` 与标签列表 | `400` | 同上 |
| 缺少端点要求的 `If-Match` | `428` | 同上；`428` 响应不得被缓存 |
| 超过调用额度 | `429` | 可附 `Retry-After`；不得被缓存；准入与额度见[容量章](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F) |
| 暂时不能处理 | `503` | 同上 |
| 未预期的服务端错误 | `500` | 只给稳定的机器类别；写入结果未知时按幂等契约查询，见[未知结果章](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F) |

`422 Unprocessable Content` 的含义是“内容语法能理解，但其中的指令无法处理”。本 API 据此把畸形 JSON 归为 `400`，把能解析但字段不合规的正文归为 `422`；把非整数路径 ID 也映射为 `422`，是本 API 额外的约定。

### OpenAPI 描述与运行时是否一致

OpenAPI 记录每个操作的路径、参数、请求和响应的媒体类型、成功与错误响应、响应头以及 schema，人和工具都据此调用服务。框架可以从请求和响应模型生成结构；自定义的异常处理器产生的错误，也要在对应操作里声明出来，否则文档里就缺了这些响应。

核对时按操作逐项看：真实路径、每个状态码、请求媒体类型、创建响应的 `Location`、Problem 的 `type`，以及可选字段是否允许缺省或 `null`（例如分页结束时为 `null` 的游标字段，要声明成必返回且允许 `null`）。schema 能表达的约束要与运行时一致：只含空格的视图名，既应被 `CreateView` 的 JSON Schema 拒绝，也应在运行时返回 `422`。媒体类型检查、认证、授权这些运行边界，schema 根本表达不了，要对照处理器单独核验。

跨实现的语义差异也会让“文档说一套、运行做一套”。视图名的 schema 用 `pattern: "\S"`（至少一个非空白字符），运行时用 Python 的 `str.strip()` 判空。两边的“空白”集合不同：

| 输入字符 | ECMAScript 正则 `\S` | Python `str.strip()` 后 | 结果 |
| --- | --- | --- | --- |
| `U+0085`（NEL） | 匹配，schema 通过 | 被去掉，变成空串，运行时拒绝 | 不一致 |
| `U+FEFF`（BOM） | 不匹配，schema 拒绝 | 不被去掉，运行时通过 | 相反方向不一致 |

普通空格和长度样例都通过，不等于 schema 与运行时对所有输入都一致。

### 实例：用 FastAPI 复现契约

下面的复现用与正文相同的数据：账户 `acct-17` 的报表 42（`Service health`，ETag `"report-42-v7"`），`acct-29` 的 `user-29`，以及不存在的报表 43。它演示三件事：

- **检查顺序。** 自定义 `APIRoute.get_route_handler()` 在 FastAPI 解析参数和正文之前，依次做认证（`401`）、账户可见性（隐藏式 `404`）和媒体类型（`415`，比较时忽略大小写和参数）。因此未认证请求带非整数 ID 得到 `401`，跨账户请求带错误媒体类型得到 `404`，媒体类型错误的坏正文得到 `415` 而不是 `400`。
- **错误映射。** `RequestValidationError` 中类型为 `json_invalid` 的映射为 `400`，其余映射为 `422` 并列出字段路径；视图名的前置校验器先检查原始长度，再去首尾空白。
- **文档核对。** 用 `TestClient` 断言状态码与正文，再断言 `app.openapi()` 为每个操作声明了对应的错误响应、`Location` 头和请求媒体类型。

复现不实现真实的令牌验证（用固定的 token 表代替）、条件写或持久存储。

> [!example]- FastAPI 契约复现（FastAPI 0.128.0、Pydantic 2.11.7、Starlette 0.47.2、httpx 0.28.1，生成 OpenAPI 3.1.0）
>
> ~~~python
> from typing import Any, Literal
>
> from fastapi import APIRouter, FastAPI, Request, Response
> from fastapi.exceptions import RequestValidationError
> from fastapi.responses import JSONResponse
> from fastapi.routing import APIRoute
> from fastapi.testclient import TestClient
> from pydantic import BaseModel, Field, field_validator
>
> PROBLEM_BASE = "https://api.reports.example.test/problems/"
> TOKENS = {"token-user-17": "user-17", "token-user-29": "user-29"}   # 代替真实令牌验证
> MEMBERS = {("acct-17", "user-17"), ("acct-29", "user-29")}
>
>
> class Delivery(BaseModel):
>     channel: Literal["email", "download"]
>     recipients: list[str] | None = None
>
>
> class ReportDetail(BaseModel):
>     id: int
>     title: str
>     status: str
>     delivery: Delivery
>     note: str | None = None          # 无值时省略，不输出 null
>
>
> class CreateView(BaseModel):
>     name: str = Field(min_length=1, max_length=60, pattern=r"\S")
>     reportId: int
>
>     @field_validator("name", mode="before")
>     @classmethod
>     def normalize_name(cls, value: Any) -> Any:
>         if isinstance(value, str):
>             if len(value) > 60:      # 先查原始长度，再去首尾空白
>                 raise ValueError("name must be at most 60 characters before trimming")
>             if not value.strip():
>                 raise ValueError("name must contain a non-whitespace character")
>             return value.strip()
>         return value
>
>
> class View(BaseModel):
>     id: int
>     name: str
>     reportId: int
>
>
> class Problem(BaseModel):
>     type: str
>     title: str
>     status: int
>     detail: str
>     errors: list[dict[str, str]] | None = None
>
>
> class ApiProblem(Exception):
>     def __init__(self, status, kind, title, detail, headers=None):
>         self.status, self.kind, self.title, self.detail = status, kind, title, detail
>         self.headers = headers
>
>
> def problem(status, kind, title, detail, headers=None, **extensions):
>     return JSONResponse(
>         status_code=status, media_type="application/problem+json", headers=headers,
>         content={"type": PROBLEM_BASE + kind, "title": title, "status": status,
>                  "detail": detail, **extensions},
>     )
>
>
> NOT_VISIBLE = ("not-found", "Report not found", "No report is visible under this identifier.")
>
>
> class ContractRoute(APIRoute):
>     """在 FastAPI 解析参数和正文之前，按契约顺序做认证、可见性与媒体类型检查。"""
>
>     def get_route_handler(self):
>         handler = super().get_route_handler()
>
>         async def ordered_checks(request: Request):
>             auth = request.headers.get("authorization", "")
>             subject = TOKENS.get(auth.removeprefix("Bearer ")) if auth.startswith("Bearer ") else None
>             if subject is None:
>                 raise ApiProblem(401, "unauthenticated", "Authentication required",
>                                  "Send a valid bearer token.",
>                                  headers={"WWW-Authenticate": 'Bearer realm="reports"'})
>             if (request.path_params.get("account_id"), subject) not in MEMBERS:
>                 raise ApiProblem(404, *NOT_VISIBLE)
>             if request.method == "POST":
>                 media = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
>                 if media != "application/json":
>                     raise ApiProblem(415, "unsupported-media-type", "Unsupported media type",
>                                      "Send this resource using application/json.")
>             return await handler(request)
>
>         return ordered_checks
>
>
> def doc(description):
>     return {"description": description,
>             "content": {"application/problem+json": {"schema": Problem.model_json_schema()}}}
>
>
> reports = {("acct-17", 42): ReportDetail(
>     id=42, title="Service health", status="ready",
>     delivery=Delivery(channel="email", recipients=["reader@example.test"]), note="Draft")}
> views: dict[tuple[str, int], View] = {}
> next_view_id = 1
>
> app = FastAPI()
> router = APIRouter(prefix="/v1/accounts/{account_id}", route_class=ContractRoute)
>
>
> @app.exception_handler(ApiProblem)
> async def on_api_problem(request: Request, exc: ApiProblem):
>     return problem(exc.status, exc.kind, exc.title, exc.detail, headers=exc.headers)
>
>
> @app.exception_handler(RequestValidationError)
> async def on_validation(request: Request, exc: RequestValidationError):
>     errors = exc.errors()
>     if any(e.get("type") == "json_invalid" for e in errors):
>         return problem(400, "malformed-json", "Malformed JSON", "Send a syntactically valid JSON body.")
>     fields = [{"field": ".".join(str(p) for p in e["loc"]), "code": "invalid_value"} for e in errors]
>     return problem(422, "validation", "Request validation failed",
>                    "Correct the fields listed in errors and resubmit.", errors=fields)
>
>
> @router.get("/reports/{report_id}", response_model=ReportDetail, response_model_exclude_none=True,
>             responses={401: doc("Missing or invalid credentials"), 404: doc("Report not visible"),
>                        422: doc("Report ID is not an integer")})
> async def get_report(account_id: str, report_id: int, response: Response):
>     report = reports.get((account_id, report_id))
>     if report is None:
>         raise ApiProblem(404, *NOT_VISIBLE)
>     response.headers["ETag"] = f'"report-{report_id}-v7"'
>     return report
>
>
> @router.post("/views", status_code=201, response_model=View,
>              responses={201: {"description": "View created",
>                               "headers": {"Location": {"schema": {"type": "string"}}}},
>                         400: doc("Malformed JSON body"), 401: doc("Missing or invalid credentials"),
>                         404: doc("Account or report not visible"), 409: doc("View name already exists"),
>                         415: doc("Content-Type must be application/json"),
>                         422: doc("Invalid view fields")})
> async def create_view(account_id: str, payload: CreateView, response: Response):
>     global next_view_id
>     if (account_id, payload.reportId) not in reports:
>         raise ApiProblem(404, *NOT_VISIBLE)
>     if any(a == account_id and v.name.casefold() == payload.name.casefold() for (a, _), v in views.items()):
>         raise ApiProblem(409, "duplicate-name", "View name already exists", "Choose another name.")
>     view = View(id=next_view_id, name=payload.name, reportId=payload.reportId)
>     views[(account_id, view.id)] = view
>     response.headers["Location"] = f"/v1/accounts/{account_id}/views/{view.id}"
>     next_view_id += 1
>     return view
>
>
> app.include_router(router)
>
>
> def check():
>     c = TestClient(app)
>     u17 = {"Authorization": "Bearer token-user-17"}
>     u29 = {"Authorization": "Bearer token-user-29"}
>     base = "/v1/accounts/acct-17"
>
>     ok = c.get(f"{base}/reports/42", headers=u17)
>     assert ok.status_code == 200 and ok.headers["etag"] == '"report-42-v7"'
>     assert ok.json()["title"] == "Service health" and ok.json()["note"] == "Draft"
>
>     missing = c.get(f"{base}/reports/43", headers=u17)
>     hidden = c.get(f"{base}/reports/42", headers=u29)
>     assert missing.status_code == hidden.status_code == 404
>     assert missing.json() == hidden.json()                     # 不存在与跨账户不可区分
>     assert missing.headers["content-type"].startswith("application/problem+json")
>
>     anon = c.get(f"{base}/reports/not-an-integer")
>     assert anon.status_code == 401 and anon.headers["www-authenticate"] == 'Bearer realm="reports"'
>     assert c.get(f"{base}/reports/not-an-integer", headers=u29).status_code == 404
>     assert c.get(f"{base}/reports/not-an-integer", headers=u17).status_code == 422
>
>     post = lambda body, media="application/json", h=u17: c.post(
>         f"{base}/views", content=body, headers={**h, "Content-Type": media})
>     assert post("{", "text/plain").status_code == 415          # 415 先于 400
>     assert post("{", "text/plain", u29).status_code == 404      # 可见性先于 415
>     assert post("{").status_code == 400
>     assert post('{"name":"   ","reportId":42}').status_code == 422
>     assert post('{"name":"' + " " * 61 + 'x","reportId":42}').status_code == 422
>     created = post('{"name":" Weekly ","reportId":42}', "Application/JSON; charset=UTF-8")
>     assert created.status_code == 201 and created.json() == {"id": 1, "name": "Weekly", "reportId": 42}
>     assert created.headers["location"] == "/v1/accounts/acct-17/views/1"
>     assert post('{"name":"weekly","reportId":42}').json()["type"] == PROBLEM_BASE + "duplicate-name"
>     assert post('{"name":"Other","reportId":43}').status_code == 404
>
>     spec = app.openapi()
>     get_op = spec["paths"]["/v1/accounts/{account_id}/reports/{report_id}"]["get"]
>     post_op = spec["paths"]["/v1/accounts/{account_id}/views"]["post"]
>     assert {"401", "404", "422"} <= set(get_op["responses"]) and "409" not in get_op["responses"]
>     assert {"400", "401", "404", "409", "415", "422"} <= set(post_op["responses"])
>     assert "Location" in post_op["responses"]["201"]["headers"]
>     assert set(post_op["requestBody"]["content"]) == {"application/json"}
>     name = spec["components"]["schemas"]["CreateView"]["properties"]["name"]
>     assert (name["minLength"], name["maxLength"], name["pattern"]) == (1, 60, r"\S")
>     print("GET 42 -> 200 + ETag; 43 and cross-account -> identical 404; no token -> 401 before 422")
>     print("POST views: 404 > 415 > 400 > 422; 201 + Location; duplicate -> 409")
>     print("OpenAPI", spec["openapi"], "declares per-operation errors, Location and media type")
>
>
> check()
> ~~~
>
> 运行输出：
>
> ~~~text
> GET 42 -> 200 + ETag; 43 and cross-account -> identical 404; no token -> 401 before 422
> POST views: 404 > 415 > 400 > 422; 201 + Location; duplicate -> 409
> OpenAPI 3.1.0 declares per-operation errors, Location and media type
> ~~~

### 返回的链接能替客户端做什么

REST 的 HATEOAS（Hypermedia as the Engine of Application State，超媒体作为应用状态引擎）约束要求客户端从服务端的表示中发现当前可用的状态转移，而不是凭报表 ID 自己拼出每个 URL。API 可以按自己的契约在表示里返回链接：

~~~json
{
  "id": 42,
  "links": [
    { "rel": "self", "href": "/v1/accounts/acct-17/reports/42" },
    { "rel": "export", "href": "/v1/accounts/acct-17/reports" }
  ]
}
~~~

这个 `links` 数组是本 API 自定的结构，不是通用的 HTTP 链接编码。链接能否被程序使用，取决于几个前提：

- **关系名要有定义。** 只有媒体类型或 API 契约规定了 `self`、`export` 的含义，客户端才能据此操作；给任意 JSON 加一个 `href` 字段，不会自动带来这些语义。
- **只有安全导航适合直接跟随。** `self` 可以渲染成普通链接。`export` 只给了 `href`，没说用什么方法、带什么正文；有副作用的操作要按契约声明的 affordance（操作描述）发送，不能伪装成 `<a>`。
- **异源链接不盲目跟随。** 只有契约允许时才跟随异源地址，也不能把当前站点的认证信息附到异源请求上。
- **链接不配置前端路由。** 单页应用可以用路由接管内部导航，但路由按自己的加载和历史规则工作，服务端返回链接不会自动配置它。

~~~tsx
type ApiLink = { rel: string; href: string };
type Report = { id: number; links: ApiLink[] };

function ReportDetailsLink({ report }: { report: Report }) {
  const self = report.links.find(link => link.rel === "self");
  return self ? <a href={self.href}>查看报表详情</a> : null;
}
~~~

### 兼容演进需要显式政策

API 改版时，“兼容”取决于调用方怎样解析，必须写成政策：

- **通常兼容**：新增可选的响应字段，对忽略未知字段的客户端无害；但严格解码器或生成的客户端代码可能拒绝它。
- **可能破坏调用方**：删除字段，改变字段类型或含义，把可选请求字段改为必填，改变 Problem `type`，调整分页结束信号。

做法是公开兼容政策，检查重要调用方，为不兼容的变更安排版本切换或迁移窗口。没有唯一强制的版本化方案。数据库结构变更与新旧版本并存时的 expand/contract 做法，见[新版本怎样逐步放量，出问题时能撤回什么？](#60.%20%E6%96%B0%E7%89%88%E6%9C%AC%E6%80%8E%E6%A0%B7%E9%80%90%E6%AD%A5%E6%94%BE%E9%87%8F%EF%BC%8C%E5%87%BA%E9%97%AE%E9%A2%98%E6%97%B6%E8%83%BD%E6%92%A4%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 下一步：两个人同时改报表 42 会怎样？

本章交出的是调用方可以依赖的契约：成功与失败各有稳定的状态码和 Problem `type`；几种错误同时成立时按认证、可见性、媒体类型、正文解析的顺序报出，前面的隐藏不被后面的错误泄漏；OpenAPI 描述要与运行时逐项核对；改版遵循公开的兼容政策。

映射表里还有 `412` 和 `428` 没展开。它们来自写请求：两位编辑者都读到了 v7，谁的修改该生效，后到者又该得到什么？见[两个客户端同时修改同一资源时，API 怎样防止互相覆盖？](#38.%20%E4%B8%A4%E4%B8%AA%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%90%8C%E6%97%B6%E4%BF%AE%E6%94%B9%E5%90%8C%E4%B8%80%E8%B5%84%E6%BA%90%E6%97%B6%EF%BC%8CAPI%20%E6%80%8E%E6%A0%B7%E9%98%B2%E6%AD%A2%E4%BA%92%E7%9B%B8%E8%A6%86%E7%9B%96%EF%BC%9F)

> [!info]- 来源
> - Problem Details 的 `type`、`title`、`status`、`detail` 与扩展字段（“错误正文”）：[IETF RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)，2023-07，§3–§4；核对于 2026-11-12。
> - `400`、`401` 质询、`403`、`404`、`409`、`415`、`422` 的语义，条件请求的评估优先级（“多个错误同时成立时先报哪个”“常见失败映射到哪个状态码”）：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，2022-06，§11.6.1、§13.2.1–§13.2.2、§15.5；`428` 与 `429` 及二者不得缓存：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，2012-04，§3–§4；核对于 2026-11-12。
> - 操作、参数、媒体类型、响应与 schema 的接口描述（“OpenAPI 描述与运行时是否一致”）：[OpenAPI Specification v3.2.1](https://spec.openapis.org/oas/v3.2.1.html)，2026-09-10，§4–§5；核对于 2026-11-12。复现环境生成的是 OpenAPI 3.1.0，以 `app.openapi()['openapi']` 为准。
> - ECMAScript 与 Python 空白集合的差异：本机 Node v26.13.1 与 Python 3.11.13 实测 `U+0085`、`U+FEFF` 两个字符，核对于 2026-11-26。
> - FastAPI 请求模型、响应模型、自定义错误处理与 `APIRoute.get_route_handler()`（“实例”）：[Request Body](https://fastapi.tiangolo.com/tutorial/body/)、[Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)、[Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)、[Custom Request and APIRoute](https://fastapi.tiangolo.com/how-to/custom-request-and-route/)；Pydantic 2.11 的前置校验器与 JSON Schema：[Validators](https://docs.pydantic.dev/2.11/concepts/validators/)、[JSON Schema](https://docs.pydantic.dev/2.11/concepts/json_schema/)；官方文档核对于 2026-11-12。复现代码在 FastAPI 0.128.0、Pydantic 2.11.7、Starlette 0.47.2、httpx 0.28.1 上运行通过。
> - 超媒体约束（“返回的链接能替客户端做什么”）：[Roy T. Fielding, Architectural Styles and the Design of Network-based Software Architectures](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)，2000，§5.1.5。
## 38. 两个客户端同时修改同一资源时，API 怎样防止互相覆盖？

两个人读到同一版本、各自修改、先后提交，后提交的人若无条件写入，就会悄悄抹掉前一个人的改动，这叫 lost update (丢失更新)。本章讲 API 在 HTTP 层怎样防止它：强 ETag 标记版本，`If-Match` 把“仍是这个版本”变成写入的前提条件，`412` 和 `428` 各报告什么，写入零行时怎样区分“版本过时”和“对象已不可见”，以及收到 `412` 之后客户端该做什么。数据库里怎样让版本检查与写入原子地绑在一起，权威讲解在[两个请求争夺最后一件库存时，怎样保证只预留一次？](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)，本章只用它的结论。

### 案例：两位编辑者都读到 v7

沿用[主线四的报表读取案例](#%E6%A1%88%E4%BE%8B%EF%BC%9A%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E9%87%8C%E7%9A%84%E4%B8%80%E6%AC%A1%E8%AF%BB%E5%8F%96)。`acct-17` 里有两位持有 `report:edit` 权限的编辑者甲和乙，他们都打开了报表 42，读到同一份详情表示和强 ETag：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "report-42-v7"

{"id":42,"title":"Service health","status":"ready","delivery":{"channel":"email","recipients":["reader@example.test"]},"note":"Draft"}
~~~

甲把交付方式改成下载，并删掉备注，先提交；乙仍在 v7 的基础上编辑，后提交。整个过程如下，后文逐行解释：

| 时点 | 甲 | 乙 | 服务端的版本与结果 |
| --- | --- | --- | --- |
| 两人读取 | 保存 v7 表示和 `"report-42-v7"` | 同左 | 当前 v7 |
| 甲提交 | `PATCH` 带 `If-Match: "report-42-v7"`；条件写入命中 | 仍在编辑 v7 草稿 | 当前 v8；甲收到 `200` 和 `"report-42-v8"` |
| 乙提交 | — | `PATCH` 带 `If-Match: "report-42-v7"`；条件写入影响 0 行 | 按当前授权重读：对象仍可见、版本已是 v8，回 `412`；乙的补丁没有生效 |
| 乙处理冲突 | — | 重读 v8，比较 v7 基线、自己的草稿和 v8，确认合并后带 `"report-42-v8"` 重提 | 新的条件写入提交前，一直是 v8 |

### 强 ETag 怎样标记一个版本

条件写依赖的版本标识规则在全领域以这里为准：

- **强 ETag 随所标记的表示一起变化。** 本例的编辑端点只返回一种规范 JSON 表示，任何可见字段的改动都会推进资源版本，所以可以用 `"report-42-v7"` 标记它。
- **不同字节的表示要有不同的强标签。** 若内容协商或内容编码产生了字节不同的表示，例如压缩与未压缩、中文与英文，每一种都要有可区分的强标签，不能共用；每个标签都要能映射回写入检查所用的资源版本。
- **`If-Match` 用强比较。** 只有两个标签都是强标签且逐字符相同才算匹配。单个弱标签（如 `W/"report-42-v7"`）语法合法，但永远通不过强比较，结果与陈旧的强标签一样是 `412`。
- **标签只证明“匹配”，不证明“读过”。** 服务端能验证提交的标签是否与当前表示强匹配，却不能证明调用方确实读过那份表示。

ETag 是不透明的：只比较相等，不能按字符串推断新旧；这里的 v7、v8 后缀只为方便追踪案例。

### 带着标签提交补丁

甲提交时声明补丁格式，并带上刚读到的强 ETag：

~~~http
PATCH /v1/accounts/acct-17/reports/42 HTTP/1.1
Content-Type: application/merge-patch+json
If-Match: "report-42-v7"

{"delivery":{"channel":"download"},"note":null}
~~~

服务端当前仍是 v7，补丁通过校验，于是返回新的规范表示和新标签：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "report-42-v8"

{"id":42,"title":"Service health","status":"ready","delivery":{"channel":"download"}}
~~~

#### 补丁正文怎样解释

这个资源只接受 JSON Merge Patch（`application/merge-patch+json`）。它按成员名递归合并，规则只有三条：

- 补丁里没出现的成员保持不变；
- 值为 `null` 的成员被删除；
- 数组整体替换，没有元素级的增删。

按这三条，甲的补丁合并出的中间文档仍保留旧的 `recipients`，因为补丁省略了它。本 API 另有一条业务规则：下载模式不保存收件人。所以服务端在合并后再做业务规范化，移除 `recipients`，然后校验最终文档；`channel` 为 `email` 时最终文档必须至少有一个合法收件人，不合法就整笔拒绝。客户端因此只需提交改动的字段，不必提交隐藏的 `recipients`。以后若切回邮件模式，新补丁要给出整个收件人数组，例如 `["editor@example.test","audit@example.test"]`。

Merge Patch 的 `null` 一律表示删除，无法表达“字段存在且值为 `null`”。资源必须保留显式 `null` 时，要为该字段另定表示，或换一种补丁格式。

JSON Patch（`application/json-patch+json`）是另一种语法：正文是由 `add`、`remove`、`replace`、`move`、`copy`、`test` 操作组成的数组，按路径逐条执行，数组元素和 `null` 都按操作解释。两种格式语义不同，调用方不能只凭 `PATCH` 这个方法名猜。服务端应公布自己接受哪些补丁格式，例如在 `OPTIONS` 响应里用 `Accept-Patch`；提交了未声明的格式，回 `415`。

无论哪种格式，整份补丁都必须原子地生效：要么所有修改一起可见，要么一项也不应用。

### 写入时怎样检查版本

把 `version = 7` 和账户谓词放进同一条 `UPDATE` 的条件里，影响 0 行只说明这次没有写入，不说明为什么。先在事务外读到 v7、再无条件写入是错的：两个并发请求可能都检查到 v7，然后依次覆盖对方。条件写入、返回行数的含义、等锁后的重新检查，见[数据库条件写入一章](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。

HTTP 层要处理的是 0 行之后的映射，这条规则在全领域以这里为准：

1. **按当前授权重读。** 0 行可能是因为版本变了，也可能是对象已被删除，或主体已失去权限。服务端用当前授权和账户范围重新读取对象。
2. **对象已不存在或不可见：回隐藏式 `404`。** 不能回 `412`，否则等于告诉无权的人“这个对象存在，只是版本变了”。
3. **对象仍可见、版本不匹配：回 `412`。** 这就是乙的情况。

这次重读只用来区分失败原因，不能替代写入时的授权。权限可能在写入期间被并发撤销时，必须在写入的同一一致性边界内重核授权：例如锁住授权记录，或把当前授权条件并入同一个原子写入条件，让撤销与写入按事务顺序发生。写入成功之后再检查权限，撤销不了已经发生的越权写入。一个补丁若要改多行或其他持久状态，就用同一个事务覆盖全部改动和最终的业务校验。

### 412 和 428 各说明什么

| 情况 | 结果 | 含义 |
| --- | --- | --- |
| `If-Match` 的强标签与当前表示不匹配，或给的是单个弱标签 | `412 Precondition Failed` | 前置条件为假，方法没有执行；客户端要重读当前表示 |
| 端点要求 `If-Match`，请求却没带 | `428 Precondition Required` | 本 API 的端点政策：拒绝无条件写入。`428` 响应不得被缓存 |
| `If-Match` 语法错误；或 `*`、标签列表这类 HTTP 合法、但本端点规定只接受单个标签的写法 | `400` | 单个弱标签语法合法，不属于这一行，而是 `412` |

乙收到的 `412`：

~~~http
HTTP/1.1 412 Precondition Failed
Content-Type: application/problem+json

{"type":"https://api.reports.example.test/problems/version-mismatch","title":"The report changed","status":412}
~~~

这些结果排在认证、对象可见性和 `415` 之后：隐藏对象带陈旧标签仍回 `404`，媒体类型不受支持时先回 `415`。完整顺序见[多个错误同时成立时先报哪个](#%E5%A4%9A%E4%B8%AA%E9%94%99%E8%AF%AF%E5%90%8C%E6%97%B6%E6%88%90%E7%AB%8B%E6%97%B6%E5%85%88%E6%8A%A5%E5%93%AA%E4%B8%AA)。

### 412 之后客户端怎么办

收到 `412`，客户端既不能自动覆盖，也不能自动重放。乙的客户端保留自己的草稿和 v7 基线，重读 v8，把三份值放在一起比较：v7 基线、本地草稿、服务器当前的 v8。用户确认合并结果后，才以 `"report-42-v8"` 重新提交；若这期间资源又变了，新的 `412` 再走一遍比较和确认。编辑界面怎样逐字段做三方比较、联动字段怎样整组处理，见[编辑表单怎样在别人同时修改时安全保存？](../../frontend/ui-state/editing-sessions-and-conditional-writes.md)。

`PATCH` 方法本身不承诺幂等，`If-Match` 也只解决“基于旧版本的写入不能生效”。它留下一个盲区：甲的提交若已成功、响应却在途中丢失，甲用原标签重发，得到的也是 `412`。仅凭这个 `412`，甲分不清是自己的第一次写入已生效，还是别人改了报表。一般的处理是重读并比较；需要精确确认首次副作用是否发生的端点，还要为操作保存幂等记录，用稳定的操作键回查，见[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。`412` 也不能替代授权结果：授权始终在版本比较之前。

### 下一步：请求组到此结束

到这里，一次同步请求的完整路径都有了：语义与传输把请求送到服务（第一章），缓存决定能否复用（第二章），会话产出可信主体（第三章），逐次授权决定能否读写（第四章），API 契约把结果交代给程序（第五章），条件写让并发修改不互相覆盖（本章）。

下一步离开“请求与契约”，进入“异步交接与容量”。本章最后留下的盲区正是它的起点：写请求超时或响应丢失时，调用方怎样用稳定的操作身份查清结果并安全重试？见[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。若页面还需要在报表生成期间持续收到更新，可先读本章的支线[服务端要持续推送更新时，怎样选通道，断线后又怎样接上？](#39.%20%E6%9C%8D%E5%8A%A1%E7%AB%AF%E8%A6%81%E6%8C%81%E7%BB%AD%E6%8E%A8%E9%80%81%E6%9B%B4%E6%96%B0%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E9%80%89%E9%80%9A%E9%81%93%EF%BC%8C%E6%96%AD%E7%BA%BF%E5%90%8E%E5%8F%88%E6%80%8E%E6%A0%B7%E6%8E%A5%E4%B8%8A%EF%BC%9F)

> [!info]- 来源
> - 强弱 ETag、不同内容编码须用不同强标签、`If-Match` 强比较与评估、`412`（“强 ETag 怎样标记一个版本”“412 和 428 各说明什么”）：[IETF RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)，2022-06，§8.8.1、§8.8.3.2–§8.8.3.3、§13.1.1、§13.2、§15.5.13；核对于 2026-11-12。
> - `428 Precondition Required` 及其不得缓存：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，2012-04，§3；核对于 2026-11-12。
> - `PATCH` 的方法语义、整份补丁原子应用、`Accept-Patch`、不承诺幂等（“补丁正文怎样解释”“412 之后客户端怎么办”）：[IETF RFC 5789, PATCH Method for HTTP](https://www.rfc-editor.org/rfc/rfc5789.html)，2010-03，§2、§3.1；核对于 2026-11-12。
> - JSON Merge Patch 的成员省略、`null` 删除与数组整体替换：[IETF RFC 7396](https://www.rfc-editor.org/rfc/rfc7396.html)，2014-10，§2；JSON Patch 的媒体类型与操作数组：[IETF RFC 6902](https://www.rfc-editor.org/rfc/rfc6902.html)，2013-04，§3–§4；核对于 2026-11-12。
> - 0 行后按当前授权映射为 `404` 或 `412`、授权须在写入的一致性边界内重核、`If-Match` 单标签政策：本例 API 选定的契约，依据上述 RFC 的语义推出。
## 39. 服务端要持续推送更新时，怎样选通道，断线后又怎样接上？

本章是[条件写章](#38.%20%E4%B8%A4%E4%B8%AA%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%90%8C%E6%97%B6%E4%BF%AE%E6%94%B9%E5%90%8C%E4%B8%80%E8%B5%84%E6%BA%90%E6%97%B6%EF%BC%8CAPI%20%E6%80%8E%E6%A0%B7%E9%98%B2%E6%AD%A2%E4%BA%92%E7%9B%B8%E8%A6%86%E7%9B%96%EF%BC%9F)之后的支线：页面不只要读一次，还要在报表生成期间持续得知变化。它回答两个问题：短轮询、长轮询、SSE、流式 Fetch、WebSocket 怎样选；连接断开后，客户端怎样不漏、不错地接上。全章围绕一个先于选型的决定展开：页面只需要最新状态，还是每条事件都不能丢。

**沿用的案例。** 沿用[主线四的报表读取案例](#%E6%A1%88%E4%BE%8B%EF%BC%9A%E8%B4%A6%E6%88%B7%E6%8A%A5%E8%A1%A8%E6%9C%8D%E5%8A%A1%E9%87%8C%E7%9A%84%E4%B8%80%E6%AC%A1%E8%AF%BB%E5%8F%96)。报表 42 被编辑到 v8 之后，用户请求重新生成；之后一次权威读取返回 `version=9`、`status=running`，以及事件日志游标 `103`，表示这份快照已经包含了日志里到第 103 条为止的事件。报表还在生成，页面需要继续收到后续变化：事件 104 会带来 `version=10`、`progress=80`。

### 先定恢复目标：只要最新状态，还是每条事件都不能丢

选通道之前先定恢复目标，因为两种目标对服务端和客户端的要求完全不同：

| 恢复目标 | 断线后怎么做 | 需要的条件 |
| --- | --- | --- |
| **只要最新状态** | 重读带单调 `version` 的权威快照，再从快照的游标继续 | 事件携带完整状态，较大版本确实覆盖较小版本，客户端才能放心丢弃中间通知 |
| **每条事件都不能丢** | 从客户端持久保存的确认位置开始重放 | 服务端保留可重放的事件日志；客户端有持久的应用确认位置；协议定义重复、顺序和缺口怎样处理 |

无论哪种目标，“重新连上”都只恢复了传输，不会补回应用漏掉的工作。报表任务的权威状态始终在状态接口或持久的任务记录里；结果不明时，客户端重新查询这些资源，而不是依赖通道。下面每种通道的恢复细节，都按这两种目标分别说明。

### 按方向、请求形状和恢复责任选通道

~~~mermaid
flowchart TD
    Need{是否要求同一通道持续双向发送？}
    Need -->|是| WS[WebSocket]
    Need -->|否| Repeat{客户端能否按所需时延反复发请求？}
    Repeat -->|能| Poll[短轮询或长轮询]
    Repeat -->|不能，服务端要主动推送| Shape{普通 GET 和原生事件解析是否够用？}
    Shape -->|够用| SSE[SSE + EventSource]
    Shape -->|需要自定义请求或解析| Fetch[Fetch 响应流]
    Poll --> Resume[按恢复目标：状态重查或事件续读]
    SSE --> Resume
    Fetch --> Resume
    WS --> Resume
    Resume --> Answer[明确游标、重复、缺口与授权]
~~~

| 方式 | 请求与消息方向 | 恢复由谁负责 | 合适的条件与成本 |
| --- | --- | --- | --- |
| short polling (短轮询) | 客户端按间隔发普通请求，取当前状态或自上次游标以来的变化 | 客户端控制间隔、退避、抖动和停止；接口定义版本或游标 | 更新不密、简单性重要时。间隔越短发现越快，空响应和请求数也越多；可带条件字段少传正文（见[缓存章](#34.%20%E4%B8%80%E4%BB%BD%20HTTP%20%E5%93%8D%E5%BA%94%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%8F%AF%E4%BB%A5%E7%9B%B4%E6%8E%A5%E5%A4%8D%E7%94%A8%EF%BC%8C%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%BF%85%E9%A1%BB%E5%9B%9E%E6%BA%90%E7%A1%AE%E8%AE%A4%EF%BC%9F)），但请求照样要发 |
| long polling (长轮询) | 服务端暂留一次请求，有变化或到期限才返回；客户端随后带新游标再问 | 客户端重新请求；服务端限制等待时长；双方处理代理超时和断线 | 要普通请求形状、又想减少空轮询时。每个挂起请求仍占服务端状态和连接资源 |
| SSE（Server-Sent Events）+ `EventSource` | 浏览器用 `GET` 打开一个 `text/event-stream` 响应，从服务端单向收事件 | 原生接口自动重连并带 `Last-Event-ID`；服务端保存事件并按有效游标重放 | 服务端单向推送、原生格式和重连够用时。构造器不能设请求方法、自定义字段或正文 |
| 流式 Fetch | 一次请求可用任意方法、字段和正文，响应体逐块读取 | 应用自己实现解析、游标、重试、退避、取消和授权 | 需要 `Authorization` 字段、`POST` 查询或自定义线格式时。读到的字节块不是事件边界 |
| WebSocket | 握手后双方都能主动发消息 | 应用定义重连、身份更新、确认、序号和重放 | 需要在一条长连接上持续双向低延迟交互时。浏览器原生 API 不恢复消息，也没有接收侧背压 |

长轮询和推送都能减少“更新不密却要尽快到达”时的等待。长轮询每次事件或到期都结束请求，客户端立即带新游标再问，要承担挂起请求、代理超时和反复建连的成本；SSE 或流式 Fetch 保持一个响应打开，减少了反复请求，却要检查代理缓冲、空闲超时和长连接容量。选择取决于目标延迟、服务器资源和部署链路，没有哪种方式只凭“实时”二字就必然胜出。

### 长轮询：游标只在收到事件后前进

报表 42 用长轮询时，查询参数 `after` 指向客户端最近取到的事件：

~~~http
GET /v1/accounts/acct-17/reports/42/updates?after=103&wait=25 HTTP/1.1
~~~

服务端最多等 25 秒。事件 104 先出现，就立即返回它，客户端下一次改带 `after=104`：

~~~http
HTTP/1.1 200 OK
Content-Type: application/json

{"cursor":"104","type":"report.updated","version":10,"status":"running","progress":80}
~~~

若先到期且没有事件，接口可以回空的 `204 No Content`，客户端仍以 `after=103` 再问。这里的 `204` 只是本接口的约定；后文 `EventSource` 收到 `204` 则是另一项标准行为，会停止自动重连。

两种恢复目标在这里的差别是：只要最新状态时，`after` 可以取“已收到”的位置；每条事件都要触发不可丢的副作用时，`after` 必须取持久保存的 application-level acknowledgement (应用层确认，ACK)，否则会越过尚未处理完的事件。

轮询的成本要按请求数估算。一万个客户端各每 0.5 秒轮询一次，请求率约为 `10,000 ÷ 0.5 = 20,000` 次/秒。这只是请求数，不等于同样数量的数据库查询或固定的 CPU 开销，也没算重试和同步突发。加随机抖动能摊平同时到达的请求；更新少时延长间隔，服务端报错时退避，任务结束或页面不再需要更新时停止。入口怎样准入与限额，见[一条异步管线能接多少工作，超出时在哪里拒绝？](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)和[流量远超容量或遭到攻击时，每一层能挡住什么？](#48.%20%E6%B5%81%E9%87%8F%E8%BF%9C%E8%B6%85%E5%AE%B9%E9%87%8F%E6%88%96%E9%81%AD%E5%88%B0%E6%94%BB%E5%87%BB%E6%97%B6%EF%BC%8C%E6%AF%8F%E4%B8%80%E5%B1%82%E8%83%BD%E6%8C%A1%E4%BD%8F%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 快照和订阅怎样衔接在同一日志位置

推送通道都面临同一个衔接问题：先读快照，再订阅后续事件，两步之间发生的变化不能漏掉。这条规则在全领域以这里为准。

快照里同时给出版本和游标：

~~~http
GET /v1/accounts/acct-17/reports/42 HTTP/1.1
Accept: application/json
~~~

~~~json
{"id":42,"version":9,"status":"running","progress":0,"event_cursor":"103"}
~~~

`version` 描述状态修订到第几版，`event_cursor` 描述从日志的哪里接着读。二者必须来自同一个一致性位置：快照涵盖到 103，订阅就从 103 之后开始。若先读快照、再订阅“当前最新”而不带位置，两步之间的变化就可能丢失。

订阅时，服务端先回放 103 之后的历史，再切到实时读取日志尾部（尾读）。切换也必须沿同一条连续日志前进：

1. 服务端授权这次订阅后，记下本轮的 high watermark (高水位) `W=105`，即此刻日志的最新位置。
2. 回放 `(103, 105]`，即事件 104 和 105。
3. 从 `W` 之后继续读同一条追加日志。回放期间追加的 106 位于 105 之后，尾读自然会读到它。

![从一致快照的游标开始订阅，回放到高水位后沿同一日志继续尾读](../../engineering-foundations/services/resources/sse-snapshot-to-events.svg)

实现若把历史读取和实时通知分开，就要先登记通知、再记下 `W`，回放到 `W` 后按日志游标读到当前尾端；通知只负责唤醒补读，不提供位置。也可以由同一个日志读取器原子地确定水位和尾读起点。不能等回放结束后再另开一个“从当前开始”的监听，否则两步之间追加的事件会丢。

示例用数字游标便于阅读。真实游标可以是不透明字符串，只在服务端定义的报表或订阅范围内有序，不同报表或分区之间没有全局顺序。服务端先认证并授权报表 42 的订阅，再验证游标属于该范围、仍在可重放窗口内。客户端提供的游标不是凭据，不能授权读取事件。

### SSE：线格式与事件边界

SSE 把 UTF-8 文本按行解析：

- CRLF、单独的 CR 或 LF 都能结束一行；空行结束一条事件。
- `event` 是事件类型，`data` 是负载，`id` 是重连位置，`retry` 是重连等待时间的建议。
- 多条 `data` 行用换行符拼成一份数据；没有 `event` 时类型为 `message`。
- 以冒号开头的行是注释，不派发事件，可用来保活。
- `retry` 只有全由 ASCII 数字组成时才被原生接口采用。

网络分块、HTTP 帧或一次 Fetch `read()` 都可能切在字符或字段行中间，不能当作事件边界。报表 42 的事件流如下：

~~~text
id: 104
event: report.updated
data: {"report_id":42,"version":10,"status":"running","progress":80}

id: 105
event: report.updated
data: {"report_id":42,"version":11,"status":"ready","progress":100}

~~~

`104`、`105` 是日志位置，`version=10`、`version=11` 是状态修订，两套编号各管一件事。

#### 代理缓冲与空闲超时

格式规则确定了事件边界，却不保证服务端每次少量写出都立即到达浏览器。代理或压缩层可能先缓冲、合并数据，例如 NGINX 反向代理默认缓冲上游响应；长响应也可能被代理或负载均衡器的空闲超时关闭。上线前要检查整条链路的缓冲和超时设置，否则应用及时写出的事件，用户可能迟迟收不到，或不得不续连。

### EventSource 能做什么、做不了什么

快照涵盖到 103，第一次订阅用应用约定的 URL 参数 `after=103`。同源页面用原生 `EventSource`：

~~~javascript
const url = '/v1/accounts/acct-17/reports/42/events?after=103';
const source = new EventSource(url);

source.addEventListener('report.updated', (event) => {
  const update = JSON.parse(event.data);
  if (update.report_id === 42) showStatus(update.status, update.version, update.progress);
});
source.addEventListener('reset', () => {           // 本例自定义：只要状态的路径
  source.close();
  void refreshSnapshotAndSubscribeAgain();
});
source.addEventListener('cursor.expired', () => {  // 本例自定义：逐事件路径的缺口
  source.close();
  showDeliveryGapAndReconcile();
});
source.addEventListener('error', () => showConnectionState(source.readyState));
~~~

`reset` 和 `cursor.expired` 是本例自定义的事件名，后文“游标过期”一节解释。`EventSource` 的能力边界：

- **请求形状固定。** 构造器只接受 URL 和 `withCredentials` 选项，不能设方法、字段或正文；首次续读位置只能放在 URL 里，页面不能设定初始的 `Last-Event-ID`。
- **重连自动带位置。** 断线后浏览器通常用同一 URL 重连，并把已解析的最后一个事件 ID 放进 `Last-Event-ID` 请求字段。本例约定该字段优先于 URL 里原来的 `after=103`：若断线前已完整解析 104，服务端就从 104 之后重放 105。重连间隔可由 `retry` 建议，但浏览器的退避策略和网络条件决定实际时刻，客户端不应假设固定的重连时间。
- **停止与终止。** 对新的 SSE 请求返回 `204 No Content`，告诉 `EventSource` 停止自动重连；这不是把已开始的 `200` 流改成 `204`。非 `200` 响应或错误的媒体类型会让连接进入终止状态。原生 `error` 事件不暴露状态码或错误正文，页面只能按 `readyState` 判断。
- **每次连接都授权。** 初连和每次重连，服务端都重新验证身份并授权报表。授权过期时，页面无法从 `error` 事件读出 `401` 再改请求字段。
- **跨源凭据。** 跨源 `EventSource` 默认不带凭据；需要 Cookie 时设 `{ withCredentials: true }`，服务端必须按 CORS 凭据规则返回与页面来源精确匹配的 `Access-Control-Allow-Origin` 和 `Access-Control-Allow-Credentials: true`。需要自定义授权字段或刷新凭据时，改用流式 Fetch，或关闭旧对象、完成认证更新后新建一个。

页面怎样保留已应用的版本 10、续读 105 后更新到版本 11，见[服务端持续推送时，界面怎样合并更新并从断线恢复？](../../frontend/ui-state/streaming-updates-and-resume.md)。

### Last-Event-ID 只是解析位置，不是业务确认

“每条事件都不能丢”时，有一条规则在全领域以这里为准：传输层记录的位置不能当作业务确认。

`Last-Event-ID` 是浏览器的解析位置，在事件交给 JavaScript 处理器之前就已更新。假设 104 已被完整解析，处理器却在持久化副作用前失败；自动重连会从 104 之后开始，应用无法靠这个字段发现 104 的处理缺失。反过来，客户端若在处理完成后才把确认写进数据库，处理已提交、确认却没写成，104 又会被重复收到。

![解析游标与持久确认是两条位置：ACK=103 时重放 104，ACK=104 时续读 105](../../engineering-foundations/services/resources/sse-parse-vs-ack.svg)

所以逐事件路径要维护一个独立的持久确认游标：

- **按消费者和订阅范围保存。** 每个消费者对每个订阅有自己的确认位置。
- **只推进连续完成的前缀。** 104 未完成，就不能因 105 已完成而确认到 105。
- **失败显式处理。** 处理失败要显式重试该事件，或停止并从持久确认位置重新订阅，不能等连接偶然断开。
- **恢复以它为准。** 即使 `Last-Event-ID` 更靠后，也不能用解析进度覆盖尚未确认的事件：确认位置是 103 时重连要重放 104；104 处理成功并持久确认后，下次才从 105 继续。

客户端处理完 104 后，用另一个已授权的请求提交确认：

~~~http
POST /v1/accounts/acct-17/reports/42/ack HTTP/1.1
Content-Type: application/json

{"cursor":"104"}
~~~

处理和确认最好在同一事务里提交。若二者分开，处理已提交、确认未提交时 104 会重复，所以要按事件 ID 去重，并让副作用保持幂等。传输层可以重发，但不提供端到端的“只处理一次”。若事件是局部补丁而非完整状态，必须按序应用，或回到快照重建，不能跳过中间版本。

### 游标过期：重置状态，还是标记缺口去对账

重放窗口不够时，不能悄悄跳过缺口。两种恢复目标的处理不同，下面的 `reset` 和 `cursor.expired` 都是本例自定义的协议，不是 SSE 标准行为：

- **只要最新状态。** 服务端发 `reset` 事件并结束当前响应。它必须带 `data` 字段并以空行结束，才会派发给前面代码里的处理器。客户端关闭旧连接，读取新快照，用新快照的游标重新订阅。

  ~~~text
  event: reset
  data: {}

  ~~~

- **每条事件都不能丢。** 游标早于日志保留期，就是业务缺口，不能把游标推进到新快照的位置假装补齐。服务端在结束流之前明确告知：

  ~~~text
  event: cursor.expired
  data: {"after":"103","earliest_available":"200"}

  ~~~

  客户端关闭订阅、停止自动重连并标记缺口，从保留更久的审计日志对账或走有记录的恢复流程，之后才从新的确认位置继续。新快照只能重建当前状态，不能替代漏掉的逐事件副作用。

### 流式 Fetch：从任意字节块组装一次有限结果

`EventSource` 只能发 `GET`、只能选择是否带 Cookie，接口需要更多时，可以用 Fetch 发带授权字段和正文的 `POST`，再按 SSE 格式或另一种明确定义的线格式读响应。本节换一个有限的例子：在报表 42 的事件中搜索 `stage` 为 `rendering` 的记录。它是一次查询的输出，不是持续订阅，也不修改报表状态。

有限结果的完整性要靠应用协议证明，规则比 `EventSource` 更严：

- **显式终止事件。** 本接口用 `result.complete` 表示结果完整。它必须带 `event` 行、`data` 行和结尾空行，空行边界完整到达后，解析器才算看到了终态。Fetch 读到 EOF 只说明字节流结束，不能代替应用的完成信号。标准 `EventSource` 会丢弃 EOF 前没有以空行结束的尾部事件；本接口更严格，未闭合的事件或缺失的终止事件都按截断失败处理。
- **跨块的 UTF-8 字符。** 字节块可能把一个字符切成两半。增量 `TextDecoder`（`stream: true`）会等后续字节补齐；默认解码器已按规则去掉开头的一个 BOM，解析器不再二次裁剪。
- **有界缓冲。** 解析器限制单行和单个事件的大小。
- **读前检查。** 先查状态码和媒体类型，不符合时取消尚未读取的响应体再报错；开始读取后出错，则取消 reader 并释放锁。
- **部分结果不冒充完整。** 已显示的匹配项只能标为部分结果；终止事件和 EOF 都通过检查后，才能把整次查询标为完成。若契约允许收到终止事件后提前结束，要调用 `reader.cancel()` 释放未读的正文，并记为“主动停止”而不是“读到 EOF”。
- **背压只在本地。** `Response.body` 是 ReadableStream（可读流），暂停读取能限制本地缓冲，却不能让服务端停止生成。

以 `报` 的 UTF-8 字节 `E6 8A A5` 为例：

~~~text
第 1 块末尾：... 64 61 74 61 3A 20 E6 8A
第 2 块开头：A5 E8 A1 A8 0A 0A ...
解码并按行解析：data: 报表\n\n  → 事件数据「报表」
~~~

第一块在 `E6 8A` 处结束，增量解码器暂不输出；第二块从 `A5` 接上，给出“报”和“表”，再遇到两个换行，解析器才派发事件。请求若跨源，浏览器仍执行 CORS 检查；带 `Authorization` 和 `application/json` 的请求通常还会触发预检。界面怎样表示部分、重连、取消和终态，见[前端流式更新一章](../../frontend/ui-state/streaming-updates-and-resume.md)。

下面的解析器按 CRLF、CR 或 LF 切行，忽略注释，拼合多条 `data`，识别 `event` 和 `id`，限制缓冲，并在 EOF 检查空行边界。“出现过 `data` 字段”与“负载为空”是两回事：单个 `data:` 字段会派发空字符串，没有 `data` 字段则不派发。它不自动重连，也不实现 `retry`。

> [!example]- 有限 SSE 响应的解析与消费实现
>
> ~~~javascript
> class StrictSSEParser {
>   constructor(onEvent, maxLineUnits = 16_384, maxEventUnits = 65_536) {
>     this.onEvent = onEvent;
>     this.maxLineUnits = maxLineUnits;
>     this.maxEventUnits = maxEventUnits;
>     this.line = '';
>     this.data = [];
>     this.type = '';
>     this.id = '';
>     this.eventUnits = 0;
>     this.skipLF = false;
>     this.pendingBlock = false;
>   }
>
>   feed(text) {
>     for (const char of text) {
>       if (this.skipLF) {
>         this.skipLF = false;
>         if (char === '\n') continue;
>       }
>       if (char === '\r') {
>         this.#line();
>         this.skipLF = true;
>       } else if (char === '\n') {
>         this.#line();
>       } else {
>         this.line += char;
>         if (this.line.length > this.maxLineUnits) throw new Error('SSE line too large');
>       }
>     }
>   }
>
>   #line() {
>     const line = this.line;
>     this.line = '';
>     this.eventUnits += line.length + 1;
>     if (this.eventUnits > this.maxEventUnits) throw new Error('SSE event too large');
>
>     if (line === '') {
>       this.#dispatch();
>       this.eventUnits = 0;
>       this.pendingBlock = false;
>       return;
>     }
>     this.pendingBlock = true;
>     if (line.startsWith(':')) return;
>
>     const colon = line.indexOf(':');
>     const field = colon < 0 ? line : line.slice(0, colon);
>     let value = colon < 0 ? '' : line.slice(colon + 1);
>     if (value.startsWith(' ')) value = value.slice(1);
>     if (field === 'data') this.data.push(value);
>     else if (field === 'event') this.type = value;
>     else if (field === 'id' && !value.includes('\0')) this.id = value;
>     // This finite Fetch reader leaves retry timing to its caller.
>   }
>
>   #dispatch() {
>     const data = this.data.join('\n');
>     if (this.data.length > 0) this.onEvent({ type: this.type || 'message', data, id: this.id });
>     this.data = [];
>     this.type = '';
>   }
>
>   finish() {
>     if (this.line !== '' || this.pendingBlock || this.data.length !== 0 || this.type !== '') {
>       throw new Error('EOF before SSE blank-line delimiter');
>     }
>   }
> }
>
> const controller = new AbortController();
> const response = await fetch('/v1/accounts/acct-17/reports/42/events/search', {
>   method: 'POST',
>   headers: {
>     Authorization: 'Bearer token-supplied-by-the-application',
>     Accept: 'text/event-stream',
>     'Content-Type': 'application/json',
>   },
>   body: JSON.stringify({ stage: 'rendering' }),
>   signal: controller.signal,
> });
> async function rejectUnreadResponse(error) {
>   if (response.body) {
>     try { await response.body.cancel(error); } catch { /* 保留原响应错误 */ }
>   }
>   throw error;
> }
> if (response.status !== 200) await rejectUnreadResponse(new Error(`HTTP ${response.status}`));
> if (!response.body) throw new Error('Missing response body');
> const mediaType = response.headers.get('content-type')?.split(';', 1)[0].trim().toLowerCase();
> if (mediaType !== 'text/event-stream') await rejectUnreadResponse(new Error('Unexpected stream media type'));
>
> let sawTerminal = false;
> const appendSearchResult = (result) => showStatus(result.status, result.version, result.progress);
> const parser = new StrictSSEParser((event) => {
>   if (sawTerminal) throw new Error('Event after result.complete');
>   if (event.type === 'result.complete') {
>     sawTerminal = true;
>   } else if (event.type === 'report.updated') {
>     const result = JSON.parse(event.data);
>     appendSearchResult(result);
>   }
> });
> const reader = response.body.getReader();
> const decoder = new TextDecoder();
> try {
>   while (true) {
>     const { done, value } = await reader.read();
>     if (done) {
>       parser.feed(decoder.decode()); // 冲刷最后一个 UTF-8 字符
>       parser.finish();               // 不把 EOF 当作事件分隔符
>       if (!sawTerminal) throw new Error('Truncated event stream');
>       break;
>     }
>     parser.feed(decoder.decode(value, { stream: true }));
>   }
> } catch (error) {
>   try { await reader.cancel(error); } catch { /* 保留原读取或解析错误 */ }
>   throw error;
> } finally {
>   reader.releaseLock();
> }
> ~~~
>
> 解析器的上限是示例值，按 UTF-16 码元计数；生产接口按负载大小、并发和内存预算选定。`appendSearchResult` 是页面提供的展示函数，合并时仍按版本处理。

### WebSocket 怎样建立连接并持续授权

前面几种方式都是服务端单向推送。客户端也要在同一通道上持续发送时，就需要 WebSocket。

- **握手。** 在 HTTP/1.1 上，WebSocket 通过 `Upgrade` 握手和 `101 Switching Protocols` 建立，之后这条连接承载双方主动发送的消息。HTTP/2、HTTP/3 各自通过协商启用的 Extended CONNECT 扩展承载 WebSocket，要求两端和中间代理都支持，不能因为底层是 H2/H3 就假定可用。HTTP/1.1 的持久连接能复用请求—响应，但服务端仍要等客户端请求，不能借此主动推送。
- **子协议。** 浏览器的 `WebSocket` 构造器只接受 URL 和可选的子协议列表，不能设任意请求字段；请求了子协议时，服务器必须选中其中一个，握手才成功，本例是 `reports.v1`。
- **来源校验。** 浏览器在握手中发送 `Origin`，服务端应按允许列表校验。`Origin` 不是用户身份，非浏览器客户端可以伪造或省略它，所以它不能代替认证。WebSocket 握手不走 CORS 的响应许可，浏览器不会替服务端拦下跨站页面发起的握手；Cookie 是否随握手发送，取决于 `SameSite`、第三方 Cookie 等浏览器策略。服务端必须自己校验来源并认证连接，防止恶意站点借用户的 Cookie 建连。
- **持续授权。** 连接建立不等于对所有动作有权。每条订阅、每个读取或变更消息都要按资源和动作授权（见[授权章](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)）；连接存活期间权限可能变化，不能只在握手时检查一次。

页面转入后台、网络切换、代理空闲超时都可能中断连接，恢复仍要走下一节的游标路径。

### WebSocket 消息怎样恢复，慢客户端怎样限流

**恢复：两个位置回答两个问题。** 本例逐事件订阅从持久化的确认游标 `103` 开始。授权后，服务端在同一事件日志上取高水位 `W=105`，按序回放 104、105，再从 105 之后尾读；订阅期间追加的 106 仍能读到。服务端先发一条 `subscribed` 消息报告本轮回放边界：

~~~json
{"type":"subscribed","replayThrough":"105"}
{"type":"report.updated","cursor":"104","version":10,"status":"running","progress":80}
{"type":"report.updated","cursor":"105","version":11,"status":"ready","progress":100}
{"type":"report.updated","cursor":"106","version":12,"status":"ready","progress":100}
~~~

`after` 来自客户端的持久应用确认，回答“从哪里补”；`replayThrough=105` 是服务端捕获的回放水位，回答“本轮回放到哪里接上实时”，不是客户端已处理的位置。二者都是本应用协议的约定，WebSocket 本身不提供恢复。若处理并确认 104 后断线，客户端重连时带 `after=104`，服务端续读 105；断线时尚未确认的事件会重放。服务端回 `cursor.expired` 时，客户端停止自动重连、进入审计对账。

WebSocket 在线上可把一条消息拆成多个帧，协议按发送顺序重组，浏览器的 `message` 事件交付完整消息。单个连接内保序；重新建连后没有跨连接的顺序或历史，应用必须携带游标并重放。关闭或网络错误只说明通道断了，不说明最后一条业务消息是否已提交；要靠应用确认或重读权威快照。

**背压：协议级信用窗口。** 经典浏览器 `WebSocket` API 没有接收侧背压：即使 `message` 处理器是异步的、每次都 `await`，浏览器仍继续派发后续消息，应用无法让发送方等它。基于 Streams、能施加背压的 `WebSocketStream` 目前只有 Chromium 系浏览器实现，还不能作为跨浏览器基线。所以有界性要由双方协议保证：

- 服务端对每个订阅最多发 16 条尚未得到连续 ACK 的事件，收到累计 ACK 后才释放额度；每条文本事件不超过 64 KiB。服务端发送前必须执行同一大小限制。
- 客户端把进入串行业务队列的待处理数也限为 16，超额或超长就关闭连接，从持久 ACK 恢复。应用队列里的事件负载因此最多约 16 × 64 KiB = 1 MiB，不含对象和运行时开销。超长检查发生在浏览器已交付完整消息之后，只能挡住它进入应用队列。
- 关闭时先停止入队；已开始的副作用可以完成并持久推进 ACK，队列里其余任务在执行副作用前检查停止标记并跳过；队列排空后只重连一次。ACK 先持久化再尝试发送，断线或发送失败时，新连接从持久位置恢复。
- `bufferedAmount` 只统计本地 `send()` 已排队、尚未交给网络的字节，不表示对端收到或处理了。示例在 ACK 发送侧设 64 KiB 预警水位，超过就关闭恢复。
- 只关心最新值的通道，可以合并状态更新或丢弃可丢的进度。Ping/Pong 或应用心跳只说明连接可达，不证明业务副作用成功。

消费代码假设已认证的服务端按同一订阅连续、按序送达；`advanceContiguousAck` 只保护确认位置。接收端若还要防上游跳过事件，必须在副作用开始前验证该订阅的预期前驱，不能等写 ACK 时才发现缺口；真实游标可能不透明，不能一概用数字加一。

> [!example]- 持久确认、串行消费与断线恢复实现
>
> ~~~javascript
> async function connectReports42() {
>   const after = await loadDurableAck(42) ?? '103';
>   const socket = new WebSocket('wss://reports.example.test/realtime', ['reports.v1']);
>   const MAX_IN_FLIGHT = 16;      // 服务端同一订阅最多发 16 条尚未确认的事件
>   const MAX_EVENT_BYTES = 64 * 1024;
>   const MAX_ACK_BUFFERED_BYTES = 64 * 1024;
>
>   let delivery = Promise.resolve(); // 串行处理；最多 16 条待完成
>   let pending = 0;
>   let stopped = false;
>   let retryAfterClose = true;
>   let recoveryScheduled = false;
>
>   function stop(reason, retry = true) {
>     if (stopped) return;
>     stopped = true;
>     retryAfterClose = retry;
>     if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
>       socket.close(4000, reason);
>     }
>   }
>
>   function recoverAfterDrain() {
>     if (recoveryScheduled) return;
>     recoveryScheduled = true;
>     void delivery.then(() => {
>       if (retryAfterClose) scheduleReconnectWithJitter(connectReports42);
>       else void showDeliveryGapAndReconcile();
>     });
>   }
>
>   socket.addEventListener('open', () => {
>     if (stopped) return;
>     try { socket.send(JSON.stringify({ type: 'subscribe', accountId: 'acct-17', reportId: 42, after })); }
>     catch { stop('subscribe send failed'); }
>   });
>
>   socket.addEventListener('message', ({ data }) => {
>     if (stopped) return;
>     let message;
>     try {
>       if (typeof data !== 'string' || new TextEncoder().encode(data).byteLength > MAX_EVENT_BYTES) {
>         throw new Error('invalid or oversized message');
>       }
>       message = JSON.parse(data);
>       if (message === null || typeof message !== 'object' || Array.isArray(message)) {
>         throw new Error('message must be a JSON object');
>       }
>       if (message.type === 'subscribed') {
>         if (typeof message.replayThrough !== 'string') throw new Error('invalid subscribed message');
>       } else if (message.type === 'cursor.expired') {
>         if (typeof message.after !== 'string') throw new Error('invalid cursor.expired message');
>       } else if (message.type === 'report.updated') {
>         if (typeof message.cursor !== 'string' || !Number.isSafeInteger(message.version) ||
>             typeof message.status !== 'string' || !Number.isFinite(message.progress)) {
>           throw new Error('invalid report.updated message');
>         }
>       } else {
>         throw new Error('unknown message type');
>       }
>     } catch {
>       stop('invalid event');
>       return;
>     }
>
>     if (message.type === 'subscribed') {
>       showReplayBoundary(message.replayThrough); // 本例收到 "105"
>       return;
>     }
>     if (message.type === 'cursor.expired') {
>       stop('cursor expired', false); // 不要带过期游标自动循环重连
>       return;
>     }
>     if (pending >= MAX_IN_FLIGHT) {
>       stop('server exceeded credit window');
>       return;
>     }
>
>     pending++;
>     delivery = delivery.then(async () => {
>       try {
>         if (stopped) return; // 关闭后跳过已排队项；不启动它们的副作用
>         await applyEventIdempotently(message);
>         const cursor = await advanceContiguousAck(42, message.cursor);
>         // 先持久化，再尝试在线发送；若连接已关，重连会从持久值恢复。
>         if (!stopped && socket.readyState === WebSocket.OPEN) {
>           if (socket.bufferedAmount > MAX_ACK_BUFFERED_BYTES) {
>             stop('ack send backlog');
>             return;
>           }
>           socket.send(JSON.stringify({ type: 'ack', reportId: 42, cursor }));
>         }
>       } catch {
>         stop('event processing failed');
>       } finally {
>         pending--;
>       }
>     });
>   });
>
>   socket.addEventListener('error', () => stop('socket error'));
>   socket.addEventListener('close', () => {
>     stopped = true;             // 立即阻止新任务
>     recoverAfterDrain();        // 在途任务落定后只重连一次
>   });
> }
> void connectReports42();
> ~~~

服务端同样要限制慢客户端。Node.js `ws` 库的 `pause()`/`resume()` 能暂停或恢复接收事件，但已缓冲的事件仍可能继续派发，所以仍需有界队列。`bufferedAmount` 是库报告的已排队发送量，计入帧开销；发送前检查水位，检查之后追加的一条消息仍可能越过它，所以水位不是硬上限，应用要为每个客户端限制待发送字节和消息大小。接收方向要设 `maxPayload`：`message` 事件收到的已是完整组装的消息，事后检查长度限制不了接收缓冲。下面的片段只演示广播循环和慢客户端处理，假设广播的是可公开的教学内容；真实的报表事件只能发给已认证、且有权读取该报表的订阅者，不能把一个全局客户端集合当作授权范围。

> [!example]- Node.js `ws` 广播与慢客户端
> ~~~javascript
> const { WebSocketServer, WebSocket } = require('ws');
> const MAX_SINGLE_MESSAGE_BYTES = 64 * 1024;
> const server = new WebSocketServer({ port: 3000, maxPayload: MAX_SINGLE_MESSAGE_BYTES });
> const clients = new Set();
> const QUEUE_WATERMARK_BYTES = 256 * 1024;
>
> server.on('connection', (socket) => {
>   clients.add(socket);
>   socket.on('message', (data, isBinary) => {
>     // maxPayload 在完整 message 交付前限制单条接收消息的字节数。
>     for (const client of clients) {
>       if (client === socket || client.readyState !== WebSocket.OPEN) continue;
>       if (client.bufferedAmount > QUEUE_WATERMARK_BYTES) {
>         client.terminate();
>         continue;
>       }
>       client.send(data, { binary: isBinary }, (error) => {
>         if (error) client.terminate();
>       });
>     }
>   });
>   socket.on('close', () => clients.delete(socket));
>   socket.on('error', () => socket.terminate());
> });
> ~~~

### 回到权威状态：通道断了以后以谁为准

本章交出的是一套通道之外的恢复规则：先定恢复目标；快照与订阅衔接在同一日志位置；传输层的位置（`Last-Event-ID`、帧、连接）不等于业务确认，逐事件路径以持久、连续的应用 ACK 为准；游标过期时，只要状态就重置，逐事件就标记缺口去对账。

重新连上 SSE、重发 Fetch 或重建 WebSocket，都只恢复传输。本例 SSE 的 `reset` 是“取新快照、从其游标继续”；有限 Fetch 以 `result.complete` 加完整 EOF 确认一次查询结束；WebSocket 在持久游标仍可回放时退避重连并重新订阅，遇到 `cursor.expired` 就停止并对账。客户端要接回的若是已受理的异步任务，而不只是页面状态，就回到主线：先查稳定的任务状态资源，见[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。AI 运行按 `runId` 续读的应用实例，见[重连后怎样回到同一个运行](../../ai-engineering/runs/disconnect-cancel-and-user-input.md)。

> [!info]- 来源
> - SSE 字段语法、多行与空负载 `data`、单个前置 BOM、空行派发、EOF 丢弃未完成事件、`EventSource` 的凭据选项、`Last-Event-ID`、`retry`、`204` 停止重连、非 `200` 与错误媒体类型（“SSE：线格式”“EventSource 能做什么”）：[WHATWG HTML Living Standard, Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)，§9.2，2026-11-11 版，核对于 2026-11-12。
> - Fetch 请求与响应体、CORS（“流式 Fetch”）：[WHATWG Fetch Standard](https://fetch.spec.whatwg.org/)，Living Standard，2026-10-19 版；增量解码与 BOM：[WHATWG Encoding Standard](https://encoding.spec.whatwg.org/)，2026-10-19 版，§7.1–§7.2；可读流的取消、队列与背压：[WHATWG Streams Standard](https://streams.spec.whatwg.org/)，2026-10-25 版，§4.2.4；均核对于 2026-11-12。
> - 轮询、长轮询、挂起请求与流式传输经过中间代理时的超时与缓冲（“选通道”“长轮询”）：[IETF RFC 6202](https://www.rfc-editor.org/rfc/rfc6202.html)，2011-04，Informational，§2.1–§2.2、§3.2、§5.5；核对于 2026-11-12。
> - 反向代理缓冲及默认值（“代理缓冲与空闲超时”）：[NGINX `proxy_buffering`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering)；gzip 压缩缓冲：[NGINX `gzip_buffers`](https://nginx.org/en/docs/http/ngx_http_gzip_module.html#gzip_buffers)；官方文档核对于 2026-11-12。
> - 浏览器 `WebSocket` 构造器、消息与发送队列：[WHATWG WebSockets Standard](https://websockets.spec.whatwg.org/)，2026-10-19 版；接收侧无背压：[MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)；`WebSocketStream` 的背压与仅 Chromium 实现：[Chrome for Developers, WebSocketStream](https://developer.chrome.com/docs/capabilities/web-apis/websocketstream)，核对于 2026-11-16。
> - WebSocket 握手、帧与消息顺序、`Origin` 安全（“WebSocket 怎样建立连接并持续授权”）：[IETF RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html)，2011-12，§1.6、§4–§5、§10.1–§10.2；HTTP/2 Extended CONNECT：[IETF RFC 8441](https://www.rfc-editor.org/rfc/rfc8441.html)，2018-09，§3–§4；HTTP/3 Extended CONNECT：[IETF RFC 9220](https://www.rfc-editor.org/rfc/rfc9220.html)，2022-06，§3；来源允许列表、连接认证与消息级授权：[OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html)，Authentication and Authorization；均核对于 2026-11-12。
> - Node.js `ws` 的广播、`bufferedAmount`、`pause()`/`resume()`、`maxPayload` 与 `send` 回调：[ws API 文档](https://github.com/websockets/ws/blob/master/doc/ws.md)，核对于 2026-11-12；它是库文档，不是协议规范。
> - 高水位衔接回放与尾读、按订阅持久保存连续 ACK、`reset` 与 `cursor.expired`、信用窗口：本例定义的应用协议；SSE 与 WebSocket 标准不提供这些业务交付保证。SSE 解析器在本机 Node v26.13.1 上用跨块 UTF-8 输入和截断输入验证过。
## 40. 写请求超时后，怎样查清结果并安全重试？

前面几章讲的是一次同步请求怎样被识别、授权并按契约回应。从本章起，请求返回之后的工作才开始：响应可能丢失，工作可能还在别处进行。本章回答三件事：超时之后调用方到底知道什么；怎样用同一个操作身份取回原操作的当前状态；什么时候允许重试、等多久、由谁重试。手上的前提是：服务已经能认出可信主体并逐次授权（见[逐次授权](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)），HTTP 方法的安全与幂等语义已在[HTTP 语义与传输](#33.%20%E4%B8%80%E6%AC%A1%20HTTP%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%B5%8F%E8%A7%88%E5%99%A8%E5%88%B0%E8%BE%BE%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%8F%88%E5%B8%A6%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)讲过。

### 案例：导出请求在响应途中丢失

沿用主线四的报表服务。`acct-17` 的成员 `user-17` 有 `report:export` 权限，要把报表 42 的 2026 年第二季度数据导出成 CSV。生成要几十秒，所以服务不在请求里生成，而是创建一个可查询的 job (任务)。本章新增三个标识符：

- `export-demo-415`：客户端为这次导出意图生成的 idempotency key (幂等键)，重试时保持不变；
- `job-demo-731`：服务受理后分配的 job ID；
- 状态地址 `/v1/jobs/job-demo-731`，取消用 `DELETE` 同一地址，下载用 `/v1/jobs/job-demo-731/result`。

幂等键、报表 ID 42 和 job ID 是三种身份，刻意不共用数字，不能互相替代。

~~~http
POST /v1/accounts/acct-17/reports HTTP/1.1
Host: api.reports.example.test
Idempotency-Key: export-demo-415
Content-Type: application/json

{"reportId":42,"period":"2026-Q2","format":"csv"}
~~~

服务把 job 写进数据库并提交，然后返回 `202 Accepted` 和 `Location: /v1/jobs/job-demo-731`。这个 202 在网络里丢了，浏览器只看到超时：

~~~mermaid
sequenceDiagram
    participant C as 浏览器
    participant A as API
    participant D as 数据库
    C->>A: POST 导出，键 export-demo-415
    A->>D: 写 job-demo-731 与幂等记录
    D-->>A: 同一事务提交
    A--xC: 202 在途中丢失
    Note over C,D: job 已存在；浏览器只知道“超时”
    C->>A: 重放原 POST，同键同正文
    A->>D: 重新授权后按作用域键读记录
    D-->>A: 已有 job-demo-731 及其当前状态
    A-->>C: 202 + Location: /v1/jobs/job-demo-731
    C->>A: GET /v1/jobs/job-demo-731
~~~

下面先说明超时让调用方处于什么状态，再看重放要满足的合同，最后讲重试的时间和次数。

### timeout 和 deadline 各限定什么？

timeout (超时) 限定一次等待或一次操作最多持续多久；deadline (截止时间) 是整条调用链最晚必须完成的时间点。两者的差别在串行调用里最明显：最外层只给整次操作 2 秒，如果每一层都重新给下游一份完整的 2 秒 timeout，三个串行调用最坏要等 6 秒：单是第一个调用就可能耗尽最外层的全部预算，后两个调用已经没有时间。

因此每一层都应该把**剩余时间**（或绝对截止时刻）传给下游，并从中扣出自己清理资源和回包所需的时间。连接建立、TLS 握手、读取响应正文是否都算在某个库的 timeout 里，各客户端 API 的定义不同，要逐个核对。

deadline 到了，调用方停止等待，但这只是**调用方**不再等。下游的工作可能还在运行，也可能已经提交。这就是下一节的问题。

### 超时之后，调用方处于什么状态？

一次写请求超时，调用方从自己的连接上分不清四种情况：请求没到服务器；服务器处理失败并回滚；事务还在进行；事务已提交但响应丢失。最后一种情况就是本例：`job-demo-731` 已经存在，浏览器却一无所知。这种状态叫 unknown outcome (未知结果)。

未知结果只能靠**原操作的身份**去消除，规则有四条：

1. **同键同参重放，取回同一操作的当前状态。** 浏览器用同一个 `export-demo-415` 和同样的正文重放原 POST。服务重新认证、重新授权，按作用域键找到已有记录，核对参数一致后返回 `job-demo-731`，不再创建第二个 job。返回的是该操作**现在**的状态：如果这期间 job 已经成功，就返回成功；如果已被合法取消，就返回 `cancelled`，不会把它重新激活。重放恢复的是同一个业务操作，不要求逐字节重现首次响应。
2. **查不到不等于失败。** 服务按键查不到记录，只说明这条查询没看到已提交的记录；原事务可能还没提交。重放必须继续经过数据库的唯一裁决，不能“先查一下，没有就当新请求放行”。
3. **只读查询保持只读。** 状态查询接口查不到记录时，不能顺手启动原操作。启动操作只能走带幂等键的原写请求。
4. **连接断开不等于取消。** 已经受理的 job 不会因为浏览器断线而停下；要取消，就向已知地址发 `DELETE`。

本例的服务没有“按幂等键查询”的 GET 接口，所以 202 丢失后的唯一入口是重放原 POST。拿到 `Location` 之后，客户端改用 `GET /v1/jobs/job-demo-731` 轮询。202 本身承诺了什么、服务在返回 202 之前必须持久化哪些东西，见下一章[耗时任务怎样被持久受理](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)。

这里的未知结果发生在 HTTP 响应的交付路径上。数据库自己也可能让 `COMMIT` 结果未知（提交请求发出后连接断开）；那时的处置同样是“保留原键回查，不换新键”，见[事务能保证什么](#24.%20%E4%BA%8B%E5%8A%A1%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%8C%E5%B9%B6%E5%8F%91%E4%BA%8B%E5%8A%A1%E5%90%84%E8%83%BD%E7%9C%8B%E8%A7%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 方法幂等和幂等键有什么不同？

RFC 9110 定义的 idempotent method (幂等方法) 指：同一个请求重复多次，**预期的服务端效果**与执行一次相同；它不禁止每次请求都记一条日志。`PUT` 和 `DELETE` 是幂等方法，`POST` 不是（详见[HTTP 语义与传输](#33.%20%E4%B8%80%E6%AC%A1%20HTTP%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E4%BB%8E%E6%B5%8F%E8%A7%88%E5%99%A8%E5%88%B0%E8%BE%BE%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%8F%88%E5%B8%A6%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)）。

给 POST 加上幂等键，是另一回事：这是应用自己定义的去重与结果重放约定。它的效果靠服务端的数据和约束实现，HTTP 不替它保证。两者也不能互相代替：把 POST 改成 PUT 不会让“创建 job”自动去重；给 PUT 加幂等键也不会改变它的协议语义。

一个可用的幂等键合同要写清下面这些要素：

| 要素 | 本例的选择 | 为什么需要 |
| --- | --- | --- |
| 作用域 | `(account_id, principal_id, key)` | 防止另一个主体猜到键就读到别人的私有结果 |
| 请求指纹 | 规范化后的 `reportId`、`period`、`format` 的摘要 | 同键异参是客户端违约，返回明确冲突，不能把旧结果当成新意图的结果 |
| 裁决方式 | 数据库唯一约束 | 两个同键请求同时到达时只有一个能提交 |
| 重放规则 | 返回同一操作的当前状态 | 见上一节 |
| 保留期与窗口外语义 | job 与幂等映射在终态后保留 14 天 | 见下一节 |

前三项的数据库实现（唯一约束怎样裁决、冲突方为什么要整笔回滚再用新事务回查、为什么效果和幂等记录必须在同一事务提交）在[两个请求争夺最后一件库存时怎样只预留一次](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)讲完整。本章只用它的结论：**作用域键加指纹由唯一约束裁决，败方回滚后新开事务读胜者，同指纹返回胜者的记录，异指纹报冲突。**

### 去重要覆盖多长时间？

幂等记录不能永远保留，但保留得太短会让重复“漏网”。判断标准只有一条：**去重保护必须覆盖这个操作的所有副本可能到达并提交的时间**，包括原请求本身、每一次重放、仍在服务器里执行的请求，以及还可能晚到的请求。

下面这个构造出来的时序说明“覆盖不到在途请求”会发生什么。假设某个服务不用数据库唯一约束，而是请求一到就在缓存里抢占键，并给它 60 秒有效期：

| 时刻 | 事件 |
| ---: | --- |
| 0 s | 原请求 A 到达，抢到键，开始执行 |
| 5 s | A 所在进程长时间停顿（例如等锁或 GC），客户端超时 |
| 60 s | 键过期被删除；A 仍在执行中 |
| 70 s | 客户端重放 B，查不到键，当作新请求执行 |
| 75 s | B 提交，产生第一份效果 |
| 90 s | A 恢复并提交，产生第二份效果 |

问题不在 60 秒太短，而在有效期没有和“A 最晚何时还能提交”绑定。两种修法：

- 让效果与幂等记录在**同一个数据库事务**里提交，并由唯一约束裁决。这样 A 和 B 谁后提交，谁就撞上唯一键，只能读回胜者。本例采用这种做法。
- 如果必须用有效期，就要先给在途请求设一个服务端强制的上限（例如数据库语句和事务超时），再让有效期至少覆盖“最后一次可能开始执行的时刻 + 这个上限 + 时钟偏差 + 余量”。webhook 支线的[去重墓碑保留期](#42.%20%E6%94%B6%E5%88%B0%E4%B8%80%E6%9D%A1%20webhook%20%E5%9B%9E%E8%B0%83%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E7%A1%AE%E8%AE%A4%E5%AE%83%E7%9C%9F%E5%AE%9E%E3%80%81%E6%9C%AA%E8%A2%AB%E9%87%8D%E6%94%BE%EF%BC%8C%E5%B9%B6%E5%8F%AF%E9%9D%A0%E5%9C%B0%E5%8F%97%E7%90%86%EF%BC%9F)就是按这个思路推导的。

覆盖了在途请求，还要声明**重放窗口**：服务保证在多长时间内认得同一个键。窗口之后若把记录全部删掉，服务就无法仅凭一个键字符串分辨“这是旧操作的重放”还是“这是一个新意图”。本例的键不带可验证的有效期，因此：

- 窗口内，保留足以识别该键的记录（作用域键、指纹、指向的 job）；
- 窗口外若仍要拒绝旧键，就必须继续保留一条 tombstone (墓碑)：只留键与指纹，不留结果；
- 合同要写明窗口外的重放会得到什么，调用方不能把过期的旧操作当新请求重做。

本例的具体数字（结果 7 天、job 与幂等映射 14 天）和 `result_expired` 的处理见[状态、取消、结果与保留期契约](#%E7%8A%B6%E6%80%81%E3%80%81%E5%8F%96%E6%B6%88%E3%80%81%E7%BB%93%E6%9E%9C%E4%B8%8E%E4%BF%9D%E7%95%99%E6%9C%9F%E6%80%8E%E6%A0%B7%E7%BA%A6%E5%AE%9A%EF%BC%9F)。

### 远端副作用超时后，什么时候可以重发？

本地数据库事务只管本库。若操作还要调用外部系统，例如付款、发通知或写另一家的 API，远端效果不在事务里：本地回滚撤不回远端，超时也不会自动撤销远端已经发生的效果。

transactional outbox (事务发件箱，下文 outbox) 能做的是让“本地结果”和“将来必须发出的指令”一起提交，并让 relay (中继) 在崩溃后重发（见[下一章](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)）。它保证指令不丢，但会重复，不会替远端去重。避免重复付款，仍要靠远端按稳定的操作键去重；对账能发现重复，却不能阻止重复。

**远端操作键怎样构造。** 用权威且全局唯一的身份加上操作类型和版本，例如 `job-demo-731:report-ready:v1`。不要直接用客户端的 `export-demo-415`：它只在 `(acct-17, user-17)` 范围内唯一，另一个主体完全可能用同一个字符串。同一个操作的每次重发都必须带同一个键和同一份请求内容；远端要按“同键、同请求摘要”去重，并提供按键查询或明确的去重保留期。

远端调用超时或结果不明时，按下表决定下一步。这是全领域唯一一张这样的决策表，AI 的退款对账、webhook 接收方的后续处理都引用它：

| 查证结果 | 处理 |
| --- | --- |
| 按原操作键查询，远端确认已完成 | 在本地持久记录完成，停止重发 |
| 结果仍未知（包括查询接口暂时不可用），但远端对“同键、同请求摘要”的去重保证仍然有效 | 在保证有效期内用原键、原摘要重试，并继续对账 |
| 结果未知，且没有仍有效的去重保证，或摘要不一致，或已过远端保留期 | 保持“未知”，转人工对账；不换新键自动重发 |

两个系统的期限互不延长。本地的重试窗口再长，也不会让远端的去重保证多保留一天；远端保证先过期，本地即使还在自己的窗口内，也不能再盲目重发。

> [!info] 应用实例：AI 运行里的退款
> AI 工程把这张决策表落到一次退款上：退款请求超时后进入专门的未知状态，只读对账查清结果，满足同键前提才重放。状态名和支付提供方的实例见[退款请求超时后，怎样查清结果而不重复扣款](../../ai-engineering/runs/external-writes-and-reconciliation.md)。

### 重试要等多久、最多试几次？

有了幂等键，重放本身是安全的，但每次重试仍然消耗时间和下游容量。决定重试之前先问两件事：

1. **失败可能自己恢复吗？** 参数校验失败、同键异参冲突、无权访问，原样再发一百次也不会成功，应该修正请求或停止。超时、连接中断、`503`、`429` 才可能随时间恢复。
2. **这次重放安全吗？** 只有带原幂等键、原参数的写请求，或本身幂等的方法，才可以重放。

对可恢复的失败，使用有上限的 exponential backoff (指数退避)，并加 full jitter (全抖动) 把各客户端的重试时刻打散：

~~~text
cap(n)  = min(max_delay, base_delay × 2^n)      n 从 0 开始，第一次失败后 n = 0
wait(n) = 在 [0, cap(n)] 上均匀随机取值
~~~

设 `base_delay = 100 ms`、`max_delay = 800 ms`，前三次退避的区间依次是 0–100 ms、0–200 ms、0–400 ms，之后封顶在 0–800 ms。这些数是服务策略，不是通用常数。

次数和时间还要受两条约束：

- **剩余 deadline。** 只有剩余时间装得下“这次等待 + 下一次调用 + 处理和回包”，才发起重试；否则停下，把结果保留为未知。“最多 3 次尝试”包括首次调用，所以最多只有两次退避。
- **`Retry-After`。** 服务明确要求等待时（`503` 或 `429` 响应携带 `Retry-After`），按接口契约尊重这个等待，不能用自己算出的更短退避绕过它；等待若超出剩余 deadline，就直接停下。

> [!example] 2 秒截止时间下的重试复盘
> 客户端总截止时间 2 s，最多 3 次尝试。第一次调用用了 1.2 s 后超时，剩余 0.8 s。
>
> - 这是第一次失败，`n = 0`，等待上限 `min(800, 100 × 2⁰) = 100 ms`。
> - 本例为下一次调用预留至少 700 ms，处理与回包再留 50 ms，所以能用于等待的时间最多是 `800 − 700 − 50 = 50 ms`。
> - 全抖动抽到 80 ms（落在 0–100 ms 内，本身合法），总需求 `80 + 700 + 50 = 830 ms`，比剩余预算多 30 ms。
>
> 结论：不再重试，停下并把导出状态记为未知；之后用同一个 `export-demo-415` 重放或查询 job。700 ms 是本例选定的最小调用预算，真实调用没有可预知的固定耗时，应按时延目标和观测数据设定。

![剩余预算 800 毫秒，计划等待 80 毫秒、调用 700 毫秒、处理返回 50 毫秒，共 830 毫秒，超出 30 毫秒](../../engineering-foundations/services/resources/api-retry-deadline-budget.svg)

客户端停止等待之后，尚未查证的写入仍是未知结果，不能自动改记为“失败且未生效”。

### 为什么只能让一层重试？

重试会在调用链上逐层相乘。设一条串行调用链上有 5 层调用者，每层对下一层都“最多尝试 3 次，全部失败才向上报错”。最上层发出一次请求，它下面一层最多收到 3 次，再下一层最多 `3² = 9` 次，依此类推，5 层调用者之下最深的那个服务最多收到 `3⁵ = 243` 次。这是最深层单独承受的次数，不是整条链所有调用的总和。下游刚开始变慢时，这种放大正好把它彻底压垮。

所以通常只让一层负责重试：选**最了解端到端 deadline 和幂等性**的那一层（往往是最外层的客户端或网关），其余各层把失败明确地交上去，不再自行重试。

### 取消在这里意味着什么？

deadline 用完或用户放弃时，调用方会发出取消。cancellation (取消) 只是告诉仍在运行的工作“结果已经不需要了”：信号要传给下游，由下游在安全的检查点停止多余计算、释放资源。它**不证明**工作已经停下，也不证明已提交的副作用被撤回；副作用是否发生，仍要查权威记录。这条“取消只是请求”的原则在 OS 线程、Node.js、Python 里的具体表现，见[一份工作该交给进程、线程还是异步 I/O](#14.%20%E4%B8%80%E4%BB%BD%E5%B7%A5%E4%BD%9C%E8%AF%A5%E4%BA%A4%E7%BB%99%E8%BF%9B%E7%A8%8B%E3%80%81%E7%BA%BF%E7%A8%8B%E8%BF%98%E6%98%AF%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)。

对已经受理的导出 job，浏览器断线只结束这一次连接。要停止 `job-demo-731`，客户端必须对已知地址发 `DELETE`，而服务端怎样处理“取消和 worker 领取同时发生”，见[任务失败、被取消或 worker 失联后怎样收尾](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)。尚未受理的请求内工作（例如直接流式返回的小 CSV）则可以在断线后结束。

### 本章产出与下一步

到这里，调用方手上有一个稳定的操作身份 `export-demo-415`，并知道：超时是未知结果；同键同参重放取回 `job-demo-731` 的当前状态；远端副作用按决策表处理；重试只在一层、受 deadline 约束地进行。还没回答的是服务端那一侧：返回 202 之前，服务到底持久化了什么，才能保证这个 job 一定会被某个 worker 执行？这是[耗时任务怎样被持久受理，并保证一定会被唤醒](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)的问题。

> [!info]- 来源
> - 幂等方法的定义（重复请求的预期服务端效果与一次相同）、`202 Accepted` 的语义、`Retry-After`：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§9.2.2、§15.3.3、§10.2.3，2022-06，核对于 2026-11-11。幂等键的作用域、指纹、当前状态重放与保留期是本例的应用合同，不是 RFC 规定。
> - 副作用、超时、重试安全与客户端请求令牌：[AWS Builders’ Library, Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)，核对于 2026-11-11。
> - timeout、带上限的退避与多层重试的放大：[AWS Builder Center, Timeouts, retries, and backoff with jitter](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter)，原文 2019-12-05，核对于 2026-11-11；[Google SRE Book, Addressing Cascading Failures — Retries](https://sre.google/sre-book/addressing-cascading-failures/#retries)，2016。
> - full jitter 的均匀等待区间：[AWS Architecture Blog, Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)，2015-03-04（2023 年补充 SDK 说明）；本章只采用其算法定义，不把文中的模拟收益当成通用性能保证。
> - deadline 向下游传播与协作式取消：[gRPC Deadlines](https://grpc.io/docs/guides/deadlines/)，核对于 2026-11-11；具体行为取决于各 API。
> - 远端副作用的操作键与“查询确认 / 同键重试 / 人工对账”决策：属于工程推论（outbox 不替远端去重，远端须按同键同摘要去重）；远端是否提供按键查询和去重期限，以各提供方的契约为准。
## 41. 耗时任务怎样被持久受理，并保证一定会被唤醒？

上一章从调用方一侧看导出请求：202 丢了，用 `export-demo-415` 重放就能取回 `job-demo-731`。本章换到服务一侧，回答：什么工作值得做成后台 job；返回 `202 Accepted` 之前必须把哪些东西写进数据库；数据库提交之后，怎样保证一定有消息去唤醒 worker (工作进程)，而且不会唤醒一个不存在的 job。沿用主线四的导出案例，本章不新增标识符，只补 job 的状态机和保留期。

### 这份工作需要做成后台 job 吗？

先问同步能不能做完。如果一次有界读取能稳定地在调用方 deadline (截止时间) 和尾延迟目标内完成，同步接口只需校验、读取、返回 CSV，不需要状态表、队列、重试和结果清理。只有出现下面任一情况，持久 job 才值得它带来的复杂度：

- 工作可能超出单个请求的时间预算；
- 浏览器断线后工作仍须继续，之后还要能查进度、拿结果；
- 工作需要和 API 进程的执行资源隔离，不能占着处理 HTTP 请求的线程和连接。

还有一条中间路线：在请求里直接流式返回 CSV。它和持久 job 是两种生命周期：

| | 请求内流式响应 | 持久 job |
| --- | --- | --- |
| 资源占用 | 正文发完之前一直占着连接、游标和处理资源 | API 只占受理事务那一小段；执行资源归 worker |
| 断线之后 | 已做的读取作废，不留下可查询的结果 | job 继续，之后可查状态、下载结果 |
| 谁让上游慢下来 | 请求自己的 deadline 和流背压 | 受理前的准入检查（见[容量章](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)） |
| 适合 | 小而快、可以整份重来的结果 | 慢、大、必须可恢复的结果 |

流式响应的资源何时释放（例如 FastAPI 的 `yield` 依赖要覆盖整个正文发送），见[异步 FastAPI 接口为什么仍会阻塞](#18.%20%E5%BC%82%E6%AD%A5%20FastAPI%20%E6%8E%A5%E5%8F%A3%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BB%8D%E4%BC%9A%E9%98%BB%E5%A1%9E%EF%BC%8C%E5%8F%96%E6%B6%88%E5%92%8C%E8%B5%84%E6%BA%90%E5%8F%88%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%EF%BC%9F)；背压怎样逐段传回源头，见[流怎样把“慢下来”传回源头](#20.%20%E6%B5%81%E6%80%8E%E6%A0%B7%E6%8A%8A%E2%80%9C%E6%85%A2%E4%B8%8B%E6%9D%A5%E2%80%9D%E9%80%90%E6%AE%B5%E4%BC%A0%E5%9B%9E%E6%BA%90%E5%A4%B4%EF%BC%8C%E4%B8%AD%E9%80%94%E5%A4%B1%E8%B4%A5%E5%8F%88%E7%95%99%E4%B8%8B%E4%BB%80%E4%B9%88%EF%BC%9F)。

还要记住一点：队列只保存“待唤醒”的工作，本身不增加处理能力。让用户在断线后仍能查到“服务接受了什么、进展如何、结果是什么”的，是数据库里的 job 记录，不是队列里的消息。

### 201 和 202 承诺的是不同的事

两个状态码都可能伴随 `status: "queued"`，但承诺不同：

- `201 Created` 表示**一个资源已经创建**。例如 `POST /api/reports` 新建一条名为 `Weekly overview` 的报表记录，返回 `201` 和 `Location: /api/reports/44`。记录已经存在，即使它的某个字段还写着 `queued`，也不表示成品已经生成。
- `202 Accepted` 表示**请求已被接受处理，但处理还没完成**，RFC 9110 也明说不承诺最终一定成功。响应应给出一个让调用方继续查询的地址。

导出属于后者：`POST /v1/accounts/acct-17/reports` 受理的是一项可能失败的作业，所以返回 202 和 job 的状态地址，而不是假装结果已经存在。

### 受理之前要检查什么？

进入受理事务之前，API 依次做完这些便宜的检查，任何一项不通过都直接拒绝，不留任何记录：

1. **认证与授权。** 确认当前主体，确认它对 `acct-17` 有 `report:export`；`report:read` 不包含导出权限。路径里的账户号和随机 job ID 都不是凭据。授权的完整骨架见[服务怎样逐次确认主体能做这个动作](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)。
2. **范围与上限。** 时间范围、格式、预计页数。本例每个 job 最多读 12 页；如果从参数就能判断会超过 12 页，在受理前拒绝。
3. **参数规范化。** 把影响执行的参数整理成规范形式（例如统一期间写法、去掉无关字段），再据此计算请求指纹。指纹只用于比较“是不是同一个意图”，worker 执行所需的参数另存在 job 行里。

执行期还有两条边界在这里一并约定：读到第 12 页仍未读完，worker 提交一个明确的失败，而不是无限分页；页数上限管不住单次 I/O 的无限等待，所以每页读取和对象上传各自要有强制执行的 deadline。

### 202 之前必须提交什么？

HTTP 的 202 只要求“已接受”。本服务把它定义得更强：**只有 job 行、一条待发布的 outbox (事务发件箱) 意图和一个等待槽在同一个数据库事务里提交之后，才返回 202。** 有了这条应用合同，202 才是一个可以查询、可以恢复的承诺，而不是“内存里排了一个后台任务”。

受理事务按顺序做四件事：

~~~text
BEGIN
  1. 插入 job 身份：(account_id, principal_id, idempotency_key) 唯一，附请求指纹
     → 唯一约束说这不是新意图：回滚，新事务读胜者（同指纹返回原 job，异指纹报冲突）
  2. 只有新意图才继续：锁定全管线共享的额度行，扣 1 枚速率令牌、占 1 个等待槽
     → 令牌或等待槽不足：回滚，在 202 之前拒绝（429 / 503）
  3. 补齐 job：规范化参数、status = 'queued'、available_at = 数据库当前时间
  4. 插入 outbox 意图：新的 intent_id、job_id、state = 'pending'
COMMIT  → 只有收到提交成功，才返回 202 + Location: /v1/jobs/job-demo-731
~~~

三处细节分别由别的章节负责：

- 第 1 步的唯一裁决和“败方整笔回滚、新事务回查”，是主线三的结论，见[两个请求争夺最后一件库存时怎样只预留一次](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。同键重放不创建第二个 job，也不再扣令牌、不再占槽。
- 第 2 步为什么必须是一条共享的额度行，以及 429 与 503 怎样区分，见[一条异步管线能接多少工作](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)。
- 如果 `COMMIT` 发出后没收到结果，API 不能假定成功，也不能宣称失败；客户端用原幂等键重放即可，唯一键会把重放和可能已提交的记录对应起来（见[上一章](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)）。

![新请求经过认证、授权和范围限制后，在 job、outbox 与等待槽同事务提交后才返回 202](../../engineering-foundations/services/resources/system-design-admission.svg)

图里只画了首次受理成功的路径。受理成功后的响应：

~~~http
HTTP/1.1 202 Accepted
Location: /v1/jobs/job-demo-731
Content-Type: application/json

{"jobId":"job-demo-731","status":"queued","cancelRequested":false,"statusUrl":"/v1/jobs/job-demo-731"}
~~~

### 数据库和消息代理之间的缺口怎样补上？

job 已经提交，接下来要通知 worker。通知走 message broker (消息代理，下文 broker)。问题在于：数据库和 broker 没有一个共同的原子事务，两步写总有一步可能在另一步之后失败。这叫 dual write (双写) 缺口：

| 顺序 | 中途崩溃的后果 |
| --- | --- |
| 先提交 job，再直接发消息 | 进程在两步之间崩溃，job 留在数据库里，永远没人唤醒 |
| 先发消息，再提交 job | 事务回滚后，消息指向一个不存在的 job |

outbox 的全称是 transactional outbox (事务发件箱)，做法是：把“将来必须发出这条消息”也写成一行数据，和 job 放在**同一个数据库事务**里提交（就是受理事务的第 4 步）。之后由独立的 relay (中继) 进程扫描未发布的意图，把消息发给 broker，再回写这条意图的状态。

outbox 消除了“提交了却没人发”，但换来了另一种情况：relay 可能在 broker 已接收、自己还没回写状态时崩溃，重启后把同一意图再发一次。所以：

- **消息会重复。** worker 必须依据数据库里的 job 状态做条件领取来去重，不能假设每条消息只投递一次（见[下一章](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)）。
- **发布成功不代表已处理。** relay 只有按所选 broker 的契约核实发布结果、路由和持久性之后，才把意图标为已发布；即使如此，这也只说明 broker 收下了消息，不说明 worker 收到、处理或完成。三种确认各证明什么，见[发布确认、消费者确认和业务完成各证明什么](#44.%20%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。
- **消息只带稳定的 job ID。** 不把原始请求正文或敏感筛选条件塞进消息；worker 需要的规范化参数在 job 行里，worker 拿到 ID 后去数据库读。

outbox 只保证本地意图不丢。它不替远端系统去重：如果 worker 之后还要调用外部服务，重复与未知结果的处理见[远端副作用的决策表](#%E8%BF%9C%E7%AB%AF%E5%89%AF%E4%BD%9C%E7%94%A8%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%8F%AF%E4%BB%A5%E9%87%8D%E5%8F%91%EF%BC%9F)。

### job 状态机与 outbox 各有自己的生命周期

job 有五个持久状态。下图回答“谁在什么条件下把 job 从一个状态推到另一个状态，同一事务里还改了什么”；三个终态（`succeeded`、`failed`、`cancelled`）一旦提交，不再回到 `queued` 或 `running`。

~~~mermaid
stateDiagram-v2
    [*] --> queued : API 受理事务提交<br/>占等待槽，插入 pending 意图
    queued --> running : worker 条件领取<br/>attempt + 1，写租约，归还等待槽
    running --> queued : worker 重试或恢复器重排<br/>预留等待槽，新 available_at，新 outbox 意图
    queued --> cancelled : API 取消<br/>归还等待槽（只还一次）
    running --> cancelled : 已有 cancel_requested<br/>由当前 attempt 或恢复器提交
    running --> failed : 不可重试错误、attempt 用尽或重排无槽<br/>authorization_revoked / attempts_exhausted / capacity_exhausted
    running --> succeeded : 当前 attempt 条件提交<br/>结果引用 + report.ready 意图同事务
    note right of running
        cancel_requested 是 running 上的标志，不是状态
    end note
~~~

每条边都是一次条件写入：条件里带着写入者看到的状态，离开 `running` 的边还带 attempt，后到者更新零行。领取的条件与栅栏见[下一章](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)，重排、取消与恢复器的判断顺序见[收尾一章](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)。各状态在行上留下的事实：

| 状态 | 持久字段与对外表现 |
| --- | --- |
| `queued` | 持有一个等待槽；`available_at` 到了才能领取。唤醒消息此刻可能还在 outbox 里，也可能已进入 broker |
| `running` | 等待槽已归还；当前 attempt (执行尝试) 编号和 lease (租约) 到期时间已写入 |
| `succeeded` | 当前 attempt 的私有结果对象引用 |
| `failed` | 有限错误码，如 `authorization_revoked`、`attempts_exhausted`、`capacity_exhausted` |
| `cancelled` | 不暴露结果对象 |

另外几条不变的规则：

- 每个 job 最多 3 次 attempt，包含首次领取，即最多两次重试。这个上限在受理时写进 job 行（`max_attempts = 3`），之后改部署配置不能悄悄改变已有 job 的上限。
- job 行至少保存：job ID、账户与原请求主体、`report_id`、规范化参数、请求指纹与幂等键、创建时间、`max_attempts`、当前 attempt、租约到期时间、`available_at`、是否持有等待槽、`cancel_requested`、终态与成功时间、结果到期时间、私有结果引用、有限错误码。
- 所有时间判断用数据库时钟。首次受理时 `available_at` 取数据库当前时间；延迟重试时保存退避到期的时刻。relay 和 worker 用同一个时间基准，不各自看本地时钟。

outbox 意图有自己的生命周期，不能拿它代替 job 状态。每一轮排队（首次受理、每次重排）都插入一条**新的**意图，各有唯一的 `intent_id`：

~~~mermaid
stateDiagram-v2
    direction LR
    [*] --> pending : 首次受理或每次重排<br/>插入新的 intent_id
    pending --> published : relay 核实发布结果后<br/>以 intent_id 和 pending 为条件回写
    published --> [*] : 过了审计与排障保留期<br/>按策略删除
~~~

relay 的回写语句：

~~~sql
UPDATE report_outbox
SET state = 'published', published_at = clock_timestamp()
WHERE intent_id = :intent_id AND state = 'pending';
~~~

这样，上一轮意图迟到的发布回执只会改它自己那一行，不会把新一轮的意图误标为已发布。这种“按身份条件回写”是栅栏原理的一个实例，原理本身在[怎样保证一个任务同一时刻只由一个 worker 推进](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)讲。

清理也按各自的生命周期：未发布的意图必须保留，不能和结果对象用同一个删除条件。

### 状态、取消、结果与保留期怎样约定？

调用方之后通过三个端点和 job 打交道，每个端点都按当前调用者重新授权：

- `GET /v1/jobs/job-demo-731`：返回持久状态和有限错误码。
- `DELETE /v1/jobs/job-demo-731`：表达“请求停止”，不代表计算已经停止。运行中的 job 可以继续显示 `running`，同时带 `cancelRequested: true`。取消和领取、和成功提交怎样竞争，见[任务失败、被取消或 worker 失联后怎样收尾](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)。
- `GET /v1/jobs/job-demo-731/result`：只有 `succeeded` 且结果仍在保留期内才允许下载。

保留期分两层，解决不同问题：

| 记录 | 本例保留期 | 计时起点 | 到期之后 |
| --- | --- | --- | --- |
| 结果对象 | 7 天 | 成功事务提交时写入 `succeeded_at`，同时写 `result_expires_at = succeeded_at + 7 天` | job 仍是 `succeeded`，下载端点返回 `result_expired`；同一幂等键仍指向原 job，不自动重新生成 |
| job 行与最小幂等映射 | 14 天 | 每种终态都写 `terminal_at`，从这里起算 | 不再提供重放保证；若仍要拒绝这个旧键，只能保留一条墓碑 |

14 天比 7 天长，是为了覆盖更长的客户端重试窗口：结果过期之后，客户端用同一个键重放，仍然得到“这是原来那个 job，结果已过期”，而不是一个新 job。墓碑与重放窗口的一般规则见[去重要覆盖多长时间](#%E5%8E%BB%E9%87%8D%E8%A6%81%E8%A6%86%E7%9B%96%E5%A4%9A%E9%95%BF%E6%97%B6%E9%97%B4%EF%BC%9F)。

最后一条容易漏掉：job 的 `status` 和 `attempt` 只描述执行过程。如果产品要告诉用户“这份报表是截至哪个时点的数据”，就要另存数据水位或快照语义作为结果元数据；给查询加一个时间过滤，并不能保证 12 页分页读取都来自同一个快照（见[怎样无重复、无遗漏地分页读取一个还在变化的集合](#29.%20%E6%80%8E%E6%A0%B7%E6%97%A0%E9%87%8D%E5%A4%8D%E3%80%81%E6%97%A0%E9%81%97%E6%BC%8F%E5%9C%B0%E5%88%86%E9%A1%B5%E8%AF%BB%E5%8F%96%E4%B8%80%E4%B8%AA%E8%BF%98%E5%9C%A8%E5%8F%98%E5%8C%96%E7%9A%84%E9%9B%86%E5%90%88%EF%BC%9F)）。

### 本章产出与下一步

受理事务提交之后，数据库里有：`queued` 的 `job-demo-731`、它占着的一个等待槽、一条 `pending` 的 outbox 意图。relay 会把只带 job ID 的消息发出去，可能不止一次。下一个问题是：消息到达多个 worker 时，怎样保证只有一个 worker 推进这个 job，并且一个停顿后又醒来的旧 worker 不会覆盖新结果？见[怎样保证一个任务同一时刻只由一个 worker 推进](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)。

如果这次 job 成功后还要用 HTTP 回调通知另一个服务，接收方怎样验证并受理这条回调，是支线[收到一条 webhook 回调时，怎样确认它真实、未被重放，并可靠地受理](#42.%20%E6%94%B6%E5%88%B0%E4%B8%80%E6%9D%A1%20webhook%20%E5%9B%9E%E8%B0%83%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E7%A1%AE%E8%AE%A4%E5%AE%83%E7%9C%9F%E5%AE%9E%E3%80%81%E6%9C%AA%E8%A2%AB%E9%87%8D%E6%94%BE%EF%BC%8C%E5%B9%B6%E5%8F%AF%E9%9D%A0%E5%9C%B0%E5%8F%97%E7%90%86%EF%BC%9F)。

> [!info]- 来源
> - `202 Accepted` 表示已接受处理但未完成、不承诺最终成功；`201 Created` 表示资源已创建并可用 `Location` 指向它：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§15.3.3、§15.3.2，2022-06，核对于 2026-11-12。“job、outbox 与等待槽同事务提交后才回 202”是本例比 HTTP 通用语义更强的应用合同。
> - 数据库提交与消息发布的双写缺口、重复消息与消费者幂等：[AWS Prescriptive Guidance, Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)，核对于 2026-11-12。
> - 唯一约束、并发插入与 `ON CONFLICT` 的行为：[PostgreSQL 18, Index Uniqueness Checks](https://www.postgresql.org/docs/18/index-unique-checks.html)、[INSERT](https://www.postgresql.org/docs/18/sql-insert.html)，核对于 2026-11-12；数据库侧的完整论证在主线三。
> - 请求内流式响应与持久 job 的生命周期对照，依据 FastAPI 对 `StreamingResponse` 与 request scope 依赖的实测（FastAPI 0.128.0、Starlette 0.47.2，2026-11-12）；细节在 runtime 主线。
## 42. 收到一条 webhook 回调时，怎样确认它真实、未被重放，并可靠地受理？

上一章的状态机约定：`job-demo-731` 成功时，同一事务还会写一条 `report.ready` outbox (事务发件箱) 意图（这笔成功提交怎样写，见[领取与栅栏一章](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)）。本支线跟着这条意图走出服务：发送服务用一个 HTTP 回调（webhook）把“报表 42 已完成”通知给另一个服务，即接收方。接收方可能暂时不可用，也可能已经把事件写进数据库，返回的响应却在网络中丢失，所以发送方无法只凭一次 HTTP 往返判断对方是否收下。本章站在接收方回答：怎样确认请求真实、没有被重放、在有效期内，并在什么条件下回应“已受理”；也说明发送方怎样重试、怎样轮换共享密钥。

接收方处理每个请求，都按同一个顺序检查，前一步不通过就不做后一步。下图是整条判定路径，编号就是检查顺序：格式、认证、授权、期限、去重、受理；最后一步持久写入收件记录（`inbox`）和处理意图，提交成功后才回应 202。图里的截止点 D、去重用的墓碑等在后文逐节定义，初读先看主干的顺序和各出口的状态码。

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 300}}}%%
flowchart TD
    R[收到 POST /hooks/reports] --> G1["① 格式<br/>头唯一、大小、无内容编码、Content-Type"]
    G1 -->|不通过| X1["400：头重复或错误、正文过大、带内容编码<br/>415：Content-Type 缺失或不支持<br/>都不写 inbox"]
    G1 -->|通过| G2["② 认证<br/>(endpointId, keyId) 查到可用键<br/>HMAC 相符、签名时间在 ±300 s 内"]
    G2 -->|"通过，信任注册记录的 sourceId"| G3["③ 严格解析 JSON 与业务授权<br/>来源、事件类型、reportId 42"]
    G2 -->|任一项失败| X401["401，统一正文<br/>不透露原因，不写 inbox"]
    G3 -->|不通过| X3["400：重复成员名或语法无效<br/>403：来源无权<br/>都不写 inbox"]
    G3 -->|通过| G4["④ 期限<br/>签名时间 &lt; D = createdAt + 30 天"]
    G4 -->|通过| G5["⑤ 去重<br/>INSERT … ON CONFLICT DO NOTHING<br/>返回一行吗？"]
    G4 -->|达到或超过 D| X410["410<br/>不写 inbox"]
    G5 -->|否：读胜者摘要| G6["已提交的行"]
    G5 -->|是：同事务插入处理 outbox| G7["⑥ 受理：COMMIT 结果"]
    G6 -->|摘要相同| D202["202 重复受理<br/>不新增处理意图"]
    G6 -->|摘要不同| D409["409<br/>写隔离记录并告警"]
    G6 -->|查不到墓碑| D503["503 并告警<br/>不重跑插入；fail-closed 门闩<br/>关闭该端点/来源的首次受理"]
    G7 -->|确认成功| A202["202 首次受理<br/>两行已持久化"]
    G7 -->|明确未提交| A503["503<br/>两行都不存在"]
    G7 -->|结果未知| A503u["503 或无响应<br/>不宣称回滚"]
    D202 ~~~ D409 ~~~ D503
    A202 ~~~ A503 ~~~ A503u

    classDef reject fill:#fff0ed,stroke:#a54838
    classDef ok fill:#e7f6ec,stroke:#34734a
    classDef warn fill:#fff6df,stroke:#9a6a12
    class X1,X401,X3,X410 reject
    class D202,A202 ok
    class D409,D503,A503,A503u warn
```

> [!info] 本例约定与通用原则
> 本章定义一个只供教学的合成 HMAC 协议，不兼容 Stripe、GitHub 或任何 webhook 提供方。下面这些都是**本例约定**：请求头名称与签名输入格式、±300 秒的签名新鲜度窗口、`createdAt + 30 天`的投递期限、各验证结果对应的状态码、发送方最多 12 次自动发送和 15 分钟退避上限。所有域名、密钥和业务数据都是合成的。通用的原则是：验签与去重分开、先认证再查收件记录、持久提交后才确认受理、去重记录要比最后一份合法请求活得久、密钥轮换先兼容后切换。

### 验签和去重回答的是不同问题

- **签名验证**回答：请求是否来自持有共享密钥的一方，签名覆盖的字节有没有被改过。
- **持久去重**回答：这个逻辑事件是否已经受理过。

两者不能互相代替：一份有效的请求被原样重放，签名照样通过；事件 ID 谁都能写，单独证明不了发送方的身份。

整条路径分三段，每段都需要稳定的标识、持久状态和处理重复的规则：

- **发送**：发送方在业务事务里写一条待投递事件（发送端 outbox），由 relay (中继) 发出请求；
- **受理**：接收方完整验证后，在同一个数据库事务里写入 `inbox` (收件箱) 行和处理用的 outbox 行，确认提交成功才返回 202；
- **处理**：已提交的处理意图由接收方的 worker 领取，不必等 HTTP 响应发出。它怎样被领取和确认，与前面几章相同（见[发布确认、消费者确认和业务完成各证明什么](#44.%20%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)）。

### 一次通知怎样从发送端出发？

报表成功的事务写了一条发送端 outbox 行，里面有稳定的 `eventId`、事件类型、不可变的 UTF-8 正文字节和待投递状态；只有业务事务提交后，relay 才能发送它。

两种 ID 的分工：

- `eventId` 表示一次**逻辑事件**，所有重试保持不变；
- 每次新的**应用层**投递生成新的 `attemptId`、新的签名时间和新的签名；网络层重传同一个 HTTP 请求时，这组请求头原样保留。

正文是一行 JSON（代码块围栏不属于正文，结尾没有换行），恰好 108 个字节：

~~~json
{"eventId":"evt-report-42-ready-001","type":"report.ready","reportId":42,"createdAt":"2026-11-09T04:00:00Z"}
~~~

第一次应用层发送（签名时间 1794196800 即 `2026-11-09T04:00:00Z`）：

~~~http
POST /hooks/reports HTTP/1.1
Host: receiver.example.test
Content-Type: application/json
X-Webhook-Key-Id: demo-k2026-02
X-Webhook-Timestamp: 1794196800
X-Webhook-Event-Id: evt-report-42-ready-001
X-Webhook-Attempt-Id: att-001
X-Webhook-Signature: v1=00ddffad798719283b3f470bfdae27dafb1e4a9b3710cdc118e75a1657c29b6f
Content-Length: 108

{"eventId":"evt-report-42-ready-001","type":"report.ready","reportId":42,"createdAt":"2026-11-09T04:00:00Z"}
~~~

假设接收方已经提交了 `inbox` 和处理 outbox，但 202 响应丢了。发送方 10 分 1 秒后重新投递。`eventId` 和 108 个正文字节完全不变；这是一次新的应用层尝试，所以签名时间、`attemptId` 和签名都变了：

~~~http
POST /hooks/reports HTTP/1.1
Host: receiver.example.test
Content-Type: application/json
X-Webhook-Key-Id: demo-k2026-02
X-Webhook-Timestamp: 1794197401
X-Webhook-Event-Id: evt-report-42-ready-001
X-Webhook-Attempt-Id: att-002
X-Webhook-Signature: v1=f03542e0a28e53585db5107e10147457ae5cd8a71596dffd5dda16d06ccc650c
Content-Length: 108

{"eventId":"evt-report-42-ready-001","type":"report.ready","reportId":42,"createdAt":"2026-11-09T04:00:00Z"}
~~~

为什么不直接重发第一次的请求？接收方只接受签名时间与自己时钟相差 ±300 秒以内的请求。在 `2026-11-09T04:10:01Z` 重发 `att-001`，它的签名时间已过去 601 秒，会被以 401 拒绝。`att-002` 用当前时间重新签名，时间差为 0。正文里的 `createdAt` 也早了 601 秒，但它不参与新鲜度检查。如果第一次已经提交，`att-002` 会命中“同一事件、同一正文摘要”的重复受理；如果第一次没提交，`att-002` 就成为首次受理。

### 签名覆盖哪些字节，密钥管到哪里？

本例把要认证的字段和字节定义为：

~~~text
signingInput = UTF8("v1" + LF + keyId + LF + decimalTimestamp + LF + eventId + LF + attemptId + LF) || rawBody
signature    = lowercase_hex(HMAC-SHA-256(secret[keyId], signingInput))
~~~

所有文本字段都是 ASCII，字段之间是单个 LF 字节（0x0A），末尾一个 LF 后直接接原始正文。ID 只接受 1–128 个 `[A-Za-z0-9._-]` 字符；时间戳只接受没有前导零的十进制 Unix 秒。上面两个示例签名用演示密钥 `synthetic-demo-secret-never-use-outside-example` 算出，它不能用作真实凭据。

![签名输入由本次尝试的字段和原始正文组成；Content-Length 不参与 HMAC](../../engineering-foundations/services/resources/webhook-signature-input.svg)

HMAC (基于哈希的消息认证码) 用共享密钥证明完整性和“持钥者”身份。它不加密正文，也不提供不可否认性：任何一方持有密钥，都能算出有效签名。

**密钥的作用域。** 签名输入不含 HTTP 方法、Host 或路径，所以本例的密钥只能用于固定的 `POST /hooks/reports` 端点。下文用 `endpointId` 表示接收方由路由确定的端点，用 `sourceId` 表示注册表中登记的发送来源。一把密钥的授权作用域是 `(endpointId, sourceId)`：不同端点、不同来源或不同账户授权域，必须使用不同的密钥值。也可以在版本化的签名输入里加入受保护的目标字段，把签名额外绑定到请求目标，但这代替不了按来源和账户隔离密钥与业务权限。HTTPS 保护的是传输通道，同样代替不了事件级的验签、去重和业务授权。

### 先保留原始字节，确定请求格式

接收边界在做任何 JSON 解析之前，先保留应用实际收到的正文字节，并设好请求头与正文的大小上限。签名覆盖的是 HTTP 定界之后的正文内容，不是网络包，也不是 `Content-Length` 的文本。由此有几条格式规则：

- **拒绝任何 `Content-Encoding`，而且要在代理或框架自动解压之前拒绝。** 不能改成“在压缩后的字节上验签”来接受编码请求。
- **网关和应用都不得规范化或重新序列化正文。**
- 本端点要求 `Content-Type: application/json`。
- **每个 `X-Webhook-*` 头在入口只能出现一次。** HTTP 允许接收方把同名字段行用逗号合并成一个值，所以应用看到“一个值”并不能证明原请求只有一行。入口要在合并之前拒绝重复，或可靠地拒绝合并后的值；重复、空值、语法错误或不支持的签名版本一律 400，避免不同代理和应用对同一请求解析出不同结果。
- 签名值必须是 64 个小写十六进制字符，解码成 32 字节后，用 constant-time comparison (常数时间比较) 与计算结果比较，避免比较耗时泄露前缀信息。

### 先认证来源，再查收件记录

接收方先由固定路由确定 `endpointId`。这时来源还没有经过验证，所以密钥注册表必须**只凭 `(endpointId, keyId)` 就唯一查到一条记录**（例如唯一约束 `UNIQUE(endpoint_id, key_id)`），不能指望验签之后再用来源去区分。请求里的 `keyId` 尚不可信，只用作查找键。

只有当前可用的密钥才参与计算；未知、未生效、已撤销的键统一返回 401。接收方用收到的受保护字段和原始正文重算 HMAC，常数时间比较，并检查签名时间落在自己时钟的 ±300 秒内。**这些全部通过之后**，才信任所选注册记录里的 `sourceId`；不能从未经验证的请求头或正文里直接取来源。轮换时新旧 `keyId` 都映射到同一个稳定的 `sourceId`。撤销以接收方当前生效的注册表为准：签名时间即使早于撤销时间，撤销之后也不再接受。

认证失败必须在查询 `inbox` **之前**就拒绝。否则攻击者可以拿猜来的 `eventId` 探测某个事件是否存在。

### 再做业务授权，检查载荷与投递期限

认证通过后才解析 JSON 并做业务授权。本例只接受指定 `sourceId` 发来的 `report.ready`，且只允许通知 `reportId` 42；请求头和正文里的 `eventId` 必须相同；字段类型、必需字段、UTC 格式的 `createdAt` 都要通过。来源身份有效、但类型或资源未获授权的事件返回 403，不写 `inbox`。

**严格 JSON。** 解析器要拒绝重复的成员名并返回 400。HMAC 保证收到的字节没被改动，却不保证不同的 JSON 解析器对两个 `reportId` 取同一个值。接收端和之后的处理 worker 必须共享同一条严格解析规则，worker 不能用更宽松的解析器从原始正文得出不同的授权对象。签名格式版本 `v1` 也不是载荷的结构版本。

**固定投递期限。** ±300 秒只限制单次尝试的新鲜度，挡不住发送方无限期地用新签名重试同一个事件。所以本例再给每个事件一个固定期限：`createdAt` 在发送端 outbox 首次提交时写定，此后整份正文不变；任何新尝试的签名时间都必须**严格早于** `createdAt + 30 天`。示例的 `createdAt` 是 `2026-11-09T04:00:00Z`，记固定截止点为 D = `2026-12-09T04:00:00Z`，签名时间恰好等于 D 也算过期。认证、新鲜度、载荷和业务授权都通过后，若签名时间达到或超过 D，返回 410，不写 `inbox`。截止前一秒签发的请求，同样要在 ±300 秒内到达。

### 每种验证结果怎样回应？

开头的判定图给出了每个结果的状态码。它们留下的持久状态不同：

- **拒绝出口**（400、415、401、403、410）都不写 `inbox`。安全日志只记失败类别；401 不透露具体原因。
- **两种 202** 都以已提交的行为准：重复受理只对照已有行，不新增处理意图；首次受理时 `inbox` 与处理意图都已持久化，worker 可能早于响应就开始。
- **409** 写受限的冲突审计或隔离记录，并告警。
- **三种 503** 含义不同。冲突后查不到墓碑：不重跑首次插入，关闭该端点/来源的首次受理，直到恢复或对账。数据库明确确认未提交：两行都不存在，发送方按原事件重试。`COMMIT` 结果未知：可能已提交，也可能没有，不宣称回滚。

401 要带适用于目标资源的 `WWW-Authenticate` challenge。这里的 `Webhook-HMAC` 是本例私有的认证方案：HTTP 只提供 challenge/response 的框架，并没有定义它；凭据放在自定义的 `X-Webhook-*` 头里，challenge 也不会让它们变成标准的 HTTP 认证凭据。公开互操作的实现要发布完整的方案规范，并按 RFC 9110 的认证方案注册程序处理。因为 HTTP 的缓存规则认不出这些自定义凭据头，本端点对所有响应都设 `Cache-Control: no-store`。认证失败的正文统一，不透露 `keyId` 是否存在或比较细节：

~~~http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Webhook-HMAC realm="report-webhooks"
Cache-Control: no-store
Content-Type: application/problem+json

{"type":"https://receiver.example.test/problems/invalid-webhook-authentication","title":"Webhook authentication failed","status":401}
~~~

错误正文使用 Problem Details 格式（`application/problem+json`）：`type` 用稳定、不含敏感数据的 URI，堆栈、密钥查找细节、用户数据和可被枚举的攻击线索都不进入响应。这种机器可判定的错误契约的完整讲解见[怎样让调用方可靠地判断 API 的成功、失败和变化](#37.%20%E6%80%8E%E6%A0%B7%E8%AE%A9%E8%B0%83%E7%94%A8%E6%96%B9%E5%8F%AF%E9%9D%A0%E5%9C%B0%E5%88%A4%E6%96%AD%20API%20%E7%9A%84%E6%88%90%E5%8A%9F%E3%80%81%E5%A4%B1%E8%B4%A5%E5%92%8C%E5%8F%98%E5%8C%96%EF%BC%9F)。

### 为什么验签之后，还要持久去重再应答？

验签只证明请求可信、字节匹配，不证明这个逻辑事件之前没被受理过。本例的表结构：

- `inbox` 以 `(sourceId, eventId)` 为唯一键，保存正文 SHA-256、原始正文、接收时间和处理状态；
- 处理用的 outbox 行通过外键引用 `inbox` 行，并用同一个 `(sourceId, eventId)` 唯一约束限制每个事件最多一条处理意图。

首次受理必须在**同一个数据库事务**里插入这两行；只有应用收到提交成功的结果，才返回首次受理的 202。提交后的处理意图可以独立于 HTTP 响应被 worker 领取。这里的 202 只表示接收方接受了待处理的工作，不表示 worker 已运行或远端副作用已完成，和[持久受理一章](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)的 202 是同一种承诺。

![接收方完整验证并授权后，由唯一键决定首次提交或重复分支；inbox 与处理 outbox 提交后 worker 可以领取；应用观察到提交成功后才返回首次 202](../../engineering-foundations/services/resources/webhook-acceptance-boundary.svg)

正文若不直接存在数据库里，而是存不可变对象存储的引用，就必须先确认对象已完整写成、可以读到，再提交引用；否则 worker 无法恢复输入，不能返回 202。对象先写、数据库后提交可能留下孤儿对象，按不再被引用且过了宽限期再清理（规则同[孤儿对象的清理条件](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)）。数据库不可写或对象不可读时返回 503。

处理结束后，可以按数据保留政策删掉正文，但去重墓碑及其 `dedupe_until` 必须保留到下一节算出的时刻。正文可能含个人或业务数据，要限制访问和保留期，日志不写正文。

### 去重墓碑要比最后一份合法请求活多久？

墓碑保存的是“这个事件已经受理过”的证据。它必须活到**最后一份仍可能通过验签的请求完成数据库裁决之后**；否则一份迟到的重复请求会因为旧行已删而被当成新事件。这是[去重要覆盖所有在途和晚到请求](#%E5%8E%BB%E9%87%8D%E8%A6%81%E8%A6%86%E7%9B%96%E5%A4%9A%E9%95%BF%E6%97%B6%E9%97%B4%EF%BC%9F)这条原则在 webhook 上的具体推导。

下图沿时间轴推导这个时刻。能进入数据库受理的请求，签名时间早于固定截止点 D（`createdAt + 30 天`），所以验签时实例的时钟早于 D + 300 秒。之后还要依次加上三个上界：

- **B**：从最后一次通过 ±300 秒检查，到数据库完成提交或确认中止的最长耗时，包括解析、授权、排队、连接池、锁等待和全部事务语句；
- **S**：清理所用的数据库时钟最多比验签实例快多少，由本合同固定；
- **G**：清理调度与存储的安全余量。

![从 createdAt 起 30 天到 D，再依次加 300 s、B、S、G 得到 dedupe_until；本例 B = 20 s、S = G = 5 s，墓碑最早在 2026-12-09T04:05:30Z 才允许清理](../../engineering-foundations/services/resources/webhook-tombstone-retention.svg)

所以把

~~~text
dedupe_until ≥ D + 300 s + B + S + G
~~~

随墓碑一起持久保存。清理进程使用数据库时钟，只清理已到期、且处理 outbox 已经终结的记录。图中的 B、S、G 取值只演示推导，部署前要证明自己的实际上界。

几条让这个公式成立的前提：

- **B 不是 HTTP 响应超时。** 应用返回或断开之后，已发出的数据库命令仍可能执行并提交。要用一个从新鲜度检查开始计时的预算覆盖所有在途阶段，并让数据库端也能强制结束超时的事务。
- **上调 B 之前，先延长所有尚未清理的墓碑。**
- **S 不能在旧墓碑删除之后放宽。** 一个更落后的验签实例可能重新接受已被其他实例判为过期的旧签名。持续监控各实例相对数据库时钟的偏差与时间回退；偏差超出 S，或回退可能重新打开已过期的窗口时，暂停该实例的受理，直到时钟回到界内并稳定。无法监测并强制 S 或 B，就不能按这个期限删除墓碑。
- **发送方必须遵守事件不可变的约定。** 重试和人工重放保持原正文与 `eventId`，不能靠改写 `createdAt` 重置期限。墓碑一旦删除，接收方无法单凭 HMAC 复原旧正文。
- 较旧但仍合法的签名也可能**首次**到达。是否重复，只看有效保留期内的已提交唯一行，不能凭时间戳或尝试日志就返回 202。

> [!info] 实例：PostgreSQL 的服务端超时（核对于 2026-11-12）
> `statement_timeout` 限制单条语句，`lock_timeout` 对每次锁等待分别计时；`transaction_timeout` 从 PostgreSQL 17 起提供，限制普通事务的时长（不覆盖 prepared transaction）。16 及更早的版本没有这个参数，要另配等效的服务端事务上限，才能强制 B。

### 两个首次投递同时到达，怎样裁决？

并发首次投递的裁决靠数据库唯一约束。首次插入时同时写入算好的 `dedupe_until`。在 Read Committed 事务里，先做一条不会抛异常的插入：

~~~sql
BEGIN ISOLATION LEVEL READ COMMITTED;

INSERT INTO webhook_inbox
  (source_id, event_id, body_sha256, raw_body, status, received_at, dedupe_until)
VALUES
  (:source_id, :event_id, :body_sha256, :raw_body, 'accepted', clock_timestamp(), :dedupe_until)
ON CONFLICT (source_id, event_id) DO NOTHING
RETURNING source_id, event_id;
~~~

按 `RETURNING` 是否返回一行分支：

- **返回一行**：本事务插入了 `inbox`。同一事务再插入处理 outbox，然后提交；只有 `COMMIT` 成功才回 202。outbox 插入失败就回滚整笔受理，返回 503，让发送方用同一 `eventId` 和同一正文重试。
- **没有返回行**：唯一键已被另一个事务占用。用**下一条语句**读胜者并核对摘要：

~~~sql
SELECT body_sha256
FROM webhook_inbox
WHERE source_id = :source_id
  AND event_id = :event_id;
~~~

Read Committed 下每条语句取新快照；如果先前的插入等过并发事务，这条 SELECT 能看到已提交的胜者。摘要相同，返回重复受理的 202，不创建第二条处理意图；摘要不同，把冲突写进受限的隔离记录、提交审计后返回 409。

不要用普通 `INSERT` 撞唯一约束、捕获异常后在同一事务里继续 SELECT：PostgreSQL 报错后当前事务已失败，后续查询要等回滚（数据库侧的规则见[两个请求争夺最后一件库存时怎样只预留一次](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)）。

**冲突后却查不到墓碑。** 在有效期内发生唯一冲突，下一条 SELECT 必然能找到墓碑，因为保留合同保证清理不会在窗口内删掉它。如果仍然无行，说明保留、时钟或清理的不变量被破坏了，这不是可以正常重试的冲突：回滚，返回 503 并告警，不能重跑 INSERT，否则已受理的 ID 可能被当成新事件。立即把这个端点/来源的首次受理切到所有接收实例共享的 fail-closed 门闩，恢复墓碑或完成核对后才解除；不能确认门闩已覆盖所有实例时，暂停整个端点的受理。

在 Repeatable Read 或 Serializable 下遇到明确的序列化失败，是另一条分支：回滚并重试整个事务，不要和“冲突后读不到墓碑”混为一谈。

这个模式让并发的首次请求只有一个事务能创建处理意图：先行者提交，后行者读到摘要；先行者回滚，等待中的请求就可以成为首次写入者。时间窗口本身不是去重，签名也说明不了 `inbox` 是否已提交。

### 提交结果未知时怎样回应？

只有收到数据库“提交成功”的结果，才能返回首次受理的 202。两种 503 要分清：

- 数据库**明确**确认受理事务没提交（例如正文存储失败后回滚、`COMMIT` 前就失败）：503 表示两行都不存在。
- `COMMIT` 已经发出，但连接断了或提交回复没到：持久状态**未知**，不能写成“一定没提交”。不发 202；连接还能应答时可回 503 表示结果未知，否则发送方看到的也是未知。数据库可能已提交两行、worker 可能已开始，也可能两行都不存在。发送方保留同一个 `eventId` 和原始正文重试，由唯一键判定状态，而不是生成新事件。

数据库客户端把“命令已发送”和“取回命令结果”分成两步，客户端没读到结果，不能证明服务端没执行提交。事务层面的处置规则见[事务能保证什么](#24.%20%E4%BA%8B%E5%8A%A1%E8%83%BD%E4%BF%9D%E8%AF%81%E4%BB%80%E4%B9%88%EF%BC%8C%E5%B9%B6%E5%8F%91%E4%BA%8B%E5%8A%A1%E5%90%84%E8%83%BD%E7%9C%8B%E8%A7%81%E4%BB%80%E4%B9%88%EF%BC%9F)。

| 崩溃或不确定的时点 | 持久事实 | 接收方之后的行为 |
| --- | --- | --- |
| 受理事务提交之前 | 两行都不存在，不能回 202 | 合法重试重新走验签、授权和首次受理 |
| 提交之后、202 送达之前 | 正文、摘要和处理意图都已提交；worker 可以独立开始 | 重试仍先完整验证；同事件同摘要只回 202，不再排队 |
| 已发 `COMMIT`，但没看到结果 | 两行可能都在，也可能都不在 | 不宣称回滚、不回首次 202；发送方按原 `eventId` 与正文重试，由唯一键查明 |
| 202 已送达，worker 还没完成 | 收件内容和处理意图都可恢复 | worker 从持久输入继续；发送方不必等业务终态才停止重试 |
| 外部效果可能已完成，本地完成记录未提交 | 结果未知 | 按原操作键查询或对账，不换新键猜测重试（见下一节） |

### 顺序与外部副作用

**本协议不保证事件顺序。** 如果业务要求按账户或资源有序，载荷还要定义受保护的资源序号；接收方按序号做条件更新或串行处理，不能把 HTTP 到达的先后当成业务顺序。

**worker 调用外部系统时，`inbox` 去重管不到下游。** 请求超时后，远端可能已经完成，本地却没收到确认。先按稳定的操作键查询，再按[远端副作用的决策表](#%E8%BF%9C%E7%AB%AF%E5%89%AF%E4%BD%9C%E7%94%A8%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%8F%AF%E4%BB%A5%E9%87%8D%E5%8F%91%EF%BC%9F)决定：确认完成就记录并停止；远端对同键同摘要的去重保证仍有效，才用原键重试；否则保持未知、人工对账。

这里有两个互相独立的期限：webhook 的 30 天投递期限不会延长远端操作键的去重期；远端的保证先过期，即使 webhook 仍在 30 天内，也不能再盲目重试副作用。反过来，接收方的 `inbox` 墓碑也不能保证远端的业务效果不重复。

### 发送端怎样重试、停止和人工重放？

发送方必须把业务变更和待发送事件放在同一个事务里，否则业务已提交、进程却在写 outbox 前崩溃时，通知就永久丢了。relay 只读已提交的 outbox 再发请求；收到 2xx 才把逻辑事件标为已受理。连接超时、断开、响应丢失都是结果未知，不代表接收方没提交：继续用原 `eventId` 和原正文重试，由接收方的唯一键区分首次与重复。

每次新的应用层尝试，先持久记下 `attemptId`、`keyId`、签名时间、事件 ID 和待发状态，再发请求。进程在发送前后崩溃时，恢复只把已持久确认的 2xx 视为已受理；不能证明请求没发出的，就视为未知，用同一逻辑事件安全重试或对账。保存 `keyId` 和尝试记录，也让撤销某把密钥之后能找到受影响的未确认事件。

本例的发送策略（合成，不是 HTTP 或 webhook 的统一标准）：

| 响应或结果 | 策略 |
| --- | --- |
| 任意 2xx | 视为已受理，结束这个逻辑事件的发送；本例接收方返回 202 |
| 408、429、5xx，或连接结果未知 | 在期限前有限重试；429/503 若带 `Retry-After`，按提示等待，但仍检查期限 |
| 其他 4xx | 停止自动重试，保留原因，进入待处理状态 |
| 3xx 或未定义的响应 | 不自动跟随、不猜含义；进入待处理状态，先修复目标或契约 |

退避从约 1 秒开始指数增长，封顶 15 分钟，加随机抖动（公式与道理见[重试要等多久、最多试几次](#%E9%87%8D%E8%AF%95%E8%A6%81%E7%AD%89%E5%A4%9A%E4%B9%85%E3%80%81%E6%9C%80%E5%A4%9A%E8%AF%95%E5%87%A0%E6%AC%A1%EF%BC%9F)）。最多**自动发送** 12 次，含首次，不是 12 次额外重试。每次发送前检查当前时间：新签名时间必须严格早于 `createdAt + 30 天`；到期或达到次数上限就停下告警。`Retry-After` 指向的时刻若在截止点或之后，不能越过期限继续投递。

达到上限后，持久保存原事件、每次尝试和最终原因，等待人工处理。操作员只能在**同一个绝对期限前**重放：正文和 `eventId` 不变，`attemptId` 变，用当前有效的密钥重新签名。若旧尝试其实已受理而响应丢了，接收方返回重复 202，不会新建处理意图；若从未提交过 `inbox`，这次可以成为首次受理。新的业务动作要生成新的 `eventId`，并用 `causationId` (因果事件 ID) 关联原事件，而不是改写旧 ID 绕过去重。

### 密钥怎样轮换，泄漏时怎样撤销？

注册表里每条密钥记录包含：稳定的 `sourceId`、密钥值、可用状态、生效和撤销时间。`keyId` 在同一端点内是唯一的查找键（因为查找发生在来源被验证之前），它本身也被签名覆盖。轮换时，新旧 `keyId` 映射到同一个 `(endpointId, sourceId)`，这样 `(sourceId, eventId)` 的去重在密钥换代之后仍然连续。密钥值只放在受控的 secrets manager 或等价的安全存储里，不进代码仓库、明文配置或日志。

#### 正常轮换：接收方先兼容，发送方再切换，接收方最后移除

1. **接收方先兼容。** 生成新的 `keyId` 和密钥，把接收方的验证映射更新为同时含旧、新两项，部署到**所有**可能接收请求的实例。若密钥是在进程启动时注入的，改密钥库不会改变正在运行的进程，必须替换接收方进程，并确认旧进程已退出（平台侧的做法见[服务该跑在哪种运行时上](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)）。
2. **发送方切换。** 所有发送实例改用新键，同样替换进程；新的尝试用新密钥对相同 `eventId` 和原始正文重新签名。等所有旧发送进程都退出之后，从持久的尝试记录里取出所有旧键签名时间的最大值 `Tmax`。
3. **等旧签名在每个接收实例上都过期。** 判定用接收实例**自己的时钟**：只有每个仍可能接收请求的实例，其时钟都已严格晚于 `Tmax + 300 秒`，并且所有已通过新鲜度检查的在途验证都已结束，旧键才不会再被接受。用接收方自己的时钟判断时，不要再额外加一次时钟偏差。若改由一个可信的协调器时钟统一判断，就要在 `Tmax + 300 秒`上再加已测得的最大接收方时钟落后量，并同样等在途验证结束。不能只从部署新发送方的时刻起等 300 秒，因为旧实例之后可能仍发出过旧签名。
4. **接收方移除旧键。** 把映射改为只含新键，替换接收方进程；确认旧进程全部退出后，旧密钥才不再驻留在内存里。旧密钥的存档版本按保留策略清理。

本例的发送端 outbox 保存的是**未签名**的正文，每次尝试才签名，所以积压的事件可以直接用新键签名，不需要为了它们延长旧键。如果实现里预先排队的是**已签名**的请求，就要在旧签名失效前重新签名，或者等这些旧签名全部失效、在途排空之后再移除旧键。

#### 紧急撤销：怀疑密钥泄漏

不保留新旧双接受的窗口，也不等正常排空：

1. 预先生成新键；暂停这个来源的事件投递，并阻断旧接收进程的入口或直接停掉它们。
2. 部署只含新键的接收方；再原子地把发送方切到新键（`keyId` 和密钥必须同时更新），替换旧发送进程，确认旧进程已退出，再恢复投递。撤销真正生效的边界是**所有**可能接收请求的实例都已拒绝旧 `keyId`；在此之前仍可能有实例接受它。
3. 还没有可用的新键时，先撤销旧键并保持暂停；不能为了可用性继续信任泄漏的密钥。
4. 按被撤销的 `keyId` 找出所有未确认的事件，只在原 `createdAt + 30 天`之前，用原 `eventId`、原正文和新的 `attemptId` 重新签名投递。换键不重置绝对期限。此前若已受理、只是响应丢了，持久的 `inbox` 会识别为重复；已确认 2xx 的事件不需重放。

撤销不会删除 `inbox` 或 outbox，不延长期限，也撤不回已经发生的外部副作用。删除密钥库里的值，也清除不了进程里已经注入的副本，仍然必须替换进程。

> [!info] 实例：ECS 注入 Secrets Manager 密钥时的两个细节（核对于 2026-11-12）
> ECS 在 task 启动时把 Secret 注入环境变量；移动 `AWSCURRENT` 标签不会更新正在运行的 task，必须强制新部署；若 task definition 固定了 VersionId，先发布引用新版本的 revision 再替换 task。`keyId` 和密钥应放在**同一个** JSON Secret 值里（例如发送端的 `{"keyId":"…","key":"…"}`，接收端的整张 keyId→密钥映射），由应用从同一份值解析：若分成两个值分别注入，两次读取之间 `AWSCURRENT` 可能恰好移动，得到新密钥配旧 `keyId`。task execution role、task role 与注入审计的分工见[服务该跑在哪种运行时上](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)。

### 怎样观察交接有没有卡住？

**记录什么。** 发送端把 `eventId` 与每个 `attemptId`、`keyId`、端点、发送时间、状态码或传输结果、下次尝试时间和事件年龄关联起来。接收端记录 `eventId`、`attemptId`、`keyId`、签名时间偏移、验签失败类别、业务授权类别、首次受理还是重复命中、正文摘要冲突，以及从 `inbox` 到业务终态的时延。

**不记录什么。** 日志不写密钥、完整签名头、`Authorization` 或其他凭据头、原始正文。正文摘要也可能成为敏感数据的稳定指纹，要同样控制访问，不能拿它代替公开日志里的事件 ID。

**按边界读信号：**

- 认证失败或签名时间偏移升高：请求还没进入受理。
- 认证通过后的 503：区分“数据库明确未提交”的持久化或对象故障，和“`COMMIT` 结果未知”；后者不能据此判断数据没写入。
- 冲突后找不到墓碑：保留完整性告警，暂停自动首次受理。
- 已受理 `inbox` 的数量或最老年龄持续增长：异步处理积压。
- 外部结果长期停在未知：需要业务对账。
- 发送端的事件年龄、自动尝试次数、待处理量和即将到期量：帮助在 30 天期限前处理积压。

一个事件应能从稳定的 `eventId` 追到每次尝试、接收方受理和最终业务状态。不要把“发出过请求”“收到 202”“副作用已完成”合成一个成功指标。

### 本支线产出

接收方现在有一条完整的受理边界：按格式、认证、授权、期限、去重、受理的顺序检查；首次受理与处理意图同事务提交才回 202；墓碑保留到 `D + 300 s + B + S + G` 之后；`COMMIT` 结果未知不宣称回滚；密钥按“先兼容、再切换、后移除”轮换，泄漏时暂停并立即撤销。处理意图提交之后，接收方 worker 的领取、确认与重试回到主线：[怎样保证一个任务同一时刻只由一个 worker 推进](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)。

> [!info]- 来源
> - HMAC 的定义、共享密钥模型与安全说明：[IETF RFC 2104](https://www.rfc-editor.org/rfc/rfc2104.html)，§1–§3，1997-02；`HMAC-SHA-256` 与测试向量：[IETF RFC 4231](https://www.rfc-editor.org/rfc/rfc4231.html)，§2–§4，2005-12。两个示例签名已按文中字节定义用 Python 标准库 `hmac`/`hashlib` 复算，正文长度复核为 108 字节。
> - JSON 对象成员名应唯一：[IETF RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html)，§4，2017-12；“拒绝重复成员名”是本例合同的进一步选择。
> - HTTP 字段重复与合并、内容编码、401 challenge、状态码、`Retry-After` 与认证方案注册：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§5.2–§5.3、§8.4、§11.1–§11.6、§15.3.3、§15.5、§15.6.4、§16.4.1，2022-06。私有 HMAC 协议不由 RFC 定义。
> - `no-store`：[IETF RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2.5)，§5.2.2.5；429 与 `Retry-After`：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，§4；问题详情类型与错误信息的安全边界：[IETF RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html)，§3、§5，2023-07。
> - 并发 `inbox` 冲突与新快照查询：[PostgreSQL 18, INSERT](https://www.postgresql.org/docs/18/sql-insert.html)（`ON CONFLICT ... DO NOTHING ... RETURNING`）、[Transaction Isolation §13.2.1](https://www.postgresql.org/docs/18/transaction-iso.html)；服务端超时参数：[PostgreSQL 18 Client Connection Defaults](https://www.postgresql.org/docs/18/runtime-config-client.html)，并对照 [17](https://www.postgresql.org/docs/17/runtime-config-client.html) 已有、[16](https://www.postgresql.org/docs/16/runtime-config-client.html) 尚无 `transaction_timeout`；核对于 2026-11-12，冲突模式另在 PostgreSQL 14 本地复放。
> - 命令发送与取回结果是两个客户端步骤：[PostgreSQL 18, libpq Asynchronous Command Processing §32.4](https://www.postgresql.org/docs/18/libpq-async.html)。
> - ECS 的 Secret 注入、版本引用与强制新部署：[Secrets Manager environment injection](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html)、[task execution role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)，核对于 2026-11-12。
> - 轮换的等待条件（以每个接收方自己的时钟判断 `Tmax + 300 s`，或协调器时钟另加最大落后量）、墓碑保留推导、发送策略中的 12 次与 15 分钟、30 天期限，都是本合成协议的合同与推导，不是任何提供方的默认值。
## 43. 怎样保证一个任务同一时刻只由一个 worker 推进？

上一章结束时，数据库里有一个 `queued` 的 `job-demo-731`，relay (中继) 已经（可能不止一次）把只带 job ID 的消息发给 broker (消息代理)。本章回答：多个 worker 都收到唤醒时，谁能执行；一个停顿很久又醒来的旧 worker，怎样被挡在外面；结果怎样提交，才能让“任务已完成”只对应一份真实结果。本章讲的是被确认的那台状态机，并在结尾整理出“持久状态什么时候允许确认消息”的清单；ACK 报文本身和各故障时点留给[下一章](#44.%20%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 消息只是唤醒线索

消息载荷只有稳定的 job ID，不带 attempt (执行尝试) 编号。收到消息的 worker 得到的只是一个提示：“去数据库看看 `job-demo-731`”。消息本身不能创建一次执行，也不能证明谁有权执行。

这样设计是因为消息一定会重复：relay 会重发，broker 会重投。任何一条唤醒，包括上一轮迟到的旧消息，都只能去**竞争数据库里当前这一轮 `queued`**；谁有权推进，由数据库里的状态和 attempt 决定，而不是靠辨认消息的新旧。

### 条件领取：先占执行槽，再改状态

worker 要领取 job，按这个顺序：

1. **先在本进程取得一个物理执行槽。** execution slot (执行槽) 是进程真正能同时运行的 attempt 数，代表 CPU、数据库连接、游标、上传句柄这些实际资源。本例每个 worker 进程 8 个槽。取不到槽就不领取：不要先把 job 改成 `running` 再塞进一个无界的进程内队列，也不要确认掉唯一的唤醒消息。消费速度靠 broker 的预取上限和暂停消费来控制（见[下一章](#44.%20%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)）。
2. **再用一条条件更新领取。** 只有 job 仍是 `queued`、`available_at` 已经到了、没有取消请求时，才把它改成 `running`，attempt 加一，写入租约到期时间，并在同一事务里归还它占着的等待槽：

~~~sql
BEGIN;
WITH claimed AS (
  UPDATE report_jobs
  SET status = 'running',
      attempt = attempt + 1,
      lease_expires_at = clock_timestamp() + :lease_duration,
      holds_waiting_slot = false
  WHERE job_id = :job_id
    AND status = 'queued'
    AND available_at <= clock_timestamp()
    AND cancel_requested = false
  RETURNING attempt
), released AS (
  UPDATE admission_budget
  SET waiting_count = waiting_count - 1
  WHERE pipeline = 'report-export'
    AND EXISTS (SELECT 1 FROM claimed)
)
SELECT attempt FROM claimed;
COMMIT;
~~~

3. **看返回行数。** 返回一行，就是赢家，返回的 attempt（例如 1）就是它的代次。返回零行，说明别人已经领取、job 已取消或已终结、或者还没到 `available_at`；worker 立即归还刚占的物理槽，再读一次 job，决定怎样处理手上这条消息（见本章末的清单）。

两个 worker 同时执行这条 UPDATE 时，第二个要等第一个释放行锁；在 Read Committed 下，它拿到锁后会在新版本的行上重新检查 `status = 'queued'`，于是更新零行。“条件写在写语句上、返回行数就是业务判断”这条原理在[两个请求争夺最后一件库存时怎样只预留一次](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)讲完整。

![已提交的 job 经 outbox 与 broker 唤醒，worker 先取物理执行槽，再条件领取当前排队轮次](../../engineering-foundations/services/resources/system-design-execution.svg)

要分清两种槽。**等待槽**是数据库里的计数，记“已受理、还没被领取”的逻辑排队轮次，领取时归还；**物理执行槽**在 worker 进程里，记正在占用资源的 attempt，要等该 attempt 真正停止、释放资源后才归还。等待槽的数量规划在[容量章](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)。

领取成功后，worker 在读取任何报表数据之前，先确认原请求主体此刻仍有 `report:export`。若权限已被撤销，就不读数据，以当前 attempt 为条件提交 `failed` 和 `authorization_revoked`。为什么后台任务要在执行时重验权限，见[服务怎样逐次确认主体能做这个动作](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)。

### 栅栏：怎样挡住醒来的旧 worker？

worker 可能卡住：进程停顿、网络分区、机器失联。为了让 job 不永远卡在 `running`，领取时写了 lease (租约)：到期时间之后，独立的恢复器可以接管。但这里有一个最容易弄错的地方。

**租约到期不会让旧 worker 停下，也不会自动撤销它的写权。** 时钟走过 `lease_expires_at` 的那一刻，数据库里什么都没变：行仍然是 `running / attempt = 1`，旧 worker A 仍可能醒来并提交。到期只给了恢复器一个资格：它可以去**竞争**接管。

真正把 A 挡在外面的，是 fencing (栅栏)。它由两部分组成，缺一不可：

1. **单调递增的代次。** 每次领取都让 attempt 加一。代次只增不减，新执行者的编号一定大于旧的。
2. **在提交处检查。** 每一次写入（成功、失败、取消、续租）都把“我是第几代”写进条件里：`WHERE status = 'running' AND attempt = :my_attempt`。不匹配，就更新零行。

于是栅栏生效的时刻是**恢复器的接管事务提交的那一刻**，而不是时钟到达租约时刻。下图以 `job-demo-731` 为例，画出恢复器先提交时 A 怎样被挡住：

~~~mermaid
sequenceDiagram
    participant A as worker A
    participant DB as job-demo-731 行
    participant R as 恢复器
    participant B as worker B
    A->>DB: 条件领取
    DB-->>A: running / attempt = 1，写入租约
    Note over A: 停顿
    Note over DB: 租约到期：行仍是 running / attempt = 1<br/>A 若此刻醒来提交成功，仍然有效
    R->>DB: 接管：锁行，仍是 running / attempt = 1 且租约已过期
    DB-->>R: 提交 queued + 等待槽 + 新 outbox 意图
    Note over DB: 栅栏从这一刻生效
    B->>DB: 条件领取新一轮
    DB-->>B: running / attempt = 2
    A->>DB: 醒来提交成功，条件<br/>status = 'running' AND attempt = 1
    DB-->>A: 更新零行，A 的结果不生效
~~~

反过来，如果 A 的成功事务先于恢复器提交，job 就是 `succeeded`；恢复器随后看到终态，不会重排。两种顺序都只有一个赢家，赢家由行锁和提交顺序决定。恢复器在接管时怎样在取消、失败和重排之间选择，见[收尾一章的决策图](#%E9%87%8D%E8%AF%95%E4%B8%8E%E6%81%A2%E5%A4%8D%E6%8C%89%E4%BB%80%E4%B9%88%E9%A1%BA%E5%BA%8F%E5%86%B3%E5%AE%9A%EF%BC%9F)。

栅栏挡住的是**写入**，不是**进程**。A 在被栅栏之后仍可能继续读数据、上传对象、占着它的物理执行槽，直到它自己停下。所以对象键要按 attempt 区分，物理槽要等 A 真正释放资源后才归还；这两件事在收尾一章展开。

同一个原理在全领域反复出现，各处只是换了“代次”的名字：

- 分片搬迁时，账户的 owner 与 epoch 以及目录上的比较并交换（见[把一个账户搬到新分片时怎样保证只有一个写入者](#32.%20%E6%8A%8A%E4%B8%80%E4%B8%AA%E8%B4%A6%E6%88%B7%E6%90%AC%E5%88%B0%E6%96%B0%E5%88%86%E7%89%87%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%BB%BB%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E6%9C%89%E4%B8%80%E4%B8%AA%E5%86%99%E5%85%A5%E8%80%85%EF%BC%9F)）；
- Kafka 消费者组的 generation 只栅栏 offset 提交，写外部数据库还要一条所有权行（见[Kafka 分区与偏移](#45.%20%E6%80%8E%E6%A0%B7%E7%94%A8%20Kafka%20%E5%88%86%E5%8C%BA%E4%BF%9D%E5%BA%8F%E3%80%81%E6%8E%A8%E8%BF%9B%E5%81%8F%E7%A7%BB%EF%BC%8C%E5%B9%B6%E5%9C%A8%E5%86%8D%E5%9D%87%E8%A1%A1%E5%90%8E%E5%AE%89%E5%85%A8%E6%8E%A5%E6%89%8B%EF%BC%9F)）；
- outbox 回写以 `intent_id` 为条件，旧一轮的回执改不了新一轮（见[上一章](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)）。

对象存储的条件写（例如“同名对象不存在才写入”）只能防止覆盖某个对象名，不知道谁是当前 attempt，替代不了数据库里的栅栏。

### 租约要用数据库的时钟判断

租约是否过期，必须用**同一个时钟**判断，这个时钟就是数据库的时钟。worker 不能看自己机器的时间觉得“我的租约应该还有效”，更不能凭本地时钟认定租约已过期、自己给 attempt 加一。

PostgreSQL 里还有一个细节：`now()`（以及 `CURRENT_TIMESTAMP`、`transaction_timestamp()`）返回的是**事务开始的时刻**，在整个事务里不变；`clock_timestamp()` 返回的才是**调用这一刻**的时间。一个事务如果先等了几秒行锁，再用 `lease_expires_at > now()` 判断，比较的是几秒前的时间，可能把已经过期的租约当成有效。所以租约判断和续租都用 `clock_timestamp()`。

续租也是一次带栅栏的写：在锁住 job 行之后，用 `clock_timestamp()` 检查状态、attempt 和租约仍然有效，再延长到期时间。否则一个已经过期的 worker 等到锁之后，可能又把自己的租约续活：

~~~sql
BEGIN;
SELECT 1 FROM report_jobs WHERE job_id = :job_id FOR UPDATE;
UPDATE report_jobs
SET lease_expires_at = clock_timestamp() + :lease_duration
WHERE job_id = :job_id
  AND status = 'running'
  AND attempt = :my_attempt
  AND lease_expires_at > clock_timestamp();
COMMIT;
~~~

### 成功提交：只有一行加一次确认的提交才算数

对象存储不在数据库事务里，所以成功提交分两步。

**第一步，写 attempt 私有的对象。** 结果先上传到只属于这次 attempt 的键，例如 `reports/job-demo-731/attempt-2.csv`。此时对象只是存在，用户还看不到它：没有任何已提交的 job 指向它。

**第二步，一个事务里条件提交三件事。** 以 job ID、`status = 'running'`、当前 attempt 和 `cancel_requested = false` 为条件，把 job 改成 `succeeded`，写入对象键、成功时间和结果到期时间；同一个事务里，只有这条更新真的命中时，才插入 `report.ready` outbox。用 CTE 把两者串起来：

~~~sql
BEGIN;
WITH completed AS (
  UPDATE report_jobs AS j
  SET status = 'succeeded',
      result_object_key = :attempt_object_key,
      lease_expires_at = NULL,
      succeeded_at = t.ts,
      terminal_at = t.ts,
      result_expires_at = t.ts + interval '7 days'
  FROM (SELECT clock_timestamp() AS ts) AS t
  WHERE j.job_id = :job_id
    AND j.status = 'running'
    AND j.attempt = :my_attempt
    AND j.cancel_requested = false
  RETURNING j.job_id, j.attempt
)
INSERT INTO report_outbox(operation_key, job_id, attempt, payload)
SELECT 'job-demo-731:report-ready:v1', job_id, attempt,
       '{"jobId":"job-demo-731","reportId":42,"type":"report.ready"}'
FROM completed
RETURNING operation_key, attempt;
COMMIT;
~~~

`report_outbox.operation_key` 上有唯一约束；`job-demo-731:report-ready:v1` 是由 job ID 加操作类型构成的稳定操作键（构造规则见[远端操作键](#%E8%BF%9C%E7%AB%AF%E5%89%AF%E4%BD%9C%E7%94%A8%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%8F%AF%E4%BB%A5%E9%87%8D%E5%8F%91%EF%BC%9F)）。这样“已就绪”通知只可能对应真正成功的那一份结果：不会出现通知已发出、job 却还是 `running`，或后来被另一个 attempt 接管的假成功。

**只有 `INSERT ... RETURNING` 返回恰好一行，且应用收到 `COMMIT` 成功，才算“持久状态允许确认”。** 其余情况都不是成功：

- **返回零行。** `completed` 没有更新任何行，INSERT 也就没写 ready 意图，但整个事务照样能提交成功，所以 `COMMIT` 成功本身不是许可。零行说明当前 attempt 已经不是赢家：可能 job 已终结、已被恢复器重排、已被更高的 attempt 领取，或者有了取消请求。worker 要在新连接上重读 job 和 outbox，按本章末的清单决定后续。若零行是因为 `cancel_requested = true` 而 worker 仍持有同一个 `running` attempt，它转去提交取消（见收尾一章）。
- **`COMMIT` 结果未知。** 提交请求发出后连接断了，持久结果就是未知：可能已提交，也可能没有。既不能当成功确认，也不能宣称已回滚。在新连接上查 job 和 ready 意图；读到一次 `running` 也不能证明原事务回滚了，因为可能读得太早。在结局查清之前，这个 attempt 的对象不能当孤儿删掉。

![当前 attempt 复验权限、读取与上传后，只有更新一行且提交确认才走成功分支；零行或提交未知另行查证](../../engineering-foundations/services/resources/system-design-result-commit.svg)

图中的 ACK 是下一章的内容，这里只需记住它的前提：数据库已经给出了一个持久的结论。

### 什么时候允许确认手上的消息？

worker 每次处理完一条消息，都要回答“这条消息还需要保留吗”。判断依据只有数据库里已提交的状态。下面是交给下一章的清单：

| 重读到的持久状态 | 允许确认这条消息吗 |
| --- | --- |
| `succeeded`、`failed` 或 `cancelled`，且必要的清理或保留决定已提交 | 允许：这个 job 已经没有需要这条消息驱动的工作 |
| 被重排为 `queued`：新的 `available_at`、等待槽和新 outbox 意图都已提交 | 允许：新一轮有自己的唤醒 |
| 更大的 attempt 已经领取并提交，且有可靠的租约恢复路径 | 允许：后继执行者负责，失联也有人接管 |
| `running` 且租约有效，属于别的 worker | 只有确认存在独立、持久的租约恢复器时才允许；否则保留或延后 |
| `running` 但租约已过期，恢复器还没提交接管 | 不允许：过期不等于旧 attempt 失权，此刻没有任何持久的后续安排 |
| `queued` 但 `available_at` 未到（早到的重复消息） | 只有到期唤醒已持久安排好时才允许；否则延后或保留 |
| 自己的成功提交返回一行且 `COMMIT` 确认 | 允许 |
| 零行，或 `COMMIT` 结果未知 | 重读之后再按上面各行判断；未查清之前不允许 |

一句话：**确认消息之前，数据库里必须已经有一个终态，或者一条已提交、可恢复的后续路径。** 这条规则的 broker 侧细节，例如用哪个 delivery tag 确认、确认丢了会怎样，见[发布确认、消费者确认和业务完成各证明什么](#44.%20%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 变体：直接把 SQL 表当队列

既然业务状态本来就以数据库为准，也可以完全不用 broker，让 worker 轮询 job 表。PostgreSQL 的 `FOR UPDATE SKIP LOCKED` 让并发的领取者跳过已被别的事务锁住的候选行，避免同一行同时交给两个 worker。它有意给出不完整的视图，所以只适合这种竞争领取，不适合普通的一致性读取。

做法是：领取事务选中一行，提交 `running`、attempt 加一和新租约后立即释放行锁；耗时的工作在事务之外做，事务越短，锁等待越少。代价是轮询、候选扫描和行锁的压力都落在数据库上。要观察空轮询次数、领取延迟和锁等待，负载上来后再决定是否引入独立的 broker。

这个变体常和另一种租约约定一起出现，必须先说清楚。本主线的案例采用**宽松约定**：租约到期只给恢复器竞争资格，旧 worker 在接管提交之前仍可能先完成。另一种是**严格租期**：每次写入都额外要求 `lease_expires_at > clock_timestamp()`，租约一到期就拒绝旧 worker，即使恢复器还没接管。两种都成立，但**同一种 job 只能选一种**，不能有的写入检查租期、有的不检查。

下面用一个与 `job-demo-731` 无关的独立任务 `pg-job-demo-42` 展示严格租期变体（30 秒租约是演示值）。和上一张栅栏图对照，区别在于 A 在租约到期、B 还没接管时就已被拒绝：

~~~mermaid
sequenceDiagram
    participant A as worker A
    participant DB as pg-job-demo-42 行
    participant B as worker B
    A->>DB: SKIP LOCKED 领取
    DB-->>A: running / attempt = 1，租约 30 秒
    Note over DB: A 的租约到期，B 尚未接管
    A->>DB: 醒来尝试完成，条件含<br/>lease_expires_at > clock_timestamp()
    DB-->>A: 更新零行（严格租期拒绝）
    B->>DB: SKIP LOCKED 接管过期行
    DB-->>B: running / attempt = 2，新租约
    B->>DB: 同一事务：succeeded、<br/>reports/42/attempt-2、report.ready 意图
    DB-->>B: 1 行，提交
    A->>DB: 迟到完成 attempt = 1
    DB-->>A: 状态与 attempt 都不匹配，更新零行，不覆盖 B
~~~

这个例子还演示了另一种情况：在最终结果之前允许发出的“处理中”通知 `report.processing`。它同样只能由当前 attempt 登记，用单条语句同时完成“有没有写权”和“插入或比对已有意图”。结果有四列，含义如下：

| 情况 | `authorized, inserted, existing_intent, same_request` | 处理 |
| --- | --- | --- |
| B 首次登记 | `true, true, false, NULL` | 提交新意图，交给 relay 发布 |
| B 同键同摘要重放 | `true, false, true, true` | 原意图已存在，不再插入 |
| B 同键异摘要 | `true, false, true, false` | 报告冲突，不覆盖、不重发 |
| B 租约已过期，或已请求取消 | `false, false, false, NULL` | 无写权，结果里不透露摘要 |
| B 领取后，A 用 attempt 1 登记 | `false, false, false, NULL` | 无写权，看不到 B 的摘要 |

有写权、没插入、却又查不到已有行，说明唯一键或保留期的假设被破坏，应回滚并告警，不能把 `NULL` 当成功。另外，如果不用 `ON CONFLICT` 而直接插入、撞上唯一约束，PostgreSQL 的当前事务就已经失败，要先回滚，再在新事务里核查。

> [!example]- 完整 SQL：严格租期下的领取、意图去重与完成（PostgreSQL 14.25 单会话实跑）
> 在一个 `psql` 会话里从头运行即可：`psql` 默认每条语句自动提交，显式 `BEGIN/COMMIT` 标出事务边界，临时表只在本会话有效。默认 Read Committed 下每条语句取新快照，所以在已锁住 job 行的事务里，`record_processing` 按当时已提交的状态判断写权。所有能为同一 job 写意图的执行者都要先锁 job 行。若改用 Repeatable Read 或 Serializable，要处理序列化失败并重试整个事务。表结构只保留 attempt、租约和意图，没有建模账户授权、共享等待槽或 broker。
>
> ~~~sql
> CREATE TEMP TABLE report_jobs (
>   job_id text PRIMARY KEY,
>   status text NOT NULL,
>   attempt integer NOT NULL DEFAULT 0,
>   available_at timestamptz NOT NULL,
>   lease_expires_at timestamptz,
>   cancel_requested boolean NOT NULL DEFAULT false,
>   result_key text
> );
> INSERT INTO report_jobs(job_id, status, attempt, available_at)
> VALUES ('pg-job-demo-42', 'queued', 0, clock_timestamp() - interval '1 second');
>
> CREATE TEMP TABLE job_effect_outbox (
>   operation_key text PRIMARY KEY,
>   job_id text NOT NULL REFERENCES report_jobs(job_id),
>   attempt integer NOT NULL,
>   request_sha256 text NOT NULL,
>   payload text NOT NULL
> );
>
> -- Worker A：取得执行槽后领取并提交；返回 attempt=1 和新租约。
> WITH candidate AS (
>   SELECT job_id
>   FROM report_jobs
>   WHERE cancel_requested = false
>     AND ((status = 'queued' AND available_at <= clock_timestamp())
>       OR (status = 'running' AND lease_expires_at <= clock_timestamp()))
>   ORDER BY available_at, job_id
>   LIMIT 1
>   FOR UPDATE SKIP LOCKED
> )
> UPDATE report_jobs AS j
> SET status = 'running',
>     attempt = j.attempt + 1,
>     lease_expires_at = clock_timestamp() + interval '30 seconds'
> FROM candidate AS c
> WHERE j.job_id = c.job_id
>   AND j.cancel_requested = false
> RETURNING j.job_id, j.status, j.attempt, j.lease_expires_at;
>
> -- 为了不等 30 秒，把 A 的租约手动置为已过期。
> UPDATE report_jobs
> SET lease_expires_at = clock_timestamp() - interval '1 second'
> WHERE job_id = 'pg-job-demo-42' AND attempt = 1;
>
> -- A 到期后、B 接管前尝试完成：返回 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> UPDATE report_jobs
> SET status = 'succeeded', result_key = 'reports/42/attempt-1', lease_expires_at = NULL
> WHERE job_id = 'pg-job-demo-42'
>   AND status = 'running'
>   AND attempt = 1
>   AND cancel_requested = false
>   AND lease_expires_at > clock_timestamp()
> RETURNING job_id, status, attempt;
> COMMIT;
>
> -- B 接管过期任务，提交 attempt=2 与新租约。
> WITH candidate AS (
>   SELECT job_id
>   FROM report_jobs
>   WHERE cancel_requested = false
>     AND ((status = 'queued' AND available_at <= clock_timestamp())
>       OR (status = 'running' AND lease_expires_at <= clock_timestamp()))
>   ORDER BY available_at, job_id
>   LIMIT 1
>   FOR UPDATE SKIP LOCKED
> )
> UPDATE report_jobs AS j
> SET status = 'running',
>     attempt = j.attempt + 1,
>     lease_expires_at = clock_timestamp() + interval '30 seconds'
> FROM candidate AS c
> WHERE j.job_id = c.job_id
>   AND j.cancel_requested = false
> RETURNING j.job_id, j.status, j.attempt, j.lease_expires_at;
>
> -- 只有当前 attempt 有写权时才插入或比对意图；无写权时不返回摘要。
> PREPARE record_processing(text, integer, text, text, text) AS
> WITH eligible AS MATERIALIZED (
>   SELECT job_id, attempt
>   FROM report_jobs
>   WHERE job_id = $1
>     AND status = 'running'
>     AND attempt = $2
>     AND cancel_requested = false
>     AND lease_expires_at > clock_timestamp()
> ),
> inserted AS (
>   INSERT INTO job_effect_outbox(operation_key, job_id, attempt, request_sha256, payload)
>   SELECT $3, e.job_id, e.attempt, $4, $5
>   FROM eligible AS e
>   ON CONFLICT (operation_key) DO NOTHING
>   RETURNING operation_key, attempt
> ),
> existing AS MATERIALIZED (
>   SELECT o.request_sha256
>   FROM eligible AS e
>   JOIN job_effect_outbox AS o
>     ON o.job_id = e.job_id
>    AND o.operation_key = $3
>   WHERE NOT EXISTS (SELECT 1 FROM inserted)
> )
> SELECT EXISTS (SELECT 1 FROM eligible) AS authorized,
>        EXISTS (SELECT 1 FROM inserted) AS inserted,
>        EXISTS (SELECT 1 FROM existing) AS existing_intent,
>        (SELECT request_sha256 = $4 FROM existing) AS same_request;
>
> -- B 首次登记 report.processing；摘要是下面 JSON 字节的 SHA-256。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 2, 'pg-job-demo-42:report-progress:v1',
>   '55799e91985ab0123fa1b56b65fb4112ad1bd06e50945da075bfe1705f365817',
>   '{"jobId":"pg-job-demo-42","type":"report.processing"}'
> );
> COMMIT;
>
> -- B 同键同摘要重放：识别既有意图，不再插入。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 2, 'pg-job-demo-42:report-progress:v1',
>   '55799e91985ab0123fa1b56b65fb4112ad1bd06e50945da075bfe1705f365817',
>   '{"jobId":"pg-job-demo-42","type":"report.processing"}'
> );
> COMMIT;
>
> -- B 同键异正文：报告冲突，不覆盖。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 2, 'pg-job-demo-42:report-progress:v1',
>   '7d5a6ce6ab778ec8937d1dd76a25e4a3d1b5f9e4cb5c3d7fb43196f3ea8a77f3',
>   '{"jobId":"pg-job-demo-42","type":"report.processing","phase":"other"}'
> );
> COMMIT;
>
> -- B 租约过期：即使同键同摘要意图存在，也不返回摘要。
> UPDATE report_jobs
> SET lease_expires_at = clock_timestamp() - interval '1 second'
> WHERE job_id = 'pg-job-demo-42' AND attempt = 2;
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 2, 'pg-job-demo-42:report-progress:v1',
>   '55799e91985ab0123fa1b56b65fb4112ad1bd06e50945da075bfe1705f365817',
>   '{"jobId":"pg-job-demo-42","type":"report.processing"}'
> );
> COMMIT;
>
> -- 恢复租期但请求取消：仍无写权。
> UPDATE report_jobs
> SET lease_expires_at = clock_timestamp() + interval '30 seconds',
>     cancel_requested = true
> WHERE job_id = 'pg-job-demo-42' AND attempt = 2;
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 2, 'pg-job-demo-42:report-progress:v1',
>   '55799e91985ab0123fa1b56b65fb4112ad1bd06e50945da075bfe1705f365817',
>   '{"jobId":"pg-job-demo-42","type":"report.processing"}'
> );
> COMMIT;
>
> -- B 恢复正常；A 用 attempt=1 登记：无写权，看不到 B 的摘要。
> UPDATE report_jobs
> SET cancel_requested = false,
>     lease_expires_at = clock_timestamp() + interval '30 seconds'
> WHERE job_id = 'pg-job-demo-42' AND attempt = 2;
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> EXECUTE record_processing(
>   'pg-job-demo-42', 1, 'pg-job-demo-42:report-progress:v1',
>   '55799e91985ab0123fa1b56b65fb4112ad1bd06e50945da075bfe1705f365817',
>   '{"jobId":"pg-job-demo-42","type":"report.processing"}'
> );
> COMMIT;
> DEALLOCATE record_processing;
>
> -- 只有当前 attempt=2 的成功更新命中时，才在同一事务创建 report.ready 意图。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> WITH completed AS (
>   UPDATE report_jobs
>   SET status = 'succeeded',
>       result_key = 'reports/42/attempt-2',
>       lease_expires_at = NULL
>   WHERE job_id = 'pg-job-demo-42'
>     AND status = 'running'
>     AND attempt = 2
>     AND cancel_requested = false
>     AND lease_expires_at > clock_timestamp()
>   RETURNING job_id, attempt
> )
> INSERT INTO job_effect_outbox(operation_key, job_id, attempt, request_sha256, payload)
> SELECT 'pg-job-demo-42:report-ready:v1',
>        job_id,
>        attempt,
>        'c4dd0f89af3442f1d58ade3561dc85ed51e5e458c7bc58873c2069d0fc97a27c',
>        '{"jobId":"pg-job-demo-42","reportId":42,"type":"report.ready"}'
> FROM completed
> RETURNING operation_key, attempt;
> COMMIT;
>
> -- A 在 B 成功后迟到完成：仍返回 0 行。
> BEGIN;
> SELECT job_id FROM report_jobs WHERE job_id = 'pg-job-demo-42' FOR UPDATE;
> UPDATE report_jobs
> SET status = 'succeeded', result_key = 'reports/42/attempt-1', lease_expires_at = NULL
> WHERE job_id = 'pg-job-demo-42'
>   AND status = 'running'
>   AND attempt = 1
>   AND cancel_requested = false
>   AND lease_expires_at > clock_timestamp()
> RETURNING job_id, status, attempt;
> COMMIT;
>
> -- 核实成功状态、对象引用与 ready 意图来自同一次提交。
> SELECT j.status, j.attempt, j.result_key, o.operation_key, o.attempt AS intent_attempt
> FROM report_jobs AS j
> JOIN job_effect_outbox AS o USING (job_id)
> WHERE j.job_id = 'pg-job-demo-42'
>   AND o.operation_key = 'pg-job-demo-42:report-ready:v1';
> ~~~

### 实例：BullMQ 的锁续期失效为什么会重复执行？

> [!info] BullMQ 6.7.5（2026-11-11 发布，核对于 2026-11-12）
> BullMQ 把 job 状态存在 Redis 里。worker 领取 job 时取得一把有时限的 Redis lock，处理期间要不断续期。进程异常退出、Redis 连接故障，或 CPU 密集工作把 Node.js 事件循环占满，都可能让续期没按时完成；随后 stalled checker 把 job 放回 waiting，让 worker 重新执行。停滞次数超过 `maxStalledCount`（该版本默认 1）后转入 failed。处理器抛出普通异常走 attempts/backoff 重试，锁丢失走 stalled 恢复，两者分开计数。
>
> 所以要监控 stalled 事件，并让 CPU 密集工作定期把控制权交还事件循环（见[Node.js 的工作实际在哪个线程上执行](#17.%20Node.js%20%E7%9A%84%E5%B7%A5%E4%BD%9C%E5%AE%9E%E9%99%85%E5%9C%A8%E5%93%AA%E4%B8%AA%E7%BA%BF%E7%A8%8B%E6%88%96%E8%BF%9B%E7%A8%8B%E4%B8%8A%E6%89%A7%E8%A1%8C%EF%BC%9F)）。调大 lock duration 只会推迟发现真正的崩溃，挡不住业务副作用重复。
>
> 如果业务状态仍以 PostgreSQL 的 job 行为准，Redis lock 就只影响 BullMQ 何时重投，既不授予也不撤销写权；写权仍由本章的状态与 attempt 栅栏决定。几个落地细节：每条 outbox 意图有稳定 UUID，加上 `outbox-` 前缀作为 BullMQ 自定义 job ID。官方文档要求自定义 ID 不能只由数字组成、不能含冒号；该版本源码会拒绝 `42` 和 `a:b`，但带前导零的 `0042` 能通过，不要依赖这种边缘行为。自定义 ID 只在所属 queue 内、且 job 仍被保留时去重；job 被移除后同一 ID 可以再次添加。Redis 的持久化要在部署时显式配置；若允许已确认的 job 丢失，就要能发现数据库里长期停在 `queued` 的 job 并重建唤醒。

### 本章产出与下一步

现在 `job-demo-731` 有一台以数据库为准的状态机：条件领取让每一轮只有一个赢家；单调的 attempt 加上提交处的检查，挡住醒来的旧 worker；成功只在“一行加一次确认的提交”时成立；每种持久状态都对应“能否确认手上的消息”。下一章把这张清单接到 broker 上：publisher confirm 和 consumer ACK 各证明什么，ACK 发出前后崩溃又会怎样？见[发布确认、消费者确认和业务完成各证明什么](#44.%20%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - `FOR UPDATE SKIP LOCKED` 跳过不能立即加锁的行、刻意提供不一致视图、适合类队列的多消费者领取：[PostgreSQL 18, SELECT — The Locking Clause](https://www.postgresql.org/docs/18/sql-select.html)，核对于 2026-11-12；行锁的持有到事务结束：[Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html)。
> - `now()`/`transaction_timestamp()` 返回事务开始时间、`clock_timestamp()` 返回调用时刻：[PostgreSQL 18, Date/Time Functions §9.9.5 Current Date/Time](https://www.postgresql.org/docs/18/functions-datetime.html)，核对于 2026-11-12；另在 PostgreSQL 14.25 本地以“事务内 `pg_sleep(1)` 后比较两者”复核。
> - Read Committed 下并发 `UPDATE` 等锁后在新版本上重检条件；Repeatable Read 与 Serializable 需处理序列化失败：[PostgreSQL 18, Transaction Isolation §13.2](https://www.postgresql.org/docs/18/transaction-iso.html)。
> - 数据修改 CTE 把 `UPDATE ... RETURNING` 的实际行交给后续 `INSERT`；`ON CONFLICT` 与 `RETURNING` 只报告实际插入的行：[Data-Modifying Statements in WITH](https://www.postgresql.org/docs/18/queries-with.html)、[INSERT](https://www.postgresql.org/docs/18/sql-insert.html)。本章的领取 SQL、成功提交 SQL 与折叠块中的严格租期 SQL 均在 PostgreSQL 14.25 本地实跑。attempt、租约、栅栏与确认清单是应用合同，不由 PostgreSQL 定义。
> - BullMQ 6.7.5：[Important Notes](https://github.com/taskforcesh/bullmq/blob/v6.7.5/docs/gitbook/bull/important-notes.md)、[Stalled Jobs](https://github.com/taskforcesh/bullmq/blob/v6.7.5/docs/gitbook/guide/workers/stalled-jobs.md)（至少一次运行、锁续期、事件循环阻塞、达到上限后失败）；[WorkerOptions](https://github.com/taskforcesh/bullmq/blob/v6.7.5/src/interfaces/worker-options.ts)（`maxStalledCount` 默认 1）；[Retrying failing jobs](https://github.com/taskforcesh/bullmq/blob/v6.7.5/docs/gitbook/guide/retrying-failing-jobs.md)；[Job IDs](https://github.com/taskforcesh/bullmq/blob/v6.7.5/docs/gitbook/guide/jobs/job-ids.md) 与版本源码 [job.ts](https://github.com/taskforcesh/bullmq/blob/v6.7.5/src/classes/job.ts#L1278-L1289)（自定义 ID 的约束与去重范围）；[Going to production](https://docs.bullmq.io/guide/going-to-production)（Redis 持久化需显式配置）；[v6.7.5 release](https://github.com/taskforcesh/bullmq/releases/tag/v6.7.5)。核对于 2026-11-12。
> - Amazon S3 条件写（`If-None-Match: *` 防覆盖同名对象）：[Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)，核对于 2026-11-12；本章的栅栏不依赖它。
## 44. 发布确认、消费者确认和业务完成各证明什么？

上一章把 `job-demo-731` 的状态机整理成了一张清单：数据库里出现什么持久状态时，worker 才可以确认手上的消息。本章把这张清单接到 broker (消息代理) 上，回答：relay (中继) 收到的 publisher confirm (发布确认) 证明了什么；worker 发出的 consumer ACK (消费者确认) 又证明了什么；这些确认在不同时刻丢失或崩溃时，系统会落在哪里；最后，怎样分段观测这条链路。机制先按一般的 broker 讲，RabbitMQ 4.4 的具体行为放在各节的实例里。

### 三个事实，由三个不同的组件观察

一次导出从 API 到 ACK 要经过六段交接。下图是整条链路的总览：每段只有自己的证据（绿字），其中三段各产生一个独立的事实——API 看到数据库持久受理了 job，relay 看到 broker 按约定接收了一次发布，worker 看到业务结果已完成；右栏是观测这一段的信号，红圈 ①–④ 是后文要分析的崩溃点。后文的发布确认图展开第 2 段，成功分支图展开第 4–6 段。

![交接链从 API 受理、relay 发布、broker 队列、worker 领取、成功提交到 ACK；每段标出证据与观测信号，四个红圈标出崩溃点](../../engineering-foundations/services/resources/queue-handoff-chain.svg)

这三件事不能互相推导。publisher confirm 只说明 broker 收下了消息，不知道 worker 是否收到、处理或完成；consumer ACK 只是结束 broker 对**这一次投递**的待确认状态，它本身不说明报表成功了。按上一章的规则，worker 在 ACK 之前必须已经提交某个终态，或已经持久安排好重试或接管，所以 ACK 可能对应成功、失败、取消或“已交给下一轮”，任何一种都有可能。

数据库和 broker 之间也没有共享的原子事务。outbox (事务发件箱) 消除的只是“数据库已提交、进程却在发布前崩溃”这一个缺口（见[耗时任务怎样被持久受理](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)），relay 和 worker 仍然必须容忍重复。因此本领域不把“最终业务效果只发生一次”简称为 exactly-once (恰好一次)：它靠的是数据库里的状态条件、幂等键、远端的去重约定和恢复路径，而不是哪一层的某一次确认。

还要分清三种身份：幂等键 `export-demo-415` 识别客户端的一次意图，报表 ID 42 识别业务对象，job ID `job-demo-731` 识别一次持久受理的作业。消息里只带最后一个。

### publisher confirm 只回答“broker 收下了没有”

publisher confirm 覆盖的只是 relay 到 broker 这一段。它有两个固有的局限：

- **回执可能丢失。** broker 已经收下消息，confirm 却在网络里丢了，relay 分不清“没收到”和“收到了但回复丢了”。为了不丢消息只能重发，于是同一个 job 可能出现多条消息。
- **“收下”不等于“送到了该去的地方”。** broker 接收后要按路由规则把消息放进队列；消息可能进了零个队列，也可能进了一个兜底队列。confirm 是否涵盖路由结果，取决于 broker 和发布选项。

所以 relay 只有在本次 confirm 已核实、路由符合预期、持久性条件满足时，才把对应的 outbox 意图标为 `published`。`published` 只是 relay 自己的记录，不是 worker 开始执行的前提：broker 完全可能先把消息投递给 worker，relay 之后才收到 confirm 去回写 outbox。

> [!info] 实例：RabbitMQ 4.4 的发布确认（核对于 2026-11-12）
> - 要在发布用的 channel 上显式开启 confirm（AMQP 0-9-1 的 `confirm.select` 或客户端库的对应 API）。`mandatory` 标志不会开启 confirm，它只决定消息无法路由时是否退回。
> - exchange 按 binding 把消息路由到零个或多个 queue，confirm 本身不保证路由成功。带 `mandatory` 的不可路由消息会**先**收到 `basic.return`，**再**收到 confirm ACK，所以同一次发布的 return 和 confirm 必须合起来判断。
> - 收到 confirm ACK 且没有 return，也只说明消息至少进了一个 queue：alternate exchange (备用交换器) 可能把它送去了别处，所以要事先核验 exchange、binding 和目标 queue。
> - 持久性：classic durable queue 中的 persistent 消息在写入磁盘后才确认；quorum queue 在多数副本接受后才确认。放进 durable queue 的 transient 消息即使写过盘，节点重启时也会丢；要在重启后保留，队列和消息都必须是持久的。

### relay 怎样判定一次发布已完成？

relay 要把一个异步回执对应到唯一一次发布。本例的做法是：

1. relay 逐条读取 `pending` 的 outbox 意图，发布它指向的 job ID。用哪条 channel、confirm 序号是多少，只保存在内存里；数据库回写仍以 `intent_id` 为条件。
2. 每条 publisher channel 同一时刻只保留一次在途发布。confirm 的 ACK/NACK 带 channel 上的发布序号，还可能用 `multiple=true` 一次确认之前的多个序号；`basic.return` 则不带序号。只有一次在途时，return 只可能属于当前这次发送，relay 仍要核对 channel 和序号。
3. 只有本次 confirm ACK 已按 channel 和序号核实、没有本次的 `basic.return`、目标拓扑已核验、持久性条件满足，才把这条意图标为 `published`。
4. 遇到 NACK、return、channel 异常或关闭、confirm 迟迟不来，都保留这条意图为 `pending`。结果不明时，先关闭并弃用旧 channel，再用新 channel 重发。

这样仍消除不了“broker 已接受、数据库还没回写”造成的重复：broker 不会按业务 job ID 替应用去重。worker 一侧依靠上一章的条件领取处理重复。

![交接链第 2 段的展开：outbox 意图经 relay 发布到 RabbitMQ；每条 channel 只保留一条在途发布，以本次 return 与 confirm 决定意图能否标为 published](../../engineering-foundations/services/resources/queue-publish-confirm.svg)

### consumer ACK 的规则

broker 把消息投递给 worker 之后，这次 delivery (投递) 处于“待确认”状态。worker 用 ACK 告诉 broker“这次投递可以结束了”；broker 随后可以删除消息，不再重投。规则有三条：

1. **ACK 之前，数据库里必须已有终态或可恢复的后续路径。** 这就是上一章清单的总结。成功分支是：条件领取 → 写 attempt (执行尝试) 私有对象 → 条件提交 `succeeded`、对象键和 `report.ready` 意图 → 确认提交成功 → ACK。
2. **用这次投递自己的标识确认。** ACK 针对的是投递，不是业务对象，不能拿 job ID 代替。并行处理多条消息时，逐条确认，不要一次确认“这之前的全部”，否则会把还没完成的工作一并确认掉。
3. **ACK 可能丢。** 确认通常是 worker 发给 broker 的单向消息，broker 不逐条回执。发出后连接断开，ACK 是否到达就是未知的；消息若被重投，下一位 worker 照样按 job 状态判断。

可靠的任务处理要用手动确认。自动确认模式下，broker 在发出消息时就视为已交付；worker 若在持久化结果之前崩溃，broker 不会重投这条消息。

![交接链第 4–6 段的展开，成功分支：worker 条件领取，写私有对象，同一事务提交成功状态、对象键与 ready 意图，最后单条 ACK](../../engineering-foundations/services/resources/queue-consumer-ack.svg)

> [!info] 实例：RabbitMQ 4.4 的消费者确认（核对于 2026-11-12）
> - 用接收该消息的 channel 上的 delivery tag 确认；并行处理时 `multiple=false`。`multiple=true` 会连带确认该 channel 上更早的所有未确认投递。
> - `basic.ack` 是单向消息，broker 不回执。
> - 手动确认模式下，未确认的投递在 channel 或 connection 关闭后重新入队；这是 RabbitMQ 的行为，不能推广到所有 broker。

### 每种 job 状态下，这条投递怎样处理？

把上一章的状态清单和 broker 动作放进同一张表。收到一条投递（首次或重复）后，worker 先读权威 job，再按行处理：

| 读到的 job 状态 | worker 的动作 | 何时 ACK 这条投递 |
| --- | --- | --- |
| `queued` 且已到 `available_at` | 先取物理执行槽，再条件领取；只有一个事务能改成 `running` | 领取成功后继续处理，此时不 ACK；领取失败则重读状态 |
| `queued` 但未到 `available_at`（早到的重复） | 不能越过退避提前运行 | 到期唤醒已持久安排好时才 ACK；否则延后或保留未确认 |
| `running`、租约有效、属于别人 | 不另起并行 attempt | 确认有独立、持久的租约恢复器时才 ACK；否则保留或延后 |
| `running`、租约已过期、恢复器未提交接管 | 不自己给 attempt 加一 | 不 ACK；等恢复器提交取消、失败或重排 |
| 恢复器已提交重排（`queued`、等待槽、新 outbox） | 旧投递已无工作 | 可 ACK；新一轮由新意图唤醒 |
| 更大的 attempt 已领取并提交 | 旧投递已无工作 | 有可靠的租约恢复路径时可 ACK |
| `succeeded`、`failed`、`cancelled` | 不再计算，不覆盖结果 | 终态和必要的清理或保留决定已持久后 ACK |
| 自己的成功提交返回一行且 `COMMIT` 确认 | — | 立即 ACK |
| 自己的成功提交零行，或 `COMMIT` 结果未知 | 在新连接上重读 job 与 outbox | 按重读结果回到上面各行；查清之前不 ACK |
| 消息格式错误，或对应不到有效 job | 不能无限重排 | 隔离到 dead-letter queue (死信队列，DLQ) 或走会告警的拒绝路径 |

可重试的失败、取消和恢复器接管各自怎样把 job 推到上表的某一行，见[任务失败、被取消或 worker 失联后怎样收尾](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)。

### 在不同时刻崩溃，系统会落在哪里？

故障发生的位置，决定消息、job 和对象之间是什么关系。四个崩溃点及其落点已画在本章开头的交接链图里：① 让同一 job ID 出现多条消息，② 和 ③ 让同一条消息被再次投递，三者都靠数据库里的条件领取、终态和恢复器收敛。

④ 不同：它是把 ACK 挪到成功提交之前的错误顺序，broker 不会再投递，恢复只剩独立的租约扫描。这说明了为什么“先 ACK 再处理”是错的：它把唯一的恢复信号交了出去。

### prefetch 限制的是什么？

prefetch (预取上限) 限制每个消费者手上**未确认**的投递数，也就决定了 broker 能提前把多少任务推进 worker 的缓冲区。它不等于业务并发度：真正能同时做多少，还取决于处理器并发、进程内队列、数据库和对象存储的容量，以及 worker 的物理执行槽（本例每进程 8 个）。

预取设得过大，只是把等待从 broker 挪进 worker 的内存；worker 停机时，还会有更多已投递、未确认的工作需要回收。

**已预取但尚未开始的投递，必须有归还的路径。** worker 没有空闲执行槽、或正在关停时，它手上可能压着几条还没开始的投递。这些投递要么在连接关闭时由 broker 自动重新入队，要么由 worker 显式退回。这里的“退回”只是把一条**还没开始处理**的投递还给 broker；它和“处理失败后靠重新入队来重试”是两回事，后者为什么不可取，见收尾一章。关停时的完整顺序见[服务进程收到停止信号后怎样排空工作](#21.%20%E6%9C%8D%E5%8A%A1%E8%BF%9B%E7%A8%8B%E6%94%B6%E5%88%B0%E5%81%9C%E6%AD%A2%E4%BF%A1%E5%8F%B7%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%8E%92%E7%A9%BA%E5%B7%A5%E4%BD%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%80%80%E5%87%BA%EF%BC%9F)。

> [!info] 实例：RabbitMQ 4.4 的预取与归还（核对于 2026-11-12）
> - AMQP 0-9-1 的 `basic.qos(count)` 在 RabbitMQ 中按每个 consumer 分别生效：同一 channel 上三个 consumer 各设 4，就能各自持有 4 条未确认消息。`0` 表示不限；consumer 没有显式设置时，broker 可能套用管理员配置的默认值。按整个 channel 计算的 global QoS 从 4.3 起弃用并默认禁用。
> - `basic.cancel` 只阻止后续分发，不会丢弃或重排已经发出、尚未确认的投递。关闭 channel 会把其中未确认的投递自动重新入队；保留 channel 时，也可以用 `basic.reject` 或 `basic.nack` 并设 `requeue=true` 显式退回。

### 先进先出不等于先完成

FIFO (先进先出) 队列只描述消息的排队和投递次序。多个 consumer 并行处理时，较早投递的消息完全可能较晚完成。如果业务要求按账户、订单或报表的顺序生效，先定义顺序键和需要保证的**提交**顺序，再选一种办法：按键串行处理；用单一有序分区（见[Kafka 分区与偏移](#45.%20%E6%80%8E%E6%A0%B7%E7%94%A8%20Kafka%20%E5%88%86%E5%8C%BA%E4%BF%9D%E5%BA%8F%E3%80%81%E6%8E%A8%E8%BF%9B%E5%81%8F%E7%A7%BB%EF%BC%8C%E5%B9%B6%E5%9C%A8%E5%86%8D%E5%9D%87%E8%A1%A1%E5%90%8E%E5%AE%89%E5%85%A8%E6%8E%A5%E6%89%8B%EF%BC%9F)）；或者用持久的序号做条件更新，拦住越序的提交。

### 怎样分段观测这条链路？

每个确认只证明一段交接，所以观测也必须分段：本章开头交接链图的右栏，就是每一段各自的信号。只看一个数字（例如 ACK 数）会把不同位置的积压混在一起；被栅栏但仍在运行的 attempt 和连接池等待，说明执行资源可能被旧 attempt 占着，而不是 worker 不够。

读这些信号的几条要点：

- 即使队列还在接收消息，**最老消息年龄**持续上升，就说明结果在变慢。
- broker 积压很低，不能说明系统空闲：outbox 里尚未发布的意图、数据库里的 `queued` job 都可能在堆积。
- broker 还在接收，不代表 worker 有处理能力。
- worker 发出 ACK，只说明应用到达了自己选定的处理边界，不等于用户后来下载到了报表。

用户结果怎样定义成 SLI、发布后的故障怎样从这些信号走到根因，见[怎样用用户结果衡量一个服务](#59.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%94%A8%E6%88%B7%E7%BB%93%E6%9E%9C%E8%A1%A1%E9%87%8F%E4%B8%80%E4%B8%AA%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%B9%B6%E5%86%B3%E5%AE%9A%E8%BF%98%E8%83%BD%E4%B8%8D%E8%83%BD%E6%94%BE%E9%87%8F%EF%BC%9F)和[发布后用户结果变坏，怎样定位并确认恢复](#61.%20%E5%8F%91%E5%B8%83%E5%90%8E%E7%94%A8%E6%88%B7%E7%BB%93%E6%9E%9C%E5%8F%98%E5%9D%8F%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BB%8E%E4%BF%A1%E5%8F%B7%E8%B5%B0%E5%88%B0%E6%A0%B9%E5%9B%A0%E5%B9%B6%E7%A1%AE%E8%AE%A4%E6%81%A2%E5%A4%8D%EF%BC%9F)。

### 本章产出与下一步

到这里，三个事实各有其证据：受理看数据库提交，发布看本次 confirm 加路由核验，完成看一行加一次确认的成功提交；ACK 只在持久状态允许时发出，不同时刻的崩溃都有明确的落点。还没讲的是那些“不顺利”的分支：attempt 遇到可重试的错误、用户请求取消、worker 失联之后，谁来把 job 推到终态或下一轮，又怎样清理留下的对象？见[任务失败、被取消或 worker 失联后怎样收尾](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)。如果消息系统是 Kafka，分区顺序、偏移提交和再均衡的问题见支线[怎样用 Kafka 分区保序、推进偏移，并在再均衡后安全接手](#45.%20%E6%80%8E%E6%A0%B7%E7%94%A8%20Kafka%20%E5%88%86%E5%8C%BA%E4%BF%9D%E5%BA%8F%E3%80%81%E6%8E%A8%E8%BF%9B%E5%81%8F%E7%A7%BB%EF%BC%8C%E5%B9%B6%E5%9C%A8%E5%86%8D%E5%9D%87%E8%A1%A1%E5%90%8E%E5%AE%89%E5%85%A8%E6%8E%A5%E6%89%8B%EF%BC%9F)。

> [!info]- 来源
> - RabbitMQ 4.4（官方 Release Information 标为 2026-10-20 发布，核对于 2026-11-12）：[Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)，confirm 与 ACK 的方向、delivery tag 的 channel 范围、发布序号与 `multiple`、持久消息与 quorum queue 的确认时机、不可路由消息先 `basic.return` 后 confirm ACK、手动与自动确认、关闭 channel/connection 后未确认消息重新入队，以及 [Negative Acknowledgement and Requeuing](https://www.rabbitmq.com/docs/confirms#consumer-nacks-requeue)；[AMQP 0-9-1 extended specification](https://github.com/rabbitmq/amqp-0.9.1-spec/blob/main/xml/amqp0-9-1.extended.xml)，`basic.return` 不含 confirm 序号；[Java client unroutable handling](https://www.rabbitmq.com/client-libraries/java-api-guide#unroutable)；[Reliability Guide](https://www.rabbitmq.com/docs/reliability)，故障中途状态与重发；[Consumer Prefetch](https://www.rabbitmq.com/docs/consumer-prefetch)，per-consumer QoS、`0` 不限、可配置默认值、4.3 起 global QoS 弃用并默认关闭；[Consumers: Cancelling a consumer](https://www.rabbitmq.com/docs/consumers#cancelling-a-consumer-unsubscribing)，`basic.cancel` 不重排已发出的未确认投递；[Release Information](https://www.rabbitmq.com/release-information)。队列副本、持久性、exchange/binding/alternate exchange 与客户端 API 仍须按实际部署核实。
> - 三个事实的划分、job 状态与 ACK 的对照表、分段观测清单是本主线的应用合同与工程推论；job 状态机的权威定义在[上一章](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)。
## 45. 怎样用 Kafka 分区保序、推进偏移，并在再均衡后安全接手？

上一章的 broker (消息代理) 按“一条消息、一次投递、一次 ACK”工作，顺序和并行交给应用。Kafka 的模型不同：消息写进分区日志，消费者自己记住读到了哪里。本支线回答：Kafka 保证的是哪一种顺序；消费者怎样记录进度才不会跳过或漏掉记录；数据库写入和偏移提交之间崩溃会怎样；成员变化（再均衡）之后，旧消费者迟到的写入怎样被挡住；以及怎样用回放重建一份投影。机制部分对 Kafka 通用，版本相关的默认值集中在标注 Kafka 4.4 的说明里。

### 案例：报表 42 的状态事件流

这一章换一个更适合 Kafka 的例子，仍在报表服务里。服务为 `reportId = 42` 依次发布三条状态记录 `queued`、`rendered`、`ready`，每条带业务序号 `seq`（1、2、3）和稳定的 `event_id`。注意这三个词是投影里的展示状态，不是前几章的 job 状态机。

消费方有两个：

- 在线消费者把记录写进数据库里的 projection (投影)，也就是供查询的报表状态表；
- 值班时，另一个消费者把同一份投影重建到一张新表。

两者属于两个 consumer group (消费者组)：`G-live`（在线组）和 `G-rebuild`（重建组），各自维护自己的读取位置。文中的 offset (偏移量) 都是讲解用的位置，不是线上测量值。

先看端到端的边界：生产者用稳定的 key 把同一报表的记录送进同一个分区；分区只给出 broker 实际追加的顺序；每个消费者组独立读取并保存自己的位置；外部数据库写入是否完成，要由数据库自己的事务和业务序号判断，Kafka 的 offset 替不了数据库确认业务效果。

![同一分区由在线组与重建组各自读取，两组的位置互不影响](../../engineering-foundations/services/resources/partition-groups.svg)

### 分区保证哪种顺序？

topic (主题) 由多个 partition (分区) 组成。每个分区是一条只追加的日志，由分区 leader (主副本) 决定追加顺序；offset 标识记录在**这个分区内**的位置。不同分区之间没有全局次序。

本例固定 3 个分区，一个生产者按业务序号串行发送：

| 分区与 offset | key | 业务序号 | 记录 |
| --- | --- | ---: | --- |
| `report-events / P0 / 40` | `report-42` | 1 | `queued` |
| `report-events / P0 / 41` | `report-42` | 2 | `rendered` |
| `report-events / P0 / 42` | `report-42` | 3 | `ready` |
| `report-events / P2 / 18` | `report-17` | 1 | `queued` |
| `report-events / P2 / 19` | `report-17` | 2 | `ready` |

表末的 `report-17` 只用来对照另一个 key 的路由。offset 40–42 只是位置，业务序号 1–3 才是报表状态的因果顺序。Kafka 按 P0 的日志次序交付记录，但不判断哪个事件**应该**先发生。如果多个生产者并发发布同一个 key，broker 仍会形成某个追加顺序，却不保证它符合业务序号。所以业务顺序要由上游定义序号，消费者检查缺口或拒绝旧序号。

### key 怎样决定分区，扩分区为什么会打乱顺序？

默认分区器按 key 序列化后的字节选分区：分区数、序列化方式和分区策略都不变时，同一个 key 总落进同一个分区。

> [!info] Kafka 4.4 Java 生产者的默认路由（核对于 2026-11-13）
> 默认的 `BuiltInPartitioner` 对 key 的字节计算 `toPositive(murmur2(keyBytes)) % partitionCount`。前提：key 按 UTF-8 序列化，没有覆盖 `partitioner.class`，发送时没有显式指定分区，`partitioner.ignore.keys=false`（默认）。按 Kafka 4.4.0 的 `Utils.murmur2` 复算：`report-42` 的正值 hash 为 `1051128390`，模 3 得 0，进 P0；`report-17` 为 `417961679`，模 3 得 2，进 P2。换用自定义分区器、改变字节编码或忽略 key，都可能改变映射。

**扩分区会改变映射。** 其他条件不变，把分区数从 3 改成 4：`report-42` 的同一个 hash 变成 `1051128390 % 4 = 2`，从 P0 移到 P2；`report-17` 变成 `417961679 % 4 = 3`，从 P2 移到 P3。新旧分区的 offset 互不可比，无法据此推出 `report-42` 跨分区的先后。

如果变更分区数时必须保序，就要安排一个可验证的迁移边界：先暂停这个 key 的新发送，等旧分区里已发布的记录处理到约定的序号，再切换路由；消费者仍校验 `seq`，发现缺口就等待或修复。换一个自定义分区器，并不能让两个分区的日志获得全局顺序。

### 消费者组怎样分工？

在同一个传统消费者组里，每个分区在任一时刻只分配给组内一位成员。所以 3 个分区最多带来 3 路分区级并行；组里再加第四个消费者，它只会闲着，不会多出第四个分区。

不同的组各自从自己的位置读同一份日志：`G-rebuild` 读到哪里，不会移动 `G-live` 的 offset。

> [!info] Kafka 4.4 的 share group
> Kafka 4.4 另有 share group (共享组)，按单条记录分发，允许多个成员同时处理同一个分区的记录。它不提供分区内的有序处理；本章只讨论需要分区内有序的传统消费者组，两种模型不要混用。

### 生产者的确认与重试各证明什么？

`acks` 决定生产者等到哪一级复制完成才把发送视为成功。它不证明消费者已经处理，更不证明数据库里有了报表结果。

| 配置 | 成功的含义 | 仍要考虑的情况 |
| --- | --- | --- |
| `acks=0` | 不等 broker 响应 | 连 broker 收没收到都不知道，也就无从判断要不要重试 |
| `acks=1` | 分区 leader 已写入自己的日志 | leader 在复制给 follower (从副本) 之前故障，记录可能丢失 |
| `acks=all` | 当前 in-sync replicas (同步副本集，ISR) 全部确认 | 只等当前 ISR，不等 `replication.factor` 规定的全部副本；若持有已确认数据的副本全部永久丢失，确认本身救不回数据 |

副本故障后谁能接任 leader，还取决于集群配置：`replication.factor`、`min.insync.replicas`、是否启用 eligible leader replicas (合格主副本，ELR)，以及持有已提交记录的副本是否存活。不能只凭 `acks=all` 推断副本丢失后的结果。

> [!info] Kafka 4.4 的 ELR（核对于 2026-11-13）
> 新集群默认启用 ELR。ISR 小于 `min.insync.replicas` 时，高水位（消费者可读的已提交位置）不再前进，leader 选举会把 ELR 纳入候选。

**生产者幂等只管协议层的重试。** 生产者超时时，它不知道请求是在追加之前还是之后失去响应。producer idempotence (生产者幂等) 用生产者 ID 和每个分区上的批次序号，去掉**同一次发送**在客户端重试时产生的重复。若关闭幂等、又启用重试并允许同一连接上有多个未确认请求，较早的批次重试时，后发的批次可能先写入，顺序就乱了。即使幂等工作正常，它也分辨不了应用两次调用 `send` 是不是同一个业务事件：应用拿到不确定的结果后重新发布，仍要靠业务 `event_id` 去重，或先查是否已发布。

> [!info] Kafka 4.4 的生产者幂等默认值
> 没有冲突配置时默认开启幂等，它要求 `acks=all`、启用重试，且 `max.in.flight.requests.per.connection <= 5`。

### 数据库写入和偏移提交之间崩溃，会怎样？

这是后面所有规则的动机。设 `G-live` 要处理 P0 offset 40 的 `queued`：效果写进 PostgreSQL，消费进度存在 Kafka。两个系统之间没有一次性的原子提交，崩溃落在哪一边决定了结果：

| 崩溃时点 | 数据库里的状态 | 恢复起点 | 结果 |
| --- | --- | --- | --- |
| 数据库事务已提交，Kafka offset 尚未提交 | 事件 40 的效果已持久 | 仍从 40 开始 | 40 被重放；数据库要在同一本地事务里按 `event_id` 去重（inbox 或唯一键），或让下文的快照条件更新成为空操作 |
| Kafka 已提交 41，数据库事务还没提交 | 事件 40 的效果不存在 | 从 41 开始 | 40 不会再被交付，投影漏掉这次更新 |

所以写外部数据库的消费者通常**先提交数据库事务，再提交 offset**，接受“至少一次”处理和可能的重放，并关闭自动提交（`enable.auto.commit=false`），否则后台自动提交可能抢在数据库事务之前。数据库提交成功但响应丢了，就重新查 inbox 或投影，再安全地重放；Kafka offset 提交成功，也证明不了数据库已提交。无论两步谁先谁后，中间的崩溃窗口都消除不了，做不到“两边恰好各成功一次”。

### 提交的 offset 为什么是“下一个要读的位置”？

消费者有两个容易混淆的位置：

- `position` (当前位置)：这个消费者下一次要取的位置，每次 `poll()` 交付记录后就前进；
- committed offset (已提交偏移)：持久保存的位置，进程重启或分区重新分配后从这里恢复。

`poll()` 把记录交给应用，不代表数据库处理已完成；本地 `position` 也不能直接当成可以安全提交的进度。提交的值是**下一条要处理的记录的 offset**：处理完 40，提交 41，表示下次从 41 继续。

假如 40、41、42 都已交付，`position` 可能已经是 43；但只要异步 worker 还没处理完 40，安全的持久进度就仍是 40，即最早未完成的那条。提交得更靠后，崩溃恢复时就会跳过它。

![当前位置可以领先于最早未完成的记录；提交位置只越过连续完成的前缀](../../engineering-foundations/services/resources/offset-prefix.svg)

同一分区的记录若交给多个 worker 并行处理，就要按**交付顺序**维护“连续完成前缀”：从最早交付的记录数起，中间没有未完成记录的那一段。

- 41、42 已完成，40 仍在运行：可提交位置保持 40；等 40 完成，才推进到 43。
- 40、42 已完成，41 仍在运行：安全位置是 41。

worker 只把完成结果交回消费者线程。Java 的 `KafkaConsumer` 不是线程安全的，poll、分区分配、前缀状态和提交都应由同一个消费者线程负责。数据库事务提交成功、且消费者仍拥有 P0 时，只提交这一分区的安全位置：

```java
consumer.commitSync(Map.of(
    new TopicPartition("report-events", 0),
    new OffsetAndMetadata(41L)
));
```

不要用无参的 `commitSync()`：它提交的是最近一次 poll 之后的位置，可能是 43，而 40 还没写进数据库。分区一旦被收回，旧分配下迟到的完成通知也不能计入新分配的前缀。

### offset 有空洞时怎样推进？

offset 整数不一定连续：日志压缩会删掉同一 key 的旧记录；`read_committed` 隔离级别会隐藏已中止事务的记录；事务控制标记也占用 offset。假设应用实际只收到 40 和 42，41 不可见：完成 40 后，下一条要处理的可见记录就是 42，不必等不存在的 41；此时提交 41 只是给出一个稍早的扫描起点，读取时会自动越过空洞。

所以：看到 offset 有缺口，不能断定记录丢失；42 还没完成时，也不能把进度提交到它之后。

另外，`read_committed` 只读到 last stable offset (最后稳定偏移) 为止，也就是第一个尚未结束的事务之前，所以消费者可能暂时看不到日志末尾的记录。

### 并行写库时，顺序怎样守住？

连续完成前缀只约束**恢复位置**，不会让数据库写入自动按业务序号发生。并行 worker 若先写 `seq=2 rendered`、再写 `seq=1 queued`，投影就会倒退。按 `event_id` 去重只防同一事件重复生效，纠正不了不同事件之间的乱序。

如果投影保存的是**可以被更新的完整快照直接替换**的状态，可以用业务序号拒绝旧快照。本例先建好一行 `report_id = 42, last_seq = 0`（`last_seq` 不为空），每条记录都携带完整状态：

```sql
UPDATE report_projection
SET status = :status, last_seq = :seq
WHERE report_id = :report_id AND last_seq < :seq;
```

先应用 `seq=2 rendered`、再应用 `seq=3 ready` 之后，迟到的 `seq=1 queued` 只会更新零行，投影保持 `ready / 3`。这条旧快照已被更新的快照取代，所以这里的零行是一次**成功的空操作**；它完成后，offset 40 才算处理完，连续前缀才能前进。

这种写法**只适用于可以跳过中间状态的完整快照**。如果 `queued → rendered → ready` 每一步都有不可省略的副作用，就要按 `reportId` 顺序处理，或者要求 `seq = last_seq + 1`、把缺口留着等补齐，不能用 `last_seq < seq` 假装每步都执行过了。

### 再均衡怎样拒绝旧成员的提交？

成员加入、退出，或两次 poll 的间隔超过上限，都会触发 rebalance (再均衡)，重新分配分区。下面的时序使用 classic 组协议和整体撤销式（eager）分配器：消费者 C1 持有 P0，已提交位置是 40；C2 加入后，组的 generation (代次) 从 5 变为 6，P0 改分配给 C2。

| C1 的提交时机 | 提交结果 | C2 的起点 |
| --- | --- | --- |
| C1 停止派发，等 offset 40 的数据库事务确认成功，在代次 5 仍有效时提交 41 | 持久位置变为 41 | 从 41 开始 |
| 带旧代次 5 的提交请求在代次 6 生效后才到 | coordinator 拒绝：成员仍被识别时报 `ILLEGAL_GENERATION`，已被移出时先报 `UNKNOWN_MEMBER_ID`；持久位置仍是 40 | 从 40 重放 |

拒绝的依据是 C1 携带的成员 ID 或代次已过期，而不是“P0 已经归 C2”。所以应用仍应只提交**当前分配内**已完成的前缀。

**有序交接与异常交接。** 有序交接时会调用 `onPartitionsRevoked`：消费者线程停止派发，在有限时间内等待正在执行的数据库事务确认成功，再趁旧成员资格仍有效时提交已完成的连续前缀。异常情况下可能直接调用 `onPartitionsLost`：这时分区可能已归别人，C1 不再提交旧进度，只停止派发、丢弃旧分配的完成通知；C2 从最后一次成功保存的位置恢复，已写数据库但未提交 offset 的记录会被重放。交接时等待的时间也受成员存活和 poll 时限约束：等数据库等得太久，旧成员可能先失去分区，提交随之失败，留下需要重放的记录。

> [!info] Kafka 4.4 的组协议（核对于 2026-11-13）
> Java 消费者默认仍是 `group.protocol=classic`。classic coordinator 校验 group、member 和 generation 状态，不逐个检查提交的分区是否仍分配给该成员。新的消费者再均衡协议（KIP-848）从 Kafka 4.0 起正式可用，需设置 `group.protocol=consumer` 才启用；它按分区增量调整分配，用 member epoch 校验提交者，回调时机不能照搬 classic 的整组撤销时序。

### 组的栅栏为什么挡不住外部写入？

上面的代次校验是 Kafka 的 group fencing (组成员栅栏)，它是[栅栏原理](#%E6%A0%85%E6%A0%8F%EF%BC%9A%E6%80%8E%E6%A0%B7%E6%8C%A1%E4%BD%8F%E9%86%92%E6%9D%A5%E7%9A%84%E6%97%A7%20worker%EF%BC%9F)的一个实例：单调递增的代次，在提交处检查。但它只在 **offset 提交**这一处检查。C1 已经交给后台线程的工作，在分区被撤销时不会自动停止；它已经提交的数据库事务也不会被撤回；捕获 `CommitFailedException` 只说明 offset 提交失败，撤不回已提交的 SQL。

所以应用要在撤销时停止派发，等待或取消未完成的工作；只要旧任务仍可能迟到，就要让**目标数据库自己**再执行一道持久的所有权栅栏。下面是一个简化的 PostgreSQL 约定：每个 topic/partition 有唯一一条 owner row (所有权行)，保存当前所有者的 token；C2 先以旧 token 为条件把它改成新 token 并提交，然后才开始业务写入；C1 的每个写入事务都先锁住同一行、核对 token，再写投影，锁一直持有到提交。

```sql
-- C2：新所有者 token=6 先落库；必须恰好更新一行，提交后才能开始业务写入
BEGIN;
UPDATE partition_owners
SET owner_token = 6
WHERE topic = 'report-events' AND partition_id = 0 AND owner_token = 5;
COMMIT;

-- C1：所有权检查和投影写入在同一事务；FOR UPDATE 的锁保持到 COMMIT
BEGIN;
SELECT owner_token
FROM partition_owners
WHERE topic = 'report-events' AND partition_id = 0
FOR UPDATE;
-- 只有读到 owner_token = 5 才继续；否则 ROLLBACK 并丢弃旧任务
UPDATE report_projection
SET status = :status, last_seq = :seq
WHERE report_id = 42 AND last_seq < :seq;
COMMIT;
```

互斥靠的是 token 切换和投影写入都经过同一行的行锁：C1 先拿到锁，C2 的切换就要等 C1 提交；C2 已提交 token 6，C1 之后锁行就读到 6 并放弃。如果只用普通 `SELECT` 读 token、稍后再 `UPDATE`，即使两句在同一个 Read Committed 事务里，也得不到这种互斥。业务 `seq` 能拒绝旧快照，却不能证明当前写入者有权写；这道数据库栅栏与报表 job 的 attempt 和租约是两套独立的约定。

这张 owner 表只服务 `G-live` 的在线投影。同时运行的 `G-rebuild` 要用独立的 owner 表，或者把 `projection_id` 加进唯一键和每个所有权条件，否则两个合法的消费者组会互相夺走所有权。

### 回放能把投影重建到哪里？

重建从一份数据库初始快照开始，并和它对应的**每分区位置向量** `S[p]` 一起保存（`p` 表示分区）：快照恰好包含每个分区里所有 offset `< S[p]` 的效果，不含任何 `>= S[p]` 的效果；重建组从 `S` 开始读。之后另选一个切换边界 `T[p]`，在线投影和重建投影在这里对齐。`S` 是恢复起点，`T` 是切换点，两者不是同一个位置。

以 P0 为例：快照已包含 offset `< 40` 的效果、不含 `>= 40` 的，所以 `S[P0] = 40`。在线表和新表都处理仍可见的 40、41、42；选定 `T[P0] = 43` 后，两边都暂停应用 `>= 43` 的事件，确认各自写进数据库的连续前缀和已提交的 offset 都停在 43。此时两张表都应恰好等于“快照 + `[40, 43)` 中可见记录的效果”。核对一致后切到新表，由 `G-rebuild` 从 43 继续。`[40, 43)` 是单个分区内的半开 offset 区间；多分区时每个分区各有自己的 `S[p]` 和 `T[p]`，不能合成一个全局时间。对齐只要求所有可见记录都已应用，不要求 offset 整数连续。

几个前提：

- 两张表若都用 inbox 去重，去重键至少要包含 `(projection_id, event_id)`，或者给每张投影单独建 inbox。只按 `event_id` 全局唯一的话，在线组处理过的事件会让重建组误以为新表也处理过，从而跳过它。
- 每个分区的 `[S[p], T[p])` 必须仍完整可读，切换期间还要保留 `>= T[p]` 的事件。
- retention (保留) 和 compaction (压缩) 会删掉记录。要读的 offset 若已早于当前最早可读位置，`auto.offset.reset=earliest` 只会从**现在仍保留的最早记录**开始，找不回已删的记录；日志压缩只保留每个 key 的较新值，不保证留下全部历史转换。所需记录已被删掉时，停止切换，改从与快照匹配的历史来源恢复。要能从空白重建完整历史，主题就得按重建耗时和最慢的消费速度留足未压缩的记录，或者提供带匹配 offset 向量的快照。

### Kafka 事务能覆盖到哪里？

前面的崩溃窗口来自“数据库”和“Kafka”是两个系统。如果输出也写回 Kafka，Kafka 的 transaction (事务) 就能把输入分区的消费位置和输出 topic 的记录一起提交。典型的 Kafka→Kafka 流程：

- 每个并发的生产者实例使用唯一、且重启后沿用的 `transactional.id`。新实例启动时调用 `initTransactions()`：旧实例遗留的进行中事务会被中止；若旧事务已开始提交或中止，就等它结束；新的 producer epoch 会拒绝旧实例继续写入。这又是一处“单调代次 + 在提交处检查”。
- 输入 topic 含事务记录、且只应处理已提交的记录时，消费者设置 `isolation.level=read_committed`，以免把已中止的记录当成输入。
- 关闭自动提交，改由生产者调用 `sendOffsetsToTransaction(offsets, consumer.groupMetadata())`，把下一读取位置和当前组元数据加进同一个事务，不再另行手动提交这些 offset。

配置正确时，输出记录和输入消费位置会一起提交或一起中止；但这不保证“一次 poll 的所有分区输出同时可见”。事务中止后，组的已提交位置仍是旧值，输入可以重新处理；消费者内存里的 `position` 却不会自动倒回，应用要回到已提交的位置，例如调用 `seek`、重启消费者，或等组内重新分配。

**Kafka 事务管不到 PostgreSQL 的 `UPDATE`、对象存储写入或 HTTP 调用。** 若 `ready` 已写进 PostgreSQL，随后 Kafka 事务中止，数据库里的变更不会跟着回滚。从 Kafka 写往外部系统，仍要外部系统配合，二选一：

- 在数据库的同一个事务里写业务结果、inbox 和**数据库自己保存的**消费位置，恢复时从这个位置 `seek`；
- 先提交数据库效果、再提交 Kafka offset，并让业务写入在重放时保持幂等。

数据库 outbox 负责把已提交的数据库变更可靠地发布出去（见[耗时任务怎样被持久受理](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)），但它不推进 Kafka 消费者的读取位置。远端 API 则必须按稳定的操作键对重复请求做到业务幂等（见[远端副作用的决策表](#%E8%BF%9C%E7%AB%AF%E5%89%AF%E4%BD%9C%E7%94%A8%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%8F%AF%E4%BB%A5%E9%87%8D%E5%8F%91%EF%BC%9F)）。

### 本支线产出

用 Kafka 承接状态事件时，顺序只在分区内成立、由上游序号定义；进度按连续完成前缀提交，并且晚于数据库事务；空洞不等于丢失；完整快照可以用序号条件更新拒绝旧值；组代次只栅栏 offset 提交，外部写入要靠目标库的所有权行；重建靠快照与每分区位置向量对齐；Kafka 事务只覆盖 Kafka 自己。回到主线，不顺利的分支怎样收尾，见[任务失败、被取消或 worker 失联后怎样收尾](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)。

> [!info]- 来源
> 核对日期 2026-11-13。Apache Kafka 官方 Downloads 将 4.4.0 列为受支持版本，发布公告日期为 2026-10-22。案例中的事件、offset、分区数、崩溃点和完成顺序均为合成推演。
>
> - [Apache Kafka Downloads](https://kafka.apache.org/downloads/) 与 [4.4.0 发布公告](https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/)：受支持版本与发布日。
> - [Kafka 4.4 Design](https://kafka.apache.org/44/design/design/) 与 [Eligible Leader Replicas](https://kafka.apache.org/44/operations/eligible-leader-replicas/)：key 路由、分区内全序、传统消费者组的成员与位置、生产者可靠性、Kafka 事务与外部系统的边界、share group 与传统组的区别、复制与 ELR/min ISR。
> - [Producer Configs](https://kafka.apache.org/44/configuration/producer-configs/) 与 [KafkaProducer Javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html)：`acks`、默认幂等、重试与顺序、`transactional.id`、`sendOffsetsToTransaction`。
> - [KafkaConsumer Javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html)：position 与 committed position、offset 空洞、提交 next offset、失权时提交失败、非线程安全、撤销与丢失回调。
> - [Consumer Configs](https://kafka.apache.org/44/configuration/consumer-configs/) 与 [Consumer Rebalance Protocol](https://kafka.apache.org/44/operations/consumer-rebalance-protocol/)：`enable.auto.commit`、`read_committed`、`auto.offset.reset`、`max.poll.interval.ms`，`classic`/`consumer` 协议；4.4 Java 消费者默认 `classic`，新协议 4.0 起 GA、需显式选择。
> - [Kafka 4.4 Protocol](https://kafka.apache.org/44/design/protocol/) 与 [Topic Configs](https://kafka.apache.org/44/configuration/topic-configs/)：offset 提交的 generation/member epoch 字段，保留与压缩配置。扩分区引起的跨分区排序缺口是 key 哈希路由与多分区独立日志的推论；保序迁移步骤是应用侧合同。
> - [Kafka 4.4.0 BuiltInPartitioner](https://github.com/apache/kafka/blob/4.4.0/clients/src/main/java/org/apache/kafka/clients/producer/internals/BuiltInPartitioner.java)、[Utils.murmur2](https://github.com/apache/kafka/blob/4.4.0/clients/src/main/java/org/apache/kafka/common/utils/Utils.java)：hash 与分区计算；`report-42`、`report-17` 的 hash 与模 3、模 4 结果已按该算法重新复算。
> - [Kafka 4.4.0 ClassicGroup.validateOffsetCommit](https://github.com/apache/kafka/blob/4.4.0/group-coordinator/src/main/java/org/apache/kafka/coordinator/group/classic/ClassicGroup.java#L798-L874)：classic 提交只检查组状态、成员与代次。
> - [PostgreSQL 18, Read Committed](https://www.postgresql.org/docs/18/transaction-iso.html#XACT-READ-COMMITTED) 与 [Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html)：语句级快照、行锁持有到事务结束、等锁后返回更新后的行。owner row 的互斥流程是应用合同。
## 46. 任务失败、被取消或 worker 失联后，怎样收尾而不重复也不留孤儿？

前两章讲了顺利的路径：条件领取、fencing (栅栏)、成功提交、ACK。本章处理三类不顺利的情况，并回答它们共同的问题：由谁、按什么顺序把 job 推到终态或下一轮，怎样保证不重复执行，也不留下没人管的对象。三类情况是：attempt (执行尝试) 遇到可重试的错误；用户对 `/v1/jobs/job-demo-731` 发了 `DELETE`；worker 失联、租约到期。沿用主线四的导出案例和[持久受理一章](#job%20%E7%8A%B6%E6%80%81%E6%9C%BA%E4%B8%8E%20outbox%20%E5%90%84%E6%9C%89%E8%87%AA%E5%B7%B1%E7%9A%84%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F)的状态机：五个状态，`cancel_requested` 是标志，每个 job 最多 3 次 attempt（含首次）。

### 谁来决定 job 的下一步？

有三个角色可能改变一个已受理 job 的命运：

- **持有当前 attempt 的 worker**：遇到错误或看到取消请求时；
- **租约恢复器**：一个独立的进程，扫描租约已过期的 `running` job，取得竞争接管的资格；
- **API**：处理用户的取消请求。

它们之间没有消息往来，只通过同一行 job 竞争。每个角色的每次写入都带着它看到的状态和 attempt 作为条件，谁先提交谁说了算，后来者更新零行、重读再决定。这就是[领取与栅栏一章](#%E6%A0%85%E6%A0%8F%EF%BC%9A%E6%80%8E%E6%A0%B7%E6%8C%A1%E4%BD%8F%E9%86%92%E6%9D%A5%E7%9A%84%E6%97%A7%20worker%EF%BC%9F)的栅栏原理用在收尾上。

恢复器也需要最小权限：它只读扫描和竞争所需的 job 标识、状态、attempt、租约到期时间和取消标志，能做条件接管、预留等待槽、写恢复用的 outbox (事务发件箱) 意图或终态；它不读报表内容，也不直接向 broker (消息代理) 发布。网络、身份与数据权限的分层见[服务该跑在哪种运行时上](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)。

### 重试与恢复按什么顺序决定？

worker 遇到错误并停止当前工作之后，或者恢复器发现租约过期之后，都按**同一个顺序**判断，第一条成立就停下。取消优先于任何重试；入口处的代次核对不成立，说明别人已经做了决定。

~~~mermaid
flowchart TD
    W["worker 遇到错误<br/>并已停下当前工作"] --> L
    R["恢复器发现租约过期<br/>（按 clock_timestamp()）"] --> L
    L{{"锁住 job 行：仍是 running，<br/>attempt 仍是我看到的那一代？"}}
    L -- 否 --> N["什么都不写<br/>重读，按新状态<br/>处理手上的消息"]
    L -- 是 --> C{{"cancel_requested？"}}
    C -- 是 --> CX["① cancelled<br/>同时提交对象<br/>清理或保留决定<br/>不占等待槽"]
    C -- 否 --> P{{"永久错误，或<br/>attempt ≥ max_attempts？"}}
    P -- 是 --> F1["② failed<br/>对应错误码或<br/>attempts_exhausted<br/>不占槽、不写 outbox"]
    P -- 否 --> S{{"能预留到等待槽？<br/>（240 个未满）"}}
    S -- 否 --> F2["③ failed<br/>capacity_exhausted<br/>不占槽、不写 outbox"]
    S -- 是 --> Q["④ queued<br/>新 available_at = 退避到期<br/>清除旧租约<br/>占一个等待槽<br/>新 pending outbox 意图"]
~~~

四个落点都要等事务提交成功之后，才可以 ACK 旧投递。

重排分支 ④ 的事务如下（入口处已在同一事务里 `SELECT ... FOR UPDATE` 锁住 job 行并完成前面的判断）：

~~~sql
-- 占一个等待槽；返回零行说明 240 个槽已满，改走 capacity_exhausted
UPDATE admission_budget
SET waiting_count = waiting_count + 1
WHERE pipeline = 'report-export' AND waiting_count < 240
RETURNING waiting_count;

UPDATE report_jobs
SET status = 'queued',
    available_at = clock_timestamp() + :backoff,
    lease_expires_at = NULL,
    holds_waiting_slot = true
WHERE job_id = :job_id AND status = 'running' AND attempt = :observed_attempt;

INSERT INTO report_outbox(job_id, state) VALUES (:job_id, 'pending');
COMMIT;
~~~

`:backoff` 用带上限的指数退避加全抖动计算，公式和参数含义见[重试要等多久、最多试几次](#%E9%87%8D%E8%AF%95%E8%A6%81%E7%AD%89%E5%A4%9A%E4%B9%85%E3%80%81%E6%9C%80%E5%A4%9A%E8%AF%95%E5%87%A0%E6%AC%A1%EF%BC%9F)。重排只占等待槽，不消耗新 job 的速率令牌：令牌限制的是新逻辑 job 的到达速度，重排不是新 job。等待槽怎样计数见[容量章](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)。

④ 提交之后旧投递可以 ACK，因为新的可执行时间、槽位和唤醒意图都已持久，新一轮有了自己的唤醒。relay (中继) 按 `available_at` 到期再发布新意图；如果旧消息或别的重复消息提前到达，领取条件 `available_at <= clock_timestamp()` 会拦住它。只有到期唤醒已持久安排好，早到的重复消息才可以被确认。

沿图走三个例子：attempt 1 遇到暂时错误，走 ④，attempt 2 成功，job 最终 `succeeded`；attempt 1、2、3 依次失败或失联，第三次之后走 ②，不再预留第四次；attempt 1 失联时 240 个槽恰好占满，恢复器走 ③，这是一个可以查询的持久终态，而不是靠 broker 无限重投把压力变成看不见的积压。

“最多 3 次”限制的是**启动**次数，不保证旧 attempt 立刻停下。被栅栏的 attempt 仍可能占着资源运行一段时间；限制这种重叠持续多久的，是每页读取和上传的 deadline 以及可观察的停止路径。

这套顺序还有一个活性前提：relay、broker、worker、数据库在故障之后最终会恢复并取得进展，租约扫描持续在跑。任何一个组件长期不可用，job 都无法推进；已排队的 job 继续占着等待槽，槽满之后 API 在受理前拒绝新 job。

### 为什么重试不能靠把消息退回队列？

最直接的“重试”做法，是处理失败时把当前投递退回 broker（例如 RabbitMQ 的 `nack(requeue=true)`），指望它再来一次就变成下一次 attempt。这行不通：

- job 仍是 `running`，下一次投递到来时，条件领取要求 `status = 'queued'`，会拒绝它；
- 快速退回、快速重投，会形成热循环，把 broker 和 worker 一起拖慢；
- 它绕过了上一节的全部判断：不检查取消，不累计 attempt，不占等待槽，没有退避。

正确的做法就是上一节的持久重排：先在数据库里决定并提交下一步，再 ACK 旧投递。其他几种错误的处置：

- **不可重试的业务错误**：以 job 仍是自己这一代的 `running` 且未请求取消为条件，提交 `failed` 和有限错误码，然后 ACK。如果条件不成立（取消已被请求，或别的转移先提交了），重读 job，走对应的分支。
- **格式错误、或对应不到有效 job 的消息**：不能无限重排，隔离到配置好的 dead-letter queue (死信队列)，或走会触发告警的拒绝路径。

退回投递只适合一种情况：worker 手上有一条**还没开始处理**的预取投递，要把它还给 broker（见[prefetch 一节](#prefetch%20%E9%99%90%E5%88%B6%E7%9A%84%E6%98%AF%E4%BB%80%E4%B9%88%EF%BC%9F)）。

### 恢复器先提交时会走哪条分支？

租约到期之后，恢复器和原 worker 可能同时动作。如果原 worker 的成功事务先提交，job 就是 `succeeded`，恢复器锁行后读到的已不是 `running`，走上图的“否”分支，什么都不做。如果恢复器先提交，`job-demo-731` 落进上图 ①–④ 之一。

走 ④ 之后，新的 worker B 领取 attempt 2；A 若再醒来提交 attempt 1 的结果，会因状态或 attempt 不匹配而更新零行（时序见领取与栅栏一章）。恢复器不需要“杀死” A，也做不到：它只改变 A 能写进数据库的东西。

### 取消和领取同时发生，谁赢？

用户的 `DELETE /v1/jobs/job-demo-731` 表达的是“请求停止”。服务怎样处理，取决于 job 此刻处于哪个状态，以及取消和领取谁先提交。规则如下：

- **job 还是 `queued`。** API 用一个条件事务把它改成 `cancelled`，提交对象的清理或保留决定（之前的 attempt 可能已上传过对象），并**只归还一次**它占着的等待槽。此后无论有多少条唤醒消息到达，worker 只会读到终态，不会领取、也不会增加 attempt。
- **领取先提交了。** 等待槽已在领取时归还，API 不能再还一次。它只能对 `running` 的 job 写 `cancel_requested = true`，返回的表示里状态仍是 `running`，带 `cancelRequested: true`。
- **取消先提交了。** worker 的领取条件 `status = 'queued'` 不再成立，更新零行。

两种写入落在同一行上，由行锁和提交顺序选出唯一的胜者。API 的处理可以写成两条条件语句，按顺序尝试：

~~~sql
-- 1. queued 分支：取消并归还等待槽（同一语句，两处修改要么都生效要么都不生效）
WITH cancelled AS (
  UPDATE report_jobs
  SET status = 'cancelled', terminal_at = clock_timestamp(), holds_waiting_slot = false
  WHERE job_id = :job_id AND status = 'queued'
  RETURNING job_id
), released AS (
  UPDATE admission_budget
  SET waiting_count = waiting_count - 1
  WHERE pipeline = 'report-export' AND EXISTS (SELECT 1 FROM cancelled)
)
SELECT count(*) FROM cancelled;

-- 2. 上一条零行时：job 可能已被领取，只能登记取消请求
UPDATE report_jobs
SET cancel_requested = true
WHERE job_id = :job_id AND status = 'running';
~~~

两条都零行，说明 job 已经是终态（或在两条语句之间又被重排回 `queued`）：重读一次，已终态就原样返回当前状态，不改写；若又回到 `queued`，再走第 1 条。

**运行中的取消由谁落终态？** 持有当前 attempt 的 worker 在每个有限的工作步骤之间、以及成功提交之前检查取消标志。看到 `cancel_requested = true`，就以 job ID、`status = 'running'`、自己的 attempt 和取消标志为条件提交 `cancelled` 及清理或保留决定。它不归还等待槽（领取时已经还过），只在停止执行后释放自己的物理执行槽。

**worker 在提交取消之前失联了。** 取消请求留在数据库里，租约到期后由恢复器代写 `cancelled` 和同样的清理决定（决策图的 ①）。恢复器不会为了取消去抢等待槽。在这个决定持久化之前，旧投递不能 ACK：`cancel_requested` 只是请求，不是终态，也不是确认许可。

**取消和成功同时发生。** 仍由提交顺序决定唯一终态。取消标志先写入，成功提交的条件 `cancel_requested = false` 不成立，更新零行，worker 转去提交取消；成功先提交，取消端读到 `succeeded`，返回现有的成功状态，不改写终态。

### 什么能证明旧 attempt 已经停下？

下面这些事件**都不**证明旧 attempt 已经停止：

- 用户请求了取消；
- 进程收到了停止信号；
- 租约到期；
- 数据库已经栅栏了旧 attempt。

它们只改变“旧 attempt 能写进数据库什么”，不改变旧 attempt 的进程是否还在读数据、上传对象、占着连接。物理执行槽要等这个 attempt 真正停止、释放了它的连接、游标和上传句柄之后才归还；同一个 worker 进程可以继续运行别的 attempt，不必整个退出。“取消只是请求，完成信号只证明本层”这条原则见[一份工作该交给进程、线程还是异步 I/O](#14.%20%E4%B8%80%E4%BB%BD%E5%B7%A5%E4%BD%9C%E8%AF%A5%E4%BA%A4%E7%BB%99%E8%BF%9B%E7%A8%8B%E3%80%81%E7%BA%BF%E7%A8%8B%E8%BF%98%E6%98%AF%E5%BC%82%E6%AD%A5%20I/O%EF%BC%9F)；进程关停时怎样停止领取、不确认未完成的投递，见[服务进程收到停止信号后怎样排空工作](#21.%20%E6%9C%8D%E5%8A%A1%E8%BF%9B%E7%A8%8B%E6%94%B6%E5%88%B0%E5%81%9C%E6%AD%A2%E4%BF%A1%E5%8F%B7%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%8E%92%E7%A9%BA%E5%B7%A5%E4%BD%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%80%80%E5%87%BA%EF%BC%9F)。

### 孤儿对象什么时候才能删？

对象存储不在数据库事务里。上传成功、数据库提交却失败（或更新零行），就会留下一个没有任何已提交 job 引用的对象，即孤儿。为了让孤儿可以安全识别和删除，先约定两件事：

- **对象键按 attempt 区分，且不可覆盖。** 例如 `reports/job-demo-731/attempt-1.csv` 与 `attempt-2.csv`。A 迟到的上传只会写到自己的键上，不会替换 B 的结果，也不会被用户下载。
- **逐个键检查引用，而不是看 job 有没有结果。** B 的键已经成为 job 的结果，A 的键仍是需要清理的孤儿；“job 已有结果”不能推出“这个 job 的所有对象都在用”。

真正难的是**什么时候删**。清理的计时起点，是数据库提交“该 attempt 已不是当前 attempt”（栅栏）或 job 终态的时刻，而不是租约到期的时刻。然后分三种情况：

| 运行环境能保证什么 | 清理方式 |
| --- | --- |
| 旧 attempt 在栅栏之后不会再发起新的上传，且栅栏生效时已在进行的上传有最长耗时上限 | 等过这个上限、对象存储的传播余量和安全宽限，再做一次清扫 |
| 停顿的旧进程仍可能在栅栏之后才开始上传 | 单次扫描不够。先撤销旧进程的写入权限或等它过期，再从它最后可能开始上传的时刻起，等过最长上传时间和宽限，做最终清扫 |
| 写入权限没有失效时间 | 持续重扫候选键 |

无论哪种情况，**每次删除之前都要重新确认**这个键没有被任何已提交的结果引用。还有一个例外：成功提交的 `COMMIT` 结果未知时，对象的结局未决，不能当孤儿删。

当前 attempt 确认停止、和异步回收孤儿是两项独立的责任。回收由独立的清理任务做，不需要为它继续占着 worker 的执行槽。

> [!info] 实例：S3 的条件写
> Amazon S3 支持带 `If-None-Match: *` 的条件写，同名对象已存在时拒绝写入，可以作为“按 attempt 区分的键不可覆盖”的存储侧保险。它只认对象名，不知道谁是当前 attempt，替代不了数据库栅栏；换别的对象存储时，按它自己的条件写语义设计。（核对于 2026-11-12）

### 本章产出与下一步

现在每条不顺利的分支都有确定的落点：可重试的失败按“attempt → 取消 → 永久错误或上限 → 等待槽”的顺序持久重排或终结；取消和领取由同一行上的条件写选出唯一胜者，等待槽只还一次；栅栏和租约都不证明旧 attempt 已停，物理槽跟着实际停止归还；孤儿对象按引用和写入时限分情况回收。

这些分支反复用到同一个资源：等待槽。重排要占槽，槽满就 `capacity_exhausted`，受理时槽满就在 202 之前拒绝。那么一条异步管线到底该有多少槽、多少执行槽、多快的准入速率？见[一条异步管线能接多少工作，超出时在哪里拒绝](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)。

> [!info]- 来源
> - 手动确认下未确认投递在 channel/connection 关闭后重新入队、自动确认在发出时视为已交付、`basic.nack`/`basic.reject` 的 `requeue`：[RabbitMQ 4.4, Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)，核对于 2026-11-12；这些是 RabbitMQ 的行为，其他 broker 须按自身契约核实。
> - Read Committed 下行锁与并发条件更新的重检：[PostgreSQL 18, Transaction Isolation §13.2.1](https://www.postgresql.org/docs/18/transaction-iso.html)、[Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html)，核对于 2026-11-12。本章的重排与取消 SQL 在 PostgreSQL 14.25 本地实跑。
> - S3 条件写：[Amazon S3, Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html)，核对于 2026-11-12。
> - 重试决策顺序、取消竞争规则、孤儿清理条件是本主线的应用合同；3 次上限、240 个等待槽为本例取值，不是框架默认。
## 47. 一条异步管线能接多少工作，超出时在哪里拒绝？

前几章让 `job-demo-731` 在受理、领取、重试和取消时都有确定的落点，但都默认资源够用。本章回答资源不够时怎么办：这条导出管线能同时承诺、执行多少工作；每一道上限由谁计数、在哪里检查；超出时为什么必须在返回 202 **之前**拒绝。主线四的合成负载只在本章算一次，其他章只引用结论。

### 容量是几道门槛，不是一个队列长度

“系统能接多少”不是一个数字。导出路径上有几道各管一件事的门槛，任何一道都可能最先到顶：

下图沿导出路径标出每道门槛的位置、本例取值、计数什么和何时归还；取值的推导在后文各节。图中的 attempt (执行尝试) 是 job 的一次实际运行，物理执行槽按它计数。

![导出路径上的门槛：受理事务里的令牌桶（7 个每秒、突发 30，不足回 429）和等待槽（240，满回 503）都在 202 之前拒绝；outbox 到 broker 不额外占槽；worker 进程有 64 个物理执行槽；受理事务和 worker 共用数据库连接（上限 200、预算 240）；结果写入对象存储](../../engineering-foundations/services/resources/capacity-admission-gates.svg)

加长队列只能改变工作**在哪里**等，不能让下游处理得更快。下面先讲拒绝发生在哪里，再逐道算数。

本章使用的合成输入如下。它们是为演算设定的教学值，不是生产测量，也不是推荐值：

| 输入 | 取值 |
| --- | ---: |
| 新 job 的平均 / 十分钟峰值到达率 | 5 / 20 个每秒 |
| 请求正文 | 8 KiB |
| 每个 attempt 的平均耗时（含生成与上传） | 6 s |
| worker 部署 | 4 副本 × 2 进程 × 8 个执行槽 |
| 每份报表的顺序读取 | 12 次，每次借连接 20 ms |
| 受理事务借用连接 | 10 ms |
| 平均结果对象 / 每个 job 的元数据 | 128 KiB / 2 KiB |
| 结果保留 / 终态后 job 与幂等元数据保留 | 7 天 / 14 天 |
| 准入：速率 / 突发 / 等待槽 | 7 个每秒 / 30 / 240（下文推导） |

### 准入、背压与拒绝怎样对应到响应？

admission control (准入控制) 决定新的逻辑 job 能不能进入系统；backpressure (背压) 把“下游已满”的信号传回上游，让上游减速、延后或停止提交。进程内的流可以靠暂停读取把背压传回源头；而服务端没法让一个 HTTP 调用方“慢一点”。对调用方来说，背压只能表现为**拒绝**，而且必须在返回 202 之前明确拒绝。先承诺受理、之后再悄悄丢掉，正是这几章一直在避免的事。

本例的映射：

| 情况 | 响应 | 是否留下 job |
| --- | --- | --- |
| 速率令牌不足 | `429 Too Many Requests`，可带 `Retry-After` | 不留 |
| 等待槽已满 | `503 Service Unavailable`，可带 `Retry-After` | 不留 |
| 同键同指纹的重放 | 返回原 job 的当前状态 | 不新增；不耗令牌、不占槽 |

两种拒绝都发生在受理事务回滚之后，数据库里什么都不留。它们是**受理边界**上的拒绝，不能伪装成“已受理的 job 失败了”。只有已经受理的 job 在重排时拿不到槽，才落成可查询的 `failed / capacity_exhausted`（见[收尾一章](#46.%20%E4%BB%BB%E5%8A%A1%E5%A4%B1%E8%B4%A5%E3%80%81%E8%A2%AB%E5%8F%96%E6%B6%88%E6%88%96%20worker%20%E5%A4%B1%E8%81%94%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%94%B6%E5%B0%BE%E8%80%8C%E4%B8%8D%E9%87%8D%E5%A4%8D%E4%B9%9F%E4%B8%8D%E7%95%99%E5%AD%A4%E5%84%BF%EF%BC%9F)）；worker 本地物理槽不足只会推迟领取，不会把 `queued` 的 job 判为容量失败。令牌和槽同时不足时先报 `429`；准入拒绝排在认证、可见性、正文校验和幂等裁决之后，完整顺序见[多个错误同时成立时先报哪个](#%E5%A4%9A%E4%B8%AA%E9%94%99%E8%AF%AF%E5%90%8C%E6%97%B6%E6%88%90%E7%AB%8B%E6%97%B6%E5%85%88%E6%8A%A5%E5%93%AA%E4%B8%AA)。

调用方收到 `Retry-After` 后，应在自己的 deadline (截止时间) 内按提示等待，再用**同一个**幂等键重放，规则见[写请求超时后怎样安全重试](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。重放不耗令牌，但每次 HTTP 往返仍要消耗 API 的认证、网络和解析资源。

请求内流式响应不走这套规则：它能持续发送多久，由请求自己的 deadline、连接和流背压决定，不应把等待槽的算式套过去。

### 受理事务怎样在多个副本之间仲裁？

受理事务（见[持久受理一章](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)）分两步仲裁，分别挡住两种并发：

**第一步：这是不是一个新意图？** 插入带唯一约束的 job 身份。同键并发时，失败方回滚后读胜者：同指纹返回原 job，异指纹报冲突。这一步只解决“同一个键来了两次”。

**第二步：还有没有额度？** 只有第一步确认是新意图，才去竞争一条**整条管线共用**的额度行。“先查重、再扣额度”挡不住另一种并发：两个**不同**的键同时抢最后一个等待槽。它们各自读到“还剩 1 个”，都接受，槽就超了。所以额度必须是所有 API 副本、所有账户共享的一行，并在同一个事务里原子地检查和扣减：

~~~sql
-- 先锁行；拿到锁之后再取时间，避免用等锁之前的时间补令牌
SELECT tokens, refilled_at, waiting_count
FROM admission_budget
WHERE pipeline = 'report-export'
FOR UPDATE;

SELECT clock_timestamp() AS checked_at;
-- 应用计算：available = min(30, tokens + 7 × (checked_at − refilled_at))
-- available < 1 → 回滚，429；waiting_count >= 240 → 回滚，503

UPDATE admission_budget
SET tokens = :available - 1,
    refilled_at = :checked_at,
    waiting_count = waiting_count + 1
WHERE pipeline = 'report-export';
-- 随后在同一事务里补齐 job 参数、写 outbox，一起提交
~~~

两个不同的键争最后一个槽时，会在这一行的锁上排队：先提交者占槽，后者拿到锁后看到 `waiting_count = 240`，回滚自己的临时 job 身份，返回 503。令牌、计数、job 和 outbox 一起提交或一起回滚。

**为什么不能让每个进程各自限流？** 本地限流器的总放行量会按进程数放大。用一个独立的小例子说明（这里换成按账户计的读取额度，因为导出案例的数字太大，不便手算）：某账户的额度是突发 8 点、每秒补 4 点。如果三个 API 进程各自维护一份这样的本地桶，一秒内三份桶合计可以放行 `3 × (8 + 4 × 1) = 36` 点，而策略本意是一秒最多 `8 + 4 = 12` 点。20 个单点请求同一时刻按 7、7、6 分到三个进程，每份本地桶都放得下这一批，于是整个服务瞬间放行 20 个，而一份共享桶此刻只会放行 8 个。要守住全局上限，就需要共享计数，或者把总额度切成总和不超过上限的分片预算。共享计数会带来网络延迟和对计数服务可用性的依赖，选择前要说清可以接受多大误差。

两条补充：

- 每账户、每主体的限流可以叠加在全局额度之上，用来保证公平，但不能代替全局额度：后者保护的是数据库和 worker 的总容量。
- 如果额度放在数据库之外的限流服务里，数据库事务回滚时不会替它退回令牌。那就要另设可以幂等确认或补偿的预留协议，不能假设回滚会自动还额度。

### 等待槽什么时候占、什么时候还？

等待槽记的是“已受理、尚未被领取的逻辑排队轮次”，全管线共 240 个：

- **受理时占一个**，与 job 和 outbox 同一事务。
- **消息从 outbox (事务发件箱) 进入 broker (消息代理)，不变。** 同一轮排队不管此刻在 outbox 里还是在 broker 里，都只占一个槽；同一 job 的重复消息不额外占槽。
- **领取提交时归还**，与改成 `running` 同一事务。
- **`queued` 状态被取消时归还一次**，与写终态同一事务。
- **重试或恢复重排时重新占一个**；拿不到就 `failed / capacity_exhausted`。

所以 broker 队列很浅，不能说明系统空闲：outbox 里还没发布的 `queued` job 同样占着槽。

![共享等待槽在领取提交时归还；物理执行槽要等 attempt 停止并释放资源才归还，worker 进程可以复用](../../engineering-foundations/services/resources/capacity-slot-ownership.svg)

图中两种槽的量纲和所有者都不同。物理执行槽属于 worker 进程，先占槽、再条件领取、领取失败立即归还；它要等 attempt 真正停止才还，被栅栏的旧 attempt 仍占着它。两次 attempt 若因租约恢复而短暂重叠，就要分别占两个物理槽。物理槽的完整规则见[怎样保证一个任务同一时刻只由一个 worker 推进](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)。

### Little 定律能算什么、不能算什么？

Little 定律给出稳定系统的长期平均关系：

~~~text
L = λ × W
平均系统内工作数 = 平均有效到达率 × 平均在系统内停留时间
~~~

三个量必须属于**同一个边界、同一种工作**：

- 边界只包括 worker 的执行，`W` 就是平均 attempt 时长；边界包括排队，`W` 也要包括等待时间。
- `λ` 是这个边界**实际接纳**的平均速率，不是包含被拒请求的原始 HTTP 请求速率。
- 它是长期稳态下有限均值之间的关系。到达率持续超过服务能力、队列一直增长时，系统没有稳态，不能用它推出一个有限的等待量。

例如一个稳定的服务平均接纳 40 个请求每秒，每个请求平均停留 0.2 s，服务内平均有 `40 × 0.2 = 8` 个在途请求。

它**不能**预测突发峰值，不能给出等待时间的 p95、p99，也不能单独证明某个容量上限是安全的。到达的成批性、服务时间的长尾、重试、拒绝策略和下游瓶颈，都要另外分析。观察排队边界时，queue depth (队列深度) 说明有多少工作在等，queue age (队列年龄，即最老工作等了多久) 说明等了多久，两者揭示的是不同的故障。

### 要多少执行槽，准入速率该定多少？

用 Little 定律把到达率换成并发需求。先假设每个新 job 只运行一次 6 秒的 attempt，重试、租约重叠和下载另计：

- **平均负载：** `5 × 6 = 30` 个 attempt 同时在执行。
- **峰值负载：** 要稳定跟上 20 个每秒，需要 `20 × 6 = 120` 个并发 attempt。这是规划需求，不是当前系统做得到的量。
- **当前容量：** `4 × 2 × 8 = 64` 个物理执行槽。即使 64 个槽一刻不停，按 6 秒平均服务时间算，理想服务率也只有 `64 ÷ 6 ≈ 10.67` 个 attempt 每秒。这是忽略调度空隙和一切额外工作的上界，不是压测吞吐。所以这套部署撑不住持续 20 个每秒：要么等待无限增长，要么新 job 被拒绝。队列只能暂存超出能力的工作，不能消除持续过载。

**准入目标。** 规划时假设平均利用率不超过 70%：`64 × 0.70 ÷ 6 ≈ 7.47` 个 attempt 每秒，于是把新 job 的准入速率定为 **7 个每秒**。若每个 job 平均只跑一次 attempt，平均占 `7 × 6 = 42` 个槽，即 `42 ÷ 64 ≈ 65.6%`。反过来算重试预算：70% 的规划相当于每秒 `64 × 0.70 = 44.8` 槽秒，分给每秒 7 个新 job，每个 job 平均最多能用 `44.8 ÷ (7 × 6) ≈ 1.067` 次 6 秒的 attempt。也就是说，按这个准入速率，平均每 15 个 job 里大约只能容纳一次重试。70% 和 7 个每秒是等待负载测试验证的起点；重试、租约重叠、长尾耗时和运维任务都会改变实际服务率。

### 令牌桶允许多少，四种限额各管什么？

token bucket (令牌桶) 是常用的限速算法：桶里最多存 `b` 枚令牌（burst，突发），以速率 `r` 匀速补充；每个请求按成本取走令牌，不够就拒绝或等待。`b` 决定能吸收多大的瞬时突发，`r` 决定长期平均速率。桶满时，长度为 `T` 的任意窗口内最多供给：

~~~text
r × T + b
~~~

本例把它用作“每个新逻辑 job 一枚令牌”：`r = 7` 个每秒，`b = 30`。请求成本也可以不相等，例如一次长范围汇总扣 4 点、一次短读取扣 1 点，同样 8 点的突发只能放行 2 个长汇总。这个上界只限制**放行**多少，不保证下游能及时**完成**同样多的工作。

**峰值时会拒绝多少？** 设十分钟内所有账户合计以每秒 20 个新幂等键提交，共 `20 × 600 = 12,000` 个新意图。桶开始时满（30 枚），此后每秒补 7 枚，十分钟最多放行 `7 × 600 + 30 = 4,230` 个。即使等待槽从不先满，也至少有 `12,000 − 4,230 = 7,770` 个在受理前被拒。实际上，worker 故障或重排会让 240 个槽更早占满。

**240 个等待槽不等于最长等 30 秒。** 设开始时没有积压、桶是满的、worker 连续 30 秒没有领取任何 job、也没有重排：这 30 秒里桶最多放进 `30 + 7 × 30 = 240` 个新 job，恰好填满等待槽；之后即使还有令牌，也只能拒绝，直到有槽释放。可见等待槽数限制的是**承诺了多少尚未领取的工作**，不直接规定队列能等多久。已有积压或重排会让它更早占满。容量应该按业务能接受的排队时长目标和实测的服务、恢复速度来校准；queue age 持续上升时，要降低准入速率或直接拒绝。

几种控制看起来相似，管的却是不同的资源，不能互相代替：

| 控制 | 管住什么 | 管不住什么 |
| --- | --- | --- |
| rate limit (速率限制)：令牌补充速率 | 新工作的长期平均到达速度 | 下游能否及时完成 |
| 突发容量：桶深 | 短时成批提交 | 不提供无限的等待区 |
| quota (配额)，本例未设 | 较长周期（如每天、每月）的总量 | 某一时刻的并发 |
| concurrency limit (并发上限)：物理执行槽 | 同时运行的 attempt 与实时资源 | 排队和 outbox 积压 |
| 有界队列：等待槽 | 已受理、尚未开始的工作量 | 正在执行的 attempt 占用的资源 |

这些门槛同时生效。流量远超容量或遭到攻击时，每一层还能挡住什么，见支线[流量远超容量或遭到攻击时，每一层能挡住什么](#48.%20%E6%B5%81%E9%87%8F%E8%BF%9C%E8%B6%85%E5%AE%B9%E9%87%8F%E6%88%96%E9%81%AD%E5%88%B0%E6%94%BB%E5%87%BB%E6%97%B6%EF%BC%8C%E6%AF%8F%E4%B8%80%E5%B1%82%E8%83%BD%E6%8C%A1%E4%BD%8F%E4%BB%80%E4%B9%88%EF%BC%9F)。

### 数据库连接预算够不够？

连接是另一份共享预算。连接池在进程内，每多一个进程就多一份上限，所以总预算是“副本数 × 进程数 × 每进程池上限”之和（公式和池耗尽的诊断见[ORM 会话怎样借用连接，连接池为什么会耗尽](#28.%20ORM%20%E4%BC%9A%E8%AF%9D%E6%80%8E%E6%A0%B7%E5%80%9F%E7%94%A8%E8%BF%9E%E6%8E%A5%EF%BC%8C%E8%BF%9E%E6%8E%A5%E6%B1%A0%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E8%80%97%E5%B0%BD%EF%BC%9F)）。本例 API 和 worker 各 4 副本 × 2 进程，每进程池上限 `8 + 2 = 10`：

| 连接使用者 | 计算 | 上限 |
| --- | ---: | ---: |
| API | `4 × 2 × 10` | 80 |
| worker | `4 × 2 × 10` | 80 |
| 其他共用这个库的服务（本例预留） | — | 40 |
| 应用配置上限合计 | `80 + 80 + 40` | 200 |
| 数据库连接预算（本例假设） | — | 240 |
| 余量 | `240 − 200` | 40 |

这是池**可以同时借出**的上限，不代表数据库此刻有 200 条活跃查询。relay (中继)、租约恢复器、迁移工具和运维连接若不在那 40 个预留里，要从剩下的 40 里单独列出。扩容 worker 副本会同时增加执行槽和连接上限；平台的自动扩缩容也不会替数据库增加连接容量。

平均借用量同样可以用 Little 定律估算，按各自边界的**实际**速率相加：

~~~text
平均借用连接数 = 0.24 × λ_attempt + 0.010 × λ_受理
                 （每个 attempt 读 12 次 × 20 ms = 0.24 连接秒；每次受理 0.010 连接秒）
~~~

- 稳定处理 5 个每秒、每个一次 attempt：`5 × 0.24 + 5 × 0.010 = 1.25` 条。
- 达到规划的 7 个每秒：`7 × 0.24 + 7 × 0.010 = 1.75` 条。
- 若扩容到能稳定处理 20 个每秒：读取约 `4.8` 条、受理约 `0.2` 条，共 5 条。当前 64 个槽达不到这个速率，所以这是扩容后的需求，不是现在的实际借用量。

这些估算都不含长事务、慢查询、池等待，以及上传期间误持连接这类问题。平均借用量很低，并不说明单个进程的池不会排队：并发尖峰时，每进程 10 条的上限仍可能先到顶。

### 请求字节和结果存储会涨到多少？

**入口正文。** 平均 `5 × 8 KiB = 40 KiB/s`；峰值 `20 × 8 KiB = 160 KiB/s`，十分钟累计 `20 × 600 × 8 KiB = 96,000 KiB = 93.75 MiB`。这是按**到达的 HTTP 请求**算的，不是按受理的 job：读完正文才拒绝的请求、重放和同键冲突都消耗网络和解析资源；如果在读正文之前就拒绝，实际流量会更低。这里没算 HTTP 头、TLS、重传和响应字节。

**结果对象。** 长期每秒 5 个 job 成功、每份 128 KiB、保留 7 天（604,800 s）：

~~~text
128 KiB × 5 个/s × 604,800 s ÷ 1,048,576 KiB/GiB = 369.140625 GiB ≈ 369 GiB
~~~

**job 与幂等元数据。** 按每秒 5 个 job 进入终态（成功、失败或取消都算）、每个 2 KiB、终态后保留 14 天（1,209,600 s）：

~~~text
2 KiB × 5 个/s × 1,209,600 s ÷ 1,048,576 KiB/GiB ≈ 11.54 GiB
~~~

2 KiB 已经包括每个 job 的一条记录（状态原地更新为终态）和它的幂等元数据，失败的 job 已在“每秒 5 个终态”里，不要再重复加一次。这两项都不含副本、索引、版本、压缩差异和删除延迟；若另存 attempt 历史或诊断事件，还要加上它们和清理滞后。

**写入速率。** 每秒 7 份都成功，结果写入约 `7 × 128 KiB = 896 KiB/s = 0.875 MiB/s`；30 个突发全部成功写入 `30 × 128 KiB = 3.75 MiB`；64 槽的理想完成率 10.67 个每秒对应约 `10.67 × 128 KiB ≈ 1.33 MiB/s`。这些是理想完成量，不是观测值。下载是另一份读取负载，要单独估算，不能和生成带宽混算。

### 怎样确认最先到顶的是哪一道？

估算只告诉你哪项预算可能先紧，最先到顶的瓶颈要靠分阶段加压找出来。用有代表性的请求大小、12 页读取和结果体量逐步加压，再分别跑这些场景：20 个每秒持续十分钟、30 个突发、240 槽占满、慢查询、对象上传变慢、重试、worker 丢失、租约重叠。每个场景按阶段记录受理、排队、执行、下载的时延 p50/p95/p99（6 秒只是假设的平均 attempt 时长，不是 p95 目标），并对照上文的门槛图和下表读信号：

| 门槛 | 到顶时最先看到的信号 | 常见误读 |
| --- | --- | --- |
| 准入速率 / 突发 | 429 增多；令牌放行率贴近 7 个每秒 | 把 429 当成服务故障，而它正是设计好的拒绝 |
| 等待槽 | 503 增多；槽占用贴近 240；最老 `queued` job 与最老 `pending` outbox 年龄上升 | broker 深度低就以为没有积压 |
| 物理执行槽 | 活跃槽贴近 64；被栅栏但仍存活的 attempt；领取延迟上升 | 调大 prefetch 能提高并行度 |
| 数据库连接 | 池 checkout 等待上升；SQL 时长上升 | 平均借用量低就以为池不会耗尽 |
| 数据库本身 | 处理器、I/O、锁等待上升 | 只看连接数 |
| 对象存储 | 上传时延与错误；对象体量增长 | 上传慢被当成 worker 慢 |
| 重试 | attempt 数 / 新 job 数明显大于 1.067 | 只看新 job 速率，忽略重试吃掉的槽秒 |

如果 broker 深度在下降，而数据库里最老 `queued` job 的年龄继续上升，工作只是换了一个地方堆积。最后按用户实际的服务目标决定调整准入速率、资源还是查询计划，而不是只把队列加长。

### 本章产出与下一步

导出管线现在有一套写明了口径的上限：准入 7 个每秒、突发 30、等待槽 240、执行槽 64、应用连接上限 200；超出时在 202 之前以 429 或 503 拒绝，不留 job；已受理 job 的重排拿不到槽才落成可查询的容量失败。流量远超这些上限、甚至是攻击时，各层还能做什么，见本章支线[流量远超容量或遭到攻击时，每一层能挡住什么](#48.%20%E6%B5%81%E9%87%8F%E8%BF%9C%E8%B6%85%E5%AE%B9%E9%87%8F%E6%88%96%E9%81%AD%E5%88%B0%E6%94%BB%E5%87%BB%E6%97%B6%EF%BC%8C%E6%AF%8F%E4%B8%80%E5%B1%82%E8%83%BD%E6%8C%A1%E4%BD%8F%E4%BB%80%E4%B9%88%EF%BC%9F)。

主线四到此结束。它交给主线五的是：每个请求、job 和 attempt 都有稳定身份和可查的持久状态，信号各自只证明自己那一段交接。主线五从[怎样判断一个抽象值不值得引入？](#49.%20%E6%80%8E%E6%A0%B7%E5%88%A4%E6%96%AD%E4%B8%80%E4%B8%AA%E6%8A%BD%E8%B1%A1%E5%80%BC%E4%B8%8D%E5%80%BC%E5%BE%97%E5%BC%95%E5%85%A5%EF%BC%9F)开始，讲一次改动怎样从设计走到生产；到度量和放量时，这些身份就是 SLI 的计数单位（见[怎样用用户结果衡量一个服务](#59.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%94%A8%E6%88%B7%E7%BB%93%E6%9E%9C%E8%A1%A1%E9%87%8F%E4%B8%80%E4%B8%AA%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%B9%B6%E5%86%B3%E5%AE%9A%E8%BF%98%E8%83%BD%E4%B8%8D%E8%83%BD%E6%94%BE%E9%87%8F%EF%BC%9F)）。

> [!info]- 来源
> - Little 定律及其有限均值、稳态条件：[Little, “A Proof for the Queuing Formula: L = λW,” Operations Research 9(3), 1961](https://pubsonline.informs.org/doi/abs/10.1287/opre.9.3.383)，DOI `10.1287/opre.9.3.383`，核对于 2026-11-12。本章只把它用于单位一致的均值演算。
> - 令牌桶在窗口 `T` 内的供给上界 `rT + b`：[IETF RFC 2216 §2](https://datatracker.ietf.org/doc/html/rfc2216#section-2)；[IETF RFC 1363](https://www.rfc-editor.org/rfc/rfc1363.html)，Token Bucket Rate / Size，1992-09。RFC 描述的是数据流量上界，本章改作“每个新逻辑 job 一枚令牌”的准入模型。
> - `429 Too Many Requests` 与 `Retry-After`：[IETF RFC 6585 §4](https://datatracker.ietf.org/doc/html/rfc6585#section-4)；`503 Service Unavailable`：[IETF RFC 9110 §15.6.4](https://datatracker.ietf.org/doc/html/rfc9110#section-15.6.4)；`202 Accepted`：[RFC 9110 §15.3.3](https://datatracker.ietf.org/doc/html/rfc9110#section-15.3.3)。令牌不足映射为 429、等待槽满映射为 503 是本例 API 的状态映射。
> - 持续过载时队列会增加等待并占用资源：[Google SRE Book, Addressing Cascading Failures — Queue Management](https://sre.google/sre-book/addressing-cascading-failures/#queue-management)；按配额拒绝多余工作：[Handling Overload](https://sre.google/sre-book/handling-overload/)，2016，核对于 2026-11-12。240 这个数不来自这些来源。
> - 服务目标与用户可见可靠性：[Google SRE Workbook, Implementing SLOs](https://sre.google/workbook/implementing-slos/)，核对于 2026-11-12；70% 利用率与分阶段压测方案是本例的工程假设。
> - 共享额度行的并发语义：[PostgreSQL 18, Read Committed](https://www.postgresql.org/docs/18/transaction-iso.html#XACT-READ-COMMITTED)，并发更新等待已锁行后在新版本上重检；同键新意图的唯一裁决：[Index Uniqueness Checks](https://www.postgresql.org/docs/18/index-unique-checks.html)。不能提供等效唯一裁决与行锁的数据库不能照搬这个额度行设计。
> - `QueuePool` 每进程最多 `pool_size + max_overflow`：[SQLAlchemy 2.1, Connection Pooling](https://docs.sqlalchemy.org/en/21/core/pooling.html)，核对于 2026-11-12；公式的权威讲解在 data 主线。
> - 本地桶按进程数放大的 `3 × (8 + 4) = 36` 是合成小例；所有负载、预算、保留期与对象大小均为教学设定，百分比与容量运算已按这些假设复算。
## 48. 流量远超容量或遭到攻击时，每一层能挡住什么？

上一章的准入、限额和等待槽假设请求都能到达 API，而且调用方大体守规矩。本章看另一种情况：denial of service (DoS，拒绝服务) 用流量、连接或昂贵请求耗尽服务资源，让正常请求得不到响应；distributed denial-of-service (DDoS，分布式拒绝服务) 由许多来源同时施压。要回答的是：过载发生在哪一层，那一层能做什么；限额键和检查顺序怎样随请求经过的阶段变化；缓解措施何时可以撤掉。令牌桶、四种限额和 429/503 的权威讲解在[上一章](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)，本章只用它们的结论。

能否缓解，取决于两件事：哪项资源先到上限，以及攻击流量到达了哪一层。如果上游链路已经被塞满，应用里的限流代码根本收不到请求。

### 案例：报表读取接口遭到洪泛

沿用主线四的报表服务，这次看读取接口。`user-17` 可以读 `acct-17` 的报表 42。读取有两种成本（“工作点”是本例的相对成本单位，不等于处理器秒或查询数）：

- `GET /v1/accounts/acct-17/reports/42?days=7`：短范围读取，1 点；
- `GET /v1/accounts/acct-17/reports/42?days=365`：长范围汇总，4 点。

正常路径是：ISP (互联网服务提供商) → 接入链路 → 边缘代理（可组合 CDN 与 WAF，即 Web 应用防火墙）→ 报表 API → 数据库。上游 scrubbing (清洗，把攻击流量滤掉后再转发) 不是默认路径：只有应急时 ISP 才把流量改路到清洗服务。本例的合成取值如下，只供推演，没有对真实服务做过负载测试：

| 取值 | 数值 |
| --- | ---: |
| 接入链路容量 | 1 Gbit/s |
| API 全局工作预算：突发 / 持续 | 80 点 / 40 点每秒 |
| 长范围汇总：最多同时运行 / 最多等待 | 12 个 / 6 个 |

![请求经过的层次、各层可观察的信号和可执行的减压位置](../../engineering-foundations/services/resources/web-availability-and-ddos-protection-boundaries.svg)

### 过载发生在哪一层，就在哪一层减压

先把链路利用率、边缘请求、API 工作量和数据库等待放在**同一条时间线**上，再选择那一层能执行的动作。只看到“流量升高”或“客户端失败”，判断不了请求是否已到达应用，也证明不了某个来源地址就是攻击者。

| 阶段与同时观察到的信号 | 解释与处理 |
| --- | --- |
| **平常。** 链路约 300 Mbit/s（30%）；边缘约 200 个请求每秒，其中进入报表 API 的短读取约 20 个每秒，即约 20 点每秒；API 与数据库等待平稳 | 这是本例的基线。200 个每秒是边缘总量，不是报表 API 的工作量；20 点每秒低于 40 点每秒的全局预算。按链路、边缘、路由和数据库资源分层保存时间序列 |
| **网络洪泛。** 清洗尚未启用，ISP 在其入口测到约 1.4 Gbit/s；接入接口遥测显示占用 100%、丢包上升；外部探针失败；API 请求数和数据库负载**没有**相应上升 | 1.4 Gbit/s 是清洗前在 ISP 侧观测的值，不是接入接口的实际吞吐，接口饱和要由接口遥测另行证实。按预案通知 ISP 或托管商启用清洗并改路；应用限额和扩容碰不到没到达应用的流量 |
| **应用洪泛。** 清洗与改路已生效；接入接口约 620 Mbit/s（62%），丢包回落，独立探针能到达边缘。工作预算和运行/等待上限启用前，边缘把每秒 250 个长范围汇总转给 API，它们来自多个已认证、且通过报表授权的主体；数据库连接等待上升 | 链路有了余量，过载转移到应用和依赖。每个 4 点，入站工作约 `250 × 4 = 1,000` 点每秒，是 40 点每秒全局预算的 25 倍。在昂贵查询之前执行工作预算，并分别限制运行数与等待数 |
| **降载之后。** 链路和 API 错误下降；数据库等待、并发占用和队列年龄逐步回落；合法探针恢复 | 不因为一次成功响应就撤掉规则，按本章最后一节的证据分步撤销 |

这些观测是合成输入，不是抓包、日志或压测结果。实际要和服务自身的基线、区域、路由和资源上限对照；合法突发也可能产生很高的请求数，攻击源还可能分散或伪装。把各层指标和**外部用户探针**一起看，才能区分三种情况：流量没到 API；请求到了但成本太高；依赖已经在排队。

### 各层的控制能力与盲区

每种防护只能作用于它**实际收到**的流量：

| 层 | 能看到、能做什么 | 做不到什么 |
| --- | --- | --- |
| ISP、托管商、上游网络 | 链路比特率、包率、丢包和路由状态；预先约定的清洗、按协议封禁、改路 | 上游没提供清洗或改路时，源站救不回已被塞满的接入链路；清洗也要避免把合法用户一起丢掉 |
| 边缘代理、CDN、WAF | 连接数、加密握手、请求大小、解析耗时、HTTP 路由；限制头部和正文大小与超时，挡已识别的模式，缓存适合共享的公开表示 | NAT 让许多合法用户共用一个地址，分布式来源能绕开单地址阈值；规则看不到业务授权和查询成本；请求若能直连源站，就绕过了边缘 |
| API 与业务逻辑 | 已认证主体、账户、路由、输入范围、估算成本、响应时延；按作用域限额，先授权再估成本，在昂贵查询前限制并发 | 只按请求数计费，会把一次廉价读取和一次长汇总算成同样的工作；范围选错或额度过低会误伤正常用户 |
| 数据库、缓存、worker、队列 | 活跃连接与池等待、处理器使用率、队列长度与最老任务年龄；限制查询、并发、等待队列、执行时长和返回量 | 无界地加长队列只会把过载推迟，最后耗尽内存、连接或存储，并拉长恢复时间；应用降级也撤不回已被占满的上游网络 |

关于边缘层，有三点要单独说明：

- WAF 适合在它能看到请求的地方挡掉已知的恶意模式或异常频率。它不是账户授权器，也未必认得出“格式合法、却会触发昂贵查询”的请求。各家边缘服务能检查的请求部分和超限时的行为不同，要明确配置超限时的规则，不能假设它检查了完整请求。
- CDN 能吸收部分请求，在边缘返回重复的**公开**内容。账户私有的报表不能作为未隔离的共享缓存对象返回（缓存规则见[一份 HTTP 响应什么时候可以直接复用](#34.%20%E4%B8%80%E4%BB%BD%20HTTP%20%E5%93%8D%E5%BA%94%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%8F%AF%E4%BB%A5%E7%9B%B4%E6%8E%A5%E5%A4%8D%E7%94%A8%EF%BC%8C%E4%BB%80%E4%B9%88%E6%97%B6%E5%80%99%E5%BF%85%E9%A1%BB%E5%9B%9E%E6%BA%90%E7%A1%AE%E8%AE%A4%EF%BC%9F)）。
- 如果架构依赖 CDN 作为唯一入口，源站就要只接受可信边缘转发的请求，否则攻击者可以绕过 CDN 直达源站。

> [!info] 实例：AWS WAF 的超限请求组件（核对于 2026-11-13）
> AWS WAF 可以按请求组件的大小匹配并阻止超限内容，但正文能检查多少字节取决于前置的 AWS 服务；批量检查全部头部另有字节数和头部数量的上限，单个头部的检查不受这组批量上限限制。允许超限内容通过时，WAF 未必检查了完整组件。这是 AWS 的配置行为，不是所有边缘服务的统一规则。

### 来源地址能信多少？

应用在代理后面看到的 `Forwarded` 或 `X-Forwarded-For` 字段，不能直接当成可信的客户端身份。转发链上的任何节点，包括客户端自己，都可能修改这些字段。只有确认直连来源是可信代理，并由代理重写或正确维护这些字段之后，才可以据此使用来源地址。

即便地址可信，它也不适合做唯一的限额键：NAT 让多个合法用户共用一个地址，僵尸网络又能把来源分散开。来源地址适合做早期信号，或作为限额的维度之一。

### 检查顺序和限额键随请求阶段变化

一个请求越往里走，服务知道的信息越多，能用的限额键也越精确；越靠后的检查也越贵。所以按这个顺序做：

1. **先做廉价检查：** 连接数、正文大小、语法。这时还不知道主体是谁，只能按连接、网段和廉价端点的策略限制。
2. **再认证和授权：** 确认主体和它对 `acct-17` 的权限。之后才能组合主体、账户、路由和估算成本作为限额键。
3. **再估算这个已验证请求的成本：** `days=365` 是 4 点。
4. **最后，在昂贵查询之前申请预算和执行位置。**

几条不能做的事：不要信任客户端自报的账户、权重或任意转发头；不要把登录失败锁定做成攻击者可以远程触发的封禁（攻击者故意输错密码就能锁住别人的账户）；也不要指望图形人机验证（CAPTCHA）：它能给某些易被滥用的功能增加一点摩擦，却挡不住塞满链路的流量，也代替不了大小、连接、速率和工作量上限。

**原子地申请预算和位置。** 长汇总的主队列只存已通过身份和资源授权、已扣过账户与全局工作预算、正在等运行位置的请求。受理时要原子地确认两级预算都够，并预留**一个运行位或一个等待位**：运行位有空就立即运行；12 个运行位已满但 6 个等待位还有空，就入队。只有预算不足，或运行位和等待位都没有空，才快速拒绝；不要求两种位置同时有空。

这样位置可能比令牌先成为约束。所有位置都空、各主体额度充足时，80 点的突发预算理论上能支付 `80 ÷ 4 = 20` 个长汇总，但 12 个运行位加 6 个等待位最多只收 18 个，共扣 `18 × 4 = 72` 点。持有 18 个也不代表它们都能及时完成。

**全局预算决定稳态上限。** 每主体的额度保证公平，全服务的工作预算保护数据库的总容量，两者叠加使用。回到应用洪泛阶段：即使 40 点每秒的全局补充全部分给长汇总，稳态下也最多接受 `40 ÷ 4 = 10` 个每秒，而到达的是 250 个每秒。其他业务还要分预算，实际上限更低；突发额度只能让拒绝晚一点发生。

### 拒绝时怎样回应，客户端怎样配合？

单个主体超出额度时，API 可以返回 `429 Too Many Requests` 并用 `Retry-After` 告诉它何时再试；服务整体暂时无法处理时返回 `503 Service Unavailable`，同样可以带 `Retry-After`。状态码只表示这一次响应的结果，不会清空排队的工作，也不保证之后一定可用。

攻击期间还有一个特殊之处：为每个请求都生成一个 429 响应，本身也消耗资源。服务不必对每个请求都这样回应，可以直接丢弃连接。

客户端要尊重等待提示和自己的 deadline (截止时间)，用有上限、带抖动的指数退避，避免许多客户端在同一秒重试形成第二波流量，并且只让一层重试（理由和公式见[写请求超时后怎样安全重试](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)）。会启动异步导出的写请求，容量不足时在 202 之前拒绝，规则同上一章。

**负载削减。** load shedding (负载削减) 是停止接纳暂时无法处理的新工作，先保住仍能可靠提供的路径。本例可以暂停 365 天汇总，把容量留给短范围读取；产品允许的话，也可以从**按账户隔离、经过授权**的缓存提供带时效说明的旧快照。不能为了“快速响应”从共享 CDN 返回别的账户的报表：读缓存仍要走正确的身份和授权边界。单靠 WAF 规则、验证码或 CDN，无法保证 API 和数据库会恢复。

### 什么时候可以撤掉缓解措施？

以下证据**同时**改善后，才逐步撤掉临时规则：

1. **上游。** ISP 或托管商确认清洗路由已生效；清洗后的接入接口低于 1 Gbit/s，丢包回落，来自独立网络的探针能稳定到达边缘。仅凭清洗后的 620 Mbit/s 判断不了原始洪泛是否已结束：停用清洗或改回原路由之前，还要看 ISP 侧清洗前的流量和提供商对安全回切的判断，切换过程中继续观察丢包。
2. **边缘。** 边缘请求数和回源率回落；“源站拒绝非可信代理直连”的检查通过；公开静态资源的缓存命中上升时，没有把私有报表放进共享缓存。
3. **API 与依赖。** 长汇总并发不超过 12、等待不超过 6，且等待年龄在下降；数据库池等待和查询时延回到基线附近。缓解期间限额拒绝可能先上升，所以要同时看合法用户成功率、被拒工作和依赖负载，不能只看 API 错误数下降。
4. **授权与限额探针。** 用 `user-17` 读 `acct-17` 的短范围报表，核对内容正确；用与 `acct-17` 无成员关系的 `user-29` 重复探测，仍按 API 合同得到与不存在的报表相同的 404（见[服务怎样逐次确认主体能做这个动作](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)）；耗尽单个主体的令牌后，应得到限额响应，而不是继续启动重查询。
5. **长查询。** 若曾暂停 365 天汇总，先给 `user-17` 放开一次合法的长汇总，核验结果、查询耗时、数据库等待、并发和队列；稳定后再逐步恢复正常准入。短读取正常不能证明长查询已恢复。
6. **客户端。** 收到 `Retry-After` 的客户端确实等待了；临时限制分步放宽时，重复同一组短读、长汇总和无权探针，观察合法成功率、拒绝率、链路和数据库信号。任何一项回退，就恢复刚放宽的策略并重新定位瓶颈。常驻的工作预算和并发、等待上限按实测容量保留。

应急结束后，记录开始和结束时刻、受影响的路由、各层信号、提供商和边缘动作、拒绝与误伤情况、恢复探针的结果，再据此调整常驻额度和预案。事后复盘的通用流程见[发布后用户结果变坏，怎样定位并确认恢复](#61.%20%E5%8F%91%E5%B8%83%E5%90%8E%E7%94%A8%E6%88%B7%E7%BB%93%E6%9E%9C%E5%8F%98%E5%9D%8F%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BB%8E%E4%BF%A1%E5%8F%B7%E8%B5%B0%E5%88%B0%E6%A0%B9%E5%9B%A0%E5%B9%B6%E7%A1%AE%E8%AE%A4%E6%81%A2%E5%A4%8D%EF%BC%9F)。

### 本支线产出

面对远超容量的流量，先在同一条时间线上判断饱和发生在哪一层：链路满了找上游清洗，应用和依赖满了就在昂贵查询之前按主体、账户和成本限额，并分别限制运行数与等待数；来源地址和转发头只作信号；拒绝时 429、503 或直接丢连接；撤销缓解要多层证据同时改善。常驻的准入、等待槽和连接预算仍按[上一章](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)的口径保留；这些用户结果怎样进入 SLI 与发布门禁，见[怎样用用户结果衡量一个服务](#59.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%94%A8%E6%88%B7%E7%BB%93%E6%9E%9C%E8%A1%A1%E9%87%8F%E4%B8%80%E4%B8%AA%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%B9%B6%E5%86%B3%E5%AE%9A%E8%BF%98%E8%83%BD%E4%B8%8D%E8%83%BD%E6%94%BE%E9%87%8F%EF%BC%9F)。主线四到此结束，主线五从[怎样判断一个抽象值不值得引入？](#49.%20%E6%80%8E%E6%A0%B7%E5%88%A4%E6%96%AD%E4%B8%80%E4%B8%AA%E6%8A%BD%E8%B1%A1%E5%80%BC%E4%B8%8D%E5%80%BC%E5%BE%97%E5%BC%95%E5%85%A5%EF%BC%9F)开始。

> [!info]- 来源
> - DoS/DDoS 的多层攻击面、资源密集型输入、限速、ISP 与过滤服务的边界、CAPTCHA 不能防 DoS：[OWASP Denial of Service Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html)，Fundamentals、Analyzing DoS attack surfaces、Application attacks、Input validation、Rate limiting、ISP-Level remediations、Global-Level remediations，核对于 2026-11-13。
> - 流量基线、攻击指标、联系 ISP/托管商、上游过滤与 CDN、事后分析：[CISA、FBI、MS-ISAC, Understanding and Responding to Distributed Denial-of-Service Attacks](https://www.cisa.gov/sites/default/files/2024-03/understanding-and-responding-to-distributed-denial-of-service-attacks_508c.pdf)，2024-03，What Steps Before、How to Know、How to Respond、After an Attack，核对于 2026-11-13。
> - `429` 与攻击期间不必对每个请求都生成 `429`：[IETF RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html)，§4、§7.2，2012-04；`503` 与 `Retry-After`：[IETF RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)，§10.2.3、§15.6.4，2022-06。
> - 过载时拒绝多余工作、按关键程度保护路径、连接负载：[Google SRE Book, Handling Overload](https://sre.google/sre-book/handling-overload/)，Customer Quotas and Throttling、Criticality、Load from Connections，O’Reilly 2016；随机指数退避与避免多层重试放大：[Addressing Cascading Failures — Retries](https://sre.google/sre-book/addressing-cascading-failures/#retries)。
> - CDN 只应是实际请求路径的入口，源站要防绕过：[AWS Best Practices for DDoS Resiliency, Protecting your origin (BP1, BP5)](https://docs.aws.amazon.com/whitepapers/latest/aws-best-practices-ddos-resiliency/protecting-your-origin-bp1-bp5.html)，核对于 2026-11-13；所列 CloudFront 与 VPC origin 配置是 AWS 的实现例。
> - 超限请求组件的检查范围：[AWS WAF, Oversize web request components](https://docs.aws.amazon.com/waf/latest/developerguide/waf-oversize-request-components.html)，核对于 2026-11-13。
> - 私有响应不得在共享缓存间复用：[IETF RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html)，§5.2.2.7，2022-06。
> - 转发地址字段可被链上节点或客户端修改：[IETF RFC 7239](https://www.rfc-editor.org/rfc/rfc7239.html)，§8.1，2014-06；可信代理配置示例：[nginx ngx_http_realip_module](https://nginx.org/en/docs/http/ngx_http_realip_module.html)，`set_real_ip_from` 与 `real_ip_header`，核对于 2026-11-13。
> - 令牌桶 `burst + rate × T` 的供给上界：[IETF RFC 1363](https://www.rfc-editor.org/rfc/rfc1363.html)，1992-09；权威讲解在容量章。
## 49. 怎样判断一个抽象值不值得引入？

本章回答：面对一条新需求，怎样判断该加一个接口、注册表或分层，还是直接改几行分支。答案是先看这次变化会传播到哪些代码，只有当一个抽象能缩小这种传播、而且收益大于维护新边界的成本时才引入它。SOLID、DRY、YAGNI 这些原则都是预测传播的工具，本章按“变化来了先看哪里”的顺序使用它们，而不是逐条背诵。

**案例。** 从[下一章](#52.%20%E6%80%8E%E6%A0%B7%E6%8A%8A%E4%B8%80%E4%BB%BD%E7%BC%BA%E9%99%B7%E6%8A%A5%E5%91%8A%E5%8F%98%E6%88%90%E5%8F%AF%E8%AF%81%E4%BC%AA%E7%9A%84%E5%8F%8D%E4%BE%8B%EF%BC%8C%E5%B9%B6%E7%94%A8%E8%AF%81%E6%8D%AE%E5%AE%A1%E6%9F%A5%E4%BF%AE%E5%A4%8D%EF%BC%9F)起，主线五跟随报表服务的一次修复发布，从缺陷一直走到生产。判断抽象却需要一个会反复增加类型的代码库，修一个读取缺陷的场景不合适，所以本章和两条支线改用一个合成的页面编辑器作独立案例。编辑器里有标题（`heading`）和按钮（`button`）两种节点，负责校验节点配置、在画布上预览、保存草稿和发布。页面当前公开的是 revision (修订) r16：分组 `section-1` 下依次是按钮 `button-1` 和标题 `heading-1`（这个状态怎样从 r12 编辑而来，见[页面编辑器的数据模型](#51.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)）。

新需求是增加图片节点（`image`），并规定**发布时**每张图片的 alt text (替代文本) 必须非空。编辑者还没填写时，`alt` 存为空字符串，草稿照样可以预览和保存。预期结果是：

- 插入 `image-1`、`alt` 为空，得到草稿 r17：可预览、可保存，发布 r17 被拒绝，访客仍看到 r16。
- 补上 `alt: '页面结构图'`，得到 r18：发布通过，访客看到 r18。

“所有图片都要非空 alt”是本例的产品约定。真实产品要区分用途：装饰图或与邻近文字重复的图片应使用空 `alt`。另假设现有存储格式已能保存任意 `type` 与 `props`，不必改存储契约。

### 一次需求会改到哪些地方？

在只支持标题和按钮的版本里，节点类型散落在五个入口：工具栏和粘贴创建节点时填默认属性；保存前检查草稿结构；画布按类型渲染预览；保存时遍历文档；发布门禁检查能否公开。代码按 `switch (node.type)` 分支，新增 `image` 就要在其中至少四处各加一个分支。

判断要不要引入抽象，先回答三个问题：

1. 这条需求实际要改哪些代码？
2. 这次改动会不会迫使不相关的调用者、规则或发布单元跟着改？
3. 新边界能不能缩小这种传播？缩小的部分是否大于维护这个边界的成本？

后面几节是这三个问题在不同位置的回答：职责按谁提出变化来划分，扩展点留给反复出现的变化，接口按调用者需要来切，重复要看是不是同一份知识。

### 按变化来源划分职责：草稿合法与可发布是两道检查

**Single Responsibility Principle (单一职责原则，SRP)** 并不要求一个类只有一个方法。Robert C. Martin 的表述是“一个模块只应有一个变化的理由”，而“理由”对应提出需求的那一方。编辑器里至少有三个来源：

- 编辑器本身定义草稿结构：`alt` 必须是字符串。
- 产品或合规方定义发布规则：发布时 `alt` 非空。
- 设计系统定义视觉呈现：图片的圆角和阴影。

如果把它们绑在一起，一方的变化就会打断另一方的工作。画布渲染函数若也检查发布用的非空 `alt`，未填完的草稿就无法预览；保存入口若复用发布门禁，草稿就无法保存。把“草稿结构检查与预览”和“发布前的完整性检查”分开，视觉样式改动也不会影响草稿能否编辑。分开之后，案例里的两个修订走出不同结果：

| 修订 | 草稿检查 | 预览与保存 | 发布该修订 |
| --- | --- | --- | --- |
| r17：`image-1` 的 `alt: ''` | 通过，字段类型完整 | 画布生成 `<img alt="">` 描述符；文档所有者保存 r17 | 发布门禁拒绝；公开版仍是 r16 |
| r18：`alt: '页面结构图'` | 通过 | 预览新属性；保存 r18 | 发布门禁接受；公开版切到 r18 |

发布失败只拒绝了这一次发布请求，不撤销已保存的 r17。浏览器里的即时提示只帮编辑者早发现问题；服务端收到发布请求时，仍要按服务端保存的那个修订重新检查，因为客户端检查可以被绕过。

反过来，也不能因为类里出现两个名词就机械拆分。若只有一个简单的预览函数，校验和生成视图总是因同一条规则一起变化，把它拆成几个接口和文件只会拉长追踪路径。拆分的依据是证据：这次变更由谁提出，哪条保证要同步修改，哪些调用者只依赖其中一部分。

### 变化点反复出现时，用注册表收拢分支

**Open/Closed Principle (开闭原则，OCP)** 的目标是：一个相对稳定的模块可以沿已知变化点扩展，而不必改动核心。它不要求代码永不修改，也不能让没预料到的需求自动适配。

如果“新增一种节点类型”已经反复发生，可以把每种类型的行为登记在一个受约束的注册表里。每项登记三种行为：`validateDraft`（草稿检查）、`render`（预览）和 `validatePublish`（发布检查）。入口只按 `type` 取定义，再调用当前阶段需要的那一项：

~~~javascript
const nodeTypes = new Map([
  ['heading', {
    validateDraft: n => typeof n.props.text === 'string' && Number.isInteger(n.props.level),
    render: n => ({ tag: `h${n.props.level}`, text: n.props.text }),
    validatePublish: () => [],
  }],
  ['image', {
    validateDraft: n => typeof n.props.src === 'string' && typeof n.props.alt === 'string',
    render: n => ({ tag: 'img', src: n.props.src, alt: n.props.alt }),
    validatePublish: n => (n.props.alt.trim() ? [] : [`${n.id}: alt must not be empty`]),
  }],
]);

function definitionFor(node) {
  const definition = nodeTypes.get(node.type);
  if (!definition) throw new RangeError(`unsupported type: ${node.type}`);
  if (!definition.validateDraft(node)) throw new TypeError(`invalid draft node: ${node.id}`);
  return definition;
}

const renderNode = node => definitionFor(node).render(node);             // 画布预览
const publishErrors = nodes =>                                           // 发布门禁
  nodes.flatMap(node => definitionFor(node).validatePublish(node));
~~~

对 r17 里的 `image-1`（`src: '/media/diagram.png'`、`alt: ''`），`renderNode` 返回 `{"tag":"img","src":"/media/diagram.png","alt":""}`，`publishErrors` 返回 `["image-1: alt must not be empty"]`；补上替代文本后，`publishErrors` 返回 `[]`。保存只对每个节点调用 `definitionFor`，所以只做草稿检查。

新增图片只需登记一项定义，画布、保存和发布都从同一个注册表读取，不必再各加一个 `image` 分支。登记本身仍是代码变更；OCP 的收益在于不必改动所有已有调用路径。

注册表也有成本：类型、校验器和渲染器必须保持一致，错误处理和注册时机要约定。如果只有一两个稳定的类型，`switch` 更直观。

### 替换实现时，子类型不能改变调用者依赖的行为

**Liskov Substitution Principle (里氏替换原则，LSP)** 讨论的是行为契约，不只是继承关系或相同的方法名。注册表里的 `render` 就是一份契约：画布依赖“只要节点通过草稿检查，`render(node)` 就同步返回预览描述符”。

假设有人为图片写了一个 `ImagePreviewRenderer` 替换默认实现，它要求调用者先下载图片，否则对同一个合法节点抛出“暂不支持”。这个实现加强了前置条件，画布无法安全地用它替换原实现。可行的做法有两种：

- 仍然同步返回 `<img>` 描述符，让浏览器自己加载资源。
- 如果产品确实要等加载结果，就把 `render` 契约整体改成异步，并让所有现有调用者处理加载状态。

不能只在一个子类型里悄悄改变行为。判断能否替换时，列清前置条件、后置保证、错误结果和状态不变量：子类型不能要求调用者额外准备条件，也不能撤回基类已经承诺的结果。Liskov 与 Wing 的形式化定义把这些可观察行为与类型不变量一起纳入。

### 接口按调用角色切分，依赖指向策略一侧

**Interface Segregation Principle (接口隔离原则，ISP)** 针对的问题是：调用者被迫依赖自己用不到的能力。画布只需要把节点渲染成视图；发布流程需要校验文档并持久化。如果两者都依赖一个同时包含编辑、渲染、校验、存储和发布的大接口，任何一方的变化都可能拉着另一方重新编译、测试或部署。

按稳定的调用角色拆分：画布依赖 `NodeRenderer`，发布流程依赖 `DocumentValidator` 和 `DocumentWriter`。这不等于给每个类、每个调用点都新建专属接口；Martin 也提醒接口切得过细，数量和关系会变得难以维护。

**Dependency Inversion Principle (依赖倒置原则，DIP)** 调整的是依赖方向。发布模块自己定义需要的 `DocumentWriter` 契约，数据库适配器实现它；启动代码（组合入口）把适配器交给发布流程：

~~~javascript
// 发布模块：契约由使用方定义，只要求 write(snapshot)
async function publish(revision, { loadRevision, writer }) {
  const document = await loadRevision(revision);
  const errors = publishErrors(document.nodes);
  if (errors.length) return { ok: false, errors };
  await writer.write({ revision, document });
  return { ok: true, revision };
}

// 组合入口：把具体的数据库适配器交给发布流程
// publish(18, { loadRevision: drafts.load, writer: postgresSnapshotWriter });
~~~

依赖箭头因此从数据库细节指向发布模块的契约，而不是发布逻辑直接依赖某个数据库驱动。**dependency injection (依赖注入)** 只是把 `writer` 传进来的手段，不等于依赖倒置本身。如果文档只写进一个简单的内存对象，既没有替换需求，也没有测试隔离收益，再包几层接口并不会让设计更好。

### DRY 消除的是重复知识，不是相似代码

DRY (Don't Repeat Yourself) 出自 Hunt 与 Thomas：每份知识在系统中只有一个清楚、权威的表示。判断标准是：一次需求变更是否必须在多个位置、以不同形式同步修改。

- **相似但不是同一知识。** 标题文本和按钮标签恰好都是字符串，含义却不同。把它们合成一个含糊的 `text` 字段，调用者反而更难判断含义。
- **同一知识被分头维护。** “哪些节点可以发布”若在编辑预览和发布流程里各写一份列表，两份迟早不一致。应找到这条政策的所有者，例如让两处都读注册表里的 `validatePublish`。
- **同一知识在两处执行。** 浏览器的即时提示和服务端的权威校验处在不同信任边界，必须分别执行。只要两处读取同一份规则定义，执行两次并不违反 DRY。

### 什么时候引入扩展点，什么时候拆掉它？

KISS (Keep It Simple) 要求方案与当前变化规模相称。YAGNI (You Aren't Gonna Need It) 提醒不要凭假想的插件需求预建多层接口：Martin Fowler 指出，未被使用的扩展点也会增加当下的复杂度。

在本例里，可以这样判断：

- **第一次新增类型、只有一处调用。** 直接加一个分支更简单。
- **多种类型接连要求修改同一批入口。** 引入注册表，把创建、校验和渲染的扩展集中到一处。
- **引入之后继续观察。** 每次新增是否真的只需登记一项定义？一致性问题是否只是从分支转移到了注册表和类型声明之间？扩展机制本身开始变复杂时，就重新评估这个边界。

### 组件和分层各解决什么问题？

前面讨论的是规则怎样组织，代码在界面和模块上怎样拆分是另外两个问题。

**component-based architecture (基于组件的架构)** 按可复用的视图和交互边界拆分界面：`Canvas` 呈现文档树，`Inspector` 编辑选中节点的属性，`NodeView` 呈现一种节点类型。组件接口要说明数据和回调怎样传入，选择、修改、删除等意图怎样传出。视图拆成组件，并不会因此获得文档的所有权。

分层按职责把交互状态、文档命令、持久化和视图分开。这个编辑器只需要少数几层：

- 会话控制器持有当前选择 `selectedId` 和拖动预览 `dragPreview`。
- 文档所有者接受命令，校验结构与业务规则，产生新修订。
- 存储适配器保存一个指定修订。
- 视图读取会话和文档的投影。

只有某一层确实承载独立的规则或依赖边界，才值得拆成独立的包或服务。给每个组件都配一套“控制器—服务—仓库”，会增加跨层跳转，却未必缩小变化范围。

### 本章产出与下一步

本章给出一套判断顺序：先列出一条需求会改到的代码，再按变化来源划分职责，只在变化反复出现时引入扩展点，并持续检查扩展点是否真的缩小了修改范围。页面编辑器的边界因此确定为：注册表负责按类型分发，草稿检查与发布门禁分开，文档所有者是唯一能产生修订的模块。

两条支线沿用同一个编辑器：[工厂、策略、观察者和单例各解决什么协作问题](#50.%20%E5%B7%A5%E5%8E%82%E3%80%81%E7%AD%96%E7%95%A5%E3%80%81%E8%A7%82%E5%AF%9F%E8%80%85%E5%92%8C%E5%8D%95%E4%BE%8B%E5%90%84%E8%A7%A3%E5%86%B3%E4%BB%80%E4%B9%88%E5%8D%8F%E4%BD%9C%E9%97%AE%E9%A2%98%EF%BC%8C%E4%BD%95%E6%97%B6%E5%A4%9A%E4%BD%99%EF%BC%9F)把“创建—校验—提交—通知”落实成对象协作；[页面编辑器怎样建模文档、编辑会话和发布快照？](#51.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)说明这三份数据怎样分开保存，r17 为什么不会混进公开页面。

主线接下来回到报表服务。设计决定了代码怎样分块，但缺陷仍会出现：下一章[怎样把一份缺陷报告变成可证伪的反例，并用证据审查修复？](#52.%20%E6%80%8E%E6%A0%B7%E6%8A%8A%E4%B8%80%E4%BB%BD%E7%BC%BA%E9%99%B7%E6%8A%A5%E5%91%8A%E5%8F%98%E6%88%90%E5%8F%AF%E8%AF%81%E4%BC%AA%E7%9A%84%E5%8F%8D%E4%BE%8B%EF%BC%8C%E5%B9%B6%E7%94%A8%E8%AF%81%E6%8D%AE%E5%AE%A1%E6%9F%A5%E4%BF%AE%E5%A4%8D%EF%BC%9F)从一份越权报告出发，讲怎样把症状写成可证伪的反例，沿调用路径找到丢失的条件。

> [!info]- 来源
> - **SRP 的“变化理由”对应提出需求的一方**（“按变化来源划分职责”）：Robert C. Martin, “The Single Responsibility Principle,” 2014-05-08，“What defines a reason to change?” 至结尾：[原文](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html)。
> - **OCP、LSP、DIP 与 ISP，以及接口切得过细的代价**（“注册表”“子类型”“接口”三节）：Robert C. Martin, “Design Principles and Design Patterns,” 2000，OCP pp. 4–8、LSP pp. 8–12、DIP pp. 12–14、ISP pp. 14–16：[PDF](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。把原则用到编辑器注册表、存储边界和调用者契约，是本章的合成案例。
> - **行为子类型：前后置条件与不变量**（“子类型不能改变调用者依赖的行为”）：Barbara H. Liskov, Jeannette M. Wing, “A Behavioral Notion of Subtyping,” *ACM TOPLAS* 16(6), 1994, pp. 1811–1841，§5.2：[PDF](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf)。
> - **DRY 是知识的单一权威表示**（“DRY 消除的是重复知识”）：Andy Hunt, Dave Thomas, *The Pragmatic Programmer*, 20th Anniversary Edition, Topic 9 “DRY—The Evils of Duplication”：[节选 PDF](https://media.pragprog.com/titles/tpp20/dry.pdf)。
> - **客户端检查只作即时反馈，服务端仍须权威校验**（“草稿合法与可发布是两道检查”“DRY”）：OWASP *Input Validation Cheat Sheet*，“Client-only checks”：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)。
> - **装饰图可用空 alt**（案例中的产品约定）：W3C WAI, “An alt Decision Tree”：[原文](https://www.w3.org/WAI/tutorials/images/decision-tree/)。
> - **YAGNI 与未使用扩展点的当下成本**（“什么时候引入扩展点”）：Martin Fowler, “Yagni”：[原文](https://martinfowler.com/bliki/Yagni.html)。
## 50. 工厂、策略、观察者和单例各解决什么协作问题，何时多余？

本章回答：页面编辑器里的四种常见模式（工厂、策略、观察者、单例）各解决哪个对象协作问题，什么时候它们只是多出来的间接层。读者已经有[上一章](#49.%20%E6%80%8E%E6%A0%B7%E5%88%A4%E6%96%AD%E4%B8%80%E4%B8%AA%E6%8A%BD%E8%B1%A1%E5%80%BC%E4%B8%8D%E5%80%BC%E5%BE%97%E5%BC%95%E5%85%A5%EF%BC%9F)的判断顺序：先看变化会传播到哪里，再决定抽象。模式是这些判断的常见落点，本章把它们放回同一次编辑里检查。

**案例。** 沿用上一章的页面编辑器：公开版是 r16，`section-1` 下有 `button-1` 和 `heading-1`。编辑者从工具栏插入一张图片 `image-1`（`alt` 还空着），文档所有者提交 r17 后，画布与检查器都要显示 r17。插入要依次经过四步：创建节点、草稿检查、提交修订、通知视图。

### 模式给协作起名，不替系统决定所有权

**design pattern (设计模式)** 给反复出现的对象协作方式起了名字。GoF（Gamma、Helm、Johnson、Vlissides 四位作者）的《设计模式》介绍每个模式时，都写明适用情境、参与者、结果和取舍，并恰好用一个文档编辑器作贯穿案例。模式不是可以机械套用的类图。

模式也不替系统回答所有权问题：谁拥有文档，哪些规则只在发布时检查，订阅何时结束。这些仍要由设计决定。判断是否需要某个模式，先看哪种变化在反复出现。如果一次普通函数调用或一个稳定的分支已经让修改范围很清楚，再加对象、注册步骤和清理责任，只会让读代码的人多跳几次。

下面三段代码各自独立，可以单独运行。

### 工厂：多个入口共享同一套创建规则

工具栏、粘贴和快捷键都能创建节点。如果每个入口各自填默认属性、各自分配 ID，节点形状会逐渐不一致。**factory (工厂)** 把这些创建规则集中到一处，最初通常只是一个函数：

~~~javascript
const defaults = new Map([
  ['heading', { text: '', level: 2 }],
  ['button', { label: '按钮' }],
  ['image', { src: '', alt: '' }],
]);

function nextId(type, existingIds) {
  let serial = 1;
  while (existingIds.has(`${type}-${serial}`)) serial += 1;
  return `${type}-${serial}`;
}

function createNode(type, existingIds, overrides = {}) {
  const initialProps = defaults.get(type);
  if (!initialProps) throw new RangeError(`unknown component type: ${type}`);
  return { id: nextId(type, existingIds), type, props: { ...initialProps, ...overrides }, children: [] };
}

const existingIds = new Set(['section-1', 'button-1', 'heading-1']);
console.log(JSON.stringify(createNode('image', existingIds, { src: '/media/diagram.png' })));
// {"id":"image-1","type":"image","props":{"src":"/media/diagram.png","alt":""},"children":[]}
console.log(createNode('heading', existingIds).id); // heading-2
createNode('constructor', existingIds);              // 抛出 RangeError
~~~

几处值得注意：

- **空 `alt` 只是编辑期默认值。** “发布时 alt 非空”属于发布门禁，不应塞进节点创建。
- **用 `Map` 登记类型。** `Map` 只认显式登记的键；普通对象会顺着原型链把 `constructor` 这类名字当成已有属性。
- **ID 只在当前文档、单个写入者内不重复。** `nextId` 跳过文档里已有的 ID，所以新标题得到 `heading-2`。多窗口协作或多个写入者并发时，需要由服务端分配或使用 UUID 这类全局唯一方案。
- **什么时候多余。** 如果整个页面只有一处创建这种固定对象，直接写对象字面量更清楚。

这个函数也不是 GoF 的 **Factory Method (工厂方法)** 或 **Abstract Factory (抽象工厂)**：前者让子类决定实例化哪个类，后者创建一族相关对象。本例没有这两类变化需求。

### 策略：同一契约下可互换的校验算法

工厂产出的节点在提交前要做草稿检查。不同类型有各自的结构规则；不想每加一种类型就往一个越来越长的条件块里加分支，可以把每种类型的检查写成独立函数，按类型查找。**strategy (策略)** 模式就是让调用方通过同一个契约使用这些可互换的算法。上一章注册表里每个类型的 `validateDraft`，就是一个策略。

~~~javascript
const draftValidators = new Map([
  ['heading', node =>
    typeof node.props.text === 'string' &&
    Number.isInteger(node.props.level) && node.props.level >= 1 && node.props.level <= 6
      ? [] : ['标题需要字符串文本和 1–6 级层级']],
  ['image', node =>
    typeof node.props.src === 'string' && typeof node.props.alt === 'string'
      ? [] : ['图片需要字符串 src 和 alt']],
]);

function validateDraftNode(node) {
  const validate = draftValidators.get(node.type);
  return validate ? validate(node) : [`未知组件类型：${node.type}`];
}

const image = { id: 'image-1', type: 'image', props: { src: '/media/diagram.png', alt: '' }, children: [] };
console.log(validateDraftNode(image));                                   // []
console.log(validateDraftNode({ ...image, props: { src: image.props.src } })); // ['图片需要字符串 src 和 alt']
console.log(validateDraftNode({ ...image, type: 'video' }));             // ['未知组件类型：video']
~~~

`alt` 为空字符串的图片通过草稿检查；缺少 `alt` 字段的节点不通过。策略的职责边界很窄：

- 它只校验已解析节点的类型特有字段。来自服务器或文件的数据，要先经过通用的结构解析。
- 它不负责授权，也不检查发布规则。“编辑时合法”和“可以发布”由不同流程负责。

如果类型和规则数量少且稳定，`switch` 更直接；只有变化确实分散到多处时，策略注册才值得额外维护。

### 状态所有者先提交，观察者再通知

校验通过的节点要提交进文档，并让画布和检查器看到同一个修订。这里有两个角色：

- **状态所有者**持有当前文档，是唯一能提交修订的模块。它自己调用策略，不相信调用者传来的错误列表。有错误就拒绝，修订保持 r16，不通知任何视图；没有错误才创建 r17、冻结、提交。
- **通知器**只持有订阅列表，不持有文档。提交完成后，所有者把已提交的 r17 交给它，由它分发给每个订阅者。

**observer (观察者)** 模式描述的正是后一半：一个主体管理多个接收者，状态变化后通知它们。“先提交再通知”保证视图收到的总是一份已经生效、不会再变的修订。

![插入图片先经工厂和草稿策略；校验通过才提交 r17，失败时修订仍为 r16 且不通知视图](../../engineering-foundations/practice/resources/design-patterns-in-practice-node-insertion.svg)

> [!example]- 状态所有者与通知器的可运行实现
>
> ~~~javascript
> class DocumentNotifier {
>   #listeners = new Set();
>
>   subscribe(listener) {
>     this.#listeners.add(listener);
>     return () => this.#listeners.delete(listener);
>   }
>
>   notify(document) {
>     for (const listener of [...this.#listeners]) listener(document); // 先复制，再遍历
>   }
> }
>
> function freezeDocument(document) {
>   return Object.freeze({
>     ...document,
>     nodes: Object.freeze(document.nodes.map(node => Object.freeze({
>       ...node,
>       props: Object.freeze({ ...node.props }),
>       children: Object.freeze([...node.children]),
>     }))),
>   });
> }
>
> function draftErrors(node) {
>   if (node.type !== 'image') return [];
>   return typeof node.props.src === 'string' && typeof node.props.alt === 'string'
>     ? [] : ['图片需要字符串 src 和 alt'];
> }
>
> class DocumentOwner {
>   #current;
>   #notifying = false;
>   notifier = new DocumentNotifier();
>
>   constructor(document) { this.#current = freezeDocument(document); }
>   get current() { return this.#current; }
>
>   insert(node) {
>     if (this.#notifying) return { ok: false, errors: ['通知期间不能同步提交'] };
>     const errors = draftErrors(node);                  // 所有者自己调用策略
>     if (errors.length) return { ok: false, errors, revision: this.#current.revision };
>
>     this.#current = freezeDocument({
>       ...this.#current,
>       revision: this.#current.revision + 1,
>       nodes: [...this.#current.nodes, node],
>     });                                                // 先提交
>     this.#notifying = true;
>     try {
>       this.notifier.notify(this.#current);             // 再通知
>     } finally {
>       this.#notifying = false;
>     }
>     return { ok: true, revision: this.#current.revision };
>   }
> }
>
> const owner = new DocumentOwner({
>   revision: 16,
>   nodes: [
>     { id: 'button-1', type: 'button', props: { label: '报名' }, children: [] },
>     { id: 'heading-1', type: 'heading', props: { text: '欢迎', level: 1 }, children: [] },
>   ],
> });
> const received = [];
> const stopCanvas = owner.notifier.subscribe(doc => received.push(`canvas r${doc.revision}`));
> const stopInspector = owner.notifier.subscribe(doc => received.push(`inspector r${doc.revision}`));
>
> const image = { id: 'image-1', type: 'image', props: { src: '/media/diagram.png', alt: '' }, children: [] };
> console.log(owner.insert({ ...image, props: { src: image.props.src } }));
> // { ok: false, errors: ['图片需要字符串 src 和 alt'], revision: 16 }，received 仍为空
> console.log(owner.insert(image), received.join(', '));
> // { ok: true, revision: 17 } 'canvas r17, inspector r17'
> stopCanvas();     // 视图卸载时取消订阅
> stopInspector();
> ~~~
>
> 为聚焦对象协作，这里把文档简化成节点数组，草稿检查也只写了图片一种类型。按 ID 索引的完整文档树见[页面编辑器的数据模型](#51.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)。

### 通知期间会发生什么：快照、重入、异常与退订

观察者最容易出错的地方不在“注册—通知”本身，而在通知进行到一半时发生的事。下面四条规则决定了视图看到的顺序和内容。

![通知器把同一个不可变的 r17 送给画布和检查器；视图挂载时注册，卸载时调用取消函数](../../engineering-foundations/practice/resources/design-patterns-in-practice-observer-lifecycle.svg)

**1. 遍历前复制接收者列表。** JavaScript 的 `Set` 迭代是“实时”的：遍历中删除一个尚未访问的成员，它会被跳过；遍历中新加入的成员，本轮也会被访问。`notify()` 先复制一份 `[...this.#listeners]` 再遍历，本轮的接收者集合就固定了：本轮中有人退订，对方仍会收到本轮通知；新订阅者从下一轮开始接收。`Set` 实时迭代的细节和事件总线里的实例，见[同步事件总线在分发途中增删监听器会怎样？](../../frontend/javascript/event-bus-and-observer-patterns.md)。

**2. 文档内容靠不可变更新保护。** 复制列表只固定了接收者，不保护文档。每次提交都复制并冻结文档、节点、属性和子节点数组，画布和检查器只能读。`Object.freeze` 是浅冻结：示例的属性值只有字符串和数字，所以冻结到 `props` 为止；属性里若有嵌套对象，要逐层冻结或采用其他不可变约定。

**3. 通知期间拒绝同步重入提交。** 假设画布在收到 r17 时立刻又提交了一次。没有保护时，内层提交产生的更新修订会先发给所有人，外层循环再继续把 r17 发给检查器：检查器先收到更新的修订、后收到 r17，最终停在旧修订上。所以所有者在通知期间拒绝同步提交，`finally` 保证通知结束后解除这个限制。

**4. 监听器抛错会中断本轮。** 某个监听器抛出的异常会传回提交的调用者，本轮排在它后面的监听器收不到通知；但修订在通知前已经提交，不会因此回滚。若要求每个视图都必须收到，可以在通知边界逐个捕获错误或安排重试。这会改变错误语义，要明确约定，不必为此另造一个事件队列。

**退订随视图生命周期结束。** `subscribe()` 返回取消函数，视图卸载时调用它。忘记退订的视图会继续收到通知，并让通知器一直引用它。

### 观察者、发布订阅、回调还是 EventTarget？

“有多个接收者”不等于需要全局事件总线。几种机制的差别在于谁知道谁：

| 机制 | 发送方知道什么 | 适合 | 代价 |
| --- | --- | --- | --- |
| 普通回调 | 唯一的接收函数 | 父子组件之间只有一个接收者 | 接收者多了就要自己管理列表 |
| 观察者 | 自己的订阅列表 | 画布和检查器天然属于这份文档，直接订阅文档通知器 | 订阅清理、只读约定和错误传播要明确 |
| publish-subscribe (发布订阅) | 只知道主题，由中介路由 | 多个互不相识的插件监听 `document:saved` | 主题字符串和跨模块调用让消息来源更难追踪 |
| `EventTarget` | 浏览器内置的监听列表 | DOM 节点和需要捕获、冒泡、取消语义的场景 | 带着事件传播的额外语义 |

发布订阅的中介可以持有 `Map<topic, Set<listener>>`，订阅者用返回的取消函数从同一主题的集合里移除自己。`EventTarget` 让对象直接管理自己的监听器，可看作内置的观察者式 API；页面级事件分发见[一次点击怎样传播到处理器？](../../frontend/browser/dom-events.md)。

### 单例：先说清“唯一”指什么范围

工厂和策略都依赖一份“组件类型 → 默认值或校验函数”的注册表。如果要求所有面板用同一份注册表，先要说清“同一份”的范围。**singleton (单例)** 把“只有一个实例”和“全局访问点”绑在一起，但它不能自动保证浏览器多个标签页、worker、多个进程或被重复打包的模块副本共享同一个对象。

多数编辑器只需要在组合入口创建一个 `EditorRuntime`，再把注册表显式传给画布、检查器和命令处理器。这样在一个应用内确实共享同一实例，测试也能各自创建独立的运行时。全局单例则有几个问题：

- 依赖被隐藏，读代码时看不出谁用了它。
- 一个页面上的两个编辑器实例，或不同测试之间，会相互污染。
- JavaScript 模块级变量只在该模块实例内共享，不保证不同模块副本共用。
- 类的构造器若仍公开，`getInstance()` 也挡不住调用方 `new` 出额外的对象。

只有全局访问点本身能解决一个明确问题时，才值得承担这种耦合。

### 用设计原则复核这些模式

沿“插入图片”流程复核一遍责任边界：工厂只负责初始属性与 ID；草稿策略只负责节点结构；状态所有者根据策略结果决定是否提交修订；观察者只通知已提交的只读状态；发布门禁另行检查一个指定修订能否公开。r17 发布被拒，不影响它已经被保存、预览和继续编辑。

模式不会自动带来开闭原则。新增一种节点类型时，开发者可能仍要改类型定义、渲染器和发布规则；只有新变化能在局部扩展、而调用契约保持稳定时，修改范围才真正缩小。上层流程依赖“提交后通知”的契约、通知器实现这个契约，是依赖倒置的一种接法。

本章产出的是一条已确认的协作链：创建 → 草稿检查 → 提交 → 通知。所有者提交的修订怎样组织成文档树、撤销怎样与修订号共存、r17 为什么进不了公开页面，见[页面编辑器怎样建模文档、编辑会话和发布快照？](#51.%20%E9%A1%B5%E9%9D%A2%E7%BC%96%E8%BE%91%E5%99%A8%E6%80%8E%E6%A0%B7%E5%BB%BA%E6%A8%A1%E6%96%87%E6%A1%A3%E3%80%81%E7%BC%96%E8%BE%91%E4%BC%9A%E8%AF%9D%E5%92%8C%E5%8F%91%E5%B8%83%E5%BF%AB%E7%85%A7%EF%BC%9F)。

> [!info]- 来源
> - **模式的适用情境、结果与取舍，以文档编辑器为贯穿案例**（“模式给协作起名”）：Gamma, Helm, Johnson, Vlissides, *Design Patterns: Elements of Reusable Object-Oriented Software*, Addison-Wesley, 1994：[出版页](https://www.oreilly.com/library/view/design-patterns-elements/0201633612/)。
> - **`Set` 的删除、迭代入口与实时迭代行为**（“通知期间会发生什么”第 1 条）：ECMAScript 2026, Keyed Collections, §§24.2.4.4、24.2.4.17–18、24.2.6.1：[规范](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-set-iterator-objects)，2026-11-12 核对。
> - **`EventTarget` 的监听列表、注册、移除与事件分发**（“观察者、发布订阅、回调还是 EventTarget”）：WHATWG DOM Standard, §§2.7、2.9：[规范](https://dom.spec.whatwg.org/#interface-eventtarget)，2026-11-12 核对。
> - **设计原则与模式的关系**（“用设计原则复核这些模式”）：Robert C. Martin, “Design Principles and Design Patterns,” 2000, p. 4：[PDF](https://objectmentor.com/resources/articles/Principles_and_Patterns.pdf)。
## 51. 页面编辑器怎样建模文档、编辑会话和发布快照？

本章回答：页面编辑器里哪些数据进入可保存的文档，哪些只属于这次编辑会话，一个已保存的修订又怎样成为访客看到的公开页面。读者已经有设计章的结论：文档所有者是唯一能产生修订的模块，草稿检查与发布门禁分开。本章给出它们背后的数据模型，并说明 r17 为什么进不了公开页面。

**案例。** 沿用[设计章](#49.%20%E6%80%8E%E6%A0%B7%E5%88%A4%E6%96%AD%E4%B8%80%E4%B8%AA%E6%8A%BD%E8%B1%A1%E5%80%BC%E4%B8%8D%E5%80%BC%E5%BE%97%E5%BC%95%E5%85%A5%EF%BC%9F)的页面编辑器，把起点往前推到 r12。页面 `page-home` 当前是修订 r12，访客读到的也是由 r12 生成的公开快照。分组 `section-1` 下有标题 `heading-1`（“首页”）和报名按钮 `button-1`。编辑者依次改标题、重排、撤销与重做、保存并发布 r16，然后插入 `alt` 为空的图片得到 r17，补上 `alt` 得到 r18。数据模型要保证两件事：选择或拖动不会误写页面；访客始终知道自己看到的是哪一个已校验的修订。

### 三种数据，三种生命周期

编辑器同时持有几类生命周期不同的数据。把它们混在一起，选择节点就会推进修订，拖动就会写进撤销历史：

| 数据 | 记录什么 | 案例初值 | 生命周期 | 所有者 |
| --- | --- | --- | --- | --- |
| 页面文档 | 页面本身的事实：稳定 ID、类型、属性、子节点、顶层顺序 | r12，`section-1.children = ['heading-1','button-1']` | 可保存、可撤销、可作为预览和发布的输入 | 文档所有者 |
| 编辑会话 | 当前选择、打开的面板、拖动中的候选位置 | `selectedId=null`、`openPanel='inspector'`、`dragPreview=null` | 本次编辑器会话；不进入文档 | 会话控制器 |
| 组件局部状态 | 输入焦点、光标、尚未确认的输入缓冲 | — | 对应组件挂载期间 | 输入组件 |
| 公开快照 | 某个修订加上固定的渲染依赖 | 活动指针指向 r12 的快照 | 新草稿不断产生时保持不变，直到下一次发布成功 | 发布服务与快照存储 |

选择某个节点不推进修订，不进入撤销历史，也不影响发布。哪些字段属于文档，取决于产品语义而不是字段名：产品要保存布局，`style` 就属于文档；某个样式只服务于拖动中的临时预览，就跟 `dragPreview` 一起留在会话里。前端各类状态（URL、查询缓存、全局 store、组件）由谁持有的通用判断，见[一份界面状态该由谁持有？](../../frontend/ui-state/state-ownership-and-composition.md)；本章只看编辑器这一个所有者。

### 用扁平 ID 表表示一片森林

文档用 `rootIds` 记录顶层节点及其顺序，用按 ID 索引的 `nodes` 保存节点；`children` 只存子节点的 ID：

~~~javascript
const documentState = {
  schemaVersion: 1,
  revision: 12,
  rootIds: ['section-1'],
  nodes: {
    'section-1': { id: 'section-1', type: 'section', props: { label: '首页内容' },
                   children: ['heading-1', 'button-1'] },
    'heading-1': { id: 'heading-1', type: 'heading', props: { text: '首页', level: 1 }, children: [],
                   style: { position: 'absolute', top: 100, left: 200 } },
    'button-1':  { id: 'button-1', type: 'button',
                   props: { label: '报名', action: { kind: 'navigate', pageId: 'form' } }, children: [] },
  },
};

const editorSession = { selectedId: null, openPanel: 'inspector', dragPreview: null };
~~~

按 ID 索引让检查器能直接定位 `heading-1` 并局部更新；重排兄弟节点只改 `section-1.children`，不必挪动节点对象。

代价是结构约束不再由嵌套自动保证。已提交的文档必须是一片合法的 forest (森林)，即若干棵互不相交的树：

- 根 ID 不重复，根节点不能同时是别人的子节点。
- 每条父子边只出现一次，每个非根节点恰好有一个父节点。
- 所有节点都能从某个根到达，且没有环。

只检查“ID 唯一、引用存在、无环”还不够：两个分组可能同时引用同一个子节点，文档里也可能留下无法从根到达的孤儿节点。这些条件可以用一次父节点计数加一次从根出发的遍历检查，算法和错误定位见[怎样遍历一棵树，又怎样把扁平记录安全地还原成树？](#3.%20%E6%80%8E%E6%A0%B7%E9%81%8D%E5%8E%86%E4%B8%80%E6%A3%B5%E6%A0%91%EF%BC%8C%E5%8F%88%E6%80%8E%E6%A0%B7%E6%8A%8A%E6%89%81%E5%B9%B3%E8%AE%B0%E5%BD%95%E5%AE%89%E5%85%A8%E5%9C%B0%E8%BF%98%E5%8E%9F%E6%88%90%E6%A0%91%EF%BC%9F)。产品若允许尚未挂进树的新节点草稿，可以先暂存在会话里，提交时再要求整棵树满足约束。

较小的编辑器也可以直接用嵌套对象表示树，不必过早拆成扁平表；但“每个节点只有一个父节点、都属于某个根”的规则不变。

### 视图只发命令，文档所有者产生修订

数组下标会随插入和排序变化，不能作节点的长期身份；稳定 ID 让检查器、历史记录和协作消息都能指向同一个节点。在此之上，编辑遵循 unidirectional data flow (单向数据流)：所有者把当前文档交给视图，视图只能用 **command (命令)** 请求变化，例如“把 `heading-1` 的 `text` 改成‘欢迎’”或“把 `heading-1` 移到 `button-1` 之后”。命令是可校验的意图，调用方不能直接改所有者持有的对象。

所有者处理命令时，在副本上应用改动，校验整份文档，通过才分配新修订：

~~~javascript
function commit(candidate, { recordHistory = true } = {}) {
  const next = structuredClone(candidate);
  next.revision = current.revision + 1;                 // 修订号只增不减
  const errors = validateDocument(next);                 // 森林约束 + 各类型的草稿检查
  if (errors.length) return { ok: false, errors, revision: current.revision };

  if (recordHistory) { past.push(current); future.length = 0; }
  current = deepFreeze(next);
  return { ok: true, revision: current.revision };
}
~~~

命令被拒绝时，错误返回给发起方，文档和撤销栈都不变。React 文档里“把需要协调的状态提升到最近的共同父组件”是同一种所有权思路，但这不意味着所有状态都要搬进一个全局对象，只要选中项、输入草稿和已提交文档各自由谁持有是清楚的。

如果浏览器端只是草稿缓存，服务端保存时还要检查客户端基于哪个版本，防止较旧的客户端覆盖较新的提交。HTTP 层用 ETag 与 `If-Match` 做这件事，见[两个客户端同时修改同一资源时，API 怎样防止互相覆盖？](#38.%20%E4%B8%A4%E4%B8%AA%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%90%8C%E6%97%B6%E4%BF%AE%E6%94%B9%E5%90%8C%E4%B8%80%E8%B5%84%E6%BA%90%E6%97%B6%EF%BC%8CAPI%20%E6%80%8E%E6%A0%B7%E9%98%B2%E6%AD%A2%E4%BA%92%E7%9B%B8%E8%A6%86%E7%9B%96%EF%BC%9F)；表单怎样处理这类冲突见[编辑表单怎样在别人同时修改时安全保存？](../../frontend/ui-state/editing-sessions-and-conditional-writes.md)。

### 拖动只改临时投影

拖动过程中，鼠标每移动一次，候选顺序就变一次。如果每次都提交命令，撤销历史和保存任务会记下几十个无意义的中间状态。所以拖动只改会话：

- 拖动开始时，会话的 `dragPreview` 记录父节点和候选顺序，例如 `{ parentId: 'section-1', children: ['button-1', 'heading-1'] }`。
- 画布显示的是**临时投影**：已提交文档加上 `dragPreview` 合成的结果，不写回文档。不读会话的普通预览（例如预览页）仍只按文档顺序显示。
- 取消拖动就清空候选，画布回到文档顺序，修订和撤销栈都不变。
- 松手确认后才发出移动命令，由所有者生成新修订；成功后清空候选。命令被拒绝时，候选留在会话里，由界面决定提示或清除。

### 撤销与重做也产生新修订

撤销和重做恢复的是文档内容，但修订号仍在当前最大值上加一。r14 撤销得到 r15（内容同 r13），再重做得到 r16（内容同 r14）。这样撤销永远不会改写已经保存或发布过的修订，任何修订号都只对应一份内容。

历史怎样存是一个取舍：

- **整份快照。** `past` 和 `future` 各存完整文档，实现直观，但占用随历史长度和文档大小增长。
- **逆命令或操作日志。** 只存改动，省空间；但必须为移动、删除以及之后发生的变更正确定义反向操作。协作写入时，还要说明每个操作基于哪个版本。

撤销历史只存在于当前编辑会话里，保存的草稿和公开快照各有独立的生命周期。要在应用重启后仍能撤销，需要另外持久化历史或命令日志。

### 从 r12 到 r18：每一步改了哪份状态

下图把案例走完：从上往下是用户动作，四条泳道是生命周期不同的四份状态，跨越多行的块或竖条表示那份状态在这段时间里没有变：

![四条泳道随用户动作推进：选中后 selectedId 一直是 heading-1，拖动候选只在会话里出现并在取消后清空；文档从 r12 依次到 r18，选择、拖动和取消期间仍是 r13；草稿存储依次保存 r16、r17、r18；公开指针在 r16 校验通过前一直是 r12，发布 r17 因 alt 为空被拒仍停在 r16，r18 通过后切到 r18。](../../engineering-foundations/practice/resources/page-editor-r12-to-r18.svg)

图里的发布每次都由发布服务重新校验那个已保存的确切修订，r17 能通过草稿检查却过不了发布门禁；两类规则的分工见下文“schema 管形状”与“发布”两节。

### 所有者交出的是不可变副本

视图拿到的文档不能被它改写，否则一次误改就会绕过命令和校验。示例用 `structuredClone` 复制、`deepFreeze` 逐层冻结来表达这条边界：所有者从不把可变的内部对象直接交给视图。

~~~javascript
function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}
~~~

示例的值都限于 JSON 能表示的形状。实际框架可以用不可变数据结构、序列化边界或受控更新实现同样的隔离。还要注意示例能证明什么：它只模拟单个编辑会话，不能据此推断并发保存是安全的；下文发布代码里对活动指针的一次同步赋值，只是标出切换的边界。

### schema 管形状，业务规则管含义

发布前要检查的规则分两类。JSON Schema 2020-12 的 `type`、`required`、数组和数值约束能表达单个节点的大部分结构条件，例如 `alt` 必须是字符串、标题层级是 1 到 6 的整数。但有些规则不是“形状”：

- 跨节点的图约束：每个节点只有一个父节点、都能从根到达。标准关键字无法表达，需要应用代码。
- 引用目标是否存在、当前用户能否操作、发布时 `alt` 是否非空：这些是产品和服务端规则。

规则也分布在不同环节：

1. **从存储载入时**，先解析结构，返回能定位到具体节点的错误。
2. **执行编辑命令时**，检查本次变更是否让文档仍然合法。
3. **发布时**，对选定的修订重新确认结构、引用、权限和所需的外部资源。

浏览器里的即时校验能更早提示，但不能替代可信边界上的校验。渲染器也不应把无效节点静默渲染成空白，否则读者分不清“内容本来为空”和“数据已损坏”。

### 发布：绑定确切修订，固定渲染依赖，原子切换指针

保存不等于发布。保存只把一个修订放进草稿存储；只有编辑者明确请求发布某个已保存的修订，发布服务才开始工作：

1. **锁定一个确切的已保存修订**，而不是“当前最新”。否则校验期间又有新编辑提交，公开出去的可能是一份没校验过的内容。
2. **重新校验**这个修订的结构、组件属性、引用目标、当前用户权限和外部资源。
3. **生成不可变快照**，记录 `documentId`、`revision`、`schemaVersion`、组件注册表版本和渲染器版本。
4. **原子切换活动指针**，访客从此读新快照。

~~~javascript
function publishRevision(revision) {
  const document = savedDrafts.get(revision);           // 只接受已保存的确切修订
  if (!document) return { ok: false, error: 'publish requires a saved revision' };

  const errors = [...validateDocument(document), ...publishRuleErrors(document)];
  if (errors.length) return { ok: false, errors, activeRevision: activeSnapshot.revision };

  activeSnapshot = deepFreeze({                          // 多进程服务里是一次原子的指针更新
    documentId: 'page-home',
    revision,
    schemaVersion: document.schemaVersion,
    componentRegistryVersion: 'components-v1',
    rendererVersion: 'renderer-v1',
    document: structuredClone(document),
  });
  return { ok: true, activeRevision: revision };
}
~~~

在案例里，`publishRevision(17)` 因“`image-1` 的 alt 为空”返回错误，活动指针仍是 r16；`publishRevision(18)` 通过，指针切到 r18。示例中的同步赋值只标出切换点；多进程服务需要用数据库事务或等效的原子更新来切换持久化的指针。

**为什么要固定渲染依赖。** 只固定文档修订不足以复现画面。组件渲染代码更新后，旧修订可能渲染出不同的结果；`image-1` 引用的 `/media/diagram.png` 若被原地替换，旧快照显示的图片也会跟着变。系统可以固定这些依赖的版本，也可以保存确切的构建产物并固定外部资源引用。

**草稿与公开版并存。** r17 被拒期间，编辑者可以继续编辑，访客仍读 r16。失败的发布不删除草稿，也不改写当前页面。

**回滚不是撤销。** 回滚是把活动指针重新指向一个仍然可用的既有快照，作用在公开版；撤销作用在编辑历史，产生新的草稿修订。二者解决不同问题。

产品也可以设计“保存即发布”，但要说清哪些校验在编辑期、保存期和发布期执行，不能让同一条规则在一个入口允许、在另一个入口意外阻断。

### 文档顺序不等于绘制顺序

`section-1.children` 的顺序决定组件在图层面板里的逻辑顺序，但浏览器的绘制顺序还受 CSS 定位、`z-index` 和 **stacking context (层叠上下文)** 影响。重排两个兄弟节点只改变树顺序；如果某个组件创建了独立的层叠上下文，把它在数组里移到另一个节点后面，不保证它在视觉上盖住另一个上下文里的元素。

所以编辑器若提供“置顶”或“置底”，要说明它改的是树的兄弟顺序、同一层叠上下文内的层级，还是另一个独立的渲染模型。层叠上下文怎样形成见[定位元素参照谁，为什么大 z-index 还会被盖住？](../../frontend/html-css/positioning-and-stacking.md)。

### 多人协作：传输、排序和冲突解决分开设计

前面的模型只有一个编辑会话。多人同时编辑时要分开回答三个问题：

- **怎样传输。** WebSocket 这类通道只把编辑事件送到对方，不决定两人同时移动 `heading-1` 时以谁为准。推送通道的选型与断线续读见[服务端要持续推送更新时，怎样选通道，断线后又怎样接上？](#39.%20%E6%9C%8D%E5%8A%A1%E7%AB%AF%E8%A6%81%E6%8C%81%E7%BB%AD%E6%8E%A8%E9%80%81%E6%9B%B4%E6%96%B0%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E9%80%89%E9%80%9A%E9%81%93%EF%BC%8C%E6%96%AD%E7%BA%BF%E5%90%8E%E5%8F%88%E6%80%8E%E6%A0%B7%E6%8E%A5%E4%B8%8A%EF%BC%9F)。
- **怎样排序。** 单写者模型由服务端按顺序处理命令；版本条件或锁可以拒绝并发写入，代价是更多冲突提示或等待。
- **怎样解决冲突。** **operational transformation (操作转换，OT)** 根据已发生的并发操作改写后到的操作，以维持规定的一致性；**conflict-free replicated data type (无冲突复制数据类型，CRDT)** 把数据类型设计成满足特定数学条件，使各副本无论以什么顺序收到更新，合并后都收敛到同一状态。两者都还要定义操作格式、删除与移动语义、版本兼容和树约束。

按离线需求、实时合并要求、服务端排序能力和审计要求选择机制。即使采用 OT 或 CRDT，节点类型校验、树的父子约束和发布规则仍然要执行。

### 本章产出

页面编辑器的数据被分成三份：文档只经命令产生单调递增的修订，会话承载选择与拖动，公开快照绑定一个已保存的确切修订和它的渲染依赖，靠原子切换指针生效。r17 能保存却进不了公开页面，因为发布门禁只对锁定的那个修订放行。

“发布绑定确切的、已验证的输入，回滚只是重新指向既有产物”这一思路在主线五后面还会出现：服务的镜像按摘要晋级、按版本回退，见[已验证的产物怎样原样晋级到生产？](#57.%20%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E4%BA%A7%E7%89%A9%E6%80%8E%E6%A0%B7%E5%8E%9F%E6%A0%B7%E6%99%8B%E7%BA%A7%E5%88%B0%E7%94%9F%E4%BA%A7%EF%BC%9F)。

> [!info]- 来源
> - **JSON Schema 能表达的结构约束**（“schema 管形状，业务规则管含义”）：JSON Schema Draft 2020-12, Validation §6 的 `type`、`required`、数组与数值关键字：[规范](https://json-schema.org/draft/2020-12/json-schema-validation)，2026-11-12 核对。
> - **绘制顺序与层叠上下文**（“文档顺序不等于绘制顺序”）：W3C CSS 2.2, Appendix E “Elaborate description of Stacking Contexts”：[规范](https://www.w3.org/TR/CSS22/zindex.html)，2026-11-12 核对。
> - **共享状态的所有权与状态提升**（“视图只发命令”）：React, “Sharing State Between Components”：[原文](https://react.dev/learn/sharing-state-between-components)，2026-11-12 核对。
> - **客户端校验只作即时反馈，可信边界仍要校验**（“schema 管形状”“发布”）：OWASP *Input Validation Cheat Sheet*, “Common Pitfalls · Client-only checks”：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html#common-pitfalls)，2026-11-12 核对。
> - **发布时按请求重新校验权限**（“发布”第 2 步）：OWASP *Authorization Cheat Sheet*, “Validate the Permissions on Every Request”：[原文](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html#validate-the-permissions-on-every-request)，2026-11-12 核对。
> - **CRDT 的收敛条件**（“多人协作”）：Shapiro 等, *Conflict-free Replicated Data Types*, SSS 2011, §§2–3：[论文](https://perso.lip6.fr/Marc.Shapiro/papers/2011/CRDTs_SSS-2011.pdf)。
> - **OT 的一致性性质**（“多人协作”）：Sun 等, *Achieving Convergence, Causality Preservation, and Intention Preservation in Real-Time Cooperative Editing Systems*, 1998：[论文](https://www.cs.cityu.edu.hk/~jia/research/reduce98.pdf)。
## 52. 怎样把一份缺陷报告变成可证伪的反例，并用证据审查修复？

本章回答：收到一份“别的账户能读到我们的报表”的缺陷报告后，怎样把它写成可观察的输入和输出，用一个最小反例去推翻或确认根因假设，沿调用路径找到丢失的条件，并用别人能复核的证据审查修复。读者手上有一份症状描述、出问题的代码和一组仍然全绿的测试。

**案例。** 主线五跟随账户报表服务的一次修复发布，从缺陷一直走到生产。服务里，账户 `acct-17` 的报表 42（标题 `Service health`）只应由该账户成员读取：成员 `user-17` 读到 `200`；另一个账户 `acct-29` 的已认证成员 `user-29` 猜中编号 42 时，应得到与读取不存在的报表 43 完全相同的通用 `404`。一次重构把读取改成了 SQLAlchemy 的 `Session.get(Report, 42)`，之后有人报告 `user-29` 读到了 acct-17 的报表；现有测试只让 `user-17` 读自己的报表，仍然全绿。

这次重构已经随生产稳定版上线，所以缺陷就在线上：本主线把这个带缺陷的稳定版镜像记作 `d-old`，修复版记作 `d-new`。本章找到根因并审查修复。后续各章接着做：证明测试能区分修复前后，把修复提交进 Git，构建成镜像，逐步放量并观察它。数据都是合成的教学数据；示例代码按 SQLAlchemy 2.0 核对。

### 先把症状写成可证伪的契约

“别的账户能读到报表”还不能直接拿来查。先把这条需求写成对每类主体的预期结果，让每一行都能被一次请求证实或推翻。本例的表结构里，`report_id` 是全局主键，`account_id` 记录报表属于哪个账户；表中只有一行 `(42, acct-17, Service health)`。

| 主体 | 请求 | 预期结果 |
| --- | --- | --- |
| `user-17`（acct-17 成员） | `GET /v1/accounts/acct-17/reports/42` | `200`，返回 `Service health` |
| `user-29`（acct-29 成员） | `GET /v1/accounts/acct-29/reports/42` | `404`，状态码和正文与请求 `/v1/accounts/acct-29/reports/43` 完全相同 |
| `user-29` | `GET /v1/accounts/acct-17/reports/42` | `404`，同样的通用正文（成员检查已拒绝） |
| 无有效凭据 | `GET /v1/accounts/acct-17/reports/42` | `401`，带 `WWW-Authenticate` 质询 |

隐藏式 `404` 是这个服务的策略：对无权访问的主体，不透露报表是否存在。为什么这样选、它与 `403` 怎样取舍，见[服务怎样逐次确认这个主体能对这份资源做这个动作？](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)。

能暴露问题的**最小反例**只需要两样东西：数据库里属于 acct-17 的报表 42，以及可信主体 `user-29` 的一次读取。关键是选对路径。`user-29` 请求 `/accounts/acct-17/...` 会先在成员检查处被拒，根本碰不到被重构的那一行取数代码；请求自己账户下的 `/accounts/acct-29/reports/42` 才能通过前面所有检查，让取数层单独接受检验。

要验证“不透露存在性”，还要把这次请求与确实不存在的报表 43 比较：两者的状态码和正文必须完全相同。只看到 `404` 状态码，不能证明正文没有带出 acct-17 的数据。

现有测试为什么没发现问题？它只让 `user-17` 读自己的报表，证明了所有者能读，却从没检验过授权边界。重构前后它都会通过。

### 一次观察能说明什么

拿反例去跑一次，结果只能缩小调查范围，不能直接给出根因：

| `user-29` 读 `/accounts/acct-29/reports/42` 的结果 | 能说明什么 | 接下来核对什么 |
| --- | --- | --- |
| `200` | 契约被违反，保护条件可能丢失；但还不知道丢在哪一层 | 当前主体、实际入口、取数调用及结果归属、缓存命中、响应映射 |
| `404` | 状态码符合预期，但还没证明没泄露 | 测试是否走到同一入口、确实使用 `user-29`、装入了 acct-17 的 42；响应正文是否与 43 相同 |

即使状态码是 `404`，正文若透露报表归属，同样违反隐藏策略。如果 SQL 正确限定了账户、查不到可见的行，响应里却仍有 acct-17 的数据，就继续追旁路缓存、备用读取或序列化分支。反例证明出了问题，它本身不是根因证据。

### 主键读取不是所有权检查

重构前，读取同时按账户和编号过滤；重构后变成：

~~~python
report = session.get(Report, report_id)
~~~

`Session.get()` 按主键取对象，有两条路径：

- 对象已在当前 Session 的 identity map (身份映射表) 里、且没有完全过期时，直接返回这个对象，**不发 SELECT**。
- 对象不在 identity map 里或已完全过期时，按主键查询数据库；传 `populate_existing=True` 也会强制查询。

无论走哪条路径，它都不会加上当前主体的账户条件。本例的 `report_id` 是全局主键，所以 `session.get(Report, 42)` 是一次合法的主键读取，却不是所有权检查。表若使用复合主键，要把相应的键元组交给 `get`，仍需另行确认主体有权访问。Session 怎样借用连接、对象怎样进出 identity map，见[ORM 会话怎样借用连接，连接池为什么会耗尽？](#28.%20ORM%20%E4%BC%9A%E8%AF%9D%E6%80%8E%E6%A0%B7%E5%80%9F%E7%94%A8%E8%BF%9E%E6%8E%A5%EF%BC%8C%E8%BF%9E%E6%8E%A5%E6%B1%A0%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E8%80%97%E5%B0%BD%EF%BC%9F)。

这也决定了排查方法：不能预设“数据库一定发了查询”。若发出了 SQL，就核对最终的 WHERE 条件和绑定值；若直接从 identity map 返回，就核对调用时用的主键和返回对象的归属。

### 沿调用路径找到丢失的条件

从公开入口向数据层追踪同一个请求，逐段核对条件是否还在：

1. **入口。** 请求到达哪条公开路由，是否经过认证依赖。
2. **主体。** 认证依赖返回的主体来自已验证的会话或令牌，而不是请求里任意填写的字段。
3. **参数传递。** 路由是否把 `report_id` 和已通过成员检查的 `account_id` 都传给了数据层。
4. **实际取数。** 取数用了什么方式和参数；若执行了查询，最终 SQL 或 ORM 条件里有没有两个绑定值；返回的对象属于哪个账户；缓存是否绕过了同一授权范围。
5. **响应。** 错误映射和序列化有没有把“查不到当前主体可见的行”改成成功响应。

![已认证的 user-29 经 acct-29 请求报表 42；两列都实际发出 SELECT 时，Session.get 只按全局编号命中 acct-17 的行并返回 200，显式查询绑定 acct-29 与 42 后无匹配，返回与报表 43 相同的通用 404](../../engineering-foundations/practice/resources/reading-debugging-report-scope.svg)

在这个案例里，前三段都没问题：路由拿到了 `account_id`，但第 4 段的 `session.get` 只按全局主键取记录，根本没用到这个值。图只画两种写法都实际发出 SELECT 的情况；`Session.get` 从 identity map 直接返回时结果相同，只是没有 SQL 可看。

修复是把报表编号和账户一起作为查询条件，`account_id` 只取已经通过成员与动作检查的那个值：

~~~python
report = session.scalar(
    select(Report).where(
        Report.account_id == account_id,
        Report.report_id == report_id,
    )
)
~~~

改完还要核对 ORM 生成的查询，确认两个绑定值都进入了最终 SQL，而不是只留在调用方的局部变量里。显式查询每次都按账户条件执行，不再从 identity map 直接返回对象。

**同一条路径上的旁路：缓存。** 如果成功响应被缓存在只含 `report_id` 的键下（例如 `report:42`），即使数据库查询修好了，`user-29` 的请求仍可能命中 acct-17 留下的缓存条目。缓存键必须包含账户等授权维度，而且授权检查要在查缓存之前完成；缓存键限制副本的范围，本身不是授权凭据。缓存键该包含哪些维度，见[加了缓存之后，读到的数据最多会旧多久？](#30.%20%E5%8A%A0%E4%BA%86%E7%BC%93%E5%AD%98%E4%B9%8B%E5%90%8E%EF%BC%8C%E8%AF%BB%E5%88%B0%E7%9A%84%E6%95%B0%E6%8D%AE%E6%9C%80%E5%A4%9A%E4%BC%9A%E6%97%A7%E5%A4%9A%E4%B9%85%EF%BC%9F)。

修完后，用同一入口和同样的输入重放契约表的四行：`user-17` 仍得到 `200`；`user-29` 读 acct-29 下的 42 和 43 得到相同的通用 `404`；读 acct-17 下的 42 也是同样的 `404`；匿名请求得到 `401` 和质询头。再检查相邻的参数校验、错误映射和缓存路径，确认修复没有改变无关响应，也没有留下另一条绕行路径。

这次复验只覆盖所测的路由和缓存状态。后台导出、其他查询入口各有独立的访问路径，要按各自的数据边界核对。

### 一条审查意见要带什么证据

修复要经过代码审查，审查意见可能来自人，也可能来自安全扫描或代码审查 Agent。无论来源，一条 finding (审查发现) 都应让另一位工程师能沿着同一份差异和执行路径复核。

**报告层面**要固定：

- 检查的基准提交与候选提交；
- 覆盖了哪些范围、跳过了哪些；
- 每个 finding 的位置。

**每条结论**要给出：

- 所依据的调用路径、授权条件和成立前提；
- 可观察的影响；
- 能重新打开的引用，例如准确的差异行、测试名和运行记录、授权检查或响应证据；
- 严重度和置信度各自的依据；
- 若问题依赖未改动的上下文，说明它怎样与这次差异共同改变行为。

拿本例对照：报告“`user-29` 可读取 acct-17 的报表 42”，证据应能沿可信主体 `user-29`、实际读取或缓存范围、对象归属和 HTTP 响应逐项回查，并指向一个通过认证入口运行的回归测试。只写“缺少账户过滤”，不能证明数据进入了 `user-29` 的响应；只列一个 `404` 测试，也不能证明它走过了这条路径。

### 核实误报，给结论分类，分清谁能批准

**核实误报。** 假如一条 finding 只因 `session.get` 没有账户条件就断定泄露，审查者要沿同一个 `user-29` 请求继续检查路由、数据层、identity map、缓存和序列化：下游是否有可靠的对象归属检查，而且它在响应或缓存返回之前执行？再用 acct-29 下的 42 与 43 验证实际入口的状态码和正文。只有路径证据与测试结果共同表明 acct-17 的对象不会进入 `user-29` 的响应，才能判为误报。否则标为“已确认”或“证据不足”，不要从函数名、单条 `404` 或测试标签推断结论。

**结论分类。** 复核后的结论分为四类，并附依据：

| 结论 | 含义 | 后续 |
| --- | --- | --- |
| 已确认 | 路径证据与测试都表明问题成立 | 进入回归测试集 |
| 误报 | 路径证据与测试共同表明问题不成立 | 回头检查检测规则或报告门槛 |
| 重复 | 与已有 finding 是同一问题 | 合并到原条目 |
| 证据不足 | 无法重现或证据链断开 | 指明要补的上下文或证据 |

**独立验收。** 本例涉及跨账户数据，可以请熟悉这条授权边界、没参与写补丁的工程师独立验收。验收人拿到基准与候选提交、finding 的引用和固定的测试夹具后，独立确认主体来源、实际读取路径和测试入口，并重放契约表。保留验收人、候选版本、测试运行记录和未覆盖的路径。

**权限分工。** 自动审查的结果只是供审查者核验的证据。修复提交、仓库写入权限和合并审批仍按仓库策略授权；对访问控制变更，团队可以指定专人审批，并要求附上同一反例在修复前后的结果。Agent 工具本身的逐次授权见[为什么提示注入防不住“模型听话”，应用该在哪里拦？](../../ai-engineering/actions/prompt-injection-as-permission-confusion.md)。

> [!info] 实例：自动审查产品怎样分工（核对于 2026-11-25）
> - **Claude Ship**（Anthropic，2026 年 11 月发布）：Code Review 提出并复核问题；PR Steward 可处理失败的检查并修改 PR；Claude Approvals 按默认分支上的团队策略决定能否批准。合并仍受仓库的必需检查和分支保护约束。发布时 Code Review 已正式推出，PR Steward 与 Claude Approvals 为 beta。
> - **Codex Security**（OpenAI）：审查代码变更时输出安全上下文、检查范围、finding 和覆盖状态。具体字段以所用版本为准，对目标仓库的效果需另行评估。

### 本章产出与下一步

本章产出三样东西：一张可证伪的读取契约表，一个能通过所有前置检查、直达取数层的最小反例，以及按 `(account_id, report_id)` 显式查询的修复。审查结论已经按证据分了类。

还剩一个问题：修复后测试变绿，能说明这组测试真的检查了账户条件吗？同一个人或同一个模型写出的实现和测试，可能共享同一个遗漏的假设。下一章[一次改动该在哪一层测试，怎样证明测试能区分对错？](#53.%20%E4%B8%80%E6%AC%A1%E6%94%B9%E5%8A%A8%E8%AF%A5%E5%9C%A8%E5%93%AA%E4%B8%80%E5%B1%82%E6%B5%8B%E8%AF%95%EF%BC%8C%E6%80%8E%E6%A0%B7%E8%AF%81%E6%98%8E%E6%B5%8B%E8%AF%95%E8%83%BD%E5%8C%BA%E5%88%86%E5%AF%B9%E9%94%99%EF%BC%9F)把契约表写成经过真实路由的测试，并证明换回 `Session.get` 时它一定会失败。

> [!info]- 来源
> - **`Session.get` 的 identity map 路径、过期刷新、`populate_existing` 与复合主键**（“主键读取不是所有权检查”）：SQLAlchemy 2.0, [Session API — `Session.get`](https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.get)，核对于 2026-11-12，包版本 2.0.44。
> - **401 必须带适用的 `WWW-Authenticate`；可用 404 隐藏禁止访问的资源**（“先把症状写成可证伪的契约”）：IETF [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) §§15.5.2、15.5.4–15.5.5，核对于 2026-11-12。正文是否披露归属仍要由响应与测试保证。
> - **在 PR 中阅读差异、对具体改动评论和提交审查**（“一条审查意见要带什么证据”）：GitHub Docs, [Reviewing proposed changes in a pull request](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request)、[About pull request reviews](https://docs.github.com/en/pull-requests/concepts/giving-reviews)，核对于 2026-11-12。
> - **自动安全审查的范围与发现报告**（“一条审查意见要带什么证据”与实例 callout）：OpenAI, [Building Security Review into Your SDLC with Codex Security](https://developers.openai.com/blog/building-security-review-into-your-sdlc-with-codex-security)，2026-11-23，“Review at the right level”“Security context gives reviewers something to reason from”“An automated review loop returns reports”；[Review code changes for security](https://developers.openai.com/codex/security/plugin/code-changes)，在线文档，核对于 2026-11-25。
> - **审查、修改与批准的权限分工**（“核实误报……分清谁能批准”与实例 callout）：Anthropic, [Introducing Claude Ship](https://claude.com/resources/articles/introducing-claude-ship)，2026-11-23。
## 53. 一次改动该在哪一层测试，怎样证明测试能区分对错？

本章回答：一次改动该用哪种测试去验证，测试通过之后能声称什么、不能声称什么，以及怎样证明一组测试真能把正确实现和错误实现分开。读者手上有上一章的读取契约表、最小反例和修复后的代码。

**案例。** 沿用主线五的报表服务修复，契约表与反例来自[怎样把一份缺陷报告变成可证伪的反例，并用证据审查修复？](#52.%20%E6%80%8E%E6%A0%B7%E6%8A%8A%E4%B8%80%E4%BB%BD%E7%BC%BA%E9%99%B7%E6%8A%A5%E5%91%8A%E5%8F%98%E6%88%90%E5%8F%AF%E8%AF%81%E4%BC%AA%E7%9A%84%E5%8F%8D%E4%BE%8B%EF%BC%8C%E5%B9%B6%E7%94%A8%E8%AF%81%E6%8D%AE%E5%AE%A1%E6%9F%A5%E4%BF%AE%E5%A4%8D%EF%BC%9F)。这次改动要守住两条契约：

- **读取范围。** `user-17` 读 acct-17 的报表 42 得到 `200`；`user-29` 经自己的账户 acct-29 读 42，得到与读不存在的 43 完全相同的通用 `404`。
- **重复处理。** 同一个导出任务被投递两次时，数据库只允许一次有效的状态转换。导出请求的幂等键是 `export-demo-415`，对应任务 `job-demo-731`；任务状态是 `queued/running/succeeded/failed/cancelled`。

下面的示例用 SQLite 和进程内的 `TestClient` 演示路由与 SQL 层的本地证据；这些证据不能推广到 PostgreSQL、消息代理或生产身份系统，后文按测试边界逐一说明。

### 测试边界由要排除的失败决定

测试边界指一次测试实际纳入的真实组件范围。选边界的方法是：先写清要守住的业务条件和可观察结果，再选一个**刚好包含可能出错组件**的最小环境。只有较小的边界证明不了目标性质时，才加大环境。下表是互相补充的检查位置，不是每次改动都要依次跑完的固定层级：

| 要排除的失败 | 测试边界 | 能看到的证据 | 不能据此声称 |
| --- | --- | --- | --- |
| 访问规则本身写反（成员与非成员判断颠倒） | 单元测试 | 给定可信主体和资源归属，规则返回允许或拒绝 | 实际路由调用了这条规则 |
| 路由丢了账户条件、状态码或响应字段错误 | API 集成 | 真实路由、测试身份接缝、参数校验、数据库查询、序列化和错误映射一起工作 | 真实网络、生产身份提供方或生产数据库方言正常 |
| 唯一约束、回滚或条件更新的实际数据库行为错误 | 数据库集成 | 选定数据库执行真实表结构和 SQL | 另一种数据库有相同的类型、锁或并发行为 |
| 新响应不兼容已发布的客户端 | 契约测试 | 当前响应与已发布 schema 或代表性旧客户端的期望比较 | 只看本次生成的 OpenAPI 就证明兼容 |
| 消息发布、重复投递或 ACK 路径丢失或重复执行 | 消息代理集成 | 选定代理在其路由、持久性和确认设置下的实际交接 | 本地把 worker 函数调用两次就等于代理完成了重投 |
| 只有各服务装配起来才出现的故障 | 近生产端到端 | 受控身份、API、数据库、队列和 worker 组成的完整旅程 | 一个健康探针就证明用户旅程正确 |

本章后面展开 API 集成和数据库集成两行。另外三行在本案例里各有一个具体用法：

**契约测试。** 已发布的客户端依赖响应里的哪些字段，要用标明必需字段的已发布 schema，或旧客户端依赖的固定响应样例来比较。本服务生成的 OpenAPI 只描述“现在”的声明，不记得过去答应过什么（见后文 OpenAPI 一节）。字段该怎样演进、什么算破坏性变更，见[怎样让调用方可靠地判断 API 的成功、失败和变化？](#37.%20%E6%80%8E%E6%A0%B7%E8%AE%A9%E8%B0%83%E7%94%A8%E6%96%B9%E5%8F%AF%E9%9D%A0%E5%9C%B0%E5%88%A4%E6%96%AD%20API%20%E7%9A%84%E6%88%90%E5%8A%9F%E3%80%81%E5%A4%B1%E8%B4%A5%E5%92%8C%E5%8F%98%E5%8C%96%EF%BC%9F)。

**消息代理集成。** 要证明“worker 没确认就崩溃时，消息会被重新投递，而重复投递只推进一次状态”，必须让真实代理参与：用与生产相同的确认模式消费消息，在 ACK 之前终止消费者，再观察代理重新投递，以及数据库里的条件更新只成功一次。在本地把处理函数连调两次，只验证了数据库那一半。代理的确认语义见[发布确认、消费者确认和业务完成各证明什么？](#44.%20%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)。

**近生产端到端。** 部署装配上的错误（配置、凭据、网络、服务之间的版本组合）只有装起整条链路才会出现。旅程要用受控的身份走完“读取—导出—下载”，而不是看一个健康探针是否返回 `200`。发布后的生产冒烟用 `user-17`、`user-29` 两个受控身份钉到新版本上，属于同一类检查，见[新版本怎样逐步放量，出问题时能撤回什么？](#60.%20%E6%96%B0%E7%89%88%E6%9C%AC%E6%80%8E%E6%A0%B7%E9%80%90%E6%AD%A5%E6%94%BE%E9%87%8F%EF%BC%8C%E5%87%BA%E9%97%AE%E9%A2%98%E6%97%B6%E8%83%BD%E6%92%A4%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)。

浏览器侧的测试边界见[前端测试该在哪一层证明什么？](../../frontend/delivery/frontend-testing-strategy.md)。

### 测试必须能区分对错

一组测试有没有用，不看它是否通过，而看它能不能把正确实现和错误实现分开。原有测试只让 `user-17` 读自己的报表：查询退化成只按全局主键读取后，它照样通过。这样的测试对这类回归没有任何区分力。

**判据：删掉条件，测试必须失败。** 证明区分力的方法很直接：把要守的条件从实现里拿掉（或换回已知错误的写法），至少一条测试必须变红。思路与 mutation testing (变异测试) 相同：人为制造一个已知错误的版本，看测试能否把它“杀死”。本例中，把查询换回 `session.get(Report, report_id)` 后，所有者那条检查仍然通过，只有 `user-29` 经 acct-29 读 42 的那条失败。正是这条跨账户反例承担了全部区分力。

**断言要精确到能排除泄露。** 只断言 `404` 不够；要断言 `user-29` 读 42 的正文与读不存在的 43 完全相同，才能证明响应没有带出 acct-17 的数据或归属。

**独立阅读实现与测试。** 同一个人或同一个 AI 模型同时写出的实现和测试，可能共享同一个遗漏的假设，测试全绿不说明漏掉的条件已经被检查。审查时，从需求列出“哪些请求必须被拒绝”，再分别读实现和测试：

- **实现侧**：改动后的公开路由、调用方、认证依赖、实际读取（SQL 查询还是 identity map 返回）、事务、缓存和响应分支。
- **测试侧**：是否用了归属不同的可信主体；是否经过被修改的入口；fixture (测试夹具) 接的是不是预期的数据库；断言有没有检查“不该发生的成功响应”。

**每种替身只覆盖自己那一层。** 模拟的会话、本地的重复调用、健康探针，各自只证明它所在那一层的事实。结论若涉及数据库约束、消息代理重投或部署装配，先确认测试真的用了目标数据库、真实代理或部署路径。

### API 集成测试：保留真实路由，只替换身份

读取契约要用 API 集成测试验证：真实的路由、成员检查、查询、序列化和错误映射都参与，只有“当前主体是谁”由测试提供。示例定义了一个测试专用依赖，从请求头 `X-Test-Principal` 读取主体。它只是测试接缝（为测试预留的替换点），不是生产认证：生产环境的主体必须来自已验证的会话或令牌，不能信任客户端填写的请求头。对已有的 FastAPI 应用，也可以在测试里用 `app.dependency_overrides` 替换认证依赖，同时保留真实路由。

示例把契约表写成一个函数 `contract_violations`，逐条重放并返回违反的条目；同一个函数分别跑在修复后的实现和回归实现上：

| 实现 | `contract_violations` 的结果 | 说明 |
| --- | --- | --- |
| 显式查询 `(account_id, report_id)` | `[]` | 三条读取契约全部满足 |
| `session.get(Report, report_id)` | `["user-29 经 acct-29 读 42"]` | `user-29` 得到 `200` 和 `Service health`；所有者检查和经 acct-17 的那条仍通过 |

第二行就是区分力的证据：回归实现只在跨账户反例上失败。实际项目里不必把回归实现永久留在测试套件中，在审查时临时换回一次、确认测试变红即可；示例保留它，是为了让这次判定可以重放。

另外三项边界各自验收：

- **认证。** 不带主体的请求得到 `401`，并断言 `WWW-Authenticate: Bearer realm="reports"` 质询头（本例假设生产用 Bearer 令牌；真实令牌校验由认证层自己的测试负责）。
- **参数校验。** `GET /v1/accounts/acct-17/reports/not-a-number` 因整数路径参数校验失败得到 `422`。
- **进程内调用的边界。** `TestClient` 在进程内调用应用，不建立真实的 HTTP socket；但 SQLAlchemy 会把查询交给 SQLite 真正执行，所以查询条件是真的被检验了。

本例为简化，错误正文用 FastAPI 默认的 `{"detail": "report not found"}`；生产 API 的错误格式见 API 契约章。认证之后的逐次授权规则（成员、动作、缓存与后台任务）见[服务怎样逐次确认这个主体能对这份资源做这个动作？](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)。

> [!example]- 完整 FastAPI + SQLAlchemy + SQLite 测试（`test_report_scope.py`）
> 每个测试由 function scope (函数作用域) 的 fixture 建立独立的内存数据库和应用。`StaticPool` 让串行访问复用同一个 SQLite 连接，使路由读到已准备的数据；它不支持并发事务，这组设置不能用于并发测试。运行：`python -m pytest -q test_report_scope.py`，预期 `4 passed`。
>
> ~~~python
> from typing import Annotated, Callable
>
> import pytest
> from fastapi import Depends, FastAPI, Header, HTTPException
> from fastapi.testclient import TestClient
> from sqlalchemy import create_engine, select
> from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
> from sqlalchemy.pool import StaticPool
>
>
> class Base(DeclarativeBase):
>     pass
>
>
> class Report(Base):
>     __tablename__ = "reports"
>     report_id: Mapped[int] = mapped_column(primary_key=True)  # 本例：全局主键
>     account_id: Mapped[str]
>     title: Mapped[str]
>
>
> class Membership(Base):
>     __tablename__ = "memberships"
>     account_id: Mapped[str] = mapped_column(primary_key=True)
>     principal_id: Mapped[str] = mapped_column(primary_key=True)
>
>
> def scoped_read(session: Session, account_id: str, report_id: int):
>     return session.scalar(
>         select(Report).where(
>             Report.account_id == account_id,
>             Report.report_id == report_id,
>         )
>     )
>
>
> def regressed_read(session: Session, account_id: str, report_id: int):
>     return session.get(Report, report_id)  # 回归：只按全局主键
>
>
> def create_app(read_row: Callable) -> FastAPI:
>     engine = create_engine(
>         "sqlite+pysqlite://",
>         connect_args={"check_same_thread": False},
>         poolclass=StaticPool,
>     )
>     Base.metadata.create_all(engine)
>     with Session(engine) as session, session.begin():
>         session.add_all([
>             Membership(account_id="acct-17", principal_id="user-17"),
>             Membership(account_id="acct-29", principal_id="user-29"),
>             Report(report_id=42, account_id="acct-17", title="Service health"),
>         ])
>
>     app = FastAPI()
>     app.state.engine = engine
>
>     def principal_from_test_header(
>         x_test_principal: Annotated[str | None, Header()] = None,
>     ) -> str:
>         # 测试接缝：生产环境的主体来自已验证的会话或令牌，不来自请求头
>         if not x_test_principal:
>             raise HTTPException(
>                 status_code=401,
>                 detail="authentication required",
>                 headers={"WWW-Authenticate": 'Bearer realm="reports"'},
>             )
>         return x_test_principal
>
>     @app.get(
>         "/v1/accounts/{account_id}/reports/{report_id}",
>         responses={401: {"description": "Unauthenticated"}, 404: {"description": "Not found"}},
>     )
>     def read_report(
>         account_id: str,
>         report_id: int,
>         principal: Annotated[str, Depends(principal_from_test_header)],
>     ):
>         with Session(engine) as session:
>             member = session.scalar(
>                 select(Membership).where(
>                     Membership.account_id == account_id,
>                     Membership.principal_id == principal,
>                 )
>             )
>             report = read_row(session, account_id, report_id) if member else None
>             if report is None:
>                 raise HTTPException(status_code=404, detail="report not found")
>             return {"report_id": report.report_id, "title": report.title}
>
>     return app
>
>
> def contract_violations(client: TestClient) -> list[str]:
>     """按读取契约逐条重放，返回违反的条目；空列表表示全部满足。"""
>     def get(principal: str, path: str):
>         return client.get(path, headers={"X-Test-Principal": principal})
>
>     missing = get("user-29", "/v1/accounts/acct-29/reports/43")
>     checks = {
>         "user-17 读自己账户的 42":
>             lambda r: r.status_code == 200
>             and r.json() == {"report_id": 42, "title": "Service health"},
>         "user-29 经 acct-29 读 42":
>             lambda r: r.status_code == 404 and r.json() == missing.json(),
>         "user-29 经 acct-17 读 42":
>             lambda r: r.status_code == 404 and r.json() == missing.json(),
>     }
>     responses = {
>         "user-17 读自己账户的 42": get("user-17", "/v1/accounts/acct-17/reports/42"),
>         "user-29 经 acct-29 读 42": get("user-29", "/v1/accounts/acct-29/reports/42"),
>         "user-29 经 acct-17 读 42": get("user-29", "/v1/accounts/acct-17/reports/42"),
>     }
>     return [name for name, ok in checks.items() if not ok(responses[name])]
>
>
> @pytest.fixture
> def client():
>     app = create_app(scoped_read)
>     with TestClient(app) as test_client:
>         yield test_client
>     app.state.engine.dispose()
>
>
> def test_scoped_read_meets_contract(client):
>     assert contract_violations(client) == []
>
>
> def test_contract_detects_regressed_read():
>     app = create_app(regressed_read)
>     with TestClient(app) as regressed:
>         assert contract_violations(regressed) == ["user-29 经 acct-29 读 42"]
>     app.state.engine.dispose()
>
>
> def test_authentication_and_validation(client):
>     anonymous = client.get("/v1/accounts/acct-17/reports/42")
>     malformed = client.get(
>         "/v1/accounts/acct-17/reports/not-a-number",
>         headers={"X-Test-Principal": "user-17"},
>     )
>     assert anonymous.status_code == 401
>     assert anonymous.headers["www-authenticate"] == 'Bearer realm="reports"'
>     assert malformed.status_code == 422
>
>
> def test_openapi_declares_error_responses(client):
>     operation = client.get("/openapi.json").json()["paths"][
>         "/v1/accounts/{account_id}/reports/{report_id}"
>     ]["get"]
>     assert {"200", "401", "404", "422"} <= set(operation["responses"])
> ~~~

### 自动生成的 OpenAPI 不证明兼容

示例里的 `test_openapi_declares_error_responses` 检查本应用声明了 `200/401/404/422` 四种响应。它只说明“当前声明了什么”。本例路由没有设置 `response_model`，生成的 200 响应 schema 是 `{}`，没有把 `title` 标为必需字段；即使有人删掉 `title`，这条 OpenAPI 检查照样通过。

在本例里，能发现字段被删的是契约函数中那条精确的 JSON 断言。要验证已发布客户端的兼容性，仍要拿标明必需字段的已发布 schema，或旧客户端依赖的固定响应来比较。

### 重复处理：用约束和条件更新守住，并精确断言

第二条契约靠数据库守住，需要数据库集成测试。它有两半：

- **重复提交。** 幂等记录以 `(account_id, principal_id, idempotency_key)` 为主键。同一个 `(acct-17, user-17, export-demo-415)` 再次插入时必须撞上主键，原映射 `job-demo-731` 保持不变。应用层随后怎样回查并返回原任务，见[两个请求争夺最后一件库存时，怎样保证只预留一次？](#22.%20%E4%B8%A4%E4%B8%AA%E8%AF%B7%E6%B1%82%E4%BA%89%E5%A4%BA%E6%9C%80%E5%90%8E%E4%B8%80%E4%BB%B6%E5%BA%93%E5%AD%98%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E5%8F%AA%E9%A2%84%E7%95%99%E4%B8%80%E6%AC%A1%EF%BC%9F)。
- **重复投递。** worker 用条件更新领取任务：只有 `status = 'queued'` 的行才能改成 `running` 并把 `attempt` 加一。第一次影响 1 行，第二次影响 0 行。

| 操作 | 数据库返回的信号 | 之后保留的状态 |
| --- | --- | --- |
| 首次受理：插入幂等记录 → `job-demo-731`，插入任务 `queued`、`attempt=0` | 影响 1 行 | 两行都已提交 |
| 同键重放，换成候选任务 `job-duplicate` 再插入 | `SQLITE_CONSTRAINT_PRIMARYKEY`，事务回滚 | 原映射仍指向 `job-demo-731`，没有多出一行 |
| 第一次投递：`queued → running` | 影响 1 行 | `running`、`attempt=1` |
| 第二次投递，同样的条件 | 影响 0 行 | 仍是 `running`、`attempt=1` |

**断言要精确，否则会假阳性。** 冲突测试要断言具体的错误码和完整的原行：

- 只数“仍是一行”：如果实现用了 `INSERT OR REPLACE`，原行被删掉、换成指向 `job-duplicate` 的新行，行数仍是 1，测试照样通过。
- 只捕获任意 `IntegrityError`：非空约束失败（`SQLITE_CONSTRAINT_NOTNULL`）也是 `IntegrityError`，会被误当成主键冲突。

**这组测试不能声称什么。** 它是串行的轨迹，不能据此说多个 worker 并发争用时的行为已经测过；它没有连接消息代理，本地执行两次更新不等于代理完成了重投。真实的领取还要先占执行槽、检查 `available_at`、设置租约，完整条件见[怎样保证一个任务同一时刻只由一个 worker 推进？](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)。

> [!example]- 用标准库 SQLite 重放唯一键与条件领取
> 这段独立示例只执行本地数据库约束，没有消息代理，也没有并发 worker。运行 `python dedupe.py`，预期输出 `SQLITE_CONSTRAINT_PRIMARYKEY 1 0 ('job-demo-731', 'running', 1)`。
>
> ~~~python
> import sqlite3
>
> db = sqlite3.connect(":memory:")
> db.executescript("""
> CREATE TABLE idempotency_records (
>     account_id      TEXT NOT NULL,
>     principal_id    TEXT NOT NULL,
>     idempotency_key TEXT NOT NULL,
>     job_id          TEXT NOT NULL,
>     PRIMARY KEY (account_id, principal_id, idempotency_key)
> );
> CREATE TABLE jobs (
>     job_id  TEXT PRIMARY KEY,
>     status  TEXT NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
>     attempt INTEGER NOT NULL
> );
> """)
> record = ("acct-17", "user-17", "export-demo-415")
>
> # 首次受理：幂等记录与 job 同一事务提交
> with db:
>     first_insert = db.execute(
>         "INSERT INTO idempotency_records VALUES (?, ?, ?, ?)", (*record, "job-demo-731")
>     ).rowcount
>     db.execute("INSERT INTO jobs VALUES ('job-demo-731', 'queued', 0)")
>
> # 同键重放却带着新的候选 job：必须撞上主键，而不是替换原映射
> try:
>     with db:
>         db.execute(
>             "INSERT INTO idempotency_records VALUES (?, ?, ?, ?)", (*record, "job-duplicate")
>         )
> except sqlite3.IntegrityError as error:
>     conflict = error.sqlite_errorname
> else:
>     raise AssertionError("duplicate key was accepted")
>
> assert conflict == "SQLITE_CONSTRAINT_PRIMARYKEY", conflict
> assert db.execute("SELECT * FROM idempotency_records").fetchall() == [(*record, "job-demo-731")]
>
> # 同一 job 被投递两次：只有一次 queued -> running 能成功
> claim = (
>     "UPDATE jobs SET status = 'running', attempt = attempt + 1 "
>     "WHERE job_id = 'job-demo-731' AND status = 'queued'"
> )
> with db:
>     first_claim = db.execute(claim).rowcount
> with db:
>     second_claim = db.execute(claim).rowcount
>
> assert (first_insert, first_claim, second_claim) == (1, 1, 0)
> assert db.execute("SELECT * FROM jobs").fetchall() == [("job-demo-731", "running", 1)]
> print(conflict, first_claim, second_claim, db.execute("SELECT * FROM jobs").fetchone())
> ~~~

### 本地测试管不到的两件事

**远端副作用。** 如果重复处理的任务还会付款、发邮件或通知其他服务，本地条件更新撤回不了已经发生的远端动作。transactional outbox (事务发件箱，之后 outbox) 让业务行与待发消息在同一事务里提交，但 relay (中继) 故障恢复后仍可能再发一次；所以外部动作还要带上对端认可的幂等键，或事后对照权威记录对账修复。单靠 outbox 挡不住远端的重复付款。远端操作键怎样构造、结果不明时怎样决策，见[写请求超时后，怎样查清结果并安全重试？](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)；outbox 本身见[耗时任务怎样被持久受理，并保证一定会被唤醒？](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)。

**测试证据要追溯到产物。** 测试通过之后，改动还要经过提交、构建和发布。测试结果应能追溯到对应的提交、测试输入和实际产物：CI 固定一个源码提交，用该快照构建镜像，发布流程晋级的是同一份通过检查的镜像。不能把“源码上的测试通过”说成另一次重新构建的镜像也验证过了，见[已验证的产物怎样原样晋级到生产？](#57.%20%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E4%BA%A7%E7%89%A9%E6%80%8E%E6%A0%B7%E5%8E%9F%E6%A0%B7%E6%99%8B%E7%BA%A7%E5%88%B0%E7%94%9F%E4%BA%A7%EF%BC%9F)。

### 本章产出与下一步

本章产出一组有区分力的测试：契约函数在修复后的实现上返回 `[]`，在 `Session.get` 回归上只报告跨账户那一条；重复提交与重复投递由主键和条件更新守住，断言精确到错误码和原行。测试边界表说明了它们各自证明到哪一层为止。

这组测试读的是工作区里的文件。下一章[Git 怎样记录一次改动，出错时又怎样按层撤回？](#54.%20Git%20%E6%80%8E%E6%A0%B7%E8%AE%B0%E5%BD%95%E4%B8%80%E6%AC%A1%E6%94%B9%E5%8A%A8%EF%BC%8C%E5%87%BA%E9%94%99%E6%97%B6%E5%8F%88%E6%80%8E%E6%A0%B7%E6%8C%89%E5%B1%82%E6%92%A4%E5%9B%9E%EF%BC%9F)回答：怎样保证被测的那份内容，正是要提交、要交给 CI 构建的那份快照。

> [!info]- 来源
> - **TestClient 在进程内调用应用、不建立真实 socket**（“API 集成测试”）：FastAPI, [Testing](https://fastapi.tiangolo.com/tutorial/testing/)、[TestClient 参考](https://fastapi.tiangolo.com/reference/testclient/)，核对于 2026-11-12。
> - **用 `dependency_overrides` 替换认证依赖、保留真实路由**（“API 集成测试”）：FastAPI, [Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)，核对于 2026-11-12。
> - **响应模型决定 OpenAPI schema；未设 `response_model` 时 200 schema 为 `{}`**（“自动生成的 OpenAPI 不证明兼容”）：FastAPI, [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)，核对于 2026-11-12；`{}` 为本地运行结果。
> - **fixture 注入与默认 function scope**（完整测试折叠块）：pytest, [How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)，核对于 2026-11-12。
> - **SQLite 内存库与 `StaticPool` 只适合串行访问**（完整测试折叠块）：SQLAlchemy 2.0, [SQLite dialect — Using a Memory Database in Multiple Threads](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#using-a-memory-database-in-multiple-threads-or-coroutines)，核对于 2026-11-12。
> - **主键与唯一约束；`REPLACE` 会删除冲突的原行；扩展错误码区分主键与非空约束**（“重复处理”）：SQLite, [CREATE TABLE](https://www.sqlite.org/lang_createtable.html)、[ON CONFLICT](https://sqlite.org/lang_conflict.html)、[Result and Error Codes](https://www.sqlite.org/rescode.html)，核对于 2026-11-12。
> - **Bearer 质询的认证参数**（“API 集成测试”的 401 断言）：IETF [RFC 6750 §3](https://www.rfc-editor.org/rfc/rfc6750.html#section-3)；401 必须带适用的 `WWW-Authenticate`：[RFC 9110 §15.5.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.2)，核对于 2026-11-12。
> - **outbox 的本地原子写入不消除重复消息**（“本地测试管不到的两件事”）：AWS Prescriptive Guidance, [Transactional outbox pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)，核对于 2026-11-12。
> - **发布确认与消费者 ACK 是不同的交接边界**（“测试边界”表的消息代理一行）：RabbitMQ 4.4, [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)，核对于 2026-11-12。**消费者未 ACK 就终止（通道或连接关闭）时，消息重新入队并再投递**（“消息代理集成”）：RabbitMQ, [Tutorial 2: Work Queues — Message acknowledgment](https://www.rabbitmq.com/tutorials/tutorial-two-python)，核对于 2026-11-25。本章示例没有执行 RabbitMQ。
> - **本地运行环境**：Python 3.11.13、FastAPI 0.128.0、Starlette 0.47.2、HTTPX 0.28.1、SQLAlchemy 2.0.44、pytest 9.0.2、SQLite 3.51.0。版本只描述本次复现环境。
## 54. Git 怎样记录一次改动，出错时又怎样按层撤回？

本章回答：Git 把一次改动依次存在哪几层，怎样保证提交里的内容正是测试过的那份快照，整合别人的提交时怎样守住语义，以及出错时怎样按改动所在的层选恢复命令。读者手上有上一章通过的测试和修复后的代码，它们此刻还只是磁盘上的文件。

**案例。** 沿用主线五的报表服务修复。修复只涉及两个文件：`src/reports.py` 把读取改成按 `(account_id, report_id)` 显式查询，`tests/test_report_scope.py` 加入跨账户反例。开发者在分支 `fix/report-account-scope` 上工作，要把这份已审查的源码快照变成一个可追溯的提交，交给 CI 构建。文中的提交 ID 是示意值：rebase 前的修复提交记作 `6ab06f8`，rebase 后成为 `c4f2a91`，后续构建章都从 `c4f2a91` 接手。

### 一次改动停在哪一层

Git 里的改动依次经过四层状态。下图从上往下画出每一层是什么、哪条命令把改动推进下一层，右侧括号标出两条比较命令各看哪两层：

![改动自上而下经过工作区、暂存区、提交与分支、远端：git add 复制执行那一刻的内容，git commit 写成提交并移动分支，git push 共享引用；git diff 比较工作区与暂存区，git diff --cached 比较暂存区与 HEAD。](../../engineering-foundations/practice/resources/git-change-layers.svg)

本章只讨论在分支上工作的常见情况：`HEAD` 指向当前分支，分支指向当前提交，提交成功后分支移动到新提交。分清改动停在哪一层，后面才能选对比较命令和恢复命令。

### 被测快照必须等于提交快照

`git add` 复制的是**执行那一刻**的文件内容。之后继续编辑，暂存区不会跟着变。下面追踪 `src/reports.py` 的三个版本：`v0` 是原内容，`v1` 加上账户条件，`v2` 又补了错误处理。表中每格是该层保存的文件内容：

| 执行到哪一步 | 工作区 | 暂存区 | HEAD 提交 |
| --- | --- | --- | --- |
| 编辑为 `v1` | `v1` | `v0` | `v0` |
| `git add src/reports.py` | `v1` | `v1` | `v0` |
| 再编辑为 `v2`，没有再次 add | `v2` | `v1` | `v0` |
| `git commit` | `v2` | `v1` | `v1` |

最后一步只提交了账户条件，错误处理仍是未暂存的改动：此刻 `git diff` 显示 `v1` 到 `v2` 的错误处理，`git diff --cached` 为空。

问题在于测试通常读取工作区里的文件。`v2` 通过了测试，不能说明只含 `v1` 的提交也能通过。所以验收要让被测内容与准备提交的快照一致：要么先把工作区整理到与暂存区相同再测试，要么在隔离目录里测试待提交的快照，例如用 `git worktree` 检出一份干净副本。工作区混有其他任务的改动时，后一种做法更可靠。

### 只把这次修复放进提交

两个常见误解会让提交混进无关内容：

- **创建分支不保存改动。** `git switch -c <name>` 只新建一个指向当前提交的引用，未提交的改动会跟着留在工作区和暂存区。切换任务前要保护它们，应先提交，或用 `git stash` 搁置。
- **按路径暂存不是“只暂存这次修复”。** `git add <path>` 不会移除暂存区里原有的其他改动，而且会暂存所选文件的**全部**修改，包括与本次修复无关的部分。

所以流程是：先看全貌，再按路径暂存，最后检查完整的暂存差异。

~~~bash
git status --short
git diff -- src/reports.py tests/test_report_scope.py

git add src/reports.py tests/test_report_scope.py
git diff --cached           # 只应出现本次修复的文件和代码块
git diff --cached --check   # 检查空白错误和遗留的冲突标记
~~~

### 把提交和验收证据绑在同一个 ID 上

对准备提交的同一份内容跑完测试，再创建提交：

~~~bash
git commit -m "fix(reports): scope report reads by account"
git show --stat --oneline HEAD
~~~

提交 ID 是后续一切证据的锚点：CI 在哪个提交上运行、镜像由哪个提交构建、发布了哪个镜像，都要能追溯到它。若验收依赖提交后的 CI，就核对实际通过检查的是哪一个提交 ID，再晋级产物。任何会改变提交 ID 的操作（rebase、cherry-pick、squash）之后，旧 ID 上的检查结果不再自动适用于新提交。

commit message (提交说明) 描述改了什么、改的对象是谁。`fix(reports): ...` 是 Conventional Commits (约定式提交) 格式，属于团队约定，不是 Git 的要求；仓库若规定 squash、merge commit 或签名提交，按仓库策略执行。标题写得好不代表测试通过，审查要看实际的差异和测试覆盖。

### 整合前先看清两边：fetch 与三点比较

提交只在本地分支上。推送或发起合并前，先看远端 `main` 在此期间是否有了新提交：

- `git fetch`（获取）只更新 `origin/main` 这类远程跟踪引用，不改当前分支。
- `git pull`（拉取）在获取后立即按配置执行合并或变基。

更稳妥的做法是先获取，看清两边差异，再决定怎样整合：

~~~bash
git fetch origin
git log --left-right --oneline --graph HEAD...origin/main
~~~

三点写法 `HEAD...origin/main` 配合 `--left-right`，列出两边各自独有的提交。本案例获取后的历史如下，`>` 一侧是同事的提交：为减少读取量，他把同一行改成了延迟加载报表正文。

![共同祖先之后分成两支：origin/main 上是 perf(reports): defer report body，标为 >；本地分支 fix/report-account-scope 上是修复提交 6ab06f8，标为 <。](../../engineering-foundations/practice/resources/git-before-rebase.svg)

两点写法 `HEAD..origin/main` 只列远端独有的提交，即图中 `>` 那一支，看不出本地是否还有没推送的提交。

### merge 还是 rebase

| 当前状态 | 常见做法 | 原因 |
| --- | --- | --- |
| 本地分支还没推送，只有自己用过 | 按仓库策略 rebase (变基) 或 merge (合并) | rebase 把本地提交重放到新基点上，生成新的提交 ID；merge 保留两侧历史，必要时生成合并提交 |
| 别人已基于这个分支继续提交 | 先协调，通常不改写共享提交 | 改写后提交 ID 不同，别人的分支仍基于旧提交，要重新整合两条历史 |
| 仓库要求保留合并节点 | `git merge --no-ff` | 普通 merge 在可快进时只移动分支；`--no-ff` 为这次合并创建节点 |

两个容易误解的边界：如果当前提交是远端提交的祖先（本地没有新提交），`git merge` 会 fast-forward (快进)，直接移动分支，不新增合并提交；如果远端没有本地缺少的提交，就没有需要整合的东西，也不会凭空生成合并节点。具体用哪种，以仓库现行策略为准，不要套用某个通用分支模型。

本案例的分支还没推送，团队约定用 rebase：`git rebase origin/main`。下图是 rebase 完成后的历史，也标出了重放时冲突两侧各是谁：

![rebase 把 6ab06f8 重放到 perf 之后，得到新提交 c4f2a91，分支移到它上面，旧提交不再被分支指向；重放冲突时 ours 即 HEAD 是上游 perf 一侧，theirs 是本地修复；CI 要在新 ID 上重跑。](../../engineering-foundations/practice/resources/git-after-rebase.svg)

### 冲突按语义不变量解决

rebase 在 `src/reports.py` 上停了下来，因为两边改了同一行：

~~~text
<<<<<<< HEAD
    report = session.get(Report, report_id, options=[defer(Report.body)])
=======
    report = session.scalar(
        select(Report).where(
            Report.account_id == account_id,
            Report.report_id == report_id,
        )
    )
>>>>>>> 6ab06f8 (fix(reports): scope report reads by account)
~~~

两侧各守着一件事：上游要延迟加载正文，修复要同时按账户和报表过滤。解决冲突的标准是**语义不变量**，而不是挑一侧：无论上游怎样改写这段查询，结果都必须同时保留两个过滤条件，再合进上游真正想要的改动：

~~~python
    report = session.scalar(
        select(Report)
        .options(defer(Report.body))
        .where(
            Report.account_id == account_id,
            Report.report_id == report_id,
        )
    )
~~~

**rebase 时 ours 和 theirs 是反的。** rebase 把本地提交一个个重放到上游之上，所以冲突里的 `HEAD`（ours）是上游那一侧，即上面同事那行 `session.get`，theirs 才是本地修复。不看内容就执行 `git checkout --ours src/reports.py`，等于把越权缺陷原样恢复；整块接受 theirs，则丢掉了上游的改动。不理解冲突内容时，两种整块接受都不要做。

解决后的检查顺序：

1. 用 `git diff --cc` 和源文件确认冲突标记都已清除。
2. 运行测试；跨账户反例会拦住误选上游一侧的结果。
3. 暂存并继续：`git add src/reports.py`，然后 `git rebase --continue`（如果进行的是 merge，用 `git merge --continue`；先看 `git status` 确认当前操作）。

rebase 完成后得到上一节图中的 `c4f2a91`。CI 必须在新 ID 上重新验证，“证据绑定提交 ID”的规则在这里生效。

**想放弃整合时：**

- `git rebase --abort` 回到变基前的状态。
- `git merge --abort` 回到合并前的状态。但如果开始合并时已有未提交的改动，Git 在某些情况下无法完整还原它们，所以整合前最好让工作区保持干净。

### 临时搁置与跨分支带修复：stash 与 cherry-pick

这是两种不同的需求。

**临时切走：`git stash`。** 修复做到一半要去处理别的任务时：

- `git stash push -m "report scope in progress"` 保存已跟踪文件在工作区和暂存区的改动；默认不含未跟踪文件，需要时加 `-u`。
- `git stash apply` 默认只恢复改动内容，不恢复“哪些改动原先已暂存”；要同时恢复暂存划分，用 `git stash apply --index`。
- `apply` 保留这条 stash 记录；`pop` 在应用成功后删除它。
- 应用后检查状态和冲突。stash 不是备份，重要工作仍应保存在提交里。

**把修复带到另一个分支：`git cherry-pick`。** `git cherry-pick <commit>` 把指定提交引入的改动应用到当前分支，并创建一个**新**提交。它适合把已审查的修复带到维护分支；新提交的 ID 与原提交不同，所以维护分支上要重新记录检查在哪个提交上运行、构建用的是哪个提交。

### 按变化所在层恢复

出错时，先判断要撤销的改动停在哪一层，再选命令。下图沿用上面的四层：右侧箭头是 restore 从哪一层把内容复制回哪一层，左侧竖条是 `git reset` 各选项改动的层，共享边界以下只用 revert：

![restore --staged 把暂存区恢复为 HEAD 的版本，restore 把工作区恢复为暂存区的版本；reset --soft 只移动分支，--mixed 还重置暂存区，--hard 再改工作区，只用于未共享的本地提交；已共享的提交用 revert 新增反向提交；reflog 找回误移前的提交。](../../engineering-foundations/practice/resources/git-recovery-by-layer.svg)

图上放不下的条件和风险记在下表，它与上图一起是本领域恢复命令的权威版本：

| 命令 | 什么时候用，风险是什么 |
| --- | --- |
| `git restore <path>` | 丢弃未暂存的编辑；被覆盖的编辑**无法找回** |
| `git reset --soft` 或 `--mixed <target>`（`--mixed` 是默认） | 重新划分未共享的本地提交，如把两个合成一个；改动留在暂存区或工作区 |
| `git reset --hard <target>` | 连同改动一起丢弃：受跟踪文件的改动被丢弃，可能覆盖同名的未跟踪文件，目标中没有的受跟踪文件被删除；先确认工作区内容可以丢弃 |
| `git revert -m 1 <merge-commit>` | 撤销已共享的合并提交；`-m` 指定以哪个父提交为主线；先检查反向差异，以及它对之后再次合并同一分支的影响 |
| `git reflog`，再 `git branch recovery/report-scope <commit-id>` | 分支被误移时找回原提交；reflog 只是本地记录，会过期，不同步到远端 |

撤销共享历史用 revert，不要把远端分支强制指回旧位置：别人可能已经基于那些提交工作了。

找回误移的提交后，先 `git show --stat recovery/report-scope` 检查这份快照，再决定是否推送。三个命令的分工可以这样记：reset 移动当前分支（并可重置暂存区和工作区），restore 恢复文件内容，revert 新增反向提交。

### 提交之后：交给构建，Git 管不到的部分

修复提交为构建系统提供了固定输入，但它还不是部署产物。之后要由 CI 用这个提交构建镜像，记录镜像摘要，验证并晋级那一份镜像。若仓库要求通过 PR 和状态检查后再发布，这些检查就是晋级条件。

Git 命令也只改变工作区、暂存区、提交和引用。`git revert` 撤回的是源码，不会撤销已执行的数据库迁移、已发布的镜像或其他生产副作用；这些要靠发布侧的回退和兼容设计处理。

下一章[源码怎样变成可运行、可追溯的容器镜像？](#55.%20%E6%BA%90%E7%A0%81%E6%80%8E%E6%A0%B7%E5%8F%98%E6%88%90%E5%8F%AF%E8%BF%90%E8%A1%8C%E3%80%81%E5%8F%AF%E8%BF%BD%E6%BA%AF%E7%9A%84%E5%AE%B9%E5%99%A8%E9%95%9C%E5%83%8F%EF%BC%9F)讲怎样从这个提交构建出可追溯的镜像；本主线把修复版本的镜像摘要记作 `d-new`。镜像怎样按摘要晋级见[已验证的产物怎样原样晋级到生产？](#57.%20%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E4%BA%A7%E7%89%A9%E6%80%8E%E6%A0%B7%E5%8E%9F%E6%A0%B7%E6%99%8B%E7%BA%A7%E5%88%B0%E7%94%9F%E4%BA%A7%EF%BC%9F)，发布后能撤回什么见[新版本怎样逐步放量，出问题时能撤回什么？](#60.%20%E6%96%B0%E7%89%88%E6%9C%AC%E6%80%8E%E6%A0%B7%E9%80%90%E6%AD%A5%E6%94%BE%E9%87%8F%EF%BC%8C%E5%87%BA%E9%97%AE%E9%A2%98%E6%97%B6%E8%83%BD%E6%92%A4%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - **工作区、暂存区与提交的差异；`--check` 检查空白错误与冲突标记**（“一次改动停在哪一层”“被测快照必须等于提交快照”“只把这次修复放进提交”）：Git 手册 [git-status](https://git-scm.com/docs/git-status)、[git-diff](https://git-scm.com/docs/git-diff)、[git-add](https://git-scm.com/docs/git-add)、[git-commit](https://git-scm.com/docs/git-commit)、[git-worktree](https://git-scm.com/docs/git-worktree)，核对于 2026-11-06。
> - **fetch 与 pull、三点与两点区间、merge 快进与 `--no-ff`、`merge --abort` 的限制**（“整合前先看清两边”“merge 还是 rebase”“冲突按语义不变量解决”）：Git 手册 [git-fetch](https://git-scm.com/docs/git-fetch)、[git-pull](https://git-scm.com/docs/git-pull)、[git-log](https://git-scm.com/docs/git-log)、[git-merge](https://git-scm.com/docs/git-merge)，核对于 2026-11-06。
> - **rebase 重放提交、冲突时 ours/theirs 对调**（“冲突按语义不变量解决”）：Git 手册 [git-rebase](https://git-scm.com/docs/git-rebase)，“the side reported as ours is the so-far rebased series … and theirs is the working branch”；冲突标记的形式与 rebase 后提交 ID 改变为本地 Git 2.56.1 演示结果（文中 ID 为示意值），2026-11-25。
> - **stash 的范围与 `--index`、cherry-pick 创建新提交**（“临时搁置与跨分支带修复”）：Git 手册 [git-stash](https://git-scm.com/docs/git-stash)、[git-cherry-pick](https://git-scm.com/docs/git-cherry-pick)，核对于 2026-11-06。
> - **restore、reset 三种模式、revert 与 `-m`、reflog**（“按变化所在层恢复”）：Git 手册 [git-restore](https://git-scm.com/docs/git-restore)、[git-reset](https://git-scm.com/docs/git-reset)、[git-revert](https://git-scm.com/docs/git-revert)、[git-reflog](https://git-scm.com/docs/git-reflog)，核对于 2026-11-06，`--hard` 的措辞按本地 Git 2.56.1 手册；`restore`/`switch` 需要 Git 2.23 及以上。
## 55. 源码怎样变成可运行、可追溯的容器镜像？

沿用主线五的案例。报表服务的修复提交 `c4f2a91` 把读取改成按 `(account_id, report_id)` 显式查询，并带上了跨账户反例测试；[Git 章](#54.%20Git%20%E6%80%8E%E6%A0%B7%E8%AE%B0%E5%BD%95%E4%B8%80%E6%AC%A1%E6%94%B9%E5%8A%A8%EF%BC%8C%E5%87%BA%E9%94%99%E6%97%B6%E5%8F%88%E6%80%8E%E6%A0%B7%E6%8C%89%E5%B1%82%E6%92%A4%E5%9B%9E%EF%BC%9F)保证被测的快照就是这个提交的快照。本章把这份源码变成容器镜像：先分清镜像、容器和摘要，再看构建读到哪些文件、Dockerfile 怎样写才可审计、构建期凭据怎样不进镜像，最后看本地检查和 CI 发布为什么是两次不同的构建，以及摘要能证明什么、不能证明什么。

本章的产出是一个经 registry (镜像仓库) 核验的不可变引用 `registry.example.com/team/report-api@sha256:…`，本主线把这个摘要记作 `d-new`（生产上仍带着跨账户缺陷的稳定版记作 `d-old`），外加一份把它和源码连起来的构建记录。

### 镜像、容器和摘要各是什么

报表服务的 API 和异步 worker 从同一份源码构建，运行时却是两个不同的进程。要说清它们共享什么、各自拥有什么，先区分几个对象：

- **container image (容器镜像)**：用只读层保存程序、依赖和默认配置（默认启动命令、工作目录、运行用户）。镜像不保存某个环境的数据库密码，那属于运行配置。
- **container (容器)**：运行时在镜像之上叠加这个容器独有的可写层，再加上进程命令和运行配置。删除容器，可写层里的改动随之丢失；要跨容器保留的数据（例如数据库文件）写进 volume (数据卷)。
- **image digest (镜像摘要)**：形如 `sha256:…`，由镜像清单的内容算出，内容不变它就不变。
- **tag (标签)**：如 `report-api:c4f2a91`，只是一个指向某份内容的名字，可以被移到别的内容上。

所以 API 与 worker 可以用同一个摘要启动，只换启动命令；它们共享镜像内容，各自有自己的可写层、进程和身份。

### 构建上下文和层缓存决定构建读到什么

一次 build (构建) 从 build context (构建上下文) 开始：Docker CLI 把指定的一组文件交给 builder (构建器)，Dockerfile 里的 `COPY` 只能取这组文件。`docker buildx build .` 中的 `.` 只有在它就是干净检出的 `c4f2a91` 源码根、且没有未跟踪的本机文件时，才代表这个提交。

发送之前，`.dockerignore` 按相对构建根目录的路径模式排除文件。它和 Git 的忽略规则互不替代，也不能把上下文之外的文件加进来。只写 `*.log` 只匹配根目录；`**` 可以匹配任意层目录（包括零层），所以 `**/*.log` 覆盖整个上下文。至少要排除版本库、虚拟环境、缓存、本机日志、真实 `.env` 和密钥文件：

~~~text
**/.git
**/.venv
**/__pycache__
**/*.py[cod]
**/*.log
**/.env
**/.env.*
**/secrets
~~~

BuildKit 按每条指令及其输入复用 build cache (构建缓存)：某一步的输入变了，这一步和之后的所有步骤都要重做。因此 Dockerfile 通常先复制依赖锁文件、安装依赖，再复制源码，只改源码时就不必重装依赖。

缓存命中不说明依赖仍是最新的，也不让构建自动可复现。基础镜像 tag、依赖索引或下载内容、目标平台和构建工具都可能变化，同一份源码分别重建，仍可能得到内容不同的镜像。这一点决定了下一章的做法：各环境晋级同一次构建的摘要，而不是各自重建。

### 一份可审计的 Python 多阶段 Dockerfile

报表服务用 Python，下面是它的两阶段 Dockerfile。示例写 tag 是为了好读；生产用的 Dockerfile 或构建参数要在每个 `FROM` 换成审核过的基础镜像摘要。

~~~dockerfile
# syntax=docker/dockerfile:1
FROM python:3.15-slim AS deps
WORKDIR /build
COPY requirements.lock .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --prefix=/install --require-hashes -r requirements.lock

FROM python:3.15-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=deps /install /usr/local
COPY --chown=10001:10001 app ./app
USER 10001:10001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
~~~

逐项看它为什么这样写：

- **基础镜像固定到摘要。** 单平台构建固定该平台的 manifest digest (清单摘要)；多平台构建可以固定已核验的 index digest (索引摘要)，由每个 stage (构建阶段) 按目标架构从中选出对应平台的清单。
- **依赖逐项校验。** `requirements.lock` 列出直接和传递依赖的精确版本与 SHA-256，`pip --require-hashes` 逐项校验下载内容。但锁文件只管运行时依赖：若某个包没有适用的 wheel (预构建安装包)、要从源码编译，pip 会为它另建一个隔离的构建环境，其中的 build backend (构建后端) 和 build-time dependencies (构建依赖) 不受这份锁文件约束，要另外审核和控制；编译器和头文件也只该出现在构建阶段。
- **多阶段与权限。** `COPY --from=deps` 只把安装好的依赖带进运行阶段，运行阶段只保留需要的共享库；非 root 的 `USER` 降低应用进程的权限。应用若要写文件，输出目录应放在受控的挂载点，而不是指望容器可写层在替换容器后还在。
- **监听地址。** Uvicorn 在容器内监听 `0.0.0.0:8080`，容器的网络接口才能收到映射进来的流量。若应用只绑定容器内的 `127.0.0.1`，宿主机的端口映射替它改不了监听地址，外部流量进不来。宿主机一侧发布到哪个地址是另一回事，见 [Compose 支线](#56.%20%E7%94%A8%20Compose%20%E5%9C%A8%E6%9C%AC%E5%9C%B0%E8%B5%B7%E4%B8%80%E5%A5%97%E6%9C%8D%E5%8A%A1%E6%97%B6%EF%BC%8C%E7%BD%91%E7%BB%9C%E3%80%81%E5%81%A5%E5%BA%B7%E6%A3%80%E6%9F%A5%E3%80%81%E5%AF%86%E9%92%A5%E5%92%8C%E6%95%B0%E6%8D%AE%E5%90%84%E6%80%8E%E6%A0%B7%E9%85%8D%EF%BC%9F)。

> [!info] 版本说明
> 示例用官方 `python:3.15-slim`（Python 3.15.2，核对于 2026-11-12）。实际项目要先确认框架、依赖和原生扩展都支持所选 Python 版本。

#### 启动命令由谁决定

`RUN` 在构建时执行，结果留在层里交给后续步骤；`CMD` 和 `ENTRYPOINT` 在容器启动时决定运行哪个进程，其中 `CMD` 是默认启动命令。用 exec form (JSON 数组形式) 书写时，应用直接成为容器里的 PID 1 (首个进程)，能亲自收到停止信号；平台怎样发这个信号、给多长宽限，见[生产运行时章](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)。

worker 复用同一镜像时只替换启动命令。Docker Compose 的覆盖规则是：

- `command` 替换镜像的 `CMD`。若镜像定义了 exec form 的 `ENTRYPOINT`，`command` 作为参数追加给它，不改写 `ENTRYPOINT`。
- Compose 设置了非空的 `entrypoint` 时，镜像默认的 `CMD` 被忽略。

本例镜像没有 `ENTRYPOINT`，所以 worker 写 `command: ["python", "-m", "app.worker"]` 就完整替换了默认的 Uvicorn 命令。

### 构建期凭据只在一条 RUN 里出现

若私有依赖源需要认证，用 BuildKit secret mount (构建密钥挂载) 只在某条 `RUN` 执行期间提供凭据文件：

~~~dockerfile
RUN --mount=type=secret,id=pip_config,target=/etc/pip.conf \
    python -m pip install --prefix=/install --require-hashes -r requirements.lock
~~~

调用构建时传 `--secret id=pip_config,src=/安全路径/pip.conf`。挂载本身不会把凭据写进镜像层。但 `RUN` 里的命令仍可能把它复制进产物、打印到日志或发到网络，所以 builder 和依赖源也必须可信，verbose 日志不能打印认证配置。不要把 token 放进 `ARG`、`ENV`、被 `COPY` 的文件或命令行参数：这些都会留在层、镜像配置或构建记录里。

### 本地 --load 与 CI --push 是两次输出

同一个提交会走两条构建路径。本地用 `--load` 把结果载入本机 image store (镜像存储)，方便启动容器检查；CI 用 `--push` 从干净检出另做一次构建，并发布到 registry。即使源码相同，两次构建也不能假定得到相同的摘要；本地摘要更不能证明 registry 收到了什么。

![同一受控提交分别进入本地 --load 检查和 CI --push 发布；两条路径各自产生摘要，只有 registry 路径经 imagetools inspect 核验后才交给运行环境。](../../engineering-foundations/practice/resources/docker-build-and-image.svg)

两段脚本结构相同，假设运行环境有 Bash、Docker Buildx 和 `jq`，当前目录是已确认干净的 `c4f2a91` 源码根：

- `mktemp` 为本次构建新建一个 metadata file (元数据文件)，避免构建失败后误读上一次的摘要；`set -euo pipefail` 让 buildx 一失败整串命令就停止。
- `jq -e` 要求本次文件里有格式正确的 `containerimage.digest`，缺字段或格式不对就失败。
- 本地路径接着用 `docker image inspect` 和 `history` 看本机镜像的配置与层；CI 路径则用 `imagetools inspect` 按摘要从 registry 读回实际清单，确认远端确实有这份内容。

> [!example]- 本地构建：读取本次 metadata，再 inspect 与 history
>
> ~~~bash
> set -euo pipefail
> metadata_file="$(mktemp "${TMPDIR:-/tmp}/report-api-build.XXXXXX")"
> trap 'rm -f "$metadata_file"' EXIT
>
> docker buildx build \
>   --load \
>   --metadata-file "$metadata_file" \
>   --tag report-api:c4f2a91 \
>   .
> digest="$(
>   jq -er '
>     ."containerimage.digest"
>     | select(type == "string" and test("^sha256:[0-9a-f]{64}$"))
>   ' "$metadata_file"
> )"
> printf 'Local build digest: %s\n' "$digest"
> docker image inspect report-api:c4f2a91
> docker image history report-api:c4f2a91
> ~~~

> [!example]- CI 发布：核验 registry 摘要后交给运行环境
>
> ~~~bash
> set -euo pipefail
> metadata_file="$(mktemp "${TMPDIR:-/tmp}/report-api-push.XXXXXX")"
> trap 'rm -f "$metadata_file"' EXIT
>
> docker buildx build \
>   --push \
>   --metadata-file "$metadata_file" \
>   --tag registry.example.com/team/report-api:c4f2a91 \
>   .
> digest="$(
>   jq -er '
>     ."containerimage.digest"
>     | select(type == "string" and test("^sha256:[0-9a-f]{64}$"))
>   ' "$metadata_file"
> )"
> registry_ref="registry.example.com/team/report-api@$digest"
> docker buildx imagetools inspect "$registry_ref"
> printf 'REPORT_IMAGE=%s\n' "$registry_ref"
> ~~~
>
> 这段命令会真实地向 registry 发布镜像；registry 地址、tag 和提交都是示意值。

本地 tag `report-api:c4f2a91` 只是别名，不会验证源码是否真的来自该提交。只有 `imagetools inspect` 通过后，CI 才把打印出的完整 `registry@sha256:…` 交给后续步骤，作为环境变量 `REPORT_IMAGE`，这就是 `d-new`。接收方若用 Compose 插值 `${REPORT_IMAGE:?…}`，它只拒绝空值，不检查值是不是摘要引用；传值的一方要保证传的是这次 push 核验过的引用。

> [!info]- 实例：本机能否载入多平台镜像（Docker Buildx，核对于 2026-11-12）
> `--load` 是 `--output=type=docker` 的 CLI 简写，本例只构建一个平台。本机能否载入多平台镜像取决于 builder 和 Engine 的 image store：classic image store (经典镜像存储) 不支持 image index 或 manifest list (清单列表)，载入不了多平台镜像；containerd image store 可以。Docker Engine 29.0 起新安装默认用 containerd image store，Docker Desktop 也默认用它；从旧版本升级的 Engine 可能仍是 classic store。当前 Buildx 探测到目标 Engine 支持 OCI importer 时会改走能导入多平台镜像的路径，否则多平台的 docker 导出会报错。无论哪种，本机输出和 metadata 都不能证明 registry 已收到镜像。

### 摘要标识内容，不证明来源

registry 摘要固定了镜像清单（或多平台 index）的内容：谁拿着 `d-new` 去拉取，得到的都是同一份内容。它回答不了“这份内容由哪个源码提交、用什么依赖构建”。CI 若检出错了提交、用了被篡改的依赖，产物照样有一个合法的摘要。

所以构建记录要把这些东西和摘要绑在一起：确切的提交 `c4f2a91`、依赖锁文件、基础镜像摘要、Buildx/BuildKit 版本、目标平台、构建参数和 CI 检查结果，并用可核验的 provenance attestation (构建来源证明) 把源码和产物关联起来。之后有人问“生产里这个摘要是从哪来的”，查的是这份记录，而不是摘要本身。

多平台构建还多一层：index digest 只证明它包含哪些平台子清单，不证明每个平台的子镜像都运行过；index 里还可能挂着 provenance 等不能运行的附件，不能把任意子项当成可启动的平台镜像。哪个子摘要算验收过，在[下一章](#57.%20%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E4%BA%A7%E7%89%A9%E6%80%8E%E6%A0%B7%E5%8E%9F%E6%A0%B7%E6%99%8B%E7%BA%A7%E5%88%B0%E7%94%9F%E4%BA%A7%EF%BC%9F)处理。

### 观察命令各能证明什么

排查时先分清看的是本机镜像、本机容器，还是 registry：

| 命令 | 看的对象 | 能回答 | 不能单独证明 |
|---|---|---|---|
| `docker image ls` | 本机镜像与 tag | 镜像是否已载入、本机有哪些名字 | 有容器在运行，或 registry 有同一内容 |
| `docker image inspect report-api:c4f2a91` | 本机镜像配置 | 平台、启动命令、环境、image ID（配置对象的标识）与已知的 RepoDigests | registry 当前的发布状态，或来源可信 |
| `docker image history report-api:c4f2a91` | 本机镜像的层记录 | 哪些构建步骤留下了层 | 完整的文件审计，或密钥从未进入层 |
| `docker ps -a` | 本机容器（含已停止的） | 容器在运行、已退出还是已停止 | 应用业务健康 |
| `docker buildx imagetools inspect <ref>@sha256:…` | registry 中的清单 | 远端确有这份内容，index 含哪些子项 | 内容来自哪个提交 |

`docker run -d` 的 detached mode (分离运行模式) 只让命令在后台返回，它不是进程监督器，也不替你配置健康检查、重启策略和告警。

容器的生命周期命令可以按对象理解。下面换一个与报表服务无关的 Redis 缓存容器，因为它最能单独展示每条命令动了什么：

- `docker pull redis:7` 把可变 tag 拉到本机；要固定版本，就用 registry 摘要。
- `docker run --name cache -d redis:7` 从镜像创建并启动一个新容器。
- `docker stop cache` 向容器主进程发送配置的停止信号，宽限期过后再强制终止；`docker start cache` 重新启动同一个容器和它原来的可写层，不会从新版镜像重建。
- `docker rm cache` 移除已停止的容器。`docker rm -f cache` 直接对运行中容器的主进程发 `SIGKILL` 再移除，没有 `stop` 的宽限期：在途工作可能被打断，可写层也随之丢失。卷是否还在，取决于卷的类型和删除方式。
- `docker image rm redis:7` 移除这个本地镜像引用；其他标签或仍在用它的容器可能让这些层继续保留。

手动发布时，`docker login registry.example.com` 登录并在本机存储凭据，`docker tag` 给本地内容加上仓库名和标签，`docker push` 才写入 registry。生产发布应由受控的 CI 身份完成，记录 registry 返回的摘要并按摘要部署，不把可变 tag 当作验收结果。

### 交给下一步的是什么

本章结束时手上有两样东西：经 registry 核验的 `d-new` 引用，以及一份把它和 `c4f2a91`、依赖、构建器、平台连起来的构建记录。想在本机用 Compose 把 API、worker 和数据库一起跑起来，看[本地服务栈支线](#56.%20%E7%94%A8%20Compose%20%E5%9C%A8%E6%9C%AC%E5%9C%B0%E8%B5%B7%E4%B8%80%E5%A5%97%E6%9C%8D%E5%8A%A1%E6%97%B6%EF%BC%8C%E7%BD%91%E7%BB%9C%E3%80%81%E5%81%A5%E5%BA%B7%E6%A3%80%E6%9F%A5%E3%80%81%E5%AF%86%E9%92%A5%E5%92%8C%E6%95%B0%E6%8D%AE%E5%90%84%E6%80%8E%E6%A0%B7%E9%85%8D%EF%BC%9F)。要让这同一个摘要原样经过预发布、获批进入生产，问题就变成：哪些状态要分别通过，谁对哪一步负责？这是[一次构建、按摘要晋级](#57.%20%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E4%BA%A7%E7%89%A9%E6%80%8E%E6%A0%B7%E5%8E%9F%E6%A0%B7%E6%99%8B%E7%BA%A7%E5%88%B0%E7%94%9F%E4%BA%A7%EF%BC%9F)的内容。

> [!info]- 来源
> - **镜像、容器、可写层与 Dockerfile 指令**（“镜像、容器和摘要各是什么”“启动命令由谁决定”）：Docker Docs，[What is an image?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/)、[What is a container?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)、[Dockerfile reference](https://docs.docker.com/reference/dockerfile/)（`RUN`/`CMD`/`ENTRYPOINT`、exec 与 shell form、`USER`）、[Multi-stage builds](https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/)，核对于 2026-11-12。
> - **构建上下文、`.dockerignore` 与缓存**（“构建上下文和层缓存决定构建读到什么”）：Docker Docs，[Build context](https://docs.docker.com/build/concepts/context/)（§.dockerignore files：`**` 匹配任意层目录，包括零层）、[Building best practices](https://docs.docker.com/build/building/best-practices/)、[Optimize cache usage](https://docs.docker.com/build/cache/optimize/)，核对于 2026-11-12。
> - **构建期密钥**（“构建期凭据只在一条 RUN 里出现”）：Docker Docs，[Build secrets](https://docs.docker.com/build/building/secrets/)，核对于 2026-11-12；secret mount 不进镜像层，不应把密钥放进 `ARG`/`ENV`。
> - **Python 依赖校验与源码包构建环境**（Dockerfile 一节）：pip，[Secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/)、[`pip install --require-hashes`](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-require-hashes)、[Build system interface](https://pip.pypa.io/en/stable/reference/build-system/)，核对于 2026-11-12；哈希模式要求锁定直接与传递依赖，源码包的隔离构建环境另有构建依赖。
> - **Python 版本**（版本说明 callout）：[Python 3.15.2 release](https://www.python.org/downloads/release/python-3152/)、Docker Hub [python `slim` 镜像](https://hub.docker.com/layers/library/python/slim/)，核对于 2026-11-12。
> - **Compose `command`/`entrypoint` 覆盖与插值**（“启动命令由谁决定”“本地 --load 与 CI --push 是两次输出”）：[Compose services reference](https://docs.docker.com/reference/compose-file/services/)、[Variable interpolation](https://docs.docker.com/reference/compose-file/interpolation/)，核对于 2026-11-12。
> - **`--load`/`--push`、metadata、registry 核验与 image store**（“本地 --load 与 CI --push 是两次输出”及多平台 callout）：Docker Docs，[`docker buildx build`](https://docs.docker.com/reference/cli/docker/buildx/build/)、[`imagetools inspect`](https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/)、[Docker Engine containerd image store](https://docs.docker.com/engine/storage/containerd)、[Docker Desktop containerd image store](https://docs.docker.com/desktop/features/containerd/)、[Multi-platform builds](https://docs.docker.com/build/building/multi-platform/)（Engine 29.0+ 默认 image store），核对于 2026-11-12；OCI importer 分支见 [Buildx v0.39.0 `build/opt.go`](https://github.com/docker/buildx/blob/v0.39.0/build/opt.go#L494-L538)。
> - **摘要、索引附件与来源证明**（“摘要标识内容，不证明来源”）：Docker Docs，[Image digests](https://docs.docker.com/dhi/explore/security-concepts/digests/)、[Build attestations](https://docs.docker.com/build/metadata/attestations/)、[SLSA provenance attestations](https://docs.docker.com/build/metadata/attestations/slsa-provenance/)，核对于 2026-11-12；摘要标识内容，提交与产物的联系需要额外的来源证据。
> - **观察与生命周期命令**（“观察命令各能证明什么”）：Docker CLI reference，[docker run](https://docs.docker.com/reference/cli/docker/container/run/)、[docker stop](https://docs.docker.com/reference/cli/docker/container/stop/)、[`docker rm --force`](https://docs.docker.com/reference/cli/docker/container/rm/#force)、[docker image rm](https://docs.docker.com/reference/cli/docker/image/rm/)、[docker image history](https://docs.docker.com/reference/cli/docker/image/history/)、[docker login](https://docs.docker.com/reference/cli/docker/login/)、[docker tag](https://docs.docker.com/reference/cli/docker/image/tag/)、[docker push](https://docs.docker.com/reference/cli/docker/image/push/)，核对于 2026-11-12；强制移除运行中容器发送 `SIGKILL`，没有 `stop` 的宽限期。
## 56. 用 Compose 在本地起一套服务时，网络、健康检查、密钥和数据各怎样配？

[镜像章](#55.%20%E6%BA%90%E7%A0%81%E6%80%8E%E6%A0%B7%E5%8F%98%E6%88%90%E5%8F%AF%E8%BF%90%E8%A1%8C%E3%80%81%E5%8F%AF%E8%BF%BD%E6%BA%AF%E7%9A%84%E5%AE%B9%E5%99%A8%E9%95%9C%E5%83%8F%EF%BC%9F)交来一个经 registry 核验的报表服务镜像引用 `d-new`。本支线用 Docker Compose 在一台开发机上把 API、worker 和 PostgreSQL 一起跑起来，依次回答：服务之间怎样互相找到、哪些端口对外；数据库什么时候算“可以用了”；本地密钥怎样交给容器；数据库文件在什么情况下能活过容器替换。最后列出观察和收尾命令各能证明什么。

本支线只讲本机服务栈。它能验证服务发现和容器间网络，验证不了生产入口、工作负载身份和账户授权；那些分别在[生产运行时章](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)和后续发布章处理。

### 一份 Compose 配置

下面的 Compose Specification (Compose 规范) 片段让 API 与 worker 共用同一个镜像引用，只替换 worker 的启动命令（覆盖规则见镜像章的[启动命令由谁决定](#%E5%90%AF%E5%8A%A8%E5%91%BD%E4%BB%A4%E7%94%B1%E8%B0%81%E5%86%B3%E5%AE%9A)）。`REPORT_IMAGE` 由外部传入，应是 CI `--push` 后核验过的完整 `registry.example.com/team/report-api@sha256:…`，而不是本地 `--load` 的摘要。`${REPORT_IMAGE:?…}` 只拒绝空值，不检查它是不是摘要引用。

只做本机开发时，也可以把 `image` 设成本地已载入的 `report-api:c4f2a91` 并加 `pull_policy: never`，或改用 `build: .` 从当前目录重建。这两种配置都不能当作 registry 发布的证据。

> [!example]- Compose 配置：共享镜像、独立凭据与命名卷
>
> ~~~yaml
> services:
>   api:
>     image: "${REPORT_IMAGE:?set REPORT_IMAGE to an immutable image digest}"
>     ports:
>       - "127.0.0.1:8080:8080"
>     environment:
>       DATABASE_HOST: db
>       DATABASE_NAME: reports
>       DATABASE_USER: report_app
>       DATABASE_PASSWORD_FILE: /run/secrets/app_db_password
>     secrets:
>       - app_db_password
>     depends_on:
>       db:
>         condition: service_healthy
>
>   worker:
>     image: "${REPORT_IMAGE:?set REPORT_IMAGE to an immutable image digest}"
>     command: ["python", "-m", "app.worker"]
>     environment:
>       DATABASE_HOST: db
>       DATABASE_NAME: reports
>       DATABASE_USER: report_app
>       DATABASE_PASSWORD_FILE: /run/secrets/app_db_password
>     secrets:
>       - app_db_password
>     depends_on:
>       db:
>         condition: service_healthy
>
>   db:
>     image: postgres:18
>     environment:
>       POSTGRES_DB: reports
>       POSTGRES_PASSWORD_FILE: /run/secrets/db_admin_password
>     secrets:
>       - db_admin_password
>     volumes:
>       - report-data:/var/lib/postgresql
>     healthcheck:
>       test:
>         - CMD-SHELL
>         - >-
>           pg_isready -h 127.0.0.1 -p 5432
>           -U "$${POSTGRES_USER:-postgres}"
>           -d "$${POSTGRES_DB:-postgres}"
>       interval: 5s
>       timeout: 3s
>       retries: 5
>
> secrets:
>   app_db_password:
>     file: ./secrets/app_db_password.txt
>   db_admin_password:
>     file: ./secrets/db_admin_password.txt
>
> volumes:
>   report-data:
> ~~~

下面逐项解释这份配置背后的规则。

### 服务网络、端口发布与监听地址

![本地 Compose 默认 bridge/NAT 拓扑：浏览器经宿主机 127.0.0.1:8080 进入 API；API 与 worker 运行同一摘要，经 db:5432 连接 PostgreSQL，数据库文件在命名卷里。](../../engineering-foundations/practice/resources/docker-compose-runtime-topology.svg)

Compose 为项目自动创建一个 default bridge network (默认桥接网络)，服务之间用 service name (服务名) 互相发现。API 和 worker 都连 `db:5432`，那是数据库容器内的端口，不需要映射到宿主机。不要保存容器 IP：Compose 重建服务时会分配新 IP，服务名不变；已有连接会断开，客户端要重新解析并连接。

只有需要从宿主机进入的 API 映射了宿主机端口。这里有两个独立的地址：

- **容器内监听地址**：API 进程监听 `0.0.0.0:8080`，映射进来的流量才能到达它（见镜像章的 Dockerfile 一节）。
- **宿主机发布地址**：`127.0.0.1:8080:8080` 只把宿主机回环地址映射到容器端口。省略宿主机 IP 时默认绑定宿主机所有接口，应视作对其他可路由主机开放。

端口映射只建立转发关系，不证明 API 健康；服务名可达也不代表数据库身份验证通过，更不代替应用认证和账户授权。

> [!info] 实例：localhost 发布的边界与 Engine 版本有关（核对于 2026-11-12）
> 从 Docker Engine 28.0.0 起，在默认 bridge/NAT 路径上发布到 localhost 的端口，预期只能从 Docker 主机本身访问；更早的版本存在例外，同一二层网络中的其他主机可能访问到这些端口。特殊 network mode (网络模式)、direct routing (直接路由) 以及宿主机路由和防火墙仍可能改变这个边界，要按实际 Engine 版本和网络设置核实。

### 健康检查、启动依赖与引导迁移

`depends_on: condition: service_healthy` 让 Compose 在启动 API 和 worker 之前，等数据库的健康检查通过。它的作用到此为止：

- 它只在 Compose 启动依赖方的那一刻等待，之后数据库出故障，它不接管恢复。
- 它不等待任何独立的引导任务。
- 健康检查本身也证明得很少。`pg_isready` 只说明服务器在接受连接；命令里的 `-U`/`-d` 只是连接请求的信息，不是身份验证，不证明角色、密码或结构迁移正确。

健康检查要写 `-h 127.0.0.1 -p 5432`，显式探测正式的 TCP 监听端口。不带 `-h` 时它走 Unix socket；官方 Postgres 镜像在初始化期间会启动一个只供本地脚本用的临时服务器，socket 检查可能在正式 TCP 服务就绪之前就提前通过。

所以一个新建空卷的本地栈要分三步启动：

1. 确认 `REPORT_IMAGE` 是本次 push 后核验过的引用，然后 `docker compose up -d db` 单独启动数据库。`POSTGRES_DB: reports` 让官方镜像在初始化空数据目录时创建 `reports` 库；默认管理用户是高权限的 `postgres`，不要把 `POSTGRES_USER` 改成应用账号 `report_app`。
2. 等 TCP 健康检查变成 healthy，运行项目提供的受控 bootstrap/migration (引导与迁移) 任务：它读取管理员密码和 `app_db_password`，创建使用应用密码的 `report_app`，只授予 `reports` 中应用需要的权限，并完成 schema migration (结构迁移)。上面的 Compose 片段没有定义这个任务。
3. 引导成功后，再 `docker compose up -d api worker`。

已有的卷不会因为环境变量改了就自动补建数据库或修改凭据，启动服务前要核对它的实际状态。

### 本地 secret 与数据库初始化凭据

Compose 的 `secrets` 把凭据文件显式挂给获准的服务，容器内出现在 `/run/secrets/<名字>`。本例的两份 secret 用途不同：

- `db_admin_password` 只交给数据库容器，供官方镜像初始化管理员。
- `app_db_password` 是独立的最小权限应用账号密码，交给 API 和 worker；应用代码要自己读取 `DATABASE_PASSWORD_FILE` 指向的文件。

本地 `file:` secret 通过 bind mount (绑定挂载) 提供（本例以 Linux 容器为前提），`uid`、`gid`、`mode` 覆盖会被忽略；要靠宿主机文件权限保证容器里的 `USER 10001` 能读到它。

`POSTGRES_PASSWORD_FILE` 只在空数据目录首次初始化时设置管理员密码。之后改宿主机上的 secret 文件，不会修改数据库里已有的密码。轮换要先在数据库里更新账号，再让应用切换到匹配的 secret。本地 secret 方便开发，但不等于加密的生产 secret store (密钥存储服务)；`secrets/` 目录不要进版本控制。

### 卷类型决定数据能活多久

容器可写层随容器删除而丢失。要让数据库文件活过容器替换，就要挂卷，而不同挂载方式的寿命不同：

| 挂载方式 | 容器替换后 | 适合 |
|---|---|---|
| named volume (命名数据卷) | 由 Docker 管理，新容器可以重新挂上同一个卷 | 本地数据库文件 |
| anonymous volume (匿名数据卷) | 没有稳定的项目名称，新容器通常不会自动挂上同一个卷 | 临时数据 |
| bind mount (绑定挂载) | 直接映射宿主机路径 | 开发时共享源码；不适合当生产数据库的备份方案 |

卷只解决“容器换了文件还在”。它不提供异机备份、时间点恢复、加密、访问控制，也不保证数据正确；这些要靠独立的备份与恢复演练。`docker compose down` 移除容器和网络、保留命名卷；`docker compose down -v` 会删除 Compose 文件声明的项目命名卷及附着的匿名卷，连同其中的数据。

> [!info] 实例：PostgreSQL 18 官方镜像改了数据路径（核对于 2026-11-12）
> 上面的卷挂在 `/var/lib/postgresql`，而不是常见的 `/var/lib/postgresql/data`。官方镜像从主版本 18 起改用按版本区分的路径：默认 `PGDATA` 是 `/var/lib/postgresql/18/docker`，卷应挂在父目录 `/var/lib/postgresql`；以后的主版本把路径中的 `18` 换成各自的版本号。PostgreSQL 19 已于 2026-11-19 发布；本例仍固定在 18 主版本，换主版本是一次需要迁移的升级，见下段。17 及更早版本的数据路径是 `/var/lib/postgresql/data`，应直接挂这个目录；只改挂父目录，可能无法持久化旧数据。
>
> 升级主版本不能靠改 image tag 自动迁移数据：18 的目录布局变化要求先检查并调整旧卷结构，主版本升级本身要先备份，再走官方支持的升级流程。`postgres:18` 这样的主版本 tag 仍会随 18.x 补丁移动；生产环境要记录并固定实际摘要，同时及时更新补丁。

### 观察与收尾命令各能证明什么

| 命令 | 看的对象 | 能回答 | 不能单独证明 |
|---|---|---|---|
| `docker compose ps` / `docker compose ps -a` | Compose 服务的容器 | 默认只列运行中的服务；`-a` 也列已停止的容器 | 没配 healthcheck 时的就绪，或用户结果 |
| `docker compose logs api worker` | 两个服务的标准输出与错误 | 启动错误和应用日志 | 端到端追踪、账户授权和完整指标 |
| `docker compose exec api /bin/sh` | 正在运行的 API 容器 | 查看进程环境、执行诊断命令 | 容器里一定有 shell（distroless 或精简镜像可能没有） |

`docker compose up -d` 只是让命令在后台返回，不是进程监督器，也不自动配置健康检查、重启策略和告警。容器 `running`、Docker 健康状态 `healthy` 和应用业务正确是三种不同的判断：只有定义了 healthcheck 才有 `healthy`，而它也证明不了 `user-29` 读不到 acct-17 的报表 42。

### 本地栈之后

这套本地栈能确认：同一个 `d-new` 的 API 和 worker 能起来，能经 `db:5432` 访问按最小权限引导好的数据库，数据库文件存在命名卷里。它确认不了预发布和生产的身份、入口与授权。回到主线：同一个摘要怎样经过预发布验收、获批进入生产，见[一次构建、按摘要晋级](#57.%20%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E4%BA%A7%E7%89%A9%E6%80%8E%E6%A0%B7%E5%8E%9F%E6%A0%B7%E6%99%8B%E7%BA%A7%E5%88%B0%E7%94%9F%E4%BA%A7%EF%BC%9F)。

> [!info]- 来源
> - **Compose 文件与服务配置**（“一份 Compose 配置”）：Docker Docs，[Compose Specification](https://docs.docker.com/reference/compose-file/)、[Services reference](https://docs.docker.com/reference/compose-file/services/)、[Variable interpolation](https://docs.docker.com/reference/compose-file/interpolation/)、[Compose history](https://docs.docker.com/compose/intro/history/)，核对于 2026-11-12；旧的顶层 `version` 字段已过时，当日文档支持的 Compose CLI 均采用 Compose Specification。
> - **服务网络与端口发布**（“服务网络、端口发布与监听地址”及 Engine 28 callout）：Docker Docs，[Networking in Compose](https://docs.docker.com/compose/how-tos/networking/)、[Port publishing and mapping](https://docs.docker.com/engine/network/port-publishing/)，核对于 2026-11-12。
> - **启动顺序与健康检查**（“健康检查、启动依赖与引导迁移”）：Docker Docs，[Control startup order](https://docs.docker.com/compose/how-tos/startup-order/)；PostgreSQL 18，[`pg_isready`](https://www.postgresql.org/docs/18/app-pg-isready.html)（检查服务器是否接受连接，不验证认证）；官方 Postgres 镜像 [Initialization scripts](https://github.com/docker-library/docs/blob/master/postgres/README.md#initialization-scripts) 与 [docker-entrypoint.sh](https://github.com/docker-library/postgres/blob/master/docker-entrypoint.sh)（初始化期间的临时本地服务器），核对于 2026-11-12。
> - **本地 secret 与初始化凭据**（“本地 secret 与数据库初始化凭据”）：Docker Docs，[Use secrets in Compose](https://docs.docker.com/compose/how-tos/use-secrets/)；官方 Postgres 镜像 [Environment variables](https://hub.docker.com/_/postgres#environment-variables)，核对于 2026-11-12；初始化变量不修改非空数据目录中已有的账号。
> - **卷与数据路径**（“卷类型决定数据能活多久”及 PostgreSQL 18 callout）：Docker Docs，[Volumes](https://docs.docker.com/engine/storage/volumes/)、[Bind mounts](https://docs.docker.com/engine/storage/bind-mounts/)、[`docker compose down`](https://docs.docker.com/reference/cli/docker/compose/down/)；官方 Postgres 镜像 [PGDATA](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)；[PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/)，核对于 2026-11-12。
> - **观察命令**（“观察与收尾命令各能证明什么”）：Docker CLI reference，[docker compose ps](https://docs.docker.com/reference/cli/docker/compose/ps/)、[docker compose logs](https://docs.docker.com/reference/cli/docker/compose/logs/)、[docker compose exec](https://docs.docker.com/reference/cli/docker/compose/exec/)，核对于 2026-11-12。
## 57. 已验证的产物怎样原样晋级到生产？

沿用主线五的案例。[镜像章](#55.%20%E6%BA%90%E7%A0%81%E6%80%8E%E6%A0%B7%E5%8F%98%E6%88%90%E5%8F%AF%E8%BF%90%E8%A1%8C%E3%80%81%E5%8F%AF%E8%BF%BD%E6%BA%AF%E7%9A%84%E5%AE%B9%E5%99%A8%E9%95%9C%E5%83%8F%EF%BC%9F)交来经 registry 核验的报表服务镜像 `d-new`，以及把它和修复提交 `c4f2a91` 连起来的构建记录；生产当前跑的仍是带着跨账户缺陷的稳定版 `d-old`。本章回答：发布流程里“通过了”分别指哪一步；为什么预发布和生产必须运行同一个摘要，而不是各自重建；多平台镜像验收的是哪个平台；谁能放行部署，流水线和配置又怎样固定下来。

产出是一个已在预发布验收、获批并以同一摘要启动的生产部署。它就绪之后怎样用生产冒烟检查和小流量逐步放量，是[金丝雀章](#60.%20%E6%96%B0%E7%89%88%E6%9C%AC%E6%80%8E%E6%A0%B7%E9%80%90%E6%AD%A5%E6%94%BE%E9%87%8F%EF%BC%8C%E5%87%BA%E9%97%AE%E9%A2%98%E6%97%B6%E8%83%BD%E6%92%A4%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)的问题。

### “通过了”指的是哪一步

先分开两个常被混用的词。continuous delivery (持续交付) 指代码通过检查后随时**可以**发布；continuous deployment (持续部署) 指门禁满足后**自动**发布。两者都不意味着“CI 绿了，用户就用上了”。

从提交到用户流量，中间至少有四个不同的状态，各由不同角色负责，前一个成立推不出后一个：

| 状态 | 负责方 | 成立时说明什么 |
|---|---|---|
| 构建与预发布验收通过 | CI；预发布检查负责人 | 这个摘要通过了约定的检查与业务验收 |
| 批准 | 环境审批者 | 部署可以继续，流量还没动 |
| 启动并就绪 | 部署系统；平台探针 | 获批的摘要在运行，平台认为可以给它发流量 |
| 切流 | 流量入口；发布负责人或预先配置的控制器 | 真实用户请求开始到达新版本 |

批准不等于部署，就绪不等于业务正确，HTTP 入口切了流也不会改变独立 worker 消费哪些消息。下图把整条路径画在一起，本章讲到“启动获批摘要”为止，之后的冒烟检查和首轮流量在金丝雀章。

![CI 固定提交并只构建一次；预发布用同一摘要验收，生产获批后启动同一摘要，就绪后经定向冒烟检查才开放首轮小流量；任一步失败都不切流。](../../engineering-foundations/practice/resources/application-deployment-flow.svg)

### 为什么只构建一次、按摘要晋级

镜像章已经说明：基础镜像 tag 和外部依赖会移动或更新，同一份源码分别重建可能得到不同的内容。如果预发布构建一次、生产再构建一次，预发布验收的就不是生产运行的东西。所以规则是：**CI 只构建一次，预发布和生产都按这次构建的 image digest 拉取和启动，不各自重建。** 晋级的单位是摘要，不是 tag，也不是“同一个提交”。

这条规则只在构建输入本身被固定时才有意义。CI 应检出确切的 `c4f2a91`，确认工作区干净，用检查过的源码树作为唯一构建上下文；依赖锁文件、Dockerfile、基础镜像解析结果、构建器版本、平台和构建参数都进入构建记录。若合并或改写提交改变了源码树，就要在最终用于构建的提交上重跑必要的门禁，或者给出可核验的“源码树相同”证据。构建和检查用了同一个可移动标签，不能证明它们针对的是同一份内容；验收证据要绑定到同一个提交 ID 和同一个摘要，提交一侧的做法见 [Git 章](#54.%20Git%20%E6%80%8E%E6%A0%B7%E8%AE%B0%E5%BD%95%E4%B8%80%E6%AC%A1%E6%94%B9%E5%8A%A8%EF%BC%8C%E5%87%BA%E9%94%99%E6%97%B6%E5%8F%88%E6%80%8E%E6%A0%B7%E6%8C%89%E5%B1%82%E6%92%A4%E5%9B%9E%EF%BC%9F)。

检查随风险而定。提交级检查覆盖静态规则、单元和集成路径（测试该放在哪一层，见[测试章](#53.%20%E4%B8%80%E6%AC%A1%E6%94%B9%E5%8A%A8%E8%AF%A5%E5%9C%A8%E5%93%AA%E4%B8%80%E5%B1%82%E6%B5%8B%E8%AF%95%EF%BC%8C%E6%80%8E%E6%A0%B7%E8%AF%81%E6%98%8E%E6%B5%8B%E8%AF%95%E8%83%BD%E5%8C%BA%E5%88%86%E5%AF%B9%E9%94%99%EF%BC%9F)）。这次修复涉及账户授权，预发布要用同一个 `d-new` 启动 API 与 worker，然后：

- 用两个经真实认证流程建立的身份读取报表 42：`user-17` 经 acct-17 读到 `200` 和预期内容；`user-29` 经自己的 acct-29 请求 `GET /v1/accounts/acct-29/reports/42`，得到与不存在的报表 43 相同的通用 `404`。不能用客户端自填的账户头代替身份。
- worker 走真实消息代理的投递、持久化与 ACK 路径，确认导出任务的条件领取仍然只成功一次。

通过后，预发布记录的是“`d-new` 通过了这些检查”，交给生产的也正是 `d-new`。

### 多平台镜像验收的是哪个平台

多平台构建得到一个 index digest，它再引用 `linux/amd64`、`linux/arm64` 等平台各自的 manifest digest。核对索引和子摘要，只证明清单之间的映射关系。如果预发布只在 amd64 上跑过，生产却运行 arm64，生产实际运行的子镜像从来没有被验证过。

做法有两种：在与生产平台一致的预发布目标上运行并验收每个将要部署的子摘要；或者把生产限制在预发布实际运行过的平台。无论哪种，生产都要记录实例实际运行的平台子摘要，并确认它等于该平台验收过的子摘要；“它属于验收过的索引”还不够。

### 谁能放行部署，流水线自己也要固定

产物身份固定后，还要明确谁能放行部署、部署脚本本身会不会变。

> [!info] 实例：GitHub Actions 的环境门禁与依赖固定（核对于 2026-11-12）
> `environment` 可以配置必需审查者、部署分支限制、等待规则和环境 secrets；引用该 environment 的 job 只有通过已生效的保护规则，才会执行受保护的部署步骤或拿到相应 secret。哪些规则可用取决于 GitHub 计划和仓库配置。审批通过只表示这个 job 可以继续。
>
> 流水线引用的外部代码也要固定，否则同一份 workflow 可能在不同时刻执行不同的代码：
>
> - 第三方 Action `uses: owner/repo@ref` 的 `ref` 固定为已核验的完整 commit SHA；或者把 workflow 纳入 workflow dependency lockfile (工作流依赖锁文件)，由它锁定远端步骤级 Action 及其传递依赖。GitHub 于 2026-10-28 宣布该功能正式可用（GA 公告列出 Enterprise Cloud、Team、Free 计划）。锁文件按 workflow 逐条纳入，仓库里有锁文件不代表每条 workflow 都已纳入。
> - 本地步骤级 Action `uses: ./path` 来自调用方的工作区，默认不被锁文件锁定。
> - 同仓 reusable workflow (可复用工作流) `uses: ./.github/workflows/deploy.yml` 的版本由调用方的同一个提交决定。跨仓引用 `owner/repo/.github/workflows/deploy.yml@ref` 要固定完整 SHA；它内部的 Action 依赖只能由定义它的仓库把它纳入自己的锁文件来锁定，调用方的锁文件替代不了。
> - Action 锁文件不锁定 job 级可复用 workflow 调用、构建参数、secret 或 runner (工作流执行器) 镜像。

### 配置与密钥随版本记录

镜像之外，运行配置也要随部署版本一起记录，但密钥值始终留在 secret store：

- 数据库地址、启用的功能开关和配置版本可以放进受控配置，部署记录写明用的是哪个配置版本。
- 部署记录只保存 secret 的名称或版本引用及其适用范围，不保存值。
- 静态前端若要在各环境间晋级同一个 bundle (打包文件)，而各环境的非秘密配置不同，就让 bundle 在运行时读取各环境自己的配置端点或配置文件；部署记录保存 bundle ID、配置版本和校验和。编译期写进浏览器 bundle 的值任何用户都能读到，不能放秘密，密钥只由服务端或密钥服务提供。前端构建侧的做法见[前端构建产物](../../frontend/delivery/build-pipeline-and-bundling.md)。

这份记录到回退时会再用到：回退目标是“摘要 + 配置版本 + secret 引用”的组合，不只是一个旧摘要。

### 进入生产前核对什么

环境审批之前，先核对目标环境的 IAM 权限、网络路由、密钥来源和数据库迁移状态。审批通过后，部署系统用预发布验收过的同一个 `d-new` 启动生产实例，并附上带版本的运行配置和 secret 引用。

此时 `d-new` 在生产里运行，但还没有真实用户流量。平台怎样判断它已启动、可以接流量，以及以后怎样停止它，要看运行时和探针的语义；就绪也只说明平台可以给它发流量，不说明账户授权和异步导出在生产环境里正确。

### 交给下一步的是什么

本章结束时：`d-new` 在预发布通过了验收，生产已获批并以同一个摘要启动，部署记录写明了摘要、平台子摘要、配置版本和 secret 引用。下一个问题是平台层面的：这个服务该跑在哪种运行时上，平台怎样探测它是否就绪、怎样停止它，每个运行角色拿着什么身份？见[生产运行时章](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)。

> [!info]- 来源
> - **持续交付与持续部署**（“‘通过了’指的是哪一步”）：DORA，[Continuous delivery](https://dora.dev/capabilities/continuous-delivery/)，核对于 2026-11-12；区分随时可发布与门禁满足后自动发布。
> - **构建输入、缓存与来源记录**（“为什么只构建一次、按摘要晋级”）：Docker Docs，[Building best practices](https://docs.docker.com/build/building/best-practices/)、[Optimize cache usage](https://docs.docker.com/build/cache/optimize/)、[Build provenance attestations](https://docs.docker.com/build/metadata/attestations/slsa-provenance/)，核对于 2026-11-12。
> - **多平台索引与子清单**（“多平台镜像验收的是哪个平台”）：Docker Docs，[Multi-platform builds](https://docs.docker.com/build/building/multi-platform/)、[Image digests](https://docs.docker.com/dhi/explore/security-concepts/digests/)（tag、索引与子清单）、[`imagetools inspect`](https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/)，核对于 2026-11-12。
> - **GitHub 环境门禁与 workflow 依赖**（GitHub Actions 实例 callout）：GitHub Docs，[Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)、[Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)、[Lock workflow dependencies](https://docs.github.com/en/actions/how-tos/secure-your-work/lock-workflow-dependencies)、[Reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)；GitHub Changelog，[Workflow lockfiles are generally available](https://github.blog/changelog/2026-10-28-github-actions-workflow-lockfiles-are-generally-available/)（2026-10-28），核对于 2026-11-12。锁文件默认不锁本地路径 Action；跨仓可复用 workflow 的依赖只能由定义仓库锁定。
> - **配置与密钥分离**（“配置与密钥随版本记录”）：Docker Docs，[Build secrets](https://docs.docker.com/build/building/secrets/)，核对于 2026-11-12；构建期不把密钥放入 `ARG`/`ENV`。部署记录只存 secret 引用、前端 bundle 运行时读配置是本章基于这一边界的工程安排。
## 58. 服务该跑在哪种运行时上，平台怎样启动、探测和停止它？

沿用主线五的案例。[上一章](#57.%20%E5%B7%B2%E9%AA%8C%E8%AF%81%E7%9A%84%E4%BA%A7%E7%89%A9%E6%80%8E%E6%A0%B7%E5%8E%9F%E6%A0%B7%E6%99%8B%E7%BA%A7%E5%88%B0%E7%94%9F%E4%BA%A7%EF%BC%9F)让 `d-new` 获批并在生产启动，但还没有用户流量。报表服务在生产里不是一个进程，而是几个角色：

- **API**：对外接收读取和导出请求（HTTP）。
- **worker**：常驻等待队列，领取导出 job，执行 attempt，把结果写进私有对象存储。
- **outbox relay (发件箱中继)**：把数据库里已提交的待发意图发布到消息代理。
- **lease recoverer (租约恢复器)**：扫描租约已过期的 job，按条件接管或收尾。

这几个角色做什么、为什么这样设计，在主线四的[持久受理与 outbox](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)和[条件领取与栅栏](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)里讲过。本章只关心平台这一侧：它们该跑在哪种运行时上，平台替你管什么、不管什么，怎样判断进程可以接流量，停止时按什么顺序关门，每个角色拿着什么网络身份和凭据，以及组件信号能说明什么。

API 与 worker 用同一个 `d-new` 摘要、不同的启动命令运行，不重新构建。relay 只有在镜像里确实包含它的执行入口时才复用这个摘要，否则要交接它自己核验过的摘要。

### 按时长、并发和停止行为选运行时

选运行时不看“云上”或“无服务器”这样的标签，而看几个问题：工作何时开始，最长会运行多久，并发怎样到达，能否安全重试，需要哪些连接和状态，平台停止进程时能否完成当前交接。

| 运行形态 | 适合的约束 | 必须核对的边界 |
|---|---|---|
| function service (函数托管服务) | 事件触发、每次工作有明确上限，供应商的重试、并发和执行上下文与业务匹配 | 单次时长上限、冷启动、并发与配额、网络与连接池、触发及重试语义；要持久进度时用平台支持的状态编排，不把内存当跨调用状态 |
| managed container service (托管容器服务) | HTTP 服务或队列消费者需要长期进程、明确的并发上限、连接生命周期和停止钩子 | 健康检查怎样影响流量、扩容是否够快、停止宽限期能否覆盖排空、多个副本怎样共享外部数据库与队列而不共享进程内状态 |
| virtual machine (虚拟机，VM) | 依赖主机级配置、守护进程、内核能力或遗留运行环境 | 主机补丁、容量与故障替换由团队负责；托管 VM 产品要按其服务合同重新划定责任 |

再按峰值与稳态负载、最低常驻容量、启动延迟容忍度、长连接、并行度、单次执行限制和团队运维能力比较。“自动扩展”有两个常被忽略的边界：它不保证尖峰请求立即拿到新实例，也不会给数据库增加连接容量。每加一个副本，就按“副本 × 每副本进程 × 每进程池上限”多占数据库连接；worker 副本还同时增加物理执行槽。这些账怎样一起算，见[容量与准入章](#47.%20%E4%B8%80%E6%9D%A1%E5%BC%82%E6%AD%A5%E7%AE%A1%E7%BA%BF%E8%83%BD%E6%8E%A5%E5%A4%9A%E5%B0%91%E5%B7%A5%E4%BD%9C%EF%BC%8C%E8%B6%85%E5%87%BA%E6%97%B6%E5%9C%A8%E5%93%AA%E9%87%8C%E6%8B%92%E7%BB%9D%EF%BC%9F)和[连接池章](#28.%20ORM%20%E4%BC%9A%E8%AF%9D%E6%80%8E%E6%A0%B7%E5%80%9F%E7%94%A8%E8%BF%9E%E6%8E%A5%EF%BC%8C%E8%BF%9E%E6%8E%A5%E6%B1%A0%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E8%80%97%E5%B0%BD%EF%BC%9F)。

报表服务的选择是：API 要持续接收读请求，worker 常驻等待队列并在停止时完成当前 attempt 或安全交还投递，所以 API、relay 和 worker 作为三个可独立扩缩容的托管容器服务运行，各自配置并发、容量、网络和身份。relay 单独控制，避免把它错误地包进 API 的健康状态或 worker 的暂停开关。只有导出能拆成明确有界的事件步骤，且平台的触发、重试、最长时长和连接约束都合适时，才把计算阶段拆成函数。

> [!info]- 实例：AWS Lambda 的三种模式时长不同（核对于 2026-11-12）
> AWS Lambda 文档区分默认函数调用、Lambda Managed Instances 和 durable functions (持久函数)：默认单次调用最长 15 分钟；Managed Instances 的异步或事件源映射调用可到 90 分钟；持久函数用检查点跨多次调用，异步执行最长可到一年。三者的状态、并发和恢复语义不同，不能用“函数最长多久”一句话概括。默认执行环境可能复用全局对象和 `/tmp`，可以做可丢弃的缓存或连接复用；但环境会被回收，不能当跨调用的持久数据，未完成的后台回调也不能指望以后继续执行。重复事件要求处理幂等。

### 托管平台管什么，应用仍负责什么

托管减少的是平台运维，不会替工作负载选择安全配置：

| 层 | 平台通常负责 | 应用团队仍负责 |
|---|---|---|
| 计算 | 按服务方案提供主机维护、调度和运行环境 | 镜像、启动与退出、资源上限、扩缩容策略、健康规则 |
| 数据库 | 所选配置包含的基础设施、补丁、备份或故障切换 | schema 与迁移、查询与连接行为、权限授予、保留期、恢复演练 |
| 对象存储 | 服务可用性与文档承诺的持久性机制 | 私有命名、保留与生命周期、上传上限、谁能拿到签名 URL 及其过期与撤权 |
| 队列 | 在服务合同和配置限制内存储并投递消息 | 幂等处理、重试退避、毒消息处理、队列年龄、dead-letter queue (死信队列) 恢复 |

托管数据库不会修复缺索引的查询或连接风暴；托管队列也不会让一个非幂等的 worker 在重试时变得安全。

### 平台怎样判断进程可以接流量

平台对一个进程要回答三个不同的问题，各用一种探针：

- **启动完成了吗？** startup probe (启动探针)。慢启动的进程在它成功之前不该被当成“卡死”。
- **还活着吗？** liveness probe (存活探针)。进程卡死、无法自愈时，重启它。
- **现在能接新请求吗？** readiness probe (就绪探针)。暂时不能接时，先别给它发流量，但不重启。

Kubernetes 中，Pod 是承载一个或多个容器的调度单元，三种探针的行为如下：

- 配置了 startup probe 时，kubelet (节点上的容器管理代理) 在它成功之前不执行另两种探针。
- startup 或 liveness 失败达到 `failureThreshold` 后，kubelet 终止容器，再按 Pod 的重启策略重启。Deployment 的 Pod 模板只允许 `restartPolicy: Always`。
- readiness 失败不会重启容器。它把 Pod 标成未就绪：默认 EndpointSlice (端点切片) 仍保留这个地址，但把 `ready` 置为 `false`，匹配的 Service 不再把它当作就绪端点发送常规新流量。Service 设置了 `publishNotReadyAddresses: true` 时，这个条件被忽略。

liveness 不要依赖每个短暂的下游故障。数据库抖动一下，所有副本的 liveness 一起失败、一起重启，只会放大故障；下游暂时不可用更适合反映在 readiness 或请求错误上。

不论哪种探针，就绪只说明平台可以把新流量发给这个实例，不说明 `user-29` 读不到 acct-17 的报表 42，也不说明导出 job 能完成。业务路径要在开放流量前另做生产冒烟检查，见[金丝雀章](#60.%20%E6%96%B0%E7%89%88%E6%9C%AC%E6%80%8E%E6%A0%B7%E9%80%90%E6%AD%A5%E6%94%BE%E9%87%8F%EF%BC%8C%E5%87%BA%E9%97%AE%E9%A2%98%E6%97%B6%E8%83%BD%E6%92%A4%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info] 版本说明
> 以上是 Kubernetes v1.37 的行为（核对于 2026-11-12）。其他平台要查各自的语义；Docker 与 Compose 的 healthcheck 见 [Compose 支线](#56.%20%E7%94%A8%20Compose%20%E5%9C%A8%E6%9C%AC%E5%9C%B0%E8%B5%B7%E4%B8%80%E5%A5%97%E6%9C%8D%E5%8A%A1%E6%97%B6%EF%BC%8C%E7%BD%91%E7%BB%9C%E3%80%81%E5%81%A5%E5%BA%B7%E6%A3%80%E6%9F%A5%E3%80%81%E5%AF%86%E9%92%A5%E5%92%8C%E6%95%B0%E6%8D%AE%E5%90%84%E6%80%8E%E6%A0%B7%E9%85%8D%EF%BC%9F)。

### 停止时各角色怎样关门

扩缩容、部署和故障替换都会停止进程。进程内部的关停顺序在[主线二的优雅关停章](#21.%20%E6%9C%8D%E5%8A%A1%E8%BF%9B%E7%A8%8B%E6%94%B6%E5%88%B0%E5%81%9C%E6%AD%A2%E4%BF%A1%E5%8F%B7%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%8E%92%E7%A9%BA%E5%B7%A5%E4%BD%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%80%80%E5%87%BA%EF%BC%9F)：先拒绝新工作，再排空在途工作；每种资源要等到可证明的完成状态才释放；内部 deadline 必须早于外部的强杀时刻。本章讲平台一侧：各角色收到停止信号后该做什么，平台按什么顺序摘流、什么时候强杀。

#### 各角色在自己的控制面立即关门

进程收到停止信号后，每个服务立即在自己的控制面开始关闭，不等入口路由更新传播完，也不等其他服务先结束：

- **API**：收到通知就关闭本地业务门闩，拒绝开始新的业务操作，开始排空在途请求；同时让 readiness 返回未就绪，让平台异步更新路由目标。路由摘除传播期间仍可能有请求到达，所以本地门闩不能依赖探针传播。已开始的请求在宽限期内完成或按应用契约安全中止，然后关闭连接池、线程、临时文件和 telemetry exporter (遥测导出器)。
- **worker**：独立停止领取新的 delivery (消息投递)，再分两类处理。运行中的 attempt 能在截止前完成，就先持久提交业务结果、再 ACK；不能完成就不 ACK，让 broker 重新投递，由租约恢复器按租约规则接管。已预取但还没启动的投递，按 broker 的关闭与归还契约放回队列：本例的 RabbitMQ 由关闭 channel 把它们自动重新入队，`basic.cancel` 本身不会让它们回队（细节见[队列确认章的 prefetch 一节](#prefetch%20%E9%99%90%E5%88%B6%E7%9A%84%E6%98%AF%E4%BB%80%E4%B9%88%EF%BC%9F)）。readiness 不会替 worker 暂停队列消费。
- **outbox relay**：停止认领新的待发意图，宽限期内等待已开始的发布得出可判定的结果。只有 broker 的确认、路由和持久性条件都满足、且数据库里的 `published` 更新成功，才把意图标为完成；缺确认或更新未提交时不伪记成功，释放认领（或等认领租约过期），由新的 relay 重试。重复发布同一个 job ID 是允许的，worker 的持久条件领取负责去重。

![API 收到通知即关本地门闩、不等路由传播；worker 独立停止领取，归还未启动的预取投递，运行中的 attempt 完成后先持久提交再 ACK，否则不 ACK，由重投与租约恢复器接手。](../../engineering-foundations/practice/resources/runtime-api-and-worker-shutdown.svg)

#### 平台的摘流顺序不能当成一条通用时间线

不同平台摘流和发停止信号的先后不同，不能合并成一条通用时间线，也不能假设只把 readiness 置为 false 就完成了摘流。

> [!info] 实例：Kubernetes 与 Amazon ECS 的停止顺序（核对于 2026-11-12）
> **Kubernetes v1.37。** 删除 Pod 时，控制面更新 EndpointSlice 与 kubelet 在节点上开始容器的优雅停止**同时**进行。终止中的 endpoint 可以暂时留在 EndpointSlice 里，但标为 `ready: false`，不是物理删除。默认的 Service 代理通常忽略 terminating (正在终止) 的 endpoint；若所有可用端点都在终止，可能路由到同时处于 `serving` 和 `terminating` 的端点；设置了 `publishNotReadyAddresses` 的 Service 会把 `ready` 置为 true。集群代理、入口控制器和 Service 配置都会影响实际路由。
>
> **Amazon ECS。** 只有 service task 配置了负载均衡目标组时，任务才会**先**在 `DEACTIVATING` 注销目标，**再**进入 `STOPPING`，通知 Linux 容器停止。正常停止信号默认是 `SIGTERM`；超过容器定义字段 `stopTimeout` 后发 `SIGKILL`。Fargate 未设置时默认 30 秒、最大 120 秒；ECS on EC2 未设置时用 agent 的 `ECS_CONTAINER_STOP_TIMEOUT`，都没配置则默认 30 秒。

#### 宽限期要覆盖整条关停路径

平台给的宽限期必须覆盖停止领取、排空、提交或归还、清理全部步骤。反过来说，进程自己的内部 deadline 加上实测的清理余量，必须落在平台的强杀时刻之前。主线二的关停回放用 1 秒内部 deadline 演示分支，在 Fargate 默认 30 秒的宽限期里有足够余量；换到下面 PM2 的默认值，就要重新核对。外部的强杀只是让进程消失，不能替代持久任务的恢复和未知副作用的对账。

> [!info] 实例：PM2 的停止信号与截止时间（核对于 2026-11-12）
> PM2 是 Node.js 常用的进程管理器，可以显式指定实例数（如 `pm2 start app.js --name api -i 2`），用 `pm2 list` 或 `pm2 monit` 查看，用 `pm2 reload api` 发起集群重载；reload 超时后会退回普通 restart。在支持 POSIX 信号的平台上，PM2 在 stop、restart 和 reload 时默认先发 `SIGINT`（可用 `PM2_KILL_SIGNAL` 改成别的信号），`kill_timeout` 默认 1600 ms，到期后发 `SIGKILL`。应用要处理部署环境实际发来的那个信号，并让自己的排空 deadline 加清理余量小于 `kill_timeout`，或者相应调大它。

### 网络可达、工作负载身份、用户授权三层不可互替

每个角色上线前都要回答“它能连到哪、能对哪些资源做什么、替谁做”。这是三层不同的控制，任何一层都替代不了另外两层：

1. **网络可达**：路由、防火墙或安全组决定“谁能连到哪个地址”。
2. **工作负载身份**：服务主体及资源策略决定“这个进程能对哪个资源做什么”。
3. **用户业务授权**：API 和 worker 的业务逻辑决定“当前用户能否读取 acct-17 的报表 42、能否导出它”，规则在[逐次授权章](#36.%20%E6%9C%8D%E5%8A%A1%E6%80%8E%E6%A0%B7%E9%80%90%E6%AC%A1%E7%A1%AE%E8%AE%A4%E8%BF%99%E4%B8%AA%E4%B8%BB%E4%BD%93%E8%83%BD%E5%AF%B9%E8%BF%99%E4%BB%BD%E8%B5%84%E6%BA%90%E5%81%9A%E8%BF%99%E4%B8%AA%E5%8A%A8%E4%BD%9C%EF%BC%9F)。

HTTPS 只加密浏览器到入口之间的传输，不替 API 授权当前主体。常见拓扑只公开应用的 HTTPS 入口；API 只接受负载均衡器转来的请求；数据库只允许 API、worker、relay 和租约恢复器各自的私有网络身份接入，并配合最小 SQL 权限：

| 角色 | 网络上要到达 | 身份与数据权限边界 |
|---|---|---|
| API | 数据库；签名下载 URL 可用本地凭据生成，不必代理对象文件 | 从真实会话或令牌取得当前主体，逐请求检查账户与报表权限；按账户范围读报表、成员关系、授权与 job 状态；只写受理事务需要的 job、outbox 与等待槽；签名身份只获准读对应的结果对象 |
| outbox relay | 数据库 + broker | 只认领待发意图并更新同一条意图；只向获准的队列发布；不承载用户授权 |
| worker | 数据库 + broker + 私有对象存储 | 按 job 的账户范围读取报表输入和当前授权；只更新被条件领取的 job/attempt；对象写入限制在报表前缀；先持久业务结果，再 ACK |
| 租约恢复器 | 用独立私有网络身份直连数据库；重排意图由 relay 另行发布 | 独立数据库主体（如 `runtime_recovery`），只读扫描与竞争所需的 job 标识、状态、attempt、租约截止时间和取消标志；用条件事务接管、重排（同时预留等待槽并插入待发意图）或写终态；不读报表内容，没有 broker 发布权，不替用户授权 |
| 浏览器下载 | 持 URL 直达浏览器可达的对象存储 HTTPS 端点，不经 API | URL 只授予被签名的那个对象操作、有效期有限；对象存储的资源策略仍须允许这条来源路径；浏览器拿不到 worker 的云角色 |

worker 的一条规则值得单独说：队列消息只带 job ID，worker 读输入前要以服务身份复核发起主体当前仍有 `report:export`；已被撤销就持久写入 `failed` 和有界错误码 `authorization_revoked`，不读报表。消息 ID、worker 的云角色或“当初提交时有权限”都不能代替这次复核。

### 每个运行角色拿着哪种凭据

“凭据”在运行时里至少有三种，它们代表不同的主体：

| 凭据 | 代表谁、用来做什么 | 谁能读取或验证 | 怎样撤销 |
|---|---|---|---|
| 工作负载临时凭据（如 ECS task role） | 一个运行中的任务调用云 API，例如 worker 向报表前缀写对象 | 该任务里的应用容器 | 角色、目标资源策略或任务凭据失效；不能替用户授予报表访问权 |
| HMAC 共享密钥（如 webhook 签名密钥） | 发送端签名、接收端验证同一来源的消息 | 两端都持有同一个密钥值 | 接收端停用 keyId，部署移除旧值，并停掉持有旧值的进程 |
| 用户 OAuth grant (用户授权) | 某个用户允许应用访问特定下游资源和 scope | 只在绑定的用户、账户、audience 和 scope 上下文中使用 | 用户撤权、授权到期或 provider 撤销；不影响其他用户的 grant |

三条要点：

- **工作负载凭据不是用户授权。** 它说明“这个进程能写这个前缀”，不说明“这个用户能导出这份报表”。支持的 SDK 标准凭据提供程序会自动取得并更新临时凭据；应用不要把它复制成长期静态密钥。
- **HMAC 是对称的。** 持有密钥的任何一方都能算出有效签名。把发送端和接收端拆成不同进程、不同角色，能缩小其他 Secret 和业务动作的暴露面，却不能在密码学上保证接收端“只能验、不能签”；真要分离签名权与验证权，就用非对称签名。
- **用户 grant 按用户隔离。** Refresh Token 不进所有 worker 共享的环境、日志、模型上下文或恢复快照，只为已绑定的那个用户 grant 取用。会话与令牌的身份边界见[会话与浏览器边界章](#35.%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E5%B8%A6%E4%B8%8A%E5%8F%AF%E4%BF%A1%E7%9A%84%E8%BA%AB%E4%BB%BD%EF%BC%8C%E6%B5%8F%E8%A7%88%E5%99%A8%E5%8F%88%E6%9B%BF%E6%9C%8D%E5%8A%A1%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%BE%B9%E7%95%8C%EF%BC%9F)。

> [!info] 实例：ECS 的两种角色与任务隔离（核对于 2026-11-12）
> ECS 区分 task execution role (任务执行角色) 和 task role (任务角色)。task definition (任务定义) 引用 Secrets Manager 中的 Secret ARN，不写密钥值；execution role 授予 ECS agent 在启动任务时读取指定 ARN 的 `secretsmanager:GetSecretValue`（用客户自管 KMS key 时还要 `kms:Decrypt`），用来取值并注入，不直接提供给应用代码。task role 只控制应用运行期的 AWS API 动作。Linux Fargate 在 task 之间提供隔离边界，但同一个 task 里的多个容器共享该 task 的权限，互不信任的应用不要放进同一个 task；ECS on EC2 上并置 task 与宿主机的访问边界不同，ECS 文档明确说明容器本身不是安全边界。

### 注入的密钥要替换任务才会更新

许多平台在进程启动时把密钥注入环境变量。这带来一条运行时规则：**改了密钥存储里的值，运行中的进程不会知道，必须启动新进程。** 所以进程能安全停止和替换，是凭据轮换的前提。

几条做法：

- **一次读取拿到一致的一组值。** 若把 keyId 和 key 分成两个值分别注入，两次读取之间当前版本可能恰好移动，结果新 key 配上旧 keyId；把它们放在同一个 JSON 值里注入就避免了这种错配。
- **轮换靠替换任务。** 跟随“当前版本”标签时，移动标签后要强制滚动部署；固定版本号时，先发布引用新版本的任务定义修订，再替换任务。删除 Secret 的值也清不掉进程里已注入的副本，同样要替换任务。
- **环境变量会被读到。** 容器内的应用、日志和调试工具都可能读环境变量：不要 dump 环境，不要在异常里回显配置，也不要把密钥放进镜像层、版本库、命令参数、前端 bundle、请求日志或模型的 prompt 与检查点。
- **轮换顺序由协议决定。** 共享密钥的正常轮换是“接收端先同时接受新旧键 → 发送端切到新键 → 等旧签名在每个接收端都已过期且在途验证结束 → 接收端移除旧键”；密钥泄漏时不留新旧双接受窗口。完整序列与等待时长的推导在 [webhook 支线](#42.%20%E6%94%B6%E5%88%B0%E4%B8%80%E6%9D%A1%20webhook%20%E5%9B%9E%E8%B0%83%E6%97%B6%EF%BC%8C%E6%80%8E%E6%A0%B7%E7%A1%AE%E8%AE%A4%E5%AE%83%E7%9C%9F%E5%AE%9E%E3%80%81%E6%9C%AA%E8%A2%AB%E9%87%8D%E6%94%BE%EF%BC%8C%E5%B9%B6%E5%8F%AF%E9%9D%A0%E5%9C%B0%E5%8F%97%E7%90%86%EF%BC%9F)，本章只负责“每一步都要替换对应的任务”。

> [!info]- 实例：ECS 注入 Secrets Manager 密钥与审计（核对于 2026-11-12）
> ECS `valueFrom` 可以引用完整 secret、其中的 JSON key、version-stage 或 VersionId；不指定 stage 或 VersionId 时默认读取 `AWSCURRENT`，两种版本选择不能同时指定。Linux Fargate 注入特定 JSON key 或版本要求平台版本 1.4.0 或更高，注入完整 secret 至少要 1.3.0。Secret 在 task 启动时注入，移动 staging label 不会更新运行中任务的环境变量，必须启动新 task 或强制服务滚动部署。
>
> 把 Secret 读取与业务 API 调用分开审计。`GetSecretValue` 会产生 CloudTrail 事件，可以查哪个授权主体请求了哪个 Secret ARN，但不能假设事件里带 taskArn 或 API 响应中的 VersionId；API 响应本身含 VersionId，SecretString/SecretBinary 不进入 CloudTrail。要证明每个运行中的 task 实际解析了哪个版本，就固定 VersionId，或使用平台确实提供的非敏感解析版本证据；只凭任务定义修订和标签移动时间线，断言不了竞态期间每个 task 读到哪一版。应用用 task role 调用 AWS API 的 CloudTrail 会话可带 taskArn，但这条业务调用审计替代不了 Secret 注入审计；审计轨迹也不能单独证明 IAM 策略和对象前缀已经最小化。

### 预签名下载 URL 是持有者凭据

导出结果的下载走另一条路径。只有任务结果和对象引用已持久、API 已按当前用户授权，API 才签发一个短期 URL；浏览器随后直接向对象存储请求，不经过 API 的数据路径。

![应用请求经可选 CDN 与负载均衡器到达私有 API；签名下载是另一条 HTTPS 路径，浏览器直达对象存储端点，端点可达与对象策略放行都要成立。](../../engineering-foundations/practice/resources/runtime-network-and-identities.svg)

这个 URL 是 bearer token (持有者令牌)：谁拿到谁就能用，不能当成可以公开缓存的普通地址。它有三个容易被误解的性质：

- **它按签发者的权限授权，而不是按用户。** 应用撤销用户的业务权限，不会撤销已经签发的 URL。所以有效期要短，签发前的授权检查不能省。
- **它在有效期内可以重复使用。** 实际有效期还不超过签发所用临时凭据的到期时间；这些凭据被撤销、删除或停用，URL 也随之失效。
- **“对象私有”不等于“浏览器连不上”。** 浏览器必须能到达被签名的对象存储端点，资源策略也要允许这个请求上下文；若策略只允许来自指定 VPC endpoint 的请求，没经过该端点的浏览器即使签名正确也会被拒绝。

浏览器网络不能直达对象存储时，可以经应用代理或配置私有源站的 CDN 提供下载。CDN 还需要单独设置签名访问、私有源站和缓存策略，保证用户不能绕过 CDN 直接访问源对象；不能照搬公共静态文件的缓存规则，CDN 签名 URL 与对象存储签名 URL 的签名方式也不是一回事。

> [!info] 实例：Amazon S3 与 CloudFront（核对于 2026-11-12）
> 本例的对象存储是 Amazon S3。worker 的 task role 只需写指定的报表对象前缀，IAM 策略还应限定目标 bucket、前缀和动作；签发下载 URL 的 API task role 需要对目标对象有 `GetObject` 权限。经 CloudFront 分发私有对象时，用其 signed URL 或 signed cookie，并限制直达源站的路径。

### 组件信号只说明组件

每个组件都要预先列出计划中的失败、观察信号和成本边界：

| 组件 | 计划中的失败 | 观察信号 | 成本与限制 |
|---|---|---|---|
| 负载均衡 / 网络 | 错路由、无健康目标、出站受阻、证书过期 | 请求错误、连接失败、健康目标数 | 请求与字节、网络地址转换、数据传输 |
| 计算服务 | 启动失败、崩溃循环、CPU 或内存饱和、扩容慢 | 就绪实例、CPU/内存、重启次数、请求排队 | 最低副本与运行时间；扩容不是瞬时容量 |
| 数据库 | 连接耗尽、锁等待、I/O 或存储、故障切换 | 连接池等待、连接数、查询时延、锁 | 计算、存储、I/O、备份保留 |
| 对象存储 | 权限错误、路由故障、对象意外公开、无限保留 | API 错误、对象增长、下载量 | 存储、请求、生命周期、复制、出站流量 |
| outbox relay | relay 停摆、确认缺失、待发意图反复重试 | 最老待发意图的年龄、认领过期数、发布确认失败 | relay 运行时间、数据库扫描与发布请求 |
| 队列 / worker | 重复或延迟投递、毒消息、积压上升、执行槽耗尽、过期租约被接管 | 最老消息年龄、队列深度、未确认数、死信队列、执行槽占用、过期租约与恢复结果 | 消息保留、worker 计算、积压排空与孤儿对象清理 |

这些信号只反映平台和组件的状态。CPU 不高不证明报表 42 能被正确读取；队列有消费者不代表报表已经生成；relay 停摆时，broker 队列深度看起来反而“正常”，所以要盯最老待发意图的年龄。组件信号要连到用户结果上才有意义。

### 交给下一步的是什么

到这里，`d-new` 的每个角色都有了明确的运行形态、探针、停止顺序、网络身份和凭据，平台能启动、探测和替换它们。但平台说“就绪”、组件信号全绿，都还没有回答用户关心的事：`user-17` 能否在 400 ms 内读到报表，导出能否按时完成。下一章先把这些用户结果定义成可计数的 SLI，再决定还能不能放量：见 [SLI、SLO 与错误预算](#59.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%94%A8%E6%88%B7%E7%BB%93%E6%9E%9C%E8%A1%A1%E9%87%8F%E4%B8%80%E4%B8%AA%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%B9%B6%E5%86%B3%E5%AE%9A%E8%BF%98%E8%83%BD%E4%B8%8D%E8%83%BD%E6%94%BE%E9%87%8F%EF%BC%9F)。

> [!info]- 来源
> - **函数服务的时长、重试与环境复用**（Lambda 实例 callout）：AWS Lambda，[Designing Lambda applications](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html) §“Build for on-demand data instead of batches”、[Lambda execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) §“Invoke phase”，核对于 2026-11-12；只适用于所列 Lambda 模式。
> - **探针语义与 EndpointSlice 条件**（“平台怎样判断进程可以接流量”）：Kubernetes v1.37 文档，[Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)、[EndpointSlice conditions](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/#conditions)、[Deployment API](https://kubernetes.io/docs/reference/kubernetes-api/apps/deployment-v1/)，核对于 2026-11-12。探针文档正文说 EndpointSlice 控制器“移除”Pod IP；v1.37.1 控制器的 [`podToEndpoint`](https://github.com/kubernetes/kubernetes/blob/v1.37.1/staging/src/k8s.io/endpointslice/utils.go#L33-L53) 实际保留地址并写入 `ready: false`，本章按 API 对象行为描述。
> - **Pod 终止与摘流并发**（Kubernetes 停止顺序实例）：Kubernetes v1.37，[Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)、[EndpointSlice conditions](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/#conditions)，核对于 2026-11-12；删除 Pod 时 EndpointSlice 更新与 kubelet 本地终止同时开始，全部端点终止时可路由到 `serving && terminating` 端点。
> - **ECS 停止顺序与超时**（ECS 停止顺序实例）：AWS，[ECS task lifecycle](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-lifecycle-explanation.html)（配置目标组时 DEACTIVATING 先注销）、[ContainerDefinition API](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ContainerDefinition.html)（`stopTimeout`；Fargate 默认 30 秒、最大 120 秒；EC2 上 agent 默认），核对于 2026-11-12。
> - **PM2 信号与截止时间**（PM2 实例 callout）：PM2，[Cluster Mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/)（reload 失败回退 restart）、[Graceful Start/Shutdown](https://pm2.keymetrics.io/docs/usage/signals-clean-restart/)（默认 `SIGINT`，`kill_timeout` 1.6 秒后 `SIGKILL`）、[Environment Variables](https://pm2.keymetrics.io/docs/usage/environment/)（`PM2_KILL_SIGNAL`），核对于 2026-11-12。
> - **工作负载角色、Secret 注入与任务隔离**（“每个运行角色拿着哪种凭据”“注入的密钥要替换任务才会更新”及 ECS 实例）：AWS，[ECS task IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)、[Task execution IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)、[IAM roles best practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html)、[Pass Secrets Manager secrets through environment variables](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html)（版本引用规则、平台版本要求、需强制新部署），核对于 2026-11-12；AWS SDK，[Standardized credential providers](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html)、[Container credential provider](https://docs.aws.amazon.com/sdkref/latest/guide/feature-container-credentials.html)，核对于 2026-11-12。
> - **Secret 读取审计**（ECS 注入与审计实例）：AWS，[GetSecretValue API](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html)（响应含 VersionId，Secret 值不写入 CloudTrail，客户自管 KMS key 需 `kms:Decrypt`）、[CloudTrail entries for Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/cloudtrail_log_entries.html)，核对于 2026-11-12；API 响应字段不等于 CloudTrail 事件字段。
> - **HMAC 是共享密钥构造**（凭据一节）：IETF，[RFC 2104](https://www.rfc-editor.org/rfc/rfc2104.html) §2；签名与验证依赖同一密钥，RFC 不规定 webhook 的 keyId、请求字段或时间期限。
> - **预签名 URL、VPC endpoint 策略与私有 CDN 内容**（“预签名下载 URL 是持有者凭据”）：Amazon S3，[Download and upload objects with presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)、[Controlling access from VPC endpoints with bucket policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-bucket-policies-vpc-endpoint.html)；Amazon CloudFront，[Serve private content with signed URLs and signed cookies](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html)、[Restrict access to files](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-overview.html)，核对于 2026-11-12。
> - **队列取消与归还**（停止一节中 worker 的预取投递）：RabbitMQ 4.4，[Consumers: Cancelling a consumer](https://www.rabbitmq.com/docs/consumers#cancelling-a-consumer-unsubscribing)、[Negative Acknowledgement and Requeuing](https://www.rabbitmq.com/docs/confirms#consumer-nacks-requeue)，核对于 2026-11-12；细节在队列确认章。
## 59. 怎样用用户结果衡量一个服务，并决定还能不能放量？

沿用主线五的案例。`d-new` 已在生产启动，[生产运行时章](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)的探针和组件信号都说它正常，但它们回答不了用户关心的事：`user-17` 能不能及时读到报表 42，`user-29` 是否仍然读不到，导出能不能按时生成、下载。本章把这些用户结果定义成可计数的 service level indicator (服务等级指标，SLI)，再用错误预算和分钟级门禁决定新版本还能不能加流。

本章依次回答：一次用户意图该数成什么单位；一个可下结论的 SLI 要写清哪些要素；读取、受理、完成、下载各怎样判好坏；异步任务的完成率怎样不漏掉还在排队的任务；长期目标和发布决策为什么用不同的时间尺度；新版本为什么不能和稳定版合在一起评估。文中阈值（400 ms、99.5%、2 分钟、10 分钟/100 个/99%/5 分钟）都是本例的合成教学数字，不是通用推荐。

### 先决定数什么：request、job、attempt

同一次“导出报表”的意图，在系统里会留下三种不同的计数单位。分母选错，结论就错：

| 单位 | 怎样计数 | 用来判断什么 |
|---|---|---|
| request (请求) | 每次到达已定义服务边界、满足该 SLI 入选条件的 API 往返；客户端重试会增加请求数 | 按该 API 的用户结果判好坏；未响应的调用不能删掉 |
| job (任务) | 每个唯一的 job ID 一次；受理事务一提交就计入，即使 `202` 响应丢了 | 到自己的完成期限时判定成功、失败或仍未完成 |
| attempt (执行尝试) | worker 每次在数据库里成功领取一次 | 诊断执行耗时、重试和资源占用；不作为用户完成率的分母 |

本例每个 job 最多 3 次 attempt（首次也算一次）。只有数据库里的领取事务提交了，才开始一轮 attempt；broker 的重复投递只是唤醒 worker 的线索，不算新的 attempt。这三种单位来自主线四：job 和 attempt 的定义在[条件领取与栅栏章](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)，同一请求重放为什么指向同一个 job 在[未知结果与重试章](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

### SLI、SLO、SLA 各是什么

- **SLI** 测量一项明确的用户结果，例如“读请求在 400 ms 内得到与授权关系一致的结果的比例”。
- **service level objective (服务等级目标，SLO)** 是团队给某个 SLI 定的内部目标值，例如“30 天内 99.5%”。
- **service level agreement (服务等级协议，SLA)** 是带对外承诺和违约后果的约定。把内部阈值换个名字，并不会变成 SLA。

一个 SLI 不能只写“成功率”。它至少要规定五样东西：测量边界（在哪一层观察）、分母（哪些事件入选）、好事件（什么算好）、时间窗口、数据延迟（多久之后的数才算齐）。另外，按请求加权的汇总值不能证明每个 region (区域) 或用户群的体验一致，必要时按稳定、取值有限的维度（如区域）分开查看。

### 读取 SLI：按授权关系判好坏

**分母**：每次进入 API 的 `GET /v1/accounts/{account_id}/reports/{report_id}`，前提是可信的身份层已确认调用主体、报表 ID 格式有效。身份服务在确认主体之前的失败，另计入入口认证 SLI。

**好事件**：API 在 400 ms 内给出与授权关系一致的结果。`user-17` 是 acct-17 成员，读报表 42 应得到 `200` 和预期报表；`user-29` 属于另一个账户 acct-29，无论经哪个账户路径请求 42，都应得到与不存在的报表 43 相同的通用 `404`。所以 `404` 是好是坏，取决于主体和资源的关系，不能只按状态码分类。

**坏事件**：有权的请求得到 `404`、超时、无响应或 `5xx`；无权的请求得到 `200`。最后这一种正是本主线修复的缺陷：只按全局主键取数时，`user-29` 经 `GET /v1/accounts/acct-29/reports/42` 读到 acct-17 的报表 42，得到 `200`。

入口为每次合格请求记录时间、路由模板、区域和实际处理它的镜像摘要，即使服务没有响应也保留记录。未响应的请求即使归不到某个摘要，也仍是坏事件；它只是不能用来证明新版本健康。

状态码和耗时只是便于观测的代理信号，单凭它们证明不了正文正确。本例另外用 `user-17`、`user-29` 两个受控测试身份和报表中的已知标记核验授权与内容；要声称每次真实响应的内容都正确，就需要每次响应都有可信的内容与授权判定证据。这个 SLI 的边界也不包括用户设备和响应发出后的网络，不能替代跨账户授权测试与审计。

### 受理 SLI：请求与 job 分开数

导出的受理用主线四的例子：`POST /v1/accounts/acct-17/reports`，`Idempotency-Key: export-demo-415`，受理后返回 `202` 和 `Location: /v1/jobs/job-demo-731`。

**请求分母**：每次进入导出 API 的调用，前提是身份已确认、调用主体对 acct-17 有 `report:export`、请求格式有效。同一幂等键的每次重试各算一次请求。

**job 分母**：首次有效请求在同一个数据库事务里提交 job、outbox 待发意图和一个等待槽，才产生一个 accepted job（202 承诺的内容见[持久受理章](#41.%20%E8%80%97%E6%97%B6%E4%BB%BB%E5%8A%A1%E6%80%8E%E6%A0%B7%E8%A2%AB%E6%8C%81%E4%B9%85%E5%8F%97%E7%90%86%EF%BC%8C%E5%B9%B6%E4%BF%9D%E8%AF%81%E4%B8%80%E5%AE%9A%E4%BC%9A%E8%A2%AB%E5%94%A4%E9%86%92%EF%BC%9F)；本例要求 `202` 之前已持久化，比 HTTP 规范对 `202 Accepted` 的通用语义更严格）。job 是否存在以数据库提交为准，与响应是否送达无关；正常返回的 `202` 只是服务看到提交成功后发给客户端的证据。

几种情况怎样计：

- 同一幂等键、同一请求指纹的重放，正确行为是指向原 job 并返回其当前状态：算一条好请求，不增加 job 数，也不占新的等待槽。
- 明确返回 `429`（速率限制）或 `503`（等待槽满）：算坏请求，但按约定不创建 job。
- 在本 SLI 的服务边界内观察到超时或无响应：坏请求。服务已经返回、之后才发生的客户端网络断开，不计入这个 SLI。
- 同一幂等键却带不同正文：客户端违反约定，单独计数，不进可靠性分母。

没收到 `202` 不能推断任务未受理；客户端该怎样用原键原正文重放、取回同一个 job，在[未知结果与重试章](#40.%20%E5%86%99%E8%AF%B7%E6%B1%82%E8%B6%85%E6%97%B6%E5%90%8E%EF%BC%8C%E6%80%8E%E6%A0%B7%E6%9F%A5%E6%B8%85%E7%BB%93%E6%9E%9C%E5%B9%B6%E5%AE%89%E5%85%A8%E9%87%8D%E8%AF%95%EF%BC%9F)。

### 完成 SLI：测的是提交确认时刻

**分母是 job**：每个已提交的唯一 job 只计一次，投递、重试和 attempt 都不增加分母。任务成功指 `succeeded`、结果对象引用和 `report.ready` outbox 在同一事务中原子提交。本例的业务目标是受理后 2 分钟内生成并提交结果。

业务目标说的是“提交”时刻，现有遥测未必测得到。本例能取到的是**提交确认**时刻：应用收到 `COMMIT` 成功响应后，再向同一数据库查询 `clock_timestamp()` 并记录，得到 `accepted_commit_confirmed_at` 和 `succeeded_commit_confirmed_at`。完成 SLI 据此定义：从受理确认起算 2 分钟内，是否观察到成功确认。

这两个确认是分别采集的，它们的差不一定比真实提交间隔更保守。设物理提交间隔为 121 秒，受理那次确认等了 10 秒、成功那次只等了 1 秒，观测到的间隔就是 `121 + 1 − 10 = 112` 秒，低估了实际间隔；反过来也可能高估。受理确认甚至可能晚于成功确认，这时本口径视为达标，但推不出两次提交的实际先后。所以它是一种独立的服务观测口径；要验证“数据库必须在 2 分钟内提交”这一物理时限，需要经过验证的权威提交时刻。

> [!info] 实例：PostgreSQL 里哪个时间是提交时刻（PostgreSQL 18，核对于 2026-11-12）
> 事务内写入的 `accepted_at`、`succeeded_at` 不能直接当提交时刻：`now()`（以及 `current_timestamp`）返回的是事务开始时间，`clock_timestamp()` 才随墙钟变化。开启 `track_commit_timestamp` 后可以用 `pg_xact_commit_timestamp` 查询事务的提交时间，但只对开启之后的事务有效，且这些信息会被 vacuum 清理；不能假设它已开启，也不能假设历史一直保留。

### 成熟窗口：只数已经到期的 job

只统计已经成功或失败的任务，会悄悄漏掉仍在排队的任务：队列越堵，分母越小，完成率反而好看。解决办法是给每个 job 定一个观测期限 `due = accepted_commit_confirmed_at + 2 min`，只在期限到了之后才判它：以 `T` 为窗口结束时刻、`W` 为窗口长度，窗口 `(T−W, T]` 只收入满足 `T−W < due ≤ T` 的“成熟”任务。下图用 12:00 结束的十分钟窗口看三个任务怎样归入，时间均为提交**确认**时刻：

![12:00 结束的十分钟窗口左开右闭：11:57:00 受理的任务 due 11:59:00 在窗口内，11:59:01 才成功，计坏；11:58:00 受理的任务 due 12:00:00 落在右闭端，12:00:01 成功，计坏；11:59:30 受理的任务虽在窗口内受理，due 12:01:30 在窗口外，不进分母。](../../engineering-foundations/practice/resources/sli-mature-window.svg)

- 好事件：`succeeded_commit_confirmed_at ≤ due`。坏事件：`failed`、`cancelled`、到期仍为 `queued` 或 `running`，以及过了期限才成功。本例把受理后的取消也算未完成；若要排除用户主动取消，要另行定义可审计的取消来源和分母规则。
- 期限未到的任务暂不进分母，但要同时观察其中最老任务已经等了多久。
- 图中的“坏”只针对确认口径的 SLI：用时 121 秒推不出物理提交也晚了 1 秒；即使第二个任务事务内的 `succeeded_at` 写的是 11:59:59，也不改变本口径。

窗口结果什么时候能发布：只有当 watermark (事件时间完整水位) 越过 `T`，即 `T` 之前的事件都已收齐，且到期的 job 已逐一与数据库核对后，才发布。任务是否存在仍以数据库中的 job 行为准。缺少受理确认、算不出期限时，把窗口标为“测量不完整”，发布门禁保持不放行；期限已确定、水位越过后仍没有成功确认，就计为坏。不能悄悄删掉缺遥测的任务，也不能用“它现在已经成功了”改写它当时是否按期完成。这套观测期限不改变任务本身的业务期限或租约约定。

### 下载与通知各需要自己的 SLI

完成 SLI 只说明按时观察到了成功提交，不说明用户拿到了文件：

- **下载**：分母是通过身份与资源授权的下载请求（`GET /v1/jobs/job-demo-731/result`），好事件要求服务实际返回该结果引用对应的文件；未授权请求按安全策略单独统计。文件大小差别大时按大小分组设时限，不能套用读取接口的 400 ms。
- **通知**：`report.ready` 还在等 relay 发布，并不撤销已提交的成功。若产品承诺通知必达，就另设通知投递 SLI。broker 确认或消费者 ACK 只说明消息交接到了哪一步（见[队列确认章](#44.%20%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)）。

若报表包含模型生成的内容，HTTP 可用性和任务完成率只衡量服务有没有交付；内容质量要单独评估，不混进同一个 SLI，见 AI 部分的[生产 trace 与指标分母](../../ai-engineering/evaluation-and-release/production-traces-and-metric-denominators.md)。

### 错误预算：长期目标允许多少坏事件

SLO 再进一步，就能算出 error budget (错误预算)。本例读取 SLO 是 30 天 99.5%。若窗口内有 10,000 个合格读请求，其中 9,940 个在 400 ms 内给出了正确结果：

- SLI 为 `9,940 ÷ 10,000 = 99.4%`。
- 允许的坏请求数是 `(1 − 0.995) × 10,000 = 50`。
- 实际坏请求 60 个，超预算 10 个，即用掉了 `60 ÷ 50 = 120%` 的预算。

错误预算的单位是窗口里的坏事件数，不是百分比或毫秒。burn rate (错误预算消耗率) 是实际坏事件率与 SLO 允许的坏事件率之比：这里 `0.6% ÷ 0.5% = 1.2`：大于 1 表示预算消耗得比 SLO 允许的快，照 1.2 的速率，30 天的预算约在第 `30 ÷ 1.2 = 25` 天用完。长期 SLO 告警可以按 burn rate 组合一长一短两个窗口：长窗口确认问题不是偶发，短窗口让告警在问题消失后尽快复位。Google SRE Workbook 给出的是配置方法和起始示例，其中具体的比例和窗口不应直接套到所有服务。

### 金丝雀门禁用分钟级窗口

30 天的目标用来跟踪长期预算；金丝雀决策要在分钟级做出，等不到 30 天结束。本例的发布门禁：

- **统计对象**：按目标摘要、路由模板和区域分别统计。
- **样本条件**：滚动 10 分钟窗口内至少有 100 个合格读请求。
- **止损条件**：满足样本条件时，好事件比例低于 99%，并**持续 5 分钟**。“持续 5 分钟”定义为每分钟评价一次，从 `t` 到 `t+5` 的六个评价点都满足样本数和比例条件。

所以只观察到一次 `98/100`，只够暂缓加流，还不满足持续止损条件；`99/100` 恰好达到比例门槛，但仍要通过身份与内容检查。有另一条告警需要连续越界 5 分钟才触发时，“告警没响”也不能代替当前的放量条件。这条门禁怎样变成“加流、保持还是止损”的判定，在[金丝雀章](#60.%20%E6%96%B0%E7%89%88%E6%9C%AC%E6%80%8E%E6%A0%B7%E9%80%90%E6%AD%A5%E6%94%BE%E9%87%8F%EF%BC%8C%E5%87%BA%E9%97%AE%E9%A2%98%E6%97%B6%E8%83%BD%E6%92%A4%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)。

告警要附上好与坏事件数、分母、窗口、摘要、路由与区域，以及指标和追踪的查询链接，让值班人能核对门槛是否基于同一个 SLI。导出完成率另按成熟 job 窗口计数，同时看未成熟 job 中最老任务的等待时长，以免“完成率还没变差”掩盖排队正在变长。

### 金丝雀不能和稳定版合在一起评估

新版本只承担一小部分流量，合并统计会把它的问题平均掉。设同一路由、同一区域、同一窗口里，`d-new` 是 `98/100`，稳定版 `d-old` 是 `900/900`：

- `d-new` 自身是 98%，低于 99% 的门槛；
- 合并后是 `998/1,000 = 99.8%`，看起来完全健康。

`d-old` 的 900/900 也不说明它安全：它正带着跨账户缺陷，这 900 个读取都好，只是因为受影响的入口已经隔离（见[金丝雀章](#%E5%B0%B1%E7%BB%AA%E4%B9%8B%E5%90%8E%E3%80%81%E5%BC%80%E6%B5%81%E4%B9%8B%E5%89%8D%EF%BC%9A%E7%94%9F%E4%BA%A7%E5%86%92%E7%83%9F%E6%A3%80%E6%9F%A5)），跨账户读取到不了它的缺陷代码。

所以门禁只统计能归因到目标摘要的请求（多平台发布还要归到实际运行的平台子摘要）。归不到摘要的无响应请求仍留在总分母里，但它们不能当作目标版本的健康样本，发布判断应保持不放量。判断恢复时也用同样的口径：看变更后实际运行的摘要，用新的时间窗口。

### 交给下一步的是什么

本章产出了一组可以下结论的度量：读取、受理、完成、下载各自的分母和好事件，按成熟窗口判定的完成率，30 天错误预算，以及按摘要分开统计的分钟级门禁。下一章用它们回答：`d-new` 开放首轮小流量之前要做什么检查，每一轮怎样在加流、保持和止损之间判定，出问题时又能撤回什么，见[金丝雀放量与回退](#60.%20%E6%96%B0%E7%89%88%E6%9C%AC%E6%80%8E%E6%A0%B7%E9%80%90%E6%AD%A5%E6%94%BE%E9%87%8F%EF%BC%8C%E5%87%BA%E9%97%AE%E9%A2%98%E6%97%B6%E8%83%BD%E6%92%A4%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - **用户结果型 SLI、错误预算与 burn rate 告警**（“SLI、SLO、SLA 各是什么”“错误预算：长期目标允许多少坏事件”“金丝雀门禁用分钟级窗口”）：Google SRE Workbook，[Implementing SLOs](https://sre.google/workbook/implementing-slos/)、[Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)（burn rate 定义与多窗口告警），核对于 2026-11-12。本章的 30 天、400 ms、99.5%、2 分钟与 10 分钟/100 个/99%/5 分钟是合成教学数字，不是该书的统一建议。
> - **`202 Accepted` 的通用语义**（“受理 SLI：请求与 job 分开数”）：IETF，[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3) §15.3.3，核对于 2026-11-12；通用语义不承诺操作最终成功，“提交后才回 202”是本例更强的应用合同。
> - **事务时间与提交时间**（PostgreSQL 实例 callout）：PostgreSQL 18，[Current Date/Time](https://www.postgresql.org/docs/18/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT)（`now()` 为事务开始时间，`clock_timestamp()` 随墙钟变化）、[System Information Functions](https://www.postgresql.org/docs/18/functions-info.html)（`pg_xact_commit_timestamp` 依赖 `track_commit_timestamp`，信息会被清理），核对于 2026-11-12。
> - **job、outbox 与等待槽的受理合同、成功提交的原子性**（受理与完成 SLI 的计数依据）：本领域主线四的持久受理、条件领取与队列确认三章；数据库是任务状态的权威。
## 60. 新版本怎样逐步放量，出问题时能撤回什么？

沿用主线五的案例。`d-new` 已在生产以同一摘要启动并通过就绪探针（见[生产运行时章](#58.%20%E6%9C%8D%E5%8A%A1%E8%AF%A5%E8%B7%91%E5%9C%A8%E5%93%AA%E7%A7%8D%E8%BF%90%E8%A1%8C%E6%97%B6%E4%B8%8A%EF%BC%8C%E5%B9%B3%E5%8F%B0%E6%80%8E%E6%A0%B7%E5%90%AF%E5%8A%A8%E3%80%81%E6%8E%A2%E6%B5%8B%E5%92%8C%E5%81%9C%E6%AD%A2%E5%AE%83%EF%BC%9F)），[上一章](#59.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%94%A8%E6%88%B7%E7%BB%93%E6%9E%9C%E8%A1%A1%E9%87%8F%E4%B8%80%E4%B8%AA%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%B9%B6%E5%86%B3%E5%AE%9A%E8%BF%98%E8%83%BD%E4%B8%8D%E8%83%BD%E6%94%BE%E9%87%8F%EF%BC%9F)定义了按摘要统计的读取 SLI 和分钟级门禁：滚动 10 分钟、至少 100 个合格请求，好事件低于 99% 且持续 5 分钟即止损。本章回答：开放第一个真实请求之前还要检查什么；每一轮怎样在加流、保持和止损之间判定；HTTP 入口放量为什么管不到 worker；止损时能退到哪里，数据库结构和外部副作用又为什么不会跟着回去。章末一节换到前端，看独立部署的微前端怎样共存与回退。

### 就绪之后、开流之前：生产冒烟检查

**先处理稳定版。** 本例的 `d-old` 正带着这次要修的跨账户缺陷：`user-29` 经 `GET /v1/accounts/acct-29/reports/42` 能读到 acct-17 的报表 42。若直接开放 10% 金丝雀，留在 `d-old` 的 90% 流量里，走这条路径的请求仍在泄露。所以开放金丝雀之前，先隔离受影响的入口，让跨账户读取到不了 `d-old` 的缺陷代码：

- **用不依赖 `d-old` 代码的控制。** 例如在入口为交给 `d-old` 的这条读取路由加一道临时的归属预检（报表不属于路径里的账户，就直接返回与报表 43 相同的通用 `404`），或者暂时停用受影响的功能。本例用前者。
- **只加在交给 `d-old` 的流量上。** 钉到 `d-new` 的冒烟请求不经过它，冒烟检查检验的才是修复本身。
- **它只是止血。** 隔离只挡住这一条已知路径，缓存、导出等旁路仍要靠修复版；它是否生效，要用 `user-29` 经 `d-old` 复测确认。

就绪只说明平台可以把新流量发给实例。开放真实流量前，先做一次 production smoke test (生产冒烟检查)：经生产入口的受控测试路由，把 `user-17` 经 acct-17、`user-29` 经 acct-29 读取报表 42 的请求都钉到 `d-new` 上。测试路由必须走正常的认证和授权逻辑。期望结果是 `user-17` 得到 `200` 和预期内容，`user-29` 得到与报表 43 相同的通用 `404`，并且两条追踪都显示请求命中了 `d-new`。

判断规则：

- 任一身份的结果错误：不开放流量，先定位业务错误。
- 追踪、版本或摘要证据缺失，或平台无法保证两条请求都命中 `d-new`：同样不开放，先补齐证据。
- 多平台发布：还要确认实例实际运行的平台子摘要等于该平台验收过的子摘要（见[晋级章](#%E5%A4%9A%E5%B9%B3%E5%8F%B0%E9%95%9C%E5%83%8F%E9%AA%8C%E6%94%B6%E7%9A%84%E6%98%AF%E5%93%AA%E4%B8%AA%E5%B9%B3%E5%8F%B0)）。
- 两条都通过，且上面的隔离已确认生效：才开放本例的首轮 10% 真实 HTTP 流量。10% 只是示意起点，不是通用比例。

三种检查各回答一个问题：readiness 说明平台可以发流量；冒烟检查验证目标版本的关键业务路径；之后的用户 SLI 按版本统计，说明真实用户经过它时结果如何。

### 每一轮怎样判定：加流、保持、止损

每一轮都要有完整、可归因到本轮目标摘要的证据：先用冒烟检查对目标摘要重测两个身份，并从追踪确认版本与摘要；再只统计属于该版本的合格请求、错误与延迟、依赖容量，以及 worker 的最老消息年龄、未确认消息数和代表性任务结果。版本标签缺失、聚合数据分不清新旧版本，或两个身份没有命中新摘要，都不拿稳定版的结果替新版本背书。

然后按三分规则判定：

| 观察结果 | 动作 | 为什么 |
|---|---|---|
| 样本达到窗口要求、遥测完整、SLI 达到加流门槛、两个身份都命中新摘要并通过、依赖与任务信号在门槛内 | **加流**：按预定小步提高比例，每次都用目标版本的新窗口复核；到 100% 后检查最终窗口，全部门禁仍达标才结束放量 | 只有可归因到本轮版本、达到门槛的代表性结果，才能支持更多用户经过它 |
| 样本不足、身份测试未确认命中、业务测试未执行、遥测缺失或聚合延迟；或 SLI 低于加流门槛但未越过止损线 | **保持**当前比例，调查指标，补齐身份测试或版本遥测，拿到完整窗口再判 | 未达加流门槛就不能加流；没触发止损也不等于必须回退。不确定不记作成功 |
| 授权契约失败，或错误、延迟、依赖饱和、任务结果越过预定的止损线 | **止损**：停止加流，限制或移除问题版本的流量，检查安全候选，执行回退、隔离或前向修复 | 已确认的用户伤害不能靠尚未触发的告警门槛抵消 |

授权失败单独处理：`user-29` 读到 acct-17 的内容，就是已确认的数据泄露，不能被 99% 的汇总成功率平均掉，必须立即止损，不等统计窗口。

套用上一章的门禁：某一分钟的评价点看到 `d-new` 为 `98/100`，低于 99%，但还没持续 5 分钟，落在第二行，**保持**并调查；若此后六个评价点都满足样本条件且低于 99%，就进入第三行。

![逐轮判定只用可归因到本轮摘要的证据：达标加流，未达标但未越线保持，越线或授权失败止损；回退或前向修复后都要复验摘要、配置、两个身份的结果和 worker。](../../engineering-foundations/practice/resources/application-deployment-decision.svg)

**低流量怎么办。** 10% 的流量在一个窗口内未必凑得够 100 个合格的 `d-new` 请求。若要把合成请求计入分母，就在度量定义里事先写明并单独标记，不能把反复运行的测试身份伪装成真实用户流量。低流量服务可以结合冒烟检查、依赖与任务信号，或改用更长但同样事先定义好的窗口。无论哪种，样本不足时都保持当前比例。

### HTTP 入口放量管不到 worker

上面的放量只控制 HTTP 入口。入口按版本或实例权重分配新请求，不会停止旧 worker，也不会让新 worker 自动切换队列消费；API 的 readiness 只影响 API 流量。发布 worker 要单独决定：是否暂停旧消费者，在途任务等待完成还是交还（见[生产运行时章](#%E5%81%9C%E6%AD%A2%E6%97%B6%E5%90%84%E8%A7%92%E8%89%B2%E6%80%8E%E6%A0%B7%E5%85%B3%E9%97%A8)），启动多少新消费者，以及用队列年龄和 ACK 观察切换是否正常。

还有一条兼容性约束：发布期间，API、relay 和 worker 对数据库结构和消息字段的兼容期，必须覆盖所有已经受理的任务。队列里可能还有旧版本 API 受理、旧格式的消息，outbox 里可能还有尚未发布的旧意图；升级不能假定队列里只剩新版本消息。

### 回退前先确认目标当前安全、数据兼容、有容量

止损时，“回到上一个版本”并不总是安全。每次发布前要记下：当前稳定的镜像摘要、配置版本、入口路由比例、worker 部署状态、数据库结构版本和候选回退摘要；secret 只记版本或引用，不复制值；数据库变化和远端副作用要列出兼容条件。

回退目标要同时满足三个条件：

1. **当前安全。** 目标版本不能带着已知会伤害用户的缺陷。本例的 `d-old` 过不了这一条：它正带着这次修复的跨账户缺陷，简单切回去就是重新打开泄露。所以顺序是先确认受影响的入口仍被隔离，再回退到已证明安全的版本（可能是更早的某个修复版），或者前向发布修复。切回 `d-old` 只在隔离持续生效时才成立，而且只是争取时间的临时状态，修复仍要前向发布。任何版本都不满足条件时，就隔离受影响的入口或功能，停掉危险的 worker 消费，直接前向修复。
2. **与当前数据兼容。** 旧代码要能读写新版本运行期间写下的数据，见下一节。
3. **有容量。** 候选版本已运行、就绪且容量足够时，入口可以直接把新请求切回它、把问题版本的权重降到零；候选已下线或容量不足，就先按记录恢复准确的摘要和兼容配置、补足容量，等它就绪后再切流。

切流只是控制面提出的期望状态。回退或前向修复之后还要核对：问题摘要已不再接请求；实际运行的目标摘要和配置正确；经生产入口用 `user-17`、`user-29` 复测得到 `200` 和 `404`，且追踪确认命中预期摘要（切回 `d-old` 时，`user-29` 的 `404` 来自隔离，要同时确认隔离仍覆盖全部交给它的流量）；worker 的代表性任务和 ACK、队列年龄恢复正常。样本或遥测不足时，保持修复后的低风险状态继续取证，不因“恢复命令执行成功”就宣布完成。

### 数据库结构怎样迁移才能回退：expand/contract

代码可以切回旧摘要，数据库结构却不会跟着回去。所以结构迁移采用 expand/contract (扩展/收缩)：先让新旧版本能共存，确认旧版本不会再回来之后再收缩。设要把旧列 `report_name_old` 换成新列 `report_name`，下图逐阶段画出两列由谁写、读写权威在哪一列、同步朝哪个方向，以及此时还能不能回退到只读旧列的旧版本：

![expand/contract 五个阶段：扩展时旧列是权威；先启用旧到新捕获再回填；新版同事务写两列，异步捕获时按暂停旧侧新写、排空、记水位、追平核对的顺序把权威切到新列；可回退窗口内新列的写入同步回旧列；所有进程和获准恢复的旧版本都不再用旧列后才删除旧列。](../../engineering-foundations/practice/resources/schema-expand-contract.svg)

图上画的是顺序，下面补上为什么必须是这个顺序：

- **先捕获再回填。** 回填读出的是某一刻的快照；若回填开始之后才启用捕获，这之间旧列上的更新就没有记录。防覆盖之外，也可以按提交顺序重放捕获的变更。
- **核对追平不等于可以切换。** 第 2 阶段的核对之后，旧侧仍可能提交写入，所以异步捕获的切换依据是暂停旧侧新写、排空之后记下的最后提交水位。
- **可回退窗口靠反向同步维持。** 新列成为权威后若不同步回旧列，退回只读旧列的版本就会读到过时的事实；切回旧列后若不先恢复旧→新同步，旧版的写入又会让新列落后。

捕获、回填、双写和反向同步的具体实现取决于数据库和业务写入模型；异步捕获必须定义提交顺序、水位和重放与重复处理的语义。独立迁移任务和锁只防止并发执行，不保证任务恰好执行一次；任务还需要版本记录、幂等批次、检查点和可恢复的步骤，重试前先核实部分批次的真实数据库状态。

### 平台自动回退与外部副作用

有些平台提供自动回退，但范围有限，而且不验证业务契约。

> [!info] 实例：Amazon ECS 部署断路器（核对于 2026-11-12）
> ECS rolling deployment (滚动部署) 开启断路器后，任务无法进入 steady state (稳定状态) 时判定部署失败；同时配置了 rollback，就恢复到最近一个 `COMPLETED` 部署。它只适用于 rolling update 部署类型，并要求之前有已完成的部署；不是 canary、蓝绿部署或其他平台的通用保证。任务健康也不验证账户授权和 worker 业务契约，切回后仍要做前面的入口与任务复验。

无论应用是否回退，都不会自动撤销已经提交的 job、已被引用的对象、已发出的邮件或已完成的支付。要恢复的外部效果必须有对应的补偿、幂等和审计边界；从数据库备份恢复可能丢掉备份之后的写入，是一个单独的数据恢复决策。发布版本、安全状态、数据兼容和外部效果要一起复核，才能确认止损完成。回退只撤回平台管理的那部分。AI 系统的发布单元是模型、提示词、工具等组成的版本组合，同一套判定在那里的应用见[AI 部署、放量与回滚](../../ai-engineering/evaluation-and-release/deployment-rollout-and-rollback.md)。

### 微前端：独立部署的前端怎样共存与回退？

前面讲的是后端服务的放量。前端拆成独立部署的部分后，同样会遇到“新旧版本并存、按人群分流、回退要求数据兼容”的问题。这里换用页面编辑器的独立例（与报表服务无关），因为它的文档格式最能说明新旧前端怎样共享数据。

#### 先判断是否值得拆

micro-frontend (微前端) 把前端的一部分按业务或团队边界独立开发、集成和发布，集成方式可以是构建时组合、运行时加载，也可以是 iframe 或 Web Components。它是组织与部署边界，不是“把组件拆成多个项目”的同义词。

只有组件库、页面编辑器和资产管理分属不同团队、确实有各自的发布节奏、集成契约也稳定时，拆分才可能减少发布协调。若画布、检查器和资产面板由同一个团队一起发布，一个模块化应用通常更直接；若当前的问题是两处各存一份节点副本，拆成微前端只会把同步问题推给跨应用通信。运行时集成还会新增路由、深链、身份传递、样式隔离、依赖版本、可访问性、故障处理和监控等方面的契约，这些成本要由独立发布的收益抵消。

#### 外壳持有路由，按 cohort 分流

设编辑器入口要从 `/editor/assets/42?panel=inspector&node=heading-1` 逐步迁到 `/assets/42/edit?panel=inspector&node=heading-1`，由新版 `EditorV2` 接替旧版 `EditorV1`。shell (应用外壳) 持有顶级路由、公共导航和错误边界；新旧地址先并存，避免旧书签和历史项没有去向：

| 地址 | 外壳的选择 |
|---|---|
| 旧地址 | 迁移窗口内继续交给 V1 |
| 新地址，用户不在 cohort (灰度分组) 中 | 交给 V1，不显示空白占位页 |
| 新地址，用户在 cohort 中 | 加载 V2，显示加载或失败状态 |

这是一种契约选择；也可以让子应用共享同一个路由器，或在构建时组合，但不能让两个互不知情的路由器同时争抢浏览器历史。几条配套规则：

- **路由格式是跨应用契约。** 改路径或参数时，要更新所有链接来源和消费者；子应用通过明确的 `navigate()` 或同源链接请求跨边界导航。
- **服务端配合。** 对这些前端深链地址都返回外壳的 HTML，由前端路由接手；`/api/` 下的请求仍交给 API 服务。
- **URL 参数只是界面状态。** `node=heading-1` 是可恢复的选择，不是文档内容；文档加载后再与该修订的稳定节点 ID 对照，节点不存在就清除选择并照常显示，不把参数当成任意资源的读取入口。

深链里的 fragment 定位、`pushState`/`replaceState` 与 `popstate` 的细节，见前端的[导航历史与 URL 状态](../../frontend/browser/navigation-history-and-url-state.md)。子应用之间怎样传递身份、为什么同页加载的远程脚本不构成隔离，见[会话与浏览器边界章](#35.%20%E8%AF%B7%E6%B1%82%E6%80%8E%E6%A0%B7%E5%B8%A6%E4%B8%8A%E5%8F%AF%E4%BF%A1%E7%9A%84%E8%BA%AB%E4%BB%BD%EF%BC%8C%E6%B5%8F%E8%A7%88%E5%99%A8%E5%8F%88%E6%9B%BF%E6%9C%8D%E5%8A%A1%E5%AE%88%E4%BD%8F%E5%93%AA%E4%BA%9B%E8%BE%B9%E7%95%8C%EF%BC%9F)；这里只需记住，客户端“能显示这个路由”不代替服务端的逐次授权，授权拒绝也不能被误判成代码加载失败而静默切换版本。

#### 新旧版本并存时的数据兼容与回退

这与上面的 expand/contract 是同一个问题，只是数据在文档格式里：

- **新字段。** V2 要写 V1 不认识的新字段，前提是 V1 会原样保留未知字段，或路由能保证旧版不再打开这些文档。V1 若只是忽略未知字段，下次保存时就可能把它删掉。
- **删除或改语义。** 要等旧版不再负责读写这些文档。
- **加载失败的回退。** V2 加载失败若发生在用户开始编辑之前，可以安全地把新地址映射回 V1；编辑开始之后若已有未保存的草稿，就先转换并交接草稿，或留在当前编辑器给出错误，不能静默切回而丢掉用户的修改。

上线按路由逐步更换处理者：先验证外壳能加载两版并保持同一输入契约；再把新地址的一小组 cohort 交给 V2；检查直接深链与刷新、Back/Forward、未授权请求、V2 代码块加载失败、V1/V2 文档兼容与草稿保留，再扩大分流。V2 错误率越过预设门槛，就把新地址重新交给 V1。有效回退还要求 V1 的代码仍可加载、且兼容当前数据格式；只把流量开关拨回去，却没有旧代码或兼容格式，并不能恢复服务。构建资源的版本并存与缓存见[前端构建产物](../../frontend/delivery/build-pipeline-and-bundling.md)。

### 交给下一步的是什么

本章给出了放量的完整判定：开流前的冒烟检查，每一轮按版本归因的三分规则，worker 与兼容期的单独控制，回退目标的三个条件，以及数据库结构与外部副作用为什么不随回退复原。剩下的问题是：真的越线了、用户结果变坏时，怎样从信号走到根因，又怎样用同一口径确认已经恢复？见[事故诊断与恢复](#61.%20%E5%8F%91%E5%B8%83%E5%90%8E%E7%94%A8%E6%88%B7%E7%BB%93%E6%9E%9C%E5%8F%98%E5%9D%8F%EF%BC%8C%E6%80%8E%E6%A0%B7%E4%BB%8E%E4%BF%A1%E5%8F%B7%E8%B5%B0%E5%88%B0%E6%A0%B9%E5%9B%A0%E5%B9%B6%E7%A1%AE%E8%AE%A4%E6%81%A2%E5%A4%8D%EF%BC%9F)。

> [!info]- 来源
> - **放量信号的窗口与门槛**（“每一轮怎样判定”）：本领域 [SLI 章](#59.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%94%A8%E6%88%B7%E7%BB%93%E6%9E%9C%E8%A1%A1%E9%87%8F%E4%B8%80%E4%B8%AA%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%B9%B6%E5%86%B3%E5%AE%9A%E8%BF%98%E8%83%BD%E4%B8%8D%E8%83%BD%E6%94%BE%E9%87%8F%EF%BC%9F)的门禁定义；10 分钟、100 个与 99% 是合成教学值。
> - **ECS 滚动部署断路器**（ECS 实例 callout）：AWS，[Deployment failure detection](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-failure-detection.html)、[DeploymentCircuitBreaker API](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentCircuitBreaker.html)，核对于 2026-11-12；仅支持 rolling update，回滚目标需为先前的 `COMPLETED` 部署。
> - **结构变更与代码变更解耦**（“数据库结构怎样迁移才能回退”）：AWS Whitepaper，[Blue/Green Deployments on AWS](https://docs.aws.amazon.com/pdfs/whitepapers/latest/blue-green-deployments/blue-green-deployments.pdf) §“Decoupling schema changes from code changes”、[Best practices for managing data synchronization and schema changes](https://docs.aws.amazon.com/whitepapers/latest/blue-green-deployments/best-practices-for-managing-data-synchronization-and-schema-changes.html)，核对于 2026-11-12。捕获变更、回填防覆盖、水位与反向同步的具体安排是按本例推导的通用做法，实际机制须匹配所选数据库与写入模型。
> - **微前端的收益、集成方式与成本；路由作为跨应用契约**（“先判断是否值得拆”“外壳持有路由，按 cohort 分流”）：Cam Jackson，[Micro Frontends](https://martinfowler.com/articles/micro-frontends.html)，2019-06-19，§Benefits、§Integration approaches、§Downsides、§[Cross-application communication via routing](https://martinfowler.com/articles/micro-frontends.html#Crossapplicationcommunicationviarouting)。
> - **客户端检查不代替服务端授权**（cohort 一节的授权提醒）：OWASP，[Micro Frontend Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Micro_Frontend_Security_Cheat_Sheet.html) §“Authorize Every Request on the Server”、[Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) §“Client-only checks”，核对于 2026-11-12。
## 61. 发布后用户结果变坏，怎样从信号走到根因并确认恢复？

沿用主线五的案例。`d-new` 正承担 10% 的金丝雀流量。12:10 起，用户读取 acct-17 的报表 42 变慢或遇到 `5xx`；同一时段，导出请求已收到 `202 Accepted`，结果却迟迟不来。[SLI 章](#59.%20%E6%80%8E%E6%A0%B7%E7%94%A8%E7%94%A8%E6%88%B7%E7%BB%93%E6%9E%9C%E8%A1%A1%E9%87%8F%E4%B8%80%E4%B8%AA%E6%9C%8D%E5%8A%A1%EF%BC%8C%E5%B9%B6%E5%86%B3%E5%AE%9A%E8%BF%98%E8%83%BD%E4%B8%8D%E8%83%BD%E6%94%BE%E9%87%8F%EF%BC%9F)已经定义了怎样判断这两种用户结果的好坏，[金丝雀章](#60.%20%E6%96%B0%E7%89%88%E6%9C%AC%E6%80%8E%E6%A0%B7%E9%80%90%E6%AD%A5%E6%94%BE%E9%87%8F%EF%BC%8C%E5%87%BA%E9%97%AE%E9%A2%98%E6%97%B6%E8%83%BD%E6%92%A4%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)给出了止损与回退的条件。本章回答剩下的问题：metrics (指标)、traces (追踪) 和 logs (日志) 各能把人带到哪里；两个同时出现的症状怎样下结论而不把相关当成根因；怎样按证据缓解，并用同一口径确认真的恢复了；遥测怎样既可诊断，又不爆炸、不泄露。文中的时间、计数和日志都是教学构造。

下图是全章的总览，把从信号到复验压成四个交接，每步的输出是下一步的输入。它与后文“按证据缓解与复验的六步”的对应关系是：图中第 1、2 步的用户结果和分母沿用 SLI 章的定义，落在六步的第 1、2 步（确认影响与信号质量、核对任务停在哪个持久边界）；图中第 3 步是“指标、追踪和日志”与案例两节的内容，也是六步的第 3 步；图中第 4 步对应六步的第 4、5 步；六步的第 6 步（事后改进）不在图中。

![从用户结果到事故复验的四步：定义用户结果，固定分母与时间边界，聚合定位再核对事件，缓解后复验用户路径。](../../engineering-foundations/practice/resources/observability-diagnosis-flow.svg)

### 指标、追踪和日志各回答什么

三种信号分工不同：指标把人带到受影响的窗口和范围，追踪指出出问题的阶段，日志解释某一次操作的具体结果。

#### 指标：影响何时出现、范围多大

指标把大量事件聚合成按时间窗的计数、比率、分布或当前积压，回答影响何时出现、范围多大、是否集中在某个摘要或依赖上。先用取值有限的标签定位到 `d-new`：路由模板、响应类别、区域、服务角色、依赖名和受控的版本标签。然后看：

- 计数器的分母、延迟分布与分位数；
- 连接池等待、数据库饱和度；
- 最老的 outbox 意图、`queued` job 和 broker 消息各等了多久；
- 实际占用的 worker 执行槽、重试和容量失败；支持的 broker 还要看未确认消息数和转入 dead-letter queue (死信队列) 的消息。

两个常见误读：broker 队列很短，不证明数据库里的 outbox 或 `queued` job 没有积压，每个交接点要分段观测（见[队列确认章](#44.%20%E5%8F%91%E5%B8%83%E7%A1%AE%E8%AE%A4%E3%80%81%E6%B6%88%E8%B4%B9%E8%80%85%E7%A1%AE%E8%AE%A4%E5%92%8C%E4%B8%9A%E5%8A%A1%E5%AE%8C%E6%88%90%E5%90%84%E8%AF%81%E6%98%8E%E4%BB%80%E4%B9%88%EF%BC%9F)）；租约到期只让恢复器有资格竞争接管，既不表示接管已提交，也不表示旧 attempt 已停止，所以租约到期、接管提交、已被栅栏挡住却仍占资源的 attempt 要分别观察（原理见[条件领取与栅栏章](#43.%20%E6%80%8E%E6%A0%B7%E4%BF%9D%E8%AF%81%E4%B8%80%E4%B8%AA%E4%BB%BB%E5%8A%A1%E5%90%8C%E4%B8%80%E6%97%B6%E5%88%BB%E5%8F%AA%E7%94%B1%E4%B8%80%E4%B8%AA%20worker%20%E6%8E%A8%E8%BF%9B%EF%BC%9F)）。

#### 追踪：哪个阶段慢或失败

trace 把一次操作拆成有父子关系的 span (操作区间)。同步调用通过 context propagation (上下文传播) 传递关联信息，把入口、授权、数据库和对象存储的 span 串成一条链。父子 span 或并发 span 的时长会重叠，不能把各 span 的时长直接相加当总延迟。

异步导出的链路在受理请求结束之后才继续，需要专门接起来：

- relay 用已提交 outbox 中保存的 trace context 创建发布 span，并把上下文附在 broker 消息上；
- worker 每次成功领取后创建一个独立的 attempt span，再用 span link (跨度链接) 指向消息里的创建上下文，接回因果链；
- 受控的 `jobId` 用来跨多次 attempt 查询持久状态。

不要让 HTTP span 一直挂到整个任务完成；每次 attempt 的执行阶段应能单独定位。trace 有采样时，要检查采样率、时间戳、导出是否正常和覆盖范围；找不到样本，不能证明请求或故障不存在。

> [!info] 实例：OpenTelemetry 的消息语义约定（semconv 1.45.0，核对于 2026-11-12）
> 当前的消息 span 语义约定默认用 link 关联生产与消费；只有处理单条消息等特定情形，才考虑把消息的创建上下文作为 parent (父 span)。

#### 日志：这一次操作的具体结果

在结构化日志里放入 trace ID、span ID，以及受控的 `jobId`、`attempt`、状态转换和有限的错误码，就能从一个有代表性的 span 找到实际错误，再对照发布摘要和事件时间。

### 案例：12:10–12:20 的两个症状

下图先把本例的所有时刻放在一条时间轴上：前三行是隔离预检和读取的症状、止损与复验，后两行是两个导出任务。本节讲 12:20 之前的症状，12:20 之后的复验在后面第 5 步：

![12:00–12:35 时间线：隔离预检全程覆盖交给 d-old 的读取；d-new 12:10 起变慢，12:15–12:20 六个评价点满足持续止损，12:20 切回 d-old，12:30 复验窗口 1,000/1,000；job-demo-731 12:00 受理、12:02 到期、12:16 仍 queued、12:26 才成功仍计坏；job-demo-732 12:31 受理、12:32 成功。](../../engineering-foundations/practice/resources/incident-timeline.svg)

#### 读取变慢：先确认缺口真实，再下钻

在 12:10–12:20 这个窗口里，同一路由、同一区域的 `d-new` 收到 100 次合格读请求，98 次在 400 ms 内给出了与授权关系一致的结果；稳定版 `d-old` 是 900/900（它带着跨账户缺陷，这些读取之所以都好，是因为受影响入口已按金丝雀章隔离）。按 SLI 章的规则，只看 `d-new` 自身（[为什么不能合并](#%E9%87%91%E4%B8%9D%E9%9B%80%E4%B8%8D%E8%83%BD%E5%92%8C%E7%A8%B3%E5%AE%9A%E7%89%88%E5%90%88%E5%9C%A8%E4%B8%80%E8%B5%B7%E8%AF%84%E4%BC%B0)），它低于 99% 的门槛。门禁每分钟评价一次，图中六个评价点首末相隔整 5 分钟，每个点上 `d-new` 的滚动 10 分钟窗口都满足样本数和比例条件，所以满足持续止损条件。事先运行的冒烟核验也确认，钉到 `d-new` 的 `user-17` 得到 `200` 和已知标记，`user-29` 经 acct-29 读 42 得到与报表 43 相同的 `404`，所以这个缺口不是把正当的拒绝误算成了失败。

接着从指标下钻到 trace。同一窗口里一条慢读请求总耗时 900 ms：

- 其中授权与报表读取阶段（去掉重叠后的墙钟时间）720 ms；
- 这 720 ms 里，从数据库连接池 checkout (签出连接) 等了 600 ms，SQL 执行约 120 ms；
- 其余约 180 ms 在其他阶段。

这些阶段层层包含，不能把 900、720、600 相加。这条 trace 把慢请求定位到“等数据库连接”，却没有证明是 `d-new` 引起的，也推不出 worker 与 API 共用同一个连接池。

#### 导出不来：从权威状态查起

导出症状要从数据库里的权威状态查起，而不是从队列深度猜。12:16 按 `job-demo-731` 查询 job 行、attempt 和 outbox：

- 受理提交确认在 12:00，所以完成 SLI 的期限是 12:02；
- 到 12:16 状态仍是 `queued`、`attempt=0`；
- outbox 已发布，broker 也有唤醒记录，却没有成功领取，也没有结果对象引用、`succeeded` 或 `report.ready`。

期限早已过去仍未成功，用户的导出确实受到了影响。worker 的结构化日志显示，获取数据库连接失败发生在领取之前，所以这项工作根本还没开始执行；只看“最老待处理任务等了多久”，看不出停在这个阶段。

#### 相关不等于根因

两个症状出现在同一个故障窗口，都指向数据库连接。但 API 和 worker 的连接池是分开配置的，同时出现还不足以证明二者同因。在补齐数据库饱和度、各连接池的使用率和查询时长对照之前，“共享数据库压力”只是一个待验证的假设，不能写成根因。

### 按证据缓解与复验的六步

定位到阶段之后，处置沿着“用户结果 → SLI → 依赖阶段 → 可逆动作 → 用同一用户路径复验”推进，每一步都把操作和判断依据分开记录：

1. **确认用户影响与信号质量。** 确定事件起止时间、受影响的接口和区域、API 与 worker 各自运行的摘要，以及读取 SLI 的分子和分母。检查遥测是否新鲜、采样和导出是否正常；无响应的请求仍是坏事件，不能因为没有 span 就移出分母。

2. **核对任务停在哪个持久边界。** 对超时的导出 `POST`，按 `(account_id, principal_id, idempotency_key)` 查询 `export-demo-415` 的幂等记录，结果不明的先标为待定；受理事务一旦提交就算一个 accepted job，即使客户端没收到 `202`，而明确返回 `429`/`503` 的请求按约定没有创建 job。再分别看 outbox 发布、broker 投递与确认、worker 领取、attempt、数据库终态和结果读取；ACK 只说明当前这条消息交接完成。已到期仍为 `queued`/`running` 的任务在完成 SLI 中算坏，未到期的暂不进分母，但保留其等待时长作为证据。

3. **用多条证据定位。** 按摘要和路由对照金丝雀与基线的同期窗口，挑有代表性的慢或失败 trace，再用 span ID 和 job/attempt 等受控键查日志。交叉检查 API 与 worker 的连接池等待、数据库连接数与查询耗时、最老的 outbox/job/消息、对象存储错误码。单条 trace、进程健康探针或 broker 队列深度都不能直接当根因。

4. **先降低影响，再选安全路径。**
   - **止损。** `d-new` 已满足持续止损条件，停止为它加流。
   - **回退目标。** 回退目标要过金丝雀章的[三个条件](#%E5%9B%9E%E9%80%80%E5%89%8D%E5%85%88%E7%A1%AE%E8%AE%A4%E7%9B%AE%E6%A0%87%E5%BD%93%E5%89%8D%E5%AE%89%E5%85%A8%E3%80%81%E6%95%B0%E6%8D%AE%E5%85%BC%E5%AE%B9%E3%80%81%E6%9C%89%E5%AE%B9%E9%87%8F)，而 `d-old` 过不了“当前安全”：它正是带着跨账户缺陷的旧版本，简单切回去就是让全部读取重新走有缺陷的代码。所以先隔离受影响的入口，再回退到已证明安全且兼容的版本，或者前向修复。本例的隔离（交给 `d-old` 的读取路由上的临时归属预检）在开放金丝雀前就已生效；值班人先复核它仍覆盖全部交给 `d-old` 的流量，才把 `d-new` 的 10% 切回 `d-old`。这只是争取时间的临时状态：缺陷仍在 `d-old` 里，修复版要在查清读取变慢的原因后前向发布。
   - **依赖。** 连接池等待还不能证明 API 和 worker 出自同一故障源，所以先比较两者的连接预算与数据库活动，再按证据限流或降载，不要只是调大每个进程的连接池（连接预算怎样算，见[连接池章](#28.%20ORM%20%E4%BC%9A%E8%AF%9D%E6%80%8E%E6%A0%B7%E5%80%9F%E7%94%A8%E8%BF%9E%E6%8E%A5%EF%BC%8C%E8%BF%9E%E6%8E%A5%E6%B1%A0%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BC%9A%E8%80%97%E5%B0%BD%EF%BC%9F)）。
   - **新导出。** 对尚未受理的新导出请求，可以按准入约定在 `202` 之前返回 `429`/`503`；已经受理的任务要保持可查询、可恢复，不能把拒绝新请求伪装成 job 失败。

5. **用同一用户结果复验，再考虑放量。**
   - **读取。** 切回 `d-old` 后，等切换后第一个完整的滚动 10 分钟窗口结束，用同一个读取 SLI 口径复验：时间线图中这个窗口的合格读请求全部为好事件，且每个请求都能归到 `d-old`。样本不足或归属缺失就维持当前流量，不能拿切换前的数据或跨摘要的总量代替。业务核验另从实际部署的入口做：`user-17` 读报表 42 得到 `200` 和已知标记；`user-29` 经 acct-29 读 42 得到与报表 43 相同的 `404`。这个 `404` 来自隔离预检而不是 `d-old` 的代码，它证明的是隔离仍然有效，不是缺陷已修好。
   - **旧任务。** `job-demo-731` 观察到成功提交确认后，按当前授权下载并核对了文件。它在原期限之后才成功，在完成 SLI 里仍是坏事件；而且 API 回退并不控制 worker，这次迟到的完成不能直接归功于回退，只说明这个旧任务后来可用了。
   - **新请求的完整路径。** 旧任务恢复代替不了新请求的复验。用新的幂等键 `export-demo-416` 发起导出，创建 `job-demo-732`：确认受理提交后返回 `202`；观察到成功提交确认时，结果引用与 `report.ready` outbox 已原子提交；然后从同一入口按授权下载并核对文件。时间线图中 60 秒的确认间隔满足 2 分钟的完成 SLI（它不证明实际 COMMIT 间隔，见 SLI 章）。
   - **不能当作恢复证据的。** 告警没有持续触发满 5 分钟，可能只是尚未触发或刚刚解除；队列 ACK 不代表用户拿到了文件；通知是否送达要按独立的通知 SLI 复验。30 天的长期错误预算继续单独跟踪。

6. **记录可执行的事后改进。** 记下用户受影响的时间窗、各 SLI 的分子与分母、摘要和阶段证据、采取的缓解措施（含切回 `d-old` 依赖的那道隔离何时生效、何时撤除）、前向修复的计划、相关测试，以及现有门禁为什么没有更早发现问题。只写“服务已恢复”，没有用户路径和时间窗，就无法判断是否真正止损。

### 遥测既要可诊断，又不能爆炸或泄露

上面的定位依赖标签和关联 ID，它们也可能让时序数量爆炸或泄露数据。

**指标标签取自有限集合**：规范化的路由模板 `/v1/accounts/{account_id}/reports/{report_id}`、响应类别、区域、`service_role=api|worker`、依赖名和受控的 release channel (发布通道)。每种标签组合都会成为一条独立的 time series (时间序列)，所以 cardinality (基数，即不同取值的数量) 必须有上限。不要把 `request_id`、trace ID、job ID、用户或账户 ID、原始 URL、报表标题、提示词、结果内容或任意错误文本作为指标维度。镜像摘要适合短期的发布对比，但要限制保留时长和组合数量，避免每次构建都让时序无限增长。

**追踪和日志只记必要字段。** 在有访问控制和保留期限的前提下，它们可以包含用于关联的操作 ID，但不得记录 access token、cookie、授权请求头、报表正文或原始用户内容。优先用有界的事件分类，例如 `authorization=allow|deny`、`db_error=timeout|unavailable`、`job_state=queued|running|succeeded|failed|cancelled`、`error_code=capacity_exhausted|attempts_exhausted`。跨账户授权错误要靠独立的安全审计和回归测试排查，不能靠在指标里暴露账户 ID。

### 这次事故留下了什么

本章从一个变坏的用户结果出发，走完了定位、止损和复验：三种信号各自把范围缩小一步，两个同期症状只有补齐对照证据才能归因，缓解按可逆动作推进，恢复用切换后完整窗口里同一口径的 SLI 和一条新的端到端导出证明。主线五到此结束。事后改进通常会回到前面几章：把漏掉的条件写成[能区分对错的测试](#53.%20%E4%B8%80%E6%AC%A1%E6%94%B9%E5%8A%A8%E8%AF%A5%E5%9C%A8%E5%93%AA%E4%B8%80%E5%B1%82%E6%B5%8B%E8%AF%95%EF%BC%8C%E6%80%8E%E6%A0%B7%E8%AF%81%E6%98%8E%E6%B5%8B%E8%AF%95%E8%83%BD%E5%8C%BA%E5%88%86%E5%AF%B9%E9%94%99%EF%BC%9F)，把没起作用的信号加进[放量门禁](#60.%20%E6%96%B0%E7%89%88%E6%9C%AC%E6%80%8E%E6%A0%B7%E9%80%90%E6%AD%A5%E6%94%BE%E9%87%8F%EF%BC%8C%E5%87%BA%E9%97%AE%E9%A2%98%E6%97%B6%E8%83%BD%E6%92%A4%E5%9B%9E%E4%BB%80%E4%B9%88%EF%BC%9F)。

> [!info]- 来源
> - **指标、追踪、日志的模型与上下文传播**（“指标、追踪和日志各回答什么”）：OpenTelemetry，[Signals](https://opentelemetry.io/docs/concepts/signals/)、[Traces](https://opentelemetry.io/docs/concepts/signals/traces/)、[Metrics](https://opentelemetry.io/docs/concepts/signals/metrics/)、[Logs](https://opentelemetry.io/docs/concepts/signals/logs/)、[Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)，核对于 2026-11-12。
> - **异步消息的 span link**（追踪一节与 OpenTelemetry 实例）：OpenTelemetry，[Messaging spans: consumer spans](https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/#consumer-spans)，semconv 1.45.0，核对于 2026-11-12；默认以 link 关联生产与消费，单条消息等情形才用创建上下文作 parent。采样与敏感字段约束是本例的应用边界。
> - **标签与基数**（“遥测既要可诊断，又不能爆炸或泄露”）：Prometheus，[Metric and label naming](https://prometheus.io/docs/practices/naming/)，核对于 2026-11-12；标签组合形成时序、高基数标签有风险。这是实践建议，不是所有遥测系统的强制规范。
> - **按用户结果定义 SLI、长短窗口告警**（案例中的门禁与复验口径）：Google SRE Workbook，[Implementing SLOs](https://sre.google/workbook/implementing-slos/)、[Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)，核对于 2026-11-12；本章的窗口与阈值沿用 SLI 章的合成教学值。
> - **job 受理、成功提交的原子性与 attempt 归属**（“导出不来：从权威状态查起”与六步中的第 2 步）：本领域主线四的持久受理、条件领取与队列确认三章；数据库是任务状态的权威。
