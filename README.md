# AutoQ – Automotive Quality Intelligence System

> **Final-Year B.Tech Computer Science & Engineering Major Project (2025–2026)**  
> *An AI-Powered, Software-Only Enterprise Platform for Manufacturing Defect Prediction, Root-Cause Attribution, and Quality Analytics.*

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite_3-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS_v4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 1. Project Overview

In high-volume automotive component manufacturing, machining deviations in safety-critical parts (such as engine cylinder liners, transmission gears, steering knuckles, and brake rotors) can result in catastrophic field failures, expensive warranty recalls, and serious safety liability.

**AutoQ** is an enterprise-grade, software-only Quality Intelligence platform. It replaces manual inspection logbooks and disparate spreadsheets with real-time machine learning inference, automated failure-mode diagnosis, interactive visual analytics, and compliance-ready audit report generation.

### Key Capabilities:
- **Instantaneous Defect Classification**: Real-time evaluation of CNC machining telemetry (speed, torque, tool wear, thermal gradients) via a serialized Random Forest pipeline ($\text{ROC-AUC} = 0.9830$).
- **Root-Cause Attribution**: Automatic multi-class diagnosis of detected anomalies into 6 physical failure modes (Heat Dissipation, Power Deviations, Overstrain Fatigue, Tool Wear Limits, Process Anomalies, and Compound Multi-Mode Failures).
- **Safety-Critical Threshold Tuning**: Dynamic operational toggle between balanced screening ($\tau = 0.50$) and high-recall safety screening ($\tau = 0.35$), capturing up to $89.71\%$ of true defect events and reducing escapes by $22.2\%$.
- **Automated Audit Certificates**: Programmatic vector PDF and tabular CSV report generation using ReportLab for IATF 16949 audit compliance.
- **Strictly Software-Only**: Zero reliance on external microcontrollers, Arduino, Raspberry Pi, or OBD devices.

---

## 2. System Architecture

AutoQ employs a decoupled 3-tier enterprise architecture:

```
┌────────────────────────────────────────────────────────┐
│             Presentation Tier: React 19 Client         │
│  ├── Views: Overview, Inspections, Analytics, Reports  │
│  ├── Charting: Recharts SVG Visualizations             │
│  └── State & Networking: Centralized API Service Layer │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP / JSON REST API
                           ▼
┌────────────────────────────────────────────────────────┐
│             Application Tier: FastAPI Backend          │
│  ├── REST Routers: /api/inspections, /api/predictions, │
│  │                /api/analytics, /api/reports, /health│
│  ├── ML Inference Engine: Mapping, Scaling, Prediction │
│  ├── Document Rendering: ReportLab PDF/CSV Generator   │
│  └── Relational Logic: SQLAlchemy Service Layer        │
└────────────┬─────────────────────────────┬─────────────┘
             │                             │
             ▼                             ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│     Persistence Tier    │   │  Serialized ML Artifacts │
│   SQLite 3 (autoq.db)   │   │  Joblib Pipelines (v1.0) │
└─────────────────────────┘   └──────────────────────────┘
```

---

## 3. Technology Stack

| Layer | Component | Version | Technology Role |
| :--- | :--- | :--- | :--- |
| **Frontend** | React | 19.0.0 | Reactive component-based user interface |
| | Vite | 6.4.6 | Fast ES-module development and production bundling |
| | Tailwind CSS | 4.0.0 | Dark industrial design system |
| | Recharts | 2.15.1 | Declarative SVG charting for quality trends and KPIs |
| | Lucide React | 0.475.0 | Industrial vector iconography |
| **Backend** | FastAPI | 0.115.0+ | Asynchronous RESTful API framework |
| | Uvicorn | 0.30.0+ | High-performance ASGI production server |
| | SQLAlchemy | 2.0.35+ | ORM with enforced SQLite foreign keys |
| | SQLite 3 | 3.45.0+ | ACID-compliant transactional persistence (`autoq.db`) |
| | Pydantic | 2.9.0+ | Strict type validation and physical envelope bounds |
| | ReportLab | 4.2.0+ | Programmatic vector PDF compilation |
| **Machine Learning**| Scikit-learn | 1.5.0+ | Balanced Random Forest & Preprocessing pipelines |
| | NumPy & Pandas| 1.26 / 2.2 | Numerical arrays, matrix math, and CSV parsing |
| | Joblib | 1.4.0+ | Serialized model artifact management |

