import { useEffect, useState } from 'react'
import { Card, Table, Spin, Button, Modal, Form, Input, InputNumber, message, Space } from 'antd'
import { api, type Product } from '../api'
import { useAuth } from '../auth'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Inventory() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'accountant'
  const [rows, setRows] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [addOpen, setAddOpen] = useState(false)
  const [moveOpen, setMoveOpen] = useState<{ type: 'in' | 'out'; product: Product } | null>(null)
  const [addForm] = Form.useForm()
  const [moveForm] = Form.useForm()

  const load = () => {
    setLoading(true)
    api.products().then(setRows).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const onAdd = async () => {
    const v = await addForm.validateFields()
    try {
      await api.createProduct(v)
      message.success('商品已新增')
      setAddOpen(false)
      addForm.resetFields()
      load()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '新增失败')
    }
  }

  const onMove = async () => {
    if (!moveOpen) return
    const v = await moveForm.validateFields()
    try {
      if (moveOpen.type === 'in') {
        await api.inventoryIn({ product_id: moveOpen.product.id, quantity: v.quantity, unit_price: v.unit_price })
      } else {
        await api.inventoryOut({ product_id: moveOpen.product.id, quantity: v.quantity })
      }
      message.success(moveOpen.type === 'in' ? '入库成功' : '出库成功')
      setMoveOpen(null)
      moveForm.resetFields()
      load()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '操作失败')
    }
  }

  if (loading) return <Spin />

  const columns: any[] = [
    { title: '编码', dataIndex: 'code', width: 100 },
    { title: '名称', dataIndex: 'name' },
    { title: '类别', dataIndex: 'category' },
    { title: '单位', dataIndex: 'unit', width: 70 },
    { title: '单价', dataIndex: 'unit_price', align: 'right', render: (v: number) => money(v) },
    { title: '数量', dataIndex: 'quantity', align: 'right', render: (v: number) => money(v) },
    { title: '金额', dataIndex: 'amount', align: 'right', render: (v: number) => money(v) },
  ]
  if (canWrite) {
    columns.push({
      title: '操作',
      key: 'op',
      render: (_: any, r: Product) => (
        <Space>
          <Button size="small" onClick={() => setMoveOpen({ type: 'in', product: r })}>入库</Button>
          <Button size="small" onClick={() => setMoveOpen({ type: 'out', product: r })}>出库</Button>
        </Space>
      ),
    })
  }

  return (
    <Card title="库存 / 商品" extra={canWrite && <Button type="primary" onClick={() => setAddOpen(true)}>新增商品</Button>}>
      <Table size="small" rowKey="id" dataSource={rows} columns={columns} pagination={{ pageSize: 20 }} />

      <Modal open={addOpen} title="新增商品" onOk={onAdd} onCancel={() => setAddOpen(false)} okText="创建">
        <Form form={addForm} layout="vertical" initialValues={{ unit: '个', unit_price: 0, quantity: 0 }}>
          <Form.Item name="code" label="编码" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="category" label="类别"><Input /></Form.Item>
          <Form.Item name="unit" label="单位"><Input /></Form.Item>
          <Form.Item name="unit_price" label="单价"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
          <Form.Item name="quantity" label="初始数量"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
        </Form>
      </Modal>

      <Modal
        open={!!moveOpen}
        title={moveOpen?.type === 'in' ? `入库 - ${moveOpen?.product.name}` : `出库 - ${moveOpen?.product.name}`}
        onOk={onMove}
        onCancel={() => setMoveOpen(null)}
        okText="确认"
      >
        <Form form={moveForm} layout="vertical">
          <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} />
          </Form.Item>
          {moveOpen?.type === 'in' && (
            <Form.Item name="unit_price" label="入库单价（可选）">
              <InputNumber style={{ width: '100%' }} min={0} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </Card>
  )
}
