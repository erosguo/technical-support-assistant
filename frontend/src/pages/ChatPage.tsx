import { useEffect, useRef, useState } from 'react';
import {
  Layout,
  Menu,
  Button,
  Input,
  List,
  Typography,
  Empty,
  Tag,
  Popconfirm,
  Modal,
  Spin,
  Alert,
} from 'antd';
import { PlusOutlined, MessageOutlined, DeleteOutlined } from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { useParams, useNavigate } from 'react-router-dom';
import type { AppDispatch, RootState, Citation } from '../store';
import {
  fetchConversations,
  createConversation,
  fetchMessages,
  appendMessage,
  setCurrentId,
  setStreaming,
  deleteConversation,
} from '../store/conversationSlice';

const { Sider, Content } = Layout;
const { Text } = Typography;
const API_BASE = 'http://localhost:8000/api/v1';

interface ApprovalRequest {
  type: string;
  title?: string;
  description?: string;
  question?: string;
}

export default function ChatPage() {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { id } = useParams();
  const { list, currentId, messages, streaming } = useSelector(
    (s: RootState) => s.conversation,
  );
  const [input, setInput] = useState('');
  const [approval, setApproval] = useState<ApprovalRequest | null>(null);
  const [resuming, setResuming] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    dispatch(fetchConversations());
  }, [dispatch]);

  useEffect(() => {
    if (id) {
      dispatch(setCurrentId(id));
      dispatch(fetchMessages(id));
    }
  }, [id, dispatch]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleDelete = (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    dispatch(deleteConversation(convId));
    if (currentId === convId) {
      navigate('/chat', { replace: true });
    }
  };

  const handleNew = async () => {
    const res = await dispatch(createConversation());
    navigate(`/chat/${(res as { payload: { id: string } }).payload.id}`);
  };

  const readStream = async (
    reader: ReadableStreamDefaultReader<Uint8Array>,
  ): Promise<{ fullText: string; citations: Citation[]; interrupt: ApprovalRequest | null }> => {
    const decoder = new TextDecoder();
    let fullText = '';
    let citations: Citation[] = [];
    let interrupt: ApprovalRequest | null = null;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      for (const line of decoder.decode(value).split('\n')) {
        if (line.startsWith('data: ')) {
          const payload = line.slice(6);
          if (payload === '[DONE]') continue;
          try {
            const parsed = JSON.parse(payload);
            if (parsed.interrupt) {
              interrupt = parsed.interrupt;
            }
            if (parsed.content !== undefined) {
              fullText = parsed.content;
            }
            if (parsed.citations) {
              citations = parsed.citations;
            }
          } catch {
            /* ignore parse errors */
          }
        }
      }
    }
    return { fullText, citations, interrupt };
  };

  const resume = async (convId: string, approved: boolean) => {
    setResuming(true);
    try {
      const resp = await fetch(`${API_BASE}/chat/completions/resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: convId, approved }),
      });
      const { fullText, citations } = await readStream(resp.body!.getReader());
      dispatch(
        appendMessage({
          role: 'assistant',
          content: fullText,
          sources: citations.length > 0 ? citations : undefined,
        }),
      );
    } finally {
      setResuming(false);
      setApproval(null);
      dispatch(setStreaming(false));
      dispatch(fetchConversations());
    }
  };

  const handleSend = async () => {
    if (!input.trim() || streaming) return;
    const msg = input;
    setInput('');
    dispatch(appendMessage({ role: 'user', content: msg }));
    dispatch(setStreaming(true));
    let convId = currentId;
    if (!convId) {
      const res = await dispatch(createConversation(msg.slice(0, 50)));
      convId = (res as { payload: { id: string } }).payload.id;
      navigate(`/chat/${convId}`, { replace: true });
    }

    try {
      const resp = await fetch(`${API_BASE}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: msg, conversation_id: convId }),
      });
      const { fullText, citations, interrupt } = await readStream(resp.body!.getReader());
      if (interrupt) {
        setApproval(interrupt);
        return;
      }
      dispatch(
        appendMessage({
          role: 'assistant',
          content: fullText,
          sources: citations.length > 0 ? citations : undefined,
        }),
      );
      dispatch(setStreaming(false));
      dispatch(fetchConversations());
    } catch {
      dispatch(setStreaming(false));
    }
  };

  return (
    <Layout style={{ height: '100%' }}>
      <Sider
        width={280}
        style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}
      >
        <div style={{ padding: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} block onClick={handleNew}>
            新建对话
          </Button>
        </div>
        <Menu
          mode="inline"
          selectedKeys={currentId ? [currentId] : []}
          onSelect={({ key }) => navigate(`/chat/${key}`)}
          items={list.map((c) => ({
            key: c.id,
            icon: <MessageOutlined />,
            label: (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
                  {c.title}
                </span>
                <Popconfirm
                  title="删除此对话？"
                  onConfirm={(e) => handleDelete(e as unknown as React.MouseEvent, c.id)}
                >
                  <DeleteOutlined
                    style={{ color: '#999', fontSize: 12 }}
                    onClick={(e) => e.stopPropagation()}
                  />
                </Popconfirm>
              </div>
            ),
          }))}
        />
      </Sider>
      <Content style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
          {messages.length === 0 ? (
            <Empty description="开始新的对话" style={{ marginTop: 120 }} />
          ) : (
            <List
              dataSource={messages}
              renderItem={(msg) => (
                <List.Item>
                  <div style={{ width: '100%' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {msg.role === 'user' ? '用户' : '助手'}
                    </Text>
                    <div
                      style={{
                        background: msg.role === 'user' ? '#e6f4ff' : '#fafafa',
                        padding: '8px 12px',
                        borderRadius: 8,
                        marginTop: 4,
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {msg.content}
                    </div>
                    {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                      <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {msg.sources.map((s, i) => (
                          <Tag key={i} color="blue" title={s.excerpt}>
                            {s.document_title}
                            <Text style={{ fontSize: 11, marginLeft: 4, color: '#999' }}>
                              ({(s.score * 100).toFixed(0)}%)
                            </Text>
                          </Tag>
                        ))}
                      </div>
                    )}
                  </div>
                </List.Item>
              )}
            />
          )}
          <div ref={endRef} />
        </div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #f0f0f0' }}>
          <Input.Search
            size="large"
            placeholder="输入您的问题..."
            enterButton="发送"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onSearch={handleSend}
            loading={streaming || resuming}
          />
        </div>
      </Content>

      <Modal
        title="升级审批"
        open={approval !== null}
        closable={!resuming}
        maskClosable={false}
        footer={
          resuming ? null : (
            <>
              <Button onClick={() => currentId && resume(currentId, false)}>
                拒绝
              </Button>
              <Button
                type="primary"
                danger
                onClick={() => currentId && resume(currentId, true)}
              >
                批准升级
              </Button>
            </>
          )
        }
      >
        {resuming ? (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin tip="正在创建工单..." />
          </div>
        ) : (
          <>
            <Alert
              type="warning"
              showIcon
              message={approval?.question || '需要人工确认'}
              style={{ marginBottom: 16 }}
            />
            {approval?.title && (
              <p>
                <Text strong>工单标题：</Text>
                {approval.title}
              </p>
            )}
            {approval?.description && (
              <p>
                <Text strong>工单内容：</Text>
                <span style={{ whiteSpace: 'pre-wrap' }}>{approval.description}</span>
              </p>
            )}
          </>
        )}
      </Modal>
    </Layout>
  );
}
