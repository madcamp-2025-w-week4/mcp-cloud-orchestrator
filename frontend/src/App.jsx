// ============================================================================
// MCP Cloud Orchestrator - Main App Component
// ============================================================================

import { useState, useEffect } from 'react';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import DashboardView from './components/dashboard/DashboardView';
import InstancesView from './components/instances/InstancesView';
import LaunchWizard from './components/wizard/LaunchWizard';
import NodesView from './components/nodes/NodesView';
import { authAPI } from './api/client';
import './index.css';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [user, setUser] = useState(null);
  const [showLaunchWizard, setShowLaunchWizard] = useState(false);

  useEffect(() => {
    // 사용자 정보 로드
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const response = await authAPI.getCurrentUser();
      setUser(response.data);
    } catch (error) {
      console.error('Failed to load user:', error);
      // 기본 데모 사용자 설정
      setUser({
        id: 'user-demo-001',
        username: 'demo',
        quota: {
          max_instances: 5,
          max_cpu: 16,
          max_memory: 32,
          used_instances: 0,
          used_cpu: 0,
          used_memory: 0
        }
      });
    }
  };

  const handleLaunchComplete = () => {
    setShowLaunchWizard(false);
    setCurrentView('instances');
  };

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <DashboardView onLaunchInstance={() => setShowLaunchWizard(true)} />;
      case 'instances':
        return <InstancesView onLaunchInstance={() => setShowLaunchWizard(true)} />;
      case 'nodes':
        return <NodesView />;
      default:
        return <DashboardView onLaunchInstance={() => setShowLaunchWizard(true)} />;
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar
        currentView={currentView}
        onNavigate={setCurrentView}
      />

      {/* Main Content */}
      <div className="main-content">
        <Header
          user={user}
          onLaunchInstance={() => setShowLaunchWizard(true)}
        />

        <main className="p-8">
          {renderView()}
        </main>
      </div>

      {/* Launch Wizard Modal */}
      {showLaunchWizard && (
        <LaunchWizard
          onClose={() => setShowLaunchWizard(false)}
          onComplete={handleLaunchComplete}
        />
      )}
    </div>
  );
}

export default App;
