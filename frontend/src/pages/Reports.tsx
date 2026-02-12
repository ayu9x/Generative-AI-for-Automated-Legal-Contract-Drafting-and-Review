
import { useQuery } from '@tanstack/react-query';
import { reportsAPI } from '../services/api';
import {
    FileText,
    Download,
    PieChart,
    BarChart2,
    TrendingUp,
    Activity,
    Shield,
    Clock,
    CheckCircle,
    XCircle,
    AlertTriangle,
} from 'lucide-react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    PieChart as RePieChart,
    Pie,
    Cell,
    LineChart,
    Line,
} from 'recharts';

export default function Reports() {
    const { data: analyticsData } = useQuery({
        queryKey: ['analytics'],
        queryFn: () => reportsAPI.getAnalytics(),
    });

    const analytics = analyticsData?.data;

    if (!analytics) {
        return (
            <div className="flex items-center justify-center h-96">
                <Activity className="w-8 h-8 animate-spin text-primary-600" />
            </div>
        );
    }

    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];
    const RISK_COLORS = ['#EF4444', '#F59E0B', '#10B981'];

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                        <BarChart2 className="w-8 h-8 text-primary-600" />
                        Reports & Analytics
                    </h1>
                    <p className="text-gray-500 mt-1">
                        Portfolio performance, compliance stats, and contract insights
                    </p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-700 shadow-sm transition-colors">
                    <Download className="w-4 h-4" />
                    Export Report
                </button>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <MetricCard
                    label="Total Contracts"
                    value={analytics.key_metrics.total_contracts}
                    trend="+12%"
                    icon={FileText}
                    color="blue"
                />
                <MetricCard
                    label="Active Contracts"
                    value={analytics.key_metrics.active_contracts}
                    trend="+5%"
                    icon={Activity}
                    color="green"
                />
                <MetricCard
                    label="Avg. Processing Time"
                    value={`${analytics.key_metrics.average_processing_time_hours}h`}
                    trend="-1.5h"
                    icon={Clock}
                    color="purple"
                />
                <MetricCard
                    label="Compliance Rate"
                    value={`${analytics.key_metrics.compliance_rate}%`}
                    trend="+2.4%"
                    icon={Shield}
                    color="indigo"
                />
            </div>

            {/* Charts Row 1 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <ChartCard title="Contract Volume (Last 12 Months)" icon={BarChart2}>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={analytics.monthly_volume}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="month" axisLine={false} tickLine={false} />
                            <YAxis axisLine={false} tickLine={false} />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="contracts_created" name="Created" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="contracts_approved" name="Approved" fill="#10B981" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>

                <ChartCard title="Contract Types Distribution" icon={PieChart}>
                    <ResponsiveContainer width="100%" height={300}>
                        <RePieChart>
                            <Pie
                                data={analytics.type_distribution}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={100}
                                fill="#8884d8"
                                paddingAngle={5}
                                dataKey="count"
                                nameKey="type"
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                            >
                                {analytics.type_distribution.map((entry: any, index: number) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </RePieChart>
                    </ResponsiveContainer>
                </ChartCard>
            </div>

            {/* Charts Row 2 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <ChartCard title="Risk Trends (Last 6 Months)" icon={TrendingUp}>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={analytics.risk_trends}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="month" axisLine={false} tickLine={false} />
                            <YAxis axisLine={false} tickLine={false} />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="high_risk" name="High Risk" stroke="#EF4444" strokeWidth={2} />
                            <Line type="monotone" dataKey="medium_risk" name="Medium Risk" stroke="#F59E0B" strokeWidth={2} />
                            <Line type="monotone" dataKey="low_risk" name="Low Risk" stroke="#10B981" strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </ChartCard>

                <ChartCard title="Compliance by Framework" icon={Shield}>
                    <div className="space-y-4">
                        {analytics.compliance.frameworks.map((fw: any) => (
                            <div key={fw.name} className="space-y-2">
                                <div className="flex justify-between text-sm font-medium">
                                    <span>{fw.name}</span>
                                    <span className={fw.pass_rate >= 90 ? 'text-green-600' : fw.pass_rate >= 80 ? 'text-yellow-600' : 'text-red-600'}>
                                        {fw.pass_rate}% Pass Rate
                                    </span>
                                </div>
                                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden flex">
                                    <div style={{ width: `${(fw.passed / fw.total_checks) * 100}%` }} className="h-full bg-green-500" />
                                    <div style={{ width: `${(fw.pending / fw.total_checks) * 100}%` }} className="h-full bg-yellow-400" />
                                    <div style={{ width: `${(fw.failed / fw.total_checks) * 100}%` }} className="h-full bg-red-500" />
                                </div>
                                <div className="flex gap-4 text-xs text-gray-500">
                                    <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-green-500" /> {fw.passed} Passed</span>
                                    <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-yellow-400" /> {fw.pending} Pending</span>
                                    <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-red-500" /> {fw.failed} Failed</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </ChartCard>
            </div>
        </div>
    );
}

function MetricCard({ label, value, trend, icon: Icon, color }: any) {
    const isPositive = trend.startsWith('+');
    return (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-lg bg-${color}-50`}>
                    <Icon className={`w-6 h-6 text-${color}-600`} />
                </div>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${isPositive ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                    {trend}
                </span>
            </div>
            <p className="text-gray-500 text-sm font-medium">{label}</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">{value}</h3>
        </div>
    );
}

function ChartCard({ title, icon: Icon, children }: any) {
    return (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
                <Icon className="w-5 h-5 text-gray-400" />
                <h3 className="font-semibold text-gray-900">{title}</h3>
            </div>
            {children}
        </div>
    );
}
