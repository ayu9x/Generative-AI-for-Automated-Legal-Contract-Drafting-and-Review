import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { complianceAPI } from '../services/api';
import { Shield, CheckCircle, XCircle, AlertCircle, Globe } from 'lucide-react';
import toast from 'react-hot-toast';

interface ComplianceResult {
  check_id: string;
  overall_score: number;
  compliance_status: string;
  total_rules_checked: number;
  compliant_count: number;
  non_compliant_count: number;
  partial_count: number;
  not_applicable_count: number;
  rule_results: Array<{
    rule_id: string;
    rule_name: string;
    framework: string;
    category: string;
    status: string;
    severity: string;
    description: string;
    finding?: string;
    recommendation?: string;
  }>;
  framework_scores: Record<string, number>;
  jurisdictions_checked: string[];
  critical_violations: Array<Record<string, string>>;
  recommendations: string[];
}

const FRAMEWORKS = [
  { id: 'general', label: 'General Contract Law' },
  { id: 'gdpr', label: 'GDPR' },
  { id: 'hipaa', label: 'HIPAA' },
  { id: 'sox', label: 'SOX' },
  { id: 'ccpa', label: 'CCPA' },
  { id: 'employment', label: 'Employment Law' },
  { id: 'international', label: 'International Trade' },
  { id: 'anti_corruption', label: 'Anti-Corruption' },
];

export default function ComplianceCenter() {
  const [content, setContent] = useState('');
  const [contractType, _setContractType] = useState('general');
  const [selectedJurisdictions, setSelectedJurisdictions] = useState<string[]>(['US-Federal']);
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>(['general']);
  const [result, setResult] = useState<ComplianceResult | null>(null);

  const { data: jurisdictions } = useQuery({
    queryKey: ['jurisdictions'],
    queryFn: () => complianceAPI.listJurisdictions(),
  });

  const { data: updates } = useQuery({
    queryKey: ['regulatory-updates'],
    queryFn: () => complianceAPI.getUpdates(),
  });

  const checkMutation = useMutation({
    mutationFn: () =>
      complianceAPI.check({
        content,
        contract_type: contractType,
        jurisdictions: selectedJurisdictions,
        frameworks: selectedFrameworks,
      }),
    onSuccess: (response) => {
      setResult(response.data);
      toast.success('Compliance check complete!');
    },
    onError: () => toast.error('Compliance check failed'),
  });

  const toggleFramework = (id: string) => {
    setSelectedFrameworks((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    );
  };

  const toggleJurisdiction = (code: string) => {
    setSelectedJurisdictions((prev) =>
      prev.includes(code) ? prev.filter((j) => j !== code) : [...prev, code]
    );
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case 'compliant': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'non_compliant': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'partial': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default: return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Shield className="w-8 h-8 text-green-500" />
          Compliance Center
        </h1>
        <p className="text-gray-500 mt-1">
          Check contracts against regulatory frameworks and jurisdictional requirements.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Input */}
        <div className="col-span-2 space-y-6">
          {/* Frameworks */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance Frameworks</h2>
            <div className="flex flex-wrap gap-2">
              {FRAMEWORKS.map(({ id, label }) => (
                <button
                  key={id}
                  onClick={() => toggleFramework(id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedFrameworks.includes(id)
                      ? 'bg-green-100 text-green-800 border-2 border-green-300'
                      : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Jurisdictions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Globe className="w-5 h-5" />
              Jurisdictions
            </h2>
            <div className="flex flex-wrap gap-2">
              {(jurisdictions?.data || []).map((j: { code: string; name: string }) => (
                <button
                  key={j.code}
                  onClick={() => toggleJurisdiction(j.code)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedJurisdictions.includes(j.code)
                      ? 'bg-primary-100 text-primary-800 border-2 border-primary-300'
                      : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                  }`}
                >
                  {j.name}
                </button>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Contract Content</h2>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={12}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm"
              placeholder="Paste your contract content here..."
            />
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => checkMutation.mutate()}
                disabled={!content.trim() || checkMutation.isPending}
                className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                <Shield className="w-5 h-5" />
                {checkMutation.isPending ? 'Checking...' : 'Check Compliance'}
              </button>
            </div>
          </div>
        </div>

        {/* Results Sidebar */}
        <div className="space-y-6">
          {result ? (
            <>
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
                <h3 className="font-semibold text-gray-900 mb-2">Compliance Score</h3>
                <div className={`text-5xl font-bold ${
                  result.overall_score >= 0.8 ? 'text-green-600' :
                  result.overall_score >= 0.6 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {(result.overall_score * 100).toFixed(0)}%
                </div>
                <span className={`inline-block mt-2 px-3 py-1 rounded-full text-sm font-medium ${
                  result.compliance_status === 'compliant'
                    ? 'bg-green-100 text-green-800'
                    : result.compliance_status === 'partially_compliant'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {result.compliance_status.replace('_', ' ').toUpperCase()}
                </span>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Results Summary</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-green-600 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Compliant</span>
                    <span className="font-bold">{result.compliant_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-red-600 flex items-center gap-1"><XCircle className="w-3 h-3" /> Non-Compliant</span>
                    <span className="font-bold">{result.non_compliant_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-yellow-600 flex items-center gap-1"><AlertCircle className="w-3 h-3" /> Partial</span>
                    <span className="font-bold">{result.partial_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Not Applicable</span>
                    <span className="font-bold">{result.not_applicable_count}</span>
                  </div>
                </div>
              </div>

              {/* Framework Scores */}
              {Object.keys(result.framework_scores).length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Framework Scores</h3>
                  <div className="space-y-3">
                    {Object.entries(result.framework_scores).map(([framework, score]) => (
                      <div key={framework}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-600">{framework.toUpperCase()}</span>
                          <span className="font-medium">{(score * 100).toFixed(0)}%</span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full">
                          <div
                            className={`h-full rounded-full ${
                              score >= 0.8 ? 'bg-green-500' : score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${score * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
                <Shield className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">
                  Select frameworks and jurisdictions, paste content, and run the compliance check.
                </p>
              </div>

              {/* Regulatory Updates */}
              {updates?.data && updates.data.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Regulatory Updates</h3>
                  <div className="space-y-3">
                    {updates.data.slice(0, 3).map((update: { id: string; title: string; framework: string; impact_level: string; effective_date: string }) => (
                      <div key={update.id} className="border-l-4 border-primary-500 pl-3">
                        <p className="text-sm font-medium text-gray-900">{update.title}</p>
                        <p className="text-xs text-gray-500">
                          {update.framework.toUpperCase()} &middot; Effective {update.effective_date}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Detailed Rule Results */}
      {result && result.rule_results.length > 0 && (
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">
              Detailed Results ({result.total_rules_checked} rules checked)
            </h2>
          </div>
          <div className="divide-y divide-gray-100">
            {result.rule_results.map((rule, i) => (
              <div key={i} className="p-4">
                <div className="flex items-center gap-3 mb-1">
                  {statusIcon(rule.status)}
                  <span className="font-medium text-gray-900">{rule.rule_name}</span>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                    {rule.framework.toUpperCase()}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    rule.severity === 'critical' ? 'bg-red-100 text-red-700' :
                    rule.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>{rule.severity}</span>
                </div>
                <p className="text-sm text-gray-600 ml-7">{rule.description}</p>
                {rule.finding && (
                  <p className="text-sm text-red-600 ml-7 mt-1">Finding: {rule.finding}</p>
                )}
                {rule.recommendation && (
                  <p className="text-sm text-primary-600 ml-7 mt-1">Recommendation: {rule.recommendation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
