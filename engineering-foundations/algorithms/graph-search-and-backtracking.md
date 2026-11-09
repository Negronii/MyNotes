# 搜索状态图时，何时永久标记节点，何时必须回退？

合成站点 S 要把一件包裹送到 Z。路网是一张有向图：S 可到 A、B；A 与 B 都可到汇点 T；T 可回到 S，也可到 Z。回边让图有环，共享汇点让两条路线合流。我们先用它找一条最少跳数路线，再枚举简单路线、检查依赖环，最后给路段加入非负代价。

本章的邻接表契约是：顶点 ID 都是字符串；Map 为每个顶点都建一项，包括没有出边的顶点（例如 Z→[]）；所有邻居也都作为顶点键出现。BFS 用 null 表示起点没有父节点，因此不接受 null 顶点 ID。

~~~mermaid
flowchart LR
    S --> A
    S --> B
    A --> T
    B --> T
    T --> S
    T --> Z
~~~

这些操作都沿边扩展候选状态，但保留的状态不同：breadth-first search（BFS，广度优先搜索）只要每个顶点的一条最短边数路径，可以全局去重；枚举简单路径时，同一顶点可能属于不同合法路径，必须只在当前递归路径内标记并在返回时撤销；拓扑排序要求有向边代表依赖且图无环；Dijkstra 选择当前代价最小的未定顶点，要求所有边权非负。

## 无权图最短路：顶点第一次入队时记录父节点

breadth-first search（广度优先搜索，BFS）用先进先出队列按层扩展：先看距 S 一条边的顶点，再看两条边的顶点。队列中的顶点按发现距离非递减排列，所以第一次发现一个顶点时，已找到它的最少边数路径。用 parent 同时记录“已经发现”与首次父节点，之后的回边或另一条同层路线不再入队。

| 处理的顶点 | 刚发现的邻居 | 队列（从前到后） | parent 新增 |
|---|---|---|---|
| S | A、B | A、B | A←S，B←S |
| A | T | B、T | T←A |
| B | T 已发现 | T | 无 |
| T | S 已发现、Z | Z | Z←T |
| Z | 已到目标 | 空 | — |

按首次父节点从 Z 回溯得到 S→A→T→Z，共 3 条边。若邻接表把 B 放在 A 前，BFS 可能返回 S→B→T→Z；两条都是最少边数路径。若目标不可达，返回 null；起点等于目标时返回仅含起点的路径。

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
  const parent = new Map([[start, null]]); // 同时是全局 visited 集合
  const queue = [start];

  for (let head = 0; head < queue.length; head++) {
    const vertex = queue[head];
    if (vertex === target) break;
    for (const next of graph.get(vertex) ?? []) {
      if (parent.has(next)) continue;
      parent.set(next, vertex); // 入队时标记，避免重复排队
      queue.push(next);
    }
  }

  if (!parent.has(target)) return null;
  const path = [];
  for (let vertex = target; vertex !== null; vertex = parent.get(vertex)) {
    path.push(vertex);
  }
  return path.reverse();
}

console.log(shortestUnweightedPath(routes, 'S', 'Z')); // ['S', 'A', 'T', 'Z']
console.log(shortestUnweightedPath(routes, 'S', 'missing')); // null
~~~

邻接表下 BFS 为 O(V + E) 时间、O(V) 额外空间，V 为顶点数、E 为边数。这里用数组递增 head 取代反复 shift，队列头前进时不搬移剩余元素。全局 visited 合适的理由是此处只保留每个顶点的一条最短距离与父节点；它并不表示顶点只能出现在一条合法简单路径中。

## 枚举简单路径：visited 只属于当前路径，并在回退时撤销

若要列出所有不重复经过同一站点的路线，S→A→T→Z 与 S→B→T→Z 都是有效候选。BFS 的 parent 只保留 T 的第一个父节点 A；若把全局 visited 直接拿来做路径枚举，T 经 A 加入 visited 后，经 B 到达 T 的分支会被误删。

