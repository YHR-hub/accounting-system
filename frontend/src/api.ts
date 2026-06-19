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
}
