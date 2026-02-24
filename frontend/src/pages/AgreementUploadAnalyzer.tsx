import { useState, useRef, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { reviewAPI } from '../services/api';
import {
    Upload,
    FileUp,
    AlertTriangle,
    CheckCircle2,
    XCircle,
    Search,
    BarChart3,
    FileText,
    Shield,
    Info,
} from 'lucide-react';
import toast from 'react-hot-toast';

interface RiskFactor {
    category: string;
    name: string;
    severity: string;
    description: string;
    recommendation: string;
    confidence: number;
}

interface FileInfo {
    filename: string;
    detected_contract_type: string;
    effective_contract_type: string;
    jurisdiction: string;
    clauses_found: number;
    metadata: Record<string, unknown>;
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
    file_info: FileInfo;
}

export default function AgreementUploadAnalyzer() {
    const [file, setFile] = useState<File | null>(null);
    const [contractType, setContractType] = useState('');
    const [jurisdiction, setJurisdiction] = useState('US-Federal');
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const allowedExtensions = ['pdf', 'docx', 'txt'];

    const analyzeMutation = useMutation({
        mutationFn: () => {
            if (!file) throw new Error('No file selected');
            return reviewAPI.uploadAndAnalyze(
                file,
                contractType || undefined,
                jurisdiction,
            );
        },
        onSuccess: (response) => {
            setResult(response.data);
            toast.success('Risk analysis complete!');
        },
        onError: (error: any) => {
            const msg = error.response?.data?.detail || 'Analysis failed';
            toast.error(msg);
        },
    });

    const validateFile = (f: File): boolean => {
        const ext = f.name.split('.').pop()?.toLowerCase() || '';
        if (!allowedExtensions.includes(ext)) {
            toast.error('Unsupported file type. Please upload PDF, DOCX, or TXT files.');
            return false;
        }
        if (f.size > 10 * 1024 * 1024) {
            toast.error('File too large. Maximum size is 10 MB.');
            return false;
        }
        return true;
    };

    const handleFileSelect = (f: File) => {
        if (validateFile(f)) {
            setFile(f);
            setResult(null);
        }
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) handleFileSelect(droppedFile);
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const severityColor: Record<string, string> = {
        critical: 'bg-red-100 text-red-800 border-red-200',
        high: 'bg-orange-100 text-orange-800 border-orange-200',
        medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        low: 'bg-green-100 text-green-800 border-green-200',
    };

    const riskScoreColor = (score: number) =>
        score >= 0.7 ? 'text-red-600' : score >= 0.4 ? 'text-yellow-600' : 'text-green-600';

    const riskScoreBg = (score: number) =>
        score >= 0.7 ? 'bg-red-50 border-red-200' : score >= 0.4 ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200';

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <FileUp className="w-8 h-8 text-indigo-500" />
                    Upload &amp; Analyze Agreement
                </h1>
                <p className="text-gray-500 mt-1">
                    Upload an existing agreement to instantly check for risks, compliance gaps, and get recommendations.
                </p>
            </div>

            <div className="grid grid-cols-3 gap-6">
                {/* Left: Upload & Options */}
                <div className="col-span-2 space-y-6">
                    {/* Drop Zone */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Agreement</h2>

                        <div
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onClick={() => fileInputRef.current?.click()}
                            className={`relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${isDragging
                                ? 'border-indigo-400 bg-indigo-50'
                                : file
                                    ? 'border-green-300 bg-green-50'
                                    : 'border-gray-300 hover:border-indigo-300 hover:bg-gray-50'
                                }`}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".pdf,.docx,.txt"
                                className="hidden"
                                onChange={(e) => {
                                    const f = e.target.files?.[0];
                                    if (f) handleFileSelect(f);
                                }}
                            />

                            {file ? (
                                <div className="flex flex-col items-center gap-3">
                                    <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center">
                                        <CheckCircle2 className="w-7 h-7 text-green-600" />
                                    </div>
                                    <div>
                                        <p className="font-semibold text-gray-900">{file.name}</p>
                                        <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
                                    </div>
                                    <p className="text-xs text-gray-400">Click or drag to replace</p>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center gap-3">
                                    <div className="w-14 h-14 bg-indigo-100 rounded-full flex items-center justify-center">
                                        <Upload className="w-7 h-7 text-indigo-500" />
                                    </div>
                                    <div>
                                        <p className="font-semibold text-gray-700">
                                            Drag &amp; drop your agreement here
                                        </p>
                                        <p className="text-sm text-gray-400 mt-1">
                                            or click to browse • PDF, DOCX, TXT (max 10 MB)
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Options */}
                        <div className="grid grid-cols-2 gap-4 mt-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Contract Type
                                    <span className="text-gray-400 font-normal"> (auto-detected if empty)</span>
                                </label>
                                <select
                                    value={contractType}
                                    onChange={(e) => setContractType(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                >
                                    <option value="">Auto-detect</option>
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
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
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

                        {/* Analyze Button */}
                        <div className="mt-6 flex items-center justify-between">
                            <div className="flex items-center gap-2 text-sm text-gray-400">
                                <Shield className="w-4 h-4" />
                                Your document is analyzed securely and never stored permanently.
                            </div>
                            <button
                                onClick={() => analyzeMutation.mutate()}
                                disabled={!file || analyzeMutation.isPending}
                                className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                            >
                                {analyzeMutation.isPending ? (
                                    <>
                                        <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                        Analyzing...
                                    </>
                                ) : (
                                    <>
                                        <Search className="w-5 h-5" />
                                        Analyze Risk
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Detailed Risk Factors */}
                    {result && result.risk_factors.length > 0 && (
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
                            <div className="p-6 border-b border-gray-100">
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Risk Factors ({result.total_factors})
                                </h2>
                            </div>
                            <div className="divide-y divide-gray-100">
                                {result.risk_factors.map((factor, i) => (
                                    <div key={i} className="p-4 hover:bg-gray-50 transition-colors">
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="flex items-center gap-3">
                                                <span
                                                    className={`px-2 py-0.5 rounded text-xs font-medium border ${severityColor[factor.severity]
                                                        }`}
                                                >
                                                    {factor.severity.toUpperCase()}
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
                                        <p className="text-sm text-indigo-600">
                                            <strong>Recommendation:</strong> {factor.recommendation}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Recommendations */}
                    {result && result.recommendations.length > 0 && (
                        <div className="bg-blue-50 rounded-xl border border-blue-200 p-6">
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

                {/* Right: Results Summary */}
                <div className="space-y-6">
                    {result ? (
                        <>
                            {/* Score Card */}
                            <div className={`rounded-xl shadow-sm border p-6 text-center ${riskScoreBg(result.overall_risk_score)}`}>
                                <h3 className="font-semibold text-gray-900 mb-2">Overall Risk Score</h3>
                                <div className={`text-5xl font-bold ${riskScoreColor(result.overall_risk_score)}`}>
                                    {(result.overall_risk_score * 100).toFixed(0)}%
                                </div>
                                <span
                                    className={`inline-block mt-2 px-3 py-1 rounded-full text-sm font-medium ${severityColor[result.risk_level] || 'bg-gray-100 text-gray-700'
                                        }`}
                                >
                                    {result.risk_level.toUpperCase()}
                                </span>
                            </div>

                            {/* File Info */}
                            {result.file_info && (
                                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                        <FileText className="w-4 h-4 text-gray-500" />
                                        File Details
                                    </h3>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">File</span>
                                            <span className="text-gray-900 font-medium truncate ml-2 max-w-[160px]">
                                                {result.file_info.filename}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Detected Type</span>
                                            <span className="text-gray-900 font-medium capitalize">
                                                {result.file_info.detected_contract_type}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Clauses Found</span>
                                            <span className="text-gray-900 font-medium">
                                                {result.file_info.clauses_found}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">Jurisdiction</span>
                                            <span className="text-gray-900 font-medium">
                                                {result.file_info.jurisdiction}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Breakdown */}
                            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                                <h3 className="font-semibold text-gray-900 mb-4">Risk Breakdown</h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <div className="flex items-center gap-2">
                                            <XCircle className="w-4 h-4 text-red-500" />
                                            <span className="text-sm text-red-600 font-medium">Critical</span>
                                        </div>
                                        <span className="bg-red-100 text-red-800 px-2 py-0.5 rounded text-sm font-bold">
                                            {result.critical_count}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <div className="flex items-center gap-2">
                                            <AlertTriangle className="w-4 h-4 text-orange-500" />
                                            <span className="text-sm text-orange-600 font-medium">High</span>
                                        </div>
                                        <span className="bg-orange-100 text-orange-800 px-2 py-0.5 rounded text-sm font-bold">
                                            {result.high_count}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <div className="flex items-center gap-2">
                                            <Info className="w-4 h-4 text-yellow-500" />
                                            <span className="text-sm text-yellow-600 font-medium">Medium</span>
                                        </div>
                                        <span className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded text-sm font-bold">
                                            {result.medium_count}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <div className="flex items-center gap-2">
                                            <CheckCircle2 className="w-4 h-4 text-green-500" />
                                            <span className="text-sm text-green-600 font-medium">Low</span>
                                        </div>
                                        <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded text-sm font-bold">
                                            {result.low_count}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Executive Summary */}
                            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                                <h3 className="font-semibold text-gray-900 mb-2">Executive Summary</h3>
                                <p className="text-sm text-gray-600 leading-relaxed">{result.executive_summary}</p>
                            </div>
                        </>
                    ) : (
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
                            <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                            <p className="text-sm text-gray-500">
                                Upload an agreement and click &quot;Analyze Risk&quot; to see detailed results.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
