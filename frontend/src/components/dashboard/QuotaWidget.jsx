// ============================================================================
// MCP Cloud Orchestrator - Quota Widget Component
// ============================================================================

import { Cpu, MemoryStick, Server } from 'lucide-react';

function QuotaWidget({ title, quota }) {
    if (!quota) {
        return (
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">{title}</h3>
                </div>
                <div className="card-body">
                    <p className="text-slate-500">Loading quota data...</p>
                </div>
            </div>
        );
    }

    const getBarClass = (percent) => {
        if (percent >= 80) return 'high';
        if (percent >= 50) return 'medium';
        return 'low';
    };

    const quotaItems = [
        {
            label: 'Instances',
            icon: Server,
            used: quota.instances?.used || 0,
            max: quota.instances?.max || 5,
        },
        {
            label: 'CPU Cores',
            icon: Cpu,
            used: quota.cpu?.used || 0,
            max: quota.cpu?.max || 16,
        },
        {
            label: 'Memory (GB)',
            icon: MemoryStick,
            used: quota.memory?.used || 0,
            max: quota.memory?.max || 32,
        },
    ];

    return (
        <div className="card">
            <div className="card-header">
                <h3 className="card-title">{title}</h3>
            </div>
            <div className="card-body space-y-6">
                {quotaItems.map((item) => {
                    const percent = item.max > 0 ? (item.used / item.max) * 100 : 0;
                    const Icon = item.icon;

                    return (
                        <div key={item.label}>
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <Icon className="w-4 h-4 text-slate-400" />
                                    <span className="text-sm font-medium text-slate-700">{item.label}</span>
                                </div>
                                <span className="text-sm text-slate-500">
                                    {item.used} / {item.max}
                                </span>
                            </div>
                            <div className="quota-bar">
                                <div
                                    className={`quota-fill ${getBarClass(percent)}`}
                                    style={{ width: `${Math.min(percent, 100)}%` }}
                                />
                            </div>
                            <div className="text-right mt-1">
                                <span className="text-xs text-slate-400">{percent.toFixed(1)}% used</span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default QuotaWidget;
