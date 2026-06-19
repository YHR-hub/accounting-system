import {
  DashboardOutlined,
  FileTextOutlined,
  BankOutlined,
  ProfileOutlined,
  LogoutOutlined,
  InboxOutlined,
  TeamOutlined,
  GoldOutlined,
  ProjectOutlined,
  AuditOutlined,
  MoneyCollectOutlined,
  FundOutlined,
  AlertOutlined,
  GlobalOutlined,
  AccountBookOutlined,
} from '@ant-design/icons'
import { Layout, Menu, Button, Typography } from 'antd'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from './auth'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Reports from './pages/Reports'
import Accounts from './pages/Accounts'
import Vouchers from './pages/Vouchers'
import Inventory from './pages/Inventory'
import Employees from './pages/Employees'
import Assets from './pages/Assets'
import Projects from './pages/Projects'
import Audit from './pages/Audit'
import Payroll from './pages/Payroll'
import Budgets from './pages/Budgets'
import Alerts from './pages/Alerts'
import ESG from './pages/ESG'
import Aging from './pages/Aging'

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
    { key: '/inventory', icon: <InboxOutlined />, label: '库存' },
    { key: '/employees', icon: <TeamOutlined />, label: '员工' },
    { key: '/assets', icon: <GoldOutlined />, label: '固定资产' },
    { key: '/projects', icon: <ProjectOutlined />, label: '项目' },
    { key: '/aging', icon: <AccountBookOutlined />, label: '应收应付' },
    { key: '/payroll', icon: <MoneyCollectOutlined />, label: '薪资' },
    { key: '/budgets', icon: <FundOutlined />, label: '预算' },
    { key: '/alerts', icon: <AlertOutlined />, label: '预警' },
    { key: '/esg', icon: <GlobalOutlined />, label: 'ESG' },
    { key: '/audit', icon: <AuditOutlined />, label: '审计日志' },
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
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/employees" element={<Employees />} />
            <Route path="/assets" element={<Assets />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/aging" element={<Aging />} />
            <Route path="/payroll" element={<Payroll />} />
            <Route path="/budgets" element={<Budgets />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/esg" element={<ESG />} />
            <Route path="/audit" element={<Audit />} />
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