backtracking（回溯）沿候选边选下一站，递归扩展；回到上一层时撤销刚才加入的站点和路径项。onPath 只表示“这个顶点正在当前候选路径上”。它会拒绝 T→S，因为 S 已在这条路径里；回到起点的另一条分支时，T 的标记已撤销，因此 T 可以再次进入另一条路线。

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
    for (const next of graph.get(vertex) ?? []) {
      if (onPath.has(next)) continue; // 本路径内重复才构成环
      onPath.add(next);
      path.push(next);
      visit(next);
      path.pop();
      onPath.delete(next); // 回退后允许别的分支复用 next
    }
  }

  visit(start);
  return results;
}

const routeGraphForPaths = new Map([
  ['S', ['A', 'B']],
  ['A', ['T']],
  ['B', ['T']],
  ['T', ['S', 'Z']],
  ['Z', []]
]);
console.log(allSimplePaths(routeGraphForPaths, 'S', 'Z'));
// [['S', 'A', 'T', 'Z'], ['S', 'B', 'T', 'Z']]
~~~

如果本次问题只需一条路线，不应枚举所有路线。固定不同起终点的完全有向图，仅遍历其余所有顶点的简单路径就有 (V−2)! 条，数量至少可达阶乘级；本例代码没有候选数上限。令 C 为实际检查的候选边数、L 为复制到结果中的路径总长度，运行时间按 O(C + L) 计；即使结果少，搜索也可能访问许多最终无法到达目标的前缀。递归栈、path 与 onPath 的辅助空间为 O(V)，返回结果另占与所有输出路径总长度相称的空间。深图也可能超过 JavaScript 调用栈深度，此时应把递归状态改成显式栈，但仍须在回退时撤销 onPath。

## 依赖排序：每条有向边都必须满足先后顺序

topological sort（拓扑排序）不是在一般图上重新安排搜索次序。若每条边 u→v 表示 u 必须先于 v，拓扑序才是可执行顺序。把 T→S 解释为一项依赖时，S→A→T→S 已成环，要求 S 先于 T 又要求 T 先于 S，因此不存在合法顺序。若 T→S 只是回程路线、不是依赖，就从依赖图删去这条边；其余边形成 DAG（directed acyclic graph，有向无环图），可排成 S、A、B、T、Z。

下面的 Kahn 算法维护每个顶点尚未满足的入边数。入度为 0 表示当前可执行；取出它后，逐条解除后继的一项依赖。若取出的顶点数少于图中顶点数，剩余边属于环内或被环阻塞的依赖，返回 null。

~~~javascript
function topologicalOrder(graph) {
  const vertices = new Set(graph.keys());
  for (const neighbors of graph.values()) {
    for (const next of neighbors) vertices.add(next);
  }

  const indegree = new Map(Array.from(vertices, vertex => [vertex, 0]));
  for (const neighbors of graph.values()) {
    for (const next of neighbors) indegree.set(next, indegree.get(next) + 1);
  }

  const ready = Array.from(vertices).filter(vertex => indegree.get(vertex) === 0);
  const order = [];
  for (let head = 0; head < ready.length; head++) {
    const vertex = ready[head];
    order.push(vertex);
    for (const next of graph.get(vertex) ?? []) {
      const remaining = indegree.get(next) - 1;
      indegree.set(next, remaining);
      if (remaining === 0) ready.push(next);
    }
  }
  return order.length === vertices.size ? order : null;
}

const dependencies = new Map([
  ['S', ['A', 'B']],
  ['A', ['T']],
  ['B', ['T']],
  ['T', ['Z']],
  ['Z', []]
]);
const cyclicDependencies = new Map([
  ['S', ['A', 'B']],
  ['A', ['T']],
  ['B', ['T']],
  ['T', ['S', 'Z']],
  ['Z', []]
]);
console.log(topologicalOrder(dependencies)); // ['S', 'A', 'B', 'T', 'Z']
console.log(topologicalOrder(cyclicDependencies)); // null：T → S 使依赖成环
~~~

