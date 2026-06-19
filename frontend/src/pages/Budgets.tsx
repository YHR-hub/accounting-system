import { useEffect, useState } from 'react'
import { Card, Table, InputNumber, Button, Space } from 'antd'
import { api, type Budget } from '../api'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Budgets() {
  const [rows, setRows] = useState<Budget[]>([])
  const [loading, setLoading] = useState(true)
  const [year, setYear] = useState(2026)

  const load = () => {
    setLoading(true)
    api.budgets(year).then(setRows).finally(() => setLoading(false))
  }
  useEffect(load, [])

  return (
    <Card
      title="预算"
      extra={
        <Space>
          <InputNumber value={year} onChange={(v) => setYear(v || 2026)} style={{ width: 100 }} />
          <Button onClick={load}>查询</Button>
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
          { title: '科目', dataIndex: 'account_code', width: 120 },
          { title: '年', dataIndex: 'fiscal_year', width: 90 },
          { title: '月', dataIndex: 'fiscal_month', width: 70 },
          { title: '预算金额', dataIndex: 'budget_amount', align: 'right', render: (v: number) => money(v) },
          { title: '备注', dataIndex: 'note' },
        ]}
      />
    </Card>
  )
}
