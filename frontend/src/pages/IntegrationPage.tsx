import { useState } from 'react';
import { Tabs, Form, Input, Select, Button, Card, message, Space, Divider, Tag } from 'antd';
import { ApiOutlined, BellOutlined } from '@ant-design/icons';
import { syncTicketToExternal } from '../services/external';
import { sendNotification, sendEscalation } from '../services/notification';

const { TextArea } = Input;

export default function IntegrationPage() {
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncResult, setSyncResult] = useState<{ external_id: string; provider: string; url: string } | null>(null);
  const [syncForm] = Form.useForm();

  const [notifyLoading, setNotifyLoading] = useState(false);
  const [notifyResult, setNotifyResult] = useState<{ success: boolean; message: string } | null>(null);
  const [notifyForm] = Form.useForm();

  const [escalationLoading, setEscalationLoading] = useState(false);
  const [escalationResult, setEscalationResult] = useState<{ success: boolean; message: string } | null>(null);
  const [escalationForm] = Form.useForm();

  const handleSync = async () => {
    try {
      const values = await syncForm.validateFields();
      setSyncLoading(true);
      setSyncResult(null);
      const result = await syncTicketToExternal(values.ticket_id, values.provider, values.config);
      setSyncResult(result);
      message.success('同步成功');
    } catch {
      message.error('同步失败');
    } finally {
      setSyncLoading(false);
    }
  };

  const handleSend = async () => {
    try {
      const values = await notifyForm.validateFields();
      setNotifyLoading(true);
      setNotifyResult(null);
      const result = await sendNotification(values.provider, values.webhook_url, values.title, values.content);
      setNotifyResult(result);
      message.success('通知发送成功');
    } catch {
      message.error('通知发送失败');
    } finally {
      setNotifyLoading(false);
    }
  };

  const handleEscalation = async () => {
    try {
      const values = await escalationForm.validateFields();
      setEscalationLoading(true);
      setEscalationResult(null);
      const result = await sendEscalation(values.provider, values.webhook_url, values.ticket_title, values.ticket_description);
      setEscalationResult(result);
      message.success('升级通知发送成功');
    } catch {
      message.error('升级通知发送失败');
    } finally {
      setEscalationLoading(false);
    }
  };

  const externalTab = (
    <div style={{ padding: '16px 0' }}>
      <Card title="外部工单同步" style={{ maxWidth: 600 }}>
        <Form form={syncForm} layout="vertical">
          <Form.Item label="工单 ID" name="ticket_id" rules={[{ required: true, message: '请输入工单 ID' }]}>
            <Input placeholder="T-12345" />
          </Form.Item>
          <Form.Item label="外部服务商" name="provider" rules={[{ required: true, message: '请选择服务商' }]}>
            <Select
              options={[
                { label: 'Jira', value: 'jira' },
                { label: 'Zendesk', value: 'zendesk' },
                { label: 'ServiceNow', value: 'servicenow' },
              ]}
            />
          </Form.Item>
          <Form.Item label="配置 (可选)" name="config" tooltip="JSON 格式的服务商配置">
            <TextArea rows={3} placeholder='{"project_key": "PROJ"}' />
          </Form.Item>
          <Form.Item>
            <Button type="primary" loading={syncLoading} onClick={handleSync}>
              同步工单
            </Button>
          </Form.Item>
        </Form>
        {syncResult && (
          <div>
            <Divider />
            <div style={{ marginBottom: 8, fontWeight: 600 }}>同步结果：</div>
            <Space direction="vertical">
              <Tag color="green">成功</Tag>
              <div>外部 ID: {syncResult.external_id}</div>
              <div>服务商: {syncResult.provider}</div>
              <a href={syncResult.url} target="_blank" rel="noreferrer">{syncResult.url}</a>
            </Space>
          </div>
        )}
      </Card>
    </div>
  );

  const notificationTab = (
    <div style={{ padding: '16px 0' }}>
      <Card title="发送 IM 通知" style={{ maxWidth: 600, marginBottom: 16 }}>
        <Form form={notifyForm} layout="vertical">
          <Form.Item label="IM 服务商" name="provider" rules={[{ required: true, message: '请选择服务商' }]}>
            <Select
              options={[
                { label: '飞书', value: 'feishu' },
                { label: '钉钉', value: 'dingtalk' },
                { label: 'Slack', value: 'slack' },
              ]}
            />
          </Form.Item>
          <Form.Item label="Webhook URL" name="webhook_url" rules={[{ required: true, message: '请输入 Webhook URL' }]}>
            <Input placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
          </Form.Item>
          <Form.Item label="标题" name="title" rules={[{ required: true, message: '请输入通知标题' }]}>
            <Input placeholder="通知标题" />
          </Form.Item>
          <Form.Item label="内容" name="content" rules={[{ required: true, message: '请输入通知内容' }]}>
            <TextArea rows={4} placeholder="通知内容" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" loading={notifyLoading} onClick={handleSend}>
              发送通知
            </Button>
          </Form.Item>
        </Form>
        {notifyResult && (
          <>
            <Divider />
            <Tag color={notifyResult.success ? 'green' : 'red'}>
              {notifyResult.success ? '发送成功' : '发送失败'}
            </Tag>
            <div>{notifyResult.message}</div>
          </>
        )}
      </Card>

      <Card title="升级通知" style={{ maxWidth: 600 }}>
        <Form form={escalationForm} layout="vertical">
          <Form.Item label="IM 服务商" name="provider" rules={[{ required: true, message: '请选择服务商' }]}>
            <Select
              options={[
                { label: '飞书', value: 'feishu' },
                { label: '钉钉', value: 'dingtalk' },
                { label: 'Slack', value: 'slack' },
              ]}
            />
          </Form.Item>
          <Form.Item label="Webhook URL" name="webhook_url" rules={[{ required: true, message: '请输入 Webhook URL' }]}>
            <Input placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
          </Form.Item>
          <Form.Item label="工单标题" name="ticket_title" rules={[{ required: true, message: '请输入工单标题' }]}>
            <Input placeholder="需要升级的工单标题" />
          </Form.Item>
          <Form.Item label="工单描述" name="ticket_description" rules={[{ required: true, message: '请输入工单描述' }]}>
            <TextArea rows={3} placeholder="工单详细描述" />
          </Form.Item>
          <Form.Item>
            <Button danger loading={escalationLoading} onClick={handleEscalation}>
              发送升级通知
            </Button>
          </Form.Item>
        </Form>
        {escalationResult && (
          <>
            <Divider />
            <Tag color={escalationResult.success ? 'green' : 'red'}>
              {escalationResult.success ? '升级通知已发送' : '升级通知发送失败'}
            </Tag>
            <div>{escalationResult.message}</div>
          </>
        )}
      </Card>
    </div>
  );

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Tabs
          items={[
            {
              key: 'external',
              label: <span><ApiOutlined /> 外部工单集成</span>,
              children: externalTab,
            },
            {
              key: 'notification',
              label: <span><BellOutlined /> IM 通知</span>,
              children: notificationTab,
            },
          ]}
        />
      </Card>
    </div>
  );
}