---

## 4. Machine Learning Methodology & Performance

### 4.1 Dataset Benchmark
The models were trained and verified on the **AI4I 2020 Predictive Maintenance Dataset** (UCI Machine Learning Repository / Matan et al.), comprising 10,000 industrial records reflecting an authentic **27.7:1 class imbalance** (96.52% conforming, 3.48% defective).

> *Academic Disclosure*: AI4I 2020 is a recognized manufacturing quality benchmark; it is not proprietary telemetry harvested from a live commercial automotive assembly line.

### 4.2 Verified Holdout Test Results (2,000 Test Records)

| Metric | Random Forest (Champion) | Gradient Boosting | Logistic Regression | Decision Tree |
| :--- | :--- | :--- | :--- | :--- |
| **Test ROC-AUC** | **0.9830** | 0.9638 | 0.9376 | 0.9259 |
| **Test PR-AUC (Average Precision)**| **0.8737** | 0.8614 | 0.5482 | 0.4912 |
| **Defect Recall ($\tau = 0.50$)** | **86.76%** (59/68) | 79.41% (54/68) | 89.71% (61/68) | 89.71% (61/68) |
| **Precision** | **67.05%** | 94.74% | 18.21% | 41.22% |
| **F1-Score** | **0.7564** | 0.8640 | 0.3027 | 0.5648 |
| **Test Defect Escapes (FN)** | **9 parts** | 14 parts | 7 parts | 7 parts |
| **Brier Score Loss** | **0.0158** | 0.0182 | 0.0410 | 0.0470 |

### 4.3 Configurable Decision Thresholds

| Metric | Balanced Default ($\tau = 0.50$) | High-Recall Safety ($\tau = 0.35$) |
| :--- | :--- | :--- |
| **Target Assembly Grade** | Standard non-critical brackets & covers | Safety-critical knuckles, calipers, gears |
| **Defect Recall** | **86.76%** (59/68 intercepted) | **89.71%** (61/68 intercepted) |
| **Defect Escapes (FN)** | **9 parts** | **7 parts** (22.2% reduction in escapes) |
| **Precision** | **67.05%** | **59.80%** |
| **False Positives (FP)** | **29 parts** | **41 parts** |

### 4.4 Top Feature Importances (Gini MDI)
1. Spindle Rotational Speed (`rotational_speed`): **20.35%**
2. Mechanical Power (`power_kw`): **19.48%**
3. Torsional Resistance (`torque`): **17.70%**
4. Tool Wear Duration (`tool_wear`): **14.32%**
5. Overstrain Fatigue Index (`overstrain_index`): **12.03%**
6. Thermal Gradient ($\Delta T$): **9.20%**

---

## 5. Project Directory Structure

