# FinAccess - Scalable Financial Inclusion Intelligence System
## Architecture Diagram Description

### Overview
FinAccess is a high-performance, full-stack predictive system designed to assess applicant risk profiles securely and equitably. The platform merges traditional tabular analysis with advanced deep learning (temporal sequence parsing and graph-based relationships) in a multithreaded backend architecture.

### System Components

#### 1. Frontend Client (React + Tailwind + Vite)
- **Applicant Dashboard:** Secure form-based application input that displays the risk prediction, key SHAP bars, and similarity graphs upon submission.
- **Admin Dashboard:** Comprehensive dashboard equipped with fairness analytics, tabular applications, multithread benchmark visualizations, and API latencies.

#### 2. RESTful API Gateway (FastAPI)
- Serves as the high-throughput entry point utilizing native asynchronous processing.
- Handles Auth (JWT-based), routing of prediction requests, logging, and metrics aggregation.

#### 3. Concurrency ThreadPool Engine (Python `concurrent.futures.ThreadPoolExecutor`)
- The ML inference process relies on an optimized thread pool for evaluating CPU/GPU bound tabular, temporal, and GNN models simultaneously for concurrent requests.
- This layer directly feeds the multithreading benchmark endpoints showing performance gains under load (10, 50, 100 RPS).

#### 4. Fusion ML Engine
Comprises three specialized deep learning models that feed into a Fusion Layer:
- **Baseline Tabular Model**: XGBoost / LightGBM analyzing static financial indicators.
- **Behavioral Sequence Model**: Transformer Encoder capturing longitudinal financial stability and income drift.
- **Relational Graph Neural Network**: PyTorch Geometric GCN assessing applicant similarity networks based on income band, occupation, and region.
- **Fusion Meta-Learner**: Concatenates and projects multi-modal embeddings yielding final Risk Score and Confidence margins.

#### 5. Explainable AI & Fairness Module
- Intercepts Fusion ML features yielding SHAP & Permutation Importance for Tabular features.
- Applies Integrated Gradients to Temporal trajectories.
- Performs bias analyses identifying disparity per Gender, Rural/Urban distribution.

#### 6. Persistence & Caching
- **PostgreSQL**: Stores applicant data, system benchmark metrics, fairness snapshots, and application history.
- **Redis (Optional)**: Results caching for frequent lookups or repeated scoring attempts.

### Data Flow Diagram (Text Description)
`[User Browser]` -> (HTTPS) -> `[FastAPI Async Endpoint]` -> `[ThreadPool ML Orchestrator]`
 `[ThreadPool ML Orchestrator]` -> `[XGBoost]` & `[Transformer]` & `[GCN]` -> `[Fusion Layer MLP]` -> `[Prediction + Confidence]`
 `[ThreadPool ML Orchestrator]` -> `[XAI Extractors]` -> `[SHAP / Integrated Gradients]`
 `[FastAPI Response]` -> (JSON) -> `[React Client Dashboards]`
