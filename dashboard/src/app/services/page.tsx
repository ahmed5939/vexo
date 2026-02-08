'use client';

import { Cog, RotateCcw, CheckCircle, XCircle, Activity, Clock, Server, Globe, Bot } from 'lucide-react';
import { useState } from 'react';

interface Service {
    id: string;
    name: string;
    description: string;
    status: 'online' | 'offline' | 'restarting';
    uptime?: string;
    icon: React.ElementType;
}

const services: Service[] = [
    {
        id: 'bot',
        name: 'Discord Bot',
        description: 'Core Discord bot handling commands and audio playback',
        status: 'online',
        uptime: '2d 14h 32m',
        icon: Bot,
    },
    {
        id: 'dashboard',
        name: 'Dashboard',
        description: 'This Next.js web dashboard',
        status: 'online',
        uptime: 'Running',
        icon: Globe,
    },
];

function ServiceCard({
    service,
    onRestart,
    isRestarting,
}: {
    service: Service;
    onRestart: () => void;
    isRestarting: boolean;
}) {
    const Icon = service.icon;

    const statusColors = {
        online: 'bg-green-500',
        offline: 'bg-red-500',
        restarting: 'bg-yellow-500',
    };

    const statusText = {
        online: 'Online',
        offline: 'Offline',
        restarting: 'Restarting...',
    };

    return (
        <div className="bento-card">
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500/20 to-pink-500/20 flex items-center justify-center">
                        <Icon className="w-6 h-6 text-violet-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">{service.name}</h3>
                        <p className="text-sm text-zinc-500">{service.description}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${statusColors[service.status]} animate-pulse`} />
                    <span className="text-sm text-zinc-400">{statusText[service.status]}</span>
                </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-white/[0.08]">
                <div className="flex items-center gap-4 text-sm text-zinc-500">
                    <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{service.uptime || '—'}</span>
                    </div>
                </div>

                <button
                    onClick={onRestart}
                    disabled={isRestarting || service.id === 'dashboard'}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all
            ${isRestarting
                            ? 'bg-yellow-500/20 text-yellow-500 cursor-not-allowed'
                            : service.id === 'dashboard'
                                ? 'bg-zinc-500/20 text-zinc-500 cursor-not-allowed'
                                : 'bg-violet-500/20 text-violet-400 hover:bg-violet-500/30'
                        }`}
                >
                    <RotateCcw className={`w-4 h-4 ${isRestarting ? 'animate-spin' : ''}`} />
                    {isRestarting ? 'Restarting...' : 'Restart'}
                </button>
            </div>
        </div>
    );
}

export default function ServicesPage() {
    const [restartingServices, setRestartingServices] = useState<Set<string>>(new Set());

    const handleRestart = async (serviceId: string) => {
        setRestartingServices(prev => new Set(prev).add(serviceId));

        try {
            // Call the Python bot's restart endpoint
            const response = await fetch(`http://localhost:8080/api/services/${serviceId}/restart`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error('Restart failed');
            }

            // Wait a bit for the service to restart
            await new Promise(resolve => setTimeout(resolve, 5000));

        } catch (error) {
            console.error('Failed to restart service:', error);
        } finally {
            setRestartingServices(prev => {
                const next = new Set(prev);
                next.delete(serviceId);
                return next;
            });
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Cog className="w-7 h-7 text-violet-500" />
                        Services
                    </h1>
                    <p className="text-sm text-zinc-500 mt-1">
                        Manage and monitor running services
                    </p>
                </div>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-3 gap-4">
                <div className="bento-card flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center">
                        <CheckCircle className="w-6 h-6 text-green-500" />
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-white">
                            {services.filter(s => s.status === 'online').length}
                        </p>
                        <p className="text-sm text-zinc-500">Services Online</p>
                    </div>
                </div>

                <div className="bento-card flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center">
                        <XCircle className="w-6 h-6 text-red-500" />
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-white">
                            {services.filter(s => s.status === 'offline').length}
                        </p>
                        <p className="text-sm text-zinc-500">Services Offline</p>
                    </div>
                </div>

                <div className="bento-card flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center">
                        <Activity className="w-6 h-6 text-violet-500" />
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-white">{services.length}</p>
                        <p className="text-sm text-zinc-500">Total Services</p>
                    </div>
                </div>
            </div>

            {/* Service Cards */}
            <div className="space-y-4">
                {services.map((service) => (
                    <ServiceCard
                        key={service.id}
                        service={service}
                        onRestart={() => handleRestart(service.id)}
                        isRestarting={restartingServices.has(service.id)}
                    />
                ))}
            </div>

            {/* Info */}
            <div className="bento-card bg-blue-500/5 border-blue-500/20">
                <div className="flex items-start gap-3">
                    <Activity className="w-5 h-5 text-blue-400 mt-0.5" />
                    <div>
                        <p className="text-sm font-medium text-white">Service Restart Note</p>
                        <p className="text-sm text-zinc-400 mt-1">
                            Restarting the Discord bot will disconnect all active voice channels.
                            Users will need to rejoin or use /play again after the bot reconnects.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
