import { Row, Col } from 'antd'
import { AnalysisForm } from '@/components/AnalysisForm'
import { AnalysisResults } from '@/components/AnalysisResults'
import { ColumnSelector } from '@/components/ColumnSelector'
import { useAnalysis } from '@/hooks/useAnalysis'
import { useDatasetColumns } from '@/hooks/useDatasetColumns'

export function DescriptivePage() {
  const { columns, datasetId } = useDatasetColumns()
  const { submitMutation, result, polling } = useAnalysis(datasetId, 'descriptive')

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
        <AnalysisResults result={result} highlightPValue={false} />
      </Col>
    </Row>
  )
}
