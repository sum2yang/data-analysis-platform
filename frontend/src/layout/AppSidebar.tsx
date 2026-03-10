import { useNavigate, useLocation } from 'react-router-dom'
import { Menu } from 'antd'
import {
  DatabaseOutlined,
  BarChartOutlined,
  SwapOutlined,
  DotChartOutlined,
  ClusterOutlined,
  PieChartOutlined,
} from '@ant-design/icons'

const menuItems = [
  {
    key: '/data',
    icon: <DatabaseOutlined />,
    label: '数据管理',
  },
  {
    key: '/analysis/descriptive',
    icon: <BarChartOutlined />,
    label: '统计描述',
  },
  {
    key: '/analysis/difference',
    icon: <SwapOutlined />,
    label: '差异分析',
  },
  {
    key: '/analysis/correlation',
    icon: <DotChartOutlined />,
    label: '相关回归',
  },
  {
    key: '/analysis/ordination',
    icon: <ClusterOutlined />,
    label: '排序分析',
  },
  {
    key: '/visualization',
    icon: <PieChartOutlined />,
    label: '可视化中心',
  },
]

export function AppSidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  const selectedKeys = menuItems
    .filter((item) => location.pathname.startsWith(item.key))
    .map((item) => item.key)

  return (
    <Menu
      mode="inline"
      selectedKeys={selectedKeys}
      items={menuItems}
      onClick={({ key }) => navigate(key)}
      style={{ height: '100%', borderRight: 0 }}
    />
  )
}
