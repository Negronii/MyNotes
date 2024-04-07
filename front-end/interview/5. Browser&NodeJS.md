## Explain how the stack is used in memory management for frontend applications
It operates on a Last In, First Out (LIFO) principle, efficiently managing function calls and primitive data types. When a function is invoked, its variables are pushed onto the stack, and upon the function's completion, they are removed. This system is particularly suitable for handling temporary, short-lived data. However, the stack's limited size means excessive usage can result in a stack overflow error.

## Explain how the heap is used in memory management for frontend web applications
It's used for dynamic allocation, primarily for objects and complex data structures. Unlike the stack, the heap is a larger, unstructured memory pool that requires manual management. Memory allocation and deallocation in the heap are handled by the JavaScript engine, which includes tasks like object creation and garbage collection.

## Explain the difference between primitive types and reference types
In JavaScript, primitive types and reference types are stored and accessed differently, which affects how they are used in programming.

Primitive types, such as `number`, `string`, `boolean`, `null`, `undefined`, `symbol`, and `bigint`, are stored directly in the variable's memory location, usually on the stack. This direct storage enables quick access and efficient memory management, particularly for simple, immutable values.

In contrast, reference types, like `object`, `array`, and `function`, are stored in the heap. When you create a reference type, the JavaScript engine allocates memory in the heap and stores the data there. The variable on the stack then holds a reference (or pointer) to that memory location. This means when you manipulate an object or an array, you're working through a reference. Any changes made to the object or array are reflected across all references to that object, as they all point to the same memory location in the heap.

### Related Topic: Memory Allocation for Objects and Arrays
Understanding how JavaScript allocates memory for objects and arrays is crucial. Since these are reference types, any operation involving copying or passing them around in your code means you're handling references, not the actual data. This behavior can lead to unexpected mutations if not properly managed, and is a fundamental concept in understanding JavaScript's memory management and behavior.

## What is debouncing and what is throttling, what are the differences, and name use cases of each

### Debouncing

Debouncing in web development is a strategy used to limit the frequency of execution of a potentially expensive operation that could be triggered repeatedly, such as during window resizing or scrolling. A debounced function will only execute after a specified amount of time has elapsed since the last time it was invoked. For example, if a debounced function is associated with a scrolling event, it will only execute after the user has stopped scrolling for a defined period.

**Throttling**

Throttling is a technique similar to debouncing, but instead of delaying the execution of a function, it ensures the function is executed at regular intervals. For instance, a function triggered by a scroll event, when throttled to execute every 100 milliseconds, will run at most 10 times per second, regardless of the frequency of the scroll event.

**Differences between Debouncing and Throttling**

1. **Timing Control**: Debouncing delays the execution of a function until a specified time has passed since its last invocation. Throttling, however, limits the function's execution to regular, specified intervals.

2. **Use Cases**: Debouncing is useful in scenarios where the function's frequent execution is unnecessary and delays are acceptable, such as in auto-saving or search bar suggestions. Throttling is employed when consistent execution rate is desired, like in handling scroll events or resizing.

3. **Behavior**: In debouncing, the function executes only after the triggering event has ceased for a defined duration. In throttling, the function executes at consistent intervals regardless of the frequency of event triggers.

**Use Cases**

1. **Debouncing**: This is commonly used in search bars, where you want to wait for the user to finish typing before firing an API request, rather than sending requests for every keystroke.

2. **Throttling**: An example is the implementation of infinite scrolling on a website, where you aim to load more content at certain intervals of scrolling, rather than at every small scroll movement.

Both debouncing and throttling are integral for enhancing performance and user experience in web applications. Libraries like **Lodash** offer robust implementations of these techniques.

### Implement debouncing in typescript
```js
function debounce(func, waitFor) {
    let timeout;

    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(this, args);
        }, waitFor);
    };
}

// Example Usage:
const debouncedLog = debounce((message) => console.log(message), 500);

// Usage
debouncedLog("Hello");
debouncedLog("Hello again, quickly"); // This call will cancel the previous one and only this message will be logged after 500ms
```

### Implement a throttling function in JavaScript
```js
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Example usage:
window.addEventListener('resize', throttle(function() {
    console.log('Resize event triggered');
}, 2000));
```

