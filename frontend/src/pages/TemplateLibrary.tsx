import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { templatesAPI } from '../services/api';
import {
    Search,
    Filter,
    FileText,
    ArrowRight,
    Star,
    Shield,
    ChevronDown,
} from 'lucide-react';

interface Template {
    id: string;
    name: string;
    category: string;
    description: string;
    jurisdiction: string;
    risk_level: string;
    estimated_pages: number;
    popularity: number;
    tags: string[];
}

interface Category {
    id: string;
    name: string;
    icon: string;
    count: number;
}

export default function TemplateLibrary() {
    const navigate = useNavigate();
    const [search, setSearch] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [selectedRisk, setSelectedRisk] = useState('');
    const [showFilters, setShowFilters] = useState(false);

    const { data: categoriesData } = useQuery({
        queryKey: ['template-categories'],
        queryFn: () => templatesAPI.getCategories(),
    });

    const { data: templatesData, isLoading } = useQuery({
        queryKey: ['templates', selectedCategory, selectedRisk, search],
        queryFn: () =>
            templatesAPI.list({
                category: selectedCategory || undefined,
                risk_level: selectedRisk || undefined,
                search: search || undefined,
                page_size: 50,
            }),
    });

    const categories: Category[] = categoriesData?.data?.categories || [];
    const templates: Template[] = templatesData?.data?.templates || [];

    const riskColor = (level: string) => {
        switch (level) {
            case 'low': return 'bg-green-100 text-green-700';
            case 'medium': return 'bg-yellow-100 text-yellow-700';
            case 'high': return 'bg-red-100 text-red-700';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Template Library</h1>
                <p className="text-gray-500 mt-1">
                    Browse {templates.length}+ contract templates across {categories.length} categories
                </p>
            </div>

            {/* Search & Filters */}
            <div className="mb-6 space-y-4">
                <div className="flex gap-4">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search templates by name or description..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        />
                    </div>
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={`flex items-center gap-2 px-4 py-3 border rounded-xl transition-colors ${showFilters ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                            }`}
                    >
                        <Filter className="w-5 h-5" />
                        Filters
                        <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
                    </button>
                </div>

                {showFilters && (
                    <div className="flex gap-4 p-4 bg-gray-50 rounded-xl">
                        <div>
                            <label className="text-xs font-medium text-gray-500 mb-1 block">Risk Level</label>
                            <select
                                value={selectedRisk}
                                onChange={(e) => setSelectedRisk(e.target.value)}
                                className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
                            >
                                <option value="">All Risks</option>
                                <option value="low">Low Risk</option>
                                <option value="medium">Medium Risk</option>
                                <option value="high">High Risk</option>
                            </select>
                        </div>
                        <button
                            onClick={() => { setSelectedCategory(''); setSelectedRisk(''); setSearch(''); }}
                            className="self-end px-3 py-2 text-sm text-primary-600 hover:bg-primary-50 rounded-lg"
                        >
                            Clear All
                        </button>
                    </div>
                )}
            </div>

            {/* Category Pills */}
            <div className="flex flex-wrap gap-2 mb-8">
                <button
                    onClick={() => setSelectedCategory('')}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${!selectedCategory ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                >
                    All ({categories.reduce((s, c) => s + c.count, 0)})
                </button>
                {categories.map((cat) => (
                    <button
                        key={cat.id}
                        onClick={() => setSelectedCategory(cat.id === selectedCategory ? '' : cat.id)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${selectedCategory === cat.id ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                    >
                        {cat.icon} {cat.name} ({cat.count})
                    </button>
                ))}
            </div>

            {/* Templates Grid */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                        <div key={i} className="bg-white rounded-xl border border-gray-100 p-6 animate-pulse">
                            <div className="h-4 bg-gray-200 rounded w-3/4 mb-3" />
                            <div className="h-3 bg-gray-100 rounded w-full mb-2" />
                            <div className="h-3 bg-gray-100 rounded w-2/3" />
                        </div>
                    ))}
                </div>
            ) : templates.length === 0 ? (
                <div className="text-center py-16">
                    <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-1">No templates found</h3>
                    <p className="text-gray-500">Try adjusting your search or filters</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {templates.map((template) => (
                        <div
                            key={template.id}
                            className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:border-primary-200 transition-all group"
                        >
                            <div className="p-6">
                                <div className="flex items-start justify-between mb-3">
                                    <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                                        <FileText className="w-5 h-5 text-primary-600" />
                                    </div>
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${riskColor(template.risk_level)}`}>
                                        {template.risk_level} risk
                                    </span>
                                </div>

                                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
                                    {template.name}
                                </h3>
                                <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                                    {template.description}
                                </p>

                                <div className="flex items-center gap-3 text-xs text-gray-400 mb-4">
                                    <span className="flex items-center gap-1">
                                        <Shield className="w-3 h-3" />
                                        {template.jurisdiction}
                                    </span>
                                    <span>•</span>
                                    <span>~{template.estimated_pages} pages</span>
                                    <span>•</span>
                                    <span className="flex items-center gap-1">
                                        <Star className="w-3 h-3" />
                                        {template.popularity}%
                                    </span>
                                </div>

                                <button
                                    onClick={() => navigate('/generate', { state: { contractType: template.category, templateId: template.id } })}
                                    className="flex items-center gap-2 w-full justify-center px-4 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
                                >
                                    Use Template
                                    <ArrowRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