每个顶点和边各处理常数次，邻接表下时间 O(V + E)、额外空间 O(V)。入度为 0 的顶点可能不止一个，因此不同合法拓扑序都可能成立。初始 ready 队列按顶点首次出现顺序排列；后续变为 ready 的顶点则按当前出队顶点的邻接表扫描顺序入队，并由 FIFO 队列处理，不保证沿用它们在原 Map 中首次出现的顺序。若业务要求特定顺序，应明确再加优先级规则，而不能把任意拓扑序当成唯一答案。

## 非负权最短路：松弛距离，并跳过过期堆项

现在为路线加上整数耗时：S→A 为 1，S→B 为 4，A→T 为 6，B→T 为 1，T→S 为 2，T→Z 为 1。BFS 仍找到 3 条边的 S→A→T→Z，但总代价是 8；代价较小的 S→B→T→Z 为 6。边数最少和代价最低是两个问题。

Dijkstra 算法用最小堆优先处理当前距离最小且尚未定型的顶点。relaxation（松弛）一条边 v→w 时，若 dist[v]+weight 小于已知 dist[w]，就更新距离与前驱并把新距离推入堆。此实现不原地修改旧堆项；某顶点改善时会留下旧项，弹出时若其距离已不等于当前 dist，就跳过。堆还可含同一个顶点的多条距离记录，settled（已定型）集合保证顶点只处理一次。

| 弹出的堆项 | 更新 | 堆中待处理项（可能含过期项） | 说明 |
|---|---|---|---|
| S:0 | A=1，B=4 | A:1、B:4 | 从源点展开 |
| A:1 | T=7 | B:4、T:7 | 暂时走 A |
| B:4 | T 从 7 改为 5 | T:5、T:7 | 新项入堆，T:7 成为过期项 |
| T:5 | Z=6；回到 S 的候选 7 不改善 S=0 | Z:6、T:7 | 走 B 得到 Z 的最短代价 6 |
| Z:6 | 无 | T:7 | 目标已定型 |
| T:7 | 无 | 空 | 因 7 不等于 dist[T]=5，跳过 |

边权必须非负：定型当前最小距离顶点的证明依赖于之后经过边不会降低代价。若绕过下方代码的输入校验，另加 B→A、权重 −5，则 A 在距离 1 时已定型；处理 B:4 时，经过 B 到 A 的真实代价为 −1，定型规则会忽略它并错误保留 1。本文实现会在运行核心循环前对负权输入抛出 RangeError；该反例用来说明为什么它拒绝这种输入。负权图应改用能处理负边的算法（例如无负环前提下的 Bellman–Ford），不能因为某个负权样例恰好算对就使用 Dijkstra。

下面的最小堆仅按 distance 排序；它只服务此完整示例，与[优先队列的上浮和下沉](heaps-and-priority-queues.md)共享数组堆机制。代码把权重和距离限制为安全整数，并拒绝负权或超出安全范围的路径和。