## Difference between HTMLCollection and NodeList

HTML and the Document Object Model (DOM) are essential components of web development. Understanding different parts of the DOM, such as `HTMLCollection` and `NodeList`, is crucial for manipulating web pages effectively.

- **HTMLCollection**: This is a live collection of HTML elements. It updates automatically when the DOM changes. `HTMLCollection` exclusively contains `Element` nodes, typically returned by methods like `document.getElementsByClassName` and the `.children` property of an element.

- **NodeList**: A more general collection that can include different types of nodes, not just elements. This can be live or static, depending on how it's obtained. For example, `NodeList` returned by `Node.childNodes` is live, but the one returned by `document.querySelectorAll` is static.

### Difference between HTMLCollection and NodeList

1. **Node Types**: `HTMLCollection` is limited to `Element` nodes, while `NodeList` can include any node types, such as `Element`, `Text`, and `Comment`.

2. **Dynamism**: `HTMLCollection` is always live, meaning it reflects DOM changes immediately. `NodeList` can be either live or static. Live `NodeList`s reflect DOM changes, whereas static ones do not.

### `.children` vs `.childNodes`

Considering the following HTML snippet:

```html
<p id='p1'>
    <em>hello</em> hello <b>bold</b><!-- comment -->
</p>
```

- `p.children` refers to an `HTMLCollection` containing only element nodes within `p` (`<em>` and `<b>` in this case). It does not include text nodes or comments.

- `p.childNodes` refers to a `NodeList` and includes all node types - `Element`, `Text`, and `Comment`. It will contain `<em>`, text nodes (including the 'hello' text), `<b>`, and the comment node.

- `p.tagName` and `p.nodeName` are properties used to get the tag name of an element. `p.tagName` is used specifically for elements and returns the tag name in uppercase, while `p.nodeName` is applicable to all types of nodes and returns the name of the node (the tag name for elements in uppercase).

In summary, `HTMLCollection` and `NodeList` are key concepts in DOM manipulation, each with its specific use cases. Understanding their differences is vital for efficient and effective front-end web development.

## Difference Between Browser and Node.js Event Loop:

JavaScript, known for its single-threaded nature, employs the event loop mechanism to manage asynchronous operations, facilitating non-blocking execution. This approach is pivotal in both browser and Node.js environments. However, the event loop's implementation and functionality exhibit distinct characteristics in each context, shaped by their unique operational demands.

### Micro-tasks and Macro-tasks:
- **Macro-tasks**: Encompass operations like `setTimeout`, `setInterval`, and various web API calls. They are scheduled to execute once the current script finishes and the micro-task queue is cleared.
- **Micro-tasks**: Primarily involve promise-related operations, including async/await. These tasks execute immediately after the current script, before any pending macro-tasks, granting them a higher execution priority.

### Browser Event Loop:
- In the browser, the event loop shares the main thread with activities such as DOM rendering, necessitating efficient task management to avoid UI disruptions.
- The browser event loop manages two kinds of task queues: macro-tasks and micro-tasks. Micro-tasks are given precedence, executing right after the current task, even before proceeding to the next macro-task. This prioritization ensures prompt handling of operations like promise resolutions, often before rendering the next frame.

### Node.js Event Loop:
- Node.js, while also single-threaded and dependent on asynchronous execution, classifies macro-tasks and micro-tasks into specific types and priorities. This reflects its backend-oriented nature, focusing on efficient I/O operations rather than UI concerns.
- **Macro-task types in Node.js**, listed in order of priority:
  - **Timers**: Includes `setTimeout` and `setInterval` for scheduling future tasks.
  - **I/O Callbacks**: Addresses network, stream, and TCP errors.
  - **Idle/Prepare**: Consists of internal Node.js engine tasks.
  - **Poll**: Responsible for fetching new I/O events.
  - **Check**: Manages `setImmediate` callbacks.
  - **Close Callbacks**: Executes callbacks such as `socket.on('close')`.

- **Micro-task types in Node.js**:
  - **`process.nextTick`**: This function defers the execution of a callback until the current operation concludes, offering very high priority.
  - **Promise/async/await**: Handles asynchronous operations using promises.

