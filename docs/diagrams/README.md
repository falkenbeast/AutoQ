# AutoQ – Architecture and Workflow Diagrams

This directory contains the authoritative visual diagrams representing the architecture, data flows, machine learning pipelines, and relational schemas of the AutoQ Automotive Quality Intelligence System.

---

## 1. Overall System Architecture

```mermaid
flowchart TB
    subgraph ClientLayer["Presentation Layer: React 19 Client"]
        UI_Dash["Overview Dashboard"]
        UI_Insp["Inspection Log & Management"]
        UI_Pred["Defect Prediction Studio"]
        UI_Anly["Quality Analytics (Recharts)"]
        UI_Rep["Audit Reports Center"]
    end

    subgraph APILayer["API Gateway & Service Layer: FastAPI"]
        Router["Centralized REST API Router (/api & /api/v1)"]
        InspService["Inspection Service"]
        PredService["Prediction Service"]
        AnlyService["Analytics Service"]
        RepService["ReportLab Reporting Service"]
    end

    subgraph MLLayer["Machine Learning Inference Tier"]
        FeatureMap["Feature Mapping & Boundary Validation"]
        PreprocPipe["StandardScaler & OneHotEncoder Pipeline"]
        ChampModel["Champion Random Forest (defect_classifier_pipeline.joblib)"]
        MultiModel["Multiclass Defect Classifier (multiclass_defect_classifier.joblib)"]
    end

    subgraph StorageLayer["Data & Artifact Storage"]
        SQLiteDB[("SQLite Database: autoq.db")]
        ModelFiles[("Trained Model Artifacts (joblib/json)")]
        ReportFiles[("Physical PDF / CSV Reports (backend/reports)")]
    end

    ClientLayer -->|HTTP / JSON REST API| Router
    Router --> InspService
    Router --> PredService
    Router --> AnlyService
    Router --> RepService

    PredService --> FeatureMap
    FeatureMap --> PreprocPipe
    PreprocPipe --> ChampModel
    ChampModel --> MultiModel

    InspService --> SQLiteDB
    PredService --> SQLiteDB
    AnlyService --> SQLiteDB
    RepService --> SQLiteDB
    RepService --> ReportFiles
    ChampModel -.-> ModelFiles
    MultiModel -.-> ModelFiles
```

---

## 2. Frontend-Backend Communication Flow

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Quality Engineer
    participant Frontend as React 19 Frontend
    participant API as FastAPI REST Gateway
    participant Predictor as DefectPredictor Engine
    participant DB as SQLite Persistence (autoq.db)

    Operator->>Frontend: Enter Component Telemetry (Speed, Torque, Wear, Temp)
    Frontend->>API: POST /api/predictions (JSON Body)
    API->>API: Pydantic Validation & Physical Envelope Checks
    API->>Predictor: predict(payload, decision_threshold=0.50)
    Predictor->>Predictor: Feature Mapping & Scaling (preprocessor.joblib)
    Predictor->>Predictor: Binary Evaluation (defect_classifier_pipeline.joblib)
    alt Defective Part Predicted
        Predictor->>Predictor: Secondary Multiclass Attribution (multiclass_defect_classifier.joblib)
    end
    Predictor-->>API: Inference Results & Confidence Score
    API->>DB: INSERT INTO predictions (Persist evaluation log)
    DB-->>API: Acknowledge Transaction
    API-->>Frontend: HTTP 200 OK (PredictionResponse JSON)
    Frontend-->>Operator: Display Defect Status, Probability Meter & Disposition
```

---

## 3. Machine Learning Training & Model Selection Pipeline

```mermaid
flowchart LR
    RawData["Raw Telemetry (AI4I 2020: 10,000 records)"]
    
    subgraph DataPrep["Zero-Leakage Partitioning"]
        Split["Stratified Split (80% Train / 20% Test)"]
        TrainSet["Train Set (8,000 rows, 280 defects)"]
        TestSet["Holdout Test Set (2,000 rows, 68 defects)"]
    end

    subgraph FeatureEng["Feature Engineering"]
        Eng1["Thermal Gradient: ΔT = T_process - T_air"]
        Eng2["Mechanical Power: P = 2π * rpm * torque / 60"]
        Eng3["Overstrain Index: Wear * Torque"]
    end

    subgraph CandidateTraining["Cross-Validation Training (5-Fold CV)"]
        LR["Logistic Regression (CV ROC: 0.9228)"]
        DT["Decision Tree (CV ROC: 0.9491)"]
        RF["Balanced Random Forest (CV ROC: 0.9801)"]
        GB["Gradient Boosting (CV ROC: 0.9795)"]
    end

    subgraph HoldoutEval["Holdout Test Evaluation (N=2,000)"]
        Eval["Model Selection: Random Forest Champion"]
        Metrics["ROC-AUC: 0.9830 | PR-AUC: 0.8737 | Recall: 86.76%"]
        Artifacts["Serialize to defect_classifier_pipeline.joblib"]
    end

    RawData --> Split
    Split --> TrainSet
    Split --> TestSet
    TrainSet --> FeatureEng
    FeatureEng --> CandidateTraining
    CandidateTraining --> HoldoutEval
