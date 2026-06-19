import { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  DatePicker,
  InputNumber,
  message,
  Popconfirm,
  Space,
  Descriptions,
} from 'antd'
import dayjs from 'dayjs'
import { api, type VoucherOut, type VoucherDetail } from '../api'
import { useAuth } from '../auth'

const money = (v: number) =>
  v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function Vouchers() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'accountant'
  const [rows, setRows] = useState<VoucherOut[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [detail, setDetail] = useState<VoucherDetail | null>(null)
  const [form] = Form.useForm()

  const load = () => {
    setLoading(true)
    api.vouchers(2026, 0).then(setRows).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const showDetail = async (id: number) => {
    try {
      setDetail(await api.voucherDetail(id))
    } catch {
      message.error('加载明细失败')
    }
  }

  const onCreate = async () => {
    const v = await form.validateFields()
    const entries = [
      { account_code: v.debit_acc, debit: v.amount, credit: 0 },
      { account_code: v.credit_acc, debit: 0, credit: v.amount },
    ]
    try {
      await api.createVoucher({ date: v.date.format('YYYY-MM-DD'), summary: v.summary, entries })
      message.success('凭证已创建')
      setOpen(false)
      form.resetFields()
      load()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '创建失败')
    }
  }

  const columns: any[] = [
    { title: '凭证号', dataIndex: 'voucher_no' },
    { title: '日期', dataIndex: 'date' },
    { title: '摘要', dataIndex: 'summary' },
    { title: '金额', dataIndex: 'total', align: 'right', render: (v: number) => money(v) },
    {
      title: '操作',
      key: 'op',
      render: (_: any, r: VoucherOut) => (
        <Space>
          <Button size="small" onClick={() => showDetail(r.id)}>详情</Button>
          {canWrite && (
            <Popconfirm
              title="确认删除该凭证？"
              onConfirm={async () => {
                await api.deleteVoucher(r.id)
                message.success('已删除')
                load()
              }}
            >
              <Button size="small" danger>删除</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Card title="凭证列表" extra={canWrite && <Button type="primary" onClick={() => setOpen(true)}>新增凭证</Button>}>
      <Table size="small" rowKey="id" loading={loading} dataSource={rows} columns={columns} pagination={{ pageSize: 15 }} />

      <Modal open={open} title="新增凭证（简易：一借一贷）" onOk={onCreate} onCancel={() => setOpen(false)} okText="创建">
        <Form form={form} layout="vertical" initialValues={{ date: dayjs() }}>
          <Form.Item name="date" label="日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="summary" label="摘要" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="debit_acc" label="借方科目编码" rules={[{ required: true }]}>
            <Input placeholder="如 1002（银行存款）" />
          </Form.Item>
          <Form.Item name="credit_acc" label="贷方科目编码" rules={[{ required: true }]}>
            <Input placeholder="如 6001（主营业务收入）" />
          </Form.Item>
          <Form.Item name="amount" label="金额" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal open={!!detail} title={`凭证明细 ${detail?.voucher_no || ''}`} footer={null} onCancel={() => setDetail(null)} width={640}>
        {detail && (
          <>
            <Descriptions size="small" column={2} style={{ marginBottom: 12 }}>
              <Descriptions.Item label="日期">{detail.date}</Descriptions.Item>
              <Descriptions.Item label="摘要">{detail.summary}</Descriptions.Item>
            </Descriptions>
            <Table
              size="small"
              rowKey={(_, i) => String(i)}
              dataSource={detail.entries}
              pagination={false}
              columns={[
                { title: '科目', render: (_: any, e: any) => `${e.account_code} ${e.account_name}` },
                { title: '借方', dataIndex: 'debit', align: 'right', render: (v: number) => (v ? money(v) : '') },
                { title: '贷方', dataIndex: 'credit', align: 'right', render: (v: number) => (v ? money(v) : '') },
              ]}
              summary={(data) => {
                const d = data.reduce((s, e) => s + e.debit, 0)
                const c = data.reduce((s, e) => s + e.credit, 0)
                return (
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0}><b>合计</b></Table.Summary.Cell>
                    <Table.Summary.Cell index={1} align="right"><b>{money(d)}</b></Table.Summary.Cell>
                    <Table.Summary.Cell index={2} align="right"><b>{money(c)}</b></Table.Summary.Cell>
                  </Table.Summary.Row>
                )
              }}
            />
          </>
        )}
      </Modal>
    </Card>
  )
}
