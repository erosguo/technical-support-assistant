import { BrowserRouter, Routes, Route, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { ConfigProvider, Layout, Menu, Button, Space, Typography } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { MessageOutlined, BookOutlined, BugOutlined, FileTextOutlined, LogoutOutlined, NodeIndexOutlined } from '@ant-design/icons';
import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from './store/hooks';
import { fetchCurrentUser, logout } from './store/authSlice';
import ChatPage from './pages/ChatPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import DiagnosisPage from './pages/DiagnosisPage';
import TicketPage from './pages/TicketPage';
import DiagnosisFlowPage from './pages/DiagnosisFlowPage';
import LoginPage from './pages/LoginPage';

const { Header, Content } = Layout;
const { Text } = Typography;

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, user } = useAppSelector((s) => s.auth);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (token && !user) {
      dispatch(fetchCurrentUser());
    }
  }, [token, user, dispatch]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((s) => s.auth);

  const currentKey = location.pathname.startsWith('/knowledge')
    ? '/knowledge'
    : location.pathname.startsWith('/diagnosis/flows')
      ? '/diagnosis/flows'
      : location.pathname.startsWith('/diagnosis')
        ? '/diagnosis'
        : location.pathname.startsWith('/tickets')
          ? '/tickets'
          : '/chat';

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

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
            { key: '/diagnosis/flows', icon: <NodeIndexOutlined />, label: '诊断流程' },
            { key: '/knowledge', icon: <BookOutlined />, label: '知识库' },
            { key: '/tickets', icon: <FileTextOutlined />, label: '工单管理' },
          ]}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1, minWidth: 0 }}
        />
        {user && (
          <Space style={{ marginLeft: 16 }}>
            <Text style={{ color: '#fff' }}>{user.name}</Text>
            <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout} style={{ color: '#fff' }} />
          </Space>
        )}
      </Header>
      <Content style={{ background: '#fff' }}>
        <Routes>
          <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
          <Route path="/chat/:id" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
          <Route path="/diagnosis" element={<ProtectedRoute><DiagnosisPage /></ProtectedRoute>} />
          <Route path="/knowledge" element={<ProtectedRoute><KnowledgeBasePage /></ProtectedRoute>} />
          <Route path="/tickets" element={<ProtectedRoute><TicketPage /></ProtectedRoute>} />
          <Route path="/diagnosis/flows" element={<ProtectedRoute><DiagnosisFlowPage /></ProtectedRoute>} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
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
