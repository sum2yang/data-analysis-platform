import { Row, Col } from 'antd'
import { AnalysisForm } from '@/components/AnalysisForm'
import { AnalysisResults } from '@/components/AnalysisResults'
import { ColumnSelector } from '@/components/ColumnSelector'
import { useAnalysis } from '@/hooks/useAnalysis'
import { useDatasetColumns } from '@/hooks/useDatasetColumns'

export function AssumptionsPage() {
  const { columns, datasetId } = useDatasetColumns()
  const { submitMutation, result, polling } = useAnalysis(datasetId, 'assumptions')

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

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <AnalysisForm
          title="假设检验"
          fields={formFields}
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
