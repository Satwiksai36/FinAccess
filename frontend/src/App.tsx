import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Landing from './components/Landing';
import ApplicantDashboard from './components/ApplicantDashboard';
import AdminDashboard from './components/AdminDashboard';

type Tab = 'landing' | 'applicant' | 'admin';

const LogoIcon = () => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className="flex-shrink-0">
        <rect x="0.5" y="0.5" width="47" height="47" rx="14" fill="#0A0F16" stroke="url(#border-gradient)" strokeWidth="1" />

        <path d="M12 34 L36 34" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
        <path d="M12 34 L12 28 M20 34 L20 20 M28 34 L28 25 M36 34 L36 16" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />

        <path d="M12 28 L20 20 L28 25 L36 16" stroke="url(#line-gradient)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ filter: 'drop-shadow(0px 4px 6px rgba(0, 229, 160, 0.4))' }} />

        <circle cx="36" cy="16" r="3" fill="#FFFFFF" style={{ filter: 'drop-shadow(0px 0px 6px #00E5A0)' }} />
        <circle cx="36" cy="16" r="1.5" fill="#00E5A0" />

        <defs>
            <linearGradient id="border-gradient" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                <stop stopColor="#00E5A0" stopOpacity="0.4" />
                <stop offset="0.5" stopColor="#4F7CFF" stopOpacity="0.1" />
                <stop offset="1" stopColor="#00E5A0" stopOpacity="0.1" />
            </linearGradient>
            <linearGradient id="line-gradient" x1="12" y1="28" x2="36" y2="16" gradientUnits="userSpaceOnUse">
                <stop stopColor="#4F7CFF" />
                <stop offset="1" stopColor="#00E5A0" />
            </linearGradient>
        </defs>
    </svg>
);

export default function App() {
    const [tab, setTab] = useState<Tab>('landing');

    return (
        <div className="min-h-screen flex flex-col" style={{ background: '#06080F' }}>
            {/* ── NAV ── */}
            <header style={{ background: 'rgba(6,8,15,0.85)', borderBottom: '1px solid rgba(255,255,255,0.06)', backdropFilter: 'blur(16px)' }}
                className="sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 h-[72px] flex items-center justify-between">
                    <button onClick={() => setTab('landing')} className="flex items-center gap-4 group">
                        <LogoIcon />
                        <div className="leading-none text-left">
                            <div className="text-[26px] font-black tracking-[-0.03em] mb-1">
                                <span style={{ color: '#00E5A0' }}>Fin</span>
                                <span style={{ color: '#FFFFFF' }}>Access</span>
                            </div>
                            <div style={{ color: '#4B5563', fontSize: '10px', letterSpacing: '0.24em', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700 }} className="uppercase">Intelligence System</div>
                        </div>
                    </button>

                    <nav className="flex items-center gap-1 p-1 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}>
                        {(['landing', 'applicant', 'admin'] as Tab[]).map((t) => {
                            const label = t === 'landing' ? 'Home' : t === 'applicant' ? 'Applicant Portal' : 'Admin Intelligence';
                            const active = tab === t;
                            return (
                                <button key={t} onClick={() => setTab(t)}
                                    style={{ background: active ? 'rgba(0,229,160,0.12)' : 'transparent', color: active ? '#00E5A0' : '#8892A4', border: active ? '1px solid rgba(0,229,160,0.2)' : '1px solid transparent' }}
                                    className="px-4 py-2 rounded-lg text-sm font-bold transition-all duration-200 hover:text-textPrimary">
                                    {label}
                                </button>
                            );
                        })}
                    </nav>

                    <div className="w-[120px]" /> {/* spacer */}
                </div>
            </header>

            {/* ── PAGE ── */}
            <main className="flex-1 flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div key={tab} className="flex-1 flex flex-col w-full h-full" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.25, ease: 'easeOut' }}>
                        {tab === 'landing' && <Landing onNavigate={t => setTab(t as Tab)} />}
                        {tab === 'applicant' && <ApplicantDashboard />}
                        {tab === 'admin' && <AdminDashboard />}
                    </motion.div>
                </AnimatePresence>
            </main>
        </div>
    );
}
