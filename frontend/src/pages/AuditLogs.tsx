import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { auditAPI } from '../services/api';
import {
    Shield,
    ChevronLeft,
    ChevronRight,
    Activity,
    Users,
    FileText,
    Clock,
} from 'lucide-react';

interface AuditEntry {
    id: string;
    timestamp: string;
    user_email: string;
    action: string;
    resource: string;
    description: string;
    ip_address: string;
    status: string;
}

export default function AuditLogs() {
    const [actionFilter, setActionFilter] = useState('');
    const [resourceFilter, setResourceFilter] = useState('');
    const [page, setPage] = useState(1);
    const pageSize = 10;

    const { data: logsData, isLoading } = useQuery({
        queryKey: ['audit-logs', actionFilter, resourceFilter, page],
        queryFn: () =>
            auditAPI.getLogs({
                action: actionFilter || undefined,
                resource: resourceFilter || undefined,
                page,
                page_size: pageSize,
            }),
    });

    const { data: statsData } = useQuery({
        queryKey: ['audit-stats'],
        queryFn: () => auditAPI.getStats(),
    });

    const { data: actionsData } = useQuery({
        queryKey: ['audit-actions'],
        queryFn: () => auditAPI.getActions(),
    });

    const logs: AuditEntry[] = logsData?.data?.logs || [];
    const total = logsData?.data?.total || 0;
    const totalPages = Math.ceil(total / pageSize);
    const stats = statsData?.data;
    const actionTypes: string[] = actionsData?.data?.actions || [];

    const actionColor = (action: string) => {
        if (action.includes('CREATE') || action.includes('LOGIN')) return 'bg-green-100 text-green-700';
        if (action.includes('DELETE')) return 'bg-red-100 text-red-700';
        if (action.includes('UPDATE') || action.includes('CHANGE')) return 'bg-yellow-100 text-yellow-700';
        if (action.includes('VIEW') || action.includes('EXPORT')) return 'bg-blue-100 text-blue-700';
        return 'bg-gray-100 text-gray-700';
    };

    const formatDate = (iso: string) => {
        const d = new Date(iso);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) +
            ' ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
                <p className="text-gray-500 mt-1">
                    Monitor all system activity and user actions
                </p>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-white rounded-xl border border-gray-100 p-5">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-100 rounded-lg">
                                <Activity className="w-5 h-5 text-blue-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-gray-900">{stats.total_entries}</p>
                                <p className="text-xs text-gray-500">Total Events</p>
                            </div>
                        </div>
                    </div>
                    <div className="bg-white rounded-xl border border-gray-100 p-5">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-green-100 rounded-lg">
                                <Users className="w-5 h-5 text-green-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-gray-900">{stats.unique_users}</p>
                                <p className="text-xs text-gray-500">Active Users</p>
                            </div>
                        </div>
                    </div>
                    <div className="bg-white rounded-xl border border-gray-100 p-5">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-purple-100 rounded-lg">
                                <FileText className="w-5 h-5 text-purple-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-gray-900">{stats.actions?.length || 0}</p>
                                <p className="text-xs text-gray-500">Action Types</p>
                            </div>
                        </div>
                    </div>
                    <div className="bg-white rounded-xl border border-gray-100 p-5">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-orange-100 rounded-lg">
                                <Clock className="w-5 h-5 text-orange-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-gray-900">{stats.resources?.length || 0}</p>
                                <p className="text-xs text-gray-500">Resources</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Filters */}
            <div className="flex gap-4 mb-6">
                <select
                    value={actionFilter}
                    onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
                    className="px-4 py-2.5 border border-gray-200 rounded-lg text-sm bg-white"
                >
                    <option value="">All Actions</option>
                    {actionTypes.map((a) => (
                        <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>
                    ))}
                </select>
                <select
                    value={resourceFilter}
                    onChange={(e) => { setResourceFilter(e.target.value); setPage(1); }}
                    className="px-4 py-2.5 border border-gray-200 rounded-lg text-sm bg-white"
                >
                    <option value="">All Resources</option>
                    <option value="auth">Authentication</option>
                    <option value="contracts">Contracts</option>
                    <option value="review">Review</option>
                    <option value="compliance">Compliance</option>
                    <option value="versions">Versions</option>
                    <option value="templates">Templates</option>
                </select>
                {(actionFilter || resourceFilter) && (
                    <button
                        onClick={() => { setActionFilter(''); setResourceFilter(''); setPage(1); }}
                        className="px-4 py-2.5 text-sm text-primary-600 hover:bg-primary-50 rounded-lg"
                    >
                        Clear Filters
                    </button>
                )}
            </div>

            {/* Logs Table */}
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-gray-50 border-b border-gray-100">
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Timestamp</th>
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">User</th>
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Action</th>
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Resource</th>
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Description</th>
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">IP</th>
                                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {isLoading ? (
                                Array.from({ length: 5 }).map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        {Array.from({ length: 7 }).map((_, j) => (
                                            <td key={j} className="px-6 py-4">
                                                <div className="h-3 bg-gray-200 rounded w-20" />
                                            </td>
                                        ))}
                                    </tr>
                                ))
                            ) : logs.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                                        <Shield className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                                        No audit entries found
                                    </td>
                                </tr>
                            ) : (
                                logs.map((entry) => (
                                    <tr key={entry.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                                            {formatDate(entry.timestamp)}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                                            {entry.user_email}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${actionColor(entry.action)}`}>
                                                {entry.action.replace(/_/g, ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-600 capitalize">
                                            {entry.resource}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                                            {entry.description}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-400 font-mono">
                                            {entry.ip_address}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                                {entry.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
                        <p className="text-sm text-gray-500">
                            Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}
                        </p>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setPage(Math.max(1, page - 1))}
                                disabled={page === 1}
                                className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
                            >
                                <ChevronLeft className="w-4 h-4" />
                            </button>
                            <span className="text-sm text-gray-600">
                                Page {page} of {totalPages}
                            </span>
                            <button
                                onClick={() => setPage(Math.min(totalPages, page + 1))}
                                disabled={page === totalPages}
                                className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
                            >
                                <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
