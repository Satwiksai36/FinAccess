"""
mock_server.py — FinAccess Lightweight Demo Backend
====================================================
Runs WITHOUT Docker, Redis, or PostgreSQL.
Uses the real ML predictor if artifacts are available,
otherwise falls back to synthetic predictions.

Usage:
    pip install fastapi uvicorn
    python mock_server.py
"""

import json
import time
import random
import math
import hashlib
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import os
import sys

app = FastAPI(title="FinAccess Mock/Demo Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Metrics state ─────────────────────────────────────────────────────────────
class _Metrics:
    total_requests = 0
    cache_hits = 0
    cache_misses = 0
    latencies: List[float] = []
    ml_latencies: List[float] = []
    active_threads = 4

    def add_latency(self, ms: float):
        self.latencies.append(ms)
        if len(self.latencies) > 1000:
            self.latencies.pop(0)

    def add_ml_latency(self, ms: float):
        self.ml_latencies.append(ms)
        if len(self.ml_latencies) > 1000:
            self.ml_latencies.pop(0)

    def p95(self, arr):
        if not arr:
            return 0.0
        s = sorted(arr)
        idx = max(0, int(0.95 * len(s)) - 1)
        return round(s[idx], 2)

metrics = _Metrics()

# ── In-memory user store (no DB needed) ──────────────────────────────────────
import hashlib as _h
users: Dict[str, dict] = {}

# Pre-seed admin account so demo works instantly
def _hash(pw: str) -> str:
    return _h.sha256(pw.encode()).hexdigest()

users["admin@finaccess.com"] = {"id": 1, "email": "admin@finaccess.com", "hashed_password": _hash("admin123"), "role": "ADMIN"}
users["applicant@finaccess.com"] = {"id": 2, "email": "applicant@finaccess.com", "hashed_password": _hash("pass1234"), "role": "APPLICANT"}

# ── Try loading real ML predictor ─────────────────────────────────────────────
real_predictor = None
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from ml.predictor import FinAccessPredictor
    real_predictor = FinAccessPredictor()
    print("✅ Real ML predictor loaded.")
except Exception as e:
    print(f"⚠️  Real predictor unavailable ({e}). Using synthetic predictions.")

# ── Synthetic prediction engine ───────────────────────────────────────────────
def _synthetic_predict(data: dict) -> dict:
    """Generate deterministic-ish synthetic risk predictions."""
    seed_str = f"{data.get('ApplicantIncome', 5000)}{data.get('LoanAmount', 128)}{data.get('Credit_History', 1)}{data.get('Gender', 'Male')}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    income = float(data.get("ApplicantIncome", 5000) or 5000)
    co_income = float(data.get("CoapplicantIncome", 0) or 0)
    loan = float(data.get("LoanAmount", 128) or 128)
    term = float(data.get("Loan_Amount_Term", 360) or 360)
    credit = str(data.get("Credit_History", "1")).strip()
    married = str(data.get("Married", "Yes")).strip()
    education = str(data.get("Education", "Graduate")).strip()
    property_area = str(data.get("Property_Area", "Urban")).strip()
    dependents = str(data.get("Dependents", "0")).strip()

    # Risk heuristics
    total_income = income + co_income
    emi = loan / max(term, 1)
    dti = (emi * 1000) / max(total_income, 1)

    base_risk = 0.5
    if credit in ("1", "1.0"):  base_risk -= 0.25
    if credit in ("0", "0.0"):  base_risk += 0.25
    if total_income > 8000:     base_risk -= 0.10
    if total_income < 3000:     base_risk += 0.12
    if married == "Yes":        base_risk -= 0.05
    if education == "Graduate": base_risk -= 0.07
    if property_area == "Urban":       base_risk -= 0.04
    if property_area == "Rural":       base_risk += 0.06
    if dependents in ("3", "3+"):      base_risk += 0.08
    if dti > 0.4:               base_risk += 0.10
    if loan > 300:              base_risk += 0.08

    noise = (rng.random() - 0.5) * 0.06
    risk_score = max(0.02, min(0.97, base_risk + noise))

    tabular = max(0.01, min(0.99, risk_score + (rng.random() - 0.5) * 0.08))
    temporal = max(0.01, min(0.99, risk_score + (rng.random() - 0.5) * 0.06))
    graph    = tabular * 0.9 + temporal * 0.1

    threshold = 0.5
    decision = "APPROVED" if risk_score < threshold else "REJECTED"
    risk_label = "HIGH" if risk_score > 0.7 else "MEDIUM" if risk_score > 0.4 else "LOW"

    top_features = [
        {"feature": "Credit_History",    "shap_value": round(-0.35 if credit == "1" else 0.38, 4), "direction": "decreases_risk" if credit == "1" else "increases_risk"},
        {"feature": "Total_Income",      "shap_value": round(-0.01 * (total_income / 5000 - 1), 4), "direction": "decreases_risk" if total_income > 5000 else "increases_risk"},
        {"feature": "LoanAmount",        "shap_value": round(0.00008 * (loan - 128), 4), "direction": "increases_risk" if loan > 128 else "decreases_risk"},
        {"feature": "DTI_Ratio",         "shap_value": round(dti * 0.3, 4), "direction": "increases_risk" if dti > 0.2 else "decreases_risk"},
        {"feature": "Property_Area",     "shap_value": round(-0.04 if property_area == "Urban" else 0.06, 4), "direction": "decreases_risk" if property_area == "Urban" else "increases_risk"},
    ]

    attention_weights = {
        "Demographics":   round(0.18 + rng.random() * 0.06, 4),
        "Income":         round(0.28 + rng.random() * 0.08, 4),
        "Loan Details":   round(0.32 + rng.random() * 0.07, 4),
        "Risk Indicators":round(0.22 + rng.random() * 0.05, 4),
    }

    top_feat = top_features[0]
    direction_text = "increases" if top_feat["direction"] == "increases_risk" else "decreases"
    summary = (
        f"The most influential factor is '{top_feat['feature']}' which {direction_text} "
        f"the risk score (SHAP={top_feat['shap_value']:+.3f}). "
        f"The temporal model focused most on '{max(attention_weights, key=attention_weights.get)}'."
    )

    return {
        "risk_score":    round(risk_score, 4),
        "risk_label":    risk_label,
        "decision":      decision,
        "model_scores":  {"tabular": round(tabular, 4), "temporal": round(temporal, 4), "graph": round(graph, 4)},
        "top_features":  top_features,
        "attention_weights": attention_weights,
        "explanation_summary": summary,
    }

# ── JWT mock (simple base64 tokens — no secret needed for demo) ──────────────
import base64

def _make_token(email: str, role: str) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"email": email, "role": role}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.demo_sig"

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "uptime_seconds": int(time.time() % 100000)}

