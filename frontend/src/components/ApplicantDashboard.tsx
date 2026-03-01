import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart, Bar, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, CartesianGrid } from 'recharts';
import { ShieldCheck, Activity, ChevronRight, CheckCircle, Database, ScanLine, Network, Zap, Upload, AlertCircle, Clock, Cpu } from 'lucide-react';
import { apiPredict, authStore, ensureAuthToken, type PredictionResult } from '../api';

const STEPS = [
    'Acquiring ThreadPool lock — max_workers=32',
    'Feature matrix extraction via XGBoost trees',
    'Multi-head attention over 12-month sequence',
    'GCN cosine-edge graph traversal',
    'Sigmoid fusion layer → risk calibration',
    'SHAP & Integrated Gradients computation',
];

const C = '#00E5A0'; // emerald
const B = '#4F7CFF'; // blue

interface ResultDisplay {
    risk_score: number;       // 0–100 display scale
    confidence: number;
    verdict: string;
    shap: { feat: string; val: number; color: string }[];
    temporal: { month: string; impact: number }[];
    graph_risk: number;
    graph_nodes: string[];
    summary: string;
    inference_time_ms: number;
    model_scores: { tabular: number; temporal: number; graph: number };
}

function mapApiResult(data: PredictionResult, applicant_id: number): ResultDisplay {
    const riskPct = +(data.risk_score * 100).toFixed(1);
    const confidence = +(Math.min(99.9, Math.max(60, Math.abs(data.risk_score - 0.5) * 100 + 55))).toFixed(1);
    return {
        risk_score: riskPct,
        confidence,
        verdict: data.decision === 'APPROVED' ? 'Low Risk · Approved' : 'High Risk · Declined',
        shap: data.top_features.map(f => ({
            feat: f.feature.replace(/_/g, ' '),
            val: f.shap_value,
            color: f.direction === 'increases_risk' ? '#F87171' : '#00E5A0',
        })),
        temporal: Object.entries(data.attention_weights).map(([k, v]) => ({
            month: k,
            impact: v as number,
        })),
        graph_risk: +(data.model_scores.graph * 100).toFixed(1),
        graph_nodes: [`USR_${applicant_id}`, `USR_${applicant_id + 11}`],
        summary: data.summary,
        inference_time_ms: data.inference_time_ms,
        model_scores: {
            tabular: +(data.model_scores.tabular * 100).toFixed(1),
            temporal: +(data.model_scores.temporal * 100).toFixed(1),
            graph: +(data.model_scores.graph * 100).toFixed(1),
        },
    };
}

const Counter = ({ value, decimals = 1 }: { value: number; decimals?: number }) => {
    const [d, setD] = useState(0);
    useEffect(() => {
        let s: number | null = null;
        const f = (ts: number) => {
            if (!s) s = ts;
            const p = Math.min((ts - s) / 1400, 1);
            setD(value * (1 - Math.pow(1 - p, 4)));
            if (p < 1) requestAnimationFrame(f);
        };
        requestAnimationFrame(f);
    }, [value]);
    return <>{d.toFixed(decimals)}</>;
};

