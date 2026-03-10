import { useState } from 'react'
import { message, Row, Col } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useDatasetStore } from '@/store/datasetStore'
import { AnalysisForm } from '@/components/AnalysisForm'
import { ResultCard } from '@/components/ResultCard'
import { ResultTable } from '@/components/ResultTable'
import { ColumnSelector } from '@/components/ColumnSelector'
import { submitAnalysis, fetchAnalysisResult } from '../api'
import { usePolling } from '@/hooks/usePolling'
import { POLL_INTERVAL } from '@/config/constants'
import type { AnalysisRunDetail } from '../types'
import type { ColumnInfo } from '@/api/types'

export function AssumptionsPage() {
  const { getCurrentDataset } = useDatasetStore()
  const dataset = getCurrentDataset()
  const [runId, setRunId] = useState<string | null>(null)
  const [result, setResult] = useState<AnalysisRunDetail | null>(null)
  const [polling, setPolling] = useState(false)

  const columns: ColumnInfo[] = dataset
    ? (dataset as unknown as { columns?: ColumnInfo[] }).columns ?? []
    : []

  const submitMutation = useMutation({
    mutationFn: (params: Record<string, unknown>) =>
      submitAnalysis(dataset!.id, 'assumptions', params),
    onSuccess: (data) => {
      setRunId(data.run_id)
      setPolling(true)
      message.info('假设检验任务已提交')
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
          message.success('假设检验完成')
        } else {
          message.error(detail.error_message ?? '检验失败')
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
      component: (
        <ColumnSelector columns={columns} filterType="numeric" multiple={false} placeholder="选择数值列" />
      ),
    },
    {
      name: 'group_column',
      label: '分组变量',
      required: true,
      component: (
        <ColumnSelector columns={columns} filterType="categorical" multiple={false} placeholder="选择分组列" />
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
          title="假设检验"
          fields={formFields}
          onSubmit={(values) => submitMutation.mutate(values)}
          loading={submitMutation.isPending || polling}
          disabled={!dataset}
          disabledReason="请先在顶部选择数据集"
        />
      </Col>
      <Col xs={24} lg={16}>
        {tables.map((table) => (
          <ResultCard key={table.title} title={table.title}>
            <ResultTable result={table} highlightPValue />
          </ResultCard>
        ))}
      </Col>
    </Row>
  )
}
