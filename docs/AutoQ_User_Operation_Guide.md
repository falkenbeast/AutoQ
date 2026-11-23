# AutoQ – Comprehensive User Operation & Demonstration Guide

**Project:** `AutoQ – Automotive Quality Intelligence System`  
**Location:** `D:\Study_material\python_mark1\project\AutoQ`  
**Academic Target:** Final-Year B.Tech CSE Major Project Demonstration  
**Author:** AutoQ Development Team  
**Date:** November 2026  

---

## 1. Introduction & Core Concept

**AutoQ** is an artificial intelligence-driven manufacturing quality platform designed for automotive assembly plants and quality engineering departments. 

### Key Conceptual Distinction: Physical Inspection vs. ML Defect Prediction
Before operating the system, understand this critical distinction:
- **Physical Inspection (`/inspections`):** Represents **ground-truth quality audit data** collected by human quality inspectors or automated CMM/optical test benches on manufactured parts. It contains observed defects and determines factory yield KPIs.
- **Machine Learning Prediction (`/predict`):** Represents an **AI-driven probabilistic forecast** made by the Scikit-learn Random Forest model from manufacturing telemetry (temperatures, rotational speeds, pressures, and cumulative tool wear). It predicts whether a part is at risk of defect *before or during* manufacturing. A prediction does not automatically mutate confirmed physical inspection logs; it serves as proactive quality assurance intelligence.

---

## 2. System Startup Instructions

AutoQ is a dual-tier web application consisting of a FastAPI backend and a React (Vite) frontend.

### 2.1 Starting the Backend API Server
1. Open PowerShell or a terminal and navigate to the project root:
   ```powershell
   cd D:\Study_material\python_mark1\project\AutoQ\backend
   ```
2. Activate the Python virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Start the Uvicorn ASGI server:
   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
4. Verify server output:
   ```text
   INFO:     Started server process
   INFO:     AutoQ ML Inference Engine loaded champion Random Forest model successfully (ROC-AUC: 0.9830).
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

### 2.2 Starting the React Frontend Application
1. Open a second terminal window and navigate to the frontend directory:
   ```powershell
   cd D:\Study_material\python_mark1\project\AutoQ\frontend
   ```
2. Launch the Vite development server:
   ```powershell
   npm run dev
   ```
3. The interface will be accessible at:
   ```text
   http://localhost:5173
   ```

---

## 3. Confirming API Connectivity & Platform Health

1. Open your browser and navigate to `http://localhost:5173`.
2. Look at the top navigation bar (`Topbar`):
   - You will see a green pulse dot indicating **API Connected (Port 8000)**.
   - Click the **Bell Icon** on the top right to open **System Status & Alerts**:
     - *ML Inference Engine Online* (ROC-AUC: 0.9830)
     - *SQLite Database Connected* (SQLAlchemy storage active)
3. Direct API Verification:
   - In your browser, open `http://127.0.0.1:8000/api/health`.
   - The response should be:
     ```json
     {
       "status": "healthy",
       "database_connected": true,
       "ml_engine": {
         "model_available": true,
         "model_name": "Random Forest Champion Pipeline",
         "test_roc_auc": 0.983
       }
     }
     ```
   - Interactive Swagger API documentation is available at `http://127.0.0.1:8000/docs`.

---

## 4. Navigating the Application

The dark industrial sidebar provides access to all seven core modules:
- 📊 **Overview (`/`):** Executive factory-floor summary, high-level KPIs, trends, and recent inspection log.
- 📋 **Component Inspections (`/inspections`):** Physical quality inspection ledger, manual logging, CSV upload, and record management.
- 🔮 **Defect Prediction (`/predict`):** Real-time ML inference engine with dual-threshold sensitivity selection and prediction history.
- 🔬 **Defect Analysis (`/defects`):** Pareto failure taxonomy, batch defect comparisons, and ML feature importance (MDI).
- 📈 **Quality Analytics (`/analytics`):** Yield performance, batch pass rates, process parameter distributions, and highest-yield batch calculation.
- 📄 **Audit Reports (`/reports`):** Certified ReportLab PDF and structured CSV compilation, automatic browser download, and archive catalog.
- ⚙️ **Settings (`/settings`):** Deep system telemetry, model parameters, API ping diagnostics, and persistent user preferences.

---

## 5. How to Add a Physical Inspection Record

1. Navigate to **Component Inspections** (`/inspections`).
2. Click the **+ Log Inspection** button in the top right.
3. Fill in the modal form:
   - **Component ID:** e.g., `CMP-BRK-501` (Unique part serial).
   - **Component Name:** e.g., `High-Pressure Caliper`.
   - **Subsystem Category:** Select from dropdown (e.g., `Braking System`, `Powertrain`, `Engine`).
   - **Production Batch:** e.g., `BATCH-2026-A2`.
   - **Manufacturing Temperature (°C):** e.g., `742.5` (Allowed: 1 to 2500°C).
   - **Clamping Pressure (bar):** e.g., `146.0` (Allowed: 1 to 1000 bar).
   - **Inspection Outcome:** Choose `Passed` or `Defective`.
   - **Defect Category:** If `Defective`, select the failure category (e.g., `Heat Dissipation Failure`, `Tool Wear Failure`). If `Passed`, leave as `None`.
   - **Inspection Notes:** Add optional engineering observations.