- In Node.js, the event loop initially executes synchronous code, then processes all micro-tasks (with `process.nextTick` having utmost priority), followed by macro-tasks. It also attends to micro-tasks as they emerge during macro-task execution.

The event loop in both browser and Node.js is fundamentally similar, enabling asynchronous JavaScript execution within a single-threaded context. However, their implementations diverge significantly. In Node.js, macro-tasks and micro-tasks are distinctly categorized with defined priorities, mirroring its backend emphasis on effective I/O management. Both environments prioritize synchronous tasks first, then micro-tasks, and finally macro-tasks. The browser's event loop, specifically designed to maintain UI responsiveness, prioritizes micro-tasks to ensure smooth user experiences. Conversely, Node.js's event loop structure is tailored for efficient I/O processing.

## Node.js Process Creation and Communication

### Process vs Thread
- **Process**: A process is the minimum unit for an Operating System (OS) to allocate resources and scheduling. It operates within its own independent memory space, ensuring that processes do not interfere with each other's operations.
- **Thread**: A thread is the smallest unit of processing within a process. It shares the memory space of its parent process, allowing for efficient execution of concurrent operations within the same application. JavaScript, while operating on a single-threaded model, supports multithreading through mechanisms like Web Workers for web applications.

### Why Use Multiprocessing in JavaScript?
- **Utilization of Multi-core CPUs**: It allows applications to leverage multi-core CPU architectures, significantly improving computation speed and application responsiveness.
- **Memory Limitations**: Each Node.js process has a memory limit. Multiprocessing enables an application to surpass the memory limitations of a single process, utilizing more memory collectively across multiple processes.
- **Efficiency and Performance**: Multiprocessing can lead to better resource utilization, enhanced performance, and reduced execution times by distributing workload across multiple CPU cores.
- **Application Methods**: In the context of web applications, `WebWorker` is utilized for multiprocessing to offload tasks from the main thread. For server-side applications using Node.js, multiprocessing is achieved through the `fork` or `cluster` modules, facilitating concurrent execution of tasks and improved application scalability.

### Fork in Node.js
The `fork` method is a part of the `child_process` module in Node.js, designed to create child processes. Here is a example illustrating how to use `fork`:

```javascript
// Main process (e.g., server.js)
const http = require('http');
const { fork } = require('child_process');

const server = http.createServer((req, res) => {
    if (req.url === '/compute') {
        const computeProcess = fork('./compute.js');
        computeProcess.send('Start');

        computeProcess.on('message', (result) => {
            res.end(`Result: ${result}`);
        });

        computeProcess.on('exit', () => console.log('Computation process exited'));
    } else {
        res.end('Server is running');
    }
});

server.listen(3000, () => console.log('Server listening on port 3000'));

// Child process (e.g., compute.js)
process.on('message', (msg) => {
    if (msg === 'Start') {
        let sum = 0;
        for (let i = 0; i < 10000; i++) sum += i;
        process.send(sum);
        process.exit(0);
    }
});
```

### Cluster in Node.js
The `cluster` module in Node.js enables the creation of child processes that share server ports, facilitating load balancing across multiple CPU cores. Below is a example of using `cluster`:

```javascript
const cluster = require('cluster');
const http = require('http');
const numCPUs = require('os').cpus().length;

if (cluster.isMaster) {
    console.log(`Master process is running with PID: ${process.pid}`);

    for (let i = 0; i < numCPUs; i++) {
        cluster.fork();
    }

    cluster.on('exit', (worker) => {
        console.log(`Worker ${worker.process.pid} died. Restarting...`);
        cluster.fork();
    });
} else {
    http.createServer((req, res) => {
        res.writeHead(200);
        res.end('Hello from Node.js!');
    }).listen(8000);

    console.log(`Worker started with PID: ${process.pid}`);
}
```

**Best Practices**:
- **PM2 for Process Management**: In production, consider using PM2 or similar tools for advanced process management and load balancing. These tools offer more sophisticated monitoring, logging, and clustering features.
- **Fork vs. Cluster Usage**:
  - **Fork**: Best suited for offloading CPU-intensive tasks to child processes, thereby preventing the main application thread from blocking.
  - **Cluster**: Ideal for creating redundant worker processes in server applications, enhancing availability and fault tolerance, especially under high load.

