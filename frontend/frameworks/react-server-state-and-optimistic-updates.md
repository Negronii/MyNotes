# How should a React UI keep server data and optimistic updates correct? / React界面如何维护服务端数据与乐观更新的正确性？

**Core answer / 核心回答：** Keep transient choices such as the selected row, open dialog, or draft input in local React state. Treat records owned by a server as server state: identify each query by all inputs that affect it, define when cached data is fresh, and invalidate or update affected entries after a mutation. A query cache is a client read model, not the source of truth. / 将选中行、打开的对话框和输入草稿等临时选择保存在 React 本地状态中。服务器拥有的记录属于服务端状态：查询键要包含所有影响结果的输入，缓存需要明确新鲜期，变更后要更新或失效相关缓存。查询缓存是客户端读模型，不是数据的权威来源。

## Identify ownership, freshness, and mutation effects / 区分数据归属、新鲜度和变更影响

For example, selecting a row is local UI state, while the list and selected record come from the server. Separate query keys encode their identities; include filters, page, or account identifiers too when they change the result. In TanStack Query v5, `staleTime` defines how long a result is considered fresh. Once stale, it can refetch on configured events; targeted invalidation marks matching entries stale and refetches active observers. The value is a freshness policy, not a promise that the server data cannot change.

~~~tsx
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

type Task = { id: string; title: string; done: boolean };
type TaskPatch = Pick<Task, "id"> & Partial<Pick<Task, "title" | "done">>;

// These request functions parse and validate their responses at the API boundary.
declare function listTasks(): Promise<Task[]>;
declare function getTask(id: string, signal: AbortSignal): Promise<Task>;
declare function saveTask(patch: TaskPatch): Promise<Task>;

const taskKeys = {
  list: ["tasks", "list"] as const,
  detail: (id: string) => ["tasks", "detail", id] as const
};

function useTaskList() {
  return useQuery({
    queryKey: taskKeys.list,
    queryFn: listTasks,
    staleTime: 30_000
  });
}

function useTaskDetail(id: string) {
  return useQuery({
    queryKey: taskKeys.detail(id),
    queryFn: ({ signal }) => getTask(id, signal)
  });
}

function TaskWorkspace() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const list = useTaskList();

  if (list.isPending) return <p>Loading tasks…</p>;
  if (list.isError) return <p role="alert">Could not load tasks.</p>;

  return (
    <div>
      <ul>
        {list.data.map(task => (
          <li key={task.id}>
            <button type="button" onClick={() => setSelectedId(task.id)}>
              {task.title}
            </button>
          </li>
        ))}
      </ul>
      {selectedId !== null && <TaskDetail id={selectedId} />}
    </div>
  );
}

function TaskDetail({ id }: { id: string }) {
  const detail = useTaskDetail(id);
  if (detail.isPending) return <p>Loading selected task…</p>;
  if (detail.isError) return <p role="alert">Could not load this task.</p>;
  return <p>{detail.data.title}</p>;
}

function useSaveTask() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: saveTask,
    onMutate: async patch => {
      const detailKey = taskKeys.detail(patch.id);
      await Promise.all([
        client.cancelQueries({ queryKey: taskKeys.list }),
        client.cancelQueries({ queryKey: detailKey })
      ]);

      const previousList = client.getQueryData<Task[]>(taskKeys.list);
      const previousDetail = client.getQueryData<Task>(detailKey);
      client.setQueryData<Task[]>(taskKeys.list, old =>
        old?.map(task => task.id === patch.id ? { ...task, ...patch } : task)
      );
      if (previousDetail !== undefined) {
        client.setQueryData<Task>(detailKey, { ...previousDetail, ...patch });
      }
      return { previousList, previousDetail };
    },
    onError: (_error, patch, previous) => {
      if (previous?.previousList !== undefined) {
        client.setQueryData(taskKeys.list, previous.previousList);
      }
      if (previous?.previousDetail !== undefined) {
        client.setQueryData(taskKeys.detail(patch.id), previous.previousDetail);
      }
    },
    onSuccess: saved => {
      client.setQueryData(taskKeys.detail(saved.id), saved);
      client.setQueryData<Task[]>(taskKeys.list, old =>
        old?.map(task => task.id === saved.id ? saved : task)
      );
    },
    onSettled: (_data, _error, patch) => Promise.all([
      client.invalidateQueries({ queryKey: taskKeys.list }),
      client.invalidateQueries({ queryKey: taskKeys.detail(patch.id) })
    ])
  });
}
~~~

The mutation cancels in-flight reads before writing optimistically, saves snapshots for rollback, replaces both cached views with the server response on success, then invalidates them to reconcile other changes. A pending save can disable its button; on error, the snapshot restores the visible list/detail and the UI can show a retry message. Because rollback restores the whole list snapshot, this example requires at most one mutation in flight across the shared list—not merely one save per task. Otherwise A can fail after B succeeds and restore B's old row too. Broader concurrency needs operation-scoped or version-aware reconciliation instead of blindly restoring that snapshot. If the user switches from task A to B while A is loading, the detail key changes from `detail/A` to `detail/B`; A may finish into its own cache entry, but cannot become B's displayed record. Passing the query's `AbortSignal` to `fetch` can also stop obsolete network work when the service consumes it. A manually managed Effect needs its own stale-result guard or cleanup; [the `useWindowSize` Effect example](./react-component-composition.md#What%20is%20a%20custom%20Hook%3F%20/%20%E4%BB%80%E4%B9%88%E6%98%AF%E8%87%AA%E5%AE%9A%E4%B9%89Hook%EF%BC%9F) shows cleanup, and an Effect fetch by itself does not activate Suspense. See [Advanced TypeScript / TypeScript进阶](../typescript/advanced-typescript.md) for validating API JSON before treating it as a `Task`.

**Related task / 相关任务：** The [responsive React search question / React搜索响应问题](./advanced-react.md) shows how the result view stays responsive while its query key follows the user's inputs. This page explains the cache identity, freshness, optimistic mutation, rollback, and concurrency rules used by that UI. / [React搜索响应问题](./advanced-react.md)说明结果查询如何跟随用户输入、同时保持界面响应；本文说明该界面所需的缓存身份、新鲜度、乐观变更、回滚与并发规则。

**See also:** [React Basics / React基础](./react-basics.md) for state snapshots and the render/commit path.

**Sources checked 2026-10-15:** [React: Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects), [TanStack Query React v5: Queries](https://tanstack.com/query/latest/docs/framework/react/guides/queries), [Query Keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys), [Important Defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults), [Query Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation), [Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates), [Suspense](https://tanstack.com/query/latest/docs/framework/react/guides/suspense), [Cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation).
