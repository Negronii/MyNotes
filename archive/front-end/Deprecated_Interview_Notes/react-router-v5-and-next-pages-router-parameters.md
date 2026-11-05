# How did React Router v5 and Next.js Pages Router expose route parameters? / React Router v5 与 Next.js Pages Router 如何读取路由参数？

React Router v5 passed a matched parameter through its route context and allowed the component prop; Next.js Pages Router exposed dynamic parameters through next/router and router.query. These are version-specific APIs. React Router v6/v7 use a different route declaration shape, and Next.js App Router uses next/navigation and different page conventions. / React Router v5 通过路由上下文提供匹配参数，并支持 component 属性；Next.js Pages Router 则通过 next/router 和 router.query 提供动态参数。这些 API 有版本边界：React Router v6/v7 的路由声明形状不同，Next.js App Router 使用 next/navigation 和不同的页面约定。

~~~jsx
// React Router v5
import { Route, useParams } from 'react-router-dom';

function Post() {
  const { postId } = useParams();
  return <h1>Post {postId}</h1>;
}

function Routes() {
  return <Route path="/post/:postId" component={Post} />;
}
~~~

The v5 reference also offered BrowserRouter for history paths, HashRouter for fragment paths, MemoryRouter for in-memory navigation, and StaticRouter for a fixed server-rendering location. Browser-history client routes require the host to serve the app entry point.

~~~jsx
// Next.js Pages Router
import { useRouter } from 'next/router';

function UserPage() {
  const router = useRouter();
  const { userId } = router.query;
  return <h1>User {userId}</h1>;
}
~~~

In automatically statically optimized Pages Router pages, query values may be unavailable during the initial prerender; use router.isReady when client-only access is required. The App Router uses APIs from next/navigation instead. For current routing behavior, see [React Basics](../../../frontend/frameworks/react-basics.md) and [Next.js](../../../frontend/frameworks/next-js.md).

**Version sources / 版本来源:** [React Router v5.2.1 source](https://github.com/remix-run/react-router/tree/v5.2.1), [Next.js Pages Router useRouter](https://nextjs.org/docs/pages/api-reference/functions/use-router), and the original [archived framework references](../../../frontend/frameworks/next-js.md).
