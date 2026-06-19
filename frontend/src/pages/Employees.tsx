import { useEffect, useState } from 'react'
import { Card, Table, Spin, Button, Modal, Form, Input, InputNumber, message } from 'antd'
import { api, type Employee } from '../api'
import { useAuth } from '../auth'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Employees() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'accountant'
  const [rows, setRows] = useState<Employee[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm()

  const load = () => {
    setLoading(true)
    api.employees().then(setRows).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const onAdd = async () => {
    const v = await form.validateFields()
    try {
      await api.addEmployee(v)
      message.success('员工已新增')
      setOpen(false)
      form.resetFields()
      load()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '新增失败')
    }
  }

  if (loading) return <Spin />

  return (
    <Card title="员工" extra={canWrite && <Button type="primary" onClick={() => setOpen(true)}>新增员工</Button>}>
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
      <Modal open={open} title="新增员工" onOk={onAdd} onCancel={() => setOpen(false)} okText="创建">
        <Form form={form} layout="vertical" initialValues={{ base_salary: 0, insurance: 0, housing_fund: 0 }}>
          <Form.Item name="code" label="工号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="name" label="姓名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="department" label="部门"><Input /></Form.Item>
          <Form.Item name="position" label="岗位"><Input /></Form.Item>
          <Form.Item name="base_salary" label="基本工资"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
          <Form.Item name="insurance" label="社保"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
          <Form.Item name="housing_fund" label="公积金"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
