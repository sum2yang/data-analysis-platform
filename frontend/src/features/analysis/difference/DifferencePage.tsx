import { useState } from 'react'
import { Tabs, Select, InputNumber, Switch, message, Row, Col } from 'antd'
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
import type { ColumnInfo } from '@/api/types'

function useAnalysisSubmit(
  datasetId: string | undefined,
  analysisType: string,
  setRunId: (id: string) => void,
  setPolling: (v: boolean) => void,
) {
  return useMutation({
    mutationFn: (params: Record<string, unknown>) =>
      submitAnalysis(datasetId!, analysisType, params),
    onSuccess: (data) => {
      setRunId(data.run_id)
      setPolling(true)
      message.info('分析任务已提交')
    },
    onError: () => {
      message.error('提交失败')
    },
  })
}

function useAnalysisPolling(
  runId: string | null,
  polling: boolean,
  setPolling: (v: boolean) => void,
  setResult: (r: AnalysisRunDetail) => void,
) {
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
}

function AnalysisResults({ result }: { result: AnalysisRunDetail | null }) {
  const tables = result?.result?.tables
    ? Object.entries(result.result.tables).map(([title, data]) => ({
        title,
        columns: data.length > 0 ? Object.keys(data[0] as Record<string, unknown>) : [],
        data: data as Record<string, unknown>[],
      }))
    : []

  return (
    <>
      {tables.map((table) => (
        <ResultCard key={table.title} title={table.title}>
          <ResultTable result={table} highlightPValue />
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
    </>
  )
}

function TTestTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const [runId, setRunId] = useState<string | null>(null)
  const [result, setResult] = useState<AnalysisRunDetail | null>(null)
  const [polling, setPolling] = useState(false)

  const submitMutation = useAnalysisSubmit(datasetId, 't_test', setRunId, setPolling)
  useAnalysisPolling(runId, polling, setPolling, setResult)

  const fields = [
    {
      name: 'response_column',
      label: '响应变量',
      required: true,
      component: <ColumnSelector columns={columns} filterType="numeric" multiple={false} placeholder="选择数值列" />,
    },
    {
      name: 'mode',
      label: '检验类型',
      required: true,
      component: (
        <Select
          options={[
            { label: '独立样本 t 检验', value: 'independent' },
            { label: '配对样本 t 检验', value: 'paired' },
            { label: '单样本 t 检验', value: 'one_sample' },
          ]}
          placeholder="选择检验类型"
        />
      ),
    },
    {
      name: 'group_column',
      label: '分组变量',
      tooltip: '独立/配对样本时必填',
      component: <ColumnSelector columns={columns} filterType="categorical" multiple={false} placeholder="选择分组列" />,
    },
    {
      name: 'alternative',
      label: '备择假设',
      component: (
        <Select
          defaultValue="two.sided"
          options={[
            { label: '双侧', value: 'two.sided' },
            { label: '大于', value: 'greater' },
            { label: '小于', value: 'less' },
          ]}
        />
      ),
    },
    {
      name: 'mu',
      label: '假设均值 (mu)',
      tooltip: '单样本检验时的假设均值',
      component: <InputNumber defaultValue={0} style={{ width: '100%' }} />,
    },
    {
      name: 'var_equal',
      label: '方差齐性假设',
      tooltip: '是否假设两组方差相等',
      component: <Switch defaultChecked />,
    },
    {
      name: 'conf_level',
      label: '置信水平',
      component: <InputNumber defaultValue={0.95} min={0.5} max={0.999} step={0.01} style={{ width: '100%' }} />,
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="t 检验"
          fields={fields}
          onSubmit={(values) => submitMutation.mutate(values)}
          loading={submitMutation.isPending || polling}
          disabled={!datasetId}
          disabledReason="请先在顶部选择数据集"
        />
      </Col>
      <Col xs={24} lg={16}>
        <AnalysisResults result={result} />
      </Col>
    </Row>
  )
}

function AnovaTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const [runId, setRunId] = useState<string | null>(null)
  const [result, setResult] = useState<AnalysisRunDetail | null>(null)
  const [polling, setPolling] = useState(false)

  const submitMutation = useAnalysisSubmit(datasetId, 'anova', setRunId, setPolling)
  useAnalysisPolling(runId, polling, setPolling, setResult)

  const fields = [
    {
      name: 'response_column',
      label: '响应变量',
      required: true,
      component: <ColumnSelector columns={columns} filterType="numeric" multiple={false} placeholder="选择数值列" />,
    },
    {
      name: 'group_column',
      label: '分组变量',
      required: true,
      component: <ColumnSelector columns={columns} filterType="categorical" multiple={false} placeholder="选择分组列" />,
    },
    {
      name: 'posthoc',
      label: '事后检验',
      component: (
        <Select
          defaultValue="tukey"
          options={[
            { label: 'Tukey HSD', value: 'tukey' },
            { label: 'Duncan', value: 'duncan' },
            { label: 'LSD', value: 'lsd' },
          ]}
        />
      ),
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="方差分析 (ANOVA)"
          fields={fields}
          onSubmit={(values) => submitMutation.mutate(values)}
          loading={submitMutation.isPending || polling}
          disabled={!datasetId}
          disabledReason="请先在顶部选择数据集"
        />
      </Col>
      <Col xs={24} lg={16}>
        <AnalysisResults result={result} />
      </Col>
    </Row>
  )
}

function NonParametricTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const [runId, setRunId] = useState<string | null>(null)
  const [result, setResult] = useState<AnalysisRunDetail | null>(null)
  const [polling, setPolling] = useState(false)

  const submitMutation = useAnalysisSubmit(datasetId, 'nonparametric', setRunId, setPolling)
  useAnalysisPolling(runId, polling, setPolling, setResult)

  const fields = [
    {
      name: 'response_column',
      label: '响应变量',
      required: true,
      component: <ColumnSelector columns={columns} filterType="numeric" multiple={false} placeholder="选择数值列" />,
    },
    {
      name: 'group_column',
      label: '分组变量',
      required: true,
      component: <ColumnSelector columns={columns} filterType="categorical" multiple={false} placeholder="选择分组列" />,
    },
    {
      name: 'test',
      label: '检验方法',
      required: true,
      component: (
        <Select
          options={[
            { label: 'Mann-Whitney U 检验', value: 'mann_whitney' },
            { label: 'Kruskal-Wallis 检验', value: 'kruskal_wallis' },
            { label: 'Wilcoxon 符号秩检验', value: 'wilcoxon' },
          ]}
          placeholder="选择检验方法"
        />
      ),
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="非参数检验"
          fields={fields}
          onSubmit={(values) => submitMutation.mutate(values)}
          loading={submitMutation.isPending || polling}
          disabled={!datasetId}
          disabledReason="请先在顶部选择数据集"
        />
      </Col>
      <Col xs={24} lg={16}>
        <AnalysisResults result={result} />
      </Col>
    </Row>
  )
}

export function DifferencePage() {
  const { columns, datasetId } = useDatasetColumns()

  const tabItems = [
    {
      key: 'ttest',
      label: 't 检验',
      children: <TTestTab columns={columns} datasetId={datasetId ?? undefined} />,
    },
    {
      key: 'anova',
      label: 'ANOVA',
      children: <AnovaTab columns={columns} datasetId={datasetId ?? undefined} />,
    },
    {
      key: 'nonparametric',
      label: '非参数检验',
      children: <NonParametricTab columns={columns} datasetId={datasetId ?? undefined} />,
    },
  ]

  return <Tabs defaultActiveKey="ttest" items={tabItems} />
}
