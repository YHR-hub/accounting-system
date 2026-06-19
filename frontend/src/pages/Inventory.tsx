import { useEffect, useState } from 'react'
import { Card, Table, Spin } from 'antd'
import { api, type Product } from '../api'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Inventory() {
  const [rows, setRows] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.products().then(setRows).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin />

  return (
    <Card title="库存 / 商品">
      <Table
        size="small"
        rowKey="id"
        dataSource={rows}
        pagination={{ pageSize: 20 }}
        columns={[
          { title: '编码', dataIndex: 'code', width: 100 },
          { title: '名称', dataIndex: 'name' },
          { title: '类别', dataIndex: 'category' },
          { title: '单位', dataIndex: 'unit', width: 70 },
          { title: '单价', dataIndex: 'unit_price', align: 'right', render: (v: number) => money(v) },
          { title: '数量', dataIndex: 'quantity', align: 'right', render: (v: number) => money(v) },
          { title: '金额', dataIndex: 'amount', align: 'right', render: (v: number) => money(v) },
        ]}
      />
    </Card>
  )
}
