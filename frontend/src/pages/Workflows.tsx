
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsAPI } from '../services/api';
import {
    GitBranch,
    Plus,
    CheckCircle,
    Clock,
    Play,
    DollarSign,
    X,
    Trash2,
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function Workflows() {
    const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newName, setNewName] = useState('');
    const [newDescription, setNewDescription] = useState('');
    const [newSteps, setNewSteps] = useState<{ name: string; approver_role: string; condition?: string }[]>([
        { name: '', approver_role: '' },
    ]);
    const queryClient = useQueryClient();

    const { data: workflowsData, isLoading } = useQuery({
        queryKey: ['workflows'],
        queryFn: () => workflowsAPI.list(),
    });

    const workflows = workflowsData?.data || [];

    const createWorkflowMutation = useMutation({
        mutationFn: (data: { name: string; description: string; steps: any[] }) =>
            workflowsAPI.create(data),
        onSuccess: () => {
            toast.success('Workflow created successfully');
            queryClient.invalidateQueries({ queryKey: ['workflows'] });
            resetCreateForm();
        },
        onError: () => toast.error('Failed to create workflow'),
    });

    const approveStepMutation = useMutation({
        mutationFn: ({ wfId, stepId }: { wfId: string; stepId: string }) =>
            workflowsAPI.approveStep(wfId, stepId),
        onSuccess: (data) => {
            toast.success('Step approved');
            setSelectedWorkflow(data.data);
            queryClient.invalidateQueries({ queryKey: ['workflows'] });
        },
        onError: () => toast.error('Failed to approve step'),
    });

    const resetCreateForm = () => {
        setShowCreateModal(false);
        setNewName('');
        setNewDescription('');
        setNewSteps([{ name: '', approver_role: '' }]);
    };

    const addStep = () => {
        setNewSteps([...newSteps, { name: '', approver_role: '' }]);
    };

    const removeStep = (index: number) => {
        if (newSteps.length > 1) {
            setNewSteps(newSteps.filter((_, i) => i !== index));
        }
    };

    const updateStep = (index: number, field: string, value: string) => {
        const updated = [...newSteps];
        updated[index] = { ...updated[index], [field]: value };
        setNewSteps(updated);
    };

    const handleCreate = () => {
        if (!newName.trim()) {
            toast.error('Workflow name is required');
            return;
        }
        if (newSteps.some(s => !s.name.trim() || !s.approver_role.trim())) {
            toast.error('All steps need a name and approver role');
            return;
        }
        createWorkflowMutation.mutate({
            name: newName.trim(),
            description: newDescription.trim() || 'No description',
            steps: newSteps.map(s => ({
                name: s.name.trim(),
                approver_role: s.approver_role.trim(),
                condition: s.condition?.trim() || undefined,
            })),
        });
    };

    return (
        <div className="p-8 max-w-7xl mx-auto h-[calc(100vh-64px)] overflow-hidden flex flex-col">
            <div className="flex justify-between items-center mb-8 shrink-0">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                        <GitBranch className="w-8 h-8 text-primary-600" />
                        Smart Workflow Builder
                    </h1>
                    <p className="text-gray-500 mt-1">Design and manage approval chains</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors shadow-sm"
                >
                    <Plus className="w-4 h-4" />
                    New Workflow
                </button>
            </div>

            <div className="flex flex-1 gap-8 overflow-hidden">
                {/* Workflow List */}
                <div className="w-1/3 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col">
                    <div className="p-4 border-b border-gray-100 bg-gray-50/50">
                        <h2 className="font-semibold text-gray-700">Active Workflows</h2>
                    </div>
                    <div className="overflow-y-auto p-2 space-y-2 flex-1">
                        {isLoading ? (
                            <div className="p-4 text-center text-gray-400">Loading workflows...</div>
                        ) : workflows.length === 0 ? (
                            <div className="p-8 text-center text-gray-400">
                                <GitBranch className="w-10 h-10 mx-auto mb-3 opacity-20" />
                                <p className="text-sm">No workflows yet</p>
                                <p className="text-xs mt-1">Click "New Workflow" to create one</p>
                            </div>
                        ) : (
                            workflows.map((wf: any) => (
                                <div
                                    key={wf.id}
                                    onClick={() => setSelectedWorkflow(wf)}
                                    className={`p-4 rounded-lg cursor-pointer border transition-all ${selectedWorkflow?.id === wf.id
                                        ? 'bg-primary-50 border-primary-200 shadow-sm'
                                        : 'bg-white border-transparent hover:bg-gray-50 hover:border-gray-200'
                                        }`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className={`font-medium ${selectedWorkflow?.id === wf.id ? 'text-primary-900' : 'text-gray-900'}`}>
                                            {wf.name}
                                        </h3>
                                        <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wide
                      ${wf.status === 'active' ? 'bg-green-100 text-green-700' :
                                                wf.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                                                    'bg-gray-100 text-gray-600'}`}>
                                            {wf.status}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500 line-clamp-2">{wf.description}</p>
                                    <p className="text-xs text-gray-400 mt-2">{wf.steps?.length || 0} steps</p>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Workflow Visualizer */}
                <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col relative overflow-hidden bg-dot-pattern">
                    {!selectedWorkflow ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                            <GitBranch className="w-16 h-16 mb-4 opacity-20" />
                            <p>Select a workflow to visualize</p>
                        </div>
                    ) : (
                        <div className="flex-1 p-8 overflow-y-auto flex flex-col items-center">
                            <div className="max-w-2xl w-full">
                                <div className="text-center mb-10">
                                    <h2 className="text-2xl font-bold text-gray-900">{selectedWorkflow.name}</h2>
                                    <p className="text-gray-500">{selectedWorkflow.description}</p>
                                </div>

                                <div className="space-y-8 relative">
                                    {/* Vertical Line */}
                                    <div className="absolute left-1/2 top-4 bottom-4 w-0.5 bg-gray-200 -translate-x-1/2 z-0" />

                                    {selectedWorkflow.steps.map((step: any, _index: number) => {
                                        const isCompleted = step.status === 'approved';
                                        const isActive = step.status === 'active';
                                        const isPending = step.status === 'pending';

                                        return (
                                            <div key={step.id} className="relative z-10 flex items-center justify-center">
                                                <div className={`w-full max-w-lg bg-white p-6 rounded-xl border-2 shadow-sm transition-all
                          ${isCompleted ? 'border-green-500 shadow-green-50' :
                                                        isActive ? 'border-blue-500 shadow-blue-50 ring-4 ring-blue-50' :
                                                            'border-gray-200'}`}>

                                                    <div className="flex items-start gap-4">
                                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 border-2
                              ${isCompleted ? 'bg-green-50 border-green-500 text-green-600' :
                                                                isActive ? 'bg-blue-50 border-blue-500 text-blue-600' :
                                                                    'bg-gray-50 border-gray-200 text-gray-400'}`}>
                                                            {isCompleted ? <CheckCircle className="w-5 h-5" /> :
                                                                isActive ? <Play className="w-5 h-5" /> :
                                                                    <Clock className="w-5 h-5" />}
                                                        </div>

                                                        <div className="flex-1">
                                                            <div className="flex justify-between">
                                                                <h4 className="font-bold text-gray-900">{step.name}</h4>
                                                                <span className={`text-xs px-2 py-1 rounded font-medium
                                  ${isCompleted ? 'bg-green-100 text-green-700' :
                                                                        isActive ? 'bg-blue-100 text-blue-700' :
                                                                            'bg-gray-100 text-gray-500'}`}>
                                                                    {step.approver_role}
                                                                </span>
                                                            </div>

                                                            {step.condition && (
                                                                <div className="mt-2 flex items-center gap-2 text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded w-fit border border-orange-100">
                                                                    <DollarSign className="w-3 h-3" />
                                                                    Condition: {step.condition}
                                                                </div>
                                                            )}

                                                            {(isActive || isPending) && !isCompleted && (
                                                                <div className="mt-4 flex gap-2">
                                                                    <button
                                                                        onClick={() => approveStepMutation.mutate({ wfId: selectedWorkflow.id, stepId: step.id })}
                                                                        disabled={approveStepMutation.isPending}
                                                                        className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded shadow-sm transition-colors disabled:opacity-50"
                                                                    >
                                                                        {approveStepMutation.isPending ? 'Approving...' : 'Approve Step'}
                                                                    </button>
                                                                    <button className="px-3 py-1.5 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded shadow-sm transition-colors">
                                                                        Reject
                                                                    </button>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}

                                    {/* End Node */}
                                    <div className="relative z-10 flex items-center justify-center">
                                        <div className="px-4 py-2 bg-gray-100 rounded-full text-xs font-semibold text-gray-500 uppercase tracking-wider border border-gray-200">
                                            End of Workflow
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Create Workflow Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center p-6 border-b border-gray-100">
                            <h2 className="text-xl font-bold text-gray-900">Create New Workflow</h2>
                            <button onClick={resetCreateForm} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                                <X className="w-5 h-5 text-gray-500" />
                            </button>
                        </div>

                        <div className="p-6 space-y-6">
                            {/* Name */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Workflow Name *</label>
                                <input
                                    type="text"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    placeholder="e.g. NDA Approval Chain"
                                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                />
                            </div>

                            {/* Description */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                                <textarea
                                    value={newDescription}
                                    onChange={(e) => setNewDescription(e.target.value)}
                                    placeholder="Describe the purpose of this workflow..."
                                    rows={3}
                                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                                />
                            </div>

                            {/* Steps */}
                            <div>
                                <div className="flex justify-between items-center mb-3">
                                    <label className="block text-sm font-medium text-gray-700">Approval Steps *</label>
                                    <button
                                        onClick={addStep}
                                        className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 font-medium"
                                    >
                                        <Plus className="w-4 h-4" />
                                        Add Step
                                    </button>
                                </div>

                                <div className="space-y-3">
                                    {newSteps.map((step, index) => (
                                        <div key={index} className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg border border-gray-100">
                                            <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold shrink-0 mt-1">
                                                {index + 1}
                                            </div>
                                            <div className="flex-1 grid grid-cols-2 gap-3">
                                                <input
                                                    type="text"
                                                    value={step.name}
                                                    onChange={(e) => updateStep(index, 'name', e.target.value)}
                                                    placeholder="Step name (e.g. Legal Review)"
                                                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                                />
                                                <input
                                                    type="text"
                                                    value={step.approver_role}
                                                    onChange={(e) => updateStep(index, 'approver_role', e.target.value)}
                                                    placeholder="Approver role (e.g. Legal Manager)"
                                                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                                />
                                                <input
                                                    type="text"
                                                    value={step.condition || ''}
                                                    onChange={(e) => updateStep(index, 'condition', e.target.value)}
                                                    placeholder="Condition (optional, e.g. value > 50000)"
                                                    className="col-span-2 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                                />
                                            </div>
                                            {newSteps.length > 1 && (
                                                <button
                                                    onClick={() => removeStep(index)}
                                                    className="p-2 hover:bg-red-50 text-gray-400 hover:text-red-500 rounded-lg transition-colors shrink-0 mt-1"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 p-6 border-t border-gray-100">
                            <button
                                onClick={resetCreateForm}
                                className="px-5 py-2.5 border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleCreate}
                                disabled={createWorkflowMutation.isPending}
                                className="px-5 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
                            >
                                <GitBranch className="w-4 h-4" />
                                {createWorkflowMutation.isPending ? 'Creating...' : 'Create Workflow'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
