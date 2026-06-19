import { useEffect, useState } from 'react'
import { Card, Table, Tag, Spin } from 'antd'
import { api, type AccountOut } from '../api'

const catLabel: Record<string, string> = {
  asset: '资产',
  liability: '负债',
  equity: '权益',
  income: '收入',
  expense: '费用',
}
const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Accounts() {
  const [rows, setRows] = useState<AccountOut[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.accounts().then(setRows).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin />

  return (
    <Card title="科目余额表">
      <Table
        size="small"
        rowKey="code"
        dataSource={rows}
        pagination={{ pageSize: 20 }}
        columns={[
          { title: '编码', dataIndex: 'code', width: 100 },
          { title: '名称', dataIndex: 'name' },
          {
            title: '类别',
            dataIndex: 'category',
            render: (c: string) => <Tag color="blue">{catLabel[c] || c}</Tag>,
          },
          { title: '借方发生', dataIndex: 'debit', align: 'right', render: (v: number) => money(v) },
          { title: '贷方发生', dataIndex: 'credit', align: 'right', render: (v: number) => money(v) },
          { title: '余额', dataIndex: 'balance', align: 'right', render: (v: number) => money(v) },
        ]}
      />
    </Card>
  )
}
