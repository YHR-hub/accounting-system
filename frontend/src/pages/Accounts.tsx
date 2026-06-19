import { useEffect, useState } from 'react'
import { Card, Table, Tag, Spin, Button, Modal, Form, Input, Select, message, Popconfirm } from 'antd'
import { api, type AccountOut } from '../api'
import { useAuth } from '../auth'

const catLabel: Record<string, string> = {
  asset: '资产',
  liability: '负债',
  equity: '权益',
  income: '收入',
  expense: '费用',
}
const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Accounts() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'accountant'
  const [rows, setRows] = useState<AccountOut[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm()

  const load = () => {
    setLoading(true)
    api.accounts().then(setRows).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const onAdd = async () => {
    const v = await form.validateFields()
    try {
      await api.addAccount(v)
      message.success('科目已新增')
      setOpen(false)
      form.resetFields()
      load()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '新增失败')
    }
  }

  if (loading) return <Spin />

  const columns: any[] = [
    { title: '编码', dataIndex: 'code', width: 100 },
    { title: '名称', dataIndex: 'name' },
    { title: '类别', dataIndex: 'category', render: (c: string) => <Tag color="blue">{catLabel[c] || c}</Tag> },
    { title: '借方发生', dataIndex: 'debit', align: 'right', render: (v: number) => money(v) },
    { title: '贷方发生', dataIndex: 'credit', align: 'right', render: (v: number) => money(v) },
    { title: '余额', dataIndex: 'balance', align: 'right', render: (v: number) => money(v) },
  ]
  if (canWrite) {
    columns.push({
      title: '操作',
      key: 'op',
      render: (_: any, r: AccountOut) => (
        <Popconfirm
          title={`确认停用科目 ${r.name}？`}
          onConfirm={async () => {
            await api.deactivateAccount(r.code)
            message.success('已停用')
            load()
          }}
        >
          <Button size="small" danger>停用</Button>
        </Popconfirm>
      ),
    })
  }

  return (
    <Card title="科目余额表" extra={canWrite && <Button type="primary" onClick={() => setOpen(true)}>新增科目</Button>}>
      <Table
        size="small"
        rowKey="code"
        dataSource={rows}
        pagination={{ pageSize: 20 }}
        columns={columns}
      />
      <Modal open={open} title="新增科目" onOk={onAdd} onCancel={() => setOpen(false)} okText="创建">
        <Form form={form} layout="vertical" initialValues={{ category: 'asset' }}>
          <Form.Item name="code" label="编码" rules={[{ required: true }]}><Input placeholder="如 1601" /></Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="category" label="类别" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'asset', label: '资产' },
                { value: 'liability', label: '负债' },
                { value: 'equity', label: '权益' },
                { value: 'income', label: '收入' },
                { value: 'expense', label: '费用' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
