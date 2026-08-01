import { useState, useEffect, useCallback } from 'react';
import { Table, Button, Modal, Form, Input, Select, Space, Tag, Popconfirm, message, Card, Empty } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, TeamOutlined } from '@ant-design/icons';
import { useAppSelector } from '../store/hooks';
import { listUsers, createUser, updateUser, deleteUser, UserSummary } from '../services/user';

export default function UserManagementPage() {
  const { user } = useAppSelector((s) => s.auth);
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<UserSummary | null>(null);
  const [form] = Form.useForm();

  const canManage = user && (user.role === 'admin' || user.role === 'manager');

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listUsers();
      setUsers(data);
    } catch {
      message.error('加载用户列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (canManage) {
      loadUsers();
    }
  }, [canManage, loadUsers]);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (record: UserSummary) => {
    setEditing(record);
    form.setFieldsValue({ name: record.name, role: record.role, is_active: record.is_active });
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editing) {
        await updateUser(editing.id, values);
        message.success('更新成功');
      } else {
        await createUser(values);
        message.success('创建成功');
      }
      setModalOpen(false);
      loadUsers();
    } catch {
      message.error('保存失败');
    }
  };

  const handleDelete = async (id: string) => {
    await deleteUser(id);
    message.success('删除成功');
    loadUsers();
  };

  const columns = [
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '角色', dataIndex: 'role', key: 'role', render: (r: string) => <Tag color="blue">{r}</Tag> },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (active ? <Tag color="green">活跃</Tag> : <Tag>已禁用</Tag>),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: any, r: UserSummary) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(r)}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (!canManage) {
    return (
      <div style={{ padding: 24 }}>
        <Card>
          <Empty description="暂无权限，请联系管理员" />
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={<span><TeamOutlined /> 用户管理</span>}
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建用户</Button>}
      >
        <Table dataSource={users} columns={columns} rowKey="id" loading={loading} />
      </Card>

      <Modal
        title={editing ? '编辑用户' : '新建用户'}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          {!editing && (
            <>
              <Form.Item label="邮箱" name="email" rules={[{ required: true, type: 'email', message: '请输入有效的邮箱' }]}>
                <Input placeholder="user@example.com" />
              </Form.Item>
              <Form.Item label="密码" name="password" rules={[{ required: true, message: '请输入密码' }]}>
                <Input.Password placeholder="密码" />
              </Form.Item>
            </>
          )}
          <Form.Item label="姓名" name="name" rules={[{ required: true, message: '请输入姓名' }]}>
            <Input placeholder="姓名" />
          </Form.Item>
          <Form.Item label="角色" name="role" rules={[{ required: true, message: '请选择角色' }]}>
            <Select
              options={[
                { label: '管理员', value: 'admin' },
                { label: '经理', value: 'manager' },
                { label: '工程师', value: 'engineer' },
                { label: '用户', value: 'user' },
              ]}
            />
          </Form.Item>
          <Form.Item label="状态" name="is_active" initialValue={true}>
            <Select
              options={[
                { label: '活跃', value: true },
                { label: '已禁用', value: false },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}