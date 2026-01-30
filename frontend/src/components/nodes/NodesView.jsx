// ============================================================================
// MCP Cloud Orchestrator - Nodes View Component
// ============================================================================

import { useState, useEffect } from 'react';
import { RefreshCw, HardDrive, Cpu, MemoryStick, Wifi, WifiOff } from 'lucide-react';
import { dashboardAPI } from '../../api/client';

function NodesView() {
    const [nodes, setNodes] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadNodes();

        // 30초마다 갱신
        const interval = setInterval(loadNodes, 30000);
        return () => clearInterval(interval);
    }, []);

    const loadNodes = async () => {
        try {
            const response = await dashboardAPI.getNodesStatus();
            setNodes(response.data);
        } catch (error) {
            console.error('Failed to load nodes:', error);
        } finally {
            setLoading(false);
        }
    };

    const getHealthBadge = (health, isOnline) => {
        if (!isOnline) {
            return <span className="badge badge-danger">Offline</span>;
        }

        switch (health) {
            case 'healthy':
                return <span className="badge badge-success">Healthy</span>;
            case 'unhealthy':
                return <span className="badge badge-danger">Unhealthy</span>;
            default:
                return <span className="badge badge-gray">Unknown</span>;
        }
    };

    const getRoleBadge = (role) => {
        switch (role) {
            case 'master':
                return <span className="badge badge-info">Master</span>;
            case 'worker':
                return <span className="badge badge-gray">Worker</span>;
            case 'storage':
                return <span className="badge badge-warning">Storage</span>;
            default:
                return <span className="badge badge-gray">{role}</span>;
        }
    };

    const onlineCount = nodes.filter(n => n.is_online).length;
    const masterNode = nodes.find(n => n.role === 'master');
    const workerNodes = nodes.filter(n => n.role === 'worker');

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800">Nodes</h2>
                    <p className="text-slate-500 mt-1">Cluster node status and health</p>
                </div>
                <button
                    onClick={loadNodes}
                    className="btn btn-secondary flex items-center gap-2"
                    disabled={loading}
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="stats-card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-blue-50 rounded-lg">
                            <HardDrive className="w-6 h-6 text-blue-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-slate-800">{nodes.length}</div>
                            <div className="text-sm text-slate-500">Total Nodes</div>
                        </div>
                    </div>
                </div>

                <div className="stats-card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-green-50 rounded-lg">
                            <Wifi className="w-6 h-6 text-green-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-slate-800">{onlineCount}</div>
                            <div className="text-sm text-slate-500">Online</div>
                        </div>
                    </div>
                </div>

                <div className="stats-card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-red-50 rounded-lg">
                            <WifiOff className="w-6 h-6 text-red-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-slate-800">{nodes.length - onlineCount}</div>
                            <div className="text-sm text-slate-500">Offline</div>
                        </div>
                    </div>
                </div>

                <div className="stats-card">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-purple-50 rounded-lg">
                            <Cpu className="w-6 h-6 text-purple-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-slate-800">{workerNodes.length}</div>
                            <div className="text-sm text-slate-500">Workers</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Master Node */}
            {masterNode && (
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Master Node</h3>
                    </div>
                    <div className="card-body">
                        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                            <div className="flex items-center gap-4">
                                <div className={`w-3 h-3 rounded-full ${masterNode.is_online ? 'bg-green-500' : 'bg-red-500'}`} />
                                <div>
                                    <div className="font-medium text-slate-800">{masterNode.hostname}</div>
                                    <div className="text-sm text-slate-500 font-mono">{masterNode.ip}</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-6">
                                <div className="text-center">
                                    <div className="text-lg font-semibold text-slate-800">{masterNode.cpu_cores}</div>
                                    <div className="text-xs text-slate-500">CPU Cores</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-lg font-semibold text-slate-800">{masterNode.memory_gb} GB</div>
                                    <div className="text-xs text-slate-500">Memory</div>
                                </div>
                                {masterNode.response_time_ms && (
                                    <div className="text-center">
                                        <div className="text-lg font-semibold text-slate-800">{masterNode.response_time_ms.toFixed(0)} ms</div>
                                        <div className="text-xs text-slate-500">Latency</div>
                                    </div>
                                )}
                                {getHealthBadge(masterNode.health, masterNode.is_online)}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Worker Nodes Table */}
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">Worker Nodes ({workerNodes.length})</h3>
                </div>
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Hostname</th>
                                <th>IP Address</th>
                                <th>Role</th>
                                <th>Health</th>
                                <th>CPU</th>
                                <th>Memory</th>
                                <th>Latency</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan="7" className="text-center py-12">
                                        <div className="flex items-center justify-center">
                                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                                            <span className="ml-3 text-slate-500">Loading nodes...</span>
                                        </div>
                                    </td>
                                </tr>
                            ) : workerNodes.length === 0 ? (
                                <tr>
                                    <td colSpan="7" className="text-center py-12 text-slate-500">
                                        No worker nodes found
                                    </td>
                                </tr>
                            ) : (
                                workerNodes.map((node) => (
                                    <tr key={node.id}>
                                        <td>
                                            <div className="flex items-center gap-2">
                                                <div className={`w-2 h-2 rounded-full ${node.is_online ? 'bg-green-500' : 'bg-red-500'}`} />
                                                <span className="font-medium">{node.hostname}</span>
                                            </div>
                                        </td>
                                        <td className="font-mono text-sm text-slate-500">{node.ip}</td>
                                        <td>{getRoleBadge(node.role)}</td>
                                        <td>{getHealthBadge(node.health, node.is_online)}</td>
                                        <td className="text-slate-600">{node.cpu_cores} cores</td>
                                        <td className="text-slate-600">{node.memory_gb} GB</td>
                                        <td className="text-slate-500">
                                            {node.response_time_ms ? `${node.response_time_ms.toFixed(0)} ms` : '-'}
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

export default NodesView;
