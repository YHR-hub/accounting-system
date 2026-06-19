import { useEffect, useState } from 'react'
import { Card, Table, InputNumber, Button, Space, Progress } from 'antd'
import { api, type BudgetExec } from '../api'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Budgets() {
  const [rows, setRows] = useState<BudgetExec[]>([])
  const [loading, setLoading] = useState(true)
  const [year, setYear] = useState(2026)

  const load = () => {
    setLoading(true)
    api.budgetExecution(year).then(setRows).finally(() => setLoading(false))
  }
  useEffect(load, [])

  return (
    <Card
      title="预算执行"
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
          { title: '科目', dataIndex: 'account_code', width: 100 },
          { title: '名称', dataIndex: 'account_name' },
          { title: '月', dataIndex: 'fiscal_month', width: 70 },
          { title: '预算', dataIndex: 'budget_amount', align: 'right', render: (v: number) => money(v) },
          { title: '实际', dataIndex: 'actual', align: 'right', render: (v: number) => money(v) },
          {
            title: '执行率',
            dataIndex: 'execution_rate',
            width: 160,
            render: (v: number) => (
              <Progress percent={Math.min(v, 100)} size="small" format={() => `${v}%`} />
            ),
          },
        ]}
      />
    </Card>
  )
}