```

---

## 4. Real-Time Defect Prediction & Attribution Workflow

```mermaid
flowchart TD
    Start([Incoming Telemetry Stream]) --> ValCheck{Valid Physical Envelope?}
    ValCheck -- No --> Err422[Raise HTTP 422 Unprocessable Entity]
    ValCheck -- Yes --> MapLayer[Feature Mapping Layer: Compute ΔT, Power, Overstrain]
    MapLayer --> Scale[Scale & Encode Features via preprocessor.joblib]
    Scale --> RFModel[Execute Random Forest: defect_classifier_pipeline.joblib]
    RFModel --> ProbCalc[Compute Calibrated Defect Probability p]
    ProbCalc --> ThreshCheck{p >= Decision Threshold τ?}
    
    ThreshCheck -- No: p < τ --> PassResult[Predicted Status: Passed]
    PassResult --> ClearRec[Recommendation: Component Conforms to Specification]
    
    ThreshCheck -- Yes: p >= τ --> DefectResult[Predicted Status: Defective]
    DefectResult --> MultiClass[Execute Secondary Multiclass Classifier]
    MultiClass --> RootCause{Determine Failure Mode}
    RootCause -->|ΔT < 8.6K| HDF[Heat Dissipation Failure]
    RootCause -->|Power Out of Range| PWF[Power Failure]
    RootCause -->|Wear * Torque > 11000| OSF[Overstrain Failure]
    RootCause -->|Tool Wear >= 200 min| TWF[Tool Wear Failure]
    RootCause -->|Other Deviation| OtherFail[Process Anomaly / Multi-mode Failure]
    
    ClearRec --> SaveDB[Persist to SQLite predictions Table]
    HDF --> SaveDB
    PWF --> SaveDB
    OSF --> SaveDB
    TWF --> SaveDB
    OtherFail --> SaveDB
    SaveDB --> End([Return PredictionResponse JSON to Client])
```

---

## 5. Database Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    COMPONENTS ||--o{ INSPECTIONS : "has"
    COMPONENTS ||--o{ PREDICTIONS : "evaluates"
    INSPECTIONS ||--o| PREDICTIONS : "optionally links"
    
    COMPONENTS {
        int id PK
        string component_id UK "e.g. CMP-BRK-401"
        string component_name "e.g. Brake Caliper Mount"
        string component_category "e.g. Braking System"
        text description
        datetime created_at
    }

    INSPECTIONS {
        int id PK
        string component_id FK
        float manufacturing_temperature "Temperature in °C"
        float pressure "Pressure in bar"
        string production_batch "e.g. BATCH-2026-A1"
        string inspection_result "Passed / Defective"
        text notes
        datetime created_at
    }

    PREDICTIONS {
        int id PK
        string component_id FK
        int inspection_id FK "Nullable, decoupled on delete"
        string predicted_status "Passed / Defective"
        float defect_probability "Calibrated [0.0, 1.0]"
        string model_version "1.0.0"
        string model_status "INFERENCE_COMPLETE"
        json contributing_factors
        text recommendation
        datetime created_at
    }

    REPORTS {
        int id PK
        string report_code UK "e.g. REP-0001-All-Batches"
        string title
        string file_type "PDF / CSV"
        string file_path "backend/reports/REP-0001.pdf"
        string status "READY"
        datetime created_at
    }
```

---

## 6. CSV Inspection Upload Workflow

```mermaid
flowchart TD
    Upload([Operator Uploads CSV File]) --> SizeCheck{File Size <= 10 MB?}
    SizeCheck -- No --> RejSize[Reject: HTTP 400 File Exceeds 10MB Limit]
    SizeCheck -- Yes --> ParseCSV[Read CSV Buffer into Pandas DataFrame]
    ParseCSV --> SchemaCheck{Required Columns Present?}
    SchemaCheck -- No --> RejSchema[Reject: HTTP 400 Missing Required Fields]
    SchemaCheck -- Yes --> LoopRows[Iterate Validated Rows in DB Transaction]
    
    LoopRows --> CompCheck{Component Exists in Catalog?}
    CompCheck -- No --> AutoCat[Auto-catalog Component in components Table]
    CompCheck -- Yes --> AddInsp[Insert Record into inspections Table]
    AutoCat --> AddInsp
    
    AddInsp --> MoreRows{More Rows?}
    MoreRows -- Yes --> LoopRows
    MoreRows -- No --> Commit[Commit Transaction & Invalidate Analytics Cache]
    Commit --> Finish([Return Ingestion Summary: Ingested Count, Skipped Count])
```

---

## 7. Report Generation & Download Workflow

```mermaid
flowchart TD
    Req([User Requests Report: PDF or CSV]) --> QueryData[Query Filtered Inspections & Analytics from SQLite]
    QueryData --> TypeCheck{Report Type?}
    
    TypeCheck -- CSV --> BuildCSV[Generate Formatted Tabular CSV Document]
    BuildCSV --> WriteCSV[Save File to backend/reports/REP-XXXX.csv]
    
    TypeCheck -- PDF --> BuildPDF[Execute ReportLab Document Builder]
    BuildPDF --> AddHeader[Draw Industrial Title, Timestamp & Company Header]
    AddHeader --> AddKPI[Render Executive Summary KPIs Table]
    AddKPI --> AddTable[Render Detailed Component Audit Table]
    AddTable --> AddSignOff[Add Quality Assurance Certification Sign-Off Block]
    AddSignOff --> WritePDF[Save File to backend/reports/REP-XXXX.pdf]
    
    WriteCSV --> SaveMeta[Create Row in reports Table]
    WritePDF --> SaveMeta
    SaveMeta --> Notify([HTTP 201 Created: Return Report Code & Details])
    
    Notify -.-> DownloadReq([User Clicks Download Report])
    DownloadReq --> SecCheck{File Exists within backend/reports Root?}
    SecCheck -- No --> Err404[HTTP 404 Not Found / Access Denied]
    SecCheck -- Yes --> Stream[FileResponse: Stream Binary Content with Safe Attachment Name]
```

