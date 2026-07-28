import { useEffect, useState } from 'react';
import {
  Button,
  Table,
  Modal,
  Input,
  Upload,
  message,
  Space,
  Typography,
  Drawer,
  Tag,
  Popconfirm,
} from 'antd';
import { PlusOutlined, UploadOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadFile } from 'antd/es/upload/interface';
import {
  listDocuments,
  uploadDocument,
  getDocument,
  deleteDocument,
  DocumentSummary,
  DocumentDetail,
} from '../services/knowledge';

const { Text } = Typography;

export default function KnowledgeBasePage() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [drawerDoc, setDrawerDoc] = useState<DocumentDetail | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const data = await listDocuments();
      setDocs(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleUpload = async () => {
    if (!uploadTitle.trim() || !uploadFile) {
      message.warning('请填写文档标题并选择文件');
      return;
    }
    setUploading(true);
    try {
      await uploadDocument(uploadTitle.trim(), uploadFile);
      message.success('上传成功');
      setUploadOpen(false);
      setUploadTitle('');
      setUploadFile(null);
      loadDocs();
    } catch {
      message.error('上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteDocument(id);
      message.success('已删除');
      loadDocs();
    } catch {
      message.error('删除失败');
    }
  };

  const handleView = async (id: string) => {
    try {
      const detail = await getDocument(id);
      setDrawerDoc(detail);
      setDrawerOpen(true);
    } catch {
      message.error('加载文档失败');
    }
  };

  const columns: ColumnsType<DocumentSummary> = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    {
      title: '类型',
      dataIndex: 'doc_type',
      key: 'doc_type',
      render: (v: string) => <Tag>{v || 'manual'}</Tag>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => (v ? new Date(v).toLocaleString() : '-'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleView(record.id)}
          >
            查看
          </Button>
          <Popconfirm
            title="确认删除此文档？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Typography.Title level={4} style={{ margin: 0 }}>
          知识库管理
        </Typography.Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setUploadOpen(true)}
        >
          上传文档
        </Button>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={docs}
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="上传文档"
        open={uploadOpen}
        onOk={handleUpload}
        onCancel={() => {
          setUploadOpen(false);
          setUploadTitle('');
          setUploadFile(null);
        }}
        confirmLoading={uploading}
        okText="上传"
        cancelText="取消"
      >
        <div style={{ marginBottom: 12 }}>
          <Text>文档标题</Text>
          <Input
            placeholder="输入文档标题"
            value={uploadTitle}
            onChange={(e) => setUploadTitle(e.target.value)}
          />
        </div>
        <Upload
          accept=".md,.txt,.html"
          maxCount={1}
          beforeUpload={(file) => {
            setUploadFile(file);
            return false;
          }}
          onRemove={() => setUploadFile(null)}
          fileList={
            uploadFile
              ? [
                  {
                    uid: '-1',
                    name: uploadFile.name,
                    status: 'done',
                  } as UploadFile,
                ]
              : []
          }
        >
          <Button icon={<UploadOutlined />}>选择文件</Button>
        </Upload>
      </Modal>

      <Drawer
        title={drawerDoc?.title || '文档详情'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={600}
      >
        {drawerDoc && (
          <div>
            <p>
              <Text type="secondary">类型：</Text>
              <Tag>{drawerDoc.doc_type || 'manual'}</Tag>
            </p>
            <p>
              <Text type="secondary">创建时间：</Text>
              {drawerDoc.created_at
                ? new Date(drawerDoc.created_at).toLocaleString()
                : '-'}
            </p>
            <div
              style={{
                marginTop: 16,
                whiteSpace: 'pre-wrap',
                background: '#fafafa',
                padding: 16,
                borderRadius: 8,
                maxHeight: '60vh',
                overflow: 'auto',
              }}
            >
              {drawerDoc.content}
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
