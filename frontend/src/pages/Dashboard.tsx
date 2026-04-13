import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { contractsAPI } from '../services/api';
import { useAuthStore } from '../store/authStore';
import {
  FileText,
  Plus,
  Shield,
  AlertTriangle,
  Clock,
  CheckCircle,
  BookOpen,
  FolderOpen,
  ArrowRight,
  TrendingUp,
  Activity,
} from 'lucide-react';

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const { data: contractsData } = useQuery({
    queryKey: ['contracts'],
    queryFn: () => contractsAPI.list({ page: 1, page_size: 10 }),
  });

  const contracts = contractsData?.data?.contracts || [];
  const totalContracts = contractsData?.data?.total || 0;

  const inReview = contracts.filter((c: { status: string }) => c.status === 'in_review').length;
  const approved = contracts.filter((c: { status: string }) => c.status === 'approved').length;
  const highRisk = contracts.filter((c: { ai_confidence_score?: number }) => (c.ai_confidence_score || 0) < 0.7).length;

  const stats = [
    { label: 'Total Contracts', value: totalContracts, icon: FileText, color: 'bg-blue-500', trend: '+12%' },
    { label: 'Under Review', value: inReview, icon: Clock, color: 'bg-yellow-500', trend: '' },
    { label: 'Approved', value: approved, icon: CheckCircle, color: 'bg-green-500', trend: '+8%' },
    { label: 'High Risk', value: highRisk, icon: AlertTriangle, color: 'bg-red-500', trend: '' },
  ];

  // Mock analytics data
  const weeklyActivity = [
    { day: 'Mon', contracts: 3, reviews: 2 },
    { day: 'Tue', contracts: 5, reviews: 4 },
    { day: 'Wed', contracts: 2, reviews: 1 },
    { day: 'Thu', contracts: 7, reviews: 5 },
    { day: 'Fri', contracts: 4, reviews: 3 },
    { day: 'Sat', contracts: 1, reviews: 0 },
    { day: 'Sun', contracts: 0, reviews: 0 },
  ];
  const maxActivity = Math.max(...weeklyActivity.map((d) => d.contracts));

  const riskDistribution = [
    { label: 'Low Risk', value: 45, color: 'bg-green-500' },
    { label: 'Medium Risk', value: 35, color: 'bg-yellow-500' },
    { label: 'High Risk', value: 20, color: 'bg-red-500' },
  ];

  const complianceStatus = [
    { label: 'GDPR Compliant', value: 78, color: 'text-green-600' },
    { label: 'HIPAA Checked', value: 65, color: 'text-blue-600' },
    { label: 'SOX Verified', value: 42, color: 'text-purple-600' },
  ];

  const recentActivity = [
    { action: 'Contract Generated', detail: 'NDA Agreement — Mutual', time: '2 min ago', icon: Plus, color: 'bg-green-100 text-green-600' },
    { action: 'Risk Analysis', detail: 'Employment Contract — High Risk', time: '15 min ago', icon: AlertTriangle, color: 'bg-red-100 text-red-600' },
    { action: 'Compliance Check', detail: 'SaaS Agreement — GDPR Passed', time: '1 hour ago', icon: Shield, color: 'bg-blue-100 text-blue-600' },
    { action: 'Contract Approved', detail: 'Service Agreement — MSA', time: '3 hours ago', icon: CheckCircle, color: 'bg-green-100 text-green-600' },
    { action: 'Version Created', detail: 'NDA v1.2 — added arbitration clause', time: '5 hours ago', icon: FileText, color: 'bg-purple-100 text-purple-600' },
  ];

  return (
    <main className="p-8" aria-labelledby="dashboard-heading">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 id="dashboard-heading" className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.full_name?.split(' ')[0]}
          </h1>
          <p className="text-gray-500 mt-1">
            Here&apos;s an overview of your legal contract operations.
          </p>
        </div>
        <Link
          to="/generate"
          className="flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          New Contract
        </Link>
      </div>

      {/* Stats Grid */}
      <section aria-label="Key Statistics" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map(({ label, value, icon: Icon, color, trend }) => (
          <article key={label} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">{label}</p>
                <div className="flex items-center gap-2">
                  <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
                  {trend && (
                    <span className="text-xs text-green-600 bg-green-50 px-1.5 py-0.5 rounded-full flex items-center gap-0.5 mt-2">
                      <TrendingUp className="w-3 h-3" />
                      {trend}
                    </span>
                  )}
                </div>
              </div>
              <div className={`${color} p-3 rounded-lg`} aria-hidden="true">
                <Icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </article>
        ))}
      </section>

      {/* Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Weekly Activity Chart */}
        <section aria-labelledby="weekly-activity-heading" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <h2 id="weekly-activity-heading" className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary-600" />
              Weekly Activity
            </h2>
            <span className="text-xs text-gray-400">Last 7 days</span>
          </div>
          <div className="flex items-end gap-3 h-40">
            {weeklyActivity.map(({ day, contracts: c, reviews }) => (
              <div key={day} className="flex-1 flex flex-col items-center gap-1">
                <div className="w-full flex flex-col items-center gap-1" style={{ height: '130px', justifyContent: 'flex-end' }}>
                  <div
                    className="w-full bg-primary-500 rounded-t-md transition-all"
                    style={{ height: `${maxActivity > 0 ? (c / maxActivity) * 100 : 0}%`, minHeight: c > 0 ? '6px' : '0' }}
                    title={`${c} contracts`}
                  />
                  <div
                    className="w-full bg-primary-200 rounded-t-md transition-all"
                    style={{ height: `${maxActivity > 0 ? (reviews / maxActivity) * 80 : 0}%`, minHeight: reviews > 0 ? '4px' : '0' }}
                    title={`${reviews} reviews`}
                  />
                </div>
                <span className="text-xs text-gray-400 mt-1">{day}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-primary-500 rounded" /> Contracts
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-primary-200 rounded" /> Reviews
            </span>
          </div>
        </section>

        {/* Risk Distribution */}
        <section aria-labelledby="risk-distribution-heading" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 id="risk-distribution-heading" className="text-lg font-semibold text-gray-900 mb-6">Risk Distribution</h2>
          <div className="space-y-4">
            {riskDistribution.map(({ label, value, color }) => (
              <div key={label}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-600">{label}</span>
                  <span className="text-sm font-semibold text-gray-900">{value}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2.5">
                  <div
                    className={`${color} rounded-full h-2.5 transition-all duration-500`}
                    style={{ width: `${value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Compliance Status */}
          <h3 className="text-sm font-semibold text-gray-700 mt-8 mb-4">Compliance Status</h3>
          <div className="space-y-3">
            {complianceStatus.map(({ label, value, color }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-sm text-gray-500">{label}</span>
                <span className={`text-sm font-bold ${color}`}>{value}%</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Quick Actions & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Quick Actions */}
        <nav aria-label="Quick Actions" className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <Link
            to="/generate"
            className="flex items-center gap-3 p-4 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span className="font-medium">Generate Contract</span>
            <ArrowRight className="w-4 h-4 ml-auto" />
          </Link>
          <Link
            to="/templates"
            className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-primary-300 transition-colors"
          >
            <FolderOpen className="w-5 h-5 text-primary-600" />
            <span className="font-medium text-gray-900">Browse Templates</span>
            <ArrowRight className="w-4 h-4 ml-auto text-gray-400" />
          </Link>
          <Link
            to="/clauses"
            className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-primary-300 transition-colors"
          >
            <BookOpen className="w-5 h-5 text-primary-600" />
            <span className="font-medium text-gray-900">Clause Library</span>
            <ArrowRight className="w-4 h-4 ml-auto text-gray-400" />
          </Link>
          <Link
            to="/risk-analysis"
            className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-orange-300 transition-colors"
          >
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            <span className="font-medium text-gray-900">Risk Analysis</span>
            <ArrowRight className="w-4 h-4 ml-auto text-gray-400" />
          </Link>
          <Link
            to="/compliance"
            className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-green-300 transition-colors"
          >
            <Shield className="w-5 h-5 text-green-500" />
            <span className="font-medium text-gray-900">Compliance Check</span>
            <ArrowRight className="w-4 h-4 ml-auto text-gray-400" aria-hidden="true" />
          </Link>
        </nav>

        {/* Recent Activity Feed */}
        <section aria-labelledby="recent-activity-heading" className="lg:col-span-2">
          <h2 id="recent-activity-heading" className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="divide-y divide-gray-50">
              {recentActivity.map((item, i) => (
                <div key={i} className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors">
                  <div className={`p-2 rounded-lg ${item.color}`}>
                    <item.icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">{item.action}</p>
                    <p className="text-xs text-gray-500 truncate">{item.detail}</p>
                  </div>
                  <span className="text-xs text-gray-400 whitespace-nowrap">{item.time}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      {/* Recent Contracts */}
      <section aria-labelledby="recent-contracts-heading" className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <h2 id="recent-contracts-heading" className="text-lg font-semibold text-gray-900">Recent Contracts</h2>
          <Link to="/generate" className="text-sm text-primary-600 hover:text-primary-700">
            View All
          </Link>
        </div>

        {contracts.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No contracts yet. Generate your first contract!</p>
            <Link
              to="/generate"
              className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              <Plus className="w-4 h-4" />
              Generate Contract
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {contracts.slice(0, 5).map((contract: {
              id: string;
              title: string;
              contract_type: string;
              status: string;
              updated_at: string;
              ai_confidence_score?: number;
            }) => (
              <Link
                key={contract.id}
                to={`/contracts/${contract.id}`}
                className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-primary-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{contract.title}</p>
                    <p className="text-sm text-gray-500">
                      {contract.contract_type} &middot; {new Date(contract.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${contract.status === 'draft'
                      ? 'bg-gray-100 text-gray-600'
                      : contract.status === 'approved'
                        ? 'bg-green-100 text-green-700'
                        : contract.status === 'in_review'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                  >
                    {contract.status}
                  </span>
                  {contract.ai_confidence_score && (
                    <span className="text-sm text-gray-500">
                      {(contract.ai_confidence_score * 100).toFixed(0)}% confidence
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
