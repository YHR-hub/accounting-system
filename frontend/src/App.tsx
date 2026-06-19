import {
  DashboardOutlined,
  FileTextOutlined,
  BankOutlined,
  ProfileOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { Layout, Menu, Button, Typography } from 'antd'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from './auth'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Reports from './pages/Reports'
import Accounts from './pages/Accounts'
import Vouchers from './pages/Vouchers'

const { Header, Sider, Content } = Layout

function Shell() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()

  const items = [
    { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '/reports', icon: <FileTextOutlined />, label: '财务报表' },
    { key: '/accounts', icon: <BankOutlined />, label: '科目余额' },
    { key: '/vouchers', icon: <ProfileOutlined />, label: '凭证' },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" breakpoint="lg" collapsedWidth="0">
        <div style={{ color: '#fff', padding: 16, fontWeight: 700, fontSize: 16 }}>
          会计系统专业版
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[loc.pathname]}
          items={items}
          onClick={(e) => nav(e.key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            gap: 12,
            paddingRight: 24,
          }}
        >
          <Typography.Text strong>
            {user?.display_name}（{user?.role}）
          </Typography.Text>
          <Button
            icon={<LogoutOutlined />}
            onClick={() => {
              logout()
              nav('/login')
            }}
          >
            退出
          </Button>
        </Header>
        <Content style={{ margin: 16 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/accounts" element={<Accounts />} />
            <Route path="/vouchers" element={<Vouchers />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default function App() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/*" element={user ? <Shell /> : <Navigate to="/login" replace />} />
    </Routes>
  )
}
