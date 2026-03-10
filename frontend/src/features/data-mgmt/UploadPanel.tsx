import { Upload, message, Card } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadDataset } from './api'

const { Dragger } = Upload

export function UploadPanel() {
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDataset(file),
    onSuccess: (data) => {
      message.success(`上传成功: ${data.name} (${data.row_count} 行, ${data.col_count} 列)`)
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
    onError: () => {
      message.error('上传失败')
    },
  })

  return (
    <Card title="上传数据" style={{ marginBottom: 16 }}>
      <Dragger
        accept=".csv,.xlsx,.xls,.tsv"
        multiple={false}
        showUploadList={false}
        customRequest={({ file }) => {
          uploadMutation.mutate(file as File)
        }}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">支持 CSV, XLSX, XLS, TSV 格式</p>
      </Dragger>
    </Card>
  )
}
