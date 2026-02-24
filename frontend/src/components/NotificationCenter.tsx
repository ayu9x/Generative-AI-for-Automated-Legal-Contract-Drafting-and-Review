import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsAPI } from '../services/api';
import { Link } from 'react-router-dom';
import {
    Bell,
    CheckCircle,
    AlertTriangle,
    Clock,
    FileText,
    Shield,
    MessageCircle,
    X,
    Check,
} from 'lucide-react';

export default function NotificationCenter() {
    const [isOpen, setIsOpen] = useState(false);
    const queryClient = useQueryClient();

    const { data: countData } = useQuery({
        queryKey: ['unread-count'],
        queryFn: () => notificationsAPI.getUnreadCount(),
        refetchInterval: 30000,
    });

    const { data: notificationsData } = useQuery({
        queryKey: ['notifications'],
        queryFn: () => notificationsAPI.list({ page_size: 10 }),
        enabled: isOpen,
    });

    const markReadMutation = useMutation({
        mutationFn: (id: string) => notificationsAPI.markAsRead(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['unread-count'] });
            queryClient.invalidateQueries({ queryKey: ['notifications'] });
        },
    });

    const markAllReadMutation = useMutation({
        mutationFn: () => notificationsAPI.markAllRead(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['unread-count'] });
            queryClient.invalidateQueries({ queryKey: ['notifications'] });
        },
    });

    const unreadCount = countData?.data?.unread_count || 0;
    const notifications = notificationsData?.data?.notifications || [];

    const getIcon = (iconName: string, color: string) => {
        const colorClass =
            color === 'red' ? 'text-red-600' :
                color === 'green' ? 'text-green-600' :
                    color === 'yellow' ? 'text-yellow-600' :
                        color === 'blue' ? 'text-blue-600' : 'text-gray-600';

        switch (iconName) {
            case 'alert-triangle': return <AlertTriangle className={`w-4 h-4 ${colorClass}`} />;
            case 'check-circle': return <CheckCircle className={`w-4 h-4 ${colorClass}`} />;
            case 'clock': return <Clock className={`w-4 h-4 ${colorClass}`} />;
            case 'shield-check': return <Shield className={`w-4 h-4 ${colorClass}`} />;
            case 'file-plus': return <FileText className={`w-4 h-4 ${colorClass}`} />;
            case 'message-circle': return <MessageCircle className={`w-4 h-4 ${colorClass}`} />;
            default: return <Bell className={`w-4 h-4 ${colorClass}`} />;
        }
    };

    const getBgColor = (color: string) => {
        switch (color) {
            case 'red': return 'bg-red-100';
            case 'green': return 'bg-green-100';
            case 'yellow': return 'bg-yellow-100';
            case 'blue': return 'bg-blue-100';
            default: return 'bg-gray-100';
        }
    };

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
            >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                    <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-gray-900" />
                )}
            </button>

            {isOpen && (
                <>
                    <div
                        className="fixed inset-0 z-30"
                        onClick={() => setIsOpen(false)}
                    />
                    <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-xl border border-gray-200 z-40 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                        <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
                            <h3 className="font-semibold text-gray-900">Notifications</h3>
                            {unreadCount > 0 && (
                                <button
                                    onClick={() => markAllReadMutation.mutate()}
                                    className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                                >
                                    <Check className="w-3 h-3" />
                                    Mark all read
                                </button>
                            )}
                        </div>

                        <div className="max-h-[32rem] overflow-y-auto">
                            {notifications.length === 0 ? (
                                <div className="p-8 text-center text-gray-500">
                                    <Bell className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                                    <p className="text-sm">No notifications yet</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-gray-50">
                                    {notifications.map((notif: any) => (
                                        <div
                                            key={notif.id}
                                            className={`p-4 hover:bg-gray-50 transition-colors relative group ${!notif.is_read ? 'bg-blue-50/30' : ''
                                                }`}
                                        >
                                            <div className="flex gap-3">
                                                <div className={`mt-1 min-w-[32px] w-8 h-8 rounded-full flex items-center justify-center ${getBgColor(notif.color)}`}>
                                                    {getIcon(notif.icon, notif.color)}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <Link
                                                        to={notif.link || '#'}
                                                        onClick={() => {
                                                            if (!notif.is_read) markReadMutation.mutate(notif.id);
                                                            setIsOpen(false);
                                                        }}
                                                    >
                                                        <p className={`text-sm ${!notif.is_read ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>
                                                            {notif.title}
                                                        </p>
                                                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                                                            {notif.message}
                                                        </p>
                                                        <p className="text-[10px] text-gray-400 mt-1.5">
                                                            {new Date(notif.created_at).toLocaleDateString()} • {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                        </p>
                                                    </Link>
                                                </div>
                                                {!notif.is_read && (
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            markReadMutation.mutate(notif.id);
                                                        }}
                                                        className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-gray-200 rounded-full text-gray-400"
                                                        title="Mark as read"
                                                    >
                                                        <X className="w-3 h-3" />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="p-3 border-t border-gray-100 bg-gray-50 text-center">
                            <Link
                                to="/notifications"
                                className="text-xs font-medium text-gray-600 hover:text-primary-600 transition-colors"
                                onClick={() => setIsOpen(false)}
                            >
                                View all notifications
                            </Link>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
