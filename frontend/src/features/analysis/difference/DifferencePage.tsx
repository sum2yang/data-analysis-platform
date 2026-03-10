import { useState } from 'react'
import { Tabs, Select, InputNumber, Switch, message, Row, Col } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { AnalysisForm } from '@/components/AnalysisForm'
import { AnalysisResults } from '@/components/AnalysisResults'
import { ColumnSelector } from '@/components/ColumnSelector'
import { submitAnalysis } from '../api'
import { useAnalysis, useAnalysisPolling } from '@/hooks/useAnalysis'
import { useDatasetColumns } from '@/hooks/useDatasetColumns'
import type { ColumnInfo } from '@/api/types'

function TTestTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const { submitMutation, result, polling } = useAnalysis(datasetId, 't_test')

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
  const { submitMutation, result, polling } = useAnalysis(datasetId, 'anova_one_way')

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
      name: 'posthoc_method',
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

function WelchAnovaTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const { submitMutation, result, polling } = useAnalysis(datasetId, 'anova_welch')

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
      name: 'posthoc_method',
      label: '事后检验',
      component: (
        <Select
          defaultValue="games-howell"
          options={[
            { label: 'Games-Howell', value: 'games-howell' },
            { label: 'Tamhane T2', value: 'tamhane-t2' },
            { label: 'Dunnett T3', value: 'dunnett-t3' },
            { label: '无', value: 'none' },
          ]}
        />
      ),
    },
    {
      name: 'alpha',
      label: '显著性水平',
      component: <InputNumber defaultValue={0.05} min={0.01} max={0.1} step={0.01} style={{ width: '100%' }} />,
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="Welch 方差分析"
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

function MultiWayAnovaTab({ columns, datasetId }: { columns: ColumnInfo[]; datasetId?: string }) {
  const { submitMutation, result, polling } = useAnalysis(datasetId, 'anova_multi_way')

  const fields = [
    {
      name: 'response_column',
      label: '响应变量',
      required: true,
      component: <ColumnSelector columns={columns} filterType="numeric" multiple={false} placeholder="选择数值列" />,
    },
    {
      name: 'factor_columns',
      label: '因子变量',
      required: true,
      tooltip: '至少选择2个因子变量',
      component: <ColumnSelector columns={columns} filterType="categorical" multiple={true} placeholder="选择分组列 (至少2个)" />,
    },
    {
      name: 'include_interactions',
      label: '包含交互效应',
      component: <Switch defaultChecked />,
    },
    {
      name: 'ss_type',
      label: '平方和类型',
      component: (
        <Select
          defaultValue="2"
          options={[
            { label: 'Type I', value: '1' },
            { label: 'Type II (推荐)', value: '2' },
            { label: 'Type III', value: '3' },
          ]}
        />
      ),
    },
  ]

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="多因素方差分析"
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
  const [selectedTest, setSelectedTest] = useState<string>('kruskal_wallis')
  const { setRunId, result, polling, setPolling } = useAnalysisPolling()

  const submitMutation = useMutation({
    mutationFn: (params: Record<string, unknown>) => {
      const { test: _test, ...cleanParams } = params
      return submitAnalysis(datasetId!, selectedTest, cleanParams)
    },
    onSuccess: (data) => {
      setRunId(data.run_id)
      setPolling(true)
      message.info('分析任务已提交')
    },
    onError: () => {
      message.error('提交失败')
    },
  })

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
          value={selectedTest}
          onChange={setSelectedTest}
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
      label: '单因素方差分析 (ANOVA)',
      children: <AnovaTab columns={columns} datasetId={datasetId ?? undefined} />,
    },
    {
      key: 'welch',
      label: 'Welch 方差分析',
      children: <WelchAnovaTab columns={columns} datasetId={datasetId ?? undefined} />,
    },
    {
      key: 'multiway',
      label: '多因素方差分析',
      children: <MultiWayAnovaTab columns={columns} datasetId={datasetId ?? undefined} />,
    },
    {
      key: 'nonparametric',
      label: '非参数检验',
      children: <NonParametricTab columns={columns} datasetId={datasetId ?? undefined} />,
    },
  ]

  return <Tabs defaultActiveKey="ttest" items={tabItems} />
}
