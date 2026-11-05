# How do ahooks list Hooks represent paged and incremental data? / ahooks 列表 Hook 如何表示分页与增量加载数据？

usePagination models a numbered page: its service receives current and pageSize and resolves to list plus total. useInfiniteScroll models an accumulated list: for downward loading the service receives current data, returns the next page, and the Hook merges its list. Both need an explicit service contract and visible loading, error, and continuation states. / usePagination 表示编号分页：服务接收 current 和 pageSize，返回 list 与 total。useInfiniteScroll 表示累积列表：向下加载时服务接收当前数据并返回下一页，由 Hook 合并 list。两者都需要明确服务契约，并呈现加载、错误和继续状态。

The pagination result exposes current, pageSize, total, totalPage, and change methods such as changeCurrent and changePageSize. Infinite-scroll state includes data, loading, loadingMore, error, noMore, loadMore, reload, mutate, and cancel. Its target selects a scroll container, threshold controls how near the edge to load, and isNoMore defines the stopping condition.

~~~jsx
const { data, loading, pagination } = usePagination(
  ({ current, pageSize }) => fetchUsers({ current, pageSize }),
  { defaultPageSize: 20 }
);

pagination.changeCurrent(2);
~~~

A complete infinite-scroll example makes the accumulated-data contract explicit:

~~~jsx
import { useInfiniteScroll } from 'ahooks';
import { useRef } from 'react';

const loadItems = async currentData => {
  const page = currentData?.nextPage ?? 1;
  const response = await fetch('/api/items?page=' + page);
  if (!response.ok) throw new Error('Request failed');
  const next = await response.json(); // { list: Item[], nextPage: number | null }
  return { list: next.list, nextPage: next.nextPage };
};

function InfiniteList() {
  const containerRef = useRef(null);
  const { data, loading, loadingMore, noMore, loadMore, error } =
    useInfiniteScroll(loadItems, {
      isNoMore: currentData => currentData != null && currentData.nextPage == null,
      target: containerRef,
      threshold: 100,
    });

  return (
    <div ref={containerRef} style={{ height: 400, overflow: 'auto' }}>
      {data?.list.map(item => <div key={item.id}>{item.name}</div>)}
      {loading && <p>Loading…</p>}
      {loadingMore && <p>Loading more…</p>}
      {error && <p>Could not load more items.</p>}
      <button disabled={loadingMore || noMore} onClick={loadMore}>Load more</button>
    </div>
  );
}
~~~

Render stable item IDs as keys and guard loadMore while a page is in flight or noMore is true. A scroll threshold does not define the product's pagination or authorization rules.

**Source checked 2026-10-15:** [ahooks usePagination](https://ahooks.js.org/hooks/use-pagination) and [useInfiniteScroll](https://ahooks.js.org/hooks/use-infinite-scroll). See [ahooks](../../../frontend/libraries/ahooks.md) and [Advanced React](../../../frontend/frameworks/advanced-react.md) for current Hook and Effect guidance.
