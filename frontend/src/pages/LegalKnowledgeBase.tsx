import { useState } from 'react';
import {
    BookOpen,
    Search,
    ChevronRight,
    Globe,
    Shield,
    FileText,
    Scale,
    AlertTriangle,
    CheckCircle2,
    ExternalLink,
    Star,
    Clock,
    Tag,
} from 'lucide-react';

interface Article {
    id: string;
    title: string;
    category: string;
    jurisdiction: string;
    summary: string;
    readTime: string;
    tags: string[];
    featured?: boolean;
    lastUpdated: string;
}

const CATEGORIES = [
    { name: 'All', icon: BookOpen, color: 'text-gray-600' },
    { name: 'Contract Basics', icon: FileText, color: 'text-blue-600' },
    { name: 'Compliance', icon: Shield, color: 'text-green-600' },
    { name: 'Risk Management', icon: AlertTriangle, color: 'text-orange-600' },
    { name: 'Jurisdictions', icon: Globe, color: 'text-teal-600' },
    { name: 'Best Practices', icon: CheckCircle2, color: 'text-violet-600' },
    { name: 'Legal Framework', icon: Scale, color: 'text-indigo-600' },
];

const ARTICLES: Article[] = [
    {
        id: '1', title: 'Essential Clauses Every NDA Must Include', category: 'Contract Basics',
        jurisdiction: 'Universal', summary: 'A comprehensive guide to the must-have clauses in non-disclosure agreements, including definition of confidential information, exclusions, term, and remedies for breach.',
        readTime: '8 min', tags: ['NDA', 'Clauses', 'Drafting'], featured: true, lastUpdated: '2026-02-20',
    },
    {
        id: '2', title: 'GDPR Compliance in International Contracts', category: 'Compliance',
        jurisdiction: 'EU', summary: 'How to ensure your contracts comply with the General Data Protection Regulation when processing personal data across EU member states. Includes DPA template guidance.',
        readTime: '12 min', tags: ['GDPR', 'Data Privacy', 'EU'], featured: true, lastUpdated: '2026-02-18',
    },
    {
        id: '3', title: 'Indian Contract Act — Key Provisions for Tech Companies', category: 'Legal Framework',
        jurisdiction: 'India', summary: 'Overview of the Indian Contract Act 1872 and the Information Technology Act 2000 as they apply to SaaS agreements, service contracts, and employment agreements in India.',
        readTime: '15 min', tags: ['India', 'IT Act', 'Contract Law'], featured: true, lastUpdated: '2026-02-15',
    },
    {
        id: '4', title: 'Risk Assessment Framework for M&A Due Diligence', category: 'Risk Management',
        jurisdiction: 'Universal', summary: 'A step-by-step framework for evaluating contractual risks during mergers and acquisitions, including red flags, scoring methodology, and prioritization matrix.',
        readTime: '20 min', tags: ['M&A', 'Due Diligence', 'Risk'], lastUpdated: '2026-02-12',
    },
    {
        id: '5', title: 'Cross-Border Contract Enforcement: US vs India vs EU', category: 'Jurisdictions',
        jurisdiction: 'Multi-Jurisdictional', summary: 'Comparing contract enforcement mechanisms across major jurisdictions, choice of law provisions, arbitration clauses, and sovereign immunity considerations.',
        readTime: '18 min', tags: ['Cross-Border', 'Enforcement', 'Arbitration'], lastUpdated: '2026-02-10',
    },
    {
        id: '6', title: 'Building a Scalable Contract Management Process', category: 'Best Practices',
        jurisdiction: 'Universal', summary: 'Best practices for implementing an enterprise-grade contract lifecycle management process. Covers intake, drafting, review, approval workflows, and renewal tracking.',
        readTime: '10 min', tags: ['CLM', 'Process', 'Enterprise'], lastUpdated: '2026-02-08',
    },
    {
        id: '7', title: 'Force Majeure Clauses Post-COVID: What Changed', category: 'Contract Basics',
        jurisdiction: 'Universal', summary: 'How force majeure clauses evolved after the pandemic. New best practices for drafting robust force majeure provisions that protect against future disruptions.',
        readTime: '7 min', tags: ['Force Majeure', 'COVID', 'Drafting'], lastUpdated: '2026-02-05',
    },
    {
        id: '8', title: 'HIPAA Business Associate Agreements (BAA) Guide', category: 'Compliance',
        jurisdiction: 'US', summary: 'Complete guide to HIPAA BAAs for healthcare SaaS providers. Includes mandatory provisions, typical negotiation points, and compliance checklist.',
        readTime: '14 min', tags: ['HIPAA', 'Healthcare', 'BAA'], lastUpdated: '2026-02-01',
    },
    {
        id: '9', title: 'Limitation of Liability: Cap Structures & Negotiation', category: 'Risk Management',
        jurisdiction: 'Universal', summary: 'Deep dive into limitation of liability clauses, including cap methodologies (fixed, percentage, tiered), carve-outs, and negotiation strategies for both vendors and customers.',
        readTime: '11 min', tags: ['Liability', 'Negotiation', 'Caps'], lastUpdated: '2026-01-28',
    },
    {
        id: '10', title: 'Singapore Arbitration: SIAC vs ICC Rules', category: 'Jurisdictions',
        jurisdiction: 'Singapore', summary: 'Comparative analysis of SIAC and ICC arbitration for contracts involving APAC parties. Covers costs, timelines, enforcement under the New York Convention, and when to choose which.',
        readTime: '13 min', tags: ['Arbitration', 'Singapore', 'SIAC'], lastUpdated: '2026-01-25',
    },
    {
        id: '11', title: 'AI in Legal Contracts: Ethical and Regulatory Considerations', category: 'Legal Framework',
        jurisdiction: 'Universal', summary: 'Legal and ethical implications of using AI for contract drafting and review. Covers bias, accountability, EU AI Act, and best practices for responsible AI deployment.',
        readTime: '16 min', tags: ['AI Ethics', 'EU AI Act', 'RegTech'], lastUpdated: '2026-01-20',
    },
    {
        id: '12', title: 'SLA Drafting Checklist for Cloud Service Providers', category: 'Best Practices',
        jurisdiction: 'Universal', summary: 'Comprehensive checklist for drafting cloud SLAs including uptime guarantees, response times, credits, escalation procedures, and data residency requirements.',
        readTime: '9 min', tags: ['SLA', 'Cloud', 'Checklist'], lastUpdated: '2026-01-15',
    },
];

