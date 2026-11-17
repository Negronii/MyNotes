# Ant Design 如何组合布局与菜单组件？

本页把旧课程里的菜单 API 更新为 Ant Design 6.7.0 的 items 写法，保留 Layout、Menu、Typography 与图标组合。Ant Design 是组件库，只负责组件的外观和交互；页面路由、筛选状态和表单语义仍由应用代码和 HTML 决定。

~~~tsx
import { Layout, Menu, Typography, type MenuProps } from "antd";
import { GlobalOutlined } from "@ant-design/icons";

const menuItems: MenuProps["items"] = [
  { key: "reports", icon: <GlobalOutlined />, label: "报表" },
  { key: "settings", label: "设置" },
];

export function ReportsShell() {
  return (
    <Layout>
      <Layout.Header>
        <Menu
          mode="horizontal"
          theme="dark"
          selectedKeys={["reports"]}
          items={menuItems}
        />
      </Layout.Header>
      <Layout.Content style={{ padding: "0 32px" }}>
        <Typography.Title level={2}>月度报表</Typography.Title>
        <p>此处放置路由页面内容。</p>
      </Layout.Content>
      <Layout.Footer>报表服务</Layout.Footer>
    </Layout>
  );
}
~~~

每个菜单项用稳定的 `key` 标识，`selectedKeys` 表示当前选中项；真实导航应由路由状态计算它，而不是写死数组。旧课程里用 `<Menu.Item>` 子元素声明菜单的写法，自 4.20.0 起被 `items` 取代并标为弃用；6.x 中它仍能运行，但会在控制台给出弃用警告，新代码应改用 `items`。`@ant-design/icons` 的主版本也应与 antd 主版本保持一致（6.x 配 6.x）。

> [!info]- 来源
> - 当前菜单的 items、selectedKeys 与 MenuItem 属性：[Ant Design Menu](https://ant.design/components/menu/)，Ant Design 6.7.0 文档，核对日期：2026-11-06。
> - Layout 的 Header、Content、Footer 结构：[Ant Design Layout](https://ant.design/components/layout/)，Ant Design 6.7.0 文档，核对日期：2026-11-06。
> - Menu `items` 自 4.20.0 引入、子元素写法弃用：[Ant Design 4.x Menu](https://4x.ant.design/components/menu)；6.x 中弃用 API 仍可用但会警告：[Ant Design 6 Migration Guide](https://ant.design/docs/react/migration-v6/)，核对日期：2026-11-17。
> - 图标包主版本匹配：[Ant Design 6 Migration Guide](https://ant.design/docs/react/migration-v6/)，Ant Design 6.7.0 文档，核对日期：2026-11-06。
