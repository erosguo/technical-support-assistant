import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Spin, message } from 'antd';
import { MessageOutlined, FileTextOutlined, FileOutlined, ReadOutlined } from '@ant-design/icons';
import { getSystemStats, SystemStats } from '../services/admin';

export default function DashboardPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await getSystemStats();
        setStats(data);
      } catch {
        message.error('加载统计数据失败');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <Spin spinning={loading}>
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总会话数"
                value={stats?.total_conversations ?? 0}
                prefix={<MessageOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总消息数"
                value={stats?.total_messages ?? 0}
                prefix={<ReadOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总文档数"
                value={stats?.total_documents ?? 0}
                prefix={<FileOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总工单数"
                value={stats?.total_tickets ?? 0}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {stats && (
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={12}>
              <Card title="工单状态分布">
                {Object.entries(stats.tickets_by_status).map(([status, count]) => (
                  <Statistic
                    key={status}
                    title={status}
                    value={count}
                    style={{ marginBottom: 8 }}
                  />
                ))}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="用户角色分布">
                {Object.entries(stats.users_by_role).map(([role, count]) => (
                  <Statistic
                    key={role}
                    title={role}
                    value={count}
                    style={{ marginBottom: 8 }}
                  />
                ))}
              </Card>
            </Col>
          </Row>
        )}
      </Spin>
    </div>
  );
}