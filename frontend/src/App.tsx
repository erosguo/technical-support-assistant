import { BrowserRouter, Routes, Route, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { ConfigProvider, Layout, Menu, Button, Space, Typography, Drawer } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { MessageOutlined, BookOutlined, BugOutlined, FileTextOutlined, LogoutOutlined, NodeIndexOutlined, DashboardOutlined, TeamOutlined, ApiOutlined, ExperimentOutlined, MenuOutlined } from '@ant-design/icons';
import { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from './store/hooks';
import { fetchCurrentUser, logout } from './store/authSlice';
import { useResponsive } from './hooks/useResponsive';
import ChatPage from './pages/ChatPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import DiagnosisPage from './pages/DiagnosisPage';
import TicketPage from './pages/TicketPage';
import DiagnosisFlowPage from './pages/DiagnosisFlowPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UserManagementPage from './pages/UserManagementPage';
import IntegrationPage from './pages/IntegrationPage';
import KnowledgeDiscoveryPage from './pages/KnowledgeDiscoveryPage';

const { Header, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/chat', icon: <MessageOutlined />, label: '对话' },
  { key: '/diagnosis', icon: <BugOutlined />, label: '故障诊断' },
  { key: '/diagnosis/flows', icon: <NodeIndexOutlined />, label: '诊断流程' },
  { key: '/knowledge', icon: <BookOutlined />, label: '知识库' },
  { key: '/tickets', icon: <FileTextOutlined />, label: '工单管理' },
  { key: '/users', icon: <TeamOutlined />, label: '用户管理' },
  { key: '/integration', icon: <ApiOutlined />, label: '集成管理' },
  { key: '/discovery', icon: <ExperimentOutlined />, label: '知识发现' },
];

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
  const isMobile = useResponsive(768);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const currentKey = location.pathname.startsWith('/dashboard')
    ? '/dashboard'
    : location.pathname.startsWith('/users')
      ? '/users'
      : location.pathname.startsWith('/integration')
        ? '/integration'
        : location.pathname.startsWith('/discovery')
          ? '/discovery'
          : location.pathname.startsWith('/knowledge')
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

  const handleMenuClick = (key: string) => {
    navigate(key);
    setDrawerOpen(false);
  };

  return (
    <Layout style={{ height: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          background: '#001529',
          padding: isMobile ? '0 12px' : '0 24px',
        }}
      >
        {isMobile && (
          <Button
            type="text"
            icon={<MenuOutlined />}
            onClick={() => setDrawerOpen(true)}
            style={{ color: '#fff', marginRight: 8 }}
          />
        )}
        <div style={{ color: '#fff', fontSize: isMobile ? 15 : 18, fontWeight: 600, marginRight: isMobile ? 8 : 40, whiteSpace: 'nowrap' }}>
          Tech Support
        </div>
        {!isMobile && (
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[currentKey]}
            items={menuItems}
            onClick={({ key }) => handleMenuClick(key)}
            style={{ flex: 1, minWidth: 0 }}
          />
        )}
        {user && (
          <Space style={{ marginLeft: 'auto' }}>
            {!isMobile && <Text style={{ color: '#fff' }}>{user.name}</Text>}
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
          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute><UserManagementPage /></ProtectedRoute>} />
          <Route path="/integration" element={<ProtectedRoute><IntegrationPage /></ProtectedRoute>} />
          <Route path="/discovery" element={<ProtectedRoute><KnowledgeDiscoveryPage /></ProtectedRoute>} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </Content>

      <Drawer
        title="导航菜单"
        placement="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        bodyStyle={{ padding: 0 }}
        width={260}
      >
        <Menu
          mode="inline"
          selectedKeys={[currentKey]}
          items={menuItems}
          onClick={({ key }) => handleMenuClick(key)}
        />
      </Drawer>
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
