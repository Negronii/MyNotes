# Next.js / Next.js开发

## What does Next.js add to React? / Next.js为React增加了什么？

**Core answer / 核心回答：** Next.js is a React framework that combines routing, server and client rendering, data access, and deployment integrations. Its Pages Router and App Router have different file conventions and rendering APIs, so name the router and version when describing behavior. / Next.js 是 React 框架，整合路由、服务端与客户端渲染、数据访问和部署集成。Pages Router 与 App Router 的文件约定和渲染 API 不同，说明行为时要注明路由器和版本。

Next.js can produce HTML on the server or ahead of a request, and it can update route content in the browser. These options are not one global switch: choose based on the route's data freshness, user-specific content, runtime, and caching needs.

## Pages Router: SSR, SSG, and ISR / Pages Router：SSR、SSG和ISR

The following APIs belong to the **Pages Router** under the pages directory.

| Strategy | API | When it fits |
|---|---|---|
| Server rendering per request | getServerSideProps | Request-specific data or authorization must be resolved on the server for each request. |
| Static generation | getStaticProps and, for dynamic paths, getStaticPaths | Output can be produced before a request and reused. |
| Incremental Static Regeneration | getStaticProps with revalidate | A generated page can be refreshed after a time window or on demand. |
| Client-side data | Browser fetch or a client data library | Data is user-specific or does not need to be in the initial server-rendered response. |

~~~jsx
// pages/posts/[id].js — Pages Router
export async function getServerSideProps({ params }) {
  const response = await fetch(
    "https://api.example.com/posts/" + params.id
  );

  if (response.status === 404) return { notFound: true };
  if (!response.ok) throw new Error("Post request failed: " + response.status);

  return { props: { post: await response.json() } };
}

export default function PostPage({ post }) {
  return <article><h1>{post.title}</h1></article>;
}
~~~

For ISR, a successful getStaticProps result can return revalidate: 60. This is a minimum interval before a request can trigger regeneration, not a timer that regenerates every minute. After the interval, a request can receive the stale page while regeneration runs; a successful new result replaces the cached version. Dynamic paths also need getStaticPaths and a deliberate fallback policy. In this Pages Router example, fallback: false makes paths omitted from the build-time list return 404; fallback: "blocking" generates an omitted path on its first request before returning HTML.

~~~jsx
// pages/posts/[id].js — Pages Router
export async function getStaticPaths() {
  const response = await fetch("https://api.example.com/posts");
  if (!response.ok) throw new Error("Could not list posts");
  const posts = await response.json();

  return {
    paths: posts.map(post => ({ params: { id: String(post.id) } })),
    fallback: "blocking"
  };
}

export async function getStaticProps({ params }) {
  const response = await fetch("https://api.example.com/posts/" + params.id);
  if (response.status === 404) return { notFound: true };
  if (!response.ok) throw new Error("Post request failed: " + response.status);

  return { props: { post: await response.json() }, revalidate: 60 };
}
~~~

## App Router: Server Components and caching / App Router：Server Components与缓存

Under the app directory, pages and layouts are Server Components by default. They can fetch on the server and pass serializable data to a Client Component. A file marked use client creates a client boundary for Hooks, event handlers, and browser APIs. Client Components may still contribute to initial HTML; use client does not mean the whole route is client-only.

~~~tsx
// app/posts/page.tsx — App Router
async function getPosts() {
  const response = await fetch("https://api.example.com/posts", {
    cache: "no-store"
  });
  return response.json();
}

export default async function PostsPage() {
  const posts = await getPosts();
  return (
    <ul>
      {posts.map(post => <li key={post.id}>{post.title}</li>)}
    </ul>
  );
}
~~~

In the current Next.js 16.4.1 documentation checked on 2026-10-15, App Router fetch requests are not cached by default. Set caching deliberately, for example with a fetch revalidation option; with Cache Components enabled, a use cache directive can cache a component or function. Request-time data and static shells can be combined with Suspense and streaming. Older Next.js App Router versions had different fetch defaults, so do not carry a versionless caching rule between projects.

A Client Component can receive data from a Server Component through props, but props crossing the boundary must be serializable. Keep secrets and server-only dependencies on the server.

## How does file-based routing work? / 文件系统路由如何工作？

**Core answer / 核心回答：** The route tree follows files, but the conventions differ between routers. Pages Router uses files such as pages/about.js and pages/posts/[id].js. App Router uses route segments containing page.tsx and can add layout.tsx, loading.tsx, and error.tsx. / 路由树由文件结构决定，但两种路由器的约定不同。Pages Router 使用 pages/about.js、pages/posts/[id].js 等文件；App Router 使用包含 page.tsx 的路由段，并可加入 layout.tsx、loading.tsx 和 error.tsx。

Use Link for navigation. Prefetching is production-only and differs by router: App Router can fully prefetch static routes and partially prefetch dynamic routes to a loading boundary; Pages Router's default behavior differs. Treat prefetch as an optimization, not a guarantee that a destination is already loaded.

## What are API routes and Route Handlers? / API routes和Route Handler是什么？

**Core answer / 核心回答：** Pages Router API routes use a default handler in pages/api. App Router Route Handlers use named HTTP method exports in a route.ts file. The runtime and deployment model depend on configuration and hosting; an endpoint is not automatically a serverless function just because it is in a Next.js app. / Pages Router 的 API route 在 pages/api 中使用默认 handler；App Router 的 Route Handler 在 route.ts 中导出 HTTP 方法函数。运行时和部署模型取决于配置与托管平台；接口不会因为位于 Next.js 应用中就自动成为 serverless function。

~~~ts
// app/api/hello/route.ts — App Router
export async function GET() {
  return Response.json({ message: "Hello from Next.js" });
}
~~~

Use framework endpoints for colocated, bounded server work such as webhooks or a small proxy. A larger backend may need its own service boundary, runtime, and operational controls.

**See also:** [React Basics / React基础](./react-basics.md) for client navigation and document models; [Node.js Fundamentals / Node.js基础](../../engineering-foundations/backend/node-js-fundamentals.md) for server runtime constraints.

**Sources checked 2026-10-15:** [Next.js 16.4.1 App Router migration guide](https://nextjs.org/docs/app/guides/migrating/app-router-migration), [Pages Router getServerSideProps](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-server-side-props), [Pages Router getStaticPaths](https://nextjs.org/docs/pages/building-your-application/data-fetching/get-static-paths), [Pages Router Incremental Static Regeneration](https://nextjs.org/docs/pages/building-your-application/data-fetching/incremental-static-regeneration), [Fetching Data](https://nextjs.org/docs/app/getting-started/fetching-data), [use cache](https://nextjs.org/docs/app/api-reference/directives/use-cache), [Incremental Static Regeneration](https://nextjs.org/docs/app/guides/incremental-static-regeneration), [Link](https://nextjs.org/docs/app/api-reference/components/link), [Route Handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route).
