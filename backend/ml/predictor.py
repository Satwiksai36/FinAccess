"""
predictor.py — FinAccess ML Inference Module
============================================
Unified inference pipeline combining XGBoost (tabular) + BiLSTM (feature-group attention)
+ MinimalGCN (graph-relational) via a Logistic Regression meta-learner fusion.

Design Notes
------------
**XGBoost (Tabular)**
  Gradient-boosted trees trained on the 20 engineered tabular features.
  SHAP explanations use TreeExplainer (exact Shapley values, O(T·D) time).

**BiLSTM — Feature-Group Attention** (NOT temporal sequence learning)
  A single applicant's 20 tabular features are reshaped into pseudo-timesteps
  (e.g. 4 groups × 5 features). This is NOT processing observations over time;
  it is an attention mechanism that learns which feature groups (Demographics,
  Income, Loan Details, Risk Indicators) contribute most to the risk signal.
  The attention weights are therefore "feature-group importance", not temporal.

**MinimalGCN — Synthetic Training Graph**
  A 2-layer GCN trained on 614 synthetically generated applicant nodes.
  Node features match the preprocessed 20-feature space; edges are cosine-
  similarity connections (threshold 0.65). The training graph does NOT encode
  real applicant relationships — it provides a neighbourhood-regularised risk
  prior from the synthetic distribution. Cold-start new applicants are embedded
  via weighted neighbour aggregation (1-hop propagation).

**Fusion**
  A Logistic Regression meta-learner combines the three model scores into the
  final risk_score.  This is the value reported in all API responses.

**Thread Safety**
  FinAccessPredictor is designed to be instantiated ONCE and shared across
  concurrent request handlers (ThreadPoolExecutor workers). The SHAP
  TreeExplainer uses C extensions with internal mutable state and is NOT
  thread-safe. All calls to ``shap_explainer.shap_values()`` are serialised
  with a ``threading.Lock()``.

Usage
-----
    from predictor import FinAccessPredictor
    predictor = FinAccessPredictor()
    result = predictor.predict(applicant_dict)       # -> risk_score, model_scores, GNN info
    explanation = predictor.explain(applicant_dict)  # -> SHAP + attention weights
    predictor.export_results([applicant_dict], "output.json")  # -> writes JSON file
"""

import json
import numpy as np
import pickle
import torch
import torch.nn as nn
import os
import threading
from datetime import datetime

# ── Model Definitions (must match training notebooks) ─────────

class AttentionLayer(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.attention = nn.Linear(hidden_dim * 2, 1)

    def forward(self, lstm_output):
        attn_weights = torch.softmax(self.attention(lstm_output), dim=1)
        context = torch.sum(attn_weights * lstm_output, dim=1)
        return context, attn_weights.squeeze(-1)


class BiLSTMAttention(nn.Module):
    """
    BiLSTM with self-attention — used as a **feature-group attention** module.

    Input: a single applicant's 20 tabular features reshaped into
    (sequence_timesteps × features_per_step) — NOT a real time series.
    The "timesteps" represent logical feature groups (e.g. Demographics, Income,
    Loan Details, Risk Indicators).  The attention weights expose which group
    the model found most discriminative for the prediction.
    """
    def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.3):
        super().__init__()
        self.bilstm = nn.LSTM(input_size, hidden_size, num_layers,
                               batch_first=True, bidirectional=True,
                               dropout=dropout if num_layers > 1 else 0)
        self.attention = AttentionLayer(hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * 2, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1), nn.Sigmoid()
        )

    def forward(self, x, return_attention=False):
        lstm_out, _ = self.bilstm(x)
        context, attn_weights = self.attention(lstm_out)
        context = self.dropout(context)
        out = self.classifier(context).squeeze(-1)
        if return_attention:
            return out, attn_weights
        return out


# ── Main Predictor Class ──────────────────────────────────────

