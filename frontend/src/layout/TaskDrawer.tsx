import { Drawer, List, Tag, Progress, Empty } from 'antd'
import { useTaskStore } from '@/store/taskStore'
import type { TaskInfo } from '@/api/types'

const statusConfig: Record<
  TaskInfo['status'],
  { color: string; label: string }
> = {
  pending: { color: 'default', label: '等待中' },
  running: { color: 'processing', label: '运行中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '已失败' },
}

export function TaskDrawer() {
  const { tasks, drawerOpen, setDrawerOpen } = useTaskStore()

  return (
    <Drawer
      title="后台任务"
      open={drawerOpen}
      onClose={() => setDrawerOpen(false)}
      width={360}
    >
      {tasks.length === 0 ? (
        <Empty description="暂无任务" />
      ) : (
        <List
          dataSource={tasks}
          renderItem={(task) => {
            const cfg = statusConfig[task.status]
            return (
              <List.Item>
                <List.Item.Meta
                  title={
                    <span>
                      {task.type} <Tag color={cfg.color}>{cfg.label}</Tag>
                    </span>
                  }
                  description={
                    task.status === 'running' ? (
                      <Progress percent={task.progress} size="small" />
                    ) : task.status === 'failed' ? (
                      <span style={{ color: '#ff4d4f' }}>{task.error}</span>
                    ) : null
                  }
                />
              </List.Item>
            )
          }}
        />
      )}
    </Drawer>
  )
}
