
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { collaborationAPI } from '../services/api';
import {
    MessageSquare,
    CheckCircle,
    Clock,
    MoreHorizontal,
    Plus,
    User,
    Activity,
    Calendar,
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function Collaboration() {
    const queryClient = useQueryClient();
    const [newTaskTitle, setNewTaskTitle] = useState('');

    const { data: tasksData, isLoading: tasksLoading } = useQuery({
        queryKey: ['collab-tasks'],
        queryFn: () => collaborationAPI.getTasks(),
    });

    const { data: activityData } = useQuery({
        queryKey: ['collab-activity'],
        queryFn: () => collaborationAPI.getActivityFeed(),
    });

    const createTaskMutation = useMutation({
        mutationFn: (title: string) => collaborationAPI.createTask({
            title,
            status: 'todo',
            assignee: 'Unassigned',
            priority: 'medium'
        }),
        onSuccess: () => {
            toast.success('Task created');
            setNewTaskTitle('');
            queryClient.invalidateQueries({ queryKey: ['collab-tasks'] });
        },
    });

    const updateStatusMutation = useMutation({
        mutationFn: ({ id, status }: { id: string; status: string }) =>
            collaborationAPI.updateTaskStatus(id, status),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['collab-tasks'] }),
    });

    const tasks = tasksData?.data || [];
    const activity = activityData?.data || [];

    const columns = [
        { id: 'todo', title: 'To Do', color: 'bg-gray-100', dot: 'bg-gray-400' },
        { id: 'in_progress', title: 'In Progress', color: 'bg-blue-50', dot: 'bg-blue-500' },
        { id: 'done', title: 'Done', color: 'bg-green-50', dot: 'bg-green-500' },
    ];

    return (
        <div className="p-8 max-w-7xl mx-auto h-[calc(100vh-64px)] flex flex-col gap-8">
            <div className="flex justify-between items-center shrink-0">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                        <MessageSquare className="w-8 h-8 text-primary-600" />
                        Collaboration Hub
                    </h1>
                    <p className="text-gray-500 mt-1">Manage tasks and track team activity</p>
                </div>
                <div className="flex -space-x-2">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="w-8 h-8 rounded-full bg-gray-200 border-2 border-white flex items-center justify-center text-xs font-medium text-gray-600">
                            U{i}
                        </div>
                    ))}
                    <div className="w-8 h-8 rounded-full bg-gray-100 border-2 border-white flex items-center justify-center text-xs text-gray-400 hover:bg-gray-200 cursor-pointer">
                        <Plus className="w-3 h-3" />
                    </div>
                </div>
            </div>

            <div className="flex flex-1 gap-8 overflow-hidden">
                {/* Kanban Board */}
                <div className="flex-1 flex gap-4 overflow-x-auto pb-4">
                    {columns.map((col) => {
                        const colTasks = tasks.filter((t: any) => t.status === col.id);
                        return (
                            <div key={col.id} className={`flex-1 min-w-[300px] rounded-xl flex flex-col ${col.color}`}>
                                <div className="p-4 flex justify-between items-center shrink-0">
                                    <div className="flex items-center gap-2 font-semibold text-gray-700">
                                        <div className={`w-2 h-2 rounded-full ${col.dot}`} />
                                        {col.title}
                                        <span className="text-xs font-normal text-gray-500 bg-white/50 px-2 py-0.5 rounded-full">
                                            {colTasks.length}
                                        </span>
                                    </div>
                                    <MoreHorizontal className="w-4 h-4 text-gray-400 cursor-pointer" />
                                </div>

                                <div className="flex-1 overflow-y-auto p-4 pt-0 space-y-3 custom-scrollbar">
                                    {colTasks.map((task: any) => (
                                        <div key={task.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 group hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing">
                                            <div className="flex justify-between items-start mb-2">
                                                <span className={`px-2 py-0.5 text-[10px] uppercase font-bold rounded-full tracking-wide
                          ${task.priority === 'high' ? 'bg-red-50 text-red-600' :
                                                        task.priority === 'medium' ? 'bg-yellow-50 text-yellow-600' : 'bg-blue-50 text-blue-600'}`}>
                                                    {task.priority}
                                                </span>
                                                <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                                                    {col.id !== 'todo' && (
                                                        <button onClick={() => updateStatusMutation.mutate({ id: task.id, status: 'todo' })} className="p-1 hover:bg-gray-100 rounded" title="Move to Todo">←</button>
                                                    )}
                                                    {col.id !== 'done' && (
                                                        <button onClick={() => updateStatusMutation.mutate({ id: task.id, status: 'done' })} className="p-1 hover:bg-gray-100 rounded" title="Move to Done">→</button>
                                                    )}
                                                </div>
                                            </div>
                                            <h3 className="font-medium text-gray-900 mb-1">{task.title}</h3>
                                            <div className="flex items-center gap-2 text-xs text-gray-500 mb-3">
                                                <User className="w-3 h-3" /> {task.assignee}
                                            </div>
                                            <div className="border-t border-gray-50 pt-2 flex justify-between items-center text-xs text-gray-400">
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="w-3 h-3" />
                                                    {task.due_date ? new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : 'No date'}
                                                </span>
                                            </div>
                                        </div>
                                    ))}

                                    {col.id === 'todo' && (
                                        <div className="mt-2">
                                            <input
                                                type="text"
                                                placeholder="+ Add task"
                                                className="w-full px-3 py-2 bg-white/50 border border-transparent hover:border-gray-300 rounded-lg text-sm transition-colors focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter') {
                                                        createTaskMutation.mutate(e.currentTarget.value);
                                                        e.currentTarget.value = '';
                                                    }
                                                }}
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Activity Feed Sidebar */}
                <div className="w-80 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col shrink-0">
                    <div className="p-4 border-b border-gray-100">
                        <h2 className="font-semibold text-gray-700 flex items-center gap-2">
                            <Activity className="w-4 h-4 text-primary-500" />
                            Activity Feed
                        </h2>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-6">
                        {activity.map((item: any) => (
                            <div key={item.id} className="flex gap-3 relative">
                                <div className="absolute left-3.5 top-6 bottom-[-24px] w-px bg-gray-100 last:hidden" />
                                <div className="w-7 h-7 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 border border-blue-100 text-xs font-bold z-10">
                                    {item.user_name.charAt(0)}
                                </div>
                                <div>
                                    <p className="text-sm text-gray-900">
                                        <span className="font-medium">{item.user_name}</span>{' '}
                                        <span className="text-gray-500">{item.action}</span>{' '}
                                        <span className="font-medium">{item.target}</span>
                                    </p>
                                    <p className="text-xs text-gray-400 mt-1">{new Date(item.timestamp).toLocaleString()}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
