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
} from 'lucide-react';

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const { data: contractsData } = useQuery({
    queryKey: ['contracts'],
    queryFn: () => contractsAPI.list({ page: 1, page_size: 5 }),
  });

  const contracts = contractsData?.data?.contracts || [];
  const totalContracts = contractsData?.data?.total || 0;

  const stats = [
    { label: 'Total Contracts', value: totalContracts, icon: FileText, color: 'bg-blue-500' },
    { label: 'Under Review', value: contracts.filter((c: { status: string }) => c.status === 'in_review').length, icon: Clock, color: 'bg-yellow-500' },
    { label: 'Approved', value: contracts.filter((c: { status: string }) => c.status === 'approved').length, icon: CheckCircle, color: 'bg-green-500' },
    { label: 'High Risk', value: contracts.filter((c: { ai_confidence_score?: number }) => (c.ai_confidence_score || 0) < 0.7).length, icon: AlertTriangle, color: 'bg-red-500' },
  ];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.full_name?.split(' ')[0]}
        </h1>
        <p className="text-gray-500 mt-1">
          Here&apos;s an overview of your legal contract operations.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">{label}</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
              </div>
              <div className={`${color} p-3 rounded-lg`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Link
          to="/generate"
          className="bg-primary-600 text-white rounded-xl p-6 hover:bg-primary-700 transition-colors group"
        >
          <Plus className="w-8 h-8 mb-3" />
          <h3 className="text-lg font-semibold">Generate Contract</h3>
          <p className="text-primary-200 text-sm mt-1">
            Create a new AI-powered legal contract
          </p>
        </Link>

        <Link
          to="/risk-analysis"
          className="bg-white border-2 border-orange-200 rounded-xl p-6 hover:border-orange-400 transition-colors"
        >
          <AlertTriangle className="w-8 h-8 mb-3 text-orange-500" />
          <h3 className="text-lg font-semibold text-gray-900">Risk Analysis</h3>
          <p className="text-gray-500 text-sm mt-1">
            Analyze contracts for potential risks
          </p>
        </Link>

        <Link
          to="/compliance"
          className="bg-white border-2 border-green-200 rounded-xl p-6 hover:border-green-400 transition-colors"
        >
          <Shield className="w-8 h-8 mb-3 text-green-500" />
          <h3 className="text-lg font-semibold text-gray-900">Compliance Check</h3>
          <p className="text-gray-500 text-sm mt-1">
            Verify regulatory compliance
          </p>
        </Link>
      </div>

      {/* Recent Contracts */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Recent Contracts</h2>
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
            {contracts.map((contract: {
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
      </div>
    </div>
  );
}
