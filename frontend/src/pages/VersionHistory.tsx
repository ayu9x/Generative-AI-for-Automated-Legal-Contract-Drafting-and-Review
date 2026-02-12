import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { versionsAPI } from '../services/api';
import { GitBranch, GitCommit, Clock, User, Check, Plus } from 'lucide-react';
import { useState } from 'react';
import toast from 'react-hot-toast';

export default function VersionHistory() {
  const { contractId } = useParams<{ contractId: string }>();
  const queryClient = useQueryClient();
  const [showBranchModal, setShowBranchModal] = useState(false);
  const [branchName, setBranchName] = useState('');
  const [selectedBranch, setSelectedBranch] = useState<string | undefined>(undefined);

  const { data: historyData, isLoading } = useQuery({
    queryKey: ['versions', contractId, selectedBranch],
    queryFn: () => versionsAPI.getHistory(contractId!, selectedBranch),
    enabled: !!contractId,
  });

  const { data: branchesData } = useQuery({
    queryKey: ['branches', contractId],
    queryFn: () => versionsAPI.listBranches(contractId!),
    enabled: !!contractId,
  });

  const createBranchMutation = useMutation({
    mutationFn: () =>
      versionsAPI.createBranch({ contract_id: contractId!, branch_name: branchName }),
    onSuccess: () => {
      toast.success('Branch created');
      setBranchName('');
      setShowBranchModal(false);
      queryClient.invalidateQueries({ queryKey: ['branches', contractId] });
    },
    onError: () => toast.error('Failed to create branch'),
  });

  const history = historyData?.data;
  const branches = branchesData?.data || [];

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <GitBranch className="w-8 h-8 text-primary-600" />
            Version History
          </h1>
          <p className="text-gray-500 mt-1">
            Track changes, branches, and version control for this contract.
          </p>
        </div>
        <button
          onClick={() => setShowBranchModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm"
        >
          <Plus className="w-4 h-4" />
          New Branch
        </button>
      </div>

      <div className="grid grid-cols-4 gap-6">
        {/* Branches Sidebar */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <GitBranch className="w-4 h-4" />
              Branches
            </h3>
            <div className="space-y-1">
              <button
                onClick={() => setSelectedBranch(undefined)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  !selectedBranch ? 'bg-primary-100 text-primary-800' : 'hover:bg-gray-100'
                }`}
              >
                All Branches
              </button>
              {branches.map((branch: { branch_id: string; branch_name: string; is_merged: boolean }) => (
                <button
                  key={branch.branch_id}
                  onClick={() => setSelectedBranch(branch.branch_name)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-between ${
                    selectedBranch === branch.branch_name ? 'bg-primary-100 text-primary-800' : 'hover:bg-gray-100'
                  }`}
                >
                  <span>{branch.branch_name}</span>
                  {branch.is_merged && (
                    <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">merged</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Summary</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Total Versions</dt>
                <dd className="font-medium">{history?.total_versions || 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Branches</dt>
                <dd className="font-medium">{branches.length || 1}</dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Timeline */}
        <div className="col-span-3">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">
                Version Timeline
                {selectedBranch && (
                  <span className="ml-2 text-sm text-primary-600">({selectedBranch})</span>
                )}
              </h2>
            </div>

            {(!history?.versions || history.versions.length === 0) ? (
              <div className="p-12 text-center">
                <GitCommit className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No versions found. Create the first version!</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {history.versions.map((version: {
                  version_id: string;
                  version_number: number;
                  change_description: string;
                  branch: string;
                  author_name: string;
                  created_at: string;
                  is_approved: boolean;
                  content_hash: string;
                }, index: number) => (
                  <div key={version.version_id} className="p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start gap-4">
                      {/* Timeline dot */}
                      <div className="flex flex-col items-center">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          index === 0 ? 'bg-primary-100' : 'bg-gray-100'
                        }`}>
                          <GitCommit className={`w-4 h-4 ${
                            index === 0 ? 'text-primary-600' : 'text-gray-400'
                          }`} />
                        </div>
                        {index < history.versions.length - 1 && (
                          <div className="w-0.5 h-8 bg-gray-200 mt-1" />
                        )}
                      </div>

                      {/* Content */}
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <span className="font-medium text-gray-900">v{version.version_number}</span>
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                            {version.branch}
                          </span>
                          {version.is_approved && (
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded flex items-center gap-1">
                              <Check className="w-3 h-3" /> Approved
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-700">{version.change_description}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {version.author_name}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(version.created_at).toLocaleString()}
                          </span>
                          <span className="font-mono">{version.content_hash?.slice(0, 8)}...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Branch Creation Modal */}
      {showBranchModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Branch</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Branch Name</label>
                <input
                  type="text"
                  value={branchName}
                  onChange={(e) => setBranchName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., negotiation-round-2"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowBranchModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createBranchMutation.mutate()}
                  disabled={!branchName.trim()}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm"
                >
                  Create Branch
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
