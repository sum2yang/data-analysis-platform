import { useState } from 'react'
import { Select, message, Row, Col, Tabs } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useDatasetColumns } from '@/hooks/useDatasetColumns'
import { AnalysisForm } from '@/components/AnalysisForm'
import { AnalysisResults } from '@/components/AnalysisResults'
import { ColumnSelector } from '@/components/ColumnSelector'
import { submitAnalysis } from '../api'
import { useAnalysis, useAnalysisPolling } from '@/hooks/useAnalysis'
import type { ColumnInfo } from '@/api/types'

function CorrelationTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const { submitMutation, result, polling } = useAnalysis(datasetId, 'correlation')

  const fields = [
    {
      name: 'columns',
      label: '选择变量',
      required: true,
      tooltip: '至少选择2个数值变量',
      component: <ColumnSelector columns={columns} filterType="numeric" placeholder="选择数值列（多选）" />,
    },
    {
      name: 'method',
      label: '相关系数方法',
      component: (
        <Select
          defaultValue="pearson"
          options={[
            { label: 'Pearson', value: 'pearson' },
            { label: 'Spearman', value: 'spearman' },
          ]}
        />
      ),
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="相关分析"
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

function RegressionTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const [selectedMethod, setSelectedMethod] = useState<string>('lm')
  const { setRunId, result, polling, setPolling } = useAnalysisPolling()

  const submitMutation = useMutation({
    mutationFn: (params: Record<string, unknown>) => {
      const analysisType = selectedMethod === 'lm' ? 'regression_linear' : 'regression_glm'
      const { method: _method, ...cleanParams } = params
      return submitAnalysis(datasetId!, analysisType, cleanParams)
    },
    onSuccess: (data) => {
      setRunId(data.run_id)
      setPolling(true)
      message.info('回归分析任务已提交')
    },
    onError: () => message.error('提交失败'),
  })

  const fields = [
    {
      name: 'response_column',
      label: '因变量 (Y)',
      required: true,
      component: <ColumnSelector columns={columns} filterType="numeric" multiple={false} placeholder="选择因变量" />,
    },
    {
      name: 'predictor_columns',
      label: '自变量 (X)',
      required: true,
      tooltip: '选择一个或多个自变量',
      component: <ColumnSelector columns={columns} filterType="numeric" placeholder="选择自变量（多选）" />,
    },
    {
      name: 'method',
      label: '回归方法',
      component: (
        <Select
          value={selectedMethod}
          onChange={setSelectedMethod}
          options={[
            { label: '线性回归 (lm)', value: 'lm' },
            { label: 'GLM (glm)', value: 'glm' },
          ]}
        />
      ),
    },
    {
      name: 'family',
      label: 'GLM 分布族',
      tooltip: '仅 GLM 方法时生效',
      component: (
        <Select
          defaultValue="gaussian"
          options={[
            { label: 'gaussian', value: 'gaussian' },
            { label: 'binomial', value: 'binomial' },
            { label: 'poisson', value: 'poisson' },
            { label: 'Gamma', value: 'Gamma' },
          ]}
        />
      ),
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="回归分析"
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

export function CorrelationPage() {
  const { columns, datasetId } = useDatasetColumns()

  return (
    <Tabs
      defaultActiveKey="correlation"
      items={[
        {
          key: 'correlation',
          label: '相关分析',
          children: <CorrelationTab columns={columns} datasetId={datasetId ?? undefined} />,
        },
        {
          key: 'regression',
          label: '回归分析',
          children: <RegressionTab columns={columns} datasetId={datasetId ?? undefined} />,
        },
      ]}
    />
  )
}
