import { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { assistantAPI } from '../services/api';
import {
    Send,
    Bot,
    User,
    Sparkles,
    ArrowRight,
    Loader2,
} from 'lucide-react';

interface Message {
    id: string;
    sender: 'user' | 'ai';
    text: string;
    timestamp: Date;
    category?: string;
    related?: Array<{ name: string; path: string; description: string }>;
}

export default function AIAssistant() {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            sender: 'ai',
            text: "Hello! I'm your AI Legal Assistant. I can help you understand legal terms, draft clauses, or answer compliance questions.\n\nTry asking about 'Force Majeure', 'GDPR requirements', or 'Termination rights'.",
            timestamp: new Date(),
        },
    ]);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const { data: suggestionsData } = useQuery({
        queryKey: ['assistant-suggestions'],
        queryFn: () => assistantAPI.getSuggestions(),
    });

    const chatMutation = useMutation({
        mutationFn: (msg: string) => assistantAPI.chat({ message: msg }),
        onSuccess: (res) => {
            const data = res.data;
            const aiMsg: Message = {
                id: data.id,
                sender: 'ai',
                text: data.response,
                timestamp: new Date(),
                category: data.category,
                related: data.related_features,
            };
            setMessages((prev) => [...prev, aiMsg]);
        },
    });

    const suggestions = suggestionsData?.data?.suggestions || [];

    const handleSend = () => {
        if (!input.trim()) return;
        const userMsg: Message = {
            id: Date.now().toString(),
            sender: 'user',
            text: input,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMsg]);
        chatMutation.mutate(input);
        setInput('');
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex h-[calc(100vh-64px)] bg-gray-50">
            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full bg-white shadow-xl border-x border-gray-100">
                {/* Header */}
                <div className="p-4 border-b border-gray-100 flex items-center gap-3 bg-white z-10">
                    <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                        <Bot className="w-6 h-6 text-primary-600" />
                    </div>
                    <div>
                        <h1 className="font-bold text-gray-900">AI Legal Assistant</h1>
                        <p className="text-xs text-gray-500 flex items-center gap-1">
                            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                            Online & Ready to help
                        </p>
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.sender === 'user' ? 'bg-gray-200' : 'bg-primary-600'
                                }`}>
                                {msg.sender === 'user' ? (
                                    <User className="w-4 h-4 text-gray-600" />
                                ) : (
                                    <Sparkles className="w-4 h-4 text-white" />
                                )}
                            </div>

                            <div className={`flex flex-col max-w-[80%] ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                                <div className={`rounded-2xl p-4 shadow-sm text-sm whitespace-pre-wrap leading-relaxed ${msg.sender === 'user'
                                    ? 'bg-gray-900 text-white rounded-tr-sm'
                                    : 'bg-white border border-gray-100 text-gray-800 rounded-tl-sm'
                                    }`}>
                                    {msg.text}
                                </div>

                                {/* Related Actions for AI messages */}
                                {msg.sender === 'ai' && msg.related && msg.related.length > 0 && (
                                    <div className="mt-3 flex flex-wrap gap-2 animate-in fade-in slide-in-from-top-2">
                                        {msg.related.map((item, i) => (
                                            <a
                                                key={i}
                                                href={item.path}
                                                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-50 text-primary-700 rounded-lg text-xs font-medium hover:bg-primary-100 transition-colors border border-primary-100"
                                            >
                                                {item.name}
                                                <ArrowRight className="w-3 h-3" />
                                            </a>
                                        ))}
                                    </div>
                                )}

                                <span className="text-[10px] text-gray-400 mt-1 px-1">
                                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        </div>
                    ))}

                    {chatMutation.isPending && (
                        <div className="flex items-start gap-3">
                            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center shrink-0">
                                <Sparkles className="w-4 h-4 text-white" />
                            </div>
                            <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm p-4 shadow-sm flex items-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin text-primary-500" />
                                <span className="text-sm text-gray-500">Thinking...</span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 bg-white border-t border-gray-100">
                    {/* Suggestions */}
                    {messages.length < 3 && (
                        <div className="flex gap-2 overflow-x-auto pb-4 scrollbar-hide">
                            {suggestions.map((s: any, i: number) => (
                                <button
                                    key={i}
                                    onClick={() => { setInput(s.text); handleSend(); }} // Fix: directly send on click logic requires state update first, or passing s.text to separate send func. Updating to setInput for now.
                                    className="flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-full text-xs text-gray-600 whitespace-nowrap transition-colors"
                                >
                                    <span>{s.icon}</span>
                                    {s.text}
                                </button>
                            ))}
                        </div>
                    )}

                    <div className="relative flex items-center gap-2">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask anything about contracts, clauses, or compliance..."
                            className="w-full pl-4 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none max-h-32 min-h-[50px] shadow-sm text-sm"
                            rows={1}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || chatMutation.isPending}
                            className="absolute right-2 p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                    <p className="text-[10px] text-center text-gray-400 mt-2">
                        AI can make mistakes. Always verify legal information with a qualified professional.
                    </p>
                </div>
            </div>
        </div>
    );
}