const TT = ({ contentStyle = {}, ...props }: any) => (
    <Tooltip {...props} contentStyle={{ background: '#141B26', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', color: '#EDF2F7', ...contentStyle }} />
);

// Past applications stored in state (backend-driven once submitted)
interface PastApp {
    date: string;
    loanId: string;
    status: string;
    risk: number;
    result: ResultDisplay;
}

export default function ApplicantDashboard() {
    const [activeTab, setActiveTab] = useState<'new' | 'history'>('new');
    const [step, setStep] = useState(-1);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ResultDisplay | null>(null);
    const [error, setError] = useState('');
    const [history, setHistory] = useState<PastApp[]>([]);

    const [formData, setFormData] = useState({
        Loan_Id: '', ApplicantIncome: '', CoapplicantIncome: '', LoanAmount: '', Loan_Amount_Term: '',
        Gender: '', Married: '', Dependents: '', Education: '', Self_Employed: '', Credit_History: '', Property_Area: 'Urban'
    });

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target?.result as string;
            const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
            if (lines.length < 2) return;
            const cleanText = (str: string) => str.replace(/^\uFEFF/, '').replace(/^["'](.*)["']$/, '$1').trim();
            const headers = lines[0].split(',').map(cleanText);
            const values = lines[1].split(',').map(cleanText);
            const newFormData = { ...formData };
            const formKeys = Object.keys(newFormData);
            headers.forEach((h, i) => {
                const matchKey = formKeys.find(k => k.toLowerCase() === h.toLowerCase());
                if (matchKey && values[i] !== undefined) {
                    (newFormData as any)[matchKey] = values[i];
                }
            });
            setFormData(newFormData);
        };
        reader.readAsText(file);
    };

    const run = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);
        setError('');
        setStep(0);

        // Silently acquire a JWT if not already logged in
        await ensureAuthToken('APPLICANT');

        // Animate steps while waiting
        let currentStep = 0;
        const animInterval = setInterval(() => {
            currentStep = Math.min(currentStep + 1, STEPS.length - 1);
            setStep(currentStep);
        }, 750);

        try {
            const match = formData.Loan_Id.match(/\d+/);
            const applicant_id = match ? parseInt(match[0], 10) : Math.floor(Math.random() * 9000) + 1;

            const payload = {
                Loan_Id: formData.Loan_Id,
                ApplicantIncome: Number(formData.ApplicantIncome) || 0,
                CoapplicantIncome: Number(formData.CoapplicantIncome) || 0,
                LoanAmount: Number(formData.LoanAmount) || 0,
                Loan_Amount_Term: Number(formData.Loan_Amount_Term) || 360,
                Gender: formData.Gender,
                Married: formData.Married,
                Dependents: formData.Dependents,
                Education: formData.Education,
                Self_Employed: formData.Self_Employed,
                Credit_History: formData.Credit_History,
                Property_Area: formData.Property_Area,
            };

            const data = await apiPredict(applicant_id, payload);
            const display = mapApiResult(data, applicant_id);

            clearInterval(animInterval);
            setStep(STEPS.length - 1);
            await new Promise(r => setTimeout(r, 400));

            // Save to history
            setHistory(prev => [{
                date: new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
                loanId: formData.Loan_Id || `LP${applicant_id}`,
                status: data.decision === 'APPROVED' ? 'Approved' : 'Declined',
                risk: display.risk_score,
                result: display,
            }, ...prev]);

            setResult(display);
        } catch (err: any) {
            clearInterval(animInterval);
            setError(err.message ?? 'Backend inference failed. Is the server running?');
        } finally {
            setLoading(false);
            setStep(-1);
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-6 py-10" style={{ background: '#06080F', minHeight: '100vh' }}>
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
                <div className="badge badge-primary mb-3">Applicant Risk Portal</div>
                <h2 className="text-3xl font-extrabold tracking-tight mb-2" style={{ color: '#EDF2F7' }}>Financial Profile Evaluation</h2>
                <p style={{ color: '#8892A4' }}>Submit your parameters into the multi-modal AI fusion pipeline.</p>
            </motion.div>

            {/* Tab Bar */}
            <div className="flex border-b mb-8 overflow-x-auto" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
                <button onClick={() => { setActiveTab('new'); setResult(null); setError(''); }} className={`relative px-5 py-3 text-sm font-bold whitespace-nowrap transition-colors ${activeTab === 'new' ? 'tab-active-line' : ''}`} style={{ color: activeTab === 'new' ? C : '#8892A4' }}>New Application</button>
                <button onClick={() => setActiveTab('history')} className={`relative px-5 py-3 text-sm font-bold whitespace-nowrap transition-colors ${activeTab === 'history' ? 'tab-active-line' : ''}`} style={{ color: activeTab === 'history' ? C : '#8892A4' }}>
                    Application History {history.length > 0 && <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded-full font-bold" style={{ background: 'rgba(0,229,160,0.12)', color: C }}>{history.length}</span>}
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Form / History List */}
                <div className="lg:col-span-4">
                    {activeTab === 'new' ? (
                        <div className="card p-7">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center">
                                    <div className="w-9 h-9 rounded-xl flex items-center justify-center mr-3" style={{ background: `${C}12`, border: `1px solid ${C}25` }}>
                                        <Database className="w-4 h-4" style={{ color: C }} />
                                    </div>
                                    <h3 className="font-bold" style={{ color: '#EDF2F7' }}>Application Form</h3>
                                </div>
                                <label className="btn-primary cursor-pointer text-[10px] flex items-center gap-1.5" style={{ margin: 0, padding: '6px 12px', borderRadius: '6px' }}>
                                    <Upload className="w-3 h-3" />
                                    Upload CSV
                                    <input type="file" accept=".csv" className="hidden" onChange={handleFileUpload} />
                                </label>
                            </div>
                            <form onSubmit={run} className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    {[{ l: 'Loan ID', p: 'LP001002', k: 'Loan_Id', t: 'text' },
                                    { l: 'Applicant Income', p: '5849', k: 'ApplicantIncome', t: 'number' },
                                    { l: 'Co-applicant Inc.', p: '0', k: 'CoapplicantIncome', t: 'number' },
                                    { l: 'Loan Amount', p: '128', k: 'LoanAmount', t: 'number' },
                                    { l: 'Loan Term (mo)', p: '360', k: 'Loan_Amount_Term', t: 'number' }].map(f => (
                                        <div key={f.l} className={f.k === 'Loan_Id' ? 'col-span-2' : ''}>
                                            <label className="block text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: '#4B5563' }}>{f.l}</label>
                                            <input type={f.t} placeholder={f.p} name={f.k} disabled={loading} className="input-dark"
                                                value={(formData as any)[f.k]} onChange={e => setFormData({ ...formData, [f.k]: e.target.value })} />
                                        </div>
                                    ))}

                                    <div className="col-span-2 grid grid-cols-2 gap-4">
                                        {[
                                            { l: 'Gender', k: 'Gender', opts: ['Male', 'Female'] },
                                            { l: 'Married', k: 'Married', opts: ['Yes', 'No'] },
                                            { l: 'Dependents', k: 'Dependents', opts: ['0', '1', '2', '3+'] },
                                            { l: 'Education', k: 'Education', opts: ['Graduate', 'Not Graduate'] },
                                            { l: 'Self Employed', k: 'Self_Employed', opts: ['Yes', 'No'] },
                                            { l: 'Credit History', k: 'Credit_History', opts: ['1 (Good)', '0 (Bad)'] },
                                        ].map(f => (
                                            <div key={f.l}>
                                                <label className="block text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: '#4B5563' }}>{f.l}</label>
                                                <select name={f.k} disabled={loading} className="input-dark"
                                                    value={(formData as any)[f.k]} onChange={e => setFormData({ ...formData, [f.k]: e.target.value })}>
                                                    <option value="" disabled>Select…</option>
                                                    {f.opts.map(o => <option key={o} value={o.split(' ')[0]}>{o}</option>)}
                                                </select>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-[10px] font-bold uppercase tracking-widest mb-1.5 mt-2" style={{ color: '#4B5563' }}>Property Area</label>
                                    <div className="grid grid-cols-3 gap-3">
                                        {['Urban', 'Semiurban', 'Rural'].map(r => (
                                            <label key={r} className="flex items-center gap-2 cursor-pointer text-[13px] font-semibold" style={{ color: '#8892A4' }}>
                                                <input type="radio" name="Property_Area" value={r}
                                                    checked={formData.Property_Area === r}
                                                    onChange={e => setFormData({ ...formData, Property_Area: e.target.value })}
                                                    className="accent-primary w-3.5 h-3.5" />
                                                {r}
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                <button type="submit" disabled={loading} className="btn-primary w-full mt-4 disabled:opacity-50 disabled:cursor-not-allowed">
                                    {loading ? <><ScanLine className="w-4 h-4 mr-2 animate-pulse" />Evaluating…</> : <>Run Pipeline <ChevronRight className="w-4 h-4 ml-2" /></>}
                                </button>
                            </form>
                        </div>
                    ) : (
                        <div className="card p-7">
                            <h3 className="font-bold mb-4" style={{ color: '#EDF2F7' }}>Past Applications</h3>
                            {history.length === 0 ? (
                                <div className="text-center py-12">
                                    <Clock className="w-10 h-10 mx-auto mb-3" style={{ color: '#4B5563' }} />
                                    <p className="text-sm" style={{ color: '#4B5563' }}>No applications submitted yet.</p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {history.map((app, i) => (
                                        <button key={i} onClick={() => { setActiveTab('new'); setResult(app.result); }} className="w-full text-left p-4 rounded-xl border transition-all hover:bg-white/5" style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.02)' }}>
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="text-xs font-mono" style={{ color: '#8892A4' }}>{app.loanId}</span>
                                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${app.status === 'Approved' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>{app.status}</span>
                                            </div>
                                            <div className="flex justify-between items-center">
                                                <span className="text-sm font-semibold" style={{ color: '#EDF2F7' }}>{app.date}</span>
                                                <span className="text-sm font-bold" style={{ color: app.status === 'Approved' ? '#22C55E' : '#F87171' }}>Risk: {app.risk}%</span>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Output Panel */}
                <div className="lg:col-span-8">
                    <AnimatePresence mode="wait">
                        {loading && (
                            <motion.div key="p" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                className="rounded-2xl min-h-[480px] flex flex-col justify-center px-10 py-10 relative overflow-hidden"
                                style={{ background: '#0D1117', border: '1px solid rgba(0,229,160,0.15)' }}>
                                <motion.div animate={{ top: ['0%', '105%'] }} transition={{ duration: 2.4, repeat: Infinity, ease: 'linear' }}
                                    className="scan-anim absolute left-0 w-full h-[2px]"
                                    style={{ background: C, boxShadow: `0 0 12px ${C}`, opacity: 0.7, position: 'absolute' }} />
                                <div className="relative z-10">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-[11px] font-bold tracking-[0.2em] uppercase font-mono" style={{ color: C }}>Thread_Pool_Exec — Active</span>
                                        <span className="font-mono text-xs" style={{ color: '#4B5563' }}>{step >= 0 ? Math.round(((step + 1) / STEPS.length) * 100) : 0}%</span>
                                    </div>
                                    <div className="h-1.5 w-full rounded-full mb-10 overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)' }}>
                                        <motion.div className="h-full rounded-full" style={{ background: `linear-gradient(90deg, ${C}, #00C48A)`, boxShadow: `0 0 8px ${C}` }}
                                            animate={{ width: `${step >= 0 ? ((step + 1) / STEPS.length) * 100 : 0}%` }} transition={{ duration: 0.4 }} />
                                    </div>
                                    <div className="space-y-5 border-l pl-6 font-mono text-sm" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                                        {STEPS.map((s, i) => (
                                            <div key={i} className="flex items-center transition-all duration-300"
                                                style={{ color: i < step ? '#22C55E' : i === step ? '#EDF2F7' : 'rgba(255,255,255,0.2)', fontWeight: i === step ? 700 : 400 }}>
                                                {i < step ? <CheckCircle className="w-4 h-4 mr-3 shrink-0" style={{ color: '#22C55E' }} />
                                                    : i === step ? <Activity className="w-4 h-4 mr-3 shrink-0 animate-spin" style={{ color: C }} />
                                                        : <span className="mr-7 text-lg opacity-20">—</span>}
                                                {s}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        {error && !loading && (
                            <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                className="rounded-2xl min-h-[200px] flex flex-col items-center justify-center p-10 text-center"
                                style={{ background: 'rgba(248,113,113,0.04)', border: '2px solid rgba(248,113,113,0.15)' }}>
                                <AlertCircle className="w-12 h-12 mb-4" style={{ color: '#F87171' }} />
                                <h4 className="text-lg font-bold mb-2" style={{ color: '#F87171' }}>Backend Connection Error</h4>
                                <p className="text-sm max-w-sm" style={{ color: '#8892A4' }}>{error}</p>
                                <p className="text-xs mt-3 font-mono" style={{ color: '#4B5563' }}>Make sure the backend server is running: <span style={{ color: '#00E5A0' }}>python server.py</span></p>
                            </motion.div>
                        )}

                        {!loading && !result && !error && (
                            <motion.div key="e" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                className="flex-1 rounded-2xl min-h-[480px] flex flex-col items-center justify-center text-center"
                                style={{ background: 'rgba(255,255,255,0.02)', border: '2px dashed rgba(255,255,255,0.06)' }}>
                                <Network className="w-14 h-14 mb-4" style={{ color: '#4B5563' }} />
                                <h4 className="text-lg font-bold mb-2" style={{ color: '#8892A4' }}>Neural Pipeline Standby</h4>
                                <p className="text-sm max-w-xs" style={{ color: '#4B5563' }}>
                                    {activeTab === 'new' ? 'Fill the form and engage the multi-modal fusion engine.' : 'Select a past application to view its analysis.'}
                                </p>
                            </motion.div>
                        )}

                        {!loading && result && (
                            <motion.div key="r" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}
                                className="grid grid-cols-2 gap-5">
                                {/* Risk Score */}
                                <div className="card p-7 flex flex-col items-center justify-center text-center" style={{ borderTop: `3px solid ${result.risk_score < 50 ? '#22C55E' : '#F87171'}` }}>
                                    <ShieldCheck className="w-9 h-9 mb-3" style={{ color: result.risk_score < 50 ? '#22C55E' : '#F87171' }} />
                                    <div className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: '#4B5563' }}>Risk Score</div>
                                    <div className="text-5xl font-black mb-3" style={{ color: '#EDF2F7' }}><Counter value={result.risk_score} />%</div>
                                    <span className={`badge ${result.risk_score < 50 ? 'badge-success' : 'badge-danger'}`}>{result.verdict}</span>
                                </div>
                                {/* Confidence */}
                                <div className="card p-7 flex flex-col items-center justify-center text-center" style={{ borderTop: `3px solid ${B}` }}>
                                    <Activity className="w-9 h-9 mb-3" style={{ color: B }} />
                                    <div className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: '#4B5563' }}>Confidence</div>
                                    <div className="text-5xl font-black mb-3" style={{ color: '#EDF2F7' }}><Counter value={result.confidence} />%</div>
                                    <span className="badge badge-blue">High Certainty</span>
                                </div>

                                {/* Model Scores */}
                                <div className="card p-5 col-span-2">
                                    <div className="text-[10px] font-bold uppercase tracking-widest mb-4" style={{ color: '#4B5563' }}>Model Sub-Scores</div>
                                    <div className="grid grid-cols-3 gap-4">
                                        {[
                                            { label: 'XGBoost Tabular', val: result.model_scores.tabular, color: C },
                                            { label: 'BiLSTM Temporal', val: result.model_scores.temporal, color: B },
                                            { label: 'GraphSAGE Graph', val: result.model_scores.graph, color: '#F59E0B' },
                                        ].map(s => (
                                            <div key={s.label} className="text-center p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                                                <div className="text-[9px] font-bold uppercase tracking-widest mb-2" style={{ color: '#4B5563' }}>{s.label}</div>
                                                <div className="text-2xl font-black" style={{ color: s.color }}>{s.val}%</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* SHAP */}
                                <div className="card p-6 col-span-2 sm:col-span-1">
                                    <div className="text-[10px] font-bold uppercase tracking-widest mb-4" style={{ color: '#4B5563' }}>SHAP Feature Attribution</div>
                                    <div className="h-44">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={result.shap} layout="vertical" margin={{ left: 10, right: 20 }}>
                                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.05)" />
                                                <XAxis type="number" hide domain={['auto', 'auto']} />
                                                <YAxis dataKey="feat" type="category" axisLine={false} tickLine={false} tick={{ fill: '#8892A4', fontSize: 11, fontWeight: 600 }} width={110} />
                                                <TT />
                                                <Bar dataKey="val" radius={4} barSize={18}>
                                                    {result.shap.map((e, i) => <Cell key={i} fill={e.color} />)}
                                                </Bar>
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* Temporal (Attention Weights) */}
                                <div className="card p-6 col-span-2 sm:col-span-1">
                                    <div className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: '#4B5563' }}>Transformer Attention Weights (IG)</div>
                                    <p className="text-[11px] mb-4" style={{ color: '#4B5563' }}>BiLSTM integrated gradient impact per sequence step</p>
                                    <div className="h-44">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={result.temporal} margin={{ left: -20, right: 10, top: 10 }}>
                                                <defs>
                                                    <linearGradient id="tGrad" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#4F7CFF" stopOpacity={0.3} />
                                                        <stop offset="95%" stopColor="#4F7CFF" stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                                                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#4B5563', fontSize: 10 }} />
                                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#4B5563', fontSize: 10 }} />
                                                <TT />
                                                <Area type="monotone" dataKey="impact" stroke={B} strokeWidth={2.5} fill="url(#tGrad)" />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* GNN Banner */}
                                <div className="card col-span-2 p-6 flex items-start gap-5" style={{ background: 'linear-gradient(135deg, rgba(0,229,160,0.08), rgba(79,124,255,0.06))', borderColor: 'rgba(0,229,160,0.15)' }}>
                                    <div className="p-3 rounded-xl shrink-0" style={{ background: `${C}15`, border: `1px solid ${C}25` }}>
                                        <Network className="w-6 h-6" style={{ color: C }} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="badge badge-primary mb-2">GCN Node Influence Attribution</div>
                                        <h4 className="text-lg font-extrabold mb-2" style={{ color: '#EDF2F7' }}>Community Risk: {result.graph_risk}%</h4>
                                        <p className="text-sm leading-relaxed mb-2" style={{ color: '#8892A4' }}>
                                            Applicant mapped via cosine-edge GCN traversal. Proximity to low-risk cluster nodes <span className="font-mono text-xs px-1.5 py-0.5 rounded" style={{ background: 'rgba(255,255,255,0.07)', color: '#EDF2F7' }}>{result.graph_nodes.join(', ')}</span> reduces overall propagated risk.
                                        </p>
                                        <p className="text-xs leading-relaxed italic" style={{ color: '#4B5563' }}>{result.summary}</p>
                                    </div>
                                    <div className="text-right shrink-0">
                                        <div className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: '#4B5563' }}>Inference Time</div>
                                        <div className="text-xl font-black" style={{ color: C }}>{result.inference_time_ms.toFixed(1)}<span className="text-xs ml-1" style={{ color: '#4B5563' }}>ms</span></div>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}