## How to Prevent 300ms Delay for Double Click to Zoom on Mobile Phones?
On mobile web applications, a common issue is the 300ms delay when users attempt to double-click (tap) to zoom. This delay was originally implemented to differentiate between a tap (single click) and a double-tap (double click). However, this can interfere with the responsiveness of web applications. In the past, developers used libraries like FastClick to circumvent this delay. Modern browsers have introduced ways to address this issue by detecting the site's responsiveness through meta tags.

To prevent the 300ms delay on mobile devices without relying on external libraries like FastClick, ensure your web application is using responsive design principles. Implement the following meta tag in your HTML:
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```
This meta tag informs the browser that your website is optimized for mobile devices, prompting it to disable the 300ms delay for a better user experience. This approach is preferred as it relies on standard responsive design practices rather than additional scripts, improving your website's performance and compatibility.

## Describe JS-bridge principles

### What is JS-bridge
JSBridge serves as a middleware between native applications and JavaScript running within a webview. JavaScript cannot directly invoke native APIs due to the sandboxed nature of web content for security reasons. A JSBridge provides a structured interface through which JavaScript can communicate with the native side of an application. This enables web content to access device features or native functionality that is otherwise inaccessible to pure web applications. For example, within the Facebook app, it's possible to open H5 websites; this is facilitated by JSBridge, allowing the web content to interact with the app's native features.

### Frequent used methods to achieve JS-Bridge

1. **Global API Registration**: This method involves exposing native functions as global JavaScript functions that can be called directly from the web content. However, this approach may encounter issues with asynchronous execution, such as delays in reading from local files or fetching data over the network. For example:

```js
// Incorrect: const version = window.getVersion() // getVersion is from bridge, but have problem of lag at async, e.g. read from local file or web
async function getVersion() {
  return new Promise((resolve, reject) => {
    if (window.bridge && window.bridge.getVersion) {
      resolve(window.bridge.getVersion());
    } else {
      reject('Bridge or getVersion method not found.');
    }
  });
}
```

2. **URL Scheme (Recommended)**: This technique involves defining custom URL schemes that the native application can recognize and handle. When a webview navigates to a URL with a custom scheme, the app intercepts the request and performs the corresponding native action. This method is more flexible and allows for easy asynchronous communication. A common implementation involves creating invisible iframes to trigger these URL schemes without navigating away from the current page. The example provided showcases an SDK object encapsulating calls to different native functions via URL schemes:

```js
// Example of an SDK object to interface with native app functions through URL schemes
const sdk = {
    invoke(url, data, onSuccess, onError) {
        const iframe = document.createElement('iframe');
        iframe.style.visibility = 'hidden';
        document.body.appendChild(iframe);
        iframe.onload = () => {
            try {
                const content = iframe.contentWindow.document.body.innerHTML;
                onSuccess(JSON.parse(content));
            } catch (error) {
                onError(error);
            } finally {
                iframe.remove();
            }
        };
        iframe.onerror = (error) => {
            onError(error);
            iframe.remove();
        };
        iframe.src = `my-app-name://${url}?data=${encodeURIComponent(JSON.stringify(data))}`;
    },
    fn1(data, onSuccess, onError) {
        this.invoke('api/fn1', data, onSuccess, onError);
    },
    fn2(data, onSuccess, onError) {
        this.invoke('api/fn2', data, onSuccess, onError);
    },
    fn3(data, onSuccess, onError) {
        this.invoke('api/fn3', data, onSuccess, onError);
    }
};
```

## Describe the Complete Process of Entering a URL to Presenting the Page

When a URL is entered into a browser, the process from initiating a web request to the final rendering of the page involves several critical steps. Here is a detailed breakdown:

### Web Request
1. **DNS Lookup**: The browser initiates a DNS query to convert the hostname in the URL into an IP address. This process may involve querying multiple DNS servers.
2. **TCP Connection**: Establishes a TCP connection with the server using a three-way handshake. This ensures a reliable communication channel.
3. **HTTP Request**: The browser sends an HTTP request to the server's IP address, requesting the webpage content.
4. **Server Response**: The server processes the request and sends back a response, typically including the HTML source code of the page.

### Parsing HTML
1. **Resource Fetching**: As the browser parses the HTML, it may encounter references to external resources such as JavaScript, CSS, images, and videos. Each of these resources may require additional DNS lookups, TCP connections, and HTTP requests.
2. **DOM and CSSOM Trees**: The browser converts the HTML document into a structured format known as the Document Object Model (DOM). Simultaneously, CSS files are processed into the CSS Object Model (CSSOM) or style tree.
3. **Render Tree Construction**: The DOM and CSSOM trees are combined to form the render tree, which represents all visible elements on the page and their styles.
4. **Optimization**: To optimize loading and parsing:
   - CSS is typically placed in the `<head>` to avoid rendering blocks.
   - JavaScript files are placed at the end of the `<body>` or loaded with `defer` or `async` attributes to not block HTML parsing.
   - Specifying image dimensions helps in layout calculation and prevents reflows.

### Rendering the Page
1. **Layout Calculation**: The browser calculates the size and position of each element in the render tree.
2. **Painting**: The visible elements are then painted onto the screen.
3. **JavaScript Execution**: JavaScript files are executed, which may modify the DOM and trigger a re-rendering of the page.
4. **Asynchronous Loading**: Some resources, like CSS and images, are fetched asynchronously and may cause the page to render again upon loading.

### Repaint vs. Reflow

Understanding the difference between repaint and reflow is crucial in web development, especially for dynamic web pages where elements can change frequently due to animations, modals, dialogs, popups, or modifications to the DOM like adding or deleting elements.

#### Repaint
A repaint occurs when changes are made to an element's visual appearance that do not affect its layout in the document. Examples include changes in color, background-color, visibility, and outline. During a repaint, the element's geometry (size and position) remains unchanged, and thus, it does not impact the position of any other elements.

#### Reflow
Reflow, also known as layout, involves recalculating the positions and sizes of elements in the document. This process is more computationally expensive than repaints because it affects the layout of the element that is changing and may also impact other elements on the page. Causes of reflow include changes to the browser window size, alterations in content (such as adding or removing elements), and modifications to elements' styles affecting their sizes (e.g., width, height, margin, padding).

#### Difference
The primary difference between repaint and reflow is the scope of impact and the cost in terms of performance. Reflows can trigger repaints, but repaints do not necessarily cause reflows. Because reflows can impact the layout of the entire page, they are more performance-intensive than repaints.

#### Methods to Avoid Unnecessary Reflows
- **Batch Style Changes**: Apply multiple style changes at once by changing the class of an element instead of individual styles.
- **Minimize DOM Access**: Modify elements offscreen or in a document fragment before adding them to the DOM. Using `display: none` before making changes can remove the element from the flow, thus reducing reflow costs.
- **Use Block Formatting Context (BFC)**: Utilizing BFC properties can isolate elements from affecting each other, minimizing the need for reflows.
- **Event Optimization**: Use debouncing and throttling for events that trigger frequent reflows, such as window resizing or scrolling.
- **Optimize Animations**: Prefer CSS3 animations and `requestAnimationFrame` over JavaScript animations to reduce reflow and repaint costs.

### Expansion: Block Formatting Context (BFC)
A Block Formatting Context is an HTML box that serves as a containment boundary, ensuring that elements within it do not affect the layout of elements outside it. BFC can be triggered by:
- The root element (`html`).
- Elements with `float` properties other than `none`.
- Elements with `position: absolute` or `fixed`.
- Elements with `display: inline-block`, `table-cell`, `table-caption`, `flex`, `grid`, or other table-related values.
- Elements with `overflow` set to anything other than `visible`.

## How to Implement Multi-Tab Communication on a Website?

Implementing multi-tab communication in web applications allows for the sharing of data and messages between different tabs or windows of the same origin. Here are three common methods to achieve this, along with their advantages, limitations, and use cases.

### 1. Using WebSockets
WebSockets provide a full-duplex communication channel over a single, long-lived connection, enabling real-time data exchange between the client and server.

- **Advantages**:
  - No CORS (Cross-Origin Resource Sharing) limitations, allowing for communication across different domains.
  - Enables real-time, bidirectional communication between the client and server.

- **Limitations**:
  - Requires server-side support, which can be more costly and complex to implement compared to client-side-only solutions.
  - Maintaining a WebSocket connection can be resource-intensive for both the server and client.

- **Use Case**:
  Ideal for applications that require real-time data exchange, such as live chat applications, online gaming, and collaborative editing tools.

### 2. Using `localStorage`
`localStorage` is a web storage API that allows data to be stored in key-value pairs in the browser, and it can be used for communication between tabs within the same origin.

- **Advantages**:
  - Simple to implement and does not require server-side support.
  - Works across tabs within the same origin, making it suitable for sharing data between different parts of the same application.

- **Limitations**:
  - Limited to communication within the same origin.
  - Storage space is limited (typically around 5MB).

- **Example Code**:
  ```html
  <!-- In one tab (e.g., list page) -->
  <script>
      window.addEventListener('storage', event => {
          if (event.key === 'changeInfo') {
              console.info('New info received:', event.newValue);
          }
      });
  </script>
  <!-- In another tab (e.g., detail page) -->
  <script>
      document.getElementById('btn1').addEventListener('click', () => {
          const newInfo = {
              id: 100,
              name: 'Item ' + Date.now()
          };
          localStorage.setItem('changeInfo', JSON.stringify(newInfo));
      });
  </script>
  ```
  - **Key Points**:
    - Tabs A and B are within the same origin.
    - Tab A sets `localStorage`, and Tab B listens for changes in `localStorage`.

### 3. Using `SharedWorker`
`SharedWorker` is a type of Web Worker that allows for the creation of a shared execution environment, accessible by multiple scripts even if they are in different windows, iframes, or tabs.

- **Advantages**:
  - Enables communication and data sharing between tabs, iframes, or windows from the same origin.
  - Offloads work to a background thread, preventing UI blocking.

- **Limitations**:
  - More complex to implement and test compared to other methods.
  - Support across browsers can be inconsistent.
  - Limited to same-origin communication.

- **Example Code**:
  ```html
  <!-- In one tab (e.g., list) -->
  <script>
      const worker = new SharedWorker('worker.js');
      worker.port.onmessage = e => console.info('Message from worker:', e.data);
  </script>
  <!-- In another tab (e.g., detail) -->
  <script>
      const worker = new SharedWorker('worker.js');
      document.getElementById('btn1').addEventListener('click', () => {
          worker.port.postMessage('Message from detail tab');
      });
  </script>
  ```
  ```js
  // worker.js
  const ports = new Set();
  onconnect = event => {
      const port = event.ports[0];
      ports.add(port);
      port.onmessage = e => {
          // Broadcast the message to all connected ports except the sender
          ports.forEach(p => {
              if (p !== port) {
                  p.postMessage(e.data);
              }
          });
      };
      port.postMessage('SharedWorker initialized');
  }
  ```
  - **Key Points**:
    - `SharedWorker` can start a shared process for communication between tabs from the same origin.
    - It is capable of running JavaScript in the background, independent of any particular tab, allowing for more complex inter-tab communication scenarios.

### How to Achieve Communication Between a Website and an Iframe

Communicating between a website and an iframe can be efficiently achieved using the `window.postMessage()` method. This approach allows for secure cross-origin communication without being restricted by CORS (Cross-Origin Resource Sharing) policies. The `postMessage` method enables sending data from the parent page to an iframe or vice versa, regardless of their origin, ensuring a versatile and secure way to interact across different domains.

- **Advantages**:
  - Bypasses CORS restrictions, enabling communication across different origins.
  - Provides a mechanism to verify the origin of the messages, enhancing security.

- **Example Code**:

  - **Child (Iframe Content)**:
    ```html
    <!-- Child HTML content -->
    <p>Child page
      <button id="btn1">Send Message</button>
    </p>
    <script>
        const btn1 = document.getElementById('btn1');
        btn1.addEventListener('click', () => {
            console.info('Child button clicked');
            window.parent.postMessage('Message from child', '*'); // Use specific origin instead of '*' in production
        });

        window.addEventListener('message', event => {
            // Always check the origin of the data!
            if (/* validate event.origin */) {
                console.info('Origin:', event.origin);
                console.info('Child received:', event.data);
            }
        });
    </script>
    ```
  - **Parent**:
    ```html
    <!-- Parent HTML content -->
    <p>Index page
      <button id="btn1">Send Message</button>
    </p>
    <iframe id="iframe1" src="./child.html"></iframe>
    <script>
        const btn1 = document.getElementById('btn1');
        const iframe = document.getElementById('iframe1');

        btn1.addEventListener('click', () => {
            console.info('Parent button clicked');
            iframe.contentWindow.postMessage('Message from parent', '*'); // Use specific origin instead of '*' in production
        });

        window.addEventListener('message', event => {
            // Always validate the origin of the data!
            if (/* validate event.origin */) {
                console.info('Origin:', event.origin);
                console.info('Parent received:', event.data);
            }
        });
    </script>
    ```
- **Key Points**:
  - The `'*'` argument in `postMessage` indicates that the message can be sent to any origin. In production environments, this should be replaced with the specific target origin to prevent security vulnerabilities.
  - It's crucial to validate the `event.origin` in the message event listener to ensure that messages are only accepted from trusted sources. This validation prevents potential cross-site scripting (XSS) attacks.

## HTML5 First-Screen Optimization Techniques

### 1. Route Lazy Loading
- **Applicability**: Suitable for Single Page Applications (SPA) but not for Multi-Page Applications (MPA).
- **Concepts**: 
  - **SPA** refers to a web application or site that interacts with the user by dynamically rewriting the current page rather than loading entire new pages from the server. This results in a more fluid user experience similar to a desktop application.
  - **MPA** is a traditional web application approach that reloads the entire page and requests the HTML from the server on each page change.
- **Implementation in React**: Achieved by splitting the route and ensuring priority loading of the homepage. This can be done using React's `React.lazy` and `Suspense` for dynamic imports and lazy loading of components.

### 2. Server-Side Rendering (SSR) - Exemplified by Next.js
- **Explanation**: Traditional SPA renders the page in a complex process, downloading HTML and JavaScript first, then fetching other resources. SSR simplifies this process by serving a fully rendered HTML page directly from the server, improving performance.
- **Benefits**: Ideal for pure HTML5 pages as it offers ultimate performance optimization, albeit at a higher cost.
- **Historical Context**: SSR is not a new technology. It has been used since the HTML1.0 era in technologies like PHP, ASP, and JSP. With the evolution of technology and the separation of front-end and back-end development, it has gained recent attention for enhancing user experience. Nuxt.js (for Vue) and Next.js (for React) are current examples.

### 3. App Prefetch
- **Usage**: When an HTML5 page is displayed within an app WebView, such as opening a page on Facebook.
- **Method**: The app preloads the first screen content of an article when the user visits the list page. Upon entering the HTML5 page, content is retrieved directly from the app using JSBridge, allowing instant display of the first screen.

### 4. Pagination
- **Application**: Specifically for list pages.
- **Strategy**: Only the first page's content is displayed by default. More content is loaded as the user scrolls up, which can be optimized further with throttling to manage load performance.

### 5. Image Lazy Loading
- **Focus**: Primarily for detail pages.
- **Approach**: Text content is displayed by default, followed by images through lazy loading.
- **Note**: Ensure image dimensions are set in advance to reserve space, minimizing layout shifts and reflows.

### 6. Hybrid Approach
- **Method**: HTML, JavaScript, and CSS files are pre-downloaded to the app. Pages are loaded using the `file://` protocol within the app's WebView, which is significantly faster as it accesses local files.
- **Content Fetching**: Content is then fetched via AJAX and displayed, potentially in combination with app prefetching for enhanced performance.

