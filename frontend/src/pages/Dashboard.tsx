import { useEffect, useState } from 'react'
import { Card, Col, Row, Statistic, Table, Spin } from 'antd'
import { api, type AccountOut } from '../api'

export default function Dashboard() {
  const [ratios, setRatios] = useState<Record<string, number>>({})
  const [accts, setAccts] = useState<AccountOut[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.ratios(), api.accounts()])
      .then(([r, a]) => {
        setRatios(r)
        setAccts(a)
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
    </>
  )
}
