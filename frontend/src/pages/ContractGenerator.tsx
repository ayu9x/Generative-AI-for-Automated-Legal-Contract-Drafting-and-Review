import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { contractsAPI } from '../services/api';
import { Sparkles, Plus, X } from 'lucide-react';
import toast from 'react-hot-toast';

const CONTRACT_TYPES = [
  { value: 'nda', label: 'Non-Disclosure Agreement (NDA)' },
  { value: 'msa', label: 'Master Service Agreement (MSA)' },
  { value: 'employment', label: 'Employment Agreement' },
  { value: 'service_agreement', label: 'Service Agreement' },
  { value: 'consulting', label: 'Consulting Agreement' },
  { value: 'license', label: 'Software License Agreement' },
  { value: 'partnership', label: 'Partnership Agreement' },
  { value: 'merger_acquisition', label: 'Merger & Acquisition' },
  { value: 'lease', label: 'Commercial Lease Agreement' },
  { value: 'purchase_order', label: 'Purchase Order Agreement' },
  { value: 'loan', label: 'Loan Agreement' },
  { value: 'supply', label: 'Supply Agreement' },
  { value: 'distribution', label: 'Distribution Agreement' },
  { value: 'franchise', label: 'Franchise Agreement' },
  { value: 'joint_venture', label: 'Joint Venture Agreement' },
  { value: 'settlement', label: 'Settlement Agreement' },
];

const JURISDICTIONS = [
  // North America
  'US-Federal', 'US-CA', 'US-NY', 'US-TX', 'US-FL', 'US-IL',
  'US-DE', 'US-WA', 'US-MA', 'US-GA', 'US-PA',
  'CA-Federal', 'CA-ON', 'CA-BC', 'CA-QC', 'MX',
  // Europe
  'UK', 'EU-GDPR', 'EU-DE', 'EU-FR', 'EU-ES',
  'CH', 'SE', 'NO', 'DK', 'FI', 'NL', 'BE', 'IT', 'AT', 'IE',
  // Asia Pacific
  'IN', 'JP', 'SG', 'AU', 'KR', 'HK', 'MY', 'PH', 'TH', 'NZ',
  // Middle East & Africa
  'AE', 'SA', 'IL', 'ZA', 'NG', 'KE',
  // South America
  'BR',
];

interface Party {
  name: string;
  role: string;
  address?: string;
}