```
AutoQ/
├── backend/
│   ├── app/
│   │   ├── api/routes/         # REST API endpoints (health, inspections, predictions, etc.)
│   │   ├── core/               # Configuration, security, and global exception handlers
│   │   ├── database/           # SQLAlchemy engine, session factory, connection hooks
│   │   ├── ml/                 # Feature mapping, inference engines, training pipelines
│   │   ├── models/             # SQLAlchemy ORM entity definitions
│   │   ├── schemas/            # Pydantic request/response validation schemas
│   │   └── services/           # Business logic service layer
│   ├── data/                   # Isolated evaluator demo datasets (demo_inspections.csv)
│   ├── datasets/               # Benchmark training & testing CSV partitions
│   ├── reports/                # Dynamically generated PDF and CSV audit documents
│   ├── trained_models/         # Serialized joblib pipelines and metadata manifests
│   ├── tests_phase4.py         # Database architecture test suite
│   ├── verify_phase6.py        # ML inference verification suite
│   ├── verify_phase7.py        # Full-stack integration test suite
│   └── verify_phase8.py        # Comprehensive audit & regression test suite
├── frontend/
│   ├── src/
│   │   ├── components/         # Reusable UI widgets and navigation cards
│   │   ├── layouts/            # Sidebar layout and topbar shells
│   │   ├── pages/              # Overview, Inspections, Prediction Studio, Analytics, Reports
│   │   └── services/           # Centralized HTTP API client
│   ├── package.json            # Node.js dependency definitions
│   └── vite.config.js          # Vite build configuration
├── docs/
│   ├── diagrams/               # Architecture diagrams (Mermaid & PNG renders)
│   ├── API_DOCUMENTATION.md    # Exhaustive REST API specification
│   ├── USER_MANUAL.md          # Evaluator step-by-step user manual
│   ├── DEMO_SCRIPT.md          # 8-10 minute live viva presentation script
│   ├── VIVA_QUESTIONS.md       # 50+ technical viva examination Q&As
│   ├── AutoQ_Final_Project_Report.md # Formal 28-section academic report
│   └── AutoQ_Final_Presentation.pptx # 20-slide widescreen presentation deck
└── README.md                   # Primary project documentation
```

---

## 6. Installation & Quick Start Guide (Windows PowerShell)

### Prerequisites:
- Python 3.10+ installed
- Node.js 18+ & npm installed

### 1. Setup Backend Virtual Environment
From the project root:
```powershell
# Create virtual environment (if not already present)
python -m venv backend\venv

# Activate virtual environment
.\backend\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 2. Start Backend Server
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend
```
- **Backend API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Health Probe**: `http://127.0.0.1:8000/api/health`

### 3. Setup & Start Frontend Client
In a separate PowerShell window:
```powershell
cd frontend
npm install
npm run dev
```
- **Frontend Web Application**: `http://localhost:5173`

---

## 7. Running Automated Test Suites

AutoQ includes automated verification suites covering **53 discrete test assertions**:

```powershell
# 1. Comprehensive System Audit & Full Regression Suite (16 Test Cases)
.\backend\venv\Scripts\python.exe backend/verify_phase8.py

# 2. Full-Stack REST API & Parity Verification (14 Test Cases)
.\backend\venv\Scripts\python.exe backend/verify_phase7.py

# 3. Machine Learning Inference & Multiclass Verification (8 Test Cases)
.\backend\venv\Scripts\python.exe backend/verify_phase6.py

# 4. Database Architecture & ORM Regression (15 Test Cases)
.\backend\venv\Scripts\python.exe backend/tests_phase4.py

# 5. Frontend Production Bundle Compilation
npm --prefix frontend run build
```

---

## 8. Academic Disclosures & System Limitations

1. **Benchmark Telemetry Scope**: Machine learning models were trained on the AI4I 2020 Predictive Maintenance Dataset. While physically realistic, performance has not been tested on active automotive assembly lines.
2. **Software-Only Boundary**: AutoQ is strictly software; it does not interface directly with physical microcontrollers, Arduino, Raspberry Pi, or OBD hardware.
3. **Correlation vs. Causation**: Feature importances indicate statistical associations within telemetry distributions and do not prove mechanical causation without physical metallurgical inspection.
4. **Single-Worker Database**: SQLite provides zero-configuration ACID persistence for single-node setups. Distributed multi-worker deployments should migrate to PostgreSQL.

---

## 9. License

This major project is developed for academic evaluation purposes under the **MIT License**.



python -m uvicorn app.main:app --reload

npm run dev