4. Click **Save Inspection Record**.
5. The record is instantly written to SQLite and appears immediately in the table and all dashboard analytics.

---

## 6. How to Upload Batch Inspection Records via CSV

1. On the **Component Inspections** page, click the **Upload CSV** button.
2. Prepare a CSV file containing the required columns:
   ```csv
   component_id,component_name,component_category,manufacturing_temperature,pressure,production_batch,inspection_result,defect_category,notes
   CMP-AXL-101,Rear Axle Shaft,Chassis & Steering,748.2,142.0,BATCH-2026-A1,Passed,None,Line inspection OK
   CMP-TRB-102,Turbo Impeller,Powertrain,792.0,165.5,BATCH-2026-B1,Defective,Heat Dissipation Failure,Thermal hairline microcracks
   ```
3. Drag and drop or browse to select your CSV file.
4. Click **Validate & Ingest CSV**.
5. The backend validates schema headers, data ranges, and duplicate IDs, and inserts the records atomically.

---

## 7. How to Run Defect Prediction with the ML Engine

1. Navigate to **Defect Prediction Engine** (`/predict`).
2. Choose your active **Operating Decision Threshold ($\tau$)**:
   - **0.50 (Standard):** Balanced industrial cutoff optimizing overall F1-score ($F_1 = 0.8125$).
   - **0.35 (High-Recall Recommended):** High-sensitivity automotive safety cutoff catching up to 89.7% of borderline defects.
3. Enter manufacturing parameters on the left card:
   - **Component ID:** e.g., `CMP-TRB-809`
   - **Batch:** e.g., `BATCH-2026-B1`
   - **Category:** e.g., `Powertrain`
   - **Manufacturing Temp:** e.g., `785.0 °C`
   - **Clamping Pressure:** e.g., `164.0 bar`
   - **Spindle Speed:** e.g., `1350 rpm`
   - **Cumulative Tool Wear:** e.g., `215 min`
   - **Torsional Resistance:** e.g., `52.0 Nm`
4. Click **Run Defect Prediction**.
5. The button triggers `POST /api/predictions`. The backend executes the trained Scikit-learn Random Forest pipeline and renders the live prediction outcome card in real time.

---

## 8. How to Interpret Prediction Results

Upon evaluation, the right panel displays:
1. **Predicted Outcome:** A green `PASSED` badge or red `DEFECTIVE` badge.
2. **Defect Probability:** Exact model probability (e.g., `78.4%`).
3. **Model Confidence:** Prediction certainty level (e.g., `96.2%`).
4. **Attributed Root-Cause Failure Mode:** If defective, the secondary multiclass classifier identifies the specific mechanism:
   - *Heat Dissipation Failure (HDF)*
   - *Power Failure (PWF)*
   - *Tool Wear Failure (TWF)*
   - *Overstrain Failure (OSF)*
   - *Random Failure (RNF)*
5. **Key Influencing Drivers:** Telemetry features that elevated risk (e.g., Tool Wear > 200 min, Delta Temp < 8.6 K).
6. **Actionable QA Directive:** Specific instruction (e.g., *"Halt machining line. Replace cutting insert and recalibrate spindle coolant."*).
7. **Recent ML Predictions History:** The bottom table updates automatically with the transaction record.

---

## 9. How to Use Defect Analysis

1. Navigate to **Defect Analysis & Patterns** (`/defects`).
2. Filter by **Batch** using the dropdown at the top right, or select **All Batches**.
3. Inspect the four analytical panels:
   - **Defect Category Breakdown:** Pareto chart showing failure types from SQLite inspections.
   - **Frequently Affected Subsystems:** Yield by mechanical subsystem (Powertrain, Braking, Engine, Chassis).
   - **ML Feature Importances (MDI):** Relative weighting of sensor inputs from the trained Random Forest model.
   - **Batch-Wise Defect Comparison:** Defect rates across manufacturing batches.
4. Review the **High-Risk Failure Modes & Directives** at the bottom for standard engineering mitigation protocols.

---

## 10. How to Interpret Quality Analytics

1. Navigate to **Quality Analytics** (`/analytics`).
2. Review the top KPI cards:
   - **Overall Pass Percentage:** Conforming units divided by total units.
   - **Average Defect Rate:** Percentage of flagged defective units.
   - **Batches Evaluated:** Total distinct production lots active in SQLite.
   - **Highest Yield Batch:** Evaluated dynamically by SQL grouping $\frac{\text{Passed}}{\text{Total}}$.
