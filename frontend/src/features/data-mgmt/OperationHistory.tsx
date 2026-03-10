import { Card, Timeline, Empty } from 'antd'

interface Operation {
  type: string
  timestamp: string
  details?: string
}

interface OperationHistoryProps {
  operations: Operation[]
}

const operationLabels: Record<string, string> = {
  upload: '上传',
  join: '合并',
  clean: '清洗',
  type_change: '类型修改',
  drop_na: '删除缺失值',
  fill_na: '填充缺失值',
  drop_duplicates: '删除重复行',
  rename: '重命名',
  drop_columns: '删除列',
  change_type: '类型转换',
}

export function OperationHistory({ operations }: OperationHistoryProps) {
  if (operations.length === 0) {
    return (
      <Card title="操作历史">
        <Empty description="暂无操作记录" />
      </Card>
    )
  }

  return (
    <Card title="操作历史">
      <Timeline
        items={operations.map((op, i) => ({
          key: i,
          children: (
            <div>
              <strong>{operationLabels[op.type] ?? op.type}</strong>
              <br />
              <span style={{ color: '#8c8c8c', fontSize: 12 }}>{op.timestamp}</span>
              {op.details && (
                <>
                  <br />
                  <span style={{ fontSize: 12 }}>{op.details}</span>
                </>
              )}
            </div>
          ),
        }))}
      />
    </Card>
  )
}
