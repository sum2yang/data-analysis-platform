import { useState } from 'react'
import { Row, Col, Input, message, Empty } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { ChartPanel } from './ChartPanel'
import { ExportCenter } from './ExportCenter'
import { fetchChartContracts } from './api'

const { Search } = Input

export function VisPage() {
  const [runId, setRunId] = useState<string>('')
  const [searchId, setSearchId] = useState<string | null>(null)

  const { data: contracts, isLoading } = useQuery({
    queryKey: ['chartContracts', searchId],
    queryFn: () => fetchChartContracts(searchId!),
    enabled: !!searchId,
  })

  const tableNames =
    contracts?.flatMap((c) =>
      Object.keys(c.metadata).filter((k) => k.startsWith('table_')),
    ) ?? []

  return (
    <div>
      <Search
        placeholder="输入分析运行 ID 查看图表"
        enterButton="查看图表"
        value={runId}
        onChange={(e) => setRunId(e.target.value)}
        onSearch={(val) => {
          if (!val.trim()) {
            message.warning('请输入运行 ID')
            return
          }
          setSearchId(val.trim())
        }}
        style={{ maxWidth: 500, marginBottom: 16 }}
      />
      <Row gutter={16}>
        <Col xs={24} lg={18}>
          {searchId ? (
            <ChartPanel contracts={contracts ?? []} loading={isLoading} />
          ) : (
            <Empty description="输入分析运行 ID 查看对应图表" />
          )}
        </Col>
        <Col xs={24} lg={6}>
          <ExportCenter runId={searchId} tableNames={tableNames} />
        </Col>
      </Row>
    </div>
  )
}
