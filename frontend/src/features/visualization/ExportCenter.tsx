import { Card, Button, Space, Select, message } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { exportChart, exportTable } from './api'

interface ExportCenterProps {
  runId: string | null
  tableNames: string[]
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function ExportCenter({ runId, tableNames }: ExportCenterProps) {
  const [chartFormat, setChartFormat] = useState<'png' | 'svg' | 'pdf'>('png')
  const [tableFormat, setTableFormat] = useState<'csv' | 'xlsx'>('csv')
  const [selectedTable, setSelectedTable] = useState<string | undefined>(tableNames[0])

  useEffect(() => {
    if (tableNames.length > 0 && !tableNames.includes(selectedTable ?? '')) {
      setSelectedTable(tableNames[0])
    }
  }, [tableNames, selectedTable])

  const chartExportMutation = useMutation({
    mutationFn: () =>
      exportChart({ run_id: runId!, format: chartFormat, dpi: 300 }),
    onSuccess: (blob) => {
      downloadBlob(blob, `chart.${chartFormat}`)
      message.success('图表导出成功')
    },
    onError: () => message.error('图表导出失败'),
  })

  const tableExportMutation = useMutation({
    mutationFn: () => {
      if (!runId || !selectedTable) throw new Error('Missing runId or table')
      return exportTable(runId, selectedTable, tableFormat)
    },
    onSuccess: (blob) => {
      downloadBlob(blob, `${selectedTable}.${tableFormat}`)
      message.success('表格导出成功')
    },
    onError: () => message.error('表格导出失败'),
  })

  if (!runId) return null

  return (
    <Card title="导出中心" size="small">
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space>
          <Select
            value={chartFormat}
            onChange={setChartFormat}
            options={[
              { label: 'PNG', value: 'png' },
              { label: 'SVG', value: 'svg' },
              { label: 'PDF', value: 'pdf' },
            ]}
            style={{ width: 100 }}
          />
          <Button
            icon={<DownloadOutlined />}
            onClick={() => chartExportMutation.mutate()}
            loading={chartExportMutation.isPending}
          >
            导出图表
          </Button>
        </Space>
        {tableNames.length > 0 && (
          <Space>
            <Select
              value={selectedTable}
              onChange={setSelectedTable}
              options={tableNames.map((n) => ({ label: n, value: n }))}
              style={{ width: 150 }}
            />
            <Select
              value={tableFormat}
              onChange={setTableFormat}
              options={[
                { label: 'CSV', value: 'csv' },
                { label: 'XLSX', value: 'xlsx' },
              ]}
              style={{ width: 100 }}
            />
            <Button
              icon={<DownloadOutlined />}
              onClick={() => tableExportMutation.mutate()}
              loading={tableExportMutation.isPending}
            >
              导出表格
            </Button>
          </Space>
        )}
      </Space>
    </Card>
  )
}
