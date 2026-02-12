import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { contractsAPI, reviewAPI, complianceAPI } from '../services/api';
import {
  Shield,
  AlertTriangle,
  GitBranch,
  Copy,
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function ContractView() {
  const { id } = useParams<{ id: string }>();

  const { data: contractData, isLoading } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => contractsAPI.get(id!),
    enabled: !!id,
  });

  const riskMutation = useMutation({
    mutationFn: () => reviewAPI.analyzeRisk({ contract_id: id }),
    onSuccess: () => toast.success('Risk analysis complete!'),
    onError: () => toast.error('Risk analysis failed'),
  });

  const complianceMutation = useMutation({
    mutationFn: () => complianceAPI.check({ contract_id: id, jurisdictions: [contract?.jurisdiction || 'US-Federal'] }),
    onSuccess: () => toast.success('Compliance check complete!'),
    onError: () => toast.error('Compliance check failed'),
  });

  const contract = contractData?.data;

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500">Contract not found.</p>
      </div>
    );
  }

  const copyContent = () => {
    navigator.clipboard.writeText(contract.content);
    toast.success('Content copied to clipboard');
  };

  const statusColor: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700',
    in_review: 'bg-yellow-100 text-yellow-700',
    approved: 'bg-green-100 text-green-700',
    executed: 'bg-blue-100 text-blue-700',
    uploaded: 'bg-purple-100 text-purple-700',
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{contract.title}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColor[contract.status] || 'bg-gray-100 text-gray-700'}`}>
              {contract.status}
            </span>
            <span className="text-sm text-gray-500">{contract.contract_type}</span>
            <span className="text-sm text-gray-500">{contract.jurisdiction}</span>
            {contract.ai_confidence_score && (
              <span className="text-sm text-gray-500">
                {(contract.ai_confidence_score * 100).toFixed(0)}% AI confidence
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={copyContent}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
          >
            <Copy className="w-4 h-4" />
            Copy
          </button>
          <Link
            to={`/versions/${contract.id}`}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
          >
            <GitBranch className="w-4 h-4" />
            Versions
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Contract Content</h2>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono bg-gray-50 p-4 rounded-lg overflow-auto max-h-[600px]">
                {contract.content}
              </pre>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Actions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Actions</h3>
            <div className="space-y-3">
              <button
                onClick={() => riskMutation.mutate()}
                disabled={riskMutation.isPending}
                className="w-full flex items-center gap-3 px-4 py-3 bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 transition-colors text-sm"
              >
                <AlertTriangle className="w-5 h-5" />
                {riskMutation.isPending ? 'Analyzing...' : 'Run Risk Analysis'}
              </button>
              <button
                onClick={() => complianceMutation.mutate()}
                disabled={complianceMutation.isPending}
                className="w-full flex items-center gap-3 px-4 py-3 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors text-sm"
              >
                <Shield className="w-5 h-5" />
                {complianceMutation.isPending ? 'Checking...' : 'Check Compliance'}
              </button>
            </div>
          </div>

          {/* Parties */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Parties</h3>
            {contract.parties.length > 0 ? (
              <div className="space-y-3">
                {contract.parties.map((party: { name: string; role: string }, i: number) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-sm font-medium text-primary-700">
                      {party.name?.charAt(0) || '?'}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{party.name}</p>
                      <p className="text-xs text-gray-500">{party.role}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No parties specified</p>
            )}
          </div>

          {/* Metadata */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Details</h3>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">Created</dt>
                <dd className="font-medium">{new Date(contract.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Updated</dt>
                <dd className="font-medium">{new Date(contract.updated_at).toLocaleString()}</dd>
              </div>
              {contract.content_hash && (
                <div>
                  <dt className="text-gray-500">Content Hash</dt>
                  <dd className="font-mono text-xs break-all">{contract.content_hash}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Risk Analysis Results */}
          {riskMutation.data && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Risk Analysis</h3>
              <div className="text-center mb-4">
                <div className={`text-3xl font-bold ${
                  riskMutation.data.data.overall_risk_score >= 0.7 ? 'text-red-600' :
                  riskMutation.data.data.overall_risk_score >= 0.4 ? 'text-yellow-600' : 'text-green-600'
                }`}>
                  {(riskMutation.data.data.overall_risk_score * 100).toFixed(0)}%
                </div>
                <p className="text-sm text-gray-500">Overall Risk Score</p>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-red-50 p-2 rounded text-center">
                  <span className="font-bold text-red-700">{riskMutation.data.data.critical_count}</span>
                  <span className="text-red-600 block">Critical</span>
                </div>
                <div className="bg-orange-50 p-2 rounded text-center">
                  <span className="font-bold text-orange-700">{riskMutation.data.data.high_count}</span>
                  <span className="text-orange-600 block">High</span>
                </div>
                <div className="bg-yellow-50 p-2 rounded text-center">
                  <span className="font-bold text-yellow-700">{riskMutation.data.data.medium_count}</span>
                  <span className="text-yellow-600 block">Medium</span>
                </div>
                <div className="bg-green-50 p-2 rounded text-center">
                  <span className="font-bold text-green-700">{riskMutation.data.data.low_count}</span>
                  <span className="text-green-600 block">Low</span>
                </div>
              </div>
            </div>
          )}

          {/* Compliance Results */}
          {complianceMutation.data && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Compliance</h3>
              <div className="text-center mb-4">
                <div className={`text-3xl font-bold ${
                  complianceMutation.data.data.overall_score >= 0.8 ? 'text-green-600' :
                  complianceMutation.data.data.overall_score >= 0.6 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {(complianceMutation.data.data.overall_score * 100).toFixed(0)}%
                </div>
                <p className="text-sm text-gray-500">Compliance Score</p>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Compliant</span>
                  <span className="font-medium text-green-600">{complianceMutation.data.data.compliant_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Non-Compliant</span>
                  <span className="font-medium text-red-600">{complianceMutation.data.data.non_compliant_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Partial</span>
                  <span className="font-medium text-yellow-600">{complianceMutation.data.data.partial_count}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
