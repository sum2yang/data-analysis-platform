import { useMemo } from 'react'
import { Select, Tag, Space } from 'antd'
import type { ColumnInfo } from '@/api/types'

interface ColumnSelectorProps {
  columns: ColumnInfo[]
  value?: string[]
  onChange?: (selected: string[]) => void
  filterType?: ColumnInfo['dtype'] | ColumnInfo['dtype'][]
  multiple?: boolean
  placeholder?: string
  style?: React.CSSProperties
}

const dtypeColor: Record<ColumnInfo['dtype'], string> = {
  numeric: 'blue',
  categorical: 'green',
  datetime: 'orange',
  text: 'default',
}

const dtypeLabel: Record<ColumnInfo['dtype'], string> = {
  numeric: '数值',
  categorical: '分类',
  datetime: '日期',
  text: '文本',
}

export function ColumnSelector({
  columns,
  value,
  onChange,
  filterType,
  multiple = true,
  placeholder = '选择列',
  style,
}: ColumnSelectorProps) {
  const filteredColumns = useMemo(() => {
    if (!filterType) return columns
    const types = Array.isArray(filterType) ? filterType : [filterType]
    return columns.filter((c) => types.includes(c.dtype))
  }, [columns, filterType])

  const options = filteredColumns.map((col) => ({
    label: (
      <Space size={4}>
        <span>{col.name}</span>
        <Tag color={dtypeColor[col.dtype]} style={{ marginRight: 0, fontSize: 11 }}>
          {dtypeLabel[col.dtype]}
        </Tag>
      </Space>
    ),
    value: col.name,
  }))

  return (
    <Select
      mode={multiple ? 'multiple' : undefined}
      value={value}
      onChange={onChange}
      options={options}
      placeholder={placeholder}
      style={{ width: '100%', ...style }}
      allowClear
      showSearch
      filterOption={(input, option) =>
        typeof option?.value === 'string' && option.value.toLowerCase().includes(input.toLowerCase())
      }
    />
  )
}
