import { Form, Input, Button, Card, Typography, Space } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'
import { useRegister } from './hooks/useAuth'
import type { RegisterRequest } from '@/api/types'

const { Title } = Typography

export function RegisterPage() {
  const registerMutation = useRegister()

  const onFinish = (values: RegisterRequest) => {
    registerMutation.mutate(values)
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#f5f5f5',
      }}
    >
      <Card style={{ width: 400 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Title level={3} style={{ textAlign: 'center', margin: 0 }}>
            注册账号
          </Title>
          <Form<RegisterRequest>
            onFinish={onFinish}
            size="large"
            autoComplete="off"
          >
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
              ]}
            >
              <Input prefix={<UserOutlined />} placeholder="用户名" />
            </Form.Item>
            <Form.Item
              name="email"
              rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
            >
              <Input prefix={<MailOutlined />} placeholder="邮箱（可选）" />
            </Form.Item>
            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="密码" />
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                block
                loading={registerMutation.isPending}
              >
                注册
              </Button>
            </Form.Item>
            <div style={{ textAlign: 'center' }}>
              已有账号？ <Link to="/login">返回登录</Link>
            </div>
          </Form>
        </Space>
      </Card>
    </div>
  )
}
