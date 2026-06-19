import { useEffect, useState } from 'react'
import { Card, Table, Button, InputNumber, Space, Tag, message } from 'antd'
import { api, type PayrollRecord } from '../api'
import { useAuth } from '../auth'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const statusColor: Record<string, string> = { draft: 'default', confirmed: 'blue', paid: 'green' }

export default function Payroll() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'accountant'
  const [rows, setRows] = useState<PayrollRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [year, setYear] = useState(2026)
  const [month, setMonth] = useState(6)

  const load = () => {
    setLoading(true)
    api.payroll(year, month).then(setRows).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const run = async () => {
    try {
      const r: any = await api.runPayroll(year, month)
      message.success(`已生成 ${r.created} 条工资记录`)
      load()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '计算失败')
    }
  }

  return (
    <Card
      title="薪资"
      extra={
        <Space>
          <InputNumber value={year} onChange={(v) => setYear(v || 2026)} style={{ width: 100 }} />
          <InputNumber value={month} min={1} max={12} onChange={(v) => setMonth(v || 1)} style={{ width: 80 }} />
          <Button onClick={load}>查询</Button>
          {canWrite && <Button type="primary" onClick={run}>算工资</Button>}
        </Space>
      }
    >
      <Table
        size="small"
        rowKey="id"
        loading={loading}
        dataSource={rows}
        pagination={{ pageSize: 20 }}
        columns={[
          { title: '员工ID', dataIndex: 'employee_id', width: 90 },
          { title: '年', dataIndex: 'year', width: 80 },
          { title: '月', dataIndex: 'month', width: 60 },
          { title: '应发', dataIndex: 'gross_pay', align: 'right', render: (v: number) => money(v) },
          { title: '个税', dataIndex: 'income_tax', align: 'right', render: (v: number) => money(v) },
          { title: '实发', dataIndex: 'net_pay', align: 'right', render: (v: number) => money(v) },
          { title: '状态', dataIndex: 'status', render: (s: string) => <Tag color={statusColor[s] || 'default'}>{s}</Tag> },
        ]}
      />
    </Card>
  )
}
