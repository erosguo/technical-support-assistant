import { useEffect, useRef, useState } from 'react';
import { Layout, Menu, Button, Input, List, Typography, Empty, Tag } from 'antd';
import { PlusOutlined, MessageOutlined } from '@ant-design/icons';
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
} from '../store/conversationSlice';

const { Sider, Content } = Layout;
const { Text } = Typography;
const API_BASE = 'http://localhost:8000/api/v1';

export default function ChatPage() {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { id } = useParams();
  const { list, currentId, messages, streaming } = useSelector(
    (s: RootState) => s.conversation,
  );
  const [input, setInput] = useState('');
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

  const handleNew = async () => {
    const res = await dispatch(createConversation());
    navigate(`/chat/${(res as { payload: { id: string } }).payload.id}`);
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

    const resp = await fetch(`${API_BASE}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: msg, conversation_id: convId }),
    });
    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();
    let fullText = '';
    let citations: Citation[] = [];
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      for (const line of decoder.decode(value).split('\n')) {
        if (line.startsWith('data: ')) {
          const payload = line.slice(6);
          if (payload === '[DONE]') continue;
          try {
            const parsed = JSON.parse(payload);
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
    dispatch(
      appendMessage({
        role: 'assistant',
        content: fullText,
        sources: citations.length > 0 ? citations : undefined,
      }),
    );
    dispatch(setStreaming(false));
    dispatch(fetchConversations());
  };

  return (
    <Layout style={{ height: '100vh' }}>
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
            label: c.title,
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
            loading={streaming}
          />
        </div>
      </Content>
    </Layout>
  );
}
