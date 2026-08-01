import { useState, useEffect, useCallback } from 'react';
import { Table, Button, Modal, Form, Input, Space, Tag, Popconfirm, message, Card, Row, Col, Empty } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ThunderboltOutlined, ArrowRightOutlined } from '@ant-design/icons';
import {
  listFlows,
  createFlow,
  updateFlow,
  deleteFlow,
  activateFlow,
  DiagnosisFlow,
  FlowStep,
} from '../services/diagnosisFlow';

const { TextArea } = Input;

export default function DiagnosisFlowPage() {
  const [flows, setFlows] = useState<DiagnosisFlow[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<DiagnosisFlow | null>(null);
  const [form] = Form.useForm();
  const [steps, setSteps] = useState<FlowStep[]>([]);

  const loadFlows = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listFlows();
      setFlows(data);
    } catch {
      message.error('加载诊断流程失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFlows();
  }, [loadFlows]);

  const openCreate = () => {
    setEditing(null);
    setSteps([{ id: 's1', title: '', description: '', conditions: [], next_step: null }]);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (flow: DiagnosisFlow) => {
    setEditing(flow);
    setSteps(flow.steps || []);
    form.setFieldsValue({ name: flow.name, description: flow.description });
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const payload = { ...values, steps };
      if (editing) {
        await updateFlow(editing.id, payload);
        message.success('更新成功');
      } else {
        await createFlow(payload);
        message.success('创建成功');
      }
      setModalOpen(false);
      loadFlows();
    } catch {
      message.error('保存失败');
    }
  };

  const handleDelete = async (id: string) => {
    await deleteFlow(id);
    message.success('删除成功');
    loadFlows();
  };

  const handleActivate = async (id: string) => {
    await activateFlow(id);
    message.success('激活成功');
    loadFlows();
  };

  const addStep = () => {
    setSteps([...steps, { id: `s${steps.length + 1}`, title: '', description: '', conditions: [], next_step: null }]);
  };

  const updateStep = (index: number, field: keyof FlowStep, value: any) => {
    const updated = [...steps];
    (updated[index] as any)[field] = value;
    setSteps(updated);
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index));
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '版本', dataIndex: 'version', key: 'version', width: 80 },
    { title: '步骤数', key: 'steps', width: 80, render: (_: any, r: DiagnosisFlow) => r.steps?.length || 0 },
    {
      title: '状态',
      key: 'is_active',
      width: 100,
      render: (_: any, r: DiagnosisFlow) =>
        r.is_active ? <Tag color="green">已激活</Tag> : <Tag>未激活</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 240,
      render: (_: any, r: DiagnosisFlow) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(r)}>编辑</Button>
          {!r.is_active && (
            <Button size="small" type="primary" ghost icon={<ThunderboltOutlined />} onClick={() => handleActivate(r.id)}>
              激活
            </Button>
          )}
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="诊断流程管理"
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建流程</Button>}
      >
        <Table dataSource={flows} columns={columns} rowKey="id" loading={loading} />
      </Card>

      <Modal
        title={editing ? '编辑流程' : '新建流程'}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        width={700}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item label="流程名称" name="name" rules={[{ required: true, message: '请输入流程名称' }]}>
            <Input placeholder="如：SSL 证书诊断流程" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <TextArea rows={2} placeholder="流程描述" />
          </Form.Item>
        </Form>

        <div style={{ marginBottom: 8, fontWeight: 600 }}>诊断步骤</div>
        {steps.length === 0 && <Empty description="暂无步骤" />}
        {steps.map((step, i) => (
          <Card key={i} size="small" style={{ marginBottom: 8 }}>
            <Row gutter={8} align="middle">
              <Col span={2}>
                <Tag color="blue">{step.id}</Tag>
              </Col>
              <Col span={8}>
                <Input
                  placeholder="步骤标题"
                  value={step.title}
                  onChange={(e) => updateStep(i, 'title', e.target.value)}
                />
              </Col>
              <Col span={9}>
                <Input
                  placeholder="步骤描述"
                  value={step.description || ''}
                  onChange={(e) => updateStep(i, 'description', e.target.value)}
                />
              </Col>
              <Col span={3}>
                <Input
                  placeholder="下一步"
                  prefix={<ArrowRightOutlined />}
                  value={step.next_step || ''}
                  onChange={(e) => updateStep(i, 'next_step', e.target.value || null)}
                />
              </Col>
              <Col span={2}>
                <Button danger size="small" icon={<DeleteOutlined />} onClick={() => removeStep(i)} />
              </Col>
            </Row>
          </Card>
        ))}
        <Button type="dashed" block icon={<PlusOutlined />} onClick={addStep} style={{ marginTop: 8 }}>
          添加步骤
        </Button>
      </Modal>
    </div>
  );
}
