Fetch data and render components in a incremental way:
```tsx
import { Suspense } from "react"
import type { Metadata } from 'next'

type Params = {
    params: {
        userId: string
    }
}

export default async function UserPage({ params: { userId } }: Params) {
    const userData: Promise<User> = getUser(userId)
    const userPostsData: Promise<Post[]> = getUserPosts(userId)
    const user = await userData
    return (
        <>
            <h2>{user.name}</h2>
            <br />
            <Suspense fallback={<h2>Loading...</h2>}>
                {/* @ts-expect-error Server Component */}
                <UserPosts promise={userPostsData} />
            </Suspense>
        </>
    )
}
type Props = {
    promise: Promise<Post[]>
}

async function UserPosts({ promise }: Props) {
    const posts = await promise
    const content = posts.map(post => {
        return (
            <article key={post.id}>
                <h2>{post.title}</h2>
                <p>{post.body}</p>
                <br />
            </article>
        )
    })
    return content
}

async function getUser(userId: string) {
    const res = await fetch(`https://jsonplaceholder.typicode.com/users/${userId}`)
    if (!res.ok) throw new Error('failed to fetch user')
    return res.json()
}

async function getUserPosts(userId: string) {
    const res = await fetch(`https://jsonplaceholder.typicode.com/posts?userId=${userId}`)
    if (!res.ok) throw new Error('failed to fetch user')
    return res.json()
}
```

Cache fetch results for 60 seconds, within 60 seconds it will not request data, instead it will use cached data. After 60 seconds, it will request data again. 

```tsx
export default async function getUserPosts(userId: string) {
    const res = await fetch(`https://jsonplaceholder.typicode.com/posts?userId=${userId}`, { next: { revalidate: 60 } })

    if (!res.ok) return undefined

    return res.json()
}
```

Cache fetch once and never request in future, use it if the data is not gonna update. 
```tsx
fetch('https://...', { cache: 'force-cache' })
```