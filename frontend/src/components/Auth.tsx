import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, User, KeyRound, ChevronRight, Mail, AlertCircle, Loader2, CheckCircle } from 'lucide-react';
import { apiLogin, apiRegister, authStore } from '../api';

/** Safely decode a base64url JWT payload even without padding */
function decodeJwtPayload(token: string): Record<string, any> {
    try {
        const part = token.split('.')[1] ?? '';
        const padded = part.replace(/-/g, '+').replace(/_/g, '/');
        const withPad = padded.padEnd(Math.ceil(padded.length / 4) * 4, '=');
        return JSON.parse(atob(withPad));
    } catch {
        return {};
    }
}

export default function Auth({
    onLogin,
    roleContext,
}: {
    onLogin: (role: 'applicant' | 'admin') => void;
    roleContext: 'applicant' | 'admin';
}) {
    const [isLogin, setIsLogin] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');

    const accentColor = roleContext === 'admin' ? '#4F7CFF' : '#00E5A0';
    const btnGrad = roleContext === 'admin'
        ? 'linear-gradient(135deg, #4F7CFF, #3b5bdb)'
        : 'linear-gradient(135deg, #00E5A0, #00C48A)';

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (!email || !password || (!isLogin && !name)) {
            setError('Please fill in all required fields.');
            return;
        }
        if (password.length < 6) {
            setError('Password must be at least 6 characters.');
            return;
        }

        setLoading(true);

        try {
            if (!isLogin) {
                // ── Create account ──────────────────────────────
                const role = roleContext === 'admin' ? 'ADMIN' : 'APPLICANT';
                await apiRegister({ email, password, role });
                setSuccess('Account created successfully! Signing you in…');
            }

            // ── Login ──────────────────────────────────────────
            const tokenData = await apiLogin({ email, password });
            const decoded = decodeJwtPayload(tokenData.access_token);
            // Role can come from JWT payload or default to context
            const serverRole: string = decoded.role ?? (roleContext === 'admin' ? 'ADMIN' : 'APPLICANT');
            authStore.setToken(tokenData.access_token, serverRole);

            // Role validation
            const isAdmin = serverRole === 'ADMIN';
            if (roleContext === 'admin' && !isAdmin) {
                authStore.clear();
                setError('This account does not have admin privileges. Please use the Applicant portal.');
                setLoading(false);
                return;
            }
            if (roleContext === 'applicant' && isAdmin) {
                authStore.clear();
                setError('Admin accounts must sign in via the Admin portal.');
                setLoading(false);
                return;
            }

            onLogin(roleContext);
        } catch (err: any) {
            const msg: string = err?.message ?? '';
            if (!msg || msg.includes('fetch') || msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('network')) {
                setError('Cannot connect to the backend server. Please start it with: python server.py (in the backend folder)');
            } else {
                setError(msg);
            }
        } finally {
            setLoading(false);
        }
    };

    const toggleMode = () => {
        setIsLogin(v => !v);
        setError('');
        setSuccess('');
        setName('');
    };

    return (
        <div className="flex-1 flex items-center justify-center p-6 min-h-[70vh]">
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="card w-full max-w-md p-8 relative overflow-hidden"
            >
                {/* Top accent line */}
                <div className="absolute top-0 left-0 w-full h-[3px]" style={{ background: accentColor }} />

                {/* Header */}
                <div className="text-center mb-8">
                    <div className="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center mb-4"
                        style={{ background: `${accentColor}12`, border: `1px solid ${accentColor}25` }}>
                        <Lock className="w-8 h-8" style={{ color: accentColor }} />
                    </div>
                    <h2 className="text-2xl font-black tracking-tight" style={{ color: '#EDF2F7' }}>
                        {roleContext === 'admin'
                            ? 'Admin Portal'
                            : isLogin ? 'Applicant Login' : 'Create Account'}
                    </h2>
                    <p className="text-sm mt-2" style={{ color: '#8892A4' }}>
                        {roleContext === 'admin'
                            ? 'Sign in with your admin credentials.'
                            : isLogin
                                ? 'Sign in to access your risk profile.'
                                : 'Register a new applicant account.'}
                    </p>
                </div>

                {/* Alerts */}
                <AnimatePresence mode="wait">
                    {error && (
                        <motion.div key="e" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mb-4 overflow-hidden">
                            <div className="p-3 rounded-xl flex items-start gap-2 text-xs font-semibold"
                                style={{ background: 'rgba(248,113,113,0.08)', color: '#F87171', border: '1px solid rgba(248,113,113,0.2)' }}>
                                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                                <span>{error}</span>
                            </div>
                        </motion.div>
                    )}
                    {success && (
                        <motion.div key="s" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mb-4 overflow-hidden">
                            <div className="p-3 rounded-xl flex items-center gap-2 text-xs font-semibold"
                                style={{ background: 'rgba(0,229,160,0.08)', color: '#00E5A0', border: '1px solid rgba(0,229,160,0.2)' }}>
                                <CheckCircle className="w-4 h-4 shrink-0" />
                                <span>{success}</span>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Name field (registration only) */}
                    <AnimatePresence>
                        {!isLogin && (
                            <motion.div key="name-field" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                                <label className="block text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: '#4B5563' }}>Full Name</label>
                                <div className="relative">
                                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#8892A4' }} />
                                    <input
                                        type="text"
                                        value={name}
                                        onChange={e => setName(e.target.value)}
                                        disabled={loading}
                                        placeholder="e.g. Rajesh Kumar"
                                        className="input-dark w-full"
                                        style={{ paddingLeft: '40px' }}
                                    />
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Email */}
                    <div>
                        <label className="block text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: '#4B5563' }}>Email Address</label>
                        <div className="relative">
                            <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#8892A4' }} />
                            <input
                                type="email"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                disabled={loading}
                                placeholder={roleContext === 'admin' ? 'admin@finaccess.com' : 'applicant@example.com'}
                                className="input-dark w-full"
                                style={{ paddingLeft: '40px' }}
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div>
                        <label className="block text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: '#4B5563' }}>Password</label>
                        <div className="relative">
                            <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#8892A4' }} />
                            <input
                                type="password"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                disabled={loading}
                                placeholder="Min. 6 characters"
                                className="input-dark w-full"
                                style={{ paddingLeft: '40px' }}
                            />
                        </div>
                    </div>

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="btn-primary w-full mt-4 disabled:opacity-60 disabled:cursor-wait flex items-center justify-center gap-2"
                        style={{ background: btnGrad, boxShadow: `0 0 24px ${accentColor}30` }}
                    >
                        {loading
                            ? <><Loader2 className="w-4 h-4 animate-spin" /> {isLogin ? 'Signing in…' : 'Creating account…'}</>
                            : <>{isLogin ? 'Sign In' : 'Create Account'} <ChevronRight className="w-4 h-4" /></>
                        }
                    </button>
                </form>

                {/* Toggle Login / Register (applicant only) */}
                {roleContext === 'applicant' && (
                    <div className="mt-6 text-center border-t pt-5" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                        <p className="text-sm" style={{ color: '#8892A4' }}>
                            {isLogin ? "New to FinAccess?" : "Already have an account?"}
                            <button
                                onClick={toggleMode}
                                disabled={loading}
                                className="ml-2 font-bold hover:underline transition-colors"
                                style={{ color: accentColor }}
                            >
                                {isLogin ? 'Create an account' : 'Sign in instead'}
                            </button>
                        </p>
                    </div>
                )}

                {/* Backend hint */}
                <div className="mt-4 p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <p className="text-[10px] text-center font-mono" style={{ color: '#4B5563' }}>
                        Secured via <span style={{ color: '#8892A4' }}>JWT HS256</span> · Data persisted in <span style={{ color: '#8892A4' }}>SQLite</span> · Backend: <span style={{ color: accentColor }}>localhost:8000</span>
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
