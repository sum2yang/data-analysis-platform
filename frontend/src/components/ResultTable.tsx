import { Table, Tooltip } from 'antd'
import type { TableResult } from '@/api/types'
import { useMemo } from 'react'
import { COLUMN_LABEL_MAP } from '@/config/constants'

interface ResultTableProps {
  result: TableResult
  highlightPValue?: boolean
}

function formatPValue(val: unknown): { text: string; style: React.CSSProperties } {
  if (typeof val !== 'number') return { text: String(val ?? ''), style: {} }
  if (val < 0.001) return { text: '< 0.001 ***', style: { color: '#f5222d', fontWeight: 'bold' } }
  if (val < 0.01) return { text: `${val.toFixed(4)} **`, style: { color: '#f5222d', fontWeight: 'bold' } }
  if (val < 0.05) return { text: `${val.toFixed(4)} *`, style: { color: '#fa8c16' } }
  return { text: val.toFixed(4), style: {} }
}

function isPColumn(col: string): boolean {
  return /p[_\s-]?val/i.test(col) || col.toLowerCase() === 'p'
}

export function ResultTable({ result, highlightPValue = true }: ResultTableProps) {
  const pColumns = useMemo(
    () => new Set(result.columns.filter(isPColumn)),
    [result.columns],
  )

  const columns = result.columns.map((col) => ({
    title: (
      <Tooltip title={col} placement="top">
        <span>{COLUMN_LABEL_MAP[col] || col}</span>
      </Tooltip>
    ),
    dataIndex: col,
    key: col,
    render: (value: unknown) => {
      if (highlightPValue && pColumns.has(col)) {
        const { text, style } = formatPValue(value)
        return <span style={style}>{text}</span>
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
