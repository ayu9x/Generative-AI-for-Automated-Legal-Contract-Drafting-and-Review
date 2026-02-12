
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { calendarAPI } from '../services/api';
import {
    Calendar as CalendarIcon,
    ChevronLeft,
    ChevronRight,
    Clock,
    AlertCircle,
    FileText,
    DollarSign,
    RefreshCw,
    Shield,
    CheckCircle,
} from 'lucide-react';

export default function ContractCalendar() {
    const [currentDate, setCurrentDate] = useState(new Date());

    const { data: eventsData } = useQuery({
        queryKey: ['calendar-events', currentDate.getMonth(), currentDate.getFullYear()],
        queryFn: () => calendarAPI.getEvents({
            month: currentDate.getMonth() + 1,
            year: currentDate.getFullYear()
        }),
    });

    const { data: upcomingData } = useQuery({
        queryKey: ['upcoming-events'],
        queryFn: () => calendarAPI.getUpcoming(30),
    });

    const events = eventsData?.data?.events || [];
    const upcoming = upcomingData?.data?.upcoming || [];

    const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
    const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay();

    const handlePrevMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    };

    const handleNextMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    };

    const getEventIcon = (type: string) => {
        switch (type) {
            case 'renewal': return <RefreshCw className="w-3 h-3" />;
            case 'payment': return <DollarSign className="w-3 h-3" />;
            case 'compliance': return <Shield className="w-3 h-3" />;
            case 'expiry': return <AlertCircle className="w-3 h-3" />;
            default: return <FileText className="w-3 h-3" />;
        }
    };

    const dayCells = [];
    // Empty cells for previous month
    for (let i = 0; i < firstDayOfMonth; i++) {
        dayCells.push(<div key={`empty-${i}`} className="min-h-[120px] bg-gray-50/30 border-r border-b border-gray-100" />);
    }

    // Day cells
    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const dayEvents = events.filter((e: any) => e.date === dateStr);
        const isToday = new Date().toISOString().split('T')[0] === dateStr;

        dayCells.push(
            <div key={d} className={`min-h-[120px] border-r border-b border-gray-100 p-2 relative group hover:bg-gray-50 transition-colors ${isToday ? 'bg-blue-50/30' : ''}`}>
                <span className={`text-sm font-medium w-6 h-6 flex items-center justify-center rounded-full ${isToday ? 'bg-primary-600 text-white' : 'text-gray-700'}`}>
                    {d}
                </span>
                <div className="mt-2 space-y-1 overflow-y-auto max-h-[88px] no-scrollbar">
                    {dayEvents.map((event: any) => (
                        <div
                            key={event.id}
                            className={`text-[10px] px-1.5 py-1 rounded truncate flex items-center gap-1 cursor-pointer hover:opacity-80 transition-opacity border border-transparent mb-1
                ${event.color === 'red' ? 'bg-red-50 text-red-700 border-red-100' :
                                    event.color === 'yellow' ? 'bg-yellow-50 text-yellow-800 border-yellow-100' :
                                        event.color === 'green' ? 'bg-green-50 text-green-700 border-green-100' :
                                            event.color === 'purple' ? 'bg-purple-50 text-purple-700 border-purple-100' :
                                                'bg-blue-50 text-blue-700 border-blue-100'}`}
                            title={event.title}
                        >
                            <div className={`w-1.5 h-1.5 rounded-full shrink-0 
                ${event.color === 'red' ? 'bg-red-500' :
                                    event.color === 'yellow' ? 'bg-yellow-500' :
                                        event.color === 'green' ? 'bg-green-500' :
                                            event.color === 'purple' ? 'bg-purple-500' :
                                                'bg-blue-500'}`} />
                            <span className="truncate">{event.title}</span>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="p-8 max-w-[1600px] mx-auto">
            <div className="flex flex-col lg:flex-row gap-8">
                {/* Main Calendar Section */}
                <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    {/* Calendar Header */}
                    <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-white">
                        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                            <CalendarIcon className="w-6 h-6 text-primary-600" />
                            {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
                        </h1>
                        <div className="flex items-center gap-2 bg-gray-50 rounded-lg p-1 border border-gray-200">
                            <button onClick={handlePrevMonth} className="p-1.5 hover:bg-white rounded-md text-gray-500 hover:text-gray-900 hover:shadow-sm transition-all">
                                <ChevronLeft className="w-5 h-5" />
                            </button>
                            <button
                                onClick={() => setCurrentDate(new Date())}
                                className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-white rounded-md hover:shadow-sm transition-all"
                            >
                                Today
                            </button>
                            <button onClick={handleNextMonth} className="p-1.5 hover:bg-white rounded-md text-gray-500 hover:text-gray-900 hover:shadow-sm transition-all">
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Weekday Headers */}
                    <div className="grid grid-cols-7 bg-gray-50 border-b border-gray-100">
                        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                            <div key={day} className="py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                {day}
                            </div>
                        ))}
                    </div>

                    {/* Calendar Grid */}
                    <div className="grid grid-cols-7 bg-white">
                        {dayCells}
                    </div>
                </div>

                {/* Sidebar - Upcoming Deadlines */}
                <div className="w-full lg:w-96 space-y-6">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-8">
                        <h2 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
                            <Clock className="w-5 h-5 text-gray-400" />
                            Approaching Deadlines
                        </h2>

                        <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
                            {upcoming.length === 0 ? (
                                <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-200">
                                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
                                    <p className="text-sm text-gray-500">No upcoming deadlines</p>
                                </div>
                            ) : (
                                upcoming.map((event: any) => (
                                    <div key={event.id} className="group flex gap-4 p-4 rounded-xl hover:bg-gray-50 transition-all border border-transparent hover:border-gray-100">
                                        <div className={`mt-1 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center 
                       ${event.priority === 'high' ? 'bg-red-50 text-red-600' :
                                                event.priority === 'medium' ? 'bg-yellow-50 text-yellow-600' :
                                                    'bg-blue-50 text-blue-600'}`}>
                                            {getEventIcon(event.type)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className={`text-sm font-semibold truncate ${event.is_overdue ? 'text-red-700' : 'text-gray-900'}`}>
                                                {event.title}
                                            </h4>
                                            <div className="flex items-center gap-2 mt-1">
                                                <p className="text-xs text-gray-500 flex items-center gap-1">
                                                    {new Date(event.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                                </p>
                                                {event.is_overdue && (
                                                    <span className="text-[10px] font-bold text-red-600 bg-red-50 px-1.5 py-0.5 rounded-full border border-red-100">
                                                        Overdue
                                                    </span>
                                                )}
                                            </div>

                                            <div className="mt-2 flex flex-wrap gap-1.5">
                                                <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide border
                          ${event.type === 'review_due' ? 'bg-blue-50 text-blue-700 border-blue-100' :
                                                        event.type === 'renewal' ? 'bg-yellow-50 text-yellow-700 border-yellow-100' :
                                                            event.type === 'expiry' ? 'bg-orange-50 text-orange-700 border-orange-100' :
                                                                'bg-gray-50 text-gray-700 border-gray-100'}`}>
                                                    {event.type.replace('_', ' ')}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="mt-6 pt-6 border-t border-gray-100">
                            <button className="w-full flex items-center justify-center gap-2 py-2.5 text-sm text-gray-700 font-medium bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200">
                                <CalendarIcon className="w-4 h-4" />
                                Sync Calendar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
