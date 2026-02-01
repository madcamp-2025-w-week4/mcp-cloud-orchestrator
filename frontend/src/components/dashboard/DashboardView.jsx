// ============================================================================
// MCP Cloud Orchestrator - Dashboard View Component
// ============================================================================

import { useState, useEffect } from 'react';
import { Server, HardDrive, Cpu, MemoryStick, Activity, Plus, Zap, ExternalLink } from 'lucide-react';
import { dashboardAPI, authAPI, rayAPI, RAY_DASHBOARD_URL } from '../../api/client';
import StatsCard from './StatsCard';
import BillingWidget from './BillingWidget';

function DashboardView({ onLaunchInstance }) {
    const [summary, setSummary] = useState(null);
    const [billing, setBilling] = useState(null);
    const [health, setHealth] = useState(null);
    const [rayStatus, setRayStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboardData();

        // 30초마다 데이터 갱신
        const interval = setInterval(loadDashboardData, 30000);
        return () => clearInterval(interval);
    }, []);

    const loadDashboardData = async () => {
        try {
            const [summaryRes, billingRes, healthRes] = await Promise.all([
                dashboardAPI.getSummary(),
                authAPI.getBilling(),
                dashboardAPI.getHealth()
            ]);

            setSummary(summaryRes.data);
            setBilling(billingRes.data);
            setHealth(healthRes.data);

            // Ray 상태 별도로 로드 (실패해도 무시)
            try {
                const rayRes = await rayAPI.getStatus();
                setRayStatus(rayRes.data);
            } catch (e) {
                console.log('Ray cluster not connected');
            }
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

            {/* Ray Cluster Resources */}
            {rayStatus && (
                <div className="card bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200">
                    <div className="card-header flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Zap className="w-5 h-5 text-amber-500" />
                            <h3 className="card-title text-amber-800">Ray Cluster Resources</h3>
                            <span className={`ml-2 px-2 py-0.5 text-xs font-medium rounded ${rayStatus.is_connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                {rayStatus.is_connected ? 'Connected' : 'Disconnected'}
                            </span>
                        </div>
                        <a
                            href={RAY_DASHBOARD_URL}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-amber-600 hover:text-amber-800 flex items-center gap-1"
                        >
                            Open Ray Dashboard
                            <ExternalLink className="w-4 h-4" />
                        </a>
                    </div>
                    <div className="card-body">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                            <div className="text-center">
                                <div className="text-3xl font-bold text-amber-600">
                                    {rayStatus.nodes?.alive || 0}
                                </div>
                                <div className="text-sm text-amber-700">Active Nodes</div>
                            </div>
                            <div className="text-center">
                                <div className="text-3xl font-bold text-blue-600">
                                    {rayStatus.resources?.total?.cpu?.toFixed(0) || 0}
                                </div>
                                <div className="text-sm text-blue-700">Total CPUs</div>
                            </div>
                            <div className="text-center">
                                <div className="text-3xl font-bold text-green-600">
                                    {rayStatus.resources?.total?.memory?.toFixed(1) || 0} GB
                                </div>
                                <div className="text-sm text-green-700">Total Memory</div>
                            </div>
                            <div className="text-center">
                                <div className="text-3xl font-bold text-purple-600">
                                    {rayStatus.resources?.total?.gpu || 0}
                                </div>
                                <div className="text-sm text-purple-700">GPUs</div>
                            </div>
                        </div>

                        {/* Usage Bars */}
                        <div className="mt-6 space-y-3">
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-slate-600">CPU Usage</span>
                                    <span className="font-medium">{rayStatus.usage_percent?.cpu?.toFixed(1) || 0}%</span>
                                </div>
                                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-blue-500 rounded-full transition-all"
                                        style={{ width: `${Math.min(rayStatus.usage_percent?.cpu || 0, 100)}%` }}
                                    />
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-slate-600">Memory Usage</span>
                                    <span className="font-medium">{rayStatus.usage_percent?.memory?.toFixed(1) || 0}%</span>
                                </div>
                                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-green-500 rounded-full transition-all"
                                        style={{ width: `${Math.min(rayStatus.usage_percent?.memory || 0, 100)}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Quota Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <BillingWidget
                    title="Usage & Billing"
                    billing={billing}
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
