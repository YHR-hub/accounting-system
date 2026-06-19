import { useEffect, useState } from 'react'
import { Card, Table, Spin } from 'antd'
import { api, type FixedAsset } from '../api'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Assets() {
  const [rows, setRows] = useState<FixedAsset[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.assets().then(setRows).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin />

  return (
    <Card title="固定资产">
      <Table
        size="small"
        rowKey="id"
        dataSource={rows}
        pagination={{ pageSize: 20 }}
        columns={[
          { title: '名称', dataIndex: 'name' },
          { title: '原值', dataIndex: 'original_value', align: 'right', render: (v: number) => money(v) },
          { title: '残值', dataIndex: 'residual_value', align: 'right', render: (v: number) => money(v) },
          { title: '使用月数', dataIndex: 'useful_life_months', align: 'right' },
          { title: '购入日期', dataIndex: 'purchase_date' },
          { title: '累计折旧', dataIndex: 'accumulated_deprec', align: 'right', render: (v: number) => money(v) },
          { title: '净值', dataIndex: 'net_value', align: 'right', render: (v: number) => money(v) },
        ]}
      />
    </Card>
  )
}
