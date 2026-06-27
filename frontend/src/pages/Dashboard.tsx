import { useEffect, useState } from 'react'
import { Card, Col, Row, Statistic, Table, Spin, Input, Button } from 'antd'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { api, type AccountOut, type TrendPoint } from '../api'

export default function Dashboard() {
  const [ratios, setRatios] = useState<Record<string, number>>({})
  const [accts, setAccts] = useState<AccountOut[]>([])
  const [trend, setTrend] = useState<TrendPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [aiQ, setAiQ] = useState('')
  const [aiA, setAiA] = useState('')
  const [aiLoading, setAiLoading] = useState(false)

  useEffect(() => {
    Promise.all([api.ratios(), api.accounts(), api.trend(2026)])
      .then(([r, a, t]) => {
        setRatios(r)
        setAccts(a)
        setTrend(t)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin />

  const sumBy = (cat: string) =>
    accts.filter((a) => a.category === cat).reduce((s, a) => s + a.balance, 0)
  const assets = sumBy('asset')
  const liab = sumBy('liability')
  const ratioData = Object.entries(ratios).map(([k, v], i) => ({ key: i, name: k, value: v }))

  return (
    <>
      <Row gutter={16}>
        <Col span={8}>
          <Card>
            <Statistic title="总资产" value={assets} precision={2} valueStyle={{ color: '#6c5ce7' }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="总负债" value={liab} precision={2} valueStyle={{ color: '#d63031' }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="净资产"
              value={assets - liab}
              precision={2}
              valueStyle={{ color: '#00b894' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="月度收支趋势" style={{ marginTop: 16 }}>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={trend} margin={{ top: 8, right: 24, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="revenue" name="收入" stroke="#6c5ce7" strokeWidth={2} />
            <Line type="monotone" dataKey="expense" name="支出" stroke="#d63031" strokeWidth={2} />
            <Line type="monotone" dataKey="profit" name="利润" stroke="#00b894" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card title="财务比率" style={{ marginTop: 16 }}>
        <Table
          size="small"
          pagination={false}
          dataSource={ratioData}
          columns={[
            { title: '指标', dataIndex: 'name' },
            { title: '数值', dataIndex: 'value', align: 'right' },
          ]}
        />
      </Card>
      <Card title="💬 AI 财务问答" style={{ marginTop: 16 }}>
        <Input.TextArea
          value={aiQ}
          onChange={(e) => setAiQ(e.target.value)}
          placeholder="用自然语言问财务数据，如：今年收入最高的科目是哪些？"
          rows={2}
          style={{ marginBottom: 8 }}
        />
        <Button
          type="primary"
          loading={aiLoading}
          onClick={async () => {
            setAiLoading(true)
            try {
              const res = await api.aiQuery(aiQ)
              setAiA(res.result)
            } catch {
              setAiA('查询失败')
            }
            setAiLoading(false)
          }}
        >
          提问
        </Button>
        {aiA && (
          <pre style={{ whiteSpace: 'pre-wrap', marginTop: 12, background: '#f5f6fa', padding: 12, borderRadius: 6 }}>
            {aiA}
          </pre>
        )}
      </Card>
    </>
  )
}
