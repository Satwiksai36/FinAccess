import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Cpu, Brain, Network, BarChart2, Scale, ShieldCheck, ChevronRight, ArrowRight, Linkedin, Instagram, Phone } from 'lucide-react';

const FUp = ({ children, delay = 0, className = '' }: any) => (
    <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-50px" }}
        transition={{ duration: 0.8, delay, ease: [0.22, 1, 0.36, 1] }} className={className}>
        {children}
    </motion.div>
);

const StaggerText = ({ text, delayOffset = 0, color = 'inherit', className = '' }: any) => {
    const words = text.split(" ");
    return (
        <span className={`inline-block ${className}`} style={{ color }}>
            {words.map((word: string, i: number) => (
                <motion.span key={i} className="inline-block mr-[0.28em]"
                    initial={{ opacity: 0, y: 20, filter: 'blur(8px)' }}
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    transition={{ duration: 0.8, delay: delayOffset + i * 0.08, ease: [0.22, 1, 0.36, 1] }}>
                    {word}
                </motion.span>
            ))}
        </span>
    );
};

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

const features = [
    { icon: Cpu, color: '#00E5A0', label: 'Concurrent Inference', desc: 'ThreadPoolExecutor async FastAPI — 125+ RPS at <45ms P95 under 100 concurrent requests.' },
    { icon: Brain, color: '#4F7CFF', label: 'Multi-Modal ML Fusion', desc: 'XGBoost tabular + Transformer temporal + GCN graph embeddings via Attention MLP.' },
    { icon: ShieldCheck, color: '#00E5A0', label: 'Explainable AI (XAI)', desc: 'SHAP values, Captum Integrated Gradients, and GNN node attribution per prediction.' },
    { icon: Scale, color: '#4F7CFF', label: 'Fairness & Bias Audit', desc: 'Disparate Impact Ratios across gender, income, and region — Four-Fifths Rule enforcement.' },
    { icon: Network, color: '#00E5A0', label: 'Graph Neural Network', desc: 'PyTorch Geometric GCN maps applicant similarity graphs for community risk diffusion.' },
    { icon: BarChart2, color: '#4F7CFF', label: 'Live System Telemetry', desc: 'Real-time RPS, latency P95, and concurrency benchmark dashboard for ops teams.' },
];

const stats = [
    { v: '125+', l: 'Req / Second' },
    { v: '42ms', l: 'P95 Latency' },
    { v: '3-Model', l: 'ML Fusion' },
    { v: '98.1%', l: 'Confidence' },
];

