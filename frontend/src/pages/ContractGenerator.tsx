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
  { value: 'license', label: 'Software License Agreement' },
  { value: 'partnership', label: 'Partnership Agreement' },
  { value: 'merger_acquisition', label: 'Merger & Acquisition' },
  { value: 'lease', label: 'Commercial Lease Agreement' },
];

const JURISDICTIONS = [
  'US-Federal', 'US-CA', 'US-NY', 'US-TX', 'US-FL',
  'EU', 'UK', 'HIPAA',
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
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Sparkles className="w-8 h-8 text-primary-600" />
          Generate Contract
        </h1>
        <p className="text-gray-500 mt-1">
          Create a new AI-powered legal contract using templates and LLM enhancement.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Info */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Contract Details</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contract Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="e.g., NDA between Company A and Company B"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contract Type
              </label>
              <select
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
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Jurisdiction
              </label>
              <select
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
        </div>

        {/* Parties */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Contract Parties</h2>
            <button
              type="button"
              onClick={addParty}
              className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
            >
              <Plus className="w-4 h-4" />
              Add Party
            </button>
          </div>

          <div className="space-y-4">
            {parties.map((party, index) => (
              <div key={index} className="flex gap-4 items-start">
                <div className="flex-1">
                  <input
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
                  <input
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
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Variables */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Contract Variables</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Effective Date</label>
              <input
                type="date"
                value={variables.effective_date}
                onChange={(e) => setVariables({ ...variables, effective_date: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Term (Years)</label>
              <input
                type="number"
                value={variables.term_years}
                onChange={(e) => setVariables({ ...variables, term_years: e.target.value })}
                min="1"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Governing State</label>
              <input
                type="text"
                value={variables.governing_state}
                onChange={(e) => setVariables({ ...variables, governing_state: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        </div>

        {/* AI Enhancement */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Enhancement</h2>

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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Special Requirements
            </label>
            <textarea
              value={specialRequirements}
              onChange={(e) => setSpecialRequirements(e.target.value)}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              placeholder="Any specific clauses, provisions, or requirements..."
            />
          </div>
        </div>

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
            className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {generateMutation.isPending ? (
              <>Generating...</>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Generate Contract
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
