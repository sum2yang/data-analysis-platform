import { Table } from 'antd'
import type { TableResult } from '@/api/types'
import { useMemo } from 'react'

interface ResultTableProps {
  result: TableResult
  highlightPValue?: boolean
}

function formatPValue(val: unknown): { text: string; color?: string } {
  if (typeof val !== 'number') return { text: String(val ?? '') }
  if (val < 0.001) return { text: '< 0.001', color: '#ff4d4f' }
  if (val < 0.01) return { text: val.toFixed(3), color: '#ff7a45' }
  if (val < 0.05) return { text: val.toFixed(3), color: '#ffa940' }
  return { text: val.toFixed(3) }
}

export function ResultTable({ result, highlightPValue = true }: ResultTableProps) {
  const pColumns = useMemo(
    () => new Set(result.columns.filter((c) => /p[_\s-]?val/i.test(c) || c.toLowerCase() === 'p')),
    [result.columns],
  )

  const columns = result.columns.map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    render: (value: unknown) => {
      if (highlightPValue && pColumns.has(col)) {
        const { text, color } = formatPValue(value)
        return <span style={{ color, fontWeight: color ? 600 : undefined }}>{text}</span>
      }
      if (typeof value === 'number') {
        return (
          <span style={{ fontFamily: '"Cascadia Code", "Fira Code", monospace' }}>
            {Number.isInteger(value) ? value : value.toFixed(4)}
          </span>
        )
      }
      if (value === null || value === undefined) {
        return <span style={{ color: '#bfbfbf' }}>-</span>
      }
      return String(value)
    },
  }))

  return (
    <Table
      columns={columns}
      dataSource={result.data.map((row, i) => ({ ...row, _key: i }))}
      rowKey="_key"
      size="small"
      bordered
      pagination={result.data.length > 20 ? { pageSize: 20 } : false}
    />
  )
}
