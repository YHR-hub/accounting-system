import { useEffect, useState } from 'react'
import { Card, Table, Tabs, Spin, Tag, Button } from 'antd'
import { api, type ReportRow, type TrialBalance } from '../api'

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

function TrialBalanceView({ tb }: { tb: TrialBalance | null }) {
  if (!tb) return <Spin />
  return (
    <>
      <div style={{ marginBottom: 8 }}>
        借贷{tb.balanced ? <Tag color="green">平衡</Tag> : <Tag color="red">不平</Tag>}
      </div>
      <Table
        size="small"
        pagination={false}
        rowKey="code"
        dataSource={tb.rows}
        columns={[
          { title: '编码', dataIndex: 'code', width: 100 },
          { title: '科目', dataIndex: 'name' },
          { title: '借方', dataIndex: 'debit', align: 'right', render: (v: number) => money(v) },
          { title: '贷方', dataIndex: 'credit', align: 'right', render: (v: number) => money(v) },
        ]}
        summary={() => (
          <Table.Summary.Row>
            <Table.Summary.Cell index={0} colSpan={2}><b>合计</b></Table.Summary.Cell>
            <Table.Summary.Cell index={2} align="right"><b>{money(tb.total_debit)}</b></Table.Summary.Cell>
            <Table.Summary.Cell index={3} align="right"><b>{money(tb.total_credit)}</b></Table.Summary.Cell>
          </Table.Summary.Row>
        )}
      />
    </>
  )
}

export default function Reports() {
  const [bs, setBs] = useState<ReportRow[]>([])
  const [inc, setInc] = useState<ReportRow[]>([])
  const [cf, setCf] = useState<ReportRow[]>([])
  const [tb, setTb] = useState<TrialBalance | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.reportBalance(), api.reportIncome(), api.reportCashflow(), api.trialBalance()])
      .then(([a, b, c, t]) => {
        setBs(a)
        setInc(b)
        setCf(c)
        setTb(t)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin />

  return (
    <Card extra={<Button onClick={() => window.open(api.exportExcelUrl)}>导出 Excel</Button>}>
      <Tabs
        items={[
          { key: 'bs', label: '资产负债表', children: <Rows rows={bs} /> },
          { key: 'inc', label: '利润表', children: <Rows rows={inc} /> },
          { key: 'cf', label: '现金流量表', children: <Rows rows={cf} /> },
          { key: 'tb', label: '试算平衡表', children: <TrialBalanceView tb={tb} /> },
        ]}
      />
    </Card>
  )
}
