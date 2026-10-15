# Next.js App Router Data Fetching / Next.js App Router数据获取

This example starts independent requests together, then lets a nested Server Component suspend while its data resolves. It covers the **App Router**; Pages Router APIs such as `getServerSideProps`, `getStaticProps`, and `getStaticPaths` belong to the separate `pages/` router. / 示例并行启动互不依赖的请求，再由嵌套 Server Component 在数据就绪前挂起。这里介绍的是 **App Router**；`getServerSideProps`、`getStaticProps` 和 `getStaticPaths` 属于独立的 `pages/` 路由器。

**Key terms / 关键词：** Server Component 服务端组件 · Suspense 挂起边界 · Data Cache 数据缓存 · revalidation 重新验证

**Related notes / 相关笔记：** [Next.js / Next.js开发](../../../../frontend/frameworks/next-js.md) compares the Pages and App Routers and their version boundaries; [React Basics / React基础](../../../../frontend/frameworks/react-basics.md) explains render and commit.

## Stream independently fetched data / 流式渲染独立获取的数据

The parameter type below uses the Next.js 15+ App Router contract: `params` is a promise and must be awaited. In Next.js 13/14 App Router examples, `params` was synchronous. The function signatures describe expected JSON shapes; TypeScript does not validate `response.json()` at runtime, so validate untrusted responses before relying on these fields in an application. / 下方参数类型遵循 Next.js 15+ App Router 约定：`params` 是 Promise，需要 await。Next.js 13/14 App Router 示例中的 `params` 是同步值。函数签名描述预期 JSON 结构；TypeScript 不会在运行时验证 `response.json()`，因此应用应先校验不可信响应。

```tsx
import { Suspense } from "react";

type Params = {
  params: Promise<{ userId: string }>;
};

type User = { name: string };
type Post = { id: number; title: string; body: string };

export default async function UserPage({ params }: Params) {
  const { userId } = await params;
  const userData = getUser(userId);
  const userPostsData = getUserPosts(userId);
  const user = await userData;
  return (
    <>
      <h2>{user.name}</h2>
      <br />
      <Suspense fallback={<h2>Loading...</h2>}>
        <UserPosts promise={userPostsData} />
      </Suspense>
    </>
  );
}
type Props = {
  promise: Promise<Post[]>;
};

async function UserPosts({ promise }: Props) {
  const posts = await promise;
  const content = posts.map((post) => {
    return (
      <article key={post.id}>
        <h2>{post.title}</h2>
        <p>{post.body}</p>
        <br />
      </article>
    );
  });
  return content;
}

async function getUser(userId: string): Promise<User> {
  const res = await fetch(
    `https://jsonplaceholder.typicode.com/users/${userId}`
  );
  if (!res.ok) throw new Error("failed to fetch user");
  return res.json();
}

async function getUserPosts(userId: string): Promise<Post[]> {
  const res = await fetch(
    `https://jsonplaceholder.typicode.com/posts?userId=${userId}`
  );
  if (!res.ok) throw new Error("failed to fetch posts");
  return res.json();
}
```

`next.revalidate` opts this request into the Data Cache and sets its revalidation interval. It is not a timer that makes a request every 60 seconds: after the interval, a later request can trigger revalidation, and the cache may serve stale data while it refreshes. In Next.js 16.2.9, App Router `fetch` calls are not persistently cached by default; identical calls in a component tree can still be memoized for that render. / `next.revalidate` 会将请求加入 Data Cache 并设置重新验证间隔。它不是每 60 秒定时发起一次请求：间隔过后，后续请求才可能触发重新验证，缓存也可能在刷新期间返回旧数据。Next.js 16.2.9 的 App Router `fetch` 默认不会持久缓存；同一组件树中的相同请求仍可能在本次 render 中去重。

```tsx
export default async function getUserPosts(userId: string) {
  const res = await fetch(
    `https://jsonplaceholder.typicode.com/posts?userId=${userId}`,
    { next: { revalidate: 60 } }
  );

  if (!res.ok) throw new Error("failed to fetch posts");

  return res.json();
}
```

`force-cache` opts into the persistent Data Cache. It can be invalidated or revalidated; it is not a guarantee that the origin will never be contacted again. Use it only when sharing the cached response across requests is appropriate. / `force-cache` 会将请求加入持久 Data Cache；缓存仍可被失效或重新验证，因此不保证源站永远不会再收到请求。只有适合跨请求共享响应时才使用。

```tsx
fetch("https://...", { cache: "force-cache" });
```

**Sources checked 2026-10-15 against Next.js 16.2.9:** [App Router Fetching Data](https://github.com/vercel/next.js/blob/v16.2.9/docs/01-app/01-getting-started/06-fetching-data.mdx), [fetch API and revalidation](https://github.com/vercel/next.js/blob/v16.2.9/docs/01-app/03-api-reference/04-functions/fetch.mdx), [Page `params`](https://github.com/vercel/next.js/blob/v16.2.9/docs/01-app/03-api-reference/03-file-conventions/page.mdx), [Incremental Static Regeneration](https://github.com/vercel/next.js/blob/v16.2.9/docs/01-app/02-guides/incremental-static-regeneration.mdx).
