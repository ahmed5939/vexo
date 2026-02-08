'use client';

import {
    FileText, Search, Trash2, Pause, Play, Download,
    AlertTriangle, AlertCircle, Info, Bug, Terminal,
    ChevronDown, Sparkles, Activity
} from 'lucide-react';
import { useState, useEffect, useRef, useMemo } from 'react';

interface LogEntry {
    timestamp: string;
    level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
    category: string;
    message: string;
}

const levelConfig = {
    INFO: {
        color: 'text-sky-400',
        bgColor: 'bg-sky-500/10',
        borderColor: 'border-sky-500/20',
        icon: Info,
        glow: 'shadow-sky-500/20',
    },
    WARNING: {
        color: 'text-amber-400',
        bgColor: 'bg-amber-500/10',
        borderColor: 'border-amber-500/20',
        icon: AlertTriangle,
        glow: 'shadow-amber-500/20',
    },
    ERROR: {
        color: 'text-rose-400',
        bgColor: 'bg-rose-500/10',
        borderColor: 'border-rose-500/20',
        icon: AlertCircle,
        glow: 'shadow-rose-500/20',
    },
    DEBUG: {
        color: 'text-zinc-500',
        bgColor: 'bg-zinc-500/10',
        borderColor: 'border-zinc-500/20',
        icon: Bug,
        glow: 'shadow-zinc-500/20',
    },
};

const categoryEmojis: Record<string, string> = {
    playback: '🎵',
    discovery: '🔍',
    voice: '🎤',
    database: '💾',
    api: '🌐',
    system: '⚙️',
    queue: '📋',
    user: '👤',
};

