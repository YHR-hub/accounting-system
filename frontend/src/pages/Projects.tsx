import { useEffect, useState } from 'react'
import { Card, Table, Tag, Spin, Button, Modal, Form, Input, InputNumber, DatePicker, message } from 'antd'
import { api, type Project } from '../api'
import { useAuth } from '../auth'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const statusLabel: Record<string, string> = {
  active: '进行中',
  completed: '已完成',
  suspended: '已暂停',
}

export default function Projects() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'accountant'
  const [rows, setRows] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm()

  const load = () => {
    setLoading(true)
    api.projects().then(setRows).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const onAdd = async () => {
    const v = await form.validateFields()
    try {
      await api.addProject({
        code: v.code,
        name: v.name,
        budget: v.budget,
        start_date: v.start_date ? v.start_date.format('YYYY-MM-DD') : null,
        end_date: v.end_date ? v.end_date.format('YYYY-MM-DD') : null,
      })
      message.success('项目已新增')
      setOpen(false)
      form.resetFields()
      load()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '新增失败')
    }
  }

  if (loading) return <Spin />

  return (
    <Card title="项目" extra={canWrite && <Button type="primary" onClick={() => setOpen(true)}>新增项目</Button>}>
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
      <Modal open={open} title="新增项目" onOk={onAdd} onCancel={() => setOpen(false)} okText="创建">
        <Form form={form} layout="vertical" initialValues={{ budget: 0 }}>
          <Form.Item name="code" label="编码" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="budget" label="预算"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
          <Form.Item name="start_date" label="开始日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="end_date" label="结束日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
