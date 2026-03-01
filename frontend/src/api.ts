/**
 * api.ts — Centralized API service layer for FinAccess frontend
 * All backend calls go through here.
 */

const BASE = 'http://localhost:8000';

// ── Auth token management ────────────────────────────────────────
export const authStore = {
    token: localStorage.getItem('finaccess_token') ?? '',
    role: localStorage.getItem('finaccess_role') ?? '',
    setToken(token: string, role: string) {
        this.token = token;
        this.role = role;
        localStorage.setItem('finaccess_token', token);
        localStorage.setItem('finaccess_role', role);
    },
    clear() {
        this.token = '';
        this.role = '';
        localStorage.removeItem('finaccess_token');
        localStorage.removeItem('finaccess_role');
    },
    isLoggedIn() {
        return !!this.token;
    }
};

// ── Base fetch helper ────────────────────────────────────────────
async function apiFetch(path: string, options: RequestInit = {}) {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string> ?? {}),
    };
    if (authStore.token) {
        headers['Authorization'] = `Bearer ${authStore.token}`;
    }
    const res = await fetch(`${BASE}${path}`, { ...options, headers });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? 'API Error');
    }
    return res.json();
}

// ── Auth API ─────────────────────────────────────────────────────
export interface RegisterPayload { email: string; password: string; role: 'APPLICANT' | 'ADMIN' }
export interface LoginPayload { email: string; password: string }

export async function apiRegister(payload: RegisterPayload) {
    return apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(payload) });
}

/** Login uses form-urlencoded format required by OAuth2PasswordRequestForm */
export async function apiLogin(payload: LoginPayload) {
    const form = new URLSearchParams();
    form.append('username', payload.email);
    form.append('password', payload.password);
    const res = await fetch(`${BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString(),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? 'Login failed');
    }
    const data = await res.json();
    return data as { access_token: string; token_type: string };
}

// ── Demo credentials (seeded by server.py on every startup) ───────
const DEMO_APPLICANT = { email: 'applicant@finaccess.com', password: 'pass1234' };
const DEMO_ADMIN = { email: 'admin@finaccess.com', password: 'admin123' };

/** Singleton promise — prevents concurrent auto-login races on mount */
let _authPromise: Promise<void> | null = null;

/**
 * Ensures a valid JWT token is stored before any protected API call.
 * 
 * If an unexpired token already exists in localStorage it is reused.
 * Otherwise it silently logs in with the seeded demo account so dashboards
 * work without the user ever seeing a login page.
 * 
 * @param role - 'APPLICANT' (default) or 'ADMIN' determines which demo account is used.
 */
export async function ensureAuthToken(role: 'APPLICANT' | 'ADMIN' = 'APPLICANT'): Promise<void> {
    if (authStore.isLoggedIn()) return;   // already have a token

    // Return existing in-flight promise to avoid parallel login races
    if (_authPromise) return _authPromise;

    _authPromise = (async () => {
        const creds = role === 'ADMIN' ? DEMO_ADMIN : DEMO_APPLICANT;
        try {
            // Try login first (account already exists on subsequent page visits)
            const data = await apiLogin(creds);
            authStore.setToken(data.access_token, role);
        } catch {
            try {
                // Account may not exist yet on a fresh DB — register then login
                await apiRegister({ ...creds, role });
                const data = await apiLogin(creds);
                authStore.setToken(data.access_token, role);
            } catch (err) {
                // Non-fatal: protected endpoints will return 401 and show error UI
                console.warn('[FinAccess] Auto-login failed:', err);
            }
        }
        _authPromise = null;
    })();

    return _authPromise;
}

// ── Prediction API ───────────────────────────────────────────────
export interface PredictPayload {
    Loan_Id?: string;
    ApplicantIncome?: number | string;
    CoapplicantIncome?: number | string;
    LoanAmount?: number | string;
    Loan_Amount_Term?: number | string;
    Gender?: string;
    Married?: string;
    Dependents?: string;
    Education?: string;
    Self_Employed?: string;
    Credit_History?: string;
    Property_Area?: string;
}

export interface PredictionResult {
    applicant_id: number;
    risk_score: number;       // 0–1 float
    risk_label: string;       // LOW | MEDIUM | HIGH
    decision: string;         // APPROVED | REJECTED
    model_scores: { tabular: number; temporal: number; graph: number };
    top_features: { feature: string; shap_value: number; direction: string }[];
    attention_weights: Record<string, number>;
    summary: string;
    inference_time_ms: number;
}

export async function apiPredict(applicantId: number, payload: PredictPayload): Promise<PredictionResult> {
    return apiFetch(`/predict/${applicantId}`, { method: 'POST', body: JSON.stringify(payload) });
}

// ── System / Metrics API ─────────────────────────────────────────
export interface BackendMetrics {
    total_requests: number;
    average_latency_ms: number;
    p95_latency_ms: number;
    average_ml_latency_ms: number;
    p95_ml_latency_ms: number;
    cache_hits: number;
    cache_misses: number;
    active_threads: number;
}

export async function apiGetMetrics(): Promise<BackendMetrics> {
    return apiFetch('/metrics');
}

export async function apiHealth() {
    return apiFetch('/health');
}

export async function apiReadiness() {
    return apiFetch('/readiness');
}

// ── Fairness API ──────────────────────────────────────────────────
export interface FairnessGroup {
    group: string;
    approval_rate: number;
    disparate_impact_ratio: number;
    four_fifths_compliant: boolean;
}

export interface FairnessData {
    source: string;
    total_predictions?: number;
    overall_approval_rate?: number;
    by_property_area: FairnessGroup[];
    by_gender: FairnessGroup[];
    violations: string[];
    overall_compliant: boolean;
    four_fifths_rule: string;
}

export async function apiFairness(): Promise<FairnessData> {
    return apiFetch('/api/fairness');
}

// ── Benchmark Compare API ─────────────────────────────────────────
export async function apiBenchmarkCompare() {
    return apiFetch('/benchmark/compare');
}