> [!example]- 可运行：Dijkstra 最小堆实现
> ~~~javascript
> class MinHeap {
>   constructor() { this.items = []; }
>   get size() { return this.items.length; }
>
>   push(item) {
>     this.items.push(item);
>     let i = this.items.length - 1;
>     while (i > 0) {
>       const parent = Math.floor((i - 1) / 2);
>       if (this.items[parent].distance <= this.items[i].distance) break;
>       [this.items[i], this.items[parent]] = [this.items[parent], this.items[i]];
>       i = parent;
>     }
>   }
>
>   pop() {
>     if (this.items.length === 0) return null;
>     const root = this.items[0];
>     const last = this.items.pop();
>     if (this.items.length > 0) {
>       this.items[0] = last;
>       let i = 0;
>       while (true) {
>         const left = 2 * i + 1;
>         const right = left + 1;
>         let smallest = i;
>         if (left < this.items.length &&
>             this.items[left].distance < this.items[smallest].distance) smallest = left;
>         if (right < this.items.length &&
>             this.items[right].distance < this.items[smallest].distance) smallest = right;
>         if (smallest === i) break;
>         [this.items[i], this.items[smallest]] = [this.items[smallest], this.items[i]];
>         i = smallest;
>       }
>     }
>     return root;
>   }
> }
>
> function dijkstra(graph, source) {
>   for (const [from, edges] of graph) {
>     for (const edge of edges) {
>       if (!Number.isSafeInteger(edge.weight) || edge.weight < 0) {
>         throw new RangeError('Dijkstra requires non-negative safe-integer weights');
>       }
>       if (!graph.has(edge.to)) throw new RangeError('every destination must be a graph vertex');
>     }
>   }
>   if (!graph.has(source)) return { distances: new Map(), previous: new Map() };
>
>   const distances = new Map(Array.from(graph.keys(), vertex => [vertex, Infinity]));
>   const previous = new Map();
>   const settled = new Set();
>   const heap = new MinHeap();
>   distances.set(source, 0);
>   heap.push({ vertex: source, distance: 0 });
>
>   while (heap.size > 0) {
>     const current = heap.pop();
>     const vertex = current.vertex;
>     if (current.distance !== distances.get(vertex) || settled.has(vertex)) continue;
>     settled.add(vertex);
>
>     for (const edge of graph.get(vertex)) {
>       if (settled.has(edge.to)) continue;
>       const candidate = current.distance + edge.weight;
>       if (!Number.isSafeInteger(candidate)) throw new RangeError('path distance exceeds the safe integer range');
>       if (candidate < distances.get(edge.to)) {
>         distances.set(edge.to, candidate);
>         previous.set(edge.to, vertex);
>         heap.push({ vertex: edge.to, distance: candidate });
>       }
>     }
>   }
>   return { distances, previous };
> }
>
> function weightedPath(result, source, target) {
>   if (!result.distances.has(target) || result.distances.get(target) === Infinity) return null;
>   const path = [];
>   let vertex = target;
>   while (vertex !== source) {
>     path.push(vertex);
>     if (!result.previous.has(vertex)) return null;
>     vertex = result.previous.get(vertex);
>   }
>   path.push(source);
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
> console.log(result.distances.get('Z'));                    // 6
> console.log(weightedPath(result, 'S', 'Z'));                // ['S', 'B', 'T', 'Z']
> console.log(weightedPath(result, 'S', 'unreachable'));      // null
> ~~~

该惰性堆实现每条边至多扫描一次，至多成功松弛并压入一条新项，故时间 O(V + (E + 1) log(E + 1))、空间 O(V + E)。若用带 decrease-key 的索引优先队列，通常可把堆空间降到 O(V)，时间写作 O((V + E) log V)。无论用哪一种实现，距离表、前驱表、堆项和 visited/settled 状态都要对应同一个图与同一组边权。

> [!info]- 来源
> - 邻接表遍历、BFS 按边数找最短路、首次发现时记录父边：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §4.1 “Undirected Graphs”](https://algs4.cs.princeton.edu/41graph/)，作者实现 [BreadthFirstPaths.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/BreadthFirstPaths.java.html)。BFS 原理同样适用于本页的有向邻接表。
> - DAG 才有拓扑序，以及顶点/边线性量级的 DFS 版本：[Algorithms, 4th ed., §4.2 “Directed Graphs”](https://algs4.cs.princeton.edu/42digraph/)，作者的队列版本 [TopologicalX.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/TopologicalX.java.html)。本页采用 Kahn 入度实现，示例输出由 Node.js 运行复算。
> - Dijkstra 的非负权前提、松弛、堆优先处理和索引优先队列复杂度：[Algorithms, 4th ed., §4.4 “Shortest Paths”](https://algs4.cs.princeton.edu/44sp/)，作者实现 [DijkstraSP.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/DijkstraSP.java.html)。本页为便于展示过期项，使用惰性重复入堆，复杂度另按本实现计。
