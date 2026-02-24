import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { clausesAPI } from '../services/api';
import toast from 'react-hot-toast';
import {
    Search,
    BookOpen,
    Copy,
    Check,
    ChevronDown,
    ChevronUp,
    AlertTriangle,
    Shield,
    Lightbulb,
    X,
} from 'lucide-react';

interface Clause {
    id: string;
    title: string;
    category: string;
    jurisdiction: string;
    risk_level: string;
    description: string;
    text: string;
    usage_count: number;
}

export default function ClauseLibrary() {
    const [search, setSearch] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [expandedClause, setExpandedClause] = useState<string | null>(null);
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const [explainClause, setExplainClause] = useState<string | null>(null);
    const [explanation, setExplanation] = useState<{ explanation: string; key_points: string[] } | null>(null);

    const { data: categoriesData } = useQuery({
        queryKey: ['clause-categories'],
        queryFn: () => clausesAPI.getCategories(),
    });

    const { data: clausesData, isLoading } = useQuery({
        queryKey: ['clauses', selectedCategory, search],
        queryFn: () =>
            clausesAPI.list({
                category: selectedCategory || undefined,
                search: search || undefined,
                page_size: 50,
            }),
    });

    const { data: fullClauseData } = useQuery({
        queryKey: ['clause-detail', expandedClause],
        queryFn: () => clausesAPI.get(expandedClause!),
        enabled: !!expandedClause,
    });

    const explainMutation = useMutation({
        mutationFn: (clauseText: string) => clausesAPI.explain({ clause_text: clauseText, audience: 'non-lawyer' }),
        onSuccess: (res) => {
            setExplanation(res.data);
        },
        onError: () => {
            toast.error('Failed to generate explanation');
        },
    });

    const categories: string[] = categoriesData?.data?.categories || [];
    const clauses: Clause[] = clausesData?.data?.clauses || [];
    const fullClause: Clause | null = fullClauseData?.data || null;

    const riskColor = (level: string) => {
        switch (level) {
            case 'low': return 'bg-green-100 text-green-700';
            case 'medium': return 'bg-yellow-100 text-yellow-700';
            case 'high': return 'bg-red-100 text-red-700';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    const riskIcon = (level: string) => {
        switch (level) {
            case 'high': return <AlertTriangle className="w-3 h-3" />;
            default: return <Shield className="w-3 h-3" />;
        }
    };

    const handleCopy = (clause: Clause) => {
        const textToCopy = fullClause && fullClause.id === clause.id ? fullClause.text : clause.text;
        navigator.clipboard.writeText(textToCopy);
        setCopiedId(clause.id);
        toast.success('Clause copied to clipboard');
        setTimeout(() => setCopiedId(null), 2000);
    };

    const handleExplain = (clause: Clause) => {
        const text = fullClause && fullClause.id === clause.id ? fullClause.text : clause.text;
        setExplainClause(clause.id);
        setExplanation(null);
        explainMutation.mutate(text);
    };

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <BookOpen className="w-8 h-8 text-primary-600" />
                    Clause Library
                </h1>
                <p className="text-gray-500 mt-1">
                    Browse {clauses.length}+ reusable legal clauses — click to expand, copy, or get AI explanations
                </p>
            </div>

            {/* Search */}
            <div className="mb-6">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search clauses by title, description, or legal text..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                </div>
            </div>

            {/* Category Pills */}
            <div className="flex flex-wrap gap-2 mb-8">
                <button
                    onClick={() => setSelectedCategory('')}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${!selectedCategory ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                >
                    All Categories
                </button>
                {categories.map((cat) => (
                    <button
                        key={cat}
                        onClick={() => setSelectedCategory(cat === selectedCategory ? '' : cat)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${selectedCategory === cat ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                    >
                        {cat}
                    </button>
                ))}
            </div>

            {/* Clauses List */}
            {isLoading ? (
                <div className="space-y-4">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="bg-white rounded-xl border border-gray-100 p-6 animate-pulse">
                            <div className="h-5 bg-gray-200 rounded w-1/3 mb-3" />
                            <div className="h-3 bg-gray-100 rounded w-2/3" />
                        </div>
                    ))}
                </div>
            ) : clauses.length === 0 ? (
                <div className="text-center py-16">
                    <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-1">No clauses found</h3>
                    <p className="text-gray-500">Try adjusting your search or category filter</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {clauses.map((clause) => {
                        const isExpanded = expandedClause === clause.id;
                        const displayText = isExpanded && fullClause ? fullClause.text : clause.text;
                        const isExplaining = explainClause === clause.id;

                        return (
                            <div
                                key={clause.id}
                                className={`bg-white rounded-xl border transition-all ${isExpanded ? 'border-primary-200 shadow-md' : 'border-gray-100 shadow-sm hover:border-gray-200'
                                    }`}
                            >
                                {/* Clause Header */}
                                <div
                                    className="p-6 cursor-pointer"
                                    onClick={() => setExpandedClause(isExpanded ? null : clause.id)}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-2">
                                                <h3 className="text-lg font-semibold text-gray-900">{clause.title}</h3>
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 ${riskColor(clause.risk_level)}`}>
                                                    {riskIcon(clause.risk_level)}
                                                    {clause.risk_level}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-500 mb-2">{clause.description}</p>
                                            <div className="flex items-center gap-4 text-xs text-gray-400">
                                                <span className="px-2 py-1 bg-gray-50 rounded">{clause.category}</span>
                                                <span>{clause.jurisdiction}</span>
                                                <span>{clause.usage_count.toLocaleString()} uses</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 ml-4">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleCopy(clause); }}
                                                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                                                title="Copy to clipboard"
                                            >
                                                {copiedId === clause.id ? (
                                                    <Check className="w-4 h-4 text-green-600" />
                                                ) : (
                                                    <Copy className="w-4 h-4 text-gray-400" />
                                                )}
                                            </button>
                                            {isExpanded ? (
                                                <ChevronUp className="w-5 h-5 text-gray-400" />
                                            ) : (
                                                <ChevronDown className="w-5 h-5 text-gray-400" />
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Expanded Content */}
                                {isExpanded && (
                                    <div className="px-6 pb-6 border-t border-gray-100 pt-4">
                                        {/* Full clause text */}
                                        <div className="bg-gray-50 rounded-xl p-5 mb-4">
                                            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                                                {displayText}
                                            </p>
                                        </div>

                                        {/* Action buttons */}
                                        <div className="flex gap-3">
                                            <button
                                                onClick={() => handleCopy(clause)}
                                                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm"
                                            >
                                                {copiedId === clause.id ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                                {copiedId === clause.id ? 'Copied!' : 'Copy Clause'}
                                            </button>
                                            <button
                                                onClick={() => handleExplain(clause)}
                                                disabled={explainMutation.isPending}
                                                className="flex items-center gap-2 px-4 py-2 border border-primary-200 text-primary-700 rounded-lg hover:bg-primary-50 transition-colors text-sm disabled:opacity-50"
                                            >
                                                <Lightbulb className="w-4 h-4" />
                                                {explainMutation.isPending && isExplaining ? 'Explaining...' : 'Explain in Plain English'}
                                            </button>
                                        </div>

                                        {/* AI Explanation */}
                                        {isExplaining && explanation && (
                                            <div className="mt-4 p-5 bg-blue-50 rounded-xl border border-blue-100">
                                                <div className="flex items-center justify-between mb-3">
                                                    <h4 className="text-sm font-semibold text-blue-800 flex items-center gap-2">
                                                        <Lightbulb className="w-4 h-4" />
                                                        AI Explanation
                                                    </h4>
                                                    <button
                                                        onClick={() => { setExplainClause(null); setExplanation(null); }}
                                                        className="text-blue-400 hover:text-blue-600"
                                                    >
                                                        <X className="w-4 h-4" />
                                                    </button>
                                                </div>
                                                <p className="text-sm text-blue-700 mb-3 leading-relaxed">{explanation.explanation}</p>
                                                {explanation.key_points.length > 0 && (
                                                    <div>
                                                        <p className="text-xs font-semibold text-blue-800 mb-1">Key Points:</p>
                                                        <ul className="space-y-1">
                                                            {explanation.key_points.map((point, i) => (
                                                                <li key={i} className="text-xs text-blue-600 flex items-center gap-2">
                                                                    <span className="w-1.5 h-1.5 bg-blue-400 rounded-full" />
                                                                    {point}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
