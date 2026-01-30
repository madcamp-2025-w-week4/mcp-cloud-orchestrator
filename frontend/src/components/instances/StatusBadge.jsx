// ============================================================================
// MCP Cloud Orchestrator - Status Badge Component
// ============================================================================

const statusConfig = {
    running: {
        color: 'bg-green-100 text-green-800',
        dot: 'bg-green-500',
        label: 'Running',
    },
    stopped: {
        color: 'bg-slate-100 text-slate-800',
        dot: 'bg-slate-400',
        label: 'Stopped',
    },
    pending: {
        color: 'bg-amber-100 text-amber-800',
        dot: 'bg-amber-500 animate-pulse',
        label: 'Pending',
    },
    terminated: {
        color: 'bg-red-100 text-red-800',
        dot: 'bg-red-500',
        label: 'Terminated',
    },
    error: {
        color: 'bg-red-100 text-red-800',
        dot: 'bg-red-500',
        label: 'Error',
    },
};

function StatusBadge({ status }) {
    const config = statusConfig[status] || statusConfig.error;

    return (
        <span className={`badge ${config.color}`}>
            <span className={`w-2 h-2 rounded-full mr-1.5 ${config.dot}`} />
            {config.label}
        </span>
    );
}

export default StatusBadge;
