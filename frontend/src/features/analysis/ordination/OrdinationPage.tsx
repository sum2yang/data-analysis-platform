import { useState } from 'react'
import { Select, InputNumber, message, Row, Col, Tabs } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { AnalysisForm } from '@/components/AnalysisForm'
import { AnalysisResults } from '@/components/AnalysisResults'
import { ColumnSelector } from '@/components/ColumnSelector'
import { submitAnalysis } from '../api'
import { useAnalysis, useAnalysisPolling } from '@/hooks/useAnalysis'
import { useDatasetColumns } from '@/hooks/useDatasetColumns'
import type { ColumnInfo } from '@/api/types'

function PcaTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const { submitMutation, result, polling } = useAnalysis(datasetId, 'pca')

  const fields = [
    {
      name: 'columns',
      label: '数值变量',
      required: true,
      tooltip: '选择用于 PCA 的数值列（至少2个）',
      component: <ColumnSelector columns={columns} filterType="numeric" placeholder="选择数值列" />,
    },
    {
      name: 'group_column',
      label: '分组变量',
      tooltip: '可选，用于着色和椭圆',
      component: <ColumnSelector columns={columns} filterType="categorical" multiple={false} placeholder="选择分组列（可选）" />,
    },
    {
      name: 'scale_mode',
      label: '标准化方式',
      component: (
        <Select
          defaultValue="scale"
          options={[
            { label: '中心化+标准化 (scale)', value: 'scale' },
            { label: '仅中心化 (center)', value: 'center' },
            { label: '不处理 (none)', value: 'none' },
          ]}
        />
      ),
    },
    {
      name: 'components',
      label: '返回轴数',
      component: <InputNumber defaultValue={5} min={2} max={20} style={{ width: '100%' }} />,
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="PCA 主成分分析"
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

function PcoaTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const { submitMutation, result, polling } = useAnalysis(datasetId, 'pcoa')

  const fields = [
    {
      name: 'columns',
      label: '数值变量',
      required: true,
      component: <ColumnSelector columns={columns} filterType="numeric" placeholder="选择数值列" />,
    },
    {
      name: 'group_column',
      label: '分组变量',
      component: <ColumnSelector columns={columns} filterType="categorical" multiple={false} placeholder="选择分组列（可选）" />,
    },
    {
      name: 'distance',
      label: '距离度量',
      component: (
        <Select
          defaultValue="bray"
          options={[
            { label: 'Bray-Curtis', value: 'bray' },
            { label: 'Jaccard', value: 'jaccard' },
            { label: 'Euclidean', value: 'euclidean' },
          ]}
        />
      ),
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="PCoA 主坐标分析"
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

function NmdsTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const { submitMutation, result, polling } = useAnalysis(datasetId, 'nmds')

  const fields = [
    {
      name: 'columns',
      label: '数值变量',
      required: true,
      component: <ColumnSelector columns={columns} filterType="numeric" placeholder="选择数值列" />,
    },
    {
      name: 'group_column',
      label: '分组变量',
      component: <ColumnSelector columns={columns} filterType="categorical" multiple={false} placeholder="选择分组列（可选）" />,
    },
    {
      name: 'distance',
      label: '距离度量',
      component: (
        <Select
          defaultValue="bray"
          options={[
            { label: 'Bray-Curtis', value: 'bray' },
            { label: 'Jaccard', value: 'jaccard' },
            { label: 'Euclidean', value: 'euclidean' },
          ]}
        />
      ),
    },
    {
      name: 'dimensions',
      label: '维度数',
      component: <InputNumber defaultValue={2} min={2} max={5} style={{ width: '100%' }} />,
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="NMDS 非度量多维尺度分析"
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

function RdaCcaTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const [selectedMethod, setSelectedMethod] = useState<string>('rda')
  const { setRunId, result, polling, setPolling } = useAnalysisPolling()

  const submitMutation = useMutation({
    mutationFn: (params: Record<string, unknown>) => {
      const { method: _method, ...cleanParams } = params
      return submitAnalysis(datasetId!, selectedMethod, cleanParams)
    },
    onSuccess: (data) => {
      setRunId(data.run_id)
      setPolling(true)
      message.info('排序分析任务已提交')
    },
    onError: () => message.error('提交失败'),
  })

  const fields = [
    {
      name: 'species_columns',
      label: '物种/响应变量',
      required: true,
      tooltip: '物种矩阵的列',
      component: <ColumnSelector columns={columns} filterType="numeric" placeholder="选择物种列" />,
    },
    {
      name: 'env_columns',
      label: '环境/解释变量',
      required: true,
      tooltip: '环境矩阵的列',
      component: <ColumnSelector columns={columns} filterType="numeric" placeholder="选择环境列" />,
    },
    {
      name: 'group_column',
      label: '分组变量',
      component: <ColumnSelector columns={columns} filterType="categorical" multiple={false} placeholder="选择分组列（可选）" />,
    },
    {
      name: 'method',
      label: '排序方法',
      component: (
        <Select
          value={selectedMethod}
          onChange={setSelectedMethod}
          options={[
            { label: 'RDA (冗余分析)', value: 'rda' },
            { label: 'CCA (典范对应分析)', value: 'cca' },
          ]}
        />
      ),
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="RDA / CCA 约束排序"
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

export function OrdinationPage() {
  const { columns, datasetId } = useDatasetColumns()

  return (
    <Tabs
      defaultActiveKey="pca"
      items={[
        { key: 'pca', label: 'PCA', children: <PcaTab columns={columns} datasetId={datasetId ?? undefined} /> },
        { key: 'pcoa', label: 'PCoA', children: <PcoaTab columns={columns} datasetId={datasetId ?? undefined} /> },
        { key: 'nmds', label: 'NMDS', children: <NmdsTab columns={columns} datasetId={datasetId ?? undefined} /> },
        { key: 'rda_cca', label: 'RDA/CCA', children: <RdaCcaTab columns={columns} datasetId={datasetId ?? undefined} /> },
      ]}
    />
  )
}
