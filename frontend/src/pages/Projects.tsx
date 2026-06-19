import { useEffect, useState } from 'react'
import { Card, Table, Tag, Spin } from 'antd'
import { api, type Project } from '../api'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const statusLabel: Record<string, string> = {
  active: '进行中',
  completed: '已完成',
  suspended: '已暂停',
}

export default function Projects() {
  const [rows, setRows] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.projects().then(setRows).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin />

  return (
    <Card title="项目">
      <Table
        size="small"
        rowKey="id"
        dataSource={rows}
        pagination={{ pageSize: 20 }}
        columns={[
          { title: '编码', dataIndex: 'code', width: 120 },
          { title: '名称', dataIndex: 'name' },
          { title: '预算', dataIndex: 'budget', align: 'right', render: (v: number) => money(v) },
          { title: '开始', dataIndex: 'start_date' },
          { title: '结束', dataIndex: 'end_date' },
          {
            title: '状态',
            dataIndex: 'status',
            render: (s: string) => <Tag color="blue">{statusLabel[s] || s}</Tag>,
          },
        ]}
      />
    </Card>
  )
}
