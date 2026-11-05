# How does the archived Ant Design example assemble React components? / 归档中的 Ant Design 示例如何组合 React 组件？

The archived example uses Ant Design layout, menu, typography, input, button, and dropdown components. Pin the package version and check the installed component API before reuse. / 归档示例使用 Ant Design 布局、菜单、排版、输入框、按钮和下拉组件。复用前应固定依赖版本，并核对项目实际 API。

## Using Ant Design

### Overview
Ant Design is a React component library. The examples below use its Layout, Menu, Typography, and icon components; component APIs can differ between Ant Design versions, so pin the package version used by the application.

### Installation
To use Ant Design, you need to install the core library along with the icons package. Run the following command to install both:
```bash
npm install antd @ant-design/icons
```

### Using Components
After installation, you can start using Ant Design components in your project. Here is a basic example demonstrating the use of the `Layout`, `Typography`, `Input`, `Menu`, `Button`, and `Dropdown` components.

#### Example
```tsx
// src/components/Header.tsx
import React from 'react';
import { Layout, Menu } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';

const { Header } = Layout;

const AppHeader: React.FC = () => (
  <Header>
    <div className="logo" />
    <Menu theme="dark" mode="horizontal" defaultSelectedKeys={['1']}>
      <Menu.Item key="1" icon={<GlobalOutlined />}>Home</Menu.Item>
      <Menu.Item key="2">About</Menu.Item>
      <Menu.Item key="3">Contact</Menu.Item>
    </Menu>
  </Header>
);

export default AppHeader;
```

#### Integrating Ant Design in `App.tsx`
```tsx
// src/components/App.tsx
import React from 'react';
import { Layout, Typography } from 'antd';
import AppHeader from './header/Header';
import AppFooter from './footer/Footer';

const { Content } = Layout;
const { Title } = Typography;

const App: React.FC = () => (
  <Layout>
    <AppHeader />
    <Content style={{ padding: '0 50px' }}>
      <Title level={2}>Welcome to My App</Title>
      <p>This is a simple example of using Ant Design with React.</p>
    </Content>
    <AppFooter />
  </Layout>
);

export default App;
```

### Exploring Ant Design Components
For more examples and detailed documentation on how to use different Ant Design components, visit the [Ant Design Components Overview](https://ant.design/components/overview).

### Best Practices
- **Consistent Use of Ant Design Components:** Ensure consistency in design by leveraging Ant Design components across the application.
- **Theming and Customization:** Use Ant Design's theming capabilities to customize the appearance to match your brand.
- **Responsive Design:** Utilize the responsive grid system and other responsive components to ensure your application works well on different screen sizes.
