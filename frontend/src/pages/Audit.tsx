import { useEffect, useState } from 'react'
import { Card, Table, Spin } from 'antd'
import { api, type AuditLog } from '../api'

export default function Audit() {
  const [rows, setRows] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.audit().then(setRows).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin />

  return (
    <Card title="审计日志">
      <Table
        size="small"
        rowKey="id"
        dataSource={rows}
        pagination={{ pageSize: 20 }}
        columns={[
          { title: '时间', dataIndex: 'created_at', width: 180 },
          { title: '用户', dataIndex: 'username', width: 120 },
          { title: '操作', dataIndex: 'action' },
          { title: '对象类型', dataIndex: 'target_type' },
          { title: '对象', dataIndex: 'target_id' },
          { title: '详情', dataIndex: 'detail' },
        ]}
      />
    </Card>
  )
}
