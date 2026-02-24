import { useState } from 'react';
import {
    BarChart3,
    TrendingUp,
    TrendingDown,
    AlertTriangle,
    CheckCircle2,
    Shield,
    Clock,
    FileText,
    ArrowUpRight,
    Zap,
    Globe,
    Scale,
} from 'lucide-react';

// Mock insights data
const insightsData = {
    overview: {
        totalContracts: 247,
        activeContracts: 189,
        pendingReview: 23,
        expiringThisMonth: 8,
        avgRiskScore: 0.34,
        complianceRate: 94.2,
    },
    riskTrend: [
        { month: 'Sep', score: 0.42 },
        { month: 'Oct', score: 0.38 },
        { month: 'Nov', score: 0.35 },
        { month: 'Dec', score: 0.31 },
        { month: 'Jan', score: 0.33 },
        { month: 'Feb', score: 0.34 },
    ],
    topRisks: [
        { name: 'Missing Limitation of Liability', count: 18, severity: 'critical', trend: 'down' },
        { name: 'Auto-Renewal without Notice', count: 14, severity: 'high', trend: 'up' },
        { name: 'Unclear IP Assignment', count: 12, severity: 'high', trend: 'down' },
        { name: 'Missing Data Processing Addendum', count: 9, severity: 'medium', trend: 'up' },
        { name: 'Inadequate Termination Clause', count: 7, severity: 'medium', trend: 'down' },
    ],
    contractsByType: [
        { type: 'NDA', count: 82, percentage: 33 },
        { type: 'MSA', count: 45, percentage: 18 },
        { type: 'Employment', count: 38, percentage: 15 },
        { type: 'Service Agreement', count: 32, percentage: 13 },
        { type: 'License', count: 25, percentage: 10 },
        { type: 'Other', count: 25, percentage: 11 },
    ],
    jurisdictionBreakdown: [
        { jurisdiction: 'US Federal', count: 85, flag: '🇺🇸' },
        { jurisdiction: 'India', count: 42, flag: '🇮🇳' },
        { jurisdiction: 'European Union', count: 38, flag: '🇪🇺' },
        { jurisdiction: 'United Kingdom', count: 28, flag: '🇬🇧' },
        { jurisdiction: 'Singapore', count: 15, flag: '🇸🇬' },
        { jurisdiction: 'Australia', count: 12, flag: '🇦🇺' },
        { jurisdiction: 'Others', count: 27, flag: '🌍' },
    ],
    aiInsights: [
        {
            id: '1',
            type: 'warning',
            title: '8 contracts expiring within 30 days',
            description: 'Review and renew or terminate before auto-renewal kicks in. 3 have auto-renewal clauses.',
            action: 'Review Expiring Contracts',
        },
        {
            id: '2',
            type: 'opportunity',
            title: 'Standardize NDA templates',
            description: 'Analysis found 12 different NDA variations. Consolidating to 2-3 standard templates could reduce review time by 40%.',
            action: 'View NDA Analysis',
        },
        {
            id: '3',
            type: 'risk',
            title: 'GDPR compliance gap detected',
            description: '6 EU-targeted contracts are missing required Data Processing Addendum. Non-compliance risk: €4M+.',
            action: 'Run Compliance Check',
        },
        {
            id: '4',
            type: 'success',
            title: 'Risk score improved by 19% this quarter',
            description: 'Average risk score dropped from 0.42 to 0.34 since September. Keep up the good work!',
            action: 'View Trend Details',
        },
    ],
    recentActivity: [
        { action: 'Risk analysis completed', contract: 'NDA — Acme Corp', time: '15 min ago', type: 'analysis' },
        { action: 'New contract generated', contract: 'MSA — CloudSync', time: '1 hour ago', type: 'create' },
        { action: 'Compliance check passed', contract: 'Employment — Sr. Dev', time: '2 hours ago', type: 'compliance' },
        { action: 'Contract signed', contract: 'License — DataFlow Pro', time: '3 hours ago', type: 'sign' },
        { action: 'Review requested', contract: 'Partnership — LegalTech', time: '5 hours ago', type: 'review' },
    ],
};

