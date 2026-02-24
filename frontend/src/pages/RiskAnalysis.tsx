import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { reviewAPI } from '../services/api';
import { AlertTriangle, Search, BarChart3 } from 'lucide-react';
import toast from 'react-hot-toast';

interface RiskFactor {
  category: string;
  name: string;
  severity: string;
  description: string;
  recommendation: string;
  confidence: number;
}

interface AnalysisResult {
  analysis_id: string;
  overall_risk_score: number;
  risk_level: string;
  total_factors: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  risk_factors: RiskFactor[];
  executive_summary: string;
  recommendations: string[];
}

export default function RiskAnalysis() {
  const [content, setContent] = useState('');
  const [contractType, setContractType] = useState('general');
  const [jurisdiction, setJurisdiction] = useState('US-Federal');
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const analyzeMutation = useMutation({
    mutationFn: () =>
      reviewAPI.analyzeRisk({ content, contract_type: contractType, jurisdiction }),
    onSuccess: (response) => {
      setResult(response.data);
      toast.success('Risk analysis complete!');
    },
    onError: () => toast.error('Analysis failed'),
  });

  const severityColor: Record<string, string> = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-green-100 text-green-800 border-green-200',
  };

  const riskScoreColor = (score: number) =>
    score >= 0.7 ? 'text-red-600' : score >= 0.4 ? 'text-yellow-600' : 'text-green-600';

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <AlertTriangle className="w-8 h-8 text-orange-500" />
          Risk Analysis
        </h1>
        <p className="text-gray-500 mt-1">
          Analyze contract content for potential legal, financial, and operational risks.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Contract Content</h2>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contract Type</label>
                <select
                  value={contractType}
                  onChange={(e) => setContractType(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  <option value="general">General</option>
                  <option value="nda">NDA</option>
                  <option value="employment">Employment</option>
                  <option value="service_agreement">Service Agreement</option>
                  <option value="msa">MSA</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Jurisdiction</label>
                <select
                  value={jurisdiction}
                  onChange={(e) => setJurisdiction(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  <optgroup label="North America">
                    <option value="US-Federal">US Federal</option>
                    <option value="US-CA">US — California</option>
                    <option value="US-NY">US — New York</option>
                    <option value="US-TX">US — Texas</option>
                    <option value="US-FL">US — Florida</option>
                    <option value="CA">Canada</option>
                    <option value="MX">Mexico</option>
                  </optgroup>
                  <optgroup label="Europe">
                    <option value="EU">European Union</option>
                    <option value="UK">United Kingdom</option>
                    <option value="DE">Germany</option>
                    <option value="FR">France</option>
                    <option value="IT">Italy</option>
                    <option value="ES">Spain</option>
                    <option value="NL">Netherlands</option>
                    <option value="CH">Switzerland</option>
                  </optgroup>
                  <optgroup label="Asia Pacific">
                    <option value="IN">India</option>
                    <option value="CN">China</option>
                    <option value="JP">Japan</option>
                    <option value="SG">Singapore</option>
                    <option value="AU">Australia</option>
                    <option value="KR">South Korea</option>
                    <option value="HK">Hong Kong</option>
                    <option value="MY">Malaysia</option>
                    <option value="ID">Indonesia</option>
                    <option value="PH">Philippines</option>
                    <option value="NZ">New Zealand</option>
                  </optgroup>
                  <optgroup label="Middle East & Africa">
                    <option value="AE">United Arab Emirates</option>
                    <option value="SA">Saudi Arabia</option>
                    <option value="IL">Israel</option>
                    <option value="ZA">South Africa</option>
                    <option value="NG">Nigeria</option>
                    <option value="KE">Kenya</option>
                  </optgroup>
                  <optgroup label="South America">
                    <option value="BR">Brazil</option>
                    <option value="AR">Argentina</option>
                    <option value="CL">Chile</option>
                    <option value="CO">Colombia</option>
                  </optgroup>
                  <optgroup label="Regulatory Frameworks">
                    <option value="HIPAA">HIPAA (US Healthcare)</option>
                    <option value="GDPR">GDPR (EU Data Privacy)</option>
                  </optgroup>
                </select>
              </div>
            </div>

            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={16}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm"
              placeholder="Paste your contract content here for risk analysis..."
            />

            <div className="mt-4 flex justify-end">
              <button
                onClick={() => analyzeMutation.mutate()}
                disabled={!content.trim() || analyzeMutation.isPending}
                className="flex items-center gap-2 px-6 py-3 bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600 disabled:opacity-50 transition-colors"
              >
                {analyzeMutation.isPending ? (
                  'Analyzing...'
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    Analyze Risk
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Results Summary */}
        <div className="space-y-6">
          {result ? (
            <>
              {/* Score */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
                <h3 className="font-semibold text-gray-900 mb-2">Overall Risk Score</h3>
                <div className={`text-5xl font-bold ${riskScoreColor(result.overall_risk_score)}`}>
                  {(result.overall_risk_score * 100).toFixed(0)}%
                </div>
                <span className={`inline-block mt-2 px-3 py-1 rounded-full text-sm font-medium ${severityColor[result.risk_level] || 'bg-gray-100 text-gray-700'
                  }`}>
                  {result.risk_level.toUpperCase()}
                </span>
              </div>

              {/* Breakdown */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Risk Breakdown</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-red-600 font-medium">Critical</span>
                    <span className="bg-red-100 text-red-800 px-2 py-0.5 rounded text-sm font-bold">{result.critical_count}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-orange-600 font-medium">High</span>
                    <span className="bg-orange-100 text-orange-800 px-2 py-0.5 rounded text-sm font-bold">{result.high_count}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-yellow-600 font-medium">Medium</span>
                    <span className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded text-sm font-bold">{result.medium_count}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-green-600 font-medium">Low</span>
                    <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded text-sm font-bold">{result.low_count}</span>
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <h3 className="font-semibold text-gray-900 mb-2">Executive Summary</h3>
                <p className="text-sm text-gray-600">{result.executive_summary}</p>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
              <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">
                Paste contract content and click &quot;Analyze Risk&quot; to see results.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Detailed Risk Factors */}
      {result && result.risk_factors.length > 0 && (
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">
              Risk Factors ({result.total_factors})
            </h2>
          </div>
          <div className="divide-y divide-gray-100">
            {result.risk_factors.map((factor, i) => (
              <div key={i} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${severityColor[factor.severity]}`}>
                      {factor.severity}
                    </span>
                    <span className="font-medium text-gray-900">{factor.name}</span>
                    <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                      {factor.category}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {(factor.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-1">{factor.description}</p>
                <p className="text-sm text-primary-600">
                  <strong>Recommendation:</strong> {factor.recommendation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {result && result.recommendations.length > 0 && (
        <div className="mt-6 bg-blue-50 rounded-xl border border-blue-200 p-6">
          <h3 className="font-semibold text-blue-900 mb-3">Recommendations</h3>
          <ul className="space-y-2">
            {result.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-blue-800">
                <span className="text-blue-500 mt-0.5">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
