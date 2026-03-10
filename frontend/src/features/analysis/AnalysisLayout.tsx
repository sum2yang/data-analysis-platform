import { Tabs } from 'antd'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const tabItems = [
  { key: '/analysis/descriptive', label: '描述统计' },
  { key: '/analysis/difference', label: '差异分析' },
]

export function AnalysisLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div>
      <Tabs
        activeKey={location.pathname}
        onChange={(key) => navigate(key)}
        items={tabItems}
        style={{ marginBottom: 16 }}
      />
      <Outlet />
    </div>
  )
}
