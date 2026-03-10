import { Card, Spin, Empty } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { SmartDataTable } from '@/components/SmartDataTable'
import { fetchDatasetPreview } from './api'

interface DataPreviewProps {
  datasetId: string | null
}

export function DataPreview({ datasetId }: DataPreviewProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['datasetPreview', datasetId],
    queryFn: () => fetchDatasetPreview(datasetId!),
    enabled: !!datasetId,
  })

  if (!datasetId) {
    return (
      <Card title="数据预览">
        <Empty description="请先选择数据集" />
      </Card>
    )
  }

  if (isLoading) {
    return (
      <Card title="数据预览">
        <Spin tip="加载中..." />
      </Card>
    )
  }

  if (!data) {
    return (
      <Card title="数据预览">
        <Empty description="暂无数据" />
      </Card>
    )
  }

  const rows = data.rows.map((row) => {
    const obj: Record<string, unknown> = {}
    data.columns.forEach((col, i) => {
      obj[col] = row[i]
    })
    return obj
  })

  return (
    <Card title={`数据预览 (显示 ${data.total_rows_shown} 行)`}>
      <SmartDataTable columns={data.columns} data={rows} totalRows={data.total_rows_shown} />
    </Card>
  )
}
