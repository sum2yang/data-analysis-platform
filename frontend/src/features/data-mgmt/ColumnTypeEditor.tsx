import { Card, Table, Select, Button, message, Empty } from 'antd'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchDatasetProfile, updateColumnTypes } from './api'
import type { ColumnTypeUpdate } from './types'

const dtypeOptions = [
  { label: '数值 (float)', value: 'float64' },
  { label: '整数 (int)', value: 'int64' },
  { label: '文本 (string)', value: 'object' },
  { label: '分类 (category)', value: 'category' },
  { label: '日期 (datetime)', value: 'datetime64' },
  { label: '布尔 (bool)', value: 'bool' },
]

interface ColumnTypeEditorProps {
  datasetId: string | null
}

export function ColumnTypeEditor({ datasetId }: ColumnTypeEditorProps) {
  const queryClient = useQueryClient()
  const [changes, setChanges] = useState<Record<string, string>>({})

  const { data: profile, isLoading } = useQuery({
    queryKey: ['datasetProfile', datasetId],
    queryFn: () => fetchDatasetProfile(datasetId!),
    enabled: !!datasetId,
  })

  const updateMutation = useMutation({
    mutationFn: (updates: ColumnTypeUpdate[]) => updateColumnTypes(datasetId!, updates),
    onSuccess: () => {
      message.success('列类型更新成功')
      setChanges({})
      queryClient.invalidateQueries({ queryKey: ['datasetProfile', datasetId] })
      queryClient.invalidateQueries({ queryKey: ['datasetPreview', datasetId] })
    },
    onError: () => {
      message.error('列类型更新失败')
    },
  })

  if (!datasetId) {
    return (
      <Card title="列类型编辑">
        <Empty description="请先选择数据集" />
      </Card>
    )
  }

  const columnsData = profile
    ? Object.entries(profile.columns).map(([name, info]) => ({
        name,
        ...(info as Record<string, unknown>),
      }))
    : []

  const handleApply = () => {
    const updates = Object.entries(changes).map(([column, new_dtype]) => ({
      column,
      new_dtype,
    }))
    if (updates.length === 0) {
      message.warning('没有修改')
      return
    }
    updateMutation.mutate(updates)
  }

  return (
    <Card
      title="列类型编辑"
      extra={
        Object.keys(changes).length > 0 && (
          <Button type="primary" size="small" onClick={handleApply} loading={updateMutation.isPending}>
            应用修改 ({Object.keys(changes).length})
          </Button>
        )
      }
    >
      <Table
        loading={isLoading}
        dataSource={columnsData}
        rowKey="name"
        size="small"
        pagination={false}
        columns={[
          { title: '列名', dataIndex: 'name', key: 'name' },
          {
            title: '当前类型',
            dataIndex: 'dtype',
            key: 'dtype',
            render: (v: string) => <code>{v}</code>,
          },
          {
            title: '修改为',
            key: 'newType',
            width: 200,
            render: (_: unknown, record: { name: string; dtype: string }) => (
              <Select
                size="small"
                options={dtypeOptions}
                value={changes[record.name]}
                placeholder="不修改"
                onChange={(val) =>
                  setChanges((prev) => {
                    if (!val) {
                      const next = { ...prev }
                      delete next[record.name]
                      return next
                    }
                    return { ...prev, [record.name]: val }
                  })
                }
                allowClear
                style={{ width: '100%' }}
              />
            ),
          },
        ]}
      />
    </Card>
  )
}
