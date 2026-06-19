import { useEffect, useState } from 'react'
import { Card, Table, Spin, Row, Col } from 'antd'
import { api, type AgingData } from '../api'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

function BucketTable({ title, data }: { title: string; data: Record<string, number> }) {
  const rows = Object.entries(data).map(([bucket, amount], i) => ({ key: i, bucket, amount }))
  const total = rows.reduce((s, r) => s + r.amount, 0)
  return (
    <Card title={title} size="small">
      <Table
        size="small"
        pagination={false}
        dataSource={rows}
        columns={[
          { title: '账龄区间', dataIndex: 'bucket' },
          { title: '金额', dataIndex: 'amount', align: 'right', render: (v: number) => money(v) },
        ]}
        summary={() => (
          <Table.Summary.Row>
            <Table.Summary.Cell index={0}><b>合计</b></Table.Summary.Cell>
            <Table.Summary.Cell index={1} align="right"><b>{money(total)}</b></Table.Summary.Cell>
          </Table.Summary.Row>
        )}
      />
    </Card>
  )
}

export default function Aging() {
  const [data, setData] = useState<AgingData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.aging().then(setData).finally(() => setLoading(false))
  }, [])

  if (loading || !data) return <Spin />

  return (
    <Row gutter={16}>
      <Col span={12}><BucketTable title="应收账款账龄" data={data.receivable} /></Col>
      <Col span={12}><BucketTable title="应付账款账龄" data={data.payable} /></Col>
    </Row>
  )
}