## Handling Rendering of 100,000 Data Entries

It's essential to first communicate to the interviewer that returning 100,000 data entries in one go is technically impractical. A preferable approach would be to use **pagination** to limit the amount of data sent and rendered at any one time.

Before seeking solutions, assess whether the browser can handle processing 100,000 data entries. While handling such data as strings or simple data structures in JavaScript might be feasible, rendering them directly to the DOM would result in significant performance issues, including sluggishness and potential crashes.

### 1. **Custom Middleware Layer**:
Implement a custom Node.js middleware layer that fetches and processes the 100,000 data entries. The front-end application would then interact with this middleware instead of directly connecting to the backend server.

While this approach can help manage the data more efficiently by pre-processing it before rendering, it is costlier in terms of development time and resources.

### 2. **Virtual Scrolling (Virtual List)**:
Implement virtual scrolling to render only the DOM elements in the viewport. Elements outside the viewport are not rendered but are accounted for in terms of spacing to ensure smooth scrolling. As the user scrolls, elements enter the viewport are rendered, and those leaving the viewport are destroyed or reused.

Implementing virtual scrolling improves application performance significantly by reducing the number of DOM elements that need to be managed at any given time, thereby minimizing browser workload and memory usage.

This method is technically challenging to implement from scratch due to the need to manage the creation and destruction of DOM elements dynamically based on the scroll position. It is highly recommended to use third-party libraries that provide virtual scrolling capabilities.