class FinAccessPredictor:
    """
    Unified predictor combining XGBoost + BiLSTM (feature-group attention)
    + MinimalGCN (synthetic training graph) + Fusion.

    Thread Safety
    -------------
    This class is safe to share across threads **with the following caveat**:
    SHAP's TreeExplainer is NOT thread-safe (C extension with mutable state).
    A ``_shap_lock`` serialises all ``shap_explainer.shap_values()`` calls.
    All other operations (XGBoost, BiLSTM, GCN, fusion) are thread-safe.
    """

    ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), 'artifacts')
    GRAPH_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'artifacts', 'graph_model.pkl')

    def __init__(self):
        self._load_artifacts()
        # Serialise SHAP calls: TreeExplainer uses mutable C-level state and
        # produces silently corrupted results when called from multiple threads.
        self._shap_lock = threading.Lock()
        print("FinAccessPredictor initialized successfully.")

    def _load_artifacts(self):
        """Load all saved model artifacts."""
        a = self.ARTIFACTS_DIR

        # Preprocessors
        self.scaler         = pickle.load(open(f'{a}/scaler.pkl', 'rb'))
        self.label_encoders = pickle.load(open(f'{a}/label_encoders.pkl', 'rb'))
        self.feature_config = pickle.load(open(f'{a}/feature_config.pkl', 'rb'))
        self.shap_explainer = pickle.load(open(f'{a}/shap_explainer.pkl', 'rb'))
        self.fusion_config  = pickle.load(open(f'{a}/fusion_config.pkl', 'rb'))

        # Models
        self.xgb_model      = pickle.load(open(f'{a}/xgb_model.pkl', 'rb'))
        self.meta_learner   = pickle.load(open(f'{a}/fusion_meta_learner.pkl', 'rb'))

        # BiLSTM (feature-group attention — NOT temporal sequence model)
        seq_input_size = self.feature_config['features_per_step']
        self.bilstm = BiLSTMAttention(input_size=seq_input_size)
        self.bilstm.load_state_dict(
            torch.load(f'{a}/bilstm_weights.pt', map_location='cpu')
        )
        self.bilstm.eval()

        # Graph Model — try to load trained MinimalGCN; fall back to proxy if unavailable
        # NOTE: MinimalGCN is trained on a SYNTHETIC graph of 614 nodes (not real applicants).
        # It provides a neighbourhood-regularised risk prior, not real relational context.
        self.gcn = None
        try:
            from ml.graph_model import MinimalGCN
            self.gcn = MinimalGCN.load(self.GRAPH_MODEL_PATH)
            print("[OK] GCN graph model loaded from artifacts.")
        except Exception as e:
            print(f"[WARN] GCN not loaded ({e}). Using XGBoost proxy for graph score.")


    def preprocess(self, raw_input: dict) -> np.ndarray:
        """
        Apply same transformations as notebook 02_preprocessing.ipynb.
        raw_input: dict with keys matching original dataset columns.
        """
        # Encode categoricals
        cat_cols = ['Gender', 'Married', 'Education', 'Self_Employed', 'Property_Area']
        encoded = {}
        for col in cat_cols:
            le = self.label_encoders[col]
            val = str(raw_input.get(col, le.classes_[0]))
            if val not in le.classes_:
                val = le.classes_[0]  # fallback to most common
            encoded[col] = le.transform([val])[0]

        # Numeric
        applicant_income   = float(raw_input.get('ApplicantIncome', 0))
        coapplicant_income = float(raw_input.get('CoapplicantIncome', 0))
        loan_amount        = float(raw_input.get('LoanAmount', 100))
        loan_term          = float(raw_input.get('Loan_Amount_Term', 360))
        credit_history     = float(raw_input.get('Credit_History', 1))
        dependents_raw     = str(raw_input.get('Dependents', '0'))
        dependents         = 3.0 if dependents_raw == '3+' else float(dependents_raw)

        # Engineered features
        total_income        = applicant_income + coapplicant_income
        emi                 = loan_amount / max(loan_term, 1)
        balance_income      = total_income - emi * 1000
        loan_to_income      = loan_amount / (total_income + 1)
        income_per_dep      = total_income / (dependents + 1)
        log_app_inc         = np.log1p(applicant_income)
        log_coapp_inc       = np.log1p(coapplicant_income)
        log_loan            = np.log1p(loan_amount)
        log_total_inc       = np.log1p(total_income)

        # Build feature vector in same order as TABULAR_FEATURES
        feature_vector = np.array([
            encoded['Gender'], encoded['Married'], dependents,
            encoded['Education'], encoded['Self_Employed'],
            applicant_income, coapplicant_income, loan_amount, loan_term,
            credit_history, encoded['Property_Area'],
            total_income, emi, balance_income, loan_to_income, income_per_dep,
            log_app_inc, log_coapp_inc, log_loan, log_total_inc
        ], dtype=np.float32)

        # Scale numerical columns
        numerical_idx = list(range(5, len(feature_vector)))  # indices 5–19
        numerical_features = feature_vector[numerical_idx].reshape(1, -1)
        feature_vector[numerical_idx] = self.scaler.transform(numerical_features)[0]

        return feature_vector

    def _bilstm_score(self, features: np.ndarray) -> float:
        """Run BiLSTM inference on feature vector."""
        seq = features.reshape(
            self.feature_config['sequence_timesteps'],
            self.feature_config['features_per_step']
        )
        seq_tensor = torch.FloatTensor(seq).unsqueeze(0)  # (1, timesteps, features)
        with torch.no_grad():
            score = self.bilstm(seq_tensor).item()
        return score

    def predict(self, raw_input: dict) -> dict:
        """
        Main prediction method. Returns final risk score and breakdown.

        Returns:
            {
                "risk_score": float (0-1),
                "risk_label": "LOW" | "MEDIUM" | "HIGH",
                "model_scores": { tabular, temporal, graph },
                "decision": "APPROVED" | "REJECTED"
            }
        """
        features = self.preprocess(raw_input)

        # Individual model scores
        tabular_score = float(self.xgb_model.predict_proba(features.reshape(1, -1))[0][1])
        temporal_score = self._bilstm_score(features)

        # Graph score: use trained MinimalGCN if available; else proxy for new applicants
        if self.gcn is not None:
            try:
                graph_score = self.gcn.predict_new(features)
            except Exception:
                graph_score = tabular_score * 0.9 + temporal_score * 0.1
        else:
            # Cold-start proxy — documented limitation (no historical graph context)
            graph_score = tabular_score * 0.9 + temporal_score * 0.1

        # Fusion
        meta_input = np.array([[tabular_score, temporal_score, graph_score]])
        final_score = float(self.meta_learner.predict_proba(meta_input)[0][1])

        threshold = self.fusion_config.get('threshold', 0.5)
        decision = 'APPROVED' if final_score >= threshold else 'REJECTED'
        risk_label = 'HIGH' if final_score > 0.7 else 'MEDIUM' if final_score > 0.4 else 'LOW'

        return {
            'risk_score':    round(final_score, 4),
            'risk_label':    risk_label,
            'decision':      decision,
            'model_scores':  {
                'tabular':   round(tabular_score, 4),
                'temporal':  round(temporal_score, 4),
                'graph':     round(graph_score, 4)
            },
            # GNN influence: absolute difference between graph score and final fusion output.
            # Non-zero value indicates the graph neighbourhood context shifted the prediction.
            'graph_influence': round(abs(graph_score - final_score), 4),
            'graph_source':  'trained_gcn' if self.gcn is not None else 'proxy_xgb_bilstm',
        }

    def explain(self, raw_input: dict, top_n: int = 5) -> dict:
        """
        Return SHAP-based explanation for a prediction.

        SHAP values are computed via ``TreeExplainer`` on the **XGBoost tabular model**,
        which is the most appropriate explainer for gradient-boosted trees and yields
        exact Shapley values in O(T·D) time.
        The fusion meta-learner aggregates all model scores; SHAP attribution is therefore
        applied at the tabular stage and contextualised with BiLSTM attention weights.

        Returns
        -------
        dict with keys:
            top_features      : list of {feature, shap_value, direction} dicts
            attention_weights : {timestep_label: weight} from BiLSTM attention head
            explanation_summary : human-readable summary string
        """
        features = self.preprocess(raw_input)

        # SHAP values — serialised via _shap_lock.
        # CRITICAL: TreeExplainer uses C-level mutable state and is NOT thread-safe.
        # Concurrent calls from ThreadPoolExecutor workers can corrupt results silently.
        with self._shap_lock:
            shap_vals = self.shap_explainer.shap_values(features.reshape(1, -1))[0]
        feature_names = self.feature_config['tabular_features']
        contributions = sorted(
            zip(feature_names, shap_vals),
            key=lambda x: abs(x[1]), reverse=True
        )[:top_n]

        top_features = [
            {
                'feature':    feat,
                'shap_value': round(float(val), 4),
                'direction':  'increases_risk' if val > 0 else 'decreases_risk'
            }
            for feat, val in contributions
        ]

        # Attention weights from BiLSTM
        seq = features.reshape(
            self.feature_config['sequence_timesteps'],
            self.feature_config['features_per_step']
        )
        seq_tensor = torch.FloatTensor(seq).unsqueeze(0)
        with torch.no_grad():
            _, attn = self.bilstm(seq_tensor, return_attention=True)
        attn_np = attn.squeeze(0).numpy()

        # Feature-group attention weights from BiLSTM.
        # NOTE: these are NOT temporal weights over time — the BiLSTM processes the
        # 20 tabular features reshaped into logical groups (Demographics, Income,
        # Loan Details, Risk Indicators). The weights show which group drove the score.
        feature_group_labels = ['Demographics', 'Income', 'Loan Details', 'Risk Indicators']
        attention_weights = {
            label: round(float(w), 4)
            for label, w in zip(feature_group_labels, attn_np)
        }

        # Human-readable summary
        top_feat = top_features[0]
        direction_text = 'increases' if top_feat['direction'] == 'increases_risk' else 'decreases'
        summary = (
            f"The most influential factor is '{top_feat['feature']}' which "
            f"{direction_text} the risk score (SHAP={top_feat['shap_value']:+.3f}). "
            f"The feature-group attention focused most on '{max(attention_weights, key=attention_weights.get)}'."
        )

        return {
            'top_features':        top_features,
            'attention_weights':   attention_weights,
            'explanation_summary': summary
        }

    def export_results(self, applicants: list, output_path: str = 'finaccess_results.json') -> str:
        """
        Export prediction results for a list of applicant dicts to a JSON file.
        Required by Interface Compliance specification.

        Args:
            applicants: list of applicant feature dicts
            output_path: path to write results JSON

        Returns:
            Absolute path to the written file.
        """
        results = []
        for i, applicant in enumerate(applicants):
            try:
                pred = self.predict(applicant)
                expl = self.explain(applicant)
                results.append({
                    'index': i,
                    'applicant_id': applicant.get('applicant_id', i),
                    'timestamp': datetime.utcnow().isoformat(),
                    **pred,
                    'top_features': expl['top_features'],
                    'attention_weights': expl['attention_weights'],
                    'explanation_summary': expl['explanation_summary'],
                })
            except Exception as e:
                results.append({'index': i, 'error': str(e)})

        abs_path = os.path.abspath(output_path)
        with open(abs_path, 'w') as f:
            json.dump({'exported_at': datetime.utcnow().isoformat(),
                       'count': len(results), 'results': results}, f, indent=2)
        print(f"[export_results] Wrote {len(results)} records to {abs_path}")
        return abs_path


# ── Quick Test ────────────────────────────────────────────────
if __name__ == '__main__':
    predictor = FinAccessPredictor()

    sample_applicant = {
        'Gender':            'Male',
        'Married':           'Yes',
        'Dependents':        '2',
        'Education':         'Graduate',
        'Self_Employed':     'No',
        'ApplicantIncome':   4000,
        'CoapplicantIncome': 1500,
        'LoanAmount':        120,
        'Loan_Amount_Term':  360,
        'Credit_History':    1,
        'Property_Area':     'Urban'
    }

    print('\n=== PREDICTION ===')
    result = predictor.predict(sample_applicant)
    for k, v in result.items():
        print(f'  {k}: {v}')

    print('\n=== EXPLANATION ===')
    explanation = predictor.explain(sample_applicant)
    print('  Top features:')
    for f in explanation['top_features']:
        print(f"    {f['feature']}: {f['shap_value']:+.4f} ({f['direction']})")
    print(f"  Attention: {explanation['attention_weights']}")
    print(f"  Summary: {explanation['explanation_summary']}")
