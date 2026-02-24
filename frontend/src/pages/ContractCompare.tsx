import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { compareAPI } from '../services/api';
import toast from 'react-hot-toast';
import {
    GitCompare,
    AlertTriangle,
    FileText,
    Activity,
} from 'lucide-react';

interface DiffLine {
    line_number: number;
    type: 'added' | 'removed' | 'modified' | 'unchanged';
    content_a: string | null;
    content_b: string | null;
}

interface ComparisonResult {
    comparison_id: string;
    summary: {
        total_lines: number;
        added: number;
        removed: number;
        modified: number;
        unchanged: number;
        similarity_percent: number;
    };
    diff_lines: DiffLine[];
    risk_impact: {
        overall_risk: 'low' | 'medium' | 'high';
        flagged_changes: Array<{
            line: number;
            risk_level: string;
            keyword: string;
            change_type: string;
        }>;
    };
}

export default function ContractCompare() {
    const [textA, setTextA] = useState('');
    const [textB, setTextB] = useState('');
    const [result, setResult] = useState<ComparisonResult | null>(null);

    const compareMutation = useMutation({
        mutationFn: (data: { text_a: string; text_b: string }) => compareAPI.compare(data),
        onSuccess: (res) => {
            setResult(res.data);
            toast.success('Comparison complete');
        },
        onError: () => {
            toast.error('Failed to compare documents');
        },
    });


    const handleCompare = () => {
        if (!textA.trim() || !textB.trim()) {
            toast.error('Please enter text for both documents');
            return;
        }
        compareMutation.mutate({ text_a: textA, text_b: textB });
    };

    const getLineColor = (type: string) => {
        switch (type) {
            case 'added': return 'bg-green-50';
            case 'removed': return 'bg-red-50';
            case 'modified': return 'bg-yellow-50';
            default: return '';
        }
    };


    return (
        <div className="p-8 max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <GitCompare className="w-8 h-8 text-primary-600" />
                    Contract Comparison
                </h1>
                <p className="text-gray-500 mt-1">
                    Compare two contract versions side-by-side to identify changes and risks
                </p>
            </div>

            {/* Input Section */}
            {!result && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                        <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                            <FileText className="w-4 h-4 text-gray-400" />
                            Original Document (Version A)
                        </h3>
                        <textarea
                            value={textA}
                            onChange={(e) => setTextA(e.target.value)}
                            className="w-full h-96 p-4 border border-gray-100 rounded-lg bg-gray-50 focus:bg-white focus:ring-2 focus:ring-primary-500 transition-all font-mono text-sm resize-none"
                            placeholder="Paste original contract text here..."
                        />
                    </div>
                    <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                        <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                            <FileText className="w-4 h-4 text-gray-400" />
                            New Document (Version B)
                        </h3>
                        <textarea
                            value={textB}
                            onChange={(e) => setTextB(e.target.value)}
                            className="w-full h-96 p-4 border border-gray-100 rounded-lg bg-gray-50 focus:bg-white focus:ring-2 focus:ring-primary-500 transition-all font-mono text-sm resize-none"
                            placeholder="Paste new contract text here..."
                        />
                    </div>
                </div>
            )}

            {/* Action Bar */}
            {!result && (
                <div className="flex justify-center mb-12">
                    <button
                        onClick={handleCompare}
                        disabled={compareMutation.isPending}
                        className="flex items-center gap-2 px-8 py-3 bg-primary-600 text-white rounded-full hover:bg-primary-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 font-medium"
                    >
                        {compareMutation.isPending ? (
                            <Activity className="w-5 h-5 animate-spin" />
                        ) : (
                            <GitCompare className="w-5 h-5" />
                        )}
                        {compareMutation.isPending ? 'Analyzing Differences...' : 'Compare Documents'}
                    </button>
                </div>
            )}

            {/* Results View */}
            {result && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
                            <p className="text-sm text-gray-500">Similarity</p>
                            <p className="text-2xl font-bold text-gray-900">{result.summary.similarity_percent}%</p>
                            <div className="w-full bg-gray-100 h-1.5 rounded-full mt-2">
                                <div style={{ width: `${result.summary.similarity_percent}%` }} className="h-full bg-primary-500 rounded-full" />
                            </div>
                        </div>
                        <div className="bg-green-50 p-5 rounded-xl border border-green-100">
                            <p className="text-sm text-green-700">Additions</p>
                            <p className="text-2xl font-bold text-green-800">+{result.summary.added} lines</p>
                        </div>
                        <div className="bg-red-50 p-5 rounded-xl border border-red-100">
                            <p className="text-sm text-red-700">Deletions</p>
                            <p className="text-2xl font-bold text-red-800">-{result.summary.removed} lines</p>
                        </div>
                        <div className={`p-5 rounded-xl border ${result.risk_impact.overall_risk === 'high' ? 'bg-red-50 border-red-100' :
                            result.risk_impact.overall_risk === 'medium' ? 'bg-yellow-50 border-yellow-100' :
                                'bg-green-50 border-green-100'
                            }`}>
                            <div className="flex items-center gap-2 mb-1">
                                <AlertTriangle className={`w-4 h-4 ${result.risk_impact.overall_risk === 'high' ? 'text-red-600' :
                                    result.risk_impact.overall_risk === 'medium' ? 'text-yellow-600' :
                                        'text-green-600'
                                    }`} />
                                <p className={`text-sm font-medium ${result.risk_impact.overall_risk === 'high' ? 'text-red-700' :
                                    result.risk_impact.overall_risk === 'medium' ? 'text-yellow-700' :
                                        'text-green-700'
                                    }`}>Risk Impact</p>
                            </div>
                            <p className={`text-xl font-bold capitalize ${result.risk_impact.overall_risk === 'high' ? 'text-red-900' :
                                result.risk_impact.overall_risk === 'medium' ? 'text-yellow-900' :
                                    'text-green-900'
                                }`}>{result.risk_impact.overall_risk} Risk</p>
                        </div>
                    </div>

                    {/* Diff Viewer */}
                    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
                            <h3 className="font-semibold text-gray-900">Difference Viewer</h3>
                            <button
                                onClick={() => { setResult(null); setTextA(''); setTextB(''); }}
                                className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
                            >
                                Start New Comparison
                            </button>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full border-collapse">
                                <thead>
                                    <tr className="bg-gray-100 text-left text-xs text-gray-500 uppercase font-semibold">
                                        <th className="p-3 w-12 text-center">#</th>
                                        <th className="p-3 w-[45%] border-r border-gray-200">Version A (Original)</th>
                                        <th className="p-3 w-[45%]">Version B (New)</th>
                                    </tr>
                                </thead>
                                <tbody className="font-mono text-sm">
                                    {result.diff_lines.map((line, idx) => (
                                        <tr key={idx} className={`border-b border-gray-50 ${getLineColor(line.type)}`}>
                                            <td className="p-3 text-center text-gray-400 select-none text-xs">{line.line_number}</td>
                                            <td className={`p-3 border-r border-gray-100 whitespace-pre-wrap ${line.type === 'removed' || line.type === 'modified' ? 'bg-red-50/50' : ''}`}>
                                                <span className={line.type === 'removed' ? 'text-red-700' : line.type === 'modified' ? 'text-yellow-700' : 'text-gray-600'}>
                                                    {line.content_a || ''}
                                                </span>
                                            </td>
                                            <td className={`p-3 whitespace-pre-wrap ${line.type === 'added' || line.type === 'modified' ? 'bg-green-50/50' : ''}`}>
                                                <span className={line.type === 'added' ? 'text-green-700' : line.type === 'modified' ? 'text-yellow-700' : 'text-gray-600'}>
                                                    {line.content_b || ''}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
