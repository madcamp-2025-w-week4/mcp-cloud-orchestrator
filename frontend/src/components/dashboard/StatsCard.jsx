// ============================================================================
// MCP Cloud Orchestrator - Stats Card Component
// ============================================================================

const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    amber: 'bg-amber-50 text-amber-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
    slate: 'bg-slate-50 text-slate-600',
};

function StatsCard({ title, value, subtitle, icon: Icon, color = 'blue' }) {
    const iconColorClass = colorClasses[color] || colorClasses.blue;

    return (
        <div className="stats-card">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm text-slate-500 font-medium">{title}</p>
                    <p className="stats-value mt-2">{value}</p>
                    {subtitle && (
                        <p className="text-sm text-slate-500 mt-1">{subtitle}</p>
                    )}
                </div>
                {Icon && (
                    <div className={`p-3 rounded-lg ${iconColorClass}`}>
                        <Icon className="w-6 h-6" />
                    </div>
                )}
            </div>
        </div>
    );
}

export default StatsCard;
