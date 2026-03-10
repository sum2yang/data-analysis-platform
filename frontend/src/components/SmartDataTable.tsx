import { useMemo } from 'react'
import { Table } from 'antd'
import type { TableProps } from 'antd'
import { VIRTUAL_TABLE_THRESHOLD } from '@/config/constants'

interface SmartDataTableProps<T extends Record<string, unknown>> {
  columns: string[]
  data: T[]
  totalRows?: number
  loading?: boolean
  scroll?: TableProps<T>['scroll']
}

function isNumeric(value: unknown): boolean {
  return typeof value === 'number' || (typeof value === 'string' && !isNaN(Number(value)) && value.trim() !== '')
}

export function SmartDataTable<T extends Record<string, unknown>>({
  columns,
  data,
  totalRows,
  loading = false,
  scroll,
}: SmartDataTableProps<T>) {
  const useVirtual = (totalRows ?? data.length) > VIRTUAL_TABLE_THRESHOLD

  const tableColumns = useMemo(
    () =>
      columns.map((col) => ({
        title: col,
        dataIndex: col,
        key: col,
        ellipsis: true,
        width: 150,
        render: (value: unknown) => {
          if (value === null || value === undefined) {
            return <span style={{ color: '#bfbfbf' }}>NA</span>
          }
          if (isNumeric(value)) {
            return <span style={{ fontFamily: '"Cascadia Code", "Fira Code", monospace' }}>{String(value)}</span>
          }
          return String(value)
        },
      })),
    [columns],
  )

  const dataSource = useMemo(
    () => data.map((row, i) => ({ ...row, _rowKey: i })),
    [data],
  )

  return (
    <Table
      columns={tableColumns}
      dataSource={dataSource}
      rowKey="_rowKey"
      loading={loading}
      size="small"
      bordered
      pagination={
        useVirtual
          ? { pageSize: 50, showSizeChanger: true, showTotal: (t) => `共 ${t} 行` }
          : false
      }
      scroll={scroll ?? { x: columns.length * 150 }}
      virtual={useVirtual}
    />
  )
}