export default function Landing({ onNavigate }: any) {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start start", "end start"] });
    const yBg = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
    const opacityBg = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

    return (
        <div ref={containerRef} className="flex-1 flex flex-col relative overflow-hidden" style={{ background: '#06080F' }}>
            {/* ── BACKGROUND ANIMATIONS ── */}
            <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
                <motion.div style={{ y: yBg, opacity: opacityBg, willChange: 'transform, opacity' }} className="absolute inset-0 flex justify-center">
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
                        className="absolute top-[-20%] w-[1200px] h-[800px] opacity-20"
                        style={{ background: 'radial-gradient(ellipse, rgba(0,229,160,0.15) 0%, rgba(79,124,255,0.1) 40%, transparent 70%)', willChange: 'transform' }} />
                    <div className="absolute inset-0 bg-grid hero-noise" style={{ opacity: 0.6 }} />
                </motion.div>
            </div>

            {/* ── HERO ── */}
            <section className="relative pt-24 pb-16 flex flex-col items-center justify-center px-6 text-center z-10 w-full">

                <div className="relative z-10 max-w-5xl mx-auto">
                    <FUp>
                        <div className="badge badge-primary mx-auto mb-8 w-fit">Enterprise Release · 2026</div>
                    </FUp>

                    <FUp delay={0.1}>
                        <h1 className="text-5xl sm:text-6xl lg:text-[76px] font-black leading-[1.05] tracking-[-0.02em] mb-6 drop-shadow-2xl">
                            <StaggerText text="Financial Inclusion" color="#EDF2F7" /><br />
                            <StaggerText text="Intelligence System" className="text-glow-primary" color="#00E5A0" delayOffset={0.2} />
                        </h1>
                    </FUp>

                    <FUp delay={0.2}>
                        <p className="text-lg max-w-2xl mx-auto mb-10 leading-relaxed font-medium" style={{ color: '#8892A4' }}>
                            A production-grade multi-modal deep learning platform combining <span style={{ color: '#EDF2F7' }}>XGBoost</span>, <span style={{ color: '#EDF2F7' }}>Transformer Encoder</span>, and <span style={{ color: '#EDF2F7' }}>PyTorch Geometric GCN</span> with Explainable AI, Fairness Auditing.
                        </p>
                    </FUp>

                    <FUp delay={0.3} className="flex flex-wrap items-center justify-center gap-4 mb-16">
                        <button className="btn-primary" onClick={() => onNavigate('applicant')}>
                            Applicant Portal <ChevronRight className="w-4 h-4 ml-2" />
                        </button>
                        <button className="btn-outline" onClick={() => onNavigate('admin')}>
                            Admin Intelligence
                        </button>
                    </FUp>

                    {/* Stats */}
                    <FUp delay={0.45}>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-2xl mx-auto">
                            {stats.map(s => (
                                <div key={s.l} className="rounded-2xl py-5 px-4 text-center"
                                    style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                                    <div className="text-3xl font-black mb-1" style={{ color: '#00E5A0' }}>{s.v}</div>
                                    <div className="text-[11px] font-bold uppercase tracking-wider" style={{ color: '#4B5563' }}>{s.l}</div>
                                </div>
                            ))}
                        </div>
                    </FUp>
                </div>
            </section>

            {/* ── FEATURES ── */}
            <section className="py-16 px-6" style={{ background: '#06080F' }}>
                <div className="max-w-6xl mx-auto">
                    <FUp className="text-center mb-12">
                        <div className="badge badge-blue mx-auto mb-4 w-fit">System Architecture</div>
                        <h2 className="text-4xl font-extrabold tracking-tight mb-4" style={{ color: '#EDF2F7' }}>
                            Built for Production Scale
                        </h2>
                        <p className="text-lg max-w-xl mx-auto" style={{ color: '#8892A4' }}>
                            Every subsystem engineered for performance, transparency, and compliance.
                        </p>
                    </FUp>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                        {features.map((f, i) => (
                            <FUp key={f.label} delay={i * 0.07}>
                                <div className="card p-7 h-full group cursor-default">
                                    <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-5 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3"
                                        style={{ background: `${f.color}14`, border: `1px solid ${f.color}25`, boxShadow: `0 0 15px ${f.color}10` }}>
                                        <f.icon className="w-5 h-5" style={{ color: f.color }} />
                                    </div>
                                    <h3 className="text-sm font-bold mb-2 transition-colors group-hover:text-white" style={{ color: '#EDF2F7' }}>{f.label}</h3>
                                    <p className="text-sm leading-relaxed" style={{ color: '#8892A4' }}>{f.desc}</p>
                                </div>
                            </FUp>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── FOOTER ── */}
            <footer className="mt-auto pt-16 pb-12 px-6 relative" style={{ background: '#06080F', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-12 lg:gap-8">
                    {/* Brand Col */}
                    <div className="lg:col-span-4 max-w-sm">
                        <div className="flex items-center mb-4 gap-3">
                            <LogoIcon />
                            <h2 className="text-3xl font-black tracking-[-0.03em] leading-none text-glow-primary" style={{ color: '#00E5A0' }}>
                                FinAccess
                            </h2>
                        </div>
                        <p className="mt-6 mb-4 font-medium" style={{ color: '#8892A4' }}>
                            Enterprise intelligence systems engineered to scale.
                        </p>
                        <p className="font-bold text-sm tracking-widest uppercase" style={{ color: '#4B5563' }}>
                            Model. Predict. Deploy.
                        </p>
                    </div>

                    {/* Links Cols */}
                    <div className="lg:col-span-2 lg:col-start-6">
                        <h4 className="font-bold mb-6 text-sm" style={{ color: '#EDF2F7' }}>Capabilities</h4>
                        <ul className="space-y-4 text-sm font-medium" style={{ color: '#8892A4' }}>
                            <li><button onClick={() => onNavigate('applicant')} className="hover:text-white transition-colors">Risk Inference</button></li>
                            <li><button onClick={() => onNavigate('admin')} className="hover:text-white transition-colors">Fairness Auditing</button></li>
                            <li>
                                <button onClick={() => onNavigate('admin')} className="hover:text-white transition-colors flex items-center gap-2">
                                    Graph Networks
                                    <div className="w-2 h-2 rounded-full" style={{ background: '#00E5A0', boxShadow: '0 0 8px #00E5A0' }}></div>
                                </button>
                            </li>
                            <li><button onClick={() => onNavigate('admin')} className="hover:text-white transition-colors">Concurrency Engine</button></li>
                        </ul>
                    </div>

                    <div className="lg:col-span-2">
                        <h4 className="font-bold mb-6 text-sm" style={{ color: '#EDF2F7' }}>System</h4>
                        <ul className="space-y-4 text-sm font-medium" style={{ color: '#8892A4' }}>
                            <li><button className="hover:text-white transition-colors">Architecture</button></li>
                            <li><button className="hover:text-white transition-colors">Benchmarks</button></li>
                            <li><button className="hover:text-white transition-colors">API Docs</button></li>
                            <li><button className="hover:text-white transition-colors">Privacy Policy</button></li>
                            <li><button className="hover:text-white transition-colors">Terms of Service</button></li>
                        </ul>
                    </div>

                    <div className="lg:col-span-3 lg:col-start-10">
                        <h4 className="font-bold mb-6 text-sm" style={{ color: '#EDF2F7' }}>Get In Touch</h4>
                        <div className="space-y-4 text-sm font-medium">
                            <a href="mailto:support@finaccess.system" className="hover:text-white transition-colors block" style={{ color: '#EDF2F7' }}>
                                support@finaccess.system
                            </a>
                            <a href="#" className="hover:text-white transition-colors block border-b w-fit pb-1" style={{ color: '#8892A4', borderColor: 'rgba(255,255,255,0.2)' }}>
                                Book a Platform Demo
                            </a>
                            <div className="flex gap-3 pt-3">
                                {[Linkedin, Instagram, Phone].map((Icon, idx) => (
                                    <button key={idx} className="w-10 h-10 flex items-center justify-center rounded-lg transition-all hover:bg-white/10"
                                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                                        <Icon className="w-4 h-4" style={{ color: '#8892A4' }} />
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}
