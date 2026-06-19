import { useEffect, useState } from 'react'
import { Card, Table, Spin } from 'antd'
import { api, type Employee } from '../api'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Employees() {
  const [rows, setRows] = useState<Employee[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.employees().then(setRows).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin />

  return (
    <Card title="员工">
      <Table
        size="small"
        rowKey="id"
        dataSource={rows}
        pagination={{ pageSize: 20 }}
        columns={[
          { title: '工号', dataIndex: 'code', width: 100 },
          { title: '姓名', dataIndex: 'name' },
          { title: '部门', dataIndex: 'department' },
          { title: '岗位', dataIndex: 'position' },
          { title: '基本工资', dataIndex: 'base_salary', align: 'right', render: (v: number) => money(v) },
          { title: '社保', dataIndex: 'insurance', align: 'right', render: (v: number) => money(v) },
          { title: '公积金', dataIndex: 'housing_fund', align: 'right', render: (v: number) => money(v) },
        ]}
      />
    </Card>
  )
}
