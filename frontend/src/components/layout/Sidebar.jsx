// ============================================================================
// MCP Cloud Orchestrator - Sidebar Component
// ============================================================================

import {
    LayoutDashboard,
    Server,
    HardDrive,
    Settings,
    LogOut,
    Cloud,
    Activity,
    ExternalLink
} from 'lucide-react';
import { RAY_DASHBOARD_URL } from '../../api/client';

const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'instances', label: 'Instances', icon: Server },
    { id: 'nodes', label: 'Nodes', icon: HardDrive },
];

function Sidebar({ currentView, onNavigate }) {
    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="sidebar-logo flex items-center gap-3">
                <Cloud className="w-6 h-6 text-blue-400" />
                <span className="font-bold text-lg">kws</span>
            </div>

            {/* Navigation */}
            <nav className="sidebar-nav">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = currentView === item.id;

                    return (
                        <button
                            key={item.id}
                            onClick={() => onNavigate(item.id)}
                            className={`sidebar-link w-full text-left ${isActive ? 'active' : ''}`}
                        >
                            <Icon className="w-5 h-5" />
                            <span>{item.label}</span>
                        </button>
                    );
                })}

                {/* Ray Dashboard Link */}
                <a
                    href={RAY_DASHBOARD_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="sidebar-link w-full text-left flex items-center gap-2 mt-4 text-amber-400 hover:text-amber-300 border-t border-slate-700 pt-4"
                >
                    <Activity className="w-5 h-5" />
                    <span>Ray Dashboard</span>
                    <ExternalLink className="w-4 h-4 ml-auto" />
                </a>
            </nav>

            {/* Footer */}
            <div className="border-t border-slate-700 p-4">
                <button className="sidebar-link w-full text-left text-slate-400 hover:text-white">
                    <Settings className="w-5 h-5" />
                    <span>Settings</span>
                </button>
                <button className="sidebar-link w-full text-left text-slate-400 hover:text-white">
                    <LogOut className="w-5 h-5" />
                    <span>Logout</span>
                </button>
            </div>
        </aside>
    );
}

export default Sidebar;
