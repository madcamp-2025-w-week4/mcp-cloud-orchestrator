// ============================================================================
// KWS - Billing Widget Component
// ============================================================================
// AWS/Railway 스타일 사용량 기반 청구 표시

import { DollarSign, Cpu, MemoryStick, Server, Calendar } from 'lucide-react';

function BillingWidget({ title, billing }) {
    if (!billing) {
        return (
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">{title}</h3>
                </div>
                <div className="card-body">
                    <p className="text-slate-500">Loading billing data...</p>
                </div>
            </div>
        );
    }

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(amount);
    };

    const billingItems = [
        {
            label: 'CPU Usage',
            icon: Cpu,
            hours: billing.usage?.cpu_hours || 0,
            cost: billing.breakdown?.cpu_cost || 0,
            rate: '$0.02/hr'
        },
        {
            label: 'Memory Usage',
            icon: MemoryStick,
            hours: billing.usage?.memory_gb_hours || 0,
            cost: billing.breakdown?.memory_cost || 0,
            rate: '$0.01/GB-hr'
        },
        {
            label: 'Instance Usage',
            icon: Server,
            hours: billing.usage?.instance_hours || 0,
            cost: billing.breakdown?.instance_cost || 0,
            rate: '$0.005/hr'
        }
    ];

    return (
        <div className="card">
            <div className="card-header flex items-center justify-between">
                <h3 className="card-title">{title}</h3>
                <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {billing.billing_month}
                </span>
            </div>
            <div className="card-body space-y-4">
                {/* Total Amount */}
                <div className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-lg p-4 border border-emerald-500/20">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <DollarSign className="w-5 h-5 text-emerald-400" />
                            <span className="text-sm text-slate-400">Current Charges</span>
                        </div>
                        <span className="text-2xl font-bold text-emerald-400">
                            {formatCurrency(billing.total_amount || 0)}
                        </span>
                    </div>
                    <div className="mt-2 text-xs text-slate-500">
                        {billing.days_remaining} days remaining in billing period
                    </div>
                </div>

                {/* Breakdown */}
                <div className="space-y-3">
                    {billingItems.map((item) => {
                        const Icon = item.icon;
                        return (
                            <div key={item.label} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
                                <div className="flex items-center gap-2">
                                    <Icon className="w-4 h-4 text-slate-400" />
                                    <div>
                                        <span className="text-sm font-medium text-slate-300">{item.label}</span>
                                        <div className="text-xs text-slate-500">{item.hours.toFixed(1)} hrs × {item.rate}</div>
                                    </div>
                                </div>
                                <span className="text-sm font-medium text-slate-300">
                                    {formatCurrency(item.cost)}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {/* Note */}
                <div className="text-xs text-slate-500 text-center pt-2 border-t border-slate-700/50">
                    💡 Usage-based billing • No resource limits
                </div>
            </div>
        </div>
    );
}

export default BillingWidget;
