import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { contractsAPI } from '../services/api';
import {
    Search,
    Filter,
    FileText,
    Clock,
    AlertTriangle,
    CheckCircle2,
    ChevronDown,
    ChevronUp,
    X,
    Tag,
    Calendar,
    Building2,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const CONTRACT_TYPES = [
    'All Types', 'NDA', 'MSA', 'Employment', 'Service Agreement',
    'License', 'Partnership', 'Lease', 'Merger & Acquisition',
];

const RISK_LEVELS = ['All', 'Low', 'Medium', 'High', 'Critical'];
const STATUSES = ['All', 'Draft', 'Active', 'Under Review', 'Expired', 'Terminated'];
const SORT_OPTIONS = [
    { value: 'newest', label: 'Newest First' },
    { value: 'oldest', label: 'Oldest First' },
    { value: 'name_asc', label: 'Name A-Z' },
    { value: 'name_desc', label: 'Name Z-A' },
    { value: 'risk_high', label: 'Highest Risk' },
];

// Generate mock contracts for search demo
const generateMockContracts = () => [
    { id: 'c1', title: 'NDA — Acme Corp & TechVentures', type: 'NDA', status: 'Active', risk: 'Low', date: '2025-12-01', organization: 'Acme Corp', jurisdiction: 'US-Federal', summary: 'Standard mutual non-disclosure agreement for sharing confidential business information between parties.' },
    { id: 'c2', title: 'Master Service Agreement — CloudSync', type: 'MSA', status: 'Active', risk: 'Medium', date: '2025-11-15', organization: 'CloudSync Inc', jurisdiction: 'US-CA', summary: 'Master service agreement covering cloud infrastructure hosting and managed services.' },
    { id: 'c3', title: 'Employment Agreement — Sr. Developer', type: 'Employment', status: 'Under Review', risk: 'Low', date: '2026-01-10', organization: 'Legal AI Corp', jurisdiction: 'IN', summary: 'Full-time employment contract for senior developer role with standard benefits and IP assignment.' },
    { id: 'c4', title: 'SaaS License Agreement — DataFlow Pro', type: 'License', status: 'Active', risk: 'High', date: '2025-10-22', organization: 'DataFlow Systems', jurisdiction: 'EU', summary: 'Enterprise SaaS licensing with unlimited users, data processing addendum, and SLA requirements.' },
    { id: 'c5', title: 'Partnership Agreement — LegalTech Alliance', type: 'Partnership', status: 'Draft', risk: 'Medium', date: '2026-02-05', organization: 'LegalTech Global', jurisdiction: 'UK', summary: 'Strategic partnership for co-development of AI-powered legal tech products across EMEA.' },
    { id: 'c6', title: 'Commercial Lease — Downtown Office', type: 'Lease', status: 'Active', risk: 'Low', date: '2025-06-01', organization: 'PropCo LLC', jurisdiction: 'US-NY', summary: '5-year commercial lease for office space at 123 Main St with annual rent escalation clause.' },
    { id: 'c7', title: 'Service Agreement — Security Audit', type: 'Service Agreement', status: 'Expired', risk: 'Critical', date: '2024-08-15', organization: 'CyberShield', jurisdiction: 'US-Federal', summary: 'Annual security audit and penetration testing engagement. Contains critical liability gaps.' },
    { id: 'c8', title: 'M&A Letter of Intent — FinanceBot', type: 'Merger & Acquisition', status: 'Under Review', risk: 'High', date: '2026-02-20', organization: 'FinanceBot AI', jurisdiction: 'US-Federal', summary: 'Non-binding LOI for acquisition of FinanceBot AI. Key terms: $50M valuation, all-stock deal.' },
    { id: 'c9', title: 'NDA — Infosys Consulting India', type: 'NDA', status: 'Active', risk: 'Low', date: '2026-01-05', organization: 'Infosys Ltd', jurisdiction: 'IN', summary: 'Bilateral NDA for consulting engagement covering proprietary algorithms and training data.' },
    { id: 'c10', title: 'Employment Agreement — Legal Counsel Mumbai', type: 'Employment', status: 'Active', risk: 'Medium', date: '2026-02-01', organization: 'Legal AI Corp', jurisdiction: 'IN', summary: 'Employment contract for in-house legal counsel in Mumbai office. Includes non-compete and ESOP.' },
    { id: 'c11', title: 'Vendor Agreement — AWS Infrastructure', type: 'Service Agreement', status: 'Active', risk: 'Medium', date: '2025-09-01', organization: 'Amazon Web Services', jurisdiction: 'US-Federal', summary: 'Enterprise agreement for AWS cloud services including reserved instances and premium support.' },
    { id: 'c12', title: 'Franchise Agreement — LegalEase Bengaluru', type: 'Partnership', status: 'Draft', risk: 'High', date: '2026-02-18', organization: 'LegalEase India', jurisdiction: 'IN', summary: 'Franchise agreement for operating the LegalEase brand in Bengaluru territory with exclusivity clause.' },
];

export default function SmartSearch() {
    const navigate = useNavigate();
    const [query, setQuery] = useState('');
    const [showFilters, setShowFilters] = useState(false);
    const [selectedType, setSelectedType] = useState('All Types');
    const [selectedRisk, setSelectedRisk] = useState('All');
    const [selectedStatus, setSelectedStatus] = useState('All');
    const [sortBy, setSortBy] = useState('newest');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');

    const { data: contractsData } = useQuery({
        queryKey: ['contracts'],
        queryFn: () => contractsAPI.list(),
    });

    // Use real data if available, otherwise mock
    const allContracts = (contractsData?.data?.length > 0 ? contractsData.data : generateMockContracts()) as any[];

    // Filter logic
    const filtered = allContracts.filter((c: any) => {
        const q = query.toLowerCase();
        const matchesQuery = !query ||
            c.title?.toLowerCase().includes(q) ||
            c.summary?.toLowerCase().includes(q) ||
            c.organization?.toLowerCase().includes(q) ||
            c.type?.toLowerCase().includes(q);
        const matchesType = selectedType === 'All Types' || c.type === selectedType;
        const matchesRisk = selectedRisk === 'All' || c.risk === selectedRisk;
        const matchesStatus = selectedStatus === 'All' || c.status === selectedStatus;
        const matchesFrom = !dateFrom || c.date >= dateFrom;
        const matchesTo = !dateTo || c.date <= dateTo;
        return matchesQuery && matchesType && matchesRisk && matchesStatus && matchesFrom && matchesTo;
    });

    // Sort
    const sorted = [...filtered].sort((a: any, b: any) => {
        switch (sortBy) {
            case 'oldest': return a.date.localeCompare(b.date);
            case 'name_asc': return a.title.localeCompare(b.title);
            case 'name_desc': return b.title.localeCompare(a.title);
            case 'risk_high': {
                const order: Record<string, number> = { Critical: 0, High: 1, Medium: 2, Low: 3 };
                return (order[a.risk] ?? 4) - (order[b.risk] ?? 4);
            }
            default: return b.date.localeCompare(a.date);
        }
    });

    const activeFilters = [selectedType !== 'All Types', selectedRisk !== 'All', selectedStatus !== 'All', !!dateFrom, !!dateTo].filter(Boolean).length;

    const clearFilters = () => {
        setSelectedType('All Types');
        setSelectedRisk('All');
        setSelectedStatus('All');
        setDateFrom('');
        setDateTo('');
    };

    const riskBadge = (risk: string) => {
        const colors: Record<string, string> = {
            Low: 'bg-green-100 text-green-700',
            Medium: 'bg-yellow-100 text-yellow-700',
            High: 'bg-orange-100 text-orange-700',
            Critical: 'bg-red-100 text-red-700',
        };
        return colors[risk] || 'bg-gray-100 text-gray-600';
    };

    const statusBadge = (s: string) => {
        const colors: Record<string, string> = {
            Active: 'bg-emerald-100 text-emerald-700',
            Draft: 'bg-gray-100 text-gray-600',
            'Under Review': 'bg-blue-100 text-blue-700',
            Expired: 'bg-red-50 text-red-600',
            Terminated: 'bg-red-100 text-red-800',
        };
        return colors[s] || 'bg-gray-100 text-gray-600';
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <Search className="w-8 h-8 text-violet-500" />
                    Smart Contract Search
                </h1>
                <p className="text-gray-500 mt-1">
                    Find contracts instantly with full-text search and intelligent filters.
                </p>
            </div>

            {/* Search Bar */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
                <div className="flex items-center gap-3">
                    <div className="flex-1 relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search by title, organization, type, content..."
                            className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 text-sm"
                        />
                        {query && (
                            <button onClick={() => setQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                                <X className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={`flex items-center gap-2 px-4 py-3 rounded-lg border text-sm font-medium transition-colors ${showFilters ? 'bg-violet-50 border-violet-300 text-violet-700' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}
                    >
                        <Filter className="w-4 h-4" />
                        Filters
                        {activeFilters > 0 && (
                            <span className="bg-violet-600 text-white text-xs px-1.5 py-0.5 rounded-full">{activeFilters}</span>
                        )}
                        {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="px-4 py-3 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500"
                    >
                        {SORT_OPTIONS.map((o) => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                    </select>
                </div>

                {/* Filter Panel */}
                {showFilters && (
                    <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-2 md:grid-cols-5 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-gray-500 mb-1">Contract Type</label>
                            <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
                                {CONTRACT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gray-500 mb-1">Risk Level</label>
                            <select value={selectedRisk} onChange={(e) => setSelectedRisk(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
                                {RISK_LEVELS.map((r) => <option key={r} value={r}>{r}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
                            <select value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
                                {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gray-500 mb-1">From Date</label>
                            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gray-500 mb-1">To Date</label>
                            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
                        </div>
                        {activeFilters > 0 && (
                            <div className="col-span-full">
                                <button onClick={clearFilters} className="text-sm text-violet-600 hover:text-violet-800 font-medium">
                                    Clear all filters
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Results Count */}
            <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-gray-500">
                    <span className="font-semibold text-gray-900">{sorted.length}</span> contract{sorted.length !== 1 ? 's' : ''} found
                </p>
            </div>

            {/* Results */}
            <div className="space-y-3">
                {sorted.length === 0 ? (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
                        <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                        <p className="text-gray-500">No contracts match your search criteria.</p>
                        <button onClick={clearFilters} className="mt-3 text-sm text-violet-600 hover:underline">Clear filters</button>
                    </div>
                ) : (
                    sorted.map((contract: any) => (
                        <div
                            key={contract.id}
                            onClick={() => navigate(`/contracts/${contract.id}`)}
                            className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md hover:border-violet-200 transition-all cursor-pointer group"
                        >
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-violet-100 rounded-lg flex items-center justify-center group-hover:bg-violet-200 transition-colors">
                                        <FileText className="w-5 h-5 text-violet-600" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-900 group-hover:text-violet-700 transition-colors">{contract.title}</h3>
                                        <div className="flex items-center gap-3 mt-1">
                                            <span className="flex items-center gap-1 text-xs text-gray-500">
                                                <Building2 className="w-3 h-3" /> {contract.organization}
                                            </span>
                                            <span className="flex items-center gap-1 text-xs text-gray-500">
                                                <Calendar className="w-3 h-3" /> {contract.date}
                                            </span>
                                            <span className="flex items-center gap-1 text-xs text-gray-500">
                                                <Tag className="w-3 h-3" /> {contract.jurisdiction}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${riskBadge(contract.risk)}`}>
                                        {contract.risk === 'Critical' || contract.risk === 'High' ? (
                                            <AlertTriangle className="w-3 h-3 inline mr-1" />
                                        ) : (
                                            <CheckCircle2 className="w-3 h-3 inline mr-1" />
                                        )}
                                        {contract.risk}
                                    </span>
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusBadge(contract.status)}`}>
                                        {contract.status}
                                    </span>
                                </div>
                            </div>
                            <p className="text-sm text-gray-500 ml-[52px]">{contract.summary}</p>
                            <div className="ml-[52px] mt-2 flex items-center gap-2">
                                <span className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600 font-medium">{contract.type}</span>
                                <span className="flex items-center gap-1 text-xs text-gray-400">
                                    <Clock className="w-3 h-3" /> Updated {contract.date}
                                </span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
