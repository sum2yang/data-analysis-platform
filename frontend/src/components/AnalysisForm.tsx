import { Form, Button, Card, Space, Tooltip } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'
import type { ReactNode } from 'react'

export interface AnalysisFormField {
  name: string
  label: string
  component: ReactNode
  required?: boolean
  tooltip?: string
  rules?: Record<string, unknown>[]
}

interface AnalysisFormProps {
  title: string
  fields: AnalysisFormField[]
  onSubmit: (values: Record<string, unknown>) => void
  loading?: boolean
  disabled?: boolean
  disabledReason?: string
  extra?: ReactNode
}

export function AnalysisForm({
  title,
  fields,
  onSubmit,
  loading = false,
  disabled = false,
  disabledReason,
  extra,
}: AnalysisFormProps) {
  const [form] = Form.useForm()

  const handleFinish = (values: Record<string, unknown>) => {
    onSubmit(values)
  }

  const submitButton = (
    <Button
      type="primary"
      htmlType="submit"
      icon={<PlayCircleOutlined />}
      loading={loading}
      disabled={disabled}
    >
      运行分析
    </Button>
  )

  return (
    <Card title={title} extra={extra} style={{ marginBottom: 16 }}>
      <Form form={form} layout="vertical" onFinish={handleFinish}>
        {fields.map((field) => (
          <Form.Item
            key={field.name}
            name={field.name}
            label={field.label}
            tooltip={field.tooltip}
            rules={
              field.required
                ? [{ required: true, message: `请选择${field.label}` }, ...(field.rules ?? [])]
                : field.rules
            }
          >
            {field.component}
          </Form.Item>
        ))}
        <Form.Item>
          <Space>
            {disabled && disabledReason ? (
              <Tooltip title={disabledReason}>{submitButton}</Tooltip>
            ) : (
              submitButton
            )}
            <Button onClick={() => form.resetFields()}>重置</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}