export default function ContractGenerator() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [contractType, setContractType] = useState('nda');
  const [jurisdiction, setJurisdiction] = useState('US-Federal');
  const [parties, setParties] = useState<Party[]>([
    { name: '', role: 'Disclosing Party' },
    { name: '', role: 'Receiving Party' },
  ]);
  const [specialRequirements, setSpecialRequirements] = useState('');
  const [useAI, setUseAI] = useState(true);
  const [variables, setVariables] = useState<Record<string, string>>({
    effective_date: new Date().toISOString().split('T')[0],
    term_years: '2',
    governing_state: 'Delaware',
  });

  const generateMutation = useMutation({
    mutationFn: (data: Parameters<typeof contractsAPI.generate>[0]) =>
      contractsAPI.generate(data),
    onSuccess: (response) => {
      toast.success('Contract generated successfully!');
      navigate(`/contracts/${response.data.id}`);
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Generation failed');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      toast.error('Please enter a contract title');
      return;
    }
    if (parties.some((p) => !p.name.trim())) {
      toast.error('Please fill in all party names');
      return;
    }

    generateMutation.mutate({
      contract_type: contractType,
      title,
      parties,
      jurisdiction,
      variables,
      special_requirements: specialRequirements || undefined,
      use_ai_enhancement: useAI,
    });
  };

  const addParty = () => setParties([...parties, { name: '', role: 'Party' }]);
  const removeParty = (index: number) => {
    if (parties.length > 2) {
      setParties(parties.filter((_, i) => i !== index));
    }
  };

  return (
    <main className="p-8 max-w-4xl mx-auto" aria-labelledby="generator-heading">
      <div className="mb-8">
        <h1 id="generator-heading" className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Sparkles className="w-8 h-8 text-primary-600" aria-hidden="true" />
          Generate Contract
        </h1>
        <p id="generator-description" className="text-gray-500 mt-1">
          Create a new AI-powered legal contract using templates and LLM enhancement.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8" aria-labelledby="generator-heading" aria-describedby="generator-description">
        {/* Basic Info */}
        <section aria-labelledby="basic-info-heading" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 id="basic-info-heading" className="text-lg font-semibold text-gray-900 mb-4">Contract Details</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label htmlFor="contractTitle" className="block text-sm font-medium text-gray-700 mb-1">
                Contract Title
              </label>
              <input
                id="contractTitle"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                aria-required="true"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="e.g., NDA between Company A and Company B"
              />
            </div>

            <div>
              <label htmlFor="contractType" className="block text-sm font-medium text-gray-700 mb-1">
                Contract Type
              </label>
              <select
                id="contractType"
                value={contractType}
                onChange={(e) => setContractType(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                {CONTRACT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="jurisdiction" className="block text-sm font-medium text-gray-700 mb-1">
                Jurisdiction
              </label>
              <select
                id="jurisdiction"
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                {JURISDICTIONS.map((j) => (
                  <option key={j} value={j}>{j}</option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {/* Parties */}
        <section aria-labelledby="parties-heading" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 id="parties-heading" className="text-lg font-semibold text-gray-900">Contract Parties</h2>
            <button
              type="button"
              onClick={addParty}
              className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
              aria-label="Add a new party"
            >
              <Plus className="w-4 h-4" aria-hidden="true" />
              Add Party
            </button>
          </div>

          <div className="space-y-4" role="group" aria-label="Parties list">
            {parties.map((party, index) => (
              <div key={index} className="flex gap-4 items-start">
                <div className="flex-1">
                  <label htmlFor={`party-name-${index}`} className="sr-only">Party name {index + 1}</label>
                  <input
                    id={`party-name-${index}`}
                    type="text"
                    value={party.name}
                    onChange={(e) => {
                      const updated = [...parties];
                      updated[index].name = e.target.value;
                      setParties(updated);
                    }}
                    placeholder="Party name (e.g., Acme Corp)"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div className="w-48">
                  <label htmlFor={`party-role-${index}`} className="sr-only">Party role {index + 1}</label>
                  <input
                    id={`party-role-${index}`}
                    type="text"
                    value={party.role}
                    onChange={(e) => {
                      const updated = [...parties];
                      updated[index].role = e.target.value;
                      setParties(updated);
                    }}
                    placeholder="Role"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                {parties.length > 2 && (
                  <button
                    type="button"
                    onClick={() => removeParty(index)}
                    className="p-2 text-gray-400 hover:text-red-500"
                    aria-label={`Remove party ${index + 1}`}
                  >
                    <X className="w-5 h-5" aria-hidden="true" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Variables */}
        <section aria-labelledby="variables-heading" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 id="variables-heading" className="text-lg font-semibold text-gray-900 mb-4">Contract Variables</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="effectiveDate" className="block text-sm font-medium text-gray-700 mb-1">Effective Date</label>
              <input
                id="effectiveDate"
                type="date"
                value={variables.effective_date}
                onChange={(e) => setVariables({ ...variables, effective_date: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label htmlFor="termYears" className="block text-sm font-medium text-gray-700 mb-1">Term (Years)</label>
              <input
                id="termYears"
                type="number"
                value={variables.term_years}
                onChange={(e) => setVariables({ ...variables, term_years: e.target.value })}
                min="1"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label htmlFor="governingState" className="block text-sm font-medium text-gray-700 mb-1">Governing State</label>
              <input
                id="governingState"
                type="text"
                value={variables.governing_state}
                onChange={(e) => setVariables({ ...variables, governing_state: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        </section>

        {/* AI Enhancement */}
        <section aria-labelledby="ai-enhancement-heading" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 id="ai-enhancement-heading" className="text-lg font-semibold text-gray-900 mb-4">AI Enhancement</h2>

          <div className="flex items-center gap-3 mb-4">
            <input
              type="checkbox"
              id="useAI"
              checked={useAI}
              onChange={(e) => setUseAI(e.target.checked)}
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
            <label htmlFor="useAI" className="text-sm text-gray-700">
              Enable AI enhancement for more comprehensive language and coverage
            </label>
          </div>

          <div>
            <label htmlFor="specialReqs" className="block text-sm font-medium text-gray-700 mb-1">
              Special Requirements
            </label>
            <textarea
              id="specialReqs"
              value={specialRequirements}
              onChange={(e) => setSpecialRequirements(e.target.value)}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              placeholder="Any specific clauses, provisions, or requirements..."
            />
          </div>
        </section>

        {/* Submit */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={generateMutation.isPending}
            aria-busy={generateMutation.isPending}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {generateMutation.isPending ? (
              <>Generating...</>
            ) : (
              <>
                <Sparkles className="w-5 h-5" aria-hidden="true" />
                Generate Contract
              </>
            )}
          </button>
        </div>
      </form>
    </main>
  );
}
