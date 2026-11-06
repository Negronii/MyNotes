# Ant Design 如何组合布局与菜单组件？

本页把旧课程里的菜单 API 更新为 Ant Design 6.7.0 的 items 写法，保留 Layout、Menu、Typography 与图标组合。Ant Design 是组件库，组件负责呈现和交互外观；页面路由、筛选状态与表单语义仍由应用和 HTML 契约决定。

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

菜单项目通过稳定 key 标识，selectedKeys 表达当前选中状态；真实导航应让路由状态驱动它，而不只是写死数组。旧版 Menu.Item 写法只在其对应的 Ant Design 版本范围内维护。6.x 图标包也应与 antd 主版本一致。

> [!info]- 来源
> - 当前菜单的 items、selectedKeys 与 MenuItem 属性：[Ant Design Menu](https://ant.design/components/menu/)，Ant Design 6.7.0 文档，核对日期：2026-11-06。
> - Layout 的 Header、Content、Footer 结构：[Ant Design Layout](https://ant.design/components/layout/)，Ant Design 6.7.0 文档，核对日期：2026-11-06。
> - 图标包主版本匹配：[Ant Design 6 Migration Guide](https://ant.design/docs/react/migration-v6/)，Ant Design 6.7.0 文档，核对日期：2026-11-06。