export default function LogsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isPaused, setIsPaused] = useState(false);
    const [filter, setFilter] = useState<string>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const logsEndRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Calculate stats
    const stats = useMemo(() => {
        const counts = { INFO: 0, WARNING: 0, ERROR: 0, DEBUG: 0 };
        logs.forEach(log => {
            if (counts[log.level] !== undefined) {
                counts[log.level]++;
            }
        });
        return counts;
    }, [logs]);

    // WebSocket connection for live logs
    useEffect(() => {
        if (isPaused) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || `${protocol}//${window.location.hostname}:6767/ws/logs`;
        let ws: WebSocket | null = null;
        let reconnectTimeout: NodeJS.Timeout;

        const connect = () => {
            try {
                ws = new WebSocket(wsUrl);

                ws.onopen = () => {
                    setIsConnected(true);
                };

                ws.onclose = () => {
                    setIsConnected(false);
                    // Reconnect after 3 seconds
                    reconnectTimeout = setTimeout(connect, 3000);
                };

                ws.onmessage = (event) => {
                    try {
                        const logEntry = JSON.parse(event.data);
                        setLogs((prev) => [...prev.slice(-500), logEntry]);
                    } catch {
                        // Handle plain text logs
                        setLogs((prev) => [
                            ...prev.slice(-500),
                            {
                                timestamp: new Date().toISOString(),
                                level: 'INFO',
                                category: 'system',
                                message: event.data,
                            },
                        ]);
                    }
                };

                ws.onerror = () => {
                    setIsConnected(false);
                };
            } catch (error) {
                console.error('Failed to connect to WebSocket:', error);
                setIsConnected(false);
            }
        };

        connect();

        return () => {
            clearTimeout(reconnectTimeout);
            if (ws) {
                ws.close();
            }
        };
    }, [isPaused]);

    // Auto-scroll to bottom
    useEffect(() => {
        if (!isPaused && logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs, isPaused]);

    const filteredLogs = useMemo(() => {
        return logs.filter((log) => {
            const matchesLevel = filter === 'all' || log.level === filter;
            const message = log.message || '';
            const category = log.category || '';
            const matchesSearch = searchQuery === '' ||
                message.toLowerCase().includes(searchQuery.toLowerCase()) ||
                category.toLowerCase().includes(searchQuery.toLowerCase());
            return matchesLevel && matchesSearch;
        });
    }, [logs, filter, searchQuery]);

    const formatTime = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    };

    const getCategoryEmoji = (category: string | null | undefined) => {
        if (!category) return '📝';
        const lower = category.toLowerCase();
        return categoryEmojis[lower] || '📝';
    };

    const exportLogs = () => {
        const content = filteredLogs.map(log =>
            `[${log.timestamp}] [${log.level}] [${log.category}] ${log.message}`
        ).join('\n');
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vexo-logs-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="h-full flex flex-col gap-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <div className="absolute inset-0 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-2xl blur-xl opacity-50" />
                        <div className="relative p-3 rounded-2xl bg-gradient-to-br from-violet-600/20 to-fuchsia-600/20 border border-violet-500/20">
                            <Terminal className="w-6 h-6 text-violet-400" />
                        </div>
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                            Live Logs
                            <Sparkles className="w-5 h-5 text-violet-400" />
                        </h1>
                        <p className="text-sm text-zinc-500">
                            Real-time bot activity stream
                        </p>
                    </div>
                </div>

                {/* Quick Stats */}
                <div className="flex items-center gap-2">
                    {Object.entries(stats).map(([level, count]) => {
                        const config = levelConfig[level as keyof typeof levelConfig];
                        if (count === 0) return null;
                        return (
                            <button
                                key={level}
                                onClick={() => setFilter(filter === level ? 'all' : level)}
                                className={`
                                    flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
                                    transition-all duration-200 border
                                    ${filter === level
                                        ? `${config.bgColor} ${config.color} ${config.borderColor}`
                                        : 'bg-white/[0.02] border-white/[0.05] text-zinc-400 hover:bg-white/[0.05]'
                                    }
                                `}
                            >
                                <config.icon className="w-3 h-3" />
                                {count}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Controls Bar */}
            <div className="flex items-center gap-3 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
                {/* Search */}
                <div className="relative flex-1 max-w-xs">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                    <input
                        type="text"
                        placeholder="Search logs..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 rounded-xl bg-white/[0.04] border border-white/[0.08] 
                                   text-sm text-white placeholder-zinc-500 outline-none 
                                   focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 transition-all"
                    />
                </div>

                {/* Filter Dropdown */}
                <div className="relative">
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="appearance-none pl-4 pr-10 py-2 rounded-xl bg-white/[0.04] border border-white/[0.08] 
                                   text-sm text-white outline-none cursor-pointer hover:bg-white/[0.06] transition-colors"
                    >
                        <option value="all">All Levels</option>
                        <option value="INFO">Info</option>
                        <option value="WARNING">Warning</option>
                        <option value="ERROR">Error</option>
                        <option value="DEBUG">Debug</option>
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 pointer-events-none" />
                </div>

                <div className="w-px h-6 bg-white/10" />

                {/* Pause/Resume */}
                <button
                    onClick={() => setIsPaused(!isPaused)}
                    className={`
                        flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200
                        ${isPaused
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20'
                        }
                    `}
                >
                    {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                    {isPaused ? 'Resume' : 'Pause'}
                </button>

                {/* Export */}
                <button
                    onClick={exportLogs}
                    className="p-2 rounded-xl bg-white/[0.04] border border-white/[0.08] 
                               hover:bg-white/[0.08] transition-colors group"
                    title="Export logs"
                >
                    <Download className="w-5 h-5 text-zinc-400 group-hover:text-violet-400 transition-colors" />
                </button>

                {/* Clear */}
                <button
                    onClick={() => setLogs([])}
                    className="p-2 rounded-xl bg-white/[0.04] border border-white/[0.08] 
                               hover:bg-rose-500/10 hover:border-rose-500/20 transition-colors group"
                    title="Clear logs"
                >
                    <Trash2 className="w-5 h-5 text-zinc-400 group-hover:text-rose-400 transition-colors" />
                </button>
            </div>

            {/* Logs Container */}
            <div className="flex-1 rounded-2xl bg-[#0c0c0d] border border-white/[0.05] overflow-hidden relative">
                {/* Glow effect */}
                <div className="absolute top-0 left-1/4 w-1/2 h-32 bg-gradient-to-b from-violet-600/5 to-transparent pointer-events-none" />

                <div ref={containerRef} className="h-full overflow-y-auto p-4 font-mono text-sm">
                    {filteredLogs.length === 0 ? (
                        <div className="h-full flex items-center justify-center">
                            <div className="text-center">
                                <div className="relative inline-block">
                                    <div className="absolute inset-0 bg-violet-600/20 rounded-full blur-xl" />
                                    <div className="relative p-6 rounded-full bg-white/[0.02] border border-white/[0.05]">
                                        <FileText className="w-10 h-10 text-zinc-600" />
                                    </div>
                                </div>
                                <p className="text-zinc-400 mt-6 font-sans">No logs yet</p>
                                <p className="text-xs text-zinc-600 mt-2 font-sans">
                                    Logs will appear here when the bot is running
                                </p>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-1">
                            {filteredLogs.map((log, i) => {
                                const config = levelConfig[log.level];
                                const Icon = config.icon;

                                return (
                                    <div
                                        key={i}
                                        className={`
                                            group flex items-start gap-3 py-2 px-3 rounded-lg
                                            hover:bg-white/[0.02] transition-colors duration-150
                                            ${log.level === 'ERROR' ? 'bg-rose-500/[0.03]' : ''}
                                        `}
                                    >
                                        {/* Time */}
                                        <span className="text-zinc-600 shrink-0 tabular-nums text-xs pt-0.5">
                                            {formatTime(log.timestamp)}
                                        </span>

                                        {/* Level Badge */}
                                        <div className={`
                                            shrink-0 flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium
                                            ${config.bgColor} ${config.color} border ${config.borderColor}
                                        `}>
                                            <Icon className="w-3 h-3" />
                                            <span className="hidden sm:inline">{log.level}</span>
                                        </div>

                                        {/* Category */}
                                        <span className="shrink-0 px-2 py-0.5 rounded-md bg-violet-500/10 text-violet-400 text-xs border border-violet-500/20">
                                            <span className="mr-1">{getCategoryEmoji(log.category)}</span>
                                            {log.category}
                                        </span>

                                        {/* Message */}
                                        <span className="text-zinc-300 break-all group-hover:text-white transition-colors">
                                            {log.message}
                                        </span>
                                    </div>
                                );
                            })}
                            <div ref={logsEndRef} />
                        </div>
                    )}
                </div>
            </div>

            {/* Status Bar */}
            <div className="flex items-center justify-between text-xs text-zinc-500 px-1">
                <div className="flex items-center gap-6">
                    {/* Connection Status */}
                    <span className={`flex items-center gap-2 ${isConnected ? 'text-emerald-400' : 'text-zinc-500'}`}>
                        <span className={`
                            relative flex h-2 w-2
                        `}>
                            {isConnected && (
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                            )}
                            <span className={`
                                relative inline-flex rounded-full h-2 w-2
                                ${isConnected ? 'bg-emerald-400' : 'bg-zinc-600'}
                            `} />
                        </span>
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </span>

                    {/* Live/Paused Status */}
                    <span className={`flex items-center gap-2 ${isPaused ? 'text-amber-400' : 'text-emerald-400'}`}>
                        <Activity className="w-3 h-3" />
                        {isPaused ? 'Paused' : 'Live'}
                    </span>

                    {/* Count */}
                    <span>
                        Showing <span className="text-white font-medium">{filteredLogs.length}</span> of <span className="text-white font-medium">{logs.length}</span> logs
                    </span>
                </div>

                <span className="text-zinc-600">
                    Buffer: {logs.length}/500
                </span>
            </div>
        </div>
    );
}
