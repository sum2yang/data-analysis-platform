import { useNavigate } from 'react-router-dom'
import { Select, Dropdown, Badge, Button, Space } from 'antd'
import {
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'
import { useDatasetStore } from '@/store/datasetStore'
import { useTaskStore } from '@/store/taskStore'

export function GlobalHeader() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { datasets, currentDatasetId, setCurrentDataset } = useDatasetStore()
  const { activeTasks, toggleDrawer } = useTaskStore()

  const activeCount = activeTasks().length

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout()
        navigate('/login')
      },
    },
  ]

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
        height: '100%',
        padding: '0 24px',
      }}
    >
      <Space size="large">
        <span style={{ fontSize: 16, fontWeight: 600 }}>
          科研数据分析平台
        </span>
        <Select
          placeholder="选择数据集"
          style={{ width: 220 }}
          value={currentDatasetId}
          onChange={setCurrentDataset}
          options={datasets.map((d) => ({
            label: d.name,
            value: d.id,
          }))}
          allowClear
        />
      </Space>
      <Space>
        <Badge count={activeCount} size="small">
          <Button
            type="text"
            icon={<BellOutlined />}
            onClick={toggleDrawer}
          />
        </Badge>
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Button type="text" icon={<UserOutlined />}>
            {user?.username ?? '用户'}
          </Button>
        </Dropdown>
      </Space>
    </div>
  )
}