3. Review **Inspection Volume & Defect Rate Trends** over time.
4. Review the **Batch Quality & Yield Audit Summary** table for temperature and pressure averages per batch.

---

## 11. How to Compile and Download Reports

1. Navigate to **Quality Inspection Reports** (`/reports`).
2. Configure report parameters:
   - **Report Category:** Choose `Defect Analysis`, `Inspection Summary`, `Quality Performance`, or `Batch Audit`.
   - **Target Batch:** Choose `All Active Batches` or a specific batch (e.g., `BATCH-2026-A2`).
   - **Audit Period:** Select `Last 7 Days`, `Last 14 Days`, `Last 30 Days`, or `Current Month`.
   - **Output Format:** Choose **PDF Document (.pdf)** or **Raw CSV Dataset (.csv)**.
3. Click **Compile & Save Report**.
4. The system will:
   - Query matching records from SQLite.
   - Physically render the file into `backend/reports/` using ReportLab.
   - Automatically trigger a browser download save dialog.
   - Update the **Generated Report Archive** table at the bottom of the page.

---

## 12. How to Download Existing Archived Reports

1. Scroll to the **Generated Report Archive** on the `/reports` page.
2. Locate the desired report row.
3. Click the **Download** button in the action column.
4. The backend streams the physical file via `GET /api/reports/{id}/download` with proper MIME headers.

---

## 13. How to Use Settings

1. Navigate to **System Settings & Diagnostics** (`/settings`).
2. **Ping API Health:** Click to test real-time connectivity to the FastAPI server.
3. **Workspace Preferences:**
   - Configure default batch, default category, chart horizon, and refresh rate.
   - Click **Save Preferences** to persist preferences to browser `localStorage`.
   - Click **Reset Defaults** to restore factory settings at any time.

---

## 14. Common Errors & Troubleshooting

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| **Top bar shows "API Disconnected (Port 8000)"** | FastAPI server is not running or crashed. | Run `uvicorn app.main:app --port 8000` in the `backend/` directory. |
| **"No qualifying inspection records found" (HTTP 422)** | Report generated for a batch or date range that has 0 records in SQLite. | Select `All Active Batches` or log inspection records for that batch first. |
| **"Component with identifier ... was not found"** | Trying to inspect a non-existent part ID. | Ensure the component ID exists or add it via the inspection creation form. |
| **Browser download does not prompt immediately** | Browser pop-up blocker or aggressive download permissions. | Check browser download settings; click **Download** from the Archive table to manually re-trigger. |
| **Prediction returns high defect probability for normal part** | High tool wear (>200 min) or high temperature (>780°C) entered. | Verify manufacturing inputs match standard operating parameters (Temp ~740°C, Tool Wear <150 min). |

---

## 15. Demonstration Script (Recommended Step-by-Step Flow)

For your project presentation or external evaluation, follow this sequence:

1. **Start on Settings (`/settings`):** Show the system health diagnostics, active Random Forest champion model specifications (ROC-AUC 0.9830), and SQLite connectivity.
2. **Show Clean Overview (`/`):** Point out that the system starts in a clean, pristine state with 0 inspections and clean empty-state visualizers.
3. **Log 2-3 Inspections (`/inspections`):**
   - Add one **Passed** part: `CMP-BRK-101`, Braking, 740°C, 142 bar, Batch `BATCH-2026-A2`.
   - Add one **Defective** part: `CMP-TRB-102`, Powertrain, 790°C, 168 bar, Batch `BATCH-2026-B1`, Defect: `Heat Dissipation Failure`.
4. **Show Cross-Page Updates:**
   - Go to **Overview (`/`)**: Show that total = 2, passed = 1, defective = 1, defect rate = 50.0%, and highest-yield batch = `BATCH-2026-A2` (100% yield).
   - Go to **Quality Analytics (`/analytics`)**: Show batch yield comparison bars.
   - Go to **Defect Analysis (`/defects`)**: Show the defect Pareto chart highlighting Heat Dissipation Failure.
5. **Demonstrate AI Prediction (`/predict`):**
   - Enter severe parameters (Temp 785°C, Tool Wear 220 min, Spindle 1300 rpm).
   - Set threshold to $\tau = 0.35$ (High-Recall).
   - Click **Run Defect Prediction**.
   - Show the live Defective result, probability, attributed failure mode (`Heat Dissipation Failure`), and contributing factors.
   - Point out the newly saved entry in the **Recent ML Predictions History** table.
6. **Generate a Quality Report (`/reports`):**
   - Select `Defect Analysis Report`, format `PDF Document (.pdf)`.
   - Click **Compile & Save Report**.
   - Show the browser automatically downloading the PDF.
   - Open the PDF and display the ReportLab executive KPI table, inspection rows, and quality approval stamp.
   - Point to the updated **Generated Report Archive** showing the saved file size and date.
