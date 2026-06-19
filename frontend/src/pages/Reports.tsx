import { useEffect, useState } from 'react'
import { Card, Table, Tabs, Spin } from 'antd'
import { api, type ReportRow } from '../api'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

function Rows({ rows }: { rows: ReportRow[] }) {
  return (
    <Table
      size="small"
      pagination={false}
      rowKey={(_, i) => String(i)}
      dataSource={rows}
      columns={[
        { title: '项目', dataIndex: 'label' },
        { title: '金额', dataIndex: 'amount', align: 'right', render: (v: number) => money(v) },
      ]}
    />
  )
}

export default function Reports() {
  const [bs, setBs] = useState<ReportRow[]>([])
  const [inc, setInc] = useState<ReportRow[]>([])
  const [cf, setCf] = useState<ReportRow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.reportBalance(), api.reportIncome(), api.reportCashflow()])
      .then(([a, b, c]) => {
        setBs(a)
        setInc(b)
        setCf(c)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin />

  return (
    <Card>
      <Tabs
        items={[
          { key: 'bs', label: '资产负债表', children: <Rows rows={bs} /> },
          { key: 'inc', label: '利润表', children: <Rows rows={inc} /> },
          { key: 'cf', label: '现金流量表', children: <Rows rows={cf} /> },
        ]}
      />
    </Card>
  )
}
