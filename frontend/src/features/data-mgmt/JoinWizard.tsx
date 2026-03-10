import { Card, Steps, Form, Select, Input, Button, Space, message } from 'antd'
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useDatasetStore } from '@/store/datasetStore'
import { joinDatasets } from './api'
import type { JoinRequest } from './types'

const joinTypes = [
  { label: '内连接 (Inner)', value: 'inner' },
  { label: '左连接 (Left)', value: 'left' },
  { label: '右连接 (Right)', value: 'right' },
  { label: '全连接 (Outer)', value: 'outer' },
]

export function JoinWizard() {
  const [step, setStep] = useState(0)
  const [form] = Form.useForm()
  const { datasets } = useDatasetStore()
  const queryClient = useQueryClient()

  const joinMutation = useMutation({
    mutationFn: (data: JoinRequest) => joinDatasets(data),
    onSuccess: (result) => {
      message.success(`合并成功: ${result.name} (${result.row_count} 行)`)
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      setStep(0)
      form.resetFields()
    },
    onError: () => {
      message.error('合并失败')
    },
  })

  const datasetOptions = datasets.map((d) => ({
    label: d.name,
    value: d.id,
  }))

  const handleFinish = (values: JoinRequest) => {
    joinMutation.mutate(values)
  }

  const steps = [
    {
      title: '选择数据集',
      content: (
        <>
          <Form.Item
            name="left_dataset_id"
            label="左侧数据集"
            rules={[{ required: true, message: '请选择左侧数据集' }]}
          >
            <Select options={datasetOptions} placeholder="选择数据集" />
          </Form.Item>
          <Form.Item
            name="right_dataset_id"
            label="右侧数据集"
            rules={[{ required: true, message: '请选择右侧数据集' }]}
          >
            <Select options={datasetOptions} placeholder="选择数据集" />
          </Form.Item>
        </>
      ),
    },
    {
      title: '配置连接',
      content: (
        <>
          <Form.Item
            name="left_key"
            label="左侧连接键"
            rules={[{ required: true, message: '请输入左侧连接键' }]}
          >
            <Input placeholder="列名" />
          </Form.Item>
          <Form.Item
            name="right_key"
            label="右侧连接键"
            rules={[{ required: true, message: '请输入右侧连接键' }]}
          >
            <Input placeholder="列名" />
          </Form.Item>
          <Form.Item
            name="how"
            label="连接类型"
            rules={[{ required: true, message: '请选择连接类型' }]}
            initialValue="inner"
          >
            <Select options={joinTypes} />
          </Form.Item>
        </>
      ),
    },
    {
      title: '命名保存',
      content: (
        <Form.Item
          name="name"
          label="新数据集名称"
          rules={[{ required: true, message: '请输入数据集名称' }]}
        >
          <Input placeholder="合并后的数据集名称" />
        </Form.Item>
      ),
    },
  ]

  return (
    <Card title="数据合并">
      <Steps current={step} items={steps.map((s) => ({ title: s.title }))} style={{ marginBottom: 24 }} />
      <Form form={form} layout="vertical" onFinish={handleFinish}>
        {steps[step].content}
        <Form.Item>
          <Space>
            {step > 0 && <Button onClick={() => setStep(step - 1)}>上一步</Button>}
            {step < steps.length - 1 && (
              <Button type="primary" onClick={() => setStep(step + 1)}>
                下一步
              </Button>
            )}
            {step === steps.length - 1 && (
              <Button type="primary" htmlType="submit" loading={joinMutation.isPending}>
                执行合并
              </Button>
            )}
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}
