import { useState } from 'react';
import {
  Button,
  Input,
  Typography,
  Card,
  Tag,
  List,
  Space,
  Empty,
  Alert,
} from 'antd';
import {
  BugOutlined,
  SafetyCertificateOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { diagnose, DiagnosisResult } from '../services/diagnosis';

const { Text, Title } = Typography;
const { TextArea } = Input;

const severityColor: Record<string, string> = {
  critical: 'red',
  high: 'orange',
  medium: 'gold',
  low: 'green',
};

export default function DiagnosisPage() {
  const [errorText, setErrorText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiagnosisResult | null>(null);

  const handleDiagnose = async () => {
    if (!errorText.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await diagnose(errorText);
      setResult(data);
    } catch {
      setResult({
        reply: '诊断服务暂时不可用，请稍后重试。',
        matches: [],
        needs_escalation: false,
        conversation_id: null,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24, maxWidth: 800, margin: '0 auto' }}>
      <Title level={4}>
        <BugOutlined /> 故障诊断
      </Title>

      <div style={{ marginBottom: 16 }}>
        <Text type="secondary">
          请输入错误信息或故障描述，系统将自动匹配已知错误模式并给出诊断建议。
        </Text>
      </div>

      <TextArea
        rows={4}
        placeholder="例如：Connection refused on port 8080, ERR_500 服务器内部错误..."
        value={errorText}
        onChange={(e) => setErrorText(e.target.value)}
        style={{ marginBottom: 12 }}
      />

      <Button
        type="primary"
        icon={<SafetyCertificateOutlined />}
        onClick={handleDiagnose}
        loading={loading}
        size="large"
      >
        开始诊断
      </Button>

      {result && (
        <div style={{ marginTop: 24 }}>
          <Card title="诊断结果" style={{ marginBottom: 16 }}>
            <div style={{ whiteSpace: 'pre-wrap' }}>{result.reply}</div>
            {result.needs_escalation && (
              <Alert
                style={{ marginTop: 12 }}
                message="建议升级处理"
                description="当前问题严重度较高，建议转交 L2/L3 工程师处理。"
                type="warning"
                showIcon
              />
            )}
          </Card>

          {result.matches.length > 0 ? (
            <>
              <Title level={5}>
                <WarningOutlined /> 匹配模式 ({result.matches.length})
              </Title>
              <List
                dataSource={result.matches}
                renderItem={(m) => (
                  <List.Item>
                    <Card
                      size="small"
                      style={{ width: '100%' }}
                      title={
                        <Space>
                          <Tag color={severityColor[m.severity] || 'default'}>
                            {m.severity}
                          </Tag>
                          <Text code>{m.pattern}</Text>
                        </Space>
                      }
                    >
                      {m.solution && (
                        <p>
                          <Text strong>解决方案：</Text>
                          {m.solution}
                        </p>
                      )}
                      <Space>
                        {m.category && <Tag>{m.category}</Tag>}
                        {m.tags.map((t, i) => (
                          <Tag key={i}>{t}</Tag>
                        ))}
                      </Space>
                    </Card>
                  </List.Item>
                )}
              />
            </>
          ) : (
            <Empty description="未匹配已知错误模式，以上为通用排查建议。" />
          )}
        </div>
      )}
    </div>
  );
}
