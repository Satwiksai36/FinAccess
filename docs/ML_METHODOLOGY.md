# ML & Explainability Methodology

## 1. Data Pipeline & Embedding Vectors

### Tabular Input Pipeline
- **Inputs**: Demographic info, static financial summary, credit pulls.
- **Encoding**: Ordinal/One-hot encoding for categoricals, StandardScaler for numericals.
- **Baseline**: XGBoost handles these sparse tabular interactions out-of-the-box.
- **Engineered Features**: EMI, Debt-to-Income ratio, log-transformed income, Balance Income.

### Behavioral Sequence Pipeline
- **Inputs**: Feature vector reshaped as 4-step time sequence (Demographics → Income → Loan Details → Risk Indicators).
- **Normalization**: Z-score normalized via StandardScaler applied before reshaping.
- **Network**: BiLSTM with custom Attention Layer. Bidirectional LSTM (hidden=64, layers=2) followed by attention-weighted pooling. Captures temporal risk patterns across financial feature groups.
- **Attention Output**: Per-timestep weights expose which feature group drove the decision (interpretable via `attention_weights` in API response).

### Graph Pipeline
- **Architecture**: Minimal Graph Convolutional Network (GCN) — 2-layer message passing on cosine-similarity adjacency matrix.
- **Node Construction**: Training applicants form graph nodes; edges built by cosine similarity of standardized feature vectors (threshold: 0.65).
- **Adjacency Normalization**: Symmetric normalization D^{-1/2} A D^{-1/2} per Kipf & Welling (2017).
- **Message Passing**: Z = A_hat @ tanh(A_hat @ X @ W1) @ W2, sigmoid output.
- **Inference (Cold-Start)**: New applicants are embedded via weighted neighbour aggregation — cosine similarity to all training nodes, weighted-average feature propagation, then forward through W1, W2. This is equivalent to 1-hop GCN propagation.
- **Implementation**: `backend/ml/graph_model.py` — no PyTorch Geometric required.

#### Graph Model Status
> The GCN is trained on the same 614-node feature space as XGBoost using synthetic node labels derived from the trained XGBoost ground truth. This is a pragmatic choice: the original dataset contains `applicant_id` but no explicit relational graph (no transaction edges or peer connections). The GCN captures *demographic similarity clustering* rather than financial contagion. A production deployment with actual loan repayment history could leverage true graph structure (e.g., shared employer, geography, guarantor relationships).

---

## 2. Model Fusion Engine
The three model scores are fused by a meta-learner:
- `tabular_score (XGBoost)` + `temporal_score (BiLSTM)` + `graph_score (GCN)` → meta-input vector
- A 2-layer MLP (meta-learner) translates this into a final risk probability via Sigmoid.
- Fusion weights are learned during training on a held-out validation set.

---

## 3. Explainable AI (XAI)
To make predictions actionable and auditable:
- **SHAP (Shapley Additive Explanations)**: Computed over tabular features using a TreeExplainer for XGBoost. Returns exact positive/negative risk contributions per feature.
- **Attention Weights (BiLSTM)**: Per-timestep attention weights expose which feature group (Demographics, Income, Loan Details, Risk Indicators) dominated the BiLSTM decision.
- **GNN Node Influence**: The GCN prediction reflects neighbourhood risk — if similar applicants in the training graph have high default rates, the graph score rises accordingly.

---

## 4. Fairness Engineering
Disparate Impact Ratio Analysis is implemented post-prediction:
- System monitors acceptance rates across `Gender` (Male/Female) and `Property_Area` (Urban/Semiurban/Rural).
- The `GET /api/fairness` endpoint computes live approval rates from the predictions database and emits a warning if the standard 80% Rule (Four-Fifths rule) is broken.
- **4/5 Rule**: If `approval_rate(group) / approval_rate(highest_group) < 0.80`, the group is flagged as a potential disparate impact violation.
