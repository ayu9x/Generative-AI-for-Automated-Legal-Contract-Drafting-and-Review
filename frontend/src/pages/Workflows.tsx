
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsAPI } from '../services/api';
import {
    GitBranch,
    Plus,
    CheckCircle,
    Clock,
    Play,
    MoreVertical,
    ArrowRight,
    Shield,
    DollarSign,
    FileText,
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function Workflows() {
    const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null);
    const queryClient = useQueryClient();

    const { data: workflowsData, isLoading } = useQuery({
        queryKey: ['workflows'],
        queryFn: () => workflowsAPI.list(),
    });

    const workflows = workflowsData?.data || [];

    const approveStepMutation = useMutation({
        mutationFn: ({ wfId, stepId }: { wfId: string; stepId: string }) =>
            workflowsAPI.approveStep(wfId, stepId),
        onSuccess: (data) => {
            toast.success('Step approved');
            setSelectedWorkflow(data.data); // Update local state with latest workflow
            queryClient.invalidateQueries({ queryKey: ['workflows'] });
        },
        onError: () => toast.error('Failed to approve step'),
    });

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
                <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors shadow-sm">
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
                      ${wf.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                                            {wf.status}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500 line-clamp-2">{wf.description}</p>
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

                                    {selectedWorkflow.steps.map((step: any, index: number) => {
                                        const isCompleted = step.status === 'approved';
                                        const isActive = step.status === 'active' || step.status === 'pending'; // In this simple mock, pending implies waiting
                                        const isPending = step.status === 'pending';

                                        return (
                                            <div key={step.id} className="relative z-10 flex items-center justify-center">
                                                <div className={`w-full max-w-lg bg-white p-6 rounded-xl border-2 shadow-sm transition-all
                          ${isCompleted ? 'border-green-500 shadow-green-50' :
                                                        isActive && !isPending ? 'border-blue-500 shadow-blue-50 ring-4 ring-blue-50' :
                                                            'border-gray-200'}`}>

                                                    <div className="flex items-start gap-4">
                                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 border-2
                              ${isCompleted ? 'bg-green-50 border-green-500 text-green-600' :
                                                                isActive && !isPending ? 'bg-blue-50 border-blue-500 text-blue-600' :
                                                                    'bg-gray-50 border-gray-200 text-gray-400'}`}>
                                                            {isCompleted ? <CheckCircle className="w-5 h-5" /> :
                                                                isActive && !isPending ? <Play className="w-5 h-5" /> :
                                                                    <Clock className="w-5 h-5" />}
                                                        </div>

                                                        <div className="flex-1">
                                                            <div className="flex justify-between">
                                                                <h4 className="font-bold text-gray-900">{step.name}</h4>
                                                                <span className={`text-xs px-2 py-1 rounded font-medium
                                  ${isCompleted ? 'bg-green-100 text-green-700' :
                                                                        isActive && !isPending ? 'bg-blue-100 text-blue-700' :
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
                                                                        className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded shadow-sm transition-colors"
                                                                    >
                                                                        Approve Step
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
        </div>
    );
}
