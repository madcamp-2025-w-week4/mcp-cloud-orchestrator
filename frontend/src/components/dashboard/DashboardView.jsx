// ============================================================================
// MCP Cloud Orchestrator - Dashboard View Component
// ============================================================================

import { useState, useEffect } from 'react';
import { Server, HardDrive, Cpu, MemoryStick, Activity, Plus } from 'lucide-react';
import { dashboardAPI, authAPI } from '../../api/client';
import StatsCard from './StatsCard';
import QuotaWidget from './QuotaWidget';

function DashboardView({ onLaunchInstance }) {
    const [summary, setSummary] = useState(null);
    const [quota, setQuota] = useState(null);
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboardData();

        // 30초마다 데이터 갱신
        const interval = setInterval(loadDashboardData, 30000);
        return () => clearInterval(interval);
    }, []);

    const loadDashboardData = async () => {
        try {
            const [summaryRes, quotaRes, healthRes] = await Promise.all([
                dashboardAPI.getSummary(),
                authAPI.getQuota(),
                dashboardAPI.getHealth()
            ]);

            setSummary(summaryRes.data);
            setQuota(quotaRes.data);
            setHealth(healthRes.data);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    const instances = summary?.instances || { total: 0, running: 0, stopped: 0, pending: 0 };
    const nodes = summary?.nodes || { total: 0, workers: 0 };

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Welcome Section */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800">Dashboard</h2>
                    <p className="text-slate-500 mt-1">Overview of your cloud resources</p>
                </div>
                <button
                    onClick={onLaunchInstance}
                    className="btn btn-primary flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Launch Instance
                </button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatsCard
                    title="Total Instances"
                    value={instances.total}
                    subtitle={`${instances.running} running`}
                    icon={Server}
                    color="blue"
                />
                <StatsCard
                    title="Active Nodes"
                    value={nodes.workers}
                    subtitle={`${nodes.total} total nodes`}
                    icon={HardDrive}
                    color="green"
                />
                <StatsCard
                    title="Cluster Health"
                    value={health?.health?.toUpperCase() || 'UNKNOWN'}
                    subtitle={`${health?.summary?.availability_percent || 0}% availability`}
                    icon={Activity}
                    color={health?.health === 'healthy' ? 'green' : health?.health === 'degraded' ? 'amber' : 'red'}
                />
                <StatsCard
                    title="Running Instances"
                    value={instances.running}
                    subtitle={`${instances.stopped} stopped`}
                    icon={Server}
                    color="purple"
                />
            </div>

            {/* Quota Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <QuotaWidget
                    title="Resource Quota"
                    quota={quota}
                />

                {/* Quick Actions */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Quick Actions</h3>
                    </div>
                    <div className="card-body space-y-4">
                        <button
                            onClick={onLaunchInstance}
                            className="w-full btn btn-primary flex items-center justify-center gap-2"
                        >
                            <Plus className="w-4 h-4" />
                            Launch New Instance
                        </button>
                        <div className="grid grid-cols-2 gap-4">
                            <button className="btn btn-secondary w-full">
                                View Instances
                            </button>
                            <button className="btn btn-secondary w-full">
                                View Nodes
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Instance Status Summary */}
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">Instance Status Summary</h3>
                </div>
                <div className="card-body">
                    <div className="grid grid-cols-4 gap-4 text-center">
                        <div className="p-4 bg-blue-50 rounded-lg">
                            <div className="text-2xl font-bold text-blue-600">{instances.total}</div>
                            <div className="text-sm text-blue-700">Total</div>
                        </div>
                        <div className="p-4 bg-green-50 rounded-lg">
                            <div className="text-2xl font-bold text-green-600">{instances.running}</div>
                            <div className="text-sm text-green-700">Running</div>
                        </div>
                        <div className="p-4 bg-amber-50 rounded-lg">
                            <div className="text-2xl font-bold text-amber-600">{instances.pending}</div>
                            <div className="text-sm text-amber-700">Pending</div>
                        </div>
                        <div className="p-4 bg-slate-50 rounded-lg">
                            <div className="text-2xl font-bold text-slate-600">{instances.stopped}</div>
                            <div className="text-sm text-slate-700">Stopped</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DashboardView;