@app.get("/readiness")
async def readiness():
    return {
        "database":           "connected",
        "redis":              "connected",
        "model":              "loaded" if real_predictor else "mock",
        "thread_pool_workers": 8,
    }

@app.get("/metrics")
async def get_metrics():
    lats = metrics.latencies
    ml_lats = metrics.ml_latencies
    avg = lambda arr: round(sum(arr) / len(arr), 2) if arr else 0.0
    return {
        "total_requests":       metrics.total_requests,
        "average_latency_ms":   avg(lats),
        "p95_latency_ms":       metrics.p95(lats),
        "average_ml_latency_ms": avg(ml_lats),
        "p95_ml_latency_ms":    metrics.p95(ml_lats),
        "cache_hits":           metrics.cache_hits,
        "cache_misses":         metrics.cache_misses,
        "active_threads":       metrics.active_threads,
    }

# ── Auth ──────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "APPLICANT"

class LoginForm(BaseModel):
    username: str
    password: str

from fastapi import Form

@app.post("/auth/register", status_code=201)
async def register(body: RegisterRequest):
    if body.email in users:
        from fastapi import HTTPException
        raise HTTPException(400, "The user with this email already exists in the system.")
    uid = len(users) + 1
    users[body.email] = {
        "id": uid,
        "email": body.email,
        "hashed_password": _hash(body.password),
        "role": body.role,
    }
    return {"id": uid, "email": body.email, "role": body.role, "created_at": "2026-01-01T00:00:00Z"}

@app.post("/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    from fastapi import HTTPException
    user = users.get(username)
    if not user or user["hashed_password"] != _hash(password):
        raise HTTPException(401, "Incorrect email or password")
    token = _make_token(user["email"], user["role"])
    return {"access_token": token, "token_type": "bearer"}

# ── Predict ───────────────────────────────────────────────────────────────────
@app.post("/predict/{applicant_id}")
async def predict(applicant_id: int, request: Request):
    t0 = time.perf_counter()
    metrics.total_requests += 1

    body_data = {}
    try:
        body_data = await request.json()
    except Exception:
        pass

    # Simulate slight processing delay for realism
    time.sleep(random.uniform(0.04, 0.12))

    if real_predictor:
        try:
            prediction = real_predictor.predict(body_data)
            explanation = real_predictor.explain(body_data)
            result = {**prediction, **explanation, "explanation_summary": explanation.get("explanation_summary", "")}
        except Exception as e:
            print(f"Real predictor error: {e}. Falling back to synthetic.")
            result = _synthetic_predict(body_data)
    else:
        result = _synthetic_predict(body_data)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    metrics.add_latency(elapsed_ms)
    metrics.add_ml_latency(elapsed_ms)
    metrics.cache_misses += 1

    decision_str = result.get("decision", "UNKNOWN")
    risk_score = result.get("risk_score", 0.5)
    model_scores = result.get("model_scores", {"tabular": 0.5, "temporal": 0.5, "graph": 0.5})

    return {
        "applicant_id":       applicant_id,
        "risk_score":         risk_score,
        "risk_label":         result.get("risk_label", "MEDIUM"),
        "decision":           decision_str,
        "model_scores":       model_scores,
        "top_features":       result.get("top_features", []),
        "attention_weights":  result.get("attention_weights", {}),
        "summary":            result.get("explanation_summary", ""),
        "inference_time_ms":  round(elapsed_ms, 2),
    }

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 FinAccess Mock Backend starting...")
    print("   URL:     http://localhost:8000")
    print("   Docs:    http://localhost:8000/docs")
    print("   Health:  http://localhost:8000/health")
    print("\n📋 Pre-seeded demo accounts:")
    print("   Admin:     admin@finaccess.com     / admin123")
    print("   Applicant: applicant@finaccess.com / pass1234\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