For Vue.js projects, `Vue-virtual-scroll-list` can be used, and for React projects, `React-virtualized` is a suitable choice. These libraries simplify the implementation of virtual scrolling by handling the complexities of DOM element management based on scroll behavior.

However, even using these libraries, the performance is still a concern for phones and low-end devices. It's important to consider the user experience and the practicality of displaying such a large amount of data at once.


## How to diagnose performance issues in a slow HTML5 page?
Start by asking the interviewer whether the issue is related to slow operations or slow loading times to narrow down the problem scope and demonstrate proactive communication skills. Then, check for any errors; if there are errors, start investigating from there. If there are no errors, use Chrome's Performance tools for further investigation.

### Front-end Performance Metrics
- **First Paint (FP):** The time it takes for the browser to render the first pixel to the screen.
- **First Contentful Paint (FCP):** The time it takes for the browser to render the first DOM content.
- **First Meaningful Paint (FMP):** Deprecated. This metric was used to measure the time it takes for the browser to render meaningful content for the first time. It has been replaced by LCP.
- **DOMContentLoaded (DCL):** The time it takes for the DOM to be fully loaded and parsed.
- **Largest Contentful Paint (LCP):** The time it takes for the largest content element in the viewport to become visible.
- **Load:** The time it takes for the entire page and all its resources to fully load.

