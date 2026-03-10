import { Card, Form, Select, Button, Space, Input, message, Empty } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { cleanDataset } from './api'
import type { CleanOperation } from './types'

const operationOptions = [
  { label: '删除缺失值行', value: 'drop_na' },
  { label: '填充缺失值', value: 'fill_na' },
  { label: '删除重复行', value: 'drop_duplicates' },
  { label: '删除列', value: 'drop_columns' },
  { label: '重命名列', value: 'rename' },
  { label: '转换类型', value: 'change_type' },
]

interface CleaningPanelProps {
  datasetId: string | null
}

export function CleaningPanel({ datasetId }: CleaningPanelProps) {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const cleanMutation = useMutation({
    mutationFn: (operations: CleanOperation[]) =>
      cleanDataset({ dataset_id: datasetId!, operations }),
    onSuccess: () => {
      message.success('数据清洗完成')
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      queryClient.invalidateQueries({ queryKey: ['datasetPreview', datasetId] })
      queryClient.invalidateQueries({ queryKey: ['datasetProfile', datasetId] })
      form.resetFields()
    },
    onError: () => {
      message.error('数据清洗失败')
    },
  })

  if (!datasetId) {
    return (
      <Card title="数据清洗">
        <Empty description="请先选择数据集" />
      </Card>
    )
  }

  const handleSubmit = () => {
    const values = form.getFieldsValue()
    const ops: CleanOperation[] = (values.operations ?? [])
      .filter((op: { type?: string }) => op?.type)
      .map((op: { type: string; param_key?: string; param_value?: string }) => ({
        type: op.type,
        params: op.param_key ? { [op.param_key]: op.param_value } : {},
      }))
    if (ops.length === 0) {
      message.warning('请至少添加一个操作')
      return
    }
    cleanMutation.mutate(ops)
  }

  return (
    <Card title="数据清洗">
      <Form form={form} layout="vertical">
        <Form.List name="operations">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Space key={key} align="start" style={{ display: 'flex', marginBottom: 8 }}>
                  <Form.Item {...restField} name={[name, 'type']} style={{ width: 180 }}>
                    <Select options={operationOptions} placeholder="选择操作" />
                  </Form.Item>
                  <Form.Item {...restField} name={[name, 'param_key']} style={{ width: 120 }}>
                    <Input placeholder="参数名" />
                  </Form.Item>
                  <Form.Item {...restField} name={[name, 'param_value']} style={{ width: 120 }}>
                    <Input placeholder="参数值" />
                  </Form.Item>
                  <Button icon={<DeleteOutlined />} onClick={() => remove(name)} danger />
                </Space>
              ))}
              <Form.Item>
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  添加操作
                </Button>
              </Form.Item>
            </>
          )}
        </Form.List>
        <Form.Item>
          <Button type="primary" onClick={handleSubmit} loading={cleanMutation.isPending}>
            执行清洗
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}
