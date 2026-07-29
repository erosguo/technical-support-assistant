import React, { useEffect, useState } from 'react';
import {
  Button,
  Table,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Typography,
  Popconfirm,
  message,
} from 'antd';
import { PlusOutlined, DeleteOutlined, FileTextOutlined } from '@ant-design/icons';
import {
  listTickets,
  createTicket,
  updateTicket,
  deleteTicket,
  TicketListItem,
  CreateTicketRequest,
} from '../services/ticket';

const { Title } = Typography;

const priorityColor: Record<string, string> = {
  critical: 'red',
  high: 'orange',
  medium: 'gold',
  low: 'green',
};

export default function TicketPage() {
  const [tickets, setTickets] = useState<TicketListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const data = await listTickets();
      setTickets(data);
    } catch {
      message.error('获取工单列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const handleCreate = async (values: CreateTicketRequest) => {
    try {
      await createTicket(values);
      message.success('工单创建成功');
      setCreateOpen(false);
      form.resetFields();
      fetchTickets();
    } catch {
      message.error('工单创建失败');
    }
  };

  const handleStatusChange = async (id: string, status: string) => {
    try {
      await updateTicket(id, { status });
      message.success('状态已更新');
      fetchTickets();
    } catch {
      message.error('更新失败');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteTicket(id);
      message.success('工单已删除');
      fetchTickets();
    } catch {
      message.error('删除失败');
    }
  };

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: TicketListItem) => (
        <Select
          value={status}
          size="small"
          style={{ width: 120 }}
          onChange={(val) => handleStatusChange(record.id, val)}
          options={[
            { label: '待处理', value: 'open' },
            { label: '处理中', value: 'in_progress' },
            { label: '已解决', value: 'resolved' },
            { label: '已关闭', value: 'closed' },
          ]}
        />
      ),
      filters: [
        { text: '待处理', value: 'open' },
        { text: '处理中', value: 'in_progress' },
        { text: '已解决', value: 'resolved' },
        { text: '已关闭', value: 'closed' },
      ],
      onFilter: (value: boolean | React.Key, record: TicketListItem) => record.status === value,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (p: string) => <Tag color={priorityColor[p]}>{p}</Tag>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (t: string) => new Date(t).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: TicketListItem) => (
        <Popconfirm
          title="确定删除此工单？"
          onConfirm={() => handleDelete(record.id)}
        >
          <Button type="link" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: '0 auto' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Title level={4} style={{ margin: 0 }}>
          <FileTextOutlined /> 工单管理
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateOpen(true)}
        >
          新建工单
        </Button>
      </div>

      <Table
        dataSource={tickets}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="新建工单"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入工单标题' }]}
          >
            <Input placeholder="工单标题" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="问题描述" />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="medium">
            <Select
              options={[
                { label: '低', value: 'low' },
                { label: '中', value: 'medium' },
                { label: '高', value: 'high' },
                { label: '紧急', value: 'critical' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
