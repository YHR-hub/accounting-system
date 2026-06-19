import { useEffect, useState } from 'react'
import { Card, Table, Spin, Button, Modal, Form, Input, InputNumber, DatePicker, Select, message } from 'antd'
import dayjs from 'dayjs'
import { api, type FixedAsset } from '../api'
import { useAuth } from '../auth'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Assets() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'accountant'
  const [rows, setRows] = useState<FixedAsset[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm()

  const load = () => {
    setLoading(true)
    api.assets().then(setRows).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const onAdd = async () => {
    const v = await form.validateFields()
    try {
      await api.addAsset({
        name: v.name,
        original_value: v.original_value,
        residual_value: v.residual_value,
        useful_life_months: v.useful_life_months,
        depreciation_method: v.depreciation_method,
        purchase_date: v.purchase_date.format('YYYY-MM-DD'),
      })
      message.success('固定资产已新增')
      setOpen(false)
      form.resetFields()
      load()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '新增失败')
    }
  }

  if (loading) return <Spin />

  return (
    <Card title="固定资产" extra={canWrite && <Button type="primary" onClick={() => setOpen(true)}>新增固定资产</Button>}>
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
      <Modal open={open} title="新增固定资产" onOk={onAdd} onCancel={() => setOpen(false)} okText="创建">
        <Form
          form={form}
          layout="vertical"
          initialValues={{ residual_value: 0, useful_life_months: 60, depreciation_method: 'straight', purchase_date: dayjs() }}
        >
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="original_value" label="原值" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} />
          </Form.Item>
          <Form.Item name="residual_value" label="残值"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
          <Form.Item name="useful_life_months" label="使用年限(月)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={1} />
          </Form.Item>
          <Form.Item name="depreciation_method" label="折旧方法">
            <Select
              options={[
                { value: 'straight', label: '年限平均法' },
                { value: 'double', label: '双倍余额递减' },
                { value: 'sum-of-years', label: '年数总和法' },
              ]}
            />
          </Form.Item>
          <Form.Item name="purchase_date" label="购入日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
