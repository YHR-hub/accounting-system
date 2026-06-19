import { Form, Input, Button, Card, message, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Login() {
  const { login } = useAuth()
  const nav = useNavigate()

  const onFinish = async (v: { username: string; password: string }) => {
    try {
      await login(v.username, v.password)
      nav('/')
    } catch {
      message.error('用户名或密码错误')
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f5f6fa',
      }}
    >
      <Card style={{ width: 360 }}>
        <Typography.Title level={3} style={{ textAlign: 'center', color: '#6c5ce7' }}>
          会计系统专业版
        </Typography.Title>
        <Form
          onFinish={onFinish}
          layout="vertical"
          initialValues={{ username: 'admin', password: 'admin123' }}
        >
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>
            登录
          </Button>
        </Form>
        <Typography.Paragraph type="secondary" style={{ marginTop: 12, fontSize: 12 }}>
          演示账号：admin/admin123 · accountant/acc123 · viewer/view123
        </Typography.Paragraph>
      </Card>
    </div>
  )
}
