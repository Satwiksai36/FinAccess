<div align="center">
  <img src="frontend/public/logo.svg" alt="FinAccess Logo" width="120" />
  <h1>FinAccess — Scalable Financial Inclusion Intelligence</h1>
  <p><strong>A high-performance AI underwriting system designed to evaluate loan applicants fairly, transparently, and securely at scale.</strong></p>
</div>

<br />

![App Preview](https://github.com/Satwiksai36/FinAccess/assets/placeholder)<!-- Update this link later with a real screenshot! -->

## 🚀 Overview

FinAccess is a complete hardware-accelerated, enterprise-grade loan evaluation platform designed for hackathons and production environments alike. Instead of relying on a single black-box algorithm, FinAccess uses a **Multi-Modal AI Fusion Pipeline** to generate a comprehensive, transparent risk profile.

Designed for extreme concurrency, the backend isolates heavy Machine Learning computations from the asynchronous web event loop using dedicated **ThreadPoolExecutors**. The React frontend provides a stunning, premium UI with real-time telemetry, fairness compliance tracking, and dynamic visualizations.

## 🧠 The Machine Learning Pipeline

Our ML architecture analyzes applicants from three distinct mathematical perspectives and ensembles them using a meta-learner:

1. **Tabular Risk Modeling (XGBoost + SHAP XAI)**
   - **How it works:** Handles core financial data (Income, Loan Amount, Credit History).
   - **Why it's special:** We integrated **SHAP (SHapley Additive exPlanations)**. The UI doesn't just say "Approved"—it renders a real-time bar chart showing exactly *which* features increased or decreased the risk score (e.g., "Credit History reduced risk by 32%"). 

2. **Feature-Group Attention (BiLSTM via PyTorch)**
   - **How it works:** We adapted a Bidirectional LSTM to process the applicant's data across distinct logical feature groups (Demographics → Income → Risk Indicators).
   - **Why it's special:** By applying an Attention Mechanism, our UI visualizes exactly which "phase" of the applicant's profile the neural network focused on the most when deriving its sub-score.

3. **Community Risk Mapping (Graph Neural Networks / GraphSAGE)**
   - **How it works:** We synthesize the applicant into a mathematical "Graph" where edges represent feature similarities.
   - **Why it's special:** It calculates "Community Risk." If an applicant's financial DNA closely matches a cluster of past low-risk individuals, the GCN lowers their risk score natively.

4. **The Sigmoid Fusion Layer**
   - All three model sub-scores are fed into a final meta-learner that outputs the ultimate, calibrated Risk Score and Confidence metric.

## ⚖️ Fairness & Compliance

AI bias in banking is a massive real-world problem. FinAccess tackles this head-on with live **Disparate Impact Monitoring**:
- The backend automatically tracks approval rates grouped by demographics (Gender, Property Area).
- It calculates the **Four-Fifths (4/5ths) Rule** in real-time. If one group's approval rate drops below 80% of the highest-approving group, the Admin Dashboard immediately flags a compliance violation.

## ✨ Key Features

### For the Applicant
- **Multi-Modal AI Fusion:** Evaluates risk using Tabular data (XGBoost), Temporal/Sequence approximations (BiLSTM), and Community graph mappings (GCN).
- **Explainable AI (XAI):** Real-time **SHAP** feature attribution shows exactly *why* a decision was made.
- **Micro-Animations:** A sleek, glass-morphic interface built with Framer Motion and modern TailwindCSS.

### For the Admin
- **System Telemetry:** Live monitoring of active threads, request volume, and average ML latency via real-time WebSocket/Polling.
- **Fairness & Compliance:** Built-in **Disparate Impact (4/5ths Rule)** monitoring. Automatically groups historical predictions by demographics (Gender, Property Area) to ensure unbiased AI models.
- **Concurrency Benchmarks:** Built to scale seamlessly. Includes Locust load testing to validate asynchronous ThreadPool architecture.

---

## 🛠️ Tech Stack

### Frontend
- **React 18** + **TypeScript** (Vite)
- **Tailwind CSS** (for glass-morphic, custom HSL enterprise designs)
- **Framer Motion** (for smooth page transitions and micro-animations)
- **Recharts** (for complex SHAP and Attention Weight visualizations)
- **Lucide React** (icons)

### Backend
- **FastAPI** (lightning-fast async Python web framework)
- **SQLAlchemy & SQLite** (ephemeral demo mode, fully scalable to PostgreSQL)
- **XGBoost & SHAP** (Core Tabular AI & explainability)
- **PyTorch** (Deep Learning fusion layers)
- **Locust** (for intense load/stress testing)

---

## 🚦 Getting Started

### One-Click Launch (Windows)
We've included custom batch scripts to make running both the frontend and backend completely frictionless.

1. Clone the repository
2. Double-click **`start.bat`** in the root folder.
3. The script will automatically install all Python and Node dependencies, and start both the Backend (Port 8000) and Frontend (Port 5173).

> **Note on Errors:** If you experience an error where `Port 8000` is already in use, or you are missing PyTorch/ML packages, double-click the **`fix_errors.bat`** script. It will kill zombie ports and install exactly what you need.

### Manual Launch

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python server.py
# Running on http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Running on http://localhost:5173
```

---

## 🔐 Demo Accounts
The SQLite database automatically seeds these accounts on every startup:
- **Admin Portal:** `admin@finaccess.com` / `admin123`
- **Applicant Portal:** `applicant@finaccess.com` / `pass1234`
*(Note: The UI is currently configured to auto-login silently, so you don't even need to type these!)*

---

## 📁 Repository Structure

```text
FinAccess/
├── backend/                   # FastAPI Python Server
│   ├── app/                   # Core application (auth, db, schemas)
│   ├── ml/                    # AI Models (XGBoost, SHAP, GCN, BiLSTM)
│   ├── load_testing/          # Locust scripts & baseline CSVs
│   ├── server.py              # Zero-config Standalone SQLite server
│   └── requirements.txt       # Python dependencies
│
├── frontend/                  # React Vite Web App
│   ├── src/components/        # Dashboard, Landing Page, Auth
│   ├── src/api.ts             # API client & auto-login logic
│   ├── src/index.css          # Core design system & glassmorphism
│   └── package.json           # Node dependencies
│
├── docs/                      # Architecture & Model documentation
├── start.bat                  # One-click dual-launcher
└── fix_errors.bat             # Maintenance utility
```

---

*Built for Hackathons. Designed for Production.*
