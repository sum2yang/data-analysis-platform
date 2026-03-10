import { Tabs } from 'antd'
import { useDatasetStore } from '@/store/datasetStore'
import { UploadPanel } from './UploadPanel'
import { DataPreview } from './DataPreview'
import { ColumnTypeEditor } from './ColumnTypeEditor'
import { JoinWizard } from './JoinWizard'
import { CleaningPanel } from './CleaningPanel'

export function DataMgmtPage() {
  const { currentDatasetId } = useDatasetStore()

  const tabItems = [
    {
      key: 'upload',
      label: '上传数据',
      children: <UploadPanel />,
    },
    {
      key: 'preview',
      label: '数据预览',
      children: <DataPreview datasetId={currentDatasetId} />,
    },
    {
      key: 'columns',
      label: '列类型',
      children: <ColumnTypeEditor datasetId={currentDatasetId} />,
    },
    {
      key: 'join',
      label: '数据合并',
      children: <JoinWizard />,
    },
    {
      key: 'clean',
      label: '数据清洗',
      children: <CleaningPanel datasetId={currentDatasetId} />,
    },
  ]

  return <Tabs defaultActiveKey="upload" items={tabItems} />
}