export default function LegalKnowledgeBase() {
    const [search, setSearch] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All');
    const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

    const filtered = ARTICLES.filter((a) => {
        const q = search.toLowerCase();
        const matchesSearch = !search ||
            a.title.toLowerCase().includes(q) ||
            a.summary.toLowerCase().includes(q) ||
            a.tags.some(t => t.toLowerCase().includes(q));
        const matchesCategory = selectedCategory === 'All' || a.category === selectedCategory;
        return matchesSearch && matchesCategory;
    });

    const featured = ARTICLES.filter(a => a.featured);

    const categoryColor = (cat: string) => {
        const colors: Record<string, string> = {
            'Contract Basics': 'bg-blue-100 text-blue-700',
            'Compliance': 'bg-green-100 text-green-700',
            'Risk Management': 'bg-orange-100 text-orange-700',
            'Jurisdictions': 'bg-teal-100 text-teal-700',
            'Best Practices': 'bg-violet-100 text-violet-700',
            'Legal Framework': 'bg-indigo-100 text-indigo-700',
        };
        return colors[cat] || 'bg-gray-100 text-gray-600';
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <BookOpen className="w-8 h-8 text-amber-500" />
                    Legal Knowledge Base
                </h1>
                <p className="text-gray-500 mt-1">Guides, best practices, and legal references for contract professionals.</p>
            </div>

            {/* Search */}
            <div className="relative mb-6">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search articles, topics, tags..."
                    className="w-full pl-12 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 shadow-sm"
                />
            </div>

            {/* Categories */}
            <div className="flex flex-wrap gap-2 mb-6">
                {CATEGORIES.map(({ name, icon: Icon, color }) => (
                    <button
                        key={name}
                        onClick={() => setSelectedCategory(name)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${selectedCategory === name
                                ? 'bg-amber-600 text-white shadow-sm'
                                : 'bg-white border border-gray-200 text-gray-600 hover:border-amber-300 hover:bg-amber-50'
                            }`}
                    >
                        <Icon className={`w-3.5 h-3.5 ${selectedCategory === name ? 'text-white' : color}`} />
                        {name}
                    </button>
                ))}
            </div>

            {/* Featured Articles (only shown when on 'All' category and no search) */}
            {selectedCategory === 'All' && !search && (
                <div className="mb-8">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <Star className="w-5 h-5 text-amber-500" /> Featured
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {featured.map((article) => (
                            <div
                                key={article.id}
                                onClick={() => setSelectedArticle(article)}
                                className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-200 p-5 cursor-pointer hover:shadow-md hover:border-amber-300 transition-all group"
                            >
                                <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium mb-2 ${categoryColor(article.category)}`}>
                                    {article.category}
                                </span>
                                <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-amber-700 transition-colors">{article.title}</h3>
                                <p className="text-xs text-gray-500 line-clamp-2">{article.summary}</p>
                                <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
                                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {article.readTime}</span>
                                    <span className="flex items-center gap-1"><Globe className="w-3 h-3" /> {article.jurisdiction}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="flex gap-6">
                {/* Articles List */}
                <div className="flex-1 space-y-3">
                    <h2 className="text-lg font-semibold text-gray-900 mb-3">
                        {search ? `Results for "${search}"` : selectedCategory === 'All' ? 'All Articles' : selectedCategory}
                        <span className="text-sm font-normal text-gray-400 ml-2">({filtered.length})</span>
                    </h2>

                    {filtered.length === 0 ? (
                        <div className="bg-white rounded-xl border border-gray-100 p-12 text-center">
                            <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                            <p className="text-gray-500">No articles match your search.</p>
                        </div>
                    ) : (
                        filtered.map((article) => (
                            <div
                                key={article.id}
                                onClick={() => setSelectedArticle(article)}
                                className={`bg-white rounded-xl border p-5 cursor-pointer transition-all group ${selectedArticle?.id === article.id
                                        ? 'border-amber-300 shadow-md bg-amber-50/30'
                                        : 'border-gray-100 hover:shadow-sm hover:border-amber-200'
                                    }`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${categoryColor(article.category)}`}>
                                                {article.category}
                                            </span>
                                            <span className="text-xs text-gray-400 flex items-center gap-1">
                                                <Globe className="w-3 h-3" />{article.jurisdiction}
                                            </span>
                                        </div>
                                        <h3 className="font-semibold text-gray-900 group-hover:text-amber-700 transition-colors">{article.title}</h3>
                                        <p className="text-sm text-gray-500 mt-1 line-clamp-2">{article.summary}</p>
                                        <div className="mt-2 flex items-center gap-3">
                                            <span className="text-xs text-gray-400 flex items-center gap-1"><Clock className="w-3 h-3" /> {article.readTime}</span>
                                            <span className="text-xs text-gray-400">Updated {article.lastUpdated}</span>
                                        </div>
                                    </div>
                                    <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-amber-500 transition-colors shrink-0 mt-1" />
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Article Detail Panel */}
                {selectedArticle && (
                    <div className="w-96 shrink-0">
                        <div className="bg-white rounded-xl border border-gray-200 shadow-sm sticky top-8 overflow-hidden">
                            <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-5 text-white">
                                <span className="text-xs bg-white/20 px-2 py-0.5 rounded backdrop-blur-sm">{selectedArticle.category}</span>
                                <h3 className="text-lg font-bold mt-2">{selectedArticle.title}</h3>
                                <div className="flex items-center gap-3 mt-2 text-amber-100 text-xs">
                                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {selectedArticle.readTime} read</span>
                                    <span className="flex items-center gap-1"><Globe className="w-3 h-3" /> {selectedArticle.jurisdiction}</span>
                                </div>
                            </div>

                            <div className="p-5">
                                <h4 className="text-sm font-semibold text-gray-900 mb-2">Summary</h4>
                                <p className="text-sm text-gray-600 leading-relaxed">{selectedArticle.summary}</p>

                                <div className="mt-4">
                                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Tags</h4>
                                    <div className="flex flex-wrap gap-1">
                                        {selectedArticle.tags.map((tag) => (
                                            <span key={tag} className="flex items-center gap-1 px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                                                <Tag className="w-3 h-3" /> {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-400">
                                    Last updated: {selectedArticle.lastUpdated}
                                </div>

                                <button className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-600 text-white rounded-lg font-medium hover:bg-amber-700 transition-colors text-sm">
                                    <ExternalLink className="w-4 h-4" />
                                    Read Full Article
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
