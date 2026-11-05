# How does this React course use Axios for HTTP requests? / 本 React 课程如何使用 Axios 发起 HTTP 请求？

Axios returns a Promise with a response object; component examples can model loading, success, and failure, while shared defaults and interceptors centralize request configuration. TypeScript generics still do not validate response JSON at runtime. / Axios 返回带响应对象的 Promise；组件示例可处理加载、成功和失败，全局默认值与拦截器可集中请求配置。TypeScript 泛型仍不会在运行时验证响应 JSON。

## Fetching Data with Axios / 使用Axios获取数据

Axios is a promise-based HTTP client for JavaScript and TypeScript. Browser support depends on the Axios version and its adapter; this course makes no compatibility claim for obsolete browsers. The examples show basic requests, loading/error state, defaults, and interceptors.

## Installation

To install Axios, use the following command:

```bash
npm install axios
```

Alternatively, if you are using Yarn:

```bash
yarn add axios
```

## Basic Usage

### Performing GET Requests

Axios simplifies making HTTP GET requests. Here's a basic example:

```typescript
import axios from 'axios';

axios.get('https://api.example.com/data')
  .then(response => {
    console.log(response.data);
  })
  .catch(error => {
    console.error('Error fetching data:', error);
  });
```

### Performing POST Requests

Similarly, making a POST request is straightforward:

```typescript
import axios from 'axios';

const data = {
  key1: 'value1',
  key2: 'value2'
};

axios.post('https://api.example.com/data', data)
  .then(response => {
    console.log('Data posted successfully:', response.data);
  })
  .catch(error => {
    console.error('Error posting data:', error);
  });
```

## Example Usage in a React Component

Here is a comprehensive example of using Axios within a React component. This example demonstrates how to handle loading states, errors, and rendering fetched data.

```typescript
import React, { Component } from 'react';
import axios from 'axios';
import { Spin, Typography, Row } from 'antd';
import { withTranslation, WithTranslation } from 'react-i18next';
import ProductCollection from './ProductCollection';

interface State {
  loading: boolean;
  error: string | null;
  productList: any[];
}

class HomePageComponent extends Component<WithTranslation, State> {
  constructor(props: WithTranslation) {
    super(props);
    this.state = {
      loading: true,
      error: null,
      productList: []
    };
  }

  async componentDidMount() {
    try {
      const response = await axios.get('https://api.example.com/product-collections');
      this.setState({
        loading: false,
        productList: response.data
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        this.setState({
          loading: false,
          error: error.message
        });
      } else {
        this.setState({ loading: false, error: 'Unexpected request error' });
      }
    }
  }

  render() {
    const { t } = this.props;
    const { productList, loading, error } = this.state;

    if (loading) {
      return <Spin size="large" style={{ marginTop: 200, marginBottom: 200, marginLeft: 'auto', marginRight: 'auto', width: '100%' }} />;
    }

    if (error) {
      return <div>Error: {error}</div>;
    }

    return (
      <>
        <Row>
          <ProductCollection
            title={<Typography.Title level={3} type="warning">{t('products.featured')}</Typography.Title>}
            sideImage="/images/featured-products.jpg"
            products={productList[0]?.touristRoutes || []}
          />
          <ProductCollection
            title={<Typography.Title level={3} type="danger">{t('products.new')}</Typography.Title>}
            sideImage="/images/new-products.jpg"
            products={productList[1]?.touristRoutes || []}
          />
          <ProductCollection
            title={<Typography.Title level={3} type="success">{t('products.popular')}</Typography.Title>}
            sideImage="/images/popular-products.jpg"
            products={productList[2]?.touristRoutes || []}
          />
        </Row>
      </>
    );
  }
}

export const HomePage = withTranslation()(HomePageComponent);
```

### Setting Default Headers

For headers that should be included in every request, you can set them globally in your `index.ts` or `index.js` file:

```typescript
import axios from 'axios';

axios.defaults.headers.common['Accept'] = 'application/json';
axios.defaults.baseURL = 'https://api.example.com/api';
axios.defaults.timeout = 10000; // 10 seconds
```

### Handling Interceptors

Interceptors allow you to run your code or modify the request/response before they are handled by `then` or `catch`. This is useful for adding authorization tokens or logging responses.

```typescript
import axios from 'axios';

// Request Interceptor
axios.interceptors.request.use(
  config => {
    // Modify config before request is sent
    config.headers.Authorization = 'Bearer YOUR_TOKEN';
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response Interceptor
axios.interceptors.response.use(
  response => {
    // With Axios's default validateStatus setting, 2xx responses resolve here.
    return response;
  },
  error => {
    // With the default validateStatus setting, other HTTP statuses reject here.
    if (error.response?.status === 401) {
      // Handle unauthorized error
    }
    return Promise.reject(error);
  }
);
```

## Error Handling

Handling errors properly ensures a better user experience. Here’s an example of how to handle errors with Axios:

```typescript
import axios from 'axios';

axios.get('https://api.example.com/data')
  .then(response => {
    console.log(response.data);
  })
  .catch(error => {
    if (axios.isAxiosError(error)) {
      console.error('Axios error:', error.message);
    } else {
      console.error('Unexpected error:', error);
    }
  });
```

**Reference checked 2026-10-15:** [Axios error handling](https://axios-http.com/docs/handling_errors).
