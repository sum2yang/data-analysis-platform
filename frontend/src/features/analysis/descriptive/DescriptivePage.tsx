import { useState } from 'react'
import { message, Row, Col } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { AnalysisForm } from '@/components/AnalysisForm'
import { ResultCard } from '@/components/ResultCard'
import { ResultTable } from '@/components/ResultTable'
import { ColumnSelector } from '@/components/ColumnSelector'
import { submitAnalysis, fetchAnalysisResult } from '../api'
import { usePolling } from '@/hooks/usePolling'
import { useDatasetColumns } from '@/hooks/useDatasetColumns'
import { POLL_INTERVAL } from '@/config/constants'
import type { AnalysisRunDetail } from '../types'

export function DescriptivePage() {
  const { columns, datasetId } = useDatasetColumns()
  const [runId, setRunId] = useState<string | null>(null)
  const [result, setResult] = useState<AnalysisRunDetail | null>(null)
  const [polling, setPolling] = useState(false)

  const submitMutation = useMutation({
    mutationFn: (params: Record<string, unknown>) =>
      submitAnalysis(datasetId!, 'descriptive', params),
    onSuccess: (data) => {
      setRunId(data.run_id)
      setPolling(true)
      message.info('分析任务已提交')
    },
    onError: () => {
      message.error('提交失败')
    },
  })

  usePolling(
    async () => {
      if (!runId) return
      const detail = await fetchAnalysisResult(runId)
      if (detail.status === 'completed' || detail.status === 'failed') {
        setPolling(false)
        setResult(detail)
        if (detail.status === 'completed') {
          message.success('分析完成')
        } else {
          message.error(detail.error_message ?? '分析失败')
        }
      }
    },
    POLL_INTERVAL,
    polling,
  )

  const formFields = [
    {
      name: 'response_column',
      label: '响应变量',
      required: true,
      tooltip: '选择需要统计的数值列',
      component: (
        <ColumnSelector columns={columns} filterType="numeric" multiple={false} placeholder="选择数值列" />
      ),
    },
    {
      name: 'group_column',
      label: '分组变量',
      tooltip: '可选，按此列分组统计',
      component: (
        <ColumnSelector columns={columns} filterType="categorical" multiple={false} placeholder="选择分组列（可选）" />
      ),
    },
  ]

  const tables = result?.result?.tables
    ? Object.entries(result.result.tables).map(([title, data]) => ({
        title,
        columns: data.length > 0 ? Object.keys(data[0] as Record<string, unknown>) : [],
        data: data as Record<string, unknown>[],
      }))
    : []

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="描述统计"
          fields={formFields}
          onSubmit={(values) => submitMutation.mutate(values)}
          loading={submitMutation.isPending || polling}
          disabled={!datasetId}
          disabledReason="请先在顶部选择数据集"
        />
      </Col>
      <Col xs={24} lg={16}>
        {tables.map((table) => (
          <ResultCard key={table.title} title={table.title}>
            <ResultTable result={table} />
          </ResultCard>
        ))}
        {result?.result?.warnings && result.result.warnings.length > 0 && (
          <ResultCard title="警告">
            <ul>
              {result.result.warnings.map((w, i) => (
                <li key={i} style={{ color: '#faad14' }}>{w}</li>
              ))}
            </ul>
          </ResultCard>
        )}
      </Col>
    </Row>
  )
}
