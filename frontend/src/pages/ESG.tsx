import { useEffect, useState } from 'react'
import { Card, Table, InputNumber, Button, Space, Tag } from 'antd'
import { api, type EsgRow } from '../api'

const catLabel: Record<string, string> = {
  environment: '环境(E)',
  social: '社会(S)',
  governance: '治理(G)',
}

export default function ESG() {
  const [rows, setRows] = useState<EsgRow[]>([])
  const [loading, setLoading] = useState(true)
  const [year, setYear] = useState(2026)

  const load = () => {
    setLoading(true)
    api.esg(year).then(setRows).finally(() => setLoading(false))
  }
  useEffect(load, [])

  return (
    <Card
      title="ESG 数据"
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
          { title: '维度', dataIndex: 'category', render: (c: string) => <Tag color="green">{catLabel[c] || c}</Tag> },
          { title: '指标', dataIndex: 'indicator' },
          { title: '数值', dataIndex: 'value', align: 'right' },
          { title: '单位', dataIndex: 'unit' },
          { title: '备注', dataIndex: 'note' },
        ]}
      />
    </Card>
  )
}
