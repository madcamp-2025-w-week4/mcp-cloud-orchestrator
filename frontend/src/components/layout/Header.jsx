// ============================================================================
// MCP Cloud Orchestrator - Header Component
// ============================================================================

import { Plus, User, Bell } from 'lucide-react';

function Header({ user, onLaunchInstance }) {
    return (
        <header className="header">
            <div className="flex items-center gap-4">
                <h1 className="page-title">Cloud Console</h1>
            </div>

            <div className="flex items-center gap-4">
                {/* Launch Button */}
                <button
                    onClick={onLaunchInstance}
                    className="btn btn-primary flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Launch Instance
                </button>

                {/* Notifications */}
                <button className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg">
                    <Bell className="w-5 h-5" />
                </button>

                {/* User Menu */}
                <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
                    <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                        {user?.username?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div className="text-sm">
                        <div className="font-medium text-slate-800">{user?.username || 'User'}</div>
                        <div className="text-xs text-slate-500">{user?.id || 'user-demo-001'}</div>
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Header;