export default function ContractInsights() {
    const [selectedPeriod, setSelectedPeriod] = useState('6mo');
    const data = insightsData;

    const severityColor: Record<string, string> = {
        critical: 'bg-red-100 text-red-700 border-red-200',
        high: 'bg-orange-100 text-orange-700 border-orange-200',
        medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    };

    const insightIcon = (type: string) => {
        switch (type) {
            case 'warning': return <Clock className="w-5 h-5 text-amber-500" />;
            case 'opportunity': return <Zap className="w-5 h-5 text-blue-500" />;
            case 'risk': return <AlertTriangle className="w-5 h-5 text-red-500" />;
            case 'success': return <CheckCircle2 className="w-5 h-5 text-green-500" />;
            default: return <FileText className="w-5 h-5 text-gray-500" />;
        }
    };

    const insightBorder = (type: string) => {
        switch (type) {
            case 'warning': return 'border-l-amber-400';
            case 'opportunity': return 'border-l-blue-400';
            case 'risk': return 'border-l-red-400';
            case 'success': return 'border-l-green-400';
            default: return 'border-l-gray-400';
        }
    };

    const maxCount = Math.max(...data.contractsByType.map(c => c.count));

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                        <BarChart3 className="w-8 h-8 text-emerald-500" />
                        Contract Insights
                    </h1>
                    <p className="text-gray-500 mt-1">AI-powered analytics and intelligence across your contract portfolio.</p>
                </div>
                <div className="flex items-center gap-2 bg-white rounded-lg border border-gray-200 p-1">
                    {['1mo', '3mo', '6mo', '1yr'].map((p) => (
                        <button
                            key={p}
                            onClick={() => setSelectedPeriod(p)}
                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${selectedPeriod === p ? 'bg-emerald-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
                        >
                            {p}
                        </button>
                    ))}
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
                    <p className="text-xs text-gray-500 mb-1">Total Contracts</p>
                    <p className="text-2xl font-bold text-gray-900">{data.overview.totalContracts}</p>
                    <p className="text-xs text-green-600 flex items-center gap-1 mt-1"><TrendingUp className="w-3 h-3" /> +12 this month</p>
                </div>
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
                    <p className="text-xs text-gray-500 mb-1">Active</p>
                    <p className="text-2xl font-bold text-emerald-600">{data.overview.activeContracts}</p>
                    <p className="text-xs text-gray-500 mt-1">{((data.overview.activeContracts / data.overview.totalContracts) * 100).toFixed(0)}% of total</p>
                </div>
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
                    <p className="text-xs text-gray-500 mb-1">Pending Review</p>
                    <p className="text-2xl font-bold text-amber-600">{data.overview.pendingReview}</p>
                    <p className="text-xs text-amber-600 flex items-center gap-1 mt-1"><Clock className="w-3 h-3" /> Needs attention</p>
                </div>
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
                    <p className="text-xs text-gray-500 mb-1">Expiring Soon</p>
                    <p className="text-2xl font-bold text-red-600">{data.overview.expiringThisMonth}</p>
                    <p className="text-xs text-red-600 flex items-center gap-1 mt-1"><AlertTriangle className="w-3 h-3" /> Within 30 days</p>
                </div>
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
                    <p className="text-xs text-gray-500 mb-1">Avg Risk Score</p>
                    <p className="text-2xl font-bold text-green-600">{(data.overview.avgRiskScore * 100).toFixed(0)}%</p>
                    <p className="text-xs text-green-600 flex items-center gap-1 mt-1"><TrendingDown className="w-3 h-3" /> -8% vs last month</p>
                </div>
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
                    <p className="text-xs text-gray-500 mb-1">Compliance Rate</p>
                    <p className="text-2xl font-bold text-blue-600">{data.overview.complianceRate}%</p>
                    <p className="text-xs text-blue-600 flex items-center gap-1 mt-1"><Shield className="w-3 h-3" /> Excellent</p>
                </div>
            </div>

            {/* AI Insights */}
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
                <div className="p-5 border-b border-gray-100 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-amber-500" />
                    <h2 className="text-lg font-semibold text-gray-900">AI Insights & Recommendations</h2>
                </div>
                <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                    {data.aiInsights.map((insight) => (
                        <div key={insight.id} className={`border-l-4 ${insightBorder(insight.type)} bg-gray-50 rounded-r-lg p-4 hover:bg-gray-100 transition-colors`}>
                            <div className="flex items-start gap-3">
                                {insightIcon(insight.type)}
                                <div className="flex-1">
                                    <h4 className="font-medium text-gray-900 text-sm">{insight.title}</h4>
                                    <p className="text-xs text-gray-500 mt-1">{insight.description}</p>
                                    <button className="mt-2 text-xs font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
                                        {insight.action} <ArrowUpRight className="w-3 h-3" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Top Risks */}
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
                    <div className="p-5 border-b border-gray-100">
                        <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 text-orange-500" />
                            Top Risk Patterns
                        </h2>
                    </div>
                    <div className="p-4 space-y-3">
                        {data.topRisks.map((risk, i) => (
                            <div key={i} className="flex items-center justify-between">
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase border ${severityColor[risk.severity]}`}>{risk.severity}</span>
                                    <span className="text-sm text-gray-700 truncate">{risk.name}</span>
                                </div>
                                <div className="flex items-center gap-2 shrink-0">
                                    <span className="text-sm font-bold text-gray-900">{risk.count}</span>
                                    {risk.trend === 'up' ? (
                                        <TrendingUp className="w-3 h-3 text-red-500" />
                                    ) : (
                                        <TrendingDown className="w-3 h-3 text-green-500" />
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Contracts by Type */}
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
                    <div className="p-5 border-b border-gray-100">
                        <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                            <Scale className="w-4 h-4 text-indigo-500" />
                            Contracts by Type
                        </h2>
                    </div>
                    <div className="p-4 space-y-3">
                        {data.contractsByType.map((item, i) => (
                            <div key={i}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-700 font-medium">{item.type}</span>
                                    <span className="text-gray-500">{item.count} ({item.percentage}%)</span>
                                </div>
                                <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-500"
                                        style={{ width: `${(item.count / maxCount) * 100}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Jurisdiction Breakdown */}
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
                    <div className="p-5 border-b border-gray-100">
                        <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                            <Globe className="w-4 h-4 text-teal-500" />
                            Jurisdictions
                        </h2>
                    </div>
                    <div className="p-4 space-y-3">
                        {data.jurisdictionBreakdown.map((item, i) => (
                            <div key={i} className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="text-lg">{item.flag}</span>
                                    <span className="text-sm text-gray-700">{item.jurisdiction}</span>
                                </div>
                                <span className="text-sm font-bold text-gray-900">{item.count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
                <div className="p-5 border-b border-gray-100">
                    <h2 className="font-semibold text-gray-900">Recent Activity</h2>
                </div>
                <div className="divide-y divide-gray-50">
                    {data.recentActivity.map((activity, i) => (
                        <div key={i} className="px-5 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors">
                            <div className="flex items-center gap-3">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${activity.type === 'analysis' ? 'bg-violet-100' :
                                        activity.type === 'create' ? 'bg-blue-100' :
                                            activity.type === 'compliance' ? 'bg-green-100' :
                                                activity.type === 'sign' ? 'bg-amber-100' : 'bg-gray-100'
                                    }`}>
                                    <FileText className={`w-4 h-4 ${activity.type === 'analysis' ? 'text-violet-600' :
                                            activity.type === 'create' ? 'text-blue-600' :
                                                activity.type === 'compliance' ? 'text-green-600' :
                                                    activity.type === 'sign' ? 'text-amber-600' : 'text-gray-600'
                                        }`} />
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                                    <p className="text-xs text-gray-500">{activity.contract}</p>
                                </div>
                            </div>
                            <span className="text-xs text-gray-400">{activity.time}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
