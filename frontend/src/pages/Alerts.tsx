import { useEffect, useState } from 'react'
import { Card, Table, Tabs, Tag, Spin } from 'antd'
import { api, type AlertRule, type AlertHistory } from '../api'

const levelColor: Record<string, string> = { info: 'blue', warning: 'orange', critical: 'red' }

export default function Alerts() {
  const [rules, setRules] = useState<AlertRule[]>([])
  const [history, setHistory] = useState<AlertHistory[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.alertRules(), api.alertHistory()])
      .then(([r, h]) => {
        setRules(r)
        setHistory(h)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin />

  return (
    <Card>
      <Tabs
        items={[
          {
            key: 'rules',
            label: '预警规则',
            children: (
              <Table
                size="small"
                rowKey="id"
                dataSource={rules}
                pagination={false}
                columns={[
                  { title: '名称', dataIndex: 'name' },
                  { title: '指标', dataIndex: 'indicator' },
                  { title: '运算', dataIndex: 'operator', width: 80 },
                  { title: '阈值', dataIndex: 'threshold', align: 'right' },
                  { title: '级别', dataIndex: 'level', render: (l: string) => <Tag color={levelColor[l] || 'default'}>{l}</Tag> },
                  { title: '启用', dataIndex: 'enabled', render: (v: number) => (v ? '是' : '否') },
                ]}
              />
            ),
          },
          {
            key: 'history',
            label: '预警历史',
            children: (
              <Table
                size="small"
                rowKey="id"
                dataSource={history}
                pagination={{ pageSize: 20 }}
                columns={[
                  { title: '时间', dataIndex: 'created_at', width: 180 },
                  { title: '消息', dataIndex: 'message' },
                  { title: '级别', dataIndex: 'level', render: (l: string) => <Tag color={levelColor[l] || 'default'}>{l}</Tag> },
                  { title: '已处理', dataIndex: 'resolved', render: (v: number) => (v ? '是' : '否') },
                ]}
              />
            ),
          },
        ]}
      />
    </Card>
  )
}
