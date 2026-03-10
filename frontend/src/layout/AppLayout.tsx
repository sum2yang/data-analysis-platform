import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Layout } from 'antd'
import { AppSidebar } from './AppSidebar'
import { GlobalHeader } from './GlobalHeader'

const { Header, Sider, Content } = Layout

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: 0,
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <GlobalHeader />
      </Header>
      <Layout>
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          width={200}
          style={{ borderRight: '1px solid #f0f0f0' }}
        >
          <AppSidebar />
        </Sider>
        <Content style={{ padding: 24, overflow: 'auto' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
