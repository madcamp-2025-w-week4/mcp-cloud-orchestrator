// ============================================================================
// MCP Cloud Orchestrator - Instances View Component
// ============================================================================

import { useState, useEffect } from 'react';
import { Plus, RefreshCw, Search, Play, Square, Trash2, ExternalLink } from 'lucide-react';
import { instanceAPI } from '../../api/client';
import StatusBadge from './StatusBadge';

function InstancesView({ onLaunchInstance }) {
    const [instances, setInstances] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadInstances();

        // 10초마다 갱신
        const interval = setInterval(loadInstances, 10000);
        return () => clearInterval(interval);
    }, []);

    const loadInstances = async () => {
        try {
            const response = await instanceAPI.list();
            setInstances(response.data);
        } catch (error) {
            console.error('Failed to load instances:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStop = async (instanceId) => {
        try {
            await instanceAPI.stop(instanceId);
            loadInstances();
        } catch (error) {
            console.error('Failed to stop instance:', error);
            alert('Failed to stop instance: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleStart = async (instanceId) => {
        try {
            await instanceAPI.start(instanceId);
            loadInstances();
        } catch (error) {
            console.error('Failed to start instance:', error);
            alert('Failed to start instance: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleTerminate = async (instanceId) => {
        if (!confirm('Are you sure you want to terminate this instance? This action cannot be undone.')) {
            return;
        }

        try {
            await instanceAPI.terminate(instanceId);
            loadInstances();
        } catch (error) {
            console.error('Failed to terminate instance:', error);
            alert('Failed to terminate instance: ' + (error.response?.data?.detail || error.message));
        }
    };

    const formatUptime = (seconds) => {
        if (!seconds) return '-';

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);

        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        }
        return `${minutes}m`;
    };

    const filteredInstances = instances.filter((instance) => {
        // 상태 필터
        if (filter !== 'all' && instance.status !== filter) {
            return false;
        }

        // 검색 필터
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            return (
                instance.name.toLowerCase().includes(term) ||
                instance.id.toLowerCase().includes(term) ||
                instance.image.toLowerCase().includes(term)
            );
        }

        return true;
    });

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800">Instances</h2>
                    <p className="text-slate-500 mt-1">Manage your container instances</p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={loadInstances}
                        className="btn btn-secondary flex items-center gap-2"
                        disabled={loading}
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                    <button
                        onClick={onLaunchInstance}
                        className="btn btn-primary flex items-center gap-2"
                    >
                        <Plus className="w-4 h-4" />
                        Launch Instance
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="card">
                <div className="p-4 flex items-center gap-4">
                    {/* Search */}
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Search instances..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="input pl-10"
                        />
                    </div>

                    {/* Status Filter */}
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-500">Status:</span>
                        <select
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="select w-32"
                        >
                            <option value="all">All</option>
                            <option value="running">Running</option>
                            <option value="stopped">Stopped</option>
                            <option value="pending">Pending</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Instances Table */}
            <div className="card">
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Instance ID</th>
                                <th>Image</th>
                                <th>Status</th>
                                <th>Public IP:Port</th>
                                <th>Resources</th>
                                <th>Uptime</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan="8" className="text-center py-12">
                                        <div className="flex items-center justify-center">
                                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                                            <span className="ml-3 text-slate-500">Loading instances...</span>
                                        </div>
                                    </td>
                                </tr>
                            ) : filteredInstances.length === 0 ? (
                                <tr>
                                    <td colSpan="8" className="text-center py-12">
                                        <div className="text-slate-500">
                                            {instances.length === 0 ? (
                                                <div>
                                                    <p>No instances found</p>
                                                    <button
                                                        onClick={onLaunchInstance}
                                                        className="btn btn-primary mt-4"
                                                    >
                                                        Launch your first instance
                                                    </button>
                                                </div>
                                            ) : (
                                                <p>No instances match your filters</p>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                filteredInstances.map((instance) => (
                                    <tr key={instance.id}>
                                        <td className="font-medium">{instance.name}</td>
                                        <td className="font-mono text-xs text-slate-500">{instance.id}</td>
                                        <td className="text-sm">{instance.image}</td>
                                        <td>
                                            <StatusBadge status={instance.status} />
                                        </td>
                                        <td>
                                            {instance.public_ip && instance.port ? (
                                                <a
                                                    href={`http://${instance.public_ip}:${instance.port}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="font-mono text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
                                                >
                                                    {instance.public_ip}:{instance.port}
                                                    <ExternalLink className="w-3 h-3" />
                                                </a>
                                            ) : (
                                                <span className="text-slate-400">-</span>
                                            )}
                                        </td>
                                        <td className="text-sm">
                                            {instance.cpu} vCPU, {instance.memory} GB
                                        </td>
                                        <td className="text-sm text-slate-500">
                                            {formatUptime(instance.uptime_seconds)}
                                        </td>
                                        <td>
                                            <div className="flex items-center gap-2">
                                                {instance.status === 'running' ? (
                                                    <button
                                                        onClick={() => handleStop(instance.id)}
                                                        className="p-1.5 text-amber-600 hover:bg-amber-50 rounded"
                                                        title="Stop"
                                                    >
                                                        <Square className="w-4 h-4" />
                                                    </button>
                                                ) : instance.status === 'stopped' ? (
                                                    <button
                                                        onClick={() => handleStart(instance.id)}
                                                        className="p-1.5 text-green-600 hover:bg-green-50 rounded"
                                                        title="Start"
                                                    >
                                                        <Play className="w-4 h-4" />
                                                    </button>
                                                ) : null}
                                                <button
                                                    onClick={() => handleTerminate(instance.id)}
                                                    className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                                                    title="Terminate"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

export default InstancesView;
