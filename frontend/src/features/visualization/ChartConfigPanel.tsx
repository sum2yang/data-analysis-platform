import { Card, Form, InputNumber, Select, Space, Slider } from 'antd'

interface ChartConfigPanelProps {
  onConfigChange: (config: ChartConfig) => void
}

export interface ChartConfig {
  width: number
  height: number
  dpi: number
  format: 'png' | 'svg' | 'pdf'
}

export function ChartConfigPanel({ onConfigChange }: ChartConfigPanelProps) {
  const [form] = Form.useForm<ChartConfig>()

  const handleChange = () => {
    const values = form.getFieldsValue()
    onConfigChange(values)
  }

  return (
    <Card title="图表配置" size="small" style={{ marginBottom: 16 }}>
      <Form
        form={form}
        layout="vertical"
        size="small"
        initialValues={{ width: 800, height: 600, dpi: 300, format: 'png' }}
        onValuesChange={handleChange}
      >
        <Space wrap>
          <Form.Item name="width" label="宽度 (px)">
            <InputNumber min={200} max={3000} step={100} />
          </Form.Item>
          <Form.Item name="height" label="高度 (px)">
            <InputNumber min={200} max={3000} step={100} />
          </Form.Item>
          <Form.Item name="dpi" label="DPI">
            <Slider min={72} max={600} step={72} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="format" label="格式">
            <Select
              options={[
                { label: 'PNG', value: 'png' },
                { label: 'SVG', value: 'svg' },
                { label: 'PDF', value: 'pdf' },
              ]}
              style={{ width: 100 }}
            />
          </Form.Item>
        </Space>
      </Form>
    </Card>
  )
}
