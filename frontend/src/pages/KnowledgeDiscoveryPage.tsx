import { useState } from 'react';
import { Card, Button, Table, Tag, Space, message } from 'antd';
import { ExperimentOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { discoverKnowledge } from '../services/admin';

interface DiscoveredPattern {
  id: string;
  pattern: string;
  solution: string;
  severity: string;
  category: string;
  created_at: string;
}

const severityColor: Record<string, string> = {
  critical: 'red',
  high: 'orange',
  medium: 'gold',
  low: 'green',
};

export default function KnowledgeDiscoveryPage() {
  const [loading, setLoading] = useState(false);
  const [patterns, setPatterns] = useState<DiscoveredPattern[]>([]);

  const handleDiscover = async () => {
    setLoading(true);
    try {
      const result = await discoverKnowledge();
      setPatterns(result.patterns || []);
      message.success(`发现 ${result.patterns?.length || 0} 条新模式`);
    } catch {
      message.error('知识发现失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '模式', dataIndex: 'pattern', key: 'pattern', width: 200 },
    { title: '解决方案', dataIndex: 'solution', key: 'solution' },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (s: string) => <Tag color={severityColor[s] || 'default'}>{s}</Tag>,
    },
    { title: '分类', dataIndex: 'category', key: 'category', width: 120 },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (t: string) => new Date(t).toLocaleString('zh-CN'),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={<span><ExperimentOutlined /> 知识发现</span>}
        extra={
          <Space>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              loading={loading}
              onClick={handleDiscover}
            >
              开始发现
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={patterns}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
}