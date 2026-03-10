import { Card, Space, Button, Dropdown } from 'antd'
import { DownloadOutlined, TableOutlined, BarChartOutlined } from '@ant-design/icons'
import type { ReactNode } from 'react'

interface ResultCardProps {
  title: string
  children: ReactNode
  extra?: ReactNode
  onExportTable?: () => void
  onExportChart?: () => void
  loading?: boolean
}

export function ResultCard({
  title,
  children,
  extra,
  onExportTable,
  onExportChart,
  loading = false,
}: ResultCardProps) {
  const exportItems = [
    onExportTable && {
      key: 'table',
      icon: <TableOutlined />,
      label: '导出表格 (CSV)',
      onClick: onExportTable,
    },
    onExportChart && {
      key: 'chart',
      icon: <BarChartOutlined />,
      label: '导出图表 (PNG)',
      onClick: onExportChart,
    },
  ].filter(Boolean) as { key: string; icon: ReactNode; label: string; onClick: () => void }[]

  return (
    <Card
      title={title}
      loading={loading}
      extra={
        <Space>
          {extra}
          {exportItems.length > 0 && (
            <Dropdown menu={{ items: exportItems }} placement="bottomRight">
              <Button size="small" icon={<DownloadOutlined />}>
                导出
              </Button>
            </Dropdown>
          )}
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      {children}
    </Card>
  )
}
