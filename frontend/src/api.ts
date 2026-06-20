import axios from 'axios'

export const http = axios.create()

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)

export interface UserOut {
  username: string
  role: string
  display_name: string
}
export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserOut
}
export interface ReportRow {
  label: string
  amount: number
  section?: string | null
}
export interface AccountOut {
  code: string
  name: string
  category: string
  debit: number
  credit: number
  balance: number
}
export interface VoucherOut {
  id: number
  voucher_no: string
  date: string
  summary: string
  fiscal_year: number
  fiscal_month: number
  total: number
}
export interface EntryIn {
  account_code: string
  debit: number
  credit: number
}
export interface VoucherCreate {
  date: string
  summary: string
  entries: EntryIn[]
}

export interface Product {
  id: number
  code: string
  name: string
  category: string
  unit: string
  unit_price: number
  quantity: number
  amount: number
  min_stock: number
  location: string
}
export interface Employee {
  id: number
  code: string
  name: string
  department: string
  position: string
  base_salary: number
  insurance: number
  housing_fund: number
}
export interface FixedAsset {
  id: number
  name: string
  original_value: number
  residual_value: number
  useful_life_months: number
  depreciation_method: string
  purchase_date: string
  accumulated_deprec: number
  net_value: number
}
export interface Project {
  id: number
  code: string
  name: string
  budget: number
  start_date: string | null
  end_date: string | null
  status: string
}
export interface AuditLog {
  id: number
  username: string
  action: string
  target_type: string
  target_id: string
  detail: string
  created_at: string
}
export interface PayrollRecord {
  id: number
  employee_id: number
  year: number
  month: number
  gross_pay: number
  income_tax: number
  net_pay: number
  status: string
}
export interface Budget {
  id: number
  account_code: string
  fiscal_year: number
  fiscal_month: number
  budget_amount: number
  note: string
}
export interface AlertRule {
  id: number
  name: string
  indicator: string
  operator: string
  threshold: number
  enabled: number
  level: string
}
export interface AlertHistory {
  id: number
  rule_id: number | null
  message: string
  level: string
  resolved: number
  created_at: string
}
export interface EsgRow {
  id: number
  category: string
  year: number | string
  month: number
  indicator: string
  value: number
  unit: string
  note: string
}
export interface VoucherEntry {
  account_code: string
  account_name: string
  debit: number
  credit: number
}
export interface VoucherDetail {
  id: number
  voucher_no: string
  date: string
  summary: string
  fiscal_year: number
  fiscal_month: number
  entries: VoucherEntry[]
}
export interface TrialBalanceRow {
  code: string
  name: string
  debit: number
  credit: number
}
export interface TrialBalance {
  rows: TrialBalanceRow[]
  total_debit: number
  total_credit: number
  balanced: boolean
}
export interface AgingData {
  receivable: Record<string, number>
  payable: Record<string, number>
}
export interface ProjectPnl {
  id: number
  code: string
  name: string
  budget: number
  income: number
  expense: number
  profit: number
}
export interface BudgetExec extends Budget {
  account_name: string
  actual: number
  execution_rate: number
}
export interface TrendPoint {
  month: string
  revenue: number
  expense: number
  profit: number
}

export const api = {
  login: (username: string, password: string) =>
    http.post<TokenResponse>('/api/auth/login', { username, password }).then((r) => r.data),
  me: () => http.get<UserOut>('/api/auth/me').then((r) => r.data),
  ratios: () => http.get<Record<string, number>>('/api/ratios').then((r) => r.data),
  accounts: () => http.get<AccountOut[]>('/api/accounts').then((r) => r.data),
  vouchers: (year: number, month: number) =>
    http.get<VoucherOut[]>('/api/vouchers', { params: { year, month } }).then((r) => r.data),
  reportBalance: () => http.get<ReportRow[]>('/api/reports/balance').then((r) => r.data),
  reportIncome: () => http.get<ReportRow[]>('/api/reports/income').then((r) => r.data),
  reportCashflow: () => http.get<ReportRow[]>('/api/reports/cashflow').then((r) => r.data),
  createVoucher: (v: VoucherCreate) =>
    http.post<{ id: number; voucher_no: string }>('/api/vouchers', v).then((r) => r.data),
  deleteVoucher: (id: number) => http.delete(`/api/vouchers/${id}`),
  products: () => http.get<Product[]>('/api/inventory/products').then((r) => r.data),
  employees: () => http.get<Employee[]>('/api/employees').then((r) => r.data),
  assets: () => http.get<FixedAsset[]>('/api/assets').then((r) => r.data),
  projects: () => http.get<Project[]>('/api/projects').then((r) => r.data),
  audit: () => http.get<AuditLog[]>('/api/audit').then((r) => r.data),
  payroll: (year: number, month: number) =>
    http.get<PayrollRecord[]>('/api/payroll', { params: { year, month } }).then((r) => r.data),
  budgets: (year: number) =>
    http.get<Budget[]>('/api/budgets', { params: { year } }).then((r) => r.data),
  alertRules: () => http.get<AlertRule[]>('/api/alerts/rules').then((r) => r.data),
  alertHistory: () => http.get<AlertHistory[]>('/api/alerts/history').then((r) => r.data),
  esg: (year: number) =>
    http.get<EsgRow[]>('/api/esg', { params: { year } }).then((r) => r.data),
  createProduct: (body: Record<string, unknown>) =>
    http.post('/api/inventory/products', body).then((r) => r.data),
  inventoryIn: (body: { product_id: number; quantity: number; unit_price?: number; note?: string }) =>
    http.post('/api/inventory/in', body).then((r) => r.data),
  inventoryOut: (body: { product_id: number; quantity: number; note?: string }) =>
    http.post('/api/inventory/out', body).then((r) => r.data),
  addEmployee: (body: Record<string, unknown>) =>
    http.post('/api/employees', body).then((r) => r.data),
  addAsset: (body: Record<string, unknown>) =>
    http.post('/api/assets', body).then((r) => r.data),
  addProject: (body: Record<string, unknown>) =>
    http.post('/api/projects', body).then((r) => r.data),
  runPayroll: (year: number, month: number) =>
    http.post('/api/payroll/run', { year, month }).then((r) => r.data),
  voucherDetail: (id: number) =>
    http.get<VoucherDetail>(`/api/vouchers/${id}`).then((r) => r.data),
  addAccount: (body: Record<string, unknown>) =>
    http.post('/api/accounts', body).then((r) => r.data),
  trialBalance: () => http.get<TrialBalance>('/api/reports/trial-balance').then((r) => r.data),
  aging: () => http.get<AgingData>('/api/aging').then((r) => r.data),
  budgetExecution: (year: number) =>
    http.get<BudgetExec[]>('/api/budgets/execution', { params: { year } }).then((r) => r.data),
  projectsPnl: () => http.get<ProjectPnl[]>('/api/projects/pnl').then((r) => r.data),
  deactivateAccount: (code: string) => http.post(`/api/accounts/${code}/deactivate`),
  updateEmployee: (id: number, body: Record<string, unknown>) =>
    http.put(`/api/employees/${id}`, body),
  trend: (year: number) =>
    http.get<TrendPoint[]>('/api/trend', { params: { year } }).then((r) => r.data),
  exportExcelUrl: '/api/reports/export.xlsx',
}