These metrics are arranged in chronological order: FP < FCP < FMP < DCL < LCP < Load.

### Chrome DevTools
- **Performance:** Records page performance data, including CPU, memory, network, rendering, and more. Enabling screenshots captures web page snapshots, and timing indicators can show the metrics mentioned above.
- **Network:** Analyzes network requests, including the resources requested, timeline, size, and more. It also shows an overview of performance metrics when enabled.

### Lighthouse
A popular third-party performance evaluation tool that works on both mobile and desktop. It provides an overall score, including the above metrics, and offers optimization suggestions such as using next-gen image formats (e.g., WebP, AVIF), compressing and correctly sizing images, which can save loading time.

**Example:**
```
npm install -g lighthouse
lighthouse https://www.baidu.com --view --preset=desktop
```

### Web Page Loading Slowly?
- Improve server hardware configurations, use CDN.
- Implement route lazy loading and asynchronously load large components to reduce the main package size.
- Optimize HTTP caching strategies.

### Slow Rendering?
- Optimize backend services (e.g., slow AJAX data fetching).
- Further analyze and optimize the logic within front-end components.
- Implement server-side rendering (SSR).

### Continuous Follow-up
Performance optimization is a gradual process, unlike bug fixes which can often be resolved quickly. Continuously monitor performance, identify bottlenecks, and implement optimizations progressively. Utilize third-party analytics services such as Alibaba Cloud ARMS, Baidu Analytics, or Google Analytics for ongoing performance tracking.

### Summary
Analyze performance metrics to identify the root causes of slowness, address issues specifically, and continuously improve and optimize for better performance.
