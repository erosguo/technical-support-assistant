import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { ConfigProvider, Layout, Menu } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { MessageOutlined, BookOutlined, BugOutlined } from '@ant-design/icons';
import ChatPage from './pages/ChatPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import DiagnosisPage from './pages/DiagnosisPage';

const { Header, Content } = Layout;

function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  const currentKey = location.pathname.startsWith('/knowledge')
    ? '/knowledge'
    : location.pathname.startsWith('/diagnosis')
      ? '/diagnosis'
      : '/chat';

  return (
    <Layout style={{ height: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          background: '#001529',
          padding: '0 24px',
        }}
      >
        <div style={{ color: '#fff', fontSize: 18, fontWeight: 600, marginRight: 40 }}>
          Tech Support
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[currentKey]}
          items={[
            { key: '/chat', icon: <MessageOutlined />, label: '对话' },
            { key: '/diagnosis', icon: <BugOutlined />, label: '故障诊断' },
            { key: '/knowledge', icon: <BookOutlined />, label: '知识库' },
          ]}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1, minWidth: 0 }}
        />
      </Header>
      <Content style={{ background: '#fff' }}>
        <Routes>
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:id" element={<ChatPage />} />
          <Route path="/diagnosis" element={<DiagnosisPage />} />
          <Route path="/knowledge" element={<KnowledgeBasePage />} />
          <Route path="*" element={<ChatPage />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </ConfigProvider>
  );
}
